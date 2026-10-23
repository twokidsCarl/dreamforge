"""Chemical / math sub- and superscripts for Pillow text (Sn⁸⁺, H₂, SnH₄, k₁, 10¹²).

Neither Heiti nor Noto Sans CJK has most of these glyphs (they draw as blank boxes), so the old tools flattened them
into normal digits (Sn8+, H2). Here every run of sub/superscript characters is typeset with the SAME font at 62 %
size, raised (sup) or lowered (sub) from the baseline: the weight and style stay those of the body text.

  draw_text(draw, xy, s, font, fill, anchor="la", **kw)  # drop-in for ImageDraw.text (stroke_* kwargs passed on)
  text_bbox(draw, xy, s, font, anchor="la")              # drop-in for ImageDraw.textbbox
  text_length(draw, s, font)                             # drop-in for ImageDraw.textlength
Strings without such characters go straight to Pillow, so existing output is unchanged.
"""
from PIL import ImageFont

SUP = dict(zip("⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾ⁿ", "0123456789+-=()n"))
SUB = dict(zip("₀₁₂₃₄₅₆₇₈₉₊₋₌₍₎", "0123456789+-=()"))
# U+00B7 middle dot (k₁ · λ, H· radical): CJK fonts draw it full-width with wide side bearings, so it is
# typeset with a Latin font at body size instead (kind "dot").
DOT = "·"
LATIN = next((p for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                          "/System/Library/Fonts/Supplemental/Arial.ttf", "/Library/Fonts/Arial.ttf")
              if __import__("os").path.exists(p)), None)
SCALE = 0.62
RAISE = 0.40      # superscript baseline shift, in body em
LOWER = 0.14      # subscript baseline shift, in body em
_cache = {}


def has_script(s):
    return any(c in SUP or c in SUB or (c == DOT and LATIN) for c in s or "")


def runs(s):
    """[(text, kind)] with kind None / 'sup' / 'sub'; script characters are mapped to plain ones."""
    out = []
    for c in s:
        kind, ch = ("sup", SUP[c]) if c in SUP else ("sub", SUB[c]) if c in SUB else \
            ("dot", c) if (c == DOT and LATIN) else (None, c)
        if out and out[-1][1] == kind:
            out[-1][0] += ch
        else:
            out.append([ch, kind])
    return [(t, k) for t, k in out]


def small(font):
    key = (getattr(font, "path", None), getattr(font, "index", 0), font.size)
    if key not in _cache:
        try:
            _cache[key] = ImageFont.truetype(font.path, max(6, round(font.size * SCALE)), index=getattr(font, "index", 0))
        except Exception:
            _cache[key] = font
    return _cache[key]


def latin(font):
    key = ("latin", font.size)
    if key not in _cache:
        _cache[key] = ImageFont.truetype(LATIN, font.size) if LATIN else font
    return _cache[key]


def _layout(draw, s, font):
    """[(text, font, dx, dy_from_baseline)], total advance."""
    sm = small(font)
    x, items = 0.0, []
    for t, k in runs(s):
        if k == "dot":
            f = latin(font)
            items.append((t, f, x, 0))
            x += draw.textlength(t, font=f)
            continue
        f = font if k is None else sm
        dy = 0 if k is None else (-RAISE * font.size if k == "sup" else LOWER * font.size)
        items.append((t, f, x, dy))
        x += draw.textlength(t, font=f)
    return items, x


def _origin(draw, xy, s, font, anchor):
    """Left x and baseline y for an anchor like Pillow's (h in l/m/r, v in a/t/m/s/b/d)."""
    h, v = (anchor or "la")[0], (anchor or "la")[1]
    _, width = _layout(draw, s, font)
    x = xy[0] - {"l": 0, "m": width / 2, "r": width}[h]
    asc, desc = font.getmetrics()
    if v in "at":
        base = xy[1] + asc
    elif v == "m":
        base = xy[1] + (asc - desc) / 2
    elif v in "sb":
        base = xy[1]
    else:                                   # d: descender
        base = xy[1] - desc
    return x, base


def draw_text(draw, xy, s, font, fill=None, anchor="la", **kw):
    if not has_script(s):
        return draw.text(xy, s, font=font, fill=fill, anchor=anchor, **kw)
    x, base = _origin(draw, xy, s, font, anchor)
    items, _ = _layout(draw, s, font)
    for t, f, dx, dy in items:
        draw.text((x + dx, base + dy), t, font=f, fill=fill, anchor="ls", **kw)


def text_bbox(draw, xy, s, font, anchor="la", **kw):
    if not has_script(s):
        return draw.textbbox(xy, s, font=font, anchor=anchor, **kw)
    x, base = _origin(draw, xy, s, font, anchor)
    items, _ = _layout(draw, s, font)
    boxes = [draw.textbbox((x + dx, base + dy), t, font=f, anchor="ls", **kw) for t, f, dx, dy in items]
    return (min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes))


def text_length(draw, s, font):
    if not has_script(s):
        return draw.textlength(s, font=font)
    return _layout(draw, s, font)[1]
