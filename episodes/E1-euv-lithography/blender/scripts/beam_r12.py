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

Use: import beam_r12 as BR; BR.install(K, M) swaps kit_r2.beam_columns and the beam materials of a shot;
BR.flush(M) builds the landing spots collected so far (call once at the end of a build).
"""
import math

import bpy
from mathutils import Vector

SPOTS = []                 # (centre, normal, radius)
FOCI = []                  # R13: (centre, radius) glow beads at waists / focus apexes
WAIST = [0.12]              # waist radius / smaller end radius
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


def columns(mb, pts, radii, seg=40, spots=True, waist=True):
    """Tapered legs with a waist between two mirror-sized ends; landing spots on the interior points."""
    import kit_r2 as K
    pts = [Vector(p) for p in pts]
    for i, ((a, b), (ra, rb)) in enumerate(zip(zip(pts, pts[1:]), zip(radii, radii[1:]))):
        L = (b - a).length
        if L < 1e-4:
            continue
        ra, rb = max(ra, 0.004), max(rb, 0.004)
        if waist and min(ra, rb) > 0.045 and L > 0.5:                   # mirror -> mirror: converge to a focus, spread again
            t = ra / (ra + rb)
            w = Vector(a.lerp(b, t))
            rw = max(0.006, WAIST[0] * min(ra, rb))
            for p, q, r1, r2 in ((a, w, ra, rw), (w, b, rw, rb)):
                m, l_ = K._orient(p, q)
                mb.cyl_m(m, r1, l_, seg=seg, r2=r2)
            FOCI.append((w, max(0.012, rw * 1.1)))
        else:
            if waist and min(ra, rb) <= 0.045 and max(ra, rb) > 0.1:     # R13: a cone out of / into a focus (IF)
                FOCI.append((a if ra < rb else b, max(0.012, min(ra, rb) * 1.0)))
            m, l_ = K._orient(a, b)
            mb.cyl_m(m, ra, L, seg=seg, r2=rb)
    if spots:
        for j in range(1, len(pts) - 1):
            n = K.mirror_normal(pts[j - 1], pts[j], pts[j + 1])
            SPOTS.append((pts[j], n, max(0.03, radii[j] * 1.55)))   # R13: 1.05 -> 1.55


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
    if FOCI:                                  # R13: glow beads where the light pinches
        fb = K.MB()
        for c, r in FOCI:
            fb.sphere(c, r, 16)
        FOCI.clear()
        fb.obj(name + "Foci", K.emit_mat("BeamFocusR13", (0.86, 0.78, 1.0), 6.0, halo=0.85))
    if not SPOTS:
        return None
    mb = K.MB()
    for c, n, r in SPOTS:
        q = Vector((0, 0, 1)).rotation_difference(n)
        for k, f in enumerate((1.0, 0.62, 0.32)):
            mb.cyl(c + n * (0.006 + 0.002 * k), r * f, 0.001, rot=q.to_euler(), seg=40)
    SPOTS.clear()
    return mb.obj(name, K.emit_mat("LandingSpotR13", (0.82, 0.72, 1.0), 7.5, halo=0.5))
