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
# CORES DO TEMA (Jamaica Style)
# ========================================================

COR_VERDE = "#009B3A"
COR_AMARELO = "#FED100"
COR_PRETO = "#000000"
COR_FUNDO = "#002b36"
COR_TEXTO = "#e0e0e0"
COR_CARD_CINZA = "#4a5a63" # Cor aproximada do card cinza da imagem

# ========================================================
# CSS PERSONALIZADO (Tema Solar Dark + Cards)
# ========================================================

st.markdown(f"""
<style>
    /* Importar fontes se necessário (opcional) */
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap');

    /* Estilo Solar Dark Theme */
    .stApp {{
        background-color: {COR_FUNDO};
        font-family: 'Roboto', sans-serif;
    }}
    
    /* Títulos */
    h1, h2, h3 {{
        color: {COR_TEXTO} !important;
        font-weight: bold;
    }}
    
    /* Sidebar */
    [data-testid="stSidebar"] {{
        background-color: #073642;
    }}
    
    /* Texto geral */
    p, span, div, label {{
        color: {COR_TEXTO};
    }}
    
    /* Botões */
    .stButton>button {{
        background-color: {COR_VERDE};
        color: white;
        border: none;
        border-radius: 5px;
        padding: 10px 20px;
        font-weight: bold;
    }}
    
    .stButton>button:hover {{
        background-color: {COR_AMARELO};
        color: {COR_FUNDO};
    }}
    
    /* Tabelas */
    .dataframe {{
        color: {COR_TEXTO};
    }}
    
    /* Plotly Background Transparente */
    .js-plotly-plot .plot-container .main-svg {{
        background: transparent !important;
    }}
    
    /* Cards Customizados (KPIs) */
    .kpi-card {{
        border-radius: 10px;
        padding: 20px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        height: 140px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }}
    
    .kpi-title {{
        font-size: 1rem;
        font-weight: 500;
        margin-bottom: 5px;
        opacity: 0.9;
    }}
    
    .kpi-value {{
        font-size: 3rem;
        font-weight: bold;
        line-height: 1.2;
    }}
    
    .kpi-icon {{
        font-size: 3rem;
        opacity: 0.5;
        position: absolute;
        right: 20px;
        top: 50%;
        transform: translateY(-50%);
    }}
    
    /* Ajuste para ícones dentro das colunas */
    div[data-testid="column"] {{
        position: relative;
    }}

</style>
""", unsafe_allow_html=True)

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
            client_id = os.getenv('SPOTIFY_CLIENT_ID')
            client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
        
        if not client_id or not client_secret:
            st.error("❌ Credenciais do Spotify não encontradas! Configure as secrets (.streamlit/secrets.toml) ou variáveis de ambiente.")
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
    """Busca todos os dados do artista Maui, incluindo participações"""
    
    sp = get_spotify_client()
    
    # ID do Maui
    maui_id = "36KguyRusb89rBTNnL32ed"
    
    # ---- 1. Informações do Artista ----
    try:
        artist_info = sp.artist(maui_id)
        info_artista = {
            'nome': artist_info['name'],
            'seguidores': artist_info['followers']['total'],
            'popularidade': artist_info['popularity'],
            'generos': ', '.join(artist_info['genres']) if artist_info['genres'] else 'N/A'
        }
    except Exception as e:
        st.error(f"Erro ao buscar informações do artista: {e}")
        return None, None, None
    
    # ---- 2. Álbuns e Singles (COM PAGINAÇÃO) ----
    albums_list = []
    
    try:
        # Busca inicial - ADICIONADO country='BR' para garantir disponibilidade
        results = sp.artist_albums(
            maui_id,
            include_groups=['album', 'single', 'appears_on', 'compilation'],
            country='BR', 
            limit=50
        )
        albums_raw = results['items']
        
        # Paginação para buscar TODOS os álbuns/participações
        while results['next']:
            results = sp.next(results)
            albums_raw.extend(results['items'])
            
        for album in albums_raw:
            albums_list.append({
                'id_album': album['id'],
                'nome_album': album['name'],
                'tipo_album': album['album_type'],
                'data_lancamento': album['release_date'],
                'total_faixas': album['total_tracks'],
                'ano_lancamento': int(album['release_date'][:4]) if album['release_date'] else None
            })
            
    except Exception as e:
        st.warning(f"Erro ao buscar álbuns: {e}")
    
    df_albums = pd.DataFrame(albums_list).drop_duplicates('id_album')
    
    # ---- 3. Faixas com participação do Maui ----
    tracks_list = []
    
    # Barra de progresso para carregamento de faixas (pode demorar)
    progress_bar = st.progress(0, text="Analisando álbuns e faixas...")
    total_albums = len(df_albums)
    
    for idx, (_, album) in enumerate(df_albums.iterrows()):
        try:
            # Atualiza barra de progresso
            progress_bar.progress((idx + 1) / total_albums, text=f"Analisando: {album['nome_album']}")
            
            # Busca faixas do álbum (com paginação se necessário)
            album_tracks_results = sp.album_tracks(album['id_album'], limit=50)
            album_tracks = album_tracks_results['items']
            
            while album_tracks_results['next']:
                album_tracks_results = sp.next(album_tracks_results)
                album_tracks.extend(album_tracks_results['items'])
            
            for track in album_tracks:
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
            # st.warning(f"⚠️ Erro ao buscar faixas do álbum {album['nome_album']}: {str(e)}")
            continue
            
    progress_bar.empty() # Remove a barra de progresso ao finalizar
    
    # CRÍTICO: Não remover duplicatas por ID de faixa para manter histórico de lançamentos (Single -> Álbum)
    # Isso garante que a contagem bata com o script R (ex: 77 faixas)
    df_tracks = pd.DataFrame(tracks_list)
    
    # ---- 4. Popularidade das Faixas ----
    if len(df_tracks) > 0:
        # Para buscar popularidade, precisamos de IDs únicos para não sobrecarregar a API
        track_ids_unicos = df_tracks['id_faixa'].unique().tolist()
        
        # API do Spotify aceita até 50 IDs por vez
        popularidades = []
        for i in range(0, len(track_ids_unicos), 50):
            batch = track_ids_unicos[i:i+50]
            try:
                tracks_info = sp.tracks(batch)
                for track in tracks_info['tracks']:
                    if track:  # Verificar se track não é None
                        popularidades.append({
                            'id_faixa': track['id'],
                            'popularidade_faixa': track['popularity']
                        })
            except Exception as e:
                continue
        
        df_popularidade = pd.DataFrame(popularidades)
        
        # Merge mantendo todas as linhas de df_tracks (mesmo as repetidas)
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
    st.markdown("---")
    st.markdown("[GitHub do Projeto](https://github.com/profwilliammelo)")

# ========================================================
# CARREGAR DADOS
# ========================================================

with st.spinner("🎵 Buscando dados do Spotify..."):
    info_artista, df_albums, df_tracks = get_maui_data()

if info_artista is None:
    st.stop()

st.success("✅ Dados carregados com sucesso!")

# ========================================================
# TÍTULO PRINCIPAL
# ========================================================

# st.markdown(f"# 🎤 {info_artista['nome']}")
# st.markdown("---")

# ========================================================
# SEÇÃO 1: VISÃO GERAL (KPIs - Cards Customizados)
# ========================================================

st.markdown("## 📊 Visão Geral")

col1, col2, col3 = st.columns(3)

# Função auxiliar para criar card HTML
def criar_card(titulo, valor, icone, cor_fundo, cor_texto):
    return f"""
    <div class="kpi-card" style="background-color: {cor_fundo}; color: {cor_texto};">
        <div class="kpi-title">{titulo}</div>
        <div class="kpi-value">{valor}</div>
        <div class="kpi-icon">{icone}</div>
    </div>
    """

with col1:
    st.markdown(criar_card(
        "Seguidores Totais", 
        f"{info_artista['seguidores']:,}".replace(',', '.'), 
        "👥", 
        COR_VERDE, 
        "white"
    ), unsafe_allow_html=True)

with col2:
    st.markdown(criar_card(
        "Popularidade (0-100)", 
        info_artista['popularidade'], 
        "📈", 
        COR_AMARELO, 
        COR_FUNDO # Texto escuro para contraste no amarelo
    ), unsafe_allow_html=True)

with col3:
    st.markdown(criar_card(
        "Total de Faixas c/ Maui", 
        len(df_tracks), 
        "🎵", 
        COR_CARD_CINZA, 
        "white"
    ), unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ========================================================
# SEÇÃO 2: VISUALIZAÇÕES
# ========================================================

# st.markdown("## 📈 Análises e Visualizações")

# Layout: Coluna Esquerda (Top Faixas) | Coluna Direita (Álbuns + Linha do Tempo)
# Mas o design original parece ser 3 colunas ou 2 linhas. Vamos manter o layout anterior mas com as cores certas.

col_main_1, col_main_2, col_main_3 = st.columns(3)

# ---- Gráfico 1: Top Faixas (Amarelo) ----
with col_main_1:
    # st.markdown("### 🏆 Top 10 Faixas")
    if not df_tracks.empty:
        top_faixas = df_tracks.nlargest(10, 'popularidade_faixa')
        
        fig_top = px.bar(
            top_faixas,
            x='popularidade_faixa',
            y='nome_faixa',
            orientation='h',
            title='Top 10 Faixas por Popularidade',
            color_discrete_sequence=[COR_AMARELO] # Amarelo
        )
        
        fig_top.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color=COR_TEXTO),
            yaxis={'categoryorder': 'total ascending', 'title': ''},
            xaxis={'title': 'Popularidade'},
            height=400,
            margin=dict(l=0, r=0, t=40, b=0)
        )
        st.plotly_chart(fig_top, use_container_width=True)

# ---- Gráfico 2: Faixas por Álbum (Verde) ----
with col_main_2:
    # st.markdown("### 📀 Faixas por Álbum")
    if not df_tracks.empty:
        faixas_por_album = df_tracks.groupby('nome_album').size().reset_index(name='count')
        faixas_por_album = faixas_por_album.nlargest(15, 'count')
        
        fig_albuns = px.bar(
            faixas_por_album,
            x='count',
            y='nome_album',
            orientation='h',
            title='Faixas por Álbum/Projeto',
            color_discrete_sequence=[COR_VERDE] # Verde
        )
        
        fig_albuns.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color=COR_TEXTO),
            yaxis={'categoryorder': 'total ascending', 'title': ''},
            xaxis={'title': 'Número de faixas'},
            height=400,
            margin=dict(l=0, r=0, t=40, b=0)
        )
        st.plotly_chart(fig_albuns, use_container_width=True)

# ---- Gráfico 3: Linha do Tempo (Verde + Pontos Amarelos) ----
with col_main_3:
    # st.markdown("### 📅 Histórico")
    if not df_tracks.empty:
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
            name='Faixas'
        ))
        
        fig_linha.update_layout(
            title='Histórico de Lançamentos',
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color=COR_TEXTO),
            xaxis_title='Ano',
            yaxis_title='Faixas lançadas',
            showlegend=False,
            height=400,
            margin=dict(l=0, r=0, t=40, b=0)
        )
        st.plotly_chart(fig_linha, use_container_width=True)

st.markdown("---")

# ========================================================
# SEÇÃO 3: DADOS DETALHADOS
# ========================================================

st.markdown("## 📋 Dados Detalhados")

if not df_tracks.empty:
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
        height=500
    )
else:
    st.info("Nenhuma faixa encontrada para exibir na tabela.")

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
