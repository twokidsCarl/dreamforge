"""P1 round 2 documentary plates (Carl picks 8A night freighter + 8C cold-white clean room + 9A suited pair;
Carl decision 3: image2 plates when Blender geometry cannot reach photo realism). The plate (generated with
gpt-image-2, no logos, no faces; prompts in handoff/p1/plates/) is an emissive card filling the frame; the camera
does a slow documentary move (push / truck / micro hand-held shake) and, for D_07, the hall lights come up.

Plates live in <renders>/plates/ (not in git); pod_styleframes.py syncs renders/ to the pod.
  variants: freighter (A0_02), crates (A0_03), cleanroom (D_07)
"""
import math
import os
import random

import bpy

import common as C
import kit_r2 as K

PLATES = {"freighter": "r2_a002.png", "crates": "r2_a003_r10.png", "cleanroom": "r2_d007.png"}
# R16 tried a wide image2 plate (r2_a003_r16.png, ~hundreds of crates) -> review: counts don't match (crates >> 250,
# ~10 ULDs, 1-2 trucks). R17 (root cause 6): back to the R15 close documentary plate r2_a003_r10.png + R15 camera;
# the exact counts (10x25 crates in 5 cyan groups, 43 ULDs, 3 freighters, 20 trucks in a row) are carried by the
# flat stacked counter panel in mograph/r2_ov_zy17p.py.


def _freighter_life(n, H, aspect):
    """Foreground motion on the A0_02 plate: a backlit ground-crew silhouette walking toward the loader, a red
    anti-collision strobe on the fuselage, and fine rain streaks falling through the sodium light."""
    import figures
    from mathutils import Vector
    dark = K.mat("CrewSil", (0.006, 0.006, 0.008), rough=0.9)
    ob = figures.person("Crew", (0, 0, 0), height=2.3, pose="walk", facing=90, mat=dark, role="env")
    ob.rotation_euler = (math.radians(-90), 0, 0)             # stand up along +Y on the card (camera looks down -Z)
    ob.location = (-5.2, -4.6, 0.5)
    ob.keyframe_insert("location", frame=1)
    ob.location = (-2.6, -4.5, 0.5)
    ob.keyframe_insert("location", frame=n)
    vest = K.MB()                                            # hi-vis band catching the floodlights
    vest.box((0, 1.33, 0.25), (0.42, 0.07, 0.02))
    vo = vest.obj("CrewVest", K.emit_mat("Vest", (0.95, 0.85, 0.25), 1.6))
    vo.parent = ob
    st = K.MB()
    st.sphere((-0.6, 1.72, 0.3), 0.06, 12)
    so = st.obj("Strobe", K.emit_mat("StrobeRed", (1.0, 0.12, 0.08), 40.0))
    em = next(nd for nd in so.data.materials[0].node_tree.nodes if nd.type == "EMISSION")
    for f in range(1, n + 1):                                # 1 flash / s, 3 frames long
        v = 40.0 if (f % 24) in (0, 1, 2) or f in (35, 78, 120) and f % 24 < 12 else 0.0
        em.inputs["Strength"].default_value = v
        em.inputs["Strength"].keyframe_insert("default_value", frame=f)
    rain = K.MB()
    rnd = random.Random(11)
    for _ in range(260):
        x, y = rnd.uniform(-H * aspect / 2, H * aspect / 2), rnd.uniform(-H / 2, H / 2 + 6)
        rain.box((x, y, 0.8), (0.006, rnd.uniform(0.25, 0.5), 0.004), rot=(0, 0, math.radians(8)))
    ro = rain.obj("Rain", K.emit_mat("RainM", (0.9, 0.85, 0.75), 0.55, halo=0.22))
    ro.location = (0, 0, 0)
    ro.keyframe_insert("location", frame=1)
    ro.location = (-0.8, -6.0, 0)
    ro.keyframe_insert("location", frame=n)
    for o in (ob, ro):
        for fc in C.fcurves(o.animation_data.action):
            for k in fc.keyframe_points:
                k.interpolation = "LINEAR"


def build(variant="freighter", shot=None):
    n = K.nframes(shot) if shot else 120
    sc = C.reset_scene(n)
    K.world_dark(0.2)
    img = bpy.data.images.load(os.path.join(C.render_root(), "plates", PLATES[variant]))
    aspect = img.size[0] / img.size[1]
    m = bpy.data.materials.new("Plate")
    m.use_nodes = True
    nt = m.node_tree
    for nd in list(nt.nodes):
        if nd.type != "OUTPUT_MATERIAL":
            nt.nodes.remove(nd)
    out = next(nd for nd in nt.nodes if nd.type == "OUTPUT_MATERIAL")
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    tex.interpolation = "Cubic"
    em = nt.nodes.new("ShaderNodeEmission")
    nt.links.new(tex.outputs["Color"], em.inputs["Color"])
    nt.links.new(em.outputs[0], out.inputs["Surface"])
    H = 10.0
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0))
    pl = bpy.context.object
    pl.scale = (H * aspect, H, 1)
    pl.data.materials.append(m)
    cam, tgt = K.camera("CamR2", lens=50, sensor=36)
    cam.data.type = "ORTHO"
    cam.constraints.clear()                    # straight down onto the card, image up = +Y
    cam.rotation_euler = (0, 0, 0)
    rnd = random.Random(7)
    # ortho scale: frame width; plates are 3:2, the frame 16:9 -> width-limited crop with room to move
    if variant == "freighter":
        # R3 (H2 fix): a real push + pan toward the open nose (25 % zoom), plus moving foreground life below
        keys = [(1, -1.7, 0.1, 15.4), (n, 2.0, 0.7, 10.6)]          # R6: bigger push + pan (R5: near-static)
        lit = None
        _freighter_life(n, H, aspect)
    elif variant == "crates":
        keys = [(1, -1.6, -0.3, 13.6), (n, 1.5, 0.15, 11.6)]              # R7/R15: truck + push (R17: R16 pull-back
                                                                          # on the wide plate reverted, see PLATES)
        lit = None
    else:
        keys = [(1, 0.6, 0.0, 13.8), (n, 1.6, 0.1, 12.4)]                 # push toward the suited pair
        lit = True
    for f, x, y, w in keys:
        cam.location = (x, y, 20)
        cam.keyframe_insert("location", frame=f)
        tgt.location = (x, y, 0)
        tgt.keyframe_insert("location", frame=f)
        cam.data.ortho_scale = w
        cam.data.keyframe_insert("ortho_scale", frame=f)
    # micro hand-held shake (documentary), smooth noise on the camera only
    for fc in C.fcurves(cam.animation_data.action):
        if fc.data_path == "location" and fc.array_index in (0, 1):
            md = fc.modifiers.new("NOISE")
            md.scale = 40
            md.strength = 0.05
            md.phase = rnd.random() * 100
    em.inputs["Strength"].default_value = 1.0
    if lit:                                                                 # hall lights come up (D_07)
        em.inputs["Strength"].default_value = 0.35
        em.inputs["Strength"].keyframe_insert("default_value", frame=1)
        em.inputs["Strength"].default_value = 1.0
        em.inputs["Strength"].keyframe_insert("default_value", frame=max(2, int(n * 0.45)))
    sc["no_glare"] = True
    sc["film_grain"] = 0.18
    sc["vignette"] = 0.25
    sc["hdri_world"] = True
    sc.view_settings.view_transform = "Standard"
    sc.camera = cam
    return sc
