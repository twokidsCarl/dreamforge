"""Round-10 overlays (P1). Name sorts after r2_ov_zr*, so entries here replace earlier ones for the same shot.
Only the mechanism heroes that changed geometry in R10 get new text: C_03 mask (reflective, ~5.4 deg in / out,
angle drawn enlarged), B7_06 centre-hole M5 / M6, B5_01 labels one beat earlier. <= 3 blocks, bottom 15 % free."""
from r2_ov_common import CYAN, VIOLET, Layer, anchor, fade

OVERLAYS = {}
NO_STORYBOARD_LABELS = set()


def ov(sid, no_labels=False):
    def wrap(fn):
        OVERLAYS[sid] = fn
        if no_labels:
            NO_STORYBOARD_LABELS.add(sid)
        return fn
    return wrap


@ov("C_03", no_labels=True)
def tour(img, t, dur, W, H):
    L = Layer(W, H)
    stations = [("coll", 0.0, 0.33, ["收集镜", "把光聚向中间焦点"]),
                ("if", 0.12, 0.42, ["中间焦点 IF", "光离开光源腔"]),
                ("ffm", 0.4, 0.72, ["照明系统", "场分面镜 · 光瞳分面镜"]),
                ("mask", 0.7, 1.01, ["反射式掩模 · 带电路图形", "约 5.4° 斜射进来 → 反射出去", "（角度放大示意）"])]
    for name, f0, f1, lines in stations:
        a = fade(t, f0 * dur + 0.4, f1 * dur, 0.5)
        if a <= 0:
            continue
        p = anchor("C_03", t, name, (0.5, 0.5))
        if not (0.03 < p[0] < 0.97 and 0.03 < p[1] < 0.85):
            continue
        tx = p[0] - 0.24 if p[0] > 0.55 else p[0] + 0.12
        L.label(p, (max(0.04, min(0.6, tx)), max(0.12, min(0.7, p[1] + 0.14))), lines, a,
                accent=VIOLET if name == "mask" else CYAN)
    return L.compose(img)


@ov("B7_06", no_labels=True)
def po(img, t, dur, W, H):
    L = Layer(W, H)
    L.tag((0.66, 0.06), ["High-NA 投影物镜", "外形示意 · 约 12 吨 · 来源 ZEISS"], fade(t, 0.3), accent=VIOLET, size=0.04)
    m6 = anchor("B7_06", t, "m6", (0.45, 0.5))
    L.label(m6, (0.05, 0.36), ["M5 / M6 中心开孔", "光从孔中穿过 → 晶圆"], fade(t, 1.2), accent=VIOLET, size=0.036)
    e = anchor("B7_06", t, "eng", (0.78, 0.7))
    L.label(e, (min(0.84, e[0] + 0.04), 0.5), ["人 ≈ 1.8 m"], fade(t, 1.0), size=0.034)
    return L.compose(img)


@ov("B5_01")
def illum(img, t, dur, W, H):
    L = Layer(W, H)
    f = anchor("B5_01", t, "ffm", (0.55, 0.12))
    p = anchor("B5_01", t, "pfm", (0.27, 0.8))
    L.label(f, (min(0.78, f[0] + 0.1), max(0.12, min(0.7, f[1] + 0.22))), ["场分面镜", "几百面弧形小镜 · 切分光场"],
            fade(t, 1.6))
    if 0.03 < p[0] < 0.97 and 0.03 < p[1] < 0.85:
        L.label(p, (min(0.8, p[0] + 0.16), min(0.72, p[1] + 0.02)), ["光瞳分面镜", "重新拼成均匀照明"], fade(t, 2.0))
    return L.compose(img)
