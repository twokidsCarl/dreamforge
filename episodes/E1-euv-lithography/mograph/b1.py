"""B1 2D shots: chapter card, droplet scale, why pre-pulse, tin spectrum, light ledger.
Design space is 1920x1080; Canvas scales to the output size."""
import math
import os
import random

from PIL import Image, ImageEnhance, ImageFilter

from mograph import (BG, BLUE_BG, CYAN, INK, INK2, LINE, ORANGE, RENDERS, VIOLET, Canvas, ease, ease_out,
                     fade, seg, shot)


# ---- reusable: the light ledger ------------------------------------------------------------
LEDGER_TOP, LEDGER_H = 150, 780
P_MAX, P_MIN = 1e6, 0.3          # log scale from megawatts down to below a watt


def ledger_y(power):
    lo, hi = math.log10(P_MIN), math.log10(P_MAX)
    return LEDGER_TOP + (hi - math.log10(power)) / (hi - lo) * LEDGER_H


def draw_ledger(c, entries, reveal, x=1640, w=46, a=1.0, title="光的账本"):
    """entries: [(power_W, label, sublabel, color)] top to bottom; reveal: 0..len(entries)."""
    c.text((x + w / 2, LEDGER_TOP - 70), title, 30, INK, a, anchor="mm")
    c.rect((x, LEDGER_TOP, x + w, LEDGER_TOP + LEDGER_H), outline=INK2, width=2, a=0.5 * a, radius=6)
    for i, (pw, label, sub, col) in enumerate(entries):
        r = ease(reveal - i)
        if r <= 0:
            continue
        y = ledger_y(pw)
        top = LEDGER_TOP if i == 0 else ledger_y(entries[i - 1][0])
        c.rect((x + 4, max(LEDGER_TOP + 4, y), x + w - 4, LEDGER_TOP + LEDGER_H - 4), fill=col, a=0.55 * a * r,
               radius=4, glow=True)
        c.line((x - 14, y), (x + w + 14, y), col, 3, a * r)
        c.text((x - 28, y), label, 30, INK, a * r, anchor="rm")
        if sub:
            c.text((x - 28, y + 38), sub, 20, INK2, a * r, anchor="rm")


def _blur_bg(path, W, H, dark=0.35):
    im = Image.open(path).convert("RGB").resize((W, H), Image.LANCZOS)
    im = im.filter(ImageFilter.GaussianBlur(H / 40))
    return ImageEnhance.Brightness(im).enhance(dark)


# ---- B1_01 chapter card --------------------------------------------------------------------
@shot("B1_01")
def chapter_b1(t, dur, W, H):
    c = Canvas(W, H)
    bg = os.path.join(RENDERS, "sample_b1", "cycles", "CamNozzle", "0060.png")
    if os.path.exists(bg):
        c.img.paste(_blur_bg(bg, W, H, 0.3 + 0.1 * ease(seg(t, 0, dur))))
    a = fade(t, 0.2, dur, dur, 0.5)
    c.text((160, 470), "第一站", 34, INK2, a)
    c.text((160, 520), "光源", 120, INK, a, weight_glow=True)
    c.text((164, 680), "Light Source", 34, VIOLET, a)
    c.line((164, 650), (164 + 420 * ease_out(seg(t, 0.3, 1.4)), 650), VIOLET, 3, a, glow=True)
    draw_ledger(c, [(1e6, "电", "兆瓦量级 · 据行业估算", CYAN)], reveal=ease(seg(t, 0.8, 2.0)), a=0.9)
    return c.finish()


# ---- B1_06 droplet vs hair -----------------------------------------------------------------
@shot("B1_06")
def droplet_scale(t, dur, W, H):
    c = Canvas(W, H)
    s = 5.2                                   # px per micrometre in design space
    cx, cy = 760, 520
    a = fade(t, 0.0, dur, dur, 0.3)
    # hair cross-section (about 80 um, F44) appears behind the droplet (25 um, F3)
    hr = 40 * s * ease_out(seg(t, 0.3, 1.2))
    c.circle((cx + 360, cy), hr, fill=(58, 46, 40), outline=(150, 120, 100), width=3, a=a)
    c.text((cx + 360, cy + 40 * s + 50), "一根头发丝 ≈ 80 μm", 32, INK2, a * ease(seg(t, 0.8, 1.4)), anchor="mm")
    # the droplet: holds, then streaks off to the right
    go = ease(seg(t, 2.6, dur))
    dx = 900 * go ** 2
    for k in range(10):                      # speed lines
        if go > 0:
            yy = cy - 50 + k * 11
            c.line((cx + dx - 40 - 300 * go, yy), (cx + dx - 40, yy), INK2, 2, a * 0.5 * go)
    c.circle((cx + dx, cy), 12.5 * s, fill=(206, 210, 220), outline=INK, width=2, a=a, glow=True)
    c.text((cx, cy - 12.5 * s - 50), "锡滴 ≈ 25 μm", 36, INK, a * (1 - go), anchor="mm")
    # speedometer readout
    v = 70 * ease_out(seg(t, 2.6, dur - 0.3))
    c.text((1500, 800), f"{v:4.0f}", 120, ORANGE, a * ease(seg(t, 2.4, 2.8)), anchor="rm", weight_glow=True)
    c.text((1520, 790), "m/s", 40, INK2, a * ease(seg(t, 2.4, 2.8)), anchor="lm")
    c.text((1520, 840), "（F3）", 22, INK2, a * ease(seg(t, 2.4, 2.8)), anchor="lm")
    return c.finish()


# ---- B1_16 why pre-pulse (blueprint) -------------------------------------------------------
@shot("B1_16")
def why_prepulse(t, dur, W, H):
    c = Canvas(W, H, bg=BLUE_BG)
    c.grid(a=0.55)
    a = fade(t, 0.0, dur, dur, 0.3)
    draw = ease_out(seg(t, 0.2, 1.6))
    heat = ease(seg(t, 2.0, 4.0))
    for side, (x0, title) in enumerate(((180, "直接打锡滴"), (1000, "先拍扁，再打"))):
        c.rect((x0, 170, x0 + 740, 820), outline=LINE, width=2, a=a * draw)
        c.text((x0 + 30, 200), title, 40, LINE, a * draw)
        cx, cy = x0 + 370, 520
        # laser spot (dashed ring)
        for k in range(48):
            ang0, ang1 = 2 * math.pi * k / 48, 2 * math.pi * (k + 0.5) / 48
            r = 210
            c.line((cx + r * math.cos(ang0), cy + r * math.sin(ang0)), (cx + r * math.cos(ang1), cy + r * math.sin(ang1)),
                   ORANGE, 3, a * draw)
        c.text((cx, cy + 250), "激光光斑", 26, ORANGE, a * draw, anchor="mm")
        if side == 0:
            c.circle((cx, cy), 46, outline=LINE, width=3, a=a * draw)
            c.circle((cx, cy), 30 * heat, fill=ORANGE, a=a * heat, glow=True)
            c.text((cx, cy - 110), "只接住光斑中间一小块", 26, LINE, a * heat, anchor="mm")
        else:
            c.rect((cx - 190, cy - 24, cx + 190, cy + 24), outline=LINE, width=3, a=a * draw, radius=24)
            c.rect((cx - 186 * heat, cy - 20, cx + 186 * heat, cy + 20), fill=ORANGE, a=a * heat, glow=True, radius=20)
            c.text((cx, cy - 110), "薄盘接住整个光斑，受热均匀", 26, LINE, a * heat, anchor="mm")
    arrow = ease_out(seg(t, 4.2, 5.4))
    c.line((700, 920), (700 + 520 * arrow, 920), LINE, 3, a * arrow)
    c.text((960, 975), "更多能量 → 变成 13.5 nm 的光（示意）", 32, LINE, a * arrow, anchor="mm")
    return c.finish(glow_radius=10)


# ---- B1_18 tin spectrum (UTA) --------------------------------------------------------------
@shot("B1_18")
def tin_spectrum(t, dur, W, H):
    c = Canvas(W, H)
    a = fade(t, 0.0, dur, dur, 0.3)
    x0, x1, yb = 220, 1700, 860
    lam0, lam1 = 10.0, 18.0
    X = lambda lam: x0 + (lam - lam0) / (lam1 - lam0) * (x1 - x0)  # noqa: E731
    c.line((x0, yb), (x1, yb), INK2, 2, a)
    for lam in range(10, 19):
        c.line((X(lam), yb), (X(lam), yb + 12), INK2, 2, a)
        c.text((X(lam), yb + 40), f"{lam}", 24, INK2, a, anchor="mm")
    c.text((x1, yb + 80), "波长（nm）", 24, INK2, a, anchor="rm")
    rnd = random.Random(7)
    heights = {}
    states = list(range(8, 15))
    for i, q in enumerate(states):
        r = ease_out(seg(t, 0.6 + 0.55 * i, 1.4 + 0.55 * i))
        if r <= 0:
            continue
        shade = 0.45 + 0.55 * i / (len(states) - 1)
        col = tuple(int(v * shade) for v in VIOLET)
        centre = 13.5 + (q - 11) * 0.05            # every charge state lands near 13.5 nm
        for _ in range(170):
            lam = rnd.gauss(centre, 0.24)
            if not lam0 < lam < lam1:
                continue
            key = round(lam, 2)
            base = heights.get(key, 0)
            hgt = rnd.uniform(14, 46)
            heights[key] = base + hgt
            y_top = yb - (base + hgt) * r
            c.line((X(lam), yb - base * r), (X(lam), y_top), col, 2, a * r)
        c.text((x0 + 10, 180 + 42 * i), f"Sn{q}+", 28, tuple(min(255, int(v * 1.25)) for v in col), a * r)
    lab = ease(seg(t, 4.8, 5.6))
    c.line((X(13.5), 160), (X(13.5), yb), INK, 2, a * lab, glow=True)
    c.text((X(13.5) + 20, 170), "13.5 nm", 40, INK, a * lab, weight_glow=True)
    c.text((x1, 130), "成千上万条谱线（示意，F24）", 24, INK2, a, anchor="rm")
    return c.finish()


# ---- B1_27 light ledger: laser -> EUV ------------------------------------------------------
@shot("B1_27")
def ledger_b1(t, dur, W, H):
    c = Canvas(W, H)
    a = fade(t, 0.0, dur, dur, 0.3)
    entries = [(1e6, "电", "兆瓦量级 · 据行业估算", CYAN),
               (4e4, "激光", "几十 kW", ORANGE),
               (600, "EUV", "量产最高约 600 W · 据报道", VIOLET)]
    reveal = 1 + 2 * ease(seg(t, 0.8, 5.5))
    # centred, larger version of the ledger
    draw_ledger(c, entries, reveal, x=1000, w=70, a=a)
    # dashed extension to the 1000 W prototype
    d = ease(seg(t, 6.0, 7.5))
    y600, y1000 = ledger_y(600), ledger_y(1000)
    for k in range(6):
        y = y600 - (y600 - y1000) * k / 6
        c.line((1090, y), (1090, y - (y600 - y1000) / 12), VIOLET, 3, a * d)
    c.text((1120, y1000), "1000 W 原理样机（实验室，据报道）", 28, VIOLET, a * d, anchor="lm")
    c.text((960, 1010), "量级示意 · 对数刻度", 22, INK2, a, anchor="mm")
    return c.finish()
