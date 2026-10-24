"""Round 30 hook (MAIN process; shots in r2_source.R30_TIN = A0_01 / B1_10). Layered after source_r29 (tin_r29 reflection
recipe stays as it is) and before beam_hook_r29.

  SHAPE_R30 (row 3, A0_01 / B1_10): tin step 4 = liquid SHAPE - tin_r30.shape() reshapes the sheet mesh in place
            (irregular outline, crown lip with finger tips curling away from the camera, molten swells instead of one flat
            mirror, translucent thin rim, detached droplets). R29 p1: 「边缘不规则、带溅射卷边和细碎飞沫…不要整片镜面反射」.
  LASER_R30 (row 3b, A0_01): the main pulse 「一根等宽、实心、发灰的光柱」 -> a beam_r29 volume cone (orange, centre-bright,
            soft) converging 4.5:1 onto the sheet + a bright landing spot on the sheet; same visibility keys as the pulse.
Remove a shot from R30_TIN -> R29 pixels; a switch False -> that row's R29 pixels.
"""
import bpy
from mathutils import Vector

SHAPE_R30 = True
LASER_R30 = True

SHEET_FRAME = {"A0_01": 160, "B1_10": 69}
ORANGE = (1.0, 0.55, 0.18)


def pre(variant, shot, mod):
    return None


def _copy_hide_keys(src, dst):
    import beam_r29 as B29
    ad = src.animation_data
    n = 0
    if ad and ad.action:
        for fc in B29._fcurves(ad.action):
            if fc.data_path == "hide_render":
                for kp in fc.keyframe_points:
                    dst.hide_render = bool(kp.co[1] > 0.5)
                    dst.keyframe_insert("hide_render", frame=kp.co[0])
                    n += 1
    if n == 0:
        dst.hide_render = src.hide_render
    return n


def _laser(sc, shot):
    import beam_r29 as B29
    import beam_r30 as B30
    mp = bpy.data.objects.get("MainPulse")
    if mp is None:
        print(f"[source_r30] {shot}: no MainPulse", flush=True)
        return
    xs = [v.co.x for v in mp.data.vertices]
    rs = [abs(v.co.y) for v in mp.data.vertices]
    x0, x1, r = min(xs), max(xs), max(rs)
    x0 = x0 - 2.0 * (x1 - x0)        # wide end well off screen (R29 / R30 8 spp: a visible end cap = 「实心光柱」)
    cone = B29.cone("MainPulseR30", (x0, 0, 0), (x1, 0, 0), r * 1.6, r * 1.6 / 4.5, color=ORANGE, strength=0.3,
                    parent=mp)
    nk = _copy_hide_keys(mp, cone)
    B29._hide_all(mp)
    sp = B30._slit_line(cone, (r * 0.55, r * 0.55), True, (1.0, 0.75, 0.45),
                        tuple(mp.matrix_world.to_3x3() @ Vector((-1, 0, 0))))
    _copy_hide_keys(mp, sp)
    print(f"[source_r30] {shot} main pulse -> volume cone {r * 1.6:.3f} -> {r * 1.6 / 4.5:.3f} over {x1 - x0:.2f}, "
          f"landing spot, {nk} visibility keys", flush=True)


def post(sc, variant, shot):
    if SHAPE_R30 and shot in SHEET_FRAME:
        import tin_r30
        tin_r30.shape(sc, shot, SHEET_FRAME[shot])
    if LASER_R30 and shot == "A0_01":
        _laser(sc, shot)
    sc.frame_set(1)
    return sc
