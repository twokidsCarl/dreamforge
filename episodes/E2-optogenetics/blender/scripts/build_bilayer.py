"""参数化脂质双层剖面 + 离子（A–D 段所有「膜」「离子流」镜头共用）。

几何依据（示意，核查表记 simplified；P6 要补 research/visual/membrane.md 的出处）：
  - 脂质双层：两层磷脂，亲水头朝外、疏水尾朝里，总厚约 4 nm（教科书通用值，例如 Alberts《Molecular Biology of
    the Cell》第 10 章）。这里头基半径 4 Å、头基间距 8 Å、双层厚 40 Å（头到头）。
  - 离子画成发光小球，放大很多倍（真实的 Na⁺ / Cl⁻ 只有 1–2 Å），只是为了看得见；种类靠颜色区分：
    阳离子 = 线稿白偏蓝，H⁺ = 膜青（更小），Cl⁻ = 抑制琥珀。颜色约定见 e2_common 和 storyboard/page.yaml。
单位：1 Å = 0.01 BU（与 build_purple_membrane 一致），膜面是 z = 0 的中平面，+z 是胞外，-z 是胞内。
"""
import math
import random

UNIT = 0.01
THICK = 40.0                # 头到头，Å
HEAD_R = 4.0
HEAD_PITCH = 8.0
TAIL_R = 1.1
ION_R = {"cation": 3.4, "h": 2.4, "cl": 3.8}


def lipid_sites(half_w, half_d, holes=(), pitch=HEAD_PITCH, seed=3):
    """单层头基中心 (x, y)，Å：六方排布加一点抖动，挖掉 holes=[(x, y, r)]（Å）里的位置。"""
    rnd = random.Random(seed)
    pts = []
    dy = pitch * math.sqrt(3) / 2
    j = 0
    y = -half_d
    while y <= half_d:
        x = -half_w + (pitch / 2 if j % 2 else 0)
        while x <= half_w:
            px, py = x + rnd.uniform(-0.8, 0.8), y + rnd.uniform(-0.8, 0.8)
            if all(math.hypot(px - hx, py - hy) > hr for hx, hy, hr in holes):
                pts.append((px, py))
            x += pitch
        y += dy
        j += 1
    return pts


def build_bilayer(name="Bilayer", half_w=200.0, half_d=120.0, holes=(), section_rows=3, seed=3):
    """建双层：头基（一个网格）、剖面上可见的尾链（一个网格，只建靠前 section_rows 排，后面被头基挡住）、
    以及中间的疏水芯（一块薄板，xray / energy 里给剖面一个底色）。返回 dict(heads, tails, core)。
    holes 的单位是 Å，蛋白所在处要挖空。"""
    import bmesh
    import bpy
    rnd = random.Random(seed)
    sites = lipid_sites(half_w, half_d, holes, seed=seed)
    bm = bmesh.new()
    zt = THICK / 2 - HEAD_R
    for leaf in (1, -1):
        for x, y in sites:
            z = leaf * (zt + rnd.uniform(-0.6, 0.6))
            m = bmesh.ops.create_icosphere(bm, subdivisions=1, radius=HEAD_R * UNIT)
            for v in m["verts"]:
                v.co.x += x * UNIT
                v.co.y += y * UNIT
                v.co.z += z * UNIT
    for f in bm.faces:
        f.smooth = True
    me = bpy.data.meshes.new(name + "Heads")
    bm.to_mesh(me)
    bm.free()
    heads = bpy.data.objects.new(name + "Heads", me)
    bpy.context.scene.collection.objects.link(heads)

    # 尾链：每个头两根，向中平面伸，略弯（只建最前面几排，剖面上看得到）
    bm = bmesh.new()
    y_front = -half_d
    for leaf in (1, -1):
        for x, y in sites:
            if y > y_front + section_rows * HEAD_PITCH:
                continue
            for k, dx in enumerate((-1.6, 1.6)):
                z0 = leaf * (zt - HEAD_R * 0.6)
                pts = []
                for s in range(5):
                    t = s / 4
                    pts.append(((x + dx + math.sin(t * 3.1 + k + x) * 0.9) * UNIT, y * UNIT,
                                (z0 - leaf * t * (zt - 2.0)) * UNIT))
                prev = None
                for p in pts:
                    ring = []
                    for a in range(5):
                        ang = 2 * math.pi * a / 5
                        ring.append(bm.verts.new((p[0] + TAIL_R * UNIT * math.cos(ang), p[1] + TAIL_R * UNIT * math.sin(ang), p[2])))
                    if prev:
                        for a in range(5):
                            bm.faces.new((prev[a], prev[(a + 1) % 5], ring[(a + 1) % 5], ring[a]))
                    prev = ring
    me = bpy.data.meshes.new(name + "Tails")
    bm.to_mesh(me)
    bm.free()
    tails = bpy.data.objects.new(name + "Tails", me)
    bpy.context.scene.collection.objects.link(tails)

    # 疏水芯：薄板，比尾链稍窄
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= 2 * half_w * UNIT
        v.co.y *= 2 * half_d * UNIT
        v.co.z *= (THICK - 4 * HEAD_R) * UNIT
    me = bpy.data.meshes.new(name + "Core")
    bm.to_mesh(me)
    bm.free()
    core = bpy.data.objects.new(name + "Core", me)
    bpy.context.scene.collection.objects.link(core)
    if holes:                                           # 芯也挖洞：蛋白从这里穿过
        for i, (hx, hy, hr) in enumerate(holes):
            bpy.ops.mesh.primitive_cylinder_add(radius=hr * 0.8 * UNIT, depth=THICK * UNIT,
                                                location=(hx * UNIT, hy * UNIT, 0))
            cut = bpy.context.object
            cut.name = f"{name}Hole{i}"
            mod = core.modifiers.new(f"Hole{i}", "BOOLEAN")
            mod.operation = "DIFFERENCE"
            mod.object = cut
            cut.hide_render = cut.hide_viewport = True
    return {"heads": heads, "tails": tails, "core": core}


def ion_material(kind):
    """离子发光材质（一种离子一个材质，同材质共享）。"""
    import bpy
    import e2_common as E
    import materials as M
    name = "Ion_" + kind
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    col = {"cation": (200, 222, 255), "h": E.MEMBRANE, "cl": E.AMBER}[kind]
    return M.emission(name, E.srgb_to_linear(col), 6.0)


def ion(name, kind, loc, role="emitter"):
    """一个离子小球。loc 单位 BU。"""
    import bpy
    import styles
    bpy.ops.mesh.primitive_uv_sphere_add(radius=ION_R[kind] * UNIT, segments=16, ring_count=10, location=loc)
    ob = bpy.context.object
    ob.name = name
    for p in ob.data.polygons:
        p.use_smooth = True
    ob.data.materials.append(ion_material(kind))
    styles.tag(ob, role)
    return ob


def cloud(prefix, kind, n, center, half, seed=11, role="emitter"):
    """在 center ± half（BU）的盒子里撒 n 个离子，返回对象列表。"""
    rnd = random.Random(seed)
    out = []
    for i in range(n):
        p = tuple(center[k] + rnd.uniform(-half[k], half[k]) for k in range(3))
        out.append(ion(f"{prefix}{i}", kind, p, role))
    return out


def jitter(ob, f0, f1, amp, seed, step=6):
    """离子在原地热运动（小幅随机游走，关键帧每 step 帧一个）。"""
    rnd = random.Random(seed)
    base = tuple(ob.location)
    for f in range(f0, f1 + 1, step):
        ob.location = tuple(base[k] + rnd.uniform(-amp, amp) for k in range(3))
        ob.keyframe_insert("location", frame=f)


def through(ob, path, f0, f1, hold_after=True):
    """离子沿 path（BU 点列）从 f0 走到 f1，先慢后快再慢。之前停在 path[0]，之后停在 path[-1]。"""
    import e2_shot as S
    ob.location = path[0]
    ob.keyframe_insert("location", frame=f0)
    n = max(2, f1 - f0)
    seg = [math.dist(path[i], path[i + 1]) for i in range(len(path) - 1)]
    tot = sum(seg) or 1.0
    for f in range(f0 + 1, f1 + 1, 2):
        u = S.smooth((f - f0) / n) * tot
        for i, L in enumerate(seg):
            if u <= L or i == len(seg) - 1:
                t = 0 if L == 0 else min(1.0, u / L)
                ob.location = tuple(path[i][k] + (path[i + 1][k] - path[i][k]) * t for k in range(3))
                break
            u -= L
        ob.keyframe_insert("location", frame=f)
