"""R20 B8_17 (root cause #4, R19 review B8_17 #1-#3): 188 flat High-NA half-field rectangles + a scanning slit.

R19 review: 「按 26 × 16.5 mm 半场排出 188 个长方形格，满格时刚好 188」「光锥做成软边、从物镜收放，落点画成一条窄狭缝亮带，并沿扫描
方向移动」「未曝光格保持硅灰，已曝光格加紫色残辉」.
- Field grid: 26 x 16.5 mm (x10 scale: 0.26 x 0.165) on a 300 mm wafer (R 1.5). A 300 mm disc can hold at most ~164 FULL
  half-fields by area (70 686 / 429 mm^2), so the 188 exposure fields are the full fields + the partial edge fields a scanner
  also exposes; a field counts when it reaches >= 3 mm into the wafer. The grid offset is searched so this count is exactly
  188 (printed to the log), edge fields are clipped at the wafer rim.
- Scan order = column serpentine along y (the scan direction), so the slit (long in x, thin in y) travels perpendicular to its
  length down each column; same timing as R19 (fields done linearly by 0.9 n) so the counters still end at 188.
- Exposure light: the R19 hard cone is replaced by a soft-edged cone (fade-in below the lens port, soft (1-facing)^3 edge,
  brightest at the slit) that narrows from the projection-lens port to the slit band.
- Unexposed fields: opaque silicon grey; exposed: faint violet afterglow; the field under the slit: bright.
Called from r2_misc._wafer only when B8_17 is in R20_SHOTS.
"""
import math

import bmesh
import bpy
from mathutils import Vector

import kit_r2 as K

FX, FY, COUNT, EDGE = 0.26, 0.165, 188, 0.03


def _near(cx, cy):
    dx = max(abs(cx) - FX / 2, 0.0)
    dy = max(abs(cy) - FY / 2, 0.0)
    return math.hypot(dx, dy)


def layout(R):
    """Grid offset with exactly COUNT fields reaching >= EDGE into the wafer; prefer x-symmetric (ox = 0)."""
    best = None
    for b in range(66):
        for a in range(52):
            ox, oy = a / 52 * FX, b / 66 * FY
            cells = [(i, j, i * FX + ox, j * FY + oy) for i in range(-9, 10) for j in range(-13, 14)
                     if _near(i * FX + ox, j * FY + oy) < R - EDGE]
            if len(cells) == COUNT:
                sc_ = (min(ox, FX - ox), abs(oy - FY / 2))
                if best is None or sc_ < best[0]:
                    best = (sc_, ox, oy, cells)
    _, ox, oy, cells = best
    full = sum(1 for (_, _, cx, cy) in cells
               if all(math.hypot(cx + sx * FX / 2, cy + sy * FY / 2) <= R for sx in (-1, 1) for sy in (-1, 1)))
    print(f"[R20 B8_17] field grid offset ox={ox:.4f} oy={oy:.4f}: {len(cells)} fields ({full} full + "
          f"{len(cells) - full} edge) of 26 x 16.5 mm on 300 mm")
    # column serpentine along y (scan direction)
    cols = sorted({c[0] for c in cells})
    order = []
    for ci, i in enumerate(cols):
        col = sorted([c for c in cells if c[0] == i], key=lambda c: c[1], reverse=(ci % 2 == 1))
        order += col
    assert len(order) == COUNT
    return order


def _op(N, L, op, a, b):
    m = N.new("ShaderNodeMath")
    m.operation = op
    for k, x in enumerate((a, b)):
        if isinstance(x, (int, float)):
            m.inputs[k].default_value = x
        else:
            L.new(x, m.inputs[k])
    return m.outputs[0]


def _field_mat(n, R):
    m = bpy.data.materials.new("FieldR20")
    m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    for x in list(N):
        if x.type != "OUTPUT_MATERIAL":
            N.remove(x)
    out = next(x for x in N if x.type == "OUTPUT_MATERIAL")
    uv = N.new("ShaderNodeUVMap")
    uv.uv_map = "UVMap"
    sep = N.new("ShaderNodeSeparateXYZ")
    L.new(uv.outputs["UV"], sep.inputs[0])
    prog = N.new("ShaderNodeValue")
    for f, v in ((1, 0.0), (round(n * 0.9), 1.0)):
        prog.outputs[0].default_value = v
        prog.outputs[0].keyframe_insert("default_value", frame=f)
    try:
        for fc in m.node_tree.animation_data.action.fcurves:
            for kp in fc.keyframe_points:
                kp.interpolation = "LINEAR"
    except Exception:
        import common as C
        for fc in C.fcurves(m.node_tree.animation_data.action):
            for kp in fc.keyframe_points:
                kp.interpolation = "LINEAR"
    d = _op(N, L, "SUBTRACT", prog.outputs[0], sep.outputs["X"])
    exposed = _op(N, L, "GREATER_THAN", d, 0.0)
    hot = N.new("ShaderNodeMapRange")                     # the field under the slit right now
    hot.inputs["From Min"].default_value = 0.0
    hot.inputs["From Max"].default_value = 0.008
    hot.inputs["To Min"].default_value = 1.0
    hot.inputs["To Max"].default_value = 0.0
    L.new(d, hot.inputs["Value"])
    hotv = _op(N, L, "MULTIPLY", exposed, hot.outputs["Result"])
    # cell border (scribe line) from the per-field corner UV
    cuv = N.new("ShaderNodeUVMap")
    cuv.uv_map = "Cell"
    cs = N.new("ShaderNodeSeparateXYZ")
    L.new(cuv.outputs["UV"], cs.inputs[0])
    ex = _op(N, L, "MINIMUM", cs.outputs["X"], _op(N, L, "SUBTRACT", 1.0, cs.outputs["X"]))
    ey = _op(N, L, "MINIMUM", cs.outputs["Y"], _op(N, L, "SUBTRACT", 1.0, cs.outputs["Y"]))
    border = _op(N, L, "LESS_THAN", _op(N, L, "MINIMUM", _op(N, L, "MULTIPLY", ex, FX), _op(N, L, "MULTIPLY", ey, FY)), 0.004)
    # clip edge fields at the wafer rim
    tco = N.new("ShaderNodeTexCoord")
    ln = N.new("ShaderNodeVectorMath")
    ln.operation = "LENGTH"
    L.new(tco.outputs["Object"], ln.inputs[0])
    inside = _op(N, L, "LESS_THAN", ln.outputs["Value"], R * 0.985)
    # silicon grey field -> faint violet afterglow when exposed
    bs = N.new("ShaderNodeBsdfPrincipled")
    mixc = N.new("ShaderNodeMix")
    mixc.data_type = "RGBA"
    mixc.inputs["A"].default_value = (*K.lin((0.50, 0.51, 0.53)), 1)
    mixc.inputs["B"].default_value = (*K.lin((0.44, 0.40, 0.56)), 1)
    L.new(exposed, mixc.inputs["Factor"])
    L.new(mixc.outputs["Result"], bs.inputs["Base Color"])
    bs.inputs["Metallic"].default_value = 0.55
    bs.inputs["Roughness"].default_value = 0.3
    bs.inputs["Emission Color"].default_value = (*K.lin(K.VIOLET), 1)
    L.new(_op(N, L, "ADD", _op(N, L, "MULTIPLY", exposed, 0.1), _op(N, L, "MULTIPLY", hotv, 3.2)),
          bs.inputs["Emission Strength"])
    dark = N.new("ShaderNodeBsdfDiffuse")
    dark.inputs["Color"].default_value = (0.012, 0.012, 0.014, 1)
    m1 = N.new("ShaderNodeMixShader")
    L.new(border, m1.inputs["Fac"])
    L.new(bs.outputs[0], m1.inputs[1])
    L.new(dark.outputs[0], m1.inputs[2])
    tr = N.new("ShaderNodeBsdfTransparent")
    m2 = N.new("ShaderNodeMixShader")
    L.new(inside, m2.inputs["Fac"])
    L.new(tr.outputs[0], m2.inputs[1])
    L.new(m1.outputs[0], m2.inputs[2])
    L.new(m2.outputs[0], out.inputs["Surface"])
    return m


def apply(sc, n, R, so, fo_old, fc_old, keep_old, prog_old):
    import misc_beam_r18 as BR18
    order = layout(R)
    fo_old.hide_render = True
    # flat field rectangles (thin raised quads; scribe gap = border in the shader)
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    uvc = bm.loops.layers.uv.new("Cell")
    z = 0.0096
    for k, (_, _, cx, cy) in enumerate(order):
        vs = [bm.verts.new((cx + sx * FX / 2, cy + sy * FY / 2, z)) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        f = bm.faces.new(vs)
        for lp, (u, v) in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
            lp[uvl].uv = ((k + 0.5) / COUNT, 0.0)
            lp[uvc].uv = (u, v)
    me = bpy.data.meshes.new("FieldsR20")
    bm.to_mesh(me)
    bm.free()
    fo = bpy.data.objects.new("FieldsR20", me)
    sc.collection.objects.link(fo)
    me.materials.append(_field_mat(n, R))
    print(f"[R20 B8_17] FieldsR20 polygons = {len(me.polygons)}")
    # plain dark polished silicon under / between the fields (no die photo -> only the 188 rectangles read as fields)
    wo = bpy.data.objects.get("Wafer")
    if wo is not None:
        wo.data.materials[0] = K.mat("WaferPlainR20", (0.22, 0.225, 0.24), metal=0.8, rough=0.18)
    # slit: re-key its path in the new scan order (same timing as R19 -> counters agree)
    act = so.animation_data.action
    import common as C
    fcs = list(C.fcurves(act))
    for fc in fcs:
        if fc.data_path == "location":
            for kp in list(fc.keyframe_points)[::-1]:
                fc.keyframe_points.remove(kp)
    for k, (_, _, cx, cy) in enumerate(order):
        so.location = (cx, cy, 0.0105)
        so.keyframe_insert("location", frame=1 + (k / COUNT) * n * 0.9)
    so.keyframe_insert("location", frame=round(n * 0.9) + 2)
    for fc in C.fcurves(so.animation_data.action):
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR"
    # soft-edged cone: from the lens port narrowing to the slit band
    for ob in fc_old:
        ob.animation_data_clear()
        ob.hide_render = True
    PX, PY, PZ = 0.45, 1.3, 1.72
    obs, _emp = BR18.hooked_cone("SlitConeR20", (PX, PY, PZ + 0.02), (0.52, 0.2), (0.13, 0.006), so, K.VIOLET,
                                 1.0, 0.3, edge=3.0, inner=0.4, inner_gain=1.8, gain=2.5)
    for ob, st, al in zip(obs, (1.3, 2.0), (0.2, 0.26)):
        ob.data.materials[0] = BR18.cone_mat(ob.name + "M20", K.VIOLET, st, al, 3.0, 0.3, 0.0, 2.5)
        ob.hide_render = False
        ob.keyframe_insert("hide_render", frame=round(n * 0.9) + 2)
        ob.hide_render = True
        ob.keyframe_insert("hide_render", frame=round(n * 0.9) + 3)
