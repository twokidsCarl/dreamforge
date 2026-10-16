"""Cut a multi-camera shot into a finished clip: transitions, captions, grade, sound.

  python3 tools/edit_sample.py --shot sample_b1 [--engine cycles] [--no-audio]

Reads the rendered cuts in renders/<shot>/<engine>/<Cam>/####.png and the edit decision list
episodes/<episode>/blender/shots/<shot>.edit.json; writes renders/<shot>/edit/####.png and
renders/<shot>/<shot>_final.mp4. Sound is synthesised placeholder design (ffmpeg lavfi).
"""
import argparse
import json
import os
import subprocess

import numpy as np
from PIL import Image, ImageDraw

from overlay_labels import ACCENT, alpha_at, draw_label, font, scrim

from paths import AUDIO, EP, REPO, RENDERS, SHARED  # noqa: E402,F401


def build_timeline(edl, src):
    """Return (frames, clip_start, scene_to_edit): frames[t] = [(path, weight), ...]."""
    frames, clip_start = [], {}
    for i, c in enumerate(edl["clips"]):
        paths = [os.path.join(src, c["cut"], f"{f:04d}.png") for f in range(c["in"], c["out"] + 1)]
        overlap = c.get("frames", 0) if (i and c["transition"] == "dissolve") else 0
        start = len(frames) - overlap
        clip_start[c["cut"]] = start
        for k, p in enumerate(paths):
            t = start + k
            if k < overlap:
                w = (k + 1) / (overlap + 1)
                frames[t] = [(q, wq * (1 - w)) for q, wq in frames[t]] + [(p, w)]
            else:
                frames.append([(p, 1.0)])
    return frames, clip_start


def compose(layers):
    acc = None
    for p, w in layers:
        a = np.asarray(Image.open(p).convert("RGB"), dtype=np.float32) * w
        acc = a if acc is None else acc + a
    return acc


def draw_title(layer, title, a, W, H):
    d = ImageDraw.Draw(layer)
    s = H / 540
    big, sub, src = font(int(54 * s)), font(int(20 * s)), font(int(12 * s))
    cx, cy = W // 2, int(H * 0.42)
    tw = d.textlength(title["text"], font=big)
    scrim(layer, (cx - max(tw, 220 * s) / 2 - 40 * s, cy, cx + max(tw, 220 * s) / 2 + 40 * s, cy + 100 * s), a, s)
    for txt, fo, col, dy in ((title["text"], big, (255, 255, 255), 0),
                             (title["sub"], sub, (214, 220, 238), int(52 * s)),
                             ("（" + title["source"] + " · " + "、".join(title["facts"]) + "）", src,
                              (150, 158, 182), int(84 * s))):
        w = d.textlength(txt, font=fo)
        d.text((cx - w / 2 + 2, cy + dy + 2), txt, font=fo, fill=(0, 0, 0, int(120 * a)))
        d.text((cx - w / 2, cy + dy), txt, font=fo, fill=(*col, int(255 * a)))
    lw = int(120 * s * a)
    y = cy + int(44 * s)
    d.rectangle([cx - lw // 2, y, cx + lw // 2, y + max(1, int(2 * s))], fill=(*ACCENT, int(255 * a)))


def render_frames(edl, frames, clip_start, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    W, H = edl["size"]
    n = len(frames)
    flashes = {}
    for c in edl["clips"]:
        if "flash_at" in c:
            t0 = clip_start[c["cut"]] + c["flash_at"] - c["in"]
            for k, v in enumerate((0.75, 0.4, 0.15)):
                flashes[t0 + k] = v
    tag_font = font(int(13 * H / 540))
    for t, layers in enumerate(frames):
        img = compose(layers)
        if t in flashes:
            img = img * (1 - flashes[t]) + np.array([235, 230, 255], np.float32) * flashes[t]
        g = min(1.0, (t + 1) / edl["fade_in"], (n - t) / edl["fade_out"])
        img = np.clip(img * g, 0, 255).astype(np.uint8)
        base = Image.fromarray(img).resize((W, H), Image.LANCZOS).convert("RGBA")
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        m = int(36 * H / 540)
        tw = d.textlength(edl["tag"], font=tag_font)
        d.text((W - m - tw, H - m), edl["tag"], font=tag_font, fill=(170, 176, 196, int(190 * g)))
        for ti in edl["titles"]:
            s0 = clip_start[ti["clip"]]
            al = alpha_at(t, s0 + ti["from"], s0 + ti["to"])
            if al > 0:
                draw_title(layer, ti, al, W, H)
        for lab in edl["labels"]:
            s0 = clip_start[lab["clip"]]
            al = alpha_at(t, s0 + lab["from"], s0 + lab["to"]) * g
            if al > 0:
                draw_label(layer, lab, al, W, H)
        Image.alpha_composite(base, layer).convert("RGB").save(os.path.join(out_dir, f"{t + 1:04d}.png"))
    return n


def build_audio(path, dur, t_pre, t_main, t_reveal):
    """Placeholder sound design: drone bed, pre-pulse zap, main-pulse boom + crackle, airy pad."""
    sr = 48000
    ms = lambda t: int(t * 1000)  # noqa: E731
    src = [
        # 0 drone bed
        f"aevalsrc='0.16*sin(2*PI*55*t)+0.10*sin(2*PI*82.41*t)+0.04*sin(2*PI*110.3*t)':d={dur}:s={sr}",
        f"anoisesrc=color=brown:amplitude=0.35:d={dur}:r={sr}",
        # 2 pre-pulse zap (falling chirp) + hiss
        f"aevalsrc='0.45*exp(-12*t)*sin(2*PI*(2400*t-2600*t*t))':d=0.45:s={sr}",
        f"anoisesrc=color=white:amplitude=0.35:d=0.3:r={sr}",
        # 4 main-pulse boom (pitch-dropping sub) + rumble + shimmer + crackle
        f"aevalsrc='0.95*exp(-1.8*t)*sin(2*PI*(48*t-7*t*t))':d=3.2:s={sr}",
        f"anoisesrc=color=brown:amplitude=0.9:d=2.8:r={sr}",
        f"anoisesrc=color=white:amplitude=0.18:d=3.5:r={sr}",
        f"aevalsrc='0.5*gt(random(0),0.996)*(random(1)-0.5)*exp(-0.9*t)':d=3.5:s={sr}",
        # 8 reveal pad
        f"aevalsrc='(0.05*sin(2*PI*220*t)+0.035*sin(2*PI*329.63*t)+0.025*sin(2*PI*440*t))"
        f"*(0.7+0.3*sin(2*PI*0.3*t))':d={dur - t_reveal:.3f}:s={sr}",
    ]
    fc = [
        f"[1]lowpass=f=160,volume=0.6[n0]",
        f"[0][n0]amix=inputs=2:normalize=0,afade=t=in:d=1.5,afade=t=out:st={dur - 2.2:.3f}:d=2.2[bed]",
        f"[2]adelay={ms(t_pre)}|{ms(t_pre)}[zap]",
        f"[3]highpass=f=2500,afade=t=out:st=0:d=0.3,adelay={ms(t_pre)}|{ms(t_pre)}[hiss]",
        f"[4]adelay={ms(t_main)}|{ms(t_main)}[boom]",
        f"[5]lowpass=f=260,afade=t=out:st=0:d=2.8:curve=exp,adelay={ms(t_main)}|{ms(t_main)}[rum]",
        f"[6]highpass=f=5000,afade=t=out:st=0:d=3.5:curve=exp,adelay={ms(t_main)}|{ms(t_main)}[shim]",
        f"[7]highpass=f=1200,adelay={ms(t_main + 0.15)}|{ms(t_main + 0.15)}[crk]",
        f"[8]afade=t=in:d=2.5,afade=t=out:st={dur - t_reveal - 2.2:.3f}:d=2.2,"
        f"aecho=0.8:0.7:180|310:0.35|0.25,adelay={ms(t_reveal)}|{ms(t_reveal)}[pad]",
        "[bed][zap][hiss][boom][rum][shim][crk][pad]amix=inputs=8:normalize=0:duration=first,"
        "loudnorm=I=-18:TP=-2:LRA=11,aformat=channel_layouts=stereo[out]",
    ]
    cmd = ["ffmpeg", "-y", "-loglevel", "error"]
    for s in src:
        cmd += ["-f", "lavfi", "-i", s]
    cmd += ["-filter_complex", ";".join(fc), "-map", "[out]", "-ar", str(sr), "-t", f"{dur:.3f}", path]
    subprocess.run(cmd, check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shot", required=True)
    ap.add_argument("--engine", default="cycles")
    ap.add_argument("--no-audio", action="store_true")
    ap.add_argument("--skip-frames", action="store_true", help="reuse existing edit frames")
    a = ap.parse_args()
    root = RENDERS
    edl = json.load(open(os.path.join(EP, "blender/shots", a.shot + ".edit.json")))
    frames, clip_start = build_timeline(edl, os.path.join(root, a.shot, a.engine))
    out_dir = os.path.join(root, a.shot, "edit")
    n = len(frames) if a.skip_frames else render_frames(edl, frames, clip_start, out_dir)
    fps = edl["fps"]
    dur = n / fps

    clips = {c["cut"]: c for c in edl["clips"]}
    t_pre = (clip_start["CamPrePulse"] + 100 - clips["CamPrePulse"]["in"]) / fps
    t_main = (clip_start["CamPlasma"] + clips["CamPlasma"]["flash_at"] - clips["CamPlasma"]["in"]) / fps
    t_reveal = clip_start["CamReveal"] / fps

    grade = ("colorbalance=rs=-0.03:gs=0.0:bs=0.04:rh=0.03:gh=0.01:bh=-0.02,"
             "eq=contrast=1.05:saturation=1.08,vignette=angle=PI/5,"
             "noise=alls=4:allf=t,format=yuv420p")
    final = os.path.join(root, a.shot, f"{a.shot}_final.mp4")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(fps),
           "-i", os.path.join(out_dir, "%04d.png")]
    if not a.no_audio:
        wav = os.path.join(root, a.shot, "sound.wav")
        build_audio(wav, dur, t_pre, t_main, t_reveal)
        cmd += ["-i", wav, "-c:a", "aac", "-b:a", "192k"]
    cmd += ["-vf", grade, "-c:v", "libx264", "-preset", "slow", "-crf", "16",
            "-movflags", "+faststart", "-shortest", final]
    subprocess.run(cmd, check=True)
    print(f"{final}  {n} frames, {dur:.2f}s  pre={t_pre:.2f}s main={t_main:.2f}s reveal={t_reveal:.2f}s")


if __name__ == "__main__":
    main()
