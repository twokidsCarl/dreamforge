#!/usr/bin/env python3
"""E2 Cut9 low-res full film: shortened timeline + photoreal mouse + Goodsell mol.
Audio/VO cut with picture so science sync is preserved on kept beats.
"""
from __future__ import annotations
import json, math, subprocess, shutil
from datetime import datetime
from pathlib import Path

OUT_DIR = Path('/workspace/e2work/lowres_cut')
BASE = OUT_DIR / 'E2_lowres_full.mp4'
SF_DIR = Path('/workspace/e2work/v8/styleframes')
WORK = OUT_DIR / '_cut9_work'
STAMP = datetime.now().strftime('%Y%m%d_%H%M')
MASTER = OUT_DIR / f'E2_cut9_{STAMP}.mp4'
SHARE = OUT_DIR / f'E2_cut9_{STAMP}_share.mp4'
CHAT = OUT_DIR / f'E2_cut9_{STAMP}_chat.mp4'
NOTES = Path('/workspace/e2work/v8/review/cut9/FIX_STATUS.md')
W, H, FPS = 1280, 720, 24
SUB_H = 100  # keep burned-in Chinese captions from base bottom

# Original SF windows on the v7 skeleton (film-absolute).
# Cut9 KEEPS the head of long filler SFs and drops their tails (sample-wall).
# Each entry: (keep_start, keep_end, sf_stem|None)
# None = keep base picture (open sting / tiny gaps).
KEEP = [
    (0.00,   3.00,   None),                  # brand sting
    (3.00,   8.00,   'SF01_open_title'),
    (8.00,   12.02,  'SF02_1979_request'),
    (12.02,  19.75,  'SF03_microbe_clues'),
    (19.75,  30.71,  'SF04_crick_quote'),
    (30.71,  40.42,  'SF12_neuron_select'),
    (40.42,  51.09,  'SF05_nobel_portraits'),
    (51.09,  51.49,  None),
    (51.49,  60.74,  'SF06_switch_diagram'),
    (60.74,  61.14,  None),
    (61.14,  68.31,  'SF07_main_title'),
    (68.31,  88.31,  'SF13_spike_causality'),   # was →121.38; keep 20s head
    # DROP 88.31–121.38 SF13 tail
    (121.38, 137.06, 'SF08_early_attempts'),
    (137.06, 137.46, None),
    (137.46, 145.21, 'SF09_chr2_channel'),
    (145.21, 161.07, 'SF14_orexin_q'),
    (161.07, 176.07, 'SF10_mouse_tripo'),       # was →180; keep 15s
    (180.05, 210.05, 'SF15_br_pump_channel'),   # was →244; keep 30s
    # DROP 210–244
    (244.39, 284.39, 'SF16_chr_path'),          # was →367; keep 40s
    # DROP 284–367
    (367.24, 389.96, 'SF17_credit_word'),
    (389.96, 419.96, 'SF18_invivo_dual'),       # was →488; keep 30s
    # DROP 420–488
    (488.16, 518.16, 'SF19_engram'),            # was →577; keep 30s
    # DROP 518–577
    (577.24, 593.87, 'SF20_retina_intro'),
    (593.87, 618.16, 'SF11_eye_goggles'),
    (618.16, 638.16, 'SF21_partial_vision'),    # was →665; keep 20s
    # DROP 638–665
    (665.49, 705.49, 'SF22_regulatory'),        # was →761; keep 40s
    # DROP 705–761
    (761.15, 806.15, 'SF23_limits_close'),      # was →865; keep 45s
]

def run(cmd):
    print('+', ' '.join(str(c) for c in cmd[:12]), ('...' if len(cmd) > 12 else ''), flush=True)
    subprocess.run(cmd, check=True)

def probe(path: Path) -> float:
    out = subprocess.check_output(
        ['ffprobe','-v','error','-show_entries','format=duration','-of','default=nk=1:nw=1', str(path)],
        text=True).strip()
    return float(out)

def scale_vf():
    return (f'scale={W}:{H}:force_original_aspect_ratio=decrease,'
            f'pad={W}:{H}:(ow-iw)/2:(oh-ih)/2,fps={FPS},format=yuv420p,setsar=1')

def extend_sf(stem: str, dur: float, out: Path):
    src = SF_DIR / f'{stem}.mp4'
    if not src.exists():
        raise FileNotFoundError(src)
    src_dur = probe(src)
    scaled = out.with_suffix('.scaled.mp4')
    run(['ffmpeg','-loglevel','error','-y','-i',str(src),'-vf',scale_vf(),
         '-c:v','libx264','-preset','fast','-crf','18','-an',str(scaled)])
    sd = probe(scaled)
    if dur <= sd + 0.05:
        run(['ffmpeg','-loglevel','error','-y','-i',str(scaled),'-t',f'{dur:.3f}',
             '-c:v','copy','-an',str(out)])
    else:
        # freeze last frame to fill (no xfade ghosting)
        pad = dur - sd
        run(['ffmpeg','-loglevel','error','-y','-i',str(scaled),
             '-vf',f'tpad=stop_mode=clone:stop_duration={pad:.3f}',
             '-t',f'{dur:.3f}','-c:v','libx264','-preset','fast','-crf','18','-an',str(out)])
    scaled.unlink(missing_ok=True)

def extract_base_av(start: float, dur: float, out_v: Path, out_a: Path):
    run(['ffmpeg','-loglevel','error','-y','-ss',f'{start:.3f}','-i',str(BASE),
         '-t',f'{dur:.3f}','-an','-vf',scale_vf(),
         '-c:v','libx264','-preset','fast','-crf','18',str(out_v)])
    run(['ffmpeg','-loglevel','error','-y','-ss',f'{start:.3f}','-i',str(BASE),
         '-t',f'{dur:.3f}','-vn','-c:a','aac','-b:a','160k',str(out_a)])

def composite_subs(sf_clip: Path, base_start: float, dur: float, out: Path):
    """Overlay bottom SUB_H px of base (burned-in Chinese captions) onto SF picture."""
    orig = out.with_suffix('.basev.mp4')
    run(['ffmpeg','-loglevel','error','-y','-ss',f'{base_start:.3f}','-i',str(BASE),
         '-t',f'{dur:.3f}','-an','-vf',scale_vf(),
         '-c:v','libx264','-preset','fast','-crf','18',str(orig)])
    # overlay bottom strip from orig onto sf
    filt = (f'[1:v]crop={W}:{SUB_H}:0:{H-SUB_H}[sub];'
            f'[0:v][sub]overlay=0:{H-SUB_H}')
    run(['ffmpeg','-loglevel','error','-y','-i',str(sf_clip),'-i',str(orig),
         '-filter_complex',filt,'-c:v','libx264','-preset','fast','-crf','18',
         '-pix_fmt','yuv420p','-t',f'{dur:.3f}','-an',str(out)])
    orig.unlink(missing_ok=True)

def main():
    if WORK.exists():
        shutil.rmtree(WORK)
    WORK.mkdir(parents=True)
    total_base = probe(BASE)
    print(f'base {total_base:.2f}s', flush=True)

    pieces_v, pieces_a, meta = [], [], []
    new_t = 0.0
    for i, (start, end, stem) in enumerate(KEEP):
        end = min(end, total_base)
        if end - start < 0.05:
            continue
        dur = end - start
        pv = WORK / f'v_{i:02d}.mp4'
        pa = WORK / f'a_{i:02d}.m4a'
        extract_base_av(start, dur, WORK / f'_bv_{i:02d}.mp4', pa)
        if stem is None:
            shutil.move(str(WORK / f'_bv_{i:02d}.mp4'), pv)
            kind = 'keep'
        else:
            raw = WORK / f'_sf_{i:02d}.mp4'
            extend_sf(stem, dur, raw)
            composite_subs(raw, start, dur, pv)
            raw.unlink(missing_ok=True)
            (WORK / f'_bv_{i:02d}.mp4').unlink(missing_ok=True)
            kind = 'sf'
        got = probe(pv)
        meta.append({'i': i, 'kind': kind, 'stem': stem, 'src_start': start, 'src_end': end,
                     'dur': dur, 'new_start': new_t, 'got': got})
        pieces_v.append(pv)
        pieces_a.append(pa)
        new_t += dur
        print(f'  [{i:02d}] {start:7.2f}-{end:7.2f} → +{dur:6.2f}s  {stem or "KEEP"}', flush=True)

    # concat video
    lst_v = WORK / 'list_v.txt'
    lst_v.write_text(''.join(f"file '{p}'\n" for p in pieces_v))
    vid = WORK / 'video.mp4'
    run(['ffmpeg','-loglevel','error','-y','-f','concat','-safe','0','-i',str(lst_v),
         '-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p',str(vid)])
    # concat audio with soft crossfade junctions via acrossfade chain if >1
    if len(pieces_a) == 1:
        aud = pieces_a[0]
    else:
        # simple concat demuxer for audio (hard cuts; VO chapter boundaries)
        lst_a = WORK / 'list_a.txt'
        lst_a.write_text(''.join(f"file '{p}'\n" for p in pieces_a))
        aud = WORK / 'audio.m4a'
        run(['ffmpeg','-loglevel','error','-y','-f','concat','-safe','0','-i',str(lst_a),
             '-c:a','aac','-b:a','160k',str(aud)])

    run(['ffmpeg','-loglevel','error','-y','-i',str(vid),'-i',str(aud),
         '-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','160k',
         '-shortest', str(MASTER)])
    # share + chat encodes
    run(['ffmpeg','-loglevel','error','-y','-i',str(MASTER),
         '-c:v','libx264','-preset','fast','-crf','28','-pix_fmt','yuv420p',
         '-c:a','aac','-b:a','96k', str(SHARE)])
    run(['ffmpeg','-loglevel','error','-y','-i',str(MASTER),
         '-c:v','libx264','-preset','fast','-crf','32','-pix_fmt','yuv420p',
         '-c:a','aac','-b:a','64k','-movflags','+faststart', str(CHAT)])

    md = probe(MASTER)
    (WORK / 'meta.json').write_text(json.dumps(meta, ensure_ascii=False, indent=2))
    print('MASTER', MASTER, f'{md:.2f}s', MASTER.stat().st_size, flush=True)
    print('SHARE', SHARE, SHARE.stat().st_size, flush=True)
    print('CHAT', CHAT, CHAT.stat().st_size, flush=True)
    print('LENGTH_VS_CUT7', f'{md:.1f}s vs 865s (Cut7); delta={md-865:.1f}s', flush=True)

if __name__ == '__main__':
    main()
