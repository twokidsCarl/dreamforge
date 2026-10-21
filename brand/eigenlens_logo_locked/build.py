#!/usr/bin/env python3
"""EigenLens locked brand: programmatic 1:1 redraw of 03s6_amber_gold.png.

Every number below was measured from the reference PNG (1254x1254), not
eyeballed: rings/lens circles are least-squares fits to ridge pixels, the
brackets are line fits to stroke edges, the crescent fills are radial
gradients fitted to the source pixels, and the wordmark glyphs are placed on
the source glyph boxes. Coordinates are in reference pixels, so a lockup
render at 1254x1254 lays directly over the source for the diff check.

SVG is the single source of truth. Headless Chrome rasterizes it (exact SVG
filters/gradients); Pillow + numpy composite the sting frames; ffmpeg encodes.

    python3 build.py            # build everything
    python3 build.py --stills   # SVG + PNG stills + diff only (fast)

Needs: google-chrome, ffmpeg, Pillow, numpy, fontTools, and the reference PNG
for the diff step (path below; override with EIGENLENS_REF).
"""
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
REF = Path(os.environ.get(
    "EIGENLENS_REF", "/workspace/eigenlens-logo-v2/color-03-strict/03s6_amber_gold.png"))
FONT_EN = "/usr/share/fonts/truetype/sand-box/google/Outfit/Outfit-VariableFont_wght.ttf"
FONT_EN_WGHT = 150
# Noto Sans SC variable (OFL, google/fonts), subset to the four glyphs; see fonts/OFL.txt
FONT_CN = str(HERE / "fonts" / "NotoSansSC-wght-subset-zhuguanzhishi.ttf")
FONT_CN_WGHT = 320
FPS = 24
CHROME = shutil.which("google-chrome") or shutil.which("chromium") or "google-chrome"

# --------------------------------------------------------------------------
# Measured geometry (reference px). Ellipses are (cx, cy, rx, ry): the source
# is a generated image and its circles are slightly out of round / off-centre;
# keeping that is what makes the overlay line up.
# --------------------------------------------------------------------------
G = {
    "outer":  (625.09, 486.07, 255.17, 252.18),
    "dotted": (625.56, 485.41, 229.98, 228.64),
    "mid":    (625.79, 484.75, 198.54, 198.10),
    "inner":  (626.11, 487.00, 60.62, 60.49),
    "lensL":  (589.10, 484.87, 157.42, 153.89),
    "lensR":  (662.68, 484.86, 157.36, 153.82),
}
CX, CY = 626.6, 487.6          # crosshair / centre point
HLINE = (314.0, 938.0)         # horizontal axis extent
VLINE = (197.5, 772.5)         # vertical axis extent
# Dotted ring: every dot at its measured angle (deg, CCW from 3 o'clock). The
# source pitch wanders between ~2.0 and ~2.9 deg, so a uniform grid drifts off.
# No dots at 0/180 deg: the axis nodes sit there.
DOT_ANGLES = [2.9, 5.4, 8.0, 10.7, 13.1, 15.6, 18.1, 20.8, 23.3, 25.7, 28.2, 30.9, 33.4, 36.1, 38.6, 41.2, 43.7, 46.4, 48.9, 51.5, 54.1, 56.9, 59.9, 62.7, 65.5, 68.4, 71.2, 73.8, 76.5, 79.3, 81.9, 84.6, 87.2, 89.7, 92.2, 94.9, 97.4, 100.4, 103.3, 105.8, 108.3, 110.7, 113.2, 115.7, 118.3, 120.7, 123.3, 125.8, 128.4, 131.0, 133.5, 136.1, 138.6, 141.3, 143.8, 146.4, 149.2, 151.7, 154.1, 156.6, 159.2, 161.8, 164.4, 166.9, 169.4, 172.1, 174.6, 177.2, 183.8, 186.3, 188.8, 191.3, 193.9, 196.4, 198.7, 201.0, 203.5, 205.8, 208.1, 210.3, 212.4, 214.5, 216.8, 219.1, 221.4, 223.8, 226.3, 228.9, 231.4, 234.1, 236.7, 239.3, 241.9, 244.4, 246.9, 249.5, 252.0, 254.5, 257.1, 259.7, 262.3, 264.9, 267.5, 270.1, 272.8, 275.4, 278.0, 280.6, 283.3, 285.9, 288.6, 291.2, 293.8, 296.4, 299.1, 301.6, 304.1, 306.4, 308.9, 311.4, 313.8, 316.2, 318.6, 321.1, 323.2, 325.6, 327.8, 329.8, 331.8, 334.2, 336.5, 338.9, 341.2, 343.5, 346.0, 348.6, 351.2, 353.8, 356.2]

# Bracket stroke edges as x = a + b*y (outer/inner edge, upper/lower arm);
# ends are cut horizontally at Y_TOP / Y_BOT.
BRACKETS = {
    "L": {"up_o": (529.96, -0.5830), "up_i": (541.78, -0.5840),
          "lo_o": (-33.41, 0.5732), "lo_i": (-22.05, 0.5730)},
    "R": {"up_o": (726.94, 0.5679), "up_i": (715.74, 0.5683),
          "lo_o": (1283.85, -0.5742), "lo_i": (1272.24, -0.5735)},
}
Y_TOP, Y_BOT = 318.6, 652.4
TEXT_HALO = (610.0, 875.0, 500.0, 175.0)
TEXT_GLOW = [(0.5, 0.15), (5, 0.22), (14, 0.2)]
# The source glow is per letter and strongest at the word ends; the central
# halo alone leaves E/s ~10-15 levels short. Extra wide bloom per WORD index
# (opacity of a blurred copy), fitted to the measured glow around each glyph.
GLOW_BOOST = {0: 0.65, 1: 0.7, 2: 0.27, 8: 0.62}
GLOW_BOOST_SD = 9
# Glyphs under a strong bloom read heavier, so they get a lighter core weight
# (fitted so the measured stem width matches the source).
WORD_WGHT = {0: 135}
DOT_R, DOT_FILL = 1.45, "#f4d283"
CENTER_CORE_R = 10.6
I_DOT = (349.1, 825.3, 4.6)   # the "i" tittle: measured centre/radius (sits higher than Outfit's)

# Axis nodes: (x, y, radius, colour)
NODES = [
    (395.6, CY, 5.9, "#ffd75a"), (855.5, CY, 5.4, "#ffe070"),   # dotted ring
    (427.3, CY, 5.1, "#fbe39a"), (824.3, CY, 5.1, "#fdf4cf"),   # mid ring
    (505.3, CY, 5.1, "#fcdf86"), (746.4, CY, 5.1, "#fdf6dc"),   # vesica edges
    (CX, 286.6, 5.2, "#fdeeb4"), (CX, 682.9, 5.2, "#fdf2cc"),   # mid ring top/bottom
    (CX, 197.5, 3.6, "#f6efc4"), (CX, 772.5, 3.6, "#f6f1d2"),   # axis ends
]

# Crescent fills: radial gradient about (GX, GY) in ellipse-scaled distance
# (px / 200), fitted to source pixels.
LENS_GRAD = {
    "L": {"gx": 620.0, "stops": [
        (0.55, (80, 45, 1)), (0.613, (96, 55, 2)), (0.662, (114, 68, 3)),
        (0.713, (138, 83, 6)), (0.762, (162, 100, 12)), (0.812, (193, 125, 18)),
        (0.863, (228, 157, 25)), (0.887, (243, 173, 27)), (0.912, (250, 187, 31)),
        (0.95, (252, 196, 40))]},
    "R": {"gx": 618.0, "stops": [
        (0.62, (95, 66, 25)), (0.688, (117, 84, 35)), (0.738, (139, 102, 45)),
        (0.787, (162, 122, 57)), (0.838, (190, 148, 74)), (0.887, (217, 174, 90)),
        (0.938, (240, 200, 107)), (0.988, (251, 215, 122)), (1.02, (253, 222, 135))]},
}

# Centre point glow: radius -> colour (measured radial profile).
CENTER_PROFILE = [
    (0, (252, 251, 250)), (10.5, (252, 249, 245)), (11.3, (248, 239, 220)),
    (12, (216, 177, 109)), (14, (188, 146, 75)), (16, (165, 126, 64)),
    (18, (143, 108, 52)), (21, (118, 85, 37)), (25, (91, 64, 23)),
    (30, (68, 45, 13)), (35, (53, 35, 7)), (40, (41, 24, 3)),
    (45, (35, 19, 2)), (50, (30, 16, 1)), (58, (26, 14, 1))]

# Background: warm radial falloff around the mark.
BG_PROFILE = [(0, (29, 16, 0)), (250, (27, 14, 0)), (270, (25, 13, 0)),
              (300, (19, 10, 0)), (340, (13, 7, 0)), (380, (8, 4, 0)),
              (420, (5, 2, 0)), (900, (5, 3, 0))]

# Palette (03s6)
GOLD_L = "#ffd645"      # left-side line gold
GOLD_R = "#fff0a8"      # right-side pale gold
BRACKET_L = "#f9c72e"
BRACKET_R = "#f9cf45"
INNER_RING = "#a8701a"
EIGEN_FILL = "#fdfdf8"
LENS_WORD = {"L": "#fbcb3a", "e": "#fce373", "n": "#fdde6f", "s": "#fce175"}
CN_FILL = "#f8eebc"

# Wordmark: every glyph is fitted to its source ink box (x0, x1, y0, y1),
# measured at the half-intensity edge in the reference (then refined by a
# render -> re-measure pass so the rendered edges land on the source edges,
# residual <= 0.3 px). Both axes are fitted
# because the source face has a shorter x-height (0.653 of cap) than Outfit
# (0.696); a single scale put every lowercase top ~4.7 px too high.
# The "i" box is the stem only; its tittle is I_DOT.
WORD = [("E", 240.8, 299.6, 807.3, 897.5), ("i", 347.35, 352.05, 840.5, 897.4),
        ("g", 397.9, 456.6, 838.9, 923.9), ("e", 502.4, 558.7, 838.9, 898.5),
        ("n", 602.6, 650.6, 838.9, 897.4), ("L", 694.5, 748.5, 807.0, 897.4),
        ("e", 781.4, 837.9, 838.9, 898.4), ("n", 882.7, 931.3, 839.0, 897.5),
        ("s", 974.8, 1018.8, 838.8, 898.4)]
CN = [("主", 503.2, 532.4, 955.5, 984.0), ("观", 576.2, 606.5, 956.9, 985.5),
      ("知", 652.0, 679.5, 955.6, 985.1), ("识", 725.3, 754.9, 956.3, 985.4)]

# Framings (viewBox in reference px)
VB_REF = (0, 0, 1254, 1254)
# The mark is the full composition (symbol + EigenLens + 主观知识), square,
# centred on the content (x 240..1019, y 193..985) with ~55 px margin.
VB_MARK = (180.0, 139.0, 900.0, 900.0)
VB_SYMBOL = (225.0, 87.0, 800.0, 800.0)   # symbol only, no text: favicon/avatar sizes only


def vb_16x9(content_h_frac):
    """16:9 viewBox centred on the lockup content (y 193..990, x 241..1019)."""
    cxv, cyv = 630.0, 591.5
    h = (990 - 193) / content_h_frac
    w = h * 16 / 9
    return (cxv - w / 2, cyv - h / 2, w, h)


VB_LOCKUP_169 = vb_16x9(0.80)
VB_END_169 = vb_16x9(0.66)


# --------------------------------------------------------------------------
# SVG building blocks
# --------------------------------------------------------------------------
def rgb(c):
    return "#%02x%02x%02x" % tuple(int(round(v)) for v in c)


def f(v):
    return ("%.2f" % v).rstrip("0").rstrip(".")


def glow_filter(fid, layers, extend="-30%"):
    """Bloom: blurred copies (stdDev, alpha gain) merged under the source."""
    parts = []
    names = []
    for i, (sd, k) in enumerate(layers):
        parts.append(f'<feGaussianBlur in="SourceGraphic" stdDeviation="{sd}" result="b{i}"/>'
                     f'<feColorMatrix in="b{i}" type="matrix" values="1 0 0 0 0 0 1 0 0 0 0 0 1 0 0 0 0 0 {k} 0" result="g{i}"/>')
        names.append(f"g{i}")
    merge = "".join(f'<feMergeNode in="{n}"/>' for n in reversed(names))
    return (f'<filter id="{fid}" x="{extend}" y="{extend}" width="160%" height="160%" '
            f'color-interpolation-filters="sRGB">{"".join(parts)}'
            f'<feMerge>{merge}<feMergeNode in="SourceGraphic"/></feMerge></filter>')


def ellipse(e, **attrs):
    a = " ".join(f'{k.replace("_", "-")}="{v}"' for k, v in attrs.items())
    return f'<ellipse cx="{f(e[0])}" cy="{f(e[1])}" rx="{f(e[2])}" ry="{f(e[3])}" {a}/>'


def defs():
    d = []
    # horizontal gold gradient shared by line work (left amber -> right pale)
    d.append(f'<linearGradient id="lineGold" gradientUnits="userSpaceOnUse" x1="300" y1="0" x2="950" y2="0">'
             f'<stop offset="0" stop-color="{GOLD_L}"/><stop offset="1" stop-color="{GOLD_R}"/></linearGradient>')
    d.append('<linearGradient id="linePale" gradientUnits="userSpaceOnUse" x1="300" y1="0" x2="950" y2="0">'
             '<stop offset="0" stop-color="#fbe48c"/><stop offset="1" stop-color="#fdf3bd"/></linearGradient>')
    d.append(f'<linearGradient id="brkGold" gradientUnits="userSpaceOnUse" x1="246" y1="0" x2="1004" y2="0">'
             f'<stop offset="0" stop-color="{BRACKET_L}"/><stop offset="1" stop-color="{BRACKET_R}"/></linearGradient>')
    # crescent gradients
    for k, e in (("L", G["lensL"]), ("R", G["lensR"])):
        lg = LENS_GRAD[k]
        sy = e[3] / e[2]
        stops = "".join(f'<stop offset="{s:.3f}" stop-color="{rgb(c)}"/>' for s, c in lg["stops"])
        d.append(f'<radialGradient id="lens{k}" gradientUnits="userSpaceOnUse" cx="0" cy="0" r="200" '
                 f'gradientTransform="translate({f(lg["gx"])} {f(e[1])}) scale(1 {sy:.5f})">{stops}</radialGradient>')
    # crescent masks: own disc minus the other disc
    for k, own, other in (("L", G["lensL"], G["lensR"]), ("R", G["lensR"], G["lensL"])):
        d.append(f'<mask id="cres{k}" maskUnits="userSpaceOnUse" x="0" y="0" width="1254" height="1254">'
                 + ellipse(own, fill="#fff") + ellipse(other, fill="#000") + '</mask>')
    # centre glow
    rmax = CENTER_PROFILE[-1][0] + 4
    stops = "".join(f'<stop offset="{r / rmax:.4f}" stop-color="{rgb(c)}"/>' for r, c in CENTER_PROFILE)
    stops += f'<stop offset="1" stop-color="{rgb(CENTER_PROFILE[-1][1])}" stop-opacity="0"/>'
    d.append(f'<radialGradient id="ctr" gradientUnits="userSpaceOnUse" cx="{CX}" cy="{CY}" r="{rmax}">{stops}</radialGradient>')
    # background
    rmax = BG_PROFILE[-1][0]
    stops = "".join(f'<stop offset="{r / rmax:.4f}" stop-color="{rgb(c)}"/>' for r, c in BG_PROFILE)
    d.append(f'<radialGradient id="bg" gradientUnits="userSpaceOnUse" cx="{CX}" cy="{CY}" r="{rmax}">{stops}</radialGradient>')
    # warm haze behind the wordmark (measured: ~#2c1d08 between letters)
    d.append('<radialGradient id="textHalo"><stop offset="0" stop-color="#271a07"/>'
             '<stop offset="0.45" stop-color="#231604"/><stop offset="0.7" stop-color="#1c0f02" stop-opacity="0.85"/>'
             '<stop offset="1" stop-color="#050200" stop-opacity="0"/></radialGradient>')
    # blooms
    d.append(glow_filter("glowLine", [(1.0, 0.45), (3.5, 0.2), (10, 0.1)]))
    d.append(glow_filter("glowThin", [(1.0, 0.45), (3.5, 0.25)]))
    d.append(glow_filter("glowBracket", [(1.5, 0.6), (5, 0.45), (14, 0.5), (32, 0.45)]))
    d.append(glow_filter("glowLens", [(2, 0.35), (8, 0.25), (22, 0.18)]))
    # source text has crisp edges with a low, wide warm glow (no tight bloom)
    d.append(glow_filter("glowText", TEXT_GLOW))
    d.append(glow_filter("glowNode", [(1.2, 0.6), (4, 0.4)]))
    d.append(f'<filter id="glowWide" x="-60%" y="-60%" width="220%" height="220%" color-interpolation-filters="sRGB">'
             f'<feGaussianBlur in="SourceGraphic" stdDeviation="{GLOW_BOOST_SD}"/></filter>')
    return "<defs>" + "".join(d) + "</defs>"


def layer_bg(vb):
    x, y, w, h = vb
    return f'<g id="bg"><rect x="{f(x - 2)}" y="{f(y - 2)}" width="{f(w + 4)}" height="{f(h + 4)}" fill="url(#bg)"/></g>'


def layer_text_halo():
    return (f'<g id="textHalo"><ellipse cx="{TEXT_HALO[0]}" cy="{TEXT_HALO[1]}" rx="{TEXT_HALO[2]}" '
            f'ry="{TEXT_HALO[3]}" fill="url(#textHalo)"/></g>')


def _lens(k):
    e = G["lens" + k]
    return (f'<g id="lens{k}"><g filter="url(#glowLens)">'
            + ellipse(e, fill=f"url(#lens{k})", mask=f"url(#cres{k})")
            + '</g><g filter="url(#glowLine)">'
            + ellipse(e, fill="none", stroke="url(#lineGold)", stroke_width="2.1")
            + '</g></g>')


def layer_lens_l():
    return _lens("L")


def layer_lens_r():
    return _lens("R")


def layer_rings():
    return ('<g id="rings" filter="url(#glowLine)">'
            + ellipse(G["outer"], fill="none", stroke="url(#lineGold)", stroke_width="2.6")
            + ellipse(G["mid"], fill="none", stroke="url(#linePale)", stroke_width="2.0")
            + '</g><g id="innerRing" filter="url(#glowThin)">'
            + ellipse(G["inner"], fill="none", stroke=INNER_RING, stroke_width="1.5")
            + '</g>')


def dot_positions():
    cx, cy, rx, ry = G["dotted"]
    for deg in DOT_ANGLES:
        a = math.radians(deg)
        yield cx + rx * math.cos(a), cy - ry * math.sin(a), a


def layer_dots():
    dots = "".join(f'<circle cx="{f(x)}" cy="{f(y)}" r="{DOT_R}"/>' for x, y, _ in dot_positions())
    return f'<g id="dots" fill="{DOT_FILL}" filter="url(#glowThin)">{dots}</g>'


def layer_axes():
    return (f'<g id="axes" stroke="url(#linePale)" filter="url(#glowLine)">'
            f'<line x1="{HLINE[0]}" y1="{CY}" x2="{HLINE[1]}" y2="{CY}" stroke-width="1.9"/>'
            f'<line x1="{CX}" y1="{VLINE[0]}" x2="{CX}" y2="{VLINE[1]}" stroke-width="1.9" stroke="#f6e6a6"/>'
            f'</g>')


def layer_nodes():
    c = "".join(f'<circle cx="{f(x)}" cy="{f(y)}" r="{r}" fill="{col}"/>' for x, y, r, col in NODES)
    return f'<g id="nodes" filter="url(#glowNode)">{c}</g>'


def layer_center_glow():
    # under the crosshair: the source shows the axis lines running through the glow
    return f'<g id="centerGlow"><circle cx="{CX}" cy="{CY}" r="{CENTER_PROFILE[-1][0] + 4}" fill="url(#ctr)"/></g>'


def layer_center():
    return (f'<g id="center" filter="url(#glowNode)">'
            f'<circle cx="{CX}" cy="{CY}" r="{CENTER_CORE_R}" fill="#fdfcf9"/></g>')


def bracket_polygon(side):
    b = BRACKETS[side]

    def x_at(line, y):
        return line[0] + line[1] * y

    def meet(l1, l2):
        y = (l2[0] - l1[0]) / (l1[1] - l2[1])
        return x_at(l1, y), y
    tip_o = meet(b["up_o"], b["lo_o"])
    tip_i = meet(b["up_i"], b["lo_i"])
    pts = [(x_at(b["up_o"], Y_TOP), Y_TOP), tip_o, (x_at(b["lo_o"], Y_BOT), Y_BOT),
           (x_at(b["lo_i"], Y_BOT), Y_BOT), tip_i, (x_at(b["up_i"], Y_TOP), Y_TOP)]
    return " ".join(f"{f(x)},{f(y)}" for x, y in pts)


def layer_brackets():
    return (f'<g id="brackets" fill="url(#brkGold)" filter="url(#glowBracket)">'
            f'<polygon points="{bracket_polygon("L")}"/><polygon points="{bracket_polygon("R")}"/></g>')


# ---- glyph outlines (text is outlined so the SVG needs no installed fonts) --
@lru_cache(None)
def _font(path, index, wght):
    from fontTools.ttLib import TTFont
    font = TTFont(path, fontNumber=index) if path.endswith(".ttc") else TTFont(path)
    if wght is not None and "fvar" in font:
        from fontTools.varLib.instancer import instantiateVariableFont
        font = instantiateVariableFont(font, {"wght": wght})
    return font


def glyph_path(font, ch):
    from fontTools.pens.svgPathPen import SVGPathPen
    from fontTools.pens.boundsPen import BoundsPen
    gs = font.getGlyphSet()
    name = font.getBestCmap()[ord(ch)]
    pen = SVGPathPen(gs)
    gs[name].draw(pen)
    bp = BoundsPen(gs)
    gs[name].draw(bp)
    return pen.getCommands(), bp.bounds  # bounds: xMin, yMin, xMax, yMax (font units, y up)


def _box_fit(bounds, box):
    """translate/scale mapping font-unit ink bounds onto a (x0, x1, y0, y1) px box."""
    gx0, gy0, gx1, gy1 = bounds
    x0, x1, y0, y1 = box
    sx = (x1 - x0) / (gx1 - gx0)
    sy = (y1 - y0) / (gy1 - gy0)
    return f"translate({f(x0 - gx0 * sx)} {f(y1 + gy0 * sy)}) scale({sx:.5f} {-sy:.5f})"


def layer_word_en():
    font = _font(FONT_EN, None, FONT_EN_WGHT)
    out = []
    boost = []
    for idx, (ch, *box) in enumerate(WORD):
        gfont = _font(FONT_EN, None, WORD_WGHT[idx]) if idx in WORD_WGHT else font
        d, bounds = glyph_path(gfont, "\u0131" if ch == "i" else ch)
        fill = LENS_WORD[ch] if idx >= 5 else EIGEN_FILL   # "Eigen" warm white, "Lens" gold
        out.append(f'<path d="{d}" fill="{fill}" transform="{_box_fit(bounds, box)}"/>')
        if GLOW_BOOST.get(idx):
            boost.append(f'<g filter="url(#glowWide)" opacity="{GLOW_BOOST[idx]}"><path d="{d}" fill="{fill}" '
                         f'transform="{_box_fit(bounds, box)}"/></g>')
        if ch == "i":
            out.append(f'<circle cx="{I_DOT[0]}" cy="{I_DOT[1]}" r="{I_DOT[2]}" fill="{fill}"/>')
    return ('<g id="wordEN">' + "".join(boost) + '<g filter="url(#glowText)">' + "".join(out) + '</g></g>')


def layer_word_cn():
    font = _font(FONT_CN, None, FONT_CN_WGHT)
    out = []
    for ch, *box in CN:
        d, bounds = glyph_path(font, ch)
        out.append(f'<path d="{d}" transform="{_box_fit(bounds, box)}"/>')
    return f'<g id="wordCN" fill="{CN_FILL}" filter="url(#glowText)">' + "".join(out) + '</g>'


# textHalo is a translucent warm haze: it must sit UNDER the symbol, otherwise
# it dims the bottom of the outer ring and the lower axis end.
MARK_LAYERS = ["lensL", "lensR", "rings", "dots", "centerGlow", "axes", "nodes", "center", "brackets"]
WORD_LAYERS = ["textHalo", "wordEN", "wordCN"]
LAYER_FN = {"lensL": layer_lens_l, "lensR": layer_lens_r, "textHalo": layer_text_halo, "rings": layer_rings, "dots": layer_dots, "axes": layer_axes,
            "nodes": layer_nodes, "centerGlow": layer_center_glow, "center": layer_center, "brackets": layer_brackets,
            "wordEN": layer_word_en, "wordCN": layer_word_cn}


def svg_doc(vb, layers, bg=True, title="EigenLens"):
    x, y, w, h = vb
    if "textHalo" in layers:   # always directly above the background
        layers = ["textHalo"] + [n for n in layers if n != "textHalo"]
    body = (layer_bg(vb) if bg else "") + "".join(LAYER_FN[n]() for n in layers)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{f(x)} {f(y)} {f(w)} {f(h)}" '
            f'width="{f(w)}" height="{f(h)}"><title>{title}</title>{defs()}{body}</svg>\n')


# --------------------------------------------------------------------------
# Rasterization (headless Chrome)
# --------------------------------------------------------------------------
def render_svg(svg_text, out_png, width, height):
    """Rasterize SVG text to an RGBA PNG at width x height (transparent bg outside shapes)."""
    with tempfile.TemporaryDirectory() as td:
        html = Path(td) / "page.html"
        svg_sized = svg_text.replace("<svg ", f'<svg style="display:block;width:{width}px;height:{height}px" ', 1)
        html.write_text('<!doctype html><html><head><meta charset="utf-8"><style>html,body{margin:0;'
                        'padding:0;background:transparent;overflow:hidden}</style></head><body>'
                        + svg_sized + "</body></html>", encoding="utf-8")
        shot = Path(td) / "shot.png"
        cmd = [CHROME, "--headless=new", "--no-sandbox", "--disable-gpu", "--hide-scrollbars",
               "--force-device-scale-factor=1", "--default-background-color=00000000",
               f"--window-size={width},{height}", f"--screenshot={shot}", html.as_uri()]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120)
        im = Image.open(shot).convert("RGBA")
        if im.size != (width, height):
            raise RuntimeError(f"chrome produced {im.size}, wanted {(width, height)}")
        im.save(out_png)
    return out_png


# --------------------------------------------------------------------------
# Diff vs reference
# --------------------------------------------------------------------------
def edges(lum):
    from scipy.ndimage import gaussian_filter
    s = 1.2
    lxx = gaussian_filter(lum, s, order=(0, 2))
    lyy = gaussian_filter(lum, s, order=(2, 0))
    lxy = gaussian_filter(lum, s, order=(1, 1))
    lam = (lxx + lyy) / 2 - np.sqrt(((lxx - lyy) / 2) ** 2 + lxy ** 2)
    r = np.clip(-lam, 0, None)
    return r / (np.percentile(r, 99.5) + 1e-6)


def _edges_1d(prof, thr):
    """Sub-pixel first/last crossing of thr in a 1-D profile."""
    idx = np.nonzero(prof > thr)[0]
    a, b = idx[0], idx[-1]
    fa = a - 1 + (thr - prof[a - 1]) / (prof[a] - prof[a - 1])
    fb = b + (prof[b] - thr) / (prof[b] - prof[b + 1])
    return fa, fb


def _text_measure(im):
    """Ink boxes, stroke widths and ink colours of the wordmark in a 1254 render."""
    lum = im.mean(2)
    m = {"boxes": {}, "stroke_px": {}, "ink_rgb": {}}
    for i, (ch, x0, x1, y0, y1) in enumerate(WORD):
        X0, X1, Y0 = int(x0) - 5, int(x1) + 7, (834 if ch == "i" else 790)
        sl = lum[Y0:935, X0:X1]
        t, b = _edges_1d(sl.max(1), 120)
        l, r = _edges_1d(sl.max(0), 120)
        m["boxes"][f"{ch}{i}"] = (l + X0, r + X0, t + Y0, b + Y0)
    for ch, x0, x1, y0, y1 in CN:
        X0, X1 = int(x0) - 5, int(x1) + 7
        sl = lum[940:1000, X0:X1]
        t, b = _edges_1d(sl.max(1), 100)
        l, r = _edges_1d(sl.max(0), 100)
        m["boxes"][ch] = (l + X0, r + X0, t + 940, b + 940)
    for k, (y, a, b) in {"E stem": (860, 236, 256), "i stem": (870, 340, 360), "n stem": (880, 598, 615),
                         "L stem": (860, 690, 710), "n(Lens) stem": (880, 880, 897)}.items():
        p = lum[y - 3:y + 4, a:b].mean(0)
        base = np.median(lum[y, a - 15:a - 5])
        l, r = _edges_1d(p, base + (p.max() - base) / 2)
        m["stroke_px"][k] = r - l
    p = lum[966:972, 508:528].mean(0)
    base = lum[969, 505:508].mean()
    l, r = _edges_1d(p, base + (p.max() - base) / 2)
    m["stroke_px"]["主 stem"] = r - l
    p = lum[956:966, 507:512].mean(1)
    l, r = _edges_1d(p, p[0] + (p.max() - p[0]) / 2)
    m["stroke_px"]["主 bar"] = r - l
    for name, (y0, y1, x0, x1, pct) in {"Eigen": (805, 925, 236, 662, 97), "Lens": (805, 925, 690, 1024, 97),
                                        "主观知识": (950, 990, 498, 760, 95)}.items():
        sl = im[y0:y1, x0:x1]
        L = sl.mean(2)
        m["ink_rgb"][name] = tuple(int(round(v)) for v in sl[L >= np.percentile(L, pct)].mean(0))
    return m


def text_check(src, new):
    """Compare the wordmark of the redraw against the source; pass/fail per check."""
    a, b = _text_measure(src), _text_measure(new)
    box_err = {k: max(abs(u - v) for u, v in zip(a["boxes"][k], b["boxes"][k])) for k in a["boxes"]}
    stroke = {k: (round(a["stroke_px"][k], 2), round(b["stroke_px"][k], 2)) for k in a["stroke_px"]}
    color = {k: (a["ink_rgb"][k], b["ink_rgb"][k], max(abs(u - v) for u, v in zip(a["ink_rgb"][k], b["ink_rgb"][k])))
             for k in a["ink_rgb"]}
    res = {
        "glyph_edge_err_max_px": round(max(box_err.values()), 2),
        "glyph_edge_err_per_glyph_px": {k: round(v, 2) for k, v in box_err.items()},
        "stroke_width_src_vs_redraw_px": stroke,
        "stroke_width_err_max_px": round(max(abs(u - v) for u, v in stroke.values()), 2),
        "ink_rgb_src_vs_redraw": {k: [list(v[0]), list(v[1])] for k, v in color.items()},
        "ink_rgb_err_max": max(v[2] for v in color.values()),
    }
    # pass bars: edges within 1 px, stroke within 0.6 px, ink colour within 8/255 per channel
    res["pass"] = bool(res["glyph_edge_err_max_px"] <= 1.0 and res["stroke_width_err_max_px"] <= 0.6
                       and res["ink_rgb_err_max"] <= 8)
    return res


def make_diff(redraw_png, out_png):
    src = np.asarray(Image.open(REF).convert("RGB")).astype(float)
    new = np.asarray(Image.open(redraw_png).convert("RGB")).astype(float)
    x0, y0, w, h = (int(v) for v in VB_REF)
    lum_s, lum_n = src.mean(2), new.mean(2)
    ad = np.abs(src - new).mean(2)
    mark = np.zeros_like(lum_s, bool)
    mark[180:790, 226:1030] = True
    text = np.zeros_like(lum_s, bool)
    text[795:1000, 220:1040] = True
    es, en = edges(lum_s), edges(lum_n)
    ms, mn = es > 0.25, en > 0.25
    from scipy.ndimage import binary_dilation
    tol = binary_dilation(ms, iterations=2)
    toln = binary_dilation(mn, iterations=2)
    prec = (mn & tol)[mark].sum() / max(1, mn[mark].sum())
    rec = (ms & toln)[mark].sum() / max(1, ms[mark].sum())
    mse = ((src - new) ** 2)[mark].mean()
    stats = {
        "mean_abs_diff_mark_0_255": round(float(ad[mark].mean()), 2),
        "mean_abs_diff_text_0_255": round(float(ad[text].mean()), 2),
        "psnr_mark_db": round(float(10 * math.log10(255 ** 2 / mse)), 2),
        "line_precision_2px": round(float(prec), 3),
        "line_recall_2px": round(float(rec), 3),
        "pixels_off_by_gt_40_mark_pct": round(float((ad[mark] > 40).mean() * 100), 2),
    }
    stats["text"] = text_check(src, new)
    # panels
    crop = (200, 170, 1060, 1010)

    def c(a):
        return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).crop(crop)
    pa = c(src)
    pb = c(new)
    blend = c(src * 0.5 + new * 0.5)
    ov = np.zeros_like(src)
    ov[..., 0] = np.clip(es * 255, 0, 255)                 # source lines: red
    ov[..., 1] = np.clip(en * 255, 0, 255)                 # redraw lines: green -> overlap yellow
    ov[..., 2] = 0
    ovp = c(ov)
    # black <8 levels, then red -> yellow -> white as |diff| grows to 64+
    t = np.clip((ad - 8) / 56, 0, 1)
    hm = np.stack([np.clip(t * 3, 0, 1), np.clip(t * 3 - 1, 0, 1), np.clip(t * 3 - 2, 0, 1)], -1) * 255
    hmp = c(hm)
    W_, H_ = pa.size
    # text zoom (2x): source / redraw / luminance overlay (red=source, green=redraw, yellow=match)
    tb = (225, 795, 1035, 1000)
    z = lambda a: Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).crop(tb).resize(
        ((tb[2] - tb[0]) * 2, (tb[3] - tb[1]) * 2), Image.LANCZOS)
    tz = [z(src), z(new), z(np.stack([lum_s, lum_n, np.zeros_like(lum_s)], -1))]
    TW, TH = tz[0].size
    sheet = Image.new("RGB", (max(W_ * 3 + 40, TW + 20), H_ * 2 + 190 + 3 * (TH + 50) + 40), (12, 12, 12))
    labels = ["03s6 source", "programmatic redraw (lockup.svg @1254)", "50/50 blend",
              "line overlay: red=source  green=redraw  yellow=match", "|diff| heatmap: black <8/255, red->yellow->white = 8..64+", ""]
    panels = [pa, pb, blend, ovp, hmp]
    d = ImageDraw.Draw(sheet)
    try:
        fnt = ImageFont.truetype(FONT_EN, 22)
        fs = ImageFont.truetype(FONT_EN, 26)
    except Exception:
        fnt = fs = ImageFont.load_default()
    for i, p in enumerate(panels):
        gx, gy = 10 + (i % 3) * (W_ + 10), 90 + (i // 3) * (H_ + 50)
        sheet.paste(p, (gx, gy))
        d.text((gx, gy - 32), labels[i], fill=(235, 220, 170), font=fnt)
    tx, ty = 10 + 2 * (W_ + 10), 90 + H_ + 50
    d.text((tx, ty - 32), "metrics (mark region)", fill=(235, 220, 170), font=fnt)
    t = stats["text"]
    lines = [(k, v) for k, v in stats.items() if k != "text"] + [
        ("text glyph edge err max px", t["glyph_edge_err_max_px"]),
        ("text stroke width err max px", t["stroke_width_err_max_px"]),
        ("text ink colour err max /255", t["ink_rgb_err_max"]),
        ("text check", "PASS" if t["pass"] else "FAIL")]
    for k, (key, v) in enumerate(lines):
        d.text((tx, ty + 10 + k * 34), f"{key}: {v}", fill=(230, 230, 230), font=fnt)
    zl = ["wordmark 2x - 03s6 source", "wordmark 2x - redraw",
          "wordmark 2x - luminance overlay: red=source  green=redraw  yellow=match"]
    y = 90 + 2 * (H_ + 50) + 10
    for lab, im_ in zip(zl, tz):
        d.text((10, y), lab, fill=(235, 220, 170), font=fnt)
        sheet.paste(im_, (10, y + 36))
        y += TH + 50
    d.text((10, 8), "EigenLens mark vs 03s6_amber_gold.png - pixel comparison", fill=(255, 215, 120), font=fs)
    sheet.save(out_png)
    return stats


# --------------------------------------------------------------------------
# Stings
# --------------------------------------------------------------------------
def ease(t):
    t = min(1.0, max(0.0, t))
    return t * t * (3 - 2 * t)


def ease_out(t):
    t = min(1.0, max(0.0, t))
    return 1 - (1 - t) ** 3


def seg(t, a, b):
    return ease((t - a) / (b - a)) if b > a else float(t >= a)


class Layers:
    """Pre-rendered RGBA layers for a 16:9 framing, premultiplied float32."""

    def __init__(self, vb, w, h, tmp):
        self.vb, self.w, self.h = vb, w, h
        self.px = w / vb[2]
        self.L = {}
        for name in ["bg"] + MARK_LAYERS + WORD_LAYERS:
            p = Path(tmp) / f"layer_{name}.png"
            if name == "bg":
                svg = svg_doc(vb, [], bg=True)
            else:
                svg = svg_doc(vb, [name], bg=False)
            render_svg(svg, p, w, h)
            a = np.asarray(Image.open(p).convert("RGBA")).astype(np.float32) / 255.0
            a[..., :3] *= a[..., 3:4]
            self.L[name] = a
        full = Path(tmp) / "full.png"
        render_svg(svg_doc(vb, MARK_LAYERS + WORD_LAYERS), full, w, h)
        self.full = np.asarray(Image.open(full).convert("RGB")).astype(np.float32) / 255.0
        ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
        self.cx = (CX - vb[0]) * self.px
        self.cy = (CY - vb[1]) * self.px
        self.ang = (np.degrees(np.arctan2(xs - self.cx, -(ys - self.cy))) % 360.0) / 360.0  # 0 at top, clockwise
        self.dx = np.abs(xs - self.cx)
        self.dy = np.abs(ys - self.cy)
        self.rad = np.hypot(xs - self.cx, ys - self.cy)

    def shift(self, a, dx_ref, dy_ref=0.0):
        dx, dy = int(round(dx_ref * self.px)), int(round(dy_ref * self.px))
        if dx == 0 and dy == 0:
            return a
        out = np.zeros_like(a)
        h, w = a.shape[:2]
        xs0, xs1 = max(0, -dx), min(w, w - dx)
        ys0, ys1 = max(0, -dy), min(h, h - dy)
        out[ys0 + dy:ys1 + dy, xs0 + dx:xs1 + dx] = a[ys0:ys1, xs0:xs1]
        return out


def over(dst, src, alpha=1.0, mask=None):
    s = src if mask is None else src * mask[..., None]
    if alpha != 1.0:
        s = s * alpha
    return dst * (1 - s[..., 3:4]) + s


def frame_open(Ly, t, T):
    """3 s opening sting: centre ignites, crosshair extends, rings sweep on,
    crescents close in from the sides, brackets lock, wordmark resolves."""
    out = np.zeros((Ly.h, Ly.w, 4), np.float32)
    out = over(out, Ly.L["bg"], seg(t, 0.0, 0.5))
    out = over(out, Ly.L["textHalo"], ease_out((t - 1.6) / 0.7))   # under the symbol
    # crescents slide toward each other
    k = ease_out((t - 0.75) / 0.75)
    if k > 0:
        out = over(out, Ly.shift(Ly.L["lensL"], -70 * (1 - k)), k)
        out = over(out, Ly.shift(Ly.L["lensR"], 70 * (1 - k)), k)
    # rings: clockwise sweep from 12 o'clock
    sw = ease((t - 0.35) / 0.9)
    if sw > 0:
        m = np.clip((sw * 1.04 - Ly.ang) / 0.04, 0, 1)
        out = over(out, Ly.L["rings"], 1.0, m)
    sd = ease((t - 0.55) / 0.9)
    if sd > 0:
        m = np.clip((sd * 1.04 - ((Ly.ang + 0.5) % 1.0)) / 0.04, 0, 1)
        out = over(out, Ly.L["dots"], 1.0, m)
    # crosshair grows from centre
    g = ease_out((t - 0.15) / 0.8)
    if g > 0:
        reach = g * 330 * Ly.px
        m = (np.clip((reach - Ly.dx) / 6, 0, 1) * (Ly.dy < 4 * Ly.px) +
             np.clip((reach - Ly.dy) / 6, 0, 1) * (Ly.dx < 4 * Ly.px))
        out = over(out, Ly.L["axes"], 1.0, np.clip(m, 0, 1))
    out = over(out, Ly.L["nodes"], seg(t, 1.05, 1.5))
    # centre: ignite with a small overshoot, then settle
    ci = seg(t, 0.0, 0.35)
    if ci > 0:
        flare = 1.0 + 0.35 * math.exp(-((t - 0.45) / 0.18) ** 2) + 0.12 * math.exp(-((t - 2.25) / 0.15) ** 2)
        out = over(out, Ly.L["centerGlow"], ci)
        out = over(out, Ly.L["center"], ci)
        if flare > 1.001:
            out[..., :3] += (Ly.L["center"][..., :3] + Ly.L["centerGlow"][..., :3]) * (flare - 1.0)
    # brackets close in
    b = ease_out((t - 1.1) / 0.6)
    if b > 0:
        lb = Ly.L["brackets"]
        half = int(Ly.cx)
        left = lb.copy()
        left[:, half:] = 0
        right = lb.copy()
        right[:, :half] = 0
        out = over(out, Ly.shift(left, -60 * (1 - b)), b)
        out = over(out, Ly.shift(right, 60 * (1 - b)), b)
    # wordmark
    w1 = ease_out((t - 1.6) / 0.7)
    if w1 > 0:
        out = over(out, Ly.shift(Ly.L["wordEN"], 0, 14 * (1 - w1)), w1)
    w2 = ease_out((t - 1.9) / 0.6)
    if w2 > 0:
        out = over(out, Ly.shift(Ly.L["wordCN"], 0, 10 * (1 - w2)), w2)
    rgbv = out[..., :3]
    # land exactly on the static lockup over the last 0.35 s
    land = seg(t, T - 0.5, T - 0.15)
    rgbv = rgbv * (1 - land) + Ly.full * land
    return rgbv


def frame_end(Ly, t, T):
    """2 s closing sting: lens and brackets settle in, wordmark follows, hold on the end card."""
    out = np.zeros((Ly.h, Ly.w, 4), np.float32)
    out = over(out, Ly.L["bg"], seg(t, 0.0, 0.3))
    out = over(out, Ly.L["textHalo"], ease_out((t - 0.45) / 0.6))   # under the symbol
    k = ease_out(t / 0.7)
    for n in ("lensL", "lensR", "rings", "dots", "centerGlow", "axes", "nodes", "center"):
        out = over(out, Ly.L[n], k)
    b = ease_out((t - 0.15) / 0.6)
    if b > 0:
        lb = Ly.L["brackets"]
        half = int(Ly.cx)
        left = lb.copy()
        left[:, half:] = 0
        right = lb.copy()
        right[:, :half] = 0
        out = over(out, Ly.shift(left, -40 * (1 - b)), b)
        out = over(out, Ly.shift(right, 40 * (1 - b)), b)
    w1 = ease_out((t - 0.45) / 0.6)
    if w1 > 0:
        out = over(out, Ly.shift(Ly.L["wordEN"], 0, 10 * (1 - w1)), w1)
    w2 = ease_out((t - 0.65) / 0.5)
    if w2 > 0:
        out = over(out, Ly.shift(Ly.L["wordCN"], 0, 8 * (1 - w2)), w2)
    land = seg(t, 1.25, 1.5)
    return out[..., :3] * (1 - land) + Ly.full * land


def encode(frames_fn, n, w, h, out_mp4):
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{w}x{h}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "slow",
           "-crf", "14", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(out_mp4)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(n):
        fr = frames_fn(i)
        p.stdin.write((np.clip(fr, 0, 1) * 255 + 0.5).astype(np.uint8).tobytes())
    p.stdin.close()
    if p.wait() != 0:
        raise RuntimeError("ffmpeg failed")


def build_stings(tmp):
    W, H = 1920, 1080
    Ly = Layers(VB_END_169, W, H, tmp)
    T = 3.0
    n = int(T * FPS)
    encode(lambda i: frame_open(Ly, i / FPS, T), n, W, H, HERE / "sting_open.mp4")
    Image.fromarray((np.clip(frame_open(Ly, 1.4, T), 0, 1) * 255).astype(np.uint8)).save(HERE / "sting_open_mid.png")
    T2 = 2.0
    n2 = int(T2 * FPS)
    encode(lambda i: frame_end(Ly, i / FPS, T2), n2, W, H, HERE / "sting_end.mp4")
    Image.fromarray((np.clip(frame_end(Ly, 0.5, T2), 0, 1) * 255).astype(np.uint8)).save(HERE / "sting_end_mid.png")


# --------------------------------------------------------------------------
def build_stills(tmp):
    all_layers = MARK_LAYERS + WORD_LAYERS
    (HERE / "mark.svg").write_text(svg_doc(VB_MARK, all_layers, title="EigenLens / 主观知识"), encoding="utf-8")
    (HERE / "symbol_only.svg").write_text(svg_doc(VB_SYMBOL, MARK_LAYERS, title="EigenLens symbol"), encoding="utf-8")
    (HERE / "lockup.svg").write_text(svg_doc(VB_REF, all_layers, title="EigenLens / 主观知识"), encoding="utf-8")
    render_svg((HERE / "mark.svg").read_text(encoding="utf-8"), HERE / "mark_1024.png", 1024, 1024)
    render_svg((HERE / "symbol_only.svg").read_text(encoding="utf-8"), HERE / "symbol_only_1024.png", 1024, 1024)
    render_svg(svg_doc(VB_LOCKUP_169, all_layers), HERE / "lockup_16x9.png", 1920, 1080)
    render_svg(svg_doc(VB_END_169, all_layers), HERE / "endcard_16x9.png", 1920, 1080)
    for p in ("mark_1024.png", "symbol_only_1024.png", "lockup_16x9.png", "endcard_16x9.png"):
        Image.open(HERE / p).convert("RGB").save(HERE / p)
    ref_render = Path(tmp) / "lockup_1254.png"
    render_svg((HERE / "lockup.svg").read_text(encoding="utf-8"), ref_render, 1254, 1254)
    Image.open(ref_render).convert("RGB").save(HERE / "lockup_1254.png")
    if REF.exists():
        stats = make_diff(HERE / "lockup_1254.png", HERE / "diff_vs_03s6.png")
        (HERE / "diff_vs_03s6.json").write_text(json.dumps(stats, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print("diff vs 03s6:", json.dumps(stats, ensure_ascii=False))
    else:
        print(f"reference {REF} not found; skipped diff")


def main():
    with tempfile.TemporaryDirectory() as tmp:
        build_stills(tmp)
        if "--stills" not in sys.argv:
            build_stings(tmp)
    print("done ->", HERE)


if __name__ == "__main__":
    main()
