"""E2 周边道具：笼箱、风格化小鼠、光纤植入件、实验台、培养皿、电极、屏幕、护目镜。

这些都**不是**核心科学结构（WORKFLOW 6.4）：参数化低细节示意，以后可以换成 Tripo / Meshy 道具（调用前先在
research/visual/assets.yaml 记录工具、prompt、日期，并核对许可）。核查表记 artistic / simplified。
红线：小鼠无写实毛发、无写实眼部特写；笼箱的「惊吓」标记是风格化锯齿符号，不是血、不是电火花特写；
护目镜是通用造型，不仿任何真实产品，也不生成佩戴者。
单位：1 BU = 1 m。所有函数接受 tag(obj, role)（一般传 styles.tag）；不传时不打 role。
"""
import math

import bpy
from mathutils import Vector

import e2_shot as S


def _tag(tag, ob, role):
    if tag:
        tag(ob, role)
    return ob


def _root(name, loc=(0, 0, 0), rot=(0, 0, 0)):
    r = S.link(bpy.data.objects.new(name, None))
    r.location = loc
    r.rotation_euler = rot
    return r


def _mat(name, color, roughness=0.5, metallic=0.0, alpha=None, transmission=0.0):
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    p.inputs["Base Color"].default_value = (*color, 1)
    p.inputs["Roughness"].default_value = roughness
    p.inputs["Metallic"].default_value = metallic
    if transmission:
        p.inputs["Transmission Weight"].default_value = transmission
        p.inputs["IOR"].default_value = 1.49
    if alpha is not None:
        p.inputs["Alpha"].default_value = alpha
        m.surface_render_method = "BLENDED"
    return m


def _parent(obs, root):
    for o in obs:
        o.parent = root


# ---- 笼箱 ------------------------------------------------------------------------------------
# TODO(prop): 可换 Tripo/Meshy 道具（先在 research/visual/assets.yaml 记录）
def _cage_floor_mat(name, tint):
    """笼箱垫面：底色 + 细噪点 + 轻微明暗，避免平涂粉/青色块。"""
    import bpy
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial"); out.location = (400, 0)
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled"); bsdf.location = (120, 0)
    bsdf.inputs["Roughness"].default_value = 0.72
    bsdf.inputs["Metallic"].default_value = 0.0
    noise = nt.nodes.new("ShaderNodeTexNoise"); noise.location = (-400, 40)
    noise.inputs["Scale"].default_value = 38.0
    noise.inputs["Detail"].default_value = 8.0
    noise.inputs["Roughness"].default_value = 0.55
    ramp = nt.nodes.new("ShaderNodeValToRGB"); ramp.location = (-180, 40)
    ramp.color_ramp.elements[0].position = 0.35
    ramp.color_ramp.elements[0].color = (*tuple(max(0, c * 0.55) for c in tint), 1)
    ramp.color_ramp.elements[1].position = 0.72
    ramp.color_ramp.elements[1].color = (*tuple(min(1, c * 1.15 + 0.04) for c in tint), 1)
    nt.links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return m


def cage(name, loc=(0, 0, 0), size=(0.42, 0.26, 0.22), shock_marks=False, floor_tint=(0.5, 0.5, 0.5), tag=None):
    """透明塑料笼箱：底面（structure，floor_tint 是环境色块）+ 四面薄壁和顶框（shell）。
    shock_marks=True 时地面上有几道风格化的锯齿标记（emitter 很弱的琥珀色，示意「这里有电击」）。"""
    w, d, h = size
    root = _root(name, loc)
    floor_m = _cage_floor_mat(name + "FloorMat", floor_tint)
    wall_m = _mat("CagePlastic", (0.85, 0.9, 0.95), 0.08, alpha=0.18, transmission=0.9)
    floor = S.box(name + "Floor", (0, 0, 0.004), (w, d, 0.008), floor_m, "structure", bevel=0.003)
    walls = []
    t = 0.004
    for nm, c, s in (("Front", (0, -d / 2, h / 2), (w, t, h)), ("Back", (0, d / 2, h / 2), (w, t, h)),
                     ("Left", (-w / 2, 0, h / 2), (t, d, h)), ("Right", (w / 2, 0, h / 2), (t, d, h))):
        walls.append(S.box(name + nm, c, s, wall_m, "shell"))
    rim_m = _mat("CageRim", (0.25, 0.27, 0.3), 0.4, metallic=0.6)
    for k, (c, s) in enumerate((((0, -d / 2, h), (w, 0.01, 0.01)), ((0, d / 2, h), (w, 0.01, 0.01)),
                                ((-w / 2, 0, h), (0.01, d, 0.01)), ((w / 2, 0, h), (0.01, d, 0.01)))):
        walls.append(S.box(f"{name}Rim{k}", c, s, rim_m, "structure"))
    marks = []
    if shock_marks:
        mm = S.glow(name + "MarkMat", S.lin((255, 193, 77)), 1.2)
        for j, (mx, my) in enumerate(((-0.12, -0.05), (0.02, 0.06), (0.13, -0.04))):
            pts = []
            for k in range(7):
                pts.append((mx - 0.045 + 0.015 * k, my + (0.012 if k % 2 else -0.012), 0.0095))
            marks.append(S.tube(f"{name}Mark{j}", pts, 0.0018, mm, "emitter", res=1))
    _parent([floor] + walls + marks, root)
    return {"root": root, "floor": floor, "walls": walls, "marks": marks, "size": size}


# ---- 风格化小鼠 ------------------------------------------------------------------------------
# TODO(prop): 可换 Tripo/Meshy 道具（先在 research/visual/assets.yaml 记录）
def mouse(name, loc=(0, 0, 0), heading=0.0, scale=1.0, tag=None):
    """椭球拼成的风格化小鼠，身长约 0.09 m（不含尾），沿局部 +X 朝前。无毛发、无写实眼睛（眼睛是两个小黑点）。
    root 在身体下方的地面上，heading 是绕 Z 的朝向（弧度）。"""
    root = _root(name, loc, (0, 0, heading))
    root.scale = (scale,) * 3
    fur = _mat("MouseFur", (0.62, 0.6, 0.58), 0.75)
    pink = _mat("MousePink", (0.78, 0.55, 0.55), 0.6)
    dark = _mat("MouseEye", (0.02, 0.02, 0.02), 0.3)
    body = S.sphere(name + "Body", 0.03, (0, 0, 0.024), fur, "structure", seg=32, rings=16, scale=(1.5, 1.0, 0.85))
    head = S.sphere(name + "Head", 0.017, (0.048, 0, 0.03), fur, "structure", seg=24, rings=12, scale=(1.35, 0.95, 0.9))
    nose = S.sphere(name + "Nose", 0.0035, (0.07, 0, 0.029), pink, "structure", seg=12, rings=8)
    ears = [S.sphere(f"{name}Ear{s}", 0.008, (0.041, s * 0.012, 0.045), pink, "structure", seg=16, rings=8,
                     scale=(0.4, 1.0, 1.0)) for s in (-1, 1)]
    eyes = [S.sphere(f"{name}Eye{s}", 0.0018, (0.06, s * 0.0085, 0.034), dark, "structure", seg=8, rings=6)
            for s in (-1, 1)]
    tail_pts = [(-0.043 - 0.012 * k, 0.004 * math.sin(k * 0.9), 0.012 - 0.0016 * k) for k in range(9)]
    tail = S.tube(name + "Tail", tail_pts, 0.0022, pink, "structure", radii=[1 - 0.07 * k for k in range(9)])
    whiskers = []
    wm = _mat("MouseWhisker", (0.85, 0.85, 0.82), 0.4)
    for s in (-1, 1):
        for k in range(3):
            a = math.radians(-18 + 18 * k)
            p0 = (0.066, s * 0.004, 0.029)
            p1 = (0.07 + 0.012 * math.cos(a), s * (0.022 + 0.004 * k), 0.029 + 0.01 * math.sin(a))
            whiskers.append(S.tube(f"{name}Whisker{s}_{k}", [p0, p1], 0.0003, wm, "structure", res=1))
    # 胡须挂在一个空物体上，whisker_twitch 转它
    wroot = _root(name + "WhiskerRoot", (0.066, 0, 0.029))
    wroot.parent = root
    for wk in whiskers:
        wk.parent = wroot
        wk.location = Vector(wk.location) - Vector((0.066, 0, 0.029))
    head_root = _root(name + "HeadRoot", (0.035, 0, 0.028))
    head_root.parent = root
    for o in [head, nose] + ears + eyes:
        o.parent = head_root
        o.location = Vector(o.location) - Vector((0.035, 0, 0.028))
    wroot.parent = head_root
    wroot.location = (0.031, 0, 0.001)
    for o in (body, tail):
        o.parent = root
    return {"root": root, "body": body, "head": head, "head_root": head_root, "ears": ears, "eyes": eyes,
            "tail": tail, "whiskers": whiskers, "whisker_root": wroot, "nose": nose}


def mouse_walk(m, f0, f1, path):
    """小鼠沿 path（世界坐标点列，z 取地面）从 f0 走到 f1，朝向跟着前进方向，身体轻微起伏。"""
    r = m["root"]
    seg = [math.dist(path[i], path[i + 1]) for i in range(len(path) - 1)]
    tot = sum(seg) or 1.0
    for f in range(f0, f1 + 1, 2):
        u = S.smooth((f - f0) / max(1, f1 - f0)) * tot
        for i, L in enumerate(seg):
            if u <= L or i == len(seg) - 1:
                t = 0 if L == 0 else min(1.0, u / L)
                p = [path[i][k] + (path[i + 1][k] - path[i][k]) * t for k in range(3)]
                d = Vector(path[i + 1]) - Vector(path[i])
                break
            u -= L
        r.location = p
        r.rotation_euler = (0, 0, math.atan2(d.y, d.x))
        r.keyframe_insert("location", frame=f)
        r.keyframe_insert("rotation_euler", frame=f)
        b = m["body"]
        b.location = (0, 0, 0.024 + 0.0015 * math.sin(f * 1.3))
        b.keyframe_insert("location", frame=f)


def mouse_freeze(m, f, hold=48):
    """从帧 f 起停住：身体略收紧（压低、缩短），头微低，之后保持不动 hold 帧。"""
    b, h = m["body"], m["head_root"]
    S.key(b, f - 1, scale=(1.5, 1.0, 0.85), location=(0, 0, 0.024))
    S.key(h, f - 1, rotation_euler=(0, 0, 0))
    S.key(b, f + 8, scale=(1.38, 1.04, 0.8), location=(-0.003, 0, 0.022))
    S.key(h, f + 8, rotation_euler=(0, math.radians(8), 0))
    S.key(b, f + hold, scale=(1.38, 1.04, 0.8), location=(-0.003, 0, 0.022))
    S.key(h, f + hold, rotation_euler=(0, math.radians(8), 0))


def whisker_twitch(m, f0, f1, amp_deg=9.0, period=6):
    """f0→f1 胡须来回摆，头部和身体轻微偏转（B_15b：示意，不做眼部特写）。"""
    w, h = m["whisker_root"], m["head_root"]
    for f in range(f0, f1 + 1, max(1, period // 2)):
        k = (f - f0) // max(1, period // 2)
        a = math.radians(amp_deg) * (1 if k % 2 else -1)
        S.key(w, f, rotation_euler=(0, 0, a))
        S.key(h, f, rotation_euler=(0, 0, a * 0.25))
    S.key(w, f1 + 3, rotation_euler=(0, 0, 0))
    S.key(h, f1 + 3, rotation_euler=(0, 0, 0))


# ---- 光纤植入件 ------------------------------------------------------------------------------
# TODO(prop): 可换 Tripo/Meshy 道具（先在 research/visual/assets.yaml 记录）
def fiber_implant(name, tip, direction=(0, 0, -1), ferrule_len=0.008, cable_len=0.25, tag=None, fiber_len=0.004,
                  color=None):
    """陶瓷插芯（白，structure）+ 从插芯下端伸出的裸光纤（细，structure）+ 从插芯上端向上弯走的线缆（structure）。
    蓝光只在光纤尖端：tip_glow 是一个光晕球（S.halo，gain 初值 0，可打关键帧），beam 是尖端前方很短的一束示意光锥。
    tip 是光纤尖端的世界坐标，direction 是光纤指向（尖端朝向）。"""
    color = color or S.lin((142, 175, 255))
    d = Vector(direction).normalized()
    tip = Vector(tip)
    root = _root(name, tuple(tip))
    ceramic = _mat("FerruleCeramic", (0.92, 0.9, 0.86), 0.35)
    glass = _mat("FiberGlass", (0.75, 0.8, 0.85), 0.15)
    jacket = _mat("FiberJacket", (0.05, 0.05, 0.055), 0.5)    # 线缆深灰：蓝色只留给尖端的光
    f_top = tip - d * fiber_len
    fiber = S.between(name + "Fiber", tip, f_top, 0.0001, glass, "structure", verts=12)
    ferrule = S.between(name + "Ferrule", f_top, f_top - d * ferrule_len, 0.00125, ceramic, "structure", verts=24)
    sleeve = S.between(name + "Sleeve", f_top - d * ferrule_len * 0.55, f_top - d * ferrule_len * 1.15, 0.0017,
                       _mat("SleeveMetal", (0.6, 0.62, 0.65), 0.3, metallic=1.0), "structure", verts=24)
    c0 = f_top - d * ferrule_len * 1.1
    side = d.orthogonal().normalized()
    pts = [tuple(c0)]
    for k in range(1, 9):
        u = k / 8
        p = c0 - d * cable_len * 0.45 * math.sin(u * math.pi / 2) + side * cable_len * 0.6 * (1 - math.cos(u * math.pi / 2))
        pts.append(tuple(p))
    cable = S.tube(name + "Cable", pts, 0.0011, jacket, "structure")
    gm = S.halo(name + "TipGlowMat", color, 0.0)
    tip_glow = S.sphere(name + "TipGlow", 0.004, tuple(tip + d * 0.0003), gm, "emitter", seg=16, rings=8)
    beam, beam_mat = S.cone_beam(name + "Beam", tuple(tip), tuple(tip + d * 0.0025), 0.0009, color, 0.0)
    for o in (fiber, ferrule, sleeve, cable, tip_glow, beam):
        o.parent = root
        o.matrix_parent_inverse = root.matrix_world.inverted()
    return {"root": root, "ferrule": ferrule, "fiber": fiber, "cable": cable, "tip_glow": tip_glow,
            "tip_glow_mat": gm, "beam": beam, "beam_mat": beam_mat, "sleeve": sleeve, "tip": tuple(tip)}


# ---- 实验台 / 培养皿 / 电极 / 屏幕 ------------------------------------------------------------
# TODO(prop): 可换 Tripo/Meshy 道具（先在 research/visual/assets.yaml 记录）
def bench(name, size=(1.6, 0.8), height=0.0, tag=None, color=(0.16, 0.17, 0.18)):
    """风格化实验台：一块 3 cm 厚的台面（顶面在 z = height），四条方腿。台面 structure。"""
    w, d = size
    top = S.box(name + "Top", (0, 0, height - 0.015), (w, d, 0.03), _mat(name + "TopMat", color, 0.55),
                "structure", bevel=0.004)
    legs = [S.box(f"{name}Leg{i}", (sx * (w / 2 - 0.05), sy * (d / 2 - 0.05), height - 0.03 - 0.4), (0.04, 0.04, 0.8),
                  _mat("BenchLeg", (0.3, 0.31, 0.33), 0.4, metallic=0.8), "env")
            for i, (sx, sy) in enumerate(((-1, -1), (1, -1), (-1, 1), (1, 1)))]
    return {"top": top, "legs": legs, "height": height}


# TODO(prop): 可换 Tripo/Meshy 道具（先在 research/visual/assets.yaml 记录）
def dish(name, loc, r=0.045, tag=None, lid=True):
    """培养皿：薄底 + 侧壁（shell，透明），内有一层浅色培养液（structure）；lid=True 时盖子略抬起放在一边。"""
    root = _root(name, loc)
    glass = _mat("DishGlass", (0.9, 0.94, 0.97), 0.05, alpha=0.22, transmission=0.95)
    med = _mat("DishMedium", (0.95, 0.75, 0.72), 0.2, alpha=0.5)
    base = S.cylinder(name + "Base", r, 0.002, (0, 0, 0.001), glass, "shell", verts=64)
    # 侧壁：开口的薄壁环（无顶、底盖面），clay 下也不会把皿内东西盖住
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=0.012, location=(0, 0, 0.007), vertices=64,
                                        end_fill_type="NOTHING")
    wall = bpy.context.object
    wall.name = name + "Wall"
    wall.data.materials.append(glass)
    S.styles.tag(wall, "shell")
    sol = wall.modifiers.new("Shell", "SOLIDIFY")
    sol.thickness = 0.0008
    wall.data.polygons.foreach_set("use_smooth", [True] * len(wall.data.polygons))
    medium = S.cylinder(name + "Medium", r * 0.97, 0.003, (0, 0, 0.0035), med, "structure", verts=64)
    lid_ob = None
    parts = [base, wall, medium]
    if lid:
        lid_ob = S.cylinder(name + "Lid", r * 1.06, 0.0015, (r * 2.3, 0.0, 0.0008), glass, "shell", verts=64)
        parts.append(lid_ob)
    _parent(parts, root)
    return {"root": root, "base": base, "wall": wall, "lid": lid_ob, "medium": medium}


# TODO(prop): 可换 Tripo/Meshy 道具（先在 research/visual/assets.yaml 记录）
def electrode(name, tip, direction=(0, 0, -1), length=0.06, tag=None):
    """记录电极示意：一根细长金属杆（structure），尖端收细成锥（structure），杆尾有个夹持块。"""
    d = Vector(direction).normalized()
    tip = Vector(tip)
    root = _root(name, tuple(tip))
    metal = _mat("ElectrodeMetal", (0.7, 0.7, 0.72), 0.25, metallic=1.0)
    taper = 0.006
    bpy.ops.mesh.primitive_cone_add(radius1=0.0004, radius2=0.0, depth=taper, location=tuple(tip - d * taper / 2),
                                    vertices=16)
    tp = bpy.context.object
    tp.name = name + "Tip"
    tp.rotation_euler = (-d).to_track_quat("Z", "Y").to_euler()
    tp.data.materials.append(metal)
    S.styles.tag(tp, "structure")
    shaft = S.between(name + "Shaft", tip - d * taper, tip - d * length, 0.0004, metal, "structure", verts=12)
    holder = S.between(name + "Holder", tip - d * length, tip - d * (length + 0.02), 0.003,
                       _mat("ElectrodeHolder", (0.12, 0.12, 0.13), 0.5), "structure", verts=20)
    for o in (tp, shaft, holder):
        o.parent = root
        o.matrix_parent_inverse = root.matrix_world.inverted()
    return {"root": root, "shaft": shaft, "tip": tp, "holder": holder}


# TODO(prop): 可换 Tripo/Meshy 道具（先在 research/visual/assets.yaml 记录）
def screen(name, loc, size=(0.5, 0.3), facing=(0, -1, 0), tag=None):
    """通用显示器：暗色边框（structure）+ 暗屏面板（emission 很低，structure）。面板在边框前 2 mm。
    调用方用 S.trace 把活动痕迹画在面板前面（局部坐标：x 向右，z 向上，面板中心在 root 原点前方）。"""
    w, h = size
    f = Vector(facing).normalized()
    root = _root(name, loc, (0, 0, math.atan2(f.x, -f.y)))
    frame_m = _mat("ScreenFrame", (0.05, 0.05, 0.055), 0.4)
    frame = S.box(name + "Frame", (0, 0.01, 0), (w + 0.03, 0.02, h + 0.03), frame_m, "structure", bevel=0.004)
    pm = S.glow(name + "PanelMat", (0.006, 0.012, 0.02), 1.0)
    panel = S.box(name + "Panel", (0, -0.0015, 0), (w, 0.002, h), pm, "structure")
    stand = S.box(name + "Stand", (0, 0.03, -h / 2 - 0.08), (0.04, 0.03, 0.16), frame_m, "structure")
    foot = S.box(name + "Foot", (0, 0.03, -h / 2 - 0.16), (0.2, 0.14, 0.012), frame_m, "structure")
    _parent([frame, panel, stand, foot], root)
    return {"root": root, "frame": frame, "panel": panel, "panel_mat": pm, "size": size}


# ---- 护目镜 ----------------------------------------------------------------------------------
# TODO(prop): 可换 Tripo/Meshy 道具（先在 research/visual/assets.yaml 记录）
def goggles(name, loc=(0, 0, 0), rot=(0, 0, 0), scale=1.0, tag=None, lens_color=(0.6, 0.75, 1.0)):
    """通用造型的护目镜：两片圆角矩形镜片（各一个发光材质，'Emission' 强度可打关键帧，初值很低），
    包住镜片的框（structure），两侧绕到后面的软带（structure）。局部坐标：镜片朝 -Y，宽约 0.16 m。"""
    root = _root(name, loc, rot)
    root.scale = (scale,) * 3
    frame_m = _mat("GoggleFrame", (0.07, 0.075, 0.08), 0.35)
    strap_m = _mat("GoggleStrap", (0.12, 0.12, 0.13), 0.8)
    lenses, mats, frames = [], [], []
    for i, s in enumerate((-1, 1)):
        lm = S.glow(f"{name}LensMat{i}", lens_color, 0.05)
        lens = S.box(f"{name}Lens{i}", (s * 0.038, -0.002, 0), (0.06, 0.003, 0.04), lm, "emitter", bevel=0.008)
        fr = S.box(f"{name}Rim{i}", (s * 0.038, 0.004, 0), (0.07, 0.014, 0.05), frame_m, "structure", bevel=0.01)
        lenses.append(lens)
        mats.append(lm)
        frames.append(fr)
    bridge = S.box(name + "Bridge", (0, 0.004, 0.004), (0.02, 0.012, 0.014), frame_m, "structure", bevel=0.004)
    frames.append(bridge)
    pts = [(0.072, 0.006, 0)] + [(0.085 * math.cos(a), 0.006 + 0.09 * math.sin(a), 0)
                                  for a in [math.radians(t) for t in range(10, 171, 20)]] + [(-0.072, 0.006, 0)]
    strap = S.tube(name + "Strap", pts, 0.006, strap_m, "structure", res=1)
    strap.data.bevel_depth = 0.0
    strap.data.extrude = 0.009
    _parent(lenses + frames + [strap], root)
    return {"root": root, "frame": frames, "lenses": lenses, "lens_mats": mats, "strap": strap}
