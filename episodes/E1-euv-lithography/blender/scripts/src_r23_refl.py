"""Round 23 (P1) helpers for the srca hook src_r23.py (R23_ROOT_CAUSE row 5: collector face reads black / matte).

reflection_sheet(): a glossy-only emitter (camera / diffuse / shadow invisible) placed ON the mirror-reflected
camera rays of a patch of the collector face (param grid r x a), so the polished face shows a graded reflection
of a lit panel exactly on that patch. The camera moves, so the sheet is re-solved at a list of frames and stored
as shape keys with triangular cross-fade weights (smooth: the vertices slide between solutions; R22 B2_08 band
was solved at one frame only and held only there).

ribbons(): SnH4 streamlines as tapered flow ribbons (width grows along the flow, alpha fades at both ends, no
end dots) with a travelling brightness streak showing the direction (R22 review B2_08 「气流线细、末端孤立白点…
用有粗细渐变的流带」).
"""
import math

import bpy
from mathutils import Vector


def glossy_only(ob):
    for attr in ("visible_camera", "visible_diffuse", "visible_shadow", "visible_transmission",
                 "visible_volume_scatter"):
        setattr(ob, attr, False)
    ob.visible_glossy = True


def _math(nt, op, a, b=None):
    n = nt.nodes.new("ShaderNodeMath")
    n.operation = op
    for i, x in enumerate((a, b)):
        if x is None:
            continue
        if isinstance(x, (int, float)):
            n.inputs[i].default_value = x
        else:
            nt.links.new(x, n.inputs[i])
    return n.outputs[0]


def _ramp(nt, src, pts, interp=None):
    r = nt.nodes.new("ShaderNodeValToRGB")
    if interp:
        r.color_ramp.interpolation = interp
    el = r.color_ramp.elements
    while len(el) > 2:
        el.remove(el[-1])
    pts = sorted(pts)
    el[0].position, el[0].color = pts[0][0], (pts[0][1],) * 3 + (1,)
    el[1].position, el[1].color = pts[-1][0], (pts[-1][1],) * 3 + (1,)
    for p, v in pts[1:-1]:
        e = el.new(p)
        e.color = (v, v, v, 1)
    nt.links.new(src, r.inputs[0])
    return r.outputs[0]


def sheet_mat(name, color, strength, u_prof, v_prof, v_interp=None, u_interp=None):
    """emission strength = strength * ramp_u(u) * ramp_v(v) (UV u = radial param, v = angular param)."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        if n.type != "OUTPUT_MATERIAL":
            nt.nodes.remove(n)
    out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*color, 1)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sp = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["UV"], sp.inputs[0])
    ru = _ramp(nt, sp.outputs["X"], u_prof, u_interp)
    rv = _ramp(nt, sp.outputs["Y"], v_prof, v_interp)
    s = _math(nt, "MULTIPLY", ru, rv)
    s = _math(nt, "MULTIPLY", s, strength)
    nt.links.new(s, em.inputs["Strength"])
    nt.links.new(em.outputs[0], out.inputs["Surface"])
    return m


def reflection_sheet(sc, cam, name, face_fn, r_rng, a_rng, frames, dist_fn, mat, nr=10, na=24):
    """face_fn(r, a) -> (P, nrm); dist_fn(P, rf) -> distance along the reflected ray. frames: solve frames
    (sorted); the middle one is the basis."""
    f_cur = sc.frame_current

    def solve(f):
        sc.frame_set(f)
        cp = cam.matrix_world.translation.copy()
        vs = []
        for j in range(na + 1):
            a = a_rng[0] + (a_rng[1] - a_rng[0]) * j / na
            for i in range(nr + 1):
                r = r_rng[0] + (r_rng[1] - r_rng[0]) * i / nr
                P, nrm = face_fn(r, a)
                d = (P - cp).normalized()
                rf = d - 2 * d.dot(nrm) * nrm
                vs.append(P + rf * dist_fn(P, rf))
        return vs

    sols = [solve(f) for f in frames]
    sc.frame_set(f_cur)
    mid = len(frames) // 2
    faces = []
    for j in range(na):
        for i in range(nr):
            k = j * (nr + 1) + i
            faces.append((k, k + 1, k + nr + 2, k + nr + 1))
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in sols[mid]], [], faces)
    uvl = me.uv_layers.new(name="UVMap")
    for poly in me.polygons:
        for li in poly.loop_indices:
            vi = me.loops[li].vertex_index
            uvl.data[li].uv = ((vi % (nr + 1)) / nr, (vi // (nr + 1)) / na)
    ob = bpy.data.objects.new(name, me)
    sc.collection.objects.link(ob)
    ob.data.materials.append(mat)
    glossy_only(ob)
    ob.shape_key_add(name="Basis")
    for k, f in enumerate(frames):
        if k == mid:
            continue
        sk = ob.shape_key_add(name="F%d" % f)
        for vi, v in enumerate(sols[k]):
            sk.data[vi].co = v
        pts = [(f, 1.0)]
        if k > 0:
            pts.append((frames[k - 1], 0.0))
        if k < len(frames) - 1:
            pts.append((frames[k + 1], 0.0))
        for ff, val in pts:
            sk.value = val
            sk.keyframe_insert("value", frame=ff)
    ad = me.shape_keys.animation_data
    if ad and ad.action:
        for fc in _fcurves(ad.action):
            for kp in fc.keyframe_points:
                kp.interpolation = "LINEAR"
    return ob


def _fcurves(action):
    try:
        return list(action.fcurves)
    except AttributeError:          # Blender 4.4+ layered actions
        out = []
        for layer in action.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    out.extend(bag.fcurves)
        return out


def ribbons(sc, name, paths, n, color=(0.66, 0.7, 0.86), w0=0.0012, w1=0.0038, base=0.3, pulse=1.1, seg=8):
    """tapered tubes along paths (lists of Vector), UV u along the path, v = path index; alpha fade at both ends."""
    verts, faces, uvs = [], [], []
    npth = len(paths)
    for pi_, pts in enumerate(paths):
        m = len(pts)
        base_i = len(verts)
        for k, p in enumerate(pts):
            u = k / (m - 1)
            t = (pts[min(k + 1, m - 1)] - pts[max(k - 1, 0)]).normalized()
            a = t.orthogonal().normalized()
            b = t.cross(a).normalized()
            rad = w0 + (w1 - w0) * (u ** 0.7)
            for s in range(seg):
                th = 2 * math.pi * s / seg
                verts.append(p + (a * math.cos(th) + b * math.sin(th)) * rad)
                uvs.append((u, pi_ / max(1, npth)))
        for k in range(m - 1):
            for s in range(seg):
                i0 = base_i + k * seg + s
                i1 = base_i + k * seg + (s + 1) % seg
                faces.append((i0, i1, i1 + seg, i0 + seg))
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], faces)
    uvl = me.uv_layers.new(name="UVMap")
    for poly in me.polygons:
        poly.use_smooth = True
        for li in poly.loop_indices:
            uvl.data[li].uv = uvs[me.loops[li].vertex_index]
    ob = bpy.data.objects.new(name, me)
    sc.collection.objects.link(ob)
    mat = bpy.data.materials.new(name + "M")
    mat.use_nodes = True
    nt = mat.node_tree
    for nd in list(nt.nodes):
        if nd.type != "OUTPUT_MATERIAL":
            nt.nodes.remove(nd)
    out = next(nd for nd in nt.nodes if nd.type == "OUTPUT_MATERIAL")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*color, 1)
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mix = nt.nodes.new("ShaderNodeMixShader")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sp = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["UV"], sp.inputs[0])
    u, v = sp.outputs["X"], sp.outputs["Y"]
    fade = _ramp(nt, u, [(0.0, 0.0), (0.12, 1.0), (0.82, 1.0), (1.0, 0.0)])     # no blunt / dotted ends
    tval = nt.nodes.new("ShaderNodeValue")                                          # time driver (keyed)
    tval.outputs[0].default_value = 0.0
    tval.outputs[0].keyframe_insert("default_value", frame=1)
    tval.outputs[0].default_value = n / 90.0
    tval.outputs[0].keyframe_insert("default_value", frame=n)
    ph = _math(nt, "MULTIPLY", u, 1.6)
    ph = _math(nt, "SUBTRACT", ph, tval.outputs[0])
    ph = _math(nt, "ADD", ph, _math(nt, "MULTIPLY", v, 3.7))
    w = _math(nt, "FRACT", ph)
    pw = _math(nt, "POWER", w, 3.0)                                                 # streak: head toward the pump
    st = _math(nt, "ADD", _math(nt, "MULTIPLY", pw, pulse), base)
    nt.links.new(st, em.inputs["Strength"])
    nt.links.new(fade, mix.inputs[0])
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(em.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])
    ad = mat.node_tree.animation_data
    if ad and ad.action:
        for fc in _fcurves(ad.action):
            for kp in fc.keyframe_points:
                kp.interpolation = "LINEAR"
    ob.data.materials.append(mat)
    for attr in ("visible_diffuse", "visible_glossy", "visible_transmission", "visible_volume_scatter",
                 "visible_shadow"):
        setattr(ob, attr, False)
    return ob
