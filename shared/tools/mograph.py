"""Small 2D motion-graphics kit for the infographic / type / blueprint-2D shots.

Every graphic is a function draw(t, dur, W, H) -> PIL.Image (t in seconds). The design system
matches the 3D looks: EUV violet, laser orange, metrology cyan, line white, Noto/Heiti type.

  python3 tools/mograph.py --shot B1_27 [--quality preview|final]

renders frames to renders/shots/<id>/<quality>/####.png like the Blender shots, so the story
reel and the edit treat both the same way. Shot functions live in episodes/<episode>/mograph/*.py and
register themselves with @shot("B1_27").
"""
import argparse
import glob
import importlib.util
import math
import os
import sys

from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(__file__))
from overlay_labels import font  # noqa: E402

from paths import AUDIO, EP, REPO, RENDERS, SHARED  # noqa: E402,F401
RENDERS = RENDERS
FPS = 24
SIZES = {"preview": (640, 360), "sample": (960, 540), "final": (1920, 1080)}

# design tokens (sRGB)
INK = (236, 238, 244)
INK2 = (150, 158, 182)
BG = (8, 10, 16)
VIOLET = (164, 128, 255)
ORANGE = (255, 138, 61)
CYAN = (60, 200, 220)
BLUE_BG = (12, 52, 122)
BLUE_GRID = (40, 88, 160)
LINE = (220, 235, 255)

REGISTRY = {}


def shot(sid):
    def wrap(fn):
        REGISTRY[sid] = fn
        return fn
    return wrap


# ---- timing helpers ------------------------------------------------------------------------
def clamp01(x):
    return max(0.0, min(1.0, x))


def ease(x):
    x = clamp01(x)
    return x * x * (3 - 2 * x)


def ease_out(x):
    x = clamp01(x)
    return 1 - (1 - x) ** 3


def seg(t, a, b):
    """Progress 0..1 of t through [a, b]."""
    return clamp01((t - a) / (b - a)) if b > a else float(t >= a)


def fade(t, a, b, dur, f=0.35):
    """1 inside [a, b] with soft edges of f seconds; 0 outside."""
    return ease(seg(t, a, a + f)) * (1 - ease(seg(t, b - f, b))) if b < dur else ease(seg(t, a, a + f))


# ---- drawing helpers -----------------------------------------------------------------------
class Canvas:
    def __init__(self, W, H, bg=BG):
        self.W, self.H = W, H
        self.k = H / 1080
        self.img = Image.new("RGB", (W, H), bg)
        self.glow = Image.new("RGB", (W, H), (0, 0, 0))
        self.d = ImageDraw.Draw(self.img, "RGBA")
        self.g = ImageDraw.Draw(self.glow)

    def px(self, v):
        return v * self.k

    def text(self, xy, s, size, color=INK, a=1.0, anchor="la", weight_glow=False):
        if a <= 0:
            return
        f = font(int(self.px(size)))
        x, y = self.px(xy[0]), self.px(xy[1])
        self.d.text((x, y), s, font=f, fill=(*color, int(255 * a)), anchor=anchor)
        if weight_glow:
            self.g.text((x, y), s, font=f, fill=tuple(int(c * a * 0.6) for c in color), anchor=anchor)

    def line(self, p0, p1, color=LINE, width=2, a=1.0, progress=1.0, glow=False):
        if a <= 0 or progress <= 0:
            return
        x0, y0 = self.px(p0[0]), self.px(p0[1])
        x1, y1 = self.px(p1[0]), self.px(p1[1])
        x1, y1 = x0 + (x1 - x0) * progress, y0 + (y1 - y0) * progress
        self.d.line([(x0, y0), (x1, y1)], fill=(*color, int(255 * a)), width=max(1, int(self.px(width))))
        if glow:
            self.g.line([(x0, y0), (x1, y1)], fill=tuple(int(c * a) for c in color),
                        width=max(1, int(self.px(width * 3))))

    def rect(self, box, fill=None, outline=None, width=2, a=1.0, glow=False, radius=0):
        if a <= 0:
            return
        b = [self.px(v) for v in box]
        kw = {}
        if fill:
            kw["fill"] = (*fill, int(255 * a))
        if outline:
            kw["outline"] = (*outline, int(255 * a))
            kw["width"] = max(1, int(self.px(width)))
        self.d.rounded_rectangle(b, radius=self.px(radius), **kw)
        if glow and fill:
            self.g.rounded_rectangle(b, radius=self.px(radius), fill=tuple(int(c * a) for c in fill))

    def circle(self, c, r, fill=None, outline=None, width=2, a=1.0, glow=False):
        if a <= 0 or r <= 0:
            return
        x, y, rr = self.px(c[0]), self.px(c[1]), self.px(r)
        kw = {}
        if fill:
            kw["fill"] = (*fill, int(255 * a))
        if outline:
            kw["outline"] = (*outline, int(255 * a))
            kw["width"] = max(1, int(self.px(width)))
        self.d.ellipse([x - rr, y - rr, x + rr, y + rr], **kw)
        if glow:
            self.g.ellipse([x - rr, y - rr, x + rr, y + rr], fill=tuple(int(cc * a) for cc in (fill or outline)))

    def grid(self, step=60, color=BLUE_GRID, a=0.6, major=5):
        for i, x in enumerate(range(0, int(1920) + 1, step)):
            self.line((x, 0), (x, 1080), color=color, width=2 if i % major == 0 else 1, a=a * (1 if i % major == 0 else 0.5))
        for i, y in enumerate(range(0, 1080 + 1, step)):
            self.line((0, y), (1920, y), color=color, width=2 if i % major == 0 else 1, a=a * (1 if i % major == 0 else 0.5))

    def finish(self, glow_radius=14, glow_gain=1.0, vignette=True):
        from PIL import ImageChops
        g = self.glow.filter(ImageFilter.GaussianBlur(self.px(glow_radius)))
        out = ImageChops.add(self.img, Image.eval(g, lambda v: min(255, int(v * glow_gain))))
        if vignette:
            vg = Image.radial_gradient("L").resize((self.W, self.H)).point(lambda v: 255 - int(v * 0.45))
            out = Image.composite(out, Image.new("RGB", out.size, (0, 0, 0)), vg)
        return out


def counter(value, digits_from=0, fmt="{:,.0f}"):
    return fmt.format(value)


def load_shots():
    for p in sorted(glob.glob(os.path.join(EP, "mograph/*.py"))):
        spec = importlib.util.spec_from_file_location(os.path.basename(p)[:-3], p)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)


def shot_duration(sid):
    import yaml
    sb = yaml.safe_load(open(os.path.join(EP, "storyboard/storyboard.timed.yaml"), encoding="utf-8"))
    return next(s["duration"] for s in sb["shots"] if s["id"] == sid)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shot", nargs="+", required=True)
    ap.add_argument("--quality", choices=list(SIZES), default="preview")
    ap.add_argument("--frames", help="comma-separated 1-based frames")
    a = ap.parse_args()
    load_shots()
    import mograph  # shot files register into the importable module, not __main__
    registry = mograph.REGISTRY
    W, H = SIZES[a.quality]
    for sid in a.shot:
        dur = shot_duration(sid)
        n = max(1, round(dur * FPS))
        out = os.path.join(RENDERS, "shots", sid, a.quality)
        os.makedirs(out, exist_ok=True)
        frames = [int(f) for f in a.frames.split(",")] if a.frames else range(1, n + 1)
        for f in frames:
            registry[sid]((f - 1) / FPS, dur, W, H).save(os.path.join(out, f"{f:04d}.png"))
        print(f"[mograph] {sid} {len(list(frames))} frames {W}x{H}")


if __name__ == "__main__":
    main()
