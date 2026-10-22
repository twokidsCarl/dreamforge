"""A3 2D shots: three hard problems as cards, air eating the beam, and the light ledger
introduced on the right of the frame."""
import glob
import math
import os
import random

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter

from mograph import CYAN, INK, INK2, RENDERS, VIOLET, Canvas, ease, ease_out, fade, seg, shot

CARD = (30, 34, 48)


def card(c, cx, cy, flip, a, num, title=None, w=440, h=600):
    """A card that flips around its vertical axis: back shows the number, front the title."""
    sx = abs(math.cos(math.pi * flip))
    hw = w / 2 * max(0.02, sx)
    front = flip > 0.5
    c.rect((cx - hw, cy - h / 2, cx + hw, cy + h / 2), fill=CARD if not front else (40, 44, 62),
           outline=(70, 76, 100) if not front else VIOLET, width=3, a=a, radius=18)
    if sx > 0.3:
        if not front:
            c.text((cx, cy), str(num), int(160 * sx), (70, 76, 100), a, anchor="mm")
        elif title:
            c.text((cx - w / 2 + 40, cy + h / 2 - 40), f"难题 {num} / 3", 28, INK, a * sx * 0.8, anchor="lm")


@shot("A3_01")
def three_cards(t, dur, W, H):
    c = Canvas(W, H, bg=(0, 0, 0))
    a = fade(t, 0.0, dur, dur, 0.3)
    c.text((960, 150), "三道难题", 72, INK, a * ease(seg(t, 0.2, 0.9)), anchor="mm", weight_glow=True)
    for k in range(3):
        card(c, 480 + 480 * k, 600, 0.0, a * ease(seg(t, 0.6 + 0.2 * k, 1.2 + 0.2 * k)), k + 1)
    return c.finish(glow_radius=10, glow_gain=0.7)


@shot("A3_02")
def problem1(t, dur, W, H):
    c = Canvas(W, H, bg=(0, 0, 0))
    a = fade(t, 0.0, dur, dur, 0.3)
    flip = ease(seg(t, 0.2, 1.0))
    card(c, 960, 520, flip, a, 1, title=True, w=1500, h=640)
    if flip > 0.5:
        on = ease(seg(t, 0.9, 1.6))
        # a log wavelength axis, 10-1000 nm: colour only across visible light (400-800 nm, ZEISS's range);
        # 193 nm (DUV) and 13.5 nm (EUV) sit far out in the ultraviolet, where the eye sees nothing
        x0, x1, y = 300, 1620, 560

        def X(nm):
            return x0 + (x1 - x0) * (math.log10(nm) - 1.0) / 2.0

        def vis_rgb(nm):                                           # rough spectral colour, for display only
            stops = [(400, (110, 0, 160)), (450, (40, 40, 255)), (490, (0, 190, 255)), (530, (40, 230, 60)),
                     (580, (250, 230, 0)), (620, (255, 120, 0)), (700, (220, 0, 0)), (800, (90, 0, 0))]
            for (l0, c0), (l1, c1) in zip(stops, stops[1:]):
                if l0 <= nm <= l1:
                    u = (nm - l0) / (l1 - l0)
                    return tuple(int(c0[i] + (c1[i] - c0[i]) * u) for i in range(3))
            return (40, 40, 50)
        c.line((x0, y + 52), (x1, y + 52), INK2, 2, a * on)
        for nm in (10, 100, 1000):
            c.line((X(nm), y + 46), (X(nm), y + 60), INK2, 2, a * on)
            c.text((X(nm), y + 88), f"{nm} nm", 26, INK, a * on * 0.8, anchor="mm")
        c.rect((x0, y - 40, X(400), y + 40), fill=(22, 24, 34), a=a * on)          # ultraviolet: invisible
        for i in range(60):
            nm0 = 400 * (2.0 ** (i / 60))
            nm1 = 400 * (2.0 ** ((i + 1) / 60))
            c.rect((X(nm0), y - 40, X(nm1) + 1, y + 40), fill=vis_rgb(nm0), a=a * on * 0.85)
        c.text(((X(400) + X(800)) / 2, y - 64), "可见光", 26, INK, a * on, anchor="mm")
        c.text(((x0 + X(400)) / 2, y - 64), "紫外 · 肉眼看不见", 26, INK2, a * on, anchor="mm")
        for nm, lab, col in ((193, "193 nm DUV", CYAN), (13.5, "13.5 nm EUV", VIOLET)):
            c.line((X(nm), y - 40), (X(nm), y + 40), col, 4, a * on, glow=True)
            c.text((X(nm), y + 124), lab, 26, col, a * on, anchor="mm")
        c.text((960, 330), "① 没有现成的 13.5 nm 强光源", 44, INK, a * on, anchor="mm", weight_glow=True)
    return c.finish(glow_radius=10, glow_gain=0.7)


@shot("A3_03")
def problem2(t, dur, W, H):
    c = Canvas(W, H, bg=(0, 0, 0))
    a = fade(t, 0.0, dur, dur, 0.3)
    k = c.k
    rnd = random.Random(10)
    mol = [(rnd.uniform(300, 1800), rnd.uniform(380, 700)) for _ in range(140)]
    x_start, x_end, yc = 200, 1800, 540
    t0, t1 = 0.3, 4.6
    front = x_start + (x_end - x_start) * seg(t, t0, t1)            # steady front: the hits happen at its head
    # absorption along the beam (Beer-Lambert, illustrative scale): every molecule near the axis takes a bite, weighted
    # by how close it sits to the axis; smooth steps, so the beam dims continuously instead of in stairs
    my = np.array([m[1] for m in mol])
    mx = np.array([m[0] for m in mol])
    wgt = np.exp(-((my - yc) / 34.0) ** 2 / 2)

    def level(x):
        x = np.asarray(x, dtype=np.float64)[..., None]
        return np.exp(-(wgt / (1 + np.exp(-(x - mx) / 10.0))).sum(-1) / 8.0)
    # the beam: one soft violet band whose width and brightness follow the remaining light, drawn per pixel column
    xs = np.arange(W) / k
    lv = level(xs)
    head = np.clip((front - xs) / 30.0, 0, 1) * (xs >= x_start)    # soft leading edge
    inten = lv * head * a
    sig = (6 + 16 * lv)[None, :]                                    # half-width shrinks as it is eaten
    ys = (np.arange(H) / k)[:, None]
    prof = np.exp(-((ys - yc) / sig) ** 2 / 2) * inten[None, :]
    core = np.exp(-((ys - yc) / (sig * 0.35)) ** 2 / 2) * inten[None, :]
    col = np.array(VIOLET, np.float32)                              # saturated EUV violet, a lighter centre line
    hi = np.array((206, 186, 255), np.float32)
    rgb = prof[..., None] * col * 1.05 + core[..., None] * (hi - col) * 0.6
    beam = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8))
    c.img = ImageChops.add(c.img, beam)
    c.glow = ImageChops.add(c.glow, Image.fromarray(np.clip(prof[..., None] * col * 0.45, 0, 255).astype(np.uint8)))
    c.d = ImageDraw.Draw(c.img, "RGBA")
    c.g = ImageDraw.Draw(c.glow)
    # molecules: a molecule lights up when the front reaches it, as bright as the light that is left there, and the
    # flash dies within ~0.3 s; once the beam is gone nothing flashes
    for (x, y), w in zip(mol, wgt):
        flash = 0.0
        p = (x - x_start) / (x_end - x_start)
        if 0 <= p <= 1 and w > 0.05:
            t_hit = t0 + (t1 - t0) * p
            if t >= t_hit:
                flash = float(level(x - 12)) * w * math.exp(-(t - t_hit) / 0.3)
        flash = min(1.0, flash * 2.2)
        col_m = tuple(int(140 + (236 - 140) * flash * (1 if i < 2 else 0.8) + (255 - 180) * flash * (i == 2))
                      for i in range(3)) if flash > 0.02 else (140, 150, 180)
        c.circle((x, y), 4 + 6 * flash, fill=col_m, a=a * (0.5 + 0.5 * flash), glow=flash > 0.05)
    c.text((960, 160), "② 几乎所有物质都吸收它，连空气也不例外", 40, INK, a, anchor="mm", weight_glow=True)
    out = c.finish(glow_radius=10, glow_gain=0.7)
    c.img, c.d = out, ImageDraw.Draw(out, "RGBA")                   # the corner note after the vignette
    c.text((1824, 1010), "示意 · F10", 28, INK, a * 0.9, anchor="rm")
    return out


# where the light path starts on A3_06's last frame (1080p design units): the cyan link to the ledger begins here.
# Set it from the final A3_06 render: open its last frame, find the plasma / collector point, scale to 1920x1080.
SRC_XY = (1180, 470)


def _a3_06_last(W, H):
    """A3_06's last rendered frame at this output size (final / sample / preview by width, else any), or None."""
    pref = {1920: "final", 960: "sample", 640: "preview"}.get(W)
    for q in [pref, "final", "sample", "preview"]:
        if not q:
            continue
        fr = sorted(glob.glob(os.path.join(RENDERS, "shots", "A3_06", q, "[0-9][0-9][0-9][0-9].png")))
        if fr:
            im = Image.open(fr[-1]).convert("RGB")
            return im if im.size == (W, H) else im.resize((W, H), Image.LANCZOS)
    return None


_BG = {}


@shot("A3_07")
def ledger_intro(t, dur, W, H):
    c = Canvas(W, H)
    a = fade(t, 0.0, dur, dur, 0.3)
    k = c.k
    if (W, H) not in _BG:
        _BG[(W, H)] = _a3_06_last(W, H)
    bg = _BG[(W, H)]
    dk = ease(seg(t, 0.15, 1.0))                                    # A3_06's last frame, then it dims
    if bg is not None:
        im = bg.filter(ImageFilter.GaussianBlur(2.0 * k * dk)) if dk > 0 else bg
        im = ImageEnhance.Brightness(im).enhance(1.0 - 0.62 * dk)
        # a little extra shade on the right, where the ledger stands
        grad = Image.linear_gradient("L").rotate(90, expand=True).resize((W, H)).point(lambda v: int(v * 0.55 * dk))
        im.paste(Image.new("RGB", (W, H), (0, 0, 0)), (0, 0), grad)
        c.img = im
        c.d = ImageDraw.Draw(c.img, "RGBA")
    x, w, top, bot = 1700, 70, 160, 920
    draw = ease_out(seg(t, 0.2, 1.0))
    c.line((x + w / 2, bot), (x + w / 2, bot - (bot - top) * draw), INK2, 2, a)
    fill = ease(seg(t, 1.0, 2.4))
    if fill > 0:
        c.rect((x, bot - (bot - top) * fill, x + w, bot), fill=VIOLET, a=a * 0.85, glow=True, radius=8)
        c.rect((x, top, x + w, bot), outline=INK2, width=2, a=a, radius=8)
    c.text((x + w / 2, top - 50), "光的账本", 32, INK, a * draw, anchor="mm", weight_glow=True)
    # lightning icon at the base: electricity is where it starts
    bx, by = x + w / 2, bot + 60
    pts = [(bx - 8, by - 30), (bx + 12, by - 30), (bx + 2, by - 6), (bx + 16, by - 6), (bx - 10, by + 30), (bx - 2, by + 4),
           (bx - 16, by + 4)]
    c.d.polygon([(c.px(px), c.px(py)) for px, py in pts], fill=(250, 220, 120, int(255 * a * draw)))
    c.text((bx - 30, by), "起点：电", 28, INK, a * draw * 0.9, anchor="rm")
    if bg is None:                                                  # fallback: a dim machine outline
        c.rect((160, 360, 1100, 760), outline=(50, 56, 74), width=2, a=a * 0.8, radius=20)
        sx, sy = 300, 560
    else:
        sx, sy = SRC_XY
    c.circle((sx, sy), 14, fill=VIOLET, a=a * ease(seg(t, 1.0, 1.6)), glow=True)   # where the light path starts
    link = ease(seg(t, 2.6, 3.6))
    ex, ey = x - 20, bot - 40
    L = math.hypot(ex - sx, ey - sy)
    for i in range(0, int(L * link), 30):
        u0, u1 = i / L, min(1.0, (i + 16) / L)
        c.line((sx + (ex - sx) * u0, sy + (ey - sy) * u0), (sx + (ex - sx) * u1, sy + (ey - sy) * u1), CYAN, 3, a)
    out = c.finish(glow_radius=10, glow_gain=0.7, vignette=False)
    if bg is not None and dk > 0:                                   # the vignette arrives with the dimming
        vg = Image.radial_gradient("L").resize((W, H)).point(lambda v: 255 - int(v * 0.45 * dk))
        out = Image.composite(out, Image.new("RGB", out.size, (0, 0, 0)), vg)
    elif bg is None:
        vg = Image.radial_gradient("L").resize((W, H)).point(lambda v: 255 - int(v * 0.45))
        out = Image.composite(out, Image.new("RGB", out.size, (0, 0, 0)), vg)
    return out
