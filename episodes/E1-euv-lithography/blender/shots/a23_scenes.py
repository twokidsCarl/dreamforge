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
    # an exact sine built vertex by vertex: 2400 segments over 16 units (~300 per wavelength), so the crests stay
    # round even in close-up (bpy.ops.mesh.subdivide caps at 100 cuts, which left visible facets)
    lam, amp, half_w, n, x0, x1 = 2.0, 0.45, 0.035, 2400, -8.0, 8.0
    verts, faces = [], []
    for i in range(n + 1):
        x = x0 + (x1 - x0) * i / n
        z = amp * math.sin(2 * math.pi * x / lam)
        verts += [(x, -half_w, z), (x, half_w, z)]
        if i:
            faces.append((2 * i - 2, 2 * i - 1, 2 * i + 1, 2 * i))
    me = bpy.data.meshes.new("WaveRibbon")
    me.from_pydata(verts, [], faces)
    me.polygons.foreach_set("use_smooth", [True] * len(faces))
    rb = bpy.data.objects.new("WaveRibbon", me)
    sc.collection.objects.link(rb)
    # the wave travels one wavelength over the shot; its ends stay out of frame
    _key(rb, 1, location=(0, 0, 0))
    _key(rb, 60, location=(-lam * 2.5 / 1.25 / 2, 0, 0))
    for fc in C.fcurves(rb.animation_data.action):
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR"
    rb.data.materials.append(M.emission("RibbonGlow", (0.40, 0.18, 1.0), 1.8))
    styles.tag(rb, "emitter")
    # three-quarter view down the wave so it recedes into the dark; focus on the nearest crest, slow push-in
    B._camera("CamA2_08", [(1, (0.0, 0, 0.1), (-3.6, -3.0, 0.75), 50, 2.8),
                           (60, (0.2, 0, 0.1), (-2.9, -2.5, 0.62), 50, 2.8)])


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
    # a plain silver-looking face, as ZEISS photographs its EUV mirrors (the multilayer shows no visible rainbow)
    mirror = A0._cyl("Mirror", 1.3, 0.16, (0, 0, 1.6), M.polished_steel("A3MirrorSilver", 0.04),
                     rot=(0, math.radians(90 + 25), 0))          # normal bisects in (+X) and out (50° up-left)
    # the whole bench sits in a vacuum chamber: air at 1 atm absorbs half the EUV in 0.1 mm (CXRO;
    # research/visual/A3_sources.md), so a beam crossing open air would contradict the shot before
    shell = M.principled("VacGlass", (0.9, 0.93, 1.0), roughness=0.02)
    shb = shell.node_tree.nodes["Principled BSDF"]
    shb.inputs["Transmission Weight"].default_value = 1.0
    shb.inputs["IOR"].default_value = 1.05
    vac = _cyl("VacChamber", 3.1, 12.0, (-0.5, 0, 1.4), shell, rot=(0, math.pi / 2, 0), role="shell")
    vac.modifiers.new("Wall", "SOLIDIFY").thickness = 0.04
    for x in (-6.5, 5.5):
        _cyl(f"VacFlange{x}", 3.25, 0.25, (x, 0, 1.4), stand, rot=(0, math.pi / 2, 0))
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
    beam_back = M.emission("A3BeamReflected", VIOLET, 8.0 * 0.7)   # ZEISS: "up to 70 percent" reflected
    b_out = _beam("BeamOut", (0, 0, 1.6), tuple(Vector((0, 0, 1.6)) + out_dir * 2.6), 0.07, beam_back)
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
def _port(name, centre, r_body, angle, mat, flange_mat, length=0.34, r=0.12, z=0.0):
    """A radial CF-style port on a vertical vacuum chamber: tube plus end flange; returns the flange's outer centre."""
    d = Vector((math.cos(angle), math.sin(angle), 0))
    base = Vector(centre) + Vector((0, 0, z))
    _cyl(name, r, length, tuple(base + d * (r_body + length / 2 - 0.05)), mat, rot=(0, math.pi / 2, angle))
    tip = base + d * (r_body + length)
    _cyl(name + "Flange", r + 0.07, 0.06, tuple(tip), flange_mat, rot=(0, math.pi / 2, angle))
    return tip, d


def montage(sc, rnd):
    C.set_world(top=(0.02, 0.022, 0.03), horizon=(0.01, 0.011, 0.015), bottom=(0.002, 0.002, 0.003))
    steel = M.principled("MonSteel", (0.58, 0.60, 0.63), metallic=1.0, roughness=0.32)   # brushed vacuum steel
    flange = M.principled("MonFlange", (0.62, 0.64, 0.66), metallic=1.0, roughness=0.2)
    dark = M.dark_anodized("MonDark")
    # 1) early source test: a vertical vacuum chamber with radial ports on an optical table; the plasma
    #    flashes behind the viewport (x = 200). Generic lab, no specific historical set-up (audit_A3: artistic)
    o1 = Vector((200, 0, 0))
    _box("Table", o1 + Vector((0, 0, 0.9)), (6, 2.4, 0.15), M.principled("TableTop", (0.05, 0.05, 0.055),
         metallic=0.6, roughness=0.45), bevel=0.02)
    for x in (-2.6, 2.6):
        _box(f"TLeg{x}", o1 + Vector((x, 0, 0.4)), (0.3, 2.0, 0.8), dark)
    cc = o1 + Vector((0.4, 0.1, 1.62))
    _cyl("ChamberBase", 0.4, 0.14, tuple(o1 + Vector((0.4, 0.1, 1.04))), dark)
    _cyl("Chamber", 0.55, 0.9, tuple(cc), steel)
    for z in (-0.47, 0.47):
        _cyl(f"ChamberFlange{z}", 0.66, 0.07, tuple(cc + Vector((0, 0, z))), flange)
    _cyl("ChamberTopPort", 0.14, 0.3, tuple(cc + Vector((0, 0, 0.62))), steel)
    _cyl("ChamberTopFlange", 0.21, 0.06, tuple(cc + Vector((0, 0, 0.78))), flange)
    for k, ang in enumerate((math.radians(-35), math.radians(30), math.radians(150), math.radians(215))):
        _port(f"Port{k}", cc, 0.55, ang, steel, flange, z=0.12 if k % 2 else -0.1)
    tip, d = _port("ViewPort", cc, 0.55, math.radians(-100), steel, flange, length=0.3, r=0.13, z=0.05)
    fl = M.emission("BenchFlash", (0.78, 0.66, 1.0), 0.0)
    _cyl("ViewGlass", 0.12, 0.02, tuple(tip + d * 0.035), fl, rot=(0, math.pi / 2, math.radians(-100)), role="emitter")
    for f in range(4, 66, 9):                                         # the source fires in bursts
        M.set_emission_strength(fl, f, 0.0)
        M.set_emission_strength(fl, f + 1, 30.0)
        M.set_emission_strength(fl, f + 4, 0.0)
    for k in range(3):                                                # optic mounts on posts
        px = -2.0 + 0.6 * k
        _cyl(f"OptPost{k}", 0.035, 0.42, tuple(o1 + Vector((px, -0.2, 1.18))), steel)
        _cyl(f"OptMount{k}", 0.13, 0.05, tuple(o1 + Vector((px, -0.2, 1.42))), dark, rot=(0, math.pi / 2, 0))
    # 2) polishing a large mirror blank on a turntable (x = 400). ZEISS figures and polishes the bare
    #    glass-ceramic substrate first and coats it afterwards (S8), so the blank is bare glass here
    o2 = Vector((400, 0, 0))
    _cyl("PolishTable", 2.2, 0.6, tuple(o2 + Vector((0, 0, 0.3))), dark)
    sub_m = M.principled("SubstrateGlass", (0.94, 0.88, 0.78), roughness=0.01)
    sb_ = sub_m.node_tree.nodes["Principled BSDF"]
    sb_.inputs["Transmission Weight"].default_value = 0.92
    sb_.inputs["IOR"].default_value = 1.54
    blank = _cyl("Blank", 1.8, 0.32, tuple(o2 + Vector((0, 0, 0.77))), sub_m, verts=128)
    bv = blank.modifiers.new("Chamfer", "BEVEL")
    bv.width, bv.segments = 0.03, 2
    _key(blank, 66, rotation_euler=(0, 0, 0))
    _key(blank, 130, rotation_euler=(0, 0, math.radians(120)))
    _cyl("PolColumn", 0.16, 2.6, tuple(o2 + Vector((2.9, 0.9, 1.3))), steel)
    _box("Arm", o2 + Vector((1.6, 0.45, 2.45)), (2.9, 0.22, 0.22), steel, bevel=0.03)
    head = _cyl("PolHead", 0.38, 0.16, tuple(o2 + Vector((0.4, 0, 1.03))), steel)
    pad = _cyl("PolPad", 0.38, 0.03, (0, 0, -0.095), M.principled("Pad", (0.16, 0.1, 0.07), roughness=0.8))
    spindle = _cyl("Spindle", 0.06, 1.35, (0, 0, 0.75), steel)
    for ob in (pad, spindle):
        ob.parent = head
    _key(head, 66, location=o2 + Vector((0.2, 0, 1.03)))
    _key(head, 130, location=o2 + Vector((1.1, 0.3, 1.03)))
    # an unseen soft box the polished face mirrors toward the camera, so the surface reads as optical quality
    bpy.ops.mesh.primitive_plane_add(size=5, location=tuple(o2 + Vector((-3.8, 4.4, 3.6))))
    sbx = bpy.context.object
    sbx.rotation_euler = (o2 + Vector((0, 0, 0.9)) - sbx.location).to_track_quat("Z", "Y").to_euler()
    sbx.data.materials.append(M.soft_emitter("PolishBox", (0.9, 0.93, 1.0), 2.2))
    sbx.visible_camera = False
    styles.tag(sbx, "rig")
    # 3) the drive-laser amplifier chain (x = 600): seed, pre-amplifier, four amplifiers (S7) as a stylised row;
    #    the infrared CO2 beam runs inside a closed beam tube, view ports glow in the film's laser orange
    o3 = Vector((600, 0, 0))
    tube = M.emission("HallBeam", ORANGE, 6.0)
    panel = M.principled("AmpPanel", (0.80, 0.82, 0.84), roughness=0.42)
    seam = M.principled("AmpSeam", (0.12, 0.12, 0.13), roughness=0.6)
    led = M.emission("AmpLED", (0.3, 0.85, 1.0), 4.0)
    tsteel = M.principled("TubeSteel", (0.6, 0.62, 0.65), metallic=0.9, roughness=0.3)
    for k in range(6):
        x = -10 + 4.2 * k
        _box(f"Amp{k}", o3 + Vector((x, 0, 1.0)), (3.2, 1.6, 2.0), panel, bevel=0.05)
        for sx in (-0.53, 0.53):                                       # door seams on the aisle face
            _box(f"AmpSeam{k}{sx}", o3 + Vector((x + sx, -0.801, 1.0)), (0.012, 0.004, 1.8), seam, bevel=0)
        _box(f"AmpLED{k}", o3 + Vector((x + 1.25, -0.803, 1.75)), (0.1, 0.004, 0.03), led, role="emitter", bevel=0)
        _cyl(f"AmpFeed{k}", 0.1, 0.24, tuple(o3 + Vector((x, 0, 2.1))), tsteel)   # beam in/out of each unit
    _cyl("BeamTube", 0.22, 26.0, tuple(o3 + Vector((1, 0, 2.2))), tsteel, rot=(0, math.pi / 2, 0))
    for k in range(7):
        _cyl(f"TubePort{k}", 0.08, 0.46, tuple(o3 + Vector((-11 + 4 * k, 0, 2.2))), tube, rot=(math.pi / 2, 0, 0),
             role="emitter")
    _box("HallFloor3", o3 + Vector((0, 0, -0.05)), (60, 20, 0.1), M.principled("Floor3", (0.05, 0.05, 0.06), roughness=0.15))
    lamp3 = M.emission("HallLamp3", (0.92, 0.95, 1.0), 5.0)
    for k in range(5):                                                 # ceiling strips mirrored in the floor
        _box(f"Lamp3_{k}", o3 + Vector((-12 + 6 * k, -2.5, 5.5)), (0.2, 3.0, 0.08), lamp3, role="env", bevel=0)
    # 4) clean-room assembly: fab hall with the machine and backlit people (origin)
    BM.fab_hall(people=4)
    BM.machine(with_path=False)
    import figures
    sil = bpy.data.materials["Silhouette"]
    figures.person("Fitter0", (1.4, -2.3, -2.2), pose="work", facing=180, mat=sil)       # at the open panels
    figures.person("Fitter1", (4.6, -2.9, -2.2), height=1.7, pose="stand", facing=150, mat=sil)
    cx = BM.CENTER[0]
    # camera: four set-ups, hard cuts (constant interpolation), slow push inside each
    cam = B._camera("CamA3_05", [
        (1, tuple(o1 + Vector((0.2, 0, 1.55))), tuple(o1 + Vector((2.6, -4.6, 2.3))), 40, 2.8),
        (64, tuple(o1 + Vector((0.3, 0, 1.55))), tuple(o1 + Vector((2.1, -3.9, 2.1))), 40, 2.8),
        (65, tuple(o2 + Vector((0, 0, 0.85))), tuple(o2 + Vector((3.2, -3.6, 1.75))), 40, 4.0),
        (129, tuple(o2 + Vector((0, 0, 0.85))), tuple(o2 + Vector((2.7, -3.1, 1.6))), 40, 4.0),
        (130, tuple(o3 + Vector((2, 0, 1.6))), tuple(o3 + Vector((-13.0, -4.5, 2.2))), 24, 5.6),
        (194, tuple(o3 + Vector((4, 0, 1.6))), tuple(o3 + Vector((-11.0, -4.2, 2.1))), 24, 5.6),
        (195, (cx - 0.5, 0, 0.9), (cx + 7.5, -12.8, 2.6), 24, 5.6),       # inside the column line (y = -14)
        (259, (cx - 0.5, 0, 0.9), (cx + 6.8, -12.0, 2.4), 24, 5.6)])
    for ob in (cam, bpy.data.objects["CamA3_05Aim"]):
        for fc in C.fcurves(ob.animation_data.action):
            pts = fc.keyframe_points
            for i, kp in enumerate(pts):
                if i % 2 == 1:
                    kp.interpolation = "CONSTANT"                     # hold, then jump at the cut
    B._area("MonKey1", tuple(o1 + Vector((2, -4, 5))), (0.8, 0, 0.5), 4, 600, (0.85, 0.9, 1.0))
    B._area("MonRim1", tuple(o1 + Vector((-1.5, 3.5, 3.5))), (-0.9, 0, 3.4), 3, 400, (0.8, 0.85, 1.0))
    B._area("MonKey2", tuple(o2 + Vector((2, -3, 6))), (0.6, 0, 0.5), 5, 900, (0.85, 0.9, 1.0))
    B._area("MonKey3", tuple(o3 + Vector((0, -6, 8))), (0.9, 0, 0), 20, 3000, (0.85, 0.9, 1.0))


# ---- A3_06 ---------------------------------------------------------------------------------
def tour(sc, rnd):
    path, pmat = BM.machine()
    path.data.bevel_factor_end = 0.0
    path.data.keyframe_insert("bevel_factor_end", frame=1)
    path.data.bevel_factor_end = 1.0
    path.data.keyframe_insert("bevel_factor_end", frame=125)
    B._area("MKey", (BM.CENTER[0], -9, 8), (0.9, 0, 0), 16, 2500, (0.8, 0.85, 1.0))
    # follow the light: source unit (+x) -> illuminator -> reticle -> projection optics and wafer (x ~ 0)
    px, f1 = BM.PLASMA, BM.FACET1
    B._camera("CamA3_06", [(1, px, (px[0] + 1.0, -7.5, px[2] + 1.6), 32, 8.0),
                           (70, f1, (f1[0] - 0.4, -8.0, f1[2] + 0.6), 32, 8.0),
                           (135, (0.0, 0, 0.6), (-1.0, -8.5, 2.2), 32, 8.0)])


def build(variant="ribbon", seed=23):
    sc = C.reset_scene(FRAMES)
    C.set_world(top=(0.03, 0.035, 0.05), horizon=(0.012, 0.014, 0.02), bottom=(0.003, 0.004, 0.006))
    C.set_color_management(exposure=0.4)
    rnd = random.Random(seed)
    {"ribbon": ribbon, "lens": lens, "montage": montage, "tour": tour}[variant](sc, rnd)
    return sc
