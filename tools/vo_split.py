"""Split a paragraph-level narration recording into its sentences.

Used by tools/tts.py --mode paragraph: the segment is synthesized in one request so the voice
keeps one tempo, pitch and mood; this finds the sentence boundaries afterwards.
Method: detect pauses (frames well below the speech level), then choose N-1 of them with
dynamic programming so the cut times best match the expected cumulative sentence lengths
(proportional to spoken characters), preferring longer pauses.
"""
import subprocess

import numpy as np

SR = 24000
HOP = 240                      # 10 ms


def load(path, sr=SR):
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", path, "-f", "s16le", "-ac", "1", "-ar", str(sr), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768


def pauses(x, min_len=0.12):
    n = len(x) // HOP
    rms = np.sqrt((x[:n * HOP].reshape(n, HOP) ** 2).mean(1)) + 1e-9
    db = 20 * np.log10(rms)
    quiet = db < np.percentile(db, 90) - 30
    out, i = [], 0
    while i < n:
        if quiet[i]:
            j = i
            while j < n and quiet[j]:
                j += 1
            if (j - i) * HOP / SR >= min_len:
                out.append(((i + j) / 2 * HOP / SR, (j - i) * HOP / SR, i * HOP / SR, j * HOP / SR))
            i = j
        else:
            i += 1
    return out          # (centre, length, start, end) in seconds


def split(path, weights):
    """Return [(start, end)] per sentence (seconds), speech only (pauses trimmed)."""
    x = load(path)
    total = len(x) / SR
    ps = [p for p in pauses(x) if 0.3 < p[0] < total - 0.3]
    n = len(weights)
    cum = np.cumsum(weights) / sum(weights)
    # speech span (exclude leading/trailing silence)
    allp = pauses(x)
    t0 = allp[0][3] if allp and allp[0][2] <= 0.01 else 0.0
    t1 = allp[-1][2] if allp and allp[-1][3] >= total - 0.01 else total
    expect = [t0 + (t1 - t0) * c for c in cum[:-1]]
    m = len(ps)
    if m < n - 1:
        raise ValueError(f"only {m} pauses for {n} sentences")
    INF = 1e18
    # cost of using pause j as boundary k: squared time error minus a bonus for long pauses
    cost = np.array([[(ps[j][0] - expect[k]) ** 2 - 0.35 * ps[j][1] for j in range(m)] for k in range(n - 1)])
    dp = np.full((n - 1, m), INF)
    back = np.zeros((n - 1, m), dtype=int)
    dp[0] = cost[0]
    for k in range(1, n - 1):
        best, arg = INF, -1
        for j in range(m):
            if j > 0 and dp[k - 1][j - 1] < best:
                best, arg = dp[k - 1][j - 1], j - 1
            if arg >= 0:
                dp[k][j] = best + cost[k][j]
                back[k][j] = arg
    j = int(np.argmin(dp[n - 2]))
    chosen = [j]
    for k in range(n - 2, 0, -1):
        j = back[k][j]
        chosen.append(j)
    chosen = chosen[::-1]
    bounds = [ps[j] for j in chosen]
    spans, start = [], t0
    for b in bounds:
        spans.append((start, b[2]))
        start = b[3]
    spans.append((start, t1))
    return spans, x


def cut(x, spans, out_paths, pad=0.03):
    import wave
    for (a, b), p in zip(spans, out_paths):
        seg = x[max(0, int((a - pad) * SR)):int((b + pad) * SR)]
        fade = int(0.01 * SR)
        seg = seg.copy()
        seg[:fade] *= np.linspace(0, 1, fade)
        seg[-fade:] *= np.linspace(1, 0, fade)
        with wave.open(p, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(SR)
            w.writeframes((np.clip(seg, -1, 1) * 32767).astype(np.int16).tobytes())
