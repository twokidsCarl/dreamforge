"""参数化微生物视紫红质（七次跨膜）和通用离子孔：A–D 段所有「通道 / 泵」镜头共用。

几何依据（示意，核查表记 simplified；P6 要补 research/visual/opsin.md，逐条附原文）：
  - 微生物视紫红质 = 7 根大致垂直于膜的 α 螺旋（A–G，或 TM1–TM7），视黄醛经席夫碱连在第 7 根螺旋的赖氨酸上，
    躺在螺旋束中部：Henderson & Unwin 1975（7 螺旋）；细菌视紫红质的 Lys216 在螺旋 G 上（Henderson 1990 等）。
  - 通道视紫红质（ChR）的阳离子通路在 TM1、TM2、TM3、TM7 之间：Kato et al. 2012, Nature 482:369（C1C2 嵌合体
    晶体结构）。真实 ChR 是二聚体；这里只画一个单体，便于看清孔（simplified）。
  - 「光打开孔」只画成 TM1/TM2/TM7 向外让开、孔道变宽，不是实测的构象变化电影（分镜：不假装是晶体结构电影）。
  - 全长 ChR 在胞内侧还有很长的 C 端；Nagel 2003 用的 ChR2 是截到跨膜核心的片段（B_07a / B_07b 用 cterm 表示）。
  - 泵（bR、NpHR）没有贯通的孔：画成螺旋紧密、中间没有孔道，离子由视黄醛附近「接力」过去。
  - 通用离子孔（第一幕，光遗传学以前的神经元放电）：n 根桶板围成的孔，不对应任何具体电压门控通道。
单位与 build_bilayer 一致：1 Å = 0.01 BU，膜中平面 z = 0。螺旋长 48 Å（两端各伸出脂质头基约 4 Å）。
"""
import math
import random

UNIT = 0.01
HELIX_R = 4.6               # 含侧链的视觉半径，Å（比 build_purple_membrane 的 4.0 粗：这里是单个蛋白特写）
HELIX_LEN = 48.0
RING_R = 15.0               # 螺旋中心所在椭圆的长半轴，Å（check_layout：相邻螺旋空隙 ≥ 1.3 Å）
RING_E = 0.85               # 短半轴 / 长半轴
NAMES = "ABCDEFG"
PORE_HELICES = (0, 1, 2, 6)  # TM1、TM2、TM3、TM7（Kato 2012）
OPEN_SHIFT = 3.2            # 完全打开时 TM1/TM2/TM7 外移的距离，Å（示意）


def helix_layout(kind="channel", seed=1):
    """7 根螺旋的 (x, y, tilt_x, tilt_y)，Å / 弧度。顺序 A→G 沿椭圆排一圈；通道的孔心偏向 A/B/C/G 一侧。"""
    rnd = random.Random(seed)
    out = []
    for i in range(7):
        a = math.radians(115 + i * 360 / 7.4)          # 不闭合的一圈：G 回到 A 旁边
        x, y = RING_R * math.cos(a), RING_R * RING_E * math.sin(a)
        s = 1 if i % 2 == 0 else -1                    # 相邻螺旋反平行，倾角正负交替
        out.append((x, y, s * math.radians(rnd.uniform(4, 11)), math.radians(rnd.uniform(-5, 5))))
    return out


def pore_center(kind="channel", seed=1):
    """孔心 (x, y)，Å：TM1/2/3/7 四根螺旋中心的平均，再往外推一点（孔在束的一侧，不在正中）。"""
    h = helix_layout(kind, seed)
    xs = [h[i][0] for i in PORE_HELICES]
    ys = [h[i][1] for i in PORE_HELICES]
    return sum(xs) / 4, sum(ys) / 4


def retinal_points(kind="channel", seed=1):
    """视黄醛：多烯链 + β-紫罗兰酮环（Å，相对蛋白中心）。从 G 螺旋（TM7）的赖氨酸处起，朝螺旋束中央横躺，
    在膜中部略偏胞外（z ≈ 0–2 Å）。返回 (chain, ring)，chain[0] 贴着 G 螺旋表面。"""
    h = helix_layout(kind, seed)
    gx, gy = h[6][:2]
    cx, cy = sum(p[0] for p in h) / 7, sum(p[1] for p in h) / 7
    d = math.hypot(cx - gx, cy - gy)
    ux, uy = (cx - gx) / d, (cy - gy) / d
    nx, ny = -uy, ux
    x0, y0 = gx + ux * (HELIX_R + 0.8), gy + uy * (HELIX_R + 0.8)
    chain = []
    for k in range(10):
        w = 0.5 if k % 2 else -0.5                     # 多烯链的锯齿
        chain.append((x0 + ux * k * 1.25 + nx * w, y0 + uy * k * 1.25 + ny * w, 0.2 * k))
    ex, ey, ez = chain[-1]
    rc = (ex + ux * 2.2, ey + uy * 2.2, ez)
    ring = [(rc[0] + 1.45 * math.cos(math.radians(60 * k)), rc[1] + 1.45 * math.sin(math.radians(60 * k)), rc[2])
            for k in range(7)]
    return chain, ring


def check_layout(kind="channel", seed=1, min_gap=0.6):
    """螺旋两两之间留出 min_gap Å，否则报错。返回最小空隙。"""
    h = helix_layout(kind, seed)
    gap = min(math.dist(h[i][:2], h[j][:2]) for i in range(7) for j in range(i + 1, 7)) - 2 * HELIX_R
    assert gap >= min_gap, f"helix gap {gap:.2f} Å < {min_gap}"
    return gap


# ---- bpy 部分 -------------------------------------------------------------------------------
def _helix_mesh(name, length, r):
    """沿 +Z、以原点为中心的带圆顶圆柱，表面有一道浅螺旋纹（α 螺旋的读法，不是原子模型）。"""
    import bmesh
    import bpy
    bm = bmesh.new()
    seg, rings = 18, 26
    prof = []
    for k in range(rings + 1):
        z = -length / 2 + length * k / rings
        prof.append((z, r))
    rows = []
    for k, (z, rr) in enumerate(prof):
        row = []
        for s in range(seg):
            ang = 2 * math.pi * s / seg
            bump = 1.0 + 0.07 * math.cos(ang * 1 - z / (5.4 * UNIT) * 2 * math.pi)   # 5.4 Å 螺距的浅纹
            row.append(bm.verts.new((rr * bump * math.cos(ang), rr * bump * math.sin(ang), z)))
        rows.append(row)
    for a, b in zip(rows[:-1], rows[1:]):
        for s in range(seg):
            bm.faces.new((a[s], a[(s + 1) % seg], b[(s + 1) % seg], b[s]))
    for row, sgn in ((rows[0], -1), (rows[-1], 1)):
        c = bm.verts.new((0, 0, sgn * (length / 2 + r * 0.6)))
        for s in range(seg):
            f = bm.faces.new((row[s], row[(s + 1) % seg], c) if sgn > 0 else (row[(s + 1) % seg], row[s], c))
    for f in bm.faces:
        f.smooth = True
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def build_opsin(name, kind="channel", loc=(0, 0, 0), mat=None, retinal_mat=None, pore_color=(0.55, 0.69, 1.0),
                cterm=False, seed=1, tag=None):
    """建一个七次跨膜蛋白。kind: channel（ChR，有孔）| pump（bR，质子泵）| cl_pump（NpHR，氯泵）。
    返回 dict(root, helices, loops, retinal, retinal_glow, pore, pore_mat, cterm, kind, center)。
    root 是空物体，整个蛋白跟着它动；pore 只在 channel 上有（发光的孔道，半径随打开程度变）。"""
    import bpy
    from mathutils import Vector
    import e2_shot as S
    tag = tag or (lambda o, r: o)
    root = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(root)
    root.location = loc
    lay = helix_layout(kind, seed)
    helices, loops = [], []
    tips = []
    for i, (x, y, tx, ty) in enumerate(lay):
        h = _helix_mesh(f"{name}_TM{i + 1}", HELIX_LEN * UNIT, HELIX_R * UNIT)
        h.parent = root
        h.location = (x * UNIT, y * UNIT, 0)
        h.rotation_euler = (tx, ty, 0)
        if mat is not None:
            h.data.materials.append(mat)
        tag(h, "structure")
        helices.append(h)
        ax = Vector((0, 0, 1))
        ax.rotate(h.rotation_euler)
        top = Vector(h.location) + ax * HELIX_LEN * UNIT / 2
        bot = Vector(h.location) - ax * HELIX_LEN * UNIT / 2
        tips.append((top, bot))
    # 环：相邻螺旋在膜两侧交替相连（A-B 在胞内，B-C 在胞外 ……），画成拱起的细管
    for i in range(6):
        side = 1 if i % 2 else 0                      # 0 = 底（胞内），1 = 顶（胞外）
        a = tips[i][side]
        b = tips[i + 1][side]
        sgn = 1 if side else -1
        mid = (a + b) / 2 + Vector((0, 0, sgn * 5.0 * UNIT))
        pts = [tuple(a), tuple(a.lerp(mid, 0.6) + Vector((0, 0, sgn * 1.5 * UNIT))), tuple(mid),
               tuple(b.lerp(mid, 0.6) + Vector((0, 0, sgn * 1.5 * UNIT))), tuple(b)]
        lp = S.tube(f"{name}_Loop{i}", pts, 1.5 * UNIT, mat, "structure")
        lp.parent = root
        loops.append(lp)
    # 视黄醛
    chain, ring = retinal_points(kind, seed)
    rmat = retinal_mat or mat
    lys = Vector((lay[6][0], lay[6][1], -1.0)) * UNIT
    ret = S.tube(f"{name}_Retinal", [tuple(lys)] + [tuple(Vector(p) * UNIT) for p in chain], 0.75 * UNIT, rmat, "structure")
    ret.parent = root
    ring_ob = S.tube(f"{name}_Ionone", [tuple(Vector(p) * UNIT) for p in ring], 0.7 * UNIT, rmat, "structure")
    ring_ob.parent = root
    rc = Vector(chain[5]) * UNIT
    rg_mat = S.halo(f"{name}_RetinalHaloMat", pore_color)
    rg = S.sphere(f"{name}_RetinalGlow", 9.0 * UNIT, tuple(rc), rg_mat, "emitter", seg=20, rings=12)
    rg.parent = root
    rg.location = tuple(rc)
    pore = pore_mat = None
    if kind == "channel":
        px, py = pore_center(kind, seed)
        pore_mat = S.glow(f"{name}_PoreMat", pore_color, 0.0)
        pore = S.cylinder(f"{name}_Pore", 1.0 * UNIT, HELIX_LEN * UNIT * 0.9, (0, 0, 0), pore_mat, "emitter", verts=24)
        pore.parent = root
        pore.location = (px * UNIT, py * UNIT, 0)
        pore["open_scale"] = 3.0                      # 完全打开时孔道半径 3 Å（示意）
        pore.scale = (0.4, 0.4, 1.0)
    ct = None
    if cterm:
        # 胞内侧的 C 端：一个空物体（CTerm）带着球形结构域和连到 G 螺旋底端的连接段，整体可以被「拿走」
        pos = Vector((2.0, -3.0, -(HELIX_LEN / 2 + 20))) * UNIT
        ct = bpy.data.objects.new(f"{name}_CTerm", None)
        bpy.context.scene.collection.objects.link(ct)
        ct.parent = root
        ct.location = pos
        dom = S.sphere(f"{name}_CTermDomain", 16.0 * UNIT, (0, 0, 0), mat, "structure", seg=32, rings=16,
                       scale=(1.25, 1.0, 0.8))
        dom.parent = ct
        g_bot = tips[6][1] - pos
        top = Vector((0, 0, 16.0 * 0.8 * UNIT))
        lk = S.tube(f"{name}_CTermLinker", [tuple(g_bot), tuple(g_bot.lerp(top, 0.5) + Vector((0.03, 0, 0))), tuple(top)],
                    1.6 * UNIT, mat, "structure")
        lk.parent = ct
    return {"root": root, "helices": helices, "loops": loops, "retinal": [ret, ring_ob], "retinal_glow": rg,
            "retinal_glow_mat": rg_mat, "pore": pore, "pore_mat": pore_mat, "cterm": ct, "kind": kind,
            "center": Vector(loc), "layout": lay, "seed": seed}


def set_open(p, f, amount, glow=None):
    """在帧 f 把孔打开到 amount（0 关，1 全开）：TM1/TM2/TM7 从孔心外移，孔道变粗；glow 给孔道亮度。
    泵没有孔，只改 glow（视黄醛光晕）。"""
    import e2_shot as S
    if p["kind"] == "channel":
        px, py = pore_center(p["kind"], p["seed"])
        for i in (0, 1, 6):
            x, y = p["layout"][i][:2]
            d = math.hypot(x - px, y - py) or 1.0
            s = OPEN_SHIFT * amount
            S.key(p["helices"][i], f, location=((x + (x - px) / d * s) * UNIT, (y + (y - py) / d * s) * UNIT, 0))
        r = 0.4 + (p["pore"]["open_scale"] - 0.4) * amount
        S.key(p["pore"], f, scale=(r, r, 1.0))
        if glow is not None:
            S.set_strength(p["pore_mat"], f, glow)
    elif glow is not None:
        S.set_gain(p["retinal_glow_mat"], f, glow)


def flash_retinal(p, f, peak=3.0, rise=3, fall=14):
    """视黄醛吸光：光晕在 rise 帧内亮到 peak，再在 fall 帧内熄灭。"""
    import e2_shot as S
    m = p["retinal_glow_mat"]
    S.set_gain(m, f - 1, 0.0)
    S.set_gain(m, f + rise, peak)
    S.set_gain(m, f + rise + fall, 0.0)


def pore_path(p, z_from=0.45, z_to=-0.45):
    """离子穿孔的路径（BU，世界坐标）：从胞外 z_from 进孔，沿孔道下行，出孔后略散开到胞内 z_to。"""
    px, py = pore_center(p["kind"], p["seed"])
    c = p["center"]
    x, y = c.x + px * UNIT, c.y + py * UNIT
    return [(x + 0.03, y - 0.02, c.z + z_from), (x, y, c.z + 0.26), (x, y, c.z), (x, y, c.z - 0.26),
            (x - 0.04, y + 0.03, c.z + z_to)]


def pump_path(p, z_from=-0.45, z_to=0.45):
    """泵的「接力」路径：经过视黄醛附近，从一侧到另一侧（不画贯通的孔）。"""
    c = p["center"]
    chain, _ = retinal_points(p["kind"], p["seed"])
    rx, ry = chain[2][0] * UNIT, chain[2][1] * UNIT
    return [(c.x + rx - 0.12, c.y + ry - 0.05, c.z + z_from), (c.x + rx * 0.5, c.y + ry, c.z - 0.18),
            (c.x + rx, c.y + ry, c.z - 0.01), (c.x + rx * 0.6, c.y + ry * 1.2, c.z + 0.2),
            (c.x + rx + 0.1, c.y + ry + 0.06, c.z + z_to)]


def build_pore_channel(name, loc=(0, 0, 0), mat=None, n=6, r=13.0, seed=2, tag=None):
    """第一幕的通用离子孔：n 根桶板围成一圈（不对应具体通道），中间一根发光孔道。返回 dict(root, staves, pore, pore_mat)。"""
    import bpy
    import e2_shot as S
    tag = tag or (lambda o, r_: o)
    rnd = random.Random(seed)
    root = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(root)
    root.location = loc
    staves = []
    for i in range(n):
        a = 2 * math.pi * i / n
        h = _helix_mesh(f"{name}_Stave{i}", HELIX_LEN * UNIT, 5.2 * UNIT)
        h.parent = root
        h.location = (r * math.cos(a) * UNIT, r * math.sin(a) * UNIT, 0)
        h.rotation_euler = (math.radians(rnd.uniform(-4, 4)), math.radians(rnd.uniform(-4, 4)), 0)
        if mat is not None:
            h.data.materials.append(mat)
        tag(h, "structure")
        staves.append(h)
    pm = S.glow(f"{name}_PoreMat", (0.7, 0.8, 1.0), 0.0)
    pore = S.cylinder(f"{name}_Pore", 3.0 * UNIT, HELIX_LEN * UNIT * 0.9, (0, 0, 0), pm, "emitter", verts=24)
    pore.parent = root
    return {"root": root, "staves": staves, "pore": pore, "pore_mat": pm, "center": loc}
