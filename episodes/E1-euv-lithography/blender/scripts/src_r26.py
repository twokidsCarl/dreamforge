"""Round 26 hook (owned by the 'srcb' sub-agent; shots in r2_source.R26_SRC = B2_08 / B1_15). Remove a shot from
R26_SRC -> exact R25 pixels. Layered AFTER the R25 hooks: pre(variant, shot, mod) at the start of build(),
post(sc, variant, shot) at the end.

R26_ROOT_CAUSE row 2 (shared soft shell beam_r26: B7_06 softened values + rim roll-off, no hard outline):
  * B1_15: src_r25 (R25_SRC) built the IF cone B115ExitR25 with beam_r25 (edge 2.4 / core 0.06 = hard bright
    silhouette). It is deleted and rebuilt with beam_r26.chain - SAME stops (start 0.62 rim->IF, in-frame IF, straight
    off-frame exit), same fade-in start, visible_glossy off (cone never in the mirror face). The R24 push + focus pull,
    the IF anchor and the zz25s 「中间焦点 IF」 label are untouched (the IF does not move).
  * B2_08 (not in R25_SRC, base = R23 pixels): the R23 SnH4RibbonsR23 tubes are replaced by gas streams built with
    beam_r26 soft shells (src_r26_b208.py).
"""
import os

_E = os.environ
_MOD = [None]


def pre(variant, shot, mod):
    _MOD[0] = mod


def post(sc, variant, shot):
    if shot == "B1_15" and variant == "contrast":
        _b115(sc)
    elif shot == "B2_08" and variant == "clean":
        import src_r26_b208 as G
        G.build(sc, _MOD[0])
    return sc


def _b115(sc):
    import bpy
    import kit_r2 as K
    import b115_r21 as B
    import b115_r22_build as BB
    import beam_r26 as BM
    import src_r25 as R25
    for ob in list(bpy.data.objects):
        if ob.name.startswith("B115ExitR25"):
            bpy.data.objects.remove(ob, do_unlink=True)
    # identical geometry to src_r25._b115 (the IF stays where the R25 label / anchor point at it)
    xr, xi0 = B.fx(B.R), BB.image_x()
    xi = xr + float(_E.get("S25_IFF", "0.62")) * (xi0 - xr)
    k = float(_E.get("S26_K", _E.get("S25_K", "0.62")))
    xa = xr + k * (xi - xr)
    ra = B.R * (xi - xa) / (xi - xr)
    ri = float(_E.get("S25_RI", "0.012"))
    xe = xi + (xi - xa) * float(_E.get("S25_EL", "1.2"))
    re = ra * (xe - xi) / (xi - xa)
    widen = float(_E.get("S26_W", "1.0"))
    ch = BM.chain("B115ExitR26", [((xa, 0, 0), None), ((xi, 0, 0), None), ((xe, 0, 0), None)],
                  [ra, ri, re], color=K.VIOLET, strength=float(_E.get("S26_CS", "5.0")),
                  widen=widen, land_final=False, mirrors=False)
    for leg in ch["legs"]:
        for ob in leg:
            ob.visible_glossy = False      # mirror-hero: the cone never shows in the face
    R25.fade_start(ch["legs"][0][0], float(_E.get("S26_FADE", "0.12")))
    from bpy_extras.object_utils import world_to_camera_view as w2c
    import math
    from mathutils import Vector
    for f in (9, 20, 31):
        sc.frame_set(f)
        ys = [round((1 - w2c(sc, sc.camera, Vector(p)).y) * 540) for p in
              ((xa, 0, 0), (xa, 0, ra * widen), (xa, 0, -ra * widen), (xi, 0, 0))]
        rim = [round((1 - w2c(sc, sc.camera, Vector((xr, B.R * math.cos(t), B.R * math.sin(t)))).y) * 540)
               for t in [i * math.pi / 36 for i in range(72)]]
        print(f"B115PROJ26 f{f} start/top/bot/IF y@540 {ys} rim y {min(rim)}..{max(rim)}", flush=True)
    BM.check(sc, ch, (9, 20, 31), exits=(2,), tag="B1_15")
    sc.frame_set(1)
