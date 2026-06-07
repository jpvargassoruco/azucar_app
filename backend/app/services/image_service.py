from PIL import Image
import os
from app.config import settings

def compress_to_thumbnail(source_path: str, target_dir: str, filename: str) -> str:
    """
    Compresses an original image to a thumbnail of size configured in settings.
    Saves it as an optimized JPEG. Returns the absolute path of the thumbnail.
    """
    os.makedirs(target_dir, exist_ok=True)
    
    # Generate thumbnail name
    base, _ = os.path.splitext(filename)
    thumb_filename = f"thumb_{base}.jpg"
    thumb_path = os.path.join(target_dir, thumb_filename)
    
    with Image.open(source_path) as img:
        # Resize preserving aspect ratio
        img.thumbnail((settings.THUMBNAIL_SIZE, settings.THUMBNAIL_SIZE))
        
        # Convert to RGB if PNG/RGBA to save as JPEG
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
            
        # Save compressed
        img.save(thumb_path, "JPEG", quality=80, optimize=True)
        
    return thumb_path
