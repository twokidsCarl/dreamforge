"""R25 cbeam helper for A0_10 (rows 1 + 2 [+ 4]). See cut_beam_r25.py.
Path (x-z, camera on -y): collector mouth -> IF -> FFM (on the collector axis, IF straight) -> PFM (up-right, deeper)
-> mask (existing reticle, pattern down) -> projection mirror (deeper, new mounted mirror) -> wafer.
Depth stagger + camera orbit from the joint search r25smoke/cbeam/sk/srch.py (seed 11: min |n.to_cam| 0.73)."""
import math

import bpy
from mathutils import Vector, Matrix

AZ, EL = 9.4, -1.0                          # small orbit (az 9.4 deg, camera RAISED 1 deg) of the R24 dolly about the machine centre (D kept)
PIV = Vector((-1.5, 0.0, 2.6))
D_FFM, Y_FFM = 1.6, 0.2                     # FFM 1.6 m beyond the IF on the collector axis, 0.2 m deeper: IF bend 7 deg (<= 8)
PFM_XZ = (-2.122, 3.563)
X_MASK, Z_MASK = 0.25, 4.0                  # mask 0.3 m left / 0.35 m lower: out from behind the projection-box roof + stage bar
Y_PFM, Y_MASK, Y_PO, Y_WAFER = -0.649, 0.6, 0.306, -0.148   # depth stagger (cbeam/sk/off6.py seed 1, real cameras)
JOB = (54, 119, 184)
_N = {}
_MASK0 = Vector((0.55, 0.3, 4.35))          # build_cutaway_r2.MASK default
_PO0 = Vector((0.93, 0.25, 1.75))           # build_cutaway_r2.PO[0] default


def _bis(a, p, b):
    return ((a - p).normalized() + (b - p).normalized()).normalized()


def points():
    import build_cutaway_r2 as B
    ax = (B.IF - B.COLL).normalized()
    src = B.COLL + ax * 0.75
    ffm = B.IF + ax * D_FFM + Vector((0, Y_FFM, 0))
    pfm = Vector((PFM_XZ[0], Y_PFM, PFM_XZ[1]))
    mask = Vector((X_MASK, _MASK0.y + Y_MASK, Z_MASK))
    po = _PO0 + Vector((0, Y_PO, 0))
    return [src, B.IF.copy(), ffm, pfm, mask, po, B.WAFER.copy() + Vector((0, Y_WAFER, 0))]


def pre():
    import build_cutaway_r2 as B
    import kit_r2 as K
    pts = points()
    import hero_kit_r10 as HK
    B.FFM = pts[2].copy()
    B.PFM = pts[3].copy()
    B.MASK = pts[4].copy()
    B.PO[0] = pts[5].copy()
    n_ffm = _bis(pts[1], pts[2], pts[3])
    n_pfm = _bis(pts[2], pts[3], pts[4])
    n_mask = _bis(pts[3], pts[4], pts[5])
    n_po = _bis(pts[4], pts[5], pts[6])
    _N.update(ffm=n_ffm, pfm=n_pfm, mask=n_mask, po=n_po)
    rorig = getattr(HK.reticle, "_r25_orig", HK.reticle)

    def _ret(P, c, *a, **kw):
        if (Vector(c) - pts[4]).length < 1e-6:          # the mask turns to its reflection bisector (pattern down-front)
            kw["face"] = tuple(n_mask)
            kw["size"] = 0.75                         # 0.62 -> 0.75 so the turned mask reads as a plate
        return rorig(P, c, *a, **kw)
    _ret._r25_orig = rorig
    HK.reticle = _ret
    orig = getattr(K.mirror_normal, "_r25_orig", K.mirror_normal)

    def _mn(a, p, b, *args, **kw):
        # builder: n = norm(mirror_normal(IF, FFM, PFM) + (0, -0.75, 0)); n2 = norm(mirror_normal(FFM, PFM, G1) + (0, -0.5, 0))
        if (Vector(p) - pts[2]).length < 1e-6 and (Vector(a) - pts[1]).length < 1e-6:
            return n_ffm + Vector((0, 0.75, 0))
        if (Vector(p) - pts[3]).length < 1e-6 and (Vector(a) - pts[2]).length < 1e-6:
            return n_pfm + Vector((0, 0.5, 0))
        if (Vector(p) - pts[5]).length < 1e-6 and (Vector(a) - pts[4]).length < 1e-6:
            return n_po.copy()
        return orig(a, p, b, *args, **kw)
    _mn._r25_orig = orig
    K.mirror_normal = _mn
    print("[r25c] A0_10 FFM ->", tuple(round(x, 3) for x in B.FFM), "PFM ->", tuple(round(x, 3) for x in B.PFM),
          "MASK ->", tuple(round(x, 3) for x in B.MASK), "PO0 ->", tuple(round(x, 3) for x in B.PO[0]))


def _obj_at(p, skip=("A0R25",)):
    """smallest mesh object whose world bbox contains p (an existing scene part at that stop)."""
    best, bv = None, 1e9
    for ob in bpy.data.objects:
        if ob.type != "MESH" or ob.name.startswith(skip) or ob.hide_render:
            continue
        cs = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
        lo = Vector([min(c[i] for c in cs) for i in range(3)])
        hi = Vector([max(c[i] for c in cs) for i in range(3)])
        if all(lo[i] - 0.03 <= p[i] <= hi[i] + 0.03 for i in range(3)):
            v = max(1e-6, (hi - lo).x) * max(1e-6, (hi - lo).y) * max(1e-6, (hi - lo).z)
            if v < bv:
                best, bv = ob, v
    return best


def orbit(sc):
    cam = sc.camera
    e = bpy.data.objects.new("A0R25CamPivot", None)
    sc.collection.objects.link(e)
    e.location = PIV
    bpy.context.view_layer.update()
    rig = [cam] + [c.target for c in cam.constraints if getattr(c, "target", None) is not None]
    for ob in rig:                         # camera AND its look-at target orbit rigidly (= the searched pose)
        if ob.parent is None:
            ob.parent = e
            ob.matrix_parent_inverse = e.matrix_world.inverted()
    print("[r25c] A0_10 orbit rig", [o.name for o in rig])
    e.rotation_euler = (math.radians(EL), 0, math.radians(AZ))
    bpy.context.view_layer.update()


def post(sc):
    import beam_r25 as BR
    gone = [ob.name for ob in list(bpy.data.objects) if ob.name.startswith("A0PathR24")]
    for nm in gone:
        bpy.data.objects.remove(bpy.data.objects[nm], do_unlink=True)
    print(f"[r25c] A0_10 removed {len(gone)} R24 chain objects")
    pts = points()
    stops = [(pts[0], None), (pts[1], None), (pts[2], _bis(pts[1], pts[2], pts[3])),
             (pts[3], _bis(pts[2], pts[3], pts[4])), (pts[4], _bis(pts[3], pts[4], pts[5])),
             (pts[5], _bis(pts[4], pts[5], pts[6])), (pts[6], Vector((0, 0, 1)))]
    existing = {}
    for i in (2, 3, 4, 5):
        ob = _obj_at(pts[i])
        if ob is not None:
            existing[i] = ob
    print("[r25c] A0_10 existing mirrors", {i: o.name for i, o in existing.items()})
    radii = [0.45, 0.03, 0.2, 0.067, 0.2, 0.067, 0.022]      # mouths >= 0.2 m, 3:1 per leg
    ch = BR.chain("A0R25Path", stops, radii, strength=9.0, alpha=0.9, core=0.28, spot_strength=14.0, existing=existing,
                  mirror_r=0.36)
    orbit(sc)
    for f in JOB:
        sc.frame_set(f)
        print(f"[r25c] A0_10 cam f{f}", tuple(round(x, 3) for x in sc.camera.matrix_world.translation))
    BR.check(sc, ch, JOB, tag="A0_10")
    try:
        import cut_beam_r25_a010d as D
        D.build(sc)
    except ImportError:
        pass
    return ch
