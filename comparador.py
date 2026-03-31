import streamlit as st
import pandas as pd
import io
import re

# Configuración de la interfaz
st.set_page_config(page_title="Comparador Amazon vs Prestashop", layout="wide")

def es_sku_valido(sku):
    """
    Reglas de validación actualizadas:
    1. No termina en punto.
    2. No empieza por F.
    3. Estructura: (Opcional S?A01_EU01_) + (Opcional A, S, IT, FR, DE) + (5 o 6 dígitos).
    """
    sku = str(sku).strip()
    
    # 1. Descarte inmediato
    if sku.endswith('.') or sku.startswith('F'):
        return False
    
    # 2. PATRÓN REGEX ACTUALIZADO:
    # ^(S?A01_EU01_)?    -> Prefijo complejo opcional (SA01_EU01_ o A01_EU01_)
    # (A|S|IT|FR|DE)?    -> Prefijo de país/canal opcional
    # \d{5,6}$           -> ACEPTA 5 O 6 DÍGITOS EXACTOS al final
    patron = r'^(S?A01_EU01_)?(A|S|IT|FR|DE)?\d{5,6}$'
    
    if re.match(patron, sku):
        return True
    
    # 3. Caso: Número puro de 5 o 6 dígitos
    if sku.isdigit() and (len(sku) == 5 or len(sku) == 6):
        return True
        
    return False

# --- INTERFAZ STREAMLIT ---
st.title("🚀 Comparador de Referencias (Versión Corregida)")
st.markdown("Identifica productos nuevos permitiendo SKUs de **5 y 6 dígitos** con prefijos `SA01_EU01_`, `FR`, `DE`, `IT`, `A` o `S`.")

db_opcion = st.sidebar.selectbox("Base de datos destino:", ["Turaco", "Jabiru", "Marabu"])

col1, col2 = st.columns(2)
with col1:
    archivo_presta = st.file_uploader("Excel Prestashop (columna 'reference')", type=["xlsx"])
with col2:
    archivo_amazon = st.file_uploader("Excel Amazon (A: SKU, B: ASIN, C: Título)", type=["xlsx"])

if archivo_presta and archivo_amazon:
    try:
        with st.spinner('Comparando catálogos...'):
            df_presta = pd.read_excel(archivo_presta)
            df_amazon = pd.read_excel(archivo_amazon)

            df_presta.columns = [str(c).strip() for c in df_presta.columns]
            df_amazon.columns = [str(c).strip() for c in df_amazon.columns]

            if 'reference' not in df_presta.columns:
                st.error("❌ No existe la columna 'reference' en el archivo de Prestashop.")
            else:
                col_sku_amz = df_amazon.columns[0]
                col_asin_amz = df_amazon.columns[1]
                col_title_amz = df_amazon.columns[2]

                # 1. Cruzar datos (identificar qué no está en PS)
                refs_ps = set(df_presta['reference'].astype(str).str.strip())
                faltantes = df_amazon[~df_amazon[col_sku_amz].astype(str).str.strip().isin(refs_ps)].copy()

                # 2. Aplicar limpieza con el nuevo criterio de 5-6 dígitos
                faltantes['valido'] = faltantes[col_sku_amz].apply(es_sku_valido)
                resultado_final = faltantes[faltantes['valido'] == True].copy()

                # 3. Formatear salida
                resultado_final = resultado_final[[col_sku_amz, col_title_amz, col_asin_amz]]
                resultado_final.columns = ['SKU', 'Título', 'ASIN']
                resultado_final['Activo'] = 1
                resultado_final['Marca'] = 'Cecotec'
                resultado_final['Proveedor'] = 'Cecotec'

                st.divider()
                st.metric("Nuevos productos válidos encontrados", len(resultado_final))

                if not resultado_final.empty:
                    st.dataframe(resultado_final, use_container_width=True)
                    
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        resultado_final.to_excel(writer, index=False, sheet_name='Importar')
                    
                    st.download_button(
                        label="📥 Descargar Excel para Prestashop",
                        data=output.getvalue(),
                        file_name=f"altas_{db_opcion.lower()}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                else:
                    st.warning("No se encontraron SKUs que cumplan los criterios de filtrado.")

    except Exception as e:
        st.error(f"Error: {e}")