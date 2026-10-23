"""Round 16 (P1) helpers for blender/shots/r2_misc.py (R16_ROOT_CAUSE #3 / #5). Never used by the photons
variant (B9_05 gold control).

  #3  fade_cone / fade_beam_mat: light as an uncapped soft-edged cone whose ENDS FADE OUT along its length (UV v),
      so a beam converges onto / opens out of a landing spot instead of ending as an equal-width solid tube;
      columns_factory_r16: drop-in for K.beam_columns in the A2_03 / A2_08 machine backdrop (each leg one fading
      cone, a soft brighter core shell inside, every turn lands on a mirror with a spot).
  #5  parts_wall_r16: B8_17 service wall of >= 10 nameable part types (no repeated panel grid), built at 1:1 machine
      scale and scaled into the shot.
"""
import math
import random

import bmesh
import bpy
from mathutils import Vector

import kit_r2 as K


# ------------------------------------------------------------------ #3 beams
def fade_beam_mat(name, color=None, strength=2.2, alpha=0.7, power=1.4, fade0=0.1, fade1=0.1):
    """Soft-edged emission (bright on the axis, clear at the silhouette) x end fades along UV v (FadeUV):
    v in [0, fade0] ramps 0 -> 1, v in [1 - fade1, 1] ramps 1 -> 0. fade = 0 keeps that end hard (on a spot)."""
    color = K.VIOLET if color is None else color
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    N, L = nt.nodes, nt.links
    for n in list(N):
        if n.type != "OUTPUT_MATERIAL":
            N.remove(n)
    out = next(n for n in N if n.type == "OUTPUT_MATERIAL")

    def op(o, a=None, b=None):
        x = N.new("ShaderNodeMath")
        x.operation = o
        for i, s in enumerate((a, b)):
            if s is None:
                continue
            if isinstance(s, (int, float)):
                x.inputs[i].default_value = s
            else:
                L.new(s, x.inputs[i])
        return x.outputs[0]

    lw = N.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.5
    edge = op("POWER", op("MAXIMUM", op("SUBTRACT", 1.0, lw.outputs["Facing"]), 0.0), power)   # no pow(<0) NaN specks
    uv = N.new("ShaderNodeUVMap")
    uv.uv_map = "FadeUV"
    sp = N.new("ShaderNodeSeparateXYZ")
    L.new(uv.outputs["UV"], sp.inputs[0])
    v = sp.outputs["Y"]
    f = None
    for (lo, hi, a_, b_) in ((0.0, max(fade0, 1e-4), 0.0, 1.0), (1.0 - max(fade1, 1e-4), 1.0, 1.0, 0.0)):
        if (a_ == 0.0 and fade0 <= 0) or (a_ == 1.0 and fade1 <= 0):
            continue
        mr = N.new("ShaderNodeMapRange")
        mr.interpolation_type = "SMOOTHSTEP"
        mr.clamp = True
        mr.inputs["From Min"].default_value = lo
        mr.inputs["From Max"].default_value = hi
        mr.inputs["To Min"].default_value = a_
        mr.inputs["To Max"].default_value = b_
        L.new(v, mr.inputs["Value"])
        f = mr.outputs["Result"] if f is None else op("MULTIPLY", f, mr.outputs["Result"])
    k = edge if f is None else op("MULTIPLY", edge, f)
    em = N.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*K.lin(color), 1)
    L.new(op("MULTIPLY", k, strength), em.inputs["Strength"])
    tr = N.new("ShaderNodeBsdfTransparent")
    mx = N.new("ShaderNodeMixShader")
    L.new(op("MULTIPLY", k, alpha), mx.inputs["Fac"])
    L.new(tr.outputs[0], mx.inputs[1])
    L.new(em.outputs[0], mx.inputs[2])
    L.new(mx.outputs[0], out.inputs["Surface"])
    return m


def _cone_into(bm, uvl, a, b, ra, rb, seg, stations):
    m, Ln = K._orient(a, b)
    if Ln < 1e-6:
        return
    rings = []
    for v in stations:
        r = ra + (rb - ra) * v
        z = -Ln / 2 + Ln * v
        rings.append([bm.verts.new(m @ Vector((r * math.cos(2 * math.pi * i / seg), r * math.sin(2 * math.pi * i / seg), z)))
                      for i in range(seg)])
    for k in range(len(stations) - 1):
        p, q = rings[k], rings[k + 1]
        for i in range(seg):
            j = (i + 1) % seg
            f = bm.faces.new((p[i], p[j], q[j], q[i]))
            f.smooth = True
            for lp, (uu, vv) in zip(f.loops, ((i / seg, stations[k]), ((i + 1) / seg, stations[k]),
                                               ((i + 1) / seg, stations[k + 1]), (i / seg, stations[k + 1]))):
                lp[uvl].uv = (uu, vv)


def fade_cone(name, a, b, ra, rb, mat, seg=48, stations=None, core=0.5):
    """Open cone a -> b (no end caps), UV v = 0 at a .. 1 at b; plus a thinner inner shell (core x radius) with
    the same material, which gives the beam a soft brighter centre instead of a hollow tube silhouette."""
    if stations is None:
        stations = [k / 16 for k in range(17)]
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("FadeUV")
    a, b = Vector(a), Vector(b)
    _cone_into(bm, uvl, a, b, ra, rb, seg, stations)
    if core:
        _cone_into(bm, uvl, a, b, ra * core, rb * core, max(16, seg // 2), stations)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    me.materials.append(mat)
    ob.visible_shadow = False
    return ob


def columns_factory_r16(spots, keep=None, mat=None, tag="BeamR16"):
    """Drop-in for K.beam_columns inside build_cutaway_r2.machine (A2_03 / A2_08 backdrop only). The R14 legs were
    open cones too, but each one ended flat at full brightness on both mirrors -> 'equal-width neon tubes'.
    R16: each leg is its own fading cone - it leaves a mirror narrow (out of the previous landing spot), opens,
    and is caught wide by the next mirror; the brightness fades in / out over the last stretch before each
    mirror so the light reads as landing in the spot; path ends (source side / wafer side) fade out long."""
    built = []

    def cols(mb, pts, radii, seg=40):
        pts = [Vector(p) for p in pts]
        s = [max(r, 0.004) for r in radii]
        wide = True
        for j in range(1, len(s) - 1):
            s[j] = s[j] if wide else s[j] * 0.15      # R16: the narrow end is the landing spot itself (a focus)
            wide = not wide
        lo, hi = keep if keep else (0, len(pts) - 1)
        mats = {}
        for i, ((a, b), (ra, rb)) in enumerate(zip(zip(pts, pts[1:]), zip(s, s[1:]))):
            if not (lo <= i < hi):
                continue
            f0 = 0.35 if i == lo else (0.18 if ra > rb else 0.04)     # wide end fades gently onto its mirror
            f1 = 0.35 if i == hi - 1 else (0.18 if rb > ra else 0.04)
            key = (f0, f1)
            if key not in mats:
                mats[key] = fade_beam_mat(f"{tag}M{len(mats)}", K.VIOLET, mat[0], mat[1], 1.4, f0, f1)
            built.append(fade_cone(f"{tag}_{i}", a, b, ra, rb, mats[key], seg=seg, core=0))
        for j in range(max(1, lo), min(len(pts) - 1, hi + 1)):
            spots.append((pts[j], K.mirror_normal(pts[j - 1], pts[j], pts[j + 1]), max(0.03, s[j] * 1.3)))
    return cols, built


def spot_ring(mb, p, nrm, r, w=0.12):
    """Thin flat annulus (a soft ring) lying on a surface at p - used where many routes converge on one node."""
    q = Vector((0, 0, 1)).rotation_difference(Vector(nrm).normalized())
    mb.ring(Vector(p), r, r * (1 - w), 0.0008, rot=q.to_euler(), seg=64)


# ------------------------------------------------------------------ #5 B8_17 parts wall
def parts_wall_r16(M, loc, scale, seed=16):
    """Service wall at 1:1 machine scale (x -2.2..2.2, z 0..1.8, front face y = 0, parts toward -Y), every block a
    different nameable part: cable tray, card cage, turbo pump, gate valve, bellows, CF viewport, vacuum gauges,
    pneumatic valve island, ion pump, power supply with louvres, drag chain, linear axis + encoder, coolant manifold,
    coolant hose bundle, cable harness. All objects parented to an empty at loc / scale."""
    import parts_kit_r8 as PK
    import hero_kit_r10 as HK
    rnd = random.Random(seed)
    P, H = PK.new_parts(), HK.new_parts()
    yb = 0.0
    P["paint_grey"].box((0, yb + 0.01, 0.9), (4.6, 0.02, 1.9))                      # dark back plate
    PK.cable_tray(P, -2.1, 2.1, 1.72, yb, seed=seed)                                # 1 cable tray
    PK.card_cage(P, -2.15, -1.4, 1.2, 1.62, yb, seed=seed)                          # 2 card cage
    PK.cf_flange(P, Vector((-0.85, yb - 0.02, 1.22)), Vector((0, -1, 0)), 0.17)
    PK.turbo_pump(P, (-0.85, yb, 1.22), r=0.15)                                     # 3 turbo pump
    P["steel"].tube((-0.62, -0.16, 0.86), (-0.15, -0.16, 0.86), 0.06, seg=24)
    PK.gate_valve(P, Vector((-0.38, -0.16, 0.86)), r=0.07)                          # 4 gate valve
    PK.bellows(P, Vector((-0.15, -0.16, 0.86)), Vector((0.32, -0.16, 0.86)), 0.075)  # 5 bellows
    HK.flange_viewport(H, (0.55, yb, 1.28), r=0.12)                                 # 6 CF viewport
    for k in range(3):                                                              # 7 vacuum gauges
        PK.gauge(P, (0.85 + 0.13 * k, yb, 1.45), r=0.04)
    HK.valve_island(H, (1.45, yb, 1.32), nval=8, s=1.0, drop=0.3)                  # 8 valve island
    ipc = Vector((1.98, yb - 0.09, 0.98))                                           # 9 ion pump: body + fins + magnets
    P["anod"].box(ipc, (0.28, 0.18, 0.34))
    for k in range(6):
        P["alu_dark"].box(ipc + Vector((-0.12 + 0.048 * k, -0.1, 0)), (0.012, 0.05, 0.32))
    for sx in (-1, 1):
        P["steel"].box(ipc + Vector((sx * 0.16, 0, 0)), (0.04, 0.16, 0.26))
    P["steel"].tube(ipc + Vector((0, 0, 0.17)), ipc + Vector((0, 0, 0.3)), 0.04, seg=16)
    psc = Vector((-1.75, yb - 0.14, 0.8))                                          # 10 power supply, louvres
    P["alu_dark"].box(psc, (0.7, 0.28, 0.66))
    for k in range(9):
        P["anod"].box(psc + Vector((0, -0.145, -0.24 + 0.06 * k)), (0.5, 0.012, 0.022))
    P["led_c"].box(psc + Vector((0.28, -0.147, 0.27)), (0.02, 0.004, 0.02))
    P["screen"].box(psc + Vector((0.2, -0.147, 0.18)), (0.12, 0.004, 0.05))
    PK.drag_chain(P, Vector((-1.25, -0.08, 0.12)), 1.3, R=0.09, w=0.08)            # 11 drag chain
    PK.linear_axis(P, -1.25, 0.3, 0.62, yb)                                         # 12 linear axis + encoder
    PK.manifold(P, 0.5, 1.5, 0.6, yb)                                              # 13 coolant manifold
    HK.cooling_bundle(H, [(0.45, -0.06, 0.78), (1.5, -0.06, 0.78), (1.75, -0.06, 0.6), (1.75, -0.06, 0.1)],
                      k=4, r=0.014)                                                 # 14 coolant hoses
    HK.cable_harness(H, [(-1.3, -0.05, 1.62), (-0.4, -0.06, 1.58), (0.2, -0.05, 1.62), (0.9, -0.08, 1.15)],
                     n=6, r=0.008)                                                  # 15 cable harness
    root = bpy.data.objects.new("PartsWallR16", None)
    bpy.context.scene.collection.objects.link(root)
    obs = PK.finish(P, M, "WallR16P") + HK.finish(H, M, "WallR16H")
    for ob in obs:
        ob.parent = root
    root.location = loc
    root.scale = (scale, scale, scale)
    return root


def spot_cap(name, center, R, direction, ang_deg, mat, seg=32, rings=6):
    """Landing spot that hugs a sphere: a spherical cap (radius R, angular radius ang_deg) around direction."""
    d = Vector(direction).normalized()
    q = Vector((0, 0, 1)).rotation_difference(d)
    bm = bmesh.new()
    top = bm.verts.new(Vector(center) + d * R)
    prev = None
    for k in range(1, rings + 1):
        th = math.radians(ang_deg) * k / rings
        ring = [bm.verts.new(Vector(center) + q @ Vector((R * math.sin(th) * math.cos(2 * math.pi * i / seg),
                                                          R * math.sin(th) * math.sin(2 * math.pi * i / seg),
                                                          R * math.cos(th)))) for i in range(seg)]
        for i in range(seg):
            j = (i + 1) % seg
            f = bm.faces.new((top, ring[i], ring[j])) if prev is None else bm.faces.new((prev[i], ring[i], ring[j], prev[j]))
            f.smooth = True
        prev = ring
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    me.materials.append(mat)
    ob.visible_shadow = False
    return ob
