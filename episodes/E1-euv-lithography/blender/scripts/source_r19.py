"""Round 19 (P1) helper for r2_source - R19 root cause #5 (drive laser as a converging cone).

R18 review A0_01 #3: "预脉冲激光是一团糊的橙色圆柱。改成锥形会聚：边缘软，焦点落在锡滴上，打中的瞬间有落点高光";
B1_10 #1: "激光是等宽、实心的发光管，像一根「光柱」。改成锥形会聚，加软边，在锡滴上做出落点".

laser_cone_r19: a volume-only orange cone along an arbitrary segment start -> focus. Its radius shrinks linearly from
r0 (wide, out of the collector side) to r1 (a small waist ON the tin); the emission falls off smoothly from the axis to
the cone surface (soft edge, no hard tube surface) and rises toward the focus (same power through a smaller section),
so the beam reads as light gathering into a point on the droplet. impact_r19: a small white-hot landing glint at the
focus (+ soft orange halo), camera-only, shown only around the hit.
No tin material parameter is touched (R14 / R15 failed that way); R18's tin environment reflections stay as they are.
"""
import bpy
from mathutils import Vector

import kit_r2 as K


def _cone_material(name, start, end, r0, r1, peak, gain, color):
    m = bpy.data.materials.new(name + "Mat")
    m.use_nodes = True
    nt = m.node_tree
    for nd in list(nt.nodes):
        if nd.type != "OUTPUT_MATERIAL":
            nt.nodes.remove(nd)
    out = next(nd for nd in nt.nodes if nd.type == "OUTPUT_MATERIAL")
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    nt.links.new(tr.outputs[0], out.inputs["Surface"])
    ve = nt.nodes.new("ShaderNodeEmission")
    ve.inputs["Color"].default_value = (*K.lin(color), 1)
    s, e = Vector(start), Vector(end)
    L = (e - s).length
    u = (e - s) / L
    geo = nt.nodes.new("ShaderNodeNewGeometry")

    def vm(op, a, b=None, val=None):
        nd = nt.nodes.new("ShaderNodeVectorMath")
        nd.operation = op
        nt.links.new(a, nd.inputs[0])
        if b is not None:
            nt.links.new(b, nd.inputs[1])
        elif val is not None:
            nd.inputs[1].default_value = val
        return nd

    def mm(op, a, b=None, val=None):
        nd = nt.nodes.new("ShaderNodeMath")
        nd.operation = op
        nt.links.new(a, nd.inputs[0])
        if b is not None:
            nt.links.new(b, nd.inputs[1])
        elif val is not None:
            nd.inputs[1].default_value = val
        return nd.outputs[0]

    rel = vm("SUBTRACT", geo.outputs["Position"], val=tuple(s))
    t = vm("DOT_PRODUCT", rel.outputs[0], val=tuple(u)).outputs["Value"]          # distance along the beam
    sc = nt.nodes.new("ShaderNodeVectorMath")
    sc.operation = "SCALE"
    sc.inputs[0].default_value = tuple(u)
    nt.links.new(t, sc.inputs["Scale"])
    perp = vm("SUBTRACT", rel.outputs[0], sc.outputs[0])
    d = vm("LENGTH", perp.outputs[0]).outputs["Value"]                           # distance from the axis
    rad = nt.nodes.new("ShaderNodeMapRange")                                     # cone radius at t
    rad.clamp = True
    rad.inputs["From Min"].default_value = 0.0
    rad.inputs["From Max"].default_value = L
    rad.inputs["To Min"].default_value = r0
    rad.inputs["To Max"].default_value = r1
    nt.links.new(t, rad.inputs["Value"])
    q = mm("DIVIDE", d, rad.outputs["Result"])
    fall = nt.nodes.new("ShaderNodeMapRange")                                    # soft edge: 1 on axis -> 0 at edge
    fall.interpolation_type = "SMOOTHERSTEP"
    fall.inputs["From Min"].default_value = 0.0
    fall.inputs["From Max"].default_value = 1.0
    fall.inputs["To Min"].default_value = 1.0
    fall.inputs["To Max"].default_value = 0.0
    nt.links.new(q, fall.inputs["Value"])
    soft = mm("POWER", fall.outputs["Result"], val=1.6)
    # brighter toward the focus: (r1 / r)^gain, capped
    dvn = nt.nodes.new("ShaderNodeMath")
    dvn.operation = "DIVIDE"
    dvn.inputs[0].default_value = r1
    nt.links.new(rad.outputs["Result"], dvn.inputs[1])
    ratio = dvn.outputs[0]
    boost = mm("POWER", ratio, val=gain)
    # fade in over the first 15 % (the beam enters the frame softly, no flat cap)
    fin = nt.nodes.new("ShaderNodeMapRange")
    fin.inputs["From Min"].default_value = 0.0
    fin.inputs["From Max"].default_value = 0.15 * L
    fin.inputs["To Min"].default_value = 0.0
    fin.inputs["To Max"].default_value = 1.0
    nt.links.new(t, fin.inputs["Value"])
    st = mm("MULTIPLY", mm("MULTIPLY", soft, boost), fin.outputs["Result"])
    st = mm("MULTIPLY", st, val=peak)
    nt.links.new(st, ve.inputs["Strength"])
    nt.links.new(ve.outputs[0], out.inputs["Volume"])
    return m


def laser_cone_r19(start, focus, r0, r1, name="LaserConeR19", peak=2.2, gain=0.6, color=None):
    """Converging soft-edged orange cone start -> focus (waist r1 on the target). Returns the object."""
    m = _cone_material(name, start, focus, r0, r1, peak, gain, color or K.ORANGE)
    mb = K.MB()
    mb.tube(tuple(start), tuple(focus), r0 * 1.02, seg=48, r2=max(r1 * 1.5, 0.0008))
    ob = mb.obj(name, m)
    for attr in ("visible_diffuse", "visible_glossy", "visible_transmission", "visible_volume_scatter",
                 "visible_shadow"):
        setattr(ob, attr, False)
    return ob


def impact_r19(c, r, name="ImpactR19", core_strength=40.0, halo_strength=6.0):
    """Landing glint at the focus: a tiny white-hot core + a soft orange halo (emission volumes, camera-only)."""
    import r2_source as S
    core = S.single(name + "Core", S.vol_glow_soft(name + "CoreM", (1.0, 0.92, 0.8), core_strength, r * 0.45,
                                                    centre=tuple(c)),
                    lambda mb: mb.sphere(tuple(c), r * 0.45, 20))
    halo = S.single(name + "Halo", S.vol_glow_soft(name + "HaloM", K.ORANGE, halo_strength, r, centre=tuple(c)),
                    lambda mb: mb.sphere(tuple(c), r, 24))
    S.camera_only(core, halo)
    return [core, halo]


# ---------------------------------------------------------------- R19 root cause #3: chamber wall de-duplication
def _place(T, P, ang_deg, rad):
    """Move a scratch wall batch (plate front at local y = 0, parts toward -Y, x along, z up) onto the inside of the
    vertical vessel cylinder at angle ang_deg, plate front at radius rad, parts facing the axis."""
    import math
    import hero_kit_r11 as H11
    from mathutils import Matrix
    a = math.radians(ang_deg)
    o = Vector((math.cos(a), math.sin(a), 0))              # local +Y -> outward
    t = Vector((math.sin(a), -math.cos(a), 0))             # local +X -> tangent (right-handed with Z)
    R = Matrix(((t.x, o.x, 0, o.x * rad), (t.y, o.y, 0, o.y * rad), (0, 0, 1, 0), (0, 0, 0, 1)))
    for mb in T.values():
        for v in mb.bm.verts:
            v.co = R @ v.co
        mb.bm.normal_update()
    H11._merge(P, T)


def wall_dedup_r19(M, segments, seed=19, hide=("ChamberRings", "ChamberBolts", "WallLines", "MLI"), keep=(),
                   tag="SrcWallR19", viewports=(), log=None):
    """Replace the repeated rib / ring grid of r2_source.chamber() with a few big named assemblies (shared read-only
    kit_r19.wall_r19 - valve island / drag chain / coolant manifold / gas panel / ion pump / power box + a diagonal
    coolant run) on the wall segments the camera sees, plus lit viewports. segments: (angle_deg, width, z0, z1,
    radius, n_blocks). keep: world-space keep-clear spheres ((x, y, z), r). Fill lights are not touched."""
    import math
    import bpy
    import hero_kit_r10 as H
    import kit_r19 as KR
    for nm in hide:
        ob = bpy.data.objects.get(nm)
        if ob is not None:
            ob.hide_render = True
    P = H.new_parts()
    kinds = []
    for i, (ang, w, z0, z1, rad, nb) in enumerate(segments):
        a = math.radians(ang)
        o = Vector((math.cos(a), math.sin(a), 0))
        t = Vector((math.sin(a), -math.cos(a), 0))
        # world keep spheres -> local wall frame (x along t, y along o measured from the plate, z)
        kl = [((Vector(c) - o * rad).dot(t), (Vector(c) - o * rad).dot(o), Vector(c).z) for c, r in keep]
        kl = [(p, r) for p, (c, r) in zip(kl, keep)]
        T = H.new_parts()
        kinds += KR.wall_r19(T, -w / 2, w / 2, z0, z1, 0.0, seed=seed + 7 * i, keep=kl, n=nb, log=log)
        _place(T, P, ang, rad)
    for c, nrm, r in viewports:
        H.flange_viewport(P, c, nrm, r, nipple=r * 0.9, side_port=False)
    out = H.finish(P, M, tag)
    return kinds, out


def pump_port_r19(M, ang_deg, z, rad=1.27, r=0.22, tag="PumpPortR19"):
    """A turbo-pump inlet in the vessel wall: big flange + bolt circle, splinter-guard spokes, dark bore."""
    import math
    import r2_source as S
    a = math.radians(ang_deg)
    n = Vector((-math.cos(a), -math.sin(a), 0))
    c = -n * rad + Vector((0, 0, z))
    q = Vector((0, 0, 1)).rotation_difference(n).to_euler()
    from mathutils import Matrix
    pf, pb, bo = K.MB(), K.MB(), K.MB()
    pf.ring(c + n * 0.03, r * 1.5, r, 0.06, rot=q, seg=64)
    pb.bolts(c + n * 0.065, r * 1.27, 16, 0.01, 0.016, rot=q)
    pf.ring(c + n * 0.045, r * 1.01, r * 0.94, 0.012, rot=q, seg=64)
    for k in range(6):
        t = math.pi * k / 6
        pf.box(c + n * 0.045, (2 * r * abs(math.cos(t)) + 0.006, 2 * r * abs(math.sin(t)) + 0.006, 0.006),
               rot=(q.to_matrix() @ Matrix.Rotation(t, 3, "Z")).to_euler())
    bo.cyl(c - n * 0.01, r, 0.01, rot=q, seg=48)
    return [pf.obj(tag + "Flange", M["alu"], bevel=0.003), pb.obj(tag + "Bolts", M["steel"]),
            bo.obj(tag + "Bore", M["hole"])]
