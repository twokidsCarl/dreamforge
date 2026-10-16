"""D — closing (F50). Variants:

  foup      D_01  yellow-light clean room: a wafer pod slides out of a load port, an overhead hoist lifts it away
  monolith  D_06  an abstract black block in a dark hall, violet light leaking from its seams, low mist
  crowd     D_07  the hall lights come on row by row: backlit people around the block; a world map of
                  5100 supplier dots lights up on the far wall
All stylised; no real fab or the ASML exterior is copied; people are faceless silhouettes.
"""
import math
import os
import random

import bpy
from mathutils import Vector

import a0_scenes as A0
import common as C
import materials as M
import sample_b1 as B
import styles

FRAMES = 160
VIOLET = (0.62, 0.45, 1.0)
TEX = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "textures")
_key, _box, _cyl = A0._key, A0._box, A0._cyl


# ---- D_01 ----------------------------------------------------------------------------------
def _pod(name, loc, mat, lid):
    return _box(name, loc, (0.42, 0.38, 0.34), mat, bevel=0.04)


def foup(sc, rnd):
    C.set_world(top=(0.05, 0.035, 0.006), horizon=(0.03, 0.02, 0.004), bottom=(0.004, 0.003, 0.001))
    floor = M.principled("YFloor", (0.3, 0.28, 0.24), roughness=0.25)
    _box("Floor", (0, 0, -0.05), (40, 40, 0.1), floor)
    panel = M.principled("ToolPanel", (0.72, 0.72, 0.7), roughness=0.5)
    _box("ToolFace", (0, 1.2, 1.5), (4.0, 0.2, 3.0), panel, bevel=0.03)      # only the front of a tool
    _box("LoadPort", (0, 0.7, 0.9), (0.9, 0.8, 0.08), M.dark_anodized("Port"))
    pod_m = M.principled("Pod", (0.75, 0.55, 0.25), roughness=0.3)
    pb = pod_m.node_tree.nodes["Principled BSDF"]
    pb.inputs["Transmission Weight"].default_value = 0.4
    lid = M.dark_anodized("PodLid")
    rail = M.polished_steel("Rail", 0.3)
    _box("OHTRail", (0, 0.3, 3.6), (30, 0.2, 0.12), rail)
    hero = _pod("HeroPod", (0, 1.0, 1.12), pod_m, lid)
    _key(hero, 1, location=(0, 1.1, 1.12))
    _key(hero, 30, location=(0, 0.6, 1.12))
    hoist = _box("Hoist", (0, 0.6, 3.35), (0.6, 0.5, 0.4), panel, bevel=0.03)
    _key(hoist, 1, location=(-1.2, 0.6, 3.35))
    _key(hoist, 30, location=(0, 0.6, 3.35))
    _key(hero, 50, location=(0, 0.6, 1.12))
    _key(hero, 80, location=(0, 0.6, 2.9))
    _key(hoist, 80, location=(0, 0.6, 3.35))
    _key(hero, 111, location=(3.0, 0.6, 2.9))
    _key(hoist, 111, location=(3.0, 0.6, 3.35))
    for k in range(5):                                             # the pods behind, one after another
        p = _pod(f"Pod{k}", (0, 0, 0), pod_m, lid)
        _key(p, 1, location=(-3.0 - 1.4 * k, 0.6, 2.9))
        _key(p, 111, location=(-0.6 - 1.4 * k, 0.6, 2.9))
    yellow = M.emission("YLamp", (1.0, 0.7, 0.2), 7.0)
    for x in range(-8, 9, 3):
        _box(f"YLamp{x}", (x, -1.0, 4.2), (0.2, 4.0, 0.06), yellow, role="emitter")
    bpy.ops.object.light_add(type="AREA", location=(0, -2, 4.0))
    l = bpy.context.object
    l.data.energy = 900
    l.data.size = 8
    l.data.color = (1.0, 0.72, 0.3)
    styles.tag(l, "rig")
    B._camera("CamD_01", [(1, (0, 0.6, 1.4), (1.6, -3.2, 0.9), 35, 2.8), (111, (0.8, 0.6, 2.4), (2.4, -3.4, 1.4), 35, 2.8)])


# ---- D_06 / D_07 ---------------------------------------------------------------------------
def _hall(sc, lamps_on_from=None):
    floor = M.principled("DarkFloor", (0.02, 0.022, 0.025), roughness=0.08)
    _box("Floor", (0, 0, -0.05), (120, 120, 0.1), floor)
    wall = M.principled("FarWall", (0.08, 0.085, 0.09), roughness=0.7)
    _box("FarWall", (0, 22, 8), (80, 0.4, 16), wall)
    lamps = []
    for i, y in enumerate(range(-20, 21, 5)):
        m = M.emission(f"HallLamp{i}", (0.98, 0.95, 0.88), 0.0)
        _box(f"Strip{i}", (0, y, 12.0), (40.0, 0.4, 0.1), m, role="emitter")
        lamps.append((i, m))
    return lamps


def _monolith():
    blk = M.principled("Monolith", (0.012, 0.012, 0.014), metallic=0.6, roughness=0.25)
    seam = M.emission("Seam", VIOLET, 4.0)
    _box("Block", (0, 0, 3.0), (6.0, 3.2, 6.0), blk, bevel=0.06)
    # a few irregular panel joints, not a grid: light leaking through
    for name, loc, size in (("SeamA", (0, -1.61, 2.1), (5.9, 0.01, 0.015)), ("SeamB", (0.9, -1.61, 4.05), (0.015, 0.01, 3.8)),
                            ("SeamC", (-1.05, -1.61, 4.8), (3.9, 0.01, 0.015)), ("SeamD", (-2.2, -1.61, 1.05), (0.015, 0.01, 2.1))):
        _box(name, loc, size, seam, role="emitter")


def _mist():
    fog = bpy.data.materials.new("Mist")
    fog.use_nodes = True
    nt = fog.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    vs = nt.nodes.new("ShaderNodeVolumePrincipled")
    vs.inputs["Density"].default_value = 0.05
    vs.inputs["Color"].default_value = (0.75, 0.75, 0.85, 1)
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 0.4
    mul = nt.nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    mul.inputs[1].default_value = 0.08
    nt.links.new(noise.outputs["Fac"], mul.inputs[0])
    nt.links.new(mul.outputs[0], vs.inputs["Density"])
    nt.links.new(vs.outputs[0], out.inputs["Volume"])
    _box("MistVol", (0, 0, 0.6), (60, 60, 1.2), fog, role="env")


def monolith(sc, rnd):
    C.set_world(top=(0.004, 0.005, 0.008), horizon=(0.002, 0.002, 0.004), bottom=(0.0, 0.0, 0.001))
    _hall(sc)
    _monolith()
    _mist()
    B._area("Rim", (6, 8, 7), (2.2, 0, 2.4), 6, 900, (0.6, 0.7, 1.0))
    B._camera("CamD_06", [(1, (0, 0, 3.6), (1.2, -13.0, 0.25), 24, 5.6), (75, (0, 0, 3.6), (0.9, -11.2, 0.3), 24, 5.6)])


def _person(name, loc, rnd, mat):
    x, y = loc
    h = rnd.uniform(1.62, 1.85)
    body = _cyl(name + "B", 0.22, h * 0.62, (x, y, h * 0.31 + 0.25), mat, verts=16)
    body.scale = (1.0, 0.7, 1.0)
    legs = _cyl(name + "L", 0.17, 0.5, (x, y, 0.25), mat, verts=12)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.13, segments=16, ring_count=8, location=(x, y, h * 0.62 + 0.4))
    hd = bpy.context.object
    hd.data.materials.append(mat)
    styles.tag(hd, "structure")


def crowd(sc, rnd):
    C.set_world(top=(0.006, 0.007, 0.01), horizon=(0.003, 0.003, 0.005), bottom=(0.0, 0.0, 0.001))
    lamps = _hall(sc)
    _monolith()
    _mist()
    sil = M.principled("Suit", (0.012, 0.012, 0.014), roughness=0.9)
    for i in range(36):                                             # people standing, working, talking
        ang = rnd.uniform(0, 2 * math.pi)
        r = rnd.uniform(4.0, 11.0)
        x, y = r * math.cos(ang), r * math.sin(ang) * 0.8
        if abs(x) < 3.5 and abs(y) < 2.2:
            continue
        _person(f"P{i}", (x, y), rnd, sil)
    for i, m in lamps:                                              # rows of lights switch on, near to far
        M.set_emission_strength(m, 10 + 6 * i, 0.0)
        M.set_emission_strength(m, 14 + 6 * i, 6.0)
    for i, (name, strength, f0) in enumerate((("worldmap_land.png", 0.35, 40), ("worldmap_dots.png", 4.0, 70))):
        img = bpy.data.images.load(os.path.join(TEX, name), check_existing=True)
        mat = M.emission(f"Map{i}", (0.25, 0.85, 0.95) if i else (0.5, 0.6, 0.8), 0.0)
        nt = mat.node_tree
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = img
        tr = nt.nodes.new("ShaderNodeBsdfTransparent")
        mix = nt.nodes.new("ShaderNodeMixShader")
        nt.links.new(tex.outputs["Color"], mix.inputs["Fac"])
        nt.links.new(tr.outputs[0], mix.inputs[1])
        nt.links.new(nt.nodes["Emission"].outputs[0], mix.inputs[2])
        nt.links.new(mix.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
        mat.surface_render_method = "BLENDED"
        bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 21.75 - 0.01 * i, 8.0))
        mp = bpy.context.object
        mp.scale = (28, 14, 1)
        mp.rotation_euler = (math.pi / 2, 0, 0)
        mp.data.materials.append(mat)
        styles.tag(mp, "emitter")
        M.set_emission_strength(mat, f0, 0.0)
        M.set_emission_strength(mat, f0 + 40, strength)
    B._area("Rim", (6, 8, 7), (2.2, 0, 2.4), 6, 900, (0.6, 0.7, 1.0))
    B._camera("CamD_07", [(1, (0, 0, 2.0), (0.6, -7.5, 0.5), 28, 5.6), (145, (0, 4, 5.0), (0.0, -26.0, 7.0), 28, 5.6)])


def build(variant="foup", seed=41):
    sc = C.reset_scene(FRAMES)
    C.set_world(top=(0.03, 0.035, 0.05), horizon=(0.012, 0.014, 0.02), bottom=(0.003, 0.004, 0.006))
    C.set_color_management(exposure=0.4)
    rnd = random.Random(seed)
    {"foup": foup, "monolith": monolith, "crowd": crowd}[variant](sc, rnd)
    return sc
