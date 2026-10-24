"""R26 chero B8_03 / B8_03M (R26_ROOT_CAUSE rows 2 + 4).

Row 2: R25 main Q4 rejected the beam_r25 slit cone as a "hard-edged translucent wedge". While the R24 hook
(cut_hero_r24_b803) runs, beam_r24.chain is patched (cut_hero_r26.pre) to chain24() below: the SAME leg (top = reticle
side, bottom = slit, xdir kept so the slit ellipse stays aligned) built by beam_r26.soft_cone (rim roll-off, filled core,
no outline). The slit end keeps the slit footprint; the top widens so the ends are >= 3:1.
Row 4 (B8_03 only): R25 review 「晶圆是灰色空心方格托盘，看不出是硅片…改成镜面硅片（微弱掠射高光 + 场内细密图形），场格之间留切割道」:
  * WStage_wafer material: metallic polished silicon grey (mirror), thin-film interference tint (SiO2 ~ 330 nm), the
    R22/R23 die pattern kept (same nodes -> the exposed fields / slit stay aligned), die colours lifted from near-black
    to silicon grey, scribe streets lighter + rougher;
  * the R23 glossy-only black card (what the mirror wafer sees) gets a broad soft gradient (dark -> cool grey, no narrow
    strip): the disc reads as a mirror (smooth sheen across it) without the R23 horizontal white band (不许回退).
Slit colour, PIP, readouts, 8:1 motion untouched.
"""
import bpy
from mathutils import Vector

CH = {}
SI_DIE = (0.62, 0.63, 0.67)       # linear: polished Si in the die fields (metallic base colour)
SI_DEV = (0.26, 0.27, 0.33)       # device areas: darker, faint blue
SI_ST = (0.85, 0.85, 0.87)        # scribe streets
FILM_NM, FILM_IOR = 330.0, 1.46
ZOOM, SHIFT_Y = 1.12, -0.04
# slit cone: try 1 = R24 strength 3.0 x1.3 -> tone-mapped flat plateau (~172) with a 6-px step edge at f92 (main note:
# strength >= ~1.8 on dark ground = flat trapezoid) -> 1.0 / alpha 0.32 (mbeam B8_17 slit fan ended at 0.9 / 0.32)
CONE_STR, CONE_ALPHA = 1.4, 0.38   # try 3 (0.9 / 0.32 + round top) nearly vanished over the lit wafer
ROUND = 0.6
ENV_COL, ENV_MAX, ENV_MIN = (0.8, 0.85, 0.95), 2.2, 0.25   # try 1 (0.55 / 0.03): disc read dark blue plate


def chain24(name, stops, radii, color=None, strength=4.0, alpha=0.6, spot_strength=12.0, land_final=True, xdir=None,
            **_kw):
    import beam_r25 as B25
    import beam_r26 as BR
    a, b = Vector(stops[0][0]), Vector(stops[1][0])
    ra, rb = radii[0], radii[1]
    s_ = 3.05 * B25._rmax(rb) / B25._rmax(ra)
    if s_ > 1.0:
        ra = B25._scale(ra, s_)
    if isinstance(ra, (tuple, list)):
        # 8-spp try 2: the flat (3.8:1) top ellipse seen near face-on = a plateau with a step edge (5 px 31 -> 119 at
        # f92 y215) -> rounder top section so the rim roll-off has depth to work on; the slit end is unchanged
        ra = (ra[0], max(ra[1], ROUND * ra[0]))
    ra, rb = BR.tapered(ra, rb)
    legs = BR.soft_cone(f"{name}Leg0", a, b, ra, rb, color, CONE_STR, alpha=CONE_ALPHA, xdir=xdir)
    ch = {"legs": [legs], "spots": [None, None], "stops": [(a, stops[0][1]), (b, stops[1][1])], "radii": [ra, rb],
          "leg_radii": [(B25._rmax(ra), B25._rmax(rb))], "mirrors": {}}
    CH["ch"] = ch
    return ch


def check24(*_a, **_k):
    return []


def _lin(c):
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


def _near(v, ref, tol=0.012):
    return all(abs(a - b) < tol for a, b in zip(v, ref))


def wafer(sc):
    w = bpy.data.objects.get("WStage_wafer")
    if w is None or not w.data.materials:
        print("[r26h b803] wafer missing", flush=True)
        return
    m = w.data.materials[0].copy()
    m.name = "WaferSiR26"
    w.data.materials[0] = m
    nt = m.node_tree
    b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Metallic"].default_value = 1.0
    for k, v in (("Thin Film Thickness", FILM_NM), ("Thin Film IOR", FILM_IOR)):
        if k in b.inputs:
            b.inputs[k].default_value = v
    # R22 sRGB colours (bare / device / street) -> x0.2 linear (R23); map them to polished Si values
    ref = {(0.2, 0.205, 0.22): SI_DIE, (0.07, 0.075, 0.12): SI_DEV, (0.34, 0.35, 0.37): SI_ST}
    hit = 0
    for mx in nt.nodes:
        if mx.type != "MIX" or getattr(mx, "data_type", "") != "RGBA":
            continue
        for key in ("A", "B"):
            s_ = mx.inputs[key]
            if s_.is_linked:
                continue
            v = s_.default_value[:3]
            for r_, new in ref.items():
                if _near(v, tuple(x * 0.2 for x in _lin(r_)), 0.004):
                    s_.default_value = (*new, 1)
                    hit += 1
    for n in nt.nodes:
        if n.type == "MAP_RANGE":
            n.inputs["To Min"].default_value = 0.035
            n.inputs["To Max"].default_value = 0.3
    print(f"[r26h b803] wafer Si colours remapped {hit}, thin film {FILM_NM} nm", flush=True)
    # glossy environment: the R23 black card -> broad soft gradient (no strip)
    card = bpy.data.objects.get("WaferEnvCardR23")
    if card is not None:
        g = bpy.data.materials.new("WaferEnvGradR26")
        g.use_nodes = True
        N, L = g.node_tree.nodes, g.node_tree.links
        for n in list(N):
            N.remove(n)
        out = N.new("ShaderNodeOutputMaterial")
        tc = N.new("ShaderNodeTexCoord")
        sp = N.new("ShaderNodeSeparateXYZ")
        L.new(tc.outputs["Object"], sp.inputs[0])
        mr = N.new("ShaderNodeMapRange")
        mr.inputs["From Min"].default_value = -1.2
        mr.inputs["From Max"].default_value = 1.2
        mr.inputs["To Min"].default_value = ENV_MIN
        mr.inputs["To Max"].default_value = ENV_MAX
        mr.interpolation_type = "SMOOTHSTEP"
        L.new(sp.outputs["X"], mr.inputs["Value"])
        em = N.new("ShaderNodeEmission")
        em.inputs["Color"].default_value = (*ENV_COL, 1)
        L.new(mr.outputs["Result"], em.inputs["Strength"])
        L.new(em.outputs[0], out.inputs[0])
        card.data.materials[0] = g
    st = bpy.data.objects.get("WaferEnvStripR23")
    if st is not None:
        st.hide_render = True


def post(sc, shot):
    import beam_r26 as BR
    if shot == "B8_03M":
        return
    wafer(sc)
    # row 4 hero >= 1/4 frame: 8-spp try 2 measured the wafer at ~0.22 of the frame at f42 -> 12 % longer lens + a
    # small downward view shift (the zoom would push the disc into the bottom edge); camera path untouched
    cam = sc.camera
    l0 = cam.data.lens
    cam.data.lens = l0 * ZOOM
    cam.data.shift_y += SHIFT_Y
    print(f"[r26h b803] lens {l0:.1f} -> {cam.data.lens:.1f}, shift_y {cam.data.shift_y:.3f}", flush=True)
    ch = CH.get("ch")
    if ch is None:
        print("[r26h b803] cone missing", flush=True)
        return
    f0 = sc.frame_current
    rx = (sc.render.resolution_x, sc.render.resolution_y)
    sc.render.resolution_x, sc.render.resolution_y = 960, 540
    BR.check(sc, ch, (42, 92, 143), tag="B8_03")
    sc.render.resolution_x, sc.render.resolution_y = rx
    sc.frame_set(f0)
