"""Round 23 (P1) hook for B3_02 / B5_01 / C_03 (R23_ROOT_CAUSE rows 2 / 3). Owned by the cuth sub-agent.

pre(variant, shot, module) at the start of r2_cutaway.build(), post(sc, variant, shot) at its end (after the R22 hooks).
SHOTS switches each shot here (removed -> R22 pixels; r2_cutaway.R23_HERO does the same).

C_03  (row 3, R22: "第一段 IF 出光向右上偏折"): pre() moves build_cutaway_r2.FFM onto the collector -> IF axis, 1.6 m past
      the IF (sketch_r23b: s = 1.6 -> (-2.95, 0, 2.66)) BEFORE the module builds, so every consumer of B.FFM (field facet
      mirror + its normal, keep-clear spheres, tour legs IF -> FFM -> PFM, landings, bounce lights, reflect_env hero,
      overlay anchor "ffm") follows. PFM stays (FFM' -> PFM -> G1 -> G2 -> mask reads in frame, sketch).
B3_02 (rows 2 + 3): cut_hero_r23_b302.post - front-oblique camera az 55 deg off the dish axis, 24 mm, dolly 4.4 -> 3.6 m
      from the rim centre (D motion), mirror group NOT scaled, laser hidden (it would cross the face), cone rebuilt with a
      0.5 m gap + ramp in front of the rim and kept at full strength through the 85 % frame.
B5_01: not in SHOTS (R22 pixels; the C_03 FFM move is per shot and does not touch B5_01).
"""
import importlib

from mathutils import Vector

SHOTS = {"B3_02", "C_03"}
FFM_C03 = [Vector((-2.95, 0.0, 2.66))]


def pre(variant, shot, mod):
    if shot not in SHOTS:
        return
    if shot == "C_03":
        import build_cutaway_r2 as B
        B.FFM = FFM_C03[0].copy()
        print("[r23h] C_03 FFM ->", tuple(B.FFM))


def post(sc, variant, shot):
    if shot not in SHOTS:
        return sc
    if shot == "B3_02":
        importlib.import_module("cut_hero_r23_b302").post(sc)
    return sc
