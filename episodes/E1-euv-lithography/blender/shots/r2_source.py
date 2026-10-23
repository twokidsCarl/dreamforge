"""P1 round 2 source-chamber shots (Carl pick 3A+D): a dense metal vacuum vessel seen from inside, liquid-tin
droplets, orange CO2 laser pulses (orange = laser only), a violet-white plasma; plus the CO2 amplifier chain.
The microscopic mechanism (ions, hydrogen chemistry, spectrum) lives in 2D magnifier overlays
(mograph/r2_ov_source.py), not in this scene.

variants (registry args: {variant: ..., shot: ...}); camera "CamR2" in every variant:
  cold     A0_01  droplet -> pre-pulse -> pancake -> main pulse -> plasma
  prepulse B1_10  thin orange pre-pulse flattens a droplet into a ~300 um pancake; next droplet for scale
  contrast B1_15  plasma on one side, the collector mirror surface on the other; hot tin debris
  track    B1_08  a stream of droplets, each with its own cyan reticle
  clean    B2_08  collector surface with tin deposits under a violet glow (chemistry in the overlay)
  spectrum B1_18  soft, defocused plasma / chamber plate under the spectrum HUD overlay
  amps     B1_22  seed laser + four amplifier modules, the orange beam growing stage by stage

Scene units: metres, plasma site at the origin, laser arrives along +X through the collector hole.
"""
import math
import random

import bpy
from mathutils import Vector

import common as C
import kit_r2 as K

CHAMBER_R = 1.3
COLL_X = -0.9          # collector vertex (dish opens towards +X)
COLL_R = 0.68
COLL_F = 0.45


# ---------------------------------------------------------------- animation helpers
def _const(ob):
    ad = ob.animation_data
    if ad and ad.action:
        for fc in C.fcurves(ad.action):
            for k in fc.keyframe_points:
                k.interpolation = "CONSTANT"


def show_between(ob, a, b=None):
    """Visible (render) only for frames a..b (b None = to the end)."""
    ob.hide_render = True
    ob.keyframe_insert("hide_render", frame=min(0, a - 1))
    if a > 1:
        ob.keyframe_insert("hide_render", frame=a - 1)
    ob.hide_render = False
    ob.keyframe_insert("hide_render", frame=a)
    if b is not None:
        ob.hide_render = True
        ob.keyframe_insert("hide_render", frame=b + 1)
    _const(ob)


def key_energy(light, keys):
    for f, e in keys:
        light.data.energy = e
        light.data.keyframe_insert("energy", frame=f)


def key_scale(ob, keys, interp="BEZIER"):
    for f, s in keys:
        ob.scale = (s, s, s) if isinstance(s, (int, float)) else s
        ob.keyframe_insert("scale", frame=f)
    for fc in C.fcurves(ob.animation_data.action):
        for k in fc.keyframe_points:
            k.interpolation = interp


def key_loc(ob, keys, interp="LINEAR"):
    for f, p in keys:
        ob.location = p
        ob.keyframe_insert("location", frame=f)
    for fc in C.fcurves(ob.animation_data.action):
        for k in fc.keyframe_points:
            k.interpolation = interp


def single(name, material, fn):
    mb = K.MB()
    fn(mb)
    return mb.obj(name, material)


# ---------------------------------------------------------------- materials
def vol_glow(name, color, strength, density=0.0):
    """Emissive volume: a sphere of it reads as a soft glow that is brightest through the middle."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for nd in list(nt.nodes):
        if nd.type != "OUTPUT_MATERIAL":
            nt.nodes.remove(nd)
    out = next(nd for nd in nt.nodes if nd.type == "OUTPUT_MATERIAL")
    v = nt.nodes.new("ShaderNodeVolumePrincipled")
    v.inputs["Density"].default_value = density
    v.inputs["Emission Color"].default_value = (*K.lin(color), 1)
    v.inputs["Emission Strength"].default_value = strength
    nt.links.new(v.outputs[0], out.inputs["Volume"])
    return m


def _mats():
    M = K.palette()
    M["tin"] = K.mat("LiquidTin", (0.9, 0.9, 0.92), metal=1.0, rough=0.14)
    M["tin_dep"] = K.mat("TinDeposit", (0.55, 0.56, 0.58), metal=1.0, rough=0.45, speck=0.4)
    M["coll"] = K.mat("CollectorML", (0.36, 0.34, 0.44), metal=1.0, rough=0.04, coat=0.5)
    M["chamber"] = K.mat("ChamberSteel", (0.3, 0.32, 0.36), metal=1.0, rough=0.34, brushed=0.12)
    M["hole"] = K.mat("PortHole", (0.01, 0.012, 0.018), rough=0.9)
    M["window"] = K.emit_mat("WindowGlow", (0.25, 0.4, 0.75), 0.6)
    M["plasma_core"] = K.emit_mat("PlasmaCore", (0.93, 0.88, 1.0), 8.0)
    M["plasma_halo"] = vol_glow("PlasmaHalo", (0.72, 0.6, 1.0), 9.0)
    M["plasma_haze"] = vol_glow("PlasmaHaze", K.VIOLET, 0.9)
    M["flash"] = K.emit_mat("LaserFlash", (1.0, 0.8, 0.55), 8.0)
    M["flash_halo"] = vol_glow("LaserFlashHalo", K.ORANGE, 10.0)
    M["hot"] = K.emit_mat("DebrisHot", (1.0, 0.92, 0.78), 25.0)
    M["warm"] = K.emit_mat("DebrisWarm", (1.0, 0.45, 0.18), 6.0)
    M["cool"] = K.emit_mat("DebrisCool", (0.55, 0.08, 0.04), 2.0)
    M["reticle"] = K.emit_mat("Reticle", K.CYAN, 9.0)
    M["reticle_lock"] = K.emit_mat("ReticleLock", K.CYAN, 18.0)
    return M


# ---------------------------------------------------------------- the vessel seen from inside
def chamber(M, seed=0, collector=True, nozzle=True):
    rnd = random.Random(seed)
    w, fl, bolt, dk = K.MB(), K.MB(), K.MB(), K.MB()
    hole, win, anod, pipe, gold = K.MB(), K.MB(), K.MB(), K.MB(), K.MB()
    w.shell((0, 0, 0), CHAMBER_R, CHAMBER_R + 0.06, 3.0, 0, 360, seg=96)
    w.cyl((0, 0, 1.53), CHAMBER_R + 0.06, 0.06, seg=96)
    w.cyl((0, 0, -1.53), CHAMBER_R + 0.06, 0.06, seg=96)
    # stiffening rings and vertical ribs on the inside face
    for z in (-1.1, -0.55, 0.62, 1.15):
        fl.ring((0, 0, z), CHAMBER_R - 0.0, CHAMBER_R - 0.05, 0.05, seg=96)
        bolt.bolts((0, 0, z + 0.03), CHAMBER_R - 0.025, 64, 0.006, 0.012)
    for k in range(24):
        a = 2 * math.pi * k / 24
        fl.box((math.cos(a) * (CHAMBER_R - 0.02), math.sin(a) * (CHAMBER_R - 0.02), 0), (0.03, 0.03, 2.9),
               rot=(0, 0, a))
    # ports: dark bores with an inward flange ring and bolt circle; some carry view windows or diagnostics
    ports = []
    for k in range(26):
        a = rnd.uniform(0, 2 * math.pi)
        z = rnd.uniform(-1.1, 1.1)
        r = rnd.choice((0.05, 0.07, 0.09, 0.12, 0.16))
        n = Vector((-math.cos(a), -math.sin(a), 0))                 # inward normal
        p = Vector((math.cos(a), math.sin(a), 0)) * (CHAMBER_R - 0.01) + Vector((0, 0, z))
        if any((p - q).length < r + rr + 0.05 for q, rr in ports):
            continue
        ports.append((p, r))
        q = Vector((0, 0, 1)).rotation_difference(n).to_euler()
        fl.ring(p + n * 0.02, r * 1.55, r, 0.04, rot=q, seg=40)
        bolt.bolts(p + n * 0.045, r * 1.3, 8 if r < 0.1 else 12, 0.008, 0.012, rot=q)
        (win if k % 4 == 0 else hole).cyl(p + n * 0.005, r * 0.98, 0.01, rot=q, seg=32)
        if k % 5 == 2:                                               # diagnostic camera pointing at the plasma
            body = p + n * 0.16
            anod.box(body, (0.1, 0.1, 0.16), rot=q)
            anod.tube(body + n * 0.08, body + n * 0.16, 0.035, seg=20)
            dk.cyl(body + n * 0.165, 0.028, 0.005, rot=q, seg=20)
        if k % 6 == 3:                                               # gas inlet tube
            pipe.path([p + n * 0.02, p + n * 0.25, p + n * 0.3 + Vector((0, 0, -0.1))], 0.012, seg=10)
    # cables / coolant lines along the wall
    for k in range(6):
        a0 = rnd.uniform(0, 2 * math.pi)
        pts = []
        for i in range(9):
            a = a0 + i * 0.12
            pts.append(Vector((math.cos(a), math.sin(a), 0)) * (CHAMBER_R - 0.09 - 0.012 * k)
                       + Vector((0, 0, -1.2 + i * 0.3)))
        pipe.path(pts, 0.01 + 0.004 * (k % 3), seg=10)
    # heat shields / MLI patches
    for _ in range(14):
        a = rnd.uniform(0, 2 * math.pi)
        z = rnd.uniform(-1.2, 1.2)
        p = Vector((math.cos(a), math.sin(a), 0)) * (CHAMBER_R - 0.035) + Vector((0, 0, z))
        gold.box(p, (0.02, rnd.uniform(0.1, 0.3), rnd.uniform(0.1, 0.25)), rot=(0, 0, a))
    objs = [w.obj("VesselWallR2", M["chamber"], bevel=0.004), fl.obj("ChamberRings", M["alu"]),
            bolt.obj("ChamberBolts", M["steel"]), dk.obj("Lenses", M["glass"]), hole.obj("PortBores", M["hole"]),
            win.obj("PortWindows", M["window"]), anod.obj("Diagnostics", M["anod"], bevel=0.004),
            pipe.obj("WallLines", M["steel"]), gold.obj("MLI", M["gold"])]
    if nozzle:
        nz = K.MB()
        nz.tube((0, 0, 1.5), (0, 0, 0.62), 0.06, seg=32)
        nz.tube((0, 0, 0.62), (0, 0, 0.42), 0.06, seg=32, r2=0.012)
        nz.ring((0, 0, 0.9), 0.12, 0.06, 0.03)
        nz.ring((0, 0, 1.2), 0.16, 0.06, 0.04)
        nz.bolts((0, 0, 1.225), 0.13, 8, 0.008, 0.015)
        for k in range(3):
            nz.box((0.09 * math.cos(k * 2.1), 0.09 * math.sin(k * 2.1), 1.0), (0.04, 0.04, 0.4))
        nz.tube((0, 0, -1.5), (0, 0, -0.55), 0.09, seg=32)
        nz.tube((0, 0, -0.55), (0, 0, -0.45), 0.09, seg=32, r2=0.16)
        nz.ring((0, 0, -0.8), 0.18, 0.09, 0.04)
        objs.append(nz.obj("NozzleCatcher", M["steel"], bevel=0.003))
    if collector:
        objs += collector_mirror(M)
    return objs


def coll_x(r):
    return COLL_X + r * r / (4 * COLL_F)


def collector_mirror(M, hole_r=0.09):
    mb = K.MB()
    nr, na = 22, 96
    rows = []
    for i in range(nr + 1):
        r = hole_r + (COLL_R - hole_r) * i / nr
        rows.append([mb.bm.verts.new((coll_x(r), r * math.cos(2 * math.pi * j / na), r * math.sin(2 * math.pi * j / na)))
                     for j in range(na)])
    for i in range(nr):
        for j in range(na):
            k = (j + 1) % na
            f = mb.bm.faces.new((rows[i][j], rows[i][k], rows[i + 1][k], rows[i + 1][j]))
            f.smooth = True
    mirror = mb.obj("Collector", M["coll"])
    rot = (0, math.radians(90), 0)
    rim = K.MB()
    rim.ring((coll_x(COLL_R) - 0.01, 0, 0), COLL_R + 0.07, COLL_R - 0.01, 0.06, rot=rot, seg=96)
    rim.bolts((coll_x(COLL_R) + 0.025, 0, 0), COLL_R + 0.035, 36, 0.009, 0.02, rot=rot)
    rim.ring((COLL_X + 0.01, 0, 0), hole_r + 0.03, hole_r, 0.04, rot=rot, seg=48)   # hole collar
    for a in range(6):
        ang = math.radians(a * 60 + 30)
        rim.tube((COLL_X - 0.08, 0.55 * math.cos(ang), 0.55 * math.sin(ang)),
                 (-1.28, 1.0 * math.cos(ang), 1.0 * math.sin(ang)), 0.025)
    back, cool = K.MB(), K.MB()
    back.cyl((COLL_X - 0.06, 0, 0), COLL_R * 0.96, 0.07, rot=rot, seg=96)
    for k in range(6):
        cool.ring((COLL_X - 0.1, 0, 0), 0.18 + k * 0.08, 0.165 + k * 0.08, 0.025, rot=rot)
    return [mirror, rim.obj("CollectorRim", M["alu"], bevel=0.003), back.obj("CollectorBack", M["anod"]),
            cool.obj("CollectorCooling", M["copper"])]


def lights_chamber(scale=1.0):
    K.area("Rim", (-0.6, 1.1, 0.9), (0, 0, 0), 0.5, 45 * scale, (0.65, 0.75, 1.0))
    K.area("Key", (0.9, -0.9, 0.7), (0, 0, 0), 0.4, 18 * scale, (0.9, 0.93, 1.0))
    K.area("Top", (0, 0, 1.35), (0, 0, 0), 1.2, 14 * scale, (0.7, 0.8, 1.0))
    K.area("WallWash", (0.3, -1.0, -0.6), (-0.6, 0.8, 0.3), 0.8, 25 * scale, (0.45, 0.55, 0.9))


def camera_only(*obs, glossy=False):
    """Glow helpers: seen by the camera (and optionally in mirrors) but they do not light the scene; the
    point light does that, so the chamber exposure stays controlled."""
    for ob in obs:
        ob.visible_diffuse = False
        ob.visible_glossy = glossy
        ob.visible_transmission = False
        ob.visible_volume_scatter = False
        ob.visible_shadow = False


def plasma(M, c=(0, 0, 0), r=0.035):
    core = single("PlasmaCore", M["plasma_core"], lambda mb: mb.sphere(c, r, 24))
    halo = single("PlasmaHalo", M["plasma_halo"], lambda mb: mb.sphere(c, r * 2.6, 32))
    haze = single("PlasmaHaze", M["plasma_haze"], lambda mb: mb.sphere(c, r * 4.5, 32))
    camera_only(core, glossy=True)
    camera_only(halo, haze)
    li = K.point("PlasmaLight", c, 0, (0.75, 0.62, 1.0), r)
    return [core, halo, haze], li


def laser(M, start, end, r, name="Laser"):
    core = single(name, M["laser"], lambda mb: mb.tube(start, end, r, seg=16))
    halo = single(name + "Halo", M["laser_halo"], lambda mb: mb.tube(start, end, r * 3.5, seg=20))
    camera_only(core, glossy=True)
    camera_only(halo)
    return [core, halo]


def flash(M, c, r):
    a = single("Flash", M["flash"], lambda mb: mb.sphere(c, r * 0.7, 16))
    b = single("FlashHalo", M["flash_halo"], lambda mb: mb.sphere(c, r * 1.7, 24))
    camera_only(a, glossy=True)
    camera_only(b)
    return [a, b]


def pancake(M, c, R, name="Pancake", seed=1):
    """Liquid-tin sheet in the YZ plane (unit radius, scaled by R): thin centre, thickened wavy rim that is
    starting to break into ligaments, and satellite droplets beyond the rim. Returns (root empty, parts)."""
    rnd = random.Random(seed)
    mb = K.MB()
    na, nr = 96, 16
    harm = [(k, rnd.uniform(0.02, 0.07), rnd.uniform(0, 6.28)) for k in (3, 5, 8, 13, 21)]

    def rim(a):
        return 1.0 + sum(amp * math.sin(k * a + ph) for k, amp, ph in harm)

    def thick(t):                       # t = 0 centre .. 1 rim: thin sheet, bulging rim
        return 0.035 + 0.11 * max(0.0, (t - 0.72) / 0.28) ** 2 + 0.01 * t

    top, bot = [], []
    for i in range(nr + 1):
        t = i / nr
        rt, rb = [], []
        for j in range(na):
            a = 2 * math.pi * j / na
            rr = t * rim(a)
            h = thick(t) * (1 + 0.25 * math.sin(7 * a + 3 * t))
            y, z = rr * math.cos(a), rr * math.sin(a)
            rt.append(mb.bm.verts.new((h / 2, y, z)))
            rb.append(mb.bm.verts.new((-h / 2, y, z)))
        top.append(rt)
        bot.append(rb)
    for i in range(nr):
        for j in range(na):
            k = (j + 1) % na
            mb.bm.faces.new((top[i][j], top[i][k], top[i + 1][k], top[i + 1][j])).smooth = True
            mb.bm.faces.new((bot[i][j], bot[i + 1][j], bot[i + 1][k], bot[i][k])).smooth = True
    for j in range(na):
        k = (j + 1) % na
        mb.bm.faces.new((top[nr][j], top[nr][k], bot[nr][k], bot[nr][j])).smooth = True
    bmesh_merge = __import__("bmesh")
    bmesh_merge.ops.remove_doubles(mb.bm, verts=mb.bm.verts[:], dist=1e-5)
    ob = mb.obj(name, M["tin"])
    sub = ob.modifiers.new("Sub", "SUBSURF")
    sub.levels = sub.render_levels = 1
    sat = K.MB()
    for k in range(30):                 # ligaments + satellite droplets
        a = 2 * math.pi * k / 30 + rnd.uniform(-0.08, 0.08)
        r0 = rim(a)
        if k % 2 == 0:
            p0 = Vector((0, r0 * math.cos(a), r0 * math.sin(a)))
            p1 = p0 * rnd.uniform(1.06, 1.16)
            sat.tube(p0 * 0.98, p1, rnd.uniform(0.012, 0.022), seg=8, r2=0.006)
            sat.sphere(p1, 0.025, 10)
        else:
            rr = r0 * rnd.uniform(1.15, 1.4)
            sat.sphere((rnd.uniform(-0.03, 0.03), rr * math.cos(a), rr * math.sin(a)), rnd.uniform(0.012, 0.03), 10)
    so = sat.obj(name + "Sat", M["tin"])
    root = bpy.data.objects.new(name + "Root", None)
    bpy.context.scene.collection.objects.link(root)
    root.location = c
    ob.parent = root
    so.parent = root
    root.scale = (R, R, R)
    return root, [ob, so]


# ---------------------------------------------------------------- variants
def build(variant="cold", shot=None):
    n = K.nframes(shot) if shot else 120
    sc = C.reset_scene(n)
    M = _mats()
    sc["hdri"] = "hangar_interior"
    sc["hdri_strength"] = 0.06
    sc["vignette"] = 0.35
    sc["film_grain"] = 0.1
    cam, tgt = K.camera("CamR2", lens=50)
    fn = {"cold": _cold, "prepulse": _prepulse, "contrast": _contrast, "track": _track, "clean": _clean,
          "spectrum": _spectrum, "amps": _amps}[variant]
    fn(sc, M, cam, tgt, n)
    sc.camera = cam
    return sc


def _dark_world():
    C.set_world(top=(0.035, 0.045, 0.08), horizon=(0.02, 0.026, 0.05), bottom=(0.01, 0.012, 0.022))


def _cold(sc, M, cam, tgt, n):
    """A0_01: frames 72 / 160 / 246 of 290 = pre-pulse hit / pancake + main pulse / plasma."""
    _dark_world()
    chamber(M)
    lights_chamber(1.0)
    r = 0.016
    hit1, hit2, boom = 68, 154, 166
    drop = single("Droplet", M["tin"], lambda mb: mb.sphere((0, 0, 0), r, 48))
    key_loc(drop, [(1, (0, 0, 0.3)), (hit1, (0, 0, 0.0))])
    show_between(drop, 1, hit1 + 2)
    nxt = single("DropletNext", M["tin"], lambda mb: mb.sphere((0, 0, 0), r, 48))
    key_loc(nxt, [(1, (0, 0, 0.62)), (n, (0, 0, 0.62 - 0.3 * n / hit1))])
    root, parts = pancake(M, (0, 0, 0), r)
    key_scale(root, [(hit1 + 2, r * 1.2), (hit2 - 6, r * 9.5), (hit2 + 4, r * 10.5)])
    for ob in parts:
        show_between(ob, hit1 + 3, boom - 1)
    beam_start = (COLL_X - 0.2, 0, 0)
    for ob in laser(M, beam_start, (0, 0, 0), 0.0025, "Pre"):
        show_between(ob, hit1 - 3, hit1 + 6)
    for ob in flash(M, (-0.01, 0, 0), r * 1.4):
        show_between(ob, hit1, hit1 + 5)
    for ob in laser(M, beam_start, (0, 0, 0), 0.011, "Main"):
        show_between(ob, hit2 - 2, hit2 + 9)
    for ob in flash(M, (-0.012, 0, 0), r * 1.1):
        show_between(ob, hit2 + 2, boom)
    pl, li = plasma(M, (0, 0, 0), 0.03)
    for ob in pl:
        show_between(ob, boom)
    key_scale(pl[2], [(boom, 0.4), (boom + 30, 1.0), (n, 1.15)])
    key_energy(li, [(boom - 1, 0), (boom, 45), (n, 55)])
    fl = K.point("LaserLight", (-0.05, -0.02, 0), 0, K.ORANGE, 0.02)
    key_energy(fl, [(hit1 - 1, 0), (hit1, 6), (hit1 + 6, 0), (hit2 - 1, 0), (hit2, 18), (hit2 + 9, 8), (boom, 0)])
    for f in (hit1 + 7, boom + 1):
        fl.data.energy = 0
        fl.data.keyframe_insert("energy", frame=f)
    cam.data.lens = 55
    cam.data.dof.use_dof = True
    cam.data.dof.aperture_fstop = 2.8
    cam.data.dof.focus_object = tgt
    K.key_path(cam, tgt, [(1, (0.6, -0.42, 0.22), (0, 0, 0.12)), (hit1, (0.52, -0.4, 0.12), (0, 0, 0.0)),
                          (n, (0.62, -0.62, 0.16), (-0.05, 0, 0.02))])


def _prepulse(sc, M, cam, tgt, n):
    """B1_10: frames 32 / 69 / 107 of 126: thin pre-pulse hits, the sheet spreads, the next droplet for scale."""
    _dark_world()
    chamber(M)
    lights_chamber(1.0)
    r = 0.014
    hit = 30
    drop = single("Droplet", M["tin"], lambda mb: mb.sphere((0, 0, 0), r, 48))
    key_loc(drop, [(1, (0, 0, 0.06)), (hit, (0, 0, 0))])
    show_between(drop, 1, hit + 2)
    nxt = single("DropletNext", M["tin"], lambda mb: mb.sphere((0, 0, 0), r, 48))
    key_loc(nxt, [(1, (0, 0, 0.30)), (n, (0, 0, 0.30 - 0.06 * n / hit))])
    root, parts = pancake(M, (0, 0, 0), r)
    key_scale(root, [(hit + 2, r * 1.2), (hit + 40, r * 9.0), (n, r * 12.0)])
    for ob in parts:
        show_between(ob, hit + 3)
    for ob in laser(M, (COLL_X - 0.2, 0, -0.02), (0, 0, 0), 0.0022, "Pre"):
        show_between(ob, hit - 6, hit + 8)
    for ob in flash(M, (-0.008, 0, 0), r * 1.3):
        show_between(ob, hit, hit + 5)
    fl = K.point("LaserLight", (-0.05, -0.02, 0), 0, K.ORANGE, 0.02)
    key_energy(fl, [(hit - 1, 0), (hit, 7), (hit + 8, 0)])
    cam.data.lens = 50
    cam.data.dof.use_dof = True
    cam.data.dof.aperture_fstop = 4
    cam.data.dof.focus_object = tgt
    K.key_path(cam, tgt, [(1, (0.55, -0.72, 0.12), (0, 0, 0.05)), (n, (0.62, -0.8, 0.14), (0, 0, 0.06))])


def _debris(M, seed=4):
    rnd = random.Random(seed)
    objs = []
    for key, cnt, rr in (("hot", 40, (0.004, 0.008)), ("warm", 60, (0.003, 0.007)), ("cool", 80, (0.003, 0.006))):
        mb = K.MB()
        for _ in range(cnt):
            v = Vector((rnd.gauss(0, 1), rnd.gauss(0, 1), rnd.gauss(0, 1))).normalized()
            d = {"hot": rnd.uniform(0.08, 0.25), "warm": rnd.uniform(0.2, 0.45), "cool": rnd.uniform(0.35, 0.7)}[key]
            p = v * d
            mb.tube(p, p + v * rnd.uniform(0.006, 0.02), rnd.uniform(*rr) * 0.4, seg=6)     # short motion streak
        ob = mb.obj("Debris_" + key, M[key])
        ob.visible_shadow = False
        objs.append(ob)
    return objs


def _contrast(sc, M, cam, tgt, n):
    """B1_15 (36 frames): plasma at the left third, the collector's polished surface filling the right."""
    _dark_world()
    chamber(M, seed=2)
    lights_chamber(0.8)
    pl, li = plasma(M, (0, 0, 0), 0.03)
    key_energy(li, [(1, 40), (n, 50)])
    for ob in _debris(M):
        key_scale(ob, [(1, 0.55), (n, 1.25)], interp="LINEAR")
    cam.data.lens = 32
    cam.data.dof.use_dof = True
    cam.data.dof.aperture_fstop = 5.6
    foc = bpy.data.objects.new("Focus", None)
    sc.collection.objects.link(foc)
    foc.location = (-0.55, 0.15, 0.1)
    cam.data.dof.focus_object = foc
    cam.data.lens = 26
    foc.location = (-0.7, 0.25, 0.05)
    K.key_path(cam, tgt, [(1, (0.5, -0.5, 0.15), (-0.75, 0.25, 0.0)), (n, (0.46, -0.47, 0.14), (-0.75, 0.27, 0.0))],
               interp="LINEAR")


def _track(sc, M, cam, tgt, n):
    """B1_08 (92 frames): droplets fall past a lock line at z = 0; each carries its own cyan reticle that
    thickens while that droplet is locked."""
    _dark_world()
    chamber(M, seed=3, collector=True)
    lights_chamber(1.0)
    r = 0.012
    sp, v = 0.13, 0.0042                      # spacing (m), speed (m / frame)
    rot = (math.radians(90), 0, 0)            # rings face the camera (camera looks along +Y)
    for i in range(8):
        z0 = 0.36 + i * sp - 0.2
        d = single(f"Drop{i}", M["tin"], lambda mb: mb.sphere((0, 0, 0), r, 32))
        key_loc(d, [(1, (0, 0, z0)), (n, (0, 0, z0 - v * (n - 1)))])
        ret = K.MB()
        ret.ring((0, 0, 0), r * 3.2, r * 3.0, 0.001, rot=rot, seg=48)
        for k in range(4):                    # corner brackets
            a = math.radians(45 + 90 * k)
            cx, cz = math.cos(a) * r * 4.3, math.sin(a) * r * 4.3
            ret.box((cx - math.copysign(r * 0.5, cx), 0, cz), (r * 1.1, 0.001, r * 0.18))
            ret.box((cx, 0, cz - math.copysign(r * 0.5, cz)), (r * 0.18, 0.001, r * 1.1))
        ro = ret.obj(f"Ret{i}", M["reticle"])
        ro.parent = d
        ro.location = (0, -0.03, 0)
        ro.visible_shadow = False
        lk = single(f"Lock{i}", M["reticle_lock"], lambda mb: mb.ring((0, 0, 0), r * 3.6, r * 3.1, 0.001, rot=rot, seg=48))
        lk.parent = d
        lk.location = (0, -0.031, 0)
        lk.visible_shadow = False
        # locked while |z| < 0.07
        fa = round(1 + (z0 - 0.07) / v)
        fb = round(1 + (z0 + 0.07) / v)
        if fb >= 1 and fa <= n:
            show_between(lk, max(1, fa), min(n, fb))
        else:
            lk.hide_render = True
    cam.data.lens = 50
    K.key_path(cam, tgt, [(1, (0.03, -0.72, 0.02), (0, 0, 0.02)), (n, (-0.03, -0.66, 0.0), (0, 0, 0.0))],
               interp="LINEAR")


def _clean(sc, M, cam, tgt, n):
    """B2_08 (242 frames): across the collector surface: grey tin deposits on the mirror, the plasma's violet
    glow reflected in it; the camera slides over the dish towards its rim."""
    _dark_world()
    chamber(M, seed=5)
    lights_chamber(0.7)
    pl, li = plasma(M, (0, 0, 0), 0.025)
    for ob in pl[1:]:
        ob.visible_glossy = True                    # the mirror shows the violet glow
    key_energy(li, [(1, 35), (n, 35)])
    K.area("Graze", (-0.35, -0.75, -0.25), (-0.85, 0.1, 0.15), 0.5, 30, (0.85, 0.88, 1.0))
    rnd = random.Random(8)
    dep, film = K.MB(), K.MB()
    for _ in range(900):
        rr = math.sqrt(rnd.uniform(0.12 ** 2, 0.64 ** 2))
        a = rnd.uniform(0, 2 * math.pi)
        y, z = rr * math.cos(a), rr * math.sin(a)
        s = rnd.uniform(0.002, 0.006) * (2.0 if rnd.random() < 0.06 else 1)
        dep.sphere((coll_x(rr) - s * 0.45, y, z), s, 10)          # sunk: reads as a flattened bead
    for _ in range(25):                             # thin tin film patches
        rr = rnd.uniform(0.2, 0.6)
        a = rnd.uniform(0, 2 * math.pi)
        y, z = rr * math.cos(a), rr * math.sin(a)
        p = Vector((coll_x(rr) + 0.0015, y, z))
        nrm = Vector((1, -y / (2 * COLL_F), -z / (2 * COLL_F))).normalized()
        from mathutils import Matrix
        film.cyl_m(Matrix.Translation(p) @ Vector((0, 0, 1)).rotation_difference(nrm).to_matrix().to_4x4(),
                   rnd.uniform(0.006, 0.014), 0.0015, seg=16)
    dob = dep.obj("TinDeposits", M["tin_dep"])
    dep2 = film.obj("TinFilm", M["tin_dep"])
    cam.data.lens = 35
    cam.data.dof.use_dof = True
    cam.data.dof.aperture_fstop = 5.6
    cam.data.dof.focus_object = tgt
    K.key_path(cam, tgt, [(1, (-0.5, -0.45, 0.42), (-0.86, 0.08, 0.12)), (n, (-0.52, -0.32, 0.5), (-0.86, 0.16, 0.08))],
               interp="LINEAR")


def _spectrum(sc, M, cam, tgt, n):
    """B1_18 (194 frames): defocused plasma and chamber, dim enough for the spectrum HUD to sit on top."""
    _dark_world()
    chamber(M, seed=6)
    lights_chamber(0.35)
    pl, li = plasma(M, (0, 0, 0), 0.03)
    key_energy(li, [(1, 40), (n, 45)])
    cam.data.lens = 45
    cam.data.dof.use_dof = True
    cam.data.dof.aperture_fstop = 1.4
    foc = bpy.data.objects.new("Focus", None)
    sc.collection.objects.link(foc)
    foc.location = (0.75, -0.45, 0.15)
    cam.data.dof.focus_object = foc
    K.key_path(cam, tgt, [(1, (1.0, -0.6, 0.18), (-0.25, 0.08, 0.0)), (n, (0.9, -0.52, 0.14), (-0.25, 0.08, 0.0))],
               interp="LINEAR")


# ---------------------------------------------------------------- CO2 amplifier chain
def _amps(sc, M, cam, tgt, n):
    """B1_22 (97 frames): seed laser + four amplifier modules on an optical table; the orange beam thickens
    and brightens stage by stage. Camera tracks along the chain."""
    K.world_dark(0.9)
    K.floor("Floor", K.mat("FloorDark", (0.05, 0.055, 0.065), rough=0.3, coat=0.3), z=0.0)
    table, hous, fins, bolt, pipe, cab, anod, led = (K.MB() for _ in range(8))
    rnd = random.Random(11)
    L = 9.2
    table.box((L / 2 - 0.6, 0, 0.42), (L + 0.6, 1.2, 0.08))
    for x in [i * 1.1 - 0.4 for i in range(10)]:
        for y in (-0.5, 0.5):
            table.box((x, y, 0.2), (0.08, 0.08, 0.38))
    for i in range(int(L / 0.1)):
        bolt.cyl((-0.5 + i * 0.1, -0.56, 0.465), 0.006, 0.008, seg=6)
    z = 0.9
    # stage x-ranges: seed then four amplifiers
    stages = [(-0.4, 0.5), (1.0, 2.6), (3.0, 4.6), (5.0, 6.6), (7.0, 8.6)]
    radii = [0.004, 0.008, 0.013, 0.02, 0.03]
    for si, (x0, x1) in enumerate(stages):
        cx = (x0 + x1) / 2
        if si == 0:
            hous.box((cx, 0, z), (x1 - x0, 0.5, 0.42))
            anod.box((cx, 0.1, z + 0.26), (0.6, 0.25, 0.1))
            for k in range(6):
                led.box((x0 + 0.1 + k * 0.08, -0.252, z + 0.12), (0.02, 0.004, 0.012))
            continue
        # amplifier: discharge tube surrounded by finned heat exchanger, end flanges, RF supply box behind
        hous.tube((x0, 0, z), (x1, 0, z), 0.16, seg=40)
        for k in range(int((x1 - x0) / 0.05)):
            fins.ring((x0 + 0.04 + k * 0.05, 0, z), 0.27, 0.16, 0.012, rot=(0, math.radians(90), 0), seg=40)
        for xe in (x0, x1):
            hous.ring((xe, 0, z), 0.32, 0.03, 0.05, rot=(0, math.radians(90), 0), seg=48)
            bolt.bolts((xe + (0.03 if xe == x0 else -0.03), 0, z), 0.29, 16, 0.008, 0.02, rot=(0, math.radians(90), 0))
        anod.box((cx, 0.45, z + 0.05), (x1 - x0 - 0.2, 0.3, 0.6))                     # RF supply
        for k in range(int((x1 - x0) / 0.12)):
            anod.box((x0 + 0.15 + k * 0.12, 0.29, z + 0.05), (0.02, 0.03, 0.5))       # vents
        for k in range(4):
            led.box((x0 + 0.2 + k * 0.06, 0.29, z + 0.33), (0.02, 0.004, 0.012))
        for k, yy in enumerate((0.18, 0.24)):                                          # coolant lines
            pipe.path([(x0 + 0.1, yy, z - 0.35), (x0 + 0.1, yy, z - 0.2), (x1 - 0.1, yy, z - 0.2),
                       (x1 - 0.1, yy, z - 0.35)], 0.014 + 0.004 * k, seg=10)
        K.cable_run(cab, [(cx, 0.6, z + 0.35), (cx + 0.2, 0.75, z + 0.6), (cx + 0.5, 0.9, 1.6)], n=5, r=0.009,
                    seed=si)
        hous.box((cx, 0, 0.5), (x1 - x0 - 0.3, 0.4, 0.08))                             # cradle
        for xs in (x0 + 0.25, x1 - 0.25):
            hous.box((xs, 0, 0.64), (0.08, 0.36, 0.22))
    # beam tubes / bellows between stages
    for (a0, a1), (b0, b1) in zip(stages, stages[1:]):
        pipe.tube((a1, 0, z), (b0, 0, z), 0.035, seg=20)
        for k in range(6):
            fins.ring((a1 + (b0 - a1) * (k + 1) / 7, 0, z), 0.05, 0.035, 0.012, rot=(0, math.radians(90), 0), seg=24)
    hous_o = hous.obj("AmpHousings", M["paint_grey"], bevel=0.006)
    objs = [table.obj("Table", M["anod"], bevel=0.004), hous_o, fins.obj("Fins", M["alu"]),
            bolt.obj("Bolts", M["steel"]), pipe.obj("Coolant", M["copper"]), cab.obj("Cables", M["cable_b"]),
            anod.obj("Supplies", M["anod"], bevel=0.005), led.obj("LEDs", M["led_c"])]
    # beam: thin glass window strip along each amplifier so the beam is visible inside
    beam_mb, halo_mb = K.MB(), K.MB()
    for si, (x0, x1) in enumerate(stages):
        nxt = stages[si + 1][0] if si + 1 < len(stages) else x1 + 0.9
        r = radii[si]
        beam_mb.tube((x1 - 0.02, 0, z), (nxt + 0.02, 0, z), r, seg=16)
        halo_mb.tube((x1 - 0.02, 0, z), (nxt + 0.02, 0, z), r * 3.5, seg=20)
        if si > 0:      # visible through a slot cut in the fins: draw the beam slightly in front of the tube
            beam_mb.tube((x0, -0.0, z), (x1, -0.0, z), r * 0.9, seg=16)
    bo = beam_mb.obj("CO2Beam", M["laser"])
    ho = halo_mb.obj("CO2BeamHalo", M["laser_halo"])
    for ob in (bo, ho):
        ob.visible_shadow = False
    # cut the front of every amplifier open (fin slot) by hiding the fins in front: use a boolean box
    cut = bpy.data.objects.new("FinCut", bpy.data.meshes.new("FinCut"))
    mb = K.MB()
    mb.box((L / 2, -0.25, z), (L + 2, 0.5, 0.06))
    cut = mb.obj("FinCut", M["anod"])
    cut.hide_render = True
    cut.display_type = "WIRE"
    for ob in (objs[2], hous_o):
        bo_ = ob.modifiers.new("Slot", "BOOLEAN")
        bo_.object = cut
        bo_.operation = "DIFFERENCE"
        bo_.solver = "FAST" if "FAST" in [i.identifier for i in bpy.types.BooleanModifier.bl_rna.properties["solver"].enum_items] else "EXACT"
    K.area("Key", (3, -4, 4), (4, 0, 0.9), 6, 700, (0.9, 0.93, 1.0))
    K.area("Rim", (4, 3, 3), (4, 0, 0.9), 8, 900, (0.7, 0.78, 1.0))
    K.area("Top", (4, 0, 4), (4, 0, 0), 10, 400, (0.9, 0.92, 1.0), size_y=3)
    for si, (x0, x1) in enumerate(stages[1:]):
        K.point(f"BeamGlow{si}", ((x0 + x1) / 2, -0.35, z), 6 + 10 * si, K.ORANGE, 0.1)
    cam.data.lens = 35
    cam.data.dof.use_dof = True
    cam.data.dof.aperture_fstop = 5.6
    cam.data.dof.focus_object = tgt
    K.key_path(cam, tgt, [(1, (-0.6, -2.4, 1.6), (1.6, 0, 0.9)), (n, (4.6, -2.6, 1.7), (6.2, 0, 0.9))],
               interp="LINEAR")
