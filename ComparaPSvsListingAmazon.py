import streamlit as st
import pandas as pd
import re
from io import BytesIO

st.set_page_config(page_title="Comparador SKU: Limpieza y Formato", layout="wide")

def formatear_y_limpiar_skus(df, columna):
    """
    Aplica limpieza, filtrado y normalización de ceros a la izquierda.
    """
    # 1. Limpieza básica inicial
    df[columna] = df[columna].astype(str).str.strip()
    
    # 2. Filtros de exclusión (F, amzn., termina en punto)
    mask_excluir = (
        df[columna].str.startswith('F', na=False) | 
        df[columna].str.startswith('amzn.', na=False) | 
        df[columna].str.endswith('.', na=False)
    )
    df_temp = df[~mask_excluir].copy()

    # 3. Lógica de normalización (Ceros a la izquierda)
    # Si el SKU es puramente numérico y tiene entre 1 y 5 dígitos, le ponemos ceros
    def normalizar(valor):
        if valor.isdigit() and len(valor) <= 5:
            return valor.zfill(5)
        return valor

    df_temp[columna] = df_temp[columna].apply(normalizar)

    # 4. Filtro de validez final (Regex)
    # ^A.* -> Empieza por A
    # ^\d{5}$ -> Es un número de exactamente 5 dígitos (ya normalizados)
    patron_valido = r'^(A.*|\d{5})$'
    mask_valido = df_temp[columna].str.contains(patron_valido, regex=True, na=False)
    
    return df_temp[mask_valido]

def main():
    st.title("🔍 Comparador SKU con Normalización")
    st.write("Esta versión corrige los SKUs numéricos para que siempre tengan 5 dígitos (ej: 123 -> 00123).")
    
    st.sidebar.header("Carga de Datos")
    file_ps = st.sidebar.file_uploader("Prestashop (.xlsx)", type=['xlsx'])
    file_amz = st.sidebar.file_uploader("Amazon (.xlsx)", type=['xlsx'])
    
    col_ps = st.sidebar.text_input("Columna SKU Prestashop", value="Reference")
    col_amz = st.sidebar.text_input("Columna SKU Amazon", value="seller-sku")

    if file_ps and file_amz:
        try:
            df_ps = pd.read_excel(file_ps)
            df_amz = pd.read_excel(file_amz)

            # Aplicar limpieza y normalización a ambos (para que coincidan al comparar)
            df_ps_limpio = formatear_y_limpiar_skus(df_ps, col_ps)
            df_amz_limpio = formatear_y_limpiar_skus(df_amz, col_amz)
            
            # Comparación
            skus_ps = set(df_ps_limpio[col_ps].unique())
            mask_faltantes = ~df_amz_limpio[col_amz].isin(skus_ps)
            df_faltantes = df_amz_limpio[mask_faltantes].copy()

            # Visualización
            st.divider()
            c1, c2, c3 = st.columns(3)
            c1.metric("Amazon Limpios", len(df_amz_limpio))
            c2.metric("Prestashop Limpios", len(df_ps_limpio))
            c3.metric("Faltantes Reales", len(df_faltantes))

            if not df_faltantes.empty:
                st.subheader("📋 Resultados listos para descargar")
                st.dataframe(df_faltantes, use_container_width=True)

                output = BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df_faltantes.to_excel(writer, index=False)
                
                st.download_button(
                    label="📥 Descargar Excel con SKUs de 5 dígitos",
                    data=output.getvalue(),
                    file_name="skus_finales_corregidos.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.success("✅ Todo está al día.")

        except Exception as e:
            st.error(f"Error técnico: {e}")

if __name__ == "__main__":
    main()