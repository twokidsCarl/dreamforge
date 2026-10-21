"""E2 C 段（第三幕）的 2D 镜头和 Blender raw 帧的叠字后处理（Pillow）。

C_01a：整脑示意（c_scenes.brain，energy 暗底）+「小鼠」。只标对象是小鼠（F9：Ramirez 等 2013 的实验对象），
不标脑区名、不写「记忆」。字在齿状回那一簇细胞亮起之后进来，位置跟着锚点 LabelAnchor_Mouse 投影。
C_07a：视网膜剖面（c_scenes.retina phase=rp，xray 浅灰底）+「可转导」。只标神经节细胞（F11：感光细胞死去、神经节细胞留着；
builder 里通道装在神经节细胞上），不写疗效、不写视力数字。字在神经节细胞套上蓝色光晕之后进来，位置跟着锚点
LabelAnchor_Transducible 投影（与 Blender 相机同一套数学，e2_common.project_point）。
读帧、相机和标签的共用件在 raw_overlay.py。
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "blender", "scripts"))

import build_retina as BR  # noqa: E402
import e2_common as E  # noqa: E402
import raw_overlay as R  # noqa: E402
from mograph import ease, ease_out, seg, shot  # noqa: E402
from overlay_labels import font  # noqa: E402

FPS = 24


# ---- C_01a：整脑示意 +「小鼠」 ----------------------------------------------------------------
C01_LABEL = "小鼠"
C01_ANCHOR = (0.75, 0.0, 0.75)                         # c_scenes.brain：LabelAnchor_Mouse（脑的前上方）
C01_AIM = (-0.1, 0.1, 0.0)
C01_LOC0 = (-0.5, -4.6, 1.9)
C01_LOC1 = tuple(C01_LOC0[i] + (C01_AIM[i] - C01_LOC0[i]) * 0.22 for i in range(3))   # S.toward(loc0, aim, 0.22)


@shot("C_01a")
def c_01a(t, dur, W, H):
    """齿状回一簇细胞在 u=0.22 起亮（c_scenes），字幕「这里只深讲一件事，而且只讲小鼠」从 6.4 s（u≈0.65）起：
    字在 0.62→0.72 淡入，停到结尾。镜头推近后锚点投影会出到画面上沿，字的纵向限制在 0.12H 以下。"""
    f, n, u = R.frame_of(t, dur)
    base = R.raw_frame("C_01a", f, W).resize((W, H), Image.LANCZOS)
    a = ease(seg(u, 0.62, 0.72))
    if a <= 0:
        return base
    k = H / 1080
    loc, aim = R.dolly(f, n, C01_AIM, C01_LOC0, C01_LOC1)
    x, y = E.project_point(C01_ANCHOR, loc, aim, W, H)
    return R.tag(base, C01_LABEL, (x, max(0.12 * H, y)), k, a=a, size=48, edge=E.CHANNEL, halo=E.CHANNEL_DEEP)


# ---- C_07a：视网膜剖面 + 「可转导」 ------------------------------------------------------------
C07_LABEL = "可转导"
C07_ANCHOR = (2.3, -0.5, BR.layer_z("GCL"))           # c_scenes.retina：LabelAnchor_Transducible
C07_INK = (22, 52, 128)                                # 深通道蓝：浅灰 xray 底上要深色字
C07_PILL = (246, 248, 252)                             # 字后的浅色衬底，压住后面的树突和细胞点


@shot("C_07a")
def c_07a(t, dur, W, H):
    """Blender 帧（<quality>_raw）+「可转导」，写到 <quality>/。神经节细胞光晕在镜头比例 0.62→0.72 亮起（c_scenes），
    引线先画出（0.64→0.70），字随后淡入（0.66→0.76）并停到结尾。"""
    n = max(1, round(dur * FPS))
    f = int(round(t * FPS)) + 1
    base = R.raw_frame("C_07a", f, W).resize((W, H), Image.LANCZOS)
    u = (f - 1) / max(1, n - 1)                        # 与 c_scenes._f 同一套比例
    lead = ease(seg(u, 0.64, 0.70))
    a = ease(seg(u, 0.66, 0.76))
    if lead <= 0:
        return base
    k = H / 1080
    loc, aim = R.dolly(f, n, (0.0, 0.0, 1.22), (-0.3, -9.4, 1.9), (0.6, -6.6, 1.4), (0.4, 0.0, 1.05))
    ax, ay = E.project_point(C07_ANCHOR, loc, aim, W, H)
    ay -= 40 * k                                       # 锚点在胞体中心偏下（y=-0.5 靠镜头）：点落在亮起的胞体上
    # 字放在神经节细胞行上方的内核层一带、锚点左上；下方约 18% 是字幕安全区，不往下放
    fn = font(int(54 * k))
    tx, ty = ax - 150 * k, ay - 250 * k
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    elbow = (ax, ty)                                   # 折线引线：字的右侧 → 竖直落到锚点
    x0, y0, x1, y1 = d.textbbox((tx, ty), C07_LABEL, font=fn, anchor="rm")
    pad = 14 * k
    box = (x0 - pad, y0 - pad * 0.7, x1 + pad, y1 + pad * 0.7)
    lw = max(1, round(3 * k))
    pts = [(box[2], ty), elbow, (ax, ay)]
    seglen = [abs(pts[1][0] - pts[0][0]), abs(pts[2][1] - pts[1][1])]
    run = lead * sum(seglen)
    if run > 0:
        e1 = min(1.0, run / seglen[0]) if seglen[0] else 1.0
        d.line([pts[0], (pts[0][0] + (pts[1][0] - pts[0][0]) * e1, ty)], fill=(*C07_INK, int(220 * lead)), width=lw)
        if run > seglen[0]:
            e2 = min(1.0, (run - seglen[0]) / seglen[1])
            d.line([elbow, (ax, ty + (ay - ty) * e2)], fill=(*C07_INK, int(220 * lead)), width=lw)
    if lead >= 1.0:
        r = 6 * k
        d.ellipse((ax - r, ay - r, ax + r, ay + r), outline=(*C07_INK, 230), width=lw)
    if a > 0:
        d.rounded_rectangle(box, radius=10 * k, fill=(*C07_PILL, int(200 * a)), outline=(*E.CHANNEL_DEEP, int(200 * a)),
                            width=lw)
        d.text((tx, ty), C07_LABEL, font=fn, fill=(*C07_INK, int(255 * a)), anchor="rm")
    # 一圈很淡的通道蓝晕，和细胞上的光晕呼应（加在底图上，不压暗）
    halo = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(halo).rounded_rectangle(box, radius=10 * k, fill=(*E.CHANNEL, int(120 * a)))
    halo = halo.filter(ImageFilter.GaussianBlur(14 * k))
    out = Image.alpha_composite(base.convert("RGBA"), halo)
    return Image.alpha_composite(out, layer).convert("RGB")


# ================================================================================================
# C 段的纯 2D 镜头（排版 / 信息图 / HUD）。画法、配色、超采样跟 a0.py 同一套（从 a0 取小工具）。
# 屏幕字逐字照 research/visual/audit_C.yaml（与分镜 visual 一致）。下方约 18%（y > 885，1080p）是字幕安全区，不放字。
# 时间点按 storyboard.timed.yaml 的字幕时刻写（板面基准 = 当前 timed 时长），重新定时后用 _warp 按比例缩放。
# 事实边界：F9 只说小鼠、不写改写记忆；F11 只说部分且离不开护目镜、不写视力数字；F12 受理 ≠ 获批、不写 PDUFA 日期、公告 ≠ 许可。
# ================================================================================================
from a0 import HUD_BG, INK, _canvas, _done, _hud_frame, _mix, _scale, _stext, _warp, _zoom  # noqa: E402
from overlay_labels import mono_font, serif_font  # noqa: E402

TYPE_BG = (0, 0, 0)                                     # 排版卡：纯黑（同 A0_02a / A0_04b）
INFO_BG = (8, 10, 16)                                   # 信息图：暗底（同 A0_03a）
HUD_LINE = _mix(E.MEMBRANE, HUD_BG, 0.45)               # HUD 框线（同 A0_01b / A0_92）
HUD_INK = _mix(E.LINE, E.MEMBRANE, 0.25)                # HUD 读数字
DIM = _scale(INK, 0.55)
SAFE_Y = 885                                            # 字幕安全区上沿（1080p）


def _cut_in(s, b=0.3, a0=0.45):
    """硬切进来的镜头：第 1 帧就有 a0 的亮度，b 秒内升满（第 1 帧不是空黑）。"""
    return a0 + (1 - a0) * ease(seg(s, 0.0, b))


def _tw(c, s, f):
    """字宽（1080p 像素）。"""
    return c.d.textlength(s, font=f) / c.px(1)


def _strike(c, x0, x1, y, run, color, a=1.0, width=5):
    """从左到右画一道划线（run 0–1）。"""
    if run > 0:
        c.line((x0, y), (x0 + (x1 - x0) * run, y), color, width, a=a)


def _lamp(c, xy, on, a, col=E.CHANNEL):
    """HUD 状态灯：on=True 实心亮灯（有）；on=False 空心环 + 横杠（不涉及），不用红色、不用叉。"""
    x, y = xy
    if on:
        c.circle((x, y), 15, fill=col, a=a, glow=True)
        c.circle((x, y), 24, outline=col, width=2.5, a=0.6 * a)
    else:
        c.circle((x, y), 22, outline=E.GREY, width=3, a=a)
        c.line((x - 11, y), (x + 11, y), E.GREY, 3, a=a)


def _sweep(c, box, u, col, a=1.0):
    """一道竖向扫描光从左扫到右（u 0–1），读数出现时用。"""
    if a <= 0 or not 0 < u < 1:
        return
    x0, y0, x1, y1 = box
    x = x0 + (x1 - x0) * u
    c.line((x, y0), (x, y1), col, 3, a=a * (1 - abs(2 * u - 1)) * 0.8, glow=True)


# ---- C_01b：标题「小鼠海马」+ 副题「不讲人体记忆操作」（信息图，1.35 s） ------------------------------
C01B_TITLE = "小鼠海马"
C01B_SUB = "不讲人体记忆操作"


def _hippo_icon(c, cx, cy, r, col, a, run=1.0):
    """海马切片示意小图标：CA 区 C 形带（口朝右）+ 齿状回 ⊃ 形带扣在 C 口上（与 C_02a 白模同一读法）。
    只是线稿符号，不标区名、不代表比例。run 0–1：两条带沿弧画出。"""
    if a <= 0 or run <= 0:
        return
    bands = ((cx, cy, r, 45, 315, 28), (cx + 0.92 * r, cy + 0.08 * r, 0.56 * r, -95, 95, 20))   # (中心, 半径, 起止角, 带宽)
    for x, y, rr, a0_, a1_, w in bands:
        end = a0_ + (a1_ - a0_) * run
        X, Y, R_ = c.px(x), c.px(y), c.px(rr)
        bb = [X - R_, Y - R_, X + R_, Y + R_]
        c.d.arc(bb, a0_, end, fill=(*_scale(col, 0.32), int(255 * a)), width=int(c.px(w)))
        c.d.arc(bb, a0_, end, fill=(*col, int(255 * a)), width=max(1, int(c.px(3))))
        c.g.arc(bb, a0_, end, fill=_scale(col, 0.4 * a), width=int(c.px(w)))


@shot("C_01b")
def c_01b(t, dur, W, H):
    """1.35 s 范围卡：左边一个海马线稿小图标（通道蓝），右边标题 + 一道细线 + 副题。副题是本片的范围声明（F9 notes）。"""
    s = _warp(t, dur, 1.35)
    c = _canvas(W, H, INFO_BG)
    ft = font(int(c.px(104)))
    fs = font(int(c.px(46)))
    tw = max(_tw(c, C01B_TITLE, ft), _tw(c, C01B_SUB, fs))
    icon_w = 220
    x0 = 960 - (icon_w + 70 + tw) / 2                   # 图标 + 字整体居中
    _hippo_icon(c, x0 + 90, 470, 84, E.CHANNEL, _cut_in(s), run=0.35 + 0.65 * ease_out(seg(s, 0.0, 0.6)))
    tx = x0 + icon_w + 70
    c.text((tx, 430), C01B_TITLE, 104, INK, _cut_in(s), anchor="ls")
    c.line((tx, 470), (tx + tw, 470), HUD_LINE, 2, a=0.9, progress=ease_out(seg(s, 0.15, 0.55)))
    c.text((tx, 530), C01B_SUB, 46, _scale(INK, 0.72), ease(seg(s, 0.3, 0.6)), anchor="lm")
    return _done(c, W, H, glow_radius=12, glow_gain=0.6)


# ---- C_04b：两行「甲，无电击」「实验组，冻结」（信息图，1.35 s） ----------------------------------------
C04B_LINES = ("甲，无电击", "实验组，冻结")


@shot("C_04b")
def c_04b(t, dur, W, H):
    """左侧色标：第一行是「环境甲」的膜青色块（与 C_02a / C_02b 地色同，artistic 区分色）；第二行是一个停住的暂停符号（冻结）。
    不画电击符号（甲里没有电击），不画小鼠痛苦特写。"""
    s = _warp(t, dur, 1.35)
    c = _canvas(W, H, INFO_BG)
    f = font(int(c.px(78)))
    tw = max(_tw(c, x, f) for x in C04B_LINES)
    x0 = 960 - (tw + 120) / 2
    ys = (400, 560)
    for i, (y, line) in enumerate(zip(ys, C04B_LINES)):
        a = _cut_in(s) if i == 0 else ease(seg(s, 0.2, 0.5))
        if i == 0:
            c.rect((x0, y - 34, x0 + 68, y + 34), fill=_scale(E.MEMBRANE, 0.55), outline=E.MEMBRANE, width=2.5, a=a,
                   radius=8)
        else:
            for dx in (14, 42):
                c.rect((x0 + dx, y - 32, x0 + dx + 14, y + 32), fill=E.LINE, a=a, radius=3)
        c.text((x0 + 120, y), line, 78, INK, a, anchor="lm")
    c.line((x0, 480), (x0 + tw + 120, 480), HUD_LINE, 2, a=0.7, progress=ease_out(seg(s, 0.1, 0.6)))
    return _done(c, W, H, glow_radius=10, glow_gain=0.5)


# ---- C_05a：划掉「一句话 / 一段人生」→「一批细胞的活动」（排版） ------------------------------------------
C05_OLD = ("一句话", "一段人生")
C05_SEP = " / "
C05_NEW = "一批细胞的活动"
C05_BASE = 11.76                                        # timed 时长；字幕：0.30 不是一句话…一段人生 / 3.64 是一批选定细胞的活动


@shot("C_05a")
def c_05a(t, dur, W, H):
    """旁白说「不是一句话」时「一句话」出现并被划掉，「也不是一段人生」同样；「写进去的是……」时两项变暗上移，
    「一批细胞的活动」在下方写出（通道蓝细线托底）。划掉的两项是旁白的否定，不是谁的说法；屏幕不写「改写记忆」（F9）。"""
    s = _warp(t, dur, C05_BASE)
    c = _canvas(W, H, TYPE_BG)
    size = 76
    f = serif_font(int(c.px(size)))
    w0, wsep, w1 = _tw(c, C05_OLD[0], f), _tw(c, C05_SEP, f), _tw(c, C05_OLD[1], f)
    total = w0 + wsep + w1
    slide = ease(seg(s, 1.65, 2.15))                    # 「一段人生」进来时，「一句话」从居中滑到左边
    x = 960 - total / 2 + (wsep + w1) / 2 * (1 - slide)
    up = ease(seg(s, 3.55, 4.25))                       # 旧的两项上移、变暗
    y = 470 - 130 * up
    dim = 1.0 - 0.55 * up
    a0_ = ease(seg(s, 0.45, 0.95))                      # 「一句话」
    a1_ = ease(seg(s, 1.75, 2.25))                      # 「一段人生」
    k0, k1 = ease_out(seg(s, 1.15, 1.55)), ease_out(seg(s, 2.75, 3.2))   # 两道划线
    _stext(c, (x, y), C05_OLD[0], size, _scale(INK, dim * (1 - 0.35 * k0)), a0_, anchor="lm")
    _stext(c, (x + w0, y), C05_SEP, size, _scale(INK, 0.45 * dim), a1_, anchor="lm")
    _stext(c, (x + w0 + wsep, y), C05_OLD[1], size, _scale(INK, dim * (1 - 0.35 * k1)), a1_, anchor="lm")
    strike_col = _scale(INK, 0.9 * dim)                 # 划掉后字压暗，划线比字亮
    _strike(c, x - 8, x + w0 + 8, y + 2, k0, strike_col, a0_)
    _strike(c, x + w0 + wsep - 8, x + total + 8, y + 2, k1, strike_col, a1_)
    # 新的一行
    na = ease(seg(s, 3.85, 4.55))
    nsize = 96
    fn = serif_font(int(c.px(nsize)))
    nw = _tw(c, C05_NEW, fn)
    _stext(c, (960, 540), C05_NEW, nsize, INK, na, anchor="mm", glow=0.25)
    c.line((960 - nw / 2, 618), (960 + nw / 2, 618), E.CHANNEL, 3, a=0.9 * na,
           progress=ease_out(seg(s, 4.3, 5.2)), glow=True)
    return _done(c, W, H, glow_radius=10, glow_gain=0.8)


# ---- C_06a：HUD 两行边界读数（F9，锁定文案） -------------------------------------------------------------
C06_LINE1 = "小鼠恐惧行为，已在实验中驱动"
C06_LINE2 = "人体记忆操作：本研究不涉及"         # 锁定（P6）；旧句「…，无此结果」读成全称否定，不再用
C06_BASE = 11.25                                         # timed 时长；字幕：2.88 选定细胞的活动…恐惧行为 / 7.19 它没有说明…人身上


@shot("C_06a")
def c_06a(t, dur, W, H):
    """HUD 框 + 两行状态读数。第一行随「足以支撑一种恐惧行为」进来，状态灯实心亮（通道蓝 = 有）；第二行随
    「它没有说明……」进来，状态灯是空心环加横杠（不涉及，不是否定全世界）。慢推镜（分镜 slow dolly-in）。"""
    s = _warp(t, dur, C06_BASE)
    c = _canvas(W, H, HUD_BG)
    fa = _cut_in(s, 0.6, 0.4)
    box = (330, 250, 1590, 790)
    _hud_frame(c, box, HUD_LINE, a=0.9 * fa)
    # 框内淡网格刻度（只有刻度，没有字和数）
    for k in range(1, 21):
        xx = box[0] + (box[2] - box[0]) * k / 21
        c.line((xx, box[3] - 26), (xx, box[3] - (40 if k % 5 == 0 else 32)), HUD_LINE, 2, a=0.45 * fa)
    c.line((box[0] + 40, 520), (box[2] - 40, 520), HUD_LINE, 2, a=0.5 * fa, progress=ease_out(seg(s, 0.2, 1.2)))
    rows = ((410, 3.0, True, C06_LINE1), (630, 7.3, False, C06_LINE2))
    for y, at, on, text in rows:
        a = ease(seg(s, at, at + 0.6))
        _sweep(c, (box[0] + 40, y - 70, box[2] - 40, y + 70), seg(s, at - 0.2, at + 0.7), E.MEMBRANE, fa)
        _lamp(c, (450, y), on, a)
        c.text((520, y), text, 64, HUD_INK if on else _mix(HUD_INK, E.GREY, 0.35), a, anchor="lm")
    img = _done(c, W, H, glow_radius=12, glow_gain=0.8)
    return _zoom(img, 1.0 + 0.04 * ease(seg(s, 0.0, C06_BASE)))


# ---- C_06b：一行「没有说明同样的操作已经用在人身上」（排版，1.35 s） --------------------------------------
C06B_LINE = "没有说明同样的操作已经用在人身上"


@shot("C_06b")
def c_06b(t, dur, W, H):
    s = _warp(t, dur, 1.35)
    c = _canvas(W, H, TYPE_BG)
    _stext(c, (960, 470), C06B_LINE, 74, INK, _cut_in(s), anchor="mm", glow=0.2)
    return _done(c, W, H, glow_radius=10)


# ---- C_10b：「部分功能恢复」「离不开护目镜」（排版，1.35 s） ---------------------------------------------
C10B_LINES = ("部分功能恢复", "离不开护目镜")


@shot("C_10b")
def c_10b(t, dur, W, H):
    """两行同等分量（F11：部分 + 离不开护目镜，两句一起才成立）；不写视力数字、不写治愈。"""
    s = _warp(t, dur, 1.35)
    c = _canvas(W, H, TYPE_BG)
    for i, line in enumerate(C10B_LINES):
        a = _cut_in(s) if i == 0 else ease(seg(s, 0.15, 0.45))
        _stext(c, (960, 390 + 150 * i), line, 92, INK, a, anchor="mm", glow=0.2)
    return _done(c, W, H, glow_radius=10)


# ---- C_11b：大字「如果获批」+ 小字「当时尚未获批」（排版，1.35 s） ----------------------------------------
C11B_BIG = "如果获批"
C11B_SMALL = "当时尚未获批"


@shot("C_11b")
def c_11b(t, dur, W, H):
    s = _warp(t, dur, 1.35)
    c = _canvas(W, H, TYPE_BG)
    _stext(c, (960, 430), C11B_BIG, 150, INK, _cut_in(s), anchor="mm", glow=0.25)
    _stext(c, (960, 600), C11B_SMALL, 52, DIM, ease(seg(s, 0.25, 0.55)), anchor="mm")
    return _done(c, W, H, glow_radius=12)


def _dashed_box(c, box, col, a, progress=1.0, width=2.5):
    from a0 import _dashed_rect
    _dashed_rect(c, box, col, width, progress, a=a)


# ---- C_11a：2026-09-09 · MCO-010 / MOGENRY「BLA 已受理」｜「尚未获批」（信息图，F12） -----------------------
C11_DATE = "2026-09-09"
C11_NAME = "MCO-010 / MOGENRY"
C11_ACCEPTED = "BLA 已受理"
C11_NOT = "尚未获批"
C11_BASE = 24.91          # timed 时长；字幕：0.30 日期 / 4.08 受理并 / 7.11 立案 MOGENRY… / 10.51 MCO-010 / 21.30 如果获批…尚未获批


@shot("C_11a")
def c_11a(t, dur, W, H):
    """上方一条时间轴只标一个点 2026-09-09（公告日，F12）。实线栏 = 这份申请：栏头 MCO-010 / MOGENRY，读数「BLA 已受理」
    （实心灯），先居中在日期下；旁白说到「所以当时尚未获批」时它滑到左边，右边进来虚线栏「尚未获批」（空心环 + 横杠），
    引线从同一个日期分叉到两栏（同一天的公告：受理了、还没批），停到结尾。不写 PDUFA 日期、不写上市；公司名只在旁白里。"""
    s = _warp(t, dur, C11_BASE)
    c = _canvas(W, H, INFO_BG)
    # 时间轴：只有一个点（公告日），在画面正中
    ax0, ax1, ay = 300, 1620, 240
    run = 0.3 + 0.7 * ease_out(seg(s, 0.0, 1.0))
    c.line((ax0, ay), (ax1, ay), HUD_LINE, 2, a=_cut_in(s, 0.5, 0.5), progress=run)
    for k in range(23):
        xx = ax0 + (ax1 - ax0) * k / 22
        if xx <= ax0 + (ax1 - ax0) * run:
            c.line((xx, ay - 6), (xx, ay + 6), HUD_LINE, 2, a=0.6)
    mx = 960
    da = ease(seg(s, 0.3, 0.9))
    c.rect((mx - 11, ay - 11, mx + 11, ay + 11), fill=E.MEMBRANE, a=da, glow=True, radius=3)
    c.text_font((mx, ay - 34), C11_DATE, mono_font(int(c.px(44))), HUD_INK, da, anchor="ms")
    # 两栏：先只有左栏（居中在日期下）；旁白说到「尚未获批」时左栏滑到左边，右栏进来，引线从日期分叉到两栏
    slide = ease(seg(s, 21.2, 22.0))
    pw, top, bot = 630, 380, 780
    lx = (mx - pw / 2) + (300 - (mx - pw / 2)) * slide   # 左栏左沿：645 → 300
    L = (lx, top, lx + pw, bot)
    Rb = (990, top, 1620, bot)
    fork_y = 315
    pa = ease(seg(s, 4.4, 5.0))
    lead = ease_out(seg(s, 4.4, 5.0))
    lcx = (L[0] + L[2]) / 2
    c.line((mx, ay + 14), (mx, fork_y), HUD_LINE, 2, a=0.8 * pa, progress=lead)
    if lead >= 1:
        c.line((mx, fork_y), (lcx, fork_y), HUD_LINE, 2, a=0.8 * pa)
        c.line((lcx, fork_y), (lcx, top), HUD_LINE, 2, a=0.8 * pa)
    rcx = (Rb[0] + Rb[2]) / 2
    ra = ease(seg(s, 21.6, 22.2))
    rl = ease_out(seg(s, 21.6, 22.3))
    if rl > 0:
        c.line((mx, fork_y), (rcx, fork_y), HUD_LINE, 2, a=0.8 * ra, progress=rl)
        if rl >= 1:
            c.line((rcx, fork_y), (rcx, top), HUD_LINE, 2, a=0.8 * ra)
    # 左栏：这份申请
    c.rect(L, fill=_scale(E.MEMBRANE, 0.06), outline=HUD_LINE, width=2.5, a=pa, radius=10)
    na = ease(seg(s, 7.6, 8.2))
    c.text_font((L[0] + 44, 462), C11_NAME, mono_font(int(c.px(46))), HUD_INK, na, anchor="lm")
    c.line((L[0] + 44, 520), (L[2] - 44, 520), HUD_LINE, 2, a=0.7 * na, progress=ease_out(seg(s, 7.8, 8.6)))
    sa = ease(seg(s, 5.6, 6.2))
    _lamp(c, (L[0] + 72, 640), True, sa)
    c.text((L[0] + 130, 640), C11_ACCEPTED, 64, HUD_INK, sa, anchor="lm")
    # 右栏：尚未获批
    _dashed_box(c, Rb, _mix(E.GREY, INFO_BG, 0.2), ra, progress=ease_out(seg(s, 21.8, 22.6)))
    xa = ease(seg(s, 22.5, 23.1))
    f64 = font(int(c.px(64)))
    w = 58 + _tw(c, C11_NOT, f64)
    x0 = rcx - w / 2
    _lamp(c, (x0 + 22, 580), False, xa)
    c.text((x0 + 80, 580), C11_NOT, 64, HUD_INK, xa, anchor="lm")
    return _done(c, W, H, glow_radius=10, glow_gain=0.6)


# ---- C_12a：RESTORE 读数 HUD（F12，公告所称） -------------------------------------------------------------
C12_WEEKS = ("第 52 周", "第 76 周")
C12_END = "视力终点达到"
C12_SAE = ("严重不良事件", "无治疗相关")
C12_FOOT = "申请方公告，不是已生效许可"
C12_BASE = 15.97          # timed 时长；字幕：1.51 第五十二周 / 4.72 第七十六周 / 6.93 终点 / 9.14 严重不良事件 / 12.15 申请方的公告


@shot("C_12a")
def c_12a(t, dur, W, H):
    """HUD：两格周读数（各带实心灯 + 「视力终点达到」，只复述公告的说法，不写视力数字）；一行严重不良事件读数；
    框底一行「申请方公告，不是已生效许可」随旁白最后一句进来，用一条琥珀细线隔开（琥珀 = 全片「关掉 / 未生效」的约定色）。慢推镜。"""
    s = _warp(t, dur, C12_BASE)
    c = _canvas(W, H, HUD_BG)
    fa = _cut_in(s, 0.6, 0.4)
    box = (330, 170, 1590, 850)
    _hud_frame(c, box, HUD_LINE, a=0.9 * fa)
    tiles = ((390, 240, 935, 500), (985, 240, 1530, 500))
    wk_at = (3.0, 5.4)
    ea = ease(seg(s, 7.4, 8.0))                         # 「主要终点」
    for (x0, y0, x1, y1), wk, at in zip(tiles, C12_WEEKS, wk_at):
        a = ease(seg(s, at, at + 0.5))
        _sweep(c, (x0, y0, x1, y1), seg(s, at - 0.2, at + 0.6), E.MEMBRANE, fa)
        c.rect((x0, y0, x1, y1), outline=HUD_LINE, width=2, a=0.8 * a, radius=8)
        c.text((x0 + 40, y0 + 80), wk, 60, HUD_INK, a, anchor="lm")
        _lamp(c, (x0 + 62, y0 + 185), True, a * ea)
        c.text((x0 + 116, y0 + 185), C12_END, 50, HUD_INK, a * ea, anchor="lm")
    sa = ease(seg(s, 10.2, 10.8))
    _sweep(c, (390, 545, 1530, 655), seg(s, 10.0, 10.9), E.MEMBRANE, fa)
    c.line((390, 545), (1530, 545), HUD_LINE, 2, a=0.5 * sa)
    c.text((420, 600), C12_SAE[0], 50, _mix(HUD_INK, E.GREY, 0.35), sa, anchor="lm")
    c.text((1500, 600), C12_SAE[1], 50, HUD_INK, sa, anchor="rm")
    c.line((420, 655), (1500, 655), HUD_LINE, 2, a=0.5 * sa)
    ba = ease(seg(s, 12.5, 13.1))
    c.line((420, 715), (1500, 715), E.AMBER, 2, a=0.8 * ba, progress=ease_out(seg(s, 12.4, 13.2)))
    c.text((960, 775), C12_FOOT, 54, _mix(HUD_INK, E.AMBER, 0.35), ba, anchor="mm")
    img = _done(c, W, H, glow_radius=12, glow_gain=0.8)
    return _zoom(img, 1.0 + 0.04 * ease(seg(s, 0.0, C12_BASE)))
