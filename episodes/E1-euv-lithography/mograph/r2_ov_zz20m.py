"""Round-20 overlays for the r2_misc shots (loaded after r2_ov_zz19m; entries replace earlier ones per shot id).
Label tweak rides only on a shot with a structural R20 change (R20_ROOT_CAUSE row #4):
  B6_12  scanner pose: the mask is flipped pattern-face DOWN, held by the chuck on its back side, pellicle hanging below;
         the mask label now says so. Active only while B6_12 is in r2_misc.R20_SHOTS (read from the module source), so a
         revert of the shot to R19 also reverts its label.
"""
import importlib.util
import os
import re

OVERLAYS = {}
NO_STORYBOARD_LABELS = set()
_HERE = os.path.dirname(os.path.abspath(__file__))


def _r20_shots():
    try:
        src = open(os.path.join(_HERE, "..", "blender", "shots", "r2_misc.py"), encoding="utf-8").read()
        m = re.search(r"^R20_SHOTS\s*=\s*\{([^}]*)\}", src, re.M)
        return set(re.findall(r"\"([A-Z0-9_]+)\"", m.group(1))) if m else set()
    except OSError:
        return set()


def _mod(module):
    spec = importlib.util.spec_from_file_location(module + "_r20mbase", os.path.join(_HERE, module + ".py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


_z18 = _mod("r2_ov_zz18m")
L, fade, _anchor, _tl, _clip = _z18.L, _z18.fade, _z18._anchor, _z18._tl, _z18._clip


def ov_B6_12(img, t, dur, W, H):
    L_ = L(W, H)
    a = fade(t, 0.25, dur * 0.6)
    _tl(L_, (0.975, 0.035), ["保护膜 pellicle", "张在金属框上，几乎透明"], a, _clip(_anchor("B6_12", t, "film", (0.42, 0.42))))
    a1 = fade(t, 0.5, dur * 0.6)
    _tl(L_, (0.975, 0.2), ["反射掩模（图形面朝下）", "卡盘吸住掩模背面"], a1, _clip(_anchor("B6_12", t, "pattern", (0.55, 0.62))))
    a2 = fade(t, dur * 0.6)
    if a2 > 0:
        ft = _clip(_anchor("B6_12", t, "gap_top", (0.6, 0.5)))
        _tl(L_, (0.975, 0.035), ["膜厚 13 nm"], a2, ft)
        g = _clip(_anchor("B6_12", t, "gap_mid", (0.6, 0.53)))
        _tl(L_, (0.975, 0.2), ["间距：膜面 ↔ 图形面", "框边剖开示意"], a2, (g[0] + 0.006, g[1]))
    return L_.compose(img).convert("RGB")


if "B6_12" in _r20_shots():
    OVERLAYS.update({"B6_12": ov_B6_12})
    NO_STORYBOARD_LABELS |= {"B6_12"}
