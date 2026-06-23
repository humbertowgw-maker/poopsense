import base64
import io
from PIL import Image, ImageOps

def image_to_base64(image_path):
    with Image.open(image_path) as image:
        normalized = ImageOps.exif_transpose(image).convert("RGB")
        normalized.thumbnail((2000, 2000))
        output = io.BytesIO()
        normalized.save(output, format="JPEG", quality=88, optimize=True)
        return base64.b64encode(output.getvalue()).decode("utf-8")
