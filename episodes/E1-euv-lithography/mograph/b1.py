"""B1 2D shots: chapter card, droplet scale, why pre-pulse, tin spectrum, light ledger.
Design space is 1920x1080; Canvas scales to the output size."""
import math
import os
import random

from PIL import Image, ImageEnhance, ImageFilter

from mograph import (BG, BLUE_BG, CYAN, INK, INK2, LINE, ORANGE, RENDERS, VIOLET, Canvas, ease, ease_out,
                     fade, seg, shot)
from overlay_labels import font


def text_w(c, s, size):
    """Width of a string in design pixels."""
    b = c.d.textbbox((0, 0), s, font=font(int(c.px(size))))
    return (b[2] - b[0]) / c.k


def rich(c, xy, parts, size, color, a, anchor="l"):
    """Text with sub/superscripts the Heiti face lacks (₂, ⁺ are blank boxes): parts = [(str, "n"|"sub"|"sup")].
    anchor: l / r / m on the baseline row, vertically centred like anchor 'lm'."""
    widths = [text_w(c, s, size * (0.62 if k != "n" else 1.0)) + (0.42 * size if k != "n" else 0) for s, k in parts]
    x = xy[0] - {"l": 0, "m": sum(widths) / 2, "r": sum(widths)}[anchor]
    for (s, k), w in zip(parts, widths):
        if k == "n":
            c.text((x, xy[1]), s, size, color, a, anchor="lm")
        else:
            dy = 0.30 * size if k == "sub" else -0.34 * size
            _script(c, (x + 1, xy[1] + dy), s, size * 0.62, color, a)
        x += w


def _script(c, xy, s, size, color, a):
    """A sub/superscript glyph beside a >= 26 px word: drawn directly (Canvas.text would raise it to 26 px)."""
    from PIL import Image, ImageDraw
    f = font(int(c.px(size)))
    x, y = c.px(xy[0]), c.px(xy[1])
    x0, y0, x1, y1 = (int(v) for v in c.d.textbbox((x, y), s, font=f, anchor="lm"))
    x0, y0, x1, y1 = max(0, x0 - 2), max(0, y0 - 2), min(c.W, x1 + 2), min(c.H, y1 + 2)
    if a > 0 and x1 > x0 and y1 > y0:
        mask = Image.new("L", (x1 - x0, y1 - y0), 0)
        ImageDraw.Draw(mask).text((x - x0, y - y0), s, font=f, fill=int(255 * min(1.0, a)), anchor="lm")
        c.img.paste(Image.new("RGB", mask.size, color), (x0, y0), mask)


# ---- reusable: the light ledger ------------------------------------------------------------
LEDGER_TOP, LEDGER_H = 150, 780
P_MAX, P_MIN = 1e6, 0.3          # log scale from megawatts down to below a watt


def ledger_y(power):
    lo, hi = math.log10(P_MIN), math.log10(P_MAX)
    return LEDGER_TOP + (hi - math.log10(power)) / (hi - lo) * LEDGER_H


def draw_ledger(c, entries, reveal, x=1640, w=46, a=1.0, title="光的账本", sub_size=28):
    """entries: [(power_W, label, sublabel, color)] top to bottom; reveal: 0..len(entries)."""
    c.text((x + w / 2, LEDGER_TOP - 70), title, 30, INK, a, anchor="mm")
    c.rect((x, LEDGER_TOP, x + w, LEDGER_TOP + LEDGER_H), outline=INK2, width=2, a=0.5 * a, radius=6)
    for i, (pw, label, sub, col) in enumerate(entries):
        r = ease(reveal - i)
        if r <= 0:
            continue
        y = ledger_y(pw)
        top = LEDGER_TOP if i == 0 else ledger_y(entries[i - 1][0])
        # no additive glow on the fill: it washed orange to peach and violet to pink
        c.rect((x + 4, max(LEDGER_TOP + 4, y), x + w - 4, LEDGER_TOP + LEDGER_H - 4), fill=col, a=0.62 * a * r,
               radius=4)
        c.line((x - 14, y), (x + w + 14, y), col, 3, a * r, glow=True)
        c.text((x - 28, y), label, 30, INK, a * r, anchor="rm")
        if sub:                                   # the number is the point: 28 px on 1080, light grey
            c.text((x - 28, y + 40), sub, sub_size, (205, 210, 222), a * r, anchor="rm")


def _blur_bg(path, W, H, dark=0.35):
    im = Image.open(path).convert("RGB").resize((W, H), Image.LANCZOS)
    im = im.filter(ImageFilter.GaussianBlur(H / 40))
    return ImageEnhance.Brightness(im).enhance(dark)


# ---- B1_01 chapter card --------------------------------------------------------------------
@shot("B1_01")
def chapter_b1(t, dur, W, H):
    c = Canvas(W, H)
    bg = os.path.join(RENDERS, "sample_b1", "cycles", "CamNozzle", "0060.png")
    if os.path.exists(bg):
        c.img.paste(_blur_bg(bg, W, H, 0.3 + 0.1 * ease(seg(t, 0, dur))))
    a = fade(t, 0.2, dur, dur, 0.5)
    c.text((160, 470), "第一站", 34, INK2, a)
    c.text((160, 520), "光源", 120, INK, a, weight_glow=True)
    c.text((164, 680), "Light Source", 34, VIOLET, a)
    c.line((164, 650), (164 + 420 * ease_out(seg(t, 0.3, 1.4)), 650), VIOLET, 3, a, glow=True)
    draw_ledger(c, [(1e6, "电", "约 1.26 MW · ASML 2025 年报", CYAN)], reveal=ease(seg(t, 0.8, 2.0)), a=0.9)
    return c.finish()


# ---- B1_06 droplet vs hair -----------------------------------------------------------------
@shot("B1_06")
def droplet_scale(t, dur, W, H):
    c = Canvas(W, H)
    s = 5.2                                   # px per micrometre in design space
    cx, cy = 760, 520
    a = fade(t, 0.0, dur, dur, 0.3)
    # hair cross-section (about 80 um, F44) appears behind the droplet (25 um, F3)
    hr = 40 * s * ease_out(seg(t, 0.3, 1.2))
    c.circle((cx + 360, cy), hr, fill=(58, 46, 40), outline=(150, 120, 100), width=3, a=a)
    c.text((cx + 360, cy + 40 * s + 50), "一根头发丝 ≈ 80 μm", 32, INK2, a * ease(seg(t, 0.8, 1.4)), anchor="mm")
    # the droplet: holds, then streaks off to the right
    go = ease(seg(t, 2.6, dur))
    dx = 900 * go ** 2
    for k in range(10):                      # speed lines
        if go > 0:
            yy = cy - 50 + k * 11
            c.line((cx + dx - 40 - 300 * go, yy), (cx + dx - 40, yy), INK2, 2, a * 0.5 * go)
    c.circle((cx + dx, cy), 12.5 * s, fill=(206, 210, 220), outline=INK, width=2, a=a, glow=True)
    c.text((cx, cy - 12.5 * s - 50), "锡滴 ≈ 25 μm", 36, INK, a * (1 - go), anchor="mm")
    # speedometer readout
    v = 70 * ease_out(seg(t, 2.6, dur - 0.3))
    c.text((1500, 800), f"{v:4.0f}", 120, ORANGE, a * ease(seg(t, 2.4, 2.8)), anchor="rm", weight_glow=True)
    c.text((1520, 790), "m/s", 40, INK2, a * ease(seg(t, 2.4, 2.8)), anchor="lm")
    c.text((1520, 845), "（F3）", 26, INK2, a * ease(seg(t, 2.4, 2.8)), anchor="lm")
    return c.finish()


# ---- B1_16 why pre-pulse (blueprint) -------------------------------------------------------
@shot("B1_16")
def why_prepulse(t, dur, W, H):
    c = Canvas(W, H, bg=BLUE_BG)
    c.grid(a=0.55)
    a = fade(t, 0.0, dur, dur, 0.3)
    draw = ease_out(seg(t, 0.2, 1.6))
    heat = ease(seg(t, 2.0, 4.0))
    for side, (x0, title) in enumerate(((180, "直接打锡滴"), (1000, "先拍扁，再打"))):
        c.rect((x0, 170, x0 + 740, 820), outline=LINE, width=2, a=a * draw)
        c.text((x0 + 30, 200), title, 40, LINE, a * draw)
        cx, cy = x0 + 370, 520
        # laser spot (dashed ring)
        for k in range(48):
            ang0, ang1 = 2 * math.pi * k / 48, 2 * math.pi * (k + 0.5) / 48
            r = 210
            c.line((cx + r * math.cos(ang0), cy + r * math.sin(ang0)), (cx + r * math.cos(ang1), cy + r * math.sin(ang1)),
                   ORANGE, 3, a * draw)
        c.text((cx, cy + 250), "激光光斑", 26, ORANGE, a * draw, anchor="mm")
        # both panels look along the beam: the target is drawn face-on at the same scale as the 400 um spot
        # (PUR20 slide 23: main-pulse beam 400 um; droplet ~27 um; FOM17 Fig.12: the disk is expanded "to match
        # the main pulse (MP) beam waist diameter")
        if side == 0:
            rd = r * 27 / 400
            c.circle((cx, cy), rd, outline=LINE, width=2, a=a * draw)
            c.circle((cx, cy), rd * heat, fill=ORANGE, a=a * heat, glow=True)
            c.text((cx, cy - 250), "锡滴只接住光斑中间一小点", 26, LINE, a * heat, anchor="mm")
        else:
            rd = r * 0.95
            c.circle((cx, cy), rd, outline=LINE, width=3, a=a * draw)
            c.circle((cx, cy), rd * heat, fill=ORANGE, a=a * heat * 0.6, glow=True)
            c.text((cx, cy - 250), "薄盘面积大、密度低，正好接住整个光斑", 26, LINE, a * heat, anchor="mm")
    arrow = ease_out(seg(t, 4.2, 5.4))
    c.line((700, 920), (700 + 520 * arrow, 920), LINE, 3, a * arrow)
    c.text((960, 975), "更多能量 → 变成 13.5 nm 的光（示意）", 32, LINE, a * arrow, anchor="mm")
    return c.finish(glow_radius=10)


# ---- B1_18 tin spectrum (UTA) --------------------------------------------------------------
BIN = 0.05                       # nm per stacking bin (a 0.01 nm bin made one needle far above the envelope)
PEAK_H = 600                     # design px: the tallest stack tops out ~60 px under the 13.5 nm label


def _spectrum_lines(seed=7, per_state=170):
    """Every line once, independent of t: (charge state index, wavelength, height, base). Stacked per BIN."""
    rnd = random.Random(seed)
    stacks, lines = {}, []
    for i, q in enumerate(range(8, 15)):
        centre = 13.5 + (q - 11) * 0.05            # every charge state lands near 13.5 nm (S12)
        for _ in range(per_state):
            lam = rnd.gauss(centre, 0.24)
            if not 10.0 < lam < 18.0:
                continue
            key = round(lam / BIN)
            hgt = rnd.uniform(14, 46)
            lines.append((i, lam, hgt, stacks.get(key, 0.0)))
            stacks[key] = stacks.get(key, 0.0) + hgt
    return lines, PEAK_H / max(stacks.values())


_SPEC = _spectrum_lines()


@shot("B1_18")
def tin_spectrum(t, dur, W, H):
    c = Canvas(W, H)
    a = fade(t, 0.0, dur, dur, 0.3)
    x0, x1, yb = 220, 1700, 860
    lam0, lam1 = 10.0, 18.0
    X = lambda lam: x0 + (lam - lam0) / (lam1 - lam0) * (x1 - x0)  # noqa: E731
    c.line((x0, yb), (x1, yb), INK2, 2, a)
    for lam in range(10, 19):
        c.line((X(lam), yb), (X(lam), yb + 12), INK2, 2, a)
        c.text((X(lam), yb + 40), f"{lam}", 26, INK2, a, anchor="mm")
    c.text((x1, yb + 84), "波长（nm）", 26, INK2, a, anchor="rm")
    lines, k = _SPEC
    n_states = 7
    rev = [ease_out(seg(t, 0.6 + 0.55 * i, 1.4 + 0.55 * i)) for i in range(n_states)]
    # soft envelope behind the lines: the smoothed sum of what has landed so far (an unresolved array, not a comb)
    nb = 240
    env = [0.0] * nb
    for i, lam, hgt, base in lines:
        if rev[i] > 0:
            j = int((lam - lam0) / (lam1 - lam0) * nb)
            if 0 <= j < nb:
                env[j] += hgt * rev[i]
    sig = 3.0
    kern = [math.exp(-0.5 * (d / sig) ** 2) for d in range(-9, 10)]
    ks = sum(kern)
    sm = [sum(env[min(nb - 1, max(0, j + d - 9))] * kern[d] for d in range(19)) / ks for j in range(nb)]
    norm = k * BIN / ((lam1 - lam0) / nb)                      # same height scale as the stacked lines
    if max(sm) > 0:
        pts = [(X(lam0 + (j + 0.5) * (lam1 - lam0) / nb), yb - sm[j] * norm * 1.05) for j in range(nb)]
        poly = [(c.px(x), c.px(y)) for x, y in [(x0, yb)] + pts + [(x1, yb)]]
        c.d.polygon(poly, fill=(*[int(v * 0.55) for v in VIOLET], int(110 * a)))
        c.g.polygon(poly, fill=tuple(int(v * 0.35 * a) for v in VIOLET))
        c.d.line([(c.px(x), c.px(y)) for x, y in pts], fill=(*VIOLET, int(200 * a)), width=max(1, int(c.px(2))))
    for i, lam, hgt, base in lines:
        r = rev[i]
        if r <= 0:
            continue
        shade = 0.45 + 0.55 * i / (n_states - 1)
        col = tuple(int(v * shade) for v in VIOLET)
        y0 = yb - base * k * r
        c.line((X(lam), y0), (X(lam), y0 - hgt * k * r), col, 2, a * r)
    for i in range(n_states):
        if rev[i] <= 0:
            continue
        shade = 0.45 + 0.55 * i / (n_states - 1)
        col = tuple(min(255, int(v * (0.75 + 0.45 * i / (n_states - 1)))) for v in VIOLET)   # legible even when dim
        rich(c, (x0 + 10, 200 + 46 * i), [("Sn", "n"), (f"{8 + i}+", "sup")], 30, col, a * rev[i])
    lab = ease(seg(t, 4.8, 5.6))
    c.line((X(13.5), 210), (X(13.5), yb), INK, 2, a * lab, glow=True)
    c.text((X(13.5) + 20, 190), "13.5 nm", 40, INK, a * lab, anchor="lm", weight_glow=True)
    c.text((x1, 120), "成千上万条谱线挤在一起（未分辨跃迁阵列 UTA · 示意）", 28, INK2, a, anchor="rm")
    return c.finish()


# ---- B1_27 light ledger: laser -> EUV ------------------------------------------------------
@shot("B1_27")
def ledger_b1(t, dur, W, H):
    c = Canvas(W, H)
    a = fade(t, 0.0, dur, dur, 0.3)
    entries = [(1e6, "电", "约 1.26 MW · ASML 2025 年报", CYAN),
               (4e4, "激光", "几十 kW", ORANGE),
               (500, "EUV", "超过 500 W · NXE:3800E", VIOLET)]
    reveal = 1 + 2 * ease(seg(t, 0.8, 5.5))
    # centred, larger version of the ledger
    draw_ledger(c, entries, reveal, x=1000, w=70, a=a)
    # dashed extension to the 1000 W prototype
    d = ease(seg(t, 6.0, 7.5))
    y600, y1000 = ledger_y(500), ledger_y(1000)
    for k in range(6):
        y = y600 - (y600 - y1000) * k / 6
        c.line((1090, y), (1090, y - (y600 - y1000) / 12), VIOLET, 3, a * d)
    c.text((1120, y1000), "1000 W · ASML 2025 年演示", 30, VIOLET, a * d, anchor="lm")
    c.text((1880, 1000), "量级示意 · 对数刻度", 26, INK2, a, anchor="rm")
    return c.finish()


@shot("B1_09")
def two_pulses(t, dur, W, H):
    """Energy view: the droplet as a dark outline; two orange pulses, thin then thick, queue up from the
    collector's central hole toward it (F4)."""
    c = Canvas(W, H, bg=(0, 0, 0))
    a = fade(t, 0.0, dur, dur, 0.3)
    dx, dy = 1300, 540
    c.circle((dx, dy), 60, outline=(90, 110, 150), width=3, a=a)          # the droplet's silhouette
    c.circle((dx, dy), 60, outline=(90, 110, 150), width=1, a=a * 0.4, glow=True)
    c.circle((200, dy), 46, outline=(60, 70, 96), width=2, a=a * 0.8)     # the collector's central hole
    hole = 200
    for k, (t0, w, length, lab) in enumerate(((0.6, 6, 220, "预脉冲：细"), (1.8, 18, 300, "主脉冲：粗"))):
        p = ease(seg(t, t0, t0 + 1.4))
        if p <= 0:
            continue
        head = hole + (dx - 80 - hole) * p - 160 * k * (1 - p)
        tail = max(hole, head - length)
        if head <= tail:
            continue
        c.line((tail, dy), (head, dy), (255, 122, 40), w, a, glow=True)        # deep orange core, not white
        # the label sits on the visible part of the pulse and only once enough of it is out of the hole
        # (it used to sit at head - length/2, off the left edge while the main pulse was still entering)
        lw = text_w(c, lab, 28)
        lx = max(hole + lw / 2 + 10, (tail + head) / 2)
        la = a * ease(seg(head - tail, 0.35 * length, 0.8 * length))
        if k == 0:
            la *= 1 - ease(seg(t, 1.9, 2.3))                       # one label at a time
        c.text((lx, dy - 52 if k == 0 else dy + 56), lab, 28, ORANGE, la, anchor="mm")
    x2 = ease(seg(t, 2.8, 3.3))
    c.text((1760, 200), "×2", 120, ORANGE, a * x2, anchor="mm", weight_glow=True)
    c.text((1760, 290), "每颗锡滴打两次", 30, INK, a * x2, anchor="mm")
    rich(c, (1880, 1000), [("CO", "n"), ("2", "sub"), ("激光为红外光，橙色为示意", "n")], 26, INK2, a, anchor="r")
    return c.finish(glow_radius=10, glow_gain=0.55)
