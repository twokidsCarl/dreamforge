"""B1_17 / B1_19 / B1_20: inside the plasma — a tin atom losing electrons, then the web of
transitions behind every 13.5 nm photon (F23, F24). Energy-view scenes (black, emission only).

  build(variant="atom")  B1_17  shells 2-8-18-18-4 (tin ground state); outer electrons fly off
                                one by one until Sn14+ (8-14 electrons stripped)
  build(variant="web")   B1_19  hundreds of energy levels stacked like floors; transition lines
                                light up in waves while the camera pulls back
                         B1_20  same web; lines dim and a single violet beam forms out of it
Illustrative: shells are drawn as Bohr-style rings, levels and transitions are random, not data.
"""
import math
import random

import bpy

import common as C
import materials as M
import styles

FRAMES = 240
VIOLET = (0.62, 0.45, 1.0)
WHITE_VIOLET = (0.9, 0.85, 1.0)


def _ring(name, radius, mat, thickness=0.006):
    bpy.ops.curve.primitive_bezier_circle_add(radius=radius)
    ob = bpy.context.object
    ob.name = name
    ob.data.bevel_depth = thickness
    ob.data.materials.append(mat)
    styles.tag(ob, "emitter")
    return ob


def _sphere(name, r, mat, loc=(0, 0, 0)):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, segments=24, ring_count=12, location=loc)
    ob = bpy.context.object
    ob.name = name
    ob.data.materials.append(mat)
    styles.tag(ob, "emitter")
    return ob


def _key(ob, f, **kw):
    for k, v in kw.items():
        setattr(ob, k, v)
        ob.keyframe_insert(k, frame=f)


def build_atom(sc, rnd):
    shells = [2, 8, 18, 18, 4]          # tin, Z = 50
    radii = [0.18, 0.38, 0.62, 0.9, 1.22]
    core_mat = M.emission("Nucleus", WHITE_VIOLET, 6.0)
    nucleus = _sphere("Nucleus", 0.07, core_mat)
    bpy.ops.object.empty_add(location=(0, 0, 0), rotation=(0.35, 0.15, 0))
    tilt = bpy.context.object                      # one tilt for the whole atom keeps shells coplanar
    ring_mat = M.emission("Shell", (0.35, 0.3, 0.7), 0.6)
    el_mat = M.emission("Electron", (0.6, 0.8, 1.0), 12.0)
    # strip order: the 4 outer electrons, then 10 from the 4th shell -> Sn14+
    strip = [(4, k) for k in range(4)] + [(3, k) for k in range(10)]
    t_strip = {s: 30 + 7 * i for i, s in enumerate(strip)}
    for si, (n, r) in enumerate(zip(shells, radii)):
        ring = _ring(f"Shell{si}", r, ring_mat)
        ring.parent = tilt
        for k in range(n):
            e = _sphere(f"E{si}_{k}", 0.018, el_mat)
            e.parent = ring
            a0 = 2 * math.pi * k / n
            w = 0.04 / (r ** 1.5)                         # inner electrons orbit faster
            f_end = t_strip.get((si, k), FRAMES)
            for f in list(range(1, f_end, 4)) + [f_end]:
                a = a0 + w * f
                e.location = (r * math.cos(a), r * math.sin(a), 0)
                e.keyframe_insert("location", frame=f)
            if (si, k) in t_strip:
                a = a0 + w * f_end
                e.location = (6.0 * r * math.cos(a), 6.0 * r * math.sin(a), rnd.uniform(-1, 1))
                e.keyframe_insert("location", frame=f_end + 14)
                _key(e, 1, hide_render=False)
                _key(e, f_end + 14, hide_render=True)
    # the ion brightens as it is stripped
    s = core_mat.node_tree.nodes["Emission"].inputs["Strength"]
    for f, v in ((1, 6.0), (30, 6.0), (130, 40.0), (FRAMES, 46.0)):
        s.default_value = v
        s.keyframe_insert("default_value", frame=f)
    glow = M.volume_glow("IonGlow", VIOLET, density=1.0, emission_strength=0.0, falloff=True)
    halo = _sphere("IonHalo", 1.0, glow)
    halo.scale = (0.5, 0.5, 0.5)
    for f, e in ((1, 0.2), (30, 0.2), (130, 3.0), (FRAMES, 3.4)):
        M.set_volume_strength(glow, f, emission_strength=e)
    import sample_b1 as B
    B._camera("CamB1_17", [(1, (0, 0, 0), (0.0, -9.0, 4.0), 50, 8.0),
                           (60, (0, 0, 0), (0.0, -4.6, 2.2), 50, 8.0),
                           (FRAMES, (0, 0, 0), (0.0, -4.3, 2.0), 50, 8.0)])
    return nucleus


def build_web(sc, rnd, n_levels=420, n_lines=2600, groups=12):
    """Energy levels as horizontal lines (floors), transitions as thin vertical-ish strokes."""
    levels = sorted(rnd.uniform(-3.0, 3.0) for _ in range(n_levels))
    lvl_mat = M.emission("Level", (0.25, 0.22, 0.5), 0.5)
    cu = bpy.data.curves.new("Levels", "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = 0.0025
    for y in levels:
        x0 = rnd.uniform(-4.0, -1.0)
        x1 = rnd.uniform(1.0, 4.0)
        sp = cu.splines.new("POLY")
        sp.points.add(1)
        sp.points[0].co = (x0, 0, y, 1)
        sp.points[1].co = (x1, 0, y, 1)
    lv = bpy.data.objects.new("Levels", cu)
    sc.collection.objects.link(lv)
    lv.data.materials.append(lvl_mat)
    styles.tag(lv, "emitter")
    # transition lines in groups, each group lights up at its own time
    group_mats = []
    for g in range(groups):
        mat = M.emission(f"Transitions{g}", VIOLET, 0.0)
        group_mats.append(mat)
        cu = bpy.data.curves.new(f"Trans{g}", "CURVE")
        cu.dimensions = "3D"
        cu.bevel_depth = 0.0018
        for _ in range(n_lines // groups):
            a, b = rnd.sample(range(n_levels), 2)
            x = rnd.uniform(-3.5, 3.5)
            sp = cu.splines.new("POLY")
            sp.points.add(1)
            depth = rnd.gauss(0, 1.2)
            sp.points[0].co = (x, depth, levels[a], 1)
            sp.points[1].co = (x + rnd.uniform(-0.15, 0.15), depth + rnd.uniform(-0.2, 0.2), levels[b], 1)
        ob = bpy.data.objects.new(f"Trans{g}", cu)
        sc.collection.objects.link(ob)
        ob.data.materials.append(mat)
        styles.tag(ob, "emitter")
        M.set_emission_strength(mat, 1, 0.0)
        M.set_emission_strength(mat, 10 + 12 * g, 0.0)
        peak = 0.8 + 2.4 * ((g * 7) % groups) / groups     # groups glow at different strengths
        M.set_emission_strength(mat, 18 + 12 * g, peak)
        # B1_20 part (frames 170+): the web dims while a beam forms
        M.set_emission_strength(mat, 170, peak)
        M.set_emission_strength(mat, 215, 0.25)
    beam_mat = M.emission("Beam", VIOLET, 0.0)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.06, depth=12, location=(6.0, 0, 0), rotation=(0, math.pi / 2, 0))
    beam = bpy.context.object
    beam.name = "ConvergedBeam"
    beam.data.materials.append(beam_mat)
    styles.tag(beam, "emitter")
    for f, v in ((1, 0.0), (175, 0.0), (205, 9.0), (380, 7.0)):
        M.set_emission_strength(beam_mat, f, v)
    import sample_b1 as B
    # B1_19: start close on a few floors, pull back until the web fills frame
    B._camera("CamB1_19", [(1, (0.4, 0, 0.3), (0.5, -1.4, 0.35), 24, 11.0),
                           (160, (0, 0, 0), (0.0, -11.0, 1.0), 24, 11.0)])
    # B1_20: arc around as the lines give way to one beam
    B._camera("CamB1_20", [(150, (1.5, 0, 0), (-4.0, -9.0, 2.5), 35, 11.0),
                           (360, (4.0, 0, 0), (2.0, -10.5, 3.5), 35, 11.0)])


def build(variant="atom", seed=23):
    sc = C.reset_scene(FRAMES if variant == "atom" else 380)
    C.set_world(top=(0, 0, 0), horizon=(0, 0, 0), bottom=(0, 0, 0))
    C.set_color_management(exposure=0.0)
    rnd = random.Random(seed)
    if variant == "atom":
        build_atom(sc, rnd)
    else:
        build_web(sc, rnd)
    return sc
