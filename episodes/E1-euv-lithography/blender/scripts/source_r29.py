"""Round 29 hook (shots in r2_source.R29_TIN = A0_01 / B1_10 / B1_08). Layered AFTER source_r27 / source_r28.
R29_ROOT_CAUSE row 2 (material, tin step 3). One switch per sub-fix:

  TIN_R29     (row 2, all three; MAIN-PROCESS recipe tin_r29.py, looked at 8 + 32 spp before dispatch) bright silver
              (0.93, rough 0.06) + LARGE SOFT-EDGED reflection sources only in the reflection (cool sky gradient, one
              soft key box, one warm box, cool + warm grazing rims from behind) on a dim chamber base; replaces the R27
              uniform env (grey plastic) AND the R28 hard emitter shapes (decals / 「P9」 / 「?」 face). The R28 droplet
              rig (source_r28.REFL_R28) is switched off for R29 shots.
  SPLASH_R29  (row 2, A0_01 / B1_10; tin agent) the rim beads are replaced by 3-5 back-lit ligaments on the far side.

Remove a shot from r2_source.R29_TIN -> exact R28 pixels; set a switch False -> that sub-fix off.
"""
TIN_R29 = True
SPLASH_R29 = False

DROP_FRAME = {"A0_01": 72, "B1_10": 69, "B1_08": 51}
SHEET_FRAME = {"A0_01": 160, "B1_10": 69}


def pre(variant, shot, mod):
    if TIN_R29:
        import source_r28
        source_r28.REFL_R28 = False


def post(sc, variant, shot):
    if TIN_R29:
        import tin_r29
        tin_r29.apply(sc, shot, DROP_FRAME[shot], SHEET_FRAME.get(shot))
    sc.frame_set(1)
    return sc
