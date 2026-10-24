"""Round-31 overlay for B6_12 (misc agent; loaded after r2_ov_zz28m, replaces its B6_12 entry).
Rides on the R31_ROOT_CAUSE row 6b structural change PELL_R31 in blender/scripts/misc_r31.py (frame shadow band on the
pattern face + membrane-only grazing sheen; new anchors film31 / pattern31). R30 p3 B6_12 #1: 「pellicle 与掩模的两个锚点落在
同一块亮面上…让 pellicle 锚点落在膜的边框 / 高光上，掩模锚点落在膜后能看到图形的位置，两条引线分别从左右引出，不交叉」:
the two first-beat labels move to opposite sides — 保护膜 pellicle on the LEFT, leader to the near frame bar inner edge at
the film plane (film31); 反射掩模 on the RIGHT, leader to the pattern seen through the film (pattern31). The magnifier
beat (zz21m / zz28m) is unchanged. Active only while B6_12 is in r2_misc.R31_MISC and PELL_R31 is True.
"""
import importlib.util
import os
import re

ENABLED = True
OVERLAYS = {}
NO_STORYBOARD_LABELS = set()
_HERE = os.path.dirname(os.path.abspath(__file__))
_BL = os.path.join(_HERE, "..", "blender")


def _set(path, name):
    try:
        src = open(path, encoding="utf-8").read()
        m = re.search(r"^" + name + r"\s*=\s*\{([^}]*)\}", src, re.M)
        return set(re.findall(r"\"([A-Z0-9_]+)\"", m.group(1))) if m else set()
    except OSError:
        return set()


def _switch(name):
    try:
        src = open(os.path.join(_BL, "scripts", "misc_r31.py"), encoding="utf-8").read()
        m = re.search(r"^" + name + r"\s*=\s*(True|False)", src, re.M)
        return bool(m and m.group(1) == "True")
    except OSError:
        return False


def _mod(module):
    spec = importlib.util.spec_from_file_location(module + "_r31mbase", os.path.join(_HERE, module + ".py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


_R31 = _set(os.path.join(_BL, "shots", "r2_misc.py"), "R31_MISC") if ENABLED else set()

if "B6_12" in _R31 and _switch("PELL_R31"):
    from r2_ov_common import Layer, anchor, fade

    _z28 = _mod("r2_ov_zz28m")
    _zb = getattr(_z28, "_z21", None)
    if _zb is None or "B6_12" not in _z28.OVERLAYS:
        _zb = _mod("r2_ov_zz21m")
        _base = _zb.ov_B6_12
    else:
        _base = _z28.ov_B6_12
    _zb._tl = lambda *a, **k: None          # the two R21 top-right first-beat tags are replaced below

    def _clip(p, lo=0.04, hi=0.96):
        return (min(hi, max(lo, p[0])), min(hi, max(lo, p[1])))

    def ov_B6_12(img, t, dur, W, H):
        img = _base(img, t, dur, W, H)
        L_ = Layer(W, H)
        a = fade(t, 0.25, dur * 0.6)
        a1 = fade(t, 0.5, dur * 0.6)
        pf = _clip(anchor("B6_12", t, "film31", (0.35, 0.62)))
        pp = _clip(anchor("B6_12", t, "pattern31", (0.62, 0.55)))
        film = (pf, ["保护膜 pellicle", "张在金属框上，几乎透明"], a)
        mask = (pp, ["反射掩模（图形面朝下）", "卡盘吸住掩模背面"], a1)
        left, right = (film, mask) if pf[0] <= pp[0] else (mask, film)     # leaders from opposite sides, never crossing
        p, lines, al = left
        if al > 0:
            box = L_.tag((0.025, max(0.1, min(0.62, p[1] - 0.16))), lines, al, anchor="la")
            if box:
                L_.leader(p, (box[2] / W, (box[1] + box[3]) / 2 / H), al)
        p, lines, al = right
        if al > 0:
            box = L_.tag((0.975, max(0.1, min(0.62, p[1] - 0.2))), lines, al, anchor="ra")
            if box:
                L_.leader(p, (box[0] / W, (box[1] + box[3]) / 2 / H), al)
        return L_.compose(img).convert("RGB")

    OVERLAYS.update({"B6_12": ov_B6_12})
    NO_STORYBOARD_LABELS |= {"B6_12"}
