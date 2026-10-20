"""E2《光遗传学》共用常量：配色、字体、镜头位置、神经元排布、A0_04a 的时间表。

纯 Python，不 import bpy：Blender 场景（blender/shots/a0_scenes.py）和 2D 镜头（mograph/a0.py）都从这里取值，
同一个数在两边只写一次（WORKFLOW 8.1：共用位置用常量，不在各镜头里硬写）。
颜色来源：storyboard/page.yaml 的 accents（通道蓝 / 抑制琥珀 / 膜青）；蓝 = 打开，琥珀 = 关掉。
"""
import math
import os

# ---- 配色（sRGB 0-255）---------------------------------------------------------------------
CHANNEL = (142, 175, 255)        # #8eafff 通道蓝（亮）：打开
CHANNEL_DEEP = (47, 111, 224)    # #2f6fe0 通道蓝（深）
AMBER = (255, 193, 77)           # #ffc14d 抑制琥珀：关掉
MEMBRANE = (93, 222, 196)        # #5ddec4 膜青
LINE = (236, 240, 248)           # 线稿白
GREY = (150, 158, 178)           # 未动的细胞
BLACK = (4, 5, 8)


def srgb_to_linear(c):
    """0-255 sRGB 三元组 -> 线性 0-1（Blender 材质、灯光用）。"""
    def f(v):
        v /= 255.0
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    return tuple(f(v) for v in c[:3])


# ---- 字体（跨平台）--------------------------------------------------------------------------
_NOTO = "/usr/share/fonts/opentype/noto"


def _first(*paths):
    return next((p for p in paths if os.path.exists(p)), None)


# Blender 的文字对象只能读 .ttc 的第 0 号字面（JP），所以 Blender 里只放拉丁字母；中文一律走 Pillow（SC 字面，index=2）。
CJK_SANS = _first("/System/Library/Fonts/STHeiti Medium.ttc", f"{_NOTO}/NotoSansCJK-Medium.ttc",
                  f"{_NOTO}/NotoSansCJK-Regular.ttc", f"{_NOTO}/NotoSansCJK-Bold.ttc")


# ---- 神经元排布（A0_03a 的 2D 线稿和 A0_03b 的 Blender 白模共用）----------------------------------
NEURON_COUNT = 9
NEURON_CIRCLED = (1, 4, 7)       # 被圈出的那一类：间隔的 3 个，两侧始终保持灰
NEURON_SEEDS = tuple(101 + 7 * i for i in range(NEURON_COUNT))   # 每个神经元的形态随机种子


# ---- A0_04a：三个光点、镜头（Blender 与 Pillow 叠字共用）---------------------------------------
LIGHT_NAMES = ("Karl Deisseroth", "Peter Hegemann", "Georg Nagel")   # 顺序按诺奖新闻稿（F1）
DATE_LINE = "2026-10-05 · 诺贝尔生理学或医学奖"
# 三个光点依次亮起的时刻（镜头内秒）和日期行出现的时刻。配音定时后（retime）按旁白对齐再改这里。
# 2026-10-21 按定时后的旁白对齐（review_words：Deisseroth 4.88 s、Hegemann 6.02 s、Nagel 7.78 s，「理由」9.06 s）
A04_LIGHT_AT = (4.9, 6.0, 7.8)
A04_DATE_AT = 9.1
A04_DUR = 15.61                  # storyboard.timed.yaml 里 A0_04a 的时长
A04_FOCAL_MM = 50.0
A04_SENSOR_MM = 36.0


def a04_orb(i, t):
    """第 i 个光点在 t 秒的世界坐标（单位 BU，+Y 远离镜头，Z 向上）：基位置 + 缓慢漂移的小幅李萨如。"""
    base = ((-2.5, 0.0, 0.5), (0.1, 1.0, -0.35), (2.4, -0.5, 0.45))[i]
    ph = (0.0, 2.1, 4.3)[i]
    return (base[0] + 0.22 * math.sin(0.31 * t + ph),
            base[1] + 0.30 * math.sin(0.23 * t + 1.7 * ph),
            base[2] + 0.16 * math.sin(0.41 * t + 0.5 * ph))


def a04_camera(t, dur=A04_DUR):
    """镜头位置和注视点：缓慢推进（沿 +Y 靠近，约 2.6 BU，从 12.6 BU 远推到 10 BU），注视点随之轻微右移。返回 (loc, aim)。"""
    u = min(1.0, max(0.0, t / dur))
    u = u * u * (3 - 2 * u) * 0.35 + u * 0.65          # 起止柔和，中段近似匀速
    return (0.0 + 0.25 * u, -12.6 + 2.6 * u, 0.0), (0.05 + 0.1 * u, 0.0, 0.0)


def a04_project(i_or_pos, t, W, H, dur=A04_DUR):
    """把世界点投影到画面像素（与 Blender 的 TRACK_TO 相机一致：50 mm、36 mm 传感器、水平适配）。"""
    p = a04_orb(i_or_pos, t) if isinstance(i_or_pos, int) else i_or_pos
    loc, aim = a04_camera(t, dur)
    fwd = [aim[k] - loc[k] for k in range(3)]
    n = math.sqrt(sum(v * v for v in fwd))
    fwd = [v / n for v in fwd]
    right = [fwd[1], -fwd[0], 0.0]                      # fwd × Z
    rn = math.hypot(right[0], right[1])
    right = [v / rn for v in right]
    up = [right[1] * fwd[2] - right[2] * fwd[1], right[2] * fwd[0] - right[0] * fwd[2],
          right[0] * fwd[1] - right[1] * fwd[0]]
    d = [p[k] - loc[k] for k in range(3)]
    z = sum(d[k] * fwd[k] for k in range(3))
    x = sum(d[k] * right[k] for k in range(3))
    y = sum(d[k] * up[k] for k in range(3))
    s = A04_FOCAL_MM / A04_SENSOR_MM * W / z
    return W / 2 + x * s, H / 2 - y * s


# ---- 纸页镜头（A0_01a / A0_02b）--------------------------------------------------------------
PAPER_SIZE_M = (0.210, 0.297)    # A4，米；1 BU = 1 m
PAPER_ROW_PITCH_M = 0.0105
PAPER_LIT_ROW = 11               # 被侧光照亮的那一行（从纸的上端数起）
