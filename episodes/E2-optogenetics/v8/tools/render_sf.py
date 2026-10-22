import sys; sys.path.insert(0,'/workspace/e2work/v8/tools')
import sf_scenes as S, sf
names=[a for a in sys.argv[1:] if not a.startswith('--')] or list(S.S); mode='both'
for n in names:
    fn,dur=S.S[n]
    sf.save(fn(dur*(0.97 if n[:4] in ('SF06','SF08') else 0.8),1280,720),f'/workspace/e2work/v8/styleframes/{n}.png')
    if '--still' not in sys.argv:
        sf.write_video(lambda i:fn(i/24,960,540),int(dur*24),f'/workspace/e2work/v8/styleframes/{n}.mp4',960,540)
    print('done',n,flush=True)
