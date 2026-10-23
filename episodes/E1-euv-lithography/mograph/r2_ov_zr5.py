"""Round-5 overlays (P1, R4 review fixes). Loaded after r2_ov_zr4 (name sorts last), so an entry here replaces
earlier overlays for the same shot. Layout rules unchanged: <= 3 blocks, bottom 15 % free for subtitles."""
from r2_ov_common import CYAN, INK, INK2, VIOLET, FPS, Layer, anchor, ease, fade

OVERLAYS = {}
NO_STORYBOARD_LABELS = set()


def ov(sid, no_labels=False):
    def wrap(fn):
        OVERLAYS[sid] = fn
        if no_labels:
            NO_STORYBOARD_LABELS.add(sid)
        return fn
    return wrap


def _lerp(a, b, u):
    return (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u)


@ov("B8_03", no_labels=True)
def scan(img, t, dur, W, H):
    """R5: travel read straight off the rulers. A cyan bar fills the travelled part of each ruler (reticle 0 -> 8,
    wafer 0 -> 1, opposite directions) with live counters in the same unit, so 8 : 1 is a number the viewer sees
    grow. One violet tag names the short illumination leg and the ~6 deg V at the mask."""
    L = Layer(W, H)
    n = max(2, round(dur * FPS))
    u = max(0.0, min(1.0, t * FPS / (n - 1)))
    a = fade(t, 0.3)
    r0, r1 = anchor("B8_03", t, "rr0", (0.25, 0.1)), anchor("B8_03", t, "rr1", (0.62, 0.1))
    w0, w1 = anchor("B8_03", t, "wr0", (0.5, 0.92)), anchor("B8_03", t, "wr1", (0.46, 0.92))
    rc, wc = _lerp(r0, r1, u), _lerp(w0, w1, u)
    lw = max(3, int(H * 0.007))
    L.d.line([L.P(r0), L.P(rc)], fill=(*CYAN, int(230 * a)), width=lw)
    L.g.line([L.P(r0), L.P(rc)], fill=(*CYAN, int(150 * a)), width=lw * 3)
    L.d.line([L.P(w0), L.P(wc)], fill=(*CYAN, int(230 * a)), width=lw)
    L.g.line([L.P(w0), L.P(wc)], fill=(*CYAN, int(150 * a)), width=lw * 3)
    L.tag((0.70, 0.14), [f"掩模台 → {8 * u:.1f} 格", "行程是晶圆台的 8 倍"], a, size=0.042)
    L.tag((0.70, 0.66), [f"← 晶圆台 {u:.1f} 格", "同一把尺 · 反向移动"], a, size=0.042)
    g = anchor("B8_03", t, "g2", (0.35, 0.6))
    L.label((g[0] - 0.01, g[1]), (0.05, 0.3), ["照明光从掩模下方射入", "约 6° 斜射 → 反射进投影镜"], fade(t, 1.0),
            accent=VIOLET, size=0.036)
    return L.compose(img)


@ov("B7_06", no_labels=True)
def po(img, t, dur, W, H):
    """R5: the storyboard label drew a dark blurred block on the light studio backdrop; one compact tag instead,
    plus the mirror count on the (now single, non-crossing) path and the scale tag on the suited figure."""
    L = Layer(W, H)
    L.tag((0.66, 0.06), ["High-NA 投影物镜", "外形示意 · 约 12 吨 · 来源 ZEISS"], fade(t, 0.3), accent=VIOLET, size=0.04)
    p = anchor("B7_06", t, "po", (0.4, 0.45))
    L.label(p, (0.05, 0.42), ["六面反射镜 M1–M6", "一条光路 · 前盖拆开"], fade(t, 1.4), accent=VIOLET, size=0.036)
    e = anchor("B7_06", t, "eng", (0.78, 0.7))
    L.label(e, (min(0.84, e[0] + 0.04), 0.5), ["人 ≈ 1.8 m"], fade(t, 1.0), size=0.034)
    return L.compose(img)


def _base(module, fn_name):
    import importlib.util
    import os
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), module + ".py")
    spec = importlib.util.spec_from_file_location(module + "_r5base", p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return getattr(m, fn_name)


# C_03: the station tags already name IF / illuminator / mask; the storyboard labels left a half-faded
# "可动分面镜 · 示意" ghost in the 25 % frame (R4 review) -> drop them for this shot
OVERLAYS["C_03"] = _base("r2_ov_cutaway", "tour")
NO_STORYBOARD_LABELS.add("C_03")
