import streamlit as st
import pandas as pd
from io import BytesIO

# Configuración de la página
st.set_page_config(page_title="Comparador SKU: Prestashop vs Amazon", layout="wide")

def main():
    st.title("🔍 Comparador de Inventario: Amazon a Prestashop")
    st.markdown("""
    Esta herramienta identifica qué productos de tu **Listing de Amazon** no existen todavía en tu **Base de Datos de Prestashop**.
    """)

    # --- SECCIÓN DE CARGA DE ARCHIVOS ---
    st.sidebar.header("Configuración de Archivos")
    
    file_ps = st.sidebar.file_uploader("1. Base de datos Prestashop (.xlsx)", type=['xlsx'])
    col_ps = st.sidebar.text_input("Nombre columna SKU en Prestashop", value="Reference")

    file_amz = st.sidebar.file_uploader("2. Listing de Amazon (.xlsx)", type=['xlsx'])
    col_amz = st.sidebar.text_input("Nombre columna SKU en Amazon", value="seller-sku")

    if file_ps and file_amz:
        try:
            # Lectura de los archivos
            df_ps = pd.read_excel(file_ps)
            df_amz = pd.read_excel(file_amz)

            # --- LÓGICA DE COMPARACIÓN ---
            # 1. Limpiar los SKUs de Prestashop (quitar espacios y asegurar que son texto)
            # Usamos un 'set' para que la búsqueda sea extremadamente rápida
            skus_prestashop = set(df_ps[col_ps].astype(str).str.strip().unique())
            
            # 2. Identificar cuáles de Amazon NO están en ese set
            # Filtramos el DataFrame de Amazon usando una máscara booleana
            mask_faltantes = ~df_amz[col_amz].astype(str).str.strip().isin(skus_prestashop)
            df_faltantes = df_amz[mask_faltantes].copy()

            # --- VISUALIZACIÓN DE RESULTADOS ---
            col1, col2, col3 = st.columns(3)
            col1.metric("Productos en Amazon", len(df_amz))
            col2.metric("Productos en Prestashop", len(df_ps))
            col3.metric("SKUs Faltantes", len(df_faltantes), delta_color="inverse")

            if not df_faltantes.empty:
                st.subheader("📋 Lista de SKUs detectados como faltantes")
                st.dataframe(df_faltantes, use_container_width=True)

                # --- GENERACIÓN DEL EXCEL DE SALIDA ---
                output = BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df_faltantes.to_excel(writer, index=False, sheet_name='SKUs_Faltantes')
                
                excel_data = output.getvalue()

                st.download_button(
                    label="📥 Descargar Excel con faltantes",
                    data=excel_data,
                    file_name="skus_faltantes_en_prestashop.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.success("✅ ¡Enhorabuena! Todos los SKUs de Amazon ya existen en Prestashop.")

        except KeyError as e:
            st.error(f"Error: No se encontró la columna {e} en uno de los archivos. Revisa los nombres en la barra lateral.")
        except Exception as e:
            st.error(f"Ocurrió un error inesperado: {e}")
    else:
        st.info("👋 Por favor, sube ambos archivos Excel en la barra lateral para comenzar la comparación.")

if __name__ == "__main__":
    main()