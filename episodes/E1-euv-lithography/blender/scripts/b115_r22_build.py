"""Round 22 (P1) B1_15 builder (R22_ROOT_CAUSE row #2). Layers on b115_r21 (left untouched): patches its geometry
globals and replaces build_contrast / chamber.

R21 review B1_15: 「右下一条紫色实心光柱从等离子体直冲镜头」「左上还有一团紫色拖尾，来路不明」「看不出椭球碗形」
「机位往后退，让收集镜碗沿完整入框，并占画面 ≥1/3」. Screen-projection sketch: /workspace/e1work/p1/r22smoke/sketch_b115b.py.
  * plasma back ON the axis at the near focus u = 1.25 f (x = 0.075; R21 off-axis OFF removed) -> image / IF at
    v = 5 f (x = 1.20), far from the mirror, on the far side of the plasma (real collector F1 -> F2);
  * camera ELEVATED ~58 deg from the mirror axis toward +z (azimuth ~8 deg): the axis runs vertically on screen,
    the rim is a wide ellipse, whole rim in frame, push-in D 2.3 -> 1.95; camera is outside the reflected cone
    (no plasma image on the face -> nothing can overlap the laser);
  * outgoing light = the REFLECTED converging cone rim -> IF: volume only from ~0.3 m in front of the rim plane
    (axial fade-in), exits the bottom edge toward the off-frame IF; never from the plasma, never at the camera;
  * vessel wall / front plate cut over the camera's sector (the camera is above the vessel); droplet line runs
    across the mouth (horizontal on screen) instead of vertical toward the camera.
"""
import math
import os

import bpy
from mathutils import Vector

import kit_r2 as K
import b115_r21 as B

_E = os.environ
U = float(_E.get("B122_U", "1.25"))                 # plasma distance from the vertex in focal lengths
TH = math.radians(float(_E.get("B122_TH", "58")))   # camera elevation from the mirror axis
AZ = math.radians(float(_E.get("B122_AZ", "8")))
D0 = float(_E.get("B122_D0", "2.3"))
D1 = float(_E.get("B122_D1", "1.95"))
LOOK0 = Vector((0.10, 0, 0))
LOOK1 = Vector((0.12, 0, 0))
CONE_E = float(_E.get("B122_CE", "2.0"))
CONE_X0 = float(_E.get("B122_CX0", "0.15"))         # cone volume starts this far in front of the rim plane
PR = float(_E.get("B122_PR", "0.034"))
WALL_A1 = float(_E.get("B122_WA1", "118"))          # vessel wall kept over b -25..WALL_A1 (camera sector cut)


def _patch():
    B.PX = B.VX + U * B.F
    B.OFF = Vector((0, 0, 0))
    B.PC = Vector((B.PX, 0, 0))
    B.chamber = chamber


def image_x():
    u = B.PX - B.VX
    return B.VX + 1.0 / (1.0 / B.F - 1.0 / u)


def chamber(M):
    """b115_r21.chamber with the wall / front plate / ports cut over the camera's (top) sector."""
    import hero_kit_r10 as H
    B.mats(M)
    w = K.MB()
    a1 = WALL_A1
    w.shell((0.05, 0, 0), B.VES_R, B.VES_R + 0.07, 2.3, -25, a1, rot=B.ROT_X, seg=160)
    w.cyl((-1.12, 0, 0), B.VES_R + 0.07, 0.07, rot=B.ROT_X, seg=128)
    for x in (-0.55, 0.65):
        w.shell((x, 0, 0), B.VES_R - 0.05, B.VES_R, 0.05, -25, a1, rot=B.ROT_X, seg=160)
    P = H.new_parts()
    wins = K.MB()
    ports = ((0.35, 35, 0.11, True), (-0.35, 100, 0.09, False), (0.0, 80, 0.07, False),
             (-0.6, 30, 0.07, False), (0.7, 100, 0.12, True), (-0.2, 10, 0.08, False))
    for x, bdeg, r, window in ports:
        b = math.radians(bdeg)
        p = Vector((x, B.VES_R * math.sin(b), -B.VES_R * math.cos(b)))
        n = (Vector((0, 0, 0)) - p).normalized()
        H.flange_viewport(P, p, n, r, nipple=r * 1.0, side_port=(bdeg % 3 == 0))
        if window:
            f1 = p + n * r * 1.0
            H._cyl(wins, f1 + n * r * 0.33, n, r * 0.6, r * 0.03, seg=40)
    for y, z, r in ((0.75, -0.75, 0.09), (-0.9, -0.55, 0.07)):
        p = Vector((-1.08, y, z))
        H.flange_viewport(P, p, (1, 0, 0), r, nipple=r * 0.8, side_port=False)
    objs = [w.obj("VesselWallR20", M["b19_wall"], bevel=0.004)]
    wo = wins.obj("ViewportLightsR20", M["b19_window"])
    wo.visible_diffuse = False
    objs.append(wo)
    return objs, P


def cone_r22(S, name, a, b, r0, r1, color, peak, fade_len):
    """Soft converging volume cone a -> b (radial smoothstep falloff as b115_r21.soft_cone) x an axial fade-in over
    the first fade_len (no hard start disc)."""
    ob = B.soft_cone(S, name, a, b, r0, r1, color, peak)
    nt = ob.active_material.node_tree
    ve = next(nd for nd in nt.nodes if nd.type == "EMISSION")
    fall = ve.inputs["Strength"].links[0].from_node
    sp = next(nd for nd in nt.nodes if nd.bl_idname == "ShaderNodeSeparateXYZ")
    ax = nt.nodes.new("ShaderNodeMapRange")
    ax.interpolation_type = "SMOOTHSTEP"
    ax.inputs["From Min"].default_value = 0.0
    ax.inputs["From Max"].default_value = fade_len
    ax.inputs["To Min"].default_value = 0.0
    ax.inputs["To Max"].default_value = 1.0
    nt.links.new(sp.outputs["X"], ax.inputs["Value"])
    mul = nt.nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    nt.links.new(fall.outputs["Result"], mul.inputs[0])
    nt.links.new(ax.outputs["Result"], mul.inputs[1])
    nt.links.new(mul.outputs[0], ve.inputs["Strength"])
    return ob


def build_contrast(sc, M, cam, tgt, n, S):
    import hero_kit_r10 as H
    import common as C
    _patch()
    PC = B.PC
    C.set_world(top=(0.03, 0.034, 0.05), horizon=(0.018, 0.02, 0.032), bottom=(0.008, 0.009, 0.014))
    S._metals_r15(M, coll_rough=0.035)
    B.collector(M)
    objs, P = chamber(M)
    for ob in objs:
        if ob.name.startswith("ViewportLights"):
            ob.visible_glossy = False
    B.h2_nozzles(M, P, H)
    dax = Vector((-0.35, -1.0, 0)).normalized()      # droplet flight: across the mouth, in front of the rim
    H.droplet_generator(P, tuple(PC - dax * 0.26), tuple(dax), s=1.0, flange_at=0.3)
    H.finish(P, M, "B115KitR22")
    cat = K.MB()
    cat.tube(tuple(PC + dax * 1.3), tuple(PC + dax * 0.52), 0.05, seg=32)
    cat.tube(tuple(PC + dax * 0.52), tuple(PC + dax * 0.45), 0.05, seg=32, r2=0.09)
    cat.obj("B115CatcherR22", M["steel"], bevel=0.002)
    pl, li = S.plasma_r10(M, tuple(PC), PR, energy=0.0, gas=float(_E.get("B122_GAS", "0.7")),
                          li_color=(0.74, 0.6, 1.0), mirror_core=True)
    for i, ob in enumerate(pl):
        ob.visible_glossy = i <= 2
    E = float(_E.get("B122_E", "700"))
    S.key_energy(li, [(1, E), (n, E * 1.12)])
    h0 = Vector((B.fx(B.HOLE) - B.SHELL - 0.12, 0, 0))
    B.soft_cone(S, "DriveLaserR22", h0, PC - Vector((0.006, 0, 0)), B.HOLE * 0.55, 0.008, K.ORANGE, 6.0)
    # reflected converging cone rim -> IF (x_if = 1.20): volume from CONE_X0 in front of the rim plane
    xr, xi = B.fx(B.R), image_x()
    xa = xr + CONE_X0
    ra = B.R * (xi - xa) / (xi - xr)
    cone_r22(S, "IFConeR22", (xa, 0, 0), (xi, 0, 0), ra, 0.012, K.VIOLET, CONE_E, 0.25)
    for ob in B.debris(M):
        S.key_scale(ob, [(1, 0.6), (n, 1.15)], interp="LINEAR")
    rr, aa = 0.45, math.radians(float(_E.get("B122_LA", "-20")))
    face_pt = Vector((B.fx(rr), rr * math.cos(aa), rr * math.sin(aa)))
    K.anchors("B1_15", {"coll": face_pt, "plasma": PC, "hole": Vector((B.fx(B.HOLE), 0, 0)), "r21": PC,
                        "r22": PC, "cone": Vector((xa + 0.2, 0, 0))})
    cam.data.lens = 32
    cam.data.dof.use_dof = True
    cam.data.dof.aperture_fstop = 5.6
    foc = bpy.data.objects.new("FocusR22", None)
    sc.collection.objects.link(foc)
    cam.data.dof.focus_object = foc
    S.key_loc(foc, [(1, tuple(PC)), (n, tuple(PC))], interp="BEZIER")
    dirc = Vector((math.cos(TH), math.sin(AZ) * math.sin(TH), math.cos(AZ) * math.sin(TH))).normalized()
    K.key_path(cam, tgt, [(1, tuple(LOOK0 + dirc * D0), tuple(LOOK0)), (n, tuple(LOOK1 + dirc * D1), tuple(LOOK1))],
               interp="BEZIER")
    for c_ in cam.constraints:       # screen-up = world -X (the optical axis runs vertically on screen)
        c_.mute = True
    import mathutils
    cam.rotation_mode = "QUATERNION"
    # orientation constant over the push (pure dolly along dirc): -Z -> -dirc, +Y -> world -X projected
    fwd = -dirc
    up = Vector((-1, 0, 0))
    up = (up - fwd * up.dot(fwd)).normalized()
    right = fwd.cross(up)
    m = mathutils.Matrix((right, up, -fwd)).transposed()
    cam.rotation_quaternion = m.to_quaternion()

    def post(sc_):
        for nm, lo, en, co in (("Key", (1.9, -1.5, 1.1), 420.0, (0.95, 0.96, 1.0)),
                               ("Top", (0.7, -0.6, 1.25), 160.0, (0.9, 0.93, 1.0)),
                               ("Side", (1.5, -0.4, -0.9), 140.0, (0.8, 0.85, 1.0)),
                               ("Wall", (0.6, 0.6, 0.9), 90.0, (0.7, 0.76, 1.0)),
                               ("Low", (0.4, 0.5, -0.9), 60.0, (0.65, 0.72, 1.0)),
                               ("Front", (0.85, 1.05, -0.85), 45.0, (0.85, 0.88, 1.0))):
            K.point("B115FillR22%s" % nm, lo, en, co, 0.4)
        recv = bpy.data.collections.new("B115FillRecvR22")
        for ob in bpy.data.objects:
            if ob.type == "MESH" and ob.name != "CollFaceR20":
                recv.objects.link(ob)
        for ob in bpy.data.objects:
            if ob.type == "LIGHT" and ob.name != "PlasmaLight":
                ob.light_linking.receiver_collection = recv
    return post
