"""Round 26 hook (owned by the 'chero' sub-agent; shots in r2_cutaway.R26_HERO = B8_03 / B8_03M / B3_02). Layered AFTER the
R22 / R23 / R24 / R25 hooks: pre(variant, shot, mod) at the start of build(), post(sc, variant, shot) at the end.
Per shot (remove a shot from r2_cutaway.R26_HERO -> exact R25 pixels):
  B8_03 / B8_03M  R26_ROOT_CAUSE row 2: the R24 slit cone (cut_hero_r24_b803 -> beam_r24.chain) is built as a beam_r26
                  soft shell (rim roll-off, filled core) while the R24 hook runs (cut_hero_r26_b803.chain24);
                  row 4 (B8_03 only): polished silicon wafer (metallic mirror, thin-film tint, scribe-lane grid) with a
                  broad soft-gradient glossy environment instead of the black card (no narrow strip -> no band).
  B3_02           row 5: camera push (dish >= 1/3 frame width, rim area +>=15 % f30 -> f103), row 2: the rim -> IF cone is
                  a beam_r26 soft shell starting 0.15 m in front of the rim plane (cut_hero_r26_b302).
"""
SHOTS = {"B3_02", "B8_03", "B8_03M"}
_SAVED = {}


def _patch(chain_fn, check_fn):
    import beam_r24 as B24
    if not _SAVED:
        _SAVED.update(chain=B24.chain, check=B24.check)
    B24.chain = chain_fn
    B24.check = check_fn


def _restore():
    import beam_r24 as B24
    for k, v in _SAVED.items():
        setattr(B24, k, v)
    _SAVED.clear()


def pre(variant, shot, mod):
    if shot in ("B8_03", "B8_03M"):
        import cut_hero_r26_b803 as H
        _patch(H.chain24, H.check24)


def post(sc, variant, shot):
    if shot not in SHOTS:
        return sc
    _restore()
    if shot in ("B8_03", "B8_03M"):
        import cut_hero_r26_b803 as H
        H.post(sc, shot)
    elif shot == "B3_02":
        import cut_hero_r26_b302 as H
        H.post(sc)
    return sc
