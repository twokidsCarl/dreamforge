"""Round 22 (P1) hook for B8_17 (R22_ROOT_CAUSE row 5). Owned by the misc sub-agent.

R21 review B8_17 #2 「计数器到 188 时，晶圆上已曝光（变灰）的格子反而变少…让灰格随计数逐格累积，188 时铺满」 and #1 「场格不对应 188」.
Layered on top of the R20 + R21 build (188 fields of 26 x 16.5 mm, slit fixed under the barrel, stage moves):
- exposure state is driven frame by frame by the SAME curve as the counter overlay (r2_ov_zr8 'wafer': value = round(188 *
  ease(u / 0.8)), u = (f - 1) / 24 / dur): exposed-field count == counter value at every frame (field k exposed iff k < C(f)).
- colour semantics fixed: unexposed = dark polished silicon, exposed = light matte grey (the "变灰" the reviewer reads),
  only the field under the slit glows violet; no violet afterglow on exposed fields any more -> grey accumulates to full.
- the wafer stage is re-keyed per frame so the field being exposed (index C(f) - 1) sits under the fixed slit (R21 win kept).
- field grid: 26 x 16.5 mm on 300 mm; counted in code and printed (full + edge). A 300 mm disc holds at most 142 WHOLE
  26 x 16.5 fields (area bound 164), so 188 = whole fields + clipped edge fields (as a real scanner exposes them).
"""
import math

import bpy

FPS, COUNT = 24, 188


def _ease(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def counter(f, dur):
    """Counter overlay value at frame f (identical formula to r2_ov_zr8.wafer row 0)."""
    u = (f - 1) / FPS / dur
    return int(round(COUNT * _ease(u / 0.8)))


def pre(variant, shot, mod):
    pass


def _set_input(nd, name, v):
    nd.inputs[name].default_value = v


def post(sc, variant, shot):
    import common as C
    import kit_r2 as K
    import misc_b817_r20 as W20
    n = sc.frame_end
    dur = n / FPS
    R = 1.5
    order = W20.layout(R)
    full = sum(1 for (_, _, cx, cy) in order if all(math.hypot(cx + sx * W20.FX / 2, cy + sy * W20.FY / 2) <= R
                                                   for sx in (-1, 1) for sy in (-1, 1)))
    print(f"[R22 B8_17] field count = {len(order)} ({full} whole 26x16.5 mm + {len(order) - full} rim-clipped)")
    m = bpy.data.materials.get("FieldR20")
    nt = m.node_tree
    # 1) progress value: per-frame CONSTANT keys = counter / 188
    val = next(x for x in nt.nodes if x.type == "VALUE")
    ad = nt.animation_data
    if ad and ad.action:
        for fc in list(C.fcurves(ad.action)):
            for kp in list(fc.keyframe_points)[::-1]:
                fc.keyframe_points.remove(kp)
    cvals = {}
    for f in range(1, n + 2):
        c = counter(f, dur)
        cvals[f] = c
        val.outputs[0].default_value = c / COUNT + 1e-4
        val.outputs[0].keyframe_insert("default_value", frame=f)
    for fc in C.fcurves(nt.animation_data.action):
        for kp in fc.keyframe_points:
            kp.interpolation = "CONSTANT"
    # 2) colours: unexposed dark polished silicon, exposed light matte grey, no violet afterglow
    mix = next(x for x in nt.nodes if x.type == "MIX" and getattr(x, "data_type", "") == "RGBA")
    mix.inputs["A"].default_value = (*K.lin((0.13, 0.14, 0.17)), 1)
    mix.inputs["B"].default_value = (*K.lin((0.44, 0.45, 0.47)), 1)
    bs = next(x for x in nt.nodes if x.type == "BSDF_PRINCIPLED")
    bs.inputs["Metallic"].default_value = 0.0
    for x in nt.nodes:                                   # exposed * 0.1 violet afterglow -> 0
        if x.type == "MATH" and x.operation == "MULTIPLY" and abs(x.inputs[1].default_value - 0.1) < 1e-6 \
                and not x.inputs[1].is_linked:
            x.inputs[1].default_value = 0.0
    exposed = mix.inputs["Factor"].links[0].from_socket
    rr = nt.nodes.new("ShaderNodeMapRange")              # unexposed glossy 0.12 -> exposed matte 0.55
    rr.inputs["To Min"].default_value = 0.12
    rr.inputs["To Max"].default_value = 0.55
    nt.links.new(exposed, rr.inputs["Value"])
    nt.links.new(rr.outputs["Result"], bs.inputs["Roughness"])
    # 3) stage: the field being exposed now (C - 1) under the fixed slit
    rig = bpy.data.objects.get("WaferStageR21")
    if rig is not None:
        fc0 = [fc for fc in C.fcurves(rig.animation_data.action) if fc.data_path == "location"]
        sx0 = fc0[0].evaluate(1) + order[0][2]
        sy0 = fc0[1].evaluate(1) + order[0][3]
        for fc in fc0:
            for kp in list(fc.keyframe_points)[::-1]:
                fc.keyframe_points.remove(kp)
        done_ = next(f for f in range(1, n + 2) if cvals[f] >= COUNT)
        for f in range(1, done_ + 4):
            k = min(max(cvals[f] - 1, 0), COUNT - 1)
            rig.location = (sx0 - order[k][2], sy0 - order[k][3], 0.0)
            rig.keyframe_insert("location", frame=f)
        # wafer done: the stage carries the fully grey wafer back to the centred hand-over pose under the barrel
        rig.location = (sx0, sy0 - 0.35, 0.0)
        rig.keyframe_insert("location", frame=done_ + 12)
        for fc in C.fcurves(rig.animation_data.action):
            for kp in fc.keyframe_points:
                kp.interpolation = "LINEAR"
    # slit + cone switch off once the counter has reached 188 (wafer done -> all grey)
    done = next(f for f in range(1, n + 2) if cvals[f] >= COUNT)
    for ob in sc.objects:
        if ob.name.startswith("SlitConeR21") or ob.name == "Slit":
            if ob.animation_data:
                ob.animation_data_clear()
            ob.hide_render = False
            ob.keyframe_insert("hide_render", frame=1)
            ob.keyframe_insert("hide_render", frame=done + 3)
            ob.hide_render = True
            ob.keyframe_insert("hide_render", frame=done + 4)
    print(f"[R22 B8_17] counter at 56/122/189 = {cvals.get(56)}/{cvals.get(122)}/{cvals.get(189)}; slit off after {done + 3}")
