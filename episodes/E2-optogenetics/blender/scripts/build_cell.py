"""参数化单细胞：衣藻（B_05a / B_05b）和爪蟾卵母细胞（B_06a）。

衣藻（Chlamydomonas reinhardtii），几何依据（教科书通用形态，核查表记 simplified；P6 补 research/visual/chlamydomonas.md）：
  - 单细胞绿藻，细胞体近卵形，长约 10 µm、宽约 8 µm（Harris《The Chlamydomonas Sourcebook》第 2 版第 1 卷第 2 章
    的通用描述；不同株系和生长期有差别，这里取长 10、宽 8）。
  - 前端（顶端）伸出两根等长鞭毛，长约 10–12 µm，比细胞体略长；这里取 11 µm。向前游时两根鞭毛做类似蛙泳的
    划桨动作（有效划 + 回复划）。真实拍频约 50 Hz，24 fps 下看不清，所以动画里放慢成每 0.5 秒一拍（artistic）。
  - 一个大的杯状叶绿体占据细胞后部和侧壁，杯底有蛋白核（pyrenoid）；细胞核在杯口里，偏前；
    眼点是叶绿体边缘、细胞赤道附近的一个橙红色小斑，在细胞的一侧（Sourcebook 同章；Hegemann 的趋光研究都以它为感光位置）。
  - 游动时细胞绕长轴自转（约每秒 1–2 圈），所以眼点像灯塔一样扫过光源方向；动画用每 2 秒一圈（示意）。
  - 前端还有两个伸缩泡，这里画成两个小透明泡（示意）。
  单位：1 µm = 0.1 BU，细胞长 1 BU。细胞长轴沿局部 +Y（前端 = +Y），眼点在局部 +X 一侧。

爪蟾卵母细胞（Xenopus laevis oocyte，VI 期），几何依据（Dumont 1972, J Morphol 136:153 的分期；示意）：
  - 直径约 1.1–1.3 mm 的大球；动物极半球深褐色（色素），植物极半球淡黄白；两半球之间有一条较浅的赤道带。
  - 这里只画外观和膜上几个「表达出来的通道」位点（示意，不按真实密度），不画卵黄颗粒和胚泡。
  单位：卵母细胞半径 1 BU（与衣藻不在同一镜头里，不需要统一比例）。

纯几何部分不依赖 bpy；bpy 部分在函数里 import，tag 由调用方传入（styles.tag）。
"""
import math
import random

UNIT = 0.1                   # 1 µm = 0.1 BU
CELL_LEN = 10.0              # µm
CELL_WID = 8.0
FLAG_LEN = 11.0
EYESPOT_LAT = math.radians(8)  # 眼点在赤道略偏前


def flagellum_points(phase, side, n=12):
    """一根鞭毛的中心线（细胞局部坐标，µm）。phase∈[0,1)：0–0.55 有效划（伸直向后扫），0.55–1 回复划（弯着收回）。
    side = ±1：左右两根，在 x-y 平面里镜像。基部在顶端（0, CELL_LEN/2, 0）稍两侧。"""
    base = (side * 0.6, CELL_LEN / 2 - 0.2, 0.0)
    if phase < 0.55:                                   # 有效划：从向前张开扫到向后
        s = phase / 0.55
        ang0 = math.radians(20 + 150 * (s * s * (3 - 2 * s)))
        curl = 0.15
    else:                                              # 回复划：弯成钩，从后往前收
        s = (phase - 0.55) / 0.45
        ang0 = math.radians(170 - 150 * (s * s * (3 - 2 * s)))
        curl = 1.25 * math.sin(math.pi * s) + 0.15
    pts = []
    ang = ang0
    p = list(base)
    seg = FLAG_LEN / (n - 1)
    pts.append(tuple(p))
    for k in range(1, n):
        ang += curl * 0.28 * (k / n)
        # 角度从 +Y（前）向外侧量；side 决定往 +x 还是 -x 摆
        d = (side * math.sin(ang), math.cos(ang), 0.0)
        p = [p[0] + d[0] * seg, p[1] + d[1] * seg, p[2] + 0.04 * math.sin(k)]
        pts.append(tuple(p))
    return pts


def eyespot_local():
    """眼点中心（局部，µm）：赤道略偏前，+X 一侧的细胞表面内侧。"""
    a = CELL_WID / 2 * 0.9
    return (a * math.cos(EYESPOT_LAT), CELL_LEN / 2 * math.sin(EYESPOT_LAT), 0.0)


# ---- bpy 部分 -------------------------------------------------------------------------------
def _sphere(name, r, loc, mat, scale=(1, 1, 1), seg=40, rings=24):
    import bpy
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, segments=seg, ring_count=rings, location=loc)
    ob = bpy.context.object
    ob.name = name
    ob.scale = scale
    for p in ob.data.polygons:
        p.use_smooth = True
    if mat is not None:
        ob.data.materials.append(mat)
    return ob


def _cup_mesh(name, rx, ry, rz, open_frac=0.42, thick=0.18, seg=48, rings=24):
    """杯状叶绿体：椭球壳，从后端（-Y）包到 open_frac 处（前端敞口），壁厚 thick（相对半径）。"""
    import bmesh
    import bpy
    bm = bmesh.new()
    lat_max = math.asin(max(-1.0, min(1.0, 1 - 2 * open_frac)))      # 敞口所在的纬度（y = sin(lat)）
    shells = []
    for scale_ in (1.0, 1.0 - thick):
        rows = []
        for i in range(rings + 1):
            lat = -math.pi / 2 + (lat_max + math.pi / 2) * i / rings
            row = []
            for j in range(seg):
                lon = 2 * math.pi * j / seg
                x = rx * scale_ * math.cos(lat) * math.cos(lon)
                z = rz * scale_ * math.cos(lat) * math.sin(lon)
                y = ry * scale_ * math.sin(lat)
                row.append(bm.verts.new((x, y, z)))
            rows.append(row)
        shells.append(rows)
    for rows, flip in ((shells[0], False), (shells[1], True)):
        for a, b in zip(rows[:-1], rows[1:]):
            for j in range(seg):
                q = (a[j], a[(j + 1) % seg], b[(j + 1) % seg], b[j])
                bm.faces.new(q[::-1] if flip else q)
    lo, li = shells[0][-1], shells[1][-1]                             # 敞口的唇
    for j in range(seg):
        bm.faces.new((lo[j], lo[(j + 1) % seg], li[(j + 1) % seg], li[j]))
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    for f in bm.faces:
        f.smooth = True
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def build_chlamy(name, loc=(0, 0, 0), mats=None, tag=None):
    """建一枚衣藻。mats: dict(wall, chloro, nucleus, pyrenoid, eyespot, flagellum, vacuole)，缺省为 None（不上材质）。
    返回 dict(root, spin, body, chloroplast, nucleus, pyrenoid, eyespot, flagella=[curve obj ×2], vacuoles)。
    root 管位置和朝向（长轴 = 局部 +Y），spin 是 root 下绕长轴自转的空物体，所有部件挂在 spin 上。"""
    import bpy
    tag = tag or (lambda o, r: o)
    mats = mats or {}
    u = UNIT
    root = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(root)
    root.location = loc
    root.rotation_mode = "XYZ"
    spin = bpy.data.objects.new(name + "Spin", None)
    bpy.context.scene.collection.objects.link(spin)
    spin.parent = root
    spin.rotation_mode = "XYZ"
    rx, ry = CELL_WID / 2 * u, CELL_LEN / 2 * u
    body = _sphere(name + "Body", 1.0, (0, 0, 0), mats.get("wall"), scale=(rx, ry * 1.0, rx))
    body.parent = spin
    tag(body, "shell")
    chl = _cup_mesh(name + "Chloroplast", rx * 0.9, ry * 0.9, rx * 0.9)
    chl.parent = spin
    if mats.get("chloro"):
        chl.data.materials.append(mats["chloro"])
    tag(chl, "structure")
    pyr = _sphere(name + "Pyrenoid", 1.1 * u, (0, -ry * 0.6, 0), mats.get("pyrenoid"), scale=(1, 0.85, 1), seg=24, rings=14)
    pyr.parent = spin
    tag(pyr, "structure")
    nuc = _sphere(name + "Nucleus", 1.5 * u, (0, ry * 0.15, 0), mats.get("nucleus"), seg=28, rings=16)
    nuc.parent = spin
    tag(nuc, "structure")
    ex, ey, ez = eyespot_local()
    eye = _sphere(name + "Eyespot", 0.75 * u, (ex * u, ey * u, ez * u), mats.get("eyespot"), scale=(0.35, 1.0, 1.0),
                  seg=20, rings=12)
    eye.parent = spin
    tag(eye, "emitter")
    vac = []
    for s in (-1, 1):
        v = _sphere(f"{name}Vacuole{s:+d}", 0.6 * u, (s * 0.9 * u, ry * 0.78, 0.4 * u), mats.get("vacuole"), seg=16, rings=10)
        v.parent = spin
        tag(v, "structure")
        vac.append(v)
    flag = []
    for s in (-1, 1):
        cu = bpy.data.curves.new(f"{name}Flagellum{s:+d}", "CURVE")
        cu.dimensions = "3D"
        cu.bevel_depth = 0.12 * u
        cu.bevel_resolution = 2
        cu.use_fill_caps = True
        sp = cu.splines.new("POLY")
        pts = flagellum_points(0.0, s)
        sp.points.add(len(pts) - 1)
        for pt, p in zip(sp.points, pts):
            pt.co = (p[0] * u, p[1] * u, p[2] * u, 1.0)
            pt.radius = 1.0
        sp.points[-1].radius = 0.5
        ob = bpy.data.objects.new(cu.name, cu)
        bpy.context.scene.collection.objects.link(ob)
        ob.parent = spin
        if mats.get("flagellum"):
            cu.materials.append(mats["flagellum"])
        tag(ob, "structure")
        flag.append((ob, s))
    return {"root": root, "spin": spin, "body": body, "chloroplast": chl, "nucleus": nuc, "pyrenoid": pyr,
            "eyespot": eye, "flagella": flag, "vacuoles": vac}


def beat(cell, f0, f1, period=12, phase0=0.0, step=2):
    """两根鞭毛 f0→f1 划桨，每 period 帧一拍（真实约 50 Hz，这里放慢，artistic）。曲线点 co 打关键帧。"""
    u = UNIT
    for ob, s in cell["flagella"]:
        sp = ob.data.splines[0]
        for f in range(f0, f1 + 1, step):
            ph = (phase0 + (f - f0) / period) % 1.0
            for pt, p in zip(sp.points, flagellum_points(ph, s)):
                pt.co = (p[0] * u, p[1] * u, p[2] * u, 1.0)
                pt.keyframe_insert("co", frame=f)


def spin(cell, f0, f1, turns_per_s=0.5, fps=24):
    """绕长轴自转（局部 Y）。"""
    sp = cell["spin"]
    sp.rotation_euler = (0, 0, 0)
    sp.keyframe_insert("rotation_euler", frame=f0)
    sp.rotation_euler = (0, 2 * math.pi * turns_per_s * (f1 - f0) / fps, 0)
    sp.keyframe_insert("rotation_euler", frame=f1)
    if sp.animation_data and sp.animation_data.action:
        import common as C
        for fc in C.fcurves(sp.animation_data.action):
            for kp in fc.keyframe_points:
                kp.interpolation = "LINEAR"


def heading_euler(direction):
    """把局部 +Y（细胞前端）转到 direction 的欧拉角。"""
    from mathutils import Vector
    return Vector(direction).normalized().to_track_quat("Y", "Z").to_euler()


def swim(cell, path, f0, f1, step=3):
    """细胞沿 path（BU 点列）从 f0 游到 f1，前端始终朝运动方向（转向就是路径拐弯）。"""
    import e2_shot as S
    from mathutils import Vector
    root = cell["root"]
    seg = [math.dist(path[i], path[i + 1]) for i in range(len(path) - 1)]
    tot = sum(seg) or 1.0
    prev_e = None
    for f in list(range(f0, f1 + 1, step)) + [f1]:
        s = S.smooth((f - f0) / max(1, f1 - f0)) * 0.3 + (f - f0) / max(1, f1 - f0) * 0.7
        d = s * tot
        for i, L in enumerate(seg):
            if d <= L or i == len(seg) - 1:
                t = 0 if L == 0 else min(1.0, d / L)
                p = Vector(path[i]).lerp(Vector(path[i + 1]), t)
                dirv = Vector(path[i + 1]) - Vector(path[i])
                break
            d -= L
        root.location = p
        root.keyframe_insert("location", frame=f)
        e = heading_euler(dirv)
        if prev_e is not None:
            e.make_compatible(prev_e)
        root.rotation_euler = e
        root.keyframe_insert("rotation_euler", frame=f)
        prev_e = e


def build_oocyte(name, loc=(0, 0, 0), r=1.0, mats=None, sites=6, seed=4, tag=None):
    """爪蟾卵母细胞：动物极半球 + 植物极半球 + 赤道带（三个对象，便于分别上材质）+ 膜上 sites 个通道位点（短圆柱，朝外）。
    动物极朝 +Z。返回 dict(root, animal, vegetal, band, sites=[obj], site_locs=[world xyz])。"""
    import bmesh
    import bpy
    from mathutils import Vector
    tag = tag or (lambda o, r_: o)
    mats = mats or {}
    rnd = random.Random(seed)
    root = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(root)
    root.location = loc

    def cap(nm, lat0, lat1, mat):
        bm = bmesh.new()
        seg, rings = 64, 18
        rows = []
        for i in range(rings + 1):
            lat = lat0 + (lat1 - lat0) * i / rings
            rows.append([bm.verts.new((r * math.cos(lat) * math.cos(2 * math.pi * j / seg),
                                       r * math.cos(lat) * math.sin(2 * math.pi * j / seg), r * math.sin(lat)))
                         for j in range(seg)])
        for a, b in zip(rows[:-1], rows[1:]):
            for j in range(seg):
                bm.faces.new((a[j], a[(j + 1) % seg], b[(j + 1) % seg], b[j]))
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
        for f in bm.faces:
            f.smooth = True
        me = bpy.data.meshes.new(nm)
        bm.to_mesh(me)
        bm.free()
        ob = bpy.data.objects.new(nm, me)
        bpy.context.scene.collection.objects.link(ob)
        ob.parent = root
        if mat is not None:
            ob.data.materials.append(mat)
        tag(ob, "structure")
        return ob

    band = math.radians(7)
    animal = cap(name + "Animal", band, math.pi / 2, mats.get("animal"))
    bandob = cap(name + "Band", -band, band, mats.get("band"))
    vegetal = cap(name + "Vegetal", -math.pi / 2, -band, mats.get("vegetal"))
    objs, locs = [], []
    for i in range(sites):
        lat = math.radians(rnd.uniform(-20, 55))
        lon = math.radians(-60 + 120 * i / max(1, sites - 1) + rnd.uniform(-8, 8))   # 都在朝 -Y（镜头）那一侧
        n = Vector((math.cos(lat) * math.sin(lon), -math.cos(lat) * math.cos(lon), math.sin(lat)))
        bpy.ops.mesh.primitive_cylinder_add(radius=0.035 * r, depth=0.05 * r, location=tuple(n * r), vertices=16)
        c = bpy.context.object
        c.name = f"{name}Site{i}"
        c.rotation_euler = n.to_track_quat("Z", "Y").to_euler()
        c.parent = root
        if mats.get("site") is not None:
            c.data.materials.append(mats["site"])
        tag(c, "structure")
        objs.append(c)
        locs.append(tuple(Vector(loc) + n * r))
    return {"root": root, "animal": animal, "vegetal": vegetal, "band": bandob, "sites": objs, "site_locs": locs}
