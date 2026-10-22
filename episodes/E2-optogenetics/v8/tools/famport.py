"""Pull a gold line-art portrait into the Goodsell family: dark contour + cyan/violet glow rim + blurred molecule ground.
Silhouette by GrabCut (warm line-art pixels = probable figure, bottom-centre = figure, top corners = ground)."""
import numpy as np, cv2
_C = {}
def silhouette(key, im):
    if ('sil', key) in _C: return _C[('sil', key)]
    h, w = im.shape[:2]; sm = cv2.resize((im*255).astype(np.uint8), (w//2, h//2)); hh, ww = sm.shape[:2]
    m = np.full((hh, ww), cv2.GC_PR_BGD, np.uint8); lum = sm.mean(2); warm = sm[..., 0].astype(int)-sm[..., 2]
    m[(warm > 25) & (lum > 50)] = cv2.GC_PR_FGD
    m[int(hh*0.85):, int(ww*0.25):int(ww*0.75)] = cv2.GC_FGD
    m[:int(hh*0.08), :int(ww*0.12)] = cv2.GC_BGD; m[:int(hh*0.08), -int(ww*0.12):] = cv2.GC_BGD
    bg = np.zeros((1, 65), np.float64); fg = np.zeros((1, 65), np.float64)
    cv2.grabCut(sm, m, None, bg, fg, 6, cv2.GC_INIT_WITH_MASK)
    sil = ((m == 1) | (m == 3)).astype(np.uint8)
    sil = cv2.morphologyEx(sil, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    sil = cv2.morphologyEx(sil, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15)))
    ff = sil.copy(); pad = np.zeros((hh+2, ww+2), np.uint8)
    for seed in ((0, 0), (ww-1, 0)):
        if ff[seed[1], seed[0]] == 0: cv2.floodFill(ff, pad, seed, 2)
    sil = (ff != 2).astype(np.uint8)                      # fill interior holes (shadowed eyes, cheeks)
    sil = cv2.resize(sil.astype(np.float32), (w, h), interpolation=cv2.INTER_LINEAR)
    sil = cv2.GaussianBlur(sil, (0, 0), w*0.002); _C[('sil', key)] = sil; return sil

def fam_portrait(key, im, blobs):
    """im: float RGB portrait; blobs: float RGB family texture (resized)."""
    if key in _C: return _C[key]
    h, w = im.shape[:2]; sil = silhouette(key, im)
    dout = cv2.distanceTransform((sil < 0.5).astype(np.uint8), cv2.DIST_L2, 5)/w
    din = cv2.distanceTransform((sil >= 0.5).astype(np.uint8), cv2.DIST_L2, 5)/w
    outline = np.exp(-(dout/0.0045)**2)*(sil < 0.5)
    rim = np.exp(-(dout/0.02))*(sil < 0.5)
    inner = np.exp(-(din/0.005))*(sil >= 0.5)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    side = np.clip(1.15-0.9*(xx/w)-0.3*(yy/h), 0.25, 1.0)[..., None]          # key light from upper left
    bl = cv2.resize(blobs, (w, h), interpolation=cv2.INTER_AREA); bl = cv2.GaussianBlur(bl, (0, 0), w*0.008)
    ground = cv2.GaussianBlur(im, (0, 0), w*0.004)*0.55+bl*0.42
    S = sil[..., None]
    out = im*S+ground*(1-S)
    out = out*(1-0.9*outline[..., None])+np.array([0.03, 0.02, 0.08])*0.9*outline[..., None]
    rimc = np.array([0.30, 0.64, 1.0])*side+np.array([0.62, 0.40, 1.0])*(1-side)
    out = out+rimc*rim[..., None]*0.50
    out = out+np.array([0.35, 0.60, 1.0])*inner[..., None]*0.30*side
    _C[key] = np.clip(out, 0, 1).astype(np.float32); return _C[key]
