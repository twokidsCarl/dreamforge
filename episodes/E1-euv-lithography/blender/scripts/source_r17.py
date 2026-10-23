"""Round 17 (P1) helpers for r2_source (source chamber) - NON-control variants only (amps / B1_22 never calls this).

R17 root cause #3 ("the tin pancake reads as a glass lens / porthole": dark thick rim frame + see-through centre +
black crescent) - GEOMETRY ONLY:
  pancake_r17   an opaque liquid-tin disc (the existing opaque droplet tin M["tin"] - no material parameter is
                changed; the see-through TinFilm is simply not used), slightly thicker in the centre (convex
                cross-section), the edge thinning out and breaking into a crown of ligaments with droplets flung
                off them. No rolled-rim torus (R16 source_kit_r16.pancake_rim_r16 = the dark thick frame).
R17 root cause #2 ("removing the fill turned the chamber black"): R15 fill LEVELS restored, but only with shapeless
lights:
  shapeless_fill_r17  each R15 rectangular area light (lights_chamber / softboxes) becomes a spherical point light at
                the same place, energy matched on its axis (a Lambertian area of power P has on-axis intensity
                P / pi, a point light P / 4 pi -> x AREA_TO_POINT), so the tin / mirrors only ever show soft round
                highlights, never a square card.
"""
import math
import random

import bpy
from mathutils import Vector

import kit_r2 as K

OFF = (0.0, 0.43, -0.31)
AREA_TO_POINT = 3.0       # a bit under the on-axis match (4): a point light also lights everything behind it

# R15 lights_chamber (r2_source) at scale 1: (name, loc, size, energy, colour)
CHAMBER_R15 = (("Rim", (-0.6, 1.1, 0.9), 0.5, 45.0, (0.65, 0.75, 1.0)),
               ("Key", (0.9, -0.9, 0.7), 0.4, 18.0, (0.9, 0.93, 1.0)),
               ("Top", (0.0, 0.0, 1.35), 1.2, 14.0, (0.7, 0.8, 1.0)),
               ("WallWash", (0.3, -1.0, -0.6), 0.8, 25.0, (0.45, 0.55, 0.9)))


def shapeless_fill_r17(scale=1.0, extra=(), tag="FillR17", glossy=True, skip=()):
    """Point-light (sphere) replacements of the R15 rectangular fills. extra = more (name, loc, size, energy,
    colour[, glossy]) entries (e.g. the R15 softboxes of one variant) at their own R15 energies."""
    out = []
    for e in tuple((nm, lo, sz, en * scale, co) for nm, lo, sz, en, co in CHAMBER_R15 if nm not in skip) + tuple(extra):
        nm, lo, sz, en, co = e[:5]
        li = K.point(f"{tag}_{nm}", lo, en * AREA_TO_POINT, co, max(0.15, sz * 0.5))
        li.visible_glossy = e[5] if len(e) > 5 else glossy
        out.append(li)
    return out


def pancake_r17(M, c, R, name="Pancake", seed=1, n_lig=18, glint=None):
    """Opaque liquid-tin sheet in the YZ plane (unit radius, scaled by R), returns (root empty, parts).
    Cross-section: convex, ~0.075 thick at the centre thinning to ~0.014 at the edge; a slightly wavy outline;
    crown ligaments (tapered fingers, slightly bent with the sheet's motion) with droplets at their tips and a
    few detached droplets further out. Nothing sits on the face; no rim bead / torus."""
    import bmesh
    rnd = random.Random(seed)
    mb = K.MB()
    na, nr = 128, 22
    harm = [(k, rnd.uniform(0.006, 0.014), rnd.uniform(0, 6.28)) for k in (3, 5, 9, 13)]

    def rim(a):
        return 1.0 + sum(amp * math.sin(k * a + ph) for k, amp, ph in harm)

    def thick(t):                       # convex: thick centre, thin edge (no bead)
        return 0.014 + 0.042 * (1.0 - t * t) ** 1.2

    def bow(t):                          # the whole sheet bows slightly with the push (+X): centre ahead
        return 0.012 * (1.0 - t * t)

    top, bot = [], []
    for i in range(nr + 1):
        t = i / nr
        rt, rb = [], []
        for j in range(na):
            a = 2 * math.pi * j / na
            rr = t * rim(a)
            h = thick(t) * (1 + 0.06 * t * math.sin(7 * a + 2 * t))     # t: no zig-zag pole at the centre
            y, z = rr * math.cos(a), rr * math.sin(a)
            rt.append(mb.bm.verts.new((bow(t) + h / 2, y + OFF[1], z + OFF[2])))
            rb.append(mb.bm.verts.new((bow(t) - h / 2, y + OFF[1], z + OFF[2])))
        top.append(rt)
        bot.append(rb)
    for i in range(nr):
        for j in range(na):
            k = (j + 1) % na
            mb.bm.faces.new((top[i][j], top[i][k], top[i + 1][k], top[i + 1][j])).smooth = True
            mb.bm.faces.new((bot[i][j], bot[i + 1][j], bot[i + 1][k], bot[i][k])).smooth = True
    for j in range(na):
        k = (j + 1) % na
        mb.bm.faces.new((top[nr][j], top[nr][k], bot[nr][k], bot[nr][j])).smooth = True
    bmesh.ops.remove_doubles(mb.bm, verts=mb.bm.verts[:], dist=1e-5)
    ob = mb.obj(name, M["tin"])                 # no subsurf: its centre pole drew a star in the reflection
    ob.location = (0, -OFF[1], -OFF[2])          # mesh offset in object space: the tin's object-space ripple
                                                 # rings centre off the sheet centre (no star at the pole)
    # crown: ligaments from the thin edge, droplets at the tips, a few detached droplets beyond
    lig = K.MB()
    for k in range(n_lig):
        a = 2 * math.pi * (k + rnd.uniform(-0.3, 0.3)) / n_lig
        u = Vector((0, math.cos(a), math.sin(a)))
        r0 = rim(a) * 0.97
        L = rnd.uniform(0.04, 0.11) * (1.5 if k % 5 == 0 else 1.0)
        w0 = rnd.uniform(0.016, 0.028)
        back = Vector((-rnd.uniform(0.01, 0.05), 0, 0))           # ligaments trail slightly behind the sheet
        p0 = u * r0
        p1 = u * (r0 + L * 0.55) + back * 0.5
        p2 = u * (r0 + L) + back
        lig.path([p0 - u * 0.02, p1, p2], w0, seg=10)
        lig.sphere(tuple(p0), w0 * 1.25, 10)                       # swelling where the finger leaves the edge
        lig.sphere(tuple(p2 + u * w0 * 0.6), w0 * rnd.uniform(1.4, 1.9), 12)
        if rnd.random() < 0.45:
            q = u * (r0 + L + rnd.uniform(0.08, 0.22)) + back * 1.5
            lig.sphere(tuple(q), w0 * rnd.uniform(0.9, 1.5), 10)
    so = lig.obj(name + "Crown", M["tin"])
    root = bpy.data.objects.new(name + "Root", None)
    bpy.context.scene.collection.objects.link(root)
    root.location = c
    ob.parent = root
    so.parent = root
    root.scale = (R, R, R)
    if glint is not None:        # one soft sphere light only the sheet sees: a round highlight, never a card
        loc, en = glint
        li = K.point(name + "GlintR17", loc, en, (0.92, 0.94, 1.0), 0.3)
        col = bpy.data.collections.new(name + "GlintR17_Recv")
        for o_ in (ob, so):
            col.objects.link(o_)
        li.light_linking.receiver_collection = col
    return root, [ob, so]
