"""E2《光遗传学》唯一调色板「Deep Lab」（STYLE_REVIEW §4.2）。2D 和 3D 都从这里取色，不在别处另写底色。

纯 Python，不 import bpy、PIL。值一律是 sRGB 0-255；Blender 材质、世界、灯光要线性值，用 linear(...)。
  2D（mograph/*.py、raw_overlay.py）：经 e2_common 取（e2_common 从本文件 re-export），或直接 `import e2_palette as P`
    （mograph 模块和本文件同目录，已在 sys.path 上）。
  3D（blender/scripts、blender/shots）：`import e2_common as E` 后用 E.P.<常量> / E.srgb_to_linear(...)；
    e2_common 会把本目录加到 sys.path，Blender 里也能 import。
  shared/blender/styles.py 是各期共用的，不 import 本文件；它的 BLUEPRINT_* 写的是本文件 SCHEMATIC_* 的线性值（见那边注释）。

规则：
  · 底色只有 BG_0 / BG_1 / SCHEMATIC_BG 三种（外加 BG_2 画网格和分隔）。不要再出现第 6 种黑。
  · 语义色只表达语义：通道蓝 = 光开 / 通道 / 激活；琥珀 = 关 / NpHR / 抑制；膜青 = 膜 / 标记细胞 / 环境甲；
    视黄醛紫 = 发色团 / 紫膜，只在 B 段和 A0_91、D_92；警示珊瑚只用于「未获批 / 无许可 / 限制」的章，每段 ≤ 2 处。
  · 组织暖色、纪实暖色只在 3D 组织和 L2 纸页上，不拿来画 2D 卡。
"""


def hexrgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def linear(c):
    """sRGB 0-255 三元组 -> 线性 0-1（Blender 用）。"""
    def f(v):
        v /= 255.0
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    return tuple(f(v) for v in c[:3])


def mix(a, b, k):
    k = max(0.0, min(1.0, k))
    return tuple(int(round(a[i] + (b[i] - a[i]) * k)) for i in range(3))


# ---- 底（全片唯一的「黑」和面板）-----------------------------------------------------------------
BG_0 = hexrgb("#070B14")            # 所有 2D 卡、energy / sem 的世界色；L1 暗棚渐变的底
BG_1 = hexrgb("#0E1626")            # 卡片 / HUD 面板填充；L1 暗棚渐变的顶
BG_2 = hexrgb("#1B2A44")            # 网格线、刻度、非活动元素

# ---- schematic（取代饱和蓝图蓝 #0C347A / #19427C）：与 BG_0 同色系，只更蓝一点 ----------------------
SCHEMATIC_BG = hexrgb("#0B1E3A")
SCHEMATIC_GRID = hexrgb("#1F3A63")
SCHEMATIC_LINE = hexrgb("#BFD6FF")

# ---- 字 / 线 ------------------------------------------------------------------------------------
INK_1 = hexrgb("#E8ECF4")           # 标题、正文、字幕
INK_2 = hexrgb("#9AA6BC")           # 标签、单位、分母；未动的细胞
INK_3 = hexrgb("#5B6780")           # 未激活、背景结构

# ---- 语义色 --------------------------------------------------------------------------------------
CHANNEL_CORE = hexrgb("#6F9BFF")    # 通道蓝（打开）核心
CHANNEL_GLOW = hexrgb("#8EAFFF")    # 通道蓝辉光；L1 冷轮廓光
CHANNEL_DEEP = hexrgb("#2F6FE0")    # 通道蓝深
AMBER = hexrgb("#FFB547")           # 抑制琥珀（关掉）
MEMBRANE = hexrgb("#4FD1B5")        # 膜青
RETINAL = hexrgb("#B784FF")         # 视黄醛紫（发色团、紫膜）
CORAL = hexrgb("#F2766B")           # 警示珊瑚：只用于「未获批 / 无许可 / 限制」

# ---- 组织暖色（只在 3D 生物体上，低饱和）---------------------------------------------------------
SCLERA = hexrgb("#D8D2C8")
CHOROID = hexrgb("#5A2A26")
RETINA = hexrgb("#C98E6E")
SKULL = hexrgb("#CFC6B4")
MOUSE = hexrgb("#B8B2AA")

# ---- L2 Document 暖（只在纸页、期刊、公告：A0_01a、A0_02b、B_13a、C_13a、D_03a）--------------------
PAPER = hexrgb("#D9CDB4")
DESK = hexrgb("#2A211A")
PRACTICAL_K = 3200                  # 实用光色温（K）

# ---- 笼子环境（取代 C_03a 的玫红）：两者明度相近，只靠色相区分 ------------------------------------------
ENV_A_FLOOR = hexrgb("#2E6F66")     # 环境甲（膜青降饱和）
ENV_B_FLOOR = hexrgb("#7A3F55")     # 环境乙（低饱和）

# ---- S SEM 点缀：冷灰，带约 5% 紫 ------------------------------------------------------------------
SEM_DARK = hexrgb("#0B0F18")
SEM_LIGHT = hexrgb("#C8D0DC")

# ---- 字幕底条（edit_film.subtitle）-----------------------------------------------------------------
SUB_INK = INK_1
SUB_BAR = (7, 11, 20)
SUB_BAR_ALPHA = 0.55

# ---- L1 暗棚世界（线性值，给 Blender set_world）：顶 BG_1 → 底 BG_0 ----------------------------------
L1_WORLD_TOP = linear(BG_1)
L1_WORLD_HORIZON = linear(mix(BG_1, BG_0, 0.5))
L1_WORLD_BOTTOM = linear(BG_0)
