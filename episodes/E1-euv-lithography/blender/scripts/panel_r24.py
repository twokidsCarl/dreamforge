"""Round 24 hook (owned by the 'panel' sub-agent; shots in r2_plates.R24_PANEL + r2_misc.R24_PANEL). Stub = R23 pixels (A0_03: R22 pixels).
pre(variant, shot, mod) runs at the START of the scene module's build() (after the R22 / R23 hooks' pre),
post(sc, variant, shot) at the END (after the R22 / R23 hooks' post). Dispatch on shot.

A0_06 (R24_ROOT_CAUSE row 3; R23 review「55 % 帧的连线是贯穿球体的直弦…所有连线改成贴着球面的大圆弧，抬高 3–5 %，末端落点加小圆点」):
  every trunk route (TrunkR18_*) is re-shaped in place as a great-circle arc on the globe whose mid-point is lifted
  3-5 % of the globe radius (was 0.4-1.5 % -> read as a flat chord), sampled densely so it bends visibly; a small
  landing dot appears on the NL ring the moment each arc arrives (origin nodes TrunkNodeR18_* already exist).
  The 5100-point supplier web, counter, NL ring, camera, timing are untouched.
A0_03 (row 1): no change -> R22 pixels (floor). See r24smoke/panel/SMOKE.md.
"""
import math

_MOD = {}


def pre(variant, shot, mod):
    _MOD[shot] = mod


def post(sc, variant, shot):
    if shot == "A0_06":
        _a006(sc, _MOD.get(shot))


A006_CAM_MID = (-10.0, 66.0)   # None -> R23 camera keys untouched
A006_CAM_DIST = 11.5           # R19 mid key 9.4 (pulled back so the globe top / NL tag stay clear)
A006_TGT_Z = 0.3               # R19 mid key aim (0, 0, 0.55)


def _a006_cam(sc, mod):
    """Middle camera key (f = 0.45 n, R19 view over lon 0 / lat 47) moved north-west to lon -10 / lat 66 (same 9.4
    distance, same target): sketch -> the NL->USA great circles all lie in ~one plane that passes within sin 0.10 of the
    old view direction (=> drawn as straight lines whatever the lift); from (-10, 66) the offset is 0.23-0.27, so the
    same arcs project as visible curves. The path still ends at the R19 Arctic view (25, 72)."""
    if not A006_CAM_MID or mod is None:
        return
    cam = sc.camera
    n = mod.K.nframes("A0_06")
    f = round(n * 0.45)
    cam.location = mod._ll(A006_CAM_MID[0], A006_CAM_MID[1], 1).normalized() * A006_CAM_DIST
    cam.keyframe_insert("location", frame=f)
    import bpy
    tgt = next((c.target for c in cam.constraints if getattr(c, "target", None)), None)
    if tgt is not None:
        tgt.location = (0, 0, A006_TGT_Z)
        tgt.keyframe_insert("location", frame=f)
    for ob in (cam, tgt):
        if ob is None:
            continue
        for fc in _fcurves(ob.animation_data):
            for k in fc.keyframe_points:
                k.interpolation = "BEZIER"
                k.easing = "EASE_IN_OUT"
            fc.update()


def _fcurves(ad):
    if not ad or not ad.action:
        return []
    try:
        return list(ad.action.fcurves)
    except AttributeError:   # Blender >= 5: layered actions
        from bpy_extras.anim_utils import action_get_channelbag_for_slot
        cb = action_get_channelbag_for_slot(ad.action, ad.action_slot)
        return list(cb.fcurves) if cb else []


def _a006(sc, mod):
    import bpy
    from mathutils import Vector
    R = 2.0
    _a006_cam(sc, mod)
    for ob in [o for o in bpy.data.objects if o.name.startswith("TrunkR18_") and o.type == "CURVE"]:
        cd = ob.data
        sp = cd.splines[0]
        a = Vector(sp.points[0].co[:3]).normalized()
        last = Vector(sp.points[len(sp.points) - 1].co[:3]).normalized()   # = point on the NL ring (t1 end)
        ang = a.angle(last)
        if ang < 1e-3:
            continue
        # lift 3 % (short hops) .. 5 % (transatlantic / Asia) of R at mid-arc, sine profile, both ends on the surface
        h = 0.030 + 0.020 * min(1.0, ang / (math.pi / 2))
        N = 160
        sp.points.add(N - len(sp.points))
        for i in range(N):
            t = i / (N - 1)
            p = a.slerp(last, t)
            sp.points[i].co = (*(p.normalized() * (R * (1.002 + h * math.sin(math.pi * t)))), 1)
        cd.bevel_depth = 0.0050
        ob.data.materials[0] = _arc_mat()
        # landing dot on the NL ring, lit when the arc's growth reaches its end
        fc = None
        fc = next((f for f in _fcurves(cd.animation_data) if f.data_path == "bevel_factor_end"), None)
        t_on = int(max(k.co[0] for k in fc.keyframe_points)) if fc else 1
        me = bpy.data.meshes.new(ob.name + "_LandR24")
        import bmesh
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=10, radius=0.0115)
        bm.to_mesh(me)
        bm.free()
        d = bpy.data.objects.new(ob.name + "_LandR24", me)
        d.location = last * (R * 1.003)
        sc.collection.objects.link(d)
        d.data.materials.append(_emit("TrunkLandR24", (0.75, 0.97, 1.0), 6.0))
        d.visible_shadow = False
        d.hide_render = True
        d.keyframe_insert("hide_render", frame=1)
        d.keyframe_insert("hide_render", frame=max(1, t_on - 1))
        d.hide_render = False
        d.keyframe_insert("hide_render", frame=t_on)


def _emit(name, col, strength):
    import bpy
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for nd in list(nt.nodes):
        nt.nodes.remove(nd)
    e = nt.nodes.new("ShaderNodeEmission")
    e.inputs[0].default_value = (*col, 1)
    e.inputs[1].default_value = strength
    o = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(e.outputs[0], o.inputs[0])
    return m


def _arc_mat():
    """Trunk arc = same cyan emission as TrunkArcR18 (K.CYAN, 3.0) but faded out where the arc runs over / behind the
    limb (view ray through the point misses the globe disc), so no arc piece floats in space."""
    import bpy
    m = bpy.data.materials.get("TrunkArcR24")
    if m:
        return m
    src = bpy.data.materials.get("TrunkArcR18")
    col, stg = (0.2, 0.85, 1.0, 1.0), 3.0
    if src and src.use_nodes:
        e0 = next((n for n in src.node_tree.nodes if n.type == "EMISSION"), None)
        if e0:
            col, stg = tuple(e0.inputs[0].default_value), e0.inputs[1].default_value
    m = bpy.data.materials.new("TrunkArcR24")
    m.use_nodes = True
    nt = m.node_tree
    for nd in list(nt.nodes):
        nt.nodes.remove(nd)
    # mask = 1 where the view ray through the arc point still hits the globe disc (d < R), 0 where the arc piece would
    # hang beyond the limb in space: d^2 = |P|^2 - (P.v)^2 (globe centred at the origin, v = unit vector to the viewer)
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    pp = nt.nodes.new("ShaderNodeVectorMath")
    pp.operation = "DOT_PRODUCT"
    nt.links.new(geo.outputs["Position"], pp.inputs[0])
    nt.links.new(geo.outputs["Position"], pp.inputs[1])
    pv = nt.nodes.new("ShaderNodeVectorMath")
    pv.operation = "DOT_PRODUCT"
    nt.links.new(geo.outputs["Position"], pv.inputs[0])
    nt.links.new(geo.outputs["Incoming"], pv.inputs[1])
    sq = nt.nodes.new("ShaderNodeMath")
    sq.operation = "MULTIPLY"
    nt.links.new(pv.outputs["Value"], sq.inputs[0])
    nt.links.new(pv.outputs["Value"], sq.inputs[1])
    d2 = nt.nodes.new("ShaderNodeMath")
    d2.operation = "SUBTRACT"
    nt.links.new(pp.outputs["Value"], d2.inputs[0])
    nt.links.new(sq.outputs[0], d2.inputs[1])
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = (2.0 * 0.995) ** 2
    mr.inputs["From Max"].default_value = (2.0 * 1.012) ** 2
    mr.inputs["To Min"].default_value = 1.0
    mr.inputs["To Max"].default_value = 0.0
    nt.links.new(d2.outputs[0], mr.inputs["Value"])
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs[0].default_value = col
    em.inputs[1].default_value = stg
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(mr.outputs["Result"], mix.inputs[0])
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(em.outputs[0], mix.inputs[2])
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(mix.outputs[0], out.inputs[0])
    return m
