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
    # B5_01: light runs from IF into the illuminator (first 4 points of the path, ~30% of its length)
    path.data.bevel_factor_end = 0.0
    path.data.keyframe_insert("bevel_factor_end", frame=1)
    path.data.bevel_factor_end = 3 / (len(BM.PATH) - 1)  # poly curve: factor steps per point -> up to FACET2
    path.data.keyframe_insert("bevel_factor_end", frame=80)
    # B5_09: the dipole — two parallel strands from the second facet mirror up to the reticle
    dip = M.emission("Dipole", VIOLET, 10.0)
    a, b = Vector(BM.FACET2), Vector(BM.RETICLE)
    perp = (b - a).normalized().cross(Vector((0, 1, 0)))     # side by side as seen from the camera
    for side in (-1, 1):
        off = perp * side * 0.12
        s = _curve(f"Pole{side}", [tuple(a + off), tuple(b + off)], dip, radius=0.022)
        s.data.bevel_factor_end = 0.0
        s.data.keyframe_insert("bevel_factor_end", frame=120)
        s.data.bevel_factor_end = 1.0
        s.data.keyframe_insert("bevel_factor_end", frame=170)
    B._area("MKey", (0, -9, 8), (0.9, 0, 0), 16, 2500, (0.8, 0.85, 1.0))
    B._camera("CamB5_01", [(1, BM.IF, (-5.4, -8.0, 1.6), 35, 5.6),
                           (110, (-1.45, 0, 1.2), (-2.6, -8.6, 2.2), 35, 5.6)])
    B._camera("CamB5_09", [(120, (-1.45, 0, 1.2), (-2.6, -8.6, 2.2), 35, 5.6),
                           (240, (0.0, 0, 2.2), (-1.8, -8.4, 3.2), 35, 5.6)])


# ---- B5_02 ---------------------------------------------------------------------------------
IN = Vector((-6.0, 0, -0.8))
P1 = Vector((0.0, 0, 0.0))
P2 = Vector((-3.0, 0, 2.2))
OUT = Vector((2.6, 0, 3.8))


def _plate(name, centre, prev, nxt, nx=9, ny=7, pitch=0.24, mat=None):
    """A plate of small square facets facing the bisector of prev->centre->nxt.
    Returns the plate's world-space facet centres in a fixed order."""
    rot = BM._mirror_rot(tuple(prev), tuple(centre), tuple(nxt))
    q = rot.to_quaternion()
    u, v = q @ Vector((1, 0, 0)), q @ Vector((0, 1, 0))
    bpy.ops.mesh.primitive_cube_add(location=tuple(centre - (q @ Vector((0, 0, 0.08)))))
    back = bpy.context.object
    back.name = name + "Back"
    back.rotation_euler = rot
    back.scale = (nx * pitch / 2 + 0.12, ny * pitch / 2 + 0.12, 0.05)
    back.data.materials.append(M.dark_anodized(name + "Dark"))
    styles.tag(back, "structure")
    centres = []
    for i in range(nx):
        for j in range(ny):
            c = centre + u * ((i - (nx - 1) / 2) * pitch) + v * ((j - (ny - 1) / 2) * pitch)
            bpy.ops.mesh.primitive_cube_add(location=tuple(c))
            f = bpy.context.object
            f.name = f"{name}F{i}_{j}"
            f.rotation_euler = rot
            f.scale = (pitch * 0.44, pitch * 0.44, 0.02)
            f.data.materials.append(mat)
            styles.tag(f, "structure")
            centres.append(c)
    return centres, u, v


def module(sc, rnd):
    mirror = M.multilayer_mirror("FacetMat", r_max=0.6)
    f1, u1, v1 = _plate("FieldFacets", P1, IN, P2, mat=mirror)
    f2, u2, v2 = _plate("PupilFacets", P2, P1, OUT, mat=mirror)
    # housing cut open toward the camera (shell -> ghost glass in xray)
    bpy.ops.mesh.primitive_cube_add(location=(-1.6, 0.6, 1.5))
    box = bpy.context.object
    box.name = "IllumHousing"
    box.scale = (4.4, 1.6, 3.0)
    box.data.materials.append(M.principled("IllumPanel", (0.78, 0.8, 0.82), metallic=0.2, roughness=0.45))
    styles.tag(box, "shell")
    # rays: uneven before the first plate (4 brightness bins), uniform afterwards
    bins = [M.emission(f"RayIn{k}", VIOLET, s) for k, s in enumerate((0.25, 0.6, 1.3, 2.6))]
    even = M.emission("RayEven", VIOLET, 1.1)
    order = list(range(len(f2)))
    rnd.shuffle(order)                                    # each field facet feeds some pupil facet
    out_axis = (OUT - P2).normalized()
    ou = out_axis.cross(Vector((0, 1, 0))).normalized()
    ov = Vector((0, 1, 0))
    for k, c1 in enumerate(f1):
        if k % 2:
            continue
        # incoming spot: brightness falls off from a hot centre, with noise (the "mountains")
        d = (c1 - P1).length / 1.1
        level = math.exp(-2.6 * d * d) * (0.6 + 0.8 * rnd.random())
        mat_in = bins[min(3, int(level * 4))]
        start = IN + (c1 - P1) * 0.35
        r_in = _curve(f"RIn{k}", [tuple(start), tuple(c1)], mat_in, radius=0.006 + 0.01 * level)
        _grow(r_in, 1, 26)
        c2 = f2[order[k]]
        r_mid = _curve(f"RMid{k}", [tuple(c1), tuple(c2)], even, radius=0.008)
        _grow(r_mid, 26, 52)
        # every pupil facet sends its light over the SAME exit field: rays overlap into one even patch
        tgt = OUT + ou * rnd.uniform(-0.45, 0.45) + ov * rnd.uniform(-0.45, 0.45)
        r_out = _curve(f"ROut{k}", [tuple(c2), tuple(tgt)], even, radius=0.008)
        _grow(r_out, 52, 80)
    # input spot (blotchy) and output field (even)
    spot = M.soft_emitter("InSpot", VIOLET, 4.0)
    bpy.ops.mesh.primitive_circle_add(radius=0.5, fill_type="NGON", location=tuple(IN))
    s = bpy.context.object
    s.rotation_euler = (0, math.pi / 2, 0)
    s.data.materials.append(spot)
    styles.tag(s, "emitter")
    field = M.emission("OutField", VIOLET, 0.0)
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=tuple(OUT))
    o = bpy.context.object
    o.rotation_euler = out_axis.to_track_quat("Z", "Y").to_euler()
    o.data.materials.append(field)
    styles.tag(o, "emitter")
    M.set_emission_strength(field, 70, 0.0)
    M.set_emission_strength(field, 90, 6.0)
    B._area("ModKey", (-1.5, -8, 6), (1.0, 0, 0), 10, 1200, (0.9, 0.92, 1.0))
    B._camera("CamB5_02", [(1, (-1.4, 0, 1.4), (-1.4, -13.5, 2.2), 50, 4.0),
                           (142, (-1.4, 0, 1.5), (-1.4, -11.0, 2.0), 50, 4.0)])


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
WALL_NX, WALL_NY, WALL_P = 26, 18, 0.32
LIGHT_POS = Vector((-5.0, -9.0, 5.0))
CAM_FINAL = Vector((0.0, -12.0, 0.4))
CAM_MACRO = Vector((-5.5, -1.8, 1.2))


def _wall_pattern(name, i, j):
    x = (i - (WALL_NX - 1) / 2) / (WALL_NX / 2)
    y = (j - (WALL_NY - 1) / 2) / (WALL_NX / 2)
    r = math.hypot(x, y)
    if name == "ring":
        return 0.45 <= r <= 0.66
    if name == "dipole":
        return min(math.hypot(x, y - 0.38), math.hypot(x, y + 0.38)) <= 0.2
    return False


def facets(sc, rnd):
    C.set_world(top=(0.02, 0.022, 0.03), horizon=(0.01, 0.011, 0.015), bottom=(0.002, 0.002, 0.003))
    mat = M.multilayer_mirror("WallFacet", r_max=0.5)
    bpy.ops.mesh.primitive_cube_add(location=(0, 0.12, 0))
    back = bpy.context.object
    back.scale = (WALL_NX * WALL_P / 2 + 0.2, 0.05, WALL_NY * WALL_P / 2 + 0.2)
    back.data.materials.append(M.dark_anodized("WallBack"))
    styles.tag(back, "structure")
    for i in range(WALL_NX):
        for j in range(WALL_NY):
            pos = Vector(((i - (WALL_NX - 1) / 2) * WALL_P, 0, (j - (WALL_NY - 1) / 2) * WALL_P))
            bpy.ops.mesh.primitive_cube_add(location=tuple(pos))
            f = bpy.context.object
            f.name = f"Facet{i}_{j}"
            f.scale = (WALL_P * 0.45, 0.025, WALL_P * 0.45)
            bev = f.modifiers.new("Bevel", "BEVEL")
            bev.width = 0.012
            bev.segments = 2
            f.data.materials.append(mat)
            styles.tag(f, "structure")
            # "bright": normal bisects light and final camera, so this facet flashes the light at us
            nb = ((LIGHT_POS - pos).normalized() + (CAM_FINAL - pos).normalized()).normalized()
            bright = nb.to_track_quat("-Y", "Z").to_euler()
            dark = Euler((bright.x + math.radians(14), bright.y, bright.z + math.radians(10)))
            nm = ((LIGHT_POS - pos).normalized() + (CAM_MACRO - pos).normalized()).normalized()
            idle = nm.to_track_quat("-Y", "Z").to_euler()
            idle = Euler((idle.x + math.radians(rnd.uniform(-4, 4)), idle.y, idle.z + math.radians(rnd.uniform(-4, 4))))
            # B5_04 (frames 1-103): a travelling wave of small tilts across the rows
            ph = 0.35 * i + 0.2 * j
            for f0 in range(1, 104, 12):
                w = math.sin(ph + f0 * 0.12)
                f.rotation_euler = Euler((idle.x + 0.05 * w, idle.y, idle.z + 0.035 * w))
                f.keyframe_insert("rotation_euler", frame=f0)
            # B5_05 (frames 121-240): flip in a stadium wave into the ring, then into two poles
            delay = int(i * 0.9)
            for start, pat in ((150, "ring"), (196, "dipole")):
                target = bright if _wall_pattern(pat, i, j) else dark
                prev = f.rotation_euler.copy()
                f.keyframe_insert("rotation_euler", frame=start + delay - 6)
                f.rotation_euler = target
                f.keyframe_insert("rotation_euler", frame=start + delay)
            f.rotation_euler = idle
            f.keyframe_insert("rotation_euler", frame=121)
    key = bpy.data.lights.new("FacetLight", "AREA")
    for f, e, sz in ((1, 7.0, 1.2), (110, 7.0, 1.2), (121, 110.0, 4.0)):   # macro sparkle, then the wall
        key.energy, key.size = e, sz
        key.keyframe_insert("energy", frame=f)
        key.keyframe_insert("size", frame=f)
    key.color = (0.85, 0.8, 1.0)
    ko = bpy.data.objects.new("FacetLight", key)
    sc.collection.objects.link(ko)
    ko.location = LIGHT_POS
    ko.rotation_euler = (-LIGHT_POS).to_track_quat("-Z", "Y").to_euler()
    B._area("WallFill", (6, -8, -3), (1.4, 0, 0.6), 6, 60, (0.6, 0.7, 1.0))
    B._camera("CamB5_04", [(1, (-3.0, 0, 0.3), (-6.5, -1.8, 1.2), 50, 2.8),
                           (103, (-1.0, 0, 0.3), (-4.5, -1.8, 1.2), 50, 2.8)])
    B._camera("CamB5_05", [(121, (0.6, 0, 0.3), (0.9, -1.6, 0.5), 50, 4.0),
                           (190, (0.0, 0, 0.0), tuple(CAM_FINAL), 50, 4.0)])


def build(variant="machine", seed=51):
    sc = C.reset_scene(FRAMES)
    C.set_world(top=(0.03, 0.035, 0.05), horizon=(0.012, 0.014, 0.02), bottom=(0.003, 0.004, 0.006))
    C.set_color_management(exposure=0.4)
    rnd = random.Random(seed)
    {"machine": machine, "module": module, "terrain": terrain, "facets": facets}[variant](sc, rnd)
    return sc
