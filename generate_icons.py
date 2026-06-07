from PIL import Image, ImageDraw
import os

os.makedirs("frontend/icons", exist_ok=True)

def create_icon(size):
    # Dark blue background (matching --bg-primary #0a0e1a)
    img = Image.new("RGBA", (size, size), (10, 14, 26, 255))
    draw = ImageDraw.Draw(img)
    
    # Indigo circle in the center
    margin = size // 10
    draw.ellipse(
        [margin, margin, size - margin, size - margin],
        fill=(129, 140, 248, 255)  # --accent-indigo
    )
    
    # White health cross
    w = size // 6
    h = size // 2
    cx, cy = size // 2, size // 2
    
    # Horizontal bar
    draw.rectangle(
        [cx - h // 2, cy - w // 2, cx + h // 2, cy + w // 2],
        fill=(255, 255, 255, 255)
    )
    # Vertical bar
    draw.rectangle(
        [cx - w // 2, cy - h // 2, cx + w // 2, cy + h // 2],
        fill=(255, 255, 255, 255)
    )
    
    img.save(f"frontend/icons/icon-{size}x{size}.png", "PNG")

if __name__ == "__main__":
    create_icon(192)
    create_icon(512)
    print("Default PWA icons generated successfully.")
