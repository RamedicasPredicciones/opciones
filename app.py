import streamlit as st
import pandas as pd
from io import BytesIO

# Cargar archivo de Google Sheets desde el enlace proporcionado
def load_inventory_file():
    inventario_url = "https://docs.google.com/spreadsheets/d/1Y9SgliayP_J5Vi2SdtZmGxKWwf1iY7ma/export?format=xlsx"
    inventario_api_df = pd.read_excel(inventario_url, sheet_name="Hoja1")
    return inventario_api_df

# Función para procesar las alternativas
def procesar_alternativas(inventario_api_df, codigo_articulo, opcion_seleccionada=None, columnas_adicionales=[]):
    # Filtrar el inventario según el código de artículo (codart) ingresado y obtener CUR correspondiente
    cur_articulo = inventario_api_df[inventario_api_df['codart'] == codigo_articulo]['cur'].values

    # Si no se encuentra el CUR para el código, devolver un DataFrame vacío
    if len(cur_articulo) == 0:
        return pd.DataFrame()
    
    # Buscar las alternativas disponibles con el mismo CUR
    alternativas_disponibles_df = inventario_api_df[inventario_api_df['cur'] == cur_articulo[0]]

    # Asegurarse de que medvitdisp es numérico y manejar valores nulos
    alternativas_disponibles_df['medvitdisp'] = pd.to_numeric(alternativas_disponibles_df['medvitdisp'], errors='coerce')
    alternativas_disponibles_df = alternativas_disponibles_df.dropna(subset=['medvitdisp'])
    alternativas_disponibles_df = alternativas_disponibles_df[alternativas_disponibles_df['medvitdisp'] > 0]

    # Ordenar por la cantidad disponible
    alternativas_disponibles_df.sort_values(by='medvitdisp', ascending=False, inplace=True)

    # Filtrar si se seleccionó una opción específica
    if opcion_seleccionada is not None:
        alternativas_disponibles_df = alternativas_disponibles_df.head(opcion_seleccionada)

    # Incluir solo las columnas seleccionadas
    columnas_basicas = ['cur', 'codart', 'medvitdisp', 'bodega']  # columnas básicas siempre incluidas
    columnas_finales = columnas_basicas + columnas_adicionales
    alternativas_disponibles_df = alternativas_disponibles_df[columnas_finales]

    return alternativas_disponibles_df

# Streamlit UI
st.title('Buscador de Alternativas por Código de Artículo')

# Cargar inventario
inventario_api_df = load_inventory_file()

# Campo para ingresar el código del producto (codart)
codigo_articulo = st.text_input("Ingrese el código del artículo (codart):")

# Selección de columnas adicionales
columnas_disponibles = ["emb", "nomart", "presentación", "precio_control_directo", "cum", "n_comercial"]
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
