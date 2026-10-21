"""E2 C 段（第三幕）的 2D 镜头和 Blender raw 帧的叠字后处理（Pillow）。

C_07a：视网膜剖面（c_scenes.retina phase=rp，xray 浅灰底）+「可转导」。只标神经节细胞（F11：感光细胞死去、神经节细胞留着；
builder 里通道装在神经节细胞上），不写疗效、不写视力数字。字在神经节细胞套上蓝色光晕之后进来，位置跟着锚点
LabelAnchor_Transducible 投影（与 Blender 相机同一套数学，e2_common.project_point）。
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "blender", "scripts"))

import build_retina as BR  # noqa: E402
import e2_common as E  # noqa: E402
from mograph import RENDERS, ease, seg, shot  # noqa: E402
from overlay_labels import font  # noqa: E402

FPS = 24


def _raw_frame(sid, f, W):
    q = {640: "preview", 960: "sample", 1920: "final"}[W]
    p = os.path.join(RENDERS, "shots", sid, q + "_raw", f"{f:04d}.png")
    if not os.path.exists(p):
        raise FileNotFoundError(f"{p} 不存在：先渲 {sid}（registry 里 raw: true，写到 {q}_raw）")
    return Image.open(p).convert("RGB")


def _lerp(a, b, s):
    return tuple(a[i] + (b[i] - a[i]) * s for i in range(3))


def _dolly(f, n, aim0, loc0, loc1, aim1):
    """e2_shot.dolly 的两个关键帧（Blender 默认贝塞尔，端点切线水平 = smoothstep）→ 第 f 帧的 (loc, aim)。"""
    u = min(1.0, max(0.0, (f - 1) / max(1, n - 1)))
    s = u * u * (3 - 2 * u)
    return _lerp(loc0, loc1, s), _lerp(aim0, aim1, s)


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
    base = _raw_frame("C_07a", f, W).resize((W, H), Image.LANCZOS)
    u = (f - 1) / max(1, n - 1)                        # 与 c_scenes._f 同一套比例
    lead = ease(seg(u, 0.64, 0.70))
    a = ease(seg(u, 0.66, 0.76))
    if lead <= 0:
        return base
    k = H / 1080
    loc, aim = _dolly(f, n, (0.0, 0.0, 1.22), (-0.3, -9.4, 1.9), (0.6, -6.6, 1.4), (0.4, 0.0, 1.05))
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
