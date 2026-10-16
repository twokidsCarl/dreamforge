"""Material library. Colors are linear RGB."""
import bpy


def _new(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    return m, m.node_tree.nodes, m.node_tree.links


def principled(name, color, metallic=0.0, roughness=0.3, emission=None, emission_strength=0.0,
               thin_film=0.0, thin_film_ior=1.5, coat=0.0):
    m, nodes, _ = _new(name)
    b = nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Metallic"].default_value = metallic
    b.inputs["Roughness"].default_value = roughness
    b.inputs["Coat Weight"].default_value = coat
    if emission:
        b.inputs["Emission Color"].default_value = (*emission, 1)
        b.inputs["Emission Strength"].default_value = emission_strength
    if thin_film:
        b.inputs["Thin Film Thickness"].default_value = thin_film  # nm
        b.inputs["Thin Film IOR"].default_value = thin_film_ior
    return m


def tin(name="Tin", roughness=0.06):
    # Molten tin: bright, slightly warm liquid metal.
    return principled(name, (0.80, 0.79, 0.77), metallic=1.0, roughness=roughness)


def polished_steel(name="Steel", roughness=0.18):
    return principled(name, (0.55, 0.57, 0.60), metallic=1.0, roughness=roughness)


def dark_anodized(name="DarkMetal"):
    return principled(name, (0.035, 0.04, 0.05), metallic=0.8, roughness=0.35)


def multilayer_mirror(name="MoSiMirror"):
    """Mo/Si coated mirror: near-perfect polish, thin-film interference gives the iridescent sheen.
    The visible-light rainbow is an artistic cue for the multilayer, not a physical EUV effect."""
    return principled(name, (0.62, 0.60, 0.66), metallic=1.0, roughness=0.04,
                      thin_film=420.0, thin_film_ior=2.0)


def emission(name, color, strength):
    """Pure emitter whose strength can be keyframed via mat.node_tree.nodes['Emission'].inputs[1]."""
    m, nodes, links = _new(name)
    nodes.remove(nodes["Principled BSDF"])
    e = nodes.new("ShaderNodeEmission")
    e.inputs["Color"].default_value = (*color, 1)
    e.inputs["Strength"].default_value = strength
    links.new(e.outputs[0], nodes["Material Output"].inputs["Surface"])
    return m


def soft_emitter(name, color, strength):
    """Emitter whose strength falls off quadratically from the centre of a plane to its edges,
    so reflections read as soft studio lights instead of hard rectangles."""
    m, nodes, links = _new(name)
    nodes.remove(nodes["Principled BSDF"])
    tc = nodes.new("ShaderNodeTexCoord")
    mp = nodes.new("ShaderNodeMapping")
    mp.inputs["Location"].default_value = (-1, -1, 0)
    mp.inputs["Scale"].default_value = (2, 2, 1)
    grad = nodes.new("ShaderNodeTexGradient")
    grad.gradient_type = "QUADRATIC_SPHERE"
    mul = nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    mul.inputs[1].default_value = strength
    e = nodes.new("ShaderNodeEmission")
    e.inputs["Color"].default_value = (*color, 1)
    links.new(tc.outputs["Generated"], mp.inputs["Vector"])
    links.new(mp.outputs["Vector"], grad.inputs["Vector"])
    links.new(grad.outputs["Fac"], mul.inputs[0])
    links.new(mul.outputs[0], e.inputs["Strength"])
    links.new(e.outputs[0], nodes["Material Output"].inputs["Surface"])
    return m


def volume_glow(name, color, density, emission_strength, noise_scale=0.0, falloff=False,
                core_color=None):
    """Emissive volume. With falloff=True density fades radially from the object origin
    (object coordinates, radius 1). Keyframe via set_volume_strength()."""
    m, nodes, links = _new(name)
    nodes.remove(nodes["Principled BSDF"])
    out = nodes["Material Output"]
    vol = nodes.new("ShaderNodeVolumePrincipled")
    vol.inputs["Color"].default_value = (*color, 1)
    vol.inputs["Emission Color"].default_value = (*color, 1)
    vol.inputs["Emission Strength"].default_value = emission_strength
    vol.inputs["Density"].default_value = density
    vol.name = "Volume"
    dens = None
    if falloff:
        tc = nodes.new("ShaderNodeTexCoord")
        length = nodes.new("ShaderNodeVectorMath")
        length.operation = "LENGTH"
        links.new(tc.outputs["Object"], length.inputs[0])
        ramp = nodes.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].position = 0.0
        ramp.color_ramp.elements[0].color = (1, 1, 1, 1)
        ramp.color_ramp.elements[1].position = 1.0
        ramp.color_ramp.elements[1].color = (0, 0, 0, 1)
        ramp.color_ramp.interpolation = "EASE"
        links.new(length.outputs["Value"], ramp.inputs["Fac"])
        dens = ramp.outputs["Color"]
        if core_color:
            hue = nodes.new("ShaderNodeValToRGB")
            hue.color_ramp.elements[0].position = 0.0
            hue.color_ramp.elements[0].color = (*core_color, 1)
            hue.color_ramp.elements[1].position = 0.7
            hue.color_ramp.elements[1].color = (*color, 1)
            links.new(length.outputs["Value"], hue.inputs["Fac"])
            links.new(hue.outputs["Color"], vol.inputs["Emission Color"])
    if noise_scale:
        tc = nodes.get("Texture Coordinate") or nodes.new("ShaderNodeTexCoord")
        noise = nodes.new("ShaderNodeTexNoise")
        noise.name = "Noise"
        noise.noise_dimensions = "4D"
        noise.inputs["Scale"].default_value = noise_scale
        noise.inputs["Detail"].default_value = 6.0
        noise.inputs["Roughness"].default_value = 0.6
        links.new(tc.outputs["Object"], noise.inputs["Vector"])
        # raise contrast so the volume breaks into filaments instead of a smooth ball
        wisps = nodes.new("ShaderNodeMapRange")
        wisps.inputs["From Min"].default_value = 0.42
        wisps.inputs["From Max"].default_value = 0.72
        links.new(noise.outputs["Fac"], wisps.inputs["Value"])
        mul = nodes.new("ShaderNodeMath")
        mul.operation = "MULTIPLY"
        links.new(wisps.outputs["Result"], mul.inputs[0])
        if dens is not None:
            links.new(dens, mul.inputs[1])
        else:
            mul.inputs[1].default_value = 1.0
        dens = mul.outputs[0]
    if dens is not None:
        # Principled Volume emission ignores density, so drive both from the same field
        # to get soft edges instead of a uniformly glowing ball.
        for label, value, socket in (("DensityScale", density, "Density"),
                                     ("EmissionScale", emission_strength, "Emission Strength")):
            scale = nodes.new("ShaderNodeMath")
            scale.operation = "MULTIPLY"
            scale.inputs[1].default_value = value
            scale.name = label
            links.new(dens, scale.inputs[0])
            links.new(scale.outputs[0], vol.inputs[socket])
    links.new(vol.outputs[0], out.inputs["Volume"])
    return m


def set_volume_strength(mat, frame, emission_strength=None, density=None):
    nodes = mat.node_tree.nodes
    vol = nodes["Volume"]
    if emission_strength is not None:
        s = nodes["EmissionScale"].inputs[1] if "EmissionScale" in nodes else vol.inputs["Emission Strength"]
        s.default_value = emission_strength
        s.keyframe_insert("default_value", frame=frame)
    if density is not None:
        target = nodes["DensityScale"].inputs[1] if "DensityScale" in nodes else vol.inputs["Density"]
        target.default_value = density
        target.keyframe_insert("default_value", frame=frame)


def set_emission_strength(mat, frame, strength):
    s = mat.node_tree.nodes["Emission"].inputs["Strength"]
    s.default_value = strength
    s.keyframe_insert("default_value", frame=frame)
