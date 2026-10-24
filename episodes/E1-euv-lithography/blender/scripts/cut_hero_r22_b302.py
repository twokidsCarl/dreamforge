"""R22 cuth B3_02 (R22_ROOT_CAUSE row 4; R21: "收集镜本身只占画面约 1/6" + R21 cuth risks: cone volume over the dish reflection,
laser across the dish, scaled holder bolts floating).

- ONLY the mirror body (coated face + substrate + back rings / cooling channels) is scaled x DISH_S about the vertex. The holder
  (flange ring, 24 bolts, support spokes) is NOT scaled: every holder vertex is moved radially by the rim growth
  (R_new - R_old) and along the axis onto the new rim plane, so the parts keep their size and sit on the new rim.
- the reflected cone is rebuilt from the bigger rim onto the same IF, but its VOLUME starts CONE_GAP m in front of the rim
  plane and fades in over the next RAMP m (density gradient), so no violet volume lies over the dish face.
- the CO2 laser line (hole -> plasma) is hidden: at any view >= 45 deg off the dish axis it projects across the dish face.
- dish face: bright high-reflective metal (no emission / violet), grazing highlights from the existing DishGraze lights.
- camera: R20 opening kept, push-in to a 3/4 view ~50 deg off the dish axis (cone axis ~80 deg to the line of sight).
"""
import math

import bpy
from mathutils import Matrix, Vector

DISH_S = [1.8]
CONE_GAP = [0.5]
RAMP = [1.8]


def post(sc):
    import build_cutaway_r2 as B
    import kit_r2 as K
    import beam_r21 as R21B
    from cut_hero_r21 import _islands, _xform_islands, _cam_tgt
    n = sc.frame_end
    S = DISH_S[0]
    c = B.COLL.copy()
    R0, f0 = 0.68, 0.42
    rim0 = c.x + R0 * R0 / (4 * f0)
    rim1 = c.x + (rim0 - c.x) * S
    dR = R0 * (S - 1)
    M_s = Matrix.Translation(c) @ Matrix.Scale(S, 4) @ Matrix.Translation(-c)

    def body(pts):
        cx = sum(p.x for p in pts) / len(pts)
        return all(-8.45 < p.x < -7.3 and math.hypot(p.y, p.z - c.z) < 0.75 for p in pts) and cx < -7.5
    for nm in ("R2_mirror", "R2_substrate", "R2_gold", "R2_copper"):
        ob = bpy.data.objects.get(nm)
        if ob is not None and ob.type == "MESH":
            print("[r22h] dish body scaled:", nm, _xform_islands(ob, body, M_s))

    # holder: not scaled - radial offset dR + axial shift onto the new rim plane (rigid per vertex)
    def holder(pts):
        return all(-8.7 < p.x < -7.3 and math.hypot(p.y, p.z - c.z) < 1.3 for p in pts)
    for nm in ("R2_flange", "R2_bolt", "R2_mount"):
        ob = bpy.data.objects.get(nm)
        if ob is None or ob.type != "MESH":
            continue
        mw = ob.matrix_world
        mwi = mw.inverted()
        me = ob.data
        k = 0
        for isl in _islands(me):
            pts = [mw @ me.vertices[i].co for i in isl]
            if not holder(pts):
                continue
            ctr = sum(pts, Vector()) / len(pts)
            rc = math.hypot(ctr.y, ctr.z - c.z)
            for i, p in zip(isl, pts):
                ry, rz = p.y, p.z - c.z
                r = math.hypot(ry, rz)
                if nm == "R2_mount":          # spokes: the dish end (near the vertex) follows the bigger back
                    w = max(0.0, min(1.0, (p.x - (-8.5)) / (c.x - 0.15 - (-8.5))))
                    if r > 1e-6:
                        s_ = (r + dR * 0.9 * w) / r
                        q = Vector((p.x - 0.05 * w, ry * s_, c.z + rz * s_))
                    else:
                        q = p
                elif nm == "R2_bolt":         # bolt islands: rigid translation (no scaling)
                    if rc > 1e-6:
                        q = p + Vector((rim1 - rim0, ctr.y / rc * dR, (ctr.z - c.z) / rc * dR))
                    else:
                        q = p
                else:                         # flange ring: radius + dR, same thickness
                    s_ = (r + dR) / r if r > 1e-6 else 1.0
                    q = Vector((p.x + rim1 - rim0, ry * s_, c.z + rz * s_))
                me.vertices[i].co = mwi @ q
            k += 1
        me.update()
        print("[r22h] holder re-placed:", nm, k)

    # laser hidden (would cross the dish face at a >= 45 deg view)
    for nm in ("LaserCore", "LaserHalo"):
        ob = bpy.data.objects.get(nm)
        if ob is not None:
            ob.hide_render = True
            ob.hide_viewport = True

    # cone: volume from CONE_GAP in front of the rim, density ramp over RAMP
    for ob in list(bpy.data.objects):
        if ob.name.startswith(("CollectConeR18", "CollectConeR21")):
            bpy.data.objects.remove(ob)
    Rr = 0.58 * S
    a0 = Vector((rim1 + 0.01, 0, c.z))
    L = (B.IF - a0).length
    t0 = CONE_GAP[0] / L
    a = a0.lerp(B.IF, t0)
    ra = Rr * (1 - t0) + 0.012 * t0
    objs, mats = R21B.cone(a, B.IF, ra, 0.012, "CollectConeR22", k=0.55, seg=64)
    for m in mats:
        _ramp(m, a, B.IF, RAMP[0])
    for o in objs:                    # the dish does not mirror the cone volume (no violet over the dish face)
        try:
            o.visible_glossy = False
        except AttributeError:
            pass
    R21B.key_vis(objs, mats, n, 0.0, 0.62, ramp=12, dim=0.5)

    # dish face: bright high-reflective metal, no emission / violet
    m = bpy.data.materials.get("CollectorDarkML_R20")
    if m is not None:
        bs = next(nd for nd in m.node_tree.nodes if nd.type == "BSDF_PRINCIPLED")
        bs.inputs["Base Color"].default_value = (0.82, 0.83, 0.86, 1.0)
        bs.inputs["Roughness"].default_value = 0.06
        bs.inputs["Metallic"].default_value = 1.0
        for nm_ in ("Emission Strength",):
            if nm_ in bs.inputs:
                bs.inputs[nm_].default_value = 0.0

    # camera: 3/4 view ~50 deg off the dish axis, push-in
    cam, tgt = _cam_tgt(sc)
    cam.animation_data_clear()
    if tgt is not None:
        tgt.animation_data_clear()
    cam.data.lens = CAM_LENS[0]
    T = Vector((-7.85, 0.0, 2.30))
    K.key_path(cam, tgt, [(1, (-4.15, -4.35, 3.45), (-6.2, 0.0, 2.42)),
                          (round(n * 0.5), tuple(T + DIR[0] * (DIST[0] * 1.45)), tuple(T + Vector((0.25, 0, 0)))),
                          (round(n * 0.85), tuple(T + DIR[0] * DIST[0]), tuple(T)),
                          (n, tuple(T + DIR[0] * (DIST[0] * 0.98)), tuple(T))])
    cam.data.dof.aperture_fstop = 11.0


CAM_LENS = [24]
DIR = [Vector((0.70, -0.62, 0.35)).normalized()]
DIST = [2.95]


def _ramp(m, a, b, ramp):
    """multiply both volume densities by smoothstep(0..1) of the distance along a->b over the first `ramp` metres"""
    nt = m.node_tree
    try:
        m.cycles.homogeneous_volume = False
    except AttributeError:
        pass
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    d = (Vector(b) - Vector(a)).normalized()
    dot = nt.nodes.new("ShaderNodeVectorMath"); dot.operation = "DOT_PRODUCT"
    sub = nt.nodes.new("ShaderNodeVectorMath"); sub.operation = "SUBTRACT"
    nt.links.new(geo.outputs["Position"], sub.inputs[0])
    sub.inputs[1].default_value = Vector(a)
    nt.links.new(sub.outputs[0], dot.inputs[0])
    dot.inputs[1].default_value = d
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.interpolation_type = "SMOOTHSTEP"
    mr.inputs["From Min"].default_value = 0.0
    mr.inputs["From Max"].default_value = ramp
    nt.links.new(dot.outputs["Value"], mr.inputs["Value"])
    for nd in list(nt.nodes):
        if nd.type == "MATH" and nd.operation == "MULTIPLY" and nd.outputs[0].links:
            lk = nd.outputs[0].links[0]
            to = lk.to_socket
            mul = nt.nodes.new("ShaderNodeMath"); mul.operation = "MULTIPLY"
            nt.links.remove(lk)
            nt.links.new(nd.outputs[0], mul.inputs[0])
            nt.links.new(mr.outputs["Result"], mul.inputs[1])
            nt.links.new(mul.outputs[0], to)
