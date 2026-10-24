"""Round 25 hook (owned by the 'cbeam' sub-agent; shots in r2_cutaway.R25_BEAM = A0_10 / C_03 / B5_01).
R25_ROOT_CAUSE row 1 (turn points = solid visible mirrors, beam_r25.chain / check) + row 2 (tapered shell cones).
Layered AFTER cut_beam_r24 (its R24 chain objects are deleted here and rebuilt with beam_r25).

A0_10: pre() moves build_cutaway_r2.FFM onto the collector axis beyond the IF (IF passed straight) and the PFM up-right
       / deeper so IF -> FFM -> PFM -> mask -> projection mirror -> wafer is one forward zig (no crossing); the builder's
       own field-facet / pupil-facet models land on those stops with exactly the reflection-bisector normal (the
       kit_r2.mirror_normal calls for these two are answered by _mn). The turn stops are staggered in depth and the
       R24 dolly is orbited (az 15.8 / el 5 deg about the machine centre, sketch cbeam/sk/srch.py) so every turn
       mirror is >= 30 deg out of edge-on. Helpers: cut_beam_r25_a010.py.
C_03 / B5_01: cut_beam_r25_swap.py (beam_r24 -> beam_r25 swap, existing scene mirrors, shell legs).
SHOTS switches each shot (removed -> R24 pixels).
"""
import bpy
from mathutils import Vector

SHOTS = {"A0_10", "C_03", "B5_01"}   # candidates R25 cbeam: B5_01 only (A0_10 / C_03 not GO, see SMOKE.md)
B501_PFM_DY = 0.15
JOB = {"A0_10": (54, 119, 184), "B5_01": (29, 64, 99), "C_03": (101, 222, 343)}


def pre(variant, shot, mod):
    if shot not in SHOTS:
        return
    if shot == "A0_10":
        import cut_beam_r25_a010 as A
        A.pre()
    else:                                  # C_03 / B5_01: cut_beam_r24 builds its path with beam_r25 (swap)
        import cut_beam_r25_swap as S
        S.swap()
        if shot == "B5_01":                # row 1: PFM (still straight below the FFM in x/z) 0.15 m deeper -> face opens at f29
            import build_cutaway_r2 as B
            B.PFM = B.PFM + Vector((0, B501_PFM_DY, 0))
            print("[r25c] B5_01 PFM ->", tuple(round(x, 3) for x in B.PFM))


def post(sc, variant, shot):
    if shot not in SHOTS:
        return sc
    if shot == "A0_10":
        import cut_beam_r25_a010 as A
        A.post(sc)
    else:
        import cut_beam_r25_swap as S
        S.restore()
    return sc
