"""B1_05: the tin jet breaking into a "string of pearls" that coalesces into evenly spaced droplets.

Illustrates the double modulation in ASML's droplet-generator patents (F21): a fast modulation
breaks the jet into small droplets, a slower one makes groups of them catch up and merge.
Built from metaball elements whose positions are set every (sub)frame by a frame-change handler,
so motion blur sees the real motion. Geometry is illustrative, not to scale.
"""
import math

import bpy

import build_source as S
import build_vacuum as V
import common as C
import materials as M
import sample_b1 as B
import styles

FRAMES = 200
V_FLOW = 0.055          # jet speed, units per frame (slow motion)
EMIT_EVERY = 1          # one element per frame
PER_SMALL = 4           # elements per small droplet (fast modulation)
PER_BIG = 3             # small droplets per final droplet (slow modulation)
R_ELEM = 0.055
NOZZLE_Y = 0.0


def _smooth(x, a, b):
    t = min(1.0, max(0.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


def _layout(frame):
    """Positions of all live elements at `frame` (float)."""
    pts = []
    n_emitted = int(frame // EMIT_EVERY) + 1
    for i in range(n_emitted):
        age = frame - i * EMIT_EVERY
        d = age * V_FLOW                                   # distance travelled
        k, K = i // PER_SMALL, i // (PER_SMALL * PER_BIG)
        # centres of this element's small droplet and of its final droplet, along the stream
        small_c = d - ((i % PER_SMALL) - (PER_SMALL - 1) / 2) * EMIT_EVERY * V_FLOW
        j = k % PER_BIG
        big_c = small_c - (j - (PER_BIG - 1) / 2) * PER_SMALL * EMIT_EVERY * V_FLOW
        s1 = _smooth(d, 0.6, 1.6)                           # pinch into small droplets
        s2 = _smooth(d, 2.2, 3.8)                           # small droplets catch up and merge
        y_small = small_c + (big_c - small_c) * s2
        y = y_small + (d - small_c) * (1 - s1)
        # surface undulation before pinch-off (Rayleigh-Plateau look)
        wobble = 0.012 * math.sin(i * 1.7 + frame * 0.4) * (1 - s1)
        pts.append((NOZZLE_Y + y, wobble, d))
    return pts


def _update(scene, depsgraph=None):
    mb = bpy.data.metaballs.get("TinJet")
    if mb is None:
        return
    f = scene.frame_current + scene.frame_subframe
    pts = _layout(f)
    els = mb.elements
    for idx, e in enumerate(els):
        if idx < len(pts):
            y, w, d = pts[idx]
            e.co = (w, y, 0.0)
            e.radius = R_ELEM * (1.0 + 0.25 * _smooth(d, 2.2, 3.8))
            e.hide = d > 9.0
        else:
            e.hide = True


def build():
    sc = C.reset_scene(FRAMES)
    C.set_world(top=(0.012, 0.016, 0.026), horizon=(0.006, 0.008, 0.014), bottom=(0.002, 0.003, 0.005))
    C.set_color_management(exposure=0.55)
    V.chamber()
    tip, _ = S.nozzle(NOZZLE_Y)
    mb = bpy.data.metaballs.new("TinJet")
    mb.resolution = 0.012
    mb.render_resolution = 0.008
    mb.threshold = 0.6
    for _ in range(int(FRAMES / EMIT_EVERY) + 2):
        e = mb.elements.new()
        e.radius = R_ELEM
        e.stiffness = 2.2
        e.hide = True
    jet = bpy.data.objects.new("TinJet", mb)
    sc.collection.objects.link(jet)
    jet.data.materials.append(M.tin("TinJetMat", roughness=0.05))
    styles.tag(jet, "structure")
    B._lights([jet, tip])
    bpy.app.handlers.frame_change_pre.append(_update)
    # truck alongside the jet, slower than the flow so the breakup unfolds across frame
    B._camera("CamB1_05", [(25, (0, 0.75, 0), (1.25, 0.75, 0.22), 70, 2.4),
                           (70, (0, 1.4, 0), (1.3, 1.4, 0.22), 70, 2.4),
                           (FRAMES, (0, 4.2, 0), (1.5, 4.1, 0.25), 70, 2.4)])
    _update(sc)
    return sc
