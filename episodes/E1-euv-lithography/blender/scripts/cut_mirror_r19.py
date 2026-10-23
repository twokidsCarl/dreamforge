"""Round 19 (P1, R19_ROOT_CAUSE row 2, r2_cutaway): mirrors read as real metal mirrors.

R18 p2 (six shots): "镜面全部换成真金属反射：分面小镜、M5 / M6、收集镜现在偏哑光，有塑料感 … 镜面能反射出周围结构".
Cause: mirror_r15.ml_mirror is already polished metal, but in each mirror's reflection direction there is only dark
chamber (or nothing), so a polished face renders as one even grey = "plastic tile / frosted plate". Two parts:

  (a) hi_mirror(): ONE high-reflective mirror surface for every mirror of the module (field / pupil facets, fold
      mirrors G1 / G2, PO mirrors M1..M6 incl. M5 / M6, collector): metallic, roughness 0.05 (tiny polish
      variation 0.04-0.06), light neutral tone, NO emission, NO violet base. apply() swaps every mirror-face
      material of the scene (mirror_r15 / R18 facet / R11 facet / M5-M6 face materials) for it.
  (b) reflect_env(): give each HERO mirror something lit to reflect - REAL structure, not a light card: from the
      camera (mid-shot) the view ray on the mirror's landing point is mirrored about its normal; where that
      reflected ray hits the scene (scene.ray_cast) a kit_r19.wall_r19 assembly (valve island / gas panel / ion
      pump / power box / coolant run ...) is mounted on that surface, facing the mirror, and lit by one small fill
      point light that is invisible to glossy rays (so the mirror shows the lit PARTS, never a lamp / card). If the
      reflected ray leaves the scene, the assembly stands at `dist`; if it would show directly in the camera frame
      it is hidden from camera rays only (it is still the real structure the mirror sees - noted in SMOKE.md).

  import cut_mirror_r19 as CM
  CM.apply(M)                                     # after the scene is built
  CM.reflect_env(sc, M, [(c, n, size)], tag="B5")  # after the camera is keyed
"""
import math

import bpy
from mathutils import Matrix, Vector

import kit_r2 as K

MIRROR_PREFIX = ("EUVMirrorML_R15", "EUVCoatingML_R15", "CollectorML_R15", "FacetML_R15", "FacetML_R18",
                 "FacetMirrorR11", "M56FaceR15", "EUVMirrorUnlit_R15")
_HI = {}
SKIP = ("Cone", "Halo", "Land", "Beam", "Vol", "Glow", "Spot", "Leg", "Ray", "Pinch", "Plasma", "Laser", "Col")
LOG = []


def hi_mirror(name="EUVMirrorHiR19", rough=0.05, tone=0.9):
    """Polished multilayer mirror: metallic 1, roughness 0.05, light warm-neutral tone (never violet), no emission."""
    key = (name, rough, tone)
    if key in _HI and _HI[key].name in bpy.data.materials:
        return _HI[key]
    m = K.mat(name, (tone, tone * 0.99, tone * 0.97), metal=1.0, rough=rough, coat=0.2)
    nt = m.node_tree
    b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 40.0
    nz.inputs["Detail"].default_value = 1.0
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["To Min"].default_value = rough * 0.8
    mr.inputs["To Max"].default_value = rough * 1.2
    nt.links.new(nz.outputs["Fac"], mr.inputs["Value"])
    nt.links.new(mr.outputs["Result"], b.inputs["Roughness"])
    _HI[key] = m
    return m


def apply(M=None, prefixes=MIRROR_PREFIX, mat=None):
    """Swap every mirror-face material in the scene for the R19 high-reflective mirror. Returns #slots swapped."""
    hi = mat or hi_mirror()
    nsw = 0
    for ob in bpy.data.objects:
        for sl in getattr(ob, "material_slots", []):
            m = sl.material
            if m is not None and m is not hi and m.name.startswith(prefixes):
                sl.material = hi
                nsw += 1
        if ob.type == "MESH":
            for i, m in enumerate(ob.data.materials):
                if m is not None and m is not hi and m.name.startswith(prefixes):
                    ob.data.materials[i] = hi
                    nsw += 1
    if M is not None:
        for k in ("mirror", "coating", "facet", "facet18"):
            if k in M and M[k] is not None and M[k].name.startswith(prefixes):
                M[k] = hi
    LOG.append(f"apply: {nsw} slots -> {hi.name}")
    print(f"[cut_mirror_r19] {LOG[-1]}")
    return nsw


def _cam_pos(sc, frame):
    sc.frame_set(frame)
    return sc.camera.matrix_world.translation.copy()


def _in_frame(sc, p, frames):
    from bpy_extras.object_utils import world_to_camera_view
    for f in frames:
        sc.frame_set(f)
        v = world_to_camera_view(sc, sc.camera, Vector(p))
        if v.z > 0 and -0.1 < v.x < 1.1 and -0.1 < v.y < 1.1:
            return True
    return False


def reflect_env(sc, M, heroes, tag="R19Env", dist=2.5, light=40.0, seed=190, frames=None, max_d=6.0, inset=0.04):
    """heroes: [(centre, normal, size)] - size = wall width (m). Builds one lit kit_r19 wall per hero mirror in its
    camera-reflection direction. Returns the objects."""
    import hero_kit_r10 as H
    import kit_r19 as KR
    n_fr = sc.frame_end
    frames = frames or [1, max(1, n_fr // 2), n_fr]
    mid = frames[len(frames) // 2]
    out = []
    dg = bpy.context.evaluated_depsgraph_get()
    for i, (c, nrm, size) in enumerate(heroes):
        c, nrm = Vector(c), Vector(nrm).normalized()
        cam = _cam_pos(sc, mid)
        v = (c - cam).normalized()
        r = (v - 2 * v.dot(nrm) * nrm).normalized()
        d = dist
        bpy.context.view_layer.update()
        dg = bpy.context.evaluated_depsgraph_get()
        o0 = c + r * 0.15
        for _k in range(12):                 # skip beam volumes / glows / landing marks: only solid parts count
            hit, loc, hn, _idx, hob, _m = sc.ray_cast(dg, o0, r, distance=max_d)
            if not hit or not any(t in hob.name for t in SKIP):
                break
            o0 = loc + r * 0.01
            hit = False
        if hit and (loc - c).length > 0.6:
            d = (loc - c).length - inset
        where = c + r * d
        # local frame: wall plate front toward local -Y must face the mirror -> local +Y = r
        y = r
        up = Vector((0, 0, 1)) if abs(r.z) < 0.9 else Vector((1, 0, 0))
        x = y.cross(up).normalized()
        z = x.cross(y).normalized()
        R = Matrix((x, y, z)).transposed().to_4x4()
        piv = bpy.data.objects.new(f"{tag}Piv{i}", None)
        sc.collection.objects.link(piv)
        piv.matrix_world = Matrix.Translation(where) @ R
        P = H.new_parts()
        h = size * 0.62
        KR.wall_r19(P, -size / 2, size / 2, -h / 2, h / 2, 0.0, seed=seed + i, scale=max(0.5, size / 2.4),
                    depth=0.8)
        obs = H.finish(P, M, f"{tag}{i}", parent=piv)
        # backing plate so the assembly reads as mounted equipment, not floating parts
        bp = K.MB()
        bp.box((0, 0.03, 0), (size * 1.04, 0.04, h * 1.06))
        obs.append(bp.obj(f"{tag}{i}_plate", M.get("paint_grey", M.get("alu"))))
        obs[-1].parent = piv
        hidden = _in_frame(sc, where, frames)
        for o in obs:
            if hidden:
                o.visible_camera = False
            o.visible_shadow = False
        lt = K.point(f"{tag}Fill{i}", where - r * (0.5 + 0.3 * size), light * max(1.0, size), (0.95, 0.96, 1.0),
                     0.3 * size)
        lt.visible_glossy = False
        try:
            lt.data.use_shadow = True
        except AttributeError:
            pass
        out += obs + [lt, piv]
        LOG.append(f"{tag}{i}: mirror {tuple(round(a, 2) for a in c)} -> reflected dir {tuple(round(a, 2) for a in r)}"
                   f", wall at d={d:.2f} m ({'hit ' + hob.name if hit else 'open'}), camera-hidden={hidden}")
        print(f"[cut_mirror_r19] {LOG[-1]}")
    sc.frame_set(1)
    return out
