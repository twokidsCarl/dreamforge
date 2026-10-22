"""Retime the storyboard to the real narration and lay the VO onto one timeline.

  python3 tools/retime.py [--voice Andre]

Inputs : episodes/<episode>/storyboard/storyboard.yaml (design durations, estimated at 250 chars/min)
         audio/vo/<voice>/timing.json + the per-sentence cache wavs (tools/tts.py)
Outputs: episodes/<episode>/storyboard/storyboard.timed.yaml  shots with real durations and VO cues
         audio/vo/<voice>/vo_track.wav                    narration placed on the film timeline
         episodes/<episode>/subs/zh.srt                          Chinese subtitles from the cues

Rule: a VO shot keeps the visual padding it was designed with (design duration minus the
estimated VO time, at least LEAD + TAIL) around its real VO; visual-only shots keep their
design duration. `hold: <s>` on a shot adds that much picture after its last word; `lead: <s>` sets when
its first word starts.
"""
import argparse
import json
import os
import re
import sys

import numpy as np
import yaml

sys.path.insert(0, os.path.dirname(__file__))
from lint_script import CHARS_PER_MIN, spoken_len  # noqa: E402
import tts  # noqa: E402

from paths import AUDIO, EP, REPO, RENDERS, SHARED  # noqa: E402,F401
LEAD, TAIL = 0.3, 0.4          # minimum silence before the first / after the last sentence
GAP = tts.PAUSE_LINE
EST_PAUSE = 0.35               # per-line pause assumed by the design estimate
END_HOLD = 2.5                 # hold on the last card after the final sentence
SUB_MAX = 18                   # max characters per subtitle
SUB_SPLIT = re.compile(r"(?<=[，；：？！。、])|(?<=——)")


CUT_AFTER = set("的了在和与把是给从到上里中或也就都对向被让并而")   # a line may end on these
CUT_BEFORE = set("和与或在把从到给被让并而但")                     # or start on these


TERMS = ("食欲素", "通道视紫红质一", "通道视紫红质二", "视紫红质", "快速眼动睡眠", "慢波睡眠", "一期二期", "离不开",
         "锋电位", "视黄醛", "嗜盐古菌", "下丘脑", "神经元", "生物制品许可申请", "主要终点", "关键次要终点",
         "神经退行性疾病", "光遗传", "司法辖区", "上市许可", "恐惧记忆", "恐惧条件化", "兴奋性神经元")
_WORD_EDGES = {}


def word_edges(c):
    """Character offsets where a word ends (jieba if installed, plus the episode's terms kept whole)."""
    if c in _WORD_EDGES:
        return _WORD_EDGES[c]
    try:
        import jieba
        for t in TERMS:
            jieba.add_word(t, freq=200000)
        edges, pos = set(), 0
        for w in jieba.lcut(c):
            pos += len(w)
            edges.add(pos)
    except ImportError:
        edges = set(range(1, len(c)))
    for t in TERMS:                                   # never cut inside a protected term
        i = c.find(t)
        while i >= 0:
            edges -= set(range(i + 1, i + len(t)))
            i = c.find(t, i + 1)
    _WORD_EDGES[c] = edges
    return edges


def best_cut(c):
    """Where to break an over-long clause: never inside a Latin word or number, never inside 《》,
    both halves at most SUB_MAX if possible, preferring a cut next to a particle and near the middle."""
    best = None
    total = spoken_len(c)
    edges = word_edges(c)
    for k in range(1, len(c)):
        a, b = c[k - 1], c[k]
        if a.isascii() and b.isascii() and (a.isalnum() or b.isalnum()) and not (a == " " or b == " "):
            continue                                      # inside a Latin word or a number
        # between two Latin words: keep a name like Karl Deisseroth whole unless nothing else fits
        latin_pair = ((a == " " and k >= 2 and c[k - 2].isascii() and c[k - 2].isalpha() and b.isascii() and b.isalpha())
                      or (b == " " and a.isascii() and a.isalpha() and k + 1 < len(c)
                          and c[k + 1].isascii() and c[k + 1].isalpha()))
        if b in "的了":
            continue                                      # a line does not start on a particle
        if k not in edges and not (a.isascii() or b.isascii()):
            continue                                      # inside a Chinese word
        if c[:k].count("《") != c[:k].count("》"):
            continue                                      # inside a book title
        if b in "，。、；：？！》）" or a in "《（":
            continue
        left = spoken_len(c[:k])
        if left == 0 or left == total:
            continue
        over = max(0, left - SUB_MAX)
        score = 10 * over + abs(left - total / 2) - (2.5 if a in CUT_AFTER or b in CUT_BEFORE else 0) \
            - (2 if a == " " or b == " " else 0) + (8 if latin_pair else 0)
        if best is None or score < best[0]:
            best = (score, k)
    return best[1] if best else None


def chunk_subtitle(text):
    """Split a sentence into subtitle-sized pieces at punctuation; drop trailing ，。"""
    pieces = [p for p in SUB_SPLIT.split(text) if p.strip()]
    out, cur = [], ""
    for p in pieces:
        if cur and spoken_len(cur + p) > SUB_MAX:
            out.append(cur)
            cur = p
        else:
            cur += p
    if cur:
        out.append(cur)
    fixed = []
    for c in out:  # a clause that is still too long: cut it until every piece fits SUB_MAX
        while spoken_len(c) > SUB_MAX:
            k = best_cut(c)
            if k is None:
                break
            fixed.append(c[:k])
            c = c[k:].lstrip()
        fixed.append(c)
    return [re.sub(r"[，。、；]+$", "", c).strip() for c in fixed if c.strip()]


_MANIFEST = {}


def wav_for(text, voice):
    """Sentence audio: paragraph-mode manifest if present, else the per-sentence cache."""
    if voice not in _MANIFEST:
        p = os.path.join(AUDIO, "vo", voice, "sentences.json")
        _MANIFEST[voice] = json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}
    if text in _MANIFEST[voice]:
        return _MANIFEST[voice][text]
    return os.path.join(AUDIO, "vo_cache", f"{tts.cache_key(text, voice)}.wav")


def read_wav(path):
    import wave
    with wave.open(path) as w:
        assert w.getframerate() == tts.SR and w.getnchannels() == 1
        return np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)


def srt_time(t):
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--voice", default="Andre")
    a = ap.parse_args()
    sb = yaml.safe_load(open(os.path.join(EP, "storyboard/storyboard.yaml"), encoding="utf-8"))
    shots = sb["shots"]
    t, cues, design_total = 0.0, [], 0.0
    for s in shots:
        design_total += s["duration"]
        vo = s.get("vo") or []
        if vo:
            durs = [len(read_wav(wav_for(v, a.voice))) / tts.SR for v in vo]
            real = sum(durs) + GAP * (len(vo) - 1)
            est = sum(spoken_len(v) / CHARS_PER_MIN * 60 + EST_PAUSE for v in vo)
            pad = max(s["duration"] - est, LEAD + TAIL)
            lead = s.get("lead") or min(max(LEAD, pad * 0.3), 1.2)       # `lead: <s>` pins the first word
            pad = max(pad, lead + TAIL)
            s["duration_design"] = s["duration"]
            s["duration"] = round(real + pad, 2)
            c = t + lead
            s["cues"] = []
            for v, d in zip(vo, durs):
                cues.append({"shot": s["id"], "text": v, "start": round(c, 3), "end": round(c + d, 3)})
                s["cues"].append({"text": v, "start": round(c - t, 3), "end": round(c - t + d, 3)})
                c += d + GAP
        if s.get("hold"):                     # pure picture after the last word (a beat, a title settling)
            s["duration"] = round(s["duration"] + s["hold"], 2)
        s["start"] = round(t, 3)
        if s is shots[-1]:
            s["duration"] = round(s["duration"] + END_HOLD, 2)
        t += s["duration"]
    total = t

    # subtitle pieces: each cue split at punctuation, time shared by spoken length
    subs = []
    for c in cues:
        parts = chunk_subtitle(c["text"])
        w = [max(spoken_len(p), 1) for p in parts]
        t0, span = c["start"], c["end"] - c["start"]
        for p, wi in zip(parts, w):
            d = span * wi / sum(w)
            subs.append({"shot": c["shot"], "text": p, "start": round(t0, 3), "end": round(t0 + d, 3)})
            t0 += d
    by_shot = {}
    for x in subs:
        by_shot.setdefault(x["shot"], []).append(x)
    for s in shots:
        if s["id"] in by_shot:
            s["subs"] = [{"text": x["text"], "start": round(x["start"] - s["start"], 3),
                          "end": round(x["end"] - s["start"], 3)} for x in by_shot[s["id"]]]

    track = np.zeros(int(np.ceil(total * tts.SR)) + tts.SR, dtype=np.int32)
    for c in cues:
        x = read_wav(wav_for(c["text"], a.voice)).astype(np.int32)
        i = int(round(c["start"] * tts.SR))
        track[i:i + len(x)] += x
    track = np.clip(track, -32768, 32767).astype(np.int16)
    vdir = os.path.join(AUDIO, "vo", a.voice)
    import wave
    with wave.open(os.path.join(vdir, "vo_track.wav"), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(tts.SR)
        w.writeframes(track.tobytes())

    os.makedirs(os.path.join(EP, "subs"), exist_ok=True)
    with open(os.path.join(EP, "subs/zh.srt"), "w", encoding="utf-8") as fh:
        for i, c in enumerate(subs, 1):
            fh.write(f"{i}\n{srt_time(c['start'])} --> {srt_time(c['end'])}\n{c['text']}\n\n")
    sb["timing"] = {"voice": a.voice, "total": round(total, 2), "design_total": round(design_total, 2)}
    with open(os.path.join(EP, "storyboard/storyboard.timed.yaml"), "w", encoding="utf-8") as fh:
        fh.write("# Generated by tools/retime.py from storyboard.yaml + real VO timing. Do not edit.\n")
        yaml.safe_dump(sb, fh, allow_unicode=True, sort_keys=False, width=120)

    segs = {}
    for s in shots:
        segs.setdefault(s["segment"], [0.0, 0.0])
        segs[s["segment"]][0] += s.get("duration_design", s["duration"])
        segs[s["segment"]][1] += s["duration"]
    for k, (d0, d1) in segs.items():
        print(f"{k:<4} design {d0:6.1f}s -> timed {d1:6.1f}s")
    print(f"total design {design_total / 60:.2f} min -> timed {total / 60:.2f} min; {len(cues)} cues, "
          f"{len(subs)} subtitles (max {max(spoken_len(x['text']) for x in subs)} chars)")


if __name__ == "__main__":
    main()
