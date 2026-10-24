"""Round-27 overlays for the r2_misc shots (misc agent; loaded after r2_ov_zz26a, entries replace earlier ones per shot id).
Rides only on the R27_ROOT_CAUSE row 5 structural changes in blender/scripts/misc_r27.py and follows its switches:
  B8_17  (GRID_R27) counter block as r2_ov_zr8 'wafer' / r2_ov_zz22m (same count curve that drives the field shader, 188 in
         white): the box height grows with the rows shown, and the 「3.4 万+」 row only enters after 场/片 and 片/小时 are
         complete, preceded by the small product 「188 × 185 = 34,780」 (R26 p3 「3.4 万+ 那行要等『188 × 185』算完再出」).
  A0_06  (GLOBE_R27) the 「荷兰 · 整机总装」 tag moves off the globe (left, in space) and its leader ends ON the NL ring
         (52N 5E, 3D anchor 'nl') with an end dot (R26 p3 「引线落在地中海…引线锚点改到中心环上」); counter block unchanged.
Active only while the shot is in r2_misc.R27_MISC and the row switch is True (read from the sources) and ENABLED.
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
        src = open(os.path.join(_BL, "scripts", "misc_r27.py"), encoding="utf-8").read()
        m = re.search(r"^" + name + r"\s*=\s*(True|False)", src, re.M)
        return bool(m and m.group(1) == "True")
    except OSError:
        return False


def _mod(module):
    spec = importlib.util.spec_from_file_location(module + "_r27mbase", os.path.join(_HERE, module + ".py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


_R27 = _set(os.path.join(_BL, "shots", "r2_misc.py"), "R27_MISC") if ENABLED else set()

if "B8_17" in _R27 and _switch("GRID_R27"):
    from r2_ov_common import CYAN, INK, INK2, Layer, ease, fade

    def ov_B8_17(img, t, dur, W, H):
        L = Layer(W, H)
        u = t / dur
        a0 = fade(t, 0.1)
        p0 = ease(u / 0.8)                       # 场 / 片 (same curve as misc_b817_r22.counter)
        p1 = ease((u - 0.3) / 0.4)               # 片 / 小时
        s2 = 0.8                                 # product row only after both are complete
        ax = fade(t, dur * s2)
        p2 = ease((u - (s2 + 0.015)) / 0.03)
        nrow = 1 + (u >= 0.3) + (u >= s2)
        if a0 > 0:
            y1 = 0.04 + 0.03 + nrow * 0.115 + (0.03 if nrow == 3 else 0.0)
            L.d.rounded_rectangle((0.74 * W, 0.04 * H, 0.97 * W, y1 * H), radius=int(H * 0.012),
                                  fill=(8, 11, 20, int(190 * a0)))
        rows = [(str(int(round(188 * p0))), "场 / 片", INK, fade(t, 0.0)),
                (str(int(round(185 * p1))) + ("+" if p1 >= 1 else ""), "片 / 小时", CYAN, fade(t, dur * 0.3))]
        for k, (s, unit, col, a) in enumerate(rows):
            if a <= 0:
                continue
            y = 0.055 + k * 0.115
            L.text((0.76, y), s, 0.052, col, a, mono=s.replace("+", "").isdigit())
            L.text((0.76, y + 0.066), unit, 0.026, INK2, a)
        if ax > 0:
            y = 0.055 + 2 * 0.115
            L.text((0.76, y), "188 × 185 =", 0.026, INK2, ax)
            if p2 > 0:
                s = "3.4 万+" if p2 >= 1 else f"{int(round(34780 * p2)):,}"
                L.text((0.76, y + 0.032), s, 0.052, INK, ax, mono=s.replace(",", "").isdigit())
                L.text((0.76, y + 0.098), "次曝光 / 小时", 0.026, INK2, ax)
        return L.compose(img)

    OVERLAYS["B8_17"] = ov_B8_17
    NO_STORYBOARD_LABELS.add("B8_17")

if "A0_06" in _R27 and _switch("GLOBE_R27"):
    _z18 = _mod("r2_ov_zz18m")

    def ov_A0_06(img, t, dur, W, H):
        L_ = _z18.L(W, H)
        u = t / dur
        a = _z18.fade(t, 0.1)
        n = int(round(5100 * _z18.ease(min(1.0, (u - 0.02) / 0.8))))
        L_.panel((0.745, 0.045, 0.975, 0.285), a)
        L_.text((0.765, 0.06), f"{n:,}", 0.085, _z18.CYAN, a, kind="mono", glow=0.5)
        L_.text((0.765, 0.165), "家供应商", 0.04, _z18.INK, a)
        L_.text((0.765, 0.235), "来源：ASML 年报 · 光点为示意", 0.024, _z18.INK2, a)
        pn = _z18._clip(_z18._anchor("A0_06", t, "nl", (0.49, 0.36)))
        a2 = _z18.fade(t, dur * 0.45)
        if a2 > 0:
            # tag in empty space LEFT of the globe, leader from its right edge straight onto the NL ring
            tp = (0.035, max(0.30, min(0.70, pn[1] + 0.10)))
            box = L_.tag(tp, ["荷兰 · 整机总装"], a2, anchor="lt", accent=_z18.INK)
            x0 = (box[2] / W + 0.004) if box else 0.2
            y0 = ((box[1] + box[3]) / 2 / H) if box else tp[1]
            L_.leader((x0, y0), pn, a2, color=_z18.INK)
            r = max(3, int(H * 0.009))
            cx, cy = pn[0] * W, pn[1] * H
            try:
                L_.d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(*_z18.INK, int(240 * a2)),
                             width=max(2, int(H / 360)))
            except AttributeError:
                pass
        return L_.compose(img).convert("RGB")

    OVERLAYS["A0_06"] = ov_A0_06
    NO_STORYBOARD_LABELS.add("A0_06")
