"""B5 2D shots: the pupil as a mosaic that re-forms (F34), the light ledger staying level while the
pupil changes (F34), and an SEM-style triptych pairing patterns with illumination shapes."""
import math
import random

from PIL import Image, ImageDraw, ImageFilter

from mograph import CYAN, INK, INK2, VIOLET, Canvas, ease, ease_out, fade, seg, shot

# ---- pupil shapes in unit coordinates (radius 1) -------------------------------------------
STEP = 0.075                                    # tile pitch in unit radii
N_TILES = 360                                   # >= the largest shape's cell count


def _cells():
    n = int(1 / STEP)
    return [(i * STEP, j * STEP) for i in range(-n, n + 1) for j in range(-n, n + 1)
            if math.hypot(i * STEP, j * STEP) <= 0.98]


def _shape(name):
    def inside(x, y):
        r = math.hypot(x, y)
        if name == "disc":
            return r <= 0.72
        if name == "annulus":
            return 0.6 <= r <= 0.95
        if name == "dipole":
            return min(math.hypot(x, y - 0.6), math.hypot(x, y + 0.6)) <= 0.36
        if name == "quad":
            d = 0.62 / math.sqrt(2)
            return min(math.hypot(x - sx * d, y - sy * d) for sx in (-1, 1) for sy in (-1, 1)) <= 0.27
        if name == "free":                     # an asymmetric, optimiser-looking freeform
            th = math.degrees(math.atan2(y, x)) % 360
            return (math.hypot(x - 0.5, y - 0.28) <= 0.3 or math.hypot(x + 0.46, y + 0.38) <= 0.26
                    or (0.74 <= r <= 0.93 and 95 <= th <= 205) or (0.2 <= r <= 0.34 and 230 <= th <= 330))
        raise KeyError(name)
    pts = [p for p in _cells() if inside(*p)]
    # every shape uses the same N tiles: small shapes stack spare tiles on cells already lit
    # (invisible overlap) so every shape reads solid and tiles appear to split or merge as it morphs
    pts = sorted(pts, key=lambda p: (round(math.atan2(p[1], p[0]) * 6), math.hypot(*p)))
    return [pts[int(k * len(pts) / N_TILES)] for k in range(N_TILES)]


SHAPES = ["disc", "annulus", "dipole", "quad", "free"]
LABELS = {"disc": "圆盘", "annulus": "圆环", "dipole": "两极", "quad": "四极", "free": "自由形状"}
_CACHE = {}


def shape_pts(name):
    if name not in _CACHE:
        _CACHE[name] = _shape(name)
    return _CACHE[name]


def pupil(c, t, cx, cy, R, a, schedule, tile=None, labels=True, label_y=None):
    """Draw the tile mosaic at time t. schedule: [(t_start_morph, shape)], first entry shape at t=0."""
    tile = tile or R * STEP * 0.82
    cur, nxt, p = schedule[0][1], None, 0.0
    for k in range(1, len(schedule)):
        t0, name = schedule[k]
        if t >= t0:
            cur = name
        elif t >= t0 - 0.9:
            nxt, p = name, ease(seg(t, t0 - 0.9, t0))
            break
    A = shape_pts(cur)
    Bp = shape_pts(nxt) if nxt else A
    c.circle((cx, cy), R * 1.02, outline=INK2, width=2, a=a * 0.6)
    for i in range(N_TILES):
        # each tile starts its slide slightly later than the previous: a ripple, not a jump
        q = ease(min(1.0, max(0.0, p * 1.6 - 0.6 * i / N_TILES)))
        x = A[i][0] + (Bp[i][0] - A[i][0]) * q
        y = A[i][1] + (Bp[i][1] - A[i][1]) * q
        X, Y = cx + x * R, cy - y * R
        c.rect((X - tile / 2, Y - tile / 2, X + tile / 2, Y + tile / 2), fill=(176, 146, 255), a=a * 0.95,
               glow=True, radius=tile * 0.18)
    if labels:
        show = nxt if (nxt and p > 0.5) else cur
        c.text((cx, label_y or cy + R + 70), LABELS[show], 40, INK, a, anchor="mm")
    return cur


@shot("B5_06")
def mosaic(t, dur, W, H):
    c = Canvas(W, H)
    a = fade(t, 0.0, dur, dur, 0.3)
    sched = [(0, "disc"), (2.4, "annulus"), (4.0, "dipole"), (5.6, "quad"), (7.2, "free")]
    appear = ease_out(seg(t, 0.0, 1.0))
    pupil(c, t, 960, 500, 360 * (0.85 + 0.15 * appear), a * appear, sched)
    c.text((960, 1010), "光瞳（示意）：每一小块光斑来自一片可转动的小镜片（F34）", 22, INK2, a, anchor="mm")
    return c.finish(glow_radius=10, glow_gain=0.6)


@shot("B5_07")
def ledger_level(t, dur, W, H):
    c = Canvas(W, H)
    a = fade(t, 0.0, dur, dur, 0.3)
    sched = [(0, "disc"), (1.6, "annulus"), (3.0, "dipole"), (4.4, "quad")]
    c.rect((140, 200, 900, 880), outline=INK2, width=2, a=a * 0.5, radius=16)
    pupil(c, t, 520, 520, 250, a, sched, label_y=820)
    # ledger bar on the right: same height whatever the shape
    x, w, top, bot = 1260, 140, 260, 860
    level = 360
    c.rect((x, top, x + w, bot), outline=INK2, width=3, a=a, radius=8)
    c.rect((x + 6, level, x + w - 6, bot - 6), fill=VIOLET, a=a * 0.8, glow=True, radius=6)
    for k in range(0, 1500, 34):                                  # dashed level line across both panels
        if k / 1500 < ease_out(seg(t, 0.3, 1.4)):
            c.line((300 + k, level), (300 + k + 18, level), CYAN, 2, a * 0.8)
    pulse = 0.5 + 0.5 * math.cos(2 * math.pi * ((t - 1.6) % 1.4) / 1.4) if t > 1.0 else 0.0
    c.text((x + w + 40, level + 4), "光量不变", 36, CYAN, a * (0.7 + 0.3 * pulse), anchor="lm", weight_glow=True)
    c.text((x + w / 2, bot + 50), "光的账本", 28, INK2, a, anchor="mm")
    c.text((960, 120), "改变照明形状 · 几乎不损失光", 44, INK, a * ease(seg(t, 0.4, 1.0)), anchor="mm")
    c.text((960, 1010), "ZEISS：照明效率接近 100%（F34）", 22, INK2, a, anchor="mm")
    return c.finish(glow_radius=10, glow_gain=0.9)


def _sem_panel(w, h, kind, sharp, seed):
    """A grey SEM-like tile: lines or holes, with grain; blurred edges when the illumination is wrong."""
    rnd = random.Random(seed)
    im = Image.new("L", (w, h), 38)
    d = ImageDraw.Draw(im)
    if kind == "lines":
        pitch = h / 9
        for k in range(9):
            y0 = k * pitch + pitch * 0.28
            pts_top, pts_bot = [], []
            for x in range(0, w + 8, 8):
                jitter = rnd.uniform(-1, 1) * (1.0 if sharp else 3.5)
                pts_top.append((x, y0 + jitter))
                pts_bot.append((x, y0 + pitch * 0.44 + rnd.uniform(-1, 1) * (1.0 if sharp else 3.5)))
            d.polygon(pts_top + pts_bot[::-1], fill=168)
            d.line(pts_top, fill=228, width=2)                 # SEM edge brightening
            d.line(pts_bot, fill=228, width=2)
    else:
        pitch = w / 7
        for i in range(7):
            for j in range(int(h / pitch) + 1):
                cx, cy = (i + 0.5) * pitch, (j + 0.5) * pitch
                r = pitch * 0.26 + rnd.uniform(-1, 1) * (0.6 if sharp else 3)
                d.ellipse((cx - r - 3, cy - r - 3, cx + r + 3, cy + r + 3), fill=210)
                d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=18)
    if not sharp:
        im = im.filter(ImageFilter.GaussianBlur(w / 70))
    noise = Image.effect_noise((w, h), 26).point(lambda v: v - 128 + 128)
    im = Image.blend(im, noise, 0.18)
    return im.convert("RGB")


@shot("B5_08")
def triptych(t, dur, W, H):
    c = Canvas(W, H)
    a = fade(t, 0.0, dur, dur, 0.3)
    panels = [("lines", "dipole", True, "横线 × 两极 → 锐利"),
              ("lines", "disc", False, "横线 × 圆盘 → 发糊"),
              ("holes", "quad", True, "孔阵 × 四极 → 清晰")]
    pw, ph = 520, 520
    for k, (kind, shape, sharp, cap) in enumerate(panels):
        on = ease(seg(t, 0.4 + 1.1 * k, 1.2 + 1.1 * k))
        if on <= 0:
            continue
        x0 = 150 + k * 560
        y0 = 230
        im = _sem_panel(int(c.px(pw)), int(c.px(ph)), kind, sharp, seed=k)
        if on < 1:
            im = Image.blend(Image.new("RGB", im.size, (8, 10, 16)), im, on)
        c.img.paste(im, (int(c.px(x0)), int(c.px(y0))))
        c.rect((x0, y0, x0 + pw, y0 + ph), outline=INK2, width=2, a=a * on)
        # pupil icon in the corner
        icx, icy, ir = x0 + pw - 62, y0 + 62, 44
        c.circle((icx, icy), ir + 4, fill=(8, 10, 16), a=a * on * 0.9)
        for (px, py) in shape_pts(shape)[::3]:
            c.circle((icx + px * ir, icy - py * ir), 3.2, fill=(196, 170, 255), a=a * on)
        c.circle((icx, icy), ir + 4, outline=INK2, width=1, a=a * on)
        c.line((x0 + 30, y0 + ph - 34), (x0 + 130, y0 + ph - 34), INK, 3, a * on)       # scale bar
        c.text((x0 + 80, y0 + ph - 54), "50 nm", 18, INK, a * on, anchor="mm")
        col = CYAN if sharp else (255, 138, 61)
        c.text((x0 + pw / 2, y0 + ph + 60), cap, 32, col, a * on, anchor="mm")
    c.text((960, 120), "图案 × 照明 匹配（示意）", 40, INK, a * ease(seg(t, 0.0, 0.6)), anchor="mm")
    return c.finish(glow_radius=6, glow_gain=0.6)
