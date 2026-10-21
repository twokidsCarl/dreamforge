"""Synthesize the narration with Qwen TTS and write a timing file.

  python3 tools/tts.py --voice Andre --mode paragraph      # default: one request per segment
  python3 tools/tts.py --voice Andre --mode sentence       # one request per sentence (auditions)
  python3 tools/tts.py --audition Neil,Andre,"Eldric Sage",Ethan --segments B1 --lines 8

Paragraph mode keeps one tempo, pitch and mood across a segment (sentence-by-sentence requests
drift: measured rate spread 265-442 chars/min). Each segment is generated up to --attempts times
and the take closest to the film's target rate and pitch is kept; tools/vo_split.py cuts it back
into sentences, which are loudness-matched and, if far off, gently time-stretched.

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
import tempfile
import time

sys.path.insert(0, os.path.dirname(__file__))
from asr_prompt import asr_prompt  # noqa: E402
from lint_script import parse  # noqa: E402
from speech_text import normalize  # noqa: E402

from paths import AUDIO, EP, REPO, RENDERS, SHARED  # noqa: E402,F401
ENDPOINTS = {"singapore": "https://dashscope-intl.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation",
             "beijing": "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"}
MODEL = "qwen3-tts-flash"
PAUSE_LINE = 0.4    # between sentences inside a segment (documentary breathing)
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


def cache_key(text, voice):
    """Cache by what is actually spoken, so pronunciation fixes re-synthesize just those lines."""
    return hashlib.sha1(f"{MODEL}|{voice}|{normalize(text)}".encode()).hexdigest()[:16]


def synth(text, voice, cache_dir):
    wav = os.path.join(cache_dir, f"{cache_key(text, voice)}.wav")
    return wav if os.path.exists(wav) else request(normalize(text), voice, wav)


def request(spoken, voice, wav):
    body = json.dumps({"model": MODEL, "input": {"text": spoken, "voice": voice,
                                                  "language_type": "Chinese"}}).encode()
    url = ENDPOINTS[os.environ.get("QWEN_REGION", "singapore")]
    fd, hdr = tempfile.mkstemp(prefix="tts_hdr_")         # the key goes in a 0600 file, not on the command line
    with os.fdopen(fd, "w") as f:
        f.write(f"Authorization: Bearer {os.environ['DASHSCOPE_API_KEY']}\nContent-Type: application/json\n")
    try:
        return _request(body, url, hdr, wav, spoken)
    finally:
        os.remove(hdr)


def _request(body, url, hdr, wav, spoken):
    r = None
    for attempt in range(5):
        try:
            # curl uses the system trust store (python.org builds of Python ship without one)
            r = subprocess.run(["curl", "-s", "-m", "90", "-X", "POST", url, "-H", f"@{hdr}", "--data-binary", "@-"],
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
        except Exception as e:  # noqa: B902  # rate limits / transient network errors / API error bodies
            wait = 2 ** attempt
            # never print the exception itself: a CalledProcessError carries the curl command line,
            # including the Authorization header with the API key
            if isinstance(e, subprocess.CalledProcessError):
                what = f"curl/ffmpeg exit {e.returncode}"
            else:
                what = type(e).__name__
            detail = r.stdout[:200].decode("utf-8", "replace") if r is not None and r.stdout else ""
            print(f"  retry {attempt + 1} in {wait}s: {what} {detail}", file=sys.stderr)
            time.sleep(wait)
    raise RuntimeError(f"TTS failed: {spoken[:30]}")


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
    cache = os.path.join(AUDIO, "vo_cache")
    os.makedirs(cache, exist_ok=True)
    vdir = os.path.join(out_dir, voice.replace(" ", "_"))
    os.makedirs(vdir, exist_ok=True)
    gap_line = silence(os.path.join(cache, f"sil_{PAUSE_LINE}.wav"), PAUSE_LINE)
    gap_seg = silence(os.path.join(cache, f"sil_{PAUSE_SEG}.wav"), PAUSE_SEG)
    script = parse(os.path.join(EP, "script/script_zh.md"))
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


TARGET_RATE = 255.0      # spoken chars per minute, the measured natural pace of a whole-paragraph take
RATE_TOL, PITCH_TOL = 0.07, 0.04
TARGET_PITCH = 107.0     # Hz, the film-wide median of Andre's takes: every segment is held to it
STRETCH_IF, STRETCH_MAX = 0.15, 0.08   # stretch a sentence only if >15% off, by at most 8%
TARGET_DB = -20.0                      # voiced RMS per sentence (dBFS)


def take_stats(x, spans, weights):
    import numpy as np
    from vo_split import SR as VSR
    rates = [w / (b - a) * 60 for (a, b), w in zip(spans, weights) if b > a]
    seg = x[int(spans[0][0] * VSR):int(spans[-1][1] * VSR)]
    return float(np.median(rates)), pitch(seg, VSR)


def pitch(x, sr):
    import numpy as np
    fr, hop = 1024, 480
    n = max(0, (len(x) - fr) // hop)
    f0s = []
    for i in range(0, n, 3):
        f = x[i * hop:i * hop + fr]
        if np.sqrt((f ** 2).mean()) < 0.02:
            continue
        f = f - f.mean()
        ac = np.correlate(f, f, "full")[fr - 1:]
        lo, hi = sr // 350, sr // 75
        k = lo + int(np.argmax(ac[lo:hi]))
        if ac[0] > 0 and ac[k] / ac[0] > 0.45:
            f0s.append(sr / k)
    return float(np.median(f0s)) if f0s else 0.0


def finish_sentence(x, a, b, rate, path, ref_rate=TARGET_RATE):
    """Loudness-match one sentence and, if its pace is far off the segment's own pace, nudge it."""
    import numpy as np
    import vo_split
    seg = x[max(0, int((a - 0.03) * vo_split.SR)):int((b + 0.03) * vo_split.SR)].copy()
    voiced = seg[np.abs(seg) > 0.01]
    rms = float(np.sqrt((voiced ** 2).mean())) if len(voiced) else 0.05
    seg *= 10 ** (TARGET_DB / 20) / max(rms, 1e-4)
    vo_split.cut(seg, [(0.0, len(seg) / vo_split.SR)], [path], pad=0.0)
    dev = rate / ref_rate - 1
    if abs(dev) > STRETCH_IF:
        tempo = 1 / (1 + max(-STRETCH_MAX, min(STRETCH_MAX, dev)))   # slow down fast lines, speed up slow ones
        tmp = path + ".tmp.wav"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", path, "-af", f"atempo={tempo:.4f}", tmp],
                       check=True)
        os.replace(tmp, path)
        return tempo
    return 1.0


_ASR = []


def intelligibility(wav, spoken):
    """How well the recogniser hears a take, as the score of its worst sentence (0-1, compared by sound so
    homophones are not errors): a take can hit the target rate and pitch and still garble two words, which a
    whole-paragraph average would hide. The transcript is cached next to the take. Needs faster-whisper,
    pypinyin (.venv)."""
    import difflib
    from asr_check import load16k, missed_terms, sounds
    from asr_prompt import asr_terms
    cache = wav + ".asr.txt"
    if os.path.exists(cache):
        heard = open(cache, encoding="utf-8").read()
    else:
        if not _ASR:
            from faster_whisper import WhisperModel
            _ASR.append(WhisperModel("large-v3-turbo", device="cpu", compute_type="int8"))
        segs, _ = _ASR[0].transcribe(load16k(wav), language="zh", beam_size=5, initial_prompt=asr_prompt())
        heard = "".join(x.text for x in segs)
        open(cache, "w", encoding="utf-8").write(heard)
    parts = [sounds(sp) for sp in spoken]
    full = [x for p in parts for x in p]
    hit = [False] * len(full)
    for blk in difflib.SequenceMatcher(None, full, sounds(heard), autojunk=False).get_matching_blocks():
        for i in range(blk.a, blk.a + blk.size):
            hit[i] = True
    worst, i = 1.0, 0
    for p in parts:
        if p:
            worst = min(worst, sum(hit[i:i + len(p)]) / len(p))
        i += len(p)
    # a glossary term that is not heard (激光 as 机关) costs as much as a badly garbled sentence
    miss = missed_terms("".join(spoken), heard, asr_terms())
    return worst - 0.05 * len(miss)


def build_paragraph(voice, segments, out_dir, attempts=3, asr=None):
    import vo_split
    from lint_script import spoken_len
    cache = os.path.join(AUDIO, "vo_cache", "para")
    os.makedirs(cache, exist_ok=True)
    vdir = os.path.join(out_dir, voice.replace(" ", "_"))
    sdir = os.path.join(vdir, "sentences")
    os.makedirs(sdir, exist_ok=True)
    script = parse(os.path.join(EP, "script/script_zh.md"))
    manifest, report, ref_pitch = {}, [], None
    timing, t_global = {"voice": voice, "model": MODEL, "mode": "paragraph", "segments": []}, 0.0
    # a partial run (--segments) must keep every other segment: carry its timing entry and sentence files over
    # (rewriting timing.json / sentences.json with only the selected segments broke retime for the rest)
    old = {}
    tpath = os.path.join(vdir, "timing.json")
    if segments and os.path.exists(tpath):
        old = {sg["id"]: sg for sg in json.load(open(tpath, encoding="utf-8")).get("segments", [])}
    for seg in script:
        if segments and seg["id"] not in segments:
            prev = old.get(seg["id"])
            if prev is None:
                raise SystemExit(f"{seg['id']} has no earlier timing entry; run tts.py for all segments once")
            for row in prev["lines"]:
                row["global_start"] = round(t_global + row["start"], 3)
            for i, L in enumerate(seg["lines"]):
                manifest[L["text"]] = os.path.join(sdir, f"{seg['id']}_{i:02d}.wav")
            prev["start"] = round(t_global, 3)
            timing["segments"].append(prev)
            t_global += prev["duration"]
            continue
        spoken = [normalize(L["text"]) for L in seg["lines"]]
        weights = [spoken_len(sp) for sp in spoken]
        text = "".join(spoken)
        best = None
        for k in range(attempts):
            key = hashlib.sha1(f"{MODEL}|{voice}|para|{k}|{text}".encode()).hexdigest()[:16]
            wav = os.path.join(cache, f"{seg['id']}_{key}.wav")
            if not os.path.exists(wav):
                request(text, voice, wav)
            spans, x = vo_split.split(wav, weights)
            rate, f0 = take_stats(x, spans, weights)
            ref = TARGET_PITCH                        # one pitch for the whole film, not per segment
            score = abs(rate / TARGET_RATE - 1) + 2 * abs(f0 / ref - 1)
            clear = intelligibility(wav, spoken) if asr and (asr == {"all"} or seg["id"] in asr) else 1.0
            score += 3 * (1 - clear)                  # a garbled word costs more than a slightly off tempo
            # (homophones the recogniser writes differently, e.g. 锡/稀, cost a little on every take alike)
            print(f"  {seg['id']} take {k + 1}: rate {rate:.0f} pitch {f0:.0f} heard {clear:.3f}", flush=True)
            if best is None or score < best[0]:
                best = (score, wav, spans, x, rate, f0, k)
            if abs(rate / TARGET_RATE - 1) <= RATE_TOL and abs(f0 / ref - 1) <= PITCH_TOL and clear >= 0.97:
                break
        score, wav, spans, x, rate, f0, k = best
        ref_pitch = ref_pitch or f0
        rows, t = [], 0.0
        for i, (L, (a, b), w) in enumerate(zip(seg["lines"], spans, weights)):
            path = os.path.join(sdir, f"{seg['id']}_{i:02d}.wav")
            tempo = finish_sentence(x, a, b, w / (b - a) * 60, path)
            d = duration(path)
            manifest[L["text"]] = path
            rows.append({"text": L["text"], "start": round(t, 3), "end": round(t + d, 3),
                         "global_start": round(t_global + t, 3), "tempo": round(tempo, 3)})
            t += d + PAUSE_LINE
        t += PAUSE_SEG - PAUSE_LINE
        timing["segments"].append({"id": seg["id"], "start": round(t_global, 3), "duration": round(t, 3),
                                   "lines": rows, "take": k, "rate": round(rate), "pitch": round(f0)})
        report.append((seg["id"], k + 1, rate, f0))
        print(f"  {voice} {seg['id']:<3} take {k + 1}/{attempts}  {rate:4.0f} chars/min  {f0:4.0f} Hz  {t:6.1f}s")
        t_global += t
    timing["total"] = round(t_global, 3)
    json.dump(timing, open(os.path.join(vdir, "timing.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump(manifest, open(os.path.join(vdir, "sentences.json"), "w", encoding="utf-8"), ensure_ascii=False,
              indent=1)
    return timing


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--voice", default="Andre")
    ap.add_argument("--mode", choices=["paragraph", "sentence"], default="paragraph")
    ap.add_argument("--attempts", type=int, default=3)
    ap.add_argument("--asr", help="segments whose takes are also scored by intelligibility, or 'all' (needs .venv)")
    ap.add_argument("--audition", help="comma-separated voices to compare")
    ap.add_argument("--segments", help="comma-separated segment ids (default: all)")
    ap.add_argument("--lines", type=int, help="only the first N lines per segment")
    ap.add_argument("--out", default=os.path.join(AUDIO, "vo"))
    a = ap.parse_args()
    load_env()
    if "DASHSCOPE_API_KEY" not in os.environ:
        sys.exit("DASHSCOPE_API_KEY missing (set it in the environment or .env)")
    segs = set(a.segments.split(",")) if a.segments else None
    voices = [v.strip() for v in a.audition.split(",")] if a.audition else [a.voice]
    out = os.path.join(AUDIO, "auditions") if a.audition else a.out
    for v in voices:
        if a.mode == "paragraph" and not a.audition:
            t = build_paragraph(v, segs, out, a.attempts, asr=set(a.asr.split(",")) if a.asr else None)
            print(f"{v}: {t['total']:.1f}s total (paragraph mode)")
        else:
            t = build(v, segs, out, a.lines)
            print(f"{v}: {t['total']:.1f}s total, {t['chars_per_min']} chars/min")


if __name__ == "__main__":
    main()
