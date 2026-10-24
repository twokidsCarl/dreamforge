"""R23 row 2 (camera motion, D dimension) for B7_06 / A0_10 / B8_03 (+ B8_03M keeps its PIP camera).

R22 review: A0_10 「三帧机位几乎不动，只有光和字幕变化」 (D 62); B7_06 D 72; B8_03 「几乎看不见…反向的运动」 (D 75).
R23 sketch: A0_10 2.6 m truck at 15 m (anchors shift ~50 px, no parallax); B7_06 0.25 m (PO 12 px); B8_03 0.23 m.
  * B7_06: turntable -22 -> +26 deg (linear; R22 -14 -> +12 eased) = ~29 deg between the 25 % and 85 % job frames,
           camera keeps the R22 crane with a slightly longer truck (0.25 -> 0.85 m); person / posts give parallax.
           (8-spp try 1 with a 14 deg camera orbit hid the incoming cone at 25 % and cut the person at 85 %.)
  * A0_10: dolly in + truck: ~16.5 m -> ~13.6 m (55 % frame, R22 framing x1.08) -> ~9 m; a clean-room column
           stands between camera and machine (foreground layer).
  * B8_03: slow push (offset to the target x1.10 -> x1.0 -> x0.85 at the job frames) + focus pull (far bay -> wafer).
The 55 % frame stays within ~10 % of the R22 framing on every shot.
"""
import math
import bpy
from mathutils import Vector


def _key(cam, tgt, keys, interp="BEZIER"):
    for ob in (cam, tgt):
        ob.animation_data_clear()
    for f, cl, tl in keys:
        cam.location = cl
        cam.keyframe_insert("location", frame=f)
        tgt.location = tl
        tgt.keyframe_insert("location", frame=f)
    import common as C
    for ob in (cam, tgt):
        for fc in C.fcurves(ob.animation_data.action):
            for k in fc.keyframe_points:
                k.interpolation = interp
                k.handle_left_type = k.handle_right_type = "AUTO_CLAMPED"
            fc.update()


def b7_06(sc):
    n = sc.frame_end
    piv = bpy.data.objects.get("Turntable")
    if piv is not None:
        piv.animation_data_clear()
        for f, deg in ((1, -22.0), (n, 26.0)):
            piv.rotation_euler = (0, 0, math.radians(deg))
            piv.keyframe_insert("rotation_euler", frame=f)
        import common as C
        for fc in C.fcurves(piv.animation_data.action):
            for k in fc.keyframe_points:
                k.interpolation = "LINEAR"
    cam = bpy.data.objects.get("CamR2")
    tgt = bpy.data.objects.get("CamR2_tgt")
    if cam is None or tgt is None:
        return
    # R22 path: (0.4,-4.3,3.0) -> (0.55,-4.2,2.7) @55 % -> (0.7,-4.05,2.45); orbit around the barrel axis (x=y=0)
    keys = []
    for f, cl, tl in ((1, (0.25, -4.3, 3.05), (0.1, 0, 2.15)), (round(n * 0.55), (0.55, -4.2, 2.7), (0.1, 0, 2.18)),
                      (n, (0.85, -4.05, 2.4), (0.1, 0, 2.2))):
        keys.append((f, cl, tl))
    _key(cam, tgt, keys)


# 8-spp try 3: with the end pan the column stood in front of the PO bay at f184 and hid the mask -> PO segment (path
# break = NO-GO); no spot gives >= 60 px parallax without crossing the path. Off: the dolly's own depth layers carry
# the parallax (open doors / front frame / people vs the bay back wall: 145 / 102 / 97 px relative, first -> last).
A0_FG_COLUMN = False


def a0_10(sc):
    n = sc.frame_end
    cam = bpy.data.objects.get("CamR2")
    tgt = bpy.data.objects.get("CamR2_tgt")
    if cam is None or tgt is None:
        return
    # 8-spp try 1 ended at ~9 m: the roof ran under the title and the people / scale tag were cut at the bottom ->
    # end at ~12.8 m, aimed a little higher (whole machine stays under the title block).
    keys = [(1, (-8.0, -17.4, 2.2), (-4.9, 0, 3.28)),
            (54, (-6.9, -16.6, 2.25), (-4.3, 0, 3.3)),
            (119, (-3.0, -13.6, 2.4), (-2.9, 0, 3.58)),   # 3.35 put the roof edge under the subtitle (8-spp try 2)
            (184, (-0.8, -12.8, 2.5), (-2.2, 0, 3.55)),
            (n, (-0.2, -12.5, 2.52), (-2.1, 0, 3.58))]
    _key(cam, tgt, keys)
    if not A0_FG_COLUMN:
        return None
    # foreground layer: a clean-room column between the camera and the machine (parallax against the bays)
    import kit_r2 as K
    mb = K.MB()
    x, y = 1.5, -5.4      # screen x 935 / 943 / 886 at the job frames vs wafer column 768 / 772 / 780
    mb.box((x, y, 3.5), (0.42, 0.42, 7.0))
    mb.box((x, y, 0.06), (0.62, 0.62, 0.12))
    mb.box((x, y, 6.9), (0.62, 0.62, 0.16))
    ob = mb.obj("A0FgColumnR23", K.mat("FgColR23", (0.62, 0.64, 0.67), rough=0.45))
    return ob


def b8_03(sc, shot):
    if shot == "B8_03M":
        return
    n = sc.frame_end
    cam = bpy.data.objects.get("CamR2")
    tgt = bpy.data.objects.get("CamR2_tgt")
    if cam is None or tgt is None:
        return
    p0, p1 = Vector((-0.3, -1.98, 1.52)), Vector((0.08, -2.0, 1.5))
    t = Vector((0.04, -0.66, 0.84))
    keys = []
    for f, s in ((1, 1.16), (42, 1.10), (92, 1.0), (143, 0.85), (n, 0.79)):
        u = (f - 1) / (n - 1)
        p = p0.lerp(p1, u)
        keys.append((f, tuple(t + (p - t) * s), tuple(t)))
    _key(cam, tgt, keys)
    d = cam.data.dof
    d.use_dof = True
    d.focus_object = None
    d.aperture_fstop = 3.2
    w = bpy.data.objects.get("WStage_wafer")
    # wafer mesh is built in world space (origin at 0): focus on its bounding-box centre (8-spp try 1 focused 0,0,0)
    wp = (sum((w.matrix_world @ Vector(c) for c in w.bound_box), Vector()) / 8) if w is not None else Vector(t)
    for f, fd in ((1, 2.6), (30, 2.4), (92, None), (n, None)):
        sc.frame_set(f)
        dist = (cam.matrix_world.translation - Vector(wp)).length
        d.focus_distance = fd if fd else dist
        d.keyframe_insert("focus_distance", frame=f)
    sc.frame_set(1)
