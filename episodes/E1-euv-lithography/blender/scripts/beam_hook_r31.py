"""Round 31 hook (MAIN process, R31_ROOT_CAUSE rows 3a / 3d / 6e - screen-space taper as one shared row).

pre() ONLY: beam_r31.install wraps beam_r29.cone (replacing the beam_r30 wrapper for the shot; the shot's R30 FOCUS /
GAIN entries are kept and the R31 entries below override them leg by leg) so that beam_hook_r29 - LAST, the only
converter - builds the legs with
  CONE_R31: the named focus ends below reach <= 1/4.5 of the wide end ON SCREEN on the mid job frame (beam_r31.SCREEN)
      - B5_01 IF -> FFM opens from the IF exit to the array width, FFM -> PFM closes onto the PFM;
        C_03 incident / reflected legs meet in one narrow point on the mask face; A2_03 right mirror -> top mirror.
Shot sets: r2_cutaway / r2_misc `R31_BEAM` (the hook-list gate also makes beam_hook_r29 convert those shots).
Remove a shot from its R31_BEAM set -> R30 legs.
"""
import beam_r31 as B31

CONE_R31 = True

FOCUS = {
    # B5_01 p2 「IF 后的光改成从一点发散的锥，落到场分面镜上的光斑等于阵列宽度」
    "B5_01": {"IllumPathR24Leg0": {"ra": 0.012, "rb": 0.42, "screen": "a"},
              "IllumPathR24Leg1": {"ra": 0.42, "rb": 0.05, "screen": "b"}},
    # C_03 p2 「入射光做成收向弧形照明带的扁锥，反射光从照明带发散出去，两束只在掩模面上相接，不在空中交叉」
    "C_03": {"C03R28IllLeg0": {"b": True, "screen": "b", "px": 7.0}, "C03R28IllLeg1": {"a": True, "screen": "a", "px": 6.0}},
    # B1_15 p1 「紫色光锥的起点比镜口窄…让光锥底面贴住整个镜口边缘，再收到 IF」 (rim radius ~0.78, CollRimR21 pick)
    "B1_15": {"B115ExitR27Leg0": {"ra": 0.78}},
    # B7_06 p2 「M5→M6 发散、M6→晶圆会聚到一点」 (cut_scene_r31 stops; overrides the R30 Leg2 ra 0.40)
    "B7_06": {"PO27BeamLeg1": {"ra": 0.045, "rb": 0.36}, "PO27BeamLeg2": {"ra": 0.36, "rb": 0.008}},
    # A2_03 p3 「从右镜到顶镜那段入射光是等宽实心光柱。改成从镜面收放的软边锥」
    "A2_03": {"A203R24Leg0": {"ra": 0.02, "rb": 0.13, "screen": "a"}},
}

# B1_15: the rim-wide cone lies over the whole mirror face -> dimmer (32 spp at 1.1: mirror-area 90/10 2.86 < 4, violet
# haze hides the reflection)
STRENGTH = {"B1_15": 0.6}


def pre(variant, shot, mod):
    if not CONE_R31:
        return
    import beam_hook_r30 as H30
    if shot in STRENGTH:
        import beam_hook_r29 as H29
        H29.STRENGTH[shot] = STRENGTH[shot]
    focus = dict(H30.FOCUS.get(shot, {}))
    focus.update(FOCUS.get(shot, {}))
    B31.install(shot, focus, gain=H30.GAIN.get(shot))


def post(sc, variant, shot):
    return sc
