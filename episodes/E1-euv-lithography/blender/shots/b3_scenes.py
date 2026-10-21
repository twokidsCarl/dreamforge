"""B3 — collector to intermediate focus (F56). Variants:

  burst    B3_01  a spherical shell of violet rays leaving the plasma in every direction
  focus    B3_05  hundreds of rays: focus 1 -> collector -> focus 2, pulsed several times
  handoff  B3_06  xray: vessel neck docking into the much larger scanner body at IF
  nave     B3_07  push through the IF aperture into a dark, clean vacuum with mirror edges lit
"""
import math
import random

import bpy
from mathutils import Vector

import build_source as S
import build_vacuum as V
import common as C
import materials as M
import sample_b1 as B
import styles

FRAMES = 260
VIOLET = (0.62, 0.45, 1.0)


def _curve(name, pts, mat, radius=0.012):
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = radius
    sp = cu.splines.new("POLY")
    sp.points.add(len(pts) - 1)
    for i, p in enumerate(pts):
        sp.points[i].co = (*p, 1)
    ob = bpy.data.objects.new(name, cu)
    bpy.context.scene.collection.objects.link(ob)
    ob.data.materials.append(mat)
    styles.tag(ob, "rays")
    return ob


def burst(sc, rnd, n=420):
    core = M.emission("Core", (0.95, 0.9, 1.0), 30.0)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.2, location=(0, 0, 0))
    ob = bpy.context.object
    ob.data.materials.append(core)
    styles.tag(ob, "emitter")
    mat = M.emission("Ray", VIOLET, 5.0)
    for k in range(n):
        d = Vector((rnd.gauss(0, 1), rnd.gauss(0, 1), rnd.gauss(0, 1))).normalized()
        r = _curve(f"Ray{k}", [(0, 0, 0), tuple(d * 40)], mat, radius=0.006)
        r.data.bevel_factor_start = 0.0
        r.data.bevel_factor_end = 0.0
        f0 = 2 + int(rnd.uniform(0, 8))
        r.data.keyframe_insert("bevel_factor_end", frame=f0)
        r.data.bevel_factor_end = 0.35
        r.data.keyframe_insert("bevel_factor_end", frame=f0 + 60)
        r.data.keyframe_insert("bevel_factor_start", frame=f0 + 10)
        r.data.bevel_factor_start = 0.25
        r.data.keyframe_insert("bevel_factor_start", frame=f0 + 60)
    B._camera("CamB3_01", [(1, (0, 0, 0), (0.6, 2.2, 0.5), 18, 11.0),
                           (130, (0, 0, 0), (2.8, 9.0, 2.2), 18, 11.0)])


def focus(sc, rnd):
    S.collector()
    S.collector_housing()
    rays, mat = S.light_rays(n=220, seed=9)
    for r in rays:
        r.data.bevel_factor_end = 0.0
    core = M.emission("Core", (0.95, 0.9, 1.0), 0.0)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.18, location=(0, 0, 0))
    ob = bpy.context.object
    ob.data.materials.append(core)
    styles.tag(ob, "emitter")
    dot = M.emission("IFDot", (0.9, 0.85, 1.0), 0.0)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.14, location=(S.IF_X, 0, 0))
    ifo = bpy.context.object
    ifo.data.materials.append(dot)
    styles.tag(ifo, "emitter")
    pulses = [4, 28, 46, 62, 76]                  # repeated pulses, accelerating
    for f0 in pulses:
        for r in rays:
            r.data.bevel_factor_end = 0.0
            r.data.keyframe_insert("bevel_factor_end", frame=f0)
            r.data.bevel_factor_end = 1.0
            r.data.keyframe_insert("bevel_factor_end", frame=f0 + 10)
        M.set_emission_strength(core, f0, 0.0)
        M.set_emission_strength(core, f0 + 1, 40.0)
        M.set_emission_strength(core, f0 + 6, 4.0)
        M.set_emission_strength(dot, f0 + 9, 2.0)
        M.set_emission_strength(dot, f0 + 11, 60.0)
        M.set_emission_strength(dot, f0 + 16, 8.0)
    s = mat.node_tree.nodes["Emission"].inputs["Strength"]
    s.default_value = 1.4
    B._camera("CamB3_05", [(1, (5.0, 0, 0), (5.0, -30.0, 6.0), 35, 11.0),
                           (90, (5.5, 0, 0), (5.5, -28.0, 5.4), 35, 11.0)])


def handoff(sc, rnd):
    V.source_vessel()
    S.collector()
    S.collector_housing()
    S.light_rays(n=120, seed=4)
    S.intermediate_focus()
    # the scanner body the neck docks into (stylised): a large housing beyond IF
    panel = M.principled("ScannerPanel", (0.78, 0.8, 0.82), metallic=0.2, roughness=0.45)
    bpy.ops.mesh.primitive_cube_add(location=(40.0, 0, 6.0))
    body = bpy.context.object
    body.name = "ScannerBody"
    body.scale = (24.0, 22.0, 22.0)
    bev = body.modifiers.new("Bevel", "BEVEL")
    bev.width = 1.2
    bev.segments = 3
    body.data.materials.append(panel)
    styles.tag(body, "shell")
    B._camera("CamB3_06", [(1, (6.0, 0, 0), (10.0, -24.0, 8.0), 30, 11.0),
                           (214, (24.0, 0, 4.0), (8.0, -78.0, 46.0), 30, 11.0)])


def nave(sc, rnd):
    """B3_07: through the intermediate focus into the illuminator, as the real optics are laid out (the High-NA
    train from build_machine, after ZEISS 2024 s.13): small fold mirror, field facet mirror, pupil facet mirror,
    each lighting up as the beam turns on it. Only the mirrors and the light path are shown."""
    import build_machine as BM
    C.set_world(top=(0.004, 0.005, 0.008), horizon=(0.002, 0.002, 0.004), bottom=(0.0, 0.0, 0.001))
    path, pmat = BM.machine()
    keep = ("FoldMirror", "Facet", "POMirror", "Reticle", "LightPath")
    for ob in list(bpy.data.objects):
        if ob.type in ("MESH", "CURVE") and not ob.name.startswith(keep):
            ob.hide_render = True
    ax = Vector(BM.SRC_AXIS)                             # points from the IF back toward the source
    rot = (-ax).to_track_quat("Z", "Y").to_euler()
    plate_mat = M.dark_anodized("Aperture")
    bpy.ops.mesh.primitive_cylinder_add(radius=1.2, depth=0.06, vertices=96, location=BM.IF, rotation=rot)
    plate = bpy.context.object
    bpy.ops.mesh.primitive_cylinder_add(radius=0.12, depth=0.5, vertices=64, location=BM.IF, rotation=rot)
    hole = bpy.context.object
    hole.hide_render = hole.hide_viewport = True
    bo = plate.modifiers.new("Hole", "BOOLEAN")
    bo.object = hole
    bo.operation = "DIFFERENCE"
    plate.data.materials.append(plate_mat)
    styles.tag(plate, "structure")
    glow = M.emission("IFPoint", (0.8, 0.7, 1.0), 25.0)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.03, location=BM.IF)
    gp = bpy.context.object
    gp.data.materials.append(glow)
    styles.tag(gp, "emitter")
    # the beam draws on from the IF to the reticle as the camera flies through
    n = len(BM.PATH) - 1
    i_if, i_ret = BM.PATH.index(BM.IF), BM.PATH.index(BM.RETICLE)
    path.data.bevel_factor_start = i_if / n
    for f, v in ((1, i_if / n), (30, i_if / n), (120, i_ret / n)):
        path.data.bevel_factor_end = v
        path.data.keyframe_insert("bevel_factor_end", frame=f)
    B._area("NaveKey", tuple(Vector(BM.FACET1) + Vector((0, -6, 4))), (0.9, 0, 0), 8, 300, (0.6, 0.7, 1.0))
    start = Vector(BM.IF) + ax * 2.2 + Vector((0, -0.25, 0.1))
    B._camera("CamB3_07", [(1, BM.IF, tuple(start), 24, 4.0),
                           (60, BM.FOLD, tuple(Vector(BM.IF) + ax * 0.15 + Vector((0, -0.3, 0.1))), 24, 4.0),
                           (132, BM.FACET2, tuple(Vector(BM.FOLD) + Vector((0.4, -2.2, 0.6))), 24, 4.0)])


def build(variant="burst", seed=31):
    sc = C.reset_scene(FRAMES)
    C.set_world(top=(0, 0, 0), horizon=(0, 0, 0), bottom=(0, 0, 0))
    C.set_color_management(exposure=0.4)
    rnd = random.Random(seed)
    {"burst": burst, "focus": focus, "handoff": handoff, "nave": nave}[variant](sc, rnd)
    return sc
