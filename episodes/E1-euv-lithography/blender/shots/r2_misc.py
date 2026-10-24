"""P1 round 2: scale / data / micro shots, rebuilt per Carl's 2026-10-23 picks (SCALE_E1 v2).

variants (registry args: {variant: ..., shot: ...}); every variant puts its camera in "CamR2":
  space    B4_10  7A: Earth, Moon and a golf ball in one 3D space, laser beam Earth -> ball on the Moon
  globe    A0_06  7A: 3D night globe turned to Europe, supplier dots appear, arcs converge on the Netherlands
  mirror   B4_07  4A/4D macro: curved multilayer mirror in its mount, push to the cut edge (TEM inset = overlay)
  pellicle B6_12  5A: near-transparent membrane on a thin frame above a reflective mask, gap revealed
  photons  B9_05  6D macro: resist lines on a wafer under falling EUV photons (1 nm^2 count = overlay)
  wafer    B8_17  7A: real wafer, 188 fields light up in scan order; finished wafers stack up beside it
  wave     A2_08  violet wave whose wavelength shrinks into a pen-tip line, faded grey 193 nm wave behind
  bokeh    A2_03  defocused machine-interior plate under the formula overlay
Overlays (numbers, magnifiers, labels) live in mograph/r2_ov_misc.py.
"""
import math
import os
import random

import bmesh
import bpy
from mathutils import Matrix, Vector

import common as C
import kit_r2 as K

EP = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TEX = os.path.join(EP, "blender", "textures")
DIES = os.path.join(C.REPO_ROOT, "shared", "assets", "dies")
# R20 (R20_ROOT_CAUSE row #4): shots whose R20 structural change is switched on. Remove a shot id to get R19 pixels back.
# mograph/r2_ov_zz20m.py reads this line to switch its label change with the shot.
R20_SHOTS = {"B6_12", "B8_17"}
# R21 (R21_ROOT_CAUSE rows 3 / 5, misc sub-agent): shots using round-21 code (remove an id -> R20 pixels)
R21_SHOTS = {"B8_17", "B6_12"}
# R22 (R22_ROOT_CAUSE.md): per-agent shot sets + hook modules, pre-wired by the main process. For a shot in a set,
# build() calls <hook>.pre(variant, shot, module) first (may patch module globals / functions) and
# <hook>.post(sc, variant, shot) last (may add / replace / delete objects, move the camera). Remove a shot id from its
# set -> exact R21 pixels. Gold shots (A0_02 / D_07 / B9_05 / B1_22) are never in a set.
R22_SHOTS = {"B8_17", "B4_10"}  # B6_12: misc Q4 no (haze milky, no crisp band) -> R21 pixels; # misc agent: misc_b817_r22.py / misc_b612_r22.py / misc_b410_r22.py
R22_HOOKS = [({"B8_17"} & R22_SHOTS, "misc_b817_r22"), ({"B6_12"} & R22_SHOTS, "misc_b612_r22"), ({"B4_10"} & R22_SHOTS, "misc_b410_r22")]
# R23 (R23_ROOT_CAUSE.md): per-agent shot sets + hook modules, pre-wired by the main process, layered AFTER the R22
# hooks (same pre(variant, shot, module) / post(sc, variant, shot) interface). Remove a shot id from its R23 set ->
# exact R22 pixels. Gold shots (A0_02 / D_07 / B9_05 / B1_22) are never in a set.
R23_MISC = {"B6_12"}   # B4_10: main 32-spp Q4 no (pebbles read as upright spikes, ball shadow = black column); B8_17: main Q4 no (exposed vs unexposed fields no longer separate -> R22 counter-sync win lost) -> R22 pixels   # misc agent: misc_r23.py
R23_PANEL = set()   # A0_06: panel agent Q4 no (cluster push not built) -> R22 pixels   # panel agent: panel_r23.py (row 4)
R23_HOOKS = [(R23_MISC, "misc_r23"), (R23_PANEL, "panel_r23")]
# R24 (R24_ROOT_CAUSE.md): per-agent shot sets + hook modules, pre-wired by the main process, layered AFTER the R23
# hooks (same pre(variant, shot, module) / post(sc, variant, shot) interface). Remove a shot id from its R24 set ->
# exact R23 pixels. Gold shots (A0_02 / D_07 / B9_05 / B1_22) are never in a set.
R24_BEAM = {"B4_07", "A2_03", "B8_17"}   # mbeam agent: misc_beam_r24h.py (row 3: one path per screen, beam_r24)
R24_MOON = {"B4_10"}                     # moon agent: moon_r24.py (row 4: real lunar texture / DEM + grounded rocks)
R24_PANEL = {"A0_06"}                    # panel agent: panel_r24.py (row 3: links as great-circle arcs on the globe)
R24_HOOKS = [(R24_BEAM, "misc_beam_r24h"), (R24_MOON, "moon_r24"), (R24_PANEL, "panel_r24")]
# R25 (R25_ROOT_CAUSE.md): per-agent shot sets + hook modules, pre-wired by the main process, layered AFTER the R24
# hooks (same pre(variant, shot, module) / post(sc, variant, shot) interface). Remove a shot id from its R25 set ->
# exact R24 pixels. Gold shots (A0_02 / D_07 / B9_05 / B1_22) are never in a set.
R25_BEAM = {"A2_03", "B8_17"}   # B4_07: main 32-spp Q4 no (f36 landing lost in the window glare -> V meets in mid-air; R24 crisp spot was an adjusted >=88 shot) -> R24 pixels   # mbeam agent: misc_beam_r25h.py (rows 1 / 2 / 4: turn mirrors + taper via beam_r25, density)
R25_HOOKS = [(R25_BEAM, "misc_beam_r25h")]
# R26 (R26_ROOT_CAUSE.md): per-agent shot sets + hook modules, pre-wired by the main process, layered AFTER the R25
# hooks (same pre(variant, shot, module) / post(sc, variant, shot) interface). Remove a shot id from its R26 set ->
# exact R25 pixels. Gold shots (A0_02 / D_07 / B9_05 / B1_22) are never in a set.
R26_BEAM = {"A2_03", "B8_17"}   # B4_07: mbeam BEAMCHECK25 NOGO f79 (coating edge-on 0.36 at the R24 camera) -> R25 pixels   # mbeam agent: misc_beam_r26h.py (row 2: beam_r26 soft shell)
R26_HOOKS = [(R26_BEAM, "misc_beam_r26h")]
# R27 (R27_ROOT_CAUSE.md): per-agent shot sets + hook modules, pre-wired by the main process, layered AFTER the R26
# hooks (same pre(variant, shot, module) / post(sc, variant, shot) interface). Remove a shot id from its R27 set ->
# exact R26 pixels. Mutate these sets, never rebind them (the hook list captures the set objects at import time).
R27_MISC = {"B8_17", "A0_06", "A2_03"}   # misc agent: misc_r27.py (row 5: B8_17 188 half-fields + slit/counter sync, A0_06 leader on the globe; row 4: A2_03 NA cone + named parts)
R27_HOOKS = [(R27_MISC, "misc_r27")]
# R28 (R28_ROOT_CAUSE.md): per-agent shot sets + hook modules, pre-wired by the main process, layered AFTER the R27
# hooks. Remove a shot id from its R28 set -> exact R27 pixels. Mutate these sets, never rebind them.
R28_MISC = {"B6_12", "A2_03"}   # misc agent: misc_r28.py (row 4: B6_12 pellicle hair-line + dark multilayer/absorber face + grey hoses; row 5: A2_03 violet NA cone, cyan marks)
R28_HOOKS = [(R28_MISC, "misc_r28")]
# R29 (R29_ROOT_CAUSE.md): per-row shot sets + hook modules, pre-wired by the main process, layered AFTER the R28
# hooks. Remove a shot id from its R29 set -> exact R28 pixels. Mutate these sets, never rebind them.
R29_BEAM = {"A2_03", "B8_17"}   # main process: beam_hook_r29.py (row 1; LAST)
R29_MISC = {"B6_12"}   # misc agent: misc_r29.py (row 6: B4_07 ceramic body + flexure mount + chamber wall; B6_12 machine context behind the mask)
R29_HOOKS = [(R29_MISC, "misc_r29"), (R29_BEAM, "beam_hook_r29")]
# R30 (R30_ROOT_CAUSE.md): per-row sets, layered AFTER the R29 hooks, BEFORE beam_hook_r29 (stays LAST).
R30_MISC = {"B4_07", "A0_06"}   # A2_03 row 6e: misc agent did not build it (switch off) -> R29 pixels;   # misc agent: misc_r30.py (row 6c: B4_07 three-point flexure + cooling bundle + substrate/coating line; row 6d: A0_06 real globe + tapered arcs; row 6e: A2_03 mixed right wall)
R30_BEAM = {"A2_03"}   # B8_17: main 32-spp Q4 no (slit fan still reads as one thin column, slit line not visible from this camera; not better than R29) -> R29 pixels;   # main process: beam_hook_r30.py (row 2; pre() only)
R30_HOOKS = [(R30_MISC, "misc_r30"), (R30_BEAM, "beam_hook_r30")]
# R31 (R31_ROOT_CAUSE.md): per-row shot sets + hook modules, pre-wired by the main process, layered AFTER the R30
# hooks but BEFORE beam_hook_r29 (stays LAST and also converts every R31_BEAM shot). Remove a shot id from its R31 set ->
# exact R30 pixels. Mutate these sets, never rebind them.
R31_MISC = {"B8_17", "A0_06"}   # B6_12 row 6b: misc agent 8-spp Q4 no (sheen = hard glass plate; frame shadow invisible on the dark pattern face) -> PELL_R31 off, B6_12 out -> R30 pixels;  # misc agent: misc_r31.py (row 6a B8_17 exposure progress = counter; 6b B6_12 pellicle frame + shadow; 6c A0_06 cool city lights + sharp dots)
R31_BEAM = {"A2_03"}   # main process: beam_hook_r31.py (row 6e: A2_03 right-mirror -> top-mirror leg tapers between the two apertures; pre() only)
R31_MAIN = {"B4_10"}   # main process: misc_main_r31.py (row 6f: B4_10 laser landing spot + scatter on the ball)
R31_HOOKS = [(R31_MISC, "misc_r31"), (R31_MAIN, "misc_main_r31"), (R31_BEAM, "beam_hook_r31")]
_CUR_SHOT = [None]


def _r21(shot):
    return _CUR_SHOT[0] == shot and shot in R21_SHOTS


def _r20(shot):
    return _CUR_SHOT[0] == shot and shot in R20_SHOTS


# ------------------------------------------------------------------ helpers
def _nodes(m):
    nt = m.node_tree
    return nt, nt.nodes, nt.links


def _new_mat(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    return m


def _uv_sphere(name, loc, r, seg=96, mat=None):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=seg // 2, radius=r, location=loc)
    ob = bpy.context.active_object
    ob.name = name
    bpy.ops.object.shade_smooth()
    if mat:
        ob.data.materials.append(mat)
    return ob


def _key_value(sock, frames_vals, interp="LINEAR"):
    for f, v in frames_vals:
        sock.default_value = v
        sock.keyframe_insert("default_value", frame=f)


def _stars_world(top=(0.012, 0.018, 0.04), bottom=(0.003, 0.004, 0.01), density=420, strength=1.0, bright=0.6,
                 share=0.7):
    """Dark-blue space gradient with sparse small stars (not pure black)."""
    C.set_world(top=top, horizon=tuple((a + b) / 2 for a, b in zip(top, bottom)), bottom=bottom, strength=strength)
    w = bpy.context.scene.world
    nt = w.node_tree
    bg = nt.nodes["Background"]
    grad = bg.inputs["Color"].links[0].from_socket
    tc = nt.nodes.new("ShaderNodeTexCoord")
    vor = nt.nodes.new("ShaderNodeTexVoronoi")
    vor.inputs["Scale"].default_value = density
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = 0.0
    mr.inputs["From Max"].default_value = 0.035
    mr.inputs["To Min"].default_value = 1.0
    mr.inputs["To Max"].default_value = 0.0
    nz = nt.nodes.new("ShaderNodeTexWhiteNoise")
    nz.noise_dimensions = "3D"
    gate = nt.nodes.new("ShaderNodeMath")
    gate.operation = "GREATER_THAN"
    gate.inputs[1].default_value = share
    mul = nt.nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    mul2 = nt.nodes.new("ShaderNodeMath")
    mul2.operation = "MULTIPLY"
    mul2.inputs[1].default_value = bright
    add = nt.nodes.new("ShaderNodeMix")
    add.data_type = "RGBA"
    add.blend_type = "ADD"
    add.inputs["Factor"].default_value = 1.0
    nt.links.new(tc.outputs["Generated"], vor.inputs["Vector"])
    nt.links.new(vor.outputs["Distance"], mr.inputs["Value"])
    nt.links.new(vor.outputs["Position"], nz.inputs["Vector"])
    nt.links.new(nz.outputs["Value"], gate.inputs[0])
    nt.links.new(mr.outputs["Result"], mul.inputs[0])
    nt.links.new(gate.outputs[0], mul.inputs[1])
    nt.links.new(mul.outputs[0], mul2.inputs[0])
    nt.links.new(grad, add.inputs["A"])
    nt.links.new(mul2.outputs[0], add.inputs["B"])
    nt.links.new(add.outputs["Result"], bg.inputs["Color"])


def _earth_photo_mat():
    """R5 (k7A): photographic Earth - NASA Blue Marble colour (public domain, visibleearth.nasa.gov), glossy
    oceans, matte land. Same equirect UV layout as worldmap_land.png."""
    m = _new_mat("EarthPhoto")
    nt, n, l = _nodes(m)
    b = next(x for x in n if x.type == "BSDF_PRINCIPLED")
    uv = n.new("ShaderNodeTexCoord")
    img = n.new("ShaderNodeTexImage")
    img.image = bpy.data.images.load(os.path.join(TEX, "nasa_bluemarble_2048.jpg"), check_existing=True)
    img.interpolation = "Cubic"
    l.new(uv.outputs["UV"], img.inputs["Vector"])
    l.new(img.outputs["Color"], b.inputs["Base Color"])
    sep = n.new("ShaderNodeSeparateColor")          # ocean = blue > red -> glossy
    l.new(img.outputs["Color"], sep.inputs["Color"])
    d = n.new("ShaderNodeMath")
    d.operation = "SUBTRACT"
    l.new(sep.outputs[2], d.inputs[0])
    l.new(sep.outputs[0], d.inputs[1])
    r = n.new("ShaderNodeMapRange")
    r.inputs["From Min"].default_value = 0.0
    r.inputs["From Max"].default_value = 0.15
    r.inputs["To Min"].default_value = 0.85
    r.inputs["To Max"].default_value = 0.3
    l.new(d.outputs[0], r.inputs["Value"])
    l.new(r.outputs["Result"], b.inputs["Roughness"])
    return m


def _clouds_mat():
    """Cloud shell: white diffuse where the NASA cloud map is bright, transparent elsewhere."""
    m = _new_mat("EarthClouds")
    nt, n, l = _nodes(m)
    for x in list(n):
        if x.type != "OUTPUT_MATERIAL":
            n.remove(x)
    out = next(x for x in n if x.type == "OUTPUT_MATERIAL")
    uv = n.new("ShaderNodeTexCoord")
    img = n.new("ShaderNodeTexImage")
    img.image = bpy.data.images.load(os.path.join(TEX, "nasa_clouds_2048.jpg"), check_existing=True)
    img.image.colorspace_settings.name = "Non-Color"
    l.new(uv.outputs["UV"], img.inputs["Vector"])
    df = n.new("ShaderNodeBsdfDiffuse")
    df.inputs["Color"].default_value = (0.95, 0.95, 0.96, 1)
    tr = n.new("ShaderNodeBsdfTransparent")
    mx = n.new("ShaderNodeMixShader")
    k = n.new("ShaderNodeMath")
    k.operation = "MULTIPLY"
    k.inputs[1].default_value = 0.7
    l.new(img.outputs["Color"], k.inputs[0])
    l.new(k.outputs[0], mx.inputs["Fac"])
    l.new(tr.outputs[0], mx.inputs[1])
    l.new(df.outputs[0], mx.inputs[2])
    l.new(mx.outputs[0], out.inputs["Surface"])
    return m


def _earth_mat(night=False, dots=None, solid=False):
    """Equirect land map on a UV sphere: dark ocean, muted land (day) or faint cyan coastlines (night),
    optional supplier-dot emission revealed by an animated threshold. Returns (material, reveal_socket)."""
    m = _new_mat("Earth" + ("Night" if night else ""))
    nt, n, l = _nodes(m)
    b = next(x for x in n if x.type == "BSDF_PRINCIPLED")
    uv = n.new("ShaderNodeTexCoord")
    img = n.new("ShaderNodeTexImage")
    img.image = bpy.data.images.load(os.path.join(TEX, "worldmap_land.png"), check_existing=True)
    img.image.colorspace_settings.name = "Non-Color"
    img.interpolation = "Cubic"
    l.new(uv.outputs["UV"], img.inputs["Vector"])
    land = n.new("ShaderNodeMapRange")              # 90 (land) / 150 (coast) of 255 -> 0..1
    land.inputs["From Min"].default_value = 0.0
    land.inputs["From Max"].default_value = 0.35
    l.new(img.outputs["Color"], land.inputs["Value"])
    coast = n.new("ShaderNodeMapRange")
    coast.inputs["From Min"].default_value = 0.45
    coast.inputs["From Max"].default_value = 0.6
    l.new(img.outputs["Color"], coast.inputs["Value"])
    nz = n.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 18.0
    nz.inputs["Detail"].default_value = 10.0
    l.new(uv.outputs["Object"], nz.inputs["Vector"])
    col = n.new("ShaderNodeMix")
    col.data_type = "RGBA"
    l.new(land.outputs["Result"], col.inputs["Factor"])
    if night and solid:
        # R14 (A0_06 #1 "陆地几乎和海一样暗，玻璃壳像空泡泡"): solid land with terrain - the NASA photo darkened
        # to a dusk tone (land ~8x brighter than the ocean), so the globe reads as a planet, not a glass bubble
        ph = n.new("ShaderNodeTexImage")
        ph.image = bpy.data.images.load(os.path.join(TEX, "nasa_bluemarble_2048.jpg"), check_existing=True)
        ph.interpolation = "Cubic"
        l.new(uv.outputs["UV"], ph.inputs["Vector"])
        dk = n.new("ShaderNodeMix")
        dk.data_type = "RGBA"
        dk.blend_type = "MULTIPLY"
        dk.inputs["Factor"].default_value = 1.0
        dk.inputs["B"].default_value = (0.62, 0.62, 0.66, 1)
        l.new(ph.outputs["Color"], dk.inputs["A"])
        col.inputs["A"].default_value = (0.002, 0.006, 0.02, 1)
        l.new(dk.outputs["Result"], col.inputs["B"])
    elif night:
        col.inputs["A"].default_value = (0.003, 0.009, 0.03, 1)
        col.inputs["B"].default_value = (0.03, 0.07, 0.12, 1)
    else:
        col.inputs["A"].default_value = (0.006, 0.02, 0.07, 1)
        land_col = n.new("ShaderNodeMix")
        land_col.data_type = "RGBA"
        land_col.inputs["A"].default_value = (0.05, 0.07, 0.03, 1)
        land_col.inputs["B"].default_value = (0.16, 0.13, 0.08, 1)
        l.new(nz.outputs["Fac"], land_col.inputs["Factor"])
        l.new(land_col.outputs["Result"], col.inputs["B"])
    l.new(col.outputs["Result"], b.inputs["Base Color"])
    rough = n.new("ShaderNodeMapRange")              # glossy ocean, matte land
    rough.inputs["To Min"].default_value = 0.45 if night else 0.25
    if solid:
        rough.inputs["To Min"].default_value = 0.62            # R14: less glassy ocean sheen
    rough.inputs["To Max"].default_value = 0.8
    l.new(land.outputs["Result"], rough.inputs["Value"])
    l.new(rough.outputs["Result"], b.inputs["Roughness"])
    em_add = None
    reveal = None
    if night:
        # faint cyan coastlines
        cm = n.new("ShaderNodeMath")
        cm.operation = "MULTIPLY"
        cm.inputs[1].default_value = 0.25 if solid else 0.6
        l.new(coast.outputs["Result"], cm.inputs[0])
        em_add = cm
    if dots:
        di = n.new("ShaderNodeTexImage")
        di.image = bpy.data.images.load(dots, check_existing=True)
        di.image.colorspace_settings.name = "Non-Color"
        l.new(uv.outputs["UV"], di.inputs["Vector"])
        wn = n.new("ShaderNodeTexNoise")              # reveal order: smooth noise so dots appear region by region
        wn.inputs["Scale"].default_value = 3.0
        l.new(uv.outputs["Object"], wn.inputs["Vector"])
        rv = n.new("ShaderNodeValue")
        reveal = rv.outputs[0]
        lt = n.new("ShaderNodeMath")
        lt.operation = "LESS_THAN"
        l.new(wn.outputs["Fac"], lt.inputs[0])
        l.new(rv.outputs[0], lt.inputs[1])
        dm = n.new("ShaderNodeMath")
        dm.operation = "MULTIPLY"
        l.new(di.outputs["Color"], dm.inputs[0])
        l.new(lt.outputs[0], dm.inputs[1])
        dm2 = n.new("ShaderNodeMath")
        dm2.operation = "MULTIPLY"
        dm2.inputs[1].default_value = 9.0
        l.new(dm.outputs[0], dm2.inputs[0])
        if em_add:
            s = n.new("ShaderNodeMath")
            s.operation = "ADD"
            l.new(em_add.outputs[0], s.inputs[0])
            l.new(dm2.outputs[0], s.inputs[1])
            em_add = s
        else:
            em_add = dm2
    if em_add:
        b.inputs["Emission Color"].default_value = (*K.lin(K.CYAN), 1)
        l.new(em_add.outputs[0], b.inputs["Emission Strength"])
    return m, reveal


def _atmosphere(name, loc, r, color=(0.3, 0.55, 1.0), strength=3.0):
    m = _new_mat(name + "Mat")
    nt, n, l = _nodes(m)
    for x in list(n):
        if x.type != "OUTPUT_MATERIAL":
            n.remove(x)
    out = next(x for x in n if x.type == "OUTPUT_MATERIAL")
    lw = n.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.6
    pw = n.new("ShaderNodeMath")
    pw.operation = "POWER"
    pw.inputs[1].default_value = 3.0
    l.new(lw.outputs["Facing"], pw.inputs[0])
    em = n.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*color, 1)
    em.inputs["Strength"].default_value = strength
    tr = n.new("ShaderNodeBsdfTransparent")
    mx = n.new("ShaderNodeMixShader")
    l.new(pw.outputs[0], mx.inputs["Fac"])
    l.new(tr.outputs[0], mx.inputs[1])
    l.new(em.outputs[0], mx.inputs[2])
    l.new(mx.outputs[0], out.inputs["Surface"])
    return _uv_sphere(name, loc, r, 64, m)


def _bump_mat(name, color, rough, voronoi_scale, noise_scale, bump=0.6, dimples=False, metal=0.0):
    m = _new_mat(name)
    nt, n, l = _nodes(m)
    b = next(x for x in n if x.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (*K.lin(color), 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    tc = n.new("ShaderNodeTexCoord")
    vor = n.new("ShaderNodeTexVoronoi")
    vor.inputs["Scale"].default_value = voronoi_scale
    l.new(tc.outputs["Object"], vor.inputs["Vector"])
    bp = n.new("ShaderNodeBump")
    bp.inputs["Strength"].default_value = bump
    if dimples:
        # golf-ball dimples: smooth bowls around each voronoi cell centre
        mr = n.new("ShaderNodeMapRange")
        mr.inputs["From Min"].default_value = 0.0
        mr.inputs["From Max"].default_value = 0.42
        mr.inputs["To Min"].default_value = 0.0
        mr.inputs["To Max"].default_value = 1.0
        mr.clamp = True
        l.new(vor.outputs["Distance"], mr.inputs["Value"])
        l.new(mr.outputs["Result"], bp.inputs["Height"])
        vor.feature = "F1"
    else:
        nz = n.new("ShaderNodeTexNoise")
        nz.inputs["Scale"].default_value = noise_scale
        nz.inputs["Detail"].default_value = 12.0
        l.new(tc.outputs["Object"], nz.inputs["Vector"])
        # craters: rim + bowl from voronoi distance, plus fine noise
        cr = n.new("ShaderNodeFloatCurve")
        cm = cr.mapping
        cm.curves[0].points[0].location = (0.0, 0.0)
        cm.curves[0].points[1].location = (1.0, 0.55)
        cm.curves[0].points.new(0.18, 0.35)
        cm.curves[0].points.new(0.26, 0.62)
        cm.curves[0].points.new(0.34, 0.5)
        cm.update()
        l.new(vor.outputs["Distance"], cr.inputs["Value"])
        ad = n.new("ShaderNodeMath")
        ad.operation = "ADD"
        l.new(cr.outputs[0], ad.inputs[0])
        sc = n.new("ShaderNodeMath")
        sc.operation = "MULTIPLY"
        sc.inputs[1].default_value = 0.35
        l.new(nz.outputs["Fac"], sc.inputs[0])
        l.new(sc.outputs[0], ad.inputs[1])
        fine = n.new("ShaderNodeTexNoise")               # regolith grain for the golf-ball close-up
        fine.inputs["Scale"].default_value = 900.0
        fine.inputs["Detail"].default_value = 6.0
        l.new(tc.outputs["Object"], fine.inputs["Vector"])
        fs = n.new("ShaderNodeMath")
        fs.operation = "MULTIPLY"
        fs.inputs[1].default_value = 0.08
        l.new(fine.outputs["Fac"], fs.inputs[0])
        ad2 = n.new("ShaderNodeMath")
        ad2.operation = "ADD"
        l.new(ad.outputs[0], ad2.inputs[0])
        l.new(fs.outputs[0], ad2.inputs[1])
        l.new(ad2.outputs[0], bp.inputs["Height"])
        # albedo variation (maria)
        nz2 = n.new("ShaderNodeTexNoise")
        nz2.inputs["Scale"].default_value = 2.2
        nz2.inputs["Detail"].default_value = 4.0
        l.new(tc.outputs["Object"], nz2.inputs["Vector"])
        ramp = n.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].position = 0.42
        ramp.color_ramp.elements[0].color = (*K.lin(tuple(c * 0.55 for c in color)), 1)
        ramp.color_ramp.elements[1].position = 0.6
        ramp.color_ramp.elements[1].color = (*K.lin(color), 1)
        l.new(nz2.outputs["Fac"], ramp.inputs["Fac"])
        l.new(ramp.outputs["Color"], b.inputs["Base Color"])
    l.new(bp.outputs["Normal"], b.inputs["Normal"])
    return m


def _sun(name, rot, energy, color=(1, 0.97, 0.92), angle=0.5):
    l = bpy.data.lights.new(name, "SUN")
    l.energy = energy
    l.color = color
    l.angle = math.radians(angle)
    ob = bpy.data.objects.new(name, l)
    bpy.context.scene.collection.objects.link(ob)
    ob.rotation_euler = rot
    return ob


def _laser(a, b, r=0.02, name="Laser", r_end=None, color=None):
    color = K.ORANGE if color is None else color
    mb, mh = K.MB(), K.MB()
    if r_end is None:
        K.beam(mb, mh, [a, b], r=r, halo=4.0)
    else:                                    # tapered: wide enough to read from Earth, needle-thin at the target
        mb.tube(a, b, r, seg=12, r2=r_end)
        mh.tube(a, b, r * 4.0, seg=16, r2=r_end * 3.0)
    o1 = mb.obj(name, K.emit_mat(name + "Core", color, 30.0))
    o2 = mh.obj(name + "Halo", K.emit_mat(name + "HaloM", color, 4.0, halo=0.5))
    for o_ in (o1, o2):                       # R14: the beam cast a long dark line across the Moon
        o_.visible_shadow = False


def _dof(cam, fstop, focus_obj=None, dist=None):
    cam.data.dof.use_dof = True
    cam.data.dof.aperture_fstop = fstop
    if focus_obj is not None:
        cam.data.dof.focus_object = focus_obj
    elif dist:
        cam.data.dof.focus_distance = dist


# ------------------------------------------------------------------ R14 beam look (root cause #1)
# R13 review: beams read as constant-width ribbons with capsule end caps. R14: open (uncapped) soft-edged cones
# that open / narrow between landing spots; the only highlight is a soft disc ON the mirror where the light lands.
def _open_cone(mb, a, b, ra, rb, seg=48):
    """Uncapped cone shell a -> b (no end discs = no capsule ends)."""
    m, L = K._orient(a, b)
    if L < 1e-5:
        return
    bm = mb.bm
    ring = []
    for z, r in ((-L / 2, ra), (L / 2, rb)):
        ring.append([bm.verts.new(m @ Vector((r * math.cos(2 * math.pi * i / seg), r * math.sin(2 * math.pi * i / seg), z)))
                     for i in range(seg)])
    p, q = ring
    for i in range(seg):
        j = (i + 1) % seg
        f = bm.faces.new((p[i], p[j], q[j], q[i]))
        f.smooth = True


def _soft_beam_mat(name, color=None, strength=2.2, alpha=0.75, power=1.6, invert=False):
    import beam_r12 as BR                     # material only: never BR.install() here (it swaps kit globals)
    return BR.soft_mat(name, K.VIOLET if color is None else color, strength, alpha, power, invert)


def _landing_spot(mb, p, nrm, r):
    """Soft footprint: three stacked discs just above the mirror plane (halo emission)."""
    q = Vector((0, 0, 1)).rotation_difference(Vector(nrm).normalized())
    for k, f in enumerate((1.0, 0.62, 0.32)):
        mb.cyl(Vector(p) + Vector(nrm).normalized() * (0.004 + 0.002 * k), r * f, 0.001, rot=q.to_euler(), seg=40)


def _r14_columns_factory(spots, keep=None):
    """Drop-in for K.beam_columns inside build_cutaway_r2.machine (only for the A2_03 / A2_08 backdrop): legs
    alternate opening / narrowing (wide footprint on one mirror, narrow on the next), no waists, no beads, open
    cones; landing spots are collected into `spots` and built once by the caller."""
    def cols(mb, pts, radii, seg=40):
        pts = [Vector(p) for p in pts]
        s = [max(r, 0.004) for r in radii]
        wide = True
        for j in range(1, len(s) - 1):
            s[j] = s[j] if wide else s[j] * 0.38
            wide = not wide
        # R15 (root cause #4, A2_03 "背景 4–5 根光柱成网压公式"): keep = (lo, hi) draws only legs lo..hi-1 - ONE
        # continuous W-shaped fold (the PO zig-zag), every other leg of the machine path is left out
        lo, hi = keep if keep else (0, len(pts) - 1)
        for i, ((a, b), (ra, rb)) in enumerate(zip(zip(pts, pts[1:]), zip(s, s[1:]))):
            if lo <= i < hi:
                _open_cone(mb, a, b, ra, rb, seg=seg)
        for j in range(max(1, lo), min(len(pts) - 1, hi + 1)):
            spots.append((pts[j], K.mirror_normal(pts[j - 1], pts[j], pts[j + 1]), max(0.03, s[j] * 1.3)))
    return cols


# ------------------------------------------------------------------ variants
def _space(sc, n):
    _stars_world(density=260, bright=5.0, share=0.5)          # R8: a visible star field, not an empty blue void
    E = Vector((0, 0, 0))
    MO = Vector((44, 16, 4))
    earth_r, moon_r = 5.0, 1.36
    earth = _uv_sphere("Earth", E, earth_r, 128, _earth_photo_mat())      # R5: photographic Earth (k7A)
    earth.rotation_euler = (math.radians(15), 0, math.radians(-105))
    cl = _uv_sphere("Clouds", E, earth_r * 1.008, 128, _clouds_mat())
    cl.rotation_euler = earth.rotation_euler
    _atmosphere("Atmos", E, earth_r * 1.035, strength=4.0)
    moon = _uv_sphere("Moon", MO, moon_r, 128, _bump_mat("MoonMat", (0.55, 0.54, 0.52), 0.85, 7.0, 40.0, bump=0.8))
    # golf ball on the lunar surface facing the incoming beam
    dirb = (E - MO).normalized()
    nrm = (dirb + Vector((0, 0, 0.55))).normalized()
    ball_r = 0.024
    surf = MO + nrm * moon_r
    ball = _uv_sphere("GolfBall", surf + nrm * ball_r * 0.9, ball_r, 96,
                      _bump_mat("Golf", (0.93, 0.93, 0.92), 0.35, 260.0, 0, bump=0.9, dimples=True))
    ball.scale = (1, 1, 1)
    # R17 (root cause #4 landing surface, B4_10 "凹坑随机大小，像一颗小月球"): the light must land on something that
    # reads as a golf ball - regular near-hexagonal dimples in white glossy plastic (geometry, not voronoi bump)
    import misc_beam_r17 as BR17
    _bl = ball.location.copy()
    bpy.data.objects.remove(ball, do_unlink=True)
    ball = BR17.golf_ball_r17("GolfBall", _bl, ball_r, K.mat("GolfR17", (0.94, 0.94, 0.93), rough=0.28, coat=0.6),
                              depth=0.03, subdiv=7)
    # tee-like little dust ring under the ball
    start = E + (ball.location - E).normalized() * earth_r * 1.01
    # R14 (B4_10 #3): leave from a ground point on the camera-facing hemisphere (the R13 start sat on the limb, so
    # the beam seemed to come out of the atmosphere edge)
    _dcam = Vector((-9.0, -14.0, 3.5)).normalized()
    _up = ((ball.location - E).normalized() + _dcam * 1.1).normalized()
    start = E + _up * earth_r * 1.011
    # R14 (root cause #7, B4_10 #1): metaphor beam is cold white - orange is reserved for the CO2 drive laser
    COLD = (0.82, 0.92, 1.0)
    # R16 (root cause #3, B4_10 "光束一样粗，到球上像插进去"): the beam is a soft cone that narrows to a pin and fades
    # out in the last few cm before the ball; a small landing spot on the ball face marks where it arrives
    import misc_kit_r16 as MK
    _hit = ball.location + (start - ball.location).normalized() * ball_r * 1.01
    _Lb = (_hit - start).length
    _st = [k / 40 for k in range(40)] + [1 - x / _Lb for x in (0.4, 0.2, 0.1, 0.05, 0.03, 0.015, 0.006)] + [1.0]
    _st = sorted(set(_st))
    _ff = 0.045 / _Lb                                    # fade over the last ~4.5 cm (ball = 4.8 cm)
    MK.fade_cone("Laser", start, _hit, 0.03, 0.0006,
                 MK.fade_beam_mat("LaserR16", COLD, 16.0, 1.0, 0.8, fade0=0.004, fade1=_ff), seg=16, stations=_st,
                 core=0)
    MK.fade_cone("LaserHalo", start, _hit, 0.12, 0.0015,
                 MK.fade_beam_mat("LaserHaloR16", COLD, 5.0, 0.5, 1.2, fade0=0.004, fade1=_ff * 2.5), seg=16,
                 stations=_st, core=0)
    # R17 (root cause #4, B4_10 −3.14): change ROUTE - no halo shell, no needle fade: the beam is ONE thin cold core
    # from the station to the ball (slight taper), it ends hard ON the ball face where a landing highlight + a
    # small light make the ball itself light up
    for nm in ("Laser", "LaserHalo"):
        bpy.data.objects.remove(bpy.data.objects[nm], do_unlink=True)
    BR17.thin_core("LaserR17", start, _hit, 0.016, COLD, 14.0, 1.0, fade0=0.002, seg=16, r_end=0.0006)
    _bh = K.point("BallHitR17", _hit + (start - ball.location).normalized() * 0.012, 0.006, COLD, 0.004)
    _bh.visible_camera = False
    _bh.visible_glossy = False
    # R14 (B4_10 #3 "激光从大气层边缘凭空出来"): a visible emitter on the ground - a small observatory pad + dome
    # on the Earth's surface with a soft footprint glow where the beam leaves it
    up = _up
    g0 = E + up * earth_r * 1.0095                              # above the cloud shell (1.008 r), else hidden
    q = Vector((0, 0, 1)).rotation_difference(up)
    em = K.MB()
    em.cyl(g0, 0.11, 0.012, rot=q.to_euler(), seg=40)
    em.sphere(g0 + up * 0.012, 0.045, 20)
    em.obj("Emitter", K.mat("EmitterDome", (0.85, 0.86, 0.88), metal=0.6, rough=0.25))
    eg = K.MB()
    _landing_spot(eg, g0 + up * 0.02, up, 0.3)
    eg.obj("EmitterGlow", K.emit_mat("EmitterGlowM", COLD, 9.0, halo=0.6))
    # R17 (B4_10 R16 "激光从地球边缘插进去"): the beam leaves from ONE visible bright station point on the ground
    _uv_sphere("StationR17", g0 + up * 0.03, 0.08, 16, K.emit_mat("StationR17M", COLD, 40.0))
    # R8: Earth-Moon distance rule under the beam (dashed, end ticks), scale cue for "380,000 km"
    rl = K.MB()
    e0, m0 = E + (MO - E).normalized() * (earth_r + 0.6), MO - (MO - E).normalized() * (moon_r + 0.6)
    off = Vector((0, 0, -2.2))
    for k in range(40):
        a_, b_ = e0.lerp(m0, k / 40), e0.lerp(m0, (k + 0.55) / 40)
        rl.tube(a_ + off, b_ + off, 0.03, seg=6)
    for p_ in (e0, m0):
        rl.tube(p_ + off + Vector((0, 0, -0.5)), p_ + off + Vector((0, 0, 0.5)), 0.035, seg=6)
    # R15 (root cause #4, B4_10 "零碎青色虚线段像断掉的尺寸线"): the dashed rule passes the camera in the middle
    # third and reads as broken fragments -> removed; the distance lives in the Moon tag only
    rl.bm.free()
    # R16: flat soft landing spot ON the ball face toward Earth (was a glowing sphere poking out = 'plugged in')
    _dir = (start - ball.location).normalized()
    MK.spot_cap("Spot", ball.location, ball_r * 1.006, _dir, 16, K.emit_mat("SpotR16", COLD, 3.0, halo=0.35))
    MK.spot_cap("SpotCore", ball.location, ball_r * 1.008, _dir, 6, K.emit_mat("SpotCoreR16", COLD, 10.0, halo=0.7))
    # R17: the dimpled ball surface sits up to 3 % below r -> landing highlight = one soft cap hugging the ball
    for nm in ("Spot", "SpotCore"):
        bpy.data.objects.remove(bpy.data.objects[nm], do_unlink=True)
    MK.spot_cap("SpotR17", ball.location, ball_r * 1.004, _dir, 8, K.emit_mat("SpotR17M", COLD, 2.0, halo=0.35))
    MK.spot_cap("SpotCoreR17", ball.location, ball_r * 1.006, _dir, 3, K.emit_mat("SpotCoreR17M", COLD, 10.0, halo=0.8))
    # R14 (B4_10 #3): contact shadow so the ball sits ON the regolith (soft dark disc under it)
    sh = _new_mat("BallContactShadow")
    nt_, nn_, l_ = _nodes(sh)
    for x in list(nn_):
        if x.type != "OUTPUT_MATERIAL":
            nn_.remove(x)
    o_ = next(x for x in nn_ if x.type == "OUTPUT_MATERIAL")
    tco = nn_.new("ShaderNodeTexCoord")
    gr = nn_.new("ShaderNodeTexGradient")
    gr.gradient_type = "SPHERICAL"
    mp_ = nn_.new("ShaderNodeMapping")
    mp_.inputs["Scale"].default_value = (1.0, 1.0, 1.0)
    l_.new(tco.outputs["Object"], mp_.inputs["Vector"])
    l_.new(mp_.outputs["Vector"], gr.inputs["Vector"])
    pw_ = nn_.new("ShaderNodeMath")
    pw_.operation = "POWER"
    pw_.inputs[1].default_value = 1.6
    l_.new(gr.outputs["Fac"], pw_.inputs[0])
    k_ = nn_.new("ShaderNodeMath")
    k_.operation = "MULTIPLY"
    k_.inputs[1].default_value = 0.85
    l_.new(pw_.outputs[0], k_.inputs[0])
    tr_ = nn_.new("ShaderNodeBsdfTransparent")
    dk_ = nn_.new("ShaderNodeBsdfDiffuse")
    dk_.inputs["Color"].default_value = (0.0, 0.0, 0.0, 1)
    mx_ = nn_.new("ShaderNodeMixShader")
    l_.new(k_.outputs[0], mx_.inputs["Fac"])
    l_.new(tr_.outputs[0], mx_.inputs[1])
    l_.new(dk_.outputs[0], mx_.inputs[2])
    l_.new(mx_.outputs[0], o_.inputs["Surface"])
    shm = K.MB()
    shm.cyl(Vector((0, 0, 0)), 1.0, 0.0005, seg=48)
    sho = shm.obj("BallShadow", sh)
    sho.location = surf + nrm * 0.0008
    sho.rotation_euler = Vector((0, 0, 1)).rotation_difference(nrm).to_euler()
    sho.scale = (ball_r * 1.7, ball_r * 1.7, 1.0)
    _sun("Sun", (math.radians(60), math.radians(10), math.radians(-40)), 4.0)
    K.point("BallFill", ball.location + nrm * 0.2 + Vector((0.1, -0.1, 0.05)), 2.0, (0.8, 0.85, 1.0), 0.05)
    side = nrm.cross(dirb).normalized()
    cam, tgt = K.camera("CamR2", lens=35)
    cam.data.clip_start = 0.002
    # earth hero -> beam crossing toward moon -> golf ball close-up
    b = ball.location
    K.key_path(cam, tgt, [
        (1, (-9.0, -14.0, 3.5), (6.0, 3.0, 0.5)),
        (round(n * 0.3), (-4.0, -12.0, 3.0), (14.0, 6.0, 1.5)),
        (round(n * 0.55), (30.0, 6.0, 5.5), MO + Vector((0, 0, 0.2))),
        (round(n * 0.75), b + side * 0.9 + nrm * 0.45 + dirb * 0.3, b),
        (n, b + side * 0.2 + nrm * 0.05 + dirb * 0.06, b)])
    sc["glare_strength"] = 0.35
    return cam


SUPPLIER_HUBS = [  # (lon, lat, weight) illustrative regional hubs; NL is the destination
    (5.5, 51.5, 30), (8.5, 49.5, 25), (11.5, 48.2, 12), (4.4, 50.8, 8), (2.3, 48.9, 8), (-1.5, 52.5, 6),
    (8.5, 47.3, 6), (10.0, 45.5, 5), (14.4, 50.1, 3), (19.0, 47.5, 2), (-3.7, 40.4, 2), (18.0, 59.3, 2),
    (-122.0, 37.4, 10), (-71.0, 42.4, 6), (-97.7, 30.3, 4), (-112.0, 33.4, 4), (-74.0, 40.7, 4),
    (139.7, 35.7, 8), (135.5, 34.7, 5), (127.0, 37.5, 6), (121.0, 24.8, 6), (121.5, 31.2, 4), (114.1, 22.5, 3),
    (103.8, 1.35, 3), (77.6, 12.9, 2), (34.8, 32.1, 3)]
NL = (5.47, 51.44)
# R17: 8 supplier regions (illustrative share, from the hub weights above; NL itself is the landing ring)
SUPPLIER_REGIONS_R17 = [(11.5, 48.2, 48), (-0.5, 47.0, 21), (-118.0, 35.5, 18), (-73.5, 41.5, 10),
                        (134.0, 36.0, 19), (119.5, 27.5, 13), (34.8, 32.1, 3), (92.0, 10.0, 5)]


def _ll(lon, lat, r):
    """lon/lat -> point on a UV sphere made by primitive_uv_sphere_add (texture u = 0.5 at +X, 0.75 at +Y)."""
    lo, la = math.radians(lon), math.radians(lat)
    return Vector((r * math.cos(la) * math.cos(lo), r * math.cos(la) * math.sin(lo), r * math.sin(la)))

# R18: supplier regions in lighting order (Europe first, then North America, East Asia, rest); weight = share of
# the 5100 points (illustrative distribution); spread in degrees (lon, lat)
SUPPLIER_REGIONS_R18 = [
    ("eu", 2250, [(5.5, 51.5, 30, 1.2, 0.8), (8.5, 49.5, 25, 2.0, 1.3), (11.5, 48.2, 12, 1.6, 1.0), (4.4, 50.8, 8, 0.9, 0.6),
                  (2.3, 48.9, 8, 1.8, 1.4), (-1.5, 52.5, 6, 1.6, 1.4), (8.5, 47.3, 6, 1.0, 0.6), (10.0, 45.5, 5, 1.6, 0.9),
                  (14.4, 50.1, 3, 1.4, 0.8), (19.0, 47.5, 2, 1.6, 1.0), (-3.7, 40.4, 2, 2.2, 1.6), (18.0, 59.3, 2, 2.0, 1.2),
                  (10.1, 48.8, 10, 0.8, 0.5)]),
    ("us", 1350, [(-122.0, 37.4, 10, 1.2, 1.4), (-71.0, 42.4, 6, 1.4, 1.0), (-97.7, 30.3, 4, 1.8, 1.4), (-112.0, 33.4, 4, 1.5, 1.2),
                  (-74.0, 40.7, 4, 1.2, 0.9), (-87.6, 41.9, 3, 2.0, 1.2), (-84.4, 33.7, 2, 2.0, 1.4), (-79.4, 43.7, 2, 1.6, 0.8)]),
    ("asia", 1150, [(139.7, 35.7, 8, 1.4, 1.0), (135.5, 34.7, 5, 1.2, 0.8), (127.0, 37.5, 6, 0.9, 0.8), (121.0, 24.8, 6, 0.6, 0.7),
                    (121.5, 31.2, 4, 1.2, 1.0), (114.1, 22.5, 3, 1.0, 0.7)]),
    ("rest", 350, [(103.8, 1.35, 3, 0.5, 0.5), (77.6, 12.9, 2, 2.0, 2.0), (34.8, 32.1, 3, 0.6, 0.8), (-46.6, -23.5, 1, 2.0, 1.5),
                   (151.2, -33.9, 1, 1.5, 1.0)])]
TRUNKS_R18 = [(11.5, 48.2), (2.3, 48.9), (-1.5, 52.5), (10.0, 45.5), (19.0, 47.5), (18.0, 59.3), (-3.7, 40.4),
              (-71.0, 42.4), (-74.0, 40.7), (-79.4, 43.7), (-84.4, 33.7), (-87.6, 41.9), (-97.7, 30.3), (-112.0, 33.4),
              (-122.0, 37.4), (34.8, 32.1)]


def _globe_r18(sc, n, R, nl, RING):
    import misc_beam_r18 as BR18
    rnd = random.Random(18)
    pts = []
    region_end = {}
    for key, total, hubs in SUPPLIER_REGIONS_R18:
        wsum = sum(h[2] for h in hubs)
        reg = []
        for lon, lat, w, slon, slat in hubs:
            k = max(1, round(total * w / wsum))
            for _ in range(k):
                lo, la = lon + rnd.gauss(0, slon * 1.6), lat + rnd.gauss(0, slat * 1.5)   # spread: a web, not a blob
                reg.append((rnd.random(), _ll(lo, la, R * 1.0025)))
        reg.sort(key=lambda x: x[0])                 # random order inside a region, regions strictly in sequence
        pts += [p for _r, p in reg]
        region_end[key] = len(pts)
    scale = 5100.0 / len(pts)

    def count(f):                                    # same curve as the counter overlay (t = (f - 1) / 24)
        u = ((f - 1) / 24.0) / (n / 24.0)
        x = max(0.0, min(1.0, (u - 0.02) / 0.8))
        return 5100.0 * x * x * (3 - 2 * x) / scale
    dot_m = K.emit_mat("SupplierDotR18", (0.2, 0.82, 1.0), 2.2)
    BR18.supplier_points("SupplierDotsR18", pts, 0.0062, dot_m, [(f, count(f)) for f in range(1, n + 2)])
    # trunk arcs: low great-circle routes hugging the globe, from a hub ON the surface to the NL ring ON the surface
    arc_m = K.emit_mat("TrunkArcR18", K.CYAN, 3.0)
    for k, (lon, lat) in enumerate(TRUNKS_R18):
        a = _ll(lon, lat, R)
        _ang = a.normalized().angle(nl.normalized())
        if _ang < 1e-3:
            continue
        t1 = max(0.2, 1.0 - (RING / R) / _ang)
        h = 0.004 + 0.022 * _ang / math.pi
        cd = bpy.data.curves.new(f"TrunkR18_{k}", "CURVE")
        cd.dimensions = "3D"
        sp = cd.splines.new("POLY")
        N = 64
        sp.points.add(N - 1)
        for i in range(N):
            t = t1 * i / (N - 1)
            p = a.normalized().slerp(nl.normalized(), t)
            sp.points[i].co = (*(p.normalized() * (R * (1.002 + h * math.sin(math.pi * t / t1)))), 1)
        cd.bevel_depth = 0.0042
        cd.bevel_resolution = 2
        ob = bpy.data.objects.new(f"TrunkR18_{k}", cd)
        sc.collection.objects.link(ob)
        ob.data.materials.append(arc_m)
        ob.visible_shadow = False
        # an arc starts growing when its region's points are lit (Europe first, Americas mid, Israel last)
        reg = "us" if lon < -30 else ("rest" if lon > 30 else "eu")
        f0 = {"eu": 0.06, "us": 0.28, "rest": 0.5}[reg] + 0.02 * (k % 5)
        st = 1 + int(n * f0)
        cd.bevel_factor_end = 0.0
        cd.keyframe_insert("bevel_factor_end", frame=st)
        cd.bevel_factor_end = 1.0
        cd.keyframe_insert("bevel_factor_end", frame=st + int(n * 0.12))
        # a small bright origin node on the surface at the arc's start
        no = _uv_sphere(f"TrunkNodeR18_{k}", _ll(lon, lat, R * 1.003), 0.012, 12, K.emit_mat(f"TrunkNodeR18M{k}", (0.7, 0.97, 1.0), 6.0))
        no.hide_render = True
        no.keyframe_insert("hide_render", frame=1)
        no.keyframe_insert("hide_render", frame=st - 1)
        no.hide_render = False
        no.keyframe_insert("hide_render", frame=st)


def _globe(sc, n):
    _stars_world(top=(0.01, 0.016, 0.035), density=260, bright=5.0, share=0.5)   # R8: star field
    R = 2.0
    m, reveal = _earth_mat(night=True, dots=os.path.join(TEX, "worldmap_dots.png"), solid=True)
    g = _uv_sphere("Globe", (0, 0, 0), R, 160, m)
    _atmosphere("GlobeAtmo", (0, 0, 0), R * 1.015, color=(0.2, 0.55, 0.95), strength=0.6)   # R14: shell halved
    _key_value(reveal, [(1, 0.18), (round(n * 0.85), 0.9), (n, 0.95)])
    # arcs to the Netherlands
    nl = _ll(*NL, R)
    rnd = random.Random(6)
    arc_mat = K.emit_mat("ArcCyan", K.CYAN, 6.0)
    # R16 (root cause #5, A0_06 "弧线在荷兰汇成白爆点"): arcs at half brightness and they END on a ring around the NL
    # node (ring radius RING) instead of all meeting in one point
    arc_mat = K.emit_mat("ArcCyanR16", K.CYAN, 3.0)
    RING = 0.11
    pts = []
    for lon, lat, w in SUPPLIER_HUBS:
        for _ in range(max(1, w // 4)):
            pts.append((lon + rnd.gauss(0, 3), lat + rnd.gauss(0, 2)))
    for i, (lon, lat) in enumerate(pts):
        a = _ll(lon, lat, R)
        if (a - nl).length < 0.05:
            continue
        cd = bpy.data.curves.new(f"Arc{i}", "CURVE")
        cd.dimensions = "3D"
        sp = cd.splines.new("POLY")
        N = 24
        sp.points.add(N - 1)
        h = 0.02 + 0.07 * (a - nl).length / (2 * R)          # R8: arcs hug the globe (great-circle routes)
        h = 0.006 + 0.03 * (a - nl).length / (2 * R)         # R14 (A0_06 #2): lower still - routes on the surface
        t_end = 1.0
        _ang = a.normalized().angle(nl.normalized())
        if _ang > 1e-4:
            t_end = max(0.2, 1.0 - (RING / R) / _ang)
        for k in range(N):
            t = t_end * k / (N - 1)
            p = a.normalized().slerp(nl.normalized(), t) if hasattr(Vector, "slerp") else a.lerp(nl, t)
            p = p.normalized() * (R * (1.0 + h * math.sin(math.pi * t / t_end) * 1.0))
            sp.points[k].co = (*p, 1)
        cd.bevel_depth = 0.0035
        cd.bevel_resolution = 2
        cd.use_fill_caps = True
        ob = bpy.data.objects.new(f"Arc{i}", cd)
        sc.collection.objects.link(ob)
        ob.data.materials.append(arc_mat)
        st = 1 + int(n * (0.12 + 0.55 * rnd.random()))
        cd.bevel_factor_end = 0.0
        cd.keyframe_insert("bevel_factor_end", frame=st)
        cd.bevel_factor_end = 1.0
        cd.keyframe_insert("bevel_factor_end", frame=st + int(n * 0.25))
    # R15 (root cause #4, A0_06 "光点挤在西欧成一团白噪点，读不出一张网"): one glowing cluster node per supplier
    # region (size ~ weight) that lights up when its arcs arrive; arcs land on these, NL main node one size up
    hub_mat = K.emit_mat("HubCyan", (0.7, 0.95, 1.0), 9.0)
    hub_halo = K.emit_mat("HubHalo", K.CYAN, 1.6, halo=0.6)
    for k, (lon, lat, w) in enumerate(SUPPLIER_HUBS):
        p = _ll(lon, lat, R * 1.003)
        if (p - nl).length < 0.12:
            continue
        r_ = 0.011 + 0.0045 * math.sqrt(w)
        core = _uv_sphere(f"Hub{k}", p, r_, 16, hub_mat)
        halo = _uv_sphere(f"HubHalo{k}", p, r_ * 2.6, 16, hub_halo)
        t_on = 1 + int(n * (0.1 + 0.5 * (k / len(SUPPLIER_HUBS))))
        for ob in (core, halo):
            ob.hide_render = True
            ob.keyframe_insert("hide_render", frame=1)
            ob.keyframe_insert("hide_render", frame=t_on - 1)
            ob.hide_render = False
            ob.keyframe_insert("hide_render", frame=t_on)
    # R16: NL = a small dim core inside a thin bright ring where the routes arrive (was a 25x white sphere + halo)
    import misc_kit_r16 as MK
    _uv_sphere("NLPoint", nl * 1.003, 0.018, 24, K.emit_mat("NLCoreR16", (0.85, 0.95, 1.0), 5.0))
    rmb = K.MB()
    MK.spot_ring(rmb, nl * 1.004, nl.normalized(), RING, w=0.14)
    rmb.obj("NLRing", K.emit_mat("NLRingR16", (0.75, 0.95, 1.0), 5.0))
    _sun("Sun", (math.radians(55), 0, math.radians(-30)), 2.6, (0.8, 0.88, 1.0))   # R14: key up, light ratio >= 8:1
    _sun("SunRim", (math.radians(100), 0, math.radians(160)), 3.0, (1.0, 0.92, 0.8))   # R8: terminator / rim light
    # turn Europe toward the camera (camera on -Y): rotate so lon 5 sits at -Y
    g.rotation_euler = (0, 0, 0)
    cam, tgt = K.camera("CamR2", lens=50)
    cn = _ll(8, 38, 1).normalized()
    # R15 (A0_06 "机位几乎不动"): the globe view turns ~40 deg west while pushing in, so the US clusters come over
    # the limb in the last third (parallax + "a worldwide web")
    ce = _ll(-28, 40, 1).normalized()
    K.key_path(cam, tgt, [(1, tuple(cn * 8.6 + Vector((0.4, 0, -0.6))), (0, 0, 0.35)),
                          (n, tuple(ce * 7.4), tuple(_ll(-12, 42, R) * 0.45))])
    # R17 (root cause #4 applied to the globe = ONE readable path per supplier region into ONE landing point;
    # A0_06 R16 "欧洲堆成一团白色噪点，读不出一张网" / "地球顶部被裁"): the scattered dot texture and the ~40 jittered
    # arcs + 26 hub blobs are replaced by 8 regional discs (area ~ supplier share) each sending one route that
    # lands on the NL ring; camera aim raised ~10 % of frame so Scandinavia / N. America sit whole in frame
    for nd in m.node_tree.nodes:
        if nd.type == "MATH" and nd.operation == "MULTIPLY" and abs(nd.inputs[1].default_value - 9.0) < 1e-6:
            nd.inputs[1].default_value = 0.0
    for ob in list(bpy.data.objects):
        if ob.name.startswith(("Arc", "Hub")):
            bpy.data.objects.remove(ob, do_unlink=True)
    # R18 (root cause #3, BRIEF "一张地图和 5100 个光点把抽象数字变成一张网"; R17 review A0_06 #1/#2): the 8 R17 discs
    # + routes are replaced by ~5100 small cyan surface points (instanced, dense in Europe / USA / East Asia) lit in
    # lighting order region by region as the counter climbs (957 -> 3,605 -> 5,100), plus 14 low trunk arcs whose
    # BOTH ends sit on the surface (supplier hub -> NL ring), no arc leaves the globe
    # R19 (root cause #5, A0_06 R18 "东亚（日本、韩国、台湾）一个点都没有…改法：在日本、韩国、台湾、新加坡各补一簇光点和 1–2 条弧线。
    # 最后一帧把镜头拉远到能同时看见欧亚和北美"): Japan / Korea / Taiwan / Singapore get denser clusters + one trunk arc each
    # (5100-point network and landing arcs kept); the camera turns NORTH and pulls back (8.6 -> 12.6 R-units) to a high
    # view over the Arctic (lat 72, lon 25) where Eurasia, East Asia and North America are on the visible hemisphere
    global SUPPLIER_REGIONS_R18, TRUNKS_R18
    _reg18, _tr18 = SUPPLIER_REGIONS_R18, TRUNKS_R18
    SUPPLIER_REGIONS_R18 = [r for r in _reg18 if r[0] in ("eu", "us")] + [
        ("asia", 1250, [(139.7, 35.7, 8, 1.4, 1.0), (135.5, 34.7, 5, 1.2, 0.8), (127.0, 37.5, 7, 0.9, 0.8),
                        (128.6, 35.9, 3, 0.7, 0.6), (121.0, 24.8, 7, 0.6, 0.7), (120.3, 22.7, 3, 0.5, 0.5),
                        (121.5, 31.2, 4, 1.2, 1.0), (114.1, 22.5, 3, 1.0, 0.7), (103.8, 1.35, 4, 0.45, 0.4)]),
        ("rest", 250, [(77.6, 12.9, 2, 2.0, 2.0), (34.8, 32.1, 3, 0.6, 0.8), (-46.6, -23.5, 1, 2.0, 1.5),
                       (151.2, -33.9, 1, 1.5, 1.0)])]
    TRUNKS_R18 = list(_tr18) + [(139.7, 35.7), (127.0, 37.5), (121.0, 24.8), (103.8, 1.35), (135.5, 34.7)]
    try:
        _globe_r18(sc, n, R, nl, RING)
    finally:
        SUPPLIER_REGIONS_R18, TRUNKS_R18 = _reg18, _tr18
    cam.animation_data_clear()
    tgt.animation_data_clear()
    cf = _ll(25, 72, 1).normalized()
    K.key_path(cam, tgt, [(1, tuple(cn * 8.6 + Vector((0.4, 0, -0.6))), (0, 0, 0.62)),
                          (round(n * 0.45), tuple(_ll(0, 47, 1).normalized() * 9.4), (0, 0, 0.55)),
                          (n, tuple(cf * 12.6), (0, 0, 0.12))])
    K.anchors("A0_06", {"nl": nl})
    return cam


def _mirror(sc, n):
    K.world_dark(1.0)
    M = K.palette()
    # spherical-cap mirror with a removed wedge: the cut face shows substrate + a thin bright coating band
    R, sag_r, th = 1.2, 6.0, 0.4          # R5: thick solid glass-ceramic blank (R4 read as a thin bowl)
    bm = bmesh.new()
    nr, na = 28, 120
    a_cut0, a_cut1 = math.radians(-35), math.radians(25)
    grid_top, grid_bot = [], []
    for i in range(nr + 1):
        r = R * i / nr
        z = sag_r - math.sqrt(sag_r * sag_r - r * r)       # concave up
        rt, rb = [], []
        for j in range(na + 1):
            a = a_cut1 + (2 * math.pi - (a_cut1 - a_cut0)) * j / na
            rt.append(bm.verts.new((r * math.cos(a), r * math.sin(a), z)))
            rb.append(bm.verts.new((r * math.cos(a), r * math.sin(a), z - th)))
        grid_top.append(rt)
        grid_bot.append(rb)
    for i in range(nr):
        for j in range(na):
            f = bm.faces.new((grid_top[i][j], grid_top[i + 1][j], grid_top[i + 1][j + 1], grid_top[i][j + 1]))
            f.smooth = True
            f.material_index = 0
            f = bm.faces.new((grid_bot[i][j + 1], grid_bot[i + 1][j + 1], grid_bot[i + 1][j], grid_bot[i][j]))
            f.material_index = 1
    for j in range(na):                                      # outer rim
        f = bm.faces.new((grid_top[nr][j], grid_bot[nr][j], grid_bot[nr][j + 1], grid_top[nr][j + 1]))
        f.smooth = True
        f.material_index = 1
    for j in (0, na):                                        # the two cut faces
        for i in range(nr):
            q = (grid_top[i][j], grid_bot[i][j], grid_bot[i + 1][j], grid_top[i + 1][j])
            f = bm.faces.new(q if j == na else q[::-1])
            f.material_index = 2
    me = bpy.data.meshes.new("MirrorCap")
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(me)
    bm.free()
    mir = bpy.data.objects.new("MirrorCap", me)
    sc.collection.objects.link(mir)
    # R6: R5 blank read as matte plastic / cake. Polished multilayer face that mirrors the studio, fine-ground
    # (sand-blasted) glass-ceramic sides with a chamfer catching the rim light
    sub = K.mat("GlassCeramicGround", (0.66, 0.63, 0.58), rough=0.55, speck=0.35, coat=0.15)
    # R14 (root cause #6, B4_07 #1 "哑光白石膏 / 切开的蛋糕"): glass-ceramic blank - warm amber, part
    # translucent with internal depth (subsurface + some transmission), polished sides catching the studio
    sub = K.mat("GlassCeramicR14", (0.6, 0.55, 0.48), rough=0.12, transmission=0.45, ior=1.54, coat=0.4)
    # R15 (root cause #4, B4_07 "右侧过曝白区 + 噪点斑"): the transmissive rim collected the strip light as a blown,
    # noisy white patch -> fine-ground ULE-like blank: satin, faintly translucent (subsurface only, no transmission)
    sub = K.mat("GlassCeramicR15", (0.58, 0.55, 0.5), rough=0.42, coat=0.1)
    _bs = next(x for x in sub.node_tree.nodes if x.type == "BSDF_PRINCIPLED")
    for _k, _v in (("Subsurface Weight", 0.35), ("Subsurface Scale", 0.08)):
        if _k in _bs.inputs:
            _bs.inputs[_k].default_value = _v
    if "Subsurface Radius" in _bs.inputs:
        _bs.inputs["Subsurface Radius"].default_value = (1.0, 0.8, 0.6)
    # R16 (root cause #5, B4_07 "切面基底哑光灰像塑料"): Zerodur / ULE-like glass-ceramic - warm amber, polished,
    # light scatters inside (subsurface, no transmission: R14's transmissive rim blew out)
    sub = K.mat("GlassCeramicR16", (0.4, 0.35, 0.29), rough=0.16, coat=0.5)
    _bs = next(x for x in sub.node_tree.nodes if x.type == "BSDF_PRINCIPLED")
    for _k, _v in (("Subsurface Weight", 0.2), ("Subsurface Scale", 0.05)):
        if _k in _bs.inputs:
            _bs.inputs[_k].default_value = _v
    if "Subsurface Radius" in _bs.inputs:
        _bs.inputs["Subsurface Radius"].default_value = (1.0, 0.6, 0.3)
    M["coating"] = K.mat("MoSiPolishedR6", (0.8, 0.78, 0.9), metal=1.0, rough=0.025, coat=0.7)
    sc["hdri"] = "hangar_interior"
    sc["hdri_strength"] = 0.35
    me.materials.append(M["coating"])
    me.materials.append(sub)
    # cut face material: substrate with a thin layered band at the top (coating) via z gradient
    cut = _new_mat("CutFace")
    nt, nn, l = _nodes(cut)
    b = next(x for x in nn if x.type == "BSDF_PRINCIPLED")
    b.inputs["Roughness"].default_value = 0.35
    tc = nn.new("ShaderNodeTexCoord")
    sep = nn.new("ShaderNodeSeparateXYZ")
    l.new(tc.outputs["Object"], sep.inputs[0])
    # distance below the top surface ~ (z_top(r) - z); approximate with z relative to local sag at r
    wave = nn.new("ShaderNodeTexWave")
    wave.wave_type = "BANDS"
    wave.bands_direction = "Z"
    wave.inputs["Scale"].default_value = 60.0
    wave.inputs["Distortion"].default_value = 0.4
    l.new(tc.outputs["Object"], wave.inputs["Vector"])
    ramp = nn.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (0.35, 0.33, 0.45, 1)
    ramp.color_ramp.elements[1].color = (0.85, 0.84, 0.9, 1)
    l.new(wave.outputs["Fac"], ramp.inputs["Fac"])
    # band mask: only the top ~1.5 cm of the cut face shows layers
    xyz_len = nn.new("ShaderNodeVectorMath")
    xyz_len.operation = "LENGTH"
    comb = nn.new("ShaderNodeCombineXYZ")
    l.new(sep.outputs["X"], comb.inputs["X"])
    l.new(sep.outputs["Y"], comb.inputs["Y"])
    l.new(comb.outputs[0], xyz_len.inputs[0])
    sq = nn.new("ShaderNodeMath")
    sq.operation = "POWER"
    sq.inputs[1].default_value = 2.0
    l.new(xyz_len.outputs["Value"], sq.inputs[0])
    sag = nn.new("ShaderNodeMath")
    sag.operation = "DIVIDE"
    sag.inputs[1].default_value = 2 * sag_r
    l.new(sq.outputs[0], sag.inputs[0])
    dz = nn.new("ShaderNodeMath")
    dz.operation = "SUBTRACT"
    l.new(sag.outputs[0], dz.inputs[0])
    l.new(sep.outputs["Z"], dz.inputs[1])
    band = nn.new("ShaderNodeMath")
    band.operation = "LESS_THAN"
    band.inputs[1].default_value = 0.014                      # R14: a thin line, not a 3 cm stripe
    band.inputs[1].default_value = 0.009                      # R15: thinner, brighter coating band
    band.inputs[1].default_value = 0.016                      # R16: coating edge exaggerated to 2-3 px, metal-bright
    l.new(dz.outputs[0], band.inputs[0])
    mix = nn.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.inputs["A"].default_value = (*K.lin((0.5, 0.48, 0.44)), 1)   # R6: fine-ground glass-ceramic, not blue plastic
    b.inputs["Roughness"].default_value = 0.6
    # R14: neutral-grey ground section with fine horizontal grinding marks (was a flat matte plaster wall)
    mix.inputs["A"].default_value = (*K.lin((0.34, 0.34, 0.35)), 1)
    b.inputs["Roughness"].default_value = 0.38
    nz_ = nn.new("ShaderNodeTexWave")
    nz_.wave_type = "BANDS"
    nz_.bands_direction = "Z"
    nz_.inputs["Scale"].default_value = 140.0
    nz_.inputs["Distortion"].default_value = 3.0
    nz_.inputs["Detail"].default_value = 4.0
    l.new(tc.outputs["Object"], nz_.inputs["Vector"])
    bp_ = nn.new("ShaderNodeBump")
    bp_.inputs["Strength"].default_value = 0.3
    l.new(nz_.outputs["Fac"], bp_.inputs["Height"])
    l.new(bp_.outputs["Normal"], b.inputs["Normal"])
    # R16 (root cause #5): the section is POLISHED glass-ceramic (warm amber, glossy, inner scatter), not ground grey
    mix.inputs["A"].default_value = (*K.lin((0.38, 0.33, 0.27)), 1)
    b.inputs["Roughness"].default_value = 0.14
    bp_.inputs["Strength"].default_value = 0.05
    for _k, _v in (("Subsurface Weight", 0.2), ("Subsurface Scale", 0.05), ("Coat Weight", 0.5)):
        if _k in b.inputs:
            b.inputs[_k].default_value = _v
    if "Subsurface Radius" in b.inputs:
        b.inputs["Subsurface Radius"].default_value = (1.0, 0.6, 0.3)
    l.new(band.outputs[0], mix.inputs["Factor"])
    l.new(ramp.outputs["Color"], mix.inputs["B"])
    l.new(mix.outputs["Result"], b.inputs["Base Color"])
    mt = nn.new("ShaderNodeMath")
    mt.operation = "MULTIPLY"
    mt.inputs[1].default_value = 0.8
    l.new(band.outputs[0], mt.inputs[0])
    l.new(mt.outputs[0], b.inputs["Metallic"])
    ramp.color_ramp.elements[0].color = (0.55, 0.53, 0.65, 1)       # R14: bright top-coat line on the section
    ramp.color_ramp.elements[1].color = (1.0, 0.98, 1.0, 1)
    b.inputs["Emission Color"].default_value = (0.85, 0.85, 1.0, 1)
    em_ = nn.new("ShaderNodeMath")
    em_.operation = "MULTIPLY"
    em_.inputs[1].default_value = 0.9
    em_.inputs[1].default_value = 2.6                         # R15 (B4_07 "切面上沿要一条极细亮的镀膜带")
    l.new(band.outputs[0], em_.inputs[0])
    l.new(em_.outputs[0], b.inputs["Emission Strength"])
    me.materials.append(cut)
    # mount: ring, hexapod and base, bolts
    mbm, mbb = K.MB(), K.MB()
    mbm.ring((0, 0, -th - 0.03), R * 1.12, R * 0.92, 0.12, seg=96)
    mbb.bolts((0, 0, -th + 0.04), R * 1.06, 24, 0.022, 0.05)
    for i in range(6):
        a = math.radians(60 * i + 15)
        a2 = math.radians(60 * i + (45 if i % 2 else -15))
        mbm.tube((R * 0.95 * math.cos(a), R * 0.95 * math.sin(a), -th - 0.08),
                 (R * 0.7 * math.cos(a2), R * 0.7 * math.sin(a2), -1.05), 0.04)
    mbm.cyl((0, 0, -1.1), R * 0.95, 0.1, seg=6)
    K.greeble(mbm, (-1.0, -1.0, -1.15), (1, 0, 0), (0, 1, 0), (0, 0, -1), 2.0, 2.0, 30, 0.1, 0.3, 0.03, 0.12, seed=3)
    mbm.obj("Mount", M["alu"], bevel=0.008)
    mbb.obj("Bolts", M["steel"])
    # violet EUV beam in and out at the mirror centre (reflects at the surface)
    hit = Vector((0.15, 0.25, 0.006))
    din = Vector((-0.75, -0.2, 1.0)).normalized()          # R6: more oblique so in / out form a visible V
    nrm = Vector((0, 0, 1))
    dout = (din - 2 * din.dot(nrm) * nrm) * -1
    # R14 (root cause #1, B4_07 #2 "实心白色胶囊端头"): open soft-edged cones - the incoming light narrows onto
    # the landing spot, the reflected light opens out of the SAME spot; no caps, no column, no end bead
    rout = Vector((-din.x, -din.y, din.z))
    # R16 (root cause #3, B4_07 "等粗实心光管"): the incoming cone converges INTO the landing spot and the reflected
    # cone opens out of it; both far ends fade out (no cut-off ends), soft core instead of a solid tube
    import misc_kit_r16 as MK
    MK.fade_cone("Beam", hit + din * 6.0, hit, 0.2, 0.05,
                 MK.fade_beam_mat("EUVInR16", strength=2.6, alpha=0.7, fade0=0.5, fade1=0.03), seg=56)
    MK.fade_cone("BeamOut", hit, hit + rout * 6.0, 0.05, 0.24,
                 MK.fade_beam_mat("EUVOutR16", strength=1.9, alpha=0.55, fade0=0.03, fade1=0.55), seg=56)
    # R17 (root cause #4, B4_07 "缺口处一团紫光透进镜体"): change ROUTE - no cones at all: the light is one thin
    # core in and one thin core out, meeting in a single elliptical highlight ON the coating; the violet point
    # lights that lit the notch / substrate are removed (below), so nothing violet sits inside the blank
    import misc_beam_r17 as BR17
    for nm in ("Beam", "BeamOut"):
        bpy.data.objects.remove(bpy.data.objects[nm], do_unlink=True)
    BR17.thin_core("BeamR17", hit + din * 6.0, hit, 0.011, K.VIOLET, 9.0, 0.95, fade0=0.45, glossy=False)
    BR17.thin_core("BeamOutR17", hit, hit + rout * 6.0, 0.011, K.VIOLET, 7.0, 0.95, fade1=0.45, glossy=False)
    # R6: mount detail: coolant ring with branch lines, three edge sensors, cable loom off the base
    det, cu, cab = K.MB(), K.MB(), K.MB()
    cu.ring((0, 0, -th - 0.13), R * 1.16, R * 1.12, 0.03, seg=96)
    for i in range(8):
        a = math.radians(45 * i + 10)
        p0 = Vector((R * 1.14 * math.cos(a), R * 1.14 * math.sin(a), -th - 0.13))
        cu.path([p0, p0 + Vector((0.12 * math.cos(a), 0.12 * math.sin(a), -0.05)),
                 p0 + Vector((0.16 * math.cos(a), 0.16 * math.sin(a), -0.5))], 0.014, seg=8)
    for i in range(3):
        a = math.radians(120 * i + 70)
        c0 = Vector((R * 1.2 * math.cos(a), R * 1.2 * math.sin(a), -th + 0.05))
        det.box(c0, (0.12, 0.08, 0.1), rot=(0, 0, a))
        det.cyl(c0 + Vector((-0.08 * math.cos(a), -0.08 * math.sin(a), 0)), 0.025, 0.06,
                rot=(0, math.radians(90), a), seg=16)
        cab.path([c0 + Vector((0, 0, -0.05)), c0 + Vector((0.1 * math.cos(a), 0.1 * math.sin(a), -0.4)),
                  c0 + Vector((0.2 * math.cos(a), 0.2 * math.sin(a), -0.75))], 0.012, seg=8)
    det.obj("EdgeSensors", M["anod"], bevel=0.004)
    cu.obj("CoolantRing", M["copper"])
    cab.obj("SensorCables", M["cable_b"])
    # R17: one soft elliptical highlight lying on the coating (stretched along the beam's footprint) replaces the
    # R14 stacked-disc footprint + its 15 W violet light
    spo = BR17.landing("BeamSpotR17", hit, Vector((0, 0, 1)), 0.085, color=(0.82, 0.72, 1.0), strength=12.0,
                       squash=0.55, major=Vector((din.x, din.y, 0)), lift=0.005)
    spo.visible_glossy = False                               # its mirror image read as a second white blob
    _b407_r19(sc, me, cut, sub, hit, din, rout)
    K.floor("Floor", K.mat("FloorDark", (0.04, 0.045, 0.055), rough=0.35), z=-1.2)
    K.area("Key", (-3, -4, 5), (0, 0, 0), 4, 900, (0.95, 0.96, 1.0))
    K.area("Rim", (3, 4, 3), (0, 0, 0), 5, 700, (0.75, 0.8, 1.0))
    K.area("Strip", (-4, 2, 2.5), (0, 0, 0), 0.6, 300, (1, 1, 1), size_y=6)
    for nm in ("Strip", "Key"):                  # R15 (B4_07 "镜面反射里有一块矩形文字块 / 过曝"): no softbox
        bpy.data.objects[nm].visible_glossy = False   # images in the coating or the rim
        bpy.data.objects[nm].visible_camera = False
    bpy.data.objects["Strip"].data.energy = 160
    # R17: no 60 W violet "Glow" over the hit - it lit the notch faces violet ("light passing into the mirror")
    for nm in ("Glow", "BeamHitLight"):          # R14: the two point-light spheres (and their mirror images) were
        o_ = bpy.data.objects.get(nm)            # the white "capsule end" over the landing spot
        if o_ is not None:
            o_.visible_camera = False
            o_.visible_glossy = False
    # cut edge midpoint (wedge between a_cut0 / a_cut1) for the push-in
    am = (a_cut0 + a_cut1) / 2
    edge = Vector((R * 0.8 * math.cos(a_cut0), R * 0.8 * math.sin(a_cut0), -0.04))
    gapdir = Vector((math.cos(am), math.sin(am), 0))
    cam, tgt = K.camera("CamR2", lens=40)
    _dof(cam, 4.0, tgt)
    K.key_path(cam, tgt, [(1, tuple(gapdir * 3.6 + Vector((0, 0, 2.4))), (0, 0, -0.1)),
                          (round(n * 0.55), tuple(gapdir * 2.2 + Vector((0, 0, 0.8))), (edge * 0.6)),
                          (n, tuple(edge + gapdir * 0.55 + Vector((0, 0, 0.12)) + Vector((-math.sin(a_cut0), math.cos(a_cut0), 0)) * 0.35), edge)])
    # R15 (B4_07 "镜面反射里有一块模糊的矩形文字块"): that block is the studio HDRI's softbox panel mirrored in
    # the coating -> the coating reflects a dim hangar interior instead (no hard rectangles)
    sc["hdri"] = "hangar_interior"
    sc["hdri_strength"] = 0.45
    # R7 (F): magnifier leader lands on the thin coating at the TOP of the cut face, not mid-substrate
    sc.camera = cam
    coat = {}
    for k, f in enumerate((0.55, 0.7, 0.8, 0.9)):
        rr = R * f
        zt = sag_r - math.sqrt(sag_r * sag_r - rr * rr)
        coat[f"coat{k}"] = Vector((rr * math.cos(a_cut0), rr * math.sin(a_cut0), zt - 0.004))
    K.anchors("B4_07", coat)
    return cam


def _pellicle(sc, n):
    K.world_studio(0.42)
    # R14 (B6_12 #3 "竖直白色亮条 / 漏光"): the sweep strip mirrored in the glossy coated floor behind the frame
    # as a vertical white bar -> satin floor without clear coat (the sweep still glints on the membrane)
    flo = K.mat("StudioFloor", (0.3, 0.31, 0.33), rough=0.6, coat=0.0)
    K.floor("Floor", flo, z=0.0)
    M = K.palette(studio=True)
    # mask: 1.52 x 1.52 x 0.064 (x10 scale), dark multilayer top with absorber pattern
    mb = K.MB()
    mb.box((0, 0, 0.12), (1.52, 1.52, 0.064))
    mask = mb.obj("Mask", K.mat("MaskSideR16", (0.06, 0.065, 0.075), metal=0.6, rough=0.12, coat=0.6), bevel=0.012)   # R16: polished chamfered blank
    top = _new_mat("MaskTop")
    nt, nn, l = _nodes(top)
    b = next(x for x in nn if x.type == "BSDF_PRINCIPLED")
    b.inputs["Metallic"].default_value = 0.15             # R5: less mirror, so the pattern is not washed out
    tc = nn.new("ShaderNodeTexCoord")
    mpm = nn.new("ShaderNodeMapping")                # absorber pattern: die layouts tiled 3 x 2 (mask is 4x/8x the chip)
    mpm.inputs["Scale"].default_value = (2.2, 1.7, 1)
    mpm.inputs["Location"].default_value = (0.5, 0.5, 0)
    l.new(tc.outputs["Object"], mpm.inputs["Vector"])
    br = nn.new("ShaderNodeTexImage")
    br.image = bpy.data.images.load(os.path.join(DIES, "zen5_ccd_full.jpg"), check_existing=True)
    l.new(mpm.outputs["Vector"], br.inputs["Vector"])
    bw = nn.new("ShaderNodeRGBToBW")
    l.new(br.outputs["Color"], bw.inputs["Color"])
    cr = nn.new("ShaderNodeValToRGB")
    cr.color_ramp.elements[0].color = (*K.lin((0.02, 0.02, 0.03)), 1)
    cr.color_ramp.elements[1].color = (*K.lin((0.66, 0.64, 0.76)), 1)   # R5: pattern reads through the film
    l.new(bw.outputs["Val"], cr.inputs["Fac"])
    l.new(cr.outputs["Color"], b.inputs["Base Color"])
    rr = nn.new("ShaderNodeMapRange")
    rr.inputs["To Min"].default_value = 0.55
    rr.inputs["To Max"].default_value = 0.3
    l.new(bw.outputs["Val"], rr.inputs["Value"])
    l.new(rr.outputs["Result"], b.inputs["Roughness"])
    # R16 (root cause #5, B6_12 "基底像灰塑料、图形像平面贴图"): dark reflective Mo/Si multilayer blank (near-mirror,
    # reflects the studio) with the absorber pattern as matte, slightly RAISED lines (bump from the layout)
    thr = nn.new("ShaderNodeMapRange")
    thr.interpolation_type = "SMOOTHSTEP"
    thr.inputs["From Min"].default_value = 0.38
    thr.inputs["From Max"].default_value = 0.52
    l.new(bw.outputs["Val"], thr.inputs["Value"])
    cr.color_ramp.elements[0].color = (*K.lin((0.05, 0.055, 0.075)), 1)     # multilayer: dark, glossy
    cr.color_ramp.elements[1].color = (*K.lin((0.36, 0.36, 0.42)), 1)       # absorber (TaN): matte grey
    l.new(thr.outputs["Result"], cr.inputs["Fac"])
    rr.inputs["To Min"].default_value = 0.06
    rr.inputs["To Max"].default_value = 0.5
    l.new(thr.outputs["Result"], rr.inputs["Value"])
    mtl = nn.new("ShaderNodeMapRange")
    mtl.inputs["To Min"].default_value = 0.9
    mtl.inputs["To Max"].default_value = 0.15
    l.new(thr.outputs["Result"], mtl.inputs["Value"])
    l.new(mtl.outputs["Result"], b.inputs["Metallic"])
    bmp = nn.new("ShaderNodeBump")
    bmp.inputs["Strength"].default_value = 0.6
    bmp.inputs["Distance"].default_value = 0.002
    l.new(thr.outputs["Result"], bmp.inputs["Height"])
    l.new(bmp.outputs["Normal"], b.inputs["Normal"])
    # R19 (root cause #4, B6_12 R18 "掩模图形是白色线描的芯片版图，更像 PCB"): reflective mask = LIGHT Mo/Si multilayer
    # field (bright polished, reflects the studio) + DARK matte TaN absorber pattern (the layout features), not white lines
    cr.color_ramp.elements[0].color = (*K.lin((0.50, 0.52, 0.60)), 1)       # multilayer reflector: light, glossy
    cr.color_ramp.elements[1].color = (*K.lin((0.035, 0.035, 0.045)), 1)    # absorber: dark, matte
    rr.inputs["To Min"].default_value = 0.1
    rr.inputs["To Max"].default_value = 0.55
    mtl.inputs["To Min"].default_value = 0.8
    mtl.inputs["To Max"].default_value = 0.0
    mpm.inputs["Scale"].default_value = (1.1, 0.85, 1)                     # bigger features: blocks + lines, not hairlines
    thr.inputs["From Min"].default_value = 0.24
    thr.inputs["From Max"].default_value = 0.32
    mt = K.MB()
    mt.box((0, 0, 0.1525), (1.44, 1.44, 0.002))
    mt.obj("MaskTop", top)
    # pellicle frame on four studs: gap above the mask
    gap = 0.055                                  # frame height = membrane stand-off (x10 scale, illustrative)
    fz = 0.152 + gap / 2
    fr = K.MB()
    fw, fh, bar, ht = 1.32, 1.06, 0.014, gap
    # R15 (root cause #4, B6_12 "间距尺寸线量的是角块，不是膜面↔图形面"): the near bar is cut open over
    # x in [nx0, nx1] (side micro-section) so the gap between membrane and pattern face is seen directly
    nx0, nx1 = 0.18, 0.40
    for (cx, cy, sx, sy) in [(0, fh / 2, fw, bar), (fw / 2, 0, bar, fh), (-fw / 2, 0, bar, fh),
                             ((-fw / 2 + nx0) / 2, -fh / 2, nx0 + fw / 2, bar), ((fw / 2 + nx1) / 2, -fh / 2, fw / 2 - nx1, bar)]:
        fr.box((cx, cy, fz), (sx, sy, ht))
    for sx in (-1, 1):                         # vent holes / pins on the frame sides
        for k in range(7):
            fr.cyl((sx * (fw / 2 + 0.018), -fh / 2 + (k + 0.5) * fh / 7, fz), 0.008, 0.006, rot=(0, math.radians(90), 0), seg=10)
    # R14 (B6_12 #1 "框太简单：一根黑方管"): vent holes (dark recessed slots) along all four sides, corner
    # clamp blocks with screws that hold the frame to the mask, and a pale adhesive line where the film is bonded
    vh, cl, sc_, gl_ = K.MB(), K.MB(), K.MB(), K.MB()
    for (cx, cy, ax, L_) in [(0, -fh / 2, "x", fw), (0, fh / 2, "x", fw), (-fw / 2, 0, "y", fh), (fw / 2, 0, "y", fh)]:
        for k in range(9):
            t = -L_ / 2 + (k + 0.5) * L_ / 9
            if ax == "x" and nx0 - 0.02 < t < nx1 + 0.02 and cy < 0:
                continue
            if ax == "x":
                vh.box((t, cy + math.copysign(bar / 2 + 0.0006, cy), fz), (0.03, 0.0015, ht * 0.32))
            else:
                vh.box((cx + math.copysign(bar / 2 + 0.0006, cx), t, fz), (0.0015, 0.03, ht * 0.32))
    for sx in (-1, 1):
        for sy in (-1, 1):
            c0 = Vector((sx * (fw / 2 + 0.03), sy * (fh / 2 + 0.03), 0.152 + 0.022))
            cl.box(c0, (0.09, 0.09, 0.044))
            cl.box(c0 + Vector((-sx * 0.045, -sy * 0.045, 0.018)), (0.05, 0.05, 0.012))   # jaw over the frame corner
            sc_.cyl(c0 + Vector((0, 0, 0.023)), 0.012, 0.004, seg=16)
    for (cx, cy, sx, sy) in [(0, fh / 2 - bar / 2, fw - bar, 0.0025), (0, -fh / 2 + bar / 2, fw - bar, 0.0025),
                             (fw / 2 - bar / 2, 0, 0.0025, fh - bar), (-fw / 2 + bar / 2, 0, 0.0025, fh - bar)]:
        gl_.box((cx, cy, fz + ht / 2 + 0.0006), (sx, sy, 0.0012))
    vh.obj("PelVents", K.mat("VentDark", (0.0, 0.0, 0.0), rough=0.9, spec=0.0))
    cl.obj("PelClamps", K.mat("ClampAlu", (0.62, 0.63, 0.66), metal=1.0, rough=0.28, brushed=0.15), bevel=0.003)
    sc_.obj("PelClampScrews", K.mat("ScrewSteel", (0.5, 0.5, 0.52), metal=1.0, rough=0.2))
    gl_.obj("PelGlueLine", K.mat("GlueLine", (0.78, 0.76, 0.7), rough=0.35))
    # R3 5A: thin black anodized frame (the R2 silver frame + gap read as a thick glass tray)
    fr.obj("PelFrame", K.mat("FrameBlack", (0.03, 0.03, 0.035), metal=0.6, rough=0.32, speck=0.1), bevel=0.003)
    # R19 (B6_12 R18 "框边金属做出阳极氧化质感，不要纯黑塑料"): dark anodized aluminium - blue-grey metal, satin sheen
    bpy.data.objects["PelFrame"].data.materials[0] = K.mat("FrameAnodR19", (0.16, 0.18, 0.23), metal=0.85, rough=0.36,
                                                         brushed=0.25, speck=0.06)
    # R19: the pale glue line drew a bright hard rim round the film (glass-lid edge) -> dark bond line
    bpy.data.objects["PelGlueLine"].data.materials[0] = K.mat("GlueLineR19", (0.10, 0.10, 0.11), rough=0.5)
    # membrane: near-transparent, faint grey haze, glossy sheen at grazing angles, slight sag
    mem = _new_mat("Membrane")
    nt, nn, l = _nodes(mem)
    for x in list(nn):
        if x.type != "OUTPUT_MATERIAL":
            nn.remove(x)
    out = next(x for x in nn if x.type == "OUTPUT_MATERIAL")
    tr = nn.new("ShaderNodeBsdfTransparent")
    tr.inputs["Color"].default_value = (0.93, 0.93, 0.94, 1)
    # R17 (B6_12 R16 "膜像一块茶色玻璃板，透过去的图形被整体压暗"): ~97 % neutral transmission - the film is
    # carried by its grazing sweep highlight (R16 material kept), not by darkening the pattern under it
    tr.inputs["Color"].default_value = (0.975, 0.975, 0.975, 1)
    gl = nn.new("ShaderNodeBsdfGlossy")
    gl.inputs["Roughness"].default_value = 0.06
    gl.inputs["Roughness"].default_value = 0.22         # R14: broad soft tension band, not a thin white streak
    gl.inputs["Color"].default_value = (0.95, 0.95, 0.96, 1)
    df = nn.new("ShaderNodeBsdfDiffuse")
    df.inputs["Color"].default_value = (0.6, 0.6, 0.62, 1)
    fres = nn.new("ShaderNodeLayerWeight")
    fres.inputs["Blend"].default_value = 0.25
    m1 = nn.new("ShaderNodeMixShader")
    m1.inputs["Fac"].default_value = 0.012              # R4: thinner haze, 5A: shown only by grazing sheen
    m1.inputs["Fac"].default_value = 0.004              # R15 (B6_12 "膜像框上盖了一层灰雾"): ~90 % clear
    l.new(tr.outputs[0], m1.inputs[1])
    l.new(df.outputs[0], m1.inputs[2])
    m2 = nn.new("ShaderNodeMixShader")
    fk = nn.new("ShaderNodeMath")
    fk.operation = "MULTIPLY"
    fk.inputs[1].default_value = 0.07                  # R5: less sheen, so it is not a dark lid
    fk.inputs[1].default_value = 0.11                  # R14: a little more sheen so the tension bands read
    fk.inputs[1].default_value = 0.05                  # R15: no grey lid; the sweep strip draws ONE thin band
    fk.operation = "MULTIPLY_ADD"                       # R16 (root cause #5): ~3 % base reflectance -> a grazing
    fk.inputs[2].default_value = 0.03                   # sweep band crosses the whole film (it reads as a sheet)
    gl.inputs["Roughness"].default_value = 0.035
    l.new(fres.outputs["Fresnel"], fk.inputs[0])
    l.new(fk.outputs[0], m2.inputs["Fac"])
    l.new(m1.outputs[0], m2.inputs[1])
    l.new(gl.outputs[0], m2.inputs[2])
    l.new(m2.outputs[0], out.inputs["Surface"])
    bm = bmesh.new()
    nx, ny = 120, 96
    vs = [[bm.verts.new(((i / nx - 0.5) * (fw - bar), (j / ny - 0.5) * (fh - bar),
                         fz + ht / 2 - 0.004 * math.sin(math.pi * i / nx) * math.sin(math.pi * j / ny)
                         # R14 (B6_12 #1 "膜面是一片乳白平面"): faint tension ripples so the sweep light
                         # draws long grazing highlight bands across the stretched film
                         + 0.0 * math.sin(math.pi * i / nx) * math.sin(math.pi * j / ny)
                         * math.sin(2 * math.pi * (3.0 * i / nx + 0.6 * j / ny))))
           for j in range(ny + 1)] for i in range(nx + 1)]
    for i in range(nx):
        for j in range(ny):
            f = bm.faces.new((vs[i][j], vs[i + 1][j], vs[i + 1][j + 1], vs[i][j + 1]))
            f.smooth = True
    me = bpy.data.meshes.new("Membrane")
    bm.to_mesh(me)
    bm.free()
    mo = bpy.data.objects.new("Membrane", me)
    sc.collection.objects.link(mo)
    me.materials.append(mem)
    _pellicle_r19(sc, mem, tr, gl, fk, fw, fh, bar, fz, ht, nx0, nx1)
    # dust particles on the membrane (what the pellicle is for) - a few tiny specks
    # R15 (root cause #4, R14 H6 "膜面颗粒无说明"): no particles in this shot (they belong to a particle beat)
    # gap dimension in the notch: cyan rule from the pattern face up to the membrane plane, end ticks on both
    gx, gy = (nx0 + nx1) / 2, -fh / 2 + 0.02
    z_bot, z_top = 0.1535, fz + ht / 2 - 0.001
    dmb = K.MB()
    dmb.tube(Vector((gx, gy, z_bot)), Vector((gx, gy, z_top)), 0.0022, seg=10)
    for zz in (z_bot, z_top):
        dmb.tube(Vector((gx - 0.03, gy, zz)), Vector((gx + 0.03, gy, zz)), 0.0018, seg=8)
    dim_o = dmb.obj("GapRule", K.emit_mat("GapRuleInk", K.CYAN, 6.0))
    f_dim = round(n * 0.58)
    dim_o.hide_render = True
    dim_o.keyframe_insert("hide_render", frame=1)
    dim_o.keyframe_insert("hide_render", frame=f_dim - 1)
    dim_o.hide_render = False
    dim_o.keyframe_insert("hide_render", frame=f_dim)
    K.anchors("B6_12", {"gap_top": Vector((gx, gy, z_top)), "gap_bot": Vector((gx, gy, z_bot)),
                        "gap_mid": Vector((gx + 0.03, gy, (z_top + z_bot) / 2)),
                        "film": Vector((-0.15, 0.1, z_top)), "mask": Vector((0.45, -0.62, 0.153)),
                        "pattern": Vector((0.22, -0.3, 0.1535))})       # R17: mask leader lands on the pattern
    # studio lights; one strip sweeps to drag a grazing highlight across the membrane
    K.area("Key", (-3, -3.5, 4.5), (0, 0, 0.3), 3, 900, (1, 0.99, 0.97))
    K.area("Fill", (3.5, -2, 2), (0, 0, 0.3), 3, 350, (0.9, 0.95, 1.0))
    K.area("Rim", (0, 4, 2.5), (0, 0, 0.3), 4, 700, (0.92, 0.95, 1.0))
    sw = K.area("Sweep", (-3, 2.5, 1.6), (0, 0, 0.4), 0.25, 450, (1, 1, 1), size_y=4)
    sw.visible_camera = False                    # R3: the strip and its glints made the speckle block on the frame edge
    sc.cycles.sample_clamp_direct = 6.0
    for nm in ("Key", "Fill", "Rim"):            # R14: no light panel / its floor glint may show up as a white bar
        o_ = bpy.data.objects.get(nm)
        if o_ is not None:
            o_.visible_camera = False
    bpy.data.objects["Rim"].visible_glossy = False
    # R14 (B6_12 #3): the sweep strip lit the far floor as a white hot spot / vertical bar -> light-link it to the
    # membrane only, and widen it so it draws a broad tension band across the film instead of a thin white line
    sw.data.size = 0.9
    sw.data.energy = 260
    sw.data.size, sw.data.energy = 0.18, 160      # R15: one thin grazing highlight band, not a broad haze
    sw.data.size, sw.data.energy = 0.3, 520       # R16: the sweep band is clearly visible across the film
    # R19 (root cause #4): the film has no uniform sheen any more -> ONE narrow grazing strip highlight carries it
    sw.data.size, sw.data.energy = 0.12, 7000
    try:
        rc = bpy.data.collections.new("SweepReceivers")
        rc.objects.link(mo)
        sw.light_linking.receiver_collection = rc
    except Exception:
        pass
    sw.location = (-3.0, 2.5, 1.6)
    sw.keyframe_insert("location", frame=1)
    sw.location = (3.0, 2.5, 1.6)
    sw.keyframe_insert("location", frame=n)
    cam, tgt = K.camera("CamR2", lens=45)
    _dof(cam, 2.8, tgt)                          # R19: stage / clamp anchor behind stays soft (defocused)
    K.key_path(cam, tgt, [(1, (-1.4, -3.0, 2.6), (0.05, 0, 0.2)),
                          (round(n * 0.55), (-1.5, -2.5, 1.0), (0.2, -0.3, 0.2)),
                          (n, (-0.75, -1.9, 0.62), (0.25, -0.3, 0.17))])
    if _r20("B6_12"):                            # R20 row #4: scanner pose (pattern face down), chuck parts
        import misc_b612_r20 as P20
        P20.apply(sc, n, cam, tgt, {"gap_top": (gx, gy, z_top), "gap_bot": (gx, gy, z_bot),
                                    "gap_mid": (gx + 0.03, gy, (z_top + z_bot) / 2), "film": (-0.15, 0.1, z_top),
                                    "mask": (0.45, -0.62, 0.153), "pattern": (0.22, -0.3, 0.1535)})
        if _r21("B6_12"):                        # R21 row #5: cut-section magnifier + black anodised frame
            import misc_b612_r21 as P21
            P21.apply(sc, n, cam, tgt, {"gap_top": (gx, gy, z_top), "gap_bot": (gx, gy, z_bot),
                                        "gap_mid": (gx + 0.03, gy, (z_top + z_bot) / 2), "film": (-0.15, 0.1, z_top),
                                        "mask": (0.45, -0.62, 0.153), "pattern": (0.22, -0.3, 0.1535)})
    sc["hdri"] = "studio_small_09"
    sc["hdri_strength"] = 0.6
    return cam


def _b817_r19(sc, n, Mk, pw16, hot, al, so):
    """R19 B8_17. Root cause #3 (R18 "背景墙是同一种「圆窗 + 横杆」重复铺排… 把其中一半换成不同零件，例如离子泵、阀岛、气路面板、
    冷却管束"): the R16 parts wall is replaced by the shared read-only kit_r19.wall_r19 (6 big different assemblies + a
    diagonal coolant run) on the same back plate. Root cause #2 (light path, R18 "光锥打在晶圆上的那一格最好再亮一点，并加一点
    溅射。已曝光格和未曝光格的颜色差可以再拉开"): the cone already ends exactly in the slit (hooked); the landing field is one
    step brighter with a soft splash spot riding with the slit; exposed fields pale violet vs unexposed neutral grey."""
    import hero_kit_r10 as H
    import kit_r19 as KR
    for ob in [pw16] + list(pw16.children_recursive):
        ob.hide_render = True
        ob.hide_viewport = True
    P = H.new_parts()
    KR.wall_r19(P, -5.2, 8.2, -0.45, 4.4, 6.25, seed=817, scale=2.6, n=6)
    root = bpy.data.objects.new("WallR19", None)
    sc.collection.objects.link(root)
    for ob in H.finish(P, Mk, "WallR19"):
        ob.parent = root
    hot.inputs["To Min"].default_value = 3.4             # landing field: one step brighter (R18 2.2)
    hot.inputs["To Max"].default_value = 0.3             # exposed: pale violet latent image (R18 0.16)
    al.inputs[1].default_value = 0.42
    import misc_beam_r17 as BR17
    sp = BR17.landing("SlitSplashR19", Vector((0, 0, 0.0005)), Vector((0, 0, 1)), 0.2, color=(0.82, 0.74, 1.0),
                      strength=2.2, squash=0.45, major=Vector((1, 0, 0)), lift=0.0005)
    sp.parent = so
    sp.visible_glossy = False


def _b407_r19(sc, me, cut, sub, hit, din, rout):
    """R19 B4_07 (root cause #2, light path + material). R18 review: 「入射光和反射光是两根等宽细管。改法：入射光锥形收拢到
    落点，落点加一圈软亮斑；反射光略微发散」 + 「把切面改成中性灰喷砂，饱和度 < 5 %，顶层膜保留亮白边」.
    The R17 thin cores are replaced by misc_beam_r18 volumetric cones whose ends sit exactly on the landing spot (zero
    density outside the cone); a soft halo ring around the spot; blank + cut face neutral-grey sand-blasted."""
    import misc_beam_r18 as BR18
    import misc_beam_r17 as BR17
    for ob in list(bpy.data.objects):
        if ob.name.startswith(("BeamR17", "BeamOutR17")):
            bpy.data.objects.remove(ob, do_unlink=True)
    BR18.vol_cone("BeamInR19", hit + din * 6.0, hit, 0.26, 0.035, K.VIOLET, 2.4, 0.6, edge=1.5, fade0=0.4, gain=1.2)
    BR18.vol_cone("BeamOutR19", hit, hit + rout * 6.0, 0.035, 0.14, K.VIOLET, 1.8, 0.5, edge=1.5, fade1=0.45, gain=0.0)
    halo = BR17.landing("BeamHaloR19", hit, Vector((0, 0, 1)), 0.2, color=(0.8, 0.7, 1.0), strength=2.6, lift=0.004)
    halo.visible_glossy = False
    # neutral grey sand-blasted section + blank (saturation < 5 %); the top coating band (emissive, bright) is kept
    b = next(x for x in cut.node_tree.nodes if x.type == "BSDF_PRINCIPLED")
    mix = next(x for x in cut.node_tree.nodes if x.type == "MIX" and x.data_type == "RGBA")
    mix.inputs["A"].default_value = (*K.lin((0.29, 0.29, 0.30)), 1)
    b.inputs["Roughness"].default_value = 0.5
    for _k in ("Subsurface Weight", "Coat Weight"):
        if _k in b.inputs:
            b.inputs[_k].default_value = 0.0
    for x in cut.node_tree.nodes:
        if x.type == "BUMP":
            x.inputs["Strength"].default_value = 0.25
    nn, l = cut.node_tree.nodes, cut.node_tree.links
    tc = nn.new("ShaderNodeTexCoord")
    nz = nn.new("ShaderNodeTexNoise")                            # sand-blast grain
    nz.inputs["Scale"].default_value = 900.0
    l.new(tc.outputs["Object"], nz.inputs["Vector"])
    bp = nn.new("ShaderNodeBump")
    bp.inputs["Strength"].default_value = 0.12
    l.new(nz.outputs["Fac"], bp.inputs["Height"])
    l.new(bp.outputs["Normal"], b.inputs["Normal"])
    me.materials[1] = K.mat("BlankGreyR19", (0.27, 0.27, 0.28), rough=0.5, speck=0.25)


def _pellicle_r19(sc, mem, tr, gl, fk, fw, fh, bar, fz, ht, nx0, nx1):
    """R19 root cause #4 (B6_12 R18 "pellicle 读起来是一块厚玻璃盖板…" two rounds): the film is a zero-thickness single
    sheet (transparent BSDF, no refraction), ~99 % clear, NO uniform base reflectance (only a weak Fresnel term), a crisp
    glossy lobe so the light-linked sweep strip draws ONE grazing strip highlight, and faint tension ripples (normal noise).
    Hair-thin bright section line where the frame is cut open; defocused mask stage (e-chuck under the mask, clamp jaws,
    stage carriage + rail behind) as the macro anchor."""
    nt = mem.node_tree
    nn, l = nt.nodes, nt.links
    tr.inputs["Color"].default_value = (0.99, 0.99, 0.99, 1)
    fk.inputs[1].default_value = 0.10                # Fresnel only: grazing glint, no lid-wide sheen
    fk.inputs[2].default_value = 0.0                 # R16 +3 % base reflectance removed (= the "glass plate")
    gl.inputs["Roughness"].default_value = 0.02
    tc = nn.new("ShaderNodeTexCoord")
    nz = nn.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 1.6
    nz.inputs["Detail"].default_value = 1.0
    l.new(tc.outputs["Object"], nz.inputs["Vector"])
    bp = nn.new("ShaderNodeBump")
    bp.inputs["Strength"].default_value = 0.035      # very light tension undulation: the strip wavers a little
    bp.inputs["Distance"].default_value = 0.01
    l.new(nz.outputs["Fac"], bp.inputs["Height"])
    l.new(bp.outputs["Normal"], gl.inputs["Normal"])
    # hair-thin section line: the film edge where the near frame bar is cut open (vs the thick frame)
    z_f = fz + ht / 2
    hl = K.MB()
    hl.tube(Vector((nx0 - 0.01, -(fh - bar) / 2, z_f)), Vector((nx1 + 0.01, -(fh - bar) / 2, z_f)), 0.0009, seg=6)
    hl.obj("FilmSectionLine", K.mat("FilmSectionInk", (0.85, 0.86, 0.9), rough=0.2, emit=(0.9, 0.92, 1.0), strength=5.0))
    # mask stage anchor: electrostatic chuck slab under the mask (light ceramic, dark electrode groove at its rim)
    ch, chg, jw, st = K.MB(), K.MB(), K.MB(), K.MB()
    ch.box((0, 0, 0.044), (1.66, 1.66, 0.088))
    for (cx, cy, sx, sy) in [(0, 0.80, 1.6, 0.01), (0, -0.80, 1.6, 0.01), (0.80, 0, 0.01, 1.6), (-0.80, 0, 0.01, 1.6)]:
        chg.box((cx, cy, 0.0885), (sx, sy, 0.003))
    # clamp jaws gripping the mask at the far corners, arms back to the stage carriage
    for sx in (-1, 1):
        x = sx * 0.62
        jw.box((x, 0.80, 0.168), (0.16, 0.10, 0.03))                  # jaw pad over the mask edge
        jw.box((x, 0.97, 0.12), (0.16, 0.26, 0.10))                   # jaw block
        jw.box((x, 2.0, 0.14), (0.12, 1.9, 0.07))                     # arm to the carriage
        jw.cyl((x, 0.97, 0.172), 0.025, 0.012, seg=16)
    st.box((0, 3.1, 0.18), (3.6, 0.4, 0.36))                         # stage carriage (defocused background)
    st.box((0, 3.55, 0.07), (6.0, 0.24, 0.14))                        # linear-motor rail
    for k in range(28):
        st.box((-2.9 + k * 0.21, 3.55, 0.145), (0.12, 0.2, 0.012))    # magnet track segments
    for k in range(5):
        st.cyl((-1.4 + k * 0.7, 2.89, 0.24), 0.04, 0.02, rot=(math.radians(90), 0, 0), seg=16)   # carriage ports
    ch.obj("EChuckR19", K.mat("ChuckCeramicR19", (0.34, 0.35, 0.37), rough=0.45, speck=0.08), bevel=0.004)
    chg.obj("EChuckGrooveR19", K.mat("ChuckGrooveR19", (0.05, 0.05, 0.06), rough=0.7))
    jw.obj("ClampJawsR19", K.mat("JawAnodR19", (0.20, 0.22, 0.27), metal=0.85, rough=0.34, brushed=0.2), bevel=0.006)
    st.obj("StageCarriageR19", K.mat("StageAluR19", (0.30, 0.31, 0.34), metal=0.9, rough=0.36, brushed=0.2), bevel=0.01)


def _resist_lines(sc, x0, x1, y0, y1, pitch, h, seed=0):
    """Resist lines along X with rough edges (many short segments with jittered width)."""
    rnd = random.Random(seed)
    mb = K.MB()
    y = y0
    while y < y1:
        x = x0
        while x < x1:
            L = rnd.uniform(0.012, 0.03)
            w = pitch * 0.5 * rnd.uniform(0.8, 1.18)          # R7: visible line-edge roughness
            mb.box((x + L / 2, y + rnd.uniform(-0.006, 0.006), h / 2), (L * 1.1, w, h * rnd.uniform(0.92, 1.05)))
            x += L
        y += pitch
    return mb.obj("Resist", K.mat("ResistM", (0.42, 0.36, 0.52), rough=0.35, speck=0.15))


def _photons(sc, n):
    K.world_dark(1.0)
    sub = K.MB()
    sub.box((0, 0, -0.05), (6, 6, 0.1))
    sub.obj("Substrate", K.mat("Si", (0.32, 0.33, 0.4), metal=1.0, rough=0.12))
    _resist_lines(sc, -2.2, 2.2, -1.8, 2.4, 0.16, 0.09, seed=2)
    rnd = random.Random(8)
    core = K.emit_mat("Photon", K.VIOLET, 40.0)
    halo = K.emit_mat("PhotonHalo", K.VIOLET, 5.0, halo=0.6)
    for i in range(70):
        x, y = rnd.uniform(-1.8, 1.8), rnd.uniform(-1.6, 1.6)
        t0 = rnd.uniform(-0.2, 0.95) * n
        dur = n * 0.35
        mb, mh = K.MB(), K.MB()
        mb.sphere((0, 0, 0), 0.012, 10)                 # R8: finer, shorter photon streaks (R7: "laser rods")
        mb.tube((0, 0, 0), (0, 0, 0.13), 0.004, seg=8, r2=0.0003)
        mh.sphere((0, 0, 0), 0.035, 10)
        ob = mb.obj(f"Ph{i}", core)
        oh = mh.obj(f"PhH{i}", halo)
        oh.parent = ob
        ob.location = (x, y, 2.6)
        ob.keyframe_insert("location", frame=round(t0))
        ob.location = (x, y, 0.09)
        ob.keyframe_insert("location", frame=round(t0 + dur))
        for fc in C.fcurves(ob.animation_data.action):
            for k in fc.keyframe_points:
                k.interpolation = "LINEAR"
        # vanish on impact (scale to zero), leave a small glow mark
        ob.scale = (1, 1, 1)
        ob.keyframe_insert("scale", frame=round(t0 + dur))
        ob.scale = (0.001, 0.001, 0.001)
        ob.keyframe_insert("scale", frame=round(t0 + dur) + 1)
    K.area("Key", (-3, -3, 4), (0, 0, 0), 3, 500, (0.9, 0.93, 1.0))
    K.area("Rim", (2, 4, 2), (0, 0, 0), 4, 400, (0.75, 0.8, 1.0))
    K.point("VGlow", (0, 0, 1.5), 120, K.VIOLET, 0.5)
    # R7 (macro anchor): the wafer's bevelled edge + chuck behind the resist field, and the projection optics'
    # last mirror housing above, defocused, with the violet exposure light coming out of its aperture
    wb = K.MB()
    wb.cyl((0.0, 3.2, -0.12), 3.9, 0.06, seg=160)
    wb.obj("WaferBody", K.mat("SiEdge", (0.3, 0.31, 0.36), metal=1.0, rough=0.08))
    ch = K.MB()
    ch.cyl((0.0, 3.2, -0.32), 4.3, 0.34, seg=160)
    ch.ring((0.0, 3.2, -0.14), 4.35, 4.05, 0.05, seg=160)
    ch.obj("ChuckR7", K.mat("ChuckDk", (0.08, 0.085, 0.1), metal=0.6, rough=0.35), bevel=0.02)
    po = K.MB()
    # R8: housing lowered / moved into the top of frame (R7: it sat above the frame, the top read as empty)
    po.cyl((0.6, 3.6, 2.35), 2.2, 1.2, seg=96)
    po.ring((0.6, 3.6, 1.73), 2.25, 0.7, 0.08, seg=96)
    po.bolts((0.6, 3.6, 1.69), 1.9, 24, 0.04, 0.05)
    for k in range(6):                                   # stiffening ribs + flange stack, readable when defocused
        po.ring((0.6, 3.6, 2.0 + k * 0.12), 2.24, 2.16, 0.04, seg=96)
    po.obj("POBottom", K.mat("POHousing", (0.55, 0.56, 0.6), metal=1.0, rough=0.25, brushed=0.1))
    ap = K.MB()
    ap.cyl((0.6, 3.6, 1.72), 0.68, 0.01, seg=64)
    ap.obj("POAperture", K.emit_mat("POAp", K.VIOLET, 6.0))
    cam, tgt = K.camera("CamR2", lens=35)
    _dof(cam, 2.8, tgt)
    # R7 (D): a real crane-down + push (R6 moved ~0.5 m and read as static)
    K.key_path(cam, tgt, [(1, (-2.3, -3.9, 2.1), (0.2, 0.5, 0.45)), (n, (-0.6, -2.6, 0.9), (0.25, 0.2, 0.2))])
    return cam


def _fields_mesh(sc, wafer_r, z, fx=0.26, fy=0.165, count=188):
    """188 exposure fields as thin quads; UV.x = scan order (serpentine) / count for the reveal shader."""
    cells = []
    nx, ny = int(2 * wafer_r / fx) + 2, int(2 * wafer_r / fy) + 2
    for j in range(ny):
        for i in range(nx):
            cx = (i - nx / 2 + 0.5) * fx
            cy = (j - ny / 2 + 0.5) * fy
            far = max(math.hypot(cx + sx * fx / 2, cy + sy * fy / 2) for sx in (-1, 1) for sy in (-1, 1))
            cells.append((far, j, i, cx, cy))
    cells.sort()
    keep = sorted(cells[:count], key=lambda c: (c[1], c[2] if c[1] % 2 == 0 else -c[2]))
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    uvc = bm.loops.layers.uv.new("Cell")                # R7: per-field corner UV -> one scribe border per field
    g = 0.006
    for k, (_, j, i, cx, cy) in enumerate(keep):
        vs = [bm.verts.new((cx + sx * (fx / 2 - g), cy + sy * (fy / 2 - g), z)) for sx, sy in
              ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        f = bm.faces.new(vs)
        for lp, (u, v) in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
            lp[uvl].uv = ((k + 0.5) / count, 0.0)
            lp[uvc].uv = (u, v)
    me = bpy.data.meshes.new("Fields")
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new("Fields", me)
    sc.collection.objects.link(ob)
    return ob, keep


def _wafer(sc, n):
    K.world_dark(1.0)
    M = K.palette()
    R = 1.5
    chuck = K.MB()
    chuck.cyl((0, 0, -0.06), R * 1.06, 0.1, seg=128)
    chuck.ring((0, 0, -0.005), R * 1.1, R * 1.02, 0.02, seg=128)
    for k in range(3):
        chuck.cyl((R * 0.6 * math.cos(2 * math.pi * k / 3), R * 0.6 * math.sin(2 * math.pi * k / 3), -0.005),
                  0.03, 0.012, seg=16)
    chuck.box((0, 0, -0.3), (3.6, 3.6, 0.36))
    chuck.obj("Chuck", K.mat("ChuckCeramic", (0.12, 0.12, 0.14), rough=0.3, speck=0.2), bevel=0.01)
    # wafer with real die texture tiled across fields
    wm = _new_mat("WaferDies")
    nt, nn, l = _nodes(wm)
    b = next(x for x in nn if x.type == "BSDF_PRINCIPLED")
    b.inputs["Metallic"].default_value = 0.85
    b.inputs["Roughness"].default_value = 0.12
    tc = nn.new("ShaderNodeTexCoord")
    mp = nn.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (1 / 0.26, 1 / 0.165, 1)
    l.new(tc.outputs["Object"], mp.inputs["Vector"])
    im = nn.new("ShaderNodeTexImage")
    im.image = bpy.data.images.load(os.path.join(DIES, "zen4_ccd_full.jpg"), check_existing=True)
    l.new(mp.outputs["Vector"], im.inputs["Vector"])
    tint = nn.new("ShaderNodeMix")
    tint.data_type = "RGBA"
    tint.blend_type = "MULTIPLY"
    tint.inputs["Factor"].default_value = 0.55          # R4: silicon grey (R3 read as a violet-dyed wafer)
    tint.inputs["B"].default_value = (0.6, 0.61, 0.64, 1)
    hs = nn.new("ShaderNodeHueSaturation")              # R4: desaturate the die photo -> silicon grey dies
    hs.inputs["Saturation"].default_value = 0.12
    l.new(im.outputs["Color"], hs.inputs["Color"])
    l.new(hs.outputs["Color"], tint.inputs["A"])
    l.new(tint.outputs["Result"], b.inputs["Base Color"])
    wmb = K.MB()
    wmb.cyl((0, 0, 0.004), R, 0.008, seg=180)
    wo = wmb.obj("Wafer", wm)
    # field reveal shader: emissive violet when uv.x < progress
    fm = _new_mat("FieldGlow")
    nt, nn, l = _nodes(fm)
    for x in list(nn):
        if x.type != "OUTPUT_MATERIAL":
            nn.remove(x)
    out = next(x for x in nn if x.type == "OUTPUT_MATERIAL")
    uv = nn.new("ShaderNodeUVMap")
    sep = nn.new("ShaderNodeSeparateXYZ")
    l.new(uv.outputs["UV"], sep.inputs[0])
    prog = nn.new("ShaderNodeValue")
    _key_value(prog.outputs[0], [(1, 0.0), (round(n * 0.9), 1.0)])
    d = nn.new("ShaderNodeMath")
    d.operation = "SUBTRACT"
    l.new(prog.outputs[0], d.inputs[0])
    l.new(sep.outputs["X"], d.inputs[1])
    on0 = nn.new("ShaderNodeMath")
    on0.operation = "GREATER_THAN"
    on0.inputs[1].default_value = 0.0
    l.new(d.outputs[0], on0.inputs[0])
    tco = nn.new("ShaderNodeTexCoord")                 # clip partial edge fields to the wafer disc
    ln = nn.new("ShaderNodeVectorMath")
    ln.operation = "LENGTH"
    l.new(tco.outputs["Object"], ln.inputs[0])
    inside = nn.new("ShaderNodeMath")
    inside.operation = "LESS_THAN"
    inside.inputs[1].default_value = 1.5 * 0.985
    l.new(ln.outputs["Value"], inside.inputs[0])
    on = nn.new("ShaderNodeMath")
    on.operation = "MULTIPLY"
    l.new(on0.outputs[0], on.inputs[0])
    l.new(inside.outputs[0], on.inputs[1])
    hot = nn.new("ShaderNodeMapRange")            # the field being exposed right now is brightest
    hot.inputs["From Min"].default_value = 0.0
    hot.inputs["From Max"].default_value = 0.012
    hot.inputs["To Min"].default_value = 2.2            # R6: was 6 -> compositor bloom read as a white band
    hot.inputs["To Max"].default_value = 0.9            # R6: done fields clearly filled (R5: too faint to read)
    l.new(d.outputs[0], hot.inputs["Value"])
    st = nn.new("ShaderNodeMath")
    st.operation = "MULTIPLY"
    l.new(on.outputs[0], st.inputs[0])
    l.new(hot.outputs["Result"], st.inputs[1])
    em = nn.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*K.lin(K.VIOLET), 1)
    l.new(st.outputs[0], em.inputs["Strength"])
    tr = nn.new("ShaderNodeBsdfTransparent")
    al = nn.new("ShaderNodeMath")
    al.operation = "MULTIPLY"
    al.inputs[1].default_value = 0.5
    l.new(on.outputs[0], al.inputs[0])
    mx = nn.new("ShaderNodeMixShader")
    l.new(al.outputs[0], mx.inputs["Fac"])
    l.new(tr.outputs[0], mx.inputs[1])
    l.new(em.outputs[0], mx.inputs[2])
    # R7 (F, B8_17): every one of the 188 fields gets one dark scribe border, so the cell count reads as 188
    cuv = nn.new("ShaderNodeUVMap")
    cuv.uv_map = "Cell"
    cs = nn.new("ShaderNodeSeparateXYZ")
    l.new(cuv.outputs["UV"], cs.inputs[0])
    edges = []
    for comp in ("X", "Y"):
        inv = nn.new("ShaderNodeMath")
        inv.operation = "SUBTRACT"
        inv.inputs[0].default_value = 1.0
        l.new(cs.outputs[comp], inv.inputs[1])
        mn = nn.new("ShaderNodeMath")
        mn.operation = "MINIMUM"
        l.new(cs.outputs[comp], mn.inputs[0])
        l.new(inv.outputs[0], mn.inputs[1])
        edges.append(mn)
    mn2 = nn.new("ShaderNodeMath")
    mn2.operation = "MINIMUM"
    l.new(edges[0].outputs[0], mn2.inputs[0])
    l.new(edges[1].outputs[0], mn2.inputs[1])
    bd = nn.new("ShaderNodeMath")
    bd.operation = "LESS_THAN"
    bd.inputs[1].default_value = 0.045
    l.new(mn2.outputs[0], bd.inputs[0])
    bdi = nn.new("ShaderNodeMath")
    bdi.operation = "MULTIPLY"
    l.new(bd.outputs[0], bdi.inputs[0])
    l.new(inside.outputs[0], bdi.inputs[1])
    dark = nn.new("ShaderNodeBsdfDiffuse")
    dark.inputs["Color"].default_value = (0.01, 0.01, 0.012, 1)
    mx2 = nn.new("ShaderNodeMixShader")
    l.new(bdi.outputs[0], mx2.inputs["Fac"])
    l.new(mx.outputs[0], mx2.inputs[1])
    l.new(dark.outputs[0], mx2.inputs[2])
    l.new(mx2.outputs[0], out.inputs["Surface"])
    fo, keep = _fields_mesh(sc, R, 0.0095)
    fo.data.materials.append(fm)
    # R14 (root cause #7, B8_17 #1 "物镜头下没有光，场格自己变紫"): the exposure itself - a violet slit band lies on
    # the field being exposed and a soft curtain of violet light comes down onto it (fading out upward, so it reads
    # as light from the optics above, not a solid bar); both track the scan, the field fills in behind it
    sm = K.MB()
    # R15 (root cause #4, B8_17 "曝光光斑是方形辉光块，读不出狭缝"): a thin crisp slit line (field width x 1.6 cm)
    # under a faint thin light sheet, instead of a 5 cm glow block under a bright frustum
    sm.box((0, 0, 0), (0.26, 0.016, 0.002))
    so = sm.obj("Slit", K.emit_mat("SlitM", (0.86, 0.8, 1.0), 18.0))
    cur = _new_mat("SlitCurtain")
    nt, nn, l = _nodes(cur)
    for x in list(nn):
        if x.type != "OUTPUT_MATERIAL":
            nn.remove(x)
    out_ = next(x for x in nn if x.type == "OUTPUT_MATERIAL")
    tcg = nn.new("ShaderNodeTexCoord")
    sz = nn.new("ShaderNodeSeparateXYZ")
    l.new(tcg.outputs["Generated"], sz.inputs[0])
    iv = nn.new("ShaderNodeMath")
    iv.operation = "SUBTRACT"
    iv.inputs[0].default_value = 1.0
    l.new(sz.outputs["Z"], iv.inputs[1])
    pw = nn.new("ShaderNodeMath")
    pw.operation = "POWER"
    pw.inputs[1].default_value = 2.2
    l.new(iv.outputs[0], pw.inputs[0])
    al_ = nn.new("ShaderNodeMath")
    al_.operation = "MULTIPLY"
    al_.inputs[1].default_value = 0.22
    l.new(pw.outputs[0], al_.inputs[0])
    st_ = nn.new("ShaderNodeMath")
    st_.operation = "MULTIPLY"
    st_.inputs[1].default_value = 0.9
    l.new(pw.outputs[0], st_.inputs[0])
    em_ = nn.new("ShaderNodeEmission")
    em_.inputs["Color"].default_value = (*K.lin(K.VIOLET), 1)
    l.new(st_.outputs[0], em_.inputs["Strength"])
    tr_ = nn.new("ShaderNodeBsdfTransparent")
    mx_ = nn.new("ShaderNodeMixShader")
    l.new(al_.outputs[0], mx_.inputs["Fac"])
    l.new(tr_.outputs[0], mx_.inputs[1])
    l.new(em_.outputs[0], mx_.inputs[2])
    l.new(mx_.outputs[0], out_.inputs["Surface"])
    cbm = bmesh.new()                                     # frustum: wide at the top, slit-sized at the wafer
    H = 0.75
    vb = [cbm.verts.new((sx * 0.13, sy * 0.008, 0.0)) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    vt = [cbm.verts.new((sx * 0.16, sy * 0.03, H)) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    for i_ in range(4):
        j_ = (i_ + 1) % 4
        cbm.faces.new((vb[i_], vb[j_], vt[j_], vt[i_]))
    cme = bpy.data.meshes.new("SlitCurtain")
    cbm.to_mesh(cme)
    cbm.free()
    co = bpy.data.objects.new("SlitCurtain", cme)
    sc.collection.objects.link(co)
    cme.materials.append(cur)
    co.parent = so
    for k, (_, j, i, cx, cy) in enumerate(keep):
        so.location = (cx, cy, 0.0105)
        so.keyframe_insert("location", frame=1 + (k / len(keep)) * n * 0.9)
    so.keyframe_insert("location", frame=round(n * 0.9) + 2)
    so.scale = (1, 1, 1)
    so.keyframe_insert("scale", frame=round(n * 0.9) + 2)
    so.scale = (0.001, 0.001, 0.001)                    # scan done: the light goes off
    so.keyframe_insert("scale", frame=round(n * 0.9) + 4)
    for fc in C.fcurves(so.animation_data.action):
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR"
    # R17 (root cause #4, B8_17 "曝光点是悬空的白色短线 + 一团紫雾，看不出光从哪里来"): change ROUTE - the fog
    # curtain is removed; ONE thin violet core comes straight down from above the frame and lands in the slit,
    # and a small light at the slit makes the landing visibly light the fields around it
    import misc_beam_r17 as BR17
    co.hide_render = True
    core17 = BR17.thin_core("ExposeCoreR17", Vector((0, 0, 0.003)), Vector((0, 0, 3.2)), 0.007, K.VIOLET, 10.0,
                            0.95, fade1=0.35, seg=12)
    core17.parent = so
    lt17 = K.point("SlitLightR17", (0, 0, 0.05), 1.2, K.VIOLET, 0.03)
    lt17.parent = so
    lt17.visible_camera = False
    lt17.visible_glossy = False
    lt17.data.keyframe_insert("energy", frame=round(n * 0.9) + 2)
    lt17.data.energy = 0.0
    lt17.data.keyframe_insert("energy", frame=round(n * 0.9) + 4)
    # R18 (root cause #2, R17 review B8_17 #1 "紫光是一根等宽实心光柱"): the thin core is replaced by a FLAT k4A cone,
    # wide at the projection optics' exit aperture above (POAperture17, fixed) and converging into the moving slit;
    # soft edge + inner glow, brighter toward the slit; slit highlight one step brighter
    import misc_beam_r18 as BR18
    core17.hide_render = True
    # the exit port = the bottom of the projection-optics column, IN frame: a housing tube coming down from above
    # the frame, a machined port block with a glowing slot on its underside; the cone leaves that slot
    PX, PY, PZ = 0.45, 1.3, 1.72
    if _r21("B8_17"):                            # R21 row #5: barrel left so the scanning stage clears the cassette
        PX -= 1.2
    pmb = K.MB()
    pmb.cyl((PX, PY, PZ + 0.18 + 1.5), 0.42, 3.0, seg=64)
    pmb.ring((PX, PY, PZ + 0.2), 0.47, 0.3, 0.06, seg=64)
    pmb.box((PX, PY, PZ + 0.09), (1.0, 0.5, 0.18))
    pmb.obj("ExitPortR18", K.mat("ExitPortR18M", (0.36, 0.37, 0.41), metal=1.0, rough=0.3, brushed=0.1), bevel=0.01)
    slot = K.MB()
    slot.box((PX, PY, PZ - 0.002), (0.88, 0.34, 0.004))
    slot.obj("ExitSlotR18", K.emit_mat("ExitSlotR18M", (0.78, 0.68, 1.0), 6.0))
    _fc, _port = BR18.hooked_cone("SlitConeR18", (PX, PY, PZ - 0.006), (0.43, 0.16), (0.13, 0.008), so, K.VIOLET,
                                  1.9, 0.42, edge=2.2, inner=0.4, inner_gain=1.8, gain=1.8)
    for ob in _fc:
        ob.hide_render = False
        ob.keyframe_insert("hide_render", frame=round(n * 0.9) + 2)
        ob.hide_render = True
        ob.keyframe_insert("hide_render", frame=round(n * 0.9) + 3)
    _sm = bpy.data.materials["SlitM"]
    for nd in _sm.node_tree.nodes:
        if nd.type == "EMISSION":
            nd.inputs["Strength"].default_value *= 1.45
    # R17 (B8_17 "已曝光场是均匀发光的紫色平块，像屏幕贴图"): exposed fields become a dim violet latent image over
    # the visible die pattern; only the field under the slit is bright, so the scan reads strip by strip
    hot.inputs["To Max"].default_value = 0.16
    al.inputs[1].default_value = 0.3
    # R14 (B8_17 #2): wafer notch at 6 o'clock
    ntc = K.MB()
    ntc.cyl((0, -R, 0.0045), 0.035, 0.0105, seg=24)
    ntc.obj("WaferNotch", K.mat("NotchDk", (0.02, 0.02, 0.025), rough=0.6))
    # finished wafers stacking up in a cassette at the right
    cas = K.MB()
    cx0 = 3.4
    for zz in (0.0, 1.9):
        cas.box((cx0, 0, -0.12 + zz), (3.3, 3.3, 0.06))
    for sx in (-1, 1):
        cas.box((cx0, sx * 1.6, 0.85), (2.8, 0.06, 1.9))
        for k in range(24):
            cas.box((cx0 - 1.0, sx * 1.55, -0.05 + k * 0.075), (0.6, 0.06, 0.012))
    cas.obj("Cassette", K.mat("CassetteAlu", (0.7, 0.71, 0.74), metal=1.0, rough=0.3, brushed=0.1), bevel=0.01)   # R5: brushed metal, not white blocks
    wfm = K.mat("WaferStack", (0.45, 0.47, 0.6), metal=0.9, rough=0.15)
    for k in range(24):
        mbw = K.MB()
        mbw.cyl((cx0, 0, -0.05 + k * 0.075), R * 0.98, 0.008, seg=96)
        ob = mbw.obj(f"Stack{k}", wfm)
        t_on = 1 + round(n * (0.1 + 0.85 * k / 24))
        ob.hide_render = True
        ob.keyframe_insert("hide_render", frame=1)
        ob.keyframe_insert("hide_render", frame=t_on - 1)
        ob.hide_render = False
        ob.keyframe_insert("hide_render", frame=t_on)
    K.area("Key", (-3, -4, 6), (0.8, 0, 0), 5, 1500, (0.95, 0.96, 1.0))
    K.area("Rim", (2, 5, 3), (1, 0, 0), 6, 900, (0.75, 0.8, 1.0))
    # R6: the R5 strip light mirrored in the wafer as a blown-out white band that read as the exposure light
    K.area("Strip", (-5, 4, 2.0), (0, 0, 0), 0.5, 220, (1, 1, 1), size_y=6)
    for nm in ("Key", "Strip", "Rim"):                  # their mirror images on the wafer read as a white slit
        bpy.data.objects[nm].visible_glossy = False
    K.area("CasSheen", (6, -2.5, 4), (3.4, 0, 0.6), 3, 900, (0.95, 0.97, 1.0))   # sheen on cassette / chuck rim
    K.area("ChuckKick", (-3.5, -1.5, 0.6), (0, 0, 0), 2, 250, (0.85, 0.9, 1.0))
    K.floor("Floor", K.mat("FloorDark", (0.04, 0.045, 0.055), rough=0.35), z=-0.48)
    # R8 (R7: "dark grey empty background"): the machine behind, out of focus - a parts-kit service wall and the
    # projection optics' bottom housing with its violet exposure aperture above the stage
    import parts_kit_r8 as PK
    Mk = K.palette()
    # R16 (root cause #5, B8_17 "墙面同一种面板铺满，7 种件"): the repeated-block wall is replaced by a service wall
    # of 15 different nameable parts (pumps, valves, viewport, gauges, valve island, ion pump, PSU, drag chain,
    # linear axis, manifold, hoses, harness), pushed back 1.6 m and thrown out of focus
    import misc_kit_r16 as MK
    bw = K.MB()
    bw.box((1.0, 6.3, 1.6), (16.0, 0.1, 6.0))
    bw.obj("BackWall", Mk["anod"])
    _pw16 = MK.parts_wall_r16(Mk, (1.4, 6.2, -1.3), 3.0)
    _b817_r19(sc, n, Mk, _pw16, hot, al, so)
    po = K.MB()
    po.cyl((1.4, 2.4, 3.35), 1.6, 1.3, seg=96)
    po.ring((1.4, 2.4, 2.68), 1.65, 0.5, 0.08, seg=96)
    for k in range(5):
        po.ring((1.4, 2.4, 2.9 + k * 0.14), 1.64, 1.57, 0.04, seg=96)
    po.obj("POBottom17", K.mat("POHousing17", (0.55, 0.56, 0.6), metal=1.0, rough=0.25, brushed=0.1))
    ap = K.MB()
    ap.cyl((1.4, 2.4, 2.67), 0.45, 0.01, seg=64)
    ap.obj("POAperture17", K.emit_mat("POAp17", K.VIOLET, 5.0))
    K.area("BackWash", (1.0, 1.0, 4.5), (1.0, 4.6, 1.5), 6, 700, (0.8, 0.85, 1.0))
    bpy.data.objects["BackWash"].location = (1.0, 2.0, 5.0)
    bpy.data.objects["BackWash"].data.energy = 1100
    cam, tgt = K.camera("CamR2", lens=32)
    _dof(cam, 8.0, tgt)
    cam.data.dof.aperture_fstop = 1.4                  # R16: back wall defocused, wafer + optics stay sharp
    # R15 (B8_17 "零件挤在上沿被裁掉一半"): camera ~10 deg lower, aim raised, so the optics bottom and the cassette
    # sit whole in frame above the wafer
    K.key_path(cam, tgt, [(1, (-1.0, -6.0, 3.0), (1.1, 0.5, 0.45)), (n, (0.4, -5.8, 2.7), (1.4, 0.5, 0.45))])
    if _r20("B8_17"):                            # R20 row #4: 188 half-fields, soft cone -> scanning slit
        import misc_b817_r20 as W20
        W20.apply(sc, n, R, so, fo, _fc, keep, prog)
        if _r21("B8_17"):                        # R21 row #5: slit fixed under the barrel, wafer stage scans under it
            import misc_b817_r21 as W21
            W21.apply(sc, n, R, so, W20.layout(R), port=(PX, PY, PZ), cam=(cam, tgt))
    sc["hdri"] = "studio_small_09"
    sc["hdri_strength"] = 0.35
    return cam


def _wave_curve(name, pts, radii, mat):
    cd = bpy.data.curves.new(name, "CURVE")
    cd.dimensions = "3D"
    sp = cd.splines.new("POLY")
    sp.points.add(len(pts) - 1)
    for p, (x, y, z) in enumerate(pts):
        sp.points[p].co = (x, y, z, 1)
        sp.points[p].radius = radii[p]
    cd.bevel_depth = 0.05
    cd.bevel_resolution = 4
    cd.use_fill_caps = True
    ob = bpy.data.objects.new(name, cd)
    bpy.context.scene.collection.objects.link(ob)
    ob.data.materials.append(mat)
    return ob, cd


def _bokeh_backdrop(sc, y0=40.0, seed=0, count=26):
    """Out-of-focus machine interior far behind (y >= y0): violet beam segments, cyan LEDs, dim metal panels."""
    rnd = random.Random(seed)
    mb, mp, ml = K.MB(), K.MB(), K.MB()
    for _ in range(count):
        c = Vector((rnd.uniform(-30, 30), y0 + rnd.uniform(0, 25), rnd.uniform(-14, 14)))
        kind = rnd.random()
        if kind < 0.35:
            a = c + Vector((rnd.uniform(-8, 8), rnd.uniform(-2, 2), rnd.uniform(-8, 8)))
            mb.tube(c, a, 0.18, seg=10)
        elif kind < 0.7:
            mp.box(c, (rnd.uniform(2, 6), 0.3, rnd.uniform(2, 6)), rot=(0, rnd.uniform(-0.4, 0.4), 0))
        else:
            ml.sphere(c, 0.25, 8)
    mb.obj("BkBeams", K.emit_mat("BkBeamM", K.VIOLET, 6.0))
    mp.obj("BkPanels", K.mat("BkPanelM", (0.4, 0.42, 0.48), metal=1.0, rough=0.3))
    ml.obj("BkLeds", K.emit_mat("BkLedM", K.CYAN, 8.0))
    K.area("BkKey", (0, y0 - 6, 18), (0, y0 + 10, 0), 30, 9000, (0.7, 0.75, 1.0))


def _machine_backdrop(sc, keep=None, dim=1.0, r17=None):
    """R3 (H14 fix): the real de-cased machine (same cutaway kit as C_03 / B5_01) as the out-of-focus world behind
    data overlays, instead of a dark void with abstract bokeh."""
    import build_cutaway_r2 as B
    M = K.palette()
    M["wafer"] = K.mat("WaferSi", (0.32, 0.33, 0.42), metal=1.0, rough=0.08)
    M["cone"] = K.beam_column_mat("EUVCone", K.VIOLET, strength=1.4, edge=0.4, core=0.06, vol=0.15)
    K.world_dark(0.55)
    K.floor("Floor", K.mat("FloorDark", (0.05, 0.055, 0.065), rough=0.3, coat=0.3), z=0.0)
    K.area("Key", (-6, -8, 8), (-2, 0, 2), 5, 2400, (0.95, 0.96, 1.0))
    K.area("Rim", (-3, 6, 7), (-3, 0, 2), 10, 1800, (0.7, 0.75, 1.0))
    K.area("FillR", (7, -5, 3), (2, 0, 2), 4, 600, (0.6, 0.7, 1.0))
    K.area("Top", (-3, 0, 12), (-3, 0, 0), 14, 600, (0.9, 0.92, 1.0), size_y=4)
    # R14 (root cause #1, A2_03 / A2_08 "等宽、满是条纹噪点的发光柱"): soft open cones that open / narrow between
    # mirror landing spots, no streak noise; K.beam_columns is swapped only for this call and restored after
    M["beam_wide"] = _soft_beam_mat("EUVSoftR14", strength=2.4 * dim, alpha=0.7 * min(1.0, 0.4 + dim))
    M["cone"] = _soft_beam_mat("EUVSoftConeR14", strength=1.9, alpha=0.6)
    spots = []
    orig, orig_cone = K.beam_columns, K.cone_beam
    K.beam_columns = _r14_columns_factory(spots, keep)
    if keep:                                   # R16 (root cause #3): each leg a fading cone into its landing spot
        import misc_kit_r16 as MK
        K.beam_columns, _r16_built = MK.columns_factory_r16(spots, keep, mat=(2.4 * dim, 0.55 * min(1.0, 0.4 + dim)))
    if r17 is not None:                        # R17 (root cause #4): change ROUTE - thin cores + landing highlights
        import misc_beam_r17 as BR17
        K.beam_columns, _r17_built = BR17.columns_factory_r17(spots, keep, r_core=r17.get("r", 0.016),
                                                              strength=r17.get("core", 7.0), color=r17.get("color"))
        # the hexapod mirror faces carried a built-in violet emissive disc each (M["spot"]) = "glowing discs facing
        # the camera, read as spotlights": they become plain polished mirror metal
        M["spot"] = K.mat("MirrorFaceR17", (0.78, 0.78, 0.82), metal=1.0, rough=0.06)
    if keep:                                   # R15: no collector cone either - one path only
        K.cone_beam = lambda *a_, **k_: None
    try:
        B.machine(M, studio=False, cut=True)
    finally:
        K.beam_columns, K.cone_beam = orig, orig_cone
    if r17 is not None:
        # every mirror the path touches gets ONE soft highlight on its face + a small light that lights its mount;
        # the other mirrors lose their violet bounce lights (they read as a row of spotlights) and stay metal
        for p, nrm, j in spots:
            BR17.landing(f"LandR17_{j}", p, nrm, r17.get("spot", 0.09), strength=r17.get("spot_e", 5.0),
                         light=r17.get("light", 6.0), squash=0.7, color=r17.get("spot_c"))
        BR17.prune_bounce({j - 1 for _p, _n, j in spots})
        for ob in bpy.data.objects:
            if ob.type == "LIGHT" and ob.name.startswith("Bounce"):
                ob.data.energy *= r17.get("bounce", 0.6)
        sc["hdri"] = "hangar_interior"
        sc["hdri_strength"] = 0.25
        K.clean_cycles(sc)
        return B
    smb = K.MB()
    for p, nrm, r in spots:
        _landing_spot(smb, p, nrm, r)
    smb.obj("LandingSpotsR14", K.emit_mat("LandingSpotR14", (0.82, 0.72, 1.0), 7.0 * dim, halo=0.5))
    sc["hdri"] = "hangar_interior"
    sc["hdri_strength"] = 0.25
    K.clean_cycles(sc)
    return B


def _wave(sc, n):
    """A2_08: 193 nm (grey) and 13.5 nm (violet) as two equal-length waves stacked above the wafer stage, in
    front of the out-of-focus projection optics; the violet period is the grey one / 14.3, so the viewer can
    count ~14 violet crests per grey crest. No floating boxes."""
    # R15 (root cause #4, A2_08 "背景紫光束与 13.5 nm 紫波同色抢眼"): one dim PO fold only (30 %), so violet
    # belongs to the foreground wave
    # R17 (root cause #4, A2_08 "背景虚焦里仍有几条交叉紫光柱，和前景紫波抢色"): background route = one thin
    # neutral cool-grey core + its mirror highlights (no violet cones, mirror discs no longer emissive), so violet
    # belongs to the 13.5 nm wave only
    B = _machine_backdrop(sc, keep=(9, 11), dim=0.3, r17=dict(r=0.012, core=2.5, spot=0.08, spot_e=1.6, light=0.0, bounce=0.0,
                                                               color=(0.72, 0.76, 0.84), spot_c=(0.8, 0.84, 0.9)))
    cx, y, span = 1.55, -2.6, 1.8
    lam193 = span / 2.0
    lam135 = lam193 / 14.3
    z193, z135 = 1.95, 1.55
    g = [(cx - span / 2 + span * i / 599, y, z193 + 0.11 * math.sin(2 * math.pi * (span * i / 599) / lam193))
         for i in range(600)]
    og, cg = _wave_curve("Wave193", g, [1.0] * 600, K.emit_mat("Grey193", (0.72, 0.75, 0.82), 3.0))
    cg.bevel_depth = 0.006
    # R17 (A2_08 R16 "紫波振幅只有白波一半、发光更强 → 读成更弱 / 不同的东西"): SAME amplitude (0.11) as the
    # 193 nm wave, same line width, no extra halo - only the wavelength (and the colour) differs
    A135 = 0.11
    v = [(cx - span / 2 + span * i / 2399, y, z135 + A135 * math.sin(2 * math.pi * (span * i / 2399) / lam135))
         for i in range(2400)]
    ov, cv = _wave_curve("Wave135", v, [1.0] * 2400, K.emit_mat("WaveMR17", K.VIOLET, 6.0))
    cv.bevel_depth = 0.006
    oh, ch = _wave_curve("Wave135Halo", v, [1.0] * 2400, K.emit_mat("WaveHaloM", K.VIOLET, 2.5, halo=0.5))
    ch.bevel_depth = 0.014
    oh.hide_render = True
    for c in (cv, ch):
        c.bevel_factor_end = 0.08
        c.keyframe_insert("bevel_factor_end", frame=1)
        c.bevel_factor_end = 1.0
        c.keyframe_insert("bevel_factor_end", frame=round(n * 0.72))
    # equal-length bracket: two thin end ticks spanning both waves
    br = K.MB()
    for x in (cx - span / 2, cx + span / 2):
        br.box((x, y, (z193 + z135) / 2), (0.004, 0.004, 0.62))
    br.obj("SpanTicks", K.emit_mat("TickInk", (0.8, 0.84, 0.92), 2.0))
    cam, tgt = K.camera("CamR2", lens=35)
    # R6 (D): parallax arc - the camera trucks 1.1 m while aiming through the wave centre, so the waves stay put
    # and the out-of-focus machine behind slides by ~1.2 m (R5 read the background as frozen)
    def _aim(cxm, cym, czm):
        k = -cym / (y - cym)
        return (cxm + (cx - cxm) * k, 0.0, czm + ((z193 + z135) / 2 - czm) * k)
    K.key_path(cam, tgt, [(1, (1.0, -5.0, 1.95), _aim(1.0, -5.0, 1.95)),
                          (n, (2.1, -4.85, 1.72), _aim(2.1, -4.85, 1.72))], interp="LINEAR")
    foc = bpy.data.objects.new("WaveFocus", None)
    sc.collection.objects.link(foc)
    foc.location = (cx, y, (z193 + z135) / 2)
    _dof(cam, 0.5, foc)
    K.anchors("A2_08", {"w193": Vector((cx - span / 2 + lam193 * 0.25, y, z193 + 0.11)),
                        "w135": Vector((cx + span * 0.3, y, z135 + A135)),
                        "span_l": Vector((cx - span / 2, y, z135 - 0.31)), "span_r": Vector((cx + span / 2, y, z135 - 0.31)),
                        "p0": Vector((cx - span / 2, y, z135 - 0.12)), "p1": Vector((cx - span / 2 + lam193, y, z135 - 0.12)),
                        "wafer": B.WAFER})
    return cam


def _bokeh(sc, n):
    """A2_03: out-of-focus machine (projection optics, violet path, wafer) under the formula overlay; anchors for
    the lambda -> beam and NA -> mirror leader lines."""
    # R15: keep=(6, 11) one W-shaped PO fold (was a net of 4-5 columns)
    # R17 (root cause #4, A2_03 "3-4 crossing violet columns out of glowing discs = spotlights"): the scene above is
    # rebuilt with ONE V-shaped return PO3 -> PO4 -> PO5 (then the NA cone onto the wafer) drawn as thin cores,
    # one soft highlight on each mirror it hits; no wide cones, the untouched mirrors are plain metal
    # R18 (root cause #2, R17 review A2_03 #1/#2 "镜子读成金属甜甜圈" / "一屏不止一条主光路… NA 锥被画成实心的花瓶"):
    # ONE light path only = the last fold PO4 -> PO5 and the converging NA cone PO5 -> a visible wafer; both are
    # k4A volumetric cones (misc_beam_r18.vol_cone: radii follow the mirror apertures, inner glow, soft edge); the
    # crossing PO3 -> PO4 column is gone; every PO mirror gets a solid polished disc face inside its ring mount
    import misc_beam_r18 as BR18
    B = _machine_backdrop(sc, keep=(10, 11), dim=0.75, r17=dict(r=0.014, core=9.0, spot=0.1, spot_e=6.0, light=8.0))
    for ob in list(bpy.data.objects):
        if ob.name.startswith("CoreR17_"):
            bpy.data.objects.remove(ob, do_unlink=True)
    _pts = [Vector(B.MASK)] + [Vector(v) for v in B.PO] + [Vector(B.WAFER)]
    # R19 (root cause #2, A2_03 R18 "镜子画成粗金属甜甜圈环…给每个环装上实心镜盘（参照 k4A 的银色厚镜片和高光边），让光锥的
    # 落点落在镜盘中心，并留一个可见的亮斑"): every ring mount now holds a THICK solid silver mirror blank (misc_mirror_r19:
    # metallic, roughness 0.05, light tone, bright chamfer rim) that fills the ring; the fold cone starts / ends exactly on
    # the PO4 / PO5 face centres, each with a soft landing spot (no fog blob at the end)
    import misc_mirror_r19 as MM
    _mm, _mr = MM.mirror_mat("MirrorR19"), K.mat("MirrorRimR19", (0.95, 0.95, 0.97), metal=1.0, rough=0.12)
    _mb = K.mat("MirrorBlankR19", (0.8, 0.81, 0.84), metal=1.0, rough=0.16)    # polished silver blank, seen from behind too
    _nrm = []
    for i, p_ in enumerate(B.PO):
        nr_ = K.mirror_normal(_pts[i], Vector(p_), _pts[i + 2])
        _nrm.append(nr_)
        # the blank overhangs the ring mount (outer r * 1.16): a thick silver plate sitting ON the ring, not a hole
        MM.solid_mirror(f"MirrorR19_{i}", p_, nr_, B.PO_R[i] * 1.24, thick=0.07, mat=_mm, rim_mat=_mr, back_mat=_mb)
    for i in (4, 5):
        MM.landing(f"MirrorSpotR19_{i}", Vector(B.PO[i]) - _nrm[i] * 0.004, _nrm[i], B.PO_R[i] * 0.28, strength=8.0, light=2.5)
    BR18.vol_cone("FoldR18", B.PO[4], B.PO[5], B.PO_R[4] * 0.62, B.PO_R[5] * 0.55, K.VIOLET, 3.2, 0.55, edge=1.6,
                  gain=0.3)
    # R14 (root cause #7 / review A2_03 #1 "NA 只有文字，没有画面"): the last PO mirror's full converging light cone
    # onto the wafer point (see-through, bright silhouette) + its half-angle theta drawn as a cyan arc at the apex
    # and a dashed cyan axis; it fades in when the narration reaches NA (~50 %)
    po5, wf = Vector(B.PO[5]), Vector(B.WAFER)
    # R18 (R17 review A2_03 #2 "NA 锥…尖端扎进地板，没有落到晶圆"): the stage wafer (z 0.62) sits BELOW the PO
    # housing floor (top z 1.025), so the cone pierced the floor; the cone now converges onto a wafer shown on a
    # chuck standing on that floor, straight under the last mirror's cone
    wf = Vector((B.WAFER.x, 0.0, 1.065))
    u = (po5 - wf).normalized()
    perp = u.cross(Vector((0, 1, 0))).normalized()
    rim = B.PO_R[5] * 0.82                                      # R18: NA cone rim = the last mirror's aperture
    na_cone, _na_in = BR18.vol_cone("NAConeR18", po5, wf, rim, 0.006, K.VIOLET, 2.6, 0.5, edge=1.7, gain=1.4)
    # R18: a visible wafer surface under the apex (polished Si disc on the stage) + the focus highlight lying on it
    wmb = K.MB()
    wmb.cyl(wf - Vector((0, 0, 0.004)), 0.3, 0.008, seg=96)
    wmb.obj("WaferR18", K.mat("WaferR18M", (0.36, 0.36, 0.46), metal=1.0, rough=0.1))
    cmb = K.MB()
    cmb.cyl(Vector((wf.x, 0.0, (1.025 + wf.z - 0.008) / 2)), 0.34, wf.z - 0.008 - 1.025, seg=96)
    cmb.obj("ChuckR18", K.mat("ChuckR18M", (0.12, 0.12, 0.14), rough=0.3), bevel=0.004)
    import misc_beam_r17 as BR17
    _wl = BR17.landing("WaferSpotR18", wf + Vector((0, 0, 0.001)), Vector((0, 0, 1)), 0.05, strength=9.0, light=3.0)
    L = (po5 - wf).length
    e = ((po5 + perp * rim) - wf).normalized()
    th = math.acos(max(-1.0, min(1.0, u.dot(e))))
    amb = K.MB()
    ar = 0.3                                                     # R18: theta arc sits at the apex on the wafer
    arc = [wf + (u * math.cos(th * k / 16) + perp * math.sin(th * k / 16)) * ar for k in range(17)]
    for a_, b_ in zip(arc, arc[1:]):
        amb.tube(a_, b_, 0.006, seg=8)
    for k in range(4):                                           # R18: short dashed axis + edge stub at the apex only
        amb.tube(wf + u * L * (0.04 + k * 0.08), wf + u * L * (0.08 + k * 0.08), 0.003, seg=6)
    amb.tube(wf, wf + e * L * 0.35, 0.003, seg=6)
    na_ink = amb.obj("NATheta", K.emit_mat("NAThetaInk", K.CYAN, 3.5))
    f_on = round(n * 0.48)
    for ob in (na_cone, _na_in, na_ink, _wl):
        ob.hide_render = True
        ob.keyframe_insert("hide_render", frame=1)
        ob.keyframe_insert("hide_render", frame=f_on - 1)
        ob.hide_render = False
        ob.keyframe_insert("hide_render", frame=f_on)
    if _r21("A2_03"):                            # R21 row #3: cones cut by the mirror faces, turn on the face centre
        import misc_a203_r21 as A21
        A21.apply(B, _nrm, wf)
    cam, tgt = K.camera("CamR2", lens=32)
    # R6 (D): push in + rack focus: starts soft (formula beat), focus pulls onto the projection mirror the NA
    # leader points at, so the background changes and the leader lands on a sharp mirror and its light cone
    # R14: the end pose tilts down so the whole NA cone (mirror -> wafer apex) and its theta arc are in frame
    K.key_path(cam, tgt, [(1, (0.5, -4.7, 2.75), (1.6, 0, 2.55)), (n, (1.55, -3.9, 2.05), (1.95, 0, 1.55))],
               interp="BEZIER")
    foc = bpy.data.objects.new("NAFocus", None)
    sc.collection.objects.link(foc)
    foc.location = (0.9, -3.0, 2.6)
    foc.keyframe_insert("location", frame=1)
    foc.keyframe_insert("location", frame=round(n * 0.35))
    foc.location = tuple(po5.lerp(wf, 0.35))                 # R14: focus holds mirror + cone + theta arc
    foc.keyframe_insert("location", frame=round(n * 0.75))
    _dof(cam, 1.6, foc)
    K.anchors("A2_03", {"beam": B.PO[4].lerp(B.PO[5], 0.5), "mirror": B.PO[5], "wafer": B.WAFER, "mask": B.MASK,
                        "theta": arc[8] + perp * 0.03, "na_apex": wf})
    return cam


VARIANTS = {"space": _space, "globe": _globe, "mirror": _mirror, "pellicle": _pellicle, "photons": _photons,
            "wafer": _wafer, "wave": _wave, "bokeh": _bokeh}


class _R30BeamGate:
    """beam_hook_r29 stays LAST (R30 HARD) and converts the legs of every shot in R29_BEAM, R30_BEAM or R31_BEAM."""
    def __contains__(self, shot):
        return shot in R29_BEAM or shot in R30_BEAM or shot in R31_BEAM


def _r22_hooks(shot):
    """R22: hook modules for this shot (in set order)."""
    import importlib
    return [importlib.import_module(h) for s_, h in R22_HOOKS + R23_HOOKS + R24_HOOKS + R25_HOOKS + R26_HOOKS + R27_HOOKS + R28_HOOKS + R29_HOOKS[:-1] + R30_HOOKS + R31_HOOKS + [(_R30BeamGate(), R29_HOOKS[-1][1])] if shot in s_]   # R23 hooks after R22, R24 after R23, R25 after R24


def _r22_pre(variant, shot):
    for h in _r22_hooks(shot):
        if hasattr(h, "pre"):
            h.pre(variant, shot, __import__(__name__))


def _r22_post(sc, variant, shot):
    for h in _r22_hooks(shot):
        if hasattr(h, "post"):
            h.post(sc, variant, shot)


def build(variant="space", shot=None):
    n = K.nframes(shot) if shot else 120
    _CUR_SHOT[0] = shot
    _r22_pre(variant, shot)
    sc = C.reset_scene(n)
    sc["vignette"] = 0.3
    sc["film_grain"] = 0.1
    K.clean_cycles(sc)
    cam = VARIANTS[variant](sc, n)
    sc.camera = cam
    _r22_post(sc, variant, shot)
    return sc
