"""Round-21 overlays for r2_cutaway hero shots (P1, cut-hero agent). Loaded after r2_ov_zz20* (name sorts later); entries
replace earlier ones per shot id. Only on shots that also have a structural R21 change (R21_ROOT_CAUSE row 4).

  B5_01  row 4 (R20: "两根细光柱，旁边还平行着一根青色箭头，读起来像三条路…去掉青色箭头"): the cyan arrow along the outgoing
         light is gone - the one violet cone is the only path; the pupil facet mirror keeps a plain label at its landing.
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


@ov("B5_01", no_labels=True)
def illum(img, t, dur, W, H):
    L = Layer(W, H)
    L.tag((0.66, 0.06), ["照明系统（示意）", "中间焦点 IF → 照明系统 → 掩模"], fade(t, 0.3), accent=VIOLET, size=0.034)
    f = anchor("B5_01", t, "ffm", (0.62, 0.25))
    p = anchor("B5_01", t, "pfm", (0.42, 0.72))
    i = anchor("B5_01", t, "if", (0.25, 0.6))
    if _in(f, hi=0.85):
        L.label(f, (min(0.8, f[0] + 0.1), max(0.3, min(0.62, f[1] + 0.3))), ["场分面镜 · 切分光场"], fade(t, 0.3), size=0.034)
    if _in(i, hi=0.85):
        L.label(i, (max(0.04, i[0] - 0.02), max(0.2, i[1] - 0.2)), ["中间焦点 IF"], fade(t, 0.4), accent=VIOLET, size=0.03)
    if _in(p, hi=0.95):
        L.label(p, (min(0.8, p[0] + 0.16), min(0.85, p[1] + 0.04)), ["光瞳分面镜"], fade(t, 0.8), size=0.03)
    return L.compose(img)


@ov("B3_02")
def collector(img, t, dur, W, H):
    """B3_02 row 4: R20 overlay (hole / first focus / IF tag at the cone tip) kept; the IF tag sits above-left of the cone tip, under the title panel, so
    it never lands inside the title panel or the hole label of the closer R21 framing."""
    L = Layer(W, H)
    steps = [("hole", 0.0, 0.36, ["中心孔", "CO₂ 激光从这里穿过"], CYAN, (0.45, 0.45)),
             ("plasma", 0.36, 0.62, ["第一焦点", "锡滴在这里被打成等离子体"], CYAN, (0.7, 0.4))]
    for name, f0, f1, lines, acc, dflt in steps:
        al = fade(t, max(0.3, f0 * dur + 0.2), f1 * dur - 0.1, 0.3)
        if al <= 0:
            continue
        p = anchor("B3_02", t, name, dflt)
        if not _in(p):
            continue
        tx = p[0] - 0.26 if p[0] > 0.55 else p[0] + 0.1
        L.label(p, (max(0.04, min(0.62, tx)), max(0.3, min(0.7, p[1] + 0.2))), lines, al, accent=acc, size=0.038)
    p = anchor("B3_02", t, "if", (1.2, 0.5))
    al = fade(t, 0.3, None, 0.3)
    if al > 0 and _in(p):
        L.label(p, (max(0.55, min(0.78, p[0] - 0.08)), max(0.33, p[1] - 0.13)), ["中间焦点 IF"], al, accent=VIOLET, size=0.034)
    return L.compose(img)


ENABLED = {"B5_01"}   # B3_02 reverted to R20 (zz20 overlay applies)
for _sid in list(OVERLAYS):
    if _sid not in ENABLED:
        OVERLAYS.pop(_sid)
        NO_STORYBOARD_LABELS.discard(_sid)
