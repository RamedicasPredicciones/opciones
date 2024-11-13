import streamlit as st
import pandas as pd
from io import BytesIO

# Cargar archivo de Google Sheets desde el enlace proporcionado
def load_inventory_file():
    inventario_url = "https://docs.google.com/spreadsheets/d/1Y9SgliayP_J5Vi2SdtZmGxKWwf1iY7ma/export?format=xlsx"
    inventario_api_df = pd.read_excel(inventario_url, sheet_name="Hoja1")
    return inventario_api_df

# Función para procesar las alternativas en base a 'codart'
def procesar_alternativas(inventario_api_df, codigo_articulo, opcion_seleccionada=None, columnas_adicionales=[]):
    # Filtrar el inventario para obtener el 'cur' correspondiente al 'codart' ingresado
    cur_producto = inventario_api_df[inventario_api_df['codart'] == codigo_articulo]['cur'].unique()
    if len(cur_producto) == 0:
        st.error(f"No se encontró el CUR para el artículo {codigo_articulo}.")
        return pd.DataFrame()

    # Filtrar las alternativas usando el 'cur' obtenido
    alternativas_disponibles_df = inventario_api_df[inventario_api_df['cur'].isin(cur_producto)]
    alternativas_disponibles_df = alternativas_disponibles_df[alternativas_disponibles_df['unidadespresentacionlote'] > 0]
    alternativas_disponibles_df.sort_values(by='unidadespresentacionlote', ascending=False, inplace=True)

    # Filtrar si se seleccionó una opción específica
    if opcion_seleccionada is not None:
        alternativas_disponibles_df = alternativas_disponibles_df.head(opcion_seleccionada)

    # Incluir solo las columnas seleccionadas
    columnas_basicas = ['cur', 'codart', 'unidadespresentacionlote', 'bodega']  # columnas siempre incluidas
    columnas_finales = columnas_basicas + columnas_adicionales
    alternativas_disponibles_df = alternativas_disponibles_df[columnas_finales]

    return alternativas_disponibles_df

# Streamlit UI
st.title('Buscador de Alternativas por Código')

# Cargar inventario
inventario_api_df = load_inventory_file()

# Campo para ingresar el código del artículo
codigo_articulo = st.text_input("Ingrese el código del artículo (codart):")

# Selección de columnas adicionales
columnas_disponibles = ["emb", "nomart", "presentacionart", "numlote", "fechavencelote"]
columnas_adicionales = st.multiselect(
    "Selecciona columnas adicionales para incluir en el archivo final:",
    options=columnas_disponibles,
    default=["emb", "nomart"]
)

if codigo_articulo:
    # Mostrar opciones de alternativas si hay resultados
    opciones_disponibles = procesar_alternativas(inventario_api_df, codigo_articulo, columnas_adicionales=columnas_adicionales)

    if not opciones_disponibles.empty:
        st.write("Alternativas disponibles:")
        st.dataframe(opciones_disponibles)

        # Seleccionar el número de la mejor opción
        opcion_seleccionada = st.number_input(
            "Ingrese el número de la alternativa que desea ver:",
            min_value=1,
            max_value=len(opciones_disponibles),
            step=1
        )

        # Filtrar por opción seleccionada y mostrar
        alternativa_seleccionada_df = procesar_alternativas(inventario_api_df, codigo_articulo, opcion_seleccionada, columnas_adicionales)
        st.write("Alternativa seleccionada:")
        st.dataframe(alternativa_seleccionada_df)

        # Función para exportar a Excel
        def to_excel(df):
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Alternativa')
            return output.getvalue()

        st.download_button(
            label="Descargar alternativa seleccionada",
            data=to_excel(alternativa_seleccionada_df),
            file_name=f'alternativa_{codigo_articulo}.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    else:
        st.write("No se encontraron alternativas para el código ingresado.")
