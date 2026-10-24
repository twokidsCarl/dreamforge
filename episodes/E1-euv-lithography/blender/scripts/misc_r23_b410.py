"""R23 B4_10 (R23_ROOT_CAUSE row 6, hero-part scale). Owned by the misc sub-agent. Layered on misc_b410_r22.

R22 review: 「第 3 帧高尔夫球和月面尺度关系出戏（球几乎和岩坑一样大）…改法：第 3 帧改为远景把球放在小石子旁」 + R22 own risk
「碎石读成悬空块」. Not repeating the R22 floating rocks.
- pre(): misc_b410_r22._craters patched -> no crater of ball size near the ball (craters within 0.35 m are <= 4 mm pits;
  bigger bowls only further out, >= 0.25 m radius = 10x the ball) -> the ball reads 4 cm against the ground.
- post(): RocksR22 replaced by PEBBLES that sit in the regolith (35-45 % buried, flat bottoms, so every one has a
  contact shadow): ~520 grains 0.6-3 mm + 7 small stones 7-11 mm right beside the ball.
- camera from the close-up beat (0.75 n on; the 55 % frame key is untouched): looks DOWN at the ball (pitch ~72 deg, ~0.6 m away = the ball ~8 % of the frame width) so
  the 1.36 m scene-Moon's limb never enters the frame (the limb next to the ball made it read moon-sized); slow push.
"""
import math
import random

import bmesh
import bpy
from mathutils import Matrix, Vector, noise

import misc_b410_r22 as R22


def _craters(rnd, cap_r):
    cr = []
    for _ in range(1400):
        r = 0.002 * (1.0 - rnd.random()) ** (-0.9)
        r = min(r, 0.6)
        d = cap_r * math.sqrt(rnd.random())
        a = rnd.random() * 2 * math.pi
        if d < 0.35 and r > 0.004:
            continue                      # nothing ball-sized near the ball
        if d < 0.6 and 0.02 < r < 0.25:
            continue
        cr.append((d * math.cos(a), d * math.sin(a), r))
    return cr


def pre(mod):
    R22._craters = _craters
    R22.SUN_ELEV = 13.0          # still a low sun, but pebble shadows ~4x their height instead of ~8x (R23 smoke: spikes)


def _pebbles(sc, b, nrm, MO, Rm, hit_dir, rnd):
    t1, t2 = R22._tangent_frame(nrm)
    rbm = bmesh.new()
    rb = 0.024
    items = []
    # small stones right beside the ball (1.4-2.2 cm across), away from the beam side
    for k in range(7):
        a = 2 * math.pi * k / 7 + 0.4 + 0.3 * rnd.random()
        d = 0.05 + 0.05 * rnd.random()
        items.append((d, a, 0.0035 + 0.0025 * rnd.random()))
    for _ in range(3000):
        if len(items) >= 527:
            break
        d = 0.035 + 0.6 * rnd.random() ** 1.5
        a = rnd.random() * 2 * math.pi
        items.append((d, a, 0.0006 + 0.0024 * rnd.random() ** 2.5))
    n = 0
    for (d, a, sz) in items:
        u, v = d * math.cos(a), d * math.sin(a)
        ang = d / Rm
        dirv = (nrm * math.cos(ang) + (t1 * math.cos(a) + t2 * math.sin(a)) * math.sin(ang)).normalized()
        base = MO + dirv * (Rm + 0.0015 + R22._height(u, v, None, (0.0, 0.0)))
        if hit_dir is not None:
            w = base - b
            al = w.dot(hit_dir)
            if al > 0 and (w - al * hit_dir).length < 0.03:
                continue
        if (base - b).length < rb + sz * 1.6:
            continue
        sx, sy, sz_ = 0.75 + 0.5 * rnd.random(), 0.75 + 0.5 * rnd.random(), 0.5 + 0.25 * rnd.random()
        geom = bmesh.ops.create_icosphere(rbm, subdivisions=3 if sz > 0.002 else 2, radius=sz)
        rot = dirv.to_track_quat("Z", "Y").to_matrix() @ Matrix.Rotation(rnd.random() * 6.28, 3, "Z")
        seed = Vector((rnd.random() * 100, rnd.random() * 100, rnd.random() * 100))
        sink = 0.4 * sz * sz_                                   # 40 % of the height below the regolith
        for vtx in geom["verts"]:
            c = vtx.co
            j = 1.0 + 0.3 * noise.noise(c / max(sz, 1e-4) * 1.3 + seed)
            z = max(c.z * sz_ * j, -sink * 1.05)                # flat buried bottom
            vtx.co = base + rot @ Vector((c.x * sx * j, c.y * sy * j, z))    # centre on the ground, bottom buried
        n += 1
    for f in rbm.faces:
        f.smooth = True
    me = bpy.data.meshes.new("PebblesR23")
    rbm.to_mesh(me)
    rbm.free()
    ob = bpy.data.objects.new("PebblesR23", me)
    sc.collection.objects.link(ob)
    import kit_r2 as K
    me.materials.append(K.mat("PebbleR23", (0.27, 0.265, 0.255), rough=0.92))
    return ob, n


def post(sc):
    import kit_r2 as K
    n = sc.frame_end
    moon = bpy.data.objects.get("Moon")
    ball = bpy.data.objects.get("GolfBall")
    if moon is None or ball is None:
        print("[R23 B4_10] Moon / GolfBall missing - skipped")
        return
    MO = moon.location.copy()
    Rm = max(moon.dimensions) / 2
    b = ball.location.copy()
    nrm = (b - MO).normalized()
    hit_dir = None
    for o in bpy.data.objects:
        if o.name.startswith("StationR17"):
            hit_dir = (o.location - b).normalized()
    old = bpy.data.objects.get("RocksR22")
    vis = None
    if old is not None:
        vis = old.animation_data.action if old.animation_data else None
        bpy.data.objects.remove(old, do_unlink=True)
    peb, npeb = _pebbles(sc, b, nrm, MO, Rm, hit_dir, random.Random(2310))
    f_on = round(n * 0.62)
    peb.hide_render = True
    peb.keyframe_insert("hide_render", frame=1)
    peb.keyframe_insert("hide_render", frame=f_on - 1)
    peb.hide_render = False
    peb.keyframe_insert("hide_render", frame=f_on)
    # camera: keep keys up to 0.55 n, re-key the close-up beat looking down onto the ball
    cam = sc.camera
    tgt = next(c.target for c in cam.constraints if c.type == "TRACK_TO")
    E = Vector((0, 0, 0))
    dirb = (E - MO).normalized()
    side = nrm.cross(dirb).normalized()
    hd = (side * 0.9 + (dirb - dirb.dot(nrm) * nrm).normalized() * 0.35).normalized()
    keys = [(1, (-9.0, -14.0, 3.5), (6.0, 3.0, 0.5)),
            (round(n * 0.3), (-4.0, -12.0, 3.0), (14.0, 6.0, 1.5)),
            (round(n * 0.55), (30.0, 6.0, 5.5), MO + Vector((0, 0, 0.2))),
            (round(n * 0.75), b + hd * 0.30 + nrm * 0.9, b),
            (round(n * 0.85), b + hd * 0.19 + nrm * 0.58, b),
            (n, b + hd * 0.16 + nrm * 0.47, b)]
    for ob in (cam, tgt):
        ob.animation_data_clear()
    K.key_path(cam, tgt, [(f, tuple(p), tuple(t)) for f, p, t in keys])
    from bpy_extras.object_utils import world_to_camera_view as w2c
    sc.frame_set(round(n * 0.85))
    v = w2c(sc, cam, b)
    d = (cam.matrix_world.translation - b).length
    print(f"[R23 B4_10] pebbles {npeb}; f{round(n * 0.85)} cam dist {d:.3f} m ball screen ({v.x:.3f},{1 - v.y:.3f}); "
          f"lens {cam.data.lens}")
    sc.frame_set(1)
