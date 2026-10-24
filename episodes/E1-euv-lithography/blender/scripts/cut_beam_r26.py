"""Round 26 hook (owned by the 'cbeam' sub-agent; shots in r2_cutaway.R26_BEAM = C_03 / B5_01).
R26_ROOT_CAUSE row 2: cut_beam_r24's R24 chains are built with the shared beam_r26 soft shell (cut_beam_r26_swap.py,
same swap pattern as R25 cut_beam_r25_swap.py; existing scene mirrors, no new mirrors).
B5_01 also keeps the R25 row-1 PFM shift (+0.15 m deeper so the pupil-facet face opens at f29).
SHOTS switches each shot (removed -> R25 pixels = R24 build)."""
from mathutils import Vector

SHOTS = {"C_03", "B5_01"}
B501_PFM_DY = 0.15
C03_REPATH = {"C_03"}                  # C_03: IF -> FFM -> PFM -> MASK (G1 / G2 off the path), cut_beam_r26_c03.py
FACETS = set()                         # row 4 trial (B5_01 strips +-7 deg tilt + 3 tones, cut_beam_r26_facets.py): marginal read, jumbled lower strips -> off; see SMOKE.md


def pre(variant, shot, mod):
    if shot not in SHOTS:
        return None
    import cut_beam_r26_swap as S
    S.swap(shot)
    if shot in C03_REPATH:
        import cut_beam_r26_c03 as C
        C.pre()
    if shot == "B5_01":
        import build_cutaway_r2 as B
        B.PFM = B.PFM + Vector((0, B501_PFM_DY, 0))
        print("[r26c] B5_01 PFM ->", tuple(round(x, 3) for x in B.PFM), flush=True)
    return None


def post(sc, variant, shot):
    if shot not in SHOTS:
        return sc
    import cut_beam_r26_swap as S
    if shot in C03_REPATH:
        import cut_beam_r26_c03 as C
        C.post(sc)
    S.restore()
    if shot in FACETS:
        import build_cutaway_r2 as B
        import cut_beam_r26_facets as F
        F.post(sc, B.FFM, B.IF)
    return sc
