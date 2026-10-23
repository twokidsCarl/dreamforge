"""Round 8 (P1): a real parts kit for every cutaway bay, replacing the R2-R7 procedural box / greeble filler.

R7 review (global gap #1): "the bays are filled with procedural coloured boxes and cable; not one part can be
named". Each function here builds one nameable vacuum / mechatronic part out of batched geometry:

  turbo_pump     turbomolecular pump: CF inlet flange + bolt circle, ribbed body, motor can, vent port, cable
  gate_valve     inline gate valve between two CF flanges, pneumatic actuator, air lines, position flag
  bellows        edge-welded bellows section between two flanges
  gauge          vacuum gauge head on a short CF nipple, lit display window
  viewport       CF viewport: flange, bolt circle, glass, clamp ring
  card_cage      19-inch card cage: chassis rails, PCB cards with front panels, handles, LEDs, ribbon cables
  drag_chain     energy chain (U-loop of hinged links) with the cables / hoses it carries
  manifold       coolant manifold: header pipe, quarter-turn valves with blue handles, quick couplings
  hexapod_mirror solid mirror on a six-strut hexapod (kit_r2.mirror_with_mount)
  cable_tray     ladder tray with looms
  linear_axis    rail pair, carriage, linear-encoder scale with ticks, read head

Parts are built in world coordinates. Wall parts sit on a back plate whose front face is the plane y = y0 and
stick out toward -Y (the camera side). populate_wall() lays 8-12 large parts out on a wall in bands (cable tray +
card cages on top, pumps / valves / gauges in the middle, manifold + drag chain at the bottom), skipping any part
whose footprint touches a keep-clear sphere (optics and beam).
"""
import math
import random

from mathutils import Matrix, Vector

import kit_r2 as K

KEYS = ("alu", "blast", "alu_dark", "steel", "anod", "paint_grey", "copper", "cable_b", "cable_o", "cable_g",
        "led_c", "led_o", "glass", "rubber", "pcb", "chip", "chain", "handle", "screen", "warn")


def new_parts():
    return {k: K.MB() for k in KEYS}


def materials(M):
    """Material per part key (adds the few the shared palette lacks)."""
    if "pcb" not in M:
        M["pcb"] = K.mat("PCBMask", (0.06, 0.2, 0.14), rough=0.35, coat=0.3)
        M["chip"] = K.mat("ChipBlack", (0.03, 0.03, 0.035), rough=0.3)
        M["chain"] = K.mat("DragChain", (0.05, 0.05, 0.055), rough=0.45)
        M["handle"] = K.mat("ValveBlue", (0.08, 0.25, 0.7), rough=0.35, coat=0.3)
        M["screen"] = K.emit_mat("GaugeLCD", (0.35, 0.95, 0.8), 3.5)
        M["warn"] = K.mat("WarnYellow", (0.95, 0.72, 0.08), rough=0.45)
        M.setdefault("blast", K.mat("Blasted", (0.55, 0.56, 0.6), metal=1.0, rough=0.55, speck=0.25))
        M.setdefault("led_o", K.emit_mat("LEDAmber", (1.0, 0.6, 0.2), 5.0))
        M.setdefault("rubber", K.mat("Rubber", (0.04, 0.04, 0.045), rough=0.7))
        M.setdefault("glass", K.mat("ViewGlass", (0.9, 0.95, 1.0), rough=0.02, transmission=1.0, ior=1.5))
    return {k: M[k] for k in KEYS}


def finish(P, M, tag, parent=None):
    mats = materials(M)
    bev = {"anod": 0.004, "paint_grey": 0.004, "alu_dark": 0.003, "blast": 0.004}
    out = []
    for k, mb in P.items():
        if len(mb.bm.verts):
            ob = mb.obj(f"{tag}_{k}", mats[k], bevel=bev.get(k, 0.0))
            if parent is not None:
                ob.parent = parent
            out.append(ob)
        else:
            mb.bm.free()
    return out


# ------------------------------------------------------------------ helpers
def _q(n):
    return Vector((0, 0, 1)).rotation_difference(Vector(n).normalized())


def _cyl(mb, c, n, r, h, seg=24, r2=None):
    mb.cyl_m(Matrix.Translation(Vector(c)) @ _q(n).to_matrix().to_4x4(), r, h, seg=seg, r2=r2)


def _ring(mb, c, n, ro, ri, h, seg=40):
    mb.ring(Vector(c), ro, ri, h, rot=_q(n).to_euler(), seg=seg)


def _bolts(mb, c, n, R, k, r, h):
    mb.bolts(Vector(c), R, k, r, h, rot=_q(n).to_euler())


def cf_flange(P, c, n, r, key="alu"):
    """ConFlat flange pair seen face-on: two rings, a bolt circle with nuts."""
    n = Vector(n).normalized()
    _ring(P[key], c, n, r * 1.55, r * 0.95, r * 0.28)
    _bolts(P["steel"], Vector(c) + n * r * 0.16, n, r * 1.3, 8 if r < 0.06 else 12, r * 0.07, r * 0.12)


# ------------------------------------------------------------------ parts
def turbo_pump(P, c, n=(0, -1, 0), r=0.09, cable_to=None):
    """Turbomolecular pump, inlet flange at c, body along n (away from the port it pumps)."""
    c, n = Vector(c), Vector(n).normalized()
    cf_flange(P, c, n, r * 1.05)
    body0 = c + n * r * 0.18
    _cyl(P["alu"], body0 + n * r * 0.65, n, r, r * 1.3, seg=40)
    for k in range(5):                                          # stator-stack ribs
        _ring(P["alu_dark"], body0 + n * (r * 0.2 + k * r * 0.24), n, r * 1.07, r * 0.98, r * 0.06, seg=40)
    _cyl(P["anod"], body0 + n * r * 1.55, n, r * 0.82, r * 0.5, seg=32)        # motor / drive can
    _cyl(P["anod"], body0 + n * r * 1.86, n, r * 0.55, r * 0.14, seg=24)
    side = n.cross(Vector((0, 0, 1)))
    if side.length < 1e-3:
        side = Vector((1, 0, 0))
    side.normalize()
    vp = body0 + n * r * 1.1 + side * r
    P["steel"].tube(vp, vp + side * r * 0.45, r * 0.16, seg=12)                 # vent / fore-line port
    _ring(P["alu"], vp + side * r * 0.45, side, r * 0.3, r * 0.14, r * 0.08, seg=20)
    up = n.cross(side).normalized()
    P["led_c"].box(body0 + n * r * 1.55 + up * r * 0.83, (r * 0.12, r * 0.12, r * 0.12))
    P["warn"].box(body0 + n * r * 0.75 - up * r * 1.0, (r * 0.35, r * 0.35, r * 0.02), rot=_q(up).to_euler())
    if cable_to is not None:
        a = body0 + n * r * 1.9
        P["cable_g"].path([a, a + n * r * 0.6, Vector(cable_to)], r * 0.07, seg=8)


def gate_valve(P, c, axis=(1, 0, 0), r=0.08, up=(0, 0, 1)):
    """Inline gate valve: flat body between two CF flanges on a pipe along axis, pneumatic actuator up."""
    c, ax, up = Vector(c), Vector(axis).normalized(), Vector(up).normalized()
    t = ax.cross(up).normalized()
    rot = Matrix((ax, t, up)).transposed().to_euler()
    P["blast"].box(c + up * r * 0.5, (r * 0.9, r * 2.6, r * 4.2), rot=rot)          # body (thin along the pipe)
    for s in (-1, 1):
        cf_flange(P, c + ax * s * r * 0.55, ax * s, r)
        P["steel"].tube(c + ax * s * r * 0.7, c + ax * s * r * 2.2, r * 0.75, seg=24)
        _ring(P["alu"], c + ax * s * r * 2.2, ax, r * 1.4, r * 0.7, r * 0.22)
    top = c + up * (r * 2.6)
    _cyl(P["steel"], top + up * r * 0.9, up, r * 0.5, r * 1.8, seg=24)                # actuator cylinder
    _cyl(P["alu_dark"], top + up * r * 1.9, up, r * 0.6, r * 0.2, seg=24)
    for s in (-1, 1):                                                                # air fittings + lines
        f = top + up * r * (0.5 + 0.9 * (s + 1) / 2) + t * r * 0.55
        P["steel"].box(f, (r * 0.18, r * 0.18, r * 0.18), rot=rot)
        P["cable_b" if s < 0 else "cable_o"].path([f, f + t * r * 0.6, f + t * r * 0.8 - up * r * 3.5], r * 0.06, seg=6)
    P["warn"].box(top + up * r * 2.15, (r * 0.35, r * 0.35, r * 0.25), rot=rot)          # position flag


def bellows(P, a, b, r, k=None):
    a, b = Vector(a), Vector(b)
    n = (b - a).normalized()
    L = (b - a).length
    k = k or max(6, int(L / (r * 0.18)))
    for i in range(k + 1):
        _ring(P["steel"], a.lerp(b, i / k), n, r * (1.12 if i % 2 else 1.0), r * 0.82, L / k * 0.55, seg=32)
    cf_flange(P, a, -n, r * 0.9)
    cf_flange(P, b, n, r * 0.9)


def gauge(P, c, n=(0, -1, 0), r=0.035):
    c, n = Vector(c), Vector(n).normalized()
    cf_flange(P, c, n, r)
    P["steel"].tube(c, c + n * r * 2.5, r * 0.6, seg=16)
    head = c + n * r * 3.4
    P["anod"].box(head, (r * 2.4, r * 1.8, r * 2.4))
    P["screen"].box(head + n * r * 0.92 + Vector((0, 0, r * 0.4)), (r * 1.5, r * 0.05, r * 0.6))
    P["led_o"].box(head + n * r * 0.92 + Vector((r * 0.7, 0, -r * 0.6)), (r * 0.2, r * 0.05, r * 0.2))
    P["cable_g"].path([head + Vector((0, 0, -r * 1.2)), head + Vector((0, 0, -r * 3)) + n * r,
                       head + Vector((r * 2, 0, -r * 6))], r * 0.12, seg=6)


def viewport(P, c, n=(0, -1, 0), r=0.06):
    c, n = Vector(c), Vector(n).normalized()
    cf_flange(P, c, n, r)
    _cyl(P["glass"], c + n * r * 0.2, n, r * 0.85, r * 0.06, seg=32)
    _ring(P["steel"], c + n * r * 0.3, n, r * 1.0, r * 0.8, r * 0.12, seg=32)


def card_cage(P, x0, x1, z0, z1, y0, ncard=None, seed=0):
    """Rack chassis on the wall: top / bottom rails, PCB cards edge-on with front panels toward -Y."""
    rnd = random.Random(seed)
    w, h = x1 - x0, z1 - z0
    d = min(0.3, h * 0.9)
    cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
    yc = y0 - d / 2
    P["anod"].box((cx, y0 - 0.01, cz), (w, 0.02, h))                                   # backplane
    for z in (z0 + 0.012, z1 - 0.012):
        P["alu"].box((cx, yc, z), (w + 0.02, d, 0.024))                                 # rails
    for x in (x0, x1):
        P["alu_dark"].box((x, yc, cz), (0.012, d, h))                                   # side plates
    ncard = ncard or max(4, int(w / 0.045))
    pitch = (w - 0.03) / ncard
    for i in range(ncard):
        x = x0 + 0.015 + pitch * (i + 0.5)
        P["pcb"].box((x, yc + 0.01, cz), (0.004, d - 0.04, h - 0.06))
        for _ in range(3):                                                            # chips on the card
            P["chip"].box((x + 0.006, yc + rnd.uniform(-d * 0.3, d * 0.3), cz + rnd.uniform(-h * 0.3, h * 0.3)),
                          (0.006, rnd.uniform(0.02, 0.05), rnd.uniform(0.02, 0.04)))
        fy = y0 - d + 0.006
        P["alu_dark"].box((x, fy, cz), (pitch * 0.92, 0.008, h - 0.03))                 # front panel
        for s in (-1, 1):
            P["handle"].box((x, fy - 0.012, cz + s * (h / 2 - 0.035)), (pitch * 0.5, 0.02, 0.012))
        P["led_c" if i % 3 else "led_o"].box((x, fy - 0.005, cz + h * 0.25), (0.006, 0.004, 0.006))
        P["led_c"].box((x, fy - 0.005, cz + h * 0.25 - 0.015), (0.006, 0.004, 0.006))
        if i % 2 == 0:                                                                 # connector + ribbon
            P["steel"].box((x, fy - 0.01, cz - h * 0.05), (pitch * 0.6, 0.012, 0.03))
            P["cable_g"].path([(x, fy - 0.016, cz - h * 0.05), (x, fy - 0.05, cz - h * 0.3),
                               (x + 0.02, fy - 0.04, z0 - 0.06)], 0.004, seg=6)


def drag_chain(P, a, length, R=0.06, w=0.05, axis=(1, 0, 0), up=(0, 0, 1)):
    """Energy chain lying along axis from a: lower run, 180-degree bend (radius R), upper return run."""
    a, ax, up = Vector(a), Vector(axis).normalized(), Vector(up).normalized()
    t = ax.cross(up).normalized()
    rot0 = Matrix((ax, t, up)).transposed()
    link = 0.03
    pts = []
    nlow = int(length / link)
    for i in range(nlow):
        pts.append((a + ax * (i * link), ax))
    c = a + ax * (nlow * link) + up * R
    nb = max(6, int(math.pi * R / link))
    for i in range(nb + 1):
        th = -math.pi / 2 + math.pi * i / nb
        p = c + ax * (R * math.cos(th)) + up * (R * math.sin(th))
        tang = (-ax * math.sin(th) + up * math.cos(th)).normalized()
        pts.append((p, tang))
    for i in range(int(length * 0.6 / link)):
        pts.append((a + ax * ((nlow - i) * link) + up * 2 * R, -ax))
    for p, d in pts:
        q = ax.rotation_difference(d)
        rot = (q.to_matrix() @ rot0).to_euler()
        P["chain"].box(p, (link * 0.85, w, 0.028), rot=rot)
        for s in (-1, 1):
            P["alu_dark"].box(p + t * s * (w / 2 + 0.003), (link * 0.9, 0.004, 0.032), rot=rot)
    P["alu"].box(a - ax * 0.03, (0.05, w + 0.03, 0.05))                                 # fixed end bracket


def manifold(P, x0, x1, z, y0, n=None):
    """Coolant manifold: header + return pipes, branch valves with blue quarter-turn handles, couplings."""
    yh = y0 - 0.05
    P["copper"].tube((x0, yh, z), (x1, yh, z), 0.018, seg=14)
    P["steel"].tube((x0, yh - 0.05, z - 0.07), (x1, yh - 0.05, z - 0.07), 0.014, seg=14)
    for x in (x0, x1):
        P["steel"].cyl((x, yh, z), 0.024, 0.03, rot=(0, math.radians(90), 0), seg=14)
    n = n or max(2, int((x1 - x0) / 0.22))
    for i in range(n):
        x = x0 + (i + 0.5) * (x1 - x0) / n
        P["steel"].cyl((x, yh, z + 0.04), 0.014, 0.05, seg=12)                           # valve body
        P["handle"].box((x + 0.025, yh - 0.012, z + 0.07), (0.06, 0.014, 0.01))            # quarter-turn handle
        P["steel"].cyl((x, yh, z + 0.09), 0.018, 0.02, seg=12)                           # quick coupling
        P["rubber"].path([(x, yh, z + 0.1), (x, yh - 0.02, z + 0.2), (x + 0.03, y0 - 0.02, z + 0.32)], 0.009, seg=8)


def cable_tray(P, x0, x1, z, y0, seed=0):
    yt = y0 - 0.06
    P["alu"].box(((x0 + x1) / 2, yt, z - 0.025), (x1 - x0, 0.1, 0.006))
    for s in (-1, 1):
        P["alu"].box(((x0 + x1) / 2, yt + s * 0.05, z), (x1 - x0, 0.005, 0.05))
    k = 0
    x = x0 + 0.04
    while x < x1:
        P["alu_dark"].box((x, yt, z - 0.02), (0.008, 0.1, 0.008))
        x += 0.12
        k += 1
    for i, key in enumerate(("cable_b", "cable_g", "cable_o", "cable_g", "cable_b")):
        K.cable_run(P[key], [(x0 + 0.02, yt - 0.03 + i * 0.015, z - 0.008), (x1 - 0.02, yt - 0.03 + i * 0.015, z - 0.008)],
                    n=1, r=0.008, spread=0.004, seed=seed + i)


def linear_axis(P, x0, x1, z, y0, car_x=None):
    """Rail pair with a carriage and a linear-encoder scale (ticks) + read head."""
    cx = (x0 + x1) / 2
    for dz in (-0.05, 0.05):
        P["steel"].box((cx, y0 - 0.02, z + dz), (x1 - x0, 0.03, 0.02))
    P["steel"].box((cx, y0 - 0.012, z - 0.09), (x1 - x0, 0.006, 0.02))                  # encoder scale
    x = x0 + 0.01
    while x < x1:
        P["chip"].box((x, y0 - 0.016, z - 0.09), (0.002, 0.003, 0.012))
        x += 0.02
    car_x = cx if car_x is None else car_x
    P["anod"].box((car_x, y0 - 0.06, z), (0.18, 0.06, 0.16))
    P["alu_dark"].box((car_x, y0 - 0.03, z - 0.09), (0.05, 0.03, 0.03))                  # read head
    P["led_c"].box((car_x + 0.07, y0 - 0.092, z + 0.05), (0.01, 0.004, 0.01))


def hexapod_mirror(P, M_mbs, p, n, r, seed=0):
    """Solid mirror on a hexapod (uses kit_r2's mirror; M_mbs needs mirror/mount/bolt/substrate/spot/copper)."""
    return K.mirror_with_mount(M_mbs["mirror"], M_mbs["mount"], M_mbs["bolt"], p, n, r, seed=seed,
                               mbsub=M_mbs["substrate"], mbspot=M_mbs.get("spot"), spot=0.55,
                               mbpipe=M_mbs.get("copper"), mbcable=P["cable_b" if seed % 2 else "cable_o"])


# ------------------------------------------------------------------ layout
def _clear(keep, c, r):
    return all((Vector(c) - Vector(k)).length > kr + r for k, kr in keep)


def populate_wall(P, x0, x1, z0, z1, y0, seed=0, keep=(), scale=1.0, chain=True):
    """Lay out 8-12 large nameable parts on a wall (front face y0, parts toward -Y)."""
    rnd = random.Random(seed)
    w, h = x1 - x0, z1 - z0
    s = scale
    # top band: cable tray + card cage(s)
    zt = z1 - 0.08 * s
    cable_tray(P, x0 + 0.04, x1 - 0.04, zt, y0, seed=seed)
    ch = min(0.32 * s, h * 0.22)
    ncage = max(1, int(w / (0.75 * s)))
    cw = min(0.55 * s, w / ncage - 0.12)
    for i in range(ncage):
        cx = x0 + (i + 0.5) * w / ncage
        cz = zt - 0.08 * s - ch / 2
        if _clear(keep, (cx, y0 - 0.15, cz), max(cw, ch) / 2):
            card_cage(P, cx - cw / 2, cx + cw / 2, cz - ch / 2, cz + ch / 2, y0, seed=seed + i)
    # middle band(s): alternate turbo pump on an elbow / gate valve on a pipe / gauge + viewport
    nr = max(1, int((h - 0.5 * s) / (0.5 * s)))
    rows = [z0 + 0.3 * s + (h - 0.62 * s) * (k + 0.5) / nr for k in range(nr)][::-1]
    for ri, zm in enumerate(rows):
        nm = max(2, int(w / (0.48 * s)))
        for i in range(nm):
            cx = x0 + (i + 0.5) * w / nm + rnd.uniform(-0.04, 0.04) * s
            kind = (i + seed + ri) % 3
            if kind == 0:
                r = 0.1 * s
                top = Vector((cx, y0 - 0.2 * s, zm + 0.12 * s))
                if _clear(keep, (cx, y0 - 0.2 * s, zm), 0.24 * s):
                    P["steel"].path([Vector((cx, y0, top.z + 0.08 * s)), Vector((cx, top.y, top.z + 0.08 * s)),
                                     top], r * 0.7, seg=20)                              # elbow from the wall
                    turbo_pump(P, top, (0, 0, -1), r, cable_to=(cx + 0.12 * s, y0 - 0.02, z0 + 0.25 * s))
            elif kind == 1:
                r = 0.075 * s
                yc = y0 - 0.16 * s
                if _clear(keep, (cx, yc, zm), 0.28 * s):
                    gate_valve(P, (cx, yc, zm - 0.1 * s), (1, 0, 0), r)
                    for sx in (-1, 1):                                                   # pipe bends to the wall
                        a = Vector((cx + sx * r * 2.2, yc, zm - 0.1 * s))
                        b = a + Vector((sx * 0.08 * s, 0, 0))
                        P["steel"].path([a, b, Vector((b.x, y0, b.z))], r * 0.75, seg=16)
            else:
                if _clear(keep, (cx, y0 - 0.1 * s, zm), 0.2 * s):
                    gauge(P, (cx - 0.09 * s, y0, zm + 0.1 * s), (0, -1, 0), 0.04 * s)
                    viewport(P, (cx + 0.1 * s, y0, zm - 0.08 * s), (0, -1, 0), 0.07 * s)
                    bellows(P, (cx - 0.2 * s, y0 - 0.06 * s, zm - 0.18 * s), (cx + 0.2 * s, y0 - 0.06 * s, zm - 0.18 * s),
                            0.035 * s)
    # bottom band: manifold, drag chain
    zb = z0 + 0.14 * s
    if _clear(keep, ((x0 + x1) / 2, y0 - 0.08, zb), 0.05):
        manifold(P, x0 + 0.08, x1 - 0.08, zb + 0.05 * s, y0)
    if chain and w > 0.9 and _clear(keep, (x0 + w * 0.3, y0 - 0.1, z0 + 0.05), 0.12):
        drag_chain(P, Vector((x0 + 0.12, y0 - 0.06, z0 + 0.04)), min(0.9, w * 0.45), R=0.06 * s,
                   axis=(1, 0, 0), up=(0, 0, 1))
