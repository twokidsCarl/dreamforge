"""R23 hook module (tin sub-agent, R23_ROOT_CAUSE row 3: tin pancake = smooth continuous liquid sheet).

  A0_01 / B1_10  pre(): source_r21.pancake_r21 -> source_r23_tin.pancake_r23 (in-process module attribute;
                 A0_01 / B1_10 are R21 pancakes in R22 because R22_TIN = {B1_08}).
                 post(): the sheet + its drops see ONE smooth gradient environment (opaque from inside, only for rays
                 that start inside it) instead of the R18 band dome + the real chamber modules (= the patchy
                 "crumpled foil" reflection). The env sphere is keyed to scale ~0 while the falling droplet is still
                 on screen (it would otherwise enclose the droplet too).
  A0_01          droplet beat (f72, same shared tin part = smooth reflection): the R22-smoked droplet env (continuous
                 gradient, no band rings) + thin rim light, reused from source_r22 (R22_TIN does not contain A0_01).
  B1_08          droplets only, no pancake -> no-op here (R22 pixels; R22 droplet fix already live via R22_TIN).
Tin material parameters untouched. Remove a shot from r2_source.R23_TIN -> exact R22 pixels.
"""
import bpy
from mathutils import Vector

ROW3_PANCAKE = {"A0_01", "B1_10"}
SHEET_R = {"A0_01": 0.26, "B1_10": 0.24}
DROP_GONE = {"A0_01": 94, "B1_10": 32}     # last frame the falling droplet is shown (r2_source show_between hit+2)
A001_DROP_ENV = True


def pre(variant, shot, mod):
    if shot in ROW3_PANCAKE:
        import source_r21 as S21
        import source_r23_tin as T
        S21.pancake_r21 = T.pancake_r23


def _ob(n):
    return bpy.data.objects.get(n)


def post(sc, variant, shot):
    if shot not in ROW3_PANCAKE:
        return
    import source_r23_tin as T
    parts = [o for o in (_ob("Pancake"), _ob("PancakeDrops")) if o]
    if parts:   # sphere encloses the sheet + its drops (max ~0.21 m at the last frame), not DropletNext
        env = T.sheet_env_r23("TinSheetEnvR23", (0, 0, 0), SHEET_R[shot], parts, shot)
        f0 = DROP_GONE[shot]
        for f, s in ((f0, 0.001), (f0 + 1, 1.0)):
            env.scale = (s, s, s)
            env.keyframe_insert("scale", frame=f)
        if env.animation_data and env.animation_data.action:
            try:
                for fc in env.animation_data.action.fcurves:
                    for kp in fc.keyframe_points:
                        kp.interpolation = "CONSTANT"
            except AttributeError:      # layered actions (Blender 5): channelbag fcurves
                for lay in env.animation_data.action.layers:
                    for st in lay.strips:
                        for cb in st.channelbags:
                            for fc in cb.fcurves:
                                for kp in fc.keyframe_points:
                                    kp.interpolation = "CONSTANT"
    if shot == "A0_01" and A001_DROP_ENV and _ob("Droplet"):
        import source_r22 as R22
        import source_r22_tin as T22
        T22.smooth_env_r22("TinEnvR22", (0, 0, 0.0), 0.06, [_ob("Droplet")])
        dome = _ob("TinEnvR22")
        dome.parent = _ob("Droplet")
        dome.location = (0, 0, 0)
        cam = Vector((0.535, -0.403, 0.14))
        back = (Vector((0, 0, 0.066)) - cam).normalized()
        li = T22.rim_light_r22("TinRimR22", (0, 0, 0), (0, 0, 0), 0.4, R22.RIM_E["A0_01"], [_ob("Droplet")])
        li.data.shape = "DISK"
        li.parent = _ob("Droplet")
        li.location = back * 0.15
        li.rotation_euler = (-back).to_track_quat("-Z", "Y").to_euler()
