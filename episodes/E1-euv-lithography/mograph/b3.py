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


def pins(c, a, plate=False):
    for (x, y), lab in ((F1, "焦点①"), (F2, "焦点②")):
        c.circle((x, y), 10, fill=LINE, a=a)
        if plate:                               # a blueprint-blue plate keeps the label legible over the rays
            c.rect((x - 52, y + 26, x + 52, y + 64), fill=BLUE_BG, a=a * 0.85, radius=8)
        c.text((x, y + 45), lab, 30, LINE, a, anchor="mm")


def mirror_arc(c, a, upto=1.0, width=5):
    """The collector's mirror: both halves of the arc from the rim to the edge of the laser hole, solid."""
    for side in (1, -1):
        for i in range(60):
            if i / 60 >= upto:
                break
            p0 = RIM + (math.pi - HOLE - RIM) * i / 60
            p1 = RIM + (math.pi - HOLE - RIM) * (i + 1) / 60
            c.line(hit(side * p0), hit(side * p1), LINE, width, a)


def _arc(c, centre, r, a0, a1, color, width, a):
    n = 16
    for i in range(n):
        t0, t1 = a0 + (a1 - a0) * i / n, a0 + (a1 - a0) * (i + 1) / n
        c.line((centre[0] + r * math.cos(t0), centre[1] + r * math.sin(t0)),
               (centre[0] + r * math.cos(t1), centre[1] + r * math.sin(t1)), color, width, a)


def _dashed(c, p0, p1, color, width, a, dash=12):
    L = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
    n = max(1, int(L / dash))
    for i in range(0, n, 2):
        u0, u1 = i / n, min(1.0, (i + 1) / n)
        c.line((p0[0] + (p1[0] - p0[0]) * u0, p0[1] + (p1[1] - p0[1]) * u0),
               (p0[0] + (p1[0] - p0[0]) * u1, p0[1] + (p1[1] - p0[1]) * u1), color, width, a)


@shot("B3_03")
def gardener(t, dur, W, H):
    c = Canvas(W, H, bg=BLUE_BG)
    c.grid(a=0.55)
    a = fade(t, 0.0, dur, dur, 0.3)
    # the mirror's arc (left part of the ellipse) first, solid; its label sits at the rim end of the arc
    arc = ease_out(seg(t, 0.0, 0.8))
    mirror_arc(c, a, arc)
    rim = hit(-RIM)
    c.text((rim[0] + 22, rim[1] - 6), "收集镜的镜面（中心留孔给激光）", 28, LINE, a * ease(seg(t, 0.5, 1.0)), anchor="lm")
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
    # the real collector's proportions are not public: the ellipse is the one used in 3D (e = 0.64), so 示意
    c.text((CX, 70), "到两个焦点的距离之和处处相等（比例示意）", 32, LINE, a * ease(seg(t, 1.6, 2.2)), anchor="mm")
    return c.finish(glow_radius=8)


@shot("B3_04")
def two_foci(t, dur, W, H):
    c = Canvas(W, H, bg=BLUE_BG)
    c.grid(a=0.55)
    a = fade(t, 0.0, dur, dur, 0.3)
    ellipse(c, 1.0, a * 0.4, dashed=True, width=2)
    mirror_arc(c, a)                           # the solid mirror of B3_03 (the rays reflect off it, not the dashes)
    phis = mirror_phis(7)                      # 14 rays, all landing on the mirror (none into the hole)
    order = [3, 10, 6, 13, 0, 7, 1, 8, 2, 9, 4, 11, 5, 12]
    glow = ease(seg(t, dur - 2.6, dur - 0.8))
    euv = (128, 84, 255)                       # saturated EUV violet (the pale token washed out under the glow)
    for idx, k in enumerate(order):
        start = 0.6 + 0.35 * idx
        g = ease_out(seg(t, start, start + 0.8))
        if g <= 0:
            continue
        q = hit(phis[k])
        col = tuple(int(l + (v - l) * glow) for l, v in zip(LINE, euv))
        c.line(F1, q, col, 3, a, progress=min(1.0, g * 2), glow=glow > 0)
        if g > 0.5:
            c.line(q, F2, col, 3, a, progress=(g - 0.5) * 2, glow=glow > 0)
        if idx < 3 and g > 0.5:             # dashed normal on the first rays; angle marks and label on the first
            nx, ny = (q[0] - CX) / A ** 2, (q[1] - CY) / B ** 2  # gradient of x²/A² + y²/B² (outward)
            ln = math.hypot(nx, ny)
            nx, ny = nx / ln, ny / ln
            na = a * 0.8 * (1 - glow * 0.7)
            _dashed(c, (q[0] - 80 * nx, q[1] - 80 * ny), (q[0] + 55 * nx, q[1] + 55 * ny), LINE, 2, na)
            if idx == 0:
                c.text((q[0] + 95 * nx, q[1] + 95 * ny), "法线", 28, LINE, na, anchor="mm")
                th_n = math.atan2(-ny, -nx)     # inward normal
                th_1 = math.atan2(F1[1] - q[1], F1[0] - q[0])
                th_2 = math.atan2(F2[1] - q[1], F2[0] - q[0])
                m = ease(seg(t, start + 0.5, start + 1.0)) * na
                for t0, t1, rr in ((th_1, th_n, 70), (th_n, th_2, 92)):
                    d = (t1 - t0 + math.pi) % (2 * math.pi) - math.pi
                    _arc(c, q, rr, t0, t0 + d, LINE, 2, m)
                    mid = t0 + d / 2
                    c.text((q[0] + (rr + 24) * math.cos(mid), q[1] + (rr + 24) * math.sin(mid)), "θ", 30, LINE, m,
                           anchor="mm")
    pins(c, a, plate=True)
    c.text((CX, 70), "从一个焦点出发 → 必经另一个焦点", 34, LINE, a * ease(seg(t, 1.0, 1.6)), anchor="mm")
    return c.finish(glow_radius=10, glow_gain=1.0 + 0.35 * glow)
