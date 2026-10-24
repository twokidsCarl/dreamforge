"""R26 chero B3_02 (R26_ROOT_CAUSE row 5 + row 2). Runs after the R25 hook (cut_hero_r24_b302 dish + camera, R25 laser /
no-glossy pass).

R25 review D 84 「三帧运动偏小…加一个慢推」 + R26 table row 5 「推近到碗占 ≥1/3 画宽、锥从碗口 0.15 m 起」:
  * camera: same R24 sketch direction (az 45 deg, el 0.1, 50 mm - not the R23 az 35), re-keyed as a stronger push-in;
    distance pair + target fraction chosen by projecting the rim ellipse / IF at the job frames: dish >= 1/3 of the
    frame width, rim area f103 / f30 >= 1.15 (aim higher), whole rim and IF stay in frame;
  * cone: the R25 beam_r25 rim -> IF shell is replaced by ONE beam_r26 soft shell starting 0.15 m in front of the rim
    plane (never across the dish face), visible_glossy off (the dish face does not mirror the cone, 不许回退).
Laser through the back centre hole, plasma, dish material untouched.
"""
import math

import bpy
from mathutils import Vector

FR = (30, 67, 103)
# main-process 32-spp Q4 (R26): the low-alpha soft cone fades in mid-dish (its wide end reads far smaller than the rim, with a
# hard cut) and the ghosted IF neck reads as a glass funnel full of fog -> R25 rim -> IF cone + solid neck kept; camera push only
CONE_R26 = False
CONE_OFF = 0.15
NECK_ALPHA = 0.2
CONE_STR, CONE_ALPHA, CONE_CORE = 0.7, 0.25, 0.15   # 8-spp try 1 (1.6 / 0.45 / 0.28) and try 2 (0.8 / 0.3 / 0.28) misted the dish face violet (the mouth sits in front of it)


def _rim_proj(sc, cam, H24):
    from bpy_extras.object_utils import world_to_camera_view as w2c
    P = []
    for k in range(64):
        q = w2c(sc, cam, H24._pt(H24.R_RIM, 2 * math.pi * k / 64))
        P.append((q.x, 1 - q.y))
    ar = 0.0
    for i in range(64):
        x1, y1 = P[i]
        x2, y2 = P[(i + 1) % 64]
        ar += x1 * y2 - x2 * y1
    xs, ys = [p[0] for p in P], [p[1] for p in P]
    return abs(ar) / 2, min(xs), max(xs), min(ys), max(ys)


def _key(sc, cam, tgt, RC, IF, dv, d0, d1, tt):
    import kit_r2 as K
    cam.animation_data_clear()
    tgt.animation_data_clear()
    n = sc.frame_end
    T = RC.lerp(IF, tt)
    K.key_path(cam, tgt, [(1, tuple(RC + dv * d0), tuple(T)),
                          (round(n * 0.85), tuple(RC + dv * d1), tuple(T)),
                          (n, tuple(RC + dv * (d1 - 0.03)), tuple(T))])


def _measure(sc, cam, IF, PL, H24):
    from bpy_extras.object_utils import world_to_camera_view as w2c
    res = []
    for f in FR:
        sc.frame_set(f)
        ar, x0, x1, y0, y1 = _rim_proj(sc, cam, H24)
        qi, qp = w2c(sc, cam, IF), w2c(sc, cam, PL)
        res.append(dict(f=f, ar=ar, x0=x0, x1=x1, y0=y0, y1=y1, ifx=qi.x, ify=1 - qi.y, plx=qp.x, ply=1 - qp.y))
    return res


def camera(sc, RC, IF, PL, H24):
    from cut_hero_r21 import _cam_tgt
    cam, tgt = _cam_tgt(sc)
    th = math.radians(H24.AZ)
    dv = Vector((math.cos(th), -math.sin(th), H24.EL)).normalized()
    rx = (sc.render.resolution_x, sc.render.resolution_y)
    sc.render.resolution_x, sc.render.resolution_y = 960, 540
    best = None
    for tt in (0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6):
        for d0 in (7.2, 7.6, 8.0):
            for d1 in (5.6, 5.9, 6.2, 6.4, 6.6):
                _key(sc, cam, tgt, RC, IF, dv, d0, d1, tt)
                m = _measure(sc, cam, IF, PL, H24)
                ok = all(r["x0"] >= -0.12 and r["y0"] >= -0.06 and r["y1"] <= 1.06 and r["ifx"] <= 0.94
                         and min(r["x1"], 1.0) - max(r["x0"], 0.0) >= 0.36 for r in m)
                g = m[-1]["ar"] / m[0]["ar"]
                print(f"[r26h cand] tt {tt} d {d0}->{d1} g {g:.2f} x0 {min(r['x0'] for r in m):.2f} "
                      f"w {min(min(r['x1'], 1) - max(r['x0'], 0) for r in m):.2f} ifx {max(r['ifx'] for r in m):.2f} "
                      f"y {min(r['y0'] for r in m):.2f}..{max(r['y1'] for r in m):.2f} {'OK' if ok else '-'}", flush=True)
                # least-cropped dish among pushes with >= 25 % rim-area growth (row 5 asks >= 15 %)
                key = min(r["x0"] for r in m) - max(0.0, max(r["y1"] for r in m) - 1.0)
                if ok and g >= 1.25 and (best is None or key > best[5]):
                    best = (g, tt, d0, d1, m, key)
    if best is None:
        raise RuntimeError("[r26h b302] no camera satisfies the constraints")
    g, tt, d0, d1, m, _k = best
    _key(sc, cam, tgt, RC, IF, dv, d0, d1, tt)
    fo = bpy.data.objects.new("B302FocusR26", None)
    sc.collection.objects.link(fo)
    fo.location = PL.lerp(RC, 0.5)
    cam.data.dof.focus_object = fo
    for r in m:
        print(f"[r26h] B3_02 f{r['f']} rim area {r['ar']:.3f} width {r['x1'] - r['x0']:.3f} x {r['x0'] * 960:.0f}.."
              f"{r['x1'] * 960:.0f} y {r['y0'] * 540:.0f}..{r['y1'] * 540:.0f} IF ({r['ifx'] * 960:.0f},{r['ify'] * 540:.0f})"
              f" PL ({r['plx'] * 960:.0f},{r['ply'] * 540:.0f})", flush=True)
    print(f"[r26h] B3_02 camera tt {tt} d {d0} -> {d1}  rim area growth f30->f103 {100 * (g - 1):.1f} %", flush=True)
    sc.render.resolution_x, sc.render.resolution_y = rx
    return cam


def ghost_neck():
    """R25 review B3_02 #1 「光锥里叠着一个灰色实心金属锥…降低它的不透明度，让紫光锥成为唯一的会聚形状」 (row 2 read of the
    cone): the faces of the IF-neck cone shell (build_cutaway_r2: (-5.85,0,2.38) -> (-4.75,0,2.53), r 0.42 -> 0.14, in
    the merged vessel / section meshes) get a faint see-through metal slot (alpha NECK_ALPHA); bellows / valve unchanged."""
    a, b = Vector((-5.85, 0, 2.38)), Vector((-4.75, 0, 2.53))
    ax = b - a
    L2 = ax.length_squared
    gm = bpy.data.materials.new("IFNeckGhostR26")
    gm.use_nodes = True
    bs = next(n for n in gm.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    bs.inputs["Base Color"].default_value = (0.55, 0.56, 0.6, 1)
    bs.inputs["Metallic"].default_value = 1.0
    bs.inputs["Roughness"].default_value = 0.3
    bs.inputs["Alpha"].default_value = NECK_ALPHA
    n_tot = 0
    for ob in bpy.data.objects:
        if ob.type != "MESH" or not ob.name.startswith("R2_"):
            continue
        mw = ob.matrix_world
        hit = []
        for p in ob.data.polygons:
            c = mw @ p.center
            t = (c - a).dot(ax) / L2
            if not (0.0 <= t <= 1.0):
                continue
            rr = ((c - a) - ax * t).length
            rc = 0.42 + (0.14 - 0.42) * t
            if abs(rr - rc) < 0.045:
                hit.append(p)
        if not hit:
            continue
        ob.data.materials.append(gm)
        k = len(ob.data.materials) - 1
        for p in hit:
            p.material_index = k
        n_tot += len(hit)
        print(f"[r26h b302] IF neck ghost: {ob.name} {len(hit)} faces", flush=True)
    return n_tot


def post(sc):
    import beam_r26 as BR
    import build_cutaway_r2 as B
    import cut_hero_r24_b302 as H24
    c0, ax, a, b, e1, e2 = H24._ell()
    PL, IF = Vector(B.PLASMA), Vector(B.IF)
    RC = H24.rim_centre()
    f0 = sc.frame_current
    # ---- cone: R25 shell out, one beam_r26 soft shell from 0.15 m in front of the rim plane
    if not CONE_R26:
        camera(sc, RC, IF, PL, H24)
        sc.frame_set(f0)
        print("[r26h b302] CONE_R26 off: R25 cone + neck kept, camera push only", flush=True)
        return
    ra = 1.15
    old = bpy.data.objects.get("CollectBeamR24Leg0")
    if old is not None:
        ra = old.get("r25_radii", (1.15, 0.02))[0]
    for ob in list(bpy.data.objects):
        if ob.name.startswith("CollectBeamR24"):
            bpy.data.objects.remove(ob)
    A = RC + ax * CONE_OFF
    # radius at the new start: the rim -> IF cone shrinks linearly along the axis
    L0 = (IF - (RC + ax * 0.02)).length
    r0 = ra * (IF - A).length / L0
    legs = BR.soft_cone("CollectBeamR26Leg0", A, IF, r0, 0.02, None, CONE_STR, alpha=CONE_ALPHA, core=CONE_CORE, gain=3.5)
    for o in legs:
        o.visible_glossy = False
    print(f"[r26h b302] cone start {CONE_OFF} m in front of rim, r {r0:.3f} -> 0.02", flush=True)
    ghost_neck()
    cam = camera(sc, RC, IF, PL, H24)
    # ---- BEAMCHECK / 25 / 26
    ch = {"legs": [legs], "spots": [None, None], "stops": [(A, None), (IF, None)], "radii": [r0, 0.02],
          "leg_radii": [tuple(legs[0]["r25_radii"])], "mirrors": {}}
    rx = (sc.render.resolution_x, sc.render.resolution_y)
    sc.render.resolution_x, sc.render.resolution_y = 960, 540
    BR.check(sc, ch, FR, exits=(1,), tag="B3_02")
    sc.render.resolution_x, sc.render.resolution_y = rx
    sc.frame_set(f0)
