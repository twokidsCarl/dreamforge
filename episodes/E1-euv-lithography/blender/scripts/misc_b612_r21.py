"""R21 B6_12 (R21_ROOT_CAUSE row #5, R20 review B6_12 #1 / #2): cut-section magnifier + black anodised pellicle frame.

R20 review: 「剖切处加一个圆形放大框，画『掩模图形面 — 间隙（几毫米）— 13 nm 膜』三层，并标注『间距不按比例』」「给 pellicle 边框做黑色
阳极氧化金属…看不出框是框、膜是膜」.
- Magnifier = a real 3D object (camera-parented so it holds one place on screen, right of the cut, at the focus distance so
  it is sharp): a black anodised bezel ring around a dark well; inside, a cut block in the SAME scanner pose as the scene
  (pattern face down): mask substrate on top with its light Mo/Si multilayer + dark absorber lines on the underside, an
  empty gap, then the pellicle membrane (bright thin sheet, thickness exaggerated) bonded to a black frame bar that stands
  the film off the mask; a cyan rule spans the gap. It appears with the R20 gap rule (0.58 n) and stays.
- The pellicle frame material becomes black anodised aluminium (R19/R20 blue-grey read as a grey bar, not as a frame).
- Anchors for the overlay (mograph/r2_ov_zz21m.py): magnifier centre / rim + right ends of the three layers, so the
  three labels sit right of the magnifier with short horizontal leaders (no crossing leaders).
Called from r2_misc._pellicle after misc_b612_r20.apply, only when B6_12 is in R21_SHOTS.
"""
import math

import bpy
from mathutils import Matrix, Vector

import kit_r2 as K

U, V, RS = 0.60, 0.37, 0.19      # magnifier centre on screen (0-1, y down) and radius in frame-height units


def _m(name, col, emit=0.0, metal=0.0, rough=0.4, **kw):
    return K.mat(name, col, metal=metal, rough=rough, emit=col if emit > 0 else None, strength=emit, **kw)


def apply(sc, n, cam, tgt, anchors20):
    # 1) black anodised pellicle frame (frame reads as frame; membrane carries the sheen)
    fr = bpy.data.objects.get("PelFrame")
    if fr is not None:
        fr.data.materials[0] = K.mat("FrameBlackAnodR21", (0.028, 0.029, 0.034), metal=0.75, rough=0.3,
                                     brushed=0.3, speck=0.04)
    # 2) magnifier, parented to the camera at the focus distance of the last beat
    f_on = round(n * 0.58)
    sc.frame_set(n)
    d = (tgt.matrix_world.translation - cam.matrix_world.translation).length * 0.6
    sc.frame_set(1)
    cd = cam.data
    hw = d * (cd.sensor_width / 2) / cd.lens
    hh = hw * sc.render.resolution_y / sc.render.resolution_x
    r = RS * 2 * hh                                  # world radius
    rig = bpy.data.objects.new("MagnifierR21", None)
    sc.collection.objects.link(rig)
    rig.parent = cam
    rig.location = ((U - 0.5) * 2 * hw, (0.5 - V) * 2 * hh, -d)
    obs = []

    def put(mb, name, mat, bevel=0.0):
        ob = mb.obj(name, mat, bevel=bevel)
        ob.parent = rig
        obs.append(ob)
        return ob

    # bezel + dark well
    bz = K.MB()
    bz.ring((0, 0, 0.0), r * 1.07, r * 0.985, r * 0.12, seg=96)
    put(bz, "MagBezelR21", K.mat("MagBezelR21M", (0.05, 0.052, 0.058), metal=0.9, rough=0.22), bevel=r * 0.012)
    rim = K.MB()
    rim.ring((0, 0, r * 0.062), r * 1.0, r * 0.985, r * 0.004, seg=96)
    put(rim, "MagRimR21", K.emit_mat("MagRimR21M", (0.75, 0.8, 0.86), 1.4))
    wl = K.MB()
    wl.cyl((0, 0, -r * 0.35), r * 0.99, r * 0.02, seg=96)
    put(wl, "MagWellR21", _m("MagWellR21M", (0.035, 0.038, 0.045), emit=0.6, rough=0.8))
    # cut block, slightly turned so its depth reads (3D section, not a flat drawing)
    blk = bpy.data.objects.new("MagBlockR21", None)
    sc.collection.objects.link(blk)
    blk.parent = rig
    blk.location = (0, 0, -r * 0.15)
    blk.rotation_euler = (math.radians(-10), math.radians(-22), 0)
    W, D = r * 1.25, r * 0.5                          # block width / depth
    y_pf = r * 0.30                                   # pattern face (mask underside)
    y_mem = -r * 0.46                                 # membrane
    t_mem = r * 0.022                                 # exaggerated film thickness
    sub, ml, ab, gapr, fb, mem = K.MB(), K.MB(), K.MB(), K.MB(), K.MB(), K.MB()
    sub.box((0, y_pf + r * 0.06 + r * 0.17, 0), (W, r * 0.34, D))                  # mask substrate
    ml.box((0, y_pf + r * 0.03, 0), (W, r * 0.06, D))                                # Mo/Si multilayer (light)
    xs = [-0.52, -0.40, -0.31, -0.18, -0.06, 0.04, 0.13, 0.27, 0.36, 0.47]
    ws = [0.06, 0.04, 0.08, 0.04, 0.06, 0.03, 0.08, 0.04, 0.06, 0.05]
    for x, w in zip(xs, ws):                                                          # absorber lines, face down
        ab.box((x * r * 2 * 0.98, y_pf - r * 0.03, 0), (w * r * 2, r * 0.06, D * 0.999))
    xb = -W / 2 + r * 0.09                                                            # frame bar at the left end
    fb.box((xb, (y_pf + y_mem) / 2 - r * 0.02, 0), (r * 0.18, (y_pf - y_mem) + r * 0.04, D * 1.02))
    mem.box((r * 0.06, y_mem - t_mem / 2, 0), (W - r * 0.02, t_mem, D * 0.98))      # membrane bonded to the bar
    gx = r * 0.44
    gapr.tube(Vector((gx, y_mem + t_mem * 0.5, D / 2 + r * 0.01)), Vector((gx, y_pf - r * 0.06, D / 2 + r * 0.01)),
              r * 0.012, seg=10)
    for yy in (y_mem + t_mem * 0.5, y_pf - r * 0.06):
        gapr.tube(Vector((gx - r * 0.06, yy, D / 2 + r * 0.01)), Vector((gx + r * 0.06, yy, D / 2 + r * 0.01)),
                  r * 0.01, seg=8)
    for mb, nm, mat, bv in ((sub, "MagSubstrateR21", _m("MagSubR21M", (0.16, 0.17, 0.22), emit=0.35, metal=0.3, rough=0.3), r * 0.01),
                            (ml, "MagMultilayerR21", _m("MagMLR21M", (0.62, 0.64, 0.72), emit=0.45, metal=0.6, rough=0.2), 0.0),
                            (ab, "MagAbsorberR21", _m("MagAbR21M", (0.03, 0.03, 0.04), emit=0.0, rough=0.6), 0.0),
                            (fb, "MagFrameBarR21", K.mat("MagFrameR21M", (0.03, 0.031, 0.036), metal=0.8, rough=0.28), r * 0.01),
                            (mem, "MagMembraneR21", _m("MagMemR21M", (0.86, 0.88, 0.92), emit=1.1, rough=0.1), 0.0),
                            (gapr, "MagGapRuleR21", K.emit_mat("MagGapRuleR21M", K.CYAN, 5.0), 0.0)):
        ob = mb.obj(nm, mat, bevel=bv)
        ob.parent = blk
        obs.append(ob)
    # a soft key on the magnifier only (it sits in the dark under the chuck): light-linked to the magnifier parts
    kl = bpy.data.lights.new("MagKeyR21", "AREA")
    kl.energy, kl.size = 6.0, r * 3
    klo = bpy.data.objects.new("MagKeyR21", kl)
    sc.collection.objects.link(klo)
    klo.parent = rig
    klo.location = (-r * 1.2, r * 1.4, r * 2.2)
    klo.rotation_euler = (Vector((0, 0, 0)) - Vector(klo.location)).to_track_quat("-Z", "Y").to_euler()
    try:
        rc = bpy.data.collections.new("MagReceiversR21")
        for ob in obs:
            rc.objects.link(ob)
        klo.light_linking.receiver_collection = rc
    except Exception:
        pass
    obs.append(klo)
    for ob in obs:
        ob.hide_render = True
        ob.keyframe_insert("hide_render", frame=1)
        ob.keyframe_insert("hide_render", frame=f_on - 1)
        ob.hide_render = False
        ob.keyframe_insert("hide_render", frame=f_on)
    # anchors: R20 set (flipped) + magnifier points (empties so they follow the camera)
    import misc_b612_r20 as P20
    M = P20._flip_matrix()
    pts = {k: M @ Vector(v) for k, v in anchors20.items()}

    def emp(name, loc):
        e = bpy.data.objects.new(name, None)
        sc.collection.objects.link(e)
        e.parent = blk
        e.location = loc
        return e
    xr = W / 2 + r * 0.02
    pts["mag_c"] = rig
    pts["mag_rim"] = emp("MagRimLeftR21", (-r * 1.07, -r * 0.2, 0))
    pts["mag_pat"] = emp("MagPatR21", (xr, y_pf, D / 2))
    pts["mag_gap"] = emp("MagGapR21", (xr, (y_pf + y_mem) / 2, D / 2))
    pts["mag_mem"] = emp("MagMemR21", (xr, y_mem, D / 2))
    K.anchors("B6_12", pts)
    print(f"[R21 B6_12] magnifier d={d:.3f} r={r:.4f} on from frame {f_on}")
