"""Re-cut paragraph-mode narration into sentences using ASR word timestamps.

  .venv/bin/python tools/vo_align.py [--voice Andre]

Pause-only splitting (vo_split.split) can land on a comma inside a sentence. Here every chosen
segment take (audio/vo/<voice>/timing.json) is transcribed with word timestamps, the recognised
characters are aligned to the script's spoken text, and each sentence boundary is snapped to the
nearest pause. Sentence wavs, sentences.json and timing.json are rewritten.
"""
import argparse
import difflib
import hashlib
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from asr_prompt import asr_prompt  # noqa: E402
import tts  # noqa: E402
import vo_split  # noqa: E402
from asr_check import load16k, norm  # noqa: E402
from lint_script import parse, spoken_len  # noqa: E402
from speech_text import normalize  # noqa: E402

from paths import AUDIO, EP, REPO  # noqa: E402


PLAIN_PROMPT = "以下是普通话科普旁白，使用简体中文。"


def char_times(model, wav, prompt=None):
    segs, _ = model.transcribe(load16k(wav), language="zh", word_timestamps=True, beam_size=5,
                               initial_prompt=prompt or asr_prompt())
    chars, times = [], []
    for s in segs:
        for w in s.words:
            txt = norm(w.word)
            if not txt:
                continue
            for i, ch in enumerate(txt):            # spread a word's span over its characters
                t0 = w.start + (w.end - w.start) * i / len(txt)
                t1 = w.start + (w.end - w.start) * (i + 1) / len(txt)
                chars.append(ch)
                times.append((t0, t1))
    return "".join(chars), times


def _char_sounds(text):
    """One toneless-pinyin token per character (other characters as themselves), so homophones align."""
    from pypinyin import Style, lazy_pinyin
    return [lazy_pinyin(c, style=Style.NORMAL)[0] if "\u4e00" <= c <= "\u9fff" else c for c in text]


def align_spans(script_sentences, asr_text, asr_times, pauses):
    keys = [norm(s) for s in script_sentences]
    full = "".join(keys)
    # match by sound, character for character: 掩模 heard as 眼膜 still anchors its timestamps
    sm = difflib.SequenceMatcher(None, _char_sounds(full), _char_sounds(asr_text), autojunk=False)
    mapping = {}
    for a, b, n in sm.get_matching_blocks():
        for k in range(n):
            mapping[a + k] = b + k
    def time_at(idx, end=False):
        # nearest mapped character at or around idx
        for d in range(0, len(full)):
            for j in (idx - d, idx + d):
                if j in mapping:
                    t = asr_times[mapping[j]]
                    return t[1] if end else t[0]
        return 0.0
    spans, pos = [], 0
    for kkey in keys:
        a, b = pos, pos + len(kkey) - 1
        spans.append([time_at(a), time_at(b, end=True)])
        pos += len(kkey)
    # snap each boundary into the pause that lies between the two sentences
    for i in range(len(spans) - 1):
        gap_mid = (spans[i][1] + spans[i + 1][0]) / 2
        near = [p for p in pauses if abs(p[0] - gap_mid) < 0.6]
        if near:                                    # a sentence break is the longest pause around, not a comma
            p = max(near, key=lambda p: (round(p[1], 2), -abs(p[0] - gap_mid)))
            spans[i][1], spans[i + 1][0] = p[2] + 0.02, p[3] - 0.02
    return [tuple(s) for s in spans]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--voice", default="Andre")
    ap.add_argument("--model", default="large-v3-turbo")
    ap.add_argument("--reuse", action="store_true", help="reuse stored spans, skip ASR")
    a = ap.parse_args()
    model = None
    if not a.reuse:
        from faster_whisper import WhisperModel
        model = WhisperModel(a.model, device="cpu", compute_type="int8")
    vdir = os.path.join(AUDIO, "vo", a.voice)
    timing = json.load(open(os.path.join(vdir, "timing.json"), encoding="utf-8"))
    script = {s["id"]: s for s in parse(os.path.join(EP, "script/script_zh.md"))}
    manifest, t_global = {}, 0.0
    for seg in timing["segments"]:
        lines = script[seg["id"]]["lines"]
        spoken = [normalize(L["text"]) for L in lines]
        text = "".join(spoken)
        key = hashlib.sha1(f"{tts.MODEL}|{a.voice}|para|{seg['take']}|{text}".encode()).hexdigest()[:16]
        wav = os.path.join(AUDIO, "vo_cache", "para", f"{seg['id']}_{key}.wav")
        x = vo_split.load(wav)
        if a.reuse and seg.get("spans"):
            spans = [tuple(v) for v in seg["spans"]]
        else:
            pz = vo_split.pauses(x, min_len=0.08)
            for prompt in (None, PLAIN_PROMPT):          # glossary prompt first; it can make the recogniser drop a line
                asr_text, asr_times = char_times(model, wav, prompt)
                spans = align_spans(spoken, asr_text, asr_times, pz)
                short = [i for i, (s0, s1) in enumerate(spans) if s1 - s0 < 0.3]
                if not short:
                    break
                print(f"  {seg['id']}: ASR alignment lost sentence(s) {short} ({'glossary' if prompt is None else 'plain'} prompt)",
                      flush=True)
            if short:                                    # still lost: fall back to the pause-based split
                spans, _ = vo_split.split(wav, [spoken_len(sp) for sp in spoken])
        seg["spans"] = [list(v) for v in spans]
        rates_all = [spoken_len(sp) / max(s1 - s0, 0.2) * 60 for sp, (s0, s1) in zip(spoken, spans)]
        ref = float(np.median(rates_all))
        rows, t = [], 0.0
        for i, (L, sp, (s0, s1)) in enumerate(zip(lines, spoken, spans)):
            path = os.path.join(vdir, "sentences", f"{seg['id']}_{i:02d}.wav")
            rate = rates_all[i]
            tempo = tts.finish_sentence(x, s0, s1, rate, path, ref_rate=ref)
            d = tts.duration(path)
            manifest[L["text"]] = path
            rows.append({"text": L["text"], "start": round(t, 3), "end": round(t + d, 3),
                         "global_start": round(t_global + t, 3), "tempo": round(tempo, 3),
                         "rate": round(rate)})
            t += d + tts.PAUSE_LINE
        t += tts.PAUSE_SEG - tts.PAUSE_LINE
        seg.update({"start": round(t_global, 3), "duration": round(t, 3), "lines": rows, "aligned": "asr"})
        rates = [r["rate"] for r in rows]
        print(f"{seg['id']:<3} {len(rows):>2} lines  rate {min(rates)}-{max(rates)}  "
              f"stretched {sum(r['tempo'] != 1.0 for r in rows)}")
        t_global += t
    timing["total"] = round(t_global, 3)
    json.dump(timing, open(os.path.join(vdir, "timing.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump(manifest, open(os.path.join(vdir, "sentences.json"), "w", encoding="utf-8"), ensure_ascii=False,
              indent=1)
    print(f"total {t_global:.1f}s")


if __name__ == "__main__":
    main()
