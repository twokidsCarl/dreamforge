"""Story reel: one board per shot, timed to the real narration, with subtitles and timecode.

  python3 tools/story_reel.py [--voice Andre] [--size 1280x720]

Uses storyboard.timed.yaml (tools/retime.py) and the VO track. Boards are drawn with Pillow:
style swatch and name, shot id, timecode, the visual description, planned on-screen text and the
current subtitle. Where a rendered frame exists for a shot, the board shows it
instead of text. A frame taken from the lithography sample_b1 cameras is marked
「B1 样片画面」; the episode's own reel still is not. As grey-box renders arrive,
put them under renders/reel/<shot_id>.png (or .mp4) and they replace the board.
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

from paths import AUDIO, EP, REPO, RENDERS, SHARED  # noqa: E402,F401
RENDERS = RENDERS
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


def is_black(s):
    """Shots that end on a black frame: the light goes out (灭) into 黑场, e.g. E2 D_04b. A shot that merely
    starts from black and shows a title (黑场中央只有片名…) is not one."""
    v = s.get("visual") or ""
    return "黑场" in v and "灭" in v


def board(s, W, H, seg_title):
    name, bg, acc = STYLE[s["style"]]
    light = sum(bg) > 400
    ink = (20, 22, 28) if light else (236, 238, 244)
    ink2 = (70, 74, 86) if light else (160, 166, 182)
    k = H / 720
    ref = s.get("ref", "")
    still = None
    from_sample = False
    if ref.startswith("sample_b1:"):
        p = sample_frame(ref.split(":")[1])
        if p:
            still = Image.open(p).convert("RGB").resize((W, H), Image.LANCZOS)
            from_sample = True
    own = os.path.join(RENDERS, "reel", f"{s['id']}.png")
    if os.path.exists(own):
        still = Image.open(own).convert("RGB").resize((W, H), Image.LANCZOS)
        from_sample = False
    img = still if still else Image.new("RGB", (W, H), bg)
    d = ImageDraw.Draw(img, "RGBA")
    m = int(48 * k)
    kf = max(k, 0.8)    # text never shrinks below a readable size on small previews (640x360)
    head = f"{seg_title}  ·  转场：{TRANSITIONS.get(s.get('transition_in'), s.get('transition_in'))}"
    if still:
        d.rectangle([0, 0, W, int(110 * k)], fill=(0, 0, 0, 120))
        ink, ink2 = (240, 242, 248), (210, 214, 226)
        if from_sample:
            head += "  （B1 样片画面）"
    if not still and is_black(s):
        # an intentional black frame stays black; only a small id so the reviewer knows where they are
        d.text((m, m), f"{s['id']}  黑场", font=font(int(16 * kf)), fill=(90, 92, 100))
        return img
    # header: style swatch + name, then the shot id large on the right, segment title and transition below
    d.rectangle([m, m, m + int(14 * kf), m + int(14 * kf)], fill=acc)
    d.text((m + int(24 * kf), m - int(5 * kf)), name, font=font(int(20 * kf)), fill=ink)
    fid = font(int(30 * kf))
    d.text((W - m - d.textlength(s["id"], font=fid), m - int(10 * kf)), s["id"], font=fid, fill=acc)
    d.text((m, m + int(26 * kf)), head, font=font(int(14 * kf)), fill=ink2)
    if not still:
        # the picture area: a framed placeholder where the render will go, never an empty field
        x0, y0, x1, y1 = m, m + int(54 * kf), W - m, int(H * 0.75)
        tint = tuple(min(255, c + 14) for c in bg) if not light else tuple(max(0, c - 14) for c in bg)
        d.rectangle([x0, y0, x1, y1], fill=tint, outline=acc + (150,), width=max(1, int(2 * k)))
        for i in (1, 2):                                  # thirds guides
            gx = x0 + (x1 - x0) * i // 3
            gy = y0 + (y1 - y0) * i // 3
            d.line([gx, y0, gx, y1], fill=acc + (40,), width=1)
            d.line([x0, gy, x1, gy], fill=acc + (40,), width=1)
        pad = int(16 * kf)
        cam = (s.get("camera") or {}).get("move", "")
        tag = f"画面待做 · {s.get('engine', '')} · {cam} · {s['duration']:.2f}s" + ("" if s.get("vo") else " · 纯画面")
        ft = font(int(13 * kf))
        d.text((x1 - pad - d.textlength(tag, font=ft), y1 - pad - int(14 * kf)), tag, font=ft, fill=ink2)
        fv = font(int(24 * kf))
        lines = wrap_px(d, s.get("visual", ""), fv, x1 - x0 - 2 * pad)
        lh = int(34 * kf)
        room = (y1 - y0 - 2 * pad - int(22 * kf)) // lh
        ovs = [o.get("text", "") for o in s.get("overlays") or [] if o.get("kind") != "chapter"]
        if ovs:
            room -= 1
        if len(lines) > room:
            lines = lines[:max(1, room - 1)] + ["……"]
        block = len(lines) * lh + (lh if ovs else 0)
        y = y0 + max(pad, (y1 - y0 - int(22 * kf) - block) // 2)
        for ln in lines:
            d.text((x0 + (x1 - x0 - d.textlength(ln, font=fv)) / 2, y), ln, font=fv, fill=ink)
            y += lh
        if ovs:
            fo = font(int(17 * kf))
            t = ("上屏：" + " ｜ ".join(ovs))[:60]
            d.text((x0 + (x1 - x0 - d.textlength(t, font=fo)) / 2, y + int(4 * kf)), t, font=fo, fill=acc)
    return img


def draw_sub(img, s, t0, W, H, total, k):
    d = ImageDraw.Draw(img, "RGBA")
    cue = next((c for c in s.get("subs", []) if c["start"] <= t0 + 1e-3 < c["end"]), None)
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
    return img


def rendered_frames(sid, quality_order=("final", "sample", "preview")):
    for q in quality_order:
        d = os.path.join(RENDERS, "shots", sid, q)
        if os.path.isdir(d):
            fr = sorted(f for f in os.listdir(d) if f.endswith(".png"))
            if fr:
                return d, fr, q
    return None, [], None


def mograph_ids():
    """Shots drawn by mograph/*.py carry their own on-frame text; no extra label for them."""
    import glob
    import re
    ids = set()
    for p in glob.glob(os.path.join(EP, "mograph", "*.py")):
        ids |= set(re.findall(r'@shot\("([A-Za-z0-9_]+)"\)', open(p, encoding="utf-8").read()))
    return ids


MOGRAPH = None


ORGS = [("asml", "ASML"), ("zeiss", "ZEISS"), ("trumpf", "TRUMPF"), ("intel", "Intel"), ("imec", "imec"),
        ("nature.com", "Nature"), ("iop", "IOP"), ("arcnl", "ARCNL"), ("nist", "NIST"), ("euvlitho", "EUVL 研讨会"),
        ("spie", "SPIE"), ("ieee", "IEEE"), ("nvidia", "NVIDIA"), ("technologyreview", "MIT Tech Review"),
        ("illinois", "伊利诺伊大学"), ("patents.google", "ASML 专利")]
_FACTS = None


def fact_orgs(ids):
    """Who said it, for the on-screen label: organisation names from the facts' source URLs."""
    global _FACTS
    if _FACTS is None:
        _FACTS = yaml.safe_load(open(os.path.join(EP, "research/facts.yaml"), encoding="utf-8")) or {}
    names = []
    for f in ids:
        for url in (_FACTS.get(f) or {}).get("sources") or []:
            for key, name in ORGS:
                if key in url and name not in names:
                    names.append(name)
    return " · ".join(names[:3])


def label_layer(s, W, H, k, a=1.0):
    """On-screen labels planned for the shot (non-chapter), stacked bottom-left above subtitles."""
    from overlay_labels import draw_label
    global MOGRAPH
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if MOGRAPH is None:
        MOGRAPH = mograph_ids()
    ovs = [o for o in s.get("overlays") or [] if o.get("kind") != "chapter"]
    if not ovs or s["id"] in MOGRAPH or s.get("style") == "type":     # text already drawn in frame
        return layer
    # sub/superscripts are typeset by overlay_labels.draw_label via richtext
    lab = {"text": ovs[0]["text"], "sub": " ｜ ".join(o["text"] for o in ovs[1:3]),
           "source": fact_orgs(sorted({f for o in ovs for f in o.get("facts") or []})),
           "facts": [],
           "pos": "upper_right"}
    draw_label(layer, lab, a, W, H)
    return layer


def build_clip(s, W, H, total, k, title, out):
    """One mp4 per shot; rebuilt only when its inputs are newer than the clip."""
    clip = os.path.join(out, "clips", f"{s['id']}.mp4")
    fdir, frames, q = rendered_frames(s["id"])
    n = max(1, round(s["duration"] * FPS))
    stamp = max([os.path.getmtime(os.path.join(fdir, f)) for f in frames] if frames else [0]
                + [os.path.getmtime(os.path.join(EP, "storyboard/storyboard.timed.yaml"))])
    if os.path.exists(clip) and os.path.getmtime(clip) > stamp:
        return clip
    tmp = os.path.join(out, "tmp", s["id"])
    os.makedirs(tmp, exist_ok=True)
    for f in os.listdir(tmp):
        os.remove(os.path.join(tmp, f))
    if frames:
        name, _, acc = STYLE[s["style"]]
        labels = label_layer(s, W, H, k)
        for i in range(n):
            src = frames[min(i, len(frames) - 1)] if len(frames) > 1 else frames[0]
            img = Image.open(os.path.join(fdir, src)).convert("RGB").resize((W, H), Image.LANCZOS)
            img = Image.alpha_composite(img.convert("RGBA"), labels).convert("RGB")
            d = ImageDraw.Draw(img, "RGBA")
            m = int(36 * k)
            d.rectangle([m, m, m + int(12 * k), m + int(12 * k)], fill=acc)
            d.text((m + int(20 * k), m - int(6 * k)), f"{s['id']} · {name} · {q}", font=font(int(15 * k)),
                   fill=(230, 232, 240))
            draw_sub(img, s, i / FPS, W, H, total, k).save(os.path.join(tmp, f"{i + 1:05d}.png"))
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", os.path.join(tmp, "%05d.png")]
    else:
        base = board(s, W, H, title)
        subs = s.get("subs", [])
        marks = sorted(set(round(x, 3) for x in [0.0, s["duration"]] + [c["start"] for c in subs]
                           + [c["end"] for c in subs] if 0 <= x <= s["duration"]))
        lst = os.path.join(tmp, "list.txt")
        with open(lst, "w") as fh:
            last = None
            for i in range(len(marks) - 1):
                t0, t1 = marks[i], marks[i + 1]
                if t1 - t0 < 1 / FPS:
                    continue
                p = os.path.join(tmp, f"b{i:02d}.png")
                draw_sub(base.copy(), s, t0, W, H, total, k).save(p)
                fh.write(f"file '{p}'\nduration {t1 - t0:.4f}\n")
                last = p
            fh.write(f"file '{last}'\n")
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst]
    os.makedirs(os.path.dirname(clip), exist_ok=True)
    subprocess.run(cmd + ["-vf", f"fps={FPS},format=yuv420p", "-frames:v", str(n), "-c:v", "libx264",
                          "-preset", "veryfast", "-crf", "20", clip], check=True)
    return clip


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--voice", default="Andre")
    ap.add_argument("--size", default="1280x720")
    a = ap.parse_args()
    W, H = (int(x) for x in a.size.split("x"))
    sb = yaml.safe_load(open(os.path.join(EP, "storyboard/storyboard.timed.yaml"), encoding="utf-8"))
    from lint_script import parse
    titles = {x["id"]: x["title"] for x in parse(os.path.join(EP, "script/script_zh.md"))}
    out = os.path.join(RENDERS, "reel")
    total = sb["timing"]["total"]
    k = H / 720
    clips, rendered = [], 0
    for s in sb["shots"]:
        clips.append(build_clip(s, W, H, total, k, titles.get(s["segment"], ""), out))
        rendered += bool(rendered_frames(s["id"])[1])
    lst = os.path.join(out, "clips.txt")
    with open(lst, "w") as fh:
        fh.writelines(f"file '{c}'\n" for c in clips)
    vo = os.path.join(AUDIO, "vo", a.voice, "vo_track.wav")
    mp4 = os.path.join(out, "story_reel.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-i", vo,
                    "-c:v", "copy", "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "160k",
                    "-shortest", "-movflags", "+faststart", mp4], check=True)
    print(mp4, f"{len(clips)} shots ({rendered} rendered), {total / 60:.2f} min")


if __name__ == "__main__":
    main()
