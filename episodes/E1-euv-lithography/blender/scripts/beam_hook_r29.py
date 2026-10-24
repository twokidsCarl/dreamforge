"""Round 29 hook (MAIN process, R29_ROOT_CAUSE row 1 - beam geometry as one shared row). Layered LAST in every scene
module's R29 hook list (r2_cutaway.R29_BEAM, r2_source.R29_BEAM, r2_misc.R29_BEAM), after all R22..R29 per-shot hooks
have built their legs. One switch:

  BEAM_R29 (row 1): every beam_r25 / beam_r26 leg in the shot -> beam_r29 volume cone (real converging / diverging
      cross-section between the two landings, centre-bright Gaussian falloff, background visible through; landing spots
      on the faces x1.6). Shots with a story order get beam_r29.levels(): current leg 1.0, others 0.6 (whole path every
      frame) - this REPLACES cut_r28.ONEPATH_R28 (non-current legs at 14-17 % read as 「缺段」 in R28).
Remove a shot from its R29_BEAM set -> that shot's pre-R29 beams (R28 pixels if no other R29 row touches it).
"""
import beam_r29 as B29

BEAM_R29 = True

STRENGTH = {"B1_15": 1.1, "B3_02": 0.55}   # per-shot centre-line radiance B (default beam_r29.B_DEFAULT 1.6): the two collector cones whose wide end lies over the mirror face are dimmer (8 spp: violet haze over the bowl)
SKIP = {}              # per-shot leg name prefixes kept as they were (e.g. gas streams that are not light)
WINDOWS = {
    "B5_01": ("IllumPathR24", [(0, 0.0, 0.40), (1, 0.40, 0.70), (2, 0.70, 1.0)]),
    "B7_06": ("PO27Beam", [(0, 0.0, 0.42), (1, 0.42, 0.70), (2, 0.70, 1.0)]),
}


def pre(variant, shot, mod):
    if BEAM_R29 and shot in WINDOWS:
        import cut_r28
        cut_r28.ONEPATH_R28 = False


def post(sc, variant, shot):
    if not BEAM_R29:
        return sc
    if shot in WINDOWS:
        # whole path every frame: landing spots revealed by keys (B7_06 R27 key_chain) are shown from frame 1
        import bpy
        nm = WINDOWS[shot][0]
        for o in bpy.data.objects:
            if o.name.startswith(nm + "Spot"):
                if o.animation_data:
                    o.animation_data_clear()
                o.hide_render = False
    done = B29.convert(sc, STRENGTH.get(shot, B29.B_DEFAULT), skip=SKIP.get(shot, ()), tag=shot)
    if shot in WINDOWS:
        name, win = WINDOWS[shot]
        legs = []
        for i in range(len(win)):
            k = f"{name}Leg{i}"
            legs.append([v for o, v in done.items() if o == k or o.startswith(k + ".")] or None)
        B29.levels(sc, legs, win, tag=shot)
    return sc
