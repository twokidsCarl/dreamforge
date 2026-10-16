"""B1_22-B1_26: the CO2 drive-laser amplifier chain (stylised, not TRUMPF CAD).

Seed (a few W) -> pre-amplifier (100 W) -> 4 amplifier stages (to tens of kW) -> beam transport
tube toward the source vessel (F6, F25). An orange pulse runs down the chain; each stage's inner
glow steps up as it passes. explode=True flies every part outward for the clay exploded view.
"""
import math
import random

import bpy

import common as C
import materials as M
import sample_b1 as B
import styles

FRAMES = 300
ORANGE = (1.0, 0.42, 0.12)
# (name, x position, length, radius) along +X; boxes are drawn as long rounded housings
MODULES = [("Seed", 0.0, 1.2, 0.35), ("PreAmp", 2.2, 2.0, 0.5),
           ("Amp1", 5.2, 3.2, 0.75), ("Amp2", 9.4, 3.2, 0.75),
           ("Amp3", 13.6, 3.2, 0.75), ("Amp4", 17.8, 3.2, 0.75)]
TUBE_END = 34.0
PULSE_START, PULSE_END = 40, 190      # frames: pulse travels from the seed to the tube exit


def _box(name, loc, size, mat, bevel=0.04):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    ob = bpy.context.object
    ob.name = name
    ob.scale = (size[0] / 2, size[1] / 2, size[2] / 2)
    bpy.ops.object.transform_apply(scale=True)
    m = ob.modifiers.new("Bevel", "BEVEL")
    m.width = bevel
    m.segments = 3
    ob.data.materials.append(mat)
    styles.tag(ob, "structure")
    return ob


def _cyl(name, loc, r, depth, mat, rot=(0, math.pi / 2, 0), verts=48):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=depth, vertices=verts, location=loc, rotation=rot)
    ob = bpy.context.object
    ob.name = name
    for p in ob.data.polygons:
        p.use_smooth = True
    ob.data.materials.append(mat)
    styles.tag(ob, "structure")
    return ob


def _pulse_x(f):
    t = min(1.0, max(0.0, (f - PULSE_START) / (PULSE_END - PULSE_START)))
    return -0.6 + (TUBE_END + 0.6) * (t ** 1.15)


def build(explode=False, seed=5):
    sc = C.reset_scene(FRAMES)
    C.set_world(top=(0.03, 0.035, 0.05), horizon=(0.012, 0.014, 0.02), bottom=(0.003, 0.004, 0.006))
    C.set_color_management(exposure=0.5)
    rnd = random.Random(seed)
    steel = M.polished_steel("ChainSteel", 0.28)
    dark = M.dark_anodized("ChainDark")
    copper = M.principled("Copper", (0.85, 0.45, 0.28), metallic=1.0, roughness=0.3)
    parts = []
    stage_glows = []
    for i, (name, x, length, r) in enumerate(MODULES):
        cx = x + length / 2
        first = len(parts)
        body = _box(f"{name}Body", (cx, 0, 0), (length, 2 * r, 2 * r), dark, bevel=0.08)
        parts.append(body)
        for side in (-1, 1):                                      # end flanges
            parts.append(_cyl(f"{name}Flange{side}", (cx + side * (length / 2 + 0.05), 0, 0), r * 0.82, 0.12, steel))
        for k in range(max(2, int(length / 0.8))):                # top panels with seams
            parts.append(_box(f"{name}Panel{k}", (x + 0.4 + k * 0.8, 0, r + 0.04), (0.7, 2 * r * 0.9, 0.05), steel, 0.01))
        for k in range(3 if i >= 2 else 1):                        # cooling water pipes
            parts.append(_cyl(f"{name}Pipe{k}", (cx, -r - 0.12, -r * 0.5 + k * 0.25), 0.05, length * 0.95, copper,
                              verts=16))
        for k in range(int(length * 6)):                           # bolts along the flanges
            a = 2 * math.pi * k / (length * 6)
            for side in (-1, 1):
                b = _cyl(f"{name}Bolt{side}{k}", (cx + side * (length / 2 + 0.12),
                                                  0.7 * r * math.cos(a), 0.7 * r * math.sin(a)),
                         0.025, 0.06, steel, verts=8)
                parts.append(b)
        for p in parts[first:]:
            p["module"] = i
        if explode:
            continue
        # inner glow (seen through a window slot on the side)
        g = M.emission(f"{name}GlowMat", ORANGE, 0.0)  # strength keyed below
        win = _box(f"{name}Window", (cx, r + 0.001 - 2 * r, 0), (length * 0.7, 0.02, r * 0.5), g, 0.005)
        win.location.y = -r - 0.012
        styles.tag(win, "emitter")
        stage_glows.append((g, x + length / 2, 2 + 6 * i))
    first = len(parts)
    tube = _cyl("BeamTube", ((21.0 + TUBE_END) / 2, 0, 0), 0.32, TUBE_END - 21.0, steel)
    parts.append(tube)
    for k in range(8):
        parts.append(_cyl(f"TubeClamp{k}", (22.0 + k * 1.6, 0, 0), 0.4, 0.12, dark))
        parts.append(_box(f"TubeStand{k}", (22.0 + k * 1.6, 0, -0.9), (0.15, 0.4, 1.1), dark, 0.02))
    for p in parts[first:]:
        p["module"] = len(MODULES)
    # glow steps up as the pulse passes each stage (a few W -> 100 W -> tens of kW)
    for g, xc, level in stage_glows:
        s = g.node_tree.nodes["Emission"].inputs["Strength"]
        for f in range(1, FRAMES + 1, 2):
            passed = _pulse_x(f) >= xc
            s.default_value = (0.1 + 0.05 * level) if passed else 0.02
            s.keyframe_insert("default_value", frame=f)
    # the pulse itself
    pmat = M.emission("PulseMat", ORANGE, 0.0 if explode else 40.0)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.12, segments=24, ring_count=12)
    pulse = bpy.context.object
    pulse.name = "Pulse"
    pulse.scale = (4.0, 1.0, 1.0)
    pulse.data.materials.append(pmat)
    styles.tag(pulse, "emitter")
    for f in range(1, FRAMES + 1):
        pulse.location = (_pulse_x(f), 0, 0)
        pulse.keyframe_insert("location", frame=f)
    pulse.hide_render = True
    pulse.keyframe_insert("hide_render", frame=PULSE_START - 1)
    pulse.hide_render = False
    pulse.keyframe_insert("hide_render", frame=PULSE_START)
    # lights: cool key and rim; reflection cards for the steel
    B._area("Key", (10, -8, 9), (0.8, 0, -0.6), 14, 1300, (0.7, 0.8, 1.0))
    B._area("Rim", (12, 9, 4), (1.3, 0, 2.6), 12, 1800, (0.5, 0.7, 1.0))
    C.softbox("ChainSoft", (12, -6, 4), (1.2, 0, -0.4), (30, 6), 0.7, (0.75, 0.85, 1.0))
    if explode:
        # orderly exploded view: every part moves out radially from the chain axis, a little
        # along X by module, with small rotations; modules open one after another
        for p in parts:
            m = p.get("module", 0)
            radial = p.location.copy()
            radial.x = 0.0
            if radial.length < 1e-3:
                radial.z = 1.0
            radial.normalize()
            f0 = 20 + 14 * m
            p.keyframe_insert("location", frame=f0)
            p.keyframe_insert("rotation_euler", frame=f0)
            p.location = p.location + radial * rnd.uniform(0.9, 1.8) + type(radial)(((m - 3) * 0.6, 0, 0))
            r0 = p.rotation_euler.copy()
            p.rotation_euler = (r0.x + rnd.uniform(-0.15, 0.15), r0.y + rnd.uniform(-0.15, 0.15),
                                r0.z + rnd.uniform(-0.15, 0.15))
            p.keyframe_insert("location", frame=f0 + 40)
            p.keyframe_insert("rotation_euler", frame=f0 + 40)
    # cameras
    B._camera("CamB1_22", [(1, (10.0, 0, 0), (10.0, -22.0, 3.0), 50, 11.0),
                           (120, (16.0, 0, 0), (16.0, -22.0, 3.0), 50, 11.0)])
    B._camera("CamB1_23", [(40, (2.0, 0, 0), (1.5, -5.5, 1.6), 35, 4.0),
                           (220, (20.0, 0, 0), (19.0, -6.0, 2.0), 35, 4.0)])
    B._camera("CamB1_24", [(f, (_pulse_x(f) + 1.5, 0, 0), (_pulse_x(f) - 1.6, -2.4, 0.8), 24, 4.0)
                           for f in range(140, 192, 4)])
    B._camera("CamB1_26", [(1, (12.0, 0, 0), (12.0, -26.0, 9.0), 50, 11.0),
                           (180, (12.0, 0, 0), (30.0, -16.0, 11.0), 50, 11.0)])
    return sc
