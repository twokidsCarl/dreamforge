"""Round 16 (P1, R16_ROOT_CAUSE row 3: "beams read as equal-width solid tubes without landing spots").

Not repeating: beam_r12's waist / glow bead / cone-radius knobs are untouched (R13 -> "floating white dots").
This module changes only the beam SHAPE TOPOLOGY and its brightness along the length:

  * every leg is a subdivided open cone wall (10 rings) carrying a per-ring brightness g in UV.x (stored as 1 - g,
    so geometry without UVs keeps full strength):  g = density * end fade
      density  - the light concentrates as the cone narrows: the narrow end is bright, the wide end dim, so a
                 leg visibly spreads out of a focus / is gathered onto the next mirror (no constant-width tube)
      end fade - an end that stops in air fades to nothing over 35 % of the leg (no elliptical rim / end cap);
                 an end on a mirror fades over the last 8 % into that mirror's landing spot
  * END_SHAPE: the last leg of a path can end on a line (B8_03: the exposure light narrows onto the slit)
  * cone_beam (collector -> IF) gets the same treatment; COLL_FADE dims its wide base over the collector face
    (B3_02 row 4: the mirror must not sit under violet haze)

install() patches beam_r12 / kit_r2 in this Blender process only (r2_cutaway); r2_misc never imports this file,
and beam_r12.soft_mat itself is unchanged on disk.
"""
import math

from mathutils import Vector

import beam_r12 as BR

FADE_AIR = 0.35
FADE_MIRROR = 0.08
END_SHAPE = [None]          # (axis_a, half_a, axis_b, half_b) for the final ring of the next path
COLL_FADE = [None]          # (floor, span) for cone_beam's wide base
_ORIG = {}


def _smooth(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def _g(t, r, rmin, rmax, air0, air1, lo0=None, span0=None):
    q = 0.0 if rmax - rmin < 1e-6 else (r - rmin) / (rmax - rmin)
    dens = 1.0 - 0.62 * q
    s0 = span0 if span0 is not None else (FADE_AIR if air0 else FADE_MIRROR)
    l0 = lo0 if lo0 is not None else (0.0 if air0 else 0.35)
    s1, l1 = (FADE_AIR, 0.0) if air1 else (FADE_MIRROR, 0.35)
    f0 = l0 + (1 - l0) * _smooth(t / s0)
    f1 = l1 + (1 - l1) * _smooth((1 - t) / s1)
    return dens * f0 * f1


def leg(mb, a, b, ra, rb, seg=40, nl=10, air0=False, air1=False, end=None, lo0=None, span0=None):
    """Open cone wall a -> b (radius ra -> rb) with the R16 brightness ramp in UV.x. end = (ax, ha, ay, hy): the
    final ring is an ellipse b + ax*ha*cos + ay*hy*sin (a line-shaped landing)."""
    import kit_r2 as K
    a, b = Vector(a), Vector(b)
    m, L = K._orient(a, b)
    if L < 1e-4:
        return
    bm = mb.bm
    uv = bm.loops.layers.uv.verify()
    rmin, rmax = min(ra, rb), max(ra, rb)
    rings, gs = [], []
    for k in range(nl + 1):
        t = k / nl
        r = ra + (rb - ra) * t
        ring = []
        for i in range(seg):
            ang = 2 * math.pi * i / seg
            p0 = m @ Vector((r * math.cos(ang), r * math.sin(ang), -L / 2 + L * t))
            if end is not None:
                ax, ha, ay, hy = end
                pe = b + Vector(ax) * ha * math.cos(ang) + Vector(ay) * hy * math.sin(ang)
                pr = m @ Vector((rb * math.cos(ang), rb * math.sin(ang), L / 2))
                p0 = p0 + (pe - pr) * (t ** 1.5)
            ring.append(bm.verts.new(p0))
        rings.append(ring)
        gs.append(_g(t, r, rmin, rmax, air0, air1, lo0, span0))
    for k in range(nl):
        for i in range(seg):
            j = (i + 1) % seg
            f = bm.faces.new((rings[k][i], rings[k][j], rings[k + 1][j], rings[k + 1][i]))
            f.smooth = True
            for lp, kk in zip(f.loops, (k, k, k + 1, k + 1)):
                lp[uv].uv = (1.0 - gs[kk], 0.0)


def _air(s, idx):
    return s[idx] >= 0.04


def columns(mb, pts, radii, seg=40, spots=True, waist=None):
    """beam_r12.columns with R16 legs (same radii via beam_r12._sizes, same landing spots)."""
    import kit_r2 as K
    pts = [Vector(p) for p in pts]
    s = BR._sizes(radii)
    nseg = len(pts) - 1
    end, END_SHAPE[0] = END_SHAPE[0], None
    for i, ((a, b), (ra, rb)) in enumerate(zip(zip(pts, pts[1:]), zip(s, s[1:]))):
        last = i == nseg - 1
        leg(mb, a, b, ra, rb, seg, air0=i == 0 and _air(s, 0), air1=last and _air(s, -1) and end is None,
            end=end if last else None)
    if spots:
        for j in range(1, len(pts) - 1):
            n = K.mirror_normal(pts[j - 1], pts[j], pts[j + 1])
            BR.SPOTS.append((pts[j], n, max(0.03, s[j] * 1.35)))


def _side16(mb, m, r1, r2, L, seg):
    """Fallback for beam_r12.timed_path's _side calls: rebuild the leg from its matrix."""
    a = m @ Vector((0, 0, -L / 2))
    b = m @ Vector((0, 0, L / 2))
    ctx = _SIDE_CTX.pop(0) if _SIDE_CTX else (False, False)
    leg(mb, a, b, r1, r2, seg, air0=ctx[0], air1=ctx[1])


_SIDE_CTX = []


def timed_path(pts, radii, sched, n, name="TimedBeam", **kw):
    s = BR._sizes(radii)
    k = len(pts) - 1
    _SIDE_CTX[:] = [(i == 0 and _air(s, 0), i == k - 1 and _air(s, -1)) for i in range(k)]
    try:
        return _ORIG["timed"](pts, radii, sched, n, name, **kw)
    finally:
        _SIDE_CTX[:] = []


def soft_mat(name, color, strength=2.2, alpha=0.75, power=1.6, invert=False):
    """beam_r12.soft_mat x (1 - UV.x): the R16 ramp; geometry without UVs renders exactly as before."""
    m = _ORIG["soft"](name, color, strength, alpha, power, invert)
    nt = m.node_tree
    mix = next(nd for nd in nt.nodes if nd.type == "MIX_SHADER")
    em = next(nd for nd in nt.nodes if nd.type == "EMISSION")
    uvn = nt.nodes.new("ShaderNodeUVMap")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(uvn.outputs["UV"], sep.inputs[0])
    one = nt.nodes.new("ShaderNodeMath"); one.operation = "SUBTRACT"
    one.inputs[0].default_value = 1.0
    nt.links.new(sep.outputs[0], one.inputs[1])
    for sock in (mix.inputs["Fac"], em.inputs["Strength"]):
        src = sock.links[0].from_socket
        mul = nt.nodes.new("ShaderNodeMath"); mul.operation = "MULTIPLY"
        nt.links.new(src, mul.inputs[0])
        nt.links.new(one.outputs[0], mul.inputs[1])
        nt.links.new(mul.outputs[0], sock)
    return m


def cone_beam(mbhalo, apex, base_c, base_r, seg=48):
    """kit_r2.cone_beam as an R16 leg: wide base on the collector (dimmed by COLL_FADE), apex at the focus."""
    lo, span = COLL_FADE[0] if COLL_FADE[0] else (0.35, FADE_MIRROR)
    leg(mbhalo, base_c, apex, base_r, 0.002, seg, lo0=lo, span0=span)


def install():
    import kit_r2 as K
    if "soft" in _ORIG:
        return
    _ORIG["soft"] = BR.soft_mat
    _ORIG["timed"] = BR.timed_path
    BR.soft_mat = soft_mat
    BR.columns = columns
    BR._side = _side16
    BR.timed_path = timed_path
    K.cone_beam = cone_beam
