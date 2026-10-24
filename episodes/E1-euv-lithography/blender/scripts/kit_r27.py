"""Round 27 shared kit (main process; R27_ROOT_CAUSE row 4 "nameable parts instead of repeated grids").

R26 review p2 #3: 「用可叫名字的零件替换重复格栅：hexapod、计量环、干涉仪头、涡轮泵、阀岛、电源箱」 - A0_10 illuminator housing
is a plain white box, B7_06 / B5_01 back walls are one grid repeated. hero_kit_r10/r11/r12 already own every builder;
what failed is the LAYOUT: wall_r11/r12 split a wall into 10-14 small blocks, so each part is 20-40 px and the eye reads
"a grid". This module does the opposite: FEW, BIG, DIFFERENT parts.

  named_row(P, x0, x1, z0, z1, y0, kinds=SIX, seed=0, scale=1.0, front_y=None)
      one block per kind (no kind twice), widths jittered 0.75-1.3, laid out in a single row (or two rows when the
      region is taller than wide), each built with the hero_kit_r12 KINDS12 builder at full block size. Plate faces -Y
      (front of the wall toward a camera at -Y), same convention as wall_r11. Returns the list of kinds.
  dress_box(P, lo, hi, faces=("-y", "+z"), kinds=..., seed=0, scale=1.0)
      mounts named parts on the visible faces of a plain housing box (axis-aligned lo/hi corners): the -Y face gets a
      named_row inset 6 % from the edges (machined skin stays visible around it), +Z gets a turbo pump + gate valve
      standing on the roof, so a "white box" reads "a machine module with a pump, valves, power, sensors".
  count(kinds) -> number of distinct nameable kinds (acceptance: >= 6 per shot).

Everything is plain geometry through hero_kit_r10.new_parts / finish (no textures, no fonts -> no repo-path risk).
"""
import random

from mathutils import Vector

import hero_kit_r10 as H
import hero_kit_r11 as H11
import hero_kit_r12 as H12

SIX = ("hexapod_mount", "metrology_ring", "turbo_gate", "valve_island", "power_supply", "ion_pump")
ROOF = ("turbo_gate", "gate_valve")
ALIAS = {"hexapod_mount": "hexapod", "metrology_ring": "metrology ring", "turbo_gate": "turbo pump",
         "valve_island": "valve island", "power_supply": "power cabinet", "ion_pump": "ion pump",
         "gate_valve": "gate valve", "gas_panel": "gas panel", "viewport_stack": "viewport", "pump": "pump",
         "card_cage": "electronics rack", "manifold": "manifold", "bellows_spool": "bellows", "drag_chain": "drag chain"}


def count(kinds):
    return len({k.split("(")[0] for k in kinds})


def _build(P, kind, cx, cz, w, h, yf, s, rnd, depth=1.0):
    fn = H12.KINDS12[kind][0]
    T = H.new_parts()
    fn(T, cx, cz, w, h, yf, s, rnd, depth)
    H11._merge(P, T)


def named_row(P, x0, x1, z0, z1, y0, kinds=SIX, seed=0, scale=1.0, depth=1.0, plate="paint_grey", log=None):
    rnd = random.Random(seed * 97 + 13)
    kinds = list(dict.fromkeys(kinds))
    w, h = x1 - x0, z1 - z0
    rows = 2 if h > w * 0.8 and len(kinds) >= 4 else 1
    per = [kinds[i::rows] for i in range(rows)]
    P[plate].box(((x0 + x1) / 2, y0 - 0.004, (z0 + z1) / 2), (w, 0.008, h))
    out = []
    g = 0.04 * scale
    for r, ks in enumerate(per):
        rz0 = z0 + (h / rows) * r
        rz1 = rz0 + h / rows
        wts = [rnd.uniform(0.75, 1.3) for _ in ks]
        tot = sum(wts)
        x = x0
        for k, wt in zip(ks, wts):
            bw = w * wt / tot
            cx, cz = x + bw / 2, (rz0 + rz1) / 2
            bd = 0.03 * scale
            P["brushed" if len(out) % 2 else "blast"].box((cx, y0 - bd / 2, cz), (bw - g, bd, (rz1 - rz0) - g))
            _build(P, k, cx, cz, (bw - g) * 0.92, ((rz1 - rz0) - g) * 0.92, y0 - bd, scale, rnd, depth)
            out.append(k)
            x += bw
    if log is not None:
        log.extend(out)
    print(f"[kit_r27] named_row seed {seed}: {count(out)} kinds {[ALIAS.get(k, k) for k in out]}", flush=True)
    return out


def dress_box(P, lo, hi, faces=("-y", "+z"), kinds=SIX, seed=0, scale=1.0, inset=0.06, depth=0.8, log=None):
    lo, hi = Vector(lo), Vector(hi)
    out = []
    if "-y" in faces:
        dx, dz = (hi.x - lo.x) * inset, (hi.z - lo.z) * inset
        out += named_row(P, lo.x + dx, hi.x - dx, lo.z + dz, hi.z - dz, lo.y - 0.005, kinds=kinds, seed=seed,
                         scale=scale, depth=depth)
    if "+z" in faces:
        rnd = random.Random(seed + 5)
        cx = (lo.x + hi.x) / 2
        span = (hi.x - lo.x)
        for i, k in enumerate(ROOF):
            x = lo.x + span * (0.28 + 0.44 * i)
            m = min(span * 0.3, 0.8 * scale)
            # roof parts: build in a temporary wall frame (x/z plane) then the block stands on the roof facing -Y
            _build(P, k, x, hi.z + m * 0.5, m, m, (lo.y + hi.y) / 2 - (hi.y - lo.y) * 0.1, scale, rnd, depth)
            out.append(k)
    if log is not None:
        log.extend(out)
    print(f"[kit_r27] dress_box {tuple(round(v, 2) for v in lo)}..{tuple(round(v, 2) for v in hi)}: {count(out)} kinds",
          flush=True)
    return out


def finish(P, tag, M=None):
    """hero_kit_r10.finish with the shared kit_r2 palette (one palette per scene is cached in _PAL)."""
    import kit_r2 as K
    if M is None:
        if "M" not in _PAL:
            _PAL["M"] = K.palette()
        M = _PAL["M"]
    return H.finish(P, M, tag)


_PAL = {}
