import os
import wave
import time
import threading
import sys
import json
import asyncio
from pathlib import Path
import numpy as np

# Asegurar que ffmpeg esté en el PATH (especialmente después de instalarlo con winget)
ffmpeg_path = r"C:\Users\agude\AppData\Local\Microsoft\WinGet\Links"
if ffmpeg_path not in os.environ["PATH"]:
    os.environ["PATH"] += os.path.pathsep + ffmpeg_path

# Dependencias críticas
try:
    import pyaudio
    import pyperclip
    import pyautogui
    from pynput import keyboard
    from openai import OpenAI
    from dotenv import load_dotenv
    import httpx
    import whisper
    import warnings
    import pystray
    from PIL import Image, ImageDraw
    warnings.filterwarnings("ignore", category=UserWarning)
except ImportError as e:
    print(f"Error: Faltan dependencias. {e}")
    sys.exit(1)

# Cargar configuración
load_dotenv()

# Se eliminó la dependencia del dashboard UI por solicitud del usuario.

try:
    from app.overlay import ModernOverlay
except ImportError as e:
    ModernOverlay = None
    print(f"Aviso: No se pudo cargar el ModernOverlay. {e}")

class VoiceToTextApp:
    def __init__(self):
        self.stop_requested = False
        # Configuración General
        self.use_local = os.getenv("USE_LOCAL_MODEL", "false").lower() == "true"
        self.local_base = os.getenv("LOCAL_API_BASE", "http://localhost:11434/v1")
        self.api_key = os.getenv("OPENAI_API_KEY", "sk-local")
        
        # Cliente para LLM (Corrección) - Local (LM Studio) u OpenAI
        llm_base = self.local_base if self.use_local else None
        self.llm_client = OpenAI(api_key=self.api_key, base_url=llm_base)
        
        # Opciones Groq
        self.use_groq_stt = os.getenv("USE_GROQ_STT", "false").lower() == "true"
        self.groq_api_key = os.getenv("GROQ_API_KEY", "")
        if self.use_groq_stt and self.groq_api_key:
            print("[INIT] Inicializando cliente Groq para STT...")
            self.groq_client = OpenAI(api_key=self.groq_api_key, base_url="https://api.groq.com/openai/v1")
            self.whisper_model = None
        else:
            self.groq_client = None
            # Cargar Modelo Whisper Local
            print("[INIT] Cargando modelo Whisper (esto puede tardar la primera vez)...")
            self.whisper_model = whisper.load_model("base") # "base" es rápido y preciso
        
        # Hotkey: Por defecto ctrl_l+space
        self.hotkey_str = os.getenv("HOTKEY", "<ctrl>+<space>")
        self.recording_path = os.getenv("RECORDING_PATH", "temp_recording.wav")
        self.stt_model = os.getenv("STT_MODEL", "whisper-1")
        self.llm_model = os.getenv("LLM_MODEL", "gpt-4o-mini")
        self.correction_prompt = os.getenv("CORRECTION_PROMPT", "Corrige el texto.")
        self.dashboard_port = int(os.getenv("DASHBOARD_PORT", "8000"))
        
        self.is_recording = False
        self.audio_frames = []
        
        # Audio config
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 44100
        self.chunk = 1024   
        self.p_audio = pyaudio.PyAudio()
        self._list_audio_devices()
        
        # Tray Icon setup
        self.icon = None

    def _list_audio_devices(self):
        """Lista los dispositivos de entrada disponibles para diagnóstico."""
        count = self.p_audio.get_device_count()
        print(f"\n[DIAGNOSTIC] Detectados {count} dispositivos de audio:")
        for i in range(count):
            info = self.p_audio.get_device_info_by_index(i)
            if info.get('maxInputChannels') > 0:
                print(f"  - [{i}] {info.get('name')} (Entrada)")
        if count == 0:
            print("  ! ADVERTENCIA: No se detectaron dispositivos de audio.")

    def on_model_change(self, model_name):
        print(f"[UI] Modelo cambiado a: {model_name}")
        if "Groq" in model_name:
            self.use_groq_stt = True
            if not self.groq_client and self.groq_api_key:
                self.groq_client = OpenAI(api_key=self.groq_api_key, base_url="https://api.groq.com/openai/v1")
        else:
            self.use_groq_stt = False
            if not self.whisper_model:
                print("[INIT] Cargando modelo Whisper (esto puede tardar la primera vez)...")
                self.whisper_model = whisper.load_model("base")

    def on_language_change(self, language):
        print(f"[UI] Idioma cambiado a: {language}")
        self.language_setting = language if language != "auto" else None

    def send_ui_update(self, msg_type, **kwargs):
        pass # Dashboard removido

    def start_recording(self):
        if self.is_recording: return
        self.is_recording = True
        self.audio_frames = []
        if hasattr(self, 'overlay') and self.overlay:
            self.overlay.set_recording_state(True)
            
        threading.Thread(target=self._record_thread, daemon=True).start()
        print(f"\n[REC] Grabando ({self.hotkey_str})...")
        self.send_ui_update("status", message="Grabando...", recording=True)

    def stop_recording(self):
        if not self.is_recording: return
        self.is_recording = False
        if hasattr(self, 'overlay') and self.overlay:
            self.overlay.set_recording_state(False)
            
        print("[PROCESS] Procesando audio...")
        self.send_ui_update("status", message="Procesando...", recording=False)
        self._save_audio()
        threading.Thread(target=self._process_flow, daemon=True).start()

    def _record_thread(self):
        try:
            # Intentar abrir el stream de audio
            try:
                stream = self.p_audio.open(format=self.format, channels=self.channels,
                                          rate=self.rate, input=True,
                                          frames_per_buffer=self.chunk)
            except Exception as e:
                msg = "ERROR: No se pudo abrir el micrófono. ¿Tienes un dispositivo conectado?"
                print(f"\n[AUDIO] {msg}")
                self.send_ui_update("status", message=msg, recording=False)
                self.is_recording = False
                return

            while self.is_recording:
                data = stream.read(self.chunk, exception_on_overflow=False)
                self.audio_frames.append(data)
                
                # Calcular nivel de audio para el visualizador
                audio_data = np.frombuffer(data, dtype=np.int16)
                level = np.abs(audio_data).mean() / 1000  # Normalizado simple
                
                if hasattr(self, 'overlay') and self.overlay:
                    # Enviar el nivel al overlay
                    # En tkinter, modificar UI desde otro thread aveces causa bugs, 
                    # pero `after` es seguro. Lo empaquetamos:
                    self.overlay.root.after(0, self.overlay.update_audio_level, level / 50.0) # Normalizar un poco más para animación

                if len(self.audio_frames) % 5 == 0: # Reducir spam de WS
                    self.send_ui_update("audio_level", level=float(level))

            stream.stop_stream()
            stream.close()
        except Exception as e:
            print(f"Error de audio: {e}")
            self.is_recording = False

    def _save_audio(self):
        wf = wave.open(self.recording_path, 'wb')
        wf.setnchannels(self.channels)
        wf.setsampwidth(self.p_audio.get_sample_size(self.format))
        wf.setframerate(self.rate)
        wf.writeframes(b''.join(self.audio_frames))
        wf.close()

    def _process_flow(self):
        raw_text = self._transcript_audio()
        if not raw_text:
            self.send_ui_update("status", message="No se detectó voz.")
            return

        print(f"[STT] {raw_text}")
        clean_text = self._correct_text(raw_text)
        print(f"[LLM] {clean_text}")
        
        self.send_ui_update("transcript", text=clean_text)
        self._inject_text(clean_text)
        self.send_ui_update("status", message="Texto inyectado.")

    def _transcript_audio(self):
        try:
            lang_param = getattr(self, 'language_setting', "es")
            if self.use_groq_stt and self.groq_client:
                # Transcripción rápida con Groq
                with open(self.recording_path, "rb") as audio_file:
                    kwargs = {
                        "file": audio_file,
                        "model": "whisper-large-v3-turbo",
                        "response_format": "text"
                    }
                    if lang_param: kwargs["language"] = lang_param
                    result = self.groq_client.audio.transcriptions.create(**kwargs)
                return result.strip()
            else:
                # Transcripción local con Whisper
                kwargs = {"fp16": False}
                if lang_param: kwargs["language"] = lang_param
                result = self.whisper_model.transcribe(self.recording_path, **kwargs)
                return result["text"].strip()
        except Exception as e:
            print(f"STT Error: {e}")
            return None

    def _correct_text(self, text):
        try:
            res = self.llm_client.chat.completions.create(
                model=self.llm_model,
                messages=[
                    {"role": "system", "content": self.correction_prompt},
                    {"role": "user", "content": text}
                ]
            )
            return res.choices[0].message.content.strip()
        except Exception as e:
            print(f"LLM Error: {e}")
            return text

    def _inject_text(self, text):
        pyperclip.copy(text)
        time.sleep(0.1)
        pyautogui.hotkey('ctrl', 'v')

    def test_mic(self):
        """Realiza una prueba de 5 segundos sin enviar a la API."""
        if self.is_recording: return
        self.is_recording = True
        self.audio_frames = []
        
        print("\n[TEST] Iniciando prueba de 5 segundos...")
        self.send_ui_update("status", message="Probando micrófono (5s)...", recording=True)
        
        # Hilo de grabación tradicional
        threading.Thread(target=self._record_thread, daemon=True).start()
        
        # Esperar 5 segundos y parar
        def stop_after_delay():
            time.sleep(5)
            self.is_recording = False
            self.send_ui_update("status", message="Analizando señal...", recording=False)
            self._analyze_test_audio()
            
        threading.Thread(target=stop_after_delay, daemon=True).start()

    def _analyze_test_audio(self):
        """Analiza los frames capturados y reporta calidad."""
        if not self.audio_frames:
            self.send_ui_update("status", message="ERROR: No se capturó audio.")
            return

        audio_data = np.frombuffer(b''.join(self.audio_frames), dtype=np.int16)
        max_val = np.abs(audio_data).max()
        avg_val = np.abs(audio_data).mean()
        
        quality = "Excelente" if avg_val > 500 else "Baja (revisa ganancia)"
        if max_val < 50: quality = "Nula (revisa conexión)"
        
        msg = f"Prueba terminada. Calidad: {quality} (Avg: {int(avg_val)})"
        print(f"[TEST] {msg}")
        self.send_ui_update("status", message=msg)

    def _setup_tray(self):
        """Configura y arranca el icono en la bandeja del sistema."""
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        
        image_path = Path(os.path.join(base_path, "app", "static", "icon.png"))
        if image_path.exists():
            image = Image.open(image_path)
        else:
            # Crear un icono temporal si no existe
            image = Image.new('RGB', (64, 64), color=(0, 120, 215))
            d = ImageDraw.Draw(image)
            d.text((10, 20), "V-Txt", fill=(255, 255, 255))
        
        menu = pystray.Menu(
            pystray.MenuItem("Cerrar Aplicación", self.quit_app)
        )
        self.icon = pystray.Icon("voice_txt", image, "Voice-txt Active", menu)
        self.icon.run()

    def quit_app(self, icon=None, item=None):
        print("\n[QUIT] Cerrando aplicación...")
        self.stop_requested = True
        if self.icon:
            self.icon.stop()
        # Forzar cierre si pynput se queda colgado
        os._exit(0)

    def run(self):
        # Iniciar Listener de teclado en hilo separado
        threading.Thread(target=self._start_standard_listener, daemon=True).start()
        
        # Pystray no le gusta correr en hilos secundarios en Windows a veces, 
        # pero para que funcione CustomTkinter, el main thread debe pertenecerle a Tkinter.
        threading.Thread(target=self._setup_tray, daemon=True).start()
        
        print(f"Listo. Hotkey: {self.hotkey_str}")
        
        # Iniciar y bloquear el hilo principal con ModernOverlay
        if ModernOverlay:
            self.overlay = ModernOverlay(self.on_model_change, self.on_language_change)
            self.overlay.start()
        else:
            # Si fallo import, mantener vivo
            while True: time.sleep(1)

    def _ui_command_listener(self):
        """Escucha comandos que vienen desde el WebSocket del Dashboard."""
        from app.server import ui_commands
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def listen():
            while True:
                msg = await ui_commands.get()
                if msg.get("command") == "test_mic":
                    self.test_mic()
        
        loop.run_until_complete(listen())

    def _start_standard_listener(self):
        """Listener para detectar presionar y soltar keys."""
        current_keys = set()
        
        # Mapeo simple de hotkey string a sets para detección
        # Soporta "ctrl+space", "alt+x", etc.
        target_keys = set(self.hotkey_str.replace("<", "").replace(">", "").lower().split("+"))
        if "ctrl_l" in target_keys or "ctrl_r" in target_keys:
            target_keys.add("ctrl")

        def on_press(key):
            try:
                # Normalizar nombre de tecla
                k_name = ""
                if hasattr(key, 'char') and key.char:
                    k_name = key.char.lower()
                elif hasattr(key, 'name'):
                    k_name = key.name.lower()
                
                if k_name:
                    current_keys.add(k_name)
                
                # Especial para CTRL
                if key in [keyboard.Key.ctrl_l, keyboard.Key.ctrl_r]:
                    current_keys.add("ctrl")

                # Verificar si todas las teclas del hotkey están presionadas
                is_match = all(k in current_keys for k in target_keys)
                
                if is_match and not self.is_recording:
                    # Al iniciar la grabación, main.py llama a self.start_recording(), 
                    # el cual llama a self.overlay.set_recording_state(True),
                    # y este ahora internamente llama a self.wake_up().
                    self.start_recording()
            except Exception as e:
                pass

        def on_release(key):
            try:
                k_name = ""
                if hasattr(key, 'char') and key.char:
                    k_name = key.char.lower()
                elif hasattr(key, 'name'):
                    k_name = key.name.lower()
                
                if k_name in current_keys:
                    current_keys.remove(k_name)
                    
                if key in [keyboard.Key.ctrl_l, keyboard.Key.ctrl_r]:
                    if "ctrl" in current_keys: current_keys.remove("ctrl")
                
                # Si se suelta cualquiera de las teclas de la combinación, paramos
                if self.is_recording:
                    # Opcional: solo parar si se suelta una del hotkey
                    self.stop_recording()
            except Exception:
                pass

        try:
            with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
                listener.join()
        except Exception as e:
            print(f"Error crítico en el listener de teclado: {e}")
            print("TIP: Esto suele ocurrir si no hay permisos de acceso al dispositivo de entrada o no hay sesión X.")

if __name__ == "__main__":
    app_instance = VoiceToTextApp()
    app_instance.run()
