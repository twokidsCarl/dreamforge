"""Sample shot for segment B1 (tin droplet + double pulse), 12 s @ 24 fps, one continuous camera.

0-4 s   follow a tin droplet out of the generator toward the plasma site (speed ramp into slow-mo)
4-8 s   pre-pulse flash flattens the droplet into a ~300 um disk (F4b)
8-12 s  main pulse -> plasma burst lights the collector; pull back to show collector -> IF
"""
import math

import bpy

import build_source as S
import common as C
import materials as M

FRAME_END = 288
T_ARRIVE = 100        # droplet reaches the plasma site
T_PRE = 100           # pre-pulse
T_MAIN = 192          # main pulse


def _key(obj, frame, **props):
    for k, v in props.items():
        setattr(obj, k, v)
        obj.keyframe_insert(k, frame=frame)


def _lights(tin_objs):
    def area(name, loc, rot, size, energy, color, shape="RECTANGLE", size_y=None):
        bpy.ops.object.light_add(type="AREA", location=loc, rotation=rot)
        lt = bpy.context.object
        lt.name = name
        lt.data.shape = shape
        lt.data.size = size
        if size_y:
            lt.data.size_y = size_y
        lt.data.energy = energy
        lt.data.color = color
        return lt

    area("Key", (2.0, 1.5, 7.0), (0.25, 0.15, 0), 5.0, 260, (0.62, 0.76, 1.0))
    area("NozzleKick", (1.8, -14.5, 1.6), (0.9, 0, 2.6), 1.2, 250, (0.5, 0.8, 1.0))
    area("Rim", (-5.0, -4.0, 2.5), (1.2, 0, -2.3), 4.0, 420, (0.45, 0.85, 1.0))
    # strip lights give the collector readable specular streaks before the plasma fires
    area("StripA", (9.0, 6.0, 5.0), (0.9, 0, 2.2), 0.3, 900, (0.55, 0.7, 1.0), size_y=14)
    area("StripB", (9.0, -6.0, -3.0), (2.2, 0, 0.9), 0.3, 500, (0.5, 0.65, 1.0), size_y=14)
    # reflection-only softboxes for the tin; light-linked so the collector does not mirror them
    tin = bpy.data.collections.new("TinReceivers")
    for o in tin_objs:
        tin.objects.link(o)
    C.softbox("SoftTop", (0, 0, 7), (0, 0, 0), (30, 30), 3.0, (0.55, 0.68, 1.0), receivers=tin)
    C.softbox("SoftSide", (8, 8, 1.0), (math.pi / 2, 0, 3 * math.pi / 4), (16, 6), 6.0, (0.75, 0.85, 1.0), receivers=tin)
    C.softbox("SoftBack", (-3, -10, 1), (math.pi / 2, 0, 0.3), (12, 4), 3.5, (0.5, 0.75, 1.0), receivers=tin)
    C.softbox("SoftFront", (9, -7, 0.5), (math.pi / 2, 0, math.pi / 4), (10, 8), 7.0, (0.7, 0.8, 1.0), receivers=tin)


def _camera(hero):
    bpy.ops.object.empty_add(location=(0, 0, 0))
    aim = bpy.context.object
    aim.name = "Aim"
    bpy.ops.object.camera_add()
    cam = bpy.context.object
    cam.name = "Camera"
    bpy.context.scene.camera = cam
    t = cam.constraints.new("TRACK_TO")
    t.target = aim
    t.track_axis = "TRACK_NEGATIVE_Z"
    t.up_axis = "UP_Y"
    cam.data.dof.use_dof = True
    cam.data.dof.focus_object = aim
    cam.data.sensor_width = 36

    # approach: follow the droplet exactly (sampled from its animation) so it stays framed
    sc = bpy.context.scene
    for f in range(1, T_ARRIVE + 1, 3):
        sc.frame_set(f)
        hp = hero.matrix_world.translation.copy()
        u = (f - 1) / (T_ARRIVE - 1)
        off = (2.4 - 0.6 * u, 1.9 - 0.9 * u, 0.55 - 0.25 * u)
        _key(aim, f, location=(hp.x, hp.y - 0.15 * (1 - u), hp.z))
        _key(cam, f, location=(hp.x + off[0], hp.y + off[1], hp.z + off[2]))
        cam.data.lens = 70
        cam.data.keyframe_insert("lens", frame=f)
        cam.data.dof.aperture_fstop = 1.6
        cam.data.dof.keyframe_insert("aperture_fstop", frame=f)
    sc.frame_set(1)

    # (frame, aim, camera, lens, fstop)
    path = [
        (130, (0.15, 0, 0), (2.4, 4.0, 0.9), 50, 2.0),
        (185, (0.3, 0, 0), (3.0, 5.4, 1.5), 50, 2.4),
        (200, (0.3, 0, 0), (3.2, 5.6, 1.8), 45, 2.8),
        (288, (5.0, 0, 0), (22.0, 14.0, 6.0), 30, 5.6),
    ]
    for f, a, c, lens, fstop in path:
        _key(aim, f, location=a)
        _key(cam, f, location=c)
        cam.data.lens = lens
        cam.data.keyframe_insert("lens", frame=f)
        cam.data.dof.aperture_fstop = fstop
        cam.data.dof.keyframe_insert("aperture_fstop", frame=f)
    return cam


def build():
    sc = C.reset_scene(FRAME_END)
    C.set_world(color=(0.008, 0.012, 0.02))
    C.set_color_management()

    # --- droplet generator and stream ---------------------------------------------------
    tip_y = -14.0
    nozzle_tip, _ = S.nozzle(tip_y)
    spacing = 3.0
    hero = S.droplet("HeroDroplet")
    stream = S.droplet_stream(count=5, spacing=spacing)
    # constant speed, then a bullet-time ramp into the plasma site
    for obj, off in ((hero, 0.0), (stream, -spacing)):
        _key(obj, 1, location=(0, -12.0 + off, 0))
        _key(obj, 80, location=(0, -1.3 + off, 0))
        _key(obj, T_ARRIVE, location=(0, 0.0 + off, 0))
    for obj in (hero, stream):
        for fc in C.fcurves(obj.animation_data.action):
            if fc.data_path == "location":
                fc.keyframe_points[0].interpolation = "LINEAR"

    # --- pre-pulse: flatten to a ~300 um disk (F4b), disk normal along the laser (+X) ----
    pre, pre_mat = S.laser_beam("PrePulse", 0.05, (1.0, 0.28, 0.06), 0.0)
    for f, s in ((T_PRE - 2, 0), (T_PRE, 150), (T_PRE + 3, 80), (T_PRE + 7, 0)):
        M.set_volume_strength(pre_mat, f, emission_strength=s)
    # droplet squashes, then hands over to the sheet mesh, which grows to ~300 um and drifts
    # downstream along the laser direction
    swap = T_PRE + 6
    s0 = 0.55 * 2.6 * S.DROPLET_R / S.PANCAKE_R
    _key(hero, T_PRE, scale=(1, 1, 1))
    _key(hero, swap, scale=(0.55, 2.6, 2.6))
    _key(hero, swap, hide_render=False)
    _key(hero, swap + 1, hide_render=True)
    sheet = S.pancake()
    _key(sheet, 1, hide_render=True)
    _key(sheet, swap, hide_render=False)
    for f, sc_, x in ((swap, s0, 0.0), (T_PRE + 30, 0.8, 0.15), (T_MAIN - 4, 1.0, 0.35)):
        _key(sheet, f, scale=(1, sc_, sc_), location=(x, 0, 0))
    ripple = sheet.modifiers["Ripple"]
    for f, st in ((swap, 0.0), (T_PRE + 40, 0.035), (T_MAIN, 0.05)):
        ripple.strength = st
        ripple.keyframe_insert("strength", frame=f)

    # --- main pulse -> plasma ------------------------------------------------------------
    main, main_mat = S.laser_beam("MainPulse", 0.45, (1.0, 0.35, 0.10), 0.0)
    for f, s in ((T_MAIN - 2, 0), (T_MAIN, 25), (T_MAIN + 3, 14), (T_MAIN + 7, 0)):
        M.set_volume_strength(main_mat, f, emission_strength=s)
    _key(sheet, T_MAIN, scale=(1, 1, 1))
    _key(sheet, T_MAIN + 3, scale=(0.0, 0.0, 0.0))

    shell, vol, core, core_mat, light = S.plasma()
    shell.location = core.location = (0.35, 0, 0)
    for f, s in ((T_MAIN - 1, 0.0), (T_MAIN, 0.1), (T_MAIN + 8, 0.6), (T_MAIN + 40, 1.0), (FRAME_END, 1.3)):
        _key(shell, f, scale=(s, s, s))
    _key(core, T_MAIN - 1, scale=(0, 0, 0))
    _key(core, T_MAIN, scale=(1, 1, 1))
    for f, e in ((T_MAIN, 0), (T_MAIN + 3, 18), (T_MAIN + 20, 8), (FRAME_END, 3.5)):
        M.set_volume_strength(vol, f, emission_strength=e)
    for f, e in ((T_MAIN, 0), (T_MAIN + 2, 50), (T_MAIN + 35, 12), (FRAME_END, 5)):
        M.set_emission_strength(core_mat, f, e)
    for f, e in ((T_MAIN, 0), (T_MAIN + 2, 4000), (T_MAIN + 40, 1200), (FRAME_END, 600)):
        light.data.energy = e
        light.data.keyframe_insert("energy", frame=f)
    w = vol.node_tree.nodes["Noise"].inputs["W"]
    w.default_value = 0.0
    w.keyframe_insert("default_value", frame=T_MAIN)
    w.default_value = 2.5
    w.keyframe_insert("default_value", frame=FRAME_END)

    # --- collector, EUV bundle (stand-in), IF ---------------------------------------------
    S.collector()
    S.collector_housing()
    cone, cone_mat = S.euv_cone()
    for f, d, e in ((T_MAIN + 4, 0.0, 0.0), (T_MAIN + 20, 0.0025, 0.035), (FRAME_END, 0.002, 0.03)):
        M.set_volume_strength(cone_mat, f, emission_strength=e, density=d)
    _, _, dot_mat = S.intermediate_focus()
    for f, e in ((T_MAIN + 10, 0), (T_MAIN + 24, 20), (FRAME_END, 15)):
        M.set_emission_strength(dot_mat, f, e)

    _lights([hero, stream, nozzle_tip, sheet])
    _camera(hero)
    return sc
