"""Round 26 (P1, R26_ROOT_CAUSE row 2, owned by the MAIN process - agents import it, never edit it).

R25 review (all three lanes): beams still "等宽实心管 / 硬边"; R25 main-process Q4 rejected B5_01 / B8_03 / B2_08 for a NEW
negative read "扁平玻璃板 / 硬边楔形": the beam_r25 shell at its default edge 2.4 / core 0.08 / alpha 0.9 is bright only in
a thin band at the silhouette and empty inside, so a cone seen side-on = two hard straight lines enclosing a clear
sheet. The one R25 beam that read as a soft beam was B7_06 after chero's softening pass (edge 1.3, core 0.28,
alpha 0.45, mouths x1.35, cut_hero_r25_b706.chain24).

beam_r26 = beam_r25 with those softened values as DEFAULTS plus one structural change:
  * rim roll-off  - k = (Facing^edge * (1 - Facing)^rim / norm + core) * (1 - Facing)^rim, rim 1.5: at the exact
                    silhouette (Facing -> 1) shell AND core fade to 0, so the cone has no hard outline line (the "glass
                    panel edge"); the brightest band sits at ~0.82 of the radius and blends into a filled core (0.28).
                    Offline profile (r26smoke/sketch26/profile.txt): R25 default fill 0.21 / hardness 0.82, R25 B5_01
                    0.39 / 0.91, B7_06 soft 0.45 / 0.92, R26 0.69 / 0.12 (8-spp look: r26smoke/shtest/sbs/B5_01_0064.jpg).
  * widen         - every stop radius except the final landing x1.35 (B7_06 mouths), so narrow legs do not collapse
                    into "wire pairs" (R25 B7_06 first pass).
  * check()       - beam_r25.check + BEAMCHECK26 profile readout per leg: the across-the-cone opacity profile of this
                    shader (front + back shell) -> fill = mean / peak (a column ~1, a wire pair ~0.2) and hardness =
                    opacity in the outermost 4 % of the width / peak (a hard edge ~1). Soft beam = fill 0.45-0.85 and
                    hardness <= 0.5; outside = NOGO (flat panel / wire pair / hard wedge).
Not R18-R21 volume fog, not R16 end fade, not R17 thin core, not R24 inner cone, not R25 edge-2.4 thin shell.
Same call shapes as beam_r25 (chain / soft_cone / mirror_at / check / tapered / key_chain / landing).
"""
import math

import bpy
from mathutils import Vector

import beam_r25 as B25
import kit_r2 as K
import misc_beam_r18 as MB

VIOLET = K.VIOLET
EDGE, CORE, ALPHA, WIDEN, RIM_POW = 1.3, 0.28, 0.45, 1.35, 1.5
FILL_MIN, FILL_MAX, HARD_MAX = 0.45, 0.85, 0.5

TAPER = B25.TAPER
tapered = B25.tapered
mirror_at = B25.mirror_at
key_chain = B25.key_chain
landing = B25.landing
_proj = B25._proj
_rmax = B25._rmax


def shell_mat(name, color, strength, alpha=ALPHA, edge=EDGE, core=CORE, gain=1.2, narrow_at_end=True, rim_pow=RIM_POW):
    """k = (Facing^edge * (1-Facing)^rim / norm + core) * (1-Facing)^rim * (1 + gain * w); norm keeps the shell peak ~1."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    for n in list(N):
        if n.type != "OUTPUT_MATERIAL":
            N.remove(n)
    out = next(n for n in N if n.type == "OUTPUT_MATERIAL")
    op = MB._op
    lw = N.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.5
    f = lw.outputs["Facing"]               # 0 face-on (cone core), -> 1 at the silhouette
    shell = op(N, L, "POWER", f, edge)
    k = op(N, L, "ADD", shell, core)
    if rim_pow:
        roll = op(N, L, "POWER", op(N, L, "SUBTRACT", 1.0, f), rim_pow)
        shell = op(N, L, "MULTIPLY", op(N, L, "MULTIPLY", shell, roll), 1.0 / _peak(edge, rim_pow))
        k = op(N, L, "MULTIPLY", op(N, L, "ADD", shell, core), roll)
    uv = N.new("ShaderNodeUVMap")
    uv.uv_map = "ConeUV"
    sp = N.new("ShaderNodeSeparateXYZ")
    L.new(uv.outputs["UV"], sp.inputs[0])
    v = sp.outputs["Y"]
    w = v if narrow_at_end else op(N, L, "SUBTRACT", 1.0, v)
    if gain:
        k = op(N, L, "MULTIPLY", k, op(N, L, "ADD", 1.0, op(N, L, "MULTIPLY", w, gain)))
    em = N.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*K.lin(color), 1)
    L.new(op(N, L, "MULTIPLY", k, strength), em.inputs["Strength"])
    tr = N.new("ShaderNodeBsdfTransparent")
    mx = N.new("ShaderNodeMixShader")
    L.new(op(N, L, "MINIMUM", op(N, L, "MULTIPLY", k, alpha), 1.0), mx.inputs["Fac"])
    L.new(tr.outputs[0], mx.inputs[1])
    L.new(em.outputs[0], mx.inputs[2])
    L.new(mx.outputs[0], out.inputs["Surface"])
    m["r26_shell"] = (edge, core, alpha, rim_pow)
    return m


def _peak(edge, rim_pow):
    return max(x ** edge * (1 - x) ** rim_pow for x in (i / 400 for i in range(401))) if rim_pow else 1.0


def profile(edge=EDGE, core=CORE, alpha=ALPHA, rim_pow=RIM_POW, n=200):
    """Across-the-cone opacity of the shell (front + back surface, circular section, orthographic): returns
    (fill = mean/peak, hardness = mean opacity in the outer 4 % / peak, list of opacity samples 0..1 of radius)."""
    pk = _peak(edge, rim_pow)
    prof = []
    for i in range(n):
        u = (i + 0.5) / n                   # screen offset / radius
        fac = 1.0 - math.sqrt(max(0.0, 1.0 - u * u))
        roll = (1 - fac) ** rim_pow if rim_pow else 1.0
        a1 = min(1.0, (fac ** edge * roll / pk + core) * roll * alpha)
        prof.append(1 - (1 - a1) ** 2)      # two shell surfaces along the ray
    p = max(prof)
    outer = prof[int(n * 0.96):]
    return sum(prof) / len(prof) / p, sum(outer) / len(outer) / p, prof


def soft_cone(name, a, b, ra, rb, color=None, strength=4.0, alpha=ALPHA, edge=EDGE, core=CORE, gain=1.2, taper=TAPER,
              xdir=None, seg=48, rim_pow=RIM_POW, **_ignored):
    """beam_r25.soft_cone with the R26 soft shell (rim roll-off, filled core). Returns [obj]."""
    ra, rb = tapered(ra, rb, taper)
    me, _s = MB._cone_mesh(name, tuple(a), tuple(b), ra, rb, xdir, seg)
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    me.materials.append(shell_mat(name + "M", VIOLET if color is None else color, strength, alpha, edge, core, gain,
                                  narrow_at_end=_rmax(rb) <= _rmax(ra), rim_pow=rim_pow))
    MB._vis(ob)
    ob["r25_radii"] = (float(_rmax(ra)), float(_rmax(rb)))
    ob["r26_profile"] = (edge, core, alpha, rim_pow)
    return [ob]


def chain(name, stops, radii, color=None, strength=4.0, alpha=ALPHA, edge=EDGE, core=CORE, gain=1.2, widen=WIDEN,
          rim_pow=RIM_POW, **kw):
    """beam_r25.chain (taper, turn mirrors, landings) with R26 soft-shell legs; radii (all but the final landing) x widen."""
    radii = [B25._scale(r, widen) for r in radii[:-1]] + [radii[-1]]
    orig = B25.soft_cone
    B25.soft_cone = lambda *a, **k: soft_cone(*a, rim_pow=rim_pow, **k)
    try:
        ch = B25.chain(name, stops, radii, color=color, strength=strength, alpha=alpha, edge=edge, core=core, gain=gain,
                       **kw)
    finally:
        B25.soft_cone = orig
    ch["r26"] = dict(edge=edge, core=core, alpha=alpha, rim_pow=rim_pow, widen=widen)
    return ch


def check(sc, ch, frames, exits=(), tag="", cam=None, mirror_stops=None):
    """beam_r25.check + BEAMCHECK26 profile readout (fill / hardness) per leg from the legs' own shader values."""
    bad = B25.check(sc, ch, frames, exits=exits, tag=tag, cam=cam, mirror_stops=mirror_stops)
    extra = []
    for i, leg in enumerate(ch["legs"]):
        ob = leg[0] if isinstance(leg, (list, tuple)) else leg
        prm = ob.get("r26_profile") if ob is not None else None
        if prm is None:
            extra.append(f"leg{i} not an R26 soft shell (beam_r25 / r24 cone)")
            continue
        fill, hard, _p = profile(*prm)
        ok = FILL_MIN <= fill <= FILL_MAX and hard <= HARD_MAX
        print(f"BEAMCHECK26 {tag} leg{i} fill {fill:.2f} hardness {hard:.2f} (edge {prm[0]} core {prm[1]} alpha {prm[2]} "
              f"rim {prm[3]}) {'soft' if ok else 'NOT SOFT'}", flush=True)
        if not ok:
            extra.append(f"leg{i} fill {fill:.2f} / hardness {hard:.2f} outside soft range "
                         f"({FILL_MIN}-{FILL_MAX}, <= {HARD_MAX}): flat panel / wire pair / hard wedge")
    for b_ in extra:
        print(f"BEAMCHECK26 {tag} NOGO {b_}", flush=True)
    bad = bad + extra
    print(f"BEAMCHECK26 {tag} {'OK' if not bad else 'NOGO ' + str(len(bad))}", flush=True)
    return bad
