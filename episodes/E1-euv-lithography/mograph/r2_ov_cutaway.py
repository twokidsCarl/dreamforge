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
    """1C: one white serif line over the machine panorama, the violet word underlined; English small line."""
    L = Layer(W, H)
    a = fade(t, 0.6, None, 0.8)
    L.text((0.5, 0.075), "一台光刻机里发生了什么", 0.088, INK, a, anchor="ma", serif=True)
    b = L.bbox((0.5, 0.075), "一台光刻机里发生了什么", 0.088, anchor="ma", serif=True)
    k = ease((t - 1.4) / 1.0)
    if k > 0:                                                    # underline under 光刻机, EUV violet
        b2 = L.bbox((b[0] / W, 0.075), "一台", 0.088, serif=True)
        b3 = L.bbox((b[0] / W, 0.075), "一台光刻机", 0.088, serif=True)
        x0, x1, y = b2[2], b3[2], b[3] + H * 0.012
        L.d.rectangle((x0, y, x0 + (x1 - x0) * k, y + max(2, H * 0.006)), fill=(*VIOLET, int(255 * a)))
        L.g.rectangle((x0, y, x0 + (x1 - x0) * k, y + max(2, H * 0.006)), fill=(*VIOLET, int(160 * a)))
    L.text((0.5, 0.21), "WHAT HAPPENS INSIDE AN EUV LITHOGRAPHY MACHINE", 0.026, INK2, fade(t, 1.6, None, 0.8),
           anchor="ma")
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
    return L.compose(img)


@ov("B8_03")
def scan(img, t, dur, W, H):
    L = Layer(W, H)
    m = anchor("B8_03", t, "rstage", (0.4, 0.12))
    w = anchor("B8_03", t, "wstage", (0.55, 0.86))
    a = fade(t, 0.8)
    k = 0.5 + 0.5 * ((t / max(dur, 0.1)) % 1.0)
    # the reticle stage covers 8x the wafer stage's travel, opposite directions (High-NA scan direction)
    L.arrow((m[0] - 0.02, m[1] + 0.06), (m[0] - 0.02 - 0.24, m[1] + 0.06), a, CYAN, 0.006, 0.026)
    L.tag((m[0] - 0.27, m[1] + 0.09), ["掩模台  8×", "速度 = 晶圆台 × 8"], a)
    wy = min(w[1] - 0.06, 0.74)
    L.arrow((w[0] - 0.02, wy), (w[0] - 0.02 + 0.03, wy), a, CYAN, 0.006, 0.02)
    L.tag((w[0] + 0.04, wy - 0.03), ["晶圆台  1×（反向）"], a)
    mk = anchor("B8_03", t, "mask", (0.42, 0.18))
    L.label(mk, (0.06, 0.34), ["反射式掩模", "光从斜下方来、反射进物镜"], fade(t, 1.6), accent=VIOLET, size=0.038)
    wf = anchor("B8_03", t, "wafer", (0.6, 0.8))
    L.label(wf, (0.74, 0.62), ["狭缝光斑"], fade(t, 2.2), accent=VIOLET, size=0.038)
    return L.compose(img)


@ov("B7_06")
def po(img, t, dur, W, H):
    L = Layer(W, H)
    e = anchor("B7_06", t, "eng", (0.78, 0.7))
    L.label(e, (0.82, 0.48), ["人 ≈ 1.8 m"], fade(t, 1.0), size=0.038)
    p = anchor("B7_06", t, "po", (0.4, 0.45))
    L.label(p, (0.06, 0.4), ["六面反射镜", "前盖拆开 · 示意"], fade(t, 1.8), accent=VIOLET, size=0.038)
    return L.compose(img)


@ov("A0_03", no_labels=True)
def crates(img, t, dur, W, H):
    """Count chain as a stack of tags that build up step by step (7A: numbers on the real objects)."""
    L = Layer(W, H)
    steps = [(0.6, "250+", "个白色铝框板条箱"), (2.8, "43", "个集装箱"), (5.0, "几架", "货机"), (7.2, "20", "辆卡车")]
    x, y = 0.06, 0.1
    for i, (t0, num, what) in enumerate(steps):
        a = fade(t, t0, None, 0.5)
        if a <= 0:
            continue
        yy = y + i * 0.105
        L.d.rounded_rectangle((x * W - H * 0.012, yy * H - H * 0.01, x * W + H * 0.5, yy * H + H * 0.085),
                              radius=int(H * 0.006), fill=(7, 11, 20, int(175 * a)))
        L.d.rectangle((x * W - H * 0.012, yy * H - H * 0.01, x * W - H * 0.008, yy * H + H * 0.085),
                      fill=(*CYAN, int(255 * a)))
        mono = num.replace("+", "").isdigit()
        L.text((x, yy), num, 0.062, INK, a, mono=mono)
        nb = L.bbox((x, yy), num, 0.062, mono=mono)
        L.text((nb[2] / W + 0.012, yy + 0.022), what, 0.036, INK2, a)
        if i:
            L.arrow((x + 0.012, yy - 0.03), (x + 0.012, yy - 0.006), a, CYAN, 0.003, 0.01)
    return L.compose(img)
