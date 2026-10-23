"""Round-14 overlays (P1). Loaded after r2_ov_zu13 (name sorts later), so entries here replace earlier ones.

B8_03 (R13: "the magnifier always shows -0.5, reads as the wafer not moving"): the ruler inset is cropped around the
wafer-stage pointer every frame (it follows the pointer) and prints the current reading inside the circle
(0 -> -0.25 / -0.55 / -0.85 at the three review frames); read-out moved top-right under the PIP, 2 lines.
B3_02 (R13: "4-5 labels on screen, 55 % overlap"): one label at a time, in story order (centre hole -> first focus
-> IF); with the storyboard label that is <= 2 text blocks on screen.
B7_06 (R14 rebuild): the light path is told in three timed steps on the parts it lands on (M5 ring -> M6 ring ->
through the M5 hole to one point on the wafer)."""
import importlib.util
import os

from PIL import Image, ImageDraw, ImageFilter

from r2_ov_common import CYAN, INK, INK2, VIOLET, FPS, Layer, anchor, fade, renders_dir

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
    spec = importlib.util.spec_from_file_location(module + "_r14base", os.path.join(_HERE, module + ".py"))
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
        L.text((PB[0] + 0.01, PB[3] - 0.045), "掩模台 · 同一时刻", 0.026, INK2, a)
    L.d.line([L.P(w0), L.P(wc)], fill=(*CYAN, int(230 * a)), width=lw)
    L.g.line([L.P(w0), L.P(wc)], fill=(*CYAN, int(150 * a)), width=lw * 3)
    # read-out top right under the PIP, two lines
    L.tag((PB[0], PB[3] + 0.025), [f"掩模台 → {r:.2f} 格 · 晶圆台 ← {w:.2f} 格", "恒 8 : 1 · 缩小 8× · 入射 5.4°（放大示意）"],
          a, size=0.03)
    # the current wafer reading printed inside the magnifier (follows the pointer)
    L.text((MC[0], MC[1] + MR * 0.45), f"{-w:+.2f}".replace("+0.00", "0.00"), 0.06, CYAN, a, anchor="ma", mono=True)
    L.text((MC[0], MC[1] + MR + 0.02), "晶圆台标尺 · 当前读数", 0.028, INK2, fade(t, 0.5), anchor="ma")
    return L.compose(out)


@ov("B3_02")
def collector(img, t, dur, W, H):
    L = Layer(W, H)
    steps = [("hole", 0.0, 0.36, ["中心孔", "CO₂ 激光从这里穿过"], CYAN, (0.45, 0.45)),
             ("plasma", 0.36, 0.62, ["第一焦点", "锡滴在这里被打成等离子体"], CYAN, (0.7, 0.4)),
             ("if", 0.62, 1.01, ["中间焦点 IF", "反射光锥会聚到这一点"], VIOLET, (1.2, 0.5))]
    for name, f0, f1, lines, acc, dflt in steps:
        al = fade(t, max(0.3, f0 * dur + 0.2), f1 * dur - 0.1, 0.3)
        if al <= 0:
            continue
        p = anchor("B3_02", t, name, dflt)
        if not (0.03 < p[0] < 0.97 and 0.03 < p[1] < 0.9):
            continue
        tx = p[0] - 0.26 if p[0] > 0.55 else p[0] + 0.1
        L.label(p, (max(0.04, min(0.62, tx)), max(0.3, min(0.7, p[1] + 0.2))), lines, al, accent=acc, size=0.038)
    return L.compose(img)


@ov("B7_06", no_labels=True)
def po(img, t, dur, W, H):
    L = Layer(W, H)
    L.tag((0.66, 0.06), ["High-NA 投影物镜（示意）", "约 12 吨 · 来源 ZEISS"], fade(t, 0.3), accent=VIOLET, size=0.036)
    steps = [("m5r", 0.0, 0.42, ["① 光从掩模来，落在 M5 镜环上"]),
             ("m6r", 0.42, 0.7, ["② M6 镜环把光反射、聚拢"]),
             ("wfoc", 0.7, 1.01, ["③ 会聚光穿过 M5 中心孔", "落到晶圆上一点"])]
    for name, f0, f1, lines in steps:
        al = fade(t, max(0.4, f0 * dur + 0.2), f1 * dur - 0.1, 0.3)
        if al <= 0:
            continue
        p = anchor("B7_06", t, name, (0.5, 0.5))
        L.label(p, (0.04, max(0.2, min(0.7, p[1] - 0.05))), lines, al, accent=VIOLET, size=0.034)
    e = anchor("B7_06", t, "eng", (0.85, 0.7))
    if 0.03 < e[0] < 0.97 and 0.03 < e[1] < 0.95:
        L.label(e, (min(0.84, e[0] - 0.02), max(0.45, e[1] - 0.12)), ["人 ≈ 1.8 m"], fade(t, 1.0), size=0.03)
    return L.compose(img)
