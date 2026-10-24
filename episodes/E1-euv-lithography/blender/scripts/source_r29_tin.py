"""Round 29 tin-agent helper (R29_ROOT_CAUSE row 2, material tin step 3). Used only by source_r29.py.

  splash(sc, shot)   SPLASH_R29 (A0_01 / B1_10): R28 p1 「边缘挂满小球，读起来像气泡或铆钉…飞溅只留在背光侧的 3–5 颗，并拉成
                     拉丝状」. Hides every rim bead / satellite rig (source_r28_tin.breakup PancakeLigR28 = ligaments with
                     beads + detached drops, PancakeDrops = random satellites; any older *Sat* / *Bead* child of
                     PancakeRoot) and adds 4 thin TAPERED, CURVED liquid ligaments torn off the rim on the BACK-LIT side
                     (the in-plane side facing the cool rim light from behind, away from camera / laser), bending
                     backwards out of the sheet plane (away from the camera). No bead on any tip (R17-R19 pin-heads),
                     no straight needle (R21): every thread is a 5-segment bent tube, radius 0.05 -> 0.02, length 0.44-0.70 (sheet units).
                     Silver = the tin_r29 material of the sheet, so they catch the tin_r29 grazing rims.
"""
import math

import bpy
from mathutils import Vector

import kit_r2 as K

N_LIG = 4
R_BASE, R_TIP = 0.05, 0.02
ARC = math.radians(70)          # spread of the 4 threads round the back-lit direction
SEG = 5
HIDE_PREFIX = ("PancakeLigR28", "PancakeDrops")
HIDE_WORDS = ("Sat", "Bead", "Satellite", "Spray")
ADD_LIG = False                   # R29 smoke: ligaments read as striped larvae + ghost ring on A0_01 -> R30 notes
LINK_RECV = True


def _ob(n):
    return bpy.data.objects.get(n)


def _hide(o):
    if o.animation_data is not None:
        o.animation_data_clear()
    o.hide_render = True
    o.hide_viewport = True


def _keys(src):
    import source_r26_tin as T26
    return sorted((kp.co[0], kp.co[1]) for fc in T26._fcs(src) if fc.data_path == "hide_render"
                  for kp in fc.keyframe_points)


def splash(sc, shot, frame):
    import source_r24 as H24
    import source_r28_tin as T28
    root = _ob("PancakeRoot")
    sh = _ob("Pancake")
    if root is None or sh is None:
        print(f"[source_r29_tin] {shot}: no PancakeRoot", flush=True)
        return
    kids = [o.name for o in bpy.data.objects if o.parent is root]
    print(f"[source_r29_tin] {shot} PancakeRoot children: {kids}", flush=True)
    keysrc = _ob("PancakeDrops") or _ob("PancakeLigR28")
    keys = _keys(keysrc) if keysrc is not None else []
    if not keys:
        keys = _keys(sh) or _keys(root)
    hidden = []
    for o in list(bpy.data.objects):
        if o.name.startswith(HIDE_PREFIX) or (o.parent is root and any(w in o.name for w in HIDE_WORDS)):
            _hide(o)
            hidden.append(o.name)
    if not ADD_LIG:
        print(f"[source_r29_tin] {shot} hidden={hidden} (no ligaments)", flush=True)
        return
    # back-lit direction in the sheet's local frame (sheet plane = local YZ, normal = local X)
    to_cam, rt, up = H24._cam_dirs(sc, frame, root.matrix_world.translation.copy())
    inv = root.matrix_world.to_3x3().inverted()
    back = inv @ (up * 0.6 + rt * 0.45 - to_cam)         # where the cool rim light (tin_r29 drop/sheet bands) comes from
    cam_l = (inv @ to_cam).normalized()
    a0 = math.atan2(back.z, back.y) if abs(back.y) + abs(back.z) > 1e-6 else math.pi / 3
    xs = -1.0 if cam_l.x > 0 else 1.0                       # bend away from the camera, out of the sheet plane
    mb = K.MB()
    lens = [0.48, 0.70, 0.60, 0.44]
    bends = [0.10, -0.06, 0.08, -0.11]
    for i in range(N_LIG):
        a = a0 - ARC / 2 + ARC * i / (N_LIG - 1)
        r0 = T28._rim(root, a) * 0.95
        L = lens[i]
        pts = []
        for k in range(SEG + 1):
            t = k / SEG
            ang = a + bends[i] * t * t
            rho = r0 + L * t
            pts.append(Vector((xs * 0.10 * L * t * t, rho * math.cos(ang), rho * math.sin(ang))))
        for k in range(SEG):
            ra = R_BASE + (R_TIP - R_BASE) * (k / SEG)
            rb = R_BASE + (R_TIP - R_BASE) * ((k + 1) / SEG)
            mb.tube(tuple(pts[k]), tuple(pts[k + 1]), ra, seg=12, r2=rb)
            if 0 < k:
                mb.sphere(tuple(pts[k]), ra, 10)           # smooth joints (same radius as the tube: no bead)
        mb.sphere(tuple(pts[0]), R_BASE * 1.25, 12)        # fillet into the rim
    lig = mb.obj("PancakeLigR29", sh.active_material)
    for p in lig.data.polygons:
        p.use_smooth = True
    lig.parent = root
    for f, h in keys:
        lig.hide_render = bool(h > 0.5)
        lig.keyframe_insert("hide_render", frame=int(f))
    import source_r26_tin as T26
    for fc in T26._fcs(lig):
        for kp in fc.keyframe_points:
            kp.interpolation = "CONSTANT"
    for col in (bpy.data.collections if LINK_RECV else []):
        if col.name.startswith("PancakeGlintR17_Recv") and sh.name in col.objects:
            col.objects.link(lig)
    print(f"[source_r29_tin] {shot} SPLASH_R29 hidden={hidden} a0={math.degrees(a0):.0f} xs={xs} keys={keys}",
          flush=True)


# ------------------------------------------------------------------ per-shot drop override (row 2, TIN_R29 tuning)
# A0_01 f72: with tin_r29.drop_bands the key glint (upper-left) and the warm glint (right, same height) sit side by
# side on the ball = a pair of 'eyes' (R28 「?」脸形 risk). Move the warm box down-right so the two glints form a
# diagonal (as on B1_08). Same recipe, same sources, only the warm box direction; tin_r29.py untouched.
DROP_WARM_R29 = {"A0_01": (0.85, -0.55, 0.4)}   # main process R29 (after the tin agent stopped): the agent's own fix, warm box moved down-right AND dimmed to 40 % -> one dominant key glint + a faint warm kick (8 spp f72: no "pair of eyes"); (right, up, gain)


def drop_override(sc, shot, frame):
    if shot not in DROP_WARM_R29:
        return
    import source_r23_tin as T23
    import source_r24 as H24
    import tin_r29 as T
    wr, wu, *wg = DROP_WARM_R29[shot]            # optional 3rd value: warm-box gain (main process R29: 0.4)
    n = 0
    for e in list(bpy.data.objects):
        if not e.name.startswith("TinEnvR27_") or e.parent is None:
            continue
        tc, rt, up = H24._cam_dirs(sc, frame, e.parent.matrix_world.translation.copy())
        bands = T.drop_bands(tc, rt, up)
        c, a, w, g, col = bands[2]
        bands[2] = (T._n(tc + up * wu + rt * wr), a, w, g * (wg[0] if wg else 1.0), col)
        mm = T23._env_mat_r23("TinEnvR29bMat_" + e.parent.name, bands, T.DROP_BASE, 1.0, 0.05)
        e.data.materials.clear()
        e.data.materials.append(mm)
        n += 1
    print(f"[source_r29_tin] {shot} drop_override warm=({wr},{wu}) envs={n}", flush=True)
