"""Round 30 A0_10 whole-machine path (R30_ROOT_CAUSE row 1; MAIN process, wired via r2_cutaway.R30_A010; layered after
a010_r26 / cut_beam_r26 etc. and BEFORE beam_hook_r29, which converts every leg built here to a beam_r29 volume).

R29 p2 (H13, new minimum): 「紫光从 IF 出来以后在照明箱里断了，箱里只有一小段斜光，再出现时已经是掩模下方的一团紫雾。整机光路
没有连成一条…把整条光路连成一根连续的紫色光带：源 → IF → 照明箱里两次反射（场/光瞳分面镜要露出来）→ 掩模 → 投影物镜 →
晶圆。每个拐点都放一块看得见镜座的实心镜，粗细从 IF 处收窄再展开」「投影物镜…开一扇剖视窗，露出 2–3 面镜子」.

R26 put the illuminator into a CLOSED housing (side-on cutaways cannot show two consecutive open turn mirrors facing the
camera, R25) - so the light vanished into the box. R30 keeps the housing but CUTS ITS FRONT WALL AWAY (section trim on
the cut edge) and puts the two reflections inside, on faces turned toward the camera like the R29 B5_01 FFM carrier
(real field facets are individually tilted, the carrier need not lie on the bisector):
  IF -> entry port -> FIELD-FACET plate (parts_r30.facet_plate = the B5_01 model) -> PUPIL-FACET disc
  (parts_r30.pupil_disc = the builder model) -> exit port -> mask (R26 open turn) -> PO barrel: its front cut open by a
  window, inside two PO mirrors on the back wall (the beam zig-zags top -> M1 -> M2 -> nose) -> wafer.
Every leg is one beam_r26 chain leg (converted to a beam_r29 volume by beam_hook_r29; R30 taper / floor by
beam_hook_r30), every landing a spot on the face; all legs every frame at level 1.0. One switch: PATH_R30.
pre(): parks the builder's illuminator mirrors / PO zig-zag behind the back wall (out of sight); post(): opens the
housing + barrel, builds the two facet mirrors, two PO mirrors and the new chains, removes the R26 entry->FFM leg.
"""
import math

import bpy
from mathutils import Vector

PATH_R30 = True

JOB = (54, 119, 184)
FFM_P = Vector((-2.42, 0.42, 3.80))       # field-facet plate landing (upper left of the visible bay between the R27 cabinets)
PFM_P = Vector((-1.62, 0.48, 3.32))       # pupil-facet disc landing (lower right of the visible bay)
HIDE_AT = Vector((-2.5, 1.9, 2.4))        # behind the housing back wall (y1 = 1.0): builder mirrors parked here
FRONT_Y = -0.68                           # housing front wall: faces with every vertex at y < FRONT_Y are cut away
Z_MIN = 1.56


def pre(variant, shot, mod):
    if not PATH_R30:
        return
    import build_cutaway_r2 as B
    B.FFM = HIDE_AT + Vector((0.0, 0.0, 0.6))
    B.PFM = HIDE_AT + Vector((-0.6, 0.0, 0.0))
    B.G1 = HIDE_AT + Vector((0.6, 0.0, 0.0))
    B.G2 = HIDE_AT + Vector((0.6, 0.3, -0.5))
    mod.PO_ZIGZAG = tuple((x, 2.0, z) for (x, _y, z) in mod.PO_ZIGZAG)
    print("[a010r30] builder illuminator mirrors + PO zig-zag parked behind the housing back wall", flush=True)


def _cut_front(names, y_max=FRONT_Y, z_min=Z_MIN, box=None):
    import bmesh
    n_del = 0
    for nm in names:
        ob = bpy.data.objects.get(nm)
        if ob is None or ob.type != "MESH":
            continue
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        mw = ob.matrix_world
        kill = []
        for f in bm.faces:
            ws = [mw @ v.co for v in f.verts]
            if all(w.y < y_max and w.z > z_min for w in ws):
                if box is None or all(box[0] <= w.x <= box[1] and box[2] <= w.z <= box[3] for w in ws):
                    kill.append(f)
        bmesh.ops.delete(bm, geom=kill, context="FACES")
        bm.to_mesh(ob.data)
        bm.free()
        n_del += len(kill)
    return n_del


def _section_trim(M, x0, x1, z0, z1, y, w=0.05):
    """neutral section colour on the cut edge (reads as 「剖开」, not as a missing wall)."""
    import kit_r2 as K
    sec = K.MB()
    for cc, ss in ((((x0 + x1) / 2, y, z1 - w / 2), (x1 - x0, 0.012, w)), (((x0 + x1) / 2, y, z0 + w / 2), (x1 - x0, 0.012, w)),
                   ((x0 + w / 2, y, (z0 + z1) / 2), (w, 0.012, z1 - z0)), ((x1 - w / 2, y, (z0 + z1) / 2), (w, 0.012, z1 - z0))):
        sec.box(cc, ss)
    return sec.obj("A0R30Section", M)


def _shell(name, a, b, r, mat, keep, nseg=28, nrad=64, r2=None):
    """cylinder a -> b of radius r cut into nseg x nrad quads; keep(t, ang_dot_cam) decides which faces stay."""
    import bmesh
    import math
    d = (b - a).normalized()
    side = Vector((1, 0, 0))
    side = (side - d * side.dot(d)).normalized()
    up = d.cross(side).normalized()
    bm = bmesh.new()
    rings = []
    for i in range(nseg + 1):
        c = a.lerp(b, i / nseg)
        rr = r if r2 is None else r + (r2 - r) * i / nseg
        rings.append([bm.verts.new(c + (side * math.cos(2 * math.pi * k / nrad) + up * math.sin(2 * math.pi * k / nrad)) * rr)
                      for k in range(nrad)])
    to_cam = Vector((0, -1, 0))
    for i in range(nseg):
        for k in range(nrad):
            k2 = (k + 1) % nrad
            ang = 2 * math.pi * (k + 0.5) / nrad
            rd = side * math.cos(ang) + up * math.sin(ang)
            if keep((i + 0.5) / nseg, rd.dot(to_cam)):
                bm.faces.new((rings[i][k], rings[i][k2], rings[i + 1][k2], rings[i + 1][k]))
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for p_ in me.polygons:
        p_.use_smooth = True
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    me.materials.append(mat)
    return ob


def _barrel_window(M):
    """the projection barrel gets a front cut-away window between 16 % and 88 % of its length (the long-quad R26 tube
    cannot be cut face by face -> replaced by a segmented shell with the same material); dark lining on the back half;
    the camera-facing halves of the flange rings / bolts inside the window are removed."""
    import bmesh
    import a010_r26 as A
    import kit_r2 as K
    a, b = A.BARREL
    d = (b - a).normalized()
    win = lambda t, dc: not (0.16 <= t <= 0.88 and dc > 0.2)
    old = bpy.data.objects.get("A0R26Barrel")
    mat = old.material_slots[0].material if old is not None and old.material_slots else M
    if old is not None:
        old.hide_render = True
    _shell("A0R30BarrelShell", a, b, A.BARREL_R, mat, win)
    _shell("A0R30BarrelNose", b, b + d * 0.32, A.BARREL_R, mat, lambda t, dc: True, nseg=6, r2=0.17)
    _shell("A0R30BarrelLining", a + d * 0.04, b - d * 0.02, A.BARREL_R - 0.02,
           K.mat("A0R30Lining", (0.03, 0.032, 0.04), metal=0.3, rough=0.55), lambda t, dc: dc < 0.1)
    n_del = 0
    for nm in ("A0R26BarrelFlange", "A0R26BarrelBolts"):
        ob = bpy.data.objects.get(nm)
        if ob is None:
            continue
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        mw = ob.matrix_world
        kill = []
        for f in bm.faces:
            c = mw @ f.calc_center_median()
            t = (c - a).dot(d) / (b - a).length
            rad = (c - a) - d * (c - a).dot(d)
            if 0.16 <= t <= 0.88 and rad.length > 1e-6 and rad.normalized().dot(Vector((0, -1, 0))) > 0.2:
                kill.append(f)
        bmesh.ops.delete(bm, geom=kill, context="FACES")
        bm.to_mesh(ob.data)
        bm.free()
        n_del += len(kill)
    return n_del


def _po_mirror(name, c, n, r=0.15):
    import kit_r2 as K
    q = Vector((0, 0, 1)).rotation_difference(n)
    mir, cell, mt = K.MB(), K.MB(), K.MB()
    from mathutils import Matrix
    R = q.to_matrix().to_4x4()
    mir.cyl_m(Matrix.Translation(c) @ R, r, 0.02, seg=40)
    cell.cyl_m(Matrix.Translation(c - n * 0.035) @ R, r * 1.12, 0.05, seg=40)
    mt.ring(c - n * 0.01, r * 1.18, r * 1.04, 0.04, rot=q.to_euler(), seg=40)
    m_mir = bpy.data.materials.get("EUVMirrorHiR19") or K.mat("R30POCoat", (0.84, 0.84, 0.88), metal=0.9, rough=0.12)
    return [mir.obj(name, m_mir), cell.obj(name + "Cell", K.mat(name + "CellM", (0.2, 0.21, 0.23), metal=0.8, rough=0.35)),
            mt.obj(name + "Mount", K.mat(name + "MountM", (0.62, 0.63, 0.66), metal=1.0, rough=0.2))]


def _anchor_house(point):
    """the 照明系统 leader points at the light landing (R29 p2: 「引线现在指着一个空箱子，要改成指向光落点」)."""
    import json
    import os
    import common as C
    from bpy_extras.object_utils import world_to_camera_view
    out = os.path.join(C.render_root(), "shots", "A0_10", "anchors")

    def h(sc, *_):
        if sc.camera is None:
            return
        fp = os.path.join(out, f"{sc.frame_current:04d}.json")
        try:
            res = json.load(open(fp))
        except Exception:
            res = {}
        v = world_to_camera_view(sc, sc.camera, point)
        res["r26_house"] = [round(v.x, 4), round(1 - v.y, 4), round(v.z, 3)]
        os.makedirs(out, exist_ok=True)
        with open(fp, "w") as fh:
            json.dump(res, fh)
    bpy.app.handlers.frame_change_post.append(h)


def post(sc, variant, shot):
    if not PATH_R30 or shot != "A0_10":
        return sc
    import a010_r26 as A
    import beam_r26 as BR
    import kit_r2 as K
    import parts_r30 as P
    for nm in [o.name for o in bpy.data.objects if o.name.startswith(("A0R26InLeg", "A0R26InSpot"))]:
        bpy.data.objects.remove(bpy.data.objects[nm], do_unlink=True)
    hp = bpy.data.objects.get("A0R26HousePanels")
    if hp is not None:
        hp.hide_render = True
    n_cut = _cut_front(["A0R26Housing", "A0R26HouseDark", "A0R26HouseFlange", "A0R26HouseBolts", "A0R26HouseHose"])
    (x0, x1), (y0, y1), (z0, z1) = A.HOUSE
    sec_m = K.mat("A0R30SectionM", (0.78, 0.79, 0.80), metal=0.0, rough=0.6)
    _section_trim(sec_m, x0, x1, z0, z1, y0 - 0.006)
    n_bar = _barrel_window(sec_m)
    # the two facet mirrors, faces turned toward the camera (mid frame) like the B5_01 carrier
    sc.frame_set(JOB[1])
    cam = sc.camera.matrix_world.translation
    ent, ex = A.ENTRY, A.EXIT
    n_f0 = ((ent - FFM_P).normalized() + (PFM_P - FFM_P).normalized()).normalized()
    n_f = (n_f0 + (cam - FFM_P).normalized() * 0.9).normalized()
    n_p0 = ((FFM_P - PFM_P).normalized() + (ex - PFM_P).normalized()).normalized()
    n_p = (n_p0 + (cam - PFM_P).normalized() * 0.9).normalized()
    P.facet_plate("A0R30Ffm", FFM_P, n_f, 0.62, 0.46)
    P.pupil_disc("A0R30Pfm", PFM_P, n_p, scale=0.48, post=False)
    S = 7.0
    chI = BR.chain("A0R30Ill", [(ent, None), (FFM_P, n_f), (PFM_P, n_p), (ex, None)], [0.075, 0.17, 0.04, 0.11],
                   strength=S, spot_strength=16.0, land_final=False, mirrors=False)
    # PO barrel: the beam enters the top, zig-zags on two mirrors on the barrel's back wall, leaves the nose
    a, b = A.BARREL
    d = (b - a).normalized()
    side = Vector((1, 0, 0))
    side = (side - d * side.dot(d)).normalized()
    back = d.cross(side).normalized()
    if back.y < 0:
        back = -back
    m1 = a.lerp(b, 0.38) - side * 0.16 + back * 0.24
    m2 = a.lerp(b, 0.66) + side * 0.16 + back * 0.24
    nose = b + d * 0.32
    n1 = ((a - m1).normalized() + (m2 - m1).normalized()).normalized()
    n2 = ((m1 - m2).normalized() + (nose - m2).normalized()).normalized()
    _po_mirror("A0R30PoM1", m1, n1)
    _po_mirror("A0R30PoM2", m2, n2)
    chP = BR.chain("A0R30Po", [(a, None), (m1, n1), (m2, n2), (nose, None)], [0.15, 0.09, 0.08, 0.13], strength=S,
                   spot_strength=14.0, land_final=False, mirrors=False)
    _anchor_house(FFM_P)
    bad = []
    for tag, ch in (("A0_10 ill30", chI), ("A0_10 po30", chP)):
        bad += BR.check(sc, ch, JOB, tag=tag) or []
    print(f"[a010r30] cut {n_cut} housing-front faces, {n_bar} barrel-window faces; FFM n.cam "
          f"{n_f.dot((cam - FFM_P).normalized()):.2f} PFM n.cam {n_p.dot((cam - PFM_P).normalized()):.2f}; "
          f"BEAMCHECK26 A0_10 R30 {'OK' if not bad else 'NOGO ' + str(len(bad))}", flush=True)
    sc.frame_set(1)
    return sc
