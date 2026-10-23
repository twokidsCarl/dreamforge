"""Round-20 overlays for r2_cutaway (P1, cut agent). Loaded after r2_ov_zz19* (name sorts later); entries replace
earlier ones per shot id. Only on shots that also have a structural R20 change (R20_ROOT_CAUSE rows 1 / 2).

  B5_01  row 1 (R19: "「下一面：光瞳分面镜 ↙」的箭头指向入射光的方向，外行会读成光原路返回"): the pupil facet mirror is
         now in frame in every frame; the "下一面" arrow runs ALONG the outgoing beamlets (field facet -> pupil facet),
         offset beside them, never along the incoming IF cone; the IF tip gets its own small tag.
  B3_02  row 2 (R19: "「中间焦点 IF」标注在后两帧消失了，应该保留到锥尖"): the IF tag sits at the cone tip from the start
         and in every frame (the R20 camera keeps the IF in frame); the R18 hole / first-focus steps are kept.
"""
import importlib.util
import math
import os

from r2_ov_common import CYAN, VIOLET, Layer, anchor, fade

OVERLAYS = {}
NO_STORYBOARD_LABELS = set()
_HERE = os.path.dirname(os.path.abspath(__file__))


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
        L.label(f, (min(0.8, f[0] + 0.12), max(0.3, min(0.62, f[1] + 0.25))), ["场分面镜 · 切分光场"],
                fade(t, 0.3), size=0.034)
    if _in(i, hi=0.85):                        # where the incoming cone opens from
        L.label(i, (max(0.04, i[0] - 0.02), max(0.2, i[1] - 0.2)), ["中间焦点 IF"], fade(t, 0.4), accent=VIOLET,
                size=0.03)
    if _in(p, hi=0.95) and _in(f, hi=0.85):
        # arrow ALONG the outgoing beamlets (facet -> pupil), offset to their right side so it never sits on a beam
        dx, dy = p[0] - f[0], (p[1] - f[1]) * H / W
        ln = math.hypot(dx, dy) or 1.0
        nx, ny = dy / ln, -dx / ln              # perpendicular (screen space)
        if nx < 0:
            nx, ny = -nx, -ny
        off = 0.045
        a0 = (f[0] + 0.3 * (p[0] - f[0]) + nx * off, f[1] + 0.3 * (p[1] - f[1]) + ny * off * W / H)
        a1 = (f[0] + 0.78 * (p[0] - f[0]) + nx * off, f[1] + 0.78 * (p[1] - f[1]) + ny * off * W / H)
        al = fade(t, 0.8)
        L.arrow(a0, a1, al, color=CYAN, width=0.0035, head=0.02)
        L.label(p, (min(0.8, p[0] + 0.16), min(0.8, p[1] + 0.02)), ["下一面：光瞳分面镜"], al, size=0.03)
    return L.compose(img)


def _mod(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(_HERE, name + ".py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


@ov("B3_02")
def collector(img, t, dur, W, H):
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
    if al > 0 and _in(p):                     # IF tag at the cone tip in every frame
        L.label(p, (max(0.6, min(0.8, p[0] - 0.08)), max(0.2, p[1] - 0.2)), ["中间焦点 IF"], al, accent=VIOLET,
                size=0.034)
    return L.compose(img)


# HARD-STOP REVERT (cut agent): r2_cutaway.R20_SHOTS is empty (R19 pixels), so these overlays are switched off too.
# To re-enable a shot: add it to r2_cutaway.R20_SHOTS and list it here.
ENABLED = {"B5_01", "B3_02"}
for _sid in list(OVERLAYS):
    if _sid not in ENABLED:
        OVERLAYS.pop(_sid)
        NO_STORYBOARD_LABELS.discard(_sid)
