"""Round-28 overlay for C_03 (main process; loaded after r2_ov_zz23h, entries replace earlier ones per shot id).
Rides only on the R28_ROOT_CAUSE row 3 scene-level change in blender/scripts/c03_r28.py (HOUSE_R28): the illuminator is a
closed housing with one front window over the field-facet landing, so the zz23h 「光瞳分面镜」 tag (PFM now inside the
box, behind the front wall) is dropped and the FFM tag says the window shows the illuminator's facet mirror. Texts /
timing otherwise as zz23h (coll -> IF -> illuminator -> mask block). Active only while C_03 is in r2_cutaway.R28_C03 and
HOUSE_R28 is True (read from the sources).
"""
import os
import re

from r2_ov_common import CYAN, VIOLET, Layer, anchor, fade

OVERLAYS = {}
NO_STORYBOARD_LABELS = set()
_HERE = os.path.dirname(os.path.abspath(__file__))
_BL = os.path.join(_HERE, "..", "blender")


def _active():
    try:
        mod = open(os.path.join(_BL, "shots", "r2_cutaway.py"), encoding="utf-8").read()
        m = re.search(r"^R28_C03\s*=\s*\{([^}]*)\}", mod, re.M)
        hook = open(os.path.join(_BL, "scripts", "c03_r28.py"), encoding="utf-8").read()
        sw = re.search(r"^HOUSE_R28\s*=\s*(True|False)", hook, re.M)
        return bool(m and '"C_03"' in m.group(1) and sw and sw.group(1) == "True")
    except OSError:
        return False


def tour(img, t, dur, W, H):
    L = Layer(W, H)
    stations = [("coll", 0.0, 0.2, ["收集镜", "把光聚向中间焦点"]),
                ("if", 0.2, 0.42, ["中间焦点 IF"]),
                ("ffm", 0.42, 0.7, ["照明系统（封闭箱体）", "窗里：光落在场分面镜上"])]
    for name, f0, f1, lines in stations:
        a = fade(t, f0 * dur + 0.3, f1 * dur - 0.15, 0.35)
        if a <= 0:
            continue
        p = anchor("C_03", t, name, (0.5, 0.5))
        if not (0.03 < p[0] < 0.97 and 0.03 < p[1] < 0.85):
            continue
        if name == "ffm":
            L.label(p, (max(0.04, min(0.6, p[0] + 0.12)), max(0.12, p[1] - 0.28)), lines, a, accent=CYAN)
            continue
        tx = p[0] - 0.24 if p[0] > 0.55 else p[0] + 0.12
        L.label(p, (max(0.04, min(0.6, tx)), max(0.3, min(0.7, p[1] + 0.14))), lines, a, accent=CYAN)
    a = fade(t, 0.7 * dur + 0.3, 1e9, 0.35)
    if a > 0:
        L.tag((0.6, 0.06), ["带电路图形的反射式掩模", "约 5.4° 斜射进来 → 反射出去（角度放大示意）"], a,
              accent=VIOLET, size=0.032)
    return L.compose(img)


if _active():
    OVERLAYS["C_03"] = tour
    NO_STORYBOARD_LABELS.add("C_03")
