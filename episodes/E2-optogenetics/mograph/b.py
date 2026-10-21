"""E2 B 段（第二幕）：Blender raw 帧的叠字后处理（Pillow），以及文件后半的 B 段全部 2D 镜头
（B_08b B_09a B_10b B_11a B_11b B_12a B_12b B_13b B_15a B_17a B_18b B_19a B_19b B_20a B_20b，见「B 段 2D 镜头」一节）。

叠字后处理：

每镜：Blender 帧（<quality>_raw）+ 中文标签，写到 <quality>/。字和锚点照 b_scenes.py 文件头；锚点、相机在这里照抄
b_scenes 里的数（改场景时两边一起改），按 e2_common.project_point 投影。时间用镜头比例 u = (f-1)/(n-1)，
和场景里的关键帧同一套；标签出现的时刻对着 timed 字幕（retime 之后再对一次）。
标签纵向限制在 0.10H–0.79H：上面不出画，下面约 18% 是字幕安全区。
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "blender", "scripts"))

from PIL import Image  # noqa: E402

import build_purple_membrane as BP  # noqa: E402
import e2_common as E  # noqa: E402
import raw_overlay as R  # noqa: E402
from mograph import ease, seg, shot  # noqa: E402

U = 0.01                                               # 1 Å = 0.01 BU（build_bilayer.UNIT）


def _y(y, H):
    return min(0.79 * H, max(0.10 * H, y))


def _base(sid, t, dur, W, H):
    f, n, u = R.frame_of(t, dur)
    return R.raw_frame(sid, f, W).resize((W, H), Image.LANCZOS), f, n, u


# ---- B_02a：紫膜晶格 +「膜片段里只有这一种蛋白」 ------------------------------------------------------
def _b02_hero():
    """b_scenes.br_lattice 的主角单体（离原点最近的单体，Å）：照抄那里的晶格和挑选规则。"""
    tri_r = 17.0                                       # b_scenes.TRI_R
    hero = None
    for cx, cy in BP.lattice_points(90.0, 70.0):
        if abs(cx) > 110 or abs(cy) > 90:
            continue
        for k in range(3):
            th = math.radians(90 + 120 * k)
            m = (cx + tri_r * math.cos(th), cy + tri_r * math.sin(th))
            if hero is None or math.hypot(*m) < math.hypot(*hero):
                hero = m
    return (hero[0] * U, hero[1] * U, 0.0)


B02_TEXT = "膜片段里只有这一种蛋白"


@shot("B_02a")
def b_02a(t, dur, W, H):
    """镜头推到主角单体正上方时，镜头已近乎俯视，锚点 LabelAnchor_onlyone（单体上方 0.42）投影出画。
    这句话说的是整片膜，不指某一个单体：字放在左上的晶格间隙一带（不画引线），x 跟着主角单体的投影左移。
    字幕「这个膜片段里，蛋白只有这一种」在 13.0 s / 16.0 s（u≈0.81）：字在 0.70→0.80 淡入，停到结尾。"""
    base, f, n, u = _base("B_02a", t, dur, W, H)
    a = ease(seg(u, 0.70, 0.80))
    if a <= 0:
        return base
    k = H / 1080
    hc = _b02_hero()
    loc, aim = R.dolly(f, n, (0.0, 0.0, 0.0), (0.0, -1.7, 2.6), (hc[0], hc[1] - 0.40, 0.95), hc)
    hx, _ = E.project_point(hc, loc, aim, W, H)
    return R.tag(base, B02_TEXT, (hx - 0.42 * W, 0.12 * H), k, a=a, anchor="lm", size=42)


# ---- B_03a：bR 剖面 +「细菌视紫红质 · 质子泵」 ------------------------------------------------------
B03_TEXT = "细菌视紫红质 · 质子泵"
B03_ANCHOR = (0.0, 0.0, 0.36)                          # b_scenes.br_pump：LabelAnchor_bR（蛋白顶上方）


@shot("B_03a")
def b_03a(t, dur, W, H):
    """第一次闪光在 u=0.30（b_scenes：cycles = F3 × 0.30 / 0.55 / 0.78），字幕「细菌视紫红质」在 5.3 s（u≈0.31）。
    字在 0.31→0.38 淡入，放在锚点上方（字底贴锚点），边线取膜青（质子的颜色）。"""
    base, f, n, u = _base("B_03a", t, dur, W, H)
    a = ease(seg(u, 0.31, 0.38))
    if a <= 0:
        return base
    k = H / 1080
    loc, aim = R.dolly(f, n, (0.0, 0.0, 0.05), (0.35, -3.0, 0.55), (0.15, -2.15, 0.32))
    x, y = E.project_point(B03_ANCHOR, loc, aim, W, H)
    return R.tag(base, B03_TEXT, (x, _y(y - 40 * k, H)), k, a=a, edge=E.MEMBRANE)


# ---- B_04a：泵 / 通道（blueprint） ---------------------------------------------------------------
B04_PUMP = (-0.78, 0.0, 0.66)                          # b_scenes.pump_channel：LabelAnchor_pump
B04_CHANNEL = (0.78, 0.0, 0.66)                        # LabelAnchor_channel


@shot("B_04a")
def b_04a(t, dur, W, H):
    """「泵」在泵箭头出现时（场景 u=0.22；字幕「泵把离子……」2.3 s，u≈0.19）淡入：0.19→0.26。
    「通道」对着旁白「通道是一个孔」（约 4.7 s，u≈0.38）淡入：0.38→0.45，比孔打开（u=0.55）早一点。两个都停到结尾。"""
    base, f, n, u = _base("B_04a", t, dur, W, H)
    k = H / 1080
    loc, aim = R.dolly(f, n, (0.0, 0.0, 0.0), (0.0, -4.9, 0.5), (0.0, -4.3, 0.42))
    for text, p, (u0, u1) in (("泵", B04_PUMP, (0.19, 0.26)), ("通道", B04_CHANNEL, (0.38, 0.45))):
        a = ease(seg(u, u0, u1))
        if a > 0:
            x, y = E.project_point(p, loc, aim, W, H)
            base = R.tag(base, text, (x, _y(y, H)), k, pal=R.BLUEPRINT, a=a, size=50)
    return base


# ---- B_16b：NpHR 蓝图，三个标签 -----------------------------------------------------------------
B16_CAM = ((0.15, -3.0, 0.35), (0.15, 0.0, 0.2))       # CamB_16b：locked，lens 35
B16_LABELS = (                                         # (字, 锚点, 对齐, 淡入 u0→u1)
    ("黄光", (-0.45, 0.0, 0.92), "rm", (0.00, 0.20)),          # LabelAnchor_light：波浪线左侧
    ("氯离子向内", (0.10, -0.32, -0.33), "lm", (0.12, 0.32)),  # LabelAnchor_cl：氯离子箭头右侧、膜下方
    ("电压下降", (1.25, -0.05, 0.47), "mb", (0.24, 0.44)),     # LabelAnchor_v：右侧下降箭头上方
)


@shot("B_16b")
def b_16b(t, dur, W, H):
    """1.35 s 的纯画面镜头（无旁白）：三个标签按光 → 氯离子 → 电压的顺序错开约 0.15 s 进来，后半段全部停住。"""
    base, f, n, u = _base("B_16b", t, dur, W, H)
    k = H / 1080
    loc, aim = B16_CAM
    for text, p, anchor, (u0, u1) in B16_LABELS:
        a = ease(seg(u, u0, u1))
        if a > 0:
            x, y = E.project_point(p, loc, aim, W, H, focal=35)
            base = R.tag(base, text, (x, _y(y, H)), k, pal=R.BLUEPRINT, a=a, anchor=anchor, size=42)
    return base


# ---- B_18a：ChrimsonR 下方「2021 用于人眼」 --------------------------------------------------------
B18_TEXT = "2021 用于人眼"
B18_ANCHOR = (0.45, -0.05, 0.34)                       # b_scenes.spectrum：LabelAnchor_human（ChrimsonR 字下方）


@shot("B_18a")
def b_18a(t, dur, W, H):
    """字幕「2021 年用在人眼上的」在 3.7 s（u≈0.30）：字在 0.30→0.38 淡入，挂在 ChrimsonR（Blender 字）正下方，
    边线取暖灰（右边长波长蛋白的色调），只标年份和用途（F11），不写疗效。"""
    base, f, n, u = _base("B_18a", t, dur, W, H)
    a = ease(seg(u, 0.30, 0.38))
    if a <= 0:
        return base
    k = H / 1080
    loc, aim = R.dolly(f, n, (0.0, 0.0, 0.08), (0.0, -2.9, 0.75), (0.05, -2.3, 0.6))
    x, y = E.project_point(B18_ANCHOR, loc, aim, W, H)
    return R.tag(base, B18_TEXT, (x, _y(y, H)), k, a=a, anchor="mt", size=40, edge=(214, 168, 150))


# ================================================================================================
# B 段 2D 镜头（Pillow）：B_08b B_09a B_10b B_11a B_11b B_12a B_12b B_13b B_15a B_17a B_18b B_19a B_19b B_20a B_20b。
# 视觉语言同 A / C 段：信息图 INFO_BG、HUD HUD_BG + 膜青框线、排版纯黑 TYPE_BG + 宋体、蓝图 BP_BG + 网格。
# 通道蓝 = 打开 / 有，琥珀 = 关掉 / 不在名单里，灰 = 空着。全部 2 倍超采样（a0._canvas / _done）。
# B_20a 分镜原写 engine: manim，本机没有 manim，按 Pillow 蓝图实现（style 仍是 blueprint）。
# 屏幕字逐字照 research/visual/audit_B.yaml。下方约 18%（y > 885，1080p）是字幕安全区，不放字。
# 长镜头的时间点按 storyboard.timed.yaml 的字幕时刻写（板面基准 = 当前 timed 时长），重新定时后用 _warp 缩放。
# 事实边界：F5 脱敏曲线只是形状，不标时间常数、不标平台比例、坐标轴没有数字；F6 脉冲列不画频率上限、不写 Hz；
# F6/F1 署名和新闻稿两列都保留，不合并；F1 2026 得主只有三行，第四行空着；F7 optogenetics + 2006；
# F6/F8/F1 时间轴只有 2005、2007 两点，中间不填月份；F8 两条色带不标纳米数；F17 箭头读作「敏感波长往长推」，
# 不画谱系、不标纳米；F14 Brain Prize 六个姓名，没有肖像；F14/F1 两份名单不并成一份。
# ================================================================================================
from mograph import ease_out  # noqa: E402
from overlay_labels import font, mono_font, serif_font  # noqa: E402

from a0 import (BP_BG, BP_LINE, HUD_BG, INK, _canvas, _dashed_rect, _done, _hud_frame, _mix, _poly,  # noqa: E402
                _scale, _stext, _warp, _zoom)
from c import (BP_SUB, DIM, HUD_INK, HUD_LINE, INFO_BG, TYPE_BG, _bp_canvas, _cut_in, _dashed_box,  # noqa: E402
               _tw)
from a import _arrow  # noqa: E402

OFF = E.AMBER                                           # 关掉 / 不在名单里
EMPTY = _scale(E.GREY, 0.55)                            # 空着的那一行
RED_SHIFT = (255, 128, 92)                              # 长波长一侧的暖色（同 B_18a 右边的暖调，不是刻度）


def _empty_row(c, x0, x1, y, a, run=1.0):
    """空着的一行：一道虚线底线，上面什么也不写（排版，表示这里不填人名）。"""
    if a <= 0 or run <= 0:
        return
    _dashed_rect(c, (x0, y, x0 + (x1 - x0) * run, y), EMPTY, 2.5, 0.5, a=a, dash=16, gap=14)


def _chip(c, xy, text, size, col, a, fill_k=0.10, pad=(34, 18), fnt=None, txt_col=None):
    """圆角名签（没有肖像）：框 + 一行字，xy 是中心。返回框。"""
    if a <= 0:
        return None
    f = (fnt or font)(int(c.px(size)))
    w = _tw(c, text, f)
    box = (xy[0] - w / 2 - pad[0], xy[1] - size / 2 - pad[1], xy[0] + w / 2 + pad[0], xy[1] + size / 2 + pad[1])
    c.rect(box, fill=_scale(col, fill_k), outline=col, width=2.5, a=a, radius=14)
    c.text_font(xy, text, f, txt_col or INK, a, "mm")
    return box


# ---- B_08b：HUD 电压计上跳，标注「阳离子」「蓝光」「ChR2」（HUD，1.35 s，F5 / F1） -----------------------
B08_LABELS = ("蓝光", "ChR2", "阳离子")


@shot("B_08b")
def b_08b(t, dur, W, H):
    """HUD 框：左边三行标签（蓝光照到 ChR2，阳离子进来），右边一根无刻度数字的竖向电压条，从低位一下跳高。
    只有方向，没有毫伏读数。"""
    s = _warp(t, dur, 1.35)
    c = _canvas(W, H, HUD_BG)
    fa = _cut_in(s)
    box = (330, 220, 1590, 800)
    _hud_frame(c, box, HUD_LINE, a=0.9 * fa)
    cols = (E.CHANNEL, E.CHANNEL, E.MEMBRANE)
    for i, (lab, col) in enumerate(zip(B08_LABELS, cols)):
        y = 360 + 150 * i
        a = fa if i == 0 else ease(seg(s, 0.08 * i, 0.08 * i + 0.3))
        c.circle((450, y), 15, fill=col, a=a, glow=True)
        c.text((500, y), lab, 66, HUD_INK, a, anchor="lm")
    # 电压条：外框 + 刻度（无数字），水位从 0.18 跳到 0.86
    bx0, by0, bx1, by1 = 1180, 290, 1290, 730
    c.rect((bx0, by0, bx1, by1), outline=HUD_LINE, width=3, a=fa, radius=6)
    for k in range(1, 10):
        y = by1 - (by1 - by0) * k / 10
        c.line((bx1 + 8, y), (bx1 + (30 if k % 5 == 0 else 18), y), HUD_LINE, 2, a=0.6 * fa)
    lv = 0.18 + 0.68 * ease_out(seg(s, 0.2, 0.55))
    top = by1 - (by1 - by0) * lv
    c.rect((bx0 + 10, top, bx1 - 10, by1 - 10), fill=_mix(E.CHANNEL, HUD_BG, 0.25), a=fa, radius=4, glow=True)
    _arrow(c, (1420, 640), (1420, 360), E.CHANNEL, 5, a=ease(seg(s, 0.3, 0.6)), progress=ease_out(seg(s, 0.3, 0.7)),
           head=26, glow=True)
    return _done(c, W, H, glow_radius=12, glow_gain=0.8)


# ---- B_09a：电流示意曲线 尖峰 → 较低平台 +「持续光照会脱敏」（信息图，F5） --------------------------------
B09_LABEL = "持续光照会脱敏"
B09_AX_Y, B09_AX_X = "电流", "时间"
B09_BASE = 12.03          # timed 时长；字幕：0.30 持续照着的时候 / 1.74 这道电流… / 3.80 高峰落到…平台 / 6.07 通道会脱敏… / 9.78 疲劳的门


def _b09_curve(u):
    """示意形状（simplified，F5 没给时间常数）：光开之前在 0，开灯后很快冲到峰，再落到一个更低的平台。"""
    on = 0.16
    if u < on:
        return 0.0
    v = u - on
    rise = 1 - math.exp(-v / 0.012)
    return rise * (0.48 + 0.52 * math.exp(-v / 0.09))


@shot("B_09a")
def b_09a(t, dur, W, H):
    """坐标系只有两根带箭头的轴和「电流」「时间」两个轴名，没有刻度数字。上方一条通道蓝的光照条随「持续照着」
    铺开（一直亮着）；曲线随「这道电流」画出，在「高峰」处冲顶，再落到较低平台；「通道会脱敏」时平台段高亮，
    下面出现「持续光照会脱敏」。"""
    s = _warp(t, dur, B09_BASE)
    c = _canvas(W, H, INFO_BG)
    fa = _cut_in(s, 0.6, 0.4)
    x0, y0, x1, y1 = 360, 760, 1600, 300                                          # 原点在左下
    _arrow(c, (x0, y0), (x1 + 30, y0), HUD_LINE, 3, a=fa, head=18)
    _arrow(c, (x0, y0), (x0, y1 - 60), HUD_LINE, 3, a=fa, head=18)
    c.text((x0 - 30, y1 - 60), B09_AX_Y, 44, DIM, fa, anchor="rm")
    c.text((x1 + 30, y0 + 50), B09_AX_X, 44, DIM, fa, anchor="rm")
    on_u = 0.16
    lx0 = x0 + (x1 - x0) * on_u
    lrun = ease_out(seg(s, 0.4, 1.6))
    if lrun > 0:                                                                   # 光照条：开灯后一直亮着
        c.rect((lx0, y1 - 70, lx0 + (x1 - lx0) * lrun, y1 - 46), fill=_scale(E.CHANNEL, 0.75), a=fa, radius=6,
               glow=True)
    run = ease(seg(s, 1.8, 6.0))
    n = 160
    pts = []
    for k in range(int(n * run) + 1):
        u = k / n
        pts.append((x0 + (x1 - x0) * u, y0 - (y0 - y1) * 0.92 * _b09_curve(u)))
    if len(pts) > 1:
        _poly(c, pts, E.MEMBRANE, 4, fa, glow=True)
    hl = ease(seg(s, 6.1, 6.8))
    if hl > 0:                                                                     # 平台段：较低的那一截高亮
        plat = [(x0 + (x1 - x0) * k / n, y0 - (y0 - y1) * 0.92 * _b09_curve(k / n)) for k in range(int(n * 0.55), n + 1)]
        _poly(c, plat, OFF, 5, hl, glow=True)
    c.text((1000, 830), B09_LABEL, 64, INK, ease(seg(s, 6.2, 6.9)), anchor="mm", weight_glow=True)
    return _done(c, W, H, glow_radius=12, glow_gain=0.7)


# ---- B_10b：HUD 光脉冲列和锋电位列对齐（HUD，1.35 s，F6，不画频率上限） --------------------------------
B10_ROWS = ("光脉冲", "锋电位")


@shot("B_10b")
def b_10b(t, dur, W, H):
    """HUD 两行：上一行通道蓝的光脉冲小方块，下一行膜青锋电位，一一对齐，竖向虚线连着每一对。没有 Hz、没有刻度数字。"""
    s = _warp(t, dur, 1.35)
    c = _canvas(W, H, HUD_BG)
    fa = _cut_in(s)
    box = (260, 230, 1660, 790)
    _hud_frame(c, box, HUD_LINE, a=0.9 * fa)
    yl, ys = 400, 640
    c.text((300, yl), B10_ROWS[0], 52, HUD_INK, fa, anchor="lm")
    c.text((300, ys), B10_ROWS[1], 52, HUD_INK, fa, anchor="lm")
    xs0, xs1, npulse = 560, 1580, 8
    c.line((xs0, yl + 40), (xs1, yl + 40), HUD_LINE, 2, a=0.6 * fa)
    c.line((xs0, ys + 40), (xs1, ys + 40), HUD_LINE, 2, a=0.6 * fa)
    run = 0.3 + 0.7 * ease_out(seg(s, 0.0, 0.8))
    for i in range(npulse):
        x = xs0 + 40 + (xs1 - xs0 - 80) * i / (npulse - 1)
        if (x - xs0) / (xs1 - xs0) > run:
            break
        c.rect((x - 16, yl - 30, x + 16, yl + 40), fill=E.CHANNEL, a=fa, glow=True)
        sp = [(x - 40, ys + 40), (x - 8, ys + 40), (x, ys - 60), (x + 10, ys + 58), (x + 22, ys + 40), (x + 40, ys + 40)]
        _poly(c, sp, E.MEMBRANE, 4, fa, glow=True)
        _dashed_rect(c, (x, yl + 52, x, ys - 70), HUD_LINE, 2, 0.5, a=0.7 * fa, dash=10, gap=10)
    return _done(c, W, H, glow_radius=12, glow_gain=0.8)


# ---- B_11a：左列论文署名｜右列 2026 新闻稿，两列都保留（信息图，F6 / F1） -----------------------------
B11_L_HEAD = "论文署名"
B11_L_ROWS = ("Boyden 第一", "Deisseroth 通讯")
B11_R_HEAD = "2026 新闻稿"
B11_R_ROWS = ("把这次发表", "记在 Deisseroth 名下")
B11_BASE = 15.0           # 字幕：0.30 第一作者是 Boyden / 2.80 通讯作者 / 5.48 新闻稿把 2005… / 8.52 Deisseroth 名下 / 10.67 两句话都对


@shot("B_11a")
def b_11a(t, dur, W, H):
    """左右两栏同等分量：左栏「论文署名」两行随旁白依次进来；右栏「2026 新闻稿」随「诺奖新闻稿」进来，
    「记在 Deisseroth 名下」随那句落下。说到「两句话都对」时两栏框线同时变亮（两列都保留，不合并、不划掉）。"""
    s = _warp(t, dur, B11_BASE)
    c = _canvas(W, H, INFO_BG)
    fa = _cut_in(s, 0.6, 0.4)
    both = ease(seg(s, 10.7, 11.4))
    panels = ((200, 200, 920, 800), (1000, 200, 1720, 800))
    heads = (B11_L_HEAD, B11_R_HEAD)
    rows = (B11_L_ROWS, B11_R_ROWS)
    times = ((0.5, 3.0), (5.6, 8.6))
    for k in range(2):
        pa = fa if k == 0 else ease(seg(s, 5.3, 6.0))
        col = _mix(HUD_LINE, E.CHANNEL, both)
        c.rect(panels[k], fill=_scale(E.MEMBRANE, 0.04), outline=col, width=2.5 + 1.5 * both, a=pa, radius=12,
               glow=both > 0)
        cx = (panels[k][0] + panels[k][2]) / 2
        c.text((cx, 300), heads[k], 54, DIM, pa, anchor="mm")
        c.line((panels[k][0] + 60, 360), (panels[k][2] - 60, 360), HUD_LINE, 2, a=0.6 * pa)
        for i, (line, at) in enumerate(zip(rows[k], times[k])):
            c.text((cx, 480 + 140 * i), line, 64, INK, ease(seg(s, at, at + 0.6)), anchor="mm")
    return _done(c, W, H, glow_radius=10, glow_gain=0.6)


# ---- B_11b：一行「第一作者 Boyden」，下一行空着（排版，1.35 s，F6） -----------------------------------
B11B_LINE = "第一作者 Boyden"


@shot("B_11b")
def b_11b(t, dur, W, H):
    s = _warp(t, dur, 1.35)
    c = _canvas(W, H, TYPE_BG)
    _stext(c, (960, 400), B11B_LINE, 96, INK, _cut_in(s), anchor="mm", glow=0.2)
    _empty_row(c, 640, 1280, 600, ease(seg(s, 0.2, 0.5)), run=ease_out(seg(s, 0.2, 0.8)))   # 下一行空着，不写得主
    return _done(c, W, H, glow_radius=10)


# ---- B_12a：三行 Deisseroth、Hegemann、Nagel，第四行空着（排版，F1） -------------------------------------
B12_HEAD = "2026 生理学或医学奖"
B12_NAMES = ("Deisseroth", "Hegemann", "Nagel")          # 顺序按诺奖新闻稿（F1）
B12_BASE = 9.54           # 字幕：0.30 2026 年的…得主是 / 2.97 Deisseroth / 4.64 Hegemann 和 Nagel / 6.97 Boyden 不在这份名单上


@shot("B_12a")
def b_12a(t, dur, W, H):
    """小字头「2026 生理学或医学奖」，三行名字随旁白依次进来；说到「Boyden 不在这份名单上」时第四行只出现一道空虚线，
    什么也不写（不出现第四个得主，也不写 Boyden）。"""
    s = _warp(t, dur, B12_BASE)
    c = _canvas(W, H, TYPE_BG)
    _stext(c, (960, 200), B12_HEAD, 48, DIM, _cut_in(s, 0.6, 0.4), anchor="mm")
    for i, (name, at) in enumerate(zip(B12_NAMES, (3.0, 4.7, 5.9))):
        _stext(c, (960, 330 + 140 * i), name, 96, INK, ease(seg(s, at, at + 0.6)), anchor="mm", glow=0.2)
    _empty_row(c, 720, 1200, 330 + 140 * 3, ease(seg(s, 7.0, 7.6)), run=ease_out(seg(s, 7.0, 7.9)))
    return _done(c, W, H, glow_radius=10)


# ---- B_12b：「2026 生理学或医学奖」三行，没有 Boyden（信息图，1.35 s，F1） -----------------------------
@shot("B_12b")
def b_12b(t, dur, W, H):
    s = _warp(t, dur, 1.35)
    c = _canvas(W, H, INFO_BG)
    a = _cut_in(s)
    box = (560, 180, 1360, 800)
    c.rect(box, fill=_scale(E.MEMBRANE, 0.04), outline=HUD_LINE, width=2.5, a=a, radius=12)
    c.text((960, 270), B12_HEAD, 54, INK, a, anchor="mm", weight_glow=True)
    c.line((620, 330), (1300, 330), HUD_LINE, 2, a=0.6 * a)
    for i, name in enumerate(B12_NAMES):
        ra = a if i == 0 else ease(seg(s, 0.08 * i, 0.08 * i + 0.3))
        y = 440 + 120 * i
        c.circle((720, y), 13, fill=E.CHANNEL, a=ra, glow=True)
        c.text((770, y), name, 64, INK, ra, anchor="lm")
    return _done(c, W, H, glow_radius=10, glow_gain=0.6)


# ---- B_13b：「optogenetics」逐字出现，年份 2006（排版，1.35 s，F7） ---------------------------------------
B13_WORD = "optogenetics"
B13_YEAR = "2006"


@shot("B_13b")
def b_13b(t, dur, W, H):
    """词从第一帧起已有前两个字母，0.75 秒内逐字打完；年份在下方小一号等宽字。"""
    s = _warp(t, dur, 1.35)
    c = _canvas(W, H, TYPE_BG)
    f = serif_font(int(c.px(130)))
    full_w = _tw(c, B13_WORD, f)
    x0 = 960 - full_w / 2
    n = min(len(B13_WORD), 2 + int(seg(s, 0.0, 0.75) * (len(B13_WORD) - 2) + 0.999))
    _stext(c, (x0, 440), B13_WORD[:n], 130, INK, 1.0, anchor="lm", glow=0.25)
    _stext(c, (960, 600), B13_YEAR, 60, _scale(INK, 0.7), ease(seg(s, 0.6, 0.95)), anchor="mm", fnt=mono_font)
    return _done(c, W, H, glow_radius=10)


# ---- B_15a：HUD 时间轴 2005 培养神经元 → 2007 光纤活体（HUD，F6 / F8 / F1，不填月份） ----------------------
B15_NODES = (("2005", "培养神经元"), ("2007", "光纤活体"))
B15_BASE = 12.95          # 字幕：0.30 新闻稿说 / 1.12 Deisseroth / 3.16 大约两年后 / 5.81 活体小鼠的脑里 / 8.88 光纤论文…2007 年


@shot("B_15a")
def b_15a(t, dur, W, H):
    """HUD 框里一条横向时间轴，只有两个节点。2005 节点随「那次神经元实验」亮；轴线随「大约两年后」画到 2007；
    「活体小鼠」时 2007 节点和「光纤活体」进来，「2007 年」时年份高亮。两点之间没有刻度、没有月份。慢推镜。"""
    s = _warp(t, dur, B15_BASE)
    c = _canvas(W, H, HUD_BG)
    fa = _cut_in(s, 0.6, 0.4)
    _hud_frame(c, (260, 200, 1660, 800), HUD_LINE, a=0.9 * fa)
    xa, xb, y = 520, 1400, 500
    c.line((340, y), (xa, y), HUD_LINE, 2, a=0.5 * fa)
    c.line((xb, y), (1580, y), HUD_LINE, 2, a=0.5 * fa)
    run = ease(seg(s, 3.3, 5.8))
    c.line((xa, y), (xb, y), E.CHANNEL, 4, a=fa, progress=run, glow=True)
    a1 = ease(seg(s, 3.2, 3.8))
    a2 = ease(seg(s, 5.9, 6.5))
    hi = ease(seg(s, 8.9, 9.5))
    for (yr, lab), x, a, hl in ((B15_NODES[0], xa, a1, 1.0), (B15_NODES[1], xb, a2, hi)):
        c.circle((x, y), 22, outline=HUD_LINE, width=3, a=fa)
        c.circle((x, y), 13, fill=E.CHANNEL, a=a, glow=True)
        c.text((x, y - 90), yr, 64, _mix(_scale(HUD_INK, 0.6), HUD_INK, hl), a, anchor="mm", weight_glow=hl > 0.5)
        c.text((x, y + 95), lab, 60, HUD_INK, a, anchor="mm")
    img = _done(c, W, H, glow_radius=12, glow_gain=0.8)
    return _zoom(img, 1.0 + 0.03 * ease(seg(s, 0.0, B15_BASE)))


# ---- B_17a：同一细胞两行「蓝光开」「黄光关」+ 两条分开的光谱色带（信息图，F8，不标纳米） --------------------
B17_ROWS = (("蓝光开", E.CHANNEL), ("黄光关", OFF))
B17_BASE = 8.51           # 字幕：0.30 黄光和蓝光的光谱分开 / 2.53 同一套细胞里…两种蛋白 / 5.43 蓝光负责打开，黄光负责关掉


def _band(c, x0, x1, y, h, col, a, run=1.0):
    """一条柔边色带（位置、宽度 simplified，不是刻度）。"""
    n = 24
    for k in range(n):
        u = k / (n - 1)
        if u > run:
            break
        w = math.sin(math.pi * u) ** 0.8
        x = x0 + (x1 - x0) * u
        c.rect((x - (x1 - x0) / n / 2 - 1, y - h / 2, x + (x1 - x0) / n / 2 + 1, y + h / 2),
               fill=_scale(col, 0.25 + 0.75 * w), a=a * w, glow=True)


@shot("B_17a")
def b_17a(t, dur, W, H):
    """下方一根无刻度的「波长」轴，两条分开的色带（蓝在短的一侧、黄在长的一侧），随「光谱分开」铺开并留出空隙。
    上方一个细胞轮廓（同一个细胞，膜上两种蛋白），右侧两行「蓝光开」「黄光关」随「蓝光负责打开，黄光负责关掉」进来。"""
    s = _warp(t, dur, B17_BASE)
    c = _canvas(W, H, INFO_BG)
    fa = _cut_in(s, 0.6, 0.4)
    ay = 740
    _arrow(c, (360, ay + 50), (1580, ay + 50), HUD_LINE, 2.5, a=fa, head=16)
    c.text((1580, ay + 90), "波长", 40, DIM, fa, anchor="rm")
    _band(c, 520, 860, ay, 60, E.CHANNEL, fa, run=ease_out(seg(s, 0.3, 1.5)))
    _band(c, 1080, 1420, ay, 60, OFF, fa, run=ease_out(seg(s, 0.8, 2.0)))
    ca = ease(seg(s, 2.6, 3.3))
    cx, cy = 640, 420
    c.circle((cx, cy), 170, fill=_scale(E.MEMBRANE, 0.06), outline=_mix(E.LINE, E.MEMBRANE, 0.3), width=3, a=ca)
    for k in range(10):                                                            # 膜上两种蛋白（交替的小块）
        th = 2 * math.pi * k / 10 - math.pi / 2
        col = E.CHANNEL if k % 2 == 0 else OFF
        x, y = cx + 170 * math.cos(th), cy + 170 * math.sin(th)
        c.circle((x, y), 13, fill=col, a=ca * ease(seg(s, 3.0 + 0.08 * k, 3.4 + 0.08 * k)), glow=True)
    for i, ((txt, col), at) in enumerate(zip(B17_ROWS, (5.5, 6.4))):
        y = 340 + 160 * i
        a = ease(seg(s, at, at + 0.6))
        c.circle((1000, y), 18, fill=col, a=a, glow=True)
        c.text((1060, y), txt, 76, INK, a, anchor="lm")
    return _done(c, W, H, glow_radius=12, glow_gain=0.7)


# ---- B_18b：箭头从蓝光通道指向更长波长的 ChrimsonR（信息图，1.35 s，F17 / F6） --------------------------
B18B_LEFT = "蓝光通道"
B18B_RIGHT = "ChrimsonR"
B18B_MID = "更长波长"


@shot("B_18b")
def b_18b(t, dur, W, H):
    """两枚名签：左蓝光通道（通道蓝）、右 ChrimsonR（暖色），中间一支箭头，箭头上方「更长波长」。
    箭头读作「敏感波长往长推」，不是谱系（ChrimsonR 来自 Chrimson，不是 ChR2 的突变体）；不画纳米刻度。"""
    s = _warp(t, dur, 1.35)
    c = _canvas(W, H, INFO_BG)
    a = _cut_in(s)
    _chip(c, (520, 470), B18B_LEFT, 64, E.CHANNEL, a)
    _chip(c, (1400, 470), B18B_RIGHT, 64, RED_SHIFT, ease(seg(s, 0.25, 0.6)), fnt=font)
    run = 0.3 + 0.7 * ease_out(seg(s, 0.0, 0.5))
    n = 20
    x0, x1 = 760, 1150
    for k in range(int(n * run)):                                                 # 箭身颜色从蓝渐到暖色
        u0, u1 = k / n, (k + 1) / n
        c.line((x0 + (x1 - x0) * u0, 470), (x0 + (x1 - x0) * u1, 470), _mix(E.CHANNEL, RED_SHIFT, u1), 6, a=a,
               glow=True)
    _arrow(c, (x1 - 1, 470), (x1 + 30, 470), RED_SHIFT, 6, a=a * ease(seg(run, 0.95, 1.0)), head=30, glow=True)
    c.text((955, 380), B18B_MID, 54, INK, ease(seg(s, 0.3, 0.65)), anchor="mm")
    return _done(c, W, H, glow_radius=10, glow_gain=0.7)


# ---- B_19a：2013 Brain Prize 六个名字一行，没有肖像（信息图，F14） --------------------------------------
B19_HEAD = "2013 Brain Prize"
B19_SUB = "隆德贝克基金会"
B19_NAMES = ("Bamberg", "Boyden", "Deisseroth", "Hegemann", "Miesenböck", "Nagel")   # brainprize.org 的顺序（F14）
B19_AT = (5.49, 7.22, 8.95, 10.97, 12.84, 14.86)
B19_BASE = 16.84          # 字幕：0.30 两份名单。2013 年 / 2.17 隆德贝克基金会 / 3.33 Brain Prize 授给六个人 / 各名字时刻见 B19_AT


def _name_row_xs(c, names, size, gap, cx=960):
    f = font(int(c.px(size)))
    ws = [_tw(c, n, f) + 2 * 26 for n in names]
    total = sum(ws) + gap * (len(names) - 1)
    x = cx - total / 2
    out = []
    for w in ws:
        out.append(x + w / 2)
        x += w + gap
    return out


@shot("B_19a")
def b_19a(t, dur, W, H):
    """硬切进来：标题「2013 Brain Prize」和六个空的虚线位第 1 帧就在（_cut_in），「隆德贝克基金会」小字随旁白；六枚同样大小的名签排成一行，
    每个名字在旁白念到时亮起（之前是空的虚线位）。没有照片、没有肖像，六个人同等分量。"""
    s = _warp(t, dur, B19_BASE)
    c = _canvas(W, H, INFO_BG)
    fa = _cut_in(s, 0.6, 0.4)
    c.text((960, 300), B19_HEAD, 80, INK, fa, anchor="mm", weight_glow=True)
    c.text((960, 395), B19_SUB, 44, DIM, ease(seg(s, 2.2, 2.8)), anchor="mm")
    size, y = 46, 560
    xs = _name_row_xs(c, B19_NAMES, size, 22)
    f = font(int(c.px(size)))
    for x, name, at in zip(xs, B19_NAMES, B19_AT):
        w = _tw(c, name, f) + 52
        slot = (x - w / 2, y - 48, x + w / 2, y + 48)
        sa = fa * (1 - ease(seg(s, at, at + 0.5)))
        if sa > 0:
            _dashed_box(c, slot, EMPTY, sa)
        _chip(c, (x, y), name, size, _mix(E.LINE, E.MEMBRANE, 0.4), ease(seg(s, at, at + 0.5)), pad=(26, 25))
    return _done(c, W, H, glow_radius=10, glow_gain=0.6)


# ---- B_19b：六个人名分两列，不配照片（排版，1.35 s，F14） -------------------------------------------------
@shot("B_19b")
def b_19b(t, dur, W, H):
    s = _warp(t, dur, 1.35)
    c = _canvas(W, H, TYPE_BG)
    for i, name in enumerate(B19_NAMES):
        col, row = i // 3, i % 3
        a = _cut_in(s) if i == 0 else ease(seg(s, 0.05 * i, 0.05 * i + 0.3))
        _stext(c, (700 + 520 * col, 330 + 150 * row), name, 84, INK, a, anchor="mm", glow=0.2, fnt=font)
    return _done(c, W, H, glow_radius=10)


# ---- B_20a：六人框里圈出 Boyden、Bamberg、Miesenböck →「不在 2026 诺奖三人里」（蓝图，F14 / F1） -------------
B20_TITLE = "2013 Brain Prize · 六人"
B20_NOT = "不在 2026 诺奖三人里"
B20_PICK = {"Boyden": 0.4, "Bamberg": 2.5, "Miesenböck": 4.0}   # 字幕：0.30 Boyden / 2.40 Bamberg / 3.93 Miesenböck
B20_GRID = ("Deisseroth", "Hegemann", "Nagel", "Bamberg", "Boyden", "Miesenböck")   # 被圈的三人放下排，箭头往下不压字
B20_BASE = 12.92          # 字幕：6.22 2026 年的诺奖是三个人 / 8.51 前一份奖不是诺贝尔奖 / 10.42 两份名单也不能并成一份


@shot("B_20a")
def b_20a(t, dur, W, H):
    """蓝图图框里一个六人框（两行三列；被圈的三人排在下排、各排内按字母序，好让箭头直接往下、不压住别的名字），旁白念到 Boyden、Bamberg、Miesenböck 时依次被琥珀虚线圈出；
    说到「诺奖是三个人」时三支箭头从圈出的名字往下汇到琥珀字「不在 2026 诺奖三人里」。六人框一直完整保留，
    不划掉任何人、不和诺奖名单并成一份。慢推镜（同 B_15a）。"""
    s = _warp(t, dur, B20_BASE)
    a = _cut_in(s, 0.6, 0.4)
    c = _bp_canvas(W, H, a)
    c.rect((60, 60, 1860, 860), outline=BP_LINE, width=2, a=0.45 * a)
    box = (330, 170, 1590, 560)
    c.rect(box, fill=_mix(BP_BG, BP_LINE, 0.05), outline=BP_LINE, width=2.5, a=a, radius=6)
    c.text((box[0] + 30, box[1] + 42), B20_TITLE, 40, BP_SUB, a, anchor="lm")
    c.line((box[0], box[1] + 84), (box[2], box[1] + 84), BP_SUB, 2, a=a)
    pos = {}
    for i, name in enumerate(B20_GRID):
        r, k = i // 3, i % 3
        x, y = 540 + 420 * k, 350 + 120 * r
        pos[name] = (x, y)
        c.text((x, y), name, 56, BP_LINE, a, anchor="mm")
    f = font(int(c.px(56)))
    for name, at in B20_PICK.items():
        x, y = pos[name]
        w = _tw(c, name, f)
        ca = ease(seg(s, at, at + 0.4))
        if ca > 0:
            _dashed_rect(c, (x - w / 2 - 30, y - 46, x + w / 2 + 30, y + 46), OFF, 3.5,
                         ease_out(seg(s, at, at + 0.8)), a=ca, glow=True)
    target = (960, 730)
    ar = ease_out(seg(s, 6.3, 7.3))
    for name in B20_PICK:
        x, y = pos[name]
        _arrow(c, (x, y + 52), (target[0] + (x - 960) * 0.25, target[1] - 52), OFF, 3, a=ease(seg(s, 6.3, 6.6)),
               progress=ar, head=18)
    c.text(target, B20_NOT, 64, OFF, ease(seg(s, 7.0, 7.6)), anchor="mm", weight_glow=True)
    img = _done(c, W, H, glow_radius=8, glow_gain=0.6)
    return _zoom(img, 1.0 + 0.03 * ease(seg(s, 0.0, B20_BASE)))


# ---- B_20b：大字「六人奖 ≠ 三人诺奖」（排版，1.35 s，F14 / F1） --------------------------------------------
B20B_L, B20B_NE, B20B_R = "六人奖", "≠", "三人诺奖"


@shot("B_20b")
def b_20b(t, dur, W, H):
    s = _warp(t, dur, 1.35)
    c = _canvas(W, H, TYPE_BG)
    a = _cut_in(s)
    size = 140
    fs = serif_font(int(c.px(size)))
    fn = font(int(c.px(size)))
    gap = 50
    wl, wn, wr = _tw(c, B20B_L, fs), _tw(c, B20B_NE, fn), _tw(c, B20B_R, fs)
    x = 960 - (wl + wn + wr + 2 * gap) / 2
    y = 460
    _stext(c, (x, y), B20B_L, size, INK, a, anchor="lm", glow=0.2)
    c.text_font((x + wl + gap, y), B20B_NE, fn, OFF, ease(seg(s, 0.15, 0.45)), "lm", 0.4)
    _stext(c, (x + wl + wn + 2 * gap, y), B20B_R, size, INK, a, anchor="lm", glow=0.2)
    return _done(c, W, H, glow_radius=10)
