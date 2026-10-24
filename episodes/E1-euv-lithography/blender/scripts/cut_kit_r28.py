"""Round 28 hook (kit sub-agent; shots in r2_cutaway.R28_KIT = B3_02 / B8_03 / B8_03M). Layered AFTER the R22..R27 hooks
(B3_02: cut_hero_r26 + cut_r27 CONE_R27 rim25 + ORBIT_R27; B8_03 / B8_03M: cut_hero_r26 R26_HERO). Remove a shot from
R28_KIT -> exact R27 pixels. One module-level switch per R28_ROOT_CAUSE row (False -> that row's R27 pixels):

  SHROUD_R28  row 5b (B3_02): p2 「紫色光锥里面还套着一个实心金属锥罩，两者重叠后整体读成『金属花瓶』…锥罩改成半透明或剖开一半」
              -> the IF-neck gas-flow cone shroud (build_cutaway_r2 IF_CUT shell, kept angles 20..200 deg = the far half
              behind the violet cone, inner face polished steel = the "vase") is cut down to a narrow lower sector whose
              inner face is dark graphite, with light section strips on both sawn edges: the violet cone silhouette reads
              alone against a dark open neck (see cut_kit_r28_b302.py).
  GRID_R28    row 5b (B3_02): 「背景是同一种格栅框重复」 -> kit_r27.named_row (few / big / different parts, proud >= 0.25 m)
              in front of the repeated frame behind the IF (see cut_kit_r28_b302.py).
  SCALE_R28   row 5b (B8_03 + B8_03M): 「晶圆台加一根同比例的小标尺（0–10 mm），或者给晶圆边缘一个参照刻线」 -> a fixed 3D tick
              bar (0..-10 mm, 1 mm = 0.02 m world = the R22 stage scale, major ticks 0 / 5 / 10) behind the wafer's back
              edge + a cyan reference line on the wafer edge parented to the wafer stage, so the stage mark walks
              -2.5 -> -5.5 -> -8.5 mm along the fixed ticks (see cut_kit_r28_b803.py). Ticks only, no text.
"""
SHROUD_R28 = True
GRID_R28 = True
SCALE_R28 = True


def pre(variant, shot, mod):
    return None


def post(sc, variant, shot):
    if shot == "B3_02":
        import cut_kit_r28_b302 as H
        H.post(sc, SHROUD_R28, GRID_R28)
    elif shot in ("B8_03", "B8_03M"):
        import cut_kit_r28_b803 as H
        H.post(sc, shot, SCALE_R28)
    return sc
