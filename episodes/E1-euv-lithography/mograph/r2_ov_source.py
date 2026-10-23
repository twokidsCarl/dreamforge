"""P1 round 2 overlays for the source-chamber shots (Micro layer of the two-layer system, SCALE_E1 v2 §4):
circular magnifiers drawn in the E2-illustration language (3D / 6D picks), a spectrum HUD and a power chain.

  OVERLAYS[sid](img, t, dur, W, H) -> PIL.Image (RGB)

Layout rules: keep x > 0.62 W, y < 0.28 H (storyboard label) and the bottom 15 % (subtitles) clear;
violet = EUV, orange = laser only, cyan = measurement; text >= 3.5 % H on dark translucent panels.
"""
import math
import os
import random
import sys

from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../../shared/tools"))
from overlay_labels import font  # noqa: E402
from richtext import draw_text, text_bbox  # noqa: E402

VIOLET = (138, 92, 255)
VIOLET_L = (196, 170, 255)
ORANGE = (255, 138, 61)
CYAN = (63, 214, 224)
INK = (232, 236, 244)
INK2 = (160, 168, 190)
OUTLINE = (18, 12, 38)
SS = 2                                      # supersampling


def clamp01(x):
    return max(0.0, min(1.0, x))


def ease(x):
    x = clamp01(x)
    return x * x * (3 - 2 * x)


class Layer:
    """RGBA overlay at SS x resolution; coordinates in pixels of the final frame."""

    def __init__(self, W, H):
        self.W, self.H = W, H
        self.im = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.im, "RGBA")

    def s(self, v):
        return v * SS

    def line(self, p0, p1, col, w=1.5, a=1.0):
        self.d.line([(self.s(p0[0]), self.s(p0[1])), (self.s(p1[0]), self.s(p1[1]))],
                    fill=(*col, int(255 * a)), width=max(1, round(self.s(w))))

    def circle(self, c, r, fill=None, outline=None, w=1.5, a=1.0):
        b = [self.s(c[0] - r), self.s(c[1] - r), self.s(c[0] + r), self.s(c[1] + r)]
        kw = {}
        if fill:
            kw["fill"] = (*fill[:3], int((fill[3] if len(fill) > 3 else 255) * a))
        if outline:
            kw["outline"] = (*outline, int(255 * a))
            kw["width"] = max(1, round(self.s(w)))
        self.d.ellipse(b, **kw)

    def rect(self, box, fill, radius=6, a=1.0, outline=None, w=1.0):
        b = [self.s(v) for v in box]
        kw = {"fill": (*fill[:3], int((fill[3] if len(fill) > 3 else 255) * a))}
        if outline:
            kw["outline"] = (*outline, int(255 * a))
            kw["width"] = max(1, round(self.s(w)))
        self.d.rounded_rectangle(b, radius=self.s(radius), **kw)

    def text(self, xy, s, px, col=INK, a=1.0, anchor="la"):
        if a <= 0:
            return
        f = font(round(self.s(px)))
        draw_text(self.d, (self.s(xy[0]), self.s(xy[1])), s, f, fill=(*col, int(255 * a)), anchor=anchor)

    def text_w(self, s, px):
        f = font(round(self.s(px)))
        l, t, r, b = text_bbox(self.d, (0, 0), s, f)
        return (r - l) / SS

    def compose(self, img):
        lay = self.im.resize((self.W, self.H), Image.LANCZOS)
        return Image.alpha_composite(img.convert("RGBA"), lay).convert("RGB")


# ---------------------------------------------------------------- illustration primitives (inside magnifiers)
def ball(d, c, r, base, light=(1.0, 1.0, 1.0), outline=OUTLINE, ow=None, glow=None):
    """Goodsell-ish shaded ball on an ImageDraw (already in SS pixels): dark outline, 3-step shading, highlight."""
    x, y = c
    ow = ow or max(2, r * 0.12)
    if glow:
        for k in range(6, 0, -1):
            rr = r * (1 + 0.18 * k)
            d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=(*glow, int(18 * (7 - k))))
    d.ellipse([x - r - ow, y - r - ow, x + r + ow, y + r + ow], fill=(*outline, 255))
    steps = [(1.0, 0.62), (0.82, 0.82), (0.58, 1.0), (0.3, 1.18)]
    for k, (sc, br) in enumerate(steps):
        rr = r * sc
        ox, oy = -r * 0.22 * k / 3, -r * 0.22 * k / 3
        col = tuple(min(255, int(cc * br)) for cc in base)
        d.ellipse([x + ox - rr, y + oy - rr, x + ox + rr, y + oy + rr], fill=(*col, 255))
    hr = r * 0.18
    d.ellipse([x - r * 0.42 - hr, y - r * 0.42 - hr, x - r * 0.42 + hr, y - r * 0.42 + hr], fill=(255, 255, 255, 200))


def wavy(d, p0, p1, col, amp, waves, w):
    (x0, y0), (x1, y1) = p0, p1
    L = math.hypot(x1 - x0, y1 - y0)
    ux, uy = (x1 - x0) / L, (y1 - y0) / L
    nx, ny = -uy, ux
    pts = []
    for i in range(121):
        t = i / 120
        o = amp * math.sin(2 * math.pi * waves * t)
        pts.append((x0 + ux * L * t + nx * o, y0 + uy * L * t + ny * o))
    for k, ww in ((3, w * 3.2), (2, w * 2), (1, w)):
        a = (60, 110, 255)[3 - k]
        d.line(pts, fill=(*col, a), width=max(1, round(ww)), joint="curve")


def magnifier(L, anchor, center, r, inner, a=1.0, title=None):
    """Circular magnifier: leader line from an anchor dot on the 3D frame to a framed disc with an inner
    illustration. inner(d, cx, cy, R) draws in SS pixels on an RGBA canvas."""
    if a <= 0:
        return
    R = round(L.s(r))
    disc = Image.new("RGBA", (2 * R, 2 * R), (0, 0, 0, 0))
    dd = ImageDraw.Draw(disc, "RGBA")
    for k in range(40, 0, -1):                                   # deep indigo radial backdrop
        rr = R * k / 40
        c = (int(14 + 22 * (1 - k / 40)), int(10 + 12 * (1 - k / 40)), int(36 + 40 * (1 - k / 40)))
        dd.ellipse([R - rr, R - rr, R + rr, R + rr], fill=(*c, 255))
    inner(dd, R, R, R)
    mask = Image.new("L", (2 * R, 2 * R), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, 2 * R - 1, 2 * R - 1], fill=int(255 * a))
    cx, cy = L.s(center[0]), L.s(center[1])
    # shadow
    sh = Image.new("RGBA", L.im.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse([cx - R - 6, cy - R + 4, cx + R + 6, cy + R + 14], fill=(0, 0, 0, int(140 * a)))
    L.im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(14)))
    # leader
    ax, ay = anchor
    dx, dy = ax - center[0], ay - center[1]
    dl = math.hypot(dx, dy) or 1
    edge = (center[0] + dx / dl * r, center[1] + dy / dl * r)
    L.line(edge, anchor, INK, 1.4, a * 0.9)
    L.circle(anchor, 4.5, outline=CYAN, w=1.6, a=a)
    L.circle(anchor, 1.8, fill=CYAN, a=a)
    L.im.paste(disc, (int(cx - R), int(cy - R)), mask)
    L.circle(center, r, outline=INK, w=2.4, a=a)
    L.circle(center, r + 3, outline=(0, 0, 0), w=1.0, a=a * 0.5)
    if title:
        tw = L.text_w(title, 0.036 * L.H)
        x0 = center[0] - tw / 2 - 8
        y0 = center[1] + r + 6
        L.rect((x0, y0, x0 + tw + 16, y0 + 0.036 * L.H + 10), (8, 10, 20, 200), radius=5, a=a)
        L.text((center[0], y0 + 5), title, 0.036 * L.H, INK, a, anchor="ma")


def panel_text(L, xy, lines, px, a=1.0, pad=8):
    """Dark translucent panel with lines [(text, colour)]."""
    w = max(L.text_w(s, px) for s, _ in lines)
    h = len(lines) * px * 1.35
    L.rect((xy[0] - pad, xy[1] - pad, xy[0] + w + pad, xy[1] + h + pad * 0.6), (8, 10, 20, 205), radius=6, a=a)
    for i, (s, c) in enumerate(lines):
        L.text((xy[0], xy[1] + i * px * 1.35), s, px, c, a)


# ---------------------------------------------------------------- shots
def ov_B1_10(img, t, dur, W, H):
    L = Layer(W, H)
    a = ease((t - 0.6) / 0.5)
    p = ease((t - 1.3) / 2.6)                       # pancake growth 25 -> 300 um
    um = 25 + (300 - 25) * p

    def inner(d, cx, cy, R):
        # left: the untouched 25 um droplet; right: the sheet as it spreads (to scale: 12x)
        k = R / 175.0
        dr = 9 * k                                   # 25 um radius in px
        ball(d, (cx - R * 0.55, cy - R * 0.05), dr, (190, 196, 210))
        pr = dr * um / 25
        pr = min(pr, R * 0.62)
        x = cx + R * 0.18
        d.ellipse([x - pr * 0.2 - 3 * k, cy - pr - 3 * k, x + pr * 0.2 + 3 * k, cy + pr + 3 * k], fill=(*OUTLINE, 255))
        for sc, br in ((1.0, 0.6), (0.85, 0.8), (0.6, 1.0), (0.35, 1.15)):
            col = tuple(min(255, int(c * br)) for c in (186, 192, 206))
            d.ellipse([x - pr * 0.2 * sc, cy - pr * sc, x + pr * 0.2 * sc, cy + pr * sc], fill=(*col, 255))
        d.ellipse([x - pr * 0.05, cy - pr * 0.75, x + pr * 0.04, cy - pr * 0.45], fill=(255, 255, 255, 180))
        # incoming pre-pulse from the left (laser orange)
        if t < 2.0:
            d.line([(cx - R, cy - R * 0.05), (cx - R * 0.55 - dr, cy - R * 0.05)], fill=(*ORANGE, 220), width=round(3 * k))
        # cyan scale ticks (diameters)
        for (x0, half, lab) in ((cx - R * 0.55, dr, "25 µm"), (x, pr, f"{um:.0f} µm")):
            yb = cy + R * 0.66
            if x0 == x:
                d.line([(x0 + pr * 0.32, cy - pr), (x0 + pr * 0.32, cy + pr)], fill=(*CYAN, 255), width=round(2.2 * k))
            f = font(round(34 * k))
            if x0 == x and p < 0.06:                 # R3: no second "25 µm" before the sheet has started to spread
                continue
            if x0 == x:                              # R4: only the final 300 µm (no fact-like mid value), inside the circle
                if p > 0.97:
                    draw_text(d, (cx, cy + R * 0.68), "薄饼 300 µm", f, fill=(*CYAN, 255), anchor="mm")
            else:
                draw_text(d, (x0, cy - R * 0.05 - dr - 10 * k), lab, f, fill=(*CYAN, 255), anchor="md")

    u = ease((t - 1.2) / 2.0)
    anchor = (W * (0.49 + (0.46 - 0.49) * u), H * (0.64 + (0.46 - 0.64) * u))
    magnifier(L, anchor, (0.19 * W, 0.4 * H), 0.22 * H, inner, a, title="锡滴 25 µm" if p < 0.06 else "锡滴 25 µm → 薄饼约 300 µm")
    return L.compose(img)


def ov_A0_01(img, t, dur, W, H):
    a = ease((t / dur - 0.72) / 0.06)
    if a <= 0:
        return img
    L = Layer(W, H)

    def inner(d, cx, cy, R):
        k = R / 150.0
        rnd = random.Random(3)
        ions = [("Sn⁸⁺", -0.52, -0.38), ("Sn¹⁰⁺", 0.18, -0.52), ("Sn¹²⁺", 0.5, 0.05), ("Sn¹⁴⁺", -0.2, 0.32)]
        ph = t * 3.0
        for i, (lab, ux, uy) in enumerate(ions):
            x, y = cx + ux * R, cy + uy * R
            ball(d, (x, y), 22 * k, (150, 150, 168), glow=VIOLET)
            ang = rnd.uniform(0, 6.28)
            L0 = (0.25 + 0.15 * ((ph + i * 0.37) % 1.0)) * R
            wavy(d, (x + 20 * k * math.cos(ang), y + 20 * k * math.sin(ang)),
                 (x + (20 * k + L0) * math.cos(ang), y + (20 * k + L0) * math.sin(ang)), VIOLET_L, 5 * k, 4, 2.2 * k)
            draw_text(d, (x, y + 27 * k), lab, font(round(30 * k)), fill=(*INK, 255), anchor="ma")

    magnifier(L, (0.53 * W, 0.53 * H), (0.2 * W, 0.42 * H), 0.2 * H, inner, a, title="锡离子 → 13.5 nm 极紫外光")
    return L.compose(img)


def ov_B2_08(img, t, dur, W, H, anchor_pt=None, center=None, panel_xy=None):
    """R6: anchor_pt / center / panel_xy (fractions) let the R6 wrapper hang the magnifier on the dish."""
    L = Layer(W, H)
    a = ease((t - 0.4) / 0.6)
    u = t / dur
    ph1 = ease((u - 0.06) / 0.26)       # photon splits H2
    ph2 = ease((u - 0.38) / 0.24)       # H radicals bind to Sn
    ph3 = ease((u - 0.66) / 0.26)       # SnH4 leaves towards the pump

    def inner(d, cx, cy, R):
        k = R / 170.0
        # mirror surface band with tin atoms
        yb = cy + R * 0.48
        d.rectangle([cx - R, yb, cx + R, cy + R], fill=(70, 74, 96, 255))
        d.line([(cx - R, yb), (cx + R, yb)], fill=(150, 156, 190, 255), width=round(3 * k))
        for i in range(-5, 6):
            if i == 0 and ph2 > 0:
                continue
            ball(d, (cx + i * 30 * k, yb - 2 * k), 11 * k, (150, 152, 166))
        # H2 molecule splitting under a violet photon
        hx, hy = cx - R * 0.35, cy - R * 0.25
        if ph1 < 1:
            wavy(d, (hx - R * 0.55, hy - R * 0.45), (hx - 14 * k, hy - 6 * k), VIOLET_L, 5 * k, 5, 2.4 * k)
        sep = 9 * k + ph1 * 34 * k
        hpos = [(hx - sep, hy), (hx + sep, hy)]
        if ph2 > 0:                                   # radicals travel to the Sn atom at the centre
            tgt = [(cx - 16 * k, yb - 22 * k), (cx + 16 * k, yb - 22 * k)]
            hpos = [(p[0] + (q[0] - p[0]) * ph2, p[1] + (q[1] - p[1]) * ph2) for p, q in zip(hpos, tgt)]
        # SnH4 molecule
        sx, sy = cx, yb - 2 * k
        if ph2 > 0:
            sy = yb - 2 * k - ph3 * R * 1.05
            sx = cx + ph3 * R * 0.25
            ball(d, (sx, sy), 12 * k, (150, 152, 166))
            for j in range(4):
                ang = math.radians(45 + 90 * j)
                hb = (sx + 18 * k * math.cos(ang), sy + 18 * k * math.sin(ang))
                ball(d, hb, 6.5 * k * ph2, (235, 238, 246))
            if ph3 > 0.05:
                draw_text(d, (sx + 28 * k, sy), "SnH₄", font(round(32 * k)), fill=(*INK, 255), anchor="lm")
        if ph2 < 1:
            for p in hpos:
                ball(d, p, 7 * k, (235, 238, 246), glow=(255, 255, 255) if ph1 > 0.5 else None)
            if ph1 > 0.4:
                draw_text(d, (hx, hy + 18 * k), "2 H·", font(round(32 * k)), fill=(*INK, 255), anchor="ma")
            elif ph1 < 0.3:
                draw_text(d, (hx, hy + 18 * k), "H₂", font(round(32 * k)), fill=(*INK, 255), anchor="ma")
        # pump direction
        d.line([(cx + R * 0.45, cy - R * 0.3), (cx + R * 0.45, cy - R * 0.82)], fill=(*CYAN, 230), width=round(3 * k))
        d.polygon([(cx + R * 0.45, cy - R * 0.9), (cx + R * 0.4, cy - R * 0.78), (cx + R * 0.5, cy - R * 0.78)],
                  fill=(*CYAN, 230))
        draw_text(d, (cx + R * 0.52, cy - R * 0.58), "泵", font(round(32 * k)), fill=(*CYAN, 255), anchor="lm")

    ap = (anchor_pt[0] * W, anchor_pt[1] * H) if anchor_pt else (0.56 * W, 0.47 * H)
    cc = (center[0] * W, center[1] * H) if center else (0.22 * W, 0.4 * H)
    magnifier(L, ap, cc, 0.22 * H, inner, a, title="收集镜表面（示意）")
    lines = [("H₂ → 2 H·", INK if ph1 > 0 else INK2), ("Sn + 4 H· → SnH₄↑", INK if ph2 > 0 else INK2)]
    px = panel_xy or (0.44, 0.62)
    panel_text(L, (px[0] * W, px[1] * H), lines, 0.04 * H, a)
    return L.compose(img)


def ov_B1_18(img, t, dur, W, H):
    L = Layer(W, H)
    a = ease((t - 0.2) / 0.5)
    grow = ease((t - 0.4) / (0.6 * dur))
    # R4 (H14 fix): panel shrunk to the left ~45 % so the source chamber + plasma read as the real object behind it
    x0, x1, y0, y1 = 0.06 * W, 0.36 * W, 0.24 * H, 0.66 * H
    L.rect((x0 - 0.025 * W, y0 - 0.1 * H, x1 + 0.13 * W, y1 + 0.075 * H), (8, 10, 20, 170), radius=8, a=a)
    L.text((x0, y0 - 0.085 * H), "锡离子谱线（示意）", 0.042 * H, INK, a)
    lo, hi = 10.0, 18.0

    def X(nm):
        return x0 + (nm - lo) / (hi - lo) * (x1 - x0)

    # mirror window band +-1 %
    L.rect((X(13.5 * 0.99), y0, X(13.5 * 1.01), y1), (*CYAN, 60), radius=0, a=a)
    # R6: each charge state has its own colour; the spectrum is built up one ion layer at a time (stacked bars),
    # so "thousands of lines from Sn8+..Sn14+ pile up at 13.5 nm" is visible as a process (R5 review)
    ICOL = [(110, 150, 255), (140, 130, 255), (170, 115, 255), (200, 105, 245), (225, 100, 225), (240, 110, 190),
            (250, 135, 160)]
    rnd = random.Random(7)
    lines = []
    for i in range(900):
        if rnd.random() < 0.82:
            nm = rnd.gauss(13.5, 0.28)
        else:
            nm = rnd.uniform(10.3, 17.7)
        lines.append((nm, i % 7, i // 7))
    per = 900 / 7
    bins = {}
    for nm, k, j in lines:
        if lo < nm < hi and j / per < clamp01(grow * 7 - k):
            b = round((nm - lo) * 40)
            bins.setdefault(b, [0] * 7)[k] += 1
    top = 40
    for b, cs in bins.items():
        nm = lo + b / 40
        yb = y1
        for k, c in enumerate(cs):
            if not c:
                continue
            hgt = (y1 - y0 - 10) * c / max(top, 60)
            L.line((X(nm), yb), (X(nm), yb - hgt), ICOL[k], 1.8, a)
            yb -= hgt
    L.line((x0, y1), (x1, y1), INK2, 1.2, a)
    for nm in (10, 12, 13.5, 15, 18):
        L.line((X(nm), y1), (X(nm), y1 + 5), INK2, 1.2, a)
        L.text((X(nm), y1 + 7), f"{nm:g}", 0.036 * H, CYAN if nm == 13.5 else INK, a, anchor="ma")
    L.text((x1 + 0.025 * W, y1 + 7), "nm", 0.036 * H, INK2, a)
    L.text((X(13.5 * 1.01) + 6, y0 + 4), "镜子反射窗口", 0.034 * H, CYAN, a)
    L.text((X(13.5 * 1.01) + 6, y0 + 4 + 0.045 * H), "±1 %", 0.034 * H, CYAN, a)
    ions = ["Sn⁸⁺", "Sn⁹⁺", "Sn¹⁰⁺", "Sn¹¹⁺", "Sn¹²⁺", "Sn¹³⁺", "Sn¹⁴⁺"]
    for i, s in enumerate(ions):
        ai = a * ease(grow * 7 - i + 0.6)
        yy = y0 - 0.02 * H + i * 0.064 * H
        L.rect((x1 + 0.03 * W, yy + 0.012 * H, x1 + 0.03 * W + 0.012 * H, yy + 0.034 * H), (*ICOL[i], 255), radius=2, a=ai)
        L.text((x1 + 0.04 * W, yy), s, 0.038 * H, ICOL[i], ai)
    return L.compose(img)


def ov_B1_22(img, t, dur, W, H):
    L = Layer(W, H)
    a = ease((t - 0.15) / 0.4)
    stages = [("种子", "~W"), ("放大 1", "~100 W"), ("放大 2", "~1 kW"), ("放大 3", "~10 kW"), ("放大 4", "数十 kW")]
    cur = min(4, int(clamp01(t / dur) * 5.2))
    x0, y = 0.05 * W, 0.075 * H
    step = 0.11 * W
    L.rect((x0 - 12, y - 10, x0 + step * 4 + 0.09 * W, y + 0.145 * H), (8, 10, 20, 195), radius=7, a=a)
    for i, (nm, pw) in enumerate(stages):
        x = x0 + i * step
        on = i <= cur
        r = 5 + i * 1.6
        L.circle((x + 0.03 * W, y + 0.035 * H), r, fill=(*ORANGE, 255) if on else (70, 60, 50, 255), a=a)
        if i < 4:
            L.line((x + 0.03 * W + r + 3, y + 0.035 * H), (x + step + 0.03 * W - 9, y + 0.035 * H),
                   ORANGE if i < cur else INK2, 1.0 + 0.6 * i, a)
        L.text((x + 0.03 * W, y + 0.065 * H), nm, 0.034 * H, INK if on else INK2, a, anchor="ma")
        L.text((x + 0.03 * W, y + 0.105 * H), pw, 0.034 * H, ORANGE if on else INK2, a, anchor="ma")
    L.text((x0 + step * 4 + 0.085 * W, y - 4), "示意", 0.03 * H, INK2, a, anchor="ra")
    return L.compose(img)


# B2_08 (R3): the reaction lines live once, in the in-frame panel; the storyboard label repeated them
NO_STORYBOARD_LABELS = {"B2_08"}

OVERLAYS = {"B1_10": ov_B1_10, "A0_01": ov_A0_01, "B2_08": ov_B2_08, "B1_18": ov_B1_18, "B1_22": ov_B1_22}
