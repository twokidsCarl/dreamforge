"""R23 cuth B3_02 (R23_ROOT_CAUSE rows 2 + 3; R22 review: "镜面本体看不出是椭球凹面…主角件不到 1/4", D 72; R22 smoke:
"85 % 帧锥消失"). Layered on the R20 B3_02 build (R22 pixels); the mirror group is NOT scaled.

- camera: front-oblique, az 55 deg off the dish axis (cut side), 24 mm, target at 50 % rim -> IF; dolly 4.4 m (f1) ->
  3.6 m (85 %) from the rim centre. The az 35 / 2.4 m sketch pose was tried first: the camera then sits beside the cone,
  perspective cancels the convergence (cone read as a violet haze, IF far off frame); az 45 cut the dish at the left edge
  -> numpy scan (r23smoke/cuth/scan.py) for poses with the whole rim AND the IF in frame AND the cone's screen width
  shrinking rim -> IF. Measured (cuth/meas.py): rim area f30 / f67 / f103 = 0.048 / 0.062 / 0.078 (R22 f103 0.053),
  IF (812,253) -> (873,246), cone axis 63-86 deg to the line of sight.
- CO2 laser hidden: from this side the hole -> plasma line projects across the dish face.
- reflected cone rebuilt (same rim, same IF): volume starts 0.5 m in front of the rim plane, smoothstep ramp over RAMP m,
  invisible to glossy rays, NOT dimmed at 62 % (R20 dimmed it to half -> the R22 "cone gone at 85 %").
- dish face: bright high-reflective neutral metal (R22 cuth recipe, no emission / violet).
"""
import math

import bpy
from mathutils import Vector

AZ = [55.0]
EL = [0.12]
LENS = [24]
D0, D1 = [4.4], [3.6]
TT = [0.5]   # target = rim centre -> IF at 60 % (keeps the converging cone + IF in frame)
KC = [2.2]   # cone density (R20 0.55 read near-invisible from the oblique side)
RAMP = [1.1]  # smoothstep fade-in length from the cone start (0.5 m in front of the rim)


def post(sc):
    import build_cutaway_r2 as B
    import kit_r2 as K
    import beam_r21 as R21B
    from cut_hero_r21 import _cam_tgt
    from cut_hero_r22_b302 import _ramp
    n = sc.frame_end
    c = B.COLL.copy()
    R0, f0 = 0.68, 0.42
    rimx = c.x + R0 * R0 / (4 * f0)
    RIMC = Vector((rimx, 0.0, c.z))

    for nm in ("LaserCore", "LaserHalo"):
        ob = bpy.data.objects.get(nm)
        if ob is not None:
            ob.hide_render = True
            ob.hide_viewport = True

    for ob in list(bpy.data.objects):
        if ob.name.startswith(("CollectConeR18", "CollectConeR21", "CollectConeR22")):
            bpy.data.objects.remove(ob)
    a0 = Vector((rimx + 0.01, 0, c.z))
    L = (B.IF - a0).length
    t0 = 0.5 / L
    a = a0.lerp(B.IF, t0)
    ra = 0.58 * (1 - t0) + 0.012 * t0
    objs, mats = R21B.cone(a, B.IF, ra, 0.012, "CollectConeR23", k=KC[0], seg=64)
    for m in mats:
        _ramp(m, a, B.IF, RAMP[0])
    for o in objs:
        try:
            o.visible_glossy = False
        except AttributeError:
            pass
    R21B.key_vis(objs, mats, n, 0.0, None)

    m = bpy.data.materials.get("CollectorDarkML_R20")
    if m is not None:
        bs = next(nd for nd in m.node_tree.nodes if nd.type == "BSDF_PRINCIPLED")
        bs.inputs["Base Color"].default_value = (0.82, 0.83, 0.86, 1.0)
        bs.inputs["Roughness"].default_value = 0.06
        bs.inputs["Metallic"].default_value = 1.0
        if "Emission Strength" in bs.inputs:
            bs.inputs["Emission Strength"].default_value = 0.0

    cam, tgt = _cam_tgt(sc)
    cam.animation_data_clear()
    if tgt is not None:
        tgt.animation_data_clear()
    cam.data.lens = LENS[0]
    th = math.radians(AZ[0])
    dv = Vector((math.cos(th), -math.sin(th), EL[0]))
    T = RIMC.lerp(B.IF, TT[0])
    f85 = round(n * 0.85)
    K.key_path(cam, tgt, [(1, tuple(RIMC + dv * D0[0]), tuple(T)),
                          (f85, tuple(RIMC + dv * D1[0]), tuple(T)),
                          (n, tuple(RIMC + dv * (D1[0] - 0.03)), tuple(T))])
    cam.data.dof.aperture_fstop = 11.0
    from bpy_extras.object_utils import world_to_camera_view
    fc = sc.frame_current
    for f in (30, 67, 103):
        sc.frame_set(f)
        s = f"[r23h] B3_02 f{f} cam {tuple(round(v, 2) for v in cam.matrix_world.translation)}"
        for nm_, p in (("IF", B.IF), ("PL", B.PLASMA), ("RIMC", RIMC), ("MID", RIMC.lerp(B.IF, 0.5))):
            q = world_to_camera_view(sc, cam, p)
            s += f" {nm_}=({q.x * 960:.0f},{(1 - q.y) * 540:.0f})"
        print(s)
    sc.frame_set(fc)
