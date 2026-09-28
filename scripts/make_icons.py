"""Create the simple leaf-and-path app mark without external assets."""
from pathlib import Path

from PIL import Image, ImageDraw

folder = Path(__file__).resolve().parents[1] / "web" / "icons"
folder.mkdir(parents=True, exist_ok=True)
canvas = Image.new("RGB", (1024, 1024), "#27634D")
draw = ImageDraw.Draw(canvas)
draw.ellipse((240, 220, 570, 550), fill="#FAF8F2")
draw.ellipse((450, 340, 700, 590), fill="#D2DDAD")
draw.line([(405, 600), (512, 475), (610, 385)], fill="#27634D", width=22)
draw.arc((330, 450, 710, 810), 110, 260, fill="#FAF8F2", width=32)
draw.ellipse((605, 702, 641, 738), fill="#FAF8F2")
for name, size in [("icon-192.png", 192), ("icon-512.png", 512), ("maskable-512.png", 512), ("apple-touch-icon.png", 180)]:
    canvas.resize((size, size), Image.Resampling.LANCZOS).save(folder / name)
