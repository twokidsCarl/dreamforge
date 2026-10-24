"""Round 30 hook (misc sub-agent; shots in r2_misc.R30_MISC = B4_07 / A0_06 / A2_03). Layered AFTER the R22..R29
hooks, BEFORE beam_hook_r29 (stays LAST). Never touches beams, landing spots, anchors, counters or overlays.

One module-level switch per R30_ROOT_CAUSE row (False -> that shot's exact R29 pixels):
- B407_R30    (row 6c, B4_07) R29 p3 「镜体像一块奶酪轮，底座只有一圈螺栓。镜底加冷却管束和三点柔性支撑，切面做出抛光基底和
  膜层的分界」: three bipod flexure mounts (A-frame blades with notch hinges, foot on the mount ring, pad clamped to the
  blank rim), a cooling-tube bundle (5 tubes + clamps) from a manifold under the blank down through the mount, and a
  cut-face substrate / coating boundary (polished glass-ceramic below, a dark interface line, the coating as a thin
  proud lip on top). misc_r30_b407.py. (R29 sandblast-only body is NOT used.)
- GLOBE_R30   (row 6d, A0_06) R29 p3 「地球像低分辨率贴图外面裹一层雾，弧线是等宽线…换高分辨率地表加夜光城市层；弧线改成从起点到
  落点由粗变细、带亮头的飞线」: NASA Blue Marble NG 4096 surface + NASA Black Marble city lights (textures/earth_r30,
  public domain), the GlobeAtmo fog shell hidden; trunk arcs tapered thick (origin) -> thin (landing) with a bright
  head riding the growth front. 5100-point web, NL ring, counters, camera untouched. misc_r30_globe.py.
- A203WALL_R30 (row 6e, A2_03) R29 p3 「右墙是同一个阀组模块排成格子，一眼看得出复制。打乱模块，混入涡轮泵、波纹管、观察窗、
  气路面板」: misc_r30_a203.py (kit_r27 parts, imported never edited). Beams / NA cone / formula card untouched.
"""

B407_R30 = True
GLOBE_R30 = True
A203WALL_R30 = False   # not built (out of time in the R30 40-min window) -> R29 pixels; see misc SMOKE.md R31 notes


def pre(variant, shot, mod):
    return None


def post(sc, variant, shot):
    try:
        if shot == "B4_07" and B407_R30:
            import misc_r30_b407 as X
            X.apply(sc)
        if shot == "A0_06" and GLOBE_R30:
            import misc_r30_globe as G
            G.apply(sc)
        if shot == "A2_03" and A203WALL_R30:
            import misc_r30_a203 as W
            W.apply(sc)
    except Exception as e:   # never break the build; the log shows it
        import traceback
        traceback.print_exc()
        print(f"[R30 misc] {shot} post FAILED: {e}", flush=True)
    return sc
