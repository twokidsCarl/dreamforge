"""P9: generate and check a segment's sound design (sound/<seg>.yaml): music plans and SFX cues via ElevenLabs.

  DREAMFORGE_EPISODE=E2-optogenetics .venv/bin/python shared/tools/sound_gen.py A0 --dry-run   # cached or paid, per request
  DREAMFORGE_EPISODE=E2-optogenetics .venv/bin/python shared/tools/sound_gen.py A0             # generate what is missing
  DREAMFORGE_EPISODE=E2-optogenetics .venv/bin/python shared/tools/sound_gen.py A0 --check     # cue timing vs narration

Music entries with a `plan:` (composition plan) are generated with eleven.music(plan=…); the cache path must equal the
entry's `file:` (the tool prints the right value when it does not, so the yaml stays reproducible). Cues go through
eleven.sfx(text, len), the same call edit_film.py makes.

--check: speech spans from the VO track (ffmpeg silencedetect -40 dB, 0.25 s), then for each cue its global time and how
much of it sits on speech. A cue on speech without an `over_vo:` reason fails; impacts belong in the gaps (WORKFLOW 6.3).
Also prints each generated file's peak (sources above -1 dBFS fail) and the music loudness after a 120 Hz high-pass.
"""
import argparse
import os
import re
import subprocess
import sys

import yaml

sys.path.insert(0, os.path.dirname(__file__))
import eleven  # noqa: E402
from paths import AUDIO, EP, timed_shots  # noqa: E402


def speech_spans(vo, t0, dur):
    err = subprocess.run(["ffmpeg", "-hide_banner", "-ss", f"{t0:.3f}", "-t", f"{dur:.3f}", "-i", vo,
                          "-af", "silencedetect=n=-40dB:d=0.25", "-f", "null", "-"], capture_output=True, text=True).stderr
    marks = [(k, float(v)) for k, v in re.findall(r"silence_(start|end): ([\d.]+)", err)]
    spans, cur = [], 0.0                     # speech = complement of silence
    for k, v in marks:
        if k == "start":
            if v > cur:
                spans.append((cur, v))
        else:
            cur = v
    if not marks or marks[-1][0] == "end":
        spans.append((cur, dur))
    return [(a, b) for a, b in spans if b - a > 0.05]


def overlap(a, b, spans):
    return sum(max(0.0, min(b, y) - max(a, x)) for x, y in spans)


def peak_db(p):
    err = subprocess.run(["ffmpeg", "-hide_banner", "-i", p, "-af", "volumedetect", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    m = re.search(r"max_volume: ([-\d.]+) dB", err)
    return float(m.group(1)) if m else None


def lufs(p, gain=0.0):
    err = subprocess.run(["ffmpeg", "-hide_banner", "-i", p, "-af", f"highpass=f=120,volume={gain}dB,ebur128",
                          "-f", "null", "-"], capture_output=True, text=True).stderr
    m = re.findall(r"I:\s+([-\d.]+) LUFS", err)
    return float(m[-1]) if m else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("segment")
    ap.add_argument("--dry-run", action="store_true", help="list requests, call nothing")
    ap.add_argument("--check", action="store_true", help="timing / peak / loudness report, call nothing")
    ap.add_argument("--voice", default="Andre")
    a = ap.parse_args()
    seg = a.segment
    cfg = yaml.safe_load(open(os.path.join(EP, "sound", f"{seg.lower()}.yaml"), encoding="utf-8"))
    shots = timed_shots([seg])
    t0 = shots[0]["start"]
    start_of = {s["id"]: s["start"] - t0 for s in shots}
    seg_dur = shots[-1]["start"] + shots[-1]["duration"] - t0

    jobs = []                                 # (label, path, call)
    for i, m in enumerate(cfg.get("music") or []):
        if "plan" in m:
            p = eleven.music_path(plan=m["plan"], take=m.get("take", 0))
            want = os.path.relpath(p, os.path.join(AUDIO, "eleven"))
            if m.get("file") != want:
                print(f"music[{i}]: yaml file: {m.get('file')} -> set to  file: {want}")
            jobs.append((f"music[{i}] plan {sum(s['duration_ms'] for s in m['plan']['sections']) / 1000:.1f}s", p,
                         lambda m=m: eleven.music(plan=m["plan"], take=m.get("take", 0))))
        else:
            jobs.append((f"music[{i}] {m['file']}", os.path.join(AUDIO, "eleven", m["file"]), None))
    for c in cfg.get("cues") or []:
        p = eleven.sfx_path(c["text"], c.get("len"))
        jobs.append((f"{c['shot']}@{c['at']} {c['text'][:48]}", p, lambda c=c: eleven.sfx(c["text"], c.get("len"))))

    if not a.check:
        paid = 0
        for label, p, call in jobs:
            have = os.path.exists(p) and os.path.getsize(p) > 1000
            state = "cached" if have else ("NEW (API)" if call else "MISSING (no plan, cannot regenerate)")
            paid += 0 if have or not call else 1
            print(f"{state:10s} {os.path.basename(p)}  {label}")
            if not have and call and not a.dry_run:
                print("  ->", call(), flush=True)
        print(f"{paid} request(s) {'would be' if a.dry_run else 'were'} sent")
        return

    vo = os.path.join(AUDIO, "vo", a.voice, "vo_track.wav")
    spans = speech_spans(vo, t0, seg_dur)
    gaps = [(b, c) for (_, b), (c, _) in zip(spans, spans[1:]) if c - b >= 0.6]
    if spans and seg_dur - spans[-1][1] >= 0.6:
        gaps.append((spans[-1][1], seg_dur))
    print("speech gaps >= 0.6 s:", ", ".join(f"{x:.2f}-{y:.2f}" for x, y in gaps))
    bad = 0
    for m in cfg.get("music") or []:
        p = os.path.join(AUDIO, "eleven", m["file"])
        if os.path.exists(p):
            print(f"music {m['file']}: at {m['at']}  peak {peak_db(p)} dBFS  "
                  f"HP120 loudness at gain {m.get('gain', -6)} dB: {lufs(p, m.get('gain', -6))} LUFS")
        else:
            print(f"music {m['file']}: NOT GENERATED")
            bad += 1
    print(f"{'shot':8s} {'global':>13s}  {'on VO':>6s}  peak   verdict")
    for c in cfg.get("cues") or []:
        if c["shot"] not in start_of:
            print(f"{c['shot']:8s} not in segment {seg}")
            bad += 1
            continue
        p = eleven.sfx_path(c["text"], c.get("len"))
        g0 = start_of[c["shot"]] + c["at"]
        g1 = g0 + c.get("len", 1.0)
        ov = overlap(g0, g1, spans)
        pk = peak_db(p) if os.path.exists(p) else None
        if pk is None:
            verdict, bad = "NOT GENERATED", bad + 1
        elif pk > -1.0:
            verdict, bad = f"SOURCE PEAK {pk} dBFS", bad + 1
        elif ov < 0.05:
            verdict = "in gap"
        elif c.get("over_vo"):
            verdict = f"over VO, allowed: {c['over_vo']}"
            if c.get("gain", -14) > -20 and "底噪" not in c["over_vo"]:
                verdict, bad = verdict + "  [gain above -20 dB on words]", bad + 1
        else:
            verdict, bad = "ON SPEECH without over_vo", bad + 1
        print(f"{c['shot']:8s} {g0:6.2f}-{g1:6.2f}  {ov:5.2f}s  {pk if pk is not None else '-':>5}  {verdict}")
    print("OK" if not bad else f"{bad} problem(s)")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
