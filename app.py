import streamlit as st
import pandas as pd
from io import BytesIO

# Cargar archivo de Google Sheets desde el enlace proporcionado
def load_inventory_file():
    inventario_url = "https://docs.google.com/spreadsheets/d/1Y9SgliayP_J5Vi2SdtZmGxKWwf1iY7ma/export?format=xlsx"
    inventario_api_df = pd.read_excel(inventario_url, sheet_name="Hoja1")
    return inventario_api_df

# Función para procesar las alternativas
def procesar_alternativas(inventario_api_df, codigo_articulo):
    # Filtrar el inventario según el código de artículo (codart) ingresado y obtener el 'cur' correspondiente
    cur_articulo = inventario_api_df[inventario_api_df['codart'] == codigo_articulo]['cur'].values

    # Si no se encuentra el CUR para el código, devolver un DataFrame vacío
    if len(cur_articulo) == 0:
        return pd.DataFrame()
    
    # Buscar las alternativas disponibles con el mismo CUR
    alternativas_disponibles_df = inventario_api_df[inventario_api_df['cur'] == cur_articulo[0]]

    # Excluir filas donde 'opcion' sea igual a 0
    alternativas_disponibles_df = alternativas_disponibles_df[alternativas_disponibles_df['opcion'] != 0]

    return alternativas_disponibles_df

# Streamlit UI
st.title('Buscador de Alternativas por Código de Artículo')

# Cargar inventario
inventario_api_df = load_inventory_file()

# Campo para ingresar el código del producto (codart)
codigo_articulo = st.text_input("Ingrese el código del artículo (codart):")

if codigo_articulo:
    # Mostrar opciones de alternativas si hay resultados
    opciones_disponibles = procesar_alternativas(inventario_api_df, codigo_articulo)

    if not opciones_disponibles.empty:
        st.write("Alternativas disponibles para el código ingresado:")
        st.dataframe(opciones_disponibles)
    else:
        st.write("No se encontraron alternativas para el código ingresado.")
