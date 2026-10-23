"""Round-19 overlays for r2_cutaway (P1, cut agent). Loaded after r2_ov_zz18 (name sorts later); entries replace
earlier ones per shot id.

Only on a shot that also has a structural R19 change (row 2: mirror material + continuous cones):
  B5_01  R18 review: "画内保留一段出射光，指向标注「下一面：光瞳分面镜」。这块标注在 55 / 85 % 帧也要留着" - the
         outgoing facet -> pupil cone stays in frame at 55 / 85 % (beam_r19), but the pupil mirror itself is out of
         frame there (camera); the label then sits where that outgoing cone leaves the frame, pointing along it.
"""
import importlib.util
import os

from r2_ov_common import CYAN, VIOLET, FPS, Layer, anchor, fade

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


def _edge(f, p, m=0.05, hi=0.86):
    """Point where the segment f -> p leaves the frame box [m, 1-m] x [m, hi]."""
    t = 1.0
    for i, (lo_, hi_) in enumerate(((m, 1 - m), (m, hi))):
        d = p[i] - f[i]
        if d < 0 and p[i] < lo_:
            t = min(t, (lo_ - f[i]) / d)
        elif d > 0 and p[i] > hi_:
            t = min(t, (hi_ - f[i]) / d)
    return (f[0] + (p[0] - f[0]) * t, f[1] + (p[1] - f[1]) * t)


@ov("B5_01", no_labels=True)
def illum(img, t, dur, W, H):
    L = Layer(W, H)
    L.tag((0.66, 0.06), ["照明系统（示意）", "中间焦点 IF → 照明系统 → 掩模"], fade(t, 0.3), accent=VIOLET, size=0.034)
    f = anchor("B5_01", t, "ffm", (0.55, 0.12))
    p = anchor("B5_01", t, "pfm", (0.27, 0.8))
    if _in(f, hi=0.85):                        # one hero label, all frames
        L.label(f, (min(0.74, max(0.04, f[0] + 0.1)), max(0.3, min(0.7, f[1] + 0.22))), ["场分面镜 · 切分光场"],
                fade(t, 0.3), size=0.034)
    if _in(p, hi=0.95) and abs(p[0] - f[0]) > 0.12:   # the next mirror the outgoing cone lands on
        L.label(p, (min(0.74, p[0] + 0.12), min(0.62, p[1] - 0.2)), ["下一面：光瞳分面镜"], fade(t, 0.8), size=0.03)
    elif _in(f, hi=0.85):                      # R19: pupil out of frame - label where the outgoing cone exits
        e = _edge(f, p)
        L.label(e, (max(0.04, min(0.6, e[0] - 0.24)), max(0.3, min(0.6, e[1] - 0.3))), ["下一面：光瞳分面镜 ↙"],
                fade(t, 0.8), size=0.03)
    return L.compose(img)
