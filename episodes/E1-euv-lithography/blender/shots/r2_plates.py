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

PLATES = {"freighter": "r2_a002.png", "crates": "r2_a003.png", "cleanroom": "r2_d007.png"}


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
        keys = [(1, 0.0, 0.4, 14.6), (n, 0.9, 0.35, 13.6)]               # push-in toward the open nose
        lit = None
    elif variant == "crates":
        keys = [(1, -1.2, -0.2, 13.4), (n, 1.0, 0.0, 13.0)]               # truck along the crate row
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
