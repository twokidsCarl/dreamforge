"""Round-31 overlay for B8_03 (kit agent; rides on the R31_ROOT_CAUSE row 5 structural change scripts/cut_kit_r31.py).
R30 p2 B8_03 「①晶圆台加一条同款细标尺（0–10 mm），三帧指针明显向左走…②画中画里露出掩模图形面 + 狭缝光斑，标尺标题写
『掩模台行程』」.
- RULER_R31 (3D fixed wafer-stage ruler + needle): title 「晶圆台行程」 left of the ruler plate (anchors k31_t0, merged into
  the B8_03 anchors json by the hook).
- PIP_R31 (PIP camera tilted up onto the mask's patterned face): the PIP crop is re-framed to ruler + mask face, the PIP
  ruler gets the title 「掩模台行程」 and a short leader 「掩模图形面」 to the moving mask.
Everything else = the R30 zz30k drawing (PIP band, read-out tag top right). Active only while B8_03 is in
r2_cutaway.R31_KIT (and R30_KIT, which zz30k needs) and the hook switch is True -> a revert also reverts this."""
import importlib.util
import os
import re

from r2_ov_common import CYAN, FPS, Layer, anchor, fade

ENABLED = True
OVERLAYS = {}
NO_STORYBOARD_LABELS = set()
_HERE = os.path.dirname(os.path.abspath(__file__))
PIP_CROP_R31 = (0.0, 0.25, 1.0, 0.615)     # R31 PIP camera: ruler 0-80 (raw y 137-198) + mask face (raw y 272-331)


def _set(module, name):
    try:
        src = open(os.path.join(_HERE, "..", "blender", "shots", module + ".py"), encoding="utf-8").read()
        m = re.search(r"^" + name + r"\s*=\s*\{([^}]*)\}", src, re.M)
        return set(re.findall(r"\"([A-Z0-9_]+)\"", m.group(1))) if m else set()
    except OSError:
        return set()


def _switch(name):
    try:
        src = open(os.path.join(_HERE, "..", "blender", "scripts", "cut_kit_r31.py"), encoding="utf-8").read()
        return re.search(r"^" + name + r"\s*=\s*True\b", src, re.M) is not None
    except OSError:
        return False


def _mod(module):
    spec = importlib.util.spec_from_file_location(module + "_r31kbase", os.path.join(_HERE, module + ".py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


_K31 = _set("r2_cutaway", "R31_KIT")
_RUL, _PIP = _switch("RULER_R31"), _switch("PIP_R31")

if ENABLED and "B8_03" in _K31 and (_RUL or _PIP) and "B8_03" in _set("r2_cutaway", "R30_KIT") \
        and "B8_03" in _set("r2_cutaway", "R23_2B"):
    _z30 = _mod("r2_ov_zz30k")
    _zu, _zr8 = _z30._zu, _z30._zr8
    if _PIP and "B8_03M" in _K31:
        _zu.PIP_CROP = PIP_CROP_R31
    if _RUL:
        # the zz18 2D wafer travel line sat on the old R28 tick bar (hidden by RULER_R31): the 3D ruler's own cyan
        # travel bar + needle replace it -> its two anchors are sent off-frame in this private zz30k instance
        def _anchor31(sid, t, name, default):
            if sid == "B8_03" and name in ("wr0", "wr1"):
                return (-1.0, -1.0)
            return anchor(sid, t, name, default)
        _z30.anchor = _anchor31

    def scan31(img, t, dur, W, H):
        out = _z30.scan30(img, t, dur, W, H)
        a = fade(t, 0.3)
        L = Layer(W, H)
        PB, PC = _zu.PIP_BOX, _zu.PIP_CROP

        def to_pip(p):
            return (PB[0] + (p[0] - PC[0]) / (PC[2] - PC[0]) * (PB[2] - PB[0]),
                    PB[1] + (p[1] - PC[1]) / (PC[3] - PC[1]) * (PB[3] - PB[1]))
        if _PIP and "B8_03M" in _K31 and _zu._pip_frame(int(round(t * FPS)) + 1) is not None:
            r0 = to_pip(anchor("B8_03M", t, "rr0", (0.3, 0.3)))
            L.text((r0[0] - 0.035, PB[1] + 0.052), "掩模台行程", 0.034, CYAN, a, anchor="rm")
            # the mask (centre = the PIP pointer x, same carriage) : leader from its right end
            n = max(2, round(dur * FPS))
            u = _zr8.scan_u(int(round(t * FPS)) + 1, n)
            r1 = to_pip(anchor("B8_03M", t, "rr1", (0.7, 0.3)))
            mx = r0[0] + (r1[0] - r0[0]) * u + 0.178     # right end of the 1.56 m plate
            my = to_pip((0.0, 0.565))[1]
            L.leader((mx, my), (mx + 0.05, my), a)
            L.tag((mx + 0.06, my - 0.016), ["掩模图形面"], a, size=0.03)     # dark tag: readable over the lamp
        if _RUL:
            p = anchor("B8_03", t, "k31_t0", None)
            if p is not None:
                L.text((p[0], p[1]), "晶圆台行程", 0.032, CYAN, a, anchor="rm")
        return L.compose(out)

    OVERLAYS["B8_03"] = scan31
    NO_STORYBOARD_LABELS.add("B8_03")
