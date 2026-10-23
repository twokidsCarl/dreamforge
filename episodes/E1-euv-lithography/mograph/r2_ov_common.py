"""Shared drawing helpers for the P1 round-2 overlay layer (SCALE_E1 v2 §4 "标注层"): thin leader lines with dot
anchors, dark translucent tags, arrows, counters, circular magnifier frames. All sizes are fractions of H so
960x540 samples and 1080p finals look the same. Text goes through richtext (Sn⁸⁺, H₂, k₁, ·)."""
import json
import math
import os
import sys

from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "../../.."))
sys.path.insert(0, os.path.join(REPO, "shared/tools"))
from overlay_labels import font, serif_font, mono_font  # noqa: E402
from richtext import draw_text, text_bbox  # noqa: E402

VIOLET = (138, 92, 255)
ORANGE = (255, 138, 61)
CYAN = (63, 214, 224)
INK = (232, 236, 244)
INK2 = (170, 178, 196)
PANEL = (7, 11, 20)
FPS = 24


def ease(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def fade(t, t0, t1=None, d=0.35):
    a = ease((t - t0) / d)
    if t1 is not None:
        a = min(a, ease((t1 - t) / d))
    return a


def renders_dir():
    sys.path.insert(0, os.path.join(REPO, "shared/tools"))
    from paths import RENDERS
    return RENDERS


def anchor(sid, t, name, default):
    """Screen position (px fractions) of a named 3D point written by kit_r2.anchors(); default if missing."""
    f = int(round(t * FPS)) + 1
    p = os.path.join(renders_dir(), "shots", sid, "anchors", f"{f:04d}.json")
    try:
        with open(p) as fh:
            v = json.load(fh)[name]
        return (v[0], v[1])
    except Exception:
        return default


SERIF_BOLD = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc"


def _font(px, serif=False, mono=False):
    """serif=True: Noto Serif CJK SC regular; serif="bold": the Bold cut (R3 title card, 1C weight)."""
    if serif == "bold":
        from PIL import ImageFont
        for path in (SERIF_BOLD, "/System/Library/Fonts/Supplemental/Songti.ttc"):
            if os.path.exists(path):
                return ImageFont.truetype(path, px, index=2 if path.endswith("CJK-Bold.ttc") else 0)
        return serif_font(px)
    return serif_font(px) if serif else mono_font(px) if mono else font(px)


class Layer:
    def __init__(self, W, H):
        self.W, self.H = W, H
        self.img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.img)
        self.glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        self.g = ImageDraw.Draw(self.glow)

    def P(self, p):
        return (p[0] * self.W, p[1] * self.H)

    def s(self, v):
        return max(1, int(round(v * self.H)))

    def text(self, p, s, size=0.036, color=INK, a=1.0, anchor="la", serif=False, mono=False, shadow=True):
        if a <= 0 or not s:
            return
        f = _font(self.s(size), serif, mono)
        x, y = self.P(p)
        if shadow:
            draw_text(self.g, (x, y), s, f, fill=(0, 0, 0, int(200 * a)), anchor=anchor)
        draw_text(self.d, (x, y), s, f, fill=(*color, int(255 * a)), anchor=anchor)

    def bbox(self, p, s, size=0.036, anchor="la", serif=False, mono=False):
        f = _font(self.s(size), serif, mono)
        return text_bbox(self.d, self.P(p), s, f, anchor=anchor)

    def tag(self, p, lines, a=1.0, accent=CYAN, size=0.04, anchor="la"):
        """Dark translucent tag with an accent bar; lines = [main, (smaller second line)...]."""
        if a <= 0:
            return
        x, y = self.P(p)
        sizes = [size] + [max(0.034, size * 0.85)] * (len(lines) - 1)
        boxes, cy = [], y
        for s, sz in zip(lines, sizes):
            b = self.bbox((x / self.W, cy / self.H), s, sz)
            boxes.append((b, cy, s, sz))
            cy += self.s(sz) * 1.35
        w = max(b[2] for b, *_ in boxes) - x
        h = cy - y
        ox = {"la": 0, "ra": -w, "ma": -w / 2}[anchor]
        pad = self.s(0.012)
        ox += max(0, 0.015 * self.W + pad - (x + ox))                 # keep the tag inside the frame
        ox -= max(0, (x + ox + w + pad) - 0.985 * self.W)
        self.d.rounded_rectangle((x + ox - pad, y - pad * 0.8, x + ox + w + pad, y + h - pad * 0.2),
                                 radius=self.s(0.006), fill=(*PANEL, int(185 * a)))
        self.d.rectangle((x + ox - pad, y - pad * 0.8, x + ox - pad + self.s(0.004), y + h - pad * 0.2),
                         fill=(*accent, int(255 * a)))
        for (b, yy, s, sz), i in zip(boxes, range(len(boxes))):
            self.text(((x + ox) / self.W, yy / self.H), s, sz, INK if i == 0 else INK2, a, shadow=False)
        return (x + ox - pad, y - pad, x + ox + w + pad, y + h)

    def leader(self, a_pt, b_pt, a=1.0, color=CYAN, prog=1.0):
        if a <= 0:
            return
        (x0, y0), (x1, y1) = self.P(a_pt), self.P(b_pt)
        x1, y1 = x0 + (x1 - x0) * prog, y0 + (y1 - y0) * prog
        w = max(1, self.s(0.0022))
        self.d.line([(x0, y0), (x1, y1)], fill=(*color, int(235 * a)), width=w)
        r = self.s(0.006)
        self.d.ellipse((x0 - r, y0 - r, x0 + r, y0 + r), fill=(*color, int(255 * a)))
        self.d.ellipse((x0 - 2.2 * r, y0 - 2.2 * r, x0 + 2.2 * r, y0 + 2.2 * r), outline=(*color, int(120 * a)),
                       width=max(1, w // 2))

    def label(self, anchor_pt, tag_pt, lines, a=1.0, accent=CYAN, size=0.04):
        """Leader from a 3D anchor to a tag; the tag sits left or right of its point depending on side."""
        if a <= 0:
            return
        tag_pt = (tag_pt[0], max(0.06, min(0.78, tag_pt[1])))          # stay above the subtitle bar
        right = tag_pt[0] >= anchor_pt[0]
        self.leader(anchor_pt, tag_pt, a, accent)
        self.tag((tag_pt[0] + (0.008 if right else -0.008), tag_pt[1] - size * 0.6), lines, a, accent, size,
                 anchor="la" if right else "ra")

    def arrow(self, p0, p1, a=1.0, color=CYAN, width=0.004, head=0.018):
        if a <= 0:
            return
        (x0, y0), (x1, y1) = self.P(p0), self.P(p1)
        w = self.s(width)
        self.d.line([(x0, y0), (x1, y1)], fill=(*color, int(255 * a)), width=w)
        ang = math.atan2(y1 - y0, x1 - x0)
        hl = self.s(head)
        pts = [(x1, y1), (x1 - hl * math.cos(ang - 0.45), y1 - hl * math.sin(ang - 0.45)),
               (x1 - hl * math.cos(ang + 0.45), y1 - hl * math.sin(ang + 0.45))]
        self.d.polygon(pts, fill=(*color, int(255 * a)))
        self.g.line([(x0, y0), (x1, y1)], fill=(*color, int(120 * a)), width=w * 3)

    def compose(self, img):
        base = img.convert("RGBA")
        gl = self.glow.filter(ImageFilter.GaussianBlur(self.s(0.006)))
        base = Image.alpha_composite(base, gl)
        return Image.alpha_composite(base, self.img).convert("RGB")


def magnifier(img, center, radius, content, anchor_pt=None, a=1.0, ring=CYAN, title=None):
    """Circular magnifier inset (picks 3D / 6D): content is an RGB image drawn into a circle of `radius`
    (fraction of H) at `center` (fractions), with a ring, soft shadow and a connector to anchor_pt."""
    W, H = img.size
    if a <= 0:
        return img
    r = int(radius * H)
    cx, cy = int(center[0] * W), int(center[1] * H)
    c = content.convert("RGB").resize((2 * r, 2 * r), Image.LANCZOS)
    mask = Image.new("L", (2 * r, 2 * r), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, 2 * r - 1, 2 * r - 1), fill=int(255 * a))
    base = img.convert("RGBA")
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse((cx - r - 6, cy - r - 2, cx + r + 6, cy + r + 10), fill=(0, 0, 0, int(150 * a)))
    base = Image.alpha_composite(base, sh.filter(ImageFilter.GaussianBlur(H * 0.012)))
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    if anchor_pt:
        ax, ay = anchor_pt[0] * W, anchor_pt[1] * H
        ang = math.atan2(ay - cy, ax - cx)
        for s in (-1, 1):
            e = (cx + r * math.cos(ang + s * 0.5), cy + r * math.sin(ang + s * 0.5))
            d.line([e, (ax, ay)], fill=(*ring, int(150 * a)), width=max(1, int(H * 0.0018)))
        rr = H * 0.012
        d.ellipse((ax - rr, ay - rr, ax + rr, ay + rr), outline=(*ring, int(255 * a)), width=max(1, int(H * 0.003)))
    base = Image.alpha_composite(base, lay)
    base.paste(c, (cx - r, cy - r), mask)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(*ring, int(255 * a)), width=max(2, int(H * 0.005)))
    d.ellipse((cx - r - H * 0.01, cy - r - H * 0.01, cx + r + H * 0.01, cy + r + H * 0.01),
              outline=(*ring, int(90 * a)), width=max(1, int(H * 0.002)))
    base = Image.alpha_composite(base, lay)
    if title:
        L = Layer(W, H)
        L.tag(((cx - r * 0.7) / W, (cy + r + H * 0.02) / H), title if isinstance(title, list) else [title], a,
              ring, 0.03)
        return L.compose(base)
    return base.convert("RGB")
