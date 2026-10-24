"""Round 31 hook (MAIN process; r2_misc.R31_MAIN = {"B4_10"}), layered after the R30 / R31 agent hooks, before
beam_hook_r29.

  LAND_R31 (row 6f, B4_10 light path): R30 p3 「激光在太空里是硬白线…给它在月面落点处加一个小光斑和少量散射，让『落在球上』
           可见」. The R22 landing caps (SpotHaloR22 14 deg / SpotHotR22 5 deg) are white on a white ball and invisible; the
           R22 scatter light is 0.02 W. R31: the halo cap widens to HALO_DEG and turns a cool blue-white, the hot core a
           little wider, and the scatter light at the hit goes to SCATTER_W so the ball's top and the regolith right
           round it catch the laser (the spot sits ON the ball - spherical caps, never a floating ball).
Remove B4_10 from R31_MAIN -> R30 pixels.
"""
import bpy
from mathutils import Vector

LAND_R31 = True
HALO_DEG, HOT_DEG = 26, 11
HALO_COL = (0.55, 0.78, 1.0)
SCATTER_W = 1.1


def pre(variant, shot, mod):
    return None


def post(sc, variant, shot):
    if not (LAND_R31 and shot == "B4_10"):
        return sc
    import kit_r2 as K
    import misc_kit_r16 as MK
    ball = bpy.data.objects.get("GolfBall")
    halo, hot, pl = (bpy.data.objects.get(n) for n in ("SpotHaloR22", "SpotHotR22", "SpotLightR22"))
    if ball is None or halo is None or hot is None:
        print("[misc_main_r31] B4_10: ball / spots missing", flush=True)
        return sc
    bb = [ball.matrix_world @ Vector(c) for c in ball.bound_box]
    b = sum(bb, Vector()) / 8
    rb = max(ball.dimensions) / 2
    top = max((halo.matrix_world @ v.co for v in halo.data.vertices), key=lambda w: (w - b).length)
    hit_dir = (sum((halo.matrix_world @ v.co for v in halo.data.vertices), Vector()) / len(halo.data.vertices) - b).normalized()
    for o in (halo, hot):
        bpy.data.objects.remove(o, do_unlink=True)
    MK.spot_cap("SpotHaloR31", b, rb * 1.035, hit_dir, HALO_DEG, K.emit_mat("SpotHaloR31M", HALO_COL, 3.2, halo=0.6))
    MK.spot_cap("SpotHotR31", b, rb * 1.04, hit_dir, HOT_DEG, K.emit_mat("SpotHotR31M", (0.80, 0.90, 1.0), 9.0, halo=0.8))
    if pl is not None:
        pl.data.energy = SCATTER_W
        pl.location = pl.location + hit_dir * 0.025      # 8 spp: at 6 mm off the cap the light blew the cap into black / orange specks
        pl.data.shadow_soft_size = 0.012
        pl.visible_camera = False
        pl.visible_glossy = True
    print(f"[misc_main_r31] B4_10 landing caps {HALO_DEG} / {HOT_DEG} deg, scatter {SCATTER_W} W at "
          f"{tuple(round(x, 3) for x in top)}", flush=True)
    return sc
