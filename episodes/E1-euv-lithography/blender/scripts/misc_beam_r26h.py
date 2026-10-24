"""Round 26 hook (owned by the 'mbeam' sub-agent; shots in r2_misc.R26_BEAM = B4_07 / A2_03 / B8_17).
Layered AFTER the R25 hooks: pre(variant, shot, mod) at the start of build(), post(sc, variant, shot) at the end.

R26_ROOT_CAUSE row 2 (shared soft shell beam_r26): pre() points beam_r24.chain / soft_cone / check at beam_r26 wrappers
so the R24 hook (misc_beam_r24h) builds R26 soft-shell legs (edge 1.3 / core 0.28 / alpha 0.45 / rim roll-off, mouths
x1.35) and runs BEAMCHECK + 25 + 26.
- A2_03 / B8_17 (in R25_BEAM): this pre() runs after misc_beam_r25h.pre and overrides its beam_r25 swap; everything else
  of R25 stays (A2_03 PO5 depth stagger + front-facing face + NA arc, density layers; B8_17 slit-oriented fan, stage
  parts, wafer swap / counter sync). misc_beam_r25h.post restores beam_r24 at the end.
- B4_07 (not in R25_BEAM = R24 build): the swap works (R24 landing / camera kept, MirrorCap turn) but the R24 camera
  sees the coating 0.36 edge-on at f79 (BEAMCHECK25 NOGO); the only fix is the rejected R25 camera rise -> switched OFF
  in SHOTS (R25 pixels). PRM entry kept for R27.
SHOTS switches each shot (removed -> R25 pixels)."""
import bpy
from mathutils import Vector

SHOTS = {"A2_03", "B8_17"}   # B4_07 off: R24 camera puts MirrorCap 0.36 edge-on at f79 (BEAMCHECK25 NOGO) -> R25 pixels
PRM = {  # per shot beam_r26 overrides (strength per scene exposure; shell defaults otherwise)
    "A2_03": dict(strength=4.0, gain=1.2, widen=1.0, alpha=0.38),  # R25 widths: PO5 landing 1/3 of the blank, NA arc on the rim
    "B8_17": dict(strength=0.9, gain=1.6, widen=1.0, alpha=0.32),  # low exposure: centre darker than rim (no flat plateau)
    "B4_07": dict(strength=4.0, gain=1.2, widen=1.0, spot_strength=16.0, spot_scale=1.9),  # R24 widths + R24 crisp spot
}
A203_R5 = 0.10
B817_MOUTH = (0.42, 0.34)  # rounder slit-fan mouth (R24/R25 (0.43, 0.16) = flat fan -> "filled wedge"); width = barrel mouth
_ORIG = {}
_STATE = {"shot": None}


def _chain(name, stops, radii, **kw):
    import beam_r26 as B26
    shot = _STATE["shot"]
    xdir = kw.pop("xdir", None)
    for k in ("inner", "inner_gain", "fade0", "fade1", "strength", "alpha", "edge", "core", "gain", "spot_strength",
              "spot_scale"):
        kw.pop(k, None)
    kw.update(PRM.get(shot, {}))
    existing = {}
    if name == "A203R24":
        existing = {1: bpy.data.objects["MirrorR19_5"]}
        radii = [A203_R5 / 3.0, A203_R5, 0.006]
    elif name == "B407R24":
        existing = {1: bpy.data.objects["MirrorCap"]}
    elif name == "B817R24":
        radii = [B817_MOUTH] + list(radii[1:])
    ch = B26.chain(name, stops, radii, existing=existing, **kw)
    if xdir is not None:               # slit-shaped (elliptic) section oriented along the slit, as R25
        import beam_r25 as B25
        for i, leg in enumerate(ch["legs"]):
            for ob in leg:
                bpy.data.objects.remove(ob, do_unlink=True)
            a, b = Vector(stops[i][0]), Vector(stops[i + 1][0])
            ra, rb = B25.tapered(B25._scale(radii[i], kw.get("widen", B26.WIDEN)), radii[i + 1])
            ch["legs"][i] = B26.soft_cone(f"{name}Leg{i}", a, b, ra, rb, kw.get("color"), kw.get("strength", 4.0),
                                          alpha=kw.get("alpha", B26.ALPHA), gain=kw.get("gain", 1.2), xdir=xdir)
    _STATE["ch_" + name] = ch
    print(f"[R26 mbeam] {shot} chain {name}: leg radii {ch['leg_radii']} mirrors {list(ch['mirrors'])} prm "
          f"{PRM.get(shot)}", flush=True)
    return ch


def _soft_cone(name, a, b, ra, rb, color=None, strength=4.0, *args, **kw):
    import beam_r26 as B26
    return B26.soft_cone(name, a, b, ra, rb, color, PRM.get(_STATE["shot"], {}).get("strength", strength))


def _chk(sc, ch, frames, exits=(), tag="", cam=None, **kw):
    import beam_r24 as B24
    import beam_r26 as B26
    B24.check = _ORIG["check"]
    try:
        return B26.check(sc, ch, frames, exits=exits, tag=tag, cam=cam)
    finally:
        B24.check = _chk


def pre(variant, shot, mod):
    if shot not in SHOTS:
        return None
    import beam_r24 as B24
    _STATE["shot"] = shot
    # _ORIG = the true R24 functions (misc_beam_r25h keeps its own copy and restores them in its post())
    import misc_beam_r25h as R25
    base = R25._ORIG if R25._ORIG else dict(chain=B24.chain, soft_cone=B24.soft_cone, check=B24.check)
    _ORIG.update(chain=base["chain"], soft_cone=base["soft_cone"], check=base["check"])
    B24.chain, B24.soft_cone, B24.check = _chain, _soft_cone, _chk
    return None


def post(sc, variant, shot):
    if shot not in SHOTS:
        return sc
    import beam_r24 as B24
    if _ORIG:
        B24.chain, B24.soft_cone, B24.check = _ORIG["chain"], _ORIG["soft_cone"], _ORIG["check"]
    return sc
