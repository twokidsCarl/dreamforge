"""Round 22 (P1) tin helpers (R22_ROOT_CAUSE row 3) - used only by source_r22.py (tin sub-agent).

  pancake_r22      R21 thin continuous sheet (1/20, low-frequency ripple, normal on the laser = local +X) kept, but
                   the edge is an IRREGULAR flung-out film: centre slightly thicker, edge thin; the outline carries
                   torn tongues of varying length/width (ragged, thinner toward the tip, swept slightly downstream)
                   + BROKEN droplets of mixed sizes, detached from the edge at different distances (clear gap, no
                   neck). No straight whiskers / ball-ended ligaments (R21), no rolled rim (R20), no even pins (R17-19).
  smooth_env_r22   the droplet's reflection environment: a continuous soft gradient dome (no rings / bands), seen
                   only by the droplets (light linking), replacing the R18 band dome for them.
  rim_light_r22    one large camera-invisible area light behind the droplet(s), linked to the droplets only:
                   a thin bright silhouette rim on the mirror sphere.
Tin material parameters are not touched.
"""
import math
import random

import bpy
from mathutils import Vector

import kit_r2 as K
import source_r18 as S18

OFF = (0.0, 0.43, -0.31)


def pancake_r22(M, c, R, name="Pancake", seed=1, glint=None):
    rnd = random.Random(seed * 7 + 22)
    mb = K.MB()
    na = 420
    harm = [(k, rnd.uniform(0.012, 0.022), rnd.uniform(0, 6.28)) for k in (2, 3)]
    ragged = [(k, rnd.uniform(0.006, 0.012), rnd.uniform(0, 6.28)) for k in (7, 12, 19)]
    ph_w = rnd.uniform(0, 6.28)
    HT = 0.055                      # centre half-thickness (slightly thicker centre) ...
    HE = 0.018                      # ... thin film at the edge / tongue tips
    # torn tongues: irregular angles, widths, lengths
    nt = 7
    base = rnd.uniform(0, 6.28)
    tongues = []
    for k in range(nt):
        a = base + 2 * math.pi * (k + rnd.uniform(-0.35, 0.35)) / nt
        L = rnd.choice((0.05, 0.1, 0.17, 0.26)) * rnd.uniform(0.85, 1.2)
        w = rnd.uniform(0.09, 0.22)
        skew = rnd.uniform(-0.35, 0.35)
        tongues.append((a, L, w, skew))

    def tongue(a):
        t_ = 0.0
        for a0, L, w, sk in tongues:
            d = math.atan2(math.sin(a - a0), math.cos(a - a0))
            d = d / (w * (1.0 + sk * (1 if d > 0 else -1)))
            if abs(d) < 1.0:                    # rounded, blunt lobe (no pointed spike)
                t_ = max(t_, L * (1.0 - d * d) ** 0.6)
        return t_

    def rim0(a):
        return 1.0 + sum(amp * math.sin(k * a + ph) for k, amp, ph in harm)

    def rim(a):
        return rim0(a) - 0.012 + tongue(a) + sum(amp * math.sin(k * a + ph) for k, amp, ph in ragged)

    def bow(rho, a):                # R21 low-frequency ripple, plus a gentle downstream sweep of the flung film
        r1 = min(1.0, rho)
        b = 0.06 * (1.0 - r1 ** 2) + 0.035 * math.sin(math.pi * r1 * 1.4) * math.cos(a + ph_w)
        if rho > 0.85:
            b += 0.1 * (rho - 0.85) ** 2
        return b

    n_in, n_out = 24, 10

    def profile(a):
        # inner sheet up to the smooth low-harmonic rim (thickness depends on rho / rim0 only -> no radial creases),
        # then the flung film / tongue zone: thin, tapering further toward the ragged tip
        R0 = rim0(a)
        ext = max(0.006, rim(a) - R0 + 0.012)
        pts = []
        for i in range(n_in + 1):
            s_ = i / n_in
            rho = R0 * (1 - (1 - s_) ** 1.3)
            t = rho / R0
            pts.append((rho, HT + (HE - HT) * t ** 2.2))
        for i in range(1, n_out + 1):
            u = i / n_out
            pts.append((R0 + ext * u, HE * (1.0 - 0.45 * u)))
        return pts

    profs = [profile(2 * math.pi * j / na) for j in range(na)]
    npf = len(profs[0])
    top, bot = [], []
    for i in range(npf):
        rt, rbt = [], []
        for j in range(na):
            a = 2 * math.pi * j / na
            rho, h = profs[j][i]
            y, z = rho * math.cos(a), rho * math.sin(a)
            x0 = bow(rho, a)
            rt.append(mb.bm.verts.new((x0 + h, y + OFF[1], z + OFF[2])))
            rbt.append(mb.bm.verts.new((x0 - h, y + OFF[1], z + OFF[2])))
        top.append(rt)
        bot.append(rbt)
    for i in range(npf - 1):
        for j in range(na):
            k = (j + 1) % na
            mb.bm.faces.new((top[i][j], top[i][k], top[i + 1][k], top[i + 1][j])).smooth = True
            mb.bm.faces.new((bot[i][j], bot[i + 1][j], bot[i + 1][k], bot[i][k])).smooth = True
    for j in range(na):                           # thin closed edge band
        k = (j + 1) % na
        mb.bm.faces.new((top[-1][j], bot[-1][j], bot[-1][k], top[-1][k])).smooth = True
    import bmesh
    bmesh.ops.remove_doubles(mb.bm, verts=mb.bm.verts[:], dist=1e-6)
    ob = mb.obj(name, M["tin"])
    ob.location = (0, -OFF[1], -OFF[2])

    # broken droplets: mixed sizes, detached (clear gap) at different distances, mostly off tongue tips, a few
    # between tongues; no neck / no ligament joins them to the sheet
    dr = K.MB()
    picks = [(a0 + rnd.uniform(-0.06, 0.06), L) for a0, L, w, sk in tongues if rnd.random() < 0.8]
    for _ in range(5):
        picks.append((rnd.uniform(0, 6.28), 0.0))
    for a, L in picks:
        for m in range(rnd.choice((1, 1, 2, 3))):
            rr = rnd.choice((0.018, 0.024, 0.03, 0.04, 0.05)) * rnd.uniform(0.9, 1.15)
            gap = rnd.uniform(0.07, 0.42) + m * rnd.uniform(0.08, 0.16)
            aa = a + rnd.uniform(-0.05, 0.05) * (m + 1)
            rho = rim(aa) + gap + rr
            p = Vector((bow(rho, aa) + 0.03 * gap, rho * math.cos(aa), rho * math.sin(aa)))
            dr.sphere(tuple(p), rr, 14)
    so = dr.obj(name + "Debris", M["tin"])
    for poly in so.data.polygons:
        poly.use_smooth = True
    root = bpy.data.objects.new(name + "Root", None)
    bpy.context.scene.collection.objects.link(root)
    root.location = c
    ob.parent = root
    so.parent = root
    root.scale = (R, R, R)
    if glint is not None:
        loc, en = glint
        li = K.point(name + "GlintR17", loc, en, (0.92, 0.94, 1.0), 0.3)
        col = bpy.data.collections.new(name + "GlintR17_Recv")
        for o_ in (ob, so):
            col.objects.link(o_)
        li.light_linking.receiver_collection = col
    return root, [ob, so]


# chrome-ball sky: one soft continuous gradient (bright cool top fading smoothly through the horizon to dark below),
# no rings / no thin bands
SMOOTH_BANDS = (((0.0, 0.0, 1.0), 1.0, 1.35, 2.2, (0.82, 0.87, 1.0)),
                ((0.3, -0.6, 0.5), 1.0, 0.9, 0.4, (0.75, 0.8, 0.95)))


def smooth_env_r22(name, centre, radius, receivers, bands=SMOOTH_BANDS, gain=1.0):
    """R18-style invisible dome (additive, glossy-only, light-linked to `receivers`) with a continuous gradient,
    and the receivers taken OUT of every older R18 dome (their band rings were the dark/bright stripes)."""
    for o in bpy.data.objects:
        if o.type == "MESH" and o.name.startswith("TinEnvR18"):
            col = o.light_linking.receiver_collection
            if col is not None:
                for r_ in receivers:
                    if r_.name in col.objects:
                        col.objects.unlink(r_)
                if len(col.objects) == 0:
                    o.hide_render = True
    return S18.env_dome_r18(name, centre, radius, receivers, bands=bands, gain=gain)


def rim_light_r22(name, loc, target, size, energy, receivers, size_y=None):
    li = K.area(name, loc, target, size, energy, (0.9, 0.94, 1.0), size_y=size_y)
    li.visible_camera = False
    li.visible_diffuse = False
    col = bpy.data.collections.new(name + "_Recv")
    for r_ in receivers:
        col.objects.link(r_)
    li.light_linking.receiver_collection = col
    return li
