"""Transcribe every narration sentence back to text and flag ones that differ from the script.

  .venv/bin/python tools/asr_check.py [--voice Andre] [--model large-v3-turbo] [--threshold 0.9]

A stand-in for listening: catches misread numbers, units, acronyms and dropped words.
Writes audio/vo/<voice>/asr_report.json and prints the flagged sentences (script vs heard).
"""
import argparse
import difflib
import json
import os
import re
import subprocess
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from lint_script import parse  # noqa: E402
from retime import wav_for  # noqa: E402

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DIGITS = "零一二三四五六七八九"


def num_to_zh(m):
    """Read an Arabic number the way a narrator would (enough for comparison, not a full spec)."""
    s = m.group(0).replace(",", "")
    if "." in s:
        a, b = s.split(".", 1)
        return int_zh(int(a)) + "点" + "".join(DIGITS[int(c)] for c in b)
    return int_zh(int(s))


def int_zh(n):
    if n == 0:
        return "零"
    units = [(100000000, "亿"), (10000, "万"), (1000, "千"), (100, "百"), (10, "十")]
    out, zero = "", False
    for u, name in units:
        q, n = divmod(n, u)
        if q:
            if zero:
                out += "零"
            out += (int_zh(q) if q >= 10 else DIGITS[q]) + name
            zero = False
        elif out:
            zero = True
    if n:
        out += ("零" if zero and out else "") + DIGITS[n]
    return out[1:] if out.startswith("一十") else out


def norm(s):
    s = re.sub(r"\d[\d,]*(\.\d+)?", num_to_zh, s)
    s = s.replace("两", "二").lower()
    return re.sub(r"[\s，。、；：？！“”‘’（）《》—…·,.;:?!()\"'\-%]", "", s)


def load16k(path):
    """Decode with ffmpeg to 16 kHz mono float32 (sidesteps PyAV version issues)."""
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", path, "-f", "f32le", "-ac", "1", "-ar", "16000", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--voice", default="Andre")
    ap.add_argument("--model", default="large-v3-turbo")
    ap.add_argument("--threshold", type=float, default=0.9)
    a = ap.parse_args()
    from faster_whisper import WhisperModel
    model = WhisperModel(a.model, device="cpu", compute_type="int8")
    try:
        from opencc import OpenCC
        t2s = OpenCC("t2s").convert
    except ImportError:
        t2s = lambda x: x  # noqa: E731
    rows = []
    for seg in parse(os.path.join(REPO, "projects/euv/script/script_zh.md")):
        for L in seg["lines"]:
            segs, _ = model.transcribe(load16k(wav_for(L["text"], a.voice)), language="zh", beam_size=5,
                                       initial_prompt="以下是普通话科普旁白，使用简体中文。")
            heard = t2s("".join(x.text for x in segs).strip())
            r = difflib.SequenceMatcher(None, norm(L["text"]), norm(heard)).ratio()
            rows.append({"seg": seg["id"], "script": L["text"], "heard": heard, "ratio": round(r, 3)})
            if r < a.threshold:
                print(f"[{seg['id']}] {r:.2f}\n  稿：{L['text']}\n  听：{heard}")
    out = os.path.join(REPO, "audio", "vo", a.voice, "asr_report.json")
    json.dump(rows, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    flagged = sum(r["ratio"] < a.threshold for r in rows)
    print(f"{len(rows)} sentences, {flagged} flagged below {a.threshold}; report: {out}")


if __name__ == "__main__":
    main()
