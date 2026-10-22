"""Round 6 (Carl preferences v1.1): realistic cell scale, Goodsell only inside magnifiers at molecular scale."""
import sys; sys.path.insert(0, '/workspace/e2work/v8/tools')
from sf_r5 import *          # noqa
from sf_r5 import _cache, circ_img

# ---------------- SF06: one realistic neuron; magnifier into the missing switch; light flips the cell on ----------------
@scene('SF06_switch_diagram', 6.0)
def sf06(t, W, H):
    s = W/1280; u = lin(t, 6); im = img('sf06r_neuron'); ih, iw = im.shape[:2]
    if 'nm6' not in _cache:
        lum = cv2.GaussianBlur(im.mean(2), (0, 0), 1.2)
        m = np.clip((lum-0.22)/0.15, 0, 1); _cache['nm6'] = cv2.GaussianBlur(m, (0, 0), 1.5)[..., None]
    nm = _cache['nm6']
    on = ramp(t, 3.7, 4.4)
    # cell lights up from the soma outward once the switch is in place
    if on > 0:
        yy, xx = np.mgrid[0:ih, 0:iw]; d = np.hypot(xx/iw-0.74, (yy/ih-0.56)*0.6)
        front = np.clip((on*0.9-d)/0.08, 0, 1)[..., None]
        src = im + nm*front*np.array([0.25, 0.65, 1.0])*0.35*(0.9+0.1*math.sin(t*5))
    else: src = im
    z = 1.0+0.09*u; cxx = 0.50+0.03*u; cyy = 0.5
    rgb = cam(src, W, H, zoom=z, cx=cxx, cy=cyy); rgb = glow(rgb, 0.7, W/70, 0.35*on)
    P = lambda x, y: to_px(im, x, y, W, H, z, cxx, cyy)
    rgb = over(rgb, drift_specks(W, H, t, 50, 31, (170, 190, 255), 0.3, 1.5, (10, -4)), shadow=0)
    # magnifier from the soma membrane
    L = Layer(W, H); ax, ay = P(0.685, 0.50); C = (350*s, 330*s); R = int(165*s)
    a = ramp(t, 1.3, 2.1)
    if a > 0:
        k = ease_out(a); px, py = ax+(C[0]-ax)*k, ay+(C[1]-ay)*k; r = max(2, int(R*k))
        L.ring((ax, ay), 9*s, fill=CYAN, width=1.6*s, alpha=a)
        ang = math.atan2(ay-py, ax-px)
        for sg in (-1, 1): L.line([(ax, ay), (px+r*math.cos(ang+sg*0.5), py+r*math.sin(ang+sg*0.5))], fill=CYAN, width=1.0*s, alpha=0.6*a)
        L.dot((px, py), r+5*s, fill=(8, 10, 24), alpha=0.85*a)
        rev = ease(ramp(t, 2.5, 3.3))
        if rev > 0:
            ch = circ_img(img('sf09e_chr2'), r, zoom=2.1+0.15*u, cx=0.495, cy=0.47)
            L.paste(ch, (px-r, py-r), alpha=a*rev)
        if rev < 1: L.text((px, py+30*s*k), '?', F(SERIF_B, 96*s*k), fill=MUTED, alpha=a*(1-rev), anchor='ms')
        L.ring((px, py), r, fill=CYAN if rev > 0.5 else (130, 150, 200), width=2.2*s, alpha=a)
    rgb = over(rgb, L.get(), shadow=0.3)
    # blue light reaches the channel inside the magnifier, pores glow
    if t > 3.3:
        b = ramp(t, 3.3, 3.8)
        rgb = rgb+radial(W, H, C[0]-20*s, C[1]-60*s, 110*s, CYAN, 0.18*b*(0.85+0.15*math.sin(t*6)))
    L2 = Layer(W, H)
    L2.text((60*s, 86*s), '从设想到方法，中间缺什么？', F(SERIF_B, 32*s), fill=CREAM, alpha=ramp(t, 0, 0.7), anchor='ls', tracking=2*s)
    a3 = ramp(t, 3.0, 3.6)
    L2.text((C[0], C[1]+R+40*s), '一枚能用光拨动的开关', F(SANS_B, 26*s), fill=CYAN, alpha=a3, anchor='ms')
    L2.text((C[0], C[1]+R+68*s), '光控离子通道（如 ChR2），装在神经元膜上', F(SANS, 16*s), fill=(176, 186, 212), alpha=a3, anchor='ms')
    # small leader labels for the two new symbols inside the magnifier
    a4 = ramp(t, 3.4, 4.0)
    for (dx, dy, tx, ty, txt, col) in ((-112, -18, 110, 140, '视黄醛：吸收光', (255, 138, 61)), (-62, 40, 600, 140, '孔道：离子通过', CYAN)):
        x0, y0 = C[0]+dx*s, C[1]+dy*s; tx, ty = tx*s, ty*s
        L2.ring((x0, y0), 5*s, fill=col, width=1.5*s, alpha=a4)
        L2.line([(x0, y0), (x0+(tx-x0)*ease_out(a4), y0+(ty-y0)*ease_out(a4))], fill=col, width=1.1*s, alpha=0.9*a4)
        tw = F(SANS_B, 16*s).getlength(txt)
        L2.rrect((tx-tw/2-10*s, ty-24*s, tx+tw/2+10*s, ty+6*s), 6*s, fill=(12, 18, 38), alpha=0.85*a4)
        L2.text((tx, ty-3*s), txt, F(SANS_B, 16*s), fill=CREAM, alpha=a4, anchor='ms')
    # thin timeline overlay along the bottom
    y = 668*s; x0, x1 = 60*s, 1220*s; a0 = ramp(t, 0.4, 1.2)
    L2.line([(x0, y), (x0+(x1-x0)*ease_out(ramp(t, 0.4, 4.8)), y)], fill=(120, 132, 170), width=1.2*s, alpha=a0)
    nodes = [(0.0, 0.6, '1999', '一句自认牵强的设想', GOLD), (0.45, 1.8, '？', '缺一枚光控开关', CYAN), (1.0, 4.6, '2026 诺奖', '一套能用的方法：光遗传学', GOLD)]
    for (q, t0, yr, txt, col) in nodes:
        aa = ramp(t, t0, t0+0.5); x = x0+(x1-x0)*q
        if aa <= 0: continue
        L2.dot((x, y), 5*s, fill=col, alpha=aa)
        an = 'l' if q < 0.9 else 'r'; xo = x+(10*s if an == 'l' else -10*s)
        L2.text((xo, y-12*s), yr+'  '+txt, F(SANS_B, 16*s), fill=CREAM, alpha=aa, anchor=an+'s')
    return grade(over(rgb, L2.get()), seed=int(t*24))

# ---------------- SF02: reframe (no desk slab, bright neuron fully in frame), kill unmotivated blue haze, constant drift ----------------
import sf_scenes as _SS
from sf_scenes import _cache
def _sf02_core(t,W,H):
    im=img('sf02_1979_crowd')
    if 'g2' not in _cache:
        hsv=cv2.cvtColor((im*255).astype(np.uint8),cv2.COLOR_RGB2HSV).astype(np.float32)
        m=((hsv[...,0]>10)&(hsv[...,0]<32)&(hsv[...,1]>90)&(hsv[...,2]>120)).astype(np.uint8)
        m[int(im.shape[0]*0.42):, :int(im.shape[1]*0.42)]=0; m[:int(im.shape[0]*0.35),:int(im.shape[1]*0.3)]=0
        nlab,lab=cv2.connectedComponents(cv2.dilate(m,np.ones((9,9),np.uint8)))
        area=np.bincount(lab.ravel()); xs_=np.array([np.nonzero(lab==k)[1].mean() if area[k]>0 else 0 for k in range(nlab)])
        big=[k for k in range(1,nlab) if area[k]>120]; big.sort(key=lambda k:xs_[k])
        order={k:i/max(1,len(big)-1) for i,k in enumerate(big)}; _cache['g2']=(lab,order,m)
        gray=im.mean(2,keepdims=True); _cache['d2']=im*0.32+gray*np.array([0.40,0.42,0.56])*0.45
    lab,order,m=_cache['g2']
    on=np.zeros(lab.shape,np.float32)
    for k in range(1,lab.max()+1):
        tk=1.0+1.6*order.get(k,0.5); on[lab==k]=ramp(t,tk,tk+0.6)
    pulse=np.zeros(lab.shape,np.float32)
    for k in range(1,lab.max()+1):
        tk=1.0+1.6*order.get(k,0.5)+0.3; pulse[lab==k]=math.exp(-((t-tk)/0.25)**2)
    gm=cv2.GaussianBlur(m.astype(np.float32)*on,(0,0),2)[...,None]; pm=cv2.GaussianBlur(m.astype(np.float32)*pulse,(0,0),6)[...,None]
    base=_cache['d2']*(1-gm)+np.clip(im*(1.15+0.5*gm),0,1)*gm+pm*np.array([1.0,0.75,0.35])*0.6
    z=1.40+0.09*(t/5); cx,cy=0.625+0.02*t/5,0.455
    rgb=cam(base,W,H,zoom=z,cx=cx,cy=cy); rgb=glow(rgb,0.6,W/90,0.7)
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


@scene('SF02_1979_request', 5.0)
def sf02(t, W, H):
    _SS.ease = lambda x: x                     # constant-speed push (the r3 code eases to a stop)
    try:
        rgb = _sf02_core(t, W, H)
    finally:
        _SS.ease = ease
    yy, xx = np.mgrid[0:H, 0:W]
    d = np.exp(-(((xx/W-1.0)/0.35)**2+((yy/H-0.0)/0.45)**2))[..., None]
    return np.clip(rgb*(1-0.55*d), 0, 1)

# ---------------- SF09 r6: retinal visibly isomerises (all-trans -> 13-cis), pore dark until it opens ----------------
def retinal_bent(k):
    C, b, n, a = mol.retinal_geom(); C = dict(C)
    cx, cy = C['C13']; ang = math.radians(-75*k)
    for key in ('C14', 'C15', 'N', 'Lys'):
        x, y = C[key][0]-cx, C[key][1]-cy
        C[key] = (cx+x*math.cos(ang)-y*math.sin(ang), cy+x*math.sin(ang)+y*math.cos(ang))
    return (C, b, n, a)
_ret_cache = {}
def ret_sprite(k, px, ang, flip):
    key = (round(k, 2), px, ang, flip)
    if key not in _ret_cache:
        C, b, n, a = retinal_bent(k)
        if flip: C = {kk: (-x, y) for kk, (x, y) in C.items()}
        _ret_cache[key] = mol.draw((C, b, n, a), px, ang)
    return _ret_cache[key]

@scene('SF09_chr2_channel', 5.0)
def sf09(t, W, H):
    im = img('sf09f_noret'); ih, iw = im.shape[:2]; s = W/1280; u = lin(t, 5); z = 1.30+0.10*u; cxx = 0.49; cyy = 0.44
    on = ramp(t, 0.3, 1.0); bend = ease(ramp(t, 1.05, 1.45)); opn = ramp(t, 1.5, 2.0)
    if 'pore9' not in _cache:
        cm = cyan_mask(im, 140, 6); yy, xx = np.mgrid[0:ih, 0:iw]
        pore = (((np.abs(xx/iw-0.434) < 0.02) | (np.abs(xx/iw-0.548) < 0.02)) & (yy/ih > 0.30) & (yy/ih < 0.66)).astype(np.float32)
        _cache['pore9'] = (cv2.GaussianBlur(pore, (0, 0), 6)*cm)[..., None]
        _cache['beam9'] = (cm[..., None]-_cache['pore9']).clip(0, 1)
    pm = _cache['pore9']; bm = _cache['beam9']
    teal = np.array([0.22, 0.62, 0.58])*(0.75+0.25*cv2.GaussianBlur(im.mean(2), (0, 0), 3)[..., None])
    base = im*(1-pm*(1-opn))+teal*pm*(1-opn)
    base = base*(1-bm*(1-(0.55+0.45*on)))
    # live retinal, ring end fixed to the protein
    base8 = base.copy()
    for (cx0, cy0, ang, flip) in ((0.394, 0.452, 38, False), (0.600, 0.458, -38, True)):
        spr0, P0 = ret_sprite(0, int(0.085*iw), ang, flip); spr, P1 = ret_sprite(round(bend*20)/20, int(0.085*iw), ang, flip)
        ax = cx0*iw-spr0.size[0]/2+P0['C1'][0]/4; ay = cy0*ih-spr0.size[1]/2+P0['C1'][1]/4
        c = (ax-P1['C1'][0]/4+spr.size[0]/2, ay-P1['C1'][1]/4+spr.size[1]/2)
        base8 = mol.composite(base8, spr, c)
    rgb = cam(base8, W, H, zoom=z, cx=cxx, cy=cyy)
    P = lambda x, y: to_px(im, x, y, W, H, z, cxx, cyy)
    for (rx, ry) in ((0.394, 0.452), (0.600, 0.458)):
        X, Y = P(rx, ry); rgb = rgb+radial(W, H, X, Y, 40*s, (255, 160, 80), 0.4*math.exp(-((t-1.1)/0.3)**2))
    L = Layer(W, H); rng = np.random.default_rng(9); offs = rng.random((2, 15))*0.6
    for j, (px_, ph0) in enumerate(((0.434, 0.0), (0.548, 0.5))):
        for n in range(15):
            p = (t*0.36+n/15+ph0+offs[j, n]*0.05) % 1.0
            if t < 2.4 and p > 0.15+0.85*ramp(t, 1.7, 2.4): continue
            X, Y = P(px_+0.004*math.sin(n*2.3+p*8), 0.20+p*0.62); a = ramp(t, 1.7, 2.0)*min(1, p*8)*min(1, (1-p)*8)
            L.dot((X, Y), 5.0*s*z, fill=(255, 209, 102), alpha=a)
    rgb = over(rgb, L.get(), shadow=0.3, glow_amt=0.6)
    rgb = over(rgb, drift_specks(W, H, t, 40, 13, (160, 190, 255), 0.25, 1.4, (4, 2)), shadow=0)
    L2 = Layer(W, H)
    X, Y = P(0.33, 0.12); label(L2, (max(X, 40*s), max(Y, 40*s)), (60*s, 96*s), '蓝光 约 470 nm', None, t=ramp(t, 0.4, 1.1), font_size=LT*s, accent=CYAN)
    X, Y = P(0.378, 0.432); label(L2, (X, Y), (60*s, 620*s), '视黄醛', '吸收蓝光后弯折，带动这扇门打开', t=ramp(t, 0.9, 1.7), font_size=LT*s, sub_size=LS*s, accent=(255, 138, 61))
    X, Y = P(0.60, 0.33); label(L2, (X, Y), (1220*s, 96*s), '通道视紫红质-2（ChR2）', '二聚体：每个亚基各有一条孔道', t=ramp(t, 1.9, 2.7), font_size=LT*s, sub_size=LS*s, accent=(99, 199, 168))
    X, Y = P(0.548, 0.70); label(L2, (X, Y), (1220*s, 630*s), '阳离子（如 Na⁺）', '门开后顺浓度梯度涌入细胞', t=ramp(t, 2.6, 3.4), font_size=LT*s, sub_size=LS*s, accent=(255, 209, 102))
    X, Y = P(0.78, 0.42); label(L2, (X, Y), (1220*s, 470*s), '其他膜蛋白', '不受光控制', t=ramp(t, 3.4, 4.1), font_size=19*s, sub_size=LS*s, accent=(150, 146, 180))
    return grade(over(rgb, L2.get()), seed=int(t*24))

# ---------------- SF04 r6: the quote is about light -> a light beam enters as "光" is read, motes drift in it ----------------
_sf04_r5 = S['SF04_crick_quote'][0]
@scene('SF04_crick_quote', 5.0)
def sf04(t, W, H):
    rgb = _sf04_r5(t, W, H); s = W/1280
    a = ramp(t, 0.9, 1.9); u = lin(t, 5)
    if a > 0:
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        sx, sy = 1300*s, -60*s; ex, ey = 700*s+40*s*u, 330*s          # beam from upper right falls toward the quote
        dx, dy = ex-sx, ey-sy; Ln = math.hypot(dx, dy); nx, ny = -dy/Ln, dx/Ln
        along = ((xx-sx)*dx+(yy-sy)*dy)/Ln/Ln; across = (xx-sx)*nx+(yy-sy)*ny
        width = 30*s+140*s*np.clip(along, 0, 1.3)
        beam = np.exp(-(across/width)**2)*np.clip(along*3, 0, 1)*np.clip((1.35-along)*2, 0, 1)
        flick = 0.85+0.15*math.sin(t*3.1)
        rgb = rgb+beam[..., None]*np.array(CYAN)/255*0.30*a*flick
        Lm = Layer(W, H); beam_motes(Lm, t, (sx, sy), (ex, ey), 110*s, n=55, seed=12, amt=0.7*a, s=s, speed=0.10)
        rgb = over(rgb, Lm.get(), shadow=0, glow_amt=0.8)
    return np.clip(rgb, 0, 1)
