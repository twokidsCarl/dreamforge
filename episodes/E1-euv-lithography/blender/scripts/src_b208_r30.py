"""Round 30 hook (kit sub-agent; r2_source.R30_B208 = {"B2_08"}), called AFTER the R22..R29 hooks (src_r27_b208
MIRROR_R27 room + SPOTS_R27 stains; src_b208_r29 is OFF) and BEFORE beam_hook_r29. Remove B2_08 from R30_B208 -> exact
R29 pixels.

  MIRROR_R30  row 6b (B2_08): R29 p1 「镜面被画成一块哑光、带同心灰白条带加一块剖开的楔形片的盘子，看不出是镜子…改成高反射、
              平滑的椭球镜面，锡斑做成镜面上的暗点；去掉楔形剖开片」. NOT the R29 tin_r29 soft-source + violet coat (read
              「哑光米色塑料」). Reuses the mirror recipe reviewers accepted on B1_15 / B3_02 (import only, never edited):
              cut_mirror_r19.hi_mirror() (metallic 1, rough 0.05, neutral tone) on the collector face, and lit REAL
              chamber structure in the face's reflection direction (cut_mirror_r19 idea: kit_r19 wall assembly lit by
              a glossy-invisible fill). Every older reflection helper that drew the grey-white concentric bands / the
              wedge (R21 graze strip, R22 graze band / neutral panel, R23 sheen sheet, R27 room + flange rings) is
              deleted. TinDeposits (dark, rough) stay = dark spots on the bright mirror.
"""
import os

MIRROR_R30 = True

_E = os.environ
KILL = ("B208ReflRoomR27", "B208ReflPortsR27", "B208SheenR23", "B208GrazeBandR22", "B208NeutralPanelR22",
        "B208GrazeStripR21", "B208GrazeR21", "B208EnvR29")


def _near_dish():
    import bpy
    from mathutils import Vector
    mir = bpy.data.objects.get("CollB208_mirror")
    bb = [mir.matrix_world @ Vector(c) for c in mir.bound_box]
    return sum(bb, Vector()) / 8, max((v - sum(bb, Vector()) / 8).length for v in bb)


def _mirror(sc):
    import bpy
    import cut_mirror_r19 as CM
    gone = []
    for o in list(bpy.data.objects):
        if o.name.startswith(KILL):
            gone.append(o.name)
            bpy.data.objects.remove(o, do_unlink=True)
    for c in list(bpy.data.collections):
        if c.name.startswith(KILL) or c.name.startswith("B208GrazeRecvR21"):
            bpy.data.collections.remove(c)
    print(f"[b208r30] removed {gone}", flush=True)
    mir = bpy.data.objects.get("CollB208_mirror")
    if mir is None:
        print("[b208r30] CollB208_mirror missing", flush=True)
        return
    hi = CM.hi_mirror(rough=float(_E.get("B30_ROUGH", "0.05")))
    mir.data.materials.clear()
    mir.data.materials.append(hi)
    print(f"[b208r30] face -> {hi.name}", flush=True)


def diag(sc, f=133):
    """reflected camera rays off the face -> what they hit first (object histogram)"""
    import bpy
    from collections import Counter
    sc.frame_set(f)
    dg = bpy.context.evaluated_depsgraph_get()
    cam = sc.camera
    co = cam.matrix_world.translation
    fr = cam.data.view_frame(scene=sc)
    hits, first, n = Counter(), Counter(), 0
    for i in range(32):
        for j in range(18):
            p = cam.matrix_world @ (fr[2] + (fr[1] - fr[2]) * ((i + 0.5) / 32) + (fr[3] - fr[2]) * ((j + 0.5) / 18))
            d = (p - co).normalized()
            o_ = co
            for _k in range(8):
                ok, loc, nrm, _, ob, _ = sc.ray_cast(dg, o_, d)
                if not ok or (ob.visible_camera and not ob.hide_render):
                    break
                o_ = loc + d * 1e-3
            first[ob.name if ok else "-"] += 1
            if not ok or ob.name != "CollB208_mirror":
                continue
            n += 1
            r = d - 2 * d.dot(nrm) * nrm
            o_ = loc + r * 1e-3
            for _k in range(8):
                ok2, loc2, _, _, ob2, _ = sc.ray_cast(dg, o_, r)
                if not ok2 or (ob2.visible_glossy and not ob2.hide_render):
                    break
                o_ = loc2 + r * 1e-3
            hits[ob2.name if ok2 else "-"] += 1
    print(f"[b208r30 diag] first hits {first.most_common(14)}", flush=True)
    print(f"[b208r30 diag] face samples {n}: {hits.most_common(16)}", flush=True)
    print(f"[b208r30 diag] lights {[(o.name, o.data.type, round(o.data.energy, 1), o.visible_glossy) for o in bpy.data.objects if o.type == 'LIGHT']}", flush=True)


_MOD = {}


def _spots_big(f=None):
    """tin deposits stay the R27 dark stains (alpha-cleaned over time); each stain island is scaled about its own
    centre so the dark spots stay legible against the now bright, structured reflection."""
    import bpy
    import bmesh
    f = f or float(_E.get("B30_SPOT", "1.6"))
    dep = bpy.data.objects.get("TinDeposits")
    if dep is None or f == 1.0:
        return
    bm = bmesh.new()
    bm.from_mesh(dep.data)
    seen = set()
    k = 0
    for v in bm.verts:
        if v.index in seen:
            continue
        grp, stack = [], [v]
        seen.add(v.index)
        while stack:
            w = stack.pop()
            grp.append(w)
            for e in w.link_edges:
                o = e.other_vert(w)
                if o.index not in seen:
                    seen.add(o.index)
                    stack.append(o)
        c = sum((w.co for w in grp), grp[0].co * 0) / len(grp)
        for w in grp:
            w.co = c + (w.co - c) * f
        k += 1
    bm.to_mesh(dep.data)
    bm.free()
    print(f"[b208r30] {k} stain islands x{f}", flush=True)


def _env(sc):
    """cut_mirror_r19.reflect_env (the B5_01 / B1_15-era accepted recipe): a lit kit_r19 wall assembly where the face's
    reflected camera ray lands, for the deposit patch and the dark mid-face, so dark tin spots sit on a bright,
    structured reflection (not on navy void)."""
    import math
    import b115_r17 as B115
    import cut_mirror_r19 as CM
    from mathutils import Vector
    mod = _MOD.get("mod")
    M = mod._mats() if mod is not None and hasattr(mod, "_mats") else {}
    F = B115.B_F
    heroes = []
    for rr, ang, size in ((0.33, 80.0, float(_E.get("B30_S1", "1.2"))), (0.34, -10.0, float(_E.get("B30_S2", "1.2")))):
        a = math.radians(ang)
        y, z = rr * math.cos(a), rr * math.sin(a)
        nrm = Vector((1, -y / (2 * F), -z / (2 * F))).normalized()
        heroes.append(((B115.face_x(rr), y, z), nrm, size))
    obs = CM.reflect_env(sc, M, heroes, tag="B208EnvR30", dist=1.8, light=float(_E.get("B30_L", "40")), seed=2080,
                         frames=[60, 133, 206])
    print(f"[b208r30] env {len(obs)} objs", flush=True)


def pre(variant, shot, mod):
    if shot == "B2_08":
        _MOD["mod"] = mod
    return None


def post(sc, variant, shot):
    if shot == "B2_08" and _E.get("B30_DIAG0"):
        diag(sc)
    if shot == "B2_08" and MIRROR_R30:
        _mirror(sc)
        _spots_big()
        if not _E.get("B30_NOENV"):
            _env(sc)
        if _E.get("B30_DIAG"):
            diag(sc)
    return sc
