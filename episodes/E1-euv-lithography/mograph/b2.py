"""B2 2D shots. B2_10: not a perfect vacuum — about 5 Pa of hydrogen inside the scanner (the source vessel runs
at ~100 Pa, ASML 2017 Source Workshop p.34, so the icon here is the scanner, not the vessel)."""
import math
import random

from mograph import CYAN, INK, INK2, VIOLET, Canvas, ease, ease_out, fade, seg, shot


def _scanner(c, x, y, w, h, a):
    """Flat icon of the scanner: an enclosure with a zig-zag of mirrors inside (the optics the light crosses)."""
    c.rect((x, y, x + w, y + h), outline=INK2, width=3, a=a, radius=22)
    pts = [(x + 0.08 * w, y + 0.5 * h), (x + 0.3 * w, y + 0.2 * h), (x + 0.5 * w, y + 0.78 * h),
           (x + 0.7 * w, y + 0.22 * h), (x + 0.92 * w, y + 0.62 * h)]
    for p0, p1 in zip(pts, pts[1:]):
        c.line(p0, p1, VIOLET, 3, a * 0.6, glow=True)
    for px, py in pts[1:-1]:
        c.line((px - 26, py), (px + 26, py), INK2, 5, a)


@shot("B2_10")
def five_pascal(t, dur, W, H):
    c = Canvas(W, H)
    a = fade(t, 0.0, dur, dur, 0.3)
    draw = ease_out(seg(t, 0.0, 0.9))
    rnd = random.Random(5)
    for side, x0 in enumerate((170, 1010)):
        _scanner(c, x0, 300, 740, 420, a * draw)
    c.text((170 + 370, 260), "设想：绝对真空", 40, INK, a * draw, anchor="mm")
    c.text((1010 + 370, 260), "扫描仪内部：约 5 Pa 氢气", 40, CYAN, a * draw, anchor="mm")
    # hydrogen molecules drifting in the right vessel (sparse: a few dozen on screen)
    show = ease(seg(t, 0.8, 2.0))
    for k in range(26):
        px = 1040 + rnd.uniform(0, 680) + 18 * math.sin(t * 0.9 + k)
        py = 330 + rnd.uniform(0, 360) + 14 * math.cos(t * 0.7 + 2 * k)
        for d in (-7, 7):
            c.circle((px + d, py), 6, fill=CYAN, a=a * show * 0.9, glow=True)
    # pressure gauge settling on ~5 Pa (log dial from 0.01 to 1e5 Pa)
    g = ease(seg(t, 2.2, 3.8))
    cx, cy, r = 1210, 845, 105                     # clear of the subtitle band at the bottom
    c.circle((cx, cy), r, outline=INK2, width=3, a=a * g)
    lo, hi = math.log10(0.01), math.log10(1e5)
    # ticks at 0.01, 1, 100 Pa and 1 atm; only the two ends are labelled (28 px labels for all four crowded the dial)
    for v, lab in ((0.01, "0.01 Pa"), (1, ""), (100, ""), (1e5, "1 atm")):
        ang = math.pi * (1.15 - 1.3 * (math.log10(v) - lo) / (hi - lo))
        c.line((cx + 0.82 * r * math.cos(ang), cy - 0.82 * r * math.sin(ang)),
               (cx + r * math.cos(ang), cy - r * math.sin(ang)), INK2, 3, a * g)
        if lab:
            c.text((cx + 1.45 * r * math.cos(ang), cy - 1.45 * r * math.sin(ang) + 8), lab, 28, INK2, a * g,
                   anchor="mm")
    target = math.log10(5)
    wob = 0.06 * math.sin(t * 6) * (1 - ease(seg(t, 3.0, 4.4)))
    val = lo + (target - lo) * ease_out(seg(t, 2.4, 3.6)) + wob
    ang = math.pi * (1.15 - 1.3 * (val - lo) / (hi - lo))
    c.line((cx, cy), (cx + 0.9 * r * math.cos(ang), cy - 0.9 * r * math.sin(ang)), CYAN, 5, a * g, glow=True)
    c.text((cx + 210, cy - 6), "≈ 5 Pa", 52, CYAN, a * g, anchor="lm", weight_glow=True)
    c.text((cx + 210, cy + 52), "（示意）", 28, INK2, a * g, anchor="lm")
    return c.finish()
