"""Generate worldmap_land.png (dim land) and worldmap_dots.png (5100 supplier dots, illustrative
positions, same sampling as mograph A0_06) from mograph/data/world110.json (Natural Earth 110m).
python3 make_worldmap.py"""
import os
import sys

from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
EP = os.path.dirname(os.path.dirname(HERE))
sys.path[:0] = [os.path.join(EP, "mograph"), os.path.join(os.path.dirname(os.path.dirname(EP)), "shared", "tools")]
import a0  # noqa: E402

W, H = 4096, 2048


def P(lon, lat):
    return ((lon + 180) / 360 * W, (90 - lat) / 180 * H)


land = Image.new("L", (W, H), 0)
d = ImageDraw.Draw(land)
for pl in a0._world():
    d.polygon([P(*p) for p in pl], fill=90, outline=150)
land.save(os.path.join(HERE, "worldmap_land.png"))
dots = Image.new("L", (W, H), 0)
d = ImageDraw.Draw(dots)
for lon, lat in a0._supplier_points():
    x, y = P(lon, lat)
    d.ellipse((x - 2.5, y - 2.5, x + 2.5, y + 2.5), fill=255)
dots = dots.filter(ImageFilter.GaussianBlur(0.8))
dots.save(os.path.join(HERE, "worldmap_dots.png"))
print("ok")
