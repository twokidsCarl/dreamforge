"""R23 hook module for the srca group (B1_15 / B2_08), R23_ROOT_CAUSE row 5 (collector face reads black / matte).

R22 review B1_15: 「镜面本身是黑的，读成『黑玻璃盘』，观众看不到『原子级精度的镜面』；加掠射高光、镜面倒映…让反光面可见」
R22 review B2_08: 「镜面本身偏灰暗、颗粒斑点看不清」「气流线细、末端孤立白点，像『悬空白点』；用有粗细渐变的流带」

post():
  * B1_15 (on top of b115_r22_build): a glossy-only lit panel placed on the mirror-reflected camera rays of the
    NEAR half of the face (z < 0 = the black lower half on screen, below the plasma; dimmed on the axis line where the cone leaves),
    clamped inside the vessel wall; radial + side-to-side gradient so the polished concave shows a graded grazing
    sheen. Re-solved per frame (shape keys), so it sits on the same face patch over the whole push-in.
  * B2_08 (on top of R21 pixels; b208_r22 not live): mirror face polished neutral metal (rough 0.03), matte grey
    shell, dark larger tin deposits; glossy-only graded panel on the reflected rays of the LOWER face (away from
    the SnH4 streamlines, which rise off the upper face), re-solved at 8 frames over the whole shot (R22: solved
    at 133 only); SnH4 lines + moving fleck spheres -> tapered flow ribbons with end fades and a travelling streak.
Env knobs: S23_*. Remove a shot from r2_source.R23_SRC -> R22 pixels.
"""
import math
import os

_E = os.environ
_MOD = [None]


def pre(variant, shot, mod):
    _MOD[0] = mod


def post(sc, variant, shot):
    if shot == "B1_15" and variant == "contrast":
        _b115(sc)
    elif shot == "B2_08" and variant == "clean":
        _b208(sc)


def _b115(sc):
    """The lower (near-rim) face reflects camera rays forward out of the mouth (+x, sketch: hits at x 1.5-8 m,
    |yz| <= 1.2 at x = 1.45) -> the open front / black world (R22 dropped the front end plate). A real vessel
    front end cap is put back there (camera-invisible: it lies behind / below the camera's view, the camera only
    sees it in the mirror), with flange ring, bolt circle, port flanges and a viewport, lit by its own linked area
    lights (nothing else in the shot changes lighting), so the polished concave face shows a graded reflection of
    lit chamber structure on its whole lower half, every frame (real geometry, no per-frame solve)."""
    import bpy
    from mathutils import Vector
    import kit_r2 as K
    import b115_r21 as B
    xp = float(_E.get("S23_PX", "1.45"))
    rv = B.VES_R + 0.05
    rot = B.ROT_X
    RC = float(_E.get("S23_RC", "0.78"))
    pm = K.mat("B115EndCapR23", (0.5, 0.52, 0.56), metal=0.7, rough=float(_E.get("S23_PR", "0.42")))
    dk = K.mat("B115EndCapDarkR23", (0.06, 0.065, 0.075), metal=0.6, rough=0.5)
    pl, fl, bo, ho = K.MB(), K.MB(), K.MB(), K.MB()
    pl.cyl((xp + 0.03, 0, 0), rv, 0.06, rot=rot, seg=128)
    fl.ring((xp - 0.02, 0, 0), rv, rv - 0.14, 0.06, rot=rot, seg=128)
    fl.ring((xp - 0.02, 0, 0), RC + 0.1, RC, 0.05, rot=rot, seg=96)
    bo.bolts((xp - 0.055, 0, 0), rv - 0.07, 36, 0.016, 0.02, rot=rot)
    for k in range(6):                   # port flanges on the cap (y, z)
        b = math.radians(30 + 60 * k)
        c = Vector((xp - 0.02, 1.1 * math.cos(b), 1.1 * math.sin(b)))
        fl.ring(tuple(c), 0.13, 0.085, 0.07, rot=rot, seg=48)
        ho.cyl(tuple(c + Vector((0.01, 0, 0))), 0.086, 0.03, rot=rot, seg=40)
        bo.bolts(tuple(c - Vector((0.04, 0, 0))), 0.108, 8, 0.008, 0.012, rot=rot)
    # dark duct strip on the cap where the hole -> plasma laser line is mirrored (sketch: cap y -0.25..0,
    # z -1.4..-0.2; z > -RC is the dark centre): the laser stays on a dark background, no bright reflection behind it
    ho.box((xp - 0.1, -0.12, -1.12), (0.05, float(_E.get("S23_DW", "0.5")), 0.9))
    ho.cyl((xp - 0.0, 0, 0), RC, 0.02, rot=rot, seg=96)   # dark centre: frames the plasma / laser
    obs = [pl.obj("B115EndCapR23", pm, bevel=0.003), fl.obj("B115EndCapFlangeR23", pm, bevel=0.003),
           bo.obj("B115EndCapBoltsR23", K.mat("B115EndCapBoltM", (0.75, 0.76, 0.78), metal=1.0, rough=0.3)),
           ho.obj("B115EndCapPortsR23", dk)]
    recv = bpy.data.collections.new("B115EndCapRecvR23")
    for ob in obs:
        ob.visible_camera = False
        ob.visible_shadow = False
        recv.objects.link(ob)
    e = float(_E.get("S23_LE", "60"))
    for nm, lo, tg, sz, en in (("A", (0.9, 0.7, -0.9), (xp, -0.3, 0.2), 0.9, e),
                                ("B", (0.9, -0.8, 0.6), (xp, 0.4, -0.4), 0.7, e * 0.35)):
        lo_ = K.area("B115EndCapLight%sR23" % nm, lo, tg, sz, en, (0.85, 0.9, 1.0))
        lo_.visible_camera = False
        lo_.visible_glossy = False
        lo_.light_linking.receiver_collection = recv
        lo_.light_linking.blocker_collection = recv


def _b208(sc):
    import bpy
    import bmesh
    from mathutils import Vector
    import kit_r2 as K
    import b115_r17 as B115
    import src_r23_refl as RF
    S = _MOD[0]
    cam = sc.camera
    n = sc.frame_end
    F = B115.B_F
    mir = bpy.data.objects.get("CollB208_mirror")
    sub = bpy.data.objects.get("CollB208_substrate")
    if sub is not None:
        sub.data.materials.clear()
        sub.data.materials.append(K.mat("CollShellMatteR23", (0.34, 0.345, 0.35), metal=0.1, rough=0.8))
    if mir is not None:
        mir.data.materials.clear()
        mir.data.materials.append(K.mat("CollFacePolishR23", (0.9, 0.91, 0.93), metal=1.0,
                                        rough=float(_E.get("S28_ROUGH", "0.03"))))
    dep = bpy.data.objects.get("TinDeposits")
    if dep is not None:              # dark matte spots, each disc larger, so they read on the bright sheen
        dep.data.materials.clear()
        dep.data.materials.append(K.mat("TinDepositDarkR23", (0.04, 0.04, 0.045), metal=0.2, rough=0.85))
        sc_ = float(_E.get("S28_DEPS", "1.5"))
        bm = bmesh.new()
        bm.from_mesh(dep.data)
        seen = set()
        for v in bm.verts:
            if v.index in seen:
                continue
            stack, isl = [v], []
            seen.add(v.index)
            while stack:
                w = stack.pop()
                isl.append(w)
                for e in w.link_edges:
                    o = e.other_vert(w)
                    if o.index not in seen:
                        seen.add(o.index)
                        stack.append(o)
            c = sum((w.co for w in isl), Vector()) / len(isl)
            for w in isl:
                w.co = c + (w.co - c) * sc_
        bm.to_mesh(dep.data)
        bm.free()

    def face(r, a):
        y, z = r * math.cos(a), r * math.sin(a)
        return Vector((B115.face_x(r), y, z)), Vector((1, -y / (2 * F), -z / (2 * F))).normalized()

    d0 = float(_E.get("S28_D", "1.2"))
    a0, a1 = (math.radians(float(_E.get(k, v))) for k, v in (("S28_A0", "185"), ("S28_A1", "355")))
    # crisp concentric lit bands with dark gaps along the radius (sharp edges = polished, not satin; concentric
    # around the hole like a turned mirror, not radial spokes that could echo the pump rotor), soft fade across
    m = RF.sheet_mat("B208SheenR23M", (0.82, 0.87, 1.0), float(_E.get("S28_E", "0.6")),
                     [(0.0, 0.0), (0.06, 0.55), (0.3, 0.1), (0.38, 1.0), (0.62, 0.12), (0.7, 0.8), (0.9, 0.0)],
                     [(0.0, 0.0), (0.15, 0.8), (0.5, 1.0), (0.85, 0.6), (1.0, 0.0)], u_interp="CONSTANT")
    RF.reflection_sheet(sc, cam, "B208SheenR23", face, (0.16, 0.65), (a0, a1),
                        [1, 30, 60, 95, 133, 170, 206, n], lambda P, rf: d0, m)
    # SnH4: tapered flow ribbons replace the thin lines + moving fleck spheres (「末端孤立白点」)
    for ob in list(bpy.data.objects):
        if ob.name == "SnH4Lines" or ob.name.startswith("SnH4_"):
            bpy.data.objects.remove(ob, do_unlink=True)
    a_p, z_p = math.radians(124), 0.5
    nrm_p = Vector((-math.cos(a_p), -math.sin(a_p), 0))
    port = Vector((math.cos(a_p), math.sin(a_p), 0)) * (S.CHAMBER_R - 0.02) + Vector((0, 0, z_p))
    paths = []
    for i in range(9):
        rr = 0.22 + 0.03 * i
        a = math.radians(55 + 7 * i)
        y, z = rr * math.cos(a), rr * math.sin(a)
        nrm = Vector((1, -y / (2 * F), -z / (2 * F))).normalized()
        p0 = Vector((B115.face_x(rr), y, z)) + nrm * 0.004
        p1 = p0 + nrm * 0.18
        p3 = port + nrm_p * 0.06 + Vector((0, 0, (i - 4) * 0.02))
        p2 = p1.lerp(p3, 0.5) + Vector((0.12, 0, 0.18))
        pts = []
        for k in range(41):
            u = k / 40
            pts.append((1 - u) ** 3 * p0 + 3 * (1 - u) ** 2 * u * p1 + 3 * (1 - u) * u * u * p2 + u ** 3 * p3)
        paths.append(pts)
    RF.ribbons(sc, "SnH4RibbonsR23", paths, n, w0=float(_E.get("S28_W0", "0.0012")),
               w1=float(_E.get("S28_W1", "0.0038")))
