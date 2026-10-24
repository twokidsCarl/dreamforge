"""R23 B6_12 (R23_ROOT_CAUSE row 1 material + hero part, row 2 camera motion). Owned by the misc sub-agent.

R22 review: 「pellicle 在主画面几乎看不见，靠第 3 帧放大框…才讲清」「灰色平底背景无景深」. Layered on R20 + R21 (scanner pose,
black anodised frame, cut-section magnifier kept; nothing the BRIEF names is deleted). Not repeating the R22 grey haze.
- membrane = glossy film: transparent ~98.5 % + GGX glossy rough 0.02 weighted by Fresnel (no base sheen, not milky),
  haze 0.015 DARK diffuse.
- ONE narrow grazing band: the light-linked R19 'Sweep' strip (membrane-only receiver) made thin + long (0.03 x 5 m) and
  re-solved per frame by mirror geometry so its specular line crosses the film and sweeps across it over the shot.
- frame bar made a touch darker (black edge).
- dark machine cavity instead of the flat grey studio: camera-only dark enclosure + 3 depth layers (near alignment head,
  mid guide rails with vacuum ports, far rails / ports on the cavity wall).
- row 2: truck (lateral) + push, 55 % pose unchanged; focus pull film edge -> mask pattern.
"""
import math

import bpy
from mathutils import Matrix, Quaternion, Vector

import kit_r2 as K

HAZE = 0.015
BAND_W, BAND_L, BAND_E = 0.03, 5.0, 20000.0
FRES_W = 0.3     # R23 smoke: full Fresnel reflected the grey studio at grazing view -> film read as an opaque grey slab
JOB = (36, 80, 124)
ALIGN_XY = ((1.55, -0.95),)   # near layer: one alignment head on the camera side (R23 smoke: more heads occluded the mask)


def _membrane_mat():
    m = bpy.data.materials.new("MembraneR23")
    m.use_nodes = True
    nt = m.node_tree
    nn, l = nt.nodes, nt.links
    for x in list(nn):
        if x.type != "OUTPUT_MATERIAL":
            nn.remove(x)
    out = next(x for x in nn if x.type == "OUTPUT_MATERIAL")
    tr = nn.new("ShaderNodeBsdfTransparent")
    tr.inputs["Color"].default_value = (0.985, 0.985, 0.985, 1)
    gl = nn.new("ShaderNodeBsdfGlossy")
    gl.inputs["Roughness"].default_value = 0.02
    gl.inputs["Color"].default_value = (1, 1, 1, 1)
    fr = nn.new("ShaderNodeFresnel")
    fr.inputs["IOR"].default_value = 1.5
    m1 = nn.new("ShaderNodeMixShader")                 # transparent + specular (thin film, no refraction offset)
    fw = nn.new("ShaderNodeMath")
    fw.operation = "MULTIPLY"
    fw.inputs[1].default_value = FRES_W
    l.new(fr.outputs[0], fw.inputs[0])
    l.new(fw.outputs[0], m1.inputs["Fac"])
    l.new(tr.outputs[0], m1.inputs[1])
    l.new(gl.outputs[0], m1.inputs[2])
    df = nn.new("ShaderNodeBsdfDiffuse")
    df.inputs["Color"].default_value = (0.03, 0.032, 0.036, 1)   # dark haze, not milky
    m2 = nn.new("ShaderNodeMixShader")
    m2.inputs["Fac"].default_value = HAZE
    l.new(m1.outputs[0], m2.inputs[1])
    l.new(df.outputs[0], m2.inputs[2])
    l.new(m2.outputs[0], out.inputs["Surface"])
    return m


def _film_frame(mo):
    mw = mo.matrix_world
    vs = [mw @ v.co for v in mo.data.vertices]
    ctr = sum(vs, Vector()) / len(vs)
    nrm = (mw.to_3x3() @ Vector((0, 0, 1))).normalized()
    ax = (mw.to_3x3() @ Vector((1, 0, 0))).normalized()
    ay = nrm.cross(ax).normalized()
    ex = max(abs((v - ctr).dot(ax)) for v in vs)
    ey = max(abs((v - ctr).dot(ay)) for v in vs)
    return ctr, nrm, ax, ay, ex, ey


def _camera(sc, n, cam, tgt):
    for ob in (cam, tgt):
        ob.animation_data_clear()
    m = round(n * 0.55)
    keys = [(1, (2.15, -3.35, 1.30), (0.22, 0.1, 2.58)),            # truck: starts right of the R22 pose
            (m, (1.25, -2.6, 1.55), (-0.18, -0.2, 2.50)),             # 55 %: R22 pose (approved framing)
            (n, (0.30, -1.95, 1.80), (-0.40, -0.36, 2.32))]           # ends left + closer
    K.key_path(cam, tgt, keys)


def _focus(sc, n, cam, ctr, nrm, ax, ay, ex, ey):
    cd = cam.data
    cd.dof.use_dof = True
    cd.dof.focus_object = None
    cd.dof.aperture_fstop = 2.8
    film_near = ctr - ay * ey * 0.75                 # film just inside the near (cut-open) frame bar
    mask_pt = ctr - nrm * 0.055 + ay * ey * 0.2      # mask pattern face, behind the film (gap 0.055 above = -nrm)
    for f, p in ((1, film_near), (JOB[0], film_near), (JOB[2], mask_pt), (n, mask_pt)):
        sc.frame_set(f)
        cd.dof.focus_distance = (p - cam.matrix_world.translation).length
        cd.dof.keyframe_insert("focus_distance", frame=f)
    sc.frame_set(1)


def _band(sc, n, cam, ctr, nrm, ax, ay, ex, ey):
    sw = bpy.data.objects.get("Sweep")
    if sw is None:
        return
    sw.animation_data_clear()
    sw.data.size, sw.data.size_y, sw.data.energy = BAND_W, BAND_L, BAND_E
    sw.visible_camera = False
    step = max(1, n // 30)
    for f in list(range(1, n + 1, step)) + [n]:
        u = (f - 1) / max(1, n - 1)
        sc.frame_set(f)
        C = cam.matrix_world.translation.copy()
        # reflection point sweeps across the film (along ax), slightly off-centre in ay
        X = ctr + ax * ex * (0.55 - 1.1 * u) + ay * ey * 0.1
        d = (X - C).normalized()
        r = d - 2 * d.dot(nrm) * nrm
        E = X + r * 2.6
        sw.location = E
        along_cross = nrm.cross(r).normalized()                 # in film plane, perpendicular to plane of incidence
        z = (-r).normalized()                                   # light faces back to X (-Z of the light toward X)
        z = -z                                                  # area light emits along its -Z: local +Z away from X
        y = (along_cross - along_cross.dot(z) * z).normalized()  # long axis (size_y) across the film
        x = y.cross(z)
        rot = Matrix((x, y, z)).transposed().to_quaternion() @ Quaternion((0, 0, 1), math.radians(18))
        sw.rotation_euler = rot.to_euler()
        sw.keyframe_insert("location", frame=f)
        sw.keyframe_insert("rotation_euler", frame=f)
    sc.frame_set(1)


def _cavity(sc):
    dark = K.mat("CavityR23", (0.012, 0.013, 0.016), rough=0.85, spec=0.1)
    enc = K.MB()
    for (c, s) in [((0, 14, 2), (40, 0.2, 20)), ((0, -14, 2), (40, 0.2, 20)), ((-16, 0, 2), (0.2, 40, 20)),
                   ((16, 0, 2), (0.2, 40, 20)), ((0, 0, -4), (40, 40, 0.2)), ((0, 0, 9), (40, 40, 0.2))]:
        enc.box(c, s)
    eo = enc.obj("CavityShellR23", dark)
    for a in ("visible_diffuse", "visible_glossy", "visible_transmission", "visible_shadow", "visible_volume_scatter"):
        setattr(eo, a, False)                       # camera-only backdrop: the studio light rig stays as it was
    rail = K.mat("GuideRailR23", (0.22, 0.23, 0.26), metal=0.9, rough=0.3, brushed=0.2)
    blk = K.mat("RailCarR23", (0.05, 0.055, 0.065), metal=0.7, rough=0.35)
    port = K.mat("VacPortR23", (0.01, 0.01, 0.012), rough=0.9)
    ring = K.mat("VacPortRingR23", (0.5, 0.5, 0.53), metal=1.0, rough=0.2)
    rl, cr, pr, pg = K.MB(), K.MB(), K.MB(), K.MB()
    # mid (2-4 m beyond the mask): two guide rails along x with carriages, vacuum ports on a manifold bar
    # far (6-9 m): rails + port rows on the cavity wall
    for (y, z, L) in ((2.4, 2.28, 7.0), (3.0, 2.22, 7.0), (6.5, 2.12, 16.0), (8.5, 2.02, 20.0)):
        rl.box((0, y, z), (L, 0.09, 0.07))
        rl.box((0, y, z - 0.06), (L, 0.05, 0.06))
        for k in range(-3, 4):
            cr.box((k * L / 7.5 + 0.3, y, z + 0.06), (0.32, 0.16, 0.08))
    for (y, z, xs) in ((3.6, 2.16, [x * 0.55 - 2.2 for x in range(9)]), (9.5, 1.9, [x * 1.1 - 6.0 for x in range(12)])):
        rl.box((0, y + 0.08, z), (len(xs) * (xs[1] - xs[0]) + 0.4, 0.12, 0.22))      # manifold bar / wall band
        for x in xs:
            pr.cyl((x, y, z), 0.05 if y < 5 else 0.09, 0.02, rot=(math.radians(90), 0, 0), seg=20)
            pg.ring((x, y - 0.012, z), 0.075 if y < 5 else 0.13, 0.05 if y < 5 else 0.09, 0.012, rot=(math.radians(90), 0, 0), seg=24)
    rl.obj("GuideRailsR23", rail, bevel=0.004)
    cr.obj("RailCarsR23", blk, bevel=0.01)
    pr.obj("VacPortsR23", port)
    pg.obj("VacPortRingsR23", ring)
    # near layer: alignment heads (microscope barrels) hanging beside the reticle, close to the camera, defocused
    bl = K.area("CavityWashR23", (1.5, 0.5, 1.2), (0, 5.0, 2.2), 3.0, 260, (0.8, 0.86, 1.0))
    bl.visible_camera = False
    bl.visible_glossy = False
    try:
        rc = bpy.data.collections.new("CavityRecvR23")
        for nm in ("GuideRailsR23", "RailCarsR23", "VacPortsR23", "VacPortRingsR23"):
            rc.objects.link(bpy.data.objects[nm])
        bl.light_linking.receiver_collection = rc
    except Exception as e:
        print("[R23 B6_12] cavity light link failed", e)
    ah, ahl = K.MB(), K.MB()
    for (x, y) in ALIGN_XY:
        ah.cyl((x, y, 2.25), 0.11, 0.42, seg=32)
        ah.cyl((x, y, 2.01), 0.075, 0.08, seg=32)
        ah.box((x, y, 2.5), (0.3, 0.3, 0.1))
        ahl.cyl((x, y, 1.965), 0.055, 0.01, seg=32)
    ah.obj("AlignHeadsR23", K.mat("AlignHeadR23", (0.06, 0.065, 0.075), metal=0.8, rough=0.3), bevel=0.01)
    ahl.obj("AlignLensR23", K.mat("AlignLensR23M", (0.05, 0.08, 0.12), metal=0.0, rough=0.05, coat=1.0))


def _measure(sc, cam):
    from bpy_extras.object_utils import world_to_camera_view as w2c
    pts = {"film_c": None, "notch": Vector((-0.29, -0.53, 2.193)), "rail_mid": Vector((0, 2.4, 2.02)),
           "rail_far": Vector((0, 8.5, 1.35)), "ah0": Vector((1.55, -0.95, 2.01)), "ah1": Vector((0.95, -1.3, 2.01)), "ah2": Vector((-1.75, -0.75, 2.01))}
    mo = bpy.data.objects.get("Membrane")
    pts["film_c"] = _film_frame(mo)[0]
    sc.render.resolution_x, sc.render.resolution_y = 960, 540
    for f in JOB:
        sc.frame_set(f)
        s = []
        for k, p in pts.items():
            v = w2c(sc, cam, p)
            s.append(f"{k}=({v.x * 960:.0f},{(1 - v.y) * 540:.0f})")
        c = cam.matrix_world.translation
        print(f"[R23 B6_12] f{f} cam=({c.x:.2f},{c.y:.2f},{c.z:.2f}) focus={cam.data.dof.focus_distance:.2f} " + " ".join(s))
    sc.frame_set(1)


def post(sc):
    mo = bpy.data.objects.get("Membrane")
    if mo is None:
        print("[R23 B6_12] no Membrane - skipped")
        return
    n = sc.frame_end
    cam = sc.camera
    tgt = next(c.target for c in cam.constraints if c.type == "TRACK_TO")
    mo.data.materials[0] = _membrane_mat()
    zs = [v.co.z for v in mo.data.vertices]
    zf = max(zs) if abs(max(zs)) > abs(min(zs)) else min(zs)   # flat stretched film (no sag -> one straight band)
    zf = sorted(zs)[len(zs) // 2] if False else zf
    for v in mo.data.vertices:
        v.co.z = zf
    fr = bpy.data.objects.get("PelFrame")
    if fr is not None:
        fr.data.materials[0] = K.mat("FrameBlackR23", (0.012, 0.012, 0.015), metal=0.6, rough=0.32, brushed=0.3)
    sc.frame_set(1)
    ff = _film_frame(mo)
    _camera(sc, n, cam, tgt)
    _focus(sc, n, cam, *ff)
    _band(sc, n, cam, *ff)
    _cavity(sc)
    sc["hdri_strength"] = 0.6
    _measure(sc, cam)
    print(f"[R23 B6_12] film ctr {tuple(round(c, 3) for c in ff[0])} nrm {tuple(round(c, 2) for c in ff[1])} n={n}")
