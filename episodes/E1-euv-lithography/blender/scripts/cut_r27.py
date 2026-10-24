"""Round 27 hook (cut sub-agent; shots in r2_cutaway.R27_CUT = C_03 / B7_06 / B3_02). Layered AFTER the R22..R26 hooks:
pre(variant, shot, mod) at the start of build(), post(sc, variant, shot) at the end. Remove a shot from R27_CUT -> R26
pixels; each root-cause row has ONE module-level switch (False -> that row's R26 pixels):

  ORBIT_R27   row 3D (B3_02): R26 push + 18 deg orbit about the collector axis (main-process sketch
              sketch27/pre_b302_orbit.py: rim area +33 %, BEAMCHECK all OK) - cut_hero_r26_b302._key re-keyed.
  CONE_R27    row 3 (B3_02): 「锥的大口没有贴着镜面的边缘起始」 -> the rim -> IF cone starts ON the rim: CONE_MODE "rim25"
              (candidate) = the R25 beam_r25 shell the R26 main smoke kept (strength 1.1 / alpha 0.32 / gain 3.5) rebuilt
              from the rim plane (off 0.02) with its wide end = R_RIM - 0.03 (was 0.92 R_RIM), visible_glossy off, plus a
              thin violet landing-glow ring ON the rim (CollectRimGlowR27, glossy off). CONE_MODE "soft" (beam_r26 soft
              shell, ghosted + darkened neck) is kept for R28 only: at 8 spp its wide end vanished over the dish face.
  ONETURN_R27 row 3 (B7_06): see cut_r27_b706.py (soft-shell rebuild of the M5 -> M6 -> M5-hole -> wafer chain, bright
              converging leg). C_03: NOT built this round (no-op -> R26 pixels; plan in r27smoke/cut/SMOKE.md R28 notes).
  KIT_R27     row 4 (B7_06): see cut_r27_b706.py.
"""
import math

import bpy
from mathutils import Vector

ORBIT_R27 = True
CONE_R27 = True
ONETURN_R27 = True
KIT_R27 = True

ORB = 18.0
CONE_MODE = "rim25"     # "soft" = beam_r26 soft shell (8-spp: wide end vanished over the dish face -> reads mid-air)
B302_CONE = dict(off=0.02, strength=1.3, alpha=0.3, core=0.2, gain=0.4)
NECK_ALPHA = 0.1
RING_STR = 3.0
RING_COL = (0.32, 0.12, 1.0)


# ---------------------------------------------------------------- B3_02
def _b302_pre():
    import cut_hero_r26_b302 as H
    if CONE_R27 and CONE_MODE == "soft":
        H.CONE_R26 = True
        H.CONE_OFF = B302_CONE["off"]
        H.CONE_STR, H.CONE_ALPHA, H.CONE_CORE = B302_CONE["strength"], B302_CONE["alpha"], B302_CONE["core"]
        H.NECK_ALPHA = NECK_ALPHA
    if ORBIT_R27:
        from mathutils import Matrix

        def _key(sc, cam, tgt, RC, IF, dv, d0, d1, tt):
            import kit_r2 as K
            cam.animation_data_clear()
            tgt.animation_data_clear()
            n = sc.frame_end
            T = RC.lerp(IF, tt)
            ax = (IF - RC).normalized()

            def rot(a):
                return Matrix.Rotation(math.radians(a), 3, ax) @ dv
            keys = []
            for fr, d, a in ((1, d0, ORB / 2), (round(n * 0.5), (d0 + d1) / 2, 0.0), (round(n * 0.85), d1, -ORB * 0.35),
                             (n, d1 - 0.03, -ORB / 2)):
                keys.append((fr, tuple(RC + rot(a) * d), tuple(T)))
            K.key_path(cam, tgt, keys)
        H._key = _key
    print(f"[r27c] B3_02 pre: orbit {ORBIT_R27} ({ORB} deg) cone {CONE_R27} {B302_CONE}", flush=True)


def _emit_mat(name, col, strength):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    for n in list(N):
        if n.type != "OUTPUT_MATERIAL":
            N.remove(n)
    out = next(n for n in N if n.type == "OUTPUT_MATERIAL")
    em = N.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*col, 1)
    em.inputs["Strength"].default_value = strength
    L.new(em.outputs[0], out.inputs["Surface"])
    return m


def _b302_cone_rim25():
    """CONE_MODE "rim25": the R25 rim -> IF shell (the cone the R26 main smoke kept: beam_r25, strength 1.1 / gain 3.5 /
    alpha 0.32) rebuilt with its wide end ON the rim (R_RIM - 0.03 instead of 0.92 R_RIM) from the rim plane."""
    import beam_r25 as BR
    import build_cutaway_r2 as B
    import cut_hero_r24_b302 as H24
    c0, ax, a, b, e1, e2 = H24._ell()
    for ob in list(bpy.data.objects):
        if ob.name.startswith("CollectBeamR24"):
            bpy.data.objects.remove(ob)
    A = H24.rim_centre() + ax * B302_CONE["off"]
    r0 = H24.R_RIM - 0.03
    ch = BR.chain("CollectBeamR27", [(A, None), (Vector(B.IF), None)], [r0, 0.02], strength=1.1, alpha=0.32, gain=3.5)
    for ob in bpy.data.objects:
        if ob.name.startswith("CollectBeamR27"):
            ob.visible_glossy = False
    print(f"[r27c] B3_02 R25 cone rebuilt on the rim r0 {r0:.3f}", flush=True)
    return ch["legs"][0], A, r0


def _b302_cone():
    """Rebuild the R26 rim -> IF soft shell with a low narrow-end gain (R26 hard-codes 3.5: the wide end over the dish
    vanished and the cone appeared to start mid-air)."""
    import beam_r26 as BR
    old = bpy.data.objects.get("CollectBeamR26Leg0")
    if old is None:
        return None
    mw = old.matrix_world.copy()
    import build_cutaway_r2 as B
    import cut_hero_r24_b302 as H24
    c0, ax, a, b, e1, e2 = H24._ell()
    A = H24.rim_centre() + ax * B302_CONE["off"]
    r0 = H24.R_RIM - 0.03     # wide end = the rim (R25 / R26 used 0.92 R_RIM: 「锥的大口没有贴着镜面的边缘起始」)
    bpy.data.objects.remove(old)
    legs = BR.soft_cone("CollectBeamR27Leg0", A, Vector(B.IF), r0, 0.02, None, B302_CONE["strength"],
                        alpha=B302_CONE["alpha"], core=B302_CONE["core"], gain=B302_CONE["gain"])
    for o in legs:
        o.visible_glossy = False
    print(f"[r27c] B3_02 cone rebuilt r0 {r0:.3f} gain {B302_CONE['gain']}", flush=True)
    return legs, A, r0


def _b302_check(sc, legs, A, r0):
    import importlib
    BR = importlib.import_module("beam_r26" if CONE_MODE == "soft" else "beam_r25")
    import build_cutaway_r2 as B
    IF = Vector(B.IF)
    ch = {"legs": [legs], "spots": [None, None], "stops": [(A, None), (IF, None)], "radii": [r0, 0.02],
          "leg_radii": [tuple(legs[0]["r25_radii"])], "mirrors": {}}
    f0 = sc.frame_current
    rx = (sc.render.resolution_x, sc.render.resolution_y)
    sc.render.resolution_x, sc.render.resolution_y = 960, 540
    BR.check(sc, ch, (30, 67, 103), exits=(1,), tag="B3_02 r27")
    sc.render.resolution_x, sc.render.resolution_y = rx
    sc.frame_set(f0)


def _b302_post(sc):
    if not CONE_R27:
        return
    import cut_hero_r24_b302 as H24
    res = _b302_cone() if CONE_MODE == "soft" else _b302_cone_rim25()
    if res is not None:
        _b302_check(sc, *res)
    # landing-glow ring on the rim: a thin emissive torus following the rim curve (slightly in front of the face)
    c0, ax, a, b, e1, e2 = H24._ell()
    n, r = 160, 0.022
    verts, faces = [], []
    pts = [H24._pt(H24.R_RIM - 0.03, 2 * math.pi * k / n) + ax * 0.03 for k in range(n)]
    m = 10
    for k in range(n):
        p, q = pts[k], pts[(k + 1) % n]
        t = (q - pts[k - 1]).normalized()
        u = ax.cross(t).normalized()
        v = t.cross(u).normalized()
        for j in range(m):
            th = 2 * math.pi * j / m
            verts.append(tuple(p + (u * math.cos(th) + v * math.sin(th)) * r))
    for k in range(n):
        for j in range(m):
            a0 = k * m + j
            a1 = k * m + (j + 1) % m
            b0 = ((k + 1) % n) * m + j
            b1 = ((k + 1) % n) * m + (j + 1) % m
            faces.append((a0, a1, b1, b0))
    me = bpy.data.meshes.new("CollectRimGlowR27")
    me.from_pydata(verts, [], faces)
    me.update()
    ob = bpy.data.objects.new("CollectRimGlowR27", me)
    sc.collection.objects.link(ob)
    import kit_r2 as K
    me.materials.append(_emit_mat("CollectRimGlowR27M", RING_COL, RING_STR))
    ob.visible_glossy = False
    ob.visible_shadow = False
    # the inner silver IF-neck cone: darker as well as more see-through (p2 #3 「内锥压暗…别和光锥抢轮廓」)
    gm = bpy.data.materials.get("IFNeckGhostR26")
    if gm is not None:
        bs = next(n_ for n_ in gm.node_tree.nodes if n_.type == "BSDF_PRINCIPLED")
        bs.inputs["Base Color"].default_value = (0.3, 0.3, 0.32, 1)
        bs.inputs["Roughness"].default_value = 0.5
    print("[r27c] B3_02 rim glow ring + darker IF neck", flush=True)


# ---------------------------------------------------------------- dispatch
def pre(variant, shot, mod):
    if shot == "B3_02":
        _b302_pre()
    elif shot == "B7_06":
        import cut_r27_b706 as H
        H.pre(mod, ONETURN_R27, KIT_R27)


def post(sc, variant, shot):
    if shot == "B3_02":
        _b302_post(sc)
    elif shot == "B7_06":
        import cut_r27_b706 as H
        H.post(sc, ONETURN_R27, KIT_R27)
    return sc
