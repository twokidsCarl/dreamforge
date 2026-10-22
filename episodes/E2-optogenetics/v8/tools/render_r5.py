import sys; sys.path.insert(0,'/workspace/e2work/v8/tools')
import importlib, sf; R=importlib.import_module(next((a.split('=')[1] for a in sys.argv if a.startswith('--mod=')),'sf_r5'))
S=R.S; out=sys.argv[sys.argv.index('--out')+1] if '--out' in sys.argv else '/workspace/e2work/v8/styleframes'
names=[a for a in sys.argv[1:] if not a.startswith('--') and a!=out] or list(S)
for n in names:
    fn,dur=S[n]
    if '--times' in sys.argv:
        for tt in (0.4,1.2,2.2,3.2,4.2,dur-0.05):
            sf.save(fn(min(tt,dur-0.05),960,540),f'{out}/{n}_t{tt:.1f}.png')
        print('times',n,flush=True); continue
    sf.save(fn(dur*(0.97 if n[:4] in ('SF06','SF08') else 0.8),1280,720),f'{out}/{n}.png')
    if '--still' not in sys.argv:
        sf.write_video(lambda i:fn(i/24,960,540),int(dur*24),f'{out}/{n}.mp4',960,540)
    print('done',n,flush=True)
