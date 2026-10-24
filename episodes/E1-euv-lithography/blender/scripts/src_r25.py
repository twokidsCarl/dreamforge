"""Round 25 hook (owned by the 'srcb' sub-agent; shots in r2_source.R25_SRC). Remove a shot from R25_SRC -> R24 pixels.

R25_ROOT_CAUSE row 2 (taper / no solid column, shared beam_r25 shell cone):
  * B1_15 (R24 review 「出射光仍像实心光柱」 / 「越走越宽的实心光柱」): runs AFTER src_r24 (R24 push 2.45 -> 1.95 + focus
    pull plasma -> face, neutral PlasmaLight, IF anchor merge all kept). The R24 beam_r24 surface leg B115ExitR24*
    (inner-filled skin = solid column) is deleted and rebuilt as ONE beam_r25.chain leg on the optical axis
    (tapered SHELL cone: bright silhouette + faint core, no inner cone, brighter toward the IF), same start (S25_K of
    the way rim -> IF) and the same off-frame IF stop; beam_r25.check on 9 / 20 / 31 (exits=(1,)).
  * B2_08 (R23 「白色气流线是等宽实线」, R24 32-spp 「扁平的半透明带子」): the R23 SnH4RibbonsR23 tubes are deleted; the gas
    flow = S25_GN (4) SEPARATED straight beam_r25 shell streams, each WIDE where it lifts off a tin-deposit patch on the
    face and NARROW (>= 3:1) at the pump port, brighter toward the port (gain) = flow direction into the port. Each
    stream is its own one-leg chain, beam_r25.check per stream on 60 / 133 / 206 (port = landing stop, in frame).
"""
import math
import os

_E = os.environ
_MOD = [None]


def pre(variant, shot, mod):
    _MOD[0] = mod


def post(sc, variant, shot):
    if shot == "B1_15" and variant == "contrast":
        _b115(sc)
    elif shot == "B2_08" and variant == "clean":
        _b208(sc)
    return sc


def fade_start(ob, w):
    """Soft start on a beam_r25 shell leg: strength and alpha ramp 0 -> 1 over the first w of its length (ConeUV Y)
    so the wide mouth emerges from the dark instead of a hard bright ellipse edge (not an equal-width tube end fade:
    the leg keeps its >= 3:1 taper)."""
    if w <= 0:
        return
    for slot in ob.material_slots:
        m = slot.material
        N, L = m.node_tree.nodes, m.node_tree.links
        sp = next(n for n in N if n.type == "SEPXYZ")
        em = next(n for n in N if n.type == "EMISSION")
        mx = next(n for n in N if n.type == "MIX_SHADER")
        mr = N.new("ShaderNodeMapRange")
        mr.interpolation_type = "SMOOTHSTEP"
        L.new(sp.outputs["Y"], mr.inputs["Value"])
        mr.inputs["From Min"].default_value = 0.0
        mr.inputs["From Max"].default_value = w
        for sock in (em.inputs["Strength"], mx.inputs["Fac"]):
            src = sock.links[0].from_socket
            mul = N.new("ShaderNodeMath")
            mul.operation = "MULTIPLY"
            L.new(src, mul.inputs[0])
            L.new(mr.outputs["Result"], mul.inputs[1])
            L.new(mul.outputs[0], sock)


def _b115(sc):
    import bpy
    from mathutils import Vector
    import kit_r2 as K
    import b115_r21 as B
    import b115_r22_build as BB
    import beam_r25 as BM
    for ob in list(bpy.data.objects):
        if ob.name.startswith("B115ExitR24") or ob.name.startswith("IFConeR22"):
            bpy.data.objects.remove(ob, do_unlink=True)
    xr, xi0 = B.fx(B.R), BB.image_x()
    # the IF (the cone's point) is brought INTO the frame (R24: off-frame -> the visible part never converged, the
    # frame bottom cut it at ~50 % = 「实心光柱」); the light passes straight through it and re-expands off-frame
    xi = xr + float(_E.get("S25_IFF", "0.62")) * (xi0 - xr)
    k = float(_E.get("S25_K", "0.62"))
    xa = xr + k * (xi - xr)
    ra = B.R * (xi - xa) / (xi - xr)
    ri = float(_E.get("S25_RI", "0.012"))
    xe = xi + (xi - xa) * float(_E.get("S25_EL", "1.2"))
    re = ra * (xe - xi) / (xi - xa)
    ch = BM.chain("B115ExitR25", [((xa, 0, 0), None), ((xi, 0, 0), None), ((xe, 0, 0), None)], [ra, ri, re],
                  color=K.VIOLET, strength=float(_E.get("S25_CS", "5.0")), alpha=float(_E.get("S25_CA", "0.55")),
                  edge=float(_E.get("S25_EDGE", "2.4")), core=float(_E.get("S25_CORE", "0.06")),
                  gain=float(_E.get("S25_GAIN", "1.4")), land_final=False, mirrors=False)
    for leg in ch["legs"]:
        for ob in leg:
            ob.visible_glossy = False      # the cone must not appear in the mirror face (mirror-hero: no overlap)
    fade_start(ch["legs"][0][0], float(_E.get("S25_FADE", "0.3")))
    import src_r24 as R24
    R24._anchor_merge("B1_15", {"if": Vector((xi, 0, 0)), "cone_mid": Vector(((xa + xi) * 0.5, 0, 0))})
    from bpy_extras.object_utils import world_to_camera_view as w2c
    for f in (9, 20, 31):
        sc.frame_set(f)
        ys = [round((1 - w2c(sc, sc.camera, Vector(p)).y) * 540) for p in
              ((xa, 0, 0), (xa, 0, ra), (xa, 0, -ra), (xa, ra, 0), (xi, 0, 0), (xe, 0, 0))]
        rim = [round((1 - w2c(sc, sc.camera, Vector((xr, B.R * math.cos(t), B.R * math.sin(t)))).y) * 540)
               for t in [i * math.pi / 36 for i in range(72)]]
        print(f"B115PROJ f{f} start/top/bot/side/IF/exit y@540 {ys} rim y {min(rim)}..{max(rim)}", flush=True)
    BM.check(sc, ch, (9, 20, 31), exits=(2,), tag="B1_15")
    sc.frame_set(1)


def _b208(sc):
    import bpy
    from mathutils import Vector
    import b115_r17 as B115
    import beam_r25 as BM
    S = _MOD[0]
    F = B115.B_F
    for ob in list(bpy.data.objects):
        if ob.name.startswith("SnH4RibbonsR23") or ob.name == "SnH4Lines" or ob.name.startswith("SnH4_") \
                or ob.name.startswith("SnH4Flow"):
            bpy.data.objects.remove(ob, do_unlink=True)
    a_p, z_p = math.radians(124), 0.5
    nrm_p = Vector((-math.cos(a_p), -math.sin(a_p), 0))
    port = Vector((math.cos(a_p), math.sin(a_p), 0)) * (S.CHAMBER_R - 0.02) + Vector((0, 0, z_p))
    col = (0.84, 0.91, 1.0)
    src = [tuple(float(v) for v in s.split(":")) for s in
           _E.get("S25_GSRC", "0.58:-27,0.54:-48,0.46:-67,0.37:-88").split(",")]
    lift = float(_E.get("S25_GLIFT", "0.04"))
    r0, r1 = float(_E.get("S25_GR0", "0.06")), float(_E.get("S25_GR1", "0.014"))
    tvec = Vector((0, 0, 1)).cross(nrm_p).normalized()
    chains = []
    for i, (rr, ad) in enumerate(src):
        a = math.radians(ad)
        y, z = rr * math.cos(a), rr * math.sin(a)
        nrm = Vector((1, -y / (2 * F), -z / (2 * F))).normalized()
        p0 = Vector((B115.face_x(rr), y, z)) + nrm * lift + Vector((float(_E.get("S25_GLX", "0.28")), 0,
                                                                         float(_E.get("S25_GLZ", "0.16"))))
        off = (i - (len(src) - 1) / 2) * float(_E.get("S25_GPS", "0.05"))
        p1 = port + nrm_p * 0.07 + tvec * off * 0.6 + Vector((0, 0, off))
        ch = BM.chain(f"SnH4FlowR25_{i}", [(tuple(p0), None), (tuple(p1), None)], [r0, r1], color=col,
                      strength=float(_E.get("S25_GS", "2.2")), alpha=float(_E.get("S25_GA", "0.42")),
                      edge=float(_E.get("S25_GE", "2.2")), core=float(_E.get("S25_GC", "0.06")),
                      gain=float(_E.get("S25_GG", "1.6")), land_final=False, mirrors=False)
        for ob in ch["legs"][0]:
            ob.visible_glossy = False   # no doubled stream in the polished face
            fade_start(ob, float(_E.get("S25_GF", "0.4")))
        chains.append(ch)
    if _E.get("S25_GDIAG") == "1":
        from bpy_extras.object_utils import world_to_camera_view as w2c
        cam = sc.camera
        for rr in (0.4, 0.5, 0.58):
            for ad in range(-80, 60, 10):
                a = math.radians(ad)
                y, z = rr * math.cos(a), rr * math.sin(a)
                nrm = Vector((1, -y / (2 * F), -z / (2 * F))).normalized()
                p0 = Vector((B115.face_x(rr), y, z)) + nrm * lift + Vector((float(_E.get("S25_GLX", "0.28")), 0,
                                                                                 float(_E.get("S25_GLZ", "0.16"))))
                p1 = port + nrm_p * 0.07
                out = []
                for f in (60, 206):
                    sc.frame_set(f)
                    cl = cam.matrix_world.translation
                    ax = (p1 - p0).normalized()
                    los = ((p0 + p1) * 0.5 - cl).normalized()
                    ang = math.degrees(math.acos(abs(ax.dot(los))))
                    v0, v1 = w2c(sc, cam, p0), w2c(sc, cam, p1)
                    out.append(f"f{f} ax/los {ang:.0f} scr ({v0.x*960:.0f},{(1-v0.y)*540:.0f})->"
                               f"({v1.x*960:.0f},{(1-v1.y)*540:.0f})")
                print(f"GDIAG rr {rr} a {ad} " + " | ".join(out), flush=True)
    for i, ch in enumerate(chains):
        BM.check(sc, ch, (60, 133, 206), tag=f"B2_08s{i}")
    sc.frame_set(1)
