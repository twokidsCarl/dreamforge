"""Whole-machine layout (stylised, NOT a copy of the ASML exterior) and a generic fab hall.

machine(): the High-NA EUV scanner (EXE:5000) laid out from published ASML/ZEISS drawings (see PATH): source
unit beside the scanner -> intermediate focus -> illuminator -> reticle stage on top -> six-mirror projection
optics with the holed M6/M5 pair -> wafer stage at the bottom — scanner inside a housing tagged `shell`, one
glowing light path tagged `rays`. Units are metres-ish. fab_hall(): floor, columns, ceiling light
grid, a floor trench for the drive-laser beam tube, backlit human silhouettes for scale.
"""
import math
import random

import bpy

import materials as M
import styles

VIOLET = (0.62, 0.45, 1.0)

# The machine is the High-NA EUV scanner (ASML EXE:5000) that A0 follows to Intel. Every position below is
# taken from published ASML/ZEISS material, collected with quotes in research/visual/high_na_optics.md:
# - module arrangement, side view [ASML, van Schoot, EUVL Workshop 2022, slide 34]: mask tier on top (mask
#   handler + mask stage), optics in the middle (projection optics "POB" on one side, illuminator on the source
#   side), base frame and wafer stage at the bottom; the source is a separate unit standing beside the scanner,
#   its collector facing the illuminator, with an optical platform (drive-laser beam delivery) further out.
# - optical train [ZEISS, Kaumanns et al., EUVL Workshop 2024, slide 13 "Current 0.55 NA"]: plasma ->
#   collector -> intermediate focus (a focus, not a mirror) -> small fold mirror -> field facet mirror (top)
#   -> pupil facet mirror -> reticle (top, face down) -> six-mirror projection optics -> wafer.
# - projection optics [ASML/ZEISS "design example", van Schoot, EUVL Workshop 2021, slide 35; Heil et al.,
#   EUVL Symposium 2015, slides 9/19/20]: M1-M4 zig-zag in a narrow column under the reticle; the beam then goes
#   down through a central hole in the large last mirror M6 to M5 just above the wafer, back up to M6, and
#   M6 focuses it down through M5's own hole onto the wafer (central obscuration ~20% of the pupil).
#   Positions are (x, height) read off that drawing as fractions of the reticle-to-wafer distance, mirrored
#   so the source side is +x.
# - chief-ray angle at the reticle 5.4 deg [ZEISS 2024 slide 9; ASML gives ~5.3 deg], so the ray from the
#   pupil facet mirror and the ray to M1 each lean 5.4 deg from the reticle normal.
# Not public (drawn as a plausible fit, labelled 示意 on screen): exact illuminator mirror count and spacing,
# source axis elevation, machine dimensions.
CRAO = math.radians(5.4)
H_PO = 4.5                                          # reticle-to-wafer distance (scene units)
WAFER = (0.0, 0.0, -1.05)


def _po(xf, hf):
    """A point of the published PO drawing: (x, height) as fractions of the reticle-wafer distance."""
    return (-xf * H_PO, 0.0, WAFER[2] + hf * H_PO)          # mirrored: the source side is +x


M1 = _po(-0.018, 0.625)
PO_MIRRORS = [M1, _po(0.12, 0.866), _po(0.067, 0.40), _po(-0.0625, 0.584),   # M1, M2, M3, M4
              _po(0.0, 0.036), _po(0.0, 0.344)]                               # M5 (holed, at the wafer), M6 (holed)
PO_FOCUS = _po(-0.035, 0.375)                       # the intermediate image just above M6
M6_R, M5_R = 0.195 * H_PO, 0.08 * H_PO              # radii (drawing widths 0.39 and 0.16 of the height)
RETICLE = (M1[0] + math.tan(CRAO) * (WAFER[2] + H_PO - M1[2]), 0.0, WAFER[2] + H_PO)
FACET2 = (RETICLE[0] + math.tan(CRAO) * 1.45, 0.0, RETICLE[2] - 1.45)          # pupil facet mirror
FACET1 = (1.75, 0.0, 2.95)                          # field facet mirror, top
FOLD = (2.85, 0.0, 0.55)                            # small fold mirror right after the IF
IF = (3.6, 0.0, 0.75)
_d = [i - f for i, f in zip(IF, FOLD)]
SRC_AXIS = tuple(v / math.sqrt(sum(c * c for c in _d)) for v in _d)           # points from the IF to the plasma
PLASMA = tuple(i + 2.2 * a for i, a in zip(IF, SRC_AXIS))
COLLECTOR = tuple(p + 0.55 * a for p, a in zip(PLASMA, SRC_AXIS))             # behind the plasma, facing the IF
ILLUM = [FOLD, FACET1, FACET2]
M6_HIT = (M6_R * 0.62, 0.0, PO_MIRRORS[5][2])        # where the drawn ray meets M6 after M5 (off-axis, outside the hole)
# M5 is holed too: the ray must reflect off its annulus, not at its centre (the hole). From PO_FOCUS it passes M6's hole
# (x ~0.16 < 0.193), reflects on M5 at x = 0.20 (> hole 0.079), goes up to M6_HIT and down through M5's hole (x ~0.06)
M5_HIT = (0.20, 0.0, PO_MIRRORS[4][2])
PATH = ([COLLECTOR, IF] + ILLUM + [RETICLE] + PO_MIRRORS[:4] + [PO_FOCUS, M5_HIT, M6_HIT, WAFER])
CENTER = (2.9, 0.0, 0.8)                            # middle of scanner + source, for cameras


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


def _annulus(name, loc, r_out, r_in, thick, mat, role="structure"):
    """A horizontal disc with a central hole (the obscured last two mirrors of the High-NA projection optics)."""
    import bmesh
    bm = bmesh.new()
    n = 96
    outer = [bm.verts.new((r_out * math.cos(2 * math.pi * k / n), r_out * math.sin(2 * math.pi * k / n), 0)) for k in range(n)]
    inner = [bm.verts.new((r_in * math.cos(2 * math.pi * k / n), r_in * math.sin(2 * math.pi * k / n), 0)) for k in range(n)]
    for k in range(n):
        j = (k + 1) % n
        bm.faces.new((outer[k], outer[j], inner[j], inner[k]))
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = loc
    ob.modifiers.new("Thick", "SOLIDIFY").thickness = thick
    for pl in ob.data.polygons:
        pl.use_smooth = True
    ob.data.materials.append(mat)
    styles.tag(ob, role)
    return _tag_module(ob)


def machine(with_path=True):
    from mathutils import Vector
    global MODULE
    steel = M.polished_steel("MachSteel", 0.3)
    dark = M.dark_anodized("MachDark")
    mount = M.principled("MirrorMount", (0.08, 0.085, 0.09), metallic=0.9, roughness=0.3)
    mirror = M.multilayer_mirror("MachMirror", r_max=0.5)
    panel = M.principled("HousingPanel", (0.78, 0.8, 0.82), metallic=0.2, roughness=0.45)
    seam = M.principled("PanelSeam", (0.05, 0.05, 0.055), roughness=0.6)
    # ---- source: a separate unit beside the scanner [ASML 2022 s.34]: vessel on a pedestal, collector
    #      inside facing the illuminator, optical platform (drive-laser beam delivery) further out
    MODULE = "source"
    ax = Vector(SRC_AXIS)                                   # from the IF towards the plasma / collector
    arot = (-ax).to_track_quat("Z", "Y").to_euler()         # local +Z looks from the collector to the IF
    across = Vector((-ax.z, 0.0, ax.x))
    drum = Vector(PLASMA) + ax * 0.15
    _disc("SrcDrum", tuple(drum), 1.1, 1.6, dark, rot=arot, role="shell")
    for k, off in enumerate((-0.8, 0.8)):
        c = tuple(drum + ax * off)
        _ring(f"SrcFlange{k}", c, 1.13, 0.06, steel, rot=arot)
        _bolt_circle(f"SrcBolt{k}", c, 1.13, 32, steel, axis=tuple(ax))
    for k, d in enumerate((across, -across)):
        prot = d.to_track_quat("Z", "Y").to_euler()
        _disc(f"SrcPort{k}", tuple(drum + d * 1.2), 0.22, 0.35, steel, rot=prot)
        _disc(f"SrcPortFlange{k}", tuple(drum + d * 1.38), 0.3, 0.06, steel, rot=prot)
    # droplet generator and catcher on opposite flanks, on one horizontal line through the plasma, at right angles
    # to the collector axis [research/visual/euv_source.md, section 1]
    yrot = (math.pi / 2, 0, 0)
    _disc("DropletGen", tuple(Vector(PLASMA) + Vector((0, 1.75, 0))), 0.14, 0.9, steel, rot=yrot)
    _disc("DropletCatcher", tuple(Vector(PLASMA) + Vector((0, -1.6, 0))), 0.2, 0.6, steel, rot=yrot)
    _disc("Viewport", tuple(drum + Vector((0, -1.12, 0)) + ax * 0.45), 0.16, 0.04,
          M.principled("ViewGlass", (0.02, 0.03, 0.05), roughness=0.02, coat=1.0), rot=(math.pi / 2, 0, 0))
    span = (Vector(IF) - drum).length - 0.8                 # vessel face -> IF
    bpy.ops.mesh.primitive_cone_add(vertices=96, radius1=1.1, radius2=0.18, depth=span,
                                    location=tuple(drum - ax * (0.8 + span / 2)), rotation=arot)
    cone = bpy.context.object
    cone.name = "SrcCone"
    for pl in cone.data.polygons:
        pl.use_smooth = True
    cone.data.materials.append(dark)
    styles.tag(cone, "shell")
    _tag_module(cone)
    for k, u in enumerate((0.25, 0.5, 0.75)):
        _ring(f"ConeRib{k}", tuple(drum - ax * (0.8 + span * u)), 1.1 - 0.92 * u + 0.02, 0.03, steel, rot=arot)
    # collector: a concave (ellipsoidal) shell with a central hole for the drive laser, facing the IF
    # (euv_source.md s.5; a flat disc read as a plate). Depth ~0.28 of the radius, drawn as a paraboloid.
    import bmesh
    bmc = bmesh.new()
    nr, ns, r_out, r_in, depth = 10, 96, 0.9, 0.14, 0.26
    rings = []
    for i in range(nr + 1):
        r = r_in + (r_out - r_in) * i / nr
        z = depth * (r * r) / (r_out * r_out)              # rim leans toward the IF (local +Z)
        rings.append([bmc.verts.new((r * math.cos(2 * math.pi * k / ns), r * math.sin(2 * math.pi * k / ns), z))
                      for k in range(ns)])
    for i in range(nr):
        for k in range(ns):
            j = (k + 1) % ns
            bmc.faces.new((rings[i][k], rings[i][j], rings[i + 1][j], rings[i + 1][k]))
    mec = bpy.data.meshes.new("Collector")
    bmc.to_mesh(mec)
    bmc.free()
    col = bpy.data.objects.new("Collector", mec)
    bpy.context.scene.collection.objects.link(col)
    col.location = Vector(COLLECTOR) - (-ax) * depth * 0.5
    col.rotation_euler = arot
    col.modifiers.new("Thick", "SOLIDIFY").thickness = -0.05
    for pl in mec.polygons:
        pl.use_smooth = True
    mec.materials.append(mirror)
    styles.tag(col, "structure")
    _tag_module(col)
    _box("SrcPedestal", (drum.x, 0, -1.05), (2.6, 2.6, 2.7), dark)          # up to the vessel's underside
    plat = PLASMA[0] + 2.6
    _box("OpticalPlatform", (plat, 0, 1.0), (2.2, 2.0, 0.25), steel)
    for dx in (-0.95, 0.95):
        for dy in (-0.85, 0.85):
            _box(f"PlatformLeg{dx}{dy}", (plat + dx, dy, -0.7), (0.3, 0.3, 3.2), steel)
    # ---- illuminator on the source side of the optics tier: fold mirror after the IF, field facet mirror
    #      (top), pupil facet mirror; its housing is wider at the top and reaches over the PO's shoulder
    MODULE = "illum"
    _panel_box("Illuminator", (2.15, 0, 1.75), (2.2, 1.4, 2.9), dark, seam, nx=3, nz=2)
    _panel_box("IllumArm", (0.7, 0, 2.55), (0.9, 1.2, 1.3), dark, seam, nx=2, nz=1)
    chain = [IF] + ILLUM + [RETICLE]
    for i, (pt, r, nm) in enumerate(zip(ILLUM, (0.2, 0.45, 0.16), ("FoldMirror", "Facet0", "Facet1"))):
        _mirror(nm, chain[i], pt, chain[i + 2], r, mirror, mount)
    # ---- mask tier: mask stage on long linear-motor rails, mask handler beside it, reticle face down
    MODULE = "reticle"
    rz = RETICLE[2]
    _box("ReticleStage", (RETICLE[0], 0, rz + 0.27), (2.4, 1.8, 0.3), steel)
    for y in (-0.95, 0.95):
        _box(f"RetRail{y}", (RETICLE[0], y, rz + 0.07), (4.6, 0.16, 0.14), dark)
        for k in range(13):
            _box(f"RetMagnet{y}{k}", (RETICLE[0] - 2.1 + 0.35 * k, y, rz + 0.15), (0.26, 0.17, 0.03), steel, bevel=0.005)
    _box("Reticle", (RETICLE[0], 0, RETICLE[2] + 0.05), (0.6, 0.6, 0.06),          # dark plate, as ASML draws it
         M.principled("ReticlePlate", (0.08, 0.085, 0.09), metallic=0.6, roughness=0.15), bevel=0.005)
    _panel_box("MaskHandler", (-2.6, 0, rz + 0.3), (1.4, 1.6, 0.9), dark, seam, nx=2, nz=1)
    # ---- projection optics: a narrow upper column for M1-M4 with a step where the illuminator reaches in,
    #      a wide lower drum around the holed M6 / M5 pair
    MODULE = "po"
    _disc("POBarrel", (0, 0, -0.1), M6_R + 0.12, 1.75, dark, role="shell")
    _ring("POFlangeLow", (0, 0, 0.77), M6_R + 0.16, 0.05, steel, rot=(0, 0, 0))
    _panel_box("POColumn", (-0.35, 0, 1.35), (1.25, 1.3, 1.25), dark, seam, nx=2, nz=1)
    _panel_box("POColumnTop", (-0.48, 0, 2.55), (1.0, 1.3, 1.15), dark, seam, nx=2, nz=1)
    seq = [RETICLE] + PO_MIRRORS[:4] + [PO_FOCUS]
    for i, r in enumerate((0.2, 0.3, 0.4, 0.2)):
        _mirror(f"POMirror{i}", seq[i], seq[i + 1], seq[i + 2], r, mirror, mount)
    m5, m6 = PO_MIRRORS[4], PO_MIRRORS[5]
    _annulus("POMirror4", m5, M5_R, M5_R * 0.22, 0.05, mirror)                   # M5: faces up, holed
    _annulus("POMirror5", m6, M6_R, M6_R * 0.22, -0.06, mirror)                 # M6: faces down, holed
    _annulus("POMirror5Substrate", (m6[0], 0, m6[2] + 0.1), M6_R * 0.98, M6_R * 0.24, 0.14,
             M.principled("Substrate", (0.85, 0.86, 0.88), roughness=0.25))
    _ring("POMirror5Mount", (m6[0], 0, m6[2] + 0.05), M6_R * 1.03, 0.04, mount, rot=(0, 0, 0))
    for k in range(6):
        th = 2 * math.pi * k / 6 + 0.3
        _disc(f"POStrut{k}", ((M6_R + 0.22) * math.cos(th), (M6_R + 0.22) * math.sin(th), 0.0), 0.04, 1.9, steel)
    # ---- wafer stage on the base, wafer under the PO; wafer handler at the far side
    MODULE = "wafer"
    _box("WaferStage", (0, 0, -1.35), (2.8, 2.8, 0.35), steel)
    tile = M.principled("MotorTile", (0.12, 0.12, 0.13), metallic=0.8, roughness=0.35)
    for i in range(6):
        for j in range(6):
            _box(f"Tile{i}{j}", (-1.25 + 0.5 * i, -1.25 + 0.5 * j, -1.56), (0.46, 0.46, 0.04), tile, bevel=0.01)
    _disc("Chuck", (WAFER[0], 0, WAFER[2] - 0.04), 0.5, 0.05, steel)
    _disc("Wafer", WAFER, 0.45, 0.02, M.principled("WaferSi", (0.30, 0.31, 0.36), metallic=0.7, roughness=0.12))
    _panel_box("WaferHandler", (-2.7, 0, -1.4), (1.2, 1.6, 1.6), dark, seam, nx=2, nz=1)
    # ---- base frame on vibration isolators, under the scanner (the source stands on its own)
    MODULE = "base"
    _box("Base", (0.5, 0, -1.9), (6.4, 3.4, 0.6), dark)
    for x in (-2.2, -0.4, 1.4, 3.2):
        for y in (-1.4, 1.4):
            _disc(f"Isolator{x}{y}", (x, y, -2.35), 0.22, 0.3, steel)
    for k in range(3):                                                     # cable trays along the base
        _box(f"CableTray{k}", (0.5, -1.75, -1.75 + 0.14 * k), (6.0, 0.12, 0.08), M.principled(
            f"Cable{k}", ((0.6, 0.08, 0.05), (0.08, 0.2, 0.55), (0.75, 0.6, 0.1))[k], roughness=0.5))
    # ---- housing: panelled enclosure over the scanner (shell -> ghost glass in xray)
    MODULE = "housing"
    _panel_box("Housing", (0.3, 0, 0.95), (7.0, 3.2, 6.0), panel, seam, nx=6, nz=3)
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
    # (no drive-laser tube on this floor: the laser sits in the sub-fab and its beam comes up through the slab, F62;
    #  b1_machine.subfab() draws that level)
    sil = M.principled("Silhouette", (0.01, 0.01, 0.012), metallic=0.0, roughness=0.9)
    import figures
    for i in range(people):                           # backlit human figures for scale (~1.75 m)
        x, y = rnd.uniform(-10, 4), rnd.choice((-1, 1)) * rnd.uniform(2.4, 5.0)   # in the aisles, not in the machine
        figures.person(f"Worker{i}", (x, y, -2.2), height=rnd.uniform(1.65, 1.85),
                       pose=rnd.choice(("stand", "work", "walk")), facing=rnd.uniform(-60, 60), mat=sil)


HOSTS = {"source": "SrcDrum", "illum": "Illuminator", "reticle": "ReticleStage", "po": "POBarrel",
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
