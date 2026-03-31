import streamlit as st
import pandas as pd
import io

# Configuración de la página
st.set_page_config(page_title="Comparador Amazon vs Prestashop", layout="centered")

st.title("📦 Comparador de Referencias")
st.write("Identifica productos de Amazon que aún no están en Prestashop.")

# --- 1. SELECCIÓN DE BASE DE DATOS ---
db_opcion = st.selectbox(
    "Selecciona la base de datos de Prestashop a procesar:",
    ["Turaco", "Jabiru", "Marabu"]
)

st.divider()

# --- 2. CARGA DE ARCHIVOS (Drag & Drop nativo) ---
col1, col2 = st.columns(2)

with col1:
    archivo_presta = st.file_uploader("Fichero PRESTASHOP (.xlsx)", type=["xlsx"])
with col2:
    archivo_amazon = st.file_uploader("Fichero AMAZON (.xlsx)", type=["xlsx"])

# --- 3. LÓGICA DE PROCESAMIENTO ---
if archivo_presta and archivo_amazon:
    try:
        # Leer los excels
        df_presta = pd.read_excel(archivo_presta)
        df_amazon = pd.read_excel(archivo_amazon)

        # Limpiar nombres de columnas
        df_presta.columns = [str(c).strip() for c in df_presta.columns]
        df_amazon.columns = [str(c).strip() for c in df_amazon.columns]

        # Validar columna 'reference' en Prestashop
        if 'reference' not in df_presta.columns:
            st.error("El archivo de Prestashop debe tener una columna llamada 'reference'")
        else:
            # Identificar columnas de Amazon por posición (A, B, C)
            col_sku_amz = df_amazon.columns[0]
            col_asin_amz = df_amazon.columns[1]
            col_title_amz = df_amazon.columns[2]

            # LÓGICA: Buscar SKUs de Amazon que NO están en 'reference' de Prestashop
            referencias_presta = set(df_presta['reference'].astype(str))
            
            # Filtramos
            faltantes = df_amazon[~df_amazon[col_sku_amz].astype(str).isin(referencias_presta)]

            # Formatear resultado final
            resultado = faltantes[[col_sku_amz, col_title_amz, col_asin_amz]].copy()
            resultado.columns = ['SKU', 'Título', 'ASIN']

            st.divider()
            st.success(f"¡Cruce completado para {db_opcion}!")
            st.metric("Referencias faltantes encontradas", len(resultado))

            if len(resultado) > 0:
                # Mostrar vista previa
                st.dataframe(resultado.head(10), use_container_width=True)

                # --- 4. DESCARGA DEL RESULTADO ---
                # Convertir DF a Excel en memoria
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    resultado.to_excel(writer, index=False, sheet_name='Faltantes')
                
                st.download_button(
                    label="📥 Descargar Excel de Faltantes",
                    data=output.getvalue(),
                    file_name=f"crear_en_prestashop_{db_opcion.lower()}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.info("Todas las referencias de Amazon ya existen en Prestashop.")

    except Exception as e:
        st.error(f"Error al procesar los archivos: {e}")
else:
    st.info("Por favor, sube ambos archivos Excel para comenzar el análisis.")