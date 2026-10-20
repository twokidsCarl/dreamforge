"""E2 A0 的 2D 镜头（Pillow）：排版、神经元线稿、蓝图、片名、HUD，以及 A0_04a 的叠字后处理。

配色和共用常量在 blender/scripts/e2_common.py（通道蓝 = 打开，抑制琥珀 = 关掉，膜青，线稿白）。
每个镜头是 draw(t, dur, W, H) -> PIL.Image；全部用 2 倍超采样再缩小（线条不起锯齿）。动画时间点按“分镜板面时长”写，
真实时长（配音定时后）不同时按比例缩放（_warp）；排版镜头里需要贴着结尾的动作（光标）从结尾倒推。
2D 镜头自己带文字，字幕和右上标签由 edit_film.py 叠加；下方约 18% 不放主要文字（字幕安全区）。
"""
import math
import os
import random
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "blender", "scripts"))

import build_neuron as BN  # noqa: E402
import e2_common as E  # noqa: E402
from mograph import RENDERS, Canvas, ease, ease_out, seg, shot  # noqa: E402
from overlay_labels import font, mono_font, serif_font  # noqa: E402

SS = 2                                    # 超采样倍数
FPS = 24
BG = (6, 7, 11)
INK = (238, 235, 226)                     # 排版的暖白
BP_BG = (12, 52, 122)                     # 蓝图底（与 mograph 的 BLUE_BG 同）
BP_GRID = (40, 88, 160)
BP_LINE = (222, 236, 255)

# 盒子（「开关」）在 A0_05a 和 A0_05b 里位置相同（1080p 坐标）
BOX = (790.0, 310.0, 1130.0, 650.0)
BOX_C = ((BOX[0] + BOX[2]) / 2, (BOX[1] + BOX[3]) / 2)

QUOTE = "理想的信号，也许是光"
QUOTE_FULL = "理想的信号，也许是光。"
TITLE = "光遗传学"


# ---- 共用小工具 ----------------------------------------------------------------------------
def _canvas(W, H, bg=BG):
    return Canvas(W * SS, H * SS, bg)


def _done(c, W, H, glow_radius=14, glow_gain=1.0, vignette=False):
    return c.finish(glow_radius=glow_radius, glow_gain=glow_gain, vignette=vignette).resize((W, H), Image.LANCZOS)


def _warp(t, dur, base):
    """把真实时间 t 换成“板面时长 base 秒”下的时间，动画时间点按 base 写。"""
    return t * base / dur if dur > 0 else t


def _mix(a, b, k):
    k = max(0.0, min(1.0, k))
    return tuple(int(round(a[i] + (b[i] - a[i]) * k)) for i in range(3))


def _scale(col, k):
    return tuple(int(c * k) for c in col)


def _stext(c, xy, s, size, color=INK, a=1.0, anchor="la", fnt=serif_font, glow=0.0):
    """用指定字体写字（Canvas.text 只有黑体）。xy 是 1080p 坐标；glow>0 时同时写进发光层。"""
    c.text_font(xy, s, fnt(int(c.px(size))), color, a, anchor, glow)


def _poly(c, pts, color, width, a=1.0, glow=False):
    for p, q in zip(pts[:-1], pts[1:]):
        c.line(p, q, color=color, width=width, a=a, glow=glow)


def _zoom(img, z):
    """以画面中心放大 z 倍（慢推镜）。img 已经是目标尺寸的 SS 倍时先裁再缩更清晰；这里直接裁再缩回原尺寸。"""
    if z <= 1.0001:
        return img
    W, H = img.size
    w, h = W / z, H / z
    return img.crop(((W - w) / 2, (H - h) / 2, (W + w) / 2, (H + h) / 2)).resize((W, H), Image.LANCZOS)


# ---- A0_01b / A0_02a：排版 ------------------------------------------------------------------
QUOTE_SIZE = 78
QUOTE_Y = 520                             # 01b 里这句的纵向中心（1080p）


def _quote_line(c, y, a):
    _stext(c, (960, y), QUOTE_FULL, QUOTE_SIZE, INK, a, anchor="mm", glow=0.25)


@shot("A0_01b")
def a0_01b(t, dur, W, H):
    c = _canvas(W, H, (0, 0, 0))
    _quote_line(c, QUOTE_Y, ease(seg(t, 0.12, 0.7)))          # 轻微淡入，之后停住
    return _done(c, W, H, glow_radius=10)


@shot("A0_02a")
def a0_02a(t, dur, W, H):
    c = _canvas(W, H, (0, 0, 0))
    up = ease(seg(t, 0.35, 1.25))
    _quote_line(c, QUOTE_Y - 120 * up, 1.0 - 0.58 * up)       # 上一句上移并变暗
    word = "相当牵强"
    f = serif_font(int(c.px(QUOTE_SIZE)))
    full_w = c.d.textlength(word, font=f) / c.px(1)
    x0 = 960 - full_w / 2
    y = QUOTE_Y + 40
    type_start = max(1.5, dur - 2.3)                          # 打字、光标都从结尾倒推：留出 2 次闪烁后停住
    cps = 0.2
    n = max(0, min(len(word), int((t - type_start) / cps) + 1)) if t >= type_start else 0
    typed = word[:n]
    if typed:
        _stext(c, (x0, y), typed, QUOTE_SIZE, INK, 1.0, anchor="lm", glow=0.25)
    cur_x = x0 + (c.d.textlength(typed, font=f) / c.px(1) if typed else 0) + 6
    type_end = type_start + len(word) * cps
    # 光标：打字前 0.3 秒出现；打完后 灭-亮-灭-亮，然后一直亮着
    if t >= type_start - 0.3:
        if t < type_end + 0.12:
            on = True
        else:
            u = t - type_end - 0.12
            on = not (u < 0.25 or 0.5 <= u < 0.75)
    else:
        on = False
    if on:
        c.rect((cur_x, y - QUOTE_SIZE * 0.46, cur_x + 5, y + QUOTE_SIZE * 0.46), fill=INK, glow=True)
    return _done(c, W, H, glow_radius=10)


# ---- A0_03a：一排神经元线稿 ---------------------------------------------------------------------
ROW_SCALE = 154.0                         # BU -> 1080p 像素（间距 1.2 BU = 185 px）
ROW_Y = 410.0                             # 胞体所在高度
_MORPH = [BN.morphology(s) for s in E.NEURON_SEEDS]


def _row_x(i):
    return 960 + (i - (E.NEURON_COUNT - 1) / 2) * BN.SPACING * ROW_SCALE


def _draw_neuron(c, i, col, a, widen=1.0, glow=False):
    m = _MORPH[i]
    ox, oy = _row_x(i), ROW_Y
    for pts, rad in m["dendrites"] + [m["axon"]] + m["twigs"]:
        p2 = [(ox + p[0] * ROW_SCALE, oy - p[2] * ROW_SCALE) for p in pts]
        w = max(1.6, rad[0] * ROW_SCALE * 1.15) * widen
        _poly(c, p2, col, w, a, glow=glow)
    r = m["soma_r"] * ROW_SCALE
    c.circle((ox, oy), r, fill=_scale(col, 0.22), outline=col, width=3.0 * widen, a=a, glow=glow)
    for b in m["boutons"]:
        c.circle((ox + b[0] * ROW_SCALE, oy - b[2] * ROW_SCALE), 4.6, fill=col, a=a, glow=glow)


@shot("A0_03a")
def a0_03a(t, dur, W, H):
    s = t   # 真实秒；按 review_words 对齐旁白：「打开」3.80 s、「关掉」4.82 s、「旁边的细胞大体不动」6.22 s（屏幕字跟旁白用同一说法）
    c = _canvas(W, H, (8, 10, 16))
    for i in range(E.NEURON_COUNT):
        circled = i in E.NEURON_CIRCLED
        a_in = ease(seg(s, 0.05 + 0.05 * i, 0.75 + 0.05 * i))
        k_open = ease(seg(s, 3.6, 4.0)) if circled else 0.0           # 灰 -> 通道蓝
        k_off = ease(seg(s, 4.85, 5.5)) if circled else 0.0            # 蓝 -> 琥珀并压暗
        col = _mix(_mix(E.GREY, E.CHANNEL, k_open), E.AMBER, k_off)
        bright = 1.0 - 0.38 * k_off
        _draw_neuron(c, i, _scale(col, bright), a_in, widen=1.0 + 0.25 * k_open * (1 - k_off),
                     glow=circled and 0.3 < k_open * (1 - k_off))
        if circled:
            # 细线圈：围着胞体画出来（弧线逐渐闭合）
            g = ease(seg(s, 1.1 + 0.18 * E.NEURON_CIRCLED.index(i), 1.9 + 0.18 * E.NEURON_CIRCLED.index(i)))
            if g > 0:
                ox, oy, rr = c.px(_row_x(i)), c.px(ROW_Y), c.px(64)
                c.d.arc([ox - rr, oy - rr, ox + rr, oy + rr], -90, -90 + 360 * g, fill=(*E.LINE, 235),
                        width=max(2, int(c.px(2.2))))
            if 3.75 < s < 4.95:                                              # 沿轴突走一道脉冲
                path = BN.axon_path(_MORPH[i])
                u = ease(seg(s, 3.75, 4.85))
                for k in range(10):                                        # 拖尾
                    uu = max(0.0, u - 0.025 * k)
                    p, _ = BN.path_at(path, uu)
                    c.circle((_row_x(i) + p[0] * ROW_SCALE, ROW_Y - p[2] * ROW_SCALE), 9 - 0.7 * k,
                             fill=E.CHANNEL, a=(1 - k / 10) * 0.9, glow=True)
    lab_open = ease(seg(s, 3.7, 4.0)) * (1 - ease(seg(s, 4.75, 4.95)))
    lab_off = ease(seg(s, 4.95, 5.25))
    c.text((960, 120), "打开", 58, E.CHANNEL, lab_open, anchor="mm", weight_glow=True)
    c.text((960, 120), "关掉", 58, E.AMBER, lab_off, anchor="mm", weight_glow=True)
    c.text((960, 770), "旁边大体不动", 38, E.GREY, ease(seg(s, 6.1, 6.6)), anchor="mm")
    return _done(c, W, H, glow_radius=12, glow_gain=0.5)


# ---- A0_04a：Blender 帧 + 名字叠加 ---------------------------------------------------------------
def _raw_frame(sid, f, W):
    q = {640: "preview", 960: "sample", 1920: "final"}[W]
    p = os.path.join(RENDERS, "shots", sid, q + "_raw", f"{f:04d}.png")
    if not os.path.exists(p):
        raise FileNotFoundError(f"{p} 不存在：先渲 {sid}（registry 里 raw: true，写到 {q}_raw）")
    return Image.open(p).convert("RGB")


@shot("A0_04a")
def a0_04a(t, dur, W, H):
    """Blender 渲出的光点帧（<quality>_raw）+ 名字 + 日期行，写到 <quality>/。名字随光点位置投影（e2_common.a04_project）。"""
    f = int(round(t * FPS)) + 1
    base = _raw_frame("A0_04a", f, W).resize((W, H), Image.LANCZOS)
    k = H / 1080
    layer = Image.new("RGB", (W, H), (0, 0, 0))
    glow = Image.new("RGB", (W, H), (0, 0, 0))
    d, g = ImageDraw.Draw(layer, "RGBA"), ImageDraw.Draw(glow)
    fn = font(int(40 * k))
    for i, name in enumerate(E.LIGHT_NAMES):
        a = ease(seg(t, E.A04_LIGHT_AT[i] + 0.3, E.A04_LIGHT_AT[i] + 1.0))
        if a <= 0:
            continue
        x, y = E.a04_project(i, t, W, H, dur)
        pos = (x, y + 92 * k)
        col = _mix(E.LINE, E.CHANNEL, 0.25)
        d.text(pos, name, font=fn, fill=(*col, int(255 * a)), anchor="mt")
        g.text(pos, name, font=fn, fill=_scale(col, a * 0.5), anchor="mt")
    a = ease(seg(t, E.A04_DATE_AT, E.A04_DATE_AT + 0.8))
    if a > 0:
        fd = font(int(42 * k))
        pos = (W / 2, 0.14 * H)          # 放在光点上方：0.745H 会压在 Hegemann 到 Nagel 的光丝上（v1 审片）
        d.text(pos, E.DATE_LINE, font=fd, fill=(*E.LINE, int(255 * a)), anchor="mm")
        g.text(pos, E.DATE_LINE, font=fd, fill=_scale(E.LINE, a * 0.4), anchor="mm")
    glow = glow.filter(ImageFilter.GaussianBlur(10 * k))
    # 文字层画在黑底上：取逐像素较亮者（文字比背景亮），再加发光
    return ImageChops.add(ImageChops.lighter(base, layer), glow)


# ---- A0_04b ------------------------------------------------------------------------------------
@shot("A0_04b")
def a0_04b(t, dur, W, H):
    c = _canvas(W, H, (0, 0, 0))
    for i, name in enumerate(E.LIGHT_NAMES):
        a = ease(seg(t, 0.04 + 0.07 * i, 0.3 + 0.07 * i))
        _stext(c, (960, 400 + 100 * i), name, 62, INK, a, anchor="mm", glow=0.2)
    return _done(c, W, H, glow_radius=10)


# ---- A0_05a：蓝图 ------------------------------------------------------------------------------
def _dashed_rect(c, box, color, width, progress, a=1.0, dash=18, gap=12, glow=False):
    """矩形虚线框，沿周长顺时针从左上角画出 progress（0–1）。"""
    x0, y0, x1, y1 = box
    pts = [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)]
    total = 2 * ((x1 - x0) + (y1 - y0))
    limit = total * progress
    pos = 0.0
    for p, q in zip(pts[:-1], pts[1:]):
        L = math.dist(p, q)
        d0 = 0.0
        while d0 < L and pos + d0 < limit:
            d1 = min(L, d0 + dash, limit - pos)
            u0, u1 = d0 / L, d1 / L
            c.line((p[0] + (q[0] - p[0]) * u0, p[1] + (q[1] - p[1]) * u0),
                   (p[0] + (q[0] - p[0]) * u1, p[1] + (q[1] - p[1]) * u1), color=color, width=width, a=a, glow=glow)
            d0 += dash + gap
        pos += L


@shot("A0_05a")
def a0_05a(t, dur, W, H):
    s = _warp(t, dur, 9.76)
    c = _canvas(W, H, BP_BG)
    c.grid(step=60, color=BP_GRID, a=0.55 * ease(seg(s, 0.0, 0.6)))
    # 图框
    fa = ease(seg(s, 0.0, 0.8))
    c.rect((60, 60, 1860, 880), outline=BP_LINE, width=2, a=0.5 * fa)
    # 右：三个人名（旁白第一句「名单上是这三个人」）
    ys = (410, 480, 550)
    for i, name in enumerate(E.LIGHT_NAMES):
        a = ease(seg(s, 0.4 + 0.45 * i, 1.0 + 0.45 * i))
        c.text((1310, ys[i]), name, 50, BP_LINE, a, anchor="lm")
    lead_r = ease(seg(s, 2.0, 3.0))
    for i in range(3):
        c.line((BOX[2], BOX_C[1]), (1282, ys[i]), BP_LINE, 2, a=0.9, progress=lead_r)
        c.circle((1282, ys[i]), 5, fill=BP_LINE, a=lead_r)
    # 左：引文 + 出处（「一句自认牵强的设想」）
    qa = ease(seg(s, 3.2, 4.2))
    c.text((110, 440), QUOTE, 54, BP_LINE, qa, anchor="lm")
    c.line((110, 480), (712, 480), BP_LINE, 2, a=0.8 * qa)
    c.text((110, 522), "Crick · 1999", 32, _mix(BP_LINE, BP_BG, 0.25), qa, anchor="lm")
    lead_l = ease(seg(s, 4.3, 5.2))
    c.line((712, 480), (BOX[0] - 6, BOX_C[1]), BP_LINE, 2, a=0.9, progress=lead_l)
    c.circle((BOX[0] - 6, BOX_C[1]), 5, fill=BP_LINE, a=lead_l)
    # 中：空的虚线框，慢慢画出来，然后才写上「开关」（「中间缺的是一枚开关」）
    _dashed_rect(c, BOX, BP_LINE, 3, ease(seg(s, 5.3, 6.9)), a=1.0)
    la = ease(seg(s, 7.0, 7.7))
    c.text((BOX_C[0], BOX[1] - 44), "开关", 50, BP_LINE, la, anchor="mm")
    c.line((BOX_C[0], BOX[1] - 14), (BOX_C[0], BOX[1]), BP_LINE, 2, a=la)
    img = _done(c, W, H, glow_radius=8, glow_gain=0.6)
    z = 1.0 + 0.045 * ease(seg(s, 0.0, 9.76))                    # 慢推
    cx, cy = W / 2, H / 2
    w, h = W / z, H / z
    return img.crop((cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)).resize((W, H), Image.LANCZOS)


# ---- A0_05b：光走到一半熄灭 ---------------------------------------------------------------------------
@shot("A0_05b")
def a0_05b(t, dur, W, H):
    s = _warp(t, dur, 1.35)
    c = _canvas(W, H, (0, 0, 0))
    _dashed_rect(c, BOX, E.LINE, 3, 1.0, a=0.42)
    x_in, x_mid, y = BOX[0] + 16, BOX_C[0], BOX_C[1]
    run = ease(seg(s, 0.12, 0.78))                                # 从左走到一半
    head = x_in + (x_mid - x_in) * run
    fade = 1.0 - ease(seg(s, 0.8, 1.2))                          # 到一半就熄灭
    if s >= 0.12 and fade > 0:
        n = 36
        for k in range(n):
            u0, u1 = k / n, (k + 1) / n
            xa, xb = head - 190 * u0, head - 190 * u1
            if xa < x_in:
                break
            a = (1 - u0) ** 1.6 * fade
            c.line((xa, y), (max(xb, x_in), y), E.CHANNEL, 9 * (1 - 0.5 * u0), a=a * 0.55, glow=True)
            c.line((xa, y), (max(xb, x_in), y), (245, 250, 255), 3, a=a, glow=False)
        c.circle((head, y), 9, fill=(245, 250, 255), a=fade, glow=True)
    return _done(c, W, H, glow_radius=16, glow_gain=1.1)


# ---- A0_06a / A0_06b：片名 -------------------------------------------------------------------------
TITLE_SIZE = 210
TITLE_Y = 470
BEAM_Y = 640


def _title_canvas(W, H, a):
    c = _canvas(W, H, (0, 0, 0))
    f = serif_font(int(c.px(TITLE_SIZE)))
    gap = 36                                                      # 字距（1080p 像素）
    ws = [c.d.textlength(ch, font=f) / c.px(1) for ch in TITLE]
    total = sum(ws) + gap * (len(TITLE) - 1)
    x = 960 - total / 2
    for ch, w in zip(TITLE, ws):
        _stext(c, (x, TITLE_Y), ch, TITLE_SIZE, INK, a, anchor="lm", glow=0.35)
        x += w + gap
    return c


def _title(W, H, a=1.0):
    return _done(_title_canvas(W, H, a), W, H, glow_radius=18)


@shot("A0_06a")
def a0_06a(t, dur, W, H):
    # 片名从第一帧起就在画面里（只是亮度由 0.55 升到 1），后面一直停着，hold 由分镜的 hold 字段留出
    return _title(W, H, 0.55 + 0.45 * ease(seg(t, 0.0, 0.9)))


@shot("A0_06b")
def a0_06b(t, dur, W, H):
    s = _warp(t, dur, 1.35)
    base = _title(W, H, 1.0)                                      # 与 A0_06a 末帧逐像素一致
    c = _canvas(W, H, (0, 0, 0))
    run = ease(seg(s, 0.1, 0.85))
    fade = 1.0 - ease(seg(s, 0.8, 1.25))
    if fade > 0 and s >= 0.1:
        x0, x1 = 300, 1620
        head = x0 + (x1 - x0) * run
        n = 40
        for k in range(n):
            u0, u1 = k / n, (k + 1) / n
            xa, xb = head - 360 * u0, head - 360 * u1
            if xb < x0:
                xb = x0
            if xa <= x0:
                break
            a = (1 - u0) ** 1.5 * fade
            c.line((xa, BEAM_Y), (xb, BEAM_Y), E.CHANNEL, 6, a=a * 0.6, glow=True)
            c.line((xa, BEAM_Y), (xb, BEAM_Y), (245, 250, 255), 2, a=a)
    beam = _done(c, W, H, glow_radius=14, glow_gain=1.1)
    return ImageChops.add(base, beam)


# ---- A0_92：HUD 计数 ---------------------------------------------------------------------------------
@shot("A0_92")
def a0_92(t, dur, W, H):
    s = _warp(t, dur, 1.5)
    c = _canvas(W, H, (5, 8, 9))
    # 只出现有事实依据的两个年份（F3 的 1999、F1 的 2026）：1999 停一拍，翻牌换成 2026 后停住。
    # 不逐年滚动——中间的 2011、2021 之类会被当成年份读出来（v1 审片）。
    prog = ease(seg(s, 0.45, 0.85))
    year = 1999 if prog < 0.5 else 2026
    settled = ease(seg(s, 0.85, 1.05))
    hud = _mix(E.MEMBRANE, (5, 8, 9), 0.45)
    # 四角取景框
    x0, y0, x1, y1, L = 470, 300, 1450, 640, 46
    for (px_, py_, dx, dy) in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
        c.line((px_, py_), (px_ + dx * L, py_), hud, 3, a=0.9)
        c.line((px_, py_), (px_, py_ + dy * L), hud, 3, a=0.9)
    # 数字（等宽）
    f = mono_font(int(c.px(230)))
    col = _mix(_mix(E.LINE, E.MEMBRANE, 0.25), (255, 255, 255), 0.0)
    br = 0.72 + 0.28 * settled
    flip = 1.0 - abs(prog - 0.5) * 2                                # 0 静止，1 翻到一半：数字纵向压扁、变暗
    yy = 470 + (-36 if prog < 0.5 else 36) * flip
    dim = 1.0 - 0.85 * flip                                        # RGB 画布上 alpha 不生效，用亮度压暗
    c.d.text((c.px(960), c.px(yy)), f"{year}", font=f, fill=(*_scale(col, br * dim), 255), anchor="mm")
    c.g.text((c.px(960), c.px(yy)), f"{year}", font=f, fill=_scale(E.MEMBRANE, 0.3 * br * (1 - flip)), anchor="mm")
    # 刻度尺：28 格，游标随计数移动（只有刻度，不写数字）
    rx0, rx1, ry = 560, 1360, 590
    for k in range(28):
        x = rx0 + (rx1 - rx0) * k / 27
        major = k in (0, 27)
        c.line((x, ry), (x, ry + (22 if major else 12)), hud, 2, a=0.8 if major else 0.5)
    mx = rx0 + (rx1 - rx0) * prog                                  # 游标平滑走过刻度，不对应中间年份
    c.line((mx, ry - 14), (mx, ry - 2), E.MEMBRANE, 3, a=0.9, glow=True)
    return _done(c, W, H, glow_radius=12, glow_gain=0.9)
