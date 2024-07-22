import io
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
import simplekml
import xml.etree.ElementTree as ET
import zipfile
import networkx as nx #type: ignore
from scipy.spatial import cKDTree #type: ignore

# Function to load data
def load_data(file_path):
    return pd.read_excel(file_path, engine='openpyxl', sheet_name='COSTOS_QQ')

# Function to parse KML file
def parse_kml(kml_file):
    routes = []
    
    if isinstance(kml_file, str):
        # If kml_file is a string (file path)
        file_name = kml_file
        with open(kml_file, 'rb') as f:
            kml_content = f.read()
    else:
        # If kml_file is a file object
        file_name = kml_file.name
        kml_content = kml_file.read()
    
    if file_name.endswith('.kmz'):
        with zipfile.ZipFile(io.BytesIO(kml_content), 'r') as kmz:
            kml_content = kmz.read('doc.kml')
    
    root = ET.fromstring(kml_content)
    
    for placemark in root.findall('.//{http://www.opengis.net/kml/2.2}Placemark'):
        coordinates = placemark.find('.//{http://www.opengis.net/kml/2.2}coordinates')
        if coordinates is not None:
            route = []
            for coord in coordinates.text.strip().split():
                lon, lat, _ = coord.split(',')
                route.append([float(lat), float(lon)])
            routes.append(route)
    
    return routes

# Haversine function
def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance = R * c
    return distance

# Function to calculate route distance
def calculate_route_distance(start, end, routes):
    # Create a graph from all routes
    G = nx.Graph()
    for route in routes:
        for i in range(len(route) - 1):
            G.add_edge(tuple(route[i]), tuple(route[i+1]), 
                       weight=haversine(route[i][0], route[i][1], route[i+1][0], route[i+1][1]))

    # Find nearest points on the routes for start and end
    all_points = list(G.nodes())
    tree = cKDTree(all_points)
    _, start_idx = tree.query(start)
    _, end_idx = tree.query(end)
    
    start_on_route = all_points[start_idx]
    end_on_route = all_points[end_idx]

    # Calculate distances to/from nearest points on routes
    start_distance = haversine(start[0], start[1], start_on_route[0], start_on_route[1])
    end_distance = haversine(end[0], end[1], end_on_route[0], end_on_route[1])

    # Find shortest path on the route network
    try:
        path = nx.shortest_path(G, source=start_on_route, target=end_on_route, weight='weight')
        route_distance = sum(G[path[i]][path[i+1]]['weight'] for i in range(len(path)-1))
        total_distance = start_distance + route_distance + end_distance
        return total_distance, path
    except nx.NetworkXNoPath:
        # If no path found, return direct distance
        return haversine(start[0], start[1], end[0], end[1]), None

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

# Uploader for alternative Excel file
uploaded_file = st.file_uploader("Elija un archivo Excel diferente (opcional)", type="xlsx")

if uploaded_file is not None:
    st.session_state.df = load_data(uploaded_file)
    st.success("Archivo del usuario cargado exitosamente!")

# KML file path
kml_file = st.secrets['kmz_file']
# Check if DataFrame is not None
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
        
        if st.button("Aplicar nuevas coordenadas"):
            st.session_state.new_lat = new_lat
            st.session_state.new_lon = new_lon
            st.session_state.show_new_farm = True
        
        # Create map centered on sugar mill
        m = folium.Map(location=sugar_mill_location, zoom_start=10)
        
        # Add sugar mill marker
        folium.Marker(
            location=sugar_mill_location,
            popup="Ingenio Santa Ana",
            tooltip="Ingenio Santa Ana",
            icon=folium.Icon(color='red', icon='home')
        ).add_to(m)
        
        if st.session_state.show_new_farm and st.session_state.new_lat != 0 and st.session_state.new_lon != 0:
            if kml_file is not None:
                try:
                    routes = parse_kml(kml_file)
                    distancia_ingenio, shortest_path = calculate_route_distance(
                        [st.session_state.new_lat, st.session_state.new_lon],
                        sugar_mill_location,
                        routes
                    )
                    st.write(f"Distancia al Ingenio por rutas cañeras: {distancia_ingenio:.2f} km")
                    
                    # Calculate direct distance for comparison
                    distancia_directa = haversine(st.session_state.new_lat, st.session_state.new_lon, sugar_mill_location[0], sugar_mill_location[1])
                    #st.write(f"Distancia directa al Ingenio: {distancia_directa:.2f} km")

                    # Visualize the shortest path
                    if shortest_path:
                        folium.PolyLine(
                            locations=shortest_path,
                            color='green',
                            weight=4,
                            opacity=0.8,
                            tooltip="Ruta más corta"
                        ).add_to(m)
                    
                    folium.Marker(
                        location=[st.session_state.new_lat, st.session_state.new_lon],
                        popup="Nueva Finca",
                        tooltip="Nueva Finca",
                        icon=folium.Icon(color='green', icon='plus')
                    ).add_to(m)
                    
                except Exception as e:
                    st.error(f"Error calculating route distance: {str(e)}")
                    distancia_ingenio = haversine(st.session_state.new_lat, st.session_state.new_lon, sugar_mill_location[0], sugar_mill_location[1])
            else:
                distancia_ingenio = haversine(st.session_state.new_lat, st.session_state.new_lon, sugar_mill_location[0], sugar_mill_location[1])
            
            st.session_state.df['DISTANCIA'] = st.session_state.df.apply(lambda row: haversine(st.session_state.new_lat, st.session_state.new_lon, row['LATITUD'], row['LONGITUD']), axis=1)
            
            df_sorted = st.session_state.df.sort_values(by='DISTANCIA')
            
            st.write("Fincas más cercanas a la nueva ubicación:")
            st.write(df_sorted.head(5))
            
            folium.Marker(
                location=[st.session_state.new_lat, st.session_state.new_lon],
                popup="Nueva Finca",
                tooltip="Nueva Finca",
                icon=folium.Icon(color='green', icon='plus')
            ).add_to(m)
            
            mid_point = [(sugar_mill_location[0] + st.session_state.new_lat) / 2, (sugar_mill_location[1] + st.session_state.new_lon) / 2]
            folium.Marker(
                location=mid_point,
                popup=f"Distancia al Ingenio: {distancia_ingenio:.2f} km",
                icon=folium.DivIcon(html=f"""<div style="font-family: Arial; color: black; font-size: 14px;">{distancia_ingenio:.2f} km</div>""")
            ).add_to(m)
        
        for idx, row in st.session_state.df.iterrows():
            folium.Marker(
                location=[row['LATITUD'], row['LONGITUD']],
                popup=f"Finca: {row['NOMFIN']}" if 'NOMFIN' in st.session_state.df.columns else None,
                tooltip=f"Lat: {row['LATITUD']}, Lon: {row['LONGITUD']}",
                icon=folium.Icon(color='blue', icon='info-sign')
            ).add_to(m)
        
        # Add KML routes to the map
        if kml_file is not None:
            try:
                routes = parse_kml(kml_file)
                for route in routes:
                    folium.PolyLine(
                        locations=route,
                        color='red',
                        weight=2,
                        opacity=0.8
                    ).add_to(m)
            except Exception as e:
                st.error(f"Error parsing KML file: {str(e)}")

        # Checkbox to show/hide sugar cane routes
        show_routes = st.checkbox("Mostrar rutas cañeras", value=True)

        if show_routes:
            # If routes are already added, no need to do anything
            pass
        else:
            # Remove all GeoJson layers (routes) from the map
            for layer in m._children.copy():
                if isinstance(m._children[layer], folium.features.GeoJson):
                    del m._children[layer]
        
        # Display map in Streamlit
        st_folium(m, width=700, height=500)
    else:
        st.error("El DataFrame no contiene columnas 'LATITUD' y 'LONGITUD'.")
