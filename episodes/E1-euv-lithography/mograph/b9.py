"""B9 2D shots: the light ledger's last page (F33, F48, F6, F47), photon energy 92 eV vs 6.4 eV (F47),
same dose -> 1/14 the photons, stochastic defects under the SEM (F59), 600 W -> 1000 W (F4c, reported),
and the closing "20 photons / nm²" card."""
import math
import random

from PIL import Image, ImageDraw, ImageFilter

from mograph import (CYAN, INK, INK2, ORANGE, VIOLET, Canvas, ease, ease_out, fade, font, seg, shot)

DUV = (190, 70, 110)
RED = (240, 72, 72)

# the ledger's stages, top to bottom (labels only; heights are illustrative, not to scale)
LEDGER = [("电力", "兆瓦量级"), ("驱动激光", "最高 40 kW"), ("EUV 产生", "几百瓦"),
          ("进入扫描仪", "约 100 W"), ("约 10 面反射镜", "每面损失三成以上"), ("到达晶圆", "约 1 W · 约 1%")]


@shot("B9_01")
def ledger_last(t, dur, W, H):
    c = Canvas(W, H)
    a = fade(t, 0.0, dur, dur, 0.3)
    slide = ease(seg(t, 0.0, 1.2))
    x = 1700 - (1700 - 900) * slide                                # from its right-hand slot to centre
    w = 60 + 60 * slide
    top, bot = 140, 940
    n = len(LEDGER)
    seg_h = (bot - top) / n
    c.rect((x, top, x + w, bot), outline=INK2, width=2, a=a, radius=8)
    for k, (name, val) in enumerate(LEDGER):
        y0 = top + k * seg_h
        last = k == n - 1
        lit = last or t < 1.4 + 0.35 * k
        if last:
            frac = 0.18                                            # the last little bit of sand
            c.rect((x + 6, y0 + seg_h * (1 - frac), x + w - 6, y0 + seg_h - 6), fill=VIOLET, a=a, glow=True, radius=4)
        else:
            col = VIOLET if lit else (40, 38, 56)
            c.rect((x + 6, y0 + 6, x + w - 6, y0 + seg_h - 6), fill=col, a=a * (0.85 if lit else 0.9), radius=4)
        c.line((x + w + 10, y0 + seg_h / 2), (x + w + 40, y0 + seg_h / 2), INK2, 1, a * slide)
        c.text((x + w + 52, y0 + seg_h / 2 - 14), name, 26, INK if last else INK2, a * slide, anchor="lm")
        c.text((x + w + 52, y0 + seg_h / 2 + 18), val, 20, VIOLET if last else INK2, a * slide, anchor="lm")
    c.text((x + w / 2, top - 50), "光的账本", 30, INK, a * slide, anchor="mm")
    c.text((960, 1010), "格子高度为示意，不按比例 · F33", 20, INK2, a, anchor="mm")
    return c.finish(glow_radius=10, glow_gain=0.9)


def _photon(c, x, y, r, col, a, core=1.0):
    for k in range(6, 0, -1):
        c.circle((x, y), r * (1 + k * 0.5), fill=col, a=a * 0.06 * core)
    c.circle((x, y), r, fill=tuple(min(255, int(v * 1.2)) for v in col), a=a, glow=True)


@shot("B9_02")
def photon_energy(t, dur, W, H):
    c = Canvas(W, H, bg=(0, 0, 0))
    a = fade(t, 0.0, dur, dur, 0.3)
    fl = 8 * math.sin(t * 1.6)
    on = ease(seg(t, 0.2, 1.0))
    _photon(c, 600, 360 + fl, 14, DUV, a * on, core=0.7)
    _photon(c, 1320, 360 - fl, 52, (180, 140, 255), a * on, core=1.4)
    c.text((600, 480), "DUV（193 nm）", 30, INK2, a * on, anchor="mm")
    c.text((1320, 480), "EUV（13.5 nm）", 30, INK, a * on, anchor="mm")
    g = ease_out(seg(t, 1.6, 3.6))
    base = 960
    u = 30                                                         # px per 6.4 eV: bars strictly to scale
    c.rect((560, base - u * g, 640, base), fill=DUV, a=a, radius=4)
    c.rect((1280, base - u * 92 / 6.4 * g, 1360, base), fill=VIOLET, a=a, glow=True, radius=4)
    c.text((700, base - u * g - 10), f"{6.4 * g:.1f} eV", 30, INK2, a * ease(seg(t, 1.8, 2.2)), anchor="lm")
    c.text((1420, base - u * 92 / 6.4 * g - 10), f"{92 * g:.0f} eV", 40, INK, a * ease(seg(t, 1.8, 2.2)),
           anchor="lm", weight_glow=True)
    c.text((960, 620), "× 14", 72, VIOLET, a * ease(seg(t, 3.8, 4.4)), anchor="mm", weight_glow=True)
    c.text((960, 1030), "F47", 18, INK2, a, anchor="mm")
    return c.finish(glow_radius=14, glow_gain=1.1)


@shot("B9_03")
def same_dose(t, dur, W, H):
    c = Canvas(W, H)
    a = fade(t, 0.0, dur, dur, 0.3)
    for k, (x0, n, r, col, lab) in enumerate(((300, 14, 18, DUV, "DUV：14 个光子"), (1100, 1, 60, (180, 140, 255), "EUV：1 个光子"))):
        on = ease(seg(t, 0.3 + 0.8 * k, 1.1 + 0.8 * k))
        c.rect((x0, 300, x0 + 520, 820), outline=INK2, width=3, a=a, radius=12)
        c.text((x0 + 260, 260), "同样剂量", 28, INK2, a, anchor="mm")
        rs = random.Random(3)
        for i in range(n):
            if n == 1:
                px, py = x0 + 260, 560
            else:
                px, py = x0 + 70 + (i % 4) * 125, 380 + (i // 4) * 120
            _photon(c, px + rs.uniform(-10, 10), py + rs.uniform(-10, 10), r, col, a * on)
        c.text((x0 + 260, 880), lab, 32, INK, a * on, anchor="mm")
    c.text((960, 1000), "同样剂量：EUV 光子数 ≈ DUV 的 1/14（F47）", 26, INK2, a * ease(seg(t, 2.2, 2.8)), anchor="mm")
    return c.finish(glow_radius=12, glow_gain=0.9)


# ---- SEM: stochastic defects ------------------------------------------------------------------
def resist_lines(Wpx, Hpx, k, roughness, defects=True, pan=0.0, seed=5):
    rnd = random.Random(seed)
    im = Image.new("L", (Wpx, Hpx), 58)
    d = ImageDraw.Draw(im)
    pitch = 110 * k
    w = 50 * k
    n = int(Hpx / pitch) + 2
    for j in range(n):
        yc = (j + 0.5) * pitch
        top, bot = [], []
        ph = [rnd.uniform(0, 6.3) for _ in range(6)]
        for i in range(0, Wpx + 24, max(1, int(5 * k))):
            u = (i / k + pan) * 0.02
            def edge(o):  # noqa: E306  low-frequency "chewed" edge plus a little grain
                return roughness * (7 * math.sin(u * 1.0 + ph[o]) + 4 * math.sin(u * 2.7 + ph[o + 1])
                                    + 2.5 * math.sin(u * 6.1 + ph[o + 2]) + rnd.gauss(0, 0.8)) * k
            top.append((i, yc - w / 2 + edge(0)))
            bot.append((i, yc + w / 2 + edge(3)))
        d.polygon(top + bot[::-1], fill=168)
        d.line(top, fill=228, width=max(1, int(2 * k)))
        d.line(bot, fill=228, width=max(1, int(2 * k)))
    marks = []
    if defects:
        bx = int((700 - pan) * k)                                   # a break in line 2
        y2 = 2.5 * pitch
        d.rectangle((bx, y2 - w, bx + int(34 * k), y2 + w), fill=58)
        marks.append((bx + 17 * k, y2))
        bx2 = int((1500 - pan) * k)                                 # a bridge between lines 5 and 6
        y5 = 5.5 * pitch
        d.ellipse((bx2 - 20 * k, y5, bx2 + 20 * k, y5 + pitch), fill=168)
        marks.append((bx2, y5 + pitch / 2))
    im = im.filter(ImageFilter.GaussianBlur(1.3 * k))
    return Image.blend(im, Image.effect_noise((Wpx, Hpx), 32), 0.2).convert("RGB"), marks


@shot("B9_07")
def stochastic_sem(t, dur, W, H):
    c = Canvas(W, H)
    a = fade(t, 0.0, dur, dur, 0.3)
    pan = 900 * ease(seg(t, 1.6, dur - 0.8))
    im, marks = resist_lines(W, H, c.k, 1.0, pan=pan)
    scan = ease(seg(t, 0.0, 1.4))                                   # SEM scan reveal from the top
    reveal = Image.new("L", (W, H), 0)
    ImageDraw.Draw(reveal).rectangle((0, 0, W, int(H * scan)), fill=255)
    c.img = Image.composite(im, c.img, reveal)
    c.d = ImageDraw.Draw(c.img, "RGBA")
    c.g = ImageDraw.Draw(c.glow)
    if scan < 1:
        c.line((0, 1080 * scan), (1920, 1080 * scan), INK, 2, a)
    for (mx, my) in marks:
        x, y = mx / c.k, my / c.k
        if 0 < x < 1920:
            c.circle((x, y), 70, outline=INK, width=3, a=a * ease(seg(t, 2.0, 2.6)))
    c.text((1860, 60), "SEM 风格示意", 22, INK, a, anchor="ra")
    c.text((960, 1010), "线边缘粗糙 · 断线 · 桥连（F59）", 28, INK, a * ease(seg(t, 2.0, 2.6)), anchor="mm")
    c.rect((80, 960, 280, 968), fill=INK, a=a)
    return c.finish(glow_radius=6, glow_gain=0.6)


@shot("B9_08")
def more_power(t, dur, W, H):
    c = Canvas(W, H, bg=(0, 0, 0))
    a = fade(t, 0.0, dur, dur, 0.3)
    p = ease(seg(t, 1.0, dur - 1.6))
    watts = 600 + 400 * p
    k = c.k
    for side, (x0, dens, rough) in enumerate(((0, 1.0, 1.0), (960, watts / 600, 1.0 - 0.75 * p))):
        rs = random.Random(int(t * 24) + side * 1000)
        for i in range(int(40 * dens)):                              # photon rain
            x = x0 + rs.uniform(20, 940)
            y = rs.uniform(60, 560)
            c.line((x, y), (x, y + 26), (190, 150, 255), 3, a * 0.8, glow=True)
        im, _ = resist_lines(int(940 * k), int(380 * k), k, rough, defects=(side == 0 or p < 0.5), seed=5)
        c.img.paste(im, (int((x0 + 10) * k), int(600 * k)))
    c.d = ImageDraw.Draw(c.img, "RGBA")
    c.line((960, 40), (960, 1040), CYAN, 2, a)
    c.text((480, 1010), "约 600 W", 30, INK2, a, anchor="mm")
    c.text((1440, 1010), f"{watts:,.0f} W", 40, INK, a, anchor="mm", weight_glow=True)
    c.text((960, 40), "量产约 600 W → 1000 W 原理样机（F4c · 示意）", 24, INK2, a, anchor="mt")
    return c.finish(glow_radius=10, glow_gain=0.9)


# ---- the whole ledger as one page --------------------------------------------------------------
PAGE = [("电力", "兆瓦量级", "行业估算", 1.0), ("驱动激光", "最高 40 kW", "F6", 0.62),
        ("EUV 进入扫描仪", "约 100 W", "F33", 0.34), ("到达晶圆", "约 1 W · 约 1%", "F33", 0.14),
        ("每 nm²", "≈ 20 个光子", "F47 · 推算", 0.0)]


@shot("B9_09")
def ledger_page(t, dur, W, H):
    c = Canvas(W, H)
    a = fade(t, 0.0, dur, dur, 0.3)
    pan = 900 * ease(seg(t, 3.6, dur - 0.8))
    x = 140 - pan
    for k, (name, val, src, hfrac) in enumerate(PAGE):
        on = ease(seg(t, 0.4 + 0.8 * k, 1.0 + 0.8 * k))
        w = 380
        h = 600 * hfrac
        cy = 520
        if hfrac > 0:
            c.rect((x, cy - h / 2, x + w, cy + h / 2), fill=VIOLET, a=a * on * (0.35 + 0.65 * (k == 3)), glow=k == 3,
                   radius=10)
        else:
            c.circle((x + 60, cy), 10, fill=(220, 200, 255), a=a * on, glow=True)
        c.text((x + (60 if hfrac == 0 else w / 2), cy + 360), name, 30, INK, a * on, anchor="mm")
        c.text((x + (60 if hfrac == 0 else w / 2), cy + 404), val, 26, VIOLET if k >= 3 else INK2, a * on, anchor="mm")
        c.text((x + (60 if hfrac == 0 else w / 2), cy + 444), src, 18, INK2, a * on, anchor="mm")
        if k < len(PAGE) - 1:
            c.text((x + w + 50, cy), "→", 44, INK2, a * on, anchor="mm")
        x += w + 100
    c.text((960, 90), "光的账本（宽度为示意，不按比例）", 26, INK2, a, anchor="mm")
    return c.finish(glow_radius=10, glow_gain=0.9)


@shot("B9_10")
def twenty(t, dur, W, H):
    c = Canvas(W, H, bg=(0, 0, 0))
    a = fade(t, 0.0, dur, dur, 0.2)
    grow = ease_out(seg(t, 0.0, 1.0))
    close = ease(seg(t, dur - 1.1, dur - 0.6))                    # the page folds shut (12 frames)
    size = 60 + 420 * grow
    c.text((960, 500), "20", int(size), (200, 160, 255), a, anchor="mm", weight_glow=True)
    c.text((960, 500 + size * 0.55), "个光子 / nm²", 44, INK, a * ease(seg(t, 0.8, 1.3)), anchor="mm")
    out = c.finish(glow_radius=22, glow_gain=1.2)
    if close > 0:
        w = max(2, int(W * (1 - close)))
        squeezed = out.resize((w, H))
        out = Image.new("RGB", (W, H), (0, 0, 0))
        out.paste(squeezed, ((W - w) // 2, 0))
    return out
