"""B3 blueprint geometry: the ellipse and its two foci (F56).
B3_03 draws the ellipse the gardener's way (two pins, a taut string); B3_04 shows that every ray
leaving focus 1 reflects through focus 2, with normals and equal angles marked."""
import math

from mograph import BLUE_BG, LINE, VIOLET, Canvas, ease, ease_out, fade, seg, shot

CX, CY, A, B = 960, 560, 640, 360          # ellipse in design space
C_ = math.sqrt(A * A - B * B)
F1, F2 = (CX - C_, CY), (CX + C_, CY)


def pt(th):
    return (CX + A * math.cos(th), CY + B * math.sin(th))


def ellipse(c, upto, a, dashed=False, width=3, color=LINE):
    n = 240
    k = int(n * upto)
    for i in range(k):
        if dashed and i % 4 >= 2:
            continue
        c.line(pt(2 * math.pi * i / n), pt(2 * math.pi * (i + 1) / n), color, width, a)


def pins(c, a):
    for (x, y), lab in ((F1, "焦点①"), (F2, "焦点②")):
        c.circle((x, y), 10, fill=LINE, a=a)
        c.text((x, y + 44), lab, 30, LINE, a, anchor="mm")


@shot("B3_03")
def gardener(t, dur, W, H):
    c = Canvas(W, H, bg=BLUE_BG)
    c.grid(a=0.55)
    a = fade(t, 0.0, dur, dur, 0.3)
    # the mirror's arc (left part of the ellipse) first, solid
    arc = ease_out(seg(t, 0.0, 0.8))
    for i in range(80):
        th0 = math.pi * 0.62 + math.pi * 0.76 * i / 80
        th1 = math.pi * 0.62 + math.pi * 0.76 * (i + 1) / 80
        if i / 80 <= arc:
            c.line(pt(th0), pt(th1), LINE, 5, a)
    c.text((CX - A - 30, CY - B - 10), "收集镜的镜面", 28, LINE, a * arc, anchor="lm")
    pins(c, a * ease(seg(t, 0.6, 1.1)))
    # taut string traces the full ellipse
    p = ease(seg(t, 1.2, dur - 0.4))
    th = 2 * math.pi * p
    ellipse(c, p, a, dashed=True, width=2)
    if 0 < p < 1:
        q = pt(th)
        c.line(F1, q, LINE, 2, a * 0.8)
        c.line(F2, q, LINE, 2, a * 0.8)
        c.circle(q, 7, fill=LINE, a=a)
    c.text((CX, 120), "到两个焦点的距离之和处处相等", 32, LINE, a * ease(seg(t, 1.6, 2.2)), anchor="mm")
    return c.finish(glow_radius=8)


@shot("B3_04")
def two_foci(t, dur, W, H):
    c = Canvas(W, H, bg=BLUE_BG)
    c.grid(a=0.55)
    a = fade(t, 0.0, dur, dur, 0.3)
    ellipse(c, 1.0, a * 0.5, dashed=True, width=2)
    pins(c, a)
    angles = [math.pi * (0.68 + 0.64 * k / 14) for k in range(15)]
    order = [7, 3, 11, 1, 5, 9, 13, 0, 2, 4, 6, 8, 10, 12, 14]
    glow = ease(seg(t, dur - 2.6, dur - 0.8))
    for idx, k in enumerate(order):
        start = 0.6 + 0.35 * idx
        g = ease_out(seg(t, start, start + 0.8))
        if g <= 0:
            continue
        q = pt(angles[k])
        col = tuple(int(l + (v - l) * glow) for l, v in zip(LINE, VIOLET))
        c.line(F1, q, col, 3, a, progress=min(1.0, g * 2), glow=glow > 0)
        if g > 0.5:
            c.line(q, F2, col, 3, a, progress=(g - 0.5) * 2, glow=glow > 0)
        if idx < 3 and g > 0.5:             # mark the normal and the two equal angles on the first rays
            th = angles[k]
            nx, ny = math.cos(th) / A, math.sin(th) / B        # gradient of x²/A² + y²/B² (unnormalised)
            ln = math.hypot(nx, ny)
            nx, ny = nx / ln, ny / ln
            c.line((q[0] - 90 * nx, q[1] - 90 * ny), (q[0] + 30 * nx, q[1] + 30 * ny), LINE, 2, a * 0.7)
            c.text((q[0] - 115 * nx, q[1] - 115 * ny), "法线", 22, LINE, a * 0.8, anchor="mm")
    c.text((CX, 120), "从一个焦点出发的光，反射后必经另一个焦点", 34, LINE,
           a * ease(seg(t, 1.0, 1.6)), anchor="mm")
    return c.finish(glow_radius=10, glow_gain=1.0 + glow)
