"""Round-22 overlays for r2_cutaway hero shots (P1, cuth). Loaded after r2_ov_zz21h; entries replace earlier ones per
shot id. Only on shots with a structural R22 change (R22_ROOT_CAUSE row 4).

  B5_01  row 4: the new third segment pupil facet mirror -> condenser G1 lands on G1, named "聚光镜 → 掩模" so the route
         IF -> illuminator -> mask closes; the field-facet label moves left so its leader does not run onto G1.
"""
from r2_ov_common import VIOLET, Layer, anchor, fade

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


@ov("B5_01", no_labels=True)
def illum(img, t, dur, W, H):
    L = Layer(W, H)
    L.tag((0.66, 0.06), ["照明系统（示意）", "中间焦点 IF → 照明系统 → 掩模"], fade(t, 0.3), accent=VIOLET, size=0.034)
    f = anchor("B5_01", t, "ffm", (0.62, 0.25))
    p = anchor("B5_01", t, "pfm", (0.42, 0.72))
    i = anchor("B5_01", t, "if", (0.25, 0.6))
    g = anchor("B5_01", t, "g1", (0.7, 0.6))
    if _in(f, hi=0.85):
        L.label(f, (max(0.04, f[0] - 0.3), max(0.2, min(0.5, f[1] - 0.02))) if f[0] > 0.6 else (f[0] + 0.08, max(0.2, f[1] - 0.12)), ["场分面镜 · 切分光场"], fade(t, 0.3), size=0.034)
    if _in(i, hi=0.85):
        L.label(i, (max(0.04, i[0] - 0.02), max(0.2, i[1] - 0.2)), ["中间焦点 IF"], fade(t, 0.4), accent=VIOLET, size=0.03)
    if _in(p, hi=0.95):
        L.label(p, (min(0.8, p[0] + 0.16), min(0.85, p[1] + 0.04)), ["光瞳分面镜"], fade(t, 0.8), size=0.03)
    if _in(g, hi=0.95):
        L.label(g, (min(0.8, g[0] + 0.12), g[1] - 0.02) if g[1] < 0.65 else (min(0.8, g[0] - 0.02), min(0.88, g[1] + 0.14)), ["聚光镜 → 掩模"], fade(t, 1.0), size=0.03)
    return L.compose(img)


ENABLED = {"B5_01"}
for _sid in list(OVERLAYS):
    if _sid not in ENABLED:
        OVERLAYS.pop(_sid)
        NO_STORYBOARD_LABELS.discard(_sid)
