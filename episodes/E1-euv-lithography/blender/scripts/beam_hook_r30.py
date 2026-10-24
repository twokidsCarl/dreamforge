"""Round 30 hook (MAIN process, R30_ROOT_CAUSE row 2 - beam taper + on-screen floor as one shared row).

pre() ONLY: wraps beam_r29.cone (beam_r30.install) so that beam_hook_r29 - which stays LAST and stays the only
converter - builds every leg of the shot with
  TAPER_R30: the named focus ends below (IF / PFM / mask landing / wafer / slit) at <= 1/4.5 of the wide end (slit ends
      = a thin ellipse), C_03 entry -> FFM re-opened toward the FFM (it narrowed the wrong way);
  FLOOR_R30: mid-leg width >= 6 px and every end >= 3 px on screen (960x540) on the three job frames.
Shot sets: r2_cutaway / r2_source / r2_misc `R30_BEAM` (the hook-list gate also makes beam_hook_r29 convert those shots).
Remove a shot from its R30_BEAM set -> R29 legs (if it was in R29_BEAM).
"""
import beam_r30 as B30

TAPER_R30 = True
FLOOR_R30 = True

FOCUS = {
    # B5_01 p2 「IF 是点光源，出来以后应该从细到粗展开成锥形；从场分面镜到光瞳镜那一段要再收窄」
    "B5_01": {"IllumPathR24Leg0": {"a": True}, "IllumPathR24Leg1": {"b": True}},
    # C_03 p2 f101 「改成从左向 IF 会聚的锥，锥尖正好插进 IF 孔里」; IF -> entry -> FFM opens toward the FFM (was
    # narrowing); f343 「入射和反射都改成软边的窄锥，反射锥要比入射锥更淡」
    "C_03": {"C03R28SrcLeg1": {"a": True}, "C03R28InLeg0": {"ra": 0.07, "rb": 0.17}, "C03R30Fp": {"b": True},
             "C03R28IllLeg0": {"b": True}, "C03R28IllLeg1": {"a": True}},
    # B8_03 p2 「狭缝光现在是一团雾。改成上宽下窄、落成一条清楚亮边狭缝的光束」
    # slit illumination = a fan: the long axis stays ~ the slit length, the thin axis converges onto the slit line
    "B8_03": {"ScanBeamR24Leg0": {"slit": "b", "ra": (0.30, 0.17), "rb": (0.124, 0.012), "slit_dir": (1, 0, 0)}},
    # B8_17 p3 「改成扁长的狭缝光带，场是长方形的半场」
    "B8_17": {"B817R24Leg0": {"slit": "b", "ra": (0.30, 0.27), "rb": (0.10, 0.006), "slit_dir": (1, 0, 0)}},
    # B7_06 p2 「最后一段（M6 → 穿孔 → 晶圆）一定要画成从整个 M6 口径收拢到一点的会聚锥」 (M6 aperture set by cut_scene_r30)
    "B7_06": {"PO27BeamLeg2": {"b": True, "ra": 0.40}},
    # A0_10 / B3_02 / B1_15 / A2_03: ratios already >= 4.5 (scan30) - floor only
}
GAIN = {
    "C_03": {"C03R28IllLeg1": 0.7},    # reflected cone fainter than the incident one (p2 f343)
}


def pre(variant, shot, mod):
    if not (TAPER_R30 or FLOOR_R30):
        return
    B30.install(shot, FOCUS.get(shot, {}), taper=TAPER_R30, floor=FLOOR_R30, gain=GAIN.get(shot))


def post(sc, variant, shot):
    return sc
