from PIL import Image
import os
import sys

img_path = r"C:\Users\agude\.gemini\antigravity\brain\877ca009-d72b-45f4-a864-e43a8c6276c2\media__1772767972071.png"

def make_frames():
    src = Image.open(img_path).convert("RGB")
    w, h = src.size
    print(f"Original size: {w}x{h}")
    
    frame_w = w // 8
    
    app_dir = r"C:\Users\agude\Documents\Whisper\Voice-txt\app"
    
    for i in range(8):
        # Añadimos un recorte de 8 píxeles a izquierda y derecha para eliminar las líneas grises divisorias
        left = (i * frame_w) + 8
        right = ((i + 1) * frame_w) - 8
        
        # Mantenemos el recorte vertical
        top = int(h * 0.15)
        bottom = int(h * 0.85)
        
        box = (left, top, right, bottom)
        frame = src.crop(box)
        
        # Redimensionar al tamaño final requerido en la UI (manteniendo el espacio para las ondas)
        frame = frame.resize((80, 60), Image.Resampling.LANCZOS)
        
        out_path = os.path.join(app_dir, f"frame_{i}.png")
        frame.save(out_path)
        print(f"Saved {out_path}")

make_frames()
