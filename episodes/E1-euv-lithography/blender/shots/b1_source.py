"""B1 light-source shots: one simulation (sample_b1) seen through a camera per storyboard shot.

Simulation events (sim frames, 24 fps): droplets fly 1-100, pre-pulse 100, sheet grows to 188,
main pulse 192, plasma/debris after, next droplet creeps in 262-346. Each CamB1_xx is keyed in
absolute sim frames; registry.yaml gives the window each shot renders.
"""
import math

import bpy

import build_source as S
import build_vacuum as V
import common as C
import sample_b1 as B

PX = B.PLASMA_X


def build(vessel=False, rays=False):
    sc = B.build()
    if vessel:
        V.source_vessel()
    if rays:
        S.light_rays()
    hero = sc.objects.get("HeroDroplet")
    cam = B._camera
    # B1_02 — exterior slow orbit around the vessel (xray)
    cam("CamB1_02", [(1, (3.0, -2.0, 0.0), (31.0, 26.0, 15.0), 30, 11.0),
                     (127, (3.0, -2.0, 0.0), (22.0, 32.0, 13.0), 30, 11.0)])
    # B1_03 — inside the chamber, slow dolly toward the droplet path
    cam("CamB1_03", [(1, (0, -5.5, 0), (16.0, 3.5, 5.0), 30, 4.0),
                     (120, (0, -4.0, 0), (12.5, 2.4, 3.6), 30, 4.0)])
    # B1_04 — nozzle macro, very shallow focus
    ny = B.NOZZLE_Y
    cam("CamB1_04", [(1, (0, ny + 0.8, 0.05), (2.5, ny + 1.6, 1.25), 50, 0.8),
                     (187, (0, ny + 1.2, 0.05), (2.0, ny + 2.4, 0.9), 50, 0.8)])
    # B1_07 — long lens down the stream axis: compressed "string of pearls"
    cam("CamB1_07", [(1, (0, -30.0, 0), (2.4, 8.0, 0.9), 135, 8.0),               # off-axis so the chain spreads
                     (94, (0, -26.0, 0), (2.2, 9.0, 0.85), 135, 8.0)], focus=hero)   # across the frame
    # B1_08 — lateral track with the stream (HUD lock boxes added in post)
    cam("CamB1_08", B._follow_keys(hero, 1, B.T_ARRIVE, (5.2, 0.0, 0.5), (5.0, 0.0, 0.45), 30, 5.6,
                                    aim_offset=(0, -1.5, 0))
        + [(118, (0, -1.0, 0), (5.4, -1.2, 0.55), 28, 5.6)])
    # B1_09 — down the laser axis through the collector's central hole (energy)
    cam("CamB1_09", [(80, (0, -1.6, 0), (-5.2, 0.0, 0.32), 40, 2.0),
                     (197, (PX, 0, 0), (-4.6, 0.0, 0.3), 40, 2.0)])
    # B1_10 — follow the droplet into the pre-pulse, then ease out as the sheet opens
    cam("CamB1_10", B._follow_keys(hero, 65, B.T_ARRIVE, (1.75, 1.15, 0.32), (1.8, 1.0, 0.3), 70, 1.0,
                                    aim_offset=(0, 0, 0.07))          # droplet a little low: clear of the caption
        # the eased-out frame keeps the opening sheet at ~60 % of the frame height, low and left of centre: the
        # upper-right caption (预脉冲：薄饼直径约 300 μm…) sat right on the sheet when it filled the frame
        + [(125, (-0.28, 0.32, 0.33), (4.48, 5.99, 1.61), 50, 2.8), (189, (-0.28, 0.37, 0.45), (4.76, 7.66, 2.0), 45, 3.2)])
    # B1_11 — edge-on silhouette of the sheet (SEM freeze)
    cam("CamB1_11", [(150, (0.25, 0, 0), (0.25, 10.4, 0.0), 55, 11.0)])         # strictly side-on: the sheet is a line; room for the tip fragments
    # B1_12 — slow arc while the sheet drifts to focus
    cam("CamB1_12", [(140, (0.25, 0, 0), (3.8, 5.0, 0.6), 50, 2.4),
                     (187, (0.3, 0, 0), (3.2, 5.5, 1.0), 50, 2.4)])
    # B1_13 — main pulse: impact shake, then slow pull-out with the plasma lighting the collector
    c13 = cam("CamB1_13", [(186, (PX, 0, 0), (3.1, 5.3, 1.5), 45, 2.8),
                           (336, (PX, 0, 0), (4.8, 7.9, 2.4), 42, 3.2)])
    B._shake(c13, B.T_MAIN, 14, 0.08, seed=13)
    # B1_14 — inside the debris field (energy)
    cam("CamB1_14", [(200, (PX, 0, 0), (1.6, 2.4, -1.3), 32, 2.2),
                     (247, (PX, 0, 0), (2.0, 2.8, -1.5), 32, 2.2)])
    # B1_15 — grazing pass across the collector surface
    cam("CamB1_15", [(205, (-2.0, 2.2, 0.6), (8.0, 1.2, 1.0), 40, 4.0),
                     (240, (-2.2, 1.2, 1.2), (7.4, 0.6, 1.6), 40, 4.0)])
    # B1_21 — pull back: collector lit, EUV cone to IF, next droplet already on its way
    cam("CamB1_21", [(260, (1.0, 0, 0), (6.5, 9.5, 3.0), 35, 4.0),
                     (343, (5.0, 0, 0), (23.0, 15.0, 6.5), 28, 6.0)])
    # A0_01 — cold open (rendered with step 2): the droplet glides in, pre-pulse, sheet, main-pulse flash
    cam("CamA0_01", B._follow_keys(hero, 4, B.T_ARRIVE, (1.9, 1.3, 0.3), (1.85, 1.15, 0.3), 85, 1.4)
        + [(130, (0.2, 0, 0), (5.2, 6.6, 0.9), 50, 2.8), (194, (0.3, 0, 0), (6.0, 7.6, 1.1), 45, 3.2),
           (232, (0.3, 0, 0), (7.2, 9.2, 1.5), 40, 3.2)])                # pull back as the plasma blooms
    # C_02 — long take part 1 (step ~0.73: slow): fly beside the droplet, pre-pulse, main pulse, turn to the collector
    cam("CamC_02", B._follow_keys(hero, 1, B.T_ARRIVE, (0.9, 1.2, 0.25), (1.0, 1.4, 0.3), 50, 2.0)
        + [(150, (0.2, 0, 0), (2.4, 3.6, 0.6), 40, 2.8), (192, (0.3, 0, 0), (3.6, 5.2, 0.9), 40, 3.2),
           (300, (-2.4, 0.0, 0.0), (4.2, 2.6, 1.4), 35, 4.0)])        # end on the lit collector (C_03 continues it)
    # D_09 — the last shot: tight on the droplet, the orange pre-pulse closing in; cut before the hit
    cam("CamD_09", B._follow_keys(hero, 86, B.T_ARRIVE, (1.9, -1.1, 0.35), (1.8, -1.05, 0.33), 100, 4.0))
    # ---- B2 reuses the same simulation ---------------------------------------------------
    # B2_01 — after the flash: the collector's iridescent face, embers drifting toward it
    cam("CamB2_01", [(205, (-1.8, 1.2, 0.6), (9.0, 7.0, 3.0), 32, 4.0),      # wide enough that the mirror never
                     (308, (-1.8, 1.0, 0.5), (7.8, 6.2, 2.6), 32, 4.0)])     # fills the frame as a flat colour
    # B2_03 — the main-pulse moment again, wider, debris shell heading for the mirror
    c3 = cam("CamB2_03", [(188, (PX - 0.6, 0, 0), (5.0, 7.2, 2.0), 32, 4.0),
                          (348, (PX - 1.2, 0, 0), (5.6, 7.8, 2.2), 32, 4.0)])
    B._shake(c3, B.T_MAIN, 12, 0.05, seed=23)
    # B2_12 — wide interior, crane up over the collector
    cam("CamB2_12", [(262, (1.0, 0, 0), (12.0, 7.0, 1.0), 28, 6.0),
                     (346, (1.0, 0, 0), (12.5, 7.4, 4.5), 28, 6.0)])
    # B3_02 — the collector before the main pulse: iridescent face, droplets crossing in front
    cam("CamB3_02", [(1, (-2.0, 0.0, 0.0), (11.0, 8.5, 3.6), 30, 5.6),
                     (123, (-2.0, 0.0, 0.0), (11.5, -6.5, 3.2), 30, 5.6)])
    return sc


def _shadowgraph():
    """B1_11 is a shadowgraph (backlit high-speed photo of the sheet), not an SEM image."""
    import bpy
    import materials as M
    import styles
    keep = {"Pancake"}
    for o in bpy.data.objects:
        if o.type in ("MESH", "CURVE") and o.name not in keep:
            o.hide_render = True
    styles._flat_world((0.62, 0.62, 0.60))
    black = M.emission("Shadow", (0.0, 0.0, 0.0), 1.0)
    sheet = bpy.data.objects["Pancake"]
    sheet.data.materials.clear()
    sheet.data.materials.append(black)
    _rim_ligaments(sheet, black)
    _shadowgraph_plate(black)


def _shadowgraph_plate(black):
    """The lab look of a shadowgram, in the frame (no post tool draws it): a backlit field with fine grain and a
    soft vignette instead of a flat grey world, and a 300 um scale bar (2.4 units) with its figure, bottom right."""
    import materials as M
    m = M.emission("ShadowField", (1, 1, 1), 1.0)
    nt = m.node_tree
    em = nt.nodes["Emission"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    grad = nt.nodes.new("ShaderNodeTexGradient")
    grad.gradient_type = "QUADRATIC_SPHERE"
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Location"].default_value = (-0.5, -0.5, 0)        # generated coords 0..1 -> centred
    mp.inputs["Scale"].default_value = (1.9, 1.9, 1)
    nt.links.new(tc.outputs["Generated"], mp.inputs["Vector"])
    nt.links.new(mp.outputs["Vector"], grad.inputs["Vector"])
    vig = nt.nodes.new("ShaderNodeMapRange")                     # centre 0.66, corners ~0.40
    vig.inputs["From Min"].default_value = 0.0
    vig.inputs["From Max"].default_value = 1.0
    vig.inputs["To Min"].default_value = 0.40
    vig.inputs["To Max"].default_value = 0.66
    nt.links.new(grad.outputs["Fac"], vig.inputs["Value"])
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 900.0
    noise.inputs["Detail"].default_value = 0.0
    grain = nt.nodes.new("ShaderNodeMapRange")
    grain.inputs["To Min"].default_value = 0.93
    grain.inputs["To Max"].default_value = 1.07
    nt.links.new(tc.outputs["Generated"], noise.inputs["Vector"])
    nt.links.new(noise.outputs["Fac"], grain.inputs["Value"])
    mul = nt.nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    nt.links.new(vig.outputs["Result"], mul.inputs[0])
    nt.links.new(grain.outputs["Result"], mul.inputs[1])
    nt.links.new(mul.outputs[0], em.inputs["Strength"])
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=(0.25, -6.0, 0.0), rotation=(math.pi / 2, 0, 0))
    plate = bpy.context.object
    plate.name = "ShadowField"
    plate.scale = (11.5, 6.6, 1)
    plate.data.materials.append(m)
    # scale bar: 300 um = 2.4 units at the sheet's depth, with end ticks and its figure
    x0, x1, z = -0.15, -0.15 - 300 / S.UNIT_UM, -1.5              # the camera looks along -y: screen right is -x
    for loc, size in ((((x0 + x1) / 2, 0.3, z), (x1 - x0, 0.01, 0.03)),
                      ((x0, 0.3, z), (0.02, 0.01, 0.12)), ((x1, 0.3, z), (0.02, 0.01, 0.12))):
        size = (abs(size[0]), size[1], size[2])
        bpy.ops.mesh.primitive_cube_add(location=loc)
        bar = bpy.context.object
        bar.name = "ScaleBar"
        bar.scale = (size[0] / 2, size[1] / 2, size[2] / 2)
        bar.data.materials.append(black)
    cu = bpy.data.curves.new("ScaleText", "FONT")
    cu.body = "300 μm"
    try:
        cu.font = bpy.data.fonts.load("/System/Library/Fonts/STHeiti Medium.ttc")
    except RuntimeError:
        pass
    cu.size = 0.17
    cu.align_x = "CENTER"
    txt = bpy.data.objects.new("ScaleText", cu)
    bpy.context.scene.collection.objects.link(txt)
    txt.location = ((x0 + x1) / 2, 0.3, z + 0.1)
    txt.rotation_euler = (math.pi / 2, 0, math.pi)                # upright and readable from +y
    txt.data.materials.append(black)


def _rim_ligaments(sheet, mat, frame=150, seed=4):
    """Edge-on shadowgrams of an expanding tin sheet (KUR16 Fig. 2, FOM17 Fig. 13B) show a hairline with a thicker
    bounding rim, beaded at the two tips, where the rim sheds ligaments that pinch into fragments. Seen edge-on the
    whole rim projects onto the line, so only the tips and what leaves them stand out: a bead at each tip, 3-4 liquid
    threads leaving it (in the sheet plane, a little tilted out of it), each ending in a drop, and a few drops that
    have already broken off. Sizes: rim ~3 um (0.025), threads ~1.5 um across, drops 2-5 um (示意)."""
    import random
    from mathutils import Euler, Vector
    rnd = random.Random(seed)
    sc = bpy.context.scene
    sc.frame_set(frame)
    m = sheet.matrix_world.copy()
    sc.frame_set(1)
    c = m.translation.copy()
    r = S.PANCAKE_R * m.to_scale().z
    made = []

    def sphere(p, rad):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=rad, segments=16, ring_count=8, location=p)
        made.append(bpy.context.object)

    def thread(a, b, rad):
        a, b = Vector(a), Vector(b)
        bpy.ops.mesh.primitive_cylinder_add(radius=rad, depth=(b - a).length, vertices=10, location=(a + b) / 2)
        ob = bpy.context.object
        ob.rotation_euler = (b - a).to_track_quat("Z", "Y").to_euler()
        made.append(ob)

    for side in (1, -1):
        tip = c + Vector((0.0, 0.0, side * r))
        sphere(tip, 0.036)
        for k in range(5):
            ang = rnd.uniform(-0.45, 0.45)                       # spread around the radial direction
            d = Vector((rnd.uniform(-0.18, 0.18), 0.0, side * 1.0))
            d.rotate(Euler((ang, 0, 0)))   # fan in the sheet plane (y-z), seen foreshortened
            d.normalize()
            base = tip + Vector((0, 0, -side * rnd.uniform(0.0, 0.05)))
            length = rnd.uniform(0.12, 0.38)
            end = base + d * length
            thread(base, end, rnd.uniform(0.006, 0.009))
            sphere(end, rnd.uniform(0.014, 0.022))
            for j in range(rnd.randint(0, 2)):                    # drops already pinched off beyond the thread
                sphere(end + d * rnd.uniform(0.06, 0.14) * (j + 1), rnd.uniform(0.009, 0.016))
    for ob in made:
        ob.name = "RimLigament"
        ob.data.materials.append(mat)


def _satin_sheet():
    """Satin tin and gentler ripples for the expanded sheet, so it does not mirror the studio in blotches."""
    import common as C
    import materials as M
    sheet = bpy.data.objects.get("Pancake")
    if not sheet:
        return
    sheet.data.materials.clear()
    sheet.data.materials.append(M.tin("TinSheetSatin", roughness=0.22))
    ad = sheet.animation_data                                  # gentler ripples: a liquid sheet, not foil
    for fc in (C.fcurves(ad.action) if ad and ad.action else []):
        if "Ripple" in fc.data_path and fc.data_path.endswith("strength"):
            for kp in fc.keyframe_points:
                kp.co[1] *= 0.35
                kp.handle_left[1] *= 0.35
                kp.handle_right[1] *= 0.35


def _cold_open():
    """A0_01 cold open (and D_08/D_09, its mirror at the end): the droplet in pure black. Chamber wall and ribs
    go, and so does the collector (out of focus it read as a flat grey-blue wall, and its edge reflected in
    the droplet looked like a second droplet). The tin reflects a faint studio, the sheet is satin so it does not mirror blotches."""
    import common as C
    import materials as M
    import styles
    for ob in list(bpy.data.objects):
        if styles.role_of(ob) == "env" or ob.name == "ChamberWall" or ob.name.startswith(("Rib", "Collector")):
            ob.hide_render = True
    C.set_world(top=(0.0, 0.0, 0.0), horizon=(0.0, 0.0, 0.0), bottom=(0.0, 0.0, 0.0))
    C.reflection_env("studio_small_09", 0.25)
    _satin_sheet()
    # a few far LEDs as bokeh, low and to the side, so the black has depth
    led = M.emission("BokehLED", (0.45, 0.7, 1.0), 6.0)
    for k, (x, y, z) in enumerate(((-14, -4, 2.5), (-16, -9, -1.8), (-13, -13, 0.6), (-18, -6, -3.2), (-15, 2, 3.4))):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.12, location=(x, y, z))
        b = bpy.context.object
        b.name = f"BokehLED{k}"
        b.data.materials.append(led)
        styles.tag(b, "emitter")


def _endless_chain():
    """B1_07 looks down the droplet line; the stylised chamber wall would end the chain after a few droplets, so it
    goes and the chain runs into the dark (the real nozzle is ~0.3 m away, ~200 droplets back)."""
    from mathutils import Vector
    for ob in bpy.data.objects:      # edge-on collector = a bright bar; no sheet before 100; the nozzle would end the chain
        if ob.name in ("ChamberWall", "Pancake") or ob.name.startswith(("Rib", "Collector", "DropletGenerator")):
            ob.hide_render = True
    # a long strip light beside the line gives every droplet down the chain its own glint
    rot = Vector((-1.0, 0.0, -0.55)).to_track_quat("-Z", "Y").to_euler()
    lt = B._area("ChainStrip", (2.6, -150.0, 1.4), rot, 300.0, 40000, (0.6, 0.78, 1.0), size_y=0.3)
    lt["keep_light"] = True


def _closing_droplet(shot_id):
    """D_08 / D_09, the last droplet: pure black, no bokeh blobs beside it (they read as a second droplet at the
    end). D_09: the camera sits outside the pre-pulse beam on the far side of the flight line, and the pulse front is
    re-keyed so a sharp orange front closes in from frame left over the whole shot (sim 88-99, registry start 90,
    step 0.155), the cut to black coming just before it reaches the droplet (beam axis: world x = local z - 20)."""
    for ob in bpy.data.objects:
        if ob.name.startswith("BokehLED"):
            ob.hide_render = True
    # D_08 flies the droplet past y = -10, right through the SoftBack card (12 x 4 m at (-3, -10, 1)): close up its dark,
    # falling-off edge filled half the tin as a black disc (the "crescent"), and the camera crossed the card (the bar)
    hide = ("SoftBack",) + (("MainPulse", "PrePulse") if shot_id == "D_08" else ("MainPulse",))
    for nm in hide:
        if bpy.data.objects.get(nm):
            bpy.data.objects[nm].hide_render = True
    if shot_id != "D_09":
        return
    mat = bpy.data.materials.get("PrePulseMat")
    if not mat:
        return
    nt = mat.node_tree
    nt.animation_data_clear()
    fr = nt.nodes["Front"]
    sc_in = nt.nodes["EmissionScale"].inputs[1]
    half = 20.0                                                    # beam from x = -40 to 0: local z = x + 20
    for f, x in ((88, -0.95), (99, -0.13)):                        # droplet edge at x = -0.1
        fr.inputs["From Min"].default_value = x + half
        fr.inputs["From Max"].default_value = x + half - 0.09        # a crisp leading edge at this scale
        fr.inputs["From Min"].keyframe_insert("default_value", frame=f)
        fr.inputs["From Max"].keyframe_insert("default_value", frame=f)
    for f, v in ((88, 3.5), (99, 3.5)):
        sc_in.default_value = v
        sc_in.keyframe_insert("default_value", frame=f)


def _beams_only_when_lit():
    """The pulse cylinders exist for the whole simulation; outside their emission window a beam at strength 0
    rendered as a dark rod across the frame (B1_08 sim 1-35). Hidden except while they emit (sim_b1 keys: pre-pulse
    T_PRE-5 .. T_PRE+9, main pulse T_MAIN-4 .. T_MAIN+8). Not used for D_08/D_09, which re-key the pre-pulse."""
    for name, on, off in (("PrePulse", B.T_PRE - 5, B.T_PRE + 9), ("MainPulse", B.T_MAIN - 4, B.T_MAIN + 8)):
        ob = bpy.data.objects.get(name)
        if ob is None or ob.hide_render:
            continue
        for f, h in ((1, True), (on, False), (off + 1, True)):
            ob.hide_render = h
            ob.keyframe_insert("hide_render", frame=f)          # boolean channel: steps, also on sub-frames


def _vessel_view():
    """B1_02 sees the vessel from outside: the nozzle (really ~0.3 m off, NOZZLE_Y = -300) and the far end of the
    26-droplet chain floated outside the vessel as a small dark ring. Inside the vessel only the last few droplets
    before the plasma site are kept."""
    for ob in bpy.data.objects:
        if ob.name.startswith("DropletGenerator"):
            ob.hide_render = True
    stream = bpy.data.objects.get("DropletStream")
    if stream and "Array" in stream.modifiers:
        stream.modifiers["Array"].count = 3                     # 3 x 1.4 mm: all inside the drum


def _hud_lock(cam_name="CamB1_08", appear=8, lock=60, half=0.26):
    """B1_08 "单独成像 · 单独瞄准": a thin metrology-cyan lock box that rides on the hero droplet, facing the
    camera. It snaps in from 1.9x, tightens, a short read-out of bars flickers beside it (decorative, no digits),
    and at `lock` it turns laser orange (the hand-off to B1_09). Imaging/targeting details are not public: the
    label carries 示意. Built in 3D so it tracks the droplet exactly through the follow move."""
    import materials as M
    import styles
    hero = bpy.data.objects["HeroDroplet"]
    cam = bpy.data.objects[cam_name]
    cyan, orange = (0.05, 0.72, 0.95), (1.0, 0.30, 0.03)
    mat = M.emission("HudLock", cyan, 0.0)
    em = mat.node_tree.nodes["Emission"]
    for f, col in ((lock - 1, cyan), (lock, orange)):
        em.inputs["Color"].default_value = (*col, 1.0)
        em.inputs["Color"].keyframe_insert("default_value", frame=f)
    for f, s in ((appear - 1, 0.0), (appear, 3.2), (appear + 3, 1.5), (lock - 1, 1.5), (lock, 4.0), (lock + 4, 2.2)):
        em.inputs["Strength"].default_value = s
        em.inputs["Strength"].keyframe_insert("default_value", frame=f)
    rig = bpy.data.objects.new("HudRig", None)
    bpy.context.scene.collection.objects.link(rig)
    c = rig.constraints.new("COPY_LOCATION")
    c.target = hero
    t = rig.constraints.new("TRACK_TO")
    t.target = cam
    t.track_axis = "TRACK_Z"
    t.up_axis = "UP_Y"

    def curve_obj(name, splines, bevel):
        cu = bpy.data.curves.new(name, "CURVE")
        cu.dimensions = "3D"
        cu.bevel_depth = bevel
        cu.bevel_resolution = 0
        for pts in splines:
            sp = cu.splines.new("POLY")
            sp.points.add(len(pts) - 1)
            for k, (x, y) in enumerate(pts):
                sp.points[k].co = (x, y, 0.0, 1.0)
        ob = bpy.data.objects.new(name, cu)
        bpy.context.scene.collection.objects.link(ob)
        ob.data.materials.append(mat)
        ob.parent = rig
        for attr in ("visible_shadow", "visible_glossy", "visible_transmission", "visible_diffuse"):
            setattr(ob, attr, False)                 # an overlay: no reflections in the tin, no shadows
        styles.tag(ob, "emitter")
        return ob

    arm = half * 0.42
    corners = []
    for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        corners.append([(sx * half, sy * (half - arm)), (sx * half, sy * half), (sx * (half - arm), sy * half)])
    ticks = [[(0.0, half * 0.93), (0.0, half * 1.12)], [(0.0, -half * 0.93), (0.0, -half * 1.12)],
             [(half * 0.93, 0.0), (half * 1.12, 0.0)], [(-half * 0.93, 0.0), (-half * 1.12, 0.0)]]
    box = curve_obj("HudLockBox", corners + ticks, 0.0042)
    for f, k in ((appear, 1.9), (appear + 7, 1.0), (lock - 2, 1.0), (lock + 1, 0.86), (lock + 4, 0.9)):
        box.scale = (k, k, k)
        box.keyframe_insert("scale", frame=f)
    # decorative read-out: three short bars beside the top-right corner, their lengths flicker (no readable values)
    import random
    rnd = random.Random(8)
    for i in range(3):
        y = half * (0.95 - 0.2 * i)
        bar = curve_obj(f"HudBar{i}", [[(0.0, 0.0), (1.0, 0.0)]], 0.0032)
        bar.location = (half * 1.25, y, 0.0)
        for f in range(appear, lock + 30, 3):
            bar.scale = (half * rnd.uniform(0.15, 0.6), 1.0, 1.0)
            bar.keyframe_insert("scale", frame=f)
    for ob in (box,) + tuple(bpy.data.objects[f"HudBar{i}"] for i in range(3)):
        ob.hide_render = True
        ob.keyframe_insert("hide_render", frame=1)
        ob.hide_render = False
        ob.keyframe_insert("hide_render", frame=appear)
        if ob is not box:
            for fc in (fc for fc in C.fcurves(ob.animation_data.action) if fc.data_path == "scale"):
                for kp in fc.keyframe_points:
                    kp.interpolation = "CONSTANT"


def _energy_debris(f0=200, f1=248):
    """B1_14 on black: at the photoreal strengths (debris 60, core 160) every fragment and the core clipped to white
    and bloomed into a grey wash, so nothing 'cooled'. Here the fragments glow at a strength where the material's
    white-violet -> orange ramp reads, and the core is a violet-white glow that pulses instead of a flat white disc."""
    import math
    deb = bpy.data.materials.get("Debris")
    if deb:                       # EEVEE gives Particle Info age 0, so the cooling is keyed in time for the whole cloud
        for n in deb.node_tree.nodes:
            if n.type == "MAP_RANGE":
                for f, v in ((f0, 3.0), (f0 + 20, 2.2), (f1, 1.4)):
                    n.inputs["To Min"].default_value = v
                    n.inputs["To Min"].keyframe_insert("default_value", frame=f)
            if n.type == "VALTORGB":
                for el in n.color_ramp.elements:
                    for f, col in ((f0, (0.62, 0.42, 1.0, 1)), (f0 + 12, (1.0, 0.55, 0.30, 1)),
                                   (f0 + 26, (1.0, 0.30, 0.05, 1)), (f1, (0.85, 0.14, 0.02, 1))):
                        el.color = col                                   # white-violet -> orange -> red-orange
                        el.keyframe_insert("color", frame=f)
    core = bpy.data.materials.get("PlasmaCoreMat")
    if core:
        core.node_tree.animation_data_clear()
        em = core.node_tree.nodes["Emission"]
        em.inputs["Color"].default_value = (0.70, 0.52, 1.0, 1)
        for f in range(f0, f1 + 1, 3):
            em.inputs["Strength"].default_value = (1.5 + 4.0 * math.exp(-(f - f0) / 7)       # still hot from the flash,
                                                   + 0.7 * math.sin((f - f0) * 0.55) * math.exp(-(f - f0) / 60))
            em.inputs["Strength"].keyframe_insert("default_value", frame=f)


def _scale_keys(fcurves, pred, k, after):
    for fc in fcurves:
        if not pred(fc):
            continue
        for kp in fc.keyframe_points:
            if kp.co[0] >= after:
                kp.co[1] *= k
                kp.handle_left[1] *= k
                kp.handle_right[1] *= k
        fc.update()


def _calm_plasma(shot_id):
    """B2_03 / B2_12: the EUV-bundle stand-in (an emissive volume from the collector rim to the IF, 0.02 from sim
    254) lies between these cameras and the mirror and veiled the whole face in flat lavender. B2_03 drops it; B2_12
    keeps it faint and lets every (slow-motion) pulse brighten it once. The persistent plasma cloud and its light are
    also turned down after the flash so the mirror and droplets read."""
    import common as C
    import materials as M
    T = B.T_MAIN
    if shot_id == "B2_03" and bpy.data.objects.get("EUVCone"):
        bpy.data.objects["EUVCone"].hide_render = True
    vol = bpy.data.materials.get("PlasmaVol")
    if vol and vol.node_tree.animation_data and vol.node_tree.animation_data.action:
        _scale_keys(C.fcurves(vol.node_tree.animation_data.action), lambda fc: "EmissionScale" in fc.data_path,
                    0.3, T + 20)
    lt = bpy.data.objects.get("PlasmaLight")
    if lt and lt.data.animation_data and lt.data.animation_data.action:
        _scale_keys(C.fcurves(lt.data.animation_data.action), lambda fc: fc.data_path == "energy", 0.25, T + 20)
    if shot_id == "B2_12":
        cone = bpy.data.materials.get("EUVConeMat")
        core = bpy.data.materials.get("PlasmaCoreMat")
        if cone:
            cone.node_tree.animation_data_clear()
            for f0 in range(264, 347, 14):
                for f, e in ((f0, 0.0025), (f0 + 2, 0.011), (f0 + 10, 0.0025)):
                    M.set_volume_strength(cone, f, emission_strength=e, density=0.0)
        if core:
            for f0 in range(264, 347, 14):
                for f, e in ((f0, 4.0), (f0 + 1, 40.0), (f0 + 8, 4.0)):
                    M.set_emission_strength(core, f, e)


def after_style(style, shot_id):
    if shot_id not in ("D_08", "D_09"):
        _beams_only_when_lit()
    if shot_id == "B1_02":
        _vessel_view()
    if shot_id == "B1_08":
        _hud_lock()
    if shot_id == "B1_14":
        _energy_debris()
    if shot_id == "B1_07":
        _endless_chain()
    elif shot_id == "B1_11":
        _shadowgraph()
    elif shot_id in ("A0_01", "D_08", "D_09"):
        _cold_open()
        if shot_id in ("D_08", "D_09"):
            _closing_droplet(shot_id)
        else:                                       # A0_01 has the same two faults as D_08: the droplet crosses the
            for ob in bpy.data.objects:             # SoftBack card (a dark crescent on the tin) and the bokeh LEDs
                if ob.name == "SoftBack" or ob.name.startswith("BokehLED"):   # read as a second droplet
                    ob.hide_render = True
    elif shot_id in ("B2_03", "B2_12"):
        _calm_plasma(shot_id)
    elif shot_id in ("B1_10", "B1_12", "B1_13", "C_02"):
        _satin_sheet()
