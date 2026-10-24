"""Round 25 hook (owned by the 'chero' sub-agent; shots in r2_cutaway.R25_HERO). Runs after the R22 / R23 / R24 hooks.
Per shot (remove a shot from r2_cutaway.R25_HERO or from SHOTS -> exact R24 pixels):
  B3_02  row 5 (+2): R24 enlarged dish + R24 sketch camera (cut_hero_r24_b302, called from here because B3_02 is not
         in R24_HERO), its cone built by beam_r25 (tapered shell); cone / laser / IF pinch visible_glossy = False
         (the dish mirrors only the chamber + plasma violet); CO2 laser enters through a back port + the centre hole and
         fades out in front of the dish (cut_hero_r25_b302)
  B7_06  rows 1 + 2 + 4: the R24 chain is built by beam_r25 (tapered shell legs) with the R24 solid ring mirrors
         passed as existing mirrors; depth-layer machine parts in the tower (cut_hero_r25_b706)
  B8_03 / B8_03M row 2: the R24 slit cone is a beam_r25 tapered shell cone (narrow at the slit, opening upward)
         (cut_hero_r25_b803)
"""
SHOTS = {"B3_02", "B7_06", "B8_03", "B8_03M"}
_SAVED = {}


def _patch(chain_fn, check_fn):
    import beam_r24 as B24
    if not _SAVED:
        _SAVED.update(chain=B24.chain, check=B24.check, soft_cone=B24.soft_cone)
    B24.chain = chain_fn
    B24.check = check_fn


def _restore():
    import beam_r24 as B24
    for k, v in _SAVED.items():
        setattr(B24, k, v)
    _SAVED.clear()


def pre(variant, shot, mod):
    if shot not in SHOTS:
        return
    if shot == "B7_06":
        import cut_hero_r25_b706 as H
        _patch(H.chain24, H.check24)
        H.pre(mod)
    elif shot in ("B8_03", "B8_03M"):
        import cut_hero_r25_b803 as H
        _patch(H.chain24, H.check24)


def post(sc, variant, shot):
    if shot not in SHOTS:
        return sc
    try:
        if shot == "B3_02":
            import beam_r25 as BR
            import cut_hero_r24_b302 as H24
            import cut_hero_r25_b302 as H
            # shell cone: wide end (over the dish mouth) dimmer, narrow end (IF) brighter -> the face is not washed violet
            _patch(lambda *a, **k: BR.chain(*a, **{**k, "strength": 1.1, "gain": 3.5}),
                   lambda *a, **k: [])   # beam_r25.check calls beam_r24.check: run it after _restore()
            try:
                H24.post(sc)
            finally:
                _restore()
            H.post(sc)
            H.check(sc)
        elif shot == "B7_06":
            _restore()
            import cut_hero_r25_b706 as H
            H.post(sc)
        elif shot in ("B8_03", "B8_03M"):
            _restore()
            import cut_hero_r25_b803 as H
            H.post(sc, shot)
    finally:
        _restore()
    return sc
