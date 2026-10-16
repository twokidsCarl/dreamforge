"""A2/A3 3D shots (F1, F8, F10, F20). Variants:

  ribbon   A2_08  a 13.5 nm wave as a glowing ribbon oscillating in the dark (energy)
  lens     A3_04  a glass lens swallows the violet beam (warm glow at entry); a Mo/Si mirror replaces it
  montage  A3_05  four stylised vignettes, hard whip cuts: optical bench, mirror polishing, laser hall,
                  clean-room assembly (no real facility copied)
  tour     A3_06  xray machine: the violet path lights module after module from source to wafer
"""
import math
import random

import bpy
from mathutils import Vector

import a0_scenes as A0
import build_machine as BM
import common as C
import materials as M
import sample_b1 as B
import styles

FRAMES = 270
VIOLET = (0.62, 0.45, 1.0)
ORANGE = (1.0, 0.42, 0.12)
_box, _cyl, _key = A0._box, A0._cyl, A0._key


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


# ---- A2_08 ---------------------------------------------------------------------------------
def ribbon(sc, rnd):
    C.set_world(top=(0, 0, 0), horizon=(0, 0, 0), bottom=(0, 0, 0))
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0))
    rb = bpy.context.object
    rb.name = "WaveRibbon"
    rb.scale = (12.0, 0.12, 1)
    sub = rb.modifiers.new("Sub", "SUBSURF")
    sub.levels = sub.render_levels = 0
    bpy.ops.object.select_all(action="DESELECT")
    rb.select_set(True)
    bpy.context.view_layer.objects.active = rb
    bpy.ops.object.transform_apply(scale=True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.subdivide(number_cuts=400)
    bpy.ops.object.mode_set(mode="OBJECT")
    tex = bpy.data.textures.new("WaveTex", "WOOD")
    tex.wood_type = "BANDS"
    tex.noise_basis_2 = "SIN"
    tex.noise_scale = 0.5
    wv = rb.modifiers.new("Wave", "DISPLACE")
    wv.texture = tex
    wv.direction = "Z"
    wv.texture_coords = "GLOBAL"
    wv.strength = 0.9
    _key(rb, 1, location=(0, 0, 0))
    _key(rb, 60, location=(-1.2, 0, 0))
    m = M.emission("RibbonGlow", (0.72, 0.52, 1.0), 6.0)
    rb.data.materials.append(m)
    styles.tag(rb, "emitter")
    B._camera("CamA2_08", [(1, (0.6, 0, 0.4), (2.6, -2.4, 0.9), 85, 1.4), (60, (0.6, 0, 0.4), (1.8, -1.9, 0.7), 85, 1.4)])


# ---- A3_04 ---------------------------------------------------------------------------------
def lens(sc, rnd):
    C.set_world(top=(0.01, 0.012, 0.018), horizon=(0.005, 0.006, 0.009), bottom=(0.001, 0.001, 0.002))
    glass = M.principled("OpticalGlass", (0.95, 0.97, 1.0), roughness=0.0)
    gb = glass.node_tree.nodes["Principled BSDF"]
    gb.inputs["Transmission Weight"].default_value = 1.0
    gb.inputs["IOR"].default_value = 1.5
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1.4, segments=96, ring_count=48, location=(0, 0, 1.6))
    ln = bpy.context.object
    ln.name = "Lens"
    ln.scale = (0.32, 1.0, 1.0)
    for p in ln.data.polygons:
        p.use_smooth = True
    ln.data.materials.append(glass)
    styles.tag(ln, "structure")
    stand = M.dark_anodized("Stand")
    ring = _cyl("LensRing", 1.45, 0.3, (0, 0, 1.6), stand, rot=(0, math.pi / 2, 0))
    ring.modifiers.new("Hollow", "SOLIDIFY").thickness = 0.08
    _cyl("Post", 0.08, 1.0, (0, 0, -0.1), stand)
    _box("Bench", (0, 0, -0.65), (10, 3, 0.1), M.principled("BenchTop", (0.04, 0.04, 0.05), roughness=0.4))
    mirror = A0._cyl("Mirror", 1.3, 0.16, (0, 0, 1.6), M.multilayer_mirror("A3Mirror", r_max=1.3),
                     rot=(0, math.radians(90 + 25), 0))          # normal bisects in (+X) and out (50° up-left)
    for ob in (ln, ring):
        _key(ob, 1, location=ob.location.copy())
        _key(ob, 90, location=ob.location.copy())
        _key(ob, 112, location=ob.location + Vector((0, 4.5, 0)))
    _key(mirror, 1, location=(0, -9.0, 1.6))
    _key(mirror, 96, location=(0, -9.0, 1.6))
    _key(mirror, 120, location=(0, 0, 1.6))
    beam_m = M.emission("A3Beam", VIOLET, 8.0)
    b_in = _beam("BeamIn", (-6.0, 0, 1.6), (-0.42, 0, 1.6), 0.07, beam_m)
    _key(b_in, 1, scale=(1, 1, 0.001))
    _key(b_in, 22, scale=(1, 1, 1))
    heat = M.emission("EntryGlow", ORANGE, 0.0)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.18, minor_radius=0.05, location=(-0.42, 0, 1.6),
                                     rotation=(0, math.pi / 2, 0))
    hg = bpy.context.object
    hg.data.materials.append(heat)
    styles.tag(hg, "emitter")
    M.set_emission_strength(heat, 22, 0.0)
    M.set_emission_strength(heat, 40, 6.0)
    M.set_emission_strength(heat, 92, 6.0)
    M.set_emission_strength(heat, 100, 0.0)
    # with the mirror in place the beam goes all the way to it and bounces off
    b_in2 = _beam("BeamIn2", (-0.42, 0, 1.6), (0.0, 0, 1.6), 0.07, beam_m)
    _key(b_in2, 1, hide_render=True)
    _key(b_in2, 121, hide_render=False)
    out_dir = Vector((-math.cos(math.radians(50)), 0, math.sin(math.radians(50))))
    b_out = _beam("BeamOut", (0, 0, 1.6), tuple(Vector((0, 0, 1.6)) + out_dir * 6), 0.07, beam_m)
    _key(b_out, 1, hide_render=True)
    _key(b_out, 122, hide_render=False)
    _key(b_out, 122, scale=(1, 1, 0.001))
    _key(b_out, 140, scale=(1, 1, 1))
    for name, loc, size, st in (("BoxA", (-3, -6, 4), 6, 1.6), ("BoxB", (4, 5, 3), 5, 1.0)):
        bpy.ops.mesh.primitive_plane_add(size=size, location=loc)
        bx = bpy.context.object
        bx.rotation_euler = (Vector((0, 0, 1.6)) - Vector(loc)).to_track_quat("Z", "Y").to_euler()
        bx.data.materials.append(M.soft_emitter(name, (0.86, 0.9, 1.0), st))
        bx.visible_camera = False
        styles.tag(bx, "rig")
    B._area("Key", (3, -5, 5), (0.8, 0, 0.6), 3, 400, (0.85, 0.9, 1.0))
    B._camera("CamA3_04", [(1, (-0.6, 0, 1.6), (2.4, -6.4, 2.4), 40, 4.0), (187, (-0.4, 0, 1.8), (1.6, -6.8, 2.6), 40, 4.0)])


# ---- A3_05 ---------------------------------------------------------------------------------
def montage(sc, rnd):
    C.set_world(top=(0.02, 0.022, 0.03), horizon=(0.01, 0.011, 0.015), bottom=(0.002, 0.002, 0.003))
    steel = M.polished_steel("MonSteel", 0.25)
    dark = M.dark_anodized("MonDark")
    # 1) optical bench with an early source chamber flashing (x = 200)
    o1 = Vector((200, 0, 0))
    _box("Table", o1 + Vector((0, 0, 0.9)), (6, 2.4, 0.15), dark)
    for x in (-2.6, 2.6):
        _box(f"TLeg{x}", o1 + Vector((x, 0, 0.4)), (0.2, 2.0, 0.8), dark)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.6, location=tuple(o1 + Vector((0, 0, 1.6))))
    ch = bpy.context.object
    ch.data.materials.append(steel)
    styles.tag(ch, "structure")
    fl = M.emission("BenchFlash", (0.8, 0.7, 1.0), 0.0)
    _cyl("Port", 0.15, 0.1, tuple(o1 + Vector((0, -0.6, 1.6))), fl, rot=(math.pi / 2, 0, 0), role="emitter")
    for f in range(4, 66, 9):
        M.set_emission_strength(fl, f, 0.0)
        M.set_emission_strength(fl, f + 1, 40.0)
        M.set_emission_strength(fl, f + 4, 0.0)
    for k in range(5):
        _cyl(f"Optic{k}", 0.12, 0.6, tuple(o1 + Vector((-2.4 + 0.5 * k, 0, 1.3))), steel)
    # 2) polishing a large mirror blank on a turntable (x = 400)
    o2 = Vector((400, 0, 0))
    _cyl("PolishTable", 2.2, 0.6, tuple(o2 + Vector((0, 0, 0.3))), dark)
    blank = _cyl("Blank", 1.8, 0.35, tuple(o2 + Vector((0, 0, 0.78))), M.multilayer_mirror("Blank", r_max=1.8))
    _key(blank, 66, rotation_euler=(0, 0, 0))
    _key(blank, 130, rotation_euler=(0, 0, math.radians(120)))
    _box("Arm", o2 + Vector((1.2, 0, 2.2)), (3.0, 0.3, 0.3), steel)
    head = _cyl("PolHead", 0.35, 0.3, tuple(o2 + Vector((0.4, 0, 1.15))), steel)
    _key(head, 66, location=o2 + Vector((0.2, 0, 1.15)))
    _key(head, 130, location=o2 + Vector((1.1, 0.3, 1.15)))
    # 3) a long laser amplifier hall (x = 600)
    o3 = Vector((600, 0, 0))
    tube = M.emission("HallBeam", ORANGE, 6.0)
    for k in range(6):
        _box(f"Amp{k}", o3 + Vector((-10 + 4.2 * k, 0, 1.0)), (3.2, 1.6, 2.0), M.principled("AmpPanel", (0.82, 0.84, 0.86),
                                                                                      roughness=0.45), bevel=0.05)
    _beam("AmpBeam", o3 + Vector((-12, 0, 2.2)), o3 + Vector((14, 0, 2.2)), 0.05, tube)
    _box("HallFloor3", o3 + Vector((0, 0, -0.05)), (60, 20, 0.1), M.principled("Floor3", (0.05, 0.05, 0.06), roughness=0.15))
    # 4) clean-room assembly: fab hall with the machine and backlit people (origin)
    BM.fab_hall(people=4)
    BM.machine(with_path=False)
    # camera: four set-ups, hard cuts (constant interpolation), slow push inside each
    cam = B._camera("CamA3_05", [
        (1, tuple(o1 + Vector((0, 0, 1.4))), tuple(o1 + Vector((3.5, -5.5, 2.4))), 35, 4.0),
        (64, tuple(o1 + Vector((0, 0, 1.4))), tuple(o1 + Vector((2.8, -4.8, 2.2))), 35, 4.0),
        (65, tuple(o2 + Vector((0, 0, 0.9))), tuple(o2 + Vector((3.6, -4.6, 3.0))), 35, 4.0),
        (129, tuple(o2 + Vector((0, 0, 0.9))), tuple(o2 + Vector((3.0, -4.0, 2.6))), 35, 4.0),
        (130, tuple(o3 + Vector((2, 0, 1.6))), tuple(o3 + Vector((-13.0, -4.5, 2.2))), 24, 5.6),
        (194, tuple(o3 + Vector((4, 0, 1.6))), tuple(o3 + Vector((-11.0, -4.2, 2.1))), 24, 5.6),
        (195, (-1.0, 0, 0.8), (7.0, -9.0, 2.2), 28, 4.0),
        (259, (-1.0, 0, 0.8), (6.0, -8.0, 2.0), 28, 4.0)])
    for ob in (cam, bpy.data.objects["CamA3_05Aim"]):
        for fc in C.fcurves(ob.animation_data.action):
            pts = fc.keyframe_points
            for i, kp in enumerate(pts):
                if i % 2 == 1:
                    kp.interpolation = "CONSTANT"                     # hold, then jump at the cut
    B._area("MonKey1", tuple(o1 + Vector((2, -4, 5))), (0.8, 0, 0.5), 4, 800, (0.85, 0.9, 1.0))
    B._area("MonKey2", tuple(o2 + Vector((2, -3, 6))), (0.6, 0, 0.5), 5, 1200, (0.85, 0.9, 1.0))
    B._area("MonKey3", tuple(o3 + Vector((0, -6, 8))), (0.9, 0, 0), 20, 3000, (0.85, 0.9, 1.0))


# ---- A3_06 ---------------------------------------------------------------------------------
def tour(sc, rnd):
    path, pmat = BM.machine()
    path.data.bevel_factor_end = 0.0
    path.data.keyframe_insert("bevel_factor_end", frame=1)
    path.data.bevel_factor_end = 1.0
    path.data.keyframe_insert("bevel_factor_end", frame=125)
    B._area("MKey", (0, -9, 8), (0.9, 0, 0), 16, 2500, (0.8, 0.85, 1.0))
    B._camera("CamA3_06", [(1, BM.PLASMA, (-6.5, -7.0, 2.4), 32, 8.0), (70, BM.FACET2, (-2.6, -7.5, 3.2), 32, 8.0),
                           (135, (0.5, 0, 0.2), (1.8, -7.8, 2.0), 32, 8.0)])


def build(variant="ribbon", seed=23):
    sc = C.reset_scene(FRAMES)
    C.set_world(top=(0.03, 0.035, 0.05), horizon=(0.012, 0.014, 0.02), bottom=(0.003, 0.004, 0.006))
    C.set_color_management(exposure=0.4)
    rnd = random.Random(seed)
    {"ribbon": ribbon, "lens": lens, "montage": montage, "tour": tour}[variant](sc, rnd)
    return sc
