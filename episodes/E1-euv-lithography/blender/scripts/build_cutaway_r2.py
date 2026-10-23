"""P1 round 2: the whole scanner as a dense, de-cased CG cutaway (Carl 2026-10-23 pick 2B, "B做极细致和还原",
plus 4A violet light bouncing between metal mirror mounts). Generic engineering, not a copy of any vendor's
exterior: source vessel -> intermediate focus -> illuminator (field + pupil facet mirrors, grazing mirrors) ->
reflective mask on the reticle stage (6 deg incidence) -> six-mirror projection optics -> wafer stage.

  P = machine(M, studio=False, cut=True)   # M = kit_r2.palette(); returns key points (Vectors)

Units: metres; beam runs along +X; the cut plane faces the camera at -Y.
"""
import math
import random

from mathutils import Vector

import kit_r2 as K

# key optical points (x, y, z)
PLASMA = Vector((-7.35, 0, 2.3))
COLL = Vector((-8.25, 0, 2.3))           # collector vertex
IF = Vector((-4.55, 0, 2.55))
FFM = Vector((-2.15, 0.15, 3.85))        # field facet mirror
PFM = Vector((-3.55, 0.25, 2.05))        # pupil facet mirror
G1 = Vector((-1.35, 0.3, 2.75))          # grazing / condenser mirror
MASK = Vector((0.55, 0.3, 4.35))         # mask surface (pattern faces down)
# R3: grazing fold mirror right under the mask so the beam meets the mask at ~6 deg from the normal (was ~35 deg,
# contradicting the "约 6° 斜入射" label); PO mirror 1 sits at the mirror-image 6 deg on the other side.
G2 = Vector((0.18, 0.3, 2.0))            # R10: drawn ~9 deg so the in / out cones separate (label: ~5.4 deg, enlarged)
# R9 (one clean line): the six PO mirrors fold without any crossing - up, down, up, down the right wall, back left,
# then down onto the wafer (R2-R8 order crossed legs 2-3 and 4-5)
PO = [Vector(v) for v in ((0.93, 0.25, 1.75), (1.45, 0.15, 3.75), (2.25, 0.05, 2.2), (2.75, 0.0, 3.6),
                         (2.6, 0.0, 1.4), (2.0, 0.0, 1.75))]
WAFER = Vector((1.75, 0.0, 0.62))


R12 = [False]             # R12: r2_cutaway switches the bay walls to hero_kit_r12.wall_r12 (14 types, no DIN rows)
FRONT_FLANGE = [True]     # R13: B3_02 drops the vessel's front flange ring (it hid the cone between plasma and IF)


def _wall():
    if R12[0]:
        import hero_kit_r12 as HK12
        return HK12.wall_r12
    import hero_kit_r11 as HK11
    return HK11.wall_r11


LIP_SKIP_X = ()           # R11: module side lips left out (tour: projection module's left lip hid the mask)
FRONT_POSTS_SKIP = ()     # R10: tour (C_03) drops the front posts that blocked the main path


def _frame(M, mbs, studio):
    """Metrology / base frame: welded box-section posts and beams, gussets, levelling feet, floor grating."""
    fr, bolt = mbs["frame"], mbs["bolt"]
    xs = [-9.4, -6.0, -4.0, -0.9, 3.4]
    for x in xs:
        for y in (1.35, -1.35):
            if y < 0 and x in FRONT_POSTS_SKIP:
                continue
            fr.box((x, y, 2.4), (0.22, 0.22, 4.8))
            fr.box((x, y, 0.06), (0.42, 0.42, 0.12))                    # foot plate
            for dx in (-0.15, 0.15):
                for dy in (-0.15, 0.15):
                    bolt.cyl((x + dx, y + dy, 0.13), 0.025, 0.04, seg=6)
            for z in (1.2, 3.4):                                          # gussets
                fr.box((x + 0.2, y, z), (0.18, 0.04, 0.18), rot=(0, math.radians(45), 0))
    for z in (0.35, 4.85):
        for y in (1.35, -1.35):
            fr.box((-3.0, y, z), (12.8, 0.2, 0.2))
        for x in xs:
            fr.box((x, 0, z), (0.18, 2.7, 0.18))
    # back wall of the vacuum enclosure (behind the beam, y > 0) with stiffening ribs
    w = mbs["wall"]
    w.box((-3.0, 1.5, 2.55), (12.6, 0.06, 4.4))
    for x in [i * 0.6 - 9.0 for i in range(22)]:
        w.box((x, 1.44, 2.55), (0.05, 0.08, 4.3))
    for z in (1.0, 2.0, 3.1, 4.1):
        w.box((-3.0, 1.43, z), (12.5, 0.07, 0.05))
    # R9 (k2B density): the long enclosure wall carries the same three layers as the module back plates
    # R10: nameable parts only (profile frame, CF viewports, valve islands, turbo pumps + gate valves, hose bundles,
    # hexapod sensor mounts, tied harnesses) - the R9 PCB / LED-box / random-block layers are gone
    import hero_kit_r10 as HK
    P = HK.new_parts()
    opt = [(PLASMA, 1.5), (COLL, 1.0), (IF, 0.5)]
    import hero_kit_r11 as HK11            # R11: non-repeating blocks, not the R10 panel+flange tile
    # front_y: stay behind the module back plates (y 1.1) - R11 smoke: a viewport stack poked into the illuminator
    _wall()(P, -9.25, 3.25, 0.5, 4.7, 1.4, seed=33, keep=opt, scale=1.25, depth=0.6, front_y=1.14)
    PENDING_KITS.append(P)
    # floor grating
    g = mbs["grate"]
    for x in [i * 0.12 - 9.6 for i in range(110)]:
        g.box((x, 0, 0.02), (0.015, 3.6, 0.04))
    for y in [i * 0.4 - 1.8 for i in range(10)]:
        g.box((-3.0, y, 0.035), (13.2, 0.02, 0.05))


def _vessel(M, mbs, cut):
    """Source vessel: a horizontal cylinder cut open on the camera side, with ports, flanges and the collector."""
    v, fl, bolt, gl = mbs["vessel"], mbs["flange"], mbs["bolt"], mbs["glass"]
    c = Vector((-7.2, 0, 2.3))
    rot = (0, math.radians(90), 0)
    a0, a1 = (-35, 215) if cut else (0, 360)    # gap centred on -Y (local 270 deg)
    v.shell(c, 1.28, 1.36, 2.6, a0, a1, rot=rot, seg=72)                # cut away towards -Y
    for dx in (-1.3, 1.3):
        if dx > 0 and not FRONT_FLANGE[0]:
            continue
        fl.ring(c + Vector((dx, 0, 0)), 1.5, 1.3, 0.1, rot=rot, seg=72)
        bolt.bolts(c + Vector((dx + (0.06 if dx > 0 else -0.06), 0, 0)), 1.42, 36, 0.022, 0.05, rot=rot)
    # end dish behind the collector
    v.cyl((-8.55, 0, 2.3), 1.36, 0.08, rot=rot, seg=72)
    # ports with flanges and view windows around the vessel (only on the kept side)
    rnd = random.Random(3)
    for i, (ang, dx, r) in enumerate([(70, -0.6, 0.18), (110, 0.3, 0.14), (150, -0.2, 0.22), (200, 0.6, 0.16),
                                      (250, -0.5, 0.2), (290, 0.4, 0.12), (100, 0.9, 0.1), (230, 0.9, 0.12)]):
        a = math.radians(ang)
        n = Vector((0, math.cos(a), math.sin(a)))
        if cut and n.y < -0.35:
            continue
        base = c + Vector((dx, 0, 0)) + n * 1.36
        tip = base + n * (0.25 + rnd.random() * 0.2)
        v.tube(base, tip, r, seg=32)
        q = Vector((0, 0, 1)).rotation_difference(n).to_euler()
        fl.ring(tip, r * 1.6, r * 0.7, 0.05, rot=q)
        bolt.bolts(tip + n * 0.03, r * 1.35, 10, 0.012, 0.03, rot=q)
        if i % 3 == 0:
            gl.cyl(tip + n * 0.02, r * 0.72, 0.02, rot=q)
    # droplet generator (top) and catcher (bottom)
    import hero_kit_r10 as HK                  # R10: a real tin droplet generator on top of the vessel
    HK.droplet_generator(_hk(), (-7.35, 0, 3.05), (0, 0, -1), s=1.25, flange_at=0.62)
    v.tube((-7.35, 0, 0.94), (-7.35, 0, 0.4), 0.13, seg=24)
    # pumps hanging under the vessel
    for x in (-8.0, -6.5):
        mbs["pump"].cyl((x, 0.2, 0.62), 0.22, 0.55, seg=36)
        fl.ring((x, 0.2, 0.92), 0.3, 0.16, 0.05)
        for k in range(10):
            mbs["pump"].ring((x, 0.2, 0.42 + k * 0.045), 0.235, 0.21, 0.015)
    # collector mirror: ellipsoid-like dish with central hole, gold-ish back structure, cooling channels
    return c


def _collector(M, mbs):
    """Collector: concave reflective dish (r 0.68 m) with a 0.12 m central hole, facing +X, cooling ring behind."""
    import bmesh
    from mathutils import Matrix
    mb = mbs["mirror"]
    R, hole, f = 0.68, 0.12, 0.42
    nr, na = 14, 72
    verts = []
    for i in range(nr + 1):
        r = hole + (R - hole) * i / nr
        x = COLL.x + r * r / (4 * f)
        row = [mb.bm.verts.new((x, r * math.cos(2 * math.pi * j / na), COLL.z + r * math.sin(2 * math.pi * j / na)))
               for j in range(na)]
        verts.append(row)
    for i in range(nr):
        for j in range(na):
            k = (j + 1) % na
            f_ = mb.bm.faces.new((verts[i][j], verts[i][k], verts[i + 1][k], verts[i + 1][j]))
            f_.smooth = True
    mb.bm.faces.ensure_lookup_table()
    # R3: a thick shell, not a film: substrate back surface 9 cm behind the reflective face, rim band, and
    # cooling channels running radially over the back
    sub = mbs["substrate"]
    back = []
    for i in range(nr + 1):
        r = hole + (R - hole) * i / nr
        x = COLL.x + r * r / (4 * f) - 0.09
        back.append([sub.bm.verts.new((x, r * math.cos(2 * math.pi * j / na), COLL.z + r * math.sin(2 * math.pi * j / na)))
                     for j in range(na)])
    for i in range(nr):
        for j in range(na):
            k = (j + 1) % na
            sub.bm.faces.new((back[i][j], back[i + 1][j], back[i + 1][k], back[i][k])).smooth = True
    rimx0 = COLL.x + R * R / (4 * f)
    sub.ring((rimx0 - 0.045, 0, COLL.z), R, R - 0.004, 0.09, rot=(0, math.radians(90), 0), seg=na)
    sub.ring((COLL.x + hole * hole / (4 * f) - 0.045, 0, COLL.z), hole + 0.004, hole, 0.09, rot=(0, math.radians(90), 0), seg=32)
    for a in range(16):
        ang = 2 * math.pi * a / 16
        pts = []
        for i in range(0, nr + 1, 2):
            r = hole + 0.04 + (R - hole - 0.06) * i / nr
            pts.append(Vector((COLL.x + r * r / (4 * f) - 0.11, r * math.cos(ang), COLL.z + r * math.sin(ang))))
        mbs["copper"].path(pts, 0.014, seg=8)
    rot = (0, math.radians(90), 0)
    rimx = COLL.x + R * R / (4 * f)
    mbs["flange"].ring((rimx, 0, COLL.z), R + 0.08, R - 0.01, 0.06, rot=rot, seg=72)
    mbs["bolt"].bolts((rimx + 0.035, 0, COLL.z), R + 0.04, 24, 0.012, 0.03, rot=rot)
    mbs["gold"].ring((COLL.x - 0.06, 0, COLL.z), R * 0.95, hole * 0.9, 0.08, rot=rot, seg=64)   # substrate back
    mbs["anod"].tube((COLL.x - 0.1, 0, COLL.z), (-8.6, 0, COLL.z), hole * 0.85, seg=32)          # laser entry tube
    for k in range(5):                                                                  # cooling channels
        mbs["copper"].ring((COLL.x - 0.11 - k * 0.002, 0, COLL.z), 0.2 + k * 0.1, 0.18 + k * 0.1, 0.03, rot=rot)
    for a in range(6):                                                                  # support spokes
        ang = math.radians(a * 60 + 30)
        mbs["mount"].tube((COLL.x - 0.15, 0.6 * math.cos(ang), COLL.z + 0.6 * math.sin(ang)),
                          (-8.5, 1.2 * math.cos(ang), COLL.z + 1.2 * math.sin(ang)), 0.03)


def _module_box(mbs, x0, x1, z0, z1, y_back=1.1, y_front=-1.0, seed=0, ribs=True):
    """An open-front optics housing: back plate, floor, roof, side walls with lightening holes simulated by
    ribs, edge flanges and bolt rows, greebles on the outside."""
    h, bolt, fl = mbs["housing"], mbs["bolt"], mbs["flange_s"]
    cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
    W, H = x1 - x0, z1 - z0
    h.box((cx, y_back, cz), (W, 0.05, H))
    h.box((cx, (y_back + y_front) / 2, z0), (W, y_back - y_front, 0.05))
    h.box((cx, (y_back + y_front) / 2, z1), (W, y_back - y_front, 0.05))
    for x in (x0, x1):                       # side walls cut back to the rear 45 % so the inside reads
        d = (y_back - y_front) * 0.45
        h.box((x, y_back - d / 2, cz), (0.05, d, H))
        for k in range(1, 6):
            h.box((x + (0.03 if x == x1 else -0.03), y_back - d / 2, z0 + k * H / 6), (0.04, d, 0.04))
    # front edge flanges (where the cover was removed) with bolt rows
    for z in (z0, z1):
        fl.box((cx, y_front, z), (W + 0.1, 0.06, 0.1))
        for i in range(int(W / 0.12)):
            bolt.cyl((x0 + 0.06 + i * 0.12, y_front - 0.035, z), 0.012, 0.02, rot=(math.radians(90), 0, 0), seg=6)
    for x in (x0, x1):
        if any(abs(x - xs) < 1e-3 for xs in LIP_SKIP_X):
            continue
        fl.box((x, y_back - (y_back - y_front) * 0.45, cz), (0.1, 0.06, H + 0.1))
    # R3 cut skin: the removed cover is shown as a sawn-off outer panel lip (pale paint) with its section face
    # (contrasting colour) along the opening, so the box reads as cut open, not as a lid taken off
    if "section" in mbs:
        sk, sec = mbs["skin"], mbs["section"]
        lip = 0.16
        yf = y_front - 0.05
        sk.box((cx, yf, z0 - 0.02 + lip / 2), (W + 0.2, 0.06, lip))                       # bottom lip
        sec.box((cx, yf - 0.002, z0 - 0.02 + lip), (W + 0.2, 0.064, 0.012))
        for x, sgn in ((x0, 1), (x1, -1)):                                                  # side lips
            if any(abs(x - xs) < 1e-3 for xs in LIP_SKIP_X):    # R11: C_03 end frame - the lip cut the mask view
                continue
            sk.box((x + sgn * lip * 0.35, yf, cz), (lip * 0.7, 0.06, H))
            sec.box((x + sgn * lip * 0.7, yf - 0.002, cz), (0.012, 0.064, H))
        sk.box((cx, yf, z1 + 0.02 - lip * 0.3), (W + 0.2, 0.06, lip * 0.6))                # top lip
        sec.box((cx, yf - 0.002, z1 + 0.02 - lip * 0.6), (W + 0.2, 0.064, 0.012))
    if ribs:
        for i in range(1, int(W / 0.45)):
            h.box((x0 + i * 0.45, y_back - 0.04, cz), (0.03, 0.05, H))
    # outside greebles on the roof
    import parts_kit_r8 as PK                 # R8: named roof parts instead of greeble boxes
    P = PK.new_parts()
    ym = (y_back + y_front) / 2
    for k in range(max(1, int(W / 1.3))):
        x = x0 + (k + 0.5) * W / max(1, int(W / 1.3))
        PK.turbo_pump(P, (x - 0.25, ym + 0.2, z1 + 0.05), (0, 0, 1), 0.15)
        PK.gate_valve(P, (x + 0.3, ym - 0.25, z1 + 0.12), (0, 1, 0), 0.07)
    PENDING_KITS.append(P)
    import hero_kit_r10 as HK
    HK.cooling_bundle(_hk(), [(x0 + 0.1, y_back - 0.12, z1 + 0.06), (x1 - 0.1, y_back - 0.12, z1 + 0.06)], k=4,
                      r=0.016, clamp_every=0.5, up=(0, 1, 0))
    HK.cable_harness(_hk(), [(x0 + 0.1, y_back - 0.3, z1 + 0.06), (x1 - 0.1, y_back - 0.3, z1 + 0.06)], n=8, r=0.008,
                     tie_every=0.2)


PENDING_KITS = []        # R8: parts-kit batches waiting for finish (machine() / _po_turntable flush them)
_HK = []                 # R10: the shared hero_kit_r10 batch of the scene being built


def _hk():
    """The current hero_kit_r10 parts batch (created on first use, flushed with the other kits)."""
    if not _HK:
        import hero_kit_r10 as HK
        _HK.append(HK.new_parts())
        PENDING_KITS.append(_HK[0])
    return _HK[0]


def flush_kits(M, parent=None, tag="Kit"):
    import parts_kit_r8 as PK
    import hero_kit_r10 as HK
    out = []
    while PENDING_KITS:
        P = PENDING_KITS.pop(0)
        fin = HK.finish if "hose_b" in P else PK.finish
        out += fin(P, M, f"{tag}{len(PENDING_KITS)}", parent=parent)
    _HK.clear()
    return out


EXTRA_KEEP = []           # R11: extra keep-clear spheres for the bay walls (B7_06 M5 / M6 column)
WALL_TONE = ["mixed"]     # R11: "dark" = dark base plates so the parts read against a white studio housing


def _interior_fill(mbs, x0, x1, z0, z1, y_back=1.1, seed=0, keep=()):
    """R8: the de-cased housing's back plate carries a real parts kit (parts_kit_r8: turbo pumps on elbows, gate
    valves, gauges + viewports, bellows, card cages, cable tray, coolant manifold, drag chain) instead of the
    R2-R7 random greeble boxes / actuator blocks / gold patches. Keeps the internal strut cage."""
    import hero_kit_r10 as HK
    W, H = x1 - x0, z1 - z0
    # R10: the back plate carries nameable parts only (hero_kit_r10.wall_r10); parts stand off the plate by up to
    # ~0.4 m (k2B depth) but stay clear of the optics
    import hero_kit_r11 as HK11            # R11: non-repeating blocks
    _wall()(_hk(), x0 + 0.08, x1 - 0.08, z0 + 0.06, z1 - 0.06, y_back - 0.025, seed=seed,
                keep=[(Vector(c), r_ + 0.1) for c, r_ in list(keep) + EXTRA_KEEP], scale=1.35 if H > 2.0 else 1.0, depth=1.5,
                  tone=WALL_TONE[0], front_y=y_back - 0.55)

    def clear(p, r=0.0):
        return all((Vector(p) - c).length > rr + r for c, rr in keep)
    for i in range(1, int(W / 0.7) + 1):
        x = x0 + i * W / (int(W / 0.7) + 1)
        for z in (z0 + 0.12, z1 - 0.12):
            mbs["frame"].box((x, y_back - 0.55, z), (0.07, 1.0, 0.07))


def _illuminator(M, mbs):
    _module_box(mbs, -4.25, -0.75, 1.55, 4.3, seed=11)
    _interior_fill(mbs, -4.25, -0.75, 1.55, 4.3, seed=12,
                   keep=[(FFM, 0.6), (PFM, 0.55), (G1, 0.4), (IF.lerp(FFM, 0.5), 0.3), (FFM.lerp(PFM, 0.5), 0.3),
                         (PFM.lerp(G1, 0.5), 0.3), (G1.lerp(MASK, 0.4), 0.3)])
    # intermediate-focus neck: cone from the vessel, bellows, gate valve
    v = mbs["vessel"]
    v.tube((-5.85, 0, 2.38), (-4.75, 0, 2.53), 0.42, seg=40, r2=0.14)
    for k in range(9):
        mbs["flange"].ring(Vector((-4.7 + k * 0.035, 0, 2.55)), 0.2, 0.13, 0.02, rot=(0, math.radians(90), 0))
    mbs["flange"].ring((-4.35, 0, 2.55), 0.32, 0.12, 0.08, rot=(0, math.radians(90), 0))
    mbs["anod"].box((-4.42, 0, 2.95), (0.16, 0.34, 0.5))
    # R10 (R9: "field facet mirror reads as a heatsink"): a curved carrier holding columns of long, thin, curved
    # (banana-shaped) polished facets, each tilted a little differently, on a hexapod - no black fin blocks
    n = K.mirror_normal(IF, FFM, PFM)
    from mathutils import Matrix
    import hero_kit_r10 as HK
    n = (n + Vector((0, -0.75, 0))).normalized()          # R10: turned toward the cut side so the facets read
    # R11 (R10: "facets read as white tiles"): curved polished strips on pedestals with gaps + individual tilt
    import hero_kit_r11 as HK11
    HK11.field_facet_mirror_r11(_hk(), FFM, n, width=1.0, height=0.72, cols=4, rows=9, seed=5, spot_mb=mbs["spot"])
    car = mbs["mount"]
    # pupil facet mirror: round facets on a disc
    n2 = (K.mirror_normal(FFM, PFM, G1) + Vector((0, -0.5, 0))).normalized()
    q2 = Vector((0, 0, 1)).rotation_difference(n2)
    R2 = q2.to_matrix()
    for ring_i, (rr, cnt) in enumerate([(0.0, 1), (0.09, 8), (0.18, 15), (0.27, 22), (0.36, 28)]):
        for k in range(cnt):
            a = 2 * math.pi * k / cnt
            c = PFM + R2 @ Vector((rr * math.cos(a), rr * math.sin(a), 0))
            mbs["mirror"].cyl_m(Matrix.Translation(c) @ R2.to_4x4(), 0.038, 0.012, seg=20)
            mbs["substrate"].cyl_m(Matrix.Translation(c - n2 * 0.018) @ R2.to_4x4(), 0.04, 0.026, seg=20)
            if ring_i >= 2 and (abs(math.cos(a)) > 0.8):                      # dipole illumination spots
                mbs["spot"].cyl_m(Matrix.Translation(c + n2 * 0.008) @ R2.to_4x4(), 0.032, 0.002, seg=16)
    car.cyl_m(Matrix.Translation(PFM - n2 * 0.04) @ R2.to_4x4(), 0.44, 0.05, seg=48)
    mbs["flange"].ring(PFM - n2 * 0.02, 0.47, 0.42, 0.08, rot=q2.to_euler())
    car.tube(PFM - n2 * 0.08, PFM - n2 * 0.08 + Vector((0, 0, -0.5)), 0.06)
    # condenser / grazing mirror
    _mirror(mbs, G1, K.mirror_normal(PFM, G1, G2), 0.22, seed=2)
    _mirror(mbs, G2, K.mirror_normal(G1, G2, MASK), 0.17, seed=3)
    for k in range(4):                                                    # G2 support column down to the base frame
        a = math.radians(45 + 90 * k)
        mbs["frame"].tube(G2 + Vector((0.12 * math.cos(a), 0.3 + 0.12 * math.sin(a), -0.25)),
                          Vector((0.3 + 0.25 * math.cos(a), 0.6 + 0.25 * math.sin(a), 0.4)), 0.03)


def _mirror(mbs, p, n, r, seed=0):
    """R10: solid mirror in a machined cell on a real hexapod (hero_kit_r10.mirror_hexapod)."""
    import hero_kit_r10 as HK
    return HK.mirror_hexapod(_hk(), p, n, r, seed=seed, spot_mb=mbs["spot"])


def _reticle_stage(M, mbs):
    """R10: reticle stage as a real maglev long-stroke stage: two maglev rails (magnet track + coil mover with
    hoses + encoder scale) on a stator bridge, a cross-beam carrying the ceramic chuck that holds the patterned
    reflective mask face-down, with the violet illuminated slit on it (R9: "mask reads as a small dark block")."""
    import hero_kit_r10 as HK
    P = _hk()
    z = MASK.z
    for y in (-0.6, 0.85):
        HK.maglev_rail(P, MASK.x - 2.0, MASK.x + 2.0, y, z + 0.32, car_x=MASK.x, car_w=0.9, depth=0.3)
    mbs["rstage"].box((MASK.x, 0.12, z + 0.62), (4.4, 2.1, 0.12))                 # stator bridge
    for x in (MASK.x - 2.1, MASK.x + 2.1):
        mbs["rstage"].box((x, 0.12, z + 0.47), (0.16, 2.0, 0.22))
    P["alu"].box((MASK.x, 0.12, z + 0.38), (0.95, 1.75, 0.08))                    # cross-beam between the movers
    HK.reticle(P, (MASK.x, MASK.y, z), size=0.62, face=(0, 0, -1), slit_mb=mbs["spot"], slit=(0.78, 0.1))
    HK.cable_harness(P, [(MASK.x - 0.5, 0.95, z + 0.5), (MASK.x - 1.2, 1.0, z + 0.75), (-1.5, 1.0, 4.8)], n=8, r=0.009)


def _projection(M, mbs):
    _module_box(mbs, 0.6, 3.0, 1.0, 4.05, seed=21)
    pts = [MASK] + PO + [WAFER]
    _interior_fill(mbs, 0.6, 3.0, 1.0, 4.05, seed=22,
                   keep=[(p, 0.5) for p in PO] + [(a.lerp(b, 0.5), 0.25) for a, b in zip(pts, pts[1:])])
    # ring frames of the PO cage
    for z in (1.05, 2.3, 3.95):
        mbs["frame"].ring((1.8, 0.5, z), 1.1, 1.0, 0.06, seg=64)
    for i, p in enumerate(PO):
        n = K.mirror_normal(pts[i], p, pts[i + 2])
        r = PO_R[i]
        plate = _mirror(mbs, p, n, r, seed=i)
        # tie each mirror plate back to the housing wall
        mbs["mount"].tube(plate, Vector((plate.x, 1.08, plate.z)), 0.035)
        mbs["anod"].box(Vector((plate.x, 1.0, plate.z)), (0.22, 0.12, 0.22))
    # sensor boxes and cooling lines inside the housing
    import hero_kit_r10 as HK
    HK.cable_harness(_hk(), [(0.7, 0.9, 1.2), (0.7, 0.9, 3.9), (2.9, 0.9, 3.95)], n=6, r=0.007)
    HK.cooling_bundle(_hk(), [(2.9, 0.95, 1.1), (2.9, 0.95, 3.8), (3.3, 0.95, 4.6)], k=4, r=0.012, up=(0, 1, 0))


def _wafer_stage(M, mbs):
    """R10: wafer stage on a planar motor (Halbach checkerboard magnet plate, coil mover, ceramic chuck, wafer,
    interferometer mirrors, umbilical) on a granite base."""
    import hero_kit_r10 as HK
    mbs["granite"].box((1.6, 0, 0.17), (4.4, 2.4, 0.34))
    zt = WAFER.z - 0.159
    HK.planar_motor(_hk(), 1.6, 0.0, zt, 3.6, 1.9, mover=(WAFER.x, 0.0), mover_w=0.5, wafer_r=0.15)


def _services(M, mbs):
    """Pipes along the back wall and roof, electronics racks behind, cable trays."""
    p = mbs["pipe"]
    rnd = random.Random(1)
    for k in range(9):
        z = 0.7 + k * 0.42
        y = 1.32 - (k % 3) * 0.07
        r = rnd.choice((0.025, 0.035, 0.05))
        pts = [(-9.3, y, z), (-5.8 + rnd.uniform(-0.3, 0.3), y, z), (-5.6, y, z + 0.15), (-1.0, y, z + 0.15),
               (-0.8, y, z), (3.3, y, z)]
        p.path(pts, r, seg=12)
        for x in range(-9, 3, 1):                                          # clamps
            mbs["steel"].box((x + 0.3, y, pts[0][2] if x < -6 else z + 0.15 if x < -1 else z), (0.04, r * 3, r * 3))
    for k in range(4):
        y = -1.0 + k * 0.6
        K.cable_run(mbs["cable_b" if k % 2 else "cable_g"],
                    [(-9.2, y, 4.95), (-6.0, y + 0.1, 5.05), (-3.0, y, 5.0), (0.0, y + 0.05, 5.1), (3.2, y, 5.0)],
                    n=6, r=0.01, seed=k)
    # racks behind the back wall peek above it
    for i, x in enumerate([-8.6, -7.4, -2.8, -1.6, 2.0]):
        mbs["housing"].box((x, 2.1, 2.3), (1.0, 0.8, 4.6))
        for j in range(14):
            mbs["anod"].box((x, 1.68, 0.5 + j * 0.3), (0.9, 0.02, 0.22))
            pass


PO_R = [0.22, 0.28, 0.27, 0.25, 0.25, 0.21]


def beam_path(start=0, end=None):
    """The violet path IF -> illuminator -> G2 -> mask -> PO -> wafer with a k4A-style column radius at each
    point (focus = thin, mirrors = ~80 % of the mirror radius)."""
    pts = [IF, FFM, PFM, G1, G2, MASK] + PO + [WAFER]
    # R4: thin at G2 / mask / PO1 so the ~6 deg in/out pair separates into a readable narrow V under the mask
    # R9: solid k4A shafts as wide as ~60 % of each mirror (PO legs were thin 8 cm tubes = "flat lines" in R8)
    rad = [0.03, 0.27, 0.22, 0.15, 0.1, 0.075] + [r * 0.6 for r in PO_R] + [0.02]   # R10: solid cones at the mask
    return pts[start:end], rad[start:end]


def machine(M, studio=False, cut=True, beam=True, bounce=20.0):
    mbs = {k: K.MB() for k in ("frame", "bolt", "wall", "grate", "vessel", "flange", "flange_s", "glass", "pump",
                                "mirror", "gold", "copper", "mount", "housing", "greeble", "anod", "stage", "steel",
                                "mask", "rstage", "alu", "led", "cable_b", "cable_o", "cable_g", "pipe", "granite", "wafer",
                                "beam", "halo", "cone", "substrate", "spot", "vol", "skin", "section")}
    _frame(M, mbs, studio)
    _vessel(M, mbs, cut)
    _collector(M, mbs)
    _illuminator(M, mbs)
    _reticle_stage(M, mbs)
    _projection(M, mbs)
    _wafer_stage(M, mbs)
    _services(M, mbs)
    if beam:
        path, radii = beam_path()
        K.beam_columns(mbs["vol"], path, radii)
        # collector cones: plasma -> collector rim (emission) and collector -> IF (converging)
        K.cone_beam(mbs["cone"], IF, Vector((COLL.x + 0.28, 0, COLL.z)), 0.62)
        mbs["cone"].sphere(PLASMA, 0.06, 16)
    mats = {"frame": M["paint"] if studio else M["alu_dark"], "bolt": M["steel"], "wall": M["blast"],
            "grate": M["anod"], "vessel": M["steel"], "flange": M["alu"], "flange_s": M["alu"], "glass": M["glass"],
            "pump": M["alu"], "mirror": M["mirror"], "gold": M["gold"], "copper": M["copper"], "mount": M["alu"],
            "housing": M["paint"] if studio else M["paint_grey"], "greeble": M["alu_dark"], "anod": M["anod"],
            "stage": M["paint"], "rstage": M["paint"], "alu": M["alu"], "steel": M["steel"], "mask": M["mirror"], "led": M["led_c"],
            "cable_b": M["cable_b"], "cable_o": M["cable_o"], "cable_g": M["cable_g"], "pipe": M["steel"],
            "granite": M["granite"], "wafer": M["wafer"] if "wafer" in M else M["mirror"],
            "beam": M["beam"], "halo": M["beam_halo"], "cone": M.get("cone", M["beam_halo"]),
            "substrate": M["substrate"], "spot": M["spot"], "vol": M["beam_wide"],
            "skin": M["paint"], "section": M.get("section", M["copper"])}
    mats["mirror"] = M["coating"]
    bev = {"frame": 0.02, "housing": 0.012, "stage": 0.015, "rstage": 0.015, "greeble": 0.006, "anod": 0.008, "flange_s": 0.008,
           "granite": 0.02, "vessel": 0.01}
    if beam and bounce:
        K.bounce_lights([FFM, PFM, G1, G2, MASK + Vector((0, -0.1, -0.15))] + PO, energy=bounce)
    flush_kits(M, tag="R8Kit")
    objs = {}
    for k, mb in mbs.items():
        if len(mb.bm.verts):
            objs[k] = mb.obj("R2_" + k, mats[k], bevel=bev.get(k, 0.0))
        else:
            mb.bm.free()
    return objs
