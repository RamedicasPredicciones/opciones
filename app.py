import streamlit as st
import pandas as pd
from io import BytesIO

# Función para cargar el inventario de Google Sheets
def load_inventory_file():
    inventario_url = "https://docs.google.com/spreadsheets/d/1Y9SgliayP_J5Vi2SdtZmGxKWwf1iY7ma/export?format=xlsx"
    inventario_api_df = pd.read_excel(inventario_url, sheet_name="Hoja1")
    return inventario_api_df

# Función para procesar las alternativas para un conjunto de códigos de artículo
def procesar_alternativas(inventario_api_df, codigos_articulos):
    # Filtrar el inventario solo por los artículos (codart) que aparecen en el archivo subido
    alternativas_disponibles_df = inventario_api_df[inventario_api_df['codart'].isin(codigos_articulos)]

    # Excluir filas donde 'opcion' sea igual a 0
    alternativas_disponibles_df = alternativas_disponibles_df[alternativas_disponibles_df['opcion'] != 0]

    return alternativas_disponibles_df

# Función para generar un archivo Excel con los resultados
def generar_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:  # Cambié el motor a openpyxl
        df.to_excel(writer, index=False, sheet_name='Alternativas')
    output.seek(0)
    return output

# Streamlit UI
st.title('Buscador de Alternativas por Código de Artículo')

# Subir archivo con códigos de artículos
uploaded_file = st.file_uploader("Sube un archivo con los códigos de artículo (codart)", type=["xlsx", "csv"])

if uploaded_file:
    # Leer el archivo subido
    if uploaded_file.name.endswith('xlsx'):
        df_subido = pd.read_excel(uploaded_file)
    else:
        df_subido = pd.read_csv(uploaded_file)

    # Verificar que el archivo tenga la columna 'codart'
    if 'codart' in df_subido.columns:
        # Cargar el inventario
        inventario_api_df = load_inventory_file()

        # Filtrar solo los códigos subidos
        codigos_articulos = df_subido['codart'].unique()

        # Procesar las alternativas solo para los códigos de artículo que subes
        alternativas = procesar_alternativas(inventario_api_df, codigos_articulos)

        # Mostrar las alternativas
        if not alternativas.empty:
            st.write("Alternativas disponibles para los códigos ingresados:")
            st.dataframe(alternativas)

            # Obtener las opciones únicas de las alternativas (sin incluir las que son 0)
            opciones_disponibles = alternativas['opcion'].unique()

            # Selección de múltiples opciones basadas en las opciones disponibles
            opciones_seleccionadas = st.multiselect(
                "Selecciona las opciones que deseas ver (puedes elegir varias)",
                options=opciones_disponibles  # No hay valor por defecto, puedes elegir las opciones manualmente
            )

            # Filtrar las alternativas para mostrar solo las opciones seleccionadas
            if opciones_seleccionadas:
                alternativas_filtradas = alternativas[alternativas['opcion'].isin(opciones_seleccionadas)]

                # Mostrar las alternativas filtradas
                st.write(f"Mostrando alternativas para las opciones seleccionadas: {', '.join(map(str, opciones_seleccionadas))}")
                st.dataframe(alternativas_filtradas)

                # Generar archivo Excel para descargar
                excel_file = generar_excel(alternativas_filtradas)

                # Botón para descargar el archivo Excel
                st.download_button(
                    label="Descargar archivo Excel con las opciones seleccionadas",
                    data=excel_file,
                    file_name=f"alternativas_opciones_{','.join(map(str, opciones_seleccionadas))}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.write("No has seleccionado ninguna opción para mostrar.")
        else:
            st.write("No se encontraron alternativas para los códigos ingresados.")
    else:
        st.error("El archivo subido no contiene la columna 'codart'.")

