"""E2 B 段（第二幕）Blender raw 帧的叠字后处理（Pillow）。B 段的 2D 镜头（B_08b、B_09a……）还没写。

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
