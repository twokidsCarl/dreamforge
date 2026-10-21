"""B8 2D shots: g gauges (F15b), reticle-stage thrust vs picometre stillness (F41), 60 pm sensor next to the silicon
lattice (F42, F60), the 80 um hair over an alignment mark (F44), tens of alignment marks (F44), 188 fields x 185
wafers (High-NA), the slit metronome, and 31 TB a week vs Hubble (F46).

Sources: research/visual/B8B9_sources.md (S-numbers).
  thrust profile: accelerate, constant-velocity exposure, decelerate; sign alternates field to field      S1, S13
  Si viewed along [110]: dumbbells 135.8 pm apart along [001], centred cell 384.0 x 543.1 pm (rows 271.6 pm
  apart, shifted 192.0 pm); the diagonal bonds lie in the image plane and show the true 235.2 pm         S17 (NIST a)
  alignment marks are gratings next to each layer's pattern; TENS of them for wafer positioning            S6
  High-NA half field 26 x 16.5 mm; 188 half fields per wafer; EXE:5000 more than 185 wafers per hour        S2, HNA [A22]
  slit 26 mm across the field, sweeping along the 16.5 mm scan length                                     HNA [Z21] s.11
  300 mm wafer, 3 mm edge exclusion                                                                        S18
"""
import math
import os
import random
import sys

from PIL import Image, ImageDraw, ImageFilter

from mograph import (BG, CYAN, INK, INK2, ORANGE, VIOLET, Canvas, ease, ease_out, fade, seg, shot)

sys.path.insert(0, os.path.dirname(__file__))

RED = (240, 72, 72)
GREY = (120, 126, 140)


# ---- wafer field layout (High-NA half fields) ------------------------------------------------------
def _fields(cx, cy, R):
    """High-NA half fields, 26 mm (x, across the scan) x 16.5 mm (y, along the scan), on a 300 mm wafer drawn with
    radius R px: grid boundaries through the wafer centre, every field touching the 294 mm usable disc (3 mm edge
    exclusion, S18) kept. Exactly 188 fields (HNA [A22] s.14; checked numerically). Serpentine order by rows."""
    fw, fh = 26.0 / 300 * 2 * R, 16.5 / 300 * 2 * R
    Ru = R * 147.0 / 150.0
    rows = []
    for j in range(-10, 10):
        row = []
        for i in range(-7, 7):
            x0, y0 = cx + i * fw, cy + j * fh
            px, py = min(max(cx, x0), x0 + fw), min(max(cy, y0), y0 + fh)
            if math.hypot(px - cx, py - cy) < Ru:
                row.append((x0, y0, fw, fh))
        if row:
            rows.append(row if len(rows) % 2 == 0 else row[::-1])
    return [f for r in rows for f in r]


def _clip_circle(c, cx, cy, R, outside=BG):
    """Keep only what lies inside the wafer circle (edge fields overhang the edge)."""
    mask = Image.new("L", (c.W, c.H), 0)
    ImageDraw.Draw(mask).ellipse([c.px(cx - R), c.px(cy - R), c.px(cx + R), c.px(cy + R)], fill=255)
    c.img = Image.composite(c.img, Image.new("RGB", (c.W, c.H), outside), mask)
    c.glow = Image.composite(c.glow, Image.new("RGB", (c.W, c.H), (0, 0, 0)), mask)
    c.d = ImageDraw.Draw(c.img, "RGBA")
    c.g = ImageDraw.Draw(c.glow)


def _cn(n):
    """Chinese large-number wording: 3.9 亿, 2600 万, 3,400."""
    if n >= 1e8:
        return f"{n / 1e8:.1f} 亿".replace(".0 ", " ")
    if n >= 1e4:
        return f"{n / 1e4:.0f} 万"
    return f"{n:,.0f}"


# ---- shared backgrounds -----------------------------------------------------------------------
def stage_bg(c, t, shake=0.0, seed=8):
    """Dark, defocused 'real stage' plate for HUD shots: soft metal edges."""
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


def gauge(c, cx, cy, R, value, vmax, a, color=CYAN, ref=None, ref_label="", label="", ring_col=None, big=False,
          readout=True):
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
        c.text((cx + R * 1.2 * math.cos(th), cy - R * 1.2 * math.sin(th)), ref_label, max(26, int(R * 0.1)), GREY, a,
               anchor="mm")
    th = a0 + (a1 - a0) * min(value, vmax) / vmax
    c.line((cx, cy), (cx + R * 0.86 * math.cos(th), cy - R * 0.86 * math.sin(th)), color, 6 if not big else 10, a, glow=True)
    c.circle((cx, cy), R * 0.06, fill=color, a=a)
    if readout:
        c.text((cx, cy + R * 0.42), f"{value:.0f} g", int(R * 0.2), INK, a, anchor="mm", weight_glow=True)
    if label:
        c.text((cx, cy + R + 50), label, 32, INK, a, anchor="mm")


@shot("B8_05")
def g_gauges(t, dur, W, H):
    c = Canvas(W, H)
    a = fade(t, 0.0, dur, dur, 0.3)
    stage_bg(c, t, shake=3.0 * ease(seg(t, 3.0, 5.5)))
    w = 8 * ease_out(seg(t, 0.8, 2.4))
    r = 32 * ease(seg(t, 2.6, 5.6)) ** 1.4
    gauge(c, 600, 500, 260, w, 40, a, label="晶圆台（High-NA）")
    gauge(c, 1320, 500, 260, r, 40, a, ref=15, ref_label="NXE 掩模台 >15 g", label="掩模台（High-NA）")
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
    big = ease(seg(t, hit + 0.05, hit + 0.2)) * (1 - ease(seg(t, hit + 0.7, hit + 0.9)))
    # the gauge's own '32 g' readout is hidden while the full-screen number is up (no doubled 32 g)
    gauge(c, 960 + shake, 540, 380 * zoom, v, 40, a, color=ORANGE if after else CYAN, ring_col=ring, big=True,
          readout=not (hit <= t < hit + 0.95))
    if after:
        c.circle((960, 540), 380 * zoom * 1.04, outline=ORANGE, width=6, a=a * flash, glow=True)
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


def _thrust(u, n_scans=3):
    """Reticle-stage thrust over n_scans fields, u in [0, 1]: accelerate (+F), constant-velocity exposure (~0),
    decelerate (-F); the next field is scanned the other way, so its pulses have the opposite sign (S1, S13).
    Returns (value in [-1, 1], phase) with phase 'acc', 'exp', 'dec' or 'gap'."""
    P = 1.0 / n_scans
    k = min(n_scans - 1, int(u / P))
    v = (u - k * P) / P
    s = 1 if k % 2 == 0 else -1
    ea, ee, ed = 0.13, 0.75, 0.88                               # acc 0-0.13, exposure -0.75, dec -0.88, gap
    def ramp(x, x0, x1, w=0.02):  # noqa: E306
        return ease((x - x0) / w) * (1 - ease((x - x1 + w) / w))
    if v < ea:
        return s * ramp(v, 0.0, ea), "acc"
    if v < ee:
        return 0.0, "exp"
    if v < ed:
        return -s * ramp(v, ee, ed), "dec"
    return 0.0, "gap"


@shot("B8_09")
def pm_still(t, dur, W, H):
    c = Canvas(W, H)
    a = fade(t, 0.0, dur, dur, 0.3)
    mask_bg(c, t)
    sx = -200 + 2400 * ((t / 2.2) % 1.0)                          # cyan scan line over the mask
    c.line((sx, 0), (sx, 660), CYAN, 3, a * 0.8, glow=True)
    x0, x1 = 230, 1800
    c.rect((80, 640, 1840, 1050), fill=(6, 8, 12), a=a * 0.85, radius=10)
    draw = ease(seg(t, 0.3, dur - 0.4))
    n = 480
    upto = int(n * draw)
    y_f = 770
    # shaded constant-velocity (exposure) intervals
    for i in range(n):
        u = i / n
        if i < upto and _thrust(u)[1] == "exp" and _thrust((i + 1) / n)[1] != "exp":
            j = i
            while j > 0 and _thrust((j - 1) / n)[1] == "exp":
                j -= 1
            xa, xb = x0 + (x1 - x0) * j / n, x0 + (x1 - x0) * (i + 1) / n
            c.rect((xa, 668, xb, 872), fill=(30, 70, 84), a=a * 0.55)
            c.text(((xa + xb) / 2, 690), "曝光 · 匀速", 26, CYAN, a * 0.9, anchor="mm")
    prev = None
    for i in range(upto):
        u = i / n
        x = x0 + (x1 - x0) * u
        y = y_f - 78 * _thrust(u)[0]
        if prev:
            c.line(prev, (x, y), ORANGE, 3, a, glow=True)
        prev = (x, y)
    c.line((x0, y_f), (x1, y_f), INK2, 1, a * 0.4)
    c.text((x0 - 20, y_f), "推力", 28, ORANGE, a, anchor="rm")
    if upto > n * 0.05:
        c.text((x0 + (x1 - x0) * 0.022, y_f - 100), "加速", 26, ORANGE, a, anchor="mm")
    if upto > n * 0.29:
        c.text((x0 + (x1 - x0) * 0.272, y_f + 100), "减速", 26, ORANGE, a, anchor="mm")
    prev = None
    rn = random.Random(7)
    y_d = 960
    for i in range(upto):
        x = x0 + (x1 - x0) * i / n
        y = y_d - 2.0 * rn.uniform(-1, 1)
        if prev:
            c.line(prev, (x, y), CYAN, 3, a, glow=True)
        prev = (x, y)
    c.line((x0, y_d), (x1, y_d), INK2, 1, a * 0.5)
    c.text((x0 - 20, y_d), "掩模位移", 28, CYAN, a, anchor="rm")
    for lab, yy in (("+5 pm", y_d - 40), ("0", y_d), ("−5 pm", y_d + 40)):
        c.text((1830, yy), lab, 24, INK2, a, anchor="rm")
    c.text((960, 70), "掩模位移/变形 ≤ 几 pm（示意曲线）", 34, INK, a * ease(seg(t, 1.0, 1.6)), anchor="mm")
    return c.finish(glow_radius=6, glow_gain=0.7)


# ---- SEM/TEM: lattice, ruler, hair ------------------------------------------------------------
DB, CELL_X, ROW_Y, SHIFT = 135.8, 384.0, 271.6, 192.0      # Si [110] projection, pm (S17)


def tem_lattice(Wpx, Hpx, s, ox=0.0, oy=0.0):
    """Grey TEM-like silicon lattice viewed along [110], drawn at s px per pm: dumbbells of two atoms 135.8 pm apart
    (vertical, [001]), every 384.0 pm along a row; rows 271.6 pm apart, alternate rows shifted 192.0 pm. Atom blobs
    ~55 pm radius. Below ~8 px per cell the lattice is not drawn (it would alias into moire): flat grey instead."""
    base = 48
    if CELL_X * s < 8:
        im = Image.new("L", (Wpx, Hpx), base + 40)
        return Image.blend(im, Image.effect_noise((Wpx, Hpx), 34), 0.22).convert("RGB")
    im = Image.new("L", (Wpx, Hpx), base)
    d = ImageDraw.Draw(im)
    r = max(0.8, 55 * s)
    cx_, ry_ = CELL_X * s, ROW_Y * s
    j0 = int(math.floor(-oy / ry_)) - 2
    j1 = int(math.ceil((Hpx - oy) / ry_)) + 2
    for j in range(j0, j1):
        y = oy + j * ry_
        xo = ox + (SHIFT * s if j % 2 else 0.0)
        i0 = int(math.floor(-xo / cx_)) - 2
        i1 = int(math.ceil((Wpx - xo) / cx_)) + 2
        for i in range(i0, i1):
            x = xo + i * cx_
            for dy in (-DB / 2 * s, DB / 2 * s):
                d.ellipse((x - r, y + dy - r, x + r, y + dy + r), fill=170)
    im = im.filter(ImageFilter.GaussianBlur(max(1.0, 11 * s)))
    return Image.blend(im, Image.effect_noise((Wpx, Hpx), 34), 0.2).convert("RGB")


_GRAIN = {}


def surface_grain(Wpx, Hpx, zoom, seed=4):
    """Polished stage surface seen through a zoom: lapping scratches and grain (a fixed texture) magnified `zoom`
    times about the centre; fine detail is re-added at every scale so the zoom never goes flat."""
    key = (Wpx, Hpx)
    if key not in _GRAIN:
        rnd = random.Random(seed)
        im = Image.new("L", (1920, 1080), 70)
        d = ImageDraw.Draw(im)
        for _ in range(900):
            y = rnd.uniform(0, 1080)
            x = rnd.uniform(-400, 1920)
            ln = rnd.uniform(80, 900)
            d.line((x, y, x + ln, y + rnd.uniform(-12, 12)), fill=int(rnd.uniform(50, 110)), width=rnd.choice((1, 1, 2)))
        im = im.filter(ImageFilter.GaussianBlur(1.0))
        _GRAIN[key] = Image.blend(im, Image.effect_noise((1920, 1080), 40), 0.25)
    big = _GRAIN[key]
    out = None
    for octave in range(3):                                  # three nested magnifications, 30x apart
        zz = zoom / (30 ** octave)
        if zz < 1:
            continue
        zz = 1 + (zz - 1) % 29 if octave else zz
        w, h = max(2, int(1920 / zz)), max(2, int(1080 / zz))
        layer = big.crop((960 - w // 2, 540 - h // 2, 960 - w // 2 + w, 540 - h // 2 + h)).resize((Wpx, Hpx), Image.BICUBIC)
        out = layer if out is None else Image.blend(out, layer, 0.35)
    return (out or big.resize((Wpx, Hpx))).convert("RGB")


def _scrim(c, box, a):
    c.rect(box, fill=(6, 8, 12), a=a * 0.72, radius=10)


S_END_11 = 1.5                                               # px per pm at the end of B8_11 (dumbbell = 204 px)
PX_PITCH_M = 0.5 / 1920                                      # a 1920-px frame on a ~0.5 m screen, for '放大约 ×'


@shot("B8_11")
def sensor_60pm(t, dur, W, H):
    c = Canvas(W, H)
    a = fade(t, 0.0, dur, dur, 0.3)
    z = ease(seg(t, 0.2, 3.2))
    s0 = 1920 / 2.0e9                                        # frame width 2 mm at the start
    s = s0 * (S_END_11 / s0) ** z                            # px per pm (exponential zoom)
    # lattice origin: a dumbbell centred on screen at the end
    ox, oy = W / 2, H / 2
    lat = tem_lattice(W, H, s * c.k, ox=ox, oy=oy)
    grain = surface_grain(W, H, s / s0)
    mix = ease(seg(math.log10(CELL_X * s + 1e-9), math.log10(6), math.log10(40)))
    c.img = Image.blend(grain, lat, mix)
    c.d = ImageDraw.Draw(c.img, "RGBA")
    c.g = ImageDraw.Draw(c.glow)
    bar = ease(seg(t, 3.2, 3.8))
    if bar > 0:
        S = S_END_11
        # an in-plane bond: lower atom of the centre dumbbell -> upper atom of the dumbbell below-right: 235.2 pm
        p0 = (960, 540 + DB / 2 * S)
        p1 = (960 + SHIFT * S, 540 + ROW_Y * S - DB / 2 * S)
        c.line(p0, p1, CYAN, 3, a * bar)
        for p in (p0, p1):
            c.circle(p, 66 * S, outline=CYAN, width=3, a=a * bar, glow=True)
        mx, my = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2
        _scrim(c, (mx + 40, my - 30, mx + 330, my + 22), a * bar)
        c.text((mx + 52, my - 4), "相邻硅原子 235 pm", 30, CYAN, a * bar, anchor="lm", weight_glow=True)
        # the 60 pm bar on the same scale, next to the upper atom of the centre dumbbell
        L = 60 * S
        bx, by = 960 - 230, 540 - DB / 2 * S
        c.line((bx - L / 2, by), (bx + L / 2, by), ORANGE, 8, a * bar, glow=True)
        c.line((bx - L / 2, by - 14), (bx - L / 2, by + 14), ORANGE, 3, a * bar)
        c.line((bx + L / 2, by - 14), (bx + L / 2, by + 14), ORANGE, 3, a * bar)
        c.text((bx, by - 40), "60 pm", 38, ORANGE, a * bar, anchor="mm", weight_glow=True)
        _scrim(c, (590, 78, 1330, 142), a * bar)
        c.text((960, 110), "传感器精度 ≈ 60 pm：比一个硅原子还小", 38, INK, a * bar, anchor="mm")
    _scrim(c, (60, 1008, 400, 1052), a)
    _scrim(c, (1440, 1008, 1900, 1052), a)
    c.text((80, 1030), f"放大约 {_cn(s * PX_PITCH_M / 1e-12)} 倍", 26, INK2, a, anchor="lm")
    c.text((1880, 1030), "硅晶格 [110] 方向 · TEM 风格示意", 26, INK2, a, anchor="rm")
    return c.finish(glow_radius=8, glow_gain=0.8, vignette=True)


HAIR_PX_PER_UM = 230 / 80.0                                  # the 80 um hair is 230 px wide


def hair_sem(Wpx, Hpx, k, seed=9):
    """SEM-style view at 2.9 px/um: a scribe lane across the wafer carrying an alignment mark made of two line
    gratings (lines across x and across y, S6 'specially designed gratings'), the hair lying across it. Mark pitch
    and size are illustrative (not public)."""
    rnd = random.Random(seed)
    im = Image.new("L", (Wpx, Hpx), 40)
    d = ImageDraw.Draw(im)
    u = HAIR_PX_PER_UM * k
    cx, cy = Wpx * 0.5, Hpx * 0.5
    # dies above and below the scribe lane: dense fine pattern; the lane itself bare and lighter
    for y in range(0, Hpx, max(2, int(6 * k))):
        d.line((0, y, Wpx, y), fill=52 if (y // max(2, int(6 * k))) % 2 else 44)
    lane = 90 * u
    d.rectangle((0, cy - lane / 2, Wpx, cy + lane / 2), fill=78)
    # mark: two gratings side by side, 16 um pitch, 8 um lines, each 150 x 60 um
    pitch, wl = 16 * u, 8 * u
    gw, gh = 150 * u, 60 * u
    for gx, vertical in ((cx - gw - 12 * u, True), (cx + 12 * u, False)):
        x0, y0 = gx, cy - gh / 2
        d.rectangle((x0, y0, x0 + gw, y0 + gh), fill=70)
        if vertical:
            x = x0
            while x + wl <= x0 + gw + 0.5:
                d.rectangle((x, y0, x + wl, y0 + gh), fill=150)
                x += pitch
        else:
            y = y0
            while y + wl * 0.6 <= y0 + gh + 0.5:
                d.rectangle((x0, y, x0 + gw, y + wl * 0.6), fill=150)
                y += pitch * 0.6
    # the hair: a thick diagonal band with overlapping cuticle scales
    w = 80 * u
    ang = math.radians(-18)
    ux, uy = math.cos(ang), math.sin(ang)
    nx_, ny_ = -uy, ux
    hx, hy = cx + 140 * u, cy - 60 * u
    L = 2400 * k
    poly = [(hx - ux * L + nx_ * w / 2, hy - uy * L + ny_ * w / 2), (hx + ux * L + nx_ * w / 2, hy + uy * L + ny_ * w / 2),
            (hx + ux * L - nx_ * w / 2, hy + uy * L - ny_ * w / 2), (hx - ux * L - nx_ * w / 2, hy - uy * L - ny_ * w / 2)]
    d.polygon(poly, fill=150)
    step = 46 * k
    for i in range(-60, 60):
        px = hx + ux * i * step
        py = hy + uy * i * step
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
    out = ease(seg(t, 0.0, 2.6))                                   # zoom out from atoms through the decades
    s_end = HAIR_PX_PER_UM / 1e6                                   # px per pm at the hair
    s = S_END_11 * (s_end / S_END_11) ** out
    kz = s / s_end                                                 # how far the hair image is still magnified
    hair = hair_sem(W, H, c.k)
    lat = tem_lattice(W, H, s * c.k, ox=W / 2, oy=H / 2)
    if kz < 40:                                                    # zoomed hair image, then the full view
        w, h = max(2, int(W / kz)), max(2, int(H / kz))
        hz = hair.crop((W // 2 - w // 2, H // 2 - h // 2, W // 2 - w // 2 + w, H // 2 - h // 2 + h)).resize((W, H),
                                                                                                         Image.BICUBIC)
        c.img = Image.blend(lat, hz, ease(seg(math.log10(40 / kz), 0.0, 0.3)))
    else:
        c.img = lat
    c.d = ImageDraw.Draw(c.img, "RGBA")
    c.g = ImageDraw.Draw(c.glow)
    c.text((80, 1030), f"放大约 {_cn(s * PX_PITCH_M / 1e-12)} 倍", 26, INK2, a, anchor="lm")
    ring = ease(seg(t, 2.9, 3.6))
    if ring > 0:
        c.circle((960, 540), 115, outline=CYAN, width=4, a=a * ring, glow=True)
        c.text((960, 110), "初始定位 ≈ 80 μm：约一根头发丝", 38, INK, a * ring, anchor="mm")
        c.rect((80, 950, 310, 960), fill=INK, a=a * ring)
        c.text((195, 920), "80 μm", 28, INK, a * ring, anchor="mm")
        c.text((960, 540 + 140 * HAIR_PX_PER_UM / 2.9 + 20), "对准标记（光栅）", 28, INK2, a * ring, anchor="mt")
    c.text((1880, 1030), "SEM 风格示意", 26, INK2, a, anchor="rm")
    return c.finish(glow_radius=8, glow_gain=0.8)


# ---- tens of alignment marks ------------------------------------------------------------------
def wafer_plate(c, cx, cy, R, a, fields=None):
    c.circle((cx, cy), R, fill=(48, 50, 58), outline=(120, 124, 140), width=2, a=a)
    for (x0, y0, fw, fh) in fields or _fields(cx, cy, R):
        c.rect((x0 + 2, y0 + 2, x0 + fw - 2, y0 + fh - 2), fill=(68, 71, 86), a=a)


def _mark_icon(c, x, y, s, col, a):
    """A tiny alignment grating in the scribe lane: four short lines."""
    for i in range(4):
        xx = x - 1.5 * s + i * s
        c.line((xx, y - 1.6 * s), (xx, y + 1.6 * s), col, max(1, int(s * 0.45)), a)


@shot("B8_13")
def overlay_marks(t, dur, W, H):
    c = Canvas(W, H)
    a = fade(t, 0.0, dur, dur, 0.3)
    zoom = 1 + 5 * ease(seg(t, dur - 1.6, dur - 0.2)) ** 2
    cx, cy, R = 960, 540, 470
    Rz = R * zoom
    fields = _fields(cx, cy, Rz)
    wafer_plate(c, cx, cy, Rz, a, fields)
    _clip_circle(c, cx, cy, Rz)
    c.circle((cx, cy), Rz, outline=(120, 124, 140), width=2, a=a)
    # tens of alignment marks (S6): one in the scribe lane at the corner of a spread-out sample of fields
    marks = [(x0, y0) for k, (x0, y0, fw, fh) in enumerate(_fields(cx, cy, R))
             if math.hypot(x0 - cx, y0 - cy) < R * 0.9 and (k * 7) % 5 == 0]
    marks = marks[:40]
    marks.sort(key=lambda p: (round((p[1] - cy) / 60), p[0] if round((p[1] - cy) / 60) % 2 else -p[0]))
    prog = ease(seg(t, 0.4, dur - 1.8))
    n = int(len(marks) * prog)
    for i, (x, y) in enumerate(marks):
        x, y = cx + (x - cx) * zoom, cy + (y - cy) * zoom
        if not (-40 < x < 1960 and -40 < y < 1120):
            continue
        _mark_icon(c, x, y, 3.2 * min(zoom, 2.5), CYAN if i < n else (110, 114, 130), a * (0.95 if i < n else 0.6))
    if 0 < n < len(marks):
        x, y = marks[n]
        c.circle((cx + (x - cx) * zoom, cy + (y - cy) * zoom), 16, outline=CYAN, width=3, a=a, glow=True)
    err = 115 * (1 - prog) ** 2 + 2
    c.circle((cx, cy), err * zoom ** 0.3, outline=CYAN, width=3, a=a, glow=True)
    c.rect((1490, 110, 1890, 230), fill=(8, 10, 16), a=a * 0.7, radius=10)
    c.text((1870, 130), f"已读取对准标记 {n}", 34, INK, a, anchor="ra")
    c.text((1870, 182), "误差：头发丝 → 亚纳米", 28, INK2, a, anchor="ra")
    c.text((1880, 1030), "标记位置示意", 26, INK2, a, anchor="rm")
    return c.finish(glow_radius=8, glow_gain=0.9)


# ---- 188 fields x 185 wafers (High-NA EXE:5000) -------------------------------------------------
@shot("B8_17")
def throughput(t, dur, W, H):
    c = Canvas(W, H)
    a = fade(t, 0.0, dur, dur, 0.3)
    cx, cy, R = 620, 500, 400
    c.circle((cx, cy), R, fill=(26, 30, 40), a=a)
    fields = _fields(cx, cy, R)
    N = len(fields)                                               # 188
    p = ease(seg(t, 0.4, 3.0))
    lit = int(N * p)
    for k, (x0, y0, fw, fh) in enumerate(fields):
        on = k < lit
        flash = max(0.0, 1 - (p * N - k) / 6) if on else 0
        c.rect((x0 + 1.5, y0 + 1.5, x0 + fw - 1.5, y0 + fh - 1.5),
               fill=(int(60 + 150 * flash), int(50 + 110 * flash), int(110 + 140 * flash)) if on else None,
               outline=VIOLET if on else (54, 60, 76), width=1, a=a)
    _clip_circle(c, cx, cy, R)
    c.circle((cx, cy), R, outline=INK2, width=2, a=a)
    c.text((cx, cy + R + 50), f"{lit} 个曝光场 / 片（High-NA 半场）", 34, INK, a, anchor="mm")
    stack = int(185 * ease(seg(t, 2.6, 5.4)))
    for i in range(min(stack, 185)):                              # a stack of wafer icons
        y = 900 - i * 3.6
        c.d.ellipse((c.px(1360), c.px(y - 14), c.px(1600), c.px(y + 14)), fill=(70 + (i % 2) * 14, 74, 96, int(255 * a)),
                    outline=(130, 136, 160, int(255 * a)))
    c.text((1480, 900 - 185 * 3.6 - 60), f"{stack} 片以上 / 小时" if stack == 185 else f"{stack} 片 / 小时", 36, INK,
           a * ease(seg(t, 2.6, 2.9)), anchor="mm")
    cnt = int(34780 * ease(seg(t, 4.6, 6.4)))
    done = cnt >= 34780
    txt = "超过 3.4 万次曝光 / 小时（推算：188 × 185）" if done else f"≈ {cnt:,} 次曝光 / 小时"
    c.text((960, 1010), txt, 36, CYAN, a * ease(seg(t, 4.4, 4.8)), anchor="mm", weight_glow=True)
    c.text((1880, 60), "TWINSCAN EXE:5000（ASML）", 26, INK2, a, anchor="ra")
    return c.finish(glow_radius=8, glow_gain=0.7)


# ---- energy metronome --------------------------------------------------------------------------
WAFER_S = (1.6, 0.9, 0.6, 0.45, 0.45)                             # seconds per wafer: time-lapse, accelerating


@shot("B8_18")
def metronome(t, dur, W, H):
    c = Canvas(W, H, bg=(0, 0, 0))
    a = fade(t, 0.0, dur, dur, 0.3)
    cx, cy, R = 960, 540, 430
    rot = math.radians(10) * t / dur
    def P(x, y):  # noqa: E306
        dx, dy = x - cx, y - cy
        return (cx + dx * math.cos(rot) - dy * math.sin(rot), cy + dx * math.sin(rot) + dy * math.cos(rot))
    t0, wi = 0.0, 0
    while wi < len(WAFER_S) - 1 and t >= t0 + WAFER_S[wi]:
        t0 += WAFER_S[wi]
        wi += 1
    per = WAFER_S[wi] if wi < len(WAFER_S) else WAFER_S[-1]
    tl = min(1.0, (t - t0) / per)
    slide = ease((tl - 0.9) / 0.1) if tl > 0.9 else 0.0
    off = -2200 * slide
    fields = _fields(cx, cy, R)
    N = len(fields)
    litf = N * min(1.0, tl / 0.88)
    lit = int(litf)
    c.d.ellipse((c.px(cx - R + off), c.px(cy - R), c.px(cx + R + off), c.px(cy + R)), fill=(10, 10, 16, int(255 * a)))
    for k, (x0, y0, fw, fh) in enumerate(fields):
        if k >= lit:
            continue
        age = (lit - k) / 24
        glow = max(0.18, 1 - age)
        pts = [P(x0 + 2 + off, y0 + 2), P(x0 + fw - 2 + off, y0 + 2), P(x0 + fw - 2 + off, y0 + fh - 2), P(x0 + 2 + off, y0 + fh - 2)]
        col = (int(100 * glow + 30), int(62 * glow + 18), int(255 * glow))
        c.d.polygon([(c.px(x), c.px(y)) for x, y in pts], fill=(*col, int(255 * a)))
        c.g.polygon([(c.px(x), c.px(y)) for x, y in pts], fill=tuple(int(v * a * glow) for v in col))
    if lit < N:
        # the slit spans the field's 26 mm width and sweeps down its 16.5 mm scan length
        x0, y0, fw, fh = fields[lit]
        yy = y0 + fh * (litf - lit)
        p0, p1 = P(x0 - 4 + off, yy), P(x0 + fw + 4 + off, yy)
        c.line(p0, p1, (215, 195, 255), 7, a, glow=True)
    # clip to the (rotated, sliding) wafer
    _clip_circle(c, cx + off, cy, R, outside=(0, 0, 0))
    c.circle((cx + off, cy), R, outline=(46, 44, 70), width=2, a=a)
    c.text((1740, 960), f"第 {wi + 1} 片", 30, INK2, a, anchor="mm")
    c.text((1740, 1010), "加速示意", 26, INK2, a, anchor="mm")
    c.text((180, 1000), f"{min(lit, N)} / {N} 场", 30, INK2, a, anchor="lm")
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
    colx, base = 820, 1500 - pan
    h_col = 900 * ease(seg(t, 0.6, 7.0))
    rs = random.Random(4)
    for i in range(260):                                          # falling bits
        x = colx + rs.uniform(-110, 110)
        sp = rs.uniform(500, 900)
        y = ((t * sp + rs.uniform(0, 1500)) % 1500) - 200 - pan
        if y > base - h_col:
            continue
        c.text((x, y), rs.choice("01"), 22, CYAN, a * 0.85)
    c.rect((colx - 120, base - h_col, colx + 120, base), fill=(30, 140, 160), a=a * 0.9, glow=True)
    hub = h_col / 3
    c.rect((colx + 330, base - hub, colx + 530, base), fill=(90, 96, 120), a=a * 0.9)
    hubble(c, colx + 430, base - hub - 90, 0.9, a)
    lab = ease(seg(t, 5.0, 5.8))
    c.text((colx, base - h_col - 60), "传感器数据：每周最多 31 TB", 36, CYAN, a * lab, anchor="mm", weight_glow=True)
    c.text((colx + 430, base - hub - 190), "哈勃望远镜一年", 30, INK, a * lab, anchor="mm")
    c.text((colx + 430, base + 50), "× 3 = 左边这一根", 30, INK2, a * lab, anchor="mm")
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
