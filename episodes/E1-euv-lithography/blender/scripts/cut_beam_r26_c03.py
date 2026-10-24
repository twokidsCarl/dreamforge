"""R26 cbeam helper for C_03 (row 2 soft shell + the R25 BEAMCHECK25 NOGO at f222: FFM / G1 / G2 edge-on).
R26 sketch: two consecutive turn mirrors cannot both face a side-on camera; G1 -> G2 is such a pair (pure reflections,
f222 n.to_cam -0.12 / +0.38). Path with FEWER open turns: collector -> IF -> FFM -> PFM -> MASK -> projection (G1 / G2
grazing condensers carry no beam). PFM 0.25 m shallower (y 0.25 -> 0.0, offline dump: FFM 0.53 / PFM 0.54 at f222 with
the builder's own facet turn-to-cut-side); the PFM model is built on the PFM -> MASK bisector (kit_r2.mirror_normal call
answered for that one call). cut_beam_r24's C_03 post is skipped (its 8-stop chain / sub-chain indices); this module
builds the 6-stop chain with beam_r26 (through cut_beam_r26_swap._chain: existing scene mirrors, no new mirrors) and runs
beam_r26.check at the three job frames."""
import bpy
from mathutils import Vector

PFM_Y = 0.0
SRC_AT = 0.45
SRC_GAIN = 4.0      # collector cone (leg 0): beam_r26 shell gain toward the IF end -> the wide dish-side mouth is 1/5 as bright
HIDE = ("MaskBandR19", "MaskBandGlowR19")   # R25 p2 #1 「掩模入射点附近还有一段白色弯曲高光…删除这段白色弯线」
_ORIG = {}


def pre():
    import build_cutaway_r2 as B
    import cut_beam_r24 as R24
    import kit_r2 as K
    R24.SHOTS.discard("C_03")
    B.PFM = Vector((B.PFM.x, PFM_Y, B.PFM.z))
    if "mn" not in _ORIG:
        _ORIG["mn"] = K.mirror_normal

    def _mn(a, p, b, *x, **k):
        if (Vector(p) - B.PFM).length < 1e-4 and (Vector(b) - B.G1).length < 1e-4:
            b = B.MASK
        return _ORIG["mn"](a, p, b, *x, **k)
    K.mirror_normal = _mn
    if hasattr(B, "K"):
        B.K.mirror_normal = _mn
    print("[r26c] C_03 PFM ->", tuple(round(x, 3) for x in B.PFM), "(G1/G2 carry no beam)", flush=True)


def post(sc):
    import build_cutaway_r2 as B
    import cut_beam_r24 as R24
    import beam_r24 as BM
    import kit_r2 as K
    import cut_beam_r26_swap as S
    if "mn" in _ORIG:
        K.mirror_normal = _ORIG["mn"]
        if hasattr(B, "K"):
            B.K.mirror_normal = _ORIG["mn"]
    R24.SHOTS.add("C_03")
    R24._cleanup("C_03")
    coll_dir = (B.IF - B.COLL).normalized()
    src = B.COLL + coll_dir * SRC_AT        # mouth on the collector dish (rim hidden by the dish / frame edge)
    po = B.PO[0]
    pts = [src, B.IF, B.FFM, B.PFM, B.MASK, po]
    stops = R24._stops(pts, mirrors=(2, 3, 4), final_n=None)
    radii = [0.55 / 1.35, 0.03, 0.2, 0.16, 0.06, 0.09]
    ch = S._chain("TourPathR26", stops, radii, spot_strength=12.0)
    import beam_r26 as B26
    (a, _), (b, _) = ch["stops"][0], ch["stops"][1]
    ra, rb = ch["leg_radii"][0]
    for ob in ch["legs"][0]:
        bpy.data.objects.remove(ob, do_unlink=True)
    ch["legs"][0] = B26.soft_cone("TourPathR26Leg0", a, b, ra, rb, None, S.STRENGTH["C_03"], gain=SRC_GAIN, taper=1.0)
    ch["leg_radii"][0] = tuple(ch["legs"][0][0]["r25_radii"])
    for nm in HIDE:
        ob = bpy.data.objects.get(nm)
        if ob is not None:
            ob.animation_data_clear()          # R19 keyed visibility would re-show it on frame_set
            ob.hide_render = True
            ob.hide_viewport = True
    print(f"[r26c] C_03 leg0 gain {SRC_GAIN}, hidden {HIDE}", flush=True)
    BM.key_chain(ch, [1, 1, 150, 170, 260])
    f0, f1, f2 = R24.JOB["C_03"]
    bad = S._check(sc, R24._sub(ch, 0, 2), [f0], exits=(0,), tag="C_03 stops0-2")
    bad += S._check(sc, R24._sub(ch, 1, 4), [f1], tag="C_03 stops1-4")
    bad += S._check(sc, R24._clip_in_frame(sc, ch, f2, 3, 5), [f2], tag="C_03 stops3-5(clipped to frame)")
    print(f"BEAMCHECK C_03 SUMMARY {'OK' if not bad else 'NOGO ' + str(len(bad))}", flush=True)
