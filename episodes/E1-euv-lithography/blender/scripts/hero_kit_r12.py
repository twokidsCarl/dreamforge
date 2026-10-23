"""Round 12 (P1): thicker shared nameable kit (R11 review: "~5-6 nameable types per shot (k2B 10+); rows of identical
terminal modules"). Extends hero_kit_r11 - no library rewrite.

New assemblies (one-word nameable):
  gate_valve      rectangular gate valve between two CF spools: body, bonnet, pneumatic actuator, position switch
  metrology_ring  machined ring on stand-offs with three interferometer / sensor heads and their fibre leads
  ion_pump        ion getter pump: box body between two pairs of magnet blocks, HV feedthrough + cable, CF neck
  bellows_spool   horizontal edge-welded bellows between two CF flanges with tie rods
  power_supply    rack power unit: vented chassis, handles, rotary knobs, display, rear cable loom

wall_r12: hero_kit_r11.wall_r11 with the 14-type table (terminal_rack dropped from the rotation - it was the
repeated DIN row) and a counter shared by all walls of one scene (reset()), so the walls of a shot together cycle
through every type before any type repeats. Blocks default to >= 10 per wall where there is room.

Also: planar_coils (B8_03 floor: herringbone coil windings on the granite, not a checkerboard) and
interferometer_head (fixed head on a post, aiming at a stage mirror bar).
"""
import math
import random

from mathutils import Vector

import hero_kit_r10 as H
import hero_kit_r11 as H11

_cyl, _ring, _bolt_circle = H._cyl, H._ring, H._bolt_circle


def gate_valve(P, cx, cz, w, h, yf, s, rnd, depth=1.0):
    m = min(w * 0.8, h)
    y = yf - m * 0.35 * depth - 0.03 * s
    c = Vector((cx, y, cz - h * 0.08))
    rb = m * 0.16
    for sx in (-1, 1):                                                         # CF spools left / right
        a = c + Vector((sx * m * 0.22, 0, 0))
        b = c + Vector((sx * min(w * 0.46, m * 0.62), 0, 0))
        P["steel"].tube(a, b, rb, seg=28)
        _ring(P["alu"], b, (sx, 0, 0), rb * 1.6, rb * 0.8, rb * 0.25, seg=36)
        _bolt_circle(P, b + Vector((sx * rb * 0.13, 0, 0)), (sx, 0, 0), rb * 1.32, 10, rb * 0.08, rb * 0.08, nuts=False)
        _ring(P["alu"], a, (sx, 0, 0), rb * 1.6, rb * 0.8, rb * 0.25, seg=36)
    P["blast"].box(c, (m * 0.42, m * 0.2, m * 0.56))                           # valve body
    P["alu_dark"].box(c + Vector((0, -m * 0.105, 0)), (m * 0.36, 0.006, m * 0.48))
    P["steel"].box(c + Vector((0, 0, m * 0.34)), (m * 0.3, m * 0.16, m * 0.12))  # bonnet
    _cyl(P["steel"], c + Vector((0, 0, m * 0.56)), (0, 0, 1), m * 0.09, m * 0.32, seg=24)    # actuator cylinder
    _cyl(P["alu_dark"], c + Vector((0, 0, m * 0.74)), (0, 0, 1), m * 0.11, m * 0.04, seg=24)
    P["solenoid"].box(c + Vector((m * 0.14, -m * 0.06, m * 0.5)), (m * 0.08, m * 0.06, m * 0.1))   # position switch
    P["hose_b"].path([c + Vector((m * 0.06, -m * 0.04, m * 0.7)), c + Vector((m * 0.2, -m * 0.08, m * 0.72)),
                      c + Vector((m * 0.3, 0.0, h * 0.42))], 0.005 * s, seg=6)
    P["hose_w"].path([c + Vector((-m * 0.06, -m * 0.04, m * 0.62)), c + Vector((-m * 0.22, -m * 0.08, m * 0.66)),
                      c + Vector((-m * 0.32, 0.0, h * 0.4))], 0.005 * s, seg=6)
    P["alu_dark"].box(Vector((cx, (yf + y) / 2, cz - h * 0.4)), (m * 0.3, yf - y, 0.03 * s))  # wall bracket


def metrology_ring(P, cx, cz, w, h, yf, s, rnd, depth=1.0):
    m = min(w, h)
    R = m * 0.4
    c = Vector((cx, yf - m * 0.25 * depth - 0.04 * s, cz))
    _ring(P["anod"], c, (0, -1, 0), R, R * 0.84, m * 0.07, seg=72)             # machined ring, face to camera
    _ring(P["alu"], c + Vector((0, -m * 0.036, 0)), (0, -1, 0), R * 0.98, R * 0.95, 0.004, seg=72)
    for k in range(4):                                                         # stand-offs to the wall
        a = math.radians(45 + 90 * k)
        p = c + Vector((R * 0.92 * math.cos(a), 0, R * 0.92 * math.sin(a)))
        P["steel"].tube(p, Vector((p.x, yf, p.z)), m * 0.02, seg=10)
    for k, a in enumerate((90, 210, 330)):                                     # three sensor heads on the ring
        d = Vector((math.cos(math.radians(a)), 0, math.sin(math.radians(a))))
        p = c + d * R * 0.92 + Vector((0, -m * 0.07, 0))
        P["brushed"].box(p, (m * 0.13, m * 0.1, m * 0.13))
        _cyl(P["glass"], p + Vector((0, -m * 0.052, 0)) - d * m * 0.02, (0, -1, 0), m * 0.035, 0.006, seg=20)
        _ring(P["steel"], p + Vector((0, -m * 0.053, 0)) - d * m * 0.02, (0, -1, 0), m * 0.045, m * 0.035, 0.008, seg=20)
        P["label"].box(p + Vector((m * 0.04, -m * 0.052, m * 0.045)), (m * 0.035, 0.002, m * 0.015))
        P["hose_w" if k % 2 else "cable_k"].path([p + d * m * 0.06, p + d * m * 0.16 + Vector((0, m * 0.05, 0)),
                                                  Vector((p.x + d.x * m * 0.25, yf - 0.01, cz - h * 0.45))],
                                                 0.004 * s, seg=6)
    P["coat"].box(c + Vector((0, -m * 0.02, 0)), (R * 0.6, 0.01, R * 0.06))    # reference bar across the bore


def ion_pump(P, cx, cz, w, h, yf, s, rnd, depth=1.0):
    m = min(w, h * 1.1)
    y = yf - m * 0.3 * depth - 0.05 * s
    c = Vector((cx, y, cz - h * 0.08))
    bw, bh, bd = m * 0.5, m * 0.55, m * 0.28
    P["steel"].box(c, (bw, bd, bh))                                           # pump body
    for sx in (-1, 1):                                                         # magnet pairs (dark blocks)
        for sz in (-1, 1):
            P["magnet2"].box(c + Vector((sx * (bw / 2 + m * 0.03), 0, sz * bh * 0.24)), (m * 0.06, bd * 1.1, bh * 0.42))
        P["alu_dark"].box(c + Vector((sx * (bw / 2 + m * 0.065), 0, 0)), (m * 0.012, bd * 1.2, bh * 1.02))   # yoke
    for k in range(5):                                                         # cell ribs on the front
        P["alu"].box(c + Vector((-bw * 0.4 + k * bw * 0.2, -bd / 2 - 0.003, 0)), (m * 0.012, 0.006, bh * 0.9))
    top = c + Vector((0, 0, bh / 2))
    _cyl(P["steel"], top + Vector((0, 0, m * 0.08)), (0, 0, 1), m * 0.08, m * 0.16, seg=24)  # neck
    _ring(P["alu"], top + Vector((0, 0, m * 0.17)), (0, 0, 1), m * 0.14, m * 0.07, m * 0.035, seg=32)
    _bolt_circle(P, top + Vector((0, 0, m * 0.19)), (0, 0, 1), m * 0.115, 8, m * 0.012, m * 0.012, nuts=False)
    hv = c + Vector((bw * 0.25, -bd / 2, -bh * 0.3))                           # HV feedthrough + cable
    _cyl(P["ceramic"], hv + Vector((0, -m * 0.04, 0)), (0, -1, 0), m * 0.03, m * 0.08, seg=16)
    _cyl(P["solenoid"], hv + Vector((0, -m * 0.1, 0)), (0, -1, 0), m * 0.04, m * 0.05, seg=16)
    P["cable_k"].path([hv + Vector((0, -m * 0.13, 0)), hv + Vector((m * 0.1, -m * 0.15, -m * 0.1)),
                       Vector((cx + w * 0.4, yf - 0.01, cz - h * 0.44))], m * 0.015, seg=8)
    P["label"].box(c + Vector((-bw * 0.2, -bd / 2 - 0.004, bh * 0.32)), (bw * 0.35, 0.002, bh * 0.1))
    P["alu_dark"].box(Vector((cx, (yf + y) / 2, c.z - bh / 2 - 0.02 * s)), (bw * 0.9, yf - y + bd / 2, 0.03 * s))


def bellows_spool(P, cx, cz, w, h, yf, s, rnd, depth=1.0):
    m = min(w * 0.6, h)
    r = m * 0.2
    y = yf - r * 1.4 - m * 0.2 * depth
    x0, x1 = cx - w * 0.4, cx + w * 0.4
    for x, sx in ((x0, -1), (x1, 1)):
        _ring(P["alu"], (x, y, cz), (1, 0, 0), r * 1.7, r * 0.7, r * 0.35, seg=40)
        _bolt_circle(P, Vector((x + sx * r * 0.18, y, cz)), (sx, 0, 0), r * 1.4, 12, r * 0.08, r * 0.08, nuts=False)
        P["steel"].tube(Vector((x, y, cz)), Vector((x, yf, cz)), r * 0.5, seg=20)  # back to the wall
    L = (x1 - x0) * 0.86
    nconv = max(8, int(L / (r * 0.16)))
    for k in range(nconv):                                                     # convolutions
        x = x0 + (x1 - x0) * 0.07 + L * (k + 0.5) / nconv
        _ring(P["steel"], (x, y, cz), (1, 0, 0), r * (1.18 if k % 2 else 1.06), r * 0.8, L / nconv * 0.9, seg=36)
    for a in (40, 160, 280):                                                   # tie rods
        o = Vector((0, math.cos(math.radians(a)), math.sin(math.radians(a)))) * r * 1.5
        P["alu_dark"].tube(Vector((x0, y, cz)) + o, Vector((x1, y, cz)) + o, r * 0.06, seg=8)


def power_supply(P, cx, cz, w, h, yf, s, rnd, depth=1.0):
    d = min(0.3 * s, h * 0.5) * depth
    yc = yf - d / 2
    nu = 2 if h > 0.45 * s else 1
    uh = h * 0.86 / nu
    for i in range(nu):
        z = cz - h * 0.43 + uh * (i + 0.5)
        P["paint_grey"].box((cx, yc, z), (w * 0.94, d, uh * 0.9))               # chassis
        fy = yf - d - 0.004
        P["anod"].box((cx, fy, z), (w * 0.96, 0.008, uh * 0.92))                # front panel
        for k in range(int(w * 0.5 / (0.018 * s))):                             # vent slots
            P["solenoid"].box((cx - w * 0.44 + k * 0.018 * s, fy - 0.005, z + uh * 0.2), (0.006 * s, 0.003, uh * 0.3))
        for sx in (-1, 1):                                                      # rack handles
            P["steel"].path([Vector((cx + sx * w * 0.45, fy, z - uh * 0.3)), Vector((cx + sx * w * 0.45, fy - 0.03 * s, z - uh * 0.25)),
                             Vector((cx + sx * w * 0.45, fy - 0.03 * s, z + uh * 0.25)), Vector((cx + sx * w * 0.45, fy, z + uh * 0.3))],
                            0.006 * s, seg=8)
        for k in range(3):                                                      # knobs
            _cyl(P["alu"], (cx + w * 0.08 + k * w * 0.1, fy - 0.012 * s, z - uh * 0.15), (0, -1, 0), uh * 0.09, 0.024 * s, seg=20)
        P["screen"].box((cx - w * 0.22, fy - 0.004, z - uh * 0.12), (w * 0.2, 0.002, uh * 0.22))
        P["label"].box((cx + w * 0.3, fy - 0.004, z + uh * 0.28), (w * 0.12, 0.002, uh * 0.08))
    H.cable_harness(P, [Vector((cx + w * 0.47, yf - d * 0.5, cz)), Vector((cx + w * 0.52, yf - 0.02, cz - h * 0.2)),
                        Vector((cx + w * 0.5, yf - 0.01, cz - h * 0.46))], n=4, r=0.006 * s, connector=False)


KINDS12 = dict(H11.KINDS)
KINDS12.pop("terminal_rack")
KINDS12.update({"gate_valve": (gate_valve, "any"), "metrology_ring": (metrology_ring, "any"),
                "ion_pump": (ion_pump, "any"), "bellows_spool": (bellows_spool, "wide"),
                "power_supply": (power_supply, "wide")})
FIT12 = {"wide": ("card_cage", "valve_island", "pump", "drag_chain", "bellows_spool", "power_supply", "gas_panel",
                  "manifold", "gate_valve"),
         "tall": ("viewport_stack", "manifold", "gas_panel", "hexapod_mount", "ion_pump"),
         "any": ("turbo_gate", "gate_valve", "metrology_ring", "ion_pump", "gas_panel", "hexapod_mount", "manifold",
                 "card_cage", "viewport_stack", "pump", "power_supply")}

USE = {}                    # shared per scene (reset() at the start of a build)


def reset():
    USE.clear()


def wall_r12(P, x0, x1, z0, z1, y0, seed=0, blocks=None, scale=1.0, log=None, **kw):
    """R11 wall with the 14-type table, no terminal rows, shared no-repeat counter; more, smaller blocks."""
    w, h = x1 - x0, z1 - z0
    if blocks is None:
        blocks = max(4, min(14, int(w * h / (0.42 * scale) ** 2 * 0.6) + 3))
    lg = [] if log is None else log
    out = H11.wall_r11(P, x0, x1, z0, z1, y0, seed=seed, blocks=blocks, scale=scale, log=lg, use=USE,
                       fallback=("power_supply", "card_cage", "gas_panel", "metrology_ring", "valve_island", "hexapod_mount"), kinds_tab=KINDS12, fit_tab=FIT12, **kw)
    print(f"[wall_r12] seed {seed}: {len(set(k for k in out if '(' not in k))} types / {len(out)} blocks: {out}")
    return out


# ------------------------------------------------------------------ B8_03 wafer-stage floor
def planar_coils(P, cx, cy, z, w, d, pitch=0.12):
    """Planar-motor stator seen through a clear epoxy top: rectangular coil windings (three nested loops each,
    long axis alternating, 3 x 3 groups turned 90 deg = herringbone), on a dark epoxy plate with a machined frame
    and coolant manifolds. z = top face. No magnet checkerboard."""
    P["coil"].box((cx, cy, z - 0.012), (w, d, 0.024))
    nx, ny = int(w / pitch), int(d / pitch)
    for i in range(nx):
        for j in range(ny):
            x = cx - w / 2 + (i + 0.5) * w / nx
            y = cy - d / 2 + (j + 0.5) * d / ny
            rot90 = ((i // 3) + (j // 3)) % 2 == 1                                # 3 x 3 groups turn 90 deg
            a, b = (pitch * 0.86, pitch * 0.5) if not rot90 else (pitch * 0.5, pitch * 0.86)
            if (i + j) % 2:
                a, b = b, a
            for k, f in enumerate((1.0, 0.72, 0.44)):                             # nested winding loops
                aa, bb, t = a * f, b * f, pitch * 0.045
                key = "alu_dark" if k != 1 else "steel"
                P[key].box((x, y + bb / 2, z + 0.002), (aa, t, 0.004))
                P[key].box((x, y - bb / 2, z + 0.002), (aa, t, 0.004))
                P[key].box((x + aa / 2, y, z + 0.002), (t, bb, 0.004))
                P[key].box((x - aa / 2, y, z + 0.002), (t, bb, 0.004))
    for sy in (-1, 1):                                                          # frame + cooling manifolds
        P["alu_dark"].box((cx, cy + sy * (d / 2 + 0.03), z - 0.01), (w + 0.12, 0.06, 0.05))
        H.cooling_bundle(P, [Vector((cx - w / 2, cy + sy * (d / 2 + 0.075), z - 0.02)),
                             Vector((cx + w / 2, cy + sy * (d / 2 + 0.075), z - 0.02))], k=3, r=0.008, clamp_every=0.4,
                         block=False, up=(0, 0, 1))


def interferometer_head(P, base, aim, h=0.25, s=1.0):
    """Fixed interferometer head on a post (base on the granite), its window looking along aim."""
    base, aim = Vector(base), Vector(aim).normalized()
    top = base + Vector((0, 0, h))
    _cyl(P["alu_dark"], base + Vector((0, 0, h / 2)), (0, 0, 1), 0.025 * s, h, seg=16)
    _cyl(P["steel"], base + Vector((0, 0, 0.01)), (0, 0, 1), 0.06 * s, 0.02, seg=24)
    u, v, n = H._basis(aim)
    P["brushed"].box(top, (0.12 * s, 0.12 * s, 0.09 * s), rot=H._rot(u, n, v))
    _cyl(P["glass"], top + aim * 0.062 * s, aim, 0.024 * s, 0.006, seg=20)
    _ring(P["steel"], top + aim * 0.064 * s, aim, 0.032 * s, 0.024 * s, 0.01, seg=20)
    P["label"].box(top - aim * 0.0 + Vector((0, 0, 0.047 * s)), (0.06 * s, 0.03 * s, 0.002))
    P["cable_k"].path([top - aim * 0.06 * s, top - aim * 0.12 * s - Vector((0, 0, 0.05)), base - aim * 0.2 * s],
                      0.006 * s, seg=6)
