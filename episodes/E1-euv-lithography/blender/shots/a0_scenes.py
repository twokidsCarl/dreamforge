"""A0 — cold open (F16, F17, F19, F20). Variants:

  cargo     A0_02  night cargo apron: a freighter's nose door lifts on rows of crates (no markings)
  convoy    A0_04  aerial: twenty trucks, a ribbon of headlights through a foggy valley
  assemble  A0_05  xray: trailers turn to glass; modules rise and assemble into the machine outline
  print     A0_07  energy: a beam lands on a dark wafer and prints a glowing circuit
  chip      A0_08  a bare chip on a backlit fingertip, diffraction colours on its surface
  title     A0_10  rim-lit machine silhouette, bursts into modules on "拆开"; the title lights up
All stylised; no real airline, truck, factory or ASML exterior is copied.
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

FRAMES = 160
VIOLET = (0.62, 0.45, 1.0)
CYAN = (0.2, 0.85, 0.95)
TEX = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "textures", "circuit.png")
FONT = "/System/Library/Fonts/STHeiti Medium.ttc"


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


REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".."))
DIES = os.path.join(REPO, "shared", "assets", "dies")


def circuit_image(die="xeon_poly"):
    """A real die photograph (CC0, Wikimedia Commons / Fritzchens Fritz) if fetched, else the procedural layout."""
    p = os.path.join(DIES, die + ".jpg")
    if os.path.exists(p):
        return bpy.data.images.load(p, check_existing=True)
    return bpy.data.images.get("circuit.png") or bpy.data.images.load(TEX)


def circuit_emission(name, color, strength, scale=1.0):
    """Emission masked by the circuit layout texture; strength keyable on node 'Emission'."""
    m = M.emission(name, color, strength)
    nt = m.node_tree
    em = nt.nodes["Emission"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (scale, scale, 1)
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = circuit_image()
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mix = nt.nodes.new("ShaderNodeMixShader")
    out = nt.nodes["Material Output"]
    nt.links.new(tc.outputs["UV"], mp.inputs["Vector"])
    nt.links.new(mp.outputs["Vector"], tex.inputs["Vector"])
    bw = nt.nodes.new("ShaderNodeRGBToBW")
    ramp = nt.nodes.new("ShaderNodeValToRGB")                       # keep the bright metal, drop the background
    ramp.color_ramp.elements[0].position = 0.3
    ramp.color_ramp.elements[1].position = 0.62
    nt.links.new(tex.outputs["Color"], bw.inputs["Color"])
    nt.links.new(bw.outputs["Val"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], mix.inputs["Fac"])
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(em.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])
    m.surface_render_method = "BLENDED"
    return m


def chip_material(name="ChipSurface"):
    """Bare die: circuit-patterned metal with a thin-film sheen (diffraction cue)."""
    m = M.principled(name, (0.5, 0.5, 0.55), metallic=0.9, roughness=0.12, thin_film=520.0, thin_film_ior=2.6)
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (1, 1, 1)
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = circuit_image()
    nt.links.new(tc.outputs["UV"], mp.inputs["Vector"])
    nt.links.new(mp.outputs["Vector"], tex.inputs["Vector"])
    dim = nt.nodes.new("ShaderNodeMix")
    dim.data_type = "RGBA"
    dim.blend_type = "MULTIPLY"
    dim.inputs["Factor"].default_value = 1.0
    dim.inputs["B"].default_value = (1.0, 1.0, 1.0, 1)
    nt.links.new(tex.outputs["Color"], dim.inputs["A"])
    nt.links.new(dim.outputs["Result"], b.inputs["Base Color"])        # the real die photograph
    b.inputs["Metallic"].default_value = 0.0                          # colour comes from the photo, sheen on top
    b.inputs["Roughness"].default_value = 0.2
    b.inputs["Specular IOR Level"].default_value = 0.25
    b.inputs["Coat Weight"].default_value = 0.12                     # glassy passivation layer: a clear highlight
    b.inputs["Coat Roughness"].default_value = 0.03
    # grating rainbow: the hue depends on the viewing direction and slides across the die as the camera moves
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    sepv = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(geo.outputs["Incoming"], sepv.inputs["Vector"])
    sepo = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sepo.inputs["Vector"])
    h1 = nt.nodes.new("ShaderNodeMath")
    h1.operation = "MULTIPLY_ADD"
    h1.inputs[1].default_value = 2.2
    nt.links.new(sepv.outputs["X"], h1.inputs[0])
    nt.links.new(sepo.outputs["X"], h1.inputs[2])
    h2 = nt.nodes.new("ShaderNodeMath")
    h2.operation = "FRACT"
    nt.links.new(h1.outputs[0], h2.inputs[0])
    hsv = nt.nodes.new("ShaderNodeCombineColor")
    hsv.mode = "HSV"
    hsv.inputs[1].default_value = 0.85
    hsv.inputs[2].default_value = 1.0
    nt.links.new(h2.outputs[0], hsv.inputs[0])
    lum = nt.nodes.new("ShaderNodeRGBToBW")
    nt.links.new(tex.outputs["Color"], lum.inputs["Color"])
    rb = nt.nodes.new("ShaderNodeMix")
    rb.data_type = "RGBA"
    rb.blend_type = "MULTIPLY"
    rb.inputs["Factor"].default_value = 1.0
    nt.links.new(hsv.outputs["Color"], rb.inputs["A"])
    nt.links.new(lum.outputs["Val"], rb.inputs["B"])
    em = nt.nodes.new("ShaderNodeMix")
    em.data_type = "RGBA"
    em.inputs["Factor"].default_value = 0.7
    nt.links.new(dim.outputs["Result"], em.inputs["A"])
    nt.links.new(rb.outputs["Result"], em.inputs["B"])
    nt.links.new(em.outputs["Result"], b.inputs["Emission Color"])
    b.inputs["Emission Strength"].default_value = 0.6
    # the dense metal lines act as a grating: thin-film thickness swept in fine bands -> flowing rainbow
    wave = nt.nodes.new("ShaderNodeTexWave")
    wave.inputs["Scale"].default_value = 3.0
    wave.inputs["Distortion"].default_value = 1.5
    nt.links.new(tc.outputs["Object"], wave.inputs["Vector"])
    add = nt.nodes.new("ShaderNodeMath")
    add.operation = "MULTIPLY_ADD"
    add.inputs[1].default_value = 500.0
    add.inputs[2].default_value = 0.0
    nt.links.new(wave.outputs["Fac"], add.inputs[0])
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sep.inputs["Vector"])
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = -1.0
    mr.inputs["To Min"].default_value = 280.0
    mr.inputs["To Max"].default_value = 980.0
    nt.links.new(sep.outputs["X"], mr.inputs["Value"])
    plus = nt.nodes.new("ShaderNodeMath")
    plus.operation = "ADD"
    nt.links.new(mr.outputs["Result"], plus.inputs[0])
    nt.links.new(add.outputs[0], plus.inputs[1])
    nt.links.new(plus.outputs[0], b.inputs["Thin Film Thickness"])
    b.inputs["Thin Film IOR"].default_value = 2.8
    return m


def _text(body, loc, rot, size, mat, align="CENTER"):
    cu = bpy.data.curves.new("T_" + body, "FONT")
    cu.body = body
    cu.size = size
    cu.align_x = align
    cu.align_y = "CENTER"
    try:
        cu.font = bpy.data.fonts.load(FONT, check_existing=True)
    except Exception:
        pass
    ob = bpy.data.objects.new("T_" + body, cu)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = loc
    ob.rotation_euler = rot
    ob.data.materials.append(mat)
    styles.tag(ob, "emitter")
    return ob


# ---- A0_02 ---------------------------------------------------------------------------------
def _loft(name, sections, segs=64, cap=True, cap_start=None, cap_end=None):
    """Fuselage-like loft along X. sections: (x, ry, rz, zc) ellipses, ordered by x."""
    import bmesh
    bm = bmesh.new()
    rings = []
    for x, ry, rz, zc in sections:
        rings.append([bm.verts.new((x, ry * math.cos(2 * math.pi * j / segs), zc + rz * math.sin(2 * math.pi * j / segs)))
                      for j in range(segs)])
    for r0, r1 in zip(rings, rings[1:]):
        for j in range(segs):
            k = (j + 1) % segs
            bm.faces.new((r0[j], r0[k], r1[k], r1[j]))
    if cap_start if cap_start is not None else cap:
        bm.faces.new(rings[0])
    if cap_end if cap_end is not None else cap:
        bm.faces.new(rings[-1])
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    for p in ob.data.polygons:
        p.use_smooth = True
    return ob


def _slab(name, pts, thick, mat):
    """A flat swept surface (wing, fin) from a 4-point outline with a thickness; pts in world space."""
    import bmesh
    bm = bmesh.new()
    n = Vector(pts[1]) - Vector(pts[0])
    m = Vector(pts[3]) - Vector(pts[0])
    up = n.cross(m).normalized() * (thick / 2)
    top = [bm.verts.new(Vector(p) + up) for p in pts]
    bot = [bm.verts.new(Vector(p) - up) for p in pts]
    bm.faces.new(top)
    bm.faces.new(list(reversed(bot)))
    for i in range(4):
        j = (i + 1) % 4
        bm.faces.new((top[i], bot[i], bot[j], top[j]))
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    bev = ob.modifiers.new("Bevel", "BEVEL")
    bev.width = min(0.15, thick * 0.45)
    bev.segments = 3
    ob.data.materials.append(mat)
    styles.tag(ob, "structure")
    return ob


def freighter(skin, belly, rnd, visor_open=None):
    """Generic wide-body freighter with a lifting nose visor (no airline, no type marks). Nose points +X."""
    zc = 4.6
    body = _loft("Fuselage", cap_start=False, cap_end=True, sections=[(0.0, 3.1, 3.2, zc), (-38, 3.1, 3.2, zc), (-44, 2.7, 2.8, zc + 0.5),
                              (-50, 1.8, 1.9, zc + 1.4), (-55, 0.7, 0.8, zc + 2.2), (-56.2, 0.15, 0.2, zc + 2.4)])
    body.data.materials.append(skin)
    body.modifiers.new("Skin", "SOLIDIFY").thickness = 0.12           # open front: a real hull edge
    styles.tag(body, "structure")
    bpy.ops.object.empty_add(location=(0.0, 0, zc + 3.1))
    hinge = bpy.context.object
    hinge.name = "NoseHinge"
    visor = _loft("Visor", cap_start=False, cap_end=True,
                  sections=[(0.0, 3.1, 3.2, zc), (2.5, 3.05, 3.12, zc), (5.0, 2.8, 2.85, zc - 0.05),
                            (7.0, 2.3, 2.3, zc - 0.2), (8.6, 1.6, 1.55, zc - 0.45), (9.7, 0.85, 0.8, zc - 0.7),
                            (10.3, 0.2, 0.2, zc - 0.85)])
    visor.modifiers.new("Skin", "SOLIDIFY").thickness = 0.12
    visor.data.materials.append(skin)
    styles.tag(visor, "structure")
    visor.parent = hinge
    visor.matrix_parent_inverse = hinge.matrix_world.inverted()
    glass = M.principled("CockpitGlass", (0.01, 0.012, 0.015), roughness=0.05, coat=1.0)
    for side in (-1, 1):                                           # cockpit windows, part of the visor
        for k in range(3):
            w = _box(f"Win{side}{k}", (7.0 + 0.6 * k, side * (1.55 - 0.25 * k), zc + 1.45 - 0.22 * k),
                     (0.5, 0.1, 0.4), glass)
            w.rotation_euler = (side * 0.75, 0, 0)
            w.parent = visor
            w.matrix_parent_inverse = visor.matrix_world.inverted()
    # belly fairing stripe
    bel = _loft("Belly", [(-1.0, 3.12, 1.4, zc - 1.9), (-37, 3.12, 1.4, zc - 1.9)], cap=False)
    bel.data.materials.append(belly)
    styles.tag(bel, "structure")
    bel.scale = (1.0, 1.0, 1.0)
    # wings (swept, slight dihedral), engines, tail
    for side in (-1, 1):
        y0, y1 = side * 3.0, side * 31.0
        _slab(f"Wing{side}", [(-16, y0, zc - 1.6), (-30, y0, zc - 1.6), (-36, y1, zc + 0.9), (-32, y1, zc + 0.9)], 0.7, skin)
        for k, yy in enumerate((10.0, 19.0)):
            t = (yy - 3) / 28
            xl = -16 - 16 * t                                       # leading edge at this span
            zz = zc - 1.6 + 2.5 * t - 1.3
            nac = _cyl(f"Nacelle{side}{k}", 1.25, 5.2, (xl + 1.2, side * yy, zz), skin, rot=(0, math.pi / 2, 0), verts=48)
            _cyl(f"Inlet{side}{k}", 1.05, 0.1, (xl + 3.82, side * yy, zz), M.dark_anodized("Inlet"), rot=(0, math.pi / 2, 0),
                 verts=48)
            _cyl(f"Pylon{side}{k}", 0.25, 1.6, (xl + 0.3, side * yy, zz + 1.1), skin, verts=12)
        _slab(f"HStab{side}", [(-48, side * 1.2, zc + 1.8), (-54, side * 1.2, zc + 1.8), (-58, side * 11, zc + 2.6),
                               (-55.5, side * 11, zc + 2.6)], 0.35, skin)
    _slab("Fin", [(-46, 0, zc + 2.6), (-54.5, 0, zc + 2.6), (-58.5, 0, zc + 12.5), (-55, 0, zc + 12.5)], 0.45, skin)
    tyre = M.principled("Tyre", (0.02, 0.02, 0.02), roughness=0.7)
    steel = M.polished_steel("GearSteel", 0.25)
    for x, ys in ((1.5, (0.0,)), (-22.0, (-2.4, 2.4)), (-25.0, (-2.4, 2.4))):
        for y in ys:
            _cyl(f"Strut{x}{y}", 0.14, zc - 2.6, (x, y, (zc - 2.6) / 2 + 0.6), steel, verts=12)
            for dy in (-0.45, 0.45):
                _cyl(f"Tyre{x}{y}{dy}", 0.62, 0.42, (x, y + dy, 0.62), tyre, rot=(math.pi / 2, 0, 0), verts=32)
    return hinge


def cargo(sc, rnd):
    sc["hdri_world"] = True
    C.hdri_world("rogland_moonlit_night", strength=0.07, rotation=math.radians(110), tint=(0.7, 0.82, 1.1))
    wet = M.pbr("Apron", "asphalt_02", scale=0.08, tint=(0.08, 0.085, 0.1), rough_mul=0.2, rough_add=0.01, normal=0.6,
                fallback=(0.02, 0.022, 0.026))                                  # wet apron (CC0)
    _box("Apron", (0, 0, -0.05), (400, 400, 0.1), wet)
    skin = M.principled("Paint", (0.78, 0.8, 0.82), roughness=0.28, coat=0.4)
    belly = M.principled("BellyPaint", (0.42, 0.45, 0.5), roughness=0.35, coat=0.3)
    hinge = freighter(skin, belly, rnd)
    _key(hinge, 1, rotation_euler=(0, 0, 0))
    _key(hinge, 24, rotation_euler=(0, 0, 0))
    _key(hinge, 140, rotation_euler=(0, math.radians(-58), 0))
    # the hold: cold strip lights, a roller floor and rows of plywood crates
    lamp = M.emission("HoldLamp", (0.86, 0.92, 1.0), 10.0)
    for k in range(7):
        _box(f"HoldLamp{k}", (-1.5 - 5.0 * k, 0, 7.3), (3.0, 0.3, 0.05), lamp, role="emitter")
    ply = M.pbr("Crate", "brushed_concrete", scale=0.5, tint=(1.5, 1.15, 0.75), rough_mul=0.5, rough_add=0.4,
                normal=0.3, fallback=(0.62, 0.5, 0.34))
    for k in range(8):
        for side in (-1, 1):
            h = rnd.uniform(1.8, 2.5)
            _box(f"Crate{k}{side}", (-2.0 - 4.2 * k, side * 1.35, 1.75 + h / 2), (3.5, 2.3, h), ply, bevel=0.04)
    _box("HoldFloor", (-18.0, 0, 1.65), (38.0, 5.6, 0.12), M.dark_anodized("HoldFloor"))
    bpy.ops.object.light_add(type="AREA", location=(-8, 0, 7.0))
    il = bpy.context.object
    il.data.energy = 6000
    il.data.size = 26
    il.data.size_y = 3.5
    il.data.color = (0.86, 0.92, 1.0)
    styles.tag(il, "rig")
    # apron: light masts (visible bulbs), a lit terminal far behind, edge lights, a tug
    bulb = M.emission("MastBulb", (1.0, 0.86, 0.62), 40.0)
    mast = M.principled("Mast", (0.05, 0.05, 0.06), roughness=0.6)
    for x, y in ((40, -45), (-30, -60), (-70, 40), (70, 35)):
        _cyl(f"Mast{x}", 0.3, 26, (x, y, 13), mast, verts=12)
        _box(f"MastHead{x}", (x, y, 26.5), (2.4, 0.8, 0.8), bulb, role="emitter")
        bpy.ops.object.light_add(type="SPOT", location=(x, y, 26))
        l = bpy.context.object
        l.data.energy = 120000
        l.data.spot_size = math.radians(55)
        l.data.spot_blend = 0.6
        l.data.color = (1.0, 0.88, 0.7)
        l.rotation_euler = (Vector((-18, 0, 2)) - Vector((x, y, 26))).to_track_quat("-Z", "Y").to_euler()
        styles.tag(l, "rig")
    win = M.emission("TerminalWin", (1.0, 0.82, 0.55), 6.0)
    _box("Terminal", (-60, 110, 9), (180, 20, 18), M.principled("TermWall", (0.03, 0.03, 0.035), roughness=0.8))
    for k in range(40):
        _box(f"TWin{k}", (-150 + 4.5 * k, 99.9, 7 + (k % 3) * 3.5), (3.2, 0.1, 1.6), win, role="emitter")
    edge = M.emission("EdgeLight", (0.3, 0.55, 1.0), 25.0)
    for k in range(30):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.18, location=(-120 + 9 * k, 70 + rnd.uniform(-1, 1), 0.3))
        e = bpy.context.object
        e.data.materials.append(edge)
        styles.tag(e, "emitter")
    # low haze so the masts throw beams
    fog = bpy.data.materials.new("ApronHaze")
    fog.use_nodes = True
    nt = fog.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    vs = nt.nodes.new("ShaderNodeVolumePrincipled")
    vs.inputs["Density"].default_value = 0.0015
    vs.inputs["Color"].default_value = (0.8, 0.85, 0.95, 1)
    nt.links.new(vs.outputs[0], out.inputs["Volume"])
    _box("Haze", (0, 0, 15), (260, 260, 30), fog, role="env")
    B._camera("CamA0_02", [(1, (-2.0, 0, 5.4), (30.0, -18.0, 1.0), 32, 4.0),
                           (156, (-4.0, 0, 5.6), (24.0, -13.5, 1.2), 32, 4.0)])


# ---- A0_03 ---------------------------------------------------------------------------------
def _group(fn):
    """Run a builder, parent everything it made to one empty, return the empty."""
    before = set(bpy.data.objects)
    fn()
    new = [o for o in bpy.data.objects if o not in before and o.parent is None]
    bpy.ops.object.empty_add(location=(0, 0, 0))
    root = bpy.context.object
    for o in new:
        o.parent = root
    return root


def _truck(name, mat_cab, mat_box, tyre):
    def build():
        _box(name + "Box", (-4.2, 0, 2.1), (9.0, 2.5, 2.8), mat_box, bevel=0.05)
        _box(name + "Cab", (1.6, 0, 1.75), (2.4, 2.45, 2.3), mat_cab, bevel=0.25)
        for x in (-7.5, -6.4, 1.6):
            for y in (-1.15, 1.15):
                _cyl(name + f"W{x}{y}", 0.5, 0.35, (x, y, 0.5), tyre, rot=(math.pi / 2, 0, 0), verts=24)
        light = M.emission(name + "Head", (1.0, 0.95, 0.85), 30.0)
        for y in (-0.9, 0.9):
            _box(name + f"HL{y}", (2.81, y, 1.0), (0.04, 0.35, 0.2), light, role="emitter")
    return _group(build)


def _corrugated(name, color):
    """Painted shipping-container steel: vertical corrugations as a bump, a little wear in the roughness."""
    m = M.principled(name, color, metallic=0.35, roughness=0.45)
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    wave = nt.nodes.new("ShaderNodeTexWave")
    wave.bands_direction = "Y"                                      # ribs along the long side
    wave.inputs["Scale"].default_value = 2.2
    wave.inputs["Distortion"].default_value = 0.0
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 1.0
    nt.links.new(tc.outputs["Object"], wave.inputs["Vector"])
    nt.links.new(wave.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    return m


def _boxa(name, size, mat, bevel=0.0):
    """A box with its size baked into the mesh, so scale keyframes animate from 1."""
    ob = _box(name, (0, 0, 0), size, mat, bevel=bevel)
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return ob


def logistics(sc, rnd):
    """One crate -> 250+ crates -> 43 containers -> freighters -> 20 trucks (F17), as one 3D miniature:
    a dark studio table that the camera tracks along, left to right."""
    C.set_world(top=(0.02, 0.026, 0.04), horizon=(0.01, 0.012, 0.018), bottom=(0.002, 0.002, 0.003))
    floor = M.pbr("Table", "brushed_concrete", scale=0.05, tint=(0.07, 0.075, 0.085), rough_mul=0.3, rough_add=0.3,
                  normal=0.3, fallback=(0.03, 0.03, 0.035))
    _box("Table", (60, 0, -0.05), (1200, 1200, 0.1), floor)
    wood = M.pbr("Plywood", "brushed_concrete", scale=0.6, tint=(1.6, 1.2, 0.78), rough_mul=0.4, rough_add=0.45,
                 normal=0.4, fallback=(0.62, 0.5, 0.34))
    # 1) one crate splits into 252 (a 21 x 12 block), f8-50
    crates = []
    for i in range(252):
        cx, cy = i % 21, i // 21
        home = Vector(((cx - 10) * 1.25, (cy - 5.5) * 1.25, 0.5))
        c = _boxa(f"Crate{i}", (1.0, 1.0, 1.0), wood, bevel=0.06)
        c.location = (0, 0, 0.5)
        big = 9.0 if i == 0 else 0.001
        _key(c, 1, location=(0, 0, 4.5) if i == 0 else (0, 0, 0.5), scale=(big, big, big))
        _key(c, 8, location=(0, 0, 4.5) if i == 0 else (0, 0, 0.5), scale=(big, big, big))
        _key(c, 26 + int(i / 252 * 14), location=home, scale=(1, 1, 1))
        crates.append((c, home))
    # 2) crates pour into 43 containers (a 9 x 5 yard, minus two), f52-86
    steels = [_corrugated(f"ContainerSteel{n}", col)
              for n, col in enumerate(((0.03, 0.08, 0.18), (0.22, 0.035, 0.025), (0.25, 0.26, 0.27), (0.38, 0.17, 0.03)))]
    conts = []
    for j in range(43):
        gx, gy = j % 9, j // 9
        pos = Vector((40 + gx * 3.0, (gy - 2) * 6.6, 1.3))
        k = _boxa(f"Container{j}", (2.44, 6.06, 2.59), steels[rnd.randrange(4)], bevel=0.03)
        _key(k, 1, location=pos, scale=(0.001, 0.001, 0.001))
        _key(k, 56 + j // 2, location=pos, scale=(0.001, 0.001, 0.001))
        _key(k, 72 + j // 2, location=pos, scale=(1, 1, 1))
        conts.append((k, pos))
    for i, (c, home) in enumerate(crates):
        k, pos = conts[i % 43]
        f0 = 48 + (i % 43) // 2
        _key(c, f0, location=home, scale=(1, 1, 1))
        _key(c, f0 + 18, location=pos + Vector((0, 0, 1.0)), scale=(0.2, 0.2, 0.2))
        _key(c, f0 + 19, scale=(0.001, 0.001, 0.001))
    # 3) containers rise into four freighters that take off to the right, f88-140
    skin = M.principled("PlanePaint", (0.78, 0.8, 0.82), roughness=0.3, coat=0.3)
    belly = M.principled("PlaneBelly", (0.42, 0.45, 0.5), roughness=0.35)
    planes = []
    for p_i in range(4):
        root = _group(lambda: freighter(skin, belly, rnd))
        root.name = f"Plane{p_i}"
        start = Vector((80 + p_i * 4, (p_i - 1.5) * 15, 0.0))
        s0 = 0.22
        _key(root, 1, location=start, scale=(0.001, 0.001, 0.001))
        _key(root, 84, location=start, scale=(0.001, 0.001, 0.001))
        _key(root, 96, location=start, scale=(s0, s0, s0))
        _key(root, 118 + 4 * p_i, location=start, scale=(s0, s0, s0))
        _key(root, 150 + 4 * p_i, location=start + Vector((60, 0, 22)), scale=(s0, s0, s0), rotation_euler=(0, math.radians(-12), 0))
        planes.append((root, start))
    for j, (k, pos) in enumerate(conts):
        root, start = planes[j % 4]
        f0 = 96 + (j % 11)
        _key(k, f0, location=pos, scale=(1, 1, 1))
        _key(k, f0 + 16, location=start + Vector((-3, 0, 1.0)), scale=(0.12, 0.12, 0.12))
        _key(k, f0 + 17, scale=(0.001, 0.001, 0.001))
    # 4) twenty trucks roll out along a road to the right, f140-198
    road = M.principled("Road", (0.02, 0.022, 0.025), roughness=0.25)
    _box("Road", (300, 0, 0.01), (360, 9, 0.02), road)
    lane = M.emission("Lane", (0.9, 0.85, 0.6), 1.5)
    for k_ in range(30):
        _box(f"Lane{k_}", (125 + 5.2 * k_, 0, 0.03), (2.2, 0.15, 0.01), lane, role="emitter")
    cab = M.principled("TruckCab", (0.8, 0.8, 0.82), roughness=0.3, coat=0.4)
    box = M.principled("TruckBox", (0.3, 0.33, 0.38), roughness=0.45)
    tyre = M.principled("TruckTyre", (0.02, 0.02, 0.02), roughness=0.7)
    for t_i in range(20):
        tr = _truck(f"Truck{t_i}", cab, box, tyre)
        y = -2.2 if t_i % 2 == 0 else 2.2
        x0 = 128 - 12 * (t_i // 2)
        _key(tr, 1, location=(x0, y, 0), scale=(0.001, 0.001, 0.001))
        _key(tr, 136 + t_i, location=(x0, y, 0), scale=(0.001, 0.001, 0.001))
        _key(tr, 146 + t_i, location=(x0, y, 0), scale=(0.6, 0.6, 0.6))
        _key(tr, 246, location=(x0 + 70, y, 0), scale=(0.6, 0.6, 0.6))
    for lt in (B._area("Key", (40, -40, 50), (0.7, 0, 0.3), 60, 60000, (1.0, 0.95, 0.88)),
               B._area("Rim", (90, 60, 25), (1.2, 0, 2.6), 60, 30000, (0.55, 0.7, 1.0))):
        lt.visible_glossy = False                                   # no hard light-panel shapes on the table
    # track left -> right with the goods, a short pause at each conversion
    B._camera("CamA0_03", [(1, (0, 0, 2.0), (-6, -38, 22), 35, 8.0), (44, (0, 0, 1.0), (-4, -36, 20), 35, 8.0),
                           (70, (44, 0, 1.0), (40, -40, 22), 35, 8.0), (100, (52, 0, 1.0), (48, -42, 22), 35, 8.0),
                           (130, (100, 0, 4.0), (96, -46, 26), 35, 8.0), (160, (140, 0, 1.0), (128, -42, 18), 35, 8.0),
                           (198, (150, 0, 1.0), (138, -40, 17), 35, 8.0),
                           (246, (175, 0, 1.0), (150, -52, 30), 32, 8.0)])          # rise: the whole convoy


# ---- A0_04 ---------------------------------------------------------------------------------
def convoy(sc, rnd):
    sc["hdri_world"] = True
    C.hdri_world("rogland_moonlit_night", strength=0.1, rotation=math.radians(200), tint=(0.7, 0.82, 1.1))
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=200, y_subdivisions=200, size=600, location=(0, 0, 0))
    ter = bpy.context.object
    ter.name = "Valley"
    tex = bpy.data.textures.new("Hills", "CLOUDS")
    tex.noise_scale = 9.0
    d = ter.modifiers.new("Hills", "DISPLACE")
    d.texture = tex
    d.strength = 45.0
    ter.location.z = -26.0                                          # the road runs along the valley floor
    for p in ter.data.polygons:
        p.use_smooth = True
    ter.data.materials.append(M.principled("Forest", (0.02, 0.028, 0.022), roughness=0.9))
    styles.tag(ter, "structure")
    # road: a gentle S along the valley floor
    def road(u):  # noqa: E306
        return Vector((-260 + 520 * u, 60 * math.sin(u * 4.0), 0.0))
    pts = [road(i / 200) for i in range(201)]
    cu = bpy.data.curves.new("Road", "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = 3.0
    sp = cu.splines.new("POLY")
    sp.points.add(len(pts) - 1)
    for i, p in enumerate(pts):
        sp.points[i].co = (p.x, p.y, 30.0, 1)
    ro = bpy.data.objects.new("Road", cu)
    sc.collection.objects.link(ro)
    ro.data.materials.append(M.principled("Asphalt", (0.03, 0.03, 0.035), roughness=0.4))
    styles.tag(ro, "structure")
    ro.scale = (1, 1, 0.08)
    head = M.emission("Headlight", (1.0, 0.95, 0.85), 400.0)
    tail = M.emission("Taillight", (1.0, 0.1, 0.05), 120.0)
    marker = M.emission("Marker", (1.0, 0.6, 0.15), 60.0)
    cab = M.principled("TruckCab", (0.3, 0.32, 0.36), metallic=0.4, roughness=0.4)
    for k in range(20):
        bpy.ops.object.empty_add(location=(0, 0, 0))
        tr = bpy.context.object
        tr.name = f"Truck{k}"
        parts = [_box(f"Trailer{k}", (-5.0, 0, 2.3), (13.0, 2.5, 3.2), cab),
                 _box(f"Cab{k}", (3.0, 0, 1.9), (2.6, 2.5, 2.8), cab, bevel=0.2)]
        for x in (-11.4, 1.4):                                    # amber marker lights, visible from above
            for y in (-1.3, 1.3):
                parts.append(_box(f"ML{k}{x}{y}", (x, y, 3.95), (0.25, 0.12, 0.12), marker, role="emitter"))
        for y in (-0.9, 0.9):
            parts.append(_box(f"HL{k}{y}", (4.35, y, 1.0), (0.1, 0.35, 0.25), head, role="emitter"))
            parts.append(_box(f"TL{k}{y}", (-11.55, y, 1.0), (0.1, 0.3, 0.2), tail, role="emitter"))
        for p in parts:
            p.parent = tr
        for f in (1, 60):
            u = 0.30 + 0.028 * k + (f - 1) / 59 * 0.03
            p = road(u)
            q = road(u + 0.002)
            tr.location = (p.x, p.y, 30.6 * 0.08 + 0.4)
            tr.rotation_euler = (0, 0, math.atan2(q.y - p.y, q.x - p.x))
            tr.keyframe_insert("location", frame=f)
            tr.keyframe_insert("rotation_euler", frame=f)
        spot = bpy.data.lights.new(f"Beam{k}", "SPOT")
        spot.energy = 60000                                         # long cones in the valley haze
        spot.spot_size = math.radians(35)
        spot.color = (1.0, 0.95, 0.85)
        so = bpy.data.objects.new(f"Beam{k}", spot)
        sc.collection.objects.link(so)
        so.parent = tr
        so.location = (4.5, 0, 1.2)
        so.rotation_euler = (0, math.radians(100), 0)
    # valley fog
    fog = bpy.data.materials.new("Fog")
    fog.use_nodes = True
    nt = fog.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    vs = nt.nodes.new("ShaderNodeVolumePrincipled")
    vs.inputs["Density"].default_value = 0.02
    vs.inputs["Color"].default_value = (0.7, 0.75, 0.85, 1)
    nt.links.new(vs.outputs[0], out.inputs["Volume"])
    _box("FogVolume", (0, 0, 20), (600, 600, 40), fog, role="env")
    moon = bpy.data.lights.new("Moon", "SUN")
    moon.energy = 0.6
    moon.color = (0.6, 0.7, 1.0)
    mo = bpy.data.objects.new("Moon", moon)
    sc.collection.objects.link(mo)
    mo.rotation_euler = (math.radians(50), 0, math.radians(30))
    c = road(0.58)
    B._camera("CamA0_04", [(1, (c.x - 30, c.y, 2.0), (c.x - 100, c.y - 70, 75.0), 35, 16.0),
                           (60, (c.x - 10, c.y, 2.0), (c.x - 75, c.y - 55, 52.0), 35, 16.0)])


# ---- A0_05 ---------------------------------------------------------------------------------
def assemble(sc, rnd):
    C.set_world(top=(0.9, 0.91, 0.93), horizon=(0.78, 0.79, 0.82), bottom=(0.6, 0.61, 0.64))
    before = set(bpy.data.objects)
    path, pmat = BM.machine()
    new = [o for o in bpy.data.objects if o not in before]
    parts = [o for o in BM.attach_small(new) if styles.role_of(o) == "structure"]
    shells = [o for o in bpy.data.objects if o not in before and styles.role_of(o) == "shell"]
    glass = M.principled("TrailerPanel", (0.78, 0.8, 0.82), metallic=0.2, roughness=0.45)
    nt = 6
    for k in range(nt):                                            # trailers in a row in front
        _box(f"Trailer{k}", (-9.0 + 3.6 * k, -7.0, -0.6), (3.2, 2.4, 2.6), glass, role="shell")
    for i, o in enumerate(parts):
        home = o.location.copy()
        k = i % nt
        start = Vector((-9.0 + 3.6 * k + rnd.uniform(-0.8, 0.8), -7.0 + rnd.uniform(-0.6, 0.6), -1.2 + 0.2 * (i // nt)))
        f0 = 20 + 4 * i
        _key(o, 1, location=start)
        _key(o, f0, location=start)
        _key(o, f0 + 20, location=Vector((start.x * 0.6 + home.x * 0.4, -3.5, home.z + 2.5)))
        _key(o, f0 + 45, location=home)
    for s in shells:                                               # the machine's own casing appears last
        _key(s, 1, hide_render=True)
        _key(s, 118, hide_render=False)
    path.data.bevel_factor_end = 0.0
    path.data.keyframe_insert("bevel_factor_end", frame=100)
    path.data.bevel_factor_end = 1.0
    path.data.keyframe_insert("bevel_factor_end", frame=138)
    B._area("MKey", (0, -9, 8), (0.9, 0, 0), 16, 2500, (0.8, 0.85, 1.0))
    B._camera("CamA0_05", [(1, (-1.0, -6.0, -0.4), (2.0, -16.0, 0.4), 35, 8.0),
                           (142, (-1.6, -1.0, 0.4), (4.0, -17.0, 6.0), 35, 8.0)])


# ---- A0_07 ---------------------------------------------------------------------------------
def print_(sc, rnd):
    C.set_world(top=(0, 0, 0), horizon=(0, 0, 0), bottom=(0, 0, 0))
    import b7_scenes
    bpy.ops.mesh.primitive_plane_add(size=6, location=(0, 0, 0))
    w = bpy.context.object
    w.data.materials.append(M.principled("DarkSi", (0.02, 0.02, 0.03), roughness=0.3))
    styles.tag(w, "structure")
    bpy.ops.mesh.primitive_plane_add(size=4.0, location=(0, 0, 0.005))
    pat = bpy.context.object
    m = circuit_emission("PrintGlow", (0.7, 0.55, 1.0), 0.0, scale=1.0)
    pat.data.materials.append(m)
    styles.tag(pat, "emitter")
    M.set_emission_strength(m, 30, 0.0)
    M.set_emission_strength(m, 60, 4.0)
    beam_m = b7_scenes._cone_mat("PrintBeam", 0.28)
    bpy.ops.mesh.primitive_cone_add(vertices=64, radius1=2.2, radius2=0.2, depth=9.0, end_fill_type="NOTHING",
                                    location=(0, 0, 4.5))
    beam = bpy.context.object
    beam.data.materials.append(beam_m)
    styles.tag(beam, "emitter")
    _key(beam, 1, location=(0, 0, 14.0))
    _key(beam, 34, location=(0, 0, 4.5))
    B._camera("CamA0_07", [(1, (0, 0, 6.0), (0.0, -9.0, 9.0), 35, 11.0), (96, (0, 0, 0.0), (0.0, -4.2, 3.2), 35, 11.0)])


# ---- A0_08 ---------------------------------------------------------------------------------
def chip(sc, rnd):
    C.set_world(top=(0.004, 0.004, 0.006), horizon=(0.002, 0.002, 0.003), bottom=(0.0, 0.0, 0.0))
    sc["hdri"], sc["hdri_strength"] = "studio_small_09", 0.12        # faint room reflection; the rainbow is in the die
    skin = M.principled("Skin", (0.22, 0.13, 0.1), roughness=0.5)
    sk = skin.node_tree.nodes["Principled BSDF"]
    sk.inputs["Subsurface Weight"].default_value = 0.5
    sk.inputs["Subsurface Radius"].default_value = (1.0, 0.35, 0.2)
    sk.inputs["Subsurface Scale"].default_value = 0.05
    _cyl("Finger", 0.8, 5.0, (-2.5, 0, 0), skin, rot=(0, math.pi / 2, 0), verts=64)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.8, segments=64, ring_count=32, location=(0, 0, 0))
    tip = bpy.context.object
    tip.scale = (1.05, 1.0, 0.92)
    for p in tip.data.polygons:
        p.use_smooth = True
    tip.data.materials.append(skin)
    styles.tag(tip, "structure")
    body = _box("DieBody", (-0.1, 0, 0.86), (1.2, 0.92, 0.04), M.principled("Silicon", (0.03, 0.03, 0.035),
                                                                             metallic=0.6, roughness=0.3))
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0))
    top = bpy.context.object
    top.name = "DieTop"
    top.data.materials.append(chip_material())
    styles.tag(top, "structure")
    top.parent = body                                               # rides on the body's top face
    top.location = (0, 0, 1.05)                               # body is a unit cube scaled by its size
    top.scale = (1.98, 1.98, 1)                                     # plane is 1 wide, the cube 2: cover the top
    body.rotation_euler = (0, math.radians(-4), math.radians(12))
    rim = B._area("BackRim", (-1.0, 4.0, 2.0), (math.radians(-60), 0, math.radians(180)), 3, 900, (1.0, 0.85, 0.7))
    rim.visible_glossy = False                                      # rim the finger only; no hot spot on the die
    for name, loc, size, st in (("ChipBoxA", (-2.4, 3.6, 2.8), 4, 0.45), ("ChipBoxB", (2.8, 3.0, 2.2), 3, 0.6)):
        bpy.ops.mesh.primitive_plane_add(size=size, location=loc)
        sb = bpy.context.object
        sb.rotation_euler = (Vector((0, 0, 0.8)) - Vector(loc)).to_track_quat("Z", "Y").to_euler()
        sb.data.materials.append(M.soft_emitter(name, (1, 0.98, 0.95), st))
        sb.visible_camera = False
        styles.tag(sb, "rig")
    # a slow arc across the die: the rainbow bands slide as the angle changes; the finger stays a soft shape
    B._camera("CamA0_08", [(1, (-0.15, 0.0, 0.9), (2.4, -2.6, 2.1), 85, 2.4),
                           (126, (-0.1, 0.05, 0.9), (3.2, -1.6, 1.8), 85, 2.4)])


# ---- A0_10 ---------------------------------------------------------------------------------
def title(sc, rnd):
    C.set_world(top=(0, 0, 0), horizon=(0, 0, 0), bottom=(0, 0, 0))
    before = set(bpy.data.objects)
    path, pmat = BM.machine(with_path=False)
    mods = BM.attach_small([o for o in bpy.data.objects if o not in before])
    centre = Vector((-1.6, 0, 0.35))
    for o in mods:                                                # burst into hovering modules on "拆开"
        home = o.location.copy()
        d = home - centre
        d = Vector((d.x, d.y - 0.4, d.z)) if d.length > 0.2 else Vector((0, -1, 0.4))
        out = home + d.normalized() * (1.8 + 0.25 * d.length) + Vector((0, 0, 0.4))
        _key(o, 120, location=home)
        _key(o, 136, location=out)
        _key(o, 160, location=out + d.normalized() * 0.25)
    chars = "一台光刻机里发生了什么"
    size = 0.9
    x0 = -1.6 - size * (len(chars) - 1) / 2
    for i, ch in enumerate(chars):
        m = M.emission(f"Glyph{i}", (0.92, 0.9, 1.0), 0.0)
        _text(ch, (x0 + i * size, -3.2, 4.9), (math.pi / 2, 0, 0), size, m)
        M.set_emission_strength(m, 92 + 3 * i, 0.0)
        M.set_emission_strength(m, 100 + 3 * i, 5.0)
    sub = M.emission("SubGlyph", (0.6, 0.62, 0.7), 0.0)
    _text("ASML EUV 光刻机", (-1.6, -3.2, 4.05), (math.pi / 2, 0, 0), 0.38, sub)
    M.set_emission_strength(sub, 128, 0.0)
    M.set_emission_strength(sub, 142, 2.0)
    B._camera("CamA0_10", [(1, (-1.6, 0, 1.4), (-1.6, -19.0, 2.6), 40, 11.0), (160, (-1.6, 0, 1.8), (-1.6, -20.5, 2.9), 40, 11.0)])


def after_style(style, shot_id):
    if shot_id == "A0_10":
        # brighter rim than the default energy look: the machine reads as a ship in a dark hangar
        for rimm in bpy.data.materials:
            if not rimm.name.startswith("EnergyRim") or not rimm.node_tree:
                continue
            for n in rimm.node_tree.nodes:
                if n.type == "MATH" and n.operation == "MULTIPLY":
                    n.inputs[1].default_value *= 3.5
                if n.type == "LAYER_WEIGHT":
                    n.inputs["Blend"].default_value = 0.3


def build(variant="cargo", seed=11):
    sc = C.reset_scene(FRAMES)
    C.set_world(top=(0.03, 0.035, 0.05), horizon=(0.012, 0.014, 0.02), bottom=(0.003, 0.004, 0.006))
    C.set_color_management(exposure=0.4)
    rnd = random.Random(seed)
    {"cargo": cargo, "logistics": logistics, "convoy": convoy, "assemble": assemble, "print": print_, "chip": chip,
     "title": title}[variant](sc, rnd)
    return sc
