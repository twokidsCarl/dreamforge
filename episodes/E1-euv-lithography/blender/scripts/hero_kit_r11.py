"""Round 11 (P1): non-repeating bay walls + new nameable assemblies (R10 review: "the walls are one repeated
'panel + round flange' tile - nothing can be named"; Carl HARD: structural, part-type count is acceptance).

wall_r11 replaces hero_kit_r10.wall_r10 everywhere. Instead of an equal grid with a service panel + one part per
cell, the wall rectangle is cut by random guillotine splits into blocks of different sizes and aspect ratios; each
block gets ONE assembly chosen by its shape, never the same type twice until every fitting type has been used:

  card_cage       electronics rack: chassis, edge-on cards with ejector handles, fan tray, ribbon cables
  terminal_rack   k2B-style control modules: white DIN modules on a rail, coloured wires into a slotted duct
  valve_island    (R10) solenoid valve island + air tubes
  turbo_gate      turbomolecular pump on an elbow + gate valve with actuator
  pump            horizontal motor (finned) + coupling + pump head + inlet / outlet pipes on a base frame
  viewport_stack  vertical spool with 2-3 CF viewports of different bore + a gauge head
  gas_panel       regulators with dial gauges, quarter-turn valves, bent stainless lines
  manifold        coolant distribution block, flow meters, hose bundle (R10 cooling_bundle)
  drag_chain      energy chain loop on a bracket with its cable bundle
  hexapod_mount   metrology sensor head on a hexapod standing off a machined block

Every block has its own machined base plate (different depth / finish), so the wall reads as stepped relief
(k2B), and bigger blocks put their part further off the wall (closer to the camera). A few harness runs cross
between blocks instead of identical vertical drops.

Also here: brushed / chamfered housing plates (B7_06) and the R11 curved field-facet mirror (B5_01).
"""
import math
import random

from mathutils import Matrix, Vector

import hero_kit_r10 as H

_q, _basis, _rot, _cyl, _ring, _bolt_circle = H._q, H._basis, H._rot, H._cyl, H._ring, H._bolt_circle


def _clear(keep, c, r):
    return all((Vector(c) - Vector(k)).length > kr + r for k, kr in keep)


def _violates(T, keep, front_y=None):
    ks = [(Vector(k), kr * kr) for k, kr in keep]
    if not ks and front_y is None:
        return False
    for mb in T.values():
        for v in mb.bm.verts:
            if front_y is not None and v.co.y < front_y:
                return True
            for kc, kr2 in ks:
                if (v.co - kc).length_squared < kr2:
                    return True
    return False


def _merge(P, T):
    """Append scratch batch T into P (per material key), keeping the smooth flags."""
    for k, src in T.items():
        if not len(src.bm.verts):
            src.bm.free()
            continue
        src._resolve()
        dst = P[k].bm
        src.bm.verts.index_update()
        vm = [dst.verts.new(v.co) for v in src.bm.verts]
        for f in src.bm.faces:
            try:
                nf = dst.faces.new([vm[v.index] for v in f.verts])
                nf.smooth = f.smooth
            except ValueError:
                pass
        src.bm.free()


# ------------------------------------------------------------------ new assemblies (front toward -Y, wall at yf)
def card_cage(P, cx, cz, w, h, yf, s, rnd, depth=1.0):
    d = min(0.34 * s, h * 0.6) * depth
    yc = yf - d / 2
    P["anod"].box((cx, yf - 0.006, cz), (w, 0.012, h))
    for z in (cz - h / 2 + 0.015 * s, cz + h / 2 - 0.015 * s):
        P["alu"].box((cx, yc, z), (w + 0.02 * s, d, 0.03 * s))
    for x in (cx - w / 2, cx + w / 2):
        P["brushed"].box((x, yc, cz), (0.014 * s, d, h))
    hf = h * 0.78
    zc = cz + h * 0.08
    nc = max(5, int(w / (0.05 * s)))
    pitch = (w - 0.04 * s) / nc
    for i in range(nc):
        x = cx - w / 2 + 0.02 * s + pitch * (i + 0.5)
        P["alu_dark"].box((x, yc + 0.01, zc), (0.004, d - 0.05 * s, hf - 0.06 * s))       # card edge
        fy = yf - d + 0.006
        P["alu_dark" if i % 4 else "paint_grey"].box((x, fy, zc), (pitch * 0.9, 0.008, hf - 0.03 * s))
        for sg in (-1, 1):                                                                 # ejector handles
            P["steel"].box((x, fy - 0.014 * s, zc + sg * (hf / 2 - 0.03 * s)), (pitch * 0.55, 0.022 * s, 0.012 * s))
        P["label"].box((x, fy - 0.005, zc + hf * 0.3), (pitch * 0.5, 0.002, 0.03 * s))
        if i % 2 == 0:
            P["steel"].box((x, fy - 0.01, zc - hf * 0.1), (pitch * 0.6, 0.014, 0.035 * s))   # front connector
            P["cable_g"].path([(x, fy - 0.018, zc - hf * 0.1), (x + 0.01, fy - 0.06 * s, zc - hf * 0.35),
                               (x + 0.03, fy - 0.03, cz - h / 2 - 0.02)], 0.004 * s, seg=6)
    # fan tray at the bottom
    zf = cz - h / 2 + h * 0.09
    P["anod"].box((cx, yf - d / 2, zf), (w - 0.02 * s, d, h * 0.12))
    nf = max(2, int(w / (0.16 * s)))
    for i in range(nf):
        x = cx - w / 2 + (i + 0.5) * w / nf
        rr = min(h * 0.05, w / nf * 0.38)
        _ring(P["alu"], (x, yf - d - 0.004, zf), (0, -1, 0), rr, rr * 0.82, 0.008, seg=24)
        for k in range(3):
            P["alu_dark"].box((x, yf - d - 0.006, zf), (rr * 1.7, 0.004, 0.004 * s),
                              rot=(0, math.radians(60 * k), 0))


def terminal_rack(P, cx, cz, w, h, yf, s, rnd, depth=1.0):
    """k2B top: white control modules on a DIN rail, coloured wires looping down into a slotted duct."""
    P["blast"].box((cx, yf - 0.008, cz), (w, 0.016, h))
    zr = cz + h * 0.12
    P["steel"].box((cx, yf - 0.022, zr), (w * 0.94, 0.01, 0.035 * s))
    x = cx - w * 0.45
    k = 0
    while x < cx + w * 0.42:
        mw = rnd.choice((0.045, 0.045, 0.07, 0.1, 0.13)) * s
        mh = rnd.choice((0.16, 0.2, 0.24)) * s * min(1.0, h / (0.5 * s))
        md = rnd.choice((0.09, 0.11, 0.13)) * s * depth
        P["paint" if k % 5 != 3 else "paint_grey"].box((x + mw / 2, yf - 0.03 - md / 2, zr), (mw * 0.94, md, mh))
        P["solenoid"].box((x + mw / 2, yf - 0.03 - md - 0.002, zr + mh * 0.32), (mw * 0.7, 0.004, mh * 0.12))
        P["label"].box((x + mw / 2, yf - 0.03 - md - 0.002, zr - mh * 0.15), (mw * 0.6, 0.003, mh * 0.18))
        nw = max(1, int(mw / (0.022 * s)))
        for j in range(nw):
            wx = x + (j + 0.5) * mw / nw
            key = ("hose_b", "cable_k", "hose_w", "cable_g")[(k + j) % 4]
            P[key].path([(wx, yf - 0.03 - md * 0.6, zr - mh / 2), (wx + 0.005, yf - 0.03 - md * 0.7, zr - mh / 2 - 0.05 * s),
                         (wx + 0.01, yf - 0.05 * s, cz - h * 0.3)], 0.0035 * s, seg=6)
        x += mw
        k += 1
    zd = cz - h * 0.34                                                                  # slotted wire duct
    P["paint_grey"].box((cx, yf - 0.04 * s, zd), (w * 0.94, 0.07 * s, 0.07 * s))
    for i in range(int(w / (0.03 * s))):
        P["anod"].box((cx - w * 0.46 + i * 0.03 * s, yf - 0.076 * s, zd + 0.02 * s), (0.008 * s, 0.004, 0.03 * s))


def turbo_gate(P, cx, cz, w, h, yf, s, rnd, depth=1.0):
    m = min(w, h)
    r = m * 0.24
    off = m * 0.42 * depth
    top = Vector((cx - w * 0.12, yf - off, cz + h * 0.1))
    P["steel"].path([Vector((top.x, yf, top.z + r * 1.1)), Vector((top.x, top.y, top.z + r * 1.1)), top], r * 0.72, seg=24)
    H._turbo(P, top, (0, 0, -1), r)
    if w > m * 1.2 or True:
        gb = Vector((cx + w * 0.25, yf - off * 0.6, cz - h * 0.12))
        P["steel"].path([Vector((gb.x, yf, gb.z)), gb], m * 0.08, seg=20)
        P["blast"].box(gb, (m * 0.42, m * 0.1, m * 0.5))
        for sy in (-1, 1):
            _ring(P["alu"], gb + Vector((0, sy * m * 0.06, 0)), (0, sy, 0), m * 0.14, m * 0.08, m * 0.03)
        _bolt_circle(P, gb + Vector((0, -m * 0.08, 0)), (0, -1, 0), m * 0.11, 8, m * 0.01, m * 0.012)
        _cyl(P["steel"], gb + Vector((0, 0, m * 0.36)), (0, 0, 1), m * 0.05, m * 0.24, seg=20)
        _cyl(P["alu_dark"], gb + Vector((0, 0, m * 0.5)), (0, 0, 1), m * 0.065, m * 0.04, seg=20)
        P["hose_b"].path([gb + Vector((m * 0.05, 0, m * 0.44)), gb + Vector((m * 0.15, -0.01, m * 0.46)),
                          gb + Vector((m * 0.2, 0.0, -m * 0.4))], 0.005 * s, seg=6)


def pump(P, cx, cz, w, h, yf, s, rnd, depth=1.0):
    """Horizontal motor + coupling guard + pump head on a base frame, inlet / outlet pipes back to the wall."""
    m = min(w * 0.55, h)
    r = m * 0.27
    y = yf - r * 1.4 - m * 0.25 * depth
    z = cz - h * 0.1
    x0 = cx - w * 0.36
    L = w * 0.38
    P["anod"].box((cx, y, z - r * 1.15), (w * 0.85, r * 2.4, r * 0.25))                      # base frame
    for sx in (-1, 1):
        P["alu_dark"].box((cx + sx * w * 0.4, (y + yf) / 2, z - r * 1.15), (r * 0.25, yf - y + r, r * 0.25))
    _cyl(P["paint_grey"], (x0 + L / 2, y, z), (1, 0, 0), r, L, seg=32)                        # motor can
    for k in range(int(L / (r * 0.18))):                                                    # cooling fins
        _ring(P["alu_dark"], (x0 + r * 0.1 + k * r * 0.18, y, z), (1, 0, 0), r * 1.1, r * 0.98, r * 0.05, seg=32)
    _cyl(P["anod"], (x0 - r * 0.08, y, z), (1, 0, 0), r * 0.8, r * 0.16, seg=24)               # fan cowl
    P["anod"].box((x0 + L * 0.4, y, z + r * 1.1), (r * 0.9, r * 0.8, r * 0.4))                # terminal box
    P["cable_k"].path([(x0 + L * 0.4, y, z + r * 1.3), (x0 + L * 0.4, y + r, z + r * 1.8), (x0 + L * 0.2, yf - 0.01, cz + h * 0.42)],
                      r * 0.08, seg=8)
    xc = x0 + L
    P["blast"].box((xc + r * 0.35, y, z), (r * 0.7, r * 1.5, r * 1.5))                        # coupling guard
    xh = xc + r * 0.7
    _cyl(P["steel"], (xh + r * 0.6, y, z), (1, 0, 0), r * 0.95, r * 1.2, seg=32)              # pump head
    _bolt_circle(P, Vector((xh + r * 1.22, y, z)), (1, 0, 0), r * 0.8, 8, r * 0.06, r * 0.06, nuts=False)
    for zz, rr in ((z + r * 0.9, r * 0.3), (z - r * 0.2, r * 0.25)):                          # suction / discharge
        a = Vector((xh + r * 0.6, y, zz))
        P["steel"].path([a, a + Vector((0, 0, r * 0.6 if zz > z else 0)), Vector((a.x + r * 0.9, y, a.z + (r * 0.6 if zz > z else 0))),
                         Vector((a.x + r * 0.9, yf - 0.005, a.z + (r * 0.6 if zz > z else 0)))], rr * 0.5, seg=14)
    P["label"].box((x0 + L * 0.6, y - r * 1.0, z + r * 0.2), (r * 0.6, 0.002, r * 0.3))


def viewport_stack(P, cx, cz, w, h, yf, s, rnd, depth=1.0):
    """Vertical CF spool with 2-3 viewports of different bores and a gauge head."""
    m = min(w, h)
    off = m * 0.3 * depth + 0.06 * s
    ys = yf - off
    rs = w * 0.17
    z0, z1 = cz - h * 0.42, cz + h * 0.42
    P["steel"].tube((cx, ys, z0), (cx, ys, z1), rs, seg=32)                                   # spool
    for z in (z0, z1):
        _ring(P["alu"], (cx, ys, z), (0, 0, 1), rs * 1.55, rs * 0.9, rs * 0.3, seg=40)
        _bolt_circle(P, Vector((cx, ys, z + rs * 0.16)), (0, 0, 1), rs * 1.3, 10, rs * 0.07, rs * 0.08, nuts=False)
    P["steel"].tube((cx, yf, (z0 + z1) / 2), (cx, ys, (z0 + z1) / 2), rs * 0.55, seg=20)     # tie to wall
    nv = 3 if h > w * 1.5 else 2
    for i in range(nv):
        z = z0 + (i + 0.7) * (z1 - z0) / (nv + 0.4)
        r = rs * (0.55, 0.8, 0.45)[i % 3]
        H.flange_viewport(P, Vector((cx, ys - rs * 0.9, z)), (0, -1, 0), r, nipple=r * 1.1, side_port=(i == 1))
    g = Vector((cx + rs * 0.9, ys, z1 - h * 0.12))
    P["steel"].tube(g, g + Vector((rs * 0.8, 0, 0)), rs * 0.18, seg=12)
    hd = g + Vector((rs * 1.1, 0, 0))
    P["anod"].box(hd, (rs * 0.7, rs * 0.6, rs * 0.9))
    P["screen"].box(hd + Vector((0, -rs * 0.31, rs * 0.1)), (rs * 0.45, 0.002, rs * 0.25))


def gas_panel(P, cx, cz, w, h, yf, s, rnd, depth=1.0):
    """Gas panel: back plate, 2-3 regulator stations (body + bonnet knob + two dial gauges), quarter-turn valves
    and bent stainless lines between them, a filter can."""
    P["brushed"].box((cx, yf - 0.008, cz), (w, 0.016, h))
    yl = yf - 0.04 * s
    ns = 2 if w < 0.5 * s else 3
    xs = [cx - w * 0.33 + i * (w * 0.66) / max(1, ns - 1) for i in range(ns)]
    zr = cz + h * 0.12
    rr = min(w / ns * 0.16, h * 0.08)
    for i, x in enumerate(xs):
        b = Vector((x, yl - rr, zr))
        P["steel"].box(b, (rr * 1.8, rr * 1.8, rr * 1.8))                                   # regulator body
        _cyl(P["steel"], b + Vector((0, 0, rr * 1.4)), (0, 0, 1), rr * 0.75, rr * 1.0, seg=20)   # bonnet
        _cyl(P["solenoid"], b + Vector((0, 0, rr * 2.1)), (0, 0, 1), rr * 0.9, rr * 0.35, seg=20)  # knob
        for sx in (-1, 1):                                                                  # dial gauges
            gc = b + Vector((sx * rr * 1.7, -rr * 0.5, rr * 0.2))
            P["steel"].tube(b + Vector((sx * rr * 0.9, 0, 0)), gc, rr * 0.15, seg=8)
            _cyl(P["alu"], gc, (0, -1, 0), rr * 0.8, rr * 0.4, seg=28)
            _cyl(P["label"], gc + Vector((0, -rr * 0.21, 0)), (0, -1, 0), rr * 0.68, 0.002, seg=28)
            P["solenoid"].box(gc + Vector((rr * 0.15, -rr * 0.215, rr * 0.15)), (rr * 0.5, 0.002, rr * 0.05),
                              rot=(0, math.radians(-40 + 70 * sx), 0))
        vz = cz - h * 0.18                                                                  # quarter-turn valve
        P["steel"].box((x, yl - rr, vz), (rr * 1.2, rr * 1.2, rr * 1.2))
        P["hose_b"].box((x + rr * 0.6, yl - rr * 2.1, vz), (rr * 1.6, rr * 0.3, rr * 0.4))    # blue lever
        P["steel"].path([Vector((x, yl - rr, zr - rr * 0.9)), Vector((x, yl - rr, vz + rr * 0.6))], rr * 0.18, seg=10)
        P["steel"].path([Vector((x, yl - rr, vz - rr * 0.6)), Vector((x, yl - rr, cz - h * 0.38)),
                         Vector((x + w * 0.12, yl - rr, cz - h * 0.44)), Vector((cx + w * 0.45, yl - rr, cz - h * 0.44))],
                        rr * 0.18, seg=10)
    _cyl(P["blast"], (cx + w * 0.42, yl - rr, cz + h * 0.25), (0, 0, 1), rr * 0.9, rr * 3.0, seg=20)   # filter can
    P["label"].box((cx - w * 0.3, yf - 0.018, cz + h * 0.42), (w * 0.3, 0.002, 0.03 * s))


def manifold(P, cx, cz, w, h, yf, s, rnd, depth=1.0):
    m = min(w, h)
    a = Vector((cx - w * 0.3, yf - 0.04 * s, cz + h * 0.38))
    H.cooling_bundle(P, [a, a + Vector((0, -0.04 * depth, -h * 0.5)), a + Vector((w * 0.55, -0.1 * depth, -h * 0.72))],
                     k=6 if w > 0.5 * s else 4, r=0.012 * s, clamp_every=0.2 * s, block=True, up=(0, -1, 0))
    fb = Vector((cx + w * 0.22, yf - 0.07 * s * depth, cz + h * 0.08))
    P["blast"].box(fb, (w * 0.34, 0.12 * s * depth, h * 0.55))                                # flow-meter block
    for j in range(3):
        z = fb.z + h * (0.18 - j * 0.17)
        _cyl(P["glass"], (fb.x, fb.y - 0.061 * s * depth, z), (0, -1, 0), m * 0.06, 0.006, seg=20)
        _ring(P["steel"], (fb.x, fb.y - 0.062 * s * depth, z), (0, -1, 0), m * 0.075, m * 0.06, 0.01, seg=20)


def drag_chain(P, cx, cz, w, h, yf, s, rnd, depth=1.0):
    """Energy chain loop on a bracket with the cable bundle running into it."""
    R = min(h * 0.28, 0.14 * s)
    L = w * 0.7
    a = Vector((cx - w * 0.4, yf - 0.08 * s, cz - R))
    link = 0.035 * s
    ww = 0.09 * s
    pts = []
    for i in range(int(L / link)):
        pts.append((a + Vector((i * link, 0, 0)), 0.0))
    c = a + Vector((int(L / link) * link, 0, R))
    nb = max(6, int(math.pi * R / link))
    for i in range(nb + 1):
        th = -math.pi / 2 + math.pi * i / nb
        pts.append((c + Vector((R * math.cos(th), 0, R * math.sin(th))), th + math.pi / 2))
    for i in range(int(L * 0.65 / link)):
        pts.append((a + Vector(((int(L / link) - i) * link, 0, 2 * R)), math.pi))
    for p, ang in pts:
        P["chain"].box(p, (link * 0.86, ww, 0.03 * s), rot=(0, -ang, 0))
        for sy in (-1, 1):
            P["alu_dark"].box(p + Vector((0, sy * (ww / 2 + 0.003), 0)), (link * 0.92, 0.005, 0.036 * s), rot=(0, -ang, 0))
    P["alu"].box(a - Vector((0.04 * s, 0, 0)), (0.06 * s, ww + 0.03, 0.08 * s))
    P["anod"].box((cx, yf - 0.03 * s, cz - R - 0.05 * s), (w * 0.9, 0.05 * s, 0.02 * s))     # support rail
    H.cable_harness(P, [a - Vector((0.04 * s, 0, 0)), a - Vector((0.1 * s, -0.03, -h * 0.3)),
                        Vector((cx - w * 0.45, yf - 0.01, cz + h * 0.42))], n=5, r=0.006 * s, connector=False)


def hexapod_mount(P, cx, cz, w, h, yf, s, rnd, depth=1.0):
    m = min(w, h) * 1.15
    base = Vector((cx, yf - 0.04 * s, cz - m * 0.05))
    P["blast"].box(base + Vector((0, 0.02 * s, 0)), (m * 0.7, 0.04 * s, m * 0.7))
    topc = base + Vector((0, -m * 0.42 * depth, 0))
    H.hexapod(P, base, topc, m * 0.3, m * 0.22, plate_key="alu", leg_key="anod")
    P["brushed"].box(topc + Vector((0, -m * 0.07, 0)), (m * 0.42, m * 0.12, m * 0.32))
    _cyl(P["glass"], topc + Vector((0, -m * 0.135, m * 0.04)), (0, -1, 0), m * 0.07, 0.012, seg=24)
    _ring(P["steel"], topc + Vector((0, -m * 0.138, m * 0.04)), (0, -1, 0), m * 0.09, m * 0.07, 0.012, seg=24)
    H.cable_harness(P, [topc + Vector((m * 0.2, -m * 0.06, 0)), topc + Vector((m * 0.35, 0.0, -m * 0.25)),
                        Vector((cx + w * 0.42, yf - 0.01, cz - h * 0.4))], n=3, r=0.005 * s, connector=False)


def valve_island(P, cx, cz, w, h, yf, s, rnd, depth=1.0):
    m = min(w, h * 1.4)
    H.valve_island(P, (cx, yf, cz + h * 0.12), (0, -1, 0), nval=max(4, min(12, int(w / (0.06 * s)))),
                   s=min(1.8, m / 0.32), drop=h * 0.4)


KINDS = {
    # name: (builder, aspect class)  wide = w/h > 1.4, tall = < 0.7, any = square-ish
    "card_cage": (card_cage, "wide"),
    "terminal_rack": (terminal_rack, "wide"),
    "valve_island": (valve_island, "wide"),
    "drag_chain": (drag_chain, "wide"),
    "pump": (pump, "wide"),
    "viewport_stack": (viewport_stack, "tall"),
    "gas_panel": (gas_panel, "any"),
    "turbo_gate": (turbo_gate, "any"),
    "manifold": (manifold, "any"),
    "hexapod_mount": (hexapod_mount, "any"),
}
FIT = {"wide": ("card_cage", "terminal_rack", "valve_island", "pump", "drag_chain", "gas_panel", "manifold"),
       "tall": ("viewport_stack", "manifold", "gas_panel", "hexapod_mount"),
       "any": ("turbo_gate", "gas_panel", "hexapod_mount", "manifold", "card_cage", "viewport_stack", "pump")}


def _split(rect, rnd, amin, smin, depth=0):
    """Guillotine split into blocks of varied size (stop randomly once a block is small enough)."""
    x0, z0, x1, z1 = rect
    w, h = x1 - x0, z1 - z0
    if (w * h < amin * rnd.uniform(1.0, 2.6) and depth > 0) or (w < 2 * smin and h < 2 * smin):
        return [rect]
    if w / h > 1.25 and w >= 2 * smin:
        vert = True
    elif h / w > 1.25 and h >= 2 * smin:
        vert = False
    else:
        vert = (w >= 2 * smin) and (rnd.random() < 0.5 or h < 2 * smin)
    t = rnd.uniform(0.3, 0.7)
    if vert:
        xm = x0 + max(smin, min(w - smin, w * t))
        return _split((x0, z0, xm, z1), rnd, amin, smin, depth + 1) + _split((xm, z0, x1, z1), rnd, amin, smin, depth + 1)
    zm = z0 + max(smin, min(h - smin, h * t))
    return _split((x0, z0, x1, zm), rnd, amin, smin, depth + 1) + _split((x0, zm, x1, z1), rnd, amin, smin, depth + 1)


def wall_r11(P, x0, x1, z0, z1, y0, seed=0, keep=(), scale=1.0, depth=1.0, blocks=None, log=None, tone="mixed",
             front_y=None, use=None, fallback=("terminal_rack", "gas_panel"), kinds_tab=None, fit_tab=None, **_ignored):
    """front_y: no vertex may come forward of this plane (keeps the line of sight to optics in front free)."""
    """Non-repeating bay wall on the plate whose front face is y = y0 (parts toward -Y).
    blocks ~ target number of blocks (default from the wall area); log (list) receives the kinds used."""
    rnd = random.Random(seed * 31 + 7)
    s = scale
    w, h = x1 - x0, z1 - z0
    nb = blocks or max(3, min(11, int(w * h / (0.55 * s) ** 2 * 0.55) + 2))
    amin = w * h / nb
    smin = min(0.3 * s, w / 2.2, h / 2.2)
    rects = _split((x0, z0, x1, z1), rnd, amin, smin)
    KT = kinds_tab or KINDS                      # R12: hero_kit_r12 passes its own (bigger) tables + a shared counter
    FT = fit_tab or FIT
    if use is None:
        use = {}
    for k in KT:
        use.setdefault(k, 0)
    yb = y0
    P["solenoid" if tone == "dark" else "paint_grey"].box(((x0 + x1) / 2, yb - 0.004, (z0 + z1) / 2), (w, 0.008, h))
    # dark tone uses non-metal greys: metallic 'anod' turns white in a white studio (B7_06 smoke)
    fins = (("paint_grey", "solenoid", "paint_grey", "coil", "paint_grey", "solenoid") if tone == "dark" else
            ("blast", "anod", "brushed", "paint", "paint_grey", "anod"))
    kinds = []
    rects.sort(key=lambda r: -(r[2] - r[0]) * (r[3] - r[1]))                               # big blocks pick first
    for i, (bx0, bz0, bx1, bz1) in enumerate(rects):
        bw, bh = bx1 - bx0, bz1 - bz0
        cx, cz = (bx0 + bx1) / 2, (bz0 + bz1) / 2
        g = 0.025 * s                                                                        # gap between blocks
        bw2, bh2 = bw - g, bh - g
        asp = bw2 / bh2
        cls = "wide" if asp > 1.4 else "tall" if asp < 0.7 else "any"
        cand = list(dict.fromkeys(FT[cls] + (FT["any"] if cls != "tall" else ())))
        rnd.shuffle(cand)
        kind = min(cand, key=lambda k: (use[k], k not in FT[cls]))
        use[kind] += 1
        kinds.append(kind)
        # own machined base plate: finish + standoff differ per block (stepped relief)
        bd = rnd.choice((0.02, 0.035, 0.05, 0.07)) * s
        fin = fins[(i + seed) % 6]
        P[fin].box((cx, yb - bd / 2, cz), (bw2, bd, bh2))
        for sx in (-1, 1):
            for sz in (-1, 1):
                _cyl(P["steel"], (cx + sx * (bw2 / 2 - 0.02 * s), yb - bd - 0.003, cz + sz * (bh2 / 2 - 0.02 * s)),
                     (0, -1, 0), 0.007 * s, 0.006, seg=6)
        yf = yb - bd
        size = math.sqrt(bw2 * bh2)
        dep = depth * (0.7 + 0.9 * min(1.0, size / (1.2 * s)))                               # bigger = further out
        # R11: keep-clear spheres no longer delete the block (R10 culled most of the B7_06 wall that way); the
        # part's standoff is shrunk so its front stays behind any sphere in front of it; only a block with no
        # room at all is left as a plain machined plate
        reach = 0.45 * min(bw2, bh2)                                  # ~ how far a part stands off at dep = 1
        room = 9.0
        for kc, kr in keep:
            kc = Vector(kc)
            dx = max(0.0, abs(kc.x - cx) - bw2 / 2)
            dz = max(0.0, abs(kc.z - cz) - bh2 / 2)
            d2 = math.hypot(dx, dz)
            if d2 < kr:
                room = min(room, yf - (kc.y + math.sqrt(kr * kr - d2 * d2)))
        dep = max(0.25, min(dep, room / max(reach, 1e-3)))          # the exact test below has the last word
        # exact test: build into a scratch batch, reject if any vertex enters a keep-clear sphere, retry flatter
        st = rnd.getstate()
        tries = [(kind, f) for f in (1.0, 0.55, 0.3, 0.15)] + [(k_, 0.4) for k_ in sorted(fallback, key=lambda k: use.get(k, 0)) if k_ != kind]
        for kd, f in tries:                         # last resort: a shallow panel-type assembly in the same block
            rnd.setstate(st)
            T = H.new_parts()
            KT[kd][0](T, cx, cz, bw2 * 0.94, bh2 * 0.94, yf, s, rnd, dep * f)
            if not _violates(T, keep, front_y):
                _merge(P, T)
                if kd != kind:
                    kinds[-1] = kd
                    use[kind] -= 1
                    use[kd] = use.get(kd, 0) + 1
                break
            for mb in T.values():
                mb.bm.free()
        else:
            kinds[-1] = kind + "(dropped)"
    # a few harness runs crossing block boundaries (no identical vertical drops)
    for k in range(max(1, int(w / (1.6 * s)))):
        xa = x0 + rnd.uniform(0.1, 0.9) * w
        xb = min(x1 - 0.05, max(x0 + 0.05, xa + rnd.uniform(-0.8, 0.8) * s))
        za, zb = z1 - 0.06 * s, z0 + rnd.uniform(0.2, 0.6) * h
        pts = [(xa, yb - 0.09 * s, za), (xa + (xb - xa) * 0.3, yb - 0.1 * s, za - h * 0.25), (xb, yb - 0.08 * s, zb)]
        if all(_clear(keep, p, 0.05) for p in pts):
            H.cable_harness(P, pts, n=rnd.choice((4, 6, 8)), r=0.006 * s, tie_every=0.12 * s, connector=False)
    if log is not None:
        log.extend(kinds)
    return kinds


# ------------------------------------------------------------------ B7_06 housing plates
def housing_plate(P, c, size, n, key="brushed", chamfer_key="alu", bolts=True, s=1.0):
    """Thick brushed plate (size = (w, t, h) in the plate's frame with t along n) with a chamfer frame strip
    around its face, counter-sunk screws along the edges and a panel seam - not a flat sheet."""
    c, n = Vector(c), Vector(n).normalized()
    u, v, _ = _basis(n)
    w, t, h = size
    R = Matrix((u, n, v)).transposed().to_euler()            # local x = u, y = n, z = v
    P[key].box(c, (w, t, h), rot=R)
    f = c + n * (t / 2 + 0.004)
    ch = 0.03 * s
    for sv in (-1, 1):                                       # chamfer frame strips (top / bottom / sides)
        P[chamfer_key].box(f + v * sv * (h / 2 - ch / 2), (w, 0.008, ch), rot=R)
        P[chamfer_key].box(f + u * sv * (w / 2 - ch / 2), (ch, 0.008, h - 2 * ch), rot=R)
    if bolts:
        nbw, nbh = max(2, int(w / (0.14 * s))), max(2, int(h / (0.14 * s)))
        for i in range(nbw + 1):
            for sv in (-1, 1):
                p = f + n * 0.004 + u * (-w / 2 + ch * 0.5 + (w - ch) * i / nbw) + v * sv * (h / 2 - ch / 2)
                _cyl(P["steel"], p, n, 0.007 * s, 0.004, seg=8)
        for k in range(1, nbh):
            for su in (-1, 1):
                p = f + n * 0.004 + u * su * (w / 2 - ch / 2) + v * (-h / 2 + h * k / nbh)
                _cyl(P["steel"], p, n, 0.007 * s, 0.004, seg=8)


# ------------------------------------------------------------------ B5_01 field facet mirror (R11)
def _curved_facet(mb, c, u, v, n, L, wd, Ra, Rc, thick, seg=14):
    """One long banana facet: centre line an arc of radius Ra (bulging +v) of chord L, width wd, with a concave
    front (sag across the width from radius Rc) - a true curved mirror strip, front toward +n."""
    V = mb.bm.verts.new
    span = 2 * math.asin(min(0.99, L / (2 * Ra)))
    cols = 5
    front, back = [], []
    for i in range(seg + 1):
        t = -span / 2 + span * i / seg
        pc = c + u * (Ra * math.sin(t)) + v * (Ra * math.cos(t) - Ra)
        rad = (u * math.sin(t) + v * math.cos(t)).normalized()
        rowf, rowb = [], []
        for j in range(cols):
            a = (j / (cols - 1) - 0.5) * wd
            sag = (a * a) / (2 * Rc) + ((Ra * math.sin(t)) ** 2) / (2 * Rc * 3)
            p = pc + rad * a
            rowf.append(V(p + n * (thick / 2 - sag)))
            rowb.append(V(p - n * thick / 2))
        front.append(rowf)
        back.append(rowb)
    F = mb.bm.faces.new
    for i in range(seg):
        for j in range(cols - 1):
            F((front[i][j], front[i + 1][j], front[i + 1][j + 1], front[i][j + 1]))
            F((back[i][j + 1], back[i + 1][j + 1], back[i + 1][j], back[i][j]))
    for i in range(seg):
        F((front[i][0], back[i][0], back[i + 1][0], front[i + 1][0]))
        F((front[i + 1][-1], back[i + 1][-1], back[i][-1], front[i][-1]))
    F([front[0][j] for j in range(cols)][::-1] + [back[0][j] for j in range(cols)])
    F([front[-1][j] for j in range(cols)] + [back[-1][j] for j in range(cols)][::-1])


def field_facet_mirror_r11(P, c, n, width=1.0, height=0.72, cols=4, rows=9, seed=0, spot_mb=None):
    """Field-facet mirror that reads as a curved MIRROR ARRAY (R10: "white tiles"): a dark machined carrier
    (thick, chamfered, bolt rows) with columns of long curved polished facets, each on its own steel pedestal
    with a visible gap and an individual tilt, so the environment / beam reflect differently in every strip.
    Facets use the 'facet' material (polished metal, low roughness), not the pale substrate."""
    rnd = random.Random(seed)
    c, n = Vector(c), Vector(n).normalized()
    u, v, _ = _basis(n)
    R = Matrix((u, v, n)).transposed().to_euler()
    th = 0.07
    P["anod"].box(c - n * th / 2, (width * 1.12, height * 1.16, th), rot=R)               # carrier
    for sv in (-1, 1):
        P["alu"].box(c - n * th / 2 + v * sv * height * 0.58, (width * 1.14, 0.02, th * 1.1), rot=R)
        P["alu"].box(c - n * th / 2 + u * sv * width * 0.56, (0.02, height * 1.18, th * 1.1), rot=R)
    for i in range(14):
        for sv in (-1, 1):
            p = c + u * (-width * 0.55 + width * 1.1 * i / 13) + v * sv * height * 0.57
            _cyl(P["steel"], p + n * 0.002, n, 0.007, 0.008, seg=8)
    cw = width / cols
    rh = height / rows
    for ci in range(cols):
        xc = -width / 2 + cw * (ci + 0.5)
        P["alu_dark"].box(c + u * xc + n * 0.006, (cw * 0.12, height * 1.02, 0.012), rot=R)  # column rib
        for ri in range(rows):
            zc = -height / 2 + rh * (ri + 0.5)
            tilt_u = rnd.uniform(-0.09, 0.09)
            tilt_v = rnd.uniform(-0.06, 0.06)
            nf = (n + u * tilt_u + v * tilt_v).normalized()
            uf = (u - nf * u.dot(nf)).normalized()
            vf = nf.cross(uf)
            pc = c + u * xc + v * zc + n * 0.03
            P["steel"].box(pc - n * 0.012, (cw * 0.3, rh * 0.35, 0.018), rot=R)            # pedestal
            _curved_facet(P["facet"], pc, uf, vf, nf, cw * 0.86, rh * 0.62, cw * 1.6, cw * 3.0, 0.012)
            if spot_mb is not None and abs(xc) < width * 0.42 and abs(zc) < height * 0.42:
                spot_mb.box(pc + nf * 0.008, (cw * 0.5, rh * 0.3, 0.001),
                            rot=Matrix((uf, vf, nf)).transposed().to_euler())
    # hexapod behind the carrier
    H.hexapod(P, c - n * (th + 0.32), c - n * (th + 0.01), width * 0.32, width * 0.28, plate_key="alu", leg_key="anod")
    for sgn in (-1, 1):
        a = c - n * th * 0.6 + u * sgn * width * 0.57
        P["hose_b" if sgn < 0 else "hose_w"].path([a, a + u * sgn * 0.08, a + u * sgn * 0.1 - n * 0.4 - v * 0.3], 0.012, seg=10)
