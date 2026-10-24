"""R27 srcb helper for B2_08 (R27_ROOT_CAUSE row 2b), called from src_r27.post on top of the R23 pixels (src_r23).

mirror=True (MIRROR_R27): the R23 concentric sheen sheet B208SheenR23* (= the 「条纹」 on a grey face) is deleted; the
  collector face gets the B1_15 polished mirror (CollFaceBrightR20 colour, metal 1; rough 0.008 so the reflected room stays crisp through the concave magnification + f/11 DOF - 0.04 smeared it to satin at 32 spp) and a glossy-only
  reflection room around the dish (B208ReflRoomR27: camera / diffuse / shadow invisible) - a smooth bright-to-dark
  vessel interior placed where the face's reflected camera rays go (B208DIAG): a crisp bright/dark horizon, a lit
  wall with a broad lamp where the labelled deposit patch reflects, dim room with a crisp horizon, two sharp-edged softboxes (one behind the labelled deposit patch), three lit flange rings - so
  the face shows a sharp, high-contrast mirror image (a mirror that reflects a dark room reads as matte grey).
spots=True (SPOTS_R27): TinDeposits = dark stains on the face; every stain island gets its own removal time and
  fades away (alpha ramp over 0.12 of the cleaning front, ~25 frames; driver on the frame); the removal front runs over the shot (f60 ~10 % gone, f133 ~40 %, f206 ~75 %).
"""
import math
import os
import random

_E = os.environ


def _op(N, L, o, a, b=None):
    n = N.new("ShaderNodeMath")
    n.operation = o
    for i, v in enumerate((a, b)):
        if v is None:
            continue
        if isinstance(v, (int, float)):
            n.inputs[i].default_value = v
        else:
            L.new(v, n.inputs[i])
    return n.outputs[0]


def _room_mat():
    import bpy
    m = bpy.data.materials.new("B208ReflRoomR27M")
    m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    for n in list(N):
        if n.type != "OUTPUT_MATERIAL":
            N.remove(n)
    out = next(n for n in N if n.type == "OUTPUT_MATERIAL")
    tc = N.new("ShaderNodeTexCoord")
    nz = N.new("ShaderNodeVectorMath")
    nz.operation = "NORMALIZE"
    L.new(tc.outputs["Object"], nz.inputs[0])
    sp = N.new("ShaderNodeSeparateXYZ")
    L.new(nz.outputs[0], sp.inputs[0])
    # what the face reflects (B208DIAG: reflected camera rays hit the room at y +0.3..+0.96, z -0.6..+0.2, x -0.3..+1):
    # a crisp bright/dark horizon at room z ~ -0.19 (dark above) (a sharp reflection edge = polished, not satin), bright lit wall
    # beyond it, a broad lamp where the labelled deposit patch reflects (dark stains on bright metal); no bands
    g = N.new("ShaderNodeMapRange")
    g.interpolation_type = "SMOOTHSTEP"
    L.new(sp.outputs["Z"], g.inputs["Value"])                 # horizon in room z: lit below, dark above
    g.inputs["From Min"].default_value = float(_E.get("S27_HZ0", "-0.24"))
    g.inputs["From Max"].default_value = float(_E.get("S27_HZ1", "-0.14"))
    g.inputs["To Min"].default_value = float(_E.get("S27_RHI", "0.1"))
    g.inputs["To Max"].default_value = float(_E.get("S27_RLO", "0.02"))
    acc = g.outputs["Result"]
    # sharp-edged softboxes (B1_15 reads as a mirror = dark face + crisp bright reflected shapes): one behind the
    # labelled deposit patch (stains read dark on it), one lower right
    for d, w, e in (((0.35, 0.8, -0.47), float(_E.get("S27_SBW", "0.94")), 3.0), ((0.93, 0.3, -0.12), 0.985, 1.6)):
        dv = N.new("ShaderNodeVectorMath")
        dv.operation = "DOT_PRODUCT"
        L.new(nz.outputs[0], dv.inputs[0])
        ln = math.sqrt(sum(c * c for c in d))
        dv.inputs[1].default_value = tuple(c / ln for c in d)
        mr = N.new("ShaderNodeMapRange")
        mr.interpolation_type = "SMOOTHSTEP"
        L.new(dv.outputs["Value"], mr.inputs["Value"])
        mr.inputs["From Min"].default_value = w
        mr.inputs["From Max"].default_value = w + (1.0 - w) * 0.12
        mr.inputs["To Max"].default_value = e * float(_E.get("S27_RLAMP", "1.0"))
        acc = _op(N, L, "ADD", acc, mr.outputs["Result"])
    em = N.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (0.86, 0.9, 1.0, 1)
    L.new(_op(N, L, "MULTIPLY", acc, float(_E.get("S27_RGAIN", "0.2"))), em.inputs["Strength"])   # scene exposure is high
    L.new(em.outputs[0], out.inputs["Surface"])
    return m


def _glossy_only(ob):
    ob.visible_camera = False
    ob.visible_diffuse = False
    ob.visible_shadow = False
    ob.visible_transmission = False
    ob.visible_volume_scatter = False
    ob.visible_glossy = True


def _mirror(sc):
    import bpy
    from mathutils import Vector
    import kit_r2 as K
    for ob in list(bpy.data.objects):
        if ob.name.startswith("B208SheenR23"):
            bpy.data.objects.remove(ob, do_unlink=True)
    mir = bpy.data.objects.get("CollB208_mirror")
    if mir is not None:
        mir.data.materials.clear()
        mir.data.materials.append(K.mat("CollFaceBrightR27", (0.9, 0.91, 0.93), metal=1.0,
                                        rough=float(_E.get("S27_ROUGH", "0.008"))))
    c = Vector(tuple(float(v) for v in _E.get("S27_RC", "-0.3,0,0").split(",")))
    rr = float(_E.get("S27_RR", "1.18"))
    mb = K.MB()
    mb.sphere(tuple(c), rr, 64)
    room = mb.obj("B208ReflRoomR27", _room_mat())
    _glossy_only(room)
    # dark port silhouettes on the room wall (what a real vessel interior shows in a polished dish)
    dk = K.emit_mat("B208ReflPortR27M", (0.8, 0.84, 0.9), float(_E.get("S27_PORTE", "0.2")))   # lit flange rings
    pm = K.MB()
    for d, r in (((0.9, 0.15, -0.35), 0.2), ((0.55, 0.8, 0.1), 0.17), ((0.75, 0.62, -0.55), 0.13)):
        v = Vector(d).normalized()
        p = c + v * (rr - 0.02)
        q = Vector((0, 0, 1)).rotation_difference(-v).to_euler()
        pm.ring(tuple(p), r, r * 0.74, 0.02, rot=q, seg=64)      # flange ring (lit wall seen through it)
        pm.cyl(tuple(p), r * 0.3, 0.02, rot=q, seg=32)            # port bore
    ports = pm.obj("B208ReflPortsR27", dk)
    _glossy_only(ports)


def _spots(sc):
    import bpy
    import bmesh
    import kit_r2 as K
    dep = bpy.data.objects.get("TinDeposits")
    if dep is None:
        print("SRC27 B2_08 no TinDeposits", flush=True)
        return
    me = dep.data
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.verts.ensure_lookup_table()
    isl_of = [0] * len(bm.verts)
    seen, k = set(), 0
    for v in bm.verts:
        if v.index in seen:
            continue
        stack = [v]
        seen.add(v.index)
        while stack:
            w = stack.pop()
            isl_of[w.index] = k
            for e in w.link_edges:
                o = e.other_vert(w)
                if o.index not in seen:
                    seen.add(o.index)
                    stack.append(o)
        k += 1
    bm.free()
    rnd = random.Random(27)
    thr = [rnd.random() for _ in range(k)]
    at = me.attributes.new("gone_t", "FLOAT", "POINT")
    for i in range(len(me.vertices)):
        at.data[i].value = thr[isl_of[i]]
    m = bpy.data.materials.new("TinDepositStainR27M")
    m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    for n in list(N):
        if n.type != "OUTPUT_MATERIAL":
            N.remove(n)
    out = next(n for n in N if n.type == "OUTPUT_MATERIAL")
    bs = N.new("ShaderNodeBsdfPrincipled")
    bs.inputs["Base Color"].default_value = (0.03, 0.03, 0.033, 1)
    bs.inputs["Metallic"].default_value = 0.2
    bs.inputs["Roughness"].default_value = 0.85
    attr = N.new("ShaderNodeAttribute")
    attr.attribute_type = "GEOMETRY"
    attr.attribute_name = "gone_t"
    prog = N.new("ShaderNodeValue")
    prog.name = "CleanProgressR27"
    # alpha = 1 while the island's time is ahead of the cleaning front, ramps to 0 over a 0.12 band
    mr = N.new("ShaderNodeMapRange")
    L.new(_op(N, L, "SUBTRACT", attr.outputs["Fac"], prog.outputs[0]), mr.inputs["Value"])
    mr.inputs["From Min"].default_value = -0.06
    mr.inputs["From Max"].default_value = 0.06
    tr = N.new("ShaderNodeBsdfTransparent")
    mx = N.new("ShaderNodeMixShader")
    L.new(mr.outputs["Result"], mx.inputs["Fac"])
    L.new(tr.outputs[0], mx.inputs[1])
    L.new(bs.outputs[0], mx.inputs[2])
    L.new(mx.outputs[0], out.inputs["Surface"])
    n = sc.frame_end
    f0, f1 = int(_E.get("S27_SPF0", "40")), int(_E.get("S27_SPF1", str(n)))
    send = float(_E.get("S27_SEND", "0.92"))
    # linear cleaning front driven by the frame (simple expression, no keyframe / fcurve API dependence)
    drv = prog.outputs[0].driver_add("default_value").driver
    drv.type = "SCRIPTED"
    drv.expression = f"min(max(-0.06 + (frame - {f0}) * {(send + 0.06) / (f1 - f0):.6f}, -0.06), {send})"
    dep.data.materials.clear()
    dep.data.materials.append(m)
    for f in (60, 133, 206):
        p = -0.06 + (f - f0) / (f1 - f0) * (float(_E.get("S27_SEND", "0.92")) + 0.06)
        print(f"SRC27 B2_08 f{f} islands {k} gone ~{sum(1 for t in thr if t < p) / k:.0%}", flush=True)


def diag(sc):
    """Reflected camera rays of a face grid at the job frames -> hit direction from the room centre (for placing
    the reflected structure)."""
    from mathutils import Vector
    import b115_r17 as B115
    F = B115.B_F
    c = Vector(tuple(float(v) for v in _E.get("S27_RC", "-0.3,0,0").split(",")))
    rr = float(_E.get("S27_RR", "1.18"))
    for f in (60, 133, 206):
        sc.frame_set(f)
        cam = sc.camera.matrix_world.translation.copy()
        print(f"B208DIAG f{f} cam {tuple(round(v, 2) for v in cam)}", flush=True)
        for r in (0.2, 0.35, 0.5, 0.62):
            row = []
            for ad in range(0, 360, 45):
                a = math.radians(ad)
                y, z = r * math.cos(a), r * math.sin(a)
                P = Vector((B115.face_x(r), y, z))
                n = Vector((1, -y / (2 * F), -z / (2 * F))).normalized()
                d = (P - cam).normalized()
                d = d - 2 * d.dot(n) * n
                o = P - c
                b = o.dot(d)
                t = -b + math.sqrt(max(0.0, b * b - (o.length_squared - rr * rr)))
                h = (P + d * t - c).normalized()
                row.append(f"{ad}:{h.x:+.2f},{h.y:+.2f},{h.z:+.2f}")
            print(f"B208DIAG f{f} r{r} " + " ".join(row), flush=True)


def build(sc, S, mirror=True, spots=True):
    if _E.get("S27_DIAG") == "1":
        diag(sc)
    if mirror:
        _mirror(sc)
    if spots:
        _spots(sc)
