"""E2 D 段（尾声）的 2D 镜头（Pillow）：D_02a D_02b D_03b D_04a D_91。

视觉语言同 A0 / A / C 段：排版纯黑 TYPE_BG + 宋体、信息图暗底 INFO_BG。通道蓝 = 有，琥珀 = 关掉，灰 = 不涉及。
全部 2 倍超采样（a0._canvas / _done）。
"""
# 屏幕字逐字照 research/visual/audit_D.yaml。下方约 18%（y > 885，1080p）是字幕安全区，不放字。
# 长镜头 D_02a / D_04a 的时间点按 storyboard.timed.yaml 的字幕时刻写（板面基准 = 当前 timed 时长），重新定时后用 _warp 缩放。
# 事实边界：F9 对象是小鼠，屏幕不写改写人类记忆；D_02b 右格锁定「人体记忆：本研究不涉及」（P6，同 C_06a 口径），
# 不写成全称否定；F11 部分视觉、离不开装置，「失明结束」只以「不等于 / 不是」的否定形式出现，不说治愈；
# F3 D_03b「相当牵强」不配年份、不写年份差；D_04a 片名同片头 A0_06a，下面没有下一期题目，也不上「审查中」三个字。
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "blender", "scripts"))

import e2_common as E  # noqa: E402
from mograph import ease, seg, shot  # noqa: E402
from overlay_labels import font, serif_font  # noqa: E402

from a0 import INK, _canvas, _done, _mix, _scale, _stext, _title, _warp  # noqa: E402
from c import DIM, HUD_LINE, INFO_BG, TYPE_BG, _cut_in, _lamp, _tw  # noqa: E402

OFF = E.AMBER


def _seg_line(c, cx, y, parts, size, a, fnt=serif_font, glow=0.2):
    """一行由几段拼成（每段自己的颜色），整行以 cx 居中。parts = [(文字, 颜色), ...]。"""
    f = fnt(int(c.px(size)))
    ws = [_tw(c, p, f) for p, _ in parts]
    x = cx - sum(ws) / 2
    for (p, col), w in zip(parts, ws):
        c.text_font((x, y), p, f, col, a, "lm", glow)
        x += w


# ---- D_02a：两行被放下的句子（排版，F9 / F11） ------------------------------------------------------------
D02_LINES = (("小鼠实验", "不等于", "某一个人的人生"), ("部分视觉报告", "不等于", "失明结束"))
D02_BASE = 13.11          # 字幕：0.30 小鼠海马里的一段恐惧 / 3.78 改写了某一个人的人生 / 6.83 也做不到把一次离不开 / 9.01 部分视觉报告 / 10.97 失明已经结束


@shot("D_02a")
def d_02a(t, dur, W, H):
    """两行句子，各自随旁白进来；每行说完后「放下」：往下沉一点、压暗成灰，但一直留在画面里（不划掉）。
    「不等于」用琥珀。第一行在第二行进来前放下，第二行在镜头末尾放下。"""
    s = _warp(t, dur, D02_BASE)
    c = _canvas(W, H, TYPE_BG)
    for i, (y, at, down) in enumerate(((400, 0.4, 6.3), (600, 6.9, 11.9))):
        a = ease(seg(s, at, at + 0.7))
        if a <= 0:
            continue
        d = ease(seg(s, down, down + 0.8))
        ink = _mix(INK, DIM, d)
        neg = _mix(OFF, _scale(OFF, 0.6), d)
        l, m, r = D02_LINES[i]
        _seg_line(c, 960, y + 22 * d, ((l, ink), (m, neg), (r, ink)), 76, a * (1 - 0.25 * d), glow=0.2 * (1 - d))
    return _done(c, W, H, glow_radius=10)


# ---- D_02b：左格「小鼠恐惧实验」｜右格「人体记忆：本研究不涉及」（信息图，1.35 s，F9） -------------------------
D02B_LEFT = "小鼠恐惧实验"
D02B_RIGHT = "人体记忆：本研究不涉及"          # P6 锁定措辞（同 C_06a），不写「无对应结果」


@shot("D_02b")
def d_02b(t, dur, W, H):
    """两格同大小：左格实心通道蓝灯（这项研究做的是这个），右格空心灰灯 + 灰字（不涉及，不是否定全世界）。"""
    s = _warp(t, dur, 1.35)
    c = _canvas(W, H, INFO_BG)
    a = _cut_in(s)
    ra = ease(seg(s, 0.1, 0.4))
    cells = ((140, 330, 920, 610), (1000, 330, 1780, 610))
    for k, (box, txt, on, ca) in enumerate(((cells[0], D02B_LEFT, True, a), (cells[1], D02B_RIGHT, False, ra))):
        c.rect(box, fill=_scale(E.MEMBRANE, 0.04), outline=HUD_LINE, width=2.5, a=ca, radius=12)
        f = font(int(c.px(50)))
        w = _tw(c, txt, f)
        cx = (box[0] + box[2]) / 2 + 30
        _lamp(c, (cx - w / 2 - 60, 470), on, ca)
        c.text((cx, 470), txt, 50, INK if on else _mix(INK, E.GREY, 0.35), ca, anchor="mm")
    return _done(c, W, H, glow_radius=10, glow_gain=0.6)


# ---- D_03b：「相当牵强」再次出现，字号更大（排版，1.35 s，F3） ---------------------------------------------
D03B_WORD = "相当牵强"                       # 同 A0_02a 的宋体；A0_02a 里是 78 px，这里放大


@shot("D_03b")
def d_03b(t, dur, W, H):
    s = _warp(t, dur, 1.35)
    c = _canvas(W, H, TYPE_BG)
    _stext(c, (960, 470), D03B_WORD, 170, INK, _cut_in(s), anchor="mm", glow=0.25)
    return _done(c, W, H, glow_radius=12)


# ---- D_04a：片名《光遗传学》停住，下面没有下一期题目（排版，F7） ---------------------------------------------
@shot("D_04a")
def d_04a(t, dur, W, H):
    """与片头 A0_06a 同一张片名（a0._title，逐像素同款）：亮度从 0.55 升满后一直停着。片名下面不放任何字。"""
    return _title(W, H, 0.55 + 0.45 * ease(seg(t, 0.0, 0.9)))


# ---- D_91：左列「打开或关掉选定细胞」｜右列「不是某人的人生，也不是失明结束」（信息图，1.5 s，F2 / F8 / F9 / F11） --
D91_LEFT = ("打开或关掉", "选定细胞")
D91_RIGHT = ("不是某人的人生，", "也不是失明结束")


@shot("D_91")
def d_91(t, dur, W, H):
    """两列，中间细分隔线。左列（这套方法做的事）旁一亮一琥珀两枚灯；右列（不是的事）灰字、空心灯。"""
    s = _warp(t, dur, 1.5)
    c = _canvas(W, H, INFO_BG)
    a = _cut_in(s)
    ra = ease(seg(s, 0.15, 0.5))
    c.line((960, 300), (960, 660), HUD_LINE, 2, a=0.8 * a)
    _lamp(c, (300, 420), True, a)
    _lamp(c, (300, 540), True, a, col=OFF)
    for i, line in enumerate(D91_LEFT):
        c.text((580, 420 + 120 * i), line, 72, INK, a, anchor="mm")
    _lamp(c, (1080, 480), False, ra)
    for i, line in enumerate(D91_RIGHT):
        c.text((1430, 420 + 120 * i), line, 64, _mix(INK, E.GREY, 0.35), ra, anchor="mm")
    return _done(c, W, H, glow_radius=10, glow_gain=0.6)
