"""Round-16 overlay for A0_03 (root cause 5: quantity not visible). Loads after r2_ov_zs10_a003 / zw15 (name sorts
last), so it replaces earlier A0_03 overlays.

Plate r2_a003_r16.png (high elevated wide view: ~250 crates in blocks, ULD container rows, freighter, trucks); the
camera starts on the crate blocks and pulls back to the whole apron (r2_plates crates keys). Each counted object gets
ONE short leader while its step is on. The R15 top-right chain repeated the same numbers (review: information shown
twice), so it is deleted."""
from r2_ov_common import Layer, ease, fade

OVERLAYS = {}
NO_STORYBOARD_LABELS = {"A0_03"}

CARD_W, CARD_H = 10.0 * 1672 / 941, 10.0
CAM0, CAM1 = (-2.2, -1.2, 10.6), (0.0, 0.0, 17.4)      # r2_plates crates keys (x, y, ortho width), frame 1 -> n


def _pix(x, y):
    return ((x / 1672 - 0.5) * CARD_W, (0.5 - y / 941) * CARD_H)


def _screen(t, dur, px, py):
    u = ease(t / max(dur, 1e-6))
    cx, cy, w = (a + (b - a) * u for a, b in zip(CAM0, CAM1))
    return (0.5 + (px - cx) / w, 0.5 - (py - cy) / (w * 9 / 16))


STEPS = [(0.5, 3.6, (520, 560), (0.10, -0.20), ["250+ 箱", "白色铝框板条箱"]),
         (3.3, 6.6, (1120, 400), (0.02, 0.17), ["43 个集装箱", "航空集装箱 · 货网托盘"]),
         (6.3, 8.2, (960, 190), (-0.12, -0.08), ["几架货机"]),
         (7.9, 99, (1500, 320), (-0.10, 0.16), ["20 辆卡车"])]


def crates(img, t, dur, W, H):
    L = Layer(W, H)
    for t0, t1, pix, off, lines in STEPS:
        a = fade(t, t0, t1, 0.4)
        if a <= 0:
            continue
        p = _screen(t, dur, *_pix(*pix))
        if not (0.03 < p[0] < 0.97 and 0.03 < p[1] < 0.97):
            continue
        L.label(p, (p[0] + off[0], p[1] + off[1]), lines, a, size=0.05)
    return L.compose(img)


OVERLAYS["A0_03"] = crates
