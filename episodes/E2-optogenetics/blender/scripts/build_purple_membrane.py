"""参数化紫膜二维晶格：细菌视紫红质（bR）三聚体排成六方晶格，三聚体之间和中间是平的脂质面（A0_91）。

几何依据：
  - 空间群 P3，六方晶格，晶胞边长 a = b ≈ 62 Å，γ = 120°，每个晶胞一个三聚体（三个 bR 单体，三重轴在格点上）。
    Krebs & Isenbarger 2000, Biochim Biophys Acta 1460:15–26，第 3 节："arranged in trimeric units that pack in a
    hexagonal lattice (space group P3 with a unit cell dimension of ~62 Å)… Lipid molecules are located between
    trimers and in the space enclosed by each trimer"。
  - 每个单体 7 段大致垂直于膜面的跨膜 α 螺旋（A–G）：Henderson & Unwin 1975, Nature 257:28–32（电镜三维重构）。
  - 螺旋直径约 9 Å（α 螺旋含侧链的典型值），跨膜部分约 35 Å，膜面外只露出几 Å；这里取半径 4.0 Å（略细于含侧链的值，
    让相邻螺旋之间看得出缝）、长 38 Å、露出脂质面 3–7 Å，倾角 ≤ 2°（「大致垂直」）。
示意（核查表 A0_91 记为 simplified）：晶格常数、三聚体、7 螺旋/单体的数目都按资料；单体内 7 根螺旋的相对位置是
我们的示意排布（两排弧形：外排 4 根、内排 3 根，沿三聚体三重轴的切向排开，三个单体各转 120°），不是 Henderson
1990 密度图的坐标。排好后用 `check_geometry()` 检查：螺旋互不重叠，三聚体不越出晶胞。
单位：1 Å = 0.01 BU，所以一个晶胞宽 0.62 BU。形态由固定种子决定，重跑一致。
"""
import math
import random

A = 62.0                    # 晶胞边长，Å
HELIX_R = 4.0               # 螺旋半径，Å（v2：4.5 → 4.0，相邻螺旋留出 ≥ 1.3 Å 空隙，避免镜头移动时互相穿插、闪烁）
HELIX_LEN = 38.0            # 跨膜长度，Å
LIPID_T = 38.0              # 脂质双层厚度，Å（脂质面在 z=0，向下 38 Å）
R0 = 18.0                   # 单体中心离三重轴的距离，Å
PITCH = 9.8                 # 同排相邻螺旋的中心距，Å
UNIT = 0.01                 # Å → BU


def monomer_layout():
    """单体局部坐标 (u 切向, v 径向外) 下的 7 根螺旋：外排 4 根 + 内排 3 根，两排都沿以三重轴为圆心的弧排开
    （弧半径 26 Å 和 18 Å）。参数是在 62 Å 晶胞里网格搜索出来的：螺旋中心距 ≥ 9.3 Å（直径 9 Å，不重叠），
    三聚体半径 ≈ 28.8 Å（相邻三聚体最近的螺旋中心距 ≥ 13 Å，留给脂质）。"""
    out = []
    for u in (-1.5 * PITCH, -0.5 * PITCH, 0.5 * PITCH, 1.5 * PITCH):
        out.append((u, 5.5 - u * u / (2 * 26.0)))
    for u in (-PITCH, 0.0, PITCH):
        out.append((u, -4.0 - u * u / (2 * 18.0)))
    return out


def trimer_helices():
    """一个三聚体 21 根螺旋的 (x, y) 中心，Å，三重轴在原点。"""
    pts = []
    for k in range(3):
        th = math.radians(90 + 120 * k)
        r = (math.cos(th), math.sin(th))
        t = (-r[1], r[0])
        for u, v in monomer_layout():
            x = (R0 + v) * r[0] + u * t[0]
            y = (R0 + v) * r[1] + u * t[1]
            pts.append((x, y))
    return pts


def lattice_points(half_w, half_h):
    """覆盖 |x|<half_w、|y|<half_h（Å）的格点：a1 = (62, 0)，a2 = (-31, 53.69)。"""
    a1 = (A, 0.0)
    a2 = (A * math.cos(math.radians(120)), A * math.sin(math.radians(120)))
    pts = []
    n = int(max(half_w, half_h) / A * 2) + 3
    for j in range(-n, n + 1):
        for i in range(-n, n + 1):
            x, y = i * a1[0] + j * a2[0], i * a1[1] + j * a2[1]
            if abs(x) <= half_w + A and abs(y) <= half_h + A:
                pts.append((x, y))
    return pts


def check_geometry():
    """返回 (最小螺旋中心距, 三聚体最大半径, 相邻三聚体螺旋最小中心距)，都是 Å。"""
    h = trimer_helices()
    dmin = min(math.dist(h[i], h[j]) for i in range(len(h)) for j in range(i + 1, len(h)))
    rmax = max(math.hypot(x, y) for x, y in h) + HELIX_R
    other = [(x + A, y) for x, y in h]
    dn = min(math.dist(p, q) for p in h for q in other)
    return dmin, rmax, dn


def assert_clear(min_gap=1.0):
    """螺旋之间（同一三聚体、相邻三聚体）至少留 min_gap Å 的空隙，否则报错。"""
    dmin, _, dn = check_geometry()
    gap = min(dmin, dn) - 2 * HELIX_R
    assert gap >= min_gap, f"helix gap {gap:.2f} Å < {min_gap} Å"
    return gap


def _helix_into(bm, base, tilt, az, length, rad, dome=3.0, seg=14, rings=4):
    """在 bmesh 里加一根带圆顶的圆柱（轴向由 tilt/az 决定，base 为底面中心）。"""
    ax = (math.sin(tilt) * math.cos(az), math.sin(tilt) * math.sin(az), math.cos(tilt))
    # 与轴垂直的两个单位向量
    ref = (1, 0, 0) if abs(ax[0]) < 0.9 else (0, 1, 0)
    e1 = [ax[1] * ref[2] - ax[2] * ref[1], ax[2] * ref[0] - ax[0] * ref[2], ax[0] * ref[1] - ax[1] * ref[0]]
    n1 = math.sqrt(sum(c * c for c in e1))
    e1 = [c / n1 for c in e1]
    e2 = [ax[1] * e1[2] - ax[2] * e1[1], ax[2] * e1[0] - ax[0] * e1[2], ax[0] * e1[1] - ax[1] * e1[0]]
    # 截面环：(离底面的高度, 半径)
    prof = [(0.0, rad), (length - dome, rad)]
    for k in range(1, rings + 1):
        a = math.radians(90 * k / rings)
        prof.append((length - dome + dome * math.sin(a), rad * math.cos(a) * 0.999 + 1e-4))
    verts = []
    for h, r in prof:
        ring = []
        for s in range(seg):
            ang = 2 * math.pi * s / seg
            p = [base[i] + ax[i] * h + r * (math.cos(ang) * e1[i] + math.sin(ang) * e2[i]) for i in range(3)]
            ring.append(bm.verts.new(p))
        verts.append(ring)
    for a, b in zip(verts[:-1], verts[1:]):
        for s in range(seg):
            f = bm.faces.new((a[s], a[(s + 1) % seg], b[(s + 1) % seg], b[s]))
            f.smooth = True
    top = bm.verts.new([base[i] + ax[i] * length for i in range(3)])
    for s in range(seg):
        f = bm.faces.new((verts[-1][s], verts[-1][(s + 1) % seg], top))
        f.smooth = True


def build_membrane(half_w=190.0, half_h=110.0, seed=5):
    """建出脂质面（"Lipid"）和所有螺旋（"Helices"，一个网格），返回两个对象。尺寸为 Å，内部换成 BU。"""
    import bmesh
    import bpy
    assert_clear()
    rnd = random.Random(seed)
    bm = bmesh.new()
    th = trimer_helices()
    for cx, cy in lattice_points(half_w, half_h):
        for hx, hy in th:
            tilt = math.radians(rnd.uniform(0.3, 2.0))
            az = rnd.uniform(0, 2 * math.pi)
            top = rnd.uniform(3.0, 7.0)                              # 露出脂质面的高度
            ax = (math.sin(tilt) * math.cos(az), math.sin(tilt) * math.sin(az), math.cos(tilt))
            # 让螺旋顶端落在名义位置上，倾斜只把下半截偏开（脂质面以下看不见），免得顶面互相重叠
            base = tuple(((cx + hx) * UNIT, (cy + hy) * UNIT, top * UNIT)[i] - ax[i] * HELIX_LEN * UNIT for i in range(3))
            _helix_into(bm, base, tilt, az, HELIX_LEN * UNIT, HELIX_R * UNIT, dome=3.0 * UNIT)
    me = bpy.data.meshes.new("Helices")
    bm.to_mesh(me)
    bm.free()
    hel = bpy.data.objects.new("Helices", me)
    bpy.context.scene.collection.objects.link(hel)

    W, H = (half_w + 2 * A) * UNIT, (half_h + 2 * A) * UNIT
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= 2 * W
        v.co.y *= 2 * H
        v.co.z = v.co.z * LIPID_T * UNIT - LIPID_T * UNIT / 2          # 顶面 z = 0
    me2 = bpy.data.meshes.new("Lipid")
    bm.to_mesh(me2)
    bm.free()
    lip = bpy.data.objects.new("Lipid", me2)
    bpy.context.scene.collection.objects.link(lip)
    return lip, hel
