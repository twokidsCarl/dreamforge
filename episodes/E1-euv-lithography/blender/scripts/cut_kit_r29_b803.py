"""R29 kit B8_03 / B8_03M helper (cut_kit_r29.SCALE_R29 / GRID_R29, R29_ROOT_CAUSE row 4).

R28 p2 B8_03: 「晶圆台的反向运动只靠数字，画面里没有晶圆标尺，看不出晶圆在动」「晶圆旁加一条同款青色短标尺（0–10 mm）和指针，
与画中画同步移动，让 8:1 用眼睛就能看出来」「场格是正方形，High-NA 半场应为长方形；格数也没对上 188」.

SCALE (B8_03): the R28 thin white tick bar (WScaleBarR28 / WScaleTickR28, "too small to be seen") is removed. A cyan
0-10 mm ruler (same cyan emissive look as the PIP ruler) is built on a dark carrier plate FIXED in the world just behind
the wafer's back edge (hanging: base line on top, ticks + labels below, so nothing sits under the PIP), its plane containing world x (the scan axis) and turned to face the camera, so ticks read as a
ruler (not a comb), PIP ruler style (white ticks / numbers, cyan travel bar 0 -> pointer, cyan needle). 1 mm = k world m (measured from PtrW at the job frames, as R28: 0.02 m). Major ticks 0 / 5 / 10
with 3D labels (repo DejaVuSans-Bold / NotoSansSC; label cap height >= the PIP ruler labels, checked in px) and a title
「晶圆台」. A cyan pointer (triangle + stem) parented to WStage moves with the wafer along the ruler: -2.5 -> -5.5 -> -8.5
mm = the read-out, opposite to the reticle stage pointer in the PIP.
GRID (B8_03 / B8_03M): the wafer die map (cut_kit_r17.wafer_mat_r17 nodes, pitch 42 x 52.5 mm-world) is re-laid as
landscape half-fields 26 x 16.5 (x = scan / screen-horizontal, y): pitch 0.0611 x 0.0388 m, full-field centre radius
< 0.3758 -> exactly 188 fields (count printed). Exposed stripe logic untouched.
"""
import math

import bpy
from mathutils import Matrix, Vector

EP = "/workspace/eigenlens-e1/episodes/E1-euv-lithography"
FONT_L = EP + "/blender/textures/fonts/DejaVuSans-Bold.ttf"
FONT_C = EP + "/blender/textures/fonts/NotoSansSC-Bold-gb2312l1.otf"
FR = {42: -2.5, 143: -8.5}
PX, PY, TC = 0.0611, 0.0388, 0.3758
OLD = (0.042, 0.0525, 0.042 / 16, 0.0525 / 6, 0.42 - 0.035 - 0.042 * 0.6)
BAR_C = (-0.235, 0.712)         # ruler base-line y, z (R28 bar y -0.27..-0.20, z 0.68)
PL_H = 0.075                    # plate height below the base line
LAB_H = 0.036                   # label font size (world m)


def _near(a, b):
    return abs(a - b) < 1e-5


def grid(sc):
    w = bpy.data.objects.get("WStage_wafer")
    if w is None or not w.data.materials:
        print("[r29k b803] wafer missing", flush=True)
        return
    nt = w.data.materials[0].node_tree
    new = {OLD[0]: PX, OLD[1]: PY, OLD[2]: PX / 16, OLD[3]: PY / 6, OLD[4]: TC}
    hit = 0
    for n in nt.nodes:
        if n.type != "MATH":
            continue
        for i in (0, 1):
            s_ = n.inputs[i]
            if s_.is_linked:
                continue
            for o, v in new.items():
                if _near(s_.default_value, o):
                    s_.default_value = v
                    hit += 1
    cnt = sum(1 for i in range(-40, 40) for j in range(-40, 40)
              if math.hypot((i + 0.5) * PX, (j + 0.5) * PY) < TC)
    print(f"[r29k b803] grid nodes changed {hit}; half-fields {PX * 1000:.1f} x {PY * 1000:.1f} mm-world, full {cnt}",
          flush=True)


def _emit(name, col, st):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    N = m.node_tree.nodes
    for n in list(N):
        if n.type != "OUTPUT_MATERIAL":
            N.remove(n)
    out = next(n for n in N if n.type == "OUTPUT_MATERIAL")
    e = N.new("ShaderNodeEmission")
    e.inputs["Color"].default_value = (*col, 1)
    e.inputs["Strength"].default_value = st
    m.node_tree.links.new(e.outputs[0], out.inputs["Surface"])
    return m


def _plain(name, col, rough=0.5):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (*col, 1)
    b.inputs["Roughness"].default_value = rough
    return m


def _quads(name, quads, mat, parent, coll, dz=0.0):
    """quads: (u0, v0, u1, v1) rectangles or ('tri', p1, p2, p3) in the parent's local u/v plane."""
    verts, faces = [], []
    for q in quads:
        o = len(verts)
        if q[0] == "tri":
            verts += [(p[0], p[1], dz) for p in q[1:]]
            faces.append((o, o + 1, o + 2))
        else:
            u0, v0, u1, v1 = q
            verts += [(u0, v0, dz), (u1, v0, dz), (u1, v1, dz), (u0, v1, dz)]
            faces.append((o, o + 1, o + 2, o + 3))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    me.materials.append(mat)
    ob.parent = parent
    ob.visible_shadow = False
    return ob


def _text(name, body, font, size, uv, parent, coll, mat, align="CENTER"):
    cu = bpy.data.curves.new(name, "FONT")
    cu.body = body
    cu.font = font
    cu.size = size
    cu.align_x = align
    cu.align_y = "BOTTOM"
    ob = bpy.data.objects.new(name, cu)
    coll.objects.link(ob)
    cu.materials.append(mat)
    ob.parent = parent
    ob.location = (uv[0], uv[1], 0.002)
    ob.visible_shadow = False
    return ob


def scale(sc):
    for o in list(bpy.data.objects):
        if o.name.startswith(("WScaleBarR28", "WScaleTickR28")):
            bpy.data.objects.remove(o, do_unlink=True)
    ptr = bpy.data.objects.get("PtrW")
    st = bpy.data.objects.get("WStage")
    if ptr is None or st is None:
        print("[r29k b803] PtrW / WStage missing - no scale", flush=True)
        return
    f0 = sc.frame_current
    xs = {}
    for f in FR:
        sc.frame_set(f)
        bb = [ptr.matrix_world @ Vector(c) for c in ptr.bound_box]
        xs[f] = sum(v.x for v in bb) / 8
    (fa, da), (fb, db) = sorted(FR.items())
    k = (xs[fb] - xs[fa]) / (db - da)             # world m per mm (+0.02: -mm -> -x)
    x0 = xs[fa] - k * da                           # pointer x at 0 mm
    # placement: 8-spp try 1 (behind the wafer's back edge, labels above the ticks) put the labels under the PIP frame;
    # try 2 (left of the wafer) left the frame by f92 (the camera push-in moves off-centre points out). Final: the R28
    # spot behind the back edge (stays near frame centre, +37 px drift) but HANGING: base line on top just under the
    # PIP, white ticks hang down, labels below the ticks (PIP ruler style: white ticks / numbers, cyan travel bar from
    # 0 to the pointer, cyan pointer needle)
    sc.frame_set(92)
    yb, zb = BAR_C
    org = Vector((x0, yb, zb))
    to_cam = (sc.camera.matrix_world.translation - org).normalized()
    u = Vector((1, 0, 0))
    n = (to_cam - u * to_cam.dot(u)).normalized()
    v = n.cross(u).normalized()
    M = Matrix((u, v, n)).transposed().to_4x4()
    M.translation = org
    coll = sc.collection
    piv = bpy.data.objects.new("WScaleR29", None)
    coll.objects.link(piv)
    piv.matrix_world = M
    cy = _emit("WScaleCyanR29M", (0.1, 0.85, 0.95), 4.0)
    wh = _emit("WScaleWhiteR29M", (0.9, 0.92, 0.95), 1.6)
    dark = _plain("WScalePlateR29M", (0.012, 0.014, 0.018), 0.6)
    lo, hi = -k * 10.0, 0.0
    _quads("WScalePlateR29", [(lo - 0.03, -PL_H, hi + 0.115, 0.010)], dark, piv, coll, dz=-0.002)
    ticks = [(lo - 0.002, -0.002, hi + 0.002, 0.002)]          # base line
    for mm in range(0, 11):
        uu = -k * mm
        major = mm % 5 == 0
        w_ = 0.0028 if major else 0.0018
        ticks.append((uu - w_, -(0.022 if major else 0.012), uu + w_, 0.0))
    _quads("WScaleTickR29", ticks, wh, piv, coll)
    fl = bpy.data.fonts.load(FONT_L, check_existing=True)
    fc = bpy.data.fonts.load(FONT_C, check_existing=True)
    yl = -0.026 - LAB_H * 0.74
    for mm in (0, 5, 10):
        _text(f"WScaleLab{mm}R29", str(mm), fl, LAB_H, (-k * mm, yl), piv, coll, wh)
    _text("WScaleUnitR29", "mm", fl, LAB_H * 0.8, (-k * 7.5, yl), piv, coll, wh)
    _text("WScaleTitleR29", "晶圆台", fc, LAB_H * 0.95, (hi + 0.012, yl), piv, coll, cy, align="LEFT")
    # cyan travel bar 0 -> pointer (keyed per frame from the stage) + pointer needle parented to the stage
    bar = _quads("WScaleTravelR29", [(-1.0, 0.003, 0.0, 0.009)], cy, piv, coll, dz=0.002)
    for f in range(sc.frame_start, sc.frame_end + 1):
        sc.frame_set(f)
        bb = [ptr.matrix_world @ Vector(c) for c in ptr.bound_box]
        bar.scale.x = max(1e-4, -(sum(v_.x for v_ in bb) / 8 - x0))
        bar.keyframe_insert("scale", index=0, frame=f)
    sc.frame_set(fa)
    pu = xs[fa] - x0
    pq = [(pu - 0.0035, -0.030, pu + 0.0035, 0.016), ("tri", (pu, 0.002), (pu - 0.011, 0.018), (pu + 0.011, 0.018))]
    pt = _quads("WScalePtrR29", pq, cy, None, coll, dz=0.004)
    pt.data.transform(M)                             # baked to world at frame fa, then follows the stage
    pt.parent = st
    pt.matrix_parent_inverse = st.matrix_world.inverted()
    # px check (labels vs the PIP ruler labels ~12-13 px cap height)
    from bpy_extras.object_utils import world_to_camera_view as w2c
    rx = (sc.render.resolution_x, sc.render.resolution_y)
    sc.render.resolution_x, sc.render.resolution_y = 960, 540
    for f in (42, 92, 143):
        sc.frame_set(f)
        P = lambda p: w2c(sc, sc.camera, M @ Vector(p))
        a, b = P((0, -0.026 - LAB_H * 0.74, 0)), P((0, -0.026, 0))
        t0, t10 = P((0, 0, 0)), P((-k * 10, 0, 0))
        pc = sum((pt.matrix_world @ Vector(c) for c in pt.bound_box), Vector()) / 8
        q = w2c(sc, sc.camera, pc)
        print(f"[r29k b803] f{f} tick0 ({t0.x * 960:.0f},{(1 - t0.y) * 540:.0f}) tick10 ({t10.x * 960:.0f},"
              f"{(1 - t10.y) * 540:.0f}) label cap {(b.y - a.y) * 540:.1f} px ptr x {q.x * 960:.0f} "
              f"-> {(q.x - t0.x) / (t10.x - t0.x) * 10:.2f} mm", flush=True)
    sc.render.resolution_x, sc.render.resolution_y = rx
    sc.frame_set(f0)
    print(f"[r29k b803] scale k {k * 1000:.1f} mm-world/mm x0 {x0:.3f}", flush=True)


def post(sc, shot, scale_on, grid_on):
    if grid_on:
        grid(sc)
    if scale_on and shot == "B8_03":
        scale(sc)
