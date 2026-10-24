"""Round-23 overlays for r2_cutaway hero shots (P1, cuth). Loaded after r2_ov_zz22h; entries replace earlier ones per
shot id. Only on shots with a structural R23 change (R23_ROOT_CAUSE rows 2 / 3).

  B3_02  rows 2 + 3: front-oblique camera, CO2 laser hidden (it crossed the dish face) -> the hole tag no longer says the
         laser "passes here" over an empty hole; the IF tag is anchored on the cone tip and sits BELOW
         it, clear of the title panel (R22 review: 标题框盖住「中间焦点 IF」标签).
  C_03   row 3: FFM moved onto the collector -> IF axis (pre()); at the 55 % frame the FFM now sits just above-right of
         the PFM, so the zx16 FFM tag (below-right of its anchor) landed on the zz18 PFM tag -> same texts / timing
         (zx16 tour + zz18 PFM tag), only the FFM tag moved ABOVE its mirror.
"""
from r2_ov_common import CYAN, VIOLET, Layer, anchor, fade

OVERLAYS = {}
NO_STORYBOARD_LABELS = set()


def ov(sid, no_labels=False):
    def wrap(fn):
        OVERLAYS[sid] = fn
        if no_labels:
            NO_STORYBOARD_LABELS.add(sid)
        return fn
    return wrap


def _in(p, lo=0.03, hi=0.9):
    return lo < p[0] < 0.97 and lo < p[1] < hi


@ov("B3_02")
def collector(img, t, dur, W, H):
    L = Layer(W, H)
    steps = [("hole", 0.0, 0.36, ["中心孔", "CO₂ 激光从镜背入口进入"], CYAN, (0.2, 0.5)),
             ("plasma", 0.36, 0.62, ["第一焦点", "锡滴在这里被打成等离子体"], CYAN, (0.4, 0.5))]
    for name, f0, f1, lines, acc, dflt in steps:
        al = fade(t, max(0.3, f0 * dur + 0.2), f1 * dur - 0.1, 0.3)
        if al <= 0:
            continue
        p = anchor("B3_02", t, name, dflt)
        if not _in(p):
            continue
        L.label(p, (max(0.04, min(0.62, p[0] + 0.1)), max(0.3, min(0.72, p[1] + 0.22))), lines, al, accent=acc, size=0.038)
    al = fade(t, 0.3, None, 0.3)
    p = anchor("B3_02", t, "if", (0.88, 0.47))
    if al > 0 and _in(p, hi=0.95):            # IF tag BELOW the cone tip, clear of the title panel (R22 review issue 2)
        L.label(p, (max(0.5, min(0.74, p[0] - 0.16)), min(0.8, p[1] + 0.2)), ["中间焦点 IF"], al, accent=VIOLET, size=0.034)
    return L.compose(img)


@ov("C_03", no_labels=True)
def tour(img, t, dur, W, H):
    L = Layer(W, H)
    stations = [("coll", 0.0, 0.2, ["收集镜", "把光聚向中间焦点"]),
                ("if", 0.2, 0.42, ["中间焦点 IF"]),
                ("ffm", 0.42, 0.7, ["照明系统 · 场分面镜"])]
    for name, f0, f1, lines in stations:
        a = fade(t, f0 * dur + 0.3, f1 * dur - 0.15, 0.35)
        if a <= 0:
            continue
        p = anchor("C_03", t, name, (0.5, 0.5))
        if not (0.03 < p[0] < 0.97 and 0.03 < p[1] < 0.85):
            continue
        if name == "ffm":                     # above-right of the mirror (the PFM tag owns the space below)
            L.label(p, (max(0.04, min(0.6, p[0] + 0.12)), max(0.12, p[1] - 0.28)), lines, a, accent=CYAN)
            continue
        tx = p[0] - 0.24 if p[0] > 0.55 else p[0] + 0.12
        L.label(p, (max(0.04, min(0.6, tx)), max(0.3, min(0.7, p[1] + 0.14))), lines, a, accent=CYAN)
    a = fade(t, 0.7 * dur + 0.3, 1e9, 0.35)
    if a > 0:
        L.tag((0.6, 0.06), ["带电路图形的反射式掩模", "约 5.4° 斜射进来 → 反射出去（角度放大示意）"], a,
              accent=VIOLET, size=0.032)
    a = fade(t, 0.5 * dur + 0.3, 0.7 * dur - 0.15, 0.35)
    p = anchor("C_03", t, "pfm", (1.2, 0.5))
    if a > 0 and _in(p, hi=0.85):
        # below-left of the PFM (right of it is now the FFM face)
        L.label(p, (max(0.04, p[0] - 0.27), max(0.3, min(0.86, p[1] + 0.07))), ["光瞳分面镜"], a, accent=CYAN, size=0.032)
    return L.compose(img)


ENABLED = {"C_03"}   # B3_02 reverted to R22 (main smoke: agent-written risk)
for _sid in list(OVERLAYS):
    if _sid not in ENABLED:
        OVERLAYS.pop(_sid)
        NO_STORYBOARD_LABELS.discard(_sid)
