"""Round-18 overlay for the source-chamber shot B1_15 (replaces r2_ov_zw15s's B1_15 entry by sort order).

R17 review B1_15: "第 1 帧「收集镜」标签被左边缘切掉了，挪到画内。" R18: the single 「收集镜」 label keeps its leader
to the mirror face anchor, but the tag sits inside the frame, upper right (labels top-right, <= 3 lines; it was
drawn right-aligned against the left edge before)."""
from r2_ov_common import CYAN, Layer, anchor, fade

OVERLAYS = {}
NO_STORYBOARD_LABELS = set()


def ov(sid):
    def wrap(fn):
        OVERLAYS[sid] = fn
        return fn
    return wrap


@ov("B1_15")
def contrast(img, t, dur, W, H):
    L = Layer(W, H)
    c = anchor("B1_15", t, "coll", (0.53, 0.27))
    L.label(c, (max(0.66, c[0] + 0.1), 0.12), ["收集镜"], fade(t, 0.0, d=0.3), accent=CYAN, size=0.044)
    return L.compose(img)
