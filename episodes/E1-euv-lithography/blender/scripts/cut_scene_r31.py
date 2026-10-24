"""Round 31 scene hook (MAIN process; r2_cutaway.R31_SCENE), layered after the R30 hooks and before beam_hook_r29.

  B706_R31 (row 4, B7_06 - scene-level path, R29 / R30 returned): R30 p2 「三帧里光都是等宽的噪点细管，M6→晶圆应该是会聚锥
           却画成直柱；①帧入射光看起来从 M6 位置旁边穿过，像穿过 M6」「光改成锥形：M5→M6 发散、M6→晶圆会聚到一点…①帧入射光从
           M6 外缘绕过的路径交代清楚」. R29 / R30 kept the R24 stops (M6 landing 0.15 m off axis, narrow M5 -> M6 leg) and only
           changed cone radii -> with the whole path shown every frame the three legs crossed between M5 and M6.
           R31 changes the STOPS (turntable frame): the roof port moves out to x = PORT_X so the incoming leg passes clear
           of the M6 rim; the M6 landing moves onto the axis and the M5 -> M6 leg OPENS to the M6 aperture (R_AP) - the
           M6 -> wafer leg CLOSES from that same aperture through the M5 hole onto the wafer point. The two cones share
           the M6 face as their base (one diamond), so no leg crosses another. Chain name stays PO27Beam so
           beam_hook_r29 (LAST) converts it and keeps the WINDOWS levels (current leg 1.0, others 0.6, whole path every
           frame).
Remove B7_06 from R31_SCENE (and R31_BEAM) -> R30 pixels.
"""
import bpy
from mathutils import Vector

B706_R31 = True
PORT_X = -1.08
R_AP = 0.36            # M6 aperture lit by the diverging leg = base of the converging leg (M5 hole 0.11 passes at 0.108)
RADII = [0.06, 0.045, R_AP, 0.008]


STRENGTH = 4.0          # beam_r29 centre radiance for B7_06 (default 1.6: the wide R_AP cones are dim by B (R0 / R)^GAMMA)


def pre(variant, shot, mod):
    if B706_R31 and shot == "B7_06":
        import beam_hook_r29 as H29
        H29.STRENGTH[shot] = STRENGTH


def _b706(sc):
    import beam_r26 as BR
    import cut_hero_r24_b706 as H24
    import cut_hero_r25_b706 as H25
    ch = H25.CH.get("ch")
    piv = bpy.data.objects.get("Turntable")
    if ch is None:
        print("[cut_scene_r31] B7_06: no R25 chain", flush=True)
        return
    for o in [o for o in bpy.data.objects if o.name.startswith(("PO27Beam", "PO24Beam"))]:
        bpy.data.objects.remove(o, do_unlink=True)
    (src0, _), (p5, n5), (p6, n6), (foc, nf) = [(Vector(p), None if n is None else Vector(n)) for p, n in ch["stops"]]
    port = Vector((PORT_X, 0.0, H24.Z_CEIL))
    src = port + (port - p5).normalized() * 1.25
    p6n = Vector((0.0, p6.y, p6.z))
    face = bpy.data.objects.get("PO24_mface")
    ex = {1: face, 2: face} if face is not None else {}
    nch = BR.chain("PO27Beam", [(src, None), (p5, n5), (p6n, n6), (foc, nf)], RADII, strength=2.4, alpha=0.75,
                   spot_strength=10.0, spot_scale=0.8, existing=ex)
    for o in [o for leg in nch["legs"] for o in leg] + [s for s in nch["spots"] if s is not None]:
        o.parent = piv
    for nm, loc in (("Anchor_m6r", p6n),):
        e_ = bpy.data.objects.get(nm)
        if e_ is not None:
            e_.location = loc
    print(f"[cut_scene_r31] B7_06 stops port x {PORT_X}, M6 landing on axis, legs {RADII}", flush=True)


def post(sc, variant, shot):
    if B706_R31 and shot == "B7_06":
        _b706(sc)
    return sc
