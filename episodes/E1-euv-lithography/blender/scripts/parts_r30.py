"""Round 30 shared hero parts (MAIN process; R30 HARD 「同一部件一个模型」).

R29 p2 C_03: 「第二帧的『场分面镜』是一块方板…和 B5_01 里的弧形长条小镜阵列不一致，同一部件在片中出现了两套画法」.
One model per part, reused by every shot that shows it:
  facet_plate(): the field-facet mirror = the R29 B5_01 model (cut_scene_r29._b501: a dark base plate, 4 columns x 11
      rows of curved arc strips each tilted a little, two mount pegs per strip, satin coating) - same construction,
      size given by the caller (B5_01 1.3 x 1.0 m, C_03 window / A0_10 housing smaller).
  pupil_disc(): the pupil-facet mirror = the builder's round facets on a disc (build_cutaway_r2: rings of 1 / 8 / 15 /
      22 / 28 round facets on substrate cups, carrier disc, flange ring, support post) - same construction.
"""
import math
import random

import bpy
from mathutils import Matrix, Vector


def facet_plate(name, piv, n, W, H, seed=29, rough=0.25, metal=0.8):
    """field-facet plate centred on piv (the strips' top faces pass through piv), facing n. Returns the 3 objects."""
    import cut_scene_r29 as S29
    import kit_r2 as K
    n = Vector(n).normalized()
    u = Vector((0, 0, 1)).cross(n)
    if u.length < 1e-6:
        u = Vector((1, 0, 0))
    u.normalize()
    v = n.cross(u).normalized()
    rnd = random.Random(seed)
    plate, strips, mounts = K.MB(), K.MB(), K.MB()
    thick_plate, lift, thick = 0.035, 0.03, 0.014
    base_c = Vector(piv) - n * (lift + thick)
    M = Matrix((u, v, n)).transposed().to_4x4()
    plate.box(tuple(base_c - n * thick_plate / 2), (W * 1.06, H * 1.08, thick_plate), rot=M.to_euler())
    cols, rows = 4, 11
    cw, rh = W / cols, H / rows
    for ci in range(cols):
        for ri in range(rows):
            c = base_c + u * (-W / 2 + cw * (ci + 0.5)) + v * (-H / 2 + rh * (ri + 0.5)) + n * lift
            ends = S29._arc_strip(strips, c, u, v, n, R=cw * 1.35, span=math.radians(38), width=rh * 0.62,
                                  thick=thick, tilt=math.radians(rnd.uniform(-4, 4)))
            for e in ends:
                mounts.cyl(tuple(e - n * (lift / 2 + 0.004)), rh * 0.16, lift + 0.008,
                           rot=Vector((0, 0, 1)).rotation_difference(n).to_euler(), seg=10)
    obs = [plate.obj(name + "Plate", K.mat(name + "PlateM", (0.09, 0.095, 0.11), metal=0.7, rough=0.42), bevel=0.004),
           strips.obj(name + "Strips", K.mat(name + "Coat", (0.84, 0.84, 0.88), metal=metal, rough=rough)),
           mounts.obj(name + "Mounts", K.mat(name + "MountM", (0.30, 0.31, 0.34), metal=0.9, rough=0.3))]
    print(f"[parts_r30] facet_plate {name} {W}x{H} at {tuple(round(x, 2) for x in piv)} n {tuple(round(x, 2) for x in n)}",
          flush=True)
    return obs


def pupil_disc(name, piv, n2, scale=1.0, post=True):
    """pupil-facet disc centred on piv facing n2 (builder construction). Returns the objects."""
    import kit_r2 as K
    n2 = Vector(n2).normalized()
    q2 = Vector((0, 0, 1)).rotation_difference(n2)
    R2 = q2.to_matrix()
    mir, sub, car, fl = K.MB(), K.MB(), K.MB(), K.MB()
    s = scale
    for rr, cnt in [(0.0, 1), (0.09, 8), (0.18, 15), (0.27, 22), (0.36, 28)]:
        for k in range(cnt):
            a = 2 * math.pi * k / cnt
            c = Vector(piv) + R2 @ Vector((rr * s * math.cos(a), rr * s * math.sin(a), 0))
            mir.cyl_m(Matrix.Translation(c) @ R2.to_4x4(), 0.038 * s, 0.012 * s, seg=20)
            sub.cyl_m(Matrix.Translation(c - n2 * 0.018 * s) @ R2.to_4x4(), 0.04 * s, 0.026 * s, seg=20)
    car.cyl_m(Matrix.Translation(Vector(piv) - n2 * 0.04 * s) @ R2.to_4x4(), 0.44 * s, 0.05 * s, seg=48)
    fl.ring(Vector(piv) - n2 * 0.02 * s, 0.47 * s, 0.42 * s, 0.08 * s, rot=q2.to_euler())
    if post:
        car.tube(Vector(piv) - n2 * 0.08 * s, Vector(piv) - n2 * 0.08 * s + Vector((0, 0, -0.5)), 0.06 * s)
    m_mir = bpy.data.materials.get("EUVMirrorHiR19") or K.mat("R30PupilCoat", (0.84, 0.84, 0.88), metal=0.9, rough=0.12)
    obs = [mir.obj(name + "Facets", m_mir),
           sub.obj(name + "Cups", K.mat(name + "CupM", (0.20, 0.21, 0.23), metal=0.8, rough=0.35)),
           car.obj(name + "Carrier", K.mat(name + "CarM", (0.12, 0.125, 0.14), metal=0.6, rough=0.4)),
           fl.obj(name + "Flange", K.mat(name + "FlM", (0.62, 0.63, 0.66), metal=1.0, rough=0.2))]
    print(f"[parts_r30] pupil_disc {name} at {tuple(round(x, 2) for x in piv)} n {tuple(round(x, 2) for x in n2)}",
          flush=True)
    return obs
