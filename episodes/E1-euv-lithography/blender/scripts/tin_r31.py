"""Round 31 tin step 5 = thin curved DISC, broken edge, high reflect, hot face (R31_ROOT_CAUSE row 2; MAIN process recipe -
looked at 8 + 32 spp before use).

R30 p1 (A0_01): 「薄饼像白瓷碗或玻璃壳…形状改成略带弧度的薄圆盘，不要深碗加波浪边；正对激光的一面加橙红热辉」; B1_10:
「薄饼的材质是哑光白瓷，形状像贝壳或碟子…做金属液膜的高反材质，形状改成薄盘，边缘破碎」「旁边还漂着几颗白色小球…删掉」.
R30 (tin_r30) kept the R24-R29 deep dish (local sag 0.30 of the radius) and added a crown lip curling out of the plane
plus a translucent glowing rim - together that is a white porcelain bowl / shell. R31 replaces tin_r30 for these shots
(source_r31 turns source_r30.SHAPE_R30 off for them) and reshapes the R29 sheet mesh in place:
  * the dish is flattened to a slight curve (local X x FLAT: sag 0.30 -> ~0.08 of the radius);
  * broken edge IN the sheet plane (no curl-up): low-frequency outline noise + NOTCHES narrow radial bites of
    different depths -> a torn, jagged rim; no crown, no fingers, no detached drops;
  * no rim glow / transmission (the R30 「透亮的边」 read as porcelain);
  * high-reflect liquid metal: the R29 tin material with metallic 1, roughness ROUGH, base a little darker silver;
  * hot face: orange-red emission, hottest at the centre where the pulse hit (radial weight r31hot), stronger on the
    face turned toward the laser (+ a residual glow on the far face: the whole thin sheet is hot).
"""
import math
import random

import bpy
from mathutils import Vector

FLAT = 0.40
EDGE_NOISE = 0.05
NOTCHES = 9
ROUGH = 0.07
SILVER = (0.80, 0.81, 0.84)
HOT = 4.0
HOT_COL = (1.0, 0.26, 0.04)
HOT_BACK = 0.60            # far-face share of the glow
HOT_R = 0.55               # hot core radius (sheet units)
RIPPLE = (2.3, 0.6, 0.21)  # molten surface: noise scale / detail / bump strength (breaks the one soft key into flowing highlights)
LASER_DIR = Vector((1.0, 0.0, 0.0))   # the pulses travel +X (LaserLight at -X of the drop)


def _noise1(rnd, n):
    ph = [rnd.uniform(0, 2 * math.pi) for _ in range(n)]
    am = [rnd.uniform(0.5, 1.0) / (k + 1) for k in range(n)]
    return lambda t: sum(a * math.sin((k + 2) * t + p) for k, (a, p) in enumerate(zip(am, ph))) / sum(am)


def _smooth(e0, e1, x):
    t = min(1.0, max(0.0, (x - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)


def _field(seed):
    rnd = random.Random(seed)
    edge = _noise1(rnd, 4)
    notch = [(rnd.uniform(0, 2 * math.pi), rnd.uniform(0.06, 0.20), rnd.uniform(0.035, 0.09)) for _ in range(NOTCHES)]

    def f_(co):
        x, y, z = co
        r = math.hypot(y, z)
        if r < 1e-6:
            return Vector((x * FLAT, y, z)), 0.0
        t = math.atan2(z, y)
        w = _smooth(0.55, 1.0, r)
        bite = 0.0
        for (tn, dp, wd) in notch:
            dt = math.atan2(math.sin(t - tn), math.cos(t - tn))
            bite = max(bite, dp * math.exp(-(dt / wd) ** 2))
        k = 1.0 + EDGE_NOISE * edge(t) * w - bite * _smooth(0.7, 1.0, r)
        return Vector((x * FLAT, y * k, z * k)), r
    return f_


def disc(sc, shot, frame, seed=31, name="Pancake"):
    sh = bpy.data.objects.get(name)
    if sh is None:
        print(f"[tin_r31] {shot}: no {name}", flush=True)
        return None
    fx = _field(seed)
    me = sh.data
    hot = []
    for v in me.vertices:
        p, r = fx(v.co)
        v.co = p
        hot.append(max(0.0, 1.0 - (r / HOT_R) ** 2) ** 2)
    at = me.attributes.get("r31hot") or me.attributes.new("r31hot", "FLOAT", "POINT")
    for i, d in enumerate(at.data):
        d.value = hot[i]
    me.update()
    root = sh.parent
    n_f = 0
    for o in bpy.data.objects:           # meshes riding on the sheet (R24 hot edge / afterglow / landing) follow it
        if o is sh or o.type != "MESH" or o.parent is not root or not o.name.startswith(("TinAfterglow", "PancakeHot", "PancakeRim", "PancakeEdge", "TinLanding")):
            continue
        M = sh.matrix_world.inverted() @ o.matrix_world
        Mi = M.inverted()
        for v in o.data.vertices:
            v.co = Mi @ fx(M @ v.co)[0]
        o.data.update()
        n_f += 1
    for o in bpy.data.objects:
        if o.name.startswith("PancakeDrops"):
            o.hide_render = True
    _material(sh)
    print(f"[tin_r31] {shot} {name}: disc flat x{FLAT}, {NOTCHES} edge notches, no crown / drops / rim glow, hot face "
          f"{HOT}, {n_f} riders follow", flush=True)
    return sh


def _material(ob):
    for s in ob.material_slots:
        m = s.material
        if m is None or not m.use_nodes or m.get("r31disc"):
            continue
        m2 = m.copy()
        m2.name = m.name.replace("_R30rim", "") + "_R31disc"
        m2["r31disc"] = True
        N, L = m2.node_tree.nodes, m2.node_tree.links
        b = next((n for n in N if n.type == "BSDF_PRINCIPLED"), None)
        if b is None:
            continue
        for n in N:
            if n.type == "TEX_NOISE":
                n.inputs["Scale"].default_value, n.inputs["Detail"].default_value = RIPPLE[0], RIPPLE[1]
            elif n.type == "BUMP":
                n.inputs["Strength"].default_value = RIPPLE[2]
        b.inputs["Metallic"].default_value = 1.0
        b.inputs["Roughness"].default_value = ROUGH
        if not b.inputs["Base Color"].is_linked:
            b.inputs["Base Color"].default_value = (*SILVER, 1)
        for k in ("Transmission Weight", "Emission Strength"):
            if k in b.inputs:
                for lk in list(b.inputs[k].links):
                    L.remove(lk)
                b.inputs[k].default_value = 0.0
        # hot face: r31hot x (HOT_BACK + (1 - HOT_BACK) * max(0, N . -laser)) x HOT
        at = N.new("ShaderNodeAttribute")
        at.attribute_name = "r31hot"
        geo = N.new("ShaderNodeNewGeometry")
        dot = N.new("ShaderNodeVectorMath")
        dot.operation = "DOT_PRODUCT"
        L.new(geo.outputs["Normal"], dot.inputs[0])
        dot.inputs[1].default_value = tuple(-LASER_DIR)
        mx = N.new("ShaderNodeMath")
        mx.operation = "MAXIMUM"
        L.new(dot.outputs["Value"], mx.inputs[0])
        mx.inputs[1].default_value = 0.0
        fa = N.new("ShaderNodeMath")
        fa.operation = "MULTIPLY_ADD"
        L.new(mx.outputs[0], fa.inputs[0])
        fa.inputs[1].default_value = 1.0 - HOT_BACK
        fa.inputs[2].default_value = HOT_BACK
        m1 = N.new("ShaderNodeMath")
        m1.operation = "MULTIPLY"
        L.new(at.outputs["Fac"], m1.inputs[0])
        L.new(fa.outputs[0], m1.inputs[1])
        m3 = N.new("ShaderNodeMath")
        m3.operation = "MULTIPLY"
        L.new(m1.outputs[0], m3.inputs[0])
        m3.inputs[1].default_value = HOT
        b.inputs["Emission Color"].default_value = (*HOT_COL, 1)
        L.new(m3.outputs[0], b.inputs["Emission Strength"])
        s.material = m2
