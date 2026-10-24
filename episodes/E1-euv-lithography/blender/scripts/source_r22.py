"""Round 22 (P1) hook for A0_01 / B1_10 / B1_08 (R22_ROOT_CAUSE row 3). Owned by the tin sub-agent.

Called by the scene module's build(): pre(variant, shot, module) before the build, post(sc, variant, shot) after it.
  A0_01 / B1_10  pancake: source_r21.pancake_r21 -> source_r22_tin.pancake_r22 (irregular flung film + broken drops)
  A0_01 / B1_08  droplet: continuous gradient reflection dome (no band rings) + one thin rim light (tin untouched)
  A0_01          plasma beat: bigger glow (~1/6 frame height) + collector bowl/hole lit by the plasma (defocused)
"""
import math

import bpy
from mathutils import Vector

ROW3_PANCAKE = {"A0_01", "B1_10"}
ROW3_DROP = {"A0_01", "B1_08"}
ROW3_PLASMA = {"A0_01"}


def pre(variant, shot, mod):
    if shot in ROW3_PANCAKE:
        import source_r21 as S21
        import source_r22_tin as T
        S21.pancake_r21 = T.pancake_r22


def _ob(n):
    return bpy.data.objects.get(n)


def post(sc, variant, shot):
    import source_r22_tin as T
    import kit_r2 as K
    if shot == "A0_01":
        T.smooth_env_r22("TinEnvR22", (0, 0, 0.0), 0.06, [_ob("Droplet")])
        # parent the dome to the falling droplet so it surrounds it (radius 0.06 > droplet r 0.016)
        dome = _ob("TinEnvR22")
        dome.parent = _ob("Droplet")
        dome.location = (0, 0, 0)
        # dome only around the first droplet: the next droplet gets the same dome via its own copy
        d2 = T.smooth_env_r22("TinEnvR22b", (0, 0, 0.0), 0.06, [_ob("DropletNext")])
        d2.parent = _ob("DropletNext")
        d2.location = (0, 0, 0)
        # thin rim: big disc light straight behind the droplet as seen from the frame-72 camera
        cam = Vector((0.535, -0.403, 0.14))
        dp = Vector((0, 0, 0.066))
        back = (dp - cam).normalized()
        li = T.rim_light_r22("TinRimR22", (0, 0, 0), (0, 0, 0), 0.4, RIM_E["A0_01"], [_ob("Droplet")])
        li.data.shape = "DISK"
        li.parent = _ob("Droplet")
        li.location = back * 0.15
        li.rotation_euler = (-back).to_track_quat("-Z", "Y").to_euler()
        _plasma_a001(sc, K)
    elif shot == "B1_08":
        drops = [o for o in bpy.data.objects if o.type == "MESH" and o.name.startswith("Drop")
                 and o.name[4:].isdigit()]
        for d in drops:
            dm = T.smooth_env_r22("TinEnvR22_" + d.name, (0, 0, 0), 0.05, [d])
            dm.parent = d
            dm.location = (0, 0, 0)
        # rim: one wide camera-invisible panel behind the droplet column (camera looks along +Y)
        li = T.rim_light_r22("TinRimR22", (0.0, 0.2, 0.05), (0.0, -1.0, 0.05), 0.75, RIM_E["B1_08"], drops,
                             size_y=1.2)
        li.data.shape = "RECTANGLE"


RIM_E = {"A0_01": 1.6, "B1_08": 4.0}


def _plasma_a001(sc, K):
    boom, n = 166, sc.frame_end
    # glow ~1/6 of the frame height: the soft violet cloud grows
    for nm, s in (("PlasmaVol2", 1.7), ("PlasmaVol1", 1.25)):
        o = _ob(nm)
        if o is None:
            continue
        for f, v in ((boom, 0.5), (boom + 30, s), (n, s * 1.08)):
            o.scale = (v, v, v)
            o.keyframe_insert("scale", frame=f)
    v3 = _ob("PlasmaVol3")
    if v3 is not None:                       # R10 keys (boom 0.4 / +30 1.0 / n 1.15) x 1.5, same frames (replaced)
        for f, v in ((boom, 0.6), (boom + 30, 1.5), (n, 1.72)):
            v3.scale = (v, v, v)
            v3.keyframe_insert("scale", frame=f)
    # the collector behind the plasma: satin-metal bowl face lit by the plasma (violet), hole collar dark,
    # defocused by the camera's existing DOF (focus on the plasma)
    coll = _ob("Collector")
    recv = [o for o in (coll, _ob("CollectorLip"), _ob("CollectorRim")) if o is not None]
    if coll is not None and coll.active_material is not None:
        # same mirror until the plasma lights; from the boom a darker satin layer is mixed in (keyed factor) so the
        # bowl catches the plasma light as a soft violet gradient instead of mirroring the dark chamber
        m = coll.active_material.copy()
        m.name = "CollectorR22"
        nt = m.node_tree
        out = next(nd for nd in nt.nodes if nd.type == "OUTPUT_MATERIAL" and nd.is_active_output)
        src = out.inputs["Surface"].links[0].from_socket
        sat = nt.nodes.new("ShaderNodeBsdfPrincipled")
        sat.inputs["Base Color"].default_value = (*SATIN_RGB, 1)
        sat.inputs["Metallic"].default_value = 1.0
        sat.inputs["Roughness"].default_value = SATIN_ROUGH
        mx = nt.nodes.new("ShaderNodeMixShader")
        nt.links.new(src, mx.inputs[1])
        nt.links.new(sat.outputs[0], mx.inputs[2])
        nt.links.new(mx.outputs[0], out.inputs["Surface"])
        for f, v in ((boom - 1, 0.0), (boom, SATIN_MIX)):
            mx.inputs["Fac"].default_value = v
            mx.inputs["Fac"].keyframe_insert("default_value", frame=f)
        coll.data.materials.clear()
        coll.data.materials.append(m)
    li = K.point("PlasmaCollR22", (0.0, 0.0, 0.0), 0.0, (0.78, 0.66, 1.0), 0.05)
    col = bpy.data.collections.new("PlasmaCollR22_Recv")
    for o in recv:
        col.objects.link(o)
    li.light_linking.receiver_collection = col
    for f, e in ((boom - 1, 0.0), (boom, PLASMA_COLL_E), (n, PLASMA_COLL_E * 1.1)):
        li.data.energy = e
        li.data.keyframe_insert("energy", frame=f)


PLASMA_COLL_E = 60.0
SATIN_RGB = (0.16, 0.15, 0.2)
SATIN_ROUGH = 0.22
SATIN_MIX = 0.85
