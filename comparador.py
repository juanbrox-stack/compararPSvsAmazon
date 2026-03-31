import streamlit as st
import pandas as pd
import io

# Configuración de la interfaz
st.set_page_config(page_title="Comparador & Optimizador SEO", layout="wide", page_icon="📦")

# --- FUNCIÓN DE RECORTE INTELIGENTE ---
def recortar_limpio(texto, limite=128):
    """
    Recorta el texto al límite indicado buscando el último punto, coma o espacio
    para no romper palabras ni dejar signos de puntuación huérfanos.
    """
    texto_str = str(texto).strip() if pd.notna(texto) else ""
    
    # Si ya cumple el límite, no tocar nada
    if len(texto_str) <= limite:
        return texto_str
    
    # Cortamos al límite para analizar dónde termina la última idea
    recorte_previo = texto_str[:limite]
    
    # Buscar último punto o coma para un corte gramatical
    ultimo_punto = recorte_previo.rfind('.')
    ultima_coma = recorte_previo.rfind(',')
    
    posicion_corte = max(ultimo_punto, ultima_coma)
    
    if posicion_corte != -1 and posicion_corte > (limite * 0.8): 
        # Si hay un signo y está cerca del final, cortamos ahí
        return recorte_previo[:posicion_corte].strip()
    else:
        # Si no hay signos o están muy lejos, buscamos el último espacio
        ultimo_espacio = recorte_previo.rfind(' ')
        if ultimo_espacio != -1:
            return recorte_previo[:ultimo_espacio].strip()
        return recorte_previo

# --- INTERFAZ STREAMLIT ---
st.title("🚀 Comparador de Referencias & Optimizador SEO")
st.markdown("""
Esta herramienta realiza dos tareas:
1. **Cruce:** Identifica SKUs de Amazon que no están en Prestashop.
2. **SEO:** Recorta los títulos de Amazon a **128 caracteres** de forma limpia para evitar errores en Prestashop.
""")

# --- BARRA LATERAL ---
st.sidebar.header("Configuración")
db_opcion = st.sidebar.selectbox("1. Base de datos destino:", ["Turaco", "Jabiru", "Marabu"])
pais_opcion = st.sidebar.selectbox("2. Selecciona el País:", ["ES", "FR", "IT", "DE", "PT", "UK"])

st.sidebar.divider()
st.sidebar.info(f"Salida: {db_opcion} | {pais_opcion} | Título máx: 128")

# --- ÁREA DE CARGA ---
col1, col2 = st.columns(2)
with col1:
    st.subheader("Fichero Prestashop")
    archivo_presta = st.file_uploader("Subir Excel (columna 'reference')", type=["xlsx"], key="ps")
with col2:
    st.subheader("Fichero Amazon")
    archivo_amazon = st.file_uploader("Subir Excel (A: SKU, B: ASIN, C: Título)", type=["xlsx"], key="amz")

if archivo_presta and archivo_amazon:
    try:
        with st.spinner('Procesando y optimizando títulos...'):
            df_presta = pd.read_excel(archivo_presta)
            df_amazon = pd.read_excel(archivo_amazon)

            # Normalizar columnas
            df_presta.columns = [str(c).strip() for c in df_presta.columns]
            df_amazon.columns = [str(c).strip() for c in df_amazon.columns]

            if 'reference' not in df_presta.columns:
                st.error("❌ No se encontró la columna 'reference' en Prestashop.")
            else:
                col_sku_amz = df_amazon.columns[0]
                col_asin_amz = df_amazon.columns[1]
                col_title_amz = df_amazon.columns[2]

                # 1. Identificar referencias nuevas
                refs_ps = set(df_presta['reference'].astype(str).str.strip())
                faltantes = df_amazon[~df_amazon[col_sku_amz].astype(str).str.strip().isin(refs_ps)].copy()

                # 2. Aplicar el recorte inteligente de 128 caracteres al título
                faltantes['Titulo_Limpio'] = faltantes[col_title_amz].apply(lambda x: recortar_limpio(x, 128))

                # 3. Formatear DataFrame final
                # Usamos el título optimizado en lugar del original
                resultado = faltantes[[col_sku_amz, 'Titulo_Limpio', col_asin_amz]].copy()
                resultado.columns = ['SKU', 'Título', 'ASIN']
                
                # Columnas fijas
                resultado['Activo'] = 1
                resultado['Marca'] = 'Cecotec'
                resultado['Proveedor'] = 'Cecotec'

                # --- RESULTADOS ---
                st.divider()
                st.success(f"Cruce y optimización completados.")
                st.metric(f"Referencias listas para {pais_opcion}", len(resultado))

                if not resultado.empty:
                    st.write("### Vista previa (Título recortado a 128 caracteres)")
                    st.dataframe(resultado.head(10), use_container_width=True)
                    
                    # Nombre del fichero
                    nombre_fichero = f"altas_{db_opcion.lower()}_{pais_opcion}_SEO.xlsx"
                    
                    # Preparar descarga
                    buffer = io.BytesIO()
                    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                        resultado.to_excel(writer, index=False, sheet_name='Altas_Optimizadas')
                    
                    st.download_button(
                        label=f"📥 Descargar Excel para {pais_opcion}",
                        data=buffer.getvalue(),
                        file_name=nombre_fichero,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                else:
                    st.info("No se han detectado referencias nuevas.")

    except Exception as e:
        st.error(f"Error: {e}")