"""E2 C 段（第三幕：假记忆 + 视觉临床路径 + 边界）的 Blender 镜头。一个模块多个 variant，只有一个 after_style（WORKFLOW 9）。

  brain     C_01a          energy / EEVEE：整脑示意（build_brain），满脑暗着的细胞点里只有齿状回附近一小簇被光标出。
                           raw：mograph 叠「小鼠」，锚点 LabelAnchor_Mouse（脑的前上方）。
  slice     C_02a / C_05b  clay / EEVEE：海马切片白模（build_brain.hippocampus_slice）+「环境甲」色块。
                           phase=tag（C_02a）：DG 一批细胞随甲的颜色亮起，随后每个亮细胞旁出现蓝色小点（装上通道，示意）。
                           phase=link（C_05b）：那批细胞已亮，一条线从细胞组画到甲色块。
  cage      C_02b / C_03a / C_04a  documentary 或 photoreal / Cycles：实验台上的透明笼箱（build_props），地面是环境色块。
                           env=A 无电击标记；env=B 地面有风格化锯齿标记（琥珀色，不是血、不是电火花特写）。
                           mouse=none（C_02b 空笼）| fiber（C_03a：小鼠头上光纤，尖端蓝光脉冲，锯齿标记同时闪）|
                           freeze（C_04a：小鼠走几步后停住）。小鼠是椭球示意，无毛发、无写实眼睛。
  cells     C_03b          energy / EEVEE：一小群参数化神经元，带「甲」颜色小环的几个在乙的地色上被一束蓝光打开。
  retina    C_07a / C_07b / C_09b  视网膜剖面（build_retina）。phase=rp（C_07a xray）：感光细胞一批批消失，神经节细胞层保留，
                           随后神经节细胞套上蓝色光晕（可转导）。raw：mograph 叠「可转导」，锚点 LabelAnchor_Transducible。
                           phase=sem（C_07b sem / Cycles）：上层（感光）稀，下层（神经节）密，静止。
                           phase=off（C_09b xray）：神经节细胞先被几次脉冲驱动，随即熄灭，细胞还在。
  eye       C_08a          clay / EEVEE：半个眼球剖面，玻璃体内注射一次，神经节细胞带亮起（获得新通道）；护目镜（示意道具）
                           把外界变化变成一颗颗光脉冲，穿过瞳孔落到视网膜上，每次落下神经节细胞带闪一下。
  goggles   C_08b / C_92   photoreal / Cycles：桌上一副通用造型护目镜。display=outline：镜片里只有高对比线框轮廓（C_08b）；
                           display=off：镜片暗着，没有图像（C_92）。不生成佩戴者。
  objects   C_09a          documentary / Cycles：第一人称看暗桌面上三个高对比的白色简单物体，视野被护目镜的两个镜框框住；
                           后段护目镜摘下（框消失）、物体随光一起暗下去，看不见。不出现任何人。
  pulses    C_10a          energy / EEVEE：左边三个高对比线框轮廓，轮廓上的点稀疏地闪，化成光脉冲飞向右边的视网膜剖面，
                           落下处的神经节细胞闪一下。始终是轮廓和点，不溶成照片。
  announce  C_13a          documentary / Cycles：暗桌上一页风格化公告，标题区只有拉丁字「GS030」「PIONEER」和日期
                           2026-10-08，其余是不可读的抽象行；不复刻任何杂志或公司页面版式。
  cochlea   C_17a          xray / EEVEE：半个耳蜗剖面（build_cochlea），一根示意光学阵列沿鼓阶亮起，随即淡出。不标编号、不画产品。
  desens    C_18a          energy / EEVEE：膜上一个通道视紫红质二（build_opsin），蓝光持续照着：孔先开到最大、随后收到一半
                           （脱敏，示意）；穿孔的阳离子先密后疏；旁边的电流示意曲线从峰落到平台。不带刻度和数值。
  split     C_19a          photoreal / Cycles：一个画面左右两半，中间暗隔板。左：组织块上的光纤，蓝光只在尖端。
                           右：桌上的护目镜后面浮着高对比线框（画法，artistic）；护目镜被拿开，线框随即消失。

依据见各 builder 文件头（build_retina、build_cochlea、build_brain、build_props、build_opsin、build_bilayer）。
线框画法（C_08b、C_09a、C_10a、C_19a 的高对比线框 / 白物暗底）只是画面语言（artistic），不是 Sahel 2021 的论文图，
也不是患者所见：论文写的是护目镜侦测亮度变化、投成光脉冲；测试物体有 40%、55%、100% 三档对比度（F11 notes、audit_C C_10a）。
全部示意（核查表记 simplified / artistic）；没有人物、没有血、没有未核实数字。颜色：蓝 = 通道 / 打开，琥珀 = 惊吓标记 / 关；
「环境甲」= 膜青色块，「环境乙」= 玫红色块（只是两种环境的区分色，不代表真实房间）。
"""
import math
import random

import bpy
from mathutils import Vector

import build_bilayer as BB
import build_brain as BRN
import build_cochlea as BC
import build_opsin as BO
import build_props as P
import build_retina as BR
import common as C
import e2_common as E
import e2_shot as S
import styles

ENV_A = E.MEMBRANE               # 环境甲：膜青
ENV_B = (236, 120, 160)          # 环境乙：玫红（只用来区分两个环境）
BLUE = S.lin(E.CHANNEL)
AMBER_L = S.lin(E.AMBER)
WHITE = (0.85, 0.9, 1.0)


def _n(sid):
    return S.shot_frames(sid)


def _f(sid, frac):
    """镜头内比例 → 帧号（1 起）。"""
    return 1 + round(frac * (_n(sid) - 1))


def _anchor(name, loc):
    a = S.link(bpy.data.objects.new(name, None))
    a.location = loc
    return a


def _tagged(ob, role):
    styles.tag(ob, role)
    return ob


def _keep_area(name, loc, aim, size, energy, color=(1.0, 0.97, 0.92)):
    return S.area(name, loc, aim, size, energy, color, keep=True)


# ---- brain：C_01a --------------------------------------------------------------------------
def brain(sc, rnd, **_):
    import bmesh
    sid = "C_01a"
    n = _n(sid)
    scale = 3.0
    b = BRN.mouse_brain("Brain", (0, 0, 0), scale, None, tag=styles.tag)
    # 暗着的细胞点：在皮层和海马的椭球里随机撒（一个网格）
    bm = bmesh.new()
    pts = []
    for nm, c, ax in BRN.parts():
        if not nm.startswith(("cortex", "hippocampus", "hypothalamus")):
            continue
        for _ in range(70 if nm.startswith("cortex") else 25):
            while True:
                u = [rnd.uniform(-1, 1) for _ in range(3)]
                if sum(v * v for v in u) < 0.8:
                    break
            p = BRN.world((0, 0, 0), scale, tuple(c[i] + u[i] * ax[i] for i in range(3)))
            pts.append(p)
            m = bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.014)
            for v in m["verts"]:
                v.co += Vector(p)
    me = bpy.data.meshes.new("DimCells")
    bm.to_mesh(me)
    bm.free()
    dim = S.link(bpy.data.objects.new("DimCells", me))
    _tagged(dim, "structure")
    # 被光标出的一小簇：齿状回附近 10 个
    dg = b["regions"]["dentate_gyrus"]
    lit_f = _f(sid, 0.22)
    for i in range(10):
        p = (dg[0] + rnd.uniform(-0.07, 0.07), dg[1] + rnd.uniform(-0.05, 0.05), dg[2] + rnd.uniform(-0.04, 0.04))
        core_m = S.glow(f"ClusterCore{i}Mat", BLUE, 0.0)
        S.sphere(f"ClusterCore{i}", 0.017, p, core_m, "emitter", seg=12, rings=8)
        hm = S.halo(f"ClusterHalo{i}Mat", BLUE)
        S.sphere(f"ClusterHalo{i}", 0.07, p, hm, "emitter", seg=16, rings=10)
        f0 = lit_f + rnd.randint(0, 10)
        S.set_strength(core_m, f0 - 1, 0.0)
        S.set_strength(core_m, f0 + 8, 9.0)
        S.set_gain(hm, f0 - 1, 0.0)
        S.set_gain(hm, f0 + 10, 2.2)
        S.set_gain(hm, n, 1.6)
    _anchor("LabelAnchor_Mouse", (0.75, 0.0, 0.75))
    S.dolly("CamC_01a", (-0.1, 0.1, 0.0), (-0.5, -4.6, 1.9), S.toward((-0.5, -4.6, 1.9), (-0.1, 0.1, 0.0), 0.22),
            1, n, lens=50)


# ---- slice：C_02a / C_05b -----------------------------------------------------------------
def slice_(sc, rnd, phase="tag", **_):
    hs = BRN.hippocampus_slice("Slice", (0, 0, 0), 4.0, n_cells=40, seed=4, tag=styles.tag)
    env_m = S.glow("EnvAMat", S.lin(ENV_A), 1.4)
    tile = S.box("EnvA", (2.55, 0.0, 0.03), (0.9, 0.9, 0.06), env_m, "emitter", bevel=0.02)
    lit = [i for i in range(40) if i % 3 == 0]                      # 一批：约三分之一
    pos = hs["dg_cell_positions"]
    sid = "C_02a" if phase == "tag" else "C_05b"
    n = _n(sid)
    f_lit = _f(sid, 0.18) if phase == "tag" else 1
    f_chan = _f(sid, 0.62) if phase == "tag" else 1
    chan_m = S.glow("ChannelDotMat", BLUE, 5.0)
    for k, i in enumerate(lit):
        p = pos[i]
        hm = S.halo(f"DGLit{i}Mat", S.lin(ENV_A))
        S.sphere(f"DGLit{i}", 0.08, p, hm, "emitter", seg=16, rings=10)
        if phase == "tag":
            f0 = f_lit + 2 * k
            S.set_gain(hm, f0 - 1, 0.0)
            S.set_gain(hm, f0 + 10, 2.4)
        else:
            S.set_gain(hm, 1, 2.4)
        dot = S.sphere(f"Chan{i}", 0.014, (p[0] + 0.03, p[1] - 0.02, p[2] + 0.02), chan_m, "emitter", seg=12, rings=8)
        if phase == "tag":
            f1 = f_chan + 2 * k
            S.key(dot, 1, scale=(0.001,) * 3)
            S.key(dot, f1, scale=(0.001,) * 3)
            S.key(dot, f1 + 8, scale=(1.0,) * 3)
    if phase == "link":
        cx = sum(pos[i][0] for i in lit) / len(lit)
        cy = sum(pos[i][1] for i in lit) / len(lit)
        line_m = S.glow("LinkMat", S.lin(ENV_A), 4.0)
        ln = S.tube("LinkLine", [(cx, cy, 0.14), ((cx + 2.55) / 2, cy * 0.5, 0.42), (2.2, 0.0, 0.14)], 0.012, line_m, "emitter")
        S.reveal(ln, 3, 24)
    S.studio_lights(0.55, (1.0, 0, 0))
    S.dolly("CamC_02a", (0.55, 0.0, 0.0), (-0.6, -4.6, 3.2), (0.2, -3.7, 2.4), 1, _n("C_02a"), lens=50,
            aim1=(0.6, 0.0, 0.0))
    S.locked("CamC_05b", (1.05, 0.0, 0.0), (1.05, -4.6, 3.6), lens=35)


# ---- cage：C_02b / C_03a / C_04a ----------------------------------------------------------
def cage(sc, rnd, env="A", mouse="none", **_):
    S.dark_room()
    P.bench("Bench", (1.8, 1.0), 0.0, tag=styles.tag, color=(0.09, 0.09, 0.1))
    tint = tuple(0.12 + 0.55 * c for c in S.lin(ENV_A if env == "A" else ENV_B))
    cg = P.cage("Cage", (0, 0, 0), (0.42, 0.26, 0.22), shock_marks=(env == "B"), floor_tint=tint, tag=styles.tag)
    wall = S.box("Backdrop", (0, 0.9, 0.6), (3.0, 0.02, 1.4), S.matte("BackdropMat", (0.02, 0.022, 0.026), 0.9), "env")
    _keep_area("Key", (-0.5, -0.5, 0.9), (0, 0, 0.05), 0.8, 60)
    _keep_area("Rim", (0.6, 0.6, 0.5), (0, 0, 0.08), 0.6, 25, color=(0.8, 0.88, 1.0))
    if mouse == "freeze":
        sid = "C_04a"
        n = _n(sid)
        m = P.mouse("Mouse", (-0.12, -0.04, 0.008), 0.3, 1.0, tag=styles.tag)
        P.mouse_walk(m, 1, _f(sid, 0.42), [(-0.12, -0.04, 0.008), (-0.05, -0.01, 0.008), (0.03, 0.02, 0.008)])
        P.mouse_freeze(m, _f(sid, 0.5), hold=n)
        S.dolly("CamC_04a", (0.0, 0.0, 0.07), (0.25, -0.85, 0.42), S.toward((0.25, -0.85, 0.42), (0, 0, 0.07), 0.3), 1, n, lens=50)
    elif mouse == "fiber":
        sid = "C_03a"
        n = _n(sid)
        m = P.mouse("Mouse", (-0.06, 0.0, 0.008), -0.4, 1.0, tag=styles.tag)
        P.mouse_walk(m, 1, _f(sid, 0.3), [(-0.06, 0.0, 0.008), (0.0, -0.03, 0.008), (0.05, -0.02, 0.008)])
        bpy.context.view_layer.update()
        hr = m.get("head_root") or m["head"]
        hp = hr.matrix_world.translation
        fb = P.fiber_implant("Fiber", (hp.x, hp.y, hp.z + 0.004), (0, 0, -1), cable_len=0.3, tag=styles.tag)
        fb["root"].parent = hr
        fb["root"].matrix_parent_inverse = hr.matrix_world.inverted()
        # 电击（乙的地面标记闪）和光（尖端蓝光脉冲）同时进行
        f_on, f_off = _f(sid, 0.42), _f(sid, 0.9)
        mm = bpy.data.materials.get("CageMarkMat")
        f = f_on
        while f < f_off:
            S.set_gain(fb["tip_glow_mat"], f - 1, 0.0)
            S.set_gain(fb["tip_glow_mat"], f + 1, 4.0)
            S.set_gain(fb["tip_glow_mat"], f + 4, 0.0)
            f += 6
        if mm is not None:
            for k, fm in enumerate((f_on, f_on + 40, f_on + 80)):
                S.set_strength(mm, fm - 1, 1.2)
                S.set_strength(mm, fm + 3, 5.0)
                S.set_strength(mm, fm + 14, 1.2)
        S.dolly("CamC_03a", (0.0, 0.0, 0.07), (-0.3, -0.85, 0.45), S.toward((-0.3, -0.85, 0.45), (0, 0, 0.07), 0.3), 1, n,
                lens=50)
    else:
        S.locked("CamC_02b", (0.0, 0.0, 0.08), (0.05, -0.78, 0.34), lens=35)


# ---- cells：C_03b --------------------------------------------------------------------------
def cells(sc, rnd, **_):
    sid = "C_03b"
    n = _n(sid)
    cl = S.neuron_cluster("Cell", 7, (0, 0, 0), 1.7, seed=31, scale=0.62)
    floor_m = S.glow("EnvBFloorMat", S.lin(ENV_B), 0.12)
    S.cylinder("EnvBFloor", 2.6, 0.01, (0, 0.6, -1.6), floor_m, "emitter", verts=64)
    tag_m = S.glow("EnvATagMat", S.lin(ENV_A), 4.0)
    tagged = (1, 3, 4, 6)
    dot_m = S.glow("SomaDotMat", (0.35, 0.4, 0.5), 0.8)          # 每个细胞一个暗暗的胞体点：能量图里细胞先看得见
    for i, (cell, root) in enumerate(cl):
        d = S.sphere(f"SomaDot{i}", 0.21, (0, 0, 0), dot_m, "emitter", seg=16, rings=10)
        d.parent = root
    for i in tagged:
        cell, root = cl[i]
        bpy.ops.mesh.primitive_torus_add(major_radius=0.32, minor_radius=0.018, location=(0, 0, 0))
        ring = bpy.context.object
        ring.name = f"TagRing{i}"
        ring.parent = root
        ring.rotation_euler = (math.pi / 2, 0, 0)
        ring.data.materials.append(tag_m)
        _tagged(ring, "emitter")
        S.soma_glow(f"Cell{i}", cell, root, BLUE, [(1, 0.0), (8, 0.0), (13, 3.0), (n, 1.8)])
    beam, bm = S.cone_beam("BlueBeam", (-1.8, 1.2, 3.6), (0.2, 0.0, -0.2), 1.5, BLUE, 0.0)
    S.set_gain(bm, 3, 0.0)
    S.set_gain(bm, 8, 1.2)
    S.locked("CamC_03b", (0.0, 0.0, -0.2), (0.0, -7.0, 0.5), lens=35)


# ---- retina：C_07a / C_07b / C_09b --------------------------------------------------------
def _retina_mats():
    """各层不同的哑光色（xray 保留原材质；clay / sem / energy 会统一替换）：感光暖、内核层灰蓝、神经节细胞蓝、色素上皮深。"""
    return {"default": S.matte("RetTissue", (0.72, 0.7, 0.68)),
            "plexiform": S.matte("RetPlexiform", (0.8, 0.8, 0.82)),
            "rpe": S.matte("RetRPE", (0.16, 0.12, 0.11)),
            "pr": S.matte("RetPR", (0.86, 0.6, 0.38)),
            "inl": S.matte("RetINL", (0.5, 0.56, 0.62)),
            "rgc": S.matte("RetRGC", (0.22, 0.36, 0.78)),
            "ilm": S.matte("RetILM", (0.6, 0.62, 0.66))}


def retina(sc, rnd, phase="rp", **_):
    tissue = _retina_mats()
    if phase == "rp":
        sid = "C_07a"
        n = _n(sid)
        r = BR.build_retina("Ret", 6.0, 1.0, photoreceptor_density=0.25, dying_groups=4, n_ganglion=16, mat=tissue,
                            glow_color=BLUE, tag=styles.tag)
        BR.fade_dying(r, _f(sid, 0.1), _f(sid, 0.45))
        BR.ganglion_glow(r, [(1, 0.0), (_f(sid, 0.62), 0.0), (_f(sid, 0.72), 1.4)])
        _anchor("LabelAnchor_Transducible", (2.3, -0.5, BR.layer_z("GCL")))
        S.dolly("CamC_07a", (0.0, 0.0, 1.22), (-0.3, -9.4, 1.9), (0.6, -6.6, 1.4), 1, n, lens=50, aim1=(0.4, 0.0, 1.05))
    elif phase == "sem":
        BR.build_retina("Ret", 6.0, 1.0, photoreceptor_density=0.25, dying_groups=0, n_ganglion=16, mat=tissue,
                        glow_color=BLUE, tag=styles.tag)
        S.locked("CamC_07b", (0.2, 0.0, 1.2), (0.9, -5.2, 3.4), lens=50)
    else:
        sid = "C_09b"
        r = BR.build_retina("Ret", 6.0, 1.0, photoreceptor_density=0.25, dying_groups=0, n_ganglion=16, mat=tissue,
                            glow_color=BLUE, tag=styles.tag)
        BR.ganglion_pulses(r, 2, 12, 4, peak=3.0, frac=0.6)
        BR.ganglion_glow(r, [(14, 0.0), (_n(sid), 0.0)])
        S.locked("CamC_09b", (0.0, 0.0, 0.9), (0.0, -6.4, 1.6), lens=35)
    S.studio_lights(0.5, (0, 0, 1.3))


# ---- eye：C_08a ----------------------------------------------------------------------------
def eye(sc, rnd, **_):
    sid = "C_08a"
    n = _n(sid)
    tissue = S.matte("EyeTissue", (0.8, 0.76, 0.74))
    e = BR.eyeball_section("Eye", (0, 0, 0), tissue, BLUE, tag=styles.tag)
    outer, entry, tip = BR.injection_path(e)
    # 注射针：建在最终位置，挂在空物体上，空物体从后退位置推进再退出
    needle_root = S.link(bpy.data.objects.new("NeedleRoot", None))
    steel = S.matte("NeedleSteel", (0.7, 0.72, 0.75), 0.25)
    shaft = S.between("Needle", outer, tip, 0.018, steel, "structure")
    shaft.parent = needle_root
    back = Vector(outer) - Vector(tip)
    back = back.normalized() * 0.7
    f_in0, f_in1, f_out0, f_out1 = _f(sid, 0.1), _f(sid, 0.2), _f(sid, 0.32), _f(sid, 0.38)
    S.key(needle_root, 1, location=tuple(back))
    S.key(needle_root, f_in0, location=tuple(back))
    S.key(needle_root, f_in1, location=(0, 0, 0))
    S.key(needle_root, f_out0, location=(0, 0, 0))
    S.key(needle_root, f_out1, location=tuple(back * 2.0))
    S.show_between(shaft, 1, f_out1 + 1)
    # 注入的液团：针尖处的一团光晕，慢慢变大变淡（病毒载体，示意）
    bm = S.halo("BolusMat", (0.75, 0.9, 1.0))
    bol = S.sphere("Bolus", 0.25, tip, bm, "emitter", seg=20, rings=12)
    S.key(bol, f_in1, scale=(0.2,) * 3)
    S.key(bol, f_out1 + 30, scale=(1.6,) * 3)
    S.set_gain(bm, f_in1, 0.0)
    S.set_gain(bm, f_in1 + 8, 2.0)
    S.set_gain(bm, f_out1 + 40, 0.0)
    # 神经节细胞获得新通道：视网膜内层带淡淡亮起
    S.set_strength(e["rgc_mat"], 1, 0.0)
    S.set_strength(e["rgc_mat"], _f(sid, 0.4), 0.0)
    S.set_strength(e["rgc_mat"], _f(sid, 0.5), 1.2)
    # 护目镜（示意道具）在眼前，镜片朝眼睛（+X）
    g = P.goggles("Goggles", (-2.9, 0.15, 0.0), (0, 0, math.pi / 2), 5.0, tag=styles.tag, lens_color=BLUE)
    f_g = _f(sid, 0.55)
    for o in [g["root"]] + g["lenses"] + g["frame"] + [g["strap"]]:
        S.show_between(o, f_g)
    # 光脉冲：从镜片出发，穿过瞳孔，落到视网膜后壁；落下时神经节细胞带闪一下
    bead_m = S.glow("PulseBeadMat", BLUE, 12.0)
    f = _f(sid, 0.62)
    k = 0
    R = e["R"]
    while f + 14 < n:
        th = math.radians(rnd.uniform(-35, 35))
        dst = (R * 0.86 * math.cos(th), 0.05, R * 0.86 * math.sin(th))
        b = S.sphere(f"Pulse{k}", 0.045, (-2.75, 0.05, 0.0), bead_m, "emitter", seg=12, rings=8)
        S.key(b, f, location=(-2.75, 0.05, rnd.uniform(-0.08, 0.08)))
        S.key(b, f + 6, location=(-1.0, 0.05, 0.0))
        S.key(b, f + 14, location=dst)
        S.linear(b)
        S.show_between(b, f, f + 15)
        S.set_strength(e["rgc_mat"], f + 13, 1.2)
        S.set_strength(e["rgc_mat"], f + 15, 4.0)
        S.set_strength(e["rgc_mat"], f + 22, 1.2)
        f += 14
        k += 1
    S.studio_lights(0.6, (-0.8, 0, 0))
    S.dolly("CamC_08a", (-0.8, 0.0, 0.0), (-0.8, -8.6, 0.8), (-0.5, -7.2, 0.5), 1, n, lens=50, aim1=(-0.5, 0.0, 0.0))


# ---- goggles：C_08b / C_92 ----------------------------------------------------------------
def _outline_shapes(prefix, center, size, mat, parent=None, normal="Y"):
    """高对比线框轮廓（画法，artistic，不是患者所见）：一个方框、一个圆、一个三角（白色发光细管），排在 center 附近的 x-z 平面。返回 [(名字, 点列)]。"""
    cx, cy, cz = center
    s = size
    shapes = {
        "Box": [(-s, 0, -s), (s, 0, -s), (s, 0, s), (-s, 0, s), (-s, 0, -s)],
        "Ring": [(s * math.cos(a), 0, s * math.sin(a)) for a in [2 * math.pi * k / 32 for k in range(33)]],
        "Tri": [(-s, 0, -s * 0.8), (s, 0, -s * 0.8), (0, 0, s), (-s, 0, -s * 0.8)],
    }
    offs = {"Box": (-2.6 * s, 0, 0), "Ring": (0, 0, 0.2 * s), "Tri": (2.6 * s, 0, -0.1 * s)}
    out = []
    for nm, pts in shapes.items():
        o = offs[nm]
        wp = [(cx + o[0] + p[0], cy + p[1], cz + o[2] + p[2]) for p in pts]
        ob = S.tube(f"{prefix}{nm}", wp, s * 0.06, mat, "emitter", res=1)
        if parent is not None:
            ob.parent = parent
        out.append((ob, wp))
    return out


def goggles(sc, rnd, display="outline", **_):
    S.dark_room()
    P.bench("Table", (1.4, 0.9), 0.0, tag=styles.tag, color=(0.07, 0.07, 0.075))
    g = P.goggles("Goggles", (0.0, 0.0, 0.026), (0, 0, 0.22), 1.0, tag=styles.tag)
    if display == "outline":
        line_m = S.glow("LensOutlineMat", WHITE, 6.0)
        for i, lens in enumerate(g["lenses"]):
            x = (-1, 1)[i] * 0.038
            for ob, _ in _outline_shapes(f"Lens{i}Outline", (x, -0.0045, 0.0), 0.0045, line_m):
                ob.parent = g["root"]
        for m in g["lens_mats"]:
            S.set_strength(m, 1, 0.02)
    else:
        for m in g["lens_mats"]:
            S.set_strength(m, 1, 0.0)
    _keep_area("Key", (-0.35, -0.4, 0.5), (0, 0, 0.02), 0.35, 14)
    _keep_area("Rim", (0.4, 0.35, 0.25), (0, 0, 0.03), 0.3, 8, color=(0.8, 0.88, 1.0))
    S.locked("CamC_08b", (0.0, 0.0, 0.026), (0.06, -0.3, 0.1), lens=50)
    S.locked("CamC_92", (0.0, 0.0, 0.02), (-0.28, -0.42, 0.24), lens=50)


# ---- objects：C_09a ------------------------------------------------------------------------
def _goggle_mask(name, cam, dist=0.03):
    """第一人称护目镜框：相机前 dist 处一块黑板，挖出两个椭圆镜孔（挂在相机上）。"""
    import bmesh
    bm = bmesh.new()
    W, H, nx, ny = 0.06, 0.04, 90, 60
    holes = ((-0.0078, 0.0, 0.0071, 0.0062), (0.0078, 0.0, 0.0071, 0.0062))
    grid = [[bm.verts.new((-W / 2 + W * i / nx, -H / 2 + H * j / ny, -dist)) for j in range(ny + 1)] for i in range(nx + 1)]
    for i in range(nx):
        for j in range(ny):
            cx = -W / 2 + W * (i + 0.5) / nx
            cy = -H / 2 + H * (j + 0.5) / ny
            if any(((cx - hx) / rx) ** 2 + ((cy - hy) / ry) ** 2 < 1 for hx, hy, rx, ry in holes):
                continue
            bm.faces.new((grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1]))
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = S.link(bpy.data.objects.new(name, me))
    ob.data.materials.append(S.matte(name + "Mat", (0.004, 0.004, 0.005), 0.9))
    ob.parent = cam
    _tagged(ob, "structure")
    return ob


def objects(sc, rnd, **_):
    sid = "C_09a"
    n = _n(sid)
    S.dark_room(top=(0.0, 0.0, 0.0))
    P.bench("Table", (1.4, 0.9), 0.0, tag=styles.tag, color=(0.012, 0.012, 0.013))
    white = S.matte("ObjWhite", (0.9, 0.9, 0.88), 0.5)
    S.box("ObjCube", (-0.14, 0.05, 0.03), (0.06, 0.06, 0.06), white, "structure", bevel=0.003)
    S.cylinder("ObjCyl", 0.028, 0.09, (0.02, 0.12, 0.045), white, "structure", verts=48)
    S.sphere("ObjBall", 0.032, (0.15, 0.0, 0.032), white, "structure", seg=32, rings=16)
    f_off0, f_off1 = _f(sid, 0.68), _f(sid, 0.82)
    sp = S.spot("Spot", (0.0, -0.1, 0.9), (0.0, 0.05, 0.0), 30.0, angle_deg=40, blend=0.5)
    sp.data.keyframe_insert("energy", frame=1)
    sp.data.keyframe_insert("energy", frame=f_off0)
    sp.data.energy = 0.0
    sp.data.keyframe_insert("energy", frame=f_off1)
    cam = S.dolly("CamC_09a", (0.0, 0.05, 0.02), (0.0, -0.55, 0.32), (0.0, -0.47, 0.28), 1, n, lens=35)
    mask = _goggle_mask("GoggleMask", cam)
    S.show_between(mask, 1, f_off0 + 4)                       # 护目镜摘下：框先消失，物体随后暗下去


# ---- pulses：C_10a -------------------------------------------------------------------------
def pulses(sc, rnd, **_):
    sid = "C_10a"
    n = _n(sid)
    line_m = S.glow("OutlineMat", WHITE, 5.0)
    shapes = _outline_shapes("Outline", (-2.6, 0.0, 0.0), 0.32, line_m)
    for k, (ob, _) in enumerate(shapes):
        S.reveal(ob, 1 + 8 * k, 30 + 8 * k)
    # 轮廓上的取样点（稀疏）
    dots = []
    for ob, wp in shapes:
        for i in range(0, len(wp) - 1, max(1, len(wp) // 8)):
            dm = S.glow(f"Dot{len(dots)}Mat", BLUE, 0.0)
            d = S.sphere(f"Dot{len(dots)}", 0.035, wp[i], dm, "emitter", seg=12, rings=8)
            dots.append((d, dm, wp[i]))
    r = BR.build_retina("Ret", 3.0, 0.6, photoreceptor_density=0.25, dying_groups=0, n_ganglion=10, glow_color=BLUE,
                        mat=_retina_mats(),
                        tag=styles.tag)
    r["root"].location = (1.05, 0.0, 0.0)
    r["root"].rotation_euler = (0, math.pi / 2, 0)              # 内界膜（神经节细胞一侧）朝 -X，迎着脉冲
    r["root"].scale = (0.55,) * 3                               # 厚 2.6 × 0.55 ≈ 1.4，整段在画面右侧
    bpy.context.view_layer.update()
    targets = [(r["root"].matrix_world @ Vector((g["x"], g["y"], g["z"]))) for g in r["ganglia"]]
    for g in r["ganglia"]:
        S.set_gain(g["halo_mat"], 1, 0.0)
    pool = [S.sphere(f"Bead{k}", 0.03, (0, 0, 0), S.glow("BeadMat", BLUE, 10.0) if k == 0 else bpy.data.materials["BeadMat"],
                     "emitter", seg=12, rings=8) for k in range(40)]
    for b in pool:
        S.key(b, 1, hide_render=True)
    f = _f(sid, 0.15)
    c = 0
    period = 12
    while f + 14 < n:
        chosen = rnd.sample(range(len(dots)), max(3, len(dots) // 4))
        for j, di in enumerate(chosen):
            d, dm, p = dots[di]
            S.set_strength(dm, f - 1, 0.0)
            S.set_strength(dm, f + 1, 8.0)
            S.set_strength(dm, f + 5, 0.0)
            gi = rnd.randrange(len(targets))
            b = pool[(c * 8 + j) % len(pool)]
            S.key(b, f, location=p, hide_render=False)
            S.key(b, f + 10, location=tuple(targets[gi]))
            S.key(b, f + 11, hide_render=True)
            hm = r["ganglia"][gi]["halo_mat"]
            S.set_gain(hm, f + 9, 0.0)
            S.set_gain(hm, f + 11, 3.0)
            S.set_gain(hm, f + 19, 0.0)
        f += period
        c += 1
    S.dolly("CamC_10a", (-0.3, 0.0, 0.0), (-0.3, -9.2, 0.4), (-0.2, -8.0, 0.25), 1, n, lens=50)


# ---- announce：C_13a -----------------------------------------------------------------------
def _text(name, body, loc, size, mat, rot=(0, 0, 0)):
    cu = bpy.data.curves.new(name, "FONT")
    cu.body = body
    cu.size = size
    cu.extrude = 0.00002
    ob = S.link(bpy.data.objects.new(name, cu))
    ob.location = loc
    ob.rotation_euler = rot
    ob.data.materials.append(mat)
    _tagged(ob, "structure")
    return ob


def announce(sc, rnd, **_):
    import bmesh
    sid = "C_13a"
    n = _n(sid)
    S.dark_room()
    P.bench("Desk", (1.2, 0.8), 0.0, tag=styles.tag, color=(0.05, 0.045, 0.04))
    paper = S.box("Page", (0.0, 0.0, 0.0003), (0.21, 0.297, 0.0006), S.matte("PageMat", (0.82, 0.82, 0.8), 0.85), "structure")
    paper.rotation_euler = (0, 0, math.radians(-3))
    ink = S.matte("InkMat", (0.03, 0.035, 0.05), 0.6)
    rot = (0, 0, math.radians(-3))
    _text("TitleGS030", "GS030", (-0.085, 0.095, 0.0007), 0.026, ink, rot)
    _text("TitlePIONEER", "PIONEER", (-0.085, 0.064, 0.0007), 0.018, ink, rot)
    _text("TitleDate", "2026-10-08", (-0.085, 0.125, 0.0007), 0.008, ink, rot)
    # 不可读的抽象行：细长的灰条，长短随机（一个网格），不排任何字
    bm = bmesh.new()
    c, s_ = math.cos(rot[2]), math.sin(rot[2])
    y = 0.035
    while y > -0.13:
        x0 = -0.085
        L = 0.17 * rnd.uniform(0.55, 1.0) if rnd.random() > 0.12 else 0.0
        while L > 0:
            w = min(L, rnd.uniform(0.008, 0.03))
            for (a, b) in (((x0, y), (x0 + w, y)),):
                cx, cy = (a[0] + b[0]) / 2, a[1]
                m = bmesh.ops.create_cube(bm, size=1.0)
                for v in m["verts"]:
                    vx, vy, vz = v.co.x * w, v.co.y * 0.0022, v.co.z * 0.00005
                    px, py = cx + vx, cy + vy
                    v.co = (px * c - py * s_, px * s_ + py * c, 0.00066 + vz)
            x0 += w + 0.003
            L -= w + 0.003
        y -= 0.0085
    me = bpy.data.meshes.new("PageLines")
    bm.to_mesh(me)
    bm.free()
    lines = S.link(bpy.data.objects.new("PageLines", me))
    lines.data.materials.append(S.matte("LineInkMat", (0.18, 0.18, 0.2), 0.7))
    _tagged(lines, "structure")
    _keep_area("Rake", (-0.5, 0.15, 0.12), (0.0, 0.0, 0.0), 0.12, 8)
    _keep_area("Fill", (0.3, -0.4, 0.5), (0.0, 0.0, 0.0), 0.5, 2.5, color=(0.8, 0.86, 1.0))
    S.dolly("CamC_13a", (-0.02, 0.06, 0.0), (0.05, -0.36, 0.34), S.toward((0.05, -0.36, 0.34), (-0.02, 0.06, 0.0), 0.3),
            1, n, lens=50, aim1=(-0.04, 0.085, 0.0))


# ---- cochlea：C_17a ------------------------------------------------------------------------
def cochlea(sc, rnd, **_):
    sid = "C_17a"
    n = _n(sid)
    co = BC.build_cochlea("Co", (0, 0, 0), S.matte("CochleaTissue", (0.82, 0.78, 0.74)), BLUE, tag=styles.tag)
    f_r0, f_r1 = _f(sid, 0.09), _f(sid, 0.27)
    arrays = co["arrays"]
    lens_ = [len(o.data.splines[0].points) for o in arrays]          # 点距相等，点数 ∝ 弧长
    tot = sum(lens_) or 1
    acc = 0
    for o, L in zip(arrays, lens_):
        a = f_r0 + round((f_r1 - f_r0) * acc / tot)
        acc += L
        b = f_r0 + round((f_r1 - f_r0) * acc / tot)
        S.reveal(o, a, max(a + 1, b))
    m = co["array_mat"]
    S.set_strength(m, f_r0 - 1, 0.0)
    S.set_strength(m, f_r0 + 6, 6.0)
    S.set_strength(m, _f(sid, 0.45), 6.0)
    S.set_strength(m, _f(sid, 0.65), 0.0)                       # 随即淡出
    S.studio_lights(1.2, (0, 0, 2.0))
    S.dolly("CamC_17a", (0.0, 0.0, 2.0), (0.0, -15.5, 5.2), (0.0, -12.5, 4.0), 1, n, lens=50)


# ---- desens：C_18a -------------------------------------------------------------------------
def desens(sc, rnd, **_):
    sid = "C_18a"
    n = _n(sid)
    px, py = BO.pore_center()
    bl = BB.build_bilayer("Bilayer", 170.0, 100.0, holes=[(0.0, 0.0, 24.0)])
    for k in ("heads", "tails"):
        _tagged(bl[k], "structure")
    _tagged(bl["core"], "shell")
    p = BO.build_opsin("ChR2", "channel", (0, 0, 0), pore_color=BLUE, tag=styles.tag)
    on = 0.12
    amt = lambda u: S.peak_plateau(u, on=on, off=2.0, peak=1.0, plateau=0.45)   # noqa: E731
    for f in range(1, n + 1, 3):
        a = amt((f - 1) / (n - 1))
        BO.set_open(p, f, a, glow=6.0 * a)
    beam, bm = S.cone_beam("BlueLight", (-0.6, 1.0, 1.9), (0.0, 0.0, 0.26), 0.24, BLUE, 0.0)   # 从后上方来，不挡蛋白
    f_on = _f(sid, on)
    S.set_gain(bm, f_on - 2, 0.0)
    S.set_gain(bm, f_on + 2, 1.2)
    # 穿孔的阳离子：按电流示意曲线积分，先密后疏
    path = BO.pore_path(p)
    acc, k = 0.0, 0
    for f in range(f_on, n - 16):
        acc += amt((f - 1) / (n - 1)) * 0.22
        if acc >= 1.0:
            acc -= 1.0
            start = (path[0][0] + rnd.uniform(-0.25, 0.25), path[0][1] + rnd.uniform(-0.2, 0.2), rnd.uniform(0.5, 0.8))
            ion = BB.ion(f"Na{k}", "cation", start)
            BB.jitter(ion, 1, f - 2, 0.02, seed=k)
            BB.through(ion, [start] + path[1:], f, f + 16)
            k += 1
    for i, ion in enumerate(BB.cloud("Bulk", "cation", 10, (-0.2, 0.35, 0.55), (0.6, 0.3, 0.1), seed=5)):
        BB.jitter(ion, 1, n, 0.025, seed=100 + i)
    # 电流示意曲线：右上方，从左往右画，和孔的开合同一条时间轴（无刻度、无数值）
    tm = S.glow("TraceMat", BLUE, 5.0)
    ax = S.matte("TraceAxis", (0.5, 0.55, 0.6))
    ob, base, pts = S.trace("Current", amt, (0.38, -0.35, 0.36), (0.55, 0.5), tm, 1, n, axis_mat=ax)
    S.trace_head("CurrentHead", pts, 1, n, 0.012, tm)
    S.dolly("CamC_18a", (0.3, 0.0, 0.14), (0.25, -2.7, 0.5), (0.3, -2.25, 0.42), 1, n, lens=50)


# ---- split：C_19a --------------------------------------------------------------------------
def split(sc, rnd, **_):
    sid = "C_19a"
    n = _n(sid)
    S.dark_room()
    P.bench("Table", (1.6, 0.9), 0.0, tag=styles.tag, color=(0.06, 0.06, 0.065))
    S.box("Divider", (0.0, 0.05, 0.4), (0.012, 0.9, 0.8), S.matte("DividerMat", (0.004, 0.004, 0.005), 0.9), "structure")
    # 左：组织块（中性灰，不画血）+ 光纤，蓝光只在尖端
    S.box("Tissue", (-0.34, 0.02, 0.04), (0.24, 0.18, 0.08), S.matte("TissueMat", (0.42, 0.42, 0.46), 0.7),
          "structure", bevel=0.01)
    fb = P.fiber_implant("Fiber", (0.0, 0.0, 0.0), (0, 0, -1), cable_len=0.014, tag=styles.tag)
    fb["root"].location = (-0.34, 0.02, 0.083)
    fb["root"].scale = (22.0,) * 3
    S.set_gain(fb["tip_glow_mat"], 1, 0.0)
    S.set_gain(fb["tip_glow_mat"], 8, 3.5)
    S.set_gain(fb["beam_mat"], 1, 0.0)
    S.set_gain(fb["beam_mat"], 8, 1.2)
    # 右：护目镜 + 后面浮着的线框（画法，不是患者所见）；护目镜拿开，线框消失
    g = P.goggles("Goggles", (0.27, -0.12, 0.026), (0, 0, 0.0), 1.0, tag=styles.tag)
    line_m = S.glow("FloatOutlineMat", WHITE, 6.0)
    _outline_shapes("Float", (0.34, 0.12, 0.13), 0.028, line_m)
    f_lift0, f_lift1 = _f(sid, 0.55), _f(sid, 0.72)
    S.key(g["root"], 1, location=(0.27, -0.12, 0.026), rotation_euler=(0, 0, 0))
    S.key(g["root"], f_lift0, location=(0.27, -0.12, 0.026), rotation_euler=(0, 0, 0))
    S.key(g["root"], f_lift1, location=(0.5, -0.3, 0.32), rotation_euler=(0.5, 0, 0.6))
    S.set_strength(line_m, f_lift0 + 4, 6.0)
    S.set_strength(line_m, f_lift0 + 14, 0.0)
    _keep_area("KeyL", (-0.6, -0.5, 0.6), (-0.34, 0, 0.05), 0.4, 14)
    _keep_area("KeyR", (0.6, -0.5, 0.6), (0.34, 0, 0.05), 0.4, 14)
    S.dolly("CamC_19a", (0.0, 0.0, 0.07), (0.0, -1.3, 0.42), (0.0, -1.14, 0.37), 1, n, lens=50)


# ---- 风格后处理（一个模块一个 after_style）-------------------------------------------------------
def after_style(style, shot_id):
    sc = bpy.context.scene
    S.after_style_common(sc, style)
    v = sc.get("variant")
    if style == "energy" and v in ("desens", "cells"):
        # 能量图的通用暗边对细螺旋 / 细树突太淡：主角换一层更亮的边，背景的脂质头基更暗
        hero = styles.dark_rim("HeroRim", color=(0.5, 0.72, 1.0), strength=4.0)
        dim = styles.dark_rim("DimRim", strength=0.45)
        for o in bpy.data.objects:
            if o.type not in ("MESH", "CURVE") or styles.role_of(o) != "structure":
                continue
            m = hero if o.name.startswith(("ChR2_", "Cell")) else dim if o.name.startswith("BilayerHeads") else None
            if m is not None:
                o.data.materials.clear()
                o.data.materials.append(m)
    if v == "objects":
        sc["vignette"] = 0.55                       # 第一人称：暗角稍重


VARIANTS = {"brain": (brain, "C_01a"), "slice": (slice_, "C_02a"), "cage": (cage, "C_03a"), "cells": (cells, "C_03b"),
            "retina": (retina, "C_07a"), "eye": (eye, "C_08a"), "goggles": (goggles, "C_08b"), "objects": (objects, "C_09a"),
            "pulses": (pulses, "C_10a"), "announce": (announce, "C_13a"), "cochlea": (cochlea, "C_17a"),
            "desens": (desens, "C_18a"), "split": (split, "C_19a")}


def build(variant="brain", seed=7, **args):
    fn, longest = VARIANTS[variant]
    sc = C.reset_scene(max(48, _n(longest) + 2))
    sc["variant"] = variant
    sc["hdri_strength"] = 0.25                      # photoreal 镜头的反射环境（apply_style 读）
    rnd = random.Random(seed)
    fn(sc, rnd, **args)
    return sc
