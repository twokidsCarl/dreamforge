"""R30 row 6d, A0_06 (misc_r30.GLOBE_R30): real high-res Earth + city-lights layer, no fog shell; trunk arcs tapered
thick (origin hub) -> thin (NL landing) with a bright head on the growth front. Textures: textures/earth_r30 (NASA,
public domain, README.txt). 5100-point web / NL ring / landing dots / counters / camera are untouched."""
import math
import os

import bpy
from mathutils import Vector

EP = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
TEXD = os.path.join(EP, "blender", "textures", "earth_r30")
DAY_GAIN = 0.42          # surface albedo multiplier: night-dominant globe (R29 dusk tone 0.62 on a 2048 map)
NIGHT_STR = 7.0          # city-light emission strength on the night side
NIGHT_FLOOR = 0.6       # lights stay visible on the lit (dusk) side too
TAPER = (2.2, 0.4)      # bevel radius factor origin -> landing (R24 bevel 0.0050)
HEAD_R = 0.017
SUN_GAIN = {"Sun": 0.45, "SunRim": 0.5}   # night globe: key / rim dimmed so the city lights carry the night side
HEAD_STR = 14.0
FACE_MIN = 0.6            # = upper end of misc_r27.A006_FACE (arc fully visible)


def _fcurves(ad):
    if not ad or not ad.action:
        return []
    try:
        return list(ad.action.fcurves)
    except AttributeError:   # Blender >= 5: layered actions
        from bpy_extras.anim_utils import action_get_channelbag_for_slot
        cb = action_get_channelbag_for_slot(ad.action, ad.action_slot)
        return list(cb.fcurves) if cb else []


def _img(name, noncolor=False):
    im = bpy.data.images.load(os.path.join(TEXD, name), check_existing=True)
    if noncolor:
        im.colorspace_settings.name = "Non-Color"
    return im


def _earth_mat(sun_dir):
    m = bpy.data.materials.new("EarthRealR30")
    m.use_nodes = True
    nt = m.node_tree
    n, l = nt.nodes, nt.links
    b = next(x for x in n if x.type == "BSDF_PRINCIPLED")
    uv = n.new("ShaderNodeTexCoord")
    day = n.new("ShaderNodeTexImage")
    day.image = _img("earth_day_4096.jpg")
    day.interpolation = "Cubic"
    l.new(uv.outputs["UV"], day.inputs["Vector"])
    dk = n.new("ShaderNodeMix")
    dk.data_type = "RGBA"
    dk.blend_type = "MULTIPLY"
    dk.inputs["Factor"].default_value = 1.0
    dk.inputs["B"].default_value = (DAY_GAIN, DAY_GAIN, DAY_GAIN * 1.04, 1)
    l.new(day.outputs["Color"], dk.inputs["A"])
    l.new(dk.outputs["Result"], b.inputs["Base Color"])
    # ocean (blue > red) glossy, land matte
    sep = n.new("ShaderNodeSeparateColor")
    l.new(day.outputs["Color"], sep.inputs["Color"])
    d = n.new("ShaderNodeMath")
    d.operation = "SUBTRACT"
    l.new(sep.outputs[2], d.inputs[0])
    l.new(sep.outputs[0], d.inputs[1])
    r = n.new("ShaderNodeMapRange")
    r.inputs["From Min"].default_value = 0.0
    r.inputs["From Max"].default_value = 0.12
    r.inputs["To Min"].default_value = 0.8
    r.inputs["To Max"].default_value = 0.5
    l.new(d.outputs[0], r.inputs["Value"])
    l.new(r.outputs["Result"], b.inputs["Roughness"])
    if "Specular IOR Level" in b.inputs:
        b.inputs["Specular IOR Level"].default_value = 0.35
    # city lights: Black Marble luminance, thresholded (dark ocean tone -> 0), warm sodium colour
    nt_ = n.new("ShaderNodeTexImage")
    nt_.image = _img("earth_night_3600.jpg")
    nt_.interpolation = "Cubic"
    l.new(uv.outputs["UV"], nt_.inputs["Vector"])
    bw = n.new("ShaderNodeRGBToBW")
    l.new(nt_.outputs["Color"], bw.inputs["Color"])
    th = n.new("ShaderNodeMapRange")
    th.inputs["From Min"].default_value = 0.16
    th.inputs["From Max"].default_value = 0.85
    l.new(bw.outputs["Val"], th.inputs["Value"])
    # night side mask from the key sun direction (world normal . -sun), floor on the lit side
    geo = n.new("ShaderNodeNewGeometry")
    dp = n.new("ShaderNodeVectorMath")
    dp.operation = "DOT_PRODUCT"
    l.new(geo.outputs["Normal"], dp.inputs[0])
    dp.inputs[1].default_value = tuple(-sun_dir)
    nm = n.new("ShaderNodeMapRange")
    nm.interpolation_type = "SMOOTHSTEP"
    nm.inputs["From Min"].default_value = 0.25
    nm.inputs["From Max"].default_value = -0.15
    nm.inputs["To Min"].default_value = NIGHT_FLOOR
    nm.inputs["To Max"].default_value = 1.0
    l.new(dp.outputs["Value"], nm.inputs["Value"])
    mul = n.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    l.new(th.outputs["Result"], mul.inputs[0])
    l.new(nm.outputs["Result"], mul.inputs[1])
    mul2 = n.new("ShaderNodeMath")
    mul2.operation = "MULTIPLY"
    mul2.inputs[1].default_value = NIGHT_STR
    l.new(mul.outputs[0], mul2.inputs[0])
    b.inputs["Emission Color"].default_value = (1.0, 0.62, 0.28, 1)
    l.new(mul2.outputs[0], b.inputs["Emission Strength"])
    return m


def _head_mat(src):
    """Same view-facing fade as the arcs (R27 TrunkArcR27), brighter / whiter emission."""
    m = src.copy()
    m.name = "TrunkHeadR30"
    for x in m.node_tree.nodes:
        if x.type == "EMISSION":
            x.inputs[0].default_value = (0.8, 0.97, 1.0, 1)
            x.inputs[1].default_value = HEAD_STR
    return m


def _arcs(sc):
    arcs = [o for o in bpy.data.objects if o.name.startswith("TrunkR18_") and o.type == "CURVE"]
    head_m = None
    nh = 0
    heads = []
    for ob in arcs:
        cd = ob.data
        sp = cd.splines[0]
        N = len(sp.points)
        for i, p in enumerate(sp.points):           # thick at the supplier hub -> thin at the NL landing
            t = i / max(1, N - 1)
            p.radius = TAPER[0] + (TAPER[1] - TAPER[0]) * t
        fc = next((f for f in _fcurves(cd.animation_data) if f.data_path == "bevel_factor_end"), None)
        if fc is None:
            continue
        ks = sorted(k.co[0] for k in fc.keyframe_points)
        f0, f1 = int(ks[0]), int(math.ceil(ks[-1]))
        if head_m is None:
            head_m = _head_mat(ob.data.materials[0])
        me = bpy.data.meshes.new(ob.name + "_HeadR30")
        import bmesh
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=10, radius=HEAD_R)
        bm.to_mesh(me)
        bm.free()
        h = bpy.data.objects.new(ob.name + "_HeadR30", me)
        sc.collection.objects.link(h)
        h.data.materials.append(head_m)
        h.visible_shadow = False
        pts = [ob.matrix_world @ Vector(p.co[:3]) for p in sp.points]
        for f in range(f0, f1 + 1):
            u = max(0.0, min(1.0, fc.evaluate(f))) * (N - 1)
            i = min(N - 2, int(u))
            h.location = pts[i].lerp(pts[i + 1], u - i)
            h.keyframe_insert("location", frame=f)
        heads.append((h, f0, f1))
        nh += 1
    # visible only while the arc grows AND where the arc itself is not faded at the limb (R27 view-facing fade
    # window starts at FACE_MIN): a head without its line would read as a floating white dot
    cam = sc.camera
    vis = {h.name: [] for h, _a, _b in heads}
    fr0 = sc.frame_current
    for f in range(1, sc.frame_end + 2):
        sc.frame_set(f)
        cp = cam.matrix_world.translation
        for h, a_, b_ in heads:
            p = h.matrix_world.translation
            facing = p.normalized().dot((cp - p).normalized())
            vis[h.name].append((f, a_ < f <= b_ + 2 and facing > FACE_MIN))
    sc.frame_set(fr0)
    for h, _a, _b in heads:
        prev = None
        for f, v in vis[h.name]:
            if v != prev:
                h.hide_render = not v
                h.keyframe_insert("hide_render", frame=f)
                prev = v
    return len(arcs), nh


def apply(sc):
    g = bpy.data.objects.get("Globe")
    if g is None:
        print("[R30 A0_06] Globe missing", flush=True)
        return
    sun = bpy.data.objects.get("Sun")
    sd = (sun.matrix_world.to_quaternion() @ Vector((0, 0, -1))).normalized() if sun else Vector((0, 0, -1))
    g.data.materials.clear()
    g.data.materials.append(_earth_mat(sd))
    for nm, k in SUN_GAIN.items():
        o = bpy.data.objects.get(nm)
        if o is not None and o.type == "LIGHT":
            o.data.energy *= k
    for nm in ("GlobeAtmo",):                        # the fog shell
        o = bpy.data.objects.get(nm)
        if o is not None:
            o.hide_render = True
    na, nh = _arcs(sc)
    print(f"[R30 A0_06] GLOBE_R30: real earth 4096 + city lights, fog shell off, {na} arcs tapered, {nh} heads",
          flush=True)
