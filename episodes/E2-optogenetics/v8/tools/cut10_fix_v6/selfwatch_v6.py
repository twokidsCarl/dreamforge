#!/usr/bin/env python3
"""fix_v6 continuous-play self audit (Carl note #3: 抽帧看不出运镜 → 连播指标).

For each window: decode EVERY frame (24fps), compute
  - mad[i]   = mean |f_i − f_{i−1}|            (cut / jump detector)
  - shift[i] = phase-correlation translation     (camera velocity; jerk = |Δshift|)
  - freeze   = runs with mad < 0.15 for > 1.5 s
  - top-edge streak score (note #2): column-variance of top 12 rows vs rows 40–80
and writes 12fps contact strips (one PNG per 2 s) for eyes-on review.
usage: selfwatch_v6.py VIDEO OUTDIR
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
import cv2

WINDOWS = [(0, 30), (20, 35), (65, 90), (120, 175), (175, 276), (276, 480), (480, 680), (680, 865)]
# intentional cuts/dissolves (film time) — jumps here are expected, everything else is flagged
PLANNED = [3.0, 8.0, 12.02, 19.75, 30.71, 40.42, 51.09, 60.74, 68.31, 83.1, 96.2, 121.38, 137.06, 145.21,
           161.07, 170.3, 183.76, 205.0, 244.2, 267.4,
           # round-2 tail beat boundaries / dissolves (rebuild_v6_tail.BEATS) + intentional cuts inside beats
           276.3, 285.6, 306.8, 343.9, 366.9, 375.9, 390.1, 404.9, 417.5, 435.6, 442.3, 452.6, 468.3, 487.4,
           499.2, 513.3, 528.7, 541.0, 577.0, 594.0, 618.6, 643.6, 665.6, 702.5, 725.3, 753.3, 761.3, 772.3,
           784.2, 789.1, 794.3, 811.1, 821.1, 828.2, 836.2, 843.2, 852.8]


def near_planned(t, tol=0.75):
    return any(abs(t - p) < tol for p in PLANNED)


def analyse(video, t0, t1, outdir):
    cap = cv2.VideoCapture(str(video))
    fps = cap.get(cv2.CAP_PROP_FPS)
    cap.set(cv2.CAP_PROP_POS_FRAMES, int(t0 * fps))
    prev = None; prevg = None
    rows = []
    strip = []
    top_scores = []
    i = int(t0 * fps)
    while i < int(t1 * fps):
        ok, f = cap.read()
        if not ok:
            break
        t = i / fps
        small = cv2.resize(f, (320, 180), interpolation=cv2.INTER_AREA).astype(np.float32)
        g = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
        if prev is not None:
            mad = float(np.abs(small - prev).mean())
            (dx, dy), resp = cv2.phaseCorrelate(prevg, g)
            rows.append((t, mad, dx, dy, resp))
        prev, prevg = small, g
        top = f[:12].astype(np.float32).mean(-1); ref = f[40:80].astype(np.float32).mean(-1)
        top_scores.append(float(np.abs(np.diff(top, axis=1)).mean() / (np.abs(np.diff(ref, axis=1)).mean() + 1e-3)))
        if i % 2 == 0:
            strip.append((t, cv2.resize(f, (213, 120))))
        i += 1
    # contact strips: 24 thumbs (2 s @ 12fps) per PNG
    outdir.mkdir(parents=True, exist_ok=True)
    for k in range(0, len(strip), 24):
        chunk = strip[k:k + 24]
        sheet = np.zeros((120 * 4, 213 * 6, 3), np.uint8)
        for j, (t, im) in enumerate(chunk):
            r, c = divmod(j, 6)
            sheet[r * 120:(r + 1) * 120, c * 213:(c + 1) * 213] = im
            cv2.putText(sheet, f'{t:.2f}', (c * 213 + 4, r * 120 + 14), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)
        cv2.imwrite(str(outdir / f'strip_{chunk[0][0]:07.2f}.jpg'), sheet, [cv2.IMWRITE_JPEG_QUALITY, 80])
    arr = np.array(rows)
    flags = []
    if len(arr):
        mad = arr[:, 1]
        med = np.median(mad)
        sh = np.hypot(arr[:, 2], arr[:, 3])
        jerk = np.abs(np.diff(sh, prepend=sh[0]))
        for (t, m, dx, dy, resp), jk in zip(rows, jerk):
            if near_planned(t):
                continue
            if m > max(6.0, 4 * med):
                flags.append({'t': round(t, 3), 'kind': 'jump/cut', 'mad': round(m, 2)})
            elif jk > 2.5 and resp > 0.3:
                flags.append({'t': round(t, 3), 'kind': 'camera jerk', 'jerk_px': round(float(jk), 2)})
        # freezes
        run = 0
        for t, m, *_ in rows:
            run = run + 1 if m < 0.15 else 0
            if run == int(1.5 * fps):
                flags.append({'t': round(t, 3), 'kind': 'freeze>1.5s'})
    return {'window': [t0, t1], 'frames': len(rows), 'mad_median': round(float(np.median(arr[:, 1])), 3) if len(arr) else None,
            'top_streak_max': round(max(top_scores), 3) if top_scores else None, 'flags': flags}


if __name__ == '__main__':
    video, outdir = Path(sys.argv[1]), Path(sys.argv[2])
    res = [analyse(video, a, b, outdir / f'w{a:03d}_{b:03d}') for a, b in WINDOWS]
    (outdir / 'selfwatch_metrics.json').write_text(json.dumps(res, ensure_ascii=False, indent=1))
    for r in res:
        print(r['window'], 'frames', r['frames'], 'mad_med', r['mad_median'], 'top_streak', r['top_streak_max'],
              'flags', len(r['flags']), r['flags'][:8])
