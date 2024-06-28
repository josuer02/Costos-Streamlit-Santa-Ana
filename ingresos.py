import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.title("Dashboard Fincas")

# Function to load data
def load_data(file_path):
    return pd.read_excel(file_path, engine='openpyxl', sheet_name="COSTOS_QQ")

# Default file path
default_file = st.secrets["default_file_path"]

# Check if default file exists
if os.path.exists(default_file):
    df = load_data(default_file)
    st.success("Archivo base cargado correctamente!")
else:
    st.warning("Archivo base no encontrado. Porfavor suba el archivo.")
    df = None

# File uploader for user to choose a different file
uploaded_file = st.file_uploader("Eliga otro archivo más reciente (opcional)", type="xlsx")

if uploaded_file is not None:
    df = load_data(uploaded_file)
    st.success("Archivo cargado correctamente!")

# While df is not None
if df is not None:
    #### Filtro por GRUPO
    st.header("Filtro por GRUPO")
    
    # Get unique values from GRUPO column
    grupos = df['GRUPO'].unique().tolist()
    
    # Create a multiselect widget for GRUPO
    selected_grupos = st.multiselect("Seleccione los GRUPOs a incluir:", grupos, default=grupos)
    
    # Filter the dataframe based on selected GRUPOs
    df_filtered = df[df['GRUPO'].isin(selected_grupos)]
    
    # Show the number of farms included
    st.write(f"Número de fincas incluidas: {len(df_filtered)}")

    #### Análisis de Ingresos
    st.header("Análisis de Ingresos")

    # Calculate total income
    ingresos_totales = df_filtered['INGRESO '].sum()
    st.metric("Ingresos Totales", f"${ingresos_totales:,.2f}")

    # Income chart by farm
    fig_ingresos = px.bar(df_filtered, x='NOMFIN', y='INGRESO ', title='Ingresos por Finca')
    st.plotly_chart(fig_ingresos)

    #### Análisis de Márgenes
    st.header("Análisis de Márgenes")

    # Calculate margin by farm
    df_filtered['Margen'] = df_filtered['INGRESO '] - df_filtered['TOTAL SIN INV']
    df_filtered['Margen %'] = (df_filtered['Margen'] / df_filtered['INGRESO ']) * 100

    # Show margins
    fig_margenes = px.scatter(df_filtered, x='INGRESO ', y='Margen', 
                              size='AREA', color='REGION', 
                              hover_name='NOMFIN', 
                              title='Margen vs Ingresos por Finca')
    st.plotly_chart(fig_margenes)

    # Top 5 farms with best percentage margin
    top_margenes = df_filtered.nlargest(5, 'Margen %')
    st.write("Top 5 Fincas con Mejor Margen Porcentual:")
    st.write(top_margenes[['NOMFIN', 'Margen %', 'INGRESO ', 'TOTAL SIN INV']])

    #### Análisis por Región
    st.header("Análisis por Región")

    region_stats = df_filtered.groupby('REGION').agg({
        'INGRESO ': 'sum',
        'TOTAL SIN INV': 'sum',
        'AREA': 'sum'
    }).reset_index()

    region_stats['Margen Regional'] = region_stats['INGRESO '] - region_stats['TOTAL SIN INV']
    region_stats['Margen % Regional'] = (region_stats['Margen Regional'] / region_stats['INGRESO ']) * 100

    fig_region = px.bar(region_stats, x='REGION', y=['INGRESO ', 'TOTAL SIN INV'], 
                        title='Ingresos y Costos por Región',
                        barmode='group')
    st.plotly_chart(fig_region)

    st.write("Estadísticas por Región:")
    st.write(region_stats)
