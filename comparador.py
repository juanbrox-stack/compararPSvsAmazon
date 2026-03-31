import streamlit as st
import pandas as pd
import io

# Configuración de la página
st.set_page_config(page_title="Comparador Amazon vs Prestashop", layout="centered")

st.title("📦 Comparador de Referencias")
st.write("Identifica productos de Amazon que faltan en Prestashop con datos de importación.")

# --- 1. SELECCIÓN DE BASE DE DATOS ---
db_opcion = st.selectbox(
    "Selecciona la base de datos de Prestashop a procesar:",
    ["Turaco", "Jabiru", "Marabu"]
)

st.divider()

# --- 2. CARGA DE ARCHIVOS ---
col1, col2 = st.columns(2)

with col1:
    archivo_presta = st.file_uploader("Fichero PRESTASHOP (.xlsx)", type=["xlsx"])
with col2:
    archivo_amazon = st.file_uploader("Fichero AMAZON (.xlsx)", type=["xlsx"])

# --- 3. LÓGICA DE PROCESAMIENTO ---
if archivo_presta and archivo_amazon:
    try:
        df_presta = pd.read_excel(archivo_presta)
        df_amazon = pd.read_excel(archivo_amazon)

        # Limpiar nombres de columnas
        df_presta.columns = [str(c).strip() for c in df_presta.columns]
        df_amazon.columns = [str(c).strip() for c in df_amazon.columns]

        if 'reference' not in df_presta.columns:
            st.error("Error: No se encuentra la columna 'reference' en el archivo de Prestashop.")
        else:
            # Identificar columnas de Amazon por posición
            col_sku_amz = df_amazon.columns[0]
            col_asin_amz = df_amazon.columns[1]
            col_title_amz = df_amazon.columns[2]

            # Filtrar lo que está en Amazon pero NO en Prestashop
            referencias_presta = set(df_presta['reference'].astype(str))
            faltantes = df_amazon[~df_amazon[col_sku_amz].astype(str).isin(referencias_presta)].copy()

            # --- NUEVA LÓGICA: Añadir columnas fijas ---
            # Creamos el dataframe final con las columnas base
            resultado = faltantes[[col_sku_amz, col_title_amz, col_asin_amz]].copy()
            resultado.columns = ['SKU', 'Título', 'ASIN']

            # Añadimos los valores fijos que solicitaste
            resultado['Activo'] = 1
            resultado['Marca'] = 'Cecotec'
            resultado['Proveedor'] = 'Cecotec'

            st.divider()
            st.success(f"¡Cruce completado para {db_opcion}!")
            st.metric("Nuevas referencias para crear", len(resultado))

            if len(resultado) > 0:
                # Mostrar vista previa (las primeras 10 filas)
                st.dataframe(resultado.head(10), use_container_width=True)

                # --- 4. DESCARGA DEL RESULTADO ---
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    resultado.to_excel(writer, index=False, sheet_name='Importar_a_PS')
                
                st.download_button(
                    label="📥 Descargar Excel para Prestashop",
                    data=output.getvalue(),
                    file_name=f"nuevos_productos_{db_opcion.lower()}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.info("No hay referencias nuevas que añadir.")

    except Exception as e:
        st.error(f"Error técnico: {e}")
else:
    st.info("Sube los archivos para generar el listado de altas.")