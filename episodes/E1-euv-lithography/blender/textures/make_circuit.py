"""Generate circuit.png: a stylised standard-cell layout mask (white = pattern), tileable rows.
Illustrative only, not a real design.   python3 make_circuit.py"""
import os
import random

from PIL import Image, ImageDraw, ImageFilter

S = 2048
rnd = random.Random(7)
im = Image.new("L", (S, S), 0)
d = ImageDraw.Draw(im)
row_h = 64
for r in range(S // row_h):
    y0 = r * row_h
    d.rectangle((0, y0, S, y0 + 5), fill=200)                          # power rails
    x = 0
    while x < S:
        w = rnd.choice((24, 32, 40, 48, 64, 96))
        for k in range(1, w // 8):                                      # vertical gates
            if rnd.random() < 0.6:
                gx = x + k * 8
                d.rectangle((gx, y0 + 12, gx + 2, y0 + row_h - 12), fill=255)
        if rnd.random() < 0.7:                                          # local metal
            yy = y0 + rnd.randint(18, row_h - 22)
            d.rectangle((x + 2, yy, x + w - 2, yy + 3), fill=230)
        for _ in range(rnd.randint(0, 3)):                              # vias
            vx, vy = x + rnd.randint(2, max(3, w - 6)), y0 + rnd.randint(10, row_h - 14)
            d.rectangle((vx, vy, vx + 4, vy + 4), fill=255)
        x += w + 4
for _ in range(90):                                                      # long routing tracks
    if rnd.random() < 0.5:
        y = rnd.randrange(0, S, 8)
        x0 = rnd.randrange(0, S - 200)
        d.rectangle((x0, y, x0 + rnd.randint(120, 900), y + 3), fill=180)
    else:
        x = rnd.randrange(0, S, 8)
        y0 = rnd.randrange(0, S - 200)
        d.rectangle((x, y0, x + 3, y0 + rnd.randint(120, 900)), fill=180)
im = im.filter(ImageFilter.GaussianBlur(0.6))
im.save(os.path.join(os.path.dirname(os.path.abspath(__file__)), "circuit.png"))
print("circuit.png", im.size)
