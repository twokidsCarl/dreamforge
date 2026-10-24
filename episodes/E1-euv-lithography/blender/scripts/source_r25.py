"""Round 25 hook (owned by the 'tin' sub-agent; shots in r2_source.R25_TIN). R25_ROOT_CAUSE row 3 (material: a LIT,
STRUCTURED environment so the opaque liquid tin reads as liquid metal, not the R24 black rubber / black glass).

  A0_01 / B1_10  base = R23 pixels (not in R24_TIN): pre() / post() first run the R24 tin hook (ultra-thin film +
                 droplet-ring edge + opaque tin), then the R25 layer below.
  all three      post(): tin = bright, slightly warm silver (metallic 1, rough 0.07); the film gets fine capillary
                 ripples (bump); every R24 dark-chamber env sphere is replaced by a STRUCTURED env (lit viewport rims,
                 two-line flange, port mouths, a port-tube streak, crisp key, dark gaps - source_r25_tin.struct_bands);
                 the sheet (R24: mirrored the real black chamber) gets its own structured env whose lit port rim +
                 flange cross the face's mirror direction.
Remove a shot from r2_source.R25_TIN -> exact R24 pixels.
"""
import math

import bpy
from mathutils import Vector

R24_BASE = {"A0_01", "B1_10"}           # not in R24_TIN -> run the R24 tin hook here
ENV_FRAME = {"A0_01": (72, 160), "B1_10": (69, 69), "B1_08": (51, 51)}
DROP_GONE = {"A0_01": 94, "B1_10": 32}
SHEET_ENV_R = {"A0_01": 0.27, "B1_10": 0.27}
DROP_GAIN = 1.0
SHEET_GAIN = {"A0_01": 1.0, "B1_10": 1.0}
CROWN = {"A0_01": (0.05, 0.010), "B1_10": (0.05, 0.010)}      # shot -> (CUP, HE): edge flares back from the laser + slightly thicker lip (crown-like thin rim)
FILM_ROUGH = None
RIPPLE = {"A0_01": 0.06, "B1_10": 0.06}


def pre(variant, shot, mod):
    if shot in R24_BASE:
        import source_r24 as H24
        H24.pre(variant, shot, mod)
        if shot in CROWN:
            import source_r24_tin as T24
            T24.CUP, T24.HE = CROWN[shot]


def _ob(n):
    return bpy.data.objects.get(n)


def post(sc, variant, shot):
    import source_r24 as H24
    import source_r25_tin as T
    if shot in R24_BASE:
        H24.post(sc, variant, shot)
    for o in list(bpy.data.objects):          # R24 dark-chamber envs out (= the black reflection)
        if o.name.startswith(("TinEnvR24", "TinSheetEnvR24")):
            bpy.data.objects.remove(o, do_unlink=True)
    tin = [o for o in bpy.data.objects if o.type == "MESH" and o.active_material is not None
           and o.active_material.name.startswith(("LiquidTin", "TinMetalR24"))]
    m = T.tin_mat_r25()
    for o in tin:
        o.data.materials.clear()
        o.data.materials.append(m)
    f_drop, f_sheet = ENV_FRAME[shot]
    root = _ob("PancakeRoot")
    if shot in R24_BASE and root is not None:
        sheet = _ob("Pancake")
        if sheet is not None:
            sheet.data.materials.clear()
            sheet.data.materials.append(T.film_mat_r25(ripple=RIPPLE[shot]))
        g = _ob("TinAfterglowR24")
        if g is not None:            # the rippled face must not smear the afterglow arc across itself
            g.visible_glossy = False
        tc, rt, up = H24._cam_dirs(sc, f_sheet, (0, 0, 0))
        nrm = Vector((-1, 0, 0))
        if shot in H24.SHEET_YAW:
            a = math.radians(H24.SHEET_YAW[shot])
            nrm = Vector((-math.cos(a), -math.sin(a), 0))
        if nrm.dot(tc) < 0:
            nrm = -nrm
        v = -tc
        mdir = v - 2 * v.dot(nrm) * nrm
        T.env_r25("TinSheetEnvR25", (0, 0, 0), SHEET_ENV_R[shot],
                  T.struct_bands(tc, rt, up, mirror_dir=mdir, gain=SHEET_GAIN[shot], key=6.0))
    drops = [o for o in tin if o.name in ("Droplet", "DropletNext") or (o.name.startswith("Drop") and o.name[4:].isdigit())]
    for d in drops:
        p = d.matrix_world.translation.copy()
        tc, rt, up = H24._cam_dirs(sc, f_drop, p)
        e = T.env_r25("TinEnvR25_" + d.name, (0, 0, 0), 0.05, T.struct_bands(tc, rt, up, gain=DROP_GAIN), parent=d)
        if d.name == "Droplet" and shot in DROP_GONE:
            for f, s_ in ((DROP_GONE[shot], 1.0), (DROP_GONE[shot] + 1, 0.001)):
                e.scale = (s_, s_, s_)
                e.keyframe_insert("scale", frame=f)
            H24._const(e)
    sc.frame_set(1)
