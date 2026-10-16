"""Story reel: one board per shot, timed to the real narration, with subtitles and timecode.

  python3 tools/story_reel.py [--voice Andre] [--size 1280x720]

Uses storyboard.timed.yaml (tools/retime.py) and the VO track. Boards are drawn with Pillow:
style swatch and name, shot id, timecode, the visual description, planned on-screen text and the
current subtitle. Where a rendered frame exists for a shot (shots that reuse the B1 sample
cameras), the board shows it instead of text. As grey-box renders arrive, put them under
renders/reel/<shot_id>.png (or .mp4) and they replace the board automatically.
Output: renders/reel/story_reel.mp4
"""
import argparse
import os
import subprocess
import sys

import yaml
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(__file__))
from overlay_labels import font  # noqa: E402
from zh_terms import TRANSITIONS  # noqa: E402

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RENDERS = os.environ.get("DREAMFORGE_RENDER_DIR", os.path.join(REPO, "renders"))
FPS = 24
STYLE = {  # name, background tint, accent
    "photoreal": ("真实渲染", (14, 18, 26), (140, 156, 180)), "xray": ("透明剖视", (196, 200, 208), (90, 100, 120)),
    "blueprint": ("蓝图", (10, 40, 110), (220, 235, 255)), "energy": ("能量图", (4, 3, 10), (150, 110, 255)),
    "infographic": ("平面信息图", (12, 22, 30), (40, 190, 210)), "clay": ("白模", (208, 204, 196), (110, 104, 96)),
    "sem": ("显微成像", (34, 34, 34), (200, 200, 200)), "hud": ("HUD 遥测", (8, 20, 18), (40, 210, 160)),
    "type": ("动态排版", (6, 7, 12), (235, 238, 245)), "documentary": ("纪实氛围", (24, 18, 10), (230, 170, 70)),
}
SAMPLE = {  # sample_b1 camera -> preferred raw (uncaptioned) frame; falls back to any rendered frame
    "CamEstablish": "0030", "CamNozzle": "0060", "CamPrePulse": "0104", "CamSheet": "0160",
    "CamPlasma": "0230", "CamReveal": "0320",
}


def sample_frame(cam):
    d = os.path.join(RENDERS, "sample_b1", "cycles", cam)
    if not os.path.isdir(d):
        return None
    want = os.path.join(d, f"{SAMPLE.get(cam, '')}.png")
    if os.path.exists(want):
        return want
    frames = sorted(f for f in os.listdir(d) if f.endswith(".png"))
    return os.path.join(d, frames[len(frames) // 2]) if frames else None


def wrap_px(d, text, f, width):
    """Wrap mixed CJK/Latin text by measured pixel width (keeps Latin words intact)."""
    import re
    tokens = re.findall(r"[A-Za-z0-9.+\-–/%°μ₁·×]+|\s+|.", text)
    lines, cur = [], ""
    for tk in tokens:
        if d.textlength(cur + tk, font=f) > width and cur.strip():
            lines.append(cur.rstrip())
            cur = tk.lstrip()
        else:
            cur += tk
    if cur.strip():
        lines.append(cur.rstrip())
    return lines


def tc(t):
    return f"{int(t // 60):02d}:{t % 60:05.2f}"


def board(s, W, H, seg_title):
    name, bg, acc = STYLE[s["style"]]
    light = sum(bg) > 400
    ink = (20, 22, 28) if light else (236, 238, 244)
    ink2 = (70, 74, 86) if light else (160, 166, 182)
    k = H / 720
    ref = s.get("ref", "")
    still = None
    if ref.startswith("sample_b1:"):
        p = sample_frame(ref.split(":")[1])
        if p:
            still = Image.open(p).convert("RGB").resize((W, H), Image.LANCZOS)
    own = os.path.join(RENDERS, "reel", f"{s['id']}.png")
    if os.path.exists(own):
        still = Image.open(own).convert("RGB").resize((W, H), Image.LANCZOS)
    img = still if still else Image.new("RGB", (W, H), bg)
    d = ImageDraw.Draw(img, "RGBA")
    m = int(48 * k)
    head = f"{s['id']}  ·  {seg_title}  ·  转场：{TRANSITIONS.get(s.get('transition_in'), s.get('transition_in'))}"
    if still:
        d.rectangle([0, 0, W, int(110 * k)], fill=(0, 0, 0, 120))
        ink, ink2 = (240, 242, 248), (210, 214, 226)
        head += "  （B1 样片画面）"
    # header: style swatch + name, shot id, segment title, transition
    d.rectangle([m, m, m + int(14 * k), m + int(14 * k)], fill=acc)
    d.text((m + int(24 * k), m - int(5 * k)), name, font=font(int(20 * k)), fill=ink)
    d.text((m, m + int(30 * k)), head, font=font(int(15 * k)), fill=ink2)
    if not still:
        y = m + int(90 * k)
        fv = font(int(25 * k))
        for para in wrap_px(d, s.get("visual", ""), fv, W - 2 * m):
            d.text((m, y), para, font=fv, fill=ink)
            y += int(38 * k)
            if y > H * 0.66:
                d.text((m, y), "……", font=font(int(25 * k)), fill=ink2)
                break
        ovs = [o.get("text", "") for o in s.get("overlays") or [] if o.get("kind") != "chapter"]
        if ovs:
            y = max(y + int(16 * k), int(H * 0.62))
            d.text((m, y), "上屏：" + " ｜ ".join(ovs)[:70], font=font(int(17 * k)), fill=acc)
    return img


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--voice", default="Andre")
    ap.add_argument("--size", default="1280x720")
    a = ap.parse_args()
    W, H = (int(x) for x in a.size.split("x"))
    sb = yaml.safe_load(open(os.path.join(REPO, "projects/euv/storyboard/storyboard.timed.yaml"), encoding="utf-8"))
    sys.path.insert(0, os.path.dirname(__file__))
    from lint_script import parse
    titles = {x["id"]: x["title"] for x in parse(os.path.join(REPO, "projects/euv/script/script_zh.md"))}
    out = os.path.join(RENDERS, "reel")
    os.makedirs(os.path.join(out, "boards"), exist_ok=True)
    total = sb["timing"]["total"]
    k = H / 720
    lst = []
    for s in sb["shots"]:
        base = board(s, W, H, titles.get(s["segment"], ""))
        # one frame per subtitle state inside the shot (no cue / each cue)
        marks = [0.0] + [c["start"] for c in s.get("cues", [])] + [c["end"] for c in s.get("cues", [])] + [s["duration"]]
        marks = sorted(set(round(x, 3) for x in marks if 0 <= x <= s["duration"]))
        for i in range(len(marks) - 1):
            t0, t1 = marks[i], marks[i + 1]
            if t1 - t0 < 1 / FPS:
                continue
            img = base.copy()
            d = ImageDraw.Draw(img, "RGBA")
            cue = next((c for c in s.get("cues", []) if c["start"] <= t0 + 1e-3 < c["end"]), None)
            if cue:
                f = font(int(28 * k))
                tw = d.textlength(cue["text"], font=f)
                lines = [cue["text"]] if tw < W * 0.86 else wrap_px(d, cue["text"], f, W * 0.8)
                y = H - int(110 * k) - (len(lines) - 1) * int(40 * k)
                for ln in lines:
                    lw = d.textlength(ln, font=f)
                    d.rectangle([(W - lw) / 2 - 12 * k, y - 4 * k, (W + lw) / 2 + 12 * k, y + 38 * k], fill=(0, 0, 0, 150))
                    d.text(((W - lw) / 2, y), ln, font=f, fill=(255, 255, 255))
                    y += int(40 * k)
            gt = s["start"] + t0
            d.rectangle([0, H - int(6 * k), int(W * gt / total), H], fill=(150, 110, 255))
            d.text((W - int(180 * k), H - int(40 * k)), tc(gt), font=font(int(16 * k)), fill=(200, 204, 216))
            p = os.path.join(out, "boards", f"{s['id']}_{i:02d}.png")
            img.save(p)
            lst.append((p, t1 - t0))
    with open(os.path.join(out, "boards.txt"), "w") as fh:
        for p, dur in lst:
            fh.write(f"file '{p}'\nduration {dur:.4f}\n")
        fh.write(f"file '{lst[-1][0]}'\n")
    vo = os.path.join(REPO, "audio", "vo", a.voice, "vo_track.wav")
    mp4 = os.path.join(out, "story_reel.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i",
                    os.path.join(out, "boards.txt"), "-i", vo, "-vf", f"fps={FPS},format=yuv420p",
                    "-c:v", "libx264", "-preset", "medium", "-crf", "22", "-c:a", "aac", "-b:a", "160k",
                    "-shortest", "-movflags", "+faststart", mp4], check=True)
    print(mp4, f"{len(lst)} boards, {total / 60:.2f} min")


if __name__ == "__main__":
    main()
