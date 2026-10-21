"""E2 第一幕（A 段）的 Blender 镜头：一个模块，多个 variant；只有一个 after_style，内部按 variant 分支（WORKFLOW 9）。

  spike      A_01a xray / A_01b energy（EEVEE）：参数化脂质双层剖面（build_bilayer）上三个通用离子孔
             （build_opsin.build_pore_channel，不对应具体电压门控通道）。膜外侧一排「+」、内侧一排「−」；
             锋电位时阳离子穿孔进入、两侧符号翻过来再翻回，前上方一条膜电位曲线（e2_shot.spike_shape）猛地翻上去再回来。
             01a 慢推看全景；01b 同场景近景，从锋电位前一刻开始（start 112），膜内侧发光后熄灭。
  recording  A_02a documentary（Cycles）：暗室实验台上一块风格化组织块（浅米灰示意块，不是真组织、无血），
             一根记录电极下探，组织上一圈细环标出被标记的一小块；后面显示器上一条锋电位串的活动痕迹慢慢画出。无人物。
  cluster    A_03b energy（EEVEE）：一小群参数化神经元（e2_shot.neuron_cluster），三个被蓝光束点亮，随后琥珀光束打上，
             蓝色光晕被按暗。示意，不对应具体脑区。
  relay      A_05a clay / A_06b clay（EEVEE）：白模工作台上四个抽象零件用箭头串成多步接力（依次亮起），最后一个零件
             （带孔的环）旁边夹着一个外加的「化学开关」小件；前面一条计时条，填充停在刻度「ms」之前。不点名任何系统。
             06b（start = 05a 之后）其他零件让开，只留中间台座上的一个七次跨膜蛋白（build_opsin）。
  opsin      A_06a energy（EEVEE）/ A_91 sem（Cycles）：双层里一个七次跨膜通道蛋白（build_opsin，kind=channel）。
             06a：一束蓝光打上，视黄醛闪一下，TM1/TM2/TM7 让开、孔打开，几个阳离子穿过；慢推。
             91：同场景开灯前（start 1），孔关着，显微风格只看结构。
  brain      A_07a xray（EEVEE）：风格化小鼠脑（build_brain.mouse_brain）冠状剖面，切面过下丘脑外侧区（LH）。外形是 shell
             （xray 下变玻璃），剖面板是 structure；镜头从斜前方推向切面，LH 一小团细胞亮起、一圈细环标出。
  bench      A_08a photoreal（Cycles）：风格化实验台上一只风格化小鼠（build_props.mouse，道具示意，无写实脸、无毛发特写），
             头顶一个示意光纤植入件（build_props.fiber_implant），蓝光只在光纤尖端，按脉冲闪；慢推到头部。
  cage       A_92 documentary（Cycles）：暗笼里的风格化小鼠，光纤是一根从上方垂下的细线，尖端一点蓝光；胡须轻动。

中文标注：A 段这些镜头都不需要（registry 里不设 raw）。几何依据见各 build_*.py 文件头；全部示意（simplified / artistic）。
"""
import math
import random

import bpy
from mathutils import Vector

import build_bilayer as BB
import build_brain as BR
import build_opsin as BO
import build_props as P
import common as C
import e2_common as E
import e2_shot as S
import styles

FPS = 24
T = styles.tag
BLUE = S.lin(E.CHANNEL)
AMBER = S.lin(E.AMBER)
CYAN = S.lin(E.MEMBRANE)
WHITE = S.lin(E.LINE)

# 各 variant 的场景长度（帧）：最长镜头 + 余量；06b 接在 05a 之后
F_01A = S.shot_frames("A_01a", 255)
F_05A = S.shot_frames("A_05a", 339)
F_06B_START = F_05A + 16
SPIKE_F = 130                       # A_01a 里锋电位的帧（曲线 reveal 到一半时）；A_01b 从 SPIKE_F - 18 开始


def _membrane_mats(b):
    """双层的材质：头基膜青（structure）、尾链浅灰（structure）、疏水芯（shell：xray 下变玻璃）。"""
    heads = S.matte("LipidHead", S.lin((150, 214, 200)), 0.5)
    tails = S.matte("LipidTail", (0.55, 0.57, 0.6), 0.6)
    core = S.matte("LipidCore", (0.35, 0.4, 0.45), 0.6)
    b["heads"].data.materials.append(heads)
    b["tails"].data.materials.append(tails)
    b["core"].data.materials.append(core)
    T(b["heads"], "structure")
    T(b["tails"], "structure")
    T(b["core"], "shell")


def _pore_through(x, y=0.0, z0=0.55, z1=-0.6):
    return [(x + 0.06, y - 0.03, z0), (x, y, 0.26), (x, y, 0.0), (x, y, -0.26), (x - 0.07, y + 0.04, z1)]


# ---- spike：A_01a / A_01b -------------------------------------------------------------------------
def spike(sc, rnd):
    sc["variant"] = "spike"
    xs = (-1.2, 0.0, 1.2)
    b = BB.build_bilayer("Mem", half_w=230.0, half_d=130.0, holes=[(x * 100, 0.0, 24.0) for x in xs], seed=3)
    _membrane_mats(b)
    stave = S.matte("PoreStave", S.lin(E.CHANNEL_DEEP), 0.45)
    pores = [BO.build_pore_channel(f"Pore{i}", loc=(x, 0, 0), mat=stave, tag=T) for i, x in enumerate(xs)]
    f_sp = SPIKE_F
    for p in pores:                                   # 锋电位前后孔道亮一下（示意「孔打开」）
        S.set_strength(p["pore_mat"], 1, 0.0)
        S.set_strength(p["pore_mat"], f_sp - 14, 0.0)
        S.set_strength(p["pore_mat"], f_sp - 6, 6.0)
        S.set_strength(p["pore_mat"], f_sp + 14, 0.0)
    # 两侧电荷符号：静息时外 + 内 −；锋电位窗口里翻过来
    plus_m = S.glow("ChargePlus", WHITE, 3.0)
    minus_m = S.glow("ChargeMinus", CYAN, 3.0)
    gx = [-1.8 + 0.45 * k for k in range(9)]
    f_flip0, f_flip1 = f_sp - 4, f_sp + 22
    for k, x in enumerate(gx):
        if any(abs(x - px) < 0.2 for px in xs):
            continue
        for side, z in (("Out", 0.42), ("In", -0.42)):
            rest_plus = side == "Out"
            for state, is_plus in (("Rest", rest_plus), ("Flip", not rest_plus)):
                root, parts = S.plus_glyph(f"Q{side}{state}{k}", (x, -1.42, z), 0.09,
                                           plus_m if is_plus else minus_m, "emitter", minus=not is_plus)
                for o in parts:
                    if state == "Rest":
                        S.key(o, 1, hide_render=False)
                        S.key(o, f_flip0, hide_render=True)
                        S.key(o, f_flip1, hide_render=False)
                    else:
                        S.show_between(o, f_flip0, f_flip1)
    # 阳离子：胞外一团，锋电位时几个顺孔进来
    ions = BB.cloud("Na", "cation", 26, (0, -0.2, 0.5), (2.0, 0.9, 0.08), seed=11)
    for i, ion in enumerate(ions):
        BB.jitter(ion, 1, F_01A, 0.02, seed=100 + i)
    movers = BB.cloud("NaIn", "cation", 9, (0, -0.1, 0.55), (0.1, 0.1, 0.03), seed=12)
    for i, ion in enumerate(movers):
        x = xs[i % 3]
        f0 = f_sp - 12 + 3 * (i // 3)
        BB.through(ion, _pore_through(x, -0.04 + 0.04 * (i // 3)), f0, f0 + 16)
    # 膜内侧的「电位光」：一块贴着内叶的薄发光板，锋电位时亮起再熄
    glow_m = S.halo("MemPotentialGlow", BLUE, 0.0)
    gl = S.box("MemGlow", (0, 0, -0.22), (4.4, 2.5, 0.05), glow_m, "emitter")
    for f, g in ((1, 0.0), (f_sp - 8, 0.0), (f_sp, 2.4), (f_sp + 18, 0.6), (f_sp + 34, 0.0)):
        S.set_gain(glow_m, f, g)
    gl.visible_shadow = False
    # 膜电位曲线：前上方，从左往右画；锋电位落在曲线一半处
    tr_m = S.glow("VmTrace", BLUE, 5.0)
    ax_m = S.matte("VmAxis", (0.6, 0.62, 0.66))
    f_r0, f_r1 = 24, 236
    at = (f_sp - f_r0) / (f_r1 - f_r0)
    tr, base, pts = S.trace("Vm", lambda u: S.spike_shape(u, at, 0.07), (-1.1, -1.35, 0.8), (2.2, 0.28),
                            tr_m, f_r0, f_r1, n=220, r=0.007, axis_mat=ax_m)   # 曲线在离子上方，画面上沿内
    S.trace_head("VmHead", pts, f_r0, f_r1, 0.018, S.glow("VmHeadMat", WHITE, 8.0))
    S.studio_lights(0.4, (0, 0, 0.2))
    # 相机
    S.dolly("CamA_01a", (0, -1.3, 0.26), (0.0, -5.6, 0.55), (0.0, -4.75, 0.47), 1, F_01A, lens=50)
    S.locked("CamA_01b", (0.0, -1.3, 0.0), (0.3, -2.9, 0.18), lens=35)


# ---- recording：A_02a -------------------------------------------------------------------------
def recording(sc, rnd):
    sc["variant"] = "recording"
    n = S.shot_frames("A_02a", 275)
    S.dark_room()
    P.bench("Bench", size=(1.4, 0.8), tag=T)
    # 组织块：浅米灰圆角块，放在一个小载物台上（示意，不是真实组织）
    stage = S.box("Stage", (0, 0.02, 0.012), (0.16, 0.12, 0.024), S.matte("StageMat", (0.08, 0.085, 0.09), 0.4),
                  "structure", bevel=0.003)
    tissue = S.box("Tissue", (0, 0.02, 0.034), (0.07, 0.05, 0.022), S.matte("TissueMat", (0.78, 0.72, 0.66), 0.65),
                   "structure", bevel=0.008)
    mark_m = S.glow("TissueMark", CYAN, 0.0)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.011, minor_radius=0.0009, location=(0.012, 0.016, 0.0452))
    ring = bpy.context.object
    ring.name = "TissueMarkRing"
    ring.data.materials.append(mark_m)
    T(ring, "emitter")
    S.set_strength(mark_m, 1, 0.0)
    S.set_strength(mark_m, int(n * 0.55), 0.0)
    S.set_strength(mark_m, int(n * 0.55) + 18, 4.0)
    # 电极：从上方斜着下探到组织表面
    el = P.electrode("Electrode", (0.0, 0.0, 0.0), direction=(0.35, 0.25, -1.0), length=0.09, tag=T)
    tip_end = Vector((-0.008, 0.022, 0.0455))
    d = Vector((0.35, 0.25, -1.0)).normalized()
    S.key(el["root"], 1, location=tuple(tip_end - d * 0.05))
    S.key(el["root"], int(n * 0.3), location=tuple(tip_end))
    # 显示器 + 锋电位串痕迹
    scr = P.screen("Monitor", (0.05, 0.3, 0.24), size=(0.46, 0.27), tag=T)
    tr_m = S.glow("ScreenTrace", S.lin((120, 230, 205)), 3.0)
    pulses = [0.18 + 0.075 * k + 0.02 * math.sin(k * 2.3) for k in range(10)]
    S.trace("ScreenVm", lambda u: S.spike_train(u, pulses, 0.012) * 0.8, (-0.16, 0.2955, 0.24), (0.42, 0.16),
            tr_m, int(n * 0.12), n - 10, n=360, r=0.0013)
    S.area("Key", (-0.5, -0.6, 0.7), (0, 0.02, 0.04), 0.5, 22.0, color=(1.0, 0.94, 0.86))
    S.area("Rim", (0.5, 0.6, 0.4), (0, 0.02, 0.04), 0.4, 8.0, color=(0.75, 0.85, 1.0))
    S.dolly("CamA_02a", (0.02, 0.06, 0.1), (0.28, -0.72, 0.34), (0.2, -0.5, 0.25), 1, n, lens=50,
            aim1=(0.01, 0.05, 0.08))


# ---- cluster：A_03b ---------------------------------------------------------------------------
def cluster(sc, rnd):
    sc["variant"] = "cluster"
    n = S.shot_frames("A_03b", 32)
    cells = S.neuron_cluster("Nc", 9, (0, 0, 0), 0.8, seed=21, mat=S.matte("CellClay", (0.7, 0.7, 0.7)), scale=0.5)
    lit = (1, 4, 6)
    for i in lit:
        cell, root = cells[i]
        S.soma_glow(f"NcBlue{i}", cell, root, BLUE, [(1, 0.0), (5, 2.6), (13, 2.6), (20, 0.3), (n, 0.0)])
        S.soma_glow(f"NcAmber{i}", cell, root, AMBER, [(1, 0.0), (12, 0.0), (19, 1.1), (n, 0.7)], r=0.42)
    bb, bm = S.cone_beam("BlueBeam", (-1.0, 2.0, 3.4), (-0.1, 0.2, 0.0), 0.32, BLUE, 0.0)
    ab, am = S.cone_beam("AmberBeam", (1.1, 2.0, 3.4), (0.1, 0.2, 0.0), 0.32, AMBER, 0.0)
    for f, gb, ga in ((1, 0.0, 0.0), (3, 0.2, 0.0), (12, 0.2, 0.0), (16, 0.0, 0.2), (n, 0.0, 0.2)):
        S.set_gain(bm, f, gb)
        S.set_gain(am, f, ga)
    S.locked("CamA_03b", (0.2, 0, -0.2), (0.2, -3.6, 0.35), lens=35)


# ---- relay：A_05a / A_06b ---------------------------------------------------------------------
def relay(sc, rnd):
    sc["variant"] = "relay"
    sc.frame_end = F_06B_START + S.shot_frames("A_06b", 32) + 8
    n = F_05A
    top = P.bench("Bench", size=(2.4, 1.3), tag=T)["top"]
    T(top, "structure")
    clay = S.matte("RelayPart", (0.7, 0.7, 0.7))
    xs = (-0.75, -0.25, 0.25, 0.75)
    parts = [
        S.cylinder("RelayDisc", 0.11, 0.05, (xs[0], 0.1, 0.025), clay, verts=48),
        S.sphere("RelayBall", 0.1, (xs[1], 0.1, 0.1), clay),
        S.box("RelayBlock", (xs[2], 0.1, 0.08), (0.18, 0.14, 0.16), clay, bevel=0.02),
    ]
    bpy.ops.mesh.primitive_torus_add(major_radius=0.09, minor_radius=0.035, location=(xs[3], 0.1, 0.13),
                                     rotation=(math.pi / 2, 0, 0))
    ring = bpy.context.object
    ring.name = "RelayRing"
    ring.data.materials.append(clay)
    T(ring, "structure")
    parts.append(ring)
    # 外加的化学开关：夹在环上的小夹子 + 两个小环的「分子」（不画成任何真实分子式）
    clip = S.box("ChemClip", (xs[3] + 0.1, 0.1, 0.22), (0.05, 0.05, 0.03), clay, bevel=0.008)
    mol = [S.sphere(f"ChemBead{k}", 0.022, (xs[3] + 0.13 + 0.04 * k, 0.1, 0.27 + 0.02 * (k % 2)), clay) for k in range(3)]
    stick = S.tube("ChemStick", [(xs[3] + 0.1, 0.1, 0.23)] + [tuple(m.location) for m in mol], 0.006, clay)
    chem = [clip, stick] + mol
    # 依次亮起的箭头
    arrows = []
    for k in range(3):
        am = S.glow(f"RelayArrow{k}", BLUE, 0.0)
        sh, hd = S.arrow(f"RelayArrow{k}", (xs[k] + 0.13, 0.1, 0.1), (xs[k + 1] - 0.13, 0.1, 0.1), 0.012, am, "emitter")
        f0 = int(n * (0.18 + 0.12 * k))
        S.set_strength(am, 1, 0.0)
        S.set_strength(am, f0, 0.0)
        S.set_strength(am, f0 + 12, 4.0)
        arrows += [sh, hd]
    # 计时条：轨道 + 刻度，右端刻度标 ms；填充慢慢走、停在 ms 之前
    trk = S.box("TimerTrack", (0, -0.32, 0.012), (1.3, 0.05, 0.012), S.matte("TimerTrack", (0.3, 0.3, 0.32)))
    ticks = [S.box(f"TimerTick{k}", (-0.65 + 0.13 * k, -0.32, 0.03), (0.006, 0.05, 0.03 if k < 10 else 0.06), clay)
             for k in range(11)]
    cu = bpy.data.curves.new("TimerMs", "FONT")
    cu.body = "ms"
    cu.size = 0.06
    cu.align_x = "CENTER"
    txt = S.link(bpy.data.objects.new("TimerMs", cu))
    txt.location = (0.65, -0.37, 0.07)
    txt.rotation_euler = (math.radians(60), 0, 0)
    txt.data.materials.append(clay)
    T(txt, "structure")
    fill_m = S.glow("TimerFill", AMBER, 3.0)
    fill = S.box("TimerFill", (-0.65, -0.32, 0.02), (1.0, 0.03, 0.01), fill_m, "emitter", bevel=0.002)   # bevel 会把尺寸烘进网格，scale.x 才是长度比例
    fill.scale = (0.001, 1, 1)
    S.key(fill, int(n * 0.2), scale=(0.001, 1, 1), location=(-0.65, -0.32, 0.02))
    stop = 0.62                                       # 停在全程 62% 处（ms 刻度在 100%）
    S.key(fill, int(n * 0.85), scale=(1.3 * stop, 1, 1), location=(-0.65 + 1.3 * stop / 2, -0.32, 0.02))
    # A_06b：台座上的七次跨膜蛋白；其他零件让开
    ped = S.cylinder("Pedestal", 0.16, 0.04, (0, 0.35, 0.02), clay, verts=48)
    op = BO.build_opsin("RelayOpsin", "channel", loc=(0, 0.35, 0.19), mat=clay, tag=T)
    op["root"].scale = (0.55, 0.55, 0.55)
    for o in op["root"].children_recursive + [ped]:
        if o.type != "EMPTY":
            S.show_between(o, F_06B_START - 2)
    f0, f1 = F_06B_START + 2, F_06B_START + 22
    for o, dx, dy in ([(p_, -1 if p_.location.x < 0 else 1, 0) for p_ in parts]
                      + [(c_, 1, 0) for c_ in chem]):
        S.key(o, f0, location=tuple(o.location))
        S.key(o, f1, location=(o.location.x + dx * 1.6, o.location.y + dy, o.location.z))
    for o in arrows + [trk, fill, txt] + ticks:
        S.key(o, f0, location=tuple(o.location))
        S.key(o, f1, location=(o.location.x, o.location.y - 1.4, o.location.z))
    S.studio_lights(0.35, (0, 0, 0.1))
    S.dolly("CamA_05a", (0, -0.05, 0.12), (0, -2.7, 1.35), (0, -2.25, 1.05), 1, n, lens=50)
    S.locked("CamA_06b", (0, 0.35, 0.17), (0.0, -0.75, 0.42), f=F_06B_START, lens=35)


# ---- opsin：A_06a / A_91 ----------------------------------------------------------------------
def opsin(sc, rnd):
    sc["variant"] = "opsin"
    n = S.shot_frames("A_06a", 134)
    px, py = BO.pore_center()
    b = BB.build_bilayer("Mem", half_w=160.0, half_d=110.0, holes=[(0.0, 0.0, 26.0)], seed=5)
    _membrane_mats(b)
    prot = S.matte("Opsin", S.lin(E.CHANNEL_DEEP), 0.4)
    ret = S.matte("Retinal", S.lin((255, 210, 120)), 0.4)
    p = BO.build_opsin("ChR", "channel", mat=prot, retinal_mat=ret, tag=T)
    f_hit = int(n * 0.42)                              # 「光打上去」
    beam, bm = S.cone_beam("Light", (-0.8, 0.9, 1.7), (0.0, 0.0, 0.05), 0.1, BLUE, 0.0)
    for f, g in ((1, 0.0), (f_hit - 10, 0.0), (f_hit, 0.6), (n, 0.45)):
        S.set_gain(bm, f, g)
    BO.flash_retinal(p, f_hit + 2, peak=3.2)
    BO.set_open(p, 1, 0.0, glow=0.0)
    BO.set_open(p, f_hit + 4, 0.0, glow=0.0)
    BO.set_open(p, f_hit + 20, 1.0, glow=2.5)
    ions = BB.cloud("NaO", "cation", 14, (0, -0.1, 0.62), (1.2, 0.8, 0.12), seed=9)
    for i, ion in enumerate(ions):
        BB.jitter(ion, 1, n, 0.02, seed=300 + i)
    for i in range(4):
        ion = BB.ion(f"NaIn{i}", "cation", (0.1, 0, 0.6))
        f0 = f_hit + 22 + 7 * i
        BB.through(ion, BO.pore_path(p, 0.6, -0.55), f0, f0 + 18)
    S.studio_lights(0.3, (0, 0, 0.05))
    S.dolly("CamA_06a", (0, 0, 0.04), (0.15, -2.3, 0.75), (0.1, -1.75, 0.5), 1, n, lens=50)
    S.locked("CamA_91", (0, 0, 0.05), (0.55, -1.3, 1.0), lens=50)


# ---- brain：A_07a -----------------------------------------------------------------------------
def brain(sc, rnd):
    sc["variant"] = "brain"
    n = S.shot_frames("A_07a", 291)
    br = BR.mouse_brain("Brain", section="coronal", tag=T, shell_role="shell")
    cut = BR.REGIONS["lateral_hypothalamus"][0]
    lh = br["regions"]["lateral_hypothalamus"]
    f_on = int(n * 0.55)
    cell_m = S.glow("LHCell", BLUE, 0.0)
    for k in range(14):
        a = rnd.uniform(0, 2 * math.pi)
        r = 0.016 * math.sqrt(rnd.random())
        c = S.sphere(f"LHCell{k}", 0.0035, (cut + 0.006, lh[1] + r * math.cos(a), lh[2] + 0.7 * r * math.sin(a)),
                     cell_m, "emitter", seg=10, rings=6)
        S.show_between(c, f_on)                         # 熄着的发光体在 xray 里是黑点：亮起之前不渲染
    S.set_strength(cell_m, 1, 0.0)
    S.set_strength(cell_m, f_on, 0.0)
    S.set_strength(cell_m, f_on + 14, 6.0)
    ring_m = S.glow("LHRing", CYAN, 0.0)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.03, minor_radius=0.0012, location=(cut + 0.007, lh[1], lh[2]),
                                     rotation=(0, math.pi / 2, 0), major_segments=64)
    ring = bpy.context.object
    ring.name = "LHRing"
    ring.data.materials.append(ring_m)
    T(ring, "emitter")
    S.show_between(ring, f_on + 8)
    S.set_strength(ring_m, 1, 0.0)
    S.set_strength(ring_m, f_on + 8, 0.0)
    S.set_strength(ring_m, f_on + 26, 5.0)
    S.studio_lights(0.25, (0, 0, 0))
    S.camera("CamA_07a", [(1, (-0.02, 0.0, 0.0), (1.55, -1.25, 0.65), 50, 8.0),
                          (n, (cut, lh[1], lh[2] + 0.02), (0.62, -0.08, 0.02), 50, 8.0)])


# ---- bench：A_08a -----------------------------------------------------------------------------
def bench_scene(sc, rnd):
    sc["variant"] = "bench"
    n = S.shot_frames("A_08a", 461)
    C.set_world(top=(0.03, 0.035, 0.045), horizon=(0.012, 0.014, 0.018), bottom=(0.004, 0.004, 0.005))
    P.bench("Bench", size=(1.2, 0.7), tag=T, color=(0.2, 0.21, 0.22))
    pad = S.box("Pad", (0.02, 0.0, 0.002), (0.22, 0.16, 0.004), S.matte("PadMat", (0.55, 0.6, 0.65), 0.8), "structure")
    m = P.mouse("Mouse", (0.0, 0.0, 0.004), heading=math.radians(15), tag=T)
    fi = P.fiber_implant("Fiber", (0.0, 0.0, 0.0), direction=(0, 0, -1), cable_len=0.3, tag=T)
    fi["root"].parent = m["head_root"]                # 植入件跟着头动；尖端在头顶表面下一点
    fi["root"].location = (0.008, 0.0, 0.019)            # 尖端在头顶表面
    gm = fi["tip_glow_mat"]
    f_on = int(n * 0.3)
    S.set_gain(gm, 1, 0.0)
    for f in range(f_on, int(n * 0.85), 4):            # 脉冲（示意节奏，不对应具体频率）
        S.set_gain(gm, f, 3.0)
        S.set_gain(gm, f + 2, 0.0)
    S.set_gain(gm, int(n * 0.85) + 2, 0.0)
    hr = m["head_root"]                                # 后段头微微抬起
    S.key(hr, 1, rotation_euler=(0, math.radians(10), 0))
    S.key(hr, int(n * 0.7), rotation_euler=(0, math.radians(10), 0))
    S.key(hr, int(n * 0.8), rotation_euler=(0, math.radians(-4), 0))
    P.whisker_twitch(m, int(n * 0.8), int(n * 0.92))
    S.area("Key", (-0.35, -0.4, 0.55), (0.03, 0, 0.03), 0.4, 4.0, color=(1.0, 0.95, 0.88))
    S.area("Fill", (0.45, -0.25, 0.2), (0.03, 0, 0.03), 0.6, 1.0, color=(0.8, 0.88, 1.0))
    S.area("Rim", (0.0, 0.45, 0.35), (0.03, 0, 0.03), 0.3, 2.5)
    S.dolly("CamA_08a", (0.03, 0.0, 0.03), (0.38, -0.42, 0.24), (0.17, -0.2, 0.11), 1, n, lens=50,
            aim1=(0.045, 0.01, 0.04))


# ---- cage：A_92 -------------------------------------------------------------------------------
def cage_scene(sc, rnd):
    sc["variant"] = "cage"
    n = S.shot_frames("A_92", 36)
    S.dark_room()
    P.bench("Shelf", size=(1.0, 0.6), tag=T, color=(0.1, 0.1, 0.11))
    P.cage("Cage", tag=T, floor_tint=(0.35, 0.33, 0.3))
    m = P.mouse("Mouse", (0.03, 0.02, 0.008), heading=math.radians(-30), tag=T)
    P.whisker_twitch(m, 4, n - 4)
    tip = (0.03 + 0.045 * math.cos(math.radians(-30)) + 0.008, 0.02 + 0.045 * math.sin(math.radians(-30)), 0.06)
    fi = P.fiber_implant("Fiber", tip, direction=(0, 0, -1), cable_len=0.12, ferrule_len=0.006, tag=T)
    S.set_gain(fi["tip_glow_mat"], 1, 1.2)
    S.tube("FiberLine", [(tip[0], tip[1], 0.075), (tip[0] + 0.01, tip[1], 0.25), (tip[0] + 0.02, tip[1], 0.5)],
           0.0006, S.matte("FiberLineMat", (0.6, 0.65, 0.7)), "structure")
    S.area("Top", (0, 0, 0.7), (0, 0, 0), 0.3, 3.0, color=(0.75, 0.82, 1.0))
    S.area("Side", (-0.6, -0.5, 0.25), (0, 0, 0.05), 0.4, 1.5, color=(1.0, 0.92, 0.85))
    S.locked("CamA_92", (0.03, 0.0, 0.05), (0.42, -0.62, 0.3), lens=50)


# ---- 风格后处理（一个模块一个 after_style）---------------------------------------------------------
def after_style(style, shot_id):
    sc = bpy.context.scene
    v = sc.get("variant")
    S.after_style_common(sc, style)
    if v in ("recording", "cage"):
        sc.cycles.volume_step_rate = 4.0
        sc["film_grain"], sc["vignette"] = 0.3, 0.45
    elif v == "bench":
        S.cycles(sc, {"preview": 32, "sample": 64, "final": 96}, bounces=6)
    elif v == "cluster" and style == "energy":
        # 细神经突在暗边材质下看不见：整群换成很暗的线稿白自发光，亮起的只有光晕
        cm = S.glow("CellEnergy", S.lin((120, 130, 150)), 0.35)
        for o in bpy.data.objects:
            if o.name.startswith("Nc") and o.type in ("MESH", "CURVE") and "Halo" not in o.name:
                o.data.materials.clear()
                o.data.materials.append(cm)
    elif v == "opsin" and style == "energy":
        # 能量图的暗边材质在细圆柱上几乎不出边，螺旋会消失：A_06a 的蛋白换成低亮度的通道蓝自发光
        hm = S.glow("OpsinEnergy", S.lin(E.CHANNEL_DEEP), 0.8)
        for o in bpy.data.objects:
            if o.name.startswith("ChR_TM") or o.name.startswith("ChR_Loop"):
                o.data.materials.clear()
                o.data.materials.append(hm)
    elif v == "opsin" and style == "sem":
        S.cycles(sc, {"preview": 16, "sample": 24, "final": 32}, bounces=1, clamp=0.0)


VARIANTS = {"spike": spike, "recording": recording, "cluster": cluster, "relay": relay, "opsin": opsin,
            "brain": brain, "bench": bench_scene, "cage": cage_scene}


def build(variant="spike", seed=7):
    sc = C.reset_scene(max(F_01A, F_06B_START + 48, 480))
    rnd = random.Random(seed)
    VARIANTS[variant](sc, rnd)
    return sc
