"""R25 mbeam helper (root-cause row 4: machine density, 3 depth layers of REAL parts - no texture wall, no fog).
Called from misc_beam_r25h.post() for the shots of r2_misc.R25_BEAM; only A2_03 / B8_17 get parts here.

B8_17 (R24 review: 「晶圆台只是一块素黑方块」「背景是同一种灰柜面板重复铺开」):
  mid-ground = the wafer stage itself becomes a machined part: polished interferometer mirror bars along the two
  camera-side chuck edges, a metrology ring with alignment fiducials around the wafer, corner sensor plates, a bolted
  skirt and an energy chain with its cables trailing off the stage (all parented to the moving stage rig);
  back = a rack row (card cages / pumps / valves via parts_kit_r8.populate_wall) in front of the repeated wall panels;
  foreground = two out-of-focus vacuum lines + a bellows at the left frame edge, close to the lens.
A2_03 (「箱内仍偏空」): foreground soft pipes at the frame edge, mid-ground pumps / valves in the empty bay floor,
  back = card cages + manifold on the rear plane.
"""
import math

import bpy
from mathutils import Vector

import kit_r2 as K
import parts_kit_r8 as PK


def _pal():
    M = K.palette()
    return M


def _parent_keep(obs, rig, frame, sc):
    sc.frame_set(frame)
    inv = rig.matrix_world.inverted()
    for o in obs:
        mw = o.matrix_world.copy()
        o.parent = rig
        o.matrix_parent_inverse = inv
        o.matrix_world = mw


def _b817(sc):
    M = _pal()
    rig = bpy.data.objects.get("WaferStageR21")
    chuck = bpy.data.objects.get("Chuck")
    f0 = 1
    sc.frame_set(f0)
    bb = [chuck.matrix_world @ Vector(c) for c in chuck.bound_box]
    x0, x1 = min(b.x for b in bb), max(b.x for b in bb)
    y0, y1 = min(b.y for b in bb), max(b.y for b in bb)
    z0, z1 = min(b.z for b in bb), max(b.z for b in bb)
    wafer = bpy.data.objects.get("Wafer")
    wb = [wafer.matrix_world @ Vector(c) for c in wafer.bound_box]
    wc = Vector(((min(b.x for b in wb) + max(b.x for b in wb)) / 2, (min(b.y for b in wb) + max(b.y for b in wb)) / 2,
                 z1))
    wr = (max(b.x for b in wb) - min(b.x for b in wb)) / 2
    P = PK.new_parts()
    mirror_bar = K.mat("StageMirrorBarR25", (0.86, 0.87, 0.9), metal=1.0, rough=0.04)
    mb_bar = K.MB()
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    # interferometer mirror bars: front (-y) edge and right (+x) edge, standing a little proud of the chuck top
    mb_bar.box((cx, y0 - 0.05, z1 - 0.06), (x1 - x0 + 0.1, 0.08, 0.2))
    mb_bar.box((x1 + 0.05, cy, z1 - 0.06), (0.08, y1 - y0 + 0.1, 0.2))
    bars = mb_bar.obj("StageMirrorBarsR25", mirror_bar, bevel=0.006)
    # bar carriers (anodised) under the bars + bolt rows
    P["anod"].box((cx, y0 - 0.05, z1 - 0.2), (x1 - x0 + 0.12, 0.12, 0.08))
    P["anod"].box((x1 + 0.05, cy, z1 - 0.2), (0.12, y1 - y0 + 0.12, 0.08))
    for i in range(14):
        x = x0 + 0.1 + i * (x1 - x0 - 0.2) / 13
        P["steel"].cyl((x, y0 - 0.115, z1 - 0.2), 0.016, 0.012, rot=(math.radians(90), 0, 0), seg=10)
    # metrology ring around the wafer (machined ring, dark ceramic + tick marks) + 3 alignment fiducial plates
    P["alu"].ring((wc.x, wc.y, z1 + 0.004), wr + 0.12, wr + 0.04, 0.012, seg=128)
    for k in range(72):
        a = 2 * math.pi * k / 72
        r0, r1 = wr + 0.05, wr + (0.1 if k % 6 == 0 else 0.075)
        P["chip"].tube((wc.x + math.cos(a) * r0, wc.y + math.sin(a) * r0, z1 + 0.011),
                       (wc.x + math.cos(a) * r1, wc.y + math.sin(a) * r1, z1 + 0.011), 0.004, seg=4)
    for (fx, fy) in ((x0 + 0.22, y0 + 0.22), (x1 - 0.22, y0 + 0.22), (x0 + 0.22, y1 - 0.22), (x1 - 0.22, y1 - 0.22)):
        P["alu_dark"].box((fx, fy, z1 + 0.006), (0.24, 0.24, 0.012))           # corner sensor plate
        P["glass"].box((fx, fy, z1 + 0.014), (0.16, 0.16, 0.006))
        P["led_c"].box((fx - 0.05, fy, z1 + 0.018), (0.08, 0.006, 0.002))      # fiducial cross
        P["led_c"].box((fx - 0.05, fy, z1 + 0.018), (0.006, 0.08, 0.002))
    # bolted skirt along the visible sides + energy chain trailing off the stage toward -x
    for i in range(10):
        x = x0 + 0.15 + i * (x1 - x0 - 0.3) / 9
        P["blast"].box((x, y0 - 0.005, (z0 + z1) / 2 - 0.12), (0.22, 0.02, 0.16))
    PK.drag_chain(P, (x0 - 0.05, cy + 0.6, z0 + 0.04), 1.6, R=0.16, w=0.14, axis=(-1, 0, 0))
    stage_obs = PK.finish(P, M, "StageR25") + [bars]
    _parent_keep(stage_obs, rig, f0, sc)
    # back racks: a populated rack row in front of the repeated wall panels (behind the stage, left of the column)
    PB = PK.new_parts()
    PK.populate_wall(PB, -6.2, -1.6, -0.3, 1.5, 4.2, seed=817, scale=1.2)
    # the row is a rack cabinet standing on the floor: plinth, side / middle posts, top cap, back panel
    PB["paint_grey"].box((-3.9, 4.45, -0.39), (4.8, 0.7, 0.18))
    for x in (-6.25, -3.9, -1.55):
        PB["alu_dark"].box((x, 4.0, 0.62), (0.1, 0.12, 2.0))
    PB["paint_grey"].box((-3.9, 4.45, 1.66), (4.8, 0.7, 0.08))
    PB["alu_dark"].box((-3.9, 4.75, 0.62), (4.8, 0.04, 2.1))
    back = PK.finish(PB, M, "RackR25")
    # foreground: the empty dark floor at lower right gets the stage's service run - a ribbed floor duct with its
    # hoses / cables coming in from the frame corner to a junction box beside the stage (nearest layer)
    PF = PK.new_parts()
    a, b = Vector((3.6, -3.4, -0.47)), Vector((1.15, -1.25, -0.47))
    ax = (b - a).normalized()
    L = (b - a).length
    rot = (0.0, 0.0, math.atan2(ax.y, ax.x))
    for i in range(int(L / 0.22)):
        c = a + ax * (0.11 + i * 0.22)
        PF["alu_dark"].box(c + Vector((0, 0, 0.05)), (0.2, 0.42, 0.1), rot=rot)
        PF["alu"].box(c + Vector((0, 0, 0.105)), (0.03, 0.44, 0.012), rot=rot)
    side = Vector((-ax.y, ax.x, 0.0))
    for j, key in enumerate(("cable_b", "rubber", "cable_g", "steel", "cable_b", "rubber")):
        o = side * (-0.15 + j * 0.06)
        PF[key].path([a + o + Vector((0, 0, 0.14)), a.lerp(b, 0.5) + o + Vector((0, 0, 0.13 + 0.01 * j)),
                      b + o + Vector((0, 0, 0.14)), b + o * 0.5 + Vector((-0.25, 0.25, 0.32))],
                     0.024 if key != "steel" else 0.03, seg=10)
    PF["paint_grey"].box(b + Vector((-0.3, 0.3, 0.2)), (0.5, 0.5, 0.4))          # junction box
    for k in range(4):
        PF["steel"].cyl(b + Vector((-0.3 + (k - 1.5) * 0.1, 0.04, 0.3)), 0.022, 0.05,
                        rot=(math.radians(90), 0, 0), seg=10)                        # cable glands
    fg = PK.finish(PF, M, "ForeR25")
    print(f"[R25 B8_17 dense] stage parts {len(stage_obs)} (chuck x {x0:.2f}..{x1:.2f} y {y0:.2f}..{y1:.2f}); "
          f"rack {len(back)}; foreground {len(fg)}", flush=True)


def _a203(sc):
    M = _pal()
    # back: a rack row standing in the dark bay right of the opened cage (behind PO4) + a card cage on the cage's
    # rear plate right of the mirrors
    PB = PK.new_parts()
    PK.populate_wall(PB, 3.3, 5.2, 0.35, 2.9, 1.2, seed=203, scale=1.1)
    PK.card_cage(PB, 2.45, 3.0, 1.12, 1.5, 1.3, seed=204)
    back = PK.finish(PB, M, "RackA203R25")
    # mid-ground: real vacuum parts on the empty cage floor, back-left of the wafer (clear of the NA cone)
    PMd = PK.new_parts()
    PK.turbo_pump(PMd, (0.42, 0.95, 1.36), n=(0, 0, -1), r=0.1)
    PK.gate_valve(PMd, (0.42, 0.95, 1.5), axis=(0, 0, 1), r=0.09, up=(1, 0, 0))
    PK.bellows(PMd, (0.42, 0.95, 1.58), (0.42, 0.95, 1.9), 0.08)
    PK.gauge(PMd, (0.62, 0.7, 1.12), n=(0, -1, 0))
    PK.manifold(PMd, 2.35, 3.0, 1.12, 0.95)
    mid = PK.finish(PMd, M, "MidA203R25")
    # foreground: a hose bundle draped along the cage's front sill (soft, nearest layer)
    PF = PK.new_parts()
    for i, key in enumerate(("cable_b", "rubber", "steel", "cable_g")):
        dz, dy = 0.03 * i, -0.04 * i
        PF[key].path([(-0.3, -1.2 + dy, 1.0 + dz), (0.8, -1.25 + dy, 1.04 + dz), (1.9, -1.22 + dy, 0.99 + dz),
                      (3.1, -1.28 + dy, 1.03 + dz)], 0.022 if key != "steel" else 0.03, seg=10)
    fg = PK.finish(PF, M, "ForeA203R25")
    print(f"[R25 A2_03 dense] back {len(back)} mid {len(mid)} fore {len(fg)}", flush=True)


def apply(sc, shot):
    fn = {"B8_17": _b817, "A2_03": _a203}.get(shot)
    if fn is not None:
        fn(sc)
