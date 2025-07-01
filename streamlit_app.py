# -----------------------------------------------------------------------------
# DASHBOARD AGRÍCOLA DE GOIÁS CON STREAMLIT
# -----------------------------------------------------------------------------
# Descripción:
# Este script crea una aplicación web interactiva para visualizar datos agrícolas
# del estado de Goiás, Brasil, utilizando Streamlit, Pandas y Plotly.
#
# Autor: Gemini
# Fecha: 2024-07-31
#
# Instrucciones para Despliegue en Streamlit Community Cloud:
# 1. Crea un repositorio público en GitHub.
# 2. Sube los siguientes archivos y carpetas a tu repositorio:
#    - Este archivo (ej: streamlit_app.py) en la raíz.
#    - El archivo 'requirements.txt'.
#    - Una carpeta llamada 'data' que contenga los 4 archivos de Excel.
# 3. Ve a share.streamlit.io, regístrate con tu cuenta de GitHub.
# 4. Haz clic en "New app", selecciona tu repositorio y el archivo principal.
# 5. ¡Haz clic en "Deploy!".
# -----------------------------------------------------------------------------

import streamlit as st
import pandas as pd
import plotly.express as px
import os

# --- Configuración de la Página ---
# st.set_page_config se debe llamar al principio del script.
st.set_page_config(
    page_title="Dashboard Agrícola de Goiás",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Función de Carga de Datos con Caché ---
# @st.cache_data le dice a Streamlit que solo ejecute esta función una vez
# y guarde el resultado en caché. Esto mejora drásticamente el rendimiento.
@st.cache_data
def cargar_y_preparar_datos():
    """
    Carga los cuatro archivos de Excel desde una subcarpeta 'data', los limpia,
    renombra columnas y los une en un único DataFrame de pandas.
    """
    # Construir la ruta a la carpeta de datos
    base_path = "data"
    
    # Nombres de los archivos de Excel
    file_paths = {
        "Area": os.path.join(base_path, "datos_goias_areas.xlsx"),
        "Toneladas": os.path.join(base_path, "datos_goias_toneladas.xlsx"),
        "Valor_Produccion": os.path.join(base_path, "datos_goias_valor.xlsx"),
        "Rendimiento": os.path.join(base_path, "datos_goias_rendimiento.xlsx")
    }

    dataframes = []
    for metric, path in file_paths.items():
        try:
            df_temp = pd.read_excel(path)
            df_temp.columns = [col.strip() for col in df_temp.columns]
            df_temp.rename(columns={'Valor': metric}, inplace=True)
            df_temp.set_index(['Año', 'Cultivo', 'Municipio'], inplace=True)
            dataframes.append(df_temp)
        except FileNotFoundError:
            # Si un archivo no se encuentra, devuelve una tupla con None y el path del error
            return None, path

    df_merged = dataframes[0].join(dataframes[1:], how='outer')
    df_merged.fillna(0, inplace=True)
    df_merged.reset_index(inplace=True)

    df_merged['Año'] = df_merged['Año'].astype(int)
    numeric_cols = ['Area', 'Toneladas', 'Valor_Produccion', 'Rendimiento']
    for col in numeric_cols:
        df_merged[col] = pd.to_numeric(df_merged[col], errors='coerce').fillna(0)

    return df_merged, None

# --- Carga de Datos y Manejo de Errores ---
df, error_path = cargar_y_preparar_datos()

if df is None:
    st.error(f"**Error Crítico:** No se pudo encontrar el archivo de datos en la ruta esperada: `{error_path}`.")
    st.warning("Por favor, asegúrate de que los 4 archivos de Excel estén dentro de una carpeta llamada `data` en tu repositorio de GitHub.")
    st.stop() # Detiene la ejecución del script si los datos no se cargan

# --- Barra Lateral de Filtros (Sidebar) ---
st.sidebar.image("https://i.imgur.com/g2E24Tf.png", width=100) # Un logo simple
st.sidebar.title("Panel de Filtros 🗺️")

# Filtro de Cultivo
cultivo_seleccionado = st.sidebar.selectbox(
    "Selecciona un Cultivo:",
    options=sorted(df['Cultivo'].unique())
)

# Filtro de Municipio (dependiente del cultivo)
municipios_disponibles = sorted(df[df['Cultivo'] == cultivo_seleccionado]['Municipio'].unique())
municipio_seleccionado = st.sidebar.selectbox(
    "Selecciona un Municipio (o todos):",
    options=['Todos los Municipios'] + municipios_disponibles
)

# --- Filtrado del DataFrame Principal ---
if municipio_seleccionado == 'Todos los Municipios':
    df_filtrado = df[df['Cultivo'] == cultivo_seleccionado]
else:
    df_filtrado = df[(df['Cultivo'] == cultivo_seleccionado) & (df['Municipio'] == municipio_seleccionado)]

# --- Cuerpo Principal del Dashboard ---

# Título dinámico
st.title(f"🌾 Dashboard Agrícola: {cultivo_seleccionado}")
st.markdown(f"Análisis para **{municipio_seleccionado}**")
st.markdown("---")

# --- Tarjetas de Indicadores Clave (KPIs) ---
if not df_filtrado.empty:
    total_area = df_filtrado['Area'].sum()
    total_toneladas = df_filtrado['Toneladas'].sum()
    total_valor = df_filtrado['Valor_Produccion'].sum()
    # Promedio ponderado de rendimiento
    avg_rendimiento = (df_filtrado['Rendimiento'] * df_filtrado['Area']).sum() / total_area if total_area > 0 else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Área Total (ha)", f"{total_area:,.0f}")
    col2.metric("Producción Total (t)", f"{total_toneladas:,.0f}")
    col3.metric("Valor Total (R$ x1000)", f"{total_valor:,.0f}")
    col4.metric("Rendimiento Promedio (kg/ha)", f"{avg_rendimiento:,.0f}")
else:
    st.warning("No hay datos disponibles para la selección actual.")

st.markdown("---")

# --- Gráficos ---
col_graf1, col_graf2 = st.columns(2)

with col_graf1:
    st.subheader("📈 Evolución Anual de Métricas")
    if not df_filtrado.empty:
        # Agrupar datos por año para el gráfico de líneas
        time_series_data = df_filtrado.groupby('Año')[['Area', 'Toneladas', 'Valor_Produccion', 'Rendimiento']].sum().reset_index()
        fig_time_series = px.line(
            time_series_data,
            x='Año',
            y=['Area', 'Toneladas', 'Valor_Produccion', 'Rendimiento'],
            title=f'Evolución para {cultivo_seleccionado}',
            labels={'value': 'Valor', 'variable': 'Métrica'},
            template='plotly_white'
        )
        fig_time_series.update_layout(legend_title_text='Métricas')
        st.plotly_chart(fig_time_series, use_container_width=True)
    else:
        st.info("Selecciona un cultivo y municipio para ver la evolución.")

with col_graf2:
    st.subheader("📊 Comparativa de Municipios/Cultivos")
    # Selector para la métrica del gráfico de barras
    metrica_barra = st.selectbox(
        "Selecciona una métrica para comparar:",
        options=[
            ('Producción (Toneladas)', 'Toneladas'),
            ('Área Cosechada (ha)', 'Area'),
            ('Valor de Producción (R$ x1000)', 'Valor_Produccion'),
            ('Rendimiento (kg/ha)', 'Rendimiento')
        ],
        format_func=lambda x: x[0] # Muestra el nombre legible en el dropdown
    )
    
    if not df_filtrado.empty:
        # Lógica del gráfico de barras
        if municipio_seleccionado == 'Todos los Municipios':
            bar_data = df_filtrado.groupby('Municipio')[metrica_barra[1]].sum().nlargest(10).reset_index()
            bar_title = f'Top 10 Municipios por {metrica_barra[0]}'
            x_axis, y_axis = 'Municipio', metrica_barra[1]
        else:
            bar_data = df[df['Municipio'] == municipio_seleccionado].groupby('Cultivo')[metrica_barra[1]].sum().reset_index()
            bar_title = f'Comparativa de Cultivos en {municipio_seleccionado}'
            x_axis, y_axis = 'Cultivo', metrica_barra[1]

        fig_bar_chart = px.bar(
            bar_data, x=x_axis, y=y_axis, title=bar_title, template='plotly_white',
            color=y_axis, color_continuous_scale=px.colors.sequential.Viridis
        )
        fig_bar_chart.update_layout(coloraxis_showscale=False)
        st.plotly_chart(fig_bar_chart, use_container_width=True)
    else:
        st.info("Selecciona un cultivo y municipio para ver la comparativa.")

# --- Pie de Página ---
st.markdown("---")
st.write("Dashboard creado con Streamlit por Gemini.")
