"""B7 — projection optics and High-NA (F7, F11–F13, F18, F20, F39, F40). Variants:

  po        B7_01  xray: the High-NA projection optics as in the published design example — M1-M4 in a narrow
                   column, the beam through the hole of the big last mirror M6 to M5 just above the wafer, back up
                   to M6, and a wide cone down through M5's hole to the wafer; each mirror lights as the beam arrives
  crate     B7_05  night apron: a white chamfered-roof ASML-type shipment box on a flatbed trailer rolls past;
                   a freighter with its nose raised and a scissor highloader behind (Intel's footage)
  turntable B7_06  clay: the High-NA projection-optics module as ZEISS shows it — a wide, low, angular frame
  cones     B7_09  energy: incident and reflected cones under the face-down mask overlap and clash (4x/4x, 6 deg)
            B7_11  the cones halve in the scan direction (8x) and tilt 6 -> 5.4 deg; a dark gap opens
            B7_12  close on the gap, a photon sliding along the reflected cone's inner edge
  holed     B7_14  photoreal: the holed last mirror M6 (large, high, facing down) and M5 (small, just above the
                   wafer, facing up)
            B7_15  fly down the narrow beam through M6's hole; the wide cone from M6 converges through M5's hole
                   onto the wafer point; look back up through both rings

Sources (research/visual/B6B7_sources.md, high_na_optics.md):
- PO layout: ASML/ZEISS "design examples" [van Schoot, EUVL Workshop 2021 s.35; Heil et al., EUVL Symposium 2015
  s.9/19/20], encoded in build_machine (BM.PO_MIRRORS, PO_FOCUS, M5_R, M6_R; source side +x). Mirror widths from the
  drawing: M1 0.094, M2 0.10, M3 0.177, M4 0.08, M5 0.155, M6 0.386 of the reticle-wafer height.
  "Extreme aspheres": faces drawn curved. Whether M5 is concave or convex is not public (drawn gently concave).
- Central obscuration ~20 % of the pupil [Davydova (ASML), SPIE 11517 p.6]; hole sizes are not public.
- NA 0.55 -> cone half-angle at the wafer asin(0.55) = 33.4 deg [ASML]; the design-example drawing itself shows ~29.
- Cones at the mask: half-angle asin(NA/mag): 4x/4x 7.9 deg vs CRAO 6 deg -> overlap; 8x in the scan direction
  3.94 deg with CRAO 5.4 deg -> separate [ZEISS, Kaumanns 2024 s.9]. Mask face down, light from below (as in the
  machine and in B7_07/08).
- Shipment: Intel newsroom 18 Apr 2024 + Intel videos (research/visual/shipment_suppliers.md A2/A3): white
  aluminium-framed shipment boxes with chamfered roof edges, flatbed trailers, 747 freighters nose-loaded from a
  scissor highloader. No logos or liveries; models shared with A0 (a0_scenes).
- PO module: ZEISS EUVL Workshop 2024 s.8 render and ASML/ZEISS 2022 s.39 photo (wide, low, angular frame,
  cabling on top, slanted lower panels, a narrower base block); ~12 t, > 40,000 parts. Absolute size not public.
"""
import math
import random

import bmesh
import bpy
from mathutils import Matrix, Vector

import build_machine as BM
import common as C
import materials as M
import sample_b1 as B
import styles

FRAMES = 340
EUV = (0.42, 0.16, 1.0)              # saturated EUV violet (a pastel violet emitter clips to white)
H_PO = BM.H_PO


def _key(ob, f, **kw):
    for k, v in kw.items():
        setattr(ob, k, v)
        ob.keyframe_insert(k, frame=f)


def _box(name, loc, size, mat, role="structure", bevel=0.0):
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


def _mesh(name, verts, faces, mat, role="structure", smooth=True):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], faces)
    me.update()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    if smooth:
        for p in ob.data.polygons:
            p.use_smooth = True
    ob.data.materials.append(mat)
    styles.tag(ob, role)
    return ob


def _holed_cap(name, r_out, r_in, curv_r, thick, segs=128, rings=24):
    """Mirror blank with a spherical-ish face z = r^2 / (2 curv_r) (concave toward +Z for curv_r > 0) and a central
    hole of radius r_in (r_in = 0: a full cap). Face up along local +Z; the substrate is solidified below."""
    bm = bmesh.new()
    grid = []
    r0 = max(r_in, 1e-4)
    for i in range(rings + 1):
        r = r0 + (r_out - r0) * i / rings
        z = r * r / (2 * curv_r)
        grid.append([bm.verts.new((r * math.cos(2 * math.pi * j / segs), r * math.sin(2 * math.pi * j / segs), z))
                     for j in range(segs)])
    for i in range(rings):
        for j in range(segs):
            k = (j + 1) % segs
            bm.faces.new((grid[i][j], grid[i + 1][j], grid[i + 1][k], grid[i][k]))
    if r_in <= 0:
        c = bm.verts.new((0, 0, 0))
        for j in range(segs):
            bm.faces.new((c, grid[0][j], grid[0][(j + 1) % segs]))
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    for p in ob.data.polygons:
        p.use_smooth = True
    sol = ob.modifiers.new("Solid", "SOLIDIFY")
    sol.thickness = thick
    sol.offset = -1.0                                            # substrate behind the face
    sol.use_even_offset = True
    bev = ob.modifiers.new("Bevel", "BEVEL")
    bev.width = min(thick * 0.15, 0.03)
    bev.segments = 2
    bev.limit_method = "ANGLE"
    return ob


def _orient(ob, loc, normal):
    ob.location = loc
    ob.rotation_euler = Vector(normal).normalized().to_track_quat("Z", "Y").to_euler()


def _beam_mat(name, front_keys, strength=0.35, tint=(0.58, 0.42, 1.0), reverse=False):
    """Translucent violet light volume for the light studio (ASML draws its design examples the same way: violet
    see-through bundles on white). The bundle grows along its local +Z from 0 to its length: front_keys are
    (frame, local z) keys of the growing front (reverse=True: visible above the front, so it grows toward z = 0)."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    L = nt.links
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    tr.inputs["Color"].default_value = (*tint, 1)
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*EUV, 1)
    lw = nt.nodes.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.4
    st = nt.nodes.new("ShaderNodeMath")
    st.operation = "MULTIPLY_ADD"
    st.inputs[1].default_value = strength
    st.inputs[2].default_value = strength * 0.35
    L.new(lw.outputs["Fresnel"], st.inputs[0])
    L.new(st.outputs[0], em.inputs["Strength"])
    add = nt.nodes.new("ShaderNodeAddShader")
    L.new(tr.outputs[0], add.inputs[0])
    L.new(em.outputs[0], add.inputs[1])
    # growth mask: object-space z below the front is visible
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    L.new(tc.outputs["Object"], sep.inputs["Vector"])
    front = nt.nodes.new("ShaderNodeValue")
    front.name = "Front"
    for f, v in front_keys:
        front.outputs[0].default_value = v
        front.outputs[0].keyframe_insert("default_value", frame=f)
    lt = nt.nodes.new("ShaderNodeMath")
    lt.operation = "GREATER_THAN" if reverse else "LESS_THAN"
    L.new(sep.outputs["Z"], lt.inputs[0])
    L.new(front.outputs[0], lt.inputs[1])
    clear = nt.nodes.new("ShaderNodeBsdfTransparent")
    mix = nt.nodes.new("ShaderNodeMixShader")
    L.new(lt.outputs[0], mix.inputs["Fac"])
    L.new(clear.outputs[0], mix.inputs[1])
    L.new(add.outputs[0], mix.inputs[2])
    L.new(mix.outputs[0], out.inputs["Surface"])
    m.surface_render_method = "BLENDED"
    m.use_backface_culling = False
    return m


def _bundle(name, a, ra, b, rb, mat, segs=48, axis_hint=None):
    """A light bundle from a disc (centre a, radius ra) to a disc (centre b, radius rb), discs perpendicular to the
    leg, as a lofted side surface; local +Z runs from a (z = 0) to b (z = |b - a|) so the growth mask works."""
    a, b = Vector(a), Vector(b)
    d = b - a
    ln = d.length
    q = d.normalized().to_track_quat("Z", "Y")
    verts, faces = [], []
    for z, r in ((0.0, ra), (ln, rb)):
        for j in range(segs):
            t = 2 * math.pi * j / segs
            verts.append((r * math.cos(t), r * math.sin(t), z))
    for j in range(segs):
        k = (j + 1) % segs
        faces.append((j, k, segs + k, segs + j))
    ob = _mesh(name, verts, faces, mat, role="emitter")
    ob.location = a
    ob.rotation_euler = q.to_euler()
    return ob


def _bundle_to_ring(name, apex, centre, normal, r, mat, segs=64):
    """An oblique cone from an apex point to a circle (centre, normal, radius r); local +Z points from the apex
    toward the circle's centre, so the growth mask runs from the apex."""
    apex, centre = Vector(apex), Vector(centre)
    axis = centre - apex
    q = axis.normalized().to_track_quat("Z", "Y")
    inv = q.inverted()
    n = Vector(normal).normalized()
    u = n.orthogonal().normalized()
    v = n.cross(u)
    verts = [(0.0, 0.0, 0.0)]
    for j in range(segs):
        t = 2 * math.pi * j / segs
        p = centre + r * (math.cos(t) * u + math.sin(t) * v) - apex
        verts.append(tuple(inv @ p))
    faces = [(0, 1 + j, 1 + (j + 1) % segs) for j in range(segs)]
    ob = _mesh(name, verts, faces, mat, role="emitter")
    ob.location = apex
    ob.rotation_euler = q.to_euler()
    return ob


def _ring_to_ring(name, c0, n0, r0, c1, n1, r1, mat, segs=64):
    """Frustum between two (possibly tilted) circles; local +Z along c0 -> c1."""
    c0, c1 = Vector(c0), Vector(c1)
    axis = c1 - c0
    q = axis.normalized().to_track_quat("Z", "Y")
    inv = q.inverted()
    verts = []
    for c, n, r in ((c0, n0, r0), (c1, n1, r1)):
        n = Vector(n).normalized()
        u = Vector((1, 0, 0)) if abs(n.x) < 0.9 else Vector((0, 1, 0))
        u = (u - n * u.dot(n)).normalized()
        v = n.cross(u)
        for j in range(segs):
            t = 2 * math.pi * j / segs
            verts.append(tuple(inv @ (c + r * (math.cos(t) * u + math.sin(t) * v) - c0)))
    faces = [(j, (j + 1) % segs, segs + (j + 1) % segs, segs + j) for j in range(segs)]
    ob = _mesh(name, verts, faces, mat, role="emitter")
    ob.location = c0
    ob.rotation_euler = q.to_euler()
    return ob


# ---- B7_01 ---------------------------------------------------------------------------------
# radii from the design-example drawing widths (fractions of the reticle-wafer height, halved)
PO_R = [0.094 * H_PO / 2, 0.10 * H_PO / 2, 0.177 * H_PO / 2, 0.08 * H_PO / 2, BM.M5_R, BM.M6_R]
M5_HOLE = 0.11                       # passes the M6 -> wafer cone at M5's height (0.092) with margin; not public
M6_HOLE = 0.21                       # passes the narrow beam from PO_FOCUS (x 0.11..0.18 at M6) ; not public


def po(sc, rnd):
    """The projection optics alone, in BM coordinates (reticle z 3.45, wafer z -1.05)."""
    C.set_world(top=(0.9, 0.91, 0.93), horizon=(0.78, 0.79, 0.82), bottom=(0.6, 0.61, 0.64))
    # grey mirror blanks as the design examples draw them (a polished mirror would only show the white studio)
    mirror = M.principled("POMirror", (0.62, 0.63, 0.66), metallic=1.0, roughness=0.22)
    sub = M.principled("POSubstrate", (0.36, 0.37, 0.4), metallic=0.3, roughness=0.4)

    def blank(ob):
        ob.data.materials.append(mirror)
        ob.data.materials.append(sub)
        ob.modifiers["Solid"].material_offset = 1
        ob.modifiers["Solid"].material_offset_rim = 1
        styles.tag(ob, "structure")
    ret, wafer = Vector(BM.RETICLE), Vector(BM.WAFER)
    pm = [Vector(p) for p in BM.PO_MIRRORS]
    focus = Vector(BM.PO_FOCUS)
    seq = [ret] + pm[:4] + [focus]
    normals = []
    for i in range(4):                                            # M1-M4: curved blanks at the bounce points
        a = (seq[i] - seq[i + 1]).normalized()
        b = (seq[i + 2] - seq[i + 1]).normalized()
        n = (a + b).normalized()
        normals.append(n)
        cap = _holed_cap(f"M{i + 1}", PO_R[i], 0.0, PO_R[i] * 6.0, PO_R[i] * 0.35)
        blank(cap)
        _orient(cap, seq[i + 1], n)
    m5 = _holed_cap("M5", PO_R[4], M5_HOLE, 6.0, 0.07)            # faces up, holed, just above the wafer
    blank(m5)
    _orient(m5, pm[4], (0, 0, 1))
    m6 = _holed_cap("M6", PO_R[5], M6_HOLE, 4.0, 0.16)            # big last mirror: faces down, holed
    blank(m6)
    _orient(m6, pm[5], (0, 0, -1))
    # reticle (dark plate, face down) and wafer
    _box("Reticle", tuple(ret + Vector((0, 0, 0.04))), (0.86, 0.68, 0.06),
         M.principled("ReticlePlate", (0.08, 0.085, 0.09), metallic=0.6, roughness=0.15), bevel=0.005)
    _cyl("Wafer", 0.45, 0.02, tuple(wafer - Vector((0, 0, 0.01))),
         M.principled("WaferSi", (0.30, 0.31, 0.36), metallic=0.7, roughness=0.12))
    # ghost housing around the mirrors (shape 示意)
    _box("POHousing", (0.05, 0, 1.0), (2.6, 2.1, 4.1), M.principled("POPanel", (0.78, 0.8, 0.82), metallic=0.2,
                                                                  roughness=0.45), role="shell", bevel=0.25)
    # light: violet see-through bundles, growing leg by leg (the design example's way of drawing it)
    legs = [("L0", ret, 0.03, pm[0], PO_R[0] * 0.85), ("L1", pm[0], PO_R[0] * 0.85, pm[1], PO_R[1] * 0.85),
            ("L2", pm[1], PO_R[1] * 0.85, pm[2], PO_R[2] * 0.85), ("L3", pm[2], PO_R[2] * 0.85, pm[3], PO_R[3] * 0.85),
            ("L4", pm[3], PO_R[3] * 0.85, focus, 0.012)]
    f = 2
    span = [16, 16, 16, 14, 12]
    lit = []
    for (nm, a, ra, b, rb), n in zip(legs, span):
        ln = (Vector(b) - Vector(a)).length
        mat = _beam_mat("Beam" + nm, [(1, -0.01), (f, -0.01), (f + n, ln + 0.01)])
        _bundle("Beam" + nm, a, ra, b, rb, mat)
        f += n
        lit.append(f)
    # focus -> M5 annulus (through M6's hole), M5 -> M6, M6 -> wafer through M5's hole (hollow centre)
    r5 = PO_R[4] * 0.92
    ln = (pm[4] - focus).length
    _bundle_to_ring("BeamL5", focus, pm[4] + Vector((0, 0, 0.004)), (0, 0, 1), r5,
                    _beam_mat("BeamL5", [(1, -0.01), (f, -0.01), (f + 12, ln + 0.05)]))
    f += 12
    lit.append(f)
    ln = (pm[5] - pm[4]).length
    _ring_to_ring("BeamL6", pm[4], (0, 0, 1), r5, pm[5], (0, 0, 1), PO_R[5] * 0.95,
                  _beam_mat("BeamL6", [(1, -0.01), (f, -0.01), (f + 12, ln + 0.05)], strength=0.25))
    f += 12
    lit.append(f)
    ln = (wafer - pm[5]).length
    for nm, r in (("BeamL7", PO_R[5] * 0.95), ("BeamL7in", M6_HOLE * 1.02)):
        _bundle_to_ring(nm, wafer, pm[5], (0, 0, 1), r,
                        _beam_mat(nm, [(1, ln + 0.05), (f, ln + 0.05), (f + 16, -0.01)], strength=0.3, reverse=True))
    f += 16
    lit.append(f)
    # each mirror lights up as the beam arrives: a violet rim ring, hidden until then (no dark ring before)
    centres = pm[:4] + [pm[4], pm[5]]
    nrm = normals + [Vector((0, 0, 1)), Vector((0, 0, -1))]
    for i, (c, n) in enumerate(zip(centres, nrm)):
        rm = M.emission(f"Ring{i + 1}", EUV, 0.0)
        bpy.ops.mesh.primitive_torus_add(major_radius=PO_R[i] * 1.02, minor_radius=0.012 + 0.006 * (i >= 4))
        t = bpy.context.object
        t.name = f"Ring{i + 1}"
        _orient(t, c, n)
        t.data.materials.append(rm)
        styles.tag(t, "emitter")
        f_hit = lit[i] if i < 4 else lit[i + 1]
        _key(t, 1, hide_render=True)
        _key(t, f_hit, hide_render=False)
        M.set_emission_strength(rm, f_hit, 3.0)
        M.set_emission_strength(rm, f_hit + 14, 0.8)
    dot = M.emission("WaferPoint", EUV, 0.0)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.025, location=tuple(wafer + Vector((0, 0, 0.012))))
    d = bpy.context.object
    d.data.materials.append(dot)
    styles.tag(d, "emitter")
    _key(d, 1, hide_render=True)
    _key(d, lit[-1], hide_render=False)
    M.set_emission_strength(dot, lit[-1], 4.0)
    # follow the light down, then rise to a 3/4 view of the whole optics
    B._camera("CamB7_01", [(1, (0.15, 0, 2.7), (2.2, -4.6, 3.6), 35, 8.0),
                           (50, (0.0, 0, 1.6), (2.6, -5.6, 2.4), 35, 8.0),
                           (100, (0.05, 0, 0.0), (2.8, -6.0, 0.9), 35, 8.0),
                           (157, (0.0, 0, 1.2), (3.9, -8.3, 3.3), 35, 8.0)])


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
    import a0_scenes as A
    sc["hdri_world"] = True
    C.hdri_world("rogland_moonlit_night", strength=0.06, rotation=math.radians(40), tint=(0.7, 0.82, 1.1))
    wet = M.pbr("Apron", "asphalt_02", scale=0.12, tint=(0.08, 0.085, 0.1), rough_mul=0.2, rough_add=0.01,
                normal=0.6, fallback=(0.02, 0.022, 0.026))                       # wet apron (CC0)
    _box("Apron", (0, 0, -0.05), (300, 300, 0.1), wet)
    mats = A.shipping_mats()
    cab = M.principled("TruckCab", (0.8, 0.8, 0.82), roughness=0.3, coat=0.4)
    tyre = M.principled("TruckTyre", (0.02, 0.02, 0.02), roughness=0.7)
    truck = A._flatbed_truck("Truck", mats, cab, tyre, box_size=(2.6, 9.0, 3.0))
    box = bpy.data.objects["TruckBox"]
    glass = M.principled("CabGlass", (0.01, 0.012, 0.016), roughness=0.05, coat=1.0)
    for nm, loc, size in (("Windscreen", (7.52, 0, 2.3), (0.04, 2.1, 0.8)), ("SideWin", (6.75, -1.235, 2.3), (0.9, 0.04, 0.7)),
                          ("Grille", (7.52, 0, 1.25), (0.04, 1.4, 0.5))):
        w = _box(nm, loc, size, glass)
        w.parent = truck
    ink = M.principled("Stencil", (0.04, 0.07, 0.2), roughness=0.6)            # navy box ID stencil, date only
    t = _text("2023.12", (0, 0, 0), (math.pi / 2, 0, -math.pi / 2), 0.42, ink)
    t.parent = box
    t.location = (-1.33, 0.0, 1.9)                                             # on the side facing the camera
    _key(truck, 1, location=(-7.5, 0, 0))
    _key(truck, 92, location=(-1.2, 0, 0))
    for fc in C.fcurves(truck.animation_data.action):
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR"
    # behind: a generic freighter with its nose raised, lit hold, and the scissor highloader at the sill
    skin = M.principled("Paint", (0.78, 0.8, 0.82), roughness=0.28, coat=0.4)
    belly = M.principled("BellyPaint", (0.42, 0.45, 0.5), roughness=0.35, coat=0.3)
    plane = A._group(lambda: A.freighter(skin, belly, rnd))
    hinge = bpy.data.objects["NoseHinge"]
    hinge.rotation_euler = (0, math.radians(-58), 0)
    plane.rotation_euler = (0, 0, math.radians(-115))                         # nose toward the camera side
    plane.location = (-26.0, 52.0, 0)
    lamp = M.emission("HoldLamp", (0.86, 0.92, 1.0), 12.0)
    hold = []
    for k in range(5):
        hold.append(_box(f"HoldLamp{k}", (-1.5 - 5.0 * k, 0, 7.3), (3.0, 0.3, 0.05), lamp, role="emitter"))
    hold.append(_box("HoldFloor", (-12.0, 0, 1.65), (26.0, 5.6, 0.12), M.dark_anodized("HoldFloor")))
    for k in range(2):
        e = A._enclosure(f"HoldBox{k}", (2.6, 6.4, 3.0), mats)
        e.rotation_euler = (0, 0, math.pi / 2)
        e.location = (-5.5 - 7.2 * k, 0, 1.71)
        hold.append(e)
    for ob in hold:
        ob.parent = plane
    lift = M.principled("Highloader", (0.85, 0.7, 0.1), metallic=0.3, roughness=0.5)

    def loader():
        _box("LoaderDeck", (0, 0, 1.55), (7.0, 3.4, 0.25), mats["pallet"])
        for sgn in (-1, 1):
            for k in range(3):
                arm = _box(f"LoaderArm{sgn}{k}", (0, sgn * 1.5, 0.75), (5.2, 0.12, 0.14), lift)
                arm.rotation_euler = (0, math.radians(17 if k % 2 else -17), 0)
        _box("LoaderBase", (0, 0, 0.25), (7.4, 3.0, 0.5), lift)
    rig = A._group(loader)
    rig.parent = plane
    rig.location = (6.6, 0, 0)
    # light masts, apron haze
    bulb = M.emission("MastBulb", (1.0, 0.86, 0.62), 40.0)
    mast = M.principled("Mast", (0.05, 0.05, 0.06), roughness=0.6)
    for x, y in ((24, 30), (-40, 48), (6, -40)):
        _cyl(f"Mast{x}", 0.3, 26, (x, y, 13), mast, verts=12)
        _box(f"MastHead{x}", (x, y, 26.5), (2.4, 0.8, 0.8), bulb, role="emitter")
        bpy.ops.object.light_add(type="SPOT", location=(x, y, 26))
        l = bpy.context.object
        l.data.energy = 90000
        l.data.spot_size = math.radians(60)
        l.data.spot_blend = 0.6
        l.data.color = (1.0, 0.88, 0.7)
        l.rotation_euler = (Vector((0, 0, 0)) - Vector((x, y, 26))).to_track_quat("-Z", "Y").to_euler()
        styles.tag(l, "rig")
    B._area("BoxKey", (6, -10, 9), (0.95, 0, 0.55), 6, 1800, (0.82, 0.9, 1.0))
    B._area("BoxRim", (-8, 8, 6), (1.2, 0, 2.6), 6, 1200, (0.6, 0.72, 1.0))
    fog = bpy.data.materials.new("ApronHaze")
    fog.use_nodes = True
    nt = fog.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    vs = nt.nodes.new("ShaderNodeVolumePrincipled")
    vs.inputs["Density"].default_value = 0.002
    vs.inputs["Color"].default_value = (0.8, 0.85, 0.95, 1)
    nt.links.new(vs.outputs[0], out.inputs["Volume"])
    _box("Haze", (0, 10, 15), (160, 160, 30), fog, role="env")
    B._camera("CamB7_05", [(1, (-3.5, 4.0, 2.6), (13.0, -21.0, 1.4), 40, 4.0),
                           (92, (-1.5, 4.0, 2.6), (12.0, -19.5, 1.5), 40, 4.0)])


# ---- B7_06 ---------------------------------------------------------------------------------
def _prism(name, bottom, top, z0, z1, mat, bevel=0.03):
    """A slanted-sided block: bottom and top are (sx, sy, chamfer) rectangles with chamfered corners."""
    def outline(sx, sy, ch, z):
        hx, hy = sx / 2, sy / 2
        return [(hx - ch, -hy, z), (hx, -hy + ch, z), (hx, hy - ch, z), (hx - ch, hy, z),
                (-hx + ch, hy, z), (-hx, hy - ch, z), (-hx, -hy + ch, z), (-hx + ch, -hy, z)]
    v = outline(*bottom, z0) + outline(*top, z1)
    f = [tuple(range(7, -1, -1)), tuple(range(8, 16))]
    for j in range(8):
        k = (j + 1) % 8
        f.append((j, k, 8 + k, 8 + j))
    ob = _mesh(name, v, f, mat, smooth=False)
    if bevel:
        bv = ob.modifiers.new("Bevel", "BEVEL")
        bv.width, bv.segments = bevel, 2
    return ob


def turntable(sc, rnd):
    """Clay model of the High-NA projection-optics module after ZEISS's render (EUVL Workshop 2024 s.8) and the
    frame-integration photo (ASML/ZEISS 2022 s.39): a wide, low, angular frame block, a slanted lower section, a
    narrower base block, ribbed panels and cabling on top. Proportions read off those images; size not public."""
    clay = M.principled("ClayPO", (0.7, 0.7, 0.7))
    floor = _box("Floor", (0, 0, -0.05), (40, 40, 0.1), clay)
    floor["clay_floor"] = True
    bpy.ops.object.empty_add(location=(0, 0, 0))
    root = bpy.context.object
    root.name = "PORoot"
    parts = []
    W, D = 3.6, 2.3
    parts.append(_prism("Base", (1.7, 1.2, 0.15), (1.9, 1.35, 0.18), 0.35, 0.75, clay))
    parts.append(_prism("Lower", (2.5, 1.6, 0.3), (W, D, 0.45), 0.75, 1.55, clay))
    parts.append(_prism("Upper", (W, D, 0.45), (W, D, 0.45), 1.55, 2.35, clay))
    parts.append(_prism("TopDeck", (W - 0.1, D - 0.1, 0.42), (W - 0.5, D - 0.4, 0.3), 2.35, 2.5, clay))
    for k in range(3):                                            # stiffener ribs on the slanted front/back panels
        z = 0.95 + 0.22 * k
        u = (z - 0.75) / 0.8
        sx = 2.5 + (W - 2.5) * u
        sy = 1.6 + (D - 1.6) * u
        for s in (-1, 1):
            parts.append(_box(f"Rib{k}{s}", (0, s * (sy / 2 + 0.015), z), (sx * 0.8, 0.05, 0.05), clay))
    for k in range(4):                                            # vertical panel seams on the upper block
        x = -W / 2 + W * (k + 1) / 5
        for s in (-1, 1):
            parts.append(_box(f"Seam{k}{s}", (x, s * (D / 2 + 0.01), 1.95), (0.05, 0.03, 0.7), clay))
    for k, (x, y, sx, sy, h) in enumerate(((-1.0, 0.3, 0.7, 0.6, 0.35), (0.2, -0.4, 0.9, 0.5, 0.28),
                                          (1.1, 0.35, 0.6, 0.7, 0.42), (-0.2, 0.55, 0.5, 0.35, 0.22))):
        parts.append(_box(f"Actuator{k}", (x, y, 2.5 + h / 2), (sx, sy, h), clay, bevel=0.03))
    for k in range(5):                                            # cable bundles across the top deck
        y = -0.8 + 0.38 * k
        pts = [(-1.6, y, 2.52), (-0.8, y + 0.08, 2.62), (0.0, y - 0.05, 2.58), (0.9, y + 0.06, 2.66), (1.6, y, 2.52)]
        cu = bpy.data.curves.new(f"Cable{k}", "CURVE")
        cu.dimensions = "3D"
        cu.bevel_depth = 0.035
        spl = cu.splines.new("NURBS")
        spl.points.add(len(pts) - 1)
        for i, p in enumerate(pts):
            spl.points[i].co = (*p, 1)
        spl.use_endpoint_u = True
        ob = bpy.data.objects.new(f"Cable{k}", cu)
        sc.collection.objects.link(ob)
        ob.data.materials.append(clay)
        styles.tag(ob, "structure")
        parts.append(ob)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.16, depth=0.06, vertices=48, location=(-0.6, -D / 2 - 0.02, 2.0),
                                        rotation=(math.pi / 2, 0, 0))
    port = bpy.context.object                                      # the round port on the front face
    port.data.materials.append(clay)
    styles.tag(port, "structure")
    parts.append(port)
    for k, (x, y) in enumerate(((-1.3, -0.7), (1.3, -0.7), (0.0, 0.8))):   # three low support pedestals (示意)
        parts.append(_box(f"Pedestal{k}", (x * 0.55, y * 0.6, 0.175), (0.5, 0.5, 0.35), clay, bevel=0.03))
    for p in parts:
        p.parent = root
    _key(root, 1, rotation_euler=(0, 0, math.radians(-20)))
    _key(root, 144, rotation_euler=(0, 0, math.radians(30)))
    for fc in C.fcurves(root.animation_data.action):
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR"
    B._area("ClayKey", (5, -6, 8), (0.8, 0, 0.6), 8, 1800, (1.0, 0.98, 0.95))
    B._camera("CamB7_06", [(1, (0.0, 0, 1.35), (7.0, -7.6, 3.4), 50, 5.6), (144, (0.0, 0, 1.4), (7.8, -6.6, 3.6), 50, 5.6)])


# ---- B7_09 / B7_11 / B7_12 -----------------------------------------------------------------
K_EXAG = 3.0                         # angles exaggerated x3 for readability (labelled 示意)
HALF_44 = math.degrees(math.asin(0.55 / 4))      # 7.9 deg
HALF_48 = math.degrees(math.asin(0.55 / 8))      # 3.94 deg (scan direction, 8x)


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
    em.inputs["Color"].default_value = (*EUV, 1)
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


def _cone(name, half_deg, length, mat):
    """Cone with its apex at the origin (the mask point) opening downward (-Z): the mask faces down, the light
    comes from below. Tilt it with rotation_euler.y (+ toward -x)."""
    bpy.ops.mesh.primitive_cone_add(vertices=96, radius1=length * math.tan(math.radians(half_deg)), radius2=0.0,
                                    depth=length, end_fill_type="NOTHING", location=(0, 0, -length / 2))
    ob = bpy.context.object
    ob.name = name
    bpy.ops.object.transform_apply(location=True)               # apex at the origin
    ob.data.materials.append(mat)
    for p in ob.data.polygons:
        p.use_smooth = True
    styles.tag(ob, "emitter")
    return ob


def cones(sc, rnd):
    C.set_world(top=(0, 0, 0), horizon=(0, 0, 0), bottom=(0, 0, 0))
    k = K_EXAG
    L = 6.0
    inc = _cone("Incident", HALF_44 * k, L, _cone_mat("IncCone", 0.32))      # NA 0.55 / 4 at the mask = 7.9 deg
    ref = _cone("Reflected", HALF_44 * k, L, _cone_mat("RefCone", 0.32))
    s48 = math.tan(math.radians(HALF_48 * k)) / math.tan(math.radians(HALF_44 * k))   # scan-direction (X) squeeze
    # B7_09 (1-96): 4x/4x, 6 deg: overlap. B7_11 (101-227): 8x in the scan direction (cone X-scale), tilt 6 -> 5.4.
    for ob, side in ((inc, 1), (ref, -1)):                       # rotation y > 0 leans the cone toward -x
        _key(ob, 1, scale=(1, 1, 1), rotation_euler=(0, math.radians(6 * k) * side, 0))
        _key(ob, 112, scale=(1, 1, 1), rotation_euler=(0, math.radians(6 * k) * side, 0))
        _key(ob, 165, scale=(s48, 1, 1), rotation_euler=(0, math.radians(6 * k) * side, 0))
        _key(ob, 205, scale=(s48, 1, 1), rotation_euler=(0, math.radians(5.4 * k) * side, 0))
    # where the 4x/4x cones overlap: a rippling sheet (示意); it fades out (transparency, not emission) as the cones
    # slim, so an unlit sheet never shows as a dark shape
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
    sepc = nt.nodes.new("ShaderNodeSeparateColor")
    fade = nt.nodes.new("ShaderNodeMath")
    fade.operation = "MULTIPLY"
    fv = fade.inputs[1]
    for f, v in ((1, 1.0), (118, 1.0), (150, 0.0)):
        fv.default_value = v
        fv.keyframe_insert("default_value", frame=f)
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (0.8, 0.7, 1.0, 1)
    em.inputs["Strength"].default_value = 2.0
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(wave.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], sepc.inputs["Color"])
    nt.links.new(sepc.outputs["Red"], fade.inputs[0])
    nt.links.new(fade.outputs[0], mix.inputs["Fac"])
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(em.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])
    rip.surface_render_method = "BLENDED"
    w = L * math.tan(math.radians(HALF_44 * k - 6 * k))         # the overlap wedge in the plane of incidence
    me = bpy.data.meshes.new("OverlapWedge")
    me.from_pydata([(0, 0, 0), (-w, 0, -L), (w, 0, -L)], [], [(0, 1, 2)])
    sheet = bpy.data.objects.new("OverlapSheet", me)
    sc.collection.objects.link(sheet)
    sheet.data.materials.append(rip)
    styles.tag(sheet, "emitter")
    _key(sheet, 1, hide_render=False)
    _key(sheet, 152, hide_render=True)
    # the mask: a dark plane above, face down
    _box("MaskPlane", (0, 0, 0.06), (14, 8, 0.1), M.principled("MaskDark", (0.02, 0.02, 0.025)))
    # B7_12: one photon sliding along the reflected cone's inner edge (the edge next to the dark gap)
    ph_m = M.emission("Photon", EUV, 3.0)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.018, location=(0, 0, 0))
    phot = bpy.context.object
    phot.name = "Photon"
    phot.data.materials.append(ph_m)
    styles.tag(phot, "emitter")
    rot = Matrix.Rotation(-math.radians(5.4 * k), 3, "Y")       # reflected cone, final state
    edge = (rot @ Vector((-s48 * math.tan(math.radians(HALF_44 * k)), 0, -1))).normalized()
    _key(phot, 1, hide_render=True)
    _key(phot, 262, hide_render=False)
    for f, d in ((262, 4.6), (330, 1.6)):
        _key(phot, f, location=tuple(edge * d))
    focus = edge * 3.1
    B._camera("CamB7_09", [(1, (0, 0, -2.6), (-7.0, -15.0, -2.2), 50, 11.0), (96, (0, 0, -2.6), (3.0, -16.0, -1.8), 50, 11.0)])
    B._camera("CamB7_11", [(101, (0, 0, -2.6), (3.0, -16.0, -1.8), 50, 11.0), (227, (0, 0, -2.6), (0.0, -16.5, -2.6), 50, 11.0)])
    B._camera("CamB7_12", [(250, tuple(focus), (focus.x * 0.6, -6.0, focus.z + 0.2), 85, 2.0),
                           (333, tuple(focus), (focus.x * 0.8, -3.6, focus.z + 0.1), 85, 2.0)])


# ---- B7_14 / B7_15 -------------------------------------------------------------------------
# The last two mirrors as in Heil 2015 s.9 / van Schoot 2021 s.35, scaled so M6 has radius 3.0: M6 high and facing
# down, M5 small just above the wafer facing up (M5 radius 0.155/0.386 of M6; ~9x closer to the wafer than to M6).
# M6's height is set so the cone from its rim meets the wafer at asin(0.55) = 33.4 deg (NA 0.55); the hole radii
# give ~20 % obscuration of the pupil (sin 6.3 / sin 33.4) and let the cone pass M5. Hole sizes are not public.
R6, R5 = 3.0, 3.0 * 0.155 / 0.386
HALF_NA = math.asin(0.55)
Z6 = R6 / math.tan(HALF_NA)                          # M6 rim 4.55 above the wafer
CURV6 = 9.0
Z6V = Z6 + R6 * R6 / (2 * CURV6)                     # M6 vertex (its face curves down toward the rim)
Z5 = Z6 * 0.105
HOLE6 = Z6 * math.tan(math.asin(0.2 * 0.55))
HOLE5 = Z5 * math.tan(HALF_NA) * 1.15
Z_FOCUS = Z6V + 0.35                                  # intermediate image just above M6


def holed(sc, rnd):
    C.set_world(top=(0.006, 0.007, 0.011), horizon=(0.003, 0.003, 0.005), bottom=(0.0, 0.0, 0.001))
    mat = M.multilayer_mirror("HoledMirror")
    sub = M.principled("HoledSubstrate", (0.6, 0.61, 0.63), metallic=0.2, roughness=0.35)
    m6 = _holed_cap("M6", R6, HOLE6, CURV6, 0.5)
    m6.data.materials.append(mat)
    m6.data.materials.append(sub)
    m6.modifiers["Solid"].material_offset = 1
    m6.modifiers["Solid"].material_offset_rim = 1
    styles.tag(m6, "structure")
    _orient(m6, (0, 0, Z6V), (0, 0, -1))                        # concave toward the wafer
    m5 = _holed_cap("M5", R5, HOLE5, 6.0, 0.22)
    m5.data.materials.append(mat)
    m5.data.materials.append(sub)
    m5.modifiers["Solid"].material_offset = 1
    m5.modifiers["Solid"].material_offset_rim = 1
    styles.tag(m5, "structure")
    _orient(m5, (0, 0, Z5), (0, 0, 1))                          # faces up toward M6
    wafer = Vector((0, 0, 0))
    # light (B7_15): narrow beam from the focus above M6, through M6's hole, out to M5's annulus; M5 -> M6 annulus;
    # M6 -> wafer point through M5's hole. Thin violet rays, revealed in that order.
    ray = M.emission("ConvRay", EUV, 0.0)
    rays = []
    n = 40
    for j in range(n):
        th = 2 * math.pi * (j + 0.5) / n
        u = Vector((math.cos(th), math.sin(th), 0))
        for kk, fr in enumerate((0.35, 0.7, 0.97)):
            p5 = u * (HOLE5 + (R5 - HOLE5) * fr) + Vector((0, 0, Z5 + 0.02))
            r6 = HOLE6 + (R6 - HOLE6) * fr
            p6 = u * r6 + Vector((0, 0, Z6V - r6 * r6 / (2 * CURV6)))
            pts = [(0, 0, Z_FOCUS), tuple(p5), tuple(p6), tuple(wafer)]
            rays.append(_curve(f"Ray{j}_{kk}", pts, ray, radius=0.006, role="emitter"))
    for r in rays:
        r.data.bevel_factor_end = 0.0
        r.data.keyframe_insert("bevel_factor_end", frame=1)
        r.data.keyframe_insert("bevel_factor_end", frame=214)
        r.data.bevel_factor_end = 1.0
        r.data.keyframe_insert("bevel_factor_end", frame=262)
        _key(r, 1, hide_render=True)                           # no unlit (black) rays before the light arrives
        _key(r, 214, hide_render=False)
    M.set_emission_strength(ray, 214, 0.0)
    M.set_emission_strength(ray, 222, 0.9)
    beam_in = _cone_mat("NarrowIn", 0.6)                       # see-through glow, not an opaque violet solid                  # the narrow beam arriving at the focus from M4
    bpy.ops.mesh.primitive_cone_add(vertices=48, radius1=0.0, radius2=0.35, depth=3.0,
                                    location=(0, 0, Z_FOCUS + 1.5))
    cin = bpy.context.object
    cin.name = "NarrowCone"
    cin.data.materials.append(beam_in)
    styles.tag(cin, "emitter")
    _key(cin, 1, hide_render=True)                             # shown already lit (an unlit emitter reads black)
    _key(cin, 196, hide_render=False)
    dot = M.emission("WaferPoint", EUV, 0.0)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.04, location=tuple(wafer))
    d = bpy.context.object
    d.data.materials.append(dot)
    styles.tag(d, "emitter")
    _key(d, 1, hide_render=True)
    _key(d, 256, hide_render=False)
    M.set_emission_strength(dot, 256, 0.0)
    M.set_emission_strength(dot, 264, 6.0)
    # studio cards seen only in the mirrors (reflections), dim rim lights
    for name, loc, size, st in (("BoxA", (-9, -7, 1.5), 7, 1.6), ("BoxB", (8, -6, 6.5), 6, 1.2),
                                ("BoxC", (0, 9, -2.5), 9, 0.7), ("BoxD", (5, 5, 0.5), 5, 0.9)):
        bpy.ops.mesh.primitive_plane_add(size=size, location=loc)
        bx = bpy.context.object
        bx.name = name
        bx.rotation_euler = (Vector((0, 0, Z6 * 0.5)) - Vector(loc)).to_track_quat("Z", "Y").to_euler()
        bx.data.materials.append(M.soft_emitter(name + "Mat", (0.86, 0.9, 1.0), st))
        bx.visible_camera = False
        styles.tag(bx, "rig")
    B._area("Rim", (7, -5, 8), (0.7, 0, 0.9), 4, 500, (0.85, 0.9, 1.0))
    B._area("Rim2", (-6, 4, -2), (2.0, 0, -2.2), 3, 160, (0.6, 0.7, 1.0))
    # B7_14: from a low side view of the mirror pair, arc under M6 to look up its axis past M5 at the hole
    B._camera("CamB7_14", [(1, (0, 0, Z6 * 0.5), (-11.0, -9.0, 1.4), 40, 5.6),
                           (90, (0, 0, Z6 * 0.75), (-5.0, -6.5, -0.6), 40, 5.6),
                           (151, (0, 0.02, Z6), (0.25, -1.1, -3.4), 40, 5.6)])
    # B7_15 (181-324): ride down the narrow beam through M6's hole, swing out to see the cone converge through M5's
    # hole onto the wafer point, then look back up through both rings
    B._camera("CamB7_15", [(181, (0, 0.05, Z6), (0.0, -1.0, Z6 + 6.5), 30, 8.0),
                           (214, (0, 0.05, Z5), (0.0, -0.25, Z6 + 1.2), 30, 8.0),
                           (232, (0, 0.05, Z5), (0.0, -0.2, Z6 - 0.8), 24, 8.0),
                           (256, (0, 0, Z5 + 1.0), (2.6, -6.0, Z5 + 1.4), 24, 8.0),
                           (290, (0, 0, Z6 * 0.45), (4.4, -9.0, Z6 * 0.4), 24, 8.0),
                           (324, (0, 0.05, Z6), (0.3, -0.9, -3.6), 30, 8.0)])


def build(variant="po", seed=71):
    sc = C.reset_scene(FRAMES)
    C.set_world(top=(0.03, 0.035, 0.05), horizon=(0.012, 0.014, 0.02), bottom=(0.003, 0.004, 0.006))
    C.set_color_management(exposure=0.4)
    rnd = random.Random(seed)
    {"po": po, "crate": crate, "turntable": turntable, "cones": cones, "holed": holed}[variant](sc, rnd)
    return sc
