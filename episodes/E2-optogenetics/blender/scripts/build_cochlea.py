"""参数化耳蜗剖面 + 一根示意的光学阵列（C_17a）。

几何依据（示意，核查表记 simplified；P6 要补 research/visual/cochlea.md）：
  - 人耳蜗是绕蜗轴约 2.5–2.75 圈的螺旋骨管，管内被前庭膜（Reissner 膜）和基底膜分成三条阶：上方前庭阶、中间中阶（蜗管，
    截面近三角形）、下方鼓阶；螺旋神经节的胞体位于蜗轴内的 Rosenthal 管，沿蜗轴绕行。教科书通用画法，例如 Purves
    《Neuroscience》第 13 章、Kandel 第 26 章的蜗轴切面示意图。这里取 2.5 圈。
  - 尺寸量级：底圈直径约 9 mm、高约 5 mm（教科书通用值）。1 BU = 1 mm。管半径从底圈 0.8 mm 收到顶圈 0.4 mm（示意，比真实截面略细，好让相邻两圈分开）。
  - 光学阵列：只是一根沿鼓阶走一圈多的发光细杆，表示「用光代替电流刺激螺旋神经节」这个想法（2023 年综述：仍处临床前）。
    不画触点数、不画成某个产品、不标试验编号。
  - 剖切：只留 y ≥ 0 的一半（螺旋各部分只扫保留的半圈，见 kept_ranges；蜗轴用布尔），相机从 -Y 看蜗轴切面：每侧能看到 2–3 个管的截面，越往上越小。
坐标：蜗轴沿 +Z，底圈在 z = 0。
"""
import math

TURNS = 2.5
R_BASE, R_APEX = 4.1, 1.15        # 螺旋中心线半径，mm
H = 5.0                           # 底到顶，mm
TUBE_BASE, TUBE_APEX = 0.8, 0.4   # 相邻两圈的管不能相交（否则剖切布尔会坏）：每圈升高 2 mm > 底圈管径 1.6 mm


def spiral(t):
    """t∈[0,1] 沿螺旋从底到顶：返回 (中心线点, 管半径, 绕行角)。"""
    a = 2 * math.pi * TURNS * t
    r = R_BASE + (R_APEX - R_BASE) * t ** 0.8
    z = H * t ** 0.9
    return (r * math.cos(a), r * math.sin(a), z), TUBE_BASE + (TUBE_APEX - TUBE_BASE) * t, a


def _frame(t):
    """螺旋上 t 处的局部标架：径向外 e_r、竖直 e_z（管截面在 e_r-e_z 平面里）。"""
    _, _, a = spiral(t)
    return (math.cos(a), math.sin(a), 0.0), (0.0, 0.0, 1.0)


def kept_ranges():
    """剖切面 y = 0 恰好在每半圈处（绕行角 a = kπ）切开螺旋：截面在 e_r-e_z 平面里，整块截面的 y 符号 = sin a 的符号。
    所以留下 y ≥ 0 的一半 = 只扫 sin a ≥ 0 的那些 t 段，不用布尔。"""
    out, k = [], 0
    while k / TURNS < 1.0:
        out.append((k / TURNS, min(1.0, (k + 0.5) / TURNS)))
        k += 1
    return out


def _ribbon_into(bm, t0, t1, prof, n=260, closed=False):
    """沿螺旋扫一条截面折线 prof(t) -> [(u_r, u_z)]（管截面局部坐标，单位 = 管半径倍数）。closed：截面首尾相连。"""
    rows = []
    for i in range(n + 1):
        t = t0 + (t1 - t0) * i / n
        c, rad, _ = spiral(t)
        er, ez = _frame(t)
        rows.append([bm.verts.new((c[0] + rad * (u * er[0]), c[1] + rad * (u * er[1]), c[2] + rad * w)) for u, w in prof(t)])
    for a, b in zip(rows[:-1], rows[1:]):
        m = len(a) if closed else len(a) - 1
        for k in range(m):
            f = bm.faces.new((a[k], a[(k + 1) % len(a)], b[(k + 1) % len(b)], b[k]))
            f.smooth = True


def _circle(k=28):
    return [(math.cos(2 * math.pi * i / k), math.sin(2 * math.pi * i / k)) for i in range(k)]


def _cut(ob, name):
    """布尔差集：去掉 y < 0 的一半。"""
    import bpy
    cutter = bpy.data.objects.get(name + "Cutter")
    if cutter is None:
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, -10.0, 2.0))
        cutter = bpy.context.object
        cutter.name = name + "Cutter"
        cutter.scale = (30, 20, 30)
        cutter.hide_render = cutter.hide_viewport = True
    m = ob.modifiers.new("Cut", "BOOLEAN")
    m.operation = "DIFFERENCE"
    m.object = cutter
    m.solver = "EXACT"
    return cutter


def build_cochlea(name, loc=(0, 0, 0), mat=None, array_color=(0.55, 0.69, 1.0), tag=None, open_top=False):
    """open_top=True（v7 C_17a 俯视用）：不做 y 半剖，整 2.5 圈都扫出来，但骨管只留下半圈截面（顶盖剖掉、前庭膜不画、基底膜改成 shell），
    沿蜗轴俯视时看得到一条连续的螺旋槽，阵列躺在槽里。
    建半个耳蜗：骨管壁（shell）、前庭膜和基底膜（structure）、蜗轴（shell，xray 里是玻璃，看得见里面的螺旋神经节）、螺旋神经节（structure 小球）、
    光学阵列（emitter，发光细杆，可 reveal / 淡出）。返回 dict(root, wall, reissner, basilar, modiolus, ganglion,
    arrays, array_mat, cutter)。"""
    import bmesh
    import bpy
    import e2_shot as S
    tag = tag or (lambda o, r: o)
    root = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(root)
    root.location = loc

    def obj(nm, bm, m, role):
        me = bpy.data.meshes.new(nm)
        bm.to_mesh(me)
        bm.free()
        ob = bpy.data.objects.new(nm, me)
        bpy.context.scene.collection.objects.link(ob)
        ob.parent = root
        if m is not None:
            ob.data.materials.append(m)
        tag(ob, role)
        return ob

    circ = _circle()
    rngs = [(0.0, 1.0)] if open_top else kept_ranges()
    nseg = 420 if open_top else 110
    trough = [(math.cos(math.pi + math.pi * i / 16), math.sin(math.pi + math.pi * i / 16)) for i in range(17)]
    bm = bmesh.new()
    for t0, t1 in rngs:
        _ribbon_into(bm, t0, t1, (lambda t: trough) if open_top else (lambda t: circ), n=nseg, closed=not open_top)
    wall = obj(f"{name}_Wall", bm, mat, "structure" if open_top else "shell")   # 开顶：骨管槽做实体，阵列看得出躺在槽里
    s = wall.modifiers.new("Solid", "SOLIDIFY")
    s.thickness = 0.12
    s.offset = 1
    # 基底膜：从内侧骨螺旋板（蜗轴侧，u = -1）斜到外侧壁，略低于中线；前庭膜：从内侧斜向外上方。两者围出三角形的中阶。
    bm = bmesh.new()
    for t0, t1 in rngs:
        _ribbon_into(bm, t0, t1, lambda t: [(-0.98, -0.08), (0.0, -0.12), (0.97, -0.16)], n=nseg)
    basilar = obj(f"{name}_Basilar", bm, mat, "shell" if open_top else "structure")   # 俯视：基底膜做成鬼影玻璃，透出下面鼓阶里的阵列
    bm = bmesh.new()
    if not open_top:
        for t0, t1 in rngs:
            _ribbon_into(bm, t0, t1, lambda t: [(-0.62, -0.06), (0.1, 0.34), (0.78, 0.6)], n=110)
    reissner = obj(f"{name}_Reissner", bm, mat, "structure")
    for m_ in (basilar, reissner):
        sm = m_.modifiers.new("Solid", "SOLIDIFY")
        sm.thickness = 0.035
    # 蜗轴：中央的锥体
    modiolus = S.cylinder(f"{name}_Modiolus", 0.85, H * 0.95, (0, 0, H * 0.45), mat, "shell", verts=48)
    modiolus.parent = root
    tp = modiolus.modifiers.new("Taper", "SIMPLE_DEFORM")
    tp.deform_method = "TAPER"
    tp.deform_axis = "Z"
    tp.factor = -0.75
    # 螺旋神经节：沿螺旋内侧（蜗轴里）的一串小球
    bm = bmesh.new()
    for i in range(120):
        t = i / 119 * 0.92
        c, rad, a = spiral(t)
        rr = math.hypot(c[0], c[1]) - rad * 1.45
        if not open_top and rr * math.sin(a) < 0.25:                 # 只放在剖切后留下的一半里（小球互相重叠，布尔切不干净）
            continue
        m = bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.13 + 0.05 * (1 - t))
        for v in m["verts"]:
            v.co.x += rr * math.cos(a)
            v.co.y += rr * math.sin(a)
            v.co.z += c[2] - rad * 0.1
    ganglion = obj(f"{name}_SpiralGanglion", bm, mat, "structure")
    # 光学阵列：鼓阶里（管截面下半、靠蜗轴一侧）走 0 → 0.48（约 1.2 圈）
    pts = []
    for i in range(140):
        t = 0.48 * i / 139
        c, rad, a = spiral(t)
        er, _ = _frame(t)
        pts.append((c[0] - er[0] * rad * 0.35, c[1] - er[1] * rad * 0.35, c[2] - rad * 0.55))
    amat = S.glow(f"{name}_ArrayMat", array_color, 0.0)
    # 只保留剖切后留下的那半边（y ≥ 0）里的段，每段一根管（曲线做不了布尔）
    segs, cur = [], []
    for p in pts:
        if open_top or p[1] >= 0.0:
            cur.append(p)
        elif cur:
            segs.append(cur)
            cur = []
    if cur:
        segs.append(cur)
    arrays = []
    for k, sp in enumerate(s_ for s_ in segs if len(s_) > 2):
        a_ = S.tube(f"{name}_OpticalArray{k}", sp, 0.16, amat, "emitter", res=3)
        a_.parent = root
        arrays.append(a_)
    cutter = None if open_top else _cut(modiolus, name)                    # 蜗轴是简单的凸体，布尔可靠
    return {"root": root, "wall": wall, "reissner": reissner, "basilar": basilar, "modiolus": modiolus,
            "ganglion": ganglion, "arrays": arrays, "array_mat": amat, "array_pts": pts, "cutter": cutter}
