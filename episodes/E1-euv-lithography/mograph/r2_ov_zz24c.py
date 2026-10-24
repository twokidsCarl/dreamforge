"""Round-24 overlay for B5_01 (cbeam; rides on the R24_ROOT_CAUSE row 3 structural change: the pupil facet mirror is
moved straight below the field facet mirror so IF -> FFM -> PFM -> condenser is a Z without the R23 X crossing).
With the PFM now just left of the condenser, the zz22h placement put the 「光瞳分面镜」 text next to the condenser and
「聚光镜 → 掩模」 next to the PFM (leaders crossed = labels read swapped). Same texts / timing as zz22h; only the
PFM tag moves LEFT of its mirror and the condenser tag ABOVE-RIGHT of its mirror.
Active only while B5_01 is in r2_cutaway.R24_BEAM and ENABLED.
"""
import os
import re
from r2_ov_common import VIOLET, Layer, anchor, fade

ENABLED = True
OVERLAYS = {}
NO_STORYBOARD_LABELS = set()
_SH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "blender", "shots")


def _r24(module):
    try:
        src = open(os.path.join(_SH, module + ".py"), encoding="utf-8").read()
        m = re.search(r"^R24_BEAM\s*=\s*\{([^}]*)\}", src, re.M)
        return set(re.findall(r"\"([A-Z0-9_]+)\"", m.group(1))) if m else set()
    except OSError:
        return set()


def _in(p, lo=0.03, hi=0.9):
    return lo < p[0] < 0.97 and lo < p[1] < hi


def illum(img, t, dur, W, H):
    L = Layer(W, H)
    L.tag((0.66, 0.06), ["照明系统（示意）", "中间焦点 IF → 照明系统 → 掩模"], fade(t, 0.3), accent=VIOLET, size=0.034)
    f = anchor("B5_01", t, "ffm", (0.62, 0.25))
    p = anchor("B5_01", t, "pfm", (0.42, 0.72))
    i = anchor("B5_01", t, "if", (0.25, 0.6))
    g = anchor("B5_01", t, "g1", (0.7, 0.6))
    if _in(f, hi=0.85):
        L.label(f, (max(0.04, f[0] - 0.3), max(0.2, min(0.5, f[1] - 0.02))) if f[0] > 0.6 else (f[0] + 0.08, max(0.2, f[1] - 0.12)), ["场分面镜 · 切分光场"], fade(t, 0.3), size=0.034)
    if _in(i, hi=0.85):
        L.label(i, (max(0.04, i[0] - 0.02), max(0.2, i[1] - 0.2)), ["中间焦点 IF"], fade(t, 0.4), accent=VIOLET, size=0.03)
    if _in(p, hi=0.95):                       # LEFT of the PFM (the condenser owns the space to its right)
        tp = (max(0.04, p[0] - 0.24), min(0.8, p[1] + 0.02)) if p[1] > 0.7 else (max(0.04, p[0] - 0.1), p[1] + 0.1)
        L.label(p, tp, ["光瞳分面镜"], fade(t, 0.8), size=0.03)   # wide 25 % frame: just below the mirror
    if _in(g, hi=0.95):                       # ABOVE-RIGHT of the condenser
        L.label(g, (min(0.82, g[0] + 0.05), max(0.2, g[1] - 0.14)), ["聚光镜 → 掩模"], fade(t, 1.0), size=0.03)
    return L.compose(img)


if ENABLED and "B5_01" in _r24("r2_cutaway"):
    OVERLAYS["B5_01"] = illum
    NO_STORYBOARD_LABELS.add("B5_01")
