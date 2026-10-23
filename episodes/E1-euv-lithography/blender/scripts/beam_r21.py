"""Round 21 (P1, R21_ROOT_CAUSE row 3, r2_cutaway, owned by the cut-beam sub-agent): copy of beam_r20 (beam_r20 is
not edited). R21 change: end caps become FLAT landing spots on the mirror face (no volume inside the bowl).
alias() makes every later `import beam_r19` AND `import beam_r20` of this Blender process load this module.

--- beam_r20 docstring follows ---
Round 20 (P1, R20_ROOT_CAUSE rows 1 + 2, r2_cutaway): copy of beam_r19 (beam_r19 itself is not edited) with the
MIRROR-TO-MIRROR TOPOLOGY rule. R19 review: "M5->M6 的光画成了弯曲的 S 形半透明体，读成『光在空中拐弯』" (B7_06),
"投影箱里的紫光…读起来接近交叉…每个拐点都落在看得见的镜面上" (A0_10), B5_01 "看不到从分面镜反射出去的那一束".

  * a light segment is defined ONLY by two landing points: mirror A landing -> mirror B landing (or a source / IF
    tip -> mirror). It is one straight frustum; no curve / spline / sweep between mirrors. segment() is the one entry.
  * each end cap lies IN its mirror's plane (the ring is projected along the beam axis onto the plane through the
    landing point with the mirror normal), so the volume stops exactly on the mirror face - it never pokes through
    the mirror / cell (the clipped wide end is what bent the R19 M5->M6 cone into an "S").
  * turns only happen at a landing: columns() / timed_path() put a landing highlight on every interior point and
    the path's end (beam_r19), and NEW a bright tip at the path's START when it starts at a focus (IF / source).
  * beam width / density knobs (DENS / ABS) are unchanged - not a width or fog retune (R20 not-repeating list).

alias() makes every `import beam_r19` of the calling Blender process load this module (r2_cutaway R20_SHOTS only).

--- beam_r19 docstring follows ---
Round 19 (P1, R19_ROOT_CAUSE row 2 "2B mirrors matte plastic + cones spread into chamber fog"): copy of beam_r18
(beam_r18 itself is not edited) with the CONTINUITY rule for the cones:

  * zero outside the cone - the 1.55x outer halo shell (the volume that spread past the cone silhouette and filled
    the bay with violet haze, R18 p2 "55-85 % frames: violet spreads into a fog filling the chamber") is no longer
    built: volume density exists ONLY inside the landing-to-landing frustum
  * ends land exactly on the landing spots - unchanged geometry: each frustum runs from the previous mirror's landing
    point to the next mirror's landing point (end radii = the two apertures, NO width parameter touched)
  * a landing highlight at every bounce AND at the final end point of a path (mask band / slit / wafer point)

Beam width / density knobs (DENS / ABS) are identical to beam_r18 - no retune.

--- beam_r18 docstring follows ---
Round 18 (P1, R18_ROOT_CAUSE row 2: "2B beams read as lines / tubes on all three previous routes - R14
alternating widths, R16 beam_r16 taper / end fade, R17 beam_r17 thin core -> 'thin lines / laser lines /
equal-width tubes'").

Asset change, not a knob change (beam_r12 / beam_r16 / beam_r17 are not edited and none of their width knobs is
used): every mirror -> mirror segment is a k4A-style SOLID VOLUMETRIC LIGHT CONE

  * geometry  - a closed frustum whose two end radii are the two mirrors' effective apertures (the path radii:
                wide on a big mirror, a few mm at a focus / slit), so a segment visibly leaves one mirror wide
                and converges onto the next (or the reverse) - never a constant-width tube; the end at a slit can
                be an ellipse (a wedge closing onto a line)
  * interior  - homogeneous emission + violet-tinted absorption VOLUME (no surface shader): the light fills the
                cone like lit air; the line integral through a round volume is brightest on the axis and falls to
                zero at the silhouette, so there is no hard outline
  * soft edge - a second, wider and much fainter volume shell around the core (separate object, so the two
                volumes add) - the edge fades out instead of stopping
  * landing   - beam_r17's landing highlight on every mirror (imported, unchanged)
  * one path  - timed legs fade fully out (dim 0) once the next leg is lit: one current segment per screen

install() swaps beam_r12.columns / beam_r12.timed_path / kit_r2.beam_columns in this Blender process only
(called from r2_cutaway.build after beam_r16 / beam_r17).
"""
import math

import bpy
import bmesh
from mathutils import Vector

import beam_r12 as BR

VIOLET_E = (0.56, 0.4, 1.0)     # emission colour (sRGB)
VIOLET_T = (0.7, 0.55, 1.0)     # transmitted tint of the absorption (white studio reads a violet body)
DENS = [7.0]                    # emission per metre of chord, normalised by the segment's mean aperture
ABS = [1.2]                     # absorption density (same normalisation)
HALO = [1.55, 0.16]             # soft shell: radius factor, density factor
OBJS = []                       # every object built since the last take() (callers parent them)
_ORIG = {}
END_LAND = [True]                # R19: landing highlight on the last point of a path
START_LAND = [True]              # R20: bright tip where a path starts at a focus (IF / source), radius <= TIP_R
TIP_R = 0.04


def vol_mat(name, dens, absorb, halo=False):
    """Volume-only material (no surface): Emission + Absorption. Both densities pass through MULTIPLY math nodes
    so beam_r12._anim_mul can key the segment on / off."""
    import kit_r2 as K
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        if n.type != "OUTPUT_MATERIAL":
            nt.nodes.remove(n)
    out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*K.lin(VIOLET_E), 1)
    me = nt.nodes.new("ShaderNodeMath"); me.operation = "MULTIPLY"
    me.inputs[0].default_value = 1.0
    me.inputs[1].default_value = dens
    nt.links.new(me.outputs[0], em.inputs["Strength"])
    ab = nt.nodes.new("ShaderNodeVolumeAbsorption")
    ab.inputs["Color"].default_value = (*K.lin(VIOLET_T), 1)
    ma = nt.nodes.new("ShaderNodeMath"); ma.operation = "MULTIPLY"
    ma.inputs[0].default_value = 1.0
    ma.inputs[1].default_value = absorb
    nt.links.new(ma.outputs[0], ab.inputs["Density"])
    add = nt.nodes.new("ShaderNodeAddShader")
    nt.links.new(em.outputs[0], add.inputs[0])
    nt.links.new(ab.outputs[0], add.inputs[1])
    nt.links.new(add.outputs[0], out.inputs["Volume"])
    try:
        m.cycles.homogeneous_volume = True
    except AttributeError:
        pass
    return m


def _onplane(ring, c, nrm, d, r, L=1.0):
    """R20: slide each ring vertex along the beam axis d onto the mirror plane (point c, normal nrm), so the cap
    lies on the mirror face. Grazing planes (|d.n| < 0.35) are left perpendicular; the slide is capped at
    min(1.5 r, 0.3 L) so the two caps never cross (no folded / self-cancelling volume)."""
    if nrm is None:
        return
    n_ = Vector(nrm).normalized()
    dn = d.dot(n_)
    if abs(dn) < 0.35:
        return
    for v in ring:
        t = (Vector(c) - v.co).dot(n_) / dn
        cap = min(1.5 * r, 0.3 * L)
        t = max(-cap, min(cap, t))
        v.co = v.co + d * t


FLAT = [True]                   # R21: caps stop in FRONT of the mirror plane + a flat landing spot on the face
GAP = [0.012]                   # clearance between the end ring and the mirror plane (concave sag of the bowl)
SPOT = [(0.8, 0.68, 1.0), 5.0, 1.6, 0.4]   # landing spot: colour, core strength, outer strength, outer alpha


def _pullback(d, nrm, r, L):
    """R21: distance to pull a perpendicular end ring back along the axis so that the WHOLE ring stays in front of
    the mirror plane (no volume on / behind the mirror face, nothing drawn inside the bowl)."""
    if nrm is None:
        return 0.0
    c = abs(d.dot(Vector(nrm).normalized()))
    if c < 0.2:
        return min(GAP[0], 0.3 * L)
    return min(r * math.sqrt(max(0.0, 1 - c * c)) / c + GAP[0], 0.35 * L)


def _spot_mat(name, strength, alpha):
    import kit_r2 as K
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        if n.type != "OUTPUT_MATERIAL":
            nt.nodes.remove(n)
    out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*K.lin(SPOT[0]), 1)
    me = nt.nodes.new("ShaderNodeMath"); me.operation = "MULTIPLY"
    me.inputs[0].default_value = 1.0
    me.inputs[1].default_value = strength
    nt.links.new(me.outputs[0], em.inputs["Strength"])
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mx = nt.nodes.new("ShaderNodeMixShader")
    ma = nt.nodes.new("ShaderNodeMath"); ma.operation = "MULTIPLY"      # alpha also fades with the segment
    ma.inputs[0].default_value = 1.0
    ma.inputs[1].default_value = alpha
    nt.links.new(ma.outputs[0], mx.inputs["Fac"])
    nt.links.new(tr.outputs[0], mx.inputs[1])
    nt.links.new(em.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs["Surface"])
    try:
        m.blend_method = "BLEND"
    except Exception:
        pass
    return m


def flat_spot(c, d, nrm, r, name):
    """R21: a flat elliptical landing spot lying ON the mirror face at c (normal nrm): the footprint of a beam of
    radius r arriving along d (semi-axes r and r/|d.n|, capped at 2.2 r), lifted 3 mm off the face. Two layers
    (bright core 0.55 + soft outer 1.0). Returns ([objects], [materials])."""
    n_ = Vector(nrm).normalized()
    if n_.dot(d) > 0:
        n_ = -n_
    c_ = max(abs(d.dot(n_)), 0.2)
    u = d - n_ * d.dot(n_)
    if u.length < 1e-6:
        u = n_.orthogonal()
    u.normalize()
    v = n_.cross(u).normalized()
    a_u, a_v = min(r / c_, 2.2 * r), r
    objs, mats = [], []
    for k, (f, st, al) in enumerate(((1.0, SPOT[2], SPOT[3]), (0.55, SPOT[1], 1.0))):
        bm = bmesh.new()
        o = Vector(c) + n_ * (0.003 + 0.001 * k)
        cen = bm.verts.new(o)
        ring = [bm.verts.new(o + u * a_u * f * math.cos(2 * math.pi * i / 48) + v * a_v * f * math.sin(2 * math.pi * i / 48))
                for i in range(48)]
        for i in range(48):
            bm.faces.new((cen, ring[i], ring[(i + 1) % 48]))
        m = _spot_mat(f"{name}SpotMat{k}", st, al)
        objs.append(_obj(bm, f"{name}Spot{k}", m))
        mats.append(m)
    return objs, mats


def _frustum(a, b, ra, rb, seg=48, end=None, na=None, nb=None):
    """Closed frustum a -> b. end = (ax, ha, ay, hy): the b ring is an ellipse (wedge onto a slit line).
    R20: na / nb = mirror normals at the two landings - the end rings are laid onto those mirror planes."""
    import kit_r2 as K
    a, b = Vector(a), Vector(b)
    m, L = K._orient(a, b)
    bm = bmesh.new()
    rings = []
    if end is not None:                 # start ring on the same (ax, ay) basis as the end ellipse: no twisted wall
        dd = (b - a).normalized()
        u = Vector(end[0]) - dd * Vector(end[0]).dot(dd)
        u.normalize()
        v = dd.cross(u)
        if v.dot(Vector(end[2])) < 0:
            v = -v
        ring = [bm.verts.new(a + (u * math.cos(2 * math.pi * i / seg) + v * math.sin(2 * math.pi * i / seg)) * ra)
                for i in range(seg)]
        rings.append(ring)
    for z, r, e in (((-L / 2, ra, None),) if end is None else ()) + ((L / 2, rb, end),):
        ring = []
        for i in range(seg):
            t = 2 * math.pi * i / seg
            if e is not None:
                ax, ha, ay, hy = e
                p = b + Vector(ax) * ha * math.cos(t) + Vector(ay) * hy * math.sin(t)
            else:
                p = m @ Vector((r * math.cos(t), r * math.sin(t), z))
            ring.append(bm.verts.new(p))
        rings.append(ring)
    A, Bv = rings
    dd_ = (b - a).normalized()
    if FLAT[0]:                         # R21: rings stay perpendicular, pulled back in front of the mirror planes
        L_ = (b - a).length
        sa = _pullback(dd_, na, ra, L_)
        sb = _pullback(dd_, nb, rb, L_) if end is None else 0.0
        for v_ in A:
            rel = v_.co - a
            v_.co = a + dd_ * sa + rel * ((ra + (rb - ra) * sa / L_) / max(ra, 1e-6))
        for v_ in (Bv if end is None else ()):
            rel = v_.co - b
            v_.co = b - dd_ * sb + rel * ((rb - (rb - ra) * sb / L_) / max(rb, 1e-6))
    else:
        _onplane(A, a, na, dd_, ra, (b - a).length)
        if end is None:
            _onplane(Bv, b, nb, dd_, rb, (b - a).length)
    for i in range(seg):
        j = (i + 1) % seg
        bm.faces.new((A[i], A[j], Bv[j], Bv[i])).smooth = True
    bm.faces.new(A[::-1])
    bm.faces.new(Bv)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    return bm


def _obj(bm, name, mat):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    ob.data.materials.append(mat)
    try:
        ob.visible_shadow = False
        if FLAT[0]:                     # R21: the cones / spots are not mirrored by the concave mirror faces (the
            ob.visible_glossy = False   # bowl reflection of the cone is the curved violet mass inside M5, R20 smoke)
    except AttributeError:
        pass
    OBJS.append(ob)
    return ob


def cone(a, b, ra, rb, name="ConeR19", k=1.0, end=None, seg=48, na=None, nb=None):
    """One segment = core volume cone + soft outer shell. Returns ([objects], [materials])."""
    ra, rb = max(ra, 0.002), max(rb, 0.002)
    mean = 0.5 * (ra + rb) if end is None else 0.5 * (ra + 0.5 * (end[1] + end[3]))
    d = DENS[0] * k * 0.06 / max(mean, 0.01)
    ab = ABS[0] * k * 0.06 / max(mean, 0.01)
    m1 = vol_mat(name + "Mat", d, ab)
    m2 = vol_mat(name + "HaloMat", d * HALO[1], ab * HALO[1] * 0.5)
    o1 = _obj(_frustum(a, b, ra, rb, seg, end, na, nb), name, m1)
    bpy.data.materials.remove(m2)          # R19: no outer shell - zero volume outside the cone
    objs, mats = [o1], [m1]
    if FLAT[0]:                            # R21: flat landing spot on each mirror face the segment touches
        dd_ = (Vector(b) - Vector(a)).normalized()
        if na is not None:
            o_, m_ = flat_spot(a, dd_, na, ra, name + "A")
            objs += o_; mats += m_
        if nb is not None and end is None:
            o_, m_ = flat_spot(b, dd_, nb, rb, name + "B")
            objs += o_; mats += m_
    return objs, mats


def segment(a, b, ra, rb, name="SegR20", k=1.0, na=None, nb=None, seg=48):
    """R20: the ONE way to draw light: a straight cone from landing a (on mirror normal na, or a focus tip when na
    is None) to landing b (mirror normal nb). Returns ([objects], [materials])."""
    return cone(a, b, ra, rb, name, k=k, seg=seg, na=na, nb=nb)


def tip(c, d, name="TipR20", f_on=1, ramp=6, scale=0.6):
    """R20: bright focus tip (IF / source point) where a path starts - the cone visibly opens from a point."""
    return _land_timed(c, d, name, f_on, ramp, scale=scale)


def take():
    out = OBJS[:]
    OBJS.clear()
    return out


def key_vis(objs, mats, n, t_on=0.0, t_off=None, ramp=6, dim=0.0):
    """Fade a segment in at t_on and (one current segment per screen) out to dim after t_off."""
    f_on = max(1, round(1 + (n - 1) * t_on))
    keys = [(1, 0.0 if f_on > 1 else 1.0)]
    if f_on > 1:
        keys += [(f_on, 0.0), (f_on + ramp, 1.0)]
    if t_off is not None:
        f_d = round(1 + (n - 1) * t_off)
        keys += [(f_d, 1.0), (f_d + ramp, dim)]
    for m in mats:
        BR._anim_mul(m, keys)
    return f_on


def _land_timed(c, nrm, name, f_on, ramp=6, f_off=None, scale=1.0):
    import beam_r17 as R17
    objs = R17._land_objs(Vector(c), Vector(nrm).normalized(), scale, name)
    for so in objs:
        if f_on > 1:
            so.hide_render = True
            so.keyframe_insert("hide_render", frame=1)
            so.keyframe_insert("hide_render", frame=f_on + ramp // 2 - 1)
            so.hide_render = False
            so.keyframe_insert("hide_render", frame=f_on + ramp // 2)
        if f_off is not None:
            so.hide_render = False
            so.keyframe_insert("hide_render", frame=f_off)
            so.hide_render = True
            so.keyframe_insert("hide_render", frame=f_off + 1)
    return objs


def columns(mb, pts, radii, seg=48, spots=True, waist=None):
    """Drop-in for kit_r2.beam_columns: one volumetric cone per segment, end radii = the apertures in radii.
    mb is left empty (the cones are their own volume objects - collected in OBJS)."""
    import kit_r2 as K
    import beam_r16 as R16
    import beam_r17 as R17
    pts = [Vector(p) for p in pts]
    end, R16.END_SHAPE[0] = R16.END_SHAPE[0], None
    nseg = len(pts) - 1
    nrm = [None] + [K.mirror_normal(pts[j - 1], pts[j], pts[j + 1]) for j in range(1, len(pts) - 1)] + [None]
    for i, (a, b) in enumerate(zip(pts, pts[1:])):
        cone(a, b, radii[i], radii[i + 1], f"VCone{len(OBJS)}", end=end if i == nseg - 1 else None, seg=seg,
             na=nrm[i], nb=nrm[i + 1])
    if spots and START_LAND[0] and len(pts) > 1 and radii[0] <= TIP_R:    # R20: the path opens from a lit tip
        R17.landing(pts[0], (pts[1] - pts[0]).normalized(), 0.6)
    if spots:
        for j in range(1, len(pts) - 1):
            R17.landing(pts[j], K.mirror_normal(pts[j - 1], pts[j], pts[j + 1]))
        if END_LAND[0] and len(pts) > 1:      # R19: the path's last point gets its landing highlight too
            R17.landing(pts[-1], (pts[-2] - pts[-1]).normalized(), 0.8)


def timed_path(pts, radii, sched, n, name="TimedBeam", dim=0.0, ramp=6, no_spot=(), k=1.0, **kw):
    """beam_r12.timed_path as volumetric cones: hidden before t_on, lit from t_on, faded OUT after t_dim
    (dim 0: earlier segments disappear, the current one carries the screen). Landing highlights with their leg."""
    import kit_r2 as K
    pts = [Vector(p) for p in pts]
    objs = []
    for i, (a, b) in enumerate(zip(pts, pts[1:])):
        t_on, t_dim = sched[i]
        na_ = K.mirror_normal(pts[i - 1], pts[i], pts[i + 1]) if i > 0 else None
        nb_ = K.mirror_normal(pts[i], pts[i + 1], pts[i + 2]) if i + 2 < len(pts) else None
        os_, ms_ = cone(a, b, radii[i], radii[i + 1], f"{name}{i}", k=k, na=na_, nb=nb_)
        f_on = key_vis(os_, ms_, n, t_on, t_dim, ramp, dim)
        objs += os_
        if i == 0 and START_LAND[0] and radii[0] <= TIP_R:         # R20: lit focus tip where the path starts
            objs += tip(a, (b - a).normalized(), f"{name}Tip", f_on, ramp)
        if i + 1 < len(pts) - 1 and i not in no_spot:
            nrm = K.mirror_normal(pts[i], pts[i + 1], pts[i + 2])
            _land_timed(pts[i + 1], nrm, f"{name}Land{i}", f_on, ramp)
        elif i + 1 == len(pts) - 1 and END_LAND[0]:          # R19: landing at the path's end point
            objs += _land_timed(pts[i + 1], (a - b).normalized(), f"{name}LandEnd", f_on, ramp, scale=0.8)
    return objs


def alias():
    """R21: every later `import beam_r19` / `import beam_r20` in this Blender process gets beam_r21."""
    import sys
    sys.modules["beam_r19"] = sys.modules[__name__]
    sys.modules["beam_r20"] = sys.modules[__name__]


def install():
    import kit_r2 as K
    if "cols" in _ORIG:
        return
    _ORIG["cols"] = BR.columns
    BR.columns = columns
    BR.timed_path = timed_path
    K.beam_columns = columns
    OBJS.clear()
