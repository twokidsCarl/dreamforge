"""Round 31 hook (MAIN process; shots in r2_source.R31_TIN = A0_01 / B1_10). Layered after source_r30 and before
beam_hook_r29.

  DISC_R31 (row 2, A0_01 / B1_10): tin step 5 - tin_r31.disc() reshapes the R29 sheet mesh into a thin, slightly curved
           disc with a broken edge in its plane (no crown, no drops, no glowing rim), high-reflect liquid metal with an
           orange-red hot face. pre() turns source_r30.SHAPE_R30 off for these shots (the R30 crown / rim glow = the
           「白瓷碗 / 贝壳」 read); the R29 reflection recipe (tin_r29) stays as it is.
Remove a shot from R31_TIN -> R30 pixels; DISC_R31 False -> R30 pixels.
"""
SHEET_FRAME = {"A0_01": 160, "B1_10": 69}
DISC_R31 = True


def pre(variant, shot, mod):
    if DISC_R31 and shot in SHEET_FRAME:
        import source_r30
        source_r30.SHAPE_R30 = False


def post(sc, variant, shot):
    if DISC_R31 and shot in SHEET_FRAME:
        import tin_r31
        tin_r31.disc(sc, shot, SHEET_FRAME[shot])
        sc.frame_set(1)
    return sc
