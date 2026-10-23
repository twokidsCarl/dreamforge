"""Round 21 (P1) helpers for r2_source (A0_01 / B1_10 tin sheet). Copy of source_r20.py (left untouched).

R21 root cause #2 (R20 review A0_01 #1 「片厚降到直径的约 1/20，表面只留低频起伏…把薄饼法线转向激光来向」, B1_10 #1
「像皱铬箔，又厚又硬…法线朝向激光来向」): GEOMETRY ONLY - M["tin"] untouched.
  * sheet = ONE thin continuous sheet: near-uniform thickness ~ 1/20 of the diameter (edge only ~15 % thicker, a
    plain rounded edge - no R20 toroidal rolled-rim bead), outline only k = 2 / 3 harmonics, surface = 1-2
    low-frequency ripples (a gentle bow + one radial swell), no high-frequency harmonics;
  * NORMAL ON THE LASER: the sheet's normal is local +X; both shots' drive / pre-pulse cones run along world +X from
    the collector hole onto the droplet (COLL_X - 0.2 -> 0), so the laser hits the FACE (the camera angle is
    unchanged - camera moves are not this row);
  * ligaments: FEWER and THICKER - 5 (<= 6), root r 0.05 / neck r >= 0.028 (unit radius; ~5-8 px wide at
    960x540 at these framings), each ending in a droplet.
"""
import math
import random

import bpy
from mathutils import Vector

import kit_r2 as K

OFF = (0.0, 0.43, -0.31)        # same object-space offset as source_r17 (the tin's ripple rings centre off the sheet)


def _smax(a, b, k=0.01):
    h = max(0.0, min(1.0, 0.5 + 0.5 * (a - b) / k))
    return a * h + b * (1 - h) + k * h * (1 - h)


def pancake_r21(M, c, R, name="Pancake", seed=1, glint=None):
    import bmesh
    rnd = random.Random(seed)
    mb = K.MB()
    na = 160
    harm = [(k, rnd.uniform(0.012, 0.022), rnd.uniform(0, 6.28)) for k in (2, 3)]   # low-frequency outline only
    ph_w = rnd.uniform(0, 6.28)
    HT = 0.05                                # half-thickness: total 0.1 = diameter (2) / 20

    def rim(a):
        return 1.0 + sum(amp * math.sin(k * a + ph) for k, amp, ph in harm)

    def bow(rho, a):                         # 1-2 low-frequency ripples: gentle bow + one radial swell
        return 0.06 * (1.0 - min(1.0, rho) ** 2) + 0.035 * math.sin(math.pi * min(1.0, rho) * 1.4) * math.cos(a + ph_w)

    n_in, n_out = 20, 8

    def profile(a):
        Ro = rim(a)
        e = HT * 1.15                        # edge only slightly thicker, plain rounded edge
        rc = Ro - e
        pts = []
        for i in range(n_in + 1):
            s_ = i / n_in
            rho = rc * (1 - (1 - s_) ** 1.4)
            t = rho / rc
            pts.append((rho, HT + (e - HT) * t ** 6))
        for i in range(1, n_out + 1):
            ph = (math.pi / 2) * i / n_out
            pts.append((rc + e * math.sin(ph), e * math.cos(ph)))
        return pts

    profs = [profile(2 * math.pi * j / na) for j in range(na)]
    npf = len(profs[0])
    top, bot = [], []
    for i in range(npf):
        rt, rbt = [], []
        for j in range(na):
            a = 2 * math.pi * j / na
            rho, h = profs[j][i]
            y, z = rho * math.cos(a), rho * math.sin(a)
            x0 = bow(rho, a)
            rt.append(mb.bm.verts.new((x0 + h, y + OFF[1], z + OFF[2])))
            rbt.append(mb.bm.verts.new((x0 - h, y + OFF[1], z + OFF[2])))
        top.append(rt)
        bot.append(rbt)
    for i in range(npf - 1):
        for j in range(na):
            k = (j + 1) % na
            mb.bm.faces.new((top[i][j], top[i][k], top[i + 1][k], top[i + 1][j])).smooth = True
            mb.bm.faces.new((bot[i][j], bot[i + 1][j], bot[i + 1][k], bot[i][k])).smooth = True
    bmesh.ops.remove_doubles(mb.bm, verts=mb.bm.verts[:], dist=1e-6)   # merges the centre poles + the edge seam
    ob = mb.obj(name, M["tin"])
    ob.location = (0, -OFF[1], -OFF[2])

    # ligaments: irregular count / spacing / length; root -> thin neck -> end bead (+ sometimes a pinched-off bead)
    lig = K.MB()
    nl = 5
    base = rnd.uniform(0, 6.28)
    angs = [base + 2 * math.pi * (k + rnd.uniform(-0.28, 0.28)) / nl for k in range(nl)]
    for k, a in enumerate(angs):
        u = Vector((0, math.cos(a), math.sin(a)))
        side = Vector((0, -math.sin(a), math.cos(a)))
        r0 = rim(a) - HT
        L = (0.26, 0.45, 0.34, 0.52, 0.2)[k] * rnd.uniform(0.85, 1.15)
        x0 = bow(r0, a)
        back = Vector((x0 - rnd.uniform(0.01, 0.04), 0, 0))
        bend = side * rnd.uniform(-0.15, 0.15) * L
        w_root, w_neck = 0.05, rnd.uniform(0.028, 0.036)
        p0 = u * r0 + Vector((x0, 0, 0))
        p1 = u * (r0 + L * 0.45) + bend * 0.4 + back
        p2 = u * (r0 + L) + bend + back
        lig.tube(p0, p1, w_root, seg=16, r2=w_neck)
        lig.sphere(tuple(p1), w_neck, 14)
        lig.tube(p1, p2, w_neck, seg=14, r2=w_neck)
        lig.sphere(tuple(p2), w_neck * rnd.uniform(1.6, 1.9), 16)      # end droplet
    so = lig.obj(name + "Crown", M["tin"])
    for o_ in (so,):
        for poly in o_.data.polygons:
            poly.use_smooth = True
    root = bpy.data.objects.new(name + "Root", None)
    bpy.context.scene.collection.objects.link(root)
    root.location = c
    ob.parent = root
    so.parent = root
    root.scale = (R, R, R)
    if glint is not None:        # same as R17: one soft sphere light only the tin sheet sees (lighting unchanged)
        loc, en = glint
        li = K.point(name + "GlintR17", loc, en, (0.92, 0.94, 1.0), 0.3)
        col = bpy.data.collections.new(name + "GlintR17_Recv")
        for o_ in (ob, so):
            col.objects.link(o_)
        li.light_linking.receiver_collection = col
    return root, [ob, so]


def b208_r21():
    """R21 root cause #6 (R20 review B2_08 #3: 「收集镜的内外两层壳在画面中部叠成一片…给镜面加一点冷色掠射高光，剖切面用
    中性灰」), variant 'clean' (not gold): called from _clean_r6's post-hook when B2_08 is in R21_SHOTS.
      * outer shell / ground blank / shell edge (CollB208_substrate) -> neutral-grey MATTE (no gloss, no violet);
      * mirror face (CollB208_mirror): one cool grazing strip light on the mirrored camera ray near the rim, seen
        only by the mirror face (light linking; invisible to camera / diffuse) -> a cool highlight band that only
        the mirror carries, so face and shell separate. Mirror material untouched."""
    mir = bpy.data.objects.get("CollB208_mirror")
    sub = bpy.data.objects.get("CollB208_substrate")
    if sub is not None:
        sub.data.materials.clear()
        sub.data.materials.append(K.mat("CollShellMatteR21", (0.4, 0.405, 0.41), metal=0.15, rough=0.78))
    if mir is None:
        return
    col = bpy.data.collections.new("B208GrazeRecvR21")
    col.objects.link(mir)
    for nm, loc, tgt, sz, szy, en in (("B208GrazeR21", (-0.07, 0.63, 0.06), (-0.76, 0.06, 0.16), 1.6, 0.14, 160.0),):
        li = K.area(nm, loc, tgt, sz, en, (0.72, 0.86, 1.0), size_y=szy)
        li.visible_camera = False
        li.visible_diffuse = False
        li.light_linking.receiver_collection = col
    # + a cool emissive strip seen ONLY by glossy rays (camera / diffuse / shadow invisible): its mirror image is
    # the grazing highlight band on the face; the matte shell cannot mirror it
    mb = K.MB()
    mb.box((0, 0, 0), (0.02, 1.8, 0.035))
    st = mb.obj("B208GrazeStripR21", K.emit_mat("B208GrazeStripR21", (0.72, 0.86, 1.0), 1.6))
    st.location = (-0.02, 0.72, 0.02)
    st.rotation_euler = (0.0, 0.0, -0.75)
    for attr in ("visible_camera", "visible_diffuse", "visible_shadow", "visible_transmission", "visible_volume_scatter"):
        setattr(st, attr, False)
