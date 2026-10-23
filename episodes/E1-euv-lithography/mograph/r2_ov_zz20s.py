"""Round-20 overlay for B1_15 (src; replaces r2_ov_zz18s's B1_15 entry by sort order).

R20 root cause #3 (R19 review B1_15 #2: 「现在那条没标注的青色短虚线要么标『→ 中间焦点』，要么删掉」): the dashed cyan
optical axis (b115_r20) now runs plasma -> out of frame toward the IF; it gets the tag 「→ 中间焦点」 at the 3D anchor
"axis_if" on the axis. The 「收集镜」 label is unchanged from r2_ov_zz18s. When B1_15 renders with R19 assets (no
"axis_if" anchor), only the R18/R19 label is drawn - identical to r2_ov_zz18s."""
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
    p = anchor("B1_15", t, "axis_if", None)
    if p is not None:
        tag = (min(0.86, max(0.62, p[0] + 0.06)), min(0.74, max(0.5, p[1] + 0.1)))
        L.label(p, tag, ["→ 中间焦点"], fade(t, 0.0, d=0.3), accent=CYAN, size=0.036)
    q = anchor("B1_15", t, "refl", None)
    if q is not None:            # the small plasma image on the far side of the bowl (on the axis line, by geometry)
        L.label(q, (max(0.08, q[0] - 0.2), min(0.74, q[1] + 0.2)), ["镜中等离子体倒影"], fade(t, 0.0, d=0.3),
                accent=CYAN, size=0.032)
    return L.compose(img)
