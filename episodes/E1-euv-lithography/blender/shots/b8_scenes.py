"""B8 — wafer and reticle stages (F11, F15, F15b, F41, F43b, F44, F51, F57, F58). Variants:

  wafer     B8_01  a patterned wafer turning in the dark, die grid throwing rainbow bands
  slit      B8_02  energy: a wide violet glow is pinched by two blades into a narrow slit on the wafer
  scan      B8_03  clay: reticle stage left, wafer stage right, fixed slit painting fields; step, scan back
            B8_04  clay: speed arrows 4:1, the reticle stage races past
  car       B8_07  photoreal reticle stage; a ghost car drops onto it, shatters into light; stage unmoved
            B8_08  slow side replay: an orange stress ring through the frame stops at the mask edge
  sync      B8_10  xray machine: the two stages sprint in opposite directions, clock ticks flash on alignment
  actuator  B8_14  macro: a row of actuators under a moving stage, indicator lights flickering
  layers    B8_15  clay chip cross-section: patterned layers drop and stack, 0.7 nm offset bar at the seam
  dual      B8_16  xray dual stage: exposing on the left, measuring on the right, swap like a dance
All shapes illustrative.
"""
import math
import random

import bpy
from mathutils import Vector

import build_machine as BM
import common as C
import materials as M
import sample_b1 as B
import styles

FRAMES = 320
VIOLET = (0.62, 0.45, 1.0)
CYAN = (0.2, 0.85, 0.95)
ORANGE = (1.0, 0.42, 0.12)


def _key(ob, f, **kw):
    for k, v in kw.items():
        setattr(ob, k, v)
        ob.keyframe_insert(k, frame=f)


def _linear(ob):
    if ob.animation_data and ob.animation_data.action:
        for fc in C.fcurves(ob.animation_data.action):
            for kp in fc.keyframe_points:
                kp.interpolation = "LINEAR"


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


def _apply_scale(ob):
    """Bake object scale into the mesh so children are not distorted."""
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return ob


def _softbox(name, loc, size, strength, target=(0, 0, 0)):
    bpy.ops.mesh.primitive_plane_add(size=size, location=loc)
    ob = bpy.context.object
    ob.name = name
    ob.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("Z", "Y").to_euler()
    ob.data.materials.append(M.soft_emitter(name + "Mat", (1.0, 0.98, 0.95), strength))
    ob.visible_camera = False
    styles.tag(ob, "rig")
    return ob


def wafer_material(name="WaferDies"):
    """Silicon wafer with a printed die grid: thin-film rainbow bands from the patterned film."""
    m = M.principled(name, (0.32, 0.32, 0.36), metallic=0.6, roughness=0.22, thin_film=520.0, thin_film_ior=2.6)
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    brick = nt.nodes.new("ShaderNodeTexBrick")
    brick.inputs["Scale"].default_value = 7.0
    brick.inputs["Mortar Size"].default_value = 0.025
    brick.inputs["Brick Width"].default_value = 0.5
    brick.inputs["Row Height"].default_value = 0.62
    brick.offset = 0.0
    brick.inputs["Color1"].default_value = (0.34, 0.33, 0.38, 1)
    brick.inputs["Color2"].default_value = (0.3, 0.3, 0.35, 1)
    brick.inputs["Mortar"].default_value = (0.12, 0.12, 0.13, 1)
    nt.links.new(tc.outputs["Object"], brick.inputs["Vector"])
    nt.links.new(brick.outputs["Color"], b.inputs["Base Color"])
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sep.inputs["Vector"])
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = -1.0
    mr.inputs["From Max"].default_value = 1.0
    mr.inputs["To Min"].default_value = 260.0
    mr.inputs["To Max"].default_value = 980.0
    nt.links.new(sep.outputs["Y"], mr.inputs["Value"])
    nt.links.new(mr.outputs["Result"], b.inputs["Thin Film Thickness"])
    return m


def _wafer(name="Wafer", r=1.5, loc=(0, 0, 0), mat=None):
    w = _cyl(name, r, 0.03, loc, mat or wafer_material(), verts=128)
    bpy.ops.mesh.primitive_cube_add(location=(loc[0], loc[1] - r, loc[2]))     # the notch
    n = bpy.context.object
    n.scale = (0.035, 0.05, 0.1)
    n.rotation_euler = (0, 0, math.radians(45))
    n.hide_render = n.hide_viewport = True
    bo = w.modifiers.new("Notch", "BOOLEAN")
    bo.object = n
    bo.operation = "DIFFERENCE"
    n.parent = w
    n.matrix_parent_inverse = w.matrix_world.inverted()
    return w


# ---- B8_01 ---------------------------------------------------------------------------------
def wafer(sc, rnd):
    C.set_world(top=(0.006, 0.007, 0.011), horizon=(0.003, 0.003, 0.005), bottom=(0.0, 0.0, 0.001))
    w = _wafer()
    _key(w, 1, rotation_euler=(0, 0, math.radians(-30)))
    _key(w, 62, rotation_euler=(0, 0, math.radians(-12)))
    _softbox("WaferBox", (-2.7, 5.2, 2.4), 7.0, 4.0)
    _softbox("WaferBox2", (3.0, 4.0, 1.8), 3.0, 2.5)
    B._area("WaferRake", (-4.0, -1.0, 1.2), (math.radians(75), 0, math.radians(-75)), 3, 700, (0.85, 0.9, 1.0))
    B._camera("CamB8_01", [(1, (0.0, -0.9, 0.0), (0.9, -3.2, 0.8), 50, 5.6), (62, (0.0, 0.0, 0.0), (0.2, -3.6, 1.1), 50, 5.6)])


# ---- B8_02 ---------------------------------------------------------------------------------
def slit(sc, rnd):
    _wafer()
    import b7_scenes
    glow = b7_scenes._cone_mat("SlitGlow", 1.0)                     # glassy: brighter edges, see-through
    bpy.ops.mesh.primitive_cube_add(location=(0, 0, 2.0))
    beam = bpy.context.object
    beam.name = "SlitBeam"
    beam.data.materials.append(glow)
    styles.tag(beam, "emitter")
    _key(beam, 1, scale=(1.4, 1.4, 2.0))
    _key(beam, 40, scale=(1.4, 1.4, 2.0))
    _key(beam, 100, scale=(0.06, 0.5, 2.0))                      # narrow across, one field long
    gm = [n for n in glow.node_tree.nodes if n.type == "MATH" and n.operation == "MULTIPLY"][0].inputs[1]
    for f, v in ((1, 0.25), (40, 0.25), (100, 3.0)):
        gm.default_value = v
        gm.keyframe_insert("default_value", frame=f)
    blade = M.dark_anodized("Blade")
    for side in (-1, 1):
        b = _box(f"Blade{side}", (side * 3.0, 0, 3.2), (2.4, 2.0, 0.08), blade)
        _key(b, 30, location=(side * 3.0, 0, 3.2))
        _key(b, 100, location=(side * 1.3, 0, 3.2))
    line = M.emission("SlitOnWafer", (0.85, 0.75, 1.0), 0.0)
    l = _box("SlitLine", (0, 0, 0.02), (0.12, 1.0, 0.004), line, role="emitter")
    M.set_emission_strength(line, 90, 0.0)
    M.set_emission_strength(line, 110, 12.0)
    B._camera("CamB8_02", [(1, (0, 0, 2.6), (0.0, -5.5, 5.2), 35, 11.0), (138, (0, 0, 0.0), (0.0, -3.4, 2.4), 35, 11.0)])


# ---- B8_03 / B8_04 -------------------------------------------------------------------------
def scan(sc, rnd):
    clay = M.principled("ClayStage", (0.7, 0.7, 0.7))
    floor = _box("Floor", (0, 0, -1.6), (60, 60, 0.1), clay)
    ret = _apply_scale(_box("ReticleStage", (0, 0, 2.2), (2.6, 1.6, 0.35), clay, bevel=0.05))
    rk = _box("Reticle", (0, 0, 2.0), (0.6, 0.6, 0.12), clay)
    rk.parent = ret
    rk.location = (0, 0, -0.22)
    ws = _apply_scale(_box("WaferStage", (0, 0, -0.6), (3.2, 3.2, 0.5), clay, bevel=0.06))
    wf = _cyl("WaferDisc", 1.3, 0.04, (0, 0, 0.6), M.principled("WaferClay", (0.8, 0.8, 0.8)), verts=96)
    wf.parent = ws
    wf.location = (0, 0, 0.27)
    for k, (x, y, z, sx, sy, sz) in enumerate(((0, 2.2, -0.2, 7, 0.3, 0.3), (0, -2.2, -0.2, 7, 0.3, 0.3))):
        _box(f"Rail{k}", (x, y, z - 0.7), (sx, sy, sz), clay)
    beam = _box("Slit", (0, 0, 0.8), (0.05, 0.55, 2.5), M.emission("SlitClay", VIOLET, 6.0), role="emitter")
    # exposed fields: strips painted on the wafer as it slides under the fixed slit
    expo = M.emission("Latent", (0.75, 0.6, 1.0), 1.6)
    fields = [(-0.55, 0.0), (0.0, 0.0), (0.55, 0.0)]
    f = 1
    dir_ = 1
    for k, (fx, fy) in enumerate(fields):
        # wafer stage so that this field starts at the slit; it moves +x (dir) over 0.5 units
        x0 = -fx - 0.25 * dir_
        _key(ws, f, location=(x0, 0, -0.6))
        _key(ret, f, location=(-4 * x0, 0, 2.2))
        f1 = f + 38
        _key(ws, f1, location=(x0 + 0.5 * dir_, 0, -0.6))
        _key(ret, f1, location=(-4 * (x0 + 0.5 * dir_), 0, 2.2))
        strip = _box(f"Field{k}", (0, 0, 0), (1.0, 0.5, 0.004), expo, role="emitter")
        strip.parent = wf
        # grow along -dir from the leading edge: scale x 0 -> 0.5 with origin at the field's start edge
        strip.location = (fx + 0.25 * dir_, fy, 0.025)
        strip.scale = (0.0, 0.25, 0.002)
        strip.keyframe_insert("scale", frame=f)
        strip.scale = (0.25, 0.25, 0.002)
        strip.location = (fx, fy, 0.025)
        strip.keyframe_insert("scale", frame=f1)
        strip.keyframe_insert("location", frame=f1)
        strip.location = (fx + 0.25 * dir_, fy, 0.025)
        strip.keyframe_insert("location", frame=f)
        f = f1 + 12                                               # step to the next field
        dir_ = -dir_
    for ob in (ws, ret):
        _linear(ob)
    # B8_04 (161-282): speed arrows 4:1, both stages start together, the reticle stage races off
    _key(ws, 170, location=(0.0, 0, -0.6))
    _key(ret, 170, location=(0.0, 0, 2.2))
    _key(ws, 270, location=(1.0, 0, -0.6))
    _key(ret, 270, location=(-4.0, 0, 2.2))
    for ob in (ws, ret):
        for fc in C.fcurves(ob.animation_data.action):
            for kp in fc.keyframe_points:
                if kp.co[0] >= 170:
                    kp.interpolation = "LINEAR"
    arrows = []
    for name, parent, length, col, z in (("RetArrow", ret, 2.4, ORANGE, 0.45), ("WafArrow", ws, 0.6, CYAN, 0.5)):
        a = _box(name, (0, 0, 0), (length, 0.08, 0.08), M.emission(name + "Mat", col, 5.0), role="emitter")
        a.parent = parent
        a.location = (-length / 2 if name == "RetArrow" else length / 2, 0, z)
        _key(a, 1, hide_render=True)
        _key(a, 165, hide_render=False)
        arrows.append(a)
    sc.render.use_motion_blur = True
    sc.render.motion_blur_shutter = 1.2
    B._area("ClayKey", (5, -6, 8), (0.8, 0, 0.6), 8, 1800, (1.0, 0.98, 0.95))
    B._camera("CamB8_03", [(1, (0, 0, 0.8), (5.2, -6.8, 3.6), 35, 8.0), (154, (0, 0, 0.8), (4.6, -7.2, 3.4), 35, 8.0)])
    B._camera("CamB8_04", [(161, (0, 0, 1.2), (2.0, -7.0, 2.4), 35, 8.0), (282, (-2.4, 0, 1.2), (-0.6, -7.4, 2.4), 35, 8.0)])


# ---- B8_07 / B8_08 -------------------------------------------------------------------------
def _ghost_car(mat_glass, mat_wire):
    parts = []
    body = _box("CarBody", (0, 0, 0.35), (4.3, 1.8, 0.7), mat_glass, role="emitter", bevel=0.18)
    cabin = _box("CarCabin", (-0.2, 0, 0.95), (2.3, 1.6, 0.6), mat_glass, role="emitter", bevel=0.2)
    parts += [body, cabin]
    for sx in (-1.35, 1.35):
        for sy in (-0.85, 0.85):
            parts.append(_cyl(f"Wheel{sx}{sy}", 0.36, 0.25, (sx, sy, 0.15), mat_glass, rot=(math.pi / 2, 0, 0),
                              role="emitter", verts=24))
    for p in list(parts):                                          # wireframe twin on every part
        w = p.copy()
        w.data = p.data.copy()
        bpy.context.scene.collection.objects.link(w)
        w.modifiers.new("Wire", "WIREFRAME").thickness = 0.015
        w.data.materials.clear()
        w.data.materials.append(mat_wire)
        styles.tag(w, "emitter")
        parts.append(w)
    bpy.ops.object.empty_add(location=(0, 0, 0))
    root = bpy.context.object
    root.name = "GhostCar"
    for p in parts:
        p.parent = root
    return root, parts


def car(sc, rnd):
    import b6_scenes
    C.set_world(top=(0.006, 0.007, 0.011), horizon=(0.003, 0.003, 0.005), bottom=(0.0, 0.0, 0.001))
    dark = M.dark_anodized("StageDark")
    steel = M.polished_steel("StageSteel", 0.22)
    stage = _box("ReticleStage", (0, 0, 0), (5.0, 3.6, 0.6), dark, bevel=0.06)
    for y in (-2.1, 2.1):
        _box(f"Rail{y}", (0, y, -0.25), (9.0, 0.35, 0.3), steel, bevel=0.03)
    chuck = _box("Chuck", (0, 0, 0.36), (2.0, 2.0, 0.12), steel, bevel=0.02)
    mask = b6_scenes._mask(loc=(0, 0, 0.5), size=1.52)
    glass = bpy.data.materials.new("GhostGlass")
    glass.use_nodes = True
    nt = glass.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    lw = nt.nodes.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.2
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (0.55, 0.75, 1.0, 1)
    mul = nt.nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    mul.inputs[1].default_value = 1.2
    nt.links.new(lw.outputs["Facing"], mul.inputs[0])
    nt.links.new(mul.outputs[0], em.inputs["Strength"])
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    add = nt.nodes.new("ShaderNodeAddShader")
    nt.links.new(tr.outputs[0], add.inputs[0])
    nt.links.new(em.outputs[0], add.inputs[1])
    nt.links.new(add.outputs[0], out.inputs["Surface"])
    glass.surface_render_method = "BLENDED"
    wire = M.emission("GhostWire", (0.6, 0.8, 1.0), 2.5)
    root, parts = _ghost_car(glass, wire)
    # fall, impact at 120 (slowed around it), squash, then vanish into light points
    _key(root, 1, location=(0.0, 0.0, 9.0), scale=(1, 1, 1))
    _key(root, 104, location=(0.0, 0.0, 9.0), scale=(1, 1, 1))
    _key(root, 118, location=(0.0, 0.0, 0.6), scale=(1, 1, 1))
    _key(root, 140, location=(0.0, 0.0, 0.6), scale=(1.12, 1.12, 0.45))
    _key(root, 141, hide_render=False)
    for p in parts:
        _key(p, 150, hide_render=False)
        _key(p, 152, hide_render=True)
    dot = M.emission("Shard", (0.65, 0.85, 1.0), 6.0)
    for k in range(160):                                           # shards of light
        d = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(0.0, 0.8))).normalized()
        start = Vector((rnd.uniform(-2, 2), rnd.uniform(-0.9, 0.9), 0.6 + rnd.uniform(0, 0.9)))
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.02, location=tuple(start))
        s = bpy.context.object
        s.data.materials.append(dot)
        styles.tag(s, "emitter")
        _key(s, 1, hide_render=True)
        _key(s, 150, hide_render=False, location=tuple(start))
        _key(s, 205, location=tuple(start + d * rnd.uniform(1.5, 4.0)))
        _key(s, 206, hide_render=True)
    ring_m = M.emission("ImpactRing", (0.7, 0.85, 1.0), 0.0)
    bpy.ops.mesh.primitive_torus_add(major_radius=1.0, minor_radius=0.02, location=(0, 0, 0.62))
    ring = bpy.context.object
    ring.data.materials.append(ring_m)
    styles.tag(ring, "emitter")
    _key(ring, 118, scale=(0.3, 0.3, 1))
    _key(ring, 150, scale=(2.6, 2.6, 1))
    M.set_emission_strength(ring_m, 117, 0.0)
    M.set_emission_strength(ring_m, 119, 8.0)
    M.set_emission_strength(ring_m, 150, 0.0)
    # B8_08 (230-314): orange stress ring through the stage frame, dying at the mask edge; car frozen foreground
    st_m = M.emission("StressRing", ORANGE, 0.0)
    bpy.ops.mesh.primitive_torus_add(major_radius=1.0, minor_radius=0.05, location=(0, 0, 0.31))
    sr = bpy.context.object
    sr.data.materials.append(st_m)
    styles.tag(sr, "emitter")
    _key(sr, 232, scale=(2.4, 2.4, 1))
    _key(sr, 300, scale=(0.78, 0.78, 1))
    M.set_emission_strength(st_m, 231, 0.0)
    M.set_emission_strength(st_m, 236, 7.0)
    M.set_emission_strength(st_m, 296, 3.0)
    M.set_emission_strength(st_m, 302, 0.0)
    for p in parts:
        _key(p, 229, hide_render=True)
        _key(p, 230, hide_render=False)
    _key(root, 229, location=(0.0, 0.0, 0.6), scale=(1.12, 1.12, 0.45))
    _key(root, 230, location=(-4.2, -1.6, 0.8), scale=(1.12, 1.12, 0.45))
    _softbox("StageBox", (-3, 5, 5), 6, 2.5)
    B._area("StageKey", (4, -5, 6), (0.8, 0, 0.6), 4, 1100, (0.85, 0.9, 1.0))
    B._camera("CamB8_07", [(1, (0, 0, 2.4), (0.6, -9.0, 0.3), 24, 5.6), (223, (0, 0, 2.0), (1.2, -8.6, 0.4), 24, 5.6)])
    B._camera("CamB8_08", [(230, (0.0, 0.0, 0.52), (-2.6, -4.2, 1.2), 85, 2.0), (314, (0.1, 0.0, 0.52), (-2.4, -4.3, 1.15), 85, 2.0)],
              focus=mask)


# ---- B8_10 ---------------------------------------------------------------------------------
def sync(sc, rnd):
    path, pmat = BM.machine()
    rs = bpy.data.objects["ReticleStage"]
    rt = bpy.data.objects["Reticle"]
    ws = bpy.data.objects["WaferStage"]
    wf = bpy.data.objects["Wafer"]
    tick = M.emission("Tick", CYAN, 1.0)
    ticks = []
    for ob, dz in ((rs, 0.3), (ws, -0.35)):
        bpy.ops.mesh.primitive_torus_add(major_radius=0.09, minor_radius=0.01,
                                         location=(ob.location.x + 1.0, -0.95, ob.location.z + dz))
        t = bpy.context.object
        t.rotation_euler = (math.pi / 2, 0, 0)
        t.data.materials.append(tick)
        styles.tag(t, "emitter")
        t.parent = ob
        t.matrix_parent_inverse = ob.matrix_world.inverted()
        ticks.append(t)
    base = {o.name: o.location.copy() for o in (rs, rt, ws, wf)}
    for k, f in enumerate(range(1, 109, 18)):
        s = 1 if k % 2 == 0 else -1
        for o, amp in ((rs, 0.8), (rt, 0.8), (ws, -0.2), (wf, -0.2)):
            loc = base[o.name].copy()
            loc.x += s * amp
            _key(o, f, location=tuple(loc))
        M.set_emission_strength(tick, f, 30.0)
        M.set_emission_strength(tick, f + 3, 1.0)
    B._area("MKey", (0, -9, 8), (0.9, 0, 0), 16, 2500, (0.8, 0.85, 1.0))
    B._camera("CamB8_10", [(1, (0.5, 0, 0.7), (0.9, -3.2, 0.8), 35, 5.6), (108, (0.5, 0, 0.7), (1.6, -8.8, 1.4), 35, 5.6)])


# ---- B8_14 ---------------------------------------------------------------------------------
def actuator(sc, rnd):
    C.set_world(top=(0.01, 0.012, 0.018), horizon=(0.005, 0.006, 0.009), bottom=(0.001, 0.001, 0.002))
    steel = M.polished_steel("ActSteel", 0.25)
    dark = M.dark_anodized("ActDark")
    plate = _box("StagePlate", (0, 0, 0.8), (14, 3.0, 0.3), steel, bevel=0.03)
    _key(plate, 1, location=(0, 0, 0.8))
    _key(plate, 150, location=(-1.6, 0, 0.8))
    leds = []
    for k in range(22):
        x = -7 + k * 0.65
        act = _box(f"Act{k}", (x, 0, 0.3), (0.45, 0.8, 0.6), dark, bevel=0.03)
        for j in range(2):
            m = M.emission(f"LED{k}_{j}", CYAN, 0.0)
            _box(f"LEDob{k}_{j}", (x - 0.1 + 0.2 * j, -0.41, 0.42), (0.06, 0.01, 0.04), m, role="emitter")
            leds.append(m)
    for m in leds:                                                 # flicker faster than the eye
        s = m.node_tree.nodes["Emission"].inputs["Strength"]
        for f in range(1, 151, 2):
            s.default_value = rnd.choice((0.3, 2.0, 6.0, 9.0))
            s.keyframe_insert("default_value", frame=f)
    sc.render.use_motion_blur = True
    sc.render.motion_blur_shutter = 0.8
    _softbox("ActBox", (0, -5, 4), 8, 2.0)
    B._area("ActKey", (-3, -4, 3), (1.0, 0, -0.6), 3, 300, (0.85, 0.9, 1.0))
    B._camera("CamB8_14", [(1, (-1.0, -0.4, 0.5), (-2.6, -2.6, 0.6), 50, 2.0), (150, (-0.2, -0.4, 0.5), (-1.8, -2.6, 0.62), 50, 2.0)])


# ---- B8_15 ---------------------------------------------------------------------------------
def layers(sc, rnd):
    clay = M.principled("ClayLayer", (0.7, 0.7, 0.7))
    _box("Floor", (0, 0, -0.05), (40, 40, 0.1), clay)
    n = 8
    for k in range(n):
        z = 0.12 + k * 0.22
        lay = _apply_scale(_box(f"Layer{k}", (0, 0, z), (3.2, 2.2, 0.2), clay, bevel=0.01))
        # each layer carries its own line pattern: grooves via an array of thin boxes in a recessed tone
        for g in range(6 + (k % 3) * 3):
            gx = -1.4 + g * (2.8 / (5 + (k % 3) * 3))
            gr = _box(f"Groove{k}_{g}", (0, 0, 0), (0.06 if k % 2 else 2.8, 2.0 if k % 2 else 0.06, 0.03), clay)
            gr.parent = lay
            gr.location = (gx if k % 2 else 0, 0 if k % 2 else -0.9 + g * (1.8 / (5 + (k % 3) * 3)), 0.11)
        f0 = 4 + 12 * k
        _key(lay, f0, location=(0, 0, z + 3.5))
        _key(lay, f0 + 12, location=(0, 0, z))
        if k == n - 1:                                            # the last one lands 0.7 nm "off" (bar marks it)
            _key(lay, f0 + 12, location=(0.0, 0, z))
    bar = _box("OffsetBar", (1.6, -1.12, 0.12 + (n - 1) * 0.22 - 0.1), (0.004, 0.01, 0.06),
               M.emission("BarCyan", CYAN, 6.0), role="emitter")
    _key(bar, 1, hide_render=True)
    _key(bar, 110, hide_render=False)
    B._area("ClayKey", (5, -6, 8), (0.8, 0, 0.6), 8, 1800, (1.0, 0.98, 0.95))
    B._camera("CamB8_15", [(1, (0, 0, 1.2), (6.0, -7.0, 4.0), 40, 8.0), (100, (0.6, -0.6, 1.3), (4.4, -5.6, 2.4), 40, 8.0),
                           (183, (1.6, -1.1, 1.56), (2.2, -1.9, 1.62), 85, 4.0)])


# ---- B8_16 ---------------------------------------------------------------------------------
def dual(sc, rnd):
    C.set_world(top=(0.9, 0.91, 0.93), horizon=(0.78, 0.79, 0.82), bottom=(0.6, 0.61, 0.64))
    base = _box("DualBase", (0, 0, -0.5), (9, 4.5, 0.8), M.principled("BasePanel", (0.78, 0.8, 0.82), metallic=0.2,
                                                                     roughness=0.45), role="shell", bevel=0.15)
    steel = M.polished_steel("DualSteel", 0.25)
    stages = []
    for k, x in enumerate((-2.2, 2.2)):
        st = _box(f"Stage{k}", (x, 0, 0.1), (2.4, 2.4, 0.35), steel, bevel=0.04)
        w = _wafer(f"DualWafer{k}", r=0.95, loc=(x, 0, 0.3))
        w.parent = st
        w.matrix_parent_inverse = st.matrix_world.inverted()
        stages.append(st)
    # exposure slit (left) and metrology dot grid (right) stay in place
    _box("ExpSlit", (-2.2, 0, 1.6), (0.05, 0.9, 2.6), M.emission("ExpSlitMat", VIOLET, 6.0), role="rays")
    dots = M.emission("MetroDots", CYAN, 6.0)
    grid = []
    for i in range(6):
        for j in range(6):
            bpy.ops.mesh.primitive_uv_sphere_add(radius=0.025, location=(2.2 - 0.5 + 0.2 * i, -0.5 + 0.2 * j, 0.36))
            d = bpy.context.object
            d.data.materials.append(dots)
            styles.tag(d, "rays")
            grid.append(d)
    a, b_ = stages
    # scan wiggles at each station, then the swap (arcs around each other), then work again
    for st, x0 in ((a, -2.2), (b_, 2.2)):
        for f, dx in ((1, -0.4), (20, 0.4), (40, -0.4), (60, 0.4), (72, 0.0)):
            _key(st, f, location=(x0 + dx, 0, 0.1))
    _key(a, 96, location=(0.0, -1.0, 0.1))
    _key(b_, 96, location=(0.0, 1.0, 0.1))
    _key(a, 120, location=(2.2, 0, 0.1))
    _key(b_, 120, location=(-2.2, 0, 0.1))
    for st, x0 in ((a, 2.2), (b_, -2.2)):
        for f, dx in ((140, -0.4), (160, 0.4), (180, -0.4)):
            _key(st, f, location=(x0 + dx, 0, 0.1))
    B._area("DualKey", (0, -9, 8), (0.9, 0, 0), 16, 2500, (0.8, 0.85, 1.0))
    B._camera("CamB8_16", [(1, (0, 0, 0.2), (-5.0, -8.0, 7.0), 35, 8.0), (180, (0, 0, 0.2), (0.5, -9.4, 7.0), 35, 8.0)])


def build(variant="wafer", seed=81):
    sc = C.reset_scene(FRAMES)
    C.set_world(top=(0.03, 0.035, 0.05), horizon=(0.012, 0.014, 0.02), bottom=(0.003, 0.004, 0.006))
    C.set_color_management(exposure=0.4)
    rnd = random.Random(seed)
    {"wafer": wafer, "slit": slit, "scan": scan, "car": car, "sync": sync, "actuator": actuator,
     "layers": layers, "dual": dual}[variant](sc, rnd)
    return sc
