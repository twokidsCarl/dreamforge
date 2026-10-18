"""Four visual languages rendered from the same scene.

  photoreal  real materials in the vacuum chamber           "this is a real thing"
  xray       light studio, ghost-glass shells, glowing core   "what it looks like inside"
  blueprint  white linework on blue, Freestyle               "how it is designed"
  energy     black, only light / plasma / particles / rays   "the invisible physics"
  clay       matte warm-white models on a soft studio cyc      "how it is assembled / moves"
  sem        greyscale, edge-bright, electron-microscope look  "what the nanoscale looks like"

Builders tag objects with a `role` custom property; apply_style() swaps materials, world,
lights and line rendering per role. Untagged objects are classified automatically:
emissive or volumetric material -> emitter, camera-invisible -> rig, otherwise structure.
"""
import bpy

import common as C
import materials as M

ROLES = ("structure", "shell", "emitter", "env", "rig", "rays")
STYLES = ("photoreal", "xray", "blueprint", "energy", "clay", "sem")

BLUEPRINT_BG = (0.010, 0.055, 0.20)
BLUEPRINT_FILL = (0.016, 0.075, 0.25)
BLUEPRINT_LINE = (0.86, 0.93, 1.0)


def tag(obj, role):
    assert role in ROLES, role
    obj["role"] = role
    return obj


def tag_new(before, role):
    """Tag every object created since `before` (a set of objects)."""
    for o in bpy.data.objects:
        if o not in before:
            tag(o, role)


def role_of(obj):
    if "role" in obj:
        return obj["role"]
    if obj.type != "MESH" and obj.type != "CURVE":
        return "rig"
    if not obj.visible_camera:
        return "rig"
    for slot in obj.material_slots:
        m = slot.material
        if m and m.use_nodes:
            out = m.node_tree.nodes.get("Material Output")
            if out and out.inputs["Volume"].is_linked:
                return "emitter"
            if any(n.type == "EMISSION" for n in m.node_tree.nodes):
                return "emitter"
    return "structure"


def _set_material(obj, mat):
    if obj.type not in ("MESH", "CURVE"):
        return
    obj.data.materials.clear()
    obj.data.materials.append(mat)
    for mod in obj.modifiers:
        if mod.type == "SOLIDIFY":
            mod.material_offset = 0
            mod.material_offset_rim = 0


def ghost_glass(name="GhostGlass", tint=(0.85, 0.9, 0.96), edge=0.9):
    """Cheap X-ray shell: transparent face-on, milky-white at grazing angles."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.remove(nt.nodes["Principled BSDF"])
    lw = nt.nodes.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.35
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.25
    ramp.color_ramp.elements[0].color = (0, 0, 0, 1)
    ramp.color_ramp.elements[1].position = 1.0
    ramp.color_ramp.elements[1].color = (edge, edge, edge, 1)
    gloss = nt.nodes.new("ShaderNodeBsdfGlossy")
    gloss.inputs["Color"].default_value = (*tint, 1)
    gloss.inputs["Roughness"].default_value = 0.08
    transp = nt.nodes.new("ShaderNodeBsdfTransparent")
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(lw.outputs["Facing"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], mix.inputs["Fac"])
    nt.links.new(transp.outputs[0], mix.inputs[1])
    nt.links.new(gloss.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
    m.surface_render_method = "BLENDED"
    return m


def dark_rim(name="EnergyRim", color=(0.15, 0.4, 1.0), strength=1.2):
    """Energy-view structure: see-through, only a thin glowing silhouette (additive), so the
    light inside shells stays visible."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.remove(nt.nodes["Principled BSDF"])
    lw = nt.nodes.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.12
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.55
    ramp.color_ramp.elements[0].color = (0, 0, 0, 1)
    ramp.color_ramp.elements[1].position = 1.0
    ramp.color_ramp.elements[1].color = (1, 1, 1, 1)
    mul = nt.nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    mul.inputs[1].default_value = strength
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*color, 1)
    transp = nt.nodes.new("ShaderNodeBsdfTransparent")
    add = nt.nodes.new("ShaderNodeAddShader")
    nt.links.new(lw.outputs["Facing"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], mul.inputs[0])
    nt.links.new(mul.outputs[0], em.inputs["Strength"])
    nt.links.new(transp.outputs[0], add.inputs[0])
    nt.links.new(em.outputs[0], add.inputs[1])
    nt.links.new(add.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
    m.surface_render_method = "BLENDED"
    return m


def clay_material(name="Clay"):
    return M.principled(name, (0.70, 0.68, 0.64), metallic=0.0, roughness=0.55)


def sem_material(name="SEM"):
    """Secondary-electron look: surfaces seen edge-on glow brighter than those facing the beam."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.remove(nt.nodes["Principled BSDF"])
    lw = nt.nodes.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.5
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.15
    ramp.color_ramp.elements[0].color = (0.035, 0.035, 0.035, 1)
    ramp.color_ramp.elements[1].position = 1.0
    ramp.color_ramp.elements[1].color = (0.62, 0.62, 0.62, 1)
    ramp.color_ramp.interpolation = "EASE"
    em = nt.nodes.new("ShaderNodeEmission")
    nt.links.new(lw.outputs["Facing"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], em.inputs["Color"])
    nt.links.new(em.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
    return m


def _flat_world(color, strength=1.0):
    sc = bpy.context.scene
    w = bpy.data.worlds.new("StyleWorld")
    sc.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (*color, 1)
    bg.inputs["Strength"].default_value = strength


def _lights(enabled):
    for o in bpy.data.objects:
        if o.type == "LIGHT" and "keep_light" not in o:
            o.hide_render = not enabled


def _freestyle(thickness):
    sc = bpy.context.scene
    sc.render.use_freestyle = True
    sc.render.line_thickness_mode = "ABSOLUTE"
    sc.render.line_thickness = thickness
    vl = bpy.context.view_layer
    fs = vl.freestyle_settings
    fs.crease_angle = 2.4  # ~137 deg: only real edges, not smooth-shading facets
    ls = fs.linesets[0] if fs.linesets else fs.linesets.new("Visible")
    ls.select_by_visibility = True
    ls.visibility = "VISIBLE"
    ls.select_silhouette = ls.select_border = ls.select_crease = True
    if ls.linestyle is None:
        ls.linestyle = bpy.data.linestyles.new("BlueprintLines")
    ls.linestyle.color = BLUEPRINT_LINE
    ls.linestyle.thickness = thickness
    hidden = fs.linesets.new("Hidden")
    hidden.select_by_visibility = True
    hidden.visibility = "HIDDEN"
    hidden.select_silhouette = hidden.select_border = True
    hidden.select_crease = False
    hidden.linestyle = bpy.data.linestyles.new("HiddenLines")
    hidden.linestyle.color = BLUEPRINT_LINE
    hidden.linestyle.alpha = 0.28
    hidden.linestyle.thickness = thickness * 0.6
    hidden.linestyle.use_dashed_line = True
    hidden.linestyle.dash1, hidden.linestyle.gap1 = 6, 5


def apply_style(style, line_px=1.3):
    """Rewrite the built scene into one of STYLES. Call after build(), before rendering."""
    assert style in STYLES, style
    sc = bpy.context.scene
    objs = list(bpy.data.objects)
    roles = {o: role_of(o) for o in objs}
    show = {"photoreal": {"structure", "emitter", "env", "rig", "shell"},
            "xray": {"structure", "shell", "emitter", "rays"},
            "blueprint": {"structure", "shell"},
            "energy": {"structure", "shell", "emitter", "rays"},
            "clay": {"structure", "shell", "emitter"},
            "sem": {"structure", "shell"}}[style]
    for o in objs:
        if roles[o] in ROLES and roles[o] not in show:
            o.hide_render = True
            o.hide_viewport = True
            if o.animation_data and o.animation_data.action:
                # keep render visibility from being re-enabled by keyframes
                for fc in C.fcurves(o.animation_data.action):
                    if fc.data_path == "hide_render":
                        fc.mute = True

    if style == "photoreal":
        _photoreal_world(sc, objs, roles)
        if sc.render.engine == "CYCLES":                          # real reflections for metal and glass
            C.reflection_env(sc.get("hdri", "studio_small_09"), sc.get("hdri_strength", 0.35))
        return
    _non_photoreal(style, sc, objs, roles, line_px)


def _photoreal_world(sc, objs, roles):
    """Exterior shots of the source scene drop the chamber walls for a dark studio backdrop."""
    cam = sc.camera
    if cam is not None:
        import build_vacuum as V
        sc.frame_set(sc.frame_current)
        p = cam.matrix_world.translation
        if (p.x ** 2 + p.y ** 2) ** 0.5 > V.CHAMBER_R * 0.95:
            # exterior view: no chamber walls; dark product-studio backdrop instead
            for o in objs:
                if roles[o] == "env":
                    o.hide_render = o.hide_viewport = True
            C.set_world(top=(0.06, 0.07, 0.085), horizon=(0.025, 0.028, 0.034),
                        bottom=(0.008, 0.009, 0.011))
            for o in objs:
                if roles[o] == "shell":
                    o.hide_render = o.hide_viewport = False


def _non_photoreal(style, sc, objs, roles, line_px):
    if style == "xray":
        C.set_world(top=(0.92, 0.93, 0.95), horizon=(0.80, 0.81, 0.84), bottom=(0.62, 0.63, 0.66))
        C.set_color_management(look="Base Contrast", exposure=0.0)
        glass = ghost_glass()
        for o in objs:
            if roles[o] == "shell":
                _set_material(o, glass)
        _lights(True)
        return

    if style == "blueprint":
        _flat_world(BLUEPRINT_BG)
        sc.view_settings.view_transform = "Standard"
        sc.view_settings.look = "None"
        sc.view_settings.exposure = 0.0
        fill = M.emission("BlueprintFill", BLUEPRINT_FILL, 1.0)
        for o in objs:
            if roles[o] in ("structure", "shell"):
                _set_material(o, fill)
        _lights(False)
        sc.render.use_motion_blur = False
        if sc.camera:
            sc.camera.data.dof.use_dof = False
        _freestyle(line_px)
        return

    if style == "energy":
        _flat_world((0.0, 0.0, 0.0))
        rim = dark_rim()
        for o in objs:
            if roles[o] in ("structure", "shell"):
                _set_material(o, rim)
        _lights(False)
        return

    if style == "clay":
        C.set_world(top=(0.42, 0.42, 0.41), horizon=(0.30, 0.30, 0.29), bottom=(0.14, 0.14, 0.135))
        C.set_color_management(look="Base Contrast", exposure=-0.2)
        clay = clay_material()
        for o in objs:
            if roles[o] in ("structure", "shell"):
                _set_material(o, clay)
        _lights(True)
        return

    if style == "sem":
        _flat_world((0.0, 0.0, 0.0))
        sc.view_settings.view_transform = "Standard"
        sc.view_settings.look = "None"
        sc.view_settings.exposure = 0.0
        mat = sem_material()
        for o in objs:
            if roles[o] in ("structure", "shell"):
                _set_material(o, mat)
        _lights(False)
        sc.render.use_motion_blur = False
        sc["no_glare"] = True
        # grain, scan lines and the scale bar are added in post (tools/post_looks.py)
        return
