"""Round-22 overlays for the r2_misc shots (misc agent; loaded after r2_ov_zz21m, entries replace earlier ones per shot id).
Rides only on the R22 structural change (R22_ROOT_CAUSE row 5, misc_b817_r22: exposed fields grey up in step with the
counter):
  B8_17  same counter block as r2_ov_zr8 'wafer' (identical count curve, which misc_b817_r22 drives the field shader with),
         the 「188」 field counter drawn in white instead of EUV violet (R21 review #3「紫色只该代表 EUV 光…改成白色或计量青」).
Active only while B8_17 is in r2_misc.R22_SHOTS (read from the module source) and ENABLED -> a revert also reverts this.
"""
import importlib.util
import os
import re

ENABLED = True
OVERLAYS = {}
NO_STORYBOARD_LABELS = set()
_HERE = os.path.dirname(os.path.abspath(__file__))


def _r22_shots():
    try:
        src = open(os.path.join(_HERE, "..", "blender", "shots", "r2_misc.py"), encoding="utf-8").read()
        m = re.search(r"^R22_SHOTS\s*=\s*\{([^}]*)\}", src, re.M)
        return set(re.findall(r"\"([A-Z0-9_]+)\"", m.group(1))) if m else set()
    except OSError:
        return set()


def _mod(module):
    spec = importlib.util.spec_from_file_location(module + "_r22mbase", os.path.join(_HERE, module + ".py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


if ENABLED and "B8_17" in _r22_shots():
    _zr8 = _mod("r2_ov_zr8")
    _zr8.VIOLET = _zr8.INK                     # module global read by wafer(): 188 counter -> white
    OVERLAYS["B8_17"] = _zr8.OVERLAYS["B8_17"]
    NO_STORYBOARD_LABELS.add("B8_17")
