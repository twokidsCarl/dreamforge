"""Round 22 (P1) hook for B3_02 / B5_01 / C_03 (R22_ROOT_CAUSE rows 4 / 5). Owned by the cuth sub-agent.

pre(variant, shot, module) before the build, post(sc, variant, shot) after it. SHOTS switches each shot (removed -> R21 pixels).
B3_02 -> cut_hero_r22_b302.post ; B5_01 / C_03 -> cut_hero_r22_illum.post_b501 / post_c03 (+ kit_r22 background).
"""
import importlib

SHOTS = {"B3_02", "B5_01"}   # C_03: not built in R22 (needs pre-build FFM move) -> R21 pixels


def pre(variant, shot, mod):
    pass


def post(sc, variant, shot):
    if shot not in SHOTS:
        return sc
    if shot == "B3_02":
        importlib.import_module("cut_hero_r22_b302").post(sc)
    elif shot == "B5_01":
        importlib.import_module("cut_hero_r22_illum").post_b501(sc)
    elif shot == "C_03":
        importlib.import_module("cut_hero_r22_illum").post_c03(sc)
    return sc
