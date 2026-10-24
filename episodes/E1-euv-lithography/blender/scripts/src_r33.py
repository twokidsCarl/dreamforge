"""Round 33 hook (MAIN process; r2_source.R33_SRC = {"B1_15"}), layered after src_r32 and before beam_hook_r29.

  CONE_R33 (row 4, B1_15): R32 p1 「紫锥的底只覆盖镜面右半，读起来像『等离子体直射出去』，不像『镜面反射会聚』。锥底改成整圈
           镜缘，从镜面外沿收向 IF，软边」. Cause: src_r32 cut the volume cone with the camera frustum through the mirror
           face, so only the slice right of the mirror on screen survived. R33 changes the cone's STRUCTURE, not its
           strength: the volume cone + its frustum booleans are replaced by a HOLLOW SHELL (open surface from the whole
           mirror rim to the IF tip, no caps) whose emission is edge-weighted (1 - |N . I|)^P: the two silhouette edges
           from the top and bottom of the rim glow and converge on the IF, while the part of the shell lying over the
           mirror face is nearly transparent - the mirror stays readable through the hollow cone (90/10 kept in 4-10).
Remove B1_15 from R33_SRC / CONE_R33 False -> R32 pixels.
"""
import math

import bpy
from mathutils import Vector

CONE_R33 = True
NSEG = 96
NLEN = 24
POWER = 5.0     # 8 spp at (1 - LayerWeight facing)^3: the shell over the mirror face was a pale lilac sheet
STRENGTH = 7.0
COLOR = (0.55, 0.36, 1.0)


def pre(variant, shot, mod):
    return None


def _shell_mat():
    m = bpy.data.materials.new("B115ShellR33M")
    m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    for n in list(N):
        if n.type != "OUTPUT_MATERIAL":
            N.remove(n)
    out = next(n for n in N if n.type == "OUTPUT_MATERIAL")
    geo = N.new("ShaderNodeNewGeometry")
    dt = N.new("ShaderNodeVectorMath")
    dt.operation = "DOT_PRODUCT"
    L.new(geo.outputs["Normal"], dt.inputs[0])
    L.new(geo.outputs["Incoming"], dt.inputs[1])
    ab = N.new("ShaderNodeMath")
    ab.operation = "ABSOLUTE"
    L.new(dt.outputs["Value"], ab.inputs[0])
    inv = N.new("ShaderNodeMath")
    inv.operation = "SUBTRACT"
    inv.inputs[0].default_value = 1.0
    L.new(ab.outputs[0], inv.inputs[1])
    pw = N.new("ShaderNodeMath")
    pw.operation = "POWER"
    L.new(inv.outputs[0], pw.inputs[0])
    pw.inputs[1].default_value = POWER
    em = N.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*COLOR, 1)
    em.inputs["Strength"].default_value = STRENGTH
    tr = N.new("ShaderNodeBsdfTransparent")
    mix = N.new("ShaderNodeMixShader")
    L.new(pw.outputs[0], mix.inputs[0])
    L.new(tr.outputs[0], mix.inputs[1])
    L.new(em.outputs[0], mix.inputs[2])
    L.new(mix.outputs[0], out.inputs["Surface"])
    return m


def _shell(a, tip, ra, rb, axis):
    """open cone surface a (radius ra) -> tip (radius rb), no caps."""
    axis = Vector(axis).normalized()
    u = axis.orthogonal().normalized()
    v = axis.cross(u).normalized()
    verts, faces = [], []
    for i in range(NLEN + 1):
        s = i / NLEN
        c = a.lerp(tip, s)
        r = ra + (rb - ra) * s
        for j in range(NSEG):
            t = 2 * math.pi * j / NSEG
            verts.append(tuple(c + (u * math.cos(t) + v * math.sin(t)) * r))
    for i in range(NLEN):
        for j in range(NSEG):
            k0, k1 = i * NSEG + j, i * NSEG + (j + 1) % NSEG
            faces.append((k0, k1, k1 + NSEG, k0 + NSEG))
    me = bpy.data.meshes.new("B115ShellR33")
    me.from_pydata(verts, [], faces)
    for p in me.polygons:
        p.use_smooth = True
    me.update()
    ob = bpy.data.objects.new("B115ShellR33", me)
    bpy.context.scene.collection.objects.link(ob)
    me.materials.append(_shell_mat())
    ob.visible_shadow = False
    ob.visible_diffuse = False
    ob.visible_glossy = False
    return ob


def post(sc, variant, shot):
    if not (CONE_R33 and shot == "B1_15"):
        return sc
    import src_r32 as S
    old = bpy.data.objects.get("B115ExitR32")
    if old is None:
        print("[src_r33] B1_15: no R32 cone", flush=True)
        return sc
    import beam_r29 as B29
    legs = [o for o in bpy.data.objects if o.name.startswith("B115ExitR27Leg") and "r25_radii" in o.keys()]
    l1 = next((o for o in legs if o.name.endswith("Leg1")), None) or next(o for o in legs if o.name.endswith("Leg0"))
    tip = l1.matrix_world @ B29._rings(l1)[1][0]       # same IF tip src_r32 used
    a = Vector((S.RIM_X, 0, 0))
    for o in list(bpy.data.objects):
        if o.name.startswith(("B115ExitR32", "B115FaceFrustum")):
            bpy.data.objects.remove(o, do_unlink=True)
    ob = _shell(a, tip, S.RIM_R, S.TIP_R, tip - a)
    print(f"[src_r33] B1_15 hollow shell rim r {S.RIM_R} at x {S.RIM_X} -> IF {tuple(round(x, 3) for x in tip)} "
          f"(R32 volume cone + frustum cut removed)", flush=True)
    sc.frame_set(1)
    return sc
