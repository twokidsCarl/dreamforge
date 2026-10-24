"""R25 chero B3_02 (R25_ROOT_CAUSE row 5 + row 2). Runs after cut_hero_r24_b302.post (enlarged R 1.25 m dish, sketch
camera, beam_r25 rim -> IF shell cone built through the patched beam_r24.chain).

R24 self-flagged risk: laser + cone reflections lay on the dish face. Here:
  * every beam object (cone legs, IF pinch / glow, laser core + halo) gets visible_glossy = False -> the dish face
    mirrors only the chamber walls and the violet plasma glow;
  * the CO2 laser is rebuilt: it enters from a back port tube behind the dish's centre hole, passes the hole and fades
    out (world-x alpha ramp) in front of the dish before the plasma glow.
"""
import bpy
from mathutils import Vector

LASER_X0, FADE0, FADE1 = -9.05, -7.95, -7.48
R_CORE, R_HALO = 0.009, 0.026
NO_GLOSSY_PREFIX = ("CollectBeamR24", "IFPinch", "IFGlow", "IFCone", "LaserCore", "LaserHalo", "LaserR25")


def _laser_mat(name, col, strength, alpha):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    N, L = nt.nodes, nt.links
    for n in list(N):
        N.remove(n)
    out = N.new("ShaderNodeOutputMaterial")
    geo = N.new("ShaderNodeNewGeometry")
    sp = N.new("ShaderNodeSeparateXYZ")
    L.new(geo.outputs["Position"], sp.inputs[0])
    mr = N.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = FADE0
    mr.inputs["From Max"].default_value = FADE1
    mr.inputs["To Min"].default_value = alpha
    mr.inputs["To Max"].default_value = 0.0
    mr.clamp = True
    L.new(sp.outputs["X"], mr.inputs["Value"])
    em = N.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*col, 1)
    em.inputs["Strength"].default_value = strength
    tr = N.new("ShaderNodeBsdfTransparent")
    mx = N.new("ShaderNodeMixShader")
    L.new(mr.outputs["Result"], mx.inputs["Fac"])
    L.new(tr.outputs[0], mx.inputs[1])
    L.new(em.outputs[0], mx.inputs[2])
    L.new(mx.outputs[0], out.inputs[0])
    return m


def post(sc):
    import build_cutaway_r2 as B
    import kit_r2 as K
    PL = Vector(B.PLASMA)
    # ---- laser: old line out, new line from a back port through the hole, fading out in front of the dish
    for nm in ("LaserCore", "LaserHalo"):
        o = bpy.data.objects.get(nm)
        if o is not None:
            o.hide_render = True
            o.hide_viewport = True
    a, b = Vector((LASER_X0, PL.y, PL.z)), PL
    core, halo = K.MB(), K.MB()
    core.tube(tuple(a), tuple(b), R_CORE, seg=16)
    halo.tube(tuple(a), tuple(b), R_HALO, seg=20)
    core.obj("LaserR25Core", _laser_mat("LaserR25CoreM", (1.0, 0.42, 0.08), 9.0, 1.0))
    halo.obj("LaserR25Halo", _laser_mat("LaserR25HaloM", (1.0, 0.32, 0.05), 2.0, 0.35))
    # back port: a short flanged tube behind the centre hole (the laser visibly comes from behind the dish)
    steel = bpy.data.materials.get("Steel") or K.mat("SteelR25", (0.5, 0.5, 0.52), metal=1.0, rough=0.3)
    pt = K.MB()
    x_back = B.COLL.x - 0.09
    pt.tube((x_back, 0, PL.z), (LASER_X0 + 0.05, 0, PL.z), 0.085, seg=32)
    pt.tube((LASER_X0 + 0.15, 0, PL.z), (LASER_X0 + 0.05, 0, PL.z), 0.15, seg=32)
    pt.obj("LaserPortR25", steel)
    # ---- dish face mirrors only chamber + plasma: no glossy rays for cone / IF pinch / laser
    n = 0
    for o in bpy.data.objects:
        if o.name.startswith(NO_GLOSSY_PREFIX):
            o.visible_glossy = False
            n += 1
    print(f"[r25h b302] visible_glossy off on {n} beam objects", flush=True)
    # R24 review #1 「把等离子体的辉光压一档，让镜面的边缘轮廓露出来」: plasma glow ball / halo one step down
    for nm, mult in (("PlasmaGlowR24", 0.6), ("PlasmaHalo", 0.6)):
        o = bpy.data.objects.get(nm)
        for m in (o.data.materials if o is not None and o.type == "MESH" else []):
            for nd in (m.node_tree.nodes if m and m.use_nodes else []):
                if nd.type == "EMISSION":
                    nd.inputs["Strength"].default_value *= mult


def check(sc):
    """BEAMCHECK + BEAMCHECK25 for the rim -> IF shell cone (job frames, 960x540)."""
    import beam_r25 as BR
    import build_cutaway_r2 as B
    import cut_hero_r24_b302 as H24
    c0, ax, a, b, e1, e2 = H24._ell()
    leg = bpy.data.objects.get("CollectBeamR24Leg0")
    if leg is None:
        print("[r25h b302] cone missing", flush=True)
        return
    RC = H24.rim_centre()
    ra, rb = leg.get("r25_radii", (1.15, 0.02))
    ch = {"legs": [[leg]], "spots": [None, None], "stops": [(RC + ax * 0.02, None), (Vector(B.IF), None)],
          "radii": [ra, rb], "leg_radii": [(ra, rb)], "mirrors": {}}
    f0 = sc.frame_current
    rx = (sc.render.resolution_x, sc.render.resolution_y)
    sc.render.resolution_x, sc.render.resolution_y = 960, 540
    BR.check(sc, ch, (30, 67, 103), exits=(1,), tag="B3_02")
    sc.render.resolution_x, sc.render.resolution_y = rx
    sc.frame_set(f0)
