"""Round 31 hook (MAIN process; r2_source.R31_SRC = {"B1_15"}), layered after the R30 hooks and before beam_hook_r29.

  MIRROR_R31 (row 3c, B1_15): R30 p1 「镜面像哑光白塑料…改成高反低粗糙度，映出等离子和腔内结构」; B2_08 「这里的收集镜是
             镀铬高反，B1_15 是哑光白，同一部件前后两镜材质不一致…以本镜为准，统一成高反」. One collector = one material:
             the ray-picked face object CollFaceR20 (sketch31/b115_grid.txt; only that object, never a shared material)
             gets the B2_08 R30 recipe - cut_mirror_r19.hi_mirror(rough 0.05) + a lit kit_r19 wall in the face's
             camera-reflection direction (cut_mirror_r19.reflect_env, same call as src_b208_r30._env).
  The cone base on the whole rim (p1 「让光锥底面贴住整个镜口边缘」) is beam_hook_r31 (r2_source.R31_BEAM).
Remove B1_15 from R31_SRC -> R30 pixels.
"""
MIRROR_R31 = True
ROUGH = 0.05
_MOD = {}


def pre(variant, shot, mod):
    if shot == "B1_15":
        _MOD["mod"] = mod


def _env(sc):
    import math
    import b115_r17 as B115
    import cut_mirror_r19 as CM
    from mathutils import Vector
    mod = _MOD.get("mod")
    M = mod._mats() if mod is not None and hasattr(mod, "_mats") else {}
    F = B115.B_F
    heroes = []
    for rr, ang, size in ((0.34, 80.0, 1.2), (0.36, -10.0, 1.2), (0.36, 200.0, 1.0)):
        a = math.radians(ang)
        y, z = rr * math.cos(a), rr * math.sin(a)
        nrm = Vector((1, -y / (2 * F), -z / (2 * F))).normalized()
        heroes.append(((B115.face_x(rr, B115.B115_SHIFT), y, z), nrm, size))
    obs = CM.reflect_env(sc, M, heroes, tag="B115EnvR31", dist=1.8, light=40.0, seed=1151, frames=[9, 20, 31])
    return len(obs)


def post(sc, variant, shot):
    if not (MIRROR_R31 and shot == "B1_15"):
        return sc
    import bpy
    import cut_mirror_r19 as CM
    face = bpy.data.objects.get("CollFaceR20")
    if face is None:
        print("[src_r31] B1_15: CollFaceR20 missing", flush=True)
        return sc
    old = [s.material.name for s in face.material_slots if s.material]
    hi = CM.hi_mirror(rough=ROUGH)
    face.data.materials.clear()
    face.data.materials.append(hi)
    n_env = _env(sc)
    print(f"[src_r31] B1_15 CollFaceR20 {old} -> {hi.name}; reflect_env {n_env} objs", flush=True)
    sc.frame_set(1)
    return sc
