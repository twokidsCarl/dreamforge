"""R23 hook for B7_06 / A0_10 / B8_03 / B8_03M (cutb; R23_ROOT_CAUSE rows 2 / 3 / 5). Runs after the R22 hooks.

Per shot gating: CAM (row 2 camera motion), PATH (row 3 A0_10 light chain), WAFER (row 5 B8_03 wafer).
Removing a shot from r2_cutaway.R23_2B (or from these sets) -> exact R22 pixels.
"""
CAM = {"B7_06", "A0_10", "B8_03"}
PATH = {"A0_10"}
WAFER = {"B8_03", "B8_03M"}


def pre(variant, shot, mod):
    pass


def post(sc, variant, shot):
    import cut_2b_r23_cam as CC
    if shot == "A0_10" and shot in CAM:      # camera first: the path's occluder ray-cast uses the R23 camera
        CC.a0_10(sc)
    if shot in PATH:
        try:
            import cut_2b_r23_path as P
            P.post(sc)
        except ImportError:
            pass
    if shot in WAFER:
        try:
            import cut_2b_r23_wafer as W
            W.post(sc, shot)
        except ImportError:
            pass
    if shot in CAM:
        if shot == "B7_06":
            CC.b7_06(sc)
        elif shot == "B8_03":
            CC.b8_03(sc, shot)
