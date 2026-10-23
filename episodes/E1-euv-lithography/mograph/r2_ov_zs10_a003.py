"""Round-10 overlay for A0_03 (R9 review: the "43 containers" link had no object in the plate; leaders crossed the
jet and crate faces). Loads after r2_ov_zr* (name sorts last), so this entry replaces earlier A0_03 overlays.

Plate r2_a003_r10.png (image2 edit, R10) adds a row of aluminium ULD air-cargo containers on dollies and net-wrapped
pallets between the crate row and the freighter. Each counted object gets ONE short straight leader with a dot
anchor while its step is on; a growing chain readout top right stacks the steps (<= 2 label groups per frame)."""
from r2_ov_common import Layer, ease, fade

OVERLAYS = {}
NO_STORYBOARD_LABELS = {"A0_03"}

CARD_W, CARD_H = 10.0 * 1672 / 941, 10.0          # r2_plates: card height 10, plate aspect 1672 x 941
CAM0, CAM1 = (-1.6, -0.3, 13.6), (1.5, 0.15, 11.6)  # r2_plates crates keys (x, y, ortho width), frame 1 -> n


def _pix(x, y):
    """Plate pixel (1672 x 941, top-left origin) -> card units (image up = +Y)."""
    return ((x / 1672 - 0.5) * CARD_W, (0.5 - y / 941) * CARD_H)


def _screen(t, dur, px, py):
    u = ease(t / max(dur, 1e-6))
    cx, cy, w = (a + (b - a) * u for a, b in zip(CAM0, CAM1))
    return (0.5 + (px - cx) / w, 0.5 - (py - cy) / (w * 9 / 16))


# (t0, t1, plate pixel of the counted object, tag offset from the anchor, tag lines, chain text)
STEPS = [(0.5, 3.2, (560, 590), (0.07, -0.13), ["250+ 箱", "白色铝框板条箱"], "250+ 箱"),
         (2.9, 6.4, (870, 455), (0.06, -0.15), ["43 个集装箱", "航空集装箱 · 货网托盘"], "43 个集装箱"),
         (6.1, 8.0, (620, 230), (0.1, -0.06), ["几架货机"], "几架货机"),
         (7.7, 99, (1290, 420), (-0.1, -0.13), ["20 辆卡车"], "20 辆卡车")]


def crates(img, t, dur, W, H):
    L = Layer(W, H)
    for t0, t1, pix, off, lines, _ in STEPS:
        a = fade(t, t0, t1, 0.4)
        if a <= 0:
            continue
        p = _screen(t, dur, *_pix(*pix))
        if not (0.03 < p[0] < 0.97):
            continue
        L.label(p, (p[0] + off[0], p[1] + off[1]), lines, a, size=0.046)
    chain = [c for t0, _, _, _, _, c in STEPS if t >= t0]
    if chain:
        L.tag((0.975, 0.055), [" → ".join(chain)], fade(t, STEPS[0][0], None, 0.4), size=0.036, anchor="ra")
    return L.compose(img)


OVERLAYS["A0_03"] = crates
