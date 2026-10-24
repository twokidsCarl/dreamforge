"""Round 23 (P1) tin helpers (R23_ROOT_CAUSE row 3) - used only by source_r23.py (tin sub-agent).

  pancake_r23   ONE smooth continuous liquid sheet: gently domed, no ripples (R21/R22 ripple + glint = "crumpled
                foil"), centre slightly thicker -> edge thins to a film and turns out a little (flared lip), outline
                with only low-frequency wobble; a FEW separate round droplets just off the edge (clear gap, no neck,
                no ligament / spike / tongue). Not repeating: R21 straight ligaments + ball tips (legs), R22 torn
                tongues (lumpy / crumpled), R20 rolled rim + filaments, R17-R19 ball needles.
  sheet_env_r23 the sheet's reflection: the R18 band dome (thin rings) is unlinked from the sheet + debris and
                replaced by one continuous soft gradient dome (same additive glossy-only R18 dome mechanism).
Tin material parameters are not touched (same M["tin"]).
"""
import math
import random

import bpy
from mathutils import Vector

import kit_r2 as K

OFF = (0.0, 0.43, -0.31)


TEX_S = 0.12


def _shrink_uv(ob):
    """Same world shape, mesh stored TEX_S times smaller with object scale 1/TEX_S: the (unchanged) tin material's
    Object-space circumferential ripple bump then spans < half a ripple across the sheet -> one smooth surface
    instead of the 4-5 concentric ripples that read as crumpled foil. Material parameters untouched."""
    from mathutils import Matrix
    ob.data.transform(Matrix.Scale(TEX_S, 4))
    ob.scale = (1 / TEX_S,) * 3
    ob.location = tuple(v for v in ob.location)


def pancake_r23(M, c, R, name="Pancake", seed=1, glint=None):
    import bmesh
    rnd = random.Random(seed * 13 + 23)
    mb = K.MB()
    na = 192
    harm = [(2, rnd.uniform(0.030, 0.040), rnd.uniform(0, 6.28)),    # low-frequency splash outline (organic,
            (3, rnd.uniform(0.022, 0.030), rnd.uniform(0, 6.28)),    # not a machined circle), no tongues
            (5, rnd.uniform(0.010, 0.014), rnd.uniform(0, 6.28)),
            (7, rnd.uniform(0.005, 0.008), rnd.uniform(0, 6.28))]
    HT, HE = 0.042, 0.009          # centre half-thickness -> thin film at the edge

    def rim(a):
        return 1.0 + sum(amp * math.sin(k * a + ph) for k, amp, ph in harm)

    def mid(t):                     # t = rho / rim in [0, 1]: smooth dome + slightly turned-out lip (no ripples)
        x = DOME * (1.0 - t * t)
        if t > LIP0:
            x += LIP * ((t - LIP0) / (1.0 - LIP0)) ** 2
        return x

    n_in, n_e = 26, 6

    def profile(a):
        Ro = rim(a)
        pts = []
        for i in range(n_in + 1):
            s_ = i / n_in
            t = 1 - (1 - s_) ** 1.5
            h = HE + (HT - HE) * (1.0 - t ** 1.8)
            pts.append((Ro * t, h, mid(t)))
        for i in range(1, n_e + 1):  # rounded thin edge (radius = film half-thickness, NOT a rolled bead)
            ph = (math.pi / 2) * i / n_e
            pts.append((Ro + HE * math.sin(ph), HE * math.cos(ph), mid(1.0)))
        return pts

    profs = [profile(2 * math.pi * j / na) for j in range(na)]
    npf = len(profs[0])
    top, bot = [], []
    for i in range(npf):
        rt, rbt = [], []
        for j in range(na):
            a = 2 * math.pi * j / na
            rho, h, x0 = profs[j][i]
            y, z = rho * math.cos(a), rho * math.sin(a)
            rt.append(mb.bm.verts.new((x0 + h, y + OFF[1], z + OFF[2])))
            rbt.append(mb.bm.verts.new((x0 - h, y + OFF[1], z + OFF[2])))
        top.append(rt)
        bot.append(rbt)
    for i in range(npf - 1):
        for j in range(na):
            k = (j + 1) % na
            mb.bm.faces.new((top[i][j], top[i][k], top[i + 1][k], top[i + 1][j])).smooth = True
            mb.bm.faces.new((bot[i][j], bot[i + 1][j], bot[i + 1][k], bot[i][k])).smooth = True
    bmesh.ops.remove_doubles(mb.bm, verts=mb.bm.verts[:], dist=1e-6)
    ob = mb.obj(name, M["tin"])
    ob.location = (0, -OFF[1], -OFF[2])
    _shrink_uv(ob)

    # a few separate droplets just off the edge (clear gap, round, no neck)
    dr = K.MB()
    nd = N_DROPS
    base = rnd.uniform(0, 6.28)
    for k in range(nd):
        a = base + 2 * math.pi * (k + rnd.uniform(-0.3, 0.3)) / nd
        rr = rnd.choice((0.05, 0.06, 0.07)) * rnd.uniform(0.9, 1.1)
        gap = rnd.uniform(0.03, 0.09)
        rho = rim(a) + HE + gap + rr
        p = Vector((mid(1.0) + 0.02 * gap / 0.2, rho * math.cos(a), rho * math.sin(a)))
        dr.sphere(tuple(p), rr, 16)
    so = dr.obj(name + "Drops", M["tin"])
    _shrink_uv(so)
    for poly in so.data.polygons:
        poly.use_smooth = True
    root = bpy.data.objects.new(name + "Root", None)
    bpy.context.scene.collection.objects.link(root)
    root.location = c
    ob.parent = root
    so.parent = root
    root.scale = (R, R, R)
    if glint is not None:        # same linked R17 glint light as before (lighting unchanged)
        loc, en = glint
        li = K.point(name + "GlintR17", loc, en, (0.92, 0.94, 1.0), 0.3)
        col = bpy.data.collections.new(name + "GlintR17_Recv")
        for o_ in (ob, so):
            col.objects.link(o_)
        li.light_linking.receiver_collection = col
    return root, [ob, so]


DOME = 0.035
LIP0, LIP = 0.8, 0.09
N_DROPS = 4

# one continuous soft gradient per shot: a broad soft bright cap between the sheet's mirror direction (camera ray
# reflected off the sheet face) and straight up, fading smoothly to a dark steel base -> the gently domed sheet shows
# ONE smooth bright-to-dark sweep + a bright thin turned-out lip (no rings / thin bands / patches).
#   A0_01 camera ~(0.54,-0.40,0.14) -> sheet-centre mirror dir ~(0.79,0.59,-0.2); B1_10 cam (-0.52,-0.6,0.12) -> (-0.65,0.75,-0.15)
def _bands(r0, up=1.1, hw=0.45, st=1.5):
    r0 = Vector(r0).normalized()
    cap = (r0 + Vector((0, 0, up))).normalized()   # cap well above the face mirror dir
    return ((tuple(cap), 1.0, hw, st, (0.84, 0.88, 1.0)),          # broad soft cap -> gentle sweep over the face
            (tuple(r0), 0.35, 0.25, 1.6, (0.86, 0.9, 1.0)),          # ~70 deg off the face mirror dir: only the
            ((0.0, 0.0, 1.0), 1.0, 0.7, 0.3, (0.75, 0.8, 0.95)))     # turned-out thin lip sees it -> bright rim


SHEET_BANDS = {"A0_01": _bands((0.79, 0.59, -0.2), 0.6, 0.6, 1.4),   # A0_01: lighter face + rim (dark face read as a bulb)
               "B1_10": _bands((-0.65, 0.75, -0.15))}
SHEET_BASE = (0.025, 0.027, 0.032)


def _env_mat_r23(name, bands, base, gain, radius):
    """R18 gradient node graph, but OPAQUE from the inside: a reflected ray leaving the sheet sees ONLY the smooth
    gradient (no real chamber modules behind it = no patchy 'crumpled foil' blotches). Camera / shadow rays and
    rays entering from outside (front face) pass through."""
    import source_r18 as S18
    m = S18.env_material_r18(name, bands, base, gain)
    nt = m.node_tree
    em = next(n for n in nt.nodes if n.type == "EMISSION")
    tr = next(n for n in nt.nodes if n.type == "BSDF_TRANSPARENT")
    add = next(n for n in nt.nodes if n.type == "ADD_SHADER")
    out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
    for l in list(em.inputs["Strength"].links):
        nt.links.remove(l)
    lp = next(n for n in nt.nodes if n.type == "LIGHT_PATH")
    geo = next(n for n in nt.nodes if n.type == "NEW_GEOMETRY")
    mul = nt.nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    nt.links.new(lp.outputs["Is Glossy Ray"], mul.inputs[0])
    nt.links.new(geo.outputs["Backfacing"], mul.inputs[1])
    # a refracted ray (camera ray through the chamber's ViewGlass port) is GLOSSY|TRANSMIT -> must pass through
    ntr = nt.nodes.new("ShaderNodeMath")
    ntr.operation = "LESS_THAN"
    nt.links.new(lp.outputs["Is Transmission Ray"], ntr.inputs[0])
    ntr.inputs[1].default_value = 0.5
    mul2 = nt.nodes.new("ShaderNodeMath")
    mul2.operation = "MULTIPLY"
    nt.links.new(mul.outputs[0], mul2.inputs[0])
    nt.links.new(ntr.outputs[0], mul2.inputs[1])
    # only rays that START inside the sphere (= leave the tin sheet / drops) see it; rays from outside (the collector
    # mirror / chamber metals reflecting through it) pass. origin = P + I * ray_length (I points back to the origin)
    inc = nt.nodes.new("ShaderNodeVectorMath")
    inc.operation = "SCALE"
    nt.links.new(geo.outputs["Incoming"], inc.inputs[0])
    nt.links.new(lp.outputs["Ray Length"], inc.inputs["Scale"])
    org = nt.nodes.new("ShaderNodeVectorMath")
    org.operation = "ADD"
    nt.links.new(geo.outputs["Position"], org.inputs[0])
    nt.links.new(inc.outputs[0], org.inputs[1])
    oi = nt.nodes.new("ShaderNodeObjectInfo")
    dv = nt.nodes.new("ShaderNodeVectorMath")
    dv.operation = "DISTANCE"
    nt.links.new(org.outputs[0], dv.inputs[0])
    nt.links.new(oi.outputs["Location"], dv.inputs[1])
    ins = nt.nodes.new("ShaderNodeMath")
    ins.operation = "LESS_THAN"
    nt.links.new(dv.outputs["Value"], ins.inputs[0])
    ins.inputs[1].default_value = 0.9 * radius
    mul3 = nt.nodes.new("ShaderNodeMath")
    mul3.operation = "MULTIPLY"
    nt.links.new(mul2.outputs[0], mul3.inputs[0])
    nt.links.new(ins.outputs[0], mul3.inputs[1])
    fac_sock = mul3.outputs[0]
    em.inputs["Strength"].default_value = 1.0
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(fac_sock, mix.inputs[0])
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(em.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])
    nt.nodes.remove(add)
    return m


def sheet_env_r23(name, centre, radius, receivers, shot, gain=1.0):
    """Smooth gradient environment for the sheet: receivers are unlinked from every R18 band dome (as R22 did for
    the droplet) and enclosed by one opaque-from-inside gradient sphere."""
    import kit_r2 as K_
    for o in bpy.data.objects:
        if o.type == "MESH" and o.name.startswith("TinEnvR18"):
            col = o.light_linking.receiver_collection
            if col is not None:
                for r_ in receivers:
                    if r_.name in col.objects:
                        col.objects.unlink(r_)
    mb = K_.MB()
    mb.sphere((0, 0, 0), radius, 64)
    ob = mb.obj(name, _env_mat_r23(name + "Mat", SHEET_BANDS[shot], SHEET_BASE, gain, radius))
    for poly in ob.data.polygons:
        poly.use_smooth = True
    ob.location = centre
    ob.visible_camera = False
    ob.visible_shadow = False
    ob.visible_diffuse = False
    ob.visible_volume_scatter = False
    ob.visible_transmission = False
    return ob
