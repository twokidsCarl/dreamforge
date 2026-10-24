"""Round 24 hook (owned by the 'cbeam' sub-agent; shots in r2_cutaway.R24_BEAM = A0_10 / B5_01 / C_03).
R24_ROOT_CAUSE row 3 (light path, shared module beam_r24): R23 review p2 #1 "一屏一条光路，光束锥形收放、软边，每个拐点落在
可见的镜面高光上（A0_10 右段、B5_01 交叉、…、C_03 断路）".

Per shot: delete that screen's old beam objects (R17-R23 volume legs, landing glows, R2_spot, source cones) and build ONE
ordered path with beam_r24.chain (surface soft cones, elliptical landings on the mirror faces; normals = reflection
bisectors), then beam_r24.check on the job frames (legs not yet revealed are left out of that frame's check).
  A0_10: collector -> IF -> FFM -> PFM -> mask -> ONE projection mirror -> wafer (R23 PO zig-zag + G1/G2 zig
         mask -> PO0 -> PO1 -> wafer dropped: right bay = illumination -> mask -> projection -> wafer, no crossing).
  B5_01: pre() moves build_cutaway_r2.PFM straight below the FFM (only in the B5_01 process) so IF -> FFM -> PFM -> G1
         is a Z without the R22/R23 X crossing; path collector -> IF -> FFM -> PFM -> G1 (condenser).
  C_03:  keeps the R23 pre() FFM move (cut_hero_r23 runs first). Path collector -> IF -> FFM -> PFM -> G1 -> G2 -> mask
         -> projection (named exit), grown with key_chain so the 55 % frame shows FFM -> PFM -> up and out.
SHOTS switches each shot (removed -> R23 pixels; r2_cutaway.R24_BEAM does the same).
"""
import bpy
from mathutils import Vector

SHOTS = {"A0_10", "B5_01", "C_03"}
JOB = {"A0_10": (54, 119, 184), "B5_01": (29, 64, 99), "C_03": (101, 222, 343)}
PFM_R23 = Vector((-3.55, 0.25, 2.05))      # build_cutaway_r2.PFM default (R23 B5_01)
PFM_B501 = Vector((-2.05, 0.25, 2.5))      # straight below the FFM (-2.15, 0.15, 3.85), above the subtitle band

PFM_C03 = Vector((-2.45, 0.25, 1.95))     # below-right of the R23 FFM (-2.95, 0, 2.66): FFM -> PFM -> G1 is a V,
                                           # the PFM -> G1 leg no longer runs under the FFM panel at 55 %
OLD_PREFIX = {
    "A0_10": ("A0PathR23_", "A0LandR23_", "BeamSeg", "R2_spot", "TitleCone", "TitleLand"),
    "B5_01": ("Illum", "IFPinchR20", "R2_spot"),
    "C_03": ("TourLeg", "TourSrcCone", "R2_spot"),
}


def pre(variant, shot, mod):
    if shot not in SHOTS:
        return
    if shot == "B5_01":
        import build_cutaway_r2 as B
        B.PFM = PFM_B501.copy()
        print("[r24c] B5_01 PFM ->", tuple(B.PFM))
    if shot == "C_03":                         # R23 FFM move (cut_hero_r23.pre) already applied; PFM below-right of it
        import build_cutaway_r2 as B
        B.PFM = PFM_C03.copy()
        print("[r24c] C_03 PFM ->", tuple(B.PFM), "FFM", tuple(B.FFM))


def _vol_out(ob):
    for s in ob.material_slots:
        m = s.material
        if m and m.use_nodes:
            for n in m.node_tree.nodes:
                if n.type == "OUTPUT_MATERIAL" and n.inputs["Volume"].is_linked:
                    return True
    return False


def _cleanup(shot):
    gone = []
    for ob in list(bpy.data.objects):
        if ob.type not in ("MESH", "CURVE"):
            continue
        if ob.name.startswith(OLD_PREFIX[shot]) or _vol_out(ob):
            gone.append(ob.name)
            bpy.data.objects.remove(ob, do_unlink=True)
    print(f"[r24c] {shot} removed {len(gone)} old beam objects: {sorted(gone)}")


def _bis(a, p, b):
    """mirror normal at p for light a -> p -> b (law of reflection)."""
    return ((a - p).normalized() + (b - p).normalized()).normalized()


def _stops(pts, mirrors, final_n=None):
    out = []
    for i, p in enumerate(pts):
        if i in mirrors:
            out.append((p, _bis(pts[i - 1], p, pts[i + 1])))
        elif i == len(pts) - 1:
            out.append((p, final_n))
        else:
            out.append((p, None))
    return out


def _sub(ch, i0, i1):
    return {"legs": ch["legs"][i0:i1], "spots": ch["spots"][i0:i1 + 1], "stops": ch["stops"][i0:i1 + 1],
            "radii": ch["radii"][i0:i1 + 1]}


def _check(sc, ch, plan, tag):
    """plan = [(frame, first_stop, last_stop, exits_relative)]"""
    import beam_r24 as BM
    bad = []
    for f, i0, i1, ex in plan:
        bad += BM.check(sc, _sub(ch, i0, i1), [f], exits=ex, tag=f"{tag} stops{i0}-{i1}")
    print(f"BEAMCHECK {tag} SUMMARY {'OK' if not bad else 'NOGO ' + str(len(bad))}", flush=True)


def _fade_src(ch, name, fade0=0.5):
    """rebuild leg 0 (collector mouth -> IF) with a soft fade-in from the dish side (no flat 'bucket' end at 25 %)."""
    import beam_r24 as BM
    (a, _), (b, _) = ch["stops"][0], ch["stops"][1]
    for ob in ch["legs"][0]:
        bpy.data.objects.remove(ob, do_unlink=True)
    ch["legs"][0] = BM.soft_cone(name + "Leg0", a, b, ch["radii"][0], ch["radii"][1], None, 4.0, 0.6, fade0=fade0)


def _clip_in_frame(sc, ch, f, i0, i1):
    """sub-chain for frame f whose off-screen END stops are moved along their leg to the frame edge (the 85 % C_03
    camera sits between G2 and the mask, so the far ends project behind the camera plane and the width test degenerates)."""
    import beam_r24 as BM
    sc.frame_set(int(f))
    W, H = sc.render.resolution_x, sc.render.resolution_y
    sub = _sub(ch, i0, i1)
    stops, radii = list(sub["stops"]), list(sub["radii"])

    def inside(p):
        s_, z = BM._proj(sc, sc.camera, p)
        return z > 0 and 0 <= s_.x <= W and 0 <= s_.y <= H
    for end, nb in ((0, 1), (len(stops) - 1, len(stops) - 2)):
        p_out, p_in = stops[end][0], stops[nb][0]
        if inside(p_out) or not inside(p_in):
            continue
        lo, hi = 0.0, 1.0                      # t: 0 = p_in, 1 = p_out
        for _ in range(30):
            m = (lo + hi) / 2
            lo, hi = (m, hi) if inside(p_in.lerp(p_out, m)) else (lo, m)
        rin = radii[nb] if isinstance(radii[nb], (int, float)) else max(radii[nb])
        rout = radii[end] if isinstance(radii[end], (int, float)) else max(radii[end])
        stops[end] = (p_in.lerp(p_out, lo * 0.98), stops[end][1])
        radii[end] = rin + (rout - rin) * lo * 0.98
    return {"legs": sub["legs"], "spots": sub["spots"], "stops": stops, "radii": radii}


def _b501_cam_target(sc):
    """cut_hero_r22_illum aims the 55-100 % camera at FFM*0.7 + (PFM + IF)/2*0.3 - with the moved PFM that target slid
    right and pushed the IF into the corner; re-key the target to the R23 value (R23 PFM) so the R23 camera stays."""
    import build_cutaway_r2 as B
    import cut_hero_r21 as H21
    cam, tgt = H21._cam_tgt(sc)
    if tgt is None:
        print("[r24c] B5_01 no camera target - camera left as built")
        return
    n = sc.frame_end
    t_r23 = B.FFM * 0.7 + (PFM_R23 + B.IF) / 2 * 0.3
    for f in (round(n * 0.55), round(n * 0.85), n):
        tgt.location = t_r23
        tgt.keyframe_insert("location", frame=f)
    print("[r24c] B5_01 camera target re-keyed to the R23 value", tuple(round(x, 3) for x in t_r23), "frames", n)


def post(sc, variant, shot):
    if shot not in SHOTS:
        return sc
    import beam_r24 as BM
    import build_cutaway_r2 as B
    _cleanup(shot)
    coll_dir = (B.IF - B.COLL).normalized()
    src = B.COLL + coll_dir * 0.75          # collector mouth plane (cone from the dish rim to the IF)
    if shot == "A0_10":
        po = B.PO[0]
        # one main path, no zig through G1 / G2 in the wide title shot: collector -> IF -> FFM -> PFM -> mask (top)
        # -> projection mirror -> wafer (bottom)
        pts = [src, B.IF, B.FFM, B.PFM, B.MASK, po, B.WAFER]
        stops = _stops(pts, mirrors=(2, 3, 4, 5), final_n=Vector((0, 0, 1)))
        radii = [0.55, 0.03, 0.2, 0.16, 0.11, 0.16, 0.05]
        ch = BM.chain("A0PathR24", stops, radii, strength=5.0, alpha=0.65, spot_strength=14.0)
        _fade_src(ch, "A0PathR24")
        n = len(pts) - 1
        _check(sc, ch, [(f, 0, n, ()) for f in JOB[shot]], "A0_10")
    elif shot == "B5_01":
        _b501_cam_target(sc)
        # path starts at the IF (the collector -> IF cone sits inside the metal IF neck and stuck out of it at 25 %)
        pts = [B.IF, B.FFM, B.PFM, B.G1]
        stops = _stops(pts, mirrors=(1, 2), final_n=None)
        stops[-1] = (B.G1, _bis(B.PFM, B.G1, B.MASK))
        radii = [0.03, 0.2, 0.17, 0.12]
        ch = BM.chain("IllumPathR24", stops, radii, strength=4.0, alpha=0.6, spot_strength=12.0)
        _check(sc, ch, [(f, 0, 3, ()) for f in JOB[shot]], "B5_01")
    elif shot == "C_03":
        po = B.PO[0]
        pts = [src, B.IF, B.FFM, B.PFM, B.G1, B.G2, B.MASK, po]
        stops = _stops(pts, mirrors=(2, 3, 4, 5, 6), final_n=None)
        radii = [0.55, 0.03, 0.2, 0.16, 0.12, 0.08, 0.06, 0.09]
        ch = BM.chain("TourPathR24", stops, radii, strength=4.5, alpha=0.6, spot_strength=12.0)
        _fade_src(ch, "TourPathR24")
        # growth: source + IF -> FFM lit from the start, FFM -> PFM -> G1 -> G2 -> mask (up, top edge) by the 55 %
        # frame, mask -> projection after it
        BM.key_chain(ch, [1, 1, 150, 165, 180, 195, 260])
        f0, f1, f2 = JOB[shot]
        bad = BM.check(sc, _sub(ch, 0, 2), [f0], exits=(0,), tag="C_03 stops0-2")
        bad += BM.check(sc, _sub(ch, 1, 6), [f1], tag="C_03 stops1-6")
        bad += BM.check(sc, _clip_in_frame(sc, ch, f2, 5, 7), [f2], tag="C_03 stops5-7(clipped to frame)")
        print(f"BEAMCHECK C_03 SUMMARY {'OK' if not bad else 'NOGO ' + str(len(bad))}", flush=True)
    return sc
