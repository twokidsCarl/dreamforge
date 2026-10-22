"""A1 2D shots: chapter card, latent image in the resist, ~100 layers vs a 100-storey tower (F44),
overlay box-in-box marks, "a finer pen writes smaller", and the pen of light that frays at its finest."""
import math
import os
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from mograph import CYAN, INK, INK2, VIOLET, Canvas, ease, ease_out, fade, seg, shot

HERE = os.path.dirname(__file__)
CIRCUIT = os.path.join(os.path.dirname(HERE), "blender", "textures", "circuit.png")


def _after_vignette(c, out):
    """Point the canvas at the finished frame so corner notes drawn next are not greyed by the vignette."""
    c.img = out
    c.d = ImageDraw.Draw(out, "RGBA")
    return out


@shot("A1_01")
def chapter(t, dur, W, H):
    c = Canvas(W, H, bg=(4, 5, 8))
    a = fade(t, 0.0, dur, dur, 0.4)
    k = c.k
    bg = Image.new("RGB", (W, H), (4, 5, 8))
    d = ImageDraw.Draw(bg)
    # rainbow sheen on a wafer edge: a band of touching arcs (no gaps, so no moire once the blur drops). The arc
    # runs 185-335 deg about a centre below the frame, so both ends lie outside the picture (no cut edge)
    # the wafer: a dark disc whose rim arcs across the upper third, centre far below the frame
    cxp, cyp, rw = 1250 * k, 2620 * k, 2520 * k
    d.ellipse((cxp - rw, cyp - rw, cxp + rw, cyp + rw), fill=(13, 14, 19))
    for i in range(60):                                            # the sheen hugs the rim, just inside it
        hue = i / 60
        col = tuple(int(90 + 80 * math.sin(2 * math.pi * (hue + o))) for o in (0.0, 0.33, 0.66))
        r = rw - (12 + i * 2.5) * k
        d.arc((cxp - r, cyp - r, cxp + r, cyp + r), 200, 340, fill=col, width=max(2, int(5 * k)))
    d.ellipse((cxp - rw, cyp - rw, cxp + rw, cyp + rw), outline=(70, 74, 88), width=max(1, int(3 * k)))   # bevel
    # soft angular falloff: the colours peak right of centre and die away before either frame edge's arc end
    yy, xx = np.mgrid[0:H, 0:W]
    ang = np.degrees(np.arctan2(yy - cyp, xx - cxp)) % 360
    ramp = np.clip(np.minimum(ang - 240, 305 - ang) / 22.0, 0, 1)
    ramp = ramp * ramp * (3 - 2 * ramp)
    rr = np.hypot(yy - cyp, xx - cxp)
    sheen = ((rr < rw - 6 * k) & (rr > rw - 190 * k))[..., None]
    base = np.asarray(bg, dtype=np.float32)
    floor = np.array((13, 14, 19), np.float32)
    arr = np.where(sheen, (base - floor) * ramp[..., None] + floor, base)
    bg = Image.fromarray(arr.clip(0, 255).astype(np.uint8))
    blur = 26 * (1 - ease(seg(t, 0.8, dur - 0.4))) + 6                # never sharper than 6 px: one smooth sheen
    bg = bg.filter(ImageFilter.GaussianBlur(blur * k))
    c.img = Image.blend(Image.new("RGB", (W, H), (4, 5, 8)), bg, 0.7 * a)
    c.d = ImageDraw.Draw(c.img, "RGBA")
    c.g = ImageDraw.Draw(c.glow)
    on = ease(seg(t, 0.2, 0.9))
    c.text((960, 500), "光刻是什么", 96, INK, a * on, anchor="mm", weight_glow=True)
    c.text((960, 610), "Lithography", 40, INK2, a * ease(seg(t, 0.5, 1.2)), anchor="mm")
    return c.finish(glow_radius=12, glow_gain=0.8)


@shot("A1_05")
def latent(t, dur, W, H):
    c = Canvas(W, H)
    a = fade(t, 0.0, dur, dur, 0.3)
    k = c.k
    rnd = random.Random(5)
    im = Image.new("L", (W, H), 30)
    d = ImageDraw.Draw(im)
    top, bot = int(300 * k), int(780 * k)
    d.rectangle((0, top, W, bot), fill=96)                         # the resist layer in section
    d.rectangle((0, bot, W, H), fill=60)                           # substrate below
    # a thin resist is exposed almost uniformly through its thickness from the start (MicroChemicals, A1_sources S10
    # p6): the exposed columns change everywhere at once, a little weaker near the substrate; no descending front
    e = ease(seg(t, 0.3, dur - 1.0))
    blocks = [(160 + 320 * i, 160 + 320 * i + 160) for i in range(6)]
    if e > 0:                                                      # the changed columns brighten as a whole
        for j in range(16):
            y0 = top + (bot - top) * j / 16
            y1 = top + (bot - top) * (j + 1) / 16
            v = int(96 + 34 * e * (1 - 0.3 * (j + 0.5) / 16))
            for b0, b1 in blocks:
                d.rectangle((b0 * k, y0, b1 * k, y1), fill=v)
    for _ in range(2600):                                          # the polymer network
        x, y = rnd.uniform(0, W), rnd.uniform(top, bot)
        exposed = any(b0 * k <= x <= b1 * k for b0, b1 in blocks)
        depth = (y - top) / (bot - top)
        v = 120 + 55 * e * (1 - 0.3 * depth) if exposed else 120
        L = rnd.uniform(4, 12) * k
        ang = rnd.uniform(0, math.pi)
        d.line((x, y, x + L * math.cos(ang), y + L * math.sin(ang)), fill=int(v), width=max(1, int(2 * k)))
    if e > 0:                                                      # the latent image outline, full height
        for b0, b1 in blocks:
            for xb in (b0, b1):
                d.line((xb * k, top, xb * k, bot), fill=int(96 + 114 * e), width=max(1, int(2 * k)))
    im = im.filter(ImageFilter.GaussianBlur(1.2 * k))
    im = Image.blend(im, Image.effect_noise((W, H), 30), 0.2)
    c.img = Image.merge("RGB", (im, im, im))
    c.d = ImageDraw.Draw(c.img, "RGBA")
    c.g = ImageDraw.Draw(c.glow)
    c.text((80, 260), "光刻胶", 30, INK, a, anchor="lm")
    c.text((80, 830), "衬底", 30, INK, a * 0.85, anchor="lm")
    c.text((1824, 260), "潜像（示意）", 30, INK, a * ease(seg(t, 1.6, 2.2)), anchor="rm")
    return c.finish(glow_radius=4, glow_gain=0.4)


@shot("A1_08")
def hundred_layers(t, dur, W, H):
    c = Canvas(W, H)
    a = fade(t, 0.0, dur, dur, 0.3)
    n = int(100 * ease(seg(t, 0.2, dur - 0.9)))
    base = 960
    lh = 7.6
    w = 300                                                         # one straight column, like the tower
    for i in range(n):
        y = base - (i + 1) * lh
        fine = i < 22                                               # the finest layers sit at the bottom (count illustrative)
        col = VIOLET if fine else (110 + i // 2, 116 + i // 2, 140 + i // 3)
        c.rect((640 - w / 2, y, 640 + w / 2, y + lh - 1.4), fill=tuple(min(255, v) for v in col), a=a * 0.9)
    if n >= 22:
        c.text((640 + w / 2 + 24, base - 11 * lh), "最精细的那几层", 30, VIOLET, a, anchor="lm")
    c.text((640, base + 50), "上百层" if n >= 100 else f"{n} 层", 40, INK, a, anchor="mm", weight_glow=n >= 100)
    # a 100-storey tower lighting floor by floor
    tx, tw = 1300, 160
    for i in range(100):
        y = base - (i + 1) * lh
        on = i < n
        c.rect((tx, y, tx + tw, y + lh - 1.6), fill=(250, 220, 150) if on else (36, 40, 52), a=a * (0.85 if on else 0.8))
    c.rect((tx + tw / 2 - 4, base - 100 * lh - 60, tx + tw / 2 + 4, base - 100 * lh), fill=(80, 86, 100), a=a)
    c.text((tx + tw / 2, base + 50), "100 层的楼", 30, INK2, a, anchor="mm")
    out = _after_vignette(c, c.finish(glow_radius=8, glow_gain=0.6))   # corner note keeps full brightness
    c.text((1824, 76), "ASML：一颗芯片有上百层图形 · 层数示意", 28, INK, a * 0.9, anchor="rm")   # action-safe
    return out


@shot("A1_10")
def overlay(t, dur, W, H):
    c = Canvas(W, H)
    a = fade(t, 0.0, dur, dur, 0.3)
    k = c.k
    rnd = random.Random(3)
    im = Image.new("L", (W, H), 54)
    d = ImageDraw.Draw(im)
    for i in range(14):                                            # lower layer pattern
        y = int((80 + i * 72) * k)
        d.rectangle((0, y, W, y + int(28 * k)), fill=120)
    im = im.filter(ImageFilter.GaussianBlur(1.5 * k))
    im = Image.blend(im, Image.effect_noise((W, H), 30), 0.2)
    c.img = Image.merge("RGB", (im, im, im))
    c.d = ImageDraw.Draw(c.img, "RGBA")
    c.g = ImageDraw.Draw(c.glow)
    slide = ease(seg(t, 0.8, 3.6))
    off = (1 - slide) * 70
    # upper layer: translucent vertical lines, shifted
    for i in range(22):
        x = 60 + i * 90 + off
        c.rect((x, 0, x + 34, 1080), fill=(220, 224, 236), a=a * 0.22)
    # box-in-box marks: outer (lower layer) fixed, inner (upper layer) slides in
    for (mx, my) in ((520, 540), (1400, 540)):
        c.rect((mx - 120, my - 120, mx + 120, my + 120), outline=(200, 204, 214), width=8, a=a)
        c.rect((mx - 55 + off, my - 55 + off * 0.6, mx + 55 + off, my + 55 + off * 0.6), outline=(240, 244, 250), width=8, a=a)
        if slide > 0.98:
            c.rect((mx - 60, my - 60, mx + 60, my + 60), outline=CYAN, width=2, a=a, glow=True)
    freeze = ease(seg(t, 3.6, 3.8)) * (1 - ease(seg(t, 4.2, 4.6)))
    if freeze > 0:
        c.rect((0, 0, 1920, 1080), outline=CYAN, width=6, a=a * freeze)
    c.text((960, 120), "套刻 overlay：每一层都要对准下面那层", 32, INK, a * ease(seg(t, 0.2, 0.8)), anchor="mm")
    out = _after_vignette(c, c.finish(glow_radius=6, glow_gain=0.8))
    c.rect((1824 - 196, 1000 - 26, 1824 + 14, 1000 + 26), fill=(6, 8, 12), a=a * 0.6, radius=10)   # scrim: legible
    c.text((1824, 1000), "SEM 风格示意", 28, INK, a, anchor="rm")
    return out


_CIRC = None


@shot("A1_11")
def finer_pen(t, dur, W, H):
    global _CIRC
    c = Canvas(W, H)
    a = fade(t, 0.0, dur, dur, 0.3)
    box = (660, 240, 1260, 840)                                    # the square stays put
    c.rect(box, outline=INK2, width=3, a=a)
    steps = [(0.0, 1), (1.6, 2), (3.0, 4), (4.2, 8), (5.2, 16), (6.0, 32)]
    n = 1
    for t0, m in steps:
        if t >= t0:
            n = m
    tex = ease(seg(t, 7.0, 8.4))                                    # characters blur into a texture -> layout
    if tex < 1:
        cell = 600 / n
        size = cell * 0.82
        if size >= 3:
            for i in range(n):
                for j in range(n):
                    c.text((660 + cell * (i + 0.5), 240 + cell * (j + 0.5)), "芯", size, INK, a * (1 - tex), anchor="mm")
    if tex > 0:
        if _CIRC is None:
            _CIRC = Image.open(CIRCUIT).convert("L")
        k = c.k
        side = int(600 * k)
        crop = _CIRC.crop((300, 300, 900, 900)).resize((side, side), Image.BICUBIC)
        vio = Image.merge("RGB", (crop.point(lambda v: int(v * 0.75)), crop.point(lambda v: int(v * 0.6)), crop))
        mask = Image.new("L", (side, side), int(255 * tex * a))
        c.img.paste(vio, (int(660 * k), int(240 * k)), mask)
        c.d = ImageDraw.Draw(c.img, "RGBA")
    labels = {1: "粗笔：1 个字", 2: "细一点：4 个", 4: "16 个", 8: "64 个", 16: "256 个", 32: "1024 个……"}
    c.text((960, 900), labels[n] if tex < 0.5 else "→ 电路版图（示意）", 34, INK, a, anchor="mm")
    c.text((960, 150), "笔越细 → 字越小 → 装得越多", 40, INK, a * ease(seg(t, 0.3, 0.9)), anchor="mm", weight_glow=True)
    return c.finish(glow_radius=8, glow_gain=0.6)


@shot("A1_12")
def pen_of_light(t, dur, W, H):
    c = Canvas(W, H, bg=(0, 0, 0))
    a = fade(t, 0.0, dur, dur, 0.3)
    p = ease_out(seg(t, 0.2, dur - 0.5))
    x0, x1 = 160, 160 + 1600 * p
    k = c.k
    layer = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(layer)
    segs = 160
    for i in range(int(segs * p)):
        u = i / segs
        w = 22 * (1 - u) ** 1.6 + 1.2                              # the line gets thinner...
        xa = 160 + 1600 * u
        xb = 160 + 1600 * (u + 1 / segs)
        jitter = max(0.0, u - 0.7) * 26                            # ...and frays at its finest
        y = 540 + random.Random(i).uniform(-1, 1) * jitter
        d.line((xa * k, y * k, xb * k, y * k), fill=255, width=max(1, int(w * k)))
    fray = max(0.0, p - 0.7) / 0.3
    if fray > 0:
        far = layer.filter(ImageFilter.GaussianBlur(6 * k * fray))
        layer = Image.composite(far, layer, Image.linear_gradient("L").rotate(90).resize((W, H)))
    rgb = Image.merge("RGB", (layer.point(lambda v: int(v * 0.8)), layer.point(lambda v: int(v * 0.65)), layer))
    c.img = rgb
    c.glow.paste(rgb)
    c.d = ImageDraw.Draw(c.img, "RGBA")
    c.circle((x1, 540), 10, fill=(240, 230, 255), a=a, glow=True)  # the pen tip
    return c.finish(glow_radius=14, glow_gain=1.0)
