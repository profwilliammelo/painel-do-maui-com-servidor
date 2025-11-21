# 🇯🇲 MELODIA&BARULHO – Painel Interativo do Maui

Dashboard interativo desenvolvido em Python usando Streamlit para visualizar dados do artista Maui via API do Spotify.

## 🚀 Como Executar

### 1. Instalar Dependências

```bash
pip install -r requirements.txt
```

### 2. Configurar Credenciais do Spotify

As credenciais já estão no arquivo `.env`. Se preferir usar suas próprias:

1. Acesse [Spotify for Developers](https://developer.spotify.com/dashboard)
2. Crie um app
3. Copie o **Client ID** e **Client Secret**
4. Cole no arquivo `.env`

### 3. Executar o Dashboard

```bash
streamlit run app.py
```

O dashboard abrirá automaticamente no seu navegador em `http://localhost:8501`

## 📊 Funcionalidades

- **KPIs em Tempo Real**: Seguidores, Popularidade, Total de Faixas
- **Visualizações Interativas**:
  - Top 10 faixas mais populares
  - Faixas por álbum/projeto
  - Linha do tempo de lançamentos
- **Tabela de Dados**: Tabela interativa com todas as faixas
- **Atualização em Tempo Real**: Botão para recarregar dados do Spotify
- **Tema Dark Solar**: Design elegante inspirado no tema Solar

## 🎨 Tecnologias

- **Streamlit**: Framework para dashboards interativos
- **Spotipy**: Biblioteca Python para API do Spotify
- **Plotly**: Gráficos interativos
- **Pandas**: Manipulação de dados

## 👨‍💻 Autor

**Prof Dr William Melo | W-Black**  
MELODIA&BARULHO DATA ANALYTICS

---

💾 Powered by Spotify API
