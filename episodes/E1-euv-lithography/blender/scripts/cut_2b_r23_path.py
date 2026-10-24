"""R23 row 3 (A0_10 light path): R22 review 「几段分离的淡色光带…像在空中断开又出现」「镜面落点不清」; R22 cutb
「path still breaks mid-bay」.  One continuous cone chain on the module's own mounted mirrors:
collector -> IF (R21 source cone kept) -> FFM -> PFM -> G1 -> G2 -> mask -> PO1 -> PO2 -> wafer, every turn a lit
landing spot on its mirror, segments revealed one after another (all on by the 55 % frame, path reaches the
FFM / PFM by the 25 % frame). The bay plates the ray-cast finds between the camera and the chain (job frames) are
taken out of camera rays (= a window), listed in the log.
"""
import bpy
from mathutils import Vector

OPEN = []          # filled by post(): names of plates opened (camera-invisible)


def _chain():
    import build_cutaway_r2 as B
    pts = [B.IF, B.FFM, B.PFM, B.G1, B.G2, B.MASK, B.PO[0], B.PO[1], B.WAFER]
    ap = [0.03, 0.24, 0.2, 0.14, 0.1, 0.07, B.PO_R[0] * 0.6, B.PO_R[1] * 0.6, 0.02]
    return [Vector(p) for p in pts], ap


def _is_beam(o):
    return o.name.startswith(("TitleCone", "TitleLand", "BeamSeg", "A0PathR23", "A0LandR23", "Cone", "Land", "Spot"))


def open_occluders(sc, pts, frames=(54, 119, 184)):
    import kit_r2 as K
    dg = bpy.context.evaluated_depsgraph_get()
    hits = {}
    cam = sc.camera
    for f in frames:
        sc.frame_set(f)
        dg = bpy.context.evaluated_depsgraph_get()
        co = cam.matrix_world.translation.copy()
        for a, b in zip(pts, pts[1:]):
            for i in range(1, 12):
                p = a.lerp(b, i / 12)
                d = p - co
                L = d.length
                ok, loc, nrm, idx, ob, mw = sc.ray_cast(dg, co, d.normalized(), distance=L - 0.15)
                guard = 0
                while ok and guard < 6:
                    guard += 1
                    o = bpy.data.objects.get(ob.name) if ob else None
                    if o is None or _is_beam(o):
                        break
                    hits[o.name] = hits.get(o.name, 0) + 1
                    break
    return hits


def post(sc):
    import kit_r2 as K
    import beam_r19 as R18          # aliased (beam_r21) for A0_10
    import beam_r17 as R17
    n = sc.frame_end
    for o in [o for o in bpy.data.objects if o.name.startswith(("TitleCone", "TitleLand", "BeamSeg1", "BeamSeg2"))]:
        bpy.data.objects.remove(o)
    pts, ap = _chain()
    nseg = len(pts) - 1
    for j, (a, b) in enumerate(zip(pts, pts[1:])):
        na = K.mirror_normal(pts[j - 1], a, b) if j > 0 else None
        nb = K.mirror_normal(a, b, pts[j + 2]) if j + 2 < len(pts) else None
        t0 = 0.10 + j * 0.055
        os_, ms_ = R18.cone(a, b, ap[j], ap[j + 1], f"A0PathR23_{j}", k=1.8, na=na, nb=nb)
        R18.key_vis(os_, ms_, n, t0, None, ramp=8)
        if 0 < j + 1 < len(pts) - 1:
            c = pts[j + 1]
            nrm = K.mirror_normal(a, c, pts[j + 2])
            R18._land_timed(c, nrm, f"A0LandR23_{j}", max(2, round(1 + (n - 1) * t0) + 6), 6, scale=1.3)
    R18._land_timed(pts[-1], Vector((0, 0, 1)), "A0LandR23_w", max(2, round(1 + (n - 1) * (0.10 + (nseg - 1) * 0.055)) + 6), 6, scale=1.0)
    try:
        R18.take()
    except Exception:
        pass
    hits = open_occluders(sc, pts)
    print("[cut_2b_r23_path] occluders", sorted(hits.items(), key=lambda kv: -kv[1])[:25])
    for nm, c in hits.items():
        o = bpy.data.objects.get(nm)
        if o is None or c < 2:
            continue
        low = nm.lower()
        if any(k in low for k in ("wall", "grate", "panel", "plate", "sec", "rib", "box", "frame", "skin", "housing", "greeble", "kit")):
            try:
                o.visible_camera = False
                OPEN.append(nm)
            except AttributeError:
                pass
    print("[cut_2b_r23_path] opened", OPEN)
    sc.frame_set(1)
