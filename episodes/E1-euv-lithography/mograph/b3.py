"""B3 blueprint geometry: the ellipse and its two foci.
B3_03 draws the ellipse the gardener's way (two pins, a taut string); B3_04 shows that every ray
leaving focus 1 reflects through focus 2, with normals and equal angles marked."""
import math

from mograph import BLUE_BG, LINE, VIOLET, Canvas, ease, ease_out, fade, seg, shot

# Same eccentricity as the 3D collector (build_source, e = 0.64), so the blueprint and the render agree.
# The mirror is the part of the ellipse behind the plasma: seen from focus 1 it spans polar angles 93-180 deg
# from the axis toward focus 2 (rim just behind the plasma plane, ~5.8 sr in 3D; ASML ">5 sr"), with a
# central hole of about +-10 deg for the drive laser (research/visual/B3_sources.md).
E_ = 0.64
A = 560
C_ = A * E_
B = math.sqrt(A * A - C_ * C_)
CX, CY = 960, 560
F1, F2 = (CX - C_, CY), (CX + C_, CY)
RIM, HOLE = math.radians(93), math.radians(10)


def pt(th):
    return (CX + A * math.cos(th), CY + B * math.sin(th))


def hit(phi):
    """Where a ray leaving focus 1 at polar angle phi (from the axis toward focus 2) meets the ellipse."""
    dx, dy = math.cos(phi), math.sin(phi)
    ox, oy = F1[0] - CX, F1[1] - CY
    qa = (dx / A) ** 2 + (dy / B) ** 2
    qb = 2 * (ox * dx / A ** 2 + oy * dy / B ** 2)
    qc = (ox / A) ** 2 + (oy / B) ** 2 - 1
    t = (-qb + math.sqrt(qb * qb - 4 * qa * qc)) / (2 * qa)
    return (F1[0] + t * dx, F1[1] + t * dy)


def mirror_phis(n_per_side):
    """Ray directions that land on the mirror (both halves), skipping the laser hole at the vertex."""
    out = []
    for side in (1, -1):
        for k in range(n_per_side):
            phi = RIM + (math.pi - HOLE - RIM) * k / max(1, n_per_side - 1)
            out.append(side * phi)
    return out


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
    for side in (1, -1):                       # the two halves, from the rim to the edge of the laser hole
        for i in range(60):
            if i / 60 > arc:
                break
            p0 = RIM + (math.pi - HOLE - RIM) * i / 60
            p1 = RIM + (math.pi - HOLE - RIM) * (i + 1) / 60
            c.line(hit(side * p0), hit(side * p1), LINE, 5, a)
    c.text((CX - A - 30, CY - B - 10), "收集镜的镜面（中心留孔给激光）", 28, LINE, a * arc, anchor="lm")
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
    c.text((CX, 70), "到两个焦点的距离之和处处相等", 32, LINE, a * ease(seg(t, 1.6, 2.2)), anchor="mm")
    return c.finish(glow_radius=8)


@shot("B3_04")
def two_foci(t, dur, W, H):
    c = Canvas(W, H, bg=BLUE_BG)
    c.grid(a=0.55)
    a = fade(t, 0.0, dur, dur, 0.3)
    ellipse(c, 1.0, a * 0.5, dashed=True, width=2)
    pins(c, a)
    phis = mirror_phis(7)                      # 14 rays, all landing on the mirror (none into the hole)
    order = [3, 10, 6, 13, 0, 7, 1, 8, 2, 9, 4, 11, 5, 12]
    glow = ease(seg(t, dur - 2.6, dur - 0.8))
    for idx, k in enumerate(order):
        start = 0.6 + 0.35 * idx
        g = ease_out(seg(t, start, start + 0.8))
        if g <= 0:
            continue
        q = hit(phis[k])
        col = tuple(int(l + (v - l) * glow) for l, v in zip(LINE, VIOLET))
        c.line(F1, q, col, 3, a, progress=min(1.0, g * 2), glow=glow > 0)
        if g > 0.5:
            c.line(q, F2, col, 3, a, progress=(g - 0.5) * 2, glow=glow > 0)
        if idx < 3 and g > 0.5:             # mark the normal and the two equal angles on the first rays
            nx, ny = (q[0] - CX) / A ** 2, (q[1] - CY) / B ** 2  # gradient of x²/A² + y²/B² (unnormalised)
            ln = math.hypot(nx, ny)
            nx, ny = nx / ln, ny / ln
            c.line((q[0] - 90 * nx, q[1] - 90 * ny), (q[0] + 30 * nx, q[1] + 30 * ny), LINE, 2, a * 0.7)
            c.text((q[0] - 115 * nx, q[1] - 115 * ny), "法线", 22, LINE, a * 0.8, anchor="mm")
    c.text((CX, 70), "从一个焦点出发的光，反射后必经另一个焦点", 34, LINE,
           a * ease(seg(t, 1.0, 1.6)), anchor="mm")
    return c.finish(glow_radius=10, glow_gain=1.0 + glow)
