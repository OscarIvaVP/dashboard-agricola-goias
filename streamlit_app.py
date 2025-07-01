# -----------------------------------------------------------------------------
# DASHBOARD AGRÍCOLA DE GOIÁS COM STREAMLIT (VERSÃO COM MAPA)
# -----------------------------------------------------------------------------
# Descrição:
# Script final com mapa interativo, slider de anos, tabela de dados e
# paleta de cores ajustada para verde.
#
# Autor: Gemini
# Data: 2024-07-31
#
# Instruções para Implantação no Streamlit Community Cloud:
# 1. Crie um repositório público no GitHub.
# 2. Envie os seguintes arquivos e pastas para o seu repositório:
#    - Este arquivo (streamlit_app.py).
#    - O arquivo 'requirements.txt'.
#    - Uma pasta 'data' com os 4 arquivos Excel.
#    - Uma pasta 'assets' com o logo (logo.png) e o GeoJSON (geojs-52-mun.json).
# 3. Acesse share.streamlit.io e implante sua aplicação.
# -----------------------------------------------------------------------------

import streamlit as st
import pandas as pd
import plotly.express as px
import os
import json

# --- Configuração da Página ---
st.set_page_config(
    page_title="Dashboard Agrícola de Goiás",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Funções de Carregamento de Dados com Cache ---
@st.cache_data
def carregar_e_preparar_dados():
    base_path = "data"
    file_paths = {
        "Area": os.path.join(base_path, "datos_goias_areas.xlsx"),
        "Toneladas": os.path.join(base_path, "datos_goias_toneladas.xlsx"),
        "Valor_Produccion": os.path.join(base_path, "datos_goias_valor.xlsx"),
        "Rendimento": os.path.join(base_path, "datos_goias_rendimiento.xlsx")
    }
    dataframes = []
    for metric, path in file_paths.items():
        try:
            df_temp = pd.read_excel(path)
            df_temp.columns = [col.strip().replace('Año', 'Ano').replace('Cultivo', 'Cultura') for col in df_temp.columns]
            df_temp.rename(columns={'Valor': metric, 'Municipio': 'Município'}, inplace=True)
            df_temp.set_index(['Ano', 'Cultura', 'Município'], inplace=True)
            dataframes.append(df_temp)
        except FileNotFoundError:
            return None, path
    df_merged = dataframes[0].join(dataframes[1:], how='outer').fillna(0).reset_index()
    df_merged['Ano'] = df_merged['Ano'].astype(int)
    for col in ['Area', 'Toneladas', 'Valor_Produccion', 'Rendimento']:
        df_merged[col] = pd.to_numeric(df_merged[col], errors='coerce').fillna(0)
    return df_merged, None

@st.cache_data
def carregar_geojson():
    """Carrega o arquivo GeoJSON dos municípios de Goiás."""
    path = "assets/geojs-52-mun.json"
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return None

# --- Carregamento de Dados e Tratamento de Erros ---
df, error_path = carregar_e_preparar_dados()
geojson_data = carregar_geojson()

if df is None:
    st.error(f"**Erro Crítico:** Não foi possível encontrar o arquivo de dados: `{error_path}`.")
    st.stop()
if geojson_data is None:
    st.error("**Erro Crítico:** Não foi possível encontrar o arquivo `geojs-52-mun.json` na pasta `assets`.")
    st.warning("Por favor, certifique-se de que o arquivo GeoJSON está na pasta correta.")
    st.stop()

# --- Barra Lateral de Filtros (Sidebar) ---
st.sidebar.image("assets/logo.png", width=200)
st.sidebar.title("Painel de Filtros 🗺️")
cultura_selecionada = st.sidebar.selectbox("Selecione uma Cultura:", options=sorted(df['Cultura'].unique()))
municipios_disponiveis = sorted(df[df['Cultura'] == cultura_selecionada]['Município'].unique())
municipio_selecionado = st.sidebar.selectbox("Selecione um Município (ou todos):", options=['Todos os Municípios'] + municipios_disponiveis)
min_ano, max_ano = int(df['Ano'].min()), int(df['Ano'].max())
ano_selecionado = st.sidebar.select_slider("Selecione um Intervalo de Anos para os gráficos:", options=range(min_ano, max_ano + 1), value=(min_ano, max_ano))

# --- Filtragem do DataFrame Principal ---
if municipio_selecionado == 'Todos os Municípios':
    df_filtrado_base = df[df['Cultura'] == cultura_selecionada]
else:
    df_filtrado_base = df[(df['Cultura'] == cultura_selecionada) & (df['Município'] == municipio_selecionado)]
df_filtrado = df_filtrado_base[(df_filtrado_base['Ano'] >= ano_selecionado[0]) & (df_filtrado_base['Ano'] <= ano_selecionado[1])]

# --- Corpo Principal do Dashboard ---
st.title("🌾 Dashboard Agrícola do Estado de Goiás")
st.subheader(cultura_selecionada)
st.markdown(f"Análise para **{municipio_selecionado}** entre **{ano_selecionado[0]}** e **{ano_selecionado[1]}**")
st.markdown("---")

# --- KPIs baseados no último ano do intervalo selecionado ---
if not df_filtrado.empty:
    latest_year_in_range = int(df_filtrado['Ano'].max())
    df_ultimo_ano = df_filtrado[df_filtrado['Ano'] == latest_year_in_range]
    st.subheader(f"Indicadores Chave (KPIs) para o Ano de {latest_year_in_range}")
    if not df_ultimo_ano.empty:
        total_area = df_ultimo_ano['Area'].sum()
        total_toneladas = df_ultimo_ano['Toneladas'].sum()
        total_valor = df_ultimo_ano['Valor_Produccion'].sum()
        avg_rendimento = (df_ultimo_ano['Rendimento'] * df_ultimo_ano['Area']).sum() / total_area if total_area > 0 else 0
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Área Total (ha)", f"{total_area:,.0f}")
        col2.metric("Produção Total (t)", f"{total_toneladas:,.0f}")
        col3.metric("Valor Total (R$ x1000)", f"{total_valor:,.0f}")
        col4.metric("Rendimento Médio (kg/ha)", f"{avg_rendimento:,.0f}")
else:
    st.warning("Não há dados disponíveis para a cultura, município e período selecionados.")

# --- Abas para organizar o conteúdo ---
tab_analise, tab_mapa = st.tabs(["📊 Análise de Gráficos", "🗺️ Mapa Interativo"])

with tab_analise:
    col_graf1, col_graf2 = st.columns(2)
    def calcular_metricas_anuais(group):
        area_sum = group['Area'].sum()
        rendimento_ponderado = (group['Rendimento'] * group['Area']).sum() / area_sum if area_sum > 0 else 0
        return pd.Series({'Area': area_sum, 'Toneladas': group['Toneladas'].sum(), 'Valor_Produccion': group['Valor_Produccion'].sum(), 'Rendimento': rendimento_ponderado})

    with col_graf1:
        st.subheader("📈 Evolução Anual das Métricas")
        if not df_filtrado.empty:
            time_series_data = df_filtrado.groupby('Ano').apply(calcular_metricas_anuais).reset_index()
            fig_time_series = px.line(time_series_data, x='Ano', y=['Area', 'Toneladas', 'Valor_Produccion', 'Rendimento'], title=f'Evolução para {cultura_selecionada}', labels={'value': 'Valor', 'variable': 'Métrica', 'Ano': 'Ano'}, template='plotly_white')
            fig_time_series.update_layout(legend_title_text='Métricas')
            st.plotly_chart(fig_time_series, use_container_width=True)

    with col_graf2:
        if not df_filtrado.empty:
            latest_year_in_range = int(df_filtrado['Ano'].max())
            df_ultimo_ano_grafico = df_filtrado[df_filtrado['Ano'] == latest_year_in_range]
            st.subheader(f"📊 Comparativo para o Ano de {latest_year_in_range}")
            metrica_barra = st.selectbox("Selecione uma métrica para comparar:", options=[('Produção (Toneladas)', 'Toneladas'), ('Área Colhida (ha)', 'Area'), ('Valor da Produção (R$ x1000)', 'Valor_Produccion'), ('Rendimento (kg/ha)', 'Rendimento')], format_func=lambda x: x[0], key='select_metrica_barra')
            if not df_ultimo_ano_grafico.empty:
                metric_key = metrica_barra[1]
                if municipio_selecionado == 'Todos os Municípios':
                    agg_func = 'mean' if metric_key == 'Rendimento' else 'sum'
                    bar_data = df_ultimo_ano_grafico.groupby('Município').agg({metric_key: agg_func}).nlargest(10, columns=metric_key).reset_index()
                    bar_title = f'Top 10 Municípios por {metrica_barra[0]}'
                    x_axis, y_axis = 'Município', metric_key
                else:
                    df_municipio_ultimo_ano = df[(df['Município'] == municipio_selecionado) & (df['Ano'] == latest_year_in_range)]
                    agg_func = 'mean' if metric_key == 'Rendimento' else 'sum'
                    bar_data = df_municipio_ultimo_ano.groupby('Cultura').agg({metric_key: agg_func}).reset_index()
                    bar_title = f'Comparativo de Culturas em {municipio_selecionado}'
                    x_axis, y_axis = 'Cultura', metric_key
                # AJUSTE: Mudar a escala de cores do gráfico de barras para verde
                fig_bar_chart = px.bar(bar_data, x=x_axis, y=y_axis, title=bar_title, template='plotly_white', color=y_axis, color_continuous_scale="Greens")
                fig_bar_chart.update_layout(coloraxis_showscale=False)
                st.plotly_chart(fig_bar_chart, use_container_width=True)

with tab_mapa:
    absolute_latest_year = int(df['Ano'].max())
    st.subheader(f"🗺️ Análise Geográfica por Município ({absolute_latest_year})")
    st.markdown(f"Exibindo dados para o último ano registrado: **{absolute_latest_year}**. O filtro de anos do menu lateral não afeta este mapa.")
    
    df_mapa = df[(df['Cultura'] == cultura_selecionada) & (df['Ano'] == absolute_latest_year)]
    
    if not df_mapa.empty:
        metrica_mapa = st.selectbox("Selecione uma métrica para visualizar no mapa:", options=[('Produção (Toneladas)', 'Toneladas'), ('Área Colhida (ha)', 'Area'), ('Valor da Produção (R$ x1000)', 'Valor_Produccion'), ('Rendimento (kg/ha)', 'Rendimento')], format_func=lambda x: x[0], key='select_metrica_mapa')
        
        agg_func_mapa = 'mean' if metrica_mapa[1] == 'Rendimento' else 'sum'
        df_mapa_agregado = df_mapa.groupby('Município').agg({metrica_mapa[1]: agg_func_mapa}).reset_index()

        # AJUSTE: Mudar a escala de cores do mapa para verde
        fig_mapa = px.choropleth_mapbox(
            df_mapa_agregado,
            geojson=geojson_data,
            locations='Município',
            featureidkey='properties.name',
            color=metrica_mapa[1],
            color_continuous_scale="Greens",
            mapbox_style="carto-positron",
            zoom=4.5,
            center={"lat": -15.9, "lon": -49.8},
            opacity=0.6,
            labels={metrica_mapa[1]: metrica_mapa[0]},
            hover_name='Município'
        )
        fig_mapa.update_layout(
            margin={"r":0,"t":40,"l":0,"b":0},
            title_text=f'{metrica_mapa[0]} por Município em {absolute_latest_year}',
            title_x=0.5
        )
        st.plotly_chart(fig_mapa, use_container_width=True)
    else:
        st.info(f"Não há dados para exibir no mapa para a cultura '{cultura_selecionada}' no ano de {absolute_latest_year}.")

# --- Tabela de Dados Detalhada ---
with st.expander("Ver Tabela de Dados Detalhada 🕵️‍♀️"):
    st.dataframe(df_filtrado)

# --- Rodapé ---
st.markdown("---")
st.write("Idealizado por Oscar Ivan Vargas Pineda. Desenvolvido com o auxílio de Google Gemini e Streamlit.")
