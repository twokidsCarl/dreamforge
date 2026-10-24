"""R26 cbeam helper for C_03 / B5_01 (R26_ROOT_CAUSE row 2: shared beam_r26 soft shell).
Same pattern as cut_beam_r25_swap.py (R25), pointed at beam_r26: pre() swaps beam_r24.chain / soft_cone / check for
beam_r26 wrappers so cut_beam_r24 builds the R26 soft-shell legs (edge 1.3 / core 0.28 / alpha 0.45 / rim roll-off,
mouths x1.35 via widen); every turn stop is given the existing scene mirror at that point via existing={i: obj} and no
new mirrors are built (mirrors=False). check() = beam_r26.check (beam_r24.check + BEAMCHECK25 + BEAMCHECK26) on the R24
sub-chains. restore() undoes the swap (called from post())."""
import bpy
from mathutils import Vector

STRENGTH = {"B5_01": 3.0, "C_03": 4.5}
ALPHA = {"B5_01": 0.38}      # main-process note: high strength on dark bays tone-maps into a flat plateau
_ORIG = {}
_FULL = []
_SHOT = [None]


def _strength():
    return STRENGTH.get(_SHOT[0], 4.5)


def _chain(name, stops, radii, **kw):
    import beam_r26 as B26
    import cut_beam_r25_a010 as A
    import build_cutaway_r2 as B
    for k in ("inner", "inner_gain", "fade0", "fade1", "strength", "alpha", "core"):
        kw.pop(k, None)
    stops = list(stops)
    for i in range(1, len(stops) - 1):
        # builder turns the facet mirrors toward the cut side: landing / BEAMCHECK25 use the face the viewer sees
        p, nr = Vector(stops[i][0]), stops[i][1]
        if nr is None:
            continue
        if (p - B.FFM).length < 1e-4:
            stops[i] = (p, (Vector(nr) + Vector((0, -0.75, 0))).normalized())
        elif (p - B.PFM).length < 1e-4:
            stops[i] = (p, (Vector(nr) + Vector((0, -0.5, 0))).normalized())
    existing = {}
    for i in range(1, len(stops) - 1):
        if stops[i][1] is not None:
            ob = A._obj_at(Vector(stops[i][0]), skip=(name,))
            if ob is not None:
                existing[i] = ob
    if name == "IllumPathR24":             # B5_01: IF end 0.03 -> 0.067 (3:1 to the FFM landing), as R25
        radii = [0.067] + list(radii[1:])
    ch = B26.chain(name, stops, radii, strength=_strength(), alpha=ALPHA.get(_SHOT[0], 0.45), existing=existing, mirrors=False, **kw)
    ch["_name"] = name
    _FULL.append(ch)
    print(f"[r26c] {_SHOT[0]} {name} existing mirrors {{{', '.join(f'{i}: {o.name}' for i, o in existing.items())}}} "
          f"leg radii {[tuple(round(x, 3) for x in r) for r in ch['leg_radii']]}", flush=True)
    return ch


def _soft_cone(name, a, b, ra, rb, color=None, strength=4.0, alpha=0.6, *args, **kw):
    import beam_r26 as B26
    import beam_r25 as B25
    w = B26.WIDEN
    ra2 = B25._scale(ra, w) if B25._rmax(ra) >= B25._rmax(rb) else ra
    rb2 = B25._scale(rb, w) if B25._rmax(rb) > B25._rmax(ra) else rb
    obs = B26.soft_cone(name, a, b, ra2, rb2, color, _strength(), alpha=ALPHA.get(_SHOT[0], 0.45))
    for ch in _FULL:                      # keep the full chain's leg radii in sync (R24 _fade_src rebuilds leg 0)
        if name == ch.get("_name", "") + "Leg0":
            ch["leg_radii"][0] = tuple(obs[0]["r25_radii"])
    return obs


def _check(sc, ch, frames, exits=(), tag="", cam=None):
    import beam_r24 as B24
    import beam_r26 as B26
    sub = dict(ch)
    for full in _FULL:
        if ch["legs"] and ch["legs"][0] in full["legs"]:
            i0 = full["legs"].index(ch["legs"][0])
            n = len(ch["legs"])
            sub["leg_radii"] = full["leg_radii"][i0:i0 + n]
            sub["mirrors"] = {j - i0: full["mirrors"][j] for j in full["mirrors"] if i0 <= j <= i0 + n}
            break
    B24.check = _ORIG["check"]
    try:
        return B26.check(sc, sub, frames, exits=exits, tag=tag, cam=cam)
    finally:
        B24.check = _check


def swap(shot):
    import beam_r24 as B24
    if not _ORIG:
        _ORIG.update(chain=B24.chain, soft_cone=B24.soft_cone, check=B24.check)
    B24.chain, B24.soft_cone, B24.check = _chain, _soft_cone, _check
    _FULL.clear()
    _SHOT[0] = shot


def restore():
    import beam_r24 as B24
    if _ORIG:
        B24.chain, B24.soft_cone, B24.check = _ORIG["chain"], _ORIG["soft_cone"], _ORIG["check"]
