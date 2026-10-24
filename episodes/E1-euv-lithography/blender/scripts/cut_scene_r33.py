"""Round 33 scene hook (MAIN process; r2_cutaway.R33_SCENE), layered after the R32 hooks and before beam_hook_r29.

  B302_R33 (row 1, B3_02 - lowest R32 80.66, H13): R32 p2 「反射光画成一条向右上方逐渐变宽、发散的光带，像手电筒，看不出向 IF
           会聚的光锥」「IF 引线指向一个螺旋波纹管」「镜外圈的放射杆像船舵」. Geometry (R33_ROOT_CAUSE row 1): the R32 camera
           (azimuth 44 deg, 6 m from the dish) stood ~4.4 m from the IF, nearer than the dish, so perspective blew the tip up;
           the face-frustum cut then left a shape that widened from the rim toward the IF. R33 keeps the R32 structure
           (free-standing bowl + rim + mount, no chrome drum, hole / plasma / IF coaxial) and changes the GEOMETRY:
    * side camera: the IF is at least as far from the lens as the dish (no perspective inflation of the tip), IF in the
      middle-right of the frame, dish face still seen as a deep bowl;
    * the cone is rebuilt for the new camera: whole rim -> IF tip (minus the camera frustums through the dish face,
      src_r32.cut_by_faces), a small aperture ring at the IF and a short cone that opens slightly past the IF;
    * the radial brackets around the rim (CollectorBracketR24, read as a ship's wheel) are removed; the mount gets
      cooling pipes from the back of the dish to the pedestal (the real mount + cooling read);
    * the big area lights (Key / FillL / DishKey) are hidden from glossy rays only, so the dish mirrors a dark chamber
      with grazing highlights instead of one grey wash (90/10 back in 4-10);
    * the IF tag follows the 3D IF point (anchors), so its leader lands on the bright point in the air.
Remove B3_02 from R33_SCENE / B302_R33 False -> R32 pixels.
"""
import math
import os

import bpy
from mathutils import Vector

B302_R33 = True
# camera keys: (frame fraction, azimuth deg from the axis toward -y, elevation deg, distance m from the dish, target
# fraction dish -> IF). Azimuth 71-74 deg at 5-5.6 m: |cam - IF| >= |cam - dish| (sketch33/b302_measure.txt)
KEYS = ((0.0, 76.0, -7.0, 6.4, 0.46), (1.0, 73.0, -9.0, 5.8, 0.44))
TGT_DZ = -0.30           # target lowered so the pedestal + pipes stay in frame
LENS = 27.0
POST_LEN = 0.75          # cone past the IF (opens slightly)
POST_R = 0.16
RING_R = 0.15            # aperture ring at the IF (outer radius)
HIDE = ("CollectorBracketR24",)
GLOSS_OFF = ("Key", "FillL", "DishKey")   # big area lights hidden from glossy rays only: at the side camera the dish
                         # mirrored them as one grey wash (32 spp dish 90/10 3.1-3.6, world / tone / haze ruled out in
                         # sketch33); the grazing lights stay -> dark chamber + a few highlights
BELLOWS_X0 = -3.95        # IF bellows (R2_flange, x -4.71 .. -3.21 after the R32 drum cut) compressed toward its far end so
                          # the IF is a point in the air in front of it (R32 p2 「IF 引线指向一个螺旋波纹管」)


def pre(variant, shot, mod):
    return None


def _cam_keys(sc):
    """cut_scene_r32._camera with the R33 keys and a lowered target."""
    import kit_r2 as K
    import cut_scene_r32 as S
    S.LENS = LENS
    S.KEYS = ((0.0, 0.0, 0.0, 1.0, 0.0),)
    S._camera(sc)                                  # clears the R32 animation / constraints, sets the lens
    cam = sc.camera
    tgt = next((c.target for c in cam.constraints if c.type == "TRACK_TO"), None)
    if tgt is not None and tgt.animation_data:
        tgt.animation_data_clear()
    if cam.animation_data:
        cam.animation_data_clear()
    f0, f1 = sc.frame_start, sc.frame_end
    keys = []
    for fr, az, el, dist, tf in KEYS:
        a, e = math.radians(az), math.radians(el)
        d = Vector((math.cos(a) * math.cos(e), -math.sin(a) * math.cos(e), math.sin(e)))
        T = S.DISH_C.lerp(S.IF_P, tf) + Vector((0, 0, TGT_DZ))
        keys.append((round(f0 + (f1 - f0) * fr), S.DISH_C + d * dist, T))
    if tgt is not None:
        K.key_path(cam, tgt, keys)
    return keys


def _drop_r32_cone():
    n = 0
    for o in list(bpy.data.objects):
        if o.name.startswith(("B302ConeR32", "B302FaceFrustum")):
            bpy.data.objects.remove(o, do_unlink=True)
            n += 1
    return n


def _cone(sc):
    """whole rim -> IF (minus the dish-face frustums for THIS camera) + a short cone that opens past the IF."""
    import beam_r29 as B29
    import cut_scene_r32 as S
    import src_r32
    orig = getattr(B29.cone, "_r30_orig", B29.cone)
    ax = S.AX
    a = S.MOUTH_C
    tip = S.IF_P
    ob = orig("B302ConeR33", a, tip, S.MOUTH_R, 0.025, None, B29.B_DEFAULT)
    src_r32.cut_by_faces(sc, ob, (30, 67, 103), S.MOUTH_C, ax, S.MOUTH_R * 1.06, "B302FaceR33")
    post = orig("B302PostR33", tip, tip + ax * POST_LEN, 0.025, POST_R, None, B29.B_DEFAULT * 0.8)
    for o in (ob, post):
        o["r29_replaced"] = "cut_scene_r33"
    return ob, post


def _ring_and_point():
    import kit_r2 as K
    import cut_scene_r32 as S
    q = Vector((0, 0, 1)).rotation_difference(S.AX)
    rg = K.MB()
    rg.ring(S.IF_P, RING_R, RING_R - 0.035, 0.03, rot=q.to_euler(), seg=48)
    ring = rg.obj("B302IFRingR33", K.mat("B302IFRingR33M", (0.62, 0.63, 0.66), metal=1.0, rough=0.22), bevel=0.004)
    pt = K.MB()
    pt.sphere(S.IF_P, 0.035, seg=16)
    m = bpy.data.materials.new("B302IFPointR33M")
    m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    for n in list(N):
        if n.type != "OUTPUT_MATERIAL":
            N.remove(n)
    em = N.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (0.86, 0.80, 1.0, 1)
    em.inputs["Strength"].default_value = 30.0
    L.new(em.outputs[0], next(n for n in N if n.type == "OUTPUT_MATERIAL").inputs["Surface"])
    point = pt.obj("B302IFPointR33", m)
    point.visible_shadow = False
    old = bpy.data.objects.get("IFPinch")
    if old is not None:
        old.hide_render = True
    return ring, point


def _pipes():
    """cooling pipes: a manifold ring on the back of the dish + three pipes down to the pedestal base."""
    import kit_r2 as K
    import cut_scene_r32 as S
    q = Vector((0, 0, 1)).rotation_difference(S.AX)
    mb = K.MB()
    back = S.DISH_C - S.AX * 0.30
    mb.ring(back, 0.78, 0.72, 0.06, rot=q.to_euler(), seg=64)
    base = Vector((S.DISH_C.x - 0.15, 0, 0.42))
    for k, ang in enumerate((215.0, 270.0, 325.0)):
        t = math.radians(ang)
        p = back + Vector((0, 0.75 * math.cos(t), 0.75 * math.sin(t)))
        mid = Vector((p.x - 0.35, p.y * 0.8, p.z - 0.25))
        end = base + Vector((-0.25, (k - 1) * 0.28, 0))
        mb.path([p, mid, Vector((end.x, end.y, mid.z - 0.2)), end], 0.035, seg=10)
    return mb.obj("B302PipesR33", K.mat("B302PipesR33M", (0.55, 0.56, 0.58), metal=1.0, rough=0.28), bevel=0.0)


def _bellows():
    ob = bpy.data.objects.get("R2_flange")
    if ob is None or ob.type != "MESH":
        return None
    import cut_scene_r32 as S
    S._bake(ob)
    mw, mi = ob.matrix_world, ob.matrix_world.inverted()
    xs = [(mw @ v.co).x for v in ob.data.vertices]
    x0, x1 = min(xs), max(xs)
    k = (x1 - BELLOWS_X0) / max(x1 - x0, 1e-6)
    for v in ob.data.vertices:
        w = mw @ v.co
        w.x = x1 - (x1 - w.x) * k
        v.co = mi @ w
    ob.data.update()
    return (round(x0, 2), round(x1, 2), round(k, 2))


def _measure(sc):
    """screen widths of the cone at the rim and at the IF (ROUND_PIPELINE: focus end <= wide end / 4.5) + distances."""
    from bpy_extras.object_utils import world_to_camera_view as w2c
    import cut_scene_r32 as S
    W, H = 960, 540
    out = []
    u = S.AX.orthogonal().normalized()
    v = S.AX.cross(u).normalized()
    for f in (30, 67, 103):
        sc.frame_set(f)
        cam = sc.camera
        cpos = cam.matrix_world.translation

        def P(p):
            q = w2c(sc, cam, p)
            return Vector((q.x * W, (1 - q.y) * H))
        tip = P(S.IF_P)
        mc = P(S.MOUTH_C)
        d = (tip - mc).normalized()
        nrm = Vector((-d.y, d.x))
        rim = [P(S.MOUTH_C + (u * math.cos(t) + v * math.sin(t)) * S.MOUTH_R) for t in [i * math.pi / 32 for i in range(64)]]
        wide = max((p - mc).dot(nrm) for p in rim) - min((p - mc).dot(nrm) for p in rim)
        ring = [P(S.IF_P + (u * math.cos(t) + v * math.sin(t)) * RING_R) for t in [i * math.pi / 16 for i in range(32)]]
        rw = max((p - tip).dot(nrm) for p in ring) - min((p - tip).dot(nrm) for p in ring)
        out.append(f"f{f} wide {wide:.0f}px ifring {rw:.1f}px ratio {wide / max(rw, 1e-3):.1f} tip ({tip.x:.0f},{tip.y:.0f}) "
                   f"mouth ({mc.x:.0f},{mc.y:.0f}) d_dish {(cpos - S.DISH_C).length:.2f} d_IF {(cpos - S.IF_P).length:.2f}")
    return out


def post(sc, variant, shot):
    if not (B302_R33 and shot == "B3_02"):
        return sc
    for nm in HIDE:
        ob = bpy.data.objects.get(nm)
        if ob is not None:
            ob.hide_render = True
    keys = _cam_keys(sc)
    n_g = 0
    for nm in GLOSS_OFF:
        lt = bpy.data.objects.get(nm)
        if lt is not None and lt.type == "LIGHT":
            lt.visible_glossy = False
            n_g += 1
    n_old = _drop_r32_cone()
    cone, postc = _cone(sc)
    ring, point = _ring_and_point()
    pipes = _pipes()
    bel = _bellows()
    meas = _measure(sc)
    print(f"[cut_scene_r33] B3_02 camera keys {[(k[0], tuple(round(x, 2) for x in k[1])) for k in keys]}; R32 cone objs "
          f"dropped {n_old}; cone {cone.name} + post {postc.name}; ring {ring.name}; point {point.name}; pipes {pipes.name}; bellows x/k {bel}; glossy-hidden lights {n_g}",
          flush=True)
    for m in meas:
        print(f"[cut_scene_r33] MEASURE {m}", flush=True)
    sc.frame_set(1)
    return sc
