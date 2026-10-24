"""Round 28 hook (cut sub-agent; shots in r2_cutaway.R28_CUT = B5_01 / B7_06). Layered AFTER the R22..R27 hooks
(B5_01: cut_beam_r26 legs + cut_kit_r27 KIT/FACET; B7_06: cut_hero_r25 + cut_r27 ONETURN/KIT). One switch per row:

  ONEPATH_R28 (row 3b, p2 #2 「B7_06 的 85% 帧、B5_01 的 55% 帧，把非当前段淡到 20% 以下」): every beam leg gets a
      per-frame curve (cut_r28_fade.py) on its emission strength AND its transparent-mix factor: the current leg 1.0,
      every non-current leg LOW (legs are NOT deleted). Story order (fractions of the shot):
        B5_01  IllumPathR24  leg0 IF -> FFM  [0, 0.40]   leg1 FFM -> PFM [0.40, 0.70]   leg2 PFM -> condenser [0.70, 1]
               (25 % frame = IF -> FFM, 55 % frame = FFM -> PFM only bright: the IF->FFM / FFM->PFM overlap near the FFM
               now has ONE bright leg)
        B7_06  PO27Beam      leg0 roof -> M5 ring [0, 0.42]  leg1 M5 -> M6 [0.42, 0.70]  leg2 M6 -> M5 hole -> wafer
               [0.70, 1] (the R27 reveal keys; 85 % frame = converging cone only bright)
      Landing spots follow the legs that touch them.
  WALL_R28 (row 5, p2 #5 「B5_01 右墙…都是同一种格子铺满，换成阀岛、涡轮泵、气路面板、冷却管束」): B5_01 right housing side
      wall (x = WALL_X plane, facing -X toward the camera) gets one kit_r27.named_row (one block per kind, few / big /
      different, kinds not used on the R27 left wall) -> the shot carries >= 10 nameable kinds. R27 left wall + FFM x1.3
      untouched.
Remove a shot from r2_cutaway.R28_CUT -> exact R27 pixels; set a switch False -> that row returns to R27.
"""
import math

import bpy
from mathutils import Matrix

ONEPATH_R28 = True
WALL_R28 = True

LOW = {"B5_01": 0.14, "B7_06": 0.17}   # non-current leg factor on strength AND alpha (emitted radiance ~ LOW^2); 0.10 = ghost legs invisible (8 spp: light from nowhere at M5 / FFM)
RAMP = 6              # frames of cross-fade
WINDOWS = {
    "B5_01": ("IllumPathR24", [(0, 0.0, 0.40), (1, 0.40, 0.70), (2, 0.70, 1.0)]),
    "B7_06": ("PO27Beam", [(0, 0.0, 0.42), (1, 0.42, 0.70), (2, 0.70, 1.0)]),
}
WALL_X = -0.80                         # R2_housing right side wall face (B5_01 rays at f64 / f99 hit x -0.77..-0.78)
WALL_Y = (0.05, 1.0)
WALL_Z = (1.55, 3.05)
WALL_KINDS = ("metrology_ring", "card_cage", "viewport_stack", "manifold")
WALL_SCALE, WALL_DEPTH = 1.0, 1.2


def pre(variant, shot, mod):
    return None


def _chain(name):
    legs, spots = [], []
    i = 0
    while True:
        obs = [o for o in bpy.data.objects if o.name == f"{name}Leg{i}" or o.name.startswith(f"{name}Leg{i}.")]
        if not obs:
            break
        legs.append(obs)
        i += 1
    for j in range(len(legs) + 1):
        spots.append(bpy.data.objects.get(f"{name}Spot{j}"))
    return {"legs": legs, "spots": spots}


def _onepath(sc, shot):
    import cut_r28_fade as F
    name, win = WINDOWS[shot]
    ch = _chain(name)
    if len(ch["legs"]) < len(win):
        print(f"[r28u] {shot} ONEPATH chain {name} has {len(ch['legs'])} legs - skipped", flush=True)
        return
    F.fade(sc, ch, win, LOW[shot], RAMP, tag=shot)


def _wall(sc):
    import hero_kit_r10 as HK
    import kit_r27 as K27
    P = HK.new_parts()
    # local frame: plate at y = 0 facing -Y, local x = -world y; rotated -90 deg about Z -> faces -X at x = WALL_X
    ks = K27.named_row(P, -WALL_Y[1], -WALL_Y[0], WALL_Z[0], WALL_Z[1], 0.0, kinds=WALL_KINDS, seed=28,
                       scale=WALL_SCALE, depth=WALL_DEPTH)
    obs = K27.finish(P, "B5R28Wall") or []
    M = Matrix.Translation((WALL_X, 0, 0)) @ Matrix.Rotation(-math.pi / 2, 4, "Z")
    for o in obs:
        o.matrix_world = M @ o.matrix_world
    print(f"[r28u] B5_01 WALL right kinds {K27.count(ks)} {ks} objs {len(obs)}", flush=True)


def post(sc, variant, shot):
    if shot not in WINDOWS:
        return sc
    if shot == "B5_01" and WALL_R28:
        _wall(sc)
    if ONEPATH_R28:
        _onepath(sc, shot)
    return sc
