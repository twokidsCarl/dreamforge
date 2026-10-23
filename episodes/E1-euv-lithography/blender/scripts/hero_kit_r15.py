"""Round 15 (P1) cutaway kit additions (R15_ROOT_CAUSE rows 1 + 2). No changes to hero_kit_r10-12.

  disc_mirror      thick aspheric mirror blank (R14 B7_06: M5 / M6 read as "chrome donuts" = torus): a lathed solid
                   with a polished, slightly concave optical face (own mesh -> mirror_r15.ml_mirror), a 45 deg
                   chamfer, a fine-ground cylindrical side, flat back and a bored centre hole (all -> ground_edge).
  three_point_mount three flexure pads gripping the blank's side at 120 deg, each on a bipod to a machined cell ring
                   with bolt circle; the cell ring hangs off a hexapod (hero_kit_r10.hexapod).
  SpotFilter       wraps a landing-spot mesh builder so the field-facet mirror only marks the facets inside the lit
                   footprint (R14 B5_01: every facet carried an emissive spot -> "self-lit LED panel").
"""
import math

from mathutils import Matrix, Vector

import hero_kit_r10 as H

_basis, _cyl, _ring, _rot = H._basis, H._cyl, H._ring, H._rot


def lathe(mb, c, n, prof, seg=96, smooth=True):
    """Revolve the (r, z) polyline prof around axis n through c (z along n) into mb."""
    c, n = Vector(c), Vector(n).normalized()
    u, v, _ = _basis(n)
    rows = []
    for r, z in prof:
        row = []
        for j in range(seg):
            a = 2 * math.pi * j / seg
            row.append(mb.bm.verts.new(c + n * z + (u * math.cos(a) + v * math.sin(a)) * r))
        rows.append(row)
    for i in range(len(rows) - 1):
        for j in range(seg):
            k = (j + 1) % seg
            f = mb.bm.faces.new((rows[i][j], rows[i][k], rows[i + 1][k], rows[i + 1][j]))
            f.smooth = smooth
    return rows


def disc_mirror(face_mb, edge_mb, c, n, r, hole_r, thick, sag=0.012, chamfer=0.03, seg=96):
    """c = centre of the optical face rim plane, n = face normal. Returns the centre of the back face."""
    rf = r - chamfer
    face = []
    for i in range(13):                                   # concave asphere: centre sits `sag` below the rim plane
        rr = hole_r + (rf - hole_r) * i / 12
        face.append((rr, -sag * (1 - (rr / rf) ** 2)))
    lathe(face_mb, c, n, face, seg)
    edge = [(rf, 0.0), (r, -chamfer), (r, -thick), (hole_r + 0.012, -thick), (hole_r, -thick + 0.012),
            (hole_r, -sag * (1 - (hole_r / rf) ** 2))]
    lathe(edge_mb, c, n, edge, seg)
    return Vector(c) - Vector(n).normalized() * thick


def three_point_mount(P, c, n, r, thick, phase=90.0):
    """Flexure pads at 120 deg on the blank's side (c = face centre, n = face normal), bipods down to a cell ring
    behind the mirror. Returns (cell centre, cell radius)."""
    c, n = Vector(c), Vector(n).normalized()
    u, v, _ = _basis(n)
    e = _rot(u, v, n)
    mid = c - n * thick * 0.55
    cell = c - n * (thick + r * 0.32)
    rc = r * 1.08
    _ring(P["anod"], cell, n, rc * 1.06, rc * 0.86, r * 0.07, seg=96)                       # machined cell ring
    H._bolt_circle(P, cell + n * r * 0.035, n, rc * 0.96, 18, r * 0.014, r * 0.012, nuts=False)
    for i in range(3):
        a = math.radians(phase + 120 * i)
        d = u * math.cos(a) + v * math.sin(a)
        t = d.cross(n).normalized()
        pad = mid + d * (r + 0.018)
        P["alu_dark"].box(pad, (0.03, 0.09, thick * 0.9), rot=e)                                   # flexure pad
        _cyl(P["steel"], pad + d * 0.02, d, 0.012, 0.03, seg=10)                                # clamp screw
        for s in (-1, 1):                                                                        # bipod
            top = pad - n * thick * 0.3
            bot = cell + d * rc * 0.95 + t * s * r * 0.16 + n * r * 0.035
            P["steel"].tube(top, bot, 0.009, seg=8)
            P["steel"].sphere(bot, 0.014, 8)
        P["label"].box(pad + d * 0.017 + n * thick * 0.25, (0.012, 0.03, 0.012), rot=e)       # sensor tag
    return cell, rc


def edge_sensors(P, c, n, r, k=4, phase=30.0, gap=0.05):
    """Capacitive edge sensors aiming at the mirror side (small heads on stalks, with leads)."""
    c, n = Vector(c), Vector(n).normalized()
    u, v, _ = _basis(n)
    for i in range(k):
        a = math.radians(phase + 360.0 * i / k)
        d = u * math.cos(a) + v * math.sin(a)
        head = c + d * (r + gap + 0.03)
        _cyl(P["brushed"], head, -d, 0.022, 0.05, seg=16)
        _cyl(P["glass"], head - d * 0.026, -d, 0.012, 0.004, seg=12)
        P["alu_dark"].tube(head + d * 0.025, head + d * 0.12, 0.008, seg=8)
        P["cable_k"].path([head + d * 0.12, head + d * 0.2 - n * 0.06, head + d * 0.26 - n * 0.18], 0.004, seg=6)


class SpotFilter:
    """Forward only spot boxes within `radius` of `centre` (the lit footprint) to the real spot builder."""

    def __init__(self, mb, centre, radius):
        self.mb, self.c, self.r = mb, Vector(centre), radius
        self.bm = mb.bm

    def box(self, c, s, rot=(0, 0, 0)):
        if (Vector(c) - self.c).length <= self.r:
            self.mb.box(c, s, rot=rot)

    def __getattr__(self, k):
        return getattr(self.mb, k)
