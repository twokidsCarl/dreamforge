"""Round 29 (P1, R29_ROOT_CAUSE row 1, owned by the MAIN process - agents import it, never edit it).

R28 review, all three lanes: the beam_r26 soft SHELL still reads as 「等宽噪点管」「均匀半透明硬壳 / 玻璃漏斗 / 花瓶」, and
C_03 「交汇点在掩模面以下约一个光柱直径处」. R24-R28 tuned shell parameters (edge / core / alpha / rim / widen) and
fades five rounds in a row without a score gain: a surface shader on an open tube can only paint the silhouette or a
flat fill. R28 B5_01 also faded the non-current legs to 20 % (R27 ask) and was read as 「IF → 场分面这一段缺失」 (-3.56).

beam_r29 = a GEOMETRY change, not a shell parameter:
  * every beam leg becomes a CLOSED cone mesh carrying a pure-emission VOLUME (Principled Volume, density 0 = no
    absorption, the background stays visible through it). The emission density is a function of the position inside
    the cone in the leg's own frame (origin = start stop, +Z = leg axis, X / Y = the ellipse axes):
        t  = z / L,  Rx(t) / Ry(t) = linear between the two landing apertures (the cone really converges / diverges),
        q2 = (x / Rx)^2 + (y / Ry)^2,  g = (exp(-K q2) - exp(-K)) / (1 - exp(-K))    (Gaussian, exactly 0 at the rim)
        E  = B * level * (R0 / R)^GAMMA / (CK * R)
    -> projected across the beam: centre bright, edges fade to 0 with no outline (volume, not glass), and the line of
    sight through the axis has radiance ~ B * (R0 / R)^GAMMA: the narrow (focus) end is mildly brighter, the wide end
    never blows into a flat plate.
  * landings: the chain's landing spots stay where beam_r25 put them (ON the mirror / mask face); each spot is made
    1.6x brighter than its R28 value, so every turn has a bright spot on the face.
  * levels: `levels(sc, legs, windows)` keys a per-leg level - the current leg 1.0, every other leg FLOOR (0.6) -
    so the WHOLE path is visible every frame (R29 HARD: no leg below 50 %).
  * convert(): post-hook helper. Every beam leg already in the scene (objects carrying r25_radii = beam_r25 / beam_r26
    soft cones, incl. hooked / per-shot swaps) is replaced in place: the old object keeps its transform / parent /
    animation but is hidden from every ray; a new volume cone is parented to it, built from the old mesh's first and
    last ring (centres = the two stops, semi-axes = the two apertures). Meshes with modifiers / degenerate rings are
    left as they are and reported.
Not R18-R21 surface "volume fog" (that was a shell with alpha), not R25 edge shell, not R26 rim roll-off, not R28 20 %
fades.
"""
import math

import bmesh
import bpy
from mathutils import Matrix, Vector

import kit_r2 as K

K_GAUSS = 3.0                # Gaussian falloff; g(1) = 0 exactly
GAMMA = 0.5                  # centre radiance ~ (R0 / R)^GAMMA: the focus end is brighter, not blown
FLOOR = 0.6                  # level of a non-current leg (R29 HARD: >= 0.5)
SPOT_GAIN = 1.6              # landing spots on the faces
B_DEFAULT = 1.6              # centre-line radiance of a leg at its wide end (scene linear)
SEG = 40
_E = math.exp(-K_GAUSS)
CK = 2.0 * sum((math.exp(-K_GAUSS * s * s) - _E) / (1 - _E) for s in (i / 400 for i in range(400))) / 400  # ~0.96


def _op(N, L, op, a, b=None):
    n = N.new("ShaderNodeMath")
    n.operation = op
    for i, v in enumerate((a, b)):
        if v is None:
            continue
        if isinstance(v, (int, float)):
            n.inputs[i].default_value = v
        else:
            L.new(v, n.inputs[i])
    return n.outputs[0]


def volume_mat(name, color, b, L_len, rx0, ry0, rx1, ry1):
    """Pure-emission volume with the Gaussian cross-section of a cone (0, rx0, ry0) -> (L, rx1, ry1) in object space."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    N, Lk = m.node_tree.nodes, m.node_tree.links
    for n in list(N):
        if n.type != "OUTPUT_MATERIAL":
            N.remove(n)
    out = next(n for n in N if n.type == "OUTPUT_MATERIAL")
    tc = N.new("ShaderNodeTexCoord")
    sp = N.new("ShaderNodeSeparateXYZ")
    Lk.new(tc.outputs["Object"], sp.inputs[0])
    x, y, z = sp.outputs[0], sp.outputs[1], sp.outputs[2]
    t = _op(N, Lk, "MINIMUM", _op(N, Lk, "MAXIMUM", _op(N, Lk, "DIVIDE", z, L_len), 0.0), 1.0)
    rx = _op(N, Lk, "ADD", rx0, _op(N, Lk, "MULTIPLY", t, rx1 - rx0))
    ry = _op(N, Lk, "ADD", ry0, _op(N, Lk, "MULTIPLY", t, ry1 - ry0))
    qx = _op(N, Lk, "DIVIDE", x, rx)
    qy = _op(N, Lk, "DIVIDE", y, ry)
    q2 = _op(N, Lk, "ADD", _op(N, Lk, "MULTIPLY", qx, qx), _op(N, Lk, "MULTIPLY", qy, qy))
    g = _op(N, Lk, "EXPONENT", _op(N, Lk, "MULTIPLY", q2, -K_GAUSS))
    g = _op(N, Lk, "MAXIMUM", _op(N, Lk, "DIVIDE", _op(N, Lk, "SUBTRACT", g, _E), 1 - _E), 0.0)
    r = _op(N, Lk, "SQRT", _op(N, Lk, "MULTIPLY", rx, ry))
    r0 = math.sqrt(max(rx0 * ry0, rx1 * ry1))
    # E = b * level * (r0 / r)^GAMMA / (CK * r)
    gain = _op(N, Lk, "DIVIDE", _op(N, Lk, "POWER", _op(N, Lk, "DIVIDE", r0, r), GAMMA), _op(N, Lk, "MULTIPLY", r, CK))
    lvl = N.new("ShaderNodeValue")
    lvl.name = "R29Lvl"
    lvl.outputs[0].default_value = 1.0
    e = _op(N, Lk, "MULTIPLY", _op(N, Lk, "MULTIPLY", g, gain), _op(N, Lk, "MULTIPLY", lvl.outputs[0], b))
    pv = N.new("ShaderNodeVolumePrincipled")
    pv.inputs["Density"].default_value = 0.0
    pv.inputs["Emission Color"].default_value = (*K.lin(color), 1)
    Lk.new(e, pv.inputs["Emission Strength"])
    Lk.new(pv.outputs[0], out.inputs["Volume"])
    try:
        m.cycles.homogeneous_volume = False
        m.cycles.volume_step_rate = 0.5
    except AttributeError:
        pass
    m["r29_volume"] = (b, L_len, rx0, ry0, rx1, ry1)
    return m


def _cone_closed(name, L_len, rx0, ry0, rx1, ry1, seg=SEG):
    bm = bmesh.new()
    rings = []
    for z, rx, ry in ((0.0, rx0, ry0), (L_len, rx1, ry1)):
        rings.append([bm.verts.new((rx * math.cos(2 * math.pi * i / seg), ry * math.sin(2 * math.pi * i / seg), z))
                      for i in range(seg)])
    for i in range(seg):
        j = (i + 1) % seg
        bm.faces.new((rings[0][i], rings[0][j], rings[1][j], rings[1][i]))
    bm.faces.new(list(reversed(rings[0])))
    bm.faces.new(rings[1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    return me


def _vis_cam_only(ob):
    for a in ("visible_shadow", "visible_diffuse", "visible_glossy", "visible_transmission", "visible_volume_scatter"):
        try:
            setattr(ob, a, False)
        except AttributeError:
            pass


def _hide_all(ob):
    _vis_cam_only(ob)
    try:
        ob.visible_camera = False
    except AttributeError:
        ob.hide_render = True


def cone(name, a, b, ra, rb, color=None, strength=B_DEFAULT, xdir=None, parent=None):
    """Volume cone a -> b (world or parent-local points); ra / rb float or (rx, ry). Returns the object."""
    a, b = Vector(a), Vector(b)
    ra = (ra, ra) if isinstance(ra, (int, float)) else tuple(ra)
    rb = (rb, rb) if isinstance(rb, (int, float)) else tuple(rb)
    d = b - a
    L_len = d.length
    ez = d.normalized()
    ex = (Vector(xdir) - ez * Vector(xdir).dot(ez)) if xdir is not None else ez.orthogonal()
    if ex.length < 1e-9:
        ex = ez.orthogonal()
    ex.normalize()
    ey = ez.cross(ex).normalized()
    me = _cone_closed(name, L_len, ra[0], ra[1], rb[0], rb[1])
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    M = Matrix((ex, ey, ez)).transposed().to_4x4()
    M.translation = a
    if parent is not None:
        ob.parent = parent
        ob.matrix_parent_inverse = Matrix.Identity(4)
        ob.matrix_basis = M
    else:
        ob.matrix_world = M
    me.materials.append(volume_mat(name + "M", K.VIOLET if color is None else color, strength, L_len, ra[0], ra[1],
                                   rb[0], rb[1]))
    _vis_cam_only(ob)
    ob["r29_beam"] = (float(L_len), float(max(ra)), float(max(rb)))
    return ob


def _rings(ob):
    """(a, ex*rx, ey*ry, b, ex*rx, ey*ry) of a beam_r18 _cone_mesh (object-local), from the ConeUV v = 0 / 1 rings."""
    me = ob.data
    uv = me.uv_layers.get("ConeUV")
    if uv is None:
        return None
    s_of = {}
    for lp in me.loops:
        s_of[lp.vertex_index] = uv.data[lp.index].uv[1]
    r0 = sorted(i for i, s in s_of.items() if abs(s) < 1e-4)
    r1 = sorted(i for i, s in s_of.items() if abs(s - 1) < 1e-4)
    if len(r0) < 8 or len(r1) < 8:
        return None
    out = []
    for ring in (r0, r1):
        pts = [me.vertices[i].co.copy() for i in ring]
        c = sum(pts, Vector()) / len(pts)
        out.append((c, pts[0] - c, pts[len(pts) // 4] - c))
    return out


def _leg_color(ob):
    for s in ob.material_slots:
        m = s.material
        if m and m.use_nodes:
            em = next((n for n in m.node_tree.nodes if n.type == "EMISSION"), None)
            if em is not None:
                c = em.inputs["Color"].default_value
                return tuple(((x ** (1 / 2.4)) * 1.055 - 0.055) if x > 0.0031308 else x * 12.92 for x in c[:3])
    return K.VIOLET


def convert(sc, strength=B_DEFAULT, names=None, skip=(), tag=""):
    """Replace every beam leg (r25_radii objects) with a volume cone parented to it. Returns {old name: new obj}."""
    done, kept = {}, []
    for ob in list(bpy.data.objects):
        if ob.type != "MESH" or "r25_radii" not in ob.keys() or ob.get("r29_replaced"):
            continue
        if names is not None and not any(ob.name.startswith(n) for n in names):
            continue
        if any(ob.name.startswith(s) for s in skip):
            continue
        if not _visible(ob) and not _vis_keyed(ob):
            continue
        if ob.modifiers or (ob.data.shape_keys is not None):
            kept.append(ob.name + " (modifiers)")
            continue
        rg = _rings(ob)
        if rg is None or (rg[1][0] - rg[0][0]).length < 1e-4:
            kept.append(ob.name + " (no rings)")
            continue
        (a, xa, ya), (b, xb, yb) = rg
        s = strength(ob) if callable(strength) else strength
        nw = cone(ob.name + "V29", a, b, (xa.length, ya.length), (xb.length, yb.length), _leg_color(ob), s, xdir=xa,
                  parent=ob)
        _hide_all(ob)
        ob["r29_replaced"] = nw.name
        done[ob.name] = nw
    for sp in bpy.data.objects:
        if sp.type == "MESH" and sp.data.uv_layers.get("SpotUV") is not None and _visible(sp) and not sp.get("r29_spot"):
            for s_ in sp.material_slots:
                m = s_.material
                if m and m.use_nodes:
                    for n in m.node_tree.nodes:
                        if n.type == "EMISSION":
                            n.inputs["Strength"].default_value *= SPOT_GAIN
            sp["r29_spot"] = True
    print(f"[beam_r29] {tag} converted {len(done)} legs {sorted(done)} kept {kept}", flush=True)
    return done


def _visible(ob):
    if ob.hide_render:
        return False
    try:
        return ob.visible_camera
    except AttributeError:
        return True


def _vis_keyed(ob):
    """A leg hidden at build time but revealed by keyframes (B7_06 R27 reveal) is still a path leg: R29 shows it
    every frame (the whole path), at the levels() floor."""
    ad = ob.animation_data
    return bool(ad and ad.action and any(fc.data_path in ("hide_render", "visible_camera") for fc in _fcurves(ad.action)))


def _fcurves(act):
    fcs = getattr(act, "fcurves", None)
    if fcs is not None:
        return list(fcs)
    out = []
    for lay in getattr(act, "layers", []):
        for st in lay.strips:
            for cb in st.channelbags:
                out += list(cb.fcurves)
    return out


def levels(sc, legs, windows, floor=FLOOR, ramp=6, tag=""):
    """legs = [volume objects in path order]; windows = [(leg index, t0, t1)] (shot fractions): 1.0 inside, floor
    outside (keyed, linear)."""
    n = sc.frame_end
    pe = bpy.context.preferences.edit
    prev = pe.keyframe_new_interpolation_type
    pe.keyframe_new_interpolation_type = "LINEAR"
    try:
        for i, t0, t1 in windows:
            if i >= len(legs) or legs[i] is None:
                continue
            f0, f1 = 1 + (n - 1) * t0, 1 + (n - 1) * t1
            keys = [(1, floor if t0 > 0 else 1.0)]
            if t0 > 0:
                keys += [(max(1, round(f0 - ramp / 2)), floor), (round(f0 + ramp / 2), 1.0)]
            if t1 < 1:
                keys += [(round(f1 - ramp / 2), 1.0), (round(f1 + ramp / 2), floor), (n, floor)]
            else:
                keys += [(n, 1.0)]
            obs = legs[i] if isinstance(legs[i], (list, tuple)) else [legs[i]]
            for ob in obs:
                for s in ob.material_slots:
                    v = s.material.node_tree.nodes.get("R29Lvl") if s.material else None
                    if v is None:
                        continue
                    for f, val in keys:
                        v.outputs[0].default_value = val
                        v.outputs[0].keyframe_insert("default_value", frame=f)
            print(f"[beam_r29] {tag} leg{i} keys {keys}", flush=True)
    finally:
        pe.keyframe_new_interpolation_type = prev
