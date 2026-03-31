import pandas as pd
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkinterdnd2 import DND_FILES, TkinterDnD
import os

class ComparadorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Comparador de Referencias Amazon -> Prestashop")
        self.root.geometry("600x450")
        
        self.file_presta = ""
        self.file_amazon = ""
        
        # --- Selección de Base de Datos ---
        ttk.Label(root, text="1. Selecciona el origen de datos:", font=('Arial', 10, 'bold')).pack(pady=10)
        self.db_var = tk.StringVar(value="Turaco")
        frame_radio = ttk.Frame(root)
        frame_radio.pack()
        for db in ["Turaco", "Jabiru", "Marabu"]:
            ttk.Radiobutton(frame_radio, text=db, variable=self.db_var, value=db).side = tk.LEFT
            ttk.Radiobutton(frame_radio, text=db, variable=self.db_var, value=db).pack(side=tk.LEFT, padx=10)

        # --- Zonas de Arrastre ---
        self.lbl_presta = ttk.Label(root, text="Arrastra aquí el Excel de PRESTASHOP", relief="groove", padding=20)
        self.lbl_presta.pack(fill="x", padx=20, pady=10)
        self.lbl_presta.drop_target_register(DND_FILES)
        self.lbl_presta.dnd_bind('<<Drop>>', self.drop_presta)

        self.lbl_amazon = ttk.Label(root, text="Arrastra aquí el Excel de AMAZON", relief="groove", padding=20)
        self.lbl_amazon.pack(fill="x", padx=20, pady=10)
        self.lbl_amazon.drop_target_register(DND_FILES)
        self.lbl_amazon.dnd_bind('<<Drop>>', self.drop_amazon)

        # --- Botón Procesar ---
        self.btn_run = ttk.Button(root, text="Generar Excel de Faltantes", command=self.procesar)
        self.btn_run.pack(pady=20)

    def drop_presta(self, event):
        self.file_presta = event.data.strip('{}')
        self.lbl_presta.config(text=f"Prestashop: {os.path.basename(self.file_presta)}")

    def drop_amazon(self, event):
        self.file_amazon = event.data.strip('{}')
        self.lbl_amazon.config(text=f"Amazon: {os.path.basename(self.file_amazon)}")

    def procesar(self):
        if not self.file_presta or not self.file_amazon:
            messagebox.showerror("Error", "Por favor, arrastra ambos archivos.")
            return

        try:
            # Leer archivos
            df_presta = pd.read_excel(self.file_presta)
            df_amazon = pd.read_excel(self.file_amazon)

            # Normalizar nombres de columnas (quitar espacios)
            df_presta.columns = [str(c).strip() for c in df_presta.columns]
            df_amazon.columns = [str(c).strip() for c in df_amazon.columns]

            # Identificar columnas de Amazon
            # Columna A (0): SKU, Columna B (1): ASIN, Columna C (2): Título
            col_sku_amz = df_amazon.columns[0]
            col_asin_amz = df_amazon.columns[1]
            col_title_amz = df_amazon.columns[2]

            # Filtrar: Amazon SKUs que NO están en la columna 'reference' de Prestashop
            # Usamos isin() y negamos con ~
            faltantes = df_amazon[~df_amazon[col_sku_amz].astype(str).isin(df_presta['reference'].astype(str))]

            # Seleccionar solo las columnas solicitadas
            resultado = faltantes[[col_sku_amz, col_title_amz, col_asin_amz]]
            resultado.columns = ['SKU', 'Título', 'ASIN']

            # Guardar
            save_path = filedialog.asksaveasfilename(defaultextension=".xlsx", 
                                                   title="Guardar listado de referencias a crear",
                                                   initialfile=f"Crear_en_{self.db_var.get()}.xlsx")
            if save_path:
                resultado.to_excel(save_path, index=False)
                messagebox.showinfo("Éxito", f"Se han encontrado {len(resultado)} referencias nuevas.")

        except Exception as e:
            messagebox.showerror("Error de proceso", f"Detalle: {str(e)}")

if __name__ == "__main__":
    root = TkinterDnD.Tk()
    app = ComparadorApp(root)
    root.mainloop()