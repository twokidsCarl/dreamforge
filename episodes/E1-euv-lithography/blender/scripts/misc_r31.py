"""Round 31 hook (misc sub-agent; shots in r2_misc.R31_MISC = B8_17 / B6_12 / A0_06). Layered AFTER the R22..R30 hooks,
BEFORE beam_hook_r29 / r30 (stay LAST). Never touches beams. Gold B9_05 (photons) never matches a branch below.

One module-level switch per R31_ROOT_CAUSE row (False -> that shot's exact R30 pixels):
- SYNC_R31  (row 6a, B8_17) R30 p3 「计数与画面不一致：第二帧计数 143/188（76 %），晶圆上只有约 1/4 的场变暗」: the R22
  logic (field k exposed iff k < counter(f), same time curve as the counter) was already right, but R27 painted EXPOSED
  fields LIGHT grey and UNEXPOSED fields dark, so viewers counted the dark quarter (= the not-yet-exposed fields) as the
  exposed ones. Tones swapped: unexposed = light bare silicon, exposed = dark violet-grey latent image -> "暗了多少格 =
  计数多少". 188 half-field grid (misc_b817_r20.layout, R27 lanes) untouched.
- PELL_R31  (row 6b, B6_12) R30 p3 「膜的存在主要靠一条高光。加一点极弱的掠射反光和边框阴影，让膜『悬在图形面前方』的间隙在
  宏观画面里也看得出」+「pellicle 锚点落在膜的边框 / 高光上，掩模锚点落在膜后能看到图形的位置，两条引线分别从左右引出」:
  (a) a soft frame shadow band on the pattern face just inside the frame bars (directional: wide on two sides, narrow on
  the other two; it sits on the pattern plane, the bars on the film plane, so it parallaxes against the frame as the
  camera moves = the gap); (b) one large, weak, soft area light linked to the membrane only (the R14 SweepReceivers
  collection) -> a faint grazing sheen over part of the film; (c) new anchors film31 (inner edge of the near frame bar at
  the film plane) / pattern31 (pattern seen through the film); labels re-placed in mograph/r2_ov_zz31m.py (left / right).
  Only new objects / the membrane-only light link; no shared material is edited.
- GLOBE_R31 (row 6c, A0_06) R30 p3 「城市灯光是暖橙 / 黄色…降成冷白或低饱和琥珀」「欧洲供应商光点糊成一团青雾…点改小、加锐、
  减 bloom」: EarthRealR30 city-light emission colour -> cool white (and a little weaker); supplier dot radius x0.55,
  emission a bit stronger (small + crisp), scene glare strength 0.35 -> 0.10. R30 earth / arcs / 5100 web untouched.
"""
import math

import bpy
from mathutils import Vector

SYNC_R31 = True
PELL_R31 = False   # misc 8-spp Q4 no: the frame-shadow band on the dark mirror pattern face does not show (diff 0 except labels); labels alone = overlay-only fix -> R30 pixels; see SMOKE.md R32 notes
GLOBE_R31 = True

# B8_17
UNEXP = ((0.52, 0.53, 0.56), (0.60, 0.61, 0.64))     # bare silicon (parity pair)
EXPO = ((0.085, 0.08, 0.12), (0.12, 0.11, 0.16))      # exposed latent image: dark violet-grey (parity pair)
# B6_12
SHADOW_W = {"+x": 0.16, "-x": 0.08, "+y": 0.16, "-y": 0.30}   # band widths inside the bars (pre-flip coords)
SHADOW_A = 0.75
SHEEN_E, SHEEN_SIZE = 0.0, 2.5   # sheen light dropped: any level drew a hard-edged bright plate on the near film (= R16 glass plate)
# A0_06
CITY_COL = (0.80, 0.88, 1.0)
CITY_GAIN = 0.8
DOT_SCALE = 0.55
DOT_STR = 3.0
GLARE = 0.10


def pre(variant, shot, mod):
    return None


def post(sc, variant, shot):
    try:
        if shot == "B8_17" and SYNC_R31:
            _b817(sc)
        if shot == "B6_12" and PELL_R31:
            _b612(sc)
        if shot == "A0_06" and GLOBE_R31:
            _a006(sc)
    except Exception as e:   # never break the build; the log shows it
        import traceback
        traceback.print_exc()
        print(f"[R31 misc] {shot} post FAILED: {e}", flush=True)
    return sc


def _lin(c):
    return tuple((x / 12.92) if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


# ------------------------------------------------------------------------------------------------ B8_17
def _b817(sc):
    # FieldR20 = the wafer under exposure (+ its R24 copy carried to the cassette); FieldR24Fresh = the R24 fresh wafer
    # (factor 0 = all unexposed) - copied before this hook, so it is patched too (else the fresh wafer reads "exposed")
    done = []
    for m in bpy.data.materials:
        if not (m.name.startswith("FieldR20") or m.name.startswith("FieldR24Fresh")) or not m.node_tree:
            continue
        N = m.node_tree.nodes
        mix = next((x for x in N if x.type == "MIX" and getattr(x, "data_type", "") == "RGBA"
                    and x.inputs["A"].is_linked and x.inputs["B"].is_linked
                    and x.inputs["A"].links[0].from_node.type == "MIX"), None)
        if mix is None and m.name.startswith("FieldR24Fresh"):
            # copied before the R27 parity nodes: plain RGBA mix, A = unexposed colour (factor 0 for the fresh wafer)
            mix = next((x for x in N if x.type == "MIX" and getattr(x, "data_type", "") == "RGBA"
                        and x.inputs["Factor"].is_linked and not x.inputs["A"].is_linked), None)
            if mix is not None:
                mix.inputs["A"].default_value = (*_lin(UNEXP[0]), 1)
                if not mix.inputs["B"].is_linked:
                    mix.inputs["B"].default_value = (*_lin(EXPO[0]), 1)
                done.append(m.name)
            continue
        if mix is None:
            continue
        for sock, (c0, c1) in (("A", UNEXP), ("B", EXPO)):
            cm = mix.inputs[sock].links[0].from_node
            cm.inputs["A"].default_value = (*_lin(c0), 1)
            cm.inputs["B"].default_value = (*_lin(c1), 1)
        done.append(m.name)
    print(f"[R31 B8_17] SYNC_R31: exposed fields dark, unexposed light (factor = R22 counter curve) in {done}", flush=True)


# ------------------------------------------------------------------------------------------------ B6_12
FW, FH, BAR = 1.32, 1.06, 0.014
Z_FILM, Z_PAT = 0.207, 0.1535


def _shadow_mat():
    m = bpy.data.materials.new("PelShadowR31")
    m.use_nodes = True
    nt = m.node_tree
    n, l = nt.nodes, nt.links
    for x in list(n):
        if x.type != "OUTPUT_MATERIAL":
            n.remove(x)
    out = next(x for x in n if x.type == "OUTPUT_MATERIAL")
    uv = n.new("ShaderNodeUVMap")
    sp = n.new("ShaderNodeSeparateXYZ")
    l.new(uv.outputs["UV"], sp.inputs[0])
    mr = n.new("ShaderNodeMapRange")
    mr.interpolation_type = "SMOOTHSTEP"
    mr.inputs["From Min"].default_value = 0.6      # umbra (flat) next to the bar, soft penumbra over the last 40 %
    mr.inputs["From Max"].default_value = 1.0
    mr.inputs["To Min"].default_value = SHADOW_A
    mr.inputs["To Max"].default_value = 0.0
    l.new(sp.outputs["X"], mr.inputs["Value"])
    tr = n.new("ShaderNodeBsdfTransparent")
    dk = n.new("ShaderNodeBsdfDiffuse")
    dk.inputs["Color"].default_value = (0.0, 0.0, 0.0, 1)
    mx = n.new("ShaderNodeMixShader")
    l.new(mr.outputs["Result"], mx.inputs["Fac"])
    l.new(tr.outputs[0], mx.inputs[1])
    l.new(dk.outputs[0], mx.inputs[2])
    l.new(mx.outputs[0], out.inputs["Surface"])
    return m


def _b612(sc):
    import misc_b612_r20 as P20
    import kit_r2 as K
    M = P20._flip_matrix()
    # (a) frame shadow bands on the pattern face (u = 0 at the bar inner edge -> 1 at the band's inner end)
    me = bpy.data.meshes.new("PelShadowR31")
    xi, yi = FW / 2 - BAR / 2, FH / 2 - BAR / 2
    z = Z_PAT + 0.0007
    verts, faces, uvs = [], [], []

    def quad(p0, p1, p2, p3):     # p0,p1 on the edge (u=0), p2,p3 inner (u=1)
        b = len(verts)
        verts.extend([p0, p1, p2, p3])
        faces.append((b, b + 1, b + 2, b + 3))
        uvs.extend([(0, 0), (0, 1), (1, 1), (1, 0)])
    w = SHADOW_W
    quad((xi, -yi, z), (xi, yi, z), (xi - w["+x"], yi, z), (xi - w["+x"], -yi, z))
    quad((-xi, yi, z), (-xi, -yi, z), (-xi + w["-x"], -yi, z), (-xi + w["-x"], yi, z))
    quad((-xi, yi, z), (xi, yi, z), (xi, yi - w["+y"], z), (-xi, yi - w["+y"], z))
    quad((xi, -yi, z), (-xi, -yi, z), (-xi, -yi + w["-y"], z), (xi, -yi + w["-y"], z))
    me.from_pydata(verts, [], faces)
    uvl = me.uv_layers.new(name="UVMap")
    for poly in me.polygons:
        for li in poly.loop_indices:
            uvl.data[li].uv = uvs[me.loops[li].vertex_index]
    me.materials.append(_shadow_mat())
    sh = bpy.data.objects.new("PelShadowR31", me)
    sc.collection.objects.link(sh)
    sh.matrix_world = M
    sh.visible_shadow = False
    try:
        sh.visible_glossy = False
    except AttributeError:
        pass
    # (b) faint grazing sheen: large soft area light, membrane-only (R14 SweepReceivers light link)
    cam = sc.camera
    fm = round((sc.frame_start + sc.frame_end) * 0.55)
    sc.frame_set(fm)
    C = cam.matrix_world.translation.copy()
    P = M @ Vector((0.15, 0.1, Z_FILM))
    nrm = (M.to_3x3() @ Vector((0, 0, 1))).normalized()
    v = (P - C)
    vr = v - 2 * v.dot(nrm) * nrm                 # mirror direction off the film plane
    Lp = P + vr.normalized() * 4.0 + (M.to_3x3() @ Vector((0.9, 0.0, 0.0)))
    lt = None if SHEEN_E <= 0 else K.area("PelSheenR31", tuple(Lp), tuple(P), SHEEN_SIZE, SHEEN_E, (0.92, 0.95, 1.0))
    rc = bpy.data.collections.get("SweepReceivers")
    if lt is not None and rc is not None:
        lt.visible_camera = False
        try:
            lt.light_linking.receiver_collection = rc
        except Exception:
            pass
    sc.frame_set(1)
    # (c) anchors for the zz31m labels (merged into the existing per-frame json, written by the last handler)
    pts = {"film31": M @ Vector((0.29, -(FH - BAR) / 2, Z_FILM)),       # film edge in the cut-open frame notch (section line)
           "pattern31": M @ Vector((-0.45, 0.0, Z_PAT))}                # pattern seen through the film, off the R28 glint
    
    for i, (cx, cy) in enumerate([(-1, 0), (1, 0), (0, -1), (0, 1), (-0.5, -1), (0.5, -1), (-0.5, 1), (0.5, 1)]):
        pts[f"cf{i}"] = M @ Vector((cx * (FW / 2 - BAR), cy * (FH / 2 - BAR), Z_FILM))
        pts[f"cp{i}"] = M @ Vector((cx * 0.45, cy * 0.35, Z_PAT))
    _merge_anchors("B6_12", pts)
    print(f"[R31 B6_12] PELL_R31: shadow bands {SHADOW_W} a={SHADOW_A}, sheen {SHEEN_E} W @ {tuple(round(x, 2) for x in Lp)}, "
          f"anchors film31 / pattern31", flush=True)


def _merge_anchors(shot, pts):
    import json
    import os
    import common as C
    from bpy_extras.object_utils import world_to_camera_view
    out = os.path.join(C.render_root(), "shots", shot, "anchors")

    def h(sc, *_):
        cam = sc.camera
        if cam is None:
            return
        fn = os.path.join(out, f"{sc.frame_current:04d}.json")
        try:
            res = json.load(open(fn))
        except Exception:
            res = {}
        for k, p in pts.items():
            v = world_to_camera_view(sc, cam, p)
            res[k] = [round(v.x, 4), round(1 - v.y, 4), round(v.z, 3)]
        os.makedirs(out, exist_ok=True)
        with open(fn, "w") as fh:
            json.dump(res, fh)
    bpy.app.handlers.frame_change_post.append(h)


# ------------------------------------------------------------------------------------------------ A0_06
def _a006(sc):
    em = bpy.data.materials.get("EarthRealR30")
    if em is not None:
        b = next(x for x in em.node_tree.nodes if x.type == "BSDF_PRINCIPLED")
        b.inputs["Emission Color"].default_value = (*CITY_COL, 1)
        mul2 = b.inputs["Emission Strength"].links[0].from_node if b.inputs["Emission Strength"].is_linked else None
        if mul2 is not None:
            mul2.inputs[1].default_value *= CITY_GAIN
    nd = 0
    for ng in bpy.data.node_groups:
        if ng.name.startswith("SupplierDotsR18"):
            for x in ng.nodes:
                if x.bl_idname == "GeometryNodeMeshIcoSphere":
                    x.inputs["Radius"].default_value *= DOT_SCALE
                    nd += 1
    dm = bpy.data.materials.get("SupplierDotR18")
    if dm is not None:
        for x in dm.node_tree.nodes:
            if x.type == "EMISSION":
                x.inputs[1].default_value = DOT_STR
    sc["glare_strength"] = GLARE
    print(f"[R31 A0_06] GLOBE_R31: city lights {CITY_COL} x{CITY_GAIN}, {nd} dot groups r x{DOT_SCALE} str {DOT_STR}, "
          f"glare {GLARE} (EarthRealR30 {'ok' if em else 'MISSING'}, dot mat {'ok' if dm else 'MISSING'})", flush=True)
