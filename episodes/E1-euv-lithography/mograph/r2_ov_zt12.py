"""Round-12 overlays (P1). Loaded after r2_ov_zs10* (name sorts last), so entries here replace earlier ones.

B8_03 (R12 rebuild around the wafer stage): the main render is the wafer stage; the reticle stage comes from the
picture-in-picture pass of the same scene and frame (renders/shots/B8_03M/<src>/####.png, camera CamR2M) pasted
top-right, with its own progress line from the B8_03M anchors. Read-outs come from the same scan knots as the
stage keyframes (2.00 / 0.25, 4.40 / 0.55, 6.80 / 0.85 - a steady 8 : 1). The wafer-ruler inset is labelled
"晶圆台标尺（放大显示）" (R11: "x4" read as a 4x reduction). <= 3 text blocks."""
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
    spec = importlib.util.spec_from_file_location(module + "_r12base", os.path.join(_HERE, module + ".py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


_misc = _mod("r2_ov_misc")
_zr8 = _mod("r2_ov_zr8")

PIP_BOX = (0.585, 0.035, 0.975, 0.395)          # frame fractions (x0, y0, x1, y1)
PIP_CROP = (0.0, 0.1, 1.0, 0.82)                # part of the B8_03M frame shown (ruler + carriage + mask V)


def _pip_frame(f):
    for src in ("sample", "preview"):
        p = os.path.join(renders_dir(), "shots", "B8_03M", src, f"{f:04d}.png")
        if os.path.exists(p):
            return Image.open(p).convert("RGB")
    return None


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
    wc = _lerp(w0, w1, u)
    # wafer-ruler inset (real pixels of this frame), bottom left, clear of the subtitle band
    if a > 0:
        cx, cy = (w0[0] + w1[0]) / 2 * W, wc[1] * H
        half = 0.04 * H
        box = (int(cx - half), int(cy - half), int(cx + half), int(cy + half))
        if box[0] > 0 and box[1] > 0 and box[2] < W and box[3] < H:
            crop = img.crop(box).resize((int(half * 8), int(half * 8)), Image.LANCZOS)
            img = _misc.magnifier(img, (0.1, 0.6), 0.115, crop, a, anchor=(cx / W, cy / H))
    # picture-in-picture: the reticle stage at the same instant
    pip = _pip_frame(f)
    out = img.convert("RGBA")
    x0, y0, x1, y1 = (int(PIP_BOX[0] * W), int(PIP_BOX[1] * H), int(PIP_BOX[2] * W), int(PIP_BOX[3] * H))
    if pip is not None and a > 0:
        pw, ph = pip.size
        c = pip.crop((int(PIP_CROP[0] * pw), int(PIP_CROP[1] * ph), int(PIP_CROP[2] * pw), int(PIP_CROP[3] * ph)))
        c = c.resize((x1 - x0, y1 - y0), Image.LANCZOS)
        sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(sh).rectangle((x0 - 4, y0 + 2, x1 + 6, y1 + 10), fill=(0, 0, 0, int(150 * a)))
        out = Image.alpha_composite(out, sh.filter(ImageFilter.GaussianBlur(H * 0.01)))
        m = Image.new("L", c.size, int(255 * a))
        out.paste(c, (x0, y0), m)
    L = Layer(W, H)
    lw = max(3, int(H * 0.006))
    if pip is not None:
        L.d.rectangle((x0, y0, x1, y1), outline=(*CYAN, int(230 * a)), width=max(2, int(H * 0.004)))

        def to_pip(p):
            px = (p[0] - PIP_CROP[0]) / (PIP_CROP[2] - PIP_CROP[0])
            py = (p[1] - PIP_CROP[1]) / (PIP_CROP[3] - PIP_CROP[1])
            return (PIP_BOX[0] + px * (PIP_BOX[2] - PIP_BOX[0]), PIP_BOX[1] + py * (PIP_BOX[3] - PIP_BOX[1]))
        r0 = to_pip(anchor("B8_03M", t, "rr0", (0.15, 0.3)))
        r1 = to_pip(anchor("B8_03M", t, "rr1", (0.85, 0.3)))
        rc = _lerp(r0, r1, u)
        L.d.line([L.P(r0), L.P(rc)], fill=(*CYAN, int(230 * a)), width=lw)
        L.g.line([L.P(r0), L.P(rc)], fill=(*CYAN, int(150 * a)), width=lw * 3)
        L.tag((PIP_BOX[0], PIP_BOX[3] + 0.012), ["掩模台 · 同一时刻"], a, size=0.028)
    L.d.line([L.P(w0), L.P(wc)], fill=(*CYAN, int(230 * a)), width=lw)
    L.g.line([L.P(w0), L.P(wc)], fill=(*CYAN, int(150 * a)), width=lw * 3)
    L.tag((0.03, 0.05), [f"掩模台 → {r:.2f} 格", f"← 晶圆台 {w:.2f} 格（反向）· 恒 8 : 1",
                         "High-NA 缩小 8× · 入射约 5.4°（角度放大示意）"], a, size=0.034)
    L.text((0.1, 0.6 + 0.135), "晶圆台标尺（放大显示）", 0.026, INK2, fade(t, 0.5), anchor="ma")
    return L.compose(out)
