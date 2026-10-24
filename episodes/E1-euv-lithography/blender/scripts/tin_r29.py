"""Round 29 tin material RECIPE (R29_ROOT_CAUSE row 2 / 2m, owned by the MAIN process - agents import it, never edit).

R28 review: tin = 「黑色钢珠，高光像『?』脸形」 (B1_08), sheets returned at 32 spp as 「黑盘上的白色贴纸 / P9」 (R28 hard-edged
emitter shapes, 90/10 10.6-15.3), R27 = 「灰色塑料椭圆盘」 (uniform soft env, 90/10 < 4). p1 #1: 「亮银、高反射的液态金属，
加掠射轮廓光」.

Recipe (between the two failures): the reflection sources stay ONLY in the reflection (env sphere seen by glossy rays
leaving the tin, source_r23/r25 env machinery) but every source is LARGE and SOFT-EDGED (smoothstep falloff, no
geometric outline, nothing letter- / face-shaped), on a dim - not black - chamber base:
  * a broad cool sky gradient above (liquid metal shows a horizon, not a stripe),
  * one large soft key box upper-left of the mirror direction + one smaller warm box on the other side (two soft
    glints, never a ring / window / dot pattern),
  * a cool and a warm GRAZING rim from behind (the bright outline p1 asks for),
  * base colour silver 0.93, roughness 0.06 (bright silver, not chrome-black).
Target: tin area 90/10 luminance percentiles 4-10 on the 32-spp mid frame.
"""
import math

import bpy
from mathutils import Vector

WHITE = (1.0, 0.98, 0.95)
COOL = (0.78, 0.86, 1.0)
WARM = (1.0, 0.84, 0.62)
SILVER = (0.93, 0.93, 0.95)
ROUGH = 0.06
DROP_BASE = (0.030, 0.032, 0.040)
SHEET_BASE = (0.018, 0.020, 0.027)


def _n(v):
    return tuple(Vector(v).normalized())


def drop_bands(tc, rt, up):
    tc, rt, up = Vector(tc), Vector(rt), Vector(up)
    return [((0, 0, 1), 1.0, 1.10, 0.55, COOL),                              # broad cool sky -> soft horizon
            (_n(tc + up * 0.9 - rt * 0.6), 1.0, 0.090, 3.2, WHITE),           # large soft key box (upper-left)
            (_n(tc + up * 0.15 + rt * 0.95), 1.0, 0.045, 1.6, WARM),          # smaller warm box (right)
            (_n(-tc + up * 0.25 + rt * 0.45), 1.0, 0.45, 1.5, COOL),          # cool grazing rim from behind
            (_n(-tc - rt * 0.55 - up * 0.1), 1.0, 0.30, 1.1, WARM)]           # warm grazing rim, other side


def sheet_bands(tc, rt, up, nrm, mdir):
    """the flat sheet only sees a ~40 deg window round its mirror direction: a soft horizon + two soft boxes inside it,
    a grazing light in the sheet plane (bright thickness edge) and rims from behind."""
    md = Vector(mdir).normalized()
    tc, rt, up = Vector(tc), Vector(rt), Vector(up)
    return [(_n(md + up * 0.50), 1.0, 0.16, 0.55, COOL),                       # sky above the mirror direction (soft horizon)
            (_n(md + up * 0.10 - rt * 0.16), 1.0, 0.030, 3.0, WHITE),         # soft key box in the face
            (_n(md - up * 0.12 + rt * 0.20), 1.0, 0.020, 1.6, WARM),          # soft warm box, lower-right
            (_n(nrm), 0.0, 0.20, 2.6, WHITE),                                 # in-plane light -> bright edge / lip
            (_n(-tc + up * 0.3), 1.0, 0.45, 1.4, COOL),                       # rim from behind
            (_n(-tc - rt * 0.5), 1.0, 0.30, 1.0, WARM)]


def silver_mat(name="TinSilverR29"):
    import source_r25_tin as T25
    m = T25.tin_mat_r25(name)
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (*SILVER, 1)
    b.inputs["Roughness"].default_value = ROUGH
    b.inputs["Metallic"].default_value = 1.0
    return m


def _ob(n):
    return bpy.data.objects.get(n)


def apply(sc, shot, drop_frame, sheet_frame=None):
    """Swap the tin material + every tin env sphere (R27 / R28) for the R29 recipe. Returns a report dict."""
    import source_r23_tin as T23
    import source_r24 as H24
    import source_r25_tin as T25
    rep = {"tin": 0, "drops": 0, "sheet": False}
    for o in list(bpy.data.objects):          # R28 hard-edged emitters (decals) never come back
        if o.name.startswith(("TinReflWindowR28", "TinReflFlangeR28", "TinReflPlasmaR28", "TinReflStripR28")):
            bpy.data.objects.remove(o, do_unlink=True)
    m = silver_mat()
    for o in bpy.data.objects:
        am = o.active_material if o.type == "MESH" else None
        if am is not None and am.name.startswith(("TinMetalR27", "TinMetalR25", "TinMetalR24", "LiquidTin")):
            for i, s in enumerate(o.material_slots):
                s.material = m
            rep["tin"] += 1
        elif am is not None and am.name.startswith("TinFilmR27"):
            b = next(n for n in am.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
            b.inputs["Base Color"].default_value = (*SILVER, 1)
            b.inputs["Roughness"].default_value = ROUGH
            rep["tin"] += 1
    for e in list(bpy.data.objects):
        if not e.name.startswith("TinEnvR27_") or e.parent is None:
            continue
        tc, rt, up = H24._cam_dirs(sc, drop_frame, e.parent.matrix_world.translation.copy())
        mm = T23._env_mat_r23("TinEnvR29Mat_" + e.parent.name, drop_bands(tc, rt, up), DROP_BASE, 1.0, 0.05)
        e.data.materials.clear()
        e.data.materials.append(mm)
        rep["drops"] += 1
    root = _ob("PancakeRoot")
    if sheet_frame is not None and root is not None:
        tc, rt, up = H24._cam_dirs(sc, sheet_frame, (0, 0, 0))
        yaw = root.rotation_euler.z
        nrm = Vector((math.cos(yaw), math.sin(yaw), 0))
        if nrm.dot(tc) < 0:
            nrm = -nrm
        v = -tc
        md = v - 2 * v.dot(nrm) * nrm
        old = [o for o in bpy.data.objects if o.name.startswith(("TinSheetEnvR27", "TinSheetEnvR28", "TinSheetEnvR25"))]
        rad = 0.27
        for o in old:
            rad = max(o.dimensions) * 0.5 if o.dimensions.length > 0 else rad
            bpy.data.objects.remove(o, do_unlink=True)
        T25.env_r25("TinSheetEnvR29", (0, 0, 0), rad, sheet_bands(tc, rt, up, nrm, md), base=SHEET_BASE)
        rep["sheet"] = True
    print(f"[tin_r29] {shot} {rep}", flush=True)
    return rep
