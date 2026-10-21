"""参数化视网膜剖面和眼球剖面（C 段 C_07a / C_07b / C_08a / C_09b / C_10a 共用）。

几何依据（全部示意，核查表记 simplified；P6 要补 research/visual/retina.md，逐条附原文）：
  - 视网膜分层：自外（巩膜侧）向内（玻璃体侧）依次是色素上皮（RPE）、感光细胞外段 / 内段（视杆、视锥）、外核层（ONL，
    感光细胞胞体）、外丛状层（OPL）、内核层（INL，双极 / 水平 / 无长突细胞）、内丛状层（IPL）、神经节细胞层（GCL）、
    神经纤维层（NFL，神经节细胞轴突汇向视盘），最内是内界膜。教科书通用分层，例如 Kandel《Principles of Neural Science》
    第 22 章、Purves《Neuroscience》第 11 章的视网膜示意图。光从玻璃体侧进来，先穿过内层才到感光细胞。
  - 各层厚度只取相对比例（感光层和 ONL 最厚，OPL 最薄），不对应具体部位的实测值。1 BU = 100 µm，总厚约 2.6 BU（≈ 260 µm，
    人视网膜中周部的量级）。
  - 视网膜色素变性（RP）：感光细胞逐渐死去，内层（尤其神经节细胞）相对保留。这里用 photoreceptor_density（0–1，保留比例）
    和 dying_groups（分几批消失）表示，不对应病程的具体时间。
  - 光遗传「可转导」：只画神经节细胞胞体上的光晕（通道装在神经节细胞上：Sahel et al. 2021, Nat Med 27:1223 用 AAV2 携带
    ChrimsonR，主要转导视网膜神经节细胞）。
  - 眼球剖面：角膜、虹膜、晶状体、玻璃体、视网膜（衬在后 3/4 内壁）、巩膜、视神经。眼轴约 24 mm（教科书通用值），这里
    1 BU = 10 mm，眼球半径 1.2 BU；玻璃体内注射从睫状体平坦部附近进针（示意，不标距离）。
坐标：视网膜剖面以 root 为原点，x 横向，y 景深，z 是层的方向：z = 0 是内界膜（玻璃体侧，神经节细胞在最下），向 +z 依次往外，
RPE 在最上。眼球的光轴沿 +X：角膜在 -X，视神经在 +X；剖切面 y = 0，只建 y ≥ 0 的半个，相机在 -Y 看剖面。
"""
import math
import random

# 层：(名字, 厚度 BU)，自内（z = 0，玻璃体侧）向外
LAYERS = (("NFL", 0.18), ("GCL", 0.26), ("IPL", 0.34), ("INL", 0.36), ("OPL", 0.14), ("ONL", 0.44),
          ("PR", 0.62), ("RPE", 0.14))


def layer_stack():
    """[(名字, z0, z1)]，自内向外。"""
    out, z = [], 0.0
    for name, t in LAYERS:
        out.append((name, z, z + t))
        z += t
    return out


def layer_z(name):
    """层中心的 z。"""
    for n, z0, z1 in layer_stack():
        if n == name:
            return (z0 + z1) / 2
    raise KeyError(name)


def photoreceptor_sites(width, depth, pitch=0.11, seed=4):
    """感光细胞 (x, y, kind)：方格加抖动；约每 6 个里 1 个视锥（周边视网膜视杆占多数，示意比例）。"""
    rnd = random.Random(seed)
    out = []
    nx, ny = int(width / pitch), max(1, int(depth / pitch))
    for j in range(ny):
        for i in range(nx):
            x = -width / 2 + (i + 0.5) * pitch + rnd.uniform(-0.02, 0.02)
            y = -depth / 2 + (j + 0.5) * pitch + rnd.uniform(-0.02, 0.02)
            out.append((x, y, "cone" if rnd.random() < 0.17 else "rod"))
    return out


def ganglion_sites(width, n, seed=6):
    """神经节细胞胞体 (x, y)：一排，略抖动（剖面上看到的一层）。"""
    rnd = random.Random(seed)
    return [(-width / 2 + (i + 0.5) * width / n + rnd.uniform(-0.05, 0.05), rnd.uniform(-0.12, 0.12)) for i in range(n)]


# ---- bpy 部分 -------------------------------------------------------------------------------
def _cyl_into(bm, p0, p1, r0, r1, seg=8):
    """bmesh 里加一段截锥（p0 半径 r0 → p1 半径 r1，z 向），带底盖。"""
    rings = []
    for (x, y, z), r in ((p0, r0), (p1, r1)):
        rings.append([bm.verts.new((x + r * math.cos(2 * math.pi * s / seg), y + r * math.sin(2 * math.pi * s / seg), z))
                      for s in range(seg)])
    for s in range(seg):
        f = bm.faces.new((rings[0][s], rings[0][(s + 1) % seg], rings[1][(s + 1) % seg], rings[1][s]))
        f.smooth = True
    bm.faces.new(list(reversed(rings[0])))
    bm.faces.new(rings[1])


def _ball_into(bm, c, r, sub=1, scale=(1, 1, 1)):
    import bmesh
    m = bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=r)
    for v in m["verts"]:
        v.co.x = c[0] + v.co.x * scale[0]
        v.co.y = c[1] + v.co.y * scale[1]
        v.co.z = c[2] + v.co.z * scale[2]
    for f in {f for v in m["verts"] for f in v.link_faces}:
        f.smooth = True


def _mesh_object(name, bm, parent, mat, role, tag):
    import bpy
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    ob.parent = parent
    if mat is not None:
        ob.data.materials.append(mat)
    tag(ob, role)
    return ob


def _photoreceptor_into(bm, x, y, kind, zs):
    """一个感光细胞：外段（PR 层上半）、内段（PR 层下半，视锥是锥形）、胞体（ONL）、到 OPL 的细轴突。"""
    pr0, pr1 = zs["PR"]
    onl0, onl1 = zs["ONL"]
    opl0, opl1 = zs["OPL"]
    mid = pr0 + (pr1 - pr0) * 0.45
    if kind == "rod":
        _cyl_into(bm, (x, y, mid), (x, y, pr1 - 0.02), 0.022, 0.022)            # 外段：细长圆柱
        _cyl_into(bm, (x, y, pr0), (x, y, mid), 0.018, 0.024)                   # 内段
    else:
        _cyl_into(bm, (x, y, mid), (x, y, mid + (pr1 - mid) * 0.55), 0.03, 0.012)  # 视锥外段：短而尖
        _cyl_into(bm, (x, y, pr0), (x, y, mid), 0.024, 0.038)                   # 内段：粗
    zc = onl0 + (onl1 - onl0) * random.Random(int(x * 1000) ^ int(y * 1000)).uniform(0.25, 0.8)
    _ball_into(bm, (x, y, zc), 0.032, sub=1, scale=(1, 1, 1.35))
    _cyl_into(bm, (x, y, opl0 + 0.03), (x, y, zc), 0.006, 0.008, seg=5)


def build_retina(name, width=6.0, depth=1.0, photoreceptor_density=1.0, dying_groups=0, n_ganglion=16,
                 seed=4, mat=None, glow_color=(0.55, 0.69, 1.0), tag=None):
    """建一段视网膜剖面。mat 可以是一个材质，也可以是 dict（键 plexiform / rpe / pr / inl / rgc / ilm，缺的用 "default"），
    让各层在 xray 这类保留原材质的风格里分得开。photoreceptor_density：一直保留的感光细胞比例；dying_groups > 0 时，其余的感光细胞分成这么多批，
    各自一个网格（dying[k]），由调用方按时间隐藏或缩没（表现变稀的过程）；dying_groups = 0 时其余的直接不建。
    返回 dict(root, layers{名字: 板}, rpe, photoreceptors, dying, inl, ganglia[{soma, axon, halo, halo_mat, x, y}],
    nfl, ilm, stack, width, depth)。"""
    import bmesh
    import bpy
    import e2_shot as S
    tag = tag or (lambda o, r: o)
    mats = mat if isinstance(mat, dict) else {}

    def m_(key):
        return mats.get(key, mats.get("default")) if mats else mat
    rnd = random.Random(seed)
    root = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(root)
    zs = {n: (z0, z1) for n, z0, z1 in layer_stack()}

    # 丛状层、神经纤维层：半透明薄板（shell：xray 里是玻璃，clay / energy 里是体块）
    layers = {}
    for ln in ("OPL", "IPL", "NFL"):
        z0, z1 = zs[ln]
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        for v in bm.verts:
            v.co.x *= width
            v.co.y *= depth
            v.co.z = (z0 + z1) / 2 + v.co.z * (z1 - z0)
        layers[ln] = _mesh_object(f"{name}_{ln}", bm, root, m_("plexiform"), "shell", tag)

    # RPE：一排六棱柱，色素细胞
    bm = bmesh.new()
    z0, z1 = zs["RPE"]
    pitch = 0.16
    for j in range(max(1, int(depth / pitch))):
        for i in range(int(width / pitch)):
            x = -width / 2 + (i + 0.5 + 0.5 * (j % 2)) * pitch
            if x > width / 2:
                continue
            y = -depth / 2 + (j + 0.5) * pitch
            _cyl_into(bm, (x, y, z0), (x, y, z1), pitch * 0.55, pitch * 0.55, seg=6)
    rpe = _mesh_object(f"{name}_RPE", bm, root, m_("rpe"), "structure", tag)

    # 感光细胞：保留的一个网格；将要消失的分批
    sites = photoreceptor_sites(width, depth, seed=seed)
    keep_bm = bmesh.new()
    groups = [bmesh.new() for _ in range(dying_groups)]
    for x, y, kind in sites:
        if rnd.random() < photoreceptor_density:
            _photoreceptor_into(keep_bm, x, y, kind, zs)
        elif dying_groups:
            _photoreceptor_into(groups[rnd.randrange(dying_groups)], x, y, kind, zs)
    photoreceptors = _mesh_object(f"{name}_Photoreceptors", keep_bm, root, m_("pr"), "structure", tag)
    dying = [_mesh_object(f"{name}_Dying{k}", g, root, m_("pr"), "structure", tag) for k, g in enumerate(groups)]

    # 内核层：双极 / 水平 / 无长突细胞胞体；双极细胞显式串起 ONL→INL→IPL（P0-6）
    bm = bmesh.new()
    i0, i1 = zs["INL"]
    ipl_mid = (zs["IPL"][0] + zs["IPL"][1]) / 2
    for k in range(int(width / 0.12)):
        for row in range(3):
            x = -width / 2 + (k + 0.5) * 0.12 + rnd.uniform(-0.03, 0.03)
            y = rnd.uniform(-depth / 2 + 0.05, depth / 2 - 0.05)
            z = i0 + (i1 - i0) * (0.22 + 0.28 * row) + rnd.uniform(-0.02, 0.02)
            _ball_into(bm, (x, y, z), 0.038, sub=2, scale=(1, 1, 1.15))
            if row == 1:  # 中排胞体做成双极：上连 ONL，下连 IPL
                _cyl_into(bm, (x, y, zs["ONL"][0] + 0.06), (x, y, z), 0.010, 0.007, seg=6)
                _cyl_into(bm, (x, y, z), (x, y, ipl_mid), 0.007, 0.009, seg=6)
    inl = _mesh_object(f"{name}_INL", bm, root, m_("inl"), "structure", tag)

    # 神经节细胞：每个一个胞体（可单独打光晕），树突伸进 IPL，轴突拐进 NFL 往 +x 走（汇向视盘的方向，示意）
    ganglia = []
    g0, g1 = zs["GCL"]
    for gi, (x, y) in enumerate(ganglion_sites(width, n_ganglion, seed=seed + 2)):
        zc = (g0 + g1) / 2
        soma = S.sphere(f"{name}_RGC{gi}", 0.075, (x, y, zc), m_("rgc"), "structure", seg=20, rings=12, scale=(1.1, 1, 0.9))
        soma.parent = root
        dend = []
        for k in range(3):
            a = math.radians(-50 + 50 * k) + rnd.uniform(-0.2, 0.2)
            top = (x + math.sin(a) * 0.22, y + rnd.uniform(-0.05, 0.05), zs["IPL"][0] + (zs["IPL"][1] - zs["IPL"][0]) * rnd.uniform(0.3, 0.8))
            dend.append(S.tube(f"{name}_RGC{gi}Dend{k}", [(x, y, zc + 0.05), ((x + top[0]) / 2, y, (zc + top[2]) / 2 + 0.03), top],
                               0.012, m_("rgc"), "structure", res=1))
        ax = S.tube(f"{name}_RGC{gi}Axon", [(x, y, zc - 0.05), (x + 0.08, y, zs["NFL"][0] + 0.09),
                                            (x + 0.6, y, zs["NFL"][0] + 0.08 + rnd.uniform(-0.03, 0.03)),
                                            (width / 2, y, zs["NFL"][0] + 0.07)], 0.014, m_("rgc"), "structure", res=1)
        for o in dend + [ax]:
            o.parent = root
        hm = S.halo(f"{name}_RGC{gi}HaloMat", glow_color, 0.0)
        h = S.sphere(f"{name}_RGC{gi}Halo", 0.2, (x, y, zc), hm, "emitter", seg=20, rings=12)
        h.parent = root
        ganglia.append({"soma": soma, "axon": ax, "dend": dend, "halo": h, "halo_mat": hm, "x": x, "y": y, "z": zc})

    # 内界膜：最内一层极薄的板
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= width
        v.co.y *= depth
        v.co.z = -0.01 + v.co.z * 0.02
    ilm = _mesh_object(f"{name}_ILM", bm, root, m_("ilm"), "structure", tag)
    return {"root": root, "layers": layers, "rpe": rpe, "photoreceptors": photoreceptors, "dying": dying, "inl": inl,
            "ganglia": ganglia, "ilm": ilm, "stack": layer_stack(), "width": width, "depth": depth}


def fade_dying(r, f0, f1):
    """f0→f1 之间，dying 网格一批批缩没（z 向压扁到 0）再隐藏：感光层变稀。"""
    import e2_shot as S
    n = len(r["dying"])
    if not n:
        return
    zc = layer_z("PR")
    for k, ob in enumerate(r["dying"]):
        a = f0 + (f1 - f0) * k / n
        b = a + max(6, (f1 - f0) / n)
        # 以 PR 层中心为基准压扁：z → z·s + zc·(1 − s)，s 从 1 到 0.02
        S.key(ob, int(a), scale=(1, 1, 1), location=(0, 0, 0))
        S.key(ob, int(b), scale=(1, 1, 0.02), location=(0, 0, zc * 0.98))
        S.show_between(ob, 1, int(b) + 1)


def ganglion_glow(r, keys, which=None):
    """神经节细胞光晕关键帧：keys = [(frame, gain)]；which = 下标列表（默认全部）。"""
    import e2_shot as S
    for i, g in enumerate(r["ganglia"]):
        if which is not None and i not in which:
            continue
        for f, v in keys:
            S.set_gain(g["halo_mat"], f, v)


def ganglion_pulses(r, f0, f1, period, peak=3.0, seed=9, frac=0.5):
    """f0→f1 之间，神经节细胞被一次次光脉冲驱动：每个周期随机挑 frac 的细胞闪一下（稀疏脉冲，不是连续亮）。"""
    import e2_shot as S
    rnd = random.Random(seed)
    for g in r["ganglia"]:
        S.set_gain(g["halo_mat"], 1, 0.0)
    f = f0
    while f < f1:
        for g in r["ganglia"]:
            if rnd.random() < frac:
                m = g["halo_mat"]
                S.set_gain(m, f - 1, 0.0)
                S.set_gain(m, f + 2, peak)
                S.set_gain(m, f + 9, 0.0)
        f += period


# ---- 眼球剖面 -------------------------------------------------------------------------------
EYE_R = 1.2


def _cap_into(bm, c, R, th0, th1, nt=40, nphi=24, axis_scale=(1, 1, 1)):
    """球面的一段（绕 +X 轴的极角 th0→th1），只建 y ≥ 0 的半边（剖切）：φ∈[0, π]，p = c + R(cosθ, sinθ sinφ, sinθ cosφ)。"""
    rows = []
    for i in range(nt + 1):
        th = th0 + (th1 - th0) * i / nt
        row = []
        for j in range(nphi + 1):
            ph = math.pi * j / nphi
            row.append(bm.verts.new((c[0] + R * math.cos(th) * axis_scale[0], c[1] + R * math.sin(th) * math.sin(ph) * axis_scale[1],
                                     c[2] + R * math.sin(th) * math.cos(ph) * axis_scale[2])))
        rows.append(row)
    for a, b in zip(rows[:-1], rows[1:]):
        for j in range(nphi):
            f = bm.faces.new((a[j], a[j + 1], b[j + 1], b[j]))
            f.smooth = True


def _cap(name, parent, mat, role, tag, R, th0, th1, thick, c=(0, 0, 0), axis_scale=(1, 1, 1)):
    import bmesh
    bm = bmesh.new()
    _cap_into(bm, c, R, th0, th1, axis_scale=axis_scale)
    ob = _mesh_object(name, bm, parent, mat, role, tag)
    if thick:
        s = ob.modifiers.new("Solid", "SOLIDIFY")
        s.thickness = thick
        s.offset = -1
    return ob


def eyeball_section(name, loc=(0, 0, 0), mat=None, retina_color=(0.55, 0.69, 1.0), tag=None):
    """半个眼球（y ≥ 0）：巩膜、脉络膜、视网膜、神经节细胞带、角膜、虹膜、睫状体、悬韧带、
    双凸晶状体、玻璃体（默认隐藏，clay 下会变实心块）、带鞘视神经、视盘、黄斑。
    返回 dict(...)。光轴沿 +X（角膜在 -X）。"""
    import bpy
    import bmesh
    import e2_shot as S
    tag = tag or (lambda o, r: o)
    root = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(root)
    root.location = loc
    R = EYE_R
    front = math.radians(148)
    sclera = _cap(f"{name}_Sclera", root, mat, "structure", tag, R, 0.0, front, 0.06)
    # 脉络膜：巩膜与视网膜之间的红棕带（emitter 保色，不被 clay 换掉）
    choroid = _cap(f"{name}_Choroid", root, S.glow(f"{name}_ChoroidMat", (0.32, 0.07, 0.04), 0.85),
                   "emitter", tag, R - 0.035, 0.0, math.radians(140), 0.028)
    retina = _cap(f"{name}_Retina", root, mat, "structure", tag, R - 0.07, 0.0, math.radians(118), 0.035)
    # RGC：离散光点贴在视网膜内壁，共用一个 glow mat（避免整块平涂蓝盘）
    rgc_mat = S.glow(f"{name}_RGCMat", retina_color, 0.0)
    rgc_spots = []
    rr = R - 0.105
    for i, th in enumerate([math.radians(a) for a in (18, 32, 48, 62, 78, 95, 40, 70)]):
        for j, ph in enumerate((0.35, 0.7, 1.05, 1.4, 1.75)):
            if (i + j) % 2 == 0 and j == 4:
                continue
            x = rr * math.cos(th)
            y = rr * math.sin(th) * math.sin(ph)
            z = rr * math.sin(th) * math.cos(ph)
            if y < 0.02:
                continue
            sp = S.sphere(f"{name}_RGC{i}_{j}", 0.045 + 0.01 * ((i + j) % 3), (x, y, z),
                          rgc_mat, "emitter", seg=16, rings=10)
            sp.parent = root
            rgc_spots.append(sp)
    rgc = rgc_spots[0] if rgc_spots else None  # 兼容旧字段：动画改 mat 强度即可
    cr = R * 0.66
    cc = (-R * math.cos(math.pi - front) + cr * math.cos(math.radians(40)) - 0.02, 0, 0)
    cornea = _cap(f"{name}_Cornea", root, mat, "shell", tag, cr, math.radians(140), math.pi, 0.04, c=cc)
    xi = -R * 0.80
    bm = bmesh.new()
    rin, rout, nseg = 0.22, R * 0.58, 28
    for j in range(nseg):
        a0, a1 = math.pi * j / nseg, math.pi * (j + 1) / nseg
        vs = [bm.verts.new((xi, r * math.sin(a), r * math.cos(a))) for r, a in ((rin, a0), (rout, a0), (rout, a1), (rin, a1))]
        bm.faces.new(vs)
    iris = _mesh_object(f"{name}_Iris", bm, root, mat, "structure", tag)
    s = iris.modifiers.new("Solid", "SOLIDIFY")
    s.thickness = 0.035
    # 睫状体：虹膜根部后方一圈稍厚的三角环（剖面里是两三个小鼓包）
    bm = bmesh.new()
    ciliary_x = xi + 0.06
    for j in range(nseg):
        a0, a1 = math.pi * j / nseg, math.pi * (j + 1) / nseg
        r_in, r_out = R * 0.52, R * 0.70
        # 三角截面：前尖后钝
        pts = [
            (ciliary_x - 0.04, r_in * math.sin(a0), r_in * math.cos(a0)),
            (ciliary_x + 0.08, r_out * math.sin(a0), r_out * math.cos(a0)),
            (ciliary_x + 0.02, r_in * math.sin(a0), r_in * math.cos(a0)),
            (ciliary_x - 0.04, r_in * math.sin(a1), r_in * math.cos(a1)),
            (ciliary_x + 0.08, r_out * math.sin(a1), r_out * math.cos(a1)),
            (ciliary_x + 0.02, r_in * math.sin(a1), r_in * math.cos(a1)),
        ]
        vs = [bm.verts.new(p) for p in pts]
        try:
            bm.faces.new((vs[0], vs[1], vs[4], vs[3]))
            bm.faces.new((vs[1], vs[2], vs[5], vs[4]))
            bm.faces.new((vs[0], vs[2], vs[5], vs[3]))
        except ValueError:
            pass
    ciliary = _mesh_object(f"{name}_Ciliary", bm, root,
                           S.glow(f"{name}_CiliaryMat", (0.55, 0.18, 0.10), 0.55), "emitter", tag)
    # 晶状体：更厚的双凸
    lens = _cap(f"{name}_Lens", root, mat, "structure", tag, 0.40, 0.0, math.pi, 0.0,
                c=(xi + 0.22, 0, 0), axis_scale=(0.70, 1.0, 1.0))
    # 悬韧带：睫状突 → 晶状体赤道的细丝（剖面可见 7–9 根）
    zonules = []
    lens_eq_x = xi + 0.22
    zon_mat = S.glow(f"{name}_ZonuleMat", (0.92, 0.88, 0.78), 0.35)
    for k in range(11):
        a = math.pi * (0.08 + 0.84 * k / 10)
        y, z = 0.36 * math.sin(a), 0.36 * math.cos(a)
        p0 = (ciliary_x + 0.03, y * 1.45, z * 1.45)
        p1 = (lens_eq_x + 0.02, y * 1.0, z * 1.0)
        mid = ((p0[0] + p1[0]) / 2 + 0.01, (p0[1] + p1[1]) / 2, (p0[2] + p1[2]) / 2)
        zobj = S.tube(f"{name}_Zonule{k}", [p0, mid, p1], 0.011, zon_mat, "emitter", res=1)
        zobj.parent = root
        zonules.append(zobj)
    # 玻璃体：默认隐藏（clay 会把它变成实心蓝/黑块）；调用方可再显示
    vit = _cap(f"{name}_Vitreous", root, mat, "shell", tag, R - 0.14, 0.0, math.radians(120), 0.0)
    vit.hide_render = vit.hide_viewport = True
    # 视神经：内芯 + 稍粗的鞘，从后极收窄伸出
    nerve_core = S.cylinder(f"{name}_OpticNerve", 0.12, 0.85, (R + 0.35, 0.0, -0.18), mat, "structure",
                            rot=(0, math.pi / 2, 0))
    nerve_core.parent = root
    nerve_sheath = S.cylinder(f"{name}_OpticSheath", 0.20, 0.55, (R + 0.18, 0.0, -0.18), mat, "structure",
                              rot=(0, math.pi / 2, 0))
    nerve_sheath.parent = root
    # 视盘 / 黄斑（emitter 保色）
    disc = S.sphere(f"{name}_OpticDisc", 0.11, (R - 0.09, 0.02, -0.18),
                    S.glow(f"{name}_OpticDiscMat", (1.0, 0.86, 0.55), 1.3), "emitter", seg=20, rings=12)
    disc.parent = root
    macula = S.sphere(f"{name}_Macula", 0.08, (R - 0.10, 0.02, 0.12),
                      S.glow(f"{name}_MaculaMat", (0.55, 0.28, 0.06), 0.9), "emitter", seg=20, rings=12)
    macula.parent = root
    return {"root": root, "sclera": sclera, "choroid": choroid, "retina": retina, "rgc_band": rgc,
            "rgc_spots": rgc_spots, "rgc_mat": rgc_mat, "cornea": cornea, "iris": iris,
            "ciliary": ciliary, "zonules": zonules, "lens": lens, "vitreous": vit,
            "nerve": nerve_core, "nerve_sheath": nerve_sheath, "optic_disc": disc,
            "macula": macula, "center": loc, "R": R}


def injection_path(eye, entry_deg=132, depth=0.55):
    """玻璃体内注射的针轨迹（局部坐标）：从睫状体平坦部附近（极角 entry_deg，靠前上方）斜向眼球中心进针 depth BU。
    返回 (针外端, 入口, 针尖)。"""
    R = eye["R"]
    th = math.radians(entry_deg)
    entry = (R * math.cos(th), 0.02, R * math.sin(th))
    d = (-entry[0], 0.0, -entry[2])
    n = math.hypot(d[0], d[2])
    d = (d[0] / n, 0.0, d[2] / n)
    tip = (entry[0] + d[0] * depth, 0.02, entry[2] + d[2] * depth)
    outer = (entry[0] - d[0] * 0.9, 0.02, entry[2] - d[2] * 0.9)
    return outer, entry, tip
