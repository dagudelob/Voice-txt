from PIL import Image
import os
import sys

img_path = r"C:\Users\agude\.gemini\antigravity\brain\877ca009-d72b-45f4-a864-e43a8c6276c2\media__1772767675548.png"

def make_transparent_and_crop():
    src = Image.open(img_path).convert("RGBA")
    w, h = src.size
    print(f"Original size: {w}x{h}")
    
    # Let's assume the background color is at (5, 5)
    bg_color = src.getpixel((5, 5))
    print(f"Background color: {bg_color}")
    
    # Process transparency
    data = src.getdata()
    new_data = []
    
    # We want to remove the grid lines too. The grid lines might be slightly lighter
    # than the background.
    # Let's completely isolate the pastel colors. The pastel colors have high RGB values.
    # If a pixel is dark (r < 100, g < 100, b < 100), we can just make it transparent.
    for item in data:
        # If the pixel is dark enough, it's background or grid.
        # The wave colors are bright pastel (e.g. #88D9AC -> 136, 217, 172)
        if item[0] < 100 and item[1] < 100 and item[2] < 100:
            new_data.append((0, 0, 0, 0)) # Transparent
        else:
            new_data.append(item)
            
    src.putdata(new_data)
    
    # Now slice into 8 frames
    frame_w = w // 8
    frames = []
    for i in range(8):
        left = i * frame_w
        right = (i + 1) * frame_w
        # Crop tight around the center. The waves occupy the middle.
        # Let's say top 30% and bottom 70% is empty space
        top = int(h * 0.25)
        bottom = int(h * 0.80)
        
        box = (left, top, right, bottom)
        frame = src.crop(box)
        
        # Resize nicely to 80x60
        frame = frame.resize((80, 60), Image.Resampling.LANCZOS)
        frames.append(frame)
        
    out_path = r"C:\Users\agude\Documents\Whisper\Voice-txt\app\waves.gif"
    frames[0].save(
        out_path,
        save_all=True,
        append_images=frames[1:],
        duration=100,
        loop=0,
        disposal=2, # Clear background per frame
        transparency=0
    )
    print(f"Success! {out_path}")

make_transparent_and_crop()
