"""Round 28 hook for B1_15 (MAIN PROCESS; shot in r2_source.R28_SRC). Layered AFTER src_r27 (cone base = bowl mouth,
short exit leg, landing ring). Remove B1_15 from R28_SRC -> exact R27 pixels. One switch per R28_ROOT_CAUSE row:

  CAM_R28   (row 2, camera) R27 p1 「光锥从镜子下沿穿出、IF 在镜子背后…读成『光穿过镜背』」: the R22 camera sits 58 deg
            above the axis with the axis running VERTICALLY on screen, so the IF projects below the lower rim over the
            grey vessel / bowl exterior. New camera on the MOUTH side, beside the axis (TH deg from the axis, E deg
            above the horizontal plane through it, on the cut -y side of the vessel), screen-up = world +Z: the axis
            runs left -> right, bowl interior on the left (we look into the mouth), the reflected cone leaves the
            whole mouth and converges to the right onto the IF against the dark far wall - nothing of the bowl lies
            behind the IF. Pure dolly push (D0 -> D1) + focus pull plasma -> IF (D row kept).
  ENV_R28   (row 2m, mirror read) R27 p1 「镜面内腔是暗底加几条灰色弧形带…加一条连续的环境反射高光和等离子体倒影」:
            one long curved lit window strip (camera-only for direct view, glossy-visible) placed so that its
            reflection runs as ONE continuous bright arc across the bowl face from this camera; the plasma kernel
            stays glossy-visible (its image on the face).
"""
import math
import os

import bpy
from mathutils import Matrix, Vector

CAM_R28 = True
ENV_R28 = True

_E = os.environ
TH = math.radians(float(_E.get("B128_TH", "64")))     # camera direction angle from the mirror axis (+X)
EL = math.radians(float(_E.get("B128_EL", "22")))     # elevation of the camera out of the horizontal plane
D0 = float(_E.get("B128_D0", "3.0"))
D1 = float(_E.get("B128_D1", "2.55"))
LOOK0 = Vector(tuple(float(v) for v in _E.get("B128_LOOK0", "0.30,0,-0.02").split(",")))
LOOK1 = Vector(tuple(float(v) for v in _E.get("B128_LOOK1", "0.34,0,-0.02").split(",")))
LENS = float(_E.get("B128_LENS", "32"))


EXIT_LEG = "0.12"     # src_r27 S27_EL (post-IF exit leg, x IF-mouth distance): 0.3 fans out over the far wall in the new view


def pre(variant, shot, mod):
    if shot == "B1_15" and CAM_R28:
        os.environ.setdefault("S27_EL", EXIT_LEG)   # read by src_r27._b115 at post time (same process, pods too)


def _dirc():
    # -y side of the vessel (the wall is cut there), elevated EL above the horizontal plane through the axis
    return Vector((math.cos(TH), -math.sin(TH) * math.cos(EL), math.sin(TH) * math.sin(EL))).normalized()


def _quat(fwd):
    up = Vector((0, 0, 1))
    up = (up - fwd * up.dot(fwd)).normalized()
    right = fwd.cross(up)
    return Matrix((right, up, -fwd)).transposed().to_quaternion()


def _camera(sc):
    import b115_r21 as B
    import b115_r22_build as BB
    cam = sc.camera
    n = sc.frame_end
    if cam.animation_data:
        cam.animation_data_clear()
    for c_ in cam.constraints:
        c_.mute = True
    cam.rotation_mode = "QUATERNION"
    cam.data.lens = LENS
    d = _dirc()
    for f, look, dist in ((1, LOOK0, D0), (n, LOOK1, D1)):
        cam.location = look + d * dist
        cam.rotation_quaternion = _quat((look - cam.location).normalized())
        cam.keyframe_insert("location", frame=f)
        cam.keyframe_insert("rotation_quaternion", frame=f)
    import source_r26_tin as T26
    for fc in T26._fcs(cam):
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR"
    foc = cam.data.dof.focus_object
    xr, xi0 = B.fx(B.R), BB.image_x()
    xi = xr + float(_E.get("S25_IFF", "0.62")) * (xi0 - xr)
    if foc is not None:
        if foc.animation_data:
            foc.animation_data_clear()
        for f, p in ((1, B.PC), (int(n * 0.35), B.PC), (int(n * 0.9), Vector((xi, 0, 0))), (n, Vector((xi, 0, 0)))):
            foc.location = p
            foc.keyframe_insert("location", frame=f)
    cam.data.dof.aperture_fstop = float(_E.get("B128_FS", "5.6"))
    return xr, xi


def _env_strip(sc):
    """A long lit window strip on the far (+y, upper) vessel side. Its mirror image on the concave face, seen from
    the -y camera, is one continuous arc. Direct view hidden (camera ray off) so it is only seen IN the mirror."""
    import bmesh
    import kit_r2 as K
    import b115_r21 as B
    a0, a1 = math.radians(float(_E.get("B128_SA0", "100"))), math.radians(float(_E.get("B128_SA1", "175")))
    x0, x1 = float(_E.get("B128_SX0", "0.25")), float(_E.get("B128_SX1", "0.55"))
    rr = float(_E.get("B128_SR", "1.25"))
    bm = bmesh.new()
    na = 40
    rows = []
    for x in (x0, x1):
        row = []
        for i in range(na + 1):
            b = a0 + (a1 - a0) * i / na          # world (y, z) = (r sin b, -r cos b) (b115_r21 convention)
            row.append(bm.verts.new((x, rr * math.sin(b), -rr * math.cos(b))))
        rows.append(row)
    for i in range(na):
        bm.faces.new((rows[0][i], rows[0][i + 1], rows[1][i + 1], rows[1][i]))
    me = bpy.data.meshes.new("B115EnvStripR28")
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new("B115EnvStripR28", me)
    sc.collection.objects.link(ob)
    m = bpy.data.materials.new("B115EnvStripR28M")
    m.use_nodes = True
    N = m.node_tree.nodes
    for nd in list(N):
        if nd.type != "OUTPUT_MATERIAL":
            N.remove(nd)
    em = N.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (0.82, 0.88, 1.0, 1)
    em.inputs["Strength"].default_value = float(_E.get("B128_SE", "10.0"))
    m.node_tree.links.new(em.outputs[0], next(nd for nd in N if nd.type == "OUTPUT_MATERIAL").inputs["Surface"])
    ob.data.materials.append(m)
    ob.visible_camera = False
    ob.visible_diffuse = False
    ob.visible_shadow = False
    return ob


def post(sc, variant, shot):
    if shot != "B1_15" or variant != "contrast":
        return sc
    if CAM_R28:
        xr, xi = _camera(sc)
    if ENV_R28:
        _env_strip(sc)
    if CAM_R28:                 # 「收集镜」 leader on the upper bowl face (the R22 'coll' point now projects onto the plasma)
        import b115_r21 as B0
        import src_r24 as S24
        rr, aa = 0.52, math.radians(float(_E.get("B128_LA", "115")))
        S24._anchor_merge("B1_15", {"coll28": Vector((B0.fx(rr), rr * math.cos(aa), rr * math.sin(aa)))})
    from bpy_extras.object_utils import world_to_camera_view as w2c
    import b115_r21 as B
    import b115_r22_build as BB
    xr, xi0 = B.fx(B.R), BB.image_x()
    xi = xr + float(_E.get("S25_IFF", "0.62")) * (xi0 - xr)
    W, H = sc.render.resolution_x, sc.render.resolution_y

    def px(p):
        v = w2c(sc, sc.camera, Vector(p))
        return round(v.x * W), round((1 - v.y) * H)
    for f in (9, 20, 31):
        sc.frame_set(f)
        rim = [px((xr, B.R * math.cos(t), B.R * math.sin(t))) for t in [i * math.pi / 36 for i in range(72)]]
        ar = 0.5 * abs(sum(rim[i][0] * rim[i - 1][1] - rim[i - 1][0] * rim[i][1] for i in range(72)))
        print(f"B115PROJ28 f{f} IF {px((xi, 0, 0))} plasma {px(tuple(B.PC))} vertex {px((B.VX, 0, 0))} "
              f"rim x {min(p[0] for p in rim)}..{max(p[0] for p in rim)} y {min(p[1] for p in rim)}..{max(p[1] for p in rim)} "
              f"rim area {ar / (W * H):.1%} cam {tuple(round(v, 2) for v in sc.camera.matrix_world.translation)}",
              flush=True)
    sc.frame_set(1)
    return sc
