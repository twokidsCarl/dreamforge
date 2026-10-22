"""A2 2D shots: diffraction through a slit, blurring lines, the Rayleigh formula (F53), the two routes,
DUV 193 nm (F1, F54), multi-patterning, 13.5 nm vs 193 nm to scale (F1), EUV collapsing the steps (F54),
and the pen of light failing."""
import math
import random

from PIL import Image, ImageDraw, ImageFilter

from mograph import (BLUE_BG, CYAN, INK, INK2, LINE, ORANGE, VIOLET, Canvas, ease, ease_out, fade, screen_text, seg,
                     shot)
from overlay_labels import font

DEEP = (90, 80, 200)
GREY = (150, 154, 168)
TAG_XY = (1824, 1010)            # corner tags: right-aligned inside action-safe, below the subtitle line (934-985)


def tag(c, s, a, size=28, xy=TAG_XY, scrim=True, color=INK):
    """A small right-aligned note (示意 / source) at >= 28 px, on a soft dark scrim so it reads on any picture."""
    s = screen_text(s)
    if a <= 0 or not s:
        return
    w = font(int(c.px(size))).getlength(s) / c.k
    if scrim:
        c.rect((xy[0] - w - 16, xy[1] - size * 0.5 - 12, xy[0] + 14, xy[1] + size * 0.5 + 12), fill=(6, 8, 12),
               a=a * 0.6, radius=10)
    c.text(xy, s, size, color, a * 0.92, anchor="rm")


def finish_tags(c, tags, **kw):
    """c.finish(), then the corner notes on top (the vignette would otherwise grey them out in the corner)."""
    out = c.finish(**kw)
    c.img = out
    c.d = ImageDraw.Draw(out, "RGBA")
    for args in tags:
        tag(c, *args)
    return out


def chapter_card(c, title, a, label="章节"):
    """Chapter card drawn inside a 2D shot, in the layout edit_film.draw_chapter uses on 3D shots: lower left on a
    soft dark gradient (dark at the left, clear from 2/3 of the width), 章节 / title / growing violet rule."""
    if a <= 0:
        return
    W, H = c.W, c.H
    grad = Image.linear_gradient("L").rotate(90, expand=True).resize((W, H))
    mask = grad.point(lambda v: int(max(0.0, (255 - v) / 255 - 0.35) / 0.65 * 230 * a))
    c.img.paste(Image.new("RGB", (W, H), (4, 5, 9)), (0, 0), mask)
    c.glow.paste(Image.new("RGB", (W, H), (0, 0, 0)), (0, 0), mask)
    c.d = ImageDraw.Draw(c.img, "RGBA")
    c.g = ImageDraw.Draw(c.glow)
    c.text((160, 470), label, 34, INK2, a)
    f = font(int(c.px(96)))
    c.g.text((c.px(160), c.px(520)), title, font=f, fill=tuple(int(v * a * 0.62) for v in VIOLET))
    c.text((160, 520), title, 96, INK, a)
    tw = f.getlength(title) / c.k
    c.rect((160, 640, 160 + tw * a, 643), fill=VIOLET, a=a)


def rot_text(c, center, s, size, color, a, angle):
    """Text rotated by angle degrees (counter-clockwise), centred on `center` (design units), alpha-faded."""
    if a <= 0:
        return
    f = font(int(c.px(size)))
    w = int(f.getlength(s)) + 8
    h = int(c.px(size) * 1.5)
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).text((w / 2, h / 2), s, font=f, fill=int(255 * min(1.0, a)), anchor="mm")
    m = m.rotate(angle, resample=Image.BICUBIC, expand=True)
    x, y = int(c.px(center[0]) - m.size[0] / 2), int(c.px(center[1]) - m.size[1] / 2)
    c.img.paste(Image.new("RGB", m.size, color), (x, y), m)


def waves(c, t, a, slit_w, cx=820, speed=160, lam=60, region=(0, 1920)):
    """Plane wavefronts from the left; after the slit they bend into circular arcs spreading in a fan.
    The narrower the slit relative to the wavelength, the wider the fan."""
    c.rect((cx - 12, 0, cx + 12, 540 - slit_w / 2), fill=(40, 44, 60), a=a)
    c.rect((cx - 12, 540 + slit_w / 2, cx + 12, 1080), fill=(40, 44, 60), a=a)
    phase = (t * speed) % lam
    x = cx + phase - lam                     # laid out back from the slit: a front reaches it as the next arc starts
    while x > region[0]:
        c.line((x, 120), (x, 960), (210, 196, 255), 3, a * 0.75, glow=True)
        x -= lam
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
    card = fade(t, 0.2, 2.8, dur, 0.5)                             # the A2 chapter card (2D shots draw their own)
    waves(c, t, a * (1 - 0.45 * card), slit_w=90, cx=1000)         # slit right of centre, clear of the card
    chapter_card(c, "为什么要短波长", card)
    return finish_tags(c, [("衍射 diffraction · 示意", a * ease(seg(t, 2.6, 3.2)), 28, TAG_XY, False)],
                       glow_radius=8, glow_gain=1.0)


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
    c.rect((60, 392, 380, 448), fill=(6, 8, 12), a=a * 0.7, radius=10)   # caption under the inset, off the lines
    c.text((80, 420), "缝越窄 → 散得越开", 30, INK, a, anchor="lm")
    return finish_tags(c, [("SEM 风格示意", a)], glow_radius=4, glow_gain=0.5)


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
    lim = a * ease(seg(t, 9.8, 10.4))                              # k with its subscript 1, as in the formula above
    c.text((958, 760), "工艺因子 k", 28, GREY, lim, anchor="rm")
    c.text((966, 772), "1", 18, GREY, lim, anchor="mm")
    c.text((976, 760), " 的物理极限：0.25（F53）", 28, GREY, lim, anchor="lm")
    return c.finish(glow_radius=10, glow_gain=0.8)


@shot("A2_04")
def two_routes(t, dur, W, H):
    c = Canvas(W, H, bg=BLUE_BG)
    c.grid(a=0.55)
    a = fade(t, 0.0, dur, dur, 0.3)
    grow = ease(seg(t, 0.8, 3.4))
    # left, route one (spoken first): a wavelength ruler that shortens segment by segment
    lam = 220 - 150 * grow
    x0, x1, y = 180, 780, 380
    x = x0
    while x + lam <= x1 + 0.5:
        pts = [(x + lam * j / 20, y - 60 * math.sin(2 * math.pi * j / 20)) for j in range(21)]
        for j in range(20):
            c.line(pts[j], pts[j + 1], LINE, 3, a)
        x += lam
    c.line((x0, 480), (x0 + lam, 480), LINE, 2, a)                 # dimension line: one wavelength
    for xe in (x0, x0 + lam):
        c.line((xe, 466), (xe, 494), LINE, 2, a)
    c.text((x0 + lam / 2, 516), "λ", 30, LINE, a, anchor="mm")
    c.text((480, 720), "路线一：λ 越短", 34, LINE, a, anchor="mm", weight_glow=True)
    # right, route two: a lens focusing a cone whose half-angle opens up. The lens grows with the cone (rays can only
    # come from the optic): half-width = L·tanθ + margin, i.e. a bigger NA needs a lens that is 'opened wider'
    th = math.radians(14 + 22 * grow)
    ax, ay, L = 1440, 640, 480
    hw = L * math.tan(th) + 24
    ly = ay - L
    for s_ in (-1, 1):
        c.line((ax + s_ * L * math.tan(th), ly), (ax, ay), LINE, 3, a)
    bulge = 10 + 0.07 * hw                                         # thin biconvex lens in section
    n = 28
    top = [(ax - hw + 2 * hw * i / n, ly - bulge * (1 - (2 * i / n - 1) ** 2)) for i in range(n + 1)]
    bot = [(ax - hw + 2 * hw * i / n, ly + bulge * (1 - (2 * i / n - 1) ** 2)) for i in range(n + 1)]
    for pts in (top, bot):
        for p0, p1 in zip(pts, pts[1:]):
            c.line(p0, p1, LINE, 4, a)
    c.text((ax, ly - bulge - 34), "镜头", 28, LINE, a, anchor="mm")
    r = 120                                                        # the half-angle θ, marked at the focus
    for s_ in (-1, 1):
        pts = [(ax + s_ * r * math.sin(th * i / 12), ay - r * math.cos(th * i / 12)) for i in range(13)]
        for p0, p1 in zip(pts, pts[1:]):
            c.line(p0, p1, LINE, 2, a * 0.8)
    c.line((ax, ay), (ax, ay - r - 30), LINE, 1, a * 0.6)
    c.text((ax + r * math.sin(th / 2) + 22, ay - r * math.cos(th / 2) - 10), "θ", 28, LINE, a, anchor="lm")
    c.text((ax, 720), "路线二：NA 越大", 34, LINE, a, anchor="mm", weight_glow=True)
    # both routes lead to the same result (kept above the subtitle band)
    conv = ease(seg(t, 3.8, 4.6))
    c.line((560, 752), (900, 846), LINE, 2, a * conv)
    c.line((1360, 752), (1020, 846), LINE, 2, a * conv)
    c.text((960, 870), "线更细", 38, LINE, a * conv, anchor="mm", weight_glow=True)
    return c.finish(glow_radius=8)


def _paper(c, a, x0=0, x1=1920, y0=0, y1=1080):
    for x in range(x0, x1, 40):
        c.line((x, y0), (x, y1), (30, 36, 50), 1, a)
    for y in range(y0, y1, 40):
        c.line((x0, y), (x1, y), (30, 36, 50), 1, a)


def _marker(c, tip, a, label):
    """A chisel marker seen from above, leaning up-right from its tip: violet nib as wide as the 40 nm stroke
    (80 px), a 360 x 110 px barrel with the label set along it, a darker cap at the end."""
    ang = math.radians(55)
    u = (math.cos(ang), -math.sin(ang))                            # along the barrel, up-right
    v = (math.sin(ang), math.cos(ang))                             # across it

    def P(s_, q):
        return (tip[0] + u[0] * s_ + v[0] * q, tip[1] + u[1] * s_ + v[1] * q)

    def poly(pts, col, alpha):
        c.d.polygon([(c.px(x), c.px(y)) for x, y in pts], fill=(*col, int(255 * alpha)))
    poly([(tip[0], tip[1] - 40), P(70, -55), P(70, 55), (tip[0], tip[1] + 40)], (150, 130, 230), a)   # chisel nib
    poly([(tip[0], tip[1] - 40), P(70, -55), P(70, -30), (tip[0] + 6, tip[1] - 20)], (186, 170, 245), a)   # facet
    poly([P(66, -60), P(66, 60), P(70, 62), P(70, -62)], (200, 204, 220), a)       # collar
    poly([P(70, -55), P(70, 55), P(430, 55), P(430, -55)], (58, 62, 88), a)       # barrel
    poly([P(70, -55), P(430, -55), P(430, -40), P(70, -40)], (84, 90, 120), a)    # a highlight along one side
    poly([P(430, -60), P(430, 60), P(530, 60), P(540, 0), P(530, -60)], (34, 36, 52), a)   # cap
    rot_text(c, P(250, 0), label, 27, INK, a, 55)


@shot("A2_05")
def duv_marker(t, dur, W, H):
    c = Canvas(W, H)
    a = fade(t, 0.0, dur, dur, 0.3)
    _paper(c, a)
    y, y2 = 470, 720
    p = ease(seg(t, 0.5, 3.0))
    c.rect((300, y - 40, 300 + 1100 * p, y + 40), fill=(150, 130, 230), a=a * 0.9)      # one 40 nm line
    c.text((300, y - 80), "最细约 40 nm", 30, INK, a * ease(seg(t, 2.6, 3.2)), anchor="lm")
    two = ease(seg(t, 4.2, 5.0))                                   # trying two finer lines: the tip covers both
    if two > 0:
        for dy in (-40, 40):                                       # two 20 nm lines, 20 nm apart (2 px per nm, as above)
            c.rect((300, y2 + dy - 20, 1400, y2 + dy + 20), outline=CYAN, width=2, a=a * two)
    q = ease(seg(t, 5.2, 7.0))
    if q > 0:
        c.rect((300, y2 - 40, 300 + 1100 * q, y2 + 40), fill=(150, 130, 230), a=a * 0.8)
    # the same pen: draws line one, lifts and travels back to the start of line two, draws it
    hop = ease(seg(t, 4.4, 5.2))
    if t < 4.4:
        tip = (300 + 1100 * p, y)
    elif q <= 0:
        tip = (1400 + (300 - 1400) * hop, y + (y2 - y) * hop - 50 * math.sin(math.pi * hop))
    else:
        tip = (300 + 1100 * q, y2)
    _marker(c, tip, a, "193 nm DUV（浸没式）")
    c.text((300, y2 + 100), "想画两条更细的线 → 一笔盖住", 30, ORANGE, a * ease(seg(t, 6.4, 7.0)), anchor="lm")
    return finish_tags(c, [("单次曝光极限约 40 nm（F1 · F54）", a, 30, TAG_XY, False)], glow_radius=6, glow_gain=0.5)


STEP_COLS = [(150, 130, 230), (230, 180, 90), (90, 170, 210)]


def _steps(c, x, y, reps, extra, a, w=110, n_vis=None):
    """reps x (coat, expose, etch) + `extra` grey blocks per rep. n_vis: how many blocks are shown (the last one
    fades in) - the bar grows block by block. Returns the right end of the full bar."""
    i = 0
    for r in range(reps):
        for k, col in enumerate(STEP_COLS + [None] * extra):
            bw = w if col else w * 0.6
            vis = 1.0 if n_vis is None else max(0.0, min(1.0, n_vis - i))
            if vis > 0:
                c.rect((x, y, x + bw - 8, y + 70), fill=col or (110, 116, 132), a=a * vis, radius=6)
            x += bw
            i += 1
    return x


def _n_blocks(reps, extra):
    return reps * (3 + extra)


@shot("A2_06")
def multipatterning(t, dur, W, H):
    c = Canvas(W, H)
    a = fade(t, 0.0, dur, dur, 0.3)
    stage = 0 if t < 2.2 else (1 if t < 4.4 else 2)
    plan = [(1, 0), (2, 1), (4, 2)]
    reps, extra = plan[stage]
    w = 130
    # the bar grows block by block; in the last stage it outruns the camera and leaves the frame on the right
    t0 = [0.2, 2.2, 4.4][stage]
    prev = 0 if stage == 0 else _n_blocks(*plan[stage - 1])
    n_vis = prev + (_n_blocks(reps, extra) - prev) * ease(seg(t, t0, t0 + (0.8 if stage < 2 else dur - 0.6 - t0)))
    chase = 260 * ease(seg(t, 5.0, dur)) if stage == 2 else 0.0    # the camera pans right but cannot keep up
    _steps(c, 120 - chase, 760, reps, extra, a, w=w, n_vis=n_vis)
    # legend pinned above the bar (never travels off the left edge)
    lx = 120
    for col, name in zip(STEP_COLS + [(110, 116, 132)], ["涂胶", "曝光", "刻蚀", "额外工序"]):
        if name == "额外工序" and stage == 0:
            continue
        c.rect((lx, 690, lx + 28, 718), fill=col, a=a, radius=4)
        c.text((lx + 40, 704), name, 28, INK, a * 0.9, anchor="lm")
        lx += 40 + 28 * len(name) + 40
    nm = [40, 20, 10][stage]
    c.text((960, 300), f"约 {nm} nm", 96, INK, a, anchor="mm", weight_glow=True)
    c.text((960, 420), ["一次曝光", "两次曝光", "四次曝光 + 额外工序"][stage], 36, INK, a * 0.85, anchor="mm")
    return finish_tags(c, [("F54", a, 28, TAG_XY, False)], glow_radius=8, glow_gain=0.6)


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
    if n >= 1:                                                     # the count starts with the first crest
        c.text((x0 + L193 + 40, 700), f"{n}", 64, INK, a, anchor="lm", weight_glow=True)
    c.line((x0, 520), (x0 + L193, 520), INK2, 1, a * 0.6)
    c.text((960, 110), "短 14 倍以上（按比例 · F1）", 36, INK, a * ease(seg(t, 5.8, 6.4)), anchor="mm",
           weight_glow=True)                                       # top: clear of the subtitle band
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
    _steps(c, 120, 600, 1, 2, a * after)                           # 8 grey steps -> 2: 4x, inside the "3-5x" caption
    c.text((480, 720), "EUV：一次曝光", 28, VIOLET, a * after, anchor="lm")
    c.text((960, 300), "部分关键层：非光刻工序最多减少 3–5 倍", 40, INK, a * ease(seg(t, 3.0, 3.6)), anchor="mm",
           weight_glow=True)
    c.text((960, 376), "（ASML 引用 imec 研究 · F54）", 30, INK, a * 0.88 * ease(seg(t, 3.0, 3.6)), anchor="mm")
    return c.finish(glow_radius=8, glow_gain=0.6)


@shot("A2_10")
def pen_fails(t, dur, W, H):
    c = Canvas(W, H, bg=(0, 0, 0))
    a = fade(t, 0.0, dur, dur, 0.05)
    out = 1 - ease(seg(t, 2.6, 4.2))
    rnd = random.Random(int(t * 24))
    flick = (0.25 + 0.75 * rnd.random()) if t > 0.6 else 1.0
    lvl = out * flick
    _wave(c, 300, 540, 120, 1320, 40, (200, 170, 255), a * lvl, width=4)
    c.circle((1620, 540), 14, fill=(240, 230, 255), a=a * lvl, glow=True)
    ember = ease(seg(t, 3.4, 4.0)) * (1 - ease(seg(t, 4.4, 5.0)))
    c.circle((1620, 540), 5, fill=(120, 80, 160), a=a * ember, glow=True)
    return c.finish(glow_radius=12, glow_gain=1.0)
