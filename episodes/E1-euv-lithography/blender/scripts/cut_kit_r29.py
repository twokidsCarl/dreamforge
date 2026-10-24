"""Round 29 hook (kit sub-agent; r2_cutaway.R29_KIT = {"B8_03", "B8_03M"}). Layered AFTER the R22..R28 hooks (cut_hero_r26
R26_HERO wafer Si + cut_kit_r28 SCALE_R28). Remove a shot from R29_KIT -> exact R28 pixels. One switch per row-4 part
(R29_ROOT_CAUSE row 4, p2 B8_03 「晶圆旁加一条同款青色短标尺（0–10 mm）和指针，与画中画同步移动…场格改为长方形半场，数量对上 188」):

  SCALE_R29  row 4 (B8_03): the R28 thin white 3D tick bar (「标尺太小没被看见」) is replaced by a readable cyan 0-10 mm ruler
             on a dark carrier plate fixed behind the wafer's back edge, turned to face the camera, labels 0 / 5 / 10 mm +
             「晶圆台」 (repo fonts), and a cyan pointer parented to the wafer stage that walks -2.5 -> -5.5 -> -8.5 mm
             (opposite to the PIP reticle pointer, in sync with the read-out). See cut_kit_r29_b803.py.
  GRID_R29   row 4 (B8_03 + B8_03M): wafer die map re-laid as 188 landscape half-fields 26 x 16.5 (exposed stripe logic
             unchanged). See cut_kit_r29_b803.py.
"""
SCALE_R29 = False   # 8-spp Q4 no (ruler squeezed under the PIP, labels 11-14 px) -> R28 bar kept; see SMOKE.md
GRID_R29 = True


def pre(variant, shot, mod):
    return None


def post(sc, variant, shot):
    if shot in ("B8_03", "B8_03M"):
        import cut_kit_r29_b803 as H
        H.post(sc, shot, SCALE_R29, GRID_R29)
    return sc
