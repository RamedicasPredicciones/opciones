import streamlit as st
import pandas as pd
from io import BytesIO

# Cargar archivo de inventario desde Google Sheets
def load_inventory_file():
    inventario_url = "https://docs.google.com/spreadsheets/d/1Y9SgliayP_J5Vi2SdtZmGxKWwf1iY7ma/export?format=xlsx"
    inventario_api_df = pd.read_excel(inventario_url, sheet_name="Hoja1")
    return inventario_api_df

# Función para procesar el archivo de faltantes y generar el resultado
def procesar_faltantes(faltantes_df, inventario_api_df, columnas_adicionales, bodega_seleccionada, opciones_seleccionadas):
    faltantes_df.columns = faltantes_df.columns.str.lower().str.strip()
    inventario_api_df.columns = inventario_api_df.columns.str.lower().str.strip()

    # Verificar que el archivo de faltantes tenga las columnas necesarias
    columnas_necesarias = {'cur', 'codart', 'faltante', 'embalaje'}
    if not columnas_necesarias.issubset(faltantes_df.columns):
        st.error(f"El archivo de faltantes debe contener las columnas: {', '.join(columnas_necesarias)}")
        return pd.DataFrame()  # Devuelve un DataFrame vacío si faltan columnas

    # Filtrar inventario por CUR de los faltantes
    cur_faltantes = faltantes_df['cur'].unique()
    alternativas_inventario_df = inventario_api_df[inventario_api_df['cur'].isin(cur_faltantes)]

    # Filtrar por bodega seleccionada
    if bodega_seleccionada:
        alternativas_inventario_df = alternativas_inventario_df[alternativas_inventario_df['bodega'].isin(bodega_seleccionada)]

    # Filtrar por las opciones seleccionadas en 'opcion' si hay selección
    if opciones_seleccionadas:
        alternativas_inventario_df = alternativas_inventario_df[alternativas_inventario_df['opcion'].isin(opciones_seleccionadas)]

    # Excluir filas donde 'unidadespresentacionlote' es cero o menor
    alternativas_disponibles_df = alternativas_inventario_df[alternativas_inventario_df['unidadespresentacionlote'] > 0]

    # Renombrar columnas para identificar la alternativa
    alternativas_disponibles_df.rename(columns={
        'codart': 'codart_alternativa',
        'opcion': 'opcion_alternativa',
        'embalaje': 'embalaje_alternativa'
    }, inplace=True)

    # Realizar un merge para obtener las mejores alternativas
    alternativas_disponibles_df = pd.merge(
        faltantes_df[['cur', 'codart', 'faltante', 'embalaje']],
        alternativas_disponibles_df,
        on='cur',
        how='inner'
    )

    alternativas_disponibles_df.sort_values(by=['codart', 'unidadespresentacionlote'], inplace=True)

    # Selección de la mejor alternativa
    mejores_alternativas = []
    for codart_faltante, group in alternativas_disponibles_df.groupby('codart'):
        faltante_cantidad = group['faltante'].iloc[0]
        # Buscar la mejor opción en la bodega seleccionada o tomar la mayor disponible
        mejor_opcion_bodega = group[group['unidadespresentacionlote'] >= faltante_cantidad]
        mejor_opcion = mejor_opcion_bodega.head(1) if not mejor_opcion_bodega.empty else group.nlargest(1, 'unidadespresentacionlote')
        
        mejores_alternativas.append(mejor_opcion.iloc[0])

    resultado_final_df = pd.DataFrame(mejores_alternativas)

    # Seleccionar columnas finales
    columnas_finales = ['cur', 'codart', 'faltante', 'embalaje', 'codart_alternativa', 'opcion_alternativa', 'embalaje_alternativa', 'unidadespresentacionlote', 'bodega']
    columnas_finales.extend([col.lower() for col in columnas_adicionales])
    columnas_presentes = [col for col in columnas_finales if col in resultado_final_df.columns]
    resultado_final_df = resultado_final_df[columnas_presentes]

    return resultado_final_df

# Streamlit UI
st.title('Generador de Alternativas de Faltantes')

# Botón para actualizar inventario
if st.button('Actualizar inventario'):
    st.cache_data.clear()  # Limpia la caché para cargar el archivo actualizado

uploaded_file = st.file_uploader("Sube tu archivo de faltantes", type="xlsx")

if uploaded_file:
    faltantes_df = pd.read_excel(uploaded_file)
    inventario_api_df = load_inventory_file()

    # Selección de bodegas
    bodegas_disponibles = inventario_api_df['bodega'].unique().tolist()
    bodega_seleccionada = st.multiselect("Seleccione la bodega", options=bodegas_disponibles, default=bodegas_disponibles)

    # Selección de opciones manualmente
    opciones_disponibles = inventario_api_df['opcion'].unique()
    opciones_seleccionadas = st.multiselect(
        "Selecciona las opciones que deseas ver (puedes elegir varias)",
        options=opciones_disponibles
    )

    # Selección de columnas adicionales para incluir
    columnas_adicionales = st.multiselect(
        "Selecciona columnas adicionales para incluir en el archivo final:",
        options=["presentacionart", "numlote", "fechavencelote"],
        default=[]
    )

    # Procesar las alternativas
    resultado_final_df = procesar_faltantes(faltantes_df, inventario_api_df, columnas_adicionales, bodega_seleccionada, opciones_seleccionadas)

    if not resultado_final_df.empty:
        st.write("Archivo procesado correctamente.")
        st.dataframe(resultado_final_df)

        # Exportar a Excel
        def to_excel(df):
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Alternativas')
            return output.getvalue()

        st.download_button(
            label="Descargar archivo de alternativas",
            data=to_excel(resultado_final_df),
            file_name='alternativas_disponibles.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    else:
        st.write("No se encontraron alternativas para los códigos ingresados.")
