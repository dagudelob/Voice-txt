import os
from PIL import Image

app_dir = r"C:\Users\agude\Documents\Whisper\Voice-txt\app"

def build():
    frames = []
    for i in range(8):
        path = os.path.join(app_dir, f"frame_{i}.png")
        if os.path.exists(path):
            frames.append(Image.open(path))
            
    if frames:
        out_path = os.path.join(app_dir, "ondas_dinamicas.gif")
        frames[0].save(
            out_path,
            save_all=True,
            append_images=frames[1:],
            duration=80, # 80ms => ~12.5 fps jumps smoothly from 1 to 8 to 1
            loop=0
        )
        print(f"Animated GIF built at: {out_path}")
    else:
        print("Frames not found!")

if __name__ == "__main__":
    build()
