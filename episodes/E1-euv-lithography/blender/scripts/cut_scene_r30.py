"""Round 30 hook (MAIN PROCESS; shots in r2_cutaway.R30_SCENE = C_03 / B3_02 / B7_06). Layered after the R22..R29 hooks and
BEFORE beam_hook_r29 (legs built here are converted to beam_r29 volumes; beam_hook_r30 tapers / floors them).

  FFM_R30    (row 4, C_03) R29 p2 「第二帧的『场分面镜』是一块方板…和 B5_01 里的弧形长条小镜阵列不一致，同一部件在片中出现了
             两套画法。要换成同一个模型。光打到场分面镜就停了，应该再画一段从场分面镜折到光瞳镜的光」: the builder's facet block
             (R8Kit2_facet) is hidden and parts_r30.facet_plate (= the B5_01 R29 model) sits on the same landing, turned
             toward the f222 camera; a new FFM -> PFM leg lands on the pupil-facet disc (spot on its face).
  DEBRIS_R30 (row 4, C_03) 「第一帧（约 210–280, 360）有一团白色噪点碎屑」: a ray pick at those pixels hits R2_vessel - the key
             light's blown specular on the polished vessel (black / red specks = blown-highlight sampling). The vessel gets
             its own satin copy of its material (roughness >= 0.45) in C_03 only -> soft sheen, no blown core.
  B302_R30   (row 5a, B3_02) 「腔壁要压暗、改喷砂哑光；镜面保留高光泽…IF 那个点正好落在锥尖上」: the chamber wall (R2_vessel)
             gets a dark sand-blasted copy material; a bright soft focus spot sits exactly on the cone tip = the IF tag's
             anchor point (B.IF), so the tag points at the tip.
B7_06 (row 5c) is handled by beam_hook_r30 (M6-aperture convergent last leg); its set membership here is a no-op.
Remove a shot from R30_SCENE -> R29 pixels; a switch False -> that item's R29 pixels.
"""
import bpy
from mathutils import Vector

FFM_R30 = True
DEBRIS_R30 = True
B302_R30 = False   # main 32-spp Q4 no (pale matte drum) -> R29 pixels

C03_WIN_FRAME = 222


def pre(variant, shot, mod):
    return None


def _mat_copy(ob, tag, base=None, rough=None, rough_min=None, metal=None):
    n = 0
    for s in ob.material_slots:
        m = s.material
        if m is None or not m.use_nodes:
            continue
        m2 = m.copy()
        m2.name = m.name + tag
        b = next((x for x in m2.node_tree.nodes if x.type == "BSDF_PRINCIPLED"), None)
        if b is None:
            continue
        for lk in list(m2.node_tree.links):
            if lk.to_node == b and lk.to_socket.name in (("Base Color",) if base else ()) + (("Roughness",) if (rough or rough_min) else ()):
                m2.node_tree.links.remove(lk)
        if base is not None:
            b.inputs["Base Color"].default_value = (*base, 1)
        if rough is not None:
            b.inputs["Roughness"].default_value = rough
        if rough_min is not None:
            b.inputs["Roughness"].default_value = max(b.inputs["Roughness"].default_value, rough_min)
        if metal is not None:
            b.inputs["Metallic"].default_value = metal
        s.material = m2
        n += 1
    return n


def _c03(sc):
    import beam_r26 as BR
    import build_cutaway_r2 as B
    import kit_r2 as K
    import parts_r30 as P
    if FFM_R30:
        fac = bpy.data.objects.get("R8Kit2_facet")
        if fac is not None:
            fac.hide_render = True
        sc.frame_set(C03_WIN_FRAME)
        cam = sc.camera.matrix_world.translation
        piv = Vector(B.FFM)
        leg = bpy.data.objects.get("C03R28InLeg0")
        entry = Vector((-4.25, 0.0, 2.57))
        n0 = ((entry - piv).normalized() + (Vector(B.PFM) - piv).normalized()).normalized()
        n = (n0 + (cam - piv).normalized() * 0.6).normalized()
        P.facet_plate("C03R30Ffm", piv, n, 1.0, 0.72)
        n2 = (K.mirror_normal(B.FFM, B.PFM, B.G1) + Vector((0, -0.5, 0))).normalized()
        ch = BR.chain("C03R30Fp", [(piv, n), (Vector(B.PFM), n2)], [0.17, 0.05], strength=7.0, spot_strength=16.0,
                      mirrors=False)
        print(f"[r30s] C_03 FFM plate (B5_01 model) n.cam {n.dot((cam - piv).normalized()):.2f}; FFM -> PFM leg "
              f"{len(ch['legs'])}; in-leg present {leg is not None}", flush=True)
    if DEBRIS_R30:
        v = bpy.data.objects.get("R2_vessel")
        k = _mat_copy(v, "_R30satin", rough_min=0.45) if v is not None else 0
        print(f"[r30s] C_03 vessel satin copies {k}", flush=True)


def _b302(sc):
    import beam_r30 as B30
    import build_cutaway_r2 as B
    v = bpy.data.objects.get("R2_vessel")
    k = _mat_copy(v, "_R30blast", base=(0.07, 0.072, 0.08), rough=0.62, metal=0.4) if v is not None else 0
    sc.frame_set(67)
    cam = sc.camera.matrix_world.translation
    to_cam = (cam - Vector(B.IF)).normalized()
    ex = to_cam.cross(Vector((0, 0, 1))).normalized()
    ey = to_cam.cross(ex).normalized()
    r = 0.045
    B30.spot_disc("B3R30IFTip", Vector(B.IF) + to_cam * 0.02, ex * r, ey * r, to_cam, None, gain=7.0)
    print(f"[r30s] B3_02 vessel blasted copies {k}; IF tip spot at {tuple(round(x, 2) for x in B.IF)}", flush=True)


def post(sc, variant, shot):
    if shot == "C_03":
        _c03(sc)
    if shot == "B3_02" and B302_R30:
        _b302(sc)
    sc.frame_set(1)
    return sc
