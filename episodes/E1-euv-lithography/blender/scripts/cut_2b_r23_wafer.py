"""R23 row 5 (B8_03 / B8_03M wafer): R22 review 「晶圆上场格是均匀灰方格」; R22 smoke: mirror Si + full environment
reflection -> bright blotches (Q4 no).  Recipe: dark silicon + in-field micro pattern (the R22 colour remap of the R17
die-map shader, reused read-only from cut_2b_r22_scan) + ONE grazing highlight band.  The band comes from a
glossy-only environment for the wafer: a large black card in the wafer's mirror direction (visible to glossy rays
only - no camera / diffuse / shadow / volume) that carries a single narrow emissive strip.  Everything the polished
disc used to mirror (bay walls, hoses, beam volumes) is hidden behind the card -> no blotches, one band.
"""
import bpy
from mathutils import Vector

CARD_D = 0.5       # card distance from the wafer centre along the mirrored view ray (m); 0.9 (try 4) let a light-grey
                   # stage part between card and disc show as a second grey band
CARD_S = 2.4       # card size (m): ±67° around the mirrored ray (>= wafer radius 0.42 so the far rim stays in front)


def _only_glossy(ob):
    for a in ("visible_camera", "visible_diffuse", "visible_shadow", "visible_transmission", "visible_volume_scatter"):
        try:
            setattr(ob, a, False)
        except AttributeError:
            pass
    ob.visible_glossy = True


def _emit_mat(name, col, strength):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*col, 1)
    em.inputs["Strength"].default_value = strength
    nt.links.new(em.outputs[0], out.inputs[0])
    return m


def _plane(name, w, h, mat):
    me = bpy.data.meshes.new(name)
    me.from_pydata([(-w / 2, -h / 2, 0), (w / 2, -h / 2, 0), (w / 2, h / 2, 0), (-w / 2, h / 2, 0)], [], [(0, 1, 2, 3)])
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    me.materials.append(mat)
    return ob


def post(sc, shot):
    import cut_2b_r22_scan as S22          # dark Si + die micro pattern (read-only reuse of the R22 recipe)
    S22.post(sc, shot)
    w = bpy.data.objects.get("WStage_wafer")
    if w is None:
        return
    m = w.data.materials[0]
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    # 8-spp try 1 (metallic Si, R22 roughness 0.04-0.16): rough dies still smeared the lights into white blotches ->
    # dielectric dark Si (specular ~4 %: the black card -> near black, the strip -> one band), roughness 0.03-0.07
    b.inputs["Metallic"].default_value = 0.0
    # try 2: dielectric with the R22 albedos (0.2 / 0.07 / 0.34) still read light grey under the stage key -> x0.2 (x0.3 still mid-grey at f92 / f143)
    for n in m.node_tree.nodes:
        if n.type == "MIX" and getattr(n, "data_type", "") == "RGBA":
            for key in ("A", "B"):
                if not n.inputs[key].is_linked:
                    c = n.inputs[key].default_value
                    n.inputs[key].default_value = (c[0] * 0.2, c[1] * 0.2, c[2] * 0.2, 1)
    for n in m.node_tree.nodes:
        if n.type == "MAP_RANGE":
            n.inputs["To Min"].default_value = 0.03
            n.inputs["To Max"].default_value = 0.07
    # try 4: the R22 x4 WaferGrazeR14 strip lit a second, diffuse light stripe across the disc (row profile 136 vs 75
    # base next to the 230 band) -> back below R21 strength (x0.25 of R22 = R21, then x0.5)
    g = bpy.data.objects.get("WaferGrazeR14")
    if g is not None:
        g.data.energy *= 0.125
    if shot == "B8_03M":
        return      # PIP pass (reticle stage; the wafer is not in its crop): material only, no card / light changes
    cam = sc.camera
    f0 = sc.frame_current
    sc.frame_set(round(sc.frame_end * 0.55))
    wc = w.matrix_world.translation.copy()
    bb = [w.matrix_world @ Vector(c) for c in w.bound_box]
    wz = max(p.z for p in bb)
    wc.z = wz
    co = cam.matrix_world.translation.copy()
    sc.frame_set(f0)
    v = (wc - co).normalized()
    r = Vector((v.x, v.y, -v.z))                     # mirrored view ray off the horizontal wafer
    cpos = wc + r * CARD_D
    rot = (-r).to_track_quat("Z", "Y").to_euler()
    black = _emit_mat("WaferEnvBlackR23", (0, 0, 0), 0.0)
    card = _plane("WaferEnvCardR23", CARD_S, CARD_S, black)
    card.location = cpos
    card.rotation_euler = rot
    _only_glossy(card)
    # one narrow strip, horizontal across the card (-> one band across the disc), slightly off-centre
    strip = _plane("WaferEnvStripR23", CARD_S * 0.9, 0.034, _emit_mat("WaferEnvStripR23", (0.92, 0.94, 1.0), 90.0))
    strip.parent = card
    strip.location = (0.0, 0.09, 0.005)
    _only_glossy(strip)
    # lights would still put extra specular spots on the polished disc through MIS: only the grazing card stays
    for o in bpy.data.objects:
        if o.type == "LIGHT":
            d = (o.matrix_world.translation - wc)
            if d.z > 0:   # try 4: a second grey band came from a light outside the 0.3 mirror cone -> all lights above
                try:
                    o.visible_glossy = False
                except AttributeError:
                    pass
    print("[cut_2b_r23_wafer] card at", tuple(round(x, 2) for x in cpos), "r", tuple(round(x, 2) for x in r))
