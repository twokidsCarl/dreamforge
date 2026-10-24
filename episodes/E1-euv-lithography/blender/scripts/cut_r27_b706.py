"""R27 cut B7_06 helper (called from cut_r27; runs after cut_hero_r25 = R24 solid ring mirrors + R25 shell chain).

ONETURN_R27 (row 3): R26 review 「入射光带是带横档的扁平条，像梯子 / 线框…②→③ 的会聚光太淡，几乎看不出穿孔」 ->
  the R24/R25 chain (PO24Beam*, beam_r25 thin-shell legs) is rebuilt as ONE beam_r26 soft-shell chain on the same stops at
  alpha ALPHA (the R26 0.45 shell let the tower struts show through = the 「梯子」 read)
  (roof port -> M5 ring -> M6 -> through the M5 hole -> wafer point; same reveal keys), and the converging M6 -> wafer leg
  gets CONV_GAIN x the emission (alpha CONV_ALPHA) so ③ reads as a bright cone collapsing into the wafer point.
KIT_R27 (row 4): 「箱内加入可叫名字的零件：hexapod 镜座支脚、计量环、干涉仪头、波纹管」 -> kit_r27.named_row of big different
  parts on the tower back wall between M5 and M6 (turntable frame, parented to the turntable).
"""
import math

import bpy
from mathutils import Vector

FRAMES = (36, 79, 122)
STRENGTH, CONV_GAIN, ALPHA, CONV_ALPHA = 2.4, 2.0, 0.75, 0.9
KINDS = ("viewport_stack", "metrology_ring", "hexapod_mount", "bellows_spool")   # the four the R26 review names (viewport_stack = interferometer head); 8-spp: 6 kinds were ~32 px each; leftmost slot sits behind the incoming leg
ROW = dict(x0=-0.8, x1=0.8, z0=1.9, z1=2.45, y0=0.4, scale=1.4)


def pre(mod, oneturn, kit):
    pass


def _rebuild(sc, piv):
    import beam_r26 as BR
    import cut_hero_r25_b706 as H25
    ch = H25.CH.get("ch")
    if ch is None:
        print("[r27c b706] no R25 chain", flush=True)
        return None
    for o in [o for o in bpy.data.objects if o.name.startswith("PO24Beam")]:
        bpy.data.objects.remove(o)
    face = bpy.data.objects.get("PO24_mface")
    ex = {1: face, 2: face} if face is not None else {}
    stops = [(Vector(p), None if n is None else Vector(n)) for p, n in ch["stops"]]
    import cut_hero_r24_b706 as H24
    nch = BR.chain("PO27Beam", stops, list(H24.RADII), strength=STRENGTH, alpha=ALPHA, spot_strength=18.0, spot_scale=1.6,
                   existing=ex)
    for o in [o for leg in nch["legs"] for o in leg] + [s for s in nch["spots"] if s is not None]:
        o.parent = piv
    # converging leg (M6 -> wafer) brighter: scale its emission-strength multiplier
    for o in nch["legs"][-1]:
        for m in o.data.materials:
            for nd in m.node_tree.nodes:
                if nd.type == "MATH" and nd.operation == "MULTIPLY" and abs(nd.inputs[1].default_value - STRENGTH) < 1e-6 \
                        and any(l.to_node.type == "EMISSION" for l in nd.outputs[0].links):
                    nd.inputs[1].default_value = STRENGTH * CONV_GAIN
                if nd.type == "MATH" and nd.operation == "MULTIPLY" and abs(nd.inputs[1].default_value - ALPHA) < 1e-6 \
                        and any(l.to_node.type == "MATH" and l.to_node.operation == "MINIMUM" for l in nd.outputs[0].links):
                    nd.inputs[1].default_value = CONV_ALPHA
    n = sc.frame_end
    BR.key_chain(nch, [1, round(1 + (n - 1) * 0.42), round(1 + (n - 1) * 0.70)])
    return nch


def _check(sc, piv, ch):
    import beam_r26 as BR
    f0 = sc.frame_current
    rx = (sc.render.resolution_x, sc.render.resolution_y)
    sc.render.resolution_x, sc.render.resolution_y = 960, 540
    import cut_hero_r24_b706 as H24
    for f in FRAMES:
        sc.frame_set(f)
        Mw = piv.matrix_world
        R = Mw.to_3x3()
        st = [(Mw @ Vector(p), None if nn is None else (R @ Vector(nn)).normalized()) for p, nn in ch["stops"]]
        BR.check(sc, {"stops": st, "radii": ch["radii"], "leg_radii": ch["leg_radii"], "mirrors": ch["mirrors"],
                      "legs": ch["legs"]}, [f], exits=(0,), tag="B7_06", mirror_stops=[1, 2])
        cam = sc.camera.matrix_world.translation
        for nm, c, nn in (("M5", st[1][0], st[1][1]), ("M6", st[2][0], st[2][1])):
            print(f"[r27c b706] f{f} {nm} n.to_cam {nn.dot((cam - c).normalized()):.2f}", flush=True)
    sc.render.resolution_x, sc.render.resolution_y = rx
    sc.frame_set(f0)


def _kit(piv):
    import hero_kit_r10 as H
    import kit_r27 as KR
    P = H.new_parts()
    kinds = KR.named_row(P, ROW["x0"], ROW["x1"], ROW["z0"], ROW["z1"], ROW["y0"], kinds=KINDS, seed=706, scale=ROW["scale"],
                         depth=1.6)
    obs = KR.finish(P, "B706KitR27") or []
    for o in (obs if isinstance(obs, (list, tuple)) else []):
        o.parent = piv
    for o in bpy.data.objects:
        if o.name.startswith("B706KitR27"):
            if o.parent is None:
                o.parent = piv
            o.visible_glossy = False     # 8-spp: M5 (tilted to the camera) mirrored the parts = "objects lying on M5"
    print(f"[r27c b706] KIT {KR.count(kinds)} kinds", flush=True)


def post(sc, oneturn, kit):
    piv = bpy.data.objects.get("Turntable")
    if kit:
        _kit(piv)
    if oneturn:
        ch = _rebuild(sc, piv)
        if ch is not None:
            _check(sc, piv, ch)
