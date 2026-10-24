"""Round 31 hook (src sub-agent; r2_source.R31_B208 = {"B2_08"}), runs AFTER src_b208_r30 (MIRROR_R30 mirror material,
dark tin spots x1.6, chamber reflection env: all untouched = 不许回退). Remove B2_08 from R31_B208 -> exact R30 pixels.

  SPECK_R31  row 6d (B2_08): R30 p1 「镜面上除了深色斑点，还有一些浮在空中的白色或灰色小点，没有说明，会被读成灰尘。改法：
             删掉，或者统一画成深色锡斑」. Ray-pick (pick31.py, step 2 on the dots, f60 / f133) shows the grey / white dots are
             the TinDeposits stain islands themselves (the only first-hit object under them): the R27 stain shader
             (base 0.03, metal 0.2, rough 0.85) catches the chamber-env fill lights + the clean-front alpha ramp, so over
             the dark half of the mirror they render light grey (lighter than the navy behind = floating grey dust).
             Fix (only that object's material): pure matte black stain (base 0.004, metal 0, specular 0, rough 1), so
             every spot is a dark tin spot on bright AND dark parts of the face. Nothing is deleted (stains are the
             BRIEF / label element 「深色斑点 = 镜面上的锡沉积」).
"""
import os

SPECK_R31 = True

_E = os.environ


def _speck(sc):
    import bpy
    dep = bpy.data.objects.get("TinDeposits")
    if dep is None:
        print("[b208r31] no TinDeposits", flush=True)
        return
    n = 0
    for m in dep.data.materials:
        if m is None or not m.use_nodes:
            continue
        for nd in m.node_tree.nodes:
            if nd.type == "BSDF_PRINCIPLED":
                nd.inputs["Base Color"].default_value = (0.004, 0.004, 0.005, 1)
                nd.inputs["Metallic"].default_value = 0.0
                nd.inputs["Roughness"].default_value = 1.0
                for k in ("Specular IOR Level", "Specular"):
                    if k in nd.inputs:
                        nd.inputs[k].default_value = float(_E.get("B31_SPEC", "0.0"))
                n += 1
    print(f"[b208r31] stain shaders -> matte black x{n}", flush=True)


def pre(variant, shot, mod):
    return None


def post(sc, variant, shot):
    if shot == "B2_08" and SPECK_R31:
        _speck(sc)
    return sc
