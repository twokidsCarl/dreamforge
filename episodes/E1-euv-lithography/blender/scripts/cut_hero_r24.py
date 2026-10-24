"""Round 24 hook (owned by the 'chero' sub-agent; shots in r2_cutaway.R24_HERO). Runs after the R22 / R23 hooks.
Per shot (remove a shot from r2_cutaway.R24_HERO or from these sets -> exact R23 pixels):
  B7_06  rows 3 + 5: solid polished M5/M6 ring mirrors (hole 22 % of the diameter) + ONE beam_r24 chain
         (cut_hero_r24_b706)
  B8_03 / B8_03M rows 3 + 5: no full-width wafer band (local weak glint only), pure violet slit, beam_r24 narrow cone
         opening upward from the slit (cut_hero_r24_b803)
  B3_02  rows 3 + 5: collector enlarged on the same ellipsoid R 0.68 -> 1.25 m, vessel rebuilt around it, laser kept,
         sketch camera, beam_r24 rim -> IF cone (cut_hero_r24_b302)
"""
SHOTS = {"B7_06", "B8_03", "B8_03M", "B3_02"}


def pre(variant, shot, mod):
    if shot == "B3_02" and shot in SHOTS:
        try:
            import cut_hero_r24_b302 as H
        except ImportError:
            return
        if hasattr(H, "pre"):
            H.pre(mod)


def post(sc, variant, shot):
    if shot not in SHOTS:
        return
    try:
        if shot == "B7_06":
            import cut_hero_r24_b706 as H
            H.post(sc)
        elif shot in ("B8_03", "B8_03M"):
            import cut_hero_r24_b803 as H
            H.post(sc, shot)
        elif shot == "B3_02":
            import cut_hero_r24_b302 as H
            H.post(sc)
    except ImportError as e:
        print("[cut_hero_r24] missing helper", shot, e)
