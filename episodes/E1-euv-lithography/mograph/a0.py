"""A0 2D shots: the logistics chain (F17), 5100 suppliers converging (F50), and the dive into a chip
under the SEM (illustrative layout)."""
import json
import math
import os
import random

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageOps

from mograph import CYAN, INK, INK2, VIOLET, Canvas, ease, ease_out, fade, seg, shot

HERE = os.path.dirname(__file__)
CIRCUIT = os.path.join(os.path.dirname(HERE), "blender", "textures", "circuit.png")
WOOD = (196, 160, 110)


# ---- icons ---------------------------------------------------------------------------------------
def crate(c, x, y, s, a):
    c.rect((x - s, y - s, x + s, y + s), outline=WOOD, width=2, a=a)
    c.line((x - s, y - s), (x + s, y + s), WOOD, 1, a * 0.7)
    c.line((x - s, y + s), (x + s, y - s), WOOD, 1, a * 0.7)


def container(c, x, y, s, a):
    c.rect((x - 2.2 * s, y - s, x + 2.2 * s, y + s), fill=(40, 90, 130), outline=(90, 150, 190), width=1, a=a)
    for k in range(1, 6):
        xx = x - 2.2 * s + k * 4.4 * s / 6
        c.line((xx, y - s), (xx, y + s), (90, 150, 190), 1, a * 0.6)


def plane(c, x, y, s, a, col=INK):
    pts = [(x + 3.0 * s, y), (x + 2.2 * s, y - 0.35 * s), (x - 2.6 * s, y - 0.35 * s), (x - 3.2 * s, y - 1.2 * s),
           (x - 3.5 * s, y - 1.2 * s), (x - 3.1 * s, y), (x - 3.5 * s, y + 0.3 * s), (x - 2.6 * s, y + 0.35 * s),
           (x + 2.2 * s, y + 0.35 * s)]
    c.d.polygon([(c.px(px), c.px(py)) for px, py in pts], fill=(*col, int(255 * a)))
    wing = [(x + 0.6 * s, y), (x - 0.6 * s, y + 2.4 * s), (x - 1.2 * s, y + 2.4 * s), (x - 0.4 * s, y)]
    c.d.polygon([(c.px(px), c.px(py)) for px, py in wing], fill=(*col, int(255 * a)))


def truck(c, x, y, s, a):
    c.rect((x - 3.0 * s, y - 0.8 * s, x + 1.2 * s, y + 0.8 * s), fill=(150, 156, 170), a=a)
    c.rect((x + 1.4 * s, y - 0.6 * s, x + 2.4 * s, y + 0.8 * s), fill=(200, 204, 214), a=a, radius=s * 0.2)
    c.circle((x + 2.45 * s, y + 0.3 * s), 0.18 * s, fill=(255, 240, 200), a=a, glow=True)


def logistics_2d(t, dur, W, H):
    c = Canvas(W, H)
    a = fade(t, 0.0, dur, dur, 0.3)
    # 1) one crate -> 250+ crates (25 x 10 grid)
    g1 = ease(seg(t, 0.2, 1.6))
    c1 = 1 - ease(seg(t, 2.0, 2.8))
    if c1 > 0.02:
        for i in range(252 if g1 > 0.05 else 1):
            col, row = i % 25, i // 25
            x = 960 + (col - 12) * 52 * g1
            y = 560 + (row - 4.5) * 52 * g1
            x += (1 - c1) * (960 + ((i % 43) % 9 - 4) * 130 - x)          # gather into the containers
            y += (1 - c1) * (500 + ((i % 43) // 9 - 2) * 80 - y)
            crate(c, x, y, 18 + 60 * (1 - g1), a * (0.5 + 0.5 * c1))
    # 2) 43 containers (9 x 5)
    g2 = ease(seg(t, 2.5, 3.1))
    c2 = 1 - ease(seg(t, 3.9, 4.6))
    if g2 > 0 and c2 > 0.02:
        for i in range(43):
            x = 960 + (i % 9 - 4) * 130
            y = 500 + (i // 9 - 2) * 80
            k = i % 4
            x += (1 - c2) * (300 - x)
            y += (1 - c2) * (330 + 110 * k - y)
            container(c, x, y, 22 * (0.5 + 0.5 * c2), a * g2)
    # 3) several freighters fly to Seattle
    g3 = ease(seg(t, 4.2, 4.7))
    fly = ease(seg(t, 4.5, 6.2))
    land = 1 - ease(seg(t, 6.1, 6.6))
    if g3 > 0 and land > 0.02:
        for k in range(4):
            x = 300 + 1250 * fly + 40 * k
            y = 330 + 110 * k - 160 * math.sin(math.pi * fly)
            plane(c, x, y, 34, a * g3 * land)
        c.text((1600, 760), "西雅图", 30, INK2, a * g3 * fly, anchor="mm")
    # 4) twenty trucks along a thin line to Oregon
    g4 = ease(seg(t, 6.2, 6.7))
    drive = ease(seg(t, 6.4, dur - 0.3))
    if g4 > 0:
        c.line((360, 760), (1600, 760), INK2, 2, a * g4)
        c.text((360, 810), "西雅图", 28, INK2, a * g4, anchor="mm")
        c.text((1600, 810), "俄勒冈", 30, INK, a * g4, anchor="mm", weight_glow=drive > 0.95)
        for k in range(20):
            x = 380 + 1150 * drive - 62 * k
            if x > 330:
                truck(c, x, 730, 16, a * g4)
    items = [("250+ 板条箱", 0.6), ("43 个集装箱", 2.6), ("多架货机 → 西雅图", 4.3), ("20 辆卡车 → 俄勒冈", 6.3)]
    for k, (txt, t0) in enumerate(items):
        c.text((1860, 90 + 48 * k), txt, 34, INK, a * ease(seg(t, t0, t0 + 0.4)), anchor="ra")
    c.text((80, 1030), "2023 年 12 月 · 首台 High-NA EUV 交付（F17）", 20, INK2, a, anchor="lm")
    return c.finish(glow_radius=8, glow_gain=0.7)


# ---- 5100 suppliers ----------------------------------------------------------------------------
_WORLD = None
_PTS = None


def _world():
    global _WORLD
    if _WORLD is None:
        _WORLD = json.load(open(os.path.join(HERE, "data", "world110.json")))["polys"]
    return _WORLD


def _inside(lon, lat, poly):
    ins = False
    j = len(poly) - 1
    for i in range(len(poly)):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > lat) != (yj > lat) and lon < (xj - xi) * (lat - yi) / (yj - yi + 1e-12) + xi:
            ins = not ins
        j = i
    return ins


def _supplier_points(n=5100):
    """Illustrative positions: land points, denser in Europe, North America and East Asia."""
    global _PTS
    if _PTS is None:
        rnd = random.Random(50)
        hubs = [(8, 50, 9, 2.4), (-95, 38, 20, 1.0), (125, 32, 14, 1.2), (5, 52, 3, 1.6)]
        polys = _world()
        bbox = [(min(p[0] for p in pl), max(p[0] for p in pl), min(p[1] for p in pl), max(p[1] for p in pl))
                for pl in polys]
        pts = []
        while len(pts) < n:
            hx, hy, sd, wgt = rnd.choices(hubs, weights=[h[3] for h in hubs])[0]
            lon, lat = rnd.gauss(hx, sd), rnd.gauss(hy, sd * 0.6)
            for pl, (x0, x1, y0, y1) in zip(polys, bbox):
                if x0 <= lon <= x1 and y0 <= lat <= y1 and _inside(lon, lat, pl):
                    pts.append((lon, lat))
                    break
        _PTS = pts
    return _PTS


@shot("A0_06")
def suppliers(t, dur, W, H):
    c = Canvas(W, H, bg=(6, 8, 14))
    a = fade(t, 0.0, dur, dur, 0.3)
    z = 1 + 1.6 * ease(seg(t, 0.4, dur - 0.3))                   # slow push toward Europe
    home = (5.4, 51.4)                                             # Veldhoven (illustrative point)
    def P(lon, lat):  # noqa: E306
        x = 960 + (lon - home[0] * (z - 1) / z) * 5.0 * z
        y = 560 - (lat - home[1] * (z - 1) / z) * 5.0 * z
        return x, y
    for pl in _world():
        pts = [P(*p) for p in pl]
        c.d.polygon([(c.px(x), c.px(y)) for x, y in pts], fill=(22, 28, 44, int(255 * a)),
                    outline=(40, 52, 76, int(255 * a)))
    pts = _supplier_points()
    lit = int(len(pts) * ease(seg(t, 0.2, 2.2)))
    conv = ease(seg(t, 2.4, 3.5))
    hx, hy = P(*home)
    for i, (lon, lat) in enumerate(pts[:lit]):
        x, y = P(lon, lat)
        if conv > 0:
            q = min(1.0, conv * 1.4 - (i % 7) * 0.05)
            q = max(0.0, q)
            mx, my = (x + hx) / 2, min(y, hy) - 80 * (abs(x - hx) / 600)
            bx = (1 - q) ** 2 * x + 2 * (1 - q) * q * mx + q * q * hx  # along a thin arc
            by = (1 - q) ** 2 * y + 2 * (1 - q) * q * my + q * q * hy
            x, y = bx, by
        c.d.point((c.px(x), c.px(y)), fill=(*CYAN, int(230 * a)))
        if i % 9 == 0:
            c.g.point((c.px(x), c.px(y)), fill=tuple(int(v * a) for v in CYAN))
    flash = ease(seg(t, 3.3, 3.5)) * (1 - ease(seg(t, 3.6, dur)))
    c.circle((hx, hy), 6 + 30 * flash, fill=VIOLET, a=a * (0.6 + 0.4 * flash), glow=True)
    c.text((960, 110), f"{min(5100, int(5100 * ease(seg(t, 0.2, 2.2)))):,} 家供应商", 48, INK, a, anchor="mm",
           weight_glow=True)
    c.text((1880, 1030), "光点位置为示意 · F50", 18, INK2, a, anchor="rm")
    return c.finish(glow_radius=6, glow_gain=1.4)


# ---- dive into a real chip (optical micrographs, CC0) ---------------------------------------------
DIES = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(HERE))), "shared", "assets", "dies")
_IMG = {}


def _die(name):
    if name not in _IMG:
        p = os.path.join(DIES, name + ".jpg")
        _IMG[name] = Image.open(p).convert("RGB") if os.path.exists(p) else Image.open(CIRCUIT).convert("RGB")
    return _IMG[name]


def _zoom(img, cx, cy, z, W, H):
    """Crop a W:H window centred on (cx, cy) (fractions) at zoom z (1 = the whole width) and scale to W x H."""
    iw, ih = img.size
    w = iw / z
    h = w * H / W
    x0 = min(max(0, cx * iw - w / 2), iw - w)
    y0 = min(max(0, cy * ih - h / 2), ih - h)
    return img.crop((int(x0), int(y0), int(x0 + w), int(y0 + h))).resize((W, H), Image.LANCZOS)


def chip_dive(t, dur, W, H, paint=(0.75, 0.55, 1.0)):
    """A0_09 / D_02: push into a real die (Intel Xeon, then a Zen 5 core macro with its own diffraction
    colours); the transistor rows are lit up stroke by stroke."""
    c = Canvas(W, H)
    a = fade(t, 0.0, dur, dur, 0.3)
    z1 = ease(seg(t, 0.0, dur * 0.62))
    far = _zoom(_die("xeon_poly"), 0.62, 0.48, 1.05 * (5.0 ** z1), W, H)
    mix = ease(seg(t, dur * 0.48, dur * 0.66))
    if mix > 0:
        z2 = ease(seg(t, dur * 0.48, dur))
        near = _zoom(_die("zen5_ccd"), 0.4, 0.66, 1.6 * (2.2 ** z2), W, H)     # the regular cell array
        img = Image.blend(far, near, mix)
    else:
        img = far
    p = ease(seg(t, dur - 1.8, dur - 0.2))
    if p > 0:                                                      # strokes of light, row by row
        m = Image.new("L", (W, H), 0)
        md = ImageDraw.Draw(m)
        rows = 8
        for r in range(rows):
            q = max(0.0, min(1.0, p * rows * 0.55 - r * 0.4))
            md.rectangle((0, int(H * r / rows), int(W * q), int(H * (r + 1) / rows)), fill=255)
        m = m.filter(ImageFilter.GaussianBlur(H / 40))                  # feathered stroke edges
        lum = img.convert("L").point(lambda v: max(0, v - 150) * 2)  # only the brightest metal lights up
        lit = Image.merge("RGB", tuple(lum.point(lambda v, k=k: int(v * k)) for k in paint))
        lit = Image.composite(lit, Image.new("RGB", (W, H)), m)
        dim = Image.composite(img.point(lambda v: int(v * 0.55)), img, m)  # the lit rows darken a little first
        img = ImageChops.screen(dim, lit)
        c.glow.paste(lit.point(lambda v: int(v * 0.5)))
    c.img = Image.blend(Image.new("RGB", (W, H)), img, a)
    c.d = ImageDraw.Draw(c.img, "RGBA")
    c.g = ImageDraw.Draw(c.glow)
    c.text((1880, 1050), "芯片显微照片：Fritzchens Fritz（CC0）", 16, INK2, a, anchor="rm")
    return c.finish(glow_radius=8, glow_gain=0.9, vignette=True)


@shot("A0_09")
def a0_chip_dive(t, dur, W, H):
    return chip_dive(t, dur, W, H)
