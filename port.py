import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import fitz  # PyMuPDF
import os

class EditorPDF:
    def __init__(self, root):
        self.root = root
        self.root.title("Editor Avanzado de PDF")
        self.root.geometry("500x600")
        self.root.resizable(True, True)
        
        # Variables
        self.pdf_doc = None
        self.total_paginas = 0
        
        self.crear_interfaz()
        
    def crear_interfaz(self):
        # Frame principal con scroll
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configurar grid
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Sección de archivo
        ttk.Label(main_frame, text="📁 Selección de archivo PDF", font=("Arial", 12, "bold")).grid(row=0, column=0, columnspan=3, pady=(0,10), sticky=tk.W)
        
        ttk.Label(main_frame, text="Archivo PDF:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.entrada_ruta_pdf = ttk.Entry(main_frame, width=40)
        self.entrada_ruta_pdf.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(5,5), pady=2)
        
        ttk.Button(main_frame, text="Buscar", command=self.seleccionar_pdf).grid(row=1, column=2, padx=(0,0), pady=2)
        
        # Información del PDF
        self.label_info = ttk.Label(main_frame, text="", foreground="blue")
        self.label_info.grid(row=2, column=0, columnspan=3, sticky=tk.W, pady=5)
        
        # Separador
        ttk.Separator(main_frame, orient='horizontal').grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=15)
        
        # Sección de edición
        ttk.Label(main_frame, text="✏️ Configuración de texto", font=("Arial", 12, "bold")).grid(row=4, column=0, columnspan=3, pady=(0,10), sticky=tk.W)
        
        # Texto a insertar
        ttk.Label(main_frame, text="Texto a insertar:").grid(row=5, column=0, sticky=tk.W, pady=2)
        self.entrada_texto = ttk.Entry(main_frame, width=40)
        self.entrada_texto.grid(row=5, column=1, columnspan=2, sticky=(tk.W, tk.E), padx=(5,0), pady=2)
        
        # Frame para opciones en la misma fila
        opciones_frame = ttk.Frame(main_frame)
        opciones_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        opciones_frame.columnconfigure(1, weight=1)
        opciones_frame.columnconfigure(3, weight=1)
        opciones_frame.columnconfigure(5, weight=1)
        
        # Página
        ttk.Label(opciones_frame, text="Página:").grid(row=0, column=0, sticky=tk.W, padx=(0,5))
        self.entrada_pagina = ttk.Spinbox(opciones_frame, from_=1, to=1, width=8, value=1)
        self.entrada_pagina.grid(row=0, column=1, sticky=tk.W, padx=(0,15))
        
        # Posición X
        ttk.Label(opciones_frame, text="Pos. X:").grid(row=0, column=2, sticky=tk.W, padx=(0,5))
        self.entrada_x = ttk.Spinbox(opciones_frame, from_=0, to=1000, width=8, value=100)
        self.entrada_x.grid(row=0, column=3, sticky=tk.W, padx=(0,15))
        
        # Posición Y
        ttk.Label(opciones_frame, text="Pos. Y:").grid(row=0, column=4, sticky=tk.W, padx=(0,5))
        self.entrada_y = ttk.Spinbox(opciones_frame, from_=0, to=1000, width=8, value=100)
        self.entrada_y.grid(row=0, column=5, sticky=tk.W)
        
        # Frame para configuración de fuente
        fuente_frame = ttk.Frame(main_frame)
        fuente_frame.grid(row=7, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        fuente_frame.columnconfigure(1, weight=1)
        fuente_frame.columnconfigure(3, weight=1)
        
        # Tamaño de fuente
        ttk.Label(fuente_frame, text="Tamaño:").grid(row=0, column=0, sticky=tk.W, padx=(0,5))
        self.entrada_tamano = ttk.Spinbox(fuente_frame, from_=6, to=72, width=8, value=12)
        self.entrada_tamano.grid(row=0, column=1, sticky=tk.W, padx=(0,15))
        
        # Color
        ttk.Label(fuente_frame, text="Color:").grid(row=0, column=2, sticky=tk.W, padx=(0,5))
        self.color_var = tk.StringVar(value="Negro")
        self.combo_color = ttk.Combobox(fuente_frame, textvariable=self.color_var, 
                                       values=["Negro", "Rojo", "Azul", "Verde", "Naranja"], 
                                       state="readonly", width=10)
        self.combo_color.grid(row=0, column=3, sticky=tk.W)
        
        # Separador
        ttk.Separator(main_frame, orient='horizontal').grid(row=8, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=15)
        
        # Botones de acción
        botones_frame = ttk.Frame(main_frame)
        botones_frame.grid(row=9, column=0, columnspan=3, pady=10)
        
        ttk.Button(botones_frame, text="👁️ Vista previa", command=self.vista_previa).pack(side=tk.LEFT, padx=(0,10))
        ttk.Button(botones_frame, text="💾 Editar y Guardar PDF", command=self.editar_pdf).pack(side=tk.LEFT)
        
        # Área de vista previa/información
        ttk.Label(main_frame, text="📋 Información:", font=("Arial", 10, "bold")).grid(row=10, column=0, columnspan=3, sticky=tk.W, pady=(20,5))
        
        self.texto_info = tk.Text(main_frame, height=8, width=60, wrap=tk.WORD)
        self.texto_info.grid(row=11, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        # Scrollbar para el texto
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=self.texto_info.yview)
        scrollbar.grid(row=11, column=3, sticky=(tk.N, tk.S))
        self.texto_info.configure(yscrollcommand=scrollbar.set)
        
        # Mensaje inicial
        self.texto_info.insert(tk.END, "👋 Bienvenido al Editor de PDF\n")
        self.texto_info.insert(tk.END, "1. Selecciona un archivo PDF\n")
        self.texto_info.insert(tk.END, "2. Configura el texto y posición\n")
        self.texto_info.insert(tk.END, "3. Usa Vista previa para verificar\n")
        self.texto_info.insert(tk.END, "4. Guarda el PDF modificado\n\n")
        self.texto_info.insert(tk.END, "💡 Tip: Las coordenadas (0,0) están en la esquina inferior izquierda de la página.")
        
    def seleccionar_pdf(self):
        ruta = filedialog.askopenfilename(
            title="Seleccionar archivo PDF",
            filetypes=[("Archivos PDF", "*.pdf"), ("Todos los archivos", "*.*")]
        )
        if ruta:
            self.entrada_ruta_pdf.delete(0, tk.END)
            self.entrada_ruta_pdf.insert(0, ruta)
            self.cargar_info_pdf(ruta)
            
    def cargar_info_pdf(self, ruta):
        try:
            if self.pdf_doc:
                self.pdf_doc.close()
                
            self.pdf_doc = fitz.open(ruta)
            self.total_paginas = len(self.pdf_doc)
            
            # Actualizar información
            nombre_archivo = os.path.basename(ruta)
            self.label_info.config(text=f"📄 {nombre_archivo} - {self.total_paginas} página(s)")
            
            # Actualizar spinbox de páginas
            self.entrada_pagina.configure(to=self.total_paginas)
            
            # Actualizar área de información
            self.texto_info.delete(1.0, tk.END)
            self.texto_info.insert(tk.END, f"✅ PDF cargado exitosamente\n")
            self.texto_info.insert(tk.END, f"📂 Archivo: {nombre_archivo}\n")
            self.texto_info.insert(tk.END, f"📄 Páginas: {self.total_paginas}\n")
            
            # Obtener información de la primera página
            pagina = self.pdf_doc[0]
            rect = pagina.rect
            self.texto_info.insert(tk.END, f"📐 Dimensiones página 1: {rect.width:.0f} x {rect.height:.0f} puntos\n\n")
            self.texto_info.insert(tk.END, "🎯 Listo para editar. Configura el texto y posición.")
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar el PDF:\n{str(e)}")
            self.label_info.config(text="")
            
    def obtener_color(self):
        colores = {
            "Negro": (0, 0, 0),
            "Rojo": (1, 0, 0),
            "Azul": (0, 0, 1),
            "Verde": (0, 0.5, 0),
            "Naranja": (1, 0.5, 0)
        }
        return colores.get(self.color_var.get(), (0, 0, 0))
        
    def vista_previa(self):
        if not self.validar_entrada():
            return
            
        texto = self.entrada_texto.get()
        pagina_num = int(self.entrada_pagina.get())
        x = int(self.entrada_x.get())
        y = int(self.entrada_y.get())
        tamano = int(self.entrada_tamano.get())
        color = self.color_var.get()
        
        self.texto_info.delete(1.0, tk.END)
        self.texto_info.insert(tk.END, "👁️ VISTA PREVIA\n")
        self.texto_info.insert(tk.END, "=" * 40 + "\n")
        self.texto_info.insert(tk.END, f"📝 Texto: '{texto}'\n")
        self.texto_info.insert(tk.END, f"📄 Página: {pagina_num}\n")
        self.texto_info.insert(tk.END, f"📍 Posición: X={x}, Y={y}\n")
        self.texto_info.insert(tk.END, f"🔤 Tamaño: {tamano}pt\n")
        self.texto_info.insert(tk.END, f"🎨 Color: {color}\n\n")
        self.texto_info.insert(tk.END, "✅ Configuración válida. Listo para guardar.")
        
    def validar_entrada(self):
        if not self.entrada_ruta_pdf.get():
            messagebox.showerror("Error", "Por favor selecciona un archivo PDF.")
            return False
            
        if not self.entrada_texto.get().strip():
            messagebox.showerror("Error", "Por favor ingresa el texto a insertar.")
            return False
            
        if not self.pdf_doc:
            messagebox.showerror("Error", "PDF no cargado correctamente.")
            return False
            
        try:
            pagina_num = int(self.entrada_pagina.get())
            if pagina_num < 1 or pagina_num > self.total_paginas:
                messagebox.showerror("Error", f"Número de página debe estar entre 1 y {self.total_paginas}.")
                return False
        except ValueError:
            messagebox.showerror("Error", "Número de página inválido.")
            return False
            
        try:
            int(self.entrada_x.get())
            int(self.entrada_y.get())
            int(self.entrada_tamano.get())
        except ValueError:
            messagebox.showerror("Error", "Las coordenadas y tamaño deben ser números enteros.")
            return False
            
        return True
        
    def editar_pdf(self):
        if not self.validar_entrada():
            return
            
        try:
            texto = self.entrada_texto.get()
            pagina_index = int(self.entrada_pagina.get()) - 1
            x = int(self.entrada_x.get())
            y = int(self.entrada_y.get())
            tamano = int(self.entrada_tamano.get())
            color = self.obtener_color()
            
            # Crear una copia del documento
            doc_copia = fitz.open(self.entrada_ruta_pdf.get())
            pagina = doc_copia[pagina_index]
            
            # Insertar texto
            pagina.insert_text((x, y), texto, fontsize=tamano, color=color)
            
            # Guardar archivo
            nueva_ruta = filedialog.asksaveasfilename(
                title="Guardar PDF editado",
                defaultextension=".pdf",
                filetypes=[("PDF", "*.pdf")],
                initialname="pdf_editado.pdf"
            )
            
            if nueva_ruta:
                doc_copia.save(nueva_ruta)
                doc_copia.close()
                
                # Actualizar información
                self.texto_info.delete(1.0, tk.END)
                self.texto_info.insert(tk.END, "🎉 ¡PDF GUARDADO EXITOSAMENTE!\n")
                self.texto_info.insert(tk.END, "=" * 40 + "\n")
                self.texto_info.insert(tk.END, f"💾 Guardado en: {nueva_ruta}\n")
                self.texto_info.insert(tk.END, f"📝 Texto agregado: '{texto}'\n")
                self.texto_info.insert(tk.END, f"📄 En página: {int(self.entrada_pagina.get())}\n\n")
                self.texto_info.insert(tk.END, "✅ Operación completada con éxito.")
                
                messagebox.showinfo("Éxito", f"PDF guardado exitosamente en:\n{nueva_ruta}")
            else:
                doc_copia.close()
                
        except Exception as e:
            messagebox.showerror("Error", f"Error al editar el PDF:\n{str(e)}")
            
    def __del__(self):
        if hasattr(self, 'pdf_doc') and self.pdf_doc:
            self.pdf_doc.close()

if __name__ == "__main__":
    root = tk.Tk()
    app = EditorPDF(root)
    root.mainloop()