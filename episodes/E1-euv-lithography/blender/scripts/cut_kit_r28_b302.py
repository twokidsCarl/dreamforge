"""R28 kit B3_02 helper (cut_kit_r28.SHROUD_R28 / GRID_R28, R28_ROOT_CAUSE row 5b).

SHROUD_R28: R27 review p2 B3_02 「紫色光锥里面还套着一个实心金属锥罩，两者重叠后整体读成『金属花瓶』…锥罩改成半透明或剖开一半，
让紫色光锥的轮廓单独可读」. The IF-neck shroud (build_cutaway_r2 IF_CUT: cone (-5.85,0,2.38) r 0.42 -> (-4.75,0,2.53)
r 0.14, kept 20..200 deg = the +Y half) projects as a full cone inside the violet one from this 45 deg camera, its
polished inner face = the "vase". Here the shell keeps only the lower-back sector THETA (theta: +Y = 0, +Z = 90,
-Y = 180, -Z = -90 deg about the neck axis), the inner faces of what stays turn dark graphite (a shadowed trough, not a
mirror), and both sawn edges get light section strips (the R14 section language) -> "a cut-open shroud", and the
violet cone's upper silhouette stands alone.
GRID_R28: 「背景是同一种格栅框重复」 -> kit_r27.named_row (one block per kind, proud, visible_glossy off so the dish does not
mirror them) in front of the repeated frame bays behind the IF.
"""
import math

import bpy
import bmesh
from mathutils import Vector

A, B_ = Vector((-5.85, 0, 2.38)), Vector((-4.75, 0, 2.53))
RA, RB, T = 0.42, 0.14, 0.025
THETA = (-70.0, -25.0)   # 8-spp try 2 (-70, 15): the lower half still filled the violet cone as a grey half-cone
INNER = (0.05, 0.05, 0.058)   # 8-spp try 2: rough 0.65 diffuse dark caught the top area light (rendered 140 grey) -> dark metal
GRID = dict(x0=-5.75, x1=-4.45, z0=1.0, z1=3.6, y0=1.1, scale=1.4, depth=0.7)   # in front of the R8Kit3 back-wall bays (y 1.14..1.4)
KINDS = ("turbo_gate", "valve_island", "power_supply", "ion_pump")


def _frame():
    ax = (B_ - A).normalized()
    ey = Vector((0, 1, 0))
    ey = (ey - ax * ey.dot(ax)).normalized()
    ez = ax.cross(ey).normalized()
    if ez.z < 0:
        ez = -ez
    return ax, ey, ez


def _theta(v, ey, ez):
    return math.degrees(math.atan2(v.dot(ez), v.dot(ey)))


def _mat(name, col, rough, metal=0.0):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (*col, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    return m


def shroud(sc):
    ax3 = B_ - A
    L2 = ax3.length_squared
    ax, ey, ez = _frame()
    dark = _mat("NeckInnerR28", INNER, 0.4, 1.0)
    tot_del, tot_dark = 0, 0
    for ob in list(bpy.data.objects):
        if ob.type != "MESH" or not ob.name.startswith("R2_"):
            continue
        mw = ob.matrix_world
        nm = mw.to_3x3()
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        dele, inner = [], []
        for f in bm.faces:
            c = mw @ f.calc_center_median()
            t = (c - A).dot(ax3) / L2
            if not (-0.01 <= t <= 1.01):
                continue
            v = (c - A) - ax3 * t
            rr = v.length
            rc = RA + (RB - RA) * t
            if abs(rr - rc) >= 0.045:
                continue
            th = _theta(v, ey, ez)
            if not (THETA[0] <= th <= THETA[1]):
                dele.append(f)
            elif ob.name != "R2_section":
                inner.append(f)   # both skins of the kept trough: the polished inner face was the "vase"
        if not dele and not inner:
            bm.free()
            continue
        if inner:
            ob.data.materials.append(dark)
            k = len(ob.data.materials) - 1
            for f in inner:
                f.material_index = k
        bmesh.ops.delete(bm, geom=dele, context="FACES")
        bm.to_mesh(ob.data)
        bm.free()
        ob.data.update()
        tot_del += len(dele)
        tot_dark += len(inner)
        print(f"[r28k b302] shroud {ob.name}: deleted {len(dele)} faces, inner dark {len(inner)}", flush=True)
    # light section strips on both sawn edges (R14 section language)
    sec = bpy.data.materials.get("SectionFace") or _mat("NeckSectionR28", (0.8, 0.8, 0.82), 0.5)
    verts, faces = [], []
    n = 8
    for th in THETA:
        r = math.radians(th)
        d = ey * math.cos(r) + ez * math.sin(r)
        p0 = A + d * (RA - T / 2)
        p1 = B_ + d * (RB - T / 2)
        u = (p1 - p0).normalized()
        w1 = d
        w2 = u.cross(d).normalized()
        o = len(verts)
        for p in (p0, p1):
            for j in range(n):
                a = 2 * math.pi * j / n
                verts.append(tuple(p + (w1 * math.cos(a) * 0.016) + (w2 * math.sin(a) * 0.016)))
        for j in range(n):
            faces.append((o + j, o + (j + 1) % n, o + n + (j + 1) % n, o + n + j))
    me = bpy.data.meshes.new("NeckSectionR28")
    me.from_pydata(verts, [], faces)
    me.update()
    so = bpy.data.objects.new("NeckSectionR28", me)
    sc.collection.objects.link(so)
    me.materials.append(sec)
    so.visible_glossy = False
    # the solid R2 "collector -> IF" cone mesh (build_cutaway_r2 K.cone_beam, EUVSoftCone, r 0.62 -> IF) still sits inside
    # the R25/R27 violet shell and renders as a grey metal cone = the main half of the 「金属花瓶」 (ray-cast f67)
    rc_ = bpy.data.objects.get("R2_cone")
    if rc_ is not None:
        rc_.hide_render = True
    print(f"[r28k b302] SHROUD_R28 R2_cone hidden {rc_ is not None}; kept theta {THETA}: deleted {tot_del}, darkened {tot_dark}", flush=True)


def grid(sc):
    import hero_kit_r10 as H
    import kit_r27 as KR
    P = H.new_parts()
    g = GRID
    kinds = KR.named_row(P, g["x0"], g["x1"], g["z0"], g["z1"], g["y0"], kinds=KINDS, seed=328, scale=g["scale"],
                         depth=g["depth"])
    obs = KR.finish(P, "B302KitR28") or []
    for o in obs:
        o.visible_glossy = False
    print(f"[r28k b302] GRID_R28 named_row {KR.count(kinds)} kinds, {len(obs)} objects", flush=True)
    return obs


def _report(sc, obs):
    from bpy_extras.object_utils import world_to_camera_view as w2c
    rx = (sc.render.resolution_x, sc.render.resolution_y)
    sc.render.resolution_x, sc.render.resolution_y = 960, 540
    f0 = sc.frame_current
    for f in (30, 67, 103):
        sc.frame_set(f)
        for o in obs:
            P = [w2c(sc, sc.camera, o.matrix_world @ Vector(c)) for c in o.bound_box]
            xs, ys = [p.x * 960 for p in P], [(1 - p.y) * 540 for p in P]
            bb = [o.matrix_world @ Vector(c) for c in o.bound_box]
            print(f"[r28k b302] f{f} {o.name} px x {min(xs):.0f}..{max(xs):.0f} y {min(ys):.0f}..{max(ys):.0f} "
                  f"ymin {min(v.y for v in bb):.2f}", flush=True)
    sc.frame_set(f0)
    sc.render.resolution_x, sc.render.resolution_y = rx


def post(sc, shroud_on, grid_on):
    if shroud_on:
        shroud(sc)
    if grid_on:
        _report(sc, grid(sc))
