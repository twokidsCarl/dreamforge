"""Round 24 hook (owned by the 'tin' sub-agent; shots in r2_source.R24_TIN). R24_ROOT_CAUSE row 2 (tin shared asset).

  A0_01 / B1_10  pre(): source_r21.pancake_r21 -> source_r24_tin.pancake_r24 (ultra-thin film + ring of separate
                 droplets; overrides the R23 swap for B1_10 because the R24 pre runs after the R23 pre).
  all three      post(): every liquid-tin object gets the OPAQUE liquid-metal material (metallic 1, rough 0.10, no
                 transmission / ripple bump); the older tin reflection rigs (R18 band domes, R22 droplet domes +
                 rim lights = the bright ring that made the droplet read as a glass marble, R23 sheet env) are taken
                 off the tin and replaced by one dark-chamber env per tin part with a single crisp key highlight.
  B1_10          sheet turned SHEET_YAW about Z so its face turns toward the laser side (more edge-on to camera) +
                 small orange afterglow arc on the laser-facing edge.
Remove a shot from r2_source.R24_TIN -> exact R23 pixels.
"""
import math

import bpy
from mathutils import Vector

PANCAKE_SHOTS = {"A0_01", "B1_10"}
SHEET_YAW = {"B1_10": -14.0}
ENV_FRAME = {"A0_01": (72, 160), "B1_10": (69, 69), "B1_08": (51, 51)}   # (droplet frame, sheet frame)
SHEET_REAL_CHAMBER = True
SHEET_KEY = {}       # light-linked soft key at the sheet face's mirror direction (W)
DROP_SKY = 0.6     # chrome-ball read: lit overhead half -> dark chamber below + one crisp key
DROP_GONE = {"A0_01": 94, "B1_10": 32}
SHEET_ENV_R = {"A0_01": 0.27, "B1_10": 0.27}


def pre(variant, shot, mod):
    if shot in PANCAKE_SHOTS:
        import source_r21 as S21
        import source_r24_tin as T
        S21.pancake_r21 = T.pancake_r24


def _const(ob):
    ad = ob.animation_data
    if not (ad and ad.action):
        return
    try:
        fcs = list(ad.action.fcurves)
    except AttributeError:
        fcs = [fc for lay in ad.action.layers for st in lay.strips for cb in st.channelbags for fc in cb.fcurves]
    for fc in fcs:
        for kp in fc.keyframe_points:
            kp.interpolation = "CONSTANT"


def _ob(n):
    return bpy.data.objects.get(n)


def _cam_dirs(sc, f, p):
    sc.frame_set(f)
    cam = sc.camera
    mw = cam.matrix_world
    cpos = mw.translation.copy()
    to_cam = (cpos - Vector(p)).normalized()
    right = (mw.to_3x3() @ Vector((1, 0, 0))).normalized()
    up = Vector((0, 0, 1))
    return to_cam, right, up


def _key(to_cam, right, up):
    return (to_cam + up * 1.0 - right * 0.5).normalized()       # upper-left highlight on the tin as seen on screen


def post(sc, variant, shot):
    import source_r24_tin as T
    tin = [o for o in bpy.data.objects if o.type == "MESH" and o.active_material is not None
           and o.active_material.name.startswith("LiquidTin")]
    m = T.tin_mat_r24()
    for o in tin:
        o.data.materials.clear()
        o.data.materials.append(m)
    # old reflection rigs off: R22 domes / rim lights, R23 sheet env (R18 domes: tin unlinked inside env_r24)
    for o in list(bpy.data.objects):
        if o.name.startswith(("TinEnvR18", "TinEnvR22", "TinSheetEnvR23", "TinRimR22")):   # tin-only rigs (an emptied R18 receiver set would light the whole chamber)
            bpy.data.objects.remove(o, do_unlink=True)
    f_drop, f_sheet = ENV_FRAME[shot]
    if shot in PANCAKE_SHOTS:
        root = _ob("PancakeRoot")
        if shot in SHEET_YAW and root is not None:
            root.rotation_euler = (0, 0, math.radians(SHEET_YAW[shot]))
        parts = [o for o in (_ob("Pancake"), _ob("PancakeDrops")) if o]
        if parts:
            tc, rt, up = _cam_dirs(sc, f_sheet, (0, 0, 0))
            nrm = Vector((-1, 0, 0))
            if shot in SHEET_YAW:
                a = math.radians(SHEET_YAW[shot])
                nrm = Vector((-math.cos(a), -math.sin(a), 0))
            if nrm.dot(tc) < 0:
                nrm = -nrm
            v = -tc
            mdir = v - 2 * v.dot(nrm) * nrm
            import os
            if SHEET_REAL_CHAMBER or os.environ.get("R24_NOSHEETENV"):   # sheet mirrors the real dark chamber
                pass
            else:
              T.env_r24("TinSheetEnvR24", (0, 0, 0), SHEET_ENV_R[shot], tin, _key(tc, rt, up), mirror_dir=mdir, sky=0.45)
            if shot in SHEET_KEY:      # one soft structured highlight on the face (round light: no square card)
                import kit_r2 as K
                kd = (mdir + Vector((0, 0, 0.18)) + rt * 0.08).normalized()
                li = K.point("TinSheetKeyR24", tuple(kd * 0.32), SHEET_KEY[shot], (0.9, 0.93, 1.0), 0.045)
                li.visible_camera = False if hasattr(li, "visible_camera") else None
                col = bpy.data.collections.new("TinSheetKeyR24_Recv")
                for o_ in parts:
                    col.objects.link(o_)
                li.light_linking.receiver_collection = col
        if shot == "B1_10" and root is not None:
            g = T.afterglow_r24(root, math.radians(-60), math.radians(60), 6.0)
            mat = g.active_material
            em = next(n for n in mat.node_tree.nodes if n.type == "EMISSION")
            for f, s in ((32, 0.0), (34, 8.0), (69, 3.0), (126, 1.0)):
                em.inputs["Strength"].default_value = s
                em.inputs["Strength"].keyframe_insert("default_value", frame=f)
    drops = [o for o in tin if o.name in ("Droplet", "DropletNext") or (o.name.startswith("Drop") and o.name[4:].isdigit())]
    for d in drops:
        p = d.matrix_world.translation
        tc, rt, up = _cam_dirs(sc, f_drop, p)
        e = T.env_r24("TinEnvR24_" + d.name, (0, 0, 0), 0.05, tin, _key(tc, rt, up), parent=d, sky=DROP_SKY, key=9.0)
        if d.name == "Droplet" and shot in DROP_GONE:     # env must go with the droplet (else: dark disc on the sheet)
            for f, s_ in ((DROP_GONE[shot], 1.0), (DROP_GONE[shot] + 1, 0.001)):
                e.scale = (s_, s_, s_)
                e.keyframe_insert("scale", frame=f)
            _const(e)
    sc.frame_set(1)
