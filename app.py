import streamlit as st
import pandas as pd
from io import BytesIO

# Función para cargar el inventario desde Google Sheets
def load_inventory_file():
    inventario_url = "https://docs.google.com/spreadsheets/d/1Y9SgliayP_J5Vi2SdtZmGxKWwf1iY7ma/export?format=xlsx"
    inventario_api_df = pd.read_excel(inventario_url, sheet_name="Hoja1")
    return inventario_api_df

# Función para procesar faltantes y generar el resultado
def procesar_faltantes(faltantes_df, inventario_api_df, columnas_adicionales, bodega_seleccionada):
    faltantes_df.columns = faltantes_df.columns.str.lower().str.strip()
    inventario_api_df.columns = inventario_api_df.columns.str.lower().str.strip()

    # Verificación de columnas necesarias
    columnas_necesarias = {'cur', 'codart', 'faltante', 'embalaje'}
    if not columnas_necesarias.issubset(faltantes_df.columns):
        st.error(f"El archivo de faltantes debe contener las columnas: {', '.join(columnas_necesarias)}")
        return pd.DataFrame()  # Devuelve un DataFrame vacío si faltan columnas

    # Filtrar inventario por los códigos de faltantes
    cur_faltantes = faltantes_df['cur'].unique()
    alternativas_inventario_df = inventario_api_df[inventario_api_df['cur'].isin(cur_faltantes)]

    # Aplicar filtro de bodega si la columna 'bodega' está presente
    if 'bodega' in inventario_api_df.columns:
        alternativas_inventario_df = alternativas_inventario_df[alternativas_inventario_df['bodega'].isin(bodega_seleccionada)]
    else:
        st.warning("La columna 'bodega' no se encontró en el archivo de inventario.")

    # Filtrar alternativas disponibles (opción mayor a 0)
    alternativas_disponibles_df = alternativas_inventario_df[alternativas_inventario_df['opcion'] > 0]

    # Renombrar columnas para claridad
    alternativas_disponibles_df.rename(columns={
        'codart': 'codart_alternativa',
        'opcion': 'opcion_alternativa',
        'embalaje': 'embalaje_alternativa'
    }, inplace=True)

    # Merge para obtener alternativas específicas de los faltantes
    alternativas_disponibles_df = pd.merge(
        faltantes_df[['cur', 'codart', 'faltante', 'embalaje']],
        alternativas_disponibles_df,
        on='cur',
        how='inner'
    )

    alternativas_disponibles_df.sort_values(by=['codart', 'opcion_alternativa'], inplace=True)

    # Selección de la mejor alternativa para cada artículo faltante
    mejores_alternativas = []
    for codart_faltante, group in alternativas_disponibles_df.groupby('codart'):
        faltante_cantidad = group['faltante'].iloc[0]

        # Seleccionar la mejor opción en la bodega filtrada o globalmente si no cumple
        mejor_opcion_bodega = group[group['opcion_alternativa'] >= faltante_cantidad]
        mejor_opcion = mejor_opcion_bodega.head(1) if not mejor_opcion_bodega.empty else group.nlargest(1, 'opcion_alternativa')
        
        mejores_alternativas.append(mejor_opcion.iloc[0])

    resultado_final_df = pd.DataFrame(mejores_alternativas)

    # Selección de columnas finales
    columnas_finales = ['cur', 'codart', 'faltante', 'embalaje', 'codart_alternativa', 'opcion_alternativa', 'embalaje_alternativa', 'opcion', 'bodega']
    columnas_finales.extend([col.lower() for col in columnas_adicionales])
    columnas_presentes = [col for col in columnas_finales if col in resultado_final_df.columns]
    resultado_final_df = resultado_final_df[columnas_presentes]

    return resultado_final_df

# Interfaz de usuario en Streamlit
st.title('Buscador de Alternativas por Código de Artículo')

# Botón para actualizar inventario
if st.button('Actualizar inventario'):
    st.cache_data.clear()  # Limpia la caché para cargar el archivo actualizado

# Subir archivo de faltantes
uploaded_file = st.file_uploader("Sube tu archivo de faltantes", type=["xlsx", "csv"])

if uploaded_file:
    # Leer el archivo subido
    faltantes_df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('xlsx') else pd.read_csv(uploaded_file)

    # Verificar la existencia de la columna 'codart'
    if 'codart' in faltantes_df.columns:
        # Cargar el inventario
        inventario_api_df = load_inventory_file()

        # Selección de bodega
        if 'bodega' in inventario_api_df.columns:
            bodegas_disponibles = inventario_api_df['bodega'].unique().tolist()
            bodega_seleccionada = st.multiselect("Seleccione la bodega", options=bodegas_disponibles, default=bodegas_disponibles)
        else:
            bodega_seleccionada = []

        # Selección de columnas adicionales
        columnas_adicionales = st.multiselect(
            "Selecciona columnas adicionales para incluir en el archivo final:",
            options=["presentacionart", "numlote", "fechavencelote"],
            default=[]
        )

        # Procesar faltantes
        resultado_final_df = procesar_faltantes(faltantes_df, inventario_api_df, columnas_adicionales, bodega_seleccionada)

        if not resultado_final_df.empty:
            st.write("Archivo procesado correctamente.")
            st.dataframe(resultado_final_df)

            # Función para exportar a Excel
            def to_excel(df):
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='Alternativas')
                return output.getvalue()

            # Botón para descargar el archivo Excel
            st.download_button(
                label="Descargar archivo de alternativas",
                data=to_excel(resultado_final_df),
                file_name="alternativas_disponibles.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.write("No se encontraron alternativas para los códigos ingresados.")
    else:
        st.error("El archivo subido no contiene la columna 'codart'.")
