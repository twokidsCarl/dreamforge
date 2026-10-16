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


@shot("A0_03")
def logistics(t, dur, W, H):
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


# ---- SEM dive into the chip ----------------------------------------------------------------------
_CIRC = None


@shot("A0_09")
def chip_dive(t, dur, W, H):
    global _CIRC
    if _CIRC is None:
        _CIRC = Image.open(CIRCUIT).convert("L")
    c = Canvas(W, H)
    a = fade(t, 0.0, dur, dur, 0.3)
    S = _CIRC.size[0]
    z = ease(seg(t, 0.0, dur - 1.2))
    span = S * (0.9 * (0.06 / 0.9) ** z)                          # crop window shrinks ~15x
    cx, cy = S * 0.42, S * 0.37
    box = (cx - span / 2, cy - span * 9 / 32, cx + span / 2, cy + span * 9 / 32)
    crop = _CIRC.crop(tuple(int(v) for v in box)).resize((W, H), Image.BICUBIC)
    sem = ImageOps.autocontrast(crop.filter(ImageFilter.GaussianBlur(max(0.6, 2.4 * (1 - z)) * c.k)))
    sem = Image.eval(sem, lambda v: 52 + int(v * 0.68))
    sem = Image.blend(sem, Image.effect_noise((W, H), 30), 0.18)
    rgb = Image.merge("RGB", (sem, sem, sem))
    # violet "pen strokes" light the transistor rows block by block in the final third
    paint = ease(seg(t, dur - 2.0, dur - 0.3))
    if paint > 0:
        m = Image.new("L", (W, H), 0)
        md = ImageDraw.Draw(m)
        rows = 9
        for r in range(rows):
            p = max(0.0, min(1.0, paint * rows * 0.6 - r * 0.45))
            md.rectangle((0, int(H * r / rows), int(W * p), int(H * (r + 1) / rows)), fill=255)
        m = Image.composite(crop, Image.new("L", (W, H), 0), m)
        vio = Image.merge("RGB", (m.point(lambda v: int(v * 0.7)), m.point(lambda v: int(v * 0.5)), m))
        rgb = ImageChops.add(rgb, vio)
        c.glow.paste(vio.point(lambda v: int(v * 0.6)))
    c.img = rgb
    c.d = ImageDraw.Draw(c.img, "RGBA")
    c.g = ImageDraw.Draw(c.glow)
    jumps = (0.33, 0.66)                                          # scan-line redraw at each scale jump
    for j in jumps:
        sl = seg(z, j - 0.06, j + 0.06)
        if 0 < sl < 1:
            c.line((0, 1080 * sl), (1920, 1080 * sl), INK, 2, a)
    c.rect((80, 990, 280, 998), fill=INK, a=a)
    c.text((1880, 60), "SEM 风格示意", 22, INK, a, anchor="ra")
    return c.finish(glow_radius=6, glow_gain=1.0)
