"""R25 mbeam helper (root-cause row 2): shell material variant of beam_r25.shell_mat.

beam_r25.shell_mat computes k = (1 - LayerWeight.Facing)^edge. Blender's Layer Weight 'Facing' output is 0 where the
surface faces the camera and 1 at grazing angles, so (1 - Facing) is brightest in the MIDDLE of the cone (the side
facing the lens) and dark at the silhouette = a filled column (B8_17 8-spp smoke: "solid violet vase").
This copy uses k = Facing^edge (bright silhouette shell) + a faint core, otherwise identical (ConeUV narrow-end gain,
emission + transparent mix). Used by misc_beam_r25h to re-material the legs it builds; beam_r25 itself is untouched.
"""
import bpy

import kit_r2 as K
import misc_beam_r18 as MB


def shell_mat(name, color, strength, alpha=0.6, edge=2.4, core=0.08, gain=1.2, narrow_at_end=True):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    for n in list(N):
        if n.type != "OUTPUT_MATERIAL":
            N.remove(n)
    out = next(n for n in N if n.type == "OUTPUT_MATERIAL")
    op = MB._op
    lw = N.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.5
    shell = op(N, L, "POWER", lw.outputs["Facing"], edge)
    k = op(N, L, "ADD", shell, core)
    fv = N.new("ShaderNodeValue")                  # fade multiplier (keyed by fade(); 1 = full beam)
    fv.name = "R25Fade"
    fv.outputs[0].default_value = 1.0
    k = op(N, L, "MULTIPLY", k, fv.outputs[0])
    uv = N.new("ShaderNodeUVMap")
    uv.uv_map = "ConeUV"
    sp = N.new("ShaderNodeSeparateXYZ")
    L.new(uv.outputs["UV"], sp.inputs[0])
    v = sp.outputs["Y"]
    w = v if narrow_at_end else op(N, L, "SUBTRACT", 1.0, v)
    if gain:
        k = op(N, L, "MULTIPLY", k, op(N, L, "ADD", 1.0, op(N, L, "MULTIPLY", w, gain)))
    em = N.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*K.lin(color), 1)
    L.new(op(N, L, "MULTIPLY", k, strength), em.inputs["Strength"])
    tr = N.new("ShaderNodeBsdfTransparent")
    mx = N.new("ShaderNodeMixShader")
    L.new(op(N, L, "MINIMUM", op(N, L, "MULTIPLY", k, alpha), 1.0), mx.inputs["Fac"])
    L.new(tr.outputs[0], mx.inputs[1])
    L.new(em.outputs[0], mx.inputs[2])
    L.new(mx.outputs[0], out.inputs["Surface"])
    return m


def remat(ch, color=None, strength=4.0, alpha=0.6, edge=2.4, core=0.08, gain=1.2):
    """Swap every leg's material of a beam_r25 chain for the silhouette-shell variant (same parameters)."""
    for i, leg in enumerate(ch["legs"]):
        for ob in leg:
            ra, rb = ob.get("r25_radii", (1.0, 0.0))
            m = shell_mat(ob.name + "M25s", K.VIOLET if color is None else color, strength, alpha, edge, core, gain,
                          narrow_at_end=rb <= ra)
            ob.data.materials.clear()
            ob.data.materials.append(m)


def fade(objs, keys):
    """keys = [(frame, value)]: keys the R25Fade multiplier of every leg material (smooth fade, no pop)."""
    for ob in objs:
        for m in ob.data.materials:
            nd = m.node_tree.nodes.get("R25Fade") if m and m.use_nodes else None
            if nd is None:
                continue
            for f, v in keys:
                nd.outputs[0].default_value = v
                nd.outputs[0].keyframe_insert("default_value", frame=f)
