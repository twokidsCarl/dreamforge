"""Round 29 hook (MAIN PROCESS; shots in r2_cutaway.R29_SCENE = B5_01 / C_03). Layered AFTER the R22..R28 hooks and
BEFORE beam_hook_r29 (which converts every beam leg to a beam_r29 volume, so legs moved here are converted after).
R29_ROOT_CAUSE row 3 (hero part >= 1/4). One switch per item:

  FFM_R29  (B5_01) R28 p2 「场分面镜不到画面 1/6，而且高光过曝成白片，读成百叶窗或散热鳍片…中帧把场分面镜做成主角，占 1/4
           以上：一块底板上排满弧形长条小镜，每片镜面带镜座，压掉过曝高光」 + 「每帧都保留完整的一条光路」:
           * the curved-strip field-facet mirror (R8Kit2_facet, R11 banana strips on pedestals, R27 x1.3 + strip mounts)
             grows x FFM_GROW about the FFM landing (landing point unchanged, beam legs unchanged);
           * its strips get a satin coating (roughness FACET_ROUGH, base 0.72) so the highlight is a soft sheen, not a
             blown white slab; a dark base plate (FFM_PLATE) goes behind the strips (the 「底板」);
           * from frame CAM_F0 on, the camera target is raised toward the FFM (CAM_UP m) and the camera pulled back
             CAM_BACK m along its view line, so the FFM sits in the upper-middle of the frame at >= 1/4 while the IF
             and the pupil facet mirror (both ends of the path) stay in frame.
  WIN_R29  (C_03) R28 p2 「第 2 帧照明箱的窗太小，场分面镜不够主角…照明箱窗口放大到半屏，或者推进进窗」: see _c03().
Remove a shot from R29_SCENE -> R28 pixels; a switch False -> that item's R28 pixels.
"""
import os

import bpy
from mathutils import Matrix, Vector

FFM_R29 = True
WIN_R29 = True

_E = os.environ
WIN_FRAME = 222
WIN_DIST = float(_E.get("R29_WIN_DIST", "1.7"))
FFM_W = float(_E.get("R29_FFM_W", "1.3"))
FFM_H = float(_E.get("R29_FFM_H", "1.0"))
FFM_TURN = float(_E.get("R29_FFM_TURN", "0.6"))
FACET_ROUGH = float(_E.get("R29_FACET_ROUGH", "0.25"))
FACET_METAL = float(_E.get("R29_FACET_METAL", "0.8"))
FACET_ENV = _E.get("R29_FACET_ENV", "1") == "1"
CAM_F0 = int(_E.get("R29_CAM_F0", "40"))
CAM_UP = float(_E.get("R29_CAM_UP", "0.0"))


def pre(variant, shot, mod):
    return None


def _fcs(ob):
    ad = ob.animation_data
    if not ad or not ad.action:
        return []
    act = ad.action
    if getattr(act, "fcurves", None) is not None:
        return list(act.fcurves)
    out = []
    for lay in getattr(act, "layers", []):
        for st in lay.strips:
            for cb in st.channelbags:
                out += list(cb.fcurves)
    return out


def _offset_keys(ob, delta, f0):
    """add delta (world vector) to the location keys at frames >= f0 (ramped in over the first 12 frames after f0)."""
    for fc in _fcs(ob):
        if fc.data_path != "location":
            continue
        for kp in fc.keyframe_points:
            f = kp.co[0]
            if f < f0:
                continue
            w = min(1.0, (f - f0) / 12.0) if f < f0 + 12 else 1.0
            kp.co[1] += delta[fc.array_index] * w
            kp.handle_left[1] += delta[fc.array_index] * w
            kp.handle_right[1] += delta[fc.array_index] * w
        fc.update()


def _arc_strip(mb, c, u, v, n, R, span, width, thick, tilt):
    """one banana-shaped facet: an arc of radius R (bowing along v) centred at c in the (u, v) plane, width across the
    arc, thickness along n, rotated by `tilt` rad about its chord (u)."""
    import math
    from mathutils import Quaternion
    q = Quaternion(u, tilt)
    v2, n2 = q @ v, q @ n
    seg = 14
    rows = []
    for i in range(seg + 1):
        t = -span / 2 + span * i / seg
        p = c + u * (R * math.sin(t)) + v2 * (R * (1 - math.cos(t)) - R * (1 - math.cos(span / 2)) / 2)
        rad = (u * math.sin(t) - v2 * math.cos(t)).normalized()       # in-plane direction across the strip
        rows.append([p + rad * (sw * width / 2) + n2 * (sn * thick) for sw in (-1, 1) for sn in (0, 1)])
    V = mb.bm.verts.new
    vv = [[V(x) for x in r] for r in rows]
    F = mb.bm.faces.new
    for i in range(seg):
        a, b = vv[i], vv[i + 1]
        for (p0, p1) in ((1, 3), (0, 2), (0, 1), (2, 3)):           # top, bottom, the two long sides
            F((a[p0], a[p1], b[p1], b[p0]))
    F((vv[0][0], vv[0][1], vv[0][3], vv[0][2]))
    F((vv[-1][0], vv[-1][2], vv[-1][3], vv[-1][1]))
    return [rows[1][1], rows[-2][1]]                                   # mount positions (near both ends)


def _b501(sc):
    import math
    import random
    import build_cutaway_r2 as B
    import kit_r2 as K
    piv = Vector(B.FFM)
    hid = []
    for nm in ("R8Kit2_facet", "B5R27FacetMounts"):
        ob = bpy.data.objects.get(nm)
        if ob is not None:
            ob.hide_render = True
            hid.append(nm)
    sc.frame_set(64)
    to_cam = (sc.camera.matrix_world.translation - piv).normalized()
    n0 = ((Vector(B.IF) - piv).normalized() + (Vector(B.PFM) - piv).normalized()).normalized()
    n = (n0 + to_cam * FFM_TURN).normalized()
    u = Vector((0, 0, 1)).cross(n).normalized()
    v = n.cross(u).normalized()
    W, H = FFM_W, FFM_H
    rnd = random.Random(29)
    plate, strips, mounts = K.MB(), K.MB(), K.MB()
    thick_plate, lift, thick = 0.035, 0.03, 0.014
    base_c = piv - n * (lift + thick)                         # strip top faces pass through the FFM landing
    M = Matrix((u, v, n)).transposed().to_4x4()
    plate.box(tuple(base_c - n * thick_plate / 2), (W * 1.06, H * 1.08, thick_plate), rot=M.to_euler())
    cols, rows = 4, 11
    cw, rh = W / cols, H / rows
    for ci in range(cols):
        for ri in range(rows):
            c = base_c + u * (-W / 2 + cw * (ci + 0.5)) + v * (-H / 2 + rh * (ri + 0.5)) + n * lift
            ends = _arc_strip(strips, c, u, v, n, R=cw * 1.35, span=math.radians(38), width=rh * 0.62, thick=thick,
                              tilt=math.radians(rnd.uniform(-4, 4)))
            for e in ends:
                mounts.cyl(tuple(e - n * (lift / 2 + 0.004)), rh * 0.16, lift + 0.008,
                           rot=Vector((0, 0, 1)).rotation_difference(n).to_euler(), seg=10)
    plate.obj("B5R29FacetPlate", K.mat("B5R29FacetPlateM", (0.09, 0.095, 0.11), metal=0.7, rough=0.42), bevel=0.004)
    strips.obj("B5R29FacetStrips", K.mat("B5R29FacetCoat", (0.84, 0.84, 0.88), metal=FACET_METAL, rough=FACET_ROUGH))
    mounts.obj("B5R29FacetMounts", K.mat("B5R29FacetMountM", (0.30, 0.31, 0.34), metal=0.9, rough=0.3))
    if FACET_ENV:
        # soft reflection env only the facets see (glossy rays starting inside the sphere; tin_r29 machinery):
        # a soft cool sky above the facets' mirror direction + one soft key -> every strip a soft sheen, none blown
        import source_r25_tin as T25
        import tin_r29 as TR
        md = (-to_cam) - 2 * (-to_cam).dot(n) * n
        up = Vector((0, 0, 1))
        bands = [(tuple((md + up * 0.5).normalized()), 1.0, 0.55, 1.0, TR.COOL),
                 (tuple((md + up * 0.1).normalized()), 1.0, 0.10, 1.8, TR.WHITE),
                 (tuple(to_cam), 1.0, 0.6, 0.35, TR.COOL)]
        T25.env_r25("B5R29FacetEnv", tuple(piv), max(W, H) * 0.75, bands, base=(0.04, 0.042, 0.05))
    print(f"[r29s] B5_01 FFM plate {W}x{H} turn {FFM_TURN} n.to_cam {n.dot(to_cam):.2f} (bisector {n0.dot(to_cam):.2f}) "
          f"{cols}x{rows} arc strips rough {FACET_ROUGH}; hidden {hid}; IF/PFM side dots "
          f"{n.dot((Vector(B.IF) - piv).normalized()):.2f} / {n.dot((Vector(B.PFM) - piv).normalized()):.2f}", flush=True)
    cam, tgt = sc.camera, None
    for c_ in cam.constraints:
        if getattr(c_, "target", None) is not None and not c_.mute:
            tgt = c_.target
    if tgt is not None and CAM_UP:
        _offset_keys(tgt, Vector((0, 0, CAM_UP)), CAM_F0)


def _set_key(ob, frame, value):
    """move the location key at `frame` to `value` (auto-clamped handles so the path eases in / out)."""
    hit = 0
    for fc in _fcs(ob):
        if fc.data_path != "location":
            continue
        for kp in fc.keyframe_points:
            if abs(kp.co[0] - frame) < 0.5:
                kp.co[1] = value[fc.array_index]
                kp.handle_left_type = kp.handle_right_type = "AUTO_CLAMPED"
                hit += 1
        fc.update()
    return hit


def _c03(sc):
    """f222 (the 55 % key of the long take): the camera moves in to WIN_DIST m in front of the illuminator window
    (centred on it), so the window + the field-facet landing behind it fill about half the frame; the keys before /
    after are untouched (push in, then the take continues to the mask)."""
    import c03_r28 as C
    (x0, x1), (z0, z1) = C.WIN
    wc = Vector(((x0 + x1) / 2, C.Y0, (z0 + z1) / 2))
    cam, tgt = sc.camera, None
    for c_ in cam.constraints:
        if getattr(c_, "target", None) is not None and not c_.mute:
            tgt = c_.target
    sc.frame_set(WIN_FRAME)
    d = (cam.matrix_world.translation - wc).normalized()
    newc = wc + d * WIN_DIST
    hc = _set_key(cam, WIN_FRAME, newc)
    ht = _set_key(tgt, WIN_FRAME, wc + Vector((0.0, 1.0, 0.05))) if tgt is not None else 0
    print(f"[r29s] C_03 WIN f{WIN_FRAME} camera -> {tuple(round(v, 2) for v in newc)} ({WIN_DIST} m from the window "
          f"centre {tuple(round(v, 2) for v in wc)}), keys moved cam {hc} tgt {ht}", flush=True)


def post(sc, variant, shot):
    if shot == "B5_01" and FFM_R29:
        _b501(sc)
    if shot == "C_03" and WIN_R29:
        _c03(sc)
    sc.frame_set(1)
    return sc
