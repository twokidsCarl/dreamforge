"""Round-30 overlay for B8_03 (kit agent; rides on the R30_ROOT_CAUSE row 6 structural change scripts/cut_kit_r30.py
RULER_R30: wafer-stage ruler in its own screen space + alignment cross moving with the wafer).
R29 p2 B8_03 「读数框放在画面左中，要挪到右上，压到 2 行以内」: same r2_ov_zz18 'scan' drawing with the r2_ov_zz23b
full-width PIP band (unchanged), only the two-line read-out tag moves from the left-middle (under the PIP's left end,
where the 3D wafer ruler now sits) to the right end directly under the PIP (top right of the open frame).
Active only while B8_03 is in r2_cutaway.R30_KIT and ENABLED -> a revert also reverts this."""
import importlib.util
import os
import re

from r2_ov_common import CYAN, FPS, Layer, anchor, fade

ENABLED = True
OVERLAYS = {}
NO_STORYBOARD_LABELS = set()
_HERE = os.path.dirname(os.path.abspath(__file__))


def _set(module, name):
    try:
        src = open(os.path.join(_HERE, "..", "blender", "shots", module + ".py"), encoding="utf-8").read()
        m = re.search(r"^" + name + r"\s*=\s*\{([^}]*)\}", src, re.M)
        return set(re.findall(r"\"([A-Z0-9_]+)\"", m.group(1))) if m else set()
    except OSError:
        return set()


def _mod(module):
    spec = importlib.util.spec_from_file_location(module + "_r30kbase", os.path.join(_HERE, module + ".py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _lerp(a, b, u):
    return (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u)


if ENABLED and "B8_03" in _set("r2_cutaway", "R30_KIT") and "B8_03" in _set("r2_cutaway", "R23_2B"):
    _z23 = _mod("r2_ov_zz23b")
    _z18 = _z23._z18                     # zz18 instance with the zz23b full-width PIP band
    _zu, _zr8 = _z18._zu, _z18._zr8

    def scan30(img, t, dur, W, H):
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
            c = pip.crop((int(PC[0] * pw), int(PC[1] * ph), int(PC[2] * pw), int(PC[3] * ph))).resize(
                (x1 - x0, y1 - y0), Image.LANCZOS)
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
        rm, wm = r * 10, w * 10
        wr = "0.0" if w == 0 else f"−{wm:.1f}"
        # R30 row 6: read-out tag top right (right end, just under the PIP band), still two lines
        L.tag((PB[2], PB[3] + 0.025), [f"行程：掩模台 → +{rm:.1f} mm · 晶圆台 ← {wr} mm",
                                       "恒 8 : 1 · 缩小 8× · 入射 5.4°（放大示意）"], a, size=0.03, anchor="ra")
        return L.compose(out)

    OVERLAYS["B8_03"] = scan30
    NO_STORYBOARD_LABELS.add("B8_03")
