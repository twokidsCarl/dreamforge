"""Round 26 hook (owned by the 'tin' sub-agent; shots in r2_source.R26_TIN = A0_01 / B1_08). R26_ROOT_CAUSE row 3
(camera on the tin content: push in toward the plasma + visible laser landing + thinner film). The R25 liquid-tin
MATERIAL is frozen (no material parameter is touched here). Layered AFTER the R25 hooks (source_r25 runs first).

  A0_01  pre():  thinner film (source_r24_tin HT / HE: total centre thickness D/80 -> D/150; overrides the R25
                 CROWN lip HE).
         post(): camera re-key = every key of CamR2 pulled toward its own target by PUSH (the D motion - droplet ->
                 sheet -> plasma pan / lens ramps - is kept, only the distance shrinks); orange laser-landing glow on
                 the laser-facing rim of the sheet while the main pulse hits (source_r26_tin.landing_rim).
  B1_08  post(): camera re-key (PUSH) - the HUD reticles / lock rings are 3D children of each droplet, so the lock
                 stays in sync; the pending-laser dashes are extended to the lock point and ride at the height of
                 the droplet nearest the lock line (snap to the next one) = the aim line always ends on a droplet.
Remove a shot from r2_source.R26_TIN -> exact R25 pixels.
"""
import bpy

FILM = {"A0_01": (0.0065, 0.0050)}        # (HT, HE) unit-radius sheet -> total centre thickness 0.013 = D / 150
PUSH = {"A0_01": {150: 0.74, 290: 0.62}, "B1_08": 0.80}   # camera distance factor to its target (per key frame)
LANDING = {"A0_01": (150, 166)}           # main-pulse window (hit2 - 4 .. boom)
DASH_LAND = {"B1_08"}


def pre(variant, shot, mod):
    if shot in FILM:
        import source_r24_tin as T24
        T24.HT, T24.HE = FILM[shot]


def post(sc, variant, shot):
    import source_r26_tin as T
    if shot in PUSH:
        T.push_camera(sc, PUSH[shot])
    if shot in LANDING:
        T.landing_rim(*LANDING[shot])
    if shot in DASH_LAND:
        T.dash_to_lock(mod_coll_x=-0.9)
        T.dash_follow(sc.frame_end)
    sc.frame_set(1)
    return sc
