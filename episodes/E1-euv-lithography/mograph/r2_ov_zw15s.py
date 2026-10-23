"""Round-15 overlays for the source-chamber shots (P1). Sorts after r2_ov_zw15.py, so entries here replace earlier
ones for the same shot. Only shots of r2_source: A0_01, B1_10, B1_15.

R15 root cause #3 (R14: "pancake fills the frame, no scale"): a metrology-cyan dimension line across the real sheet
(rim anchors pk_top / pk_bot written by r2_source._rim_markers), "300 µm" only once the sheet is full size (no
fact-like mid value), matching the B1_10 magnifier.
R15 root cause #5 (B1_15: "4 lines of text in 1.5 s"): one label only, 「收集镜」."""
import importlib.util
import math
import os

from r2_ov_common import CYAN, FPS, Layer, anchor, ease, fade

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


def _mod(module):
    spec = importlib.util.spec_from_file_location(module + "_r15sbase", os.path.join(_HERE, module + ".py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


_src = _mod("r2_ov_source")
_zr8 = _mod("r2_ov_zr8")


def _dimension(L, sid, t, a, text):
    """Dimension line parallel to the sheet's top-bottom diameter, offset to its right, with extension lines."""
    top = anchor(sid, t, "pk_top", None)
    bot = anchor(sid, t, "pk_bot", None)
    if a <= 0 or top is None or bot is None:
        return
    (x0, y0), (x1, y1) = L.P(top), L.P(bot)
    dx, dy = x1 - x0, y1 - y0
    ln = math.hypot(dx, dy)
    if ln < 10:
        return
    nx, ny = -dy / ln, dx / ln                     # perpendicular; pick the side to the right on screen
    if nx < 0:
        nx, ny = -nx, -ny
    off = 0.42 * ln + 0.03 * L.W                   # clear of the sheet's own (foreshortened) width
    p0 = (x0 + nx * off, y0 + ny * off)
    p1 = (x1 + nx * off, y1 + ny * off)
    col = (*CYAN, int(255 * a))
    w = max(2, L.s(0.003))
    L.d.line([p0, p1], fill=col, width=w)
    for (xa, ya), (xb, yb) in (((x0, y0), p0), ((x1, y1), p1)):      # extension lines from the rim
        L.d.line([(xa + nx * 0.015 * L.W, ya + ny * 0.015 * L.W), (xb + nx * 0.012 * L.W, yb + ny * 0.012 * L.W)],
                 fill=(*CYAN, int(170 * a)), width=max(1, w // 2))
    for (px, py), sgn in ((p0, 1), (p1, -1)):                        # arrow heads pointing outwards
        ux, uy = -dx / ln * sgn, -dy / ln * sgn
        hl = L.s(0.018)
        L.d.polygon([(px, py), (px - ux * hl + nx * hl * 0.45, py - uy * hl + ny * hl * 0.45),
                     (px - ux * hl - nx * hl * 0.45, py - uy * hl - ny * hl * 0.45)], fill=col)
    if text:
        mx, my = (p0[0] + p1[0]) / 2 + nx * 0.012 * L.W, (p0[1] + p1[1]) / 2
        L.tag(((mx + 0.006 * L.W) / L.W, (my - L.s(0.04) * 0.6) / L.H), [text], a, accent=CYAN, size=0.04)


@ov("B1_10")
def prepulse(img, t, dur, W, H):
    img = _zr8.OVERLAYS["B1_10"](img, t, dur, W, H)      # magnifier 25 µm -> 300 µm (R8: no caption)
    p = ease((t - 1.3) / 2.6)                            # same growth clock as the magnifier
    L = Layer(W, H)
    _dimension(L, "B1_10", t, fade(t, 1.6), "300 µm" if p > 0.97 else None)
    return L.compose(img)


@ov("A0_01")
def cold(img, t, dur, W, H):
    img = _src.ov_A0_01(img, t, dur, W, H)
    f = t * FPS + 1
    a = min(ease((f - 128) / 8), ease((165 - f) / 4))    # sheet at full size until the plasma (boom 166)
    if a > 0:
        L = Layer(W, H)
        _dimension(L, "A0_01", t, a, "薄饼 300 µm")
        img = L.compose(img)
    return img


@ov("B1_15")
def contrast(img, t, dur, W, H):
    L = Layer(W, H)
    c = anchor("B1_15", t, "coll", (0.2, 0.55))
    L.label(c, (0.06, 0.3), ["收集镜"], fade(t, 0.3), accent=CYAN, size=0.044)
    return L.compose(img)
