"""B8 2D shots: g gauges (F15b), force vs picometre displacement (F41), 60 pm sensor next to a silicon
atom (F42, F60), the 80 µm hair (F44), 1000+ overlay marks (F44), 96 fields x 220 wafers (F45), the
slit metronome, and 31 TB a week vs Hubble (F46)."""
import math
import os
import random
import sys

from PIL import Image, ImageDraw, ImageFilter

from mograph import (CYAN, INK, INK2, ORANGE, VIOLET, Canvas, ease, ease_out, fade, seg, shot)

sys.path.insert(0, os.path.dirname(__file__))
import b6  # noqa: E402  (wafer-field layout)

RED = (240, 72, 72)
GREY = (120, 126, 140)


# ---- shared backgrounds -----------------------------------------------------------------------
def stage_bg(c, t, shake=0.0, seed=8):
    """Dark, defocused 'real stage' plate for HUD shots: soft metal edges and rails."""
    rnd = random.Random(seed)
    k = c.k
    bg = Image.new("RGB", (c.W, c.H), (14, 16, 20))
    d = ImageDraw.Draw(bg)
    for i in range(7):
        y = int((200 + i * 130 + rnd.uniform(-30, 30)) * k)
        d.rectangle((0, y, c.W, y + int(rnd.uniform(8, 40) * k)), fill=(26 + i * 3, 29 + i * 3, 36 + i * 3))
    for i in range(5):
        x = int(rnd.uniform(100, 1800) * k)
        d.rectangle((x, int(150 * k), x + int(rnd.uniform(60, 260) * k), int(950 * k)), fill=(30, 33, 40))
    bg = bg.filter(ImageFilter.GaussianBlur(18 * k))
    dx = int(shake * k * math.sin(t * 90))
    dy = int(shake * k * math.cos(t * 77))
    c.img.paste(bg, (dx, dy))


def gauge(c, cx, cy, R, value, vmax, a, color=CYAN, ref=None, ref_label="", label="", ring_col=None, big=False):
    ring_col = ring_col or color
    c.circle((cx, cy), R, outline=ring_col, width=3 if not big else 6, a=a, glow=True)
    a0, a1 = math.radians(225), math.radians(-45)              # 270° sweep, clockwise
    for v in range(0, vmax + 1, 5 if vmax <= 40 else 10):
        th = a0 + (a1 - a0) * v / vmax
        r0 = R * (0.82 if v % 10 == 0 else 0.88)
        c.line((cx + r0 * math.cos(th), cy - r0 * math.sin(th)), (cx + R * 0.95 * math.cos(th), cy - R * 0.95 * math.sin(th)),
               INK2, 2, a)
        if v % 10 == 0:
            c.text((cx + R * 0.68 * math.cos(th), cy - R * 0.68 * math.sin(th)), str(v), int(R * 0.11), INK2, a, anchor="mm")
    if ref is not None:
        th = a0 + (a1 - a0) * ref / vmax
        c.line((cx + R * 0.7 * math.cos(th), cy - R * 0.7 * math.sin(th)), (cx + R * 1.08 * math.cos(th), cy - R * 1.08 * math.sin(th)),
               GREY, 5, a)
        c.text((cx + R * 1.2 * math.cos(th), cy - R * 1.2 * math.sin(th)), ref_label, int(R * 0.1), GREY, a, anchor="mm")
    th = a0 + (a1 - a0) * min(value, vmax) / vmax
    c.line((cx, cy), (cx + R * 0.86 * math.cos(th), cy - R * 0.86 * math.sin(th)), color, 6 if not big else 10, a, glow=True)
    c.circle((cx, cy), R * 0.06, fill=color, a=a)
    c.text((cx, cy + R * 0.42), f"{value:.0f} g", int(R * 0.2), INK, a, anchor="mm", weight_glow=True)
    if label:
        c.text((cx, cy + R + 50), label, 30, INK, a, anchor="mm")


@shot("B8_05")
def g_gauges(t, dur, W, H):
    c = Canvas(W, H)
    a = fade(t, 0.0, dur, dur, 0.3)
    stage_bg(c, t, shake=3.0 * ease(seg(t, 3.0, 5.5)))
    w = 8 * ease_out(seg(t, 0.8, 2.4))
    r = 32 * ease(seg(t, 2.6, 5.6)) ** 1.4
    gauge(c, 600, 500, 260, w, 40, a, label="晶圆台")
    gauge(c, 1320, 500, 260, r, 40, a, ref=15, ref_label="NXE 掩模台 >15 g", label="掩模台（High-NA）")
    c.text((960, 1010), "F15b", 18, INK2, a, anchor="mm")
    return c.finish(glow_radius=8, glow_gain=0.8)


@shot("B8_06")
def g_slam(t, dur, W, H):
    c = Canvas(W, H)
    a = fade(t, 0.0, dur, dur, 0.2)
    hit = 0.9
    v = 32 * ease(seg(t, 0.0, hit)) ** 2.2
    after = t >= hit
    shake = 22 if hit <= t < hit + 2 / 24 else 0
    stage_bg(c, t, shake=shake)
    flash = 0.5 + 0.5 * math.sin(t * 30) if after else 0
    ring = tuple(int(CYAN[i] + (ORANGE[i] - CYAN[i]) * (1 if after else 0)) for i in range(3))
    zoom = 1 + 0.25 * ease(seg(t, 0.0, hit))
    gauge(c, 960 + shake, 540, 380 * zoom, v, 40, a, color=ORANGE if after else CYAN, ring_col=ring, big=True)
    if after:
        c.circle((960, 540), 380 * zoom * 1.04, outline=ORANGE, width=6, a=a * flash, glow=True)
    big = ease(seg(t, hit + 0.05, hit + 0.2)) * (1 - ease(seg(t, hit + 0.7, hit + 0.9)))
    if big > 0:
        c.rect((0, 0, 1920, 1080), fill=(10, 8, 6), a=a * big * 0.75)
        c.text((960, 540), "32 g", 300, (255, 196, 150), a * big, anchor="mm", weight_glow=True)
    return c.finish(glow_radius=12, glow_gain=1.0 + flash * 0.5)


# ---- picometre stillness -------------------------------------------------------------------
def mask_bg(c, t, seed=3):
    rnd = random.Random(seed)
    k = c.k
    bg = Image.new("RGB", (c.W, c.H), (12, 14, 18))
    d = ImageDraw.Draw(bg)
    for i in range(22):
        y = int((40 + i * 48) * k)
        d.rectangle((int(rnd.uniform(0, 300) * k), y, int(rnd.uniform(1400, 1920) * k), y + int(18 * k)), fill=(46, 50, 62))
    bg = bg.filter(ImageFilter.GaussianBlur(10 * k))
    c.img.paste(bg, (0, 0))


@shot("B8_09")
def pm_still(t, dur, W, H):
    c = Canvas(W, H)
    a = fade(t, 0.0, dur, dur, 0.3)
    mask_bg(c, t)
    sx = -200 + 2400 * ((t / 2.2) % 1.0)                          # cyan scan line over the mask
    c.line((sx, 0), (sx, 700), CYAN, 3, a * 0.8, glow=True)
    c.rect((80, 700, 1840, 1040), fill=(6, 8, 12), a=a * 0.8, radius=10)
    rnd = random.Random(int(t * 24))
    draw = ease(seg(t, 0.3, dur - 0.4))
    xs = [100 + 1700 * i / 240 for i in range(int(240 * draw))]
    prev = None
    rn = random.Random(5)
    vals = [math.sin(i * 0.31) * 0.6 + rn.uniform(-0.4, 0.4) for i in range(241)]
    for i, x in enumerate(xs):
        y = 790 - 60 * vals[i]
        if prev:
            c.line(prev, (x, y), ORANGE, 2, a, glow=True)
        prev = (x, y)
    c.text((110, 720), "推力（N）", 22, ORANGE, a)
    prev = None
    rn = random.Random(7)
    for i, x in enumerate(xs):
        y = 960 - 2.0 * rn.uniform(-1, 1)
        if prev:
            c.line(prev, (x, y), CYAN, 2, a, glow=True)
        prev = (x, y)
    c.line((100, 960), (1800, 960), INK2, 1, a * 0.5)
    c.text((110, 880), "掩模位移（pm）", 22, CYAN, a)
    c.text((1830, 940), "+5 pm", 16, INK2, a, anchor="rm")
    c.text((1830, 990), "−5 pm", 16, INK2, a, anchor="rm")
    c.text((1830, 960), "0", 16, INK2, a, anchor="rm")
    c.text((960, 70), "掩模位移/变形 ≤ 几 pm（F41 · 示意曲线）", 28, INK, a * ease(seg(t, 1.0, 1.6)), anchor="mm")
    return c.finish(glow_radius=6, glow_gain=0.7)


# ---- SEM/TEM: lattice, ruler, hair ------------------------------------------------------------
def tem_lattice(Wpx, Hpx, spacing_px, ox=0.0, oy=0.0, seed=2):
    """Grey TEM-like silicon lattice ([110] dumbbells) with grain."""
    im = Image.new("L", (Wpx, Hpx), 48)
    d = ImageDraw.Draw(im)
    s = spacing_px
    r = s * 0.28
    nx, ny = int(Wpx / s) + 3, int(Hpx / (s * 0.82)) + 3
    for j in range(-1, ny):
        for i in range(-1, nx):
            x = ox % s + i * s + (j % 2) * s / 2
            y = oy % (s * 0.82) + j * s * 0.82
            for dx in (-0.16 * s, 0.16 * s):
                d.ellipse((x + dx - r, y - r, x + dx + r, y + r), fill=168)
    im = im.filter(ImageFilter.GaussianBlur(max(1.0, s * 0.08)))
    noise = Image.effect_noise((Wpx, Hpx), 34)
    return Image.blend(im, noise, 0.22).convert("RGB")


def si_ruler_icon(c, x, y, a):
    c.circle((x, y), 26, outline=CYAN, width=3, a=a, glow=True)
    c.circle((x + 70, y), 26, outline=CYAN, width=3, a=a, glow=True)
    c.line((x, y + 44), (x + 70, y + 44), CYAN, 2, a)
    c.text((x + 35, y + 72), "相邻硅原子 ≈ 235 pm", 20, CYAN, a, anchor="mm")


@shot("B8_11")
def sensor_60pm(t, dur, W, H):
    c = Canvas(W, H)
    a = fade(t, 0.0, dur, dur, 0.3)
    z = ease(seg(t, 0.2, 3.2))
    # 0 -> 1: a cyan grating (sensor scale) dissolves into the lattice as we zoom ~10^6 x
    spacing = 30 + 330 * z                                         # px per 235 pm at the end
    lat = tem_lattice(W, H, spacing * c.k, ox=W * 0.5, oy=H * 0.5)
    g = Image.new("RGB", (W, H), (6, 10, 14))
    gd = ImageDraw.Draw(g)
    pitch = (14 + 900 * z ** 3) * c.k
    x = 0.0
    while x < W:
        gd.rectangle((x, 0, x + pitch * 0.45, H), fill=(30, 140, 160))
        x += pitch
    mix = ease(seg(t, 1.0, 2.6))
    c.img = Image.blend(g, lat, mix)
    c.d = ImageDraw.Draw(c.img, "RGBA")
    c.g = ImageDraw.Draw(c.glow)
    bar = ease(seg(t, 3.2, 3.8))
    if bar > 0:
        s = spacing
        L = s * 60 / 235
        ax, ay = 960 + s * 0.16, 540
        c.line((ax - L / 2, ay + s * 0.42), (ax + L / 2, ay + s * 0.42), CYAN, 6, a * bar, glow=True)
        c.text((ax, ay + s * 0.42 + 40), "60 pm", 34, CYAN, a * bar, anchor="mm", weight_glow=True)
        c.text((960, 120), "传感器精度 ≈ 60 pm：比一个硅原子还小", 34, INK, a * bar, anchor="mm")
    si_ruler_icon(c, 1700, 900, a * ease(seg(t, 3.6, 4.2)))
    c.text((80, 1030), f"放大 ×{int(10 ** (2 + 5 * z)):,}", 20, INK2, a, anchor="lm")
    c.text((1880, 1030), "TEM 风格示意 · F42 · F60", 18, INK2, a, anchor="rm")
    return c.finish(glow_radius=8, glow_gain=0.8, vignette=True)


def hair_sem(Wpx, Hpx, k, seed=9):
    rnd = random.Random(seed)
    im = Image.new("L", (Wpx, Hpx), 40)
    d = ImageDraw.Draw(im)
    # wafer surface with an alignment cross under the hair
    for i in range(0, Wpx, int(60 * k)):
        d.line((i, 0, i, Hpx), fill=46)
    cx, cy = Wpx * 0.5, Hpx * 0.5
    d.rectangle((cx - 300 * k, cy - 18 * k, cx + 300 * k, cy + 18 * k), fill=110)
    d.rectangle((cx - 18 * k, cy - 300 * k, cx + 18 * k, cy + 300 * k), fill=110)
    # the hair: a thick diagonal band with overlapping cuticle scales
    w = 230 * k                                                   # 80 µm in this framing
    ang = math.radians(-18)
    ux, uy = math.cos(ang), math.sin(ang)
    nx_, ny_ = -uy, ux
    L = 2400 * k
    poly = [(cx - ux * L + nx_ * w / 2, cy - uy * L + ny_ * w / 2), (cx + ux * L + nx_ * w / 2, cy + uy * L + ny_ * w / 2),
            (cx + ux * L - nx_ * w / 2, cy + uy * L - ny_ * w / 2), (cx - ux * L - nx_ * w / 2, cy - uy * L - ny_ * w / 2)]
    d.polygon(poly, fill=150)
    step = 46 * k
    for i in range(-60, 60):
        px = cx + ux * i * step
        py = cy + uy * i * step
        for j in range(-2, 3):
            ox = px + nx_ * j * w * 0.2 + rnd.uniform(-4, 4) * k
            oy = py + ny_ * j * w * 0.2
            d.arc((ox - 30 * k, oy - 30 * k, ox + 30 * k, oy + 30 * k), 100, 250, fill=210, width=max(1, int(3 * k)))
    d.line(poly[:2], fill=225, width=max(1, int(5 * k)))
    d.line(poly[2:], fill=225, width=max(1, int(5 * k)))
    im = im.filter(ImageFilter.GaussianBlur(1.4 * k))
    return Image.blend(im, Image.effect_noise((Wpx, Hpx), 30), 0.2).convert("RGB")


@shot("B8_12")
def hair_80um(t, dur, W, H):
    c = Canvas(W, H)
    a = fade(t, 0.0, dur, dur, 0.3)
    out = ease(seg(t, 0.0, 2.4))                                   # zoom out from atoms through decades
    if out < 1:
        lat = tem_lattice(W, H, max(4.0, 360 * (1 - out) ** 3) * c.k + 2, ox=W * 0.5, oy=H * 0.5)
        c.img = lat
    hair = hair_sem(W, H, c.k)
    hm = ease(seg(t, 1.6, 2.6))
    c.img = Image.blend(c.img, hair, hm) if out < 1 else hair
    c.d = ImageDraw.Draw(c.img, "RGBA")
    c.g = ImageDraw.Draw(c.glow)
    c.text((80, 1030), f"放大 ×{int(10 ** (7 - 5 * out)):,}", 20, INK2, a, anchor="lm")
    ring = ease(seg(t, 2.8, 3.6))
    if ring > 0:
        c.circle((960, 540), 115, outline=CYAN, width=4, a=a * ring, glow=True)
        c.text((960, 120), "初始定位 ≈ 80 μm：约一根头发丝", 34, INK, a * ring, anchor="mm")
        c.rect((80, 960, 310, 970), fill=INK, a=a * ring)
        c.text((195, 935), "80 μm", 22, INK, a * ring, anchor="mm")
    c.text((1880, 1030), "SEM 风格示意 · F44", 18, INK2, a, anchor="rm")
    return c.finish(glow_radius=8, glow_gain=0.8)


# ---- 1000+ overlay marks -----------------------------------------------------------------------
def wafer_plate(c, cx, cy, R, a):
    c.circle((cx, cy), R, fill=(48, 50, 58), outline=(120, 124, 140), width=2, a=a)
    for (x0, y0, fw, fh) in b6._fields(cx, cy, R):
        c.rect((x0 + 2, y0 + 2, x0 + fw - 2, y0 + fh - 2), fill=(62, 64, 76), a=a)


@shot("B8_13")
def overlay_marks(t, dur, W, H):
    c = Canvas(W, H)
    a = fade(t, 0.0, dur, dur, 0.3)
    zoom = 1 + 5 * ease(seg(t, dur - 1.6, dur - 0.2)) ** 2
    cx, cy, R = 960, 540, 470
    def Z(p):  # noqa: E306
        return (cx + (p[0] - cx) * zoom, cy + (p[1] - cy) * zoom)
    wafer_plate(c, cx, cy, R * zoom, a) if zoom < 1.01 else c.circle((cx, cy), R * zoom, fill=(48, 50, 58), a=a)
    rnd = random.Random(13)
    marks = []
    while len(marks) < 1040:
        x, y = rnd.uniform(cx - R, cx + R), rnd.uniform(cy - R, cy + R)
        if math.hypot(x - cx, y - cy) < R * 0.96:
            marks.append((x, y))
    marks.sort(key=lambda p: (round((p[1] - cy) / 40), p[0] if round((p[1] - cy) / 40) % 2 else -p[0]))
    prog = ease(seg(t, 0.4, dur - 1.8))
    n = int(len(marks) * prog)
    for i, p in enumerate(marks):
        x, y = Z(p)
        if not (-20 < x < 1940 and -20 < y < 1100):
            continue
        col = CYAN if i < n else (90, 94, 108)
        s = 5 * min(zoom, 2)
        c.line((x - s, y), (x + s, y), col, 1, a * (0.9 if i < n else 0.5))
        c.line((x, y - s), (x, y + s), col, 1, a * (0.9 if i < n else 0.5))
    if 0 < n < len(marks):
        x, y = Z(marks[n])
        c.circle((x, y), 10, outline=CYAN, width=2, a=a, glow=True)
    err = 115 * (1 - prog) ** 2 + 2
    c.circle((cx, cy), err * zoom ** 0.3, outline=CYAN, width=3, a=a, glow=True)
    c.text((1880, 140), f"已读取套刻标记 {n:,}", 30, INK, a, anchor="ra")
    c.text((1880, 190), "误差：头发丝 → 亚纳米", 24, INK2, a, anchor="ra")
    c.text((1880, 1030), "F44 · 示意", 18, INK2, a, anchor="rm")
    return c.finish(glow_radius=8, glow_gain=0.9)


# ---- 96 fields x 220 wafers ----------------------------------------------------------------
@shot("B8_17")
def throughput(t, dur, W, H):
    c = Canvas(W, H)
    a = fade(t, 0.0, dur, dur, 0.3)
    cx, cy, R = 640, 520, 400
    c.circle((cx, cy), R, fill=(26, 30, 40), outline=INK2, width=2, a=a)
    fields = b6._fields(cx, cy, R, 60 * R / 430, 80 * R / 430)
    N = len(fields)
    p = ease(seg(t, 0.4, 3.0))
    lit = int(N * p)
    for k, (x0, y0, fw, fh) in enumerate(fields):
        on = k < lit
        flash = max(0.0, 1 - (p * N - k) / 4) if on else 0
        c.rect((x0 + 2, y0 + 2, x0 + fw - 2, y0 + fh - 2),
               fill=(int(60 + 150 * flash), int(50 + 110 * flash), int(110 + 140 * flash)) if on else None,
               outline=VIOLET if on else (54, 60, 76), width=1, a=a)
    c.text((cx, cy + R + 50), f"{lit} 个曝光场 / 片", 30, INK, a, anchor="mm")
    stack = int(220 * ease(seg(t, 2.6, 5.4)))
    for i in range(min(stack, 220)):                              # a stack of wafer icons
        y = 900 - i * 3.2
        c.d.ellipse((c.px(1360), c.px(y - 14), c.px(1600), c.px(y + 14)), fill=(70 + (i % 2) * 14, 74, 96, int(255 * a)),
                    outline=(130, 136, 160, int(255 * a)))
    c.text((1480, 900 - 220 * 3.2 - 60), f"{stack} 片 / 小时", 34, INK, a, anchor="mm")
    cnt = int(21120 * ease(seg(t, 4.6, 6.6)))
    c.text((960, 1010), f"≈ {cnt:,} 次曝光 / 小时（推算 · F45）", 34, CYAN, a * ease(seg(t, 4.4, 4.8)), anchor="mm",
           weight_glow=True)
    return c.finish(glow_radius=8, glow_gain=0.7)


# ---- energy metronome --------------------------------------------------------------------------
@shot("B8_18")
def metronome(t, dur, W, H):
    c = Canvas(W, H, bg=(0, 0, 0))
    a = fade(t, 0.0, dur, dur, 0.3)
    cx, cy, R = 960, 540, 430
    rot = math.radians(10) * t / dur
    def P(x, y):  # noqa: E306
        dx, dy = x - cx, y - cy
        return (cx + dx * math.cos(rot) - dy * math.sin(rot), cy + dx * math.sin(rot) + dy * math.cos(rot))
    per = 0.8                                                    # one wafer every 0.8 s
    wi = int(t / per)
    tl = (t % per) / per
    slide = 0.0
    if tl > 0.9:
        slide = ease((tl - 0.9) / 0.1)
    off = -2200 * slide
    fields = b6._fields(cx, cy, R)
    N = len(fields)
    lit = int(N * min(1.0, tl / 0.88))
    c.d.ellipse((c.px(cx - R + off), c.px(cy - R), c.px(cx + R + off), c.px(cy + R)), fill=(10, 10, 16, int(255 * a)),
                outline=(40, 40, 60, int(255 * a)))
    for k, (x0, y0, fw, fh) in enumerate(fields):
        if k >= lit:
            continue
        age = (lit - k) / 14
        glow = max(0.18, 1 - age)
        pts = [P(x0 + 3 + off, y0 + 3), P(x0 + fw - 3 + off, y0 + 3), P(x0 + fw - 3 + off, y0 + fh - 3), P(x0 + 3 + off, y0 + fh - 3)]
        col = (int(150 * glow + 20), int(110 * glow + 10), int(255 * glow))
        c.d.polygon([(c.px(x), c.px(y)) for x, y in pts], fill=(*col, int(255 * a)))
        c.g.polygon([(c.px(x), c.px(y)) for x, y in pts], fill=tuple(int(v * a * glow) for v in col))
    if lit < N:
        x0, y0, fw, fh = fields[lit]
        p0, p1 = P(x0 + fw / 2 + off, y0 - 6), P(x0 + fw / 2 + off, y0 + fh + 6)
        c.line(p0, p1, (230, 210, 255), 6, a, glow=True)
    c.text((1700, 980), f"第 {wi + 1} 片", 26, INK2, a, anchor="mm")
    return c.finish(glow_radius=14, glow_gain=1.2 + 0.25 * min(wi, 4))


# ---- 31 TB a week ------------------------------------------------------------------------------
def hubble(c, x, y, s, a):
    c.rect((x - 40 * s, y - 14 * s, x + 40 * s, y + 14 * s), fill=(200, 204, 214), a=a, radius=6 * s)
    c.rect((x - 26 * s, y - 52 * s, x + 26 * s, y - 20 * s), fill=(60, 110, 200), a=a)
    c.rect((x - 26 * s, y + 20 * s, x + 26 * s, y + 52 * s), fill=(60, 110, 200), a=a)
    c.circle((x + 44 * s, y), 10 * s, fill=(40, 44, 56), a=a)


@shot("B8_19")
def data_31tb(t, dur, W, H):
    c = Canvas(W, H)
    a = fade(t, 0.0, dur, dur, 0.3)
    pan = 700 * ease(seg(t, 1.6, 5.0))                           # tilt down from the falls to the base
    rnd = random.Random(int(t * 12))
    colx, base = 820, 1500 - pan
    h_col = 900 * ease(seg(t, 0.6, 7.0))
    rs = random.Random(4)
    for i in range(260):                                          # falling bits
        x = colx + rs.uniform(-110, 110)
        sp = rs.uniform(500, 900)
        y = ((t * sp + rs.uniform(0, 1500)) % 1500) - 200 - pan
        if y > base - h_col:
            continue
        c.text((x, y), rs.choice("01"), 20, CYAN, a * 0.85)
    c.rect((colx - 120, base - h_col, colx + 120, base), fill=(30, 140, 160), a=a * 0.9, glow=True)
    hub = h_col / 3
    c.rect((colx + 330, base - hub, colx + 530, base), fill=(90, 96, 120), a=a * 0.9)
    hubble(c, colx + 430, base - hub - 90, 0.9, a)
    lab = ease(seg(t, 5.0, 5.8))
    c.text((colx, base - h_col - 60), "传感器数据：每周最多 31 TB", 34, CYAN, a * lab, anchor="mm", weight_glow=True)
    c.text((colx + 430, base - hub - 190), "哈勃望远镜一年", 26, INK, a * lab, anchor="mm")
    c.text((colx + 430, base + 50), "× 3 = 左边这一根", 26, INK2, a * lab, anchor="mm")
    c.text((960, 1030), "F46", 18, INK2, a, anchor="mm")
    return c.finish(glow_radius=8, glow_gain=0.7)


@shot("B8_20")
def data_weeks(t, dur, W, H):
    c = Canvas(W, H)
    a = fade(t, 0.0, dur, dur, 0.5)
    pull = ease(seg(t, 0.0, dur - 0.6))
    s = 1 - 0.75 * pull                                           # pull back
    base = 820
    n = 1 + int(20 * pull)
    for i in range(n):
        x = 960 + (i - n / 2) * 260 * s
        h = 900 * s * (0.35 + 0.65 * min(1.0, (n - i) / 3)) if i == n - 1 else 900 * s
        c.rect((x - 110 * s, base - h, x + 110 * s, base), fill=(30, 140, 160), a=a * 0.85, glow=True)
    hubble(c, 960 - n / 2 * 260 * s - 220 * s, base - 40 * s, max(0.08, s * 0.5), a)
    c.text((960, 960), "31 TB / 周", 40, CYAN, a, anchor="mm", weight_glow=True)
    return c.finish(glow_radius=8, glow_gain=0.7)
