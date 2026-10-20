"""参数化通用神经元：胞体球 + 分叉树突 + 一根带终末分支的轴突（A0_03a 的线稿和 A0_03b 的白模共用同一份形态）。

几何依据（全部是示意，不对应任何具体脑区或细胞类型，也不代表真实尺寸比例，核查表 A0_03a/03b 记为 simplified）：
  - 一个胞体，一根轴突，多根树突：神经元的基本形态（任何神经科学教科书的通用画法，例如 Kandel《Principles of
    Neural Science》第 2 章的示意图）。
  - 树突：4–6 根主干从胞体上半球伸出，逐级二叉分叉（3 级），每级变短变细（长度 ×0.7–0.8，半径 ×0.65）。
  - 轴突：从胞体下方发出，一根细长的主干，末端三叉并带小结（突触小结）。
  - 单位 BU：胞体半径 0.2；排布间距 SPACING = 1.2 BU；纯示意。
形态由 `morphology(seed)` 生成（纯 Python，不依赖 bpy），所以 2D 线稿（mograph/a0.py）和 3D 白模用同一份点；
`build_neuron()` 才用 bpy 把它建成曲线和球。随机种子固定，重跑结果一致。
"""
import math
import random

SPACING = 1.2
SOMA_R = 0.20
AXON_R = 0.028
AXON_LEN = 1.45


def _norm(v):
    n = math.sqrt(sum(c * c for c in v)) or 1.0
    return [c / n for c in v]


def _cross(a, b):
    return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]


def _rot(v, axis, ang):
    """Rodrigues：v 绕单位轴 axis 转 ang。"""
    c, s = math.cos(ang), math.sin(ang)
    d = sum(v[i] * axis[i] for i in range(3))
    x = _cross(axis, v)
    return [v[i] * c + x[i] * s + axis[i] * d * (1 - c) for i in range(3)]


def _grow(rnd, p0, d, length, r0, r1, steps=9, wander=0.10, up=0.05):
    """一段带缓慢弯曲的树突枝：返回点和半径列表。"""
    pts, rad = [list(p0)], [r0]
    p = list(p0)
    for k in range(1, steps + 1):
        d = _norm([d[0] + rnd.uniform(-wander, wander), d[1] + rnd.uniform(-wander, wander),
                   d[2] + rnd.uniform(-wander, wander) * 0.6 + up])
        p = [p[i] + d[i] * length / steps for i in range(3)]
        pts.append(list(p))
        rad.append(r0 + (r1 - r0) * k / steps)
    return pts, rad, d


def morphology(seed, soma_r=SOMA_R):
    """返回 dict(soma_r, dendrites=[(pts, radii)], axon=(pts, radii), twigs=[(pts, radii)], boutons=[pt])。
    坐标：x 向右，z 向上，y 是景深；胞体在原点；树突朝上，轴突朝下。"""
    rnd = random.Random(seed)
    dendrites = []
    n = rnd.choice((4, 5, 5))
    off = rnd.uniform(0, 2 * math.pi)

    def branch(p0, d, length, r0, level):
        pts, rad, dend = _grow(rnd, p0, d, length, r0, r0 * 0.7)
        dendrites.append((pts, rad))
        if level >= 2 or (level == 1 and rnd.random() < 0.4):     # 第 3 级只在一部分枝上出现，别画成一团
            return
        ax = _norm(_cross(dend, [rnd.uniform(-1, 1), rnd.uniform(-0.4, 0.4), rnd.uniform(-1, 1)]))
        for sgn in (1, -1):
            ang = math.radians(rnd.uniform(24, 40)) * sgn
            # 子枝从父枝末端往回 1 个点的位置起，盖住连接缝
            start = pts[-2]
            branch(start, _rot(dend, ax, ang), length * rnd.uniform(0.7, 0.8), rad[-1] * 0.9, level + 1)

    for i in range(n):
        az = off + 2 * math.pi * i / n + rnd.uniform(-0.3, 0.3)
        polar = math.radians(rnd.uniform(16, 48))                 # 离 +Z 的夹角：只往上半球长
        d = [math.sin(polar) * math.cos(az), math.sin(polar) * math.sin(az) * 0.5, math.cos(polar)]
        p0 = [d[0] * soma_r * 0.85, d[1] * soma_r * 0.85, d[2] * soma_r * 0.85]
        branch(p0, d, rnd.uniform(0.32, 0.40), 0.040, 0)

    # 轴突：S 形缓摆的细长主干，往下
    amp, ph = rnd.uniform(0.07, 0.13), rnd.uniform(0, 2 * math.pi)
    ay = rnd.uniform(-0.1, 0.1)
    pts, rad = [], []
    N = 44
    for k in range(N + 1):
        s = k / N
        pts.append([amp * math.sin(2 * math.pi * s * 1.25 + ph) * s ** 0.6,
                    ay * s, -(soma_r * 0.9 + AXON_LEN * s)])
        rad.append(AXON_R * (1.15 - 0.25 * s))
    end = pts[-1]
    twigs, boutons = [], []
    for sgn, tilt in ((-1, 0.55), (0, 0.0), (1, 0.55)):
        d = _norm([sgn * math.sin(tilt), rnd.uniform(-0.1, 0.1), -math.cos(tilt)])
        tp, tr = [list(end)], [rad[-1]]
        for k in range(1, 7):
            tp.append([end[i] + d[i] * 0.2 * k / 6 + (rnd.uniform(-0.01, 0.01) if i != 2 else 0) for i in range(3)])
            tr.append(AXON_R * 0.55)
        twigs.append((tp, tr))
        boutons.append(tp[-1])
    return {"soma_r": soma_r, "dendrites": dendrites, "axon": (pts, rad), "twigs": twigs, "boutons": boutons}


def axon_path(m):
    """脉冲沿轴突走的折线（点列），供动画取位置。"""
    return m["axon"][0]


def path_at(pts, u):
    """折线上按弧长比例 u∈[0,1] 的位置和切线。"""
    seg = [math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]
    target = max(0.0, min(1.0, u)) * sum(seg)
    for i, L in enumerate(seg):
        if target <= L or i == len(seg) - 1:
            f = 0.0 if L == 0 else min(1.0, target / L)
            p = [pts[i][k] + (pts[i + 1][k] - pts[i][k]) * f for k in range(3)]
            t = _norm([pts[i + 1][k] - pts[i][k] for k in range(3)])
            return p, t
        target -= L


# ---- bpy 部分 -------------------------------------------------------------------------------
def _curve_object(name, strands, origin, mat, bevel_res=3):
    import bpy
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = 1.0                    # 管半径 = bevel_depth × 点的 radius
    cu.bevel_resolution = bevel_res
    cu.resolution_u = 2
    cu.use_fill_caps = True
    for pts, rad in strands:
        sp = cu.splines.new("POLY")
        sp.points.add(len(pts) - 1)
        for pt, p, r in zip(sp.points, pts, rad):
            pt.co = (p[0], p[1], p[2], 1.0)
            pt.radius = r
    ob = bpy.data.objects.new(name, cu)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = origin
    if mat is not None:
        ob.data.materials.append(mat)
    return ob


def _sphere(name, r, loc, mat, seg=24, rings=14, scale=(1, 1, 1)):
    import bpy
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, segments=seg, ring_count=rings, location=loc)
    ob = bpy.context.object
    ob.name = name
    ob.scale = scale
    for p in ob.data.polygons:
        p.use_smooth = True
    if mat is not None:
        ob.data.materials.append(mat)
    return ob


def build_neuron(name, seed, origin, mat=None, tag=None):
    """在 origin 处建一个神经元，返回 dict(soma, dendrites, axon, twigs, boutons, morph, origin)。
    tag(obj, role) 由调用方传入（styles.tag），这样本模块不依赖 styles。"""
    m = morphology(seed)
    soma = _sphere(name + "_Soma", m["soma_r"], origin, mat, scale=(1.0, 0.92, 1.05))
    dend = _curve_object(name + "_Dendrites", m["dendrites"], origin, mat)
    axon = _curve_object(name + "_Axon", [m["axon"]] + m["twigs"], origin, mat)
    boutons = [_sphere(f"{name}_Bouton{i}", 0.05, (origin[0] + b[0], origin[1] + b[1], origin[2] + b[2]), mat,
                       seg=12, rings=8) for i, b in enumerate(m["boutons"])]
    parts = [soma, dend, axon] + boutons
    if tag:
        for o in parts:
            tag(o, "structure")
    return {"soma": soma, "dendrites": dend, "axon": axon, "boutons": boutons, "morph": m, "origin": origin}
