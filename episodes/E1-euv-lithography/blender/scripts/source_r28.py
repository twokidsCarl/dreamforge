"""Round 28 hook (owned by the 'tin' sub-agent; shots in r2_source.R28_TIN = A0_01 / B1_10 / B1_08). Layered AFTER
source_r27 (MAT_R27 tin material / sheet yaw / edge bead, PULSE2_R27, AIM_R27 stay as they are underneath).

R28_ROOT_CAUSE row 1 (material, tin step 2). One switch per sub-fix:

  REFL_R28    (row 1, all three) the R27 uniform soft env (= 「灰色哑光塑料盘」) is replaced by a DARK chamber with
              DISCRETE, NAMEABLE bright sources that only rays leaving the tin see (glossy + short ray length):
              sheet (A0_01 / B1_10): real emitter geometry near the face's mirror direction = a 2x2-pane rectangular
              chamber viewport window, a warm flange ring, a violet plasma blob, a cool window strip (helper
              source_r28_tin.sheet_rig). Droplets: the env sphere keeps its place but its bands are swapped for a
              dark base + a round viewport (key), a flange ring, a violet point and a thin rim from behind
              (source_r28_tin.drop_bands). No continuous bands (R25 「条纹星球」), no uniform soft light (R27).
  BREAK_R28   (row 1, A0_01 / B1_10) sheet breakup: low-frequency thickness undulation, 3 local holes near the rim,
              radial ligaments with beads at the edge, satellites at random positions / random sizes (replaces the
              evenly spaced R24 ring = 「铆钉」). Helper source_r28_tin.breakup.
  PULSE2_R28  (row 1, A0_01) main pulse = thin, soft-edged converging beam (source_r19 cone, like the pre-pulse but
              brighter / wider at the source) that lights up only at the landing on the sheet; on screen from
              P2_SHOW (covers job frame 160) to boom; the pre-pulse's thin cone gets a faint fading afterglow so
              f160 shows two orange shots (the spent first one fading + the second one landing).

  REFL_SHEET  (sub-switch of REFL_R28, main process 32-spp Q4) False: the sheet rig (crisp white window / ring shapes on
              a now mostly dark disc) reads as white decals / letters printed on a black disc (B1_10 f107 「P9」, A0_01
              f160 window-logo) = new misread -> sheets keep the R27 env; the droplet rigs (B1_08 / A0_01 droplet) stay.

Remove a shot from r2_source.R28_TIN -> exact R27 pixels; set a switch False -> that sub-fix off.
"""
import bpy

REFL_R28 = True
BREAK_R28 = True
PULSE2_R28 = True
REFL_SHEET = False   # main 32-spp Q4 no on A0_01 / B1_10 sheets (decal / letters read) -> R27 sheet env kept

SHEETS = {"A0_01", "B1_10"}


def post(sc, variant, shot):
    import source_r28_tin as T
    if BREAK_R28 and shot in SHEETS:
        T.breakup(shot)
    if REFL_R28:
        if REFL_SHEET:
            T.reflections(sc, shot)
        else:
            T.drop_rigs(sc, shot)
    if PULSE2_R28 and shot == "A0_01":
        T.pulse2(sc)
    sc.frame_set(1)
    return sc
