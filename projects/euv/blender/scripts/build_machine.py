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
    return ob


def _disc(name, loc, r, depth, mat, rot=(0, 0, 0), role="structure"):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=depth, vertices=64, location=loc, rotation=rot)
    ob = bpy.context.object
    ob.name = name
    for p in ob.data.polygons:
        p.use_smooth = True
    ob.data.materials.append(mat)
    styles.tag(ob, role)
    return ob


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


def machine(with_path=True):
    steel = M.polished_steel("MachSteel", 0.3)
    dark = M.dark_anodized("MachDark")
    mirror = M.multilayer_mirror("MachMirror", r_max=0.5)
    panel = M.principled("HousingPanel", (0.78, 0.8, 0.82), metallic=0.2, roughness=0.45)
    # source vessel: drum + cone toward IF
    _disc("SrcDrum", (-5.6, 0, 0), 1.1, 1.6, dark, rot=(0, math.pi / 2, 0), role="shell")
    bpy.ops.mesh.primitive_cone_add(vertices=64, radius1=1.1, radius2=0.18, depth=2.0, location=(-3.8, 0, 0),
                                    rotation=(0, math.pi / 2, 0))
    cone = bpy.context.object
    cone.name = "SrcCone"
    cone.data.materials.append(dark)
    styles.tag(cone, "shell")
    _disc("Collector", (-6.2, 0, 0), 0.9, 0.08, mirror, rot=(0, math.pi / 2, 0))
    # illuminator with two facet mirrors
    _box("Illuminator", (-1.45, 0, 1.3), (2.1, 1.3, 1.4), dark, role="shell")
    for i, pt in enumerate((FACET1, FACET2)):
        rot = _mirror_rot(PATH[1 + i], pt, PATH[3 + i])
        _disc(f"Facet{i}", pt, 0.32, 0.06, mirror, rot=rot)
    # reticle stage on top, reticle underside facing down
    _box("ReticleStage", (0.5, 0, 2.62), (2.4, 1.8, 0.3), steel)
    _box("Reticle", (RETICLE[0], 0, RETICLE[2] + 0.05), (0.6, 0.6, 0.06), mirror, bevel=0.005)
    # projection optics column with six mirrors
    _box("POColumn", (0.5, 0, 0.6), (1.6, 1.6, 2.6), dark, role="shell")
    seq = [RETICLE] + PO_MIRRORS + [WAFER]
    for i, pt in enumerate(PO_MIRRORS):
        rot = _mirror_rot(seq[i], pt, seq[i + 2])
        _disc(f"POMirror{i}", pt, 0.22 if i < 5 else 0.3, 0.05, mirror, rot=rot)
    # wafer stage at the bottom
    _box("WaferStage", (0.5, 0, -1.35), (2.8, 2.8, 0.35), steel)
    _disc("Wafer", WAFER, 0.45, 0.02, M.multilayer_mirror("WaferFilm", r_max=0.45))
    _box("Base", (-1.5, 0, -1.9), (11.0, 3.4, 0.6), dark)
    # housing: big rounded panels around everything (shell -> ghost glass in xray)
    _box("Housing", (-1.6, 0, 0.35), (10.4, 3.2, 4.4), panel, role="shell", bevel=0.25)
    if with_path:
        return light_path()
    return None, None


def fab_hall(seed=3, people=6):
    rnd = random.Random(seed)
    floor = M.principled("HallFloor", (0.06, 0.065, 0.07), metallic=0.0, roughness=0.12)
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
