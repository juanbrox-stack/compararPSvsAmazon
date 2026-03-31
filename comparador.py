Aimport streamlit as st
import pandas as pd
import io
import re

# Configuración de la interfaz
st.set_page_config(page_title="Comparador Amazon vs Prestashop", layout="wide")

def es_sku_valido(sku):
    """
    Reglas de validación:
    1. No termina en punto.
    2. No empieza por F.
    3. Estructura: (Opcional SA01_EU01_ o A01_EU01_) + (Opcional A, S, IT, FR, DE) + 5 dígitos exactos.
    """
    sku = str(sku).strip()
    
    # Descarte inmediato
    if sku.endswith('.') or sku.startswith('F'):
        return False
    
    # Patrón Regex:
    # ^(S?A01_EU01_)? -> Prefijo SA01 o A01 opcional
    # (A|S|IT|FR|DE)? -> Prefijo de país/canal opcional
    # \d{5}$          -> 5 dígitos obligatorios al final
    patron = r'^(S?A01_EU01_)?(A|S|IT|FR|DE)?\d{5}$'
    
    if re.match(patron, sku):
        return True
    
    # Caso: Número puro de 5 dígitos
    if sku.isdigit() and len(sku) == 5:
        return True
        
    return False

# --- INTERFAZ STREAMLIT ---
st.title("🚀 Comparador de Referencias para Altas")
st.markdown("""
Esta herramienta identifica productos en Amazon que **no existen** en tu base de datos de Prestashop, 
aplicando filtros de limpieza para asegurar que solo se procesen SKUs correctos.
""")

# Selector de base de datos
db_opcion = st.sidebar.selectbox(
    "Base de datos de destino:",
    ["Turaco", "Jabiru", "Marabu"]
)

st.sidebar.divider()
st.sidebar.info(f"Configuración activa: **{db_opcion}**")

# Columnas de carga
col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Base Prestashop")
    archivo_presta = st.file_uploader("Arrastra el Excel de Prestashop", type=["xlsx"], key="presta")

with col2:
    st.subheader("2. Listado Amazon")
    archivo_amazon = st.file_uploader("Arrastra el Excel de Amazon", type=["xlsx"], key="amazon")

# --- PROCESAMIENTO ---
if archivo_presta and archivo_amazon:
    try:
        # Cargar datos
        with st.spinner('Procesando y cruzando datos...'):
            df_presta = pd.read_excel(archivo_presta)
            df_amazon = pd.read_excel(archivo_amazon)

            # Normalizar nombres de columnas
            df_presta.columns = [str(c).strip() for c in df_presta.columns]
            df_amazon.columns = [str(c).strip() for c in df_amazon.columns]

            if 'reference' not in df_presta.columns:
                st.error("❌ Error: No se encontró la columna 'reference' en el archivo de Prestashop.")
            else:
                # Columnas de Amazon por posición: A=0 (SKU), B=1 (ASIN), C=2 (Título)
                col_sku_amz = df_amazon.columns[0]
                col_asin_amz = df_amazon.columns[1]
                col_title_amz = df_amazon.columns[2]

                # 1. Obtener referencias actuales de Prestashop
                referencias_existentes = set(df_presta['reference'].astype(str).str.strip())

                # 2. Identificar qué hay en Amazon que NO está en Prestashop
                faltantes = df_amazon[~df_amazon[col_sku_amz].astype(str).str.strip().isin(referencias_existentes)].copy()

                # 3. Aplicar limpieza de SKUs
                faltantes['valido'] = faltantes[col_sku_amz].apply(es_sku_valido)
                resultado_limpio = faltantes[faltantes['valido'] == True].copy()

                # 4. Dar formato final
                final_df = resultado_limpio[[col_sku_amz, col_title_amz, col_asin_amz]].copy()
                final_df.columns = ['SKU', 'Título', 'ASIN']
                
                # Añadir columnas fijas requeridas
                final_df['Activo'] = 1
                final_df['Marca'] = 'Cecotec'
                final_df['Proveedor'] = 'Cecotec'

                # --- MOSTRAR RESULTADOS ---
                st.divider()
                m1, m2 = st.columns(2)
                m1.metric("Total Amazon no en PS", len(faltantes))
                m2.metric("SKUs válidos tras limpieza", len(final_df))

                if not final_df.empty:
                    st.write(f"### Vista previa de nuevos productos para {db_opcion}")
                    st.dataframe(final_df.head(50), use_container_width=True)

                    # Botón de descarga
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        final_df.to_excel(writer, index=False, sheet_name='Altas')
                    
                    st.download_button(
                        label="📥 Descargar Excel para Importación",
                        data=output.getvalue(),
                        file_name=f"nuevas_referencias_{db_opcion.lower()}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                else:
                    st.warning("No se encontraron SKUs nuevos que cumplan con las reglas de 5 dígitos.")

    except Exception as e:
        st.error(f"Se produjo un error durante el análisis: {e}")
else:
    st.info("👋 Por favor, sube ambos archivos para comparar las referencias.")