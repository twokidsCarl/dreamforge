import sys; sys.path.insert(0, '/workspace/e2work/v8/tools')
import sf_r20, sf_scenes as S, sf
OUT = '/workspace/e2work/v8/styleframes/'
for a in sys.argv[1:]:
    if a.startswith('--out='): OUT = a[6:]
names = [a for a in sys.argv[1:] if not a.startswith('--')] or sorted(S.S)
for n in names:
    fn, dur = S.S[n]
    sf.save(fn(dur*(0.97 if n[:4] in ('SF06', 'SF08') else 0.8), 1280, 720), f'{OUT}/{n}.png')
    if '--still' not in sys.argv:
        sf.write_video(lambda i: fn(i/24, 960, 540), int(round(dur*24)), f'{OUT}/{n}.mp4', 960, 540)
    print('done', n, flush=True)
