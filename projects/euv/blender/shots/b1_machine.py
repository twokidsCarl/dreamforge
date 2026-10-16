"""B1_25 (fab hall with the drive-laser beam tube) and B1_28/B1_29 (light leaving the source and
heading into the scanner) — uses build_machine's stylised layout."""
import math

import bpy

import build_machine as BM
import common as C
import materials as M
import sample_b1 as B
import styles

FRAMES = 240


def build(variant="machine"):
    sc = C.reset_scene(FRAMES)
    C.set_color_management(exposure=0.4)
    if variant == "hall":
        C.set_world(top=(0.02, 0.022, 0.03), horizon=(0.01, 0.011, 0.015), bottom=(0.002, 0.002, 0.003))
        BM.fab_hall()
        # an orange light dot racing along the tube's observation slot (illustrative)
        mat = M.emission("TubeDot", (1.0, 0.42, 0.12), 60.0)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.06, location=(-23, -0.37, -1.85))
        dot = bpy.context.object
        dot.scale = (6, 1, 1)
        dot.data.materials.append(mat)
        styles.tag(dot, "emitter")
        for f in (1, 30, 70, 110, 140):
            dot.location.x = -23 + ((f - 1) % 40) / 40 * 22
            dot.keyframe_insert("location", frame=f)
        # stylised scanner blocks in the background
        dark = M.dark_anodized("HallMachine")
        for i, x in enumerate((6, 16, 26)):
            bpy.ops.mesh.primitive_cube_add(location=(x, 0, 0.3))
            blk = bpy.context.object
            blk.scale = (4.5, 1.8, 2.5)
            blk.data.materials.append(dark)
            styles.tag(blk, "env")
        B._area("HallKey", (0, -10, 8), (1.0, 0, 0), 30, 4000, (0.8, 0.85, 1.0))
        B._camera("CamB1_25", [(1, (-6, 0, -1.0), (-20, -6.0, -1.7), 20, 8.0),
                               (140, (-2, 0, -0.6), (-17, -7.0, -1.6), 20, 8.0)])
        return sc
    C.set_world(top=(0.03, 0.035, 0.05), horizon=(0.012, 0.014, 0.02), bottom=(0.003, 0.004, 0.006))
    path, pmat = BM.machine()
    path.data.bevel_factor_end = 0.0
    path.data.keyframe_insert("bevel_factor_end", frame=1)
    path.data.bevel_factor_end = 1.0
    path.data.keyframe_insert("bevel_factor_end", frame=100)
    B._area("MKey", (0, -9, 8), (0.9, 0, 0), 16, 2500, (0.8, 0.85, 1.0))
    B._area("MRim", (-6, 8, 4), (1.2, 0, 3.0), 10, 1500, (0.5, 0.7, 1.0))
    B._camera("CamB1_28", [(1, BM.IF, (-5.0, -4.2, 1.4), 28, 6.0),
                           (113, (0.5, 0, 0.6), (2.6, -5.2, 1.0), 28, 6.0)])
    B._camera("CamB1_29", [(100, (-1.4, 0, 1.0), (-3.6, -2.6, 0.7), 35, 6.0),
                           (160, (-0.6, 0, 1.4), (-2.8, -2.8, 1.0), 35, 6.0)])
    return sc
