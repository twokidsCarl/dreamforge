"""Round 32 tin = REGULAR near-round thin disc (R32_ROOT_CAUSE row 2; MAIN process recipe - looked at 8 + 32 spp before
use).

Carl t381: 「A0_01 R31 更好；但锡片应是规则圆盘——R31 的破碎 / 锯齿边不是 Carl 要的（物理上预脉冲把锡滴压成近圆的薄饼）」;
R31 p1: 「薄饼像一张撕开的灰纸片或玻璃碎片…边缘做成连续的翻卷唇边…去掉锯齿状的缺口」.
R31 (tin_r31) deformed the R29 sheet mesh with outline noise + 9 radial notches = torn paper. R32 does NOT deform that
mesh: the sheet object's mesh is REBUILT from scratch (same object, transform, material slots, same radius):
  * a regular round disc: NS segments x NR rings, perfectly round smooth outline (no notches, no outline noise);
  * thickness thick at the centre, thinning toward the rim, closed by a slightly fuller rounded LIP (continuous, no
    serrations) - a liquid pancake, not a coin edge;
  * a slight curve (sag) so it is not a flat plate, plus a very low-frequency smooth wobble of the surface;
  * high-metal / low-rough liquid tin (tin_r31 material recipe, gentler ripple), hot glow = warm on the laser-facing
    side (N . -laser) + a heated red rim; the R31 central fire blob is gone (core weight small);
  * the R24-R31 riders (TinLandingR26 orange edge etc.) are hidden: they outlined the old jagged edge.
"""
import math

import bpy
from mathutils import Vector

NS = 128
NR = 24
SAG = 0.10                  # dish depth at the rim, x offset in units of the radius (toward +x = away from the laser)
T0 = 0.060                  # centre half-thickness (units of the radius)
T_RIM = 0.018               # half-thickness just inside the lip
LIP = 0.010                 # lip half-thickness (rounded, continuous)
WOB = 0.050                 # low-frequency surface wobble (units of the radius)
ROUGH = 0.04
RIPPLE = (2.4, 0.5, 0.20)   # flowing highlights (32 spp v1 at 1.8 / 0.13: 90/10 3.8 < 4, smooth glass-lens read)
RIPPLE_SHOT = {"B1_10": (1.6, 0.3, 0.12)}   # 32 spp: the small B1_10 sheet broke into black / white camouflage patches at 2.4 / 0.20
HOT = 3.0
HOT_BACK = 0.30             # glow share on the face away from the laser
HOT_COL = (1.0, 0.30, 0.05)
LASER_DIR = Vector((1.0, 0.0, 0.0))
RIDERS = ("TinAfterglow", "PancakeHot", "PancakeRim", "PancakeEdge", "TinLanding", "PancakeDrops")


def _smooth(e0, e1, x):
    t = min(1.0, max(0.0, (x - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)


def _profile(r):
    """half-thickness at normalised radius r (0..1): thins toward the rim, then a rounded lip."""
    base = T_RIM + (T0 - T_RIM) * (1 - r * r) ** 1.5
    return base + LIP * math.exp(-((r - 0.97) / 0.05) ** 2)


def _wob(r, t):
    return WOB * r * r * (math.sin(2 * t + 0.7) * 0.5 + math.sin(3 * t + 2.1) * 0.3 + math.sin(5 * t + 4.0) * 0.2)


def _rebuild(me, R, cx):
    """closed disc: top (+x side) and bottom (-x side) ring grids joined at a rounded rim ring."""
    verts, faces, hot = [], [], []
    rings = [i / NR for i in range(1, NR + 1)]

    def mid(r, t):
        return cx + SAG * R * r * r + _wob(r, t) * R

    top, bot = [], []
    for side, lst in ((1, top), (-1, bot)):
        verts.append((mid(0, 0) + side * _profile(0) * R, 0.0, 0.0))
        hot.append(0.0)
        c = len(verts) - 1
        rows = []
        for r in rings:
            row = []
            for j in range(NS):
                t = 2 * math.pi * j / NS
                verts.append((mid(r, t) + side * _profile(r) * R, R * r * math.cos(t), R * r * math.sin(t)))
                hot.append(0.0)
                row.append(len(verts) - 1)
            rows.append(row)
        lst.extend([c, rows])
    # rim: rounded closing ring slightly outside r = 1
    rim = []
    for j in range(NS):
        t = 2 * math.pi * j / NS
        verts.append((mid(1.0, t), R * 1.012 * math.cos(t), R * 1.012 * math.sin(t)))
        hot.append(0.0)
        rim.append(len(verts) - 1)
    for (c, rows), flip in ((top, False), (bot, True)):
        r0 = rows[0]
        for j in range(NS):
            f = (c, r0[j], r0[(j + 1) % NS])
            faces.append(f[::-1] if flip else f)
        for a, b in zip(rows[:-1], rows[1:]):
            for j in range(NS):
                f = (a[j], b[j], b[(j + 1) % NS], a[(j + 1) % NS])
                faces.append(f[::-1] if flip else f)
        last = rows[-1]
        for j in range(NS):
            f = (last[j], rim[j], rim[(j + 1) % NS], last[(j + 1) % NS])
            faces.append(f[::-1] if flip else f)
    mats = [p.material_index for p in me.polygons[:1]] or [0]
    me.clear_geometry()
    me.from_pydata(verts, [], faces)
    for p in me.polygons:
        p.use_smooth = True
        p.material_index = mats[0]
    me.update()
    # hot weight: heated rim ring (R31 p1 「内部橙色只留边缘受热红光」)
    at = me.attributes.get("r31hot") or me.attributes.new("r31hot", "FLOAT", "POINT")
    for i, v in enumerate(me.vertices):
        r = math.hypot(v.co.y, v.co.z) / R
        at.data[i].value = 0.85 * _smooth(0.86, 1.0, r)   # heated rim only (32 spp v2: a face core glow lifted the darks, 90/10 3.8)
    me.update()


def disc(sc, shot, frame, name="Pancake"):
    sh = bpy.data.objects.get(name)
    if sh is None:
        print(f"[tin_r32] {shot}: no {name}", flush=True)
        return None
    me = sh.data
    co = [v.co.copy() for v in me.vertices]
    R = max(math.hypot(c.y, c.z) for c in co) * 0.97
    cx = sum(c.x for c in co) / len(co)
    _rebuild(me, R, cx)
    n_h = 0
    for o in bpy.data.objects:
        if o is not sh and o.name.startswith(RIDERS):
            o.hide_render = True
            n_h += 1
    import tin_r31 as T31
    T31.ROUGH, T31.HOT, T31.HOT_BACK, T31.HOT_COL = ROUGH, HOT, HOT_BACK, HOT_COL
    for s in sh.material_slots:          # rebuild from the pre-R31 material if R31 already swapped it
        m = s.material
        if m is not None and m.get("r31disc"):
            base = bpy.data.materials.get(m.name.replace("_R31disc", ""))
            if base is not None:
                s.material = base
    T31._material(sh, RIPPLE_SHOT.get(shot, RIPPLE))
    print(f"[tin_r32] {shot} {name}: rebuilt regular round disc R {R:.3f} ({NS}x{NR}), sag {SAG}, lip {LIP}, "
          f"{n_h} riders hidden", flush=True)
    return sh
