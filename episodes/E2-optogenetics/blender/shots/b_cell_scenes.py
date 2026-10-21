"""E2 B 段：细胞 / 活体 / 文献镜头（一个模块，多个 variant；只有一个 after_style，内部按 variant 分支，见 WORKFLOW 9）：

  chlamy_swim  B_05a  photoreal / Cycles：一枚参数化衣藻（build_cell）在暗水里朝右侧一束光游过去，眼点是赤道旁的橙红小斑，
                      游动时绕长轴自转、鞭毛划桨（拍频放慢，artistic）。慢推。
  chlamy_turn  B_05b  energy / EEVEE：同一衣藻特写，眼点处一道快速电流（沿细胞表面从眼点亮到鞭毛基部），随后细胞转向光源。
  oocyte       B_06a  blueprint / EEVEE（分镜 engine 写 manim；builder 是 parametric_blender，膜和通道按 WORKFLOW 6.4 必须用
                      Blender，所以改用 EEVEE 的 blueprint 风格，registry 里写明）：衣藻蛋白的基因（DNA 双螺旋示意 + 箭头）指向
                      一枚爪蟾卵母细胞；膜上出现通道位点；加上视黄醛（小分子示意）、光线箭头打下，双电极接到一只风格化电流表，
                      指针偏转；几颗标「H⁺」的小球经位点进入细胞（主要是质子，F5）。
  dish_spikes  B_10a  clay / EEVEE：培养皿里一枚参数化神经元（build_neuron），蓝光短脉冲照在胞体上；后方记录板上，脉冲标记列和
                      锋电位曲线同步从左往右画出，每根锋电位紧跟在一个脉冲标记的同一 x 位置之后。曲线、脉冲都无刻度、无数字，
                      不画频率上限（分镜要求）。
  journal      B_13a  documentary / Cycles：暗桌上一份风格化期刊（封面 + 目录页）。只有目录页上一行拉丁字「optogenetic」可读，
                      年份「2006」，其余是不可读的抽象笔画；不复制任何真实期刊的刊名、版式或标志。慢推到那一行。
  head_fiber   B_14a  xray / EEVEE：啮齿动物头部矢状剖面（build_brain.head_section），一根光纤（build_props.fiber_implant）从颅顶
                      插到运动皮层，只有兴奋性神经元那一层泛蓝光，其他层不亮。慢推。
  fiber_tip    B_14b  photoreal / Cycles：示意光纤植入件夹在风格化支架上，蓝光只在裸光纤尖端。
  whisker      B_15b  documentary / Cycles：风格化小鼠（build_props.mouse）头上带光纤线缆，胡须和头部轻微偏转。不做眼部特写。

时间：动画长度用 S.shot_frames；旁白里的关键时刻（秒，镜头内）写在下面的常量里，retime 后按 review_words 再对一次。
示意说明（核查表 B 段记 simplified / artistic）：鞭毛拍频放慢；锋电位曲线无单位；电流表是风格化表头，不是真实记录仪；
期刊是风格化纸页；头部剖面和皮层分层按 build_brain 的示意。道具（光纤、支架、小鼠、培养皿）是参数化低细节示意，
TODO(prop)：以后可换 Tripo / Meshy 道具（先记 research/visual/assets.yaml）。
已知问题：e2_shot.cone_beam 的光束材质在 EEVEE 预览里渲成不透明的灰白锥（Cycles 里过亮），所以 B_05a 用聚光灯 + 体积光柱，
B_05b 用 halo 光晕；B_10a 的脉冲光锥仍用 cone_beam（增益压低，clay 里可读），共用材质修好后再看一遍。
没有中文标注（「H⁺」「optogenetic」「2006」是拉丁字，用 Blender 文字对象），所以本模块没有 raw 镜头。
"""
import math
import random

import bpy
import bmesh
from mathutils import Vector

import build_cell as BC
import build_neuron as BN
import common as C
import e2_common as E
import e2_shot as S
import materials as M
import styles

FPS = 24

# 旁白关键时刻（镜头内秒；按定时后的整句和字数比例估的，retime 后用 review_words 校）
B06_GENE_AT = 1.0          # 基因画出
B06_INSERT_AT = 5.5        # 箭头到卵母细胞（「放进爪蟾的卵母细胞」）
B06_SITES_AT = 7.0         # 通道位点出现
B06_RETINAL_AT = 10.6      # 「加上视黄醛」
B06_LIGHT_AT = 12.2        # 「再给光」
B06_CURRENT_AT = 13.4      # 「膜上出现了一道电流」
B06_PROTON_AT = 15.2       # 「主要让质子通过」
B10_TRACE = (1.4, 23.6)    # 记录曲线从哪一秒画到哪一秒
B10_PULSES = 10            # 脉冲个数（等间距，不表示任何频率）
B14_LIGHT_AT = 7.6         # 「用光纤把蓝光送进啮齿动物的运动皮层」


def _f(t):
    return 1 + round(t * FPS)


def _mat(name, color, roughness=0.5, transmission=0.0, alpha=None, emission=None, strength=0.0, sss=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    p.inputs["Base Color"].default_value = (*color, 1)
    p.inputs["Roughness"].default_value = roughness
    if transmission:
        p.inputs["Transmission Weight"].default_value = transmission
        p.inputs["IOR"].default_value = 1.38
    if sss:
        p.inputs["Subsurface Weight"].default_value = sss
        p.inputs["Subsurface Radius"].default_value = (0.05, 0.08, 0.04)
    if emission:
        p.inputs["Emission Color"].default_value = (*emission, 1)
        p.inputs["Emission Strength"].default_value = strength
    if alpha is not None:
        p.inputs["Alpha"].default_value = alpha
        m.surface_render_method = "BLENDED"
    return m


def _text(name, body, loc, size, mat, rot=(math.pi / 2, 0, 0), align="CENTER", role="structure", extrude=0.0):
    """拉丁字文字对象（Blender 内置字体）。默认竖起来朝 -Y。"""
    cu = bpy.data.curves.new(name, "FONT")
    cu.body = body
    cu.size = size
    cu.align_x = align
    cu.align_y = "CENTER"
    cu.extrude = extrude
    ob = S.link(bpy.data.objects.new(name, cu))
    ob.location = loc
    ob.rotation_euler = rot
    if mat is not None:
        cu.materials.append(mat)
    styles.tag(ob, role)
    return ob


def _chlamy_mats(energy=False):
    green = (0.10, 0.48, 0.06)
    return {
        "wall": _mat("ChlWall", (0.8, 0.92, 0.76), 0.2, transmission=0.8),
        "chloro": _mat("ChlChloroplast", green, 0.45, emission=(0.12, 0.5, 0.08), strength=0.25),
        "pyrenoid": _mat("ChlPyrenoid", (0.55, 0.66, 0.42), 0.4),
        "nucleus": _mat("ChlNucleus", (0.58, 0.6, 0.52), 0.5, transmission=0.3),
        "vacuole": _mat("ChlVacuole", (0.85, 0.92, 0.95), 0.08, transmission=0.95),
        "flagellum": _mat("ChlFlagellum", (0.82, 0.86, 0.78), 0.35),
        "eyespot": M.emission("ChlEyespot", (0.95, 0.28, 0.05), 0.6),
    }


def _water(sc):
    """暗水底色：photoreal 镜头不用 HDRI 反射（sc["hdri_world"] 让 styles 跳过默认 HDRI）。"""
    C.set_world(top=(0.006, 0.014, 0.016), horizon=(0.003, 0.008, 0.009), bottom=(0.0008, 0.0015, 0.0018))
    C.set_color_management(look="Base Contrast", exposure=0.0)
    sc["hdri_world"] = 1


def _light_shaft(name, src, aim, angle_deg, energy=3500.0, density=0.018):
    """photoreal 里的一束光：聚光灯 + 罩住光路的低密度体积（Cycles 体积散射出光柱）。"""
    S.spot(name + "Spot", src, aim, energy, angle_deg=angle_deg, blend=0.35, color=(0.85, 0.93, 1.0), radius=0.05)
    bpy.ops.mesh.primitive_cube_add(location=(0, 0.3, 0))
    vol = bpy.context.object
    vol.name = name + "Volume"
    vol.scale = (4.5, 3.0, 3.0)
    m = bpy.data.materials.new(name + "VolMat")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.remove(next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"))
    pv = nt.nodes.new("ShaderNodeVolumePrincipled")
    pv.inputs["Density"].default_value = density
    pv.inputs["Color"].default_value = (0.8, 0.95, 0.9, 1)
    pv.inputs["Anisotropy"].default_value = 0.4
    nt.links.new(pv.outputs[0], next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL").inputs["Volume"])
    vol.data.materials.append(m)
    vol.visible_shadow = False
    vol.display_type = "WIRE"
    styles.tag(vol, "rig")
    return vol


def _motes(prefix, n, center, half, rnd, mat):
    """水里的悬浮小颗粒（photoreal 的景深参照）。"""
    for i in range(n):
        p = tuple(center[k] + rnd.uniform(-half[k], half[k]) for k in range(3))
        ob = S.sphere(f"{prefix}{i}", rnd.uniform(0.006, 0.02), p, mat, "env", seg=8, rings=6)
        S.key(ob, 1, location=p)
        S.key(ob, 400, location=(p[0] + rnd.uniform(-0.05, 0.05), p[1], p[2] + rnd.uniform(-0.08, 0.02)))
        S.linear(ob)


# ---- chlamy_swim：B_05a -----------------------------------------------------------------------
def chlamy_swim(sc, rnd):
    n = S.shot_frames("B_05a", 288)
    _water(sc)
    cell = BC.build_chlamy("Chlamy", mats=_chlamy_mats(), tag=styles.tag)
    path = []
    for k in range(13):                                  # 朝光束游，带一点螺旋游动的摆
        u = k / 12
        path.append((-2.3 + 2.7 * u, 0.12 * math.sin(u * 7.0), -0.35 + 0.45 * u + 0.08 * math.cos(u * 7.0)))
    BC.swim(cell, path, 1, n)
    BC.beat(cell, 1, n, period=12)
    BC.spin(cell, 1, n, turns_per_s=0.5)
    _light_shaft("Shaft", (3.4, 0.5, 3.6), (1.1, 0.0, -0.3), 18.0)
    for lt in (S.area("Key", (-1.5, -3.5, 2.5), (-0.6, 0, 0), 2.5, 420, color=(0.95, 0.97, 1.0), keep=True),
               S.area("Rim", (-2.0, 3.0, 1.0), (-0.8, 0, 0), 3.0, 600, color=(0.6, 0.85, 0.75), keep=True),
               S.area("Under", (-1.0, -2.0, -2.5), (-0.6, 0, 0), 4.0, 80, color=(0.5, 0.7, 0.6), keep=True)):
        lt.visible_volume_scatter = False                 # 只让光束那盏灯在水里散射出光柱
    _motes("Mote", 40, (-0.3, 0.6, 0.0), (3.0, 2.2, 1.6), rnd, _mat("MoteMat", (0.12, 0.15, 0.12), 0.7))
    S.camera("CamB_05a", [(1, (-0.6, 0, -0.15), (-0.9, -6.4, 0.35), 50, 4.0),
                          (n, (0.2, 0, 0.05), (-0.3, -5.3, 0.3), 50, 4.0)], dof=True)


# ---- chlamy_turn：B_05b -----------------------------------------------------------------------
def chlamy_turn(sc, rnd):
    n = S.shot_frames("B_05b", 32)
    sc["variant"] = "chlamy_turn"
    cell = BC.build_chlamy("Chlamy", mats=_chlamy_mats(), tag=styles.tag)
    root = cell["root"]
    light_dir = Vector((1.0, 0.0, 0.25)).normalized()
    start = Vector((math.cos(math.radians(-50)), 0.0, math.sin(math.radians(-50))))
    e0 = BC.heading_euler(start)
    e1 = BC.heading_euler(light_dir)
    e1.make_compatible(e0)
    S.key(root, 1, rotation_euler=e0)
    S.key(root, 9, rotation_euler=e0)
    S.key(root, n, rotation_euler=e1)
    BC.beat(cell, 1, n + 4, period=10)
    # 眼点闪一下
    em = cell["eyespot"].data.materials[0]
    S.set_strength(em, 1, 0.8)
    S.set_strength(em, 3, 14.0)
    S.set_strength(em, 12, 2.0)
    # 快速电流：沿细胞表面（+X 子午线）从眼点到前端鞭毛基部
    u = BC.UNIT
    rx, ry = BC.CELL_WID / 2 * u, BC.CELL_LEN / 2 * u
    pts = []
    for k in range(18):
        lat = BC.EYESPOT_LAT + (math.radians(84) - BC.EYESPOT_LAT) * k / 17
        pts.append((rx * 1.04 * math.cos(lat), ry * 1.04 * math.sin(lat), 0.0))
    cur = S.tube("Current", pts, 0.012, M.emission("CurrentMat", S.lin(E.CHANNEL), 18.0), "emitter")
    cur.parent = cell["spin"]
    S.reveal(cur, 3, 9)
    curm = cur.data.materials[0]
    S.set_strength(curm, 9, 18.0)
    S.set_strength(curm, 20, 0.0)
    # 光源：画面右侧一团软光晕（halo，A0 验证过的做法；cone_beam 在 EEVEE 下透明不生效，见模块头）
    hm = S.halo("LightHaloMat", (0.75, 0.9, 1.0), 1.4)
    S.sphere("LightHalo", 0.75, tuple(light_dir * 1.75 + Vector((0, 0.5, 0.0))), hm, "emitter", seg=32, rings=16)
    S.camera("CamB_05b", [(1, (0.25, 0, 0.05), (0.3, -2.1, 0.3), 35, 8.0)])


# ---- oocyte：B_06a（blueprint）---------------------------------------------------------------
def _helix(prefix, x0, x1, z, r, turns, mat, f_on):
    """DNA 双螺旋示意：两条螺旋管 + 碱基对横档，沿 x 从 x0 到 x1。"""
    obs = []
    for ph in (0.0, math.pi):
        pts = []
        for k in range(97):
            u = k / 96
            a = 2 * math.pi * turns * u + ph
            pts.append((x0 + (x1 - x0) * u, r * math.sin(a), z + r * math.cos(a)))
        ob = S.tube(f"{prefix}Strand{int(ph)}", pts, 0.022, mat, "structure")
        S.reveal(ob, f_on, f_on + 30)
        obs.append(ob)
    for k in range(int(turns * 10)):
        u = (k + 0.5) / (turns * 10)
        a = 2 * math.pi * turns * u
        x = x0 + (x1 - x0) * u
        p0 = (x, r * math.sin(a), z + r * math.cos(a))
        p1 = (x, -r * math.sin(a), z - r * math.cos(a))
        rung = S.between(f"{prefix}Rung{k}", p0, p1, 0.010, mat, "structure", verts=8)
        S.show_between(rung, f_on + round(30 * u))
        obs.append(rung)
    return obs


def oocyte(sc, rnd):
    n = S.shot_frames("B_06a", 586)
    sc["variant"] = "oocyte"
    mat = S.matte("BPStruct", (0.8, 0.85, 0.9))
    oc_c = (0.9, 0.0, -0.1)
    ooc = BC.build_oocyte("Oocyte", loc=oc_c, r=1.05, mats={"animal": mat, "band": mat, "vegetal": mat, "site": mat},
                          sites=6, tag=styles.tag)
    for s_ in ooc["sites"]:
        S.show_between(s_, _f(B06_SITES_AT) + 3 * ooc["sites"].index(s_))
    # 基因 + 箭头
    _helix("Gene", -3.4, -1.7, 0.75, 0.16, 2.0, mat, _f(B06_GENE_AT))
    gl = _text("GeneLabel", "Chlamydomonas", (-2.55, 0, 0.32), 0.17, mat)
    S.show_between(gl, _f(B06_GENE_AT) + 20)
    sh, hd = S.arrow("GeneArrow", (-1.55, 0, 0.6), (-0.25, 0, 0.25), 0.03, mat)
    for o in (sh, hd):
        S.show_between(o, _f(B06_INSERT_AT) - 30)
    # 视黄醛：锯齿小分子从左上落到膜旁
    zz = [(0.06 * k, 0, 0.035 * (1 if k % 2 else -1)) for k in range(9)]
    ret_root = S.link(bpy.data.objects.new("RetinalRoot", None))
    ret = S.tube("Retinal", zz, 0.014, mat, "structure")
    ring = S.tube("RetinalRing", [(0.48 + 0.06 * math.cos(math.radians(60 * k)), 0, 0.06 * math.sin(math.radians(60 * k)))
                                  for k in range(7)], 0.012, mat, "structure")
    for o in (ret, ring):
        o.parent = ret_root
    fr = _f(B06_RETINAL_AT)
    S.key(ret_root, fr - 1, location=(-1.4, 0, 1.6))
    S.key(ret_root, fr + 30, location=(-0.35, -0.2, 0.75))
    for o in (ret, ring):
        S.show_between(o, fr)
    rl = _text("RetinalLabel", "retinal", (0.25, 0, 0.22), 0.13, mat)
    rl.parent = ret_root
    S.show_between(rl, fr + 6)
    # 光：三支平行的光线箭头从上方打下
    fl = _f(B06_LIGHT_AT)
    for i, dx in enumerate((-0.45, 0.0, 0.45)):
        a = Vector((oc_c[0] + dx - 0.5, 0, 2.6))
        b = Vector((oc_c[0] + dx - 0.15, 0, 1.25 - 0.08 * abs(dx)))
        sh, hd = S.arrow(f"Ray{i}", tuple(a), tuple(b), 0.022, mat)
        for o in (sh, hd):
            S.show_between(o, fl + 2 * i)
        for k in range(3):                               # 波浪纹，读作「光」
            w = S.tube(f"RayWave{i}_{k}", [(a.x + 0.08 + 0.05 * j / 6 + 0.06 * (k - 1), 0,
                                            a.z - 0.25 - 0.35 * k / 3 - 0.06 * math.sin(j)) for j in range(7)],
                       0.008, mat, "structure")
            S.show_between(w, fl + 2 * i)
    # 双电极 + 电流表
    meter_c = Vector((3.25, 0, 0.35))
    for i, (dx, dz) in enumerate(((0.45, 0.85), (0.75, 0.6))):
        tip = Vector(oc_c) + Vector((dx, -0.2, dz)) * 0.98
        top = tip + Vector((0.5, 0, 1.0))
        S.between(f"Electrode{i}", tuple(tip), tuple(top), 0.018, mat, "structure")
        S.tube(f"Wire{i}", [tuple(top), tuple(top + Vector((0.4, 0, 0.25))),
                            tuple(meter_c + Vector((-0.45 + 0.25 * i, 0, 0.55)))], 0.008, mat, "structure")
    S.box("MeterBody", tuple(meter_c), (1.15, 0.12, 0.85), mat, "structure", bevel=0.03)
    face = S.box("MeterFace", tuple(meter_c + Vector((0, -0.07, 0.02))), (0.98, 0.02, 0.68), S.matte("BPFace", (1, 1, 1)),
                 "structure")
    arc = []
    for k in range(25):
        a = math.radians(-50 + 100 * k / 24)
        arc.append((meter_c.x + 0.36 * math.sin(a), -0.09, meter_c.z - 0.2 + 0.36 * math.cos(a)))
    S.tube("MeterArc", arc, 0.008, mat, "structure")
    for k in range(5):
        a = math.radians(-50 + 25 * k)
        p0 = Vector((meter_c.x + 0.33 * math.sin(a), -0.09, meter_c.z - 0.2 + 0.33 * math.cos(a)))
        p1 = Vector((meter_c.x + 0.40 * math.sin(a), -0.09, meter_c.z - 0.2 + 0.40 * math.cos(a)))
        S.between(f"MeterTick{k}", tuple(p0), tuple(p1), 0.007, mat, "structure", verts=8)
    piv = S.link(bpy.data.objects.new("NeedlePivot", None))
    piv.location = (meter_c.x, -0.1, meter_c.z - 0.2)
    needle = S.box("Needle", (0, 0, 0.17), (0.018, 0.012, 0.34), mat, "structure")
    needle.parent = piv
    fc = _f(B06_CURRENT_AT)
    S.key(piv, 1, rotation_euler=(0, math.radians(-40), 0))
    S.key(piv, fc, rotation_euler=(0, math.radians(-40), 0))
    S.key(piv, fc + 10, rotation_euler=(0, math.radians(32), 0))
    S.key(piv, fc + 16, rotation_euler=(0, math.radians(26), 0))
    S.key(piv, n, rotation_euler=(0, math.radians(28), 0))
    S.sphere("NeedleHub", 0.04, tuple(piv.location), mat, "structure", seg=12, rings=8)
    # 质子：标 H⁺ 的小球经位点进入细胞
    fp = _f(B06_PROTON_AT)
    oc = Vector(oc_c)
    for i, sl in enumerate(ooc["site_locs"][:5]):
        sl = Vector(sl)
        nrm = (sl - oc).normalized()
        p0 = sl + nrm * 0.55
        p1 = sl - nrm * 0.22
        pr = S.link(bpy.data.objects.new(f"Proton{i}", None))
        ball = S.sphere(f"ProtonBall{i}", 0.075, (0, 0, 0), mat, "structure", seg=16, rings=8)
        ball.parent = pr
        lab = _text(f"ProtonLabel{i}", "H+", (0.0, -0.08, 0.2), 0.2, mat)
        lab.parent = pr
        f0 = fp + 9 * i
        S.key(pr, 1, location=tuple(p0))
        S.key(pr, f0, location=tuple(p0))
        S.key(pr, f0 + 30, location=tuple(sl))
        S.key(pr, f0 + 46, location=tuple(p1))
        for o in (ball, lab):
            S.show_between(o, fp - 18 + 9 * i)
    S.camera("CamB_06a", [(1, (0.0, 0, 0.45), (0.0, -12.2, 1.1), 50, 8.0),
                          (n, (0.35, 0, 0.35), (0.35, -10.2, 0.9), 50, 8.0)])


# ---- dish_spikes：B_10a（clay）---------------------------------------------------------------
def _reveal_by_x(ob, pts, f0, f1, step=2):
    """曲线按 x 匀速画出（bevel_factor_end = 到该 x 的弧长 / 总弧长），这样笔尖与脉冲标记的 x 对齐。"""
    acc = [0.0]
    for i in range(len(pts) - 1):
        acc.append(acc[-1] + math.dist(pts[i], pts[i + 1]))
    tot = acc[-1]
    x0, x1 = pts[0][0], pts[-1][0]
    cu = ob.data
    cu.bevel_factor_mapping_end = "SPLINE"
    for f in list(range(f0, f1 + 1, step)) + [f1]:
        x = x0 + (x1 - x0) * (f - f0) / max(1, f1 - f0)
        k = min(len(pts) - 1, max(0, round((x - x0) / (x1 - x0) * (len(pts) - 1))))
        cu.bevel_factor_end = acc[k] / tot
        cu.keyframe_insert("bevel_factor_end", frame=f)
    S.linear(ob)


NEURON_Z = 0.19                # 培养液（放大后）顶面约 0.15 BU；clay 里培养液不透明，神经元贴在液面上方一点


def _open_wall(ob):
    """培养皿侧壁：去掉圆柱的上下盖面，只留一圈壁（build_props.dish 的侧壁是带盖的圆柱）。"""
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    caps = [f for f in bm.faces if abs(f.normal.z) > 0.9]
    bmesh.ops.delete(bm, geom=caps, context="FACES_ONLY")
    bm.to_mesh(ob.data)
    bm.free()


def dish_spikes(sc, rnd):
    import build_props as BPR
    n = S.shot_frames("B_10a", 594)
    sc["variant"] = "dish_spikes"
    blue = S.lin(E.CHANNEL)
    d = BPR.dish("Dish", (0, 0, 0), r=0.045, tag=styles.tag, lid=False)
    d["root"].scale = (30, 30, 30)                       # 培养皿放大到 2.7 BU 直径，神经元是示意比例
    _open_wall(d["wall"])
    nroot = S.link(bpy.data.objects.new("NeuronRoot", None))
    nroot.location = (0.0, -0.45, NEURON_Z)
    nroot.rotation_euler = (math.pi / 2, 0, math.radians(8))
    cell = BN.build_neuron("DishNeuron", E.NEURON_SEEDS[4], (0, 0, 0), None, tag=styles.tag)
    for o in [cell["soma"], cell["dendrites"], cell["axon"]] + cell["boutons"]:
        o.parent = nroot
    # 记录板
    board_y = 2.3
    S.box("Board", (0, board_y + 0.05, 1.25), (3.9, 0.08, 1.75), None, "structure", bevel=0.02)
    f0, f1 = _f(B10_TRACE[0]), _f(B10_TRACE[1])
    pulses = [0.07 + k * (0.86 / (B10_PULSES - 1)) for k in range(B10_PULSES)]
    spikes = [p + 0.006 for p in pulses]                 # 锋电位紧跟脉冲（潜伏期示意，不按比例）
    ox, w = -1.65, 3.3
    tm = M.emission("TraceMat", (0.92, 0.95, 1.0), 4.0)
    ob, base, pts = S.trace("SpikeTrace", lambda u: S.spike_train(u, spikes, width=0.03), (ox, board_y - 0.02, 0.95),
                            (w, 1.0), tm, f0, f1, n=1100, r=0.011)
    ob.data.animation_data_clear()
    _reveal_by_x(ob, pts, f0, f1)
    head = S.sphere("TraceHead", 0.03, pts[0], M.emission("TraceHeadMat", (1, 1, 1), 8.0), "emitter", seg=12, rings=8)
    for f in list(range(f0, f1 + 1, 2)) + [f1]:
        x = ox + w * (f - f0) / max(1, f1 - f0)
        k = min(len(pts) - 1, round((x - ox) / w * (len(pts) - 1)))
        S.key(head, f, location=pts[k])
    S.linear(head)
    S.show_between(head, f0, f1 + 6)
    beam, bmat = S.cone_beam("Pulse", (0.0, -1.1, 2.7), (0.0, -0.45, NEURON_Z), 0.2, blue, 0.0)
    halo_m = S.halo("SomaFlashMat", blue)
    S.sphere("SomaFlash", 0.34, (0.0, -0.45, NEURON_Z), halo_m, "emitter", seg=20, rings=12)
    pm = M.emission("PulseMarkMat", blue, 6.0)
    S.set_gain(bmat, 1, 0.0)
    S.set_gain(halo_m, 1, 0.0)
    for k, p in enumerate(pulses):
        fk = f0 + round(p * (f1 - f0))
        mark = S.box(f"PulseMark{k}", (ox + w * p, board_y - 0.03, 1.62), (0.05, 0.02, 0.16), pm, "emitter")
        S.show_between(mark, fk)
        S.set_gain(bmat, fk - 1, 0.0)
        S.set_gain(bmat, fk, 0.8)
        S.set_gain(bmat, fk + 3, 0.8)
        S.set_gain(bmat, fk + 5, 0.0)
        S.set_gain(halo_m, fk, 0.0)
        S.set_gain(halo_m, fk + 2, 3.0)
        S.set_gain(halo_m, fk + 9, 0.0)
    S.studio_lights(0.6, (0, 0.6, 0.6))
    S.camera("CamB_10a", [(1, (0, 0.45, 0.8), (0.0, -6.3, 3.2), 50, 8.0),
                          (n, (0, 0.5, 0.8), (0.0, -5.5, 2.85), 50, 8.0)])


# ---- journal：B_13a（documentary）------------------------------------------------------------
def _strokes(name, rows, mat):
    """抽象笔画行：rows = [(x0, x1, y, h)]，每行一串断开的小横条（不可读，不排任何文字）。合成一个网格。"""
    bm = bmesh.new()
    rnd = random.Random(len(rows))
    for x0, x1, y, h in rows:
        x = x0
        while x < x1:
            wd = rnd.uniform(0.004, 0.02)
            xe = min(x1, x + wd)
            vs = [bm.verts.new((x, y - h / 2, 0)), bm.verts.new((xe, y - h / 2, 0)),
                  bm.verts.new((xe, y + h / 2, 0)), bm.verts.new((x, y + h / 2, 0))]
            bm.faces.new(vs)
            x = xe + rnd.uniform(0.0015, 0.004)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = S.link(bpy.data.objects.new(name, me))
    ob.data.materials.append(mat)
    styles.tag(ob, "structure")
    return ob


def journal(sc, rnd):
    n = S.shot_frames("B_13a", 636)
    sc["variant"] = "journal"
    S.dark_room()
    desk = S.box("Desk", (0, 0, -0.01), (1.6, 1.0, 0.02), _mat("DeskMat", (0.06, 0.04, 0.03), 0.55), "env")
    paper = _mat("JournalPaper", (0.78, 0.76, 0.7), 0.7)
    ink = _mat("JournalInk", (0.05, 0.05, 0.06), 0.6)
    accent = _mat("JournalAccent", (0.18, 0.26, 0.4), 0.5)
    W, H = 0.21, 0.28
    # 封面（左，略转）：上方一条抽象刊名色带（不仿任何刊名），中间一块抽象图形，下方几行抽象笔画
    cov = S.link(bpy.data.objects.new("Cover", None))
    cov.location = (-0.13, 0.02, 0.0)
    cov.rotation_euler = (0, 0, math.radians(6))
    parts = [S.box("CoverSheet", (0, 0, 0.0015), (W, H, 0.003), paper, "structure"),
             S.box("CoverBand", (0, H / 2 - 0.03, 0.0031), (W - 0.02, 0.035, 0.0003), accent, "structure"),
             S.box("CoverArt", (0, 0.0, 0.0031), (W - 0.05, 0.12, 0.0003), _mat("CoverArtMat", (0.3, 0.33, 0.36), 0.6),
                   "structure")]
    st = _strokes("CoverStrokes", [(-W / 2 + 0.015, W / 2 - 0.05, -H / 2 + 0.05 - 0.009 * k, 0.003) for k in range(4)], ink)
    st.location.z = 0.0032
    parts.append(st)
    yr = _text("CoverYear", "2006", (W / 2 - 0.035, -H / 2 + 0.03, 0.0033), 0.012, ink, rot=(0, 0, 0))
    parts.append(yr)
    for o in parts:
        o.parent = cov
    # 目录页（右）：抽象条目，只有一条里有可读的「optogenetic」
    toc = S.link(bpy.data.objects.new("TOC", None))
    toc.location = (0.11, 0.0, 0.0)
    toc.rotation_euler = (0, 0, math.radians(-2))
    sheet = S.box("TOCSheet", (0, 0, 0.0015), (W, H, 0.003), paper, "structure")
    sheet.parent = toc
    rows = []
    hi_row = 9
    for k in range(18):
        y = H / 2 - 0.035 - k * 0.0125
        if k == hi_row:
            rows.append((-W / 2 + 0.015, -W / 2 + 0.05, y, 0.0035))
            rows.append((-W / 2 + 0.125, W / 2 - 0.02, y, 0.0035))
        else:
            rows.append((-W / 2 + 0.015, W / 2 - 0.02 - (0.04 if k % 3 == 2 else 0), y, 0.0035 if k % 3 else 0.005))
    tst = _strokes("TOCStrokes", rows, ink)
    tst.parent = toc
    tst.location.z = 0.0032
    head = _strokes("TOCHead", [(-W / 2 + 0.015, W / 2 - 0.06, H / 2 - 0.016, 0.007)], accent)
    head.parent = toc
    head.location.z = 0.0032
    word = _text("Optogenetic", "optogenetic", (-W / 2 + 0.088, H / 2 - 0.035 - hi_row * 0.0125, 0.0033), 0.0105, ink,
                 rot=(0, 0, 0))
    word.parent = toc
    yr2 = _text("TOCYear", "2006", (W / 2 - 0.03, H / 2 - 0.016, 0.0033), 0.008, ink, rot=(0, 0, 0))
    yr2.parent = toc
    # 灯：左上低角度暖光 + 极弱的室内底光
    S.area("Key", (-0.55, 0.45, 0.42), (0.06, -0.02, 0), 0.35, 26, color=(1.0, 0.88, 0.72), keep=True)
    S.area("Fill", (0.5, -0.6, 0.5), (0, 0, 0), 0.8, 1.2, color=(0.75, 0.82, 1.0), keep=True)
    tgt = (0.11 - 0.012, H / 2 - 0.035 - hi_row * 0.0125, 0.003)
    S.camera("CamB_13a", [(1, (0.0, 0.0, 0.0), (-0.02, -0.46, 0.42), 50, 4.0),
                          (n, tgt, (0.05, -0.17, 0.16), 50, 2.8)], dof=True)


# ---- head_fiber：B_14a（xray）----------------------------------------------------------------
def head_fiber(sc, rnd):
    import build_brain as BB
    import build_props as BPR
    n = S.shot_frames("B_14a", 469)
    sc["variant"] = "head_fiber"
    hs = BB.head_section("Head", (0, 0, 0), 1.0, tag=styles.tag)
    reg = hs["regions"]
    tip = Vector(reg["excitatory_layer_at_motor_cortex"]) + Vector((0, 0, 0.012))   # 尖端停在兴奋性层上方一点
    top = Vector(reg["skull_top_at_motor_cortex"])
    k = 100.0                                        # 脑长 1 BU ≈ 1 cm：光纤道具（米制）放大 100 倍
    fib = BPR.fiber_implant("Fiber", tuple(tip), (0, 0, -1), ferrule_len=0.002, cable_len=0.004,
                            fiber_len=(top.z - tip.z) / k + 0.0004, tag=styles.tag)
    fib["root"].scale = (k, k, k)
    f_on = _f(B14_LIGHT_AT)
    S.set_gain(fib["tip_glow_mat"], 1, 0.0)
    S.set_gain(fib["tip_glow_mat"], f_on, 0.0)
    S.set_gain(fib["tip_glow_mat"], f_on + 8, 2.5)
    S.set_gain(fib["beam_mat"], 1, 0.0)
    S.set_gain(fib["beam_mat"], f_on, 0.0)
        # 只有兴奋性层泛蓝光（build_brain 准备好的发光材质，强度 0 起）
    exc = hs["cortex_layers"]["excitatory"]
    gm = hs["excitatory_glow_mat"]
    exc.data.materials.clear()
    exc.data.materials.append(gm)
    M.set_emission_strength(gm, 1, 0.0)
    M.set_emission_strength(gm, f_on + 6, 0.0)
    M.set_emission_strength(gm, f_on + 36, 2.4)
    S.set_gain(fib["beam_mat"], f_on + 8, 0.5)
    c0 = (0.08, tip.y, 0.0)                          # 先看整个头部剖面，再推向运动皮层
    c1 = (tip.x, tip.y, tip.z - 0.08)
    S.studio_lights(0.3, c0)
    S.camera("CamB_14a", [(1, c0, (c0[0] - 0.1, tip.y - 2.9, 0.35), 50, 8.0),
                          (n, c1, (c1[0] - 0.05, tip.y - 1.7, c1[2] + 0.22), 50, 8.0)])


# ---- fiber_tip：B_14b（photoreal）-----------------------------------------------------------
def fiber_tip(sc, rnd):
    import build_props as BPR
    n = S.shot_frames("B_14b", 32)
    sc["variant"] = "fiber_tip"
    C.set_world(top=(0.012, 0.013, 0.016), horizon=(0.006, 0.0065, 0.008), bottom=(0.002, 0.002, 0.0025))
    C.set_color_management(look="Base Contrast", exposure=0.0)
    sc["hdri_world"] = 1
    tip = Vector((0, 0, 0.012))
    fib = BPR.fiber_implant("Fiber", tuple(tip), (0, 0, -1), ferrule_len=0.008, cable_len=0.12, fiber_len=0.005,
                            tag=styles.tag)
    S.set_gain(fib["tip_glow_mat"], 1, 1.3)
    S.set_gain(fib["beam_mat"], 1, 1.4)
    # 示意固定件：夹住插芯的小夹块 + 立杆 + 底座（TODO(prop)）
    metal = _mat("ClampMetal", (0.55, 0.56, 0.58), 0.28)
    M_ = metal.node_tree.nodes["Principled BSDF"] if "Principled BSDF" in metal.node_tree.nodes else None
    if M_ is not None:
        M_.inputs["Metallic"].default_value = 1.0
    ft = tip.z + 0.005
    S.box("ClampJaw", (0.004, 0, ft + 0.0045), (0.006, 0.0055, 0.004), metal, "structure", bevel=0.0004)
    S.box("ClampArm", (0.018, 0, ft + 0.0045), (0.024, 0.004, 0.003), metal, "structure", bevel=0.0003)
    S.cylinder("ClampPost", 0.002, 0.03, (0.03, 0, ft - 0.008), metal, "structure", verts=24)
    S.box("Base", (0.02, 0.0, -0.0025), (0.09, 0.06, 0.005), _mat("BaseMat", (0.05, 0.05, 0.055), 0.6), "env")
    S.area("Key", (-0.06, -0.07, 0.08), (0, 0, 0.012), 0.06, 0.12, color=(1.0, 0.95, 0.88), keep=True)
    S.area("Rim", (0.05, 0.07, 0.05), (0, 0, 0.012), 0.05, 0.08, color=(0.8, 0.86, 1.0), keep=True)
    S.camera("CamB_14b", [(1, (0.002, 0, 0.0145), (-0.018, -0.052, 0.022), 50, 2.8)], dof=True)


# ---- whisker：B_15b（documentary）-----------------------------------------------------------
def whisker(sc, rnd):
    import build_props as BPR
    n = S.shot_frames("B_15b", 32)
    sc["variant"] = "whisker"
    S.dark_room(top=(0.004, 0.0045, 0.006))
    S.box("Floor", (0, 0, -0.002), (0.6, 0.4, 0.004), _mat("FloorMat", (0.05, 0.05, 0.05), 0.8), "env")
    m = BPR.mouse("Mouse", (0, 0, 0), heading=math.radians(200), tag=styles.tag)
    BPR.whisker_twitch(m, 6, n - 4, amp_deg=8.0, period=6)
    # 头顶的光纤线缆（尖端在头里，看不见；线缆往上走出画）
    head = m["head"]
    bpy.context.view_layer.update()
    hp = head.matrix_world.translation
    fib = BPR.fiber_implant("Fiber", (hp.x, hp.y, hp.z + 0.008), (0, 0, -1), ferrule_len=0.008, cable_len=0.2,
                            fiber_len=0.003, tag=styles.tag)
    fib["root"].parent = m["head_root"]
    fib["root"].matrix_parent_inverse = m["head_root"].matrix_world.inverted()
    S.spot("Key", (0.25, -0.2, 0.35), (hp.x, hp.y, 0.02), 16, angle_deg=28, blend=0.5, color=(1.0, 0.92, 0.82))
    S.area("Rim", (-0.25, 0.25, 0.2), (0, 0, 0.03), 0.3, 6, color=(0.7, 0.8, 1.0), keep=True)
    c = (hp.x * 0.6, hp.y * 0.6, 0.03)
    S.camera("CamB_15b", [(1, c, (c[0] + 0.05, c[1] - 0.33, 0.1), 35, 4.0)], dof=True)


# ---- 风格后处理（一个模块一个 after_style）-------------------------------------------------------
def after_style(style, shot_id):
    sc = bpy.context.scene
    v = sc.get("variant")
    S.after_style_common(sc, style)
    if v == "chlamy_swim":
        sc.cycles.transmission_bounces = 8
        sc["film_grain"], sc["vignette"] = 0.18, 0.4
    elif v == "journal":
        sc["film_grain"], sc["vignette"] = 0.3, 0.45
    elif v in ("fiber_tip", "whisker"):
        sc.cycles.transmission_bounces = 6


VARIANTS = {"chlamy_swim": (chlamy_swim, "B_05a"), "chlamy_turn": (chlamy_turn, "B_05b"), "oocyte": (oocyte, "B_06a"),
            "dish_spikes": (dish_spikes, "B_10a"), "journal": (journal, "B_13a"), "head_fiber": (head_fiber, "B_14a"),
            "fiber_tip": (fiber_tip, "B_14b"), "whisker": (whisker, "B_15b")}


def build(variant="chlamy_swim", seed=7):
    fn, sid = VARIANTS[variant]
    sc = C.reset_scene(S.shot_frames(sid, 600) + 24)
    sc["variant"] = variant
    rnd = random.Random(seed)
    fn(sc, rnd)
    return sc
