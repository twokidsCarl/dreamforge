"""B1 light-source shots: one simulation (sample_b1) seen through a camera per storyboard shot.

Simulation events (sim frames, 24 fps): droplets fly 1-100, pre-pulse 100, sheet grows to 188,
main pulse 192, plasma/debris after, next droplet creeps in 262-346. Each CamB1_xx is keyed in
absolute sim frames; registry.yaml gives the window each shot renders.
"""
import bpy

import build_source as S
import build_vacuum as V
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
    cam("CamB1_10", B._follow_keys(hero, 65, B.T_ARRIVE, (1.75, 1.15, 0.32), (1.8, 1.0, 0.3), 70, 1.0)
        + [(125, (0.1, 0, 0), (2.7, 3.1, 0.7), 50, 1.8), (189, (0.25, 0, 0), (3.5, 4.7, 1.0), 45, 2.4)])
    # B1_11 — edge-on silhouette of the sheet (SEM freeze)
    cam("CamB1_11", [(150, (0.25, 0, 0), (0.25, 8.6, 0.0), 55, 11.0)])          # strictly side-on: the sheet is a line
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
    cam("CamB2_01", [(205, (-2.2, 3.4, 1.4), (6.0, 2.0, 2.2), 45, 2.8),
                     (308, (-2.2, 3.0, 1.2), (5.0, 1.8, 1.9), 45, 2.8)])
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


def after_style(style, shot_id):
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
    elif shot_id in ("B1_10", "B1_12", "B1_13", "C_02"):
        _satin_sheet()
