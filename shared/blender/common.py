"""Scene setup shared by every shot: reset, render presets, color management, compositor."""
import os
import bpy

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

# preset -> (resolution_x, resolution_y, eevee taa samples, cycles samples)
PRESETS = {
    "preview": (640, 360, 16, 32),
    "sample": (960, 540, 64, 64),
    "final": (1920, 1080, 128, 256),
}


def render_root():
    """Episode render root (see shared/tools/paths.py)."""
    import sys
    sys.path.insert(0, os.path.join(REPO_ROOT, "shared", "tools"))
    import paths
    return paths.RENDERS


def reset_scene(frame_end, fps=24):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.frame_start = 1
    sc.frame_end = frame_end
    sc.render.fps = fps
    return sc


def set_world(top=(0.05, 0.066, 0.1), horizon=(0.02, 0.028, 0.045), bottom=(0.006, 0.008, 0.014),
              strength=1.0):
    """Studio gradient: lighter overhead, dark below. Gives metals and mirrors something to
    reflect and keeps the background off pure black."""
    sc = bpy.context.scene
    w = bpy.data.worlds.new("World")
    sc.world = w
    w.use_nodes = True
    nt = w.node_tree
    bg = nt.nodes["Background"]
    bg.inputs["Strength"].default_value = strength
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    els = ramp.color_ramp.elements
    els[0].position, els[0].color = 0.35, (*bottom, 1)
    els[1].position, els[1].color = 1.0, (*top, 1)
    mid = els.new(0.52)
    mid.color = (*horizon, 1)
    rng = nt.nodes.new("ShaderNodeMapRange")       # direction z in [-1, 1] -> [0, 1]
    rng.inputs["From Min"].default_value = -1.0
    nt.links.new(tc.outputs["Generated"], sep.inputs[0])
    nt.links.new(sep.outputs["Z"], rng.inputs["Value"])
    nt.links.new(rng.outputs["Result"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bg.inputs["Color"])


def softbox(name, location, rotation, size, strength, color=(0.7, 0.8, 1.0), receivers=None):
    """Emissive card that shows up in reflections but not directly in camera,
    so polished metal has something to reflect against the dark world.
    receivers: optional collection; with Cycles light linking only those objects see the card."""
    import materials as M
    bpy.ops.mesh.primitive_plane_add(size=1, location=location, rotation=rotation)
    card = bpy.context.object
    card.name = name
    card.scale = (size[0], size[1], 1)
    card.visible_camera = False
    card.visible_shadow = False
    card.data.materials.append(M.soft_emitter(name + "Mat", color, strength))
    if receivers is not None:
        card.light_linking.receiver_collection = receivers
    return card


def set_color_management(look="Base Contrast", exposure=0.0):
    vs = bpy.context.scene.view_settings
    vs.view_transform = "AgX"
    vs.exposure = exposure
    # Look names differ across Blender versions ("AgX - Punchy" vs "Punchy").
    for name in (look, f"AgX - {look}"):
        try:
            vs.look = name
            return
        except TypeError:
            pass


def setup_render(engine, preset, motion_blur=True):
    sc = bpy.context.scene
    rx, ry, taa, spp = PRESETS[preset]
    sc.render.resolution_x, sc.render.resolution_y = rx, ry
    sc.render.resolution_percentage = 100
    sc.render.use_motion_blur = motion_blur
    sc.render.film_transparent = False
    if engine == "eevee":
        sc.render.engine = "BLENDER_EEVEE"
        ee = sc.eevee
        ee.taa_render_samples = taa
        ee.use_raytracing = True
        ee.volumetric_tile_size = "4"
        ee.volumetric_samples = 96
        ee.volumetric_end = 120
        ee.use_volumetric_shadows = True
    elif engine == "cycles":
        sc.render.engine = "CYCLES"
        prefs = bpy.context.preferences.addons["cycles"].preferences
        prefs.compute_device_type = "METAL"
        prefs.get_devices()
        for d in prefs.devices:
            d.use = d.type == "METAL"
        sc.cycles.device = "GPU"
        sc.cycles.samples = spp
        sc.cycles.use_denoising = True
        sc.cycles.denoiser = "OPENIMAGEDENOISE"
        sc.cycles.volume_bounces = 2
    else:
        raise ValueError(engine)


def setup_compositor(glare_strength=0.6, glare_size=7, dispersion=0.012):
    """Bloom + subtle chromatic dispersion. Blender 5.x uses a scene-level node group."""
    sc = bpy.context.scene
    ng = bpy.data.node_groups.new("Compositing", "CompositorNodeTree")
    ng.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
    n = ng.nodes
    rl = n.new("CompositorNodeRLayers")
    glare = n.new("CompositorNodeGlare")
    glare.inputs["Type"].default_value = "Bloom"
    glare.inputs["Threshold"].default_value = 0.8
    glare.inputs["Strength"].default_value = 0.0 if sc.get("no_glare") else glare_strength
    glare.inputs["Size"].default_value = glare_size / 9
    lens = n.new("CompositorNodeLensdist")
    lens.inputs["Dispersion"].default_value = dispersion
    out = n.new("NodeGroupOutput")
    ng.links.new(rl.outputs["Image"], glare.inputs["Image"])
    ng.links.new(glare.outputs["Image"], lens.inputs["Image"])
    ng.links.new(lens.outputs["Image"], out.inputs[0])
    sc.compositing_node_group = ng


def set_output(shot, engine, fmt="PNG", sub="frames"):
    sc = bpy.context.scene
    path = os.path.join(render_root(), shot, engine, sub, "")
    os.makedirs(path, exist_ok=True)
    sc.render.filepath = path
    sc.render.image_settings.file_format = fmt
    sc.render.image_settings.color_mode = "RGB"
    return path


def fcurves(action):
    # Blender 4.4+ layered actions keep fcurves inside channelbags.
    if hasattr(action, "fcurves") and len(getattr(action, "fcurves", [])):
        return list(action.fcurves)
    out = []
    for layer in getattr(action, "layers", []):
        for strip in layer.strips:
            for bag in strip.channelbags:
                out.extend(bag.fcurves)
    return out


ASSETS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "polyhaven")


def reflection_env(name="studio_small_09", strength=0.5, rotation=0.0):
    """Add a Poly Haven HDRI (CC0) to the current world for glossy rays only: the camera and diffuse
    lighting keep the designed gradient, but metals and mirrors reflect a real environment.
    No-op if the asset has not been fetched (shared/tools/fetch_assets.py)."""
    import glob
    hits = glob.glob(os.path.join(ASSETS, "hdri", f"{name}_*.hdr"))
    sc = bpy.context.scene
    if not hits or sc.world is None or not sc.world.use_nodes:
        return False
    nt = sc.world.node_tree
    bg = nt.nodes.get("Background")
    if bg is None or not bg.inputs["Color"].links:
        return False
    grad = bg.inputs["Color"].links[0].from_socket
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Rotation"].default_value = (0, 0, rotation)
    env = nt.nodes.new("ShaderNodeTexEnvironment")
    env.image = bpy.data.images.load(hits[0], check_existing=True)
    lp = nt.nodes.new("ShaderNodeLightPath")
    mul = nt.nodes.new("ShaderNodeMix")
    mul.data_type = "RGBA"
    mul.blend_type = "MULTIPLY"
    mul.inputs["Factor"].default_value = 1.0
    gain = nt.nodes.new("ShaderNodeMath")
    gain.operation = "MULTIPLY"
    gain.inputs[1].default_value = strength
    add = nt.nodes.new("ShaderNodeMix")
    add.data_type = "RGBA"
    add.blend_type = "ADD"
    nt.links.new(tc.outputs["Generated"], mp.inputs["Vector"])
    nt.links.new(mp.outputs["Vector"], env.inputs["Vector"])
    nt.links.new(lp.outputs["Is Glossy Ray"], gain.inputs[0])
    nt.links.new(gain.outputs[0], add.inputs["Factor"])
    nt.links.new(grad, add.inputs["A"])
    nt.links.new(env.outputs["Color"], add.inputs["B"])
    nt.links.new(add.outputs["Result"], bg.inputs["Color"])
    return True
