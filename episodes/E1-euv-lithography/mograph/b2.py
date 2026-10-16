"""B2 2D shots. B2_10: not a perfect vacuum — about 5 Pa of hydrogen inside the scanner (F28)."""
import math
import random

from mograph import CYAN, INK, INK2, VIOLET, Canvas, ease, ease_out, fade, seg, shot


def _vessel(c, x, y, w, h, a):
    """Flat icon of the source vessel: drum plus cone toward IF (matches the 3D silhouette)."""
    c.rect((x, y, x + w * 0.55, y + h), outline=INK2, width=3, a=a, radius=28)
    c.line((x + w * 0.55, y + 20), (x + w, y + h / 2 - 18), INK2, 3, a)
    c.line((x + w * 0.55, y + h - 20), (x + w, y + h / 2 + 18), INK2, 3, a)
    c.line((x + w, y + h / 2 - 18), (x + w, y + h / 2 + 18), INK2, 3, a)


@shot("B2_10")
def five_pascal(t, dur, W, H):
    c = Canvas(W, H)
    a = fade(t, 0.0, dur, dur, 0.3)
    draw = ease_out(seg(t, 0.0, 0.9))
    rnd = random.Random(5)
    for side, x0 in enumerate((170, 1010)):
        _vessel(c, x0, 300, 740, 420, a * draw)
    c.text((170 + 200, 260), "绝对真空", 40, INK, a * draw, anchor="mm")
    c.text((1010 + 200, 260), "实际：约 5 Pa 氢气", 40, CYAN, a * draw, anchor="mm")
    # hydrogen molecules drifting in the right vessel (sparse: a few dozen on screen)
    show = ease(seg(t, 0.8, 2.0))
    for k in range(26):
        px = 1040 + rnd.uniform(0, 360) + 18 * math.sin(t * 0.9 + k)
        py = 330 + rnd.uniform(0, 360) + 14 * math.cos(t * 0.7 + 2 * k)
        for d in (-7, 7):
            c.circle((px + d, py), 6, fill=CYAN, a=a * show * 0.9, glow=True)
    # a faint violet EUV path crossing both vessels
    c.line((300, 510), (910, 510), VIOLET, 4, a * 0.6 * draw, glow=True)
    c.line((1140, 510), (1750, 510), VIOLET, 4, a * 0.6 * draw, glow=True)
    # pressure gauge settling on ~5 Pa (log dial from 0.01 to 1e5 Pa)
    g = ease(seg(t, 2.2, 3.8))
    cx, cy, r = 1210, 880, 110
    c.circle((cx, cy), r, outline=INK2, width=3, a=a * g)
    lo, hi = math.log10(0.01), math.log10(1e5)
    for v, lab in ((0.01, "0.01"), (1, "1"), (100, "100"), (1e5, "1 atm")):
        ang = math.pi * (1.15 - 1.3 * (math.log10(v) - lo) / (hi - lo))
        c.line((cx + 0.82 * r * math.cos(ang), cy - 0.82 * r * math.sin(ang)),
               (cx + r * math.cos(ang), cy - r * math.sin(ang)), INK2, 3, a * g)
        c.text((cx + 1.32 * r * math.cos(ang), cy - 1.32 * r * math.sin(ang)), lab, 20, INK2, a * g, anchor="mm")
    target = math.log10(5)
    wob = 0.06 * math.sin(t * 6) * (1 - ease(seg(t, 3.0, 4.4)))
    val = lo + (target - lo) * ease_out(seg(t, 2.4, 3.6)) + wob
    ang = math.pi * (1.15 - 1.3 * (val - lo) / (hi - lo))
    c.line((cx, cy), (cx + 0.9 * r * math.cos(ang), cy - 0.9 * r * math.sin(ang)), CYAN, 5, a * g, glow=True)
    c.text((cx + 170, cy), "≈ 5 Pa", 52, CYAN, a * g, anchor="lm", weight_glow=True)
    c.text((cx + 170, cy + 55), "（F28 · 示意）", 22, INK2, a * g, anchor="lm")
    return c.finish()
