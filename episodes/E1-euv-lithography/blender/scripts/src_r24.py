"""Round 24 hook (owned by the 'srcb' sub-agent; shots in r2_source.R24_SRC). Remove a shot from R24_SRC -> R23 pixels.

R24_ROOT_CAUSE row 3 (beam unification via beam_r24) + row 6 (B1_15 camera motion).
  * B1_15 (row 3): the R22 volume IFConeR22 (r 0.59 mouth, screen -104..993 px = >100 % frame, camera ~1.2 m from its
    surface -> 「实心光柱 / 花瓶」) is deleted. The exit light is ONE beam_r24.chain leg on the optical axis from a point
    S24_K (>= 40 %) of the way rim -> IF to the off-frame IF (x 1.20), soft surface cone (bright skin, darker core),
    fading in at its start; a small "IF" anchor (screen point of the IF) is merged into the shot's anchors json for the
    zz24s overlay. beam_r24.check on 9 / 20 / 31 (exits=(1,)).
  * B1_15 (row 6): stronger push (D 2.3 -> 1.95 becomes S24_D0 -> S24_D1, linear) + focus pull plasma -> mirror face.
  * B2_08 (row 3): the R23 constant-ish tubes (SnH4RibbonsR23*) -> tapered soft white-blue cones (beam_r24.soft_cone
    recipe) along the same Bezier paths, fading in off the face, converging into the pump port, no end dots.
"""
import math
import os

_E = os.environ
_MOD = [None]


def pre(variant, shot, mod):
    _MOD[0] = mod
    if shot == "B1_15":
        import b115_r22_build as BB
        BB.D0 = float(_E.get("S24_D0", "2.45"))
        BB.D1 = float(_E.get("S24_D1", "1.95"))
        from mathutils import Vector
        BB.LOOK0 = Vector((float(_E.get("S24_L0", "0.16")), 0, 0))
        BB.LOOK1 = Vector((float(_E.get("S24_L1", "0.20")), 0, 0))


def post(sc, variant, shot):
    if shot == "B1_15" and variant == "contrast":
        _b115(sc)
    elif shot == "B2_08" and variant == "clean":
        _b208(sc)


def _anchor_merge(shot, pts):
    """Append a frame handler that merges extra named points into the shot's anchors json (runs after kit_r2's)."""
    import json
    import bpy
    import common as C
    from bpy_extras.object_utils import world_to_camera_view as w2c
    out = os.path.join(C.render_root(), "shots", shot, "anchors")

    def h(sc, *_):
        if sc.camera is None:
            return
        fn = os.path.join(out, f"{sc.frame_current:04d}.json")
        try:
            with open(fn) as fh:
                res = json.load(fh)
        except Exception:
            res = {}
        for k, p in pts.items():
            v = w2c(sc, sc.camera, p)
            res[k] = [round(v.x, 4), round(1 - v.y, 4), round(v.z, 3)]
        os.makedirs(out, exist_ok=True)
        with open(fn, "w") as fh:
            json.dump(res, fh)
    bpy.app.handlers.frame_change_post.append(h)


def _fcurves(ob):
    ad = ob.animation_data
    if not ad or not ad.action:
        return []
    act = ad.action
    if hasattr(act, "fcurves"):
        return list(act.fcurves)
    out = []
    for ly in act.layers:
        for st in ly.strips:
            for cb in st.channelbags:
                out += list(cb.fcurves)
    return out


def _b115(sc):
    import bpy
    from mathutils import Vector
    import kit_r2 as K
    import b115_r21 as B
    import b115_r22_build as BB
    import beam_r24 as BM
    from bpy_extras.object_utils import world_to_camera_view as w2c
    n = sc.frame_end
    cam = sc.camera
    for ob in list(bpy.data.objects):
        if ob.name.startswith("IFConeR22"):
            bpy.data.objects.remove(ob, do_unlink=True)
    xr, xi = B.fx(B.R), BB.image_x()
    k = float(_E.get("S24_K", "0.40"))
    xa = xr + k * (xi - xr)
    ra = B.R * (xi - xa) / (xi - xr)
    ch = BM.chain("B115ExitR24", [((xa, 0, 0), None), ((xi, 0, 0), None)], [ra, 0.015], color=K.VIOLET,
                  strength=float(_E.get("S24_CS", "6.0")), alpha=float(_E.get("S24_CA", "0.45")),
                  edge=float(_E.get("S24_EDGE", "5.0")), inner=float(_E.get("S24_IN", "0.0")),
                  land_final=False, inner_gain=float(_E.get("S24_IG", "0.9")), fade0=float(_E.get("S24_F0", "0.18")))
    _anchor_merge("B1_15", {"if": Vector((xi, 0, 0)), "cone_mid": Vector(((xa + xi) * 0.5, 0, 0))})
    # row 6: linear push (visible over 9..31) + focus pull plasma -> mirror face
    for fc in _fcurves(cam):
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR"
    foc = cam.data.dof.focus_object
    rr, aa = 0.42, math.radians(float(_E.get("S24_FA", "-60")))
    face_pt = Vector((B.fx(rr), rr * math.cos(aa), rr * math.sin(aa)))
    cam.data.dof.aperture_fstop = float(_E.get("S24_FS", "4.0"))
    if foc is not None:
        if foc.animation_data:
            foc.animation_data_clear()
        for f, p in ((1, B.PC), (int(n * 0.3), B.PC), (int(n * 0.85), face_pt), (n, face_pt)):
            foc.location = p
            foc.keyframe_insert("location", frame=f)
    # 「腔内左侧的大块紫色弧面」= chamber wall lit violet by PlasmaLight, seen in the polished face -> neutral light
    li = bpy.data.objects.get("PlasmaLight")
    if li is not None and _E.get("S24_PLN", "1") == "1":
        li.data.color = (0.93, 0.92, 1.0)
    BM.check(sc, ch, (9, 20, 31), exits=(1,), tag="B1_15")
    # motion measurement: rim ellipse screen area + plasma screen point, f9 vs f31
    W, H = sc.render.resolution_x, sc.render.resolution_y
    for f in (9, 20, 31):
        sc.frame_set(f)
        pts = []
        for i in range(72):
            a = 2 * math.pi * i / 72
            v = w2c(sc, cam, Vector((xr, B.R * math.cos(a), B.R * math.sin(a))))
            pts.append((v.x * W, (1 - v.y) * H))
        ar = 0.5 * abs(sum(pts[i][0] * pts[i - 1][1] - pts[i - 1][0] * pts[i][1] for i in range(72)))
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        cl = cam.matrix_world.translation
        print(f"MOTION B1_15 f{f} rim area {ar:.0f}px2 ({ar / (W * H):.1%}) bbox x {min(xs):.0f}..{max(xs):.0f} "
              f"y {min(ys):.0f}..{max(ys):.0f} cam ({cl.x:.2f},{cl.y:.2f},{cl.z:.2f}) focus "
              f"{(foc.matrix_world.translation - cl).length if foc else 0:.2f}", flush=True)
    sc.frame_set(1)
    for ob in bpy.data.objects:
        if ob.type == "MESH":
            ms = [s.material.name for s in ob.material_slots if s.material]
            if any(("iol" in m or "VIOL" in m.upper() or "Purple" in m) for m in ms):
                print("VIOLETMAT", ob.name, ms, flush=True)


def _b208(sc):
    import bpy
    from mathutils import Vector
    import kit_r2 as K
    import b115_r17 as B115
    import beam_r24 as BM
    S = _MOD[0]
    F = B115.B_F
    rm = [ob for ob in bpy.data.objects if ob.name.startswith("SnH4RibbonsR23") or ob.name.startswith("SnH4")]
    for ob in rm:
        bpy.data.objects.remove(ob, do_unlink=True)
    a_p, z_p = math.radians(124), 0.5
    nrm_p = Vector((-math.cos(a_p), -math.sin(a_p), 0))
    port = Vector((math.cos(a_p), math.sin(a_p), 0)) * (S.CHAMBER_R - 0.02) + Vector((0, 0, z_p))
    col = (0.85, 0.92, 1.0)
    st = float(_E.get("S24_GS", "2.2"))
    al = float(_E.get("S24_GA", "0.32"))
    nseg = int(_E.get("S24_GN", "10"))
    for i in range(9):
        rr = 0.22 + 0.03 * i
        a = math.radians(55 + 7 * i)
        y, z = rr * math.cos(a), rr * math.sin(a)
        nrm = Vector((1, -y / (2 * F), -z / (2 * F))).normalized()
        p0 = Vector((B115.face_x(rr), y, z)) + nrm * 0.004
        p1 = p0 + nrm * 0.18
        p3 = port + nrm_p * 0.06 + Vector((0, 0, (i - 4) * 0.012))   # converge harder into the port
        p2 = p1.lerp(p3, 0.5) + Vector((0.12, 0, 0.18))

        def bz(u):
            return (1 - u) ** 3 * p0 + 3 * (1 - u) ** 2 * u * p1 + 3 * (1 - u) * u * u * p2 + u ** 3 * p3
        r0, r1 = float(_E.get("S24_GR0", "0.004")), float(_E.get("S24_GR1", "0.024"))
        for s in range(nseg):
            u0, u1 = s / nseg, (s + 1) / nseg
            ra = r0 + (r1 - r0) * u0
            rb = r0 + (r1 - r0) * u1
            # fade in over the first segments off the face; brightest near the pump; last segment tapers into port
            g = min(1.0, 0.15 + 1.1 * u0) * (0.75 if s == nseg - 1 else 1.0)   # fade in off the face
            if s == nseg - 1:
                rb = ra * 0.55
            BM.soft_cone(f"SnH4FlowR24_{i}_{s}", bz(u0), bz(u1), ra, rb, color=col, strength=st * g,
                         alpha=al * g, edge=float(_E.get("S24_GE", "0.8")), inner=0.0, gain=0.4, seg=16)
