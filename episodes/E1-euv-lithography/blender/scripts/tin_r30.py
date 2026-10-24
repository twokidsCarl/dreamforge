"""Round 30 tin step 4 = liquid SHAPE (R30_ROOT_CAUSE row 3; MAIN process recipe - looked at 8 + 32 spp before use).

R29 p1 (A0_01): 「55 % 帧的薄饼读起来像一面玻璃或金属盘子，中间还有一团白色污斑…要改成液态锡：边缘不规则、带溅射卷边和
细碎飞沫，表面是熔融金属的高光，不要整片镜面反射」; B1_10: 「像一张玻璃或铝箔片，表面有大块污白反光。改成液态金属：边缘
不规则，有冠状溅射，有薄处透亮的边」. R25-R29 tuned only the REFLECTION (stripes / uniform / decals / soft mirror); the
silhouette stayed a perfect flat disc, which is what reads as a plate. tin_r29's reflection recipe stays as it is; R30
changes the GEOMETRY of the sheet mesh in place (keeps every key / visibility / material of the R29 sheet):
  * irregular outline: radius x (1 + low-frequency + mid-frequency noise of the angle), weighted to the outer part;
  * crown lip: the outer ring curls back out of the sheet plane (away from the camera) and rises into 9-13 finger
    tips of different lengths (a splash crown, not a bead ring);
  * molten surface: a shallow impact dimple + a few broad random swells (no concentric rings - R25 「条纹星球」), so the
    one soft key reflection breaks into curved highlights instead of one 「白色污斑」;
  * thin translucent rim: a per-vertex `r30rim` weight drives a soft cool-white glow + transmission on a copy of the
    sheet material (thin metal edge with light coming through);
  * 4-6 detached droplets beyond the crown on the back-lit side (part of the same mesh -> same visibility).
"""
import math
import random

import bpy
from mathutils import Vector

RIM0 = 0.72           # radius (sheet units, disc radius ~1) where the crown starts
LIP = 0.09            # how far the crown curls out of the plane at the rim
FINGERS = 11
EDGE_NOISE = 0.09
SWELL = 0.025
RIM_GLOW = 0.22


def _noise1(rnd, n):
    ph = [rnd.uniform(0, 2 * math.pi) for _ in range(n)]
    am = [rnd.uniform(0.5, 1.0) / (k + 1) for k in range(n)]
    return lambda t: sum(a * math.sin((k + 2) * t + p) for k, (a, p) in enumerate(zip(am, ph))) / sum(am)


def _smooth(e0, e1, x):
    t = min(1.0, max(0.0, (x - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)


def shape(sc, shot, frame, seed=30, name="Pancake"):
    import bmesh
    sh = bpy.data.objects.get(name)
    root = bpy.data.objects.get("PancakeRoot")
    if sh is None or root is None:
        print(f"[tin_r30] {shot}: no {name}", flush=True)
        return None
    sc.frame_set(frame)
    cam_l = (sh.matrix_world.inverted() @ sc.camera.matrix_world.translation)
    away = -1.0 if cam_l.x > 0 else 1.0                  # curl the crown away from the camera (sheet normal = local X)
    rnd = random.Random(seed)
    rnd_state = seed
    edge = _noise1(rnd, 5)
    fing = [(rnd.uniform(0, 2 * math.pi), rnd.uniform(0.6, 1.25)) for _ in range(FINGERS)]
    fing.sort()
    swells = [(rnd.uniform(-0.6, 0.6), rnd.uniform(-0.6, 0.6), rnd.uniform(0.25, 0.45), rnd.choice((-1, 1)))
              for _ in range(5)]
    me = sh.data
    bm = bmesh.new()
    bm.from_mesh(me)
    rimw = {}
    for v in bm.verts:
        x, y, z = v.co
        r = math.hypot(y, z)
        if r < 1e-6:
            rimw[v.index] = 0.0
            continue
        t = math.atan2(z, y)
        w = _smooth(0.35, 1.0, r)
        # fingers: narrow angular bumps at the rim (crown tips)
        f = 0.0
        for (tf, ln) in fing:
            dt = math.atan2(math.sin(t - tf), math.cos(t - tf))
            f = max(f, ln * math.exp(-(dt / 0.09) ** 2))
        lip_w = _smooth(RIM0, 1.02, r)
        k = 1.0 + EDGE_NOISE * edge(t) * w + 0.11 * f * lip_w
        ny, nz = y * k, z * k
        # crown curl out of the plane + molten swells + impact dimple
        dx = away * LIP * (lip_w ** 1.5) * (1.0 + 0.9 * f)
        for (cy, cz, s, sg) in swells:
            dx += sg * SWELL * math.exp(-((y - cy) ** 2 + (z - cz) ** 2) / (s * s)) * (1 - lip_w) * _smooth(0.18, 0.4, r)
        v.co = Vector((x + dx, ny, nz))
        rimw[v.index] = lip_w
    # detached droplets beyond the crown, on the side away from the camera key (back-lit side = +angle half)
    n_drop = 0
    for i in range(rnd.randint(4, 6)):
        t = rnd.uniform(0.2, 2.6)
        rr = rnd.uniform(1.18, 1.45)
        rad = rnd.uniform(0.022, 0.04)
        c = Vector((away * (LIP + rnd.uniform(0.05, 0.2)), rr * math.cos(t), rr * math.sin(t)))
        res = bmesh.ops.create_icosphere(bm, subdivisions=2, radius=rad)
        for v in res["verts"]:
            v.co = v.co + c
        n_drop += 1
    bm.verts.index_update()
    bm.to_mesh(me)
    _follow(rnd_state, away, sh)
    bm.free()
    at = me.attributes.get("r30rim") or me.attributes.new("r30rim", "FLOAT", "POINT")
    for i, d in enumerate(at.data):
        d.value = rimw.get(i, 1.0)
    me.update()
    for p in me.polygons:
        p.use_smooth = True
    _rim_material(sh)
    print(f"[tin_r30] {shot} {name} reshaped: crown lip {LIP} x{FINGERS} fingers, edge noise {EDGE_NOISE}, swells 5, "
          f"{n_drop} detached drops, curl {'+' if away > 0 else '-'}X", flush=True)
    return sh


def _field(seed, away):
    """the same outline / crown displacement as shape() (no swells, no drops) for meshes riding on the sheet rim."""
    rnd = random.Random(seed)
    edge = _noise1(rnd, 5)
    fing = sorted((rnd.uniform(0, 2 * math.pi), rnd.uniform(0.6, 1.25)) for _ in range(FINGERS))

    def f_(co):
        x, y, z = co
        r = math.hypot(y, z)
        if r < 1e-6:
            return Vector(co)
        t = math.atan2(z, y)
        w = _smooth(0.35, 1.0, r)
        f = 0.0
        for (tf, ln) in fing:
            dt = math.atan2(math.sin(t - tf), math.cos(t - tf))
            f = max(f, ln * math.exp(-(dt / 0.09) ** 2))
        lip_w = _smooth(RIM0, 1.02, r)
        k = 1.0 + EDGE_NOISE * edge(t) * w + 0.11 * f * lip_w
        return Vector((x + away * LIP * (lip_w ** 1.5) * (1.0 + 0.9 * f), y * k, z * k))
    return f_


def _follow(seed, away, sh):
    """meshes parented to the sheet's root that sit on its rim (R24 hot edge / afterglow) follow the new outline."""
    root = sh.parent
    fx = _field(seed, away)
    for o in bpy.data.objects:
        if o is sh or o.type != "MESH" or o.parent is not root or not o.name.startswith(("TinAfterglow", "PancakeHot", "PancakeRim", "PancakeEdge")):
            continue
        M = sh.matrix_world.inverted() @ o.matrix_world
        Mi = M.inverted()
        for v in o.data.vertices:
            v.co = Mi @ fx(M @ v.co)
        o.data.update()
        print(f"[tin_r30] {o.name} follows the new rim", flush=True)


def _rim_material(ob):
    for s in ob.material_slots:
        m = s.material
        if m is None or not m.use_nodes or m.get("r30rim"):
            continue
        m2 = m.copy()
        m2.name = m.name + "_R30rim"
        m2["r30rim"] = True
        N, L = m2.node_tree.nodes, m2.node_tree.links
        b = next((n for n in N if n.type == "BSDF_PRINCIPLED"), None)
        if b is None:
            continue
        at = N.new("ShaderNodeAttribute")
        at.attribute_name = "r30rim"
        mul = N.new("ShaderNodeMath")
        mul.operation = "MULTIPLY"
        mul.inputs[1].default_value = RIM_GLOW
        L.new(at.outputs["Fac"], mul.inputs[0])
        try:
            b.inputs["Emission Color"].default_value = (0.80, 0.86, 1.0, 1)
            L.new(mul.outputs[0], b.inputs["Emission Strength"])
            tr = N.new("ShaderNodeMath")
            tr.operation = "MULTIPLY"
            tr.inputs[1].default_value = 0.15
            L.new(at.outputs["Fac"], tr.inputs[0])
            L.new(tr.outputs[0], b.inputs["Transmission Weight"])
        except KeyError:
            pass
        s.material = m2
