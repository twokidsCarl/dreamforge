"""C — the assembly long take, on the High-NA whole-machine layout (build_machine; source unit on +x). Variants:

  assemble  C_01  clay: the six modules float apart, fly in and lock together; orbit, push to the source drum
  ride      C_03  xray: the light leaves the collector, through the IF and the illuminator onto the mask (arc slit)
            C_04  energy: down through the projection optics to the wafer; stages scan 8:1; latent field
            C_05  energy: fast pull-back to the whole machine, the light path as one glowing nerve
  pulses    C_06  energy: flashes run plasma -> wafer, faster and faster until they fuse into one band
  accents   C_08  xray: source, mirrors, mask, stages light up in voice-over order, then one beam threads them
            C_09  xray: each module's little axis jitters, then all snap to one shared origin and grid
  heart     C_10  energy: the path beats like a heart, fades, an ember left at the plasma (centred for D_08)

Beats are keyed to the narration (storyboard.timed.yaml cues + word timestamps of the VO track). The light path
grows by length (bevel mapping SPLINE), so "reaches point i" is _frac(i). Illustrative layout, not the ASML exterior.

Sources for the details drawn here (research/visual/CD_sources.md):
- slit at the reticle 104 x 12.8 mm, curved; at the wafer a 26 x 1.6 mm arc; magnification 1/8 in scan, 1/4 across
  [ZEISS/ASML, Wischmeier et al., EUVL Workshop 2021, slide 11] -> reticle stroke 8x the wafer stroke
- one EXE exposure field 26 x 16.5 mm ("half field") [ASML, van Schoot, EUVL Workshop 2022, slide 12]
- drive laser through the collector's central aperture [Fomenkov et al. 2017 p.176]
- facet count is not public: facets are drawn as a texture, never counted, labelled 示意 on screen
"""
import math
import random

import bmesh
import bpy
from mathutils import Euler, Vector

import a0_scenes as A0
import build_machine as BM
import common as C
import materials as M
import sample_b1 as B
import styles

FRAMES = 1100
EUV = (0.30, 0.06, 1.0)               # saturated EUV violet that stays violet under AgX (xray uses the same)
VIOLET = (0.62, 0.45, 1.0)
CYAN = (0.2, 0.85, 0.95)
ORANGE = (1.0, 0.42, 0.12)
_key, _box, _cyl = A0._key, A0._box, A0._cyl
N = len(BM.PATH) - 1
# PATH indices: 0 collector, 1 IF, 2 fold, 3 field facet, 4 pupil facet, 5 reticle, 6-9 M1-M4, 10 PO focus,
# 11 M5 hit, 12 M6 hit, 13 wafer
COL, IF_, FOLD, FAC1, FAC2, RET, M1, M2, M3, M4, FOC, M5H, M6H, WAF = range(14)
MM_W = 0.45 / 150.0                   # scene units per mm at the wafer (wafer radius 0.45 = 150 mm)
SLIT_W = (26 * MM_W, 1.6 * MM_W)      # 26 x 1.6 mm arc at the wafer (y = across scan, x = scan)
FIELD = (26 * MM_W, 16.5 * MM_W)      # one EXE field 26 x 16.5 mm
SLIT_R = (104 / 152 * 0.6, 12.8 / 152 * 0.6)   # 104 x 12.8 mm at the reticle (reticle plate 0.6 = 152 mm)


def _P(i):
    return Vector(BM.PATH[i])


def _lerp(a, b, u):
    return Vector(a).lerp(Vector(b), u)


_CUM = [0.0]
for _a, _b in zip(BM.PATH, BM.PATH[1:]):
    _CUM.append(_CUM[-1] + (Vector(_a) - Vector(_b)).length)


def _frac(i, u=0.0):
    """Path fraction (by length) of point i, or u of the way from point i to i+1."""
    if u and i < N:
        return (_CUM[i] + u * (_CUM[i + 1] - _CUM[i])) / _CUM[-1]
    return _CUM[i] / _CUM[-1]


def _linear(idb, path_prefix=""):
    ad = idb.animation_data
    for fc in (C.fcurves(ad.action) if ad and ad.action else []):
        if fc.data_path.startswith(path_prefix):
            for kp in fc.keyframe_points:
                kp.interpolation = "LINEAR"


def _machine_and_path(strength=2.5):
    before = set(bpy.data.objects)
    path, pmat = BM.machine()
    new = [o for o in bpy.data.objects if o not in before]
    path.data.bevel_factor_mapping_start = "SPLINE"
    path.data.bevel_factor_mapping_end = "SPLINE"
    em = pmat.node_tree.nodes["Emission"]
    em.inputs["Color"].default_value = (*EUV, 1)
    em.inputs["Strength"].default_value = strength
    return path, pmat, new


def _grow(path, keys):
    for f, v in keys:
        path.data.bevel_factor_end = v
        path.data.keyframe_insert("bevel_factor_end", frame=f)
    _linear(path.data, "bevel_factor_end")


def _masked(name, color, strength, mask_fn):
    """Emission where mask_fn(nodes, links) -> socket is 1, transparent where it is 0 (reads on light and dark)."""
    m = M.emission(name, color, strength)
    nt = m.node_tree
    nodes, links = nt.nodes, nt.links
    tr = nodes.new("ShaderNodeBsdfTransparent")
    mix = nodes.new("ShaderNodeMixShader")
    links.new(mask_fn(nodes, links), mix.inputs["Fac"])
    links.new(tr.outputs[0], mix.inputs[1])
    links.new(nodes["Emission"].outputs[0], mix.inputs[2])
    links.new(mix.outputs[0], nodes["Material Output"].inputs["Surface"])
    m.surface_render_method = "BLENDED"
    return m


def _lines_mask(scale=60.0, seg_scale=9.0, thr=0.55):
    """Generic line/space pattern broken into segments (illustrative circuit lines, 示意; not a real layout)."""
    def fn(nodes, links):
        tc = nodes.new("ShaderNodeTexCoord")
        wave = nodes.new("ShaderNodeTexWave")
        wave.wave_type = "BANDS"
        wave.bands_direction = "Y"
        wave.inputs["Scale"].default_value = scale
        wave.inputs["Distortion"].default_value = 0.0
        links.new(tc.outputs["Object"], wave.inputs["Vector"])
        gt = nodes.new("ShaderNodeMath")
        gt.operation = "GREATER_THAN"
        gt.inputs[1].default_value = thr
        links.new(wave.outputs["Fac"], gt.inputs[0])
        noise = nodes.new("ShaderNodeTexNoise")
        noise.inputs["Scale"].default_value = seg_scale
        noise.inputs["Detail"].default_value = 0.0
        links.new(tc.outputs["Object"], noise.inputs["Vector"])
        gn = nodes.new("ShaderNodeMath")
        gn.operation = "GREATER_THAN"
        gn.inputs[1].default_value = 0.42
        links.new(noise.outputs["Fac"], gn.inputs[0])
        mul = nodes.new("ShaderNodeMath")
        mul.operation = "MULTIPLY"
        links.new(gt.outputs[0], mul.inputs[0])
        links.new(gn.outputs[0], mul.inputs[1])
        return mul.outputs[0]
    return fn


def _band_lines(name, strength, scale=110.0):
    """A solid violet band whose generic line pattern (示意) glows brighter: reads as one band from afar."""
    m = M.emission(name, EUV, strength)
    nt = m.node_tree
    nodes, links = nt.nodes, nt.links
    mask = _lines_mask(scale=scale, seg_scale=16.0, thr=0.5)(nodes, links)
    mix = nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.inputs["A"].default_value = (*EUV, 1)
    mix.inputs["B"].default_value = (0.75, 0.62, 1.0, 1)
    links.new(mask, mix.inputs["Factor"])
    links.new(mix.outputs["Result"], nodes["Emission"].inputs["Color"])
    return m


def _arc_strip(name, centre, length, width, sag, mat, z_up=True, segs=40, role="emitter"):
    """A thin curved band in the xy plane: long along y, narrow along x, bowed by `sag` in x (the curved slit)."""
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    rows = []
    for k in range(segs + 1):
        v = -0.5 + k / segs
        y = v * length
        x = sag * (2 * v) ** 2
        rows.append((bm.verts.new((x - width / 2, y, 0)), bm.verts.new((x + width / 2, y, 0))))
    for (a0, a1), (b0, b1) in zip(rows, rows[1:]):
        bm.faces.new((a0, a1, b1, b0))
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = centre
    ob.data.materials.append(mat)
    styles.tag(ob, role)
    return ob


def _facet_textures():
    """Field facet mirror = many slender facets in columns; pupil facet mirror = many small round facets. Drawn as a
    texture (the facet count is not public, ZEISS 2021 slide 13), so no number is implied."""
    def facet_mat(name, kind):
        m = M.principled(name, (0.86, 0.85, 0.82), metallic=1.0, roughness=0.05)
        nt = m.node_tree
        nodes, links = nt.nodes, nt.links
        b = nodes["Principled BSDF"]
        tc = nodes.new("ShaderNodeTexCoord")
        if kind == "field":
            t = nodes.new("ShaderNodeTexBrick")
            t.inputs["Scale"].default_value = 3.0
            t.inputs["Mortar Size"].default_value = 0.025
            t.inputs["Brick Width"].default_value = 1.6
            t.inputs["Row Height"].default_value = 0.09
            t.inputs["Color1"].default_value = (0.86, 0.85, 0.82, 1)
            t.inputs["Color2"].default_value = (0.80, 0.80, 0.78, 1)
            t.inputs["Mortar"].default_value = (0.04, 0.04, 0.045, 1)
            links.new(tc.outputs["Object"], t.inputs["Vector"])
            links.new(t.outputs["Color"], b.inputs["Base Color"])
        else:
            vor = nodes.new("ShaderNodeTexVoronoi")
            vor.feature = "F1"
            vor.inputs["Scale"].default_value = 26.0
            vor.inputs["Randomness"].default_value = 0.0
            links.new(tc.outputs["Object"], vor.inputs["Vector"])
            ramp = nodes.new("ShaderNodeValToRGB")
            ramp.color_ramp.elements[0].position = 0.36
            ramp.color_ramp.elements[0].color = (0.86, 0.85, 0.82, 1)
            ramp.color_ramp.elements[1].position = 0.42
            ramp.color_ramp.elements[1].color = (0.04, 0.04, 0.045, 1)
            links.new(vor.outputs["Distance"], ramp.inputs["Fac"])
            links.new(ramp.outputs["Color"], b.inputs["Base Color"])
        return m
    for nm, kind in (("Facet0", "field"), ("Facet1", "pupil")):
        ob = bpy.data.objects.get(nm)
        if ob:
            ob.data.materials.clear()
            ob.data.materials.append(facet_mat(nm + "Tex", kind))


def _stage_keys(f, rdx, wdx, wdy=0.0):
    """Reticle stage + reticle move rdx in x (scan); wafer stage + wafer + chuck move (wdx, wdy)."""
    for nm in ("ReticleStage", "Reticle"):
        o = bpy.data.objects[nm]
        _key(o, f, location=(o["home"][0] + rdx, o["home"][1], o["home"][2]))
    for nm in ("WaferStage", "Wafer", "Chuck"):
        o = bpy.data.objects[nm]
        _key(o, f, location=(o["home"][0] + wdx, o["home"][1] + wdy, o["home"][2]))


def _stage_homes():
    for nm in ("ReticleStage", "Reticle", "WaferStage", "Wafer", "Chuck"):
        o = bpy.data.objects[nm]
        o["home"] = tuple(o.location)


def _stages_race(f0, f1, period=16, r_amp=0.8, ratio=8.0):
    """Back-and-forth scan strokes. EXE magnification is 1/8 in the scan direction (ZEISS 2021 s.11), so the
    reticle stroke is 8x the wafer stroke. The relative direction is not public for the EXE (CD_sources S9): drawn
    opposite, as in B8; the narration does not assert it."""
    _stage_keys(f0, 0.0, 0.0)
    f, k = f0 + period // 2, 0
    while f < f1:
        s = 1 if k % 2 == 0 else -1
        _stage_keys(f, s * r_amp, -s * r_amp / ratio)
        f += period
        k += 1
    _stage_keys(f1, 0.0, 0.0)


# ---- C_01 ----------------------------------------------------------------------------------
def assemble(sc, rnd):
    path, pmat, new = _machine_and_path()
    path.hide_render = True
    hosts = BM.attach_small(new)                                    # whole modules move, not loose bolts
    housing = bpy.data.objects["Housing"]
    for o in [housing] + list(housing.children):                    # a section: no outer casing
        o.hide_render = True
    # modules in assembly order (base first, the source last), each floating a little apart in its own place,
    # then flying in and locking; the six modules of the High-NA layout (ASML 2022 slide 34)
    plan = [("Base", (0.0, -0.6, -2.0)), ("WaferStage", (0.2, -2.6, -0.5)), ("POBarrel", (-2.2, -2.2, 0.3)),
            ("ReticleStage", (-0.4, -1.8, 2.2)), ("Illuminator", (0.6, -2.6, 1.8)), ("SrcDrum", (2.6, -2.4, 0.9))]
    names = [p[0] for p in plan]
    extra = [o for o in hosts if o is not housing and o.name not in names]
    for o in extra:                                                  # anything untagged rides with the nearest module
        near = min(names, key=lambda n: (bpy.data.objects[n].location - o.location).length)
        mw = o.matrix_world.copy()
        o.parent = bpy.data.objects[near]
        o.matrix_parent_inverse = o.parent.matrix_world.inverted()
        o.matrix_world = mw
    for i, (nm, off) in enumerate(plan):
        o = bpy.data.objects[nm]
        home, rot0 = o.location.copy(), o.rotation_euler.copy()
        off = Vector(off)
        tilt = Euler((rnd.uniform(-0.12, 0.12), rnd.uniform(-0.12, 0.12), rnd.uniform(-0.15, 0.15)))
        f0 = 18 + 14 * i                                             # last lock at ~4.5 s ("跟着一滴锡")
        _key(o, 1, location=home + off * 1.05,
             rotation_euler=(rot0.x + tilt.x, rot0.y + tilt.y, rot0.z + tilt.z))
        _key(o, f0, location=home + off,
             rotation_euler=(rot0.x + tilt.x * 0.9, rot0.y + tilt.y * 0.9, rot0.z + tilt.z * 0.9))
        _key(o, f0 + 16, location=home - off * 0.012, rotation_euler=rot0)    # a hair past home: the lock
        _key(o, f0 + 21, location=home, rotation_euler=rot0)
    B._area("ClayKey", (BM.CENTER[0] - 2, -7, 9), (0.75, 0, -0.25), 10, 2600, (1.0, 0.98, 0.95))
    cx, cz = BM.CENTER[0], BM.CENTER[2]
    pl = Vector(BM.PLASMA)
    B._camera("CamC_01", [(1, (cx - 0.6, 0, cz + 0.5), (cx - 8.5, -19.5, 6.0), 32, 8.0),
                          (108, (cx + 0.4, 0, cz + 0.4), (cx + 3.0, -16.5, 3.8), 32, 8.0),
                          (192, tuple(pl + Vector((-0.2, 0, -0.1))), tuple(pl + Vector((-2.4, -5.4, 2.9))), 35, 8.0)])


# whole machine, side view: the path from the collector (x 6.3) to the wafer, structures x -3.3..9.4
WIDE_AIM = Vector((BM.CENTER[0] - 0.3, 0.0, 1.1))
WIDE_LOC = WIDE_AIM + Vector((0.0, -15.2, 0.8))


# ---- C_03 / C_04 / C_05 --------------------------------------------------------------------
C04 = 430                    # C_04 starts at sim 431 (registry), C_03 covers sim 1-419, C_05 starts at 911


def ride(sc, rnd):
    path, pmat, new = _machine_and_path(strength=1.6)
    _facet_textures()
    _stage_homes()
    F = _frac
    # C_03, keyed to its cues: collector -> IF by "中间焦点" (3.3 s), the illuminator during "匀化、整形"
    # (4.1-6.4 s), the reticle by "电路图形" (7.9 s), reflected down to M1 by "反射出来" (9.3 s)
    _grow(path, [(1, 0.0), (26, 0.0), (80, F(IF_)), (98, F(FOLD)), (126, F(FAC1)), (150, F(FAC2)),
                 (190, F(RET)), (204, F(RET)), (226, F(M1)),
                 # C_04: through the projection optics, onto the wafer by "投向晶圆" (~4.0 s = shot frame 96)
                 (C04 + 1, F(M1)), (C04 + 20, F(M2)), (C04 + 40, F(M3)), (C04 + 50, F(M4)), (C04 + 60, F(FOC)),
                 (C04 + 74, F(M5H)), (C04 + 85, F(M6H)), (C04 + 96, 1.0)])
    # intermediate focus: a point of light as the beam converges through it
    ifm = M.emission("IFGlow", EUV, 0.0)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.045, location=BM.IF)
    ifo = bpy.context.object
    ifo.data.materials.append(ifm)
    styles.tag(ifo, "emitter")
    _key(ifo, 1, hide_render=True)
    _key(ifo, 78, hide_render=False)
    M.set_emission_strength(ifm, 78, 0.5)
    M.set_emission_strength(ifm, 84, 6.0)
    M.set_emission_strength(ifm, 120, 3.0)
    # the curved illumination slit on the face-down reticle (104 x 12.8 mm, curved; ZEISS 2021 s.11), with a
    # generic line pattern (示意). It is fixed in space: the reticle scans under it.
    rz = BM.RETICLE[2] + 0.05 - 0.03 - 0.004
    slit_m = _band_lines("ReticleSlit", 0.0)
    _arc_strip("ReticleSlit", (BM.RETICLE[0], 0, rz), SLIT_R[0], SLIT_R[1], 0.03, slit_m)
    M.set_emission_strength(slit_m, 188, 0.0)
    M.set_emission_strength(slit_m, 196, 3.0)
    # the exposure slit at the wafer: 26 x 1.6 mm arc, fixed under the projection optics
    wz = BM.WAFER[2] + 0.0125
    wslit_m = M.emission("WaferSlit", EUV, 0.0)
    _arc_strip("WaferSlit", (BM.WAFER[0], 0, wz), SLIT_W[0], SLIT_W[1], 0.004, wslit_m)
    M.set_emission_strength(wslit_m, C04 + 94, 0.0)
    M.set_emission_strength(wslit_m, C04 + 98, 12.0)
    # close to the wafer: the light as a sheet converging onto the slit; the line hands over to it
    fan, f_top = _landing_fan()
    _key(fan, 1, hide_render=True)
    _key(fan, C04 + 196, hide_render=False)
    path.data.bevel_factor_end = 1.0
    path.data.keyframe_insert("bevel_factor_end", frame=C04 + 196)
    path.data.bevel_factor_end = f_top
    path.data.keyframe_insert("bevel_factor_end", frame=C04 + 197)
    _linear(path.data, "bevel_factor_end")
    # C_04 stages: during "狭缝扫过，掩模和晶圆…飞驰" (4.7-8.2 s) the strokes race, 8:1, outlined in metrology cyan
    _stages_race(C04 + 112, C04 + 190)
    out_m = M.emission("StageOutline", CYAN, 3.0)
    # (build_machine boxes have their transform applied: origin at the world origin, so offsets are world positions)
    for nm, size, cen in (("ReticleStage", (2.4, 1.8, 0.3), (BM.RETICLE[0], BM.RETICLE[2] + 0.27)),
                          ("WaferStage", (2.8, 2.8, 0.35), (0.0, -1.35))):
        host = bpy.data.objects[nm]
        for dz in (size[2] / 2, -size[2] / 2):
            for k, (dx, dy, sx, sy) in enumerate(((0, -size[1] / 2, size[0], 0.03), (0, size[1] / 2, size[0], 0.03),
                                                  (-size[0] / 2, 0, 0.03, size[1]), (size[0] / 2, 0, 0.03, size[1]))):
                e = _box(f"Outline{nm}{dz:.2f}{k}", (0, 0, 0), (sx, sy, 0.03), out_m, role="emitter")
                e.parent = host
                e.location = (cen[0] + dx, dy, cen[1] + dz)
                _key(e, 1, hide_render=True)
                _key(e, C04 + 104, hide_render=False)
                _key(e, C04 + 204, hide_render=True)
    M.set_emission_strength(out_m, C04 + 104, 0.0)
    M.set_emission_strength(out_m, C04 + 112, 3.0)
    M.set_emission_strength(out_m, C04 + 194, 3.0)
    M.set_emission_strength(out_m, C04 + 204, 0.0)
    # "光子落进光刻胶，一层电路就此写定" (8.6-11.7 s): one slow scan of one field under the slit; the latent image
    # fills in behind the slit (it is a chemical change in the resist; drawn glowing, 示意)
    wafer = bpy.data.objects["Wafer"]
    lat = _latent_field(wafer, "Latent0", (0.0, 0.0), progressive=True)
    s0, s1 = C04 + 206, C04 + 282
    half = (FIELD[1] + SLIT_W[1]) / 2
    _stage_keys(s0 - 8, 8 * half, -half)
    _stage_keys(s0, 8 * half, -half)
    _stage_keys(s1, -8 * half, half)
    thr = lat.data.materials[0].node_tree.nodes["Reveal"].inputs[1]
    for f, wdx in ((s0 - 8, -half), (s0, -half), (s1, half)):
        thr.default_value = -wdx           # a field point at local x has passed the slit once wafer offset > -x
        thr.keyframe_insert("default_value", frame=f)
    for idb in (lat.data.materials[0].node_tree,):
        _linear(idb)
    for nm in ("ReticleStage", "Reticle", "WaferStage", "Wafer", "Chuck"):
        ad = bpy.data.objects[nm].animation_data
        for fc in C.fcurves(ad.action):
            for kp in fc.keyframe_points:
                if s0 <= kp.co[0] <= s1:
                    kp.interpolation = "LINEAR"
    # then step-and-scan across the wafer: the wafer steps to the next field and scans it, field after field
    f = s1 + 22
    fields = [(dx, dy) for dy in (0.0, -FIELD[0], FIELD[0]) for dx in (FIELD[1], 2 * FIELD[1], -FIELD[1],
                                                                     -2 * FIELD[1], 3 * FIELD[1])]
    sign = 1
    for k, (fx, fy) in enumerate(fields):
        if f + 9 > C04 + 466:
            break
        _latent_field(wafer, f"Latent{k + 1}", (fx, fy), on=f + 9)
        # the field centre (fx, fy) in wafer coordinates passes the slit (fixed at world x = WAFER.x): wafer offset
        # runs from -fx - half to -fx + half (alternating), the reticle 8x as far
        _stage_keys(f, sign * 8 * half, -fx - sign * half, -fy)
        _stage_keys(f + 9, -sign * 8 * half, -fx + sign * half, -fy)
        sign = -sign
        f += 14
    # cameras ------------------------------------------------------------------------------------
    w = Vector(BM.WAFER)
    pl, ifp = Vector(BM.PLASMA), Vector(BM.IF)
    ret = Vector(BM.RETICLE)
    keys3 = [(1, _lerp(_P(COL), pl, 0.5), Vector((4.0, -1.9, 3.5)), 28, 11.0),
             (50, _lerp(pl, ifp, 0.5), _lerp(pl, ifp, 0.35) + Vector((-0.2, -2.2, 2.2)), 28, 11.0),
             (92, ifp, ifp + Vector((0.6, -1.9, 0.35)), 28, 11.0),
             (138, _lerp(_P(FOLD), _P(FAC1), 0.6), Vector((3.3, -3.6, 2.0)), 28, 11.0),
             (178, _lerp(_P(FAC2), ret, 0.5), Vector((1.7, -3.3, 2.1)), 28, 11.0),
             (222, ret + Vector((0, 0, -0.15)), ret + Vector((1.0, -2.1, -1.0)), 28, 11.0),
             (330, ret + Vector((-0.1, 0, -0.35)), ret + Vector((-0.7, -2.4, -1.0)), 28, 11.0),
             (419, _P(M1) + Vector((-0.1, 0, 0.3)), _P(M1) + Vector((0.7, -2.6, 0.8)), 28, 11.0)]
    B._camera("CamC_03", [(f, tuple(a), tuple(l), lens, fs) for f, a, l, lens, fs in keys3])
    r = C04
    keys4 = [(r + 1, keys3[-1][1], keys3[-1][2], 28, 8.0),
             (r + 42, _lerp(_P(M2), _P(M3), 0.5), Vector((0.5, -2.9, 1.9)), 28, 8.0),
             (r + 80, Vector((0.15, 0, -0.25)), Vector((1.0, -3.0, 0.1)), 28, 8.0),
             (r + 100, w + Vector((0.05, 0, 0.1)), w + Vector((0.7, -2.4, 0.5)), 30, 8.0),
             (r + 126, Vector((0.3, 0, 1.15)), Vector((0.7, -12.6, 1.6)), 35, 8.0),       # both stages in frame
             (r + 196, Vector((0.3, 0, 1.15)), Vector((0.6, -12.0, 1.5)), 35, 8.0),
             # down to the resist, under M5 (it sits 0.16 above the wafer): the slit across the frame, the light
             # coming down through M5's hole; then the half-second still
             (r + 236, w + Vector((-0.01, 0, 0.0)), w + Vector((0.24, -0.16, 0.145)), 30, 22.0),
             (r + 284, w + Vector((-0.01, 0, 0.0)), w + Vector((0.21, -0.14, 0.14)), 30, 22.0),
             (r + 300, w + Vector((-0.01, 0, 0.0)), w + Vector((0.21, -0.14, 0.14)), 30, 22.0),
             (r + 472, w, w + Vector((0.6, -1.15, 1.0)), 40, 16.0)]
    B._camera("CamC_04", [(f, tuple(a), tuple(l), lens, fs) for f, a, l, lens, fs in keys4])
    # C_05 (911-1054): fast pull-back from the wafer to the whole machine (machine spans x -3.3..9.4)
    cx = Vector(BM.CENTER)
    B._camera("CamC_05", [(911, w, w + Vector((0.6, -1.15, 1.0)), 40, 16.0),
                          (930, w + Vector((0.2, 0, 0.6)), w + Vector((0.8, -4.0, 1.4)), 35, 11.0),
                          (1010, WIDE_AIM, WIDE_LOC + Vector((0, 0.6, -0.05)), 35, 11.0),
                          (1054, WIDE_AIM, WIDE_LOC, 35, 11.0)])


def _latent_lines(nodes, links, lines=20, field_x=None):
    """Generic line/space pattern for a latent field (示意): `lines` thin lines across the scan direction, each broken
    at its own random places (a stand-in for a circuit layer, not a real layout)."""
    fx = field_x or FIELD[1]
    S = lines / fx
    tc = nodes.new("ShaderNodeTexCoord")
    sep = nodes.new("ShaderNodeSeparateXYZ")
    links.new(tc.outputs["Object"], sep.inputs[0])
    mx = nodes.new("ShaderNodeMath")
    mx.operation = "MULTIPLY"
    mx.inputs[1].default_value = S
    links.new(sep.outputs["X"], mx.inputs[0])
    fr = nodes.new("ShaderNodeMath")
    fr.operation = "FRACT"
    links.new(mx.outputs[0], fr.inputs[0])
    line = nodes.new("ShaderNodeMath")
    line.operation = "LESS_THAN"
    line.inputs[1].default_value = 0.28
    links.new(fr.outputs[0], line.inputs[0])
    fl = nodes.new("ShaderNodeMath")
    fl.operation = "FLOOR"
    links.new(mx.outputs[0], fl.inputs[0])
    my = nodes.new("ShaderNodeMath")
    my.operation = "MULTIPLY"
    my.inputs[1].default_value = S * 0.35
    links.new(sep.outputs["Y"], my.inputs[0])
    comb = nodes.new("ShaderNodeCombineXYZ")
    links.new(fl.outputs[0], comb.inputs["X"])
    links.new(my.outputs[0], comb.inputs["Y"])
    noise = nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 1.0
    noise.inputs["Detail"].default_value = 0.0
    links.new(comb.outputs[0], noise.inputs["Vector"])
    gap = nodes.new("ShaderNodeMath")
    gap.operation = "GREATER_THAN"
    gap.inputs[1].default_value = 0.47
    links.new(noise.outputs["Fac"], gap.inputs[0])
    mul = nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    links.new(line.outputs[0], mul.inputs[0])
    links.new(gap.outputs[0], mul.inputs[1])
    return mul.outputs[0]


def _latent_field(wafer, name, centre, progressive=False, on=None):
    """One 26 x 16.5 mm exposure field on the wafer (x = scan direction), parented to the wafer."""
    def mask(nodes, links):
        base = _latent_lines(nodes, links)
        if not progressive:
            return base
        tc = nodes.new("ShaderNodeTexCoord")
        sep = nodes.new("ShaderNodeSeparateXYZ")
        links.new(tc.outputs["Object"], sep.inputs[0])
        rev = nodes.new("ShaderNodeMath")
        rev.name = "Reveal"
        rev.operation = "GREATER_THAN"
        links.new(sep.outputs["X"], rev.inputs[0])
        rev.inputs[1].default_value = 1.0
        mul = nodes.new("ShaderNodeMath")
        mul.operation = "MULTIPLY"
        links.new(base, mul.inputs[0])
        links.new(rev.outputs[0], mul.inputs[1])
        return mul.outputs[0]
    m = _masked(name + "Mat", (0.42, 0.22, 1.0), 1.6, mask)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0))
    ob = bpy.context.object
    ob.name = name
    ob.scale = (FIELD[1], FIELD[0], 1)
    bpy.ops.object.transform_apply(scale=True)
    ob.data.materials.append(m)
    styles.tag(ob, "emitter")
    ob.parent = wafer                                    # wafer disc: no rotation/scale, so local = offset
    ob.location = (centre[0], centre[1], 0.0115)
    if on is not None:
        M.set_emission_strength(m, 1, 0.0)
        M.set_emission_strength(m, on - 1, 0.0)
        M.set_emission_strength(m, on + 3, 1.6)
        _key(ob, 1, hide_render=True)
        _key(ob, on - 1, hide_render=False)
    return ob


def _landing_fan(z_top=BM.PO_MIRRORS[4][2] - 0.012):
    """Close to the wafer the single line would be a fat tube; there the light is drawn as what it is, light converging
    onto the 26 mm slit (a sheet along the slit, fading upward), from just under M5, through whose hole it passes.
    It continues the line's last segment (M6 -> wafer)."""
    a, b = _P(M6H), _P(WAF)
    t = (a.z - z_top) / (a.z - b.z)
    top = a.lerp(b, t)
    bot = Vector((b.x, 0.0, b.z + 0.0125))
    me = bpy.data.meshes.new("LandingFan")
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    half_top, half_bot = BM.M5_R * 0.2, SLIT_W[0] / 2          # it leaves through M5's central hole (r = 0.22 M5_R)
    v = [bm.verts.new((top.x, -half_top, top.z)), bm.verts.new((top.x, half_top, top.z)),
         bm.verts.new((bot.x, half_bot, bot.z)), bm.verts.new((bot.x, -half_bot, bot.z))]
    f = bm.faces.new(v)
    for loop, (u, w) in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
        loop[uv].uv = (u, w)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new("LandingFan", me)
    bpy.context.scene.collection.objects.link(ob)

    def grad(nodes, links):
        tc = nodes.new("ShaderNodeTexCoord")
        sep = nodes.new("ShaderNodeSeparateXYZ")
        links.new(tc.outputs["UV"], sep.inputs[0])
        pw = nodes.new("ShaderNodeMath")
        pw.operation = "POWER"
        pw.inputs[1].default_value = 1.6
        links.new(sep.outputs["Y"], pw.inputs[0])
        k = nodes.new("ShaderNodeMath")
        k.operation = "MULTIPLY"
        k.inputs[1].default_value = 0.75
        links.new(pw.outputs[0], k.inputs[0])
        return k.outputs[0]
    m = _masked("LandingFanMat", EUV, 2.0, grad)
    ob.data.materials.append(m)
    styles.tag(ob, "rays")
    return ob, _frac(M6H, t)


# ---- C_06 ----------------------------------------------------------------------------------
def pulses(sc, rnd):
    path, pmat, new = _machine_and_path(strength=0.35)
    pm = M.emission("PulseMat", (0.42, 0.16, 1.0), 9.0)
    # flashes run from the collector to the wafer along the path; launches come closer and closer and each run is
    # faster, until they fuse into one band ("这一切" at 1.0 s ... "万次" at ~3.0 s)
    t, gap, travel, launches = 22, 20.0, 16.0, []
    while t < 84:
        launches.append((t, travel))
        t += max(2, round(gap))
        gap *= 0.74
        travel = max(8.0, travel * 0.9)
    width = 0.07
    for k, (t0, T) in enumerate(launches):
        cu = path.data.copy()
        cu.bevel_depth = 0.045
        cu.materials.clear()
        cu.materials.append(pm)
        ob = bpy.data.objects.new(f"Pulse{k}", cu)
        sc.collection.objects.link(ob)
        styles.tag(ob, "rays")
        _key(ob, 1, hide_render=True)
        _key(ob, t0, hide_render=False)
        _key(ob, int(t0 + T) + 2, hide_render=True)
        for f in range(t0, int(t0 + T) + 2):
            h = (f - t0) / T * (1 + width)
            cu.bevel_factor_start = min(1.0, max(0.0, h - width))
            cu.bevel_factor_end = min(1.0, max(0.0, h))
            cu.keyframe_insert("bevel_factor_start", frame=f)
            cu.keyframe_insert("bevel_factor_end", frame=f)
        _linear(cu)
    s = pmat.node_tree.nodes["Emission"].inputs["Strength"]
    for fr, v in ((1, 0.35), (60, 0.5), (84, 3.0), (92, 2.4), (100, 2.9), (110, 2.5), (120, 2.8), (130, 2.5), (139, 2.7)):
        s.default_value = v                                        # fused: a steady band that trembles slightly
        s.keyframe_insert("default_value", frame=fr)
    cx = Vector(BM.CENTER)
    B._camera("CamC_06", [(1, WIDE_AIM, WIDE_LOC, 35, 11.0),
                          (139, WIDE_AIM, WIDE_LOC + Vector((0, 1.3, -0.07)), 35, 11.0)])


# ---- C_08 / C_09 ---------------------------------------------------------------------------
# C_08 cues (word timestamps): 光源造光 2.4-3.5 s, 镜子传光 4.1-4.8, 掩模给图 5.0-5.7, 工件台对准 6.4-7.6
T_SRC, T_MIR, T_MSK, T_STG, T_BEAM = 58, 98, 120, 154, 176


def _lit(ob, mat, f0, peak, f_end=None):
    """Hidden until lit (an unlit emitter would render as a black solid on the light xray studio)."""
    _key(ob, 1, hide_render=True)
    _key(ob, f0, hide_render=False)
    if mat is None:                       # a shared material keyed by its first user
        return
    M.set_emission_strength(mat, f0, 0.3 * peak)
    M.set_emission_strength(mat, f0 + 8, peak)
    if f_end:
        M.set_emission_strength(mat, f_end, peak)


def accents(sc, rnd):
    path, pmat, new = _machine_and_path()
    path.data.bevel_factor_mapping_end = "SPLINE"
    _grow(path, [(1, 0.0), (T_BEAM, 0.0), (T_BEAM + 30, 1.0)])
    pl, ax = Vector(BM.PLASMA), Vector(BM.SRC_AXIS)
    # source: the plasma (EUV violet) fed by the drive laser through the collector's central hole (orange)
    src = M.emission("AccSource", EUV, 0.0)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.16, location=BM.PLASMA)
    so = bpy.context.object
    so.data.materials.append(src)
    styles.tag(so, "emitter")
    _lit(so, src, T_SRC, 1.6)
    las = M.emission("AccLaser", (1.0, 0.28, 0.02), 0.0)            # deep accents: on the light xray studio

    a, b = pl + ax * 2.4, pl
    bpy.ops.mesh.primitive_cylinder_add(radius=0.035, depth=(a - b).length, location=tuple((a + b) / 2))
    lo = bpy.context.object
    lo.rotation_euler = (a - b).to_track_quat("Z", "Y").to_euler()
    lo.data.materials.append(las)
    styles.tag(lo, "emitter")
    _lit(lo, las, T_SRC - 6, 1.5)
    # mirrors: a ring at every mirror the drawn path reflects on (10: collector, fold, two facet mirrors, M1-M6),
    # sized to the mirror, in the camera plane
    mir = M.emission("AccMirror", (0.10, 0.30, 0.95), 0.0)          # a bright emitter would wash out to grey
    radii = [(BM.COLLECTOR, 0.95), (BM.FOLD, 0.26), (BM.FACET1, 0.5), (BM.FACET2, 0.22),
             (BM.PO_MIRRORS[0], 0.26), (BM.PO_MIRRORS[1], 0.34), (BM.PO_MIRRORS[2], 0.44), (BM.PO_MIRRORS[3], 0.26),
             (BM.PO_MIRRORS[4], BM.M5_R + 0.05), (BM.PO_MIRRORS[5], BM.M6_R + 0.06)]
    for i, (p, r) in enumerate(radii):
        bpy.ops.mesh.primitive_torus_add(major_radius=r, minor_radius=0.03, location=(p[0], -0.05, p[2]),
                                         rotation=(math.pi / 2, 0, 0))
        t = bpy.context.object
        t.name = f"AccRing{i}"
        t.data.materials.append(mir)
        styles.tag(t, "emitter")
        _lit(t, mir if i == 0 else None, T_MIR + 2 * i, 1.4)
    # mask: the pattern on its face-down side and a white outline around the plate
    msk = A0.circuit_emission("AccMask", (0.95, 0.95, 1.0), 0.0, scale=0.4)
    rz = BM.RETICLE[2] + 0.05 - 0.03 - 0.006
    bpy.ops.mesh.primitive_plane_add(size=0.56, location=(BM.RETICLE[0], 0, rz))
    mp = bpy.context.object
    mp.data.materials.append(msk)
    styles.tag(mp, "emitter")
    _lit(mp, msk, T_MSK, 3.0)
    edge = M.emission("AccMaskEdge", (0.95, 0.95, 1.0), 0.0)
    for k, (dx, dy, sx, sy) in enumerate(((0, -0.31, 0.64, 0.02), (0, 0.31, 0.64, 0.02), (-0.31, 0, 0.02, 0.64),
                                          (0.31, 0, 0.02, 0.64))):
        e = _box(f"AccMaskEdge{k}", (BM.RETICLE[0] + dx, dy, BM.RETICLE[2] + 0.05), (sx, sy, 0.08), edge, role="emitter")
        _lit(e, edge if k == 0 else None, T_MSK, 5.0)
    # stages: metrology-cyan outlines of the mask stage and the wafer stage
    stg = M.emission("AccStage", (0.0, 0.55, 0.62), 0.0)
    # (build_machine boxes have their transform applied, so their origins are at the world origin: use the centres)
    for k, (o, size) in enumerate(((Vector((BM.RETICLE[0], 0, BM.RETICLE[2] + 0.27)), (2.4, 1.8, 0.3)),
                                   (Vector((0.0, 0.0, -1.35)), (2.8, 2.8, 0.35)))):
        for j, (dz, sz) in enumerate(((size[2] / 2, 0.025), (-size[2] / 2, 0.025))):
            for (dx, dy, sx, sy) in ((0, -size[1] / 2 - 0.01, size[0] + 0.04, 0.03), (0, size[1] / 2 + 0.01, size[0] + 0.04, 0.03),
                                     (-size[0] / 2 - 0.01, 0, 0.03, size[1] + 0.04), (size[0] / 2 + 0.01, 0, 0.03, size[1] + 0.04)):
                e = _box(f"AccStage{k}{j}{dx:.1f}{dy:.1f}", (o.x + dx, o.y + dy, o.z + dz),
                         (sx * 1.0 if sx > 0.1 else 0.05, sy if sy > 0.1 else 0.05, 0.05), stg, role="emitter")
                _key(e, 1, hide_render=True)
                _key(e, T_STG + 6 * k, hide_render=False)
    M.set_emission_strength(stg, T_STG, 0.5)
    M.set_emission_strength(stg, T_STG + 8, 1.4)
    # C_09 (sim 241-420): per-module axes jitter, then snap to one shared origin; a shared grid fades in.
    # cues: 千百个“不可能” 1.0-1.7 s, 同一时刻 2.7-3.4, 同一个坐标系 3.7-4.6, 成立 5.0
    c9 = 240
    snap0, snap1 = c9 + 86, c9 + 98
    axes_m = M.emission("Axes", (0.0, 0.42, 0.56), 1.3)               # deep teal: reads on the light studio
    centres = [BM.PLASMA, BM.IF, BM.FACET1, BM.RETICLE, (0.0, 0, 1.6), BM.WAFER]
    origin = Vector((BM.CENTER[0] - 0.6, -2.2, BM.CENTER[2] - 0.4))
    for i, c0 in enumerate(centres):
        bpy.ops.object.empty_add(location=(c0[0], -1.6, c0[2]))
        axo = bpy.context.object
        axo.name = f"Axis{i}"
        bars = []
        for d in ((0.85, 0.0, 0.0), (0.0, 0.85, 0.0), (0.0, 0.0, 0.85)):
            size = tuple(max(v, 0.065) for v in d)
            b = _box(f"AxisBar{i}{d}", (0, 0, 0), size, axes_m, role="emitter")
            b.parent = axo
            b.location = (d[0] / 2, d[1] / 2, d[2] / 2)
            bars.append(b)
        for b in bars + [axo]:
            _key(b, 1, hide_render=True)
            _key(b, c9 + 1, hide_render=False)
        for f in range(c9 + 1, snap0, 5):
            amp = 0.5
            axo.rotation_euler = Euler((rnd.uniform(-amp, amp), rnd.uniform(-amp, amp), rnd.uniform(-amp, amp)))
            axo.keyframe_insert("rotation_euler", frame=f)
            axo.location = Vector((c0[0], -1.6, c0[2])) + Vector([rnd.uniform(-0.04, 0.04) for _ in range(3)])
            axo.keyframe_insert("location", frame=f)
        _key(axo, snap0, location=(c0[0], -1.6, c0[2]))
        _key(axo, snap1, rotation_euler=(0, 0, 0), location=tuple(origin))
        _key(axo, snap1 + 3, rotation_euler=(0, 0, 0), location=tuple(origin))
        sc_ = 1.0
        _key(axo, snap1, scale=(sc_, sc_, sc_))
        _key(axo, snap1 + 4, scale=(2.6, 2.6, 2.6))                 # the one shared frame, larger
    def alpha(nodes, links):                                          # fades in by opacity, not from black
        v = nodes.new("ShaderNodeValue")
        v.name = "Alpha"
        v.outputs[0].default_value = 0.0
        return v.outputs[0]
    gm = _masked("SharedGrid", (0.0, 0.28, 0.38), 1.0, alpha)          # deep teal lines read on the light studio
    gx0, gz0 = BM.CENTER[0], BM.CENTER[2]
    for i in range(-26, 27):                                          # wider than the frame at the end of C_09
        _box(f"Gx{i}", (gx0 + i * 0.5, 2.2, gz0), (0.03 if i % 4 else 0.06, 0.01, 14.0), gm, role="emitter")
    for i in range(-14, 15):
        _box(f"Gz{i}", (gx0, 2.2, gz0 + i * 0.5), (26.0, 0.01, 0.03 if i % 4 else 0.06), gm, role="emitter")
    gobs = [o for o in bpy.data.objects if o.name.startswith(("Gx", "Gz"))]
    for o in gobs:
        _key(o, 1, hide_render=True)
        _key(o, snap1 - 2, hide_render=False)
    av = gm.node_tree.nodes["Alpha"].outputs[0]
    for f, v in ((snap1 - 2, 0.0), (snap1 + 22, 1.0)):
        av.default_value = v
        av.keyframe_insert("default_value", frame=f)
    B._area("MKey", (BM.CENTER[0], -9, 8), (0.9, 0, 0), 16, 2500, (0.8, 0.85, 1.0))
    cx = Vector(BM.CENTER)
    B._camera("CamC_08", [(1, pl + Vector((-0.4, 0, -0.1)), pl + Vector((0.2, -6.2, 1.2)), 35, 8.0),
                          (T_SRC + 12, pl + Vector((-0.8, 0, -0.1)), pl + Vector((-0.5, -7.0, 1.3)), 35, 8.0),
                          (T_STG, cx + Vector((-0.9, 0, 0.3)), cx + Vector((-0.9, -13.6, 1.9)), 35, 8.0),
                          (216, cx, cx + Vector((0.0, -16.2, 1.8)), 35, 8.0)])
    B._camera("CamC_09", [(c9 + 1, cx, cx + Vector((0.0, -16.2, 1.8)), 35, 8.0),
                          (c9 + 180, cx + Vector((0, 0, 0.2)), cx + Vector((0.0, -18.6, 2.6)), 35, 8.0)])


# ---- C_10 ----------------------------------------------------------------------------------
def heart(sc, rnd):
    path, pmat, new = _machine_and_path()
    s = pmat.node_tree.nodes["Emission"].inputs["Strength"]
    for f, v in ((1, 2.4), (6, 4.5), (12, 1.6), (20, 4.0), (28, 1.4), (46, 3.6), (56, 1.0), (78, 0.0)):
        s.default_value = v
        s.keyframe_insert("default_value", frame=f)
    em = M.emission("Ember", EUV, 0.0)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.03, location=BM.PLASMA)
    e = bpy.context.object
    e.data.materials.append(em)
    styles.tag(e, "emitter")
    M.set_emission_strength(em, 50, 0.0)
    M.set_emission_strength(em, 74, 14.0)
    M.set_emission_strength(em, 96, 10.0)
    # start on the whole machine, push slowly toward the plasma so the ember ends at frame centre, where D_08's
    # droplet sits (match cut)
    cx, pl = Vector(BM.CENTER), Vector(BM.PLASMA)
    B._camera("CamC_10", [(1, WIDE_AIM, WIDE_LOC + Vector((0, 1.3, -0.07)), 35, 11.0),
                          (96, pl, pl + Vector((-0.6, -9.5, 0.4)), 35, 11.0)])


def after_style(style, shot_id):
    """EUV beams saturated violet in every style (energy kept the build colour and could clip to white)."""
    for o in bpy.data.objects:
        if styles.role_of(o) != "rays":
            continue
        for slot in o.material_slots:
            m = slot.material
            em = m and m.use_nodes and m.node_tree.nodes.get("Emission")
            if em and m.name.startswith("LightPath"):
                em.inputs["Color"].default_value = (*EUV, 1)
    if shot_id == "C_10" and style == "energy":       # the structure outlines withdraw with the light
        for m in bpy.data.materials:
            if m.name.startswith("EnergyRim") and m.use_nodes:
                mul = next((n for n in m.node_tree.nodes if n.type == "MATH" and n.operation == "MULTIPLY"), None)
                if mul:
                    for f, v in ((1, mul.inputs[1].default_value), (30, mul.inputs[1].default_value), (72, 0.0)):
                        mul.inputs[1].default_value = v
                        mul.inputs[1].keyframe_insert("default_value", frame=f)


def build(variant="ride", seed=31):
    sc = C.reset_scene(FRAMES)
    C.set_world(top=(0.03, 0.035, 0.05), horizon=(0.012, 0.014, 0.02), bottom=(0.003, 0.004, 0.006))
    C.set_color_management(exposure=0.4)
    rnd = random.Random(seed)
    {"assemble": assemble, "ride": ride, "pulses": pulses, "accents": accents, "heart": heart}[variant](sc, rnd)
    return sc
