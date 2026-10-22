"""Full-film animatic for checkpoint 2: finished sample sections + timed story-reel boards, real VO, temp music.

  .venv/bin/python shared/tools/animatic.py --sample A0=renders/edit/A0_sample_v2.mp4 [--size 640x360]

- Picture: a segment given with --sample is cut from that finished sample (trimmed to the segment's timed
  length, so a stand-alone tail is dropped); every other shot is a story_reel clip: its rendered frames if
  any exist, otherwise the storyboard board (style, visual, planned on-screen text) with the subtitle.
  Clips are cached per shot under renders/animatic/clips/, so an interrupted run resumes where it stopped.
- Sound: a sample segment keeps its own finished mix. Elsewhere the VO track, plus the segment's
  sound/<seg>.yaml music if it exists, else the temp music in sound/temp_music.yaml (marked temp),
  ducked under the voice the same way edit_film does; each part loudness-normalised to -16 LUFS.
Output: renders/animatic/animatic_<W>x<H>.mp4
"""
import argparse
import os
import subprocess
import sys

import yaml

sys.path.insert(0, os.path.dirname(__file__))
import story_reel as SR  # noqa: E402

from paths import AUDIO, EP, RENDERS  # noqa: E402

FPS = 24


def run(cmd):
    subprocess.run(cmd, check=True)


def enc(extra_in, vf, out, frames=None):
    # tpad: a clip one frame short of its slot holds its last frame instead of shifting the rest of the film
    cmd = ["ffmpeg", "-y", "-loglevel", "error", *extra_in, "-vf", f"{vf},fps={FPS},tpad=stop_mode=clone:stop=12,format=yuv420p"]
    if frames:
        cmd += ["-frames:v", str(frames)]
    run(cmd + ["-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", out])


def music_entries(seg, seg_start):
    """(file, absolute start, gain, fade_out, temp?) for one segment."""
    own = os.path.join(EP, "sound", f"{seg.lower()}.yaml")
    if os.path.exists(own):
        cfg = yaml.safe_load(open(own, encoding="utf-8")) or {}
        if cfg.get("music"):
            return [(m["file"], seg_start + m.get("at", 0), m.get("gain", -6), m.get("fade_out", 2.0), False)
                    for m in cfg["music"]]
    tmp = os.path.join(EP, "sound", "temp_music.yaml")
    cfg = yaml.safe_load(open(tmp, encoding="utf-8")) if os.path.exists(tmp) else {}
    return [(m["file"], seg_start + m.get("at", 0), m.get("gain", -10), m.get("fade_out", 3.0), True)
            for m in (cfg.get(seg) or [])]


def mix_part(t0, t1, segs, voice, out_wav, end_fade=0.0):
    """VO from t0 to t1 on the film timeline, plus music for the segments in that span, -16 LUFS."""
    dur = t1 - t0
    # the end fade comes after loudnorm: loudnorm's dynamic gain would otherwise lift a fading tail back up
    ef = f",afade=t=out:st={dur - end_fade:.3f}:d={end_fade:.3f}" if end_fade else ""
    vo = os.path.join(AUDIO, "vo", voice, "vo_track.wav")
    inputs = ["-ss", f"{t0:.3f}", "-t", f"{dur:.3f}", "-i", vo]
    f = [f"[0:a]aresample=48000,pan=stereo|c0=c0|c1=c0,apad=whole_dur={dur:.3f},asplit=2[vo][key]"]
    parts, n = [], 1
    for seg, s0 in segs:
        for file, at, gain, fo, _ in music_entries(seg, s0):
            inputs += ["-i", os.path.join(AUDIO, "eleven", file)]
            d = max(0, int((at - t0) * 1000))
            # temp music sits under the voice: no low end, a small dip where speech intelligibility lives
            f.append(f"[{n}:a]aresample=48000,highpass=f=120,equalizer=f=2800:t=q:w=1.2:g=-4,volume={gain}dB,"
                     f"afade=t=in:d=2.0,areverse,afade=t=in:d={fo},areverse,"
                     f"adelay={d}|{d}[m{n}]")
            parts.append(f"[m{n}]")
            n += 1
    if parts:
        f.append("".join(parts) + f"amix=inputs={len(parts)}:normalize=0[mus]")
        f.append("[mus][key]sidechaincompress=threshold=0.02:ratio=8:attack=20:release=600[musd]")
        f.append(f"[vo][musd]amix=inputs=2:normalize=0,atrim=0:{dur:.3f},loudnorm=I=-16:TP=-1.5:LRA=11{ef}[out]")
    else:
        f.append("[key]anullsink")
        f.append(f"[vo]atrim=0:{dur:.3f},loudnorm=I=-16:TP=-1.5:LRA=11{ef}[out]")
    run(["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex", ";".join(f), "-map", "[out]",
         "-ar", "48000", out_wav])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", action="append", default=[], help="SEG=path/to/finished_sample.mp4")
    ap.add_argument("--size", default="640x360")
    ap.add_argument("--voice", default="Andre")
    ap.add_argument("--tail", type=float, default=4.0,
                    help="seconds after the last shot: the last frame fades to black while the music rings out")
    a = ap.parse_args()
    W, H = (int(x) for x in a.size.split("x"))
    samples = dict(x.split("=", 1) for x in a.sample)
    sb = yaml.safe_load(open(os.path.join(EP, "storyboard/storyboard.timed.yaml"), encoding="utf-8"))
    from lint_script import parse
    titles = {x["id"]: x["title"] for x in parse(os.path.join(EP, "script/script_zh.md"))}
    total, k = sb["timing"]["total"], H / 720
    out = os.path.join(RENDERS, "animatic")
    cdir = os.path.join(out, f"clips_{W}x{H}")
    os.makedirs(cdir, exist_ok=True)
    segs, order = {}, []
    for s in sb["shots"]:
        g = s["segment"]
        if g not in segs:
            segs[g] = [s["start"], s["start"] + s["duration"]]
            order.append(g)
        segs[g][1] = s["start"] + s["duration"]
    clips, n_board = [], 0
    for g in order:
        g0, g1 = segs[g]
        if g in samples:
            clip = os.path.join(cdir, f"_sample_{g}.mp4")
            src = samples[g]
            if not os.path.exists(clip) or os.path.getmtime(clip) < os.path.getmtime(src):
                enc(["-i", src], f"scale={W}:{H}", clip, frames=round(g1 * FPS) - round(g0 * FPS))
            clips.append(clip)
            print(f"{g}: finished sample {os.path.basename(src)}", flush=True)
            continue
        for s in [x for x in sb["shots"] if x["segment"] == g]:
            c = SR.build_clip(s, W, H, total, k, titles.get(g, ""), out)   # cached per shot
            fixed = os.path.join(cdir, f"{s['id']}.mp4")
            if not os.path.exists(fixed) or os.path.getmtime(fixed) < os.path.getmtime(c):
                # frame count from the film-timeline boundaries, so rounding never accumulates into VO drift
                n = round((s["start"] + s["duration"]) * FPS) - round(s["start"] * FPS)
                enc(["-i", c], f"scale={W}:{H}", fixed, frames=max(1, n))
            clips.append(fixed)
            n_board += not SR.rendered_frames(s["id"])[1]
        print(f"{g}: {sum(1 for x in sb['shots'] if x['segment'] == g)} shots", flush=True)
    n_tail = round(a.tail * FPS)
    if n_tail:
        last_png = os.path.join(out, "tail_last.png")
        run(["ffmpeg", "-y", "-loglevel", "error", "-sseof", "-0.2", "-i", clips[-1], "-update", "1", last_png])
        tail_clip = os.path.join(cdir, "_tail.mp4")
        fd = max(0.5, a.tail - 0.25)                      # reach black a quarter second before the end
        enc(["-loop", "1", "-framerate", str(FPS), "-i", last_png], f"scale={W}:{H},fade=t=out:st=0:d={fd:.3f}",
            tail_clip, frames=n_tail)
        clips.append(tail_clip)
    end = round(total * FPS) / FPS + n_tail / FPS        # picture length, frame-exact
    lst = os.path.join(out, "clips.txt")
    with open(lst, "w") as fh:
        fh.writelines(f"file '{c}'\n" for c in clips)
    video = os.path.join(out, "video.mp4")
    run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", video])
    # sound, part by part: a sample segment keeps its mix, the stretches between get VO + music
    pieces, t, run_segs = [], 0.0, []

    def flush(t_end):
        nonlocal t, run_segs
        if run_segs and t_end > t:
            w = os.path.join(out, f"mix_{len(pieces):02d}.wav")
            last = t_end >= total
            mix_part(t, end if last else t_end, run_segs, a.voice, w,
                     end_fade=(a.tail + 2.0) if last and a.tail else (2.5 if last else 0.0))   # music rings out over the tail
            pieces.append(w)
        run_segs = []

    for g in order:
        g0, g1 = segs[g]
        if g in samples:
            flush(g0)
            w = os.path.join(out, f"mix_{len(pieces):02d}.wav")
            run(["ffmpeg", "-y", "-loglevel", "error", "-i", samples[g], "-t", f"{g1 - g0:.3f}", "-vn",
                 "-ar", "48000", "-ac", "2", w])
            pieces.append(w)
            t = g1
        else:
            if not run_segs:
                t = g0
            run_segs.append((g, g0))
    flush(total)
    alst = os.path.join(out, "audio.txt")
    with open(alst, "w") as fh:
        fh.writelines(f"file '{p}'\n" for p in pieces)
    wav = os.path.join(out, "mix.wav")
    run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", alst, "-c", "copy", wav])
    mp4 = os.path.join(out, f"animatic_{W}x{H}.mp4")
    # audio padded to the picture and cut at the picture's length: no frame is dropped at the end
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", video, "-i", wav, "-c:v", "copy", "-af", "apad", "-t", f"{end:.4f}",
         "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", mp4])
    print(mp4, f"{len(clips)} clips, {n_board} boards, {end:.2f} s ({end / 60:.2f} min) incl. {a.tail:.1f} s tail")


if __name__ == "__main__":
    main()
