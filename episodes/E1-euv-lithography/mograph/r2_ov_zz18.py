"""Round-18 overlays for r2_cutaway (P1). Loaded after r2_ov_zy17 (name sorts later); entries replace earlier ones.

R18_ROOT_CAUSE row 2 (mechanism read of the new volumetric cones - the parts the cones connect get names):
  B3_02  a small "中间焦点 IF" label where the cone closes, from the first-focus step on (R17: "only the first focus
         is labelled, the two-foci mechanism is half told")
  B5_01  one hero label in all frames ("场分面镜", R17: "25 % says pupil facet -> mask on a beam, 55 % says field
         facet"); the pupil label points AT the next mirror; position line IF -> 照明系统 -> 掩模 in the title block
  C_03   "光瞳分面镜" label on the round hexagon-array mirror (R17: new symbol without a name, near H6)
  B7_06  leader labels directly on M5 / M6 (R17: "only the top-right text says M5/M6, the viewer can't find them")
R18_ROOT_CAUSE row 5: B8_03 read-out in mm ("掩模台 → +20.0 mm · 晶圆台 ← −2.5 mm"; ruler digits in mm in 3D).
"""
import importlib.util
import os

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
    spec = importlib.util.spec_from_file_location(module + "_r18base", os.path.join(_HERE, module + ".py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


_zr8 = _mod("r2_ov_zr8")
_zu = _mod("r2_ov_zu13")
_zx = _mod("r2_ov_zx16")
_zy = _mod("r2_ov_zy17")


def _in(p, lo=0.03, hi=0.9):
    return lo < p[0] < 0.97 and lo < p[1] < hi


@ov("B3_02")
def collector(img, t, dur, W, H):
    L = Layer(W, H)
    steps = [("hole", 0.0, 0.36, ["中心孔", "CO₂ 激光从这里穿过"], CYAN, (0.45, 0.45)),
             ("plasma", 0.36, 0.62, ["第一焦点", "锡滴在这里被打成等离子体"], CYAN, (0.7, 0.4))]
    for name, f0, f1, lines, acc, dflt in steps:
        al = fade(t, max(0.3, f0 * dur + 0.2), f1 * dur - 0.1, 0.3)
        if al <= 0:
            continue
        p = anchor("B3_02", t, name, dflt)
        if not _in(p):
            continue
        tx = p[0] - 0.26 if p[0] > 0.55 else p[0] + 0.1
        L.label(p, (max(0.04, min(0.62, tx)), max(0.3, min(0.7, p[1] + 0.2))), lines, al, accent=acc, size=0.038)
    p = anchor("B3_02", t, "if", (1.2, 0.5))
    al = fade(t, 0.5, None, 0.3)
    if al > 0 and _in(p):                     # small IF tag whenever the IF is in frame (the cone closes here)
        L.label(p, (min(0.8, p[0] + 0.03), max(0.2, p[1] - 0.16)), ["中间焦点 IF"], al, accent=VIOLET, size=0.032)
    return L.compose(img)


@ov("B5_01", no_labels=True)
def illum(img, t, dur, W, H):
    L = Layer(W, H)
    L.tag((0.66, 0.06), ["照明系统（示意）", "中间焦点 IF → 照明系统 → 掩模"], fade(t, 0.3), accent=VIOLET, size=0.034)
    f = anchor("B5_01", t, "ffm", (0.55, 0.12))
    p = anchor("B5_01", t, "pfm", (0.27, 0.8))
    if _in(f, hi=0.85):                        # one hero label, all frames
        L.label(f, (min(0.74, max(0.04, f[0] + 0.1)), max(0.3, min(0.7, f[1] + 0.22))), ["场分面镜 · 切分光场"],
                fade(t, 0.3), size=0.034)
    if _in(p, hi=0.95) and abs(p[0] - f[0]) > 0.12:   # the next mirror the outgoing cone lands on
        L.label(p, (min(0.74, p[0] + 0.12), min(0.62, p[1] - 0.2)), ["下一面：光瞳分面镜"], fade(t, 0.8), size=0.03)
    return L.compose(img)


@ov("C_03", no_labels=True)
def tour(img, t, dur, W, H):
    out = _zx.tour(img, t, dur, W, H)
    L = Layer(W, H)
    a = fade(t, 0.5 * dur + 0.3, 0.7 * dur - 0.15, 0.35)
    p = anchor("C_03", t, "pfm", (1.2, 0.5))
    if a > 0 and _in(p, hi=0.85):
        L.label(p, (min(0.7, p[0] + 0.12), max(0.3, min(0.7, p[1] + 0.1))), ["光瞳分面镜"], a, accent=CYAN,
                size=0.032)
    return L.compose(out)


@ov("B7_06", no_labels=True)
def po(img, t, dur, W, H):
    out = _zy.po(img, t, dur, W, H)
    L = Layer(W, H)
    a = fade(t, 0.5)
    for key, txt, dx in (("m6h", "M6", -0.16), ("m5h", "M5", -0.16)):
        p = anchor("B7_06", t, key, (1.2, 0.5))
        if _in(p, hi=0.95):
            L.label(p, (max(0.04, p[0] + dx), p[1] - 0.02), [txt], a, accent=VIOLET, size=0.03)
    return L.compose(out)


def _lerp(a, b, u):
    return (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u)


@ov("B8_03", no_labels=True)
def scan(img, t, dur, W, H):
    from PIL import Image, ImageDraw, ImageFilter
    n = max(2, round(dur * FPS))
    f = int(round(t * FPS)) + 1
    u = _zr8.scan_u(f, n)
    w = round(u, 2)
    r = 8 * w
    a = fade(t, 0.3)
    w0, w1 = anchor("B8_03", t, "wr0", (0.55, 0.9)), anchor("B8_03", t, "wr1", (0.45, 0.9))
    wc = _lerp(w0, w1, u)
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
    # R18 row 5: travel in millimetres (1 ruler division = 10 mm, schematic) - strict 8 : 1 kept
    rm, wm = r * 10, w * 10
    wr = "0.0" if w == 0 else f"−{wm:.1f}"
    L.tag((PB[0], PB[3] + 0.025), [f"行程：掩模台 → +{rm:.1f} mm · 晶圆台 ← {wr} mm",
                                   "恒 8 : 1 · 缩小 8× · 入射 5.4°（放大示意）"], a, size=0.03)
    return L.compose(out)
