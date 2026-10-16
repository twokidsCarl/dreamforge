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


def multilayer_mirror(name="MoSiMirror", r_max=7.0):
    """Mo/Si coated mirror: near-perfect polish; thin-film interference whose thickness drifts
    with radius gives concentric iridescent bands. The visible-light rainbow is an artistic cue
    for the multilayer, not a physical EUV effect."""
    m = principled(name, (0.62, 0.60, 0.66), metallic=1.0, roughness=0.035,
                   thin_film=420.0, thin_film_ior=2.0)
    nt = m.node_tree
    tc = nt.nodes.new("ShaderNodeTexCoord")
    radial = nt.nodes.new("ShaderNodeVectorMath")
    radial.operation = "MULTIPLY"
    radial.inputs[1].default_value = (0, 1, 1)        # distance from the optical (X) axis
    length = nt.nodes.new("ShaderNodeVectorMath")
    length.operation = "LENGTH"
    rng = nt.nodes.new("ShaderNodeMapRange")
    rng.inputs["From Max"].default_value = r_max
    rng.inputs["To Min"].default_value = 300.0
    rng.inputs["To Max"].default_value = 620.0
    nt.links.new(tc.outputs["Object"], radial.inputs[0])
    nt.links.new(radial.outputs["Vector"], length.inputs[0])
    nt.links.new(length.outputs["Value"], rng.inputs["Value"])
    nt.links.new(rng.outputs["Result"], nt.nodes["Principled BSDF"].inputs["Thin Film Thickness"])
    rng.inputs["To Min"].default_value = 250.0
    rng.inputs["To Max"].default_value = 900.0
    # faint concentric tint so the bands survive AgX desaturation
    bands = nt.nodes.new("ShaderNodeMath")
    bands.operation = "MULTIPLY"
    bands.inputs[1].default_value = 3.0 / r_max
    nt.links.new(length.outputs["Value"], bands.inputs[0])
    frac = nt.nodes.new("ShaderNodeMath")
    frac.operation = "FRACT"
    nt.links.new(bands.outputs[0], frac.inputs[0])
    tint = nt.nodes.new("ShaderNodeValToRGB")
    els = tint.color_ramp.elements
    els[0].position, els[0].color = 0.0, (0.72, 0.62, 0.48, 1)
    els[1].position, els[1].color = 1.0, (0.72, 0.62, 0.48, 1)
    for pos, col in ((0.25, (0.52, 0.62, 0.78)), (0.5, (0.68, 0.52, 0.74)), (0.75, (0.5, 0.72, 0.66))):
        e = els.new(pos)
        e.color = (*col, 1)
    nt.links.new(frac.outputs[0], tint.inputs["Fac"])
    nt.links.new(tint.outputs["Color"], nt.nodes["Principled BSDF"].inputs["Base Color"])
    return m


def beam(name, color, radius, length):
    """Laser beam stand-in on a Z-aligned cylinder: soft radial falloff (hot core, faint halo)
    and a travelling front. Keyframe the front with set_beam(); strength via EmissionScale."""
    m, nodes, links = _new(name)
    nodes.remove(nodes["Principled BSDF"])
    tc = nodes.new("ShaderNodeTexCoord")
    sep = nodes.new("ShaderNodeSeparateXYZ")
    links.new(tc.outputs["Object"], sep.inputs[0])
    xy = nodes.new("ShaderNodeVectorMath")
    xy.operation = "MULTIPLY"
    xy.inputs[1].default_value = (1, 1, 0)
    rlen = nodes.new("ShaderNodeVectorMath")
    rlen.operation = "LENGTH"
    links.new(tc.outputs["Object"], xy.inputs[0])
    links.new(xy.outputs["Vector"], rlen.inputs[0])
    core = nodes.new("ShaderNodeMapRange")          # 1 on the axis -> 0 at the rim
    core.inputs["From Max"].default_value = radius
    core.inputs["To Min"].default_value = 1.0
    core.inputs["To Max"].default_value = 0.0
    links.new(rlen.outputs["Value"], core.inputs["Value"])
    sharp = nodes.new("ShaderNodeMath")
    sharp.operation = "POWER"
    sharp.inputs[1].default_value = 3.0
    links.new(core.outputs["Result"], sharp.inputs[0])
    front = nodes.new("ShaderNodeMapRange")         # lit behind the front, dark ahead of it
    front.name = "Front"
    front.inputs["From Min"].default_value = length / 2
    front.inputs["From Max"].default_value = length / 2 - 1.5
    links.new(sep.outputs["Z"], front.inputs["Value"])
    mask = nodes.new("ShaderNodeMath")
    mask.operation = "MULTIPLY"
    links.new(sharp.outputs[0], mask.inputs[0])
    links.new(front.outputs["Result"], mask.inputs[1])
    strength = nodes.new("ShaderNodeMath")
    strength.operation = "MULTIPLY"
    strength.name = "EmissionScale"
    strength.inputs[1].default_value = 0.0
    links.new(mask.outputs[0], strength.inputs[0])
    vol = nodes.new("ShaderNodeEmission")
    vol.inputs["Color"].default_value = (*color, 1)
    links.new(strength.outputs[0], vol.inputs["Strength"])
    links.new(vol.outputs[0], nodes["Material Output"].inputs["Volume"])
    return m


def set_beam(mat, frame, front=None, strength=None):
    """front: position of the leading edge along the beam's local Z (-L/2 .. +L/2)."""
    nodes = mat.node_tree.nodes
    if front is not None:
        f = nodes["Front"]
        f.inputs["From Min"].default_value = front
        f.inputs["From Max"].default_value = front - 1.5
        f.inputs["From Min"].keyframe_insert("default_value", frame=frame)
        f.inputs["From Max"].keyframe_insert("default_value", frame=frame)
    if strength is not None:
        s = nodes["EmissionScale"].inputs[1]
        s.default_value = strength
        s.keyframe_insert("default_value", frame=frame)


def debris():
    """Glowing tin fragments: white-violet when young, cooling to orange, then fading.
    Uses Particle Info, so it is meant for particle instances."""
    m, nodes, links = _new("Debris")
    nodes.remove(nodes["Principled BSDF"])
    info = nodes.new("ShaderNodeParticleInfo")
    frac = nodes.new("ShaderNodeMath")
    frac.operation = "DIVIDE"
    links.new(info.outputs["Age"], frac.inputs[0])
    links.new(info.outputs["Lifetime"], frac.inputs[1])
    col = nodes.new("ShaderNodeValToRGB")
    e = col.color_ramp.elements
    e[0].position, e[0].color = 0.0, (0.85, 0.75, 1.0, 1)
    e[1].position, e[1].color = 0.35, (1.0, 0.45, 0.12, 1)
    links.new(frac.outputs[0], col.inputs["Fac"])
    fade = nodes.new("ShaderNodeMapRange")
    fade.inputs["To Min"].default_value = 60.0
    fade.inputs["To Max"].default_value = 0.0
    links.new(frac.outputs[0], fade.inputs["Value"])
    em = nodes.new("ShaderNodeEmission")
    links.new(col.outputs["Color"], em.inputs["Color"])
    links.new(fade.outputs["Result"], em.inputs["Strength"])
    links.new(em.outputs[0], nodes["Material Output"].inputs["Surface"])
    return m


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
