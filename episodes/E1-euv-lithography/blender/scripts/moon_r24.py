"""Round 24 hook (owned by the 'moon' sub-agent; shots in r2_misc.R24_MOON = {"B4_10"}). R24_ROOT_CAUSE row 4.

R23 review B4_10: 「85 % 帧月面是程序化噪声地形：拉丝纹、浮空的石块、长条阴影，一眼 CG…换真实月面 DEM 或摄影测量地块，石块落地
贴地，太阳角压低，阴影边缘做实」「高尔夫球的凹坑偏少偏大。改法：换标准凹坑法线贴图，加一点次表面和接触阴影」.
Base = R22 build (B4_10 is not in R23_MISC). Only the close-up beat (from 0.62 n, like R22) is touched; frames <= 0.55 n
(Earth 25 % / Moon 55 %) keep R23 pixels.
- ground: the R22 procedural regolith cap + RocksR22 are deleted. New ground = a tangent disc (12 m) under the ball,
  displaced by REAL data: Poly Haven "Gravelly Sand" photogrammetry height map (CC0, 0.5 m tile) for the cm-scale
  regolith and a crop of the NASA LOLA DEM (ldem_3_8bit, public domain) for the distant relief / horizon; colour = the
  photogrammetry albedo desaturated to lunar grey + its normal map. Files: blender/textures/moon/ (README.txt).
- rocks: a few dozen stones, half buried (centre on the local ground height, 45-55 % of their height below it) ->
  contact shadows, nothing floating; no upright spikes (low, rounded, flattened).
- sun ~7 deg above the local horizon, angular size 0.25 deg -> hard shadow edges; side / back light.
- golf ball: rebuilt with a standard geodesic dimple layout (362 dimples, spherical-cap profile, ~78 % coverage),
  a touch of subsurface; sits 2.5 mm into the regolith (contact).
- camera (keys at 0.75 n and n only; earlier keys untouched): low view (~8 deg), horizon + black sky in the top
  quarter, ball at the R18 overlay leader point (0.52, 0.45) via lens shift keyed from the close-up beat.
"""
import math
import os
import random

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector, kdtree, noise

TEX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "textures", "moon")
SUN_ELEV = 7.0
TILE = 0.5           # photogrammetry tile size (m) on the ground
A_FINE = 0.0045      # photogrammetry height amplitude (m)
A_DEM = 0.9          # LOLA relief amplitude (m) far from the ball
DISC = 12.0
GTEX = "gravelly_sand"   # Poly Haven CC0 photogrammetry ground (textures/moon/README.txt)


def pre(variant, shot, mod):
    pass


def _img(name):
    p = os.path.normpath(os.path.join(TEX, name))
    im = bpy.data.images.load(p, check_existing=True)
    return im


def _arr(im):
    w, h = im.size
    a = np.empty(w * h * 4, dtype=np.float32)
    im.pixels.foreach_get(a)
    return a.reshape(h, w, 4)[:, :, 0].copy()


def _bilerp(A, x, y, wrap=True):
    h, w = A.shape
    if wrap:
        x = np.mod(x, w)
        y = np.mod(y, h)
    else:
        x = np.clip(x, 0, w - 1.001)
        y = np.clip(y, 0, h - 1.001)
    x0 = np.floor(x).astype(np.int64)
    y0 = np.floor(y).astype(np.int64)
    fx, fy = x - x0, y - y0
    x1, y1 = (x0 + 1) % w, (y0 + 1) % h
    x0 %= w
    y0 %= h
    return (A[y0, x0] * (1 - fx) * (1 - fy) + A[y0, x1] * fx * (1 - fy) + A[y1, x0] * (1 - fx) * fy
            + A[y1, x1] * fx * fy)


class Ground:
    def __init__(self):
        self.disp = _arr(_img(GTEX + "_disp_2k.jpg"))
        dem = _arr(_img("ldem_3_8bit.jpg"))           # 1024 x 512 equirect, row 0 = bottom (Blender pixel order)
        # crop: southern highlands around Tycho (lon -11, lat -43): heavily cratered, real relief
        h, w = dem.shape
        cx, cy = int((-11 + 180) / 360 * w), int((-43 + 90) / 180 * h)
        self.dem = dem[cy - 40:cy + 40, cx - 40:cx + 40].copy()
        self.dem -= self.dem.mean()
        self.dem /= max(1e-6, np.abs(self.dem).max())

    def h(self, u, v):
        u = np.asarray(u, dtype=np.float64)
        v = np.asarray(v, dtype=np.float64)
        n = self.disp.shape[0]
        fine = _bilerp(self.disp, (u / TILE) * n, (v / TILE) * n) * A_FINE
        dn = self.dem.shape[0]
        big = _bilerp(self.dem, (u / (2 * DISC) + 0.5) * (dn - 1), (v / (2 * DISC) + 0.5) * (dn - 1), wrap=False)
        d = np.hypot(u, v)
        wb = np.clip((d - 1.0) / 3.0, 0, 1) ** 1.5
        return fine + big * A_DEM * wb


def _tangent(nrm):
    t1 = nrm.cross(Vector((0, 0, 1)))
    if t1.length < 1e-3:
        t1 = nrm.cross(Vector((1, 0, 0)))
    t1.normalize()
    return t1, nrm.cross(t1).normalized()


def _ground_mat():
    m = bpy.data.materials.new("RegolithR24")
    m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    bs = next(x for x in N if x.type == "BSDF_PRINCIPLED")
    uv = N.new("ShaderNodeUVMap")
    tx = N.new("ShaderNodeTexImage")
    tx.image = _img(GTEX + "_diff_2k.jpg")
    L.new(uv.outputs["UV"], tx.inputs["Vector"])
    hs = N.new("ShaderNodeHueSaturation")
    hs.inputs["Saturation"].default_value = 0.08
    hs.inputs["Value"].default_value = 1.0
    L.new(tx.outputs["Color"], hs.inputs["Color"])
    bc = N.new("ShaderNodeBrightContrast")
    bc.inputs["Bright"].default_value = 0.0
    bc.inputs["Contrast"].default_value = 0.15
    L.new(hs.outputs["Color"], bc.inputs["Color"])
    gm = N.new("ShaderNodeGamma")
    gm.inputs["Gamma"].default_value = 0.95
    L.new(bc.outputs["Color"], gm.inputs["Color"])
    L.new(gm.outputs["Color"], bs.inputs["Base Color"])
    bs.inputs["Roughness"].default_value = 1.0
    if "Specular IOR Level" in bs.inputs:
        bs.inputs["Specular IOR Level"].default_value = 0.1
    nt = N.new("ShaderNodeTexImage")
    nt.image = _img(GTEX + "_nor_gl_2k.jpg")
    nt.image.colorspace_settings.name = "Non-Color"
    L.new(uv.outputs["UV"], nt.inputs["Vector"])
    nm = N.new("ShaderNodeNormalMap")
    nm.inputs["Strength"].default_value = 1.0
    L.new(nt.outputs["Color"], nm.inputs["Color"])
    L.new(nm.outputs["Normal"], bs.inputs["Normal"])
    return m


def _rock_mat():
    m = bpy.data.materials.new("RockR24")
    m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    bs = next(x for x in N if x.type == "BSDF_PRINCIPLED")
    tc = N.new("ShaderNodeTexCoord")
    mp = N.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (3.0, 3.0, 3.0)
    L.new(tc.outputs["Object"], mp.inputs["Vector"])
    tx = N.new("ShaderNodeTexImage")
    tx.image = _img(GTEX + "_diff_2k.jpg")
    tx.projection = "BOX"
    tx.projection_blend = 0.3
    L.new(mp.outputs["Vector"], tx.inputs["Vector"])
    hs = N.new("ShaderNodeHueSaturation")
    hs.inputs["Saturation"].default_value = 0.06
    hs.inputs["Value"].default_value = 0.95
    L.new(tx.outputs["Color"], hs.inputs["Color"])
    L.new(hs.outputs["Color"], bs.inputs["Base Color"])
    bs.inputs["Roughness"].default_value = 0.9
    nz = N.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 400.0
    nz.inputs["Detail"].default_value = 6.0
    L.new(tc.outputs["Object"], nz.inputs["Vector"])
    bp = N.new("ShaderNodeBump")
    bp.inputs["Strength"].default_value = 0.5
    bp.inputs["Distance"].default_value = 0.0008
    L.new(nz.outputs["Fac"], bp.inputs["Height"])
    L.new(bp.outputs["Normal"], bs.inputs["Normal"])
    return m


def _build_ground(sc, G, p0, nrm, t1, t2):
    NR, NS = 760, 1000
    rings = np.concatenate([[0.0], 0.0015 * (DISC / 0.0015) ** (np.arange(NR) / (NR - 1))])
    ang = 2 * np.pi * np.arange(NS) / NS
    D, A = np.meshgrid(rings[1:], ang, indexing="ij")
    U = np.concatenate([[0.0], (D * np.cos(A)).ravel()])
    V = np.concatenate([[0.0], (D * np.sin(A)).ravel()])
    H = G.h(U, V)
    P0, N_, T1, T2 = (np.array(x[:]) for x in (p0, nrm, t1, t2))
    co = P0[None] + U[:, None] * T1[None] + V[:, None] * T2[None] + H[:, None] * N_[None]
    faces = []
    idx = lambda r, s: 1 + r * NS + (s % NS)            # noqa: E731
    s = np.arange(NS)
    tri = np.stack([np.zeros(NS, dtype=np.int64), idx(0, s), idx(0, s + 1)], 1)
    r = np.arange(NR - 1)[:, None]
    q = np.stack([idx(r, s[None]), idx(r + 1, s[None]), idx(r + 1, s[None] + 1), idx(r, s[None] + 1)], -1).reshape(-1, 4)
    me = bpy.data.meshes.new("RegolithR24")
    nv = co.shape[0]
    me.vertices.add(nv)
    me.vertices.foreach_set("co", co.astype(np.float32).ravel())
    nl = tri.size + q.size
    nf = tri.shape[0] + q.shape[0]
    me.loops.add(nl)
    me.loops.foreach_set("vertex_index", np.concatenate([tri.ravel(), q.ravel()]).astype(np.int32))
    me.polygons.add(nf)
    ls = np.concatenate([np.arange(tri.shape[0]) * 3, tri.size + np.arange(q.shape[0]) * 4]).astype(np.int32)
    lt = np.concatenate([np.full(tri.shape[0], 3), np.full(q.shape[0], 4)]).astype(np.int32)
    me.polygons.foreach_set("loop_start", ls)
    me.polygons.foreach_set("loop_total", lt)
    me.update(calc_edges=True)
    me.validate()
    uvl = me.uv_layers.new(name="UVMap")
    vi = np.empty(len(me.loops), dtype=np.int32)
    me.loops.foreach_get("vertex_index", vi)
    uvs = np.stack([U[vi] / TILE, V[vi] / TILE], 1).astype(np.float32)
    uvl.data.foreach_set("uv", uvs.ravel())
    me.polygons.foreach_set("use_smooth", np.ones(nf, dtype=bool))
    if me.polygons[nf // 2].normal.dot(nrm) < 0:
        me.flip_normals()
    ob = bpy.data.objects.new("RegolithR24", me)
    sc.collection.objects.link(ob)
    me.materials.append(_ground_mat())
    return ob


def _rocks(sc, G, p0, nrm, t1, t2, b, rb, hit_dir, cam_h, rnd):
    bm = bmesh.new()
    items = []
    for _ in range(26):           # stones 1-3.5 cm across, 6-40 cm from the ball
        items.append((0.06 + 0.34 * rnd.random() ** 0.8, rnd.random() * 2 * math.pi, 0.005 + 0.012 * rnd.random() ** 2))
    for _ in range(160):          # gravel 3-8 mm
        items.append((0.035 + 0.5 * rnd.random() ** 1.3, rnd.random() * 2 * math.pi, 0.0015 + 0.0025 * rnd.random()))
    n = 0
    for d, a, sz in items:
        u, v = d * math.cos(a), d * math.sin(a)
        w = t1 * u + t2 * v
        if w.length < rb + sz * 1.8:
            continue
        if hit_dir is not None:
            hh = (hit_dir - hit_dir.dot(nrm) * nrm).normalized()
            al = w.dot(hh)
            if al > 0 and (w - al * hh).length < 0.03 + sz:
                continue
        # keep the camera -> ball line clear
        al = w.dot(cam_h)
        if al > 0 and (w - al * cam_h).length < rb + sz + 0.01:
            continue
        hz = float(G.h(u, v))
        base = p0 + w + nrm * hz
        sx, sy = 0.8 + 0.4 * rnd.random(), 0.8 + 0.4 * rnd.random()
        sz_ = 0.5 + 0.2 * rnd.random()
        sink = (0.45 + 0.1 * rnd.random()) * sz * sz_ * 2       # 45-55 % of the full height below ground
        geom = bmesh.ops.create_icosphere(bm, subdivisions=3 if sz > 0.004 else 2, radius=sz)
        rot = nrm.to_track_quat("Z", "Y").to_matrix() @ Matrix.Rotation(rnd.random() * 6.28, 3, "Z")
        seed = Vector((rnd.random() * 100, rnd.random() * 100, rnd.random() * 100))
        for vt in geom["verts"]:
            c = vt.co
            j = 1.0 + 0.28 * noise.noise(c / sz * 1.2 + seed) + 0.08 * noise.noise(c / sz * 4 + seed)
            z = c.z * sz_ * j + sz * sz_ - sink                      # bottom at -sink
            vt.co = base + rot @ Vector((c.x * sx * j, c.y * sy * j, z))
        n += 1
    for f in bm.faces:
        f.smooth = True
    me = bpy.data.meshes.new("RocksR24")
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new("RocksR24", me)
    sc.collection.objects.link(ob)
    me.materials.append(_rock_mat())
    return ob, n


def _golf(ball, rb):
    """Standard geodesic dimple layout: vertices of a frequency-6 icosahedral geodesic = 362 dimples."""
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=1, radius=1.0)
    # frequency-6 geodesic: subdivide each icosahedron face into 36
    bm.free()
    import itertools  # noqa: F401
    phi = (1 + 5 ** 0.5) / 2
    V0 = [Vector(v).normalized() for v in [(-1, phi, 0), (1, phi, 0), (-1, -phi, 0), (1, -phi, 0), (0, -1, phi),
                                           (0, 1, phi), (0, -1, -phi), (0, 1, -phi), (phi, 0, -1), (phi, 0, 1),
                                           (-phi, 0, -1), (-phi, 0, 1)]]
    F0 = [(0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11), (1, 5, 9), (5, 11, 4), (11, 10, 2), (10, 7, 6),
          (7, 1, 8), (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9), (4, 9, 5), (2, 4, 11), (6, 2, 10),
          (8, 6, 7), (9, 8, 1)]
    fq = 6
    pts = []
    for a, b_, c in F0:
        A, B, C = V0[a], V0[b_], V0[c]
        for i in range(fq + 1):
            for j in range(fq + 1 - i):
                k = fq - i - j
                pts.append(((A * i + B * j + C * k) / fq).normalized())
    kd0 = kdtree.KDTree(len(pts))
    for i, p in enumerate(pts):
        kd0.insert(p, i)
    kd0.balance()
    cen = []
    for p in pts:
        if all((p - q).length > 1e-4 for q in cen[-200:]) and not any((p - q).length < 1e-4 for q in cen):
            cen.append(p)
    kd = kdtree.KDTree(len(cen))
    for i, c in enumerate(cen):
        kd.insert(c, i)
    kd.balance()
    dnn = min((cen[0] - c).length for c in cen[1:])
    ang0 = 0.5 * dnn * 0.96                         # dimple radius (chord) -> ~80 % coverage
    depth = 0.0105                                  # 0.25 mm on a 24 mm radius
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=7, radius=1.0)
    for v in bm.verts:
        u = v.co.normalized()
        c, i, d = kd.find(u)
        x = d / ang0
        h = depth * (1.0 - x * x) ** 0.5 if x < 1.0 else 0.0
        v.co = u * rb * (1.0 - h)
    for f in bm.faces:
        f.smooth = True
    old = ball.data
    me = bpy.data.meshes.new("GolfBallR24")
    bm.to_mesh(me)
    bm.free()
    for m in old.materials:
        me.materials.append(m)
    ball.data = me
    for m in me.materials:
        if m is None or not m.use_nodes:
            continue
        bs = next((x for x in m.node_tree.nodes if x.type == "BSDF_PRINCIPLED"), None)
        if bs is None:
            continue
        bs.inputs["Base Color"].default_value = (0.86, 0.86, 0.84, 1)
        bs.inputs["Roughness"].default_value = 0.35
        if "Subsurface Weight" in bs.inputs:
            bs.inputs["Subsurface Weight"].default_value = 0.12
            bs.inputs["Subsurface Radius"].default_value = (1.0, 0.9, 0.8)
            bs.inputs["Subsurface Scale"].default_value = 0.0015
        if "Coat Weight" in bs.inputs:
            bs.inputs["Coat Weight"].default_value = 0.35
            bs.inputs["Coat Roughness"].default_value = 0.12
    return len(cen)


GLOBE_LROC = True     # 55 % frame: Moon globe colour = NASA LROC WAC mosaic (near side toward Earth)


def _globe(moon):
    m = moon.active_material
    if m is None or not m.use_nodes:
        return False
    N, L = m.node_tree.nodes, m.node_tree.links
    bs = next((x for x in N if x.type == "BSDF_PRINCIPLED"), None)
    if bs is None:
        return False
    uv = N.new("ShaderNodeUVMap")
    tx = N.new("ShaderNodeTexImage")
    tx.image = _img("lroc_color_2k.jpg")
    L.new(uv.outputs["UV"], tx.inputs["Vector"])
    for lk in list(bs.inputs["Base Color"].links):
        L.remove(lk)
    L.new(tx.outputs["Color"], bs.inputs["Base Color"])
    E = Vector((0, 0, 0))
    d = E - moon.location
    moon.rotation_euler = (0.0, 0.0, math.atan2(d.y, d.x))    # LROC u = 0.5 (lon 0, near side) at local +X
    return True


def _vis_from(ob, f_on, path="hide_render"):
    ob.hide_render = True
    ob.keyframe_insert(path, frame=1)
    ob.keyframe_insert(path, frame=f_on - 1)
    ob.hide_render = False
    ob.keyframe_insert(path, frame=f_on)


def post(sc, variant, shot):
    if shot != "B4_10":
        return
    n = sc.frame_end
    f_on = round(n * 0.62)
    moon = bpy.data.objects.get("Moon")
    ball = bpy.data.objects.get("GolfBall")
    if moon is None or ball is None:
        print("[R24 B4_10] Moon / GolfBall missing - skipped")
        return
    if GLOBE_LROC:
        print(f"[R24 B4_10] globe LROC: {_globe(moon)}")
    for nm in ("RegolithR22", "RocksR22", "PebblesR23"):
        o = bpy.data.objects.get(nm)
        if o is not None:
            bpy.data.objects.remove(o, do_unlink=True)
    MO = moon.location.copy()
    b = ball.location.copy()
    rb = 0.024
    nrm = (b - MO).normalized()
    t1, t2 = _tangent(nrm)
    hit_dir = None
    for o in bpy.data.objects:
        if o.name.startswith("StationR17"):
            hit_dir = (o.location - b).normalized()
    G = Ground()
    # ball sits 2.5 mm into the regolith: mean ground height under the ball -> plane offset
    rr = np.linspace(0, rb * 0.5, 6)
    aa = np.linspace(0, 2 * np.pi, 12, endpoint=False)
    RR, AA = np.meshgrid(rr, aa)
    h0 = float(np.mean(G.h(RR * np.cos(AA), RR * np.sin(AA))))
    bbot = b - nrm * rb
    p0 = bbot + nrm * (0.0025 - h0)
    ground = _build_ground(sc, G, p0, nrm, t1, t2)
    _vis_from(ground, f_on)
    nd = _golf(ball, rb)
    # ---- camera (keys at 0.75 n and n): low, ball at the overlay leader point
    cam = sc.camera
    tgt = next(c.target for c in cam.constraints if c.type == "TRACK_TO")
    hb = (hit_dir - hit_dir.dot(nrm) * nrm).normalized() if hit_dir is not None else t1
    best = None
    for k in range(360):
        a = math.radians(k)
        f = (t1 * math.cos(a) + t2 * math.sin(a))          # horizontal forward (camera -> ball)
        R = f.cross(nrm)
        sc_ = -abs(hb.dot(f) - 0.45) - abs(hb.dot(R) + 0.89)   # beam arrives from the upper left, a bit from behind
        if best is None or sc_ > best[0]:
            best = (sc_, f, R)
    _, fwd, right = best
    cam_h = -fwd
    el = math.radians(8.0)

    def cpos(dist):
        return b + (cam_h * math.cos(el) + nrm * math.sin(el)) * dist
    # the Track-To constraint keeps world Z up -> the tilted lunar ground would roll the horizon; from the close-up
    # beat the constraint is switched off and the camera is keyed with the local ground normal as "up"
    con = next(c for c in cam.constraints if c.type == "TRACK_TO")
    f_cu = round(n * 0.75)
    con.influence = 1.0
    con.keyframe_insert("influence", frame=f_on)
    con.influence = 0.0
    con.keyframe_insert("influence", frame=f_cu)          # linear blend over the fly-in -> no roll pop
    cam.rotation_mode = "QUATERNION"
    for fr, dist in ((round(n * 0.75), 0.42), (n, 0.31)):
        cl = cpos(dist)
        cam.location = cl
        cam.keyframe_insert("location", frame=fr)
        tgt.location = b
        tgt.keyframe_insert("location", frame=fr)
    cd = cam.data
    for attr, v in (("shift_x", -0.02), ("shift_y", -0.028)):
        setattr(cd, attr, 0.0)
        cd.keyframe_insert(attr, frame=f_on)
        setattr(cd, attr, v)
        cd.keyframe_insert(attr, frame=f_cu)
    # Blender 5 slotted actions: object + data keys may share one action -> touch only the switch channels
    import kit_r2 as K
    for idb in (cam, cd):
        if idb.animation_data and idb.animation_data.action:
            for fc in K.C.fcurves(idb.animation_data.action):
                for kp in fc.keyframe_points:
                    if "shift" in fc.data_path or "influence" in fc.data_path:
                        kp.interpolation = "LINEAR"
                    else:
                        kp.interpolation = "BEZIER"
                        kp.easing = "EASE_IN_OUT"
    # per-frame look-at with the local ground normal as up (exact: ball stays on the leader point)
    for fr in range(f_on, n + 1):
        sc.frame_set(fr)
        cl = cam.location.copy()
        f3 = (b - cl).normalized()
        x3 = f3.cross(nrm).normalized()
        y3 = (-f3).cross(x3).normalized()
        cam.rotation_quaternion = Matrix((x3, y3, -f3)).transposed().to_quaternion()
        cam.keyframe_insert("rotation_quaternion", frame=fr)
    sc.frame_set(1)
    # ---- rocks (half buried)
    rocks, nrk = _rocks(sc, G, p0, nrm, t1, t2, b, rb, hit_dir, cam_h, random.Random(2410))
    _vis_from(rocks, f_on)
    # ---- low sun, hard edges: from the right, a bit behind the ball
    sun = bpy.data.objects.get("SunLowR22")
    e = math.radians(SUN_ELEV)
    az = (right * 0.88 + fwd * 0.47).normalized()
    to_sun = (az * math.cos(e) + nrm * math.sin(e)).normalized()
    if sun is not None:
        sun.rotation_euler = (-to_sun).to_track_quat("-Z", "Y").to_euler()
        sun.data.angle = math.radians(0.25)
        sun.data.energy = 6.0
    from bpy_extras.object_utils import world_to_camera_view as w2c
    for fr in (round(n * 0.75), round(n * 0.85), n):
        sc.frame_set(fr)
        v = w2c(sc, cam, b)
        print(f"[R24 B4_10] f{fr} ball screen ({v.x:.3f},{1 - v.y:.3f}) dist {(cam.matrix_world.translation - b).length:.3f}")
    sc.frame_set(1)
    print(f"[R24 B4_10] ground {len(ground.data.vertices)} verts (photogrammetry disp + LOLA crop), rocks {nrk}, "
          f"dimples {nd}, sun {SUN_ELEV} deg, n={n} f_on={f_on}")
