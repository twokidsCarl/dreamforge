"""R21 B8_17 (R21_ROOT_CAUSE row #5, R20 review B8_17 #1 "机理画反了…真实扫描仪光带固定、是晶圆台在动。改成光带固定在镜筒正下方，
让晶圆台带着晶圆平移，用逐格点亮表示进度"): mechanism reversed back to the real scanner.

Runs AFTER misc_b817_r20.apply (188 half-fields 26 x 16.5 mm, grey -> violet, soft cone, counters all kept):
- the slit (and the soft cone hooked to it) is pinned directly under the projection-lens exit port (PX, PY) - it never moves;
- the wafer stage (chuck block + wafer + 188 field rectangles + notch) is parented to one empty that is keyed so the field
  being exposed at each instant sits exactly under the fixed slit: offset(t) = slit - field_centre(order[k]); same timing
  as R20 (field k at frame 1 + k/188 * 0.9 n) so the field material's progress / counters stay in sync.
NOT repeating: moving slit band (R20).  Called from r2_misc._wafer only when B8_17 is in R21_SHOTS.
"""
import bpy
from mathutils import Vector

import common as C

STAGE_NAMES = ("Chuck", "Wafer", "FieldsR20", "WaferNotch", "Fields", "FieldGlow")


CASSETTE_DX = 0.8     # cassette + finished-wafer stack nudged right (stage block must never pass through it)


def _cone(sc, n, so, port):
    """R20 soft cone (same params as misc_b817_r20) rebuilt from the moved exit port down to the FIXED slit."""
    import misc_beam_r18 as BR18
    import kit_r2 as K
    for ob in list(sc.objects):
        if ob.name.startswith("SlitConeR20"):
            bpy.data.objects.remove(ob, do_unlink=True)
    PX, PY, PZ = port
    obs, _emp = BR18.hooked_cone("SlitConeR21", (PX, PY, PZ + 0.02), (0.52, 0.2), (0.13, 0.006), so, K.VIOLET,
                                 1.0, 0.3, edge=3.0, inner=0.4, inner_gain=1.8, gain=2.5)
    for ob, st, al in zip(obs, (1.3, 2.0), (0.2, 0.26)):
        ob.data.materials[0] = BR18.cone_mat(ob.name + "M21", K.VIOLET, st, al, 3.0, 0.3, 0.0, 2.5)
        ob.hide_render = False
        ob.keyframe_insert("hide_render", frame=round(n * 0.9) + 2)
        ob.hide_render = True
        ob.keyframe_insert("hide_render", frame=round(n * 0.9) + 3)


def apply(sc, n, R, so, order, port, cam=None):
    for ob in list(sc.objects):
        if ob.name == "Cassette" or ob.name.startswith("Stack"):
            ob.location.x += CASSETTE_DX
    SX, SY = port[0], port[1]
    # 1) slit fixed under the barrel
    if so.animation_data and so.animation_data.action:
        for fc in list(C.fcurves(so.animation_data.action)):
            if fc.data_path == "location":
                for kp in list(fc.keyframe_points)[::-1]:
                    fc.keyframe_points.remove(kp)
    so.location = (SX, SY, 0.0105)
    _cone(sc, n, so, port)
    # 2) stage carrier: everything that sits on / is the wafer stage
    rig = bpy.data.objects.new("WaferStageR21", None)
    sc.collection.objects.link(rig)
    moved = []
    for ob in list(sc.objects):
        if ob is rig or ob.parent is not None or ob.type != "MESH" or ob is so:
            continue
        nm = ob.name
        hit = any(nm == s or nm.startswith(s + ".") for s in STAGE_NAMES)
        if not hit:
            # anything else lying on the wafer disc (field meshes from older rounds, notch, rings)
            bb = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
            xs, ys, zs = [p.x for p in bb], [p.y for p in bb], [p.z for p in bb]
            hit = (max(zs) < 0.05 and min(zs) > -0.5 and max(map(abs, xs)) < R * 1.25 and max(map(abs, ys)) < R * 1.25
                   and (max(xs) - min(xs)) > 0.0)
        if hit:
            mw = ob.matrix_world.copy()
            ob.parent = rig
            ob.matrix_world = mw
            moved.append(nm)
    print(f"[R21 B8_17] stage objects moved with the wafer: {moved}")
    for k, (_, _, cx, cy) in enumerate(order):
        rig.location = (SX - cx, SY - cy, 0.0)
        rig.keyframe_insert("location", frame=1 + (k / len(order)) * n * 0.9)
    rig.keyframe_insert("location", frame=round(n * 0.9) + 2)
    for fc in C.fcurves(rig.animation_data.action):
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR"
    # camera: same R20 move, framed 1.0 m further left (centred on the fixed barrel) and lens 32 -> 28 mm so the
    # travelling wafer stays in frame at both ends of its stroke
    for ob in (cam or ()):
        ad = ob.animation_data
        if ad and ad.action:
            for fc in C.fcurves(ad.action):
                if fc.data_path == "location" and fc.array_index == 0:
                    for kp in fc.keyframe_points:
                        kp.co.y -= 1.0
                        kp.handle_left.y -= 1.0
                        kp.handle_right.y -= 1.0
        else:
            ob.location.x -= 1.0
    if cam and cam[0].type == "CAMERA":
        cam[0].data.lens = 28
    return rig
