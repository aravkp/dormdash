from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

OUT_DIR = Path(__file__).parent
BG = "#4f46e5"   # theme color
FG = "white"
LABEL = "DD"

sizes = [
    (192, "icon-192.png"),
    (512, "icon-512.png"),
]

def make_icon(size, filename):
    img = Image.new("RGB", (size, size), BG)
    draw = ImageDraw.Draw(img)
    # Try to use a decent TTF if available, fallback to default bitmap font
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", int(size * 0.5))
    except Exception:
        font = ImageFont.load_default()
    w, h = draw.textsize(LABEL, font=font)
    x = (size - w) / 2
    y = (size - h) / 2
    draw.text((x, y), LABEL, font=font, fill=FG)
    out_path = OUT_DIR / filename
    img.save(out_path, format="PNG")
    print(f"Written {out_path}")

if __name__ == "__main__":
    for s, name in sizes:
        make_icon(s, name)