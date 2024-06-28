import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.title("Dashboard Fincas")

# Function to load data
def load_data(file_path):
    return pd.read_excel(file_path, engine='openpyxl', sheet_name="COSTOS_QQ")

# Default file path
default_file = "/Users/josuer/Documents/DashBoard Fincas/Costos-Streamlit-Santa-Ana/Costos2022_2023 V8.xlsx"

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

# Mientras que el df no es nulo.
if df is not None:
    # Mostrar el DataFrame cargado
    st.write("DataFrame cargado:")
    
    #st.write(df)
    #st.header("Análisis de Ingresos")

    # Calcular ingresos totales
    ingresos_totales = df['INGRESO '].sum()
    st.metric("Ingresos Totales", f"${ingresos_totales:,.2f}")

    # Gráfico de ingresos por finca
    fig_ingresos = px.bar(df, x='NOMFIN', y='INGRESO ', title='Ingresos por Finca')
    st.plotly_chart(fig_ingresos)

    #### Análisis de Márgenes

    st.header("Análisis de Márgenes")

    # Calcular margen por finca
    df['Margen'] = df['INGRESO '] - df['TOTAL SIN INV']
    df['Margen %'] = (df['Margen'] / df['INGRESO ']) * 100

    # Mostrar márgenes
    fig_margenes = px.scatter(df, x='INGRESO ', y='Margen', 
                              size='AREA', color='REGION', 
                              hover_name='NOMFIN', 
                              title='Margen vs Ingresos por Finca')
    st.plotly_chart(fig_margenes)

    # Top 5 fincas con mejor margen porcentual
    top_margenes = df.nlargest(5, 'Margen %')
    st.write("Top 5 Fincas con Mejor Margen Porcentual:")
    st.write(top_margenes[['NOMFIN', 'Margen %', 'INGRESO ', 'TOTAL SIN INV']])

    #### Análisis por Región

    st.header("Análisis por Región")

    region_stats = df.groupby('REGION').agg({
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
