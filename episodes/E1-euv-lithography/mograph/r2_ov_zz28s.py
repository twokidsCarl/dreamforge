"""Round-28 overlay for B1_15 (main process; R28_ROOT_CAUSE row 2 camera change in blender/scripts/b115_r28.py). The camera
now sits on the mouth side beside the axis (bowl on the left, cone converging to the right onto the IF), so the R22
'coll' face point used by zz25s projects onto the plasma: the 「收集镜」 leader goes to 'coll28' (upper bowl face, merged
into the anchors json by b115_r28) with the tag up-left in the empty dark; the 「中间焦点 IF」 tag stays beside the IF as in
zz25s. Active only while B1_15 is in r2_source.R28_SRC and CAM_R28 is True (read from the sources).
"""
import os
import re

from r2_ov_common import CYAN, Layer, anchor, fade

OVERLAYS = {}
NO_STORYBOARD_LABELS = set()
_BL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "blender")


def _active():
    try:
        mod = open(os.path.join(_BL, "shots", "r2_source.py"), encoding="utf-8").read()
        m = re.search(r"^R28_SRC\s*=\s*\{([^}]*)\}", mod, re.M)
        hook = open(os.path.join(_BL, "scripts", "b115_r28.py"), encoding="utf-8").read()
        sw = re.search(r"^CAM_R28\s*=\s*(True|False)", hook, re.M)
        return bool(m and '"B1_15"' in m.group(1) and sw and sw.group(1) == "True")
    except OSError:
        return False


def b115(img, t, dur, W, H):
    L = Layer(W, H)
    c = anchor("B1_15", t, "coll28", (0.66, 0.3))
    L.label(c, (max(0.04, c[0] - 0.36), 0.1), ["收集镜"], fade(t, 0.0, d=0.3), accent=CYAN, size=0.044)
    p = anchor("B1_15", t, "if", None)
    if p is not None and 0.05 < p[0] < 0.95 and 0.05 < p[1] < 0.98:
        L.label((p[0] + 0.006, p[1]), (min(0.84, p[0] + 0.08), min(0.9, p[1] + 0.12)), ["中间焦点 IF"],
                fade(t, 0.15, d=0.3), accent=CYAN, size=0.038)
    return L.compose(img)


if _active():
    OVERLAYS["B1_15"] = b115
