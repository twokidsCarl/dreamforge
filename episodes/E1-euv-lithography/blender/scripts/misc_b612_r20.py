"""R20 B6_12 (root cause #4, R19 review B6_12 #1-#3, F 80): scanner pose.

R19 review: 「卡盘吸住掩模背面，图形面朝下对着光学系统」「25 % 和 55 % 帧只能看到框」「掩模台缺少细节…加真空吸盘、定位销、
气路接头」. The R19 assembly (chuck, mask, pellicle frame, membrane, section line, gap rule, clamp jaws, stage carriage) is
rotated 180 deg about the world Y axis through z = PIVOT, so the chuck holds the mask BACK side from above and the pattern
face + pellicle frame + membrane hang BELOW the mask, facing the optics. The camera looks UP from below at a grazing angle onto
the cut-open frame edge. The light-linked grazing strip light is re-solved per key frame by mirror geometry so its specular band
crosses the membrane in every beat (25 / 55 / 85 %). The chuck gets three nameable part kinds: vacuum pads with suction
grooves, locating pins, and gas / vacuum fittings with hoses. Called from r2_misc._pellicle only when B6_12 is in R20_SHOTS.
"""
import math

import bpy
from mathutils import Matrix, Quaternion, Vector

import kit_r2 as K

PIVOT = 1.2


def _flip_matrix():
    return Matrix.Translation((0, 0, PIVOT)) @ Matrix.Rotation(math.pi, 4, "Y") @ Matrix.Translation((0, 0, -PIVOT))


def apply(sc, n, cam, tgt, anchors):
    M = _flip_matrix()
    keep = {"Floor"}
    for ob in list(sc.objects):
        if ob.type != "MESH" or ob.name in keep or ob.parent is not None:
            continue
        ob.matrix_world = M @ ob.matrix_world
    fl = bpy.data.objects.get("Floor")
    if fl is not None:                                   # camera looks up: floor would only block the under-lights
        fl.hide_render = True
    # membrane plane / mask faces after the flip (R19 values: film z 0.207, pattern face 0.1535, chuck top 0.088+)
    z_film = 2 * PIVOT - 0.207
    # under-lights: mirror the R19 studio rig through the same transform (they light the pattern face + frame from below)
    for nm, tgt0 in (("Key", (0, 0, 0.3)), ("Fill", (0, 0, 0.3)), ("Rim", (0, 0, 0.3))):
        o = bpy.data.objects.get(nm)
        if o is None:
            continue
        p = M @ o.location
        t = M @ Vector(tgt0)
        o.location = p
        o.rotation_euler = (t - p).to_track_quat("-Z", "Y").to_euler()
    # membrane sheen a little stronger (Fresnel-only, still no base reflectance -> no glass lid)
    mem = bpy.data.materials.get("Membrane")
    if mem is not None:
        for nd in mem.node_tree.nodes:
            if nd.type == "MATH" and nd.operation == "MULTIPLY_ADD":
                nd.inputs[1].default_value = 0.2
            if nd.type == "BSDF_GLOSSY":
                nd.inputs["Roughness"].default_value = 0.05   # soft-edged sheen band, pattern still reads through
    # camera: from below, grazing up-angle, push to the cut-open frame edge (notch now at x -0.40..-0.18, y -0.53)
    for ob in (cam, tgt):
        ob.animation_data_clear()
    keys = [(1, (1.5, -3.4, 1.32), (-0.05, 0.1, 2.58)),
            (round(n * 0.55), (1.25, -2.6, 1.55), (-0.18, -0.2, 2.50)),
            (n, (0.72, -1.95, 1.80), (-0.27, -0.36, 2.32))]
    K.key_path(cam, tgt, keys)
    if cam.data.dof.use_dof:
        cam.data.dof.aperture_fstop = 4.0
    # grazing strip: per key frame put the light where the camera's mirror image through the film plane sees it
    sw = bpy.data.objects["Sweep"]
    sw.animation_data_clear()
    sw.data.size, sw.data.size_y, sw.data.energy = 0.32, 4.0, 15000      # broad soft band, not a thin white bar
    refl = {1: (0.30, 0.05), round(n * 0.25): (0.12, 0.0), round(n * 0.55): (-0.05, -0.1),
            round(n * 0.85): (-0.22, -0.2), n: (-0.28, -0.22)}
    for f, (rx, ry) in sorted(refl.items()):
        sc.frame_set(f)
        c = cam.matrix_world.translation.copy()
        cm = Vector((c.x, c.y, 2 * z_film - c.z))
        r = Vector((rx, ry, z_film))
        d = (r - cm).normalized()
        L = r + d * 2.6
        sw.location = L
        q = (r - L).to_track_quat("-Z", "Y") @ Quaternion((0, 0, 1), math.radians(32))   # band runs diagonally
        sw.rotation_euler = q.to_euler()
        sw.keyframe_insert("location", frame=f)
        sw.keyframe_insert("rotation_euler", frame=f)
    sc.frame_set(1)
    # R19 clamp-jaw arms + carriage would now hang BEHIND / below the mask in screen (far objects drop toward the
    # horizon when looking up) -> replaced by a stage block ABOVE the chuck (the chuck hangs from the reticle stage)
    for nm in ("ClampJawsR19", "StageCarriageR19"):
        o = bpy.data.objects.get(nm)
        if o is not None:
            o.hide_render = True
    stg = K.MB()
    stg.box((0, 0.2, 2 * PIVOT + 0.14), (2.3, 2.2, 0.28))
    for sx in (-1, 1):
        stg.box((sx * 0.98, 0.2, 2 * PIVOT + 0.36), (0.16, 3.2, 0.16))       # linear-motor rails over the stage
    stg.obj("ReticleStageR20", K.mat("StageAnodR20", (0.20, 0.22, 0.27), metal=0.85, rough=0.34, brushed=0.2), bevel=0.01)
    _chuck_parts()
    K.anchors("B6_12", {k: M @ Vector(v) for k, v in anchors.items()})


def _chuck_parts():
    """Chuck (now above the mask, bottom face z 2*PIVOT-0.088 = 2.312, 1.66 m square; mask 1.52 m square below it)."""
    zc = 2 * PIVOT - 0.088                    # chuck bottom face (holds the mask back side)
    zt = 2 * PIVOT                            # chuck top
    zm = 2 * PIVOT - 0.1535                   # pattern face (mask bottom)
    pads, grv, pins, fit, hose = K.MB(), K.MB(), K.MB(), K.MB(), K.MB()
    # vacuum pads on the chuck rim around the mask, each with a dark suction groove ring + centre port
    rim = 0.795
    spots = [(x, -rim) for x in (-0.6, -0.05, 0.55)] + [(x, rim) for x in (-0.6, 0.55)] + \
            [(sx * rim, y) for sx in (-1, 1) for y in (-0.45, 0.45)]
    for (x, y) in spots:
        pads.cyl((x, y, zc - 0.006), 0.03, 0.012, seg=24)
        grv.ring((x, y, zc - 0.0125), 0.022, 0.016, 0.002, seg=24)
        grv.cyl((x, y, zc - 0.0125), 0.006, 0.002, seg=12)
    # suction grooves: dark lines on the chuck bottom rim just outside the mask edge
    for (cx, cy, sx, sy) in [(0, -0.815, 1.6, 0.006), (0, 0.815, 1.6, 0.006), (0.815, 0, 0.006, 1.6), (-0.815, 0, 0.006, 1.6)]:
        grv.box((cx, cy, zc - 0.001), (sx, sy, 0.002))
    # locating pins: polished steel pins hanging from the chuck, touching the mask edges (2 front + 1 right side)
    for (x, y) in ((0.35, -0.772), (0.65, -0.772), (0.772, 0.2)):
        pins.cyl((x, y, zc - 0.05), 0.011, 0.1, seg=16)
        pins.sphere((x, y, zc - 0.1), 0.011, 12)
        pins.cyl((x, y, zc - 0.006), 0.02, 0.012, seg=16)
    # gas / vacuum fittings on the chuck front + right faces, hoses running back up to the stage
    for x in (0.15, 0.4, 0.65):
        p0 = Vector((x, -0.83, zt - 0.044))
        fit.box(p0 + Vector((0, -0.012, 0)), (0.05, 0.024, 0.05))                     # hex body (block)
        fit.cyl(p0 + Vector((0, -0.045, 0)), 0.014, 0.045, rot=(math.radians(90), 0, 0), seg=16)   # barb
        fit.cyl(p0 + Vector((0, -0.035, 0)), 0.02, 0.012, rot=(math.radians(90), 0, 0), seg=6)     # nut
        hose.path([p0 + Vector((0, -0.06, 0)), p0 + Vector((0, -0.16, 0.03)), p0 + Vector((0.05, -0.22, 0.2)),
                   p0 + Vector((0.12, -0.2, 0.9))], 0.013, seg=12)
    for y in (-0.3, 0.1):
        p0 = Vector((0.83, y, zt - 0.044))
        fit.box(p0 + Vector((0.012, 0, 0)), (0.024, 0.05, 0.05))
        fit.cyl(p0 + Vector((0.045, 0, 0)), 0.014, 0.045, rot=(0, math.radians(90), 0), seg=16)
        fit.cyl(p0 + Vector((0.035, 0, 0)), 0.02, 0.012, rot=(0, math.radians(90), 0), seg=6)
        hose.path([p0 + Vector((0.06, 0, 0)), p0 + Vector((0.16, 0.02, 0.03)), p0 + Vector((0.22, 0.06, 0.2)),
                   p0 + Vector((0.2, 0.15, 0.9))], 0.013, seg=12)
    pads.obj("VacPadsR20", K.mat("VacPadR20", (0.06, 0.065, 0.07), rough=0.75), bevel=0.002)
    grv.obj("SuctionGrooveR20", K.mat("GrooveR20", (0.01, 0.01, 0.012), rough=0.9))
    pins.obj("LocPinsR20", K.mat("PinSteelR20", (0.72, 0.72, 0.74), metal=1.0, rough=0.15))
    fit.obj("GasFittingsR20", K.mat("FittingBrassR20", (0.72, 0.6, 0.38), metal=1.0, rough=0.25), bevel=0.002)
    hose.obj("GasHosesR20", K.mat("HosePUR20", (0.18, 0.4, 0.7), rough=0.35))
