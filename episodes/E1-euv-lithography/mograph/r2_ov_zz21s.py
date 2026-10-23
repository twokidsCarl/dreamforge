"""Round-21 overlay for the src group (replaces r2_ov_zz20s's B1_15 entry by sort order).

R21 root cause #1 (R20 review B1_15 #2: 「1.5 s 无旁白，三条标签读不完。只留『收集镜』一条」): when B1_15 renders with the
R21 asset (anchor "r21" present) only the 「收集镜」 label is drawn - no 「→ 中间焦点」 (the violet IF cone replaces
the cyan axis) and no 「镜中等离子体倒影」. Without the "r21" anchor (shot reverted to R20) this draws exactly what
r2_ov_zz20s drew."""
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
    if anchor("B1_15", t, "r21", None) is not None:
        return L.compose(img)
    p = anchor("B1_15", t, "axis_if", None)          # R20 path (shot reverted): identical to r2_ov_zz20s
    if p is not None:
        tag = (min(0.86, max(0.62, p[0] + 0.06)), min(0.74, max(0.5, p[1] + 0.1)))
        L.label(p, tag, ["→ 中间焦点"], fade(t, 0.0, d=0.3), accent=CYAN, size=0.036)
    q = anchor("B1_15", t, "refl", None)
    if q is not None:
        L.label(q, (max(0.08, q[0] - 0.2), min(0.74, q[1] + 0.2)), ["镜中等离子体倒影"], fade(t, 0.0, d=0.3),
                accent=CYAN, size=0.032)
    return L.compose(img)
