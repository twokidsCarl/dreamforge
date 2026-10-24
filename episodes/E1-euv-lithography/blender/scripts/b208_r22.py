"""Round 22 (P1) hook for B2_08 (R22_ROOT_CAUSE row 6). Owned by the src-a sub-agent.

R21 review B2_08: 「镜面偏哑光深蓝，像喷涂件，不像原子级抛光的镜子（A 扣分）。改法：镜面粗糙度降到 ≤0.05，加一条掠射高光带，
深色锡斑做成镜面上能看清的小斑点。」 R21 attempt (source_r21.b208_r21, off) put its cool highlight on the SnH4
streamlines (upper face) and did not separate face / shell.

post() (material + light path only, geometry untouched):
  * mirror face (CollB208_mirror) -> light neutral polished metal, roughness 0.03 (was the violet-blue-reading
    multilayer at 0.035 mirroring a dark blue room);
  * grazing highlight band: a ribbon emitter seen ONLY by glossy rays (camera / diffuse / shadow invisible), built
    by reflecting the frame-133 camera rays off a chord of face points in the LOWER half of the face on screen (below
    the hole, away from the streamlines / pump side): its mirror image is a sharp cool-white band across the face;
    the dark tin deposits on that band read as small dark spots;
  * outer shell / ground blank (CollB208_substrate) -> neutral matte grey, so the matte shell and the polished face
    separate;
  * a dim glossy-only neutral panel behind the camera lifts the face from "deep blue" to a neutral steel tone.
Remove B2_08 from r2_source.R22_SRC -> R21 pixels.
"""
import math
import os

_E = os.environ


def pre(variant, shot, mod):
    pass


def _glossy_only(ob):
    for attr in ("visible_camera", "visible_diffuse", "visible_shadow", "visible_transmission",
                 "visible_volume_scatter"):
        setattr(ob, attr, False)
    ob.visible_glossy = True


def post(sc, variant, shot):
    if shot != "B2_08":
        return
    import bpy
    from mathutils import Vector
    import kit_r2 as K
    import b115_r17 as B115
    mir = bpy.data.objects.get("CollB208_mirror")
    sub = bpy.data.objects.get("CollB208_substrate")
    if sub is not None:
        sub.data.materials.clear()
        sub.data.materials.append(K.mat("CollShellMatteR22", (0.36, 0.365, 0.37), metal=0.1, rough=0.8))
    if mir is None:
        return
    mir.data.materials.clear()
    mir.data.materials.append(K.mat("CollFacePolishR22", (0.9, 0.91, 0.93), metal=1.0,
                                    rough=float(_E.get("B228_ROUGH", "0.03"))))
    dep = bpy.data.objects.get("TinDeposits")
    if dep is not None:              # deposits: dark, matte, a touch larger so they read as spots on the band
        dep.data.materials.clear()
        dep.data.materials.append(K.mat("TinDepositDarkR22", (0.05, 0.05, 0.055), metal=0.2, rough=0.85))
        sc_ = float(_E.get("B228_DEPS", "1.5"))
        dep.scale = (1.0, 1.0, 1.0)
        mesh = dep.data
        # scale each deposit disc about its own centre (mesh islands): approximate with vertex-normal-free scaling
        import bmesh
        bm = bmesh.new()
        bm.from_mesh(mesh)
        islands = []
        seen = set()
        for v in bm.verts:
            if v.index in seen:
                continue
            stack, isl = [v], []
            seen.add(v.index)
            while stack:
                w = stack.pop()
                isl.append(w)
                for e in w.link_edges:
                    o = e.other_vert(w)
                    if o.index not in seen:
                        seen.add(o.index)
                        stack.append(o)
            islands.append(isl)
        for isl in islands:
            c = sum((w.co for w in isl), Vector()) / len(isl)
            for w in isl:
                w.co = c + (w.co - c) * sc_
        bm.to_mesh(mesh)
        bm.free()
    cam = sc.camera
    f0 = sc.frame_current
    sc.frame_set(int(_E.get("B228_FR", "133")))
    cm = cam.matrix_world.copy()
    sc.frame_set(f0)
    cpos = cm.translation
    up = (cm.to_3x3() @ Vector((0, 1, 0))).normalized()
    right = (cm.to_3x3() @ Vector((1, 0, 0))).normalized()
    F = B115.B_F
    # chord of face points below the hole on screen: in the face (y, z) plane, along screen-right at a fixed
    # screen-down offset
    dn2 = Vector((-up.y, -up.z)).normalized()
    rt2 = Vector((right.y, right.z)).normalized()
    off = float(_E.get("B228_OFF", "0.42"))
    s0, s1 = float(_E.get("B228_S0", "-0.4")), float(_E.get("B228_S1", "0.15"))
    width = float(_E.get("B228_W", "0.03"))
    dist = float(_E.get("B228_D", "1.4"))
    verts, faces = [], []
    N = 24
    for i in range(N + 1):
        s = s0 + (s1 - s0) * i / N
        p2 = dn2 * off + rt2 * s
        r = p2.length
        if r > 0.66:
            p2 = p2 * (0.66 / r)
            r = 0.66
        y, z = p2.x, p2.y
        P = Vector((B115.face_x(r), y, z))
        nrm = Vector((1, -y / (2 * F), -z / (2 * F))).normalized()
        d = (P - cpos).normalized()
        rf = d - 2 * d.dot(nrm) * nrm
        Q = P + rf * dist
        side = rf.cross(right).normalized()
        verts.append(tuple(Q + side * width))
        verts.append(tuple(Q - side * width))
        if i:
            k = 2 * i
            faces.append((k - 2, k - 1, k + 1, k))
    me = bpy.data.meshes.new("B208GrazeBandR22")
    me.from_pydata(verts, [], faces)
    band = bpy.data.objects.new("B208GrazeBandR22", me)
    sc.collection.objects.link(band)
    uvl = me.uv_layers.new(name="UVMap")
    for poly in me.polygons:             # u along the band, v across it (soft edges: strength ~ sin(pi v) sin(pi u))
        for li_ in poly.loop_indices:
            vi = me.loops[li_].vertex_index
            uvl.data[li_].uv = ((vi // 2) / N, float(vi % 2))
    m = K.emit_mat("B208GrazeBandR22M", (0.86, 0.92, 1.0), float(_E.get("B228_E", "1.6")))
    nt = m.node_tree
    em = next(nd for nd in nt.nodes if nd.type == "EMISSION")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sp = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["UV"], sp.inputs[0])
    prod = None
    for ch in ("X", "Y"):
        mu = nt.nodes.new("ShaderNodeMath")
        mu.operation = "MULTIPLY"
        mu.inputs[1].default_value = math.pi
        nt.links.new(sp.outputs[ch], mu.inputs[0])
        si = nt.nodes.new("ShaderNodeMath")
        si.operation = "SINE"
        nt.links.new(mu.outputs[0], si.inputs[0])
        if prod is None:
            prod = si
        else:
            mm = nt.nodes.new("ShaderNodeMath")
            mm.operation = "MULTIPLY"
            nt.links.new(prod.outputs[0], mm.inputs[0])
            nt.links.new(si.outputs[0], mm.inputs[1])
            prod = mm
    sc2 = nt.nodes.new("ShaderNodeMath")
    sc2.operation = "MULTIPLY"
    sc2.inputs[1].default_value = em.inputs["Strength"].default_value
    nt.links.new(prod.outputs[0], sc2.inputs[0])
    nt.links.new(sc2.outputs[0], em.inputs["Strength"])
    e0 = sc2.inputs[1].default_value     # band only while the camera's reflection geometry puts it on the lower
    for f_, k_ in ((1, 0.0), (85, 0.0), (120, 1.0), (240, 1.0)):    # face (frame 60: a stray comma blob)
        sc2.inputs[1].default_value = e0 * k_
        sc2.inputs[1].keyframe_insert("default_value", frame=f_)
    band.data.materials.append(m)
    _glossy_only(band)
    # dim neutral glossy-only panel behind the camera (face tone: neutral steel instead of deep blue)
    pe = float(_E.get("B228_PE", "0"))
    if pe > 0:
        fwd = (cm.to_3x3() @ Vector((0, 0, -1))).normalized()
        me2 = bpy.data.meshes.new("B208NeutralPanelR22")
        c = cpos - fwd * 0.25
        a, b = right * 0.6, up * 0.45
        me2.from_pydata([tuple(c - a - b), tuple(c + a - b), tuple(c + a + b), tuple(c - a + b)], [], [(0, 1, 2, 3)])
        pn = bpy.data.objects.new("B208NeutralPanelR22", me2)
        sc.collection.objects.link(pn)
        pn.data.materials.append(K.emit_mat("B208NeutralPanelR22M", (0.8, 0.82, 0.85), pe))
        _glossy_only(pn)
