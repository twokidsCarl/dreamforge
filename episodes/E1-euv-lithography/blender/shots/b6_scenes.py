"""B6 — the reflective mask and its pellicle (F14, F35–F37). Variants:

  mask      B6_01  the mask turning into frame in a dark holder; the pattern throws diffraction colours
  section   B6_02  dive into the mask edge: the B4_02 Mo/Si cross-section plus a row of absorber blocks
            B6_03  energy: violet light reflects off bare multilayer, dies on the absorber blocks
  dust      B6_08  a dust grain drifting down through a slanted beam above a defocused mask
  robot     B6_10  clay reticle-handling robot: pick, move, place, faster each cycle
  pellicle  B6_12  xray: frame and near-invisible membrane above the mask, iridescent at grazing angles
            B6_13  the membrane glowing dull red under EUV pulses, violet hydrogen-plasma rim
            B6_14  grazing close-up of the hot membrane, interference bands flowing
  down      B6_17  xray machine: patterned violet light from the reticle down into the projection optics
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


def _beam(name, a, b, radius, mat, role="emitter"):
    a, b = Vector(a), Vector(b)
    d = b - a
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=d.length, vertices=24, location=(a + b) / 2)
    ob = bpy.context.object
    ob.name = name
    ob.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    ob.data.materials.append(mat)
    styles.tag(ob, role)
    return ob


def mask_material(name="MaskPattern"):
    """Mo/Si blank with a dark absorber circuit pattern; grating-like thin-film bands give the
    rainbow sheen a patterned mask throws under raking light (artistic cue)."""
    m = M.principled(name, (0.6, 0.6, 0.64), metallic=1.0, roughness=0.06, thin_film=500.0, thin_film_ior=2.8)
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    brick = nt.nodes.new("ShaderNodeTexBrick")              # die fields
    brick.inputs["Scale"].default_value = 3.0
    brick.inputs["Mortar Size"].default_value = 0.03
    brick.inputs["Brick Width"].default_value = 0.5
    brick.inputs["Row Height"].default_value = 0.5
    brick.offset = 0.0
    lines = nt.nodes.new("ShaderNodeTexWave")               # dense circuit lines inside each die
    lines.inputs["Scale"].default_value = 48.0
    lines.inputs["Distortion"].default_value = 3.0
    lines.inputs["Detail"].default_value = 2.0
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 24.0
    mixm = nt.nodes.new("ShaderNodeMath")
    mixm.operation = "MULTIPLY"
    nt.links.new(tc.outputs["Object"], brick.inputs["Vector"])
    nt.links.new(tc.outputs["Object"], lines.inputs["Vector"])
    nt.links.new(tc.outputs["Object"], noise.inputs["Vector"])
    lr = nt.nodes.new("ShaderNodeMath")                      # lines -> 0/1 stripes
    lr.operation = "GREATER_THAN"
    lr.inputs[1].default_value = 0.45
    nt.links.new(lines.outputs["Fac"], lr.inputs[0])
    nt.links.new(lr.outputs[0], mixm.inputs[0])
    nt.links.new(brick.outputs["Fac"], mixm.inputs[1])       # mortar (die streets) stays bare
    inv = nt.nodes.new("ShaderNodeMath")
    inv.operation = "SUBTRACT"
    inv.inputs[0].default_value = 1.0
    nt.links.new(mixm.outputs[0], inv.inputs[1])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.45
    ramp.color_ramp.elements[1].position = 0.55
    nt.links.new(inv.outputs[0], ramp.inputs["Fac"])
    col = nt.nodes.new("ShaderNodeMix")
    col.data_type = "RGBA"
    col.inputs["A"].default_value = (0.04, 0.045, 0.05, 1)            # absorber
    col.inputs["B"].default_value = (0.62, 0.6, 0.66, 1)              # multilayer
    nt.links.new(ramp.outputs["Color"], col.inputs["Factor"])
    nt.links.new(col.outputs["Result"], b.inputs["Base Color"])
    # thin-film thickness swept along X: rainbow bands that slide as the mask turns
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sep.inputs["Vector"])
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = -1.0
    mr.inputs["From Max"].default_value = 1.0
    mr.inputs["To Min"].default_value = 250.0
    mr.inputs["To Max"].default_value = 1100.0
    nt.links.new(sep.outputs["X"], mr.inputs["Value"])
    nt.links.new(mr.outputs["Result"], b.inputs["Thin Film Thickness"])
    rough = nt.nodes.new("ShaderNodeMapRange")
    rough.inputs["To Min"].default_value = 0.05
    rough.inputs["To Max"].default_value = 0.2
    nt.links.new(ramp.outputs["Color"], rough.inputs["Value"])
    return m


def _mask(loc=(0, 0, 0), size=3.0):
    """6-inch mask, scaled: a square plate with the pattern area on top; returns the plate."""
    plate = _box("Mask", loc, (size, size, size * 0.042), M.principled("MaskSub", (0.12, 0.12, 0.13), roughness=0.2),
                 bevel=0.01)
    bpy.ops.mesh.primitive_plane_add(size=size * 0.8, location=(loc[0], loc[1], loc[2] + size * 0.0215))
    pat = bpy.context.object
    pat.name = "MaskPatternArea"
    pat.data.materials.append(mask_material())
    styles.tag(pat, "structure")
    pat.parent = plate
    pat.matrix_parent_inverse = plate.matrix_world.inverted()
    return plate


def _softbox(name, loc, size, strength, target=(0, 0, 0)):
    """Camera-invisible emissive card: shows up only in reflections."""
    bpy.ops.mesh.primitive_plane_add(size=size, location=loc)
    ob = bpy.context.object
    ob.name = name
    ob.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("Z", "Y").to_euler()
    ob.data.materials.append(M.soft_emitter(name + "Mat", (1.0, 0.98, 0.95), strength))
    ob.visible_camera = False
    styles.tag(ob, "rig")
    return ob


# ---- B6_01 ---------------------------------------------------------------------------------
def mask(sc, rnd):
    C.set_world(top=(0.012, 0.014, 0.02), horizon=(0.006, 0.007, 0.01), bottom=(0.001, 0.001, 0.002))
    holder = M.dark_anodized("Holder")
    plate = _mask()
    for sx in (-1, 1):
        for sy in (-1, 1):
            _box(f"Pin{sx}{sy}", (sx * 1.35, sy * 1.35, -0.12), (0.18, 0.18, 0.18), holder, bevel=0.02).parent = plate
    _box("Cradle", (0, 0, -0.3), (3.6, 3.6, 0.12), holder, bevel=0.03).parent = plate
    _key(plate, 1, rotation_euler=(math.radians(4), 0, math.radians(-38)), location=(0.6, 0, 0))
    _key(plate, 128, rotation_euler=(math.radians(-2), 0, math.radians(-14)), location=(0, 0, 0))
    _softbox("Mirrorbox", (2.6, 7.0, 2.2), 11.0, 7.0)              # the mask mirrors this to the camera
    B._area("Top", (2, -3, 6), (0.4, 0, 0.5), 4, 150, (0.75, 0.82, 1.0))
    B._camera("CamB6_01", [(1, (0, 0, 0), (-2.4, -6.6, 2.2), 50, 4.0), (128, (0.3, 0, 0), (0.4, -7.0, 2.0), 50, 4.0)])


# ---- B6_02 / B6_03 -------------------------------------------------------------------------
def section(sc, rnd):
    import b2_scenes
    b2_scenes.multilayer(sc, n_pairs=20, t=0.11)                 # identical to B4_02
    ab = M.principled("Absorber", (0.05, 0.05, 0.05), roughness=0.6)
    xs = [-2.4, -1.2, 0.0, 1.2, 2.4]
    for k, x in enumerate(xs):
        blk = _box(f"Absorber{k}", (x, 0, 0.26), (0.6, 2.0, 0.52), ab)
        blk["sem_tone"] = 0.2
        blk.hide_render = True                                     # appears during B6_02's dive
        _key(blk, 1, hide_render=True)
        _key(blk, 60, hide_render=False)
    # B6_03 light: beams come down at a slight angle; bare gaps reflect, absorber tops swallow
    inc = M.emission("Incident", VIOLET, 2.6)
    ref = M.emission("Reflected", VIOLET, 0.0)
    ang = math.radians(6)
    for k in range(11):
        x = -3.0 + 0.6 * k
        on_absorber = any(abs(x - xa) < 0.31 for xa in xs)
        z_hit = 0.52 if on_absorber else 0.0
        top = Vector((x - 6.0 * math.tan(ang), 0, 6.0))
        hit = Vector((x, 0, z_hit))
        b_in = _beam(f"In{k}", top, hit, 0.03, inc, role="rays")
        b_in.hide_render = True
        _key(b_in, 1, hide_render=True)
        _key(b_in, 300 - 120 + 10 + k, hide_render=False)          # B6_03 starts at frame 181
        if not on_absorber:
            out = Vector((x + 6.0 * math.tan(ang), 0, 6.0))
            b_out = _beam(f"Out{k}", hit, out, 0.04, ref, role="rays")
    M.set_emission_strength(ref, 200, 0.0)
    M.set_emission_strength(ref, 215, 4.5)
    # B6_02 ends exactly on B4_02's last frame
    B._camera("CamB6_02", [(1, (0, 0, 0.2), (0.0, -14.0, 6.0), 100, 11.0),
                           (128, (0, 0, -2.2), (0.0, -7.5, -1.2), 100, 11.0)])
    B._camera("CamB6_03", [(181, (0, 0, -1.0), (0.0, -8.5, -0.6), 100, 11.0),
                           (300, (0, 0, 1.4), (0.0, -19.0, 2.4), 100, 11.0)])


def after_style(style, shot_id):
    import b2_scenes
    b2_scenes.after_style(style, shot_id)
    if shot_id == "B6_12":                     # the quiet look: no pulses, no plasma yet
        for name in ("PulseIn", "PulseOut", "H2RimVol"):
            ob = bpy.data.objects.get(name)
            if ob:
                ob.hide_render = True
    if shot_id in ("B6_13", "B6_14"):
        mem = bpy.data.objects.get("Membrane")
        if mem:
            mem.data.materials.clear()
            mem.data.materials.append(hot_membrane())


# ---- B6_08 ---------------------------------------------------------------------------------
def dust(sc, rnd):
    C.set_world(top=(0.004, 0.005, 0.008), horizon=(0.002, 0.002, 0.004), bottom=(0.0, 0.0, 0.001))
    _mask(loc=(0, 0, -1.4), size=3.0)
    # slanted light shaft (emissive, faint) and the grain
    shaft = M.volume_glow("Shaft", (0.75, 0.7, 1.0), 0.004, 0.07)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.28, depth=8.0, vertices=48, location=(0, 0, 0.6),
                                        rotation=(0, math.radians(28), 0))
    sh = bpy.context.object
    sh.data.materials.append(shaft)
    styles.tag(sh, "emitter")
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=0.018, location=(0.1, 0, 0.5))
    g = bpy.context.object
    g.name = "Grain"
    g.scale = (1.0, 0.7, 1.3)
    sparkle = M.principled("GrainMat", (0.8, 0.78, 0.72), roughness=0.3, emission=(1, 0.95, 0.9), emission_strength=0.5)
    g.data.materials.append(sparkle)
    styles.tag(g, "structure")
    mote = M.emission("Mote", (1.0, 0.96, 0.9), 1.2)
    for k in range(40):                                    # out-of-focus motes give the shaft depth
        t = rnd.uniform(-1.5, 1.5)
        c = Vector((0, 0, 0.6)) + Vector((math.sin(math.radians(28)), 0, math.cos(math.radians(28)))) * t
        c += Vector((rnd.uniform(-0.2, 0.2), rnd.uniform(-0.6, 0.6), rnd.uniform(-0.2, 0.2)))
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.005, location=tuple(c))
        mo = bpy.context.object
        mo.data.materials.append(mote)
        styles.tag(mo, "emitter")
        _key(mo, 1, location=tuple(c))
        _key(mo, 58, location=tuple(c + Vector((rnd.uniform(-0.02, 0.02), 0, -rnd.uniform(0.04, 0.1)))))
    _key(g, 1, location=(0.1, 0, 0.5), rotation_euler=(0, 0, 0))
    _key(g, 58, location=(0.02, 0, 0.18), rotation_euler=(1.4, 0.6, 2.0))
    em = sparkle.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
    for f in range(1, 60, 4):
        em.default_value = 0.2 + 1.4 * rnd.random()
        em.keyframe_insert("default_value", frame=f)
    spot = bpy.data.lights.new("ShaftLight", "SPOT")
    spot.energy = 400
    spot.spot_size = math.radians(16)
    so = bpy.data.objects.new("ShaftLight", spot)
    sc.collection.objects.link(so)
    so.location = (-1.9, 0, 4.1)
    so.rotation_euler = (0, math.radians(-28), 0)
    B._camera("CamB6_08", [(1, (0.08, 0, 0.42), (0.6, -1.9, 0.6), 100, 2.0), (58, (0.03, 0, 0.2), (0.55, -1.9, 0.4), 100, 2.0)])


# ---- B6_10 ---------------------------------------------------------------------------------
def robot(sc, rnd):
    mat = M.principled("Robot", (0.7, 0.7, 0.7))
    floor = _box("Floor", (0, 0, -0.05), (40, 40, 0.1), mat)
    floor["clay_floor"] = True
    base = _box("RBase", (0, 0, 0.4), (0.9, 0.9, 0.8), mat, bevel=0.06)
    bpy.ops.object.empty_add(location=(0, 0, 0.85))
    yaw = bpy.context.object
    yaw.name = "Yaw"
    tower = _box("Tower", (0, 0, 0.35), (0.5, 0.5, 0.7), mat, bevel=0.05)
    tower.parent = yaw
    tower.location = (0, 0, 0.35)
    bpy.ops.object.empty_add(location=(0, 0, 0))
    sh = bpy.context.object
    sh.name = "Shoulder"
    sh.parent = yaw
    sh.location = (0, 0, 0.7)
    l1 = _box("Link1", (0, 0, 0), (1.6, 0.3, 0.26), mat, bevel=0.06)
    l1.parent = sh
    l1.location = (0.8, 0, 0)
    bpy.ops.object.empty_add(location=(0, 0, 0))
    el = bpy.context.object
    el.name = "Elbow"
    el.parent = sh
    el.location = (1.6, 0, 0)
    l2 = _box("Link2", (0, 0, 0), (1.4, 0.24, 0.2), mat, bevel=0.05)
    l2.parent = el
    l2.location = (0.7, 0, -0.05)
    fork = _box("Fork", (0, 0, 0), (0.9, 0.9, 0.04), mat, bevel=0.01)
    fork.parent = el
    fork.location = (1.75, 0, -0.12)
    reticle = _box("Reticle", (0, 0, 0), (0.62, 0.62, 0.04), M.principled("RetClay", (0.75, 0.75, 0.75)), bevel=0.005)
    reticle.parent = fork
    reticle.location = (0, 0, 0.045)
    for k, (x, y) in enumerate(((3.35, 0.0), (0.0, 3.35))):          # pick-up and put-down pedestals
        _box(f"Pedestal{k}", (x, y, 0.585), (0.8, 0.8, 1.17), mat, bevel=0.04)
    # pick at +X pedestal, place at +Y pedestal; cycles get shorter (60, 40, 26, 18, 14 frames)
    f = 1
    poses = [(0.0, 0.0, 0.0), (math.radians(90), 0.0, 0.0)]
    for k, n in enumerate((44, 30, 22, 16, 12, 10)):
        a, b_ = poses[k % 2], poses[(k + 1) % 2]
        _key(yaw, f, rotation_euler=(0, 0, a[0]))
        _key(sh, f, rotation_euler=(0, math.radians(8), 0))
        _key(el, f, rotation_euler=(0, math.radians(-8), 0))
        _key(sh, f + n // 4, rotation_euler=(0, math.radians(-6), 0))         # lift
        _key(el, f + n // 4, rotation_euler=(0, math.radians(6), 0))
        _key(yaw, f + 3 * n // 4, rotation_euler=(0, 0, b_[0]))
        _key(sh, f + n, rotation_euler=(0, math.radians(8), 0))               # lower
        _key(el, f + n, rotation_euler=(0, math.radians(-8), 0))
        f += n + 2
    sc.render.use_motion_blur = True
    sc.render.motion_blur_shutter = 1.6
    B._area("ClayKey", (5, -6, 7), (0.9, 0, 0.6), 8, 1800, (1.0, 0.98, 0.95))
    B._camera("CamB6_10", [(1, (1.4, 1.4, 1.0), (6.8, -4.4, 2.8), 30, 8.0),
                           (147, (1.4, 1.4, 1.0), (7.6, -1.4, 3.0), 30, 8.0)])


# ---- B6_12 / B6_13 / B6_14 -----------------------------------------------------------------
def hot_membrane():
    """Dull red heat glow (blackbody) mottled by noise; thin-film sheen on top."""
    m = M.principled("HotMembrane", (0.5, 0.5, 0.52), metallic=0.0, roughness=0.15, thin_film=380.0,
                     thin_film_ior=1.8)
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Alpha"].default_value = 0.55
    bb = nt.nodes.new("ShaderNodeBlackbody")
    bb.inputs["Temperature"].default_value = 1050.0
    nt.links.new(bb.outputs["Color"], b.inputs["Emission Color"])
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 3.0
    w = nt.nodes.new("ShaderNodeValue")                           # drifting bands
    w.outputs[0].default_value = 0.0
    w.outputs[0].keyframe_insert("default_value", frame=1)
    w.outputs[0].default_value = 3.0
    w.outputs[0].keyframe_insert("default_value", frame=300)
    noise.noise_dimensions = "4D"
    nt.links.new(w.outputs[0], noise.inputs["W"])
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["To Min"].default_value = 0.15
    mr.inputs["To Max"].default_value = 0.9
    nt.links.new(noise.outputs["Fac"], mr.inputs["Value"])
    ramp_t = nt.nodes.new("ShaderNodeValue")                       # heats up over the shot
    ramp_t.outputs[0].default_value = 0.0
    ramp_t.outputs[0].keyframe_insert("default_value", frame=1)
    ramp_t.outputs[0].default_value = 1.0
    ramp_t.outputs[0].keyframe_insert("default_value", frame=80)
    mul = nt.nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    nt.links.new(mr.outputs["Result"], mul.inputs[0])
    nt.links.new(ramp_t.outputs[0], mul.inputs[1])
    nt.links.new(mul.outputs[0], b.inputs["Emission Strength"])
    tf = nt.nodes.new("ShaderNodeMapRange")
    tf.inputs["To Min"].default_value = 250.0
    tf.inputs["To Max"].default_value = 700.0
    nt.links.new(noise.outputs["Fac"], tf.inputs["Value"])
    nt.links.new(tf.outputs["Result"], b.inputs["Thin Film Thickness"])
    return m


def pellicle(sc, rnd):
    C.set_world(top=(0.006, 0.007, 0.011), horizon=(0.003, 0.003, 0.005), bottom=(0.0, 0.0, 0.001))
    _mask(loc=(0, 0, 0), size=3.0)
    frame_mat = M.polished_steel("PelFrame", 0.25)
    w, h, t = 2.6, 0.2, 0.08
    for (x, y, sx, sy) in ((0, w / 2, w, t), (0, -w / 2, w, t), (w / 2, 0, t, w), (-w / 2, 0, t, w)):
        _box(f"PelFrame{x}{y}", (x, y, 0.06 + h / 2), (sx, sy, h), frame_mat, bevel=0.01)
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=60, y_subdivisions=60, size=w - 0.04, location=(0, 0, 0.06 + h))
    mem = bpy.context.object
    mem.name = "Membrane"
    film = M.principled("PellicleFilm", (0.9, 0.9, 0.92), roughness=0.02, thin_film=420.0, thin_film_ior=1.9)
    fb = film.node_tree.nodes["Principled BSDF"]
    fb.inputs["Transmission Weight"].default_value = 1.0
    fb.inputs["IOR"].default_value = 1.02
    mem.data.materials.append(film)
    styles.tag(mem, "structure")
    wob = mem.modifiers.new("Flutter", "WAVE")                       # faint billow
    wob.height = 0.006
    wob.width = 1.2
    wob.speed = 0.01
    # B6_13: EUV pulses through the membrane (down to the mask, back up)
    pulse = M.emission("PelPulse", VIOLET, 0.0)
    beams = [_beam("PulseIn", (-1.2, 0, 3.0), (0, 0, 0.03), 0.18, pulse),
             _beam("PulseOut", (0, 0, 0.03), (1.2, 0, 3.0), 0.18, pulse)]
    for k in range(8):
        f0 = 4 + 12 * k
        for bo in beams:
            _key(bo, f0, hide_render=False)
            _key(bo, f0 + 6, hide_render=True)
        if k == 0:
            for bo in beams:
                _key(bo, 1, hide_render=True)
        M.set_emission_strength(pulse, f0, 0.0)
        M.set_emission_strength(pulse, f0 + 1, 7.0)
        M.set_emission_strength(pulse, f0 + 5, 0.0)
    # violet hydrogen-plasma rim hugging the membrane (echoes B2)
    rim = M.volume_glow("H2Rim", (0.55, 0.4, 1.0), 0.15, 1.2, noise_scale=6.0)
    bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0.06 + h + 0.03))
    rv = bpy.context.object
    rv.name = "H2RimVol"
    rv.scale = (w / 2, w / 2, 0.03)
    rv.data.materials.append(rim)
    styles.tag(rv, "emitter")
    B._area("PelKey", (-4, -3, 2.0), (1.2, 0, -0.9), 3, 300, (0.85, 0.9, 1.0))
    B._camera("CamB6_12", [(1, (0, 0, 0.2), (3.4, -3.8, 2.6), 40, 5.6), (145, (0, 0, 0.2), (-1.2, -4.8, 1.5), 40, 5.6)])
    _softbox("FilmBox13", (-0.2, 4.2, 1.2), 3.0, 3.0, target=(0, 0, 0.26))
    _softbox("FilmBox14", (0.8, 2.6, 0.45), 1.5, 3.0, target=(0, 0, 0.26))
    B._camera("CamB6_13", [(1, (0, 0.3, 0.26), (0.2, -3.6, 0.85), 35, 4.0), (106, (0, 0.3, 0.26), (-0.3, -3.5, 0.8), 35, 4.0)])
    B._camera("CamB6_14", [(1, (-0.6, 0, 0.27), (-1.4, -2.2, 0.33), 85, 2.0), (96, (0.6, 0, 0.27), (-0.2, -2.2, 0.33), 85, 2.0)])


# ---- B6_17 ---------------------------------------------------------------------------------
def down(sc, rnd):
    path, pmat = BM.machine()
    n = len(BM.PATH) - 1
    path.data.bevel_factor_start = 4 / n                           # from the reticle on
    path.data.bevel_factor_end = 4 / n
    path.data.keyframe_insert("bevel_factor_end", frame=1)
    path.data.bevel_factor_end = 6 / n
    path.data.keyframe_insert("bevel_factor_end", frame=84)
    B._area("MKey", (0, -9, 8), (0.9, 0, 0), 16, 2500, (0.8, 0.85, 1.0))
    B._camera("CamB6_17", [(1, (0.5, 0, 2.4), (-0.6, -6.2, 3.2), 35, 5.6), (84, (0.5, 0, 1.0), (-0.6, -6.4, 1.6), 35, 5.6)])


def build(variant="mask", seed=61):
    sc = C.reset_scene(FRAMES)
    C.set_world(top=(0.03, 0.035, 0.05), horizon=(0.012, 0.014, 0.02), bottom=(0.003, 0.004, 0.006))
    C.set_color_management(exposure=0.4)
    rnd = random.Random(seed)
    {"mask": mask, "section": section, "dust": dust, "robot": robot, "pellicle": pellicle,
     "down": down}[variant](sc, rnd)
    return sc
