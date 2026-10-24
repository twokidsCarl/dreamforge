"""Round 32 hook (MAIN process; shots in r2_source.R32_TIN = A0_01 / B1_10). Layered after source_r31 and before
beam_hook_r29.

  DISC_R32 (row 2, A0_01 / B1_10): Carl t381 「锡片应是规则圆盘…预脉冲把锡滴压成近圆的薄饼」 - tin_r32.disc() REBUILDS
           the sheet mesh as a regular near-round thin disc (smooth continuous round edge, thinning toward the rim with
           a slight rounded lip, no notches / fragments), liquid-tin material with a warm laser-facing glow + heated rim;
           the R24-R31 riders on the sheet are hidden. pre() turns source_r31.DISC_R31 off for these shots (the R31
           broken edge = 「撕开的灰纸片 / 玻璃碎片」).
Remove a shot from R32_TIN -> R31 pixels; DISC_R32 False -> R31 pixels.
"""
SHEET_FRAME = {"A0_01": 160, "B1_10": 69}
DISC_R32 = True


def pre(variant, shot, mod):
    if DISC_R32 and shot in SHEET_FRAME:
        import source_r30
        import source_r31
        source_r30.SHAPE_R30 = False
        source_r31.DISC_R31 = False


def post(sc, variant, shot):
    if DISC_R32 and shot in SHEET_FRAME:
        import tin_r32
        tin_r32.disc(sc, shot, SHEET_FRAME[shot])
        sc.frame_set(1)
    return sc
