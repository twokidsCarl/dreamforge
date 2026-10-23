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


def _earth_mat(night=False, dots=None):
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
    if night:
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
    rough.inputs["To Max"].default_value = 0.8
    l.new(land.outputs["Result"], rough.inputs["Value"])
    l.new(rough.outputs["Result"], b.inputs["Roughness"])
    em_add = None
    reveal = None
    if night:
        # faint cyan coastlines
        cm = n.new("ShaderNodeMath")
        cm.operation = "MULTIPLY"
        cm.inputs[1].default_value = 0.6
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


def _laser(a, b, r=0.02, name="Laser", r_end=None):
    mb, mh = K.MB(), K.MB()
    if r_end is None:
        K.beam(mb, mh, [a, b], r=r, halo=4.0)
    else:                                    # tapered: wide enough to read from Earth, needle-thin at the target
        mb.tube(a, b, r, seg=12, r2=r_end)
        mh.tube(a, b, r * 4.0, seg=16, r2=r_end * 3.0)
    mb.obj(name, K.emit_mat(name + "Core", K.ORANGE, 30.0))
    mh.obj(name + "Halo", K.emit_mat(name + "HaloM", K.ORANGE, 4.0, halo=0.5))


def _dof(cam, fstop, focus_obj=None, dist=None):
    cam.data.dof.use_dof = True
    cam.data.dof.aperture_fstop = fstop
    if focus_obj is not None:
        cam.data.dof.focus_object = focus_obj
    elif dist:
        cam.data.dof.focus_distance = dist


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
    # tee-like little dust ring under the ball
    start = E + (ball.location - E).normalized() * earth_r * 1.01
    _laser(start, ball.location, r=0.03, r_end=0.0012)
    # R8: Earth-Moon distance rule under the beam (dashed, end ticks), scale cue for "380,000 km"
    rl = K.MB()
    e0, m0 = E + (MO - E).normalized() * (earth_r + 0.6), MO - (MO - E).normalized() * (moon_r + 0.6)
    off = Vector((0, 0, -2.2))
    for k in range(40):
        a_, b_ = e0.lerp(m0, k / 40), e0.lerp(m0, (k + 0.55) / 40)
        rl.tube(a_ + off, b_ + off, 0.03, seg=6)
    for p_ in (e0, m0):
        rl.tube(p_ + off + Vector((0, 0, -0.5)), p_ + off + Vector((0, 0, 0.5)), 0.035, seg=6)
    rl.obj("DistanceRule", K.emit_mat("RuleInk", (0.7, 0.85, 0.95), 2.0))
    spot = _uv_sphere("Spot", ball.location - dirb * ball_r * 0.15, ball_r * 0.35, 24, K.emit_mat("SpotM", K.ORANGE, 20.0))
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


def _ll(lon, lat, r):
    """lon/lat -> point on a UV sphere made by primitive_uv_sphere_add (texture u = 0.5 at +X, 0.75 at +Y)."""
    lo, la = math.radians(lon), math.radians(lat)
    return Vector((r * math.cos(la) * math.cos(lo), r * math.cos(la) * math.sin(lo), r * math.sin(la)))


def _globe(sc, n):
    _stars_world(top=(0.01, 0.016, 0.035), density=260, bright=5.0, share=0.5)   # R8: star field
    R = 2.0
    m, reveal = _earth_mat(night=True, dots=os.path.join(TEX, "worldmap_dots.png"))
    g = _uv_sphere("Globe", (0, 0, 0), R, 160, m)
    _atmosphere("GlobeAtmo", (0, 0, 0), R * 1.015, color=(0.2, 0.55, 0.95), strength=1.2)
    _key_value(reveal, [(1, 0.18), (round(n * 0.85), 0.9), (n, 0.95)])
    # arcs to the Netherlands
    nl = _ll(*NL, R)
    rnd = random.Random(6)
    arc_mat = K.emit_mat("ArcCyan", K.CYAN, 6.0)
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
        for k in range(N):
            t = k / (N - 1)
            p = a.normalized().slerp(nl.normalized(), t) if hasattr(Vector, "slerp") else a.lerp(nl, t)
            p = p.normalized() * (R * (1.0 + h * math.sin(math.pi * t)))
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
    _uv_sphere("NLPoint", nl * 1.004, 0.022, 24, K.emit_mat("NLWhite", (1, 1, 1), 25.0))
    _uv_sphere("NLHalo", nl * 1.004, 0.06, 24, K.emit_mat("NLHaloM", (0.85, 0.95, 1.0), 3.0, halo=0.6))
    _sun("Sun", (math.radians(55), 0, math.radians(-30)), 1.6, (0.75, 0.85, 1.0))
    _sun("SunRim", (math.radians(100), 0, math.radians(160)), 3.0, (1.0, 0.92, 0.8))   # R8: terminator / rim light
    # turn Europe toward the camera (camera on -Y): rotate so lon 5 sits at -Y
    g.rotation_euler = (0, 0, 0)
    cam, tgt = K.camera("CamR2", lens=50)
    cn = _ll(8, 38, 1).normalized()
    K.key_path(cam, tgt, [(1, tuple(cn * 8.6 + Vector((0.4, 0, -0.6))), (0, 0, 0.35)),
                          (n, tuple((cn * 6.8 + _ll(*NL, 1) * 0.6)), tuple(nl * 0.55))])
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
    band.inputs[1].default_value = 0.03
    l.new(dz.outputs[0], band.inputs[0])
    mix = nn.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.inputs["A"].default_value = (*K.lin((0.5, 0.48, 0.44)), 1)   # R6: fine-ground glass-ceramic, not blue plastic
    b.inputs["Roughness"].default_value = 0.6
    nz_ = nn.new("ShaderNodeTexNoise")
    nz_.inputs["Scale"].default_value = 900.0
    bp_ = nn.new("ShaderNodeBump")
    bp_.inputs["Strength"].default_value = 0.12
    l.new(nz_.outputs["Fac"], bp_.inputs["Height"])
    l.new(bp_.outputs["Normal"], b.inputs["Normal"])
    l.new(band.outputs[0], mix.inputs["Factor"])
    l.new(ramp.outputs["Color"], mix.inputs["B"])
    l.new(mix.outputs["Result"], b.inputs["Base Color"])
    mt = nn.new("ShaderNodeMath")
    mt.operation = "MULTIPLY"
    mt.inputs[1].default_value = 0.8
    l.new(band.outputs[0], mt.inputs[0])
    l.new(mt.outputs[0], b.inputs["Metallic"])
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
    bc = K.MB()                                              # R3: volume-light column, footprint spot on the face
    K.beam_columns(bc, [hit + din * 6.0, hit, hit + Vector((-dout.x, -dout.y, dout.z)) * 6.0], [0.12, 0.08, 0.12])
    # (the R5 out-leg above retraced the in-leg; dout itself is the reflected direction -> draw it)
    bc.obj("Beam", M["beam_wide"])
    bo = K.MB()
    K.beam_columns(bo, [hit, hit + Vector((din.x * -1, din.y * -1, din.z)) * 6.0], [0.08, 0.13])
    bo.obj("BeamOut", K.beam_column_mat("EUVOut", K.VIOLET, strength=1.0, edge=0.45, core=0.08, vol=0.12))
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
    sp = K.MB()
    sp.cyl((hit.x, hit.y, hit.z + 0.003), 0.12, 0.002, seg=32)
    sp.obj("BeamSpot", M["spot"])
    K.point("BeamHitLight", hit + Vector((0, 0, 0.25)), 15, K.VIOLET, 0.1)
    K.floor("Floor", K.mat("FloorDark", (0.04, 0.045, 0.055), rough=0.35), z=-1.2)
    K.area("Key", (-3, -4, 5), (0, 0, 0), 4, 900, (0.95, 0.96, 1.0))
    K.area("Rim", (3, 4, 3), (0, 0, 0), 5, 700, (0.75, 0.8, 1.0))
    K.area("Strip", (-4, 2, 2.5), (0, 0, 0), 0.6, 300, (1, 1, 1), size_y=6)
    K.point("Glow", hit + Vector((0, 0, 0.3)), 60, K.VIOLET, 0.1)
    # cut edge midpoint (wedge between a_cut0 / a_cut1) for the push-in
    am = (a_cut0 + a_cut1) / 2
    edge = Vector((R * 0.8 * math.cos(a_cut0), R * 0.8 * math.sin(a_cut0), -0.04))
    gapdir = Vector((math.cos(am), math.sin(am), 0))
    cam, tgt = K.camera("CamR2", lens=40)
    _dof(cam, 4.0, tgt)
    K.key_path(cam, tgt, [(1, tuple(gapdir * 3.6 + Vector((0, 0, 2.4))), (0, 0, -0.1)),
                          (round(n * 0.55), tuple(gapdir * 2.2 + Vector((0, 0, 0.8))), (edge * 0.6)),
                          (n, tuple(edge + gapdir * 0.55 + Vector((0, 0, 0.12)) + Vector((-math.sin(a_cut0), math.cos(a_cut0), 0)) * 0.35), edge)])
    sc["hdri"] = "studio_small_09"
    sc["hdri_strength"] = 0.6
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
    flo = K.mat("StudioFloor", (0.3, 0.31, 0.33), rough=0.25, coat=0.5)
    K.floor("Floor", flo, z=0.0)
    M = K.palette(studio=True)
    # mask: 1.52 x 1.52 x 0.064 (x10 scale), dark multilayer top with absorber pattern
    mb = K.MB()
    mb.box((0, 0, 0.12), (1.52, 1.52, 0.064))
    mask = mb.obj("Mask", K.mat("MaskSide", (0.2, 0.21, 0.23), rough=0.3), bevel=0.006)
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
    mt = K.MB()
    mt.box((0, 0, 0.1525), (1.44, 1.44, 0.002))
    mt.obj("MaskTop", top)
    # pellicle frame on four studs: gap above the mask
    gap = 0.055                                  # frame height = membrane stand-off (x10 scale, illustrative)
    fz = 0.152 + gap / 2
    fr = K.MB()
    fw, fh, bar, ht = 1.32, 1.06, 0.014, gap
    for (cx, cy, sx, sy) in [(0, fh / 2, fw, bar), (0, -fh / 2, fw, bar), (fw / 2, 0, bar, fh), (-fw / 2, 0, bar, fh)]:
        fr.box((cx, cy, fz), (sx, sy, ht))
    for sx in (-1, 1):                         # vent holes / pins on the frame sides
        for k in range(7):
            fr.cyl((sx * (fw / 2 + 0.018), -fh / 2 + (k + 0.5) * fh / 7, fz), 0.008, 0.006, rot=(0, math.radians(90), 0), seg=10)
    # R3 5A: thin black anodized frame (the R2 silver frame + gap read as a thick glass tray)
    fr.obj("PelFrame", K.mat("FrameBlack", (0.03, 0.03, 0.035), metal=0.6, rough=0.32, speck=0.1), bevel=0.003)
    # membrane: near-transparent, faint grey haze, glossy sheen at grazing angles, slight sag
    mem = _new_mat("Membrane")
    nt, nn, l = _nodes(mem)
    for x in list(nn):
        if x.type != "OUTPUT_MATERIAL":
            nn.remove(x)
    out = next(x for x in nn if x.type == "OUTPUT_MATERIAL")
    tr = nn.new("ShaderNodeBsdfTransparent")
    tr.inputs["Color"].default_value = (0.93, 0.93, 0.94, 1)
    gl = nn.new("ShaderNodeBsdfGlossy")
    gl.inputs["Roughness"].default_value = 0.06
    gl.inputs["Color"].default_value = (0.95, 0.95, 0.96, 1)
    df = nn.new("ShaderNodeBsdfDiffuse")
    df.inputs["Color"].default_value = (0.6, 0.6, 0.62, 1)
    fres = nn.new("ShaderNodeLayerWeight")
    fres.inputs["Blend"].default_value = 0.25
    m1 = nn.new("ShaderNodeMixShader")
    m1.inputs["Fac"].default_value = 0.012              # R4: thinner haze, 5A: shown only by grazing sheen
    l.new(tr.outputs[0], m1.inputs[1])
    l.new(df.outputs[0], m1.inputs[2])
    m2 = nn.new("ShaderNodeMixShader")
    fk = nn.new("ShaderNodeMath")
    fk.operation = "MULTIPLY"
    fk.inputs[1].default_value = 0.07                  # R5: less sheen, so it is not a dark lid
    l.new(fres.outputs["Fresnel"], fk.inputs[0])
    l.new(fk.outputs[0], m2.inputs["Fac"])
    l.new(m1.outputs[0], m2.inputs[1])
    l.new(gl.outputs[0], m2.inputs[2])
    l.new(m2.outputs[0], out.inputs["Surface"])
    bm = bmesh.new()
    nx, ny = 40, 32
    vs = [[bm.verts.new(((i / nx - 0.5) * (fw - bar), (j / ny - 0.5) * (fh - bar),
                         fz + ht / 2 - 0.004 * math.sin(math.pi * i / nx) * math.sin(math.pi * j / ny)))
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
    # dust particles on the membrane (what the pellicle is for) - a few tiny specks
    dm = K.MB()
    rnd = random.Random(4)
    for _ in range(9):
        dm.sphere((rnd.uniform(-0.5, 0.5), rnd.uniform(-0.4, 0.4), fz + ht / 2 + 0.004), rnd.uniform(0.004, 0.009), 8)
    dm.obj("Dust", K.mat("DustM", (0.25, 0.24, 0.22), rough=0.9))
    # studio lights; one strip sweeps to drag a grazing highlight across the membrane
    K.area("Key", (-3, -3.5, 4.5), (0, 0, 0.3), 3, 900, (1, 0.99, 0.97))
    K.area("Fill", (3.5, -2, 2), (0, 0, 0.3), 3, 350, (0.9, 0.95, 1.0))
    K.area("Rim", (0, 4, 2.5), (0, 0, 0.3), 4, 700, (0.92, 0.95, 1.0))
    sw = K.area("Sweep", (-3, 2.5, 1.6), (0, 0, 0.4), 0.25, 450, (1, 1, 1), size_y=4)
    sw.visible_camera = False                    # R3: the strip and its glints made the speckle block on the frame edge
    sc.cycles.sample_clamp_direct = 6.0
    sw.location = (-3.0, 2.5, 1.6)
    sw.keyframe_insert("location", frame=1)
    sw.location = (3.0, 2.5, 1.6)
    sw.keyframe_insert("location", frame=n)
    cam, tgt = K.camera("CamR2", lens=45)
    _dof(cam, 5.6, tgt)
    K.key_path(cam, tgt, [(1, (-1.4, -3.0, 2.6), (0.05, 0, 0.2)),
                          (round(n * 0.55), (-1.5, -2.5, 1.0), (0.2, -0.3, 0.2)),
                          (n, (-0.75, -1.9, 0.62), (0.25, -0.3, 0.17))])
    sc["hdri"] = "studio_small_09"
    sc["hdri_strength"] = 0.6
    return cam


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
    # scan slit above the wafer following the current field (thin violet bar)
    slit = K.MB()
    slit.box((0, 0, 0), (0.26, 0.02, 0.004))
    so = slit.obj("Slit", K.emit_mat("SlitM", K.VIOLET, 4.0, halo=0.3))
    for k, (_, j, i, cx, cy) in enumerate(keep):
        if k % 6 == 0 or k == len(keep) - 1:
            so.location = (cx, cy, 0.03)
            so.keyframe_insert("location", frame=1 + round((k / len(keep)) * n * 0.9))
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
    bw = K.MB()
    bw.box((1.0, 4.6, 1.6), (12.0, 0.1, 4.6))
    bw.obj("BackWall", Mk["anod"])
    import hero_kit_r10 as HK                         # R10: nameable parts (no PCB / LED boxes)
    P = HK.new_parts()
    import hero_kit_r11 as HK11            # R11: non-repeating blocks
    HK11.wall_r11(P, -4.5, 6.5, -0.4, 3.8, 4.55, seed=21, scale=1.6, depth=1.4)
    HK.finish(P, Mk, "B8_17Kit")
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
    cam, tgt = K.camera("CamR2", lens=32)
    _dof(cam, 8.0, tgt)
    K.key_path(cam, tgt, [(1, (-1.0, -5.6, 3.8), (1.0, 0.2, -0.1)), (n, (0.4, -5.4, 3.3), (1.3, 0.2, -0.1))])
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


def _machine_backdrop(sc):
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
    B.machine(M, studio=False, cut=True)
    sc["hdri"] = "hangar_interior"
    sc["hdri_strength"] = 0.25
    K.clean_cycles(sc)
    return B


def _wave(sc, n):
    """A2_08: 193 nm (grey) and 13.5 nm (violet) as two equal-length waves stacked above the wafer stage, in
    front of the out-of-focus projection optics; the violet period is the grey one / 14.3, so the viewer can
    count ~14 violet crests per grey crest. No floating boxes."""
    B = _machine_backdrop(sc)
    cx, y, span = 1.55, -2.6, 1.8
    lam193 = span / 2.0
    lam135 = lam193 / 14.3
    z193, z135 = 1.95, 1.55
    g = [(cx - span / 2 + span * i / 599, y, z193 + 0.11 * math.sin(2 * math.pi * (span * i / 599) / lam193))
         for i in range(600)]
    og, cg = _wave_curve("Wave193", g, [1.0] * 600, K.emit_mat("Grey193", (0.72, 0.75, 0.82), 3.0))
    cg.bevel_depth = 0.006
    v = [(cx - span / 2 + span * i / 2399, y, z135 + 0.07 * math.sin(2 * math.pi * (span * i / 2399) / lam135))
         for i in range(2400)]
    ov, cv = _wave_curve("Wave135", v, [1.0] * 2400, K.emit_mat("WaveM", K.VIOLET, 14.0))
    cv.bevel_depth = 0.0045
    oh, ch = _wave_curve("Wave135Halo", v, [1.0] * 2400, K.emit_mat("WaveHaloM", K.VIOLET, 2.5, halo=0.5))
    ch.bevel_depth = 0.014
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
                        "w135": Vector((cx + span * 0.3, y, z135 + 0.07)),
                        "span_l": Vector((cx - span / 2, y, z135 - 0.31)), "span_r": Vector((cx + span / 2, y, z135 - 0.31)),
                        "p0": Vector((cx - span / 2, y, z135 - 0.12)), "p1": Vector((cx - span / 2 + lam193, y, z135 - 0.12)),
                        "wafer": B.WAFER})
    return cam


def _bokeh(sc, n):
    """A2_03: out-of-focus machine (projection optics, violet path, wafer) under the formula overlay; anchors for
    the lambda -> beam and NA -> mirror leader lines."""
    B = _machine_backdrop(sc)
    cam, tgt = K.camera("CamR2", lens=32)
    # R6 (D): push in + rack focus: starts soft (formula beat), focus pulls onto the projection mirror the NA
    # leader points at, so the background changes and the leader lands on a sharp mirror and its light cone
    K.key_path(cam, tgt, [(1, (0.5, -4.7, 2.75), (1.6, 0, 2.55)), (n, (1.6, -3.7, 2.45), (2.0, 0, 2.45))],
               interp="BEZIER")
    foc = bpy.data.objects.new("NAFocus", None)
    sc.collection.objects.link(foc)
    foc.location = (0.9, -3.0, 2.6)
    foc.keyframe_insert("location", frame=1)
    foc.keyframe_insert("location", frame=round(n * 0.35))
    foc.location = tuple(B.PO[5])
    foc.keyframe_insert("location", frame=round(n * 0.75))
    _dof(cam, 1.2, foc)
    K.anchors("A2_03", {"beam": B.PO[1].lerp(B.PO[2], 0.5), "mirror": B.PO[5], "wafer": B.WAFER, "mask": B.MASK})
    return cam


VARIANTS = {"space": _space, "globe": _globe, "mirror": _mirror, "pellicle": _pellicle, "photons": _photons,
            "wafer": _wafer, "wave": _wave, "bokeh": _bokeh}


def build(variant="space", shot=None):
    n = K.nframes(shot) if shot else 120
    sc = C.reset_scene(n)
    sc["vignette"] = 0.3
    sc["film_grain"] = 0.1
    K.clean_cycles(sc)
    cam = VARIANTS[variant](sc, n)
    sc.camera = cam
    return sc
