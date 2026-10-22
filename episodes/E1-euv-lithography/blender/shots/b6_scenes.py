"""B6 — the reflective mask and its pellicle (F14, F35–F37). Variants:

  mask      B6_01  the mask turning into frame in a dark holder; plain metallic pattern area, no rainbow
  section   B6_02  dive into the mask edge: the B4_02 Mo/Si cross-section plus ~60 nm absorber lines on top
            B6_03  energy: violet light reflects off bare multilayer, dies on the absorber lines (6 deg, NXE)
  dust      B6_08  a small irregular grain drifting down through a slanted beam above a defocused mask
  robot     B6_10  clay reticle-handling robot: pick, move, place, faster each cycle (shape 示意)
  pellicle  B6_12  xray: the pellicle on its frame and studs over the pattern area, a faint grey film
            B6_13  the membrane under EUV light at 5.4 deg, a dim dull-red glow, violet hydrogen-plasma rim
            B6_14  grazing close-up of the hot membrane
  down      B6_17  xray High-NA machine: light from the pupil facet mirror to the reticle, down into M1/M2

Sources (research/visual/B6B7_sources.md, audit_B6.yaml):
- reticle 6 inch = 152 mm square, 6.35 mm thick [AGC US 8,288,062]; image field 104 x 132 mm, unchanged NXE -> EXE
  [ASML, van Schoot, EUVL Workshop 2021 s.34]. The long side (132 mm) is the scan direction; here it runs along X and
  the plane of incidence is XZ, as in the scanner (the chief ray leans in the scan direction).
- Mo/Si period 6.8 nm (2.3 nm Mo / 4.5 nm Si) [AGC]; Ru cap; reference TaBN absorber ~60 nm [imec, Philipsen,
  EUVL Workshop 2021 s.2/8/11]. Dense mask pitch >= 104 nm (NXE 13 nm resolution -> 26 nm pitch x 4) [ASML].
- No visible thin-film or diffraction colour: 6.8 nm period, a 13 nm membrane and 104-160 nm pitches are all far
  below what gives visible colour (B6B7_sources.md section D).
- Pellicle: ASML NXE pellicle concept [Brouns, Adv. Opt. Techn. 6 (2017) p.222-223, Fig. 3/4]: a rectangular
  full-field membrane on a thin border, a low frame suspended over the reticle with a ~0.2 mm slit, held only by
  four stud mounts glued to the reticle. 13 nm thick, up to 500 C in vacuum, "just below the reticle" [ASML 2022].
  Membrane size, frame height and stud positions are not public: 示意.
- Chief-ray angle at the reticle: 6 deg NXE [ZEISS, Conradi 2011 s.20], 5.4 deg EXE [ZEISS, Kaumanns 2024 s.9].
- 500 C = 773 K, about the Draper point: at most a barely visible dull red (section D). The glow is drawn at
  773 K and labelled 示意 on screen.
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

FRAMES = 320
EUV = (0.42, 0.16, 1.0)             # saturated EUV violet: a pastel violet emitter clips to white
NM = 1 / 30.9                       # scene units per nm in the B6_02/B6_03 cross-section (period 0.22 = 6.8 nm)
MM = 3.0 / 152.0                    # scene units per mm for the 6-inch reticle (side 3.0 units)
FIELD = (132 * MM, 104 * MM)        # image field at reticle level: 132 mm along X (scan), 104 mm along Y
CRA_EXE = math.radians(5.4)


def _key(ob, f, **kw):
    for k, v in kw.items():
        setattr(ob, k, v)
        ob.keyframe_insert(k, frame=f)


def _const(ob):
    """Constant interpolation on every F-curve of an object (switch-like keys: visibility, pulses)."""
    if ob.animation_data and ob.animation_data.action:
        for fc in C.fcurves(ob.animation_data.action):
            for kp in fc.keyframe_points:
                kp.interpolation = "CONSTANT"


def _box(name, loc, size, mat, role="structure", bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    ob = bpy.context.object
    ob.name = name
    ob.scale = (size[0] / 2, size[1] / 2, size[2] / 2)
    bpy.ops.object.transform_apply(scale=True)                 # unit scale, so parenting never inherits it
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


def _rect(name, sx, sy, loc, mat, role="structure"):
    """A flat rectangle whose object coordinates are real scene units (for texture layouts)."""
    bm = bmesh.new()
    vs = [bm.verts.new((x * sx / 2, y * sy / 2, 0)) for x, y in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    bm.faces.new(vs)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = loc
    ob.data.materials.append(mat)
    styles.tag(ob, role)
    return ob


def mask_material(name="MaskPattern"):
    """Image field of an EUV reticle as photographs show it: a mirror-bright Mo/Si surface carrying a dark absorber
    pattern. The dense lines are far below the pixel size, so what reads is a mosaic of functional blocks of
    different line density (different reflectivity) inside dies separated by scribe streets. No thin film and no
    rainbow (see module docstring). Object coordinates are scene units centred on the field."""
    m = M.principled(name, (0.62, 0.62, 0.65), metallic=1.0, roughness=0.05)
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    L = nt.links
    tc = nt.nodes.new("ShaderNodeTexCoord")
    off = nt.nodes.new("ShaderNodeVectorMath")             # die grid starts at the field corner
    off.operation = "ADD"
    off.inputs[1].default_value = (FIELD[0] / 2, FIELD[1] / 2, 0)
    L.new(tc.outputs["Object"], off.inputs[0])
    dies = nt.nodes.new("ShaderNodeTexBrick")              # 3 x 2 dies with ~1.5 mm scribe streets
    dies.offset = 0.0
    dies.squash = 1.0
    dies.inputs["Scale"].default_value = 1.0
    dies.inputs["Mortar Size"].default_value = 1.5 * MM
    dies.inputs["Mortar Smooth"].default_value = 0.0
    dies.inputs["Brick Width"].default_value = FIELD[0] / 3
    dies.inputs["Row Height"].default_value = FIELD[1] / 2
    L.new(off.outputs[0], dies.inputs["Vector"])
    # functional blocks: two overlapping brick grids of incommensurate size cut the die into rectangles of many
    # sizes; each gets its own line density, i.e. its own average reflectivity (the lines themselves are sub-pixel)
    dens = []
    for k, (bw, rh, offs, mortar) in enumerate(((0.31, 0.205, 0.5, 0.004), (0.118, 0.077, 0.27, 0.002))):
        bk = nt.nodes.new("ShaderNodeTexBrick")
        bk.offset = offs
        bk.inputs["Scale"].default_value = 1.0
        bk.inputs["Mortar Size"].default_value = mortar
        bk.inputs["Brick Width"].default_value = bw
        bk.inputs["Row Height"].default_value = rh
        bk.inputs["Bias"].default_value = 0.0
        bk.inputs["Color1"].default_value = (0.1, 0.1, 0.1, 1)
        bk.inputs["Color2"].default_value = (0.9, 0.9, 0.9, 1)
        bk.inputs["Mortar"].default_value = (0.5, 0.5, 0.5, 1)
        L.new(off.outputs[0], bk.inputs["Vector"])
        sp = nt.nodes.new("ShaderNodeSeparateColor")
        L.new(bk.outputs["Color"], sp.inputs["Color"])
        dens.append(sp.outputs["Red"])
    mixd = nt.nodes.new("ShaderNodeMath")
    mixd.operation = "MULTIPLY_ADD"
    mixd.inputs[1].default_value = 0.6
    L.new(dens[0], mixd.inputs[0])
    half = nt.nodes.new("ShaderNodeMath")
    half.operation = "MULTIPLY"
    half.inputs[1].default_value = 0.4
    L.new(dens[1], half.inputs[0])
    L.new(half.outputs[0], mixd.inputs[2])
    absorb = nt.nodes.new("ShaderNodeMapRange")              # absorber area fraction per block, 0.25..0.9
    absorb.inputs["To Min"].default_value = 0.25
    absorb.inputs["To Max"].default_value = 0.9
    L.new(mixd.outputs[0], absorb.inputs["Value"])
    street = nt.nodes.new("ShaderNodeMath")                # scribe streets: absorber-free bare multilayer strips
    street.operation = "SUBTRACT"
    street.inputs[0].default_value = 1.0
    L.new(dies.outputs["Fac"], street.inputs[1])
    a2 = nt.nodes.new("ShaderNodeMath")
    a2.operation = "MULTIPLY"
    L.new(absorb.outputs["Result"], a2.inputs[0])
    L.new(street.outputs[0], a2.inputs[1])
    col = nt.nodes.new("ShaderNodeValToRGB")                 # 0 = Mo/Si multilayer, 1 = TaBN-type absorber
    col.color_ramp.elements[0].color = (0.62, 0.62, 0.65, 1)
    col.color_ramp.elements[1].color = (0.035, 0.037, 0.042, 1)
    L.new(a2.outputs[0], col.inputs["Fac"])
    L.new(col.outputs["Color"], b.inputs["Base Color"])
    met = nt.nodes.new("ShaderNodeMapRange")
    met.inputs["To Min"].default_value = 1.0
    met.inputs["To Max"].default_value = 0.0
    L.new(a2.outputs[0], met.inputs["Value"])
    L.new(met.outputs["Result"], b.inputs["Metallic"])
    rough = nt.nodes.new("ShaderNodeMapRange")
    rough.inputs["To Min"].default_value = 0.05
    rough.inputs["To Max"].default_value = 0.35
    L.new(a2.outputs[0], rough.inputs["Value"])
    L.new(rough.outputs["Result"], b.inputs["Roughness"])
    return m


def _mask(loc=(0, 0, 0), size=3.0):
    """6-inch reticle, scaled: a dark square plate (absorber-covered outside the field) with the 104 x 132 mm image
    field on top, long side along X; returns the plate."""
    plate = _box("Mask", loc, (size, size, size * 0.042), M.principled("MaskSub", (0.09, 0.095, 0.1), metallic=0.4,
                                                                     roughness=0.18), bevel=0.01)
    k = size / 3.0
    pat = _rect("MaskPatternArea", FIELD[0] * k, FIELD[1] * k, (loc[0], loc[1], loc[2] + size * 0.0215),
                mask_material())
    pat.parent = plate
    pat.location = (0, 0, size * 0.0215)
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
    _softbox("Stripbox", (-4.5, 5.0, 3.5), 3.0, 4.0)
    B._area("Top", (2, -3, 6), (0.4, 0, 0.5), 4, 150, (0.75, 0.82, 1.0))
    B._camera("CamB6_01", [(1, (0, 0, 0), (-2.4, -6.6, 2.2), 50, 4.0), (128, (0.3, 0, 0), (0.4, -7.0, 2.0), 50, 4.0)])


# ---- B6_02 / B6_03 -------------------------------------------------------------------------
ABS_H = 60 * NM                     # ~1.94 units: reference TaBN absorber ~60 nm [imec 2021 s.8/11]
ABS_PITCH = 104 * NM                # 3.37 units: densest NXE mask pitch, 26 nm on the wafer x 4 [ASML]
ABS_W = ABS_PITCH / 2
ABS_X = [k * ABS_PITCH for k in (-2, -1, 0, 1, 2)]


def section(sc, rnd):
    import b2_scenes
    b2_scenes.multilayer(sc, n_pairs=20, t=0.11, width=16.0)    # the B4_02 stack, wide enough for 5 absorber lines
    ab = M.principled("Absorber", (0.05, 0.05, 0.05), roughness=0.6)
    for k, x in enumerate(ABS_X):
        blk = _box(f"Absorber{k}", (x, 0, ABS_H / 2), (ABS_W, 2.0, ABS_H), ab)
        blk["sem_tone"] = 0.22
        blk["absorber"] = True
    # B6_03 light (NXE, 6 deg from the normal): bare multilayer reflects, absorber tops swallow
    inc = M.emission("Incident", EUV, 0.45)
    ref = M.emission("Reflected", EUV, 0.0)
    ang = math.radians(6)
    for k in range(21):
        x = -6.0 + 0.6 * k
        on_absorber = any(abs(x - xa) < ABS_W / 2 + 0.02 for xa in ABS_X)
        z_hit = ABS_H if on_absorber else 0.0
        top = Vector((x - (8.0 - z_hit) * math.tan(ang), 0, 8.0))
        hit = Vector((x, 0, z_hit))
        b_in = _beam(f"In{k}", top, hit, 0.035, inc, role="rays")
        _key(b_in, 1, hide_render=True)
        _key(b_in, 184 + k // 3, hide_render=False)                  # B6_03 starts at frame 181
        if not on_absorber:
            out = Vector((x + 8.0 * math.tan(ang), 0, 8.0))
            b_out = _beam(f"Out{k}", hit, out, 0.035, ref, role="rays")
            _key(b_out, 1, hide_render=True)
            _key(b_out, 200, hide_render=False)
    M.set_emission_strength(ref, 200, 0.0)
    M.set_emission_strength(ref, 216, 0.7)
    # B6_02: from above the absorber lines down to the edge, ending on stack + absorber together
    B._camera("CamB6_02", [(1, (0, 0, 0.6), (0.0, -15.0, 9.0), 100, 11.0),
                           (128, (0, 0, -0.1), (0.0, -31.0, 1.2), 100, 11.0)])
    B._camera("CamB6_03", [(181, (0, 0, 0.0), (0.0, -31.0, 1.2), 100, 11.0),
                           (306, (0, 0, 2.6), (0.0, -42.0, 4.0), 100, 11.0)])


def after_style(style, shot_id):
    import b2_scenes
    b2_scenes.after_style(style, shot_id)
    if shot_id == "B6_03":                     # energy look: the absorber reads as solid dark-grey blocks
        fill = M.emission("AbsorberFill", (0.16, 0.15, 0.2), 0.3)
        for ob in bpy.data.objects:
            if ob.get("absorber"):
                ob.data.materials.clear()
                ob.data.materials.append(fill)
    if shot_id == "B6_12":                     # the quiet look: no light, no plasma yet
        for name in ("PulseIn", "PulseOut", "H2RimVol"):
            ob = bpy.data.objects.get(name)
            if ob:
                ob.animation_data_clear()      # keyed visibility would override the static value
                ob.hide_render = True
    if shot_id in ("B6_13", "B6_14"):
        mem = bpy.data.objects.get("Membrane")
        if mem:
            mem.data.materials.clear()
            mem.data.materials.append(film_material("HotMembrane", hot=True))


# ---- B6_08 ---------------------------------------------------------------------------------
def _grain(name, r, rnd):
    """An irregular particle: a few fused, displaced lumps (not a smooth egg)."""
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=4, radius=r)
    g = bpy.context.object
    g.name = name
    tex = bpy.data.textures.new(name + "Lumps", "VORONOI")
    tex.noise_scale = r * 0.9
    d = g.modifiers.new("Lumps", "DISPLACE")
    d.texture = tex
    d.strength = r * 0.55
    d.mid_level = 0.5
    tex2 = bpy.data.textures.new(name + "Grit", "CLOUDS")
    tex2.noise_scale = r * 0.3
    d2 = g.modifiers.new("Grit", "DISPLACE")
    d2.texture = tex2
    d2.strength = r * 0.18
    g.scale = (1.0, 0.72, 0.85)
    for p in g.data.polygons:
        p.use_smooth = False
    return g


def dust(sc, rnd):
    C.set_world(top=(0.003, 0.004, 0.006), horizon=(0.0015, 0.002, 0.003), bottom=(0.0, 0.0, 0.001))
    _mask(loc=(0, 0, -0.063), size=3.0)                              # top face at z = 0
    # slanted light shaft (a soft volume beam) and the grain falling through it
    tilt = math.radians(28)
    axis = Vector((math.sin(tilt), 0, math.cos(tilt)))
    shaft = M.volume_glow("Shaft", (0.86, 0.84, 1.0), 0.5, 0.0)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.16, depth=6.0, vertices=48, location=(0.0, 0, 0.0),
                                        rotation=(0, tilt, 0))
    sh = bpy.context.object
    sh.name = "ShaftVol"
    sh.data.materials.append(shaft)
    styles.tag(sh, "env")
    g = _grain("Grain", 0.0055, rnd)
    g.data.materials.append(M.principled("GrainMat", (0.62, 0.58, 0.52), roughness=0.55))
    styles.tag(g, "structure")
    mote = M.emission("Mote", (1.0, 0.96, 0.9), 0.6)
    for k in range(36):                                              # out-of-focus motes give the shaft depth
        t = rnd.uniform(-0.2, 1.0)
        c = axis * t + Vector((rnd.uniform(-0.1, 0.1), rnd.uniform(-0.6, 0.6), rnd.uniform(-0.05, 0.05)))
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=rnd.uniform(0.0015, 0.003), location=tuple(c))
        mo = bpy.context.object
        mo.data.materials.append(mote)
        styles.tag(mo, "emitter")
        _key(mo, 1, location=tuple(c))
        _key(mo, 58, location=tuple(c + Vector((rnd.uniform(-0.01, 0.01), 0, -rnd.uniform(0.01, 0.03)))))
    p0 = axis * 0.36 + Vector((0.004, 0, 0))
    p1 = axis * 0.25 + Vector((-0.010, 0, 0))
    _key(g, 1, location=tuple(p0), rotation_euler=(0, 0, 0))
    _key(g, 58, location=tuple(p1), rotation_euler=(1.1, 0.5, 1.7))
    spot = bpy.data.lights.new("ShaftLight", "SPOT")
    spot.energy = 900
    spot.spot_size = math.radians(9)
    spot.spot_blend = 0.4
    spot.shadow_soft_size = 0.05
    so = bpy.data.objects.new("ShaftLight", spot)
    sc.collection.objects.link(so)
    so.location = tuple(axis * 3.0)
    so.rotation_euler = (0, tilt, 0)
    _softbox("MaskSheen", (-2.2, 2.4, 1.2), 2.0, 1.5, target=(0, 0, 0))
    B._camera("CamB6_08", [(1, tuple(p0), (0.75, -1.45, 0.62), 100, 2.0),
                           (58, tuple(p1 + Vector((0, 0, 0.015))), (0.7, -1.42, 0.55), 100, 2.0)])


# ---- B6_10 ---------------------------------------------------------------------------------
def robot(sc, rnd):
    mat = M.principled("Robot", (0.7, 0.7, 0.7))
    floor = _box("Floor", (0, 0, -0.05), (40, 40, 0.1), mat)
    floor["clay_floor"] = True
    _box("RBase", (0, 0, 0.4), (0.9, 0.9, 0.8), mat, bevel=0.06)
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
    # pick at +X pedestal, place at +Y pedestal; cycles get shorter
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
MEM = (137 * MM, 107 * MM)          # membrane just larger than the 132 x 104 mm field (Brouns Fig. 4 "full field"); 示意
GAP = 0.3 * MM                      # the ~0.2 mm slit between reticle and frame [Brouns p.222], drawn slightly wider
FRAME_W, FRAME_H = 4.0 * MM, 1.6 * MM   # frame bar width / height: not public, 示意
BORDER_W, BORDER_H = 2.5 * MM, 0.6 * MM
MASK_TOP = 3.0 * 0.021              # top face of the 3.0-unit reticle built at the origin
MEM_Z = MASK_TOP + GAP + FRAME_H + BORDER_H


def film_material(name="PellicleFilm", hot=False):
    """A 13 nm p-Si film: almost fully transmissive with a faint warm-grey tint and a weak, Fresnel-weighted sheen.
    No thin-film colours (a 13 nm film is far below a quarter visible wavelength). hot=True adds a dim 773 K
    (500 C) blackbody glow, mottled and slowly drifting; it brightens over the first 80 frames."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    L = nt.links
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    tr.inputs["Color"].default_value = (0.9, 0.88, 0.84, 1)
    gl = nt.nodes.new("ShaderNodeBsdfGlossy")
    gl.inputs["Roughness"].default_value = 0.05
    gl.inputs["Color"].default_value = (0.95, 0.93, 0.9, 1)
    lw = nt.nodes.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.12
    k = nt.nodes.new("ShaderNodeMath")
    k.operation = "MULTIPLY"
    k.inputs[1].default_value = 0.85
    L.new(lw.outputs["Fresnel"], k.inputs[0])
    mix = nt.nodes.new("ShaderNodeMixShader")
    L.new(k.outputs[0], mix.inputs["Fac"])
    L.new(tr.outputs[0], mix.inputs[1])
    L.new(gl.outputs[0], mix.inputs[2])
    surf = mix.outputs[0]
    if hot:
        em = nt.nodes.new("ShaderNodeEmission")
        # the colour of a 773 K body (deep red; Blender's Blackbody node is luminance-normalised, so the colour is
        # set directly and the strength kept low: a faint dull red, labelled 示意 on screen)
        em.inputs["Color"].default_value = (1.0, 0.07, 0.0, 1)
        tc = nt.nodes.new("ShaderNodeTexCoord")
        noise = nt.nodes.new("ShaderNodeTexNoise")
        noise.noise_dimensions = "4D"
        noise.inputs["Scale"].default_value = 2.5
        noise.inputs["Detail"].default_value = 3.0
        L.new(tc.outputs["Object"], noise.inputs["Vector"])
        w = nt.nodes.new("ShaderNodeValue")                       # slow drift of the hot spots
        w.outputs[0].default_value = 0.0
        w.outputs[0].keyframe_insert("default_value", frame=1)
        w.outputs[0].default_value = 2.0
        w.outputs[0].keyframe_insert("default_value", frame=300)
        L.new(w.outputs[0], noise.inputs["W"])
        mr = nt.nodes.new("ShaderNodeMapRange")
        mr.inputs["To Min"].default_value = 0.35
        mr.inputs["To Max"].default_value = 1.0
        L.new(noise.outputs["Fac"], mr.inputs["Value"])
        ramp_t = nt.nodes.new("ShaderNodeValue")                  # heats up over the first 80 frames
        ramp_t.outputs[0].default_value = 0.004
        ramp_t.outputs[0].keyframe_insert("default_value", frame=1)
        ramp_t.outputs[0].default_value = 0.05
        ramp_t.outputs[0].keyframe_insert("default_value", frame=80)
        mul = nt.nodes.new("ShaderNodeMath")
        mul.operation = "MULTIPLY"
        L.new(mr.outputs["Result"], mul.inputs[0])
        L.new(ramp_t.outputs[0], mul.inputs[1])
        L.new(mul.outputs[0], em.inputs["Strength"])
        add = nt.nodes.new("ShaderNodeAddShader")
        L.new(surf, add.inputs[0])
        L.new(em.outputs[0], add.inputs[1])
        surf = add.outputs[0]
    L.new(surf, out.inputs["Surface"])
    m.surface_render_method = "BLENDED"
    return m


def _ring_frame(prefix, inner, width, z0, h, mat):
    """Four bars forming a rectangular ring around an inner rectangle (inner = (x, y) size)."""
    ix, iy = inner
    ox, oy = ix + 2 * width, iy + 2 * width
    obs = []
    for k, (x, y, sx, sy) in enumerate(((0, (iy + width) / 2, ox, width), (0, -(iy + width) / 2, ox, width),
                                        ((ix + width) / 2, 0, width, iy), (-(ix + width) / 2, 0, width, iy))):
        obs.append(_box(f"{prefix}{k}", (x, y, z0 + h / 2), (sx, sy, h), mat, bevel=min(h, width) * 0.15))
    return obs


def pellicle(sc, rnd):
    C.set_world(top=(0.006, 0.007, 0.011), horizon=(0.003, 0.003, 0.005), bottom=(0.0, 0.0, 0.001))
    _mask(loc=(0, 0, 0), size=3.0)
    # pellicle after Brouns 2017 Fig. 3: frame (suspended over a small slit) -> border -> membrane;
    # four studs glued to the reticle carry the frame through fixtures
    frame_mat = M.principled("PelFrame", (0.55, 0.56, 0.58), metallic=0.9, roughness=0.32)
    border_mat = M.principled("PelBorder", (0.18, 0.19, 0.21), metallic=0.5, roughness=0.3)
    stud_mat = M.principled("PelStud", (0.62, 0.6, 0.56), metallic=0.8, roughness=0.3)
    frame_inner = (MEM[0] + 2 * BORDER_W - 2 * 1.0 * MM, MEM[1] + 2 * BORDER_W - 2 * 1.0 * MM)
    _ring_frame("PelFrame", frame_inner, FRAME_W, MASK_TOP + GAP, FRAME_H, frame_mat)
    _ring_frame("PelBorder", MEM, BORDER_W, MASK_TOP + GAP + FRAME_H, BORDER_H, border_mat)
    fx, fy = frame_inner[0] / 2 + FRAME_W / 2, frame_inner[1] / 2 + FRAME_W / 2
    for k, (sx, sy) in enumerate(((-1, -1), (1, -1), (1, 1), (-1, 1))):
        x, y = sx * fx * 0.78, sy * (fy + FRAME_W * 0.9)              # on the long sides, near the corners (示意)
        bpy.ops.mesh.primitive_cylinder_add(radius=2.2 * MM, depth=GAP + FRAME_H, vertices=24,
                                            location=(x, y, MASK_TOP + (GAP + FRAME_H) / 2))
        st = bpy.context.object
        st.name = f"PelStud{k}"
        st.data.materials.append(stud_mat)
        styles.tag(st, "structure")
        _box(f"PelFixture{k}", (x, y - sy * FRAME_W * 0.45, MASK_TOP + GAP + FRAME_H + 0.6 * MM),
             (7.0 * MM, 2.6 * FRAME_W, 1.2 * MM), frame_mat, bevel=0.002)
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=80, y_subdivisions=64, size=1.0, location=(0, 0, MEM_Z))
    mem = bpy.context.object
    mem.name = "Membrane"
    mem.scale = (MEM[0], MEM[1], 1)
    bpy.ops.object.transform_apply(scale=True)
    mem.data.materials.append(film_material())
    styles.tag(mem, "structure")
    wob = mem.modifiers.new("Flutter", "WAVE")                       # faint billow (示意)
    wob.height = 0.0012
    wob.width = 1.0
    wob.speed = 0.008
    # EUV light at the EXE chief-ray angle (5.4 deg from the normal), in the scan plane (XZ), through the membrane
    # down to the mask and back out. The real source fires at 50 kHz; the visible pulses are 示意.
    pulse = M.emission("PelPulse", EUV, 0.0)
    hit = (0.0, 0.0, MASK_TOP + 0.001)
    top = 3.2
    dx = math.tan(CRA_EXE) * top
    beams = [_beam("PulseIn", (-dx, 0, top), hit, 0.05, pulse), _beam("PulseOut", hit, (dx, 0, top), 0.05, pulse)]
    for bo in beams:
        _key(bo, 1, hide_render=True)
    s = pulse.node_tree.nodes["Emission"].inputs["Strength"]
    s.default_value = 0.0
    s.keyframe_insert("default_value", frame=1)
    for k in range(9):
        f0 = 8 + 11 * k
        for bo in beams:                               # visibility and emission switch on the same frames
            _key(bo, f0, hide_render=False)
            _key(bo, f0 + 5, hide_render=True)
        for f, v in ((f0, 1.0), (f0 + 2, 0.75), (f0 + 4, 0.45), (f0 + 5, 0.0)):
            s.default_value = v
            s.keyframe_insert("default_value", frame=f)
    for bo in beams:
        _const(bo)
    for fc in C.fcurves(pulse.node_tree.animation_data.action):
        for kp in fc.keyframe_points:
            kp.interpolation = "CONSTANT"
    # violet hydrogen-plasma rim hugging the membrane (EUV-induced H2 plasma near the reticle; look 示意)
    rim = M.volume_glow("H2Rim", (0.45, 0.25, 1.0), 0.12, 0.7, noise_scale=7.0)
    bpy.ops.mesh.primitive_cube_add(location=(0, 0, MEM_Z + 0.025))
    rv = bpy.context.object
    rv.name = "H2RimVol"
    rv.scale = (MEM[0] / 2, MEM[1] / 2, 0.022)
    rv.data.materials.append(rim)
    styles.tag(rv, "emitter")
    B._area("PelKey", (-4, -3, 2.0), (1.2, 0, -0.9), 3, 300, (0.85, 0.9, 1.0))
    B._camera("CamB6_12", [(1, (0.15, 0, 0.0), (3.0, -3.4, 1.9), 40, 5.6), (146, (-0.1, 0, 0.0), (-1.4, -4.2, 1.3), 40, 5.6)])
    _softbox("FilmBox13", (-0.4, 4.6, 0.9), 3.4, 2.4, target=(0, 0, MEM_Z))
    _softbox("FilmBox14", (0.8, 3.2, 0.32), 1.8, 2.2, target=(0, 0, MEM_Z))
    B._camera("CamB6_13", [(1, (0.0, 0.2, MEM_Z), (0.45, -2.9, 1.45), 50, 4.0),
                           (106, (0.0, 0.2, MEM_Z), (-0.2, -2.6, 1.25), 50, 4.0)])
    ey = -MEM[1] / 2                                                  # the near border, in focus
    B._camera("CamB6_14", [(1, (-0.75, ey + 0.12, MEM_Z), (-1.25, ey - 0.95, MEM_Z + 0.13), 85, 2.8),
                           (96, (0.35, ey + 0.12, MEM_Z), (-0.15, ey - 0.95, MEM_Z + 0.13), 85, 2.8)])


# ---- B6_17 ---------------------------------------------------------------------------------
def down(sc, rnd):
    """The High-NA machine (BM): light from the pupil facet mirror up to the face-down reticle (5.4 deg) and the
    reflected beam growing down into the projection optics (M1, M2)."""
    path, pmat = BM.machine()
    path.data.bevel_depth = 0.04
    n = len(BM.PATH) - 1
    i_f2 = BM.PATH.index(BM.FACET2)
    i_m2 = i_f2 + 3                                                 # FACET2 -> RETICLE -> M1 -> M2
    path.data.bevel_factor_start = i_f2 / n                         # the incoming ray, then the reflection
    path.data.bevel_factor_end = (i_f2 + 1) / n
    path.data.keyframe_insert("bevel_factor_end", frame=1)
    path.data.bevel_factor_end = i_m2 / n
    path.data.keyframe_insert("bevel_factor_end", frame=70)
    B._area("MKey", (0, -9, 8), (0.9, 0, 0), 16, 2500, (0.8, 0.85, 1.0))
    r = Vector(BM.RETICLE)
    m12 = (Vector(BM.PO_MIRRORS[0]) + Vector(BM.PO_MIRRORS[1])) / 2
    B._camera("CamB6_17", [(1, tuple(r + Vector((0.0, 0, -0.35))), tuple(r + Vector((-2.0, -5.2, -0.9))), 40, 5.6),
                           (84, tuple(m12 + Vector((0.05, 0, -0.1))), tuple(m12 + Vector((-2.2, -5.6, 0.2))), 40, 5.6)])


def build(variant="mask", seed=61):
    sc = C.reset_scene(FRAMES)
    C.set_world(top=(0.03, 0.035, 0.05), horizon=(0.012, 0.014, 0.02), bottom=(0.003, 0.004, 0.006))
    C.set_color_management(exposure=0.4)
    rnd = random.Random(seed)
    {"mask": mask, "section": section, "dust": dust, "robot": robot, "pellicle": pellicle,
     "down": down}[variant](sc, rnd)
    return sc
