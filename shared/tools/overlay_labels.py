"""Composite on-screen labels onto rendered frames and encode an H.264 preview.

  python3 tools/overlay_labels.py --shot sample_b1 --engine cycles

Reads  renders/<shot>/<engine>/frames/####.png and episodes/<episode>/blender/shots/<shot>.labels.json,
writes renders/<shot>/<engine>/labeled/####.png and renders/<shot>/<shot>_<engine>.mp4.
Labels live in post (not in the 3D scene) so wording can change without re-rendering.
"""
import argparse
import json
import os
import subprocess

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from paths import AUDIO, EP, REPO, RENDERS, SHARED  # noqa: E402,F401
from richtext import draw_text, text_bbox, text_length  # noqa: E402  (Sn⁸⁺, H₂: the CJK faces lack these glyphs)
MAC_FONT = "/System/Library/Fonts/STHeiti Medium.ttc"
NOTO_DIR = "/usr/share/fonts/opentype/noto"
# 优先 macOS 的 Heiti（保持 mac 上的原有表现）；没有时退回 Noto Sans CJK SC。
# .ttc 里各语言字面的顺序是 JP, KR, SC, TC, HK，所以 SC 的 index 是 2（用 PIL 比对过字形）。
if os.path.exists(MAC_FONT):
    FONT, FONT_INDEX = MAC_FONT, 1  # Heiti SC
else:
    FONT = next((os.path.join(NOTO_DIR, n) for n in
                 ("NotoSansCJK-Medium.ttc", "NotoSansCJK-Regular.ttc", "NotoSansCJK-Bold.ttc")
                 if os.path.exists(os.path.join(NOTO_DIR, n))), MAC_FONT)
    FONT_INDEX = 2  # Noto Sans CJK SC
SERIF = os.path.join(NOTO_DIR, "NotoSerifCJK-Regular.ttc")   # 宋体感；没有时 serif_font() 退回黑体
MONO = next((p for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
                         "/System/Library/Fonts/Menlo.ttc", "/System/Library/Fonts/Monaco.ttf")
             if os.path.exists(p)), None)
FADE = 8        # frames
ACCENT = (150, 120, 255)


def font(px):
    return ImageFont.truetype(FONT, px, index=FONT_INDEX)


def serif_font(px):
    """排版镜头用的衬线体（Noto Serif CJK SC）；mac 上没有就退回黑体。"""
    if os.path.exists(SERIF):
        return ImageFont.truetype(SERIF, px, index=2)
    return font(px)


def mono_font(px):
    """等宽数字（HUD 计数器）；找不到系统等宽字体就退回黑体。"""
    return ImageFont.truetype(MONO, px) if MONO else font(px)


def alpha_at(f, start, end):
    if f < start or f > end:
        return 0.0
    return max(0.0, min(1.0, (f - start) / FADE, (end - f) / FADE))


def scrim(layer, box, a, s):
    """Soft dark backing behind text so captions stay legible over bright footage."""
    pad = int(26 * s)
    sh = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle(
        [box[0] - pad, box[1] - pad, box[2] + pad, box[3] + pad], radius=int(20 * s),
        fill=(4, 7, 14, int(165 * a)))
    layer.alpha_composite(sh.filter(ImageFilter.GaussianBlur(int(18 * s))))


def draw_label(layer, lab, a, W, H):
    d = ImageDraw.Draw(layer)
    s = H / 540
    f_main, f_sub, f_src = font(int(26 * s)), font(int(16 * s)), font(int(12 * s))
    m = int(36 * s)
    lines = [(lab["text"], f_main, (255, 255, 255)),
             (lab.get("sub", ""), f_sub, (205, 212, 230)),
             (("来源：" + lab["source"]) if lab.get("source") else "", f_src, (140, 148, 170))]
    heights = [text_bbox(d, (0, 0), t or " ", fo)[3] for t, fo, _ in lines]
    gap = int(8 * s)
    block_h = sum(heights) + gap * (len(lines) - 1)
    widths = [text_length(d, t, fo) for t, fo, _ in lines]
    if lab["pos"] == "upper_right":
        x0, y0 = W - m - max(widths), m + int(24 * s)
    else:
        x0, y0 = m + int(10 * s), H - m - block_h - int(24 * s)
    scrim(layer, (x0 - int(12 * s), y0, x0 + max(widths), y0 + block_h), a, s)
    # accent bar slides in with the fade
    bar_x = x0 - int(12 * s)
    d.rectangle([bar_x, y0 + 2, bar_x + max(2, int(3 * s)), max(y0 + 2, y0 + int(block_h * a))],
                fill=(*ACCENT, int(255 * a)))
    y = y0
    for (t, fo, col), h in zip(lines, heights):
        if t:
            draw_text(d, (x0 + 1, y + 1), t, fo, fill=(0, 0, 0, int(140 * a)))
            draw_text(d, (x0, y), t, fo, fill=(*col, int(255 * a)))
        y += h + gap


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shot", required=True)
    ap.add_argument("--engine", default="cycles")
    ap.add_argument("--fps", type=int, default=24)
    a = ap.parse_args()
    root = RENDERS
    src = os.path.join(root, a.shot, a.engine, "frames")
    dst = os.path.join(root, a.shot, a.engine, "labeled")
    os.makedirs(dst, exist_ok=True)
    spec = json.load(open(os.path.join(EP, "blender/shots", a.shot + ".labels.json")))

    frames = sorted(n for n in os.listdir(src) if n.endswith(".png"))
    for name in frames:
        f = int(name[:4])
        im = Image.open(os.path.join(src, name)).convert("RGBA")
        W, H = im.size
        s = H / 540
        layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        m = int(36 * s)
        d.text((m, m - int(8 * s)), spec["title"], font=font(int(14 * s)), fill=(190, 198, 220, 200))
        tag_font = font(int(13 * s))
        tw = d.textlength(spec["tag"], font=tag_font)
        d.text((W - m - tw, H - m), spec["tag"], font=tag_font, fill=(170, 176, 196, 190))
        for lab in spec["labels"]:
            al = alpha_at(f, lab["start"], lab["end"])
            if al > 0:
                draw_label(layer, lab, al, W, H)
        Image.alpha_composite(im, layer).convert("RGB").save(os.path.join(dst, name))

    out = os.path.join(root, a.shot, f"{a.shot}_{a.engine}.mp4")
    first = int(frames[0][:4])
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(a.fps),
                    "-start_number", str(first), "-i", os.path.join(dst, "%04d.png"),
                    "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p",
                    "-movflags", "+faststart", out], check=True)
    print(out)


if __name__ == "__main__":
    main()
