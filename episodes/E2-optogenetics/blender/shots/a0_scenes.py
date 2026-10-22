"""E2 A0 — 冷开场的 Blender 镜头（一个模块，多个 variant；只有一个 after_style，内部按 variant 分支，见 WORKFLOW 9）：

  paper      A0_01a / A0_02b  documentary / Cycles：暗室木桌上一页略泛黄的纸，一道掠射窄光只照亮其中一行，光束里有浮尘。
                              纸上是程序生成的不可读笔画行（不排任何文字，不冒充 Crick 原稿）。01a 慢推，02b 同一场景近景，亮行渐暗。
  neurons    A0_03b           clay / EEVEE：9 个参数化神经元白模（build_neuron.py），只有被圈的一类沿轴突起伏亮起。
  laureates  A0_04a           energy / EEVEE：三个抽象光点依次亮起、缓慢漂移，彼此有细光丝相连，镜头慢推。
                              名字和日期行由 mograph/a0.py 的 A0_04a 后处理叠到帧上（Blender 的文字对象读不了 .ttc 的 SC 字面）。
  membrane   A0_91            sem / Cycles：紫膜二维晶格（build_purple_membrane.py），1.5 秒轻微横移。

颜色、相机运动、排布等共用常量在 blender/scripts/e2_common.py。全部示意，没有人物。
"""
import math
import random

import bpy
from mathutils import Vector

import build_neuron as BN
import build_purple_membrane as BP
import common as C
import e2_common as E
import materials as M
import styles

FRAMES = 560
FPS = 24


# ---- 小工具 --------------------------------------------------------------------------------
def _lin(c):
    return E.srgb_to_linear(c)


def _key(ob, f, **kw):
    for k, v in kw.items():
        setattr(ob, k, v)
        ob.keyframe_insert(k, frame=f)


def _linear_interp(ob):
    """把物体上所有关键帧改成线性插值（浮尘缓慢匀速漂移用）。"""
    if ob.animation_data and ob.animation_data.action:
        for fc in C.fcurves(ob.animation_data.action):
            for kp in fc.keyframe_points:
                kp.interpolation = "LINEAR"


def _camera(name, keys, parent=None, dof=True):
    """keys: (frame, aim, location, lens, fstop)。aim 空物体同时是对焦目标。parent 下的坐标是局部坐标。"""
    bpy.ops.object.empty_add(location=(0, 0, 0))
    aim = bpy.context.object
    aim.name = name + "Aim"
    bpy.ops.object.camera_add()
    cam = bpy.context.object
    cam.name = name
    if parent is not None:
        aim.parent = parent
        cam.parent = parent
    t = cam.constraints.new("TRACK_TO")
    t.target = aim
    t.track_axis = "TRACK_NEGATIVE_Z"
    t.up_axis = "UP_Y"
    cam.data.sensor_width = 36
    cam.data.clip_start = 0.01
    cam.data.clip_end = 400
    cam.data.dof.use_dof = dof
    cam.data.dof.focus_object = aim
    for f, a, loc, lens, fstop in keys:
        _key(aim, f, location=a)
        _key(cam, f, location=loc)
        cam.data.lens = lens
        cam.data.keyframe_insert("lens", frame=f)
        cam.data.dof.aperture_fstop = fstop
        cam.data.dof.keyframe_insert("aperture_fstop", frame=f)
    return cam


def _node(nt, kind, **kw):
    n = nt.nodes.new(kind)
    for k, v in kw.items():
        setattr(n, k, v)
    return n


def _halo(name, color, size_gain=1.0):
    """软光晕：球心最亮，向边缘平方衰减；叠加在透明上，强度可在节点 'Gain' 上打关键帧（0=熄灭）。"""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.remove(nt.nodes["Principled BSDF"])
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    dot = _node(nt, "ShaderNodeVectorMath", operation="DOT_PRODUCT")
    nt.links.new(geo.outputs["Normal"], dot.inputs[0])
    nt.links.new(geo.outputs["Incoming"], dot.inputs[1])
    ab = _node(nt, "ShaderNodeMath", operation="ABSOLUTE")
    nt.links.new(dot.outputs["Value"], ab.inputs[0])
    pw = _node(nt, "ShaderNodeMath", operation="POWER")           # 球心 1 -> 边缘 0，高次幂 = 柔和的光晕
    pw.inputs[1].default_value = 5.0
    nt.links.new(ab.outputs[0], pw.inputs[0])
    gain = _node(nt, "ShaderNodeMath", operation="MULTIPLY")
    gain.name = "Gain"
    gain.inputs[1].default_value = 0.0
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*color, 1)
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    add = nt.nodes.new("ShaderNodeAddShader")
    nt.links.new(pw.outputs[0], gain.inputs[0])
    nt.links.new(gain.outputs[0], em.inputs["Strength"])
    nt.links.new(tr.outputs[0], add.inputs[0])
    nt.links.new(em.outputs[0], add.inputs[1])
    nt.links.new(add.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
    m.surface_render_method = "BLENDED"
    return m


def _set_gain(mat, frame, v):
    g = mat.node_tree.nodes["Gain"].inputs[1]
    g.default_value = v
    g.keyframe_insert("default_value", frame=frame)


def _cycles(sc, spp, bounces=4, clamp=4.0):
    """final 要在 60 秒/帧内：采样数按质量档给（preview / sample / final），降噪用 OpenImageDenoise。"""
    q = "preview" if sc.render.resolution_x <= 640 else "sample" if sc.render.resolution_x <= 960 else "final"
    cy = sc.cycles
    cy.samples = spp[q]
    cy.use_adaptive_sampling = True
    cy.adaptive_threshold = 0.03
    cy.use_denoising = True
    cy.denoiser = "OPENIMAGEDENOISE"
    cy.max_bounces = bounces
    cy.diffuse_bounces = bounces
    cy.glossy_bounces = 2
    cy.transmission_bounces = 2
    cy.volume_bounces = 1
    cy.caustics_reflective = cy.caustics_refractive = False
    cy.sample_clamp_indirect = clamp
    cy.volume_step_rate = 2.0
    cy.volume_max_steps = 96
    return q


# ---- paper：A0_01a / A0_02b ------------------------------------------------------------------
PAPER_FRAME_02B = 201            # 02b 在同一场景的 201–233 帧：亮行在 1.35 秒里暗下
RIG_ROT = math.radians(-4.0)     # 整个纸页装置相对桌面转几度，木纹因此不与纸平行
INK_PX_PER_MM = 12


def _ink_array(rnd):
    """程序生成的不可读笔画行：每行若干“词”，每词由短横线、竖笔、斜笔拼成。返回 (H, W) float 数组，1 = 墨，
    第 0 行是纸的上端。"""
    import numpy as np
    wmm, hmm = E.PAPER_SIZE_M[0] * 1000, E.PAPER_SIZE_M[1] * 1000
    W, H = int(wmm * INK_PX_PER_MM), int(hmm * INK_PX_PER_MM)
    img = np.zeros((H, W), np.float32)
    px = INK_PX_PER_MM
    lw = 0.7 * px                                           # 笔画宽 0.7 mm

    def seg(x0, y0, x1, y1, a):
        xa, xb = int(max(0, min(x0, x1) - lw - 2)), int(min(W, max(x0, x1) + lw + 3))
        ya, yb = int(max(0, min(y0, y1) - lw - 2)), int(min(H, max(y0, y1) + lw + 3))
        if xb <= xa or yb <= ya:
            return
        yy, xx = np.mgrid[ya:yb, xa:xb].astype(np.float32)
        dx, dy = x1 - x0, y1 - y0
        L2 = dx * dx + dy * dy or 1.0
        t = np.clip(((xx - x0) * dx + (yy - y0) * dy) / L2, 0, 1)
        d = np.hypot(xx - (x0 + t * dx), yy - (y0 + t * dy))
        cov = np.clip(lw / 2 + 0.7 - d, 0, 1) * a
        img[ya:yb, xa:xb] = np.maximum(img[ya:yb, xa:xb], cov)

    margin, pitch = 18.0, E.PAPER_ROW_PITCH_M * 1000
    for row in range(26):
        yc = (22.0 + row * pitch) * px                       # 从纸的上端往下数（图像坐标，y 向下）
        if row in (7, 17, 18) and row != E.PAPER_LIT_ROW:      # 空行，分段落
            continue
        x = margin + (6 if row in (0, 8, 19) else 0)         # 段首缩进
        x_end = wmm - margin - (rnd.uniform(0, 60) if row in (6, 16, 25) else rnd.uniform(0, 6))
        if row == E.PAPER_LIT_ROW:
            x, x_end = margin, wmm - margin
        slope = rnd.uniform(-0.6, 0.6) / wmm * px            # 一行略微倾斜
        while x < x_end:
            word_end = min(x_end, x + rnd.uniform(8, 32))
            a = rnd.uniform(0.7, 1.0)
            while x < word_end:
                slot = rnd.uniform(1.5, 2.7)
                y0 = yc + slope * (x * px) + rnd.uniform(-0.35, 0.35) * px
                kind = rnd.random()
                if kind < 0.55:                              # 短横
                    ln = slot * rnd.uniform(0.65, 1.0)
                    seg(x * px, y0, (x + ln) * px, y0 + rnd.uniform(-0.25, 0.25) * px, a)
                elif kind < 0.8:                             # 竖笔
                    h = rnd.uniform(1.6, 3.2)
                    seg(x * px, y0 + 0.8 * px, x * px + rnd.uniform(-0.2, 0.3) * px, y0 - h * px * 0.6, a)
                else:                                        # 斜笔
                    seg(x * px, y0 + 0.6 * px, (x + slot * 0.8) * px, y0 - 0.9 * px, a)
                x += slot
            x += rnd.uniform(2.4, 4.2)                       # 词间空
    return img


def _ink_image(rnd):
    """把 _ink_array 的结果放进 bpy 图像（R 通道是墨的覆盖度）。"""
    import numpy as np
    img = _ink_array(rnd)
    H, W = img.shape
    rgba = np.zeros((H, W, 4), np.float32)
    rgba[..., 0] = rgba[..., 1] = rgba[..., 2] = img[::-1]   # Blender 图像原点在左下
    rgba[..., 3] = 1.0
    im = bpy.data.images.new("PaperInk", W, H, alpha=False)
    im.colorspace_settings.name = "Non-Color"                # 先设色彩空间再写像素（之后改会清空缓冲）
    im.pixels.foreach_set(rgba.ravel())
    im.update()
    return im


def _paper_material(ink):
    m = bpy.data.materials.new("Paper")
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    L = nt.links.new
    tc = nt.nodes.new("ShaderNodeTexCoord")
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = ink
    tex.extension = "CLIP"
    tex.interpolation = "Cubic"
    L(tc.outputs["UV"], tex.inputs["Vector"])
    # 纸色：泛黄，边缘更黄更暗（年久），带细纤维色斑
    noise = _node(nt, "ShaderNodeTexNoise", noise_dimensions="3D")
    noise.inputs["Scale"].default_value = 260
    noise.inputs["Detail"].default_value = 8
    L(tc.outputs["Object"], noise.inputs["Vector"])
    big = _node(nt, "ShaderNodeTexNoise", noise_dimensions="3D")
    big.inputs["Scale"].default_value = 9
    big.inputs["Detail"].default_value = 3
    L(tc.outputs["Object"], big.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (0.50, 0.38, 0.17, 1)
    ramp.color_ramp.elements[1].color = (0.80, 0.69, 0.42, 1)
    ramp.color_ramp.elements[0].position = 0.30
    ramp.color_ramp.elements[1].position = 0.72
    L(big.outputs["Fac"], ramp.inputs["Fac"])
    fib = _node(nt, "ShaderNodeMix", data_type="RGBA", blend_type="MULTIPLY")
    fib.inputs["Factor"].default_value = 0.18
    L(ramp.outputs["Color"], fib.inputs["A"])
    L(noise.outputs["Color"], fib.inputs["B"])
    ink_col = nt.nodes.new("ShaderNodeRGB")
    ink_col.outputs[0].default_value = (0.022, 0.017, 0.014, 1)
    mix = _node(nt, "ShaderNodeMix", data_type="RGBA")
    L(tex.outputs["Color"], mix.inputs["Factor"])
    L(fib.outputs["Result"], mix.inputs["A"])
    L(ink_col.outputs[0], mix.inputs["B"])
    L(mix.outputs["Result"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.88
    b.inputs["Specular IOR Level"].default_value = 0.25
    # 凹凸：纤维 + 墨迹微微隆起（掠射光下能看出质感）
    add = _node(nt, "ShaderNodeMath", operation="ADD")
    L(noise.outputs["Fac"], add.inputs[0])
    L(tex.outputs["Color"], add.inputs[1])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.45
    bump.inputs["Distance"].default_value = 0.0003
    L(add.outputs[0], bump.inputs["Height"])
    L(bump.outputs["Normal"], b.inputs["Normal"])
    return m


def _desk_material():
    m = bpy.data.materials.new("Desk")
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    L = nt.links.new
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (3.0, 28.0, 3.0)      # 木纹沿 x 拉长
    L(tc.outputs["Object"], mp.inputs["Vector"])
    wave = _node(nt, "ShaderNodeTexWave", wave_type="BANDS", bands_direction="Y")
    wave.inputs["Scale"].default_value = 1.0
    wave.inputs["Distortion"].default_value = 7.0
    wave.inputs["Detail"].default_value = 3.0
    wave.inputs["Detail Scale"].default_value = 1.5
    L(mp.outputs["Vector"], wave.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (0.010, 0.005, 0.0025, 1)
    ramp.color_ramp.elements[1].color = (0.060, 0.032, 0.015, 1)
    L(wave.outputs["Fac"], ramp.inputs["Fac"])
    L(ramp.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.42
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.25
    bump.inputs["Distance"].default_value = 0.002
    L(wave.outputs["Fac"], bump.inputs["Height"])
    L(bump.outputs["Normal"], b.inputs["Normal"])
    return m


def _paper_mesh(rig, mat, rnd):
    import bmesh
    from mathutils import noise
    wd, hd = E.PAPER_SIZE_M
    nx, ny = 70, 98
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UV")
    off = rnd.uniform(0, 50)
    grid = []
    for j in range(ny + 1):
        row = []
        for i in range(nx + 1):
            x = (i / nx - 0.5) * wd
            y = (j / ny - 0.5) * hd
            z = (0.0003 + 0.0012 * (x / (wd / 2)) ** 2 + 0.0004 * (y / (hd / 2)) ** 2   # 微微拱起
                 + 0.0002 * noise.noise(Vector((x * 22 + off, y * 22, 1.3)))
                 + 0.00012 * noise.noise(Vector((x * 120, y * 120 + off, 4.1))))
            row.append(bm.verts.new((x, y, z)))
        grid.append(row)
    for j in range(ny):
        for i in range(nx):
            f = bm.faces.new((grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]))
            f.smooth = True
            for lp in f.loops:
                lp[uv].uv = (lp.vert.co.x / wd + 0.5, lp.vert.co.y / hd + 0.5)
    me = bpy.data.meshes.new("Paper")
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new("Paper", me)
    bpy.context.scene.collection.objects.link(ob)
    ob.parent = rig
    ob.data.materials.append(mat)
    sol = ob.modifiers.new("Thick", "SOLIDIFY")
    sol.thickness = 0.00022
    sol.offset = -1
    return ob


def paper(sc, rnd):
    C.set_world(top=(0.0016, 0.0018, 0.0024), horizon=(0.0008, 0.0009, 0.0012), bottom=(0, 0, 0))
    C.set_color_management(look="Base Contrast", exposure=0.0)
    sc["variant"] = "paper"
    bpy.ops.object.empty_add(location=(0, 0, 0), rotation=(0, 0, RIG_ROT))
    rig = bpy.context.object
    rig.name = "PaperRig"
    wd, hd = E.PAPER_SIZE_M
    yr = hd / 2 - 0.022 - E.PAPER_LIT_ROW * E.PAPER_ROW_PITCH_M      # 被照亮那一行的 y（纸坐标）
    sc["lit_row_y"] = yr
    # 桌面
    bpy.ops.mesh.primitive_plane_add(size=2.4, location=(0, 0, 0), rotation=(0, 0, math.radians(11)))
    desk = bpy.context.object
    desk.name = "Desk"
    desk.data.materials.append(_desk_material())
    # 纸
    ink = _ink_image(rnd)
    _paper_mesh(rig, _paper_material(ink), rnd)

    # 掠射窄光：点状聚光灯 + 一道窄缝挡板。灯与缝都在一条通过亮行的射线上，射线对纸面的仰角约 14.6°，
    # 缝宽 2.5 mm，所以只有纸上约 7–8 mm 宽的一条（≈ 一行）被照亮，射线在空气里形成一片薄光幕，浮尘穿过时被照出。
    target = Vector((0, yr, 0.0))
    lamp = Vector((0, yr + 0.50, 0.13))
    wall_y = yr + 0.26
    wall_z = 0.13 * (wall_y - yr) / (lamp.y - yr)
    gap = 0.0025
    for nm, z0, z1 in (("SlitLow", -0.02, wall_z - gap / 2), ("SlitHigh", wall_z + gap / 2, 0.8)):
        bpy.ops.mesh.primitive_cube_add(location=(0, wall_y, (z0 + z1) / 2))
        w = bpy.context.object
        w.name = nm
        w.scale = (0.45, 0.004, (z1 - z0) / 2)
        w.parent = rig
        w.data.materials.append(M.principled(nm + "Mat", (0.01, 0.01, 0.01), roughness=0.9))
        w.visible_glossy = False                              # 黑色哑光，在暗处看不见；但要入镜，不然会透过它直接看到灯
        styles.tag(w, "rig")
    ratio = (lamp.y - yr) / (lamp.y - wall_y)                 # 灯点发散：纸上的宽度 = 缝上宽度 × ratio
    x_edge = (wd / 2 - 0.004) / ratio
    for sgn in (-1, 1):                                       # 缝两端的挡块：光幕刚好和纸一样宽，不照到桌面上
        bpy.ops.mesh.primitive_cube_add(location=(sgn * (x_edge + 0.2), wall_y - 0.006, wall_z))
        sh = bpy.context.object
        sh.name = f"Shutter{sgn}"
        sh.scale = (0.2, 0.004, 0.01)
        sh.parent = rig
        sh.data.materials.append(M.principled("ShutterMat", (0.01, 0.01, 0.01), roughness=0.9))
        styles.tag(sh, "rig")
    bpy.ops.object.light_add(type="SPOT", location=lamp)
    lt = bpy.context.object
    lt.name = "SlitLight"
    lt.parent = rig
    lt.rotation_euler = (target - lamp).to_track_quat("-Z", "Y").to_euler()
    lt.data.spot_size = math.radians(32)
    lt.data.spot_blend = 0.2
    lt.data.shadow_soft_size = 0.0035
    lt.data.color = (1.0, 0.90, 0.74)
    lt.data.energy = 70.0
    lt["keep_light"] = 1
    lt.visible_camera = False
    # 室内极弱的底光：让未被照亮的纸边和桌面隐约可辨（亮行 : 其余 ≈ 30 : 1），不然画面里只有一条亮线
    bpy.ops.object.light_add(type="AREA", location=(-0.5, -0.55, 0.55))
    rf = bpy.context.object
    rf.name = "RoomFill"
    rf.data.size = 0.8
    rf.data.energy = 0.6
    rf.data.color = (1.0, 0.82, 0.6)
    rf["keep_light"] = 1
    rf.rotation_euler = (Vector((0, 0, 0)) - rf.location).to_track_quat("-Z", "Y").to_euler()
    sc["slit_light"] = lt.name
    # 02b：201–205 帧保持，之后按指数曲线暗到 4%（1.35 秒）
    for f in range(PAPER_FRAME_02B - 10, PAPER_FRAME_02B + 33):
        u = max(0.0, (f - (PAPER_FRAME_02B + 3)) / 29.0)
        lt.data.energy = 70.0 * (1.0 - 0.96 * u * u * (3 - 2 * u)) if f >= PAPER_FRAME_02B else 70.0
        lt.data.keyframe_insert("energy", frame=f)
    # 空气里的薄尘：一个方盒里的低密度噪声体积 + 一些被光幕照亮的小颗粒
    bpy.ops.mesh.primitive_cube_add(location=(0, yr + 0.065, 0.11))
    vol = bpy.context.object
    vol.name = "DustVolume"
    vol.scale = (0.26, 0.185, 0.11)           # y 只到挡板前面（挡板后面的体积会被灯直接照亮）
    vol.parent = rig
    vm = bpy.data.materials.new("Dust")
    vm.use_nodes = True
    nt = vm.node_tree
    nt.nodes.remove(nt.nodes["Principled BSDF"])
    pv = nt.nodes.new("ShaderNodeVolumePrincipled")
    pv.inputs["Color"].default_value = (1.0, 0.95, 0.85, 1)
    pv.inputs["Anisotropy"].default_value = 0.35
    nz = _node(nt, "ShaderNodeTexNoise", noise_dimensions="3D")
    nz.inputs["Scale"].default_value = 34.0
    nz.inputs["Detail"].default_value = 4.0
    rp = nt.nodes.new("ShaderNodeMapRange")
    rp.inputs["From Min"].default_value = 0.42
    rp.inputs["From Max"].default_value = 0.75
    rp.inputs["To Max"].default_value = 1.6
    tcv = nt.nodes.new("ShaderNodeTexCoord")
    nt.links.new(tcv.outputs["Object"], nz.inputs["Vector"])
    nt.links.new(nz.outputs["Fac"], rp.inputs["Value"])
    nt.links.new(rp.outputs["Result"], pv.inputs["Density"])
    nt.links.new(pv.outputs[0], nt.nodes["Material Output"].inputs["Volume"])
    vol.data.materials.append(vm)
    vol.display_type = "WIRE"
    vol.visible_shadow = False
    styles.tag(vol, "rig")
    mote_mat = M.principled("Mote", (0.85, 0.82, 0.75), roughness=0.6)
    for i in range(190):
        t = rnd.uniform(0.04, 0.97)                          # 在缝与纸之间的射线上取点
        slit_pt = Vector((0, wall_y, wall_z))
        p = slit_pt + (target - slit_pt) * t
        p = Vector((rnd.uniform(-0.22, 0.22), p.y, p.z))
        if rnd.random() < 0.7:
            p.z += rnd.uniform(-0.0016, 0.0016)               # 大多数落在光幕里
        else:
            p.z += rnd.uniform(-0.03, 0.03)
        r = rnd.uniform(0.00025, 0.0007)
        bpy.ops.mesh.primitive_ico_sphere_add(radius=r, subdivisions=1, location=p)
        mote = bpy.context.object
        mote.name = f"Mote{i}"
        mote.parent = rig
        mote.data.materials.append(mote_mat)
        d = Vector((rnd.uniform(-0.004, 0.004), rnd.uniform(-0.01, 0.01), rnd.uniform(-0.008, 0.002)))
        _key(mote, 1, location=p)
        _key(mote, 260, location=p + d)
        _linear_interp(mote)
        styles.tag(mote, "structure")

    aim_y = yr + 0.02
    # 01a：50 mm 慢推（机位在桌前左侧，斜着看亮行，光幕在尘里侧向可见）
    _camera("CamA0_01a", [(1, (0.0, aim_y, 0.004), (-0.13, aim_y - 0.37, 0.14), 50, 2.8),
                          (92, (0.0, aim_y, 0.004), (-0.08, aim_y - 0.27, 0.10), 50, 2.8)], parent=rig)
    # 02b：同一场景近景，机位固定
    _camera("CamA0_02b", [(PAPER_FRAME_02B, (0.01, aim_y, 0.003), (-0.07, aim_y - 0.17, 0.065), 50, 2.0)], parent=rig)


# ---- neurons：A0_03b -------------------------------------------------------------------------
def _clay_default():
    return styles.clay_material()


def neurons(sc, rnd):
    sc["variant"] = "neurons"
    sc["spacing"] = BN.SPACING
    clay = _clay_default()
    glow = _lin(E.CHANNEL)
    bead_mat = M.emission("PulseBead", glow, 9.0)
    ring_mat = M.emission("CircleRing", (0.06, 0.06, 0.065), 1.0)
    half = _halo("SomaHalo", glow)
    bouton_halo = _halo("BoutonHalo", glow)
    n = E.NEURON_COUNT
    xs = [(i - (n - 1) / 2) * BN.SPACING for i in range(n)]
    ys = [rnd.uniform(-0.18, 0.18) for _ in range(n)]
    F0, F_END = 1, 32
    cells = []
    for i in range(n):
        origin = (xs[i], ys[i], 0.0)
        cell = BN.build_neuron(f"N{i}", E.NEURON_SEEDS[i], origin, clay, tag=styles.tag)
        cells.append(cell)
        if i not in E.NEURON_CIRCLED:
            continue
        # 被圈出的一类：细环 + 沿轴突的亮点（起伏）+ 胞体和终末小结的光晕
        bpy.ops.mesh.primitive_torus_add(major_radius=0.46, minor_radius=0.006, major_segments=64, minor_segments=6,
                                         location=origin, rotation=(math.pi / 2, 0, 0))
        ring = bpy.context.object
        ring.name = f"Ring{i}"
        ring.data.materials.append(ring_mat)
        styles.tag(ring, "emitter")
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.30, segments=24, ring_count=14, location=origin)
        hs = bpy.context.object
        hs.name = f"SomaHalo{i}"
        hm = half.copy()
        hs.data.materials.append(hm)
        styles.tag(hs, "emitter")
        hs.hide_render = True
        _key(hs, 1, hide_render=True)
        _key(hs, 3, hide_render=False)
        _set_gain(hm, 1, 0.0)
        _set_gain(hm, 3, 0.0)
        _set_gain(hm, 7, 2.6)
        _set_gain(hm, 20, 1.2)
        _set_gain(hm, 32, 0.0)
        so = cell["soma"]                                    # 胞体鼓一下
        _key(so, 1, scale=(1.0, 0.92, 1.05))
        _key(so, 7, scale=(1.18, 1.08, 1.24))
        _key(so, 20, scale=(1.04, 0.96, 1.09))
        _key(so, 32, scale=(1.0, 0.92, 1.05))
        # 沿轴突的起伏亮点：椭球，朝向跟着轴突切线
        path = [(origin[0] + p[0], origin[1] + p[1], origin[2] + p[2]) for p in BN.axon_path(cell["morph"])]
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.062, segments=20, ring_count=12, location=path[0])
        bead = bpy.context.object
        bead.name = f"Bead{i}"
        bead.scale = (1.0, 1.0, 2.4)
        bead.rotation_mode = "QUATERNION"
        bead.data.materials.append(bead_mat)
        styles.tag(bead, "emitter")
        for f in range(F0, F_END + 1):
            u = max(0.0, min(1.0, (f - 5) / 18.0))
            u = u * u * (3 - 2 * u)
            p, t = BN.path_at(path, u)
            _key(bead, f, location=p, rotation_quaternion=Vector((0, 0, 1)).rotation_difference(Vector(t)),
                 hide_render=(f < 5 or f > 25))
        for k, b in enumerate(cell["boutons"]):              # 终末小结在脉冲到达后亮起
            bpy.ops.mesh.primitive_uv_sphere_add(radius=0.16, segments=16, ring_count=10, location=b.location)
            bh = bpy.context.object
            bh.name = f"BoutonGlow{i}_{k}"
            bm_ = bouton_halo.copy()
            bh.data.materials.append(bm_)
            styles.tag(bh, "emitter")
            _set_gain(bm_, 1, 0.0)
            _set_gain(bm_, 20, 0.0)
            _set_gain(bm_, 26, 7.0)
            _set_gain(bm_, 32, 4.0)
    # 灯光：左上主光 + 右前补光（clay 风格会保留）
    for nm, loc, rot, size, e in (("Key", (-5, -9, 8), (math.radians(62), 0, math.radians(-25)), 9, 1200),
                                  ("Fill", (7, -8, 2), (math.radians(80), 0, math.radians(40)), 12, 380)):
        bpy.ops.object.light_add(type="AREA", location=loc, rotation=rot)
        lt = bpy.context.object
        lt.name = nm
        lt.data.size = size
        lt.data.energy = e
        lt.data.color = (1.0, 0.97, 0.92)
    _camera("CamA0_03b", [(1, (0, 0, -0.34), (0, -11.4, -0.34), 35, 22.0)], dof=False)


# ---- laureates：A0_04a ------------------------------------------------------------------------
def _cyl_y(name, r, mat):
    """沿 +Y 从 0 到 1 的细圆柱（STRETCH_TO 的约定：长度沿局部 Y）。"""
    import bmesh
    bm = bmesh.new()
    seg = 6
    a = [bm.verts.new((r * math.cos(2 * math.pi * s / seg), 0, r * math.sin(2 * math.pi * s / seg))) for s in range(seg)]
    b = [bm.verts.new((r * math.cos(2 * math.pi * s / seg), 1, r * math.sin(2 * math.pi * s / seg))) for s in range(seg)]
    for s in range(seg):
        bm.faces.new((a[s], a[(s + 1) % seg], b[(s + 1) % seg], b[s]))
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    ob.data.materials.append(mat)
    return ob


def laureates(sc, rnd):
    sc["variant"] = "laureates"
    sc.frame_end = FRAMES
    dur = E.A04_DUR
    n_f = int(dur * FPS) + 1
    glow = _lin(E.CHANNEL)
    white = (0.78, 0.88, 1.0)
    lit_f = [1 + round(t * FPS) for t in E.A04_LIGHT_AT]
    orbs, cores, halos = [], [], []
    for i in range(3):
        core_m = M.emission(f"OrbCore{i}", white, 0.0)
        halo_m = _halo(f"OrbHalo{i}", glow)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.05, segments=48, ring_count=24, location=E.a04_orb(i, 0))
        core = bpy.context.object
        core.name = f"Orb{i}"
        core.data.materials.append(core_m)
        styles.tag(core, "emitter")
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.5, segments=32, ring_count=16, location=(0, 0, 0))
        halo = bpy.context.object
        halo.name = f"OrbHalo{i}"
        for o_ in (core, halo):
            for pl in o_.data.polygons:
                pl.use_smooth = True
        halo.parent = core
        halo.data.materials.append(halo_m)
        styles.tag(halo, "emitter")
        for f in range(1, n_f + 1, 6):
            _key(core, f, location=E.a04_orb(i, (f - 1) / FPS))
        f0 = lit_f[i]
        M.set_emission_strength(core_m, f0 - 1, 0.0)           # 亮起：0.5 秒内升到 24，再回落到 14
        M.set_emission_strength(core_m, f0 + 12, 24.0)
        M.set_emission_strength(core_m, f0 + 30, 14.0)
        _set_gain(halo_m, f0 - 1, 0.0)
        _set_gain(halo_m, f0 + 14, 1.6)
        _set_gain(halo_m, f0 + 40, 0.9)
        orbs.append(core)
        cores.append(core_m)
        halos.append(halo_m)
    # 光丝：每对光点之间 3 根细线，端点是挂在光点上的小空物体（偏移不同），所以丝会随漂移轻微交织
    fil_mat = []
    pairs = ((0, 1, lit_f[1] + 8), (1, 2, lit_f[2] + 8), (0, 2, lit_f[2] + 26))
    for pi, (a, b, f0) in enumerate(pairs):
        fm = M.emission(f"Filament{pi}", glow, 0.0)
        M.set_emission_strength(fm, f0 - 1, 0.0)
        M.set_emission_strength(fm, f0 + 20, 3.2)
        fil_mat.append(fm)
        for k in range(3):
            ends = []
            for host in (orbs[a], orbs[b]):
                bpy.ops.object.empty_add(location=(0, 0, 0))
                em = bpy.context.object
                em.name = f"FilEnd{pi}_{k}_{host.name}"
                em.parent = host
                em.location = (rnd.uniform(-0.14, 0.14), rnd.uniform(-0.14, 0.14), rnd.uniform(-0.14, 0.14)) if k else (0, 0, 0)
                ends.append(em)
            cyl = _cyl_y(f"Fil{pi}_{k}", 0.0035 if k == 0 else 0.0022, fm)
            styles.tag(cyl, "emitter")
            cyl.parent = ends[0]
            st = cyl.constraints.new("STRETCH_TO")
            st.target = ends[1]
            st.volume = "NO_VOLUME"
            st.rest_length = 1.0                               # 网格长 1，缩放 = 两端距离
    # 镜头：缓慢推进
    cam = _camera("CamA0_04a", [(1, E.a04_camera(0)[1], E.a04_camera(0)[0], E.A04_FOCAL_MM, 4.0)], dof=False)
    for f in range(1, n_f + 1, 8):
        loc, aim = E.a04_camera((f - 1) / FPS)
        _key(cam, f, location=loc)
        _key(bpy.data.objects["CamA0_04aAim"], f, location=aim)


# ---- membrane：A0_91 --------------------------------------------------------------------------
def membrane(sc, rnd):
    sc["variant"] = "membrane"
    lip, hel = BP.build_membrane(half_w=330.0, half_h=300.0)
    styles.tag(lip, "structure")
    styles.tag(hel, "structure")
    # 机位：斜上方 52° 俯视，50 mm，1.5 秒横移约 0.45 个晶胞
    _camera("CamA0_91", [(1, (-0.18, 0.0, 0.0), (-0.18, -1.55, 2.75), 50, 8.0),
                         (36, (0.20, 0.0, 0.0), (0.20, -1.55, 2.75), 50, 8.0)], dof=False)


# ---- 风格后处理（一个模块一个 after_style）-------------------------------------------------------
def after_style(style, shot_id):
    sc = bpy.context.scene
    v = sc.get("variant")
    if v == "paper":
        _cycles(sc, {"preview": 24, "sample": 40, "final": 32}, bounces=4)
        sc.render.use_motion_blur = False
        sc.cycles.volume_step_rate = 4.0
        sc["film_grain"], sc["vignette"] = 0.3, 0.45                                # 低照度纪实：细颗粒 + 轻暗角
        sc["no_glare"] = True                                                       # L2 Document 不开 bloom
    elif v == "membrane":
        _cycles(sc, {"preview": 16, "sample": 24, "final": 32}, bounces=1, clamp=0.0)
        sc["dispersion"], sc["film_grain"], sc["vignette"] = 0.0, 0.5, 0.55        # 电镜：无色散，颗粒，暗角
        for mat in bpy.data.materials:                      # 灰度电镜 + 一点紫色调；脂质面比蛋白暗得多，三聚体才读得出来
            if not mat.name.startswith("SEM") or not mat.node_tree:
                continue
            lipid = mat.copy()
            lipid.name = "SEMLipid"
            for m_, lo, hi in ((mat, (0.20, 0.17, 0.26), (0.86, 0.80, 0.96)), (lipid, (0.030, 0.024, 0.040), (0.10, 0.085, 0.13))):
                for nd in m_.node_tree.nodes:
                    if nd.type == "VALTORGB":
                        nd.color_ramp.elements[0].position = 0.0
                        nd.color_ramp.elements[0].color = (*lo, 1)
                        nd.color_ramp.elements[1].color = (*hi, 1)
            bpy.data.objects["Lipid"].data.materials.clear()
            bpy.data.objects["Lipid"].data.materials.append(lipid)
    elif v == "neurons":
        sc.eevee.use_raytracing = False
    elif v == "laureates":
        sc.eevee.use_raytracing = False


def build(variant="paper", seed=7):
    sc = C.reset_scene(FRAMES)
    rnd = random.Random(seed)
    {"paper": paper, "neurons": neurons, "laureates": laureates, "membrane": membrane}[variant](sc, rnd)
    return sc
