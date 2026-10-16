"""B9 — photon rain (F47). One variant, three shots on one timeline:

  B9_04  (1-130)    one 1 nm x 1 nm cell above the dark resist; violet photons drop in one by one, ~20
  B9_05  (141-248)  ultra slow motion: the camera falls with one photon, ripples where photons land
  B9_06  (261-421)  rise to a 20 x 20 field of cells; Poisson counts make an uneven, flickering mosaic
Counts are drawn from a Poisson distribution with mean 20 (illustrative).
"""
import math
import random

import bpy
from mathutils import Vector

import common as C
import materials as M
import sample_b1 as B
import styles

FRAMES = 430
VIOLET = (0.62, 0.45, 1.0)
CYAN = (0.2, 0.85, 0.95)
N = 20                       # cells per side in B9_06
MEAN = 20


def _key(ob, f, **kw):
    for k, v in kw.items():
        setattr(ob, k, v)
        ob.keyframe_insert(k, frame=f)


def _poisson(rnd, lam):
    L, k, p = math.exp(-lam), 0, 1.0
    while True:
        p *= rnd.random()
        if p <= L:
            return k
        k += 1


def _level(count):
    """Tile brightness for a photon count; the spread is exaggerated so a ±20% count reads (示意)."""
    return 0.07 * max(0.0, count - 9) ** 1.1


def _photon(name, mat, loc, radius=0.045, stretch=3.0):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, segments=16, ring_count=8, location=loc)
    ob = bpy.context.object
    ob.name = name
    ob.scale = (1, 1, stretch)                        # a short streak along the fall
    ob.data.materials.append(mat)
    styles.tag(ob, "emitter")
    return ob


def _ripple(name, mat, loc, f, size=0.35):
    bpy.ops.mesh.primitive_torus_add(major_radius=1.0, minor_radius=0.04, location=loc)
    r = bpy.context.object
    r.name = name
    r.data.materials.append(mat)
    styles.tag(r, "emitter")
    _key(r, 1, hide_render=True)
    _key(r, f, hide_render=False, scale=(0.02, 0.02, 1))
    _key(r, f + 10, scale=(size, size, 1))
    _key(r, f + 11, hide_render=True)
    return r


def _drop(ob, f_land, loc, height=6.0, dur=10, slow=False):
    x, y, z = loc
    _key(ob, 1, hide_render=True)
    _key(ob, f_land - dur, hide_render=False, location=(x, y, z + height))
    _key(ob, f_land, location=(x, y, z + 0.02))
    _key(ob, f_land + 1, hide_render=True)
    for fc in C.fcurves(ob.animation_data.action):
        if fc.data_path == "location":
            for kp in fc.keyframe_points:
                kp.interpolation = "BEZIER" if slow else "LINEAR"


def rain(sc, rnd):
    C.set_world(top=(0, 0, 0), horizon=(0, 0, 0), bottom=(0, 0, 0))
    resist = M.principled("Resist", (0.03, 0.025, 0.04), roughness=0.5)
    bpy.ops.mesh.primitive_plane_add(size=60, location=(0, 0, -0.01))
    pl = bpy.context.object
    pl.data.materials.append(resist)
    styles.tag(pl, "structure")
    line = M.emission("GridLine", CYAN, 1.6)
    half = N / 2
    for i in range(N + 1):                                         # cell grid, 1 unit = 1 nm
        for ax in ("x", "y"):
            v = i - half
            bpy.ops.mesh.primitive_cube_add(location=(v, 0, 0.005) if ax == "x" else (0, v, 0.005))
            b = bpy.context.object
            b.scale = (0.008, half, 0.004) if ax == "x" else (half, 0.008, 0.004)
            b.data.materials.append(line)
            styles.tag(b, "emitter")
            centre = v in (-1.0, 0.0)                               # the B9_04 cell's own lines show first
            _key(b, 1, hide_render=not centre)
            _key(b, 250, hide_render=not centre)
            _key(b, 262, hide_render=False)
    # tiles: brightness = photons received
    tiles = {}
    for i in range(N):
        for j in range(N):
            m = M.emission(f"Tile{i}_{j}", (0.42, 0.22, 1.0), 0.0)
            bpy.ops.mesh.primitive_plane_add(size=0.96, location=(i - half + 0.5, j - half + 0.5, 0.0))
            t = bpy.context.object
            t.data.materials.append(m)
            styles.tag(t, "emitter")
            tiles[(i, j)] = m
    centre = (int(half) - 1, int(half) - 1)                         # the cell spanning x, y in [-1, 0]
    cx, cy = centre[0] - half + 0.5, centre[1] - half + 0.5
    pm = M.emission("PhotonMat", (0.78, 0.6, 1.0), 9.0)
    rm = M.emission("RippleMat", (0.6, 0.42, 1.0), 2.0)
    # ---- B9_04: ~20 photons into the centre cell
    n0 = 20
    for k in range(n0):
        f = 14 + int(k * 5.2)
        loc = (cx + rnd.uniform(-0.42, 0.42), cy + rnd.uniform(-0.42, 0.42), 0.0)
        _drop(_photon(f"P4_{k}", pm, loc), f, loc, height=7.0, dur=12)
        _ripple(f"R4_{k}", rm, loc, f, size=0.25)
    s = tiles[centre].node_tree.nodes["Emission"].inputs["Strength"]
    for k in range(n0 + 1):
        s.default_value = 0.045 * k
        s.keyframe_insert("default_value", frame=14 + int(max(0, k - 1) * 5.2) + (1 if k else 0))
    # ---- B9_05: one hero photon falls with the camera; neighbours rain around it
    hero_loc = (cx + 0.1, cy - 0.15, 0.0)
    hero = _photon("Hero", pm, hero_loc, radius=0.06, stretch=2.0)
    _key(hero, 1, hide_render=True)
    _key(hero, 141, hide_render=False, location=(hero_loc[0], hero_loc[1], 6.0))
    _key(hero, 230, location=(hero_loc[0], hero_loc[1], 0.6))
    _key(hero, 240, location=(hero_loc[0], hero_loc[1], 0.03))
    _key(hero, 241, hide_render=True)
    _ripple("RHero", rm, hero_loc, 240, size=0.5)
    for k in range(40):
        loc = (cx + rnd.uniform(-2.5, 2.5), cy + rnd.uniform(-2.5, 2.5), 0.0)
        f = 150 + int(rnd.uniform(0, 95))
        _drop(_photon(f"P5_{k}", pm, loc), f, loc, height=6.0, dur=40)
        _ripple(f"R5_{k}", rm, loc, f, size=0.3)
    # ---- B9_06: Poisson mosaic across 20 x 20 cells, with a visible rain on top
    counts = {key: _poisson(rnd, MEAN) for key in tiles}
    for key, m in tiles.items():
        st = m.node_tree.nodes["Emission"].inputs["Strength"]
        base = 0.045 * MEAN if key == centre else 0.0
        st.default_value = base
        st.keyframe_insert("default_value", frame=262)
        for f in range(270, 381, 10):                               # accumulate with flicker
            frac = (f - 262) / (380 - 262)
            st.default_value = _level(counts[key]) * frac * rnd.uniform(0.8, 1.2)
            st.keyframe_insert("default_value", frame=f)
        st.default_value = _level(counts[key])
        st.keyframe_insert("default_value", frame=392)
    for k in range(260):
        loc = (rnd.uniform(-half, half), rnd.uniform(-half, half), 0.0)
        f = 270 + int(rnd.uniform(0, 120))
        _drop(_photon(f"P6_{k}", pm, loc, radius=0.06, stretch=4.0), f, loc, height=9.0, dur=10)
    B._camera("CamB9_04", [(1, (cx, cy, 0.0), (cx, cy - 4.2, 3.2), 50, 11.0), (130, (cx, cy, 0.0), (cx, cy - 3.0, 2.0), 50, 11.0)])
    B._camera("CamB9_05", [(141, (hero_loc[0], hero_loc[1] + 0.4, 5.2), (hero_loc[0] - 0.4, hero_loc[1] - 1.2, 6.4), 35, 11.0),
                           (230, (hero_loc[0], hero_loc[1] + 0.4, 0.2), (hero_loc[0] - 0.4, hero_loc[1] - 1.2, 1.1), 35, 11.0),
                           (248, (hero_loc[0], hero_loc[1] + 0.2, 0.0), (hero_loc[0] - 0.4, hero_loc[1] - 1.3, 0.7), 35, 11.0)])
    B._camera("CamB9_06", [(261, (cx, cy, 0.0), (cx, cy - 2.4, 1.6), 35, 11.0),
                           (421, (0.0, 0.0, 0.0), (0.0, -3.0, 30.0), 35, 11.0)])


def build(variant="rain", seed=91):
    sc = C.reset_scene(FRAMES)
    C.set_color_management(exposure=0.4)
    rain(sc, random.Random(seed))
    return sc
