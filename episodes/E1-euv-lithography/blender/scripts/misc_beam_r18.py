"""Round 18 (P1) helpers for blender/shots/r2_misc.py only (R18_ROOT_CAUSE #2 and #3). Never used by the photons
variant (B9_05 gold control); shared beam_r12/16/17, misc_beam_r17, misc_kit_r16 untouched (cut's beam_r18 not imported).

#2  vol_cone   - k4A-style volumetric light cone between two surfaces: the radii at both ends follow the apertures
                 (elliptical cross-section allowed -> a flat cone converging into a slit), interior glow (inner cone),
                 soft edge (facing falloff), brighter toward the focus. Optional hook: the start ring stays pinned on a
                 fixed exit port while the end follows a moving slit (B8_17).
    disc_mirror - solid polished disc mirror face (k4A mirror cup) sitting inside an existing mount ring.
#3  supplier_points - ~5100 instanced surface points on the globe, lit in index order by an animated count
                 (geometry nodes: Instance on Points, selection = index < count).
"""
import math

import bmesh
import bpy
from mathutils import Vector

import kit_r2 as K


def _op(N, L, o, a, b):
    x = N.new("ShaderNodeMath")
    x.operation = o
    for i, s in enumerate((a, b)):
        if isinstance(s, (int, float)):
            x.inputs[i].default_value = s
        else:
            L.new(s, x.inputs[i])
    return x.outputs[0]


def cone_mat(name, color, strength, alpha=0.6, edge=1.8, fade0=0.0, fade1=0.0, gain=0.8):
    """Emission + transparency, k = (1 - facing)^edge * along(v) * (1 + gain * v); v = 0 at the start ring."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    N, L = nt.nodes, nt.links
    for n in list(N):
        if n.type != "OUTPUT_MATERIAL":
            N.remove(n)
    out = next(n for n in N if n.type == "OUTPUT_MATERIAL")
    lw = N.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.5
    k = _op(N, L, "POWER", _op(N, L, "SUBTRACT", 1.0, lw.outputs["Facing"]), edge)
    uv = N.new("ShaderNodeUVMap")
    uv.uv_map = "ConeUV"
    sp = N.new("ShaderNodeSeparateXYZ")
    L.new(uv.outputs["UV"], sp.inputs[0])
    v = sp.outputs["Y"]
    if fade0 > 0:
        k = _op(N, L, "MULTIPLY", k, _op(N, L, "MINIMUM", _op(N, L, "DIVIDE", v, fade0), 1.0))
    if fade1 > 0:
        k = _op(N, L, "MULTIPLY", k, _op(N, L, "MINIMUM", _op(N, L, "DIVIDE", _op(N, L, "SUBTRACT", 1.0, v), fade1), 1.0))
    if gain:
        k = _op(N, L, "MULTIPLY", k, _op(N, L, "ADD", 1.0, _op(N, L, "MULTIPLY", v, gain)))
    em = N.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*K.lin(color), 1)
    L.new(_op(N, L, "MULTIPLY", k, strength), em.inputs["Strength"])
    tr = N.new("ShaderNodeBsdfTransparent")
    mx = N.new("ShaderNodeMixShader")
    L.new(_op(N, L, "MINIMUM", _op(N, L, "MULTIPLY", k, alpha), 1.0), mx.inputs["Fac"])
    L.new(tr.outputs[0], mx.inputs[1])
    L.new(em.outputs[0], mx.inputs[2])
    L.new(mx.outputs[0], out.inputs["Surface"])
    return m


def _cone_mesh(name, a, b, ra, rb, xdir=None, seg=48, rings=24, hook_w=False, offsets_only=False):
    """Open tube a -> b; ra / rb = (rx, ry) semi-axes at each end (float = circle). Returns mesh + per-vertex s."""
    a, b = Vector(a), Vector(b)
    ra = (ra, ra) if isinstance(ra, (int, float)) else ra
    rb = (rb, rb) if isinstance(rb, (int, float)) else rb
    d = (b - a).normalized()
    if xdir is None:
        ex = d.orthogonal().normalized()
        ey = d.cross(ex).normalized()
    else:
        ex = Vector(xdir).normalized()
        ey = Vector((0, 0, 1)).cross(ex).normalized() if offsets_only else d.cross(ex).normalized()
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("ConeUV")
    rows, svals = [], []
    for r_ in range(rings + 1):
        s = r_ / rings
        rx = ra[0] + (rb[0] - ra[0]) * s
        ry = ra[1] + (rb[1] - ra[1]) * s
        c = Vector((0, 0, 0)) if offsets_only else a.lerp(b, s)
        row = []
        for i in range(seg):
            t = 2 * math.pi * i / seg
            row.append(bm.verts.new(c + ex * (rx * math.cos(t)) + ey * (ry * math.sin(t))))
            svals.append(s)
        rows.append(row)
    for r_ in range(rings):
        for i in range(seg):
            j = (i + 1) % seg
            f = bm.faces.new((rows[r_][i], rows[r_][j], rows[r_ + 1][j], rows[r_ + 1][i]))
            for lp, vv in zip(f.loops, (r_ / rings, r_ / rings, (r_ + 1) / rings, (r_ + 1) / rings)):
                lp[uvl].uv = (0.5, vv)
            f.smooth = True
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    return me, svals


def vol_cone(name, a, b, ra, rb, color=None, strength=4.0, alpha=0.6, edge=1.8, inner=0.45, inner_gain=1.6,
             fade0=0.0, fade1=0.0, gain=0.8, xdir=None, seg=48):
    """Volumetric cone a -> b with an inner glow cone (radius * inner). Returns [outer, inner] objects."""
    color = K.VIOLET if color is None else color
    obs = []
    for tag, sc_, st_ in (("", 1.0, strength), ("In", inner, strength * inner_gain)):
        if sc_ <= 0:
            continue
        ra_ = tuple(x * sc_ for x in ((ra, ra) if isinstance(ra, (int, float)) else ra))
        rb_ = tuple(x * sc_ for x in ((rb, rb) if isinstance(rb, (int, float)) else rb))
        me, _s = _cone_mesh(name + tag, a, b, ra_, rb_, xdir, seg)
        ob = bpy.data.objects.new(name + tag, me)
        bpy.context.scene.collection.objects.link(ob)
        me.materials.append(cone_mat(name + tag + "M", color, st_, alpha, edge, fade0, fade1, gain))
        _vis(ob)
        obs.append(ob)
    return obs


def _vis(ob):
    ob.visible_shadow = False
    try:
        ob.visible_diffuse = False
        ob.visible_glossy = False
        ob.visible_transmission = False
    except AttributeError:
        pass


def hooked_cone(name, port, ra, rb, parent, color=None, strength=4.0, alpha=0.6, edge=1.6, inner=0.45,
                inner_gain=1.6, gain=1.0, xdir=(1, 0, 0), seg=40):
    """Cone whose start ring sits on a FIXED port (world point `port`) and whose end ring follows `parent` (the
    moving slit; mesh origin = parent origin). Each ring at s is offset(s) in the parent frame, pulled toward the
    port by a hook with weight (1 - s): world = (1 - s) * port + s * slit + offset(s)."""
    color = K.VIOLET if color is None else color
    emp = bpy.data.objects.new(name + "Port", None)
    bpy.context.scene.collection.objects.link(emp)
    emp.location = Vector(port)
    obs = []
    for tag, sc_, st_ in (("", 1.0, strength), ("In", inner, strength * inner_gain)):
        ra_ = tuple(x * sc_ for x in ra)
        rb_ = tuple(x * sc_ for x in rb)
        me, svals = _cone_mesh(name + tag, (0, 0, 1), (0, 0, 0), ra_, rb_, xdir, seg, offsets_only=True)
        ob = bpy.data.objects.new(name + tag, me)
        bpy.context.scene.collection.objects.link(ob)
        ob.parent = parent
        vg = ob.vertex_groups.new(name="port")
        for i, s in enumerate(svals):
            vg.add([i], 1.0 - s, "REPLACE")
        hk = ob.modifiers.new("PortHook", "HOOK")
        hk.object = emp
        hk.vertex_group = "port"
        hk.strength = 1.0
        me.materials.append(cone_mat(name + tag + "M", color, st_, alpha, edge, 0.0, 0.0, gain))
        _vis(ob)
        obs.append(ob)
    return obs, emp


def disc_mirror(name, p, nrm, r, mat, thick=0.05, back=0.006):
    """Solid disc mirror (front face just behind p, so a landing highlight at p + n * lift lies on it)."""
    n = Vector(nrm).normalized()
    mb = K.MB()
    mb.cyl(Vector((0, 0, 0)), r, thick, seg=64)
    ob = mb.obj(name, mat)
    q = Vector((0, 0, 1)).rotation_difference(n)
    ob.rotation_euler = q.to_euler()
    ob.location = Vector(p) - n * (back + thick / 2)
    return ob


def supplier_points(name, pts, dot_r, mat, count_keys):
    """pts: world positions in lighting order; count_keys: [(frame, count)]. Instances an ico dot on every point
    whose index < count(frame)."""
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(p) for p in pts], [], [])
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    ng = bpy.data.node_groups.new(name + "GN", "GeometryNodeTree")
    try:
        ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
        ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    except AttributeError:
        ng.inputs.new("NodeSocketGeometry", "Geometry")
        ng.outputs.new("NodeSocketGeometry", "Geometry")
    N, L = ng.nodes, ng.links
    gi = N.new("NodeGroupInput")
    go = N.new("NodeGroupOutput")
    ico = N.new("GeometryNodeMeshIcoSphere")
    ico.inputs["Radius"].default_value = dot_r
    ico.inputs["Subdivisions"].default_value = 1
    sm = N.new("GeometryNodeSetMaterial")
    sm.inputs["Material"].default_value = mat
    L.new(ico.outputs["Mesh"], sm.inputs["Geometry"])
    iop = N.new("GeometryNodeInstanceOnPoints")
    L.new(gi.outputs[0], iop.inputs["Points"])
    L.new(sm.outputs["Geometry"], iop.inputs["Instance"])
    idx = N.new("GeometryNodeInputIndex")
    val = N.new("ShaderNodeValue")
    cmp_ = N.new("FunctionNodeCompare")
    cmp_.data_type = "FLOAT"
    cmp_.operation = "LESS_THAN"
    L.new(idx.outputs[0], cmp_.inputs[0])
    L.new(val.outputs[0], cmp_.inputs[1])
    L.new(cmp_.outputs["Result"], iop.inputs["Selection"])
    rl = N.new("GeometryNodeRealizeInstances")
    L.new(iop.outputs["Instances"], rl.inputs["Geometry"])
    L.new(rl.outputs["Geometry"], go.inputs[0])
    for f, c in count_keys:
        val.outputs[0].default_value = float(c)
        val.outputs[0].keyframe_insert("default_value", frame=f)
    mod = ob.modifiers.new("Points", "NODES")
    mod.node_group = ng
    ob.visible_shadow = False
    return ob
