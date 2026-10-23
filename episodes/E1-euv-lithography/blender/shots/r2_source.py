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


def show_from(ob, a):
    """Render-visible from frame a on; only the hide_render curve is made constant (show_between flattens every
    curve of the object, which froze the R10 droplets' fall)."""
    ob.hide_render = True
    ob.keyframe_insert("hide_render", frame=a - 1)
    ob.hide_render = False
    ob.keyframe_insert("hide_render", frame=a)
    for fc in C.fcurves(ob.animation_data.action):
        if fc.data_path == "hide_render":
            for k in fc.keyframe_points:
                k.interpolation = "CONSTANT"


def show_between_vis(ob, a, b=None):
    """R14: like show_between, but only the hide_render curve is made constant (show_between froze the A0_01
    droplet's fall at z = 0.3, so in R13 the droplet was out of frame until the hit)."""
    ob.hide_render = True
    ob.keyframe_insert("hide_render", frame=min(0, a - 1))
    if a > 1:
        ob.keyframe_insert("hide_render", frame=a - 1)
    ob.hide_render = False
    ob.keyframe_insert("hide_render", frame=a)
    if b is not None:
        ob.hide_render = True
        ob.keyframe_insert("hide_render", frame=b + 1)
    for fc in C.fcurves(ob.animation_data.action):
        if fc.data_path == "hide_render":
            for k in fc.keyframe_points:
                k.interpolation = "CONSTANT"


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
    # R3: smoked viewport glass (the R2 glowing blue disc read as an unexplained "blue window")
    M["window"] = K.mat("ViewportSmoked", (0.03, 0.035, 0.045), metal=0.0, rough=0.04, coat=1.0)
    M["plasma_core"] = K.emit_mat("PlasmaCore", (0.93, 0.88, 1.0), 8.0)
    M["plasma_halo"] = vol_glow("PlasmaHalo", (0.72, 0.6, 1.0), 9.0)
    M["plasma_haze"] = vol_glow("PlasmaHaze", K.VIOLET, 0.9)
    M["flash"] = K.emit_mat("LaserFlash", (1.0, 0.8, 0.55), 8.0)
    M["flash_halo"] = vol_glow("LaserFlashHalo", K.ORANGE, 10.0)
    # R10: debris is hot white / tin grey - orange is reserved for the CO2 laser (R9 review, B1_15)
    M["hot"] = K.emit_mat("DebrisHot", (0.95, 0.95, 1.0), 14.0)
    M["warm"] = K.emit_mat("DebrisTin", (0.66, 0.68, 0.74), 2.2)
    M["cool"] = K.emit_mat("DebrisCool", (0.4, 0.41, 0.45), 0.8)
    M["reticle"] = K.emit_mat("Reticle", K.CYAN, 4.0)          # R5: thin HUD lines, not game-UI rings
    M["reticle_lock"] = K.emit_mat("ReticleLock", K.CYAN, 7.0)
    return M


# ---------------------------------------------------------------- R14 metals (non-amps variants only)
PLASMA_LIGHT_R14 = (0.86, 0.82, 1.0)     # violet stays in the glow; the light on the metal is near-neutral


def _liquid_tin_r14(name="LiquidTinR14"):
    """R14 root cause #6 ("pancake reads as a grey plate"): liquid tin = near-perfect silver mirror (rough 0.025)
    with fine circumferential flow ripples in the normal (bump only - the colour stays clean), so it shows the
    studio cards as bright, rippling bands (k3A) instead of a matte disc with dark smudges."""
    m = K.mat(name, (0.95, 0.95, 0.96), metal=1.0, rough=0.025)
    nt = m.node_tree
    b = next(nd for nd in nt.nodes if nd.type == "BSDF_PRINCIPLED")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sp = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sp.inputs[0])
    cb = nt.nodes.new("ShaderNodeCombineXYZ")
    nt.links.new(sp.outputs["Y"], cb.inputs["X"])
    nt.links.new(sp.outputs["Z"], cb.inputs["Y"])
    ln = nt.nodes.new("ShaderNodeVectorMath")
    ln.operation = "LENGTH"
    nt.links.new(cb.outputs[0], ln.inputs[0])
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 2.2
    nz.inputs["Detail"].default_value = 3.0
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    add = nt.nodes.new("ShaderNodeMath")
    add.operation = "MULTIPLY_ADD"
    nt.links.new(nz.outputs["Fac"], add.inputs[0])
    add.inputs[1].default_value = 0.28
    nt.links.new(ln.outputs["Value"], add.inputs[2])
    sn = nt.nodes.new("ShaderNodeMath")
    sn.operation = "SINE"
    mul = nt.nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    mul.inputs[1].default_value = 26.0
    nt.links.new(add.outputs[0], mul.inputs[0])
    nt.links.new(mul.outputs[0], sn.inputs[0])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.035
    bump.inputs["Distance"].default_value = 0.02
    nt.links.new(sn.outputs[0], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    return m


def _mirror_r14(name, rough=0.012):
    """R14 root cause #6: the collector is a neutral, high-reflectance polished multilayer mirror (no violet base
    colour, no emissive sheen); any violet on it is the plasma's own reflection."""
    return K.mat(name, (0.9, 0.9, 0.92), metal=1.0, rough=rough, coat=0.4)


def _metals_r14(M):
    M["tin"] = _liquid_tin_r14()
    M["coll"] = _mirror_r14("CollectorMLMirrorR14")


# ---------------------------------------------------------------- R15 (root causes #2 / #3, non-amps variants only)
def _tin_film_r15(name="TinFilmR15"):
    """R15 root cause #3 (R14: "crumpled aluminium foil filling the frame"): the pre-pulse sheet is a THIN liquid
    film. Smooth liquid-tin surface (no ripple bump); in object space (unit-radius sheet) the thin centre lets most
    light through (transparent mix ~0.7) while the rolled rim is opaque bright metal, so the sheet reads as a
    thin liquid membrane with a bright edge instead of a solid plate."""
    m = K.mat(name, (0.94, 0.94, 0.96), metal=1.0, rough=0.035)
    nt = m.node_tree
    out = next(nd for nd in nt.nodes if nd.type == "OUTPUT_MATERIAL")
    b = next(nd for nd in nt.nodes if nd.type == "BSDF_PRINCIPLED")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sp = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sp.inputs[0])
    cb = nt.nodes.new("ShaderNodeCombineXYZ")
    nt.links.new(sp.outputs["Y"], cb.inputs["X"])
    nt.links.new(sp.outputs["Z"], cb.inputs["Y"])
    ln = nt.nodes.new("ShaderNodeVectorMath")
    ln.operation = "LENGTH"
    nt.links.new(cb.outputs[0], ln.inputs[0])
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.interpolation_type = "SMOOTHSTEP"
    mr.inputs["From Min"].default_value = 0.55
    mr.inputs["From Max"].default_value = 0.9
    mr.inputs["To Min"].default_value = 0.55
    mr.inputs["To Max"].default_value = 0.0
    nt.links.new(ln.outputs["Value"], mr.inputs["Value"])
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    tr.inputs["Color"].default_value = (0.92, 0.93, 0.96, 1)
    mx = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(mr.outputs["Result"], mx.inputs["Fac"])
    nt.links.new(b.outputs[0], mx.inputs[1])
    nt.links.new(tr.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs["Surface"])
    return m


def _metals_r15(M, coll_rough=0.02):
    """R15 root cause #2: the collector uses the shared mirror_r15 multilayer surface (neutral silver, no violet
    base, no emission); liquid tin droplets stay mirror-bright; the pre-pulse sheet is the thin film above."""
    import mirror_r15 as MR
    M["tin"] = _liquid_tin_r14()
    M["tin_film"] = _tin_film_r15()
    M["coll"] = MR.ml_mirror("CollectorML_R15", rough=coll_rough)


def pancake_r15(M, c, R, name="Pancake", seed=1):
    """R15 root cause #3: thin liquid sheet in the YZ plane (unit radius, scaled by R): a membrane ~1/40 of its
    radius thick, a smooth rolled rim (torus-like bead) and a few droplets flung off OUTSIDE the rim, in the sheet
    plane - nothing sits on the face (R14 review B1_10 #1). Not repeating: the R14 crumple / rippled liquid
    metal plate."""
    import bmesh
    rnd = random.Random(seed)
    mb = K.MB()
    na, nr = 128, 20
    harm = [(k, rnd.uniform(0.004, 0.01), rnd.uniform(0, 6.28)) for k in (3, 5, 9)]

    def rim(a):
        return 1.0 + sum(amp * math.sin(k * a + ph) for k, amp, ph in harm)

    def thick(t):                       # thin membrane, rolled bead at the rim
        return 0.022 + 0.075 * max(0.0, (t - 0.84) / 0.16) ** 1.5

    top, bot = [], []
    for i in range(nr + 1):
        t = i / nr
        rt, rb = [], []
        for j in range(na):
            a = 2 * math.pi * j / na
            rr = t * rim(a)
            h = thick(t)
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
    bmesh.ops.remove_doubles(mb.bm, verts=mb.bm.verts[:], dist=1e-5)
    ob = mb.obj(name, M["tin_film"])
    sub = ob.modifiers.new("Sub", "SUBSURF")
    sub.levels = sub.render_levels = 1
    sat = K.MB()
    for k in range(9):                  # droplets flung off the rim, in the sheet plane
        a = 2 * math.pi * (k + rnd.uniform(-0.3, 0.3)) / 9
        rr = rim(a) * rnd.uniform(1.12, 1.35)
        sat.sphere((0.0, rr * math.cos(a), rr * math.sin(a)), rnd.uniform(0.03, 0.05), 14)
    so = sat.obj(name + "Sat", M["tin"])
    root = bpy.data.objects.new(name + "Root", None)
    bpy.context.scene.collection.objects.link(root)
    root.location = c
    ob.parent = root
    so.parent = root
    root.scale = (R, R, R)
    cv = Vector(c)
    K.area(name + "Softbox", cv + Vector((0.42, 0.48, -0.1)), cv, 0.35, 0.28, (0.9, 0.93, 1.0))
    sb = bpy.data.objects.get(name + "Softbox")
    if sb is not None:
        sb.visible_camera = False
        _link_only(sb, [ob, so])                     # R15: no white softbox rectangle in the collector mirror
    return root, [ob, so]


def _link_only(emitter, receivers):
    """Cycles light linking: `emitter` only shows on / lights `receivers`."""
    col = bpy.data.collections.new(emitter.name + "_Recv")
    for ob in receivers:
        col.objects.link(ob)
    try:
        emitter.light_linking.receiver_collection = col
    except Exception as e:
        print("light linking unavailable", e)


def _rim_markers(root):
    """Empties on the sheet's rim (top / bottom), parented to the scaled root: the overlay's 300 um dimension line
    follows the real sheet edge on screen."""
    out = {}
    for k, z in (("pk_top", 1.0), ("pk_bot", -1.0)):
        e = bpy.data.objects.new("Mark_" + k, None)
        bpy.context.scene.collection.objects.link(e)
        e.parent = root
        e.location = (0, 0, z)
        out[k] = e
    return out


def main_pulse_cone_r15(start, end, r0, r1, name="MainPulse"):
    """R15 (A0_01 review #1: "main pulse drawn as a disc spot on the sheet centre"): the main CO2 pulse is a
    soft-edged orange cone seen side-on, widening from the collector hole to cover the sheet."""
    m = bpy.data.materials.new(name + "Mat")           # volume-only: soft glowing cone, no hard surface
    m.use_nodes = True
    nt = m.node_tree
    for nd in list(nt.nodes):
        if nd.type != "OUTPUT_MATERIAL":
            nt.nodes.remove(nd)
    out = next(nd for nd in nt.nodes if nd.type == "OUTPUT_MATERIAL")
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    nt.links.new(tr.outputs[0], out.inputs["Surface"])
    ve = nt.nodes.new("ShaderNodeEmission")
    ve.inputs["Color"].default_value = (*K.lin(K.ORANGE), 1)
    # soft edge: strength falls off with distance from the beam axis (the beam runs along world X here)
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    sp = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(geo.outputs["Position"], sp.inputs[0])
    cb = nt.nodes.new("ShaderNodeCombineXYZ")
    nt.links.new(sp.outputs["Y"], cb.inputs["Y"])
    nt.links.new(sp.outputs["Z"], cb.inputs["Z"])
    ln = nt.nodes.new("ShaderNodeVectorMath")
    ln.operation = "LENGTH"
    nt.links.new(cb.outputs[0], ln.inputs[0])
    x0, x1 = start[0], end[0]
    rad = nt.nodes.new("ShaderNodeMapRange")            # cone radius at this x
    rad.clamp = False
    rad.inputs["From Min"].default_value = x0
    rad.inputs["From Max"].default_value = x1
    rad.inputs["To Min"].default_value = r0
    rad.inputs["To Max"].default_value = r1
    nt.links.new(sp.outputs["X"], rad.inputs["Value"])
    dv = nt.nodes.new("ShaderNodeMath")
    dv.operation = "DIVIDE"
    nt.links.new(ln.outputs["Value"], dv.inputs[0])
    nt.links.new(rad.outputs["Result"], dv.inputs[1])
    fall = nt.nodes.new("ShaderNodeMapRange")
    fall.interpolation_type = "SMOOTHSTEP"
    fall.inputs["From Min"].default_value = 0.0
    fall.inputs["From Max"].default_value = 1.0
    fall.inputs["To Min"].default_value = 3.2
    fall.inputs["To Max"].default_value = 0.0
    nt.links.new(dv.outputs[0], fall.inputs["Value"])
    nt.links.new(fall.outputs["Result"], ve.inputs["Strength"])
    nt.links.new(ve.outputs[0], out.inputs["Volume"])
    ob = single(name, m, lambda mb: mb.tube(start, end, r0, seg=48, r2=r1))
    camera_only(ob)
    return ob


def _studio_cards(name, target, cam, normal, dist=0.45, n=4, length=0.7, width=0.05, strength=6.0, spread=0.16,
                  tilt=0.6):
    """Camera-invisible emissive strips placed where a mirror at `target` (surface normal `normal`) reflects the
    camera's view: the metal shows clean bright bands with dark gaps (studio reflections, k3A) instead of the dim
    chamber. They do not light the scene (diffuse off) - only reflections see them."""
    t, c, nrm = Vector(target), Vector(cam), Vector(normal).normalized()
    d = (t - c).normalized()
    if d.dot(nrm) > 0:
        nrm = -nrm
    r = (d - 2 * d.dot(nrm) * nrm).normalized()
    ctr = t + r * dist
    u = r.cross(Vector((0, 0, 1)))
    if u.length < 1e-4:
        u = Vector((1, 0, 0))
    u.normalize()
    v = u.cross(r).normalized()
    mat = K.emit_mat(name + "Mat", (0.95, 0.96, 1.0), strength)
    mb = K.MB()
    for i in range(n):
        off = (i - (n - 1) / 2) * spread
        p = ctr + u * off
        a = tilt * (i - (n - 1) / 2) / max(1, n - 1)
        axis = (v * math.cos(a) + u * math.sin(a)).normalized()
        w = width * (1.0 + 0.6 * (i % 2))
        nn = (t - p).normalized()
        side = nn.cross(axis).normalized()
        q0, q1, q2, q3 = (p - axis * length / 2 - side * w / 2, p + axis * length / 2 - side * w / 2,
                          p + axis * length / 2 + side * w / 2, p - axis * length / 2 + side * w / 2)
        vs = [mb.bm.verts.new(tuple(q)) for q in (q0, q1, q2, q3)]
        mb.bm.faces.new(vs)
    ob = mb.obj(name, mat)
    ob.visible_camera = False
    ob.visible_diffuse = False
    ob.visible_shadow = False
    ob.visible_transmission = False
    ob.visible_volume_scatter = False
    return ob


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
    nr, na = 22, 160
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
    # R10 (B1_15 "white sawtooth on the rim"): the R2-R9 rim ring's inner radius (R - 1 cm) cut through the dish
    # edge, so the jagged mesh intersection caught the light. The ring now starts just outside the dish edge and
    # sits slightly behind it, with a rolled-back lip; the hole collar is dark anodised (read as a white ring).
    rim.ring((coll_x(COLL_R) - 0.035, 0, 0), COLL_R + 0.08, COLL_R + 0.006, 0.06, rot=rot, seg=192)
    rim.bolts((coll_x(COLL_R) - 0.0, 0, 0), COLL_R + 0.045, 36, 0.009, 0.02, rot=rot)
    lip = K.MB()
    lip.ring((coll_x(COLL_R) - 0.012, 0, 0), COLL_R + 0.008, COLL_R - 0.004, 0.02, rot=rot, seg=192)
    lip.ring((COLL_X - 0.012, 0, 0), hole_r + 0.022, hole_r - 0.002, 0.03, rot=rot, seg=64)   # hole collar
    for a in range(6):
        ang = math.radians(a * 60 + 30)
        rim.tube((COLL_X - 0.08, 0.55 * math.cos(ang), 0.55 * math.sin(ang)),
                 (-1.28, 1.0 * math.cos(ang), 1.0 * math.sin(ang)), 0.025)
    back, cool = K.MB(), K.MB()
    back.cyl((COLL_X - 0.06, 0, 0), COLL_R * 0.96, 0.07, rot=rot, seg=96)
    for k in range(6):
        cool.ring((COLL_X - 0.1, 0, 0), 0.18 + k * 0.08, 0.165 + k * 0.08, 0.025, rot=rot)
    return [mirror, rim.obj("CollectorRim", M["alu"], bevel=0.003), lip.obj("CollectorLip", M["anod"]),
            back.obj("CollectorBack", M["anod"]),
            cool.obj("CollectorCooling", M["copper"])]


def chamber_r10(M, seed=0, tip_z=0.45, collector=True, catcher=True, diag=(), extra_ports=True, hide_front=None,
                liner=True, wall_skip=None, r16=False):
    """R10 (R9 review gap 4: "B1_08 / B1_10 / A0_01 backgrounds are a flat striped wall / a few arcs"): a k3A-style
    metal source vessel seen from inside. Dark brushed steel wall behind curved liner panels (seams + corner bolts,
    no bright ribs), CF ports with viewports (hero_kit_r10.flange_viewport) pointing at the plasma, tapered
    diagnostic barrels (EUV sensors / droplet cameras) converging on the plasma site, hose bundles along the wall,
    the tin droplet generator coming down from the lid with its nozzle tip at (0, 0, tip_z), the droplet catcher
    below, and the collector. diag = list of (azimuth deg, z) for extra barrels aimed at the origin.
    hide_front(p) -> True skips a part at p (keeps the camera side clear).
    R16 (root cause #2, r16=True): no liner panel grid, no blue/white hose bundles / cable trays - the wall carries
    interleaved nameable modules (source_kit_r16.wall_modules_r16)."""
    if r16:
        liner = False
    import hero_kit_r10 as H
    rnd = random.Random(seed)
    R = CHAMBER_R
    skip = hide_front or (lambda p: False)
    M.setdefault("chamber_dk", K.mat("ChamberDarkR10", (0.16, 0.17, 0.2), metal=1.0, rough=0.32, brushed=0.1))
    M.setdefault("liner", K.mat("LinerR10", (0.34, 0.35, 0.39), metal=1.0, rough=0.5, speck=0.08))
    M.setdefault("barrel", K.mat("BarrelR10", (0.62, 0.63, 0.67), metal=1.0, rough=0.18))
    w, ln, sm, bolt, br, dk = K.MB(), K.MB(), K.MB(), K.MB(), K.MB(), K.MB()
    w.shell((0, 0, 0), R, R + 0.08, 3.0, 0, 360, seg=128)
    w.cyl((0, 0, 1.54), R + 0.08, 0.08, seg=128)
    w.cyl((0, 0, -1.54), R + 0.08, 0.08, seg=128)
    # liner panels: 18 deg x 0.5 m curved plates, 1.2 deg seams, 4 bolts each
    for k in range(6 if liner else 0):        # R12 (liner=False): no repeated panel grid (B1_15 / B1_08)
        zc = -1.25 + k * 0.5
        for j in range(20):
            a0 = j * 18.0
            mid = math.radians(a0 + 9)
            pm = Vector((math.cos(mid) * R, math.sin(mid) * R, zc))
            if skip(pm):
                continue
            ln.shell((0, 0, zc), R - 0.04, R - 0.025, 0.47, a0 + 0.6, a0 + 17.4, seg=60)
            for da in (1.6, 16.4):
                for dz in (-0.2, 0.2):
                    a = math.radians(a0 + da)
                    p = Vector((math.cos(a) * (R - 0.045), math.sin(a) * (R - 0.045), zc + dz))
                    bolt.cyl(p, 0.007, 0.01, rot=Vector((0, 0, 1)).rotation_difference(Vector((math.cos(a), math.sin(a), 0))).to_euler(), seg=6)
    # two machined stiffening rings at the panel joints (dark, not bright stripes)
    for z in (-0.75, 0.75):
        sm.ring((0, 0, z), R - 0.02, R - 0.075, 0.035, seg=128)
    P = H.new_parts()
    # ports: CF viewports / blank flanges on the wall pointing at the plasma
    ports = []
    for k in range(22 if extra_ports else 10):
        a = rnd.uniform(0, 2 * math.pi)
        z = rnd.uniform(-1.05, 1.05)
        r = rnd.choice((0.05, 0.065, 0.08, 0.1))
        p = Vector((math.cos(a), math.sin(a), 0)) * (R - 0.04) + Vector((0, 0, z))
        if skip(p) or any((p - q).length < r * 2.2 + rr * 2.2 for q, rr in ports):
            continue
        if abs(z) < 0.4 and math.cos(a) < -0.45:               # keep clear of the collector
            continue
        ports.append((p, r))
        n = (-p).normalized()
        H.flange_viewport(P, p, n, r, nipple=r * 1.0, side_port=(k % 3 == 0))
    # tapered diagnostic barrels converging on the plasma (k3A)
    bars = [(rnd.uniform(0, 360), rnd.uniform(-0.6, 0.6)) for _ in range(5)] + list(diag)
    for bi, (az, z) in enumerate(bars):
        a = math.radians(az)
        base = Vector((math.cos(a) * (R - 0.04), math.sin(a) * (R - 0.04), z))
        if bi < 5 and (skip(base) or (abs(z) < 0.45 and math.cos(a) < -0.4)):
            continue
        d = (-base).normalized()
        L = base.length - 0.42
        tip = base + d * L
        H._ring(P["alu"], base + d * 0.02, d, 0.13, 0.06, 0.04, seg=40)
        H._bolt_circle(P, base + d * 0.045, d, 0.105, 10, 0.008, 0.012)
        br.tube(base + d * 0.04, base + d * (L * 0.55), 0.07, seg=32, r2=0.055)
        br.tube(base + d * (L * 0.55), tip, 0.045, seg=32, r2=0.026)
        H._ring(P["alu_dark"], base + d * (L * 0.55), d, 0.075, 0.05, 0.03, seg=32)
        H._ring(P["alu_dark"], base + d * (L * 0.3), d, 0.08, 0.06, 0.02, seg=32)
        H._cyl(dk, tip + d * 0.003, d, 0.02, 0.006, seg=24)                 # lens / sensor window
        H.cable_harness(P, [base + d * (L * 0.2) + Vector((0, 0, 0.07)), base + d * 0.06 + Vector((0, 0, 0.16)),
                            base + Vector((0, 0, 0.35)) - d * 0.0], n=3, r=0.006, connector=False)
    # hose bundles running up the wall
    for k in range(0 if r16 else 4):
        a0 = rnd.uniform(0, 2 * math.pi)
        pts = []
        for i in range(7):
            a = a0 + i * 0.07
            pts.append(Vector((math.cos(a), math.sin(a), 0)) * (R - 0.09) + Vector((0, 0, -1.2 + i * 0.4)))
        if any(skip(q) for q in pts) or any(math.cos(a0) < -0.5 and abs(q.z) < 0.6 for q in pts):
            continue
        H.cooling_bundle(P, pts, k=4, r=0.011, clamp_every=0.3, up=(math.cos(a0), math.sin(a0), 0), block=False)
    if r16:
        import source_kit_r16 as SK
        SK.wall_modules_r16(P, R, wall_skip or skip, seed=seed,
                            avoid=lambda p: abs(p[2]) < 0.5 and p[0] / R < -0.42)   # keep clear of the collector
    elif not liner:
        _wall_parts_r12(P, sm, R, wall_skip or skip, rnd)
    # tin droplet generator through the lid, nozzle tip at (0, 0, tip_z)
    if tip_z is not None:
        H.droplet_generator(P, (0, 0, tip_z), (0, 0, -1), s=1.0, flange_at=0.3)
        top = tip_z + 1.1
        if top < 1.5:
            sm.tube((0, 0, top), (0, 0, 1.52), 0.05, seg=24)                  # feed line to the lid
            H.cable_harness(P, [(0.13, 0.02, top - 0.4), (0.15, 0.05, top + 0.05), (0.15, 0.05, 1.5)], n=5,
                            r=0.006, connector=False)
    if catcher:
        sm.tube((0, 0, -1.5), (0, 0, -0.62), 0.07, seg=32)
        sm.tube((0, 0, -0.62), (0, 0, -0.52), 0.07, seg=32, r2=0.13)
        H._ring(P["alu"], (0, 0, -0.85), (0, 0, 1), 0.15, 0.07, 0.04, seg=40)
        H._bolt_circle(P, (0, 0, -0.83), (0, 0, 1), 0.12, 10, 0.008, 0.012)
    objs = [w.obj("VesselWallR10", M["chamber_dk"], bevel=0.004), ln.obj("LinerPanels", M["liner"]),
            sm.obj("VesselRingsR10", M["steel"], bevel=0.003), bolt.obj("LinerBolts", M["steel"]),
            br.obj("DiagBarrels", M["barrel"]), dk.obj("DiagLenses", M["window"])]
    objs += H.finish(P, M, "SrcKit")
    if collector:
        objs += collector_mirror(M)
    return objs


def away_from(cam_xy, cos_lim=0.45):
    """hide_front helper: skip wall parts on the camera's side of the vessel (they would block the view)."""
    c = Vector((cam_xy[0], cam_xy[1], 0)).normalized()

    def f(p):
        q = Vector((p[0], p[1], 0))
        return q.length > 1e-6 and q.normalized().dot(c) > cos_lim
    return f


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


def plasma(M, c=(0, 0, 0), r=0.035, li_color=(0.75, 0.62, 1.0)):
    core = single("PlasmaCore", M["plasma_core"], lambda mb: mb.sphere(c, r, 24))
    halo = single("PlasmaHalo", M["plasma_halo"], lambda mb: mb.sphere(c, r * 2.6, 32))
    haze = single("PlasmaHaze", M["plasma_haze"], lambda mb: mb.sphere(c, r * 4.5, 32))
    camera_only(core, glossy=True)
    camera_only(halo, haze)
    li = K.point("PlasmaLight", c, 0, li_color, r)
    return [core, halo, haze], li


def vol_glow_soft(name, color, strength, radius, centre=(0, 0, 0), noise=0.0, scale=40.0):
    """Emission volume whose strength falls smoothly to zero at `radius` from `centre` (object space), optionally
    modulated by 3D noise: a soft, turbulent glowing gas with no visible ball edge."""
    m = vol_glow(name, color, strength)
    nt = m.node_tree
    v = next(nd for nd in nt.nodes if nd.type == "PRINCIPLED_VOLUME")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sub = nt.nodes.new("ShaderNodeVectorMath")
    sub.operation = "SUBTRACT"
    sub.inputs[1].default_value = centre
    nt.links.new(tc.outputs["Object"], sub.inputs[0])
    ln = nt.nodes.new("ShaderNodeVectorMath")
    ln.operation = "LENGTH"
    nt.links.new(sub.outputs[0], ln.inputs[0])
    fall = nt.nodes.new("ShaderNodeMapRange")                 # 1 at the centre -> 0 at the radius
    fall.interpolation_type = "SMOOTHERSTEP"
    fall.inputs["From Min"].default_value = 0.0
    fall.inputs["From Max"].default_value = radius
    fall.inputs["To Min"].default_value = strength
    fall.inputs["To Max"].default_value = 0.0
    nt.links.new(ln.outputs["Value"], fall.inputs["Value"])
    out = fall.outputs["Result"]
    if noise:
        nz = nt.nodes.new("ShaderNodeTexNoise")
        nz.inputs["Scale"].default_value = scale
        nz.inputs["Detail"].default_value = 6.0
        nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
        mr = nt.nodes.new("ShaderNodeMapRange")
        mr.inputs["From Min"].default_value = 0.3
        mr.inputs["From Max"].default_value = 0.7
        mr.inputs["To Min"].default_value = 1 - noise
        mr.inputs["To Max"].default_value = 1 + noise
        nt.links.new(nz.outputs["Fac"], mr.inputs["Value"])
        mul = nt.nodes.new("ShaderNodeMath")
        mul.operation = "MULTIPLY"
        nt.links.new(out, mul.inputs[0])
        nt.links.new(mr.outputs["Result"], mul.inputs[1])
        out = mul.outputs[0]
    nt.links.new(out, v.inputs["Emission Strength"])
    return m


def plasma_r10(M, c=(0, 0, 0), r=0.035, energy=60.0, gas=1.0, li_color=(0.75, 0.62, 1.0), mirror_core=False):
    """R10 (R9 review B1_15: "a white disc plus a wire ring cannot read as a hot glow"): a k3A volumetric core.
    No hard emissive surface - four nested emission volumes, each fading smoothly to zero at its edge (so the sum
    is a bright white-violet kernel inside a soft violet cloud), the outer two turbulent; a violet point light that
    washes the collector."""
    obs = []
    for i, (k, st, col, noisy) in enumerate(((0.35, 600.0, (0.97, 0.95, 1.0), 0.0), (0.9, 110.0, (0.86, 0.78, 1.0), 0.0),
                                             (2.0, 16.0, (0.68, 0.52, 1.0), 0.5), (4.2, 2.6, K.VIOLET, 0.6))):
        rr = r * k
        mat = vol_glow_soft(f"PlasmaVol{i}", col, st * (gas if i >= 2 else 1.0), rr, centre=c, noise=noisy,
                            scale=9.0 / rr)
        ob = single(f"PlasmaVol{i}", mat, lambda mb, rr=rr: mb.sphere(c, rr, 32))
        camera_only(ob)
        # the collector images the plasma: only the faint outer gas is mirrored, so the dish fills with a soft
        # turbulent violet (k3A) instead of a blown-out magnified core
        ob.visible_glossy = (i == 2) if mirror_core else (i == 3)   # R14: mirror the compact glow, not the haze
        obs.append(ob)
    li = K.point("PlasmaLight", c, energy, li_color, r * 0.8)
    li.visible_glossy = False                 # its magnified image in the dish was a white blob
    return obs, li


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
    # R4: a smooth, gently undulating disc (the R3 crown-splash read as wrong physics for a pre-pulse sheet)
    harm = [(k, rnd.uniform(0.006, 0.018), rnd.uniform(0, 6.28)) for k in (3, 5, 8, 13, 21)]

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
            h = thick(t) * (1 + 0.08 * math.sin(7 * a + 3 * t))
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
    for k in range(0, 30, 3):           # a few satellite droplets / short ligaments only
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
    # R4: a softbox the sheet mirrors, so liquid tin reads silver-bright instead of black plastic
    cv = Vector(c)
    # both cameras sit near (0.55, -0.6, 0.15): the sheet (normal X) mirrors the direction (0.55, +0.6, -0.15)
    sb = K.area(name + "Softbox", cv + Vector((0.42, 0.48, -0.1)), cv, 0.35, 0.28, (0.9, 0.93, 1.0))
    sb = bpy.data.objects.get(name + "Softbox")
    if sb is not None:
        sb.visible_camera = False
    return root, [ob, so]


# ---------------------------------------------------------------- variants
# R16 root cause #2: the single shapeless weak cool rim per variant (spherical point light, round soft highlight)
RIM_R16 = {"cold": dict(rim=(-0.25, 0.42, 0.5), rim_energy=90.0, rim_radius=0.25),
           "prepulse": dict(rim=(0.35, 0.6, 0.55), rim_energy=24.0, rim_radius=0.25),
           "contrast": dict(rim=(0.2, 0.9, 0.9), rim_energy=30.0),
           "track": dict(rim=(-0.5, 0.5, 0.6), rim_energy=14.0),
           "clean": dict(rim=(0.3, 0.9, 0.9), rim_energy=10.0, rim_radius=0.5),
           "spectrum": dict(rim=(-0.2, 0.9, 0.8), rim_energy=8.0)}


def build(variant="cold", shot=None):
    n = K.nframes(shot) if shot else 120
    sc = C.reset_scene(n)
    M = _mats()
    K.clean_cycles(sc)
    sc["hdri"] = "hangar_interior"
    sc["hdri_strength"] = 0.06
    sc["vignette"] = 0.35
    sc["film_grain"] = 0.1
    cam, tgt = K.camera("CamR2", lens=50)
    fn = {"cold": _cold, "prepulse": _prepulse, "contrast": _contrast, "track": _track, "clean": _clean_r6,
          "spectrum": _spectrum, "amps": _amps}[variant]
    fn(sc, M, cam, tgt, n)
    if variant != "amps":                         # R16 #2: gold control B1_22 (amps) keeps its R15 lighting
        import source_kit_r16 as SK
        SK.relight_r16(sc, **RIM_R16[variant])
    sc.camera = cam
    return sc


def _dark_world():
    C.set_world(top=(0.035, 0.045, 0.08), horizon=(0.02, 0.026, 0.05), bottom=(0.01, 0.012, 0.022))


def _cold(sc, M, cam, tgt, n):
    """A0_01: frames 72 / 160 / 246 of 290 = clean droplet / pancake + main pulse / plasma.
    R14: the pre-pulse moved later (hit1 68 -> 92) so the first beat is a clean mirror-silver droplet before the
    laser arrives (R13 review A0_01 #1; a hair for scale was tried and dropped - it filled the frame);
    liquid-tin / neutral-mirror metals + studio cards (root cause #6, review #2)."""
    _dark_world()
    _metals_r15(M)                                   # R15 #2 / #3: shared mirror collector + thin tin film
    chamber_r10(M, seed=7, tip_z=0.78, hide_front=away_from((0.6, -0.5)), r16=True)   # R16 #2: modules, no grid
    lights_chamber(1.0)
    r = 0.016
    hit1, hit2, boom = 92, 154, 166
    drop = single("Droplet", M["tin"], lambda mb: mb.sphere((0, 0, 0), r, 48))
    key_loc(drop, [(1, (0, 0, 0.3)), (hit1, (0, 0, 0.0))])
    show_between_vis(drop, 1, hit1 + 2)               # R14: the droplet now really falls into frame
    nxt = single("DropletNext", M["tin"], lambda mb: mb.sphere((0, 0, 0), r, 48))
    # R15: the next droplet stays well above the sheet's rim (R14: it sat on the face and read as a blob)
    key_loc(nxt, [(1, (0, 0, 0.62)), (n, (0, 0, 0.36))])
    root, parts = pancake_r15(M, (0, 0, 0), r)
    import source_kit_r16 as SK
    parts.append(SK.pancake_rim_r16(root, M["tin"], seed=3))     # R16 #2: thick rolled rim + flung droplets
    key_scale(root, [(hit1 + 2, r * 1.2), (hit2 - 6, r * 9.5), (hit2 + 4, r * 10.5)])
    for ob in parts:
        show_between(ob, hit1 + 3, boom - 1)
    beam_start = (COLL_X - 0.2, 0, 0)
    for ob in laser(M, beam_start, (0, 0, 0), 0.0025, "Pre"):
        show_between(ob, hit1 - 3, hit1 + 6)
    for ob in flash(M, (-0.01, 0, 0), r * 1.4):
        show_between(ob, hit1, hit1 + 5)
    # R15 (A0_01 review #1): main pulse = side-on soft orange cone covering the sheet, no disc spot on its centre
    mp = main_pulse_cone_r15((COLL_X - 0.2, 0, 0), (-0.012, 0, 0), 0.025, r * 9.0, "MainPulse")
    show_between(mp, hit2 - 4, boom)
    pl, li = plasma_r10(M, (0, 0, 0), 0.032, energy=0, li_color=PLASMA_LIGHT_R14)   # R10: volumetric core
    for ob in pl:
        show_between(ob, boom)
    key_scale(pl[3], [(boom, 0.4), (boom + 30, 1.0), (n, 1.15)])
    key_energy(li, [(boom - 1, 0), (boom, 45), (n, 55)])
    fl = K.point("LaserLight", (-0.05, -0.02, 0), 0, K.ORANGE, 0.02)
    key_energy(fl, [(hit1 - 1, 0), (hit1, 6), (hit1 + 6, 0), (hit2 - 1, 0), (hit2, 18), (hit2 + 9, 8), (boom, 0)])
    for f in (hit1 + 7, boom + 1):
        fl.data.energy = 0
        fl.data.keyframe_insert("energy", frame=f)
    # R14: studio reflections for the liquid tin (pancake faces +X; droplet is a sphere) - camera-invisible strips
    # R16 #2: no studio cards (the R14/R15 TinCards / DropCards were the square light strips in the tin); a faint
    # violet bounce from the previous droplet's plasma (50 kHz) off-frame, as in B1_10
    pg = K.point("PrevPlasmaGlowR16", (-0.3, 0.3, 0.25), 6.0, (0.7, 0.6, 1.0), 0.25)
    key_energy(pg, [(1, 6.0), (boom - 1, 6.0), (boom, 0.0)])
    cam.data.lens = 55
    cam.data.dof.use_dof = True
    cam.data.dof.aperture_fstop = 2.8
    foc = bpy.data.objects.new("FocusDrop", None)    # R14: focus rides on the falling droplet, then the sheet
    sc.collection.objects.link(foc)
    key_loc(foc, [(1, (0, 0, 0.3)), (hit1, (0, 0, 0.0))])
    cam.data.dof.focus_object = foc
    # R15 #3 (review A0_01 #1): pull back while the sheet spreads so it is ~1/3 of the frame, with the nozzle and
    # vessel wall in view for scale (R14: the sheet filled the frame, no scale)
    K.key_path(cam, tgt, [(1, (0.6, -0.42, 0.22), (0, 0, 0.12)), (hit1, (0.52, -0.4, 0.12), (0, 0, 0.0)),
                          (n, (0.62, -0.62, 0.16), (-0.05, 0, 0.02))])
    cam.data.keyframe_insert("lens", frame=hit1 + 6)      # lens 55 on the droplet ...
    cam.data.lens = 24                                    # ... widens as the sheet spreads (camera stays clear of
    cam.data.keyframe_insert("lens", frame=hit2 - 12)     # the vessel wall): sheet ~1/3 of the frame + nozzle in view
    cam.data.keyframe_insert("lens", frame=boom + 4)
    cam.data.lens = 40                                    # back in on the plasma for the last beat
    cam.data.keyframe_insert("lens", frame=boom + 50)
    K.anchors("A0_01", _rim_markers(root))


def _prepulse(sc, M, cam, tgt, n):
    """B1_10: frames 32 / 69 / 107 of 126: thin pre-pulse hits, the sheet spreads, the next droplet for scale.
    R14: (review B1_10 #2) the camera moved to the laser's side of the sheet (x < 0), so the face that catches the
    pulse - and the beam coming out of the collector hole behind it - are seen together; (root cause #6 / review
    #1) the sheet is liquid tin with ripples and studio reflections, the collector a neutral mirror."""
    _dark_world()
    _metals_r15(M)                                   # R15 #2 / #3
    # R15 (review B1_10 #3 "square panel grid repeated"): wall hardware (hoses, H2 nozzles, gauges) instead of liner
    chamber_r10(M, seed=8, tip_z=0.42, hide_front=away_from((-0.5, -0.65)), liner=False, r16=True)
    lights_chamber(1.0)
    r = 0.014
    hit = 30
    drop = single("Droplet", M["tin"], lambda mb: mb.sphere((0, 0, 0), r, 48))
    key_loc(drop, [(1, (0, 0, 0.06)), (hit, (0, 0, 0))])
    show_between(drop, 1, hit + 2)
    nxt = single("DropletNext", M["tin"], lambda mb: mb.sphere((0, 0, 0), r, 48))
    key_loc(nxt, [(1, (0, 0, 0.36)), (n, (0, 0, 0.27))])   # R15: stays above the rim (R14: on the face)
    root, parts = pancake_r15(M, (0, 0, 0), r)
    import source_kit_r16 as SK
    parts.append(SK.pancake_rim_r16(root, M["tin"], seed=4))     # R16 #2: thick rolled rim + flung droplets
    key_scale(root, [(hit + 2, r * 1.2), (hit + 40, r * 9.0), (n, r * 12.0)])
    for ob in parts:
        show_between(ob, hit + 3)
    for ob in laser(M, (COLL_X - 0.2, 0, -0.02), (0, 0, 0), 0.0022, "Pre"):
        show_between(ob, hit - 6, hit + 8)
    for ob in flash(M, (-0.008, 0, 0), r * 1.3):
        show_between(ob, hit, hit + 5)
    fl = K.point("LaserLight", (-0.05, -0.02, 0), 0, K.ORANGE, 0.02)
    key_energy(fl, [(hit - 1, 0), (hit, 7), (hit + 8, 0)])
    # R16 #2: no studio cards; a faint violet afterglow of the previous droplet's plasma (50 kHz) off-frame
    K.point("PrevPlasmaGlowR16", (-0.22, 0.36, 0.08), 1.2, (0.7, 0.6, 1.0), 0.25)
    cam.data.lens = 30                            # R15 #3: wider -> sheet about 1/2 frame height, wall for scale
    cam.data.dof.use_dof = True
    cam.data.dof.aperture_fstop = 4
    cam.data.dof.focus_object = tgt
    # R15 #3: pulled back (~1/3 frame) so the nozzle / wall give scale; the 300 um dimension line rides on anchors
    K.key_path(cam, tgt, [(1, (-0.52, -0.6, 0.12), (-0.03, 0, 0.05)), (n, (-0.48, -0.72, 0.15), (-0.02, 0, 0.06))])
    K.anchors("B1_10", _rim_markers(root))


def _debris(M, seed=4):
    rnd = random.Random(seed)
    objs = []
    for key, cnt, rr in (("hot", 8, (0.004, 0.007)), ("warm", 16, (0.003, 0.006)), ("cool", 40, (0.003, 0.006))):
        mb = K.MB()
        for _ in range(cnt):
            v = Vector((rnd.gauss(0, 1), rnd.gauss(0, 1), rnd.gauss(0, 1))).normalized()
            d = {"hot": rnd.uniform(0.08, 0.25), "warm": rnd.uniform(0.2, 0.45), "cool": rnd.uniform(0.35, 0.7)}[key]
            p = v * d
            # R15 (review B1_15 #3 "equal white sticks read as snow / floating dots"): tapered motion streaks -
            # thick head outward, thread-thin tail back towards the plasma, random lengths
            ln_ = rnd.uniform(0.02, 0.06)
            mb.tube(p, p - v * ln_, rnd.uniform(*rr) * 0.4, seg=6, r2=rnd.uniform(*rr) * 0.04)
        ob = mb.obj("Debris_" + key, M[key])
        ob.visible_shadow = False
        ob.visible_glossy = False          # R15: no magnified white crescents of the streaks in the dish
        objs.append(ob)
    return objs


def _radial_sheen(m, centre, edge):
    """Emission strength falls off from the dish axis (world Y/Z distance) to the rim: brightest where the
    plasma's light is strongest."""
    nt = m.node_tree
    b = next(nd for nd in nt.nodes if nd.type == "BSDF_PRINCIPLED")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sp = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sp.inputs[0])
    cb = nt.nodes.new("ShaderNodeCombineXYZ")
    nt.links.new(sp.outputs["Y"], cb.inputs["Y"])
    nt.links.new(sp.outputs["Z"], cb.inputs["Z"])
    ln = nt.nodes.new("ShaderNodeVectorMath")
    ln.operation = "LENGTH"
    nt.links.new(cb.outputs[0], ln.inputs[0])
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = 0.05
    mr.inputs["From Max"].default_value = COLL_R
    mr.inputs["To Min"].default_value = centre
    mr.inputs["To Max"].default_value = edge
    mr.interpolation_type = "SMOOTHSTEP"
    nt.links.new(ln.outputs["Value"], mr.inputs["Value"])
    nt.links.new(mr.outputs["Result"], b.inputs["Emission Strength"])


def _wall_parts_r12(P, sm, R, skip, rnd):
    """R12 (R11 review B1_15 / B1_08: "the wall is one square metal panel repeated" / "a dark flat plate"): k3A
    vessel hardware instead of liner panels - circumferential coolant hose bundles with clamps, rows of hydrogen
    gas inlet nozzles (flange + feed tube + nozzle tip aimed at the collector region), vacuum gauge heads on short
    CF stubs, vertical cable trays with harnesses, machined pad plates under each group."""
    import hero_kit_r10 as H

    def wp(a, z, inset=0.0):
        return Vector((math.cos(a) * (R - 0.04 - inset), math.sin(a) * (R - 0.04 - inset), z))
    for zc, k_ in ((-1.15, 5), (-0.78, 4), (-0.42, 4), (0.18, 3), (0.52, 4), (0.86, 5), (1.2, 4)):            # coolant hose rings (arcs)
        a0 = rnd.uniform(0, 2 * math.pi)
        pts = [wp(a0 + i * 0.12, zc, 0.06) for i in range(26)]
        segs, cur = [], []
        for q in pts:
            if skip(q):
                if len(cur) > 2:
                    segs.append(cur)
                cur = []
            else:
                cur.append(q)
        if len(cur) > 2:
            segs.append(cur)
        for sg in segs:
            mid = sg[len(sg) // 2]
            H.cooling_bundle(P, sg, k=k_, r=0.011, clamp_every=0.28, up=(-mid.x, -mid.y, 0), block=False)
    for k in range(22):                                                        # H2 gas inlet nozzles
        a = rnd.uniform(0, 2 * math.pi)
        z = rnd.choice((-0.62, -0.25, 0.0, 0.28, 0.66))
        b = wp(a, z)
        if skip(b):
            continue
        d = (-b).normalized()
        H._ring(P["alu"], b + d * 0.01, d, 0.05, 0.02, 0.025, seg=24)
        H._bolt_circle(P, b + d * 0.025, d, 0.04, 6, 0.005, 0.008, nuts=False)
        P["steel"].tube(b + d * 0.02, b + d * 0.16, 0.014, seg=12)
        P["steel"].tube(b + d * 0.16, b + d * 0.2, 0.014, seg=12, r2=0.005)      # nozzle tip
        P["steel"].tube(b + Vector((0, 0, 0.012)), b + Vector((0, 0, 0.3)), 0.006, seg=8)   # feed line
        sm.box(b - d * 0.005, (0.08, 0.08, 0.08))                                # pad plate
    for k in range(16):                                                        # vacuum gauge heads
        a = rnd.uniform(0, 2 * math.pi)
        z = rnd.uniform(-1.0, 1.0)
        b = wp(a, z)
        if skip(b):
            continue
        d = (-b).normalized()
        H._ring(P["alu"], b + d * 0.01, d, 0.045, 0.02, 0.02, seg=24)
        P["steel"].tube(b + d * 0.01, b + d * 0.09, 0.02, seg=16)
        P["anod"].box(b + d * 0.13, (0.07, 0.07, 0.09))
        P["screen"].box(b + d * 0.166, (0.035, 0.002, 0.02))
        P["cable_k"].path([b + d * 0.13 + Vector((0, 0, 0.045)), b + d * 0.06 + Vector((0, 0, 0.12)),
                           b + Vector((0, 0, 0.4))], 0.005, seg=6)
    for k in range(7):                                                         # vertical cable trays
        a = rnd.uniform(0, 2 * math.pi)
        pts = [wp(a, -1.3 + i * 0.26, 0.03) for i in range(11)]
        if any(skip(q) for q in pts):
            continue
        for q in pts[::2]:
            d = (-q).normalized()
            P["alu_dark"].box(q, (0.09 * abs(d.y) + 0.01, 0.09 * abs(d.x) + 0.01, 0.02))
        H.cable_harness(P, [q + (-q).normalized() * 0.02 for q in pts], n=6, r=0.006, connector=False)


def _debris_r16(M, seed=4):
    """R16 #1 (R15 review B1_15 #2: white fly-lines read as HUD noise): debris = dark tin specks (silhouettes against
    the glow) plus a few faint-orange hot specks, each a short tapered trail pointing away from the plasma."""
    rnd = random.Random(seed)
    M.setdefault("deb_dark", K.mat("DebrisDarkR16", (0.06, 0.06, 0.065), metal=0.6, rough=0.5))
    M.setdefault("deb_hot", K.emit_mat("DebrisHotR16", (1.0, 0.55, 0.28), 1.6))
    objs = []
    for key, cnt, rr, (d0, d1) in (("deb_dark", 34, (0.0025, 0.004), (0.08, 0.38)),
                                   ("deb_hot", 12, (0.0018, 0.003), (0.06, 0.25))):
        mb = K.MB()
        for _ in range(cnt):
            v = Vector((rnd.gauss(0, 1), rnd.gauss(0, 1), rnd.gauss(0, 1))).normalized()
            if v.x < -0.3:                  # nothing behind the plasma towards the dish centre
                v.x = -v.x
            p = v * rnd.uniform(d0, d1)
            r0 = rnd.uniform(*rr)
            mb.sphere(tuple(p), r0, 8)
            mb.tube(p, p - v * rnd.uniform(0.012, 0.03), r0 * 0.8, seg=6, r2=r0 * 0.08)
        ob = mb.obj("DebrisR16_" + key, M[key])
        ob.visible_shadow = False
        ob.visible_glossy = False
        objs.append(ob)
    return objs


def _contrast(sc, M, cam, tgt, n):
    """B1_15 (36 frames). R16 root cause #1 (R15: 20 deg off-axis camera -> no mirror face, H1): camera near the
    collector's optical axis, in front of the dish: a deep ellipsoidal collector whose first focus IS the plasma
    site fills the frame (>= 1/3), its polished face full of the plasma's glow, the central hole beside the plasma
    by a small parallax, the bolted flange cropped at the frame edges / a defocused foreground port flange; debris =
    dark / faint-orange specks with short trails; no cyan dashed axis, no white fly-lines; one leader to the mirror.
    Not repeating: the R15 20 deg off-axis camera."""
    _dark_world()
    import mirror_r15 as MR
    import source_kit_r16 as SK
    _metals_r15(M, coll_rough=0.004)
    coll_m = MR.ml_mirror("CollectorML_R16", rough=0.035)        # soft spread of the plasma glow, no rainbow

    def hide(p):                                  # only the wall right behind the camera is cleared: the rest of the
        return p[0] > 0.85 and abs(p[1]) < 0.7 and abs(p[2]) < 0.7      # vessel is what the mirror reflects
    chamber_r10(M, seed=12, tip_z=0.4, diag=[], hide_front=lambda p: p[0] > 0.1 or hide(p),
                wall_skip=hide, collector=False, r16=True)   # no end-on barrels from the camera side
    objs, rim_x = SK.collector_r16(M, coll_m)
    pl, li = plasma_r10(M, (0, 0, 0), 0.04, energy=70.0, gas=1.0, li_color=PLASMA_LIGHT_R14, mirror_core=False)
    key_energy(li, [(1, 220), (n, 260)])          # the plasma is the light source of the chamber
    for ob in pl:                                 # R16 smoke: the mirrored glow volumes were a big off-centre fog blob
        ob.visible_glossy = False
    tight = single("PlasmaMirrorGlowR16", vol_glow_soft("PlasmaMirrorGlowR16M", (0.8, 0.7, 1.0), 14.0, 0.03),
                   lambda mb: mb.sphere((0, 0, 0), 0.03, 24))
    camera_only(tight, glossy=True)               # only the dish sees it: a tight glow reflection near the centre
    # the polished outer rim catches the plasma as one continuous bright elliptical edge ("inside a bowl")
    rim_li = K.point("PlasmaRimGlintR16", (0, 0, 0), 260.0, PLASMA_LIGHT_R14, 0.05)
    SK.rim_lip_r16(M, objs, rim_x, rim_li)
    for ob in _debris_r16(M):
        key_scale(ob, [(1, 0.6), (n, 1.15)], interp="LINEAR")
    K.anchors("B1_15", {"coll": Vector((-0.276, -0.3, 0.32)), "plasma": Vector((0, 0, 0))})   # on the lit mirror face
    cam.data.lens = 21
    cam.data.dof.use_dof = True
    cam.data.dof.aperture_fstop = 2.2
    foc = bpy.data.objects.new("Focus", None)
    sc.collection.objects.link(foc)
    foc.location = (-0.12, 0.05, 0.0)
    cam.data.dof.focus_object = foc
    K.key_path(cam, tgt, [(1, (1.2, -0.1, 0.07), (-0.3, 0.0, 0.0)), (n, (1.08, -0.09, 0.06), (-0.3, 0.0, 0.0))],
               interp="BEZIER")


def _track(sc, M, cam, tgt, n):
    """B1_08 (92 frames): droplets fall past a lock line at z = 0; each carries its own cyan reticle that
    thickens while that droplet is locked."""
    _dark_world()
    _metals_r15(M)                                # R15 #2: shared mirror collector; liquid-tin droplets
    # R10: k3A metal vessel; the droplet generator nozzle is in frame (tip at z = 0.13), two droplet cameras on
    # the back wall aim at the lock line, a lit illumination window between them, the collector rim at the left
    tip_z = 0.13
    front = away_from((0.0, -0.7), 0.3)

    def hide(p):                                  # also keep the wall straight behind the droplet line calm
        a = math.degrees(math.atan2(p[1], p[0]))
        return front(p) or (lim[0] < a < lim[1] and -0.55 < p[2] < 0.5)
    lim = (68, 112)

    def hide_wall(p):                             # R12: wall hardware may come closer to the droplet line
        a = math.degrees(math.atan2(p[1], p[0]))
        return front(p) or (82 < a < 98 and -0.55 < p[2] < 0.5)
    chamber_r10(M, seed=3, tip_z=tip_z, diag=[(60, 0.1), (120, 0.1)], hide_front=hide, liner=False, wall_skip=hide_wall,
                r16=True)
    import hero_kit_r10 as H
    Pw = H.new_parts()                            # the illumination window low on the back wall
    H.flange_viewport(Pw, (0.0, CHAMBER_R - 0.04, -0.3), (0, -1, 0), 0.08, nipple=0.06, side_port=False)
    # R14 (review B1_08 #2: "the back plate is a flat empty wall"): vacuum-vessel hardware on the back wall - a
    # big CF viewport with its bolt circle, a blank flange, a horizontal coolant manifold with clamps - softened
    # by a shallow depth of field (layered, not a flat wall)
    H.flange_viewport(Pw, (0.42, CHAMBER_R - 0.11, 0.3), Vector((-0.32, -1, 0)).normalized(), 0.13, nipple=0.05,
                      side_port=True)
    H.flange_viewport(Pw, (-0.48, CHAMBER_R - 0.14, -0.05), Vector((0.36, -1, 0)).normalized(), 0.1, nipple=0.04,
                      side_port=False)
    for zc in (-0.52, -0.6):
        H.cooling_bundle(Pw, [Vector((math.cos(math.radians(a)), math.sin(math.radians(a)), 0)) * (CHAMBER_R - 0.12)
                              + Vector((0, 0, zc)) for a in range(55, 128, 8)], k=3, r=0.012, clamp_every=0.22,
                         up=(0, -1, 0), block=False)
    H.finish(Pw, M, "IllumPort")
    # R14 (review B1_08 #1: "the horn-shaped parts are unreadable"): the two diagnostic barrels become droplet
    # cameras - a box body, a lens hood with a coated front element, a ring of status LEDs - each with a faint
    # cyan sight cone to the lock point, so it is visible who takes the picture
    cb, hood, lens, leds, cone = K.MB(), K.MB(), K.MB(), K.MB(), K.MB()
    for az in (60, 120):
        a = math.radians(az)
        base = Vector((math.cos(a) * (CHAMBER_R - 0.04), math.sin(a) * (CHAMBER_R - 0.04), 0.1))
        d = (-base).normalized()
        tip = base + d * (base.length - 0.42)
        q = Vector((0, 0, 1)).rotation_difference(d).to_euler()
        cb.box(base + d * 0.36, (0.15, 0.13, 0.2), rot=q)
        hood.tube(tip - d * 0.035, tip + d * 0.045, 0.04, seg=32, r2=0.05)
        lens.cyl(tip + d * 0.005, 0.034, 0.008, rot=q, seg=32)
        Rm = q.to_matrix()
        for k in range(10):
            t = 2 * math.pi * k / 10
            leds.sphere(tip - d * 0.03 + Rm @ Vector((math.cos(t) * 0.046, math.sin(t) * 0.046, 0)), 0.0035, 6)
        cone.tube(tip + d * 0.05, Vector((0, 0, 0.0)) - d * 0.03, 0.026, seg=24, r2=0.003)
    cb.obj("DropCamBodies", M["anod"], bevel=0.006)
    hood.obj("DropCamHoods", M["alu_dark"], bevel=0.002)
    lens.obj("DropCamLens", K.mat("DropCamCoated", (0.05, 0.08, 0.12), metal=0.0, rough=0.02, coat=1.0, spec=1.0))
    led_o = leds.obj("DropCamLEDs", K.emit_mat("DropCamLED", (0.45, 1.0, 0.65), 5.0))
    led_o.visible_shadow = False
    cone_o = cone.obj("DropCamSight", K.emit_mat("DropCamSightInk", K.CYAN, 0.5, halo=0.07))
    camera_only(cone_o)
    win = K.MB()
    win.cyl((0.0, CHAMBER_R - 0.11, -0.3), 0.05, 0.004, rot=(math.radians(90), 0, 0), seg=40)
    wo = win.obj("IllumWindow", K.emit_mat("IllumWindowGlow", (0.8, 0.88, 1.0), 6.0))
    wo.visible_shadow = False
    K.point("IllumLight", (0.0, 1.05, -0.25), 4.0, (0.8, 0.88, 1.0), 0.06)
    # the next step: the laser's pending path, dim orange dashes from the collector hole to the lock point
    dsh = K.MB()
    for k in range(14):
        x0 = COLL_X + 0.05 + k * 0.06
        if x0 + 0.03 < -0.04:
            dsh.tube((x0, 0.0, 0.0), (x0 + 0.03, 0.0, 0.0), 0.0018, seg=8)
    do = dsh.obj("PendingLaser", K.emit_mat("PendingLaserInk", K.ORANGE, 3.0))
    camera_only(do)
    lights_chamber(0.8)
    r = 0.016                                 # R10: bigger droplets (R9: "too small, read as dust")
    sp, v = 0.13, 0.0042                      # spacing (m), speed (m / frame)
    rot = (math.radians(90), 0, 0)            # rings face the camera (camera looks along +Y)
    for i in range(8):
        z0 = 0.36 + i * sp - 0.2
        d = single(f"Drop{i}", M["tin"], lambda mb: mb.sphere((0, 0, 0), r, 32))
        key_loc(d, [(1, (0, 0, z0)), (n, (0, 0, z0 - v * (n - 1)))])
        fe = round(1 + (z0 - (tip_z - 0.025)) / v)              # emerges from the nozzle
        if fe > n:
            d.hide_render = True
        elif fe > 1:
            show_from(d, fe)
        ret = K.MB()
        ret.ring((0, 0, 0), r * 3.08, r * 3.0, 0.001, rot=rot, seg=64)
        for sx, sz in ((1, 0), (-1, 0), (0, 1), (0, -1)):      # crosshair ticks
            ret.box((sx * r * 2.3, 0, sz * r * 2.3), (r * 0.9 if sx else r * 0.05, 0.001, r * 0.9 if sz else r * 0.05))
        for k in range(4):                    # corner brackets
            a = math.radians(45 + 90 * k)
            cx, cz = math.cos(a) * r * 4.3, math.sin(a) * r * 4.3
            ret.box((cx - math.copysign(r * 0.5, cx), 0, cz), (r * 1.1, 0.001, r * 0.07))
            ret.box((cx, 0, cz - math.copysign(r * 0.5, cz)), (r * 0.07, 0.001, r * 1.1))
        ro = ret.obj(f"Ret{i}", M["reticle"])
        ro.parent = d
        ro.location = (0, -0.03, 0)
        ro.visible_shadow = False
        if fe > n:
            ro.hide_render = True
        elif fe > 1:
            show_from(ro, fe)
        lk = single(f"Lock{i}", M["reticle_lock"], lambda mb: mb.ring((0, 0, 0), r * 3.5, r * 3.38, 0.001, rot=rot, seg=64))
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
    cam.data.dof.use_dof = True                   # R14: shallow depth of field -> wall reads as layered depth
    cam.data.dof.aperture_fstop = 3.2
    cam.data.dof.focus_object = tgt
    # R7 (D): an arc around the droplet line so the chamber wall slides behind the drops (R6 read as static)
    K.key_path(cam, tgt, [(1, (0.2, -0.72, 0.08), (0, 0, 0.045)), (n, (-0.18, -0.64, 0.0), (0, 0, 0.03))],
               interp="LINEAR")


def _clean(sc, M, cam, tgt, n):
    """B2_08 (242 frames): across the collector surface: grey tin deposits on the mirror, the plasma's violet
    glow reflected in it; the camera slides over the dish towards its rim."""
    _dark_world()
    # R4 (H6 fix): a bright polished multilayer dish (the R3 dark dish read as night sky with the deposits as stars)
    # R5: satin sheen (rough 0.16) so the lights read on the dish instead of a black mirror of the dark chamber
    M["coll"] = K.mat("CollectorMLPolished", (0.7, 0.68, 0.78), metal=1.0, rough=0.16, coat=0.8)
    M["tin_dep"] = K.mat("TinDepositDull", (0.42, 0.43, 0.45), metal=1.0, rough=0.6, speck=0.4)
    for ob in chamber(M, seed=5):                  # R5: no gold MLI patches in the dish's reflection
        if ob.name.startswith("MLI"):
            ob.hide_render = True
    lights_chamber(0.7)
    pl, li = plasma(M, (0, 0, 0), 0.025)
    for ob in pl[1:]:
        ob.visible_glossy = True                    # the mirror shows the violet glow
    key_energy(li, [(1, 35), (n, 35)])
    K.area("Graze", (-0.35, -0.75, -0.25), (-0.85, 0.1, 0.15), 0.5, 30, (0.85, 0.88, 1.0))
    K.area("DishSoftbox", (0.75, -0.55, 0.95), (-0.85, 0.05, 0.05), 1.1, 70, (0.88, 0.9, 1.0), size_y=0.5)
    rnd = random.Random(8)
    dep, film = K.MB(), K.MB()
    for _ in range(380):
        rr = math.sqrt(rnd.uniform(0.12 ** 2, 0.64 ** 2))
        a = rnd.uniform(0, 2 * math.pi)
        y, z = rr * math.cos(a), rr * math.sin(a)
        s = rnd.uniform(0.0015, 0.0035) * (1.8 if rnd.random() < 0.06 else 1)
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
    hz = K.MB()                                     # faint hydrogen-plasma glow hugging the dish (F28)
    hz.sphere((COLL_X + 0.25, 0.1, 0.1), 0.42, 32)    # R5: much fainter (R4 read as a flat blue disc)
    hob = hz.obj("H2Glow", vol_glow("H2GlowM", (0.62, 0.55, 1.0), 0.025))
    camera_only(hob)
    K.anchors("B2_08", {"dep": Vector((coll_x(0.32), 0.05, 0.31)), "dish": Vector((coll_x(0.5), 0.35, -0.3))})
    dep2 = film.obj("TinFilm", M["tin_dep"])
    cam.data.lens = 35
    cam.data.dof.use_dof = True
    cam.data.dof.aperture_fstop = 11                # R5: the dish reads as a mirror: rim, bolts and highlight in
    cam.data.dof.focus_object = tgt                 # frame, sharper, and a slow push towards the deposits
    K.key_path(cam, tgt, [(1, (0.05, -0.72, 0.5), (-0.8, 0.04, 0.08)), (n, (-0.32, -0.5, 0.45), (-0.84, 0.1, 0.1))],
               interp="LINEAR")


def _clean_r6(sc, M, cam, tgt, n):
    """B2_08 R6. R5 review: the camera sat so close to the dish that the hole collar read as an unknown "small
    ring" and the frame was a static star field. Now the whole collector is the macro anchor: a 3/4 view of the
    polished dish (rim + bolt circle + central hole + cooling back) with the plasma site in front, then a slow
    push onto one deposit patch (the magnifier's anchor). Tin -> SnH4 leaves the dish along visible streamlines
    towards a pump port in the vessel wall, so the macro frame moves with the chemistry."""
    from mathutils import Matrix
    _dark_world()
    # R14 (root cause #6, review B2_08 #2): neutral, high-reflectance multilayer mirror (was violet-grey satin)
    _metals_r15(M, coll_rough=0.07)                  # R15 #2: shared mirror_r15 collector; a touch of polish
    # haze so the softboxes read as soft highlights on the metal (R14: "dark-blue matte plate, not a mirror")
    M["tin_dep"] = K.mat("TinDepositDull", (0.16, 0.16, 0.17), metal=0.5, rough=0.8, speck=0.5)
    for ob in chamber(M, seed=5):
        if ob.name.startswith("MLI"):
            ob.hide_render = True
    lights_chamber(0.45)
    pl, li = plasma(M, (0, 0, 0), 0.022, li_color=PLASMA_LIGHT_R14)
    for ob in pl[1:]:
        ob.visible_glossy = True
    for ob in pl:                     # R14 (review B2_08 #1): the off-dish violet ball read as a second plasma -
        ob.visible_camera = False     # only its soft violet reflection in the mirror remains
    pl[0].visible_glossy = False      # the magnified white core was a blown wedge over the deposits in the true mirror
    li.visible_glossy = False
    key_energy(li, [(1, 30), (n, 30)])
    # soft, camera-invisible panels for the dish to reflect (a mirror of a dark room reads as night sky)
    for nm, loc, tg, sz, e in (("DishSoftA", (0.6, -0.9, 0.9), (-0.8, 0, 0), 1.0, 5),     # R14: 14 -> 5 (mirror)
                                ("DishSoftB", (0.5, 0.9, -0.7), (-0.8, 0, 0), 0.8, 6),
                                ("Graze", (-0.3, -1.0, -0.2), (-0.85, 0.1, 0.15), 0.5, 10)):
        lo = K.area(nm, loc, tg, sz, e, (0.88, 0.9, 1.0))
        if nm == "DishSoftB":       # R14: in the true mirror its image was a blown white wedge over the deposits
            lo.visible_glossy = False
    # pump port in the vessel wall (upper back): big flange, bolt circle, grille, pipe stub out of the wall
    a_p, z_p = math.radians(124), 0.5
    nrm_p = Vector((-math.cos(a_p), -math.sin(a_p), 0))
    port = Vector((math.cos(a_p), math.sin(a_p), 0)) * (CHAMBER_R - 0.02) + Vector((0, 0, z_p))
    q = Vector((0, 0, 1)).rotation_difference(nrm_p).to_euler()
    pf, pg, pb = K.MB(), K.MB(), K.MB()
    pf.ring(port + nrm_p * 0.03, 0.26, 0.17, 0.06, rot=q, seg=64)
    pb.bolts(port + nrm_p * 0.065, 0.22, 16, 0.01, 0.016, rot=q)
    # R14 (review B2_08 #2: "the pump port is just a striped window"): a turbomolecular pump inlet - splinter
    # guard ring + spokes, a spinning rotor of 18 pitched blades around a hub, built in local space on a pivot
    pf.ring(port + nrm_p * 0.045, 0.172, 0.16, 0.012, rot=q, seg=64)
    for k in range(6):
        t = math.pi * k / 6
        pf.box(port + nrm_p * 0.045, (0.33 * abs(math.cos(t)) + 0.006, 0.33 * abs(math.sin(t)) + 0.006, 0.006),
               rot=(q.to_matrix() @ Matrix.Rotation(t, 3, "Z")).to_euler())
    pivot = bpy.data.objects.new("PumpRotorPivot", None)
    sc.collection.objects.link(pivot)
    pivot.location = port + nrm_p * 0.015
    pivot.rotation_euler = q
    for k in range(18):
        t = 2 * math.pi * k / 18
        pg.box((math.cos(t) * 0.1, math.sin(t) * 0.1, 0), (0.12, 0.03, 0.004),
               rot=(Matrix.Rotation(t, 3, "Z") @ Matrix.Rotation(math.radians(35), 3, "X")).to_euler())
    pg.cyl((0, 0, 0.004), 0.045, 0.03, seg=32)
    rotor = pg.obj("PumpRotor", M["alu"], bevel=0.001)
    rotor.parent = pivot
    rotor.rotation_euler = (0, 0, 0)
    rotor.keyframe_insert("rotation_euler", frame=1)
    rotor.rotation_euler = (0, 0, math.radians(2.2 * n))
    rotor.keyframe_insert("rotation_euler", frame=n)
    for fc in C.fcurves(rotor.animation_data.action):
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR"
    K.point("PumpInnerLight", port - nrm_p * 0.05, 0.6, (0.85, 0.9, 1.0), 0.05)     # rims the blades
    pf.obj("PumpFlange", M["alu"], bevel=0.003)
    pb.obj("PumpBolts", M["steel"])
    bore = K.MB()
    bore.cyl(port - nrm_p * 0.01, 0.17, 0.01, rot=q, seg=48)
    bore.obj("PumpBore", M["hole"])
    # tin deposits: fewer, flatter, dull, concentrated in a band the camera ends on
    rnd = random.Random(8)
    dep = K.MB()
    for _ in range(260):
        rr = math.sqrt(rnd.uniform(0.14 ** 2, 0.64 ** 2))
        a = rnd.uniform(0, 2 * math.pi)
        if rnd.random() < 0.45:
            a = rnd.gauss(math.radians(80), 0.35)
            rr = rnd.uniform(0.22, 0.45)
        y, z = rr * math.cos(a), rr * math.sin(a)
        s = rnd.uniform(0.002, 0.0045)
        nrm = Vector((1, -y / (2 * COLL_F), -z / (2 * COLL_F))).normalized()
        p = Vector((coll_x(rr), y, z)) + nrm * 0.0006
        dep.cyl_m(Matrix.Translation(p) @ Vector((0, 0, 1)).rotation_difference(nrm).to_matrix().to_4x4(),
                  s, s * 0.35, seg=12)
    dep.obj("TinDeposits", M["tin_dep"])
    # SnH4 streamlines: lift off the dish along its normal, arc towards the pump; faint lines + moving flecks
    trail_m = K.emit_mat("SnH4Trail", (0.66, 0.7, 0.86), 0.45, halo=0.35)   # R16: faint (R15: wire birdcage)
    fleck_m = K.emit_mat("SnH4Fleck", (0.85, 0.88, 0.95), 4.0)
    tr = K.MB()
    paths = []
    for i in range(9):
        rr = 0.22 + 0.03 * i
        a = math.radians(55 + 7 * i)
        y, z = rr * math.cos(a), rr * math.sin(a)
        nrm = Vector((1, -y / (2 * COLL_F), -z / (2 * COLL_F))).normalized()
        p0 = Vector((coll_x(rr), y, z))
        p1 = p0 + nrm * 0.18
        p3 = port + nrm_p * 0.06 + Vector((0, 0, (i - 4) * 0.02))
        p2 = p1.lerp(p3, 0.5) + Vector((0.12, 0, 0.18))
        pts = []
        for k in range(17):
            u = k / 16
            pts.append((1 - u) ** 3 * p0 + 3 * (1 - u) ** 2 * u * p1 + 3 * (1 - u) * u * u * p2 + u ** 3 * p3)
        paths.append(pts)
        tr.path(pts, 0.0012, seg=6)
    tob = tr.obj("SnH4Lines", trail_m)
    camera_only(tob)
    for i, pts in enumerate(paths):
        for j in range(2):
            fl = K.MB()
            fl.sphere((0, 0, 0), 0.008, 10)
            ob = fl.obj(f"SnH4_{i}_{j}", fleck_m)
            camera_only(ob)
            start = 1 + (i * 23 + j * 110) % max(1, n - 60)
            dur = 85
            keys = []
            for k in range(0, 17, 2):
                f = start + dur * k / 16
                if f <= n + 40:
                    keys.append((round(f), tuple(pts[k])))
            key_loc(ob, keys)
            key_scale(ob, [(1, 0.0), (start - 1, 0.0), (start, 1.0), (start + dur - 2, 1.0),
                           (start + dur, 0.0)], interp="CONSTANT")
    hz = K.MB()
    hz.sphere((COLL_X + 0.3, 0.0, 0.1), 0.5, 32)
    hob = hz.obj("H2Glow", vol_glow("H2GlowM", (0.62, 0.55, 1.0), 0.015))
    camera_only(hob)
    dep_pt = Vector((coll_x(0.33), 0.33 * math.cos(math.radians(80)), 0.33 * math.sin(math.radians(80))))
    K.anchors("B2_08", {"dep": dep_pt, "dish": Vector((coll_x(0.6), -0.45, -0.38)), "pump": port + nrm_p * 0.06,
                        "rim": Vector((coll_x(COLL_R), -COLL_R * 0.7, -COLL_R * 0.7))})
    cam.data.lens = 20
    cam.data.dof.use_dof = True
    cam.data.dof.aperture_fstop = 5.6
    cam.data.dof.focus_object = tgt
    K.key_path(cam, tgt, [(1, (0.55, -0.98, 0.28), (-0.72, 0.05, 0.08)),
                          (n, (0.05, -0.66, 0.36), (-0.8, 0.07, 0.24))], interp="BEZIER")


def _spectrum(sc, M, cam, tgt, n):
    """B1_18 (194 frames): R4 (H14 fix): the real source chamber behind the spectrum HUD: polished collector dish
    and the plasma on the right half, softly out of focus (f/2.8) but recognisable; the HUD sits on the left."""
    _dark_world()
    # R14 (root cause #6): neutral mirror collector; (R13 frames: the plasma was a hard white disc = "floating white
    # dot") the soft volumetric k3A core of B1_15 instead, light near-neutral so the vessel metal is not tinted
    _metals_r15(M, coll_rough=0.008)                 # R15 #2: shared mirror_r15 collector
    chamber(M, seed=6)
    lights_chamber(0.55)
    pl, li = plasma_r10(M, (0, 0, 0), 0.04, energy=40.0, gas=1.3, li_color=PLASMA_LIGHT_R14, mirror_core=True)
    # R6 (D): the plasma pulses (50 kHz shown as a slow shimmer) instead of a constant glow
    rk = random.Random(18)
    key_energy(li, [(f, 32 + 22 * rk.random()) for f in range(1, n + 1, 4)])
    for ob in pl:
        if ob.type == "MESH":
            key_scale(ob, [(f, 0.85 + 0.3 * rk.random()) for f in range(1, n + 1, 6)])
    K.area("CollSoftbox", (0.2, -1.0, 0.75), (-0.75, 0.0, 0.0), 0.7, 30, (0.85, 0.9, 1.0))
    cam.data.lens = 26
    cam.data.dof.use_dof = True
    cam.data.dof.aperture_fstop = 2.8
    foc = bpy.data.objects.new("Focus", None)
    sc.collection.objects.link(foc)
    foc.location = (0.0, 0.0, 0.0)
    cam.data.dof.focus_object = foc
    # R6 (D): a real push towards the plasma with a slight arc (R5: three near-identical frames)
    K.key_path(cam, tgt, [(1, (0.7, -0.56, 0.2), (-0.49, -0.08, 0.0)), (n, (0.42, -0.4, 0.1), (-0.5, 0.02, -0.02))],
               interp="LINEAR")


# ---------------------------------------------------------------- CO2 amplifier chain
def _amps(sc, M, cam, tgt, n):
    """B1_22 (97 frames): seed laser + four amplifier modules on an optical table; the orange beam thickens
    and brightens stage by stage. Camera tracks along the chain."""
    K.world_dark(0.9)
    K.floor("Floor", K.mat("FloorDark", (0.05, 0.055, 0.065), rough=0.3, coat=0.3), z=0.0)
    import hero_kit_r10 as H
    HP = H.new_parts()
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
            H.valve_island(HP, (cx, -0.252, z + 0.02), (0, -1, 0), nval=8, s=1.3, drop=0.4)   # gas valves
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
        # R10: nameable services instead of LED strips / blue cable runs: supply + return coolant hoses with
        # clamps, a tied RF harness up to the overhead tray, a gas flange with viewport on each tube
        H.cooling_bundle(HP, [(x0 + 0.1, 0.2, z - 0.36), (x0 + 0.1, 0.2, z - 0.2), (x1 - 0.1, 0.2, z - 0.2),
                              (x1 - 0.1, 0.2, z - 0.36)], k=2, r=0.014, clamp_every=0.4, up=(0, 1, 0), block=False)
        H.cable_harness(HP, [(cx + 0.3, 0.6, z + 0.36), (cx + 0.45, 0.75, z + 0.7), (cx + 0.6, 1.05, 1.95)], n=6,
                        r=0.008, connector=True)
        H.flange_viewport(HP, (cx - 0.35, 0, z + 0.27), (0, 0, 1), 0.05, nipple=0.06, side_port=True,
                          up=(1, 0, 0))
        hous.box((cx, 0, 0.5), (x1 - x0 - 0.3, 0.4, 0.08))                             # cradle
        for xs in (x0 + 0.25, x1 - 0.25):
            hous.box((xs, 0, 0.64), (0.08, 0.36, 0.22))
    # beam tubes / bellows between stages
    for (a0, a1), (b0, b1) in zip(stages, stages[1:]):
        pipe.tube((a1, 0, z), (b0, 0, z), 0.035, seg=20)
        for k in range(6):
            fins.ring((a1 + (b0 - a1) * (k + 1) / 7, 0, z), 0.05, 0.035, 0.012, rot=(0, math.radians(90), 0), seg=24)
    # R10: overhead harness tray, a 45-deg beam-turning mirror on a hexapod after the last amplifier (the chain
    # folds toward the source vessel), and a service wall behind the table with nameable parts (wall_r10)
    tray = K.MB()
    tray.box((L / 2 - 0.6, 1.05, 2.0), (L + 1.6, 0.3, 0.02))
    tray.box((L / 2 - 0.6, 0.9, 2.04), (L + 1.6, 0.01, 0.08))
    for k in range(12):
        tray.box((-0.9 + k * 0.85, 1.05, 2.4), (0.04, 0.04, 0.8))
    H.cable_harness(HP, [(-1.2, 1.05, 2.03), (L + 0.4, 1.05, 2.03)], n=9, r=0.009, tie_every=0.3, connector=False)
    fold = Vector((stages[-1][1] + 0.9, 0, z))
    H.mirror_hexapod(HP, fold, Vector((-1, 1, 0)).normalized(), 0.12, hex_len=0.1)
    pipe.tube(fold + Vector((0, 0.08, 0)), fold + Vector((0, 1.4, 0)), 0.04, seg=20)                 # beam tube on
    for k in range(5):
        fins.ring(fold + Vector((0, 0.25 + k * 0.25, 0)), 0.06, 0.04, 0.015, rot=(math.radians(90), 0, 0), seg=24)
    wallp = K.MB()
    wallp.box((L / 2 - 0.6, 2.42, 1.5), (L + 4.0, 0.04, 3.0))
    wallp.obj("ServiceWallPlate", K.mat("ServiceWallDark", (0.09, 0.095, 0.11), metal=0.6, rough=0.45))
    import hero_kit_r11 as HK11            # R11: non-repeating blocks
    HK11.wall_r11(HP, -2.4, L + 1.2, 0.15, 2.9, 2.4, seed=22, scale=1.3, depth=0.8)   # far + dim: depth, not clutter
    tray.obj("OverheadTray", M["alu_dark"], bevel=0.003)
    H.finish(HP, M, "AmpKit")
    hous_o = hous.obj("AmpHousings", M["paint_grey"], bevel=0.006)
    objs = [table.obj("Table", M["anod"], bevel=0.004), hous_o, fins.obj("Fins", M["alu"]),
            bolt.obj("Bolts", M["steel"]), pipe.obj("Coolant", M["copper"]),
            anod.obj("Supplies", M["anod"], bevel=0.005)]
    for mb_ in (cab, led):
        mb_.bm.free()
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
