"""Round 18 (P1, R18_ROOT_CAUSE row 2: "2B beams read as lines / tubes on all three previous routes - R14
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


def _frustum(a, b, ra, rb, seg=48, end=None):
    """Closed frustum a -> b. end = (ax, ha, ay, hy): the b ring is an ellipse (wedge onto a slit line)."""
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
    except AttributeError:
        pass
    OBJS.append(ob)
    return ob


def cone(a, b, ra, rb, name="ConeR18", k=1.0, end=None, seg=48):
    """One segment = core volume cone + soft outer shell. Returns ([objects], [materials])."""
    ra, rb = max(ra, 0.002), max(rb, 0.002)
    mean = 0.5 * (ra + rb) if end is None else 0.5 * (ra + 0.5 * (end[1] + end[3]))
    d = DENS[0] * k * 0.06 / max(mean, 0.01)
    ab = ABS[0] * k * 0.06 / max(mean, 0.01)
    m1 = vol_mat(name + "Mat", d, ab)
    m2 = vol_mat(name + "HaloMat", d * HALO[1], ab * HALO[1] * 0.5)
    o1 = _obj(_frustum(a, b, ra, rb, seg, end), name, m1)
    hend = None if end is None else (end[0], end[1] * HALO[0], end[2], end[3] * 1.08)
    o2 = _obj(_frustum(a, b, ra * HALO[0], rb * HALO[0], seg, hend), name + "Halo", m2)
    return [o1, o2], [m1, m2]


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
    objs = R17._land_objs(Vector(c), nrm, scale, name)
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
    for i, (a, b) in enumerate(zip(pts, pts[1:])):
        cone(a, b, radii[i], radii[i + 1], f"VCone{len(OBJS)}", end=end if i == nseg - 1 else None, seg=seg)
    if spots:
        for j in range(1, len(pts) - 1):
            R17.landing(pts[j], K.mirror_normal(pts[j - 1], pts[j], pts[j + 1]))


def timed_path(pts, radii, sched, n, name="TimedBeam", dim=0.0, ramp=6, no_spot=(), k=1.0, **kw):
    """beam_r12.timed_path as volumetric cones: hidden before t_on, lit from t_on, faded OUT after t_dim
    (dim 0: earlier segments disappear, the current one carries the screen). Landing highlights with their leg."""
    import kit_r2 as K
    pts = [Vector(p) for p in pts]
    objs = []
    for i, (a, b) in enumerate(zip(pts, pts[1:])):
        t_on, t_dim = sched[i]
        os_, ms_ = cone(a, b, radii[i], radii[i + 1], f"{name}{i}", k=k)
        f_on = key_vis(os_, ms_, n, t_on, t_dim, ramp, dim)
        objs += os_
        if i + 1 < len(pts) - 1 and i not in no_spot:
            nrm = K.mirror_normal(pts[i], pts[i + 1], pts[i + 2])
            _land_timed(pts[i + 1], nrm, f"{name}Land{i}", f_on, ramp)
    return objs


def install():
    import kit_r2 as K
    if "cols" in _ORIG:
        return
    _ORIG["cols"] = BR.columns
    BR.columns = columns
    BR.timed_path = timed_path
    K.beam_columns = columns
    OBJS.clear()
