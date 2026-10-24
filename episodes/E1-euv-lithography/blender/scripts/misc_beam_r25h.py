"""Round 25 hook (owned by the 'mbeam' sub-agent; shots in r2_misc.R25_BEAM = A2_03 / B8_17 / B4_07).

R25_ROOT_CAUSE rows:
- row 2 (taper, all three): pre() swaps beam_r24.chain / soft_cone / check for the beam_r25 versions, so the R24 hook
  (misc_beam_r24h) builds TAPERED SHELL legs (>= 3:1, no inner cone) and runs BEAMCHECK + BEAMCHECK25. The swap is undone
  in post() (nothing else ever sees the patched module).
- row 1 (turn mirrors): every interior stop is passed an EXISTING scene mirror (existing={1: obj}):
  A2_03: the PO5 turn sat edge-on / seen from behind (|n.to_cam| 0.13-0.28) -> PO5 is staggered 0.8 m in DEPTH (away
  from the camera) in pre() via build_cutaway_r2.PO[5] (the backdrop ring mount, solid blank, NA cone, theta arc and
  anchors all follow) so its coated face opens toward the camera; PO5's aperture grows so the landing is ~1/3 of it.
  B4_07: the V's turn IS the coating (MirrorCap). B8_17: one leg, no turn.
- row 4 (machine density, A2_03 / B8_17): misc_beam_r25h_dense.py adds 3 depth layers of real parts (no texture wall,
  no fog).
Remove a shot from r2_misc.R25_BEAM -> exact R24 pixels.
"""
import math

import bpy
from mathutils import Vector

_ORIG = {}
_STATE = {"shot": None}
A203_PO5_DY = 0.8          # depth stagger of the PO5 turn (m, away from the camera)
A203_PO5_R = 0.25          # PO5 ring radius (R24 0.21) -> mirror blank r 0.31
A203_R5 = 0.10             # beam radius at the PO5 landing (~1/3 of the blank)
B407_HIT = Vector((-0.2, -0.7, 0.006))  # R24 (0.15, 0.25) sat at the wedge apex -> intact coating, 0.64 m (> 1/4 diameter) from the cut
B407_RISE = (0.7, 0.3, 79)             # camera rise (m) peaking at f79, target rises by the 2nd factor x rise
B407_FADE = (96, 110)                  # the V fades out on the dive to the cut edge (was: keyed off once off screen)


def _smooth(u):
    u = max(0.0, min(1.0, u))
    return u * u * (3 - 2 * u)


def _b407_camera(sc):
    """Row 1 (B4_07): at f79 the push-in camera looked at the coating from 21 deg elevation (|n.to_cam| 0.36 = the
    turn mirror 'edge-on' by the R25 rule). The descent is re-keyed with a rise bell (0 at f1, +0.7 m at f79, 0 again at
    the end frame of the push): same D push-in to the cut edge, the coating seen >= 30 deg out of edge-on."""
    cam = sc.camera
    tgt = next((c.target for c in cam.constraints if c.type == "TRACK_TO" and c.target), None)
    A, kt, fp = B407_RISE
    n = sc.frame_end
    rec = []
    for f in range(1, n + 1):
        sc.frame_set(f)
        rec.append((f, cam.location.copy(), tgt.location.copy() if tgt else None))
    for ob in (cam, tgt):
        if ob is not None and ob.animation_data:
            ob.animation_data_clear()
    for f, cl, tl in rec:
        dz = A * (_smooth((f - 1) / (fp - 1)) if f <= fp else 1.0 - _smooth((f - fp) / (n - fp)))
        cam.location = cl + Vector((0, 0, dz))
        cam.keyframe_insert("location", frame=f)
        if tgt is not None:
            tgt.location = tl + Vector((0, 0, dz * kt))
            tgt.keyframe_insert("location", frame=f)
    for ob in (cam, tgt):
        if ob is not None and ob.animation_data and ob.animation_data.action:
            import common as C
            for fc in C.fcurves(ob.animation_data.action):
                for k in fc.keyframe_points:
                    k.interpolation = "LINEAR"
    print(f"[R25 B4_07] camera re-keyed with a {A} m rise bell peaking at f{fp} (target x{kt})", flush=True)


def _chk(sc, ch, frames, exits=(), tag="", cam=None, **kw):
    import beam_r24 as B24
    import beam_r25 as B25
    if tag == "B4_07":
        off = [f for f in frames if f >= B407_FADE[1]]
        frames = [f for f in frames if f < B407_FADE[1]]
        if off:
            print(f"BEAMCHECK B4_07 frames {off}: path faded out (f{B407_FADE[0]}-{B407_FADE[1]}, light off on the "
                  f"dive to the cut edge)", flush=True)
    B24.check = _ORIG["check"]
    try:
        return B25.check(sc, ch, frames, exits=exits, tag=tag, cam=cam)
    finally:
        B24.check = _chk


def _chain(name, stops, radii, **kw):
    import beam_r25 as B25
    shot = _STATE["shot"]
    xdir = kw.pop("xdir", None)
    existing = {}
    if name == "A203R24":
        existing = {1: bpy.data.objects["MirrorR19_5"]}
        radii = [A203_R5 / 3.0, A203_R5, 0.006]
        kw.update(strength=4.0, alpha=0.6, edge=2.4, core=0.08, gain=1.2)
    elif name == "B407R24":
        sc = bpy.context.scene
        _b407_camera(sc)
        d = B407_HIT - Vector(stops[1][0])
        stops = [(Vector(p) + d, nr) for p, nr in stops]
        existing = {1: bpy.data.objects["MirrorCap"]}
        kw.update(spot_scale=3.5, spot_strength=40.0, strength=4.0, alpha=0.6, edge=2.0, core=0.15, gain=1.6)
    elif name == "B817R24":
        kw.update(strength=3.0, alpha=0.5, edge=1.4, core=0.35, gain=1.6)
    for k in ("inner", "inner_gain", "fade0", "fade1"):
        kw.pop(k, None)
    ch = B25.chain(name, stops, radii, existing=existing, **kw)
    if xdir is not None:               # keep the slit-shaped (elliptic) section oriented along the slit
        for i, leg in enumerate(ch["legs"]):
            for ob in leg:
                bpy.data.objects.remove(ob, do_unlink=True)
            a, b = Vector(stops[i][0]), Vector(stops[i + 1][0])
            ra, rb = B25.tapered(radii[i], radii[i + 1])
            ch["legs"][i] = B25.soft_cone(f"{name}Leg{i}", a, b, ra, rb, kw.get("color"), kw.get("strength", 4.0),
                                          kw.get("alpha", 0.6), kw.get("edge", 2.4), kw.get("core", 0.08),
                                          kw.get("gain", 1.2), xdir=xdir)
    import misc_beam_r25h_shell as SH
    SH.remat(ch, kw.get("color"), kw.get("strength", 4.0), kw.get("alpha", 0.6), kw.get("edge", 2.4),
             kw.get("core", 0.08), kw.get("gain", 1.2))
    _STATE["ch_" + name] = ch
    print(f"[R25 mbeam] {shot} chain {name}: leg radii {ch['leg_radii']} mirrors {list(ch['mirrors'])}", flush=True)
    return ch


def pre(variant, shot, mod):
    import beam_r24 as B24
    import beam_r25 as B25
    _STATE["shot"] = shot
    if not _ORIG:
        _ORIG.update(chain=B24.chain, soft_cone=B24.soft_cone, check=B24.check)
    B24.chain, B24.soft_cone, B24.check = _chain, B25.soft_cone, _chk
    if shot == "A2_03":
        import build_cutaway_r2 as B
        _ORIG["po5"] = Vector(B.PO[5])
        _ORIG["po_r5"] = B.PO_R[5]
        B.PO[5] = Vector(B.PO[5]) + Vector((0.0, A203_PO5_DY, 0.0))
        B.PO_R[5] = A203_PO5_R


def _restore():
    import beam_r24 as B24
    if _ORIG:
        B24.chain, B24.soft_cone, B24.check = _ORIG["chain"], _ORIG["soft_cone"], _ORIG["check"]
    if "po5" in _ORIG:
        import build_cutaway_r2 as B
        B.PO[5] = _ORIG.pop("po5")
        B.PO_R[5] = _ORIG.pop("po_r5")


def _a203_post(sc):
    """PO5 face now opens toward the camera: drop the R24 lip glint; NA theta arc rebuilt to the new cone rim."""
    import build_cutaway_r2 as B
    import kit_r2 as K
    n = sc.frame_end
    for nm in ("A203R24LipGlint", "NATheta"):
        ob = bpy.data.objects.get(nm)
        if ob is not None:
            bpy.data.objects.remove(ob, do_unlink=True)
    po5, wf = Vector(B.PO[5]), Vector((B.WAFER.x, 0.0, 1.065))
    u = (po5 - wf).normalized()
    perp = u.cross(Vector((0, 1, 0))).normalized()
    rim = A203_R5
    L = (po5 - wf).length
    e = ((po5 + perp * rim) - wf).normalized()
    th = math.acos(max(-1.0, min(1.0, u.dot(e))))
    amb = K.MB()
    ar = 0.3
    arc = [wf + (u * math.cos(th * k / 16) + perp * math.sin(th * k / 16)) * ar for k in range(17)]
    for a_, b_ in zip(arc, arc[1:]):
        amb.tube(a_, b_, 0.006, seg=8)
    for k in range(4):
        amb.tube(wf + u * L * (0.04 + k * 0.08), wf + u * L * (0.08 + k * 0.08), 0.003, seg=6)
    amb.tube(wf, wf + e * L * 0.35, 0.003, seg=6)
    na = amb.obj("NATheta", K.emit_mat("NAThetaInk25", K.CYAN, 3.5))
    f_on = round(n * 0.48)
    na.hide_render = True
    na.keyframe_insert("hide_render", frame=1)
    na.keyframe_insert("hide_render", frame=f_on - 1)
    na.hide_render = False
    na.keyframe_insert("hide_render", frame=f_on)
    K.anchors("A2_03", {"beam": B.PO[4].lerp(po5, 0.5), "mirror": po5, "wafer": B.WAFER, "mask": B.MASK,
                        "theta": arc[8] + perp * 0.03, "na_apex": wf})
    print(f"[R25 A2_03] PO5 at {tuple(round(x, 3) for x in po5)} (depth +{A203_PO5_DY} m), theta {math.degrees(th):.1f} "
          f"deg", flush=True)


def _b407_post(sc):
    import misc_beam_r25h_shell as SH
    ch = _STATE.get("ch_B407R24")
    if ch is None:
        return
    legs = [o for leg in ch["legs"] for o in leg]
    f0, f1 = B407_FADE
    SH.fade(legs, [(f0, 1.0), (f1, 0.0)])
    for s_ in ch["spots"]:
        if s_ is None:
            continue
        sc_ = s_.scale.copy()
        s_.keyframe_insert("scale", frame=f0)
        s_.scale = (0.0, 0.0, 0.0)
        s_.keyframe_insert("scale", frame=f1)
        s_.scale = sc_
    for o in legs + [s_ for s_ in ch["spots"] if s_ is not None]:
        o.hide_render = True
        o.keyframe_insert("hide_render", frame=f1 + 1)
        o.hide_render = False
        o.keyframe_insert("hide_render", frame=f1)
    print(f"[R25 B4_07] V fades out f{f0}-{f1}, hidden from f{f1 + 1}", flush=True)


def post(sc, variant, shot):
    try:
        if shot == "A2_03":
            _a203_post(sc)
        if shot == "B4_07":
            _b407_post(sc)
        try:
            import misc_beam_r25h_dense as D
            D.apply(sc, shot)
        except ImportError:
            pass
    finally:
        _restore()
    return sc
