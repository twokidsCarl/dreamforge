"""Round 6b (Carl v1.2, 17:44): whole set in the SF08/SF09 Goodsell-style illustration family.
Plates restyled with image2 (style ref = sf09d); subject motion from Wan i2v where available; overlays added after."""
import sys, os; sys.path.insert(0, '/workspace/e2work/v8/tools')
from sf_r6 import *          # noqa
from sf_r6 import _cache
import sf_r5 as R5, sf_r6 as R6

GV = '/workspace/e2work/v8/gen/vid/'
_vids = {}
def vframes(name, size):
    """all frames of a Wan clip as float RGB, resized to the plate size (w,h)"""
    if name not in _vids:
        cap = cv2.VideoCapture(GV+name+'.mp4'); fr = []; fps = cap.get(cv2.CAP_PROP_FPS) or 24
        while True:
            ok, f = cap.read()
            if not ok: break
            fr.append(cv2.resize(cv2.cvtColor(f, cv2.COLOR_BGR2RGB), size, interpolation=cv2.INTER_CUBIC).astype(np.float32)/255)
        _vids[name] = (fr, fps)
    return _vids[name]
def vat(name, t, size):
    fr, fps = vframes(name, size); x = min(max(t*fps, 0), len(fr)-1.001); i = int(x); a = x-i
    return fr[i]*(1-a)+fr[min(i+1, len(fr)-1)]*a
def have(name): return os.path.exists(GV+name+'.mp4')

def alias(old, new):
    _cache[old] = img(new)

# restyled plates replace the old ones under the old names, so the tuned scene code keeps working
alias('sf01b_open_bg', 'sf01c_open_bg')
alias('sf02_1979_crowd', 'sf02b_crowd')
alias('sf03d_microbes', 'sf03e_microbes')
alias('sf06r_neuron', 'sf06s_neuron')

# ---------------- SF01: Wan light-wave clip as the plate; plate darkened on the left so the title sits on a calm field ----------------
def _darkL(a, edge=0.56, amt=0.78):
    h, w = a.shape[:2]; xx = np.arange(w)[None, :, None]/w; m = np.clip((edge-xx)/0.25, 0, 1)
    return a*(1-amt*m)+np.array(INK, np.float32)/255*amt*m
_sf01 = S['SF01_open_title'][0]
_sf01_plate = _darkL(img('sf01c_open_bg'))
_cache['fg1'] = cv2.GaussianBlur(_darkL(img('sf01c_open_bg'), 0.9, 0.85), (0, 0), 18)   # calm foreground haze, not the mirrored bright neurons
@scene('SF01_open_title', 5.0)
def sf01(t, W, H):
    base = img('sf01c_open_bg')
    _cache['sf01b_open_bg'] = _darkL(vat('sf01_wave', t, (base.shape[1], base.shape[0]))) if have('sf01_wave') else _sf01_plate
    return _sf01(t, W, H)

from sf_scenes import ramp as _r
def _sf02_core7(t,W,H):
    im=img('sf02_1979_crowd')
    if 'g2b' not in _cache:
        hsv=cv2.cvtColor((im*255).astype(np.uint8),cv2.COLOR_RGB2HSV).astype(np.float32)
        m=((hsv[...,0]>10)&(hsv[...,0]<32)&(hsv[...,1]>90)&(hsv[...,2]>120)).astype(np.uint8)
        m[int(im.shape[0]*0.42):, :int(im.shape[1]*0.42)]=0; m[:int(im.shape[0]*0.35),:int(im.shape[1]*0.3)]=0
        nlab,lab=cv2.connectedComponents(cv2.dilate(m,np.ones((9,9),np.uint8)))
        area=np.bincount(lab.ravel()); xs_=np.array([np.nonzero(lab==k)[1].mean() if area[k]>0 else 0 for k in range(nlab)])
        big=[k for k in range(1,nlab) if area[k]>120]; big.sort(key=lambda k:xs_[k])
        order={k:i/max(1,len(big)-1) for i,k in enumerate(big)}; _cache['g2b']=(lab,order,m)
        gray=im.mean(2,keepdims=True); _cache['d2b']=im*0.32+gray*np.array([0.40,0.42,0.56])*0.45
    lab,order,m=_cache['g2b']
    on=np.zeros(lab.shape,np.float32)
    for k in range(1,lab.max()+1):
        tk=1.0+1.6*order.get(k,0.5); on[lab==k]=ramp(t,tk,tk+0.6)
    pulse=np.zeros(lab.shape,np.float32)
    for k in range(1,lab.max()+1):
        tk=1.0+1.6*order.get(k,0.5)+0.3; pulse[lab==k]=math.exp(-((t-tk)/0.25)**2)
    gm=cv2.GaussianBlur(m.astype(np.float32)*on,(0,0),2)[...,None]; pm=cv2.GaussianBlur(m.astype(np.float32)*pulse,(0,0),6)[...,None]
    base=_cache['d2b']*(1-gm)+im*0.92*gm+pm*np.array([1.0,0.75,0.35])*0.35
    z=1.80+0.10*(t/5); cx,cy=0.70+0.02*t/5,0.43
    rgb=cam(base,W,H,zoom=z,cx=cx,cy=cy); rgb=glow(rgb,0.75,W/90,0.3)
    rgb=over(rgb,drift_specks(W,H,t,40,5,(255,220,170),0.25),shadow=0)
    L=Layer(W,H); s=W/1280
    L.rrect((56*s,52*s,470*s,124*s),6*s,fill=(14,20,40),alpha=0.8*ramp(t,0.2,0.9))
    L.line([(56*s,52*s),(56*s,124*s)],fill=GOLD,width=3*s,alpha=ramp(t,0.2,0.9))
    L.text((76*s,84*s),'Francis Crick · 1979',F(SANS_B,23*s),fill=CREAM,alpha=ramp(t,0.3,1.0),anchor='ls')
    L.text((76*s,110*s),'《科学美国人》 Thinking about the Brain',F(SANS,16*s),fill=(176,186,212),alpha=ramp(t,0.4,1.1),anchor='ls')
    a=ramp(t,2.6,3.4); bx=56*s; by=590*s
    L.rrect((bx,by,bx+380*s,by+92*s),8*s,fill=(12,18,38),alpha=0.8*a)
    L.dot((bx+26*s,by+30*s),6*s,fill=GOLD,alpha=a); L.text((bx+44*s,by+38*s),'只动某一类神经元',F(SANS_B,25*s),fill=CREAM,alpha=a,anchor='ls')
    b=ramp(t,3.3,4.0)
    L.dot((bx+26*s,by+70*s),6*s,fill=(130,134,160),alpha=b); L.text((bx+44*s,by+78*s),'其余的大体不动',F(SANS,22*s),fill=(176,186,212),alpha=b,anchor='ls')
    return grade(over(rgb,L.get()),seed=int(t*24))



# ---------------- SF02: tighter framing on the neuron field (plate has a desk at lower-left) ----------------
@scene('SF02_1979_request', 5.0)
def sf02(t, W, H):
    R6._SS.ease = lambda x: x
    try:
        rgb = _sf02_core7(t, W, H)
    finally:
        R6._SS.ease = ease
    yy, xx = np.mgrid[0:H, 0:W]
    d = np.exp(-(((xx/W-1.0)/0.35)**2+((yy/H-0.0)/0.45)**2))[..., None]
    return np.clip(rgb*(1-0.45*d), 0, 1)

# ---------------- SF03: restyled plate; Wan swim clip when available ----------------
_sf03 = S['SF03_microbe_clues'][0]
@scene('SF03_microbe_clues', 5.0)
def sf03(t, W, H):
    base = img('sf03e_microbes')
    if have('sf03_swim'): _cache['sf03d_microbes'] = vat('sf03_swim', t, (base.shape[1], base.shape[0]))
    return _sf03(t, W, H)

# ---------------- SF07: restyled brain; the portrait plate sits on a blurred, darkened extension of itself ----------------
@scene('SF07_main_title', 5.0)
def sf07(t, W, H):
    s = W/1280; im = img('sf07e_title_bg'); ih, iw = im.shape[:2]; u = lin(t, 5)
    if 'p7e' not in _cache:
        tip = (0.59, 0.20); yy, xx = np.mgrid[0:ih, 0:iw]; d = np.hypot(xx/iw-tip[0], (yy/ih-tip[1])*1.5)
        cm2 = cyan_mask(im, 175, 1.0)*(d < 0.18); ys, xs = np.nonzero(cm2 > 0.5); rng = np.random.default_rng(2)
        idx = rng.choice(len(xs), min(110, len(xs)), replace=False) if len(xs) else []
        ext = cv2.GaussianBlur(im, (0, 0), 30)*0.45
        _cache['p7e'] = ([(xs[i]/iw, ys[i]/ih, rng.random()) for i in idx], tip, ext)
    pts, tip, ext = _cache['p7e']
    bgc = cam(ext, W, H, zoom=1.0+0.05*u, cx=0.5, cy=0.35)
    z = 1.0+0.12*u; sc_ = H*0.95/ih*z; Wi, Hi = int(iw*sc_), int(ih*sc_)
    ox = W*0.5-0.5*Wi-14*s*u; oy = H*0.10-0.12*Hi+4*s*u
    M = np.array([[sc_, 0, ox], [0, sc_, oy]], np.float32)
    pic = cv2.warpAffine(im, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
    yy, xx = np.mgrid[0:H, 0:W]
    e = np.minimum.reduce([(xx-ox)/(160*s), (ox+Wi-xx)/(160*s)]); mk = np.clip(e, 0, 1)[..., None]
    rgb = bgc*(1-mk)+pic*mk
    # calm the lower third for the title
    lm = np.clip((yy/H-0.62)/0.2, 0, 1)[..., None]; rgb = rgb*(1-0.6*lm)+np.array(INK)/255*0.6*lm
    L = Layer(W, H)
    for (px, py, ph) in pts:
        d = math.hypot(px-tip[0], (py-tip[1])*1.5); a = 0.2*(t > 0.7+d*8)
        for w0 in (0.7, 2.2, 3.7): a += math.exp(-((t-(w0+d*8.0+ph*0.15))/0.16)**2)
        L.dot((ox+px*Wi, oy+py*Hi), 2.2*s, fill=(170, 225, 255), alpha=min(1, a))
    fx = ox+tip[0]*Wi; fbot = oy+tip[1]*Hi
    for n in range(5):
        p = (t*0.9+n/5) % 1.0; L.dot((fx, fbot*p), 2.6*s, fill=(210, 240, 255), alpha=ramp(t, 0.4, 0.8)*min(1, (1-p)*6))
    rgb = over(rgb, L.get(), shadow=0, glow_amt=1.4)
    rgb = rgb+radial(W, H, fx, fbot, 60*s, CYAN, 0.35*ramp(t, 0.5, 1.2)*(0.85+0.15*math.sin(t*4)))
    rgb = over(rgb, drift_specks(W, H, t, 60, 11, (180, 205, 255), 0.3, 1.6, (10, -5)), shadow=0)
    L = Layer(W, H)
    a = ramp(t, 1.0, 2.2); tr = (60*(1-ease_out(ramp(t, 1.0, 3.2)))+34)*s
    L.text((W/2, 598*s), '光遗传学', F(SERIF_B, 108*s), fill=CREAM, alpha=a, anchor='ms', tracking=tr)
    L.text((W/2, 640*s), 'O P T O G E N E T I C S', F(SANS, 17*s), fill=CYAN, alpha=ramp(t, 2.0, 2.8), anchor='ms', tracking=4*s)
    L.text((W/2, 680*s), '这一期，就讲这枚开关', F(SANS, 22*s), fill=(190, 198, 222), alpha=ramp(t, 2.6, 3.4), anchor='ms', tracking=4*s)
    return grade(over(rgb, L.get(), glow_amt=0.35), seed=int(t*24))

# ---------------- SF10: Wan continuous wake-up (sleep -> stand), light leads the waking, then walks ----------------
def _track10():
    if 'trk10' in _cache: return _cache['trk10']
    A = img('sf10_awake'); size = (A.shape[1], A.shape[0])
    fr, fps = vframes('sf10_wake', size); ih, iw = A.shape[:2]
    g = [cv2.cvtColor((f*255).astype(np.uint8), cv2.COLOR_RGB2GRAY) for f in fr]
    x, y = int(0.612*iw), int(0.315*ih); r = 22; pos = []
    for k in range(len(g)):
        if k == 0: tpl = g[0][y-r:y+r, x-r:x+r]
        x0, y0 = max(0, x-120), max(0, y-120); win = g[k][y0:y+120, x0:x+120]
        res = cv2.matchTemplate(win, tpl, cv2.TM_CCOEFF_NORMED); _, _, _, ml = cv2.minMaxLoc(res)
        x, y = x0+ml[0]+r, y0+ml[1]+r; pos.append((x/iw, y/ih))
        tpl = g[k][y-r:y+r, x-r:x+r] if k % 3 == 0 else tpl
    pos = np.array(pos); pos = np.stack([cv2.GaussianBlur(pos[:, i].reshape(-1, 1), (1, 0), 2).ravel() for i in (0, 1)], 1)
    _cache['trk10'] = (pos, fps); return _cache['trk10']

@scene('SF10_mouse_tripo', 7.5)
def sf10(t, W, H, still=False, still_frame=None):
    if still: t = 6.2
    s = W/1280; A = img('sf10_awake'); ih, iw = A.shape[:2]; TV = 4.95
    z = 1.04+0.08*lin(t, 7.5); cxx = 0.56-0.03*lin(t, 7.5); cyy = 0.50
    P = lambda x, y: to_px(A, x, y, W, H, z, cxx, cyy)
    if t < TV:
        frame = vat('sf10_wake', t, (iw, ih)); pos, fps = _track10(); k = min(int(t*fps), len(pos)-1)
        ix, iy = pos[k]
        rgb = cam(frame, W, H, zoom=z, cx=cxx, cy=cyy)
        on = ramp(t, 0.5, 0.9)*(1-ramp(t, 3.4, 3.9))                 # our glow leads; the clip's own glow takes over ~3.5 s
        X, Y = P(ix, iy); Lf = Layer(W, H)
        if on > 0:
            for q in np.linspace(0, 1, 40): Lf.dot((X+(P(ix+0.004, 0)[0]-X)*(1-q)*0, Y*q), 1.8*s, fill=CYAN, alpha=0.9*on)
        rgb = over(rgb, Lf.get(), shadow=0, glow_amt=1.2)
        rgb = rgb+radial(W, H, X, Y, 22*s, CYAN, 0.75*on)+radial(W, H, X, Y, 90*s, CYAN, 0.14*on)
        imp = (X, Y-6*s)
    else:
        R5._sf10_prep(); A_, Cn, alpha = _cache['m10']
        t_walk = t-TV; v = 0.05*iw; dxm = -v*t_walk
        src_pts, dsp = R5._warp_mouse(5.0, t_walk, iw, ih)
        x0, x1, y0, y1 = int(0.40*iw), int(1.0*iw), 0, int(0.82*ih)
        gy, gx = np.mgrid[y0:y1:8, x0:x1:8]; grid = np.stack([gx.ravel(), gy.ravel()], 1).astype(np.float64)
        D = R5.RBFInterpolator(src_pts+dsp, dsp, kernel='thin_plate_spline', smoothing=1.0)(grid).reshape(gx.shape+(2,)).astype(np.float32)
        D = cv2.resize(D, (x1-x0, y1-y0), interpolation=cv2.INTER_LINEAR)
        fully, fullx = np.mgrid[0:ih, 0:iw].astype(np.float32); mapx = fullx-dxm; mapy = fully.copy()
        yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32); mapx[y0:y1, x0:x1] = xx-D[..., 0]-dxm; mapy[y0:y1, x0:x1] = yy-D[..., 1]
        mouse = cv2.remap(A_, mapx, mapy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
        al = cv2.remap(alpha, mapx, mapy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)[..., None]
        yyp, xxp = np.mgrid[0:ih, 0:iw]
        sh = np.exp(-(((xxp-(0.72*iw+dxm))/(0.20*iw))**2+((yyp-0.725*ih)/(0.022*ih))**2))[..., None]
        plate = Cn*(1-0.45*sh)*(1-al)+mouse*al
        # blend the first 0.25 s from the clip's last frame into the walk plate (they are the same pose)
        last = vat('sf10_wake', 99, (iw, ih)); b = ramp(t_walk, 0.0, 0.25)
        plate = last*(1-b)+plate*b
        rgb = cam(plate, W, H, zoom=z, cx=cxx, cy=cyy)
        X, Y = P((0.602*iw+dxm)/iw, 0.265); imp = (X, Y)
        rgb = rgb+radial(W, H, X, Y, 20*s, CYAN, 0.5)
    rgb = over(rgb, drift_specks(W, H, t, 30, 17, (190, 215, 255), 0.22, 1.3, (3, -2)), shadow=0)
    L2 = Layer(W, H)
    label(L2, imp, (60*s, 96*s), '光纤 + 颅骨植入件', '把蓝光送进下丘脑外侧那群细胞', t=ramp(t, 0.6, 1.3), font_size=LT*s, sub_size=LS*s, accent=CYAN)
    a = ramp(t, 0.2, 0.9)
    L2.rrect((56*s, 612*s, 560*s, 684*s), 6*s, fill=(14, 20, 40), alpha=0.78*a); L2.line([(56*s, 612*s), (56*s, 684*s)], fill=GOLD, width=3*s, alpha=a)
    L2.text((76*s, 642*s), '2007 · 小鼠 · 食欲素神经元', F(SANS_B, 21*s), fill=CREAM, alpha=a, anchor='ls')
    L2.text((76*s, 670*s), '光一开：从睡眠转入清醒的概率升高', F(SANS, 16*s), fill=(176, 186, 212), alpha=a, anchor='ls')
    st = [('睡眠中', (150, 160, 190), 0.0, 0.5), ('光开', CYAN, 0.5, 2.2), ('这一次：醒来', GOLD, 2.2, TV), ('走动', GOLD, TV, 99)]
    for name, col, a0, a1 in st:
        aa = (ramp(t, a0, a0+0.25) if a0 > 0 else 1)*(1-ramp(t, a1, a1+0.25))
        if aa <= 0: continue
        tw_ = F(SANS_B, 20*s).getlength(name)
        L2.rrect((1200*s-tw_-60*s, 44*s, 1230*s, 88*s), 22*s, fill=(12, 18, 38), alpha=0.8*aa); L2.dot((1200*s-tw_-34*s, 66*s), 7*s, fill=col, alpha=aa)
        L2.text((1200*s-tw_-18*s, 74*s), name, F(SANS_B, 20*s), fill=CREAM, alpha=aa, anchor='ls')
    return grade(over(rgb, L2.get()), seed=int(t*24))
