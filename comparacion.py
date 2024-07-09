import streamlit as st
import pandas as pd
import folium
import numpy as np
import matplotlib.pyplot as plt
import altair as alt
from streamlit_folium import st_folium
from math import radians, cos, sin, sqrt, atan2
import os

import requests

def get_route(start_lat, start_lon, end_lat, end_lon):
    url = f"http://router.project-osrm.org/route/v1/driving/{start_lon},{start_lat};{end_lon},{end_lat}?overview=full&geometries=geojson"
    response = requests.get(url).json()
    route = response['routes'][0]['geometry']['coordinates']
    distance = response['routes'][0]['distance'] / 1000  # Convertir de metros a kilómetros
    return [(coord[1], coord[0]) for coord in route], distance

def costo_por_area(costo, area):
    return costo * area if area > 0 else 0

# Function to load data
def load_data(file_path):
    return pd.read_excel(file_path, engine='openpyxl', sheet_name='COSTOS_QQ')

# Default file path
default_file = st.secrets["default_file_path"]

# Initialize session state variables
if 'new_lat' not in st.session_state:
    st.session_state.new_lat = 0.0
if 'new_lon' not in st.session_state:
    st.session_state.new_lon = 0.0
if 'show_new_farm' not in st.session_state:
    st.session_state.show_new_farm = False
if 'df' not in st.session_state:
    st.session_state.df = None

sugar_mill_location = [14.239920460668085, -90.84192521827173]

st.title("Comparación Fincas")

# Check if default file exists and load it
if os.path.exists(default_file):
    st.session_state.df = load_data(default_file)
    st.success("Archivo predeterminado cargado exitosamente!")
else:
    st.warning("Archivo predeterminado no encontrado. Por favor, suba un archivo.")

# File uploader for user to choose a different file
uploaded_file = st.file_uploader("Elija un archivo Excel diferente (opcional)", type="xlsx")

if uploaded_file is not None:
    st.session_state.df = load_data(uploaded_file)
    st.success("Archivo del usuario cargado exitosamente!")

# The rest of your code remains the same, but wrapped in a condition to check if df is not None
if st.session_state.df is not None:
    if 'LATITUD' in st.session_state.df.columns and 'LONGITUD' in st.session_state.df.columns:
        # Set default values for latitude and longitude
        default_lat = 14.066438171238065
        default_lon = -90.77373649999998

        # Your existing code for latitude and longitude inputs with default values
        new_lat = st.number_input("Ingrese la latitud de la nueva finca:", 
                                value=default_lat,
                                step=1e-6,
                                format="%.6f")
        new_lon = st.number_input("Ingrese la longitud de la nueva finca:", 
                                value=default_lon,
                                step=1e-6,
                                format="%.6f")
        
        # Botón para aplicar los nuevos valores
        if st.button("Aplicar nuevas coordenadas"):
            st.session_state.new_lat = new_lat
            st.session_state.new_lon = new_lon
            st.session_state.show_new_farm = True
        
        m = folium.Map(location=sugar_mill_location, zoom_start=10)

        # Añadir marcador del ingenio azucarero
        folium.Marker(
            location=sugar_mill_location,
            popup="Ingenio Santa Ana",
            tooltip="Ingenio Santa Ana",
            icon=folium.Icon(color='red', icon='home')
        ).add_to(m)

        if st.session_state.show_new_farm and st.session_state.new_lat != 0 and st.session_state.new_lon != 0:
            # Función para calcular la distancia usando la fórmula de Haversine
            def haversine(lat1, lon1, lat2, lon2):
                R = 6371.0
                dlat = radians(lat2 - lat1)
                dlon = radians(lon2 - lon1)
                a = sin(dlat / 2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2)**2
                c = 2 * atan2(sqrt(a), sqrt(1 - a))
                distance = R * c
                return distance
            
            # Calcular la distancia entre la nueva finca y el ingenio azucarero
            distancia_ingenio = haversine(st.session_state.new_lat, st.session_state.new_lon, sugar_mill_location[0], sugar_mill_location[1])
            
            # Calcular las distancias desde la nueva finca a todas las fincas existentes
            st.session_state.df['DISTANCIA'] = st.session_state.df.apply(lambda row: haversine(st.session_state.new_lat, st.session_state.new_lon, row['LATITUD'], row['LONGITUD']), axis=1)
            
            # Ordenar el DataFrame por distancia
            df_sorted = st.session_state.df.sort_values(by='DISTANCIA')
            
            # Mostrar las fincas más cercanas
            st.write("Fincas más cercanas a la nueva ubicación:")
            st.write(df_sorted.head(5))
            
            # Añadir marcador de la nueva finca
            folium.Marker(
                location=[st.session_state.new_lat, st.session_state.new_lon],
                popup="Nueva Finca",
                tooltip="Nueva Finca",
                icon=folium.Icon(color='green', icon='plus')
            ).add_to(m)
            
            # Obtener la ruta
            route, route_distance = get_route(14.239920460668085,  -90.84192521827173, st.session_state.new_lat, st.session_state.new_lon)

            # Dibujar la ruta en el mapa
            folium.PolyLine(
                locations=route,
                color='blue',
                weight=2.5,
                opacity=0.8
            ).add_to(m)

            # Añadir un marcador en el medio de la ruta que indique la distancia real
            mid_point = route[len(route)//2]
            folium.Marker(
                location=mid_point,
                popup=f"Distancia de la ruta: {route_distance:.2f} km",
                icon=folium.DivIcon(html=f"""<div style="font-family: Arial; color: black; font-size: 14px;">{route_distance:.2f} km</div>""")
            ).add_to(m)

        # Añadir marcadores de las fincas al mapa
        for idx, row in st.session_state.df.iterrows():
            folium.Marker(
                location=[row['LATITUD'], row['LONGITUD']],
                popup=f"Finca: {row['NOMFIN']}" if 'NOMFIN' in st.session_state.df.columns else None,
                tooltip=f"Lat: {row['LATITUD']}, Lon: {row['LONGITUD']}",
                icon=folium.Icon(color='blue', icon='info-sign')
            ).add_to(m)

        # Mostrar el mapa en Streamlit
        st_folium(m, width=700, height=500)

    else:
        st.error("El DataFrame no contiene columnas 'LATITUD' y 'LONGITUD'.")

    st.subheader("Análisis de Costos y Producción")

    # Filtros para la nueva finca
    col1, col2, col3 = st.columns(3)
    with col1:
        nuevo_manejo = st.number_input("Manejo de la nueva finca:", min_value=0.0, format="%.2f")
        nueva_renta = st.number_input("Renta de la nueva finca:", min_value=0.0, format="%.2f")
    with col2:
        nuevo_cat = st.number_input("CAT de la nueva finca:", min_value=0.0, format="%.2f")
        nueva_area = st.number_input("Área de la nueva finca:", min_value=0.0, format="%.2f")
    with col3:
        if st.session_state.df is not None:
            grupos_disponibles = ['Todos'] + list(st.session_state.df['GRUPO'].unique())
            grupo_seleccionado = st.selectbox("Filtrar por GRUPO:", grupos_disponibles)
        else:
            st.write("Carga un archivo para ver opciones de grupo.")
        
        # Nuevo filtro para el tipo de corte
        tipo_corte = st.selectbox("Tipo de corte para la nueva finca:", ["Manual", "Mecanizado"])

    if st.session_state.df is not None:
        # Filtrar el DataFrame
        if grupo_seleccionado != 'Todos':
            df_filtered = st.session_state.df[st.session_state.df['GRUPO'] == grupo_seleccionado]
        else:
            df_filtered = st.session_state.df

        # Ordenar y seleccionar las 5 fincas más cercanas
        if 'DISTANCIA' in df_filtered.columns:
            top_5_fincas = df_filtered.sort_values(by='DISTANCIA').head(5)
        else:
            top_5_fincas = df_filtered.head(5)

        # Añadir la nueva finca a la comparación
        nueva_finca = pd.DataFrame({
            'NOMFIN': ['Nueva Finca'],
            'MANEJO SIN INV.': [nuevo_manejo],
            'RENTA': [nueva_renta],
            'CAT': [nuevo_cat],
            'AREA': [nueva_area],
            'Manejo /ha': [nuevo_manejo / nueva_area if nueva_area > 0 else 0],
            'Renta / ha': [nueva_renta / nueva_area if nueva_area > 0 else 0],
            'CAT /ha': [nuevo_cat / nueva_area if nueva_area > 0 else 0],
            'TOTAL SIN INV': [nuevo_manejo + nueva_renta + nuevo_cat],
            'PORCENTAJE_CORTE_MANUAL': [1.00 if tipo_corte == "Manual" else 0],
            'PORCENTAJE_CORTE_MECANIZADO': [1.00 if tipo_corte == "Mecanizado" else 0]
        })

        top_5_fincas = pd.concat([nueva_finca, top_5_fincas])

        costos_ha = ['Manejo /ha', 'Renta / ha', 'CAT /ha']
        fig, ax = plt.subplots(figsize=(12, 6))
        top_5_fincas[costos_ha].plot(kind='bar', ax=ax)
        ax.set_ylabel('Costo por Hectárea')
        ax.set_title('Desglose de Costos por Hectárea incluyendo la nueva finca')
        ax.set_xticklabels(top_5_fincas['NOMFIN'], rotation=45, ha='right')
        plt.legend(title='Tipo de Costo')
        plt.tight_layout()
        st.pyplot(fig)


        # Gráfico de barras apiladas para el tipo de corte
        if 'PORCENTAJE_CORTE_MANUAL' in top_5_fincas.columns and 'PORCENTAJE_CORTE_MECANIZADO' in top_5_fincas.columns:
            fig, ax = plt.subplots(figsize=(12, 6))
            
            # Multiplicar los valores por 100 para convertirlos a porcentajes
            data_to_plot = top_5_fincas[['PORCENTAJE_CORTE_MANUAL', 'PORCENTAJE_CORTE_MECANIZADO']] * 100
            
            data_to_plot.plot(kind='bar', stacked=True, ax=ax)
            ax.set_ylabel('Porcentaje')
            ax.set_title('Distribución del Tipo de Corte')
            ax.set_xticklabels(top_5_fincas['NOMFIN'], rotation=45, ha='right')
            plt.legend(title='Tipo de Corte')
            
            # Añadir etiquetas con los valores
            for c in ax.containers:
                ax.bar_label(c, fmt='%.1f%%', label_type='center')
            
            # Ajustar el límite superior del eje y a 100%
            ax.set_ylim(0, 100)
            
            plt.tight_layout()
            st.pyplot(fig)
        else:
            st.write("No hay datos disponibles sobre el tipo de corte.")

        # Gráfico de dispersión para Área vs. Producción con línea de tendencia
        if 'TONS' in top_5_fincas.columns:
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # Asegurarse de que los datos son numéricos
            x = top_5_fincas['AREA'].astype(float)
            y = top_5_fincas['TONS'].astype(float)
            
            # Graficar los puntos
            ax.scatter(x, y)
            
            # Añadir línea de tendencia
            z = np.polyfit(x, y, 1)
            p = np.poly1d(z)
            ax.plot(x, p(x), "r--", alpha=0.8)
            
            ax.set_xlabel('Área')
            ax.set_ylabel('Toneladas producidas')
            ax.set_title('Relación Área vs. Producción incluyendo la nueva finca')
            
            for i, txt in enumerate(top_5_fincas['NOMFIN']):
                ax.annotate(txt, (x.iloc[i], y.iloc[i]))
            
            plt.tight_layout()
            st.pyplot(fig)
        else:
            st.write("No hay datos de producción disponibles para mostrar el gráfico de Área vs. Producción.")
    else:
        st.write("Por favor, carga un archivo Excel para comenzar el análisis.")


    st.subheader("Análisis de Costos")

    # New inputs for cost analysis
    area_arrendada = st.number_input("Area Arrendada (Has):", value=400, step=100)
    area_productiva = st.number_input("Area Productiva (Has):", value=360, step=100)
    rendimiento = st.number_input("Rendimiento (Lbs/TC):", value=220.0, step=0.1, format="%.1f")
    productividad = st.number_input("Productividad (THC):", value=115)
    tipo_de_cambio = st.number_input("Tipo de Cambio:", value=7.85, step=0.01, format="%.2f")

    cat_option = st.selectbox("CAT:", ["Con depreciación", "Sin depreciación"])
    cat_value = 7.61 if cat_option == "Con depreciación" else 4.8
    
    caña_tc = area_productiva * productividad
    azucar_qq = caña_tc * rendimiento /100
    azucar_tc = azucar_qq / 21.739

    total_cat = cat_value * caña_tc

    cat_ha = total_cat/area_productiva

    cat_qq = total_cat/azucar_qq
    

    df_costos_v1 = pd.DataFrame({
        'Tipo CAT': ['CAT'],
        'Por Ha': [total_cat/area_productiva],
        'Por TC': [cat_value],
        'Por QQ': [total_cat/azucar_qq],
        'Total' : [total_cat]
    })

    st.write(df_costos_v1)

    st.subheader("Manejo Agrícola")
    costo_riego = st.number_input("Costo de riego", min_value=0.0, value=0.0, step=0.01)
    costo_riego_por_area = costo_por_area(costo_riego, area_productiva)

    costo_fertilizacion = st.number_input("Costo de fertilización", min_value=0.0, value=0.0, step=0.01)
    costo_fertilizacion_por_area = costo_por_area(costo_fertilizacion, area_productiva)

    costo_malezas = st.number_input("Costo de control de malezas", min_value=0.0, value=0.0, step=0.01)
    costo_malezas_por_area = costo_por_area(costo_malezas, area_productiva)

    costo_plagas = st.number_input("Costo de manejo de plagas", min_value=0.0, value=0.0, step=0.01)
    costo_plagas_por_area = costo_por_area(costo_plagas, area_productiva)

    costo_administracion = st.number_input("Costo de administración", min_value=0.0, value=0.0, step=0.01)
    costo_administracion_por_area = costo_por_area(costo_administracion, area_productiva)

    costo_total_agri = costo_riego + costo_fertilizacion + costo_malezas + costo_plagas + costo_administracion
    costo_total_agri_p_area = costo_riego_por_area + costo_fertilizacion_por_area + costo_malezas_por_area + costo_plagas_por_area+costo_administracion_por_area
    costo_agri_qq_total = costo_total_agri_p_area / azucar_qq

    st.write(f"Costo total: ${costo_total_agri:.2f}")


    st.subheader("Arrendamiento")

    costo_arrendamiento_fijo = st.number_input("Costo de arrendamiento fijo", min_value=0.0, value=0.0, step=0.01)
    costo_arrendamiento_variable = st.number_input("Costo de arrendamiento variable", min_value=0.0, value=0.0, step=0.01)
    costo_arrendamiento_total = costo_arrendamiento_fijo + costo_arrendamiento_variable

    costo_arrendamiento_por_area_fijo = costo_por_area(costo_arrendamiento_fijo, area_arrendada)
    costo_arrendamiento_por_area_variable = costo_por_area(costo_arrendamiento_variable, area_arrendada)
    costo_arrendamiento_por_area_total = costo_arrendamiento_por_area_variable+costo_arrendamiento_por_area_fijo
    costo_arrendamiento_tot_qq = costo_arrendamiento_por_area_total / azucar_qq

    st.write(f"Costo total: ${costo_arrendamiento_total:.2f}")
    
    st.header("Inversiones")
    costo_capex = st.number_input("Costo CAPEX (inversiones de capital)", min_value=0.0, value=0.0, step=0.01)
    costo_renovacion = st.number_input("Costo de renovación", min_value=0.0, value=0.0, step=0.01)
    costo_inversiones_total = costo_capex + costo_renovacion
    
    costo_capex_por_area = costo_por_area(costo_capex, area_productiva)
    costo_renovacion_por_area = costo_por_area(costo_renovacion, area_productiva)
    costo_inversiones_p_area = costo_capex_por_area+costo_renovacion_por_area
    costo_inversiones_qq = costo_inversiones_p_area/azucar_qq

    st.write(f"Costo total: ${costo_inversiones_total:.2f}")

    costo_de_caña_en_patio = cat_ha + costo_total_agri + costo_arrendamiento_total + costo_inversiones_total

    st.markdown(f"<h3 style='color: green;'>Costo total en patio: ${costo_de_caña_en_patio:,.2f}</h3>", unsafe_allow_html=True)
    
    costo_de_caña_en_patio_qq = costo_inversiones_qq + costo_arrendamiento_tot_qq + costo_agri_qq_total + cat_qq
    #st.write(costo_de_caña_en_patio_qq)

    st.subheader("Análisis de Ingresos")

    # Usar los inputs existentes para los datos base
    precio_ny_11 = st.session_state.get('precio_ny_11', 15.00)
    white_premium = st.session_state.get('white_premium', 4.78)
    prima_vhp = st.session_state.get('prima_vhp', 1.66)
    precio_local = st.session_state.get('precio_local', 34.00)

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
    st.write(df_costos_fabrica)
    st.write(f"Total Ponderado Fabrica: ${total_ponderado_fabrica:.2f}")
    #st.write(df_costos_fabrica)
    total_fabrica = azucar_qq * df_costos_fabrica['Ponderado']

    #st.write(total_fabrica)

    df_costo_transporte['Ponderado'] = df_costo_transporte['Costo'] * df_costo_transporte['Porcentaje']
    total_ponderado_transporte = df_costo_transporte['Ponderado'].sum()
    st.subheader("Transporte")
    st.write(df_costo_transporte)
    st.write(f"Total Ponderado Transporte: ${total_ponderado_transporte:.2f}")

    total_fabrica = azucar_qq * df_costos_fabrica['Ponderado']

    df_ingresos['Ponderado'] = df_ingresos['Precio'] * df_ingresos['Porcentaje']
    total_ponderado = df_ingresos['Ponderado'].sum()

    contribuciones = 2.386363636+2.590909091 # Valor fijo de contribuciones
    total_ingresos = total_ponderado + contribuciones


    


    # Mostrar resultados
    st.subheader("Ingresos")
    st.write(df_ingresos)
    st.write(f"Total Ponderado: ${total_ponderado:.2f}")
    st.write(f"Contribuciones: ${contribuciones:.2f}")
    st.write(f"Total Ingresos: ${total_ingresos:.2f}")
    total_ingresos_qq = (total_ponderado+contribuciones)*azucar_qq

    st.markdown(f"<h3 style='color: green;'>Ingreso Total: ${total_ingresos_qq:,.1f}</h3>", unsafe_allow_html=True)


    costos_total = costo_de_caña_en_patio_qq + total_ponderado_fabrica + total_ponderado_transporte
    st.write(f"Margen: ${total_ingresos - costos_total:.2f}")
    st.markdown(f"<h3 style='color: green;'>Margen: ${(total_ingresos-costos_total)*azucar_qq:,.2f}</h3>", unsafe_allow_html=True)

    

    df_ingresos['Totales'] = df_ingresos['Ponderado'] * azucar_qq 
    total_ponderado_qq = total_ponderado * azucar_qq
    total_contrib_qq = contribuciones * azucar_qq
    total_azu = df_ingresos['Totales'].sum()


    #st.write("Ingresos totales", df_ingresos['Totales'])
    # Gráfico de barras para mostrar la distribución de ingresos
    


    chart = alt.Chart(df_ingresos).mark_bar().encode(
        x='Tipo',
        y='Ponderado',
        color='Tipo',
        tooltip=['Tipo', 'Ponderado']
    ).properties(
        title='Distribución de Ingresos por Tipo de Azúcar'
    )
    st.altair_chart(chart, use_container_width=True)