# -----------------------------------------------------------------------------
# DASHBOARD AGRÍCOLA DE GOIÁS COM STREAMLIT (VERSÃO AJUSTADA E EM PORTUGUÊS)
# -----------------------------------------------------------------------------
# Descrição:
# Script com slider de anos e tabela de dados interativa.
# KPIs e gráficos de barras refletem o último ano do intervalo selecionado.
#
# Autor: Gemini
# Data: 2024-07-31
#
# Instruções para Implantação no Streamlit Community Cloud:
# 1. Crie um repositório público no GitHub.
# 2. Envie os seguintes arquivos e pastas para o seu repositório:
#    - Este arquivo (ex: streamlit_app.py) na raiz.
#    - O arquivo 'requirements.txt'.
#    - Uma pasta chamada 'data' contendo os 4 arquivos Excel.
#    - Uma pasta chamada 'assets' contendo o seu logo (ex: logo.png).
# 3. Acesse share.streamlit.io, faça login com sua conta do GitHub.
# 4. Clique em "New app", selecione seu repositório e o arquivo principal.
# 5. Clique em "Deploy!".
# -----------------------------------------------------------------------------

import streamlit as st
import pandas as pd
import plotly.express as px
import os

# --- Configuração da Página ---
st.set_page_config(
    page_title="Dashboard Agrícola de Goiás",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Função de Carregamento de Dados com Cache ---
@st.cache_data
def carregar_e_preparar_dados():
    """
    Carrega os quatro arquivos Excel de uma subpasta 'data', os limpa,
    renomeia colunas e os une em um único DataFrame do pandas.
    """
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
            # Renomear colunas para o português
            df_temp.columns = [col.strip().replace('Año', 'Ano').replace('Cultivo', 'Cultura') for col in df_temp.columns]
            df_temp.rename(columns={'Valor': metric, 'Municipio': 'Município'}, inplace=True)
            df_temp.set_index(['Ano', 'Cultura', 'Município'], inplace=True)
            dataframes.append(df_temp)
        except FileNotFoundError:
            return None, path

    df_merged = dataframes[0].join(dataframes[1:], how='outer')
    df_merged.fillna(0, inplace=True)
    df_merged.reset_index(inplace=True)
    df_merged['Ano'] = df_merged['Ano'].astype(int)
    numeric_cols = ['Area', 'Toneladas', 'Valor_Produccion', 'Rendimento']
    for col in numeric_cols:
        df_merged[col] = pd.to_numeric(df_merged[col], errors='coerce').fillna(0)
    return df_merged, None

# --- Carregamento de Dados e Tratamento de Erros ---
df, error_path = carregar_e_preparar_dados()

if df is None:
    st.error(f"**Erro Crítico:** Não foi possível encontrar o arquivo de dados no caminho esperado: `{error_path}`.")
    st.warning("Por favor, certifique-se de que os 4 arquivos Excel estão dentro de uma pasta chamada `data` em seu repositório do GitHub.")
    st.stop()

# --- Barra Lateral de Filtros (Sidebar) ---
st.sidebar.image("assets/logo.png", width=100)
st.sidebar.title("Painel de Filtros 🗺️")

cultura_selecionada = st.sidebar.selectbox(
    "Selecione uma Cultura:",
    options=sorted(df['Cultura'].unique())
)

municipios_disponiveis = sorted(df[df['Cultura'] == cultura_selecionada]['Município'].unique())
municipio_selecionado = st.sidebar.selectbox(
    "Selecione um Município (ou todos):",
    options=['Todos os Municípios'] + municipios_disponiveis
)

# NOVO: Filtro por intervalo de anos com um slider
min_ano = int(df['Ano'].min())
max_ano = int(df['Ano'].max())
ano_selecionado = st.sidebar.select_slider(
    "Selecione um Intervalo de Anos:",
    options=range(min_ano, max_ano + 1),
    value=(min_ano, max_ano)
)

# --- Filtragem do DataFrame Principal ---
# Filtra primeiro por cultura e município
if municipio_selecionado == 'Todos os Municípios':
    df_filtrado_base = df[df['Cultura'] == cultura_selecionada]
else:
    df_filtrado_base = df[(df['Cultura'] == cultura_selecionada) & (df['Município'] == municipio_selecionado)]

# Aplica o filtro de anos ao resultado anterior
df_filtrado = df_filtrado_base[
    (df_filtrado_base['Ano'] >= ano_selecionado[0]) &
    (df_filtrado_base['Ano'] <= ano_selecionado[1])
]


# --- Corpo Principal do Dashboard ---
st.title(f"🌾 Dashboard Agrícola: {cultura_selecionada}")
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
        st.warning(f"Não há dados disponíveis para o ano de {latest_year_in_range} com a seleção atual.")
else:
    st.warning("Não há dados disponíveis para a cultura, município e período selecionados.")


st.markdown("---")

# --- Gráficos ---
col_graf1, col_graf2 = st.columns(2)

def calcular_metricas_anuais(group):
    area_sum = group['Area'].sum()
    if area_sum > 0:
        rendimento_ponderado = (group['Rendimento'] * group['Area']).sum() / area_sum
    else:
        rendimento_ponderado = 0
    return pd.Series({
        'Area': area_sum,
        'Toneladas': group['Toneladas'].sum(),
        'Valor_Produccion': group['Valor_Produccion'].sum(),
        'Rendimento': rendimento_ponderado
    })

with col_graf1:
    st.subheader("📈 Evolução Anual das Métricas")
    if not df_filtrado.empty:
        time_series_data = df_filtrado.groupby('Ano').apply(calcular_metricas_anuais).reset_index()
        fig_time_series = px.line(
            time_series_data, x='Ano', y=['Area', 'Toneladas', 'Valor_Produccion', 'Rendimento'],
            title=f'Evolução para {cultura_selecionada}',
            labels={'value': 'Valor', 'variable': 'Métrica', 'Ano': 'Ano'},
            template='plotly_white'
        )
        fig_time_series.update_layout(legend_title_text='Métricas')
        st.plotly_chart(fig_time_series, use_container_width=True)
    else:
        st.info("Selecione um período para ver a evolução.")

with col_graf2:
    if not df_filtrado.empty:
        latest_year_in_range = int(df_filtrado['Ano'].max())
        df_ultimo_ano_grafico = df_filtrado[df_filtrado['Ano'] == latest_year_in_range]
        st.subheader(f"📊 Comparativo para o Ano de {latest_year_in_range}")
        metrica_barra = st.selectbox(
            "Selecione uma métrica para comparar:",
            options=[
                ('Produção (Toneladas)', 'Toneladas'), ('Área Colhida (ha)', 'Area'),
                ('Valor da Produção (R$ x1000)', 'Valor_Produccion'), ('Rendimento (kg/ha)', 'Rendimento')
            ],
            format_func=lambda x: x[0]
        )
        
        if not df_ultimo_ano_grafico.empty:
            metric_key = metrica_barra[1]
            if municipio_selecionado == 'Todos os Municípios':
                aggregation_func = 'mean' if metric_key == 'Rendimento' else 'sum'
                bar_data = df_ultimo_ano_grafico.groupby('Município').agg({metric_key: aggregation_func}).nlargest(10, columns=metric_key).reset_index()
                bar_title = f'Top 10 Municípios por {metrica_barra[0]}'
                x_axis, y_axis = 'Município', metric_key
            else:
                df_municipio_ultimo_ano = df[(df['Município'] == municipio_selecionado) & (df['Ano'] == latest_year_in_range)]
                aggregation_func = 'mean' if metric_key == 'Rendimento' else 'sum'
                bar_data = df_municipio_ultimo_ano.groupby('Cultura').agg({metric_key: aggregation_func}).reset_index()
                bar_title = f'Comparativo de Culturas em {municipio_selecionado}'
                x_axis, y_axis = 'Cultura', metric_key
            
            fig_bar_chart = px.bar(
                bar_data, x=x_axis, y=y_axis, title=bar_title, template='plotly_white',
                color=y_axis, color_continuous_scale=px.colors.sequential.Viridis
            )
            fig_bar_chart.update_layout(coloraxis_showscale=False)
            st.plotly_chart(fig_bar_chart, use_container_width=True)
        else:
            st.info("Não há dados para comparar no último ano do intervalo.")

# --- NOVO: Tabela de Dados Detalhada ---
st.markdown("---")
with st.expander("Ver Tabela de Dados Detalhada 🕵️‍♀️"):
    # Mostra o dataframe filtrado, que já corresponde a todas as seleções
    st.dataframe(df_filtrado)

# --- Rodapé ---
st.markdown("---")
st.write("Idealizado por Oscar Ivan Vargas Pineda. Desenvolvido com o auxílio de IA e Streamlit.")
