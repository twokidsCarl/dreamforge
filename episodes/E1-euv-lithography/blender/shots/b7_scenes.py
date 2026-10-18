"""B7 — projection optics and High-NA (F7, F11–F13, F18, F20, F39, F40). Variants:

  po        B7_01  xray: six mirrors (M1–M6) on a folded path, each lighting up as the beam arrives
  crate     B7_05  night loading dock: a white crate marked "EXE 示意" pushed into a container
  turntable B7_06  clay High-NA projection-optics silhouette turning, a clay figure for scale
  cones     B7_09  energy: incident and reflected cones on the mask overlap and clash
            B7_11  the cones slim in the scan direction and tilt 6° -> 5.4°; a dark gap opens
            B7_12  close on the gap, a photon sliding along an edge
  holed     B7_14  photoreal: a huge concave mirror with a central hole, a second one behind
            B7_15  fly through the hole; violet light converges past the camera to the wafer
All shapes illustrative, not the real design.
"""
import math
import random

import bmesh
import bpy
from mathutils import Vector

import build_machine as BM
import common as C
import materials as M
import sample_b1 as B
import styles

FRAMES = 340
VIOLET = (0.62, 0.45, 1.0)


def _key(ob, f, **kw):
    for k, v in kw.items():
        setattr(ob, k, v)
        ob.keyframe_insert(k, frame=f)


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


def _curve(name, pts, mat, radius=0.03, role="rays"):
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


# ---- B7_01 ---------------------------------------------------------------------------------
PO_PATH = [Vector(p) for p in ((0.0, 0, 7.0), (1.6, 0, 5.2), (-1.4, 0, 6.0), (1.8, 0, 3.4), (-1.6, 0, 2.4),
                               (1.2, 0, 0.9), (-0.5, 0, 0.1), (0.3, 0, -1.6))]


def po(sc, rnd):
    C.set_world(top=(0.9, 0.91, 0.93), horizon=(0.78, 0.79, 0.82), bottom=(0.6, 0.61, 0.64))
    mirror = M.multilayer_mirror("POMirror", r_max=0.9)
    ring_mats = []
    for i in range(1, 7):
        rot = BM._mirror_rot(tuple(PO_PATH[i - 1]), tuple(PO_PATH[i]), tuple(PO_PATH[i + 1]))
        _cyl(f"M{i}", 0.75 if i < 6 else 1.0, 0.16, tuple(PO_PATH[i]), mirror, rot=rot)
        rm = M.emission(f"Ring{i}", (0.7, 0.55, 1.0), 0.0)
        bpy.ops.mesh.primitive_torus_add(major_radius=0.78 if i < 6 else 1.03, minor_radius=0.03,
                                         location=tuple(PO_PATH[i]), rotation=rot)
        t = bpy.context.object
        t.data.materials.append(rm)
        styles.tag(t, "emitter")
        ring_mats.append(rm)
    # mask on top, wafer at the bottom, a ghost-glass housing around the mirrors
    _box("Mask", (0, 0, 7.2), (2.2, 2.2, 0.12), M.multilayer_mirror("MaskTop", r_max=1.0))
    _cyl("Wafer", 0.9, 0.03, tuple(PO_PATH[-1]), M.multilayer_mirror("WaferTop", r_max=0.9))
    _box("POHousing", (0.1, 0, 2.6), (5.0, 3.0, 7.4), M.principled("POPanel", (0.78, 0.8, 0.82), metallic=0.2,
                                                                 roughness=0.45), role="shell", bevel=0.2)
    beam = _curve("POBeam", [tuple(p) for p in PO_PATH], M.emission("POBeamMat", VIOLET, 6.0))
    beam.data.bevel_factor_end = 0.0
    beam.data.keyframe_insert("bevel_factor_end", frame=1)
    beam.data.bevel_factor_end = 1.0
    beam.data.keyframe_insert("bevel_factor_end", frame=120)
    n = len(PO_PATH) - 1
    for i, rm in enumerate(ring_mats, start=1):                   # each mirror lights as the beam arrives
        f = 1 + int(119 * i / n)
        M.set_emission_strength(rm, f - 1, 0.0)
        M.set_emission_strength(rm, f + 2, 8.0)
        M.set_emission_strength(rm, f + 14, 2.5)
    B._camera("CamB7_01", [(1, (0.3, 0, 6.2), (2.6, -6.5, 7.6), 35, 8.0),
                           (60, (0.2, 0, 3.6), (2.8, -7.5, 4.4), 35, 8.0),
                           (120, (0.1, 0, 0.6), (2.4, -8.0, 1.8), 35, 8.0),
                           (167, (0.1, 0, 2.8), (7.0, -11.0, 9.0), 35, 8.0)])


# ---- B7_05 ---------------------------------------------------------------------------------
def _text(body, loc, rot, size, mat, extrude=0.0):
    cu = bpy.data.curves.new("T_" + body, "FONT")
    cu.body = body
    cu.size = size
    cu.extrude = extrude
    cu.align_x = "CENTER"
    try:
        cu.font = bpy.data.fonts.load("/System/Library/Fonts/STHeiti Medium.ttc")
    except Exception:
        pass
    ob = bpy.data.objects.new("T_" + body, cu)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = loc
    ob.rotation_euler = rot
    ob.data.materials.append(mat)
    styles.tag(ob, "structure")
    return ob


def crate(sc, rnd):
    C.set_world(top=(0.004, 0.006, 0.012), horizon=(0.003, 0.004, 0.007), bottom=(0.0, 0.0, 0.001))
    wet = M.pbr("WetAsphalt", "asphalt_02", scale=0.25, tint=(0.11, 0.115, 0.13), rough_mul=0.22, rough_add=0.01,
                normal=0.6, fallback=(0.02, 0.022, 0.025))                     # wet asphalt (CC0)
    _box("Ground", (0, 0, -0.05), (60, 60, 0.1), wet)
    wall = M.principled("DockWall", (0.12, 0.13, 0.14), roughness=0.7)
    _box("Wall", (0, 14.0, 4.0), (40, 0.4, 8), wall)
    _box("DockOpening", (-2.0, 13.7, 2.4), (6.0, 0.2, 4.4), M.emission("DockGlow", (0.7, 0.8, 0.95), 0.6))
    # container: open end facing -Y (toward the forklift)
    steel = M.pbr("Container", "container_side", scale=0.4, tint=(0.55, 0.75, 1.0), metallic=0.3, fallback=(0.18, 0.26, 0.34))
    for (x, y, z, sx, sy, sz) in ((5.0 - 1.2, 6.0, 1.45, 0.06, 12.0, 2.9), (5.0 + 1.2, 6.0, 1.45, 0.06, 12.0, 2.9),
                                  (5.0, 6.0, 2.9, 2.44, 12.0, 0.06), (5.0, 6.0, 0.02, 2.44, 12.0, 0.04),
                                  (5.0, 12.0, 1.45, 2.44, 0.06, 2.9)):
        _box("ContainerPanel", (x, y, z), (sx, sy, sz), steel)
    door = _box("ContainerDoor", (3.8 - 0.6, -0.3, 1.45), (1.2, 0.06, 2.8), steel)
    door.rotation_euler = (0, 0, math.radians(-75))
    # the crate (white plywood) carried on the forks
    ply = M.principled("Crate", (0.82, 0.8, 0.74), roughness=0.75)
    crate_ob = _box("Crate", (0, 0, 0), (2.2, 3.0, 1.8), ply, bevel=0.02)
    bpy.ops.object.select_all(action="DESELECT")
    crate_ob.select_set(True)
    bpy.context.view_layer.objects.active = crate_ob
    bpy.ops.object.transform_apply(scale=True)
    ink = M.principled("Stencil", (0.05, 0.05, 0.06), roughness=0.8)
    for txt, z, size in (("EXE 示意", 0.25, 0.34), ("2023.12", -0.3, 0.26)):
        t = _text(txt, (0, 0, 0), (math.pi / 2, 0, -math.pi / 2), size, ink)
        t.parent = crate_ob
        t.location = (-1.112, 0, z)
    yel = M.principled("Forklift", (0.75, 0.55, 0.08), roughness=0.4)
    lift = _box("ForkBody", (0, 0, 0.8), (1.3, 1.9, 1.3), yel, bevel=0.06)
    mast = _box("Mast", (0, 0, 0), (1.0, 0.12, 3.0), M.dark_anodized("MastMetal"))
    mast.parent = lift
    mast.location = (0, 1.05, 0.8)
    crate_ob.parent = lift
    crate_ob.location = (0, 2.7, 0.35)
    _key(lift, 1, location=(5.0, -6.2, 0.8))
    _key(lift, 105, location=(5.0, -2.6, 0.8))
    for k in range(5):                                          # cold top lights
        x = -2 + 2.5 * k
        bpy.ops.object.light_add(type="AREA", location=(x, -2.0, 7.0))
        l = bpy.context.object
        l.data.energy = 260
        l.data.size = 1.2
        l.data.color = (0.82, 0.9, 1.0)
        styles.tag(l, "rig")
        _box(f"Lamp{k}", (x, -2.0, 7.05), (1.2, 1.2, 0.05), M.emission(f"LampMat{k}", (0.85, 0.92, 1.0), 6.0),
             role="emitter")
    B._camera("CamB7_05", [(1, (4.6, -2.8, 1.3), (-3.4, -6.4, 0.45), 35, 2.8),
                           (105, (4.8, -1.0, 1.3), (-3.2, -5.6, 0.45), 35, 2.8)])


# ---- B7_06 ---------------------------------------------------------------------------------
def turntable(sc, rnd):
    clay = M.principled("ClayPO", (0.7, 0.7, 0.7))
    floor = _box("Floor", (0, 0, -0.05), (40, 40, 0.1), clay)
    bpy.ops.object.empty_add(location=(0, 0, 0))
    root = bpy.context.object
    root.name = "PORoot"
    parts = []
    parts.append(_cyl("Barrel", 1.1, 1.6, (0, 0, 1.0), clay))
    parts.append(_box("UpperFrame", (0.3, 0, 2.6), (2.8, 2.2, 1.6), clay, bevel=0.08))
    parts.append(_box("SideTower", (-1.4, 0.2, 1.9), (0.8, 1.4, 3.4), clay, bevel=0.06))
    parts.append(_cyl("TopRing", 1.25, 0.18, (0.3, 0, 3.5), clay))
    for k in range(10):                                        # framework ribs
        th = 2 * math.pi * k / 10
        parts.append(_cyl(f"Rib{k}", 0.05, 2.0, (1.3 * math.cos(th), 1.3 * math.sin(th), 1.6), clay, verts=12))
    for k in range(3):
        parts.append(_cyl(f"Flange{k}", 1.22, 0.08, (0, 0, 0.35 + 0.65 * k), clay))
    for k in range(48):                                        # bolt circles
        th = 2 * math.pi * k / 48
        parts.append(_cyl(f"Bolt{k}", 0.03, 0.08, (1.2 * math.cos(th), 1.2 * math.sin(th), 3.62), clay, verts=8))
    for p in parts:
        p.parent = root
    # clay figure for scale (faceless mannequin, 1.75 m)
    fig = []
    fig.append(_cyl("FigLegs", 0.16, 0.85, (3.0, -1.2, 0.43), clay, verts=24))
    fig.append(_cyl("FigBody", 0.2, 0.7, (3.0, -1.2, 1.2), clay, verts=24))
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.12, location=(3.0, -1.2, 1.68))
    head = bpy.context.object
    head.data.materials.append(clay)
    styles.tag(head, "structure")
    _key(root, 1, rotation_euler=(0, 0, 0))
    _key(root, 144, rotation_euler=(0, 0, math.radians(50)))
    for fc in C.fcurves(root.animation_data.action):
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR"
    B._area("ClayKey", (5, -6, 8), (0.8, 0, 0.6), 8, 1800, (1.0, 0.98, 0.95))
    B._camera("CamB7_06", [(1, (0.6, 0, 1.6), (8.5, -8.5, 3.2), 50, 5.6), (144, (0.6, 0, 1.7), (9.5, -7.0, 3.4), 50, 5.6)])


# ---- B7_09 / B7_11 / B7_12 -----------------------------------------------------------------
def _cone_mat(name, strength):
    """Glassy violet light cone: brighter at grazing edges, transparent in the middle."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    lw = nt.nodes.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.35
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (0.5, 0.3, 1.0, 1)
    mul = nt.nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    mul.inputs[1].default_value = strength
    add = nt.nodes.new("ShaderNodeMath")
    add.operation = "ADD"
    add.inputs[1].default_value = 0.25
    nt.links.new(lw.outputs["Facing"], add.inputs[0])
    nt.links.new(add.outputs[0], mul.inputs[0])
    nt.links.new(mul.outputs[0], em.inputs["Strength"])
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    addsh = nt.nodes.new("ShaderNodeAddShader")
    nt.links.new(tr.outputs[0], addsh.inputs[0])
    nt.links.new(em.outputs[0], addsh.inputs[1])
    nt.links.new(addsh.outputs[0], out.inputs["Surface"])
    m.surface_render_method = "BLENDED"          # additive glow; dithered would discard it
    return m


def _cone(name, apex, axis_tilt_deg, half_deg, length, mat, side):
    """Cone with its apex on the mask point, axis tilted from the normal (+Z) toward side (-1/+1) in XZ.
    The cone's scan-direction (X) opening is scaled separately, so we keep half angle in a scale."""
    bpy.ops.mesh.primitive_cone_add(vertices=96, radius1=0.0, radius2=length * math.tan(math.radians(half_deg)),
                                    depth=length, end_fill_type="NOTHING", location=(0, 0, length / 2))
    ob = bpy.context.object
    ob.name = name
    bpy.ops.object.transform_apply(location=True)               # apex at the origin
    ob.location = apex
    ob.rotation_euler = (0, math.radians(axis_tilt_deg) * side, 0)
    ob.data.materials.append(mat)
    for p in ob.data.polygons:
        p.use_smooth = True
    styles.tag(ob, "emitter")
    return ob


def cones(sc, rnd):
    C.set_world(top=(0, 0, 0), horizon=(0, 0, 0), bottom=(0, 0, 0))
    k = 3.0                                     # angles exaggerated x3 for readability (labelled 示意)
    L = 6.0
    mi, mr = _cone_mat("IncCone", 0.32), _cone_mat("RefCone", 0.32)
    inc = _cone("Incident", (0, 0, 0), 6 * k, 7.9 * k, L, mi, -1)          # NA 0.55 / 4 at the mask ≈ 7.9°
    ref = _cone("Reflected", (0, 0, 0), 6 * k, 7.9 * k, L, mr, 1)
    # B7_09 (1-96): overlap clash. B7_11 (101-244): scan-direction NA halves (cone X-scale) and tilt 6->5.4.
    for ob, side in ((inc, -1), (ref, 1)):
        _key(ob, 1, scale=(1, 1, 1), rotation_euler=(0, math.radians(6 * k) * side, 0))
        _key(ob, 120, scale=(1, 1, 1), rotation_euler=(0, math.radians(6 * k) * side, 0))
        _key(ob, 210, scale=(3.9 / 7.9, 1, 1), rotation_euler=(0, math.radians(5.4 * k) * side, 0))
    # interference ripples where the cones overlap (a thin wavy sheet on the normal)
    rip = bpy.data.materials.new("Ripples")
    rip.use_nodes = True
    nt = rip.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    wave = nt.nodes.new("ShaderNodeTexWave")
    wave.wave_type = "RINGS"
    wave.inputs["Scale"].default_value = 6.0
    wave.inputs["Distortion"].default_value = 2.0
    ph = wave.inputs["Phase Offset"]
    ph.default_value = 0.0
    ph.keyframe_insert("default_value", frame=1)
    ph.default_value = 30.0
    ph.keyframe_insert("default_value", frame=240)
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.72
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (0.95, 0.92, 1.0, 1)
    st = em.inputs["Strength"]
    for f, v in ((1, 3.0), (130, 3.0), (175, 0.0)):
        st.default_value = v
        st.keyframe_insert("default_value", frame=f)
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(wave.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], mix.inputs["Fac"])
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(em.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])
    rip.surface_render_method = "BLENDED"
    w = L * math.tan(math.radians(7.9 * k - 6 * k))              # the overlap wedge in the plane of incidence
    me = bpy.data.meshes.new("OverlapWedge")
    me.from_pydata([(0, 0, 0), (-w, 0, L), (w, 0, L)], [], [(0, 1, 2)])
    sheet = bpy.data.objects.new("OverlapSheet", me)
    sc.collection.objects.link(sheet)
    sheet.data.materials.append(rip)
    styles.tag(sheet, "emitter")
    _key(sheet, 1, hide_render=False)
    _key(sheet, 176, hide_render=True)                            # unlit ripples would read as black marks
    # mask plane (dark, faint edge) and one photon sliding along the reflected cone's inner edge (B7_12)
    _box("MaskPlane", (0, 0, -0.06), (14, 8, 0.1), M.principled("MaskDark", (0.02, 0.02, 0.025)))
    ph_m = M.emission("Photon", (0.85, 0.75, 1.0), 10.0)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.03, location=(0, 0, 0))
    phot = bpy.context.object
    phot.data.materials.append(ph_m)
    styles.tag(phot, "emitter")
    th = math.radians((5.4 - 3.9) * k)
    _key(phot, 1, hide_render=True)
    _key(phot, 256, hide_render=False)
    for f, d in ((262, 5.0), (318, 1.2)):
        _key(phot, f, location=(d * math.sin(th) * 1.02, 0, d * math.cos(th)))
    B._camera("CamB7_09", [(1, (0, 0, 2.6), (-7.0, -15.0, 3.0), 50, 11.0), (96, (0, 0, 2.6), (3.0, -16.0, 3.4), 50, 11.0)])
    B._camera("CamB7_11", [(101, (0, 0, 2.6), (3.0, -16.0, 3.4), 50, 11.0), (244, (0, 0, 2.6), (0.0, -16.5, 2.6), 50, 11.0)])
    B._camera("CamB7_12", [(250, (0, 0, 3.0), (0.0, -6.0, 3.0), 85, 1.4), (333, (0, 0, 3.0), (0.0, -3.4, 3.0), 85, 1.4)])


# ---- B7_14 / B7_15 -------------------------------------------------------------------------
def _holed_cap(name, r_out, r_in, curv_r, segs=128, rings=40):
    bm = bmesh.new()
    grid = []
    for i in range(rings + 1):
        r = r_in + (r_out - r_in) * i / rings
        z = r * r / (2 * curv_r)
        grid.append([bm.verts.new((r * math.cos(2 * math.pi * j / segs), r * math.sin(2 * math.pi * j / segs), z))
                     for j in range(segs)])
    for i in range(rings):
        for j in range(segs):
            k = (j + 1) % segs
            bm.faces.new((grid[i][j], grid[i + 1][j], grid[i + 1][k], grid[i][k]))
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    for p in ob.data.polygons:
        p.use_smooth = True
    sol = ob.modifiers.new("Solid", "SOLIDIFY")
    sol.thickness = 0.35
    bev = ob.modifiers.new("Bevel", "BEVEL")
    bev.width = 0.03
    bev.segments = 3
    return ob


def holed(sc, rnd):
    C.set_world(top=(0.006, 0.007, 0.011), horizon=(0.003, 0.003, 0.005), bottom=(0.0, 0.0, 0.001))
    mat = M.multilayer_mirror("HoledMirror", r_max=3.0)
    m1 = _holed_cap("HoledMirror1", 3.0, 0.45, 14.0)
    m1.data.materials.append(mat)
    styles.tag(m1, "structure")
    m1.rotation_euler = (math.pi / 2, 0, 0)                     # optical axis along +Y
    m2 = _holed_cap("HoledMirror2", 2.2, 0.35, 10.0)
    m2.data.materials.append(mat)
    styles.tag(m2, "structure")
    m2.location = (0, 7.0, 0)
    m2.rotation_euler = (math.pi / 2, 0, 0)                     # also concave toward -Y: light runs -Y
    # converging light: rays from the mirror rims through the hole to the wafer point (B7_15)
    ray = M.emission("ConvRay", VIOLET, 0.0)
    focus = Vector((0, -6.0, 0))
    for k in range(64):
        th = 2 * math.pi * k / 64
        start = Vector((2.4 * math.cos(th), 6.6, 2.4 * math.sin(th)))
        via = Vector((0.3 * math.cos(th), 0.0, 0.3 * math.sin(th)))
        r = _curve(f"Conv{k}", [tuple(start), tuple(via), tuple(focus)], ray, radius=0.008, role="emitter")
        _key(r, 1, hide_render=True)                             # unlit emitters would read as black rods
        _key(r, 229, hide_render=False)
    M.set_emission_strength(ray, 230, 0.0)
    M.set_emission_strength(ray, 250, 5.0)
    dot = M.emission("WaferPoint", (0.9, 0.85, 1.0), 0.0)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.06, location=tuple(focus))
    d = bpy.context.object
    d.data.materials.append(dot)
    styles.tag(d, "emitter")
    M.set_emission_strength(dot, 245, 0.0)
    M.set_emission_strength(dot, 262, 60.0)
    for name, loc, size, st in (("BoxA", (-7, -11, 6), 8, 2.5), ("BoxB", (9, -9, -3), 6, 1.6), ("BoxC", (0, -12, -7), 10, 0.8),
                                ("BoxD", (3, -16, 2), 6, 1.2)):
        bpy.ops.mesh.primitive_plane_add(size=size, location=loc)
        bx = bpy.context.object
        bx.name = name
        bx.rotation_euler = (-Vector(loc)).to_track_quat("Z", "Y").to_euler()
        bx.data.materials.append(M.soft_emitter(name + "Mat", (0.86, 0.9, 1.0), st))
        bx.visible_camera = False                                 # only seen in the mirror
        styles.tag(bx, "rig")
    B._area("Rim", (6, -4, 5), (0.9, 0, 0.9), 4, 600, (0.85, 0.9, 1.0))
    B._area("Rim2", (-6, 3, -3), (2.0, 0, -2.2), 3, 200, (0.6, 0.7, 1.0))
    soft = bpy.data.lights.new("HoleKicker", "POINT")
    soft.energy = 60
    so = bpy.data.objects.new("HoleKicker", soft)
    sc.collection.objects.link(so)
    so.location = (0.0, 1.0, 0.9)
    B._camera("CamB7_14", [(1, (0, 0, 0), (-7.5, -6.0, 2.0), 35, 5.6), (171, (0, 0, 0), (0.0, -9.5, 0.0), 35, 5.6)])
    # B7_15: slow, then a rush through the hole, out the far side, a quick 180° look back
    B._camera("CamB7_15", [(181, (0, 2, 0), (0.0, -9.0, 0.0), 35, 8.0),
                           (226, (0, 6, 0), (0.0, -1.2, 0.0), 30, 8.0),
                           (240, (0, 9, 0), (0.0, 3.5, 0.0), 30, 8.0),
                           (251, (5, 4.5, 0), (0.0, 4.0, 0.0), 30, 8.0),
                           (262, (0, -6, 0), (0.0, 4.5, 0.0), 30, 8.0),
                           (300, (0, -6, 0), (0.0, 10.0, 0.0), 30, 8.0),
                           (324, (0, -6, 0), (0.1, 11.0, 0.2), 30, 8.0)])


def build(variant="po", seed=71):
    sc = C.reset_scene(FRAMES)
    C.set_world(top=(0.03, 0.035, 0.05), horizon=(0.012, 0.014, 0.02), bottom=(0.003, 0.004, 0.006))
    C.set_color_management(exposure=0.4)
    rnd = random.Random(seed)
    {"po": po, "crate": crate, "turntable": turntable, "cones": cones, "holed": holed}[variant](sc, rnd)
    return sc
