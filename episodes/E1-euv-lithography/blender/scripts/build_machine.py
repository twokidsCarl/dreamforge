"""Whole-machine layout (stylised, NOT a copy of the ASML exterior) and a generic fab hall.

machine(): modules placed along the real optical order — source vessel -> intermediate focus ->
illuminator (facet mirrors) -> reticle stage on top -> six-mirror projection optics -> wafer stage
at the bottom — inside a housing tagged `shell`, with one glowing light path tagged `rays`.
Units are metres-ish, the whole machine ~12 m long. fab_hall(): floor, columns, ceiling light
grid, a floor trench for the drive-laser beam tube, backlit human silhouettes for scale.
"""
import math
import random

import bpy

import materials as M
import styles

VIOLET = (0.62, 0.45, 1.0)

# key points of the optical path (x, y, z)
PLASMA = (-5.2, 0.0, 0.0)
IF = (-2.9, 0.0, 0.0)
FACET1 = (-2.0, 0.0, 0.9)
FACET2 = (-0.9, 0.0, 1.7)
RETICLE = (0.5, 0.0, 2.35)
PO_MIRRORS = [(1.0, 0.0, 1.75), (0.0, 0.0, 1.3), (1.05, 0.0, 0.85), (0.05, 0.0, 0.35),
              (0.95, 0.0, -0.1), (0.35, 0.0, -0.5)]
WAFER = (0.5, 0.0, -1.05)
PATH = [PLASMA, IF, FACET1, FACET2, RETICLE] + PO_MIRRORS + [WAFER]


MODULE = None


def _tag_module(ob):
    if MODULE:
        ob["module"] = MODULE
    return ob


def _box(name, loc, size, mat, role="structure", bevel=0.03):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    ob = bpy.context.object
    ob.name = name
    ob.scale = (size[0] / 2, size[1] / 2, size[2] / 2)
    bpy.ops.object.transform_apply(scale=True)
    if bevel:
        m = ob.modifiers.new("Bevel", "BEVEL")
        m.width = bevel
        m.segments = 2
    ob.data.materials.append(mat)
    styles.tag(ob, role)
    return _tag_module(ob)


def _disc(name, loc, r, depth, mat, rot=(0, 0, 0), role="structure"):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=depth, vertices=64, location=loc, rotation=rot)
    ob = bpy.context.object
    ob.name = name
    for p in ob.data.polygons:
        p.use_smooth = True
    ob.data.materials.append(mat)
    styles.tag(ob, role)
    return _tag_module(ob)


def _mirror_rot(prev, here, nxt):
    """Orient a mirror so its normal bisects the incoming and outgoing rays."""
    from mathutils import Vector
    a = (Vector(prev) - Vector(here)).normalized()
    b = (Vector(nxt) - Vector(here)).normalized()
    n = (a + b).normalized()
    return n.to_track_quat("Z", "Y").to_euler()


def light_path(name="LightPath", radius=0.025, strength=8.0):
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = radius
    sp = cu.splines.new("POLY")
    sp.points.add(len(PATH) - 1)
    for i, p in enumerate(PATH):
        sp.points[i].co = (*p, 1)
    ob = bpy.data.objects.new(name, cu)
    bpy.context.scene.collection.objects.link(ob)
    mat = M.emission(name + "Mat", VIOLET, strength)
    ob.data.materials.append(mat)
    styles.tag(ob, "rays")
    return ob, mat


def _ring(name, loc, r, minor, mat, rot=(0, math.pi / 2, 0), role="structure"):
    bpy.ops.mesh.primitive_torus_add(major_radius=r, minor_radius=minor, major_segments=96, minor_segments=12,
                                     location=loc, rotation=rot)
    ob = bpy.context.object
    ob.name = name
    for p in ob.data.polygons:
        p.use_smooth = True
    ob.data.materials.append(mat)
    styles.tag(ob, role)
    return _tag_module(ob)


def _bolt_circle(prefix, centre, r, n, mat, axis="X", size=0.035):
    from mathutils import Vector
    for k in range(n):
        th = 2 * math.pi * k / n
        if axis == "X":
            p = (centre[0], centre[1] + r * math.cos(th), centre[2] + r * math.sin(th))
            rot = (0, math.pi / 2, 0)
        else:
            p = (centre[0] + r * math.cos(th), centre[1] + r * math.sin(th), centre[2])
            rot = (0, 0, 0)
        _disc(f"{prefix}{k}", p, size, 0.05, mat, rot=rot)


def _mirror(name, prev, here, nxt, r, mat, mount):
    """A mirror at a bounce point: the reflective face, a thicker substrate behind it and a mount ring."""
    from mathutils import Vector
    rot = _mirror_rot(prev, here, nxt)
    q = rot.to_quaternion()
    n = q @ Vector((0, 0, 1))
    face = _disc(name, here, r, 0.05, mat, rot=rot)
    sub = _disc(name + "Substrate", tuple(Vector(here) - n * 0.09), r * 0.98, 0.12,
                M.principled("Substrate", (0.85, 0.86, 0.88), roughness=0.25), rot=rot)
    ring = _ring(name + "Mount", tuple(Vector(here) - n * 0.06), r * 1.04, 0.035, mount, rot=rot)
    return face


def _panel_box(name, loc, size, mat, seam, role="shell", nx=4, nz=2):
    """An enclosure: one bevelled box plus thin recessed seam lines that break it into service panels."""
    box = _box(name, loc, size, mat, role=role, bevel=0.12)
    x0, y0, z0 = loc[0] - size[0] / 2, loc[1] - size[1] / 2, loc[2] - size[2] / 2
    for i in range(1, nx):
        x = x0 + size[0] * i / nx
        for y in (y0 - 0.005, y0 + size[1] + 0.005):
            _box(f"{name}SeamV{i}{y:.0f}", (x, y, loc[2]), (0.03, 0.01, size[2] * 0.96), seam, role=role, bevel=0)
    for j in range(1, nz):
        z = z0 + size[2] * j / nz
        for y in (y0 - 0.005, y0 + size[1] + 0.005):
            _box(f"{name}SeamH{j}{y:.0f}", (loc[0], y, z), (size[0] * 0.98, 0.01, 0.03), seam, role=role, bevel=0)
    return box


def machine(with_path=True):
    global MODULE
    MODULE = "source"
    steel = M.polished_steel("MachSteel", 0.3)
    dark = M.dark_anodized("MachDark")
    mount = M.principled("MirrorMount", (0.08, 0.085, 0.09), metallic=0.9, roughness=0.3)
    mirror = M.multilayer_mirror("MachMirror", r_max=0.5)
    panel = M.principled("HousingPanel", (0.78, 0.8, 0.82), metallic=0.2, roughness=0.45)
    seam = M.principled("PanelSeam", (0.05, 0.05, 0.055), roughness=0.6)
    # ---- source vessel: drum with flanges, ports and a viewport; cone with stiffening rings to IF
    _disc("SrcDrum", (-5.6, 0, 0), 1.1, 1.6, dark, rot=(0, math.pi / 2, 0), role="shell")
    for x in (-6.4, -4.8):
        _ring(f"SrcFlange{x}", (x, 0, 0), 1.13, 0.06, steel)
        _bolt_circle(f"SrcBolt{x}", (x, 0, 0), 1.13, 32, steel)
    for k, (dy, dz) in enumerate(((0, 1), (0, -1), (1, 0), (-1, 0))):
        rot = (math.pi / 2, 0, 0) if dy else (0, 0, 0)
        p = (-5.6, dy * 1.2, dz * 1.2)
        _disc(f"SrcPort{k}", p, 0.22, 0.35, steel, rot=rot)
        _disc(f"SrcPortFlange{k}", (p[0], dy * 1.38, dz * 1.38), 0.3, 0.06, steel, rot=rot)
    _disc("DropletGen", (-5.6, 0, 1.75), 0.14, 0.9, steel)                         # droplet generator on top
    _disc("Viewport", (-5.6, -1.12, 0.45), 0.16, 0.04, M.principled("ViewGlass", (0.02, 0.03, 0.05), roughness=0.02,
                                                                    coat=1.0), rot=(math.pi / 2, 0, 0))
    bpy.ops.mesh.primitive_cone_add(vertices=96, radius1=1.1, radius2=0.18, depth=2.0, location=(-3.8, 0, 0),
                                    rotation=(0, math.pi / 2, 0))
    cone = bpy.context.object
    cone.name = "SrcCone"
    for p in cone.data.polygons:
        p.use_smooth = True
    cone.data.materials.append(dark)
    styles.tag(cone, "shell")
    _tag_module(cone)
    for k, x in enumerate((-4.4, -3.8, -3.2)):
        r = 1.1 - (x + 4.8) / 2.0 * 0.92
        _ring(f"ConeRib{k}", (x, 0, 0), r + 0.02, 0.03, steel)
    _disc("Collector", (-6.2, 0, 0), 0.9, 0.08, mirror, rot=(0, math.pi / 2, 0))
    MODULE = "illum"
    # ---- illuminator: panelled box, two facet mirrors (with mounts) at the bounce points
    _panel_box("Illuminator", (-1.45, 0, 1.3), (2.1, 1.3, 1.4), dark, seam, nx=3, nz=2)
    for i, pt in enumerate((FACET1, FACET2)):
        _mirror(f"Facet{i}", PATH[1 + i], pt, PATH[3 + i], 0.36, mirror, mount)
    MODULE = "reticle"
    # ---- reticle stage: platen on linear-motor rails, reticle face down
    _box("ReticleStage", (0.5, 0, 2.62), (2.4, 1.8, 0.3), steel)
    for y in (-0.95, 0.95):
        _box(f"RetRail{y}", (0.5, y, 2.42), (4.2, 0.16, 0.14), dark)
        for k in range(12):
            _box(f"RetMagnet{y}{k}", (-1.4 + 0.34 * k, y, 2.5), (0.26, 0.17, 0.03), steel, bevel=0.005)
    _box("Reticle", (RETICLE[0], 0, RETICLE[2] + 0.05), (0.6, 0.6, 0.06), mirror, bevel=0.005)
    MODULE = "po"
    # ---- projection optics: a stacked barrel with flanges and struts, six mirrors with mounts
    for k in range(5):
        z = -0.55 + 0.52 * k
        _disc(f"POSection{k}", (0.5, 0, z), 0.82, 0.46, dark, role="shell")
        _ring(f"POFlange{k}", (0.5, 0, z + 0.25), 0.86, 0.045, steel, rot=(0, 0, 0))
    _box("POColumn", (0.5, 0, 0.6), (1.6, 1.6, 2.6), dark, role="shell").hide_render = True   # kept for scripts
    for k in range(6):
        th = 2 * math.pi * k / 6 + 0.3
        _disc(f"POStrut{k}", (0.5 + 1.0 * math.cos(th), 1.0 * math.sin(th), 0.6), 0.04, 2.7, steel)
    seq = [RETICLE] + PO_MIRRORS + [WAFER]
    for i, pt in enumerate(PO_MIRRORS):
        _mirror(f"POMirror{i}", seq[i], pt, seq[i + 2], 0.26 if i < 5 else 0.34, mirror, mount)
    MODULE = "wafer"
    # ---- wafer stage: planar-motor platen with a tile grid, wafer chuck
    _box("WaferStage", (0.5, 0, -1.35), (2.8, 2.8, 0.35), steel)
    tile = M.principled("MotorTile", (0.12, 0.12, 0.13), metallic=0.8, roughness=0.35)
    for i in range(6):
        for j in range(6):
            _box(f"Tile{i}{j}", (-0.75 + 0.5 * i + 0.5 * 0.5 - 0.25, -1.25 + 0.5 * j, -1.56), (0.46, 0.46, 0.04), tile,
                 bevel=0.01)
    _disc("Chuck", (WAFER[0], 0, WAFER[2] - 0.04), 0.5, 0.05, steel)
    _disc("Wafer", WAFER, 0.45, 0.02, M.multilayer_mirror("WaferFilm", r_max=0.45))
    MODULE = "base"
    # ---- base frame on vibration isolators
    _box("Base", (-1.5, 0, -1.9), (11.0, 3.4, 0.6), dark)
    for x in (-6.5, -3.0, 0.5, 3.5):
        for y in (-1.4, 1.4):
            _disc(f"Isolator{x}{y}", (x, y, -2.35), 0.22, 0.3, steel)
    for k in range(3):                                                     # cable trays along the base
        _box(f"CableTray{k}", (-1.5, -1.75, -1.75 + 0.14 * k), (10.5, 0.12, 0.08), M.principled(
            f"Cable{k}", ((0.6, 0.08, 0.05), (0.08, 0.2, 0.55), (0.75, 0.6, 0.1))[k], roughness=0.5))
    MODULE = "housing"
    # ---- housing: panelled enclosure (shell -> ghost glass in xray)
    _panel_box("Housing", (-1.6, 0, 0.35), (10.4, 3.2, 4.4), panel, seam, nx=8, nz=3)
    MODULE = None
    if with_path:
        return light_path()
    return None, None


def fab_hall(seed=3, people=6):
    rnd = random.Random(seed)
    floor = M.pbr("HallFloor", "brushed_concrete", scale=0.12, tint=(0.13, 0.135, 0.145), rough_mul=0.3, rough_add=0.03,
                  normal=0.4, fallback=(0.06, 0.065, 0.07))      # polished clean-room concrete (CC0)
    wall = M.principled("HallWall", (0.18, 0.19, 0.2), metallic=0.0, roughness=0.6)
    lamp = M.emission("HallLamp", (0.95, 0.97, 1.0), 6.0)
    bpy.ops.mesh.primitive_plane_add(size=120, location=(0, 0, -2.2))
    fl = bpy.context.object
    fl.name = "HallFloor"
    fl.data.materials.append(floor)
    styles.tag(fl, "env")
    for x in range(-40, 41, 12):                       # columns
        for y in (-14, 14):
            _box(f"Col{x}{y}", (x, y, 4.0), (0.8, 0.8, 12.4), wall, role="env", bevel=0)
    for x in range(-42, 43, 6):                        # ceiling light strips
        _box(f"Lamp{x}", (x, 0, 9.8), (0.25, 26.0, 0.12), lamp, role="env", bevel=0)
    _box("Ceiling", (0, 0, 10.3), (120, 40, 0.4), wall, role="env", bevel=0)
    # trench with the drive-laser beam tube (B1_25)
    _box("Trench", (-12, 0, -2.19), (22, 1.4, 0.02), M.dark_anodized("TrenchDark"), role="env", bevel=0)
    _disc("BeamTubeHall", (-12, 0, -1.85), 0.35, 22, M.polished_steel("TubeSteel", 0.25), rot=(0, math.pi / 2, 0),
          role="env")
    _box("TubeSlot", (-12, -0.36, -1.85), (21, 0.02, 0.08), M.emission("SlotGlass", (0.2, 0.25, 0.3), 0.4),
         role="env", bevel=0)
    sil = M.principled("Silhouette", (0.01, 0.01, 0.012), metallic=0.0, roughness=0.9)
    for i in range(people):                           # backlit human figures for scale (~1.75 m)
        x, y = rnd.uniform(-10, 4), rnd.uniform(-5, 5)
        bpy.ops.mesh.primitive_cylinder_add(radius=0.2, depth=1.45, location=(x, y, -2.2 + 0.73))
        body = bpy.context.object
        body.data.materials.append(sil)
        styles.tag(body, "env")
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.13, location=(x, y, -2.2 + 1.6))
        head = bpy.context.object
        head.data.materials.append(sil)
        styles.tag(head, "env")


HOSTS = {"source": "SrcDrum", "illum": "Illuminator", "reticle": "ReticleStage", "po": "POSection2",
         "wafer": "WaferStage", "base": "Base", "housing": "Housing"}


def attach_small(objs, thresh=None):
    """Parent every part of a module to that module's main body so assembly / explode animations move
    whole modules. Returns the module hosts (plus any untagged top-level meshes)."""
    by_name = {o.name: o for o in objs}
    hosts = {m: by_name[h] for m, h in HOSTS.items() if h in by_name}
    out = list(hosts.values())
    for o in objs:
        if o.type != "MESH" or o.parent is not None or o in out:
            continue
        host = hosts.get(o.get("module"))
        if host is None:
            out.append(o)
            continue
        mw = o.matrix_world.copy()
        o.parent = host
        o.matrix_parent_inverse = host.matrix_world.inverted()
        o.matrix_world = mw
    return out
