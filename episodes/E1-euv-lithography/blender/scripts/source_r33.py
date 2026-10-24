"""Round 33 hook (MAIN process; shots in r2_source.R33_TIN = A0_01 / B1_10 / B1_08). Layered after source_r32 and before
beam_hook_r29.

  DISC_R33 (row 3, A0_01 / B1_10 + the same part in B1_08): R32 p1 「薄饼像一块凸透镜 / 玻璃片」「仍像玻璃透镜 / 化妆镜：
           中间是镜面反射斑块，边缘橙色像镜框」「锡滴读成深色玻璃弹珠」. tin_r33.disc() rebuilds the R32 regular round disc
           with a thick rolled bead edge + gentle concentric wrinkles, satin liquid-tin material reflecting the real
           chamber (the sheet env sphere with its white key box hidden) and the warm glow only on the laser-side arc;
           tin_r33.drops() gives the B1_08 droplets the same liquid-tin material (drop env spheres hidden). pre() turns
           source_r32.DISC_R32 off for the sheet shots (R33 rebuilds the mesh itself).
Remove a shot from R33_TIN -> R32 pixels; DISC_R33 False -> R32 pixels.
"""
SHEET_FRAME = {"A0_01": 160, "B1_10": 69}
DROP_SHOTS = {"B1_08"}
DISC_R33 = True


def pre(variant, shot, mod):
    if DISC_R33 and shot in SHEET_FRAME:
        import source_r32
        source_r32.DISC_R32 = False
        import source_r30
        import source_r31
        source_r30.SHAPE_R30 = False
        source_r31.DISC_R31 = False


def post(sc, variant, shot):
    if not DISC_R33:
        return sc
    import tin_r33
    if shot in SHEET_FRAME:
        tin_r33.disc(sc, shot, SHEET_FRAME[shot])
        sc.frame_set(1)
    elif shot in DROP_SHOTS:
        tin_r33.drops(sc, shot)
    return sc
