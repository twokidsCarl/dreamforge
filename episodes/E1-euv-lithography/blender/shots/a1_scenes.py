"""A1 — what lithography is (F44, F55). Variants:

  cut      A1_02  clay wafer with a wedge cut away: substrate and film layers in section
  spin     A1_03  yellow-room spin coater: amber resist spreads into an even film
  expose   A1_04  energy: light through a patterned (transmissive, generic) mask prints a glow on the resist
  process  A1_06  clay section: develop -> etch -> deposit, one layer of wiring left behind
           A1_07  the cycle repeats faster and faster; the stack grows, the camera rises
  stack    A1_09  xray chip section: ~100 layers, coarse at the top, the finest ~20 at the bottom glow violet
Illustrative, not to scale.
"""
import math
import random

import bpy
from mathutils import Matrix, Vector

import a0_scenes as A0
import common as C
import materials as M
import sample_b1 as B
import styles

FRAMES = 330
VIOLET = (0.62, 0.45, 1.0)
GOLD = (0.83, 0.62, 0.3)


def _key(ob, f, **kw):
    for k, v in kw.items():
        setattr(ob, k, v)
        ob.keyframe_insert(k, frame=f)


_box = A0._box
_cyl = A0._cyl


def _apply_scale(ob):
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return ob


def _additive(name, color):
    """Emission added over a fully transparent surface: invisible at strength 0 (no black card)."""
    m = M.emission(name, color, 0.0)
    nt = m.node_tree
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    add = nt.nodes.new("ShaderNodeAddShader")
    nt.links.new(tr.outputs[0], add.inputs[0])
    nt.links.new(nt.nodes["Emission"].outputs[0], add.inputs[1])
    nt.links.new(add.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
    m.surface_render_method = "BLENDED"
    return m


def _floor(mat):
    return _box("Floor", (0, 0, -0.6), (60, 60, 0.1), mat)


# ---- A1_02 ---------------------------------------------------------------------------------
def cut(sc, rnd):
    clay = M.principled("Clay", (0.7, 0.7, 0.7))
    _floor(clay)
    bpy.ops.mesh.primitive_cube_add(location=(1.2, -1.2, 0.0))
    wedge = bpy.context.object
    wedge.scale = (1.2, 1.2, 1.0)
    wedge.hide_render = wedge.hide_viewport = True
    z = -0.5
    for k, (th, col) in enumerate(((0.32, (0.62, 0.62, 0.62)), (0.06, (0.78, 0.78, 0.8)), (0.05, (0.7, 0.72, 0.76)),
                                   (0.04, (0.85, 0.82, 0.74)))):
        d = _cyl(f"Layer{k}", 2.0, th, (0, 0, z + th / 2), M.principled(f"L{k}", col), verts=128)
        b = d.modifiers.new("Cut", "BOOLEAN")
        b.object = wedge
        b.operation = "DIFFERENCE"
        z += th
    B._area("ClayKey", (5, -6, 8), (0.8, 0, 0.6), 8, 1800, (1.0, 0.98, 0.95))
    B._camera("CamA1_02", [(1, (0.6, -0.6, -0.3), (-2.5, -6.0, 2.6), 45, 8.0), (125, (0.9, -0.9, -0.3), (2.8, -6.4, 0.9), 50, 8.0)])


# ---- A1_03 ---------------------------------------------------------------------------------
def spin(sc, rnd):
    C.set_world(top=(0.04, 0.03, 0.005), horizon=(0.02, 0.015, 0.002), bottom=(0.002, 0.002, 0.0))
    steel = M.polished_steel("Bowl", 0.3)
    bpy.ops.mesh.primitive_cylinder_add(radius=3.0, depth=1.2, vertices=96, end_fill_type="NOTHING", location=(0, 0, -0.5))
    bowl = bpy.context.object
    bowl.modifiers.new("Wall", "SOLIDIFY").thickness = 0.08
    bowl.data.materials.append(steel)
    styles.tag(bowl, "structure")
    _cyl("Chuck", 0.6, 0.4, (0, 0, -0.25), steel)
    bpy.ops.object.empty_add(location=(0, 0, 0))
    rot = bpy.context.object
    rot.name = "Spinner"
    wafer = _cyl("Wafer", 2.0, 0.03, (0, 0, 0), M.principled("WaferSi", (0.4, 0.4, 0.45), metallic=1.0, roughness=0.04),
                 verts=128)
    wafer.parent = rot
    resist = M.principled("Resist", (0.9, 0.45, 0.05), roughness=0.05, coat=1.0)
    rb = resist.node_tree.nodes["Principled BSDF"]
    rb.inputs["Transmission Weight"].default_value = 0.6
    film = _cyl("ResistFilm", 1.99, 0.012, (0, 0, 0.022), resist, verts=128)
    film.parent = rot
    _key(film, 1, scale=(0.05, 0.05, 3.0))
    _key(film, 40, scale=(0.08, 0.08, 3.0))
    _key(film, 150, scale=(1.0, 1.0, 1.0))
    notch = _box("WaferNotch", (2.0, 0, 0.02), (0.12, 0.12, 0.06), M.principled("Notch", (0.02, 0.02, 0.02)))
    notch.parent = rot                                              # the orientation notch shows the slow phase
    # spin coating: resist is dispensed at rest / slowly, then the wafer spins up to a few thousand rpm
    # (MicroChemicals application notes; research/visual/A1_sources.md). 3000 rpm = 750 deg per frame at 24 fps,
    # read through motion blur; excess resist leaves the edge as droplets flung off along the tangent.
    _key(rot, 1, rotation_euler=(0, 0, 0))
    _key(rot, 60, rotation_euler=(0, 0, math.radians(60)))          # dispense, wafer turning slowly
    _key(rot, 90, rotation_euler=(0, 0, math.radians(60 + 15 * 750)))   # ramp (about half the top speed on average)
    _key(rot, 174, rotation_euler=(0, 0, math.radians(60 + 15 * 750 + 84 * 750)))
    for fc in C.fcurves(rot.animation_data.action):
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR"
    for k in range(14):                                             # droplets flung off the edge, tangentially
        th = 2 * math.pi * rnd.random()
        f0 = 92 + 5 * k
        p0 = Vector((2.0 * math.cos(th), 2.0 * math.sin(th), 0.03))
        tang = Vector((-math.sin(th), math.cos(th), 0.0))
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.025, location=tuple(p0))
        d = bpy.context.object
        d.name = f"Fling{k}"
        d.data.materials.append(resist)
        styles.tag(d, "structure")
        _key(d, 1, hide_render=True)
        _key(d, f0, hide_render=False, location=tuple(p0))
        _key(d, f0 + 6, location=tuple(p0 + tang * 1.4 + Vector((p0.x, p0.y, 0)) * 0.08))
        _key(d, f0 + 7, hide_render=True)
    stream = _cyl("Drip", 0.04, 3.0, (0, 0, 1.55), resist, verts=12)
    _key(stream, 1, scale=(1, 1, 1))
    _key(stream, 60, scale=(1, 1, 1))
    _key(stream, 75, scale=(0.0, 0.0, 1))
    _cyl("Nozzle", 0.08, 0.6, (0, 0, 3.3), steel)
    yellow = M.emission("YellowRoom", (1.0, 0.72, 0.18), 6.0)
    for k in range(4):                                              # yellow light strips mirrored in the wafer
        _box(f"Strip{k}", (-6.0 + 4.0 * k, 5.0, 4.5), (0.3, 6.0, 0.08), yellow, role="emitter")
    bpy.ops.object.light_add(type="AREA", location=(0, 2, 6))
    l = bpy.context.object
    l.data.energy = 600
    l.data.size = 6
    l.data.color = (1.0, 0.75, 0.3)
    styles.tag(l, "rig")
    sc.render.use_motion_blur = True
    B._camera("CamA1_03", [(1, (0.6, 0.2, 0.0), (2.6, -2.8, 0.45), 50, 2.8), (174, (-0.2, 0.4, 0.0), (1.4, -3.2, 0.5), 50, 2.8)])


# ---- A1_04 ---------------------------------------------------------------------------------
def expose(sc, rnd):
    import b7_scenes
    C.set_world(top=(0, 0, 0), horizon=(0, 0, 0), bottom=(0, 0, 0))
    _box("ResistLayer", (0, 0, -0.08), (6, 6, 0.16), M.principled("ResistDark", (0.05, 0.03, 0.01)))
    glow = A0.circuit_emission("Latent", (0.95, 0.7, 0.3), 0.0, scale=0.6)
    bpy.ops.mesh.primitive_plane_add(size=4.0, location=(0, 0, 0.005))
    p = bpy.context.object
    p.data.materials.append(glow)
    styles.tag(p, "emitter")
    M.set_emission_strength(glow, 50, 0.0)
    M.set_emission_strength(glow, 110, 2.0)
    _box("MaskPlate", (0, 0, 3.0), (4.6, 4.6, 0.12), M.principled("MaskGlass", (0.5, 0.5, 0.55)))
    lit = A0.circuit_emission("MaskLit", (0.85, 0.75, 1.0), 0.0, scale=0.6)
    bpy.ops.mesh.primitive_plane_add(size=4.0, location=(0, 0, 3.07))
    mp = bpy.context.object
    mp.data.materials.append(lit)
    styles.tag(mp, "emitter")
    M.set_emission_strength(lit, 20, 0.0)
    M.set_emission_strength(lit, 40, 3.0)
    bm = b7_scenes._cone_mat("ExposeBeam", 0.3)
    _box("Beam", (0, 0, 6.0), (4.0, 4.0, 6.0), bm, role="emitter")
    shadow = b7_scenes._cone_mat("ShadowBeam", 0.12)              # patterned light between mask and resist
    _box("BeamBelow", (0, 0, 1.5), (4.0, 4.0, 3.0), shadow, role="emitter")
    B._camera("CamA1_04", [(1, (0, 0, 3.0), (0.0, -6.0, 9.0), 35, 11.0), (170, (0, 0, 0.0), (0.0, -5.2, 0.9), 35, 11.0)])


# ---- A1_06 / A1_07 -------------------------------------------------------------------------
def process(sc, rnd):
    clay = M.principled("ClayProc", (0.7, 0.7, 0.7))
    film_m = M.principled("Film", (0.55, 0.58, 0.62))
    resist_m = M.principled("ResistClay", (0.86, 0.8, 0.66))
    metal_m = M.principled("Metal", GOLD, metallic=0.6, roughness=0.35)
    _box("Substrate", (0, 0, -0.5), (8.0, 2.0, 1.0), clay)
    n = 9
    w = 8.0 / n
    exposed = [k % 2 == 1 for k in range(n)]
    for k in range(n):
        x = -4.0 + w * (k + 0.5)
        film = _apply_scale(_box(f"Film{k}", (x, 0, 0.15), (w, 2.0, 0.3), film_m))
        res = _apply_scale(_box(f"Resist{k}", (x, 0, 0.42), (w, 2.0, 0.24), resist_m, role="emitter"))
        # scale about the bottom face: move the origin down
        for ob, zb in ((film, 0.0), (res, 0.3)):
            ob.data.transform(Matrix.Translation((0, 0, ob.location.z - zb)))
            ob.location.z = zb
        # damascene order (IBM): develop -> etch the trench -> strip the resist -> deposit metal over the whole
        # wafer (filling and overfilling the trenches) -> chemical-mechanical polish back to the dielectric
        if exposed[k]:
            _key(res, 20, scale=(1, 1, 1))
            _key(res, 55, scale=(1, 1, 0.001))                      # develop: exposed resist dissolves
            _key(film, 60, scale=(1, 1, 1))
            _key(film, 95, scale=(1, 1, 0.001))                     # etch: trench bites into the film
            met = _apply_scale(_box(f"Metal{k}", (x, 0, 0.0), (w * 0.98, 2.0, 0.3), metal_m, role="emitter"))
            met.data.transform(Matrix.Translation((0, 0, 0.15)))
            _key(met, 1, scale=(1, 1, 0.001))
            _key(met, 122, scale=(1, 1, 0.001))
            _key(met, 145, scale=(1, 1, 1))                         # deposit: metal fills the trench
        else:
            _key(res, 98, scale=(1, 1, 1))
            _key(res, 118, scale=(1, 1, 0.001))                     # strip the remaining resist (before metal)
    over = _apply_scale(_box("Overburden", (0, 0, 0.0), (8.0, 2.0, 0.14), metal_m, role="emitter"))
    over.data.transform(Matrix.Translation((0, 0, 0.07)))
    over.location.z = 0.3
    _key(over, 1, scale=(1, 1, 0.001))
    _key(over, 124, scale=(1, 1, 0.001))
    _key(over, 145, scale=(1, 1, 1))                                # blanket deposition overfills the trenches
    _key(over, 152, scale=(1, 1, 1))
    _key(over, 174, scale=(1, 1, 0.001))                            # CMP polishes it away: lines left in the trenches
    # A1_07 (181-321): the cycle repeats, faster and faster; each new layer grows on top with a violet flash
    flash = _additive("ExpoFlash", VIOLET)
    # the exposure flash lights only the newest layer's top face (a full-frame card blew the picture out)
    fl = _box("FlashSheet", (0, 0, 0.3), (8.1, 2.1, 0.005), flash, role="emitter")
    top = 0.3
    f = 182
    for c in range(9):
        dur = max(8, int(30 * 0.8 ** c))
        th = 0.3
        # every level is dielectric with metal embedded: wire levels carry parallel lines (direction alternating
        # from one wire level to the next), via levels carry a few vertical plugs; a continuous metal sheet
        # would short everything. wire ends stand 0.003 proud of the cut faces: flush faces z-fought into slivers
        parts = [_apply_scale(_box(f"Stack{c}", (0, 0, 0), (8.0, 2.0, th), film_m, bevel=0.012))]   # bevel: layer seams read
        if c % 2 == 0:
            along_x = (c // 2) % 2 == 0
            for j in range(7):
                if along_x:
                    parts.append(_apply_scale(_box(f"Stack{c}W{j}", (0, -0.85 + 0.283 * j, 0), (8.006, 0.13, th * 0.9),
                                                   metal_m, role="emitter")))
                else:
                    parts.append(_apply_scale(_box(f"Stack{c}W{j}", (-3.6 + 1.2 * j, 0, 0), (0.22, 2.006, th * 0.9),
                                                   metal_m, role="emitter")))
        else:
            for j in range(5):
                parts.append(_apply_scale(_box(f"Stack{c}V{j}", (-3.0 + 1.5 * j, -0.85 + 0.566 * (j % 4), 0),
                                               (0.12, 0.12, th), metal_m, role="emitter")))
        for lay in parts:
            _key(lay, 1, hide_render=True)
            _key(lay, f, hide_render=False)
            lay.data.transform(Matrix.Translation((0, 0, th / 2)))
            lay.location.z = top
            _key(lay, 1, scale=(1, 1, 0.001))
            _key(lay, f, scale=(1, 1, 0.001))
            _key(lay, f + dur // 2, scale=(1, 1, 1))
        _key(fl, f + dur // 2 - 1, location=(0, 0, top + th + 0.01))
        M.set_emission_strength(flash, f + dur // 2 - 1, 0.0)
        M.set_emission_strength(flash, f + dur // 2, 3.0)
        M.set_emission_strength(flash, f + dur // 2 + 3, 0.0)
        top += th
        f += dur
    for fc in C.fcurves(fl.animation_data.action):
        for kp in fc.keyframe_points:
            kp.interpolation = "CONSTANT"
    B._area("ClayKey", (5, -6, 8), (0.8, 0, 0.6), 8, 1800, (1.0, 0.98, 0.95))
    B._camera("CamA1_06", [(1, (0, 0, 0.2), (0.0, -12.5, 1.4), 50, 11.0), (176, (0, 0, 0.2), (0.8, -12.5, 1.5), 50, 11.0)])
    B._camera("CamA1_07", [(181, (0, 0, 0.6), (0.8, -12.5, 1.6), 50, 11.0), (321, (0, 0, 2.2), (6.0, -14.0, 5.0), 40, 11.0)])


# ---- A1_09 ---------------------------------------------------------------------------------
def _band_mat(name, scale, color, emit=0.0):
    m = M.principled(name, color, metallic=0.5, roughness=0.4)
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    wave = nt.nodes.new("ShaderNodeTexWave")
    wave.inputs["Scale"].default_value = scale
    wave.inputs["Distortion"].default_value = 0.0
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.48
    ramp.color_ramp.elements[1].position = 0.52
    nt.links.new(tc.outputs["Object"], wave.inputs["Vector"])
    nt.links.new(wave.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], b.inputs["Alpha"])
    if emit:
        b.inputs["Emission Color"].default_value = (*VIOLET, 1)
        b.inputs["Emission Strength"].default_value = emit
    return m


def stack(sc, rnd):
    C.set_world(top=(0.9, 0.91, 0.93), horizon=(0.78, 0.79, 0.82), bottom=(0.6, 0.61, 0.64))
    _box("ChipSub", (0, 0, -0.4), (6.0, 6.0, 0.8), M.principled("SubPanel", (0.78, 0.8, 0.82), metallic=0.2,
                                                                roughness=0.45), role="shell")
    n = 60
    z = 0.0
    for k in range(n):
        fine = k < 22
        th = 0.025 if fine else 0.025 + 0.004 * (k - 22)
        scale = 90.0 - 1.4 * k if k < 50 else 18.0
        m = _band_mat(f"Lay{k}", scale, (0.6, 0.62, 0.68) if not fine else (0.45, 0.3, 0.9), emit=3.0 if fine else 0.0)
        lay = _box(f"ChipLayer{k}", (0, 0, z + th / 2), (5.6, 5.6, th * 0.8), m, role="emitter" if fine else "structure")
        lay.rotation_euler = (0, 0, 0 if k % 2 else math.pi / 2)
        z += th * 1.15
    B._area("MKey", (0, -9, 8), (0.9, 0, 0), 16, 2500, (0.8, 0.85, 1.0))
    B._camera("CamA1_09", [(1, (0, 0, 1.6), (0.0, -11.0, 1.6), 40, 8.0), (171, (0, 0, 0.6), (6.5, -7.5, 5.0), 40, 5.6)])


def build(variant="cut", seed=21):
    sc = C.reset_scene(FRAMES)
    C.set_world(top=(0.03, 0.035, 0.05), horizon=(0.012, 0.014, 0.02), bottom=(0.003, 0.004, 0.006))
    C.set_color_management(exposure=0.4)
    rnd = random.Random(seed)
    {"cut": cut, "spin": spin, "expose": expose, "process": process, "stack": stack}[variant](sc, rnd)
    return sc
