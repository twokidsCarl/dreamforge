"""Round-24 overlay for B1_15 (srcb; R24_ROOT_CAUSE row 3 structural change: volume IFConeR22 -> beam_r24 soft cone
leaving the frame toward the off-frame IF). R23 review B1_15 #1: 「…从镜缘收到画外一点…并加一个小『IF』锚点」.
Same 「收集镜」 label as r2_ov_zz21s + a small 「IF ↓」 marker on the cone axis at the bottom edge (the "if" anchor is
merged into the shot's anchors json by src_r24). Active only while B1_15 is in r2_source.R24_SRC and ENABLED.
"""
import os
import re

from r2_ov_common import CYAN, Layer, anchor, fade

ENABLED = True
_IFC = (205, 190, 255)   # light violet: readable on the dark floor and on the cone
OVERLAYS = {}
NO_STORYBOARD_LABELS = set()
_SH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "blender", "shots")


def _r24(module):
    try:
        src = open(os.path.join(_SH, module + ".py"), encoding="utf-8").read()
        m = re.search(r"^R24_SRC\s*=\s*\{([^}]*)\}", src, re.M)
        return set(re.findall(r"\"([A-Z0-9_]+)\"", m.group(1))) if m else set()
    except OSError:
        return set()


def b115(img, t, dur, W, H):
    L = Layer(W, H)
    c = anchor("B1_15", t, "coll", (0.53, 0.27))
    L.label(c, (max(0.66, c[0] + 0.1), 0.12), ["收集镜"], fade(t, 0.0, d=0.3), accent=CYAN, size=0.044)
    p = anchor("B1_15", t, "if", None)
    if p is not None and 0.05 < p[0] < 0.95:
        a = fade(t, 0.15, d=0.3)
        x = p[0]
        L.arrow((x, 0.86), (x, 0.975), a, color=_IFC, width=0.0035, head=0.016)
        L.text((x + 0.018, 0.885), "IF", size=0.036, color=_IFC, a=a)
    return L.compose(img)


if ENABLED and "B1_15" in _r24("r2_source"):
    OVERLAYS["B1_15"] = b115
