"""Round 32 hook (MAIN process; r2_source.R32_SRC = {"B1_15"}), layered after the R31 hooks and before beam_hook_r29.

  MIRROR_R32 (row 4, B1_15): R31 p1 「镜面被紫雾和一条白色弧形条带盖住，看不出是一面光滑的椭球镜…让镜面清楚映出法兰和喷嘴的倒影，
             用掠射高光证明它是镜子」「橙色激光从镜缘侧孔射入…激光要沿光轴从中心孔穿过来打到等离子体」「光锥也应该从整个镜口
             出发，收向 IF」; Carl t381: no visible R30 -> R31 difference. Structural, not a re-tune:
    * the violet landing disc lying over the whole mirror face (B115LandR27, r 0.67 - sketch32/probe_B1_15.txt) is
      removed, not dimmed;
    * the ray-picked mirror object CollFaceR20 gets the B2_08 accepted high-reflect material + lit wall in its
      reflection direction (src_r31 recipe, the same call);
    * the exit cone is rebuilt as ONE beam_r29 volume from the whole mouth rim to the IF tip, minus (boolean) the
      camera's view frustum through the mirror rim: it visibly leaves the rim but never covers the mirror face on
      screen (ROUND_PIPELINE「R32 起追加」; a cone started past the rim floated detached from the mirror at 8 spp);
    * the axial drive laser (DriveLaserR22, on the axis from the centre hole to the plasma) becomes a bright orange
      beam with a soft halo, so the laser visibly comes out of the centre hole along the axis.
Remove B1_15 from R32_SRC / MIRROR_R32 False -> R31 pixels.
"""
import bpy
from mathutils import Vector

MIRROR_R32 = True
JOB = (9, 20, 31)
RIM_X, RIM_R = 0.09, 0.68
LASER_R = 0.007
LASER_STRENGTH = 24.0
TIP_R = 0.012
_MOD = {}


def pre(variant, shot, mod):
    if shot == "B1_15" and MIRROR_R32:
        import src_r31
        src_r31._MOD["mod"] = mod
        _MOD["mod"] = mod


def face_frustum(sc, C, centre, axis, radius, name):
    """closed cone with its apex at camera position C through the circle (centre, axis, radius): every point inside it
    lies in front of that mirror face on screen. Shared with cut_scene_r32 (B3_02) - one model for both collectors."""
    import bmesh
    import math
    axis = Vector(axis).normalized()
    u = axis.orthogonal().normalized()
    v = axis.cross(u).normalized()
    bm = bmesh.new()
    n = 64
    near, far = [], []
    for k in range(n):
        t = 2 * math.pi * k / n
        P = Vector(centre) + (u * math.cos(t) + v * math.sin(t)) * radius
        near.append(bm.verts.new(C + (P - C) * 0.05))
        far.append(bm.verts.new(C + (P - C) * 1.6))
    for k in range(n):
        bm.faces.new((near[k], near[(k + 1) % n], far[(k + 1) % n], far[k]))
    bm.faces.new(near[::-1])
    bm.faces.new(far)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    sc.collection.objects.link(ob)
    ob.hide_render = True
    ob.display_type = "WIRE"
    return ob


def cut_by_faces(sc, ob, frames, centre, axis, radius, tag):
    """boolean the volume cone ob by one camera frustum per job frame (the camera moves)."""
    for f in frames:
        sc.frame_set(f)
        cut = face_frustum(sc, sc.camera.matrix_world.translation.copy(), centre, axis, radius, f"{tag}Frustum{f}")
        md = ob.modifiers.new(f"FaceFrustum{f}", "BOOLEAN")
        md.operation = "DIFFERENCE"
        md.solver = "EXACT"
        md.object = cut


def _cone(sc):
    import beam_r29 as B29
    legs = [o for o in bpy.data.objects if o.name.startswith("B115ExitR27Leg") and "r25_radii" in o.keys()]
    if not legs:
        print("[src_r32] B1_15: no exit legs", flush=True)
        return None
    rg = {o.name: B29._rings(o) for o in legs}
    l0 = next(o for o in legs if o.name.endswith("Leg0"))
    l1 = next((o for o in legs if o.name.endswith("Leg1")), l0)
    a = l0.matrix_world @ rg[l0.name][0][0]
    tip = l1.matrix_world @ rg[l1.name][1][0]
    for o in legs:
        o.hide_render = True
        o.hide_viewport = True
        o["r29_replaced"] = "src_r32"
    import beam_hook_r29 as H29
    orig = getattr(B29.cone, "_r30_orig", B29.cone)
    ob = orig("B115ExitR32", a, tip, RIM_R, TIP_R, None, H29.STRENGTH.get("B1_15", B29.B_DEFAULT))
    cut_by_faces(sc, ob, JOB, Vector((RIM_X, 0, 0)), Vector((1, 0, 0)), RIM_R * 1.05, "B115Face")
    print(f"[src_r32] B1_15 cone rim (r {RIM_R}) -> IF tip {tuple(round(x, 3) for x in tip)}, minus the camera frustum "
          f"through the mirror face", flush=True)
    return ob


def _laser():
    import kit_r2 as K
    las = bpy.data.objects.get("DriveLaserR22")
    if las is None:
        return 0
    bb = [las.matrix_world @ Vector(x) for x in las.bound_box]
    x0, x1 = min(b.x for b in bb), max(b.x for b in bb)
    a, b = Vector((max(x0, -0.31), 0, 0)), Vector((x1, 0, 0))
    m = bpy.data.materials.new("LaserR32M")
    m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    for n in list(N):
        if n.type != "OUTPUT_MATERIAL":
            N.remove(n)
    em = N.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (1.0, 0.36, 0.06, 1)
    em.inputs["Strength"].default_value = LASER_STRENGTH
    L.new(em.outputs[0], next(n for n in N if n.type == "OUTPUT_MATERIAL").inputs["Surface"])
    mh = bpy.data.materials.new("LaserR32HaloM")
    mh.use_nodes = True
    N, L = mh.node_tree.nodes, mh.node_tree.links
    for n in list(N):
        if n.type != "OUTPUT_MATERIAL":
            N.remove(n)
    lw = N.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.5
    inv = N.new("ShaderNodeMath")
    inv.operation = "SUBTRACT"
    inv.inputs[0].default_value = 1.0
    L.new(lw.outputs["Facing"], inv.inputs[1])
    pw = N.new("ShaderNodeMath")
    pw.operation = "POWER"
    L.new(inv.outputs[0], pw.inputs[0])
    pw.inputs[1].default_value = 2.0
    em = N.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (1.0, 0.32, 0.05, 1)
    em.inputs["Strength"].default_value = 1.2
    tr = N.new("ShaderNodeBsdfTransparent")
    mix = N.new("ShaderNodeMixShader")
    L.new(pw.outputs[0], mix.inputs[0])
    L.new(tr.outputs[0], mix.inputs[1])
    L.new(em.outputs[0], mix.inputs[2])
    L.new(mix.outputs[0], next(n for n in N if n.type == "OUTPUT_MATERIAL").inputs["Surface"])
    core, halo = K.MB(), K.MB()
    core.tube(a, b, LASER_R, seg=16)
    halo.tube(a, b, LASER_R * 2.6, seg=24)
    o1 = core.obj("B115LaserR32", m)
    o2 = halo.obj("B115LaserR32Halo", mh)
    for o in (o1, o2):
        o.visible_shadow = False
        o.visible_diffuse = False
        o.visible_glossy = True
    las.hide_render = True
    return 2


def post(sc, variant, shot):
    if not (MIRROR_R32 and shot == "B1_15"):
        return sc
    land = bpy.data.objects.get("B115LandR27")
    if land is not None:
        land.hide_render = True
    import src_r31
    src_r31.post(sc, variant, shot)          # B2_08 high-reflect mirror on CollFaceR20 + lit wall in its reflection
    ob = _cone(sc)
    n_l = _laser()
    print(f"[src_r32] B1_15 landing haze off: {land is not None}; cone {ob.name if ob else None}; laser objs {n_l}",
          flush=True)
    sc.frame_set(1)
    return sc
