import streamlit as st
import pandas as pd
import io

# Configuración de la interfaz
st.set_page_config(page_title="Comparador & Limpieza SEO", layout="wide", page_icon="📦")

# --- FUNCIÓN DE LIMPIEZA Y RECORTE ---
def limpiar_y_recortar(texto, limite=128):
    """
    1. Sustituye ';' por un espacio.
    2. Recorta el texto al límite indicado buscando el último punto, coma o espacio.
    """
    if pd.isna(texto):
        return ""
    
    # Convertir a string y sustituir punto y coma por espacio
    texto_limpio = str(texto).replace(';', ' ').strip()
    
    # Si ya cumple el límite después de quitar los ';', no tocar nada
    if len(texto_limpio) <= limite:
        return texto_limpio
    
    # Cortamos al límite para analizar el punto de ruptura
    recorte_previo = texto_limpio[:limite]
    
    # Buscar último punto o coma para un corte gramatical
    ultimo_punto = recorte_previo.rfind('.')
    ultima_coma = recorte_previo.rfind(',')
    
    # Priorizamos signos de puntuación si están cerca del final (último 20% del límite)
    posicion_corte = max(ultimo_punto, ultima_coma)
    
    if posicion_corte != -1 and posicion_corte > (limite * 0.8): 
        return recorte_previo[:posicion_corte].strip()
    else:
        # Si no hay signos cerca, buscamos el último espacio para no romper una palabra
        ultimo_espacio = recorte_previo.rfind(' ')
        if ultimo_espacio != -1:
            return recorte_previo[:ultimo_espacio].strip()
        return recorte_previo

# --- INTERFAZ STREAMLIT ---
st.title("🚀 Comparador de Referencias & Limpieza de Títulos")
st.markdown("""
**Procesos automáticos:**
1. **Cruce:** Identifica SKUs nuevos.
2. **Limpieza:** Sustituye `;` por espacios (evita errores de importación).
3. **SEO:** Recorta a **128 caracteres** sin romper palabras.
""")

# --- BARRA LATERAL ---
st.sidebar.header("Configuración")
db_opcion = st.sidebar.selectbox("1. Base de datos destino:", ["Turaco", "Jabiru", "Marabu"])
pais_opcion = st.sidebar.selectbox("2. Selecciona el País:", ["ES", "FR", "IT", "DE", "PT", "UK"])

# --- CARGA DE FICHEROS ---
col1, col2 = st.columns(2)
with col1:
    st.subheader("Fichero Prestashop")
    archivo_presta = st.file_uploader("Excel Prestashop (col 'reference')", type=["xlsx"])
with col2:
    st.subheader("Fichero Amazon")
    archivo_amazon = st.file_uploader("Excel Amazon (A:SKU, B:ASIN, C:Título)", type=["xlsx"])

if archivo_presta and archivo_amazon:
    try:
        with st.spinner('Procesando...'):
            df_presta = pd.read_excel(archivo_presta)
            df_amazon = pd.read_excel(archivo_amazon)

            # Limpieza de nombres de columnas
            df_presta.columns = [str(c).strip() for c in df_presta.columns]
            df_amazon.columns = [str(c).strip() for c in df_amazon.columns]

            if 'reference' not in df_presta.columns:
                st.error("❌ No se encontró la columna 'reference' en Prestashop.")
            else:
                col_sku_amz = df_amazon.columns[0]
                col_asin_amz = df_amazon.columns[1]
                col_title_amz = df_amazon.columns[2]

                # 1. Filtrar referencias inexistentes
                refs_ps = set(df_presta['reference'].astype(str).str.strip())
                faltantes = df_amazon[~df_amazon[col_sku_amz].astype(str).str.strip().isin(refs_ps)].copy()

                # 2. Aplicar limpieza de ';' y recorte a 128 caracteres
                faltantes['Titulo_SEO'] = faltantes[col_title_amz].apply(lambda x: limpiar_y_recortar(x, 128))

                # 3. Preparar DataFrame de salida
                resultado = faltantes[[col_sku_amz, 'Titulo_SEO', col_asin_amz]].copy()
                resultado.columns = ['SKU', 'Título', 'ASIN']
                resultado['Activo'] = 1
                resultado['Marca'] = 'Cecotec'
                resultado['Proveedor'] = 'Cecotec'

                st.divider()
                st.success(f"Listo para descargar.")
                st.metric(f"Nuevas referencias {pais_opcion}", len(resultado))

                if not resultado.empty:
                    st.dataframe(resultado.head(15), use_container_width=True)
                    
                    # Nombre dinámico del archivo
                    nombre_fichero = f"altas_{db_opcion.lower()}_{pais_opcion}.xlsx"
                    
                    # Buffer para descarga
                    buffer = io.BytesIO()
                    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                        resultado.to_excel(writer, index=False, sheet_name='Altas_Limpias')
                    
                    st.download_button(
                        label=f"📥 Descargar Excel para {pais_opcion}",
                        data=buffer.getvalue(),
                        file_name=nombre_fichero,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                else:
                    st.info("No hay referencias nuevas para procesar.")

    except Exception as e:
        st.error(f"Error técnico: {e}")