import streamlit as st
import pandas as pd
import requests
from io import BytesIO

# Función para cargar el inventario desde la API
def cargar_inventario_y_completar():
    # URL de la API para obtener los productos
    url_inventario = "https://apkit.ramedicas.com/api/items/ws-batchsunits?token=3f8857af327d7f1adb005b81a12743bc17fef5c48f228103198100d4b032f556"
    try:
        # Hacer la solicitud GET para obtener los datos de la API
        response = requests.get(url_inventario, verify=False)
        if response.status_code == 200:
            # Convertir la respuesta JSON a un DataFrame
            data_inventario = response.json()
            inventario_df = pd.DataFrame(data_inventario)

            # Normalizar las columnas para evitar discrepancias en mayúsculas/minúsculas
            inventario_df.columns = inventario_df.columns.str.lower().str.strip()

            # Filtrar solo las bodegas permitidas
            bodegas_permitidas = ["A011", "C015", "C018", "C017"]
            inventario_df = inventario_df[inventario_df['bodega'].isin(bodegas_permitidas)]
            
            return inventario_df
        else:
            st.error(f"Error al obtener datos de la API: {response.status_code}")
            return pd.DataFrame()
    except requests.exceptions.RequestException as e:
        st.error(f"Error en la conexión con la API: {e}")
        return pd.DataFrame()

# Función para procesar las alternativas basadas en los productos faltantes
def procesar_alternativas(faltantes_df, inventario_api_df):
    faltantes_df.columns = faltantes_df.columns.str.lower().str.strip()

    if not {'cur', 'codart', 'embalaje'}.issubset(faltantes_df.columns):
        st.error("El archivo de faltantes debe contener las columnas: 'cur', 'codart' y 'embalaje'")
        return pd.DataFrame()

    cur_faltantes = faltantes_df['cur'].unique()
    alternativas_inventario_df = inventario_api_df[inventario_api_df['cur'].isin(cur_faltantes)]

    columnas_necesarias = ['codart', 'cur', 'opcionart', 'nomart', 'descontart']
    for columna in columnas_necesarias:
        if columna not in alternativas_inventario_df.columns:
            st.error(f"La columna '{columna}' no se encuentra en el inventario. Verifica el archivo de origen.")
            st.stop()

    alternativas_inventario_df['opcionart'] = alternativas_inventario_df['opcionart'].fillna(0).astype(int)

    alternativas_inventario_df = alternativas_inventario_df.rename(columns={
        'codart': 'codart_alternativa'
    })

    alternativas_inventario_df = alternativas_inventario_df[['cur', 'codart_alternativa', 'opcionart', 'nomart', 'descontart']]

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

# Subir archivo de faltantes
uploaded_file = st.file_uploader("Sube un archivo con los productos faltantes (contiene 'codart', 'cur' y 'embalaje')", type=["xlsx", "csv"])

if uploaded_file:
    if uploaded_file.name.endswith('xlsx'):
        faltantes_df = pd.read_excel(uploaded_file)
    else:
        faltantes_df = pd.read_csv(uploaded_file)

    inventario_api_df = cargar_inventario_y_completar()

    if not inventario_api_df.empty:
        alternativas_disponibles_df = procesar_alternativas(faltantes_df, inventario_api_df)

        if not alternativas_disponibles_df.empty:
            st.write("Filtra las alternativas por opciones:")

            # Filtrar las opciones disponibles para excluir el valor 0
            opciones_disponibles = alternativas_disponibles_df['opcion'].unique().tolist()
            opciones_disponibles = [opcion for opcion in opciones_disponibles if opcion != 0]

            opciones_seleccionadas = st.multiselect(
                "Selecciona las opciones que deseas visualizar:",
                options=opciones_disponibles,
                default=[]
            )

            if opciones_seleccionadas:
                alternativas_filtradas_df = alternativas_disponibles_df[
                    alternativas_disponibles_df['descontart'].isin(opciones_seleccionadas)
                ]
                st.write(alternativas_filtradas_df)

                # Botón para descargar el archivo Excel
                output = generar_excel(alternativas_filtradas_df)
                st.download_button(
                    label="Descargar resultados en Excel",
                    data=output,
                    file_name="alternativas_filtradas.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

