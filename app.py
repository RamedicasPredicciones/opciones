import streamlit as st
import pandas as pd
from io import BytesIO

# Función para cargar el archivo de inventario de Google Sheets
def load_inventory_file():
    inventario_url = "https://docs.google.com/spreadsheets/d/1Y9SgliayP_J5Vi2SdtZmGxKWwf1iY7ma/export?format=xlsx"
    inventario_api_df = pd.read_excel(inventario_url, sheet_name="Hoja1")
    return inventario_api_df

# Función para procesar las alternativas para un solo código de artículo
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

# Función para generar un archivo Excel con los resultados
def generar_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Alternativas')
    output.seek(0)
    return output

# Streamlit UI
st.title('Buscador de Alternativas por Código de Artículo')

# Subir archivo con códigos de artículos
uploaded_file = st.file_uploader("Sube un archivo con los códigos de artículo (codart)", type=["xlsx", "csv"])

# Cargar inventario
inventario_api_df = load_inventory_file()

if uploaded_file:
    # Leer el archivo subido
    if uploaded_file.name.endswith('xlsx'):
        df_subido = pd.read_excel(uploaded_file)
    else:
        df_subido = pd.read_csv(uploaded_file)

    # Verificar que el archivo tenga la columna 'codart'
    if 'codart' in df_subido.columns:
        # Procesar alternativas para cada código en el archivo subido
        resultados = pd.DataFrame()  # DataFrame vacío para acumular los resultados

        for codart in df_subido['codart']:
            alternativas = procesar_alternativas(inventario_api_df, codart)
            if not alternativas.empty:
                # Añadir los resultados al DataFrame final
                resultados = pd.concat([resultados, alternativas])

        # Mostrar los resultados
        if not resultados.empty:
            st.write("Alternativas disponibles para los códigos ingresados:")
            st.dataframe(resultados)

            # Generar archivo Excel para descargar
            excel_file = generar_excel(resultados)
            st.download_button(
                label="Descargar archivo Excel con alternativas",
                data=excel_file,
                file_name="alternativas_disponibles.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.write("No se encontraron alternativas para los códigos ingresados.")
    else:
        st.error("El archivo subido no contiene la columna 'codart'.")
