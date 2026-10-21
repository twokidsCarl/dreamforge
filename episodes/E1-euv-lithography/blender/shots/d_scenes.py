"""D — closing (F50). Variants:

  foup      D_01  yellow-light clean room: a wafer pod sits on a load port (plate at ~900 mm), undocks, and an overhead
                  hoist vehicle lowers its gripper on belts, lifts the pod and carries it off; every pod on the rail
                  rides in its own vehicle
  monolith  D_06  an abstract black block (double-decker-bus proportions) in a dark hall, violet light leaking from
                  its seams, low mist
  crowd     D_07  the hall lights come on row by row: silhouettes around the block; a world map of the 5100 supplier
                  dots (regional counts from the ASML Annual Report 2025, positions within a region illustrative)
All stylised; no real fab or the ASML exterior is copied; people are faceless silhouettes.

Sources (research/visual/CD_sources.md): load-port kinematic plate at ~900 mm, the OHT a cable-hoist vehicle that
lowers the FOUP onto it [Asyst/Murata US 7,410,340]; FOUP holds 26 slots, polycarbonate, size of the order of the
300 mm FOSB 389.5 x 327 x 341.8 mm [Miraial]; yellow light protects the resist [DLR PR-13]; EXE "as big as a
double-decker bus" [Intel]. The undock stroke and the FOUP envelope (SEMI E47.1) are not public: drawn as 示意.
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
EUV = (0.30, 0.06, 1.0)
TEX = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "textures")
_key, _box, _cyl = A0._key, A0._box, A0._cyl


# ---- D_01 ----------------------------------------------------------------------------------
POD = (0.39, 0.33, 0.34)                 # w x d x h, of the order of the 300 mm FOSB (Miraial); FOUP envelope not public
PLATE_Z = 0.90                           # load-port kinematic plate height (US 7,410,340)
TOOL_FACE_Y = 1.1                        # front face of the tool
RAIL_Z = 3.6
VEH_Z = RAIL_Z - 0.06 - 0.24             # vehicle body centre, hanging under the rail
VEH_H = 0.42
FLANGE_UP = POD[2] / 2 + 0.035 + 0.012   # pod centre -> top of its handling flange


def _pod(name, mat, door, flange_m):
    """A FOUP: body, a darker door face toward the tool (+y), and the top handling flange the hoist grips
    (a plate on a short neck). Parts hang under an empty so the whole pod can be keyed."""
    root = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(root)
    parts = [_box(name + "Body", (0, 0, 0), POD, mat, bevel=0.03),
             _box(name + "Door", (0, POD[1] / 2 + 0.006, 0), (POD[0] - 0.04, 0.012, POD[2] - 0.04), door, bevel=0.006),
             _box(name + "Neck", (0, 0, POD[2] / 2 + 0.0175), (0.07, 0.07, 0.035), flange_m, bevel=0.004),
             _box(name + "Flange", (0, 0, POD[2] / 2 + 0.035 + 0.006), (0.2, 0.2, 0.012), flange_m, bevel=0.004)]
    for p in parts:
        p.parent = root
    # 25 wafers (300 mm) in their slots, ~10 mm pitch, seen through the translucent shell
    wm = bpy.data.materials.get("PodWafer") or M.principled("PodWafer", (0.42, 0.43, 0.48), metallic=0.8, roughness=0.15)
    if "PodWaferMesh" not in bpy.data.meshes:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.15, depth=0.0016, vertices=48, location=(0, 0, 0))
        tmp = bpy.context.object
        tmp.data.name = "PodWaferMesh"
        tmp.data.materials.append(wm)
        bpy.data.objects.remove(tmp)
    for k in range(25):
        w = bpy.data.objects.new(f"{name}Wafer{k}", bpy.data.meshes["PodWaferMesh"])
        bpy.context.scene.collection.objects.link(w)
        styles.tag(w, "structure")
        w.parent = root
        w.location = (0, -0.01, -0.125 + 0.0104 * k)
    return root


def _vehicle(name, panel, dark):
    """An OHT vehicle hanging under the rail: body, a darker underside, and a gripper plate on four belts.
    Returns (root, gripper root, belts); belts have their origin at the top so scale z = length."""
    root = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(root)
    body = _box(name + "Body", (0, 0, 0), (0.95, 0.52, VEH_H), panel, bevel=0.03)
    under = _box(name + "Under", (0, 0, -VEH_H / 2 - 0.01), (0.86, 0.44, 0.02), dark, bevel=0.0)
    trolley = _box(name + "Trolley", (0, 0, VEH_H / 2 + 0.06), (0.5, 0.16, 0.12), dark, bevel=0.01)
    for p in (body, under, trolley):
        p.parent = root
    grip = bpy.data.objects.new(name + "Grip", None)
    bpy.context.scene.collection.objects.link(grip)
    grip.parent = root
    gp = _box(name + "GripPlate", (0, 0, 0.02), (0.3, 0.3, 0.04), dark, bevel=0.005)
    gp.parent = grip
    belts = []
    for k, (dx, dy) in enumerate(((-0.12, -0.12), (0.12, -0.12), (-0.12, 0.12), (0.12, 0.12))):
        bm = bpy.data.meshes.new(f"{name}Belt{k}")
        h = 0.5
        verts = [(x, y, z) for z in (0.0, -1.0) for (x, y) in ((-0.006, -0.02), (0.006, -0.02), (0.006, 0.02), (-0.006, 0.02))]
        faces = [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
        bm.from_pydata(verts, [], faces)
        b = bpy.data.objects.new(f"{name}Belt{k}", bm)
        bpy.context.scene.collection.objects.link(b)
        b.data.materials.append(dark)
        styles.tag(b, "structure")
        b.parent = root
        b.location = (dx, dy, -VEH_H / 2 - 0.02)
        b.scale = (1, 1, h)
        belts.append(b)
    return root, grip, belts


def _hoist_keys(grip, belts, f, drop):
    """Gripper `drop` metres below the vehicle underside; belts as long."""
    _key(grip, f, location=(0, 0, -VEH_H / 2 - 0.02 - drop - 0.04))
    for b in belts:
        _key(b, f, scale=(1, 1, max(0.001, drop)))


def foup(sc, rnd):
    C.set_world(top=(0.05, 0.035, 0.006), horizon=(0.03, 0.02, 0.004), bottom=(0.004, 0.003, 0.001))
    floor = M.pbr("YFloor", "brushed_concrete", scale=0.3, tint=(0.55, 0.5, 0.42), rough_mul=0.4, rough_add=0.08,
                  fallback=(0.3, 0.28, 0.24))
    _box("Floor", (0, 0, -0.05), (40, 40, 0.1), floor)
    panel = M.principled("ToolPanel", (0.72, 0.72, 0.7), roughness=0.5)
    dark = M.dark_anodized("Port")
    _box("ToolFace", (0, TOOL_FACE_Y + 0.1, 1.5), (4.0, 0.2, 3.0), panel, bevel=0.03)      # only the front of a tool
    seam = M.principled("ToolSeam", (0.08, 0.075, 0.06), roughness=0.6)
    glass = M.principled("EFEMWindow", (0.03, 0.03, 0.035), roughness=0.08, coat=1.0)
    _box("EFEMWindow", (0, TOOL_FACE_Y - 0.005, 1.95), (2.9, 0.01, 0.42), glass, bevel=0.01)   # generic tool front:
    for x in (-1.55, 1.55):                                                                  # a window band,
        _box(f"ToolSeamV{x}", (x, TOOL_FACE_Y - 0.004, 1.5), (0.012, 0.01, 3.0), seam, bevel=0.0)   # panel seams,
    _box("ToolSeamH", (0, TOOL_FACE_Y - 0.004, 2.55), (4.0, 0.01, 0.012), seam, bevel=0.0)  # three load ports
    _box("ToolPlinth", (0, TOOL_FACE_Y - 0.03, 0.06), (4.0, 0.06, 0.12), dark, bevel=0.005)
    pin = M.polished_steel("PinSteel", 0.2)
    for px in (-0.85, 0.0, 0.85):
        _box(f"PortOpening{px}", (px, TOOL_FACE_Y - 0.004, PLATE_Z + 0.2), (0.44, 0.01, 0.38), dark, bevel=0.005)
        _box(f"LoadPort{px}", (px, 0.72, PLATE_Z - 0.04), (0.62, 0.76, 0.08), dark)          # plate top at 0.90 m
        _box(f"PortStand{px}", (px, 0.82, (PLATE_Z - 0.08) / 2), (0.5, 0.5, PLATE_Z - 0.08), panel, bevel=0.02)
        for dx, dy in ((-0.1, 0.62), (0.1, 0.62), (0.0, 0.82)):                             # kinematic pins
            _cyl(f"Pin{px}{dx}{dy}", 0.012, 0.016, (px + dx, dy, PLATE_Z + 0.008), pin)
    pod_m = M.principled("Pod", (0.66, 0.6, 0.5), roughness=0.1, coat=0.6)       # translucent polycarbonate shell
    pod_m.node_tree.nodes["Principled BSDF"].inputs["Transmission Weight"].default_value = 0.8
    pod_m.node_tree.nodes["Principled BSDF"].inputs["IOR"].default_value = 1.58
    door = M.principled("PodDoor", (0.16, 0.13, 0.09), roughness=0.4)
    flange_m = M.principled("PodFlange", (0.55, 0.42, 0.22), roughness=0.35)
    rail = M.polished_steel("Rail", 0.3)
    rail_y = TOOL_FACE_Y - POD[1] / 2 - 0.06                       # above the undocked pod
    _box("OHTRail", (0, rail_y, RAIL_Z), (30, 0.2, 0.12), rail)
    # hero: docked on the plate (door against the port), undocks a few cm (示意), the vehicle overhead lowers its
    # gripper on belts, grips the flange, hoists the pod up into the vehicle and drives off along the rail.
    # Narration 0.3-4.6 s: lift during "每一片晶圆上的图案", away on "一层一层写出来的"
    dock_y = TOOL_FACE_Y - POD[1] / 2 - 0.004
    pz = PLATE_Z + POD[2] / 2
    hero = _pod("HeroPod", pod_m, door, flange_m)
    docked = _pod("DockedPod", pod_m, door, flange_m)                # the next port is busy
    docked.location = (-0.85, dock_y, pz)
    veh, grip, belts = _vehicle("HeroOHT", panel, dark)
    _key(veh, 1, location=(0, rail_y, VEH_Z))
    top_drop = (VEH_Z - VEH_H / 2 - 0.02) - (pz + FLANGE_UP) - 0.04     # plate bottom on the flange top
    lift_drop = 0.03
    _key(hero, 1, location=(0, dock_y, pz))
    _key(hero, 6, location=(0, dock_y, pz))
    _key(hero, 18, location=(0, rail_y, pz))                       # undock: back off the port by ~6 cm
    _hoist_keys(grip, belts, 1, lift_drop)
    _hoist_keys(grip, belts, 10, lift_drop)
    _hoist_keys(grip, belts, 32, top_drop)                         # the gripper comes down on its belts
    _hoist_keys(grip, belts, 38, top_drop)
    _key(hero, 38, location=(0, rail_y, pz))
    hoisted = VEH_Z - VEH_H / 2 - 0.02 - lift_drop - 0.04 - FLANGE_UP
    _hoist_keys(grip, belts, 74, lift_drop)
    _key(hero, 74, location=(0, rail_y, hoisted))
    _key(veh, 78, location=(0, rail_y, VEH_Z))
    _key(veh, 119, location=(3.4, rail_y, VEH_Z))
    _key(hero, 78, location=(0, rail_y, hoisted))
    _key(hero, 119, location=(3.4, rail_y, hoisted))
    # the pods behind, each carried in its own vehicle along the rail
    for k in range(4):
        v, g, bl = _vehicle(f"OHT{k}", panel, dark)
        p = _pod(f"Pod{k}", pod_m, door, flange_m)
        _hoist_keys(g, bl, 1, lift_drop)
        x0, x1 = -3.2 - 2.4 * k, -1.4 - 2.4 * k
        _key(v, 1, location=(x0, rail_y, VEH_Z))
        _key(v, 119, location=(x1, rail_y, VEH_Z))
        _key(p, 1, location=(x0, rail_y, hoisted))
        _key(p, 119, location=(x1, rail_y, hoisted))
    for ob in list(bpy.data.objects):                              # constant speed along the rail
        ad = ob.animation_data
        if ad and ad.action and (ob.name.startswith(("OHT", "Pod")) and ob.parent is None):
            for fc in C.fcurves(ad.action):
                for kp in fc.keyframe_points:
                    kp.interpolation = "LINEAR"
    yellow = M.emission("YLamp", (1.0, 0.7, 0.2), 7.0)
    for x in range(-8, 9, 3):
        _box(f"YLamp{x}", (x, -1.0, 4.2), (0.2, 4.0, 0.06), yellow, role="emitter")
    bpy.ops.object.light_add(type="AREA", location=(0, -2, 4.0))
    l = bpy.context.object
    l.data.energy = 900
    l.data.size = 8
    l.data.color = (1.0, 0.72, 0.3)
    styles.tag(l, "rig")
    B._camera("CamD_01", [(1, (-0.15, 0.8, 1.3), (1.15, -1.75, 1.15), 35, 2.8),
                          (40, (-0.05, 0.8, 1.7), (1.3, -1.95, 1.3), 35, 2.8),
                          (119, (0.9, 0.8, 2.85), (2.1, -2.7, 1.75), 35, 2.8)])


# ---- D_06 / D_07 ---------------------------------------------------------------------------
def _hall(sc, lamps_on_from=None):
    floor = M.pbr("DarkFloor", "brushed_concrete", scale=0.1, tint=(0.08, 0.085, 0.09), rough_mul=0.3, rough_add=0.03,
                  normal=0.4, fallback=(0.02, 0.022, 0.025))
    _box("Floor", (0, 0, -0.05), (120, 120, 0.1), floor)
    wall = M.principled("FarWall", (0.08, 0.085, 0.09), roughness=0.7)
    _box("FarWall", (0, 22, 8), (80, 0.4, 16), wall)
    lamps = []
    for i, y in enumerate(range(-20, 21, 5)):
        m = M.emission(f"HallLamp{i}", (0.98, 0.95, 0.88), 0.0)
        _box(f"Strip{i}", (0, y, 12.0), (40.0, 0.4, 0.1), m, role="emitter")
        lamps.append((i, m))
    return lamps


BLOCK = (10.0, 3.2, 4.5)                 # double-decker-bus proportions (Intel: "as big as a double-decker bus")


def _monolith():
    blk = M.principled("Monolith", (0.012, 0.012, 0.014), metallic=0.6, roughness=0.42)
    seam = M.emission("Seam", EUV, 6.0)                          # saturated violet: a pale violet clipped to white
    L, D, Hh = BLOCK
    _box("Block", (0, 0, Hh / 2), BLOCK, blk, bevel=0.06)
    # a few irregular panel joints on the long face, not a grid: light leaking through
    y = -D / 2 - 0.006
    for name, loc, size in (("SeamA", (0, y, 1.55), (L - 0.15, 0.012, 0.02)),
                            ("SeamB", (1.4, y, 3.05), (0.02, 0.012, 2.9)),
                            ("SeamC", (-1.9, y, 3.6), (6.0, 0.012, 0.02)),
                            ("SeamD", (-3.4, y, 0.78), (0.02, 0.012, 1.55)),
                            ("SeamE", (3.6, y, 2.3), (2.4, 0.012, 0.02))):
        _box(name, loc, size, seam, role="emitter")
    # a low cold backlight behind the block: the mist glows around its silhouette
    rot = Vector((0, -1, 0.4)).to_track_quat("-Z", "Y").to_euler()
    lt = B._area("MistBack", (0, D / 2 + 3.0, 0.5), rot, 13.0, 1400, (0.55, 0.5, 1.0), size_y=0.8)
    styles.tag(lt, "rig")


def _mist():
    """Low mist that actually reads: denser near the floor (fades out by ~1.5 m), lit by the rim light and the seams."""
    fog = bpy.data.materials.new("Mist")
    fog.use_nodes = True
    nt = fog.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    vs = nt.nodes.new("ShaderNodeVolumePrincipled")
    vs.inputs["Color"].default_value = (0.7, 0.72, 0.85, 1)
    vs.inputs["Anisotropy"].default_value = 0.65                   # forward scatter: glows toward a backlight
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sep.inputs[0])
    hgt = nt.nodes.new("ShaderNodeMapRange")                       # object z -1 (floor) .. +1 (top): dense -> clear
    hgt.inputs["From Min"].default_value = -1.0
    hgt.inputs["From Max"].default_value = 1.0
    hgt.inputs["To Min"].default_value = 1.0
    hgt.inputs["To Max"].default_value = 0.0
    nt.links.new(sep.outputs["Z"], hgt.inputs["Value"])
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 0.22
    noise.inputs["Detail"].default_value = 3.0
    wisp = nt.nodes.new("ShaderNodeMapRange")                      # contrast: wisps and gaps, not a uniform haze
    wisp.inputs["From Min"].default_value = 0.38
    wisp.inputs["From Max"].default_value = 0.68
    nt.links.new(noise.outputs["Fac"], wisp.inputs["Value"])
    m1 = nt.nodes.new("ShaderNodeMath")
    m1.operation = "MULTIPLY"
    nt.links.new(hgt.outputs["Result"], m1.inputs[0])
    nt.links.new(wisp.outputs["Result"], m1.inputs[1])
    m2 = nt.nodes.new("ShaderNodeMath")
    m2.operation = "MULTIPLY"
    m2.inputs[1].default_value = 2.2
    nt.links.new(m1.outputs[0], m2.inputs[0])
    nt.links.new(m2.outputs[0], vs.inputs["Density"])
    nt.links.new(vs.outputs[0], out.inputs["Volume"])
    _box("MistVol", (0, 0, 0.75), (60, 60, 1.5), fog, role="env")


def monolith(sc, rnd):
    C.set_world(top=(0.004, 0.005, 0.008), horizon=(0.002, 0.002, 0.004), bottom=(0.0, 0.0, 0.001))
    _hall(sc)
    _monolith()
    _mist()
    B._area("Rim", (6, 8, 7), (2.2, 0, 2.4), 6, 900, (0.6, 0.7, 1.0))
    B._camera("CamD_06", [(1, (1.0, 0, 2.2), (8.0, -10.6, 0.22), 24, 5.6), (83, (1.0, 0, 2.2), (7.0, -9.0, 0.26), 24, 5.6)])


def _person(name, loc, rnd, mat):
    import figures
    figures.person(name, (loc[0], loc[1], 0.0), height=rnd.uniform(1.62, 1.85),
                   pose=rnd.choice(("stand", "stand", "work", "walk")), facing=rnd.uniform(-180, 180), mat=mat,
                   role="structure")


def crowd(sc, rnd):
    C.set_world(top=(0.006, 0.007, 0.01), horizon=(0.003, 0.003, 0.005), bottom=(0.0, 0.0, 0.001))
    lamps = _hall(sc)
    _monolith()
    _mist()
    sil = M.principled("Suit", (0.012, 0.012, 0.014), roughness=0.9)
    L, D, _ = BLOCK
    placed = []
    while len(placed) < 34:                                         # people standing, working, talking, around
        x, y = rnd.uniform(-L / 2 - 4.5, L / 2 + 4.5), rnd.uniform(-D / 2 - 4.0, D / 2 + 3.0)   # the block, not in it
        if abs(x) < L / 2 + 0.5 and abs(y) < D / 2 + 0.5:
            continue
        if any((x - a) ** 2 + (y - b) ** 2 < 0.7 ** 2 for a, b in placed):
            continue
        placed.append((x, y))
        _person(f"P{len(placed)}", (x, y), rnd, sil)
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
    B._area("Rim", (6, 8, 7), (2.2, 0, 2.4), 6, 250, (0.6, 0.7, 1.0))      # low: it flared the block corner white
    B._camera("CamD_07", [(1, (0, 0, 2.0), (0.6, -8.5, 0.5), 28, 5.6), (154, (0, 4, 5.0), (0.0, -25.0, 6.5), 28, 5.6)])


def build(variant="foup", seed=41):
    sc = C.reset_scene(FRAMES)
    C.set_world(top=(0.03, 0.035, 0.05), horizon=(0.012, 0.014, 0.02), bottom=(0.003, 0.004, 0.006))
    C.set_color_management(exposure=0.4)
    rnd = random.Random(seed)
    {"foup": foup, "monolith": monolith, "crowd": crowd}[variant](sc, rnd)
    return sc
