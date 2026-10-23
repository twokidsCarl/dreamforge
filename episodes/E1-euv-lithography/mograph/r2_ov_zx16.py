"""Round-16 overlays for r2_cutaway (P1). Loaded after r2_ov_zw15 (name sorts later); entries replace R15's.
Label work = deletions / merges only.

C_03 (R15: "the top-right block and the '反射式掩模' callout say the same thing"): the mask station keeps only the
  top-right 2-line block; the duplicate leader is deleted.
B5_01 (R15: "no next station"): the pupil-facet leader is merged with the onward route ("光瞳分面镜 → 掩模") so the
  newly lit outgoing leg (r2_cutaway R16) names where the light goes next; no new label added.
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
        tx = p[0] - 0.24 if p[0] > 0.55 else p[0] + 0.12
        L.label(p, (max(0.04, min(0.6, tx)), max(0.3, min(0.7, p[1] + 0.14))), lines, a, accent=CYAN)
    a = fade(t, 0.7 * dur + 0.3, 1e9, 0.35)
    if a > 0:
        L.tag((0.6, 0.06), ["带电路图形的反射式掩模", "约 5.4° 斜射进来 → 反射出去（角度放大示意）"], a,
              accent=VIOLET, size=0.032)
    return L.compose(img)


@ov("B5_01", no_labels=True)
def illum(img, t, dur, W, H):
    L = Layer(W, H)
    L.tag((0.72, 0.06), ["照明系统（示意）"], fade(t, 0.3), accent=VIOLET, size=0.038)
    f = anchor("B5_01", t, "ffm", (0.55, 0.12))
    p = anchor("B5_01", t, "pfm", (0.27, 0.8))
    if 0.03 < f[0] < 0.97 and 0.03 < f[1] < 0.85:
        L.label(f, (min(0.74, max(0.04, f[0] + 0.1)), max(0.3, min(0.7, f[1] + 0.22))), ["场分面镜 · 切分光场"],
                fade(t, 1.2), size=0.034)
    if 0.03 < p[0] < 0.97 and 0.03 < p[1] < 0.95:          # R16: the pupil mirror sits low in the opening frames
        L.label(p, (min(0.74, p[0] + 0.16), min(0.62, p[1] - 0.2)), ["光瞳分面镜 → 掩模"], fade(t, 0.8), size=0.034)
    return L.compose(img)
