"""Round-7 overlays (P1, R6 review fixes). Loaded after r2_ov_zr6 (name sorts last), so an entry here replaces
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
    """R7 (H9): one generation only. High-NA (EXE): 5.4 deg at the mask and 8x scan-direction reduction -> the
    reticle stage travels 8x the wafer stage. The R6 '约 6°' was NXE data mixed with the EXE 8x."""
    L = Layer(W, H)
    n = max(2, round(dur * FPS))
    u = max(0.0, min(1.0, t * FPS / (n - 1)))
    a = fade(t, 0.3)
    r0, r1 = anchor("B8_03", t, "rr0", (0.25, 0.1)), anchor("B8_03", t, "rr1", (0.62, 0.1))
    w0, w1 = anchor("B8_03", t, "wr0", (0.5, 0.92)), anchor("B8_03", t, "wr1", (0.46, 0.92))
    rc, wc = _lerp(r0, r1, u), _lerp(w0, w1, u)
    lw = max(3, int(H * 0.007))
    for p0, pc in ((r0, rc), (w0, wc)):
        L.d.line([L.P(p0), L.P(pc)], fill=(*CYAN, int(230 * a)), width=lw)
        L.g.line([L.P(p0), L.P(pc)], fill=(*CYAN, int(150 * a)), width=lw * 3)
    L.tag((0.66, 0.1), [f"掩模台 → {8 * u:.1f} 格", f"← 晶圆台 {u:.1f} 格 · 反向", "High-NA 扫描向缩小 8× → 行程 8 倍"],
          a, size=0.04)
    g = anchor("B8_03", t, "g2", (0.35, 0.6))
    L.label((g[0] - 0.01, g[1]), (0.04, 0.3), ["照明光从掩模下方射入", "High-NA：约 5.4° 斜射 → 反射进投影镜"],
            fade(t, 1.0), accent=VIOLET, size=0.034)
    return L.compose(img)


@ov("C_03", no_labels=True)
def tour(img, t, dur, W, H):
    """R7 (H9 risk): the mask station no longer quotes an angle (R6 '约 6°' was NXE data in a High-NA film)."""
    L = Layer(W, H)
    stations = [("coll", 0.0, 0.33, ["收集镜", "把光聚向中间焦点"]),
                ("if", 0.12, 0.42, ["中间焦点 IF", "光离开光源腔"]),
                ("ffm", 0.4, 0.72, ["照明系统", "匀化 · 整形"]),
                ("mask", 0.7, 1.01, ["掩模", "斜射进来 · 反射出电路图形"])]
    for name, f0, f1, lines in stations:
        a = fade(t, f0 * dur + 0.4, f1 * dur, 0.5)
        if a <= 0:
            continue
        p = anchor("C_03", t, name, (0.5, 0.5))
        if not (0.03 < p[0] < 0.97 and 0.03 < p[1] < 0.85):
            continue
        tx = p[0] - 0.2 if p[0] > 0.55 else p[0] + 0.12
        L.label(p, (max(0.04, min(0.6, tx)), max(0.08, min(0.7, p[1] + 0.12))), lines, a)
    return L.compose(img)


def _base(module, fn_name):
    import importlib.util
    import os
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), module + ".py")
    spec = importlib.util.spec_from_file_location(module + "_r7base", p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return getattr(m, fn_name)


_magnifier = _base("r2_ov_misc", "magnifier")
_tem_panel = _base("r2_ov_misc", "_tem_panel")
_track = _base("r2_ov_misc", "track")


@ov("B4_07", no_labels=True)
def mirror(img, t, dur, W, H):
    """R7 (F): the TEM magnifier's leader ends on the thin coating at the top edge of the cut face (3D anchor),
    and the tag says the 40 pairs are only that top film (~0.3 um), the rest is glass-ceramic substrate."""
    u = t / dur
    a = ease((u - 0.42) / 0.14)
    r = 0.15 + 0.17 * ease((u - 0.42) / 0.3)
    fb = _track(t, dur, [(0.42, (0.3, 0.6)), (0.55, (0.3, 0.58)), (1.0, (0.3, 0.2))])
    cand = [anchor("B4_07", t, f"coat{k}", None) for k in (2, 1, 3, 0)]
    cand = [c for c in cand if c and 0.06 < c[0] < 0.6 and 0.08 < c[1] < 0.8]
    an = cand[0] if cand else fb
    if a > 0:
        size = int(2 * r * H)
        img = _magnifier(img, (0.66, 0.47), r, _tem_panel(max(64, size)), a, anchor=an)
    L = Layer(W, H)
    a2 = fade(t, dur * 0.72)
    L.tag((0.04, 0.6), ["钼 / 硅 × 40 对 · 每对约 7 nm", "只在镜面最顶层 · 总厚约 0.3 μm"], a2, size=0.038)
    a0 = fade(t, 0.2, dur * 0.45)
    L.label((0.34, 0.56), (0.05, 0.7), ["多层膜反射镜"], a0)
    return L.compose(img)
