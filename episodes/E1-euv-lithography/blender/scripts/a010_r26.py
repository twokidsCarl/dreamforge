"""Round 26 A0_10 scene-level restructure (R26_ROOT_CAUSE row 1; MAIN process, wired via r2_cutaway.R26_A010).

R25 review (p2, H13 + H8): 「光柱在右上方两处转折，画面里看不到镜子…每个转折点都放一面带镜座的实心镜…上层转折点应该是
掩模（掩模层在顶）…光路改成 光源 → IF → 照明 → 掩模（顶）→ 投影 → 晶圆（底）」. R24 / R25 tried 4-5 open turns in the
side-on title cutaway; R26 sketch (r26smoke/sketch26/sk26_search.py, real R24-dolly cameras): with the IF passed
straight, the best open 3-turn path reaches only min n.to_cam 0.29, and two CONSECUTIVE turn mirrors can never both
show their face to a side-on camera when every leg stays >= 45 deg off the line of sight (the light would have to arrive
from the camera side at both). So the title shot gets FEWER open turns:

  collector -> IF -> [ILLUMINATOR housing: closed machined box, IF enters its left port; FFM / PFM / G1 / G2 inside]
  -> exit port (front, top right) -> MASK (the one open turn: reticle stage hung below the roof, patterned face turned
  down-front to the camera, n.to_cam 0.6-0.7 on all three frames) -> [PROJECTION barrel: closed lens column, light
  enters its top and leaves its nose, PO mirrors inside] -> wafer (converging cone onto the wafer stage).

Every open stop: the mask (front-facing mirror, landing on its pattern) or a straight pass-through port (bend 0).
Camera = the R23/R24 dolly (D kept, no orbit -> R24 title / subtitle clearance kept). Beams = beam_r26 soft shells.
pre(): moves the builder's illuminator / PO / wafer / mask stops (housing interior, barrel interior, new wafer and
mask); post(): deletes the earlier title path objects, builds the two housings + the three chains, BEAMCHECK/25/26.
"""
import math

import bpy
from mathutils import Vector

JOB = (54, 119, 184)
IF = Vector((-4.55, 0.0, 2.55))
COLL = Vector((-8.25, 0.0, 2.3))
AX = (IF - COLL).normalized()
HOUSE = ((-3.95, -1.12), (-0.75, 1.0), (1.55, 4.3))     # illuminator housing x / y / z ranges
WINDOW = ((-2.75, -1.35), (3.0, 4.12))                   # front-wall window onto the field-facet mirror (x, z)
ENTRY = IF + AX * ((HOUSE[0][0] - IF.x) / AX.x)          # left wall, on the collector axis (IF straight)
EXIT = Vector((-1.12, 0.0, 3.95))                        # exit port on the right wall, top (sketch26/sk26_mask.py)
MASK = Vector((-0.05, 0.45, 3.6))                        # mask surface point (below the roof / stage bridge)
D_OUT = Vector((0.04, -0.29, -0.956)).normalized()        # mask -> projection barrel -> wafer (one straight line)
WAFER_Z = 0.62
WAFER = MASK + D_OUT * ((MASK.z - WAFER_Z) / -D_OUT.z)
BARREL = (MASK + D_OUT * 0.95, WAFER - D_OUT * 0.6)      # barrel top / nose points on the axis (mask turn stands clear)
BARREL_R = 0.42
PREFIXES = ("A0PathR24", "A0PathR23_", "A0LandR23_", "BeamSeg", "R2_spot", "TitleCone", "TitleLand", "IllumSrcCone",
            "A0R25")


def n_mask():
    return ((EXIT - MASK).normalized() + D_OUT).normalized()


def pre(variant, shot, mod):
    import build_cutaway_r2 as B
    import hero_kit_r10 as HK
    # illuminator mirrors (field / pupil facets, condenser G1, fold G2) all inside the closed housing
    B.FFM = Vector((-2.0, 0.25, 3.7))
    B.PFM = Vector((-3.3, 0.3, 2.1))
    B.G1 = Vector((-1.6, 0.3, 2.6))
    B.G2 = Vector((-2.4, 0.35, 2.2))
    # the builder's open PO zig-zag mirrors (title variant reads r2_cutaway.PO_ZIGZAG after pre) go into the closed
    # housing's lower half (out of sight); the projection optics are the closed barrel built in post()
    mod.PO_ZIGZAG = ((-3.4, 0.4, 1.95), (-3.0, 0.45, 2.2), (-2.6, 0.4, 1.95), (-2.2, 0.45, 2.2), (-1.8, 0.4, 1.95),
                     (-1.5, 0.45, 2.2))
    B.WAFER = WAFER.copy()
    B.MASK = MASK.copy()
    nm = n_mask()
    rorig = getattr(HK.reticle, "_r26_orig", HK.reticle)

    def _ret(P, c, *a_, **kw):
        if (Vector(c) - MASK).length < 1e-6:         # the mask turns its pattern down-front toward the camera
            kw["face"] = tuple(nm)
            kw["size"] = 1.0
        return rorig(P, c, *a_, **kw)
    _ret._r26_orig = rorig
    HK.reticle = _ret
    print("[r26a] A0_10 mask", tuple(round(x, 3) for x in MASK), "n", tuple(round(x, 3) for x in nm),
          "wafer", tuple(round(x, 3) for x in WAFER), "entry", tuple(round(x, 3) for x in ENTRY), flush=True)


def _mats():
    import kit_r2 as K
    return dict(
        shell=K.mat("A0R26Shell", (0.86, 0.87, 0.88), metal=0.6, rough=0.32, brushed=0.08),
        panel=K.mat("A0R26Panel", (0.70, 0.72, 0.75), metal=0.8, rough=0.26, brushed=0.1),
        dark=K.mat("A0R26Dark", (0.06, 0.065, 0.075), metal=0.4, rough=0.4),
        flange=K.mat("A0R26Flange", (0.62, 0.63, 0.66), metal=1.0, rough=0.2),
        barrel=K.mat("A0R26Barrel", (0.80, 0.81, 0.83), metal=1.0, rough=0.32),
        bolt=K.mat("A0R26Bolt", (0.55, 0.56, 0.6), metal=1.0, rough=0.25),
        hose=K.mat("A0R26Hose", (0.12, 0.24, 0.62), rough=0.4),
        port=K.emit_mat("A0R26PortGlow", (0.62, 0.42, 1.0), 3.0),
    )


def _rot_to(d):
    """Euler that turns local +Z onto direction d."""
    return Vector((0, 0, 1)).rotation_difference(Vector(d).normalized()).to_euler()


def _housing(M):
    import kit_r2 as K
    (x0, x1), (y0, y1), (z0, z1) = HOUSE
    c = Vector(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
    s = Vector((x1 - x0, y1 - y0, z1 - z0))
    sh, pn, dk, fl, bo, ho = K.MB(), K.MB(), K.MB(), K.MB(), K.MB(), K.MB()
    t = 0.06
    (wx0, wx1), (wz0, wz1) = WINDOW
    for cc, ss in (((c.x, y1 - t / 2, c.z), (s.x, t, s.z)), ((x0 + t / 2, c.y, c.z), (t, s.y, s.z)),
                   ((x1 - t / 2, c.y, c.z), (t, s.y, s.z)), ((c.x, c.y, z1 - t / 2), (s.x, s.y, t)),
                   ((c.x, c.y, z0 + t / 2), (s.x, s.y, t)),
                   # front wall around the window opening
                   (((x0 + wx0) / 2, y0 + t / 2, c.z), (wx0 - x0, t, s.z)), (((wx1 + x1) / 2, y0 + t / 2, c.z), (x1 - wx1, t, s.z)),
                   (((wx0 + wx1) / 2, y0 + t / 2, (z0 + wz0) / 2), (wx1 - wx0, t, wz0 - z0)),
                   (((wx0 + wx1) / 2, y0 + t / 2, (wz1 + z1) / 2), (wx1 - wx0, t, z1 - wz1))):
        sh.box(cc, ss)
    # window frame (machined bezel + bolts) and two big access panels left of it
    wc = Vector(((wx0 + wx1) / 2, y0 - 0.01, (wz0 + wz1) / 2))
    for cc, ss in (((wc.x, wc.y, wz0 - 0.04), (wx1 - wx0 + 0.16, 0.05, 0.08)), ((wc.x, wc.y, wz1 + 0.04), (wx1 - wx0 + 0.16, 0.05, 0.08)),
                   ((wx0 - 0.04, wc.y, wc.z), (0.08, 0.05, wz1 - wz0)), ((wx1 + 0.04, wc.y, wc.z), (0.08, 0.05, wz1 - wz0))):
        fl.box(cc, ss)
    for k in range(8):
        bo.cyl((wx0 - 0.04 + (wx1 - wx0 + 0.08) * (k % 4) / 3, y0 - 0.04, wz0 - 0.04 if k < 4 else wz1 + 0.04), 0.012, 0.02,
               rot=(math.pi / 2, 0, 0), seg=10)
    for j in range(2):
        pc = Vector(((x0 + wx0) / 2, y0 - 0.012, z0 + (j + 0.5) * s.z / 2))
        pn.box(pc, ((wx0 - x0) - 0.12, 0.02, s.z / 2 - 0.1))
    dk.box(((x0 + wx0) / 2, y0 - 0.004, c.z), ((wx0 - x0) - 0.02, 0.006, s.z - 0.02))
    # dark interior lining so the window reads as a lit cavity
    dk.box((c.x, y1 - t - 0.01, c.z), (s.x - 2 * t, 0.01, s.z - 2 * t))
    # base plinth + top service rail
    dk.box((c.x, c.y, z0 - 0.06), (s.x + 0.12, s.y + 0.12, 0.12))
    fl.box((c.x, c.y, z1 + 0.03), (s.x + 0.06, s.y + 0.06, 0.06))
    # entry port (left wall, on the collector axis) and exit port (right wall, along the exit leg)
    d_in, d_out = AX, (MASK - EXIT).normalized()
    for p, d in ((ENTRY, d_in), (EXIT, d_out)):
        e = _rot_to(d)
        fl.ring(p, 0.2, 0.11, 0.05, rot=e, seg=48)
        fl.cyl(p - d * 0.08, 0.17, 0.12, rot=e, seg=40)
        bo.bolts(p + d * 0.03, 0.155, 8, 0.012, 0.02, rot=e)
    # side hoses / cable runs on the housing (density without a texture wall)
    ho.path([(x0 + 0.2, y0 - 0.05, z0 + 0.15), (x0 + 0.2, y0 - 0.05, z1 - 0.3), (x1 - 0.4, y0 - 0.05, z1 - 0.3)], 0.025)
    ho.path([(x1 - 0.25, y0 - 0.06, z0 + 0.1), (x1 - 0.25, y0 - 0.06, z0 + 0.9)], 0.03)
    obs = [sh.obj("A0R26Housing", M["shell"], bevel=0.02), pn.obj("A0R26HousePanels", M["panel"], bevel=0.008),
           dk.obj("A0R26HouseDark", M["dark"]), fl.obj("A0R26HouseFlange", M["flange"], bevel=0.005),
           bo.obj("A0R26HouseBolts", M["bolt"]), ho.obj("A0R26HouseHose", M["hose"])]
    pg = K.MB()
    for p, d in ((ENTRY, d_in), (EXIT, d_out)):
        pg.cyl(p - d * 0.005, 0.11, 0.01, rot=_rot_to(d), seg=32)
    obs.append(pg.obj("A0R26PortGlow", M["port"]))
    return obs


def _barrel(M):
    import kit_r2 as K
    a, b = BARREL
    d = (b - a).normalized()
    e = _rot_to(-d)                                       # local +Z = up the column
    L = (b - a).length
    bm, fl, bo, dk = K.MB(), K.MB(), K.MB(), K.MB()
    bm.tube(tuple(a), tuple(b + d * 0.0), BARREL_R, seg=64)
    # stacked lens-cell flanges + bolt circles (reads as a lens column)
    for k in range(6):
        p = a.lerp(b, (k + 0.5) / 6)
        fl.ring(p, BARREL_R + 0.05, BARREL_R - 0.01, 0.05, rot=e, seg=64)
        bo.bolts(p, BARREL_R + 0.025, 12, 0.012, 0.07, rot=e)
    # top entrance (open ring) and the nose cone toward the wafer
    fl.ring(a, BARREL_R + 0.08, 0.16, 0.06, rot=e, seg=64)
    dk.cyl(a + d * 0.04, 0.155, 0.02, rot=e, seg=40)
    bm.tube(tuple(b), tuple(b + d * 0.32), BARREL_R, seg=64, r2=0.17)
    fl.ring(b + d * 0.32, 0.2, 0.09, 0.04, rot=e, seg=48)
    # two mounting arms back to the frame
    for z in (0.35, 0.75):
        p = a.lerp(b, z)
        dk.tube(tuple(p), tuple(Vector((p.x, 1.1, p.z))), 0.05, seg=16)
    obs = [bm.obj("A0R26Barrel", M["barrel"], bevel=0.0), fl.obj("A0R26BarrelFlange", M["flange"]),
           bo.obj("A0R26BarrelBolts", M["bolt"]), dk.obj("A0R26BarrelDark", M["dark"])]
    return obs


def _anchors(points):
    """kit_r2.anchors writes one JSON per frame and a second handler would overwrite it: MERGE into the same file."""
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
        for k, p in points.items():
            v = world_to_camera_view(sc, sc.camera, p)
            res[k] = [round(v.x, 4), round(1 - v.y, 4), round(v.z, 3)]
        os.makedirs(out, exist_ok=True)
        with open(fp, "w") as fh:
            json.dump(res, fh)
    bpy.app.handlers.frame_change_post.append(h)


def post(sc, variant, shot):
    import beam_r26 as BR
    gone = [ob.name for ob in list(bpy.data.objects) if ob.name.startswith(PREFIXES)]
    for nm in gone:
        bpy.data.objects.remove(bpy.data.objects[nm], do_unlink=True)
    print(f"[r26a] A0_10 removed {len(gone)} earlier path objects", flush=True)
    M = _mats()
    _housing(M)
    _barrel(M)
    nm = n_mask()
    src = COLL + AX * 0.75
    ex = {}
    import cut_beam_r25_a010 as A25
    mobj = A25._obj_at(MASK, skip=("A0R26",))
    if mobj is not None:
        ex[1] = mobj
    S = 7.0
    chA = BR.chain("A0R26Src", [(src, None), (IF, None), (ENTRY, None)], [0.42, 0.03, 0.1], strength=S,
                   spot_strength=0.0, land_final=False, mirrors=False)
    import build_cutaway_r2 as B
    chI = BR.chain("A0R26In", [(ENTRY, None), (B.FFM, (ENTRY - B.FFM).normalized())], [0.1, 0.035], strength=S,
                   spot_strength=16.0)
    chB = BR.chain("A0R26Ill", [(EXIT, None), (MASK, nm), (BARREL[0], None)], [0.16, 0.05, 0.15], strength=S,
                   spot_strength=14.0, land_final=False, existing=ex, mirrors=not ex)
    chC = BR.chain("A0R26Po", [(BARREL[1] + (BARREL[1] - BARREL[0]).normalized() * 0.32, None), (WAFER, Vector((0, 0, 1)))],
                   [0.13, 0.012], strength=S, spot_strength=14.0)
    _anchors({"r26_house": Vector(((WINDOW[0][0] + WINDOW[0][1]) / 2, HOUSE[1][0], WINDOW[1][0] - 0.2)),
              "r26_mask": MASK.copy(), "r26_barrel": BARREL[0].lerp(BARREL[1], 0.45) + Vector((-BARREL_R, -0.2, 0))})
    for f in JOB:
        sc.frame_set(f)
        print(f"[r26a] A0_10 cam f{f}", tuple(round(x, 3) for x in sc.camera.matrix_world.translation), flush=True)
    bad = []
    for tag, ch in (("A0_10 src", chA), ("A0_10 ill", chB), ("A0_10 po", chC)):
        bad += BR.check(sc, ch, JOB, tag=tag)
    print(f"BEAMCHECK26 A0_10 SUMMARY {'OK' if not bad else 'NOGO ' + str(len(bad))}", flush=True)
    return sc
