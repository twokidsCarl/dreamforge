"""Round-23 overlays for the cutb shots (cutb agent; loaded after r2_ov_zz22*, entries replace earlier ones per shot id).
Rides only on the R23 structural change of B8_03 (R23_ROOT_CAUSE row 5: dark-Si wafer with one grazing band + row 2
slow push / focus pull, scripts/cut_2b_r23*.py):
  B8_03  the reticle-stage picture-in-picture (B8_03M pass) enlarged to ~1/3 of the screen area (R22 review
         「画中画放大到 1/3 屏」, it was 0.39 x 0.36 = 14 %) -> 0.96 x 0.35 = 34 %, a full-width band across the top (mask stage above, wafer stage below); same r2_ov_zz18 'scan' drawing
         (8 : 1 read-out, progress lines), only the box changes.
Active only while B8_03 is in r2_cutaway.R23_2B (read from the module source) and ENABLED -> a revert also reverts this.
"""
import importlib.util
import os
import re

ENABLED = True
OVERLAYS = {}
NO_STORYBOARD_LABELS = set()
_HERE = os.path.dirname(os.path.abspath(__file__))
# 8-spp try 1 top-right 0.615 x 0.54: hid the incoming beam; try 2 top-left 0.54 x 0.6: covered half the pushed-in wafer.
# -> a full-width band across the top (0.96 x 0.35 = 34 %): reticle stage on top, wafer stage below, the beam runs
#    from under the band down to the slit - the two stages read stacked like the machine (mask above, wafer below).
PIP_BOX_R23 = (0.02, 0.015, 0.98, 0.365)
PIP_CROP_R23 = (0.0, 0.15, 1.0, 0.54)           # ruler 0-80 + carriage + mask; aspect 4.55 vs box 4.68 (3 % stretch)


def _r23_2b():
    try:
        src = open(os.path.join(_HERE, "..", "blender", "shots", "r2_cutaway.py"), encoding="utf-8").read()
        m = re.search(r"^R23_2B\s*=\s*\{([^}]*)\}", src, re.M)
        return set(re.findall(r"\"([A-Z0-9_]+)\"", m.group(1))) if m else set()
    except OSError:
        return set()


def _mod(module):
    spec = importlib.util.spec_from_file_location(module + "_r23bbase", os.path.join(_HERE, module + ".py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


if ENABLED and "B8_03" in _r23_2b():
    _z18 = _mod("r2_ov_zz18")
    _z18._zu.PIP_BOX = PIP_BOX_R23              # private copy of r2_ov_zu13 inside this zz18 instance only
    _z18._zu.PIP_CROP = PIP_CROP_R23
    OVERLAYS["B8_03"] = _z18.OVERLAYS["B8_03"]
    NO_STORYBOARD_LABELS.add("B8_03")
