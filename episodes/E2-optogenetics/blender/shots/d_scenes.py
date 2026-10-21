"""E2 D 段（结尾）的 Blender 镜头。一个模块，多个 variant；只有一个 after_style，内部按 variant 分支（WORKFLOW 9）。

  switch   D_01a  energy / EEVEE：A0_03b 同一排 9 个参数化神经元（同一套种子和排布，首尾呼应），只有被圈的那一类
                  （E.NEURON_CIRCLED）先被蓝光打开、沿轴突放电，再被琥珀光按住；两侧细胞始终暗。被选中的胞体上嵌着
                  缩小的参数化通道视紫红质（蓝，build_opsin channel）和氯泵（琥珀，cl_pump）：蓝光时通道孔亮，琥珀光时泵的
                  视黄醛亮、通道熄灭。慢推。
           D_01b  clay / EEVEE：同一场景，锁定近景只看中间那一个被选中的神经元：1.35 秒里先蓝后琥珀（单独时间表）。
  paper    D_03a  documentary / Cycles：直接复用 A0 的纸页场景（a0_scenes.paper，不改 A0 代码），掠射光和室内底光都比开场
                  稍亮（分镜：「光线比开场稍亮」）；新相机 CamD_03a 慢推，比 A0_01a 略高、略近。没有手、没有人脸。
  line     D_04b  energy / EEVEE：黑场中一条细光横线（与 A0_06b 的细光同一语汇），在前 0.6 秒内熄灭，之后全黑；不出现任何
                  下集标题。
  closing  D_92   sem / Cycles：膜里的一个参数化通道视紫红质（build_opsin + build_bilayer），从打开回到关闭：TM1/TM2/TM7 回到
                  原位、孔道收窄。sem 只显示结构（发光的孔道和光束在 sem 下隐藏），所以「光灭」由孔合上来读。

时间：D_01a 按 timed.yaml 的 cue（0.3–7.53 s）按字数估计「打开」≈ 2.6 s、「关掉」≈ 3.5 s。蓝光 1.0 s 起，琥珀光 3.5 s 起并保持到
结尾（蓝光仍在：表达的是按住而不是关灯）。P8 之前用 review_words.py 按词级时间戳再对一次。
几何依据见 build_neuron / build_opsin / build_bilayer 文件头；全部示意（simplified），没有人物。
"""
import math
import random

import bpy

import a0_scenes as A0
import build_bilayer as BB
import build_neuron as BN
import build_opsin as BO
import common as C
import e2_common as E
import e2_shot as S
import materials as M
import styles

FPS = 24
F_D01A = S.shot_frames("D_01a", 190)
F_D01B = S.shot_frames("D_01b", 32)
D01B_START = F_D01A + 40          # D_01b 在同一场景里另起一段时间表
FRAMES = D01B_START + F_D01B + 10


def _sec(t):
    return 1 + round(t * FPS)


# ---- switch：D_01a / D_01b --------------------------------------------------------------------
def _opsins_on_soma(prefix, cell_origin, kind, n, mat, color, rnd, scale=0.16):
    """在胞体表面嵌 n 个缩小的七次跨膜蛋白（channel 或 cl_pump），蛋白轴沿胞体法向。返回 build_opsin 的 dict 列表。"""
    out = []
    for k in range(n):
        az = rnd.uniform(0, 2 * math.pi)
        el = rnd.uniform(-0.2, 0.9)
        nrm = (math.cos(el) * math.cos(az), math.cos(el) * math.sin(az) * 0.6 - 0.4, math.sin(el))
        L = math.sqrt(sum(v * v for v in nrm))
        nrm = tuple(v / L for v in nrm)
        loc = tuple(cell_origin[i] + nrm[i] * BN.SOMA_R * 1.02 for i in range(3))
        p = BO.build_opsin(f"{prefix}{k}", kind=kind, loc=loc, mat=mat, pore_color=color, tag=styles.tag, seed=1 + k)
        p["root"].scale = (scale, scale, scale)
        from mathutils import Vector
        p["root"].rotation_euler = Vector(nrm).to_track_quat("Z", "Y").to_euler()
        p["center"] = Vector(loc)
        out.append(p)
    return out


def _pulse_beads(prefix, cell, mat, times):
    """沿轴突跑的放电亮点：times 是每个亮点出发的帧，走完轴突用 14 帧。"""
    from mathutils import Vector
    o = cell["origin"]
    path = [(o[0] + p[0], o[1] + p[1], o[2] + p[2]) for p in BN.axon_path(cell["morph"])]
    for j, f0 in enumerate(times):
        b = S.sphere(f"{prefix}Bead{j}", 0.05, path[0], mat, "emitter", seg=16, rings=10, scale=(1, 1, 2.2))
        b.rotation_mode = "QUATERNION"
        for f in range(f0, f0 + 15):
            p, t = BN.path_at(path, (f - f0) / 14)
            S.key(b, f, location=p, rotation_quaternion=Vector((0, 0, 1)).rotation_difference(Vector(t)))
        S.show_between(b, f0, f0 + 15)


def switch(sc, rnd):
    sc["variant"] = "switch"
    clay = styles.clay_material()
    blue, amber = S.lin(E.CHANNEL), S.lin(E.AMBER)
    n = E.NEURON_COUNT
    xs = [(i - (n - 1) / 2) * BN.SPACING for i in range(n)]
    ys = [random.Random(7).uniform(-0.18, 0.18) for _ in range(n)]
    bead_mat = M.emission("D01Bead", blue, 9.0)
    # 两段时间表：D_01a（1…F_D01A）和 D_01b（D01B_START…）
    tl = [
        {"blue": _sec(1.0), "amber": _sec(3.5), "end": F_D01A},
        {"blue": D01B_START + 1, "amber": D01B_START + 15, "end": D01B_START + F_D01B},
    ]
    for i in range(n):
        origin = (xs[i], ys[i], 0.0)
        cell = BN.build_neuron(f"D{i}", E.NEURON_SEEDS[i], origin, clay, tag=styles.tag)
        if i not in E.NEURON_CIRCLED:
            continue
        chans = _opsins_on_soma(f"D{i}ChR", origin, "channel", 3, clay, blue, rnd)
        pumps = _opsins_on_soma(f"D{i}NpHR", origin, "cl_pump", 3, clay, amber, rnd)
        hb = S.halo(f"D{i}BlueHaloMat", blue)
        ha = S.halo(f"D{i}AmberHaloMat", amber)
        for m_, r in ((hb, 0.30), (ha, 0.34)):
            h = S.sphere(f"{m_.name}Ob", r, origin, m_, "emitter", seg=24, rings=12)
        beads = []
        for t in tl:
            fb, fa, fe = t["blue"], t["amber"], t["end"]
            S.set_gain(hb, fb - 1, 0.0)
            S.set_gain(hb, fb + 6, 2.4)
            S.set_gain(hb, fa, 2.0)
            S.set_gain(hb, fa + 6, 0.0)                     # 被按住：蓝晕退掉
            S.set_gain(ha, fa - 1, 0.0)
            S.set_gain(ha, fa + 6, 1.8)
            S.set_gain(ha, fe, 1.4)
            S.set_gain(ha, fe + 4, 0.0)
            for p in chans:
                BO.set_open(p, fb - 1, 0.0, glow=0.0)
                BO.set_open(p, fb + 4, 1.0, glow=6.0)
                BO.set_open(p, fa + 2, 1.0, glow=6.0)      # 蓝光一直开着：通道还开，但胞体被氯泵按住，不放电
            for p in pumps:
                S.set_gain(p["retinal_glow_mat"], fa - 1, 0.0)
                S.set_gain(p["retinal_glow_mat"], fa + 4, 2.6)
                S.set_gain(p["retinal_glow_mat"], fe, 2.0)
            step = 9 if fa - fb > 30 else 5
            beads += list(range(fb + 4, fa - 6, step))      # 蓝光期间一串放电；琥珀光之后不再有
        _pulse_beads(f"D{i}", cell, bead_mat, beads)
    # 光：蓝束和琥珀束从上方斜照到被圈的那一类（只照它们）
    for nm, col, key_t in (("Blue", blue, "blue"), ("Amber", amber, "amber")):
        for i in E.NEURON_CIRCLED:
            tgt = (xs[i], ys[i], 0.0)
            apex = (xs[i] + (-0.6 if nm == "Blue" else 0.6), ys[i] + 0.4, 3.2)
            ob, m = S.cone_beam(f"D{nm}Beam{i}", apex, tgt, 0.26, col, 0.0)
            for t in tl:
                S.set_gain(m, t[key_t] - 1, 0.0)
                S.set_gain(m, t[key_t] + 4, 0.22)               # 光束只是示意：淡，不盖过细胞
                S.set_gain(m, t["end"], 0.22)
                S.set_gain(m, t["end"] + 3, 0.0)
    S.studio_lights(scale=1.0)
    # D_01a：50 mm 慢推，排在 A0_03b 的机位旁（首尾呼应），推到中间三格
    S.dolly("CamD_01a", (0, 0, -0.30), (0, -13.4, 0.4), (0, -10.6, 0.1), 1, F_D01A, lens=50)
    # D_01b：35 mm 锁定近景，只看中间那个被选中的神经元
    mid = E.NEURON_CIRCLED[1]
    S.locked("CamD_01b", (xs[mid], ys[mid], -0.25), (xs[mid] + 0.3, ys[mid] - 3.0, 0.15), f=D01B_START, lens=35)


# ---- paper：D_03a ---------------------------------------------------------------------------
def paper(sc, rnd):
    A0.paper(sc, rnd)                                       # 同一张纸、同一行（A0 代码不动）
    lt = bpy.data.objects[sc["slit_light"]]
    if lt.data.animation_data:
        lt.data.animation_data_clear()                       # 去掉 A0_02b 的渐暗
    lt.data.energy = 70.0 * 1.35                             # 比开场稍亮
    fill = bpy.data.objects["RoomFill"]
    fill.data.energy = 0.6 * 1.8
    rig = bpy.data.objects["PaperRig"]
    aim_y = sc["lit_row_y"] + 0.02
    n = S.shot_frames("D_03a", 152)
    A0._camera("CamD_03a", [(1, (0.0, aim_y, 0.004), (-0.11, aim_y - 0.33, 0.16), 50, 2.8),
                            (n, (0.0, aim_y, 0.004), (-0.07, aim_y - 0.25, 0.115), 50, 2.8)], parent=rig)


# ---- line：D_04b ----------------------------------------------------------------------------
def line(sc, rnd):
    sc["variant"] = "line"
    m = S.glow("EndLine", S.lin(E.CHANNEL), 0.0)
    ob = S.tube("EndLine", [(-1.2, 0, -0.32), (1.2, 0, -0.32)], 0.004, m, "emitter", res=2)
    S.set_strength(m, 1, 6.0)
    S.set_strength(m, 6, 6.0)
    S.set_strength(m, 15, 0.0)                              # 0.6 秒内熄灭，之后全黑
    # 光从两端往中间收：曲线两端的 bevel factor 同时收拢
    cu = ob.data
    cu.bevel_factor_mapping_start = cu.bevel_factor_mapping_end = "SPLINE"
    for f, a, b in ((1, 0.0, 1.0), (6, 0.0, 1.0), (15, 0.47, 0.53)):
        cu.bevel_factor_start, cu.bevel_factor_end = a, b
        cu.keyframe_insert("bevel_factor_start", frame=f)
        cu.keyframe_insert("bevel_factor_end", frame=f)
    S.locked("CamD_04b", (0, 0, 0), (0, -4.2, 0), lens=35)


# ---- closing：D_92 --------------------------------------------------------------------------
def closing(sc, rnd):
    sc["variant"] = "closing"
    px, py = BO.pore_center()
    b = BB.build_bilayer("D92Bilayer", half_w=160.0, half_d=100.0, holes=[(0.0, 0.0, 24.0)], seed=9)
    for o in b.values():
        styles.tag(o, "structure")
    mat = M.principled("D92Protein", (0.7, 0.7, 0.72), roughness=0.5)
    p = BO.build_opsin("D92ChR", "channel", (0, 0, 0), mat, tag=styles.tag)
    n = S.shot_frames("D_92", 96)
    BO.set_open(p, 1, 1.0, glow=5.0)
    BO.set_open(p, 18, 1.0, glow=5.0)
    BO.set_open(p, 22, 1.0, glow=0.0)                       # 光灭
    BO.set_open(p, 70, 0.0, glow=0.0)                       # 孔慢慢合上
    beam, bm = S.cone_beam("D92Beam", (0.0, -0.2, 1.4), (px * 0.01, py * 0.01, 0.2), 0.22, S.lin(E.CHANNEL), 0.8)
    S.set_gain(bm, 18, 0.8)
    S.set_gain(bm, 22, 0.0)
    # 斜上方 50 mm，看得到胞外一侧的孔口和半截剖面
    S.locked("CamD_92", (px * 0.01, py * 0.01, 0.02), (0.55, -1.55, 0.95), lens=50)
    sc["d92_frames"] = n


# ---- 风格后处理（一个模块一个 after_style）-------------------------------------------------------
def after_style(style, shot_id):
    sc = bpy.context.scene
    v = sc.get("variant")
    if v == "paper":
        A0.after_style(style, shot_id)                       # 纸页的 Cycles 采样、颗粒和暗角跟 A0 一致
        return
    S.after_style_common(sc, style)
    if v == "closing":
        S.cycles(sc, {"preview": 16, "sample": 24, "final": 32}, bounces=1, clamp=0.0)


def build(variant="switch", seed=7):
    sc = C.reset_scene(FRAMES)
    rnd = random.Random(seed)
    {"switch": switch, "paper": paper, "line": line, "closing": closing}[variant](sc, rnd)
    return sc
