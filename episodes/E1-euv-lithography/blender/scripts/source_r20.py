"""Round 20 (P1) helpers for r2_source (A0_01 / B1_10 tin sheet). New file; source_r17 / source_r19 untouched.

R20 root cause #5 (R19 review A0_01 #1 / B1_10 #1: 「边缘一圈小液滴像图钉…飞溅改成拉丝状的细颈液滴，不要等距排一圈的
球头针」「表面张力形成的圆滑卷边，飞溅改成细颈液丝」): GEOMETRY ONLY - the tin material (M["tin"]) is untouched.
  * sheet: one continuous revolved profile - thick centre thinning smoothly toward the edge, ending in a rounded
    toroidal rim (surface-tension bead, semicircular cross-section, its size varies slowly around the rim) - no flat
    cut edge, no separate torus;
  * splash: a few (9-12) ligaments at irregular, unequal spacing, very different lengths: a broad root that grows out
    of a rim bulge, a thin neck, an end bead (Rayleigh-Plateau), some with a pinch-off bead beyond the tip - not an
    evenly spaced ring of pin-head spheres.
Same contract as source_r17.pancake_r17: unit radius in the YZ plane scaled by R, returns (root, [sheet, crown]),
names Pancake / PancakeCrown (tin_objects() still finds them by material), optional linked glint light.
"""
import math
import random

import bpy
from mathutils import Vector

import kit_r2 as K

OFF = (0.0, 0.43, -0.31)        # same object-space offset as source_r17 (the tin's ripple rings centre off the sheet)


def _smax(a, b, k=0.01):
    h = max(0.0, min(1.0, 0.5 + 0.5 * (a - b) / k))
    return a * h + b * (1 - h) + k * h * (1 - h)


def pancake_r20(M, c, R, name="Pancake", seed=1, glint=None):
    import bmesh
    rnd = random.Random(seed)
    mb = K.MB()
    na = 160
    harm = [(k, rnd.uniform(0.006, 0.014), rnd.uniform(0, 6.28)) for k in (3, 5, 9, 13)]
    bead_h = [(k, rnd.uniform(0.08, 0.18), rnd.uniform(0, 6.28)) for k in (2, 3, 5, 7)]

    def rim(a):                         # outer radius (slightly wavy outline)
        return 1.0 + sum(amp * math.sin(k * a + ph) for k, amp, ph in harm)

    def rb(a):                          # rim-bead radius: slowly varying (incipient Rayleigh-Plateau corrugation)
        return 0.034 * (1.0 + sum(amp * math.sin(k * a + ph) for k, amp, ph in bead_h))

    def bow(rho):                       # the sheet bows slightly with the push (+X): centre ahead
        return 0.012 * (1.0 - min(1.0, rho) ** 2)

    def membrane(rho):                  # half-thickness: thick centre -> thin near the rim (continuous)
        t = min(1.0, rho / 0.92)
        return 0.5 * (0.012 + 0.042 * (1.0 - t * t) ** 1.3)

    # profile parameters: inner samples in rho (0..rho_c), then a quarter circle around the bead to the edge
    n_in, n_out = 22, 8

    def profile(a):
        """List of (rho, half-thickness) from the centre to the outer edge (half-thickness -> 0)."""
        Ro, b = rim(a), rb(a)
        rc = Ro - b
        pts = []
        for i in range(n_in + 1):
            s = i / n_in
            rho = rc * (1 - (1 - s) ** 1.6)
            bead = math.sqrt(max(0.0, b * b - (rho - rc) ** 2))
            pts.append((rho, _smax(membrane(rho), bead, 0.012)))
        for i in range(1, n_out + 1):
            ph = (math.pi / 2) * i / n_out
            pts.append((rc + b * math.sin(ph), b * math.cos(ph)))
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
            x0 = bow(rho)
            rt.append(mb.bm.verts.new((x0 + h, y + OFF[1], z + OFF[2])))
            rbt.append(mb.bm.verts.new((x0 - h, y + OFF[1], z + OFF[2])))
        top.append(rt)
        bot.append(rbt)
    for i in range(npf - 1):
        for j in range(na):
            k = (j + 1) % na
            mb.bm.faces.new((top[i][j], top[i][k], top[i + 1][k], top[i + 1][j])).smooth = True
            mb.bm.faces.new((bot[i][j], bot[i + 1][j], bot[i + 1][k], bot[i][k])).smooth = True
    bmesh.ops.remove_doubles(mb.bm, verts=mb.bm.verts[:], dist=1e-6)   # merges the centre poles + the edge seam
    ob = mb.obj(name, M["tin"])
    ob.location = (0, -OFF[1], -OFF[2])

    # ligaments: irregular count / spacing / length; root -> thin neck -> end bead (+ sometimes a pinched-off bead)
    lig = K.MB()
    nl = rnd.randint(9, 12)
    angs = sorted(rnd.uniform(0, 2 * math.pi) for _ in range(nl))
    for k, a in enumerate(angs):
        u = Vector((0, math.cos(a), math.sin(a)))
        side = Vector((0, -math.sin(a), math.cos(a)))
        b = rb(a)
        r0 = rim(a) - b                                    # starts inside the bead (grows out of it)
        L = rnd.choice((rnd.uniform(0.1, 0.16), rnd.uniform(0.16, 0.28), rnd.uniform(0.28, 0.44)))
        w_root = b * rnd.uniform(0.8, 1.0)
        w_neck = b * rnd.uniform(0.38, 0.5) * (1.0 + 0.9 * max(0.0, 0.3 - L) / 0.2)   # short = stubby finger
        bend = side * rnd.uniform(-0.25, 0.25) * L
        back = Vector((-rnd.uniform(0.005, 0.04), 0, 0))   # trails slightly behind the sheet
        p0 = u * r0
        p1 = u * (r0 + b + L * 0.3) + bend * 0.2 + back * 0.3
        p2 = u * (r0 + b + L * 0.75) + bend * 0.7 + back * 0.75
        p3 = u * (r0 + b + L) + bend + back
        lig.tube(p0, p1, w_root, seg=14, r2=w_neck * 1.2)  # broad root growing out of the rim bead
        lig.sphere(tuple(p1), w_neck * 1.2, 14)
        lig.tube(p1, p2, w_neck * 1.2, seg=14, r2=w_neck)   # thin neck
        lig.sphere(tuple(p2), w_neck, 12)
        w_bead = w_neck * rnd.uniform(1.5, 2.1)            # teardrop end bead (swells out of the neck, no pin head)
        lig.tube(p2, p3, w_neck, seg=12, r2=w_bead * 0.92)
        lig.sphere(tuple(p3), w_bead, 16)
        if rnd.random() < 0.4:                             # pinched-off bead beyond the tip, irregular gap
            q = p3 + (p3 - p2).normalized() * rnd.uniform(0.04, 0.12) + back * 0.5
            lig.sphere(tuple(q), w_neck * rnd.uniform(1.0, 1.8), 12)
    so = lig.obj(name + "Crown", M["tin"])
    for o_ in (so,):
        for poly in o_.data.polygons:
            poly.use_smooth = True
    root = bpy.data.objects.new(name + "Root", None)
    bpy.context.scene.collection.objects.link(root)
    root.location = c
    ob.parent = root
    so.parent = root
    root.scale = (R, R, R)
    if glint is not None:        # same as R17: one soft sphere light only the tin sheet sees (lighting unchanged)
        loc, en = glint
        li = K.point(name + "GlintR17", loc, en, (0.92, 0.94, 1.0), 0.3)
        col = bpy.data.collections.new(name + "GlintR17_Recv")
        for o_ in (ob, so):
            col.objects.link(o_)
        li.light_linking.receiver_collection = col
    return root, [ob, so]
