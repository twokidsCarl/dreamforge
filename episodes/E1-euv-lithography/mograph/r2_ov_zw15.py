"""Round-15 overlays (P1, R15_ROOT_CAUSE row 5 "label overload"). Loaded after r2_ov_zv14 (name sorts later), so
entries here replace earlier ones for the same shot. Rule: one top-right block + at most one leader label on screen.

B8_03 (R14: "PIP + 2-line tag + magnifier reading + wafer-edge ticks -1 / -0.5 / 0 + small caption + subtitle"):
  the wafer-ruler digits are gone from the render (r2_cutaway R15); here the PIP's inner caption and the magnifier's
  small caption go, the read-out stays one block under the PIP, the magnifier keeps only the current reading.
C_03 (R14: "label blocks pile up"): one station label at a time (no overlap between stations); at the mask the
  explanation is the single top-right block, the leader only names the mask.
B5_01 (R14: "two labels + subtitle stacked mid-frame; top-right title only on the last frame"): fixed top-right
  "照明系统（示意）" from the start + at most two small one-line leader labels.
B7_06 (R15 rebuild: disc mirrors, full-figure person on the right): steps name the mirror faces, labels on the left.
"""
import importlib.util
import os

from PIL import Image, ImageDraw, ImageFilter

from r2_ov_common import CYAN, INK2, VIOLET, FPS, Layer, anchor, fade

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
    spec = importlib.util.spec_from_file_location(module + "_r15base", os.path.join(_HERE, module + ".py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


_misc = _mod("r2_ov_misc")
_zr8 = _mod("r2_ov_zr8")
_zu = _mod("r2_ov_zu13")


def _lerp(a, b, u):
    return (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u)


@ov("B8_03", no_labels=True)
def scan(img, t, dur, W, H):
    n = max(2, round(dur * FPS))
    f = int(round(t * FPS)) + 1
    u = _zr8.scan_u(f, n)
    w = round(u, 2)
    r = 8 * w
    a = fade(t, 0.3)
    w0, w1 = anchor("B8_03", t, "wr0", (0.55, 0.9)), anchor("B8_03", t, "wr1", (0.45, 0.9))
    wc = _lerp(w0, w1, u)                                    # the wafer-stage pointer on its ruler, this frame
    MC, MR = (0.13, 0.55), 0.14
    if a > 0:
        cx, cy = wc[0] * W, wc[1] * H
        half = 0.04 * H
        box = (int(cx - half), int(cy - half * 0.8), int(cx + half), int(cy + half * 1.2))
        if box[0] > 0 and box[1] > 0 and box[2] < W and box[3] < H:
            crop = img.crop(box).resize((int(MR * H * 2), int(MR * H * 2)), Image.LANCZOS)
            img = _misc.magnifier(img, MC, MR, crop, a, anchor=(wc[0], wc[1]))
    pip = _zu._pip_frame(f)
    out = img.convert("RGBA")
    PB, PC = _zu.PIP_BOX, _zu.PIP_CROP
    x0, y0, x1, y1 = (int(PB[0] * W), int(PB[1] * H), int(PB[2] * W), int(PB[3] * H))
    if pip is not None and a > 0:
        pw, ph = pip.size
        c = pip.crop((int(PC[0] * pw), int(PC[1] * ph), int(PC[2] * pw), int(PC[3] * ph))).resize((x1 - x0, y1 - y0), Image.LANCZOS)
        sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(sh).rectangle((x0 - 4, y0 + 2, x1 + 6, y1 + 10), fill=(0, 0, 0, int(150 * a)))
        out = Image.alpha_composite(out, sh.filter(ImageFilter.GaussianBlur(H * 0.01)))
        out.paste(c, (x0, y0), Image.new("L", c.size, int(255 * a)))
    L = Layer(W, H)
    lw = max(3, int(H * 0.006))
    if pip is not None:
        L.d.rectangle((x0, y0, x1, y1), outline=(*CYAN, int(230 * a)), width=max(2, int(H * 0.004)))

        def to_pip(p):
            px = (p[0] - PC[0]) / (PC[2] - PC[0])
            py = (p[1] - PC[1]) / (PC[3] - PC[1])
            return (PB[0] + px * (PB[2] - PB[0]), PB[1] + py * (PB[3] - PB[1]))
        r0 = to_pip(anchor("B8_03M", t, "rr0", (0.15, 0.3)))
        r1 = to_pip(anchor("B8_03M", t, "rr1", (0.85, 0.3)))
        rc = _lerp(r0, r1, u)
        L.d.line([L.P(r0), L.P(rc)], fill=(*CYAN, int(230 * a)), width=lw)
        L.g.line([L.P(r0), L.P(rc)], fill=(*CYAN, int(150 * a)), width=lw * 3)
    L.d.line([L.P(w0), L.P(wc)], fill=(*CYAN, int(230 * a)), width=lw)
    L.g.line([L.P(w0), L.P(wc)], fill=(*CYAN, int(150 * a)), width=lw * 3)
    # the one top-right block: PIP + its read-out directly under it
    L.tag((PB[0], PB[3] + 0.025), [f"掩模台 → {r:.2f} 格 · 晶圆台 ← {w:.2f} 格", "恒 8 : 1 · 缩小 8× · 入射 5.4°（放大示意）"],
          a, size=0.03)
    # the magnifier keeps only the current wafer reading (follows the pointer)
    L.text((MC[0], MC[1] + MR * 0.45), f"{-w:+.2f}".replace("+0.00", "0.00"), 0.06, CYAN, a, anchor="ma", mono=True)
    return L.compose(out)


@ov("C_03", no_labels=True)
def tour(img, t, dur, W, H):
    L = Layer(W, H)
    stations = [("coll", 0.0, 0.2, ["收集镜", "把光聚向中间焦点"]),
                ("if", 0.2, 0.42, ["中间焦点 IF"]),
                ("ffm", 0.42, 0.7, ["照明系统 · 场分面镜"]),
                ("mask", 0.7, 1.01, ["反射式掩模"])]
    for name, f0, f1, lines in stations:
        a = fade(t, f0 * dur + 0.3, f1 * dur - 0.15, 0.35)
        if a <= 0:
            continue
        p = anchor("C_03", t, name, (0.5, 0.5))
        if not (0.03 < p[0] < 0.97 and 0.03 < p[1] < 0.85):
            continue
        tx = p[0] - 0.24 if p[0] > 0.55 else p[0] + 0.12
        L.label(p, (max(0.04, min(0.6, tx)), max(0.3, min(0.7, p[1] + 0.14))), lines, a,
                accent=VIOLET if name == "mask" else CYAN)
        if name == "mask":
            L.tag((0.6, 0.06), ["带电路图形的反射式掩模", "约 5.4° 斜射进来 → 反射出去（角度放大示意）"], a,
                  accent=VIOLET, size=0.032)
    return L.compose(img)


@ov("B5_01", no_labels=True)
def illum(img, t, dur, W, H):
    L = Layer(W, H)
    L.tag((0.72, 0.06), ["照明系统（示意）"], fade(t, 0.3), accent=VIOLET, size=0.038)
    f = anchor("B5_01", t, "ffm", (0.55, 0.12))
    p = anchor("B5_01", t, "pfm", (0.27, 0.8))
    if 0.03 < f[0] < 0.97 and 0.03 < f[1] < 0.85:
        L.label(f, (min(0.74, max(0.04, f[0] + 0.1)), max(0.3, min(0.7, f[1] + 0.22))), ["场分面镜 · 切分光场"],
                fade(t, 1.2), size=0.034)
    if 0.03 < p[0] < 0.97 and 0.03 < p[1] < 0.8:
        L.label(p, (min(0.74, p[0] + 0.16), min(0.72, p[1] + 0.02)), ["光瞳分面镜"], fade(t, 1.8), size=0.034)
    return L.compose(img)


@ov("B7_06", no_labels=True)
def po(img, t, dur, W, H):
    L = Layer(W, H)
    L.tag((0.66, 0.06), ["High-NA 投影物镜（示意）", "约 12 吨 · 来源 ZEISS"], fade(t, 0.3), accent=VIOLET, size=0.036)
    steps = [("m5r", 0.0, 0.42, ["① 光从掩模来，落在 M5 镜面上"]),
             ("m6r", 0.42, 0.7, ["② 反射到 M6 镜面，再聚拢"]),
             ("wfoc", 0.7, 1.01, ["③ 会聚光穿过 M5 中心孔", "落到晶圆上一点"])]
    for name, f0, f1, lines in steps:
        al = fade(t, max(0.4, f0 * dur + 0.2), f1 * dur - 0.1, 0.3)
        if al <= 0:
            continue
        p = anchor("B7_06", t, name, (0.5, 0.5))
        L.label(p, (0.04, max(0.28, min(0.62, p[1] - 0.05))), lines, al, accent=VIOLET, size=0.032)
    e = anchor("B7_06", t, "eng", (0.8, 0.55))
    if 0.03 < e[0] < 0.97 and 0.03 < e[1] < 0.95:
        L.label(e, (min(0.86, e[0] + 0.05), max(0.3, e[1] - 0.1)), ["人 ≈ 1.8 m"], fade(t, 1.0), size=0.03)
    return L.compose(img)
