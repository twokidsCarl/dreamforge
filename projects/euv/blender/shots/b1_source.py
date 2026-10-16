"""B1 light-source shots: one simulation (sample_b1) seen through a camera per storyboard shot.

Simulation events (sim frames, 24 fps): droplets fly 1-100, pre-pulse 100, sheet grows to 188,
main pulse 192, plasma/debris after, next droplet creeps in 262-346. Each CamB1_xx is keyed in
absolute sim frames; registry.yaml gives the window each shot renders.
"""
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
    cam("CamB1_04", [(1, (0, -13.2, 0.05), (2.5, -12.4, 1.25), 50, 0.8),
                     (187, (0, -12.8, 0.05), (2.0, -11.6, 0.9), 50, 0.8)])
    # B1_07 — long lens down the stream axis: compressed "string of pearls"
    cam("CamB1_07", [(1, (0, -8.0, 0), (0.7, 13.0, 0.5), 200, 5.6),
                     (94, (0, -7.0, 0), (0.6, 12.5, 0.45), 200, 5.6)])
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
    cam("CamB1_11", [(150, (0.25, 0, 0), (2.3, 8.6, 0.4), 55, 11.0)])
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
    return sc


def after_style(style, shot_id):
    """B1_11 is a shadowgraph (backlit high-speed photo of the sheet), not an SEM image."""
    if shot_id != "B1_11":
        return
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
