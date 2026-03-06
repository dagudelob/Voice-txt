import os
import threading
import customtkinter as ctk
from PIL import Image, ImageDraw, ImageTk
import numpy as np
import os

class ModernOverlay:
    def __init__(self, on_model_change_callback, on_language_change_callback):
        self.root = ctk.CTk()
        
        # Tema moderno y oscuro
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Configurar ventana
        self.root.overrideredirect(True) # Quitar bordes de Windows
        self.root.attributes("-topmost", True) # Siempre arriba
        self.ui_scale = 1.0
        self.default_width = 130
        self.default_height = 160
        
        # Aplicar el ícono de micrófono a la ventana ("Barra de Tareas" Windows)
        import os
        ico_path = os.path.join(os.path.dirname(__file__), "icon.ico")
        if os.path.exists(ico_path):
            try:
                self.root.iconbitmap(ico_path)
            except Exception:
                pass

        # Posicionar ventana vertical arriba/centro o abajo/centro
        self._update_window_geometry()
        
        # Variables de estado de la ventana
        self._drag_data = {"x": 0, "y": 0}
        self.hide_timer = None
        self.is_visible = True
        
        # Main vertical flow container
        self.main_frame = ctk.CTkFrame(self.root, corner_radius=15, fg_color="#1E1E1E")
        self.main_frame.pack(fill="both", expand=True, padx=2, pady=2)
        
        self.main_frame.bind("<ButtonPress-1>", self.on_drag_start)
        self.main_frame.bind("<B1-Motion>", self.on_drag_motion)
        self.root.bind("<Any-Motion>", self.reset_hide_timer)
        self.root.bind("<Enter>", self.reset_hide_timer)
        
        import tkinter as tk 
        
        # ==== TOP CONTROL BAR (Apple Style) ====
        self.top_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent", height=20)
        self.top_frame.pack(side="top", fill="x", padx=2, pady=(5, 0))
        # Para que los botones se empujen a la izquierda
        self.top_frame.bind("<ButtonPress-1>", self.on_drag_start)
        self.top_frame.bind("<B1-Motion>", self.on_drag_motion)

        # Red: Close, Yellow: Minimize, Green: Scale
        self.close_btn = ctk.CTkButton(self.top_frame, text="", width=12, height=12, corner_radius=6,
                                       fg_color="#FF5F56", hover_color="#E0443E", command=self.quit)
        self.close_btn.pack(side="left", padx=(2, 4))
        
        self.min_btn = ctk.CTkButton(self.top_frame, text="", width=12, height=12, corner_radius=6,
                                     fg_color="#FFBD2E", hover_color="#DEA125", command=self.hide)
        self.min_btn.pack(side="left", padx=4)
        
        self.scale_btn = ctk.CTkButton(self.top_frame, text="", width=12, height=12, corner_radius=6,
                                       fg_color="#27C93F", hover_color="#1AAB29", command=self.cycle_ui_scale)
        self.scale_btn.pack(side="left", padx=4)

        # ==== MIDDLE FRAME (Big Dynamic Microphone) ====
        self.mid_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.mid_frame.pack(side="top", fill="both", expand=True)
        self.mid_frame.bind("<ButtonPress-1>", self.on_drag_start)
        self.mid_frame.bind("<B1-Motion>", self.on_drag_motion)

        # Cargar el micrófono purificado y encogerlo 40% adicional (48x60 -> 29x36)
        base_dir = os.path.dirname(__file__)
        self.mic_img = ctk.CTkImage(Image.open(os.path.join(base_dir, "mic_active.png")), size=(56, 60))
        
        # Secuencia de onda animada continua reducida 40% (80x60 -> 48x36)
        self.wave_frames = []
        for i in range(8):
            frame_path = os.path.join(base_dir, f"frame_{i}.png")
            if os.path.exists(frame_path):
                img = Image.open(frame_path).convert("RGB")
                self.wave_frames.append(ctk.CTkImage(light_image=img, dark_image=img, size=(80, 60)))
        
        self.current_frame = 0
        
        # Un solo Label central que intercambiará entre el Micro y las Ondas, con menor separación
        self.center_label = ctk.CTkLabel(self.mid_frame, text="", image=self.mic_img)
        self.center_label.pack(expand=True, pady=(2, 5))
        self.center_label.bind("<ButtonPress-1>", self.on_drag_start)
        self.center_label.bind("<B1-Motion>", self.on_drag_motion)
        
        # ==== BOTTOM FRAME (Stacked Menus) ====
        self.bottom_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.bottom_frame.pack(side="bottom", fill="x", padx=10, pady=(0, 15))
        self.bottom_frame.bind("<ButtonPress-1>", self.on_drag_start)
        self.bottom_frame.bind("<B1-Motion>", self.on_drag_motion)

        self._on_model_callback = on_model_change_callback
        self._on_lang_callback = on_language_change_callback

        self.lang_var = ctk.StringVar(value="Auto Detect")
        self.model_var = ctk.StringVar(value="Local Model : LM-Studio")
        
        pill_kwargs = {
            "height": 22, "corner_radius": 21, "border_width": 3, 
            "fg_color": "transparent", "border_color": "#536173", "hover_color": "#2A2A2D", 
            "text_color": "#A9B1BD", "font": ("Inter", 8)
        }

        # Botón Idioma arriba (stacked)
        self.lang_btn = ctk.CTkButton(self.bottom_frame, textvariable=self.lang_var, command=self._show_lang_menu, **pill_kwargs)
        self.lang_btn.pack(side="top", fill="x", pady=2)
        
        # Botón Modelo abajo (stacked)
        self.model_btn = ctk.CTkButton(self.bottom_frame, textvariable=self.model_var, command=self._show_model_menu, **pill_kwargs)
        self.model_btn.pack(side="top", fill="x", pady=2)

        # Crear menús nativos escondidos en negro/gris
        self.lang_menu = tk.Menu(self.root, tearoff=0, bg="#1E1E1E", fg="#A9B1BD", activebackground="#2A2A2D", font=("Inter", 8))
        for lang in ["Spanish (ES)", "English (US)", "Auto Detect"]:
            self.lang_menu.add_command(label=lang, command=lambda l=lang: self._select_lang(l))
            
        self.model_menu = tk.Menu(self.root, tearoff=0, bg="#1E1E1E", fg="#A9B1BD", activebackground="#2A2A2D", font=("Inter", 8))
        for mod in ["Speech GPT v4", "Local Model : LM-Studio", "Whisper (Local)"]:
            self.model_menu.add_command(label=mod, command=lambda m=mod: self._select_model(m))
        
        # Estado de animación
        self.is_recording = False
        
        # Iniciar el timer la primera vez
        self.reset_hide_timer()

    def _update_window_geometry(self):
        """Actualiza el tamaño de la ventana según el scale factor."""
        w = int(self.default_width * self.ui_scale)
        h = int(self.default_height * self.ui_scale)
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x_cordinate = int((screen_width/2) - (w/2))
        y_cordinate = screen_height - h - 60
        self.root.geometry(f"{w}x{h}+{x_cordinate}+{y_cordinate}")

    def cycle_ui_scale(self):
        """Alterna el tamaño general de la interfaz 1.0 -> 1.25 -> 1.5 -> 1.0"""
        if self.ui_scale == 1.0:
            self.ui_scale = 1.25
        elif self.ui_scale == 1.25:
            self.ui_scale = 1.5
        else:
            self.ui_scale = 1.0
            
        self._update_window_geometry()
        
        # Aumentar un poco la fuente de los botones píldora a escala
        new_font = ("Inter", int(12 * self.ui_scale))
        new_h = int(34 * (1 + (self.ui_scale-1)/2)) # Escala suavizada
        self.lang_btn.configure(font=new_font, height=new_h)
        self.model_btn.configure(font=new_font, height=new_h)
        self.reset_hide_timer()

    def _show_lang_menu(self):
        # Muestra el menu justo debajo de lang_btn
        x = self.lang_btn.winfo_rootx()
        y = self.lang_btn.winfo_rooty() + self.lang_btn.winfo_height() + 2
        self.lang_menu.tk_popup(x, y)
        self.reset_hide_timer()

    def _select_lang(self, lang):
        self.lang_var.set(lang)
        if self._on_lang_callback:
            val = "es" if "Spanish" in lang else "en" if "English" in lang else "auto"
            self._on_lang_callback(val)
        self.reset_hide_timer()

    def _show_model_menu(self):
        x = self.model_btn.winfo_rootx()
        y = self.model_btn.winfo_rooty() + self.model_btn.winfo_height() + 2
        self.model_menu.tk_popup(x, y)
        self.reset_hide_timer()

    def _select_model(self, mod):
        self.model_var.set(mod)
        if self._on_model_callback:
            val = mod
            self._on_model_callback(val)
        self.reset_hide_timer()

    def on_drag_start(self, event):
        """Guarda la posición inicial cuando se hace clic para arrastrar."""
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y

    def on_drag_motion(self, event):
        """Calcula el offset y mueve la ventana."""
        x = self.root.winfo_x() - self._drag_data["x"] + event.x
        y = self.root.winfo_y() - self._drag_data["y"] + event.y
        self.root.geometry(f"+{x}+{y}")
        self.reset_hide_timer()
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y

    def on_drag_motion(self, event):
        """Calcula el offset y mueve la ventana."""
        x = self.root.winfo_x() - self._drag_data["x"] + event.x
        y = self.root.winfo_y() - self._drag_data["y"] + event.y
        self.root.geometry(f"+{x}+{y}")
        self.reset_hide_timer()

    def hide(self):
        """Oculta visualmente la ventana sin destruirla."""
        if self.is_visible:
            self.root.withdraw()
            self.is_visible = False
            
    def wake_up(self):
        """Vuelve a mostrar la ventana y reinicia el timer (usado cuando hay voz)."""
        if not self.is_visible:
            self.root.deiconify()
            self.is_visible = True
        self.reset_hide_timer()
        self.root.lift()

    def reset_hide_timer(self, event=None):
        """Reinicia el temporizador de 30 segundos. Si está grabando, no oculta."""
        if self.hide_timer is not None:
            self.root.after_cancel(self.hide_timer)
            
        if not self.is_recording:
            # Configurar para que llame a `self.hide` en 30000 ms (30 segundos)
            self.hide_timer = self.root.after(30000, self.hide)
        else:
            self.hide_timer = None

    def set_recording_state(self, state: bool):
        self.is_recording = state
        if state:
            self.wake_up()
            # Al grabar, mostrar el primer frame de ondas
            if self.wave_frames:
                self.center_label.configure(image=self.wave_frames[0])
            self.reset_hide_timer()
        else:
            # En reposo, volver a mostrar el micrófono colorido
            self.center_label.configure(image=self.mic_img)
            self.current_frame = 0
            self.reset_hide_timer()

    def update_audio_level(self, level: float):
        # Avanza continuamente independiente del volumen como pidió el usuario, saltando frame a frame (dinámico)
        if self.is_recording and self.wave_frames:
            self.center_label.configure(image=self.wave_frames[self.current_frame])
            self.current_frame = (self.current_frame + 1) % len(self.wave_frames)

    def start(self):
        """Inicia el mainloop. Esto DEBE ser llamado desde el hilo principal de Python."""
        self.root.mainloop()
        
    def quit(self):
        """Sale completamente de la aplicación."""
        import os
        self.root.quit()
        os._exit(0) # Forzar cierre de todos los hilos
