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
EUV_BEAM = (0.30, 0.04, 1.0)           # saturated EUV violet: at moderate strength it stays violet in AgX, not white


def _rod(name, origin, radius, mat, rot_y=0.0, role="emitter"):
    """Unit-length cylinder along local +X starting at its origin: scale.x is the beam length, so it grows from
    its start (a centred cylinder scaled from zero leaves a bright dot in mid-air)."""
    from mathutils import Matrix
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=1.0, vertices=32, location=(0, 0, 0))
    ob = bpy.context.object
    ob.name = name
    ob.data.transform(Matrix.Translation((0, 0, 0.5)))
    ob.data.transform(Matrix.Rotation(math.pi / 2, 4, "Y"))        # local +Z -> +X
    for p in ob.data.polygons:
        p.use_smooth = True
    ob.location = origin
    ob.rotation_euler = (0, rot_y, 0)
    ob.data.materials.append(mat)
    styles.tag(ob, role)
    return ob


def lens(sc, rnd):
    from mathutils import Matrix
    n = 195
    try:
        import a1_scenes
        n = a1_scenes._shot_frames("A3_04", 195)
    except Exception:
        pass
    C.set_world(top=(0.01, 0.012, 0.018), horizon=(0.005, 0.006, 0.009), bottom=(0.001, 0.001, 0.002))
    ZB = 1.6                                                       # beam height
    stand = M.dark_anodized("Stand")
    steel = M.principled("ChamberSteel", (0.62, 0.63, 0.66), metallic=1.0, roughness=0.36)
    flange = M.principled("ChamberFlange", (0.70, 0.71, 0.73), metallic=1.0, roughness=0.22)
    # --- the vacuum chamber, seen from inside: air at 1 atm absorbs half the EUV in 0.1 mm (CXRO; A3_sources S3,
    #     S4), so the whole bench sits in a steel vessel: stiffener rings, CF ports, viewports, an end-cap inlet
    bpy.ops.mesh.primitive_cylinder_add(radius=4.6, depth=16.0, vertices=128, end_fill_type="NOTHING",
                                        location=(-0.5, 0, 1.4), rotation=(0, math.pi / 2, 0))
    vessel = bpy.context.object
    vessel.name = "VacChamber"
    vessel.data.polygons.foreach_set("use_smooth", [True] * len(vessel.data.polygons))
    vessel.modifiers.new("Wall", "SOLIDIFY").thickness = 0.12
    vessel.data.materials.append(steel)
    styles.tag(vessel, "structure")
    for x in (-6.0, -3.5, -1.0, 1.5, 4.0, 6.5):
        bpy.ops.mesh.primitive_torus_add(major_radius=4.56, minor_radius=0.07, major_segments=128,
                                         location=(x, 0, 1.4), rotation=(0, math.pi / 2, 0))
        rr = bpy.context.object
        rr.name = f"VacRib{x}"
        rr.data.materials.append(flange)
        styles.tag(rr, "structure")
    for x in (-8.5, 7.5):                                          # end caps
        _cyl(f"VacCap{x}", 4.7, 0.16, (x, 0, 1.4), steel, rot=(0, math.pi / 2, 0), verts=128)
    glass_dark = M.principled("ViewportGlass", (0.02, 0.025, 0.035), roughness=0.05)
    port_glow = M.emission("ViewportGlow", (0.55, 0.68, 0.85), 0.9)
    for k, (x, ang, r) in enumerate(((-3.0, 70, 0.42), (0.6, 105, 0.55), (3.2, 80, 0.38), (5.6, 120, 0.3),
                                     (-1.6, 145, 0.3))):
        a_ = math.radians(ang)                                     # angle around the axis, 90 = straight back (+y)
        d = Vector((0, math.cos(a_ - math.pi / 2) * -1, 0))
        dirv = Vector((0, math.sin(a_), math.cos(a_)))             # outward normal of the wall at that angle
        c = Vector((x, 0, 1.4)) + dirv * 4.5
        rot = dirv.to_track_quat("Z", "Y").to_euler()
        f_ = _cyl(f"PortFlange{k}", r + 0.16, 0.12, tuple(c), flange, verts=64)
        f_.rotation_euler = rot
        for j in range(8):                                         # CF bolt circle
            bpy.ops.mesh.primitive_cylinder_add(radius=0.025, depth=0.05, vertices=12)
            bolt = bpy.context.object
            bolt.parent = f_
            bolt.location = ((r + 0.08) * math.cos(j * math.pi / 4), (r + 0.08) * math.sin(j * math.pi / 4), -0.07)
            bolt.data.materials.append(flange)
            styles.tag(bolt, "structure")
        g = _cyl(f"PortGlass{k}", r, 0.02, tuple(c - dirv * 0.07), port_glow if k in (1, 3) else glass_dark,
                 verts=64, role="emitter" if k in (1, 3) else "structure")
        g.rotation_euler = rot
    _cyl("BeamInletFlange", 0.42, 0.14, (-8.35, 0, ZB), flange, rot=(0, math.pi / 2, 0))
    _cyl("BeamInlet", 0.2, 0.05, (-8.27, 0, ZB), glass_dark, rot=(0, math.pi / 2, 0))
    # --- optical bench on two pedestals, a linear stage across the beam carrying the lens and the mirror
    _box("Bench", (-1.5, 0, -0.65), (11, 3.0, 0.12), M.principled("BenchTop", (0.05, 0.05, 0.06), roughness=0.4),
         bevel=0.02)
    for x in (-5.5, 2.5):
        _box(f"Pedestal{x}", (x, 0, -2.0), (0.8, 1.6, 2.6), stand)
    for y in (-0.35, 0.35):
        _box(f"Rail{y}", (0, y - 1.2, -0.55), (0.12, 7.0, 0.08), flange, bevel=0.01)
    bpy.ops.object.empty_add(location=(0, 0, 0))
    car = bpy.context.object
    car.name = "Changer"
    sp = 2.9                                                       # lens at y = 0, mirror waiting at y = -sp
    parts = [_box("Carriage", (0, -sp / 2, -0.47), (1.1, sp + 1.6, 0.1), stand, bevel=0.015)]
    glass = M.principled("OpticalGlass", (0.97, 0.98, 1.0), roughness=0.0)
    gb = glass.node_tree.nodes["Principled BSDF"]
    gb.inputs["Transmission Weight"].default_value = 1.0
    gb.inputs["IOR"].default_value = 1.5
    LR, LD = 1.4, 0.448                                            # lens radius, half thickness at the centre
    bpy.ops.mesh.primitive_uv_sphere_add(radius=LR, segments=96, ring_count=48, location=(0, 0, ZB))
    ln = bpy.context.object
    ln.name = "Lens"
    ln.scale = (LD / LR, 1.0, 1.0)
    ln.data.polygons.foreach_set("use_smooth", [True] * len(ln.data.polygons))
    ln.data.materials.append(glass)
    styles.tag(ln, "structure")
    ring = _cyl("LensRing", 1.47, 0.22, (0, 0, ZB), stand, rot=(0, math.pi / 2, 0), verts=96)
    ring.modifiers.new("Hollow", "SOLIDIFY").thickness = 0.08
    parts += [ln, ring, _cyl("LensPost", 0.07, ZB - 1.47 + 0.43, (0, 0, (ZB - 1.47 - 0.43) / 2), stand)]
    # a plain silver-looking face, as ZEISS photographs its EUV mirrors (the multilayer shows no visible rainbow).
    # Angle of incidence 12 deg (beam back up at 24 deg): EUV imaging mirrors work near normal incidence
    AOI = math.radians(12)
    mirror = _cyl("Mirror", 1.3, 0.16, (0, -sp, ZB), M.polished_steel("A3MirrorSilver", 0.04),
                  rot=(0, math.pi / 2 + AOI, 0), verts=128)
    mz = ZB - 1.3 * math.cos(AOI) - 0.05
    parts += [mirror,
              _cyl("MirrorPost", 0.07, mz + 0.43, (0, -sp, (mz - 0.43) / 2), stand),
              _box("MirrorClamp", (0.0, -sp, mz + 0.02), (0.5, 0.22, 0.14), stand, bevel=0.02)]
    for ob in parts:
        ob.parent = car
    _key(car, 1, location=(0, 0, 0))
    _key(car, 96, location=(0, 0, 0))
    _key(car, 124, location=(0, sp, 0))                            # the mirror takes the lens's place
    fc_y = next(fc for fc in C.fcurves(car.animation_data.action) if fc.data_path == "location" and fc.array_index == 1)
    # --- beams. Incoming: 2.5; reflected: 0.7 x 2.5 (ZEISS: "up to 70 percent" usable after a Mo/Si mirror)
    x0 = -8.2
    n_m = Vector((-math.cos(AOI), 0, math.sin(AOI)))               # mirror front normal (towards the beam)
    x_hit = -0.08 / math.cos(AOI)                                  # beam meets the mirror face (thickness 0.16)
    beam_m = M.emission("A3Beam", EUV_BEAM, 1.3)
    b_in = _rod("BeamIn", (x0, 0, ZB), 0.05, beam_m)
    out_ang = 2 * AOI
    beam_back = M.emission("A3BeamReflected", EUV_BEAM, 1.3 * 0.7)
    b_out = _rod("BeamOut", (x_hit, 0, ZB), 0.05, beam_back, rot_y=-(math.pi - out_ang))
    for ob in (b_in, b_out):            # the glow is a stand-in for invisible EUV: no glints of it in the glass or
        ob.visible_glossy = False       # the waiting mirror (a violet line seen 'inside' the lens would read as
        ob.visible_transmission = False  # light passing through it)
        ob.visible_diffuse = False
    f_cover = None
    for f in range(1, n + 25):
        s_ = fc_y.evaluate(f)
        if abs(s_) < LR:                                           # the lens still covers the axis
            x_end = -LD * math.sqrt(max(0.0, 1 - (s_ / LR) ** 2))
        else:
            x_end = x_hit
            if f_cover is None and abs(s_ - sp) < 1.3:
                f_cover = f
        grow = min(1.0, max(0.0, (f - 1) / 20.0))
        b_in.scale = (max(1e-3, (x_end - x0) * (grow ** 0.7)), 1, 1)
        b_in.keyframe_insert("scale", frame=f)
    f_cover = f_cover or 112
    _key(b_in, 1, hide_render=True)
    _key(b_in, 2, hide_render=False)
    _key(b_out, 1, hide_render=True, scale=(1e-3, 1, 1))
    _key(b_out, f_cover, hide_render=False, scale=(1e-3, 1, 1))
    _key(b_out, f_cover + 14, scale=(3.4, 1, 1))
    # warm glow where the EUV dies in the first ~0.1 um of glass (artistic heat cue), on the camera side; it goes
    # away (hidden, not left as an unlit ring) as soon as the stage starts to move
    heat = M.emission("EntryGlow", ORANGE, 0.0)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.13, minor_radius=0.035, location=(-LD - 0.01, 0, ZB),
                                     rotation=(0, math.pi / 2, 0))
    hg = bpy.context.object
    hg.data.materials.append(heat)
    styles.tag(hg, "emitter")
    M.set_emission_strength(heat, 20, 0.0)
    M.set_emission_strength(heat, 34, 3.0)
    M.set_emission_strength(heat, 92, 3.0)
    M.set_emission_strength(heat, 96, 0.0)
    _key(hg, 1, hide_render=True)
    _key(hg, 20, hide_render=False)
    _key(hg, 97, hide_render=True)
    # --- light inside the vessel
    B._area("VacKey", (-1.5, -1.8, 5.2), (0.35, 0, 0.2), 4, 900, (0.9, 0.93, 1.0))
    B._area("VacFill", (-5.5, -3.0, 2.0), (1.2, 0, -1.1), 3, 160, (0.85, 0.9, 1.0))
    B._area("VacBack", (2.5, 2.5, 4.5), (-0.7, 0, 2.4), 3, 260, (0.85, 0.9, 1.0))
    # camera on the reflecting side (-x), inside the vessel: lens first, the mirror slides in from the right and the
    # bounce point faces the lens; a slow arc
    cam = B._camera("CamA3_04", [(1, (-0.9, 0.3, 1.5), (-4.5, -3.3, 2.6), 35, 4.0),
                                 (n + 25, (-0.7, -0.2, 1.75), (-4.0, -3.8, 2.8), 35, 4.0)])
    for ob in (cam, bpy.data.objects["CamA3_04Aim"]):
        for fc in C.fcurves(ob.animation_data.action):
            for kp in fc.keyframe_points:
                kp.interpolation = "LINEAR"


# ---- A3_05 ---------------------------------------------------------------------------------
def _port(name, centre, r_body, angle, mat, flange_mat, length=0.34, r=0.12, z=0.0):
    """A radial CF-style port on a vertical vacuum chamber: tube plus end flange; returns the flange's outer centre."""
    d = Vector((math.cos(angle), math.sin(angle), 0))
    base = Vector(centre) + Vector((0, 0, z))
    _cyl(name, r, length, tuple(base + d * (r_body + length / 2 - 0.05)), mat, rot=(0, math.pi / 2, angle))
    tip = base + d * (r_body + length)
    _cyl(name + "Flange", r + 0.07, 0.06, tuple(tip), flange_mat, rot=(0, math.pi / 2, angle))
    return tip, d


FONT = "/System/Library/Fonts/STHeiti Medium.ttc"


def _montage_overlay(cam, lens_keys, n=246):
    """A3_05's promised graphics, drawn in the shot (storyboard: 画面底部一条时间轴从 1 年滚到 17 年，欧元计数器滚到
    "60 多亿"; ASML: "more than EUR 6 billion in EUV R&D over 17 years", F20). Relative years only - ASML gives no start
    or end year. Everything rides on a rig parented to the camera at a distance proportional to the focal length, so
    sizes stay fixed in frame across the cuts (40 mm / 24 mm). Coordinates below are in 1080p pixels.
    The counter sits upper left: the upper right carries edit_film's label."""
    rig = bpy.data.objects.new("OverlayRig", None)
    bpy.context.scene.collection.objects.link(rig)
    rig.parent = cam
    for f, lens in lens_keys:
        rig.location = (0, 0, -lens / 40.0)
        rig.keyframe_insert("location", frame=f)
    for fc in C.fcurves(rig.animation_data.action):
        for kp in fc.keyframe_points:
            kp.interpolation = "CONSTANT"
    HW = 18.0 / 40.0                                                # half frame width at distance lens/40
    PX = 2 * HW / 1920.0                                            # one 1080p pixel in rig units

    def at(x, y):
        return ((x - 960) * PX, (540 - y) * PX, 0.0)
    try:
        fnt = bpy.data.fonts.load(FONT, check_existing=True)
    except Exception:
        fnt = None
    ink = M.emission("OvInk", (0.93, 0.94, 0.98), 0.75)
    dim = M.emission("OvDim", (0.62, 0.66, 0.78), 0.6)
    vio = M.emission("OvViolet", (0.30, 0.06, 1.0), 0.9)
    scrim = bpy.data.materials.new("OvScrim")
    scrim.use_nodes = True
    nt = scrim.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    mix = nt.nodes.new("ShaderNodeMixShader")
    mix.inputs[0].default_value = 0.86
    nt.links.new(nt.nodes.new("ShaderNodeBsdfTransparent").outputs[0], mix.inputs[1])
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (0, 0, 0, 1)
    nt.links.new(em.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])

    def obj(name, data, mat, xy, z=0.0):
        ob = bpy.data.objects.new(name, data)
        bpy.context.scene.collection.objects.link(ob)
        ob.parent = rig
        x, y, _ = at(*xy)
        ob.location = (x, y, z)
        if mat:
            ob.data.materials.append(mat)
        styles.tag(ob, "emitter")
        for a in ("visible_diffuse", "visible_glossy", "visible_transmission", "visible_shadow"):
            setattr(ob, a, False)
        return ob

    def rect(name, x0, y0, x1, y1, mat, z=0.0):
        me = bpy.data.meshes.new(name)
        w, h = (x1 - x0) * PX / 2, (y1 - y0) * PX / 2
        me.from_pydata([(-w, -h, 0), (w, -h, 0), (w, h, 0), (-w, h, 0)], [], [(0, 1, 2, 3)])
        return obj(name, me, mat, ((x0 + x1) / 2, (y0 + y1) / 2), z)

    def text(name, body, px, mat, xy, align="LEFT"):
        cu = bpy.data.curves.new(name, "FONT")
        cu.body = body
        cu.size = px * PX / 0.86                                    # CJK glyphs fill ~0.86 em
        cu.align_x, cu.align_y = align, "CENTER"
        if fnt:
            cu.font = fnt
        return obj(name, cu, mat, xy, 0.0005)

    def show(ob, f_on, f_off=None):
        ob.hide_render = True
        ob.keyframe_insert("hide_render", frame=1)
        ob.hide_render = False
        ob.keyframe_insert("hide_render", frame=max(1, f_on))
        if f_off is not None:
            ob.hide_render = True
            ob.keyframe_insert("hide_render", frame=f_off)

    # time bar above the subtitle band (subtitles start at y ~934): track, 17 year ticks, violet fill, year readout
    x0, x1, yb = 300, 1620, 850
    f0, f1 = 8, 232                                                 # 1 -> 17 years across the four vignettes
    rect("OvBarScrim", x0 - 40, yb - 64, x1 + 40, yb + 30, scrim, -0.0005)
    rect("OvTrack", x0, yb - 2, x1, yb + 2, dim)
    for y_ in range(17):
        xt = x0 + (x1 - x0) * y_ / 16
        rect(f"OvTick{y_}", xt - 1.5, yb - 9, xt + 1.5, yb + 9, dim)
    fill = rect("OvFill", x0, yb - 5, x0 + (x1 - x0), yb + 5, vio, 0.0002)
    me = fill.data                                                  # grow from the left end: origin at x0
    for v in me.vertices:
        v.co.x += (x1 - x0) * PX / 2
    fill.location.x = at(x0, yb)[0]
    for f, u in ((1, 0.0), (f0, 0.0), (f1, 1.0)):
        fill.scale = (max(1e-3, u), 1, 1)
        fill.keyframe_insert("scale", frame=f)
    for y_ in range(1, 18):                                         # readout rides at the head of the fill
        u0 = (y_ - 1) / 16
        fa = int(f0 + (f1 - f0) * u0)
        fb = int(f0 + (f1 - f0) * (y_ / 16)) if y_ < 17 else None
        t = text(f"OvYearN{y_}", f"{y_} 年", 36 if y_ == 17 else 30, ink, (x0 + (x1 - x0) * u0, yb - 34), align="CENTER")
        show(t, fa, fb)
    # euro counter, upper left: rolls up with the narration (投入了 60 多亿欧元 ~ 4-5.5 s) and holds
    solid = scrim.copy()                                            # opaque: the clean room's ceiling strips are
    solid.name = "OvScrimSolid"                                     # far too bright for a see-through plate
    solid.node_tree.nodes["Mix Shader"].inputs[0].default_value = 0.97
    rect("OvCountScrim", 96, 70, 600, 196, solid, -0.0005)
    text("OvCountLab", "投入", 30, dim, (130, 104))
    vals = [0, 2, 4, 7, 10, 14, 18, 23, 28, 33, 38, 43, 47, 51, 54, 57, 59]
    fr = 96
    for i, v in enumerate(vals):
        t = text(f"OvCount{i}", f"{v} 亿欧元", 56, ink, (130, 156))
        show(t, fr, fr + 2)
        fr += 2
    show(text("OvCountEnd", "60 多亿欧元", 56, ink, (130, 156)), fr)
    show(bpy.data.objects["OvCountScrim"], 96)
    show(bpy.data.objects["OvCountLab"], 96)
    return rig


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
    # a closed hall: floor well past the view, back and side walls, a ceiling the lamp strips hang from (no void)
    _box("HallFloor3", o3 + Vector((0, -4, -0.05)), (90, 40, 0.1), M.principled("Floor3", (0.05, 0.05, 0.06), roughness=0.15))
    wall3 = M.principled("HallWall3", (0.42, 0.44, 0.47), roughness=0.55)
    _box("HallBack3", o3 + Vector((0, 3.2, 3.2)), (90, 0.2, 6.6), wall3)
    _box("HallFront3", o3 + Vector((0, -16, 3.2)), (90, 0.2, 6.6), wall3)
    _box("HallEnd3", o3 + Vector((26, -6, 3.2)), (0.2, 40, 6.6), wall3)
    _box("HallStart3", o3 + Vector((-30, -6, 3.2)), (0.2, 40, 6.6), wall3)
    _box("HallCeil3", o3 + Vector((0, -6, 6.45)), (90, 40, 0.1), M.principled("HallCeil3", (0.3, 0.31, 0.33), roughness=0.7))
    for k in range(10):                                                # wall panel seams on the back wall
        _box(f"HallSeam3_{k}", o3 + Vector((-22 + 5 * k, 3.09, 3.2)), (0.03, 0.02, 6.4), seam, bevel=0)
    lamp3 = M.emission("HallLamp3", (0.92, 0.95, 1.0), 5.0)
    for k in range(8):                                                 # ceiling strips mirrored in the floor
        _box(f"Lamp3_{k}", o3 + Vector((-16 + 6 * k, -2.5, 6.36)), (0.2, 3.0, 0.08), lamp3, role="env", bevel=0)
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
    for ad in (cam.animation_data, bpy.data.objects["CamA3_05Aim"].animation_data, cam.data.animation_data):
        for fc in C.fcurves(ad.action):                               # location, aim and lens all hold, then jump
            pts = fc.keyframe_points
            for i, kp in enumerate(pts):
                if i % 2 == 1:
                    kp.interpolation = "CONSTANT"                     # hold, then jump at the cut
    cam.data.dof.use_dof = False                                       # the on-screen time bar rides on the camera
    _montage_overlay(cam, lens_keys=[(1, 40), (65, 40), (130, 24), (195, 24)])
    B._area("MonKey1", tuple(o1 + Vector((2, -4, 5))), (0.8, 0, 0.5), 4, 600, (0.85, 0.9, 1.0))
    B._area("MonRim1", tuple(o1 + Vector((-1.5, 3.5, 3.5))), (-0.9, 0, 3.4), 3, 400, (0.8, 0.85, 1.0))
    B._area("MonKey2", tuple(o2 + Vector((2, -3, 6))), (0.6, 0, 0.5), 5, 900, (0.85, 0.9, 1.0))
    B._area("MonKey3", tuple(o3 + Vector((0, -6, 8))), (0.9, 0, 0), 20, 3000, (0.85, 0.9, 1.0))


# ---- A3_06 ---------------------------------------------------------------------------------
TOUR_DRAW = (1, 125)                    # frames over which the violet path draws from the collector to the wafer
TOUR_MODULES = (("SrcDrum", 0), ("Illuminator", 2), ("ReticleStage", 5), ("POBarrel", 6), ("WaferStage", 13))


def _path_frac():
    """Cumulative length fraction of every BM.PATH point (the bevel is mapped by spline length)."""
    pts = [Vector(p) for p in BM.PATH]
    seg = [(b - a).length for a, b in zip(pts, pts[1:])]
    tot = sum(seg)
    out, acc = [0.0], 0.0
    for d in seg:
        acc += d
        out.append(acc / tot)
    return out


def tour(sc, rnd):
    path, pmat = BM.machine()
    path.data.bevel_depth = 0.035                              # colour: styles.xray makes rays saturated violet
    path.data.bevel_factor_mapping_end = "SPLINE"               # by length, so module timings below are exact
    path.data.bevel_factor_end = 0.0
    path.data.keyframe_insert("bevel_factor_end", frame=TOUR_DRAW[0])
    path.data.bevel_factor_end = 1.0
    path.data.keyframe_insert("bevel_factor_end", frame=TOUR_DRAW[1])
    for fc in C.fcurves(path.data.animation_data.action):
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR"
    B._area("MKey", (BM.CENTER[0], -9, 8), (0.9, 0, 0), 16, 2500, (0.8, 0.85, 1.0))
    # follow the light: source unit (+x) -> illuminator -> reticle and projection optics -> pull back until the whole
    # path, source to wafer, is in frame (A3_07 starts from this last frame). The last key lies past the shot end
    px = BM.PLASMA
    B._camera("CamA3_06", [(1, px, (px[0] + 1.0, -7.5, px[2] + 1.6), 32, 8.0),
                           (55, (2.4, 0, 1.9), (2.3, -8.6, 2.7), 32, 8.0),
                           (105, (0.5, 0, 1.2), (0.4, -9.0, 2.1), 32, 8.0),
                           (170, (3.35, 0, 1.25), (3.6, -11.3, 2.6), 32, 8.0)])


def _tour_glow():
    """Each module lights up (a soft violet glow added to its own surface) as the path reaches it, then settles:
    the storyboard's glowing module cores. Applied after the xray style has assigned the ghost-glass shells."""
    fr = _path_frac()
    f0, f1 = TOUR_DRAW
    for name, idx in TOUR_MODULES:
        ob = bpy.data.objects.get(name)
        if ob is None or not ob.material_slots:
            continue
        f_hit = int(round(f0 + (f1 - f0) * fr[idx]))
        for slot in ob.material_slots:
            if not slot.material or not slot.material.use_nodes:
                continue
            m = slot.material.copy()
            m.name = f"{slot.material.name}_{name}Glow"
            slot.material = m
            nt = m.node_tree
            outn = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
            if not outn.inputs["Surface"].is_linked:
                continue
            src = outn.inputs["Surface"].links[0].from_socket
            em = nt.nodes.new("ShaderNodeEmission")
            em.inputs["Color"].default_value = (0.42, 0.22, 1.0, 1.0)
            add = nt.nodes.new("ShaderNodeAddShader")
            nt.links.new(src, add.inputs[0])
            nt.links.new(em.outputs[0], add.inputs[1])
            nt.links.new(add.outputs[0], outn.inputs["Surface"])
            st = em.inputs["Strength"]
            for f, v in ((1, 0.0), (max(1, f_hit - 4), 0.0), (f_hit + 3, 0.4), (f_hit + 24, 0.14)):
                st.default_value = v
                st.keyframe_insert("default_value", frame=f)


def after_style(style, shot_id):
    sc = bpy.context.scene
    if shot_id == "A3_04":
        # clear glass in front of a lit steel wall needs enough transmission / glossy bounces (a starved path reads
        # as an opaque black puck)
        sc.cycles.max_bounces = 24
        sc.cycles.transmission_bounces = 16
        sc.cycles.glossy_bounces = 8
        sc.cycles.transparent_max_bounces = 16
    if shot_id == "A3_06":
        _tour_glow()
    if shot_id == "A3_05":
        # hard cuts: the shutter opens on the frame, so the first frame after a cut never blends in the old set-up
        sc.render.motion_blur_position = "START"
        sc.cycles.transparent_max_bounces = 16


def build(variant="ribbon", seed=23):
    sc = C.reset_scene(FRAMES)
    C.set_world(top=(0.03, 0.035, 0.05), horizon=(0.012, 0.014, 0.02), bottom=(0.003, 0.004, 0.006))
    C.set_color_management(exposure=0.4)
    rnd = random.Random(seed)
    {"ribbon": ribbon, "lens": lens, "montage": montage, "tour": tour}[variant](sc, rnd)
    return sc
