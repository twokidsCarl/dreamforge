#!/usr/bin/env python3
"""E2 v8 rough cut: v7 full film skeleton + selective v8 styleframe inserts.

Inserts micro/diagram/title SFs PLUS macro clean/photo where ready:
  SF04 Crick, SF05 Nobel, SF10 photo mouse (ground-locked).
Writes INTERNAL master only (E2_roughcut_v8_internal_YYYYMMDD.mp4).
Do NOT scp to public files unless self-eval near broadcastable.

Audio: always muxed from v7 full (VO+music). Never silent.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import time
from datetime import datetime
from pathlib import Path

OUT_DIR = Path("/workspace/e2work/lowres_cut")
BASE = OUT_DIR / "E2_lowres_full.mp4"
SF_DIR = Path("/workspace/e2work/v8/styleframes")
WORK = OUT_DIR / "_v8_roughcut_work"
STAMP = datetime.now().strftime("%Y%m%d_%H%M")
TODAY = STAMP  # used in NOTES title
MASTER = OUT_DIR / f"E2_roughcut_v8_internal_{STAMP}.mp4"
SHARE = OUT_DIR / f"E2_roughcut_v8_internal_{STAMP}_share.mp4"
NOTES = OUT_DIR / "E2_roughcut_v8_internal_NOTES.md"

W, H, FPS = 1280, 720, 24
SUB_H = 100

# Film-absolute times (3s open sting included). Macro portraits/mouse OMITTED on purpose.
REPLACES = [
    # (start, end, sf_stem)  — all loop-extended
    (3.00, 8.00, "SF01_open_title"),
    (8.00, 12.02, "SF02_1979_request"),
    (12.02, 19.75, "SF03_microbe_clues"),
    (19.75, 30.71, "SF04_crick_quote"),
    (30.71, 40.42, "SF12_neuron_select"),       # A0_03 diagram
    (40.42, 51.09, "SF05_nobel_portraits"),
    (51.49, 60.74, "SF06_switch_diagram"),
    (61.14, 68.31, "SF07_main_title"),
    (68.31, 121.38, "SF13_spike_causality"),    # A_01–A_04
    (121.38, 137.06, "SF08_early_attempts"),
    (137.46, 145.21, "SF09_chr2_channel"),
    (145.21, 161.07, "SF14_orexin_q"),          # A_07
    (161.07, 180.05, "SF10_mouse_tripo"),
    (180.05, 244.39, "SF15_br_pump_channel"),   # B_01–B_04
    (244.39, 367.24, "SF16_chr_path"),          # B_05–B_10
    (367.24, 389.96, "SF17_credit_word"),       # B_11–B_13
    (389.96, 488.16, "SF18_invivo_dual"),       # B_14–B_20
    (488.16, 577.24, "SF19_engram"),            # C_01–C_06
    (577.24, 593.87, "SF20_retina_intro"),      # C_07
    (593.87, 618.16, "SF11_eye_goggles"),
    (618.16, 665.49, "SF21_partial_vision"),    # C_09–C_10
    (665.49, 761.15, "SF22_regulatory"),        # C_11–C_16
    (761.15, 99999.0, "SF23_limits_close"),     # C_17–D end; clamped to total in main
]

# Still v7 / deferred (NOTES)
DEFERRED_MACRO = [
    (0.00, 3.00, "open_sting", "品牌叮 · 低 ROI defer"),
    (51.09, 51.49, "gap", "SF 间隙 0.4s"),
    (60.74, 61.14, "gap", "SF 间隙 0.4s"),
    (137.06, 137.46, "gap", "SF 间隙 0.4s"),
    # macro photoreal placeholders inside boards:
    (None, None, "macro_cage_mouse", "C_03/C_04 笼箱写实毛发 deferred until align-loop; see v8/review/ALIGN_LOOP_READY.md — overwrite styleframes/SF10|SF18|SF19*.mp4 to auto-pick"),
    (None, None, "macro_patient_face", "患者脸仍 deferred；SF21 已嵌 SF11 护目镜板 · 无人脸"),
]


def run(cmd):
    print("+", " ".join(str(c) for c in cmd[:10]), ("..." if len(cmd) > 10 else ""), flush=True)
    subprocess.run(cmd, check=True)


def probe_dur(path: Path) -> float:
    out = subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nk=1:nw=1", str(path)],
        text=True,
    ).strip()
    if not out or out == "N/A":
        raise RuntimeError(f"ffprobe duration N/A for {path}")
    return float(out)


def scale_vf() -> str:
    return (
        f"scale={W}:{H}:force_original_aspect_ratio=decrease,"
        f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2,fps={FPS},format=yuv420p,setsar=1"
    )


def make_sf_segment(stem: str, dur: float, out: Path, fade: float = 0.75) -> dict:
    """Scale SF to 720p and extend to `dur`.
    If dur > src: crossfade-chain copies (xfade) instead of hard stream_loop,
    so loop restarts no longer flash empty/phase-reset frames.
    """
    import math
    src = SF_DIR / f"{stem}.mp4"
    if not src.exists():
        raise FileNotFoundError(src)
    src_dur = probe_dur(src)
    mtime = src.stat().st_mtime
    scaled = out.with_suffix(".scaled.mp4")
    run([
        "ffmpeg", "-loglevel", "error", "-y", "-i", str(src),
        "-an", "-vf", scale_vf(),
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
        "-pix_fmt", "yuv420p", str(scaled),
    ])
    scaled_dur = probe_dur(scaled)
    HOLD_LAST_STEMS = set()  # prefer freeze-tail over xfade-loop ghosting
    if stem in HOLD_LAST_STEMS and dur > scaled_dur + 0.05:
        pad = dur - scaled_dur
        run([
            "ffmpeg", "-loglevel", "error", "-y", "-i", str(scaled),
            "-vf", f"tpad=stop_mode=clone:stop_duration={pad:.3f}",
            "-t", f"{dur:.3f}",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
            "-pix_fmt", "yuv420p", str(out),
        ])
        try:
            scaled.unlink()
        except OSError:
            pass
        got = probe_dur(out)
        return {
            "stem": stem, "src": str(src), "src_dur": src_dur,
            "mtime": mtime, "mtime_iso": time.strftime("%Y-%m-%d %H:%M:%S %z", time.localtime(mtime)),
            "out_dur": got, "extend": "hold_last",
        }
    if dur <= scaled_dur + 0.05:
        run([
            "ffmpeg", "-loglevel", "error", "-y", "-i", str(scaled),
            "-t", f"{dur:.3f}", "-c:v", "copy", "-an", str(out),
        ])
    else:
        # Crossfade chain: advance (scaled_dur - fade) per join
        fade_use = min(fade, scaled_dur * 0.35)
        step = max(scaled_dur - fade_use, scaled_dur * 0.5)
        n_extra = max(0, int(math.ceil((dur - scaled_dur) / step)))
        n_inputs = n_extra + 1
        # Cap inputs to keep filter graph sane
        if n_inputs > 24:
            # Fall back: longer effective step via smaller fade
            fade_use = min(0.4, scaled_dur * 0.2)
            step = max(scaled_dur - fade_use, scaled_dur * 0.5)
            n_extra = max(0, int(math.ceil((dur - scaled_dur) / step)))
            n_inputs = min(n_extra + 1, 24)
        inputs = []
        for _ in range(n_inputs):
            inputs.extend(["-i", str(scaled)])
        if n_inputs == 1:
            fc = f"[0:v]trim=duration={dur:.3f},setpts=PTS-STARTPTS[v]"
        else:
            parts = []
            prev = "[0:v]"
            for i in range(1, n_inputs):
                offset = i * step
                label = f"[x{i}]" if i < n_inputs - 1 else "[xx]"
                parts.append(
                    f"{prev}[{i}:v]xfade=transition=fade:duration={fade_use:.3f}:offset={offset:.3f}{label}"
                )
                prev = label
            # trim to exact duration
            parts.append(f"{prev}trim=duration={dur:.3f},setpts=PTS-STARTPTS[v]")
            fc = ";".join(parts)
        run([
            "ffmpeg", "-loglevel", "error", "-y",
            *inputs,
            "-filter_complex", fc, "-map", "[v]",
            "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
            "-pix_fmt", "yuv420p", str(out),
        ])
        try:
            scaled.unlink()
        except OSError:
            pass
    got = probe_dur(out)
    if abs(got - dur) > 0.12:
        pad = dur - got
        if pad > 0.05:
            tmp = out.with_suffix(".pad.mp4")
            run([
                "ffmpeg", "-loglevel", "error", "-y", "-i", str(out),
                "-vf", f"tpad=stop_mode=clone:stop_duration={pad:.3f}",
                "-t", f"{dur:.3f}",
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
                "-pix_fmt", "yuv420p", str(tmp),
            ])
            tmp.replace(out)
            got = probe_dur(out)
    return {
        "stem": stem, "src": str(src), "src_dur": src_dur,
        "mtime": mtime, "mtime_iso": time.strftime("%Y-%m-%d %H:%M:%S %z", time.localtime(mtime)),
        "out_dur": got, "extend": "xfade" if dur > src_dur + 0.05 else "trim",
    }


def extract_base_segment(start: float, dur: float, out: Path):
    run([
        "ffmpeg", "-loglevel", "error", "-y",
        "-ss", f"{start:.3f}", "-i", str(BASE),
        "-t", f"{dur:.3f}", "-an",
        "-vf", f"scale={W}:{H}:flags=lanczos,fps={FPS},format=yuv420p,setsar=1",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
        "-pix_fmt", "yuv420p", str(out),
    ])


def composite_sf_with_subs(sf_clip: Path, base_start: float, dur: float, out: Path):
    orig = WORK / f"_orig_{base_start:.2f}.mp4"
    extract_base_segment(base_start, dur, orig)
    filt = (
        f"[0:v]fps={FPS},format=yuv420p,setsar=1[sf];"
        f"[1:v]fps={FPS},format=yuv420p,setsar=1,crop={W}:{SUB_H}:0:{H - SUB_H}[bar];"
        f"[sf][bar]overlay=0:{H - SUB_H}:shortest=1[v]"
    )
    run([
        "ffmpeg", "-loglevel", "error", "-y",
        "-i", str(sf_clip), "-i", str(orig),
        "-filter_complex", filt, "-map", "[v]", "-an",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
        "-pix_fmt", "yuv420p", "-t", f"{dur:.3f}", str(out),
    ])


def build_timeline(total: float):
    cuts = sorted(REPLACES, key=lambda x: x[0])
    for a, b in zip(cuts, cuts[1:]):
        if a[1] > b[0] + 1e-6:
            raise SystemExit(f"overlap {a} vs {b}")
    segs = []
    t = 0.0
    for start, end, stem in cuts:
        if start > t + 1e-3:
            segs.append((t, start, "keep", None))
        segs.append((start, end, "sf", stem))
        t = end
    if t < total - 1e-3:
        segs.append((t, total, "keep", None))
    return segs


def main():
    if not BASE.exists():
        raise SystemExit(f"missing base {BASE}")
    total = probe_dur(BASE)
    print(f"base duration {total:.3f}s  audio will be copied from base", flush=True)

    # clamp replace ends to film length; drop zero-length
    global REPLACES
    REPLACES = [(a, min(b, total), s) for a, b, s in REPLACES if a < total - 1e-3]
    REPLACES = [(a, b, s) for a, b, s in REPLACES if b - a > 0.05]

    if WORK.exists():
        shutil.rmtree(WORK)
    WORK.mkdir(parents=True)

    segs = build_timeline(total)
    # drop tiny keep crumbs (<2 frames)
    segs = [(a, b, k, s) for a, b, k, s in segs if b - a > 0.05]
    if segs and segs[-1][1] < total - 0.05:
        # extend last segment to total if it is an SF covering the end
        a, b, k, s = segs[-1]
        segs[-1] = (a, total, k, s)
    elif not segs or segs[-1][1] < total - 0.05:
        pass
    concat_list = WORK / "concat.txt"
    piece_meta = []

    with concat_list.open("w") as flist:
        for i, (start, end, kind, stem) in enumerate(segs):
            dur = end - start
            piece = WORK / f"piece_{i:03d}.mp4"
            if kind == "keep":
                extract_base_segment(start, dur, piece)
                piece_meta.append({"i": i, "kind": "keep", "start": start, "end": end, "dur": dur})
            else:
                raw = WORK / f"sfraw_{i:03d}.mp4"
                info = make_sf_segment(stem, dur, raw)
                composite_sf_with_subs(raw, start, dur, piece)
                info.update({"i": i, "kind": "sf", "start": start, "end": end, "dur": dur})
                piece_meta.append(info)
            flist.write(f"file '{piece}'\n")
            got = probe_dur(piece)
            if abs(got - dur) > 0.15:
                print(f"WARN piece {i} dur {got:.3f} vs expected {dur:.3f}", flush=True)

    video_only = WORK / "video_concat.mp4"
    run([
        "ffmpeg", "-loglevel", "error", "-y",
        "-f", "concat", "-safe", "0", "-i", str(concat_list),
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(video_only),
    ])

    # CRITICAL: map v7 audio
    run([
        "ffmpeg", "-loglevel", "error", "-y",
        "-i", str(video_only), "-i", str(BASE),
        "-map", "0:v:0", "-map", "1:a:0",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
        "-shortest", "-movflags", "+faststart", str(MASTER),
    ])

    run([
        "ffmpeg", "-loglevel", "error", "-y", "-i", str(MASTER),
        "-c:v", "libx264", "-preset", "fast", "-crf", "28",
        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "96k",
        "-movflags", "+faststart", str(SHARE),
    ])

    master_dur = probe_dur(MASTER)
    # Verify audio stream exists
    has_audio = subprocess.check_output(
        ["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=codec_name",
         "-of", "csv=p=0", str(MASTER)],
        text=True,
    ).strip()
    if not has_audio:
        raise SystemExit("MASTER has no audio — abort")

    master_sz = MASTER.stat().st_size
    share_sz = SHARE.stat().st_size

    replaced_lines = []
    for p in piece_meta:
        if p["kind"] != "sf":
            continue
        replaced_lines.append(
            f"- **{p['stem']}** film {p['start']:.2f}–{p['end']:.2f}s "
            f"(dur {p['dur']:.2f}s); src loop-extend from {p['src_dur']:.2f}s; "
            f"`{Path(p['src']).name}` @ {p['mtime_iso']}"
        )

    deferred_lines = []
    for a, b, stem, why in DEFERRED_MACRO:
        if a is None:
            deferred_lines.append(f"- **{stem}** — {why}")
        else:
            deferred_lines.append(f"- **{stem}** film {a:.2f}–{b:.2f}s — {why}")
    deferred_block = "\n".join(deferred_lines) if deferred_lines else "- (none)"

    sf_inserted_dur = sum(p["dur"] for p in piece_meta if p["kind"] == "sf")

    notes = f"""# E2 rough cut v8 internal — {TODAY}

## Deliverables
- Master: `{MASTER}` ({master_dur:.2f}s ≈ {master_dur/60:.1f} min, {master_sz/1e6:.1f} MB, {W}×{H} @{FPS}fps, **with AAC audio**)
- Share: `{SHARE}` ({share_sz/1e6:.1f} MB, CRF 28)
- Audio codec present: `{has_audio}` (copied from v7 full mix)

## Method
- Skeleton: `E2_lowres_full.mp4` (v7, 865s) — **VO / music / SFX / brand stings / timing unchanged**. No TTS.
- Style: micro → v8 illustration; macro SF04/SF05/SF10 → clean/photo inserts when files exist.
- **INTERNAL only** — not for Carl/public share until self-eval near broadcastable.
- Picture inserts: micro/diagram/title + macro SF04/SF05/SF10 (~{sf_inserted_dur:.0f}s of picture). Bottom {SUB_H}px of v7 composited back for burned-in Chinese captions.
- Output {W}×{H}; v7 was 640×360 (upscaled), SF was 960×540.

## Replaced with v8 styleframes
{chr(10).join(replaced_lines)}

## Still v7 picture (everything outside inserted SF windows)
{deferred_block}

## SF01 / SF02 sequencing
BRIEF lists both near 0:03. Cut uses **SF01 3.00–8.00** then **SF02 8.00–12.02** so they do not overwrite each other.

## Macro inserts this build
- SF04 / SF05: clean editorial portraits (no face beads).
- SF10: photo mouse on locked ground; matte tightened (studio plate / white fringe).

## This build swap stats
- v8 picture inserted: ~{sf_inserted_dur:.0f}s ({100*sf_inserted_dur/master_dur:.0f}% of runtime)
- Still v7 picture: ~{master_dur-sf_inserted_dur:.0f}s ({100 - 100*sf_inserted_dur/master_dur:.0f}%)
- This round: xfade loop-extend (no hard stream_loop); lengthened SF13/15/16/22/23; SF18/19 photo-mouse plates; SF21←SF11 eye plate.
- Cost: $0. e1r3 not stopped.

## Known flaws (internal 初剪 — NOT for Carl yet)
- Remaining v7 is mostly open sting + tiny SF gaps (~few seconds).
- Loop seams reduced via longer sources + xfade (see `_seam_probe/SEAM_METRICS.md`); residual phase jumps remain on narrative boards.
- 360p/540p → 720p upscale soft; most of film is still diagram/type boards, not hero photoreal.
- Macro cage fur / patient face still not hero-aligned (photo insets only).
- Self-eval: still far below ACCEPTANCE ~95; **do not push Carl / public share**.

## Audio
- Identical to v7 full mix (VO + music/SFX). Master verified to contain an audio stream.
"""
    NOTES.write_text(notes, encoding="utf-8")
    (WORK / "meta.json").write_text(json.dumps(piece_meta, indent=2, ensure_ascii=False), encoding="utf-8")
    print("MASTER", MASTER, master_dur, master_sz, "audio=", has_audio)
    print("SHARE", SHARE, share_sz)
    print("NOTES", NOTES)


if __name__ == "__main__":
    main()
