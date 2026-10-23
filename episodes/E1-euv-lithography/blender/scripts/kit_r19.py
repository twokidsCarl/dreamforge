"""Round 19 (P1): shared wall de-duplication kit - R19 root cause #3 (main process owns this file; module agents
import it READ-ONLY).

R18 review (p1 / p2): A0_10 mid-bay back wall, B8_03 stage deck, B3_02 right wall, B1_18 / B1_22 back walls are
"one kind of grid tiled across" - nothing can be named. Cause: wall_r12 cuts a wall into up to 14 small cells and
the scene-wide no-repeat counter hands each cell a different small part on a near-identical base plate; at
960x540 the equal cells + plates read as a grid, not as parts.

wall_r19 = few, BIG, different assemblies, strong stepped relief and something crossing the blocks:
  - only the six R19 types, each at most once per wall (fresh counter per wall):
      valve_island   solenoid valve island + air tubes
      drag_chain     energy-chain loop on a bracket with its cable bundle
      manifold       coolant bundle: distribution block, flow meters, blue / white hoses
      gas_panel      regulators with dial gauges, quarter-turn valves, bent stainless lines
      ion_pump       ion getter pump between magnet blocks, HV feedthrough
      power_supply   rack power box: vented chassis, knobs, display, cable loom
  - n blocks (default 5-6 depending on area) instead of up to 14 -> each part is big enough to be named
  - base-plate standoff 0.02 ... 0.16 m (relief steps you can see), alternating finishes
  - one coolant-hose run (4 hoses with clamps) crossing the wall diagonally in front of the blocks + one cable
    harness, so the eye never reads equal cells

deck_r19 = the same layout lying on a horizontal deck facing +Z (B8_03 stage deck instead of the socket grid).

Both take keep / front_y like wall_r11 (keep-clear spheres for optics and lines of sight).
"""
import math
import random

from mathutils import Matrix, Vector

import hero_kit_r10 as H
import hero_kit_r11 as H11
import hero_kit_r12 as H12

TYPES = ("valve_island", "drag_chain", "manifold", "gas_panel", "ion_pump", "power_supply")
KINDS19 = {k: H12.KINDS12[k] for k in TYPES}
FIT19 = {"wide": ("valve_island", "drag_chain", "power_supply", "manifold", "gas_panel"),
         "tall": ("manifold", "gas_panel", "ion_pump"),
         "any": ("ion_pump", "gas_panel", "manifold", "power_supply", "valve_island")}


def _nblocks(w, h, scale, n):
    if n is not None:
        return n
    return max(3, min(6, int(w * h / (0.9 * scale) ** 2) + 2))


def wall_r19(P, x0, x1, z0, z1, y0, seed=0, keep=(), front_y=None, scale=1.0, depth=1.0, n=None, tone="mixed",
             hoses=True, log=None):
    """Mixed wall on the plate whose front face is y = y0 (parts toward -Y). Returns the kinds used."""
    w, h = x1 - x0, z1 - z0
    nb = _nblocks(w, h, scale, n)
    use = {}                                                     # fresh per wall: six types, none twice
    kinds = H11.wall_r11(P, x0, x1, z0, z1, y0, seed=seed + 1900, keep=keep, scale=scale, depth=depth * 1.25,
                         blocks=nb, tone=tone, front_y=front_y, use=use,
                         fallback=("power_supply", "gas_panel", "valve_island"), kinds_tab=KINDS19, fit_tab=FIT19)
    rnd = random.Random(seed * 53 + 19)
    s = scale
    # deeper, uneven relief: push 1-2 of the big blocks' assemblies out further with a machined riser plate
    # (wall_r11 picks 0.02-0.07; R19 adds risers 0.06-0.09 under alternate blocks so steps read at 960x540)
    for i in range(min(2, nb)):
        bx = x0 + w * rnd.uniform(0.15, 0.85)
        bz = z0 + h * rnd.uniform(0.2, 0.8)
        bw, bh = w * rnd.uniform(0.12, 0.2), h * rnd.uniform(0.15, 0.3)
        c = (bx, y0 - 0.004, bz)
        if H11._clear(keep, c, max(bw, bh)) and (front_y is None or y0 - 0.09 * s > front_y):
            P["brushed" if i % 2 == 0 else "anod"].box((bx, y0 - 0.045 * s, bz), (bw, 0.012 * s, bh))
    if hoses:
        # coolant run crossing the blocks diagonally (in front of them, behind keep-clear zones)
        yh = y0 - 0.17 * s * depth
        if front_y is not None:
            yh = max(yh, front_y + 0.01)
        za, zb = z0 + h * rnd.uniform(0.62, 0.85), z0 + h * rnd.uniform(0.12, 0.35)
        pts = [(x0 + 0.06 * w, yh, za), (x0 + 0.45 * w, yh - 0.02 * s, (za + zb) / 2 + 0.08 * h),
               (x1 - 0.06 * w, yh, zb)]
        if all(H11._clear(keep, p, 0.06 * s) for p in pts):
            H.cooling_bundle(P, pts, k=4, r=0.011 * s, clamp_every=0.4 * s, up=(0, -1, 0))
            if log is not None:
                log.append("coolant_run")
    print(f"[wall_r19] seed {seed}: {len(set(k for k in kinds if '(' not in k))} types / {len(kinds)} blocks: {kinds}")
    if log is not None:
        log.extend(kinds)
    return kinds


def deck_r19(P, x0, x1, y0, y1, z, seed=0, keep=(), scale=1.0, depth=0.8, n=None, hoses=True, log=None):
    """Mixed deck lying flat on the plane z (parts toward +Z): wall_r19 built in a scratch batch in the XZ plane
    then turned +90 deg about X (wall -Y front -> deck +Z up) and moved onto the deck rectangle."""
    T = H.new_parts()
    # wall frame: x along deck x, wall z along deck y, plate front at y = 0 (parts toward -Y)
    # keep spheres mapped into the wall frame: deck (x, y, zz) -> wall (x, -(zz - z), y)
    kw = [((kx, -(kz - z), ky), kr) for (kx, ky, kz), kr in [(tuple(k), r) for k, r in keep]]
    kinds = wall_r19(T, x0, x1, y0, y1, 0.0, seed=seed, keep=kw, scale=scale, depth=depth, n=n, hoses=hoses,
                     log=log)
    # wall (x, y, zz) -> deck (x, zz, z - y): proper rotation, winding kept
    R = Matrix.Translation((0, 0, z)) @ Matrix(((1, 0, 0, 0), (0, 0, 1, 0), (0, -1, 0, 0), (0, 0, 0, 1)))
    for mb in T.values():
        for v in mb.bm.verts:
            v.co = R @ v.co
        mb.bm.normal_update()
    H11._merge(P, T)
    return kinds
