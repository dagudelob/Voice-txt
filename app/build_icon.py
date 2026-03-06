from PIL import Image
import os

app_dir = r"C:\Users\agude\Documents\Whisper\Voice-txt\app"
png_path = os.path.join(app_dir, "mic_active.png")

if os.path.exists(png_path):
    img = Image.open(png_path)
    ico_path = os.path.join(app_dir, "icon.ico")
    img.save(ico_path, format="ICO", sizes=[(256, 256), (128, 128), (64, 64), (32, 32)])
    print(f"Icon saved at {ico_path}")
