"""E2 A 段（第一幕）的 2D 镜头（Pillow）：A_02b A_03a A_04a A_04b A_05b A_07b A_08b。

视觉语言同 A0 / C 段：信息图暗底 INFO_BG、HUD 暗底 HUD_BG + 膜青框线、蓝图 BP_BG + 网格 + 线稿白；
通道蓝 = 有 / 可用，琥珀 = 关掉 / 走不通，灰 = 不涉及。全部 2 倍超采样（a0._canvas / _done）。
A_04b、A_05b 分镜原写 engine: manim，本机没有 manim，按 Pillow 蓝图实现（style 仍是 blueprint）。
"""
# 屏幕字逐字照 research/visual/audit_A.yaml（与分镜 visual 一致）。下方约 18%（y > 885，1080p）是字幕安全区，不放字。
# 长镜头 A_03a / A_04a 的时间点按 storyboard.timed.yaml 的字幕时刻写（板面基准 = 当前 timed 时长），重新定时后用 _warp 缩放。
# 事实边界：F2 记录 / 损毁是建立相关的传统方法，同一行写「证明不了因果」，不写损毁证明因果；F2/F10 不画统计图、不编相关系数；
# F6/F16/F3 慢计时器没有读数（F16 没给早期方案的时间尺度），快计时器也不报数字；F16 不点名具体系统；
# F10 只用 5–30 Hz 和 1 Hz 两个档，不加别的频率或潜伏期数值；A_07b 只是「相关还是足以驱动」的提问，不讲睡眠疾病。
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "blender", "scripts"))

import e2_common as E  # noqa: E402
from mograph import ease, ease_out, seg, shot  # noqa: E402
from overlay_labels import font  # noqa: E402

from a0 import (BP_BG, BP_LINE, HUD_BG, INK, _canvas, _dashed_rect, _done, _hud_frame, _mix, _poly,  # noqa: E402
                _scale, _warp, _zoom)
from c import (BP_FAINT, BP_SUB, DIM, HUD_INK, HUD_LINE, INFO_BG, _bp_canvas, _cut_in, _dashed_box,  # noqa: E402
               _lamp, _tw)

NO_GO = E.AMBER                                         # 走不通 / 达不到（同 C 段失败路径的琥珀）


def _ring(c, xy, r, col, a, run=1.0, width=4, start=-90):
    """圈出：从 start 角顺时针画一道圆环（run 0–1），带一点发光。"""
    if a <= 0 or run <= 0:
        return
    X, Y, R_ = c.px(xy[0]), c.px(xy[1]), c.px(r)
    bb = [X - R_, Y - R_, X + R_, Y + R_]
    end = start + 360 * min(1.0, run)
    c.d.arc(bb, start, end, fill=(*col, int(255 * a)), width=max(1, int(c.px(width))))
    c.g.arc(bb, start, end, fill=_scale(col, a), width=max(1, int(c.px(width * 3))))


def _cross(c, xy, size, col, a, run=1.0, width=7):
    """打叉（两笔依次画出）。"""
    if a <= 0 or run <= 0:
        return
    x, y = xy
    h = size / 2
    c.line((x - h, y - h), (x + h, y + h), col, width, a=a, progress=min(1.0, run / 0.5), glow=True)
    if run > 0.5:
        c.line((x + h, y - h), (x - h, y + h), col, width, a=a, progress=(run - 0.5) / 0.5, glow=True)


def _arrow(c, p0, p1, col, width, a=1.0, progress=1.0, head=18, glow=False):
    """直线箭头，progress 画到哪里箭头跟到哪里。"""
    if a <= 0 or progress <= 0:
        return
    x1 = p0[0] + (p1[0] - p0[0]) * progress
    y1 = p0[1] + (p1[1] - p0[1]) * progress
    c.line(p0, (x1, y1), col, width, a=a, glow=glow)
    ang = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
    for s in (-1, 1):
        q = (x1 - head * math.cos(ang + s * 0.45), y1 - head * math.sin(ang + s * 0.45))
        c.line((x1, y1), q, col, width, a=a, glow=glow)


# ---- A_02b：两个图标「记录」「损毁」+ 同一行「证明不了因果」（信息图，1.35 s，F2） -------------------------
A02B_REC = "记录"
A02B_LES = "损毁"
A02B_FOOT = "证明不了因果"


def _rec_icon(c, cx, cy, col, a, run=1.0):
    """记录：一根电极从上方下探到一个细胞轮廓旁，右边一小段锋电位痕迹（无刻度）。只是示意。"""
    c.circle((cx - 50, cy + 40), 38, fill=_scale(col, 0.15), outline=col, width=2.5, a=a)
    c.line((cx - 120, cy - 120), (cx - 72, cy + 8), col, 4, a=a)                  # 电极杆
    c.circle((cx - 72, cy + 8), 5, fill=col, a=a, glow=True)                      # 电极尖
    x0, y0, w = cx + 10, cy - 40, 150
    pts = []
    n = 40
    for k in range(int(n * run) + 1):
        u = k / n
        y = y0
        if 0.42 < u < 0.5:
            y = y0 - 70 * (1 - abs(u - 0.46) / 0.04)                             # 一个尖峰
        elif 0.5 <= u < 0.58:
            y = y0 + 18 * math.sin((u - 0.5) / 0.08 * math.pi)                   # 回落
        pts.append((x0 + w * u, y))
    if len(pts) > 1:
        _poly(c, pts, E.MEMBRANE, 3, a, glow=True)


def _les_icon(c, cx, cy, col, a, run=1.0):
    """损毁：一块组织示意（圆角块）里挖掉一小块（虚线缺口 + 斜线阴影），只是线稿符号，不画血、不画真实组织。"""
    c.rect((cx - 120, cy - 80, cx + 120, cy + 80), fill=_scale(col, 0.12), outline=col, width=2.5, a=a, radius=36)
    gx0, gy0, gx1, gy1 = cx + 5, cy - 45, cx + 85, cy + 35                        # 被损毁的一小块
    c.rect((gx0, gy0, gx1, gy1), fill=INFO_BG, a=a * min(1.0, run * 1.5))
    _dashed_rect(c, (gx0, gy0, gx1, gy1), NO_GO, 2.5, run, a=a)
    for k in range(4):                                                            # 斜线阴影
        u = (k + 1) / 5
        c.line((gx0 + (gx1 - gx0) * u, gy0 + 6), (gx0 + (gx1 - gx0) * u - 22, gy1 - 6),
               _scale(NO_GO, 0.7), 2, a=a * ease(seg(run, 0.4 + 0.1 * k, 0.7 + 0.1 * k)))


@shot("A_02b")
def a_02b(t, dur, W, H):
    """两个图标并排（同等分量），标签在下；底下一条横线托住两个图标，线下同一行「证明不了因果」——两种方法一起读。"""
    s = _warp(t, dur, 1.35)
    c = _canvas(W, H, INFO_BG)
    a = _cut_in(s)
    run = 0.35 + 0.65 * ease_out(seg(s, 0.0, 0.7))
    col = _mix(E.LINE, E.MEMBRANE, 0.3)
    for cx, lab, icon in ((640, A02B_REC, _rec_icon), (1280, A02B_LES, _les_icon)):
        icon(c, cx, 360, col, a, run)
        c.text((cx, 540), lab, 64, INK, a, anchor="mm")
    c.line((440, 630), (1480, 630), HUD_LINE, 2, a=0.9, progress=ease_out(seg(s, 0.1, 0.55)))
    for x in (640, 1280):                                                         # 两个图标都落到同一条线上
        c.line((x, 590), (x, 630), HUD_LINE, 2, a=0.9 * ease(seg(s, 0.15, 0.45)))
    c.text((960, 715), A02B_FOOT, 76, INK, ease(seg(s, 0.25, 0.6)), anchor="mm", weight_glow=True)
    return _done(c, W, H, glow_radius=10, glow_gain=0.6)


# ---- A_03a：左栏「同时亮着」｜右栏「是它造成的吗？」（信息图，F2 / F10，没有统计图） ----------------------
A03_LEFT = "同时亮着"
A03_RIGHT = "是它造成的吗？"
A03_BASE = 13.08          # timed 时长；字幕：0.30 相关是…醒了 / 4.20 或者怕了。因果要多问一句 / 6.72 放电造成了行为 / 9.70 只是跟着一起亮


def _cells(c, cx, cy, a, lit):
    """一小簇细胞（三个圆），lit 0–1 时亮通道蓝。个数是示意。"""
    for dx, dy in ((-34, -18), (30, -26), (2, 28)):
        x, y = cx + dx, cy + dy
        c.circle((x, y), 24, fill=_mix(_scale(E.GREY, 0.25), _scale(E.CHANNEL, 0.55), lit),
                 outline=_mix(E.GREY, E.CHANNEL, lit), width=2.5, a=a)
        if lit > 0:
            c.circle((x, y), 12, fill=E.CHANNEL, a=a * lit, glow=True)


def _eye(c, cx, cy, a, open_):
    """「行为」符号：一只眼（open_ 0 闭 → 1 睁，表示醒了）。只是符号，不是论文里的行为指标。"""
    w, h = 70, 38 * open_
    col = _mix(E.GREY, E.LINE, open_)
    top = [(cx - w + 2 * w * k / 20, cy - h * math.sin(math.pi * k / 20)) for k in range(21)]
    bot = [(cx - w + 2 * w * k / 20, cy + h * math.sin(math.pi * k / 20)) for k in range(21)]
    _poly(c, top, col, 3, a)
    _poly(c, bot, col, 3, a)
    if open_ > 0.3:
        c.circle((cx, cy), 16 * open_, fill=col, a=a * ease(seg(open_, 0.3, 0.8)))


@shot("A_03a")
def a_03a(t, dur, W, H):
    """左栏：细胞簇和「行为」眼符号一起亮起、一起暗下（同一个节奏），下面「同时亮着」。右栏随「因果要多问一句」进来：
    同一对符号，中间一支从细胞指向行为的虚线箭头，箭头上一个问号，下面「是它造成的吗？」。说到「还是只是跟着一起亮」时
    问号轻轻闪。两栏都只是符号，没有坐标轴、没有点、没有相关系数。"""
    s = _warp(t, dur, A03_BASE)
    c = _canvas(W, H, INFO_BG)
    fa = _cut_in(s, 0.6, 0.4)
    panels = ((220, 200, 900, 800), (1020, 200, 1700, 800))
    # 左栏
    la = fa
    c.rect(panels[0], fill=_scale(E.MEMBRANE, 0.04), outline=HUD_LINE, width=2.5, a=la, radius=12)
    pulse = 0.5 + 0.5 * math.sin(2 * math.pi * (s - 0.6) / 2.4)                 # 同一节奏
    lit = ease(seg(s, 0.6, 1.4)) * (0.35 + 0.65 * pulse)
    _cells(c, 420, 440, la, lit)
    _eye(c, 700, 440, la, 0.15 + 0.85 * lit)
    c.line((470, 440), (620, 440), _scale(HUD_LINE, 0.8), 2, a=0.5 * la)       # 并排（不是箭头）
    c.text((560, 680), A03_LEFT, 72, INK, ease(seg(s, 0.8, 1.4)), anchor="mm")
    # 右栏
    ra = ease(seg(s, 4.6, 5.3))
    c.rect(panels[1], fill=_scale(E.MEMBRANE, 0.04), outline=HUD_LINE, width=2.5, a=ra, radius=12)
    _cells(c, 1180, 440, ra, lit)
    _eye(c, 1540, 440, ra, 0.15 + 0.85 * lit)
    arun = ease_out(seg(s, 6.9, 7.9))                                             # 「放电造成了行为」：箭头画出
    if arun > 0:
        _dashed_rect(c, (1235, 440, 1235 + 220 * arun, 440), E.CHANNEL, 3, 0.5, a=ra)
        tip = (1235 + 220 * arun, 440)
        for sgn in (-1, 1):
            c.line(tip, (tip[0] - 18, tip[1] + sgn * 12), E.CHANNEL, 3, a=ra * ease(seg(arun, 0.8, 1.0)))
    qa = ease(seg(s, 5.0, 5.6))
    blink = 1.0 - 0.45 * max(0.0, math.sin(2 * math.pi * (s - 9.9) / 1.2)) * ease(seg(s, 9.8, 10.2))
    c.text((1345, 340), "？", 96, E.AMBER, qa * blink, anchor="mm", weight_glow=True)
    c.text((1360, 680), A03_RIGHT, 72, INK, ease(seg(s, 5.1, 5.7)), anchor="mm")
    return _done(c, W, H, glow_radius=12, glow_gain=0.7)


# ---- A_04a：HUD 两个计时器「毫秒」｜「分钟」，只圈毫秒为可用（HUD，F6 / F16 / F3） ------------------------
A04_FAST = "毫秒"
A04_SLOW = "分钟"
FPS_JUMP = 24                                           # 毫秒盘每秒跳的格数（按真实时间）
A04_BASE = 8.51           # timed 时长；字幕：0.30 只推动那一类细胞 / 3.30 也能按住…锋电位 / 6.71 是毫秒，不是分钟


def _dial(c, cx, cy, r, col, a, angle, ticks=60):
    """无数字的计时盘：外圈 + 刻度 + 一根指针（angle 度，0 = 12 点方向，顺时针）。不出现读数。"""
    c.circle((cx, cy), r, fill=_scale(E.MEMBRANE, 0.05), outline=col, width=3, a=a)
    for k in range(ticks):
        th = 2 * math.pi * k / ticks
        L = 22 if k % 5 == 0 else 11
        p = (cx + (r - 8) * math.sin(th), cy - (r - 8) * math.cos(th))
        q = (cx + (r - 8 - L) * math.sin(th), cy - (r - 8 - L) * math.cos(th))
        c.line(p, q, col, 2.5 if k % 5 == 0 else 1.5, a=a * (0.9 if k % 5 == 0 else 0.55))
    th = math.radians(angle)
    c.line((cx, cy), (cx + (r - 40) * math.sin(th), cy - (r - 40) * math.cos(th)), E.LINE, 4, a=a, glow=True)
    c.circle((cx, cy), 9, fill=E.LINE, a=a)


@shot("A_04a")
def a_04a(t, dur, W, H):
    """HUD 框里两个无数字计时盘。左「毫秒」：指针一跳一跳飞快地走（每帧跳一格多）；右「分钟」：指针几乎不动、慢慢爬。
    旁白说到「是毫秒，不是分钟」时，毫秒盘被通道蓝圆环圈出、状态灯亮；分钟盘压暗、空心灯（不可用）。慢推镜。"""
    s = _warp(t, dur, A04_BASE)
    c = _canvas(W, H, HUD_BG)
    fa = _cut_in(s, 0.6, 0.4)
    box = (300, 170, 1620, 820)
    _hud_frame(c, box, HUD_LINE, a=0.9 * fa)
    c.line((960, box[1] + 60), (960, box[3] - 60), HUD_LINE, 2, a=0.45 * fa)
    pick = ease(seg(s, 6.8, 7.4))                                                 # 「是毫秒，不是分钟」
    fast_x, slow_x, dy = 630, 1290, 450
    da = fa
    step = int(t * FPS_JUMP)                                                       # 跳格：按真实帧走，不跟 _warp 拉伸
    _dial(c, fast_x, dy, 190, HUD_LINE, da, (step * 37) % 360)
    slow_col = _mix(HUD_LINE, E.GREY, 0.5 * pick)
    _dial(c, slow_x, dy, 190, slow_col, da * (1.0 - 0.45 * pick), 6 + 10 * s / A04_BASE)
    c.text((fast_x, 715), A04_FAST, 60, HUD_INK, fa, anchor="mm")
    c.text((slow_x, 715), A04_SLOW, 60, _mix(HUD_INK, E.GREY, 0.45 * pick), fa * (1 - 0.4 * pick),
           anchor="mm")
    _ring(c, (fast_x, dy), 225, E.CHANNEL, pick, run=ease_out(seg(s, 6.8, 7.6)))
    _lamp(c, (fast_x - 115, 715), True, pick)
    _lamp(c, (slow_x - 115, 715), False, pick)
    img = _done(c, W, H, glow_radius=12, glow_gain=0.8)
    return _zoom(img, 1.0 + 0.04 * ease(seg(s, 0.0, A04_BASE)))



# ---- A_04b：蓝图标题「只动一类、可开可关、毫秒」（蓝图，F3 / F6，1.35 s） ---------------------------------
A04B_TITLE = ("只动一类、", "可开可关、", "毫秒")


@shot("A_04b")
def a_04b(t, dur, W, H):
    """蓝图图框 + 标题栏：一行三段（三个设计要求），每段下面一道尺寸线式的短横线依次画出。只是规格标题，不标年份、不写人名。"""
    s = _warp(t, dur, 1.35)
    a = _cut_in(s)
    c = _bp_canvas(W, H, a)
    c.rect((60, 60, 1860, 860), outline=BP_LINE, width=2, a=0.45 * a)
    box = (330, 330, 1590, 640)
    c.rect(box, fill=_mix(BP_BG, BP_LINE, 0.05), outline=BP_LINE, width=2.5, a=a, radius=6)
    c.line((box[0], box[3] - 70), (box[2], box[3] - 70), BP_SUB, 2, a=a)
    for i in range(3):                                                            # 标题栏底部三格（无字示意）
        x = box[0] + (box[2] - box[0]) * (i + 1) / 3
        if i < 2:
            c.line((x, box[3] - 70), (x, box[3]), BP_SUB, 2, a=a)
        c.rect((box[0] + (box[2] - box[0]) * i / 3 + 40, box[3] - 42, box[0] + (box[2] - box[0]) * i / 3 + 220,
                box[3] - 28), fill=BP_FAINT, a=0.5 * a, radius=7)
    size = 84
    f = font(int(c.px(size)))
    ws = [_tw(c, p, f) for p in A04B_TITLE]
    x = 960 - sum(ws) / 2
    y = 455
    for i, (p, w) in enumerate(zip(A04B_TITLE, ws)):
        pa = a if i == 0 else ease(seg(s, 0.08 * i, 0.08 * i + 0.3)) * a
        c.text((x, y), p, size, BP_LINE, pa, anchor="lm", weight_glow=True)
        core = w - (_tw(c, "、", f) if p.endswith("、") else 0)
        run = ease_out(seg(s, 0.1 + 0.15 * i, 0.5 + 0.15 * i))
        c.line((x, y + 62), (x + core, y + 62), BP_LINE, 2, a=pa, progress=run)
        for xx in (x, x + core):                                                  # 尺寸线两端的小竖线
            c.line((xx, y + 50), (xx, y + 74), BP_LINE, 2, a=pa * run)
        x += w
    return _done(c, W, H, glow_radius=8, glow_gain=0.6)


# ---- A_05b：多步箭头末端打叉 +「达不到毫秒」（蓝图，F16，1.35 s） -----------------------------------------
A05B_NOT = "达不到毫秒"


@shot("A_05b")
def a_05b(t, dur, W, H):
    """蓝图上四个抽象方块（同 A_05a 的多步接力，不对应任何具体系统、不写名字）用箭头串起，最后一支箭头指向终点虚线框，
    框上一枚琥珀叉，旁边琥珀小字「达不到毫秒」。不庆祝、不红色。"""
    s = _warp(t, dur, 1.35)
    a = _cut_in(s)
    c = _bp_canvas(W, H, a)
    c.rect((60, 60, 1860, 860), outline=BP_LINE, width=2, a=0.45 * a)
    y = 420
    xs = (390, 650, 910, 1170)                                                     # 整条链居中
    for i, x in enumerate(xs):
        c.rect((x - 70, y - 60, x + 70, y + 60), fill=_mix(BP_BG, BP_LINE, 0.06), outline=BP_LINE, width=2.5,
               a=a, radius=10)
        c.rect((x - 40, y - 8, x + 40, y + 8), fill=BP_FAINT, a=0.5 * a, radius=8)
        if i < len(xs) - 1:
            _arrow(c, (x + 80, y), (xs[i + 1] - 80, y), BP_LINE, 3, a=a)
    run = 0.4 + 0.6 * ease_out(seg(s, 0.0, 0.45))                                 # 最后一支箭头接着画出
    _arrow(c, (xs[-1] + 80, y), (1430, y), BP_LINE, 3, a=a, progress=run)
    end_box = (1450, y - 70, 1590, y + 70)
    _dashed_box(c, end_box, BP_SUB, a, progress=ease_out(seg(s, 0.0, 0.5)))
    _cross(c, (1520, y), 110, NO_GO, 1.0, run=ease_out(seg(s, 0.4, 0.75)))
    c.text((1520, y + 150), A05B_NOT, 64, NO_GO, ease(seg(s, 0.55, 0.85)), anchor="mm", weight_glow=True)
    return _done(c, W, H, glow_radius=8, glow_gain=0.6)


# ---- A_07b：左「和清醒有关」｜右「放电够不够」，右列被圈出（信息图，F10，1.35 s） --------------------------
A07B_LEFT = "和清醒有关"
A07B_RIGHT = "放电够不够"


@shot("A_07b")
def a_07b(t, dur, W, H):
    """左右两列同字号，中间一条细分隔线；左列压暗（只是相关），右列被通道蓝圆角框圈出（论文要问的是这个）。"""
    s = _warp(t, dur, 1.35)
    c = _canvas(W, H, INFO_BG)
    a = _cut_in(s)
    pick = ease(seg(s, 0.2, 0.6))
    c.text((560, 470), A07B_LEFT, 84, _mix(INK, DIM, pick), a, anchor="mm")
    c.text((1360, 470), A07B_RIGHT, 84, INK, a, anchor="mm", weight_glow=True)
    c.line((960, 340), (960, 600), HUD_LINE, 2, a=0.8 * a)
    f = font(int(c.px(84)))
    w = _tw(c, A07B_RIGHT, f)
    box = (1360 - w / 2 - 60, 470 - 100, 1360 + w / 2 + 60, 470 + 100)
    run = ease_out(seg(s, 0.15, 0.75))
    if run > 0:
        x0, y0, x1, y1 = box
        top = (x1 - x0) * run                                                     # 上下两边从中间向两侧展开，竖边随后
        cx = (x0 + x1) / 2
        c.line((cx - top / 2, y0), (cx + top / 2, y0), E.CHANNEL, 4, a=1.0, glow=True)
        c.line((cx - top / 2, y1), (cx + top / 2, y1), E.CHANNEL, 4, a=1.0, glow=True)
        side = ease(seg(run, 0.75, 1.0))
        if side > 0:
            c.rect(box, outline=E.CHANNEL, width=4, a=side, radius=18)
    return _done(c, W, H, glow_radius=10, glow_gain=0.7)


# ---- A_08b：HUD「5–30 Hz 潜伏期缩短」「1 Hz 不缩短」（HUD，F10，1.35 s） ---------------------------------
A08B_ROWS = (("5–30 Hz 潜伏期缩短", True), ("1 Hz 不缩短", False))       # 只用论文里这两个档


@shot("A_08b")
def a_08b(t, dur, W, H):
    """HUD 框 + 两行状态读数：第一行实心通道蓝灯（有缩短），第二行空心环加横杠、字压灰（没有缩短）。只有这两行，没有别的数。"""
    s = _warp(t, dur, 1.35)
    c = _canvas(W, H, HUD_BG)
    fa = _cut_in(s)
    box = (380, 270, 1540, 750)
    _hud_frame(c, box, HUD_LINE, a=0.9 * fa)
    c.line((box[0] + 40, 510), (box[2] - 40, 510), HUD_LINE, 2, a=0.5 * fa, progress=ease_out(seg(s, 0.0, 0.5)))
    for i, (y, (text, on)) in enumerate(zip((400, 620), A08B_ROWS)):
        a = fa if i == 0 else ease(seg(s, 0.2, 0.5))
        _lamp(c, (500, y), on, a)
        c.text((570, y), text, 68, HUD_INK if on else _mix(HUD_INK, E.GREY, 0.35), a, anchor="lm")
    return _done(c, W, H, glow_radius=12, glow_gain=0.8)
