import streamlit as st
import pandas as pd
from io import BytesIO

# Función para cargar el inventario de Google Sheets
def load_inventory_file():
    inventario_url = "https://docs.google.com/spreadsheets/d/1Y9SgliayP_J5Vi2SdtZmGxKWwf1iY7ma/export?format=xlsx"
    inventario_api_df = pd.read_excel(inventario_url, sheet_name="Hoja1")
    return inventario_api_df

# Función para procesar alternativas basadas en el inventario y los productos faltantes
def procesar_alternativas(faltantes_df, inventario_api_df, bodega_seleccionada):
    faltantes_df.columns = faltantes_df.columns.str.lower().str.strip()
    inventario_api_df.columns = inventario_api_df.columns.str.lower().str.strip()

    cur_faltantes = faltantes_df['cur'].unique()
    alternativas_inventario_df = inventario_api_df[inventario_api_df['cur'].isin(cur_faltantes)]

    # Filtrar por bodega seleccionada si se especifica
    if bodega_seleccionada:
        alternativas_inventario_df = alternativas_inventario_df[alternativas_inventario_df['bodega'] == bodega_seleccionada]

    # Eliminar alternativas sin stock
    alternativas_disponibles_df = alternativas_inventario_df[alternativas_inventario_df['unidadespresentacionlote'] > 0]

    alternativas_disponibles_df = pd.merge(
        faltantes_df[['cur', 'codart', 'embalaje']],
        alternativas_disponibles_df,
        on='cur',
        how='inner'
    )

    # Ordenar por cantidad y agrupar para encontrar la mejor opción
    alternativas_disponibles_df.sort_values(by=['codart', 'unidadespresentacionlote'], ascending=[True, False], inplace=True)

    # Obtener la mejor opción de cada código de artículo faltante
    mejores_alternativas = alternativas_disponibles_df.drop_duplicates(subset=['codart'], keep='first')

    return mejores_alternativas

# Función para generar el archivo Excel de resultados
def generar_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Alternativas')
    output.seek(0)
    return output

# Streamlit UI
st.title('Buscador de Alternativas para Faltantes')

uploaded_file = st.file_uploader("Sube tu archivo de faltantes", type=["xlsx", "csv"])

if uploaded_file:
    if uploaded_file.name.endswith('xlsx'):
        faltantes_df = pd.read_excel(uploaded_file)
    else:
        faltantes_df = pd.read_csv(uploaded_file)

    # Verificar columnas esperadas en el archivo de faltantes
    if set(['cur', 'codart', 'embalaje']).issubset(faltantes_df.columns.str.lower()):
        inventario_api_df = load_inventory_file()

        # Seleccionar bodega
        bodegas_disponibles = inventario_api_df['bodega'].unique().tolist()
        bodega_seleccionada = st.selectbox("Seleccione la bodega", options=[""] + bodegas_disponibles)

        # Procesar alternativas
        alternativas = procesar_alternativas(faltantes_df, inventario_api_df, bodega_seleccionada)

        # Mostrar alternativas en tabla
        if not alternativas.empty:
            st.write("Alternativas encontradas:")
            st.dataframe(alternativas)

            # Generar archivo Excel
            excel_file = generar_excel(alternativas)
            st.download_button(
                label="Descargar archivo de alternativas",
                data=excel_file,
                file_name="alternativas_disponibles.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.write("No se encontraron alternativas para los códigos ingresados.")
    else:
        st.error("El archivo de faltantes debe contener las columnas: 'cur', 'embalaje' y 'codart'.")
