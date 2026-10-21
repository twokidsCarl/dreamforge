"""B1 sample: tin droplet + double pulse, cut as six shots from one continuous simulation.

Scene timeline (24 fps):
  1-100    droplet stream flies from the generator to the plasma site (speed ramp into slow-mo)
  100      pre-pulse arrives; droplet flattens into a ~300 um sheet (F4b) that drifts downstream
  192      main pulse; plasma burst, glowing debris, collector lights up, EUV bundle to IF
  262-346  stream resumes: the next droplet approaches (every 20 us in reality, F2)

CUTS lists (camera, first scene frame, last scene frame); shared/tools/edit_sample.py assembles them.
"""
import math
import random

import bpy

import build_source as S
import build_vacuum as V
import common as C
import materials as M

FRAME_END = 346
T_ARRIVE = 100
T_PRE = 100
T_MAIN = 192
PLASMA_X = 0.35
NOZZLE_Y = -300.0                    # off-screen: really ~0.3 m (2400 units) from the plasma

CUTS = [
    ("CamEstablish", 1, 64),
    ("CamNozzle", 28, 88),
    ("CamPrePulse", 86, 132),
    ("CamSheet", 128, 190),
    ("CamPlasma", 187, 258),
    ("CamReveal", 246, 346),
    ("CamLaserPOV", 84, 98),
    ("CamMainPOV", 183, 191),
    ("CamDebris", 222, 246),
    ("CamCollector", 240, 268),
]


def _key(obj, frame, **props):
    for k, v in props.items():
        setattr(obj, k, v)
        obj.keyframe_insert(k, frame=frame)


def _area(name, loc, rot, size, energy, color, size_y=None):
    bpy.ops.object.light_add(type="AREA", location=loc, rotation=rot)
    lt = bpy.context.object
    lt.name = name
    lt.data.shape = "RECTANGLE"
    lt.data.size = size
    lt.data.size_y = size_y or size
    lt.data.energy = energy
    lt.data.color = color
    return lt


def _lights(tin_objs):
    _area("Key", (2.0, 1.5, 7.0), (0.25, 0.15, 0), 5.0, 320, (0.62, 0.76, 1.0))
    _area("Fill", (6.0, 6.0, 2.0), (1.3, 0, 2.35), 8.0, 260, (0.75, 0.82, 1.0))
    _area("Rim", (-5.0, -4.0, 2.5), (1.2, 0, -2.3), 4.0, 520, (0.45, 0.85, 1.0))
    _area("NozzleKick", (1.8, NOZZLE_Y - 0.5, 1.6), (0.9, 0, 2.6), 1.2, 250, (0.5, 0.8, 1.0))
    # grazing washes on the chamber wall so it reads as a space, not a void
    _area("WallWashA", (12, 18, 14), (0.6, 0, 2.6), 12, 9000, (0.35, 0.55, 1.0))
    _area("WallWashB", (-6, -20, -6), (1.9, 0, -0.4), 10, 5000, (0.3, 0.6, 0.9))
    _area("CollectorStrip", (9.0, 6.0, 5.0), (0.9, 0, 2.2), 0.4, 700, (0.6, 0.72, 1.0), size_y=14)

    tin = bpy.data.collections.new("TinReceivers")
    for o in tin_objs:
        tin.objects.link(o)
    C.softbox("SoftTop", (0, 0, 7), (0, 0, 0), (30, 30), 3.0, (0.55, 0.68, 1.0), receivers=tin)
    C.softbox("SoftSide", (8, 8, 1.0), (math.pi / 2, 0, 3 * math.pi / 4), (16, 6), 6.0,
              (0.75, 0.85, 1.0), receivers=tin)
    C.softbox("SoftBack", (-3, -10, 1), (math.pi / 2, 0, 0.3), (12, 4), 3.5, (0.5, 0.75, 1.0),
              receivers=tin)
    C.softbox("SoftFront", (9, -7, 0.5), (math.pi / 2, 0, math.pi / 4), (10, 8), 7.0,
              (0.7, 0.8, 1.0), receivers=tin)


def _camera(name, keys, focus=None):
    """keys: (frame, aim, location, lens, fstop). The aim empty doubles as the focus target."""
    bpy.ops.object.empty_add(location=(0, 0, 0))
    aim = bpy.context.object
    aim.name = name + "Aim"
    bpy.ops.object.camera_add()
    cam = bpy.context.object
    cam.name = name
    t = cam.constraints.new("TRACK_TO")
    t.target = aim
    t.track_axis = "TRACK_NEGATIVE_Z"
    t.up_axis = "UP_Y"
    cam.data.sensor_width = 36
    cam.data.clip_end = 400
    cam.data.dof.use_dof = True
    cam.data.dof.focus_object = focus or aim
    for f, a, loc, lens, fstop in keys:
        _key(aim, f, location=a)
        _key(cam, f, location=loc)
        cam.data.lens = lens
        cam.data.keyframe_insert("lens", frame=f)
        cam.data.dof.aperture_fstop = fstop
        cam.data.dof.keyframe_insert("aperture_fstop", frame=f)
    return cam


def _follow_keys(obj, f0, f1, offset0, offset1, lens, fstop, step=2, aim_offset=(0, 0, 0)):
    """Camera keys that track obj exactly between f0 and f1 with an interpolated offset;
    aim_offset shifts the look-at point (and the camera with it) relative to obj."""
    sc = bpy.context.scene
    keys = []
    for f in list(range(f0, f1, step)) + [f1]:
        sc.frame_set(f)
        p = obj.matrix_world.translation.copy()
        p.x += aim_offset[0]
        p.y += aim_offset[1]
        p.z += aim_offset[2]
        u = (f - f0) / max(1, f1 - f0)
        off = [a + (b - a) * u for a, b in zip(offset0, offset1)]
        keys.append((f, tuple(p), (p.x + off[0], p.y + off[1], p.z + off[2]), lens, fstop))
    sc.frame_set(1)
    return keys


def _shake(cam, f0, frames, amp, seed=11):
    """Short decaying camera shake layered on top of the existing location keys."""
    sc = bpy.context.scene
    rnd = random.Random(seed)
    base = {}
    for f in range(f0, f0 + frames + 1):
        sc.frame_set(f)
        base[f] = cam.location.copy()
    for f in range(f0, f0 + frames + 1):
        k = amp * (1 - (f - f0) / frames) ** 2
        jitter = base[f].copy()
        jitter.x += rnd.uniform(-k, k)
        jitter.y += rnd.uniform(-k, k)
        jitter.z += rnd.uniform(-k, k)
        cam.location = jitter
        cam.keyframe_insert("location", frame=f)
    sc.frame_set(1)


def build():
    sc = C.reset_scene(FRAME_END)
    C.set_world(top=(0.012, 0.016, 0.026), horizon=(0.006, 0.008, 0.014),
                bottom=(0.002, 0.003, 0.005))
    C.set_color_management(exposure=0.55)
    V.chamber()

    # --- droplet generator and stream ---------------------------------------------------
    # the nozzle sits ~0.3 m from the plasma (research/visual/B1_sources.md): far outside any frame that shows
    # the plasma site, so it is placed well off-screen; droplets fly 1.4 mm apart (Cymer/ASML: ~1.5 mm measured)
    nozzle_tip, _ = S.nozzle(NOZZLE_Y)
    spacing = 11.2                                   # 1.4 mm at 125 um per unit
    hero = S.droplet("HeroDroplet")
    stream = S.droplet_stream(count=26, spacing=spacing)        # back to the nozzle: a chain with no visible end
    for obj, off in ((hero, 0.0), (stream, -spacing)):
        _key(obj, 1, location=(0, -12.0 + off, 0))
        _key(obj, 80, location=(0, -1.3 + off, 0))
        _key(obj, T_ARRIVE, location=(0, 0.0 + off, 0))
    # the stream holds in bullet time, then the next droplet creeps toward the focus
    _key(stream, 262, location=(0, -spacing, 0))
    _key(stream, FRAME_END, location=(0, -0.9, 0))
    for obj in (hero, stream):
        for fc in C.fcurves(obj.animation_data.action):
            if fc.data_path == "location":
                fc.keyframe_points[0].interpolation = "LINEAR"

    # --- pre-pulse: a travelling orange pulse flattens the droplet into a sheet ----------
    pre, pre_mat, pre_len = S.laser_beam("PrePulse", 0.4, (1.0, 0.32, 0.06))          # ~100 um spot (PUR20 s.23)
    M.set_beam(pre_mat, T_PRE - 5, front=-pre_len / 2, strength=0)
    M.set_beam(pre_mat, T_PRE - 4, strength=12)        # strengths scaled down with the larger, real spot areas
    M.set_beam(pre_mat, T_PRE, front=pre_len / 2 + 1.5)
    M.set_beam(pre_mat, T_PRE + 3, strength=7)
    M.set_beam(pre_mat, T_PRE + 9, strength=0)

    swap = T_PRE + 6
    s0 = 0.55 * 2.6 * S.DROPLET_R / S.PANCAKE_R
    _key(hero, T_PRE, scale=(1, 1, 1))
    _key(hero, swap, scale=(0.55, 2.6, 2.6))
    _key(hero, swap, hide_render=False)
    _key(hero, swap + 1, hide_render=True)
    sheet = S.pancake()
    _key(sheet, 1, hide_render=True)
    _key(sheet, swap, hide_render=False)
    for f, k, x in ((swap, s0, 0.0), (T_PRE + 30, 0.8, 0.15), (T_MAIN - 4, 1.0, PLASMA_X)):
        _key(sheet, f, scale=(1, k, k), location=(x, 0, 0))
    ripple = sheet.modifiers["Ripple"]
    for f, st in ((swap, 0.0), (T_PRE + 40, 0.003), (T_MAIN, 0.005)):    # a liquid film tens of nm thick: barely rippled
        ripple.strength = st
        ripple.keyframe_insert("strength", frame=f)
    _key(sheet, T_MAIN, scale=(1, 1, 1))
    _key(sheet, T_MAIN + 2, scale=(0, 0, 0))

    # --- main pulse -> plasma, debris -----------------------------------------------------
    main, main_mat, main_len = S.laser_beam("MainPulse", 1.6, (1.0, 0.4, 0.12))       # ~400 um spot, covers the sheet
    M.set_beam(main_mat, T_MAIN - 4, front=-main_len / 2, strength=0)
    M.set_beam(main_mat, T_MAIN - 3, strength=10)
    M.set_beam(main_mat, T_MAIN, front=main_len / 2 + 1.5)
    M.set_beam(main_mat, T_MAIN + 2, strength=6)
    M.set_beam(main_mat, T_MAIN + 8, strength=0)

    shell, vol, core, core_mat, light = S.plasma()
    shell.location = core.location = (PLASMA_X, 0, 0)
    for f, k in ((T_MAIN - 1, 0.0), (T_MAIN, 0.1), (T_MAIN + 6, 0.65), (T_MAIN + 40, 1.05),
                 (FRAME_END, 1.25)):
        _key(shell, f, scale=(k, k, k))
    _key(core, T_MAIN - 1, scale=(0, 0, 0))
    _key(core, T_MAIN, scale=(1.6, 1.6, 1.6))
    for fc in C.fcurves(core.animation_data.action):        # appears at the main pulse, no dark dot growing before it
        for kp in fc.keyframe_points:
            if kp.co[0] < T_MAIN:
                kp.interpolation = "CONSTANT"
    _key(core, T_MAIN + 30, scale=(1, 1, 1))
    for f, e in ((T_MAIN, 0), (T_MAIN + 2, 22), (T_MAIN + 20, 4.5), (FRAME_END, 1.5)):
        M.set_volume_strength(vol, f, emission_strength=e)
    for f, e in ((T_MAIN, 0), (T_MAIN + 1, 160), (T_MAIN + 35, 14), (FRAME_END, 4)):
        M.set_emission_strength(core_mat, f, e)
    for f, e in ((T_MAIN, 0), (T_MAIN + 1, 4000), (T_MAIN + 14, 600), (T_MAIN + 40, 110), (FRAME_END, 45)):
        light.data.energy = e
        light.data.keyframe_insert("energy", frame=f)
    w = vol.node_tree.nodes["Noise"].inputs["W"]
    w.default_value = 0.0
    w.keyframe_insert("default_value", frame=T_MAIN)
    w.default_value = 3.0
    w.keyframe_insert("default_value", frame=FRAME_END)
    S.debris(T_MAIN, (PLASMA_X, 0, 0))

    # --- collector, EUV bundle (stand-in), IF ---------------------------------------------
    collector = S.collector()
    S.collector_housing()
    cone, cone_mat = S.euv_cone()
    for f, d, e in ((T_MAIN + 62, 0.0, 0.0), (T_MAIN + 95, 0.0, 0.02), (FRAME_END, 0.0, 0.018)):
        M.set_volume_strength(cone_mat, f, emission_strength=e, density=d)
    _, _, dot_mat = S.intermediate_focus()
    for f, e in ((T_MAIN + 10, 0), (T_MAIN + 26, 25), (FRAME_END, 18)):
        M.set_emission_strength(dot_mat, f, e)

    # exposure kick on the main pulse (reads as a flash on screen)
    vs = sc.view_settings
    for f, ex in ((T_MAIN, 0.55), (T_MAIN + 1, 2.3), (T_MAIN + 6, 0.9), (T_MAIN + 14, 0.55)):
        vs.exposure = ex
        vs.keyframe_insert("exposure", frame=f)

    _lights([hero, stream, nozzle_tip, sheet])
    mirror = bpy.data.collections.new("CollectorReceivers")
    mirror.objects.link(collector)
    glow = C.softbox("CollectorGlow", (11, 0, 0), (0, math.pi / 2, 0), (16, 16), 4.0,
                     (0.8, 0.85, 1.0), receivers=mirror)
    # once the plasma fires, the mirror should show the plasma, not a studio light
    _key(glow, 1, hide_render=False)
    _key(glow, T_MAIN - 6, hide_render=True)

    # --- cameras --------------------------------------------------------------------------
    _camera("CamEstablish", [
        (1, (0, -5.5, 0), (16.0, 3.5, 5.0), 30, 4.0),
        (64, (0, -4.5, 0), (13.5, 2.8, 4.0), 30, 4.0),
    ])
    _camera("CamNozzle", [
        (28, (0, -13.2, 0.05), (2.5, -12.4, 1.25), 50, 0.8),
        (88, (0, -12.9, 0.05), (2.25, -11.9, 1.05), 50, 0.8),
    ])
    _camera("CamPrePulse",
            _follow_keys(hero, 86, T_ARRIVE, (1.75, 1.15, 0.32), (1.8, 1.0, 0.3), 70, 0.9)
            + [(116, (0.05, 0, 0), (1.9, 1.7, 0.45), 60, 1.2),
               (132, (0.12, 0, 0), (2.2, 2.6, 0.6), 55, 1.6)])
    _camera("CamSheet", [
        (128, (0.12, 0, 0), (3.8, 5.0, 0.6), 50, 2.4),
        (190, (0.3, 0, 0), (2.2, 6.2, 2.2), 50, 2.6),
    ])
    plasma_cam = _camera("CamPlasma", [
        (187, (PLASMA_X, 0, 0), (3.1, 5.3, 1.5), 45, 2.8),
        (258, (PLASMA_X, 0, 0), (4.6, 7.6, 2.3), 42, 3.2),
    ])
    _shake(plasma_cam, T_MAIN, 14, 0.08)
    _camera("CamReveal", [
        (246, (1.0, 0, 0), (6.5, 9.5, 3.0), 35, 4.0),
        (346, (5.0, 0, 0), (23.0, 15.0, 6.5), 28, 6.0),
    ])
    # inserts: through the collector's central hole, inside the debris, across the mirror
    _camera("CamLaserPOV", [
        (84, (0, -1.6, 0), (-5.2, 0.0, 0.32), 40, 2.0),
        (98, (0, -0.2, 0), (-4.9, 0.0, 0.3), 40, 2.0),
    ])
    _camera("CamMainPOV", [
        (183, (PLASMA_X, 0, 0), (-5.4, 0.15, 0.35), 45, 2.4),
        (191, (PLASMA_X, 0, 0), (-5.0, 0.12, 0.32), 45, 2.4),
    ])
    _camera("CamDebris", [
        (222, (PLASMA_X, 0, 0), (1.6, 2.4, -1.3), 32, 2.2),
        (246, (PLASMA_X, 0, 0), (2.1, 2.9, -1.6), 32, 2.2),
    ])
    _camera("CamCollector", [
        (240, (-2.6, 1.0, 0.6), (0.4, 4.6, 2.4), 35, 1.8),
        (268, (-2.4, -0.4, 1.0), (0.3, 3.4, 3.8), 35, 1.8),
    ])
    sc.camera = bpy.data.objects["CamEstablish"]
    return sc
