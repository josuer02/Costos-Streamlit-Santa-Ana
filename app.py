import streamlit as st

dashboard = st.Page("ingresos.py", title="Ingresos", icon=":material/dashboard:", default=True)
bugs = st.Page("comparacion.py", title="Análisis de Fincas", icon=":material/analytics:")
mapa = st.Page("mapa.py", title="Mapa", icon=":material/pin_drop:")

pg = st.navigation(
        {
            "Reportes": [dashboard, bugs, mapa]
        }
    )
pg.run()