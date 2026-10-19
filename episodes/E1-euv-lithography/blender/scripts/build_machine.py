"""Whole-machine layout (stylised, NOT a copy of the ASML exterior) and a generic fab hall.

machine(): modules placed on the real optical train (ZEISS's published NXE layout, see PATH) — tilted
source vessel -> intermediate focus -> four-mirror illuminator -> reticle stage on top -> six-mirror
projection optics -> wafer stage at the bottom — inside a housing tagged `shell`, with one glowing
light path tagged `rays`. Units are metres-ish, the whole machine ~9 m long. fab_hall(): floor, columns, ceiling light
grid, a floor trench for the drive-laser beam tube, backlit human silhouettes for scale.
"""
import math
import random

import bpy

import materials as M
import styles

VIOLET = (0.62, 0.45, 1.0)

# The optical train follows ZEISS's published NXE layout (O. Conradi et al., "Optics for EUV Production",
# 2011 International Symposium on EUV Lithography, slide 5 "The optical train" and slide 20; positions read
# off that drawing in the x-z plane and scaled): plasma above a normal-incidence collector, the beam rising
# through the intermediate focus (a focus, not a mirror) to the field facet mirror at the top; the
# illuminator zig-zags field facet (top) -> pupil facet (bottom) -> third mirror (top) -> fourth mirror
# (bottom) -> reticle on top, face down, hit at a 6 deg chief-ray angle (CRAO = 6 deg, slide 20); six
# projection mirrors M1-M6 (M5 small, just beside the wafer; M6 large, above it) image 4x down to the wafer.
CRAO = math.radians(6.0)
PLASMA = (-3.878, 0.0, -0.608)
IF = (-2.9, 0.0, 1.16)
FACET1 = (-1.795, 0.0, 2.988)                      # field facet mirror
FACET2 = (-1.667, 0.0, 0.565)                      # pupil facet mirror
RETICLE = (0.441, 0.0, 3.438)
ILLUM3 = (-0.35, 0.0, 2.902)
ILLUM4 = (RETICLE[0] - math.tan(CRAO) * (RETICLE[2] - 0.735), 0.0, 0.735)
ILLUM = [FACET1, FACET2, ILLUM3, ILLUM4]
PO_MIRRORS = [(RETICLE[0] + math.tan(CRAO) * (RETICLE[2] - 1.117), 0.0, 1.117),   # M1
              (1.095, 0.0, 2.945), (1.18, 0.0, 0.48), (1.945, 0.0, 0.863),          # M2, M3, M4
              (0.88, 0.0, -0.82), (0.542, 0.0, -0.2)]                               # M5, M6
WAFER = (0.5, 0.0, -1.05)
_axis = [b - a for a, b in zip(PLASMA, IF)]
SRC_AXIS = tuple(v / math.sqrt(sum(c * c for c in _axis)) for v in _axis)          # collector -> plasma -> IF
COLLECTOR = tuple(p - 0.55 * d for p, d in zip(PLASMA, SRC_AXIS))
PATH = [COLLECTOR, IF] + ILLUM + [RETICLE] + PO_MIRRORS + [WAFER]
PO_X, PO_R = 1.3, 0.9                              # projection-optics barrel (axis x, radius)


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
    """n bolt heads on a circle around `axis` ("X", "Z" or any direction vector)."""
    from mathutils import Vector
    a = Vector({"X": (1, 0, 0), "Z": (0, 0, 1)}.get(axis, axis) if isinstance(axis, str) else axis).normalized()
    u = a.orthogonal().normalized()
    v = a.cross(u)
    rot = a.to_track_quat("Z", "Y").to_euler()
    for k in range(n):
        th = 2 * math.pi * k / n
        p = Vector(centre) + r * (math.cos(th) * u + math.sin(th) * v)
        _disc(f"{prefix}{k}", tuple(p), size, 0.05, mat, rot=rot)


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
    # ---- source vessel on its tilted axis (collector -> plasma -> IF): drum with flanges, ports, droplet
    #      generator across the axis, a viewport; a cone with stiffening rings narrowing to the IF
    from mathutils import Vector
    ax = Vector(SRC_AXIS)
    arot = ax.to_track_quat("Z", "Y").to_euler()
    across = Vector((-ax.z, 0.0, ax.x))                      # perpendicular to the axis, in the x-z plane
    drum = Vector(PLASMA) - ax * 0.15
    _disc("SrcDrum", tuple(drum), 1.1, 1.6, dark, rot=arot, role="shell")
    for k, off in enumerate((-0.8, 0.8)):
        c = tuple(drum + ax * off)
        _ring(f"SrcFlange{k}", c, 1.13, 0.06, steel, rot=arot)
        _bolt_circle(f"SrcBolt{k}", c, 1.13, 32, steel, axis=tuple(ax))
    for k, d in enumerate((across, -across, Vector((0, 1, 0)), Vector((0, -1, 0)))):
        prot = d.to_track_quat("Z", "Y").to_euler()
        _disc(f"SrcPort{k}", tuple(drum + d * 1.2), 0.22, 0.35, steel, rot=prot)
        _disc(f"SrcPortFlange{k}", tuple(drum + d * 1.38), 0.3, 0.06, steel, rot=prot)
    _disc("DropletGen", tuple(Vector(PLASMA) + across * 1.75), 0.14, 0.9, steel,
          rot=across.to_track_quat("Z", "Y").to_euler())                      # fires droplets across the axis
    _disc("Viewport", tuple(drum + Vector((0, -1.12, 0)) + ax * 0.45), 0.16, 0.04,
          M.principled("ViewGlass", (0.02, 0.03, 0.05), roughness=0.02, coat=1.0), rot=(math.pi / 2, 0, 0))
    span = (Vector(IF) - drum).length - 0.8                 # drum face -> IF
    bpy.ops.mesh.primitive_cone_add(vertices=96, radius1=1.1, radius2=0.18, depth=span,
                                    location=tuple(drum + ax * (0.8 + span / 2)), rotation=arot)
    cone = bpy.context.object
    cone.name = "SrcCone"
    for p in cone.data.polygons:
        p.use_smooth = True
    cone.data.materials.append(dark)
    styles.tag(cone, "shell")
    _tag_module(cone)
    for k, u in enumerate((0.25, 0.5, 0.75)):
        _ring(f"ConeRib{k}", tuple(drum + ax * (0.8 + span * u)), 1.1 - 0.92 * u + 0.02, 0.03, steel, rot=arot)
    _disc("Collector", COLLECTOR, 0.9, 0.08, mirror, rot=arot)            # faces the plasma and the IF
    _box("SrcPedestal", (drum.x - 0.2, 0, -2.25), (2.4, 2.4, 0.5), dark)   # the source stands on its own footing
    MODULE = "illum"
    # ---- illuminator: panelled box around four mirrors (field facet, pupil facet, two more), as in the
    #      ZEISS optical-train drawing; each mirror sits on its bounce point, normal bisecting the rays
    _panel_box("Illuminator", (-0.95, 0, 1.8), (2.3, 1.3, 2.9), dark, seam, nx=3, nz=2)
    chain = [IF] + ILLUM + [RETICLE]
    for i, (pt, r) in enumerate(zip(ILLUM, (0.42, 0.34, 0.3, 0.2))):
        _mirror(f"Facet{i}" if i < 2 else f"IllumMirror{i + 1}", chain[i], pt, chain[i + 2], r, mirror, mount)
    MODULE = "reticle"
    # ---- reticle stage: platen on linear-motor rails, reticle face down
    rz = RETICLE[2]
    _box("ReticleStage", (0.5, 0, rz + 0.27), (2.4, 1.8, 0.3), steel)
    for y in (-0.95, 0.95):
        _box(f"RetRail{y}", (0.5, y, rz + 0.07), (4.2, 0.16, 0.14), dark)
        for k in range(12):
            _box(f"RetMagnet{y}{k}", (-1.4 + 0.34 * k, y, rz + 0.15), (0.26, 0.17, 0.03), steel, bevel=0.005)
    _box("Reticle", (RETICLE[0], 0, RETICLE[2] + 0.05), (0.6, 0.6, 0.06), mirror, bevel=0.005)
    MODULE = "po"
    # ---- projection optics: a stacked barrel with flanges and struts, six mirrors with mounts
    for k in range(7):                                      # barrel from just above the wafer to under the reticle
        z = -0.6 + 0.55 * k
        _disc(f"POSection{k}", (PO_X, 0, z), PO_R, 0.51, dark, role="shell")
        _ring(f"POFlange{k}", (PO_X, 0, z + 0.27), PO_R + 0.04, 0.045, steel, rot=(0, 0, 0))
    _box("POColumn", (PO_X, 0, 1.05), (1.8, 1.8, 3.8), dark, role="shell").hide_render = True   # kept for scripts
    for k in range(6):
        th = 2 * math.pi * k / 6 + 0.3
        _disc(f"POStrut{k}", (PO_X + 1.08 * math.cos(th), 1.08 * math.sin(th), 1.05), 0.04, 3.9, steel)
    seq = [RETICLE] + PO_MIRRORS + [WAFER]
    for i, (pt, r) in enumerate(zip(PO_MIRRORS, (0.22, 0.26, 0.14, 0.24, 0.12, 0.34))):   # M5 small, M6 large
        _mirror(f"POMirror{i}", seq[i], pt, seq[i + 2], r, mirror, mount)
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
    _box("Base", (-0.2, 0, -1.9), (5.8, 3.4, 0.6), dark)                 # under the scanner (not the source)
    for x in (-2.6, -0.8, 1.0, 2.4):
        for y in (-1.4, 1.4):
            _disc(f"Isolator{x}{y}", (x, y, -2.35), 0.22, 0.3, steel)
    for k in range(3):                                                     # cable trays along the base
        _box(f"CableTray{k}", (-0.2, -1.75, -1.75 + 0.14 * k), (5.4, 0.12, 0.08), M.principled(
            f"Cable{k}", ((0.6, 0.08, 0.05), (0.08, 0.2, 0.55), (0.75, 0.6, 0.1))[k], roughness=0.5))
    MODULE = "housing"
    # ---- housing: panelled enclosure (shell -> ghost glass in xray)
    _panel_box("Housing", (-1.6, 0, 0.95), (8.4, 3.2, 6.0), panel, seam, nx=7, nz=3)
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
