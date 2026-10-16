"""Synthesize the narration sentence by sentence with Qwen TTS and write a timing file.

  python3 tools/tts.py [--voice Neil] [--segments B1,B2] [--out audio/vo]
  python3 tools/tts.py --audition Neil,Andre,"Eldric Sage",Ethan --segments B1 --lines 8

Reads DASHSCOPE_API_KEY / QWEN_REGION from the environment or the repo's .env (never
committed). Each sentence is cached under audio/vo_cache/<hash>.wav, so editing the script
only re-synthesizes changed sentences. Output per run:
  <out>/<voice>/<SEG>.wav      one file per segment, sentences joined with pauses
  <out>/<voice>/timing.json    start/end of every sentence (seconds, per segment and global)
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))
from lint_script import parse  # noqa: E402

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ENDPOINTS = {"singapore": "https://dashscope-intl.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation",
             "beijing": "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"}
MODEL = "qwen3-tts-flash"
PAUSE_LINE = 0.25   # between sentences inside a segment
PAUSE_SEG = 0.8     # appended after each segment
SR = 24000


def load_env():
    p = os.path.join(REPO, ".env")
    if os.path.exists(p):
        for line in open(p):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


def synth(text, voice, cache_dir):
    key = hashlib.sha1(f"{MODEL}|{voice}|{text}".encode()).hexdigest()[:16]
    wav = os.path.join(cache_dir, f"{key}.wav")
    if os.path.exists(wav):
        return wav
    body = json.dumps({"model": MODEL, "input": {"text": text, "voice": voice, "language_type": "Chinese"}}).encode()
    url = ENDPOINTS[os.environ.get("QWEN_REGION", "singapore")]
    r = None
    for attempt in range(5):
        try:
            # curl uses the system trust store (python.org builds of Python ship without one)
            r = subprocess.run(["curl", "-s", "-m", "90", "-X", "POST", url,
                                "-H", f"Authorization: Bearer {os.environ['DASHSCOPE_API_KEY']}",
                                "-H", "Content-Type: application/json", "--data-binary", "@-"],
                               input=body, capture_output=True, check=True)
            d = json.loads(r.stdout)
            audio_url = d["output"]["audio"]["url"]
            raw = wav + ".dl"
            subprocess.run(["curl", "-s", "-m", "90", "-o", raw, audio_url], check=True)
            # normalise to mono 24 kHz 16-bit PCM so segments concatenate cleanly
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw, "-ac", "1", "-ar", str(SR),
                            "-sample_fmt", "s16", wav], check=True)
            os.remove(raw)
            return wav
        except Exception as e:  # rate limits / transient network errors / API error bodies
            wait = 2 ** attempt
            detail = r.stdout[:200] if "r" in locals() and hasattr(r, "stdout") else ""
            print(f"  retry {attempt + 1} in {wait}s: {e} {detail}", file=sys.stderr)
            time.sleep(wait)
    raise RuntimeError(f"TTS failed: {text[:30]}")


def duration(wav):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", wav],
                         capture_output=True, text=True, check=True).stdout
    return float(out.strip())


def silence(path, secs):
    if not os.path.exists(path):
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i",
                        f"anullsrc=r={SR}:cl=mono", "-t", f"{secs}", "-sample_fmt", "s16", path], check=True)
    return path


def build(voice, segments, out_dir, max_lines=None):
    cache = os.path.join(REPO, "audio", "vo_cache")
    os.makedirs(cache, exist_ok=True)
    vdir = os.path.join(out_dir, voice.replace(" ", "_"))
    os.makedirs(vdir, exist_ok=True)
    gap_line = silence(os.path.join(cache, f"sil_{PAUSE_LINE}.wav"), PAUSE_LINE)
    gap_seg = silence(os.path.join(cache, f"sil_{PAUSE_SEG}.wav"), PAUSE_SEG)
    script = parse(os.path.join(REPO, "projects/euv/script/script_zh.md"))
    timing, t_global, chars = {"voice": voice, "model": MODEL, "segments": []}, 0.0, 0
    for seg in script:
        if segments and seg["id"] not in segments:
            continue
        lines = seg["lines"][:max_lines] if max_lines else seg["lines"]
        parts, rows, t = [], [], 0.0
        for i, L in enumerate(lines):
            wav = synth(L["text"], voice, cache)
            d = duration(wav)
            rows.append({"text": L["text"], "start": round(t, 3), "end": round(t + d, 3),
                         "global_start": round(t_global + t, 3)})
            parts.append(wav)
            t += d
            chars += len(L["text"])
            if i < len(lines) - 1:
                parts.append(gap_line)
                t += PAUSE_LINE
        parts.append(gap_seg)
        t += PAUSE_SEG
        lst = os.path.join(vdir, f"{seg['id']}.txt")
        with open(lst, "w") as fh:
            fh.writelines(f"file '{p}'\n" for p in parts)
        seg_wav = os.path.join(vdir, f"{seg['id']}.wav")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst,
                        "-c", "copy", seg_wav], check=True)
        os.remove(lst)
        timing["segments"].append({"id": seg["id"], "start": round(t_global, 3), "duration": round(t, 3),
                                   "lines": rows})
        print(f"  {voice:<12} {seg['id']:<4} {len(lines):>3} lines {t:6.1f}s")
        t_global += t
    timing["total"] = round(t_global, 3)
    timing["chars_per_min"] = round(chars / (t_global / 60), 1) if t_global else 0
    json.dump(timing, open(os.path.join(vdir, "timing.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return timing


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--voice", default="Neil")
    ap.add_argument("--audition", help="comma-separated voices to compare")
    ap.add_argument("--segments", help="comma-separated segment ids (default: all)")
    ap.add_argument("--lines", type=int, help="only the first N lines per segment")
    ap.add_argument("--out", default=os.path.join(REPO, "audio", "vo"))
    a = ap.parse_args()
    load_env()
    if "DASHSCOPE_API_KEY" not in os.environ:
        sys.exit("DASHSCOPE_API_KEY missing (set it in the environment or .env)")
    segs = set(a.segments.split(",")) if a.segments else None
    voices = [v.strip() for v in a.audition.split(",")] if a.audition else [a.voice]
    out = os.path.join(REPO, "audio", "auditions") if a.audition else a.out
    for v in voices:
        t = build(v, segs, out, a.lines)
        print(f"{v}: {t['total']:.1f}s total, {t['chars_per_min']} chars/min")


if __name__ == "__main__":
    main()
