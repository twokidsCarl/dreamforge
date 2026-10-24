"""Round 32 A0_10 (R32_ROOT_CAUSE row 1; MAIN process, wired via r2_cutaway.R32_A010; layered after a010_r31 and BEFORE
beam_hook_r29, which converts every leg to a beam_r29 volume).

Carl t381 HARD: 「整条光路必须完整可见（IF → 照明箱 → 掩模 → 投影 → 晶圆，不许断段、不许悬空落点）」; R31 p2: 「照明区每个拐点
补一个有厚度的实心镜加镜座…现在像在空中折了两下」「把锚点移到光实际拐弯的那面分面镜上」.
Root cause (r32smoke/sketch32/a010_occ_r31.txt, one camera ray per 10 px along every leg's centre line, 3 frames):
IF -> housing entry 60-80 % behind the IF bellows / housing-wall flanges; PFM -> exit 17-57 % behind the housing's
upper right wall; exit -> mask 11-50 %; PO barrel M2 -> nose 43-60 % behind the barrel flange / nose. On screen the
PFM -> mask leg vanishes behind the white post at the housing's top right and re-appears at the mask = a broken path.
One switch, PATH_R32 (never brighten - move / cut the occluder, ROUND_PIPELINE「R32 起追加」):
  * SLOT: along every leg, on the three job frames, every ~4 px of the projected centre line (and +-0.7 x the leg
    radius across it) a camera ray; every face of a non-path object that is hit IN FRONT of the leg is cut away
    together with the faces around it within SLOT_R (a cut-away slot along the beam). Path parts (mirrors, mask,
    wafer, people, landing spots) are never cut; faces larger than MAX_AREA are reported, not cut;
  * thick turn mirrors with mounts: the FFM plate gets a machined frame (deep) + two thick pedestal posts, the PFM disc
    a deep cell ring + a thick post, the two PO mirrors a deep cell + an arm to the barrel back wall;
  * 照明系统 leader anchor = the FFM plate centre (r26_house).
Remove A0_10 from R32_A010 / PATH_R32 False -> R31 pixels.
"""
import bpy
from mathutils import Matrix, Vector

PATH_R32 = True
JOB = (54, 119, 184)
SLOT_R = 0.08
CUT_LEGS = ("IF>ENTRY", "ENTRY>FFM", "FFM>PFM", "PFM>EXIT", "EXIT>MASK")   # legs whose occluders are cut. The vessel interior
# (src>IF, seen through its open side) and the projection barrel (legs seen through the R30 barrel window; beam into / out of
# the nose funnel) keep their parts: 32 spp with the barrel legs cut = a gutted dark tube without its funnel (投影物镜 lost)
MAX_AREA = 0.35
STEP_PX = 4
KEEP = ("A0R31Ffm", "A0R31Pfm", "A0R30PoM", "A0R32", "Eng", "A0R31Ill", "A0R30Po", "A0R26Src", "A0R26Ill", "A0R26Po",
        "Wafer", "R2_wafer", "Mask", "R2_mask", "Title", "Beam", "R2_vol", "R2_spot")
LOG = {}
# exit port moved down the right wall onto the straight PFM -> mask line (was z 3.95 at the top: the leg climbed behind
# the housing's top-right post and vanished). Set at import, i.e. before a010_r26.pre() derives the mask normal from it;
# a010_r32 is imported only for shots in R32_A010.
EXIT_R32 = Vector((-1.12, 0.47, 3.33))
if PATH_R32:
    import a010_r26 as _A26
    _A26.EXIT = EXIT_R32.copy()


def pre(variant, shot, mod):
    return None


def legs():
    import a010_r26 as A
    import a010_r31 as A31
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
    src = A.COLL + A.AX * 0.75
    return [("src>IF", src, A.IF, 0.10), ("IF>ENTRY", A.IF, A.ENTRY, 0.06), ("ENTRY>FFM", A.ENTRY, A31.FFM_P, 0.10),
            ("FFM>PFM", A31.FFM_P, A31.PFM_P, 0.08), ("PFM>EXIT", A31.PFM_P, A.EXIT, 0.07),
            ("EXIT>MASK", A.EXIT, A.MASK, 0.08), ("MASK>BARREL", A.MASK, a, 0.10), ("BARREL>M1", a, m1, 0.09),
            ("M1>M2", m1, m2, 0.08), ("M2>NOSE", m2, nose, 0.09), ("NOSE>WAFER", nose, A.WAFER, 0.08)], (m1, m2, back)


def _skip(ob):
    return (ob.hide_render or not getattr(ob, "visible_camera", True) or ob.name.startswith(("R29Vol", "B29", "Plasma"))
            or ob.name.endswith("V29") or "r29_beam" in ob.keys())


def _keep(ob, ends, hit):
    if ob.name.startswith(KEEP):
        return True
    return any((hit - e).length < 0.08 for e in ends)


def _cut_slots(sc, L):
    """collect faces hit in front of each leg (3 frames), then delete them + neighbours within SLOT_R."""
    import bmesh
    from bpy_extras.object_utils import world_to_camera_view as w2c
    hits = {}
    import a010_r26 as A
    ends = [p for _, a, b, _ in L for p in (a, b) if (p - A.EXIT).length > 1e-6 and (p - A.ENTRY).length > 1e-6]   # ports are cut through, mirrors / mask / wafer kept
    for f in JOB:
        sc.frame_set(f)
        cam = sc.camera
        dg = bpy.context.evaluated_depsgraph_get()
        o = cam.matrix_world.translation.copy()
        for nm, P0, P1, rad in L:
            if nm not in CUT_LEGS:
                continue
            s0, s1 = w2c(sc, cam, P0), w2c(sc, cam, P1)
            px = (((s0.x - s1.x) * 960) ** 2 + ((s0.y - s1.y) * 540) ** 2) ** 0.5
            n = max(3, int(px / STEP_PX) + 1)
            ax = (P1 - P0).normalized()
            for i in range(n + 1):
                C = P0.lerp(P1, i / n)
                vd = (C - o).normalized()
                perp = ax.cross(vd).normalized()
                for off in (-0.7, 0.0, 0.7):
                    P = C + perp * rad * off
                    d = P - o
                    dist = d.length
                    d.normalize()
                    org = o.copy()
                    for _k in range(10):
                        ok, loc, nrm, idx, ob, mx = sc.ray_cast(dg, org, d)
                        if not ok or (loc - o).length >= dist - 0.03:
                            break
                        if _skip(ob):
                            org = loc + d * 1e-3
                            continue
                        if _keep(ob, ends, loc):
                            break
                        hits.setdefault(ob.name, []).append((loc.copy(), nm))
                        org = loc + d * 1e-3       # cut every occluding layer in front of the leg
    n_cut, big, who = 0, 0, {}
    for name, pts in hits.items():
        ob = bpy.data.objects.get(name)
        if ob is None or ob.type != "MESH":
            who[name] = "skip"
            continue
        if ob.modifiers:                                 # bake the modifier stack (bevel) so faces can be cut
            ev = ob.evaluated_get(bpy.context.evaluated_depsgraph_get())
            me = bpy.data.meshes.new_from_object(ev)
            ob.modifiers.clear()
            ob.data = me
        if ob.data.users > 1:
            ob.data = ob.data.copy()
        mw = ob.matrix_world
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        from mathutils.kdtree import KDTree
        kd = KDTree(len(pts))
        for i, (p, _) in enumerate(pts):
            kd.insert(p, i)
        kd.balance()
        dead = []
        for fa in bm.faces:
            c = mw @ fa.calc_center_median()
            if kd.find(c)[2] > SLOT_R:
                continue
            area = fa.calc_area() * (mw.to_scale().x * mw.to_scale().y)
            if area > MAX_AREA:
                big += 1
                continue
            dead.append(fa)
        if dead:
            bmesh.ops.delete(bm, geom=dead, context="FACES")
            bm.to_mesh(ob.data)
            ob.data.update()
            n_cut += len(dead)
            who[name] = len(dead)
        bm.free()
    LOG["who"] = who
    return n_cut, big


def _mat(name, col, metal=0.9, rough=0.3):
    import kit_r2 as K
    return K.mat(name, col, metal=metal, rough=rough)


def _thick_mirrors(m1, m2, back):
    """deep frames / cells + pedestal posts / arms on all four turn mirrors."""
    import a010_r31 as A31
    import kit_r2 as K
    sc = bpy.context.scene
    sc.frame_set(JOB[1])
    cam = sc.camera.matrix_world.translation
    import a010_r26 as A
    ent, ex = A.ENTRY, A.EXIT
    FFM_P, PFM_P = A31.FFM_P, A31.PFM_P
    n_f0 = ((ent - FFM_P).normalized() + (PFM_P - FFM_P).normalized()).normalized()
    n_f = (n_f0 + (cam - FFM_P).normalized() * 0.9).normalized()
    n_p0 = ((FFM_P - PFM_P).normalized() + (ex - PFM_P).normalized()).normalized()
    n_p = (n_p0 + (cam - PFM_P).normalized() * 0.9).normalized()
    W, H = A31.FFM_WH
    u = Vector((0, 0, 1)).cross(n_f).normalized()
    v = n_f.cross(u).normalized()
    rot = Matrix((u, v, n_f)).transposed().to_euler()
    fr, mt = K.MB(), K.MB()
    dep, bw = 0.16, 0.055
    c0 = FFM_P - n_f * (0.06 + dep / 2)
    for s_ in (-1, 1):                                  # machined frame: 4 deep bars around the plate
        fr.box(tuple(c0 + u * s_ * (W * 0.53 + bw / 2)), (bw, H * 1.08 + 2 * bw, dep), rot=rot)
        fr.box(tuple(c0 + v * s_ * (H * 0.54 + bw / 2)), (W * 1.06, bw, dep), rot=rot)
    fr.box(tuple(FFM_P - n_f * (0.06 + dep + 0.02)), (W * 1.06, H * 1.08, 0.04), rot=rot)   # back plate
    foot = FFM_P - v * (H * 0.54 + bw) - n_f * 0.10
    for s_ in (-0.32, 0.32):                            # two thick pedestal posts under the frame
        top = foot + u * s_ * W
        mt.tube(top, top + Vector((0, 0, -0.55)), 0.045)
        mt.box(tuple(top + Vector((0, 0, -0.57))), (0.16, 0.16, 0.04))
    mt.box(tuple(foot + Vector((0, 0, -0.30))), (W * 0.75, 0.06, 0.06), rot=(0, 0, u.to_track_quat("X", "Z").to_euler().z))
    # PFM: deep cell ring + thick post
    import a010_r31 as A31b
    s = A31b.PFM_SCALE
    q = Vector((0, 0, 1)).rotation_difference(n_p)
    cell = K.MB()
    cell.ring(PFM_P - n_p * 0.09 * s, 0.52 * s, 0.44 * s, 0.20 * s, rot=q.to_euler())
    cell.cyl_m(Matrix.Translation(PFM_P - n_p * 0.17 * s) @ q.to_matrix().to_4x4(), 0.50 * s, 0.08 * s, seg=48)
    mt.tube(PFM_P - n_p * 0.2 * s, PFM_P - n_p * 0.2 * s + Vector((0, 0, -0.62)), 0.05)
    mt.box(tuple(PFM_P - n_p * 0.2 * s + Vector((0, 0, -0.64))), (0.18, 0.18, 0.04))
    # PO mirrors: deep cells + arms to the barrel back wall
    a, b = A.BARREL
    for c in (m1, m2):
        nn = ((a - c).normalized() + (b - c).normalized()).normalized()
        qq = Vector((0, 0, 1)).rotation_difference(nn)
        cell.cyl_m(Matrix.Translation(c - nn * 0.09) @ qq.to_matrix().to_4x4(), 0.17, 0.12, seg=40)
        mt.tube(c - nn * 0.14, c - nn * 0.14 + back * 0.22, 0.03)
    obs = [fr.obj("A0R32FfmFrame", _mat("A0R32FrameM", (0.55, 0.56, 0.60), 1.0, 0.22), bevel=0.006),
           cell.obj("A0R32Cells", _mat("A0R32CellM", (0.16, 0.17, 0.19), 0.8, 0.35)),
           mt.obj("A0R32Mounts", _mat("A0R32MountM", (0.50, 0.51, 0.55), 1.0, 0.25))]
    return obs, FFM_P


def _anchor_house(point):
    import json
    import os
    import common as C
    from bpy_extras.object_utils import world_to_camera_view
    out = os.path.join(C.render_root(), "shots", "A0_10", "anchors")

    def h32(sc, *_):
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
    bpy.app.handlers.frame_change_post.append(h32)     # after a010_r31's handler -> overwrites r26_house


def post(sc, variant, shot):
    if not PATH_R32 or shot != "A0_10":
        return sc
    L, (m1, m2, back) = legs()
    obs, ffm = _thick_mirrors(m1, m2, back)
    n_cut, big = _cut_slots(sc, L)
    pg = bpy.data.objects.get("A0R26PortGlow")      # glowing port discs: with the wall cut around the exit port the
    if pg is not None:                              # disc sat on the leg as a lit ball (R30 「悬空发光球点」 read)
        pg.hide_render = True
    _anchor_house(ffm)
    print(f"[a010r32] slots cut {n_cut} faces (big faces left {big}) {LOG.get('who')}; thick mirrors {len(obs)} objs",
          flush=True)
    sc.frame_set(1)
    return sc
