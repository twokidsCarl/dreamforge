"""Transcribe a finished cut (or any audio) to check that every narration line is intelligible in the mix.

  .venv/bin/python shared/tools/review_asr.py episodes/E1-euv-lithography/renders/edit/A0_v8.mp4
"""
import subprocess
import sys

import numpy as np
from faster_whisper import WhisperModel

pcm = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", sys.argv[1], "-ac", "1", "-ar", "16000", "-f", "f32le", "-"],
                     capture_output=True, check=True).stdout
m = WhisperModel("large-v3-turbo", device="cpu", compute_type="int8")
segs, _ = m.transcribe(np.frombuffer(pcm, dtype=np.float32), language="zh", initial_prompt="以下是普通话科普旁白。")
for s in segs:
    print(f"{s.start:6.2f} {s.end:6.2f} {s.text}")
