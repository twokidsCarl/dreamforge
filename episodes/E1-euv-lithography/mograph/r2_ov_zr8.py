"""Round-8 overlays (P1, R7 review fixes). Loaded after r2_ov_zr7 (name sorts last), so an entry here replaces
earlier overlays for the same shot. Layout rules: <= 2-3 text blocks per frame, upper right first, bottom 15 %
free for subtitles."""
import importlib.util
import os

from PIL import Image

from r2_ov_common import CYAN, INK, INK2, VIOLET, FPS, Layer, anchor, ease, fade

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
    spec = importlib.util.spec_from_file_location(module + "_r8base", os.path.join(_HERE, module + ".py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


_misc = _mod("r2_ov_misc")
_src = _mod("r2_ov_source")


# ---------------------------------------------------------------- B8_03
def scan_u(f, n):
    """Same knots as blender/shots/r2_cutaway.scan_knots: the 25 / 55 / 85 % frames sit on u = .25 / .55 / .85."""
    fr = [1 + round((n - 1) * p) for p in (0.245, 0.545, 0.85)]
    ks = [(1, 0.0)] + list(zip(fr, (0.25, 0.55, 0.85))) + [(n, 1.0)]
    for (f0, u0), (f1, u1) in zip(ks, ks[1:]):
        if f <= f1:
            return u0 + (u1 - u0) * max(0.0, (f - f0)) / max(1, f1 - f0)
    return 1.0


def _lerp(a, b, u):
    return (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u)


@ov("B8_03", no_labels=True)
def scan(img, t, dur, W, H):
    """R8: read-outs from the same scan knots as the stage keyframes -> 2.00 / 0.25, 4.40 / 0.55, 6.80 / 0.85
    grid units, a steady 8 : 1. A x4 zoom inset on the wafer-stage ruler makes its (short) reverse travel visible.
    The in / out legs at the mask are drawn at an enlarged angle, and the tag says so (EXE: ~5.4 deg)."""
    n = max(2, round(dur * FPS))
    f = int(round(t * FPS)) + 1
    u = scan_u(f, n)
    w = round(u, 2)
    r = 8 * w
    a = fade(t, 0.3)
    r0, r1 = anchor("B8_03", t, "rr0", (0.25, 0.1)), anchor("B8_03", t, "rr1", (0.62, 0.1))
    w0, w1 = anchor("B8_03", t, "wr0", (0.5, 0.92)), anchor("B8_03", t, "wr1", (0.46, 0.92))
    wc = _lerp(w0, w1, u)
    # x4 zoom of the wafer ruler around its pointer (real pixels of this frame)
    if a > 0:
        cx, cy = (w0[0] + w1[0]) / 2 * W, wc[1] * H
        half = 0.06 * H
        box = (int(cx - half), int(cy - half), int(cx + half), int(cy + half))
        if box[0] > 0 and box[1] > 0 and box[2] < W and box[3] < H:
            crop = img.crop(box).resize((int(half * 8), int(half * 8)), Image.LANCZOS)
            img = _misc.magnifier(img, (0.13, 0.66), 0.13, crop, a, anchor=(cx / W, cy / H))
    L = Layer(W, H)
    rc = _lerp(r0, r1, u)
    lw = max(3, int(H * 0.007))
    for p0, pc in ((r0, rc), (w0, wc)):
        L.d.line([L.P(p0), L.P(pc)], fill=(*CYAN, int(230 * a)), width=lw)
        L.g.line([L.P(p0), L.P(pc)], fill=(*CYAN, int(150 * a)), width=lw * 3)
    L.tag((0.66, 0.06), [f"掩模台 → {r:.2f} 格", f"← 晶圆台 {w:.2f} 格（反向）", "行程比恒为 8 : 1（High-NA 缩小 8×）"],
          a, size=0.038)
    L.text((0.13, 0.66 + 0.155), "晶圆台标尺 ×4", 0.03, INK2, fade(t, 0.5), anchor="ma")
    g = anchor("B8_03", t, "mask", (0.45, 0.25))
    L.label((g[0] - 0.005, g[1] + 0.03), (0.04, 0.2), ["掩模：斜射进 · 反射出", "约 5.4°（图中角度放大示意）"],
            fade(t, 1.0), accent=VIOLET, size=0.034)
    return L.compose(img)


# ---------------------------------------------------------------- B8_17: counters stacked upper right
@ov("B8_17", no_labels=True)
def wafer(img, t, dur, W, H):
    L = Layer(W, H)
    u = t / dur
    rows = [("场 / 片", 0.0, 0.8, 188), ("片 / 小时", 0.3, 0.7, 185), ("次曝光 / 小时", 0.55, 0.8, 34780)]
    a0 = fade(t, 0.1)
    if a0 > 0:
        L.d.rounded_rectangle((0.74 * W, 0.04 * H, 0.97 * W, 0.4 * H), radius=int(H * 0.012),
                              fill=(8, 11, 20, int(190 * a0)))
    for k, (unit, s0, s1, val) in enumerate(rows):
        a = fade(t, dur * s0)
        if a <= 0:
            continue
        p = ease((u - s0) / max(0.05, s1 - s0))
        if k == 0:
            s = str(int(round(188 * p)))
        elif k == 1:
            s = str(int(round(185 * p))) + ("+" if p >= 1 else "")
        else:
            s = "3.4 万+" if p >= 1 else f"{int(round(val * p)):,}"
        y = 0.055 + k * 0.115
        L.text((0.76, y), s, 0.052, VIOLET if k == 0 else CYAN if k == 1 else INK, a,
               mono=s.replace("+", "").replace(",", "").isdigit())
        L.text((0.76, y + 0.066), unit, 0.026, INK2, a)
    return L.compose(img)


# ---------------------------------------------------------------- B1_22: amplifier chain bar at the bottom
@ov("B1_22")
def amps(img, t, dur, W, H):
    """R8: the progress bar moves from the top-left (it fought the title block) to just above the subtitles."""
    m = _mod("r2_ov_source")
    orig = m.Layer

    class Shift(orig):
        def __init__(self, W_, H_):
            super().__init__(W_, H_)
            self._dy = 0.58 * H_

        def rect(self, box, *a_, **k_):
            return super().rect((box[0], box[1] + self._dy, box[2], box[3] + self._dy), *a_, **k_)

        def circle(self, c, *a_, **k_):
            return super().circle((c[0], c[1] + self._dy), *a_, **k_)

        def line(self, p0, p1, *a_, **k_):
            return super().line((p0[0], p0[1] + self._dy), (p1[0], p1[1] + self._dy), *a_, **k_)

        def text(self, p, *a_, **k_):
            return super().text((p[0], p[1] + self._dy), *a_, **k_)
    m.Layer = Shift
    return m.ov_B1_22(img, t, dur, W, H)


# ---------------------------------------------------------------- B2_08: equation only inside the magnifier
_b2 = _mod("r2_ov_zr6")


@ov("B2_08", no_labels=True)
def clean(img, t, dur, W, H):
    """R8: the lower-left equation panel is dropped (the magnifier already shows H2 -> 2H, Sn + 4H -> SnH4)."""
    d = anchor("B2_08", t, "dep", (0.5, 0.3))
    img = _src.ov_B2_08(img, t, dur, W, H, anchor_pt=d, center=(0.2, 0.36), panel_xy=(3.0, 3.0))
    L = Layer(W, H)
    p = anchor("B2_08", t, "pump", (0.85, 0.25))
    p = (min(0.96, max(0.55, p[0])), min(0.6, max(0.08, p[1])))
    L.label(p, (0.66, 0.05), ["SnH₄ 气体 → 抽气泵口", "深色斑点 = 镜面上的锡沉积"], fade(t, 0.8), accent=CYAN, size=0.036)
    return L.compose(img)


# ---------------------------------------------------------------- B1_10: no caption under the magnifier
@ov("B1_10")
def prepulse(img, t, dur, W, H):
    m = _mod("r2_ov_source")
    orig = m.magnifier

    def mag(L_, anchor_, center, r, inner, a=1.0, title=None):
        return orig(L_, anchor_, center, r, inner, a, title=None)
    m.magnifier = mag
    return m.ov_B1_10(img, t, dur, W, H)


# ---------------------------------------------------------------- B6_12: one title, two leaders
@ov("B6_12", no_labels=True)
def pellicle(img, t, dur, W, H):
    """R8: the upper-right storyboard title repeated '13 nm'; the in-frame leaders carry it alone."""
    return _misc.ov_B6_12(img, t, dur, W, H)


# ---------------------------------------------------------------- A2_08: two tag groups only
@ov("A2_08")
def wave(img, t, dur, W, H):
    m = _mod("r2_ov_misc")
    orig = m.L

    class NoTopRight(orig):
        def tag(self, p, lines, *a_, **k_):
            if p == (0.66, 0.06):               # the third, upper-right block (R7: 4 text groups on screen)
                return None
            return super().tag(p, lines, *a_, **k_)
    m.L = NoTopRight
    return m.ov_A2_08(img, t, dur, W, H)


# ---------------------------------------------------------------- A0_03: one counter, upper right, replaced in turn
_cut = _mod("r2_ov_cutaway")


@ov("A0_03", no_labels=True)
def crates(img, t, dur, W, H):
    """R8 (E): one upper-right counter block (mono digits) that is replaced step by step, each with a leader onto
    its object (crates -> freighters -> trucks), instead of three tags stacked on the left."""
    L = Layer(W, H)
    steps = [(0.6, 4.0, (-1.94, -0.91), ["250+ 箱", "白色铝框板条箱 · 装进 43 个集装箱"]),
             (4.0, 6.4, (-1.29, 2.17), ["几 架", "货机"]),
             (6.4, 99, (5.63, 0.56), ["20 辆", "卡车"])]
    for t0, t1, pp, lines in steps:
        a = fade(t, t0, t1, 0.4)
        if a <= 0:
            continue
        p = _cut._a003_screen(t, dur, *pp)
        L.tag((0.62, 0.06), lines, a, size=0.05)
        if 0.02 < p[0] < 0.98:
            L.d.line([L.P((0.62, 0.17)), L.P(p)], fill=(*CYAN, int(200 * a)), width=max(2, int(H * 0.003)))
    return L.compose(img)
