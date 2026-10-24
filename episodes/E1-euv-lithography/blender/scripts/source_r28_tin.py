"""Round 28 tin helpers (R28_ROOT_CAUSE row 1, material tin step 2). Used only by source_r28.py.

  reflections   REFL_R28: dark chamber env + DISCRETE nameable bright sources seen only by rays leaving the tin.
                sheet: real emitter geometry (2x2-pane viewport window, flange ring, violet plasma blob, cool window
                strip) placed around the face's mirror direction inside a dark env sphere; droplets: env-sphere bands
                swapped for dark base + round viewport + flange ring + violet point + thin back rim.
  breakup       BREAK_R28: sheet thickness undulation, 3 rim holes, radial ligaments with beads, random satellites.
  pulse2        PULSE2_R28: main pulse = thin soft converging beam lit at the landing (+ landing glow).
"""
import math
import random

import bpy
from mathutils import Vector

import kit_r2 as K

DARK = (0.010, 0.011, 0.015)          # chamber between the sources: dark, not pure black (R24)
WHITE = (1.0, 0.98, 0.95)
COOL = (0.80, 0.88, 1.0)
WARM = (1.0, 0.86, 0.66)
VIOLET = (0.62, 0.42, 1.0)
SHEET_FRAME = {"A0_01": 160, "B1_10": 69}
DROP_FRAME = {"A0_01": 72, "B1_10": 69, "B1_08": 51}
SHEET_ENV_R = 0.46
DROP_BASE = (0.05, 0.053, 0.062)       # droplet chamber base (R27 level, never black)
SHEET_BASE = (0.045, 0.050, 0.064)    # sheet: dim lit chamber between the sources (silver, not black)
SRC_D = 0.27                          # sources this far from the sheet centre along its mirror direction
RIG = {"A0_01": dict(d=0.27, k=1.0, base=(0.060, 0.065, 0.080), top=0.30, und=0.025),
       "B1_10": dict(d=0.36, k=0.75, base=(0.060, 0.065, 0.080), top=0.30, und=0.012)}   # B1_10: cupped face magnifies
WIN_GAIN = 5.0
RING_GAIN = 6.0
VIOLET_GAIN = 5.0
STRIP_GAIN = 3.5
LIQUID_WOBBLE = 0.08                  # R27 0.12: halved so the window / ring images stay nameable


def _ob(n):
    return bpy.data.objects.get(n)


def _n(v):
    return tuple(Vector(v).normalized())


# ------------------------------------------------------------------ emitters seen only by rays leaving the tin
def _glossy_only_mat(name, rgb, strength, centre, radius):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for nd in list(nt.nodes):
        if nd.type != "OUTPUT_MATERIAL":
            nt.nodes.remove(nd)
    out = next(nd for nd in nt.nodes if nd.type == "OUTPUT_MATERIAL")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*rgb, 1)
    em.inputs["Strength"].default_value = strength
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    lp = nt.nodes.new("ShaderNodeLightPath")
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    inc = nt.nodes.new("ShaderNodeVectorMath")
    inc.operation = "SCALE"
    nt.links.new(geo.outputs["Incoming"], inc.inputs[0])
    nt.links.new(lp.outputs["Ray Length"], inc.inputs["Scale"])
    org = nt.nodes.new("ShaderNodeVectorMath")
    org.operation = "ADD"
    nt.links.new(geo.outputs["Position"], org.inputs[0])
    nt.links.new(inc.outputs[0], org.inputs[1])
    dv = nt.nodes.new("ShaderNodeVectorMath")
    dv.operation = "DISTANCE"
    nt.links.new(org.outputs[0], dv.inputs[0])
    dv.inputs[1].default_value = tuple(centre)
    ins = nt.nodes.new("ShaderNodeMath")
    ins.operation = "LESS_THAN"
    nt.links.new(dv.outputs["Value"], ins.inputs[0])
    ins.inputs[1].default_value = radius
    ntr = nt.nodes.new("ShaderNodeMath")
    ntr.operation = "LESS_THAN"
    nt.links.new(lp.outputs["Is Transmission Ray"], ntr.inputs[0])
    ntr.inputs[1].default_value = 0.5
    a = nt.nodes.new("ShaderNodeMath")
    a.operation = "MULTIPLY"
    nt.links.new(lp.outputs["Is Glossy Ray"], a.inputs[0])
    nt.links.new(ins.outputs[0], a.inputs[1])
    b = nt.nodes.new("ShaderNodeMath")
    b.operation = "MULTIPLY"
    nt.links.new(a.outputs[0], b.inputs[0])
    nt.links.new(ntr.outputs[0], b.inputs[1])
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(b.outputs[0], mix.inputs[0])
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(em.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])
    return m


def _hide_from_all_but_glossy(ob):
    for attr in ("visible_camera", "visible_diffuse", "visible_shadow", "visible_transmission",
                 "visible_volume_scatter"):
        setattr(ob, attr, False)


def _quad(mb, c, u, v, hu, hv, nrm):
    V = mb.bm.verts.new
    c = Vector(c)
    pts = [V(c + u * su * hu + v * sv * hv) for su, sv in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    f = mb.bm.faces.new(pts)
    f.normal_update()
    if f.normal.dot(nrm) < 0:
        f.normal_flip()


def sheet_rig(sc, shot):
    import source_r24 as H24
    import source_r25_tin as T25
    root = _ob("PancakeRoot")
    if root is None:
        return
    f = SHEET_FRAME[shot]
    tc, rt, up = H24._cam_dirs(sc, f, (0, 0, 0))
    yaw = root.rotation_euler.z
    nrm = Vector((math.cos(yaw), math.sin(yaw), 0))
    if nrm.dot(tc) < 0:
        nrm = -nrm
    v_ = -tc
    md = (v_ - 2 * v_.dot(nrm) * nrm).normalized()
    u = md.cross(Vector((0, 0, 1))).normalized()
    v = u.cross(md).normalized()
    if v.z < 0:
        v = -v
    # flip u so that +u is screen-right in the mirror image (mirror flips left/right)
    P = RIG[shot]
    k = P["k"]
    c0 = md * P["d"]
    face = -md                                   # emitters face back toward the sheet
    for o in list(bpy.data.objects):
        if o.name.startswith(("TinSheetEnvR27", "TinSheetEnvR25")):
            bpy.data.objects.remove(o, do_unlink=True)
    env = T25.env_r25("TinSheetEnvR28", (0, 0, 0), SHEET_ENV_R,
                      [((0, 0, 1), 1.0, 1.3, P["top"], COOL)], base=P["base"])    # dark chamber, faintly lighter above
    env["r28"] = 1
    R = SHEET_ENV_R * 0.85
    # 1 viewport window: 2x2 panes with a dark mullion cross
    mb = K.MB()
    wc = c0 + (u * (-0.015) + v * 0.045) * k
    pw, ph, gap = 0.024 * k, 0.030 * k, 0.006 * k
    for su in (-1, 1):                # two tall panes, one mullion (a 2x2 grid read as a 'Windows logo')
        _quad(mb, wc + u * su * (pw + gap), u, v, pw, ph * 2.0, face)
    win = mb.obj("TinReflWindowR28", _glossy_only_mat("TinReflWindowR28Mat", WHITE, WIN_GAIN, (0, 0, 0), R))
    # 2 flange ring (warm, below-right)
    mb = K.MB()
    rc = c0 + (u * 0.070 + v * 0.110) * k         # above-left of the window: nothing curved below it (no 'smiley')
    rr, n = 0.032 * k, 40
    pts = [rc + (u * math.cos(2 * math.pi * i / n) + v * math.sin(2 * math.pi * i / n)) * rr for i in range(n)]
    for i in range(n):
        mb.tube(tuple(pts[i]), tuple(pts[(i + 1) % n]), 0.0055, seg=8)
    ring = mb.obj("TinReflFlangeR28", _glossy_only_mat("TinReflFlangeR28Mat", WARM, RING_GAIN, (0, 0, 0), R))
    # 3 violet plasma blob (previous droplet's plasma)
    mb = K.MB()
    mb.sphere(tuple(c0 + (u * 0.060 + v * (-0.055)) * k), 0.020 * k, 24)
    vio = mb.obj("TinReflPlasmaR28", _glossy_only_mat("TinReflPlasmaR28Mat", VIOLET, VIOLET_GAIN, (0, 0, 0), R))
    # 4 cool window strip (vertical slot)
    mb = K.MB()
    _quad(mb, c0 + (u * (-0.072) + v * (-0.06)) * k, u, v, 0.006 * k, 0.06 * k, face)
    strip = mb.obj("TinReflStripR28", _glossy_only_mat("TinReflStripR28Mat", COOL, STRIP_GAIN, (0, 0, 0), R))
    for o in (win, ring, vio, strip):
        _hide_from_all_but_glossy(o)
        o["r28"] = 1
    print("R28TIN sheet rig f%d mdir (%.2f %.2f %.2f)" % (f, *md))


def drop_bands(tc, rt, up):
    tc, rt, up = Vector(tc), Vector(rt), Vector(up)
    return [((0, 0, 1), 1.0, 1.25, 0.40, COOL),                                      # lit chamber top (no hard horizon)
            (_n(tc + up * 1.0 - rt * 0.55), 1.0, 0.035, 6.0, WHITE),                 # round viewport (key)
            (_n(tc + up * 0.25 + rt * 0.85), math.cos(math.radians(16)), 0.012, 3.0, WARM),   # flange ring
            (_n(tc * 0.9 - up * 0.45 + rt * 0.55), 1.0, 0.006, 12.0, VIOLET),        # violet plasma point
            (_n(-tc + up * 0.35), 1.0, 0.40, 1.6, COOL)]                             # back window -> rim


def drop_rigs(sc, shot):
    import source_r24 as H24
    import source_r23_tin as T23
    f = DROP_FRAME[shot]
    for e in list(bpy.data.objects):
        if not e.name.startswith("TinEnvR27_"):
            continue
        d = e.parent
        if d is None:
            continue
        tc, rt, up = H24._cam_dirs(sc, f, d.matrix_world.translation.copy())
        r = max(e.dimensions) * 0.5 / max(1e-6, max(e.scale)) if e.dimensions.length > 0 else 0.05
        m = T23._env_mat_r23("TinEnvR28Mat_" + d.name, drop_bands(tc, rt, up), DROP_BASE, 1.0, 0.05)
        e.data.materials.clear()
        e.data.materials.append(m)


def reflections(sc, shot):
    if shot in SHEET_FRAME:
        sheet_rig(sc, shot)
        sh = _ob("Pancake")
        if sh is not None and sh.active_material is not None:
            for nd in sh.active_material.node_tree.nodes:
                if nd.type == "BUMP":
                    nd.inputs["Strength"].default_value = LIQUID_WOBBLE
    drop_rigs(sc, shot)


# ------------------------------------------------------------------ BREAK_R28 sheet geometry
HOLES = [(0.95, 0.84, 0.13), (2.75, 0.80, 0.10), (4.55, 0.86, 0.115)]   # (angle rad, rho, radius) unit sheet
UND_A, THK_A = 0.025, 0.55


def _rim(root, a):
    rr = root.get("r24_rim")
    if not rr:
        return 1.0
    rr = list(rr)
    n = len(rr)
    x = (a % (2 * math.pi)) / (2 * math.pi) * n
    i = int(x) % n
    t = x - int(x)
    return rr[i] * (1 - t) + rr[(i + 1) % n] * t


def breakup(shot):
    import bmesh
    root = _ob("PancakeRoot")
    sh = _ob("Pancake")
    if root is None or sh is None:
        return
    rnd = random.Random(2800 + len(shot))
    bm = bmesh.new()
    bm.from_mesh(sh.data)
    # low-frequency undulation (sheet bends) + thickness variation (thin / thick patches)
    for vt in bm.verts:
        x, y, z = vt.co
        und = RIG[shot]["und"] * (math.sin(2.1 * y + 0.7) * math.cos(1.6 * z - 0.3) + 0.6 * math.sin(2.9 * (y - 0.6 * z) + 1.9))
        thk = 1.0 + THK_A * math.sin(2.6 * y - 1.2) * math.sin(2.2 * z + 0.8)
        vt.co.x = x * thk + und
    # 3 local holes near the rim
    kill = []
    for f in bm.faces:
        c = f.calc_center_median()
        for a, rho, hr in HOLES:
            hy, hz = rho * math.cos(a), rho * math.sin(a)
            if (c.y - hy) ** 2 + (c.z - hz) ** 2 < hr * hr:
                kill.append(f)
                break
    bmesh.ops.delete(bm, geom=kill, context="FACES_ONLY")
    bm.to_mesh(sh.data)
    bm.free()
    sh.data.update()
    # radial ligaments with beads + random satellites (replace the evenly spaced R24 ring)
    mat = sh.active_material
    mb = K.MB()
    angs = sorted(rnd.uniform(0, 2 * math.pi) for _ in range(8))
    for a in angs:                       # tapered liquid fingers torn out of the rim; the drop pinching off
        r0 = _rim(root, a) * 0.96            # is DETACHED (gap) - no bead on the tip (R17-R19 ball-head pin)
        L = rnd.uniform(0.12, 0.30)
        w = rnd.uniform(0.026, 0.036)
        bend = rnd.uniform(-0.07, 0.07)
        x1 = rnd.uniform(-0.025, 0.025)
        p0 = Vector((0.0, r0 * math.cos(a), r0 * math.sin(a)))
        pm = Vector((x1 * 0.5, (r0 + L * 0.5) * math.cos(a + bend * 0.5), (r0 + L * 0.5) * math.sin(a + bend * 0.5)))
        p1 = Vector((x1, (r0 + L) * math.cos(a + bend), (r0 + L) * math.sin(a + bend)))
        mb.tube(tuple(p0), tuple(pm), w, seg=12, r2=w * 0.6)
        mb.tube(tuple(pm), tuple(p1), w * 0.6, seg=12, r2=w * 0.3)
        mb.sphere(tuple(pm), w * 0.6, 12)
        mb.sphere(tuple(p1), w * 0.3, 8)
        if rnd.random() < 0.6:
            rd = w * rnd.uniform(0.6, 1.1)
            g = rnd.uniform(0.04, 0.09) + rd
            mb.sphere((x1, (r0 + L + g) * math.cos(a + bend), (r0 + L + g) * math.sin(a + bend)), rd, 14)
    lig = mb.obj("PancakeLigR28", mat)
    for p in lig.data.polygons:
        p.use_smooth = True
    lig.parent = root
    drops = _ob("PancakeDrops")
    mb = K.MB()
    for _ in range(15):
        a = rnd.uniform(0, 2 * math.pi)
        rad = math.exp(rnd.uniform(math.log(0.016), math.log(0.065)))
        rho = _rim(root, a) + rnd.uniform(0.06, 0.62) + rad
        mb.sphere((rnd.uniform(-0.06, 0.06), rho * math.cos(a), rho * math.sin(a)), rad, 16)
    tmp = mb.obj("PancakeDropsR28tmp", mat)
    if drops is not None:
        old = drops.data
        drops.data = tmp.data
        for p in drops.data.polygons:
            p.use_smooth = True
        bpy.data.objects.remove(tmp, do_unlink=True)
        if old.users == 0:
            bpy.data.meshes.remove(old)
        src = drops
    else:
        tmp.parent = root
        src = tmp
    # ligaments share the satellites' visibility keys
    import source_r26_tin as T26
    keys = sorted((kp.co[0], kp.co[1]) for fc in T26._fcs(src) if fc.data_path == "hide_render"
                  for kp in fc.keyframe_points)
    for f, h in keys:
        lig.hide_render = bool(h > 0.5)
        lig.keyframe_insert("hide_render", frame=int(f))
    for fc in T26._fcs(lig):
        for kp in fc.keyframe_points:
            kp.interpolation = "CONSTANT"
    # glint light-linking receivers (R17): add the ligaments
    for col in bpy.data.collections:
        if col.name.startswith("PancakeGlintR17_Recv") and src.name in col.objects:
            col.objects.link(lig)


# ------------------------------------------------------------------ PULSE2_R28 main pulse
P2_R0, P2_R1, P2_PEAK, P2_GAIN = 0.10, 0.012, 300.0, 1.0


def pulse2(sc):
    import sys
    import source_r19 as S19
    mod = sys.modules.get("r2_source")
    old = _ob("MainPulse")
    if mod is None or old is None:
        return
    import source_r26_tin as T26
    hide = sorted((kp.co[0], kp.co[1]) for fc in T26._fcs(old) if fc.data_path == "hide_render"
                  for kp in fc.keyframe_points)
    shown = sorted(f for f, h in hide if h < 0.5)
    gone = sorted(f for f, h in hide if h > 0.5 and shown and f > shown[0])
    bpy.data.objects.remove(old, do_unlink=True)
    mp = S19.laser_cone_r19((mod.COLL_X - 0.2, 0, 0), (-0.012, 0, 0), P2_R0, P2_R1, "MainPulse",
                            peak=P2_PEAK, gain=P2_GAIN)
    if shown:
        mod.show_between(mp, int(shown[0]), int(gone[0]) - 1 if gone else None)
