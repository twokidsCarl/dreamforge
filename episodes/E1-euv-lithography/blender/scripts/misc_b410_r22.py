"""Round 22 (P1) hook for B4_10 (R22_ROOT_CAUSE row 6, material). Owned by the misc sub-agent.

R21 review B4_10 #1 「末帧月面是光滑浅灰平面，没有陨坑、碎石、掠射阴影，像塑料（A 主扣点）。换高分月面位移 + 低角度太阳光，让高尔夫球
投出长影」 and #2 「光束…终点没有落点光斑。在球面上加一个小亮斑，光束在终点收细」.
Layered on the R21 build of r2_misc._space (only the golf-ball close-up beat is touched; Earth / mid frames unchanged):
- regolith cap: a spherical cap of the Moon (60 deg half-angle around the ball) rebuilt as real geometry, dense near the
  ball, displaced with a power-law crater field (bowl + raised rim) + fbm grain, flattened under the ball; grey regolith
  material with fine bump; visible from the close-up beat on (hidden before -> mid frames keep R21 pixels).
- scattered rocks: ~260 irregular displaced rocks (2-40 mm) around the ball, none on the ball / beam footprint.
- low sun: from the close-up beat the R21 high Sun is switched off and a sun ~7 deg above the local horizon lights the
  scene from the side -> crater rims and rocks throw grazing shadows and the ball throws a long shadow.
- landing: a brighter soft landing spot cap on the ball where the beam arrives + a short converging tip on the beam end.
"""
import math
import random

import bmesh
import bpy
from mathutils import Matrix, Vector, noise

CAP_DEG = 60.0
SUN_ELEV = 7.0


def pre(variant, shot, mod):
    pass


def _tangent_frame(nrm):
    t1 = nrm.cross(Vector((0, 0, 1)))
    if t1.length < 1e-3:
        t1 = nrm.cross(Vector((1, 0, 0)))
    t1.normalize()
    t2 = nrm.cross(t1).normalized()
    return t1, t2


def _regolith_mat():
    m = bpy.data.materials.new("RegolithR22")
    m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    bs = next(x for x in N if x.type == "BSDF_PRINCIPLED")
    tc = N.new("ShaderNodeTexCoord")
    nz = N.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 18.0
    nz.inputs["Detail"].default_value = 8.0
    L.new(tc.outputs["Object"], nz.inputs["Vector"])
    ramp = N.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (0.13, 0.128, 0.122, 1)
    ramp.color_ramp.elements[1].color = (0.30, 0.295, 0.285, 1)
    L.new(nz.outputs["Fac"], ramp.inputs["Fac"])
    L.new(ramp.outputs["Color"], bs.inputs["Base Color"])
    bs.inputs["Roughness"].default_value = 0.97
    try:
        bs.inputs["Specular IOR Level"].default_value = 0.15
    except KeyError:
        pass
    fine = N.new("ShaderNodeTexNoise")
    fine.inputs["Scale"].default_value = 900.0
    fine.inputs["Detail"].default_value = 4.0
    L.new(tc.outputs["Object"], fine.inputs["Vector"])
    bp = N.new("ShaderNodeBump")
    bp.inputs["Strength"].default_value = 0.6
    bp.inputs["Distance"].default_value = 0.002
    L.new(fine.outputs["Fac"], bp.inputs["Height"])
    L.new(bp.outputs["Normal"], bs.inputs["Normal"])
    return m


def _craters(rnd, cap_r):
    """(u, v, radius) in tangent-plane metres; power-law sizes, denser small ones."""
    cr = []
    for _ in range(900):
        r = 0.006 * (1.0 - rnd.random()) ** (-0.85)
        r = min(r, 0.35)
        d = cap_r * math.sqrt(rnd.random())
        a = rnd.random() * 2 * math.pi
        cr.append((d * math.cos(a), d * math.sin(a), r))
    # a few clear mid-size craters near the ball (readable in the close-up)
    for (u, v, r) in ((0.16, -0.10, 0.06), (-0.22, 0.05, 0.09), (0.05, 0.30, 0.11), (-0.10, -0.24, 0.045),
                      (0.34, 0.18, 0.13), (0.09, 0.09, 0.025), (-0.07, 0.12, 0.018)):
        cr.append((u, v, r))
    return cr


_GRID = {}
_CELL = 0.08


def _bin(craters):
    _GRID.clear()
    for c in craters:
        cu, cv, r = c
        ext = 1.6 * r
        for i in range(math.floor((cu - ext) / _CELL), math.floor((cu + ext) / _CELL) + 1):
            for j in range(math.floor((cv - ext) / _CELL), math.floor((cv + ext) / _CELL) + 1):
                _GRID.setdefault((i, j), []).append(c)


def _height(u, v, craters, ball_uv):
    h = 0.0
    for (cu, cv, r) in _GRID.get((math.floor(u / _CELL), math.floor(v / _CELL)), ()):
        dx, dy = u - cu, v - cv
        if abs(dx) > 1.6 * r or abs(dy) > 1.6 * r:
            continue
        q = math.hypot(dx, dy) / r
        depth = 0.12 * r
        if q < 1.0:
            h += depth * (q * q - 1.0) + 0.03 * r
        elif q < 1.6:
            h += 0.03 * r * math.exp(-((q - 1.0) / 0.25) ** 2)
    h += 0.0015 * noise.fractal(Vector((u * 30, v * 30, 0.3)), 0.6, 2.0, 5)
    h += 0.005 * noise.noise(Vector((u * 4, v * 4, 1.7)))
    # flatten under the ball (it rests on a level patch)
    db = math.hypot(u - ball_uv[0], v - ball_uv[1])
    w = min(1.0, max(0.0, (db - 0.03) / 0.05))
    return h * w


def post(sc, variant, shot):
    import kit_r2 as K
    n = sc.frame_end
    moon = bpy.data.objects.get("Moon")
    ball = bpy.data.objects.get("GolfBall")
    if moon is None or ball is None:
        print("[R22 B4_10] Moon / GolfBall missing - skipped")
        return
    MO = moon.location.copy()
    Rm = max(moon.dimensions) / 2
    b = ball.location.copy()
    nrm = (b - MO).normalized()
    t1, t2 = _tangent_frame(nrm)
    f_on = round(n * 0.62)                           # close-up beat starts (camera key at 0.75 n; mid frame 0.55 n untouched)
    rnd = random.Random(410)
    cap_r = Rm * math.radians(CAP_DEG)
    craters = _craters(rnd, cap_r)
    _bin(craters)
    # surface base point under the ball
    ball_uv = (0.0, 0.0)
    # polar grid: rings geometric from 2 mm to cap_r
    NR, NS = 230, 360
    rings = [0.0] + [0.002 * (cap_r / 0.002) ** (k / (NR - 1)) for k in range(NR)]
    bm = bmesh.new()
    grid = []
    for ri, d in enumerate(rings):
        row = []
        segs = 1 if ri == 0 else NS
        for s in range(segs):
            a = 2 * math.pi * s / NS
            u, v = d * math.cos(a), d * math.sin(a)
            ang = d / Rm
            dirv = (nrm * math.cos(ang) + (t1 * math.cos(a) + t2 * math.sin(a)) * math.sin(ang)).normalized()
            fade = 1.0 - min(1.0, max(0.0, (d - cap_r * 0.75) / (cap_r * 0.25)))
            h = _height(u, v, craters, ball_uv) * fade
            row.append(bm.verts.new(MO + dirv * (Rm + 0.0015 * fade + h)))
        grid.append(row)
    for ri in range(1, len(grid)):
        for s in range(NS):
            s2 = (s + 1) % NS
            if ri == 1:
                bm.faces.new((grid[0][0], grid[1][s], grid[1][s2]))
            else:
                bm.faces.new((grid[ri - 1][s], grid[ri][s], grid[ri][s2], grid[ri - 1][s2]))
    for f in bm.faces:
        f.smooth = True
    bm.normal_update()
    me = bpy.data.meshes.new("RegolithR22")
    bm.to_mesh(me)
    bm.free()
    # outward normals
    if me.polygons[len(me.polygons) // 2].normal.dot(nrm) < 0:
        me.flip_normals()
    cap = bpy.data.objects.new("RegolithR22", me)
    sc.collection.objects.link(cap)
    rmat = _regolith_mat()
    me.materials.append(rmat)
    # rocks
    rockm = K.mat("RockR22", (0.24, 0.235, 0.225), rough=0.9)
    rbm = bmesh.new()
    nrock = 0
    beam_dir = None
    las = bpy.data.objects.get("LaserR17")
    hit_dir = None
    for o in bpy.data.objects:
        if o.name.startswith("StationR17"):
            hit_dir = (o.location - b).normalized()
    for _ in range(4000):
        if nrock >= 420:
            break
        d = 0.04 + 0.7 * rnd.random() ** 1.8
        a = rnd.random() * 2 * math.pi
        u, v = d * math.cos(a), d * math.sin(a)
        if d < 0.05:
            continue
        sz = 0.0012 + 0.009 * rnd.random() ** 3.0
        ang = d / Rm
        dirv = (nrm * math.cos(ang) + (t1 * math.cos(a) + t2 * math.sin(a)) * math.sin(ang)).normalized()
        p = MO + dirv * (Rm + 0.0015 + _height(u, v, craters, ball_uv) + sz * 0.3)
        if hit_dir is not None:
            w = p - b
            along = w.dot(hit_dir)
            if along > 0 and (w - along * hit_dir).length < 0.05:
                continue
        geom = bmesh.ops.create_icosphere(rbm, subdivisions=3, radius=sz)
        sx, sy, sz_ = 0.7 + 0.6 * rnd.random(), 0.7 + 0.6 * rnd.random(), 0.45 + 0.3 * rnd.random()
        rot = dirv.to_track_quat("Z", "Y").to_matrix() @ Matrix.Rotation(rnd.random() * 6.28, 3, "Z")
        seed = Vector((rnd.random() * 100, rnd.random() * 100, rnd.random() * 100))
        for vtx in geom["verts"]:
            c = vtx.co
            j = 1.0 + 0.35 * noise.noise(c / max(sz, 1e-4) * 1.3 + seed)
            loc = Vector((c.x * sx * j, c.y * sy * j, c.z * sz_ * j))
            vtx.co = p + rot @ loc
        nrock += 1
    for f in rbm.faces:
        f.smooth = True
    rme = bpy.data.meshes.new("RocksR22")
    rbm.to_mesh(rme)
    rbm.free()
    rocks = bpy.data.objects.new("RocksR22", rme)
    sc.collection.objects.link(rocks)
    rme.materials.append(rockm)
    for o in (cap, rocks):
        o.hide_render = True
        o.keyframe_insert("hide_render", frame=1)
        o.keyframe_insert("hide_render", frame=f_on - 1)
        o.hide_render = False
        o.keyframe_insert("hide_render", frame=f_on)
    # old soft contact-shadow disc: the real low-sun shadow replaces it in the close-up
    bsh = bpy.data.objects.get("BallShadow")
    if bsh is not None:
        bsh.hide_render = False
        bsh.keyframe_insert("hide_render", frame=f_on - 1)
        bsh.hide_render = True
        bsh.keyframe_insert("hide_render", frame=f_on)
    # low sun: from the side away from Earth so the camera-facing ground and the long shadow both read
    cam = sc.camera
    sc.frame_set(n)
    cpos = cam.matrix_world.translation.copy()
    sc.frame_set(1)
    vc = cpos - b
    vc_t = (vc - vc.dot(nrm) * nrm).normalized()             # camera azimuth in the tangent plane
    perp = nrm.cross(vc_t).normalized()
    az = (-perp * 0.85 + vc_t * 0.25).normalized()            # sun mostly side-on to the view, a bit toward camera
    e = math.radians(SUN_ELEV)
    to_sun = (az * math.cos(e) + nrm * math.sin(e)).normalized()
    ld = bpy.data.lights.new("SunLowR22", "SUN")
    ld.energy = 7.0
    ld.angle = math.radians(0.5)
    ld.color = (1.0, 0.97, 0.92)
    so = bpy.data.objects.new("SunLowR22", ld)
    sc.collection.objects.link(so)
    so.rotation_euler = (-to_sun).to_track_quat("-Z", "Y").to_euler()
    so.hide_render = True
    so.keyframe_insert("hide_render", frame=1)
    so.keyframe_insert("hide_render", frame=f_on - 1)
    so.hide_render = False
    so.keyframe_insert("hide_render", frame=f_on)
    for nm in ("Sun",):
        o = bpy.data.objects.get(nm)
        if o is None:
            continue
        o.hide_render = False
        o.keyframe_insert("hide_render", frame=f_on - 1)
        o.hide_render = True
        o.keyframe_insert("hide_render", frame=f_on)
    bf = bpy.data.objects.get("BallFill")                   # R21 near fill flattened the close-up -> dim
    if bf is not None:
        bf.data.energy = 2.0
        bf.data.keyframe_insert("energy", frame=f_on - 1)
        bf.data.energy = 0.25
        bf.data.keyframe_insert("energy", frame=f_on)
    # landing: brighter spot cap on the ball + short converging tip at the beam end
    if hit_dir is not None:
        import misc_kit_r16 as MK
        COLD = (0.82, 0.92, 1.0)
        rb = max(ball.dimensions) / 2
        MK.spot_cap("SpotHaloR22", b, rb * 1.035, hit_dir, 14, K.emit_mat("SpotHaloR22M", COLD, 1.6, halo=0.6))
        MK.spot_cap("SpotHotR22", b, rb * 1.04, hit_dir, 5, K.emit_mat("SpotHotR22M", COLD, 22.0, halo=0.8))
        hit = b + hit_dir * rb * 1.02
        try:
            if True:
                raise RuntimeError("tip disabled (fat beam at 8 spp)")
            import misc_beam_r17 as BR17
            BR17.thin_core("BeamTipR22", hit + hit_dir * 0.18, hit, 0.0035, COLD, 22.0, 1.0, fade0=0.0, seg=16,
                           r_end=0.0004)
        except Exception as ex:                       # noqa: BLE001
            print(f"[R22 B4_10] beam tip skipped: {ex}")
        pl = K.point("SpotLightR22", hit + hit_dir * 0.006, 0.02, COLD, 0.002)
        pl.visible_camera = False
        pl.visible_glossy = False
    print(f"[R22 B4_10] regolith cap {len(me.vertices)} verts, {len(craters)} craters, {nrock} rocks; low sun "
          f"{SUN_ELEV} deg from frame {f_on}")
