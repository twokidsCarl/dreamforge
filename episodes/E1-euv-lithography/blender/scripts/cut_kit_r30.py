"""Round 30 hook (kit sub-agent; r2_cutaway.R30_KIT = {"B8_03", "B8_03M"}). Layered AFTER the R22..R29 hooks (cut_kit_r29
GRID_R29 188 half-fields stays; its SCALE_R29 stays False) and BEFORE beam_hook_r29. Remove a shot from R30_KIT -> exact
R29 pixels.

  RULER_R30  row 6 (B8_03): R29 p2 「晶圆台在三帧之间几乎看不出位移…给晶圆台也加一条带数字的青色小标尺…或者在晶圆边缘加一个
             移动的对准标记…读数框放在画面左中，要挪到右上」. (a) the R29 cyan 0-10 mm wafer-stage ruler (cut_kit_r29_b803.scale,
             imported, never edited: fixed plate, 0 / 5 / 10 mm + 「晶圆台」, cyan travel bar + needle on WStage) gets its OWN
             screen space: the read-out box that sat on the left-middle under the PIP moves to the top right (overlay
             mograph/r2_ov_zz30k.py, gated on R30_KIT), the ruler is lowered / enlarged (labels bigger) into that freed
             band; (b) a cyan alignment cross + ring on the wafer edge, parented to the wafer stage, moves with the wafer
             (opposite to the PIP reticle pointer) so 「反向」 reads without numbers. B8_03M (PIP pass) untouched.
"""
import math
import os

RULER_R30 = True
# sub-part of row 6 (not a separate row): the enlarged R29 3D ruler. 8-spp Q4 no (still ~100 px wide under the PIP
# edge, 「晶圆台」 title ~8 px blobs, sits in the slit-beam haze) -> False = the R28/R29 white tick bar + PtrW stay.
SCALE3D = os.environ.get("R30K_SCALE") == "1"

_E = os.environ


def _emit(name, col, st):
    import cut_kit_r29_b803 as H
    return H._emit(name, col, st)


def _cross(sc):
    """cyan alignment cross + ring lying on the wafer surface near its upper-left edge, parented to the stage."""
    import bpy
    from bpy_extras.object_utils import world_to_camera_view as w2c
    from mathutils import Vector
    w = bpy.data.objects.get("WStage_wafer")
    st = bpy.data.objects.get("WStage")
    if w is None or st is None:
        print("[r30k] wafer / stage missing", flush=True)
        return
    sc.frame_set(92)
    bb = [w.matrix_world @ Vector(c) for c in w.bound_box]
    ctr = sum(bb, Vector()) / 8
    zt = max(v.z for v in bb) + 0.0015
    rad = (max(v.x for v in bb) - min(v.x for v in bb)) / 2
    ang = math.radians(float(_E.get("R30K_ANG", "128")))
    ri = rad * float(_E.get("R30K_RF", "0.86"))
    p = Vector((ctr.x + ri * math.cos(ang), ctr.y + ri * math.sin(ang), zt))
    arm, th = float(_E.get("R30K_ARM", "0.045")), float(_E.get("R30K_TH", "0.0045"))
    verts, faces = [], []

    def quad(cs):
        o = len(verts)
        verts.extend(cs)
        faces.append((o, o + 1, o + 2, o + 3))
    quad([(-arm, -th, 0), (arm, -th, 0), (arm, th, 0), (-arm, th, 0)])
    quad([(-th, -arm, 0), (th, -arm, 0), (th, arm, 0), (-th, arm, 0)])
    n, r0, r1 = 48, arm * 0.62, arm * 0.62 + th * 1.3
    for i in range(n):
        a0, a1 = 2 * math.pi * i / n, 2 * math.pi * (i + 1) / n
        quad([(r0 * math.cos(a0), r0 * math.sin(a0), 0), (r1 * math.cos(a0), r1 * math.sin(a0), 0),
              (r1 * math.cos(a1), r1 * math.sin(a1), 0), (r0 * math.cos(a1), r0 * math.sin(a1), 0)])
    me = bpy.data.meshes.new("WAlignCrossR30")
    me.from_pydata(verts, [], faces)
    me.update()
    ob = bpy.data.objects.new("WAlignCrossR30", me)
    sc.collection.objects.link(ob)
    me.materials.append(_emit("WAlignCyanR30M", (0.1, 0.85, 0.95), float(_E.get("R30K_E", "5.0"))))
    ob.visible_shadow = False
    ob.matrix_world = __import__("mathutils").Matrix.Translation(p)
    ob.parent = st
    ob.matrix_parent_inverse = st.matrix_world.inverted()
    ob.matrix_world = __import__("mathutils").Matrix.Translation(p)
    for f in (42, 92, 143):
        sc.frame_set(f)
        q = w2c(sc, sc.camera, ob.matrix_world.translation)
        c = w2c(sc, sc.camera, w.matrix_world @ (sum((Vector(c_) for c_ in w.bound_box), Vector()) / 8))
        e = w2c(sc, sc.camera, ob.matrix_world.translation + Vector((arm, 0, 0)))
        print(f"[r30k] f{f} cross ({q.x * 960:.0f},{(1 - q.y) * 540:.0f}) arm {abs(e.x - q.x) * 960:.1f}px "
              f"wafer c ({c.x * 960:.0f},{(1 - c.y) * 540:.0f}) world x {ob.matrix_world.translation.x:.3f}", flush=True)
    sc.frame_set(92)


def pre(variant, shot, mod):
    return None


def post(sc, variant, shot):
    if shot != "B8_03" or not RULER_R30:
        return sc
    if not SCALE3D:
        _cross(sc)
        return sc
    import cut_kit_r29_b803 as H
    # own screen space: the read-out box left the left-middle band (zz30k) -> ruler a little lower / larger there
    old = (H.BAR_C, H.LAB_H, H.PL_H)
    H.BAR_C = (float(_E.get("R30K_BY", str(H.BAR_C[0]))), float(_E.get("R30K_BZ", "0.68")))
    H.LAB_H = float(_E.get("R30K_LAB", "0.052"))
    H.PL_H = H.LAB_H * 2.1
    try:
        H.scale(sc)
        import bpy
        t = bpy.data.objects.get("WScaleTitleR29")       # 「晶圆台」 to the far (10 mm) end, out of the slit-beam haze
        if t is not None:
            t.data.align_x = "RIGHT"
            t.location.x = -0.02 * 10.0 - 0.035
        pl = bpy.data.objects.get("WScalePlateR29")
        if pl is not None:                               # widen the dark carrier plate under the moved title
            for v in pl.data.vertices:
                if v.co.x < -0.1:
                    v.co.x -= float(_E.get("R30K_PLX", "0.13"))
    finally:
        H.BAR_C, H.LAB_H, H.PL_H = old
    _cross(sc)
    return sc
