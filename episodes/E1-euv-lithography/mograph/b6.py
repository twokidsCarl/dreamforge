"""B6 2D shots: incidence-angle blueprint (F40), OPC mask shapes under the SEM (F38),
computational lithography in three beats (F38), one particle -> every die (F35),
one in a million (F37), defocused dust on the pellicle, and the "indistinguishable from magic" card (F36).

Sources (research/visual/B6B7_sources.md, audit_B6.yaml): NXE chief ray 6 deg [ZEISS, Conradi 2011 s.20]; cone
half-angle at the mask asin(0.33/4) = 4.73 deg; OPC shapes = hammerheads at line ends, serifs at corners, separate
assist bars [Brion/ASML US 7,694,267]; densest NXE mask pitch 104 nm = 26 nm on the wafer x 4 [ASML]; 96 full fields
of 26 x 33 mm per 300 mm wafer, edge fields included [F45; ASML 2022 s.12]; "100% yield loss for full field dies"
[ASML, van de Kerkhof 2019 s.3]; article title "Indistinguishable from magic: the EUV pellicle" [ASML 2022]."""
import math
import random

from PIL import Image, ImageChops, ImageDraw, ImageFilter

from mograph import (BLUE_BG, CYAN, INK, INK2, LINE, ORANGE, VIOLET, Canvas, ease, ease_out, fade, font,
                     seg, shot)

RED = (240, 72, 72)


# ---- blueprint: incident and reflected cones on the mask ------------------------------------
def cone_diagram(c, t, a, angle_deg, label, half_deg=4.73):
    """Orthographic side view: mask plane, normal, incident cone (left) and reflected cone (right).
    half_deg: cone half-angle at the mask, asin(NA / magnification) = 4.73 deg for the NXE (NA 0.33, 4x)."""
    px, py, L = 960, 820, 640
    d = ease_out(seg(t, 0.0, 1.0))
    c.line((px - 760 * d, py), (px + 760 * d, py), LINE, 5, a)
    c.text((px - 760, py + 40), "掩模平面", 26, LINE, a * d)
    for k in range(0, 600, 30):                                        # dashed normal
        c.line((px, py - k), (px, py - k - 16), LINE, 2, a * 0.8 * ease(seg(t, 0.6, 1.2)))
    c.text((px + 14, py - 620), "法线", 24, LINE, a * ease(seg(t, 0.6, 1.2)))
    g = ease_out(seg(t, 1.0, 2.2))
    for sgn, start in ((-1, 1.0), (1, 2.0)):                            # incident, then reflected
        gg = ease_out(seg(t, start, start + 1.2))
        if gg <= 0:
            continue
        for edge in (-half_deg, half_deg):
            th = math.radians(angle_deg + edge)
            x = px + sgn * L * math.sin(th)
            y = py - L * math.cos(th)
            if sgn < 0:
                c.line((x, y), (x + (px - x) * gg, y + (py - y) * gg), LINE, 3, a)
            else:
                c.line((px, py), (px + (x - px) * gg, py + (y - py) * gg), LINE, 3, a)
        if sgn > 0 and gg > 0.6:                                       # pattern stripes in the reflection
            for k in range(1, 9):
                r = L * k / 9 * gg
                th0, th1 = math.radians(angle_deg - half_deg), math.radians(angle_deg + half_deg)
                p0 = (px + r * math.sin(th0), py - r * math.cos(th0))
                p1 = (px + r * math.sin(th1), py - r * math.cos(th1))
                c.line(p0, p1, VIOLET if k % 2 else LINE, 2, a * 0.7)
    arc = ease(seg(t, 3.0, 3.8))
    if arc > 0:
        R = 260
        n = 24
        for i in range(int(n * arc)):
            t0 = math.radians(angle_deg * i / n)
            t1 = math.radians(angle_deg * (i + 1) / n)
            c.line((px - R * math.sin(t0), py - R * math.cos(t0)), (px - R * math.sin(t1), py - R * math.cos(t1)),
                   LINE, 3, a)
        c.text((px - 200, py - 330), label, 56, LINE, a * arc, anchor="mm", weight_glow=True)
    return c


@shot("B6_04")
def incidence(t, dur, W, H):
    c = Canvas(W, H, bg=BLUE_BG)
    c.grid(a=0.55)
    a = fade(t, 0.0, dur, dur, 0.3)
    cone_diagram(c, t, a, 6.0, "≈ 6°", half_deg=math.degrees(math.asin(0.33 / 4)))
    c.text((960, 110), "NXE：入射角 ≈ 6°（主光线相对法线）", 32, LINE, a * ease(seg(t, 3.4, 4.0)), anchor="mm")
    return c.finish(glow_radius=8)


# ---- SEM top-down: OPC / ILT shapes ---------------------------------------------------------
def _sem(im_l, blur=1.2, grain=0.2):
    im_l = im_l.filter(ImageFilter.GaussianBlur(blur))
    noise = Image.effect_noise(im_l.size, 30)
    return Image.blend(im_l, noise, grain).convert("RGB")


PITCH = 104                          # design px = nm on the mask: the densest NXE pitch, 26 nm on the wafer x 4


def _feature(d, x0, x1, yc, w, p, ends=(True, True), fill=170):
    """A horizontal line (mask: p=0) with hammerheads at its free ends; p=1 is the printed resist line (straight,
    ends slightly rounded, no hammerheads). Returns nothing; draws on the L image."""
    d.rectangle((x0, yc - w / 2, x1, yc + w / 2), fill=fill)
    hh = (1 - p) * w * 0.32                                            # hammerhead overhang
    hl = w * 0.9
    for x, e, sgn in ((x0, ends[0], 1), (x1, ends[1], -1)):
        if not e:
            continue
        if hh > 0.5:
            xa, xb = (x, x + sgn * hl) if sgn > 0 else (x + sgn * hl, x)
            d.rectangle((min(xa, xb), yc - w / 2 - hh, max(xa, xb), yc + w / 2 + hh), fill=fill)
        if p > 0.05:                                                   # printed ends round off a little
            r = w / 2 * p
            d.ellipse((x - r, yc - w / 2, x + r, yc + w / 2), fill=fill)


def sem_field(Wpx, Hpx, p, pan, seed=4):
    """SEM view of OPC'd mask features (p=0) or the straight lines they print (p=1): dense lines at the 104 nm mask
    pitch with hammerheads at line ends, an L-shaped wire with a corner serif and a jog, and isolated lines flanked
    by thin assist bars that do not print (US 7,694,267). Design px = nm on the mask."""
    rnd = random.Random(seed)
    s = Hpx / 1080
    im = Image.new("L", (Wpx, Hpx), 62)
    d = ImageDraw.Draw(im)
    w = PITCH / 2

    def X(v):
        return (v - pan) * s
    # region A: dense lines, segments with line ends facing each other across small gaps
    for k in range(10):
        yc = (110 + k * PITCH) * s
        x = -200 + rnd.uniform(0, 160)
        while x < 1150:
            ln = rnd.choice((260, 340, 420, 560))
            _feature(d, X(x), X(min(x + ln, 1150)), yc, w * s, p, ends=(x > -150, x + ln < 1150))
            x += ln + 110
    # region B: two isolated lines, each with assist bars above and below (they vanish in print)
    for yc0 in (318, 734):
        yc = yc0 * s
        _feature(d, X(1260), X(1900), yc, w * s, p)
        sa = 1 - p
        if sa > 0.02:
            for off in (-1, 1):
                ya = yc + off * 0.9 * PITCH * s
                d.rectangle((X(1280), ya - 7 * s, X(1880), ya + 7 * s), fill=int(62 + (150 - 62) * sa))
    # region C: an L-shaped wire with a serif on its outer corner and a jog
    for yc0, x0 in ((214, 2050), (630, 2120)):
        yc = yc0 * s
        xc = X(x0 + 420)
        d.rectangle((X(x0), yc - w / 2 * s, xc + w / 2 * s, yc + w / 2 * s), fill=170)
        d.rectangle((xc - w / 2 * s, yc, xc + w / 2 * s, yc + 300 * s), fill=170)
        if p < 0.98:
            sr = (1 - p) * 18 * s                                       # serif on the outer corner
            d.rectangle((xc + w / 2 * s - sr, yc - w / 2 * s - sr, xc + w / 2 * s + sr, yc - w / 2 * s + sr), fill=170)
            d.rectangle((xc - w / 2 * s - sr, yc + 300 * s - sr * 0.2, xc + w / 2 * s + sr, yc + 300 * s + sr), fill=170)
        jog = 0.5 * w * s                                              # a jog: the line steps by half a width
        d.rectangle((X(x0 - 300), yc - w / 2 * s + jog, X(x0), yc + w / 2 * s + jog), fill=170)
    return _sem(im)


def _scale_bar(c, a, label):
    c.rect((60, 980, 60 + PITCH, 990), fill=INK, a=a)
    c.text((60, 950), label, 22, INK, a, anchor="lm")


@shot("B6_05")
def opc_sem(t, dur, W, H):
    c = Canvas(W, H)
    a = fade(t, 0.0, dur, dur, 0.3)
    c.img.paste(sem_field(W, H, 0.0, pan=60 * t), (0, 0))
    _scale_bar(c, a, "104 nm（掩模上）")
    c.text((1860, 60), "掩模图形（示意）", 26, INK, a, anchor="ra")
    out = c.finish(vignette=True)
    return Image.blend(Image.new("RGB", out.size), out, a)


@shot("B6_07")
def opc_morph(t, dur, W, H):
    c = Canvas(W, H)
    a = fade(t, 0.0, dur, dur, 0.3)
    p = ease(seg(t, 0.3, dur - 0.6))
    c.img.paste(sem_field(W, H, p, pan=60 * (4.46 + t)), (0, 0))
    # same picture scale, but the end state is the wafer: 4x smaller in reality, shown enlarged 4x
    lab = ease(seg(t, dur - 1.4, dur - 0.9))
    _scale_bar(c, a * (1 - lab), "104 nm（掩模上）")
    _scale_bar(c, a * lab, "26 nm（晶圆上）")
    c.text((1860, 60), "掩模图形（示意）", 26, INK, a * (1 - lab), anchor="ra")
    c.text((1860, 60), "晶圆上的线条（已按 4× 放大显示）", 26, INK, a * lab, anchor="ra")
    out = c.finish(vignette=True)
    return Image.blend(Image.new("RGB", out.size), out, a)


# ---- infographic: computational lithography in three beats ----------------------------------
def _lines(c, x, y, a, col, outline=True, rounded=0, shorten=0, width=3):
    for k in range(3):
        yy = y + k * 70
        box = (x + shorten, yy, x + 380 - shorten, yy + 34)
        if outline:
            c.rect(box, outline=col, width=width, a=a, radius=rounded)
        else:
            c.rect(box, fill=col, a=a, radius=rounded)


def _opc_mask(c, x, y, a):
    for k in range(3):
        yy = y + k * 70
        c.rect((x, yy, x + 380, yy + 34), fill=INK2, a=a)
        for xe in (x - 14, x + 380 - 16):                        # hammerheads
            c.rect((xe, yy - 10, xe + 30, yy + 44), fill=INK2, a=a)
        for (cx, cy) in ((x + 30, yy - 6), (x + 350, yy + 40)):  # serifs
            c.rect((cx - 8, cy - 4, cx + 8, cy + 4), fill=INK2, a=a)
        c.rect((x + 60, yy + 50, x + 320, yy + 55), fill=INK2, a=a * 0.6)   # assist bar


@shot("B6_06")
def comp_litho(t, dur, W, H):
    c = Canvas(W, H)
    a = fade(t, 0.0, dur, dur, 0.3)
    cols = [140, 760, 1380]
    # beat 1: the target
    b1 = ease(seg(t, 0.2, 1.0))
    c.text((cols[0] + 190, 150), "① 目标图形", 34, INK, a * b1, anchor="mm")
    _lines(c, cols[0], 560, a * b1, CYAN)
    c.text((cols[0] + 190, 850), "一组笔直的线", 26, INK2, a * b1, anchor="mm")
    # beat 2: draw it as-is on the mask -> corners round off, line ends pull back
    b2 = ease(seg(t, 2.6, 3.4))
    c.text((cols[1] + 190, 150), "② 照原样画在掩模上", 34, INK, a * b2, anchor="mm")
    _lines(c, cols[1], 260, a * b2, INK2, outline=False)
    arrow2 = ease(seg(t, 3.6, 4.4))
    c.line((cols[1] + 190, 480), (cols[1] + 190, 540), INK2, 3, a * arrow2)
    c.text((cols[1] + 210, 510), "衍射 + 光刻胶", 20, INK2, a * arrow2, anchor="lm")
    r2 = ease(seg(t, 4.2, 5.0))
    _lines(c, cols[1], 560, a * r2 * 0.6, INK2, outline=True, width=1)               # target, dashed-ish
    _lines(c, cols[1], 560, a * r2, RED, outline=True, rounded=17, shorten=34)
    c.text((cols[1] + 190, 850), "边角磨圆 · 线头缩短", 26, RED, a * r2, anchor="mm")
    # beat 3: draw it "wrong" on purpose -> prints straight
    b3 = ease(seg(t, 6.0, 6.8))
    c.text((cols[2] + 190, 150), "③ 计算机“反着画”", 34, INK, a * b3, anchor="mm")
    _opc_mask(c, cols[2], 260, a * b3)
    arrow3 = ease(seg(t, 7.0, 7.8))
    c.line((cols[2] + 190, 480), (cols[2] + 190, 540), CYAN, 3, a * arrow3)
    c.text((cols[2] + 210, 510), "衍射 + 光刻胶", 20, CYAN, a * arrow3, anchor="lm")
    r3 = ease(seg(t, 7.6, 8.4))
    _lines(c, cols[2], 560, a * r3, CYAN, outline=True, rounded=4)
    c.text((cols[2] + 190, 850), "投出来正好笔直 ✓", 26, CYAN, a * r3, anchor="mm", weight_glow=True)
    c.text((960, 1010), "计算光刻：把变形提前算进掩模（示意）", 22, INK2, a, anchor="mm")
    return c.finish(glow_radius=8, glow_gain=0.7)


# ---- HUD: one particle, every die -------------------------------------------------------------
MM_PX = 430 / 150                     # wafer graphics: 300 mm wafer drawn with a 430 px radius
FULL = (26 * MM_PX, 33 * MM_PX)       # 26 x 33 mm full field (NXE) = 74.5 x 94.6 px
HALF = (26 * MM_PX, 16.5 * MM_PX)     # 26 x 16.5 mm half field (High-NA)


def _fields(cx, cy, R, fw=FULL[0], fh=FULL[1]):
    """Exposure fields at true size on a wafer of radius R (px), every field that touches the wafer, edge fields
    included: columns on the wafer centre line, rows centred. This gives 96 full fields and 188 half fields on a
    300 mm wafer, the counts ASML quotes (F45, F52). Serpentine scan order."""
    out = []
    nx, ny = int(R / fw) + 2, int(R / fh) + 2
    for j in range(-ny, ny + 1):
        row = []
        for i in range(-nx, nx + 1):
            x0, y0 = cx + i * fw, cy - fh / 2 + j * fh
            inside = any(math.hypot(x0 + (u + 0.5) * fw / 6 - cx, y0 + (v + 0.5) * fh / 6 - cy) <= R
                         for u in range(6) for v in range(6))
            if inside:
                row.append((x0, y0, fw, fh))
        out.extend(row if j % 2 == 0 else row[::-1])
    return out


def clipped(c, cx, cy, R, draw):
    """Run draw() on a transparent layer and composite it clipped to the wafer circle (edge fields are cut)."""
    layer = Image.new("RGBA", c.img.size, (0, 0, 0, 0))
    d0 = c.d
    c.d = ImageDraw.Draw(layer, "RGBA")
    draw()
    c.d = d0
    m = Image.new("L", c.img.size, 0)
    ImageDraw.Draw(m).ellipse([c.px(cx - R), c.px(cy - R), c.px(cx + R), c.px(cy + R)], fill=255)
    layer.putalpha(ImageChops.multiply(layer.getchannel("A"), m))
    c.img.paste(layer, (0, 0), layer)


@shot("B6_09")
def every_die(t, dur, W, H):
    c = Canvas(W, H)
    a = fade(t, 0.0, dur, dur, 0.3)
    # 0-1.1 s: the grain lands on the mask
    if t < 1.3:
        m = 1 - ease(seg(t, 1.0, 1.3))
        c.rect((560, 240, 1360, 840), fill=(40, 44, 54), outline=INK2, width=2, a=a * m)
        for k in range(12):
            c.line((600, 280 + 46 * k), (1320, 280 + 46 * k), (70, 76, 92), 8, a * m)
        fall = ease(seg(t, 0.0, 0.8))
        c.circle((1010, 200 + 360 * fall), 9, fill=(230, 226, 214), a=a * m, glow=True)
        if t > 0.8:
            ring = ease_out(seg(t, 0.8, 1.2))
            c.circle((1010, 560), 20 + 40 * ring, outline=RED, width=3, a=a * m * (1 - ring * 0.5))
        c.text((960, 120), "掩模上落下 1 颗颗粒", 34, INK, a * m, anchor="mm")
        if t < 1.0:
            return c.finish()
    cx, cy, R = 960, 560, 430
    w = ease(seg(t, 1.0, 1.4))
    shift = (1 - w) * 600                                        # whip-pan in
    c.circle((cx + shift, cy), R, fill=(26, 30, 40), outline=INK2, width=2, a=a * w)
    fields = _fields(cx + shift, cy, R)
    N = len(fields)
    prog = ease(seg(t, 1.6, dur - 0.7)) ** 1.6                    # accelerating
    lit = int(N * prog)

    def draw():
        for k, (x0, y0, fw, fh) in enumerate(fields):
            if k < lit:
                flash = max(0.0, 1 - (prog * N - k) / 4)
                c.rect((x0 + 3, y0 + 3, x0 + fw - 3, y0 + fh - 3),
                       fill=(int(60 + 120 * flash), int(52 + 90 * flash), int(110 + 120 * flash)),
                       outline=CYAN, width=1, a=a * w * 0.9)
                c.rect((x0 + fw * 0.62, y0 + fh * 0.3, x0 + fw * 0.82, y0 + fh * 0.46), outline=RED, width=2, a=a * w)
            else:
                c.rect((x0 + 3, y0 + 3, x0 + fw - 3, y0 + fh - 3), outline=(54, 60, 76), width=1, a=a * w)
    clipped(c, cx + shift, cy, R, draw)
    c.text((1560, 420), "缺陷芯片", 28, INK2, a * w, anchor="lm")
    c.text((1560, 480), f"{lit} / {N}", 52, RED if lit else INK, a * w, anchor="lm", weight_glow=lit == N)
    c.text((1560, 560), "良率损失 100%（满场芯片）", 30, RED, a * ease(seg(t, dur - 1.2, dur - 0.7)), anchor="lm")
    c.text((960, 1010), "示意：同一个缺陷被复制到每一个曝光场", 22, INK2, a, anchor="mm")
    return c.finish(glow_radius=8, glow_gain=0.7)


# ---- 1 / 1,000,000 ----------------------------------------------------------------------------
@shot("B6_11")
def one_in_million(t, dur, W, H):
    c = Canvas(W, H)
    a = fade(t, 0.0, dur, dur, 0.3)
    N = 1000
    z = ease(seg(t, 0.2, dur - 0.5))
    span = 12 * (N / 12) ** z                  # how many dots fit across the frame height
    pitch = 1000 / span                        # in design px
    cx, cy = 960, 540
    red_ij = (0, 0)                            # the red dot sits at the array centre
    mix = ease(seg(pitch, 9, 20))                # 1: discrete dots; 0: star-field square
    if mix > 0:
        r = max(1.0, pitch * 0.18)
        half_x, half_y = int(1000 / pitch) + 1, int(560 / pitch) + 1
        for i in range(-half_x, half_x + 1):
            for j in range(-half_y, half_y + 1):
                if abs(i) > N // 2 or abs(j) > N // 2 or (i, j) == red_ij:
                    continue
                c.circle((cx + i * pitch, cy + j * pitch), r, fill=(210, 214, 230), a=a * 0.85 * mix)
    if mix < 1:
        side = N * pitch
        c.rect((cx - side / 2, cy - side / 2, cx + side / 2, cy + side / 2), fill=(30, 32, 40), outline=(70, 74, 90),
               width=1, a=a * (1 - mix))
        rs = random.Random(11)
        for _ in range(4200):
            x = cx + (rs.random() - 0.5) * side
            y = cy + (rs.random() - 0.5) * side
            c.circle((x, y), 1.2, fill=(200, 204, 220), a=a * (1 - mix) * (0.4 + 0.6 * rs.random()))
    c.circle((cx, cy), max(5.0, pitch * 0.22), fill=RED, a=a, glow=True)
    c.text((960, 1000), "1 / 1,000,000", 48, INK, a * ease(seg(t, dur - 1.4, dur - 0.8)), anchor="mm", weight_glow=True)
    return c.finish(glow_radius=10, glow_gain=1.4)


# ---- energy: dust on the pellicle prints nothing ---------------------------------------------
@shot("B6_15")
def defocus(t, dur, W, H):
    c = Canvas(W, H, bg=(0, 0, 0))
    a = fade(t, 0.0, dur, dur, 0.3)
    p = ease(seg(t, 0.6, dur - 0.8))
    # left: side view — cones converge on the mask plane; the grain on the pellicle sits in a wide cone
    my, py_ = 760, 520
    c.line((120, my), (860, my), (90, 96, 120), 3, a)
    c.line((120, py_), (860, py_), (90, 96, 120), 2, a)
    c.text((130, my + 30), "掩模面（焦平面）", 22, INK2, a)
    c.text((130, py_ - 40), "保护膜", 22, INK2, a)
    for k, x in enumerate((300, 440, 580, 720)):
        c.line((x - 70, 260), (x, my), VIOLET, 2, a * 0.7, glow=True)
        c.line((x + 70, 260), (x, my), VIOLET, 2, a * 0.7, glow=True)
    c.circle((452, py_ - 8), 9, fill=(236, 230, 214), a=a, glow=True)
    c.line((900, py_), (900, my), INK2, 2, a)
    c.text((915, (py_ + my) / 2), "离焦距离", 22, INK2, a, anchor="lm")
    # right: image plane — the pattern stays sharp; the grain's shadow spreads and fades away
    x0, y0, w, h = 1040, 240, 740, 600
    c.rect((x0, y0, x0 + w, y0 + h), outline=(60, 64, 84), width=2, a=a)
    for k in range(7):
        c.rect((x0 + 60, y0 + 50 + k * 78, x0 + w - 60, y0 + 50 + k * 78 + 34), fill=(176, 146, 255), a=a * 0.85, glow=True)
    shadow = Image.new("L", (W, H), 0)
    sd = ImageDraw.Draw(shadow)
    k = H / 1080
    r = (16 + 220 * p) * k
    sx, sy = (x0 + w * 0.45) * k, (y0 + h * 0.5) * k
    sd.ellipse((sx - r, sy - r, sx + r, sy + r), fill=int(230 * (1 - p) ** 1.5))
    shadow = shadow.filter(ImageFilter.GaussianBlur(max(1, r * 0.45)))
    c.img = Image.composite(Image.new("RGB", (W, H), (0, 0, 0)), c.img, shadow)
    c.d = ImageDraw.Draw(c.img, "RGBA")
    c.text((x0 + w / 2, y0 + h + 50), "像面：图形清晰，灰尘的影子化开", 24, INK, a, anchor="mm")
    c.text((960, 1010), "小颗粒离焦 → 印不出来（示意）", 22, INK2, a, anchor="mm")
    return c.finish(glow_radius=10, glow_gain=0.8)


# ---- type card: "indistinguishable from magic" ----------------------------------------------
@shot("B6_16")
def magic(t, dur, W, H):
    c = Canvas(W, H, bg=(6, 4, 6))
    a = fade(t, 0.0, dur, dur, 0.5)
    rnd = random.Random(16)
    for k in range(34):                                        # drifting bokeh of the hot membrane
        x = rnd.uniform(0, 1920) + 30 * math.sin(0.3 * t + k)
        y = rnd.uniform(0, 1080) + 20 * math.cos(0.25 * t + 2 * k)
        r = rnd.uniform(40, 160)
        col = (rnd.randint(120, 200), rnd.randint(30, 60), rnd.randint(40, 80))
        c.circle((x, y), r, fill=col, a=a * rnd.uniform(0.08, 0.22), glow=True)
    c.img = c.img.filter(ImageFilter.GaussianBlur(c.px(26)))
    c.d = ImageDraw.Draw(c.img, "RGBA")
    title = "与魔法无异"
    size = 150
    f = font(int(c.px(size)))
    total = sum(f.getlength(ch) for ch in title) / c.k
    x = 960 - total / 2
    for i, ch in enumerate(title):
        ca = ease(seg(t, 0.5 + 0.28 * i, 1.1 + 0.28 * i))
        c.text((x, 470), ch, size, (246, 236, 232), a * ca, anchor="lm", weight_glow=True)
        x += f.getlength(ch) / c.k
    sub = ease(seg(t, 2.3, 3.0))
    c.text((960, 640), "Indistinguishable from magic: the EUV pellicle · ASML, 2022", 30, INK2, a * sub,
           anchor="mm")
    return c.finish(glow_radius=18, glow_gain=0.8)
