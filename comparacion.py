import math
import streamlit as st
import pandas as pd
import folium
import numpy as np
import matplotlib.pyplot as plt
import altair as alt
from streamlit_folium import st_folium
from math import radians, cos, sin, sqrt, atan2
import os

# Function to load data
def load_data(file_path):
    return pd.read_excel(file_path, engine='openpyxl', sheet_name='COSTOS_QQ')

def costo_por_area(costo, area):
    return costo * area if area > 0 else 0

# Usar los inputs existentes para los datos base
precio_ny_11 = st.session_state.get('precio_ny_11', 15.00)
white_premium = st.session_state.get('white_premium', 4.78)
prima_vhp = st.session_state.get('prima_vhp', 1.66)
precio_local = st.session_state.get('precio_local', 34.00)

TC = 2204.62
TM = 2000

# Default file path
default_file = st.secrets['default_file_path']
st.title("Comparación Fincas")

# Check if default file exists and load it
if os.path.exists(default_file):
    st.session_state.df = load_data(default_file)
    st.success("Archivo predeterminado cargado exitosamente!")
else:
    st.warning("Archivo predeterminado no encontrado. Por favor, suba un archivo.")

# uploader por si no tienen el documento base
uploaded_file = st.file_uploader("Elija un archivo Excel diferente (opcional)", type="xlsx")

if uploaded_file is not None:
    st.session_state.df = load_data(uploaded_file)
    st.success("Archivo del usuario cargado exitosamente!")

st.sidebar.header("Inputs")

st.sidebar.subheader("Inputs Técnicos")
area_arrendada = st.sidebar.number_input("Área Arrendada (Has):", value=400, step=100)
area_productiva = st.sidebar.number_input("Área Productiva (Has):", value=360, step=100)
rendimiento = st.sidebar.number_input("Rendimiento (Lbs/TC):", value=220.0, step=0.1, format="%.1f")
productividad = st.sidebar.number_input("Productividad (TCH):", value=115)
tipo_de_cambio = st.sidebar.number_input("Tipo de Cambio:", value=7.85, step=0.01, format="%.2f")

cat_option = st.sidebar.selectbox("CAT:", ["Con depreciación", "Sin depreciación"])
cat_value = 7.61 if cat_option == "Con depreciación" else 4.8

    # Inputs de manejo
st.sidebar.subheader("Manejo Agrícola")
costo_riego = st.sidebar.number_input("Costo de riego (Ha)", min_value=0.0, value=0.0, step=0.01)
costo_fertilizacion = st.sidebar.number_input("Costo de fertilización (Ha)", min_value=0.0, value=0.0, step=0.01)
costo_malezas = st.sidebar.number_input("Costo de control de malezas (Ha)", min_value=0.0, value=0.0, step=0.01)
costo_plagas = st.sidebar.number_input("Costo de manejo de plagas (Ha)", min_value=0.0, value=0.0, step=0.01)
costo_administracion = st.sidebar.number_input("Costo de administración (Ha)", min_value=0.0, value=0.0, step=0.01)

    # Inputs de arrendamiento
st.sidebar.subheader("Arrendamiento")
costo_arrendamiento_fijo_mz = st.sidebar.number_input("Costo de arrendamiento fijo (Mz)", min_value=0.0, value=0.0, step=0.01)
costo_arrendamiento_fijo = math.ceil(costo_arrendamiento_fijo_mz * 1.43115)

base_arrend = st.sidebar.number_input("Ingrese el precio base: ", min_value=0.0, value=0.0, step=0.01)
incremento_arrend = st.sidebar.number_input("Ingrese el incremento negociado: ", min_value=0.0, value=0.0, step=0.01)
precio_ny_11_arrend = st.sidebar.number_input("Ingrese el precioNY11: ", min_value=0.0, value=precio_ny_11, step=0.01)

    # Inputs de inversiones
st.sidebar.subheader("Inversiones")
costo_capex = st.sidebar.number_input("Costo CAPEX (Ha)", min_value=0.0, value=0.0, step=0.01)
costo_renovacion = st.sidebar.number_input("Costo de renovación", min_value=0.0, value=0.0, step=0.01)

    #Inputs de contribuciones.0
st.sidebar.subheader("Precios para calculo de contribuciones")
precio_mwh = st.sidebar.number_input("Precio MWh", min_value=0.0, value=70.0, step=0.01)
precio_tm_melaza= st.sidebar.number_input("Precio TM Melaza", min_value=0.0, value=70.0, step=0.01)

    # Contenido principal
st.title("Análisis de Costos e Ingresos")

    # Cálculos iniciales
caña_tc = area_productiva * productividad
azucar_qq = caña_tc * rendimiento* (22.0462/21.739)/ 100
azucar_tc = azucar_qq / 21.739

total_cat = cat_value * caña_tc
cat_ha = total_cat / area_productiva
cat_qq = total_cat / azucar_qq

    # Mostrar resultados iniciales
st.subheader("Resultados Iniciales")
st.write(f"Caña TC: {caña_tc:,.2f}")
st.write(f"Azúcar QQ: {azucar_qq:,.2f}")
st.write(f"Azúcar TC: {azucar_tc:,.2f}")

    # CAT
st.subheader("CAT (Costo Agrícola Total)")
df_costos_v1 = pd.DataFrame({
    'Tipo CAT': ['CAT'],
    'Por Ha': [cat_ha],
    'Por TC': [cat_value],
    'Por QQ': [cat_qq],
    'Total': [total_cat]
})
st.write(df_costos_v1)

    # Manejo Agrícola
st.subheader("Manejo Agrícola")
costo_total_agri = costo_riego + costo_fertilizacion + costo_malezas + costo_plagas + costo_administracion

costo_riego_por_area = costo_por_area(costo_riego, area_productiva)
costo_fertilizacion_por_area = costo_por_area(costo_fertilizacion, area_productiva)
costo_malezas_por_area = costo_por_area(costo_malezas, area_productiva)
costo_plagas_por_area = costo_por_area(costo_plagas, area_productiva)
costo_administracion_por_area = costo_por_area(costo_administracion, area_productiva)

costo_total_agri = costo_riego + costo_fertilizacion + costo_malezas + costo_plagas + costo_administracion
costo_total_agri_p_area = costo_riego_por_area + costo_fertilizacion_por_area + costo_malezas_por_area + costo_plagas_por_area+costo_administracion_por_area
costo_agri_qq_total = costo_total_agri_p_area / azucar_qq


st.write(f"Costo total manejo agrícola (Ha): ${costo_total_agri:.2f}")

    # Arrendamiento
st.subheader("Arrendamiento")

costo_arrendamiento_variable = 0
if precio_ny_11_arrend > base_arrend: 
    costo_arrendamiento_variable = (precio_ny_11_arrend - base_arrend)*incremento_arrend
else:
    costo_arrendamiento_variable = 0

costo_arrendamiento_total = costo_arrendamiento_fijo + costo_arrendamiento_variable

costo_arrendamiento_por_area_fijo = costo_por_area(costo_arrendamiento_fijo, area_arrendada)
costo_arrendamiento_por_area_variable = costo_por_area(costo_arrendamiento_variable, area_arrendada)

costo_arrendamiento_por_area_total = costo_arrendamiento_por_area_variable+costo_arrendamiento_por_area_fijo
costo_arrendamiento_tot_qq = costo_arrendamiento_por_area_total / azucar_qq

st.write(f"Costo total arrendamiento (Ha): ${costo_arrendamiento_total:.2f}")
#
# st.write("Costo Fijo", costo_arrendamiento_fijo)
#st.write("Costo Variable", costo_arrendamiento_variable)


# Inversiones
st.subheader("Inversiones - Amortizacion por Ha")
costo_inversiones_total = costo_capex + costo_renovacion

costo_capex_por_area = costo_por_area(costo_capex, area_productiva)
costo_renovacion_por_area = costo_por_area(costo_renovacion, area_productiva)
costo_inversiones_p_area = costo_capex_por_area+costo_renovacion_por_area
costo_inversiones_qq = costo_inversiones_p_area/azucar_qq

st.write(f"Costo total inversiones (Ha): ${costo_inversiones_total:.2f}")

# Costo total en patio
costo_de_caña_en_patio = cat_ha + costo_total_agri + costo_arrendamiento_total + costo_inversiones_total
costo_de_caña_en_patio_qq = costo_inversiones_qq + costo_arrendamiento_tot_qq + costo_agri_qq_total + cat_qq

st.markdown(f"<h3 style='color: green;'>Costo total en patio (Ha): ${costo_de_caña_en_patio:,.2f}</h3>", unsafe_allow_html=True)

st.subheader("Análisis de Ingresos")



# Crear un DataFrame con los datos de ingresos
df_ingresos = pd.DataFrame({
    'Tipo': ['Crudo', 'VHP', 'Refino', 'Local'],
    'Precio': [precio_ny_11, precio_ny_11 + prima_vhp, precio_ny_11 + white_premium, precio_local],
    'Local': [0.0421052631578947, 0.115789473684211, 0.336842105263158, 0.505263157894737],
    'Solo exp': [0.0851063829787234, 0.234042553191489, 0.680851063829787, 0.00],
    'Crudo': [1.00, 0.00, 0.00, 0.00]
})

base_fabrica = 1.82939469645536

df_costos_fabrica = pd.DataFrame({
    'Costo': [base_fabrica, base_fabrica+0.815424721259047, base_fabrica+2.02016467433601, base_fabrica+0.439909136083208],
    'Local': [0.0421052631578947, 0.115789473684211, 0.336842105263158, 0.505263157894737],
    'Solo exp': [0.0851063829787234, 0.234042553191489, 0.680851063829787, 0.00],
    'Crudo': [1.00, 0.00, 0.00, 0.00]
})

df_costo_transporte = pd.DataFrame({
    'Costo': [0.25, 0.25, 0.25, 0.08],
    'Local': [0.0421052631578947, 0.115789473684211, 0.336842105263158, 0.505263157894737],
    'Solo exp': [0.0851063829787234, 0.234042553191489, 0.680851063829787, 0.00],
    'Crudo': [1.00, 0.00, 0.00, 0.00]
})
# Selector para el escenario
escenario = st.selectbox("Seleccione el escenario:", ["Comercialización", "a 15$ el Crudo", "Ingreso Manual"])

# Selector para el tipo de venta
tipo_venta = st.selectbox("Tipo de venta:", ["Con Local", "Solo Exportación", "Solo Crudo"])

if escenario == "a 15$ el Crudo":
    df_ingresos.loc[df_ingresos['Tipo'] == 'Crudo', 'Precio'] = 15.00
    df_ingresos.loc[df_ingresos['Tipo'] == 'VHP', 'Precio'] = 15.00 + prima_vhp
    df_ingresos.loc[df_ingresos['Tipo'] == 'Refino', 'Precio'] = 15.00 + white_premium
elif escenario == "Ingreso Manual":
    precio_ny_11 = st.number_input("Precio NY 11:", value=precio_ny_11, step=0.01, format="%.2f")
    white_premium = st.number_input("White Premium:", value=white_premium, step=0.01, format="%.2f")
    prima_vhp = st.number_input("Prima VHP:", value=prima_vhp, step=0.01, format="%.2f")
    precio_local = st.number_input("Precio Local:", value=precio_local, step=0.01, format="%.2f")
    
    df_ingresos.loc[df_ingresos['Tipo'] == 'Crudo', 'Precio'] = precio_ny_11
    df_ingresos.loc[df_ingresos['Tipo'] == 'VHP', 'Precio'] = precio_ny_11 + prima_vhp
    df_ingresos.loc[df_ingresos['Tipo'] == 'Refino', 'Precio'] = precio_ny_11 + white_premium
    df_ingresos.loc[df_ingresos['Tipo'] == 'Local', 'Precio'] = precio_local

if tipo_venta == "Con Local":
    df_ingresos['Porcentaje'] = df_ingresos['Local']
    df_costos_fabrica['Porcentaje'] = df_costos_fabrica['Local']
    df_costo_transporte['Porcentaje'] = df_costo_transporte['Local']

elif tipo_venta == "Solo Exportación":
    df_ingresos['Porcentaje'] = df_ingresos['Solo exp']
    df_costos_fabrica['Porcentaje'] = df_costos_fabrica['Solo exp']
    df_costo_transporte['Porcentaje'] = df_costo_transporte['Solo exp']


else:  # Solo Crudo
    df_ingresos['Porcentaje'] = df_ingresos['Crudo']
    df_costos_fabrica['Porcentaje'] = df_costos_fabrica['Crudo']
    df_costo_transporte['Porcentaje'] = df_costo_transporte['Crudo']


df_costos_fabrica['Ponderado'] = df_costos_fabrica['Costo'] * df_costos_fabrica['Porcentaje']
total_ponderado_fabrica = df_costos_fabrica['Ponderado'].sum()

st.subheader("Fabrica")
st.write(df_costos_fabrica[['Costo', 'Ponderado']])
st.write(f"Total Ponderado Fabrica (qq): ${total_ponderado_fabrica:.2f}")
#st.write(df_costos_fabrica)
total_fabrica = azucar_qq * df_costos_fabrica['Ponderado']

#st.write(total_fabrica)

df_costo_transporte['Ponderado'] = df_costo_transporte['Costo'] * df_costo_transporte['Porcentaje']
total_ponderado_transporte = df_costo_transporte['Ponderado'].sum()
st.subheader("Transporte")
st.write(df_costo_transporte[['Costo', 'Ponderado']])
st.write(f"Total Ponderado Transporte (qq): ${total_ponderado_transporte:.2f}")

total_fabrica = azucar_qq * df_costos_fabrica['Ponderado']

df_ingresos['Ponderado'] = df_ingresos['Precio'] * df_ingresos['Porcentaje']
total_ponderado = df_ingresos['Ponderado'].sum()

contribucion_1 = (caña_tc*75)/1000
contribucion_2 = (caña_tc*38)/1000

c1 = (contribucion_1* precio_mwh)/azucar_qq
c2 = (contribucion_2* precio_tm_melaza)/azucar_qq


contribuciones = c1+c2 # Valor fijo de contribuciones
total_ingresos = total_ponderado + contribuciones

# Mostrar resultados
st.subheader("Ingresos")
st.write(df_ingresos[['Tipo', 'Ponderado']])
st.write(f"Total Ponderado ingresos (qq): ${total_ponderado:.2f}")
st.write(f"Contribuciones: ${contribuciones:.2f}")
st.write(f"Total Ingresos (qq): ${total_ingresos:.2f}")
total_ingresos_qq = (total_ponderado+contribuciones)*azucar_qq

st.markdown(f"<h3 style='color: green;'>Ingreso Total: ${total_ingresos_qq:,.1f}</h3>", unsafe_allow_html=True)


costos_total = costo_de_caña_en_patio_qq + total_ponderado_fabrica + total_ponderado_transporte

st.write(f"Margen (qq): ${total_ingresos - costos_total:.2f}")
st.markdown(f"<h3 style='color: green;'>Margen: ${(total_ingresos-costos_total)*azucar_qq:,.2f}</h3>", unsafe_allow_html=True)


df_ingresos['Totales'] = df_ingresos['Ponderado'] * azucar_qq 
total_ponderado_qq = total_ponderado * azucar_qq
total_contrib_qq = contribuciones * azucar_qq
total_azu = df_ingresos['Totales'].sum()

chart = alt.Chart(df_ingresos).mark_bar().encode(
    x='Tipo',
    y='Ponderado',
    color='Tipo',
    tooltip=['Tipo', 'Ponderado']
).properties(
    title='Distribución de Ingresos por Tipo de Azúcar'
)
st.altair_chart(chart, use_container_width=True)