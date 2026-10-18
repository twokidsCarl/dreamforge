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
FONT = "/System/Library/Fonts/STHeiti Medium.ttc"
FONT_INDEX = 1  # Heiti SC
FADE = 8        # frames
ACCENT = (150, 120, 255)


def font(px):
    return ImageFont.truetype(FONT, px, index=FONT_INDEX)


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
    heights = [d.textbbox((0, 0), t or " ", font=fo)[3] for t, fo, _ in lines]
    gap = int(8 * s)
    block_h = sum(heights) + gap * (len(lines) - 1)
    widths = [d.textlength(t, font=fo) for t, fo, _ in lines]
    if lab["pos"] == "upper_right":
        x0, y0 = W - m - max(widths), m + int(24 * s)
    else:
        x0, y0 = m + int(10 * s), H - m - block_h - int(24 * s)
    scrim(layer, (x0 - int(12 * s), y0, x0 + max(widths), y0 + block_h), a, s)
    # accent bar slides in with the fade
    bar_x = x0 - int(12 * s)
    d.rectangle([bar_x, y0 + 2, bar_x + max(2, int(3 * s)), y0 + int(block_h * a)],
                fill=(*ACCENT, int(255 * a)))
    y = y0
    for (t, fo, col), h in zip(lines, heights):
        if t:
            d.text((x0 + 1, y + 1), t, font=fo, fill=(0, 0, 0, int(140 * a)))
            d.text((x0, y), t, font=fo, fill=(*col, int(255 * a)))
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
