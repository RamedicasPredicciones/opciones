import pandas as pd
import streamlit as st

# Cargar los archivos
def cargar_archivos():
    archivo_faltantes = st.file_uploader("Sube el archivo de faltantes", type=["xlsx", "csv"])
    archivo_inventario = st.file_uploader("Sube el archivo de inventario", type=["xlsx", "csv"])
    
    if archivo_faltantes is not None and archivo_inventario is not None:
        faltantes_df = pd.read_excel(archivo_faltantes) if archivo_faltantes.name.endswith("xlsx") else pd.read_csv(archivo_faltantes)
        inventario_df = pd.read_excel(archivo_inventario) if archivo_inventario.name.endswith("xlsx") else pd.read_csv(archivo_inventario)
        return faltantes_df, inventario_df
    return None, None

# Filtrar alternativas basadas en el código de artículo
def filtrar_alternativas(faltantes_df, inventario_df):
    codigos_faltantes = faltantes_df['cur'].unique()  # Los códigos que subiste
    alternativas = inventario_df[inventario_df['cur'].isin(codigos_faltantes)]
    return alternativas

# Filtrar por opciones seleccionadas
def filtrar_por_opciones(df, opciones_seleccionadas):
    if opciones_seleccionadas:
        return df[df['opcion'].isin(opciones_seleccionadas)]
    return df

# Generar un archivo Excel con los datos filtrados
def generar_excel(df):
    output = "alternativas_filtradas.xlsx"
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name="Alternativas")
    return output

# Interfaz Streamlit
def app():
    st.title("Filtrar y Descargar Alternativas de Artículos")

    # Cargar los archivos
    faltantes_df, inventario_df = cargar_archivos()
    
    if faltantes_df is not None and inventario_df is not None:
        # Mostrar las primeras filas de los datos cargados
        st.write("Datos de Faltantes")
        st.write(faltantes_df.head())
        
        st.write("Datos de Inventario")
        st.write(inventario_df.head())
        
        # Filtrar alternativas basadas en los códigos de los artículos
        alternativas_df = filtrar_alternativas(faltantes_df, inventario_df)
        
        # Mostrar los resultados de las alternativas disponibles
        st.write("Alternativas Disponibles")
        st.write(alternativas_df.head())
        
        # Selección de opciones
        opciones_unicas = alternativas_df['opcion'].unique()
        opciones_seleccionadas = st.multiselect("Selecciona las opciones que deseas ver", opciones_unicas, default=opciones_unicas[:3])
        
        # Filtrar según las opciones seleccionadas
        alternativas_filtradas = filtrar_por_opciones(alternativas_df, opciones_seleccionadas)
        
        # Mostrar las alternativas filtradas
        st.write(f"Alternativas filtradas por opción ({', '.join(map(str, opciones_seleccionadas))})")
        st.write(alternativas_filtradas)
        
        # Generar y descargar el archivo Excel
        if st.button("Descargar Excel"):
            archivo = generar_excel(alternativas_filtradas)
            st.download_button("Descargar archivo Excel", archivo, file_name="alternativas_filtradas.xlsx")

# Ejecutar la app
if __name__ == "__main__":
    app()
