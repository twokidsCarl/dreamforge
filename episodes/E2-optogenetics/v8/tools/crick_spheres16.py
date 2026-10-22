"""Round 16 SF04 sample c2: the round-11 painted Crick re-rendered as packed shaded spheres (Goodsell technique),
dark indigo contours on the main shapes, only on the figure (GrabCut split from sf_r12.port_split)."""
import sys; sys.path.insert(0, '/workspace/e2work/v8/tools')
import numpy as np, cv2
def spheres(im, msk, d=9, seed=3):
    h, w = im.shape[:2]; rng = np.random.default_rng(seed)
    src = cv2.GaussianBlur(im, (0, 0), d*0.35)
    lum = src.mean(2)
    out = im.copy(); acc = np.zeros((h, w), np.float32)
    canvas = np.zeros_like(im); cov = np.zeros((h, w), np.float32)
    pts = []
    for y in range(0, h, d):
        for x in range(0, w, d):
            jx, jy = rng.uniform(-0.35, 0.35, 2)*d
            X, Y = int(x+d/2+jx), int(y+d/2+jy)
            if 0 <= X < w and 0 <= Y < h and msk[Y, X] > 0.5: pts.append((Y, X))
    pts.sort()
    r = int(d*0.68); yy, xx = np.mgrid[-r:r+1, -r:r+1].astype(np.float32); rr = np.sqrt(xx*xx+yy*yy)/r
    disk = (rr <= 1).astype(np.float32)
    nz = np.sqrt(np.clip(1-rr*rr, 0, 1))
    shade = np.clip(0.55+0.55*(nz*0.75+(-xx-yy)/r*0.28), 0.25, 1.25)          # light from upper left
    rim = np.clip((rr-0.78)/0.22, 0, 1)*disk
    for (Y, X) in pts:
        c = src[Y, X]
        y0, y1, x0, x1 = Y-r, Y+r+1, X-r, X+r+1
        if y0 < 0 or x0 < 0 or y1 > h or x1 > w: continue
        col = c[None, None, :]*shade[..., None]
        col = col*(1-0.65*rim[..., None])+np.array([0.08, 0.06, 0.18])*0.65*rim[..., None]
        m = disk[..., None]
        canvas[y0:y1, x0:x1] = canvas[y0:y1, x0:x1]*(1-m)+col*m; cov[y0:y1, x0:x1] = np.maximum(cov[y0:y1, x0:x1], disk)
    gaps = np.array([0.10, 0.08, 0.22])                                           # dark indigo between beads
    fig = canvas*cov[..., None]+gaps*(1-cov[..., None])
    # contours of the main shapes
    g = cv2.GaussianBlur((lum*255).astype(np.uint8), (0, 0), 3.0)
    ed = cv2.Canny(g, 18, 42); ed = cv2.dilate(ed, np.ones((3, 3), np.uint8)).astype(np.float32)/255
    ed = cv2.GaussianBlur(ed, (0, 0), 1.0)
    fig = fig*(1-0.7*ed[..., None])+np.array([0.06, 0.05, 0.16])*0.7*ed[..., None]
    mk = cv2.GaussianBlur(msk.astype(np.float32), (0, 0), 1.5)[..., None]
    sil = cv2.GaussianBlur(np.clip(cv2.dilate((msk > 0.5).astype(np.uint8), np.ones((7, 7), np.uint8)).astype(np.float32)-mk[..., 0], 0, 1), (0, 0), 1.5)
    out = im*(1-mk)+fig*mk
    out = out*(1-0.8*sil[..., None])+np.array([0.05, 0.04, 0.14])*0.8*sil[..., None]
    return np.clip(out, 0, 1)
if __name__ == '__main__':
    import sf_r12 as R12
    im, ground, msk = R12.port_split('sf04h_crick')
    out = spheres(im, msk)
    cv2.imwrite('/workspace/e2work/v8/gen/r16_crick_spheres.png', cv2.cvtColor((out*255).astype(np.uint8), cv2.COLOR_RGB2BGR))
    print('ok', im.shape)
