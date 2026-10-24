"""Round-25 overlay for B1_15 (srcb; R25_ROOT_CAUSE row 2 structural change: the exit light is now a beam_r25 shell
cone that converges to the IF INSIDE the frame, so the R24 「IF ↓」 bottom-edge arrow (zz24s) would sit on the cone's
waist). Same 「收集镜」 label as zz21s / zz24s + the IF label moved to the side of the in-frame focus point, as the
R24 review asked: 「首次出现写成『中间焦点 IF』，用计量青」. Active only while B1_15 is in r2_source.R25_SRC and ENABLED.
"""
import os
import re

from r2_ov_common import CYAN, Layer, anchor, fade

ENABLED = True
OVERLAYS = {}
NO_STORYBOARD_LABELS = set()
_SH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "blender", "shots")


def _r25(module):
    try:
        src = open(os.path.join(_SH, module + ".py"), encoding="utf-8").read()
        m = re.search(r"^R25_SRC\s*=\s*\{([^}]*)\}", src, re.M)
        return set(re.findall(r"\"([A-Z0-9_]+)\"", m.group(1))) if m else set()
    except OSError:
        return set()


def b115(img, t, dur, W, H):
    L = Layer(W, H)
    c = anchor("B1_15", t, "coll", (0.53, 0.27))
    L.label(c, (max(0.66, c[0] + 0.1), 0.12), ["收集镜"], fade(t, 0.0, d=0.3), accent=CYAN, size=0.044)
    p = anchor("B1_15", t, "if", None)
    if p is not None and 0.05 < p[0] < 0.95 and 0.05 < p[1] < 0.98:
        L.label((p[0] + 0.006, p[1]), (min(0.9, p[0] + 0.19), min(0.93, p[1] + 0.02)), ["中间焦点 IF"],
                fade(t, 0.15, d=0.3), accent=CYAN, size=0.038)
    return L.compose(img)


if ENABLED and "B1_15" in _r25("r2_source"):
    OVERLAYS["B1_15"] = b115
