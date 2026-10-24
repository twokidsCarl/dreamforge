"""Round 22 (P1) cuth: B5_01 / C_03 (R22_ROOT_CAUSE rows 4 + 5), called from cut_hero_r22.post.

B5_01 (row 4, R21: "场分面镜在 85 % 帧接近 1/4，25 % 和 55 % 帧只有约 1/6…下游去掩模的那一段没画出来"; layered on the
       R21 cut_hero_r21._illum build: FFM x1.75, one FFM -> PFM cone, rotated source module):
  - camera re-keyed: the push-in reaches the field facet mirror by 55 % (>= 1/4 frame) and then drifts slowly
  - third segment: pupil facet mirror -> condenser G1 (converging soft cone, beam_r21 landings on both mirrors, both
    in frame); overlay r2_ov_zz22h names G1 "聚光镜 → 掩模" (a G1 -> mask exit cone crossed the facet mirror on screen)
  (row 5) illuminator bay wall rebuilt with kit_r22 selection "B5_01"
C_03 (row 5): illuminator bay wall rebuilt with kit_r22 selection "C_03" (different kinds + seed).
"""
import math

import bpy
from mathutils import Vector

ON = {"B5_01": True, "C_03": False}   # C_03: wall-only trial read flatter (lighter plates, fainter FFM->PFM cone), IF-axis fix not built -> R21 pixels


def _M():
    import sys
    m = sys.modules.get("r2_cutaway")
    return m._M19[0]


def _keep(ffm_r=0.6):
    import build_cutaway_r2 as B
    return [(B.FFM, ffm_r), (B.PFM, 0.55), (B.G1, 0.4), (B.IF.lerp(B.FFM, 0.5), 0.3), (B.FFM.lerp(B.PFM, 0.5), 0.3),
            (B.PFM.lerp(B.G1, 0.5), 0.3), (B.G1.lerp(B.MASK, 0.4), 0.3)]


def _hull_area(pts):
    pts = sorted(set(pts))
    if len(pts) < 3:
        return 0.0

    def cr(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, up = [], []
    for p in pts:
        while len(lo) >= 2 and cr(lo[-2], lo[-1], p) <= 0:
            lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(up) >= 2 and cr(up[-2], up[-1], p) <= 0:
            up.pop()
        up.append(p)
    h = lo[:-1] + up[:-1]
    return abs(sum(h[i][0] * h[i - 1][1] - h[i - 1][0] * h[i][1] for i in range(len(h)))) / 2


def measure(sc, frames, obname="R8Kit2_facet", extra=()):
    from bpy_extras.object_utils import world_to_camera_view
    ob = bpy.data.objects.get(obname)
    if ob is None:
        return
    fc = sc.frame_current
    for f in frames:
        sc.frame_set(f)
        mw = ob.matrix_world
        vs = ob.data.vertices
        step = max(1, len(vs) // 4000)
        pts = []
        for i in range(0, len(vs), step):
            p = world_to_camera_view(sc, sc.camera, mw @ vs[i].co)
            if p.z > 0:
                pts.append((round(min(1, max(0, p.x)), 4), round(min(1, max(0, p.y)), 4)))
        s = f"[r22h] f{f} hero area {_hull_area(pts):.3f}"
        for nm, pnt in extra:
            q = world_to_camera_view(sc, sc.camera, Vector(pnt))
            s += f" {nm}=({q.x:.2f},{1 - q.y:.2f})"
        print(s)
    sc.frame_set(fc)


def post_b501(sc):
    if not ON["B5_01"]:
        return
    import build_cutaway_r2 as B
    import kit_r2 as K
    import beam_r21 as R21B
    n = sc.frame_end
    # ---- row 4: third segment PFM -> G1 (landing) -> exit toward the mask
    npf = K.mirror_normal(B.FFM, B.PFM, B.G1)
    ng1 = K.mirror_normal(B.PFM, B.G1, B.MASK)
    o1, m1 = R21B.segment(B.PFM, B.G1, 0.17, 0.11, "IllumPfmG1R22", k=1.2, na=npf, nb=ng1, seg=64)
    R21B.key_vis(o1, m1, n, 0.12, None)
    # ---- row 5: own bay wall
    import kit_r22
    kit_r22.rebuild_wall("B5_01", _M(), keep=_keep(0.95))
    # ---- row 4: camera reaches the facet mirror by 55 %
    import cut_hero_r21 as H21
    cam, tgt = H21._cam_tgt(sc)
    cam.animation_data_clear()
    if tgt is not None:
        tgt.animation_data_clear()
    cam.data.lens = 16
    t_end = B.FFM * 0.7 + (B.PFM + B.IF) / 2 * 0.3
    K.key_path(cam, tgt, [(1, (-2.95, -5.7, 3.05), (-3.0, 0.15, 2.9)),
                          (round(n * 0.3), (-2.85, -4.7, 3.25), (-2.95, 0.15, 3.05)),
                          (round(n * 0.55), CAM55[0], tuple(t_end)),
                          (round(n * 0.85), (-2.57, -1.52, 4.12), tuple(t_end)),
                          (n, (-2.56, -1.5, 4.12), tuple(t_end))])
    cam.data.dof.aperture_fstop = 11.0
    measure(sc, (29, 64, 99, n), extra=(("IF", B.IF), ("PFM", B.PFM), ("G1", B.G1)))


CAM55 = [(-2.6, -1.6, 4.1)]


def post_c03(sc):
    if not ON["C_03"]:
        return
    import kit_r22
    kit_r22.rebuild_wall("C_03", _M(), keep=_keep(0.6))
