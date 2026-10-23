"""Round-19 overlays for the r2_misc shots (loaded after r2_ov_zz18m; entries replace earlier ones per shot id).
Label tweaks ride only on shots with a structural R19 change:
  B6_12  root cause #4 (pellicle rebuilt + mask stage anchor): the mask label names the reflective mask and the stage
         clamp it sits in (the new e-chuck / clamp jaws), otherwise the R18 two-labels-per-beat layout is unchanged
"""
import importlib.util
import os

OVERLAYS = {}
NO_STORYBOARD_LABELS = set()
_HERE = os.path.dirname(os.path.abspath(__file__))


def _mod(module):
    spec = importlib.util.spec_from_file_location(module + "_r19mbase", os.path.join(_HERE, module + ".py"))
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
    _tl(L_, (0.975, 0.2), ["反射掩模（图形面朝上）", "夹在掩模台的卡盘上"], a1, _clip(_anchor("B6_12", t, "pattern", (0.55, 0.62))))
    a2 = fade(t, dur * 0.6)
    if a2 > 0:
        ft = _clip(_anchor("B6_12", t, "gap_top", (0.6, 0.5)))
        _tl(L_, (0.975, 0.035), ["膜厚 13 nm"], a2, ft)
        g = _clip(_anchor("B6_12", t, "gap_mid", (0.6, 0.53)))
        _tl(L_, (0.975, 0.2), ["间距：膜面 ↔ 图形面", "框边剖开示意"], a2, (g[0] + 0.006, g[1]))
    return L_.compose(img).convert("RGB")


OVERLAYS.update({"B6_12": ov_B6_12})
NO_STORYBOARD_LABELS |= {"B6_12"}
