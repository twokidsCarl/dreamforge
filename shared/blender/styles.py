"""Four visual languages rendered from the same scene.

  photoreal  real materials in the vacuum chamber           "this is a real thing"
  xray       dark studio, ghost-glass shells, glowing core    "what it looks like inside"
  blueprint  pale linework on deep-navy schematic, Freestyle "how it is designed"
  energy     near-black, only light / plasma / particles / rays "the invisible physics"
  clay       matte warm-white models in the dark studio       "how it is assembled / moves"
  sem        greyscale, edge-bright, electron-microscope look  "what the nanoscale looks like"

Look rules (E2 STYLE_REVIEW §4.3, P0-3): every non-photoreal style renders through AgX + Base Contrast
(no "Standard" view transform); xray and clay share one dark studio gradient (L1_WORLD_*) instead of a
near-white / mid-grey cyc, so a style change no longer flips the frame's brightness.

Builders tag objects with a `role` custom property; apply_style() swaps materials, world,
lights and line rendering per role. Untagged objects are classified automatically:
emissive or volumetric material -> emitter, camera-invisible -> rig, otherwise structure.
"""
import bpy

import common as C
import materials as M

ROLES = ("structure", "shell", "emitter", "env", "rig", "rays")
STYLES = ("photoreal", "xray", "blueprint", "energy", "clay", "sem")

# All colours below are LINEAR (Blender world / emission / linestyle inputs), converted from sRGB with
# the standard sRGB EOTF. The sRGB sources are the E2 "Deep Lab" palette
# (episodes/E2-optogenetics/mograph/e2_palette.py); keep the two in sync — this module is shared by
# every episode, so it does not import that file.
# Blueprint = deep-navy schematic (same hue family as the 2D BG_0, not the old saturated blueprint blue,
# which was sRGB #19427C here vs #0C347A in 2D):
BLUEPRINT_BG = (0.0033, 0.0130, 0.0423)     # sRGB #0B1E3A  SCHEMATIC_BG
BLUEPRINT_FILL = (0.0060, 0.0212, 0.0648)   # sRGB #122848  35% SCHEMATIC_BG -> SCHEMATIC_GRID
BLUEPRINT_LINE = (0.521, 0.672, 1.0)        # sRGB #BFD6FF  SCHEMATIC_LINE
# L1 "Lab Night" dark studio: top BG-1 -> bottom BG-0 (background mean stays <= ~35/255 after AgX)
L1_WORLD_TOP = (0.0044, 0.0080, 0.0194)     # sRGB #0E1626  BG_1
L1_WORLD_HORIZON = (0.0030, 0.0052, 0.0123)  # sRGB #0A101D  halfway BG_1 -> BG_0
L1_WORLD_BOTTOM = (0.0021, 0.0033, 0.0070)  # sRGB #070B14  BG_0
DARK_BG = L1_WORLD_BOTTOM                   # energy / sem flat world: BG-0, not pure black
# S "SEM accent": cool grey ramp with ~5% violet, sRGB #0B0F18 -> #C8D0DC (was neutral 0.035 -> 0.62)
SEM_DARK = (0.0033, 0.0048, 0.0091)
SEM_LIGHT = (0.5776, 0.6308, 0.7157)


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
    if obj.type not in ("MESH", "CURVE", "META"):
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
    ramp.color_ramp.elements[0].color = (*SEM_DARK, 1)
    ramp.color_ramp.elements[1].position = 1.0
    ramp.color_ramp.elements[1].color = (*SEM_LIGHT, 1)
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
        if sc.render.engine == "CYCLES" and not sc.get("hdri_world"):   # real reflections for metal and glass
            C.reflection_env(sc.get("hdri", "studio_small_09"), sc.get("hdri_strength", 0.35))
        return
    _non_photoreal(style, sc, objs, roles, line_px)


def _photoreal_world(sc, objs, roles):
    """Exterior shots of the source scene drop the chamber walls for a dark studio backdrop."""
    cam = sc.camera
    if cam is not None and bpy.data.objects.get("ChamberWall") is not None:   # source-chamber scenes only
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


def _l1_world():
    C.set_world(top=L1_WORLD_TOP, horizon=L1_WORLD_HORIZON, bottom=L1_WORLD_BOTTOM)


def _non_photoreal(style, sc, objs, roles, line_px):
    if style == "xray":
        _l1_world()          # was a near-white cyc (0.92 / 0.80 / 0.62) that sat above the bloom threshold
        C.set_color_management(look="Base Contrast", exposure=0.0)
        glass = ghost_glass()
        for o in objs:
            if roles[o] == "shell":
                _set_material(o, glass)
            elif roles[o] == "rays":                     # on the light studio a strong emitter clips to white:
                for slot in o.material_slots:          # a saturated, moderate violet stays violet
                    em = slot.material and slot.material.use_nodes and slot.material.node_tree.nodes.get("Emission")
                    if em:
                        em.inputs["Color"].default_value = (0.30, 0.06, 1.0, 1.0)
                        em.inputs["Strength"].default_value = 1.0
        _lights(True)
        return

    if style == "blueprint":
        _flat_world(BLUEPRINT_BG)
        C.set_color_management(look="Base Contrast", exposure=0.0)
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
        _flat_world(DARK_BG)
        C.set_color_management(look="Base Contrast", exposure=0.0)
        rim = dark_rim()
        for o in objs:
            if roles[o] in ("structure", "shell"):
                _set_material(o, rim)
            elif roles[o] == "rays":                     # a strong pastel emitter clips to a white bar on black;
                for slot in o.material_slots:          # saturated violet at a moderate strength stays violet
                    em = slot.material and slot.material.use_nodes and slot.material.node_tree.nodes.get("Emission")
                    if em:
                        em.inputs["Color"].default_value = (0.40, 0.16, 1.0, 1.0)
                        em.inputs["Strength"].default_value = min(em.inputs["Strength"].default_value, 2.2)
        _lights(False)
        return

    if style == "clay":
        _l1_world()          # was a mid-grey cyc (0.42 / 0.30 / 0.14)
        C.set_color_management(look="Base Contrast", exposure=0.0)
        clay = clay_material()
        for o in objs:
            if roles[o] in ("structure", "shell"):
                _set_material(o, clay)
        _lights(True)
        return

    if style == "sem":
        _flat_world(DARK_BG)
        C.set_color_management(look="Base Contrast", exposure=0.0)
        mat = sem_material()
        for o in objs:
            if roles[o] in ("structure", "shell"):
                _set_material(o, mat)
        _lights(False)
        sc.render.use_motion_blur = False
        sc["no_glare"] = True
        # grain, scan lines and the scale bar are added in post (tools/post_looks.py)
        return
