"""Round 24 (P1) tin helpers (R24_ROOT_CAUSE row 2: tin shared asset -> all importers). Used only by source_r24.py.

  tin_mat_r24   OPAQUE liquid metal: Principled metallic 1, roughness 0.10, no transmission / coat / ripple bump.
  pancake_r24   ULTRA-THIN film (total thickness <= diameter / 80, i.e. well under the 1/40 limit), slightly cupped
                away from the laser, finely scalloped edge (no tongues / ligaments / legs / rolled rim) and a ring of
                N separate round droplets just outside the edge with a visible gap (no neck / filament).
  afterglow_r24 small orange emissive arc on the laser-facing part of the edge (cause hint), fades out.
  env_r24       the tin's reflection: one opaque-from-inside gradient sphere (R23 _env_mat_r23 mechanism) = dark
                chamber base + soft overhead sky + ONE crisp key highlight (+ faint violet bounce) - no band rings,
                no rectangular cards.
Not repeating: R21 straight ligaments + ball tips, R22 tongues, R23 smooth thick disc / bright gradient (white bowl),
R20 rolled rim + filaments, R17-R19 ball needles.
"""
import math
import random

import bpy
from mathutils import Vector

import kit_r2 as K

TIN_COL = (0.78, 0.78, 0.80)
TIN_ROUGH = 0.10


def tin_mat_r24(name="TinMetalR24"):
    m = K.mat(name, TIN_COL, metal=1.0, rough=TIN_ROUGH)
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    for key in ("Transmission Weight", "Transmission", "Coat Weight", "Clearcoat"):
        if key in b.inputs:
            b.inputs[key].default_value = 0.0
    return m


HT, HE = 0.0125, 0.006      # half-thickness centre / edge (unit radius sheet) -> total 0.025 = D / 80
CUP = 0.015                 # sheet centre bulges toward the laser by this much (cupped film, not a lid)
N_RING = 16


def pancake_r24(M, c, R, name="Pancake", seed=1, glint=None):
    import bmesh
    rnd = random.Random(seed * 31 + 24)
    harm = [(2, rnd.uniform(0.02, 0.03), rnd.uniform(0, 6.28)),
            (3, rnd.uniform(0.015, 0.022), rnd.uniform(0, 6.28)),
            (5, rnd.uniform(0.008, 0.012), rnd.uniform(0, 6.28)),
            (11, rnd.uniform(0.006, 0.009), rnd.uniform(0, 6.28)),
            (17, rnd.uniform(0.004, 0.006), rnd.uniform(0, 6.28))]
    ph_s = rnd.uniform(0, 6.28)

    def rim(a):             # low-freq wobble + fine scallops (one cusp per ring droplet = edge breaking up)
        return 1.0 + sum(amp * math.sin(k * a + p) for k, amp, p in harm)

    def mid(t):             # cupped: centre toward -X (laser side), edge flares back
        return -CUP * (1.0 - t * t)

    mb = K.MB()
    na, n_in, n_e = 256, 22, 5
    profs = []
    for j in range(na):
        a = 2 * math.pi * j / na
        Ro = rim(a)
        pts = []
        for i in range(1, n_in + 1):          # no degenerate centre pole (it drew a dark disc): tri fan below
            t = 1 - (1 - i / n_in) ** 1.4
            h = HE + (HT - HE) * (1.0 - t * t)
            pts.append((Ro * t, h, mid(t)))
        for i in range(1, n_e + 1):
            ph = (math.pi / 2) * i / n_e
            pts.append((Ro + HE * math.sin(ph), HE * math.cos(ph), mid(1.0)))
        profs.append(pts)
    npf = len(profs[0])
    top, bot = [], []
    for i in range(npf):
        rt, rb = [], []
        for j in range(na):
            a = 2 * math.pi * j / na
            rho, h, x0 = profs[j][i]
            y, z = rho * math.cos(a), rho * math.sin(a)
            rt.append(mb.bm.verts.new((x0 + h, y, z)))
            rb.append(mb.bm.verts.new((x0 - h, y, z)))
        top.append(rt)
        bot.append(rb)
    for i in range(npf - 1):
        for j in range(na):
            k = (j + 1) % na
            mb.bm.faces.new((top[i][j], top[i][k], top[i + 1][k], top[i + 1][j])).smooth = True
            mb.bm.faces.new((bot[i][j], bot[i + 1][j], bot[i + 1][k], bot[i][k])).smooth = True
    ct = mb.bm.verts.new((mid(0.0) + HT, 0.0, 0.0))
    cb_ = mb.bm.verts.new((mid(0.0) - HT, 0.0, 0.0))
    for j in range(na):
        k = (j + 1) % na
        mb.bm.faces.new((ct, top[0][j], top[0][k])).smooth = True
        mb.bm.faces.new((cb_, bot[0][k], bot[0][j])).smooth = True
    ob = mb.obj(name, M["tin"])
    for p in ob.data.polygons:
        p.use_smooth = True

    dr = K.MB()
    for k in range(N_RING):     # one droplet in front of each scallop cusp, clear gap, sizes vary
        a = 2 * math.pi * (k + rnd.uniform(-0.12, 0.12)) / N_RING - 2 * ph_s / N_RING
        rr = rnd.uniform(0.04, 0.058)
        gap = rnd.uniform(0.05, 0.10)
        rho = rim(a) + HE + gap + rr
        dr.sphere((mid(1.0) + rnd.uniform(-0.01, 0.01), rho * math.cos(a), rho * math.sin(a)), rr, 16)
        if rnd.random() < 0.35:   # a few smaller satellite drops further out
            r2 = rr * 0.55
            rho2 = rho + rr + rnd.uniform(0.04, 0.07) + r2
            a2 = a + rnd.uniform(-0.06, 0.06)
            dr.sphere((mid(1.0), rho2 * math.cos(a2), rho2 * math.sin(a2)), r2, 12)
    so = dr.obj(name + "Drops", M["tin"])
    for p in so.data.polygons:
        p.use_smooth = True
    root = bpy.data.objects.new(name + "Root", None)
    bpy.context.scene.collection.objects.link(root)
    root.location = c
    ob.parent = root
    so.parent = root
    root.scale = (R, R, R)
    root["r24_rim"] = [rim(2 * math.pi * j / 64) for j in range(64)]
    if glint is not None:
        loc, en = glint
        li = K.point(name + "GlintR17", loc, en, (0.92, 0.94, 1.0), 0.3)
        col = bpy.data.collections.new(name + "GlintR17_Recv")
        for o_ in (ob, so):
            col.objects.link(o_)
        li.light_linking.receiver_collection = col
    return root, [ob, so]


def afterglow_r24(root, a0, a1, strength=6.0, name="TinAfterglowR24"):
    """Orange emissive arc hugging the laser-facing part of the edge (unit coords, parented to the sheet root)."""
    rims = root["r24_rim"]
    mb = K.MB()
    n = 40
    pts = []
    for i in range(n + 1):
        a = a0 + (a1 - a0) * i / n
        j = int(round(a / (2 * math.pi) * 64)) % 64
        rho = rims[j] + HE * 0.5
        pts.append(Vector((-CUP * 0 + 0.0, rho * math.cos(a), rho * math.sin(a))))
    for i in range(n):
        w = math.sin(math.pi * (i + 0.5) / n)            # thickest mid-arc, tapering ends
        mb.tube(tuple(pts[i]), tuple(pts[i + 1]), 0.006 + 0.012 * w, seg=8)
    m = K.emit_mat(name + "Mat", (1.0, 0.42, 0.08), strength)
    ob = mb.obj(name, m)
    ob.parent = root
    ob.visible_shadow = False
    return ob


def env_r24(name, centre, radius, receivers, key_dir, mirror_dir=None, key=7.0, sky=0.22, parent=None):
    import source_r23_tin as T23
    key_dir = Vector(key_dir).normalized()
    bands = [((0.0, 0.0, 1.0), 1.0, 0.9, sky, (0.70, 0.76, 0.88)),            # soft overhead sky -> dark below
             (tuple(key_dir), 1.0, 0.035, key, (0.95, 0.96, 1.0)),            # one crisp key highlight
             ((-0.4, 0.6, -0.5), 1.0, 0.35, 0.10, (0.55, 0.45, 0.9))]          # faint violet plasma bounce
    if mirror_dir is not None:      # sheet: soft lighter streak just above the face's mirror direction
        md = Vector(mirror_dir).normalized()
        st = (md + Vector((0, 0, 0.10))).normalized()
        bands.append((tuple(md), 1.0, 0.30, 0.35, (0.62, 0.66, 0.78)))       # soft lit chamber behind the face
        bands.append((tuple(st), 1.0, 0.025, 1.4, (0.85, 0.88, 0.96)))       # one crisp streak across the film
    base = (0.010, 0.011, 0.014)
    for o in bpy.data.objects:      # tin out of every older dome / rim light
        if o.name.startswith(("TinEnvR18",)) or o.type == "LIGHT":
            col = o.light_linking.receiver_collection if hasattr(o, "light_linking") else None
            if col is not None and o.name.startswith(("TinEnvR18", "TinRimR22")):
                for r_ in receivers:
                    if r_.name in col.objects:
                        col.objects.unlink(r_)
    mb = K.MB()
    mb.sphere((0, 0, 0), radius, 64)
    ob = mb.obj(name, T23._env_mat_r23(name + "Mat", bands, base, 1.0, radius))
    for p in ob.data.polygons:
        p.use_smooth = True
    if parent is not None:
        ob.parent = parent
        ob.location = (0, 0, 0)
    else:
        ob.location = centre
    ob.visible_camera = False
    ob.visible_shadow = False
    ob.visible_diffuse = False
    ob.visible_volume_scatter = False
    ob.visible_transmission = False
    return ob
