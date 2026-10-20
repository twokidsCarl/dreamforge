"""Word timestamps for a stretch of audio: where a word falls, to sync titles, bursts and sound cues.

  .venv/bin/python shared/tools/review_words.py audio/vo/Andre/vo_track.wav <start_s> <dur_s>
"""
import os, subprocess, sys, numpy as np
from faster_whisper import WhisperModel
wav, t0, dur = sys.argv[1], float(sys.argv[2]), float(sys.argv[3])
pcm = subprocess.run(["ffmpeg", "-loglevel", "error", "-ss", str(t0), "-t", str(dur), "-i", wav, "-ac", "1", "-ar", "16000",
                      "-f", "f32le", "-"], capture_output=True, check=True).stdout
m = WhisperModel("large-v3-turbo", device="cpu", compute_type=os.environ.get("DREAMFORGE_ASR_COMPUTE", "int8"))
segs, _ = m.transcribe(np.frombuffer(pcm, dtype=np.float32), language="zh", word_timestamps=True)
print(" ".join(f"{w.word}@{w.start:.2f}-{w.end:.2f}" for s in segs for w in s.words))
