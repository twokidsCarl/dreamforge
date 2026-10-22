"""Round 17 (PROMPT 第 17 轮, 2026-10-23): subject animation — each shot's subject gets its own action (2.5D,
procedural: no generated video, no texture boiling).  Kept only if both calibrated reviewers re-score it higher.
Narration NOT changed."""
import sys, os, math; sys.path.insert(0, '/workspace/e2work/v8/tools')
import numpy as np, cv2
import sf_r17 as R17
from sf_r17 import S, R16, R15, R14, R12, R11, R10, _wrapped
TRY = set(x for x in os.environ.get('R17_TRY', '').split(',') if x)
ACCEPT = {'SF04', 'SF05', 'SF03', 'SF11', 'SF10', 'MID', 'SF08'}   # SF08 91.05->91.20 / 91.00->91.10; MID: SF04 90.25->90.60 / 90.65->91.00; SF05 91.40->91.55 / 91.60->91.75
# re-scores (A / B): SF04 90.10->90.25 / 90.50->90.65; SF05 91.10->91.40 / 91.45->91.60;
#                    SF03 92.30->92.55 / 91.25->91.50; SF11 91.15->91.15 / 91.00->91.15;
#                    SF10 2.5D lobe mouse vs R16 version 90.90->91.05 / 89.80->89.90 (k76->kra75 rise morph ghosted -> not used)
TNOW = [0.0]

# ------------------------------------------------------------------------------------------------
# 2.5D head motion on the portrait layer: rotation about the neck, weight fading to 0 below the neck (shoulders fixed)
# ------------------------------------------------------------------------------------------------
def head_warp(im, msk, pivot, ang_deg, dy, neck_y, band=0.14):
    h, w = im.shape[:2]
    k = ('hw_grid', h, w)
    if k not in R12._cache: R12._cache[k] = np.mgrid[0:h, 0:w].astype(np.float32)
    yy, xx = R12._cache[k]
    wgt = np.clip((neck_y*h-yy)/(band*h), 0, 1); wgt = wgt*wgt*(3-2*wgt)
    a = math.radians(ang_deg)*wgt; px, py = pivot[0]*w, pivot[1]*h
    ca, sa = np.cos(a), np.sin(a)
    sx = px+(xx-px)*ca+(yy-py)*sa; sy = py-(xx-px)*sa+(yy-py)*ca-dy*h*wgt          # inverse map
    im2 = cv2.remap(im, sx, sy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    m2 = cv2.remap(msk, sx, sy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    return im2, m2
ANIM = {}           # key -> function(t) -> (angle_deg, dy, rim)
PIV = {}            # key -> (pivot, neck_y)
_pv_prev = R12.port_view
def port_view17(key, Wc, Hc, zoom, cx, cy, par):
    if key not in ANIM: return _pv_prev(key, Wc, Hc, zoom, cx, cy, par)
    im, ground, msk = R12.port_split(key)
    ang, dy, rim = ANIM[key](TNOW[0]); pivot, neck = PIV[key]
    im2, m2 = head_warp(im, msk, pivot, ang, dy, neck)
    B = R12._cam0(ground, Wc, Hc, zoom=zoom, cx=cx, cy=cy)
    Fg = R12._cam0(im2, Wc, Hc, zoom=zoom*par, cx=cx, cy=cy)
    M = R12._cam0(np.repeat(m2[..., None], 3, 2), Wc, Hc, zoom=zoom*par, cx=cx, cy=cy)[..., :1]
    out = B*(1-M)+Fg*M
    if rim > 0:                                         # rim light along the silhouette (lights up the person)
        e = np.clip(M[..., 0]-cv2.erode(M[..., 0], np.ones((7, 7), np.uint8)), 0, 1)
        e = cv2.GaussianBlur(e, (0, 0), 3)
        out = np.clip(out+e[..., None]*np.array([0.45, 0.8, 1.0])*0.9*rim, 0, 1)
    return out
R12.port_view = port_view17
def _timed(fn):
    def g(t, W, H):
        TNOW[0] = t; return fn(t, W, H)
    g._r11 = True; return g

def _ease(x): return R12.ease(min(1.0, max(0.0, x)))
# SF04: Crick lifts his head toward the quote as it appears (0.8-2.0 s), then a small nod at "相当牵强" (2.6-3.6 s)
def crick_anim(t):
    up = _ease((t-0.8)/1.2); nod = math.sin(math.pi*min(1, max(0, (t-2.6)/1.0)))
    return (-4.0*up+2.2*nod, 0.014*up-0.010*nod, 0.0)
# SF05: each laureate lights up (rim light) and nods at the moment his contribution icon lights (1.6 + 0.75 i)
def laureate_anim(i):
    def f(t):
        tl = 1.6+i*0.75; x = (t-tl+0.35)/0.9
        nod = math.sin(math.pi*min(1, max(0, x))) if 0 < x < 1 else 0.0
        rim = _ease((t-tl+0.3)/0.4)*(0.55+0.45*math.exp(-max(0, t-tl-0.2)/0.6))
        return (2.8*nod*(1 if i != 1 else -1), -0.008*nod, 1.4*rim)
    return f

def apply_sf04():
    ANIM['sf04h_crick'] = crick_anim; PIV['sf04h_crick'] = ((0.52, 0.70), 0.70)
    f, d = S['SF04_crick_quote']; S['SF04_crick_quote'] = (_timed(f), d)
def apply_sf05():
    for i, k in enumerate(('sf05h_deisseroth', 'sf05h_hegemann', 'sf05h_nagel')):
        ANIM[k] = laureate_anim(i); PIV[k] = ((0.50, 0.66), 0.68)
    src = R15._s5
    for o, n in (("a = ramp(t, 0.2+i*0.3, 0.9+i*0.3)", "a = ramp(t, 0.0+i*0.22, 0.6+i*0.22)"),
                 ("k = ease(ramp(t, 0.5, 1.3))", "k = 1.0")):                 # badge: fades in at the title bar, never crosses a face
        assert o in src, o; src = src.replace(o, n)
    exec(compile(src, 'sf_r18_sf05', 'exec'), R12.__dict__)
    S['SF05_nobel_portraits'] = (_timed(_wrapped('SF05_nobel_portraits', R12.S['SF05_nobel_portraits'][0])), 5.0)
def apply():
    if 'SF04' in TRY or 'SF04' in ACCEPT: apply_sf04()
    if 'SF05' in TRY or 'SF05' in ACCEPT: apply_sf05()
apply()

# ---- SF03: the eyespot channel (right magnifier) opens when light arrives: pores glow, cations stream through ----
def _ov_sf03(fn):
    def g(t, W, H):
        rgb = fn(t, W, H); s = W/1280; a = R12.ramp(t, 3.5, 3.9)
        if a <= 0: return rgb
        C = (1110*s, 440*s); RR = 108*s; L = R12.Layer(W, H)
        for j, px in enumerate((1070*s, 1162.5*s)):
            L.line([(px, 392*s), (px, 488*s)], fill=(150, 230, 255), width=3.2*s, alpha=0.55*a*(0.8+0.2*math.sin(t*6+j)))
            for n in range(5):
                p = (t*0.85+n/5+j*0.37) % 1.0; y = 372*s+(512*s-372*s)*p; x = px+1.5*s*math.sin(n*2.1+t*5)
                if math.hypot(x-C[0], y-C[1]) < RR-8*s:
                    L.dot((x, y), 4.2*s, fill=(255, 209, 102), alpha=a*min(1, p*6)*min(1, (1-p)*6))
        return np.clip(R12.over(rgb, L.get(), shadow=0, glow_amt=0.7), 0, 1)
    g._r11 = True; return g
# ---- SF11: each ganglion-cell flash sends a spike along its axon (firing -> conduction toward the optic nerve) ----
RGC = ((0.18, 0.23), (0.47, 0.23), (0.82, 0.23))
def _ov_sf11(fn):
    def g(t, W, H):
        rgb = fn(t, W, H); s = W/1280
        if t < 2.6: return rgb
        C = (1010*s, 545*s); R = 140*s; IP = lambda x, y: (C[0]+(x-0.5)*2*R, C[1]+(y-0.5)*2*R)
        L = R12.Layer(W, H)
        for j, (rx, ry) in enumerate(RGC):
            ph = ((t-2.6-j*0.12) % 0.8)/0.8
            q = ph/0.6
            if q >= 1: continue
            for k in range(4):                                   # spike head + short trail
                qq = q-k*0.05
                if qq < 0: continue
                X, Y = IP(rx+0.30*qq, 0.238)
                if math.hypot(X-C[0], Y-C[1]) < R-6*s:
                    L.dot((X, Y), (7.0-k*1.6)*s, fill=(235, 252, 255), alpha=R12.ramp(t, 2.6, 2.9)*min(1.0, 1.6*(1-qq))*(1-0.25*k))
        return np.clip(R12.over(rgb, L.get(), shadow=0, glow_amt=1.0), 0, 1)
    g._r11 = True; return g
if 'SF03' in TRY or 'SF03' in ACCEPT:
    f, d = S['SF03_microbe_clues']; S['SF03_microbe_clues'] = (_ov_sf03(f), d)
if 'SF11' in TRY or 'SF11' in ACCEPT:
    f, d = S['SF11_eye_goggles']; S['SF11_eye_goggles'] = (_ov_sf11(f), d)

# ---- SF10 candidate: 2.5D lobe-built mouse (tools/sf10_lobe25d.py -> gen/vid/sf10_lobe25d.mp4, 24 fps, scene timing) ----
def src10_17(t):
    return R12._fat('sf10_lobe25d', t*24)
def cam17(t):
    z = math.exp(0.034*t); hx = 0.5/z; hh = 0.4219/z
    cx = 0.47-0.02*R12.ease(min(1.0, max(0.0, (t-4.0)/5.0))); cy = 0.46
    return z, min(max(cx, hx+0.004), 1-hx-0.004), min(max(cy, hh+0.004), 1-hh-0.004)
def apply_sf10():
    R10.CAM14 = cam17
    R10.frame10 = lambda ct: np.clip(R12.src10(ct), 0, 1).astype(np.float32)       # no Wan glow -> no HSV patch
    R11.rerun10('sf10', [
        ("circ_img(img('sf10_orexin'), r, zoom=1.15+0.05*lin(t, 3), cx=0.5, cy=0.47)", "circ_img(_orx11(), r, zoom=1.55+0.10*lin(t, 3), cx=0.73, cy=0.53)"),
        ("radial(W, H, C[0], C[1]-6*s, 70*s, CYAN, 0.5*pl*a)", "radial(W, H, C[0]+4*s, C[1]+4*s, 46*s, CYAN, 0.55*pl*a)"),
        ("L = Layer(W, H); C = (1100*s, 250*s); R = int(138*s)", "L = Layer(W, H); C = (205*s, 352*s); R = int(116*s)"),
        ("z = 1.04+0.05*lin(t, SF10_D); cxx = 0.55-0.05*lin(t, SF10_D); cyy = 0.50", "z, cxx, cyy = CAM14(t)"),
        ("cx_, cy_ = W*0.36, 112*s+120*s", "cx_, cy_ = W*0.74, 150*s"),
        ("L2.text((C[0], C[1]+R+34*s), '下丘脑外侧 · 食欲素神经元'", "plate_text(L2, (C[0], C[1]+R+34*s), '下丘脑外侧 · 食欲素神经元'"),
        ("L2.text((C[0], C[1]+R+62*s), '膜上装了光控通道，随光脉冲放电'", "plate_text(L2, (C[0]+6*s, C[1]+R+66*s), '膜上装了光控通道，随光脉冲放电'"),
        ("[('睡眠中', (150, 160, 190), 0.0, 2.9), ('醒来', GOLD, 2.9, 6.3), ('醒来后走动', GOLD, 6.3, 99)]",
         "[('睡眠中', (150, 160, 190), 0.0, 3.7), ('醒来', GOLD, 3.7, 99)]"),
    ])
    f = _wrapped('SF10_mouse_tripo', R10.S['SF10_mouse_tripo'][0])
    def g(t, W, H):
        if R12.src10 is not src10_17:
            R12.src10 = src10_17; R12._cache.pop('trk12', None)
        return f(t, W, H)
    g._r11 = True
    S['SF10_mouse_tripo'] = (g, R10.SF10_D)
if 'SF10' in TRY or 'SF10' in ACCEPT: apply_sf10()

# ---- SF04/SF05 'middle setting': lobes ~40 % smaller + inked features (r17_*_mid_ink) ----
MID = {'sf04h_crick': 'r17_crick_mid_ink', 'sf05h_deisseroth': 'r17_mid_deisseroth_ink', 'sf05h_hegemann': 'r17_mid_hegemann_ink', 'sf05h_nagel': 'r17_mid_nagel_ink'}
if 'MID' in TRY or 'MID' in ACCEPT:
    _psm = R12.port_split
    def _psmid(k):
        return _psm(MID.get(k, k))
    R12.port_split = _psmid

# ---- SF08: labels accumulate instead of all clearing and coming back; final frame holds 3 groups ----
def sf08_v17():
    orig = R14._s8; s8 = orig
    for o, n in (("'路线一：好几步接力', '感光蛋白 → 中间几步 → 通道', t=ramp(t, 4.9, 5.5)", "'路线一：好几步接力', '感光蛋白 → 中间几步 → 通道', t=ramp(t, 3.1, 3.6)"),
                 ("'受紫光弯折 → 通道打开', None, t=ramp(t, 5.4, 6.0)", "'受紫光弯折 → 通道打开', None, t=ramp(t, 5.4, 6.0)*(1-ramp(t, 6.4, 6.8))")):
        assert o in s8, o; s8 = s8.replace(o, n)
    R14._s8 = s8
    try: return R17.sf08_v16()
    finally: R14._s8 = orig
if 'SF08' in TRY or 'SF08' in ACCEPT:
    S['SF08_early_attempts'] = (sf08_v17(), 7.0)
