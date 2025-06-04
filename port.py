import tkinter as tk
from tkinter import filedialog, messagebox, ttk, font
import fitz  # PyMuPDF
import os
from PIL import Image, ImageTk
import io

class EditorPDFAvanzado:
    def __init__(self, root):
        self.root = root
        self.root.title("📄 Editor PDF Profesional - Estilo Adobe")
        self.root.geometry("1200x800")
        self.root.resizable(True, True)
        self.root.configure(bg="#2c2c2c")
          # Variables principales
        self.pdf_doc = None
        self.pagina_actual = 0
        self.total_paginas = 0
        self.zoom_level = 1.0
        self.archivo_cargado = False
        self.modo_edicion = "texto"  # texto, resaltado, firma
        self.elementos_agregados = []  # Lista de elementos añadidos
        
        # Variables de herramientas
        self.color_actual = (0, 0, 0)  # Negro por defecto
        self.tamano_fuente = 12
        self.fuente_actual = "helvetica"
        self.grosor_linea = 2
        
        self.crear_interfaz()
        self.configurar_shortcuts()
        
    def crear_interfaz(self):
        # Barra de menú
        self.crear_menu()
        
        # Barra de herramientas principal
        self.crear_toolbar()
        
        # Frame principal con paneles
        main_frame = tk.Frame(self.root, bg="#2c2c2c")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Panel izquierdo - Navegación y propiedades
        self.crear_panel_izquierdo(main_frame)
        
        # Panel central - Visor de PDF
        self.crear_panel_central(main_frame)
        
        # Panel derecho - Herramientas de edición
        self.crear_panel_derecho(main_frame)
        
        # Barra de estado
        self.crear_barra_estado()
        
    def crear_menu(self):
        menubar = tk.Menu(self.root, bg="#404040", fg="white", font=("Arial", 10))
        self.root.config(menu=menubar)
        
        # Menú Archivo
        archivo_menu = tk.Menu(menubar, tearoff=0, bg="#404040", fg="white")
        menubar.add_cascade(label="📁 Archivo", menu=archivo_menu)
        archivo_menu.add_command(label="🔍 Abrir PDF...", command=self.abrir_pdf, accelerator="Ctrl+O")
        archivo_menu.add_separator()
        archivo_menu.add_command(label="💾 Guardar", command=self.guardar_pdf, accelerator="Ctrl+S")
        archivo_menu.add_command(label="💾 Guardar como...", command=self.guardar_como_pdf, accelerator="Ctrl+Shift+S")
        archivo_menu.add_separator()
        archivo_menu.add_command(label="🚪 Salir", command=self.root.quit)
        
        # Menú Edición
        edicion_menu = tk.Menu(menubar, tearoff=0, bg="#404040", fg="white")
        menubar.add_cascade(label="✏️ Edición", menu=edicion_menu)
        edicion_menu.add_command(label="↶ Deshacer", command=self.deshacer, accelerator="Ctrl+Z")
        edicion_menu.add_command(label="↷ Rehacer", command=self.rehacer, accelerator="Ctrl+Y")
        edicion_menu.add_separator()
        edicion_menu.add_command(label="🗑️ Eliminar selección", command=self.eliminar_seleccion, accelerator="Del")
        
        # Menú Vista
        vista_menu = tk.Menu(menubar, tearoff=0, bg="#404040", fg="white")
        menubar.add_cascade(label="👁️ Vista", menu=vista_menu)
        vista_menu.add_command(label="🔍 Zoom +", command=self.zoom_mas, accelerator="Ctrl++")
        vista_menu.add_command(label="🔍 Zoom -", command=self.zoom_menos, accelerator="Ctrl+-")
        vista_menu.add_command(label="🔍 Ajustar a ventana", command=self.ajustar_ventana, accelerator="Ctrl+0")
        
    def crear_toolbar(self):
        toolbar_frame = tk.Frame(self.root, bg="#3c3c3c", height=60)
        toolbar_frame.pack(fill=tk.X, padx=5, pady=(5,0))
        toolbar_frame.pack_propagate(False)
        
        # Grupo 1: Archivo
        grupo1 = tk.Frame(toolbar_frame, bg="#3c3c3c")
        grupo1.pack(side=tk.LEFT, padx=10, pady=5)
        
        self.btn_abrir = tk.Button(grupo1, text="📁\nAbrir", font=("Arial", 9, "bold"),
                                  bg="#4a9eff", fg="white", width=8, height=2,
                                  command=self.abrir_pdf, relief=tk.FLAT)
        self.btn_abrir.pack(side=tk.LEFT, padx=2)
        
        self.btn_guardar = tk.Button(grupo1, text="💾\nGuardar", font=("Arial", 9, "bold"),
                                    bg="#28a745", fg="white", width=8, height=2,
                                    command=self.guardar_pdf, relief=tk.FLAT)
        self.btn_guardar.pack(side=tk.LEFT, padx=2)
        
        # Separador
        tk.Frame(toolbar_frame, bg="#555", width=2, height=40).pack(side=tk.LEFT, padx=10, pady=10, fill=tk.Y)
        
        # Grupo 2: Herramientas de edición
        grupo2 = tk.Frame(toolbar_frame, bg="#3c3c3c")
        grupo2.pack(side=tk.LEFT, padx=10, pady=5)
        
        self.btn_texto = tk.Button(grupo2, text="📝\nTexto", font=("Arial", 9, "bold"),
                                  bg="#ff6b35", fg="white", width=8, height=2,
                                  command=lambda: self.cambiar_modo("texto"), relief=tk.FLAT)
        self.btn_texto.pack(side=tk.LEFT, padx=2)
        
        self.btn_resaltar = tk.Button(grupo2, text="🖍️\nResaltar", font=("Arial", 9, "bold"),
                                     bg="#ffd700", fg="black", width=8, height=2,
                                     command=lambda: self.cambiar_modo("resaltar"), relief=tk.FLAT)
        self.btn_resaltar.pack(side=tk.LEFT, padx=2)
        
        self.btn_firma = tk.Button(grupo2, text="✍️\nFirma", font=("Arial", 9, "bold"),
                                  bg="#9b59b6", fg="white", width=8, height=2,
                                  command=lambda: self.cambiar_modo("firma"), relief=tk.FLAT)
        self.btn_firma.pack(side=tk.LEFT, padx=2)
        
        # Separador
        tk.Frame(toolbar_frame, bg="#555", width=2, height=40).pack(side=tk.LEFT, padx=10, pady=10, fill=tk.Y)
        
        # Grupo 3: Navegación
        grupo3 = tk.Frame(toolbar_frame, bg="#3c3c3c")
        grupo3.pack(side=tk.LEFT, padx=10, pady=5)
        
        self.btn_anterior = tk.Button(grupo3, text="⬅️", font=("Arial", 12, "bold"),
                                     bg="#6c757d", fg="white", width=3, height=2,
                                     command=self.pagina_anterior, relief=tk.FLAT)
        self.btn_anterior.pack(side=tk.LEFT, padx=2)
        
        self.label_pagina = tk.Label(grupo3, text="0 / 0", font=("Arial", 12, "bold"),
                                    bg="#3c3c3c", fg="white", width=8)
        self.label_pagina.pack(side=tk.LEFT, padx=5)
        
        self.btn_siguiente = tk.Button(grupo3, text="➡️", font=("Arial", 12, "bold"),
                                      bg="#6c757d", fg="white", width=3, height=2,
                                      command=self.pagina_siguiente, relief=tk.FLAT)
        self.btn_siguiente.pack(side=tk.LEFT, padx=2)
        
    def crear_panel_izquierdo(self, parent):
        # Panel de navegación y miniaturas
        self.panel_izq = tk.Frame(parent, bg="#383838", width=200)
        self.panel_izq.pack(side=tk.LEFT, fill=tk.Y, padx=(0,5))
        self.panel_izq.pack_propagate(False)
        
        # Título del panel
        tk.Label(self.panel_izq, text="📑 Páginas", font=("Arial", 12, "bold"),
                bg="#383838", fg="white").pack(pady=10)
        
        # Lista de páginas con scroll
        self.frame_paginas = tk.Frame(self.panel_izq, bg="#383838")
        self.frame_paginas.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Canvas para scroll de miniaturas
        self.canvas_paginas = tk.Canvas(self.frame_paginas, bg="#484848", highlightthickness=0)
        self.scrollbar_paginas = ttk.Scrollbar(self.frame_paginas, orient="vertical", command=self.canvas_paginas.yview)
        self.scrollable_frame = tk.Frame(self.canvas_paginas, bg="#484848")
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas_paginas.configure(scrollregion=self.canvas_paginas.bbox("all"))
        )
        
        self.canvas_paginas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas_paginas.configure(yscrollcommand=self.scrollbar_paginas.set)
        
        self.canvas_paginas.pack(side="left", fill="both", expand=True)
        self.scrollbar_paginas.pack(side="right", fill="y")
        
    def crear_panel_central(self, parent):
        # Panel principal del visor
        self.panel_central = tk.Frame(parent, bg="#2c2c2c")
        self.panel_central.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        # Frame para el PDF con scroll
        self.frame_visor = tk.Frame(self.panel_central, bg="#404040", relief=tk.SUNKEN, bd=2)
        self.frame_visor.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Canvas principal para mostrar PDF
        self.canvas_pdf = tk.Canvas(self.frame_visor, bg="#555555", highlightthickness=0)
        
        # Scrollbars para el canvas
        self.scroll_v = ttk.Scrollbar(self.frame_visor, orient="vertical", command=self.canvas_pdf.yview)
        self.scroll_h = ttk.Scrollbar(self.frame_visor, orient="horizontal", command=self.canvas_pdf.xview)
        
        self.canvas_pdf.configure(yscrollcommand=self.scroll_v.set, xscrollcommand=self.scroll_h.set)
        
        # Empaquetar canvas y scrollbars
        self.canvas_pdf.pack(side="left", fill="both", expand=True)
        self.scroll_v.pack(side="right", fill="y")
        self.scroll_h.pack(side="bottom", fill="x")
        
        # Eventos del canvas
        self.canvas_pdf.bind("<Button-1>", self.on_canvas_click)
        self.canvas_pdf.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas_pdf.bind("<ButtonRelease-1>", self.on_canvas_release)
        self.canvas_pdf.bind("<MouseWheel>", self.on_mousewheel)
        
        # Variables para el modo de edición
        self.click_x = 0
        self.click_y = 0
        self.elemento_temporal = None
        
    def crear_panel_derecho(self, parent):
        # Panel de herramientas
        self.panel_der = tk.Frame(parent, bg="#383838", width=250)
        self.panel_der.pack(side=tk.RIGHT, fill=tk.Y, padx=(5,0))
        self.panel_der.pack_propagate(False)
        
        # Título del panel
        tk.Label(self.panel_der, text="🛠️ Herramientas", font=("Arial", 12, "bold"),
                bg="#383838", fg="white").pack(pady=10)
        
        # Notebook para organizar herramientas
        self.notebook = ttk.Notebook(self.panel_der)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Pestaña de Texto
        self.crear_pestana_texto()
        
        # Pestaña de Colores
        self.crear_pestana_colores()
        
        # Pestaña de Elementos
        self.crear_pestana_elementos()
        
    def crear_pestana_texto(self):
        self.frame_texto = tk.Frame(self.notebook, bg="#484848")
        self.notebook.add(self.frame_texto, text="📝 Texto")
        
        # Entrada de texto
        tk.Label(self.frame_texto, text="Escribe tu texto:", font=("Arial", 10, "bold"),
                bg="#484848", fg="white").pack(anchor=tk.W, padx=10, pady=(10, 5))
        
        self.entry_texto = tk.Text(self.frame_texto, height=4, width=25, font=("Arial", 11),
                                  relief=tk.SOLID, bd=1, wrap=tk.WORD)
        self.entry_texto.pack(padx=10, pady=5, fill=tk.X)
        
        # Tamaño de fuente
        tk.Label(self.frame_texto, text="Tamaño:", font=("Arial", 10, "bold"),
                bg="#484848", fg="white").pack(anchor=tk.W, padx=10, pady=(15, 5))
        
        self.scale_tamano = tk.Scale(self.frame_texto, from_=8, to=72, orient=tk.HORIZONTAL,
                                    bg="#484848", fg="white", highlightthickness=0,
                                    variable=tk.IntVar(value=12), length=200)
        self.scale_tamano.pack(padx=10, pady=5)
        self.scale_tamano.bind("<Motion>", self.actualizar_tamano)
        
        # Fuente
        tk.Label(self.frame_texto, text="Fuente:", font=("Arial", 10, "bold"),
                bg="#484848", fg="white").pack(anchor=tk.W, padx=10, pady=(15, 5))
        
        fuentes = ["helvetica", "times", "courier", "arial", "calibri"]
        self.combo_fuente = ttk.Combobox(self.frame_texto, values=fuentes, state="readonly")
        self.combo_fuente.set("helvetica")
        self.combo_fuente.pack(padx=10, pady=5, fill=tk.X)
          # Botón para agregar texto
        self.btn_agregar_texto = tk.Button(self.frame_texto, text="✅ Agregar Texto",
                                          font=("Arial", 11, "bold"), bg="#28a745", fg="white",
                                          command=self.modo_agregar_texto, relief=tk.FLAT)
        self.btn_agregar_texto.pack(padx=10, pady=15, fill=tk.X)
        
    def crear_pestana_colores(self):
        self.frame_colores = tk.Frame(self.notebook, bg="#484848")
        self.notebook.add(self.frame_colores, text="🎨 Colores")
        
        # Título
        titulo = tk.Label(self.frame_colores, text="Selecciona un color:", font=("Arial", 10, "bold"),
                bg="#484848", fg="white")
        titulo.grid(row=0, column=0, columnspan=3, pady=10)
        
        # Paleta de colores predefinidos
        colores = [
            ("Negro", "#000000"), ("Rojo", "#ff0000"), ("Azul", "#0000ff"),
            ("Verde", "#00ff00"), ("Amarillo", "#ffff00"), ("Naranja", "#ff8000"),
            ("Rosa", "#ff00ff"), ("Cyan", "#00ffff"), ("Marrón", "#8b4513"),
            ("Gris", "#808080"), ("Púrpura", "#800080"), ("Verde oscuro", "#006400")
        ]
        
        # Grid de botones de color
        for i, (nombre, hex_color) in enumerate(colores):
            fila = (i // 3) + 1  # +1 porque el título está en la fila 0
            col = i % 3
            
            btn_color = tk.Button(self.frame_colores, bg=hex_color, width=8, height=2,
                                 relief=tk.RAISED, bd=2,
                                 command=lambda c=hex_color: self.seleccionar_color(c))
            btn_color.grid(row=fila, column=col, padx=5, pady=3, sticky="ew")
            
        # Configurar grid
        for i in range(3):
            self.frame_colores.grid_columnconfigure(i, weight=1)
            
        # Color actual
        self.frame_color_actual = tk.Frame(self.frame_colores, bg="#484848")
        self.frame_color_actual.grid(row=6, column=0, columnspan=3, pady=20, padx=10, sticky="ew")
        
        color_actual_label = tk.Label(self.frame_color_actual, text="Color actual:", 
                                    font=("Arial", 10, "bold"), bg="#484848", fg="white")
        color_actual_label.grid(row=0, column=0, pady=5)
        
        self.muestra_color = tk.Label(self.frame_color_actual, bg="#000000", width=20, height=2,
                                     relief=tk.SUNKEN, bd=2)
        self.muestra_color.grid(row=1, column=0, pady=5)
        
    def crear_pestana_elementos(self):
        self.frame_elementos = tk.Frame(self.notebook, bg="#484848")
        self.notebook.add(self.frame_elementos, text="📋 Elementos")
        
        tk.Label(self.frame_elementos, text="Elementos agregados:", font=("Arial", 10, "bold"),
                bg="#484848", fg="white").pack(pady=10)
        
        # Lista de elementos
        self.lista_elementos = tk.Listbox(self.frame_elementos, height=10, bg="white",
                                         font=("Arial", 9), selectmode=tk.SINGLE)
        self.lista_elementos.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)
        
        # Botones de control
        frame_botones = tk.Frame(self.frame_elementos, bg="#484848")
        frame_botones.pack(pady=10, fill=tk.X, padx=10)
        
        self.btn_eliminar_elemento = tk.Button(frame_botones, text="🗑️ Eliminar",
                                              font=("Arial", 10, "bold"), bg="#dc3545", fg="white",
                                              command=self.eliminar_elemento_seleccionado, relief=tk.FLAT)
        self.btn_eliminar_elemento.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        self.btn_limpiar_todos = tk.Button(frame_botones, text="🧹 Limpiar Todo",
                                          font=("Arial", 10, "bold"), bg="#fd7e14", fg="white",
                                          command=self.limpiar_todos_elementos, relief=tk.FLAT)
        self.btn_limpiar_todos.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        
    def crear_barra_estado(self):
        self.barra_estado = tk.Frame(self.root, bg="#3c3c3c", height=25)
        self.barra_estado.pack(fill=tk.X, side=tk.BOTTOM)
        self.barra_estado.pack_propagate(False)
        
        self.label_estado = tk.Label(self.barra_estado, text="Listo - Abre un PDF para comenzar",
                                    font=("Arial", 9), bg="#3c3c3c", fg="white")
        self.label_estado.pack(side=tk.LEFT, padx=10, pady=3)
        
        # Información de zoom
        self.label_zoom = tk.Label(self.barra_estado, text="Zoom: 100%",
                                  font=("Arial", 9), bg="#3c3c3c", fg="white")
        self.label_zoom.pack(side=tk.RIGHT, padx=10, pady=3)
        
    def configurar_shortcuts(self):
        # Atajos de teclado
        self.root.bind('<Control-o>', lambda e: self.abrir_pdf())
        self.root.bind('<Control-s>', lambda e: self.guardar_pdf())
        self.root.bind('<Control-Shift-S>', lambda e: self.guardar_como_pdf())
        self.root.bind('<Control-z>', lambda e: self.deshacer())
        self.root.bind('<Control-y>', lambda e: self.rehacer())
        self.root.bind('<Delete>', lambda e: self.eliminar_seleccion())
        self.root.bind('<Control-plus>', lambda e: self.zoom_mas())
        self.root.bind('<Control-minus>', lambda e: self.zoom_menos())
        self.root.bind('<Control-0>', lambda e: self.ajustar_ventana())
        
    # Métodos principales
    def abrir_pdf(self):
        ruta = filedialog.askopenfilename(
            title="Seleccionar archivo PDF",
            filetypes=[("Archivos PDF", "*.pdf")],
            initialdir=os.path.expanduser("~/Desktop")
        )
        if ruta:
            self.cargar_pdf(ruta)
            
    def cargar_pdf(self, ruta):
        try:
            if self.pdf_doc:
                self.pdf_doc.close()
                
            self.pdf_doc = fitz.open(ruta)
            self.total_paginas = len(self.pdf_doc)
            self.pagina_actual = 0
            self.archivo_cargado = True
            self.elementos_agregados = []
            
            # Actualizar interfaz
            self.actualizar_navegacion()
            self.generar_miniaturas()
            self.mostrar_pagina_actual()
            
            self.label_estado.config(text=f"PDF cargado: {os.path.basename(ruta)} ({self.total_paginas} páginas)")
            messagebox.showinfo("¡Éxito!", f"PDF cargado correctamente\n{self.total_paginas} páginas encontradas")
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar el PDF:\n{str(e)}")
            
    def mostrar_pagina_actual(self):
        if not self.archivo_cargado:
            return
            
        try:
            pagina = self.pdf_doc[self.pagina_actual]
            
            # Obtener la imagen de la página con zoom
            matrix = fitz.Matrix(self.zoom_level, self.zoom_level)
            pix = pagina.get_pixmap(matrix=matrix)
            img_data = pix.tobytes("ppm")
            
            # Convertir a imagen PIL y luego a PhotoImage
            pil_image = Image.open(io.BytesIO(img_data))
            self.imagen_pagina = ImageTk.PhotoImage(pil_image)
            
            # Limpiar canvas y mostrar nueva imagen
            self.canvas_pdf.delete("all")
            self.canvas_pdf.create_image(0, 0, anchor=tk.NW, image=self.imagen_pagina)
            
            # Configurar región de scroll
            self.canvas_pdf.configure(scrollregion=self.canvas_pdf.bbox("all"))
            
            # Redibujar elementos agregados
            self.redibujar_elementos()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al mostrar la página:\n{str(e)}")
            
    def generar_miniaturas(self):
        # Limpiar miniaturas anteriores
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
            
        if not self.archivo_cargado:
            return
            
        for i in range(self.total_paginas):
            try:
                pagina = self.pdf_doc[i]
                
                # Crear miniatura pequeña
                matrix = fitz.Matrix(0.3, 0.3)  # Escala pequeña para miniatura
                pix = pagina.get_pixmap(matrix=matrix)
                img_data = pix.tobytes("ppm")
                
                # Convertir a imagen
                pil_image = Image.open(io.BytesIO(img_data))
                thumbnail = ImageTk.PhotoImage(pil_image)
                
                # Frame para cada miniatura
                frame_mini = tk.Frame(self.scrollable_frame, bg="#484848", relief=tk.RAISED, bd=1)
                frame_mini.pack(fill=tk.X, padx=5, pady=2)
                
                # Label con la miniatura
                label_mini = tk.Label(frame_mini, image=thumbnail, bg="#484848")
                label_mini.image = thumbnail  # Mantener referencia
                label_mini.pack(pady=5)
                
                # Número de página
                tk.Label(frame_mini, text=f"Página {i+1}", font=("Arial", 8),
                        bg="#484848", fg="white").pack()
                
                # Evento de clic para ir a la página
                frame_mini.bind("<Button-1>", lambda e, p=i: self.ir_a_pagina(p))
                label_mini.bind("<Button-1>", lambda e, p=i: self.ir_a_pagina(p))
                
            except Exception as e:
                print(f"Error generando miniatura {i}: {e}")
                
    def ir_a_pagina(self, pagina):
        if 0 <= pagina < self.total_paginas:
            self.pagina_actual = pagina
            self.mostrar_pagina_actual()
            self.actualizar_navegacion()
            
    def actualizar_navegacion(self):
        if self.archivo_cargado:
            self.label_pagina.config(text=f"{self.pagina_actual + 1} / {self.total_paginas}")
        else:
            self.label_pagina.config(text="0 / 0")
            
    def pagina_anterior(self):
        if self.pagina_actual > 0:
            self.pagina_actual -= 1
            self.mostrar_pagina_actual()
            self.actualizar_navegacion()
            
    def pagina_siguiente(self):
        if self.pagina_actual < self.total_paginas - 1:
            self.pagina_actual += 1
            self.mostrar_pagina_actual()
            self.actualizar_navegacion()
            
    # Métodos de edición
    def cambiar_modo(self, modo):
        self.modo_edicion = modo
        self.label_estado.config(text=f"Modo: {modo.title()}")
        
        # Actualizar apariencia de botones
        botones = [self.btn_texto, self.btn_resaltar, self.btn_firma]
        for btn in botones:
            btn.config(relief=tk.FLAT)
            
        if modo == "texto":
            self.btn_texto.config(relief=tk.RAISED)
        elif modo == "resaltar":
            self.btn_resaltar.config(relief=tk.RAISED)
        elif modo == "firma":
            self.btn_firma.config(relief=tk.RAISED)
            
    def modo_agregar_texto(self):
        texto = self.entry_texto.get("1.0", tk.END).strip()
        if not texto:
            messagebox.showwarning("Advertencia", "Escribe algún texto primero")
            return
            
        self.cambiar_modo("texto")
        self.label_estado.config(text="Haz clic donde quieras agregar el texto")
        
    def on_canvas_click(self, event):
        self.click_x = self.canvas_pdf.canvasx(event.x)
        self.click_y = self.canvas_pdf.canvasy(event.y)
        
        if self.modo_edicion == "texto":
            self.agregar_texto(self.click_x, self.click_y)
            
    def on_canvas_drag(self, event):
        pass  # Para futuras funcionalidades como dibujar líneas
        
    def on_canvas_release(self, event):
        pass  # Para futuras funcionalidades
        
    def on_mousewheel(self, event):
        # Scroll vertical en el canvas
        self.canvas_pdf.yview_scroll(int(-1*(event.delta/120)), "units")
        
    def agregar_texto(self, x, y):
        if not self.archivo_cargado:
            return
            
        texto = self.entry_texto.get("1.0", tk.END).strip()
        if not texto:
            return
            
        tamano = self.scale_tamano.get()
        fuente = self.combo_fuente.get()        # Crear elemento de texto en el canvas
        texto_id = self.canvas_pdf.create_text(x, y, text=texto, anchor=tk.NW,
                                              font=(fuente, tamano), fill=self.muestra_color.cget('bg'))
        
        # Guardar información del elemento
        elemento = {
            'tipo': 'texto',
            'canvas_id': texto_id,
            'texto': texto,
            'x': x / self.zoom_level,  # Coordenadas relativas
            'y': y / self.zoom_level,
            'tamano': tamano,
            'fuente': fuente,
            'color': self.muestra_color.cget('bg'),
            'pagina': self.pagina_actual
        }
        self.elementos_agregados.append(elemento)
        self.actualizar_lista_elementos()
        self.label_estado.config(text=f"Texto agregado en página {self.pagina_actual + 1}")
        
    def redibujar_elementos(self):
        """Redibuja todos los elementos de la página actual"""
        if not self.archivo_cargado:
            return
            
        for elemento in self.elementos_agregados:
            if elemento['pagina'] == self.pagina_actual:
                if elemento['tipo'] == 'texto':
                    x = elemento['x'] * self.zoom_level
                    y = elemento['y'] * self.zoom_level
                    elemento['canvas_id'] = self.canvas_pdf.create_text(
                        x, y, text=elemento['texto'], anchor=tk.NW,
                        font=(elemento['fuente'], int(elemento['tamano'] * self.zoom_level)),
                        fill=elemento['color']
                    )
                    
    def actualizar_lista_elementos(self):
        self.lista_elementos.delete(0, tk.END)
        for i, elemento in enumerate(self.elementos_agregados):
            if elemento['tipo'] == 'texto':
                texto_preview = elemento['texto'][:20] + "..." if len(elemento['texto']) > 20 else elemento['texto']
                item = f"📝 Página {elemento['pagina'] + 1}: {texto_preview}"
                self.lista_elementos.insert(tk.END, item)
                
    def eliminar_elemento_seleccionado(self):
        seleccion = self.lista_elementos.curselection()
        if seleccion:
            indice = seleccion[0]
            elemento = self.elementos_agregados[indice]
            
            # Eliminar del canvas si está visible
            try:
                self.canvas_pdf.delete(elemento['canvas_id'])
            except:
                pass
                
            # Eliminar de la lista
            del self.elementos_agregados[indice]
            self.actualizar_lista_elementos()
            
            self.label_estado.config(text="Elemento eliminado")
            
    def limpiar_todos_elementos(self):
        if messagebox.askyesno("Confirmar", "¿Eliminar todos los elementos agregados?"):
            self.elementos_agregados.clear()
            self.actualizar_lista_elementos()
            self.mostrar_pagina_actual()  # Redibujar página limpia
            self.label_estado.config(text="Todos los elementos eliminados")
            
    def seleccionar_color(self, hex_color):
        self.muestra_color.config(bg=hex_color)
        self.color_actual = self.hex_to_rgb(hex_color)
        
    def hex_to_rgb(self, hex_color):
        """Convierte color hex a tupla RGB normalizada (0-1)"""
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16) / 255.0
        g = int(hex_color[2:4], 16) / 255.0
        b = int(hex_color[4:6], 16) / 255.0
        return (r, g, b)
        
    def actualizar_tamano(self, event):
        self.tamano_fuente = self.scale_tamano.get()
        
    # Métodos de zoom
    def zoom_mas(self):
        self.zoom_level = min(self.zoom_level * 1.25, 5.0)
        self.mostrar_pagina_actual()
        self.label_zoom.config(text=f"Zoom: {int(self.zoom_level * 100)}%")
        
    def zoom_menos(self):
        self.zoom_level = max(self.zoom_level / 1.25, 0.25)
        self.mostrar_pagina_actual()
        self.label_zoom.config(text=f"Zoom: {int(self.zoom_level * 100)}%")
        
    def ajustar_ventana(self):
        self.zoom_level = 1.0
        self.mostrar_pagina_actual()
        self.label_zoom.config(text="Zoom: 100%")
        
    # Métodos de guardado
    def guardar_pdf(self):
        if not self.archivo_cargado:
            messagebox.showwarning("Advertencia", "No hay PDF cargado")
            return
            
        if not self.elementos_agregados:
            messagebox.showinfo("Info", "No hay elementos para guardar")
            return
              # Guardar con el mismo nombre (sobrescribir)
        try:
            self.aplicar_elementos_a_pdf()
            ruta_guardado = filedialog.asksaveasfilename(
                title="Guardar PDF editado",
                defaultextension=".pdf",
                filetypes=[("PDF", "*.pdf")],
                initialfile="PDF_Editado.pdf",
                initialdir=os.path.expanduser("~/Desktop")
            )
            
            if ruta_guardado:
                self.pdf_doc.save(ruta_guardado)
                messagebox.showinfo("¡Éxito!", f"PDF guardado como:\n{os.path.basename(ruta_guardado)}")
                self.label_estado.config(text=f"PDF guardado: {os.path.basename(ruta_guardado)}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar PDF:\n{str(e)}")
            
    def guardar_como_pdf(self):
        self.guardar_pdf()  # Usa el mismo método
        
    def aplicar_elementos_a_pdf(self):
        """Aplica todos los elementos agregados al documento PDF"""
        if not self.archivo_cargado:
            return
            
        for elemento in self.elementos_agregados:
            if elemento['tipo'] == 'texto':
                pagina = self.pdf_doc[elemento['pagina']]
                
                # Convertir coordenadas de canvas a PDF
                x = elemento['x']
                y = pagina.rect.height - elemento['y']  # Invertir Y para PDF
                
                # Convertir color hex a RGB
                color = self.hex_to_rgb(elemento['color'])
                
                # Insertar texto en el PDF
                pagina.insert_text(
                    (x, y),
                    elemento['texto'],
                    fontsize=elemento['tamano'],
                    color=color,
                    fontname=elemento['fuente']
                )
                
    # Métodos de deshacer/rehacer (básicos)
    def deshacer(self):
        if self.elementos_agregados:
            elemento = self.elementos_agregados.pop()
            try:
                self.canvas_pdf.delete(elemento['canvas_id'])
            except:
                pass
            self.actualizar_lista_elementos()
            self.label_estado.config(text="Acción deshecha")
        else:
            self.label_estado.config(text="Nada que deshacer")
            
    def rehacer(self):
        # Implementación básica - se puede mejorar con un stack de rehacer
        self.label_estado.config(text="Función de rehacer no implementada")
        
    def eliminar_seleccion(self):
        self.eliminar_elemento_seleccionado()
        
    def __del__(self):
        if hasattr(self, 'pdf_doc') and self.pdf_doc:
            self.pdf_doc.close()

# Función principal
def main():
    root = tk.Tk()
    
    # Configurar estilo
    style = ttk.Style()
    style.theme_use('clam')
    
    # Configurar colores del tema
    style.configure('TNotebook', background='#383838', borderwidth=0)
    style.configure('TNotebook.Tab', background='#484848', foreground='white', 
                    padding=[20, 8], borderwidth=1)
    style.map('TNotebook.Tab', background=[('selected', '#4a9eff')])
    
    app = EditorPDFAvanzado(root)
    
    # Centrar ventana
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
    y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
    root.geometry(f"+{x}+{y}")
    
    root.mainloop()

if __name__ == "__main__":
    main()