import streamlit as st
import pandas as pd
from io import BytesIO

# Función para cargar el inventario desde Google Sheets
def load_inventory_file():
    inventario_url = "https://docs.google.com/spreadsheets/d/1Y9SgliayP_J5Vi2SdtZmGxKWwf1iY7ma/export?format=xlsx"
    inventario_api_df = pd.read_excel(inventario_url, sheet_name="Hoja1")
    return inventario_api_df

# Función para procesar las alternativas basadas en los productos faltantes
def procesar_alternativas(faltantes_df, inventario_api_df):
    # Convertir los nombres de las columnas a minúsculas
    faltantes_df.columns = faltantes_df.columns.str.lower().str.strip()
    inventario_api_df.columns = inventario_api_df.columns.str.lower().str.strip()

    # Verificar si el archivo de faltantes contiene las columnas requeridas
    if not {'cur', 'codart', 'embalaje'}.issubset(faltantes_df.columns):
        st.error("El archivo de faltantes debe contener las columnas: 'cur', 'codart' y 'embalaje'")
        return pd.DataFrame()  # Devuelve un DataFrame vacío si faltan columnas

    # Filtrar el inventario solo por los artículos que están en el archivo de faltantes
    cur_faltantes = faltantes_df['cur'].unique()
    alternativas_inventario_df = inventario_api_df[inventario_api_df['cur'].isin(cur_faltantes)]

    # Excluir opciones sin stock
    alternativas_disponibles_df = alternativas_inventario_df[alternativas_inventario_df['opcion'] != 0]

    # Combinar los faltantes con las alternativas disponibles
    alternativas_disponibles_df = pd.merge(
        faltantes_df[['cur', 'codart', 'embalaje']],
        alternativas_disponibles_df,
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

# Interfaz de Streamlit
st.title('Buscador de Alternativas por Código de Artículo')

# Subir archivo de faltantes
uploaded_file = st.file_uploader("Sube un archivo con los productos faltantes (contiene 'cur', 'codart', 'embalaje')", type=["xlsx", "csv"])

if uploaded_file:
    # Leer el archivo subido
    if uploaded_file.name.endswith('xlsx'):
        faltantes_df = pd.read_excel(uploaded_file)
    else:
        faltantes_df = pd.read_csv(uploaded_file)

    # Cargar el inventario
    inventario_api_df = load_inventory_file()

    # Procesar alternativas
    alternativas_disponibles_df = procesar_alternativas(faltantes_df, inventario_api_df)

    # Mostrar las alternativas
    if not alternativas_disponibles_df.empty:
        st.write("Alternativas disponibles para los productos faltantes:")
        st.dataframe(alternativas_disponibles_df)

        # Obtener las opciones únicas para seleccionar
        opciones_disponibles = alternativas_disponibles_df['opcion'].unique()
        opciones_seleccionadas = st.multiselect(
            "Selecciona las opciones que deseas ver (puedes elegir varias)",
            options=opciones_disponibles
        )

        # Filtrar las alternativas para mostrar solo las opciones seleccionadas
        if opciones_seleccionadas:
            alternativas_filtradas = alternativas_disponibles_df[alternativas_disponibles_df['opcion'].isin(opciones_seleccionadas)]
            st.write(f"Mostrando alternativas para las opciones seleccionadas: {', '.join(map(str, opciones_seleccionadas))}")
            st.dataframe(alternativas_filtradas)

            # Generar archivo Excel para descargar
            excel_file = generar_excel(alternativas_filtradas)
            st.download_button(
                label="Descargar archivo Excel con las opciones seleccionadassssss",
                data=excel_file,
                file_name=f"alternativas_opciones_seleccionadas.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.write("No has seleccionado ninguna opción para mostrar.")
    else:
        st.write("No se encontraron alternativas para los códigos ingresados.")
