"""R24 chero B7_06 (R24_ROOT_CAUSE rows 3 + 5). Layered on R22 (cut_2b_r22_po) + R23 (turntable / truck camera).

R23 review: 「M5/M6 读成空心铁环：镜面要做成实心环形反射面（镜面金属感），中心孔约占直径 20 %」
            「光是一团紫雾（55 % 帧），M6 上的亮椭圆像悬空白点：改成清楚的三段光锥…一屏只有这一条光路」
  * M5 / M6 optical faces rebuilt as SOLID polished ring mirrors: hole radius 0.11 m (= 22 % of the 1.0 m diameter;
    R15 hole 0.16 + dark-reflecting face read as an empty ring), polished metal + a glossy-only soft card in each
    mirror's reflected view direction, so the face reads as one bright continuous metal surface.
  * the R22 volume cones / spots / glows (POConeR22_*, POLand*) deleted -> ONE beam_r24.chain in the turntable frame:
    roof port -> M5 ring landing -> M6 landing -> converging through the M5 hole -> wafer point (landings ON the faces).
    M6 landing moved 0.38 -> 0.15 m off axis so the converging leg passes the 0.11 m hole cleanly.
  * path topology / turntable / truck camera / dark backdrop untouched (不许回退).
"""
import math

import bpy
from mathutils import Vector

Z_CEIL = 3.3
Z6, Z5, ZW = 2.78, 1.64, 1.185
TILT = math.radians(18)
R6, R5, HOLE, TH = 0.5, 0.52, 0.11, 0.14
X5, X6 = -0.40, 0.15
RADII = [0.15, 0.045, 0.12, 0.008]
CH = {}


def _face_mat():
    m = bpy.data.materials.new("M56SolidR24")
    m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (0.9, 0.91, 0.94, 1)
    b.inputs["Metallic"].default_value = 1.0
    b.inputs["Roughness"].default_value = 0.045
    return m


def _card_mat(name, strength):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    gr = nt.nodes.new("ShaderNodeTexGradient")
    gr.gradient_type = "SPHERICAL"
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Location"].default_value = (0.5, 0.5, 0)
    mp.inputs["Scale"].default_value = (1.6, 1.6, 1)  # unused
    nt.links.new(tc.outputs["UV"], mp.inputs[0])
    sub = nt.nodes.new("ShaderNodeVectorMath")
    sub.operation = "SUBTRACT"
    nt.links.new(tc.outputs["UV"], sub.inputs[0])
    sub.inputs[1].default_value = (0.5, 0.5, 0)
    sc_ = nt.nodes.new("ShaderNodeVectorMath")
    sc_.operation = "SCALE"
    sc_.inputs["Scale"].default_value = 2.2
    nt.links.new(sub.outputs[0], sc_.inputs[0])
    nt.links.new(sc_.outputs[0], gr.inputs[0])
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (0.78, 0.82, 0.92, 1)
    ms = nt.nodes.new("ShaderNodeMath")
    ms.operation = "MULTIPLY"
    nt.links.new(gr.outputs["Fac"], ms.inputs[0])
    ms.inputs[1].default_value = strength
    nt.links.new(ms.outputs[0], em.inputs["Strength"])
    nt.links.new(em.outputs[0], out.inputs[0])
    return m


def _only_glossy(ob):
    for a in ("visible_camera", "visible_diffuse", "visible_shadow", "visible_transmission", "visible_volume_scatter"):
        try:
            setattr(ob, a, False)
        except AttributeError:
            pass


def post(sc):
    import kit_r2 as K
    import hero_kit_r15 as H15
    import beam_r24 as BR
    piv = bpy.data.objects.get("Turntable")
    n = sc.frame_end
    # ---- delete the R22 volume path (cones, spots, glows)
    for o in [o for o in bpy.data.objects if o.name.startswith(("POConeR22_", "POLandM5", "POLandM6", "POConeR20_",
                                                                 "POTopTipR20"))]:
        bpy.data.objects.remove(o)
    n5 = Vector((0, -math.sin(TILT), math.cos(TILT)))
    n6 = Vector((0, -math.sin(TILT), -math.cos(TILT)))
    c5, c6 = Vector((0, 0, Z5)), Vector((0, 0, Z6))
    # ---- solid ring mirror faces (replace PO15_mface)
    old = bpy.data.objects.get("PO15_mface")
    edge_mat = None
    oe = bpy.data.objects.get("PO15_medge")
    if oe is not None and oe.data.materials:
        edge_mat = oe.data.materials[0]
    if old is not None:
        old.hide_render = True
        old.hide_viewport = True
    fm, em_ = K.MB(), K.MB()
    H15.disc_mirror(fm, em_, c6, n6, R6, HOLE, TH, sag=0.006)
    H15.disc_mirror(fm, em_, c5, n5, R5, HOLE, TH, sag=0.006)
    face = fm.obj("PO24_mface", _face_mat())
    edge = em_.obj("PO24_medge", edge_mat or K.mat("M56EdgeR24", (0.2, 0.2, 0.22), metal=0.6, rough=0.4))
    for o in (face, edge):
        o.parent = piv
    # glossy-only soft cards in each mirror's reflected view direction (camera at mid shot, turntable frame)
    f0 = sc.frame_current
    sc.frame_set(round(n * 0.55))
    inv = piv.matrix_world.inverted() if piv is not None else None
    cl = sc.camera.matrix_world.translation.copy()
    if inv is not None:
        cl = inv @ cl
    sc.frame_set(f0)
    for nm, c_, n_, dist in (("PO24CardM5", c5, n5, 0.55), ("PO24CardM6", c6, n6, 0.5)):
        v = (c_ - cl).normalized()
        r = v - 2 * v.dot(n_) * n_
        me = bpy.data.meshes.new(nm)
        s = 0.9
        me.from_pydata([(-s, -s, 0), (s, -s, 0), (s, s, 0), (-s, s, 0)], [], [(0, 1, 2, 3)])
        uv = me.uv_layers.new()
        for i, lp in enumerate(me.loops):
            uv.data[i].uv = ((0, 0), (1, 0), (1, 1), (0, 1))[lp.vertex_index]
        ob = bpy.data.objects.new(nm, me)
        sc.collection.objects.link(ob)
        me.materials.append(_card_mat(nm + "M", 2.2))
        ob.location = c_ + r * dist
        ob.rotation_euler = (-r).to_track_quat("Z", "Y").to_euler()
        _only_glossy(ob)
        ob.parent = piv
    # ---- ONE path (turntable frame, same topology as R22/R23): roof port -> M5 -> M6 -> M5 hole -> wafer
    p5 = c5 + Vector((X5, 0, 0))
    p5.z = Z5 - 0.006 * (1 - (abs(X5) / 0.49) ** 2) + 0.002
    p6 = c6 + Vector((X6, 0, 0))
    p6.z = Z6 + 0.006 * (1 - (X6 / 0.47) ** 2) - 0.002
    foc = Vector((0, 0, ZW + 0.003))
    port = Vector((-0.86, 0.0, Z_CEIL))
    src = port + (port - p5).normalized() * 1.25
    ch = BR.chain("PO24Beam", [(src, None), (p5, n5), (p6, n6), (foc, (0, 0, 1))], RADII,
                  strength=3.2, alpha=0.55, spot_strength=18.0, spot_scale=1.6)
    objs = [o for leg in ch["legs"] for o in leg] + [s for s in ch["spots"] if s is not None]
    for o in objs:
        o.parent = piv
    BR.key_chain(ch, [1, round(1 + (n - 1) * 0.42), round(1 + (n - 1) * 0.70)])
    for nm, loc in (("Anchor_m5r", p5), ("Anchor_m6r", p6)):
        e_ = bpy.data.objects.get(nm)
        if e_ is not None:
            e_.location = loc
    CH["ch"] = ch
    # ---- BEAMCHECK on the job frames (stops transformed by the turntable per frame)
    rx = (sc.render.resolution_x, sc.render.resolution_y)
    sc.render.resolution_x, sc.render.resolution_y = 960, 540
    for f in (36, 79, 122):
        sc.frame_set(f)
        M = piv.matrix_world if piv is not None else None
        st = [((M @ p) if M is not None else p, nn) for p, nn in ch["stops"]]
        BR.check(sc, {"stops": st, "radii": ch["radii"]}, [f], exits=(0,), tag="B7_06")
    sc.render.resolution_x, sc.render.resolution_y = rx
    sc.frame_set(f0)
