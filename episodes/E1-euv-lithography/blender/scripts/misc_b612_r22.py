"""Round 22 (P1) hook for B6_12 (R22_ROOT_CAUSE row 6, material). Owned by the misc sub-agent.

R21 review B6_12 #1 「宏观里 pellicle 几乎看不见，只有一块亮斑。按 k5A 加掠射高光带、膜框黑边，以及一点微透的灰雾，让膜在 25 % 帧就能
被认出来」. Layered on the R20 + R21 build (scanner pose, cut-section magnifier, black anodised frame all kept; nothing deleted):
- grazing highlight band: a long thin emissive strip that is visible ONLY to glossy rays, placed (and keyed through the
  camera move) in the mirror direction of the camera about the membrane plane, aimed at a line across the membrane, its
  long axis in the membrane plane -> one soft band crosses the stretched film in every frame.
- faint translucent grey haze in the membrane material (a little grey diffuse + translucent mixed over the Fresnel sheen),
  so the film reads as a thin sheet over the pattern, not as nothing.
"""
import bpy
from mathutils import Vector

HAZE = 0.0          # share of grey haze in the membrane shader
BAND_U = 0.38        # where across the film the band crosses (0..1 along the film's long axis from the camera side)


def pre(variant, shot, mod):
    pass


def _haze(mem):
    nt = mem.node_tree
    out = next(x for x in nt.nodes if x.type == "OUTPUT_MATERIAL" and x.is_active_output)
    lk = out.inputs["Surface"].links[0]
    src = lk.from_socket
    dif = nt.nodes.new("ShaderNodeBsdfDiffuse")
    dif.inputs["Color"].default_value = (0.22, 0.225, 0.235, 1)
    trl = nt.nodes.new("ShaderNodeBsdfTranslucent")
    trl.inputs["Color"].default_value = (0.15, 0.155, 0.16, 1)
    hz = nt.nodes.new("ShaderNodeMixShader")
    hz.inputs["Fac"].default_value = 0.5
    nt.links.new(dif.outputs[0], hz.inputs[1])
    nt.links.new(trl.outputs[0], hz.inputs[2])
    mx = nt.nodes.new("ShaderNodeMixShader")
    mx.inputs["Fac"].default_value = HAZE
    nt.links.new(src, mx.inputs[1])
    nt.links.new(hz.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs["Surface"])


def post(sc, variant, shot):
    import kit_r2 as K
    mo = bpy.data.objects.get("Membrane")
    if mo is None:
        print("[R22 B6_12] no Membrane - skipped")
        return
    mem = mo.data.materials[0]
    _haze(mem)
    cam = sc.camera
    n = sc.frame_end
    # membrane frame: centre, normal, long axis (world)
    sc.frame_set(1)
    mw = mo.matrix_world.copy()
    vs = [mw @ v.co for v in mo.data.vertices]
    ctr = sum(vs, Vector()) / len(vs)
    nrm = (mw.to_3x3() @ Vector((0, 0, 1))).normalized()
    ax = (mw.to_3x3() @ Vector((1, 0, 0))).normalized()
    ay = nrm.cross(ax).normalized()
    ext_x = max(abs((v - ctr).dot(ax)) for v in vs)
    ext_y = max(abs((v - ctr).dot(ay)) for v in vs)
    # strip emitter (mesh plane), glossy-only
    w, L = 0.03, 4.0
    me = bpy.data.meshes.new("PelBandR22")
    me.from_pydata([(-L / 2, -w / 2, 0), (L / 2, -w / 2, 0), (L / 2, w / 2, 0), (-L / 2, w / 2, 0)], [], [(0, 1, 2, 3)])
    ob = bpy.data.objects.new("PelBandR22", me)
    sc.collection.objects.link(ob)
    em = K.emit_mat("PelBandR22M", (0.92, 0.95, 1.0), 150.0)
    me.materials.append(em)
    for attr in ("visible_camera", "visible_diffuse", "visible_transmission", "visible_volume_scatter", "visible_shadow"):
        setattr(ob, attr, False)
    ob.visible_glossy = True
    import os
    if os.environ.get("B612DBG"):
        ob.visible_camera = True
    step = max(1, n // 24)
    for f in list(range(1, n + 1, step)) + [n]:
        sc.frame_set(f)
        C = cam.matrix_world.translation.copy()
        # band line across the film: choose the axis more perpendicular to the view direction's in-plane part
        vd = (ctr - C)
        vp = vd - vd.dot(nrm) * nrm
        along = ax if abs(vp.normalized().dot(ax)) > abs(vp.normalized().dot(ay)) else ay
        ext = ext_x if along is ax else ext_y
        s = 1.0 if vp.dot(along) > 0 else -1.0
        X = ctr + along * s * ext * (2 * BAND_U - 1)
        d = (X - C).normalized()
        r = d - 2 * d.dot(nrm) * nrm                  # reflected view ray
        E = X + r * 1.6
        ob.location = E
        long_ax = nrm.cross(along).normalized()       # in-plane, perpendicular to plane of incidence
        z = (-r).normalized()                          # plane faces back toward the membrane
        x = (long_ax - long_ax.dot(z) * z).normalized()
        y = z.cross(x)
        from mathutils import Matrix
        rot = Matrix((x, y, z)).transposed().to_euler()
        ob.rotation_euler = rot
        ob.keyframe_insert("location", frame=f)
        ob.keyframe_insert("rotation_euler", frame=f)
    sc.frame_set(1)
    print(f"[R22 B6_12] haze {HAZE}, glossy-only band keyed every {step} frames; membrane normal {tuple(round(c, 2) for c in nrm)}")
