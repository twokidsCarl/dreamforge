"""E2 镜头脚本共用的 bpy 小工具：关键帧、相机、光晕材质、Cycles 采样、灯、管子和箭头。

a0_scenes.py 里同名的私有函数是 A0 定稿时写的，A0 不动；A–D 段的 *_scenes.py 都从这里取。
镜头长度从 storyboard.timed.yaml 读（shot_frames），retime 之后不用改代码。
"""
import math

import bpy
from mathutils import Vector

import common as C
import e2_common as E
import materials as M
import styles

FPS = 24


# ---- 时间 -----------------------------------------------------------------------------------
def shot_frames(sid, default=48):
    """镜头的帧数（timed.yaml 的 duration × 24）。找不到 timed 文件或镜头时回退 default。"""
    try:
        from paths import timed_shots
        return max(1, round(next(s["duration"] for s in timed_shots(quiet=True) if s["id"] == sid) * FPS))
    except Exception:
        return default


def smooth(u):
    u = max(0.0, min(1.0, u))
    return u * u * (3 - 2 * u)


# ---- 关键帧 ---------------------------------------------------------------------------------
def key(ob, f, **kw):
    for k, v in kw.items():
        setattr(ob, k, v)
        ob.keyframe_insert(k, frame=f)


def linear(ob):
    """物体（和它的数据块）上所有关键帧改成线性插值。"""
    for idb in (ob, getattr(ob, "data", None)):
        if idb is not None and idb.animation_data and idb.animation_data.action:
            for fc in C.fcurves(idb.animation_data.action):
                for kp in fc.keyframe_points:
                    kp.interpolation = "LINEAR"


def show_between(ob, f_on, f_off=None):
    """f_on 之前和 f_off 之后不渲染（hide_render 关键帧是阶跃）。"""
    key(ob, 1, hide_render=f_on > 1)
    if f_on > 1:
        key(ob, f_on, hide_render=False)
    if f_off is not None:
        key(ob, f_off, hide_render=True)


# ---- 相机 -----------------------------------------------------------------------------------
def camera(name, keys, parent=None, dof=False):
    """keys: [(frame, aim, location, lens_mm, fstop)]。aim 空物体同时是对焦目标。"""
    aim = bpy.data.objects.new(name + "Aim", None)
    bpy.context.scene.collection.objects.link(aim)
    cam = bpy.data.objects.new(name, bpy.data.cameras.new(name))
    bpy.context.scene.collection.objects.link(cam)
    if parent is not None:
        aim.parent = cam.parent = parent
    t = cam.constraints.new("TRACK_TO")
    t.target = aim
    t.track_axis = "TRACK_NEGATIVE_Z"
    t.up_axis = "UP_Y"
    cam.data.sensor_width = 36
    cam.data.clip_start = 0.005
    cam.data.clip_end = 500
    cam.data.dof.use_dof = dof
    cam.data.dof.focus_object = aim
    for f, a, loc, lens, fstop in keys:
        key(aim, f, location=a)
        key(cam, f, location=loc)
        cam.data.lens = lens
        cam.data.keyframe_insert("lens", frame=f)
        cam.data.dof.aperture_fstop = fstop
        cam.data.dof.keyframe_insert("aperture_fstop", frame=f)
    return cam


def dolly(name, aim, loc0, loc1, f0, f1, lens=50, fstop=8.0, dof=False, aim1=None):
    """慢推：f0→f1 从 loc0 推到 loc1（分镜里长镜头的 slow dolly-in）。"""
    return camera(name, [(f0, aim, loc0, lens, fstop), (f1, aim1 or aim, loc1, lens, fstop)], dof=dof)


def locked(name, aim, loc, f=1, lens=50, fstop=8.0, dof=False):
    return camera(name, [(f, aim, loc, lens, fstop)], dof=dof)


def toward(loc, aim, frac):
    """loc 沿着到 aim 的方向前进 frac（0–1）。"""
    return tuple(loc[i] + (aim[i] - loc[i]) * frac for i in range(3))


# ---- 材质 -----------------------------------------------------------------------------------
def lin(c):
    return E.srgb_to_linear(c)


def halo(name, color, gain=0.0):
    """软光晕球：球心最亮，向边缘高次幂衰减，叠在透明上；节点 'Gain' 可打关键帧（0 = 熄灭）。"""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.remove(nt.nodes["Principled BSDF"])
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    dot = nt.nodes.new("ShaderNodeVectorMath")
    dot.operation = "DOT_PRODUCT"
    ab = nt.nodes.new("ShaderNodeMath")
    ab.operation = "ABSOLUTE"
    pw = nt.nodes.new("ShaderNodeMath")
    pw.operation = "POWER"
    pw.inputs[1].default_value = 5.0
    g = nt.nodes.new("ShaderNodeMath")
    g.operation = "MULTIPLY"
    g.name = "Gain"
    g.inputs[1].default_value = gain
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*color, 1)
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    add = nt.nodes.new("ShaderNodeAddShader")
    L = nt.links.new
    L(geo.outputs["Normal"], dot.inputs[0])
    L(geo.outputs["Incoming"], dot.inputs[1])
    L(dot.outputs["Value"], ab.inputs[0])
    L(ab.outputs[0], pw.inputs[0])
    L(pw.outputs[0], g.inputs[0])
    L(g.outputs[0], em.inputs["Strength"])
    L(tr.outputs[0], add.inputs[0])
    L(em.outputs[0], add.inputs[1])
    L(add.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
    m.surface_render_method = "BLENDED"
    return m


def set_gain(mat, f, v):
    s = mat.node_tree.nodes["Gain"].inputs[1]
    s.default_value = v
    s.keyframe_insert("default_value", frame=f)


def set_strength(mat, f, v):
    M.set_emission_strength(mat, f, v)


def set_emit_color(mat, f, color):
    """M.emission 材质的颜色关键帧（细菌视紫红质吸收颜色变化用）。"""
    s = mat.node_tree.nodes["Emission"].inputs["Color"]
    s.default_value = (*color, 1)
    s.keyframe_insert("default_value", frame=f)


def glow(name, color, strength=0.0):
    return M.emission(name, color, strength)


def matte(name, color, roughness=0.6):
    return M.principled(name, color, roughness=roughness)


# ---- 几何 -----------------------------------------------------------------------------------
def link(ob):
    bpy.context.scene.collection.objects.link(ob)
    return ob


def holed_plane(name, half_w, half_h, z, holes, seg=96, center=(0.0, 0.0)):
    """平板（法线 +z），在 holes=[(cx, cy, rx, ry)] 处挖出真正的椭圆孔：孔边是 seg 段的多边形，
    外框和孔边用 triangle_fill 一次三角化。替代「方格网按格心挖格子」那种孔边成阶梯的做法。
    孔必须两两不相交，且整个落在外框里（越界的孔会断言失败）。"""
    import bmesh
    bm = bmesh.new()
    ox, oy = center
    edges = []

    def loop(pts):
        vs = [bm.verts.new((x, y, z)) for x, y in pts]
        for k in range(len(vs)):
            edges.append(bm.edges.new((vs[k], vs[(k + 1) % len(vs)])))

    loop([(ox - half_w, oy - half_h), (ox + half_w, oy - half_h), (ox + half_w, oy + half_h), (ox - half_w, oy + half_h)])
    for hx, hy, rx, ry in holes:
        assert abs(hx - ox) + rx < half_w and abs(hy - oy) + ry < half_h, (name, hx, hy)
        loop([(hx + rx * math.cos(2 * math.pi * k / seg), hy + ry * math.sin(2 * math.pi * k / seg)) for k in range(seg)])
    bmesh.ops.triangle_fill(bm, use_beauty=True, use_dissolve=False, edges=edges, normal=(0.0, 0.0, 1.0))
    for f in bm.faces:
        if f.normal.z < 0:
            f.normal_flip()
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    return link(bpy.data.objects.new(name, me))


def sphere(name, r, loc, mat=None, role="structure", seg=24, rings=14, scale=(1, 1, 1)):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, segments=seg, ring_count=rings, location=loc)
    ob = bpy.context.object
    ob.name = name
    ob.scale = scale
    for p in ob.data.polygons:
        p.use_smooth = True
    if mat is not None:
        ob.data.materials.append(mat)
    styles.tag(ob, role)
    return ob


def box(name, loc, size, mat=None, role="structure", bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    ob = bpy.context.object
    ob.name = name
    ob.scale = (size[0] / 2, size[1] / 2, size[2] / 2)
    if bevel:
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        b = ob.modifiers.new("Bevel", "BEVEL")
        b.width = bevel
        b.segments = 3
    if mat is not None:
        ob.data.materials.append(mat)
    styles.tag(ob, role)
    return ob


def cylinder(name, r, depth, loc, mat=None, role="structure", rot=(0, 0, 0), verts=32):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=depth, location=loc, rotation=rot, vertices=verts)
    ob = bpy.context.object
    ob.name = name
    if mat is not None:
        ob.data.materials.append(mat)
    styles.tag(ob, role)
    return ob


def tube(name, pts, r, mat=None, role="structure", radii=None, res=3, caps=True):
    """沿点列的圆管（POLY 曲线 + bevel）。radii 给出时逐点半径 = r × radii[i]。"""
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = r
    cu.bevel_resolution = res
    cu.use_fill_caps = caps
    sp = cu.splines.new("POLY")
    sp.points.add(len(pts) - 1)
    for i, (pt, p) in enumerate(zip(sp.points, pts)):
        pt.co = (p[0], p[1], p[2], 1.0)
        pt.radius = radii[i] if radii else 1.0
    ob = link(bpy.data.objects.new(name, cu))
    if mat is not None:
        ob.data.materials.append(mat)
    styles.tag(ob, role)
    return ob


def reveal(ob, f0, f1, start=0.0):
    """曲线从头画到尾：bevel_factor_end 在 f0→f1 从 start 升到 1。"""
    cu = ob.data
    cu.bevel_factor_mapping_end = "SPLINE"
    cu.bevel_factor_end = start
    cu.keyframe_insert("bevel_factor_end", frame=f0)
    cu.bevel_factor_end = 1.0
    cu.keyframe_insert("bevel_factor_end", frame=f1)


def between(name, a, b, r, mat=None, role="structure", verts=16):
    """a、b 两点之间的圆柱。"""
    a, b = Vector(a), Vector(b)
    d = b - a
    ob = cylinder(name, r, d.length, (a + b) / 2, mat, role, verts=verts)
    ob.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    return ob


def arrow(name, a, b, r, mat=None, role="structure", head=2.6):
    """a→b 的箭头：杆 + 圆锥头（头长 = 杆半径 × head × 2.2）。返回 (杆, 头)。"""
    a, b = Vector(a), Vector(b)
    d = (b - a).normalized()
    hl = r * head * 2.2
    shaft = between(name + "Shaft", a, b - d * hl, r, mat, role)
    bpy.ops.mesh.primitive_cone_add(radius1=r * head, radius2=0, depth=hl, location=b - d * hl / 2, vertices=24)
    tip = bpy.context.object
    tip.name = name + "Head"
    tip.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    if mat is not None:
        tip.data.materials.append(mat)
    styles.tag(tip, role)
    return shaft, tip


def cone_beam(name, apex, target, r_end, color, strength=0.0, role="emitter"):
    """一束光：apex 到 target 的圆锥，体积感由软发光材质给出（只是示意的光束，不是光学计算）。"""
    apex, target = Vector(apex), Vector(target)
    d = target - apex
    bpy.ops.mesh.primitive_cone_add(radius1=r_end, radius2=r_end * 0.08, depth=d.length,
                                    location=(apex + target) / 2, vertices=48, end_fill_type="NOTHING")
    ob = bpy.context.object
    ob.name = name
    ob.rotation_euler = (-d).to_track_quat("Z", "Y").to_euler()     # 窄头在 apex
    m = beam_material(name + "Mat", color, strength, length=d.length)
    ob.data.materials.append(m)
    ob.visible_shadow = False
    styles.tag(ob, role)
    return ob, m


def beam_material(name, color, strength, length=None):
    """半透明的光束：轮廓边缘淡、中间亮（Layer Weight 取反），叠在透明上。'Gain' 可打关键帧。
    只渲正面（背面也发光会叠成实心的灰白锥）。length 给出时（cone_beam 传入），亮度沿光束从窄头（局部 +Z）
    到宽头衰减到 25%，读起来是一束散开的光，而不是一个锥体。"""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.remove(nt.nodes["Principled BSDF"])
    lw = nt.nodes.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.4
    inv = nt.nodes.new("ShaderNodeMath")
    inv.operation = "SUBTRACT"
    inv.inputs[0].default_value = 1.0
    g = nt.nodes.new("ShaderNodeMath")
    g.operation = "MULTIPLY"
    g.name = "Gain"
    g.inputs[1].default_value = strength
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*color, 1)
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    add = nt.nodes.new("ShaderNodeAddShader")
    L = nt.links.new
    L(lw.outputs["Facing"], inv.inputs[1])
    if length:
        tc = nt.nodes.new("ShaderNodeTexCoord")
        sep = nt.nodes.new("ShaderNodeSeparateXYZ")
        rng = nt.nodes.new("ShaderNodeMapRange")
        rng.inputs["From Min"].default_value = -length / 2
        rng.inputs["From Max"].default_value = length / 2
        rng.inputs["To Min"].default_value = 0.25
        rng.inputs["To Max"].default_value = 1.0
        mul = nt.nodes.new("ShaderNodeMath")
        mul.operation = "MULTIPLY"
        L(tc.outputs["Object"], sep.inputs[0])
        L(sep.outputs["Z"], rng.inputs["Value"])
        L(inv.outputs[0], mul.inputs[0])
        L(rng.outputs["Result"], mul.inputs[1])
        L(mul.outputs[0], g.inputs[0])
    else:
        L(inv.outputs[0], g.inputs[0])
    geo = nt.nodes.new("ShaderNodeNewGeometry")            # 背面不发光（Cycles 不认 use_backface_culling）
    front = nt.nodes.new("ShaderNodeMath")
    front.operation = "SUBTRACT"
    front.inputs[0].default_value = 1.0
    fm = nt.nodes.new("ShaderNodeMath")
    fm.operation = "MULTIPLY"
    L(geo.outputs["Backfacing"], front.inputs[1])
    L(g.outputs[0], fm.inputs[0])
    L(front.outputs[0], fm.inputs[1])
    L(fm.outputs[0], em.inputs["Strength"])
    L(tr.outputs[0], add.inputs[0])
    L(em.outputs[0], add.inputs[1])
    L(add.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
    m.surface_render_method = "BLENDED"
    m.use_backface_culling = True
    return m


def plus_glyph(name, loc, size, mat, role="structure", minus=False, normal_axis="Y"):
    """「+」或「−」号的扁平几何（不用文字对象）。normal_axis：字面朝哪个轴（默认朝 -Y，即朝镜头）。"""
    t = size * 0.22
    parts = [box(name + "H", (0, 0, 0), (size, t, t) if normal_axis == "Y" else (size, t, t), mat, role)]
    if not minus:
        parts.append(box(name + "V", (0, 0, 0), (t, t, size) if normal_axis == "Y" else (t, size, t), mat, role))
    root = bpy.data.objects.new(name, None)
    link(root)
    root.location = loc
    for p in parts:
        p.parent = root
    return root, parts


# ---- 灯 -------------------------------------------------------------------------------------
def area(name, loc, aim, size, energy, color=(1.0, 0.97, 0.92), keep=False):
    bpy.ops.object.light_add(type="AREA", location=loc)
    lt = bpy.context.object
    lt.name = name
    lt.data.size = size
    lt.data.energy = energy
    lt.data.color = color
    lt.rotation_euler = (Vector(aim) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    if keep:
        lt["keep_light"] = 1
    return lt


def spot(name, loc, aim, energy, angle_deg=30, blend=0.3, color=(1.0, 0.95, 0.85), radius=0.02, keep=True):
    bpy.ops.object.light_add(type="SPOT", location=loc)
    lt = bpy.context.object
    lt.name = name
    lt.data.energy = energy
    lt.data.spot_size = math.radians(angle_deg)
    lt.data.spot_blend = blend
    lt.data.color = color
    lt.data.shadow_soft_size = radius
    lt.rotation_euler = (Vector(aim) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    lt.visible_camera = False
    if keep:
        lt["keep_light"] = 1
    return lt


def studio_lights(scale=1.0, center=(0, 0, 0)):
    """白模 / 剖视用的两盏面光：左上主光 + 右前补光（clay、xray 会保留，energy、sem 会关）。"""
    cx, cy, cz = center
    area("Key", (cx - 5 * scale, cy - 9 * scale, cz + 8 * scale), center, 9 * scale, 1200 * scale * scale)
    area("Fill", (cx + 7 * scale, cy - 8 * scale, cz + 2 * scale), center, 12 * scale, 380 * scale * scale)


def dark_room(top=(0.0016, 0.0018, 0.0024)):
    """纪实暗室：极暗的世界，AgX Base Contrast。"""
    C.set_world(top=top, horizon=tuple(v * 0.5 for v in top), bottom=(0, 0, 0))
    C.set_color_management(look="Base Contrast", exposure=0.0)


def cycles(sc, spp, bounces=4, clamp=4.0):
    """Cycles 采样按质量档（preview / sample / final），OpenImageDenoise 降噪；final 目标 60 秒/帧以内。"""
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
    cy.transmission_bounces = 4
    cy.volume_bounces = 1
    cy.caustics_reflective = cy.caustics_refractive = False
    cy.sample_clamp_indirect = clamp
    return q


def after_style_common(sc, style):
    """各模块 after_style 的公共部分：EEVEE 风格化镜头关掉光追（只有发光和描边，没必要）；
    纪实 / 真实渲染镜头用 Cycles 低采样 + 降噪，并加纪实的细颗粒和暗角；L2 纪实和 S 电镜关 bloom。"""
    if sc.render.engine == "CYCLES":
        cycles(sc, {"preview": 24, "sample": 48, "final": 64})
        if style in ("documentary", "photoreal"):
            sc["film_grain"], sc["vignette"] = 0.25, 0.4
    else:
        sc.eevee.use_raytracing = False
    if style == "sem":
        sc["dispersion"], sc["film_grain"], sc["vignette"] = 0.0, 0.5, 0.55
    if style == "documentary":
        sc["no_glare"] = True                     # L2 Document 不开 bloom（STYLE_REVIEW §4.3 技术参数 2）


# ---- 膜电位 / 电流曲线（A_01a、B_08a、B_10a、B_16a 等）------------------------------------------
# 形状全是示意（核查表记 simplified）：只表达「猛地翻上去再回来」「升到高峰落到平台」「往下走」，不带刻度和数值。
def spike_shape(u, at=0.35, width=0.12):
    """单个锋电位的示意波形，u∈[0,1]，返回 -1..1：静息 -0.6，快速上冲到 +1，回落时略低于静息，再恢复。"""
    x = (u - at) / width
    if x < 0:
        return -0.6
    if x < 0.25:                                          # 上冲
        return -0.6 + 1.6 * smooth(x / 0.25)
    if x < 1.0:                                           # 复极化
        return 1.0 - 1.8 * smooth((x - 0.25) / 0.75)
    return -0.8 + 0.2 * smooth(min(1.0, (x - 1.0) / 1.2))  # 超极化后恢复到 -0.6


def spike_train(u, pulses, width=0.035):
    """一串锋电位：pulses 是 u 位置列表，每个位置一个锋电位。"""
    v = -0.6
    for p in pulses:
        s = spike_shape(u, p, width)
        if s != -0.6 and (u - p) / width < 2.2:
            v = s
    return v


def peak_plateau(u, on=0.2, off=0.85, peak=1.0, plateau=0.45):
    """持续光照下的通道电流示意：on 处升到峰值，指数式落到平台，off 处回到 0。返回 0..1。"""
    if u < on:
        return 0.0
    if u >= off:
        return plateau * math.exp(-(u - off) / 0.03)
    x = (u - on)
    rise = smooth(x / 0.02)
    return rise * (plateau + (peak - plateau) * math.exp(-x / 0.08))


def trace(name, fn, origin, size, mat, f0, f1, n=160, r=0.006, axis_mat=None, role="emitter"):
    """在 x-z 平面画一条曲线：x 从 origin.x 到 origin.x + size[0]，z = origin.z + fn(u) × size[1] / 2。
    f0→f1 从左往右画出来（reveal）。axis_mat 给出时加一条基线（fn = 0 处）。返回 (曲线, 基线或 None, 点列)。"""
    ox, oy, oz = origin
    w, h = size
    pts = [(ox + w * k / (n - 1), oy, oz + fn(k / (n - 1)) * h / 2) for k in range(n)]
    ob = tube(name, pts, r, mat, role, res=2)
    reveal(ob, f0, f1)
    base = None
    if axis_mat is not None:
        base = tube(name + "Axis", [(ox, oy + 0.001, oz), (ox + w, oy + 0.001, oz)], r * 0.35, axis_mat, "structure", res=1)
    return ob, base, pts


def trace_head(name, pts, f0, f1, r, mat, role="emitter"):
    """曲线笔尖上的亮点，跟着 reveal 走（reveal 按弧长，这里也按弧长）。"""
    head = sphere(name, r, pts[0], mat, role, seg=16, rings=8)
    seg = [math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]
    tot = sum(seg)
    for f in range(f0, f1 + 1, 2):
        target = (f - f0) / max(1, f1 - f0) * tot
        acc = 0.0
        for i, L in enumerate(seg):
            if acc + L >= target or i == len(seg) - 1:
                t = 0 if L == 0 else (target - acc) / L
                head.location = tuple(pts[i][k] + (pts[i + 1][k] - pts[i][k]) * min(1.0, t) for k in range(3))
                break
            acc += L
        head.keyframe_insert("location", frame=f)
    show_between(head, f0, f1 + 12)
    return head


# ---- 神经元簇（A_03b、C_01a、C_03b、D_01a）----------------------------------------------------
def neuron_cluster(prefix, n, center, radius, seed, mat=None, scale=0.35, lit=(), seed_base=301):
    """在 center 附近撒 n 个缩小的参数化神经元（build_neuron，scale 倍），lit 是要被光点亮的那些下标。
    返回 [(cell_dict, root_empty)]，每个 root 是空物体，神经元整体跟着它缩放和移动。"""
    import random
    import build_neuron as BN
    rnd = random.Random(seed)
    out = []
    for i in range(n):
        a = rnd.uniform(0, 2 * math.pi)
        rr = radius * math.sqrt(rnd.random())
        loc = (center[0] + rr * math.cos(a), center[1] + rnd.uniform(-radius, radius) * 0.4, center[2] + rr * math.sin(a))
        root = link(bpy.data.objects.new(f"{prefix}{i}Root", None))
        root.location = loc
        root.scale = (scale, scale, scale)
        root.rotation_euler = (rnd.uniform(-0.3, 0.3), rnd.uniform(-0.3, 0.3), rnd.uniform(-math.pi, math.pi))
        cell = BN.build_neuron(f"{prefix}{i}", seed_base + 13 * i, (0, 0, 0), mat, tag=styles.tag)
        for o in [cell["soma"], cell["dendrites"], cell["axon"]] + cell["boutons"]:
            o.parent = root
        out.append((cell, root))
    return out


def soma_glow(prefix, cell, root, color, keys, r=0.34):
    """给一个神经元胞体套光晕球（halo）；keys = [(frame, gain)]。返回材质。"""
    m = halo(prefix + "HaloMat", color)
    h = sphere(prefix + "Halo", r, (0, 0, 0), m, "emitter", seg=20, rings=12)
    h.parent = root
    for f, g in keys:
        set_gain(m, f, g)
    return m
