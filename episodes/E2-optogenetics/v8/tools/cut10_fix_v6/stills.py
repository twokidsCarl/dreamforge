import sys, time
sys.argv=['x']
import rebuild_v6 as R
from PIL import Image, ImageDraw
import numpy as np
ts=[float(x) for x in open(sys.stdin.fileno()).read().split()]
out=sys.argv[0]
ims=[]
for t in ts:
    t0=time.time()
    fn=None
    for n,f in R.CHUNKS:
        f0,f1=R.frames_of(n)
        if f0<=round(t*24)<f1: fn=f
    rgb=fn(t)
    im=Image.fromarray((np.clip(rgb,0,1)*255).astype(np.uint8))
    im.save(f'stills/t{t:07.2f}.png')
    print(t, round(time.time()-t0,2), flush=True)
