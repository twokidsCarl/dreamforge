"""Round-17 overlays for r2_cutaway (P1). Loaded after r2_ov_zx16 (name sorts later); entries replace earlier ones.
Label work = deletions / merges only (R17_ROOT_CAUSE row 5).

B7_06 (R16: "labels all crowd the left side; >3 lines on screen"): one top-right block, <= 3 lines: the title, the
  current step (① -> ② -> ③ replace each other in the same line, no leaders across the barrel) and one fact line
  that also carries the person scale (the separate "人 ≈ 1.8 m" leader is merged into it). A small numbered marker
  sits on the part the current step names.
B8_03 (R16: "PIP + two lines + magnifier + subtitle = four layers; '-0.25' in the magnifier has no unit"): the
  magnifier circle is deleted; its reading is merged into the PIP read-out line with the same unit and sign
  convention as the rulers ("掩模台 → +2.00 格 · 晶圆台 ← −0.25 格"). Strict 8 : 1 read-out and the PIP unchanged.
"""
import importlib.util
import os

from PIL import Image, ImageDraw, ImageFilter

from r2_ov_common import CYAN, VIOLET, FPS, Layer, anchor, fade

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
    spec = importlib.util.spec_from_file_location(module + "_r17base", os.path.join(_HERE, module + ".py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


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
    # one block under the PIP: both readings in one line, same unit, signed like the rulers (no magnifier)
    wr = "0.00" if w == 0 else f"−{w:.2f}"
    L.tag((PB[0], PB[3] + 0.025), [f"掩模台 → +{r:.2f} 格 · 晶圆台 ← {wr} 格", "恒 8 : 1 · 缩小 8× · 入射 5.4°（放大示意）"],
          a, size=0.03)
    return L.compose(out)


@ov("B7_06", no_labels=True)
def po(img, t, dur, W, H):
    L = Layer(W, H)
    steps = [("m5r", 0.0, 0.42, "① 光从掩模来，落在 M5 镜面上"),
             ("m6r", 0.42, 0.7, "② 反射到 M6 镜面，再聚拢"),
             ("wfoc", 0.7, 1.01, "③ 会聚光穿过 M5 中心孔，落到晶圆一点")]
    cur, name = steps[0][3], steps[0][0]
    for nm, f0, f1, s in steps:
        if t >= f0 * dur:
            cur, name = s, nm
    a = fade(t, 0.3)
    L.tag((0.6, 0.05), ["High-NA 投影物镜（示意）", cur, "约 12 吨 · 来源 ZEISS · 右侧人 ≈ 1.8 m"], a, accent=VIOLET,
          size=0.034)
    p = anchor("B7_06", t, name, (0.5, 0.5))
    if 0.03 < p[0] < 0.97 and 0.03 < p[1] < 0.95 and a > 0:  # numbered marker on the part the step names
        x, y = L.P(p)
        rr = L.s(0.016)
        L.d.ellipse((x - rr, y - rr, x + rr, y + rr), outline=(*VIOLET, int(255 * a)), width=max(2, L.s(0.003)))
        L.text(((x + rr * 1.4) / W, (y - rr) / H), cur[0], 0.03, VIOLET, a)
    return L.compose(img)
