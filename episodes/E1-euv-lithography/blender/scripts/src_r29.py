"""Round 29 hook for B1_15 (MAIN PROCESS; shot in r2_source.R29_SRC). Layered AFTER b115_r28 (mouth-side camera, env
strip) and BEFORE beam_hook_r29 (which turns the src_r27 mouth -> IF -> exit legs into beam_r29 volumes). One switch per
R29_ROOT_CAUSE row-5 item:

  CAM_R29     (row 5, D) R28 p1 「三帧之间只有很小的机位漂移…1.5 s 也该有明确的推镜或对焦拉动，从等离子体拉到镜面」:
              the b115_r28 dolly 3.0 -> 2.55 m (+25 % bowl area) read as drift (D 80). Push 3.4 -> 2.25 m (bowl
              area first -> last >= +40 %) and an f/2.8 focus pull plasma (f1-f12) -> the mirror face (f27-end).
  NOZZLE_R29  (row 5) R28 p1 「光锥穿过液滴发生器的喷嘴…把喷嘴移出光锥，或者从侧面伸进来」: the droplet generator +
              catcher come in from the SIDE (vertical, perpendicular to the axis, generator above / catcher below the
              plasma) instead of diagonally across the mouth toward the camera, so on screen neither crosses the
              cone that leaves the mouth to the right.
  EXIT_R29    (row 1 / 5) R28 p1 「在 IF 收成点后要继续发散一小段」: the post-IF leg 0.12 -> 0.25 of the mouth-IF distance so
              the volume visibly diverges again after the focus (the R27 0.3 fanned over the far wall in the old view).
Remove B1_15 from R29_SRC -> R28 camera / nozzle (beams still beam_r29 while B1_15 is in R29_BEAM).
"""
import math
import os

import bpy
from mathutils import Vector

CAM_R29 = True
NOZZLE_R29 = True
EXIT_R29 = True

D0, D1, FSTOP = 3.4, 2.25, 2.8
FOCUS_FACE = (0.52, 115.0)          # (radius, angle deg) of the mirror-face focus point (b115_r28 「收集镜」 anchor)
EXIT_LEG = "0.25"
_ORIG = {}


def pre(variant, shot, mod):
    if shot != "B1_15":
        return
    if CAM_R29:
        import b115_r28
        b115_r28.D0, b115_r28.D1 = D0, D1
    if EXIT_R29:
        os.environ["S27_EL"] = EXIT_LEG
    if NOZZLE_R29:
        import hero_kit_r10 as H
        import b115_r21 as B
        if "dg" not in _ORIG:
            _ORIG["dg"] = H.droplet_generator

        def dg(P, pos, dax, *a, **k):
            d2 = Vector((0, 0, -1))                       # droplets fall vertically through the plasma point
            return _ORIG["dg"](P, tuple(Vector(B.PC) - d2 * 0.26), tuple(d2), *a, **k)
        H.droplet_generator = dg


def _catcher():
    import b115_r21 as B
    import kit_r2 as K
    old = bpy.data.objects.get("B115CatcherR22")
    if old is None:
        return
    mat = old.active_material
    bpy.data.objects.remove(old, do_unlink=True)
    PC, d2 = Vector(B.PC), Vector((0, 0, -1))
    cat = K.MB()
    cat.tube(tuple(PC + d2 * 1.3), tuple(PC + d2 * 0.52), 0.05, seg=32)
    cat.tube(tuple(PC + d2 * 0.52), tuple(PC + d2 * 0.45), 0.05, seg=32, r2=0.09)
    cat.obj("B115CatcherR29", mat, bevel=0.002)


def _focus(sc):
    import b115_r21 as B
    cam = sc.camera
    foc = cam.data.dof.focus_object
    n = sc.frame_end
    r, a = FOCUS_FACE[0], math.radians(FOCUS_FACE[1])
    face = Vector((B.fx(r), r * math.cos(a), r * math.sin(a)))
    if foc is not None:
        if foc.animation_data:
            foc.animation_data_clear()
        for f, p in ((1, Vector(B.PC)), (12, Vector(B.PC)), (27, face), (n, face)):
            foc.location = p
            foc.keyframe_insert("location", frame=f)
    cam.data.dof.use_dof = True
    cam.data.dof.aperture_fstop = FSTOP


def post(sc, variant, shot):
    if shot != "B1_15":
        return sc
    if NOZZLE_R29:
        import hero_kit_r10 as H
        if "dg" in _ORIG:
            H.droplet_generator = _ORIG["dg"]
        _catcher()
    if CAM_R29:
        _focus(sc)
    sc.frame_set(1)
    return sc
