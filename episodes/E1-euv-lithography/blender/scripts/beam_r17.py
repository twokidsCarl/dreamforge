"""Round 17 (P1, R17_ROOT_CAUSE row 4: "the beam SHAPE was changed twice without being read - R14 alternating
cones, R16 beam_r16 taper + end fade - and at 960x540 it still reads as an equal-width tube / slab; the volumetric
haze hides the mirrors").

Route change, not a knob change: beam_r16's taper / end-fade parameters and beam_r12's waist / bead / cone radius
are NOT touched (both files unchanged on disk; r2_misc / r2_source keep importing them as before). Instead:

  * every mirror -> mirror leg is ONE THIN CORE (constant radius CORE[0], a few px at review size) - no wide cone
    wall, so the mirrors behind / around the path are no longer under a violet haze;
  * every bounce gets a BRIGHT LANDING HIGHLIGHT on the mirror: a small hot white-violet spot + a tight violet
    glow + a small violet point light that actually lights the mirror face around the spot ("one bright point on
    each mirror" is what tells where the light goes);
  * collector -> IF source cones and wide-shaft materials stay, but at a fraction of their opacity (haze()).

install() patches beam_r12 / kit_r2 in this Blender process only (called by r2_cutaway.build after beam_r16).
"""
import math

import bpy
from mathutils import Vector

import beam_r12 as BR

CORE = [0.016]              # core radius (m) for the next build; r2_cutaway sets it per variant
HOT = [1.0]                 # landing-spot size factor per variant
LAND = []                   # (centre, normal, scale)
_ORIG = {}


def core_mat(name, strength=7.0, alpha=0.95):
    """Thin-core look: beam_r12's soft shell (bright axis, soft silhouette) - at a few px wide it reads as a
    bright line of light, not as a tube."""
    return _ORIG["soft"](name, (0.62, 0.45, 1.0), strength, alpha, 0.9)


def core_leg(mb, a, b, air0=False, air1=False, r=None):
    """One thin core a -> b (beam_r16.leg with a constant radius: no taper, the light just ends softly in air)."""
    import beam_r16 as R16
    r = CORE[0] if r is None else r
    R16.leg(mb, a, b, r, r, seg=16, air0=air0, air1=air1)


def landing(c, n, scale=1.0):
    LAND.append((Vector(c), Vector(n).normalized(), scale))


def _land_objs(c, n, s, name, energy=14.0):
    import kit_r2 as K
    q = Vector((0, 0, 1)).rotation_difference(n)
    hot, glow = K.MB(), K.MB()
    r0 = 0.022 * s * HOT[0]
    hot.cyl(c + n * 0.007, r0, 0.0015, rot=q.to_euler(), seg=32)
    for k, f in enumerate((2.6, 1.7)):
        glow.cyl(c + n * (0.005 + 0.001 * k), r0 * f, 0.001, rot=q.to_euler(), seg=40)
    o1 = hot.obj(name + "Hot", K.emit_mat("LandHotR17", (0.96, 0.92, 1.0), 45.0))
    o2 = glow.obj(name + "Glow", K.emit_mat("LandGlowR17", (0.7, 0.55, 1.0), 9.0, halo=0.7))
    lt = K.point(name + "Lt", c + n * 0.09, energy * s * HOT[0], K.VIOLET, 0.03)
    try:
        lt.visible_glossy = False          # lights the mirror around the spot; no extra sparkle in polished parts
    except AttributeError:
        pass
    return [o1, o2] + ([lt] if lt is not None else [])


def columns(mb, pts, radii, seg=40, spots=True, waist=None):
    """Drop-in for kit_r2.beam_columns: thin cores between the points + a landing highlight on every interior
    point. radii is accepted for compatibility and ignored (it was the cone-width knob)."""
    import kit_r2 as K
    import beam_r16 as R16
    pts = [Vector(p) for p in pts]
    s = [max(r, 0.004) for r in radii]
    end, R16.END_SHAPE[0] = R16.END_SHAPE[0], None
    nseg = len(pts) - 1
    for i, (a, b) in enumerate(zip(pts, pts[1:])):
        last = i == nseg - 1
        core_leg(mb, a, b, air0=i == 0 and s[0] >= 0.04, air1=last and s[-1] >= 0.04 and end is None)
    if spots:
        for j in range(1, len(pts) - 1):
            landing(pts[j], K.mirror_normal(pts[j - 1], pts[j], pts[j + 1]))


def timed_path(pts, radii, sched, n, name="TimedBeam", strength=7.0, alpha=0.95, dim=0.14, seg=16, ramp=6,
               no_spot=()):
    """beam_r12.timed_path with thin cores and R17 landing highlights (timed with their leg)."""
    import kit_r2 as K
    pts = [Vector(p) for p in pts]
    s = [max(r, 0.004) for r in radii]
    k_ = len(pts) - 1
    objs = []
    for i, (a, b) in enumerate(zip(pts, pts[1:])):
        t_on, t_dim = sched[i]
        mb = K.MB()
        core_leg(mb, a, b, air0=i == 0 and s[0] >= 0.04, air1=i == k_ - 1 and s[-1] >= 0.04)
        mat = core_mat(f"{name}Mat{i}", strength, alpha)
        ob = mb.obj(f"{name}{i}", mat)
        f_on = max(1, round(1 + (n - 1) * t_on))
        keys = [(1, 0.0 if f_on > 1 else 1.0)]
        if f_on > 1:
            keys += [(f_on, 0.0), (f_on + ramp, 1.0)]
        if t_dim is not None:
            f_d = round(1 + (n - 1) * t_dim)
            keys += [(f_d, 1.0), (f_d + ramp, dim)]
        BR._anim_mul(mat, keys)
        objs.append(ob)
        if i + 1 < len(pts) - 1 and i not in no_spot:
            nrm = K.mirror_normal(pts[i], pts[i + 1], pts[i + 2])
            for so in _land_objs(pts[i + 1], nrm, 1.0, f"{name}Land{i}"):
                if f_on > 1:
                    so.hide_render = True
                    so.keyframe_insert("hide_render", frame=1)
                    so.keyframe_insert("hide_render", frame=f_on + ramp // 2 - 1)
                    so.hide_render = False
                    so.keyframe_insert("hide_render", frame=f_on + ramp // 2)
    return objs


def flush(M=None, name="LandingSpots"):
    """beam_r12.flush replacement: every collected bounce (beam_r12.SPOTS from callers + LAND) becomes an R17
    landing highlight. Returns a parent empty so callers can parent it (B7_06 turntable)."""
    BR.FOCI.clear()
    items = [(Vector(c), Vector(n).normalized(), 1.0) for c, n, r in BR.SPOTS] + LAND[:]
    BR.SPOTS.clear()
    LAND.clear()
    if not items:
        return None
    piv = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(piv)
    for i, (c, n, s) in enumerate(items):
        for o in _land_objs(c, n, s, f"{name}{i}"):
            o.parent = piv
    return piv


def haze(names, k=0.35):
    """Lower the opacity / emission of wide-volume beam objects (source cones, wide shafts) by k."""
    done = set()
    for nm in names:
        ob = bpy.data.objects.get(nm)
        if ob is None or ob.type != "MESH":
            continue
        for slot in ob.material_slots:
            m = slot.material
            if m is None or m.name in done or not m.use_nodes:
                continue
            done.add(m.name)
            for nd in m.node_tree.nodes:
                if nd.type == "MIX_SHADER":
                    sock = nd.inputs["Fac"]
                    if sock.is_linked:
                        src = sock.links[0].from_socket
                        mul = m.node_tree.nodes.new("ShaderNodeMath"); mul.operation = "MULTIPLY"
                        mul.inputs[1].default_value = k
                        m.node_tree.links.new(src, mul.inputs[0])
                        m.node_tree.links.new(mul.outputs[0], sock)
                    else:
                        sock.default_value *= k
                if nd.type == "EMISSION":
                    sock = nd.inputs["Strength"]
                    if sock.is_linked:
                        src = sock.links[0].from_socket
                        mul = m.node_tree.nodes.new("ShaderNodeMath"); mul.operation = "MULTIPLY"
                        mul.inputs[1].default_value = k
                        m.node_tree.links.new(src, mul.inputs[0])
                        m.node_tree.links.new(mul.outputs[0], sock)
                    else:
                        sock.default_value *= k
            out = next((nd for nd in m.node_tree.nodes if nd.type == "OUTPUT_MATERIAL"), None)
            if out is not None and out.inputs["Volume"].is_linked:       # beam_column_mat's emissive volume
                m.node_tree.links.remove(out.inputs["Volume"].links[0])


def _install_mats(K, M, strength=2.2, alpha=0.75):
    _ORIG["bri"](K, M, strength, alpha)
    M["beam_wide"] = core_mat("EUVCoreR17")


def install():
    import kit_r2 as K
    if "soft" in _ORIG:
        return
    _ORIG["soft"] = BR.soft_mat           # (beam_r16's UV-ramp wrapper when installed first - same look on cores)
    _ORIG["bri"] = BR.install
    BR.columns = columns
    BR.timed_path = timed_path
    BR.flush = flush
    BR.install = _install_mats
