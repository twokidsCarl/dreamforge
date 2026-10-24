"""Round 29 hook (misc sub-agent; shots in r2_misc.R29_MISC = B4_07 / B6_12). Layered AFTER the R22..R28 hooks.

R29_ROOT_CAUSE row 6 (主角件 / 材质: B4_07 hero part, B6_12 background context). One switch per shot-row:
- B407_R29   (row 6, B4_07)  R28 p3 「镜体和镜座材质偏平：镜体是匀灰哑光块，镜座只有一圈螺栓，背景是空暗场。建议镜体切面做
  喷砂陶瓷质感（微糙 + 边缘倒角高光），镜座加 3 个柔性铰链和冷却管，背景虚化出一角真空腔壁」:
  blank sides + cut faces -> sand-blasted glass-ceramic (light warm grey, fine micro-rough grain, shader bevel edge
  highlight; the emissive coating band on the cut face is kept), 3 blade flexure hinges + a copper cooling line with
  fittings on the mount, a defocused vacuum-chamber wall corner behind (misc_r29_b407.py). Beams / landing /
  magnifier anchors / Mo-Si inset untouched.
- B612BG_R29 (row 6, B6_12)  R28 p3 「背景是纯黑，看不出『装在机器里』。建议远处虚化出掩模台导轨、观察窗和气路面板，补一层景深」:
  defocused machine context far behind the chuck (reticle-stage rails + carriage, a viewport, a gas panel; kit_r27
  parts), dim, invisible to glossy rays so nothing new reflects in the mask face / pellicle (misc_r29_b612.py).
  The R28 FILM / FACE / HOSE rows stay ON underneath and are not touched.
"""

B407_R29 = True
B612BG_R29 = True


def pre(variant, shot, mod):
    return None


def post(sc, variant, shot):
    if shot == "B4_07" and B407_R29:
        import misc_r29_b407 as X
        X.apply(sc)
    if shot == "B6_12" and B612BG_R29:
        import misc_r29_b612 as Y
        Y.apply(sc)
    return sc
