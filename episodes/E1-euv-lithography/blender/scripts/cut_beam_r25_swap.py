"""R25 cbeam helper for C_03 / B5_01 (row 2 taper + row 1 existing turn mirrors).
pre(): swap beam_r24.chain / soft_cone / check for beam_r25 wrappers so cut_beam_r24 builds tapered SHELL legs; every
turn stop is given the existing scene mirror at that point (smallest mesh whose bbox holds the stop) via existing={i: obj}
and no new mirrors are built (mirrors=False). check() runs beam_r24.check + BEAMCHECK25 on the R24 sub-chains (mirrors and
tapered leg radii re-indexed from the full chain). restore() undoes the swap (called from post())."""
import bpy
from mathutils import Vector

STRENGTH, ALPHA, CORE = 9.0, 0.9, 0.18
_ORIG = {}
_FULL = []


def _chain(name, stops, radii, **kw):
    import beam_r25 as B25
    import cut_beam_r25_a010 as A
    for k in ("inner", "inner_gain", "fade0", "fade1", "strength", "alpha", "core"):
        kw.pop(k, None)
    import build_cutaway_r2 as B
    stops = list(stops)
    for i in range(1, len(stops) - 1):
        # the builder turns the facet mirrors toward the cut side (FFM +(0,-0.75,0), PFM +(0,-0.5,0) on the bisector):
        # the landing / BEAMCHECK25 use that ACTUAL face normal, i.e. the face the viewer sees
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
    if name == "IllumPathR24":             # B5_01: IF end 0.03 -> 0.067 (3:1 to the FFM landing) so the cone visibly leaves the IF
        radii = [0.067] + list(radii[1:])
    ch = B25.chain(name, stops, radii, strength=STRENGTH, alpha=ALPHA, core=CORE, existing=existing, mirrors=False, **kw)
    ch["_name"] = name
    _FULL.append(ch)
    print(f"[r25c] {name} existing mirrors {{{', '.join(f'{i}: {o.name}' for i, o in existing.items())}}} "
          f"leg radii {[tuple(round(x, 3) for x in r) for r in ch['leg_radii']]}", flush=True)
    return ch


def _soft_cone(name, a, b, ra, rb, color=None, strength=4.0, alpha=0.6, *args, **kw):
    import beam_r25 as B25
    obs = B25.soft_cone(name, a, b, ra, rb, color, STRENGTH, ALPHA, core=CORE)
    for ch in _FULL:                      # keep the full chain's leg radii in sync (R24 _fade_src rebuilds leg 0)
        if name == ch.get("_name", "") + "Leg0":
            ch["leg_radii"][0] = tuple(obs[0]["r25_radii"])
    return obs


def _check(sc, ch, frames, exits=(), tag="", cam=None):
    import beam_r24 as B24
    import beam_r25 as B25
    sub = dict(ch)
    for full in _FULL:
        if ch["legs"] and ch["legs"][0] in full["legs"]:
            i0 = full["legs"].index(ch["legs"][0])
            n = len(ch["legs"])
            sub["leg_radii"] = full["leg_radii"][i0:i0 + n]
            sub["mirrors"] = {j - i0: full["mirrors"][j] for j in full["mirrors"] if i0 <= j - 0 <= i0 + n}
            break
    B24.check = _ORIG["check"]
    try:
        return B25.check(sc, sub, frames, exits=exits, tag=tag, cam=cam)
    finally:
        B24.check = _check


def swap():
    import beam_r24 as B24
    if not _ORIG:
        _ORIG.update(chain=B24.chain, soft_cone=B24.soft_cone, check=B24.check)
    B24.chain, B24.soft_cone, B24.check = _chain, _soft_cone, _check
    _FULL.clear()


def restore():
    import beam_r24 as B24
    if _ORIG:
        B24.chain, B24.soft_cone, B24.check = _ORIG["chain"], _ORIG["soft_cone"], _ORIG["check"]
