"""参数化的风格化小鼠脑：整脑外形、冠状 / 矢状剖面、头部矢状剖面（皮层分层）、海马切片白模。

几何依据（全部示意，核查表记 simplified；P6 要补 research/visual/brain.md，附 Allen 图谱截图页）：
  - 大体分区和相对位置按 Allen Mouse Brain Atlas / Common Coordinate Framework v3 的大体解剖（Wang et al. 2020,
    Cell 181:936）：嗅球在最前；大脑皮层盖住背侧大部分；海马在皮层下、偏后；下丘脑在腹侧、中线两旁，
    下丘脑外侧区（LH）在下丘脑的外侧部；小脑在后上方，脑干在后下方；运动皮层在背侧前部。
  - 皮层分层只画三条带：L1（外层，细胞稀少）、L2/3–L5（兴奋性锥体神经元为主，B_14a 只让这一层发蓝光）、L6
    （内层）。真实的六层厚度比不在这里，宽度是示意。
  - 海马切片：CA 区画成一条「C」形带（CA1→CA3），齿状回（DG）是嵌在 C 口里的一个更小的「U」形带，颗粒细胞
    排在 DG 带上（Amaral & Witter 1989 的经典切片示意）。
示意的部分：所有部件都是椭球，没有沟回（小鼠皮层本来就近乎光滑，但形状仍是近似）；比例按整脑长约 1.0 BU 缩放，
不是毫米真值。剖面的轮廓 = 每个椭球和切面的交线（解析算出，见 `section_ellipse`），所以剖面和外形严格一致。

坐标（局部，乘以 scale 再加 loc）：+X 朝前（嗅球），+Y 朝左右外侧（Y=0 是中线），+Z 朝背侧。
"""
import math
import random

# ---- 纯 Python：部件椭球和区域坐标 ---------------------------------------------------------------
# name: (中心 (x, y, z), 半轴 (a, b, c))；成对的部件只写 +Y 一侧，`parts()` 镜像出另一侧。
PAIRED = {
    "cortex": ((0.02, 0.118, 0.02), (0.31, 0.135, 0.17)),
    "bulb": ((0.385, 0.042, -0.01), (0.085, 0.042, 0.055)),
    "hippocampus": ((-0.09, 0.095, 0.025), (0.095, 0.07, 0.045)),
}
SINGLE = {
    "cerebellum": ((-0.335, 0.0, -0.005), (0.095, 0.19, 0.12)),
    "stem": ((-0.33, 0.0, -0.12), (0.2, 0.065, 0.06)),
    "hypothalamus": ((0.0, 0.0, -0.115), (0.085, 0.07, 0.04)),
}

# 各区的代表点（局部 BU）：LH 在下丘脑外侧部（中线旁约 0.05），运动皮层在背侧前部的皮层表面下，
# 海马 / 齿状回在皮层下偏后。
REGIONS = {
    "lateral_hypothalamus": (0.0, 0.05, -0.115),
    "motor_cortex": (0.15, 0.06, 0.165),
    "hippocampus": (-0.09, 0.095, 0.035),
    "dentate_gyrus": (-0.085, 0.085, 0.01),
    "cerebellum": (-0.335, 0.0, 0.05),
    "olfactory_bulb": (0.385, 0.042, -0.01),
}


def parts():
    """[(名字, 中心, 半轴)]，成对的部件左右各一（后缀 L/R）。"""
    out = []
    for nm, (c, ax) in PAIRED.items():
        for s, suf in ((1, "L"), (-1, "R")):
            out.append((nm + suf, (c[0], s * c[1], c[2]), ax))
    for nm, (c, ax) in SINGLE.items():
        out.append((nm, c, ax))
    return out


def section_ellipse(center, axes, axis, value):
    """椭球与平面 axis = value（axis 0=x 冠状，1=y 矢状）的交线：返回 (平面内中心 (u, v), 半轴 (au, av))，没有交线返回 None。
    平面内坐标：冠状面 (u, v) = (y, z)，矢状面 (u, v) = (x, z)。"""
    d = (value - center[axis]) / axes[axis]
    if abs(d) >= 1.0:
        return None
    k = math.sqrt(1 - d * d)
    ui = 1 if axis == 0 else 0
    return (center[ui], center[2]), (axes[ui] * k, axes[2] * k)


def world(loc, scale, p):
    return tuple(loc[i] + scale * p[i] for i in range(3))


def hippo_arcs(n=60):
    """海马切片（局部，x-y 平面，单位 BU）的 CA 带和 DG 带中线点列。CA：C 形，开口朝 +X；DG：U 形，嵌在开口里。"""
    ca = [(0.26 * math.cos(a) - 0.04, 0.17 * math.sin(a)) for a in
          [math.radians(40 + 280 * k / (n - 1)) for k in range(n)]]
    dg = [(0.11 * math.cos(a) + 0.13, 0.085 * math.sin(a)) for a in
          [math.radians(110 + 140 * k / (n - 1)) for k in range(n)]]
    return ca, dg


# ---- bpy 部分 -------------------------------------------------------------------------------
def _tag(tag, ob, role):
    if tag:
        tag(ob, role)
    return ob


def _mat(name, color, roughness=0.55, alpha=None):
    import bpy
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    p.inputs["Base Color"].default_value = (*color, 1)
    p.inputs["Roughness"].default_value = roughness
    if alpha is not None:
        p.inputs["Alpha"].default_value = alpha
        m.surface_render_method = "BLENDED"
    return m


def _ellipsoid(name, center, axes, mat, root, seg=48, rings=24):
    import bpy
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, segments=seg, ring_count=rings, location=center)
    ob = bpy.context.object
    ob.name = name
    ob.scale = axes
    for p in ob.data.polygons:
        p.use_smooth = True
    if mat is not None:
        ob.data.materials.append(mat)
    ob.parent = root
    return ob


def _slab(name, axis, value, center2, axes2, mat, root, inner=None, arc=None, offset=0.002, thick=0.003, n=72):
    """切面上的一块平板：椭圆（或 inner 给出时是 inner..1 倍半径之间的环带；arc=(a0, a1) 度只取这段弧）。
    平板贴在切面外侧 offset 处（朝被切掉的那一侧），厚 thick。"""
    import bmesh
    import bpy
    bm = bmesh.new()
    a0, a1 = arc if arc else (0.0, 360.0)
    closed = arc is None
    m = n if closed else n + 1

    def pt(f, a):
        u = center2[0] + axes2[0] * f * math.cos(math.radians(a))
        v = center2[1] + axes2[1] * f * math.sin(math.radians(a))
        return (value + offset, u, v) if axis == 0 else (u, value - offset, v)   # 冠状朝 +X，矢状朝 -Y

    angs = [a0 + (a1 - a0) * k / (n if closed else n) for k in range(m)]
    if inner is None:
        c_top = bm.verts.new(pt(0.0, 0.0))
        ring = [bm.verts.new(pt(1.0, a)) for a in angs]
        for k in range(len(ring) - (0 if closed else 1)):
            bm.faces.new((c_top, ring[k], ring[(k + 1) % len(ring)]))
    else:
        outer = [bm.verts.new(pt(1.0, a)) for a in angs]
        inn = [bm.verts.new(pt(inner, a)) for a in angs]
        for k in range(len(outer) - (0 if closed else 1)):
            k2 = (k + 1) % len(outer)
            bm.faces.new((outer[k], outer[k2], inn[k2], inn[k]))
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    sol = ob.modifiers.new("Thick", "SOLIDIFY")
    sol.thickness = thick
    if mat is not None:
        ob.data.materials.append(mat)
    ob.parent = root
    return ob


def _cutter(name, axis, value, root, keep_below=True):
    """布尔切块：去掉 axis 方向上 > value（keep_below）的那一半。"""
    import bpy
    loc = [0.0, 0.0, 0.0]
    loc[axis] = value + (2.0 if keep_below else -2.0)
    bpy.ops.mesh.primitive_cube_add(size=4.0, location=loc)
    c = bpy.context.object
    c.name = name
    c.parent = root
    c.hide_render = c.hide_viewport = True
    return c


def mouse_brain(name, loc=(0, 0, 0), scale=1.0, section=None, tag=None, cut=None, shell_role="structure"):
    """建脑。section=None 整脑；"coronal" 在 x = cut（默认过 LH 的 x）切开，去掉前半；"sagittal" 在 y = cut
    （默认 0.05，过 LH 和运动皮层附近）切开，去掉 y < cut 的那一侧（相机应从 -Y 看）。
    剖面上：每个被切到的部件一块椭圆板（灰），皮层外侧一圈层带，海马、下丘脑各自颜色，LH 一个小圆盘。
    shell_role：外形椭球的 role（xray 镜头传 "shell" 让外形变玻璃，剖面板保持 structure）。
    返回 dict(root, cortex, cerebellum, bulbs, stem, hypothalamus, hippocampus, cut, regions, section_objs, scale)。
    regions 是世界坐标。"""
    import bpy
    root = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(root)
    root.location = loc
    root.scale = (scale,) * 3
    tissue = _mat("BrainTissue", (0.86, 0.74, 0.72), 0.6)
    obs = {}
    for nm, c, ax in parts():
        ob = _ellipsoid(f"{name}_{nm}", c, ax, tissue, root)
        _tag(tag, ob, shell_role)
        obs[nm] = ob
    cut_obj = None
    sec = []
    if section in ("coronal", "sagittal"):
        axis = 0 if section == "coronal" else 1
        value = cut if cut is not None else (REGIONS["lateral_hypothalamus"][0] if axis == 0 else 0.05)
        # 冠状：去掉前半（x > value）；矢状：去掉 y < value 的一侧
        cut_obj = _cutter(f"{name}_Cutter", axis, value, root, keep_below=(axis == 0))
        for ob in obs.values():
            mod = ob.modifiers.new("Section", "BOOLEAN")
            mod.operation = "DIFFERENCE"
            mod.object = cut_obj
            mod.solver = "EXACT"
        off = 0.0015                              # 板贴在切面外一点点（朝相机）
        grey = _mat("BrainSection", (0.6, 0.52, 0.5), 0.7)
        band = _mat("BrainCortexBand", (0.3, 0.4, 0.82), 0.6)
        hip = _mat("BrainHippocampus", (0.12, 0.62, 0.52), 0.6)
        hyp = _mat("BrainHypothalamus", (0.92, 0.62, 0.2), 0.6)
        lhm = _mat("BrainLH", (0.95, 0.35, 0.1), 0.5)
        for nm, c, ax in parts():
            e = section_ellipse(c, ax, axis, value)
            if e is None:
                continue
            kind = nm.rstrip("LR") if nm[-1] in "LR" else nm
            mat = {"hippocampus": hip, "hypothalamus": hyp}.get(kind, grey)
            lift = {"cortex": 0.0, "bulb": 0.0, "cerebellum": 0.0, "stem": 0.0}.get(kind, 0.0012)
            s = _slab(f"{name}_Sec_{nm}", axis, value, e[0], e[1], mat, root, offset=off + lift)
            _tag(tag, s, "structure")
            sec.append(s)
            if kind == "cortex":
                s2 = _slab(f"{name}_Sec_{nm}_Band", axis, value, e[0], e[1], band, root, inner=0.84, arc=(10, 170),
                           offset=off + 0.0012)
                _tag(tag, s2, "structure")
                sec.append(s2)
        lh = REGIONS["lateral_hypothalamus"]
        for sgn in ((1, -1) if axis == 0 else (1,)):
            p2 = (lh[1] * sgn, lh[2]) if axis == 0 else (lh[0], lh[2])
            d = _slab(f"{name}_Sec_LH{'L' if sgn > 0 else 'R'}", axis, value, p2, (0.022, 0.016), lhm, root,
                      offset=off + 0.0026)
            _tag(tag, d, "structure")
            sec.append(d)
    regions = {k: world(loc, scale, v) for k, v in REGIONS.items()}
    return {"root": root, "cortex": [obs["cortexL"], obs["cortexR"]], "cerebellum": obs["cerebellum"],
            "bulbs": [obs["bulbL"], obs["bulbR"]], "stem": obs["stem"], "hypothalamus": obs["hypothalamus"],
            "hippocampus": [obs["hippocampusL"], obs["hippocampusR"]], "cut": cut_obj, "regions": regions,
            "section_objs": sec, "scale": scale, "loc": tuple(loc)}


def head_section(name, loc=(0, 0, 0), scale=1.0, tag=None, cut=0.06):
    """啮齿动物头部矢状剖面示意：脑（mouse_brain 矢状剖面，y = cut）外面包一层颅骨（shell，半壳）和头皮（shell），
    前面一个锥形吻部（shell）。剖面上皮层分三条带：L1、兴奋性层（L2/3–L5）、L6，各自一块弧形板。
    cortex_layers = {"L1": obj, "excitatory": obj, "L6": obj}；兴奋性层的材质叫 <name>_ExcitatoryMat，
    caller 可以把它换成发光材质（或用 excitatory_glow_mat：已经建好的蓝色发光材质，强度 0，可打关键帧）。
    layer_z：兴奋性层在运动皮层处的世界 z（光纤尖端应停在这里上方一点）。"""
    import bpy
    import e2_shot as S
    br = mouse_brain(name + "Brain", loc, scale, section="sagittal", tag=tag, cut=cut)
    root = br["root"]
    bone = _mat("Skull", (0.9, 0.88, 0.82), 0.45)
    skin = _mat("Scalp", (0.75, 0.62, 0.6), 0.6)
    skull = _ellipsoid(name + "_Skull", (0.0, 0.0, 0.0), (0.56, 0.3, 0.25), bone, root)
    scalp = _ellipsoid(name + "_Scalp", (0.0, 0.0, 0.0), (0.6, 0.33, 0.29), skin, root)
    snout = _ellipsoid(name + "_Snout", (0.62, 0.0, -0.06), (0.3, 0.14, 0.13), skin, root)
    for ob, th in ((skull, 0.018), (scalp, 0.012), (snout, 0.01)):
        sol = ob.modifiers.new("Shell", "SOLIDIFY")
        sol.thickness = th
        mod = ob.modifiers.new("Section", "BOOLEAN")
        mod.operation = "DIFFERENCE"
        mod.object = br["cut"]
        mod.solver = "EXACT"
        _tag(tag, ob, "shell")
    # 皮层分层：在已有皮层剖面椭圆上叠三条弧形带
    c, ax = PAIRED["cortex"]
    cen = (c[0], c[1], c[2])
    e = section_ellipse(cen, ax, 1, cut)
    layers = {}
    off = 0.0032
    exc_glow = S.glow(name + "_ExcitatoryGlowMat", S.lin((142, 175, 255)), 0.0)
    for nm, (f0, col) in (("L1", (0.95, (0.85, 0.85, 0.9))), ("excitatory", (0.84, (0.55, 0.62, 0.9))),
                          ("L6", (0.76, (0.5, 0.5, 0.62)))):
        f1 = {"L1": 1.0, "excitatory": 0.95, "L6": 0.84}[nm]
        mat = _mat(f"{name}_{nm.capitalize()}Mat" if nm != "excitatory" else name + "_ExcitatoryMat", col, 0.6)
        s = _slab(f"{name}_Layer_{nm}", 1, cut, e[0], e[1], mat, root, inner=f0 / f1, arc=(15, 165), offset=off)
        # inner/outer 是相对 f1 的：把整块缩到 f1
        _rescale_slab(s, e[0], f1)
        _tag(tag, s, "structure")
        layers[nm] = s
    mc = REGIONS["motor_cortex"]
    # 运动皮层处兴奋性层的 z：皮层椭圆在 x = mc.x 处的上沿 × 0.9
    u = (mc[0] - e[0][0]) / e[1][0]
    z_top = e[0][1] + e[1][1] * math.sqrt(max(0.0, 1 - u * u))
    z_exc = e[0][1] + (z_top - e[0][1]) * 0.895
    regions = dict(br["regions"])
    regions["excitatory_layer_at_motor_cortex"] = world(loc, scale, (mc[0], cut, z_exc))
    regions["skull_top_at_motor_cortex"] = world(loc, scale, (mc[0], cut, 0.25 * math.sqrt(max(0.0, 1 - (mc[0] / 0.56) ** 2))))
    return {"root": root, "skull": skull, "scalp": scalp, "snout": snout, "brain": br, "cortex_layers": layers,
            "excitatory_glow_mat": exc_glow, "layer_z": regions["excitatory_layer_at_motor_cortex"][2],
            "regions": regions, "cut": cut}


def _rescale_slab(ob, center2, f):
    """把 _slab 生成的板在切面内按 f 缩放（以椭圆中心为原点），用于分层带：只改网格顶点。"""
    for v in ob.data.vertices:
        v.co.x = center2[0] + (v.co.x - center2[0]) * f
        v.co.z = center2[1] + (v.co.z - center2[1]) * f


def hippocampus_slice(name, loc=(0, 0, 0), scale=1.0, n_cells=40, seed=4, tag=None):
    """海马切片白模：一块躺在 x-y 平面的圆角厚片（顶面 z = 0.02），上面一条 C 形 CA 带和一条 U 形 DG 带
    （各是一根扁管），DG 带上撒 n_cells 个小细胞球（structure）。
    返回 dict(root, slab, ca_band, dg_band, dg_cells, dg_cell_positions)；位置是世界坐标。"""
    import bpy
    import e2_shot as S
    rnd = random.Random(seed)
    root = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(root)
    root.location = loc
    root.scale = (scale,) * 3
    slab_m = _mat("SliceTissue", (0.85, 0.8, 0.78), 0.7)
    band_m = _mat("SliceBand", (0.7, 0.7, 0.75), 0.6)
    cell_m = _mat("SliceCell", (0.9, 0.9, 0.92), 0.5)
    slab = _ellipsoid(name + "_Slab", (0.0, 0.0, 0.0), (0.42, 0.3, 0.02), slab_m, root, seg=64, rings=8)
    _tag(tag, slab, "structure")
    ca, dg = hippo_arcs()
    ca_band = S.tube(name + "_CA", [(x, y, 0.0) for x, y in ca], 0.014, band_m, "structure", res=2)
    dg_band = S.tube(name + "_DG", [(x, y, 0.0) for x, y in dg], 0.011, band_m, "structure", res=2)
    for b in (ca_band, dg_band):
        b.scale = (1, 1, 0.45)                         # 扁管：先在 z = 0 建，压扁后再抬到片子顶面
        b.location = (0, 0, 0.021)
        b.parent = root
        _tag(tag, b, "structure")
    cells, pos = [], []
    for i in range(n_cells):
        x, y = dg[int((i + rnd.random()) / n_cells * (len(dg) - 1))]
        p = (x + rnd.uniform(-0.008, 0.008), y + rnd.uniform(-0.008, 0.008), 0.03)
        c = S.sphere(f"{name}_DGCell{i}", 0.0075, p, cell_m, "structure", seg=12, rings=8)
        c.parent = root
        cells.append(c)
        pos.append(world(loc, scale, p))
    return {"root": root, "slab": slab, "ca_band": ca_band, "dg_band": dg_band, "dg_cells": cells,
            "dg_cell_positions": pos}
