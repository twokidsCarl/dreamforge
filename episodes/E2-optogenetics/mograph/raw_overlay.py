"""E2 raw: true 镜头叠字后处理的共用件（Pillow）：读 Blender 帧、复现 Blender 相机、画中文标签。

本文件不注册镜头（mograph.load_shots 会执行它，但这里没有 @shot）。b.py、c.py 从这里取；a0.py 的 A0_04a 仍用自己那份。
标签的颜色跟着底图风格：energy / sem 是暗底，用线稿白字 + 半透明黑衬底；blueprint 是深蓝底，用蓝图白字 + 蓝底衬底。
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "blender", "scripts"))

import e2_common as E  # noqa: E402
from mograph import RENDERS  # noqa: E402
from overlay_labels import font  # noqa: E402

FPS = 24

# 衬底配色：(字, 衬底, 衬底不透明度 0-255, 边线)
DARK = (E.LINE, (8, 10, 16), 170, E.GREY)
BLUEPRINT = ((222, 236, 255), (12, 52, 122), 215, (222, 236, 255))   # 与 a0.py 的 BP_LINE / BP_BG 同


def raw_frame(sid, f, W):
    q = {640: "preview", 960: "sample", 1920: "final"}[W]
    p = os.path.join(RENDERS, "shots", sid, q + "_raw", f"{f:04d}.png")
    if not os.path.exists(p):
        raise FileNotFoundError(f"{p} 不存在：先渲 {sid}（registry 里 raw: true，写到 {q}_raw）")
    return Image.open(p).convert("RGB")


def frame_of(t, dur):
    """(t, dur) → (镜头内帧号 f（1 起）, 帧数 n, 比例 u)。u 与场景模块里 _f(sid, frac) 同一套。"""
    n = max(1, round(dur * FPS))
    f = int(round(t * FPS)) + 1
    return f, n, (f - 1) / max(1, n - 1)


def _lerp(a, b, s):
    return tuple(a[i] + (b[i] - a[i]) * s for i in range(3))


def dolly(f, n, aim0, loc0, loc1, aim1=None):
    """e2_shot.camera 的两个关键帧（第 1 帧、第 n 帧；Blender 默认贝塞尔，端点切线水平 = smoothstep）→ 第 f 帧的 (loc, aim)。"""
    u = min(1.0, max(0.0, (f - 1) / max(1, n - 1)))
    s = u * u * (3 - 2 * u)
    return _lerp(loc0, loc1, s), _lerp(aim0, aim1 or aim0, s)


def tag(img, text, xy, k, pal=DARK, a=1.0, anchor="mm", size=44, edge=None, halo=None):
    """在 img（RGB）上画一个中文标签，返回新图。

    xy：字的位置（画面像素，anchor 照 Pillow）；k = H/1080；a：标签不透明度；edge：边线颜色（默认照 pal）。
    halo：可选，衬底后面一圈很淡的光（颜色），和场景里的光晕呼应。
    """
    if a <= 0:
        return img
    ink, pill, fill_a, edge0 = pal
    edge = edge or edge0
    fn = font(int(size * k))
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    x0, y0, x1, y1 = d.textbbox(xy, text, font=fn, anchor=anchor)
    pad = 14 * k
    box = (x0 - pad, y0 - pad * 0.7, x1 + pad, y1 + pad * 0.7)
    lw = max(1, round(3 * k))
    d.rounded_rectangle(box, radius=10 * k, fill=(*pill, int(fill_a * a)), outline=(*edge, int(200 * a)), width=lw)
    d.text(xy, text, font=fn, fill=(*ink, int(255 * a)), anchor=anchor)
    out = img.convert("RGBA")
    if halo is not None:
        h = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ImageDraw.Draw(h).rounded_rectangle(box, radius=10 * k, fill=(*halo, int(110 * a)))
        out = Image.alpha_composite(out, h.filter(ImageFilter.GaussianBlur(14 * k)))
    return Image.alpha_composite(out, layer).convert("RGB")
