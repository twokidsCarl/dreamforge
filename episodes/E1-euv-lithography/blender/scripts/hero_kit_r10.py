"""Round 10 (P1): nameable high-detail interior assets that replace the R8/R9 "LED box + threaded pipe + PCB"
greeble everywhere (R9 review, next-round item 1: "viewers cannot name a single part - it reads as sci-fi greeble").

Every function builds ONE part a viewer can name, out of batched geometry (kit_r2.MB per material key):

  hexapod            six-strut hexapod: triangular base plate, actuator legs (motor can, screw, ball joints), top ring
  mirror_hexapod     solid mirror (coated face, thick body, mount cell, cooling lines) on a hexapod
  flange_viewport    vacuum port: CF nipple from the wall, flange pair + bolt circle, thick glass viewport,
                     clamp ring, side KF port with wing-nut clamp
  cooling_bundle     4-6 coolant hoses (supply / return) in a bundle with bolted P-clamps and a distribution block
  maglev_rail        mask-stage maglev: stator beam, alternating magnet track, coil mover with hoses, encoder scale
  planar_motor       wafer-stage planar motor: Halbach checkerboard magnet plate, coil mover, ceramic chuck + wafer,
                     interferometer mirror blocks, umbilical
  droplet_generator  tin droplet generator: heated reservoir (heater bands + terminals), filter housing, gas valve,
                     piezo nozzle cartridge, mounting flange
  valve_island       pneumatic valve island: manifold block, solenoid valve slices with labels, multipin connector,
                     push-in fittings + air-tube bundle, tied cable harness to the wall
  cable_harness      tied cable bundle with ties and a connector at each end
  extrusion_frame    slotted aluminium-profile frame (the back plate structure)

  wall_r10           lays the parts above out on a wall (front face y = y0, parts toward -Y), in rows, with
                     keep-clear spheres; no PCBs, no LED boxes, no random blocks.

Colour discipline (R9): no orange / yellow / copper. Orange stays the laser's colour.
"""
import math
import random

from mathutils import Matrix, Vector

import kit_r2 as K

KEYS = ("alu", "alu_dark", "steel", "blast", "anod", "paint_grey", "paint", "rubber", "glass", "hose_b", "hose_w",
        "magnet", "magnet2", "coil", "ceramic", "solenoid", "label", "coat", "subs", "wafer", "chain", "cable_k",
        "cable_g", "screen", "granite", "mask", "brushed", "facet")   # R11: brushed plates, polished facets


def new_parts():
    return {k: K.MB() for k in KEYS}


def materials(M):
    if "hose_b" not in M:
        M["hose_b"] = K.mat("HoseBlueR10", (0.1, 0.24, 0.55), rough=0.5, coat=0.2)
        M["hose_w"] = K.mat("HoseWhiteR10", (0.78, 0.8, 0.82), rough=0.45, coat=0.2)
        M["magnet"] = K.mat("MagnetNiR10", (0.55, 0.56, 0.6), metal=1.0, rough=0.25)
        M["magnet2"] = K.mat("MagnetDarkR10", (0.16, 0.17, 0.2), metal=0.9, rough=0.3)
        M["coil"] = K.mat("CoilEpoxyR10", (0.1, 0.11, 0.13), rough=0.35, coat=0.5)
        M["ceramic"] = K.mat("CeramicR10", (0.88, 0.88, 0.86), rough=0.3, coat=0.2)
        M["solenoid"] = K.mat("SolenoidR10", (0.06, 0.065, 0.07), rough=0.4)
        M["label"] = K.mat("LabelR10", (0.86, 0.87, 0.88), rough=0.6)
        M["cable_k"] = K.mat("CableBlackR10", (0.05, 0.05, 0.055), rough=0.5)
        M["screenR10"] = K.emit_mat("GaugeLCDR10", (0.75, 0.85, 0.95), 1.5)
        M.setdefault("blast", K.mat("Blasted", (0.55, 0.56, 0.6), metal=1.0, rough=0.55, speck=0.25))
        M.setdefault("rubber", K.mat("Rubber", (0.04, 0.04, 0.045), rough=0.7))
        M.setdefault("glass", K.mat("ViewGlass", (0.9, 0.95, 1.0), rough=0.02, transmission=1.0, ior=1.5))
        M.setdefault("chain", K.mat("DragChain", (0.05, 0.05, 0.055), rough=0.45))
        M.setdefault("granite", K.mat("Granite", (0.1, 0.1, 0.11), rough=0.35, speck=0.6))
        M.setdefault("paint", K.mat("PaintWhite", (0.72, 0.74, 0.77), rough=0.32, coat=0.4))
        M.setdefault("paint_grey", K.mat("PaintGrey", (0.32, 0.34, 0.38), rough=0.45))
    if "brushed" not in M:                                   # R11 (hero_kit_r11): housing plates, facet strips
        M["brushed"] = K.mat("BrushedAluR11", (0.7, 0.71, 0.74), metal=1.0, rough=0.22, brushed=0.35)
        M["facet"] = K.mat("FacetMirrorR11", (0.86, 0.85, 0.9), metal=1.0, rough=0.035, coat=0.6)
    out = {k: M[k] for k in KEYS if k in M}
    out["coat"] = M.get("coating", M.get("mirror"))
    out["subs"] = M.get("substrate", M["alu"])
    out["wafer"] = M.get("wafer", out["coat"])
    out["screen"] = M["screenR10"]
    out["cable_g"] = M.get("cable_g", M["paint_grey"])
    if "mask_r10" not in M:
        M["mask_r10"] = mask_material()
    out["mask"] = M["mask_r10"]
    return out


def finish(P, M, tag, parent=None):
    mats = materials(M)
    bev = {"anod": 0.004, "paint_grey": 0.004, "alu_dark": 0.003, "blast": 0.004, "solenoid": 0.003,
           "ceramic": 0.004, "paint": 0.006, "coil": 0.003, "brushed": 0.008}
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


def _basis(n, up=(0, 0, 1)):
    """Right-handed frame (u, v, n) with n the given normal and v as close to `up` as possible."""
    n = Vector(n).normalized()
    up = Vector(up)
    if abs(n.dot(up.normalized())) > 0.95:
        up = Vector((0, 1, 0)) if abs(n.y) < 0.9 else Vector((1, 0, 0))
    u = up.cross(n).normalized()
    v = n.cross(u).normalized()
    return u, v, n


def _rot(u, v, n):
    return Matrix((u, v, n)).transposed().to_euler()


def _cyl(mb, c, n, r, h, seg=24, r2=None):
    mb.cyl_m(Matrix.Translation(Vector(c)) @ _q(n).to_matrix().to_4x4(), r, h, seg=seg, r2=r2)


def _ring(mb, c, n, ro, ri, h, seg=40):
    mb.ring(Vector(c), ro, ri, h, rot=_q(n).to_euler(), seg=seg)


def _bolt_circle(P, c, n, R, k, r, h, nuts=True):
    """Bolt heads (hex) + washers on a circle, facing n."""
    c, n = Vector(c), Vector(n).normalized()
    e = _q(n).to_euler()
    P["steel"].bolts(c + n * h * 0.5, R, k, r, h, rot=e)
    if nuts:
        P["alu_dark"].bolts(c + n * 0.002, R, k, r * 1.45, 0.003, rot=e)


def _offset_poly(pts, off):
    return [Vector(p) + off for p in pts]


# ------------------------------------------------------------------ 1. hexapod
def hexapod(P, base_c, top_c, r_base, r_top, n=None, plate_key="alu", leg_key="anod"):
    """Stewart platform: triangular base plate with 3 pairs of clevis blocks, 6 legs (motor can + screw jack +
    ball joints) crossing to a top ring. Axis from base_c to top_c."""
    base_c, top_c = Vector(base_c), Vector(top_c)
    ax = (top_c - base_c).normalized() if n is None else Vector(n).normalized()
    u, v, _ = _basis(ax)
    e = _rot(u, v, ax)
    H = (top_c - base_c).length
    # triangular base plate with rounded corners (hexagon with 3 long + 3 short sides)
    tri = []
    for i in range(3):
        a = math.radians(90 + 120 * i)
        for s in (-1, 1):
            b = a + s * math.radians(22)
            tri.append(base_c + (u * math.cos(b) + v * math.sin(b)) * r_base * 1.15)
    mb = P[plate_key]
    t = max(0.012, r_base * 0.12)
    lo = [mb.bm.verts.new(p - ax * t / 2) for p in tri]
    hi = [mb.bm.verts.new(p + ax * t / 2) for p in tri]
    mb.bm.faces.new(lo[::-1])
    mb.bm.faces.new(hi)
    for i in range(6):
        j = (i + 1) % 6
        mb.bm.faces.new((lo[i], lo[j], hi[j], hi[i]))
    # top ring
    _ring(P[plate_key], top_c, ax, r_top * 1.05, r_top * 0.72, max(0.01, r_top * 0.14), seg=48)
    _bolt_circle(P, top_c + ax * r_top * 0.07, ax, r_top * 0.88, 12, r_top * 0.03, r_top * 0.03, nuts=False)
    for i in range(6):
        pair = i // 2
        s = 1 if i % 2 else -1
        ab = math.radians(90 + 120 * pair + s * 14)
        at = math.radians(90 + 120 * pair + 60 * s + (60 if s < 0 else -60) + s * 46)
        b = base_c + ax * t / 2 + (u * math.cos(ab) + v * math.sin(ab)) * r_base * 0.92
        tp = top_c - ax * r_top * 0.07 + (u * math.cos(at) + v * math.sin(at)) * r_top * 0.9
        d = (tp - b)
        L = d.length
        dn = d.normalized()
        rr = max(0.006, r_base * 0.07)
        P["alu_dark"].box(b + ax * rr, (rr * 2.6, rr * 2.6, rr * 2.2), rot=e)                # clevis block
        P["steel"].sphere(b + ax * rr * 2.2, rr * 1.15, 12)                                   # lower ball joint
        p0 = b + ax * rr * 2.2
        p1 = p0 + dn * L * 0.42
        _cyl(P[leg_key], p0.lerp(p1, 0.5), dn, rr * 1.35, L * 0.42, seg=16)                  # motor + gearbox can
        _ring(P["alu"], p1, dn, rr * 1.5, rr * 1.0, rr * 0.5, seg=16)                         # collar
        p2 = tp - dn * rr * 1.2
        P["steel"].tube(p1, p2, rr * 0.6, seg=12)                                             # screw jack rod
        P["steel"].sphere(tp, rr * 1.0, 12)                                                   # upper ball joint
        P["cable_k"].path([p0 + u * rr * 1.2 + dn * L * 0.15, p0 + u * rr * 3 - ax * rr * 2,
                           b - ax * rr + u * rr * 4], rr * 0.28, seg=6)                       # motor lead
    return top_c


def mirror_hexapod(P, p, n, r, seed=0, hex_len=None, spot_mb=None):
    """Solid EUV mirror at p facing n (front face on p) in a machined cell, carried by a hexapod behind it."""
    p, n = Vector(p), Vector(n).normalized()
    u, v, _ = _basis(n)
    R = _q(n).to_matrix().to_4x4()
    thick = r * 0.42
    P["coat"].cyl_m(Matrix.Translation(p - n * 0.004) @ R, r * 0.985, 0.008, seg=64)
    back = p - n * (thick / 2 + 0.008)
    P["subs"].cyl_m(Matrix.Translation(back) @ R, r, thick, seg=64)
    if spot_mb is not None:
        spot_mb.cyl_m(Matrix.Translation(p + n * 0.002) @ R, r * 0.6, 0.002, seg=32)
    # mount cell: ring around the body with 3 flexure tabs
    _ring(P["alu"], back, n, r * 1.14, r * 1.0, thick * 1.2, seg=64)
    for i in range(3):
        a = math.radians(90 + 120 * i)
        d = u * math.cos(a) + v * math.sin(a)
        P["alu_dark"].box(back + d * r * 1.2, (r * 0.2, r * 0.2, thick * 1.3), rot=_rot(*_basis(n)))
        _cyl(P["steel"], back + d * r * 1.2 + n * thick * 0.66, n, r * 0.04, r * 0.03, seg=6)
    _bolt_circle(P, back + n * thick * 0.6, n, r * 1.07, 16, r * 0.022, r * 0.02, nuts=False)
    plate_c = back - n * (thick * 0.6 + 0.01)
    P["alu"].cyl_m(Matrix.Translation(plate_c) @ R, r * 0.8, 0.025, seg=6)
    hl = hex_len or r * 0.85
    base = plate_c - n * hl
    hexapod(P, base, plate_c - n * 0.015, r * 0.85, r * 0.75, plate_key="alu", leg_key="anod")
    # cooling in / out lines from the body edge, bent away behind the hexapod
    for s in (-1, 1):
        a = back + u * s * r * 1.02 - n * thick * 0.2
        b = a + u * s * r * 0.25
        c = b - n * (hl + r * 0.2)
        P["hose_b" if s < 0 else "hose_w"].path([a, b, c, c - n * r * 0.6 + v * (-r * 0.4)], r * 0.045, seg=10)
        _cyl(P["steel"], a, u * s, r * 0.065, r * 0.06, seg=10)
    return base


# ------------------------------------------------------------------ 2. vacuum flange + viewport
def flange_viewport(P, c, n=(0, -1, 0), r=0.08, nipple=0.12, side_port=True, up=(0, 0, 1)):
    """CF port from a wall at c: short nipple tube along n, flange pair with a bolt circle (hex heads + nuts on the
    back flange), thick viewport glass behind a clamp ring, and a small KF side port with a wing-nut clamp."""
    c, n = Vector(c), Vector(n).normalized()
    u, v, _ = _basis(n, up)
    _ring(P["alu"], c + n * 0.01, n, r * 1.35, r * 0.85, 0.02, seg=40)                        # weld collar
    P["steel"].tube(c, c + n * nipple, r * 0.9, seg=40)                                       # nipple
    f1 = c + n * nipple
    _ring(P["alu"], f1, n, r * 1.6, r * 0.88, r * 0.3, seg=48)                                # flange 1
    _ring(P["alu"], f1 + n * r * 0.32, n, r * 1.6, r * 0.6, r * 0.3, seg=48)                  # viewport flange
    nb = 8 if r < 0.06 else 12 if r < 0.12 else 16
    _bolt_circle(P, f1 + n * r * 0.48, n, r * 1.32, nb, r * 0.075, r * 0.12)
    _bolt_circle(P, f1 - n * r * 0.16, -n, r * 1.32, nb, r * 0.075, r * 0.06, nuts=False)
    _cyl(P["glass"], f1 + n * r * 0.4, n, r * 0.62, r * 0.12, seg=40)                         # thick glass
    _ring(P["steel"], f1 + n * r * 0.5, n, r * 0.75, r * 0.58, r * 0.06, seg=40)              # clamp ring
    if side_port:
        sp = c + n * nipple * 0.5 + u * r * 0.9
        P["steel"].tube(sp, sp + u * r * 0.7, r * 0.22, seg=16)
        e = sp + u * r * 0.7
        _ring(P["alu"], e, u, r * 0.34, r * 0.2, r * 0.07, seg=20)                            # KF flange
        _ring(P["alu_dark"], e + u * r * 0.06, u, r * 0.38, r * 0.3, r * 0.09, seg=20)        # KF clamp
        P["alu_dark"].box(e + u * r * 0.06 + v * r * 0.42, (r * 0.08, r * 0.08, r * 0.18), rot=_rot(u, v, n))  # wing nut
        _cyl(P["blast"], e + u * r * 0.2, u, r * 0.16, r * 0.3, seg=16)                       # blank / gauge stub


# ------------------------------------------------------------------ 3. cooling hose bundle
def cooling_bundle(P, pts, k=4, r=0.012, gap=None, clamp_every=0.35, up=(0, 0, 1), block=True):
    """k coolant hoses side by side along polyline pts (alternating supply blue / return white), P-clamps bolted
    to a strut every clamp_every metres, a distribution block with push-in fittings at the start."""
    pts = [Vector(p) for p in pts]
    gap = gap or r * 2.6
    d0 = (pts[1] - pts[0]).normalized()
    side = d0.cross(Vector(up))
    if side.length < 1e-3:
        side = d0.cross(Vector((0, 1, 0)))
    side.normalize()
    for i in range(k):
        off = side * (i - (k - 1) / 2) * gap
        P["hose_b" if i % 2 == 0 else "hose_w"].path(_offset_poly(pts, off), r, seg=12)
    # clamps
    for a, b in zip(pts, pts[1:]):
        L = (b - a).length
        d = (b - a).normalized()
        sd = d.cross(Vector(up))
        if sd.length < 1e-3:
            sd = d.cross(Vector((0, 1, 0)))
        sd.normalize()
        nn = d.cross(sd).normalized()
        e = _rot(sd, nn, d)
        m = max(1, int(L / clamp_every))
        for j in range(1, m + 1):
            p = a + d * (L * j / (m + 1))
            P["alu"].box(p, (gap * k + r * 2, r * 2.6, r * 1.6), rot=e)                     # clamp body
            P["steel"].box(p + sd * (gap * k / 2 + r * 1.6), (r * 1.4, r * 1.4, r * 2.2), rot=e)  # bolt
            P["steel"].box(p - sd * (gap * k / 2 + r * 1.6), (r * 1.4, r * 1.4, r * 2.2), rot=e)
    if block:
        a = pts[0]
        e = _rot(side, d0.cross(side).normalized(), d0)
        P["alu"].box(a - d0 * r * 2.5, (gap * k + r * 3, r * 5, r * 5), rot=e)                # distribution block
        for i in range(k):
            off = side * (i - (k - 1) / 2) * gap
            _cyl(P["steel"], a + off - d0 * r * 0.2, d0, r * 1.35, r * 1.2, seg=12)           # push-in fittings
            _ring(P["hose_b" if i % 2 == 0 else "hose_w"], a + off + d0 * r * 0.5, d0, r * 1.4, r * 1.0, r * 0.4, seg=12)
        P["label"].box(a - d0 * r * 2.5 + d0.cross(side).normalized() * r * 2.55, (gap * k * 0.7, r * 0.1, r * 2.2), rot=e)


# ------------------------------------------------------------------ 4. mask-stage maglev rail
def maglev_rail(P, x0, x1, y, z, car_x=None, car_w=0.7, depth=0.32, coil_hoses=True, encoder=True):
    """Long-stroke maglev of the reticle stage, along X at (y, z): stator beam, top track of alternating magnet
    blocks (two finishes), coil mover wrapping the track with cooling hoses and cable, encoder scale + read head.
    Returns the mover's centre (the mask chuck sits under / on it)."""
    cx = (x0 + x1) / 2
    L = x1 - x0
    P["anod"].box((cx, y, z - 0.07), (L, depth, 0.1))                                        # stator beam
    for s in (-1, 1):
        P["alu_dark"].box((cx, y + s * depth * 0.42, z - 0.02), (L, 0.012, 0.05))             # side guards
    pitch = 0.06
    k = int(L / pitch)
    for i in range(k):
        P["magnet" if i % 2 else "magnet2"].box((x0 + (i + 0.5) * pitch, y, z), (pitch * 0.9, depth * 0.62, 0.025))
    for i in range(int(L / 0.2) + 1):                                                          # stator bolts
        for s in (-1, 1):
            P["steel"].cyl((x0 + 0.05 + i * 0.2, y + s * depth * 0.44, z + 0.006), 0.008, 0.01, seg=6)
    if encoder:
        ye = y - depth * 0.5 - 0.02
        P["glass"].box((cx, ye, z - 0.04), (L, 0.006, 0.03))                                  # glass scale
        xx = x0 + 0.01
        while xx < x1:
            P["alu_dark"].box((xx, ye - 0.004, z - 0.04), (0.003, 0.002, 0.018))
            xx += 0.03
    car_x = cx if car_x is None else car_x
    # coil mover: U-shaped yoke around the track
    P["coil"].box((car_x, y, z + 0.06), (car_w, depth * 0.9, 0.07))
    for s in (-1, 1):
        P["coil"].box((car_x, y + s * depth * 0.5, z + 0.0), (car_w, 0.04, 0.12))
        for j in range(int(car_w / 0.08)):                                                    # coil windings edge
            P["alu_dark"].box((car_x - car_w / 2 + 0.04 + j * 0.08, y + s * (depth * 0.5 + 0.021), z + 0.0),
                              (0.05, 0.004, 0.08))
    P["alu"].box((car_x, y, z + 0.11), (car_w * 1.04, depth * 0.95, 0.025))                   # mover top plate
    for sx in (-1, 1):
        for sy in (-1, 1):
            P["steel"].cyl((car_x + sx * car_w * 0.45, y + sy * depth * 0.4, z + 0.126), 0.01, 0.008, seg=6)
    if encoder:
        P["alu_dark"].box((car_x, y - depth * 0.5 - 0.04, z - 0.03), (0.06, 0.03, 0.05))     # read head
    if coil_hoses:
        a = Vector((car_x + car_w * 0.35, y + depth * 0.2, z + 0.13))
        cooling_bundle(P, [a, a + Vector((0, 0, 0.12)), a + Vector((car_w * 0.6, depth * 0.3, 0.2))], k=2, r=0.009,
                       clamp_every=1.0, block=False)
        P["cable_k"].path([Vector((car_x - car_w * 0.35, y + depth * 0.2, z + 0.13)),
                           Vector((car_x - car_w * 0.35, y + depth * 0.25, z + 0.28)),
                           Vector((car_x - car_w * 0.9, y + depth * 0.4, z + 0.32))], 0.012, seg=8)
    return Vector((car_x, y, z))


# ------------------------------------------------------------------ 5. wafer-stage planar motor
def planar_motor(P, cx, cy, z, w, d, mover=None, mover_w=0.55, wafer_r=0.15, tiles=None, base=True):
    """Planar motor of the wafer stage. Magnet plate (top face at z): checkerboard Halbach tiles in two finishes on
    a dark base; coil mover floating above with a white ceramic chuck, the wafer, two interferometer mirror blocks
    on its edges and an umbilical. Returns the wafer centre."""
    if base:
        P["granite"].box((cx, cy, z - 0.09), (w + 0.1, d + 0.1, 0.16))
    t = tiles or 0.05
    nx, ny = int(w / t), int(d / t)
    for i in range(nx):
        for j in range(ny):
            key = "magnet" if (i + j) % 2 else "magnet2"
            P[key].box((cx - w / 2 + (i + 0.5) * t, cy - d / 2 + (j + 0.5) * t, z - 0.006), (t * 0.94, t * 0.94, 0.012))
    P["alu_dark"].box((cx, cy - d / 2 - 0.02, z - 0.02), (w + 0.1, 0.03, 0.04))               # plate edge frame
    P["alu_dark"].box((cx, cy + d / 2 + 0.02, z - 0.02), (w + 0.1, 0.03, 0.04))
    if mover is False:
        return None
    mx, my = (cx, cy) if mover is None else mover
    return planar_mover(P, mx, my, z, mover_w, wafer_r)


def planar_mover(P, mx, my, z, mover_w=0.55, wafer_r=0.15, wafer=True):
    """The moving part of the planar motor (z = magnet plate top): coil mover, frame, white ceramic chuck, pin
    chuck + wafer, interferometer mirror blocks, umbilical. Returns the wafer centre."""
    mw = mover_w
    zc = z + 0.015                                                                            # air gap
    P["coil"].box((mx, my, zc + 0.03), (mw, mw, 0.06))                                       # coil mover
    for i in range(4):                                                                        # coil edges visible
        for s in (-1, 1):
            P["alu_dark"].box((mx - mw / 2 + (i + 0.5) * mw / 4, my + s * (mw / 2 + 0.002), zc + 0.03),
                              (mw / 4 * 0.8, 0.004, 0.045))
    P["alu"].box((mx, my, zc + 0.075), (mw * 1.02, mw * 1.02, 0.03))                          # mover frame
    P["ceramic"].box((mx, my, zc + 0.11), (mw * 0.92, mw * 0.92, 0.04))                       # ceramic chuck body
    _cyl(P["ceramic"], (mx, my, zc + 0.135), (0, 0, 1), wafer_r * 1.08, 0.012, seg=64)        # pin chuck
    if wafer:
        P["wafer"].cyl((mx, my, zc + 0.1425), wafer_r, 0.003, seg=128)
    # interferometer / encoder mirror blocks on two edges
    P["coat"].box((mx, my - mw * 0.48, zc + 0.11), (mw * 0.9, 0.012, 0.035))
    P["coat"].box((mx + mw * 0.48, my, zc + 0.11), (0.012, mw * 0.9, 0.035))
    # umbilical (hoses + cable) to the side
    a = Vector((mx - mw / 2, my + mw * 0.3, zc + 0.05))
    cooling_bundle(P, [a, a + Vector((-0.12, 0, 0.05)), a + Vector((-0.35, 0.1, 0.18))], k=3, r=0.008,
                   clamp_every=1.0, block=False)
    return Vector((mx, my, zc + 0.144))


# ------------------------------------------------------------------ 6. tin droplet generator
def droplet_generator(P, nozzle_tip, axis=(0, 0, -1), s=1.0, flange_at=None):
    """Tin droplet generator pointing along axis (nozzle tip at nozzle_tip). Heated reservoir with heater bands and
    terminal boxes, insulation jacket, filter housing, gas inlet with a valve, piezo nozzle cartridge, a CF
    mounting flange where it meets the chamber (flange_at = distance from the tip, default 0.35 s)."""
    tip = Vector(nozzle_tip)
    ax = Vector(axis).normalized()                                     # flow direction (toward the plasma)
    up = -ax
    u, v, _ = _basis(up)
    fa = flange_at if flange_at is not None else 0.35 * s
    # nozzle cartridge (tapered) + piezo ring
    _cyl(P["steel"], tip + up * 0.04 * s, up, 0.012 * s, 0.08 * s, seg=20, r2=0.03 * s)
    _cyl(P["coil"], tip + up * 0.11 * s, up, 0.038 * s, 0.05 * s, seg=24)                    # piezo actuator
    P["steel"].tube(tip + up * 0.13 * s, tip + up * fa, 0.032 * s, seg=20)
    # mounting flange on the chamber
    f = tip + up * fa
    _ring(P["alu"], f, up, 0.14 * s, 0.035 * s, 0.035 * s, seg=40)
    _bolt_circle(P, f + up * 0.02 * s, up, 0.115 * s, 10, 0.009 * s, 0.014 * s)
    # filter housing
    fh = f + up * 0.12 * s
    _cyl(P["blast"], fh, up, 0.06 * s, 0.16 * s, seg=32)
    for k in (-1, 1):
        _ring(P["alu"], fh + up * k * 0.08 * s, up, 0.075 * s, 0.055 * s, 0.02 * s, seg=32)
    # reservoir with heater bands
    rv = fh + up * 0.3 * s
    _cyl(P["steel"], rv, up, 0.11 * s, 0.32 * s, seg=40)
    P["steel"].sphere(rv + up * 0.16 * s, 0.11 * s, 24)
    for k in range(4):
        zc = rv + up * (-0.12 + k * 0.08) * s
        _ring(P["alu_dark"], zc, up, 0.122 * s, 0.108 * s, 0.035 * s, seg=40)               # heater band
        tb = zc + u * 0.13 * s
        P["solenoid"].box(tb, (0.03 * s, 0.04 * s, 0.03 * s), rot=_rot(u, v, up))            # terminal box
        P["cable_k"].path([tb + u * 0.015 * s, tb + u * 0.06 * s - up * 0.02 * s,
                           tb + u * 0.09 * s + v * 0.05 * s - up * (0.1 + 0.02 * k) * s], 0.005 * s, seg=6)
    P["label"].box(rv + v * 0.112 * s, (0.08 * s, 0.002 * s, 0.05 * s), rot=_rot(u, v, up))
    # gas inlet (pressurises the tin) with a valve
    g0 = rv + up * 0.24 * s
    P["steel"].path([g0, g0 + up * 0.08 * s, g0 + up * 0.08 * s + u * 0.2 * s], 0.012 * s, seg=10)
    gv = g0 + up * 0.08 * s + u * 0.12 * s
    P["blast"].box(gv, (0.05 * s, 0.05 * s, 0.05 * s), rot=_rot(u, v, up))
    _cyl(P["solenoid"], gv + up * 0.05 * s, up, 0.018 * s, 0.05 * s, seg=16)                  # actuator
    P["cable_k"].path([gv + up * 0.075 * s, gv + up * 0.12 * s - v * 0.05 * s, gv + up * 0.1 * s - v * 0.2 * s],
                      0.006 * s, seg=6)
    # support bracket
    for k in (-1, 1):
        P["alu"].box(f + up * 0.2 * s + v * k * 0.13 * s, (0.02 * s, 0.02 * s, 0.4 * s) if abs(up.z) > 0.5 else
                     (0.02 * s, 0.02 * s, 0.02 * s), rot=_rot(u, v, up))
    return f


# ------------------------------------------------------------------ 7. valve island + harness
def cable_harness(P, pts, n=5, r=0.006, tie_every=0.12, key="cable_k", connector=True):
    """A tied bundle of n cables along pts, steel ties every tie_every m, a rectangular connector at each end."""
    pts = [Vector(p) for p in pts]
    rnd = random.Random(len(pts) * 31 + n)
    br = r * (1.0 + 0.55 * math.sqrt(n))
    for i in range(n):
        a = 2 * math.pi * i / n
        off = Vector((math.cos(a), math.sin(a), math.cos(a + 1.0))) * (br - r) * 0.8
        P[key if i % 3 else "cable_g"].path(_offset_poly(pts, off), r, seg=8)
    for a, b in zip(pts, pts[1:]):
        L = (b - a).length
        d = (b - a).normalized()
        for j in range(1, int(L / tie_every) + 1):
            _ring(P["alu_dark"], a + d * j * tie_every, d, br * 1.08, br * 0.9, r * 0.8, seg=12)
    if connector:
        for p, q in ((pts[0], pts[1]), (pts[-1], pts[-2])):
            d = (p - q).normalized()
            u, v, _ = _basis(d)
            P["solenoid"].box(p + d * br, (br * 2.6, br * 1.8, br * 2.4), rot=_rot(u, v, d))
            P["steel"].box(p + d * br * 2.3, (br * 2.2, br * 1.4, br * 0.4), rot=_rot(u, v, d))
    return br


def valve_island(P, c, n=(0, -1, 0), nval=8, s=1.0, drop=0.35, up=(0, 0, 1)):
    """Pneumatic valve island on a wall at c facing n: manifold rail, nval solenoid valve slices (black head,
    grey body, white label, manual override), end plates, multipin connector + harness, push-in fittings with an
    air-tube bundle dropping `drop` metres."""
    c, n = Vector(c), Vector(n).normalized()
    u, v, _ = _basis(n, up)
    e = _rot(u, v, n)
    pw = 0.022 * s                                                     # slice pitch
    W = nval * pw
    P["alu"].box(c + n * 0.015 * s, (W + 0.06 * s, 0.07 * s, 0.03 * s), rot=e)               # manifold rail
    P["alu_dark"].box(c + n * 0.002 * s - v * 0.0 * s, (W + 0.12 * s, 0.03 * s, 0.006 * s), rot=e)  # DIN rail
    for i in range(nval):
        x = (i - (nval - 1) / 2) * pw
        b = c + u * x + n * 0.05 * s
        P["paint_grey"].box(b, (pw * 0.92, 0.06 * s, 0.04 * s), rot=e)                       # valve body
        P["solenoid"].box(b + v * 0.04 * s + n * 0.005 * s, (pw * 0.92, 0.035 * s, 0.05 * s), rot=e)  # coil head
        P["label"].box(b + v * 0.04 * s + n * 0.031 * s, (pw * 0.7, 0.02 * s, 0.002 * s), rot=e)      # label
        _cyl(P["alu_dark"], b + v * 0.01 * s + n * 0.022 * s, n, 0.004 * s, 0.006 * s, seg=8)  # manual override
        for k in (-1, 1):                                                                     # 2 fittings / valve
            f = c + u * (x + k * pw * 0.22) - v * 0.04 * s + n * 0.04 * s
            _cyl(P["steel"], f, -v, 0.005 * s, 0.012 * s, seg=8)
    for k in (-1, 1):
        P["alu"].box(c + u * k * (W / 2 + 0.02 * s) + n * 0.045 * s, (0.03 * s, 0.075 * s, 0.065 * s), rot=e)  # end plates
    con = c + u * (W / 2 + 0.05 * s) + n * 0.05 * s
    P["solenoid"].box(con, (0.04 * s, 0.05 * s, 0.05 * s), rot=e)                             # multipin connector
    cable_harness(P, [con + u * 0.03 * s, con + u * 0.08 * s - n * 0.02 * s, con + u * 0.1 * s - v * drop - n * 0.04 * s],
                  n=6, r=0.004 * s, tie_every=0.08 * s, connector=False)
    # air tube bundle: blue + black thin tubes dropping down
    for i in range(nval * 2):
        x = (i // 2 - (nval - 1) / 2) * pw + (0.22 if i % 2 else -0.22) * pw
        a = c + u * x - v * 0.046 * s + n * 0.04 * s
        b = a - v * 0.06 * s
        cc = c + u * (x * 0.3) - v * drop + n * (0.03 + 0.002 * i) * s
        P["hose_b" if i % 2 else "cable_k"].path([a, b, cc], 0.0028 * s, seg=6)


# ------------------------------------------------------------------ 8. aluminium profile frame
def extrusion_frame(P, x0, x1, z0, z1, y0, cell=0.5, prof=0.04):
    """Slotted 40 mm aluminium profile frame flat on the wall (front y0 - prof): verticals + horizontals, corner
    gussets, slot lines on the profiles."""
    w, h = x1 - x0, z1 - z0
    nx, nz = max(1, round(w / cell)), max(1, round(h / cell))
    yc = y0 - prof / 2
    xs = [x0 + w * i / nx for i in range(nx + 1)]
    zs = [z0 + h * k / nz for k in range(nz + 1)]
    for x in xs:
        P["alu"].box((x, yc, (z0 + z1) / 2), (prof, prof, h))
        P["alu_dark"].box((x, y0 - prof - 0.001, (z0 + z1) / 2), (prof * 0.22, 0.003, h))     # T-slot
    for z in zs:
        P["alu"].box(((x0 + x1) / 2, yc, z), (w, prof, prof))
        P["alu_dark"].box(((x0 + x1) / 2, y0 - prof - 0.001, z), (w, 0.003, prof * 0.22))
    for x in xs:
        for z in zs:
            for sx, sz in ((1, 1), (-1, -1)):
                if x0 <= x + sx * prof <= x1 and z0 <= z + sz * prof <= z1:
                    P["alu_dark"].box((x + sx * prof * 1.1, yc, z + sz * prof * 1.1), (prof * 1.3, prof * 0.9, prof * 1.3),
                                      rot=(0, math.radians(45), 0))
    return xs, zs


# ------------------------------------------------------------------ wall layout
def _clear(keep, c, r):
    return all((Vector(c) - Vector(k)).length > kr + r for k, kr in keep)


def _turbo(P, c, n, r):
    """Turbomolecular pump (R8 design, re-keyed to this kit's materials): CF flange, ribbed body, drive can,
    fore-line port with KF clamp."""
    c, n = Vector(c), Vector(n).normalized()
    _ring(P["alu"], c, n, r * 1.55, r * 0.95, r * 0.28, seg=40)
    _bolt_circle(P, c + n * r * 0.16, n, r * 1.3, 12, r * 0.07, r * 0.12)
    b0 = c + n * r * 0.18
    _cyl(P["alu"], b0 + n * r * 0.65, n, r, r * 1.3, seg=40)
    for k in range(5):
        _ring(P["alu_dark"], b0 + n * (r * 0.2 + k * r * 0.24), n, r * 1.07, r * 0.98, r * 0.06, seg=40)
    _cyl(P["anod"], b0 + n * r * 1.55, n, r * 0.82, r * 0.5, seg=32)
    _cyl(P["anod"], b0 + n * r * 1.86, n, r * 0.55, r * 0.14, seg=24)
    u, v, _ = _basis(n)
    vp = b0 + n * r * 1.1 + u * r
    P["steel"].tube(vp, vp + u * r * 0.45, r * 0.16, seg=12)
    _ring(P["alu_dark"], vp + u * r * 0.45, u, r * 0.3, r * 0.14, r * 0.1, seg=20)
    P["label"].box(b0 + n * r * 0.75 - v * r * 1.0, (r * 0.4, r * 0.25, r * 0.02), rot=_rot(u, n, v))
    P["cable_k"].path([b0 + n * r * 1.9, b0 + n * r * 2.4, b0 + n * r * 2.4 - v * r * 2.5], r * 0.07, seg=8)


def _cell_panel(P, cx, cz, cw, ch, yf, rnd, s):
    """Flush machined service panel filling a frame cell (so no cell reads as an empty hole): blasted cover with
    corner bolts and a name plate; some carry a DIN terminal row with wires or a ribbed access cover."""
    pw, ph = cw - 0.05 * s, ch - 0.05 * s
    y = yf + 0.012
    P["blast" if rnd.random() < 0.6 else "paint_grey"].box((cx, y, cz), (pw, 0.012, ph))
    for sx in (-1, 1):
        for sz in (-1, 1):
            P["steel"].cyl((cx + sx * pw * 0.46, y - 0.008, cz + sz * ph * 0.46), 0.006 * s, 0.006,
                           rot=(math.radians(90), 0, 0), seg=6)
    P["label"].box((cx - pw * 0.3, y - 0.007, cz + ph * 0.4), (pw * 0.22, 0.002, ph * 0.06))
    r = rnd.random()
    if r < 0.35:                                                       # DIN rail + terminal row + wires
        zt = cz - ph * 0.33
        P["steel"].box((cx, y - 0.01, zt), (pw * 0.86, 0.008, 0.03 * s))
        nt = max(4, int(pw * 0.86 / (0.02 * s)))
        for t in range(nt):
            tx = cx - pw * 0.43 + (t + 0.5) * pw * 0.86 / nt
            P["paint_grey" if t % 6 else "label"].box((tx, y - 0.025 * s, zt), (0.016 * s, 0.03 * s, 0.05 * s))
            if t % 2 == 0:
                P["cable_k" if t % 4 else "hose_b"].path([(tx, y - 0.03 * s, zt + 0.025 * s),
                                                          (tx, y - 0.035 * s, zt + ph * 0.25)], 0.0025 * s, seg=5)
    elif r < 0.6:                                                      # ribbed access cover
        for k in range(5):
            P["alu_dark"].box((cx, y - 0.012, cz - ph * 0.3 + k * ph * 0.15), (pw * 0.8, 0.012, 0.012 * s))


def wall_r10(P, x0, x1, z0, z1, y0, seed=0, keep=(), scale=1.0, depth=1.0, frame=True, roof=False):
    """R10 bay wall: aluminium-profile frame on the plate; in every frame cell ONE large nameable part
    (CF viewport port, valve island + harness, turbo pump on an elbow, cooling distribution with hose bundle,
    hexapod spare / sensor mount on a bracket); a horizontal hose bundle + harness tray along the top and a
    coolant header along the bottom. depth scales how far the parts stand off the wall (mid-depth layer)."""
    rnd = random.Random(seed * 17 + 3)
    s = scale
    w, h = x1 - x0, z1 - z0
    cell = 0.55 * s
    if frame:
        xs, zs = extrusion_frame(P, x0, x1, z0, z1, y0, cell=cell, prof=0.04 * min(1.4, s))
    else:
        nx, nz = max(1, round(w / cell)), max(1, round(h / cell))
        xs = [x0 + w * i / nx for i in range(nx + 1)]
        zs = [z0 + h * k / nz for k in range(nz + 1)]
    yf = y0 - 0.045 * min(1.4, s)
    # top: harness tray + horizontal hose bundle
    zt = z1 - 0.09 * s
    if _clear(keep, ((x0 + x1) / 2, yf - 0.05, zt), 0.0) or True:
        P["alu_dark"].box(((x0 + x1) / 2, yf - 0.05 * s, zt - 0.03 * s), (w - 0.04, 0.1 * s, 0.006))
        P["alu_dark"].box(((x0 + x1) / 2, yf - 0.1 * s, zt), (w - 0.04, 0.006, 0.05 * s))
        cable_harness(P, [(x0 + 0.03, yf - 0.05 * s, zt - 0.005), (x1 - 0.03, yf - 0.05 * s, zt - 0.005)], n=7,
                      r=0.006 * s, tie_every=0.15 * s, connector=False)
        cooling_bundle(P, [(x0 + 0.05, yf - 0.03 * s, zt - 0.09 * s), (x1 - 0.05, yf - 0.03 * s, zt - 0.09 * s)],
                       k=4, r=0.011 * s, clamp_every=0.4 * s, block=True, up=(0, 1, 0))
    # bottom: coolant header with branch valves
    zb = z0 + 0.1 * s
    P["steel"].tube((x0 + 0.04, yf - 0.05 * s, zb), (x1 - 0.04, yf - 0.05 * s, zb), 0.02 * s, seg=16)
    P["hose_w"].tube((x0 + 0.04, yf - 0.1 * s, zb + 0.05 * s), (x1 - 0.04, yf - 0.1 * s, zb + 0.05 * s), 0.016 * s, seg=14)
    for i in range(max(2, int(w / (0.25 * s)))):
        x = x0 + (i + 0.5) * w / max(2, int(w / (0.25 * s)))
        _cyl(P["steel"], (x, yf - 0.05 * s, zb + 0.035 * s), (0, 0, 1), 0.014 * s, 0.04 * s, seg=12)
        P["alu_dark"].box((x + 0.02 * s, yf - 0.065 * s, zb + 0.06 * s), (0.05 * s, 0.012 * s, 0.008 * s))
    # cells between the top tray and the bottom header
    zc0, zc1 = zb + 0.12 * s, zt - 0.16 * s
    if zc1 - zc0 < 0.2 * s:
        return
    nz = max(1, round((zc1 - zc0) / cell))
    nx = max(1, round(w / cell))
    cw, ch = w / nx, (zc1 - zc0) / nz
    kinds = ["port", "island", "turbo", "bundle", "hexapod", "flange_gauge"]
    order = list(range(len(kinds)))
    cells = []                                                         # (cx, cz, cell width, cell height)
    for k in range(nz):
        x = x0
        while x < x1 - cw * 0.5:
            span = rnd.choice((1, 1, 2)) if x1 - x > cw * 1.9 else 1
            cells.append((x + span * cw / 2, zc0 + (k + 0.5) * ch, span * cw, ch))
            x += span * cw
    for idx, (cx, cz, cwi, chi) in enumerate(cells):
        if idx % len(kinds) == 0:
            rnd.shuffle(order)
        kind = kinds[order[idx % len(kinds)]]
        m = min(cwi, chi)
        if cwi > chi * 1.5 and kind in ("hexapod", "flange_gauge"):
            kind = "island" if idx % 2 else "turbo"
        _cell_panel(P, cx, cz, cwi, chi, yf, rnd, s)
        if not _clear(keep, (cx, yf - 0.15 * s * depth, cz), m * 0.4):
            continue
        if kind == "port":
            r = m * 0.17
            flange_viewport(P, (cx, yf, cz), (0, -1, 0), r, nipple=r * 1.3 * depth)
        elif kind == "flange_gauge":
            r = m * 0.12
            flange_viewport(P, (cx - m * 0.18, yf, cz + m * 0.1), (0, -1, 0), r, nipple=r * 1.6 * depth,
                            side_port=False)
            g = Vector((cx + m * 0.2, yf, cz - m * 0.12))                                 # gauge head on a nipple
            P["steel"].tube(g, g + Vector((0, -m * 0.15, 0)), m * 0.04, seg=12)
            _ring(P["alu"], g + Vector((0, -m * 0.15, 0)), (0, -1, 0), m * 0.08, m * 0.04, m * 0.03, seg=20)
            hd = g + Vector((0, -m * 0.25, 0))
            P["anod"].box(hd, (m * 0.2, m * 0.16, m * 0.2))
            P["screen"].box(hd + Vector((0, -m * 0.081, m * 0.03)), (m * 0.13, 0.002, m * 0.06))
            cable_harness(P, [hd - Vector((0, 0, m * 0.1)), hd - Vector((0, -0.01, m * 0.3)),
                              Vector((hd.x + m * 0.2, yf - 0.01, cz - ch * 0.5))], n=2, r=0.004 * s,
                          connector=False)
        elif kind == "island":
            valve_island(P, (cx, yf, cz + m * 0.1), (0, -1, 0), nval=rnd.choice((6, 8, 10)),
                         s=min(1.6, m / 0.32), drop=ch * 0.45)
        elif kind == "turbo":
            r = m * 0.16
            if cwi > chi * 1.5:                                           # wide cell: pump + gate valve on a pipe
                gx = cx + cwi * 0.25
                gz = cz - m * 0.1
                P["steel"].path([Vector((gx - cwi * 0.2, yf, gz)), Vector((gx - cwi * 0.2, yf - m * 0.3 * depth, gz)),
                                 Vector((gx + cwi * 0.18, yf - m * 0.3 * depth, gz))], m * 0.07, seg=20)
                gb = Vector((gx, yf - m * 0.3 * depth, gz))
                P["blast"].box(gb, (m * 0.08, m * 0.36, m * 0.5))                         # gate valve body
                for sx in (-1, 1):
                    _ring(P["alu"], gb + Vector((sx * m * 0.05, 0, 0)), (sx, 0, 0), m * 0.12, m * 0.07, m * 0.03)
                    _bolt_circle(P, gb + Vector((sx * m * 0.07, 0, 0)), (sx, 0, 0), m * 0.1, 8, m * 0.008, m * 0.012)
                _cyl(P["steel"], gb + Vector((0, 0, m * 0.36)), (0, 0, 1), m * 0.05, m * 0.22, seg=20)  # actuator
                _cyl(P["alu_dark"], gb + Vector((0, 0, m * 0.48)), (0, 0, 1), m * 0.06, m * 0.03, seg=20)
                P["hose_b"].path([gb + Vector((m * 0.05, 0, m * 0.4)), gb + Vector((m * 0.12, 0, m * 0.42)),
                                  gb + Vector((m * 0.14, 0.02, -m * 0.3))], 0.004, seg=6)
                cx = cx - cwi * 0.22
            top = Vector((cx, yf - m * 0.35 * depth, cz + m * 0.12))
            P["steel"].path([Vector((cx, yf, top.z + m * 0.16)), Vector((cx, top.y, top.z + m * 0.16)), top],
                            r * 0.7, seg=20)
            _turbo(P, top, (0, 0, -1), r)
        elif kind == "bundle":
            # vertical hose bundle from a distribution block, with a manifold of quarter-turn valves
            a = Vector((cx - m * 0.2, yf - 0.03 * s, cz + ch * 0.4))
            cooling_bundle(P, [a, a + Vector((0, 0, -ch * 0.55)), a + Vector((m * 0.4, -0.05 * depth, -ch * 0.75))],
                           k=5, r=0.01 * s, clamp_every=0.18 * s, block=True, up=(0, -1, 0))
            P["blast"].box((cx + m * 0.22, yf - 0.06 * s, cz + m * 0.05), (m * 0.3, 0.1 * s, m * 0.42))   # flow meter block
            for j in range(3):
                _cyl(P["glass"], (cx + m * 0.22, yf - 0.112 * s, cz + m * (0.16 - j * 0.11)), (0, -1, 0),
                     m * 0.035, 0.006, seg=16)
                _ring(P["steel"], (cx + m * 0.22, yf - 0.115 * s, cz + m * (0.16 - j * 0.11)), (0, -1, 0),
                      m * 0.045, m * 0.035, 0.008, seg=16)
        elif kind == "hexapod":
            # sensor / metrology frame mount on a hexapod standing off the wall
            base = Vector((cx, yf - 0.005, cz))
            topc = base + Vector((0, -m * 0.38 * depth, 0))
            hexapod(P, base, topc, m * 0.26, m * 0.2, plate_key="alu", leg_key="anod")
            P["blast"].box(topc + Vector((0, -m * 0.06, 0)), (m * 0.36, m * 0.1, m * 0.3))
            _cyl(P["glass"], topc + Vector((0, -m * 0.115, m * 0.04)), (0, -1, 0), m * 0.06, 0.01, seg=20)
            cable_harness(P, [topc + Vector((m * 0.18, -m * 0.06, 0)), topc + Vector((m * 0.3, 0.0, -m * 0.2)),
                              Vector((cx + m * 0.35, yf - 0.01, cz - ch * 0.45))], n=3, r=0.004 * s,
                          connector=False)
    # vertical harness drops at frame verticals (between cells), tied
    for x in xs[1:-1]:
        if _clear(keep, (x, yf - 0.03, (z0 + z1) / 2), 0.05):
            cable_harness(P, [(x + 0.03 * s, yf - 0.03 * s, zt - 0.04 * s), (x + 0.03 * s, yf - 0.03 * s, zb + 0.08 * s)],
                          n=4, r=0.005 * s, tie_every=0.12 * s, connector=False)


# ------------------------------------------------------------------ 9. field facet mirror (R10 hero)
def _arc_facet(mb, c, u, v, n, Ra, wr, span, thick, seg=12):
    """One banana-shaped facet: an annulus sector (arc radius Ra, radial width wr, angle span) of thickness thick,
    centred on c, arc bulging toward +v, front face toward +n."""
    V = mb.bm.verts.new
    rows = []
    for dz in (-thick / 2, thick / 2):
        ring = []
        for r in (Ra - wr / 2, Ra + wr / 2):
            ring.append([V(c + u * (r * math.sin(t)) + v * (r * math.cos(t) - Ra) + n * dz)
                         for t in [(-span / 2 + span * i / seg) for i in range(seg + 1)]])
        rows.append(ring)
    (bi, bo), (ti, to) = rows
    F = mb.bm.faces.new
    for i in range(seg):
        F((ti[i], to[i], to[i + 1], ti[i + 1]))                 # front
        F((bi[i + 1], bo[i + 1], bo[i], bi[i]))                 # back
        F((bo[i], bo[i + 1], to[i + 1], to[i]))                 # outer edge
        F((bi[i + 1], bi[i], ti[i], ti[i + 1]))                 # inner edge
    F((bi[0], bo[0], to[0], ti[0]))
    F((ti[-1], to[-1], bo[-1], bi[-1]))


def field_facet_mirror(P, c, n, width=0.8, height=0.56, cols=4, rows=11, seed=0, spot_mb=None, hexa=True):
    """EUV field facet mirror: a slightly concave carrier holding `cols` columns of `rows` long curved
    (banana-shaped) polished facets, each tilted a little differently; machined carrier frame; hexapod behind."""
    rnd = random.Random(seed)
    c, n = Vector(c), Vector(n).normalized()
    u, v, _ = _basis(n)
    cw = width / cols
    rh = height / rows
    Ra = cw * 1.6
    span = 2 * math.asin(min(0.99, cw * 0.46 / Ra))
    for j in range(cols):
        xo = (j - (cols - 1) / 2) * cw
        bow = -n * (xo * xo) * 0.35                                         # concave carrier
        cc = c + u * xo + bow
        ncol = (n - u * xo * 0.7).normalized()                             # each column faces the centre a bit
        uc = v.cross(ncol).normalized()
        P["alu"].box(cc - ncol * 0.035, (cw * 0.97, height * 1.04, 0.05), rot=_rot(uc, v, ncol))   # column block
        for i in range(rows):
            yo = (i - (rows - 1) / 2) * rh
            tilt_u = rnd.uniform(-0.05, 0.05)
            tilt_v = rnd.uniform(-0.05, 0.05)
            nf = (ncol + uc * tilt_u + v * tilt_v).normalized()
            uf = v.cross(nf).normalized()
            vf = nf.cross(uf).normalized()
            fc = cc + v * yo - ncol * 0.004
            _arc_facet(P["coat"], fc, uf, vf, nf, Ra, rh * 0.84, span, 0.012)
            _arc_facet(P["subs"], fc - nf * 0.012, uf, vf, nf, Ra, rh * 0.88, span * 1.02, 0.014)
            if spot_mb is not None and abs(yo) < height * 0.36 and (i + j) % 3:
                _arc_facet(spot_mb, fc + nf * 0.0075, uf, vf, nf, Ra, rh * 0.6, span * 0.8, 0.001, seg=8)
    # carrier frame around the facet field + bolts
    fr = 0.03
    e = _rot(u, v, n)
    for sgn in (-1, 1):
        P["alu_dark"].box(c + v * sgn * (height / 2 + fr) - n * 0.03, (width + 2 * fr + 0.02, fr * 1.4, 0.07), rot=e)
        P["alu_dark"].box(c + u * sgn * (width / 2 + fr) - n * (0.03 + (width / 2) ** 2 * 0.35),
                          (fr * 1.4, height + 2 * fr, 0.07), rot=e)
        for k in range(6):
            P["steel"].cyl(c + v * sgn * (height / 2 + fr) + u * (-width / 2 + width * (k + 0.5) / 6) - n * 0.0,
                           0.006, 0.01, rot=e, seg=6)
    P["alu"].box(c - n * 0.11, (width * 0.9, height * 0.9, 0.04), rot=e)                      # back plate
    for sgn in (-1, 1):                                                                         # cooling in / out
        a = c - n * 0.11 + u * sgn * width * 0.4
        P["hose_b" if sgn < 0 else "hose_w"].path([a, a - n * 0.12, a - n * 0.2 + v * -height * 0.6], 0.012, seg=10)
    if hexa:
        hexapod(P, c - n * 0.5, c - n * 0.14, min(width, height) * 0.45, min(width, height) * 0.38)


# ------------------------------------------------------------------ 10. reflective EUV mask (R10 hero)
def _math(nt, op, a, b=None, v=None):
    m = nt.nodes.new("ShaderNodeMath")
    m.operation = op
    for i, x in enumerate((a, b)):
        if x is None:
            continue
        if isinstance(x, (int, float)):
            m.inputs[i].default_value = x
        else:
            nt.links.new(x, m.inputs[i])
    return m.outputs[0]


def mask_material(name="EUVMaskR10", fields=(3, 4), lines=70.0):
    """Reflective EUV reticle seen on its patterned face (Generated coords 0..1 over the plate): black absorber
    border, a fields[0] x fields[1] grid of die fields separated by dark streets, inside each die a dense
    absorber line / block layout on the bright Mo/Si multilayer; a faint violet sheen so the pattern reads in a dark
    machine."""
    m = K.mat(name, (0.72, 0.7, 0.82), metal=1.0, rough=0.08, coat=0.6)
    nt = m.node_tree
    b = K._bsdf(m)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sp = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Generated"], sp.inputs[0])
    x, y = sp.outputs["X"], sp.outputs["Y"]
    # border (absorber) outside [0.09, 0.91]
    def inside(c, lo, hi):
        return _math(nt, "MULTIPLY", _math(nt, "GREATER_THAN", c, lo), _math(nt, "LESS_THAN", c, hi))
    core = _math(nt, "MULTIPLY", inside(x, 0.09, 0.91), inside(y, 0.09, 0.91))
    # die fields + streets
    def field_coord(c, k):
        t = _math(nt, "DIVIDE", _math(nt, "SUBTRACT", c, 0.09), 0.82 / k)
        return _math(nt, "FRACT", t)
    fx, fy = field_coord(x, fields[0]), field_coord(y, fields[1])
    die = _math(nt, "MULTIPLY", inside(fx, 0.06, 0.94), inside(fy, 0.06, 0.94))
    # line / space pattern inside the die (alternating orientation per die half) + blocks
    wave = nt.nodes.new("ShaderNodeTexWave")
    wave.wave_type = "BANDS"
    wave.bands_direction = "X"
    wave.inputs["Scale"].default_value = lines
    wave.inputs["Distortion"].default_value = 0.0
    nt.links.new(tc.outputs["Generated"], wave.inputs["Vector"])
    ln = _math(nt, "GREATER_THAN", wave.outputs["Fac"], 0.5)
    vor = nt.nodes.new("ShaderNodeTexVoronoi")
    vor.inputs["Scale"].default_value = 28.0
    nt.links.new(tc.outputs["Generated"], vor.inputs["Vector"])
    blk = _math(nt, "GREATER_THAN", vor.outputs["Distance"], 0.42)       # pad / block islands
    pat = _math(nt, "MAXIMUM", ln, blk)                                   # 1 = reflective, 0 = absorber
    refl = _math(nt, "MULTIPLY", _math(nt, "MULTIPLY", core, die), pat)
    mc = nt.nodes.new("ShaderNodeMix")
    mc.data_type = "RGBA"
    mc.inputs["A"].default_value = (*K.lin((0.06, 0.06, 0.075)), 1)     # absorber
    mc.inputs["B"].default_value = (*K.lin((0.8, 0.76, 0.92)), 1)        # multilayer
    nt.links.new(refl, mc.inputs["Factor"])
    nt.links.new(mc.outputs["Result"], b.inputs["Base Color"])
    rr = nt.nodes.new("ShaderNodeMapRange")
    rr.inputs["To Min"].default_value = 0.45
    rr.inputs["To Max"].default_value = 0.06
    nt.links.new(refl, rr.inputs["Value"])
    nt.links.new(rr.outputs["Result"], b.inputs["Roughness"])
    mt = nt.nodes.new("ShaderNodeMapRange")
    mt.inputs["To Min"].default_value = 0.2
    mt.inputs["To Max"].default_value = 1.0
    nt.links.new(refl, mt.inputs["Value"])
    nt.links.new(mt.outputs["Result"], b.inputs["Metallic"])
    b.inputs["Emission Color"].default_value = (*K.lin(K.VIOLET), 1)
    nt.links.new(_math(nt, "MULTIPLY", refl, 0.35), b.inputs["Emission Strength"])
    return m


def reticle(P, c, size=0.6, face=(0, 0, -1), clamps=True, slit_mb=None, slit=(0.8, 0.12)):
    """Reflective mask plate (patterned face toward `face`) in a chuck with four clamps and fiducial marks; the
    patterned plate goes into P["mask"] as its own object so Generated coords span the plate. slit_mb gets the
    violet illuminated slit footprint (slit = fractions of size)."""
    c, f = Vector(c), Vector(face).normalized()
    u, v, _ = _basis(f, (0, 1, 0))
    e = _rot(u, v, f)
    t = size * 0.05
    P["mask"].box(c - f * t / 2, (size, size, t), rot=e)
    P["subs"].box(c - f * (t + 0.004), (size * 1.0, size * 1.0, 0.008), rot=e)
    # chuck behind the mask, clamp frame around the edge
    P["ceramic"].box(c - f * (t + size * 0.08), (size * 1.15, size * 1.15, size * 0.14), rot=e)
    if clamps:
        for su in (-1, 1):
            for sv in (-1, 1):
                p = c + u * su * size * 0.5 + v * sv * size * 0.38 - f * t * 0.3
                P["steel"].box(p, (size * 0.1, size * 0.14, t * 1.6), rot=e)
                P["alu_dark"].box(p + f * t * 0.5 - u * su * size * 0.02, (size * 0.05, size * 0.08, t * 0.6), rot=e)
    # fiducial / alignment marks just outside the pattern (crosses)
    for su in (-1, 1):
        for sv in (-1, 1):
            p = c + u * su * size * 0.455 + v * sv * size * 0.455 + f * 0.0012
            P["label"].box(p, (size * 0.05, size * 0.008, 0.001), rot=e)
            P["label"].box(p, (size * 0.008, size * 0.05, 0.001), rot=e)
    if slit_mb is not None:
        slit_mb.box(c + f * 0.003, (size * slit[0], size * slit[1], 0.002), rot=e)
    return c


# ------------------------------------------------------------------ 11. obscured (centre-hole) mirror (R10 hero, M5 / M6)
def annular_mirror(P, c, n, r, hole_r, spot_mb=None, spot=(0.45, 0.92), hexa=True, thick=None):
    """High-NA M5 / M6 style mirror: thick solid mirror with a central hole the beam passes through. Coated face
    ring, body ring, machined cell with flexure tabs, bore liner, 3-point hexapod mount offset outside the hole."""
    c, n = Vector(c), Vector(n).normalized()
    u, v, _ = _basis(n)
    th = thick or r * 0.28
    _ring(P["coat"], c - n * 0.004, n, r * 0.985, hole_r, 0.008, seg=96)
    _ring(P["subs"], c - n * (th / 2 + 0.008), n, r, hole_r, th, seg=96)
    _ring(P["steel"], c - n * (th / 2 + 0.008), n, hole_r + 0.006, hole_r, th * 1.04, seg=48)   # bore liner
    _ring(P["alu"], c - n * (th / 2 + 0.008), n, r * 1.12, r * 1.0, th * 1.2, seg=96)            # cell
    _bolt_circle(P, c - n * 0.0 + n * th * 0.05, n, r * 1.06, 24, r * 0.016, r * 0.014, nuts=False)
    for i in range(3):
        a = math.radians(90 + 120 * i)
        d = u * math.cos(a) + v * math.sin(a)
        P["alu_dark"].box(c - n * th * 0.5 + d * r * 1.17, (r * 0.16, r * 0.16, th * 1.3), rot=_rot(u, v, n))
    if spot_mb is not None:
        _ring(spot_mb, c + n * 0.002, n, r * spot[1], max(hole_r * 1.05, r * spot[0]), 0.002, seg=72)
    if hexa:
        back = c - n * (th + 0.03)
        for i in range(3):                                            # three bipod legs from the cell to a base ring
            a = math.radians(90 + 120 * i)
            d = u * math.cos(a) + v * math.sin(a)
            for sgn in (-1, 1):
                a2 = a + sgn * math.radians(25)
                d2 = u * math.cos(a2) + v * math.sin(a2)
                top = back + d * r * 0.95
                bot = back - n * r * 0.45 + d2 * r * 1.05
                _cyl(P["anod"], top.lerp(bot, 0.6), (bot - top), r * 0.04, (bot - top).length * 0.55, seg=12)
                P["steel"].tube(top, top.lerp(bot, 0.33), r * 0.018, seg=8)
                P["steel"].sphere(top, r * 0.03, 10)
                P["steel"].sphere(bot, r * 0.03, 10)
        _ring(P["alu"], back - n * r * 0.45, n, r * 1.15, r * 0.85, r * 0.08, seg=64)
    return c
