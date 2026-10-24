"""Round 29 hook (kit sub-agent; r2_source.R29_B208 = {"B2_08"}), called AFTER the R22..R28 hooks (src_r27_b208 MIRROR_R27
room + SPOTS_R27 fading stains underneath). Remove B2_08 from R29_B208 -> exact R28 pixels.

  MIRROR_R29  row 2m (B2_08): R28 p1 「收集镜画成了哑光白塑料，上面还有黑色同心弧带…改成高反射镀膜：环境反射 + 掠射高光，
              深色锡斑保留成低反射的斑点」 -> the R27 reflection room (B208ReflRoomR27: hard horizon + sharp softboxes) and
              its three lit flange rings (B208ReflPortsR27 = the black/white concentric arcs once the concave face
              magnifies them) are deleted. The collector face gets a high-reflective multilayer coating (metal 1,
              silver with a faint violet Mo/Si tint, low roughness) lit by the main-process tin_r29 RECIPE idea: ONE
              env_r25 sphere around the dish (glossy rays leaving the face only; invisible to camera / shadow) whose
              bands are all large and soft-edged (tin_r29 colours): a broad cool sky gradient (soft horizon across the
              concave face), one soft key box where the labelled deposit patch reflects (dark stains read on bright
              metal), a smaller warm box, and a cool grazing rim near the edge of the reflected cone (bright rim on the
              dish lip). No rings / windows / letters. TinDeposits (SPOTS_R27 fading stains) are untouched = dark,
              low-reflectance spots.
"""
import os

MIRROR_R29 = False   # 8-spp Q1 no (face still reads matte beige) -> R28 pixels; see SMOKE.md

_E = os.environ
# reflected camera-ray directions of the face (src_r27_b208 B208DIAG): x -0.3..+1, y +0.3..+0.96, z -0.6..+0.2
CENTRE = (-0.3, 0.0, 0.0)
RADIUS = 1.18


def _bands(g):
    import tin_r29 as T
    return [((0, 0, 1), 1.0, 1.00, 0.55 * g, T.COOL),                 # broad cool sky -> soft horizon over the face
            ((0.35, 0.80, -0.47), 1.0, 0.11, 3.2 * g, T.WHITE),       # large soft key box behind the deposit patch
            ((0.90, 0.32, -0.20), 1.0, 0.06, 1.6 * g, T.WARM),        # smaller warm box, lower right of the face
            ((-0.25, 0.95, 0.10), 1.0, 0.30, 1.4 * g, T.COOL),        # cool grazing rim (edge of the reflected cone)
            ((0.60, 0.30, -0.75), 1.0, 0.25, 0.9 * g, T.WARM)]        # warm grazing rim, other side


def _mirror(sc):
    import bpy
    import source_r25_tin as T25
    import tin_r29 as T
    for o in list(bpy.data.objects):
        if o.name.startswith(("B208ReflRoomR27", "B208ReflPortsR27", "B208SheenR23")):
            bpy.data.objects.remove(o, do_unlink=True)
    mir = bpy.data.objects.get("CollB208_mirror")
    if mir is None:
        print("[b208r29] CollB208_mirror missing", flush=True)
        return
    m = bpy.data.materials.new("CollCoatR29")
    m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (0.90, 0.88, 0.97, 1)       # silver + faint violet multilayer tint
    b.inputs["Metallic"].default_value = 1.0
    b.inputs["Roughness"].default_value = float(_E.get("B29_ROUGH", "0.03"))
    mir.data.materials.clear()
    mir.data.materials.append(m)
    g = float(_E.get("B29_GAIN", "0.12"))
    base = tuple(c * float(_E.get("B29_BASE", "1.0")) for c in T.DROP_BASE)
    from mathutils import Vector
    bb = [mir.matrix_world @ Vector(c) for c in mir.bound_box]
    ctr = sum(bb, Vector()) / 8
    rad = max((v - ctr).length for v in bb) * float(_E.get("B29_RAD", "1.08"))
    env = T25.env_r25("B208EnvR29", tuple(ctr), rad, _bands(g), base=base)
    # opaque for the face's reflected rays (8-spp try 1: the additive see-through sphere let the face mirror the
    # cut chamber / dish rings = the black concentric arcs came back): emission only, glossy-only visibility
    nt = env.data.materials[0].node_tree
    em = next(n for n in nt.nodes if n.type == "EMISSION")
    out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
    for l in list(em.inputs["Strength"].links):
        nt.links.remove(l)
    em.inputs["Strength"].default_value = 1.0
    nt.links.new(em.outputs[0], out.inputs["Surface"])
    env.visible_glossy = True
    print(f"[b208r29] env centre {tuple(round(x, 3) for x in ctr)} r {rad:.3f}", flush=True)
    print(f"[b208r29] mirror coat + soft env gain {g}", flush=True)


def diag(sc, f=133):
    """reflected camera rays off the face -> what they hit first (object histogram)"""
    import bpy
    from collections import Counter
    from mathutils import Vector
    sc.frame_set(f)
    dg = bpy.context.evaluated_depsgraph_get()
    cam = sc.camera
    co = cam.matrix_world.translation
    fr = cam.data.view_frame(scene=sc)
    hits, first, n = Counter(), Counter(), 0
    for i in range(24):
        for j in range(14):
            p = cam.matrix_world @ (fr[2] + (fr[1] - fr[2]) * ((i + 0.5) / 24) + (fr[3] - fr[2]) * ((j + 0.5) / 14))
            d = (p - co).normalized()
            o_ = co
            for _k in range(8):
                ok, loc, nrm, _, ob, _ = sc.ray_cast(dg, o_, d)
                if not ok or not (ob.name.startswith("B208EnvR29") or not ob.visible_camera or ob.hide_render):
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
                if not ok2 or ob2.name.startswith("B208EnvR29") or (ob2.visible_glossy and not ob2.hide_render):
                    break
                o_ = loc2 + r * 1e-3
            hits[ob2.name if ok2 else "-"] += 1
    print(f"[b208r29 diag] first hits {first.most_common(8)}", flush=True)
    print(f"[b208r29 diag] face samples {n}: {hits.most_common(12)}", flush=True)


def pre(variant, shot, mod):
    return None


def post(sc, variant, shot):
    if shot == "B2_08" and MIRROR_R29:
        _mirror(sc)
        if _E.get("B29_DIAG"):
            diag(sc)
    return sc
