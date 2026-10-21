"""Per-line intelligibility check of a mix against the VO alone: which script characters the mix loses.

  DREAMFORGE_EPISODE=E2-optogenetics .venv/bin/python shared/tools/review_lines.py A0 renders/edit/A0_sample_v4_sound.mp4

Each narration line (storyboard.timed.yaml cues; the mix starts at the segment start) is transcribed on its own, from the
mix and from audio/vo/<voice>/vo_track.wav. A character counts as masked when the VO-only transcript has it and the mix
transcript does not; misreads the VO already has (TTS or ASR) are not the mix's fault and are listed separately.

Why not one pass over the whole file (review_asr.py): on a loaded CPU box the int8 decoder sometimes derails and then loops
for the rest of the file, the same input giving different text run to run. Here each line is decoded independently
(condition_on_previous_text=False, one thread), up to 3 tries, best kept; derailed tries are counted and printed.
"""
import argparse
import difflib
import os
import re
import subprocess
import sys

import numpy as np
from faster_whisper import WhisperModel

sys.path.insert(0, os.path.dirname(__file__))
from paths import AUDIO, timed_shots  # noqa: E402

norm = lambda s: re.sub(r"[^一-鿿0-9]", "", s)        # Chinese + digits; Latin names are unreliable either way


def load(f, t0=0.0, dur=None):
    cmd = ["ffmpeg", "-loglevel", "error", "-ss", f"{t0:.3f}"] + (["-t", f"{dur:.3f}"] if dur else []) + \
          ["-i", f, "-ac", "1", "-ar", "16000", "-f", "f32le", "-"]
    return np.frombuffer(subprocess.run(cmd, capture_output=True, check=True).stdout, dtype=np.float32)


def best(m, x, ref, tries=3):
    r, out, derailed = norm(ref), None, 0
    for _ in range(tries):
        segs, _ = m.transcribe(x, language="zh", beam_size=5, condition_on_previous_text=False)
        hyp = "".join(s.text for s in segs)
        sm = difflib.SequenceMatcher(None, r, norm(hyp), autojunk=False)
        got = set()
        for bl in sm.get_matching_blocks():
            got.update(range(bl.a, bl.a + bl.size))
        derailed += len(got) < 0.5 * len(r)
        if out is None or len(got) > len(out[0]):
            out = (got, hyp)
        if len(got) == len(r):
            break
    return out[0], out[1], derailed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("segment")
    ap.add_argument("mix")
    ap.add_argument("--voice", default="Andre")
    a = ap.parse_args()
    shots = timed_shots([a.segment])
    t0 = shots[0]["start"]
    lines = [(s["start"] - t0 + c["start"] - 0.25, s["start"] - t0 + c["end"] + 0.25, c["text"])
             for s in shots for c in s.get("cues") or []]
    m = WhisperModel("large-v3-turbo", device="cpu", compute_type=os.environ.get("DREAMFORGE_ASR_COMPUTE", "int8"),
                     cpu_threads=1)
    mix = load(a.mix)
    vo = load(os.path.join(AUDIO, "vo", a.voice, "vo_track.wav"), t0, lines[-1][1] + 1)
    masked_total = vo_total = n_total = 0
    for s, e, ref in lines:
        cut = lambda x: x[int(max(0, s) * 16000):int(e * 16000)]
        r = norm(ref)
        g_vo, h_vo, d_vo = best(m, cut(vo), ref)
        g_mx, h_mx, d_mx = best(m, cut(mix), ref)
        masked = "".join(r[i] for i in sorted(g_vo - g_mx))
        vo_miss = "".join(r[i] for i in range(len(r)) if i not in g_vo)
        masked_total += len(masked); vo_total += len(g_vo); n_total += len(r)
        print(f"{s:6.2f}-{e:6.2f}  vo {len(g_vo)}/{len(r)}  mix {len(g_mx)}/{len(r)}  masked[{masked}]  vo-misread[{vo_miss}]"
              f"  derailed vo {d_vo} mix {d_mx}\n      mix: {h_mx.strip()}", flush=True)
    print(f"{a.mix}: VO-only {vo_total}/{n_total}; characters masked by the mix: {masked_total}")
    sys.exit(1 if masked_total else 0)


if __name__ == "__main__":
    main()
