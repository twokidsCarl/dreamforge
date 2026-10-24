"""R29 row 6, B6_12 (misc_r29.B612BG_R29): defocused machine context far behind the chuck / mask / pellicle -
reticle-stage rails + carriage, a viewport, a gas panel (kit_r27 parts, few / big / different), dim satin, invisible
to glossy rays (nothing new reflects in the mask face or the pellicle). Never touches the pellicle, mask face, hoses,
labels or the R28 misc_r28 rows."""
import math

import bpy

import kit_r2 as K

WALL_Y = 7.5
X0, X1 = -11.0, 1.0
LIGHT_W = 20.0


def apply(sc):
    import kit_r27 as KR
    import hero_kit_r10 as H
    from misc_r29_b407 import _dim
    out = []
    P = H.new_parts()
    P["paint_grey"].box(((X0 + X1) / 2, WALL_Y + 0.06, 5.5), (X1 - X0, 0.12, 9.0))          # machine frame skin
    kinds = KR.named_row(P, X0 + 1.0, X1 - 1.5, 4.3, 7.8, WALL_Y, kinds=("viewport_stack", "gas_panel", "valve_island"),
                         seed=12, scale=2.0, depth=1.2)
    # reticle-stage rails: two long linear guides + carriage across the frame, in front of the wall
    for z in (3.1, 3.75):
        P["brushed"].box(((X0 + X1) / 2, WALL_Y - 0.5, z), (X1 - X0, 0.35, 0.22))
        P["alu_dark"].box(((X0 + X1) / 2, WALL_Y - 0.72, z), (X1 - X0, 0.1, 0.08))
    for xc in (-6.5, -2.0):
        P["blast"].box((xc, WALL_Y - 0.95, 3.42), (1.6, 0.5, 1.1))                          # stage carriage blocks
    for ob in KR.finish(P, "MachineBgR29"):
        if ob.name.endswith("paint_grey"):
            ob.data.materials[0] = K.mat("MachineSkinR29", (0.1, 0.11, 0.13), metal=0.5, rough=0.5)
        else:
            ob.data.materials[0] = _dim(ob.data.materials[0])
        ob.visible_glossy = False
        out.append(ob)
    lt = K.area("MachineWashR29", (-4.5, WALL_Y - 3.5, 7.0), (-4.5, WALL_Y, 4.0), 6.0, LIGHT_W, (0.8, 0.86, 1.0))
    lt.visible_camera = False
    lt.visible_glossy = False
    print(f"[R29 B6_12] B612BG_R29: machine wall y={WALL_Y} kinds {kinds} + 2 stage rails ({len(out)} objs)", flush=True)
