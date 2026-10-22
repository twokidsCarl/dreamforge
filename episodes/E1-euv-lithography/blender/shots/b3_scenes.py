"""B3 — collector to intermediate focus (F56). Variants:

  burst    B3_01  a spherical shell of violet rays leaving the plasma in every direction
  focus    B3_05  hundreds of rays: focus 1 -> collector -> focus 2, pulsed several times
  handoff  B3_06  xray: vessel neck docking into the much larger scanner body at IF
  nave     B3_07  push through the IF aperture into a dark, clean vacuum with mirror edges lit
"""
import math
import random

import bpy
from mathutils import Vector

import build_source as S
import build_vacuum as V
import common as C
import materials as M
import sample_b1 as B
import styles

FRAMES = 260
VIOLET = (0.62, 0.45, 1.0)


def _curve(name, pts, mat, radius=0.012):
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = radius
    sp = cu.splines.new("POLY")
    sp.points.add(len(pts) - 1)
    for i, p in enumerate(pts):
        sp.points[i].co = (*p, 1)
    ob = bpy.data.objects.new(name, cu)
    bpy.context.scene.collection.objects.link(ob)
    ob.data.materials.append(mat)
    styles.tag(ob, "rays")
    return ob


def burst(sc, rnd, n=300):
    """Repeated bursts: each is a spherical shell of short violet dashes flying out of the plasma (start follows
    end), so the light visibly spreads in every direction instead of filling the frame with full-length rays
    (the old 420 full rays from 2 units away washed frames 13-34 into a flat lavender field)."""
    core = M.emission("Core", (0.75, 0.55, 1.0), 9.0)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.16, location=(0, 0, 0))
    ob = bpy.context.object
    ob.data.materials.append(core)
    styles.tag(ob, "emitter")
    mat = M.emission("Ray", VIOLET, 2.0)
    for b, f_b in enumerate((2, 48, 92)):
        M.set_emission_strength(core, f_b, 9.0)
        M.set_emission_strength(core, f_b + 2, 22.0)
        M.set_emission_strength(core, f_b + 12, 9.0)
        for k in range(n):
            d = Vector((rnd.gauss(0, 1), rnd.gauss(0, 1), rnd.gauss(0, 1))).normalized()
            r = _curve(f"Ray{b}_{k}", [(0, 0, 0), tuple(d * 40)], mat, radius=0.007)
            f0 = f_b + int(rnd.uniform(0, 4))
            life = int(rnd.uniform(80, 100))
            for attr, keys in (("bevel_factor_end", ((1, 0.0), (f0, 0.0), (f0 + life, 1.0))),
                               ("bevel_factor_start", ((1, 0.0), (f0 + 4, 0.0), (f0 + 4 + life, 1.0)))):
                for f, v in keys:
                    setattr(r.data, attr, v)
                    r.data.keyframe_insert(attr, frame=f)
            for fc in C.fcurves(r.data.animation_data.action):
                for kp in fc.keyframe_points:
                    kp.interpolation = "LINEAR"
    B._camera("CamB3_01", [(1, (0, 0, 0), (1.4, 5.0, 1.2), 18, 11.0),
                           (141, (0, 0, 0), (2.8, 10.5, 2.4), 18, 11.0)])


def focus(sc, rnd):
    S.collector()
    S.collector_housing()
    rays, mat = S.light_rays(n=220, seed=9)
    for r in rays:
        r.data.bevel_factor_end = 0.0
    # the plasma at focus 1 and the spot at focus 2 never go fully dark between pulses (an unlit emitter is a
    # black dot in front of the rays)
    core = M.emission("Core", (0.85, 0.75, 1.0), 3.0)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.18, location=(0, 0, 0))
    ob = bpy.context.object
    ob.data.materials.append(core)
    styles.tag(ob, "emitter")
    dot = M.emission("IFDot", (0.7, 0.55, 1.0), 2.0)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.14, location=(S.IF_X, 0, 0))
    ifo = bpy.context.object
    ifo.data.materials.append(dot)
    styles.tag(ifo, "emitter")
    # each pulse is a shell of light that leaves focus 1, bounces off the mirror and closes on focus 2 as a short
    # travelling dash (start follows end), so the pulses read one by one instead of piling up into a static fan
    pulses = [3, 22, 37, 49, 59, 68]              # repeated pulses, accelerating; the last lands at ~79 of 84
    for r in rays:
        for f0 in pulses:
            for attr, keys in (("bevel_factor_end", ((f0, 0.0), (f0 + 10, 1.0))),
                               ("bevel_factor_start", ((f0 + 3, 0.0), (f0 + 14, 1.0)))):
                for f, v in keys:
                    setattr(r.data, attr, v)
                    r.data.keyframe_insert(attr, frame=f)
        for fc in C.fcurves(r.data.animation_data.action):
            pts = fc.keyframe_points
            for k, kp in enumerate(pts):
                # travel linearly; after a pass jump straight back to 0 (hidden: start == end) for the next pulse
                kp.interpolation = "LINEAR" if k % 2 == 0 else "CONSTANT"
    for f0 in pulses:
        M.set_emission_strength(core, f0, 3.0)
        M.set_emission_strength(core, f0 + 1, 30.0)
        M.set_emission_strength(core, f0 + 6, 4.0)
        M.set_emission_strength(dot, f0 + 8, 3.0)
        M.set_emission_strength(dot, f0 + 11, 22.0)
        M.set_emission_strength(dot, f0 + 17, 5.0)
    s = mat.node_tree.nodes["Emission"].inputs["Strength"]
    s.default_value = 1.4
    # same framing as the B3_04 blueprint it cuts from: a side view with focus 1 at x = 602 px and focus 2 at
    # 1318 px of 1920, the axis 20 px below the centre (blueprint: c = 358 px for c = 7 units -> 51.2 px/unit;
    # 1920 * lens / (36 * D) = 51.2 with lens 35 -> D = 36.5)
    c = S.IF_X / 2
    B._camera("CamB3_05", [(1, (c, 0, 0.39), (c, -36.5, 0.39), 35, 11.0),
                           (90, (c, 0, 0.39), (c, -36.5, 0.39), 35, 11.0)])


def handoff(sc, rnd):
    V.source_vessel()
    S.collector()
    S.collector_housing()
    rays, rmat = S.light_rays(n=120, seed=4)
    S.intermediate_focus()
    # the plasma at focus 1 (storyboard: 焦点① 处是等离子体): a saturated violet core with a soft halo, so it
    # reads on the light x-ray backdrop instead of clipping to a white dot
    core = M.emission("PlasmaCoreB3", (0.5, 0.2, 1.0), 4.0)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.38, segments=32, ring_count=16, location=(0, 0, 0))
    ob = bpy.context.object
    ob.name = "PlasmaCore"
    ob.data.materials.append(core)
    styles.tag(ob, "emitter")
    halo = M.volume_glow("PlasmaHaloB3", (0.45, 0.2, 1.0), density=0.6, emission_strength=3.0, falloff=True)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=1.4, location=(0, 0, 0))
    ob = bpy.context.object
    ob.name = "PlasmaHalo"
    ob.data.materials.append(halo)
    styles.tag(ob, "emitter")
    # past the IF the light carries on, diverging, into the scanner (each ray continues straight through focus 2)
    f2 = Vector((S.IF_X, 0, 0))
    for k, r in enumerate(rays[::2]):
        p = Vector(r.data.splines[0].points[1].co[:3])
        d = (f2 - p).normalized()
        _curve(f"OnwardRay{k}", [tuple(f2), tuple(f2 + d * 5.0)], rmat, radius=0.018)
    # the scanner body the neck docks into (stylised, generic shell): its face flush with the end of the neck
    # (x = 14.4, build_vacuum.source_vessel x_end), much larger than the vessel
    bpy.ops.mesh.primitive_cube_add(location=(14.4 + 24.0, 0, 6.0))
    body = bpy.context.object
    body.name = "ScannerBody"
    body.scale = (24.0, 22.0, 22.0)
    bev = body.modifiers.new("Bevel", "BEVEL")
    bev.width = 0.5
    bev.segments = 1
    body.data.materials.append(M.principled("ScannerPanel", (0.78, 0.8, 0.82), metallic=0.2, roughness=0.45))
    styles.tag(body, "shell")
    # the docking interface: a flange ring on the scanner face around the end of the neck, and panel seams
    steel = M.polished_steel("DockSteel", 0.25)
    bpy.ops.mesh.primitive_torus_add(major_radius=2.2, minor_radius=0.22, major_segments=96, minor_segments=12,
                                     location=(14.45, 0, 0), rotation=(0, math.pi / 2, 0))
    ob = bpy.context.object
    ob.name = "DockFlange"
    ob.data.materials.append(steel)
    styles.tag(ob, "structure")
    seam = M.principled("ScannerSeam", (0.25, 0.27, 0.3), roughness=0.5)
    for k, z in enumerate((-8.0, 6.0, 20.0)):                  # horizontal seams on the face and the near side
        for loc, sc_ in (((14.38, 0, z), (0.04, 21.5, 0.06)), ((38.4, -22.02, z), (23.5, 0.04, 0.06))):
            bpy.ops.mesh.primitive_cube_add(location=loc)
            sm = bpy.context.object
            sm.name = f"ScannerSeam{k}{loc[0]:.0f}"
            sm.scale = sc_
            sm.data.materials.append(seam)
            styles.tag(sm, "structure")
    # hold on focus 1 (first clause), travel along the axis to focus 2 (second), rise to the docking (third)
    B._camera("CamB3_06", [(1, (0.0, 0, 0), (5.5, -15.0, 4.5), 30, 11.0),
                           (66, (0.6, 0, 0), (6.5, -14.5, 4.4), 30, 11.0),
                           (120, (13.0, 0, 0), (17.0, -15.5, 5.0), 30, 11.0),
                           (213, (17.0, 0, 3.0), (4.0, -42.0, 21.0), 30, 11.0)])


HOLE_R, OFF_R = 0.25, 0.15          # IF aperture (stylised: its size is not public) and the eye's offset from the axis


def _bez(p0, p1, p2, p3, u):
    v = 1 - u
    return p0 * v ** 3 + p1 * 3 * v * v * u + p2 * 3 * v * u * u + p3 * u ** 3


def _nave_keys(BM, ax, up, cross, last=136):
    """CamB3_07 keyed on every frame from one 3D curve (per-axis Bezier keys bent the approach off the offset
    line and put the eye on the beam): a straight run along the axis, OFF_R off it, through the HOLE_R IF hole
    without slowing down, then one smooth swing out to a 3/4 view of the illuminator train."""
    IF, FOLD, F1 = Vector(BM.IF), Vector(BM.FOLD), Vector(BM.FACET1)
    t0, t1, f_a = 1.9, -0.12, cross + 3                     # axial distance from the IF (toward the source = +)
    speed = 2 * (t0 - t1) / (f_a - 1)                       # ease-in: t = t0 - (t0 - t1) u^2, slope at the end
    q0 = IF + up * OFF_R + ax * t1
    p_mid = FOLD + ax * 0.75 + Vector((0, -1.35, 0.15))
    p_end = Vector((2.65, -4.3, 2.75))
    seg1 = (q0, q0 - ax * speed * 3 + Vector((0, -0.15, 0)), p_mid + (q0 - p_end) * 0.2, p_mid)
    seg2 = (p_mid, p_mid + (p_end - q0) * 0.2, p_end + Vector((0.3, 0.8, -0.3)), p_end)
    aim_a, aim_mid, aim_end = IF - ax * 1.2, FOLD + (F1 - FOLD) * 0.3, Vector((1.9, 0.0, 2.0))
    keys = []
    for f in range(1, last + 1):
        if f <= f_a:
            u = (f - 1) / (f_a - 1)
            loc = IF + up * OFF_R + ax * (t0 - (t0 - t1) * u * u)
            aim = aim_a
        elif f <= 76:
            u = (f - f_a) / (76 - f_a)
            loc = _bez(*seg1, u)
            aim = aim_a.lerp(aim_mid, u * u * (3 - 2 * u))
        else:
            u = (f - 76) / (last - 76)
            ue = 1 - (1 - u) ** 2 * (1 - 0.5 * u) / 1.0 if u < 1 else 1.0
            loc = _bez(*seg2, ue)
            aim = aim_mid.lerp(aim_end, u * u * (3 - 2 * u))
        keys.append((f, tuple(aim), tuple(loc), 24, 5.6))
    return keys


def nave(sc, rnd):
    """B3_07: through the intermediate focus into the illuminator, as the real optics are laid out (the High-NA
    train from build_machine, after ZEISS 2024 s.13): small fold mirror, field facet mirror, pupil facet mirror,
    each lighting up as the beam turns on it. Only the mirrors and the light path are shown."""
    import build_machine as BM
    C.set_world(top=(0.010, 0.012, 0.020), horizon=(0.004, 0.005, 0.008), bottom=(0.001, 0.001, 0.002))
    path, pmat = BM.machine()
    # only the illuminator mirrors the beam actually turns on, and the reticle it ends on; the projection optics
    # below would be unlit clutter with no beam on them in this shot
    keep = ("FoldMirror", "Facet0", "Facet1", "Reticle", "LightPath")
    for ob in list(bpy.data.objects):
        if ob.type in ("MESH", "CURVE") and (not ob.name.startswith(keep) or ob.name.startswith("ReticleStage")):
            ob.hide_render = True
    # the light path is tagged `rays`, which the photoreal style hides: here it is the subject, so it is an emitter
    # (saturated violet at a moderate strength, so it does not clip to a white bar)
    styles.tag(path, "emitter")
    em = pmat.node_tree.nodes["Emission"]
    em.inputs["Color"].default_value = (0.36, 0.12, 1.0, 1.0)
    em.inputs["Strength"].default_value = 2.2
    path.data.bevel_depth = 0.02
    ax = Vector(BM.SRC_AXIS)                             # points from the IF back toward the source
    up = Vector((-ax.z, 0.0, ax.x))                      # perpendicular to the axis, in the optical plane
    rot = (-ax).to_track_quat("Z", "Y").to_euler()
    plate_mat = M.principled("Aperture", (0.05, 0.055, 0.065), metallic=0.85, roughness=0.3)
    bpy.ops.mesh.primitive_cylinder_add(radius=1.2, depth=0.06, vertices=128, location=BM.IF, rotation=rot)
    plate = bpy.context.object
    plate.name = "IFAperture"
    bpy.ops.mesh.primitive_cylinder_add(radius=HOLE_R, depth=0.5, vertices=96, location=BM.IF, rotation=rot)
    hole = bpy.context.object
    hole.hide_render = hole.hide_viewport = True
    bo = plate.modifiers.new("Hole", "BOOLEAN")
    bo.object = hole
    bo.operation = "DIFFERENCE"
    bev = plate.modifiers.new("Bevel", "BEVEL")
    bev.width = 0.008
    bev.segments = 2
    plate.data.materials.append(plate_mat)
    styles.tag(plate, "structure")
    glow = M.emission("IFPoint", (0.45, 0.2, 1.0), 12.0)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.03, location=BM.IF)
    gp = bpy.context.object
    gp.name = "IFPoint"
    gp.data.materials.append(glow)
    styles.tag(gp, "emitter")
    # the beam leaves the IF ahead of the camera and turns at each mirror; with the default RESOLUTION mapping a
    # POLY spline gives every PATH leg an equal share of the factor, so the head can be keyed at each bounce point
    n = len(BM.PATH) - 1
    i_if = BM.PATH.index(BM.IF)
    path.data.bevel_factor_start = i_if / n
    arrive = {BM.IF: 1, BM.FOLD: 30, BM.FACET1: 74, BM.FACET2: 98, BM.RETICLE: 116}
    for pt, f in arrive.items():
        path.data.bevel_factor_end = BM.PATH.index(pt) / n
        path.data.keyframe_insert("bevel_factor_end", frame=f)
    for fc in C.fcurves(path.data.animation_data.action):
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR"
    # each mirror lights up (a violet glint on its face and mount) the moment the beam reaches it
    for nm, pt, nxt in (("Fold", BM.FOLD, BM.FACET1), ("Facet0", BM.FACET1, BM.FACET2),
                        ("Facet1", BM.FACET2, BM.RETICLE), ("Reticle", BM.RETICLE, None)):
        prev = BM.PATH[BM.PATH.index(pt) - 1]
        nrm = (Vector(prev) - Vector(pt)).normalized()
        if nxt is not None:
            nrm = (nrm + (Vector(nxt) - Vector(pt)).normalized()).normalized()
        # a spot aimed at the mirror only (a point light leaked through the thin IF plate in EEVEE)
        bpy.ops.object.light_add(type="SPOT", location=tuple(Vector(pt) + nrm * 0.45),
                                 rotation=(-nrm).to_track_quat("-Z", "Y").to_euler())
        lt = bpy.context.object
        lt.name = f"Glint{nm}"
        lt.data.color = (0.55, 0.35, 1.0)
        lt.data.spot_size = math.radians(70)
        lt.data.spot_blend = 0.6
        lt.data.shadow_soft_size = 0.05
        lt["keep_light"] = True
        f = arrive[pt]
        for ff, e in ((1, 0.0), (f - 1, 0.0), (f + 3, 40.0), (136, 18.0)):
            lt.data.energy = e
            lt.data.keyframe_insert("energy", frame=max(1, ff))
    B._area("NaveKey", tuple(Vector(BM.FACET1) + Vector((1.0, -5.0, 3.0))), (0.95, 0, 0.2), 6, 160, (0.6, 0.7, 1.0))
    B._area("NaveRim", tuple(Vector(BM.IF) + ax * 2.5 + up * 2.0 + Vector((0, -1.5, 0))), (0.6, 0, 1.2), 3, 60,
            (0.55, 0.65, 1.0))
    # the eye threads the hole OFF_R off the axis (inside HOLE_R, never touching the plate), the beam running
    # just below the frame centre as a leading line; then it swings out to a 3/4 view of the illuminator train
    cross = 46
    cam = B._camera("CamB3_07", _nave_keys(BM, ax, up, cross))
    # once the eye is beside it, the aperture plate is only a dark slab cutting the frame: gone from frame 60
    for f, h in ((1, False), (60, True)):
        plate.hide_render = h
        plate.keyframe_insert("hide_render", frame=f)
    # the IF point dims as the eye passes close by it (close up it clipped to a white blob)
    # and is back once the eye has swung out, marking where the beam enters the illuminator
    for f, e in ((1, 12.0), (34, 12.0), (45, 2.5), (54, 2.5), (72, 10.0)):
        M.set_emission_strength(glow, f, e)
    cam.data.clip_start = 0.005
    cam.data.dof.use_dof = False
    # passing the light: a short lift of exposure, then back to the dark
    vs = sc.view_settings
    for f, ex in ((1, 0.4), (cross - 5, 0.4), (cross, 0.85), (cross + 10, 0.4)):
        vs.exposure = ex
        vs.keyframe_insert("exposure", frame=f)


def _scanner_glass():
    """B3_06: the scanner body as a darker, smoky glass (the plain ghost glass vanished into the grey x-ray
    backdrop, so the docking never read): translucent slate face-on, bright at grazing angles."""
    m = bpy.data.materials.new("ScannerSmoke")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.remove(nt.nodes["Principled BSDF"])
    lw = nt.nodes.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.25
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = (0.45, 0.45, 0.45, 1)
    ramp.color_ramp.elements[1].position = 1.0
    ramp.color_ramp.elements[1].color = (0.95, 0.95, 0.95, 1)
    body = nt.nodes.new("ShaderNodeBsdfPrincipled")
    body.inputs["Base Color"].default_value = (0.10, 0.12, 0.16, 1)
    body.inputs["Roughness"].default_value = 0.25
    body.inputs["Metallic"].default_value = 0.3
    transp = nt.nodes.new("ShaderNodeBsdfTransparent")
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(lw.outputs["Facing"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], mix.inputs["Fac"])
    nt.links.new(transp.outputs[0], mix.inputs[1])
    nt.links.new(body.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
    m.surface_render_method = "BLENDED"
    return m


def after_style(style, shot_id):
    """B3_05: the energy style draws structure as a faint blue rim; the collector must stay readable between the
    pulses, so its outline is a brighter metrology-cyan rim. B3_06: the scanner body in smoky glass."""
    if shot_id == "B3_06" and style == "xray":
        body = bpy.data.objects.get("ScannerBody")
        if body:
            styles._set_material(body, _scanner_glass())
    if shot_id == "B3_05" and style == "energy":
        rim = styles.dark_rim("CollectorRimB3", color=(0.15, 0.75, 1.0), strength=3.0)
        for ob in bpy.data.objects:
            if ob.name.startswith(("Collector", "CollectorRing")) and ob.type == "MESH":
                styles._set_material(ob, rim)


def build(variant="burst", seed=31):
    sc = C.reset_scene(FRAMES)
    C.set_world(top=(0, 0, 0), horizon=(0, 0, 0), bottom=(0, 0, 0))
    C.set_color_management(exposure=0.4)
    rnd = random.Random(seed)
    {"burst": burst, "focus": focus, "handoff": handoff, "nave": nave}[variant](sc, rnd)
    return sc
