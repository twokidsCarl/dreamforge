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
    """Near-normal incidence on the Mo/Si stack, drawn as in ZEISS's figure (Kaiser, VLSI-TSA 2019 s.23): the beam
    comes in ~8 deg from the normal, every interface reflects a weak wavelet in the mirror direction, all wavelets are
    parallel and their crests line up on common wavefronts (in phase), so they add up to one strong reflected beam."""
    c = Canvas(W, H)
    a = fade(t, 0.0, dur, dur, 0.3)
    n, top = 5, 470
    mo_t, si_t = 30, 50                                   # Mo thinner than Si (Gamma ~0.4)
    ys, y = [], top
    for k in range(n):
        c.rect((240, y, 1680, y + mo_t), fill=(70, 66, 96), a=a * 0.9)
        c.rect((240, y + mo_t, 1680, y + mo_t + si_t), fill=(34, 36, 50), a=a * 0.9)
        ys.append(y)
        y += mo_t + si_t
    c.text((240, top - 34), "钼（深） / 硅（浅）交替", 24, INK2, a)
    th = math.radians(10)
    dx, dy = math.sin(th), math.cos(th)                   # incoming direction (screen y down)
    hit_x = 700
    inc = ease_out(seg(t, 0.3, 1.6))
    x_top = hit_x - (top - 90) * dx / dy
    c.line((x_top, 90), (x_top + (hit_x - x_top) * inc, 90 + (top - 90) * inc), VIOLET, 4, a)
    ylast = ys[-1]
    if inc >= 1:
        p2 = ease(seg(t, 1.4, 2.4))
        c.line((hit_x, top), (hit_x + (ylast - top) * dx / dy * p2, top + (ylast - top) * p2), VIOLET, 3, a * 0.5)
    rx, ry = math.sin(th), -math.cos(th)                  # reflected direction, mirror-symmetric about the normal
    lam = 50.0
    L = 360
    for k, yk in enumerate(ys):
        hx = hit_x + (yk - top) * dx / dy
        r = ease_out(seg(t, 1.5 + 0.22 * k, 2.5 + 0.22 * k))
        if r <= 0:
            continue
        ex, ey = hx + rx * L * r, yk + ry * L * r
        c.line((hx, yk), (ex, ey), VIOLET, 2, a * 0.45 * r)
        proj0 = hx * rx + yk * ry                           # crests where p.r = m * lam (one shared set of wavefronts)
        s0 = (-proj0) % lam
        sv = s0
        while sv < L * r:
            px, py = hx + rx * sv, yk + ry * sv
            c.line((px - 17 * ry, py + 17 * rx), (px + 17 * ry, py - 17 * rx), (230, 210, 255), 2, a * r)
            sv += lam
    s1 = ease(seg(t, 1.8, 2.6))
    c.text((1180, 250), "单层 ≈ 1%", 36, INK, a * s1 * (1 - ease(seg(t, 5.0, 5.6))))
    wf = ease(seg(t, 3.6, 4.6))                             # the shared wavefronts across all wavelets
    # (the crest ticks of neighbouring wavelets join into shared wavefronts)
    c.text((1180, 300), "波峰对齐 · 同相叠加", 28, INK2, a * wf)
    sm = ease(seg(t, 5.4, 6.8))
    bx, by = hit_x + 60, top - 10
    c.line((bx, by), (bx + rx * 520, by + ry * 520), (230, 210, 255), 12, a * sm, glow=True)
    c.text((1180, 250), "叠加后 最高约 70%", 44, INK, a * sm, weight_glow=True)
    c.text((960, 1010), "每层反射的弱光波步调一致、同相叠加（示意 · 层数少画）", 24, INK2, a, anchor="mm")
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
    # 0.1 mm drawn ~10 px tall on a ~640 km profile (1 px ~ 0.9 km): vertical exaggeration ~1e8 (audit_B4 B4_06)
    c.text((bx1, by - 120), "纵向放大约 1 亿倍" if zoom > 0.5 else "", 26, INK2, a * pl * ease(seg(zoom, 0.5, 1.0)),
           anchor="rm")
    lab = ease(seg(t, 5.0, 5.8))
    c.text((1340, 760), "最大偏差只有 0.1 mm", 46, INK, a * lab, anchor="mm", weight_glow=True)
    c.text((1340, 820), "（ZEISS）", 24, INK2, a * lab, anchor="mm")
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
    # a tilt error turns the mirror and its normal by a tiny angle; the reflected ray swings by twice that (夸大示意)
    arc = ease(seg(t, 3.4, 4.2))
    dg = math.radians(4) * arc
    ca, sa = math.cos(dg), math.sin(dg)
    def rot(px, py):                                                         # noqa: E306
        return (mx + (px - mx) * ca - (py - my) * sa, my + (px - mx) * sa + (py - my) * ca)
    c.line(rot(mx - 10, my - 220), rot(mx + 10, my + 220), CYAN, 4, a * arc * 0.8)
    c.line((mx, my), rot(mx + 380, my), CYAN, 2, a * arc * 0.6)
    ang_r = math.atan2(676, 1300) + 2 * dg
    c.line((mx, my), (mx + 1400 * math.cos(ang_r), my + 1400 * math.sin(ang_r)), CYAN, 2, a * arc * 0.8)
    c.text((mx + 400, my + 40), "δ", 30, CYAN, a * arc)
    c.text((mx + 900, my + 640), "反射光偏转 2δ", 26, CYAN, a * arc)
    c.text((mx - 40, my + 340), "转角已夸大示意", 22, CYAN, a * arc, anchor="mm")
    c.text((1280, 300), "倾角误差 < 0.1 nrad", 52, LINE, a * arc, anchor="mm", weight_glow=True)
    c.text((1280, 360), "（ZEISS）", 24, LINE, a * arc, anchor="mm")
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
