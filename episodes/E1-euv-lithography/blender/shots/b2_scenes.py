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
ION_COLORS = [(1.0, 0.95, 0.9), (1.0, 0.85, 0.7), (1.0, 0.72, 0.5), (1.0, 0.6, 0.35),
              (0.95, 0.5, 0.25), (0.85, 0.4, 0.2), (0.7, 0.3, 0.15), (0.55, 0.22, 0.12)]
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


def ions(sc, rnd, buffer=False, n=520):
    S.collector()
    S.collector_housing()
    core = _sphere("PlasmaCore", 0.18, M.emission("Core", (0.9, 0.85, 1.0), 25.0), (0, 0, 0))
    mats = [M.emission(f"Ion{q}", ION_COLORS[q], 6.0 - 0.5 * q) for q in range(8)]
    dim = [M.emission(f"IonDim{q}", tuple(v * 0.5 for v in ION_COLORS[q]), 1.2) for q in range(8)]
    spark = M.emission("Spark", (1.0, 0.8, 0.5), 30.0)
    h2 = M.emission("H2", H2_COLOR, 2.0)
    made = 0
    while made < n:
        d = Vector((rnd.uniform(-1, -0.05), rnd.uniform(-1, 1), rnd.uniform(-1, 1))).normalized()
        r = _mirror_hit(d)
        if r is None:
            continue
        q = rnd.randrange(8)
        f0 = 4 + int(rnd.uniform(0, 30))
        if not buffer:
            ob = _curve(f"Track{made}", [(0, 0, 0), tuple(d * r)], mats[q], radius=0.006 + 0.002 * (7 - q))
            ob.data.bevel_factor_end = 0.0
            ob.data.keyframe_insert("bevel_factor_end", frame=f0)
            ob.data.bevel_factor_end = 1.0
            ob.data.keyframe_insert("bevel_factor_end", frame=f0 + 10)
            if made % 4 == 0:                       # impact spark on the mirror
                sp = _sphere(f"Spark{made}", 0.05, spark, tuple(d * r * 0.995), seg=8)
                _key(sp, 1, scale=(0, 0, 0))
                _key(sp, f0 + 10, scale=(0, 0, 0))
                _key(sp, f0 + 11, scale=(1.4, 1.4, 1.4))
                _key(sp, f0 + 16, scale=(0, 0, 0))
        else:
            # deflected, shortened tracks: bright first leg, dim tail, dying out before the mirror
            stop = r * rnd.uniform(0.35, 0.82)
            pts, p, dirn = [Vector((0, 0, 0))], Vector((0, 0, 0)), d.copy()
            legs = 4
            for k in range(legs):
                p = p + dirn * (stop / legs)
                pts.append(p.copy())
                dirn = (dirn + Vector((rnd.gauss(0, 0.5), rnd.gauss(0, 0.5), rnd.gauss(0, 0.5)))).normalized()
            a_ = _curve(f"TrackA{made}", [tuple(v) for v in pts[:3]], mats[q], radius=0.005)
            b_ = _curve(f"TrackB{made}", [tuple(v) for v in pts[2:]], dim[q], radius=0.004)
            for ob, (fa, fb) in ((a_, (f0, f0 + 8)), (b_, (f0 + 8, f0 + 20))):
                ob.data.bevel_factor_end = 0.0
                ob.data.keyframe_insert("bevel_factor_end", frame=fa)
                ob.data.bevel_factor_end = 1.0
                ob.data.keyframe_insert("bevel_factor_end", frame=fb)
        made += 1
    if buffer:
        for k in range(900):                         # hydrogen molecules as small cyan dumbbells
            d = Vector((rnd.uniform(-1, 0.2), rnd.uniform(-1, 1), rnd.uniform(-1, 1))).normalized()
            rr = rnd.uniform(1.0, 5.5)
            c = d * rr
            ax = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-1, 1))).normalized() * 0.03
            for s_ in (-1, 1):
                _sphere(f"H{k}{s_}", 0.022, h2, tuple(c + ax * s_), seg=8)
    B._camera("CamB2_04", [(1, (-1.5, 0, 0), (7.5, 8.5, 4.0), 24, 11.0),
                           (150, (-1.5, 0, 0), (9.5, 5.0, 5.5), 24, 11.0)])
    B._camera("CamB2_06", [(1, (-1.5, 0, 0), (7.5, 8.5, 4.0), 24, 11.0),
                           (163, (-1.5, 0, 0), (9.8, 4.6, 5.6), 24, 11.0)])
    return core


def bounce(sc, rnd):
    h2 = M.emission("H2", H2_COLOR, 3.0)
    flash = M.emission("H2Flash", (0.7, 1.0, 1.0), 0.0)
    mirror = M.multilayer_mirror("Mirror", r_max=3.0)
    bpy.ops.mesh.primitive_plane_add(size=6, location=(-3.2, 0, 0), rotation=(0, math.pi / 2, 0))
    m = bpy.context.object
    m.data.materials.append(mirror)
    styles.tag(m, "structure")
    ion_mat = M.emission("Ion", (1.0, 0.75, 0.45), 40.0)
    ion = _sphere("Ion", 0.025, ion_mat, (2.8, 0.2, 0.0))
    path = [Vector((2.8, 0.2, 0.0)), Vector((1.6, -0.15, 0.1)), Vector((0.7, 0.35, -0.12)),
            Vector((-0.4, -0.2, 0.15)), Vector((-1.4, 0.15, -0.05)), Vector((-2.25, 0.05, 0.0))]
    times = [1, 18, 34, 50, 64, 80]
    for k, (p, f) in enumerate(zip(path, times)):
        _key(ion, f, location=tuple(p))
        if 0 < k < len(path) - 1:                       # an H2 molecule at every collision
            off = Vector((0, 0.07, 0))
            for s_ in (-1, 1):
                _sphere(f"HB{k}{s_}", 0.035, h2, tuple(p + off * s_ + Vector((0.06, 0, 0))), seg=12)
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
    trail = _curve("Trail", [tuple(p) for p in path], M.emission("Trail", (1.0, 0.6, 0.3), 3.0), radius=0.006)
    trail.data.bevel_factor_end = 0.0
    trail.data.keyframe_insert("bevel_factor_end", frame=1)
    trail.data.bevel_factor_end = 1.0
    trail.data.keyframe_insert("bevel_factor_end", frame=80)
    B._camera("CamB2_07", [(1, (2.0, 0.1, 0.0), (2.4, 2.4, 0.4), 65, 4.0),
                           (84, (-1.8, 0.0, 0.0), (-1.2, 2.2, 0.4), 65, 4.0)])


def multilayer(sc, n_pairs=10, width=6.0, depth=2.0, t=0.18):
    """Alternating Mo (dark) / Si (light) layers seen in cross-section; top surface at z=0."""
    mo = M.principled("Mo", (0.2, 0.2, 0.2), roughness=0.5)
    si = M.principled("Si", (0.6, 0.6, 0.6), roughness=0.5)
    z = 0.0
    for k in range(2 * n_pairs):
        bpy.ops.mesh.primitive_cube_add(location=(0, 0, z - t / 2))
        lay = bpy.context.object
        lay.name = f"{'Mo' if k % 2 == 0 else 'Si'}Layer{k}"
        lay.scale = (width / 2, depth / 2, t / 2 * 0.98)
        lay.data.materials.append(mo if k % 2 == 0 else si)
        styles.tag(lay, "structure")
        lay["sem_tone"] = 0.45 if k % 2 == 0 else 1.0
        z -= t


def micro(sc, rnd):
    multilayer(sc)
    sn = M.principled("SnAtom", (0.9, 0.9, 0.9), roughness=0.3)
    for k in range(60):
        x = rnd.uniform(-2.6, 2.6)
        y = rnd.uniform(-0.6, 0.6)
        f = 10 + k * 2
        fate = rnd.random()
        a = _sphere(f"Sn{k}", 0.07, sn, (x, y, 3.0), role="structure", seg=16)
        a["sem_tone"] = 1.3
        _key(a, f, location=(x + rnd.uniform(-0.3, 0.3), y, 3.0))
        if fate < 0.65:          # deposit: a growing grey crust on top
            _key(a, f + 10, location=(x, y, 0.07 + 0.11 * (k % 3)))
        elif fate < 0.85:        # implant into the top layers
            _key(a, f + 10, location=(x, y, -rnd.uniform(0.1, 0.35)))
        else:                    # sputter: knocks a surface atom out
            _key(a, f + 10, location=(x, y, 0.05))
            b = _sphere(f"Sput{k}", 0.06, sn, (x + 0.1, y, -0.05), role="structure", seg=12)
            b["sem_tone"] = 0.8
            _key(b, f + 10, location=(x + 0.1, y, -0.05))
            _key(b, f + 30, location=(x + rnd.uniform(-1.5, 1.5), y, 2.5))
    B._camera("CamB2_05", [(1, (0, 0, -0.6), (0.0, -7.5, 0.6), 100, 11.0),
                           (130, (0, 0, -0.4), (0.0, -6.6, 0.9), 100, 11.0)])


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
    B._camera("CamB2_08", [(1, (0, 0, 0.2), (0.0, -7.0, 0.6), 100, 11.0),
                           (262, (0, 0, 0.9), (0.0, -7.0, 1.8), 100, 11.0)])


def pumps(sc, rnd):
    V.source_vessel()
    S.collector()
    S.collector_housing()
    steel = M.polished_steel("PumpSteel", 0.3)
    flow = M.emission("Stannane", (0.75, 0.75, 0.78), 1.6)
    for k, ang in enumerate((-0.6, 0.0, 0.6)):
        y, z = 16.2 * math.cos(ang + math.pi / 2), 16.2 * math.sin(ang + math.pi / 2)
        bpy.ops.mesh.primitive_cylinder_add(radius=1.4, depth=2.6, vertices=48, location=(-3.0, y * 0.0 + 0.0, 16.4),
                                            rotation=(0, 0, 0))
        pump = bpy.context.object
        pump.location = (-4.0 + 3.2 * k, 0.0, 16.4)
        pump.data.materials.append(steel)
        styles.tag(pump, "shell")
        for b in range(6):                                  # impeller blades
            bpy.ops.mesh.primitive_cube_add(location=pump.location)
            bl = bpy.context.object
            bl.scale = (1.1, 0.08, 0.05)
            bl.rotation_euler = (0, 0, b * math.pi / 3)
            bl.data.materials.append(steel)
            styles.tag(bl, "structure")
            _key(bl, 1, rotation_euler=(0, 0, b * math.pi / 3))
            _key(bl, FRAMES, rotation_euler=(0, 0, b * math.pi / 3 + 40 * math.pi))
            for fc in C.fcurves(bl.animation_data.action):
                for kp in fc.keyframe_points:
                    kp.interpolation = "LINEAR"
        for j in range(10):                                  # stannane drifting up the wall into the pump
            th = rnd.uniform(-0.8, 0.8)
            pts = [(rnd.uniform(-4, 0), 7.0 * math.sin(th), 7.0 * math.cos(th) * 0.4),
                   (pump.location.x + rnd.uniform(-1, 1), 6.0, 10.0 + rnd.uniform(-1, 1)),
                   (pump.location.x, 0.6 * rnd.uniform(-1, 1), 15.2)]
            ob = _curve(f"Flow{k}_{j}", pts, flow, radius=0.05)
            ob.data.bevel_factor_start = 0.0
            ob.data.bevel_factor_end = 0.0
            ob.data.keyframe_insert("bevel_factor_end", frame=1)
            ob.data.keyframe_insert("bevel_factor_start", frame=20 + j * 3)
            ob.data.bevel_factor_end = 1.0
            ob.data.keyframe_insert("bevel_factor_end", frame=40 + j * 3)
            ob.data.bevel_factor_start = 0.85
            ob.data.keyframe_insert("bevel_factor_start", frame=72 + j * 3)
    B._camera("CamB2_09", [(1, (-1.0, 0, 6.0), (30.0, 30.0, 18.0), 30, 11.0),
                           (72, (-1.0, 0, 6.0), (36.0, 34.0, 21.0), 30, 11.0)])


def air(sc, rnd):
    V.source_vessel()
    glass = M.principled("TubeGlass", (0.9, 0.95, 1.0), roughness=0.05)
    bpy.ops.mesh.primitive_cylinder_add(radius=1.2, depth=12, vertices=64, location=(10, -30, 4),
                                        rotation=(0, math.pi / 2, 0))
    tube = bpy.context.object
    tube.name = "AirTube"
    tube.data.materials.append(glass)
    styles.tag(tube, "shell")
    beam, bmat, blen = S.laser_beam("EUVinAir", 0.18, (0.62, 0.45, 1.0), x_from=4.0, x_to=16.0)
    beam.location = (10, -30, 4)
    # attenuation: the beam lights only its first few units (EUV is absorbed within a short path)
    M.set_beam(bmat, 1, front=-blen / 2, strength=0)
    M.set_beam(bmat, 8, strength=30)
    M.set_beam(bmat, 24, front=-blen / 2 + 2.2)
    for k in range(40):                                     # air molecules
        _sphere(f"Air{k}", 0.05, M.emission("AirMol", (0.55, 0.6, 0.7), 1.5),
                (rnd.uniform(4.5, 15.5), -30 + rnd.uniform(-0.9, 0.9), 4 + rnd.uniform(-0.9, 0.9)), seg=8)
    B._camera("CamB2_02", [(1, (8.5, -30, 4), (8.5, -42, 6.5), 35, 11.0),
                           (170, (2.0, -14, 2.0), (34.0, -60.0, 22.0), 35, 11.0)])


def glow(sc, rnd):
    BM.machine()
    for ob in list(bpy.data.objects):          # camera is inside the scanner: drop the housings
        if ob.get("role") == "shell":
            ob.hide_render = True
    # a soft volumetric sheath along each leg of the light path, pulsed once
    vol = M.volume_glow("H2Plasma", (0.6, 0.45, 1.0), density=0.0, emission_strength=0.0)
    for i in range(len(BM.PATH) - 1):
        a, b = Vector(BM.PATH[i]), Vector(BM.PATH[i + 1])
        mid, d = (a + b) / 2, (b - a)
        bpy.ops.mesh.primitive_cylinder_add(radius=0.12, depth=d.length, vertices=32, location=mid)
        ob = bpy.context.object
        ob.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
        ob.data.materials.append(vol)
        styles.tag(ob, "emitter")
    for f, e in ((1, 0.0), (30, 0.0), (40, 0.9), (80, 0.35), (150, 0.0)):
        M.set_volume_strength(vol, f, emission_strength=e)
    lp = bpy.data.objects.get("LightPath")
    if lp:
        lmat = lp.data.materials[0]
        for f, e in ((1, 0.0), (30, 0.0), (40, 12.0), (80, 4.0), (150, 0.0)):
            M.set_emission_strength(lmat, f, e)
    B._area("GlowKey", (0, -6, 6), (0.8, 0, 0), 8, 120, (0.6, 0.7, 1.0))
    B._camera("CamB2_11", [(1, (0.4, 0, 1.0), (-3.2, -3.4, 1.6), 35, 4.0),
                           (156, (0.6, 0, 0.6), (-2.2, -3.6, 1.2), 35, 4.0)])


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
    """SEM shots: Mo layers darker than Si; atoms brighter (sem_tone scales the emission)."""
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
