"""CPU check for sub/superscripts: a 3D-shot label, a subtitle and a mograph Canvas line, one 960x540 frame.
  python3 episodes/E1-euv-lithography/handoff/tools/test_richtext.py OUT.png"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../../shared/tools"))
from PIL import Image, ImageDraw
import edit_film as EF
from overlay_labels import draw_label, font
from richtext import draw_text

W, H = 960, 540
img = Image.new("RGBA", (W, H), (18, 22, 34, 255))
layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
draw_label(layer, {"text": "Sn⁸⁺ – Sn¹⁴⁺ 谱线", "sub": "H₂ → 2 H· ｜ Sn + 4 H· → SnH₄", "source": "ASML · ARCNL",
                   "pos": "upper_right"}, 1.0, W, H)
img = Image.alpha_composite(img, layer)
d = ImageDraw.Draw(img)
y = 60
for s, px in [("CD = k₁ · λ / NA", 40), ("锡烷 SnH₄ · 氢气 H₂ · Sn¹²⁺ · 10¹⁰ 种跃迁", 30), ("旧做法（压平）：Sn8+ H2 SnH4", 24)]:
    draw_text(d, (40, y), s, font(px), fill=(235, 238, 245)); y += px * 2
img = EF.subtitle(img, "氢自由基抓住锡，变成锡烷 SnH₄", W, H)
img.convert("RGB").save(sys.argv[1] if len(sys.argv) > 1 else "/tmp/richtext_test.png")
