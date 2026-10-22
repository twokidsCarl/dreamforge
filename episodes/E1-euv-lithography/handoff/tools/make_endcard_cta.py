"""E1 end card with the eigenlens.ai call to action (Carl 2026-10-23): the locked brand end card, unchanged, lifted
10 %, with two lines under it. Output: episodes/E1-euv-lithography/brand/endcard_cta.png (1920x1080).
Also writes endcard_cta_text.png (the two lines on transparent). edit_film.apply_brand_stings, when that file exists,
appends a CTA tail after sting_end.mp4: the locked card slides up 10 % and the lines fade in (see handoff/END_CARD.md).
  python3 episodes/E1-euv-lithography/handoff/tools/make_endcard_cta.py"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "../../../.."))
sys.path.insert(0, os.path.join(REPO, "shared/tools"))
from PIL import Image, ImageDraw, ImageFilter
from overlay_labels import font

CTA = "互动版在这里：跟着光，自己走一遍"
URL = "eigenlens.ai"
OUTFIT = "/usr/share/fonts/truetype/sand-box/google/Outfit/Outfit-VariableFont_wght.ttf"
W, H = 1920, 1080
GOLD, INK = (236, 190, 92), (232, 236, 244)

base = Image.open(os.path.join(REPO, "brand/eigenlens_logo_locked/endcard_16x9.png")).convert("RGB").resize((W, H))
img = Image.new("RGB", (W, H), base.getpixel((3, 3)))        # the card's own near-black, so no seam
img.paste(base, (0, round(-0.10 * H)))                         # locked card unchanged, lifted 10 % to make room
layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
d = ImageDraw.Draw(layer)
f_cta = font(round(0.034 * H))
try:
    from PIL import ImageFont
    f_url = ImageFont.truetype(OUTFIT, round(0.056 * H)); f_url.set_variation_by_axes([300])
except Exception:
    f_url = font(round(0.05 * H))
d.text((W / 2, 0.835 * H), CTA, font=f_cta, anchor="mm", fill=(*INK, 235))
glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
ImageDraw.Draw(glow).text((W / 2, 0.91 * H), URL, font=f_url, anchor="mm", fill=(*GOLD, 150))
layer.alpha_composite(glow.filter(ImageFilter.GaussianBlur(10)))
d.text((W / 2, 0.91 * H), URL, font=f_url, anchor="mm", fill=(*GOLD, 255))
out = os.path.join(REPO, "episodes/E1-euv-lithography/brand/endcard_cta.png")
Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB").save(out, optimize=True)
layer.save(out.replace(".png", "_text.png"), optimize=True)    # text only (RGBA): edit_film fades it in
print(out, os.path.getsize(out))
