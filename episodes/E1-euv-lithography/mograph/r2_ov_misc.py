"""P1 round 2 overlays for the r2_misc shots: numbers, tags, leaders and Micro-layer magnifiers drawn on top of the
Blender frame (SCALE_E1 v2: annotation layer on Macro / Micro pictures, never a dark full-screen card).

  OVERLAYS[sid](img, t, dur, W, H) -> PIL.Image (RGB)

Coordinates are fractions of the frame; type sizes are fractions of H (body >= 3.5 % H). The upper-right label zone
(x > 0.62 W, y < 0.28 H) and the bottom 15 % (subtitles) are left clear.
"""
import math
import os
import random
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "shared", "tools"))
from overlay_labels import font, mono_font, serif_font  # noqa: E402
from richtext import draw_text, text_bbox  # noqa: E402
from r2_ov_common import anchor as _anchor  # noqa: E402

VIOLET = (138, 92, 255)
VIOLET_L = (178, 150, 255)
ORANGE = (255, 138, 61)
CYAN = (63, 214, 224)
INK = (232, 236, 244)
INK2 = (160, 168, 188)
PANEL = (8, 12, 22)


# ------------------------------------------------------------------ timing
def clamp01(x):
    return max(0.0, min(1.0, x))


def ease(x):
    x = clamp01(x)
    return x * x * (3 - 2 * x)


def fade(t, t0, t1=None, f=0.35):
    a = clamp01((t - t0) / f)
    if t1 is not None:
        a = min(a, clamp01((t1 - t) / f))
    return a


def lerp2(a, b, u):
    return (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u)


def track(t, dur, keys):
    """keys: [(frac_of_dur, (x, y))] -> eased position at t."""
    u = t / max(dur, 1e-6)
    if u <= keys[0][0]:
        return keys[0][1]
    for (u0, p0), (u1, p1) in zip(keys, keys[1:]):
        if u <= u1:
            return lerp2(p0, p1, ease((u - u0) / max(1e-6, u1 - u0)))
    return keys[-1][1]


# ------------------------------------------------------------------ drawing
class L:
    """An RGBA layer with 1080p-relative helpers."""

    def __init__(self, W, H):
        self.W, self.H = W, H
        self.im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.im)
        self.glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        self.g = ImageDraw.Draw(self.glow)

    def P(self, p):
        return (p[0] * self.W, p[1] * self.H)

    def px(self, v):
        return max(1, int(round(v * self.H / 1080)))

    def panel(self, box, a=1.0, alpha=0.62, radius=10):
        x0, y0 = self.P(box[:2])
        x1, y1 = self.P(box[2:])
        self.d.rounded_rectangle((x0, y0, x1, y1), radius=self.px(radius), fill=(*PANEL, int(255 * alpha * a)))

    def text(self, p, s, size, color=INK, a=1.0, anchor="la", kind="sans", glow=0.0):
        if a <= 0 or not s:
            return None
        px = max(8, int(size * self.H))
        f = {"sans": font, "mono": mono_font, "serif": serif_font}[kind](px)
        xy = self.P(p)
        draw_text(self.d, xy, s, f, fill=(*color, int(255 * a)), anchor=anchor)
        if glow:
            draw_text(self.g, xy, s, f, fill=(*color, int(255 * a * glow)), anchor=anchor)
        return text_bbox(self.d, xy, s, f, anchor=anchor)

    def tag(self, p, lines, a=1.0, size=0.036, color=INK, accent=CYAN, anchor="la"):
        """A compact label block: dark panel + accent bar + 1-3 lines (first line larger)."""
        if a <= 0:
            return
        x, y = self.P(p)
        fs = [max(8, int(size * self.H))] + [max(8, int(size * 0.72 * self.H))] * (len(lines) - 1)
        fonts = [font(s) for s in fs]
        ws = [text_bbox(self.d, (0, 0), s, f)[2] for s, f in zip(lines, fonts)]
        hgt = sum(int(s * 1.32) for s in fs)
        w = max(ws)
        pad = self.px(14)
        if anchor[0] == "r":
            x -= w + 2 * pad
        if anchor[1] == "b":
            y -= hgt + 2 * pad
        if anchor[1] == "m":
            y -= (hgt + 2 * pad) / 2
        self.d.rounded_rectangle((x, y, x + w + 2 * pad + self.px(6), y + hgt + 2 * pad), radius=self.px(8),
                                 fill=(*PANEL, int(255 * 0.66 * a)))
        self.d.rectangle((x, y + pad * 0.6, x + self.px(4), y + hgt + pad * 1.4), fill=(*accent, int(255 * a)))
        yy = y + pad
        for i, (s, f) in enumerate(zip(lines, fonts)):
            draw_text(self.d, (x + pad + self.px(6), yy), s, f, fill=(*(color if i == 0 else INK2), int(255 * a)))
            yy += int(fs[i] * 1.32)
        return (x, y, x + w + 2 * pad, y + hgt + 2 * pad)

    def leader(self, p0, p1, a=1.0, color=CYAN, prog=1.0, dot=True):
        if a <= 0 or prog <= 0:
            return
        x0, y0 = self.P(p0)
        x1, y1 = self.P(p1)
        x1, y1 = x0 + (x1 - x0) * prog, y0 + (y1 - y0) * prog
        self.d.line((x0, y0, x1, y1), fill=(*color, int(230 * a)), width=self.px(2.5))
        if dot and prog >= 1:
            r = self.px(6)
            self.d.ellipse((x1 - r, y1 - r, x1 + r, y1 + r), fill=(*color, int(255 * a)))
            r2 = self.px(14)
            self.g.ellipse((x1 - r2, y1 - r2, x1 + r2, y1 + r2), fill=(*color, int(150 * a)))

    def line(self, p0, p1, color=CYAN, a=1.0, w=2.5):
        self.d.line((*self.P(p0), *self.P(p1)), fill=(*color, int(255 * a)), width=self.px(w))

    def compose(self, img):
        out = img.convert("RGBA")
        g = self.glow.filter(ImageFilter.GaussianBlur(self.px(10)))
        out = Image.alpha_composite(out, g)
        return Image.alpha_composite(out, self.im)


def magnifier(img, center, r, content, a=1.0, ring=CYAN, anchor=None, W=None, H=None):
    """Paste `content` (square PIL image) as a circular inset with a ring, soft shadow and an optional leader to
    `anchor` (frame fraction). center / r in frame fractions (r of H)."""
    if a <= 0:
        return img
    W, H = img.size
    cx, cy, rr = center[0] * W, center[1] * H, r * H
    d = int(2 * rr)
    c = content.convert("RGB").resize((d, d), Image.LANCZOS)
    mask = Image.new("L", (d, d), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, d - 1, d - 1), fill=int(255 * a))
    out = img.convert("RGBA")
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse((cx - rr - 6, cy - rr + 4, cx + rr + 6, cy + rr + 14), fill=(0, 0, 0, int(140 * a)))
    out = Image.alpha_composite(out, sh.filter(ImageFilter.GaussianBlur(H * 0.012)))
    out.paste(c, (int(cx - rr), int(cy - rr)), mask)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dd = ImageDraw.Draw(lay)
    wpx = max(2, int(H * 0.005))
    if anchor is not None:
        ax, ay = anchor[0] * W, anchor[1] * H
        ang = math.atan2(ay - cy, ax - cx)
        ex, ey = cx + rr * math.cos(ang), cy + rr * math.sin(ang)
        dd.line((ex, ey, ax, ay), fill=(*ring, int(230 * a)), width=max(2, int(H * 0.0028)))
        rd = H * 0.007
        dd.ellipse((ax - rd, ay - rd, ax + rd, ay + rd), fill=(*ring, int(255 * a)))
        rd2 = H * 0.02
        dd.ellipse((ax - rd2, ay - rd2, ax + rd2, ay + rd2), outline=(*ring, int(200 * a)), width=max(1, wpx // 2))
    dd.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), outline=(*ring, int(255 * a)), width=wpx)
    return Image.alpha_composite(out, lay)


# ------------------------------------------------------------------ micro content
_TEM = {}


def tem_image(px=640, pairs=40, seed=3):
    """Grayscale TEM-like cross-section of a Mo/Si multilayer: Si substrate at the bottom, `pairs` bilayers
    (Mo ~2.8 nm dark, Si ~4.1 nm bright, period 6.9 nm), thin capping layer, then vacuum/epoxy. Slight waviness,
    interface roughness, grain noise and scan lines. Returns (PIL L image, nm_per_px, stack bounds in px)."""
    key = (px, pairs, seed)
    if key in _TEM:
        return _TEM[key]
    rng = np.random.default_rng(seed)
    period, mo = 6.9, 2.8
    stack = pairs * period
    nm_h = stack * 1.22                      # field of view height in nm
    npx = nm_h / px
    yy, xx = np.mgrid[0:px, 0:px].astype(np.float32)
    z = (px - 1 - yy) * npx                  # nm above the bottom of the view
    sub_top = nm_h * 0.06
    wav = (0.6 * np.sin(xx * npx / 37.0 + 1.3) + 0.35 * np.sin(xx * npx / 11.0) +
           0.25 * rng.standard_normal(px).cumsum()[None, :] * 0.04)
    zr = z - sub_top - wav * (0.2 + 0.8 * np.clip(z / stack, 0, 1))
    inter = rng.standard_normal((px, px)).astype(np.float32)
    inter = np.array(Image.fromarray(((inter * 20) + 128).clip(0, 255).astype(np.uint8)).filter(
        ImageFilter.GaussianBlur(1.2)), dtype=np.float32) / 128 - 1
    ph = (zr + inter * 0.35) % period
    img = np.where(ph < mo, 70.0, 175.0)                    # Mo dark, Si bright (bright-field TEM look)
    # soften interfaces (Si-on-Mo interlayer)
    edge = np.minimum(np.abs(ph - mo), np.minimum(ph, period - ph))
    img = img - 35.0 * np.exp(-(edge / 0.45) ** 2) * (ph >= mo)
    img = np.where(zr < 0, 150.0, img)                      # substrate
    img = np.where(zr > stack, 120.0, img)                  # top: capping then epoxy
    img = np.where((zr > stack) & (zr < stack + 2.5), 95.0, img)
    img = np.where(zr > stack + 2.5, 205.0 - 0.08 * (zr - stack), img)
    img += rng.normal(0, 13, img.shape)                     # shot / grain noise
    img += 6 * np.sin(yy * 2.1)                             # faint scan lines
    g = Image.fromarray(img.clip(0, 255).astype(np.uint8), "L").filter(ImageFilter.GaussianBlur(0.6))
    bounds = (px - 1 - (sub_top + stack) / npx, px - 1 - sub_top / npx)
    _TEM[key] = (g, npx, bounds)
    return _TEM[key]


def _tem_panel(size):
    g, npx, (ytop, ybot) = tem_image(512)
    im = Image.merge("RGB", (g, g, g.point(lambda v: min(255, int(v * 1.04 + 3)))))
    d = ImageDraw.Draw(im)
    # scale bar 50 nm (cyan, lower-left) and pair ticks every 10 pairs on the right
    L50 = 50 / npx
    x0, y0 = 40, 512 - 40
    d.rectangle((x0, y0 - 6, x0 + L50, y0), fill=CYAN)
    d.text((x0, y0 - 46), "50 nm", fill=CYAN, font=font(32))
    per = 6.9 / npx
    for k in range(0, 41, 10):
        y = ybot - k * per
        d.line((512 - 70, y, 512 - 40, y), fill=CYAN, width=3)
        d.text((512 - 112, y - 18), str(k), fill=CYAN, font=mono_font(26), anchor="ra")
    return im.resize((size, size), Image.LANCZOS)


# ------------------------------------------------------------------ shots
def ov_B4_10(img, t, dur, W, H):
    L_ = L(W, H)
    u = t / dur
    # Earth tag (opening third)
    a = fade(t, 0.2, dur * 0.42)
    L_.leader((0.30, 0.68), (0.16, 0.55), a)
    L_.tag((0.30, 0.68), ["地球"], a, anchor="lm")
    # Moon tag + distance
    pm = track(t, dur, [(0.0, (0.79, 0.33)), (0.28, (0.79, 0.33)), (0.55, (0.5, 0.51)), (0.7, (0.5, 0.51))])
    a2 = fade(t, dur * 0.12, dur * 0.66)
    L_.leader((pm[0] - 0.06, pm[1] + 0.2), (pm[0] - 0.012, pm[1] + 0.03), a2)
    L_.tag((pm[0] - 0.06, pm[1] + 0.2), ["月球", "距地球约 38 万 km"], a2, anchor="rt")
    # Golf ball (final third)
    a3 = fade(t, dur * 0.7)
    L_.leader((0.30, 0.30), (0.48, 0.45), a3, prog=ease((u - 0.7) / 0.1))
    L_.tag((0.30, 0.30), ["高尔夫球", "直径约 4 cm"], a3, anchor="rm", accent=ORANGE)
    return L_.compose(img).convert("RGB")


def ov_A0_06(img, t, dur, W, H):
    L_ = L(W, H)
    u = t / dur
    a = fade(t, 0.1)
    n = int(round(5100 * ease(min(1.0, (u - 0.02) / 0.8))))
    L_.panel((0.66, 0.05, 0.95, 0.31), a)
    L_.text((0.69, 0.07), f"{n:,}", 0.11, CYAN, a, kind="mono", glow=0.5)
    L_.text((0.69, 0.22), "家供应商", 0.045, INK, a)
    pn = track(t, dur, [(0.0, (0.49, 0.36)), (1.0, (0.47, 0.39))])
    a2 = fade(t, dur * 0.45)
    L_.leader((pn[0] - 0.08, pn[1] - 0.12), pn, a2, color=INK)
    L_.tag((pn[0] - 0.08, pn[1] - 0.12), ["荷兰 · 整机总装"], a2, anchor="rb", accent=INK)
    L_.text((0.04, 0.79), "各地区数量据 ASML 年报；光点位置为示意", 0.026, INK2, fade(t, 0.3))
    return L_.compose(img).convert("RGB")


def ov_B4_07(img, t, dur, W, H):
    u = t / dur
    a = ease((u - 0.42) / 0.14)
    r = 0.15 + 0.17 * ease((u - 0.42) / 0.3)
    anchor = track(t, dur, [(0.42, (0.3, 0.64)), (0.55, (0.3, 0.62)), (1.0, (0.3, 0.24))])
    if a > 0:
        size = int(2 * r * H)
        img = magnifier(img, (0.66, 0.47), r, _tem_panel(max(64, size)), a, anchor=anchor)
    L_ = L(W, H)
    a2 = fade(t, dur * 0.72)
    L_.tag((0.04, 0.6), ["钼 / 硅 × 40 对", "每对约 7 nm · 电镜截面（示意）"], a2)
    a0 = fade(t, 0.2, dur * 0.45)
    L_.leader((0.18, 0.7), (0.34, 0.56), a0)
    L_.tag((0.18, 0.7), ["多层膜反射镜"], a0, anchor="rm")
    return L_.compose(img).convert("RGB")


def ov_B6_12(img, t, dur, W, H):
    L_ = L(W, H)
    u = t / dur
    a = fade(t, 0.25, dur * 0.6)
    L_.leader((0.2, 0.3), (0.42, 0.42), a)
    L_.tag((0.2, 0.3), ["保护膜 pellicle", "张在金属框上，几乎透明"], a, anchor="rm")
    a1 = fade(t, 0.5, dur * 0.6)
    L_.leader((0.2, 0.78), (0.6, 0.7), a1)
    L_.tag((0.2, 0.78), ["掩模（图形面朝上）"], a1, anchor="rm")
    # final third: side view, gap bracket at the frame's right end
    a2 = fade(t, dur * 0.6)
    if a2 > 0:
        x = 0.8
        y0, y1 = 0.46, 0.53
        L_.line((x, y0), (x, y1), CYAN, a2, 3)
        for y in (y0, y1):
            L_.line((x - 0.012, y), (x + 0.012, y), CYAN, a2, 3)
        L_.tag((x + 0.02, y1 + 0.06), ["间距（示意）"], a2, anchor="rt")
        L_.leader((0.3, 0.3), (0.45, 0.47), a2)
        L_.tag((0.3, 0.3), ["膜厚 13 nm"], a2, anchor="rm")
    return L_.compose(img).convert("RGB")


_PH = {}


def _photon_cells(seed=5):
    if seed not in _PH:
        rnd = random.Random(seed)
        cells = {}
        target = [[14, 23, 17], [19, 20, 26], [22, 15, 18]]
        for i in range(3):
            for j in range(3):
                cells[(i, j)] = [(rnd.random(), rnd.random(), rnd.uniform(0.05, 0.92)) for _ in range(target[i][j])]
        _PH[seed] = cells
    return _PH[seed]


def _photon_panel(size, u):
    im = Image.new("RGB", (size, size), (10, 12, 26))
    d = ImageDraw.Draw(im)
    g = Image.new("RGB", (size, size), (0, 0, 0))
    gd = ImageDraw.Draw(g)
    m = size * 0.1
    cs = (size - 2 * m) / 3
    cells = _photon_cells()
    for (i, j), ph in cells.items():
        x0, y0 = m + j * cs, m + i * cs
        hi = (i, j) == (1, 1)
        d.rectangle((x0, y0, x0 + cs, y0 + cs), outline=(*CYAN,) if hi else (60, 90, 110), width=3 if hi else 1)
        cnt = 0
        for (px, py, t0) in ph:
            if u >= t0:
                cnt += 1
                cx, cy = x0 + cs * (0.1 + 0.8 * px), y0 + cs * (0.1 + 0.8 * py)
                r = size * 0.0075
                d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=VIOLET_L)
                gd.ellipse((cx - 3 * r, cy - 3 * r, cx + 3 * r, cy + 3 * r), fill=VIOLET)
        d.text((x0 + cs - 6, y0 + 4), str(cnt), fill=CYAN if hi else INK2, font=mono_font(int(size * (0.07 if hi else 0.05))),
               anchor="ra")
    im = Image.composite(im, im, Image.new("L", im.size, 255))
    from PIL import ImageChops
    im = ImageChops.add(im, g.filter(ImageFilter.GaussianBlur(size * 0.012)))
    d = ImageDraw.Draw(im)
    d.text((size / 2, size - m * 0.55), "每格 1 nm²", fill=INK, font=font(int(size * 0.055)), anchor="mm")
    return im


def ov_B9_05(img, t, dur, W, H):
    u = t / dur
    a = ease(u / 0.15)
    size = int(0.56 * H)
    img = magnifier(img, (0.25, 0.43), 0.28, _photon_panel(max(64, size), clamp01(u / 0.92)), a, anchor=(0.58, 0.62))
    L_ = L(W, H)
    a1 = fade(t, 0.3)
    L_.tag((0.53, 0.08), ["1 个 EUV 光子 ≈ 92 eV"], a1, accent=VIOLET)
    a2 = fade(t, dur * 0.55)
    L_.tag((0.53, 0.2), ["剂量 ≈ 20 光子 / nm²（示意）", "落点随机 → 线条边缘起伏"], a2)
    return L_.compose(img).convert("RGB")


def ov_B8_17(img, t, dur, W, H):
    L_ = L(W, H)
    u = t / dur
    cols = [("188", "场 / 片", 0.0, 0.8, 188), ("185+", "片 / 小时", 0.3, 0.7, 185), ("3.4 万+", "次曝光 / 小时", 0.55, 0.8, 34780)]
    for k, (final, unit, s0, s1, val) in enumerate(cols):
        a = fade(t, dur * s0)
        if a <= 0:
            continue
        x = 0.03 + k * 0.17                       # R3: tighter row so card 3 no longer covers the wafer stack
        L_.panel((x, 0.05, x + 0.16, 0.27), a)
        p = ease((u - s0) / max(0.05, s1 - s0))
        if k == 0:
            s = str(int(round(188 * p)))
        elif k == 1:
            s = str(int(round(185 * p))) + ("+" if p >= 1 else "")
        else:
            v = int(round(val * p))
            s = final if p >= 1 else f"{v:,}"
        L_.text((x + 0.015, 0.07), s, 0.075, VIOLET_L if k == 0 else CYAN if k == 1 else INK, a,
                kind="mono" if s.replace("+", "").replace(",", "").replace(".", "").isdigit() else "sans", glow=0.4)
        L_.text((x + 0.015, 0.19), unit, 0.036, INK2, a)
    a0 = fade(t, 0.3)
    L_.leader((0.11, 0.27), (0.26, 0.52), a0, color=VIOLET_L)
    a1 = fade(t, dur * 0.3)
    L_.leader((0.28, 0.27), (0.62, 0.38), a1)
    return L_.compose(img).convert("RGB")


def ov_A2_08(img, t, dur, W, H):
    """R3: tags on the two 3D waves (anchored), the equal-length bracket and the 14x count."""
    L_ = L(W, H)
    g = _anchor("A2_08", t, "w193", (0.25, 0.32))
    v = _anchor("A2_08", t, "w135", (0.7, 0.55))
    a = fade(t, 0.1)
    gy = max(0.2, g[1] - 0.12)                       # R4: never above the top edge (R3 frame 3 cropped it)
    L_.leader((g[0] - 0.02, gy - 0.02), g, a, color=INK2)
    L_.tag((g[0] - 0.02, gy), ["193 nm", "上一代光刻光（深紫外）"], a, size=0.05, color=INK, accent=INK2, anchor="lb")
    a2 = fade(t, dur * 0.3)
    L_.leader((v[0] + 0.02, v[1] + 0.2), v, a2, color=VIOLET_L)
    L_.tag((v[0] + 0.02, v[1] + 0.2), ["13.5 nm", "极紫外 EUV"], a2, size=0.05, color=VIOLET_L, accent=VIOLET, anchor="lt")
    a3 = fade(t, dur * 0.72)
    l = _anchor("A2_08", t, "span_l", (0.12, 0.66))
    r = _anchor("A2_08", t, "span_r", (0.88, 0.66))
    if a3 > 0:
        L_.line(l, r, INK2, a3, 2)
        L_.tag((0.66, 0.06), ["同样长度里", "13.5 nm 短约 14 倍"], a3, size=0.05, accent=VIOLET)   # R4: upper right
    return L_.compose(img).convert("RGB")


def ov_A2_03(img, t, dur, W, H):
    """R3: the formula sits on the out-of-focus machine (no full-screen panel); lambda points at the violet beam,
    NA at a projection mirror's light cone."""
    L_ = L(W, H)
    u = t / dur
    L_.panel((0.14, 0.27, 0.86, 0.55), fade(t, 0.0), alpha=0.38, radius=18)     # local backing for the formula only
    terms = [("CD", INK, "能画多细", 0.0), ("=", INK2, None, 0.06), ("k₁", INK2, "工艺因子", 0.12),
             ("·", INK2, None, 0.16), ("λ", VIOLET_L, "光的波长", 0.22), ("/", INK2, None, 0.3),
             ("NA", CYAN, "数值孔径", 0.36)]
    size = 0.13
    px = int(size * H)
    f = serif_font(px)
    ws = [text_bbox(L_.d, (0, 0), s, f)[2] + 0.03 * W for s, *_ in terms]
    x = 0.5 * W - sum(ws) / 2
    yb = 0.44 * H
    pos = {}
    for (s, col, name, t0), w in zip(terms, ws):
        a = fade(u * dur, t0 * dur, f=0.5)
        draw_text(L_.d, (x + w / 2, yb), s, f, fill=(*col, int(255 * a)), anchor="ms")
        if col in (VIOLET_L, CYAN):
            draw_text(L_.g, (x + w / 2, yb), s, f, fill=(*col, int(160 * a)), anchor="ms")
        if name:
            L_.text(((x + w / 2) / W, 0.49), name, 0.038, col if col != INK2 else INK, a, anchor="mt")
        pos[s] = ((x + w / 2) / W, 0.29)
        x += w
    # leaders from the symbols to the real things behind
    a1 = fade(t, dur * 0.3)
    bm = _anchor("A2_03", t, "beam", (0.4, 0.2))
    L_.leader(pos["λ"], (min(0.95, max(0.05, bm[0])), max(0.06, min(0.2, bm[1]))), a1, color=VIOLET_L)
    a2 = fade(t, dur * 0.4)
    mr = _anchor("A2_03", t, "mirror", (0.7, 0.8))
    L_.leader((pos["NA"][0], 0.55), (min(0.95, max(0.05, mr[0])), max(0.6, min(0.8, mr[1]))), a2, color=CYAN)
    L_.tag((min(0.8, max(0.05, mr[0])) + 0.02, max(0.6, min(0.8, mr[1])) - 0.02), ["镜子收光的锥角 → NA"], a2,
           size=0.034, accent=CYAN)
    a3 = fade(t, dur * 0.72)
    kx = pos["k₁"][0]                                    # R5: own leader from k₁ (R4 read as attached to NA)
    L_.leader((kx, 0.53), (kx, 0.6), a3, color=INK2)
    L_.tag((max(0.04, kx - 0.04), 0.6), ["k₁ 的物理极限：0.25"], a3, size=0.045, accent=INK2)
    return L_.compose(img).convert("RGB")


OVERLAYS = {"B4_10": ov_B4_10, "A0_06": ov_A0_06, "B4_07": ov_B4_07, "B6_12": ov_B6_12, "B9_05": ov_B9_05,
            "B8_17": ov_B8_17, "A2_08": ov_A2_08, "A2_03": ov_A2_03}

# B4_07: the storyboard label ("比例尺 nm → pm · 原子排布示意") no longer matches the TEM magnifier
NO_STORYBOARD_LABELS = {"B4_07", "A0_06"}   # A0_06 (R3): the counter now owns the upper-right zone
