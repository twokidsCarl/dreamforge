"""Round 19: de-lump the face skin of a lobe portrait — skin mask (warm ochre hues inside the figure, upper part),
mean-shift + bilateral smoothing, 3-tone warm quantisation; dark feature lines (eyes, brows, lids, mouth, wrinkles)
and highlights from the original are kept on top.  Hair and clothes untouched.
usage: face_smooth19.py SRC_KEY OUT_KEY"""
import sys, cv2, numpy as np
G = '/workspace/e2work/v8/gen/'
src, dst = sys.argv[1], sys.argv[2]
im = cv2.imread(G+src+'.png'); h, w = im.shape[:2]
hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV).astype(np.int32)
YMAX = float(sys.argv[3]) if len(sys.argv) > 3 else 0.62
skin = ((hsv[..., 0] >= 8) & (hsv[..., 0] <= 30) & (hsv[..., 1] > 70) & (hsv[..., 2] > 130)).astype(np.uint8)
skin[int(YMAX*h):] = 0
skin = cv2.morphologyEx(skin, cv2.MORPH_CLOSE, np.ones((21, 21), np.uint8))
skin = cv2.morphologyEx(skin, cv2.MORPH_OPEN, np.ones((9, 9), np.uint8))          # cut thin bridges to the membrane
n, lab, st, _ = cv2.connectedComponentsWithStats(skin)
k = 1+int(np.argmax(st[1:, cv2.CC_STAT_AREA]))                                   # the face = largest component
skin = cv2.morphologyEx((lab == k).astype(np.uint8), cv2.MORPH_CLOSE, np.ones((31, 31), np.uint8))
ff = skin.copy(); pad = np.zeros((h+2, w+2), np.uint8)
# fill holes (eyes, mouth inside the face region)
inv = (1-skin).astype(np.uint8); n2, lab2, st2, _ = cv2.connectedComponentsWithStats(inv)
for i in range(1, n2):
    x, y, ww, hh, a = st2[i]
    if a < 0.0025*h*w and x > 0 and y > 0 and x+ww < w and y+hh < h: skin[lab2 == i] = 1
sm = cv2.pyrMeanShiftFiltering(im, 26, 46)
for _ in range(4): sm = cv2.bilateralFilter(sm, 15, 60, 15)
lab_ = cv2.cvtColor(sm, cv2.COLOR_BGR2LAB).astype(np.float32)
L = lab_[..., 0]; lv = np.percentile(L[skin > 0], [20, 55, 85])
q = np.where(L < (lv[0]+lv[1])/2, lv[0], np.where(L < (lv[1]+lv[2])/2, lv[1], lv[2]))
L2 = cv2.GaussianBlur(0.55*cv2.GaussianBlur(q.astype(np.float32), (0, 0), 7)+0.45*cv2.GaussianBlur(L, (0, 0), 9), (0, 0), 2.0)
lab_[..., 0] = L2
flat = cv2.GaussianBlur(cv2.cvtColor(np.clip(lab_, 0, 255).astype(np.uint8), cv2.COLOR_LAB2BGR).astype(np.float32), (0, 0), 3.0)
# keep dark feature lines and highlights from the original
g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY).astype(np.float32); loc = cv2.GaussianBlur(g, (0, 0), 6)
dark = np.clip((95-g)/30, 0, 1)*np.clip((loc-g-20)/20, 0, 1)        # only genuinely dark features (eyes, pupils, deep creases)
hi = np.clip((g-loc-45)/25, 0, 1)
feat = np.clip(cv2.GaussianBlur(np.maximum(dark, hi), (0, 0), 0.8)*1.3, 0, 1)
m = cv2.GaussianBlur(skin.astype(np.float32), (0, 0), 3)[..., None]
f = feat[..., None]
face = flat*(1-f)+im.astype(np.float32)*f
# ink only the face outline (the skin mask border) — no interior lobe borders
edge = np.clip(cv2.dilate(skin, np.ones((3, 3), np.uint8)).astype(np.float32)-cv2.erode(skin, np.ones((3, 3), np.uint8)).astype(np.float32), 0, 1)
ed = cv2.GaussianBlur(edge, (0, 0), 0.9)[..., None]
face = face*(1-0.5*ed)+np.array([40, 15, 18])*0.5*ed
out = im.astype(np.float32)*(1-m)+face*m
cv2.imwrite(G+dst+'.png', np.clip(out, 0, 255).astype(np.uint8)); print('ok', dst, int(skin.sum()))
