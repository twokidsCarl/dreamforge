"""Round-2 overlay layer for the cutaway, title and documentary-plate shots (A0_10, B5_01, C_03, B3_02, B8_03,
B7_06, A0_02, A0_03, D_07). fn(img, t, dur, W, H) -> RGB. Storyboard labels (top right) and subtitles are added
later by the compositor, so these keep x > 0.62 W / y < 0.28 H and the bottom 15 % free."""
from r2_ov_common import CYAN, INK, INK2, VIOLET, Layer, anchor, ease, fade

OVERLAYS = {}
NO_STORYBOARD_LABELS = set()


def ov(sid, no_labels=False):
    def wrap(fn):
        OVERLAYS[sid] = fn
        if no_labels:
            NO_STORYBOARD_LABELS.add(sid)
        return fn
    return wrap


@ov("A0_10", no_labels=True)
def title(img, t, dur, W, H):
    """1C (R3): one heavy white serif line ~60 % of the frame width over the machine panorama, the violet
    underline under 光刻机; English small line; scale tag on the suited pair."""
    L = Layer(W, H)
    a = fade(t, 0.6, None, 0.8)
    txt, y0 = "一台光刻机里发生了什么", 0.06
    size = 0.6 * W / H / 11 * 1.0                     # 11 CJK glyphs across ~60 % of the width
    L.text((0.5, y0), txt, size, INK, a, anchor="ma", serif="bold")
    b = L.bbox((0.5, y0), txt, size, anchor="ma", serif="bold")
    k = ease((t - 1.4) / 1.0)
    if k > 0:                                                    # underline under 光刻机, EUV violet
        b2 = L.bbox((b[0] / W, y0), "一台", size, serif="bold")
        b3 = L.bbox((b[0] / W, y0), "一台光刻机", size, serif="bold")
        x0, x1, y = b2[2], b3[2], b[3] + H * 0.014
        L.d.rectangle((x0, y, x0 + (x1 - x0) * k, y + max(3, H * 0.008)), fill=(*VIOLET, int(255 * a)))
        L.g.rectangle((x0, y, x0 + (x1 - x0) * k, y + max(3, H * 0.008)), fill=(*VIOLET, int(160 * a)))
    L.text((0.5, b[3] / H + 0.045), "WHAT HAPPENS INSIDE AN EUV LITHOGRAPHY MACHINE", 0.026, INK2,
           fade(t, 1.6, None, 0.8), anchor="ma")
    e = anchor("A0_10", t, "eng", (0.5, 0.72))
    L.label(e, (e[0] + 0.07, e[1] - 0.05), ["人 ≈ 1.8 m", "尺度参照 · 机器为示意"], fade(t, 3.0, None), size=0.036)
    return L.compose(img)


@ov("B5_01")
def illum(img, t, dur, W, H):
    L = Layer(W, H)
    f = anchor("B5_01", t, "ffm", (0.55, 0.12))
    p = anchor("B5_01", t, "pfm", (0.27, 0.8))
    g = anchor("B5_01", t, "g1", (0.68, 0.62))
    L.label(f, (min(0.9, f[0] + 0.1), max(0.1, f[1] + 0.22)), ["场分面镜", "数百面小镜 · 切分光场"], fade(t, 2.6))
    L.label(p, (min(0.9, p[0] + 0.16), min(0.78, p[1] + 0.02)), ["光瞳分面镜", "重新拼成均匀照明"], fade(t, 2.9))
    L.label(g, (min(0.9, g[0] + 0.08), min(0.78, g[1] + 0.12)), ["聚光镜 → 掩模"], fade(t, 3.2))
    return L.compose(img)


@ov("C_03")
def tour(img, t, dur, W, H):
    L = Layer(W, H)
    stations = [("coll", 0.0, 0.33, ["收集镜", "把光聚向中间焦点"]),
                ("if", 0.12, 0.42, ["中间焦点 IF", "光离开光源腔"]),
                ("ffm", 0.4, 0.72, ["照明系统", "匀化 · 整形"]),
                ("mask", 0.7, 1.01, ["掩模", "反射电路图形 · 约 6° 斜入射"])]
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


@ov("B3_02")
def collector(img, t, dur, W, H):
    L = Layer(W, H)
    h = anchor("B3_02", t, "hole", (0.45, 0.45))
    p = anchor("B3_02", t, "plasma", (0.7, 0.4))
    L.label(h, (max(0.06, h[0] - 0.22), min(0.76, h[1] + 0.22)), ["中心孔", "CO₂ 激光从这里穿过"], fade(t, 1.0))
    L.label(p, (min(0.8, p[0] + 0.08), min(0.72, p[1] + 0.25)), ["第一焦点", "锡滴在这里被打成等离子体"], fade(t, 2.0),
            size=0.038)
    f = anchor("B3_02", t, "if", (1.2, 0.5))
    if 0.03 < f[0] < 0.97:
        L.label(f, (min(0.86, f[0] - 0.06), min(0.72, f[1] + 0.2)), ["中间焦点 IF", "反射光锥在这里会聚"],
                fade(t, 0.6, 3.6), accent=VIOLET, size=0.038)
    return L.compose(img)


@ov("B8_03", no_labels=True)
def scan(img, t, dur, W, H):
    """R3: three blocks only (mask stage 8x, wafer stage 1x opposite, the 6-degree reflective mask) with travel
    arrows that follow the stages."""
    L = Layer(W, H)
    m = anchor("B8_03", t, "rstage", (0.62, 0.2))
    w = anchor("B8_03", t, "wstage", (0.58, 0.82))
    a = fade(t, 0.6)
    L.arrow((m[0] - 0.02, m[1] + 0.07), (m[0] + 0.2, m[1] + 0.07), a, CYAN, 0.006, 0.026)
    L.label(m, (min(0.8, m[0] + 0.12), max(0.31, m[1] + 0.13)), ["掩模台  行程 8×", "比晶圆台快 8 倍"], a, size=0.04)
    L.arrow((w[0] + 0.02, w[1] - 0.06), (w[0] - 0.005, w[1] - 0.06), a, CYAN, 0.006, 0.02)
    L.label(w, (min(0.82, w[0] + 0.16), min(0.74, w[1] - 0.04)), ["晶圆台  1×", "反向移动"], a, size=0.04)
    mk = anchor("B8_03", t, "mask", (0.5, 0.25))
    L.label(mk, (0.08, 0.36), ["反射式掩模", "光以约 6° 斜射、再反射进物镜"], fade(t, 1.6), accent=VIOLET, size=0.038)
    return L.compose(img)


@ov("B7_06")
def po(img, t, dur, W, H):
    L = Layer(W, H)
    e = anchor("B7_06", t, "eng", (0.78, 0.7))
    L.label(e, (0.82, 0.48), ["人 ≈ 1.8 m"], fade(t, 1.0), size=0.038)
    p = anchor("B7_06", t, "po", (0.4, 0.45))
    L.label(p, (0.06, 0.4), ["六面反射镜", "前盖拆开 · 示意"], fade(t, 1.8), accent=VIOLET, size=0.038)
    return L.compose(img)


def _a003_screen(t, dur, px, py):
    """Plate point (plate units, r2_plates crates card: 15 x 10) -> screen fraction under the camera truck."""
    u = ease(t / max(dur, 1e-6))
    cx, cy, w = -1.2 + 2.2 * u, -0.2 + 0.2 * u, 13.4 - 0.4 * u
    return (0.5 + (px - cx) / w, 0.5 - (py - cy) / (w * 9 / 16))


@ov("A0_03", no_labels=True)
def crates(img, t, dur, W, H):
    """R3 (7A): every number sits on its object with a leader (crates, freighter, trucks) as the camera trucks
    along the row; the container step has no object in this plate, so it joins the chain line top right."""
    L = Layer(W, H)
    steps = [(0.6, (-1.94, -0.91), (0.16, 0.5), ["250+ 个", "白色铝框板条箱"]),
             (4.0, (-1.29, 2.17), (0.08, 0.34), ["几架", "货机"]),
             (6.4, (5.63, 0.56), (0.62, 0.58), ["20 辆", "卡车"])]
    for t0, pp, tagp, lines in steps:
        a = fade(t, t0, None, 0.5)
        if a <= 0:
            continue
        p = _a003_screen(t, dur, *pp)
        if not (0.02 < p[0] < 0.98):
            continue
        L.label(p, tagp if tagp[0] < p[0] else tagp, lines, a, size=0.05)
    a2 = fade(t, 2.4, None, 0.5)
    L.tag((0.64, 0.06), ["250+ 箱 → 43 个集装箱", "→ 几架货机 → 20 辆卡车"], a2, size=0.036)
    return L.compose(img)
