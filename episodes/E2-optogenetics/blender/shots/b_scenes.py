"""E2 第二幕（B 段）的分子 / 膜镜头：一个模块，多个 variant，只有一个 after_style（WORKFLOW 9）。

  patch        B_01a          sem / Cycles：嗜盐古菌的杆状细胞表面，几块颜色更深的膜斑（紫膜），慢推到最大一块。
  sheet        B_01b          clay：一张紫膜片（build_purple_membrane，只有 bR 三聚体一种蛋白）从下方升到镜头前。
  br_lattice   B_02a / B_02b  sem：紫膜三聚体晶格（缩小的 bR 单体，带视黄醛）从俯视慢推到一个单体；
                              energy：同一场景近景，视黄醛闪一下，骨架不动。
  br_pump      B_03a / B_03b  energy：单个 bR 剖面，三次闪光，每次视黄醛光晕紫 → 黄 → 紫，一个质子从胞内被送到胞外；
                              xray：同一场景收尾，胞外质子多、胞内少（pH 一高一低）。
  pump_channel B_04a          blueprint（分镜写 manim，见 registry 注释）：左右两张膜，左泵（逆梯度箭头）、右通道（孔开、顺梯度）。
  pair         B_04b / B_92   clay：两只蛋白各带一小片膜，分开托在镜头前。args.kinds 决定是哪两只（泵 + 通道 / ChR2 + NpHR）。
  chr1         B_06b          sem：ChR1 孔开着，只有质子（小球）在孔里，一个更大的阳离子停在孔口外。
  truncate     B_07a / B_07b  clay：先是「分开的感受器 + 分开的孔」两件，光 → 信号 → 孔开；两件移走。
                              全长 ChR（带胞内 C 端）升上来，光直接开孔；C 端被拿走，只剩跨膜核心，光仍开孔。
                              xray：收尾状态，截短的核心开着，离子在过。
  chr2         B_08a / B_09b  energy：膜上三个 ChR2，蓝光打开，阳离子流入；右上角两条示意曲线：膜电位上升、电流从峰落到平台。
                              B_09b 近景：光还在，孔口从大变小（脱敏）。
  nphr         B_16a          energy：NpHR，黄光，氯离子被泵进细胞；示意膜电位先有几次锋电位，光后往下走、锋电位消失。
  nphr_plan    B_16b          blueprint（分镜写 manim）：NpHR 剖面，波浪线表示黄光，箭头氯离子向内，右侧向下箭头表示电压下降。
  dual         B_17b / B_91   energy：同一膜上 ChR2（蓝）和 NpHR（琥珀），先蓝光只开左边，再黄光只开右边；xray：同一场景。
  spectrum     B_18a          sem：两个通道并排，左蓝敏、右长波长（ChrimsonR），只做缓慢推近，不假装构象电影。

几何依据（全部示意，核查表 audit_B.yaml 在 P6 补，状态预计 simplified）：
  - 七次跨膜、视黄醛、ChR 的孔在 TM1/2/3/7 之间、泵没有贯通孔：见 build_opsin.py 文件头（Henderson & Unwin 1975；
    Kato et al. 2012）。
  - 紫膜：嗜盐古菌（Halobacterium salinarum）是杆状细胞，紫膜是细胞膜上的斑块，里面只有 bR 一种蛋白，三聚体排成六方晶格
    （Oesterhelt & Stoeckenius 1971；Krebs & Isenbarger 2000，见 build_purple_membrane.py）。斑块的大小、形状、个数是示意。
    br_lattice 的单体按 0.72 倍缩小，三聚体中心距仍取 62 Å，避免螺旋穿插（比例 simplified）。
  - bR 是光驱动质子泵，质子从胞内送到胞外（Oesterhelt & Stoeckenius 1973，F4b）；吸收从紫色态跳到黄色中间态再回来
    （光循环的 M 中间态，P6 补出处；只画颜色变化，不标波长）。闪光颜色取黄绿，示意。
  - ChR1 主要通过质子（Nagel et al. 2002，F5）；ChR2 通过阳离子、不限于质子，持续光照下电流从峰值落到较低平台
    （Nagel et al. 2003，F5；分镜 B_09a）。曲线没有刻度和时间常数。
  - 截短：只保留形成通道的跨膜部分，光仍能打开电导（诺奖科学背景，F5）。真实的截短是去掉胞内 C 端，
    这里用 build_opsin 的 cterm 表示；truncate 开头的「分开的感受器 + 分开的孔」是旁白里被否定的旧设想，画成抽象零件，
    不对应任何具体系统。
  - NpHR 是黄光驱动的氯离子泵，氯离子进入细胞，膜电位往负方向走（Zhang et al. 2007，F8）。
  - ChrimsonR：长波长敏感的通道视紫红质变体（Klapoetke et al. 2014，光谱见 F17），2021 年用于人眼（Sahel et al. 2021，F11）。
    sem 下用冷 / 暖两种灰调区分左右，两个蛋白是两个物体。
  - 离子大小放大很多倍，见 build_bilayer.py。

需要 mograph 后处理叠中文字的镜头（registry 里 raw: true；锚点是场景里的空物体，后处理按相机投影取位置）：
  B_02a  「膜片段里只有这一种蛋白」          锚点 LabelAnchor_onlyone（主角单体上方），后半段出现
  B_03a  「细菌视紫红质 · 质子泵」          锚点 LabelAnchor_bR（蛋白上方），第一次闪光后出现
  B_04a  「泵」「通道」                       锚点 LabelAnchor_pump / LabelAnchor_channel（各自膜片上方）
  B_16b  「黄光」「氯离子向内」「电压下降」   锚点 LabelAnchor_light / LabelAnchor_cl / LabelAnchor_v
  B_18a  「2021 用于人眼」（ChrimsonR 这个词已经是 Blender 文字）  锚点 LabelAnchor_human（ChrimsonR 下方）
颜色约定见 e2_common：蓝 = 打开（ChR），琥珀 = 关掉（NpHR），膜青 = H⁺。没有人物。
"""
import math
import random

import bpy
from mathutils import Vector, noise

import build_bilayer as BB
import build_opsin as BO
import build_purple_membrane as BP
import common as C
import e2_common as E
import e2_shot as S
import materials as M
import styles

FPS = 24
U = BB.UNIT                       # 1 Å = 0.01 BU

BLUE = S.lin(E.CHANNEL)
AMBER = S.lin(E.AMBER)
CYAN = S.lin(E.MEMBRANE)
WHITE = S.lin(E.LINE)
PURPLE = (0.42, 0.10, 0.62)       # bR 紫色态（示意）
YELLOW = (0.95, 0.78, 0.18)       # 黄色中间态（示意）
FLASH = (0.70, 1.00, 0.30)        # 黄绿闪光（示意）
RED = (1.00, 0.28, 0.20)          # 长波长光（ChrimsonR，示意）


# ---- 小工具 ---------------------------------------------------------------------------------
def _frames(*sids):
    return max(S.shot_frames(s) for s in sids)


def _anchor(name, loc):
    ob = S.link(bpy.data.objects.new(name, None))
    ob.location = loc
    return ob


def _membrane(name, holes=(), half_w=200.0, half_d=60.0, loc=(0, 0, 0), rows=3, seed=3, parent=None, front=-10.0):
    """build_bilayer 外包一层：全部部件挂到一个空物体上（可整体移动），给 xray / clay 用的哑光材质。
    剖面镜头：膜整体往后挪，剖切面落在 y = front（Å），蛋白前半截露在剖面前面，不被膜挡住。"""
    off = half_d + front if front is not None else 0.0
    holes = [(hx, hy - off, hr) for hx, hy, hr in holes]
    parts = BB.build_bilayer(name, half_w=half_w, half_d=half_d, holes=holes, section_rows=rows, seed=seed)
    root = S.link(bpy.data.objects.new(name + "Root", None))
    root.location = (loc[0], loc[1] + off * U, loc[2])
    if parent is not None:
        root.parent = parent
    heads = S.matte(name + "HeadMat", (0.78, 0.80, 0.84), 0.5)
    tails = S.matte(name + "TailMat", (0.62, 0.58, 0.46), 0.7)
    core = S.matte(name + "CoreMat", (0.42, 0.40, 0.34), 0.8)
    for key, m in (("heads", heads), ("tails", tails), ("core", core)):
        ob = parts[key]
        ob.parent = root
        ob.data.materials.append(m)
        styles.tag(ob, "structure")
    for i in range(len(holes)):
        cut = bpy.data.objects.get(f"{name}Hole{i}")
        if cut is not None:
            cut.parent = root
            styles.tag(cut, "rig")
    parts["root"] = root
    return parts


def _protein(name, kind, loc, color, seed=1, cterm=False, scale=1.0, pore_color=None, parent=None):
    """build_opsin + 哑光材质（xray / clay 下可读颜色）。返回 build_opsin 的 dict。"""
    mat = S.matte(name + "Mat", color, 0.5)
    rmat = S.matte(name + "RetMat", (0.95, 0.62, 0.20), 0.4)
    p = BO.build_opsin(name, kind=kind, loc=loc, mat=mat, retinal_mat=rmat, pore_color=pore_color or BLUE,
                       cterm=cterm, seed=seed, tag=styles.tag)
    if scale != 1.0:
        p["root"].scale = (scale, scale, scale)
    if parent is not None:
        p["root"].parent = parent
    for o in p["root"].children_recursive:
        if o.type in ("MESH", "CURVE") and o.get("role") == "structure":
            o["protein"] = 1                               # energy 下用更亮的轮廓（after_style）
    return p


def _hole(x_bu=0.0, y_bu=0.0, r=24.0):
    """膜上给蛋白挖的洞（build_bilayer 的 holes 单位是 Å）。"""
    return (x_bu / U, y_bu / U, r)


def _wander(ob, base, f0, f1, amp, rnd, step=6):
    if f1 < f0:
        return
    for f in range(f0, f1 + 1, step):
        ob.location = tuple(base[k] + rnd.uniform(-amp, amp) * (0.6 if k == 2 else 1.0) for k in range(3))
        ob.keyframe_insert("location", frame=f)


def _ion_story(ob, path, f_go, travel, f_end, rnd, amp=0.012, spread=(0.14, 0.08, 0.10)):
    """离子先在 path[0] 附近热运动，f_go 起沿 path 走 travel 帧，出口后散开到随机位置继续热运动到 f_end。"""
    end = tuple(path[-1][k] + rnd.uniform(-spread[k], spread[k]) for k in range(3))
    full = list(path) + [end]
    _wander(ob, full[0], 1, f_go - 2, amp, rnd)
    BB.through(ob, full, f_go, f_go + travel)
    _wander(ob, end, f_go + travel + 4, f_end, amp, rnd)


def _idle_ions(prefix, kind, n, center, half, f_end, rnd, role="emitter", amp=0.012):
    obs = []
    for i in range(n):
        p = tuple(center[k] + rnd.uniform(-half[k], half[k]) for k in range(3))
        ob = BB.ion(f"{prefix}{i}", kind, p, role)
        _wander(ob, p, 1, f_end, amp, rnd)
        obs.append(ob)
    return obs


def _beam(name, x, color, keys, y=0.0, top=1.6, r_end=0.26, z_target=0.18):
    """从上方斜照下来的一束光；keys = [(frame, gain)]。"""
    ob, m = S.cone_beam(name, (x - 0.25, y - 0.35, top), (x, y, z_target), r_end, color, 0.0)
    for f, g in keys:
        S.set_gain(m, f, g * 0.25)                         # 光束只是示意：实际 gain 约 0.5–0.6（新版 cone_beam）
    return ob, m


def _pulse(mat, f, peak, rise=3, hold=0, fall=10, base=0.0, setter=S.set_gain):
    setter(mat, f - 1, base)
    setter(mat, f + rise, peak)
    if hold:
        setter(mat, f + rise + hold, peak)
    setter(mat, f + rise + hold + fall, base)


def _ret_color(p, f, color):
    S.set_emit_color(p["retinal_glow_mat"], f, color)


def _sem_tone(ob, tone):
    """sem 下单独的灰调（after_style 里按 tone 生成材质副本）。tone = (r, g, b) 乘到电镜灰度上。"""
    ob["sem_tone"] = list(tone)


def _tone_tree(p, tone):
    for o in [p["root"]] + list(p["root"].children_recursive):
        if o.type in ("MESH", "CURVE") and o.get("role") == "structure":
            _sem_tone(o, tone)


# ---- patch：B_01a -----------------------------------------------------------------------------
# 本 variant 单位 1 BU = 1 µm（细胞尺度）。杆状细胞长 3 µm、半径 0.35 µm（示意）。
ROD_L, ROD_R = 3.0, 0.35


def _rod_point(x, th, lift=0.0):
    h = ROD_L / 2 - ROD_R
    ax = abs(x)
    r = ROD_R if ax <= h else math.sqrt(max(0.0, ROD_R ** 2 - (ax - h) ** 2))
    r += lift
    n = noise.noise(Vector((x * 3.0, math.cos(th) * 2.0, math.sin(th) * 2.0))) * 0.012
    return Vector((x, (r + n) * math.cos(th), (r + n) * math.sin(th)))


def _rod_mesh(name, nx=150, nt=72):
    import bmesh
    bm = bmesh.new()
    rows = []
    for i in range(nx + 1):
        x = -ROD_L / 2 + ROD_L * i / nx
        rows.append([bm.verts.new(_rod_point(x, 2 * math.pi * j / nt)) for j in range(nt)])
    for a, b in zip(rows[:-1], rows[1:]):
        for j in range(nt):
            f = bm.faces.new((a[j], a[(j + 1) % nt], b[(j + 1) % nt], b[j]))
            f.smooth = True
    for row, sgn in ((rows[0], -1), (rows[-1], 1)):
        c = bm.verts.new((sgn * ROD_L / 2, 0, 0))
        for j in range(nt):
            f = bm.faces.new((row[j], row[(j + 1) % nt], c) if sgn < 0 else (row[(j + 1) % nt], row[j], c))
            f.smooth = True
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    return S.link(bpy.data.objects.new(name, me))


def _patch_mesh(name, x0, th0, size, seed):
    """细胞表面上一块不规则的膜斑：在 (x, 弧长) 参数域里取一个起伏边界的区域，抬高 6 nm，表面细颗粒（晶格本身太小，看不见）。"""
    import bmesh
    rnd = random.Random(seed)
    ph = [rnd.uniform(0, 2 * math.pi) for _ in range(3)]

    def rho(phi):
        return size * (1 + 0.18 * math.sin(3 * phi + ph[0]) + 0.10 * math.sin(5 * phi + ph[1]) + 0.06 * math.sin(2 * phi + ph[2]))

    bm = bmesh.new()
    step = 0.012
    n = int(size * 1.5 / step)
    grid = {}
    for i in range(-n, n + 1):
        for j in range(-n, n + 1):
            dx, ds = i * step, j * step
            if math.hypot(dx, ds) <= rho(math.atan2(ds, dx)):
                th = th0 + ds / ROD_R
                p = _rod_point(x0 + dx, th, 0.006 + 0.002 * noise.noise(Vector((dx * 60, ds * 60, seed))))
                grid[(i, j)] = bm.verts.new(p)
    for (i, j), v in grid.items():
        q = [(i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)]
        if all(k in grid for k in q):
            f = bm.faces.new([grid[k] for k in q])
            f.smooth = True
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = S.link(bpy.data.objects.new(name, me))
    sol = ob.modifiers.new("Thick", "SOLIDIFY")
    sol.thickness = 0.006
    return ob


def patch(sc, rnd):
    F = _frames("B_01a")
    rod = _rod_mesh("HaloRod")
    rod.rotation_euler = (0, 0, math.radians(8))
    styles.tag(rod, "structure")
    patches = []
    for k, (x0, th0, size) in enumerate(((0.35, -math.pi / 2 + 0.25, 0.30), (-0.85, -math.pi / 2 - 0.35, 0.16),
                                         (1.05, -math.pi / 2 + 0.9, 0.12), (-0.2, math.pi / 2, 0.22))):
        pm = _patch_mesh(f"PurplePatch{k}", x0, th0, size, seed=17 + k)
        pm.parent = rod
        styles.tag(pm, "structure")
        _sem_tone(pm, (0.55, 0.48, 0.62))                  # 更深、略偏紫的一块（sem 灰度上的「深色补丁」）
        patches.append(pm)
    # 第二个细胞在后面虚出一截，给尺度感；底下一块基底
    rod2 = _rod_mesh("HaloRod2")
    rod2.location = (-0.9, 1.6, -0.25)
    rod2.rotation_euler = (0, 0.15, math.radians(-30))
    styles.tag(rod2, "structure")
    _sem_tone(rod2, (0.7, 0.7, 0.72))
    base = S.box("Substrate", (0, 0, -ROD_R - 0.03), (12, 12, 0.04))
    _sem_tone(base, (0.35, 0.35, 0.36))
    tgt = Vector(_rod_point(0.35, -math.pi / 2 + 0.25))
    tgt.rotate(rod.rotation_euler)
    S.camera("CamB_01a", [(1, (0.15, 0.0, 0.0), (0.4, -4.2, 1.6), 50, 5.6),
                          (F, tuple(tgt), tuple(tgt + Vector((0.12, -1.5, 0.55))), 50, 5.6)])


# ---- sheet：B_01b -----------------------------------------------------------------------------
def sheet(sc, rnd):
    F = _frames("B_01b")
    lip, hel = BP.build_membrane(half_w=95.0, half_h=70.0)
    # build_membrane 的脂质板比晶格大很多；这里换成刚好托住螺旋的一片（一张「膜片」）
    xs = [v.co.x for v in hel.data.vertices]
    ys = [v.co.y for v in hel.data.vertices]
    bpy.data.objects.remove(lip)
    pad = 0.12
    w, d = max(xs) - min(xs) + pad, max(ys) - min(ys) + pad
    slab = S.box("SheetLipid", ((max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2, -BP.LIPID_T * U / 2),
                 (w, d, BP.LIPID_T * U), bevel=0.015)
    root = S.link(bpy.data.objects.new("SheetRoot", None))
    for o in (slab, hel):
        o.parent = root
        styles.tag(o, "structure")
    # 膜片从下方升起、转到正对镜头（倾 62°），停住
    S.key(root, 1, location=(0.0, 0.3, -2.4), rotation_euler=(math.radians(20), 0, math.radians(-14)))
    S.key(root, max(2, F - 8), location=(0.0, 0.0, 0.0), rotation_euler=(math.radians(62), 0, math.radians(-4)))
    S.key(root, F + 24, location=(0.0, -0.03, 0.02), rotation_euler=(math.radians(63), 0, math.radians(-3)))
    S.studio_lights(0.6)
    S.locked("CamB_01b", (0, 0, 0), (0.0, -4.6, 0.5), lens=35, fstop=8.0)


# ---- br_lattice：B_02a / B_02b ----------------------------------------------------------------
LAT_SCALE = 0.72
TRI_R = 17.0                       # 单体中心到三重轴，Å（缩小后的单体）


def _lipid_plane(name, half_w, half_d, holes, z_top, step=2.0, thick=0.3):
    """平的脂质面（顶面 z_top，Å 网格），holes=[(x, y, r)] Å 处挖空，向下加厚 thick BU。紫膜里脂质只占少数面积，
    头基小球在这个尺度上会盖住三聚体图案，所以这里照 A0_91 用一块面（simplified）。"""
    import bmesh
    bm = bmesh.new()
    nx, ny = int(2 * half_w / step), int(2 * half_d / step)
    vs = {}

    def v(i, j):
        if (i, j) not in vs:
            vs[(i, j)] = bm.verts.new(((-half_w + i * step) * U, (-half_d + j * step) * U, z_top))
        return vs[(i, j)]

    for i in range(nx):
        for j in range(ny):
            cx, cy = -half_w + (i + 0.5) * step, -half_d + (j + 0.5) * step
            if any(math.hypot(cx - hx, cy - hy) < hr for hx, hy, hr in holes):
                continue
            bm.faces.new((v(i, j), v(i + 1, j), v(i + 1, j + 1), v(i, j + 1)))
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = S.link(bpy.data.objects.new(name, me))
    sol = ob.modifiers.new("Thick", "SOLIDIFY")
    sol.thickness = thick
    sol.offset = -1.0
    styles.tag(ob, "structure")
    return ob


def br_lattice(sc, rnd):
    F = _frames("B_02a", "B_02b")
    centers = [p for p in BP.lattice_points(90.0, 70.0) if abs(p[0]) <= 110 and abs(p[1]) <= 90]
    holes, mons = [], []
    for cx, cy in centers:
        for k in range(3):
            th = math.radians(90 + 120 * k)
            mx, my = cx + TRI_R * math.cos(th), cy + TRI_R * math.sin(th)
            holes.append((mx, my, 11.5))                   # 孔边藏在螺旋圈下面
            mons.append((mx, my, th))
    lip = _lipid_plane("PMLipid", 150.0, 125.0, holes, 0.15, step=1.0, thick=0.04)
    floor = _lipid_plane("PMFloor", 150.0, 125.0, (), -0.10, step=25.0, thick=0.02)   # 孔里看下去是暗底，不是空洞
    _sem_tone(floor, (0.18, 0.17, 0.2))
    _sem_tone(lip, (0.35, 0.33, 0.40))                     # 脂质面比蛋白暗（照 A0_91）
    hero = None
    for i, (mx, my, th) in enumerate(mons):
        p = _protein(f"bR{i}", "pump", (mx * U, my * U, 0.0), (0.55, 0.42, 0.68), seed=1, scale=LAT_SCALE,
                     pore_color=PURPLE)
        p["root"].rotation_euler = (0, 0, th + math.pi / 2)
        S.set_gain(p["retinal_glow_mat"], 1, 0.0)
        if hero is None or math.hypot(mx, my) < math.hypot(*hero[1]):
            hero = (p, (mx, my))
    p, (hx, hy) = hero
    # 主角的视黄醛在电镜灰度里提亮一点，镜头推近时读得出来
    for r_ in p["retinal"]:
        _sem_tone(r_, (1.5, 1.4, 1.2))
    hc = Vector((hx * U, hy * U, 0.0))
    _anchor("LabelAnchor_onlyone", tuple(hc + Vector((0.0, 0.0, 0.42))))
    # B_02a：从 A0_91 那样的斜俯视慢推到主角单体正上方偏前
    S.camera("CamB_02a", [(1, (0.0, 0.0, 0.0), (0.0, -1.7, 2.6), 50, 8.0),
                          (_frames("B_02a"), tuple(hc), tuple(hc + Vector((0.0, -0.40, 0.95))), 50, 8.0)])
    # B_02b：同一单体侧上方近景，视黄醛闪一下（energy 下只有光晕在亮，骨架是暗边）
    S.set_emit_color(p["retinal_glow_mat"], 1, YELLOW)
    _pulse(p["retinal_glow_mat"], 12, 3.2, rise=2, hold=2, fall=12)
    S.locked("CamB_02b", tuple(hc), tuple(hc + Vector((0.18, -0.55, 0.42))), lens=35)


# ---- br_pump：B_03a / B_03b -------------------------------------------------------------------
def br_pump(sc, rnd):
    F3 = S.shot_frames("B_03a")
    F = F3 + 8
    _membrane("BM", holes=[_hole()], half_w=190.0, half_d=26.0)
    p = _protein("bR", "pump", (0, 0, 0), (0.55, 0.40, 0.70), seed=1, pore_color=PURPLE)
    gm = p["retinal_glow_mat"]
    _ret_color(p, 1, PURPLE)
    S.set_gain(gm, 1, 1.2)                                    # 紫色态一直微亮：吸收状态读得出来
    beam, bm = _beam("Flash", 0.0, FLASH, [(1, 0.0)])
    cycles = [round(F3 * u) for u in (0.30, 0.55, 0.78)]
    out_n, in_n = 18, 10
    _idle_ions("HOut", "h", out_n, (0.0, 0.0, 0.42), (1.6, 0.35, 0.14), F, rnd)      # 胞外（+z）质子多
    _idle_ions("HIn", "h", in_n, (0.0, 0.0, -0.42), (1.6, 0.35, 0.14), F, rnd)       # 胞内少
    for k, fc in enumerate(cycles):
        _pulse(bm, fc, 2.4, rise=2, hold=3, fall=8)          # 闪光
        S.set_emit_color(gm, fc, PURPLE)
        S.set_emit_color(gm, fc + 4, YELLOW)                 # 吸收峰移动：紫 → 黄
        S.set_gain(gm, fc, 1.2)
        S.set_gain(gm, fc + 4, 2.6)
        S.set_emit_color(gm, fc + 34, YELLOW)
        S.set_emit_color(gm, fc + 44, PURPLE)                # 回到紫色态
        S.set_gain(gm, fc + 34, 2.6)
        S.set_gain(gm, fc + 44, 1.2)
        h = BB.ion(f"HPumped{k}", "h", (0, 0, -0.45))
        path = BO.pump_path(p, z_from=-0.45, z_to=0.45)
        _ion_story(h, path, fc + 3, 36, F, rnd)
    _anchor("LabelAnchor_bR", (0.0, 0.0, 0.36))           # 0.62 在低机位下投影出画
    S.studio_lights(0.5)
    S.dolly("CamB_03a", (0.0, 0.0, 0.05), (0.35, -3.0, 0.55), (0.15, -2.15, 0.32), 1, F3)
    S.locked("CamB_03b", (0.0, 0.0, 0.0), (0.9, -2.6, 0.25), f=1, lens=35)


# ---- pump_channel：B_04a ----------------------------------------------------------------------
def pump_channel(sc, rnd):
    F = _frames("B_04a")
    XL, XR = -0.78, 0.78
    for nm, x in (("ML", XL), ("MR", XR)):
        _membrane(nm, holes=[_hole()], half_w=58.0, half_d=32.0, loc=(x, 0, 0), rows=2)
    pump = _protein("Pump", "pump", (XL, 0, 0), (0.5, 0.5, 0.5), seed=1)
    chan = _protein("Chan", "channel", (XR, 0, 0), (0.5, 0.5, 0.5), seed=1)
    # 两边同一个梯度：胞外（上）离子多，胞内（下）少。蓝图只显示 structure，所以离子标成 structure。
    for nm, x in (("L", XL), ("R", XR)):
        _idle_ions(f"Hi{nm}", "cation", 12, (x, 0, 0.40), (0.42, 0.15, 0.10), F, rnd, role="structure")
        _idle_ions(f"Lo{nm}", "cation", 3, (x, 0, -0.40), (0.42, 0.15, 0.08), F, rnd, role="structure")
    # 左：泵把离子从少的一侧推到多的一侧（逆梯度）
    f_pump = round(F * 0.22)
    sh, hd = S.arrow("PumpArrow", (XL - 0.36, -0.05, -0.36), (XL - 0.36, -0.05, 0.36), 0.012)
    for o in (sh, hd):
        S.show_between(o, f_pump)
    for k in range(3):
        ion = BB.ion(f"Pumped{k}", "cation", (XL, 0, -0.45), "structure")
        _ion_story(ion, BO.pump_path(pump, z_from=-0.45, z_to=0.42), f_pump + 6 + 40 * k, 30, F, rnd)
    # 右：孔打开，离子顺梯度流下去
    f_open = round(F * 0.55)
    BO.set_open(chan, 1, 0.0)
    BO.set_open(chan, f_open - 1, 0.0)
    BO.set_open(chan, f_open + 10, 1.0)
    sh, hd = S.arrow("ChanArrow", (XR + 0.36, -0.05, 0.36), (XR + 0.36, -0.05, -0.36), 0.012)
    for o in (sh, hd):
        S.show_between(o, f_open + 8)
    for k in range(6):
        ion = BB.ion(f"Flow{k}", "cation", (XR, 0, 0.45), "structure")
        _ion_story(ion, BO.pore_path(chan, z_from=0.45, z_to=-0.42), f_open + 10 + 14 * k, 22, F, rnd)
    _anchor("LabelAnchor_pump", (XL, 0, 0.66))
    _anchor("LabelAnchor_channel", (XR, 0, 0.66))
    S.dolly("CamB_04a", (0.0, 0.0, 0.0), (0.0, -4.9, 0.5), (0.0, -4.3, 0.42), 1, F)


# ---- pair：B_04b / B_92 -----------------------------------------------------------------------
def pair(sc, rnd, kinds=("pump", "channel")):
    F = _frames("B_04b", "B_92")
    cols = {"pump": (0.6, 0.45, 0.7), "channel": (0.45, 0.58, 0.85), "cl_pump": (0.85, 0.66, 0.35)}
    for i, (kind, x) in enumerate(zip(kinds, (-0.62, 0.62))):
        root = S.link(bpy.data.objects.new(f"Pair{i}", None))
        _membrane(f"PD{i}", holes=[_hole()], half_w=40.0, half_d=40.0, rows=2, parent=root)
        p = _protein(f"P{i}{kind}", kind, (0, 0, 0), cols[kind], seed=1 + i, parent=root)
        S.set_gain(p["retinal_glow_mat"], 1, 0.0)
        # 两只托在镜头前，缓慢转、略微分开
        S.key(root, 1, location=(x * 0.92, 0, 0), rotation_euler=(math.radians(14), 0, math.radians(-20 if i else 20)))
        S.key(root, F, location=(x, 0, 0.02), rotation_euler=(math.radians(14), 0, math.radians(-8 if i else 8)))
        S.linear(root)
    S.studio_lights(0.5)
    S.locked("CamB_04b", (0, 0, 0), (0.0, -3.2, 0.7), lens=35)
    S.locked("CamB_92", (0, 0, 0), (0.0, -4.3, 0.8), lens=50)


# ---- chr1：B_06b ------------------------------------------------------------------------------
def chr1(sc, rnd):
    F = _frames("B_06b")
    _membrane("C1M", holes=[_hole()], half_w=160.0, half_d=45.0)
    p = _protein("ChR1", "channel", (0, 0, 0), (0.55, 0.6, 0.7), seed=2)
    BO.set_open(p, 1, 1.0)                                  # 光已经开着：孔打开（分镜：光只打开质子通路）
    path = BO.pore_path(p, z_from=0.40, z_to=-0.40)
    for k in range(4):                                      # 质子在孔里接连通过（sem 只显示 structure，所以离子标 structure）
        h = BB.ion(f"H{k}", "h", path[0], "structure")
        BB.through(h, path, 1 - 8 * k + 6, 1 - 8 * k + 30)
    na = BB.ion("NaOut", "cation", tuple(Vector(path[0]) + Vector((0.09, -0.03, 0.06))), "structure")
    _wander(na, tuple(na.location), 1, F, 0.006, rnd)       # 更大的阳离子停在孔口外
    _sem_tone(na, (1.3, 1.3, 1.3))
    S.locked("CamB_06b", (0.0, 0.0, 0.05), (0.25, -1.55, 0.45), lens=35)


# ---- truncate：B_07a / B_07b -----------------------------------------------------------------
def _receptor_part(name, loc, mat):
    """旧设想里「分开的感受器」：抽象零件（圆台 + 一个朝上的收光碟），不对应具体蛋白。"""
    root = S.link(bpy.data.objects.new(name, None))
    root.location = loc
    body = S.cylinder(name + "Body", 0.13, 0.46, (0, 0, 0), mat, verts=40)
    dish = S.cylinder(name + "Dish", 0.17, 0.03, (0, 0, 0.26), mat, verts=40)
    for o in (body, dish):
        o.parent = root
    return root


def truncate(sc, rnd):
    F7 = S.shot_frames("B_07a")
    F = F7 + S.shot_frames("B_07b") + 8
    t = lambda u: max(2, round(F7 * u))                    # noqa: E731
    mat = S.matte("PartMat", (0.62, 0.62, 0.66))
    # 1) 旧设想：分开的感受器 + 分开的孔，中间要一串信号去「通知」
    rec_root = S.link(bpy.data.objects.new("OldRec", None))
    _membrane("RecM", holes=[_hole(r=20)], half_w=36.0, half_d=36.0, rows=2, parent=rec_root)
    _receptor_part("Receptor", (0, 0, 0), mat).parent = rec_root
    pore_root = S.link(bpy.data.objects.new("OldPore", None))
    _membrane("PoreM", holes=[_hole(r=24)], half_w=36.0, half_d=36.0, rows=2, parent=pore_root)
    old = BO.build_pore_channel("OldChan", mat=mat, tag=styles.tag)
    old["root"].parent = pore_root
    for root, x in ((rec_root, -0.62), (pore_root, 0.62)):
        S.key(root, 1, location=(x, 0, 0))
        S.key(root, t(0.30), location=(x, 0, 0))
        S.key(root, t(0.40), location=(x * 3.2, 0.6, -0.6))
        S.show_between(root, 1, t(0.40))
        for o in root.children_recursive:
            if o.type in ("MESH", "CURVE"):
                S.show_between(o, 1, t(0.40))
    _beam("OldLight", -0.62, BLUE, [(t(0.10), 0.0), (t(0.12), 2.0), (t(0.20), 2.0), (t(0.22), 0.0)])
    sig_mat = S.glow("SignalMat", BLUE, 6.0)
    for k in range(6):                                      # 信号接力：一串小点从感受器跑到孔
        d = S.sphere(f"Signal{k}", 0.025, (-0.45, -0.05, 0.05), sig_mat, "emitter", seg=12, rings=8)
        f0 = t(0.13) + 3 * k
        S.key(d, f0, location=(-0.45, -0.05, 0.05))
        S.key(d, f0 + 26, location=(0.42, -0.05, 0.05))
        S.show_between(d, f0, f0 + 27)
    S.set_strength(old["pore_mat"], t(0.20), 0.0)
    S.set_strength(old["pore_mat"], t(0.24), 5.0)
    S.set_strength(old["pore_mat"], t(0.30), 0.0)
    # 2) 全长 ChR（跨膜核心 + 胞内 C 端）升上来，光直接开孔
    ch_root = S.link(bpy.data.objects.new("ChRRoot", None))
    _membrane("ChM", holes=[_hole()], half_w=70.0, half_d=55.0, rows=3, parent=ch_root)
    p = _protein("ChRFull", "channel", (0, 0, 0), (0.62, 0.62, 0.66), seed=1, cterm=True, parent=ch_root)
    S.key(ch_root, 1, location=(0, 0.4, -1.6))
    S.key(ch_root, t(0.34), location=(0, 0.4, -1.6))
    S.key(ch_root, t(0.44), location=(0, 0, 0))
    ct_parts = {p["cterm"]} | set(p["cterm"].children_recursive)
    for o in ch_root.children_recursive:
        if o.type in ("MESH", "CURVE") and o not in ct_parts:
            S.show_between(o, t(0.34))
    _beam("Light1", 0.0, BLUE, [(t(0.48), 0.0), (t(0.50), 2.2), (t(0.60), 2.2), (t(0.62), 0.0),
                                (t(0.80), 0.0), (t(0.82), 2.2), (F, 2.2)])
    BO.set_open(p, 1, 0.0, glow=0.0)
    BO.set_open(p, t(0.49), 0.0, glow=0.0)
    BO.set_open(p, t(0.52), 1.0, glow=1.3)
    BO.set_open(p, t(0.60), 1.0, glow=1.3)
    BO.set_open(p, t(0.63), 0.0, glow=0.0)
    # 3) C 端被拿走：只留形成通道的跨膜部分
    ct = p["cterm"]
    S.key(ct, t(0.64), location=tuple(ct.location))
    S.key(ct, t(0.76), location=tuple(Vector(ct.location) + Vector((0.9, -0.2, -0.7))))
    for o in ct_parts:
        if o.type in ("MESH", "CURVE"):
            S.show_between(o, t(0.34), t(0.76))
    BO.set_open(p, t(0.81), 0.0, glow=0.0)
    BO.set_open(p, t(0.84), 1.0, glow=1.3)
    BO.set_open(p, F, 1.0, glow=1.3)
    # 两次开孔都有阳离子流过（电导）
    for k in range(10):
        ion = BB.ion(f"Cat{k}", "cation", (0, 0, 0.45))
        phase = (t(0.52), t(0.60)) if k < 4 else (t(0.84), F - 20)
        f_go = phase[0] + (k % 6) * max(4, (phase[1] - phase[0]) // 6)
        _ion_story(ion, BO.pore_path(p, z_from=0.45, z_to=-0.45), f_go, 20, F, rnd)
        S.show_between(ion, t(0.40))
    S.studio_lights(0.5)
    S.dolly("CamB_07a", (0.0, 0.0, -0.05), (0.0, -3.6, 0.8), (0.0, -2.6, 0.45), 1, F7)
    S.locked("CamB_07b", (0.0, 0.0, 0.0), (0.55, -1.9, 0.3), lens=35)


# ---- chr2：B_08a / B_09b ----------------------------------------------------------------------
def chr2_times():
    F8 = S.shot_frames("B_08a")
    return F8, round(F8 * 0.58)                            # 「蓝光直接打开它」约在旁白 58% 处


def chr2(sc, rnd):
    F8, f_on = chr2_times()
    F = F8 + 8
    xs = (-0.55, 0.0, 0.55)
    _membrane("C2M", holes=[_hole(x) for x in xs], half_w=200.0, half_d=26.0)
    chans = [_protein(f"ChR2_{i}", "channel", (x, 0, 0), (0.5, 0.6, 0.85), seed=1 + i) for i, x in enumerate(xs)]
    _beam("Blue", 0.0, BLUE, [(1, 0.0), (f_on, 0.0), (f_on + 4, 2.4), (F, 2.4)], r_end=0.55, top=3.2, z_target=0.5)
    for c in chans:
        BO.set_open(c, 1, 0.0, glow=0.0)
        BO.set_open(c, f_on, 0.0, glow=0.0)
        BO.set_open(c, f_on + 6, 1.0, glow=1.3)            # 峰
        BO.set_open(c, f_on + 44, 0.5, glow=0.5)           # 持续光照：落到平台（脱敏，示意）
        BO.set_open(c, F, 0.5, glow=0.5)
    _idle_ions("Out", "cation", 22, (-0.35, 0.0, 0.36), (0.95, 0.25, 0.08), F, rnd)   # 让开右上角的曲线
    # 进入的离子：峰值时密，平台时疏
    k = 0
    for i, c in enumerate(chans):
        f = f_on + 6 + i * 2
        while f < F - 24:
            ion = BB.ion(f"In{k}", "cation", (c["center"].x, 0, 0.45))
            _ion_story(ion, BO.pore_path(c, z_from=0.45, z_to=-0.42), f, 18, F, rnd)
            k += 1
            f += 7 if f < f_on + 44 else 18
    # 右上角两条示意曲线（无刻度）：上 = 膜电位（光后上升、去极化），下 = 电流（峰 → 平台）
    u_on = (f_on - 1) / F8
    vm = M.emission("VmTrace", WHITE, 4.0)
    im = M.emission("ITrace", BLUE, 5.0)
    ax = S.matte("TraceAxis", (0.5, 0.5, 0.5))
    S.trace("Vm", lambda u: -0.6 + 1.1 * S.smooth((u - u_on) / 0.10) if u > u_on else -0.6,
            (0.42, -0.35, 0.55), (0.75, 0.16), vm, 1, F8, axis_mat=ax)
    S.trace("Icur", lambda u: S.peak_plateau(u, on=u_on, off=2.0) * 1.8 - 0.9,
            (0.42, -0.35, 0.36), (0.75, 0.16), im, 1, F8, axis_mat=ax)
    S.dolly("CamB_08a", (0.25, 0.0, 0.12), (0.3, -3.3, 0.45), (0.25, -2.8, 0.35), 1, F8)
    S.locked("CamB_09b", (0.0, 0.0, 0.08), (0.18, -1.05, 0.62), lens=35)


# ---- nphr：B_16a ------------------------------------------------------------------------------
def nphr(sc, rnd):
    F6 = S.shot_frames("B_16a")
    F = F6 + 8
    f_on = round(F6 * 0.62)                                # 「黄光照上去」约在旁白 62% 处
    xs = (-0.42, 0.42)
    _membrane("NpM", holes=[_hole(x) for x in xs], half_w=200.0, half_d=26.0)
    pumps = [_protein(f"NpHR{i}", "cl_pump", (x, 0, 0), (0.85, 0.66, 0.35), seed=3 + i, pore_color=AMBER)
             for i, x in enumerate(xs)]
    _beam("Yellow", 0.0, AMBER, [(1, 0.0), (f_on, 0.0), (f_on + 4, 2.4), (F, 2.4)], r_end=0.55, top=3.2, z_target=0.5)
    _idle_ions("ClOut", "cl", 20, (-0.35, 0.0, 0.36), (0.95, 0.25, 0.08), F, rnd)
    k = 0
    for i, p in enumerate(pumps):
        S.set_emit_color(p["retinal_glow_mat"], 1, AMBER)
        S.set_gain(p["retinal_glow_mat"], 1, 0.0)
        f = f_on + 4 + 6 * i
        while f < F - 30:
            _pulse(p["retinal_glow_mat"], f, 2.6, rise=2, fall=10)
            ion = BB.ion(f"ClIn{k}", "cl", (p["center"].x, 0, 0.45))
            path = list(reversed(BO.pump_path(p, z_from=-0.45, z_to=0.45)))   # 胞外 → 胞内
            _ion_story(ion, path, f + 2, 26, F, rnd)
            k += 1
            f += 20
    u_on = (f_on - 1) / F6
    spikes = [0.08, 0.20, 0.31, 0.43, 0.54]                 # 光前的自发锋电位（示意，不对应频率）

    def vm(u):
        if u < u_on:
            return S.spike_train(u, spikes)
        return -0.6 - 0.3 * S.smooth((u - u_on) / 0.06)       # 光后往下走（超极化），锋电位消失

    S.trace("Vm", vm, (0.42, -0.35, 0.50), (0.75, 0.22), M.emission("VmTrace", WHITE, 4.0), 1, F6,
            axis_mat=S.matte("TraceAxis", (0.5, 0.5, 0.5)))
    S.dolly("CamB_16a", (0.25, 0.0, 0.12), (0.3, -3.3, 0.45), (0.25, -2.8, 0.35), 1, F6)


# ---- nphr_plan：B_16b -------------------------------------------------------------------------
def nphr_plan(sc, rnd):
    F = _frames("B_16b")
    _membrane("NPM", holes=[_hole()], half_w=110.0, half_d=30.0, rows=2)
    p = _protein("NpHRPlan", "cl_pump", (0, 0, 0), (0.6, 0.6, 0.6), seed=3)
    # 黄光：一条向下的正弦波线（蓝图里光束不显示，用线表示）
    pts = [(-0.30 + 0.03 * math.sin(k * 1.1), -0.05, 0.92 - 0.55 * k / 40) for k in range(41)]
    wave = S.tube("LightWave", pts, 0.008)
    S.reveal(wave, 1, 10)
    S.arrow("LightHead", pts[-3], (-0.30, -0.05, 0.30), 0.008)
    # 氯离子向内
    S.arrow("ClArrow", (0.0, -0.32, 0.42), (0.0, -0.32, -0.42), 0.012)
    path = list(reversed(BO.pump_path(p, z_from=-0.45, z_to=0.45)))
    for k in range(3):
        ion = BB.ion(f"ClPlan{k}", "cl", path[0], "structure")
        BB.through(ion, path, 4 + 9 * k, 4 + 9 * k + 18)
    # 电压下降：膜右端外侧向下的箭头（放在膜上会被剖面挡住，只露出箭杆）
    S.arrow("VArrow", (1.25, -0.05, 0.35), (1.25, -0.05, -0.15), 0.014)
    _anchor("LabelAnchor_light", (-0.45, 0, 0.92))
    _anchor("LabelAnchor_cl", (0.10, -0.32, -0.33))         # 箭头右侧、膜下方；再往下就进字幕安全区
    _anchor("LabelAnchor_v", (1.25, -0.05, 0.47))
    S.locked("CamB_16b", (0.15, 0.0, 0.2), (0.15, -3.0, 0.35), lens=35)


# ---- dual：B_17b / B_91 -----------------------------------------------------------------------
def dual(sc, rnd):
    F = _frames("B_17b", "B_91") + 4
    XL, XR = -0.40, 0.40
    _membrane("DM", holes=[_hole(XL), _hole(XR)], half_w=150.0, half_d=26.0)
    ch = _protein("DualChR2", "channel", (XL, 0, 0), (0.45, 0.58, 0.90), seed=1)
    np_ = _protein("DualNpHR", "cl_pump", (XR, 0, 0), (0.90, 0.68, 0.32), seed=3, pore_color=AMBER)
    mid = F // 2
    _beam("DBlue", XL, BLUE, [(1, 0.0), (2, 2.4), (mid - 2, 2.4), (mid, 0.0)], r_end=0.22)
    _beam("DAmber", XR, AMBER, [(mid, 0.0), (mid + 2, 2.4), (F, 2.4)], r_end=0.22)
    BO.set_open(ch, 1, 0.0, glow=0.0)
    BO.set_open(ch, 4, 1.0, glow=1.3)
    BO.set_open(ch, mid - 2, 1.0, glow=1.3)
    BO.set_open(ch, mid + 2, 0.0, glow=0.0)
    S.set_emit_color(np_["retinal_glow_mat"], 1, AMBER)
    S.set_gain(np_["retinal_glow_mat"], 1, 0.0)
    _pulse(np_["retinal_glow_mat"], mid + 2, 2.8, rise=2, hold=F - mid - 8, fall=4)
    for k in range(3):
        ion = BB.ion(f"DCat{k}", "cation", (XL, 0, 0.45))
        BB.through(ion, BO.pore_path(ch, 0.45, -0.42), 4 + 4 * k, 4 + 4 * k + 12)
        cl = BB.ion(f"DCl{k}", "cl", (XR, 0, 0.45))
        BB.through(cl, list(reversed(BO.pump_path(np_, -0.45, 0.45))), mid + 3 + 4 * k, mid + 3 + 4 * k + 12)
    S.studio_lights(0.5)
    S.locked("CamB_17b", (0.0, 0.0, 0.05), (0.0, -2.3, 0.5), lens=35)
    S.locked("CamB_91", (0.0, 0.0, 0.0), (0.25, -2.6, 0.75), lens=50)


# ---- spectrum：B_18a --------------------------------------------------------------------------
def spectrum(sc, rnd):
    F = _frames("B_18a")
    XL, XR = -0.45, 0.45
    _membrane("SM", holes=[_hole(XL), _hole(XR)], half_w=160.0, half_d=60.0)
    left = _protein("BlueChan", "channel", (XL, 0, 0), (0.5, 0.5, 0.5), seed=1)
    right = _protein("ChrimsonR", "channel", (XR, 0, 0), (0.5, 0.5, 0.5), seed=4)
    _tone_tree(left, (0.80, 0.92, 1.25))                   # 冷灰：蓝敏
    _tone_tree(right, (1.25, 0.88, 0.80))                  # 暖灰：长波长
    cu = bpy.data.curves.new("ChrimsonRLabel", "FONT")
    cu.body = "ChrimsonR"
    cu.align_x = "CENTER"
    cu.size = 0.085
    cu.extrude = 0.004
    txt = S.link(bpy.data.objects.new("ChrimsonRLabel", cu))
    txt.location = (XR, -0.05, 0.42)
    txt.rotation_euler = (math.radians(90), 0, 0)
    bpy.context.view_layer.objects.active = txt
    for o in bpy.context.selected_objects:
        o.select_set(False)
    txt.select_set(True)
    bpy.ops.object.convert(target="MESH")                  # 文字转网格：风格系统只给 MESH / CURVE 换材质
    txt = bpy.data.objects["ChrimsonRLabel"]
    styles.tag(txt, "structure")
    _sem_tone(txt, (1.6, 1.5, 1.4))
    _anchor("LabelAnchor_human", (XR, -0.05, 0.34))
    S.dolly("CamB_18a", (0.0, 0.0, 0.08), (0.0, -2.9, 0.75), (0.05, -2.3, 0.6), 1, F)


# ---- 风格后处理（一个模块一个 after_style）---------------------------------------------------------
def _apply_sem_tones():
    cache = {}
    for o in bpy.data.objects:
        tone = o.get("sem_tone")
        if tone is None or o.type not in ("MESH", "CURVE", "FONT") or not o.data.materials:
            continue
        base = o.data.materials[0]
        if base is None or not base.use_nodes:
            continue
        key = (base.name, tuple(round(v, 3) for v in tone))
        if key not in cache:
            m = base.copy()
            m.name = f"{base.name}_tone{len(cache)}"
            for nd in m.node_tree.nodes:
                if nd.type == "VALTORGB":
                    for el in nd.color_ramp.elements:
                        el.color = (*(min(1.0, el.color[i] * tone[i]) for i in range(3)), 1)
            cache[key] = m
        o.data.materials.clear()
        o.data.materials.append(cache[key])


def _energy_dim_membrane():
    """energy 下膜只做背景：头基 / 尾链 / 芯的暗边减到三成，蛋白的轮廓才读得出来；离子降亮度，免得泛白。"""
    dim = styles.dark_rim("EnergyRimDim", strength=0.35)
    for o in bpy.data.objects:
        if o.type == "MESH" and o.name.endswith(("Heads", "Tails", "Core")) and o.get("role") == "structure":
            o.data.materials.clear()
            o.data.materials.append(dim)
    for m in bpy.data.materials:
        if m.name.startswith("Ion_") and m.node_tree.nodes.get("Emission"):
            m.node_tree.nodes["Emission"].inputs["Strength"].default_value = 2.2


def after_style(style, shot_id):
    sc = bpy.context.scene
    S.after_style_common(sc, style)
    if style == "energy":
        _energy_dim_membrane()
        bright = styles.dark_rim("EnergyRimProtein", strength=2.8)
        for o in bpy.data.objects:
            if o.get("protein"):
                o.data.materials.clear()
                o.data.materials.append(bright)
    if style == "sem":
        _apply_sem_tones()
        if sc.render.engine == "CYCLES":
            S.cycles(sc, {"preview": 16, "sample": 24, "final": 32}, bounces=1, clamp=0.0)
    if style == "blueprint":
        sc.render.use_motion_blur = False


VARIANTS = {"patch": patch, "sheet": sheet, "br_lattice": br_lattice, "br_pump": br_pump,
            "pump_channel": pump_channel, "pair": pair, "chr1": chr1, "truncate": truncate, "chr2": chr2,
            "nphr": nphr, "nphr_plan": nphr_plan, "dual": dual, "spectrum": spectrum}

FRAMES = 700


def build(variant="chr2", seed=7, kinds=None):
    sc = C.reset_scene(FRAMES)
    rnd = random.Random(seed)
    sc["variant"] = variant
    fn = VARIANTS[variant]
    if variant == "pair":
        fn(sc, rnd, tuple(kinds or ("pump", "channel")))
    else:
        fn(sc, rnd)
    return sc
