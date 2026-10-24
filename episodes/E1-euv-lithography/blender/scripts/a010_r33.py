"""Round 33 A0_10 (R33_ROOT_CAUSE row 2; MAIN process, wired via r2_cutaway.R33_A010; layered after a010_r32 and BEFORE
beam_hook_r29).

R32 self-check: the continuous path (R32 slots + straight PFM -> mask leg) sat in a ~60 px band of the wide shot =
not delivered. R32 p2: 「光在一组鳍片和一个螺旋圆盘处拐弯，读成在暖气片上拐弯」「掩模是一块蓝色小方格板，像太阳能板」.
One switch, PATH_R33 (on top of a010_r32.PATH_R32, whose slots / exit port / leg geometry stay as they are):
  * the two illuminator turn points (FFM facet plate = 「鳍片」, PFM pupil disc = 「螺旋圆盘」) are replaced by ONE turn
    mirror model used twice: a solid polished disc + a deep ring mount + a post, the R31 landing spot on its face;
  * the mask (R8Kit2_mask, blue EUVMaskR10 grid) becomes the C_03 frame-3 look: black base with fine grey line
    pattern, a light clamp frame around it and four cross marks;
  * camera push-in over the later frames, done with the focal length + lens shift (same camera position and
    perspective, so the R32 occlusion slots stay valid): from f60 the view narrows onto the illuminator + mask +
    barrel band (IF -> wafer), ~1.25x at the mid frame and ~1.45x at the end frame, so the continuous path fills the
    frame in a 480 px side-by-side.
Remove A0_10 from R33_A010 / PATH_R33 False -> R32 pixels.
"""
import math

import bpy
from mathutils import Matrix, Vector

PATH_R33 = True
ZOOM = ((60, 1.0), (90, 1.08), (119, 1.20), (150, 1.28), (184, 1.32), (240, 1.32))
BAND_DY = -0.075          # band centre aimed above its box centre (content moves down) so the illuminator clears the title block
FFM_R, PFM_R = 0.34, 0.27
HIDE = ("A0R31FfmPlate", "A0R31FfmStrips", "A0R31FfmMounts", "A0R31FfmMount", "A0R32FfmFrame", "A0R31PfmFacets",
        "A0R31PfmCups", "A0R31PfmCarrier", "A0R31PfmFlange")
LOG = {}


def pre(variant, shot, mod):
    return None


def _normals(sc):
    import a010_r26 as A
    import a010_r31 as A31
    sc.frame_set(119)
    cam = sc.camera.matrix_world.translation
    F, P = A31.FFM_P, A31.PFM_P
    n_f0 = ((A.ENTRY - F).normalized() + (P - F).normalized()).normalized()
    n_f = (n_f0 + (cam - F).normalized() * 0.9).normalized()
    n_p0 = ((F - P).normalized() + (A.EXIT - P).normalized()).normalized()
    n_p = (n_p0 + (cam - P).normalized() * 0.9).normalized()
    return (F, n_f), (P, n_p)


def turn_mirror(name, C, n, R, mats):
    """one model: polished disc (face at C) + deep ring mount + post down to the shelf."""
    import kit_r2 as K
    q = Vector((0, 0, 1)).rotation_difference(n)
    M = Matrix.Translation(C - n * 0.045) @ q.to_matrix().to_4x4()
    disc, ring, post = K.MB(), K.MB(), K.MB()
    disc.cyl_m(M, R, 0.07, seg=64)
    ring.ring(C - n * 0.05, R + 0.07, R - 0.01, 0.14, rot=q.to_euler(), seg=64)
    base = C - n * 0.12
    post.tube(base, base + Vector((0, 0, -0.62)), 0.045)
    post.box(tuple(base + Vector((0, 0, -0.64))), (0.20, 0.20, 0.04))
    post.tube(base, C - n * 0.05 + Vector((0, 0, -(R + 0.05))), 0.035)
    return [disc.obj(name + "Disc", mats[0]), ring.obj(name + "Ring", mats[1], bevel=0.008),
            post.obj(name + "Post", mats[2])]


def _mirrors(sc):
    import cut_mirror_r19 as CM
    import kit_r2 as K
    n_h = 0
    for nm in HIDE:
        ob = bpy.data.objects.get(nm)
        if ob is not None:
            ob.hide_render = True
            n_h += 1
    mats = (CM.hi_mirror(rough=0.06, tone=0.85), K.mat("A0R33RingM", (0.30, 0.31, 0.34), metal=0.9, rough=0.3),
            K.mat("A0R33PostM", (0.50, 0.51, 0.55), metal=1.0, rough=0.25))
    (F, n_f), (P, n_p) = _normals(sc)
    obs = turn_mirror("A0R33Ffm", F, n_f, FFM_R, mats) + turn_mirror("A0R33Pfm", P, n_p, PFM_R, mats)
    return n_h, len(obs)


def _mask():
    """C_03 frame-3 mask look: black base + fine line pattern, light clamp frame, four cross marks."""
    import kit_r2 as K
    ob = bpy.data.objects.get("R8Kit2_mask")
    if ob is None or ob.type != "MESH":
        return None
    m = bpy.data.materials.new("A0R33MaskM")
    m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    b = next(n for n in N if n.type == "BSDF_PRINCIPLED")
    tc = N.new("ShaderNodeTexCoord")
    mp = N.new("ShaderNodeMapping")
    L.new(tc.outputs["Object"], mp.inputs["Vector"])
    w = N.new("ShaderNodeTexWave")
    w.wave_type = "BANDS"
    w.inputs["Scale"].default_value = 30.0
    w.inputs["Distortion"].default_value = 0.0
    L.new(mp.outputs["Vector"], w.inputs["Vector"])
    br = N.new("ShaderNodeTexChecker")
    br.inputs["Scale"].default_value = 3.0
    br.inputs["Color1"].default_value = (1, 1, 1, 1)
    br.inputs["Color2"].default_value = (0.35, 0.35, 0.35, 1)
    L.new(mp.outputs["Vector"], br.inputs["Vector"])
    ramp = N.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.80
    ramp.color_ramp.elements[0].color = (0.012, 0.012, 0.016, 1)
    ramp.color_ramp.elements[1].position = 0.86
    ramp.color_ramp.elements[1].color = (0.42, 0.43, 0.48, 1)
    L.new(w.outputs["Fac"], ramp.inputs["Fac"])
    mul = N.new("ShaderNodeMix")
    mul.data_type = "RGBA"
    mul.blend_type = "MULTIPLY"
    mul.inputs["Factor"].default_value = 1.0
    L.new(ramp.outputs["Color"], mul.inputs[6])
    L.new(br.outputs["Color"], mul.inputs[7])
    L.new(mul.outputs[2], b.inputs["Base Color"])
    b.inputs["Metallic"].default_value = 0.6
    b.inputs["Roughness"].default_value = 0.25
    for s in ob.material_slots:
        if s.material is not None and s.material.name.startswith("EUVMaskR10"):
            s.material = m
    # clamp frame + cross marks around the largest planar face group
    me = ob.data
    mw = ob.matrix_world
    big = max(me.polygons, key=lambda p: p.area)
    n = (mw.to_3x3() @ big.normal).normalized()
    pts = [mw @ me.vertices[i].co for p in me.polygons if (mw.to_3x3() @ p.normal).normalized().dot(n) > 0.98
           for i in p.vertices]
    u = n.orthogonal().normalized()
    v = n.cross(u).normalized()
    c0 = sum(pts, Vector()) / len(pts)
    us = [(p - c0).dot(u) for p in pts]
    vs = [(p - c0).dot(v) for p in pts]
    cu, cv = (max(us) + min(us)) / 2, (max(vs) + min(vs)) / 2
    W, H = max(us) - min(us), max(vs) - min(vs)
    c = c0 + u * cu + v * cv + n * 0.01
    rot = Matrix((u, v, n)).transposed().to_euler()
    bw = max(W, H) * 0.06
    fr, cx = K.MB(), K.MB()
    for s_ in (-1, 1):
        fr.box(tuple(c + u * s_ * (W / 2 + bw / 2)), (bw, H + 2 * bw, 0.04), rot=rot)
        fr.box(tuple(c + v * s_ * (H / 2 + bw / 2)), (W + 2 * bw, bw, 0.04), rot=rot)
    for su in (-1, 1):
        for sv in (-1, 1):
            p = c + u * su * (W / 2 - bw * 0.9) + v * sv * (H / 2 - bw * 0.9) + n * 0.012
            cx.box(tuple(p), (bw * 0.9, bw * 0.18, 0.006), rot=rot)
            cx.box(tuple(p), (bw * 0.18, bw * 0.9, 0.006), rot=rot)
    fr.obj("A0R33MaskFrame", K.mat("A0R33MaskFrameM", (0.82, 0.82, 0.84), metal=0.2, rough=0.45))
    cx.obj("A0R33MaskCross", K.mat("A0R33MaskCrossM", (0.95, 0.95, 0.95), metal=0.0, rough=0.5))
    return (round(W, 2), round(H, 2))


def _band_points():
    import a010_r26 as A
    import a010_r31 as A31
    return [A.IF, A31.FFM_P, A31.PFM_P, A.EXIT, A.MASK, A.BARREL[0], A.BARREL[1], A.WAFER]


def _zoom(sc):
    """lens + shift keys: the view narrows onto the band's screen box centre (computed at zoom 1 per key frame)."""
    from bpy_extras.object_utils import world_to_camera_view as w2c
    cam = sc.camera
    cd = cam.data
    base = cd.lens
    if cd.animation_data:
        cd.animation_data_clear()
    pts = _band_points()
    keys = []
    for f, z in ZOOM:
        sc.frame_set(f)
        cd.lens, cd.shift_x, cd.shift_y = base, 0.0, 0.0
        sp = [w2c(sc, cam, p) for p in pts]
        xs, ys = [s.x for s in sp], [1 - s.y for s in sp]
        cx_, cy_ = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2 + BAND_DY
        keys.append((f, z, cx_, cy_))
    aspect = sc.render.resolution_y / sc.render.resolution_x
    for f, z, cx_, cy_ in keys:
        k = (z - 1.0) / max(ZOOM[-1][1] - 1.0, 1e-6)          # shift grows with the zoom (no jump at the start)
        cd.lens = base * z
        cd.shift_x = z * (cx_ - 0.5) * k
        cd.shift_y = z * (0.5 - cy_) * aspect * k
        cd.keyframe_insert("lens", frame=f)
        cd.keyframe_insert("shift_x", frame=f)
        cd.keyframe_insert("shift_y", frame=f)
    import common as C
    for fc in C.fcurves(cd.animation_data.action):
        for kp in fc.keyframe_points:
            kp.interpolation = "BEZIER"
            kp.easing = "EASE_IN_OUT"
    LOG["zoom"] = [(f, z, round(cx_, 3), round(cy_, 3)) for f, z, cx_, cy_ in keys]
    return base


def post(sc, variant, shot):
    if not PATH_R33 or shot != "A0_10":
        return sc
    n_h, n_m = _mirrors(sc)
    wh = _mask()
    base = _zoom(sc)
    print(f"[a010r33] turn mirrors: {n_h} R31/R32 plate / disc parts hidden, {n_m} disc-mirror objs; mask C_03 look {wh}; "
          f"zoom from lens {base} {LOG.get('zoom')}", flush=True)
    sc.frame_set(1)
    return sc
