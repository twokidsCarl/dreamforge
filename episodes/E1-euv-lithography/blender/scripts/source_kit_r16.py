"""Round 16 (P1) helpers for r2_source (source chamber) - NON-control variants only (amps / B1_22 never calls this).

R16 root cause #2 ("tin reads as glass / chrome": the sheet and droplets mirrored square studio cards / softboxes):
  relight_r16      delete every rectangular emitter (area lights, studio card strips, softboxes) and the glossy HDRI
                   window environment; the chamber is lit only by the plasma / laser themselves plus at most ONE
                   shapeless weak cool rim (a large spherical point light: in a mirror it is a soft round blob, never a
                   square card)
  pancake_rim_r16  geometry, not material: a thick rolled rim bead with Rayleigh-Plateau swellings around the sheet
                   edge and droplets flung off it on short tapering ligaments
  wall_modules_r16 de-grid the vessel wall: interleaved nameable modules (turbo pump + gate valve, viewport spool,
                   bellows, coolant manifold bundle, gas panel, drag chain, ion pump) from hero_kit_r11 / r12, built
                   in their flat local frame and bent onto the cylindrical wall (no repeated cable-tray / panel grid)
R16 root cause #1 (B1_15 H1):
  collector_r16    a deep ellipsoidal collector whose FIRST FOCUS is the plasma site (origin), central hole, bolted
                   flange, cooling back - so a camera near the optical axis sees the plasma sitting at the dish focus
                   and the polished face full of its glow.
"""
import math
import random

import bpy
from mathutils import Matrix, Vector

import kit_r2 as K
import hero_kit_r10 as H
import hero_kit_r11 as H11
import hero_kit_r12 as H12

RECT_EMITTER_TAGS = ("Cards", "Softbox", "Soft", "Graze")


# ---------------------------------------------------------------- lighting (#2)
def relight_r16(sc, rim=None, rim_energy=6.0, rim_radius=0.35, rim_color=(0.62, 0.72, 1.0)):
    """Remove all rectangular emitters; optionally add one shapeless cool rim (spherical point light)."""
    for ob in list(bpy.data.objects):
        if ob.type == "LIGHT" and ob.data.type == "AREA":
            bpy.data.objects.remove(ob)
        elif ob.type == "MESH" and any(t in ob.name for t in RECT_EMITTER_TAGS):
            bpy.data.objects.remove(ob)
    sc["hdri_world"] = True                 # styles.py: no glossy HDRI (its windows were square cards in the tin)
    if rim is not None:
        li = K.point("CoolRimR16", rim, rim_energy, rim_color, rim_radius)
        return li
    return None


# ---------------------------------------------------------------- pancake rim geometry (#2)
def pancake_rim_r16(root, mat, seed=5, bead=0.055, n_fling=11):
    """Unit-space (sheet in the YZ plane, radius ~1) rolled rim + flung droplets, parented to the sheet root."""
    rnd = random.Random(seed)
    mb = K.MB()
    na = 160
    pts = []
    for j in range(na + 1):
        a = 2 * math.pi * j / na
        rr = 0.985 + 0.012 * math.sin(5 * a + 1.3) + 0.008 * math.sin(11 * a + 0.4)
        pts.append(Vector((0.012 * math.sin(7 * a), rr * math.cos(a), rr * math.sin(a))))
    mb.path(pts, bead, seg=18)
    # swellings on the bead (where ligaments pinch off) and the ligaments + droplets flung outward
    for k in range(n_fling):
        a = 2 * math.pi * (k + rnd.uniform(-0.35, 0.35)) / n_fling
        u = Vector((0, math.cos(a), math.sin(a)))
        base = u * 0.99
        mb.sphere(tuple(base), bead * rnd.uniform(1.15, 1.45), 14)
        L = rnd.uniform(0.04, 0.13)
        out = Vector((rnd.uniform(-0.06, 0.06), 0, 0))
        tip = base + u * L + out
        mb.tube(tuple(base + u * bead * 0.6), tuple(tip), bead * 0.45, seg=10, r2=bead * 0.15)
        mb.sphere(tuple(tip + u * 0.02), bead * rnd.uniform(0.4, 0.6), 12)
        if rnd.random() < 0.7:          # a detached droplet further out
            mb.sphere(tuple(base + u * (L + rnd.uniform(0.15, 0.35)) + out * 2), bead * rnd.uniform(0.35, 0.6), 10)
    ob = mb.obj("PancakeRimR16", mat)
    ob.parent = root
    return ob


# ---------------------------------------------------------------- de-gridded wall (#2)
MODULES = (
    ("turbo_gate", H11.turbo_gate, 0.5, 0.5),
    ("viewport_stack", H11.viewport_stack, 0.32, 0.62),
    ("bellows_spool", H12.bellows_spool, 0.55, 0.3),
    ("manifold", H11.manifold, 0.42, 0.45),
    ("gas_panel", H11.gas_panel, 0.5, 0.42),
    ("drag_chain", H11.drag_chain, 0.6, 0.32),
    ("ion_pump", H12.ion_pump, 0.42, 0.42),
    ("gate_valve", H12.gate_valve, 0.45, 0.42),
)


def _wall_frame(R, a, z, inset):
    o = Vector((math.cos(a), math.sin(a), 0))          # local +Y = outward (modules face local -Y = inward)
    X = Vector((math.sin(a), -math.cos(a), 0))         # X = Y x Z (right-handed)
    Z = Vector((0, 0, 1))
    m = Matrix((X, o, Z)).transposed().to_4x4()
    m.translation = o * (R - inset) + Vector((0, 0, z))
    return m


def wall_modules_r16(P, R, skip, seed=0, rows=(-0.72, 0.02, 0.74), step_deg=24.0, avoid=None, log=None):
    """Interleave nameable modules around the inside of the vessel wall (cylinder radius R, axis Z)."""
    rnd = random.Random(seed * 13 + 5)
    order = list(range(len(MODULES)))
    rnd.shuffle(order)
    i = 0
    for ri, z in enumerate(rows):
        a0 = rnd.uniform(0, step_deg) + ri * step_deg * 0.5
        a = a0
        while a < a0 + 360 - step_deg * 0.6:
            ar = math.radians(a)
            name, fn, w, h = MODULES[order[i % len(order)]]
            i += 1
            p = Vector((math.cos(ar) * R, math.sin(ar) * R, z))
            a += step_deg * rnd.uniform(0.85, 1.25)
            if skip(p) or (avoid is not None and avoid(p)):
                continue
            s = rnd.uniform(0.85, 1.1)
            T = H.new_parts()
            # machined pad plate on the wall behind every module (different depth per module)
            bd = rnd.choice((0.015, 0.03, 0.045))
            T["anod" if i % 2 else "blast"].box((0, -bd / 2, 0), (w * s * 1.05, bd, h * s * 1.05))
            try:
                fn(T, 0.0, 0.0, w * s, h * s, -bd, 1.0, rnd, rnd.uniform(0.55, 0.9))
            except Exception as e:           # a library builder that does not fit: leave the plain pad
                print("wall module skipped", name, e)
            mtx = _wall_frame(R, ar, z, 0.045)
            for mb in T.values():
                mb._resolve()
                for v in mb.bm.verts:
                    v.co = mtx @ v.co
            H11._merge(P, T)
            if log is not None:
                log.append(name)


# ---------------------------------------------------------------- ellipsoidal collector (#1)
def collector_r16(M, mirror_mat, vertex_x=-0.42, f2=2.6, R=0.74, hole_r=0.075):
    """Ellipsoid of revolution about X, first focus at the origin (plasma), second focus (IF) at x = f2.
    Returns (objects, rim_x)."""
    c = f2 / 2.0
    a = c - vertex_x                    # vertex at x = c - a
    b = math.sqrt(a * a - c * c)

    def ex(r):
        return c - a * math.sqrt(max(0.0, 1 - (r / b) ** 2))
    mb = K.MB()
    nr, na = 30, 192
    rows = []
    for i in range(nr + 1):
        r = hole_r + (R - hole_r) * i / nr
        rows.append([mb.bm.verts.new((ex(r), r * math.cos(2 * math.pi * j / na), r * math.sin(2 * math.pi * j / na)))
                     for j in range(na)])
    for i in range(nr):
        for j in range(na):
            k = (j + 1) % na
            mb.bm.faces.new((rows[i][j], rows[i][k], rows[i + 1][k], rows[i + 1][j])).smooth = True
    # back skin (shell thickness) so the dish edge reads as a thick blank
    back = []
    for i in (nr, 0):
        r = hole_r + (R - hole_r) * i / nr
        back.append([mb.bm.verts.new((ex(r) - 0.035, r * math.cos(2 * math.pi * j / na), r * math.sin(2 * math.pi * j / na)))
                     for j in range(na)])
    for j in range(na):
        k = (j + 1) % na
        mb.bm.faces.new((rows[nr][j], back[0][j], back[0][k], rows[nr][k]))
        mb.bm.faces.new((rows[0][k], back[1][k], back[1][j], rows[0][j]))
    mirror = mb.obj("CollectorR16", mirror_mat)
    rim_x = ex(R)
    rot = (0, math.radians(90), 0)
    rim, lip, cool = K.MB(), K.MB(), K.MB()
    rim.ring((rim_x - 0.03, 0, 0), R + 0.1, R + 0.004, 0.06, rot=rot, seg=192)
    rim.bolts((rim_x + 0.002, 0, 0), R + 0.055, 40, 0.009, 0.02, rot=rot)
    lip.ring((vertex_x - 0.01, 0, 0), hole_r + 0.02, hole_r - 0.002, 0.03, rot=rot, seg=64)
    bore = K.MB()                                       # dark laser feed bore behind the central hole
    bore.tube((vertex_x - 0.4, 0, 0), (vertex_x - 0.01, 0, 0), hole_r + 0.01, seg=48)
    for k in range(5):
        rr = 0.2 + k * 0.11
        cool.ring((ex(rr) - 0.05, 0, 0), rr + 0.012, rr, 0.03, rot=rot, seg=96)
    objs = [mirror, rim.obj("CollectorRimR16", M["alu"], bevel=0.003), lip.obj("CollectorLipR16", M["anod"]),
            cool.obj("CollectorCoolingR16", M["copper"]), bore.obj("CollectorBoreR16", M["hole"])]
    return objs, rim_x


def rim_lip_r16(M, objs, rim_x, light, R=0.74):
    """Thin polished lip torus on the collector's outer edge, light-linked to a plasma-site glint light: it shows
    the plasma's light all the way round as a continuous bright elliptical edge (the bowl's outline)."""
    M.setdefault("lip_pol", K.mat("CollectorLipPolishedR16", (0.92, 0.92, 0.94), metal=1.0, rough=0.08))
    mb = K.MB()
    na = 192
    pts = [Vector((rim_x + 0.004, (R + 0.006) * math.cos(2 * math.pi * j / na), (R + 0.006) * math.sin(2 * math.pi * j / na)))
           for j in range(na + 1)]
    mb.path(pts, 0.011, seg=14)
    lip = mb.obj("CollectorEdgeLipR16", M["lip_pol"])
    col = bpy.data.collections.new("RimGlintR16_Recv")
    col.objects.link(lip)
    light.light_linking.receiver_collection = col
    objs.append(lip)
    return lip
