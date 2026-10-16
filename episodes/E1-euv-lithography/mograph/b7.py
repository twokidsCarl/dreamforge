"""B7 2D shots: 4x reduction blueprint (F11), NA and resolution NXE vs EXE (F12, F13), cones widening
and clashing (F40), anamorphic 4x/8x (F12), half fields 188 vs 96 (F52, F45), Zernike -> Tatian (F39)."""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from mograph import (BLUE_BG, CYAN, INK, INK2, LINE, ORANGE, VIOLET, Canvas, ease, ease_out, fade, seg,
                     shot)

sys.path.insert(0, os.path.dirname(__file__))
import b6  # noqa: E402  (shared wafer-field layout)

RED = (240, 72, 72)


# ---- a stylised standard-cell layout snippet (SKY130-like rectangles, not a real cell) --------
CELL = [(0, 0, 10, 1.2), (0, 8.8, 10, 10), (1.0, 2.2, 1.8, 7.8), (3.2, 2.2, 4.0, 7.8), (5.4, 2.2, 6.2, 7.8),
        (7.6, 2.2, 8.4, 7.8), (1.0, 4.6, 4.0, 5.4), (5.4, 3.4, 8.4, 4.2), (2.0, 1.2, 2.6, 2.2), (6.6, 7.8, 7.2, 8.8)]


def layout(c, x0, y0, s, a, color=LINE, width=2, progress=1.0):
    for k, (u0, v0, u1, v1) in enumerate(CELL):
        if k / len(CELL) > progress:
            break
        c.rect((x0 + u0 * s, y0 + v0 * s, x0 + u1 * s, y0 + v1 * s), outline=color, width=width, a=a)


@shot("B7_02")
def reduce4(t, dur, W, H):
    c = Canvas(W, H, bg=BLUE_BG)
    c.grid(a=0.55)
    a = fade(t, 0.0, dur, dur, 0.3)
    draw = ease_out(seg(t, 0.0, 1.4))
    c.text((960, 70), "掩模", 26, LINE, a, anchor="mm")
    layout(c, 760, 110, 40, a, progress=draw)                      # 400 px wide on the mask
    for k, (u, v) in enumerate(((0, 0), (10, 0), (0, 10), (10, 10))):   # dashed projection rays
        p0 = (760 + u * 40, 110 + v * 40)
        p1 = (910 + u * 10, 820 + v * 10)
        g = ease(seg(t, 1.2 + 0.1 * k, 2.4 + 0.1 * k))
        n = 22
        for i in range(n):
            if i % 2:
                continue
            q0 = i / n * g
            q1 = (i + 1) / n * g
            c.line((p0[0] + (p1[0] - p0[0]) * q0, p0[1] + (p1[1] - p0[1]) * q0),
                   (p0[0] + (p1[0] - p0[0]) * q1, p0[1] + (p1[1] - p0[1]) * q1), LINE, 2, a * 0.7)
    land = ease(seg(t, 2.4, 3.0))
    layout(c, 910, 820, 10, a * land, width=2)
    c.text((960, 950), "晶圆", 26, LINE, a * land, anchor="mm")
    dim = ease(seg(t, 3.0, 3.6))
    c.line((760, 540), (1160, 540), LINE, 2, a * dim)
    c.text((1180, 540), "4 份", 24, LINE, a * dim, anchor="lm")
    c.line((910, 800), (1010, 800), LINE, 2, a * dim)
    c.text((1030, 800), "1 份", 24, LINE, a * dim, anchor="lm")
    c.text((1460, 540), "缩小 4×", 64, LINE, a * dim, anchor="mm", weight_glow=True)
    c.text((960, 1030), "电路图形示意（标准单元风格，非真实版图）· F11", 20, LINE, a * 0.8, anchor="mm")
    return c.finish(glow_radius=8)


# ---- NA vs resolution -------------------------------------------------------------------------
def _cone(c, cx, top, bottom, na, a, color=VIOLET):
    h = bottom - top
    half = h * math.tan(math.asin(na)) * 0.55                      # flattened drawing scale
    c.d.polygon([(c.px(cx - half), c.px(top)), (c.px(cx + half), c.px(top)), (c.px(cx), c.px(bottom))],
                fill=(*color, int(150 * a)))
    c.g.polygon([(c.px(cx - half), c.px(top)), (c.px(cx + half), c.px(top)), (c.px(cx), c.px(bottom))],
                fill=tuple(int(v * a * 0.35) for v in color))


def _lines_panel(c, cx, y, pitch_nm, res_nm, a, wpx=560, hpx=200):
    """White lines at a given pitch; blurred into grey when the pitch is below what the optics resolve."""
    k = c.k
    Wp, Hp = int(wpx * k), int(hpx * k)
    im = Image.new("L", (Wp, Hp), 0)
    d = ImageDraw.Draw(im)
    px_per_nm = 9.0 * k
    period = pitch_nm * px_per_nm
    x = 0.0
    while x < Wp:
        d.rectangle((x, 0, x + period / 2, Hp), fill=235)
        x += period
    blur = max(0.0, (res_nm / pitch_nm) ** 3 - 0.35) * period * 0.9
    if blur > 0.3:
        im = im.filter(ImageFilter.GaussianBlur(blur))
    rgb = Image.merge("RGB", (im, im, im))
    rgb = Image.blend(Image.new("RGB", rgb.size, (8, 10, 16)), rgb, a)
    c.img.paste(rgb, (int((cx - wpx / 2) * k), int(y * k)))


@shot("B7_03")
def na_nxe(t, dur, W, H):
    c = Canvas(W, H)
    a = fade(t, 0.0, dur, dur, 0.3)
    c.line((960, 80), (960, 1000), CYAN, 1, a * 0.8)
    g = ease_out(seg(t, 0.0, 1.0))
    _cone(c, 480, 170, 560, 0.33 * g, a)
    c.text((480, 130), "NXE", 36, INK, a, anchor="mm")
    c.text((660, 360), f"NA {0.33 * g:.2f}", 40, INK, a, anchor="lm", weight_glow=True)
    _lines_panel(c, 480, 640, 26, 13, a * ease(seg(t, 1.2, 2.0)))
    c.text((480, 890), "约 13 nm 的线条 · 清晰分开", 28, INK, a * ease(seg(t, 1.6, 2.2)), anchor="mm")
    c.rect((1200, 170, 1680, 860), outline=(60, 64, 80), width=2, a=a * 0.8, radius=12)
    c.text((1440, 515), "？", 80, (70, 74, 90), a, anchor="mm")
    c.text((960, 1030), "F13", 18, INK2, a, anchor="mm")
    return c.finish(glow_radius=10, glow_gain=0.7)


@shot("B7_04")
def na_exe(t, dur, W, H):
    c = Canvas(W, H)
    a = fade(t, 0.0, dur, dur, 0.3)
    c.line((960, 80), (960, 1000), CYAN, 1, a * 0.8)
    # left: NXE, then forced down to 8 nm pitch — it blurs
    squeeze = ease(seg(t, 3.6, 5.0))
    _cone(c, 480, 170, 560, 0.33, a)
    c.text((480, 130), "NXE", 36, INK, a, anchor="mm")
    c.text((660, 360), "NA 0.33", 40, INK, a, anchor="lm")
    pitch_l = 26 - (26 - 16) * squeeze
    _lines_panel(c, 480, 640, pitch_l, 13, a)
    c.text((480, 890), "约 13 nm" if squeeze < 0.5 else "压到 8 nm → 糊成一片", 28, RED if squeeze >= 0.5 else INK,
           a, anchor="mm")
    # right: EXE lights up, NA rolls 0.33 -> 0.55, 8 nm lines stay separate
    on = ease(seg(t, 0.2, 1.0))
    roll = ease(seg(t, 0.6, 2.2))
    na = 0.33 + 0.22 * roll
    _cone(c, 1440, 170, 560, na, a * on)
    c.text((1440, 130), "High-NA EXE", 36, INK, a * on, anchor="mm")
    c.text((1660, 360), f"NA {na:.2f}", 40, INK, a * on, anchor="lm", weight_glow=True)
    _lines_panel(c, 1440, 640, 16, 8, a * ease(seg(t, 1.8, 2.6)))
    c.text((1440, 890), "约 8 nm · 依然清楚", 28, CYAN, a * ease(seg(t, 2.2, 2.8)), anchor="mm")
    c.text((960, 1030), "F12 · F13", 18, INK2, a, anchor="mm")
    return c.finish(glow_radius=10, glow_gain=0.7)


# ---- blueprint: cones widen and clash ----------------------------------------------------------
EXAG = 2.6                                     # angles drawn x2.6 (labelled 示意)


def clash(c, t, a, na, tilt_deg=6.0, hatch=0.0):
    """Mask cross-section with incident (left) and reflected (right) cones; returns overlap flag."""
    px, py, L = 960, 360, 620
    c.rect((360, py - 40, 1560, py), fill=(28, 74, 150), outline=LINE, width=3, a=a)
    c.text((380, py - 70), "掩模", 24, LINE, a)
    for k in range(0, 640, 30):
        c.line((px, py + k), (px, py + k + 16), LINE, 2, a * 0.7)
    half = math.degrees(math.asin(na / 4)) * EXAG
    tilt = tilt_deg * EXAG
    for sgn, col in ((-1, (164, 128, 255)), (1, (60, 200, 220))):       # translucent fills: incident / reflected
        th0, th1 = math.radians(tilt - half), math.radians(tilt + half)
        pts = [(px, py), (px + sgn * L * math.sin(th0), py + L * math.cos(th0)),
               (px + sgn * L * math.sin(th1), py + L * math.cos(th1))]
        c.d.polygon([(c.px(x), c.px(y)) for x, y in pts], fill=(*col, int(70 * a)))
    c.text((px - 420, py + 560), "入射光", 24, (200, 186, 255), a, anchor="mm")
    c.text((px + 420, py + 560), "反射光", 24, (150, 230, 240), a, anchor="mm")
    for sgn in (-1, 1):
        for edge in (-half, half):
            th = math.radians(tilt + edge)
            c.line((px, py), (px + sgn * L * math.sin(th), py + L * math.cos(th)), LINE, 3, a)
    overlap = half > tilt
    if overlap and hatch > 0:                  # the wedge shared by both cones, orange hatching
        w = math.radians(half - tilt)
        for k in range(1, 26):
            r = L * k / 26
            x0, x1 = px - r * math.sin(w), px + r * math.sin(w)
            y = py + r * math.cos(w)
            c.line((x0, y), (x1, y - 14), ORANGE, 3, a * hatch, glow=True)
    return overlap, half / EXAG


def _slider(c, a, na, lo=0.33, hi=0.55):
    x0, x1, y = 560, 1360, 1000
    c.line((x0, y), (x1, y), LINE, 3, a)
    p = (na - lo) / (hi - lo)
    c.circle((x0 + (x1 - x0) * p, y), 14, fill=LINE, a=a)
    c.text((x0 - 30, y), "NA", 28, LINE, a, anchor="rm")
    c.text((x0 + (x1 - x0) * p, y - 40), f"{na:.2f}", 30, LINE, a, anchor="mm")


@shot("B7_07")
def widen(t, dur, W, H):
    c = Canvas(W, H, bg=BLUE_BG)
    c.grid(a=0.55)
    a = fade(t, 0.0, dur, dur, 0.3)
    na = 0.33 + 0.16 * ease(seg(t, 1.2, dur - 0.3))
    clash(c, t, a * ease_out(seg(t, 0.0, 1.0)), na)
    _slider(c, a, na)
    c.text((960, 110), "NA ↑ → 光锥变粗（角度放大示意）", 32, LINE, a, anchor="mm")
    return c.finish(glow_radius=8)


@shot("B7_08")
def overlap(t, dur, W, H):
    dark = ease(seg(t, dur - 2.4, dur - 0.4))
    bg = tuple(int(v * (1 - dark)) for v in BLUE_BG)
    c = Canvas(W, H, bg=bg)
    c.grid(a=0.55 * (1 - dark))
    a = fade(t, 0.0, dur, dur, 0.3)
    na = 0.49 + 0.06 * ease(seg(t, 0.0, 1.4))
    blink = 0.55 + 0.45 * math.sin(t * 9) if t > 1.6 else 0.0
    clash(c, t, a, na, hatch=blink)
    _slider(c, a * (1 - dark), na)
    c.text((960, 110), "4× / 4×：入射光锥与反射光锥重叠", 34, ORANGE, a * ease(seg(t, 1.4, 2.0)), anchor="mm",
           weight_glow=True)
    return c.finish(glow_radius=8 + 10 * dark, glow_gain=1.0 + dark)


# ---- anamorphic 4x / 8x -------------------------------------------------------------------------
@shot("B7_10")
def anamorphic(t, dur, W, H):
    c = Canvas(W, H)
    a = fade(t, 0.0, dur, dur, 0.3)
    sx = 1 - 0.75 * ease(seg(t, 1.4, 2.8))                        # ÷4 across
    sy = 1 - 0.875 * ease(seg(t, 3.0, 4.6))                       # ÷8 along the scan
    zoom = 1 + 3.0 * ease(seg(t, 4.6, 5.6))                       # zoom in to see the holes are round
    cx, cy = 960, 530
    n = 5
    pitch = 90
    for i in range(n):
        for j in range(n):
            x = cx + (i - (n - 1) / 2) * pitch * sx * zoom
            y = cy + (j - (n - 1) / 2) * pitch * 2 * sy * zoom
            rx = 32 * sx * zoom
            ry = 64 * sy * zoom                                   # mask holes are 2x tall ellipses
            c.d.ellipse((c.px(x - rx), c.px(y - ry), c.px(x + rx), c.px(y + ry)), outline=(*VIOLET, int(255 * a)),
                        width=max(1, int(c.px(3))))
    ax = ease(seg(t, 1.0, 1.4))
    c.line((420, 980), (1500, 980), INK, 3, a * ax)
    c.text((1520, 980), "÷4（非扫描方向）", 30, INK, a * ax, anchor="lm")
    ay = ease(seg(t, 2.8, 3.2))
    c.line((240, 120), (240, 940), CYAN, 3, a * ay)
    c.text((260, 140), "÷8（扫描方向）", 30, CYAN, a * ay, anchor="lm")
    lab = ease(seg(t, 0.2, 0.8)) * (1 - ease(seg(t, 4.6, 5.0)))
    c.text((960, 70), "掩模上：接触孔画成拉长的椭圆", 30, INK, a * lab, anchor="mm")
    lab2 = ease(seg(t, 5.0, 5.6))
    c.text((960, 70), "晶圆上：又变回正圆", 30, CYAN, a * lab2, anchor="mm", weight_glow=True)
    c.text((960, 1040), "F12", 18, INK2, a, anchor="mm")
    return c.finish(glow_radius=8, glow_gain=0.7)


# ---- half fields: 188 vs 96 ---------------------------------------------------------------------
@shot("B7_13")
def half_fields(t, dur, W, H):
    c = Canvas(W, H)
    a = fade(t, 0.0, dur, dur, 0.3)
    # beat 1 (0-2.6 s): the mask icon stretches 2x along the scan direction
    m = 1 - ease(seg(t, 2.4, 2.8))
    st = 1 + ease(seg(t, 0.5, 1.8))
    if m > 0:
        w, h = 260, 160 * st
        c.rect((960 - w / 2, 540 - h / 2, 960 + w / 2, 540 + h / 2), fill=(40, 44, 58), outline=VIOLET, width=3,
               a=a * m)
        c.text((960 + w / 2 + 30, 540), "扫描方向 ×2", 34, INK, a * m * ease(seg(t, 1.2, 1.8)), anchor="lm")
    # beat 2 (2.8-4.4 s): a field cut in half
    f2 = ease(seg(t, 2.8, 3.2)) * (1 - ease(seg(t, 4.4, 4.8)))
    if f2 > 0:
        cut = ease(seg(t, 3.3, 3.9))
        c.rect((860, 380, 1060, 540 - 10 * cut), outline=CYAN, width=3, a=a * f2)
        c.rect((860, 540 + 10 * cut, 1060, 700), outline=CYAN, width=3, a=a * f2)
        c.line((820, 540), (820 + 280 * cut, 540), ORANGE, 3, a * f2, glow=True)
        c.text((1100, 540), "一次只曝光半个场", 34, INK, a * f2 * cut, anchor="lm")
    # beat 3 (4.8 s-): half fields strobe across the wafer, counter to 188; the NXE wafer for reference
    w3 = ease(seg(t, 4.6, 5.0))
    if w3 > 0:
        cx, cy, R = 860, 560, 430
        c.circle((cx, cy), R, fill=(26, 30, 40), outline=INK2, width=2, a=a * w3)
        fields = b6._fields(cx, cy, R, 62, 42)
        N = len(fields)
        prog = ease(seg(t, 5.2, dur - 0.8))
        lit = int(N * prog)
        for k, (x0, y0, fw, fh) in enumerate(fields):
            on = k < lit
            flash = max(0.0, 1 - (prog * N - k) / 5) if on else 0
            c.rect((x0 + 2, y0 + 2, x0 + fw - 2, y0 + fh - 2),
                   fill=(int(50 + 140 * flash), int(46 + 110 * flash), int(96 + 140 * flash)) if on else None,
                   outline=CYAN if on else (54, 60, 76), width=1, a=a * w3)
        c.text((1420, 420), "High-NA · 半场", 28, INK2, a * w3, anchor="lm")
        c.text((1420, 490), f"{lit} 次", 64, INK, a * w3, anchor="lm", weight_glow=lit == N)
        sx, sy, sr = 1600, 820, 130
        c.circle((sx, sy), sr, fill=(20, 22, 30), outline=(70, 74, 90), width=1, a=a * w3 * 0.7)
        for (x0, y0, fw, fh) in b6._fields(sx, sy, sr, 60 * sr / 430, 80 * sr / 430):
            c.rect((x0 + 1, y0 + 1, x0 + fw - 1, y0 + fh - 1), outline=(90, 94, 110), width=1, a=a * w3 * 0.7)
        c.text((sx, sy + sr + 34), "对照 NXE：96 个满场", 22, INK2, a * w3, anchor="mm")
    c.text((960, 1040), "F40 · F52 · F45", 18, INK2, a, anchor="mm")
    return c.finish(glow_radius=8, glow_gain=0.7)


# ---- Zernike -> Tatian ---------------------------------------------------------------------------
def _zmap(n, m, size, eps=0.0):
    """Wavefront map of a Zernike (eps=0) or annular, Tatian-style (eps>0) polynomial, diverging colours."""
    y, x = np.mgrid[-1:1:size * 1j, -1:1:size * 1j]
    r = np.hypot(x, y)
    th = np.arctan2(y, x)
    rr = r if eps == 0 else np.clip((r - eps) / (1 - eps), 0, 1)        # radial remap onto the annulus
    R = np.zeros_like(r)
    for k in range((n - abs(m)) // 2 + 1):
        R += ((-1) ** k * math.factorial(n - k) /
              (math.factorial(k) * math.factorial((n + abs(m)) // 2 - k) * math.factorial((n - abs(m)) // 2 - k))
              * rr ** (n - 2 * k))
    Z = R * (np.cos(m * th) if m >= 0 else np.sin(-m * th))
    mask = (r <= 1) & (r >= eps)
    v = np.clip(Z, -1, 1)
    red = np.where(v > 0, 230, 230 + v * 200)
    blu = np.where(v < 0, 240, 240 - v * 200)
    grn = 230 - np.abs(v) * 170
    rgb = np.stack([red, grn, blu], -1).astype(np.uint8)
    alpha = (mask * 255).astype(np.uint8)
    return Image.fromarray(np.dstack([rgb, alpha]), "RGBA")


Z_SET = [(2, 0), (2, 2), (3, 1), (3, 3), (4, 0), (4, 2)]


@shot("B7_16")
def tatian(t, dur, W, H):
    c = Canvas(W, H, bg=BLUE_BG)
    c.grid(a=0.55)
    a = fade(t, 0.0, dur, dur, 0.3)
    pan = 620 * ease(seg(t, 6.0, 8.0))                            # slide from old (left) to new (right)
    k = c.k
    # pupil: disc, then a hole is cut (annulus)
    hole = ease(seg(t, 1.8, 2.8))
    pcx, pcy = 360 - pan, 380
    c.circle((pcx, pcy), 170, outline=LINE, width=3, a=a)
    if hole > 0:
        c.circle((pcx, pcy), 170 * 0.3 * hole, fill=BLUE_BG, outline=LINE, width=3, a=a)
    c.text((pcx, pcy + 220), "光瞳 → 中心开孔", 26, LINE, a, anchor="mm")
    # old row: Zernike maps on the full disc, cracked and struck out once the hole appears
    size = int(150 * k)
    for i, (n, m) in enumerate(Z_SET):
        x = 640 + i * 190 - pan
        on = ease(seg(t, 0.3 + 0.12 * i, 0.9 + 0.12 * i))
        if on <= 0 or x < -200:
            continue
        im = _zmap(n, m, size)
        im.putalpha(im.getchannel("A").point(lambda v, o=on * a: int(v * o)))
        c.img.paste(im, (int((x - 75) * k), int(305 * k)), im)
        cross = ease(seg(t, 3.0 + 0.25 * i, 3.4 + 0.25 * i))
        if cross > 0:
            c.line((x - 80, 300), (x - 80 + 160 * cross, 460), LINE, 4, a)
            c.line((x + 80, 300), (x + 80 - 160 * cross, 460), LINE, 4, a)
    c.text((1000 - pan, 520), "Zernike 多项式：在圆环上不再正交", 30, LINE, a * ease(seg(t, 3.0, 3.6)), anchor="mm")
    # new row: Tatian polynomials drawn on the annular pupil
    for i, (n, m) in enumerate(Z_SET):
        x = 640 + i * 190 + 620 - pan
        on = ease(seg(t, 8.2 + 0.3 * i, 8.8 + 0.3 * i))
        if on <= 0 or x > 2100:
            continue
        im = _zmap(n, m, size, eps=0.3)
        im.putalpha(im.getchannel("A").point(lambda v, o=on * a: int(v * o)))
        c.img.paste(im, (int((x - 75) * k), int(645 * k)), im)
        c.circle((x, 720), 75, outline=LINE, width=2, a=a * on)
        c.circle((x, 720), 22.5, outline=LINE, width=2, a=a * on)
    c.text((1240, 870), "Tatian 多项式：为环形光瞳而生", 30, LINE, a * ease(seg(t, 8.4, 9.0)), anchor="mm",
           weight_glow=True)
    c.text((960, 1030), "示意 · ZEISS / ASML（F39）", 20, LINE, a * 0.8, anchor="mm")
    return c.finish(glow_radius=8)
