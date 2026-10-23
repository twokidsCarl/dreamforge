"""Round 18 (P1) helpers for r2_source (source chamber) - tin variants only (cold / prepulse / track); the amps
variant (B1_22 gold control) never calls this module.

R18 root cause #4 ("the tin has nothing to reflect": geometry right since R17, but the pancake reads as chalk /
plaster and the droplet as a glass bead) - LIGHTING / ENVIRONMENT ONLY, no tin material parameter is touched:

  env_dome_r18   a shapeless chamber environment that only the tin sees: an invisible sphere around the tin whose
                 INSIDE, seen by a reflected ray that starts inside it (transparent depth 0, back face), is a dark
                 chamber-steel gradient with a few soft bright bands (no edges, no cards). Every other ray passes
                 straight through it (camera rays, shadow rays, rays from outside: the chamber renders as before).
                 So the liquid tin mirrors a dark room with soft bright bands = liquid-metal reflections instead of
                 the large lit wall modules that gave the white matte blotches.
  grazing_r18    one or two soft sphere lights light-linked to the tin only, at grazing angles to the sheet /
                 droplet: thin travelling highlights along the ripples and the rim.
"""
import math

import bpy

import kit_r2 as K

BASE = (0.0, 0.0, 0.0)       # additive: the tin keeps mirroring the real (dark) chamber
# (axis, centre, half-width, strength, colour): soft rings on the dome (dot(dir, axis) == centre)
BANDS_DEFAULT = (((0.0, 0.0, 1.0), 0.42, 0.10, 1.6, (0.86, 0.9, 1.0)),       # a high cool ring
                 ((0.55, -0.35, 0.76), -0.25, 0.06, 0.9, (0.8, 0.86, 1.0)),  # a tilted thin band
                 ((0.0, 0.0, 1.0), 1.0, 0.22, 0.5, (0.7, 0.78, 1.0)),        # soft overhead glow
                 ((-0.3, 0.9, -0.3), 0.55, 0.12, 0.35, (0.55, 0.6, 0.85)))   # dim far-wall wash


def _m(nt, op, a, b=None, v=None):
    n = nt.nodes.new("ShaderNodeMath")
    n.operation = op
    nt.links.new(a, n.inputs[0])
    if b is not None:
        nt.links.new(b, n.inputs[1])
    elif v is not None:
        n.inputs[1].default_value = v
    return n.outputs[0]


def env_material_r18(name, bands=BANDS_DEFAULT, base=BASE, gain=1.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for nd in list(nt.nodes):
        if nd.type != "OUTPUT_MATERIAL":
            nt.nodes.remove(nd)
    out = next(nd for nd in nt.nodes if nd.type == "OUTPUT_MATERIAL")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nrm = nt.nodes.new("ShaderNodeVectorMath")
    nrm.operation = "NORMALIZE"
    nt.links.new(tc.outputs["Object"], nrm.inputs[0])
    col = nt.nodes.new("ShaderNodeRGB")
    col.outputs[0].default_value = (*base, 1)
    acc = col.outputs[0]
    for axis, c, w, st, rgb in bands:
        dp = nt.nodes.new("ShaderNodeVectorMath")
        dp.operation = "DOT_PRODUCT"
        nt.links.new(nrm.outputs[0], dp.inputs[0])
        ln = math.sqrt(sum(a * a for a in axis))
        dp.inputs[1].default_value = tuple(a / ln for a in axis)
        d = _m(nt, "ABSOLUTE", _m(nt, "SUBTRACT", dp.outputs["Value"], v=c))
        mr = nt.nodes.new("ShaderNodeMapRange")
        mr.interpolation_type = "SMOOTHSTEP"
        mr.inputs["From Min"].default_value = 0.0
        mr.inputs["From Max"].default_value = w
        mr.inputs["To Min"].default_value = st * gain
        mr.inputs["To Max"].default_value = 0.0
        nt.links.new(d, mr.inputs["Value"])
        sc = nt.nodes.new("ShaderNodeVectorMath")
        sc.operation = "SCALE"
        sc.inputs[0].default_value = rgb
        nt.links.new(mr.outputs["Result"], sc.inputs["Scale"])
        ad = nt.nodes.new("ShaderNodeVectorMath")
        ad.operation = "ADD"
        nt.links.new(acc, ad.inputs[0])
        nt.links.new(sc.outputs[0], ad.inputs[1])
        acc = ad.outputs[0]
    # fully transparent everywhere PLUS an additive emission that only shows on the inside (back face) and never
    # to camera / shadow rays; light linking (env_dome_r18 receivers) limits the emission to the tin
    lp = nt.nodes.new("ShaderNodeLightPath")
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    notcam = _m(nt, "LESS_THAN", _m(nt, "ADD", lp.outputs["Is Shadow Ray"], lp.outputs["Is Camera Ray"]), v=0.5)
    fac = _m(nt, "MULTIPLY", geo.outputs["Backfacing"], notcam)
    em = nt.nodes.new("ShaderNodeEmission")
    nt.links.new(acc, em.inputs["Color"])
    nt.links.new(fac, em.inputs["Strength"])
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    ad = nt.nodes.new("ShaderNodeAddShader")
    nt.links.new(tr.outputs[0], ad.inputs[0])
    nt.links.new(em.outputs[0], ad.inputs[1])
    nt.links.new(ad.outputs[0], out.inputs["Surface"])
    return m


def env_dome_r18(name, centre, radius, receivers, bands=BANDS_DEFAULT, base=BASE, gain=1.0, rot=(0, 0, 0)):
    """The invisible shapeless environment sphere (see module doc); its emission is light-linked to receivers
    (the tin objects) only. rot turns the band layout."""
    mb = K.MB()
    mb.sphere((0, 0, 0), radius, 48)
    ob = mb.obj(name, env_material_r18(name + "Mat", bands, base, gain))
    ob.location = centre
    ob.rotation_euler = rot
    ob.visible_shadow = False
    ob.visible_diffuse = False
    ob.visible_volume_scatter = False
    ob.visible_transmission = False
    col = bpy.data.collections.new(name + "_Recv")
    for o_ in receivers:
        col.objects.link(o_)
    ob.light_linking.receiver_collection = col
    return ob


def tin_objects():
    """Every liquid-tin object of the scene (material LiquidTin*), droplets / pancake / crown."""
    return [o for o in bpy.data.objects if o.type == "MESH" and o.active_material is not None
            and o.active_material.name.startswith("LiquidTin")]


def tighten_glint_r18(radius=0.07, energy_scale=0.8):
    """The R17 pancake glint (one linked sphere light, radius 0.3) drew a large soft white patch on the rippled
    sheet = the 'white matte blotch'. Same light, small radius: a crisp liquid-metal highlight instead."""
    for o in bpy.data.objects:
        if o.type == "LIGHT" and "GlintR17" in o.name:
            o.data.shadow_soft_size = radius
            o.data.energy *= energy_scale


def grazing_r18(name, receivers, lights):
    """lights = [(loc, energy, radius)]: soft sphere lights only the receivers see (light linking)."""
    col = bpy.data.collections.new(name + "_Recv")
    for o_ in receivers:
        col.objects.link(o_)
    out = []
    for i, (loc, en, rad) in enumerate(lights):
        li = K.point(f"{name}{i}", loc, en, (0.93, 0.95, 1.0), rad)
        li.light_linking.receiver_collection = col
        out.append(li)
    return out


def dark_wall_in_reflections_r18(mat_names=("ChamberDarkR10",), keep=0.3):
    """The big smooth vessel wall, lit by the fills, was what the rippled tin mirrored over most of its face (a
    uniform pale patch = 'chalk'). The wall looks exactly as before to the camera; only when it is SEEN IN A
    REFLECTION (glossy ray) it is darker (x keep): the tin mirrors a dark chamber, the soft dome bands and the
    bright hardware, i.e. liquid-metal contrast. Wall material only - the tin shader is untouched."""
    for nm in mat_names:
        m = bpy.data.materials.get(nm)
        if m is None or not m.use_nodes:
            continue
        nt = m.node_tree
        out = next(nd for nd in nt.nodes if nd.type == "OUTPUT_MATERIAL" and nd.is_active_output)
        lk = out.inputs["Surface"].links
        if not lk:
            continue
        src = lk[0].from_socket
        lp = nt.nodes.new("ShaderNodeLightPath")
        fac = _m(nt, "MULTIPLY", lp.outputs["Is Glossy Ray"], v=1.0 - keep)
        blk = nt.nodes.new("ShaderNodeEmission")
        blk.inputs["Strength"].default_value = 0.0
        mx = nt.nodes.new("ShaderNodeMixShader")
        nt.links.new(fac, mx.inputs["Fac"])
        nt.links.new(src, mx.inputs[1])
        nt.links.new(blk.outputs[0], mx.inputs[2])
        nt.links.new(mx.outputs[0], out.inputs["Surface"])


def tighten_light_r18(name, radius):
    """Same light, same energy, smaller sphere: a large soft sphere light next to the sheet mirrors as a large pale
    patch over the whole face (B1_10: the violet 'previous plasma' afterglow at 0.43 m, radius 0.25 = the lavender
    chalk); a small one gives a crisp highlight."""
    o = bpy.data.objects.get(name)
    if o is not None and o.type == "LIGHT":
        o.data.shadow_soft_size = radius


def bands_around(r0, s1=2.0, s2=1.2):
    """Two soft bands laid across the direction r0 the sheet mirrors toward the camera (so they actually cross the
    face): one near-horizontal, one oblique; plus the default soft overhead glow."""
    from mathutils import Vector
    r = Vector(r0).normalized()
    u = r.cross(Vector((0, 0, 1))).normalized()
    v = u.cross(r).normalized()
    w = (u * 0.6 + v * 0.8).normalized()
    return ((tuple(v), 0.10, 0.07, s1, (0.88, 0.92, 1.0)),
            (tuple(w), -0.22, 0.09, s2, (0.8, 0.86, 1.0)),
            ((0.0, 0.0, 1.0), 1.0, 0.22, 0.5, (0.7, 0.78, 1.0)))
