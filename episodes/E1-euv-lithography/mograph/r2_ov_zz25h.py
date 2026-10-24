"""Round-25 overlay (chero, copy of r2_ov_zz24h gated on R25_HERO: B3_02 is not in R24_HERO, so the R24 IF tag
never showed; the R25 row-5 dish + camera need it). Original R24 text:
Round-24 overlay for B3_02 (chero; rides on the R24_ROOT_CAUSE row 5 structural change: collector enlarged on the
same ellipsoid R 0.68 -> 1.25 m + sketch camera). With the new camera the cone tip / IF sits at the right edge and the
older IF tag (above-left of the tip) landed inside the title panel -> R23 review B3_02 #2 「IF 标签移到波纹管下方」:
the IF tag sits BELOW-LEFT of the tip. Hole / plasma tags = the R23 cuth texts (laser kept -> the hole tag is true).
Active only while B3_02 is in r2_cutaway.R25_HERO and ENABLED.
"""
import os
import re
from r2_ov_common import CYAN, VIOLET, Layer, anchor, fade

ENABLED = True
OVERLAYS = {}
NO_STORYBOARD_LABELS = set()
_SH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "blender", "shots")


def _r24(module):
    try:
        src = open(os.path.join(_SH, module + ".py"), encoding="utf-8").read()
        m = re.search(r"^R25_HERO\s*=\s*\{([^}]*)\}", src, re.M)
        return set(re.findall(r"\"([A-Z0-9_]+)\"", m.group(1))) if m else set()
    except OSError:
        return set()


def _in(p, lo=0.03, hi=0.9):
    return lo < p[0] < 0.99 and lo < p[1] < hi


def collector(img, t, dur, W, H):
    L = Layer(W, H)
    steps = [("hole", 0.0, 0.36, ["中心孔", "CO₂ 激光从镜背入口进入"], CYAN, (0.2, 0.5)),
             ("plasma", 0.36, 0.62, ["第一焦点", "锡滴在这里被打成等离子体"], CYAN, (0.4, 0.5))]
    for name, f0, f1, lines, acc, dflt in steps:
        al = fade(t, max(0.3, f0 * dur + 0.2), f1 * dur - 0.1, 0.3)
        if al <= 0:
            continue
        p = anchor("B3_02", t, name, dflt)
        if not _in(p):
            continue
        L.label(p, (max(0.04, min(0.62, p[0] + 0.1)), max(0.3, min(0.72, p[1] + 0.22))), lines, al, accent=acc, size=0.038)
    al = fade(t, 0.3, None, 0.3)
    p = anchor("B3_02", t, "if", (0.95, 0.47))
    if al > 0 and _in(p, hi=0.95):            # below-left of the IF / bellows, clear of the title panel
        # R25: below-left of the tip but right of / below the plasma tag (R25 8-spp: the R24 spot touched it at f67)
        L.label(p, (max(0.84, min(0.87, p[0] - 0.09)), min(0.78, p[1] + 0.3)), ["中间焦点 IF"], al, accent=VIOLET,
                size=0.034)
    return L.compose(img)


if ENABLED and "B3_02" in _r24("r2_cutaway"):
    OVERLAYS["B3_02"] = collector
