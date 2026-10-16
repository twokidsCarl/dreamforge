"""B4 2D shots: Bragg stacking (F8), the Germany-sized mirror (F9), tilt blueprint (F30),
High-NA mirror size/weight/time (F31), light ledger 100 W -> 1 W (F33), the "1%" card."""
import json
import math
import os

from mograph import (BLUE_BG, CYAN, INK, INK2, LINE, ORANGE, VIOLET, Canvas, ease, ease_out, fade, seg,
                     shot)

HERE = os.path.dirname(__file__)


@shot("B4_03")
def bragg(t, dur, W, H):
    c = Canvas(W, H)
    a = fade(t, 0.0, dur, dur, 0.3)
    n = 14
    top, gap = 330, 34
    for k in range(n):                                  # glowing layer boundaries
        y = top + k * gap
        col = (120, 110, 160) if k % 2 == 0 else (80, 84, 110)
        c.line((260, y), (1660, y), col, 2, a * 0.9)
    c.text((260, top - 40), "钼 / 硅 层界面", 24, INK2, a)
    # incoming wave (angled), wavelets peeling off at each interface, summing into one reflected beam
    inc = ease_out(seg(t, 0.4, 2.0))
    x0, y0 = 360, 140
    ang = math.radians(28)
    hit_x = 720
    for k in range(int(n * inc)):
        y = top + k * gap
        x = hit_x + (y - top) * math.tan(ang)
        c.line((x0 + (x - x0) * 0, y0), (x, y), VIOLET, 3, a * 0.5)
        # reflected wavelet
        r = ease_out(seg(t, 1.2 + 0.18 * k, 2.4 + 0.18 * k))
        rx = x + 420 * r
        ry = y - 420 * r * math.tan(math.radians(62))
        c.line((x, y), (rx, ry), VIOLET, 2, a * 0.35 * r)
    # single-layer readout, then the sum
    s1 = ease(seg(t, 1.6, 2.4))
    c.text((1180, 230), "单层 ≈ 1%", 36, INK, a * s1 * (1 - ease(seg(t, 5.0, 5.6))))
    sm = ease(seg(t, 5.4, 6.8))
    c.line((900, 300), (1500, -40), (230, 210, 255), 10, a * sm, glow=True)
    c.text((1180, 230), "叠加后 最高约 70%", 44, INK, a * sm, weight_glow=True)
    c.text((960, 1010), "每层反射的弱光波步调一致、同相叠加（示意，F8）", 24, INK2, a, anchor="mm")
    return c.finish()


@shot("B4_06")
def germany(t, dur, W, H):
    c = Canvas(W, H)
    a = fade(t, 0.0, dur, dur, 0.3)
    ring = json.load(open(os.path.join(HERE, "data", "germany.json")))["lonlat"]
    lon0, lon1, lat0, lat1 = 5.8, 15.1, 47.2, 55.1
    sx, sy = 560, 780
    def P(lon, lat):  # noqa: E301
        x = 260 + (lon - lon0) / (lon1 - lon0) * sx * 1.0
        y = 120 + (lat1 - lat) / (lat1 - lat0) * sy * 0.92
        return (x, y)
    grow = ease_out(seg(t, 0.0, 1.2))
    pts = [P(*p) for p in ring]
    k = int(len(pts) * grow)
    for i in range(max(0, k - 1)):
        c.line(pts[i], pts[i + 1], CYAN, 3, a)
    if grow >= 1:
        c.line(pts[-1], pts[0], CYAN, 3, a)
    # profile line across the country and the magnified section below
    pl = ease(seg(t, 1.4, 2.2))
    yline = 520
    c.line((260, yline), (260 + 560 * pl, yline), ORANGE, 2, a)
    c.text((260, 960), "镜子放大到德国那么大", 30, INK, a * pl)
    zoom = ease(seg(t, 2.6, 5.4))
    bx0, bx1, by = 980, 1700, 600
    c.line((bx0, by), (bx1, by), INK2, 2, a * pl)
    amp = 1 + 60 * zoom ** 2
    import random
    rnd = random.Random(3)
    pts2 = [(bx0 + (bx1 - bx0) * i / 120, by - amp * 0.02 * math.sin(i * 0.31) - amp * 0.015 * rnd.uniform(-1, 1))
            for i in range(121)]
    for i in range(120):
        c.line(pts2[i], pts2[i + 1], ORANGE, 3, a * pl, glow=zoom > 0.5)
    c.text((bx1, by - 120), f"放大 ×{int(1 + 999 * zoom ** 2):,}", 26, INK2, a * pl, anchor="rm")
    lab = ease(seg(t, 5.0, 5.8))
    c.text((1340, 760), "最大偏差只有 0.1 mm", 46, INK, a * lab, anchor="mm", weight_glow=True)
    c.text((1340, 820), "（ZEISS · F9）", 24, INK2, a * lab, anchor="mm")
    return c.finish()


@shot("B4_09")
def tilt(t, dur, W, H):
    c = Canvas(W, H, bg=BLUE_BG)
    c.grid(a=0.55)
    a = fade(t, 0.0, dur, dur, 0.3)
    d = ease_out(seg(t, 0.0, 1.2))
    mx, my = 620, 560
    c.line((mx - 10, my - 220), (mx + 10, my + 220), LINE, 6, a * d)          # mirror (edge-on)
    c.rect((mx - 40, my + 230, mx + 40, my + 300), outline=LINE, width=3, a=a * d)
    c.line((mx, my), (mx + 380, my), LINE, 2, a * d * 0.6)                   # normal (dashed look)
    c.text((mx + 390, my - 10), "法线", 24, LINE, a * d)
    inc = ease_out(seg(t, 1.0, 2.0))
    c.line((mx + 500, my - 260), (mx + 500 - 500 * inc, my - 260 + 260 * inc), LINE, 3, a)
    ref = ease_out(seg(t, 2.0, 3.6))
    c.line((mx, my), (mx + 1300 * ref, my + 676 * ref), LINE, 3, a)
    arc = ease(seg(t, 3.4, 4.2))
    c.text((mx + 70, my + 60), "∠", 30, LINE, a * arc)
    c.text((1280, 300), "倾角误差 < 0.1 nrad", 52, LINE, a * arc, anchor="mm", weight_glow=True)
    c.text((1280, 360), "（ZEISS · F30）", 24, LINE, a * arc, anchor="mm")
    return c.finish(glow_radius=8)


@shot("B4_12")
def mirror_scale(t, dur, W, H):
    c = Canvas(W, H)
    a = fade(t, 0.0, dur, dur, 0.3)
    g = ease_out(seg(t, 0.3, 1.8))
    c.circle((420, 430), 120, outline=INK2, width=4, a=a)
    c.text((420, 600), "上一代镜子", 28, INK2, a, anchor="mm")
    c.circle((1000, 430), 120 + 120 * g, outline=VIOLET, width=5, a=a, glow=True)
    c.text((1000, 720), "High-NA 镜子 ≈ 2× 大", 32, INK, a * g, anchor="mm")
    w = ease(seg(t, 2.0, 3.6))                                      # weights: 1 vs 10
    c.line((1350, 360), (1750, 360), INK2, 3, a * w)
    c.rect((1380, 380, 1440, 430), fill=INK2, a=a * w)
    for k in range(10):
        c.rect((1560 + (k % 5) * 36, 380 + (k // 5) * 52, 1590 + (k % 5) * 36, 425 + (k // 5) * 52),
               fill=ORANGE, a=a * w * ease(seg(t, 2.2 + 0.1 * k, 2.5 + 0.1 * k)))
    c.text((1550, 540), "重量 ≈ 10×", 32, INK, a * w, anchor="mm")
    cal = ease(seg(t, 3.8, dur - 0.6))                               # one year per mirror
    for m in range(12):
        ang = -math.pi / 2 + 2 * math.pi * m / 12
        on = cal * 12 > m
        c.circle((1550 + 120 * math.cos(ang), 800 + 120 * math.sin(ang)), 14,
                 fill=CYAN if on else None, outline=INK2, width=2, a=a * (0.4 + 0.6 * on))
    c.text((1550, 800), "约 1 年 / 面", 28, INK, a * ease(seg(t, 3.8, 4.4)), anchor="mm")
    c.text((960, 1010), "剪影示意，具体尺寸未公开（ZEISS · F31）", 22, INK2, a, anchor="mm")
    return c.finish()


@shot("B4_17")
def ledger_100w(t, dur, W, H):
    c = Canvas(W, H)
    a = fade(t, 0.0, dur, dur, 0.3)
    x, w, top, bot = 900, 120, 180, 900
    c.rect((x, top, x + w, bot), outline=INK2, width=3, a=a, radius=8)
    drop = ease(seg(t, 0.6, 3.4))
    level = top + (bot - top - 12) * (1 - (1 - drop) ** 0.4) if drop > 0 else top
    level = top + (bot - top - 12) * drop
    c.rect((x + 6, level, x + w - 6, bot - 6), fill=VIOLET, a=a * 0.8, glow=True, radius=6)
    c.text((x - 40, top + 10), "进入扫描仪 100 W", 40, INK, a, anchor="rm")
    c.text((x - 40, bot - 20), "到晶圆 ≈ 1 W", 44, INK, a * ease(seg(t, 3.0, 3.8)), anchor="rm",
           weight_glow=True)
    c.text((x + w + 40, bot - 20), "约 10 面反射镜之后（F33）", 26, INK2, a * ease(seg(t, 3.0, 3.8)), anchor="lm")
    return c.finish()


@shot("B4_18")
def one_percent(t, dur, W, H):
    c = Canvas(W, H)
    a = fade(t, 0.0, dur, dur, 0.4)
    flick = 1 - 0.35 * max(0.0, math.sin((t - 2.0) * 9)) * (1.8 < t < 2.4)
    c.text((960, 540), "1%", 360, (225, 214, 255), a * flick, anchor="mm", weight_glow=True)
    return c.finish(glow_radius=26, glow_gain=1.4)
