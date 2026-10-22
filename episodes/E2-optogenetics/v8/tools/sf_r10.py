"""Round 9 (PROMPT 第 9 轮, 20:50): only the round-8 independent-review Top-5, plus density / secondary motion.
1 SF05: rebuilt layout (bottom-anchored, no title crop, badge beside the reason line, no ghost); portraits redrawn
        as dark ground + gold line art + family outline (image2 sf05g_*); one contribution icon per laureate.
        SF04 portrait redrawn in the same family (sf04g_crick).
2 SF07: ions run down the two subunit pores (sf09e coordinates); title from 1.0 s and held >3 s; subtitle bright;
        an optical fibre drawn above the beam; motion from frame 0.
3 label diet: <=1 title + 3 labels on screen at once (time-staggered fades), lead protein named <1 s, >=20 px.
4 SF04: right-hand vignette is a real neuron swept by blue light that then fires (spike trace); no empty open.
  SF02: lit cells pulse in sync after they light up; field sways slightly.
5 SF10: walk/rise re-timed from de-duplicated Wan keyframes with optical-flow in-betweens (24 fps);
        the time skip is a same-camera fast-forward (no dip to dark).
  SF08: speed bar compares only light -> channel open; violet light beam drawn; azobenzene tether as a bead chain.
  Narration is NOT changed."""
import sys, os, math, re; sys.path.insert(0, '/workspace/e2work/v8/tools')
import sf, sf_scenes
import sf_r9 as R9
from sf_r9 import *          # noqa
from sf_r9 import _cache, vframes, chip_seq, family_tex, _vframes_native, _trk10, pulses
import sf_r8 as R8, sf_r7 as R7, sf_r6 as R6, sf_r5 as R5
from sf_r5 import circ_img
from sf_r8 import _ins_l3
TOOLS = '/workspace/e2work/v8/tools/'

# ------------------------------------------------------------------------------------------------
# scene clock + label diet: per-scene fade-outs / drops keyed by label title or text string
# ------------------------------------------------------------------------------------------------
_CUR = ['']; _T = [0.0]
LBL = {   # (scene, title) -> fade-out time, or None = never drawn
    ('SF09_chr2_channel', '其他膜蛋白'): None,
    ('SF09_chr2_channel', '蓝光 约 470 nm'): 2.3,
    ('SF08_early_attempts', '① 感光蛋白先接住光'): 2.3,
    ('SF08_early_attempts', '② 中间好几步接力'): 2.7,
    ('SF11_eye_goggles', '感光细胞：已大量丢失'): 2.3,
}
_label_prev = R9.label2
def label3(L, anchor_pt, text_pt, title, sub=None, **k):
    key = (_CUR[0], title)
    if key in LBL:
        if LBL[key] is None: return
        f = 1-ramp(_T[0], LBL[key], LBL[key]+0.35)
        if f <= 0: return
        if f < 1: k['t'] = min(k.get('t', 1.0), 1.0)*f
    return _label_prev(L, anchor_pt, text_pt, title, sub, **k)
for _m in list(sys.modules.values()):
    if _m is None or '/e2work/v8/tools/' not in (getattr(_m, '__file__', '') or ''): continue
    if getattr(_m, 'label', None) is _label_prev: _m.label = label3
label = label3

def src_of(path, start, end_marker='# ====', after=None):
    s = open(TOOLS+path).read(); a = s.index(start, s.index(after) if after else 0)
    b = s.index(end_marker, a+len(start)) if end_marker else len(s)
    return s[a:b]
def sub(src, old, new, count=1):
    assert old in src, ('patch target missing', old[:70]); return src.replace(old, new, count)

def fg_bokeh(W, H, t, spots, col=(40, 26, 74), rim=(120, 90, 200), blur=14):
    """foreground layer: out-of-focus Goodsell blobs at the frame edge, drifting faster than the plate (parallax)"""
    key = ('fgb', W, tuple(spots))
    if key not in _cache:
        s = W/1280; rng = np.random.default_rng(len(spots)*7+3); L = Layer(W, H)
        for (x, y, r) in spots:
            for _ in range(26):
                a = rng.uniform(0, 2*math.pi); d = rng.uniform(0, r*0.75)*s
                rr = rng.uniform(0.18, 0.34)*r*s; cx, cy = x*s+math.cos(a)*d, y*s+math.sin(a)*d
                L.dot((cx, cy), rr+3*s, fill=(14, 8, 30)); L.dot((cx-rr*0.15, cy-rr*0.2), rr, fill=col)
                L.dot((cx-rr*0.35, cy-rr*0.4), rr*0.35, fill=rim, alpha=0.5)
        a = L.get(); a = cv2.GaussianBlur(a, (0, 0), blur*s); _cache[key] = a
    a = _cache[key]; s = W/1280
    dx, dy = 22*s*math.sin(t*0.35), 10*s*math.sin(t*0.27+1)
    M = np.array([[1, 0, dx], [0, 1, dy]], np.float32)
    return cv2.warpAffine(a, M, (W, H), borderMode=cv2.BORDER_CONSTANT)

def fam_bg(W, H):
    """family backdrop without the membrane strip: the blob field above the ChR2 membrane, blurred"""
    k = ('fbg10', W, H)
    if k not in _cache:
        im = img('sf09e_chr2'); top = im[:int(0.30*im.shape[0])]
        b = cv2.GaussianBlur(cv2.resize(top, (W, H), interpolation=cv2.INTER_CUBIC), (0, 0), 6*W/1280)
        _cache[k] = b
    return _cache[k]

def plate_text(L, xy, txt, font, fill=CREAM, alpha=1.0, anchor='ms', pad=10):
    if alpha <= 0: return
    s = L.W/1280; w = font.getlength(txt); x, y = xy; fs = font.size
    x0 = x-w/2 if anchor[0] == 'm' else (x-w if anchor[0] == 'r' else x)
    L.rrect((x0-pad*s, y-fs-6*s, x0+w+pad*s, y+8*s), 6*s, fill=(11, 16, 34), alpha=0.78*alpha)
    L.text(xy, txt, font, fill=fill, alpha=alpha, anchor=anchor)

# ================================================================================================
# SF01: black open cut to <0.2 s (scene clock advanced 0.3 s); everything else unchanged
# ================================================================================================
_sf01_prev = S['SF01_open_title'][0]
@scene('SF01_open_title', 5.0)
def sf01(t, W, H):
    return _sf01_prev(min(t+0.3, 4.98), W, H)

# ================================================================================================
# SF02: labels earlier (1.7 / 2.2 s); lit cells pulse together after lighting; whole field sways (secondary)
# ================================================================================================
_s = src_of('sf_r8.py', "@scene('SF02_1979_request', 5.0)")
_s = sub(_s, "t=ramp(t, 2.7, 3.5)", "t=ramp(t, 1.7, 2.4)")
_s = sub(_s, "t=ramp(t, 3.3, 4.1)", "t=ramp(t, 2.2, 2.9)")
_s = sub(_s, "    z = 1.10+0.08*lin(t, 5)",
"""    sy = ramp(t, 2.9, 3.3)*max(0.0, math.sin((t-2.9)*2*math.pi*1.25))**4
    gb = cv2.GaussianBlur(gm[..., 0], (0, 0), 14)[..., None]
    base = base+gm*sy*np.array([1.0, 0.74, 0.36])*0.30+gb*sy*np.array([1.0, 0.62, 0.25])*0.30
    if 'sway2' not in _cache:
        yy_, xx_ = np.mgrid[0:ih, 0:iw].astype(np.float32); _cache['sway2'] = (xx_, yy_)
    xx_, yy_ = _cache['sway2']; amp = 2.2
    base = cv2.remap(base.astype(np.float32), xx_+amp*np.sin(yy_/97.0+t*1.3), yy_+amp*np.sin(xx_/131.0+t*1.1), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    _cache['sf02_sync'] = sy
    z = 1.10+0.08*lin(t, 5)""")
_s = sub(_s, "    P = lambda x, y: to_px(im, x, y, W, H, z, cx, cy)\n",
"""    P = lambda x, y: to_px(im, x, y, W, H, z, cx, cy)
    rgb = over(rgb, fg_bokeh(W, H, t, ((1240, 690, 150), (60, 720, 110))), shadow=0)
    if t > 2.9:      # each synchronous burst sends a ring out of the big lit cell
        ph = ((t-2.9)*1.25) % 1.0; Xg, Yg = P(*gpos); Lr = Layer(W, H)
        Lr.ring((Xg, Yg), (20+90*ph)*s, fill=(255, 200, 120), width=2.2*s, alpha=0.7*(1-ph)*ramp(t, 2.9, 3.2))
        rgb = over(rgb, Lr.get(), shadow=0, glow_amt=0.8)
""")
exec(compile(_s, 'sf_r10_sf02', 'exec'), globals())

# ================================================================================================
# SF03: top strip removed; H+ caption on a plate and retired when the second clue arrives (<= 3 text blocks)
# ================================================================================================
_s = src_of('sf_r8.py', "@scene('SF03_microbe_clues', 5.0)")
_s = sub(_s, "    L.rrect((28*s, 26*s, 352*s, 68*s), 6*s, fill=(12, 18, 38), alpha=0.75*ramp(t, 0.1, 0.8))\n", "")
_s = sub(_s, "    L.text((44*s, 54*s), '接下来的那些年 · 微生物那边', F(SANS, 18*s), fill=CREAM, alpha=ramp(t, 0.1, 0.8)*0.92, anchor='ls', tracking=3*s)\n", "")
_s = sub(_s, "L2.text((CL[0], CL[1]+RL+26*s), 'H⁺ 被一个一个泵到膜外', F(SANS_B, 17*s), fill=(150, 240, 175), alpha=a, anchor='ms')",
             "plate_text(L2, (CL[0], CL[1]+RL+30*s), 'H⁺ 被一个一个泵到膜外', F(SANS_B, 20*s), fill=(150, 240, 175), alpha=a*(1-ramp(t, 2.9, 3.3)))")
_s = sub(_s, "L2.text((CR[0], CR[1]-RR-14*s), '眼点膜上的感光蛋白', F(SANS_B, 17*s), fill=CREAM, alpha=a, anchor='ms')",
             "plate_text(L2, (CR[0], CR[1]-RR-16*s), '眼点膜上的感光蛋白', F(SANS_B, 20*s), fill=CREAM, alpha=a)")
exec(compile(_s, 'sf_r10_sf03', 'exec'), globals())

# ================================================================================================
# SF04: family portrait (dark + gold line art), present from frame 0; neuron vignette swept by blue light -> fires
# ================================================================================================
def _gold_neuron():
    """a single gold neuron from the SF02 plate (same family), and its dimmed 'unlit' version"""
    if 'n4' in _cache: return _cache['n4']
    S['SF02_1979_request'][0](0.0, 320, 180)          # populates g2c
    lab, order, m, d2, gpos, bpos = _cache['g2c']; im = img('sf02c_crowd')
    _cache['n4'] = (im, d2, gpos); return _cache['n4']

@scene('SF04_crick_quote', 5.0)
def sf04(t, W, H):
    s = W/1280; u = lin(t, 5)
    P0 = img('sf04g_crick'); bg = np.array([0.075, 0.06, 0.17])
    rgb = np.zeros((H, W, 3), np.float32)+bg
    rgb = rgb*0.6+fam_bg(W, H)*0.32+radial(W, H, W*(0.32-0.05*u), H*0.45, W*0.26, (60, 70, 150), 0.22)
    ph = int(H*0.96); pw = ph
    Pc = cam(P0, pw, ph, zoom=1.02+0.08*u, cx=0.5+0.015*u, cy=0.47)
    sw = ramp(t, 2.3, 4.4)                                  # gold light sweep over the line art
    if 0 < sw < 1:
        yy, xx = np.mgrid[0:ph, 0:pw]; band = np.exp(-(((xx+yy*0.6)/pw-(-0.2+1.8*sw))/0.08)**2)
        lum = Pc.mean(2, keepdims=True); Pc = np.clip(Pc+band[..., None]*np.clip(lum-0.2, 0, 1)*np.array([1.0, 0.8, 0.45])*0.6, 0, 1)
    yy, xx = np.mgrid[0:ph, 0:pw]; e = np.minimum.reduce([xx/pw*3, (1-xx/pw)*1.7, yy/ph*4, (1-yy/ph)*3]); m = (np.clip(e, 0, 1)**1.4*(0.6+0.4*ramp(t, 0, 0.5)))[..., None]
    x0 = int(36*s-10*s*ease_out(ramp(t, 0, 1.5))); y0 = H-ph
    rgb[y0:, x0:x0+pw] = rgb[y0:, x0:x0+pw]*(1-m)+Pc*m
    rgb = over(rgb, drift_specks(W, H, t, 45, 9, (240, 220, 180), 0.3, 1.6, (-10, -5)), shadow=0)
    # quote block (second depth plane, drifts up)
    L = Layer(W, H); ty = -8*s*u
    L.text((690*s, 246*s+ty), '1999', F(SANS_B, 22*s), fill=GOLD, alpha=ramp(t, 0.15, 0.6), anchor='ls', tracking=6*s)
    L.text((690*s, 318*s+ty), '“理想的信号会是光”', F(SERIF_B, 46*s), fill=CREAM, alpha=ramp(t, 0.4, 1.3), anchor='ls')
    L.text((690*s, 390*s+ty), '——他也承认：', F(SERIF, 27*s), fill=BRIGHT, alpha=ramp(t, 2.0, 2.6), anchor='ls')
    em = ramp(t, 2.4, 3.2); tr = (2.5*ease_out(ramp(t, 2.4, 3.8)))*s
    L.text((690*s, 448*s+ty), '这个想法相当牵强。', F(SERIF_B, 38*s), fill=GOLD, alpha=em, anchor='ls', tracking=tr)
    L.line([(690*s, 490*s+ty), (690*s+440*s*ease_out(ramp(t, 3.0, 4.0)), 490*s+ty)], fill=(110, 120, 160), width=1*s)
    L.text((690*s, 526*s+ty), '原文 “rather far-fetched”', F(SANS, 20*s), fill=CREAM, alpha=ramp(t, 3.3, 4.0), anchor='ls')
    L.text((690*s, 556*s+ty), 'F. Crick, Phil. Trans. R. Soc. Lond. B, 1999', F(SANS, 20*s), fill=BRIGHT, alpha=ramp(t, 3.4, 4.1), anchor='ls')
    rgb = over(rgb, L.get(), glow_amt=0.15)
    f = F(SERIF_B, 46*s); gx = 690*s+f.getlength('“理想的信号会是')+f.getlength('光')/2; gy = 302*s+ty
    gl = ramp(t, 1.2, 1.8)*(0.75+0.25*math.sin(t*3.2)); rgb = rgb+radial(W, H, gx, gy, 34*s, CYAN, 0.5*gl)
    rgb = rgb+radial(W, H, 850*s, 435*s+ty, 170*s, GOLD, 0.06*em*(0.6+0.4*math.sin(t*3)))
    # neuron vignette (upper right): the imagined experiment, played out
    im, d2, gp = _gold_neuron(); NC = (1112*s, 142*s); NR = int(100*s); na = ramp(t, 1.4, 1.9)
    if na > 0:
        zN = 3.2; cxN, cyN = gp[0], gp[1]
        lit = circ_img(im, NR, zoom=zN, cx=cxN, cy=cyN); dim = circ_img(d2, NR, zoom=zN, cx=cxN, cy=cyN)
        sweep = ramp(t, 2.0, 2.9); fire = ramp(t, 2.85, 3.05)
        a_l = np.asarray(lit).astype(np.float32)/255; a_d = np.asarray(dim).astype(np.float32)/255
        xx = np.linspace(0, 1, NR*2)[None, :, None]
        front = np.clip((sweep*1.3-0.15-xx)/0.15, 0, 1)                         # blue scan front, left -> right
        blue = np.exp(-((xx-(sweep*1.3-0.15))/0.06)**2)
        mix = a_d.copy(); mix[..., :3] = a_d[..., :3]*(1-front*fire)+a_l[..., :3]*front*fire
        mix[..., :3] = np.clip(mix[..., :3]+blue*np.array([0.25, 0.55, 1.0])*0.55*(sweep > 0)*(sweep < 1), 0, 1)
        mix[..., :3] = np.clip(mix[..., :3]*(1+0.35*fire*(0.6+0.4*math.sin(t*14)**2)), 0, 1)
        vim = Image.fromarray((mix*255).astype(np.uint8), 'RGBA')
        Lv = Layer(W, H); Lv.dot(NC, NR+6*s, fill=(8, 10, 24), alpha=0.92*na); Lv.paste(vim, (NC[0]-NR, NC[1]-NR), alpha=na)
        Lv.ring(NC, NR, fill=CYAN if sweep > 0 else (130, 150, 200), width=2.4*s, alpha=na)
        if fire > 0:
            rr = ramp(t, 3.0, 3.9); Lv.ring(NC, NR+(6+40*rr)*s, fill=(255, 200, 120), width=2.4*s, alpha=0.8*(1-rr)*fire)
            # spike trace under the vignette: flat while dark, spikes once lit
            bx0, bx1, by = NC[0]-NR, NC[0]+NR, NC[1]+NR+30*s; pts = []
            for q in np.linspace(0, 1, 120):
                tt = 2.85+q*(t-2.85); v = 0
                if tt > 2.95 and ((tt-2.95)*6) % 1.0 < 0.12: v = 1
                pts.append((bx0+(bx1-bx0)*q, by-v*20*s))
            Lv.line([(bx0, by), (bx1, by)], fill=(90, 100, 140), width=1*s, alpha=na)
            Lv.line(pts, fill=(255, 205, 130), width=1.8*s, alpha=fire)
        rgb = over(rgb, Lv.get(), shadow=0.35, glow_amt=0.5)
        rgb = rgb+radial(W, H, NC[0], NC[1], 70*s, (255, 180, 90), 0.3*fire*(0.7+0.3*math.sin(t*9)))
    L2 = Layer(W, H); ta = ramp(t, 3.0, 3.5)
    plate_text(L2, (NC[0]-NR-20*s, NC[1]+8*s), '设想：光一照，神经元就放电', F(SANS_B, 22*s), fill=CREAM, alpha=ta, anchor='rs')
    rgb = over(rgb, L2.get(), shadow=0.4)
    return grade(rgb, seed=int(t*24))

# ================================================================================================
# SF05: rebuilt.  Header anchored at the top with a safe margin (no camera push on the text); ChR2 badge sits left
#       of the reason line; three family portraits; under each name a contribution icon lights in turn.
# ================================================================================================
def _icon(L, kind, c, s, a, lit, t):
    x, y = c; col = GOLD if lit < 0.5 else (255, 222, 150)
    if a <= 0: return
    L.dot((x, y), 26*s, fill=(14, 18, 40), alpha=0.9*a); L.ring((x, y), 26*s, fill=col, width=1.8*s, alpha=a)
    if kind == 'alga':      # Chlamydomonas: oval cell, red eyespot, two flagella
        L.d.ellipse([(x-11*s)*2, (y-8*s)*2, (x+11*s)*2, (y+12*s)*2], fill=(99, 199, 120, int(255*a)), outline=(10, 30, 20, int(255*a)), width=int(2*s*2))
        L.dot((x+6*s, y+1*s), 3.2*s, fill=(255, 90, 60), alpha=a*(0.6+0.4*lit))
        wv = math.sin(t*9)*3*s
        L.line([(x-3*s, y-8*s), (x-9*s+wv, y-16*s), (x-13*s, y-21*s)], fill=(200, 230, 200), width=1.4*s, alpha=a)
        L.line([(x+3*s, y-8*s), (x+9*s-wv, y-16*s), (x+13*s, y-21*s)], fill=(200, 230, 200), width=1.4*s, alpha=a)
    elif kind == 'current':  # light pulse (top) -> inward current step
        L.line([(x-18*s, y-9*s), (x-8*s, y-9*s), (x-8*s, y-15*s), (x+6*s, y-15*s), (x+6*s, y-9*s), (x+18*s, y-9*s)], fill=CYAN, width=1.6*s, alpha=a)
        k = lit; L.line([(x-18*s, y+4*s), (x-8*s, y+4*s), (x-6*s, y+4*s+14*s*k), (x+6*s, y+4*s+11*s*k), (x+8*s, y+4*s), (x+18*s, y+4*s)], fill=(255, 209, 102), width=2*s, alpha=a)
    else:                    # neuron that lights cyan
        nc = (60, 70, 120) if lit < 0.5 else CYAN
        for ang in (0.3, 1.4, 2.6, 3.6, 4.9):
            L.line([(x, y), (x+16*s*math.cos(ang), y+16*s*math.sin(ang))], fill=nc, width=2*s, alpha=a)
        L.dot((x, y), 7*s, fill=nc, alpha=a); L.dot((x, y), 3*s, fill=(230, 245, 255), alpha=a*lit)

@scene('SF05_nobel_portraits', 5.0)
def sf05(t, W, H):
    s = W/1280; u = lin(t, 5)
    rgb = np.zeros((H, W, 3), np.float32)+np.array([0.07, 0.055, 0.16])
    rgb = rgb*0.6+fam_bg(W, H)*0.30+radial(W, H, W*(0.3+0.4*u), H*0.12, W*0.42, (80, 90, 160), 0.12)
    rgb = over(rgb, fg_bokeh(W, H, t, ((-20, 680, 120), (1300, 60, 110))), shadow=0)
    people = [('sf05g_deisseroth', 'Karl Deisseroth', 'neuron', '装进神经元'),
              ('sf05g_hegemann', 'Peter Hegemann', 'alga', '衣藻的感光电流'),
              ('sf05g_nagel', 'Georg Nagel', 'current', '证明它是光控通道')]
    cw = int(340*s); gap = int(40*s); x0 = (W-3*cw-2*gap)//2; y0 = int(160*s)
    L = Layer(W, H)
    for i, (key, nm, kind, cap) in enumerate(people):
        a = ramp(t, 0.2+i*0.3, 0.9+i*0.3); dy = int(18*s*(1-ease_out(a)))
        P0 = img(key) if os.path.exists(G+key+'.png') else img('sf05b_'+key.split('_')[1])
        Pc = cam(P0, cw, cw, zoom=1.12+0.08*u, cx=0.5+(i-1)*0.01*u, cy=0.42-0.02*u)
        tl = 2.4+i*0.55; sw = ramp(t, tl-0.3, tl+0.9)
        if 0 < sw < 1:
            yy, xx = np.mgrid[0:cw, 0:cw]; band = np.exp(-(((xx+yy*0.5)/cw-(-0.2+1.7*sw))/0.09)**2)
            lum = Pc.mean(2, keepdims=True); Pc = np.clip(Pc+band[..., None]*np.clip(lum-0.18, 0, 1)*np.array([1.0, 0.82, 0.45])*0.6, 0, 1)
        x = x0+i*(cw+gap); y = y0+dy
        yy, xx = np.mgrid[0:cw, 0:cw]; e = np.minimum.reduce([xx/cw*2.2, (1-xx/cw)*2.2, yy/cw*3, (1-yy/cw)*1.6]); m = (np.clip(e/0.5, 0, 1)**1.6)[..., None]*a
        rgb[y:y+cw, x:x+cw] = rgb[y:y+cw, x:x+cw]*(1-m)+Pc*m
        ly = y0+cw+16*s
        L.line([(x+18*s, ly), (x+18*s+(cw-36*s)*ease_out(a), ly)], fill=GOLD, width=1.4*s, alpha=a)
        L.text((x+cw/2, ly+40*s), nm, F(SERIF_B, 28*s), fill=CREAM, alpha=a, anchor='ms')
        lit = ramp(t, tl, tl+0.3); ia = ramp(t, tl-0.35, tl)
        _icon(L, kind, (x+cw/2-F(SANS_B, 20*s).getlength(cap)/2-20*s, ly+86*s), s, ia, lit, t)
        L.text((x+cw/2+18*s, ly+93*s), cap, F(SANS_B, 20*s), fill=(255, 226, 170) if lit > 0.5 else BRIGHT, alpha=ia, anchor='ms')
    # header (fixed, 56 px safe margin)
    L.text((W/2, 72*s), '2026 年 10 月 5 日  ·  诺贝尔生理学或医学奖', F(SANS_B, 28*s), fill=GOLD, alpha=ramp(t, 0, 0.5), anchor='ms', tracking=2*s)
    fr = F(SERIF, 22*s); reason = '获奖理由：发现光控离子通道，并由此建立光遗传学'; tw = fr.getlength(reason)
    rx0 = W/2-tw/2+24*s
    L.text((rx0, 120*s), reason, fr, fill=CREAM, alpha=ramp(t, 0.9, 1.5), anchor='ls')
    ux0 = rx0+fr.getlength('获奖理由：发现'); ux1 = ux0+fr.getlength('光控离子通道'); kk = ease_out(ramp(t, 1.5, 2.1))
    L.line([(ux0, 130*s), (ux0+(ux1-ux0)*kk, 130*s)], fill=CYAN, width=2*s, alpha=ramp(t, 1.5, 1.7))
    L.text((W/2, H-26*s), '据诺贝尔奖官方新闻稿  ·  头像为插画', F(SANS, 20*s), fill=BRIGHT, alpha=ramp(t, 3.4, 4.0), anchor='ms')
    rgb = over(rgb, drift_specks(W, H, t, 40, 21, (240, 220, 170), 0.26, 1.5, (8, -4)), shadow=0)
    rgb = over(rgb, L.get(), shadow=0.45)
    # ChR2 badge: big at centre for the first beat, then settles LEFT of the reason line (never over text)
    bx, by = rx0-40*s, 112*s; k = ease(ramp(t, 0.5, 1.3))
    cx_, cy_ = W/2+(bx-W/2)*k, 380*s+(by-380*s)*k; r = int((150-124*k)*s)
    Lb = Layer(W, H); ba = 1.0 if t > 0.05 else 0.0
    Lb.dot((cx_, cy_), r+4*s, fill=(8, 10, 24), alpha=0.95*ba)
    Lb.paste(circ_img(img('sf09e_chr2'), r, zoom=2.2, cx=0.49, cy=0.47), (cx_-r, cy_-r), alpha=ba)
    Lb.ring((cx_, cy_), r, fill=CYAN, width=2*s, alpha=ba)
    rgb = over(rgb, Lb.get(), shadow=0.3)
    opn = ramp(t, 1.6, 2.0)                                  # badge pulses with ions while the line names the channel
    if opn > 0:
        Li = Layer(W, H)
        for j, pxn in enumerate((0.4375, 0.558)):
            X = cx_+(2*r/1024)*2.2*(pxn*1536-0.49*1536)
            for n in range(3):
                p = (t*0.9+n/3+j*0.5) % 1.0; Li.dot((X, cy_-r*0.6+p*r*1.2), 1.8*s, fill=(255, 209, 102), alpha=opn*min(1, p*5)*min(1, (1-p)*5))
        rgb = over(rgb, Li.get(), shadow=0, glow_amt=0.7)
        rgb = rgb+radial(W, H, cx_, cy_, r*1.5, CYAN, 0.18*opn*(0.7+0.3*math.sin(t*5)))
    return grade(rgb, seed=int(t*24))

# ================================================================================================
# SF06: timeline strip removed (1 title + 1 caption + 2 labels); inside the magnifier the switch works once:
#       a blue pulse arrives -> both pores light -> ions pass.  Early beats: '?' breathes, push starts at 0.
# ================================================================================================
_s = src_of('sf_r8.py', "@scene('SF06_switch_diagram', 6.0)")
_a = _s.index("    y = 676*s; x0, x1 = 60*s, 1220*s"); _b = _s.index("    return grade(over(rgb, L2.get())")
_s = _s[:_a]+_s[_b:]
_s = sub(_s, "calm = np.maximum(calm, np.clip((yy/H-0.86)/0.08, 0, 1))", "calm = calm")
_s = sub(_s, "z = 1.0+0.08*u; cxx = 0.50+0.03*u", "z = 1.0+0.10*ease(u)+0.02*u; cxx = 0.50+0.03*u")
_s = sub(_s, "'?', F(SERIF_B, 96*s*k)", "'?', F(SERIF_B, 96*s*k*(1+0.06*math.sin(t*5)))")
_s = sub(_s, "    if t > 3.3:\n",
"""    rgb = over(rgb, fg_bokeh(W, H, t, ((-30, 560, 130), (40, 760, 120))), shadow=0)
    if t > 3.7:      # the switch works: blue pulse in, pores glow, ions down both pores
        zi = 2.1+0.15*u; kk = ramp(t, 3.7, 4.1); Li = Layer(W, H)
        for j, pxn in enumerate((0.4375, 0.558)):
            X = C[0]+(2*R/1024)*zi*(pxn*1536-0.495*1536)
            y_top = C[1]+(2*R/1024)*zi*(0.34*1024-0.47*1024); y_bot = C[1]+(2*R/1024)*zi*(0.64*1024-0.47*1024)
            Li.line([(X, y_top), (X, y_bot)], fill=(150, 220, 255), width=4*s, alpha=0.8*kk)
            for n in range(5):
                p = (t*0.8+n/5+j*0.5) % 1.0
                if t > 4.0: Li.dot((X, y_top+(y_bot-y_top)*p), 4.2*s, fill=(255, 209, 102), alpha=ramp(t, 4.0, 4.3)*min(1, p*6)*min(1, (1-p)*6))
        rgb = over(rgb, Li.get(), shadow=0, glow_amt=1.0)
        rgb = rgb+radial(W, H, C[0]-R*0.6, C[1]-R*0.8, 80*s, CYAN, 0.45*math.exp(-((t-3.75)/0.18)**2))
    if t > 3.3:
""")
exec(compile(_s, 'sf_r10_sf06', 'exec'), globals())

# ================================================================================================
# SF07: title at 1.0 s and held; bright subtitle; fibre above the beam; ions down the subunit pores
# ================================================================================================
_s = src_of('sf_r8.py', "@scene('SF07_main_title'")
_s = sub(_s, "def sf07(t, W, H):", "def _sf07_base10(t, W, H):"); _s = sub(_s, "@scene('SF07_main_title', 5.0)\n", "")
_s = sub(_s, "    L = Layer(W, H)\n    a = ramp(t, 1.0, 2.2)", "    _cache['sf07_tip10'] = (fx, fbot, ox, oy, Wi, Hi)\n    L = Layer(W, H)\n    a = ramp(t, 1.0, 1.8)")
_s = sub(_s, "'光遗传学', F(SERIF_B, 108*s)", "'光遗传学', F(SERIF_B, 96*s)")
_s = sub(_s, "ramp(t, 1.0, 3.2)", "ramp(t, 1.0, 2.6)")
_s = sub(_s, "'O P T O G E N E T I C S', F(SANS, 17*s), fill=CYAN, alpha=ramp(t, 2.0, 2.8)", "'O P T O G E N E T I C S', F(SANS_B, 20*s), fill=(185, 225, 255), alpha=ramp(t, 1.6, 2.2)")
_s = sub(_s, "'这一期，就讲这枚开关', F(SANS, 22*s), fill=(190, 198, 222), alpha=ramp(t, 2.6, 3.4)", "'', F(SANS, 22*s), fill=(190, 198, 222), alpha=0")
_s = sub(_s, "z = 1.0+0.06*u+0.10*ease(ramp(t, 1.5, 5.0))", "z = 1.0+0.06*u+0.10*ease(ramp(t, 0.0, 5.0))")
_s = sub(_s, "a = 0.25*(t > 0.7+d*8)", "a = 0.25*(t > 0.15+d*8)")
_s = sub(_s, "for w0 in (0.7, 1.9, 3.1, 4.3)", "for w0 in (0.15, 1.3, 2.45, 3.6, 4.75)")
_s = sub(_s, "alpha=ramp(t, 0.4, 0.8)*min(1, (1-p)*6)", "alpha=min(1, (1-p)*6)")
_s = sub(_s, "0.35*ramp(t, 0.5, 1.2)*(0.85", "0.35*(0.85")
exec(compile(_s, 'sf_r10_sf07', 'exec'), globals())

@scene('SF07_main_title', 5.0)
def sf07(t, W, H):
    s = W/1280; rgb = _sf07_base10(t, W, H); fx, fbot, ox, oy, Wi, Hi = _cache['sf07_tip10']
    # optical fibre + ferrule above the brain (the beam comes out of its tip)
    Lf = Layer(W, H); ftip = oy+0.150*Hi; fer0, fer1 = oy+0.085*Hi, oy+0.135*Hi
    Lf.line([(fx, -10), (fx, ftip)], fill=(10, 8, 26), width=13*s); Lf.line([(fx, -10), (fx, ftip)], fill=(78, 92, 140), width=9*s)
    Lf.line([(fx-2*s, -10), (fx-2*s, ftip)], fill=(150, 170, 220), width=2*s, alpha=0.7)
    Lf.rrect((fx-12*s, fer0, fx+12*s, fer1), 3*s, fill=(170, 176, 196), outline=(10, 8, 26), width=2.5*s)
    Lf.line([(fx-6*s, fer0+3*s), (fx-6*s, fer1-3*s)], fill=(235, 240, 250), width=2*s, alpha=0.8)
    rgb = over(rgb, Lf.get(), shadow=0.3)
    rgb = rgb+radial(W, H, fx, ftip, 16*s, (200, 235, 255), 0.7*(0.75+0.25*math.sin(t*6)))
    C = (990*s, 300*s); R = int(150*s); a = ramp(t, 0.5, 1.3)
    L = Layer(W, H); hx, hy = fx, fbot+14*s
    zc = 1.6+0.5*ease(ramp(t, 1.3, 4.5))
    if a > 0:
        k = ease_out(a); px, py = hx+(C[0]-hx)*k, hy+(C[1]-hy)*k; r = max(2, int(R*k))
        L.ring((hx, hy), 10*s, fill=CYAN, width=1.8*s, alpha=a)
        ang = math.atan2(hy-py, hx-px)
        for sg in (-1, 1): L.line([(hx, hy), (px+r*math.cos(ang+sg*0.55), py+r*math.sin(ang+sg*0.55))], fill=CYAN, width=1.3*s, alpha=0.75*a)
        L.dot((px, py), r+6*s, fill=(8, 10, 24), alpha=0.92*a)
        L.paste(circ_img(img('sf10_orexin'), r, zoom=1.2+0.8*ease(ramp(t, 0.8, 1.6)), cx=0.47, cy=0.42), (px-r, py-r), alpha=a*(1-ease(ramp(t, 1.3, 1.8))))
        L.paste(circ_img(img('sf09e_chr2'), r, zoom=zc, cx=0.49, cy=0.46), (px-r, py-r), alpha=a*ease(ramp(t, 1.3, 1.8)))
        L.ring((px, py), r, fill=CYAN, width=2.4*s, alpha=a)
    rgb = over(rgb, L.get(), shadow=0.35)
    op = ramp(t, 2.0, 2.4)
    if op > 0:      # ions travel down each subunit's own pore (same coordinates as SF09)
        Li = Layer(W, H); sc = (2*R/1024)*zc
        for j, pxn in enumerate((0.4375, 0.558)):
            X = C[0]+sc*(pxn*1536-0.49*1536); yt = C[1]+sc*(0.34-0.46)*1024; yb = C[1]+sc*(0.64-0.46)*1024
            Li.line([(X, yt), (X, yb)], fill=(160, 225, 255), width=3*s, alpha=0.5*op)
            for n in range(6):
                p = (t*0.75+n/6+j*0.5) % 1.0; Y = yt-20*s+(yb-yt+40*s)*p
                if math.hypot(X-C[0], Y-C[1]) < R-6*s:
                    Li.dot((X+1.5*s*math.sin(n*2+t*5), Y), 4*s, fill=(255, 209, 102), alpha=op*min(1, p*6)*min(1, (1-p)*6))
        rgb = over(rgb, Li.get(), shadow=0, glow_amt=0.7)
        rgb = rgb+radial(W, H, C[0], C[1]-R*0.75, 70*s, CYAN, 0.22*op*(0.8+0.2*math.sin(t*6)))
    L2 = Layer(W, H); ta = ramp(t, 2.6, 3.2)
    L2.text((C[0], C[1]+R+36*s), '这一期，就讲这枚开关', F(SANS_B, 24*s), fill=CREAM, alpha=ta, anchor='ms', tracking=2*s)
    L2.text((C[0], C[1]+R+66*s), '神经元膜上的光控通道', F(SANS, 20*s), fill=(226, 232, 248), alpha=ramp(t, 2.9, 3.5), anchor='ms')
    return over(rgb, L2.get(), shadow=0.6)

# ================================================================================================
# SF08: speed bar compares only "light -> channel open"; violet beam; azobenzene tether drawn as a bead chain
# ================================================================================================
_s = src_of('sf_r9.py', "@scene('SF08_early_attempts', 7.0)")
_s = sub(_s, "    L.line([P(0.808, 0.395), end], fill=MAG_O, width=5*s); L.line([P(0.808, 0.395), end], fill=MAG, width=3*s)\n    L.dot(end, 4*s, fill=MAG)\n",
"""    b0 = P(0.808, 0.395); mid = ((b0[0]+end[0])/2-10*s, (b0[1]+end[1])/2+4*s); beads = []
    for q in np.linspace(0, 1, 7):
        beads.append(((1-q)**2*b0[0]+2*q*(1-q)*mid[0]+q*q*end[0], (1-q)**2*b0[1]+2*q*(1-q)*mid[1]+q*q*end[1]))
    L.line(beads, fill=MAG_O, width=6*s); L.line(beads, fill=MAG, width=3*s)
    for bp in beads: L.dot(bp, 5*s, fill=MAG_O); L.dot(bp, 3.6*s, fill=(250, 140, 220))
    L.dot(b0, 6*s, fill=(255, 220, 120)); L.ring(b0, 6*s, fill=MAG_O, width=1.6*s)
""")
_a = _s.index("    if t > 4.3:\n        Lp = Layer(W, H)"); _b = _s.index("    openB = ramp(t, 5.55, 5.9)")
_s = _s[:_a]+"""    if t > 4.2:      # violet light: a beam from the upper right onto the azobenzene, photons travelling in it
        vb = ramp(t, 4.2, 4.5)*(1-0.6*ramp(t, 5.8, 6.4)); sx, sy = TX+330*s, -40*s
        yy_, xx_ = np.mgrid[0:H, 0:W].astype(np.float32); dx, dy = TX-sx, TY-sy; Ln = math.hypot(dx, dy)
        along = ((xx_-sx)*dx+(yy_-sy)*dy)/Ln/Ln; across = np.abs((xx_-sx)*(-dy/Ln)+(yy_-sy)*(dx/Ln))
        wdt = 14*s+60*s*np.clip(along, 0, 1)
        beam = np.exp(-(across/wdt)**2)*np.clip(along*4, 0, 1)*np.clip((1.08-along)*8, 0, 1)
        rgb = rgb+beam[..., None]*np.array([0.62, 0.42, 1.0])*0.62*vb
        Lp = Layer(W, H)
        for n in range(6):
            q = ((t-4.2)*0.9+n/6) % 1.0; x = sx+dx*q; y = sy+dy*q
            Lp.dot((x, y), 5.5*s, fill=(225, 200, 255), alpha=vb*min(1, (1-q)*5)*min(1, q*5))
        rgb = over(rgb, Lp.get(), shadow=0, glow_amt=1.2)
        rgb = rgb+radial(W, H, TX, TY, 40*s, (190, 150, 255), 0.5*hit*(1-ramp(t, 5.3, 6.0)))
"""+_s[_b:]
_a = _s.index("    # how long until each switch can be used"); _b = _s.index("    return grade(over(rgb, L.get())")
_s = _s[:_a]+"""    # light -> channel open: the only quantity on this axis (log time, 1 ms ... 10 s)
    a = ramp(t, 4.5, 5.0)
    if a > 0:
        bx, by, bw, bh = 40*s, 548*s, 640*s, 150*s
        L.rrect((bx, by, bx+bw, by+bh), 8*s, fill=(12, 18, 38), alpha=0.9*a)
        L.text((bx+22*s, by+34*s), '从给光到通道打开', F(SANS_B, 22*s), fill=CREAM, alpha=a, anchor='ls')
        x0, x1 = bx+34*s, bx+bw-40*s; ay_ = by+bh-42*s
        L.line([(x0, ay_), (x1, ay_)], fill=(150, 160, 190), width=1.4*s, alpha=a)
        for q, tk in ((0.0, '1 ms'), (0.25, '10 ms'), (0.5, '100 ms'), (0.75, '1 s'), (1.0, '10 s')):
            x = x0+(x1-x0)*q; L.line([(x, ay_-5*s), (x, ay_+5*s)], fill=(150, 160, 190), width=1.4*s, alpha=a)
            L.text((x, ay_+28*s), tk, F(SANS, 20*s), fill=BRIGHT, alpha=a, anchor='ms')
        L.rrect((x0-4*s, ay_-16*s, x0+(x1-x0)*0.07, ay_-5*s), 4*s, fill=CYAN, alpha=a)
        L.text((x0-4*s, ay_-24*s), '需要：毫秒级', F(SANS_B, 20*s), fill=(140, 205, 255), alpha=a, anchor='ls')
        g = ease_out(ramp(t, 4.7, 5.4)); xa0, xa1 = x0+(x1-x0)*0.62, x0+(x1-x0)*0.96
        L.rrect((xa0, ay_-16*s, xa0+(xa1-xa0)*g, ay_-5*s), 4*s, fill=(255, 180, 120), alpha=a)
        L.text((xa1, ay_-24*s), '多步接力：秒级', F(SANS_B, 20*s), fill=(255, 205, 160), alpha=a, anchor='rs')
"""+_s[_b:]
exec(compile(_s, 'sf_r10_sf08', 'exec'), globals())

# ================================================================================================
# SF10: de-duplicated Wan keyframes + optical-flow in-betweens; time skip = same-camera fast-forward
#   map: 0-2.6 asleep (clip 0-2.21) | 2.6-3.4 fast-forward x1.5 (clip 2.21-3.41, eyes open) | 3.4- 1:1 rise + walk
# ================================================================================================
SF10_D = 9.4
def c10(t):
    if t < 2.6: return [(t*0.85, 1.0)]
    if t < 3.4: return [(2.21+(t-2.6)*1.5, 1.0)]
    return [(3.41+(t-3.4), 1.0)]

def _keys10():
    if 'keys10' in _cache: return _cache['keys10']
    fr, fps = _vframes_native(R9.CL10)
    sm = [cv2.resize(cv2.cvtColor((f*255).astype(np.uint8), cv2.COLOR_RGB2GRAY), (160, 107)).astype(np.float32) for f in fr]
    d = np.array([np.abs(sm[i+1]-sm[i]).mean() for i in range(len(sm)-1)])
    groups = [[0]]
    for i in range(1, len(fr)):
        w = d[max(0, i-4):i+3]; big = w.max()
        new = (d[i-1] > 0.45*big) if big > 1.5 else True
        if new: groups.append([i])
        else: groups[-1].append(i)
    keys = [(np.mean(g)/fps, np.mean([fr[k] for k in g], 0).astype(np.float32)) for g in groups]
    _cache['keys10'] = keys; return keys

_dis = None
def _flow(a, b):
    global _dis
    if _dis is None: _dis = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)
    ga = cv2.cvtColor((a*255).astype(np.uint8), cv2.COLOR_RGB2GRAY); gb = cv2.cvtColor((b*255).astype(np.uint8), cv2.COLOR_RGB2GRAY)
    return _dis.calc(ga, gb, None)

def frame10(ct):
    keys = _keys10(); ts = [k[0] for k in keys]
    i = int(np.searchsorted(ts, ct))-1
    if i < 0: return keys[0][1]
    if i >= len(keys)-1: return keys[-1][1]
    (ta, A), (tb, B) = keys[i], keys[i+1]; al = float((ct-ta)/(tb-ta))
    if al < 0.02: return A
    if al > 0.98: return B
    fk = ('fl10', i)
    if fk not in _cache: _cache[fk] = (_flow(A, B), _flow(B, A))
    fab, fba = _cache[fk]
    h, w = A.shape[:2]
    if 'grid10' not in _cache:
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32); _cache['grid10'] = (xx, yy)
    xx, yy = _cache['grid10']
    Aw = cv2.remap(A, (xx-al*fab[..., 0]).astype(np.float32), (yy-al*fab[..., 1]).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    Bw = cv2.remap(B, (xx-(1-al)*fba[..., 0]).astype(np.float32), (yy-(1-al)*fba[..., 1]).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    return Aw*(1-al)+Bw*al

_s = src_of('sf_r9.py', "@scene('SF10_mouse_tripo', SF10_D)")
_s = sub(_s, "pl = max(pulses(t, 1.0, 2.75), pulses(t, 3.35, 4.6))", "pl = max(pulses(t, 0.8, 2.55), pulses(t, 2.75, 3.9))")
_s = sub(_s, "dip = math.exp(-((t-3.05)/0.13)**2); rgb = rgb*(1-0.85*dip)", "pass")
_s = sub(_s, "sk = ramp(t, 2.6, 2.85)*(1-ramp(t, 3.45, 3.7))", "sk = ramp(t, 2.5, 2.7)*(1-ramp(t, 3.4, 3.65))")
_s = sub(_s, "rgb = rgb*(1-0.2*sk*np.clip(np.abs(xx/W-0.5)*2, 0, 1)[..., None])", "pass")
_s = sub(_s, "a = ramp(t, 0.5, 1.2)*(1-ramp(t, 2.9, 3.3))", "a = ramp(t, 0.4, 1.0)*(1-ramp(t, 4.0, 4.4))")
_s = sub(_s, "ga = ramp(t, 0.9, 1.3)*(1-ramp(t, 4.6, 5.0))", "ga = ramp(t, 0.7, 1.1)*(1-ramp(t, 3.9, 4.3))")
_s = sub(_s, "chip_seq(L2, t, [('睡眠中', (150, 160, 190), 0.0, 3.4), ('醒来', GOLD, 3.4, 5.0), ('醒来后走动', GOLD, 5.0, 99)], s, y=620)",
             "chip_seq(L2, t, [('睡眠中', (150, 160, 190), 0.0, 2.9), ('醒来', GOLD, 2.9, 6.3), ('醒来后走动', GOLD, 6.3, 99)], s, y=620)")
_s = sub(_s, "z = 1.04+0.05*lin(t, SF10_D)", "z = 1.04+0.05*lin(t, SF10_D)")
# time-lapse cue on the same camera: a small clock whose hand spins during the fast-forward
_s = sub(_s, "        L2.text((cx_, cy_+42*s), '光脉冲串反复给', F(SANS, 20*s), fill=BRIGHT, alpha=sk, anchor='ms')\n",
"""        L2.text((cx_, cy_+42*s), '光脉冲串反复给', F(SANS, 20*s), fill=BRIGHT, alpha=sk, anchor='ms')
        ccx, ccy = cx_+tw/2+60*s, cy_-9*s; L2.ring((ccx, ccy), 20*s, fill=CREAM, width=2*s, alpha=sk)
        hand = (t-2.5)*9.0; L2.line([(ccx, ccy), (ccx+15*s*math.sin(hand), ccy-15*s*math.cos(hand))], fill=CYAN, width=2.4*s, alpha=sk)
""")
exec(compile(_s, 'sf_r10_sf10', 'exec'), globals())

# ================================================================================================
# SF11: ChrimsonR first (<1 s, matches the narration order), then goggles -> beam -> fovea; <=3 labels at once;
#       the half-cropped lens disc at the left edge is painted out.
# ================================================================================================
_s = src_of("sf_r8.py", "EYE7 = ", end_marker=None); _e = _s.index("# ====", _s.index("def sf11")); _s = _s[:_e]
for o, n in (("C = (300*s, 515*s); R = int(152*s)", "C = (1010*s, 545*s); R = int(140*s)"),
             ("for sg in (-1, 1): L.line([(FX, FY), (px+r*math.cos(ang+sg*0.6), py+r*math.sin(ang+sg*0.6))], fill=AMBER, width=1.1*s, alpha=0.6*a)",
              "e1 = (px+r*math.cos(ang+0.75), py+r*math.sin(ang+0.75)); e2 = (px+r*math.cos(ang-0.75), py+r*math.sin(ang-0.75))\n"
              "        L.d.polygon([(FX*2, FY*2), (e1[0]*2, e1[1]*2), (e2[0]*2, e2[1]*2)], fill=(255, 190, 90, int(46*a)))\n"
              "        for e in (e1, e2): L.line([(FX, FY), e], fill=AMBER, width=1.8*s, alpha=0.9*a)"),
             ("label(L2, (X, Y), (60*s, 96*s), '护目镜', '把外界明暗换成琥珀色光脉冲', t=ramp(t, 0.3, 1.1), font_size=LT*s, sub_size=LS*s, accent=AMBER)", "pass"),
             ("(560*s, 70*s), '角膜、晶状体把光折向中央凹', None, t=ramp(t, 1.1, 1.9)", "(640*s, 60*s), '角膜、晶状体把光折向中央凹', None, t=ramp(t, 2.6, 3.3)"),
             ("(520*s, 448*s), '神经节细胞：膜上装了 ChrimsonR', '病毒载体（AAV，紫色小颗粒）把基因带进去', t=ramp(t, 2.7, 3.5)",
              "(760*s, 440*s), '神经节细胞：膜上装了 ChrimsonR', '病毒载体（AAV，紫色小颗粒）把基因带进去', t=ramp(t, 0.5, 1.2)"),
             ("(520*s, 640*s), '感光细胞：已大量丢失', None, t=ramp(t, 3.5, 4.2)", "(760*s, 660*s), '感光细胞：已大量丢失', None, t=ramp(t, 1.1, 1.7)"),
             ("on = ramp(t, 0.6, 1.1)", "on = ramp(t, 1.6, 2.0)"),
             ("grow = ramp(t, 0.6, 1.6)*tot", "grow = ramp(t, 1.6, 2.5)*tot"),
             ("        if t > 1.6:\n", "        if t > 2.5:\n"),
             ("alpha=ramp(t, 1.6, 1.9))", "alpha=ramp(t, 2.5, 2.8))"),
             ("0.8*ramp(t, 1.4, 1.7)*(0.8+0.2*math.sin(t*7))", "0.8*ramp(t, 2.3, 2.6)*(0.8+0.2*math.sin(t*7))"),
             ("a = ramp(t, 1.9, 2.6)", "a = ramp(t, 0.15, 0.7)"),
             ("ph = ((t-2.6-j*0.12) % 0.8)/0.8 if t > 2.6 else 1", "ph = ((t-2.5-j*0.12) % 0.8)/0.8 if t > 2.5 else 1"),
             ("fl = math.exp(-(ph/0.18)**2)*ramp(t, 2.6, 2.9)", "fl = math.exp(-(ph/0.18)**2)*ramp(t, 2.5, 2.8)"),
             ("_cache['eye7'] = cv2.inpaint(raw, m, 7, cv2.INPAINT_TELEA).astype(np.float32)/255",
              "_e7 = cv2.inpaint(raw, m, 7, cv2.INPAINT_TELEA).astype(np.float32)/255\n"
              "        sh = np.roll(_e7, -int(0.36*ih), axis=0); lm = np.zeros((ih, iw), np.float32); lm[:int(0.64*ih), :int(0.17*iw)] = 1\n"
              "        lm = cv2.GaussianBlur(lm, (0, 0), 0.012*iw)[..., None]; _cache['eye7b'] = _e7*(1-lm)+sh*lm"),
             ("im = _cache['eye7']; z", "im = _cache['eye7b']; z"),
             ("if 'eye7' not in _cache:", "if 'eye7b' not in _cache:")):
    _s = sub(_s, o, n)
_s = sub(_s, "def sf11(t, W, H):", "def _sf11_base10(t, W, H):"); _s = sub(_s, "@scene('SF11_eye_goggles', 5.0)\n", "")
exec(compile(_s, 'sf_r10_sf11', 'exec'), globals())

@scene('SF11_eye_goggles', 5.0)
def sf11(t, W, H):
    s = W/1280; rgb = _sf11_base10(t, W, H)
    C = (150*s, 150*s); R = int(112*s); a = ramp(t, 1.3, 1.9)
    if a > 0:
        L = Layer(W, H)
        L.dot(C, R+6*s, fill=(8, 10, 24), alpha=0.92*a)
        L.paste(circ_img(img('sf11_goggles'), R, zoom=1.7, cx=0.32, cy=0.44), (C[0]-R, C[1]-R), alpha=a)
        L.ring(C, R, fill=AMBER, width=2.4*s, alpha=a)
        rgb = over(rgb, L.get(), shadow=0.35)
        pl = ramp(t, 1.8, 2.1)*(0.6+0.4*math.sin(t*7.5)**2)
        rgb = rgb+radial(W, H, C[0]+8*s, C[1]+2*s, 14*s, (255, 200, 110), 0.7*pl)
    L2 = Layer(W, H); ta = ramp(t, 1.5, 2.1)
    if ta > 0:
        L2.rrect((C[0]+R+14*s, C[1]-46*s, C[0]+R+400*s, C[1]+44*s), 6*s, fill=(11, 16, 34), alpha=0.78*ta)
        L2.text((C[0]+R+28*s, C[1]-12*s), '护目镜（戴在眼前）', F(SANS_B, 22*s), fill=CREAM, alpha=ta, anchor='ls')
        L2.text((C[0]+R+28*s, C[1]+24*s), '摄像头看外界 → 打出琥珀色光脉冲', F(SANS, 20*s), fill=BRIGHT, alpha=ta, anchor='ls')
    return grade(over(rgb, L2.get()), seed=int(t*24)+7, grain=0.004, vig=0.0, lift=(0, 0, 0))

# ------------------------------------------------------------------------------------------------
# wrap every scene: label scale + scene clock for the label diet
# ------------------------------------------------------------------------------------------------
def _wrap10(name, fn):
    def g(t, W, H, *a, **k):
        R9._SC[0] = W/1280; _CUR[0] = name; _T[0] = t; return fn(t, W, H, *a, **k)
    g._r10 = True; return g
for _n in list(S):
    _fn, _d = S[_n]
    if not getattr(_fn, '_r10', False): S[_n] = (_wrap10(_n, _fn), _d)
S['SF10_mouse_tripo'] = (S['SF10_mouse_tripo'][0], SF10_D)
