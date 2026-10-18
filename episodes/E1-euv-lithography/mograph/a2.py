"""A2 2D shots: diffraction through a slit, blurring lines, the Rayleigh formula (F53), the two routes,
DUV 193 nm (F1, F54), multi-patterning, 13.5 nm vs 193 nm to scale (F1), EUV collapsing the steps (F54),
and the pen of light failing."""
import math
import random

from PIL import Image, ImageDraw, ImageFilter

from mograph import (BLUE_BG, CYAN, INK, INK2, LINE, ORANGE, VIOLET, Canvas, ease, ease_out, fade, seg, shot)

DEEP = (90, 80, 200)
GREY = (150, 154, 168)


def waves(c, t, a, slit_w, cx=820, speed=160, lam=60, region=(0, 1920)):
    """Plane wavefronts from the left; after the slit they bend into circular arcs spreading in a fan.
    The narrower the slit relative to the wavelength, the wider the fan."""
    c.rect((cx - 12, 0, cx + 12, 540 - slit_w / 2), fill=(40, 44, 60), a=a)
    c.rect((cx - 12, 540 + slit_w / 2, cx + 12, 1080), fill=(40, 44, 60), a=a)
    phase = (t * speed) % lam
    x = region[0] + phase
    while x < cx:
        c.line((x, 120), (x, 960), (210, 196, 255), 3, a * 0.75, glow=True)
        x += lam
    spread = min(math.radians(85), math.asin(min(1.0, lam / max(slit_w, 1))) * 1.4)
    r = phase
    while r < 1100:
        if r > 4:
            n = 40
            fade_r = max(0.0, 1 - r / 1150)
            pts = []
            for i in range(n + 1):
                th = -spread + 2 * spread * i / n
                pts.append((cx + r * math.cos(th), 540 + r * math.sin(th)))
            for i in range(n):
                c.line(pts[i], pts[i + 1], (210, 196, 255), 3, a * 0.75 * fade_r, glow=True)
        r += lam
    return spread


@shot("A2_01")
def diffraction(t, dur, W, H):
    c = Canvas(W, H, bg=(0, 0, 0))
    a = fade(t, 0.0, dur, dur, 0.3)
    waves(c, t, a, slit_w=90)
    c.text((1860, 1030), "衍射 diffraction · 示意", 20, INK2, a, anchor="rm")
    return c.finish(glow_radius=8, glow_gain=1.0)


def sem_lines(Wpx, Hpx, k, blur, gap=140):
    im = Image.new("L", (Wpx, Hpx), 56)
    d = ImageDraw.Draw(im)
    for x0 in (Wpx / 2 - gap * k - 90 * k, Wpx / 2 + gap * k - 90 * k):
        d.rectangle((x0, 0, x0 + 180 * k, Hpx), fill=176)
    if blur > 0.3:
        im = im.filter(ImageFilter.GaussianBlur(blur * k))
    return Image.blend(im, Image.effect_noise((Wpx, Hpx), 30), 0.2).convert("RGB")


@shot("A2_02")
def narrower(t, dur, W, H):
    c = Canvas(W, H)
    a = fade(t, 0.0, dur, dur, 0.3)
    p = ease(seg(t, 0.4, dur - 0.6))
    c.img = sem_lines(W, H, c.k, blur=4 + 110 * p ** 1.6)
    c.d = ImageDraw.Draw(c.img, "RGBA")
    c.g = ImageDraw.Draw(c.glow)
    # inset: the energy view from A2_01, slit narrowing
    k = c.k
    inset = Canvas(int(560 * k), int(315 * k), bg=(0, 0, 0))
    waves(inset, t, 1.0, slit_w=90 - 70 * p)
    ins = inset.finish(glow_radius=8, vignette=False)
    c.img.paste(ins, (int(60 * k), int(60 * k)))
    c.d = ImageDraw.Draw(c.img, "RGBA")
    c.rect((60, 60, 620, 375), outline=INK2, width=2, a=a)
    c.text((640, 360), "缝越窄 → 散得越开", 24, INK, a, anchor="lm")
    c.text((1860, 1030), "SEM 风格示意", 18, INK, a, anchor="rm")
    return c.finish(glow_radius=4, glow_gain=0.5)


@shot("A2_03")
def rayleigh(t, dur, W, H):
    c = Canvas(W, H, bg=(0, 0, 0))
    a = fade(t, 0.0, dur, dur, 0.3)
    parts = [("CD", INK, "能画多细", 1.0), ("=", INK2, "", 0.4), ("k", GREY, "工艺因子", 9.2), ("·", INK2, "", 0.4),
             ("λ", VIOLET, "光的波长", 4.0), ("/", INK2, "", 0.4), ("NA", CYAN, "数值孔径 · 镜头收光的能力", 6.4)]
    xs = [500, 670, 810, 950, 1060, 1200, 1420]
    for (sym, col, name, t0), x in zip(parts, xs):
        on = ease(seg(t, t0, t0 + 0.6)) if name else ease(seg(t, 0.4, 1.0))
        pop = 1 + 0.12 * math.sin(math.pi * seg(t, t0, t0 + 0.6)) if name else 1
        c.text((x, 480), sym, int(120 * pop), col, a * max(on, 0.25 if name else 0), anchor="mm", weight_glow=on > 0.5)
        if sym == "k":                                             # subscript 1 (the font lacks ₁)
            c.text((x + 38, 520), "1", int(56 * pop), col, a * max(on, 0.25), anchor="mm")
        if name:
            c.text((x, 600), name, 30, col, a * on, anchor="mm")
    c.text((960, 760), "工艺因子 k 的物理极限：0.25（F53）", 28, GREY, a * ease(seg(t, 9.8, 10.4)), anchor="mm")
    return c.finish(glow_radius=10, glow_gain=0.8)


@shot("A2_04")
def two_routes(t, dur, W, H):
    c = Canvas(W, H, bg=BLUE_BG)
    c.grid(a=0.55)
    a = fade(t, 0.0, dur, dur, 0.3)
    # left: converging cone, half-angle opening up
    th = math.radians(14 + 22 * ease(seg(t, 0.8, 3.4)))
    ax, ay, L = 480, 820, 520
    for s in (-1, 1):
        c.line((ax + s * L * math.tan(th), ay - L), (ax, ay), LINE, 3, a)
    c.line((ax - 260, ay - L), (ax + 260, ay - L), LINE, 5, a)
    c.text((ax, ay - L - 50), "镜头", 26, LINE, a, anchor="mm")
    c.text((ax, ay + 60), "路线二：NA 越大", 32, LINE, a, anchor="mm", weight_glow=True)
    # right: a wavelength ruler that shortens segment by segment
    lam = 220 - 150 * ease(seg(t, 0.8, 3.4))
    x, y = 1180, 420
    i = 0
    while x + lam <= 1760:
        pts = [(x + lam * j / 20, y - 60 * math.sin(2 * math.pi * j / 20)) for j in range(21)]
        for j in range(20):
            c.line(pts[j], pts[j + 1], LINE, 3, a)
        x += lam
        i += 1
    c.line((1180, 520), (1180 + lam, 520), LINE, 2, a)
    c.text((1180 + lam / 2, 550), "λ", 28, LINE, a, anchor="mm")
    c.text((1470, 880), "路线一：λ 越短", 32, LINE, a, anchor="mm", weight_glow=True)
    conv = ease(seg(t, 3.8, 4.6))
    c.line((ax + 200, 960), (900, 1010), LINE, 2, a * conv)
    c.line((1470, 940), (1020, 1010), LINE, 2, a * conv)
    c.text((960, 1030), "线更细", 34, LINE, a * conv, anchor="mm", weight_glow=True)
    return c.finish(glow_radius=8)


def _paper(c, a, x0=0, x1=1920, y0=0, y1=1080):
    for x in range(x0, x1, 40):
        c.line((x, y0), (x, y1), (30, 36, 50), 1, a)
    for y in range(y0, y1, 40):
        c.line((x0, y), (x1, y), (30, 36, 50), 1, a)


@shot("A2_05")
def duv_marker(t, dur, W, H):
    c = Canvas(W, H)
    a = fade(t, 0.0, dur, dur, 0.3)
    _paper(c, a)
    p = ease(seg(t, 0.5, 3.0))
    y = 560
    c.rect((300, y - 40, 300 + 1100 * p, y + 40), fill=(150, 130, 230), a=a * 0.9)      # one 40 nm line
    c.text((300, y - 90), "最细约 40 nm", 30, INK, a * ease(seg(t, 2.6, 3.2)), anchor="lm")
    mx = 300 + 1100 * p
    c.rect((mx - 10, y - 200, mx + 70, y - 40), fill=(60, 64, 90), a=a, radius=10)          # the marker
    c.rect((mx - 5, y - 52, mx + 65, y + 40), fill=(150, 130, 230), a=a, radius=4)
    c.text((mx + 30, y - 120), "193 nm DUV", 20, INK, a, anchor="mm")
    two = ease(seg(t, 4.2, 5.4))                                   # trying two finer lines: the tip covers both
    if two > 0:
        y2 = 820
        for dy in (-22, 22):
            c.rect((300, y2 + dy - 6, 1400, y2 + dy + 6), outline=CYAN, width=2, a=a * two)
        c.rect((300, y2 - 40, 300 + 1100 * ease(seg(t, 5.0, 7.0)), y2 + 40), fill=(150, 130, 230), a=a * 0.8)
        c.text((1450, y2), "想画两条更细的线 → 一笔盖住", 26, ORANGE, a * ease(seg(t, 6.4, 7.0)), anchor="lm")
    c.text((960, 1030), "单次曝光极限约 40 nm（F1 · F54）", 20, INK2, a, anchor="mm")
    return c.finish(glow_radius=6, glow_gain=0.5)


STEP_COLS = [(150, 130, 230), (230, 180, 90), (90, 170, 210)]


def _steps(c, x, y, reps, extra, a, w=110):
    for r in range(reps):
        for k, col in enumerate(STEP_COLS):
            c.rect((x, y, x + w - 8, y + 70), fill=col, a=a, radius=6)
            x += w
        for e in range(extra):
            c.rect((x, y, x + w * 0.6 - 8, y + 70), fill=(110, 116, 132), a=a, radius=6)
            x += w * 0.6
    return x


@shot("A2_06")
def multipatterning(t, dur, W, H):
    c = Canvas(W, H)
    a = fade(t, 0.0, dur, dur, 0.3)
    stage = 0 if t < 2.2 else (1 if t < 4.4 else 2)
    reps, extra = (1, 0) if stage == 0 else ((2, 1) if stage == 1 else (4, 2))
    total = _steps(c, 0, 0, reps, extra, 0.0)                     # measure
    chase = max(0.0, total - 1700) * ease(seg(t, 4.6, dur - 0.3))
    _steps(c, 120 - chase, 760, reps, extra, a)
    c.text((120 - chase, 870), "涂胶 · 曝光 · 刻蚀", 24, INK2, a, anchor="lm")
    nm = [40, 20, 10][stage]
    c.text((960, 300), f"约 {nm} nm", 96, INK, a, anchor="mm", weight_glow=True)
    c.text((960, 420), ["一次曝光", "两次曝光", "四次曝光 + 额外工序"][stage], 34, INK2, a, anchor="mm")
    c.text((960, 1030), "F54", 18, INK2, a, anchor="mm")
    return c.finish(glow_radius=8, glow_gain=0.6)


def _wave(c, x0, y, lam_px, length, amp, col, a, width=3, glow=True):
    n = int(length / 3)
    if n < 1:
        return
    prev = None
    for i in range(n + 1):
        x = x0 + length * i / n
        p = (x, y - amp * math.sin(2 * math.pi * (x - x0) / lam_px))
        if prev:
            c.line(prev, p, col, width, a, glow=glow)
        prev = p


@shot("A2_07")
def to_scale(t, dur, W, H):
    c = Canvas(W, H, bg=(0, 0, 0))
    a = fade(t, 0.0, dur, dur, 0.3)
    x0 = 200
    L193 = 1400                                                    # one 193 nm period spans 1400 px
    lam = L193 * 13.5 / 193
    _wave(c, x0, 360, L193, L193, 120, DEEP, a * ease(seg(t, 0.2, 1.0)), width=4)
    c.text((x0, 220), "DUV 193 nm", 30, (160, 150, 240), a, anchor="lm")
    n = int(14.3 * ease(seg(t, 1.6, 5.6)))
    _wave(c, x0, 700, lam, lam * n, 60, (200, 170, 255), a, width=3)
    for i in range(n):
        c.circle((x0 + lam * (i + 0.25), 640), 6, fill=(230, 214, 255), a=a, glow=True)
    c.text((x0, 840), "EUV 13.5 nm", 30, (220, 200, 255), a, anchor="lm")
    c.text((x0 + L193 + 40, 700), f"{n}", 64, INK, a, anchor="lm", weight_glow=True)
    c.line((x0, 520), (x0 + L193, 520), INK2, 1, a * 0.6)
    c.text((960, 1000), "短 14 倍以上（按比例 · F1）", 32, INK, a * ease(seg(t, 5.8, 6.4)), anchor="mm")
    return c.finish(glow_radius=10, glow_gain=1.0)


@shot("A2_09")
def collapse(t, dur, W, H):
    c = Canvas(W, H)
    a = fade(t, 0.0, dur, dur, 0.3)
    sweep = ease(seg(t, 0.6, 2.6))
    if sweep < 1:
        _steps(c, 120, 600, 4, 2, a * (1 - sweep))
    pops = random.Random(2)
    for i in range(14):                                            # surplus blocks pop out and vanish
        p = ease(seg(t, 1.2 + 0.06 * i, 2.4 + 0.06 * i))
        if 0 < p < 1:
            x = 500 + 90 * i
            c.rect((x, 600 - 260 * p, x + 60, 670 - 260 * p), fill=(110, 116, 132), a=a * (1 - p), radius=6)
    sx = 120 + 1700 * sweep
    c.line((sx, 520), (sx, 760), VIOLET, 6, a * (sweep < 1), glow=True)
    after = ease(seg(t, 2.2, 3.0))
    _steps(c, 120, 600, 1, 0, a * after)
    c.text((480, 720), "EUV：一次曝光", 28, VIOLET, a * after, anchor="lm")
    c.text((960, 300), "部分关键层：非光刻工序最多减少 3–5 倍", 40, INK, a * ease(seg(t, 3.0, 3.6)), anchor="mm",
           weight_glow=True)
    c.text((960, 370), "（ASML 引用 imec 研究 · F54）", 24, INK2, a * ease(seg(t, 3.0, 3.6)), anchor="mm")
    return c.finish(glow_radius=8, glow_gain=0.6)


@shot("A2_10")
def pen_fails(t, dur, W, H):
    c = Canvas(W, H, bg=(0, 0, 0))
    a = fade(t, 0.0, 0.2, dur, 0.05)
    out = 1 - ease(seg(t, 2.6, 4.2))
    rnd = random.Random(int(t * 24))
    flick = (0.25 + 0.75 * rnd.random()) if t > 0.6 else 1.0
    lvl = out * flick
    _wave(c, 300, 540, 120, 1320, 40, (200, 170, 255), a * lvl, width=4)
    c.circle((1620, 540), 14, fill=(240, 230, 255), a=a * lvl, glow=True)
    ember = ease(seg(t, 3.4, 4.0)) * (1 - ease(seg(t, 4.4, 5.0)))
    c.circle((1620, 540), 5, fill=(120, 80, 160), a=a * ember, glow=True)
    return c.finish(glow_radius=12, glow_gain=1.0)
