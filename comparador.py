import streamlit as st
import pandas as pd
import io

# Configuración de la interfaz
st.set_page_config(page_title="Comparador Amazon vs Prestashop", layout="wide")

# --- INTERFAZ STREAMLIT ---
st.title("🚀 Comparador de Referencias (Versión Estable)")
st.markdown("""
Esta versión realiza el cruce directo entre Amazon y Prestashop. 
Identifica lo que está en Amazon pero no en tu base de datos, sin filtros de limpieza adicionales.
""")

# --- BARRA LATERAL (SIDEBAR) ---
st.sidebar.header("Configuración")

db_opcion = st.sidebar.selectbox(
    "1. Base de datos destino:", 
    ["Turaco", "Jabiru", "Marabu"]
)

pais_opcion = st.sidebar.selectbox(
    "2. Selecciona el País:",
    ["ES", "FR", "IT", "DE", "PT", "UK"]
)

st.sidebar.divider()
st.sidebar.write(f"**Destino:** {db_opcion}")
st.sidebar.write(f"**País:** {pais_opcion}")

# --- ÁREA PRINCIPAL ---
col1, col2 = st.columns(2)
with col1:
    st.subheader("Archivo Prestashop")
    archivo_presta = st.file_uploader("Subir Excel de Prestashop", type=["xlsx"], key="ps")
with col2:
    st.subheader("Archivo Amazon")
    archivo_amazon = st.file_uploader("Subir Excel de Amazon", type=["xlsx"], key="amz")

if archivo_presta and archivo_amazon:
    try:
        with st.spinner('Comparando referencias...'):
            # Leer los archivos Excel
            df_presta = pd.read_excel(archivo_presta)
            df_amazon = pd.read_excel(archivo_amazon)

            # Normalizar nombres de columnas (quitar espacios en blanco)
            df_presta.columns = [str(c).strip() for c in df_presta.columns]
            df_amazon.columns = [str(c).strip() for c in df_amazon.columns]

            if 'reference' not in df_presta.columns:
                st.error("❌ No se encontró la columna 'reference' en el archivo de Prestashop.")
            else:
                # Definir columnas de Amazon por su posición (A, B, C)
                col_sku_amz = df_amazon.columns[0]
                col_asin_amz = df_amazon.columns[1]
                col_title_amz = df_amazon.columns[2]

                # 1. Crear set de referencias existentes en Prestashop para comparar rápido
                refs_existentes = set(df_presta['reference'].astype(str).str.strip())

                # 2. Filtrar: Amazon SKUs que NO están en Prestashop
                # No aplicamos filtros de limpieza (Regex), solo el cruce directo
                faltantes = df_amazon[~df_amazon[col_sku_amz].astype(str).str.strip().isin(refs_existentes)].copy()

                # 3. Formatear el DataFrame final con las columnas solicitadas
                resultado_final = faltantes[[col_sku_amz, col_title_amz, col_asin_amz]].copy()
                resultado_final.columns = ['SKU', 'Título', 'ASIN']
                
                # Añadir columnas de valor fijo
                resultado_final['Activo'] = 1
                resultado_final['Marca'] = 'Cecotec'
                resultado_final['Proveedor'] = 'Cecotec'

                # --- MOSTRAR RESULTADOS ---
                st.divider()
                st.success(f"Cruce completado con éxito.")
                st.metric(f"Referencias nuevas para {pais_opcion}", len(resultado_final))

                if not resultado_final.empty:
                    st.dataframe(resultado_final, use_container_width=True)
                    
                    # Generar el nombre del fichero con las siglas del país
                    nombre_fichero = f"altas_{db_opcion.lower()}_{pais_opcion}.xlsx"
                    
                    # Convertir a Excel para descarga
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        resultado_final.to_excel(writer, index=False, sheet_name='Altas')
                    
                    st.download_button(
                        label=f"📥 Descargar Excel para {pais_opcion}",
                        data=output.getvalue(),
                        file_name=nombre_fichero,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                else:
                    st.info(f"No se han detectado referencias nuevas para {pais_opcion}.")

    except Exception as e:
        st.error(f"Error al procesar los archivos: {e}")
else:
    st.info("👋 Por favor, sube ambos archivos Excel para generar el listado de referencias.")