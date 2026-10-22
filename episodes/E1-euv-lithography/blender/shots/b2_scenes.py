"""B2 — vacuum, hydrogen and debris. Variants (build(variant=...)):

  ions    B2_04  tin-ion "shrapnel": hundreds of tracks from the plasma hit the collector (F26)
  ions_h2 B2_06  same tracks slowed and stopped by a hydrogen buffer before the mirror (F27)
  bounce  B2_07  one ion caroming off H2 molecules and dying out short of the mirror
  micro   B2_05  SEM cross-section: tin deposits on / implants into / sputters the Mo/Si stack
  clean   B2_08  EUV splits H2 into radicals; four grab a tin atom; SnH4 lifts off (F27)
  air     B2_02  EUV dies within a short run of air; the vacuum vessel behind (F10)
  pumps   B2_09  stannane drifting along the vessel wall into turbo pumps (xray)
  glow    B2_11  a pulse along the scanner light path lights the ~5 Pa hydrogen into plasma (F28)
All illustrative (counts, sizes and speeds are not data).
"""
import math
import random

import bpy
from mathutils import Vector

import build_machine as BM
import build_source as S
import build_vacuum as V
import common as C
import materials as M
import sample_b1 as B
import styles

FRAMES = 300
ION_COLOR = (1.0, 0.72, 0.45)                 # tin-ion tracks: one warm hue, brighter = higher charge state
ION_DIM = (0.85, 0.4, 0.2)                    # the same ions slowed in hydrogen
H2_COLOR = (0.35, 0.85, 0.95)


def _curve(name, pts, mat, radius=0.006, role="emitter"):
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = radius
    sp = cu.splines.new("POLY")
    sp.points.add(len(pts) - 1)
    for i, p in enumerate(pts):
        sp.points[i].co = (*p, 1)
    ob = bpy.data.objects.new(name, cu)
    bpy.context.scene.collection.objects.link(ob)
    ob.data.materials.append(mat)
    styles.tag(ob, role)
    return ob


def _sphere(name, r, mat, loc, role="emitter", seg=16):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, segments=seg, ring_count=seg // 2, location=loc)
    ob = bpy.context.object
    ob.name = name
    ob.data.materials.append(mat)
    styles.tag(ob, role)
    return ob


def _key(ob, f, **kw):
    for k, v in kw.items():
        setattr(ob, k, v)
        ob.keyframe_insert(k, frame=f)


def _mirror_hit(d):
    """Distance from the plasma (focus) to the collector along unit direction d, or None."""
    c = S.IF_X / 2
    a = c - S.COLLECTOR_VERTEX_X
    b2 = a * a - c * c
    r = b2 / (a - c * d.x)
    p = d * r
    if p.x > S.COLLECTOR_RIM_X or (p.y ** 2 + p.z ** 2) ** 0.5 < S.COLLECTOR_HOLE_R:
        return None
    return r


def _dash(ob, f0, f1, lag):
    """Key a travelling dash along a curve: the head runs f0 -> f1, the tail follows `lag` frames behind, so the
    track fades out behind the ion instead of staying drawn (the old tracks piled into a static starburst)."""
    for attr, keys in (("bevel_factor_end", ((f0, 0.0), (f1, 1.0))),
                       ("bevel_factor_start", ((f0 + lag, 0.0), (f1 + lag, 1.0)))):
        for f, v in keys:
            setattr(ob.data, attr, v)
            ob.data.keyframe_insert(attr, frame=f)
    for fc in C.fcurves(ob.data.animation_data.action):
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR"


def ions(sc, rnd, buffer=False, n=520):
    S.collector()
    S.collector_housing()
    core = _sphere("PlasmaCore", 0.18, M.emission("Core", (0.9, 0.85, 1.0), 25.0), (0, 0, 0))
    # one hue; brightness rises with the charge state (for ions of the same energy-over-charge, the higher charged
    # ones carry more energy, Poirier 2022), so a brighter track never means a weaker ion
    mats = [M.emission(f"Ion{q}", ION_COLOR, 1.6 + 0.6 * q) for q in range(8)]
    dim = [M.emission(f"IonDim{q}", tuple(v * 0.6 for v in ION_DIM), 0.8 + 0.25 * q) for q in range(8)]
    spark = M.emission("Spark", (1.0, 0.8, 0.5), 18.0)
    h2 = M.emission("H2", H2_COLOR, 2.0)
    made = 0
    while made < n:
        d = Vector((rnd.uniform(-1, -0.05), rnd.uniform(-1, 1), rnd.uniform(-1, 1))).normalized()
        r = _mirror_hit(d)
        if r is None:
            continue
        q = rnd.randrange(8)
        f0 = int(rnd.uniform(-10, 140))             # the source fires 60,000 times a second: tracks keep coming
        if not buffer:
            ob = _curve(f"Track{made}", [(0, 0, 0), tuple(d * r)], mats[q], radius=0.008)
            _dash(ob, f0, f0 + 10, 4)
            if made % 4 == 0:                       # impact on the mirror
                sp = _sphere(f"Spark{made}", 0.035, spark, tuple(d * r * 0.995), seg=8)
                _key(sp, -20, scale=(0, 0, 0))
                _key(sp, f0 + 10, scale=(0, 0, 0))
                _key(sp, f0 + 11, scale=(1.2, 1.2, 1.2))
                _key(sp, f0 + 15, scale=(0, 0, 0))
        else:
            # slowed in the hydrogen: a tin ion (119 u) hitting H2 (2 u) is deflected by about 1 deg at most per
            # collision, so the track stays straight, dims and stops short of the mirror
            # (research/visual/B2_sources.md)
            stop = r * rnd.uniform(0.35, 0.82)
            mid = d * (stop * 0.5)
            a_ = _curve(f"TrackA{made}", [(0, 0, 0), tuple(mid)], mats[q], radius=0.007)
            b_ = _curve(f"TrackB{made}", [tuple(mid), tuple(d * stop)], dim[q], radius=0.006)
            _dash(a_, f0, f0 + 8, 4)
            _dash(b_, f0 + 8, f0 + 22, 6)              # slower in the gas, then gone short of the mirror
        made += 1
    if buffer:
        # hydrogen molecules as small cyan dumbbells, drifting away from the mirror with the gas flow
        # (Fomenkov 2017 slide 34: "Hydrogen flow away from collector")
        for k in range(900):
            d = Vector((rnd.uniform(-1, 0.2), rnd.uniform(-1, 1), rnd.uniform(-1, 1))).normalized()
            rr = rnd.uniform(1.0, 5.5)
            c = d * rr
            ax = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-1, 1))).normalized() * 0.03
            drift = Vector((rnd.uniform(0.5, 0.9), rnd.uniform(-0.1, 0.1), rnd.uniform(-0.1, 0.1)))
            for s_ in (-1, 1):
                hb = _sphere(f"H{k}{s_}", 0.022, h2, tuple(c + ax * s_), seg=8)
                _key(hb, 1, location=hb.location.copy())
                _key(hb, 160, location=hb.location + drift)
                for fc in C.fcurves(hb.animation_data.action):
                    for kp in fc.keyframe_points:
                        kp.interpolation = "LINEAR"
    B._camera("CamB2_04", [(1, (-1.5, 0, 0), (7.5, 8.5, 4.0), 24, 11.0),
                           (150, (-1.5, 0, 0), (9.5, 5.0, 5.5), 24, 11.0)])
    B._camera("CamB2_06", [(1, (-1.5, 0, 0), (7.5, 8.5, 4.0), 24, 11.0),
                           (163, (-1.5, 0, 0), (9.8, 4.6, 5.6), 24, 11.0)])
    return core


def bounce(sc, rnd):
    h2 = M.emission("H2", H2_COLOR, 3.0)
    flash = M.emission("H2Flash", (0.7, 1.0, 1.0), 0.0)
    # the mirror face at x = -1.55, just beyond where the ion stops (x = -1.19), so both are in frame at the end
    # (a plane at x = -3.2 was edge-on and outside the final frame). In the energy view it is a faint cyan sheet
    # with a bright metrology-cyan outline
    bpy.ops.mesh.primitive_plane_add(size=2.6, location=(-1.55, 0, 0), rotation=(0, math.pi / 2, 0))
    m = bpy.context.object
    m.name = "BounceMirror"
    m.data.materials.append(M.emission("MirrorSheet", (0.08, 0.45, 0.7), 0.045))
    styles.tag(m, "emitter")
    h = 1.3
    _curve("MirrorEdge", [(-1.55, -h, -h), (-1.55, h, -h), (-1.55, h, h), (-1.55, -h, h), (-1.55, -h, -h)],
           M.emission("MirrorEdge", (0.15, 0.8, 1.0), 4.0), radius=0.008)
    ion_mat = M.emission("Ion", (1.0, 0.75, 0.45), 40.0)
    ion = _sphere("Ion", 0.025, ion_mat, (2.8, 0.2, 0.0))
    # a heavy tin ion barely deviates from a straight line (<= ~1 deg per collision with H2); it loses
    # speed at each collision and stops before the mirror, while each light H2 molecule is knocked away
    path = [Vector((2.8 - 4.2 * u, 0.2 - 0.18 * u, 0.0)) for u in (0.0, 0.32, 0.56, 0.74, 0.87, 0.95)]
    times = [1, 14, 30, 48, 66, 84]                     # longer and longer between collisions: decelerating
    for k, (p, f) in enumerate(zip(path, times)):
        _key(ion, f, location=tuple(p))
        if 0 < k < len(path) - 1:                       # an H2 molecule at every collision, knocked away
            off = Vector((0, 0.07, 0))
            kick = Vector((rnd.uniform(-0.4, 0.2), rnd.choice((-1, 1)) * rnd.uniform(0.6, 1.0), rnd.uniform(-0.4, 0.4)))
            for s_ in (-1, 1):
                hb = _sphere(f"HB{k}{s_}", 0.035, h2, tuple(p + off * s_ + Vector((0.06, 0, 0))), seg=12)
                _key(hb, f, location=hb.location.copy())
                _key(hb, f + 30, location=hb.location + kick * 1.6)
            fl = _sphere(f"Flash{k}", 0.05, flash, tuple(p), seg=12)
            _key(fl, 1, scale=(0, 0, 0))
            _key(fl, f - 1, scale=(0, 0, 0))
            _key(fl, f, scale=(1.0, 1.0, 1.0))
            _key(fl, f + 6, scale=(0, 0, 0))
    M.set_emission_strength(flash, 1, 10.0)
    s = ion_mat.node_tree.nodes["Emission"].inputs["Strength"]
    for f, v in ((1, 14), (34, 8), (64, 4), (80, 2), (FRAMES, 0.5)):
        s.default_value = v
        s.keyframe_insert("default_value", frame=f)
    # the trail follows the ion and keeps only the last leg, so it visibly shortens as the ion slows
    trail = _curve("Trail", [tuple(path[0]), tuple(path[-1])], M.emission("Trail", (1.0, 0.6, 0.3), 3.0), radius=0.006)
    us = [(p - path[0]).length / (path[-1] - path[0]).length for p in path]
    for k, f in enumerate(times):
        trail.data.bevel_factor_end = us[k]
        trail.data.keyframe_insert("bevel_factor_end", frame=f)
        trail.data.bevel_factor_start = us[max(0, k - 1)]
        trail.data.keyframe_insert("bevel_factor_start", frame=f)
    trail.data.bevel_factor_start = us[-1] - 0.01
    trail.data.keyframe_insert("bevel_factor_start", frame=times[-1] + 14)
    B._camera("CamB2_07", [(1, (2.0, 0.1, 0.0), (2.4, 2.4, 0.4), 65, 4.0),
                           (84, (-0.95, 0.05, 0.0), (-0.55, 3.1, 0.55), 65, 4.0)])


def multilayer(sc, n_pairs=10, width=7.0, depth=2.0, t=0.18):
    """Alternating Mo (dark) / Si (light) layers seen in cross-section, under a thin protective capping layer
    (collectors carry "special collector capping layers", Fomenkov 2017 p.182); top surface at z=0."""
    mo = M.principled("Mo", (0.2, 0.2, 0.2), roughness=0.5)
    si = M.principled("Si", (0.6, 0.6, 0.6), roughness=0.5)
    cap = M.principled("Cap", (0.75, 0.72, 0.6), roughness=0.4)
    bpy.ops.mesh.primitive_cube_add(location=(0, 0, -t * 0.35))
    cl = bpy.context.object
    cl.name = "CappingLayer"
    cl.scale = (width / 2, depth / 2, t * 0.35 * 0.98)
    cl.data.materials.append(cap)
    styles.tag(cl, "structure")
    cl["sem_tone"] = 0.75
    z = -t * 0.7
    for k in range(2 * n_pairs):
        # Mo thinner than Si: measured ~2.1 nm Mo / ~3.7 nm Si (Liu 2023; Gamma ~0.4, research/visual/B4B5_sources.md)
        tk = t * (0.8 if k % 2 == 0 else 1.2)
        bpy.ops.mesh.primitive_cube_add(location=(0, 0, z - tk / 2))
        lay = bpy.context.object
        lay.name = f"{'Mo' if k % 2 == 0 else 'Si'}Layer{k}"
        lay.scale = (width / 2, depth / 2, tk / 2 * 0.98)
        lay.data.materials.append(mo if k % 2 == 0 else si)
        styles.tag(lay, "structure")
        lay["sem_tone"] = 0.45 if k % 2 == 0 else 1.0
        z -= tk


def micro(sc, rnd):
    multilayer(sc)
    sn = M.principled("SnAtom", (0.9, 0.9, 0.9), roughness=0.3)
    # every atom lands on the cut face of the stack (y = -1, the section plane the camera looks at), so an implanted
    # atom shows in cross-section instead of disappearing inside the opaque layers
    face_y = -1.0 + 0.03
    for k in range(60):
        x = rnd.uniform(-2.8, 2.8)
        f = 4 + int(k * 1.8)
        fate = rnd.random()
        a = _sphere(f"Sn{k}", 0.07, sn, (x, face_y, 2.2), role="structure", seg=16)
        a["sem_tone"] = 1.3
        _key(a, f, location=(x + rnd.uniform(-0.3, 0.3), face_y, 2.2))
        if fate < 0.6:           # deposit: a growing grey crust on top
            _key(a, f + 10, location=(x, face_y, 0.07 + 0.11 * (k % 3)))
        elif fate < 0.85:        # implant into the top layers
            _key(a, f + 10, location=(x, face_y, -rnd.uniform(0.15, 0.5)))
        else:                    # sputter: knocks a surface atom out
            _key(a, f + 10, location=(x, face_y, 0.05))
            b = _sphere(f"Sput{k}", 0.06, sn, (x + 0.1, face_y, -0.05), role="structure", seg=12)
            b["sem_tone"] = 0.8
            _key(b, f + 10, location=(x + 0.1, face_y, -0.05))
            _key(b, f + 30, location=(x + rnd.uniform(-1.2, 1.2), face_y, 1.6))
    # about a third of the frame above the surface so the atoms are seen arriving (they were cut by the top edge)
    B._camera("CamB2_05", [(1, (0, 0, -0.45), (0.0, -17.0, -0.25), 100, 11.0),
                           (130, (0, 0, -0.4), (0.0, -15.0, -0.2), 100, 11.0)])


def clean(sc, rnd):
    multilayer(sc)
    sn = M.principled("SnAtom", (0.9, 0.9, 0.9), roughness=0.3)
    hmat = M.principled("H", (0.95, 0.95, 0.95), roughness=0.3)
    crust = [(x, y) for x in (-1.8, -0.9, 0.0, 0.9, 1.8) for y in (-0.3, 0.3)]
    for k, (x, y) in enumerate(crust):
        a = _sphere(f"Sn{k}", 0.08, sn, (x, y, 0.08), role="structure")
        a["sem_tone"] = 1.3
        f_grab = 80 + 12 * k
        tetra = [Vector((1, 1, 1)), Vector((1, -1, -1)), Vector((-1, 1, -1)), Vector((-1, -1, 1))]
        hs = []
        for j, v in enumerate(tetra):
            h = _sphere(f"H{k}_{j}", 0.035, hmat, (x + rnd.uniform(-1.5, 1.5), y, 2.6), role="structure", seg=12)
            h["sem_tone"] = 1.6
            _key(h, 30 + 3 * j, location=h.location.copy())
            _key(h, f_grab, location=(x + v.x * 0.1, y + v.y * 0.1, 0.08 + v.z * 0.1))
            hs.append((h, v))
        lift = rnd.uniform(1.8, 3.2)
        _key(a, f_grab, location=(x, y, 0.08))
        _key(a, f_grab + 70, location=(x + rnd.uniform(-0.4, 0.4), y, lift))
        for h, v in hs:
            _key(h, f_grab + 70, location=(a.location.x + v.x * 0.1, y + v.y * 0.1, lift + v.z * 0.1))
    B._camera("CamB2_08", [(1, (0, 0, 0.6), (0.0, -8.0, 0.9), 70, 11.0),          # wide enough to keep the
                           (262, (0, 0, 1.4), (0.0, -9.0, 1.7), 70, 11.0)])        # rising SnH4 in frame


PORT_X = -4.6                                            # pumping ports on the drum, near its back wall
PORT_ANGLES = (25.0, 70.0, 115.0)                        # around the axis, from +Y toward +Z (deg)


def _port_dir(ang):
    a = math.radians(ang)
    return Vector((0.0, math.cos(a), math.sin(a)))


def _pump_ports(r_vessel=15.0):
    """Generic pumping ports on the vessel drum: a flanged duct and a plain pump housing outside it. Type, count
    and position of the real pumps are not public (示意); drawn opaque so they read in the x-ray view."""
    steel = M.polished_steel("PumpSteel", 0.3)
    dark = M.principled("PumpBody", (0.18, 0.2, 0.24), metallic=0.6, roughness=0.4)
    out = []
    for k, ang in enumerate(PORT_ANGLES):
        d = _port_dir(ang)
        rot = d.to_track_quat("Z", "Y").to_euler()
        base = Vector((PORT_X, 0, 0))
        for nm, rr, depth, rad, mat in (("Duct", r_vessel + 1.0, 2.6, 1.15, steel),
                                        ("Pump", r_vessel + 3.4, 2.4, 1.75, dark)):
            bpy.ops.mesh.primitive_cylinder_add(radius=rad, depth=depth, vertices=48, location=tuple(base + d * rr),
                                                rotation=rot)
            ob = bpy.context.object
            ob.name = f"Port{nm}{k}"
            ob.data.materials.append(mat)
            styles.tag(ob, "structure")
        bpy.ops.mesh.primitive_torus_add(major_radius=1.45, minor_radius=0.16, major_segments=48, minor_segments=10,
                                         location=tuple(base + d * (r_vessel + 0.15)), rotation=rot)
        fl = bpy.context.object
        fl.name = f"PortFlange{k}"
        fl.data.materials.append(steel)
        styles.tag(fl, "structure")
        out.append(base + d * r_vessel)
    return out


def _smooth_curve(name, pts, mat, radius, role="emitter"):
    """A NURBS stream through pts (order 4, clamped ends): smooth, no V-shaped kinks."""
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = radius
    cu.bevel_resolution = 3
    cu.resolution_u = 24
    sp = cu.splines.new("NURBS")
    sp.points.add(len(pts) - 1)
    for i, p in enumerate(pts):
        sp.points[i].co = (*p, 1)
    sp.order_u = min(4, len(pts))
    sp.use_endpoint_u = True
    ob = bpy.data.objects.new(name, cu)
    bpy.context.scene.collection.objects.link(ob)
    ob.data.materials.append(mat)
    styles.tag(ob, role)
    return ob


def _stannane_flow(rnd, ports, f_first, f_last, per_port=7):
    """Stannane carried off the mirror region by the gas flow, along the wall and into the pumping ports
    (Fomenkov 2017 slide 34: flow from the collector surface; exhaust positions not public). Each stream is a
    short travelling dash (start follows end), so the gas visibly flows instead of standing as lines."""
    flow = M.emission("Stannane", (0.34, 0.37, 0.47), 1.0)      # grey streams that read on the light x-ray backdrop
    span = f_last - f_first
    for k, mouth in enumerate(ports):
        d = Vector((0.0, mouth.y, mouth.z)).normalized()
        for j in range(per_port):
            jit = Vector((0.0, rnd.uniform(-1, 1), rnd.uniform(-1, 1))) * 1.2
            th = math.atan2(d.z, d.y) + rnd.uniform(-0.35, 0.35)
            dd = Vector((0.0, math.cos(th), math.sin(th)))
            pts = [Vector((rnd.uniform(-2.8, -1.6), 0, 0)) + dd * rnd.uniform(4.5, 6.5),   # off the mirror face
                   Vector((rnd.uniform(-0.5, 0.8), 0, 0)) + dd * rnd.uniform(8.5, 10.0),
                   Vector((PORT_X + 1.8, 0, 0)) + dd * 13.2 + jit * 0.5,
                   mouth + d * (-0.6) + jit * 0.3,
                   mouth + d * 2.2]
            ob = _smooth_curve(f"Flow{k}_{j}", [tuple(p) for p in pts], flow, radius=0.26)
            f0 = f_first + int(span * j / per_port) + int(rnd.uniform(-2, 2))
            for attr, keys in (("bevel_factor_end", ((f0, 0.0), (f0 + 30, 1.0))),
                               ("bevel_factor_start", ((f0 + 14, 0.0), (f0 + 44, 1.0)))):
                for f, v in keys:
                    setattr(ob.data, attr, v)
                    ob.data.keyframe_insert(attr, frame=f)
            for fc in C.fcurves(ob.data.animation_data.action):
                for kp in fc.keyframe_points:
                    kp.interpolation = "LINEAR"


def _source_light_path(n=90, seed=4, draw=None):
    """Collector, violet rays plasma -> collector -> IF (role rays: violet in x-ray), IF plate and a small
    plasma core, for the x-ray views of the vessel. draw=(f0, f1) draws the rays on."""
    S.collector()
    S.collector_housing()
    rays, _ = S.light_rays(n=n, seed=seed)
    S.intermediate_focus()
    _sphere("PlasmaCoreX", 0.3, M.emission("PlasmaCoreX", (0.5, 0.2, 1.0), 4.0), (0, 0, 0))
    if draw:
        for r in rays:
            r.data.bevel_factor_end = 0.0
            r.data.keyframe_insert("bevel_factor_end", frame=draw[0])
            r.data.bevel_factor_end = 1.0
            r.data.keyframe_insert("bevel_factor_end", frame=draw[1])
    return rays


def pumps(sc, rnd):
    V.source_vessel()
    _source_light_path()
    ports = _pump_ports()
    _stannane_flow(rnd, ports, -40, 60, per_port=14)          # already flowing at frame 1, still at the end
    B._camera("CamB2_09", [(1, (-1.0, 0, 6.0), (30.0, 30.0, 18.0), 30, 11.0),
                           (72, (-1.0, 0, 6.0), (36.0, 34.0, 21.0), 30, 11.0)])


def _surface_beam(name, radius, x_from, x_to, loc, live=2.2):
    """B2_02: the EUV beam in the air tube as an opaque violet surface (on the light x-ray backdrop an emissive
    volume only adds light and turns white-lavender). It is bright where it enters and dies within `live` units;
    its front is keyed through the node 'Front' (local z)."""
    length = x_to - x_from
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=length, vertices=48, location=loc,
                                        rotation=(0, math.pi / 2, 0))
    ob = bpy.context.object
    ob.name = name
    m = bpy.data.materials.new(name + "Mat")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.remove(nt.nodes["Principled BSDF"])
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sep.inputs[0])
    fade = nt.nodes.new("ShaderNodeMapRange")            # absorbed along the run: 1 at the entry, 0 after `live`
    fade.inputs["From Min"].default_value = -length / 2
    fade.inputs["From Max"].default_value = -length / 2 + live
    fade.inputs["To Min"].default_value = 1.0
    fade.inputs["To Max"].default_value = 0.0
    nt.links.new(sep.outputs["Z"], fade.inputs["Value"])
    front = nt.nodes.new("ShaderNodeMapRange")           # 1 behind the front, 0 ahead of it
    front.name = "Front"
    front.inputs["From Min"].default_value = -length / 2
    front.inputs["From Max"].default_value = -length / 2 - 0.3
    nt.links.new(sep.outputs["Z"], front.inputs["Value"])
    mul = nt.nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    nt.links.new(fade.outputs["Result"], mul.inputs[0])
    nt.links.new(front.outputs["Result"], mul.inputs[1])
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (0.30, 0.06, 1.0, 1)
    em.inputs["Strength"].default_value = 1.3
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(mul.outputs[0], mix.inputs["Fac"])
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(em.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
    m.surface_render_method = "BLENDED"
    ob.data.materials.append(m)
    styles.tag(ob, "emitter")
    return ob, front, length


def air(sc, rnd):
    V.source_vessel()
    # after the first clause the vessel's own light path draws on: collector, rays to the IF, pumping ports
    _source_light_path(draw=(66, 100))
    _pump_ports()
    glass = M.principled("TubeGlass", (0.9, 0.95, 1.0), roughness=0.05)
    bpy.ops.mesh.primitive_cylinder_add(radius=1.2, depth=12, vertices=64, location=(10, -30, 4),
                                        rotation=(0, math.pi / 2, 0))
    tube = bpy.context.object
    tube.name = "AirTube"
    tube.data.materials.append(glass)
    styles.tag(tube, "shell")
    # attenuation: the beam lives only over its first ~2 units (EUV is absorbed within a short path; 示意)
    beam, front, blen = _surface_beam("EUVinAir", 0.18, 4.0, 16.0, (10, -30, 4))
    for f, z in ((1, -blen / 2), (6, -blen / 2), (22, blen / 2)):
        front.inputs["From Min"].default_value = z
        front.inputs["From Max"].default_value = z - 0.3
        front.inputs["From Min"].keyframe_insert("default_value", frame=f)
        front.inputs["From Max"].keyframe_insert("default_value", frame=f)
    air_mat = M.principled("AirMol", (0.22, 0.26, 0.34), roughness=0.5)
    for k in range(40):                                     # air molecules
        _sphere(f"Air{k}", 0.06, air_mat,
                (rnd.uniform(4.5, 15.5), -30 + rnd.uniform(-0.9, 0.9), 4 + rnd.uniform(-0.9, 0.9)), role="structure",
                seg=8)
    # first clause: looking down onto the tube, the vessel out of frame (behind it, it cluttered the picture);
    # then pull back and up until the whole vessel with its light path is in view, the dead tube in the foreground
    B._camera("CamB2_02", [(1, (9.0, -30, 4), (8.5, -38.5, 13.5), 35, 11.0),
                           (62, (8.5, -29, 4), (9.0, -40.5, 15.0), 35, 11.0),
                           (156, (2.0, -8, 3.0), (32.0, -50.0, 20.0), 35, 11.0)])


def glow(sc, rnd):
    BM.machine()
    for ob in list(bpy.data.objects):          # camera is inside the scanner: drop the housings
        if ob.get("role") == "shell":
            ob.hide_render = True
    # the glow follows the beam envelope: a cone on every leg whose radius at each end is the beam's footprint
    # there - wide on the mirrors (about 0.7 of each mirror's radius), pinched at the foci (IF, the intermediate
    # image above M6, the wafer) - plus a fainter halo cone around it ("plasma accumulation beyond the beam
    # confines", van de Kerkhof 2021 Fig. 4b). Footprint sizes are illustrative (示意).
    foot = {BM.COLLECTOR: 0.6, BM.IF: 0.03, BM.FOLD: 0.14, BM.FACET1: 0.32, BM.FACET2: 0.11, BM.RETICLE: 0.16,
            BM.PO_MIRRORS[0]: 0.14, BM.PO_MIRRORS[1]: 0.21, BM.PO_MIRRORS[2]: 0.28, BM.PO_MIRRORS[3]: 0.14,
            BM.PO_FOCUS: 0.03, BM.M5_HIT: 0.2, BM.M6_HIT: 0.5, BM.WAFER: 0.03}
    vol = M.volume_glow("H2Plasma", (0.42, 0.2, 1.0), density=0.0, emission_strength=0.0)
    halo = M.volume_glow("H2PlasmaHalo", (0.4, 0.18, 1.0), density=0.0, emission_strength=0.0)
    for i in range(len(BM.PATH) - 1):
        a, b = Vector(BM.PATH[i]), Vector(BM.PATH[i + 1])
        mid, d = (a + b) / 2, (b - a)
        ra, rb = foot.get(BM.PATH[i], 0.1), foot.get(BM.PATH[i + 1], 0.1)
        for mat, k, nm in ((vol, 1.0, "Glow"), (halo, 1.7, "Halo")):
            # primitive cone: radius1 at local -Z (the start, a), radius2 at +Z (the end, b)
            bpy.ops.mesh.primitive_cone_add(vertices=48, radius1=ra * k + 0.01, radius2=rb * k + 0.01, depth=d.length,
                                            location=mid)
            ob = bpy.context.object
            ob.name = f"H2{nm}{i}"
            ob.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
            ob.data.materials.append(mat)
            styles.tag(ob, "emitter")
    # the EUV pulses come 60,000 times a second (F2), so the hydrogen plasma they leave is a quasi-steady glow
    # that follows the beam (van de Kerkhof et al. 2021), not one flash dying away
    for f, e in ((1, 0.0), (30, 0.0), (48, 0.28), (FRAMES, 0.28)):      # faint: "淡淡的" (ionisation is tiny)
        M.set_volume_strength(vol, f, emission_strength=e)
        M.set_volume_strength(halo, f, emission_strength=e * 0.2)
    lp = bpy.data.objects.get("LightPath")
    if lp:
        lmat = lp.data.materials[0]
        for f, e in ((1, 0.0), (30, 0.0), (48, 8.0), (FRAMES, 8.0)):
            M.set_emission_strength(lmat, f, e)
    B._area("GlowKey", (BM.CENTER[0], -6, 6), (0.8, 0, 0), 8, 120, (0.6, 0.7, 1.0))
    f2, ret = BM.FACET2, BM.RETICLE
    B._camera("CamB2_11", [(1, f2, (f2[0] + 1.6, -3.4, f2[2] - 0.4), 35, 4.0),
                           (156, ret, (ret[0] + 1.0, -3.6, ret[2] - 0.9), 35, 4.0)])


def build(variant="ions", seed=11):
    sc = C.reset_scene(FRAMES)
    C.set_world(top=(0.01, 0.012, 0.02), horizon=(0.004, 0.005, 0.008), bottom=(0.001, 0.001, 0.002))
    C.set_color_management(exposure=0.4)
    rnd = random.Random(seed)
    {"ions": lambda: ions(sc, rnd), "ions_h2": lambda: ions(sc, rnd, buffer=True),
     "bounce": lambda: bounce(sc, rnd), "micro": lambda: micro(sc, rnd), "clean": lambda: clean(sc, rnd),
     "pumps": lambda: pumps(sc, rnd), "air": lambda: air(sc, rnd), "glow": lambda: glow(sc, rnd)}[variant]()
    return sc


def after_style(style, shot_id):
    """Energy shots B2_04/B2_06: the collector as a bright metrology-cyan outline (the default faint blue rim was
    barely visible). SEM shots: Mo layers darker than Si; atoms brighter (sem_tone scales the emission)."""
    if style == "energy" and shot_id in ("B2_04", "B2_06"):
        rim = styles.dark_rim("CollectorRimB2", color=(0.15, 0.8, 1.0), strength=6.0)
        for ob in bpy.data.objects:
            if ob.type == "MESH" and ob.name.startswith(("Collector", "CollectorRing")):
                styles._set_material(ob, rim)
        return
    if style != "sem":
        return
    import styles as St
    for ob in bpy.data.objects:
        tone = ob.get("sem_tone")
        if tone is None or ob.type != "MESH":
            continue
        m = St.sem_material(f"SEM_{tone}")
        m.node_tree.nodes["Emission"].inputs["Strength"].default_value = tone
        ob.data.materials.clear()
        ob.data.materials.append(m)
