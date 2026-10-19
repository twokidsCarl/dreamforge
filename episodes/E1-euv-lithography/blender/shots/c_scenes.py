"""C — the assembly long take, on the stylised whole-machine layout (build_machine). Variants:

  assemble  C_01  clay: subsystems float in place, fly in and lock together; orbit and push to the source
  ride      C_03  xray: ride the beam from the collector through IF and the illuminator onto the mask
            C_04  energy: down through the six projection mirrors to the wafer; stages race; latent line
            C_05  energy: fast pull-back to the whole machine, the light path as one glowing nerve
  pulses    C_06  energy: flashes run plasma -> wafer, faster and faster until they fuse into one band
  accents   C_08  xray: source, mirrors, mask, stages light up in their accent colours, then one beam threads them
            C_09  xray + HUD: each module's little axis jitters, then all snap to one shared origin and grid
  heart     C_10  energy: the path beats like a heart, fades, an ember left at the plasma
Illustrative layout, not the ASML exterior.
"""
import math
import random

import bpy
from mathutils import Euler, Vector

import a0_scenes as A0
import build_machine as BM
import common as C
import materials as M
import sample_b1 as B
import styles

FRAMES = 520
VIOLET = (0.62, 0.45, 1.0)
CYAN = (0.2, 0.85, 0.95)
ORANGE = (1.0, 0.42, 0.12)
_key, _box, _cyl = A0._key, A0._box, A0._cyl
N = len(BM.PATH) - 1                                   # path segments; bevel factor steps per point


def _P(i):
    return Vector(BM.PATH[i])


def _machine_and_path():
    before = set(bpy.data.objects)
    path, pmat = BM.machine()
    new = [o for o in bpy.data.objects if o not in before]
    return path, pmat, new


def _grow(path, keys):
    for f, v in keys:
        path.data.bevel_factor_end = v
        path.data.keyframe_insert("bevel_factor_end", frame=f)


def _stages_race(f0, f1, period=24):
    rs, rt = bpy.data.objects["ReticleStage"], bpy.data.objects["Reticle"]
    ws, wf = bpy.data.objects["WaferStage"], bpy.data.objects["Wafer"]
    base = {o.name: o.location.copy() for o in (rs, rt, ws, wf)}
    k = 0
    for f in range(f0, f1, period):
        s = 1 if k % 2 == 0 else -1
        for o, amp in ((rs, 0.8), (rt, 0.8), (ws, -0.2), (wf, -0.2)):
            loc = base[o.name].copy()
            loc.x += s * amp
            _key(o, f, location=tuple(loc))
        k += 1


# ---- C_01 ----------------------------------------------------------------------------------
def assemble(sc, rnd):
    path, pmat, new = _machine_and_path()
    path.hide_render = True
    bpy.data.objects["Housing"].hide_render = True                  # a section: no outer casing
    parts = [o for o in new if o.type == "MESH" and o.parent is None and o.name != "Housing"]
    for i, o in enumerate(parts):
        home = o.location.copy()
        off = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(0.2, 1))).normalized() * rnd.uniform(3, 6)
        f0 = 30 + 6 * (i % 14)
        _key(o, 1, location=home + off)
        _key(o, f0, location=home + off * 0.9)
        _key(o, f0 + 40, location=home)
    B._area("ClayKey", (5, -6, 9), (0.8, 0, 0.6), 10, 2400, (1.0, 0.98, 0.95))
    B._camera("CamC_01", [(1, (-1.6, 0, 0.4), (9.0, -19.0, 8.0), 30, 8.0), (120, (-2.5, 0, 0.4), (-12.0, -16.0, 5.0), 30, 8.0),
                          (187, (-4.8, 0, 0.0), (-9.5, -5.5, 1.6), 30, 8.0)])


# ---- C_03 / C_04 / C_05 --------------------------------------------------------------------
def ride(sc, rnd):
    path, pmat, new = _machine_and_path()
    # C_03 (1-401): up to the reticle;  C_04 (411-898 -> compressed to 411-898 in sim frames): to the wafer
    _grow(path, [(1, 1 / N), (120, 1 / N + 0.02), (400, 4 / N)])
    _grow(path, [(411, 4 / N), (860, 1.0)])
    _stages_race(560, 900)
    latent = M.emission("LatentLine", (0.8, 0.65, 1.0), 0.0)
    w = Vector(BM.WAFER)
    _box("Latent", tuple(w + Vector((0, 0, 0.03))), (0.5, 0.06, 0.005), latent, role="emitter")
    M.set_emission_strength(latent, 840, 0.0)
    M.set_emission_strength(latent, 880, 3.0)
    off = Vector((0.25, -0.9, 0.3))
    keys3 = [(1, _P(0) + Vector((-0.6, 0, 0)), _P(0) + Vector((0.6, -1.4, 0.5)), 30, 5.6),
             (120, _P(1), _P(1) + Vector((-0.9, -0.8, 0.2)), 30, 5.6),
             (220, _P(2), _P(1) + off, 30, 5.6),
             (300, _P(3), _P(2) + off, 30, 5.6),
             (401, _P(4), _P(3) + off * 1.2, 30, 5.6)]
    B._camera("CamC_03", [(f, tuple(a), tuple(l), lens, fs) for f, a, l, lens, fs in keys3])
    keys4 = [(411, _P(4), _P(3) + off * 1.2, 30, 8.0)]
    f = 411
    for i in range(5, 11):
        f += 60
        keys4.append((f, _P(i + 1), _P(i) + Vector((0.3, -1.1, 0.2)), 30, 8.0))
    keys4 += [(840, w, w + Vector((0.2, -0.9, 0.9)), 35, 8.0), (886, w, w + Vector((0.1, -0.35, 0.45)), 35, 8.0),
              (898, w, w + Vector((0.1, -0.35, 0.45)), 35, 8.0)]
    B._camera("CamC_04", [(f, tuple(a), tuple(l), lens, fs) for f, a, l, lens, fs in keys4])
    # C_05 (911-1054): fast pull-back from the wafer to the whole machine, side view
    B._camera("CamC_05", [(911, w, w + Vector((0.1, -0.35, 0.45)), 35, 11.0), (1020, (-1.6, 0, 0.6), (-1.6, -15.0, 1.2), 35, 11.0),
                          (1054, (-1.6, 0, 0.6), (-1.6, -15.5, 1.2), 35, 11.0)])


# ---- C_06 ----------------------------------------------------------------------------------
def pulses(sc, rnd):
    path, pmat, new = _machine_and_path()
    pmat.node_tree.nodes["Emission"].inputs["Strength"].default_value = 1.2
    cu = path.data.copy()
    pulse = bpy.data.objects.new("Pulse", cu)
    sc.collection.objects.link(pulse)
    pm = M.emission("PulseMat", (0.9, 0.8, 1.0), 20.0)
    pulse.data.materials.clear()
    pulse.data.materials.append(pm)
    pulse.data.bevel_depth = 0.04
    styles.tag(pulse, "rays")
    f = 4
    gap = 26
    while f < 120:
        for v_s, v_e, ff in ((0.0, 0.0, f), (0.0, 0.12, f + 2), (0.88, 1.0, f + max(4, gap - 4)), (1.0, 1.0, f + max(5, gap - 3))):
            pulse.data.bevel_factor_start = v_s
            pulse.data.bevel_factor_end = v_e
            pulse.data.keyframe_insert("bevel_factor_start", frame=ff)
            pulse.data.keyframe_insert("bevel_factor_end", frame=ff)
        f += gap
        gap = max(6, int(gap * 0.78))
    s = pmat.node_tree.nodes["Emission"].inputs["Strength"]
    for fr, v in ((1, 1.2), (100, 1.2), (128, 9.0)):
        s.default_value = v
        s.keyframe_insert("default_value", frame=fr)
    B._camera("CamC_06", [(1, (-1.6, 0, 0.6), (-1.6, -15.5, 1.2), 35, 11.0), (138, (-1.6, 0, 0.6), (-1.6, -15.2, 1.2), 35, 11.0)])


# ---- C_08 / C_09 ---------------------------------------------------------------------------
def accents(sc, rnd):
    path, pmat, new = _machine_and_path()
    _grow(path, [(1, 0.0), (190, 0.0), (232, 1.0)])
    # accent lights in voice-over order: source, mirrors, mask, stages
    src = M.emission("AccSource", ORANGE, 0.0)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.35, location=BM.PLASMA)
    so = bpy.context.object
    so.data.materials.append(src)
    styles.tag(so, "emitter")
    mir = M.emission("AccMirror", (0.75, 0.85, 1.0), 0.0)
    for i, p in enumerate([BM.FACET1, BM.FACET2] + BM.PO_MIRRORS):
        bpy.ops.mesh.primitive_torus_add(major_radius=0.32, minor_radius=0.025, location=p, rotation=(math.pi / 2, 0, 0))
        t = bpy.context.object
        t.data.materials.append(mir)
        styles.tag(t, "emitter")
    msk = A0.circuit_emission("AccMask", (0.95, 0.95, 1.0), 0.0, scale=0.4)
    bpy.ops.mesh.primitive_plane_add(size=0.6, location=(BM.RETICLE[0], 0, BM.RETICLE[2] + 0.09))
    mp = bpy.context.object
    mp.data.materials.append(msk)
    styles.tag(mp, "emitter")
    stg = M.emission("AccStage", CYAN, 0.0)
    for z in (BM.RETICLE[2] + 0.27, -1.35):
        bpy.ops.mesh.primitive_torus_add(major_radius=1.3, minor_radius=0.03, location=(0.5, 0, z))
        t = bpy.context.object
        t.data.materials.append(stg)
        styles.tag(t, "emitter")
    for m, f0 in ((src, 20), (mir, 70), (msk, 115), (stg, 160)):
        M.set_emission_strength(m, f0, 0.0)
        M.set_emission_strength(m, f0 + 10, 8.0 if m is not msk else 3.0)
    # C_09 (241-429): per-module axes jitter, then snap to one origin; a shared grid fades in
    axes_m = M.emission("Axes", CYAN, 4.0)
    centres = [BM.PLASMA, BM.IF, BM.FACET2, BM.RETICLE, (0.5, 0, 0.8), BM.WAFER]
    for i, c0 in enumerate(centres):
        bpy.ops.object.empty_add(location=c0)
        ax = bpy.context.object
        ax.name = f"Axis{i}"
        for d in ((0.5, 0.01, 0.01), (0.01, 0.5, 0.01), (0.01, 0.01, 0.5)):
            b = _box(f"AxisBar{i}{d}", (0, 0, 0), tuple(v * 2 for v in d), axes_m, role="emitter")
            b.parent = ax
            b.location = (d[0] if d[0] > 0.1 else 0, d[1] if d[1] > 0.1 else 0, d[2] if d[2] > 0.1 else 0)
        _key(ax, 1, hide_render=True)
        _key(ax, 241, hide_render=False)
        for f in range(241, 361, 6):
            ax.rotation_euler = Euler((rnd.uniform(-0.6, 0.6), rnd.uniform(-0.6, 0.6), rnd.uniform(-0.6, 0.6)))
            ax.keyframe_insert("rotation_euler", frame=f)
        _key(ax, 372, rotation_euler=(0, 0, 0))
        _key(ax, 400, rotation_euler=(0, 0, 0), location=Vector(c0) * 0.0 + Vector((-1.6, -2.0, 0.35)))
    gm = M.emission("SharedGrid", CYAN, 0.0)
    for i in range(-12, 13):
        for ax_ in ("x", "z"):
            loc = (-1.6 + i * 0.5, 2.0, 0.35) if ax_ == "x" else (-1.6, 2.0, 0.35 + i * 0.5)
            _box(f"G{ax_}{i}", loc, (0.01, 0.01, 12.0) if ax_ == "x" else (12.0, 0.01, 0.01), gm, role="emitter")
    M.set_emission_strength(gm, 395, 0.0)
    M.set_emission_strength(gm, 425, 1.2)
    B._area("MKey", (0, -9, 8), (0.9, 0, 0), 16, 2500, (0.8, 0.85, 1.0))
    B._camera("CamC_08", [(1, (-5.0, 0, 0.4), (-5.5, -6.0, 1.8), 35, 8.0), (70, (-1.6, 0, 1.3), (-2.0, -6.5, 2.2), 35, 8.0),
                          (160, (0.5, 0, 0.8), (0.8, -6.8, 1.8), 35, 8.0), (235, (-1.6, 0, 0.5), (-1.6, -12.0, 2.5), 35, 8.0)])
    B._camera("CamC_09", [(241, (-1.6, 0, 0.5), (-1.6, -12.0, 2.5), 35, 8.0), (429, (-1.6, 0, 0.5), (-1.6, -17.0, 3.5), 35, 8.0)])


# ---- C_10 ----------------------------------------------------------------------------------
def heart(sc, rnd):
    path, pmat, new = _machine_and_path()
    s = pmat.node_tree.nodes["Emission"].inputs["Strength"]
    for f, v in ((1, 6.0), (8, 12.0), (16, 4.0), (30, 12.0), (40, 4.0), (56, 10.0), (80, 0.0)):
        s.default_value = v
        s.keyframe_insert("default_value", frame=f)
    em = M.emission("Ember", VIOLET, 0.0)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.03, location=BM.PLASMA)
    e = bpy.context.object
    e.data.materials.append(em)
    styles.tag(e, "emitter")
    M.set_emission_strength(em, 60, 0.0)
    M.set_emission_strength(em, 80, 30.0)
    B._camera("CamC_10", [(1, (-1.6, 0, 0.6), (-1.6, -15.2, 1.2), 35, 11.0), (96, (-1.6, 0, 0.6), (-1.6, -15.0, 1.2), 35, 11.0)])


def build(variant="ride", seed=31):
    sc = C.reset_scene(1100)
    C.set_world(top=(0.03, 0.035, 0.05), horizon=(0.012, 0.014, 0.02), bottom=(0.003, 0.004, 0.006))
    C.set_color_management(exposure=0.4)
    rnd = random.Random(seed)
    {"assemble": assemble, "ride": ride, "pulses": pulses, "accents": accents, "heart": heart}[variant](sc, rnd)
    return sc
