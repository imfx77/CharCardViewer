"""Image utility functions for thumbnail generation."""

import os
import hashlib
from PIL import Image
from pathlib import Path


def getThumbnailCache(app_path : str, image_path : str, size=(256, 256)):

    # Ensure cache directory exists
    thumbnails_cache_dir = Path(app_path).joinpath('.thumbs_cache')
    os.makedirs(thumbnails_cache_dir, exist_ok=True)

    # Stable prefix based only on image path
    prefix = hashlib.sha1(image_path.encode()).hexdigest()

    # Get last modified timestamp of original file
    mtime = Path(image_path).stat().st_mtime

    # Hash only the changing parts (size + mtime)
    variable_key = f"{size}-{mtime}"
    variable_hash = hashlib.sha1(variable_key.encode()).hexdigest()

    # Final filename: <prefix>_<variable_hash>.jpg
    cache_name = f"{prefix}_{variable_hash}.jpg"
    cache_path = thumbnails_cache_dir / cache_name

    # If cached thumbnail exists → return it
    if os.path.exists(cache_path):
        return cache_path

    # Remove stale thumbnails for this image
    for f in thumbnails_cache_dir.glob(f"{prefix}_*.jpg"):
        try:
            f.unlink()
        except Exception:
            pass

    # Otherwise generate thumbnail
    img = Image.open(image_path)
    img.thumbnail(size)
    imgRGB = img.convert("RGB")
    imgRGB.save(cache_path)
    #imgRGB.save(cache_path, format="JPEG", optimize=True, compress_level=9)

    return cache_path

