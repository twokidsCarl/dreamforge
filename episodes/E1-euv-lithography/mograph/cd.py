"""C/D 2D shots: four flash inserts cut from earlier renders, the chip dive in warm white, one droplet /
two pulses / ~10 mirrors (F4, F7), energy per wafer (F48, F49), source power (F4c, reported), next episode."""
import math
import os
import random
import sys

from PIL import Image, ImageDraw

from mograph import (CYAN, INK, INK2, ORANGE, RENDERS, VIOLET, Canvas, ease, ease_out, fade, seg, shot)

sys.path.insert(0, os.path.dirname(__file__))
import a0  # noqa: E402


def shot_frame(sid, idx, W, H):
    """Frame idx (1-based, clamped) of another shot's best available render, or None."""
    for q in ("final", "sample", "preview"):
        d = os.path.join(RENDERS, "shots", sid, q)
        if os.path.isdir(d):
            fr = sorted(f for f in os.listdir(d) if f.endswith(".png"))
            if fr:
                p = os.path.join(d, fr[max(0, min(len(fr) - 1, idx - 1))])
                return Image.open(p).convert("RGB").resize((W, H), Image.LANCZOS)
    return None


INSERTS = [("B1_13", 6), ("B2_01", 20), ("B8_04", 30), ("B8_03", 100)]


@shot("C_07")
def inserts(t, dur, W, H):
    k = min(3, int(t / 1.0))
    sid, f0 = INSERTS[k]
    local = t - k
    im = shot_frame(sid, f0 + int(local * 24), W, H) or Image.new("RGB", (W, H), (0, 0, 0))
    flash = max(0.0, 1 - local / 0.12)                             # a white flash on every cut
    if flash > 0:
        im = Image.blend(im, Image.new("RGB", (W, H), (255, 255, 255)), flash)
    return im


@shot("D_02")
def chip_warm(t, dur, W, H):
    start = shot_frame("A0_08", 999, W, H)
    im = a0.chip_dive(t * 1.4, dur * 1.4, W, H)                     # the A0_09 dive, faster
    im = im.convert("RGB", (0, 0, 1, 0, 0.5, 0, 0.5, 0, 0, 1, 0, 0))  # violet strokes -> warm white
    if start is not None:
        x = ease(seg(t, 0.0, 0.9))
        im = Image.blend(start, im, x)
    return im


@shot("D_03")
def one_two_ten(t, dur, W, H):
    c = Canvas(W, H, bg=(0, 0, 0))
    a = fade(t, 0.0, dur, dur, 0.3)
    on = ease(seg(t, 0.2, 0.8))
    c.circle((420, 540), 46, fill=(200, 205, 215), a=a * on)
    c.circle((404, 522), 12, fill=(255, 255, 255), a=a * on)
    for k, t0 in enumerate((1.0, 1.5)):                            # two orange pulses
        f = max(0.0, 1 - (t - t0) / 0.3) if t >= t0 else 0
        if f > 0:
            c.line((0, 540 - 30 + 60 * k), (420, 540), ORANGE, 8 + 10 * k, a * f, glow=True)
            c.circle((420, 540), 70 + 40 * k, fill=ORANGE, a=a * f * 0.5, glow=True)
    pts = [(560, 400), (720, 660), (880, 380), (1040, 640), (1200, 360), (1360, 620), (1500, 380), (1640, 600),
           (1780, 400), (1940, 560)]
    prev = (420, 540)
    for i, p in enumerate(pts):
        g = ease(seg(t, 2.2 + 0.18 * i, 2.4 + 0.18 * i))
        if g <= 0:
            break
        c.line(prev, p, VIOLET, 3, a * g, glow=True)
        c.circle(p, 10, fill=(230, 220, 255), a=a * g, glow=True)
        prev = p
    c.text((420, 650), "1 滴锡", 32, INK, a * on, anchor="mm")
    c.text((420, 300), "2 发激光", 32, ORANGE, a * ease(seg(t, 1.2, 1.6)), anchor="mm")
    c.text((1200, 850), "约 10 面镜子", 32, VIOLET, a * ease(seg(t, 3.4, 3.9)), anchor="mm")
    c.text((1880, 1030), "F4 · F7", 18, INK2, a, anchor="rm")
    return c.finish(glow_radius=10, glow_gain=1.0)


@shot("D_04")
def energy(t, dur, W, H):
    c = Canvas(W, H)
    a = fade(t, 0.0, dur, dur, 0.3)
    # left: a power dial with no precise scale, needle swinging into the "megawatt class" band
    cx, cy, R = 520, 560, 280
    l = ease(seg(t, 0.2, 1.0))
    c.circle((cx, cy), R, outline=INK2, width=3, a=a * l)
    a0_, a1_ = math.radians(210), math.radians(-30)
    band0, band1 = 0.68, 0.9
    for i in range(30):
        u = band0 + (band1 - band0) * i / 30
        th = a0_ + (a1_ - a0_) * u
        c.line((cx + 0.86 * R * math.cos(th), cy - 0.86 * R * math.sin(th)), (cx + R * math.cos(th), cy - R * math.sin(th)),
               ORANGE, 4, a * l)
    v = 0.79 * ease_out(seg(t, 0.8, 2.4)) + 0.01 * math.sin(t * 7) * (t > 2.4)
    th = a0_ + (a1_ - a0_) * v
    c.line((cx, cy), (cx + 0.82 * R * math.cos(th), cy - 0.82 * R * math.sin(th)), INK, 6, a * l, glow=True)
    c.text((cx, cy + 120), "兆瓦量级", 44, ORANGE, a * ease(seg(t, 2.0, 2.6)), anchor="mm", weight_glow=True)
    c.text((cx, cy + 180), "行业估算（F48）", 22, INK2, a * ease(seg(t, 2.0, 2.6)), anchor="mm")
    # right: energy per wafer, two data points only
    r = ease(seg(t, 5.2, 6.4))
    base, hmax = 860, 520
    c.rect((1180, base - hmax * r, 1340, base), fill=(120, 126, 150), a=a, radius=6)
    c.rect((1500, base - hmax * 0.43 * ease(seg(t, 6.4, 7.6)), 1660, base), fill=CYAN, a=a, glow=True, radius=6)
    c.text((1260, base + 40), "2018", 28, INK2, a * r, anchor="mm")
    c.text((1580, base + 40), "2025", 28, INK, a * r, anchor="mm")
    dd = ease(seg(t, 7.6, 8.4))
    c.text((1580, base - hmax * 0.43 - 70), "−57%", 64, CYAN, a * dd, anchor="mm", weight_glow=True)
    c.text((1420, 200), "每片晶圆的能耗（ASML · F49）", 28, INK, a * r, anchor="mm")
    return c.finish(glow_radius=8, glow_gain=0.7)


@shot("D_05")
def power_curve(t, dur, W, H):
    c = Canvas(W, H)
    a = fade(t, 0.0, dur, dur, 0.3)
    pan = 380 * ease(seg(t, 1.6, dur - 0.2))
    def Y(w):  # noqa: E306
        return 900 - (w - 200) * 0.9 + pan
    p = ease_out(seg(t, 0.0, dur - 0.4))
    pts = [(200 + 1500 * u, Y(250 + 1350 * u ** 1.6)) for u in [i / 80 for i in range(81)]]
    n = int(80 * p)
    for i in range(n):
        c.line(pts[i], pts[i + 1], VIOLET, 4, a, glow=True)
    if n:
        c.circle(pts[n], 10, fill=(240, 230, 255), a=a, glow=True)
    for w, lab in ((600, "量产约 600 W"), (1000, "1000 W 原理样机（实验室）")):
        y = Y(w)
        for x in range(160, 1760, 30):
            c.line((x, y), (x + 16, y), INK2, 2, a * 0.7)
        c.text((1780, y), lab, 26, INK, a, anchor="rm")
    c.text((80, 1030), "F4c · 数据为媒体报道", 18, INK2, a, anchor="lm")
    return c.finish(glow_radius=10, glow_gain=0.9)


STYLE_THUMBS = [("cycles", "photoreal", "真实"), ("cycles", "xray", "透明"), ("eevee", "blueprint", "蓝图"),
                ("eevee", "energy", "能量")]


@shot("D_10")
def next_episode(t, dur, W, H):
    c = Canvas(W, H, bg=(0, 0, 0))
    a = fade(t, 0.0, dur, dur, 0.5)
    c.text((960, 260), "下一期 · 幕后篇", 72, INK, a * ease(seg(t, 0.2, 0.9)), anchor="mm", weight_glow=True)
    c.text((960, 350), "用 AI 和 Blender 做一部片子", 34, INK2, a * ease(seg(t, 0.6, 1.2)), anchor="mm")
    k = c.k
    tw, th = 360, 203
    for i, (eng, st, lab) in enumerate(STYLE_THUMBS):
        x0 = 960 - 2 * (tw + 30) + 15 + i * (tw + 30)
        flip = ease(seg(t, 1.4 + 0.5 * i, 1.9 + 0.5 * i))
        sx = max(0.02, math.sin(math.pi / 2 * flip))
        p = os.path.join(RENDERS, "style_test", eng, f"CamStyle_{st}", "0230.png")
        if os.path.exists(p) and flip > 0:
            im = Image.open(p).convert("RGB").resize((max(1, int(tw * sx * k)), int(th * k)), Image.LANCZOS)
            im = Image.blend(Image.new("RGB", im.size), im, a)
            c.img.paste(im, (int((x0 + tw / 2 - tw * sx / 2) * k), int(560 * k)))
            c.d = ImageDraw.Draw(c.img, "RGBA")
        c.rect((x0, 560, x0 + tw, 560 + th), outline=INK2, width=2, a=a * 0.8)
        c.text((x0 + tw / 2, 560 + th + 40), lab, 28, INK, a * flip, anchor="mm")
    return c.finish(glow_radius=10, glow_gain=0.7)
