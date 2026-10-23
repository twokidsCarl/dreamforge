"""Round 12 (P1): shared beam look (R11 review: "every violet beam is a constant-width noisy tube").

  * soft_mat     - no noise streaks, no emissive volume (both were the 32 spp grain): a transparent shell whose
                   emission and opacity fall off as (1 - facing)^p, so the axis is bright and the silhouette
                   fades to nothing (soft edge, reads as a lit cone of air rather than a solid rod).
  * columns      - drop-in for kit_r2.beam_columns: every leg between two mirrors pinches to a waist (an
                   intermediate focus), so the light visibly converges after one mirror and spreads onto the next;
                   legs that start / end at a focus stay simple cones. Landing spots go on every bounce point.
  * landing spot - three stacked, slightly lifted discs on the mirror plane (halo emission), a soft footprint
                   that tells where the light lands (k4A).

Round 13 (R12 review: "2B beams still read as constant-width tubes at 960x540"): waist 0.3 -> 0.12 of the smaller
end (an hourglass you can see at review size), a small glow bead at every waist / focus apex, landing spots 1.5x
wider and ~2x brighter. Shots importing this: r2_cutaway (A0_10 B5_01 C_03 B3_02 B8_03 B8_03M B7_06).

Round 14 (R13 review: waist glow beads read as "floating white dots / light turning in mid-air"; the waist was
the R13 knob, so R14 removes it instead of retuning it): no waists, no beads. Legs alternate opening / narrowing
between mirror landing spots (_sizes), the only highlights are the landing spots on mirrors; timed_path lights a
path leg by leg (current leg bright, earlier legs a dim ghost, later legs not yet lit) so no two bright beams cross.

Use: import beam_r12 as BR; BR.install(K, M) swaps kit_r2.beam_columns and the beam materials of a shot;
BR.flush(M) builds the landing spots collected so far (call once at the end of a build).
"""
import math

import bpy
from mathutils import Vector

SPOTS = []                 # (centre, normal, radius)
FOCI = []                  # R13 glow beads: R14 never fills or draws them (kept so old callers do not break)
CONV = [0.38]               # R14: narrow-end footprint / mirror radius on alternate mirrors
_ORIG = {}


def soft_mat(name, color, strength=2.2, alpha=0.75, power=1.6, invert=False):
    """invert=True: bright / opaque silhouette, clear centre (a see-through cone in front of a mirror)."""
    import kit_r2 as K
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        if n.type != "OUTPUT_MATERIAL":
            nt.nodes.remove(n)
    out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
    lw = nt.nodes.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.5
    inv = nt.nodes.new("ShaderNodeMath"); inv.operation = "SUBTRACT"
    inv.inputs[0].default_value = 1.0
    nt.links.new(lw.outputs["Facing"], inv.inputs[1])
    if invert:
        inv = lw
    pw = nt.nodes.new("ShaderNodeMath"); pw.operation = "POWER"
    pw.inputs[1].default_value = power
    nt.links.new(inv.outputs["Facing"] if invert else inv.outputs[0], pw.inputs[0])
    a = nt.nodes.new("ShaderNodeMath"); a.operation = "MULTIPLY"
    a.inputs[1].default_value = alpha
    nt.links.new(pw.outputs[0], a.inputs[0])
    s = nt.nodes.new("ShaderNodeMath"); s.operation = "MULTIPLY"
    s.inputs[1].default_value = strength
    nt.links.new(pw.outputs[0], s.inputs[0])
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*K.lin(color), 1)
    nt.links.new(s.outputs[0], em.inputs["Strength"])
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mx = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(a.outputs[0], mx.inputs["Fac"])
    nt.links.new(tr.outputs[0], mx.inputs[1])
    nt.links.new(em.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs["Surface"])
    return m


def _side(mb, m, r1, r2, L, seg):
    """R14: an open cone wall (no end caps - a cap seen at an angle read as a flat disc floating on the beam)."""
    V = mb.bm.verts.new
    a = [V(m @ Vector((r1 * math.cos(2 * math.pi * i / seg), r1 * math.sin(2 * math.pi * i / seg), -L / 2))) for i in range(seg)]
    b = [V(m @ Vector((r2 * math.cos(2 * math.pi * i / seg), r2 * math.sin(2 * math.pi * i / seg), L / 2))) for i in range(seg)]
    for i in range(seg):
        j = (i + 1) % seg
        f = mb.bm.faces.new((a[i], a[j], b[j], b[i]))
        f.smooth = True


def _sizes(radii, conv=None):
    """R14: beam width at every point. Interior mirrors alternate wide / narrow, so each leg visibly opens up
    or narrows down between two landing spots (a cone, never a constant-width ribbon and never an hourglass waist
    in mid-air). The end points keep their given radius (a focus stays thin)."""
    conv = CONV[0] if conv is None else conv
    s = [max(r, 0.004) for r in radii]
    if len(s) < 3:
        return s
    wide = s[0] < 0.06                       # starting at a focus -> the first mirror carries the wide footprint
    for j in range(1, len(s) - 1):
        s[j] = s[j] if wide else s[j] * conv
        wide = not wide
    return s


def columns(mb, pts, radii, seg=40, spots=True, waist=None):
    """R14: tapered soft cones between landing spots (drop-in for kit_r2.beam_columns). `waist` is accepted for
    compatibility and ignored: R13's mid-air waists + glow beads read as "floating white dots" and are gone."""
    import kit_r2 as K
    pts = [Vector(p) for p in pts]
    s = _sizes(radii)
    for (a, b), (ra, rb) in zip(zip(pts, pts[1:]), zip(s, s[1:])):
        m, L = K._orient(a, b)
        if L > 1e-4:
            _side(mb, m, ra, rb, L, seg)
    if spots:
        for j in range(1, len(pts) - 1):
            n = K.mirror_normal(pts[j - 1], pts[j], pts[j + 1])
            SPOTS.append((pts[j], n, max(0.03, s[j] * 1.35)))


def _anim_mul(mat, keys):
    """Key the alpha / strength multipliers of a soft_mat by a factor: keys = [(frame, factor)]."""
    mul = [nd for nd in mat.node_tree.nodes if nd.type == "MATH" and nd.operation == "MULTIPLY"]
    hi = [nd.inputs[1].default_value for nd in mul]
    for f, k in keys:
        for nd, h_ in zip(mul, hi):
            nd.inputs[1].default_value = h_ * k
            nd.inputs[1].keyframe_insert("default_value", frame=f)


def timed_path(pts, radii, sched, n, name="TimedBeam", strength=2.2, alpha=0.75, dim=0.14, seg=40, ramp=6, no_spot=()):
    """R14 (R13: "two beams cross in mid-air; 4-5 violet segments per screen"): one object per leg, lit in story
    order. sched[i] = (t_on, t_dim) as fractions of the shot: hidden before t_on, bright from t_on, dimmed to a
    ghost (dim) after t_dim (None = stays bright). The landing spot at the end of a leg appears with the leg."""
    import kit_r2 as K
    pts = [Vector(p) for p in pts]
    s = _sizes(radii)
    objs = []
    for i, ((a, b), (ra, rb)) in enumerate(zip(zip(pts, pts[1:]), zip(s, s[1:]))):
        t_on, t_dim = sched[i]
        mb = K.MB()
        m, L = K._orient(a, b)
        _side(mb, m, ra, rb, L, seg)
        mat = soft_mat(f"{name}Mat{i}", K.VIOLET, strength, alpha)
        ob = mb.obj(f"{name}{i}", mat)
        f_on = max(1, round(1 + (n - 1) * t_on))
        keys = [(1, 0.0 if f_on > 1 else 1.0)]
        if f_on > 1:
            keys += [(f_on, 0.0), (f_on + ramp, 1.0)]
        if t_dim is not None:
            f_d = round(1 + (n - 1) * t_dim)
            keys += [(f_d, 1.0), (f_d + ramp, dim)]
        _anim_mul(mat, keys)
        objs.append(ob)
        if i + 1 < len(pts) - 1 and i not in no_spot:              # landing spot where this leg lands
            nrm = K.mirror_normal(pts[i], pts[i + 1], pts[i + 2])
            sm = K.MB()
            q = Vector((0, 0, 1)).rotation_difference(nrm)
            for k, f in enumerate((1.0, 0.62, 0.32)):
                sm.cyl(pts[i + 1] + nrm * (0.006 + 0.002 * k), max(0.03, rb * 1.35) * f, 0.001, rot=q.to_euler(), seg=40)
            so = sm.obj(f"{name}Spot{i}", K.emit_mat(f"{name}SpotMat{i}", (0.82, 0.72, 1.0), 7.5, halo=0.5))
            if f_on > 1:
                so.hide_render = True
                so.keyframe_insert("hide_render", frame=1)
                so.keyframe_insert("hide_render", frame=f_on + ramp // 2 - 1)
                so.hide_render = False
                so.keyframe_insert("hide_render", frame=f_on + ramp // 2)
    return objs


def install(K, M, strength=2.2, alpha=0.75):
    """Swap the shot's beam helpers / materials to the R12 look (this Blender process only)."""
    if "cols" not in _ORIG:
        _ORIG["cols"] = K.beam_columns
    K.beam_columns = columns
    M["beam_wide"] = soft_mat("EUVSoft", K.VIOLET, strength, alpha)
    M["cone"] = soft_mat("EUVSoftCone", K.VIOLET, strength * 0.8, alpha * 0.85)
    SPOTS.clear()
    FOCI.clear()


def flush(M=None, name="LandingSpots"):
    import kit_r2 as K
    FOCI.clear()                              # R14: no glow beads anywhere
    if not SPOTS:
        return None
    mb = K.MB()
    for c, n, r in SPOTS:
        q = Vector((0, 0, 1)).rotation_difference(n)
        for k, f in enumerate((1.0, 0.62, 0.32)):
            mb.cyl(c + n * (0.006 + 0.002 * k), r * f, 0.001, rot=q.to_euler(), seg=40)
    SPOTS.clear()
    return mb.obj(name, K.emit_mat("LandingSpotR13", (0.82, 0.72, 1.0), 7.5, halo=0.5))
