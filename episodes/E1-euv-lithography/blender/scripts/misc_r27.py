"""Round 27 hook (misc sub-agent; shots in r2_misc.R27_MISC = B8_17 / A0_06 / A2_03). Layered AFTER the R22..R26 hooks.

One module-level switch per root-cause row (False -> that row's R26 pixels for the shot):
- GRID_R27   (row 5, B8_17)  R26 p3 「晶圆上画的是约 12 列细长竖条…数不出 188」: the 188 half-field cells (26 x 16.5 mm,
  misc_b817_r20.layout, count printed) become individually legible: wide scribe lanes in BOTH directions (the 16.5 mm rows
  were sub-pixel at this camera -> only 12 columns read), dark scribe lanes, unexposed fields mid-dark silicon (was near-black), alternating
  cell tone (scan-order parity) so neighbouring fields separate. Exposure state / counter sync / stage (R22) untouched.
  Counter block (box grows with rows, 3.4 万+ only after 「188 × 185」) lives in mograph/r2_ov_zz27m.py, gated on this switch.
- GLOBE_R27  (row 5, A0_06)  R26 p3 「弧线伸出了球体边缘…转到背面的弧线做透明度衰减」: trunk arcs fade out smoothly as
  they turn toward the limb (view-facing falloff), both ends stay on the surface. The 「荷兰 · 整机总装」 leader is drawn
  in the overlay (r2_ov_zz27m) -> its re-anchoring on the NL ring (52N 5E) IS the structural fix there.
- NA_R27     (row 5, A2_03)  R26 p3 「『NA = 收光锥角』没有画成锥」: the last leg PO5 -> wafer becomes a wide soft
  converging cone (mouth = PO5 blank, apex on the wafer), the theta arc is enlarged + a 3D 「θ」 (repo font), and the
  cone (with its theta arc) opens wider in the 3rd beat (NA grows).
- KIT_R27    (row 4, A2_03)  R26 p3 「右侧墙面是同一种格子…换 2–3 种模块」: the R25 populate_wall rack row (RackA203R25,
  x 3.3..5.2) is replaced by kit_r27.named_row: 6 different nameable parts, one each, big blocks (2 rows x 3).
"""
import math
import os

import bpy
from mathutils import Matrix, Vector

GRID_R27 = True
GLOBE_R27 = True
NA_R27 = True
KIT_R27 = False   # 8-spp Q4 no: right bay reads as a light, sparse wall (R26 dense rack lost) -> R26 rack; see SMOKE.md

EP = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
FONT = os.path.join(EP, "blender", "textures", "fonts", "DejaVuSans-Bold.ttf")


def pre(variant, shot, mod):
    pass


def post(sc, variant, shot):
    try:
        if shot == "B8_17" and GRID_R27:
            _b817_grid(sc)
        if shot == "A0_06" and GLOBE_R27:
            _a006_arcs(sc)
        if shot == "A2_03" and NA_R27:
            _a203_na(sc)
        if shot == "A2_03" and KIT_R27:
            _a203_kit(sc)
    except Exception as e:   # never break the build; the log shows it
        import traceback
        traceback.print_exc()
        print(f"[R27 misc] {shot} post FAILED: {e}", flush=True)
    return sc


# ------------------------------------------------------------------------------------------------ helpers
def _op(nt, op, a, b):
    m = nt.nodes.new("ShaderNodeMath")
    m.operation = op
    for k, x in enumerate((a, b)):
        if isinstance(x, (int, float)):
            m.inputs[k].default_value = x
        else:
            nt.links.new(x, m.inputs[k])
    return m.outputs[0]


def _lin(c):
    return tuple(((x + 0.055) / 1.055) ** 2.4 if x > 0.04045 else x / 12.92 for x in c)


# ------------------------------------------------------------------------------------------------ B8_17
GRID_LANE_X = 0.008    # half-lane across the 26 mm edge (scene units: 0.26 = 26 mm)
GRID_LANE_Y = 0.013    # half-lane across the 16.5 mm edge (foreshortened ~3x at this camera)


def _b817_grid(sc):
    import misc_b817_r20 as W20
    m = bpy.data.materials.get("FieldR20")
    if m is None:
        print("[R27 B8_17] FieldR20 missing", flush=True)
        return
    nt = m.node_tree
    N = nt.nodes
    # 1) scribe border: separate x / y lane widths (was one 0.004 threshold -> rows sub-pixel)
    lt = next(x for x in N if x.type == "MATH" and x.operation == "LESS_THAN" and not x.inputs[1].is_linked
              and abs(x.inputs[1].default_value - 0.004) < 1e-6)
    mn = lt.inputs[0].links[0].from_node                  # MINIMUM(ex * FX, ey * FY)
    exf = mn.inputs[0].links[0].from_socket
    eyf = mn.inputs[1].links[0].from_socket
    bx = _op(nt, "LESS_THAN", exf, GRID_LANE_X)
    by = _op(nt, "LESS_THAN", eyf, GRID_LANE_Y)
    border = _op(nt, "MAXIMUM", bx, by)
    m1 = next(x for x in N if x.type == "MIX_SHADER" and x.inputs["Fac"].is_linked
              and x.inputs["Fac"].links[0].from_node == lt)
    # 2) lane shader: light on unexposed (dark silicon) fields, dark on exposed (light grey) fields
    mix = next(x for x in N if x.type == "MIX" and getattr(x, "data_type", "") == "RGBA")
    exposed = mix.inputs["Factor"].links[0].from_socket
    light = N.new("ShaderNodeBsdfDiffuse")
    light.inputs["Color"].default_value = (0.008, 0.008, 0.010, 1)   # R27 v2: dark lanes on both (v1 light lanes read as a white mesh)
    dark = next(x for x in N if x.type == "BSDF_DIFFUSE" and x is not light)
    lane = N.new("ShaderNodeMixShader")
    nt.links.new(exposed, lane.inputs["Fac"])
    nt.links.new(light.outputs[0], lane.inputs[1])
    nt.links.new(dark.outputs[0], lane.inputs[2])
    nt.links.new(border, m1.inputs["Fac"])
    nt.links.new(lane.outputs[0], m1.inputs[2])
    # 3) alternating cell tone by scan-order parity (UVMap.x = (k + .5) / 188)
    uv = next(x for x in N if x.type == "UVMAP" and x.uv_map == "UVMap")
    sep = N.new("ShaderNodeSeparateXYZ")
    nt.links.new(uv.outputs["UV"], sep.inputs[0])
    par = _op(nt, "MODULO", _op(nt, "FLOOR", _op(nt, "MULTIPLY", sep.outputs["X"], W20.COUNT), 0.0), 2.0)
    for sock, (c0, c1) in (("A", ((0.20, 0.21, 0.25), (0.27, 0.28, 0.32))), ("B", ((0.50, 0.51, 0.53), (0.60, 0.61, 0.63)))):
        cm = N.new("ShaderNodeMix")
        cm.data_type = "RGBA"
        cm.inputs["A"].default_value = (*_lin(c0), 1)
        cm.inputs["B"].default_value = (*_lin(c1), 1)
        nt.links.new(par, cm.inputs["Factor"])
        nt.links.new(cm.outputs["Result"], mix.inputs[sock])
    print(f"[R27 B8_17] GRID_R27: {len(W20.layout(1.5))} fields, lanes x {GRID_LANE_X * 2 * 100:.0f} mm / "
          f"y {GRID_LANE_Y * 2 * 100:.0f} mm (scene x10), parity tone", flush=True)


# ------------------------------------------------------------------------------------------------ A0_06
A006_FACE = (0.30, 0.60)   # view-facing fade window (v2 0.25-0.50: emission 3.0 saturates, half alpha still read full). An arc lifted 3-5 % R projects OUTSIDE the disc while n.v < ~0.24-0.30 (v1 0.04-0.32 left it visible there)


def _a006_arcs(sc):
    arcs = [o for o in bpy.data.objects if o.name.startswith("TrunkR18_") and o.type == "CURVE"]
    if not arcs:
        print("[R27 A0_06] no trunk arcs", flush=True)
        return
    src = arcs[0].data.materials[0]
    col, stg = (0.2, 0.85, 1.0, 1.0), 3.0
    if src and src.use_nodes:
        e0 = next((n for n in src.node_tree.nodes if n.type == "EMISSION"), None)
        if e0:
            col, stg = tuple(e0.inputs[0].default_value), e0.inputs[1].default_value
    m = bpy.data.materials.new("TrunkArcR27")
    m.use_nodes = True
    nt = m.node_tree
    for nd in list(nt.nodes):
        nt.nodes.remove(nd)
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    nrm = nt.nodes.new("ShaderNodeVectorMath")
    nrm.operation = "NORMALIZE"
    nt.links.new(geo.outputs["Position"], nrm.inputs[0])
    dp = nt.nodes.new("ShaderNodeVectorMath")
    dp.operation = "DOT_PRODUCT"
    nt.links.new(nrm.outputs["Vector"], dp.inputs[0])
    nt.links.new(geo.outputs["Incoming"], dp.inputs[1])
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.interpolation_type = "SMOOTHSTEP"
    mr.inputs["From Min"].default_value = A006_FACE[0]
    mr.inputs["From Max"].default_value = A006_FACE[1]
    mr.inputs["To Min"].default_value = 0.0
    mr.inputs["To Max"].default_value = 1.0
    nt.links.new(dp.outputs["Value"], mr.inputs["Value"])
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs[0].default_value = col
    em.inputs[1].default_value = stg
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(mr.outputs["Result"], mix.inputs[0])
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(em.outputs[0], mix.inputs[2])
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(mix.outputs[0], out.inputs[0])
    for o in arcs:
        o.data.materials[0] = m
    print(f"[R27 A0_06] GLOBE_R27: {len(arcs)} trunk arcs fade with view-facing {A006_FACE}", flush=True)


# ------------------------------------------------------------------------------------------------ A2_03
NA_MOUTH = (0.20, 0.30)    # cone mouth radius at PO5: NA beat -> widened (3rd beat); PO5 blank r 0.31
NA_WIDEN = (0.70, 0.84)    # fraction of the shot over which the cone opens
NA_STRENGTH, NA_ALPHA, NA_GAIN, NA_EDGE, NA_CORE = 1.5, 0.30, 1.6, 1.8, 0.12   # v2 edge/core: rim > centre; v1 4.0 / 0.38 / 1.2 = flat 185-lum plateau over the lit bay (RETRO a NO-GO)


def _a203_na(sc):
    import beam_r26 as B26
    import build_cutaway_r2 as B
    import kit_r2 as K
    n = sc.frame_end
    th_ob = bpy.data.objects.get("NATheta")
    leg = [o for o in bpy.data.objects if o.name.startswith("A203R24Leg1")]
    wf = Vector((B.WAFER.x, 0.0, 1.065))
    po5 = Vector(B.PO[5])
    if leg and leg[0].type == "MESH":           # PO5 landing = centre of the R26 leg-1 mouth ring (staggered PO5)
        vs = [leg[0].matrix_world @ v.co for v in leg[0].data.vertices]
        dmax = max((v - wf).length for v in vs)
        ring = [v for v in vs if (v - wf).length > dmax - 0.02]
        po5 = sum(ring, Vector()) / len(ring)
    print(f"[R27 A2_03] leg1 objs {[o.name for o in leg]} po5 {tuple(round(x, 3) for x in po5)}", flush=True)
    vis = None
    if leg:
        vis = [(fc.data_path, [(k.co[0], k.co[1]) for k in fc.keyframe_points])
               for fc in _fcurves(leg[0].animation_data)]
    for o in leg:
        bpy.data.objects.remove(o, do_unlink=True)
    u = (po5 - wf).normalized()
    L = (po5 - wf).length
    # local frame: apex at origin, +Z toward PO5; x = perp in the camera-facing plane (same as the theta arc)
    # theta-arc plane faces the camera (v1 used u x Y -> arc seen edge-on, read as an "I"): perp = u x view at the NA beat
    sc.frame_set(round(n * 0.6))
    view = (sc.camera.matrix_world.translation - wf).normalized()
    perp = u.cross(view).normalized()
    if perp.dot(Vector((-1, 0, 0))) < 0:      # edge stub on the screen-left silhouette
        perp = -perp
    yv = u.cross(perp).normalized()
    M = Matrix((perp, yv, u)).transposed().to_4x4()
    M.translation = wf
    cone = B26.soft_cone("NAConeR27", po5, wf + u * 0.002, NA_MOUTH[0], 0.006, K.VIOLET, NA_STRENGTH, alpha=NA_ALPHA,
                         gain=NA_GAIN, edge=NA_EDGE, core=NA_CORE)[0]
    cone.data.transform(M.inverted())
    cone.matrix_world = M
    # theta arc + edge stub + dashed axis (rebuilt larger) + 3D theta glyph, parented to the cone (opens with it)
    if th_ob is not None:
        bpy.data.objects.remove(th_ob, do_unlink=True)
    e = (u * L + perp * NA_MOUTH[0]).normalized()
    th = math.acos(max(-1.0, min(1.0, u.dot(e))))
    ar = 0.55 * L                               # v3: arc spans the FULL aperture (-th..+th) across the cone
    amb = K.MB()
    arc = [wf + (u * math.cos(th * (k - 24) / 24) + perp * math.sin(th * (k - 24) / 24)) * ar for k in range(49)]
    for a_, b_ in zip(arc, arc[1:]):
        amb.tube(a_, b_, 0.008, seg=8)
    for k in range(5):
        amb.tube(wf + u * L * (0.04 + k * 0.12), wf + u * L * (0.10 + k * 0.12), 0.004, seg=6)
    amb.tube(wf, wf + e * L * 0.75, 0.004, seg=6)
    e_ = (u * L - perp * NA_MOUTH[0]).normalized()
    amb.tube(wf, wf + e_ * L * 0.75, 0.004, seg=6)
    ink = amb.obj("NAThetaR27", K.emit_mat("NAThetaInk27", K.CYAN, 4.0))
    ink.data.transform(M.inverted())
    ink.matrix_world = M
    ink.parent = cone
    ink.matrix_parent_inverse = cone.matrix_world.inverted()
    td = bpy.data.curves.new("NAThetaGlyph", "FONT")
    td.body = "θ"
    td.font = bpy.data.fonts.load(FONT, check_existing=True)
    td.size = 0.16
    td.align_x, td.align_y = "CENTER", "CENTER"
    glyph = bpy.data.objects.new("NAThetaGlyphR27", td)
    sc.collection.objects.link(glyph)
    glyph.data.materials.append(K.emit_mat("NAThetaInk27", K.CYAN, 4.0))
    mid = u * ar
    glyph.location = wf + (u * math.cos(th / 2) + perp * math.sin(th / 2)) * (ar + 0.12)   # half-angle (axis -> edge)
    cam = sc.camera
    glyph.rotation_euler = cam.matrix_world.to_euler() if cam else (math.radians(70), 0, 0)
    f_on = round(n * 0.48)
    f0, f1 = round(n * NA_WIDEN[0]), round(n * NA_WIDEN[1])
    s = NA_MOUTH[1] / NA_MOUTH[0]
    for ob in (cone, ink, glyph):
        ob.hide_render = True
        ob.keyframe_insert("hide_render", frame=1)
        ob.keyframe_insert("hide_render", frame=f_on - 1)
        ob.hide_render = False
        ob.keyframe_insert("hide_render", frame=f_on)
    cone.scale = (1, 1, 1)
    cone.keyframe_insert("scale", frame=f0)
    cone.scale = (s, s, 1)
    cone.keyframe_insert("scale", frame=f1)
    g0 = glyph.location.copy()
    glyph.keyframe_insert("location", frame=f0)
    th2 = math.atan(math.tan(th) * s)
    glyph.location = wf + (u * math.cos(th2 / 2) + perp * math.sin(th2 / 2)) * (ar + 0.12)
    glyph.keyframe_insert("location", frame=f1)
    K.anchors("A2_03", {"beam": B.PO[4].lerp(po5, 0.5), "mirror": po5, "wafer": B.WAFER, "mask": B.MASK,
                        "theta": wf + mid, "na_apex": wf})
    print(f"[R27 A2_03] NA_R27: cone L {L:.2f} mouth {NA_MOUTH} theta {math.degrees(th):.1f} -> {math.degrees(th2):.1f} "
          f"deg, on f{f_on}, widen f{f0}-{f1}; old leg vis {vis}", flush=True)


def _fcurves(ad):
    if not ad or not ad.action:
        return []
    try:
        return list(ad.action.fcurves)
    except AttributeError:
        from bpy_extras.anim_utils import action_get_channelbag_for_slot
        cb = action_get_channelbag_for_slot(ad.action, ad.action_slot)
        return list(cb.fcurves) if cb else []


# ------------------------------------------------------------------------------------------------ A2_03 kit (row 4)
A203_KIT = dict(x=(3.3, 5.2), z=(0.35, 2.9), y=1.2, scale=1.1, depth=1.6)
A203_KINDS = ("turbo_gate", "power_supply", "hexapod_mount", "valve_island", "ion_pump", "metrology_ring")


def _a203_kit(sc):
    import hero_kit_r10 as HK
    import kit_r27 as K27
    gone = [o for o in bpy.data.objects if o.name.startswith("RackA203R25")]
    for o in gone:
        bpy.data.objects.remove(o, do_unlink=True)
    P = HK.new_parts()
    c = A203_KIT
    ks = K27.named_row(P, c["x"][0], c["x"][1], c["z"][0], c["z"][1], c["y"], kinds=A203_KINDS, seed=203,
                       scale=c["scale"], depth=c["depth"])
    obs = K27.finish(P, "KitA203R27")
    # the wall plate behind the parts: dark anodised (light paint_grey plate read as an empty white wall at 8 spp)
    import kit_r2 as K
    dark = K.mat("KitA203PlateR27", (0.10, 0.11, 0.13), metal=0.6, rough=0.4)
    for o in obs or []:
        if "paint_grey" in o.name and o.type == "MESH":
            o.data.materials.clear()
            o.data.materials.append(dark)
    print(f"[R27 A2_03] KIT_R27: removed {len(gone)} rack objs, {K27.count(ks)} kinds {ks}, objs {[o.name for o in obs or []]}",
          flush=True)
