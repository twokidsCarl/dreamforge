"""Round 19 variant: same as sf07_sym18 but the fibre is NOT painted into the plate (gen/sf07k_brain.png) —
the scene draws it and animates its insertion.  Round 18 SF07: dorsal brain made bilaterally symmetric — the clean lower half of sf07h_brain mirrored onto the
upper half (fibre + cyan network then redrawn procedurally, nothing inpainted) about the midline (y = 0.482), a thin dark
midline fissure drawn between the hemispheres.  -> gen/sf07j_brain.png"""
import cv2, numpy as np
G = '/workspace/e2work/v8/gen/'
im = cv2.imread(G+'sf07h_brain.png'); h, w = im.shape[:2]; ym = int(0.482*h)
# remove the original network's spill below the midline (small, thin -> recolour to the local cortex tone)
hsv0 = cv2.cvtColor(im, cv2.COLOR_BGR2HSV).astype(int)
cy0 = ((hsv0[..., 0] > 78) & (hsv0[..., 0] < 112) & (hsv0[..., 1] > 40) & (hsv0[..., 2] > 120)).astype(np.uint8)
cy0[:ym] = 0; cy0 = cv2.dilate(cy0, np.ones((7, 7), np.uint8))
im = cv2.inpaint(im, cy0*255, 5, cv2.INPAINT_TELEA)
low = im[ym:2*ym]                                    # lower hemisphere: no fibre, no network
up = low[::-1]; n = up.shape[0]
out = im.copy(); y0 = ym-n
wgt = np.ones((n, 1, 1), np.float32); k = int(0.01*h); wgt[-k:, 0, 0] = np.linspace(1, 0, k)    # soft seam at the midline
kt = int(0.04*h); wgt[:kt, 0, 0] = np.linspace(0, 1, kt)
out[max(0, y0):ym] = (up[max(0, -y0):]*wgt[max(0, -y0):]+im[max(0, y0):ym]*(1-wgt[max(0, -y0):])).astype(np.uint8)
# midline fissure over the cerebral hemispheres
x0, x1 = int(0.245*w), int(0.585*w)
L = np.zeros((h, w), np.float32); cv2.line(L, (x0, ym), (x1, ym), 1.0, 3, cv2.LINE_AA); L = cv2.GaussianBlur(L, (0, 0), 1.2)
xx = np.arange(w)[None, :]; fade = np.clip(np.minimum((xx-x0)/(0.04*w), (x1-xx)/(0.04*w)), 0, 1)
L = (L*fade)[..., None]
out = (out*(1-0.8*L)+np.array([60, 20, 30])*0.8*L).astype(np.uint8)
cv2.imwrite(G+'sf07j_base.png', out); print('ok', ym)
# fibre + cyan network on the upper hemisphere, drawn procedurally (same method as tools/sf07_brain13.py)
import importlib.util, sys
src = open('/workspace/e2work/v8/tools/sf07_brain13.py').read()
src = src.replace("Image.open(G+'r13_sf07_brain.png')", "Image.open(G+'sf07j_base.png')").replace("BT = (0.420, 0.300)", "BT = (0.426, 0.255)")
src = src.replace("cortex[int(0.475*h):] = False; cortex[:, :int(0.215*w)] = False; cortex[:, int(0.585*w):] = False",
                  "cortex[int(0.47*h):] = False; cortex[:, :int(0.22*w)] = False; cortex[:, int(0.60*w):] = False")
src = src.replace("fib.save(G+'sf07i_brain.png')", "fib.save(G+'sf07k_brain.png')").replace("fd.rectangle", "(lambda *a, **k: None)").replace("fd.rectangle", "(lambda *a, **k: None)")
exec(compile(src, 'sf07_net', 'exec'), {'__name__': 'x'})
