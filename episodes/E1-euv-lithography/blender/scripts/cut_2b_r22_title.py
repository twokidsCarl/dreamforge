"""R22 row 4 (A0_10 depth / camera): R21 review 「机位从正立面改成 15–20° 的斜侧前方，加前景虚焦的框架柱和背景的辅助机柜，
做出 3 层景深」. Camera swung ~18 deg to the front-left (same target, same slow push), DOF on the machine, a
defocused foreground frame post at the left edge and an auxiliary cabinet row behind the machine (3 depth layers)."""
import math
import bpy
from mathutils import Vector


def post(sc):
    import kit_r2 as K
    cam = bpy.data.objects.get("CamR2")
    tgt = bpy.data.objects.get("CamR2_target") or (cam.constraints[0].target if cam and cam.constraints else None)
    n = sc.frame_end
    if cam is None:
        return
    cam.animation_data_clear()
    if tgt is not None:
        tgt.animation_data_clear()
    a = math.radians(18)
    keys = [(1, (-3.6, 0, 3.3), 15.7), (n, (-2.3, 0, 3.4), 14.2)]
    for f, t_, d in keys:
        t_ = Vector(t_)
        cam.location = t_ + Vector((-math.sin(a) * d, -math.cos(a) * d, 2.35 - t_.z))
        cam.keyframe_insert("location", frame=f)
        if tgt is not None:
            tgt.location = t_
            tgt.keyframe_insert("location", frame=f)
    try:
        for o in (cam, tgt):
            if o is not None and o.animation_data and o.animation_data.action:
                for fc in o.animation_data.action.fcurves:
                    for kp in fc.keyframe_points:
                        kp.interpolation = "LINEAR"
    except AttributeError:                    # Blender 5 layered actions: K.key_path's own helper
        pass
    cam.data.dof.use_dof = True
    cam.data.dof.focus_distance = 15.0
    cam.data.dof.aperture_fstop = 1.8
    # foreground: a cut frame post (white paint, dark section) at the left edge, ~4 m from the lens
    paint = bpy.data.materials.get("PaintR11") or K.mat("PostPaintR22", (0.8, 0.81, 0.83), rough=0.35)
    mb = K.MB()
    p = Vector((-8.55, -10.6, 0))
    mb.box(p + Vector((0, 0, 3.0)), (0.32, 0.32, 6.0))
    mb.box(p + Vector((0.25, 0, 0.6)), (0.2, 0.36, 0.12))
    mb.box(p + Vector((0.25, 0, 2.1)), (0.2, 0.36, 0.12))
    mb.obj("FgPostR22", paint)
    # background: auxiliary cabinet row behind the machine (doors, vents, cable trays), slightly darker
    cab = K.mat("AuxCabR22", (0.36, 0.37, 0.4), rough=0.4)
    vent = K.mat("AuxVentR22", (0.08, 0.085, 0.095), rough=0.6)
    mc, mv = K.MB(), K.MB()
    for i, (x, w, h) in enumerate(((-12.5, 1.6, 3.2), (-10.7, 1.2, 2.6), (-9.2, 1.5, 3.4), (6.4, 1.4, 3.0), (8.0, 1.7, 3.6),
                                   (9.9, 1.2, 2.4))):
        y = 4.2
        mc.box((x, y, h / 2), (w, 1.0, h))
        for k in range(3):
            mv.box((x - w * 0.25 + (k % 2) * w * 0.5, y - 0.51, h * (0.25 + 0.22 * k)), (w * 0.36, 0.02, 0.12 + 0.08 * (i % 2)))
    mc.obj("AuxCabR22", cab)
    mv.obj("AuxCabVentR22", vent)
