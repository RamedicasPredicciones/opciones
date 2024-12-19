import requests
import pandas as pd
import streamlit as st

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
            st.success("Datos cargados correctamente desde la API.")
            return inventario_df
        else:
            st.error(f"Error al cargar los datos del inventario: Código de estado {response.status_code}")
            return pd.DataFrame()
    except requests.exceptions.RequestException as e:
        st.error(f"Error en la solicitud a la API: {e}")
        return pd.DataFrame()

# Interfaz de Streamlit
st.title("Carga de Inventario desde API")
inventario_df = cargar_inventario_y_completar()

if not inventario_df.empty:
    st.subheader("Inventario cargado:")
    st.dataframe(inventario_df)
else:
    st.warning("No se pudieron cargar datos del inventario.")
