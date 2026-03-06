from PIL import Image
import os
import sys

# La última imagen subida es el micrófono colorido
img_path = r"C:\Users\agude\.gemini\antigravity\brain\877ca009-d72b-45f4-a864-e43a8c6276c2\media__1772768049793.png"

def extract_microphone():
    src = Image.open(img_path).convert("RGBA")
    w, h = src.size
    print(f"Original Mic size: {w}x{h}")
    
    # Queremos borrar el fondo. En la imagen parece ser gris muy oscuro casi negro.
    # El micrófono tiene colores brillantes (pastel azul, morado, durazno).
    data = src.getdata()
    active_data = []
    idle_data = [] # Para el micrófono negro puro
    
    for item in data:
        r, g, b, a = item
        # Si no es brillante (los colores del mic son muy claros), lo volvemos transparente
        if r < 80 and g < 80 and b < 80:
            active_data.append((0, 0, 0, 0))
            idle_data.append((0, 0, 0, 0))
        else:
            # Mantener para activo
            active_data.append(item)
            
            # Convertir a negro con la misma transparecia original (opaco) para el modo inactivo (Idle)
            # Pero el usuario pidió "completamente negro cuando este apagado"
            idle_data.append((0, 0, 0, a))
            
    # Activo (Color)
    active_img = Image.new("RGBA", (w, h))
    active_img.putdata(active_data)
    
    # Recortar los bordes vacíos automáticamente
    bbox = active_img.getbbox()
    if bbox:
        active_img = active_img.crop(bbox)
        
    # Resize a un tamaño visible pero que encaje en el nuevo diseño
    # Un cuadrado de aprox 120x150 se ve bien
    active_img.thumbnail((120, 150), Image.Resampling.LANCZOS)
    
    out_active = r"C:\Users\agude\Documents\Whisper\Voice-txt\app\mic_active.png"
    active_img.save(out_active)
    print(f"Active micro guardado en: {out_active}")
    
    # Inactivo (Negro)
    idle_img = Image.new("RGBA", (w, h))
    idle_img.putdata(idle_data)
    if bbox:
        idle_img = idle_img.crop(bbox)
        
    idle_img.thumbnail((120, 150), Image.Resampling.LANCZOS)
    out_idle = r"C:\Users\agude\Documents\Whisper\Voice-txt\app\mic_idle.png"
    idle_img.save(out_idle)
    print(f"Idle micro guardado en: {out_idle}")

extract_microphone()
