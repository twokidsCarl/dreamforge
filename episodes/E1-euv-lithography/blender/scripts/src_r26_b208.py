"""R26 srcb helper, B2_08 (R26_ROOT_CAUSE row 2, shared soft shell beam_r26).

R25 review (B2_08) #2: 「白色流线像线框鸟笼：改成半透明、软边、逐渐变细的气流带，从斑点处升起、汇向泵口」. R25 srcb attempt
(straight beam_r25 shells from the lower-right face) read as 「glass shards」 and did not start at the deposits.
R26: the R23 SnH4RibbonsR23 thin ribbons are replaced by S26_GN soft gas streams. Each stream is ONE curved tube swept
along the R23 Bezier (lifts off the deposit area of the face, arcs to the pump port), radius tapering wide -> narrow
into the port, shaded with beam_r26.shell_mat (rim roll-off: no outline line, filled core) + a soft fade-in at the face.
Not visible in the polished face (visible_glossy off). Base = R23 pixels otherwise (mirror / sheen / deposits kept).
"""
import math
import os

_E = os.environ


def _tube(name, pts, r0, r1, sides=24):
    import bpy
    import bmesh
    from mathutils import Vector
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("ConeUV")
    n = len(pts)
    rings = []
    prev_x = None
    for i, p in enumerate(pts):
        t = (pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]).normalized()
        ref = Vector((0, 0, 1)) if abs(t.z) < 0.9 else Vector((1, 0, 0))
        x = (ref - t * ref.dot(t)).normalized() if prev_x is None else (prev_x - t * prev_x.dot(t)).normalized()
        prev_x = x
        y = t.cross(x)
        u = i / (n - 1)
        r = r0 + (r1 - r0) * (u ** 0.8)
        rings.append([bm.verts.new(p + (x * math.cos(a) + y * math.sin(a)) * r)
                      for a in (2 * math.pi * k / sides for k in range(sides))])
    for i in range(n - 1):
        for k in range(sides):
            k2 = (k + 1) % sides
            f = bm.faces.new((rings[i][k], rings[i][k2], rings[i + 1][k2], rings[i + 1][k]))
            vs = (i / (n - 1), i / (n - 1), (i + 1) / (n - 1), (i + 1) / (n - 1))
            us = (k / sides, (k + 1) / sides, (k + 1) / sides, k / sides)
            for lp, uu, vv in zip(f.loops, us, vs):
                lp[uvl].uv = (uu, vv)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def _spots(name, rr, ad, F, B115):
    """a small cluster of dark matte tin-deposit dots under each stream foot (the stream rises FROM the deposit)."""
    import bpy
    import bmesh
    from mathutils import Vector, Matrix
    import kit_r2 as K
    m = bpy.data.materials.get("TinDepositDarkR23") or K.mat("TinDepositDarkR26", (0.04, 0.04, 0.045), metal=0.2,
                                                              rough=0.85)
    bm = bmesh.new()
    for j, (dr, da, rad) in enumerate(((0, 0, 0.012), (0.03, 3, 0.008), (-0.025, -4, 0.009), (0.01, -7, 0.007),
                                       (-0.01, 6, 0.0075))):
        r_ = rr + dr
        a = math.radians(ad + da)
        y, z = r_ * math.cos(a), r_ * math.sin(a)
        nrm = Vector((1, -y / (2 * F), -z / (2 * F))).normalized()
        c = Vector((B115.face_x(r_), y, z)) + nrm * 0.002
        rot = nrm.to_track_quat("Z", "Y").to_matrix().to_4x4()
        bmesh.ops.create_circle(bm, cap_ends=True, radius=rad, segments=16, matrix=Matrix.Translation(c) @ rot)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    me.materials.append(m)
    return ob


def _wisp(ob, frames):
    """gas, not a beam: 4D noise on ConeUV (U around, V along, W keyed over the shot = drift toward the port)
    modulates strength and alpha -> broken wisps that flow, instead of a uniform translucent rod."""
    if float(_E.get("S26_WISP", "1")) <= 0:
        return
    m = ob.material_slots[0].material
    N, L = m.node_tree.nodes, m.node_tree.links
    sp = next(n for n in N if n.type == "SEPXYZ")
    uvn = next(n for n in N if n.type == "UVMAP")
    em = next(n for n in N if n.type == "EMISSION")
    mx = next(n for n in N if n.type == "MIX_SHADER")
    mp = N.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (float(_E.get("S26_WU", "2.0")), float(_E.get("S26_WV", "5.0")), 1.0)
    L.new(uvn.outputs["UV"], mp.inputs["Vector"])
    nz = N.new("ShaderNodeTexNoise")
    nz.noise_dimensions = "4D"
    nz.inputs["Scale"].default_value = 1.6
    nz.inputs["Detail"].default_value = 3.0
    L.new(mp.outputs["Vector"], nz.inputs["Vector"])
    f0, f1 = frames
    nz.inputs["W"].default_value = 0.0
    nz.inputs["W"].keyframe_insert("default_value", frame=f0)
    nz.inputs["W"].default_value = float(_E.get("S26_WW", "3.0"))
    nz.inputs["W"].keyframe_insert("default_value", frame=f1)
    # loc.y moves the pattern along the stream (toward the port)
    mp.inputs["Location"].default_value = (0, 0, 0)
    mp.inputs["Location"].keyframe_insert("default_value", frame=f0)
    mp.inputs["Location"].default_value = (0, -float(_E.get("S26_WF", "4.0")), 0)
    mp.inputs["Location"].keyframe_insert("default_value", frame=f1)
    try:   # linear drift (Blender 4.4+ slotted actions have no Action.fcurves -> keep the default ease)
        for fc in m.node_tree.animation_data.action.fcurves:
            for kp in fc.keyframe_points:
                kp.interpolation = "LINEAR"
    except AttributeError:
        pass
    mr = N.new("ShaderNodeMapRange")
    L.new(nz.outputs["Fac"], mr.inputs["Value"])
    mr.inputs["From Min"].default_value = 0.38
    mr.inputs["From Max"].default_value = 0.68
    mr.inputs["To Min"].default_value = float(_E.get("S26_WMIN", "0.15"))
    mr.inputs["To Max"].default_value = 1.25
    for sock in (em.inputs["Strength"], mx.inputs["Fac"]):
        src = sock.links[0].from_socket
        mul = N.new("ShaderNodeMath")
        mul.operation = "MULTIPLY"
        L.new(src, mul.inputs[0])
        L.new(mr.outputs["Result"], mul.inputs[1])
        L.new(mul.outputs[0], sock)


def build(sc, S):
    import bpy
    from mathutils import Vector
    import b115_r17 as B115
    import beam_r26 as BM
    import misc_beam_r18 as MB
    import src_r25 as R25
    F = B115.B_F
    for ob in list(bpy.data.objects):
        if ob.name.startswith("SnH4RibbonsR23") or ob.name == "SnH4Lines" or ob.name.startswith("SnH4_"):
            bpy.data.objects.remove(ob, do_unlink=True)
    a_p, z_p = math.radians(124), 0.5
    nrm_p = Vector((-math.cos(a_p), -math.sin(a_p), 0))
    port = Vector((math.cos(a_p), math.sin(a_p), 0)) * (S.CHAMBER_R - 0.02) + Vector((0, 0, z_p))
    col = tuple(float(v) for v in _E.get("S26_GCOL", "0.72,0.9,1.0").split(","))
    r0, r1 = float(_E.get("S26_GR0", "0.06")), float(_E.get("S26_GR1", "0.01"))
    obs = []
    # sources = separate deposit spots right / below the label cluster whose stream chord stays >= 48 deg to the LOS on
    # f60..f206 (GDIAG26 grid); widely separated so the streams do not merge into one striped fin
    src = [tuple(float(v) for v in t.split(":")) for t in
           _E.get("S26_GSRC", "0.42:18,0.30:2,0.46:-24,0.26:-46").split(",")]
    gn = len(src)
    for i, (rr, ad) in enumerate(src):
        s = i / max(gn - 1, 1)
        a = math.radians(ad)
        y, z = rr * math.cos(a), rr * math.sin(a)
        nrm = Vector((1, -y / (2 * F), -z / (2 * F))).normalized()
        p0 = Vector((B115.face_x(rr), y, z)) + nrm * float(_E.get("S26_GLIFT", "0.03"))
        p1 = p0 + nrm * float(_E.get("S26_GN1", "0.08"))
        p3 = port + nrm_p * 0.06 + Vector((0, 0, (0.5 - s) * float(_E.get("S26_GPS", "0.1"))))
        p2 = p1.lerp(p3, 0.5) + Vector((float(_E.get("S26_BX", "0.3")), 0, float(_E.get("S26_BZ", "0.22"))))
        pts = [(1 - u) ** 3 * p0 + 3 * (1 - u) ** 2 * u * p1 + 3 * (1 - u) * u * u * p2 + u ** 3 * p3
               for u in (k / 48 for k in range(49))]
        ob = _tube(f"SnH4FlowR26_{i}", pts, r0, r1)
        ob.data.materials.append(BM.shell_mat(ob.name + "M", col, float(_E.get("S26_GS", "1.0")),
                                              alpha=float(_E.get("S26_GA", _E.get("S26_GAD", "0.25"))),
                                              gain=float(_E.get("S26_GG", "1.2")), narrow_at_end=True))
        MB._vis(ob)
        ob.visible_glossy = False
        ob["r25_radii"] = (r0, r1)
        ob["r26_profile"] = (BM.EDGE, BM.CORE, float(_E.get("S26_GA", _E.get("S26_GAD", "0.25"))), BM.RIM_POW)
        R25.fade_start(ob, float(_E.get("S26_GF", "0.15")))
        _wisp(ob, (1, sc.frame_end))
        obs.append((ob, pts))
        _spots(f"SnH4SrcSpotsR26_{i}", rr, ad, F, B115)
    if _E.get("S26_GDIAG") == "1":
        from bpy_extras.object_utils import world_to_camera_view as w2c0
        for rr in (0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55):
            for ad in range(-90, 120, 15):
                a = math.radians(ad)
                y, z = rr * math.cos(a), rr * math.sin(a)
                nrm = Vector((1, -y / (2 * F), -z / (2 * F))).normalized()
                q0 = Vector((B115.face_x(rr), y, z)) + nrm * 0.03
                q1 = port + nrm_p * 0.06
                out = []
                for f in (60, 206):
                    sc.frame_set(f)
                    cl = sc.camera.matrix_world.translation
                    ang = math.degrees(math.acos(abs((q1 - q0).normalized().dot(((q0 + q1) * 0.5 - cl).normalized()))))
                    v0 = w2c0(sc, sc.camera, q0)
                    out.append(f"f{f} {ang:.0f}deg ({v0.x*960:.0f},{(1-v0.y)*540:.0f})")
                print(f"GDIAG26 rr {rr} a {ad} " + " | ".join(out), flush=True)
    # checks: stream chord as a one-leg chain (ends in frame, taper, width, camera) + BEAMCHECK26 profile
    from bpy_extras.object_utils import world_to_camera_view as w2c
    for i, (ob, pts) in enumerate(obs):
        ch = {"legs": [[ob]], "spots": [], "stops": [(pts[0], None), (pts[-1], None)], "radii": [r0, r1]}
        BM.check(sc, ch, (60, 133, 206), tag=f"B2_08g{i}")
        for f in (60, 206):
            sc.frame_set(f)
            cl = sc.camera.matrix_world.translation
            mn = min(math.degrees(math.acos(min(1.0, abs((pts[k + 1] - pts[k]).normalized().dot(
                (pts[k] - cl).normalized()))))) for k in range(len(pts) - 1))
            v0, v1 = w2c(sc, sc.camera, pts[0]), w2c(sc, sc.camera, pts[-1])
            print(f"B208PROJ26 g{i} f{f} start ({v0.x*960:.0f},{(1-v0.y)*540:.0f}) port ({v1.x*960:.0f},"
                  f"{(1-v1.y)*540:.0f}) min local axis/los {mn:.0f}deg", flush=True)
    sc.frame_set(1)
