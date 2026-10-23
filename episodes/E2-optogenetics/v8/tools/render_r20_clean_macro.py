"""Re-render SF04/SF05 with clean illustration portraits (no lobe/beads on people).
Uses r20_clean_* plates; keeps scene layout/overlays from r18 pipeline.
"""
import os, sys
sys.path.insert(0, '/workspace/e2work/v8/tools')
os.environ['R17_TRY'] = ''  # don't override ACCEPT from env oddly

import sf_r18 as R18
import sf_scenes as S
import sf
import sf_r12 as R12

CLEAN = {
    'sf04h_crick': 'r20_clean_crick',
    'sf05h_deisseroth': 'r20_clean_deisseroth',
    'sf05h_hegemann': 'r20_clean_hegemann',
    'sf05h_nagel': 'r20_clean_nagel',
}
# Also map MID keys if active
for k, v in list(CLEAN.items()):
    CLEAN[v] = v

_ps = R12.port_split
def _ps_clean(key):
    return _ps(CLEAN.get(key, key))
R12.port_split = _ps_clean
# clear port_split cache
for k in list(R12._cache):
    if isinstance(k, tuple) and k and k[0] == 'ps12':
        R12._cache.pop(k, None)

OUT = '/workspace/e2work/v8/styleframes/'
names = [a for a in sys.argv[1:] if not a.startswith('--')] or ['SF04_crick_quote', 'SF05_nobel_portraits']
for n in names:
    fn, dur = S.S[n]
    still_t = dur * (0.97 if n[:4] in ('SF06', 'SF08') else 0.8)
    sf.save(fn(still_t, 1280, 720), f'{OUT}/{n}.png')
    sf.write_video(lambda i, fn=fn, dur=dur: fn(i / 24, 960, 540), int(round(dur * 24)), f'{OUT}/{n}.mp4', 960, 540)
    print('done', n, flush=True)
