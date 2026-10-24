"""R24 chero B3_02 (R24_ROOT_CAUSE rows 3 + 5; sketch r24smoke/sketch/sketch_r24_b302.py / sk_b302_render.py).

R23 review: 「主角件太小：收集镜面约占画面 1/8…让镜面占 ≥1/4 画面；给镜面加清晰的反射（映出腔壁和光锥），亮度高于腔壁」
            「第一焦点的等离子体只是一个小青点。加一团紫色辉光」
  * collector rebuilt ON THE SAME ELLIPSOID (foci B.PLASMA / B.IF, vertex B.COLL), rim radius 0.68 -> 1.25 m (hole 0.12):
    the old dish / substrate / back plumbing are cut out of the merged meshes (vertex delete inside the collector
    region), a new polished dish + substrate shell + rim flange ring tied to the vessel wall + radial brackets are
    built around it (no uniform scaling of the mirror group: R21 floating bolts);
  * CO2 laser line through the centre hole KEPT visible (R23 hid it);
  * reflected cone rim -> IF = ONE beam_r24.chain (old volume cones deleted), visible to glossy -> mirrored in the dish;
  * plasma: violet soft glow ball (facing falloff, surface emission - no fog) around the first focus;
  * camera per sketch: az 45 deg off the dish axis, el 0.1, 50 mm, target = rim centre -> IF 35 %, 7.2 -> 6.5 m.
"""
import math

import bmesh
import bpy
from mathutils import Vector

R_RIM, R_HOLE = 1.25, 0.12
AZ, EL, LENS, TT, D0, D1 = 45.0, 0.1, 50, 0.35, 7.2, 6.5


def _ell():
    import build_cutaway_r2 as B
    PL, IF, V = Vector(B.PLASMA), Vector(B.IF), Vector(B.COLL)
    c0 = (PL + IF) / 2
    ax = (IF - PL).normalized()
    a = (V - c0).length
    cf = (IF - PL).length / 2
    b = math.sqrt(a * a - cf * cf)
    e1 = ax.cross(Vector((0, 0, 1))).normalized()
    e2 = ax.cross(e1).normalized()
    return c0, ax, a, b, e1, e2


def _pt(r, t, off=0.0):
    c0, ax, a, b, e1, e2 = _ell()
    xo = -a * math.sqrt(max(0.0, 1 - r * r / (b * b)))
    p = c0 + ax * xo + r * (math.cos(t) * e1 + math.sin(t) * e2)
    if off:
        # outward normal of the ellipsoid (away from the inside) -> offset behind the face
        q = p - c0
        lx = q.dot(ax)
        rad = q - ax * lx
        nrm = (ax * (lx / (a * a)) + rad / (b * b)).normalized()
        p = p + nrm * off
    return p


def rim_centre(R=R_RIM):
    c0, ax, a, b, e1, e2 = _ell()
    return c0 + ax * (-a * math.sqrt(1 - R * R / (b * b)))


def _dish_mesh(name, r0, r1, off, mat, nr=28, nt=128):
    bm = bmesh.new()
    rows = []
    for i in range(nr + 1):
        r = r0 + (r1 - r0) * i / nr
        rows.append([bm.verts.new(_pt(r, 2 * math.pi * j / nt, off)) for j in range(nt)])
    for i in range(nr):
        for j in range(nt):
            bm.faces.new((rows[i][j], rows[i][(j + 1) % nt], rows[i + 1][(j + 1) % nt], rows[i + 1][j]))
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    me.materials.append(mat)
    return ob


def _cut_region(ob, test):
    if ob is None or ob.type != "MESH":
        return 0
    mw = ob.matrix_world
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    dv = [v for v in bm.verts if test(mw @ v.co)]
    bmesh.ops.delete(bm, geom=dv, context="VERTS")
    bm.to_mesh(ob.data)
    bm.free()
    return len(dv)


def _metal(name, col, rough):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (*col, 1)
    b.inputs["Metallic"].default_value = 1.0
    b.inputs["Roughness"].default_value = rough
    return m


def _glow_mat(name, col, strength):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    lw = nt.nodes.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.5
    inv = nt.nodes.new("ShaderNodeMath")
    inv.operation = "SUBTRACT"
    inv.inputs[0].default_value = 1.0
    nt.links.new(lw.outputs["Facing"], inv.inputs[1])
    pw = nt.nodes.new("ShaderNodeMath")
    pw.operation = "POWER"
    nt.links.new(inv.outputs[0], pw.inputs[0])
    pw.inputs[1].default_value = 2.5
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*col, 1)
    em.inputs["Strength"].default_value = strength
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mx = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(pw.outputs[0], mx.inputs["Fac"])
    nt.links.new(tr.outputs[0], mx.inputs[1])
    nt.links.new(em.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs[0])
    return m


def post(sc):
    import build_cutaway_r2 as B
    import kit_r2 as K
    import beam_r24 as BR
    from cut_hero_r21 import _cam_tgt
    n = sc.frame_end
    c0, ax, a, b, e1, e2 = _ell()
    PL, IF = Vector(B.PLASMA), Vector(B.IF)
    RC = rim_centre()

    # ---- cut the old collector (dish, substrate, rim ring, back plumbing) out of the merged meshes
    def in_coll(p):
        q = p - c0
        lx = q.dot(ax)
        rr = (q - ax * lx).length
        return (lx < (RC - c0).dot(ax) + 0.05) and lx > -a - 0.45 and rr < 0.86
    cut = {nm: _cut_region(bpy.data.objects.get(nm), in_coll)
           for nm in ("R2_mirror", "R2_substrate", "R2_gold", "R2_copper", "R2_flange", "R2_flange_s", "R2_steel",
                     "R2_bolt", "R2_anod", "R2_mount")}     # 8-spp try 1: the old 0.7 m rim ring floated inside the dish
    print("[r24h b302] cut verts", cut)

    # ---- new dish on the same ellipsoid + substrate shell + rim flange + brackets
    dm = bpy.data.materials.get("CollectorDarkML_R20")
    dish_mat = _metal("CollectorR24", (0.86, 0.87, 0.9), 0.05)
    _dish_mesh("CollectorDishR24", R_HOLE, R_RIM, 0.0, dish_mat)
    sub_mat = bpy.data.materials.get("CollectorBlankR15") or _metal("CollSubR24", (0.3, 0.31, 0.33), 0.35)
    _dish_mesh("CollectorSubR24", R_HOLE + 0.02, R_RIM + 0.05, 0.07, sub_mat, nr=16, nt=96)
    # rim edge band (dish -> substrate) and hole wall
    alu = bpy.data.materials.get("Alu") or _metal("AluR24", (0.7, 0.71, 0.74), 0.3)
    steel = bpy.data.materials.get("Steel") or _metal("SteelR24", (0.5, 0.5, 0.52), 0.3)
    mb = K.MB()
    rot = ax.to_track_quat("Z", "Y").to_euler()
    mb.ring(tuple(RC - ax * 0.035), R_RIM + 0.17, R_RIM + 0.01, 0.07, rot=tuple(rot), seg=128)
    ring_o = mb.obj("CollectorRimR24", alu)
    # vessel wall radius around the collector (from the vessel mesh) -> radial brackets rim flange -> wall
    ves = bpy.data.objects.get("R2_vessel")
    rw = 1.36
    if ves is not None:
        rs = []
        mw = ves.matrix_world
        for v in ves.data.vertices:
            p = mw @ v.co
            q = p - RC
            if abs(q.dot(ax)) < 0.15:
                rs.append((q - ax * q.dot(ax)).length)
        if rs:
            rs.sort()
            rw = rs[len(rs) // 2]
    mb2 = K.MB()
    for k in range(8):
        t = 2 * math.pi * (k + 0.5) / 8
        d = math.cos(t) * e1 + math.sin(t) * e2
        r_in, r_out = R_RIM + 0.15, max(rw - 0.02, R_RIM + 0.2)
        c = RC - ax * 0.035
        mb2.tube(tuple(c + d * r_in), tuple(c + d * r_out), 0.035, seg=12)
    mb2.obj("CollectorBracketR24", steel)
    # bolt circle on the rim flange
    mb3 = K.MB()
    for k in range(36):
        t = 2 * math.pi * k / 36
        d = math.cos(t) * e1 + math.sin(t) * e2
        c = RC + ax * 0.005 + d * (R_RIM + 0.09)
        mb3.cyl(tuple(c), 0.014, 0.025, rot=tuple(rot), seg=10)
    mb3.obj("CollectorBoltsR24", steel)
    print(f"[r24h b302] rim centre {tuple(round(x, 3) for x in RC)} vessel r {rw:.2f}")

    # ---- laser kept (R23 hid it)
    for nm in ("LaserCore", "LaserHalo"):
        ob = bpy.data.objects.get(nm)
        if ob is not None:
            ob.animation_data_clear()
            ob.hide_render = False
            ob.hide_viewport = False

    # ---- ONE cone rim -> IF (old volume cones out)
    for ob in list(bpy.data.objects):
        if ob.name.startswith("CollectCone"):
            bpy.data.objects.remove(ob)
    ch = BR.chain("CollectBeamR24", [(RC + ax * 0.02, None), (IF, None)], [R_RIM * 0.92, 0.02],
                  strength=1.7, alpha=0.32)   # try 1 (2.6 / 0.45) washed the dish face violet

    # ---- plasma glow (violet, surface falloff ball)
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=48, v_segments=24, radius=0.24)
    me = bpy.data.meshes.new("PlasmaGlowR24")
    bm.to_mesh(me)
    bm.free()
    gl = bpy.data.objects.new("PlasmaGlowR24", me)
    sc.collection.objects.link(gl)
    gl.location = PL
    gl.data.materials.append(_glow_mat("PlasmaGlowR24M", (0.5, 0.22, 1.0), 3.5))  # try 2: 9.0 clipped to a white ball
    for p in gl.data.polygons:
        p.use_smooth = True

    # ---- camera (sketch pose)
    cam, tgt = _cam_tgt(sc)
    cam.animation_data_clear()
    if tgt is not None:
        tgt.animation_data_clear()
    cam.data.lens = LENS
    th = math.radians(AZ)
    dv = Vector((math.cos(th), -math.sin(th), EL)).normalized()
    T = RC.lerp(IF, TT)
    f85 = round(n * 0.85)
    K.key_path(cam, tgt, [(1, tuple(RC + dv * D0), tuple(T)),
                          (f85, tuple(RC + dv * D1), tuple(T)),
                          (n, tuple(RC + dv * (D1 - 0.03)), tuple(T))])
    cam.data.dof.aperture_fstop = 11.0

    # ---- measurements + BEAMCHECK at 960x540
    from bpy_extras.object_utils import world_to_camera_view as w2c
    rx = (sc.render.resolution_x, sc.render.resolution_y)
    sc.render.resolution_x, sc.render.resolution_y = 960, 540
    fc = sc.frame_current
    for f in (30, 67, 103):
        sc.frame_set(f)
        P = []
        for k in range(64):
            q = w2c(sc, cam, _pt(R_RIM, 2 * math.pi * k / 64))
            P.append((q.x * 960, (1 - q.y) * 540))
        ar = 0.0
        for i in range(64):
            x1, y1 = P[i]
            x2, y2 = P[(i + 1) % 64]
            ar += x1 * y2 - x2 * y1
        ar = abs(ar) / 2 / (960 * 540)
        qi, qp = w2c(sc, cam, IF), w2c(sc, cam, PL)
        xs, ys = [p[0] for p in P], [p[1] for p in P]
        print(f"[r24h] B3_02 f{f} rim area {ar:.3f} bbox x {min(xs):.0f}..{max(xs):.0f} y {min(ys):.0f}..{max(ys):.0f}"
              f" IF ({qi.x * 960:.0f},{(1 - qi.y) * 540:.0f}) PL ({qp.x * 960:.0f},{(1 - qp.y) * 540:.0f})", flush=True)
    BR.check(sc, ch, (30, 67, 103), exits=(1,), tag="B3_02")
    sc.render.resolution_x, sc.render.resolution_y = rx
    sc.frame_set(fc)
