import streamlit as st

dashboard = st.Page(
    "ingresos.py", title="Ingresos", icon=":material/dashboard:", default=True
)
bugs = st.Page("comparacion.py", title="Finca Nueva", icon=":material/pin_drop:")

pg = st.navigation(
        {
            "Reportes": [dashboard, bugs]
        }
    )
pg.run()