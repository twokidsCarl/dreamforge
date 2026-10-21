"""B1_04 / B1_05: the tin jet leaving the nozzle, breaking into a "string of pearls" that coalesces into
widely spaced droplets — at the published proportions (1 unit = 125 um, the sample_b1 scale):

- orifice 3-5 um (US9715174 "inner diameter of 3-5 um"): bore radius 2 um = 0.016; the jet is as thick as the bore;
- "Approximately 100 small droplets at an average frequency of 5 MHz ... produce 50 kHz droplets with a 1.5-mm
  droplet-to-droplet spacing" (ASML/Cymer, Fomenkov 2017 p.180): small droplets 27 um / 100^(1/3) = 5.8 um,
  14 um apart at 70 m/s and 5 MHz; final droplets 27 um, 1.4 mm (11.2 units) apart;
- the jet breaks up first and the small droplets coalesce "at some distance away from the nozzle" (US9715174):
  neighbours merge first, so one droplet grows in the middle of each group and sweeps up the rest.
Breakup length, coalescence distance and the nozzle's outer shape are not public (drawn as 示意).

The jet is a mesh tube whose radius profile is rewritten every (sub)frame; the droplets are metaball elements so
merging droplets neck into each other. Both are driven by a frame-change handler, so motion blur sees the motion.
"""
import math

import bmesh
import bpy
from mathutils import Matrix

import build_vacuum as V
import common as C
import materials as M
import sample_b1 as B
import styles

FRAMES = 700
UM = 1 / 125.0                       # units per micrometre
R_BORE = 2.0 * UM                    # 4 um orifice
R_JET = 1.6 * UM                     # 3.2 um jet
R_SMALL = 2.9 * UM                   # 5.8 um small droplet
R_BIG = 13.5 * UM                    # 27 um final droplet
LAM = 14.0 * UM                      # small-droplet spacing (70 m/s / 5 MHz)
GROUP = 100                          # small droplets per final droplet
V_FLOW = LAM / 2.0                   # slow motion: one small droplet every 2 frames
L_BREAK = LAM * 5.25                 # breakup length (not public; ~75 um), on a wave crest
D0, K_MERGE, W_MERGE = 1.2, 1.15, 0.9   # coalescence: member at offset o merges at D = D0 + K|o| .. + W
META_GROW = 1.0 / 0.575              # a lone metaball's surface sits at ~0.575 of its radius (threshold 0.6)
Y_MAX = 30.0
RINGS, SEGS = 160, 20


def _smooth(x, a, b):
    t = min(1.0, max(0.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


def _jet_radius(y, f):
    """Radius of the continuous jet at distance y from the orifice: a Rayleigh wave that grows until it pinches."""
    amp = 0.95 * _smooth(y, 0.0, L_BREAK) ** 1.5
    r = R_JET * (1.0 + amp * math.sin(2 * math.pi * (y - V_FLOW * f) / LAM))
    if y > L_BREAK - LAM / 2:                                         # the last half wave closes onto the droplet
        r *= max(0.0, 1.0 - (y - (L_BREAK - LAM / 2)) / (LAM / 2)) ** 0.5
    return max(r, 0.0)


def _droplets(f):
    """(y, visible radius) of every drop beyond the breakup point at frame f."""
    t_s = LAM / V_FLOW                                                # frames between small droplets
    n_born = int((f * V_FLOW) // LAM)                                 # small droplets past the breakup point
    out = []
    g_first = max(0, int((n_born - Y_MAX / LAM) // GROUP) - 1)
    for g in range(g_first, n_born // GROUP + 1):
        yc = L_BREAK + V_FLOW * (f - (g * GROUP + (GROUP - 1) / 2) * t_s)    # group centre
        if yc > Y_MAX:
            continue
        absorbed = 0
        for m in range(GROUP):
            i = g * GROUP + m
            if i >= n_born:
                break
            off = ((GROUP - 1) / 2 - m) * LAM
            s = _smooth(yc, D0 + K_MERGE * abs(off), D0 + K_MERGE * abs(off) + W_MERGE)
            if s >= 1.0:
                absorbed += 1
                continue
            out.append((yc + off * (1 - s), R_SMALL))
        if absorbed:
            out.append((yc, R_SMALL * (1 + absorbed) ** (1 / 3)))       # volume conserved
    return out


def _update(scene, depsgraph=None):
    f = scene.frame_current + scene.frame_subframe
    me = bpy.data.meshes.get("TinJetTube")
    if me is not None:
        co = []
        for k in range(RINGS):
            y = L_BREAK * k / (RINGS - 1)
            r = _jet_radius(y, f)
            for j in range(SEGS):
                a = 2 * math.pi * j / SEGS
                co += [r * math.cos(a), y, r * math.sin(a)]
        co += [0.0, -0.002, 0.0, 0.0, L_BREAK, 0.0]
        me.vertices.foreach_set("co", co)
        me.update()
    mb = bpy.data.metaballs.get("TinDrops")
    if mb is None:
        return
    drops = _droplets(f)
    for idx, e in enumerate(mb.elements):
        if idx < len(drops):
            y, r = drops[idx]
            e.co = (0.0, y, 0.0)
            e.radius = r * META_GROW
            e.hide = False
        else:
            e.hide = True


def _jet_mesh(sc):
    me = bpy.data.meshes.new("TinJetTube")
    verts = [(0.0, 0.0, 0.0)] * (RINGS * SEGS) + [(0, 0, 0), (0, 0, 0)]
    faces = []
    for k in range(RINGS - 1):
        for j in range(SEGS):
            a, b = k * SEGS + j, k * SEGS + (j + 1) % SEGS
            faces.append((a, b, b + SEGS, a + SEGS))
    c0, c1 = RINGS * SEGS, RINGS * SEGS + 1
    for j in range(SEGS):                                             # caps: inside the bore and at the pinch
        faces.append((c0, (j + 1) % SEGS, j))
        faces.append((c1, (RINGS - 1) * SEGS + j, (RINGS - 1) * SEGS + (j + 1) % SEGS))
    me.from_pydata(verts, [], faces)
    me.polygons.foreach_set("use_smooth", [True] * len(faces))
    ob = bpy.data.objects.new("TinJet", me)
    sc.collection.objects.link(ob)
    return ob


def nozzle():
    """Nozzle tip pointing +Y with its face at y = 0: a tapered steel tip (outer shape 示意), a flat matte end face
    30 um across and a 4 um dark orifice — the bore is several times smaller than the droplet it makes."""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=False, segments=96, radius1=0.9, radius2=0.12, depth=2.4)
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(-math.pi / 2, 3, "X"))
    bmesh.ops.translate(bm, verts=bm.verts, vec=(0, -1.2, 0))
    me = bpy.data.meshes.new("NozzleTip")
    bm.to_mesh(me)
    me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
    tip = bpy.data.objects.new("NozzleTip", me)
    bpy.context.scene.collection.objects.link(tip)
    tip.data.materials.append(M.polished_steel("NozzleSteel", 0.14))
    styles.tag(tip, "structure")
    face = M.principled("NozzleFace", (0.5, 0.52, 0.55), metallic=1.0, roughness=0.5)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.12, depth=0.004, vertices=96, location=(0, -0.002, 0),
                                        rotation=(math.pi / 2, 0, 0))
    fc = bpy.context.object
    fc.name = "NozzleFace"
    fc.data.materials.append(face)
    styles.tag(fc, "structure")
    bpy.ops.mesh.primitive_cylinder_add(radius=R_BORE, depth=0.004, vertices=32, location=(0, -0.0015, 0),
                                        rotation=(math.pi / 2, 0, 0))
    bore = bpy.context.object
    bore.name = "Orifice"
    bore.data.materials.append(M.principled("OrificeDark", (0.0, 0.0, 0.0), roughness=1.0))
    styles.tag(bore, "structure")
    bpy.ops.mesh.primitive_cylinder_add(radius=1.6, depth=6.0, vertices=96, location=(0, -2.4 - 3.0, 0),
                                        rotation=(math.pi / 2, 0, 0))
    body = bpy.context.object
    body.name = "NozzleBody"
    body.data.materials.append(M.dark_anodized("NozzleBody"))
    styles.tag(body, "structure")
    return tip


def build():
    sc = C.reset_scene(FRAMES)
    C.set_world(top=(0.012, 0.016, 0.026), horizon=(0.006, 0.008, 0.014), bottom=(0.002, 0.003, 0.005))
    C.set_color_management(exposure=0.55)
    V.chamber()
    tip = nozzle()
    jet = _jet_mesh(sc)
    mb = bpy.data.metaballs.new("TinDrops")
    mb.resolution = 0.01
    mb.render_resolution = 0.0025
    mb.threshold = 0.6
    for _ in range(int(Y_MAX / LAM) + 60):
        e = mb.elements.new()
        e.radius = R_SMALL * META_GROW
        e.hide = True
    drops = bpy.data.objects.new("TinDrops", mb)
    sc.collection.objects.link(drops)
    tin = M.tin("TinJetMat", roughness=0.05)
    for ob in (jet, drops):
        ob.data.materials.append(tin)
        styles.tag(ob, "structure")
    B._lights([jet, drops, tip])
    bpy.app.handlers.frame_change_pre.append(_update)
    # B1_04: nozzle macro, slow push; only the hair-thin jet and the first small droplets are in frame
    B._camera("CamB1_04", [(300, (0, 0.34, 0), (1.05, -0.2, 0.36), 50, 8.0),     # frame ~140 um wide
                           (520, (0, 0.32, 0), (0.85, -0.1, 0.29), 50, 8.0)])
    # B1_05: ride along with one group (g = 2) at the flow speed, centred on the drop that grows in its middle, so
    # the small droplets stream in from both sides and merge; then pull back to two final droplets 1.4 mm apart
    def yc(f, g=2):
        return L_BREAK + V_FLOW * (f - (g * GROUP + (GROUP - 1) / 2) * LAM / V_FLOW)
    keys = [(498, 0.7), (575, 1.2), (640, 2.0), (692, 3.4)]          # frame, picture width (units)
    cam_keys = [(f, (0, yc(f), 0), (w * 85 / 36 * 0.97, yc(f) - w * 0.12, w * 0.22), 85, 4.0) for f, w in keys]
    # (B1_07 shows the 1.4 mm spacing; at that width a 27 um droplet is a dot, so this shot ends on the merged drop)
    cam = B._camera("CamB1_05", cam_keys)
    for ob in (cam, bpy.data.objects["CamB1_05Aim"]):
        for fc in C.fcurves(ob.animation_data.action):
            for kp in fc.keyframe_points[:3]:
                kp.interpolation = "LINEAR"                   # match the flow exactly while riding along
    _update(sc)
    return sc
