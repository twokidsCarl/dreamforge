"""Round 15 SF10 candidate: family treatment of the mouse on the source frames — dark indigo ink contour where the
silhouette meets the bedding/background, soft cyan-violet rim light on the upper edges (light from the fibre side)."""
import numpy as np, cv2
def mouse_mask(f):
    u8 = (np.clip(f, 0, 1)*255).astype(np.uint8); hsv = cv2.cvtColor(u8, cv2.COLOR_RGB2HSV)
    m = ((hsv[..., 2] < 118) & (hsv[..., 1] < 150) & ~((hsv[..., 0] > 5) & (hsv[..., 0] < 35) & (hsv[..., 1] > 90))).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(m)
    if n <= 1: return None
    k = 1+int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
    if st[k, cv2.CC_STAT_AREA] < 0.02*m.size: return None
    m = (lab == k).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((21, 21), np.uint8))
    ff = m.copy(); h, w = m.shape; pad = np.zeros((h+2, w+2), np.uint8)
    for seed in ((0, 0), (w-1, 0), (0, h-1), (w-1, h-1)):
        if ff[seed[1], seed[0]] == 0: cv2.floodFill(ff, pad, seed, 2)
    return (ff != 2).astype(np.uint8)
def stylize(f, amt=1.0):
    m = mouse_mask(f)
    if m is None: return f
    mf = cv2.GaussianBlur(m.astype(np.float32), (0, 0), 1.0)
    # ink contour just outside the silhouette
    ring = np.clip(cv2.GaussianBlur(cv2.dilate(m, np.ones((5, 5), np.uint8)).astype(np.float32), (0, 0), 1.2)-mf, 0, 1)
    out = f*(1-0.75*amt*ring[..., None])+np.array([0.04, 0.03, 0.10])*0.75*amt*ring[..., None]
    # rim light inside the silhouette, stronger on edges whose outward normal points up / up-right
    d = cv2.distanceTransform(m, cv2.DIST_L2, 5)
    band = np.exp(-d/3.5)*m
    gy = cv2.Sobel(mf, cv2.CV_32F, 0, 1, ksize=7); gx = cv2.Sobel(mf, cv2.CV_32F, 1, 0, ksize=7)
    nrm = np.sqrt(gx*gx+gy*gy)+1e-6; up = np.clip((gy*0.85-gx*0.35)/nrm, 0, 1)        # outward normal = -grad
    up = cv2.GaussianBlur(up, (0, 0), 3)
    rim = band*(0.25+0.75*up)
    out = out+rim[..., None]*np.array([0.35, 0.62, 1.0])*0.55*amt
    return np.clip(out, 0, 1).astype(np.float32)
