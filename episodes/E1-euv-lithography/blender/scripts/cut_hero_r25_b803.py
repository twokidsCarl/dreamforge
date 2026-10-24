"""R25 chero B8_03 / B8_03M (R25_ROOT_CAUSE row 2). The R24 helper (cut_hero_r24_b803) builds the slit cone through
beam_r24.chain; while the R24 hook runs, beam_r24.chain is patched (cut_hero_r25.pre) to chain24() below, which builds
the SAME leg as a beam_r25 tapered SHELL cone (narrow at the slit, opening upward, ends >= 3:1, xdir kept so the slit
ellipse stays aligned; the slit end keeps the slit size, the top widens) - no inner cone (R24 inner x1.15 = solid slab). Slit colour, no band, PIP and readouts untouched.
"""
from mathutils import Vector

CH = {}


def chain24(name, stops, radii, color=None, strength=4.0, alpha=0.6, spot_strength=12.0, land_final=True, xdir=None,
            **_kw):
    import beam_r25 as BR
    a, b = Vector(stops[0][0]), Vector(stops[1][0])
    ra, rb = radii[0], radii[1]
    # keep the slit footprint (narrow end = the slit, 8-spp try 1: shrinking it left a thin line inside a wider slit);
    # widen the TOP (reticle side) instead so the ends are >= 3:1
    s_ = 3.05 * BR._rmax(rb) / BR._rmax(ra)
    if s_ > 1.0:
        ra = BR._scale(ra, s_)
    ra, rb = BR.tapered(ra, rb)
    legs = BR.soft_cone(f"{name}Leg0", a, b, ra, rb, color, strength * 1.15, min(alpha * 1.3, 0.85), xdir=xdir)
    ch = {"legs": [legs], "spots": [None, None], "stops": [(a, stops[0][1]), (b, stops[1][1])], "radii": [ra, rb],
          "leg_radii": [(BR._rmax(ra), BR._rmax(rb))], "mirrors": {}}
    CH["ch"] = ch
    return ch


def check24(*_a, **_k):
    return []


def post(sc, shot):
    import beam_r25 as BR
    ch = CH.get("ch")
    if ch is None or shot == "B8_03M":
        return
    f0 = sc.frame_current
    rx = (sc.render.resolution_x, sc.render.resolution_y)
    sc.render.resolution_x, sc.render.resolution_y = 960, 540
    BR.check(sc, ch, (42, 92, 143), tag="B8_03")
    sc.render.resolution_x, sc.render.resolution_y = rx
    sc.frame_set(f0)
