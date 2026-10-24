"""Round 31 (P1, R31_ROOT_CAUSE rows 3a / 3d / 6e - SCREEN-space taper; MAIN process, agents never edit it).

R30 review: B5_01 「IF 出射本该是发散锥，现在是等宽光柱」 although beam_r30 gave the leg a 4.5:1 world taper - the IF end is
near the camera and the FFM end far away, so perspective cancels the taper on screen (R30 scan: 27 px vs 31 px).
C_03 f343 「入射/反射在掩模下方像两根交叉的光柱」; A2_03 「从右镜到顶镜那段入射光是等宽实心光柱」.
beam_r31 keeps beam_r30 (TAPER + FLOOR, same wrapper of beam_r29.cone, beam_hook_r29 still the only converter and still
LAST) and adds one stage for the legs named in a shot's spec with "screen": "a" | "b":
  SCREEN: on the shot's mid job frame the focus end's ON-SCREEN width is made <= the wide end's on-screen width /
      SCREEN_RATIO (but >= END_PX), so the cone really opens / closes on screen.
No shell parameter, no fade.
"""
from mathutils import Vector

SCREEN_RATIO = 4.5
END_PX = 3.0
LOG = []


def _screen(shot, end, a, b, ra, rb, parent, frames, px=None):
    import bpy
    import beam_r30 as B30
    sc = bpy.context.scene
    cam = sc.camera
    if cam is None or not frames:
        return ra, rb, None
    keep = sc.frame_current
    order = [frames[len(frames) // 2]] + [f for f in frames if f != frames[len(frames) // 2]]
    pa = pb = None
    for f in order:                      # mid job frame first; else the first job frame where both ends are on screen
        sc.frame_set(f)
        M = parent.matrix_world if parent is not None else None
        s = M.to_scale().x if M is not None else 1.0
        wa = (M @ Vector(a)) if M is not None else Vector(a)
        wb = (M @ Vector(b)) if M is not None else Vector(b)
        d = (wb - wa).normalized()
        pa = B30._px_width(sc, cam, wa, max(ra) * s, d)
        pb = B30._px_width(sc, cam, wb, max(rb) * s, d)
        if (pa and pb) or (px is not None and (pa if end == "a" else pb)):
            break
    sc.frame_set(keep)
    if px is not None:                   # focus end given as an on-screen width (the wide end is off screen)
        w = pa if end == "a" else pb
        if not w:
            return ra, rb, (pa, pb)
        k = min(1.0, px / w)
        if end == "a":
            ra = tuple(x * k for x in ra)
        else:
            rb = tuple(x * k for x in rb)
        return ra, rb, (pa, pb, round(k, 3))
    if not pa or not pb:
        return ra, rb, (pa, pb)
    if end == "a":
        tgt = max(END_PX, pb / SCREEN_RATIO)
        k = min(1.0, tgt / pa)
        ra = tuple(x * k for x in ra)
    else:
        tgt = max(END_PX, pa / SCREEN_RATIO)
        k = min(1.0, tgt / pb)
        rb = tuple(x * k for x in rb)
    return ra, rb, (round(pa, 1), round(pb, 1), round(k, 3))


def install(shot, focus, gain=None):
    """wrap beam_r29.cone for this build (replaces a beam_r30.install wrapper; same TAPER + FLOOR + the SCREEN stage)."""
    import beam_r29 as B29
    import beam_r30 as B30
    orig = getattr(B29.cone, "_r30_orig", B29.cone)
    frames = B30._jobs(shot)

    def cone(name, a, b, ra, rb, color=None, strength=B29.B_DEFAULT, xdir=None, parent=None):
        ra = (ra, ra) if isinstance(ra, (int, float)) else tuple(ra)
        rb = (rb, rb) if isinstance(rb, (int, float)) else tuple(rb)
        leg = name[:-3] if name.endswith("V29") else name
        r0 = (ra, rb)
        spec = next((v for k, v in focus.items() if leg.startswith(k)), None)
        if spec:
            ra, rb = B30._taper(spec, ra, rb)
        ra, rb, info = B30._floor(name, a, b, ra, rb, parent, frames)
        sinfo = None
        if spec and spec.get("screen") in ("a", "b"):
            ra, rb, sinfo = _screen(shot, spec["screen"], a, b, ra, rb, parent, frames, spec.get("px"))
        g = next((v for k, v in (gain or {}).items() if leg.startswith(k)), 1.0)
        msg = (f"[beam_r31] {shot} {leg} r {tuple(round(x, 3) for x in r0[0])}->{tuple(round(x, 3) for x in r0[1])}"
               f" => {tuple(round(x, 3) for x in ra)}->{tuple(round(x, 3) for x in rb)} focus {spec} gain {g}"
               f" floor {None if info is None else tuple(None if x is None else round(x, 2) for x in info)} screen {sinfo}")
        print(msg, flush=True)
        LOG.append(msg)
        if spec and spec.get("slit_dir") is not None:
            xd = Vector(spec["slit_dir"])
            if parent is not None:
                xd = parent.matrix_world.to_3x3().inverted() @ xd
            xdir = xd
        ob = orig(name, a, b, ra, rb, color, strength * g, xdir=xdir, parent=parent)
        if spec and spec.get("slit") in ("a", "b"):
            B30._slit_line(ob, ra if spec["slit"] == "a" else rb, spec["slit"] == "b", color, spec.get("face", (0, 0, 1)))
        return ob
    cone._r30_orig = orig
    B29.cone = cone
