"""B5 — the illuminator (F18, F34). Variants:

  machine  B5_01  xray machine, violet path from IF into the ghost-glass illuminator
           B5_09  same framing; a dipole-shaped beam leaves the illuminator and climbs to the reticle
  module   B5_02  illuminator cut open: two facet plates; an uneven spot becomes a uniform field
  terrain  B5_03  intensity as a glowing landscape: peaks and valleys flatten into a mesa
  facets   B5_04  macro over rows of facet mirrors tilting one after another
           B5_05  pull back to the whole wall; the facets that catch the light spell a ring, then two poles
All shapes illustrative; facet counts are not public (F34).
"""
import math
import random

import bpy
from mathutils import Euler, Vector

import build_machine as BM
import common as C
import materials as M
import sample_b1 as B
import styles

FRAMES = 240
VIOLET = (0.62, 0.45, 1.0)


def _key(ob, f, **kw):
    for k, v in kw.items():
        setattr(ob, k, v)
        ob.keyframe_insert(k, frame=f)


def _curve(name, pts, mat, radius=0.01, role="rays"):
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = radius
    sp = cu.splines.new("POLY")
    sp.points.add(len(pts) - 1)
    for i, p in enumerate(pts):
        sp.points[i].co = (*p, 1)
    ob = bpy.data.objects.new(name, cu)
    bpy.context.scene.collection.objects.link(ob)
    ob.data.materials.append(mat)
    styles.tag(ob, role)
    return ob


def _grow(ob, f0, f1):
    ob.data.bevel_factor_end = 0.0
    ob.data.keyframe_insert("bevel_factor_end", frame=f0)
    ob.data.bevel_factor_end = 1.0
    ob.data.keyframe_insert("bevel_factor_end", frame=f1)


# ---- B5_01 / B5_09 -------------------------------------------------------------------------
def machine(sc, rnd):
    path, pmat = BM.machine()
    # B5_01: light runs from the IF through the fold mirror and the field facet mirror to the pupil facet mirror
    path.data.bevel_factor_end = 0.0
    path.data.keyframe_insert("bevel_factor_end", frame=1)
    path.data.bevel_factor_end = 4 / (len(BM.PATH) - 1)  # poly curve: factor steps per point; index 4 = FACET2
    path.data.keyframe_insert("bevel_factor_end", frame=80)
    # B5_09: dipole illumination is an angular distribution: light leaves two separated spots on the pupil facet
    # mirror and converges on the same illuminated area of the reticle (audit_B5 B5_09)
    dip = M.emission("Dipole", VIOLET, 10.0)
    a, b = Vector(BM.FACET2), Vector(BM.RETICLE)
    across = (b - a).normalized().cross(Vector((0, 1, 0)))
    for side in (-1, 1):
        s = _curve(f"Pole{side}", [tuple(a + across * side * 0.16), tuple(b)], dip, radius=0.022)
        s.data.bevel_factor_end = 0.0
        s.data.keyframe_insert("bevel_factor_end", frame=120)
        s.data.bevel_factor_end = 1.0
        s.data.keyframe_insert("bevel_factor_end", frame=170)
    f1, f2, ret = Vector(BM.FACET1), Vector(BM.FACET2), Vector(BM.RETICLE)
    mid = (Vector(BM.IF) + f1 + f2) / 3
    B._area("MKey", (BM.CENTER[0], -9, 8), (0.9, 0, 0), 16, 2500, (0.8, 0.85, 1.0))
    B._camera("CamB5_01", [(1, tuple(Vector(BM.IF) + Vector((-0.6, 0, 0.4))), (BM.IF[0] + 1.5, -7.5, 2.0), 35, 5.6),
                           (110, tuple(mid), (mid.x + 0.6, -7.8, mid.z + 0.8), 35, 5.6)])
    B._camera("CamB5_09", [(120, tuple(mid), (mid.x + 0.6, -7.8, mid.z + 0.8), 35, 5.6),
                           (240, tuple((f2 + ret) / 2), ((f2.x + ret.x) / 2 + 0.4, -7.6, (f2.z + ret.z) / 2 + 0.9), 35, 5.6)])


# ---- B5_02 ---------------------------------------------------------------------------------
def _arc_mesh(name, length, height, curv_r, depth=0.03, n=24):
    """A thin arc-shaped facet (ZEISS field facets are long curved strips, aspect >= 8:1; Starlith 3400 deck)."""
    half = length / 2 / curv_r
    verts, faces = [], []
    for k in range(n + 1):
        t = -half + 2 * half * k / n
        for rr in (curv_r, curv_r + height):
            x, y = rr * math.sin(t), rr * math.cos(t) - curv_r - height / 2
            verts += [(x, y, 0.0), (x, y, depth)]
    for k in range(n):
        a = 4 * k
        q = [(a, a + 4, a + 6, a + 2), (a + 1, a + 3, a + 7, a + 5), (a, a + 1, a + 5, a + 4), (a + 2, a + 6, a + 7, a + 3)]
        faces += q
    last = 4 * n
    faces += [(0, 2, 3, 1), (last, last + 1, last + 3, last + 2)]
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.validate()
    return me


def _field_plate(name, centre, prev, nxt, cols=3, rows=10, mat=None):
    """Field facet mirror: an elliptical carrier with stacked arc-shaped facets. Returns facet centres."""
    rot = BM._mirror_rot(tuple(prev), tuple(centre), tuple(nxt))
    q = rot.to_quaternion()
    u, v, w = q @ Vector((1, 0, 0)), q @ Vector((0, 1, 0)), q @ Vector((0, 0, 1))
    bpy.ops.mesh.primitive_cylinder_add(radius=1.0, depth=0.08, vertices=96, location=tuple(centre - w * 0.07))
    back = bpy.context.object
    back.name = name + "Carrier"
    back.rotation_euler = rot
    back.scale = (cols * 0.29, rows * 0.056, 1.0)                    # the carrier just holds the facet columns
    back.data.materials.append(M.dark_anodized(name + "Dark"))
    styles.tag(back, "structure")
    me = _arc_mesh(name + "Arc", 0.46, 0.06, 0.9)
    centres = []
    for i in range(cols):
        for j in range(rows):
            c = centre + u * ((i - (cols - 1) / 2) * 0.5) + v * ((j - (rows - 1) / 2) * 0.085)
            f = bpy.data.objects.new(f"{name}F{i}_{j}", me)
            bpy.context.scene.collection.objects.link(f)
            f.location = c
            f.rotation_euler = rot
            if mat and not me.materials:
                me.materials.append(mat)
            styles.tag(f, "structure")
            centres.append(c)
    return centres


def _pupil_plate(name, centre, prev, nxt, radius=0.75, pitch=0.12, mat=None, mats=None):
    """Pupil facet mirror: a round carrier with round facets on a hexagonal grid. Returns (centres, objects)."""
    rot = BM._mirror_rot(tuple(prev), tuple(centre), tuple(nxt))
    q = rot.to_quaternion()
    u, v, w = q @ Vector((1, 0, 0)), q @ Vector((0, 1, 0)), q @ Vector((0, 0, 1))
    bpy.ops.mesh.primitive_cylinder_add(radius=radius + 0.12, depth=0.08, vertices=96, location=tuple(centre - w * 0.07))
    back = bpy.context.object
    back.name = name + "Carrier"
    back.rotation_euler = rot
    back.data.materials.append(M.dark_anodized(name + "Dark"))
    styles.tag(back, "structure")
    centres, obs = [], []
    n = int(radius / pitch) + 1
    for i in range(-n, n + 1):
        for j in range(-n, n + 1):
            x, y = (i + 0.5 * (j % 2)) * pitch, j * pitch * 0.866
            if math.hypot(x, y) > radius:
                continue
            c = centre + u * x + v * y
            bpy.ops.mesh.primitive_cylinder_add(radius=pitch * 0.42, depth=0.02, vertices=24, location=tuple(c))
            f = bpy.context.object
            f.name = f"{name}F{len(obs)}"
            f.rotation_euler = rot
            f.data.materials.append(mats[len(obs)] if mats else mat)
            styles.tag(f, "structure")
            centres.append((c, x / radius, y / radius))
            obs.append(f)
    return centres, obs


IN = Vector((-6.0, 0, -0.8))            # the intermediate focus: one point, the light diverges from it
P1 = Vector((0.0, 0, 0.0))
P2 = Vector((-3.0, 0, 2.2))
OUT = Vector((2.6, 0, 3.8))


def module(sc, rnd):
    mirror = M.multilayer_mirror("FacetMat")
    f1 = _field_plate("FieldFacets", P1, IN, P2, mat=mirror)
    f2, _ = _pupil_plate("PupilFacets", P2, P1, OUT, mat=mirror)
    bpy.ops.mesh.primitive_cube_add(location=(-1.6, 0.6, 1.5))
    box = bpy.context.object
    box.name = "IllumHousing"
    box.scale = (4.4, 1.6, 3.0)
    box.data.materials.append(M.principled("IllumPanel", (0.78, 0.8, 0.82), metallic=0.2, roughness=0.45))
    styles.tag(box, "shell")
    # rays: a cone from the IF to the field facets, brightness uneven across the cone; after the pupil facets
    # every channel covers the whole exit field, so the patch there is even
    bins = [M.emission(f"RayIn{k}", VIOLET, s) for k, s in enumerate((0.25, 0.6, 1.3, 2.6))]
    even = M.emission("RayEven", VIOLET, 1.1)
    out_axis = (OUT - P2).normalized()
    ou = out_axis.cross(Vector((0, 1, 0))).normalized()
    ov = Vector((0, 1, 0))
    corners = [OUT + ou * 0.5 * sx + ov * 0.12 * sy for sx in (-1, 1) for sy in (-1, 1)]
    order = list(range(len(f2)))
    rnd.shuffle(order)
    for k, c1 in enumerate(f1):
        d = (c1 - P1).length / 1.4
        level = math.exp(-2.6 * d * d) * (0.6 + 0.8 * rnd.random())
        r_in = _curve(f"RIn{k}", [tuple(IN), tuple(c1)], bins[min(3, int(level * 4))], radius=0.004 + 0.008 * level)
        _grow(r_in, 1, 26)
        c2 = f2[order[k % len(f2)]][0]
        r_mid = _curve(f"RMid{k}", [tuple(c1), tuple(c2)], even, radius=0.006)
        _grow(r_mid, 26, 52)
        if k % 3 == 0:                                   # a few channels drawn as a full cone onto the field
            for cn, corner in enumerate(corners):
                r_out = _curve(f"ROut{k}_{cn}", [tuple(c2), tuple(corner)], even, radius=0.004)
                _grow(r_out, 52, 80)
    field = M.emission("OutField", VIOLET, 0.0)
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=tuple(OUT))
    o = bpy.context.object
    o.scale = (1.0, 0.24, 1.0)
    o.rotation_euler = out_axis.to_track_quat("Z", "Y").to_euler()
    o.data.materials.append(field)
    styles.tag(o, "emitter")
    M.set_emission_strength(field, 70, 0.0)
    M.set_emission_strength(field, 90, 6.0)
    _key(o, 1, hide_render=True)                          # unlit it would be a black card
    _key(o, 71, hide_render=False)
    B._area("ModKey", (-1.5, -8, 6), (1.0, 0, 0), 10, 1200, (0.9, 0.92, 1.0))
    # from the IF side: the field facets face -x (toward the IF), so the camera stands there; the exit patch in frame
    B._camera("CamB5_02", [(1, (-0.6, 0, 1.6), (-8.5, -8.0, 3.2), 32, 5.6),
                           (142, (-0.4, 0, 1.7), (-7.6, -7.4, 3.0), 32, 5.6)])


# ---- B5_03 ---------------------------------------------------------------------------------
def terrain(sc, rnd):
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=180, y_subdivisions=180, size=10)
    g = bpy.context.object
    g.name = "IntensityField"
    tex = bpy.data.textures.new("Peaks", "CLOUDS")
    tex.noise_scale = 1.1
    d = g.modifiers.new("Peaks", "DISPLACE")
    d.texture = tex
    d.texture_coords = "OBJECT"
    d.mid_level = 0.5
    d.strength = 2.2
    d.keyframe_insert("strength", frame=20)
    d.strength = 0.0
    d.keyframe_insert("strength", frame=80)
    mat = bpy.data.materials.new("HeightGlow")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = -1.1
    mr.inputs["From Max"].default_value = 1.1
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    e = ramp.color_ramp.elements
    e[0].position, e[0].color = 0.0, (0.02, 0.0, 0.08, 1)
    e[1].position, e[1].color = 1.0, (1.0, 0.95, 1.0, 1)
    mid = ramp.color_ramp.elements.new(0.5)
    mid.color = (0.3, 0.17, 0.85, 1)
    nt.links.new(tc.outputs["Object"], sep.inputs["Vector"])
    nt.links.new(sep.outputs["Z"], mr.inputs["Value"])
    nt.links.new(mr.outputs["Result"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], em.inputs["Color"])
    em.inputs["Strength"].default_value = 0.9
    nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
    g.data.materials.append(mat)
    styles.tag(g, "emitter")
    # a brighter wire overlay on the same surface reads as a measured field
    w = g.copy()
    w.data = g.data.copy()
    sc.collection.objects.link(w)
    w.name = "FieldWire"
    w.modifiers.new("Wire", "WIREFRAME").thickness = 0.012
    w.data.materials.clear()
    w.data.materials.append(M.emission("WireGlow", (0.62, 0.5, 1.0), 1.1))
    styles.tag(w, "emitter")
    w.location.z = 0.005
    B._camera("CamB5_03", [(1, (0, 0, 0), (9.0, -9.0, 7.5), 35, 8.0),
                           (108, (0, 0, 0), (12.0, -3.0, 7.0), 35, 8.0)])


# ---- B5_04 / B5_05 -------------------------------------------------------------------------
# The tilting mirrors are the field facets (long arc-shaped strips on an elliptical carrier); the illumination shape
# appears on the SECOND plate, the pupil facet mirror (round facets): each field facet sends its light to one pupil
# facet, and tilting a field facet chooses which one. Lit pupil facets spell the setting: ring, then dipole
# (ZEISS Starlith 3400 deck s.4-10; audit_B5 B5_05). Facet counts are not public (F34): drawn counts are 示意.
WALL_COLS, WALL_ROWS = 5, 22
PUPIL_C = Vector((9.0, 2.2, 0.0))
LIGHT_POS = Vector((-5.0, -9.0, 5.0))
CAM_MACRO = Vector((-5.5, -1.8, 1.2))


def _pupil_pattern(name, x, y):
    r = math.hypot(x, y)
    if name == "ring":
        return 0.55 <= r <= 0.88
    if name == "dipole":
        return abs(x) < 0.32 and 0.45 <= abs(y) <= 0.92
    return False


def facets(sc, rnd):
    C.set_world(top=(0.02, 0.022, 0.03), horizon=(0.01, 0.011, 0.015), bottom=(0.002, 0.002, 0.003))
    mat = M.multilayer_mirror("WallFacet")
    # field facet wall in the XZ plane, facing -Y
    bpy.ops.mesh.primitive_cylinder_add(radius=1.0, depth=0.1, vertices=128, location=(0, 0.12, 0),
                                        rotation=(math.pi / 2, 0, 0))
    car = bpy.context.object
    car.scale = (WALL_COLS * 0.65 + 0.4, WALL_ROWS * 0.075 + 0.35, 1.0)
    car.data.materials.append(M.dark_anodized("WallBack"))
    styles.tag(car, "structure")
    arc = _arc_mesh("WallArc", 1.15, 0.1, 1.6, depth=0.04)
    arc.materials.append(mat)
    field = []
    for i in range(WALL_COLS):
        for j in range(WALL_ROWS):
            x, z = (i - (WALL_COLS - 1) / 2) * 1.3, (j - (WALL_ROWS - 1) / 2) * 0.13
            if (x / (WALL_COLS * 0.65 + 0.2)) ** 2 + (z / (WALL_ROWS * 0.075 + 0.15)) ** 2 > 1:
                continue                                           # stay on the elliptical carrier
            f = bpy.data.objects.new(f"Facet{i}_{j}", arc)
            sc.collection.objects.link(f)
            f.location = (x, 0.0, z)
            styles.tag(f, "structure")
            base = Euler((math.pi / 2, 0, 0))
            ph = 0.35 * i + 0.25 * j                               # B5_04: a travelling wave of small tilts
            for f0 in range(1, 104, 12):
                w = math.sin(ph + f0 * 0.12)
                f.rotation_euler = Euler((base.x + 0.05 * w, 0.0, 0.035 * w))
                f.keyframe_insert("rotation_euler", frame=f0)
            f.rotation_euler = base
            f.keyframe_insert("rotation_euler", frame=121)
            field.append((f, Vector((x, 0.0, z)), i))
    # pupil facet mirror: round carrier with round facets; each facet can light up violet
    rot = (PUPIL_C - Vector((0, 0, 0))).normalized()
    q = (-rot).to_track_quat("Z", "Y")
    u, v = q @ Vector((1, 0, 0)), q @ Vector((0, 1, 0))
    bpy.ops.mesh.primitive_cylinder_add(radius=2.2, depth=0.1, vertices=128, location=tuple(PUPIL_C + rot * 0.08))
    pc = bpy.context.object
    pc.rotation_euler = q.to_euler()
    pc.data.materials.append(M.dark_anodized("PupilBack"))
    styles.tag(pc, "structure")
    pupil = []
    pitch, rad = 0.23, 2.0
    n = int(rad / pitch) + 1
    for a_ in range(-n, n + 1):
        for b_ in range(-n, n + 1):
            x, y = (a_ + 0.5 * (b_ % 2)) * pitch, b_ * pitch * 0.866
            if math.hypot(x, y) > rad:
                continue
            c = PUPIL_C + u * x + v * y
            m = M.principled(f"Pupil{len(pupil)}", (0.80, 0.78, 0.74), metallic=1.0, roughness=0.04,
                             emission=(0.40, 0.16, 1.0), emission_strength=0.0)
            bpy.ops.mesh.primitive_cylinder_add(radius=pitch * 0.42, depth=0.03, vertices=24, location=tuple(c))
            pf = bpy.context.object
            pf.rotation_euler = q.to_euler()
            pf.data.materials.append(m)
            styles.tag(pf, "structure")
            pupil.append((c, x / rad, y / rad, m))
    ray_mat = M.emission("FacetRay", (0.40, 0.16, 1.0), 2.0)
    for pat, (t0, t1) in (("ring", (150, 196)), ("dipole", (196, FRAMES + 40))):   # the dipole stays to the end
        lit = [p for p in pupil if _pupil_pattern(pat, p[1], p[2])]
        pool = field[:]
        rnd.shuffle(pool)
        for k, (c, px, py, m) in enumerate(lit):
            f, fc, col = pool[k % len(pool)]
            on = t0 + int(col * 4)                                  # a column-by-column wave of re-tilting
            em = m.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
            for fr, val in ((on - 1, 0.0), (on + 4, 2.2), (t1 - 1, 2.2), (t1, 0.0)):
                if fr > FRAMES:
                    continue
                em.default_value = val
                em.keyframe_insert("default_value", frame=fr)
            if k % 2 == 0:                                          # every other channel drawn as a ray
                r = _curve(f"Ch{pat}{k}", [tuple(fc + Vector((0, -0.05, 0))), tuple(c)], ray_mat, radius=0.03)
                r.data.bevel_factor_end = 0.0
                r.data.keyframe_insert("bevel_factor_end", frame=on - 2)
                r.data.bevel_factor_end = 1.0
                r.data.keyframe_insert("bevel_factor_end", frame=on + 6)
                _key(r, 1, hide_render=True)
                _key(r, on - 2, hide_render=False)
                if t1 < FRAMES:
                    _key(r, t1, hide_render=True)
            # the field facet tilts a little at the switch (the tilt that picks this pupil facet)
            f.keyframe_insert("rotation_euler", frame=on - 6)
            f.rotation_euler = Euler((math.pi / 2 + rnd.uniform(-0.06, 0.06), 0, rnd.uniform(-0.05, 0.05)))
            f.keyframe_insert("rotation_euler", frame=on)
    key = bpy.data.lights.new("FacetLight", "AREA")
    for fr, e, sz in ((1, 60.0, 2.0), (110, 60.0, 2.0), (121, 160.0, 4.0)):   # macro sparkle, then the wall
        key.energy, key.size = e, sz
        key.keyframe_insert("energy", frame=fr)
        key.keyframe_insert("size", frame=fr)
    key.color = (0.85, 0.8, 1.0)
    ko = bpy.data.objects.new("FacetLight", key)
    sc.collection.objects.link(ko)
    ko.location = LIGHT_POS
    ko.rotation_euler = (-LIGHT_POS).to_track_quat("-Z", "Y").to_euler()
    B._area("WallFill", (6, -8, -3), (1.4, 0, 0.6), 6, 60, (0.6, 0.7, 1.0))
    # cards where the facets' mirror direction points (macro camera on -x/-y, so the reflections look +x/-y/-z)
    C.softbox("FacetSoft", (6.0, -5.0, -2.5), (math.radians(95), 0, math.radians(55)), (10, 4), 2.5, (0.75, 0.82, 1.0))
    C.softbox("FacetSoft2", (-2.0, -7.0, 4.0), (1.0, 0, -0.3), (14, 5), 1.2, (0.75, 0.82, 1.0))
    B._camera("CamB5_04", [(1, (-3.0, 0, 0.3), (-6.5, -1.8, 1.2), 50, 2.8),
                           (103, (-1.0, 0, 0.3), (-4.5, -1.8, 1.2), 50, 2.8)])
    B._camera("CamB5_05", [(121, (0.6, 0, 0.3), (0.9, -2.2, 0.5), 50, 4.0),
                           (175, (4.5, 1.0, 0.0), (3.0, -14.5, 3.5), 35, 6.0),
                           (240, (4.6, 1.0, 0.0), (3.4, -14.0, 3.3), 35, 6.0)])


def build(variant="machine", seed=51):
    sc = C.reset_scene(FRAMES)
    C.set_world(top=(0.03, 0.035, 0.05), horizon=(0.012, 0.014, 0.02), bottom=(0.003, 0.004, 0.006))
    C.set_color_management(exposure=0.4)
    rnd = random.Random(seed)
    {"machine": machine, "module": module, "terrain": terrain, "facets": facets}[variant](sc, rnd)
    return sc
