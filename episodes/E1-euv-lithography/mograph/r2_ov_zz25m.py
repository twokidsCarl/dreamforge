"""Round-25 overlay for A2_03 (mbeam; rides on the R25_ROOT_CAUSE row 1 structural change: the PO5 turn mirror is
staggered 0.8 m in depth so its coated face opens toward the camera -> on screen it moved up into the band where the
R17 "k1 的物理极限：0.25" tag sits). Same layout as r2_ov_zz18m (R17 formula band, NA leader on theta); only the k1 tag
moves LEFT of its leader (tag right edge at the k1 column) so the PO5 face + landing stay uncovered.
Active only while A2_03 is in r2_misc.R25_BEAM and ENABLED.
"""
import importlib.util
import os
import re

ENABLED = True
OVERLAYS = {}
NO_STORYBOARD_LABELS = set()
_HERE = os.path.dirname(os.path.abspath(__file__))
_SH = os.path.join(_HERE, "..", "blender", "shots")


def _r25(module):
    try:
        src = open(os.path.join(_SH, module + ".py"), encoding="utf-8").read()
        m = re.search(r"^R25_BEAM\s*=\s*\{([^}]*)\}", src, re.M)
        return set(re.findall(r"\"([A-Z0-9_]+)\"", m.group(1))) if m else set()
    except OSError:
        return set()


def _mod(module):
    spec = importlib.util.spec_from_file_location(module + "_r25mbase", os.path.join(_HERE, module + ".py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


if ENABLED and "A2_03" in _r25("r2_misc"):
    _z18 = _mod("r2_ov_zz18m")
    _z17 = _z18._z17
    _tag_orig = None

    def ov_A2_03(img, t, dur, W, H):
        Lcls = _z17.L

        class _L(Lcls):
            def tag(self, p, lines, a, *args, **kw):
                if lines and str(lines[0]).startswith("k₁ 的物理极限"):
                    # R25: right-anchored at the k1 column (tag left of the leader) instead of starting there
                    kx = p[0] + 0.04
                    kw["anchor"] = "ra"
                    return super().tag((kx + 0.01, p[1]), lines, a, *args, **kw)
                return super().tag(p, lines, a, *args, **kw)

        _z17.L = _L
        try:
            return _z18.ov_A2_03(img, t, dur, W, H)
        finally:
            _z17.L = Lcls

    OVERLAYS["A2_03"] = ov_A2_03
