import streamlit as st
import pandas as pd
from io import BytesIO

# Función para cargar el inventario desde Google Sheets
def load_inventory_file():
    inventario_url = "https://docs.google.com/spreadsheets/d/19myWtMrvsor2P_XHiifPgn8YKdTWE39O/export?format=xlsx"
    inventario_api_df = pd.read_excel(inventario_url, sheet_name="Hoja1")
    inventario_api_df.columns = inventario_api_df.columns.str.lower().str.strip()  # Asegurar nombres consistentes
    return inventario_api_df

# Función para procesar las alternativas basadas en los productos faltantes
def procesar_alternativas(faltantes_df, inventario_api_df):
    faltantes_df.columns = faltantes_df.columns.str.lower().str.strip()

    if not {'cur', 'codart', 'embalaje'}.issubset(faltantes_df.columns):
        st.error("El archivo de faltantes debe contener las columnas: 'cur', 'codart' y 'embalaje'")
        return pd.DataFrame()

    cur_faltantes = faltantes_df['cur'].unique()
    alternativas_inventario_df = inventario_api_df[inventario_api_df['cur'].isin(cur_faltantes)]

    columnas_necesarias = ['codart', 'cur', 'opcion', 'nomart', 'carta', 'descontinuado']
    for columna in columnas_necesarias:
        if columna not in alternativas_inventario_df.columns:
            st.error(f"La columna '{columna}' no se encuentra en el inventario. Verifica el archivo de origen.")
            st.stop()

    alternativas_inventario_df['opcion'] = alternativas_inventario_df['opcion'].fillna(0).astype(int)

    alternativas_inventario_df = alternativas_inventario_df.rename(columns={
        'codart': 'codart_alternativa'
    })

    # Se agrega la columna 'descontinuado' al DataFrame de alternativas
    alternativas_inventario_df = alternativas_inventario_df[['cur', 'codart_alternativa', 'opcion', 'nomart', 'carta', 'descontinuado']]

    alternativas_disponibles_df = pd.merge(
        faltantes_df,
        alternativas_inventario_df,
        on='cur',
        how='inner'
    )

    return alternativas_disponibles_df

# Función para generar un archivo Excel
def generar_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Alternativas')
    output.seek(0)
    return output

# Función para descargar la plantilla
def descargar_plantilla():
    plantilla_url = "https://docs.google.com/spreadsheets/d/1DWK-kyp5fy_AmjDrj9UUiiWIynT6ob3N/export?format=xlsx"
    return plantilla_url

# Interfaz de Streamlit
st.markdown(
    """
    <h1 style="text-align: center; color: #FF5800; font-family: Arial, sans-serif;">
        RAMEDICAS S.A.S.
    </h1>
    <h3 style="text-align: center; font-family: Arial, sans-serif; color: #3A86FF;">
        Buscador de Alternativas por Código de Artículo
    </h3>
    <p style="text-align: center; font-family: Arial, sans-serif; color: #6B6B6B;">
        Esta herramienta te permite buscar y consultar los códigos alternativos de productos con las opciones deseadas de manera eficiente y rápida.
    </p>
    """,
    unsafe_allow_html=True
)

st.markdown(
    f"""
    <a href="{descargar_plantilla()}" download>
        <button style="background-color: #FF5800; color: white; padding: 10px 15px; border: none; border-radius: 5px; cursor: pointer;">
            Descargar plantilla
        </button>
    </a>
    """,
    unsafe_allow_html=True
)

# Subir archivo de faltantes
uploaded_file = st.file_uploader("Sube un archivo con los productos faltantes (contiene 'codart', 'cur' y 'embalaje')", type=["xlsx", "csv"])

if uploaded_file:
    if uploaded_file.name.endswith('xlsx'):
        faltantes_df = pd.read_excel(uploaded_file)
    else:
        faltantes_df = pd.read_csv(uploaded_file)

    inventario_api_df = load_inventory_file()

    alternativas_disponibles_df = procesar_alternativas(faltantes_df, inventario_api_df)

    if not alternativas_disponibles_df.empty:
        st.write("Filtra las alternativas por opciones:")

        # Filtrar las opciones disponibles para excluir el valor 0
        opciones_disponibles = alternativas_disponibles_df['opcion'].unique().tolist()
        opciones_disponibles = [opcion for opcion in opciones_disponibles if opcion != 0]  # Eliminar opción 0

        opciones_seleccionadas = st.multiselect(
            "Selecciona las opciones que deseas visualizar:",
            options=opciones_disponibles,
            default=[]  # Sin opciones seleccionadas por defecto
        )

        # Filtrar el dataframe según las opciones seleccionadas
        alternativas_filtradas_df = alternativas_disponibles_df[
            alternativas_disponibles_df['opcion'].isin(opciones_seleccionadas)
        ]

        st.write("Alternativas disponibles filtradas:")
        st.dataframe(alternativas_filtradas_df[['codart', 'cur', 'codart_alternativa', 'opcion', 'nomart', 'carta', 'descontinuado']])

        if not alternativas_filtradas_df.empty:
            excel_file = generar_excel(alternativas_filtradas_df[['codart', 'cur', 'codart_alternativa', 'opcion', 'nomart', 'carta', 'descontinuado']])
            st.download_button(
                label="Descargar archivo Excel con las alternativas filtradas",
                data=excel_file,
                file_name="alternativas_filtradas.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.write("No hay alternativas disponibles para las opciones seleccionadas.")
    else:
        st.write("No se encontraron alternativas para los códigos ingresados.")
