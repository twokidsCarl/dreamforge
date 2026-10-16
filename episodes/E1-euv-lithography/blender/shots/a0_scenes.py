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


def circuit_image():
    img = bpy.data.images.get("circuit.png") or bpy.data.images.load(TEX)
    return img


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
    nt.links.new(tex.outputs["Color"], mix.inputs["Fac"])
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
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.inputs["A"].default_value = (0.18, 0.17, 0.2, 1)
    mix.inputs["B"].default_value = (0.75, 0.72, 0.68, 1)
    nt.links.new(tex.outputs["Color"], mix.inputs["Factor"])
    nt.links.new(mix.outputs["Result"], b.inputs["Base Color"])
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sep.inputs["Vector"])
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = -1.0
    mr.inputs["To Min"].default_value = 280.0
    mr.inputs["To Max"].default_value = 980.0
    nt.links.new(sep.outputs["X"], mr.inputs["Value"])
    nt.links.new(mr.outputs["Result"], b.inputs["Thin Film Thickness"])
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
def cargo(sc, rnd):
    C.set_world(top=(0.004, 0.006, 0.012), horizon=(0.003, 0.004, 0.008), bottom=(0.0, 0.0, 0.001))
    wet = M.principled("Apron", (0.02, 0.022, 0.026), roughness=0.07)
    _box("Apron", (0, 0, -0.05), (200, 200, 0.1), wet)
    skin = M.principled("Fuselage", (0.55, 0.57, 0.6), metallic=0.3, roughness=0.5)
    body = _cyl("Fuselage", 3.0, 36.0, (-18.0, 0, 4.2), skin, rot=(0, math.pi / 2, 0), verts=96)
    # nose section on a hinge at its top edge: lifts like a visor
    bpy.ops.object.empty_add(location=(0.0, 0, 7.2))
    hinge = bpy.context.object
    hinge.name = "NoseHinge"
    bpy.ops.mesh.primitive_uv_sphere_add(radius=3.0, segments=64, ring_count=32, location=(0, 0, 4.2))
    nose = bpy.context.object
    nose.name = "Nose"
    nose.scale = (1.9, 1.0, 1.0)
    for p in nose.data.polygons:
        p.use_smooth = True
    bis = nose.modifiers.new("Half", "BOOLEAN")
    bpy.ops.mesh.primitive_cube_add(location=(-6.0, 0, 4.2))
    cutter = bpy.context.object
    cutter.scale = (6.0, 6.0, 6.0)
    cutter.hide_render = cutter.hide_viewport = True
    bis.object = cutter
    bis.operation = "DIFFERENCE"
    nose.data.materials.append(skin)
    styles.tag(nose, "structure")
    nose.parent = hinge
    nose.matrix_parent_inverse = hinge.matrix_world.inverted()
    _key(hinge, 1, rotation_euler=(0, 0, 0))
    _key(hinge, 20, rotation_euler=(0, 0, 0))
    _key(hinge, 130, rotation_euler=(0, math.radians(-62), 0))
    for side in (-1, 1):                                           # swept wings, engines, tail
        w = _box(f"Wing{side}", (-20.0, side * 11.0, 3.2), (7.0, 18.0, 0.5), skin, bevel=0.1)
        w.rotation_euler = (0, 0, math.radians(-22 * side))
        _cyl(f"Engine{side}", 1.2, 4.0, (-16.5, side * 8.0, 1.8), M.dark_anodized(f"Eng{side}"),
             rot=(0, math.pi / 2, 0))
    _box("Fin", (-34.0, 0, 9.0), (6.0, 0.5, 9.0), skin, bevel=0.1).rotation_euler = (0, math.radians(-20), 0)
    for x in (-4.0, -20.0):
        for y in ((0.0,) if x > -10 else (-2.5, 2.5)):
            _cyl(f"Gear{x}{y}", 0.6, 0.5, (x, y, 0.6), M.dark_anodized("Tyre"), rot=(math.pi / 2, 0, 0))
            _cyl(f"Strut{x}{y}", 0.12, 1.4, (x, y, 1.5), M.polished_steel("GearSteel"))
    # interior: cold strip lights and rows of plywood crates
    lamp = M.emission("HoldLamp", (0.86, 0.92, 1.0), 8.0)
    for k in range(6):
        _box(f"HoldLamp{k}", (-3.0 - 5.0 * k, 0, 6.9), (3.0, 0.25, 0.05), lamp, role="emitter")
    ply = M.principled("Crate", (0.62, 0.5, 0.34), roughness=0.8)
    for k in range(7):
        for side in (-1, 1):
            h = rnd.uniform(1.6, 2.4)
            _box(f"Crate{k}{side}", (-2.5 - 4.2 * k, side * 1.25, 1.3 + h / 2), (3.4, 2.1, h), ply, bevel=0.03)
    _box("HoldFloor", (-18.0, 0, 1.25), (36.0, 5.2, 0.1), M.dark_anodized("HoldFloor"))
    for x in (-40, -20, 10, 30):                                   # apron flood lights
        bpy.ops.object.light_add(type="SPOT", location=(x, -30, 18))
        l = bpy.context.object
        l.data.energy = 25000
        l.data.spot_size = math.radians(40)
        l.data.color = (0.82, 0.9, 1.0)
        l.rotation_euler = (Vector((0, 0, 3)) - Vector((x, -30, 18))).to_track_quat("-Z", "Y").to_euler()
        styles.tag(l, "rig")
    bpy.ops.object.light_add(type="AREA", location=(-10, 0, 6.8))
    il = bpy.context.object
    il.data.energy = 3000
    il.data.size = 20
    il.data.size_y = 3
    il.data.color = (0.86, 0.92, 1.0)
    styles.tag(il, "rig")
    B._camera("CamA0_02", [(1, (-6, 0, 4.0), (20.0, -9.0, 0.7), 28, 5.6), (148, (-4.0, 0, 3.2), (13.0, -4.5, 0.9), 28, 5.6)])


# ---- A0_04 ---------------------------------------------------------------------------------
def convoy(sc, rnd):
    C.set_world(top=(0.006, 0.008, 0.014), horizon=(0.01, 0.012, 0.018), bottom=(0.0, 0.0, 0.001))
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
    ter.data.materials.append(M.principled("Forest", (0.01, 0.014, 0.012), roughness=0.9))
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
        spot.energy = 3000
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
    vs.inputs["Density"].default_value = 0.012
    vs.inputs["Color"].default_value = (0.7, 0.75, 0.85, 1)
    nt.links.new(vs.outputs[0], out.inputs["Volume"])
    _box("FogVolume", (0, 0, 20), (600, 600, 40), fog, role="env")
    moon = bpy.data.lights.new("Moon", "SUN")
    moon.energy = 0.35
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
    parts = [o for o in bpy.data.objects if o not in before and o.type == "MESH"
             and styles.role_of(o) == "structure" and o.parent is None]
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
    C.set_world(top=(0.008, 0.009, 0.013), horizon=(0.004, 0.004, 0.006), bottom=(0.0, 0.0, 0.001))
    skin = M.principled("Skin", (0.55, 0.36, 0.28), roughness=0.45)
    sk = skin.node_tree.nodes["Principled BSDF"]
    sk.inputs["Subsurface Weight"].default_value = 0.6
    sk.inputs["Subsurface Radius"].default_value = (1.0, 0.35, 0.2)
    sk.inputs["Subsurface Scale"].default_value = 0.08
    wave = skin.node_tree.nodes.new("ShaderNodeTexWave")           # fingerprint ridges
    wave.wave_type = "RINGS"
    wave.inputs["Scale"].default_value = 30.0
    wave.inputs["Distortion"].default_value = 1.5
    bump = skin.node_tree.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.25
    skin.node_tree.links.new(wave.outputs["Fac"], bump.inputs["Height"])
    skin.node_tree.links.new(bump.outputs["Normal"], sk.inputs["Normal"])
    # fingertip: a capsule pointing toward +X, pad facing up
    _cyl("Finger", 0.8, 5.0, (-2.5, 0, 0), skin, rot=(0, math.pi / 2, 0), verts=64)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.8, segments=64, ring_count=32, location=(0, 0, 0))
    tip = bpy.context.object
    tip.scale = (1.05, 1.0, 0.92)
    for p in tip.data.polygons:
        p.use_smooth = True
    tip.data.materials.append(skin)
    styles.tag(tip, "structure")
    die = _box("Die", (-0.25, 0, 0.83), (1.1, 1.1, 0.06), chip_material(), bevel=0.004)
    die.rotation_euler = (0, math.radians(-4), math.radians(12))
    B._area("BackRim", (-1.0, 4.0, 2.0), (math.radians(-60), 0, math.radians(180)), 3, 900, (0.9, 0.85, 0.8))
    B._area("ChipKey", (3.0, -3.0, 3.0), (0.8, 0, 0.8), 2, 220, (0.85, 0.9, 1.0))
    bpy.ops.mesh.primitive_plane_add(size=6, location=(-1.8, 3.8, 2.6))
    sb = bpy.context.object
    sb.rotation_euler = (Vector((0, 0, 0.8)) - Vector((-1.8, 3.8, 2.6))).to_track_quat("Z", "Y").to_euler()
    sb.data.materials.append(M.soft_emitter("ChipBox", (1, 0.98, 0.95), 4.0))
    sb.visible_camera = False
    styles.tag(sb, "rig")
    B._camera("CamA0_08", [(1, (-0.7, -0.6, 0.55), (1.6, -4.6, 1.8), 85, 2.8),
                           (60, (0.25, -0.4, 0.86), (2.0, -5.0, 2.2), 85, 2.8),
                           (126, (-0.25, 0.0, 0.86), (2.8, -6.8, 3.0), 70, 3.2)])


# ---- A0_10 ---------------------------------------------------------------------------------
def title(sc, rnd):
    C.set_world(top=(0, 0, 0), horizon=(0, 0, 0), bottom=(0, 0, 0))
    before = set(bpy.data.objects)
    path, pmat = BM.machine(with_path=False)
    mods = [o for o in bpy.data.objects if o not in before and o.type == "MESH" and o.parent is None]
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
    {"cargo": cargo, "convoy": convoy, "assemble": assemble, "print": print_, "chip": chip,
     "title": title}[variant](sc, rnd)
    return sc
