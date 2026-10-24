#!/usr/bin/env python3
"""fix_v6 render library: clamped camera (no reflect borders), image-space overlays that
track the camera, sprites (ions / chips / knowledge cards), frame-exact writer.

Rules baked in (Carl t353–t366):
- camera viewport is clamped inside the plate → no mirrored flagella / top streak artifacts
- overlays are defined in plate fractions and mapped through the same camera → ions stay on pores
- knowledge chips live in screen space (top-left), never burned into the plate
"""
from __future__ import annotations
import math, subprocess
from functools import lru_cache
from pathlib import Path
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1280, 720, 24
SANS_B = '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'
SANS_R = '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
GEN = Path('/workspace/e2work/v8/gen')
BRAND = Path('/workspace/eigenlens/brand/eigenlens_logo_locked')

MINT = (99, 199, 168); GOLD = (233, 184, 92); CYAN = (90, 200, 255); AMBER = (255, 150, 60)
YELLOW = (255, 214, 90); INK = (11, 16, 34); CREAM = (244, 239, 230); PURPLE = (176, 120, 255)
NA = (110, 215, 255); KION = (255, 170, 70); HION = (255, 236, 150); RED = (255, 96, 96)


def ease(t):
    t = min(max(t, 0.0), 1.0)
    return t * t * (3 - 2 * t)


def ramp(t, a, b):
    if b <= a:
        return float(t >= a)
    return ease((t - a) / (b - a))


def win(t, a, b, fi=0.35, fo=0.35):
    """1 inside [a,b] with eased fades."""
    return min(ramp(t, a, a + fi), 1 - ramp(t, b - fo, b))


def font(sz, bold=True):
    return _font(sz, bold)


@lru_cache(maxsize=64)
def _font(sz, bold):
    return ImageFont.truetype(SANS_B if bold else SANS_R, sz)


# ---------------------------------------------------------------- plates & camera
class Plate:
    def __init__(self, path, crop=None, work=1.35):
        im = Image.open(path).convert('RGB')
        if crop:
            x0, y0, x1, y1 = crop
            im = im.crop((int(x0 * im.width), int(y0 * im.height), int(x1 * im.width), int(y1 * im.height)))
        s = max(W / im.width, H / im.height) * work
        im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)
        self.img = np.asarray(im).astype(np.float32) / 255.0
        self.h, self.w = self.img.shape[:2]
        self.s0 = max(W / self.w, H / self.h)

    def M(self, z, cx, cy):
        s = self.s0 * z
        vw, vh = W / s, H / s
        x0 = min(max(cx * self.w - vw / 2, 0.0), self.w - vw)
        y0 = min(max(cy * self.h - vh / 2, 0.0), self.h - vh)
        return np.array([[s, 0, -s * x0], [0, s, -s * y0]], np.float32), s

    def cam(self, z, cx=0.5, cy=0.5):
        M, s = self.M(z, cx, cy)
        frame = cv2.warpAffine(self.img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        return frame, View(M, s, self)

    def warp_mask(self, mask, view):
        return cv2.warpAffine(mask, view.M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)


class View:
    def __init__(self, M, s, plate):
        self.M, self.s, self.p = M, s, plate

    def pt(self, fx, fy):
        return (self.M[0, 0] * fx * self.p.w + self.M[0, 2], self.M[1, 1] * fy * self.p.h + self.M[1, 2])

    def px(self, frac_w):
        """plate-width fraction → screen pixels"""
        return frac_w * self.p.w * self.s


def hue_mask(plate, hlo, hhi, smin=90, vmin=90, blur=9, region=None):
    hsv = cv2.cvtColor((plate.img * 255).astype(np.uint8), cv2.COLOR_RGB2HSV)
    h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    if hlo <= hhi:
        m = (h >= hlo) & (h <= hhi)
    else:
        m = (h >= hlo) | (h <= hhi)
    m = (m & (s >= smin) & (v >= vmin)).astype(np.float32)
    if region is not None:
        x0, y0, x1, y1 = region
        r = np.zeros_like(m)
        r[int(y0 * plate.h):int(y1 * plate.h), int(x0 * plate.w):int(x1 * plate.w)] = 1
        m *= r
    k = blur | 1
    return cv2.GaussianBlur(m, (k, k), 0)


def disc_mask(plate, centers, rad_frac, soft=0.5):
    yy, xx = np.mgrid[0:plate.h, 0:plate.w].astype(np.float32)
    m = np.zeros((plate.h, plate.w), np.float32)
    r = rad_frac * plate.w
    for cx, cy in centers:
        d = np.sqrt((xx - cx * plate.w) ** 2 + (yy - cy * plate.h) ** 2)
        m = np.maximum(m, np.clip((r - d) / (r * soft), 0, 1))
    return m


# ---------------------------------------------------------------- compositing
def add_glow(rgb, mask, color, amt):
    if amt <= 1e-4:
        return rgb
    c = np.asarray(color, np.float32) / 255.0
    return rgb + mask[..., None] * c * amt


def tint(rgb, mask, color, amt):
    """recolor masked region toward color, keeping luminance"""
    if amt <= 1e-4:
        return rgb
    c = np.asarray(color, np.float32) / 255.0
    lum = (rgb * np.array([0.3, 0.55, 0.15], np.float32)).sum(-1, keepdims=True)
    tgt = np.clip(lum * c / max(float((c * np.array([0.3, 0.55, 0.15])).sum()), 1e-3), 0, 1.4)
    a = (mask * amt)[..., None]
    return rgb * (1 - a) + tgt * a


def dim(rgb, mask, amt, desat=0.6):
    if amt <= 1e-4:
        return rgb
    lum = (rgb * np.array([0.3, 0.55, 0.15], np.float32)).sum(-1, keepdims=True)
    g = rgb * (1 - desat) + lum * desat
    a = (mask * amt)[..., None]
    return rgb * (1 - a) + g * 0.35 * a


def radial(x, y, r, color, amt):
    if amt <= 1e-4:
        return None
    x0, x1 = int(max(0, x - 3 * r)), int(min(W, x + 3 * r))
    y0, y1 = int(max(0, y - 3 * r)), int(min(H, y + 3 * r))
    if x1 <= x0 or y1 <= y0:
        return None
    yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    d = np.exp(-((xx - x) ** 2 + (yy - y) ** 2) / (2 * r * r))
    return (x0, y0, x1, y1, d[..., None] * (np.asarray(color, np.float32) / 255.0) * amt)


def add_radial(rgb, x, y, r, color, amt):
    g = radial(x, y, r, color, amt)
    if g is not None:
        x0, y0, x1, y1, d = g
        rgb[y0:y1, x0:x1] += d
    return rgb


def paste(rgb, spr, x, y, alpha=1.0, center=True):
    """alpha-composite RGBA float sprite at (x,y)."""
    if alpha <= 1e-3:
        return rgb
    sh, sw = spr.shape[:2]
    if center:
        x, y = x - sw / 2, y - sh / 2
    x, y = int(round(x)), int(round(y))
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(W, x + sw), min(H, y + sh)
    if x1 <= x0 or y1 <= y0:
        return rgb
    sub = spr[y0 - y:y1 - y, x0 - x:x1 - x]
    a = sub[..., 3:4] * alpha
    rgb[y0:y1, x0:x1] = rgb[y0:y1, x0:x1] * (1 - a) + sub[..., :3] * a
    return rgb


def paste_add(rgb, spr, x, y, alpha=1.0):
    sh, sw = spr.shape[:2]
    x, y = int(round(x - sw / 2)), int(round(y - sh / 2))
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(W, x + sw), min(H, y + sh)
    if x1 <= x0 or y1 <= y0:
        return rgb
    sub = spr[y0 - y:y1 - y, x0 - x:x1 - x]
    rgb[y0:y1, x0:x1] += sub[..., :3] * sub[..., 3:4] * alpha
    return rgb


def pil_rgba(im):
    return np.asarray(im.convert('RGBA')).astype(np.float32) / 255.0


# ---------------------------------------------------------------- sprites
@lru_cache(maxsize=256)
def ion_sprite(r, color, label='', glow=True):
    """shaded sphere with soft halo; label like 'Na⁺' drawn small on it."""
    r = max(3, int(r))
    S = 4
    pad = r * 2 if glow else 2
    size = (2 * r + 2 * pad) * S
    im = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    arr = np.zeros((size, size, 4), np.float32)
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32)
    cx = cy = size / 2
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / S
    c = np.asarray(color, np.float32) / 255.0
    if glow:
        halo = np.exp(-((d / (r * 1.6)) ** 2)) * 0.55
        arr[..., :3] = c
        arr[..., 3] = halo
    inside = np.clip(r - d + 0.5, 0, 1)
    # lambert-ish shading with highlight
    lx, ly = -0.45, -0.55
    nx = (xx - cx) / (r * S); ny = (yy - cy) / (r * S)
    nz = np.sqrt(np.clip(1 - nx ** 2 - ny ** 2, 0, 1))
    shade = np.clip(0.55 + 0.6 * (nx * lx + ny * ly + nz * 0.7), 0.25, 1.25)
    spec = np.clip((nx * lx + ny * ly + nz * 0.7) - 0.75, 0, 1) * 2.2
    body = np.clip(c[None, None, :] * shade[..., None] + spec[..., None], 0, 1)
    rim = np.clip((d - (r - 1.4)) / 1.4, 0, 1) * inside
    body = body * (1 - 0.45 * rim[..., None])
    arr[..., :3] = arr[..., :3] * (1 - inside[..., None]) + body * inside[..., None]
    arr[..., 3] = np.maximum(arr[..., 3], inside)
    im = Image.fromarray((arr * 255).astype(np.uint8), 'RGBA')
    if label:
        dr = ImageDraw.Draw(im)
        f = _font(int(r * 1.05 * S), True)
        tw = f.getlength(label)
        dr.text((cx - tw / 2, cy - r * 0.78 * S), label, font=f, fill=(11, 16, 34, 235))
    im = im.resize((size // S, size // S), Image.LANCZOS)
    return pil_rgba(im)


@lru_cache(maxsize=256)
def text_sprite(text, size, color=CREAM, bold=True, shadow=True, spacing=0):
    f = _font(size, bold)
    if spacing:
        tw = int(sum(f.getlength(ch) + spacing for ch in text))
    else:
        tw = int(f.getlength(text))
    pad = 8
    im = Image.new('RGBA', (tw + 2 * pad, int(size * 1.45) + 2 * pad), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)

    def draw(dx, dy, fill):
        if spacing:
            x = pad + dx
            for ch in text:
                d.text((x, pad + dy), ch, font=f, fill=fill)
                x += f.getlength(ch) + spacing
        else:
            d.text((pad + dx, pad + dy), text, font=f, fill=fill)
    if shadow:
        sh = Image.new('RGBA', im.size, (0, 0, 0, 0))
        d2 = ImageDraw.Draw(sh)
        d, dsave = d2, d
        draw(0, 2, (0, 0, 0, 200))
        d = dsave
        from PIL import ImageFilter
        sh = sh.filter(ImageFilter.GaussianBlur(2.5))
        im = Image.alpha_composite(sh, im)
        d = ImageDraw.Draw(im)
    draw(0, 0, tuple(color) + (255,))
    return pil_rgba(im)


@lru_cache(maxsize=128)
def chip_sprite(text, accent=MINT, sub=''):
    """knowledge-layer chip: readable 22px, glass bg, accent bar. Screen space only."""
    f = _font(22, True); fs = _font(16, False)
    tw = int(f.getlength(text)); sw = int(fs.getlength(sub)) if sub else 0
    w = max(tw, sw) + 34
    h = 40 if not sub else 64
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, h - 1), radius=7, fill=(11, 16, 34, 175), outline=tuple(accent) + (110,), width=1)
    d.rounded_rectangle((0, 0, 5, h - 1), radius=3, fill=tuple(accent) + (255,))
    d.text((17, 5), text, font=f, fill=CREAM + (255,))
    if sub:
        d.text((17, 37), sub, font=fs, fill=(200, 210, 225, 255))
    return pil_rgba(im)


def chip(rgb, text, t, a, b, accent=MINT, sub='', x=36, y=30):
    al = win(t, a, b, 0.3, 0.3)
    if al > 0:
        spr = chip_sprite(text, tuple(accent), sub)
        paste(rgb, spr, x - 8 * (1 - al), y, al, center=False)
    return rgb


def card_base(w, h, accent=GOLD):
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, h - 1), radius=14, fill=(12, 18, 38, 236), outline=tuple(accent) + (230,), width=2)
    return im, d


def card(rgb, spr, x, y, t, a, b, target=None, accent=GOLD, anchor='left'):
    """paste knowledge card (top-left at x,y) with fade/slide; optional leader line to target point."""
    al = win(t, a, b, 0.45, 0.4)
    if al <= 0:
        return rgb
    sh, sw = spr.shape[:2]
    dx = (1 - al) * (-24 if anchor == 'left' else 24)
    if target is not None:
        ov = np.zeros((H, W, 4), np.float32)
        ex = x + dx + (sw if target[0] > x + sw / 2 else 0)
        ex = min(max(target[0], x + dx), x + dx + sw) if y <= target[1] <= y + sh else ex
        ey = min(max(target[1], y + 18), y + sh - 18)
        if y <= target[1] <= y + sh:
            ex = x + dx + (sw if target[0] > x + sw else 0)
        c = tuple(float(v) / 255 for v in accent) + (0.95 * al,)
        cv2.line(ov, (int(ex), int(ey)), (int(target[0]), int(target[1])), c, 2, cv2.LINE_AA)
        cv2.circle(ov, (int(target[0]), int(target[1])), 7, c, 2, cv2.LINE_AA)
        cv2.circle(ov, (int(target[0]), int(target[1])), 3, c, -1, cv2.LINE_AA)
        a_ = ov[..., 3:4]
        rgb[:] = rgb * (1 - a_) + ov[..., :3] * a_
    paste(rgb, spr, x + dx, y, al, center=False)
    return rgb


def overlay_layer():
    return np.zeros((H, W, 4), np.float32)


def comp(rgb, ov):
    a = ov[..., 3:4]
    return rgb * (1 - a) + ov[..., :3] * a


def col(c, a=1.0):
    return (c[0] / 255.0, c[1] / 255.0, c[2] / 255.0, float(a))


# ---------------------------------------------------------------- particles
def stream(t, n, path_fn, rate, seed=0):
    """deterministic particles; path_fn(u, k) -> (x,y,alpha) in screen space for u in [0,1)."""
    out = []
    rng = np.random.RandomState(seed)
    offs = rng.rand(n)
    for k in range(n):
        u = (t * rate + offs[k]) % 1.0
        out.append(path_fn(u, k))
    return out


# ---------------------------------------------------------------- writer
def write_segment(out, f0, f1, frame_fn, crf=17):
    n = f1 - f0
    cmd = ['ffmpeg', '-loglevel', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
           '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', str(crf),
           '-threads', '2', '-pix_fmt', 'yuv420p', '-r', str(FPS), str(out)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(f0, f1):
        rgb = frame_fn(i / FPS)
        p.stdin.write((np.clip(rgb, 0, 1) * 255 + 0.5).astype(np.uint8).tobytes())
    p.stdin.close()
    assert p.wait() == 0
    return n


def draw_rich(d, xy, text, size, fill, bold=False):
    """draw text where _{..} is subscript and ^{..} superscript (Noto CJK lacks ₂⁺ glyphs)."""
    import re
    x, y = xy
    f = _font(size, bold); fs = _font(int(size * 0.62), bold)
    for m in re.finditer(r'_\{([^}]*)\}|\^\{([^}]*)\}|([^_^]+)', text):
        if m.group(3):
            d.text((x, y), m.group(3), font=f, fill=fill); x += f.getlength(m.group(3))
        elif m.group(1):
            d.text((x, y + size * 0.48), m.group(1), font=fs, fill=fill); x += fs.getlength(m.group(1))
        else:
            d.text((x, y - size * 0.08), m.group(2), font=fs, fill=fill); x += fs.getlength(m.group(2))
    return x
