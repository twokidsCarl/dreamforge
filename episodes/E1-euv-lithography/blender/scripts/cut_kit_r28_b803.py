"""R28 kit B8_03 / B8_03M helper (cut_kit_r28.SCALE_R28, R28_ROOT_CAUSE row 5b).

R27 review p2 B8_03: 「晶圆本体本身在三帧里几乎看不出位移…晶圆台加一根同比例的小标尺（0–10 mm），或者给晶圆边缘一个参照刻线，
让 −2.5 → −8.5 的反向位移看得见」.
The stage pointer PtrW (parented to WStage) moves 0.02 m per mm (measured here from its world x at the job frames against
the read-outs -2.5 / -8.5 mm). A FIXED tick bar (not parented) is placed just above the pointer tip behind the wafer's
back edge: 0 mm where the pointer would sit at 0, ticks every 1 mm to -10 mm (major 0 / -5 / -10). A cyan reference
line on the wafer's back edge (parented to WStage, same x as the pointer) ties the mark to the wafer itself.
No text (ticks only), no textures.
"""
import bpy
from mathutils import Vector

FR = {42: -2.5, 143: -8.5}
BAR_Y, BAR_Z = (-0.27, -0.20), (0.672, 0.680)   # flat scale just behind the pointer tip (8-spp try 1: a 25 mm tall bar
# with ticks on its front + top read as a white comb / heat sink from this high camera)
TICK_W, TICK_WM = 0.0065, 0.0095


def _mat(name, col, rough=0.5, emit=0.0, metal=0.0):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (*col, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if emit:
        b.inputs["Emission Color"].default_value = (*col, 1)
        b.inputs["Emission Strength"].default_value = emit
    return m


def _boxes(name, boxes, mat, sc):
    verts, faces = [], []
    for (c, s) in boxes:
        o = len(verts)
        for dx in (-1, 1):
            for dy in (-1, 1):
                for dz in (-1, 1):
                    verts.append((c[0] + dx * s[0] / 2, c[1] + dy * s[1] / 2, c[2] + dz * s[2] / 2))
        for f in ((0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)):
            faces.append(tuple(o + i for i in f))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    ob = bpy.data.objects.new(name, me)
    sc.collection.objects.link(ob)
    me.materials.append(mat)
    return ob


def post(sc, shot, on):
    if not on:
        return
    ptr = bpy.data.objects.get("PtrW")
    st = bpy.data.objects.get("WStage")
    if ptr is None or st is None:
        print("[r28k b803] PtrW / WStage missing - no scale", flush=True)
        return
    f0 = sc.frame_current
    xs = {}
    for f in FR:
        sc.frame_set(f)
        bb = [ptr.matrix_world @ Vector(c) for c in ptr.bound_box]
        xs[f] = sum(v.x for v in bb) / 8
    (fa, da), (fb, db) = sorted(FR.items())
    k = (xs[fb] - xs[fa]) / (db - da)          # world m per mm
    x0 = xs[fa] - k * da                        # pointer x at 0 mm
    sc.frame_set(fa)
    bb = [ptr.matrix_world @ Vector(c) for c in ptr.bound_box]
    py = sum(v.y for v in bb) / 8
    print(f"[r28k b803] PtrW x {xs} -> {k * 1000:.1f} mm world per mm, 0 mm at x {x0:.3f}, ptr y {py:.3f}", flush=True)
    yb, zb = BAR_Y, BAR_Z
    xa, xb = x0 + k * 1.0, x0 + k * -11.0
    bar = [(((xa + xb) / 2, (yb[0] + yb[1]) / 2, (zb[0] + zb[1]) / 2), (abs(xb - xa), yb[1] - yb[0], zb[1] - zb[0]))]
    ticks = []
    for mm in range(0, 11):
        x = x0 + k * (-mm)
        major = mm % 5 == 0
        w = TICK_WM if major else TICK_W
        ln = (yb[1] - yb[0]) * (0.9 if major else 0.45)
        ticks.append(((x, yb[0] + ln / 2, zb[1] + 0.001), (w, ln, 0.002)))   # light line on the top face from the front edge
    _boxes("WScaleBarR28", bar, _mat("WScaleBarR28M", (0.05, 0.055, 0.06), 0.4, metal=1.0), sc)
    _boxes("WScaleTickR28", ticks, _mat("WScaleTickR28M", (0.85, 0.86, 0.88), 0.4), sc)
    # wafer-edge reference line (moves with the stage): radial cyan strip on the wafer surface at the pointer x
    w = bpy.data.objects.get("WStage_wafer")
    zt = 0.712
    if w is not None:
        zt = max((w.matrix_world @ Vector(c)).z for c in w.bound_box) + 0.0015
    ym = py - 0.06
    cy = bpy.data.materials.get("PtrCyan") or _mat("WRefCyanR28M", (0.1, 0.85, 0.95), 0.4, 2.0)
    ref = _boxes("WaferRefLineR28", [((xs[fa], ym - 0.03, zt), (0.006, 0.09, 0.002))], cy, sc)
    ref.parent = st
    ref.matrix_parent_inverse = st.matrix_world.inverted()
    for o in (ref,):
        o.visible_shadow = False
    print(f"[r28k b803] {shot} scale bar x {xa:.3f}..{xb:.3f} y {yb} z {zb}; wafer ref line z {zt:.3f}", flush=True)
    # screen check: pointer vs fixed 0-tick, px at the job frames
    if shot == "B8_03":
        from bpy_extras.object_utils import world_to_camera_view as w2c
        rx = (sc.render.resolution_x, sc.render.resolution_y)
        sc.render.resolution_x, sc.render.resolution_y = 960, 540
        for f in (42, 92, 143):
            sc.frame_set(f)
            bb = [ptr.matrix_world @ Vector(c) for c in ptr.bound_box]
            pc = sum(bb, Vector()) / 8
            q = w2c(sc, sc.camera, pc)
            t0 = w2c(sc, sc.camera, Vector((x0, yb[0], zb[1])))
            t10 = w2c(sc, sc.camera, Vector((x0 - k * 10, yb[0], zb[1])))
            print(f"[r28k b803] f{f} ptr px ({q.x * 960:.0f},{(1 - q.y) * 540:.0f}) tick0 ({t0.x * 960:.0f},"
                  f"{(1 - t0.y) * 540:.0f}) tick10 ({t10.x * 960:.0f},{(1 - t10.y) * 540:.0f}) "
                  f"ptr-tick0 {(q.x - t0.x) * 960:.0f} px", flush=True)
        sc.render.resolution_x, sc.render.resolution_y = rx
    sc.frame_set(f0)
