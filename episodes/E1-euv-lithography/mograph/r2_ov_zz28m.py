"""Round-28 overlay for B6_12 (misc agent; loaded after r2_ov_zz27m, replaces the B6_12 entry of r2_ov_zz21m).
Rides on the R28_ROOT_CAUSE row 4 structural change FILM_R28 in blender/scripts/misc_r28.py: the 3D cut-section magnifier
(misc_b612_r21) sits ~6 px out of focus in the last beat, so a 3D hair-line would smear into a plate. The membrane of the
inset is therefore DRAWN here (this overlay IS the structural fix for 「13 nm 膜画成和掩模一样厚的白板」): a crisp 1.5 px
hair-line along the membrane edge (3D anchors mag_hair_l / mag_hair_r exported by misc_r28) + two parallel break strokes
across the gap rule (gap not to scale). Labels / leaders are r2_ov_zz21m's, unchanged.
Active only while B6_12 is in r2_misc.R28_MISC and FILM_R28 is True (read from the sources) and ENABLED.
"""
import importlib.util
import os
import re

from PIL import Image, ImageDraw

ENABLED = True
OVERLAYS = {}
NO_STORYBOARD_LABELS = set()
_HERE = os.path.dirname(os.path.abspath(__file__))
_BL = os.path.join(_HERE, "..", "blender")
SS = 4                                           # supersampling for anti-aliased thin lines


def _set(path, name):
    try:
        src = open(path, encoding="utf-8").read()
        m = re.search(r"^" + name + r"\s*=\s*\{([^}]*)\}", src, re.M)
        return set(re.findall(r"\"([A-Z0-9_]+)\"", m.group(1))) if m else set()
    except OSError:
        return set()


def _switch(name):
    try:
        src = open(os.path.join(_BL, "scripts", "misc_r28.py"), encoding="utf-8").read()
        m = re.search(r"^" + name + r"\s*=\s*(True|False)", src, re.M)
        return bool(m and m.group(1) == "True")
    except OSError:
        return False


def _mod(module):
    spec = importlib.util.spec_from_file_location(module + "_r28mbase", os.path.join(_HERE, module + ".py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


_R28 = _set(os.path.join(_BL, "shots", "r2_misc.py"), "R28_MISC") if ENABLED else set()

if "B6_12" in _R28 and _switch("FILM_R28"):
    from r2_ov_common import anchor, fade

    _z21 = _mod("r2_ov_zz21m")
    _base = _z21.ov_B6_12

    def ov_B6_12(img, t, dur, W, H):
        img = _base(img, t, dur, W, H)
        a = fade(t, dur * 0.6)
        pl, pr = anchor("B6_12", t, "mag_hair_l", None), anchor("B6_12", t, "mag_hair_r", None)
        c, px_, py_ = (anchor("B6_12", t, k, None) for k in ("mag_brk_c", "mag_brk_x", "mag_brk_y"))
        if a <= 0 or None in (pl, pr, c, px_, py_):
            return img
        lay = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))
        d = ImageDraw.Draw(lay)
        S = lambda p: (p[0] * W * SS, p[1] * H * SS)
        w = max(1, round(1.5 * H / 540 * SS))
        d.line([S(pl), S(pr)], fill=(236, 240, 246, int(250 * a)), width=w)          # the 13 nm membrane: a hair-line
        # break strokes: two parallel slanted strokes across the gap rule (gap shown broken = not to scale)
        ux, uy = px_[0] - c[0], px_[1] - c[1]
        vx, vy = py_[0] - c[0], py_[1] - c[1]
        for o in (-0.22, 0.22):
            p0 = (c[0] - ux * 0.75 + vx * (o - 0.25), c[1] - uy * 0.75 + vy * (o - 0.25))
            p1 = (c[0] + ux * 0.75 + vx * (o + 0.25), c[1] + uy * 0.75 + vy * (o + 0.25))
            d.line([S(p0), S(p1)], fill=(120, 224, 232, int(240 * a)), width=max(1, round(2.0 * H / 540 * SS)))
        lay = lay.resize((W, H), Image.LANCZOS)
        out = img.convert("RGBA")
        out.alpha_composite(lay)
        return out.convert("RGB")

    OVERLAYS["B6_12"] = ov_B6_12
    NO_STORYBOARD_LABELS |= {"B6_12"}
