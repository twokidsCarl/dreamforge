"""Round 21 (P1, R21_ROOT_CAUSE rows 4 / 6): post-build hook for cut-hero (B3_02 / B5_01), called from r2_cutaway.build after the
R20 build when the shot is in its R21 set. Owned by that sub-agent.

B5_01 (row 4, R20: "场分面镜只占约 5% 画面…两根细光柱，旁边还平行着一根青色箭头…IF 后的光束方向相对 IF 锥轴偏折了约 25°";
       row 6: "整舱被紫色环境光洗过，切面不是中性灰"):
  - field facet mirror assembly scaled 1.75x about its centre + camera pushed in (16 mm) so the facets are >= 1/4 of the last
    frame while IF and the pupil facet mirror stay in frame
  - the 6 R20 beamlets -> ONE outgoing cone field facets -> pupil facets (beam_r21 flat landings)
  - the source module (vessel, IF neck cone, collector) is turned about the IF so the IF cone axis points at the field facet
    mirror: the light leaves the IF along its axis, no turn at the IF
  - violet fill / bounce lights -> neutral (violet only on the beams and their landings)
B3_02 (row 4 / 6): see _collect().
"""
import math

import bpy
from mathutils import Matrix, Vector

SHOTS = {"B5_01"}   # B3_02 code kept for R22, switched off (r2_cutaway.R21_HERO)


def _islands(me):
    par = list(range(len(me.vertices)))

    def f(i):
        while par[i] != i:
            par[i] = par[par[i]]
            i = par[i]
        return i
    for e in me.edges:
        a, b = f(e.vertices[0]), f(e.vertices[1])
        if a != b:
            par[a] = b
    grp = {}
    for i in range(len(me.vertices)):
        grp.setdefault(f(i), []).append(i)
    return list(grp.values())


def _xform_islands(ob, sel, mat):
    """apply world-space matrix `mat` to every vertex island of ob for which sel(world_points) is True"""
    mw = ob.matrix_world
    mwi = mw.inverted()
    me = ob.data
    n = 0
    for isl in _islands(me):
        pts = [mw @ me.vertices[i].co for i in isl]
        if sel(pts):
            for i, p in zip(isl, pts):
                me.vertices[i].co = mwi @ (mat @ p)
            n += 1
    me.update()
    return n


def _cam_tgt(sc):
    cam = sc.camera
    tgt = None
    for c in cam.constraints:
        if getattr(c, "target", None) is not None:
            tgt = c.target
    return cam, tgt


def _illum(sc):
    import build_cutaway_r2 as B
    import kit_r2 as K
    import beam_r21 as R21B
    n = sc.frame_end
    # ---- 1. source module turned about the IF: IF neck axis -> field facet mirror (no turn at the IF)
    ax_old = (B.IF - B.COLL).normalized()
    ax_new = (B.FFM - B.IF).normalized()
    rot = ax_old.rotation_difference(ax_new).to_matrix().to_4x4()
    M_src = Matrix.Translation(B.IF) @ rot @ Matrix.Translation(-B.IF)
    for nm in ("R2_vessel", "IllumSrcCone", "R2_flange", "R2_bolt", "R2_mirror", "R2_substrate", "R2_mount", "R2_anod",
               "PlasmaGlow"):
        ob = bpy.data.objects.get(nm)
        if ob is None:
            continue
        if ob.type != "MESH":
            ob.matrix_world = M_src @ ob.matrix_world
            continue
        k = _xform_islands(ob, lambda pts: sum(p.x for p in pts) / len(pts) < B.IF.x + 0.12 and
                           max(p.x for p in pts) < B.IF.x + 0.3, M_src)
        print("[r21h] source turned:", nm, k)
    # ---- 2. field facet mirror assembly x FFM_S about its centre (facets + their mount islands)
    fo = bpy.data.objects.get("R8Kit2_facet")
    S = FFM_S[0]
    if fo is not None:
        mw = fo.matrix_world
        ps = [mw @ v.co for v in fo.data.vertices]
        lo = Vector([min(p[i] for p in ps) for i in range(3)])
        hi = Vector([max(p[i] for p in ps) for i in range(3)])
        c = (lo + hi) / 2
        M_s = Matrix.Translation(c) @ Matrix.Scale(S, 4) @ Matrix.Translation(-c)
        mg = 0.1

        def inbox(pts):
            return all(lo.x - mg < p.x < hi.x + mg and lo.y - mg < p.y < hi.y + mg and lo.z - mg < p.z < hi.z + mg
                       for p in pts)
        for ob in list(bpy.data.objects):
            if ob.type == "MESH" and ob.name.startswith(("R8Kit2_", "R8Kit1_")):
                k = _xform_islands(ob, inbox, M_s)
                if k:
                    print("[r21h] ffm scaled:", ob.name, k)
    # ---- 3. outgoing: 6 beamlets -> one cone, field facets -> pupil facets
    for ob in list(bpy.data.objects):
        if ob.name.startswith("IllumOutR20"):
            bpy.data.objects.remove(ob)
    nf = K.mirror_normal(B.IF, B.FFM, B.PFM)
    npf = K.mirror_normal(B.FFM, B.PFM, B.G1)
    os_, ms_ = R21B.segment(B.FFM, B.PFM, 0.26, 0.17, "IllumOutR21", k=1.35, na=nf, nb=npf, seg=64)
    R21B.key_vis(os_, ms_, n, 0.1, None)
    # ---- 4. ambient de-violeted: violet only for the beams (+ their landing lights)
    for ob in bpy.data.objects:
        if ob.type != "LIGHT":
            continue
        if ob.name in ("Bounce0", "Bounce1", "IFGlow", "PlasmaGlow", "MaskGlow"):
            ob.data.color = (0.92, 0.93, 0.95)
            ob.data.energy *= 0.5
        elif ob.name in ("FillL", "FillR", "Rim"):
            ob.data.color = (0.93, 0.94, 0.96)
    # ---- 5. camera: R20 wide opening, push-in to the (now large) field facet mirror; IF + pupil mirror stay in frame
    cam, tgt = _cam_tgt(sc)
    cam.animation_data_clear()
    if tgt is not None:
        tgt.animation_data_clear()
    cam.data.lens = 16
    t_end = B.FFM * 0.7 + (B.PFM + B.IF) / 2 * 0.3
    K.key_path(cam, tgt, [(1, (-2.95, -5.7, 3.05), (-3.0, 0.15, 2.9)),
                          (round(n * 0.3), (-2.85, -4.7, 3.25), (-2.95, 0.15, 3.05)),
                          (round(n * 0.85), (-2.6, -1.6, 4.1), tuple(t_end)),
                          (n, (-2.6, -1.55, 4.1), tuple(t_end))])
    cam.data.dof.aperture_fstop = 11.0


def _collect(sc):
    """B3_02 row 4 (R20: "收集镜镜面只占约 6% 画面…外层带辐条的大壳反而更像镜子…镜口约占画面高度的 60%。镜面用高反射金属镀膜，
    带掠射高光，不要做成暗紫色的碟子…外壳内壁换成哑光喷砂"): the collector dish (+ its holder ring) x DISH_S about its vertex,
    the reflected cone rebuilt from the bigger rim onto the same IF; dish = bright high-reflective coating (grazing studio
    highlights from DishGraze*), outer vessel shell = matte blasted grey; camera ends close on the dish with IF in frame."""
    import build_cutaway_r2 as B
    import kit_r2 as K
    import beam_r21 as R21B
    n = sc.frame_end
    S = DISH_S[0]
    c = B.COLL.copy()
    M_s = Matrix.Translation(c) @ Matrix.Scale(S, 4) @ Matrix.Translation(-c)

    def dish(pts):
        cx = sum(p.x for p in pts) / len(pts)
        return all(p.x < -7.3 and math.hypot(p.y, p.z - c.z) < 0.95 for p in pts) and cx < -7.5
    for nm in ("R2_mirror", "R2_substrate", "R2_flange", "R2_bolt", "R2_mount", "R2_anod"):
        ob = bpy.data.objects.get(nm)
        if ob is not None and ob.type == "MESH":
            print("[r21h] dish scaled:", nm, _xform_islands(ob, dish, M_s))
    for ob in list(bpy.data.objects):
        if ob.name.startswith("CollectConeR18"):
            bpy.data.objects.remove(ob)
    Rr, ff = 0.62 * S, 0.42 * S
    cc_ = R21B.cone(Vector((c.x + Rr * Rr / (4 * ff) + 0.01, 0, c.z)), B.IF, 0.58 * S, 0.012, "CollectConeR21", k=0.55,
                    seg=64)
    R21B.key_vis(cc_[0], cc_[1], n, 0.0, 0.62, ramp=12, dim=0.5)
    m = bpy.data.materials.get("CollectorDarkML_R20")
    if m is not None:
        bs = next(nd for nd in m.node_tree.nodes if nd.type == "BSDF_PRINCIPLED")
        bs.inputs["Base Color"].default_value = (0.80, 0.81, 0.84, 1.0)
        bs.inputs["Roughness"].default_value = 0.07
        bs.inputs["Metallic"].default_value = 1.0
    matte = K.mat("VesselMatteR21", (0.13, 0.13, 0.135), metal=0.1, rough=0.8)
    vo = bpy.data.objects.get("R2_vessel")
    if vo is not None:
        vo.data.materials.clear()
        vo.data.materials.append(matte)
    cam, tgt = _cam_tgt(sc)
    cam.animation_data_clear()
    if tgt is not None:
        tgt.animation_data_clear()
    cam.data.lens = 20
    K.key_path(cam, tgt, [(1, (-4.15, -4.35, 3.45), (-6.2, 0.0, 2.42)),
                          (round(n * 0.5), (-5.4, -3.2, 3.0), tuple(c * 0.55 + B.IF * 0.45)),
                          (round(n * 0.85), (-6.3, -2.55, 2.8), tuple(c * 0.5 + B.IF * 0.5)),
                          (n, (-6.33, -2.53, 2.8), tuple(c * 0.5 + B.IF * 0.5))])


DISH_S = [1.8]
FFM_S = [1.75]


def post(sc, variant, shot):
    if shot == "B5_01" and shot in SHOTS:
        _illum(sc)
    elif shot == "B3_02" and shot in SHOTS:
        _collect(sc)
    return sc
