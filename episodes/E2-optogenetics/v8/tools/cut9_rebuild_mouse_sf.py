#!/usr/bin/env python3
"""Rebuild SF10/14/18/19 forward-only from graded clips (no ping-pong reverse)."""
import subprocess
from pathlib import Path

GRAD = Path('/workspace/e2work/v8/cut9/graded')
OUT = Path('/workspace/e2work/v8/styleframes')
W, H, FPS = 1280, 720, 24

def run(cmd):
    print('+', ' '.join(str(c) for c in cmd[:8]), '...')
    subprocess.run(cmd, check=True)

def probe(p):
    return float(subprocess.check_output(
        ['ffprobe','-v','error','-show_entries','format=duration','-of','default=nk=1:nw=1',str(p)], text=True))

def scale(inp, out):
    run(['ffmpeg','-loglevel','error','-y','-i',str(inp),
         '-vf',f'scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2,fps={FPS},format=yuv420p',
         '-c:v','libx264','-preset','fast','-crf','18','-an',str(out)])

def hold_last(inp, extra, out):
    """Append freeze of last frame for `extra` seconds."""
    run(['ffmpeg','-loglevel','error','-y','-i',str(inp),
         '-vf',f'tpad=stop_mode=clone:stop_duration={extra:.3f}',
         '-c:v','libx264','-preset','fast','-crf','18','-an',str(out)])

def concat(paths, out):
    lst = out.with_suffix('.txt')
    lst.write_text(''.join(f"file '{p}'\n" for p in paths))
    run(['ffmpeg','-loglevel','error','-y','-f','concat','-safe','0','-i',str(lst),
         '-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-an',str(out)])

def badge_overlay(inp, out, chapter, title, title_s=2.5):
    # drawtext minimal badge
    # escape for ffmpeg
    def esc(s): return s.replace(':','\\:').replace("'","\\'")
    vf = (
      f"drawbox=x=18:y=16:w=160:h=26:color=black@0.75:t=fill,"
      f"drawtext=fontfile=/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc:text='EIGENLENS · 02':"
      f"x=28:y=20:fontsize=14:fontcolor=0xECE6D6,"
      f"drawtext=fontfile=/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc:text='{esc(chapter)}':"
      f"x=190:y=20:fontsize=13:fontcolor=0x5AC8E6:enable='lt(t,{title_s+0.5})',"
      f"drawtext=fontfile=/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc:text='{esc(title)}':"
      f"x=(w-text_w)/2:y=64:fontsize=26:fontcolor=0xECE6D6:box=1:boxcolor=black@0.55:boxborderw=8:enable='lt(t,{title_s})'"
    )
    run(['ffmpeg','-loglevel','error','-y','-i',str(inp),'-vf',vf,
         '-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-an',str(out)])

work = Path('/workspace/e2work/v8/cut9/_mouse_rebuild')
work.mkdir(exist_ok=True)

# --- SF10 15s: sleep(4) + sideA(5) + side(4) + front hold to 15
parts = []
for name, src in [('sleep','c9_msleep_c'),('sideA','c9_mouseA_clip'),('side','c9_mside_c'),('front','c9_mfront_c')]:
    s = work/f'sf10_{name}.mp4'; scale(GRAD/f'{src}.mp4', s); parts.append(s)
raw = work/'sf10_raw.mp4'; concat(parts, raw)
# trim/pad to 15s
d = probe(raw)
if d < 15:
    hold_last(raw, 15-d, work/'sf10_len.mp4')
else:
    run(['ffmpeg','-loglevel','error','-y','-i',str(raw),'-t','15','-c:v','copy',str(work/'sf10_len.mp4')])
badge_overlay(work/'sf10_len.mp4', OUT/'SF10_mouse_tripo.mp4', '活体', '下丘脑食欲素神经元 · 蓝光唤醒', 2.5)
run(['ffmpeg','-loglevel','error','-y','-ss','3','-i',str(OUT/'SF10_mouse_tripo.mp4'),'-frames:v','1',str(OUT/'SF10_mouse_tripo.png')])
print('SF10', probe(OUT/'SF10_mouse_tripo.mp4'))

# --- SF14 16s: sleep + side + front
parts = []
for name, src in [('sleep','c9_msleep_c'),('side','c9_mside_c'),('front','c9_mfront_c'),('oh','c9_moh_c')]:
    s = work/f'sf14_{name}.mp4'; scale(GRAD/f'{src}.mp4', s); parts.append(s)
raw = work/'sf14_raw.mp4'; concat(parts, raw)
d = probe(raw)
run(['ffmpeg','-loglevel','error','-y','-i',str(raw),'-t','16',
     '-vf' if d<16 else '-c:v', *( [f'tpad=stop_mode=clone:stop_duration={16-d:.3f}','-c:v','libx264','-preset','fast','-crf','18','-an'] if d<16 else ['copy'] ),
     str(work/'sf14_len.mp4')])
badge_overlay(work/'sf14_len.mp4', OUT/'SF14_orexin_q.mp4', '2007', '光纤蓝光：睡眠 → 清醒', 2.5)
print('SF14', probe(OUT/'SF14_orexin_q.mp4'))

# --- SF18 30s: oh + side + front + yellow + close + sideA + hold
parts = []
for name, src in [('oh','c9_moh_c'),('side','c9_mside_c'),('front','c9_mfront_c'),
                  ('yellow','c9_myellow_c'),('close','c9_mclose_c'),('sideA','c9_mouseA_clip'),('sleep','c9_msleep_c')]:
    s = work/f'sf18_{name}.mp4'; scale(GRAD/f'{src}.mp4', s); parts.append(s)
raw = work/'sf18_raw.mp4'; concat(parts, raw)
d = probe(raw)
if d < 30:
    hold_last(raw, 30-d, work/'sf18_len.mp4')
else:
    run(['ffmpeg','-loglevel','error','-y','-i',str(raw),'-t','30','-c:v','copy',str(work/'sf18_len.mp4')])
badge_overlay(work/'sf18_len.mp4', OUT/'SF18_invivo_dual.mp4', '活体', '蓝开 · 黄关', 2.5)
print('SF18', probe(OUT/'SF18_invivo_dual.mp4'))

# --- SF19 30s
parts = []
for name, src in [('oh','c9_moh_c'),('sideA','c9_mouseA_clip'),('front','c9_mfront_c'),
                  ('side','c9_mside_c'),('close','c9_mclose_c'),('yellow','c9_myellow_c'),('sleep','c9_msleep_c')]:
    s = work/f'sf19_{name}.mp4'; scale(GRAD/f'{src}.mp4', s); parts.append(s)
raw = work/'sf19_raw.mp4'; concat(parts, raw)
d = probe(raw)
if d < 30:
    hold_last(raw, 30-d, work/'sf19_len.mp4')
else:
    run(['ffmpeg','-loglevel','error','-y','-i',str(raw),'-t','30','-c:v','copy',str(work/'sf19_len.mp4')])
badge_overlay(work/'sf19_len.mp4', OUT/'SF19_engram.mp4', '记忆', '海马齿状回 · 虚假恐惧记忆', 2.5)
print('SF19', probe(OUT/'SF19_engram.mp4'))
print('DONE')
