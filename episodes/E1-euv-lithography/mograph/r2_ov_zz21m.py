"""Round-21 overlays for the r2_misc shots (loaded after r2_ov_zz20m; entries replace earlier ones per shot id).
Label change rides only on the R21 structural change (R21_ROOT_CAUSE row #5):
  B6_12  3D cut-section magnifier (misc_b612_r21): in the last beat the two long crossing leaders of R20 are replaced by
         three short labels RIGHT of the magnifier (「掩模图形面」「间隙（几毫米）」「13 nm 膜」, horizontal leaders
         <= 1/5 frame width, no crossings) + 「间距不按比例」, and one short callout line from the cut to the magnifier rim.
         Active only while B6_12 is in r2_misc.R21_SHOTS (read from the module source) -> a revert also reverts labels.
"""
import importlib.util
import os
import re

OVERLAYS = {}
NO_STORYBOARD_LABELS = set()
_HERE = os.path.dirname(os.path.abspath(__file__))


def _r21_shots():
    try:
        src = open(os.path.join(_HERE, "..", "blender", "shots", "r2_misc.py"), encoding="utf-8").read()
        m = re.search(r"^R21_SHOTS\s*=\s*\{([^}]*)\}", src, re.M)
        return set(re.findall(r"\"([A-Z0-9_]+)\"", m.group(1))) if m else set()
    except OSError:
        return set()


def _mod(module):
    spec = importlib.util.spec_from_file_location(module + "_r21mbase", os.path.join(_HERE, module + ".py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


_z18 = _mod("r2_ov_zz18m")
L, fade, _anchor, _tl, _clip = _z18.L, _z18.fade, _z18._anchor, _z18._tl, _z18._clip
CYAN = _z18.CYAN


def ov_B6_12(img, t, dur, W, H):
    L_ = L(W, H)
    a = fade(t, 0.25, dur * 0.6)
    _tl(L_, (0.975, 0.035), ["保护膜 pellicle", "张在金属框上，几乎透明"], a, _clip(_anchor("B6_12", t, "film", (0.42, 0.42))))
    a1 = fade(t, 0.5, dur * 0.6)
    _tl(L_, (0.975, 0.2), ["反射掩模（图形面朝下）", "卡盘吸住掩模背面"], a1, _clip(_anchor("B6_12", t, "pattern", (0.55, 0.62))))
    a2 = fade(t, dur * 0.6)
    if a2 > 0:
        cut = _clip(_anchor("B6_12", t, "gap_mid", (0.42, 0.6)))
        rim = _clip(_anchor("B6_12", t, "mag_rim", (0.49, 0.41)))
        # callout: small ring on the cut, one short line to the magnifier rim
        x0, y0 = L_.P(cut)
        x1, y1 = L_.P(rim)
        rr = L_.px(24)
        L_.d.ellipse((x0 - rr, y0 - rr, x0 + rr, y0 + rr), outline=(*CYAN, int(230 * a2)), width=max(1, L_.px(3)))
        dx, dy = x1 - x0, y1 - y0
        dl = max(1e-6, (dx * dx + dy * dy) ** 0.5)
        L_.d.line([(x0 + dx / dl * rr, y0 + dy / dl * rr), (x1, y1)], fill=(*CYAN, int(220 * a2)), width=max(1, L_.px(2.5)))
        xs = 0.745
        for key, lines, dflt in (("mag_pat", ["掩模图形面"], (0.67, 0.33)),
                                 ("mag_gap", ["间隙（几毫米）"], (0.67, 0.38)),
                                 ("mag_mem", ["13 nm 膜"], (0.67, 0.43))):
            p = _clip(_anchor("B6_12", t, key, dflt))
            box = L_.tag((xs, p[1] - 0.021), lines, a2, size=0.03)
            if box:
                L_.leader((box[0] / W, p[1]), p, a2)
        pm = _clip(_anchor("B6_12", t, "mag_mem", (0.67, 0.43)))
        L_.text((xs, pm[1] + 0.05), "间距不按比例", 0.03, a=a2)
    return L_.compose(img).convert("RGB")


if "B6_12" in _r21_shots():
    OVERLAYS.update({"B6_12": ov_B6_12})
    NO_STORYBOARD_LABELS |= {"B6_12"}
