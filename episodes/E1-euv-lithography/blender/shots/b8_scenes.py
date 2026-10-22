"""B8 — wafer and reticle stages (F15, F15b, F41, F43b, F44, F51, F57, F58). Variants:

  wafer     B8_01  a 300 mm wafer in the dark: per-die grating diffraction, 775 um thick, 1 mm 90-deg V notch
  slit      B8_02  energy: a ghost glow over the whole wafer gives way to the light the projection optics actually
                   deliver: a converging fan (NA 0.55) onto one arc slit, 26 mm long, across one 26 x 16.5 mm field
  scan      B8_03  clay: reticle stage and wafer stage scan in opposite directions under a fixed slit, the wafer
                   moves 1/8 as far (High-NA, 8x in the scan direction); field after field, meander (scan up / down)
            B8_04  clay: speed arrows 8 : 1 on the two stages during one scan
  car       B8_07  photoreal maglev reticle stage (NXE, >15 g); mask clamped under it, pattern down; ghost car drops
            B8_08  slow side replay from below: a stress wave across the stage stops at the clamp / mask edge
  sync      B8_10  xray High-NA machine (build_machine): reticle stage and wafer stage sprint in opposite
                   directions, travel 8 : 1, while the light path stays fixed on its mirrors
  maglev    B8_14  macro: wafer table floating over a planar-motor magnet plate (no contact, no lamps)
  layers    B8_15  clay chip cross-section: patterned layers drop and stack; the last one lands with a LATERAL offset
  dual      B8_16  xray dual stage: exposing on the left, measuring on the right, swap

Sources (research/visual/B8B9_sources.md, S-numbers there):
  wafer 300 mm, 775 um thick, notch 1.0 mm deep and 90 deg, 3 mm edge exclusion       S18 (SVMI SV029 / SEMI)
  High-NA: 4x across the scan, 8x along it; half field 26 x 16.5 mm; reticle image field 104 x 132 mm;
  slit at the wafer an arc 26 x 1.6 mm, at the reticle 104 x 12.8 mm                    S2, HNA [A22] s.12/27, [Z21] s.11
  slit shaped by the illuminator's arc-shaped field facets (not by blades above the wafer) S12; REMA blades frame the
  field at the reticle side                                                              S11
  reticle and wafer scanned in opposite directions at constant speed                     S3, S13
  successive fields scanned in opposite directions (+Y, -Y, ... "scan up / scan down")   ASML patent US8711329B2
  reticle stage "completely magnetically levitated"; >15 g, >10,000 N, the car metaphor  S1 (NXE stage)
  reticle held by an electrostatic clamp on its backside, pattern facing down            S11, HNA [C11] s.5, S9 p.16
  wafer stage "dual planar stage + balance mass", "magnetically levitating wafer tables" S11, S3
  overlay = lateral alignment of one layer to the previous one                          S6, S10
  two wafer tables: one exposes while the other is aligned and mapped, then they swap    S7
Not public (drawn as plausible, 示意): slit arc radius, stage shapes and sizes, die layout, alignment-mark layout.
"""
import math
import os
import random

import bpy
from mathutils import Vector

import build_machine as BM
import common as C
import materials as M
import sample_b1 as B
import styles

FRAMES = 520
VIOLET = (0.62, 0.45, 1.0)
EUV = (0.30, 0.08, 1.0)          # saturated violet for light volumes: stays violet under AgX, does not clip white
CYAN = (0.2, 0.85, 0.95)
ORANGE = (1.0, 0.42, 0.12)
NA_HALF = math.asin(0.55)        # High-NA: half-angle of the light cone at the wafer (33.4 deg)
B8_08_START = 400                # sim frame where the B8_08 replay starts (registry.yaml B8_08 start)


def _frames(sid, default):
    """Shot length in frames from storyboard.timed.yaml, so key beats follow a re-voiced line."""
    try:
        import yaml
        import paths
        sb = yaml.safe_load(open(os.path.join(paths.EP, "storyboard/storyboard.timed.yaml"), encoding="utf-8"))
        return max(1, round(next(s["duration"] for s in sb["shots"] if s["id"] == sid) * 24))
    except Exception:
        return default


def _key(ob, f, **kw):
    for k, v in kw.items():
        setattr(ob, k, v)
        ob.keyframe_insert(k, frame=f)


def _interp(ob, mode="LINEAR", after=None):
    if ob.animation_data and ob.animation_data.action:
        for fc in C.fcurves(ob.animation_data.action):
            for kp in fc.keyframe_points:
                if after is None or kp.co[0] >= after:
                    kp.interpolation = mode


def _box(name, loc, size, mat, role="structure", bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    ob = bpy.context.object
    ob.name = name
    ob.scale = (size[0] / 2, size[1] / 2, size[2] / 2)
    if bevel:
        m = ob.modifiers.new("Bevel", "BEVEL")
        m.width = bevel
        m.segments = 2
    ob.data.materials.append(mat)
    styles.tag(ob, role)
    return ob


def _cyl(name, r, depth, loc, mat, rot=(0, 0, 0), role="structure", verts=64):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=depth, vertices=verts, location=loc, rotation=rot)
    ob = bpy.context.object
    ob.name = name
    for p in ob.data.polygons:
        p.use_smooth = True
    es = ob.modifiers.new("Edges", "EDGE_SPLIT")
    es.split_angle = math.radians(40)
    ob.data.materials.append(mat)
    styles.tag(ob, role)
    return ob


def _mesh(name, verts, faces, mat, role="structure"):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], faces)
    me.update()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    ob.data.materials.append(mat)
    styles.tag(ob, role)
    return ob


def _parent(ch, par):
    ch.parent = par
    ch.matrix_parent_inverse = par.matrix_world.inverted()
    return ch


def _apply_scale(ob):
    """Bake object scale into the mesh so children are not distorted."""
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return ob


def _softbox(name, loc, size, strength, target=(0, 0, 0), color=(1.0, 0.98, 0.95)):
    bpy.ops.mesh.primitive_plane_add(size=size, location=loc)
    ob = bpy.context.object
    ob.name = name
    ob.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("Z", "Y").to_euler()
    ob.data.materials.append(M.soft_emitter(name + "Mat", color, strength))
    ob.visible_camera = False
    styles.tag(ob, "rig")
    return ob


def _aim_light(name, loc, target, size, energy, color=(0.85, 0.9, 1.0), size_y=None):
    rot = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    return B._area(name, loc, tuple(rot), size, energy, color, size_y=size_y)


# ---- node helpers -----------------------------------------------------------------------------
class _NB:
    def __init__(self, m):
        self.nt = m.node_tree
        self.N = self.nt.nodes
        self.L = self.nt.links.new

    def _set(self, sock, v):
        if isinstance(v, (int, float)):
            sock.default_value = v
        elif isinstance(v, tuple):
            sock.default_value = v
        else:
            self.L(v, sock)

    def math(self, op, a=None, b=None, c=None):
        n = self.N.new("ShaderNodeMath")
        n.operation = op
        for i, v in enumerate((a, b, c)):
            if v is not None:
                self._set(n.inputs[i], v)
        return n.outputs[0]

    def vmath(self, op, a, b=None):
        n = self.N.new("ShaderNodeVectorMath")
        n.operation = op
        for i, v in enumerate((a, b)):
            if v is not None:
                self._set(n.inputs[i], v)
        return n.outputs["Value"] if op in ("DOT_PRODUCT", "LENGTH") else n.outputs["Vector"]

    def xyz(self, x, y, z):
        n = self.N.new("ShaderNodeCombineXYZ")
        for i, v in enumerate((x, y, z)):
            self._set(n.inputs[i], v)
        return n.outputs[0]

    def mix_rgb(self, fac, a, b, blend="MIX"):
        n = self.N.new("ShaderNodeMix")
        n.data_type = "RGBA"
        n.blend_type = blend
        self._set(n.inputs["Factor"], fac)
        self._set(n.inputs["A"], a)
        self._set(n.inputs["B"], b)
        return n.outputs["Result"]

    def mix_vec(self, fac, a, b):
        n = self.N.new("ShaderNodeMix")
        n.data_type = "VECTOR"
        self._set(n.inputs["Factor"], fac)
        n.inputs[4].default_value = a
        n.inputs[5].default_value = b
        return n.outputs[1]


def wafer_material(name="WaferDies", r=1.5, lamp=(-0.5, 1.6, 2.6), strength=2.4, die_mm=(13.0, 16.5),
                   blocks=(6, 5), seed=0.37):
    """Patterned 300 mm wafer. The colour is diffraction, block by block (docs/WORKFLOW.md s.9): every die carries the
    same layout, so block (i, j) of each die has the same grating (pitch d 0.8-1.8 um, lines along x or y); a block
    lights only where lamp and eye satisfy the grating equation, lambda = d |V.t + L.t| / m (t = line normal), with
    brightness ~ exp(-((V.b + L.b)/0.25)^2) along the lines, as in a0_scenes.chip_material. The hue therefore repeats
    die to die and drifts slowly across the wafer with the viewing angle; no thin-film coating. Scribe streets and
    the 3 mm edge exclusion (S18) stay bare polished silicon. Die size is illustrative (13 x 16.5 mm, two per
    High-NA half field). `lamp` must be the position of a real light in the scene."""
    upm = r / 150.0                                      # scene units per mm
    m = M.principled(name, (0.05, 0.05, 0.06), metallic=0.7, roughness=0.12)
    nb = _NB(m)
    N = nb.N
    b = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord")
    geo = N.new("ShaderNodeNewGeometry")
    sep = N.new("ShaderNodeSeparateXYZ")
    nb.L(tc.outputs["Object"], sep.inputs[0])
    x, y = sep.outputs["X"], sep.outputs["Y"]
    dw, dh = die_mm[0] * upm, die_mm[1] * upm
    fu = nb.math("FRACT", nb.math("DIVIDE", x, dw))
    fv = nb.math("FRACT", nb.math("DIVIDE", y, dh))
    sw, sh = 0.3 / die_mm[0], 0.3 / die_mm[1]           # 0.3 mm scribe streets (slightly wider than real, to read)
    street = nb.math("MAXIMUM", nb.math("LESS_THAN", fu, sw), nb.math("LESS_THAN", fv, sh))
    bu = nb.math("MULTIPLY", nb.math("DIVIDE", nb.math("SUBTRACT", fu, sw), 1 - sw), blocks[0])
    bv = nb.math("MULTIPLY", nb.math("DIVIDE", nb.math("SUBTRACT", fv, sh), 1 - sh), blocks[1])
    gap = nb.math("MAXIMUM", nb.math("LESS_THAN", nb.math("FRACT", bu), 0.03),
                  nb.math("LESS_THAN", nb.math("FRACT", bv), 0.03))
    wn = N.new("ShaderNodeTexWhiteNoise")
    wn.noise_dimensions = "3D"
    nb.L(nb.xyz(nb.math("FLOOR", bu), nb.math("FLOOR", bv), seed), wn.inputs["Vector"])
    rnd = N.new("ShaderNodeSeparateColor")
    nb.L(wn.outputs["Color"], rnd.inputs["Color"])
    pitch = nb.math("MULTIPLY_ADD", rnd.outputs["Red"], 1000.0, 800.0)              # nm
    horiz = nb.math("GREATER_THAN", rnd.outputs["Green"], 0.5)
    active = nb.math("GREATER_THAN", rnd.outputs["Blue"], 0.45)
    # inside a block the line density is not uniform (arrays vs. logic): modulate by a fine noise, per block
    nz = N.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 900.0 / r
    nz.inputs["Detail"].default_value = 3.0
    nb.L(tc.outputs["Object"], nz.inputs["Vector"])
    dens = nb.math("MULTIPLY_ADD", nb.math("GREATER_THAN", rnd.outputs["Blue"], 0.8), 0.5,
                   nb.math("MULTIPLY_ADD", nz.outputs["Fac"], 0.9, 0.05))
    rad = nb.vmath("LENGTH", nb.xyz(x, y, 0.0))
    edge = nb.math("GREATER_THAN", rad, r - 3.0 * upm)
    bare = nb.math("MAXIMUM", street, edge)
    # base: patterned die area dark and slightly rough, block tones vary a little; bare silicon bright and polished
    tone = nb.math("MULTIPLY_ADD", rnd.outputs["Red"], 0.03, 0.035)
    die_col = nb.xyz(tone, tone, nb.math("ADD", tone, 0.008))
    die_col = nb.mix_rgb(nb.math("MULTIPLY", gap, 0.6), die_col, (0.015, 0.015, 0.018, 1))
    nb.L(nb.mix_rgb(bare, die_col, (0.33, 0.34, 0.37, 1)), b.inputs["Base Color"])
    nb.L(nb.math("MULTIPLY_ADD", bare, -0.08, 0.14), b.inputs["Roughness"])
    # grating vectors in world space
    t_w, b_w = [], []
    for out, (va, vb) in ((t_w, ((0.0, 1.0, 0.0), (1.0, 0.0, 0.0))), (b_w, ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0)))):
        vt = N.new("ShaderNodeVectorTransform")
        vt.vector_type = "VECTOR"
        vt.convert_from, vt.convert_to = "OBJECT", "WORLD"
        nb.L(nb.mix_vec(horiz, va, vb), vt.inputs["Vector"])
        out.append(nb.vmath("NORMALIZE", vt.outputs["Vector"]))
    t_w, b_w = t_w[0], b_w[0]
    Ldir = nb.vmath("NORMALIZE", nb.vmath("SUBTRACT", lamp, geo.outputs["Position"]))
    V = geo.outputs["Incoming"]
    st = nb.math("ADD", nb.vmath("DOT_PRODUCT", V, t_w), nb.vmath("DOT_PRODUCT", Ldir, t_w))
    sb = nb.math("ADD", nb.vmath("DOT_PRODUCT", V, b_w), nb.vmath("DOT_PRODUCT", Ldir, b_w))
    lam1 = nb.math("MULTIPLY", nb.math("ABSOLUTE", st), pitch)
    lobe = nb.math("EXPONENT", nb.math("MULTIPLY", nb.math("POWER", nb.math("DIVIDE", sb, 0.25), 2.0), -1.0))
    total = None
    for order, w in ((1, 1.0), (2, 0.7), (3, 0.45)):
        for spread in (0.94, 1.0, 1.06):
            lam = nb.math("DIVIDE", nb.math("MULTIPLY", lam1, spread), float(order))
            wl = N.new("ShaderNodeWavelength")
            nb.L(lam, wl.inputs["Wavelength"])
            lo = N.new("ShaderNodeMapRange")
            lo.interpolation_type = "SMOOTHSTEP"
            lo.inputs["From Min"].default_value, lo.inputs["From Max"].default_value = 395.0, 430.0
            nb.L(lam, lo.inputs["Value"])
            hi = N.new("ShaderNodeMapRange")
            hi.interpolation_type = "SMOOTHSTEP"
            hi.inputs["From Min"].default_value, hi.inputs["From Max"].default_value = 700.0, 660.0
            nb.L(lam, hi.inputs["Value"])
            win = nb.math("MULTIPLY", nb.math("MULTIPLY", lo.outputs["Result"], hi.outputs["Result"]), w / 3)
            term = nb.mix_rgb(1.0, wl.outputs["Color"], win, blend="MULTIPLY")
            total = term if total is None else nb.mix_rgb(1.0, total, term, blend="ADD")
    live = nb.math("MULTIPLY", nb.math("MULTIPLY", nb.math("SUBTRACT", 1.0, bare), nb.math("SUBTRACT", 1.0, gap)),
                   nb.math("MINIMUM", dens, 1.0))
    gain = nb.math("MULTIPLY", nb.math("MULTIPLY", nb.math("MULTIPLY", lobe, active), live), strength)
    nb.L(nb.mix_rgb(1.0, total, gain, blend="MULTIPLY"), b.inputs["Emission Color"])
    b.inputs["Emission Strength"].default_value = 1.0
    return m


def light_material(name, strength=1.0, height=1.0, edge=0.65, color=EUV):
    """Light volume drawn as a glassy additive sheet: brighter at grazing edges, fading out with height above its
    origin (object z from 0 at the bottom to `height`). Strength via the 'Gain' node (keyframable)."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nb = _NB(m)
    nb.N.clear()
    out = nb.N.new("ShaderNodeOutputMaterial")
    tc = nb.N.new("ShaderNodeTexCoord")
    sep = nb.N.new("ShaderNodeSeparateXYZ")
    nb.L(tc.outputs["Object"], sep.inputs[0])
    fade = nb.math("POWER", nb.math("MAXIMUM", nb.math("SUBTRACT", 1.0, nb.math("DIVIDE", sep.outputs["Z"], height)),
                                    0.0), 1.6)
    lw = nb.N.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.4
    face = nb.math("MULTIPLY_ADD", lw.outputs["Facing"], edge, 1.0 - edge)
    gain = nb.N.new("ShaderNodeMath")
    gain.name = "Gain"
    gain.operation = "MULTIPLY"
    gain.inputs[1].default_value = strength
    nb.L(nb.math("MULTIPLY", fade, face), gain.inputs[0])
    em = nb.N.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*color, 1)
    nb.L(gain.outputs[0], em.inputs["Strength"])
    tr = nb.N.new("ShaderNodeBsdfTransparent")
    add = nb.N.new("ShaderNodeAddShader")
    nb.L(tr.outputs[0], add.inputs[0])
    nb.L(em.outputs[0], add.inputs[1])
    nb.L(add.outputs[0], out.inputs["Surface"])
    m.surface_render_method = "BLENDED"
    m.use_backface_culling = False
    return m


def _gain(mat, frame, v):
    s = mat.node_tree.nodes["Gain"].inputs[1]
    s.default_value = v
    s.keyframe_insert("default_value", frame=frame)


def _wafer(name="Wafer", r=1.5, loc=(0, 0, 0), mat=None, verts=256):
    """300 mm wafer scaled to radius r: 775 um thick, rounded edge, 1 mm deep 90-degree V notch at -y (S18)."""
    upm = r / 150.0
    t = 0.775 * upm
    w = _cyl(name, r, t, loc, mat or wafer_material(r=r), verts=verts)
    w.modifiers.remove(w.modifiers["Edges"])
    bv = w.modifiers.new("Edge", "BEVEL")
    bv.width = t * 0.35
    bv.segments = 3
    bv.limit_method = "ANGLE"
    bpy.ops.mesh.primitive_cube_add(location=(loc[0], loc[1] - r, loc[2]))     # the notch
    n = bpy.context.object
    n.name = name + "NotchCut"
    s = 1.0 * upm / math.sqrt(2)                       # rotated square: corner reaches 1 mm in, flanks at 90 deg
    n.scale = (s, s, t * 4)
    n.rotation_euler = (0, 0, math.radians(45))
    n.hide_render = n.hide_viewport = True
    bo = w.modifiers.new("Notch", "BOOLEAN")
    bo.object = n
    bo.operation = "DIFFERENCE"
    _parent(n, w)
    return w


# ---- field grid (High-NA half fields, 26 mm across the scan x 16.5 mm along it) -------------------
def _half_fields(r, scan_axis="x"):
    """Field rectangles (local wafer coords, units) of the 188-field High-NA layout: a grid with boundaries at
    multiples of the field size, every field touching the 294 mm usable disc (S18 edge exclusion) counted.
    Computed: exactly 188 (HNA [A22] s.14). Returns (cx, cy, sx, sy) with sx, sy the sizes along x, y."""
    upm = r / 150.0
    a_scan, a_cross = 16.5 * upm, 26.0 * upm
    sx, sy = (a_scan, a_cross) if scan_axis == "x" else (a_cross, a_scan)
    out = []
    R = 147.0 * upm
    for i in range(-12, 12):
        for j in range(-12, 12):
            x0, y0 = i * sx, j * sy
            px, py = min(max(0.0, x0), x0 + sx), min(max(0.0, y0), y0 + sy)
            if math.hypot(px, py) < R:
                out.append((x0 + sx / 2, y0 + sy / 2, sx, sy))
    return out


def _grid_lines(prefix, r, z, mat, scan_axis="x", width=None, role="emitter"):
    """Thin lines along the half-field boundaries, clipped to the usable disc. Returns the line objects."""
    upm = r / 150.0
    R = 147.0 * upm
    sx, sy = (16.5 * upm, 26.0 * upm) if scan_axis == "x" else (26.0 * upm, 16.5 * upm)
    w = width or 0.12 * upm
    obs = []
    for axis, step in (("x", sx), ("y", sy)):
        k = -int(R / step)
        while k * step <= R:
            c = k * step
            half = math.sqrt(max(0.0, R * R - c * c))
            if half > 0.01 * r:
                if axis == "x":
                    ob = _box(f"{prefix}X{k}", (c, 0, z), (w, 2 * half, 0.0004 * r), mat, role=role)
                else:
                    ob = _box(f"{prefix}Y{k}", (0, c, z), (2 * half, w, 0.0004 * r), mat, role=role)
                obs.append(ob)
            k += 1
    return obs


def _arc_outline(L, w, sag, n=24, cx=0.0, cy=0.0):
    """Arc slit (long along y, narrow along x, bowed toward +x by `sag`): left edge then right edge, as a ring."""
    Rarc = (L * L / 4 + sag * sag) / (2 * sag)
    def xo(y):  # noqa: E306
        return sag - (Rarc - math.sqrt(Rarc * Rarc - y * y))
    ys = [-L / 2 + L * i / n for i in range(n + 1)]
    left = [(cx + xo(y) - w / 2, cy + y) for y in ys]
    right = [(cx + xo(y) + w / 2, cy + y) for y in reversed(ys)]
    return left + right, ys, xo


def _arc_strip(name, L, w, sag, z, mat, cx=0.0, cy=0.0, role="emitter"):
    _, ys, xo = _arc_outline(L, w, sag)
    verts, faces = [], []
    for y in ys:
        verts += [(cx + xo(y) - w / 2, cy + y, z), (cx + xo(y) + w / 2, cy + y, z)]
    for i in range(len(ys) - 1):
        faces.append((2 * i, 2 * i + 1, 2 * i + 3, 2 * i + 2))
    return _mesh(name, verts, faces, mat, role=role)


def _loft(name, ring0, z0, ring1, z1, mat, role="emitter", origin=(0, 0, 0)):
    """Open loft between two rings of (x, y) points with equal counts; mesh origin at `origin`."""
    ox, oy, oz = origin
    n = len(ring0)
    verts = [(x - ox, y - oy, z0 - oz) for x, y in ring0] + [(x - ox, y - oy, z1 - oz) for x, y in ring1]
    faces = [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
    ob = _mesh(name, verts, faces, mat, role=role)
    ob.location = origin
    return ob


# ---- B8_01 ---------------------------------------------------------------------------------
LAMP_01 = (-0.55, 1.7, 2.6)


def wafer(sc, rnd):
    C.set_world(top=(0.004, 0.005, 0.008), horizon=(0.002, 0.002, 0.003), bottom=(0.0, 0.0, 0.0))
    w = _wafer(mat=wafer_material(r=1.5, lamp=LAMP_01, strength=2.0))
    th0, th1 = math.radians(-8), math.radians(-3)
    _key(w, 1, rotation_euler=(0, 0, th0))
    _key(w, 60, rotation_euler=(0, 0, th1))
    _interp(w, "LINEAR")
    # the lamp whose diffraction the dies show (a real light at LAMP_01, above and behind the wafer)
    _aim_light("GratingLamp", LAMP_01, (0, 0, 0), 0.8, 260, (0.95, 0.97, 1.0))
    _softbox("SheenStrip", (-0.6, 4.6, 0.9), 2.2, 0.5, target=(0, 0, 0))
    _aim_light("EdgeRake", (3.2, -2.6, 0.18), (0.0, -1.4, 0.0), 1.5, 380, (0.75, 0.85, 1.0))
    _aim_light("NotchKick", (-1.6, -2.4, 0.25), (-0.2, -1.48, 0.0), 0.6, 60, (0.8, 0.88, 1.0))
    r = 1.5
    n1 = Vector((r * math.sin(th0), -r * math.cos(th0), 0.004))
    rad = Vector((math.sin(th0), -math.cos(th0), 0))
    tan = Vector((math.cos(th0), math.sin(th0), 0))
    loc1 = n1 + rad * 0.12 + tan * 0.30 + Vector((0, 0, 0.21))     # off the lamp's mirror direction
    B._camera("CamB8_01", [(1, tuple(n1), tuple(loc1), 100, 8.0),
                           (26, (n1.x * 0.6, n1.y * 0.55, 0.0), (0.35, -2.35, 0.36), 80, 8.0),
                           (60, (0.0, 0.05, 0.0), (0.75, -3.55, 0.62), 60, 8.0)])


# ---- B8_02 ---------------------------------------------------------------------------------
SLIT_L, SLIT_W, SLIT_SAG = 0.26, 0.02, 0.012          # 26 mm x 1.6 mm (drawn 2 mm), arc (r = 1.5 -> 100 mm/unit)
SLIT_C = (0.0825, 0.13)                               # slit centre: across the field x 0..0.165, y 0..0.26


def slit(sc, rnd):
    r = 1.5
    w = _wafer(r=r, mat=M.principled("WaferPlain", (0.3, 0.31, 0.35), metallic=0.7, roughness=0.15))
    top = 0.775 * r / 150 / 2
    _grid_lines("Field", r, top + 0.0006, M.emission("FieldLine", (0.42, 0.46, 0.62), 0.2), scan_axis="x")
    # the one field the slit crosses, a touch brighter
    fx0, fy0, fsx, fsy = 0.0, 0.0, 16.5 / 100, 26.0 / 100
    fm = M.emission("FieldHi", (0.55, 0.6, 0.85), 0.0)
    for k, (cx, cy, sx, sy) in enumerate(((fx0, fy0 + fsy / 2, 0.003, fsy), (fx0 + fsx, fy0 + fsy / 2, 0.003, fsy),
                                          (fx0 + fsx / 2, fy0, fsx, 0.003), (fx0 + fsx / 2, fy0 + fsy, fsx, 0.003))):
        hb = _box(f"FieldHi{k}", (cx, cy, top + 0.0008), (sx, sy, 0.0004), fm, role="emitter")
        _key(hb, 1, hide_render=True)
        _key(hb, 70, hide_render=False)
    M.set_emission_strength(fm, 70, 0.0)
    M.set_emission_strength(fm, 100, 0.9)
    # 1) the idea that is NOT how it works: a faint glow over the whole wafer at once (ghost)
    n = 96
    ring = [(r * math.cos(2 * math.pi * i / n), r * math.sin(2 * math.pi * i / n)) for i in range(n)]
    gmat = light_material("WholeWaferGhost", 0.0, height=1.6, edge=0.85)
    _loft("WholeWaferGhost", ring, top, ring, top + 1.6, gmat, origin=(0, 0, top))
    for f, v in ((1, 0.12), (12, 0.4), (58, 0.4), (82, 0.0)):
        _gain(gmat, f, v)
    # 2) what the projection optics deliver: light converging at NA 0.55 onto an arc slit (shaped upstream by the
    #    illuminator's arc-shaped field facets, S12). Cross-section at height h = slit grown by h tan(33.4 deg).
    h = 1.15
    d = h * math.tan(NA_HALF)
    ring0, _, xo = _arc_outline(SLIT_L, SLIT_W, SLIT_SAG, cx=SLIT_C[0], cy=SLIT_C[1])
    ring1 = []
    for (x, y) in ring0:
        yy = y - SLIT_C[1]
        side = -1 if x < SLIT_C[0] + xo(yy) else 1
        ys = yy * (SLIT_L / 2 + d) / (SLIT_L / 2)
        ring1.append((SLIT_C[0] + xo(yy) + side * (SLIT_W / 2 + d), SLIT_C[1] + ys))
    fmat = light_material("SlitFan", 0.0, height=h, edge=0.85)
    _loft("SlitFan", ring0, top + 0.001, ring1, top + h, fmat, origin=(0, 0, top + 0.001))
    for f, v in ((1, 0.0), (60, 0.0), (96, 0.42)):
        _gain(fmat, f, v)
    lm = M.emission("SlitOnWafer", (0.42, 0.18, 1.0), 0.0)
    _arc_strip("SlitLine", SLIT_L, SLIT_W, SLIT_SAG, top + 0.0012, lm, cx=SLIT_C[0], cy=SLIT_C[1])
    M.set_emission_strength(lm, 84, 0.0)
    M.set_emission_strength(lm, 104, 4.0)
    sx, sy = SLIT_C
    B._camera("CamB8_02", [(1, (0.0, 0.05, 0.45), (-4.9, -0.5, 4.2), 35, 11.0),
                           (66, (sx * 0.6, sy, 0.25), (-2.5, -0.15, 2.0), 35, 11.0),
                           (140, (sx, sy, 0.035), (-0.42, sy, 0.24), 35, 11.0)])


# ---- B8_03 / B8_04 -------------------------------------------------------------------------
# Units: wafer radius 1.3 = 150 mm (0.008667 units/mm). High-NA: field 16.5 mm along the scan (x) x 26 mm across (y);
# slit at the wafer 1.6 x 26 mm (drawn 2 mm wide), at the reticle 12.8 x 104 mm; reticle 152 mm square with the
# 132 x 104 mm image field; reticle travel per field = 8 x wafer travel (S2, HNA [A22] s.27).
U3 = 1.3 / 150.0
F_SCAN, F_CROSS = 16.5 * U3, 26.0 * U3
SLIT_W3 = 2.0 * U3
W_TRAVEL = F_SCAN + 1.6 * U3                 # field length + slit width
R_TRAVEL = 8 * W_TRAVEL
Z_WAF = -0.013                               # wafer top
Z_RET = 1.9                                  # reticle pattern face (down)


def scan(sc, rnd):
    floor = _box("Floor", (0, 0, -1.6), (60, 60, 0.1), M.principled("ClayFloor", (0.7, 0.7, 0.7)))
    # wafer side: planar-motor base, wafer stage floating above it (gap), chuck, wafer
    _box("PlanarBase", (0, 0, -0.6), (6.4, 6.4, 0.3), floor.data.materials[0], bevel=0.04)
    ws = _apply_scale(_box("WaferStage", (0, 0, -0.225), (3.0, 3.0, 0.35), floor.data.materials[0], bevel=0.05))
    ch = _cyl("Chuck", 1.33, 0.03, (0, 0, -0.035), floor.data.materials[0], verts=128)
    _parent(ch, ws)
    wf = _cyl("WaferDisc", 1.3, 0.775 * U3, (0, 0, Z_WAF - 0.775 * U3 / 2), M.principled("WaferClay", (0.8, 0.8, 0.8)),
              verts=160)
    _parent(wf, ws)
    # true-scale half-field grid on the wafer (kept out of the clay override: role emitter, plain grey material)
    for ob in _grid_lines("Grid", 1.3, Z_WAF + 0.0004, M.principled("GridGrey", (0.22, 0.22, 0.24), roughness=0.6),
                          width=0.0035):
        _parent(ob, ws)
    # reticle side: maglev stage between two linear-motor tracks (gap, no contact), e-clamp under it, reticle
    # pattern-side down (S1, S11)
    rs = _apply_scale(_box("ReticleStage", (0, 0, Z_RET + 0.06 + 0.15 + 0.05), (2.3, 2.0, 0.3), floor.data.materials[0],
                           bevel=0.04))
    clamp = _box("EClamp", (0, 0, Z_RET + 0.085), (1.45, 1.45, 0.05), floor.data.materials[0])
    _parent(clamp, rs)
    ret = _box("Reticle", (0, 0, Z_RET + 0.03), (152 * U3, 152 * U3, 0.06), floor.data.materials[0], bevel=0.004)
    _parent(ret, rs)
    pat = M.principled("ReticlePattern", (0.22, 0.22, 0.25), metallic=0.3, roughness=0.35)
    nb = _NB(pat)
    bsdf = nb.N["Principled BSDF"]
    tcn = nb.N.new("ShaderNodeTexCoord")
    wave = nb.N.new("ShaderNodeTexWave")
    wave.inputs["Scale"].default_value = 14.0
    nb.L(tcn.outputs["Object"], wave.inputs["Vector"])
    nb.L(nb.mix_rgb(nb.math("GREATER_THAN", wave.outputs["Fac"], 0.55), (0.42, 0.42, 0.46, 1), (0.16, 0.16, 0.19, 1)),
         bsdf.inputs["Base Color"])
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, Z_RET - 0.0008))
    pp = bpy.context.object
    pp.name = "ReticleImageField"
    pp.scale = (132 * U3, 104 * U3, 1)
    pp.rotation_euler = (math.pi, 0, 0)                      # faces down
    pp.data.materials.append(pat)
    styles.tag(pp, "emitter")
    _parent(pp, rs)
    for y in (-1, 1):
        _box(f"Track{y}", (0, y * (1.0 + 0.05 + 0.15), Z_RET + 0.2), (4.8, 0.3, 0.2), floor.data.materials[0],
             bevel=0.03)
        for x in (-2.3, 2.3):                                    # tracks stand on the machine frame
            _box(f"Post{y}{x}", (x, y * 1.2, (Z_RET + 0.1 - 1.55) / 2), (0.22, 0.22, Z_RET + 0.1 + 1.55),
                 floor.data.materials[0])
    # the slit: fixed in space. A tapered light sheet from the reticle (104 x 12.8 mm) to the wafer (26 x 1.6 mm):
    # 4x across the scan, 8x along it (anamorphic; the path through the six mirrors is not drawn, 示意)
    rw, rl = 12.8 * U3 / 2, 104 * U3 / 2
    ww, wl = SLIT_W3 / 2, F_CROSS / 2
    ring_top = [(-rw, -rl), (rw, -rl), (rw, rl), (-rw, rl)]
    ring_bot = [(-ww, -wl), (ww, -wl), (ww, wl), (-ww, wl)]
    smat = light_material("SlitSheet", 2.2, height=Z_RET - Z_WAF + 0.2, edge=0.5)
    sheet = _loft("SlitSheet", ring_bot, Z_WAF + 0.001, ring_top, Z_RET - 0.002, smat, origin=(0, 0, Z_WAF))
    sheet.data.polygons.foreach_set("use_smooth", [False] * len(sheet.data.polygons))
    _box("SlitFoot", (0, 0, Z_WAF + 0.0012), (SLIT_W3, F_CROSS, 0.0004), M.emission("SlitFootMat", (0.6, 0.4, 1.0), 5.0),
         role="emitter")
    _box("SlitHead", (0, 0, Z_RET - 0.003), (2 * rw, 2 * rl, 0.0004), M.emission("SlitHeadMat", (0.6, 0.4, 1.0), 3.0),
         role="emitter")
    # fields exposed one after the other, alternating scan direction (scan up / scan down, US8711329B2);
    # between scans the wafer stage steps one field across the scan (y)
    fields = [(F_SCAN / 2, -1.5 * F_CROSS), (F_SCAN / 2, -0.5 * F_CROSS), (F_SCAN / 2, 0.5 * F_CROSS),
              (F_SCAN / 2, 1.5 * F_CROSS)]
    plan = [(4, 40, +1), (52, 88, -1), (100, 136, +1), (172, 262, -1)]     # last one is B8_04 (sim 161-)
    expo = M.emission("Latent", (0.4, 0.2, 1.0), 2.2)
    ws_keys, rs_keys = [], []
    for k, ((fxc, fyc), (f0, f1, d)) in enumerate(zip(fields, plan)):
        half = W_TRAVEL / 2
        x_mid = -fxc                                         # wafer-stage x with the field centre under the slit
        xs, xe = x_mid - d * half, x_mid + d * half
        ws_keys += [(f0, (xs, -fyc)), (f1, (xe, -fyc))]
        rs_keys += [(f0, -8 * (xs - x_mid)), (f1, -8 * (xe - x_mid))]
        # latent image: grows from the field's leading edge, opposite to the wafer's motion
        hy = F_CROSS / 2 - 0.006                             # small inset so neighbouring fields read apart
        verts = [(0, -hy, 0), (-d, -hy, 0), (-d, hy, 0), (0, hy, 0)]
        strip = _mesh(f"Field{k}", verts, [(0, 1, 2, 3)], expo, role="emitter")
        strip.location = (fxc + d * (F_SCAN / 2 - 0.004), fyc, Z_WAF + 0.0009)
        _parent(strip, ws)
        _key(strip, 1, scale=(1e-4, 1, 1))
        _key(strip, f0, scale=(1e-4, 1, 1))
        _key(strip, f1, scale=(F_SCAN - 0.008, 1, 1))
        _interp(strip, "LINEAR")
    for f, (x, y) in ws_keys:
        _key(ws, f, location=(x, y, -0.225))
    for f, x in rs_keys:
        _key(rs, f, location=(x, 0, rs.location.z))
    _interp(ws, "LINEAR")
    _interp(rs, "LINEAR")
    for ob in (ws, rs):                                      # ease the steps and the reversals between scans
        for fc in C.fcurves(ob.animation_data.action):
            pts = fc.keyframe_points
            for i, kp in enumerate(pts):
                if i % 2 == 1 and i + 1 < len(pts):
                    kp.interpolation = "BEZIER"
    # B8_04: speed arrows 8 : 1, stuck to the stages' front faces, pointing the way each stage moves
    for name, parent, length, col, sign in (("RetArrow", rs, 1.6, ORANGE, +1), ("WafArrow", ws, 0.2, CYAN, -1)):
        mat = M.emission(name + "Mat", tuple(c * c for c in col), 1.6)
        hd = min(0.16, 0.4 * length)
        y_face = -(0.82 if parent is rs else 1.32)                    # local: flat on the stage top, front edge
        z_top = (0.15 if parent is rs else 0.175) + 0.016
        shaft = _box(name, (0, 0, 0), (length - hd, 0.06, 0.03), mat, role="emitter")
        _apply_scale(shaft)
        bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=0.08, depth=hd, rotation=(0, sign * math.pi / 2, 0))
        head = bpy.context.object
        head.name = name + "Head"
        head.data.materials.append(mat)
        styles.tag(head, "emitter")
        for o, lx in ((shaft, sign * (length - hd) / 2), (head, sign * (length - hd / 2))):
            o.parent = parent
            o.matrix_parent_inverse.identity()
            o.location = (lx, y_face, z_top)
            _key(o, 1, hide_render=True)
            _key(o, 166, hide_render=False)
    sc.render.use_motion_blur = True
    sc.render.motion_blur_shutter = 1.0
    B._area("ClayKey", (5, -6, 8), (0.8, 0, 0.6), 8, 1800, (1.0, 0.98, 0.95))
    B._area("ClayUnder", (3, -5, -0.4), (math.radians(100), 0, math.radians(30)), 6, 500, (1.0, 0.98, 0.95))
    B._camera("CamB8_03", [(1, (0.15, 0, 0.8), (4.6, -7.4, 3.6), 35, 8.0), (154, (0.15, 0, 0.8), (4.1, -7.7, 3.5), 35, 8.0)])
    B._camera("CamB8_04", [(161, (-0.35, 0, 0.9), (2.3, -5.8, 3.0), 35, 8.0), (262, (0.45, 0, 0.9), (3.1, -5.8, 3.0), 35, 8.0),
                           (300, (0.45, 0, 0.9), (3.1, -5.8, 3.0), 35, 8.0)])


# ---- B8_07 / B8_08 -------------------------------------------------------------------------
def mask_material(name="EUVMask"):
    """EUV reticle seen on its pattern side: bright Mo/Si multilayer (plain metal, no rainbow) with a dark absorber
    pattern inside the 132 x 104 mm image field (dies with dense lines), a dark border round the field, bare
    multilayer outside. Plane object coords: +-0.5 = the 152 mm plate edge."""
    m = M.principled(name, (0.62, 0.62, 0.65), metallic=1.0, roughness=0.07)
    nb = _NB(m)
    b = nb.N["Principled BSDF"]
    tc = nb.N.new("ShaderNodeTexCoord")
    sep = nb.N.new("ShaderNodeSeparateXYZ")
    nb.L(tc.outputs["Object"], sep.inputs[0])
    ax = nb.math("ABSOLUTE", sep.outputs["X"])
    ay = nb.math("ABSOLUTE", sep.outputs["Y"])
    hx, hy = 66 / 152, 52 / 152
    inside = nb.math("MULTIPLY", nb.math("LESS_THAN", ax, hx), nb.math("LESS_THAN", ay, hy))
    border = nb.math("SUBTRACT", nb.math("MULTIPLY", nb.math("LESS_THAN", ax, hx + 0.02),
                                         nb.math("LESS_THAN", ay, hy + 0.02)), inside)
    brick = nb.N.new("ShaderNodeTexBrick")                   # dies, 4 x 4 in the field
    brick.offset = 0.0
    brick.inputs["Scale"].default_value = 1.0
    brick.inputs["Mortar Size"].default_value = 0.006
    brick.inputs["Brick Width"].default_value = 2 * hx / 4
    brick.inputs["Row Height"].default_value = 2 * hy / 4
    nb.L(tc.outputs["Object"], brick.inputs["Vector"])
    lines = nb.N.new("ShaderNodeTexWave")                    # dense lines inside each die, two orientations
    lines.inputs["Scale"].default_value = 70.0
    lines.inputs["Distortion"].default_value = 0.0
    lines.wave_profile = "SAW"
    nb.L(tc.outputs["Object"], lines.inputs["Vector"])
    lines2 = nb.N.new("ShaderNodeTexWave")
    lines2.inputs["Scale"].default_value = 46.0
    lines2.bands_direction = "Y"
    nb.L(tc.outputs["Object"], lines2.inputs["Vector"])
    blocks = nb.N.new("ShaderNodeTexVoronoi")
    blocks.feature = "F1"
    blocks.distance = "CHEBYCHEV"
    blocks.inputs["Scale"].default_value = 14.0
    nb.L(tc.outputs["Object"], blocks.inputs["Vector"])
    sel = nb.math("GREATER_THAN", blocks.outputs["Color"], 0.5)
    l1 = nb.math("GREATER_THAN", lines.outputs["Fac"], 0.5)
    l2 = nb.math("GREATER_THAN", lines2.outputs["Fac"], 0.5)
    lin = nb.N.new("ShaderNodeMix")
    lin.data_type = "FLOAT"
    nb.L(sel, lin.inputs["Factor"])
    nb.L(l1, lin.inputs["A"])
    nb.L(l2, lin.inputs["B"])
    in_die = nb.math("LESS_THAN", brick.outputs["Fac"], 0.5)         # Fac = 1 in the mortar (die streets)
    absorber = nb.math("MAXIMUM", nb.math("MULTIPLY", nb.math("MULTIPLY", inside, in_die), lin.outputs[0]), border)
    nb.L(nb.mix_rgb(absorber, (0.62, 0.62, 0.65, 1), (0.025, 0.025, 0.03, 1)), b.inputs["Base Color"])
    nb.L(nb.math("MULTIPLY_ADD", absorber, 0.4, 0.07), b.inputs["Roughness"])
    nb.L(nb.math("MULTIPLY_ADD", absorber, -0.8, 1.0), b.inputs["Metallic"])
    return m


def _ghost_car(mat_glass, mat_wire):
    parts = []
    body = _box("CarBody", (0, 0, 0.35), (4.3, 1.8, 0.7), mat_glass, role="emitter", bevel=0.18)
    cabin = _box("CarCabin", (-0.2, 0, 0.95), (2.3, 1.6, 0.6), mat_glass, role="emitter", bevel=0.2)
    parts += [body, cabin]
    for sx in (-1.35, 1.35):
        for sy in (-0.85, 0.85):
            parts.append(_cyl(f"Wheel{sx}{sy}", 0.36, 0.25, (sx, sy, 0.15), mat_glass, rot=(math.pi / 2, 0, 0),
                              role="emitter", verts=24))
    for p in list(parts):                                          # wireframe twin on every part
        w = p.copy()
        w.data = p.data.copy()
        bpy.context.scene.collection.objects.link(w)
        w.modifiers.new("Wire", "WIREFRAME").thickness = 0.015
        w.data.materials.clear()
        w.data.materials.append(mat_wire)
        styles.tag(w, "emitter")
        parts.append(w)
    bpy.ops.object.empty_add(location=(0, 0, 0))
    root = bpy.context.object
    root.name = "GhostCar"
    for p in parts:
        p.parent = root
    return root, parts


def car(sc, rnd):
    """NXE reticle stage (the >15 g, >10,000 N stage of S1). Units 1 = 100 mm. The stage floats between two linear-motor
    tracks with a visible gap (maglev, S1); the reticle hangs under it on an electrostatic clamp, pattern down (S11)."""
    C.set_world(top=(0.006, 0.007, 0.011), horizon=(0.003, 0.0035, 0.005), bottom=(0.0, 0.0, 0.001))
    dark = M.dark_anodized("StageDark")
    steel = M.polished_steel("StageSteel", 0.22)
    ceramic = M.principled("ClampCeramic", (0.06, 0.065, 0.07), metallic=0.0, roughness=0.3)
    coil = M.principled("CoilPlate", (0.35, 0.18, 0.08), metallic=0.9, roughness=0.35)
    magnet = M.principled("MagnetTile", (0.1, 0.1, 0.11), metallic=0.85, roughness=0.3)
    stage = _apply_scale(_box("ReticleStage", (0, 0, 0), (4.4, 3.0, 0.5), dark, bevel=0.05))
    for k, x in enumerate((-1.45, 0.0, 1.45)):                     # ribbed top: a lightweight stage frame
        _parent(_box(f"Rib{k}", (x, 0, 0.27), (0.12, 2.8, 0.04), steel, bevel=0.01), stage)
    for y in (-1, 1):
        _parent(_box(f"Wing{y}", (0, y * 1.75, 0.34), (3.8, 0.5, 0.1), coil, bevel=0.01), stage)  # motor coils
        _box(f"Track{y}", (0, y * 2.2, 0.34), (7.4, 0.36, 0.42), dark, bevel=0.03)              # magnet tracks
        for k in range(20):
            _box(f"Mag{y}{k}", (-3.47 + 0.365 * k, y * 2.015, 0.34), (0.32, 0.012, 0.3), magnet, bevel=0.004)
    cl = _box("EClamp", (0, 0, -0.29), (1.75, 1.75, 0.08), ceramic, bevel=0.01)
    _parent(cl, stage)
    plate = _box("Mask", (0, 0, -0.3625), (1.52, 1.52, 0.0635), M.principled("MaskGlass", (0.1, 0.1, 0.11), roughness=0.2),
                 bevel=0.004)
    _parent(plate, stage)
    bpy.ops.mesh.primitive_plane_add(size=1.52, location=(0, 0, -0.3945))
    pat = bpy.context.object
    pat.name = "MaskPattern"
    pat.rotation_euler = (math.pi, 0, 0)                           # pattern side faces down
    pat.scale = (1, 1, 1)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    pat.data.materials.append(mask_material())
    styles.tag(pat, "structure")
    # object coords +-0.5 at the plate edge: rescale the mesh to unit size and the object to 1.52
    for v in pat.data.vertices:
        v.co.x /= 1.52
        v.co.y /= 1.52
    pat.scale = (1.52, 1.52, 1)
    _parent(pat, stage)
    # chamber: back wall with panel seams, a frame beam overhead, floor far below (reads as a space, not a void)
    wall = M.principled("ChamberWall", (0.05, 0.055, 0.06), metallic=0.5, roughness=0.45)
    for i in range(8):
        _box(f"WallPanel{i}", (-10.5 + 3.0 * i, 8.0, 0.5), (2.95, 0.1, 9.0), wall)
    _box("ChamberFloor", (0, 0, -4.0), (90, 90, 0.1), wall)
    # timing: strokes until the car, impact ~1.25 s before the end of B8_07, stage still from then on
    n7 = min(_frames("B8_07", 203), B8_08_START - 40)
    imp = n7 - 30
    x_amp = 0.7                                                    # +-70 mm: 132 mm field + slit (NXE, 4x)
    f, s = 1, 1
    while f + 14 <= imp - 26:
        _key(stage, f, location=(s * x_amp, 0, 0))
        f += 14
        s = -s
    _key(stage, f, location=(s * x_amp, 0, 0))
    _key(stage, imp - 12, location=(0, 0, 0))
    _key(stage, B8_08_START + 120, location=(0, 0, 0))
    sc.render.use_motion_blur = True
    sc.render.motion_blur_shutter = 0.5
    # ghost car
    glass = bpy.data.materials.new("GhostGlass")
    glass.use_nodes = True
    nb = _NB(glass)
    nb.N.clear()
    out = nb.N.new("ShaderNodeOutputMaterial")
    lw = nb.N.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.2
    em = nb.N.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (0.55, 0.75, 1.0, 1)
    nb.L(nb.math("MULTIPLY", lw.outputs["Facing"], 1.2), em.inputs["Strength"])
    tr = nb.N.new("ShaderNodeBsdfTransparent")
    add = nb.N.new("ShaderNodeAddShader")
    nb.L(tr.outputs[0], add.inputs[0])
    nb.L(em.outputs[0], add.inputs[1])
    nb.L(add.outputs[0], out.inputs["Surface"])
    glass.surface_render_method = "BLENDED"
    wire = M.emission("GhostWire", (0.6, 0.8, 1.0), 2.5)
    root, parts = _ghost_car(glass, wire)
    top = 0.25
    _key(root, 1, location=(0.0, 0.0, 9.0), scale=(1, 1, 1))
    _key(root, imp - 16, location=(0.0, 0.0, 9.0), scale=(1, 1, 1))
    _key(root, imp, location=(0.0, 0.0, top), scale=(1, 1, 1))
    _key(root, imp + 10, location=(0.0, 0.0, top), scale=(1.12, 1.12, 0.45))
    for fc in C.fcurves(root.animation_data.action):
        for kp in fc.keyframe_points:
            if imp - 16 <= kp.co[0] < imp:
                kp.interpolation = "QUAD"
                kp.easing = "EASE_IN"
    for p in parts:
        _key(p, 1, hide_render=False)
        _key(p, imp + 12, hide_render=False)
        _key(p, imp + 14, hide_render=True)
    dot = M.emission("Shard", (0.65, 0.85, 1.0), 6.0)
    for k in range(160):                                           # shards of light
        d = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(0.0, 0.8))).normalized()
        start = Vector((rnd.uniform(-2, 2), rnd.uniform(-0.9, 0.9), top + rnd.uniform(0, 0.9)))
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.02, location=tuple(start))
        sh = bpy.context.object
        sh.data.materials.append(dot)
        styles.tag(sh, "emitter")
        _key(sh, 1, hide_render=True)
        _key(sh, imp + 12, hide_render=False, location=tuple(start))
        _key(sh, imp + 60, location=tuple(start + d * rnd.uniform(1.5, 4.0)))
        _key(sh, imp + 61, hide_render=True)
    ring_m = M.emission("ImpactRing", (0.7, 0.85, 1.0), 0.0)
    bpy.ops.mesh.primitive_torus_add(major_radius=1.0, minor_radius=0.02, location=(0, 0, top + 0.02))
    ring = bpy.context.object
    ring.data.materials.append(ring_m)
    styles.tag(ring, "emitter")
    _key(ring, imp, scale=(0.3, 0.3, 1))
    _key(ring, imp + 30, scale=(2.6, 2.6, 1))
    M.set_emission_strength(ring_m, imp - 1, 0.0)
    M.set_emission_strength(ring_m, imp + 1, 8.0)
    M.set_emission_strength(ring_m, imp + 30, 0.0)
    # B8_08: replay, car frozen in its squash, an orange stress wave runs across the stage's underside and stops at
    # the clamp, i.e. at the mask edge (metaphor for "no slip, no distortion", S1)
    S = B8_08_START
    for p in parts:
        _key(p, S - 1, hide_render=True)
        _key(p, S, hide_render=False)
    _key(root, S - 1, location=(0.0, 0.0, top), scale=(1.12, 1.12, 0.45))
    _key(root, S, location=(0.0, 0.0, top), scale=(1.06, 1.06, 0.7))
    st_m = M.emission("StressWave", ORANGE, 0.0)
    wv = []
    hw, th = 0.5, 0.035                                            # unit square frame, scaled
    for k, (cx, cy, sx, sy) in enumerate(((0, hw, 2 * hw, th), (0, -hw, 2 * hw, th), (hw, 0, th, 2 * hw), (-hw, 0, th, 2 * hw))):
        wv.append(_box(f"Stress{k}", (cx, cy, 0), (sx, sy, 0.01), st_m, role="emitter"))
    bpy.ops.object.empty_add(location=(0, 0, -0.256))
    wave = bpy.context.object
    wave.name = "StressWaveRoot"
    for o in wv:
        o.parent = wave
    _parent(wave, stage)
    _key(wave, S + 2, scale=(4.3, 2.9, 1))
    _key(wave, S + 70, scale=(1.76, 1.76, 1))
    M.set_emission_strength(st_m, S + 1, 0.0)
    M.set_emission_strength(st_m, S + 6, 9.0)
    M.set_emission_strength(st_m, S + 64, 5.0)
    M.set_emission_strength(st_m, S + 76, 0.0)
    # light: key from above-front, a long strip for the stage's top edges, and a card BELOW the mask that its
    # multilayer reflects towards the low cameras (that is what makes the absorber pattern readable)
    _softbox("StageBox", (-3, -2, 6), 6, 2.0)
    _aim_light("StageKey", (4, -5, 6), (0, 0, 0), 4, 900, (0.85, 0.9, 1.0))
    _aim_light("WallWash", (0, 4.0, 5.5), (0, 8.0, 0), 8, 110, (0.4, 0.55, 0.9))
    _softbox("UnderCard", (2.4, 3.2, -1.9), 3.5, 6.0, target=(0, 0, -0.4))
    _softbox("UnderCard7", (-0.9, 7.5, -1.2), 5.0, 3.0, target=(0, 0, -0.4))
    _aim_light("RimL", (-6, 3, 1.0), (0, 0, 0), 2, 500, (0.6, 0.75, 1.0))
    B._camera("CamB8_07", [(1, (0.6, 0, 0.0), (-5.4, -1.25, -1.2), 28, 5.6), (imp - 20, (0.6, 0, 0.55), (-6.2, -1.35, -1.15), 28, 5.6),
                           (n7, (0.6, 0, 0.55), (-6.3, -1.35, -1.15), 28, 5.6)])
    B._camera("CamB8_08", [(S, (0.0, 0.0, -0.39), (-2.5, -2.9, -1.75), 100, 2.2),
                           (S + 90, (0.12, 0.0, -0.39), (-2.25, -3.05, -1.7), 100, 2.2)], focus=pat)


# ---- B8_10 ---------------------------------------------------------------------------------
def sync(sc, rnd):
    """High-NA layout from build_machine (source on +x). The scan axis is x. Reticle stage and wafer stage move in
    opposite directions, travel 8 : 1 (8x in the scan direction, S2); the light path (BM.PATH) stays fixed, every
    turn of it on a mirror or on the reticle. Reticle travel is kept inside the reticle so the beam never leaves it."""
    path, pmat = BM.machine()
    rs = bpy.data.objects["ReticleStage"]
    rt = bpy.data.objects["Reticle"]
    movers_r = [rs, rt]
    movers_w = [bpy.data.objects[n] for n in ("WaferStage", "Chuck", "Wafer")]
    tick = M.emission("Tick", CYAN, 1.0)
    # build_machine bakes object locations into the meshes, so place the tick rings from its constants: on the front
    # faces of the reticle stage (1.8 deep, centre RETICLE z + 0.27) and of the wafer stage (2.8 deep, centre z -1.35)
    for movers, loc in ((movers_r, (BM.RETICLE[0] + 0.85, -0.915, BM.RETICLE[2] + 0.27)), (movers_w, (0.95, -1.415, -1.35))):
        bpy.ops.mesh.primitive_torus_add(major_radius=0.09, minor_radius=0.014, location=loc)
        t = bpy.context.object
        t.rotation_euler = (math.pi / 2, 0, 0)
        t.data.materials.append(tick)
        styles.tag(t, "emitter")
        movers.append(t)
    amp_r = 0.24                                    # reticle 0.6 wide: the fixed beam spot stays on it
    amp_w = amp_r / 8
    base = {o.name: o.location.copy() for o in movers_r + movers_w}
    period = 18
    n = _frames("B8_10", 130)
    for k, f in enumerate(range(1, n + period, period)):
        s = 1 if k % 2 == 0 else -1
        for o in movers_r:
            loc = base[o.name].copy()
            loc.x -= s * amp_r
            _key(o, f, location=tuple(loc))
        for o in movers_w:
            loc = base[o.name].copy()
            loc.x += s * amp_w
            _key(o, f, location=tuple(loc))
        M.set_emission_strength(tick, f, 30.0)
        M.set_emission_strength(tick, f + 4, 1.0)
    sc.render.use_motion_blur = True
    sc.render.motion_blur_shutter = 0.6
    B._area("MKey", (2, -10, 8), (0.9, 0, 0), 16, 2500, (0.8, 0.85, 1.0))
    cx, cy, cz = BM.CENTER
    B._camera("CamB8_10", [(1, (0.15, 0, 0.75), (0.9, -4.6, 0.85), 35, 5.6),
                           (n, (cx + 0.1, 0, cz + 0.5), (cx + 0.4, -14.6, cz + 2.3), 35, 5.6)])


# ---- B8_14 ---------------------------------------------------------------------------------
def maglev(sc, rnd):
    """Wafer table floating over a planar motor (S11 'Dual planar stage + balance mass', S3 'magnetically levitating
    wafer tables'). Units 1 = 100 mm. Magnet plate of square tiles on the balance-mass block; the table's coil layer
    rides ~2.5 mm above it (gap exaggerated to read); wafer on the chuck. The table scans with motion blur; the
    camera tracks its edge. No lamps, no contact actuators."""
    C.set_world(top=(0.012, 0.014, 0.02), horizon=(0.005, 0.006, 0.009), bottom=(0.001, 0.001, 0.002))
    dark = M.dark_anodized("BalanceMass")
    steel = M.polished_steel("TableSteel", 0.2)
    ceramic = M.principled("TableCeramic", (0.22, 0.225, 0.235), roughness=0.4)
    magnet = M.principled("Magnet", (0.07, 0.07, 0.08), metallic=0.85, roughness=0.28)
    magnet2 = M.principled("Magnet2", (0.12, 0.12, 0.13), metallic=0.85, roughness=0.22)
    coil = M.principled("CoilLayer", (0.03, 0.03, 0.035), roughness=0.5)
    _box("BalanceMass", (0, 0, -0.45), (22, 9, 0.8), dark, bevel=0.03)
    for i in range(52):                                         # Halbach-style checkerboard of magnets
        for j in range(20):
            x, y = -10.2 + 0.4 * i, -3.8 + 0.4 * j
            _box(f"M{i}_{j}", (x, y, -0.03), (0.385, 0.385, 0.04), magnet if (i + j) % 2 else magnet2, bevel=0.004)
    table = _apply_scale(_box("WaferTable", (0, 0, 0.29), (4.0, 4.0, 0.5), ceramic, bevel=0.04))
    _parent(_box("Coils", (0, 0, 0.025), (3.9, 3.9, 0.03), coil, bevel=0.005), table)
    _parent(_cyl("Chuck", 1.55, 0.04, (0, 0, 0.56), steel, verts=128), table)
    upm = 1.5 / 150
    wf = _wafer("Wafer", r=1.5, loc=(0, 0, 0.58 + 0.775 * upm / 2), mat=wafer_material(r=1.5, lamp=(-3.0, 4.0, 3.0),
                                                                                         strength=2.0))
    _parent(wf, table)
    # motion: scans along x with turnarounds, a step in y half way
    n = _frames("B8_14", 160)
    f, s, k = 1, 1, 0
    while f <= n + 20:
        _key(table, f, location=(s * 1.1, -0.12 * (k // 3), 0.29))
        f += 20
        s = -s
        k += 1
    sc.render.use_motion_blur = True
    sc.render.motion_blur_shutter = 0.8
    _softbox("TopBox", (-1.0, -2.0, 5.0), 6, 2.0)
    _aim_light("Key", (-3.0, -5.0, 2.5), (0, 0, 0.2), 3, 260, (0.85, 0.9, 1.0))
    _aim_light("GapLight", (-1.0, -6.0, 0.0), (0, 0, 0.0), 4, 160, (0.7, 0.8, 1.0), size_y=0.3)
    _aim_light("BackGap", (1.0, 6.0, 0.02), (0, 0, 0.0), 6, 120, (0.6, 0.75, 1.0), size_y=0.2)
    _aim_light("GratingLamp", (-3.0, 4.0, 3.0), (0, 0, 0.6), 1.0, 300, (0.95, 0.97, 1.0))
    # camera rides with the table (child of an empty that follows its x)
    bpy.ops.object.empty_add(location=(0, 0, 0))
    rig = bpy.context.object
    rig.name = "CamRig"
    rig.constraints.new("COPY_LOCATION").target = table
    rig.constraints[0].use_y = rig.constraints[0].use_z = False
    cam = B._camera("CamB8_14", [(1, (-0.3, -1.0, 0.4), (-3.4, -8.4, 2.6), 60, 8.0),
                                 (n, (-1.0, -2.0, 0.08), (-3.0, -8.2, 0.55), 85, 5.6)])
    cam.parent = rig
    bpy.data.objects["CamB8_14Aim"].parent = rig


# ---- B8_15 ---------------------------------------------------------------------------------
def layers(sc, rnd):
    clay = M.principled("ClayLayer", (0.7, 0.7, 0.7))
    _box("Floor", (0, 0, -0.05), (40, 40, 0.1), clay)
    n = 8
    off = 0.04                                                   # overlay error drawn as a lateral shift (放大示意)
    for k in range(n):
        z = 0.12 + k * 0.22
        lay = _apply_scale(_box(f"Layer{k}", (0, 0, z), (3.2, 2.2, 0.2), clay, bevel=0.01))
        for g in range(6 + (k % 3) * 3):
            gx = -1.4 + g * (2.8 / (5 + (k % 3) * 3))
            gr = _box(f"Groove{k}_{g}", (0, 0, 0), (0.06 if k % 2 else 2.8, 2.0 if k % 2 else 0.06, 0.03), clay)
            gr.parent = lay
            gr.location = (gx if k % 2 else 0, 0 if k % 2 else -0.9 + g * (1.8 / (5 + (k % 3) * 3)), 0.11)
        f0 = 4 + 12 * k
        x_land = off if k == n - 1 else 0.0
        _key(lay, f0, location=(x_land, 0, z + 3.5))
        _key(lay, f0 + 12, location=(x_land, 0, z))
    # the offset marker: a short horizontal bar at the seam, from the lower layer's edge to the top layer's edge,
    # with end ticks (front face, front-right corner)
    zs = 0.12 + (n - 1) * 0.22 - 0.1
    cyan = M.emission("BarCyan", CYAN, 6.0)
    parts = [_box("OffsetBar", (1.6 + off / 2, -1.105, zs), (off, 0.004, 0.004), cyan, role="emitter"),
             _box("OffsetTickA", (1.6, -1.105, zs), (0.003, 0.004, 0.05), cyan, role="emitter"),
             _box("OffsetTickB", (1.6 + off, -1.105, zs), (0.003, 0.004, 0.05), cyan, role="emitter")]
    for p in parts:
        _key(p, 1, hide_render=True)
        _key(p, 110, hide_render=False)
    B._area("ClayKey", (5, -6, 8), (0.8, 0, 0.6), 8, 1800, (1.0, 0.98, 0.95))
    B._camera("CamB8_15", [(1, (0, 0, 1.2), (6.0, -7.0, 4.0), 40, 8.0), (100, (0.6, -0.6, 1.3), (4.4, -5.6, 2.4), 40, 8.0),
                           (183, (1.62, -1.1, zs), (1.9, -2.15, zs + 0.12), 85, 4.0)])


# ---- B8_16 ---------------------------------------------------------------------------------
def dual(sc, rnd):
    C.set_world(top=(0.9, 0.91, 0.93), horizon=(0.78, 0.79, 0.82), bottom=(0.6, 0.61, 0.64))
    _box("DualBase", (0, 0, -0.5), (9, 4.5, 0.8), M.principled("BasePanel", (0.78, 0.8, 0.82), metallic=0.2,
                                                               roughness=0.45), role="shell", bevel=0.15)
    steel = M.polished_steel("DualSteel", 0.25)
    wmat = M.principled("DualWaferSi", (0.18, 0.19, 0.22), metallic=0.7, roughness=0.15)
    r = 0.95
    upm = r / 150
    stages = []
    for k, x in enumerate((-2.2, 2.2)):
        st = _box(f"Stage{k}", (x, 0, 0.1), (2.4, 2.4, 0.35), steel, bevel=0.04)
        w = _wafer(f"DualWafer{k}", r=r, loc=(x, 0, 0.275 + 0.775 * upm / 2), mat=wmat, verts=128)
        _parent(w, st)
        stages.append(st)
    # exposure slit (left): the converging fan onto a 26 mm arc slit (scaled to this wafer), fixed in space
    zt = 0.275 + 0.775 * upm
    L, W_ = 26 * upm, 0.02
    h = 1.6
    d = h * math.tan(NA_HALF) * 0.35                              # fan narrowed: its top would hide the stage
    ring0, _, xo = _arc_outline(L, W_, 0.006, cx=-2.2, cy=0.0)
    ring1 = []
    for (x, y) in ring0:
        side = -1 if x < -2.2 + xo(y) else 1
        ring1.append((-2.2 + xo(y) + side * (W_ / 2 + d), y * (L / 2 + d) / (L / 2)))
    fan = _loft("ExpSlit", ring0, zt + 0.001, ring1, zt + h, M.emission("ExpSlitMat", VIOLET, 6.0), role="rays",
                origin=(-2.2, 0, zt))
    fan.data.polygons.foreach_set("use_smooth", [False] * len(fan.data.polygons))
    dots = M.emission("MetroDots", CYAN, 6.0)
    for i in range(6):
        for j in range(6):
            bpy.ops.mesh.primitive_uv_sphere_add(radius=0.025, location=(2.2 - 0.5 + 0.2 * i, -0.5 + 0.2 * j, zt + 0.02))
            dd = bpy.context.object
            dd.data.materials.append(dots)
            styles.tag(dd, "emitter")                          # keeps metrology cyan (xray recolours 'rays' violet)
    a, b_ = stages
    # exposure station: meander, scan one field (16.5 mm) along x, step one field (26 mm) along y, scan back
    fs, fc = 16.5 * upm, 26 * upm
    f = 1
    for k in range(9):
        y = (k - 4) * fc
        x0 = -2.2 + (-1) ** k * fs / 2
        _key(a, f, location=(x0, -y, 0.1))
        _key(a, f + 5, location=(x0 - (-1) ** k * fs, -y, 0.1))
        f += 8
    _key(a, 76, location=(-2.2, 0, 0.1))
    for f_, dx in ((1, -0.4), (20, 0.4), (40, -0.4), (60, 0.4), (76, 0.0)):  # measurement: the stage sweeps the sensors
        _key(b_, f_, location=(2.2 + dx, 0, 0.1))
    _key(a, 96, location=(0.0, -1.0, 0.1))
    _key(b_, 96, location=(0.0, 1.0, 0.1))
    _key(a, 120, location=(2.2, 0, 0.1))
    _key(b_, 120, location=(-2.2, 0, 0.1))
    f = 128
    for k in range(7):
        y = (k - 3) * fc
        x0 = -2.2 + (-1) ** k * fs / 2
        _key(b_, f, location=(x0, -y, 0.1))
        _key(b_, f + 5, location=(x0 - (-1) ** k * fs, -y, 0.1))
        f += 8
    for f_, dx in ((140, -0.4), (160, 0.4), (180, -0.4)):
        _key(a, f_, location=(2.2 + dx, 0, 0.1))
    B._area("DualKey", (0, -9, 8), (0.9, 0, 0), 16, 2500, (0.8, 0.85, 1.0))
    B._camera("CamB8_16", [(1, (0, 0, 0.2), (-5.0, -8.0, 7.0), 35, 8.0), (180, (0, 0, 0.2), (0.5, -9.4, 7.0), 35, 8.0)])


def build(variant="wafer", seed=81):
    sc = C.reset_scene(FRAMES)
    C.set_world(top=(0.03, 0.035, 0.05), horizon=(0.012, 0.014, 0.02), bottom=(0.003, 0.004, 0.006))
    C.set_color_management(exposure=0.4)
    rnd = random.Random(seed)
    {"wafer": wafer, "slit": slit, "scan": scan, "car": car, "sync": sync, "maglev": maglev,
     "layers": layers, "dual": dual}[variant](sc, rnd)
    return sc
