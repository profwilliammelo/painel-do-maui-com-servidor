"""
🇯🇲 MELODIA&BARULHO – Painel Interativo do Maui 🇯🇲
Dashboard interativo usando Streamlit para visualizar dados do Spotify
"""

import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# ========================================================
# CONFIGURAÇÃO DA PÁGINA
# ========================================================

st.set_page_config(
    page_title="MELODIA&BARULHO – Painel do Maui",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========================================================
# CSS PERSONALIZADO (Tema Solar Dark)
# ========================================================

st.markdown("""
<style>
    /* Estilo Solar Dark Theme */
    .stApp {
        background-color: #002b36;
    }
    
    /* Títulos */
    h1, h2, h3 {
        color: #FED100 !important;
        font-weight: bold;
    }
    
    /* Métricas */
    [data-testid="stMetricValue"] {
        color: #009B3A;
        font-size: 2rem;
        font-weight: bold;
    }
    
    [data-testid="stMetricLabel"] {
        color: #e0e0e0;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #073642;
    }
    
    /* Texto geral */
    p, span, div {
        color: #e0e0e0;
    }
    
    /* Botões */
    .stButton>button {
        background-color: #009B3A;
        color: white;
        border: none;
        border-radius: 5px;
        padding: 10px 20px;
        font-weight: bold;
    }
    
    .stButton>button:hover {
        background-color: #FED100;
        color: #002b36;
    }
    
    /* Tabelas */
    .dataframe {
        color: #e0e0e0;
    }
    
    /* Cards */
    div[data-testid="column"] {
        background-color: transparent;
    }
</style>
""", unsafe_allow_html=True)

# ========================================================
# CORES DO TEMA (Jamaica Style)
# ========================================================

COR_VERDE = "#009B3A"
COR_AMARELO = "#FED100"
COR_PRETO = "#000000"
COR_FUNDO = "#002b36"

# ========================================================
# AUTENTICAÇÃO SPOTIFY
# ========================================================

@st.cache_data(ttl=600)  # Cache por 10 minutos
def get_spotify_client():
    """Cria e retorna cliente autenticado do Spotify"""
    try:
        # Tentar pegar das secrets do Streamlit primeiro
        if 'SPOTIFY_CLIENT_ID' in st.secrets and 'SPOTIFY_CLIENT_SECRET' in st.secrets:
            client_id = st.secrets['SPOTIFY_CLIENT_ID']
            client_secret = st.secrets['SPOTIFY_CLIENT_SECRET']
        else:
            # Senão, tentar pegar das variáveis de ambiente
            client_id = os.getenv('SPOTIFY_CLIENT_ID', '0caec502acbb484b88aed47f7166130e')
            client_secret = os.getenv('SPOTIFY_CLIENT_SECRET', '1017306e97a04cdfbb3784fd27589c98')
        
        if not client_id or not client_secret:
            st.error("❌ Credenciais do Spotify não encontradas!")
            st.stop()
        
        auth_manager = SpotifyClientCredentials(
            client_id=client_id,
            client_secret=client_secret
        )
        
        sp = spotipy.Spotify(auth_manager=auth_manager)
        return sp
    
    except Exception as e:
        st.error(f"❌ Erro ao conectar com Spotify: {str(e)}")
        st.stop()

# ========================================================
# FUNÇÃO PARA BUSCAR DADOS DO MAUI
# ========================================================

@st.cache_data(ttl=600)  # Cache por 10 minutos
def get_maui_data():
    """Busca todos os dados do artista Maui"""
    
    sp = get_spotify_client()
    
    # ID do Maui
    maui_id = "36KguyRusb89rBTNnL32ed"
    
    # ---- 1. Informações do Artista ----
    artist_info = sp.artist(maui_id)
    
    info_artista = {
        'nome': artist_info['name'],
        'seguidores': artist_info['followers']['total'],
        'popularidade': artist_info['popularity'],
        'generos': ', '.join(artist_info['genres']) if artist_info['genres'] else 'N/A'
    }
    
    # ---- 2. Álbuns e Singles ----
    albums_raw = sp.artist_albums(
        maui_id,
        include_groups=['album', 'single', 'appears_on', 'compilation'],
        limit=50
    )
    
    albums_list = []
    for album in albums_raw['items']:
        albums_list.append({
            'id_album': album['id'],
            'nome_album': album['name'],
            'tipo_album': album['album_type'],
            'data_lancamento': album['release_date'],
            'total_faixas': album['total_tracks'],
            'ano_lancamento': int(album['release_date'][:4]) if album['release_date'] else None
        })
    
    df_albums = pd.DataFrame(albums_list).drop_duplicates('id_album')
    
    # ---- 3. Faixas com participação do Maui ----
    tracks_list = []
    
    for _, album in df_albums.iterrows():
        try:
            tracks = sp.album_tracks(album['id_album'], limit=50)
            
            for track in tracks['items']:
                # Verificar se Maui está nos artistas da faixa
                artist_ids = [artist['id'] for artist in track['artists']]
                
                if maui_id in artist_ids:
                    tracks_list.append({
                        'id_faixa': track['id'],
                        'nome_faixa': track['name'],
                        'nome_album': album['nome_album'],
                        'id_album': album['id_album'],
                        'numero_faixa': track['track_number'],
                        'duracao_ms': track['duration_ms'],
                        'duracao_min': round(track['duration_ms'] / 60000, 2),
                        'explicita': track['explicit'],
                        'ano_lancamento': album['ano_lancamento']
                    })
        except Exception as e:
            st.warning(f"⚠️ Erro ao buscar faixas do álbum {album['nome_album']}: {str(e)}")
            continue
    
    df_tracks = pd.DataFrame(tracks_list).drop_duplicates('id_faixa')
    
    # ---- 4. Popularidade das Faixas ----
    if len(df_tracks) > 0:
        track_ids = df_tracks['id_faixa'].unique().tolist()
        
        # API do Spotify aceita até 50 IDs por vez
        popularidades = []
        for i in range(0, len(track_ids), 50):
            batch = track_ids[i:i+50]
            tracks_info = sp.tracks(batch)
            
            for track in tracks_info['tracks']:
                if track:  # Verificar se track não é None
                    popularidades.append({
                        'id_faixa': track['id'],
                        'popularidade_faixa': track['popularity']
                    })
        
        df_popularidade = pd.DataFrame(popularidades)
        df_tracks = df_tracks.merge(df_popularidade, on='id_faixa', how='left')
    
    return info_artista, df_albums, df_tracks

# ========================================================
# SIDEBAR
# ========================================================

with st.sidebar:
    st.markdown("# 🇯🇲 MELODIA&BARULHO")
    st.markdown("### Painel do Maui")
    st.markdown("**Prof Dr William Melo | W-Black | v2.0**")
    st.markdown("---")
    
    if st.button("🔄 Atualizar Dados", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    
    st.markdown("---")
    st.markdown("**Fonte:** Spotify Web API")
    st.markdown(f"**Última atualização:**  \n{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

# ========================================================
# CARREGAR DADOS
# ========================================================

with st.spinner("🎵 Buscando dados do Spotify..."):
    info_artista, df_albums, df_tracks = get_maui_data()

st.success("✅ Dados carregados com sucesso!")

# ========================================================
# TÍTULO PRINCIPAL
# ========================================================

st.markdown(f"# 🎤 {info_artista['nome']}")
st.markdown("---")

# ========================================================
# SEÇÃO 1: VISÃO GERAL (KPIs)
# ========================================================

st.markdown("## 📊 Visão Geral")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        label="👥 Seguidores Totais",
        value=f"{info_artista['seguidores']:,}".replace(',', '.')
    )

with col2:
    st.metric(
        label="📈 Popularidade (0-100)",
        value=info_artista['popularidade']
    )

with col3:
    st.metric(
        label="🎵 Total de Faixas c/ Maui",
        value=len(df_tracks)
    )

st.markdown("---")

# ========================================================
# SEÇÃO 2: VISUALIZAÇÕES
# ========================================================

st.markdown("## 📈 Análises e Visualizações")

# ---- Top 10 Faixas por Popularidade ----
st.markdown("### 🏆 Top 10 Faixas por Popularidade")

top_faixas = df_tracks.nlargest(10, 'popularidade_faixa')

fig_top_faixas = px.bar(
    top_faixas,
    x='popularidade_faixa',
    y='nome_faixa',
    orientation='h',
    labels={'popularidade_faixa': 'Popularidade', 'nome_faixa': ''},
    title='As mais ouvidas no Spotify',
    color='popularidade_faixa',
    color_continuous_scale=[[0, COR_VERDE], [1, COR_AMARELO]]
)

fig_top_faixas.update_layout(
    plot_bgcolor=COR_FUNDO,
    paper_bgcolor=COR_FUNDO,
    font=dict(color='#e0e0e0'),
    yaxis={'categoryorder': 'total ascending'},
    showlegend=False,
    height=400
)

st.plotly_chart(fig_top_faixas, use_container_width=True)

# ---- Row com 2 gráficos ----
col_left, col_right = st.columns(2)

with col_left:
    st.markdown("### 📀 Faixas por Álbum/Projeto")
    
    faixas_por_album = df_tracks.groupby('nome_album').size().reset_index(name='count')
    faixas_por_album = faixas_por_album.nlargest(15, 'count')
    
    fig_albuns = px.bar(
        faixas_por_album,
        x='count',
        y='nome_album',
        orientation='h',
        labels={'count': 'Número de faixas', 'nome_album': ''},
        color_discrete_sequence=[COR_VERDE]
    )
    
    fig_albuns.update_layout(
        plot_bgcolor=COR_FUNDO,
        paper_bgcolor=COR_FUNDO,
        font=dict(color='#e0e0e0'),
        yaxis={'categoryorder': 'total ascending'},
        showlegend=False,
        height=400
    )
    
    st.plotly_chart(fig_albuns, use_container_width=True)

with col_right:
    st.markdown("### 📅 Linha do Tempo de Lançamentos")
    
    lancamentos_por_ano = df_tracks.groupby('ano_lancamento').size().reset_index(name='count')
    lancamentos_por_ano = lancamentos_por_ano.sort_values('ano_lancamento')
    
    fig_linha = go.Figure()
    
    fig_linha.add_trace(go.Scatter(
        x=lancamentos_por_ano['ano_lancamento'],
        y=lancamentos_por_ano['count'],
        mode='lines+markers',
        line=dict(color=COR_VERDE, width=3),
        marker=dict(
            size=10,
            color=COR_AMARELO,
            line=dict(color=COR_PRETO, width=2)
        ),
        name='Faixas lançadas'
    ))
    
    fig_linha.update_layout(
        plot_bgcolor=COR_FUNDO,
        paper_bgcolor=COR_FUNDO,
        font=dict(color='#e0e0e0'),
        xaxis_title='Ano',
        yaxis_title='Faixas lançadas',
        showlegend=False,
        height=400
    )
    
    st.plotly_chart(fig_linha, use_container_width=True)

st.markdown("---")

# ========================================================
# SEÇÃO 3: DADOS DETALHADOS
# ========================================================

st.markdown("## 📋 Dados Detalhados")

# Preparar tabela
tabela_exibicao = df_tracks[[
    'nome_faixa', 
    'nome_album', 
    'ano_lancamento', 
    'popularidade_faixa', 
    'duracao_min'
]].copy()

tabela_exibicao.columns = [
    'Música', 
    'Álbum', 
    'Ano', 
    'Popularidade', 
    'Duração (min)'
]

tabela_exibicao = tabela_exibicao.sort_values('Popularidade', ascending=False)

# Exibir tabela interativa
st.dataframe(
    tabela_exibicao,
    use_container_width=True,
    hide_index=True,
    height=400
)

# ========================================================
# RODAPÉ
# ========================================================

st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #586e75;'>"
    "💾 MELODIA&BARULHO DATA ANALYTICS | Powered by Spotify API"
    "</div>",
    unsafe_allow_html=True
)
