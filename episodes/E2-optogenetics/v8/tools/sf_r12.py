"""Round 11 (PROMPT 第 11 轮, 2026-10-23): only the round-10 independent-review Top gaps.  Narration NOT changed.
1 SF04/SF05 portraits: repainted in the Goodsell family (image2 sf04h_/sf05h_*: bead texture, soft 3D shading,
  membrane ground) instead of gold line art -> no square glow edge; person/ground parallax (GrabCut split, ground
  inpainted) as secondary motion; SF05 light streams badge -> icon, picture icons, footnote on a plate (>=7:1).
2 SF03: the alga is a sprite cut from the still (rigid drift + rotational flagellar beat) instead of the Wan clip
  (no flagellum warping / stray segment); eyespot moved to the cell equator; label fades staggered (no ghosts).
3 SF10: new mouse-proportioned plates (sf10s2/sf10a2) -> Wan 3.0 first/last wake + Wan 2.6 walk; the eyes-shut
  frames (f77-83) cut out and bridged by optical flow; implant light only during the pulse trains.
4 SF07: new dorsal mouse brain (sf07g_brain: olfactory bulbs, smooth cortex, colliculi, foliated cerebellum).
5 key labels held to the last frame (SF08 route-one summary, SF09 retinal, SF11 photoreceptors);
  SF02 burst decays over ~6 frames."""
import sys, os, math; sys.path.insert(0, '/workspace/e2work/v8/tools')
import sf, sf_scenes
import sf_r11 as R11
from sf_r11 import *          # noqa
from sf_r11 import _cam0, _cache, _gold_neuron
import sf_r10 as R10, sf_r9 as R9, sf_r8 as R8, sf_r5 as R5
from sf_r5 import circ_img
TOOLS = '/workspace/e2work/v8/tools/'

# ================================================================================================
# SF02: synchronous burst = quick attack, ~6-frame decay (was a 2-frame sin^4 spike); rings fade in
# ================================================================================================
def _env12(t):
    p = ((t-2.9)*1.25) % 1.0
    if p < 0.10: return 0.0
    if p < 0.25: return ease((p-0.10)/0.15)
    return math.exp(-(p-0.25)/0.20)
R10._env12 = _env12
R11.rerun10('sf02', [("max(0.0, math.sin((t-2.9)*2*math.pi*1.25))**4", "_env12(t)"),
                     ("alpha=0.7*(1-ph)*ramp(t, 2.9, 3.2)", "alpha=0.7*(1-ph)*min(1, ph*6)*ramp(t, 2.9, 3.2)")])

# ================================================================================================
# labels held to the end
# ================================================================================================
R10.LBL.pop(('SF09_chr2_channel', '视黄醛'), None)
R10.LBL.pop(('SF11_eye_goggles', '感光细胞：已大量丢失'), None)

# ================================================================================================
# SF08: slower pan; a one-line route-one summary stays on screen after the pan
# ================================================================================================
_c8 = R11._code8
_c8 = _c8[:_c8.rindex("exec(compile(_s, 'sf_r11_sf08'")]
_c8 += "_s = sub(_s, 'pan = ease(ramp(t, 3.3, 4.5))', 'pan = ease(ramp(t, 3.1, 4.8))')\n"
_c8 += ("_s = sub(_s, '    # light -> channel open: the only quantity', "
        "\"    X1, Y1 = P(0.415, 0.40); label(L, (X1, Y1), (300*s, 196*s), '路线一：好几步接力', '信号一级传一级', t=ramp(t, 4.9, 5.5), font_size=LT*s, sub_size=LS*s, accent=(255, 226, 176))\\n"
        "    # light -> channel open: the only quantity\")\n")
_c8 += "exec(compile(_s, 'sf_r12_sf08', 'exec'), globals())\n"
exec(compile(_c8, 'rerun_sf08_r12', 'exec'), R10.__dict__)

# ================================================================================================
# portraits: person / ground split (GrabCut) with the ground inpainted -> parallax between the two
# ================================================================================================
def port_split(key):
    k = ('ps12', key)
    if k in _cache: return _cache[k]
    im = img(key); h, w = im.shape[:2]
    sm = cv2.resize((im*255).astype(np.uint8), (w//2, h//2), interpolation=cv2.INTER_AREA); hh, ww = sm.shape[:2]
    hsv = cv2.cvtColor(sm, cv2.COLOR_RGB2HSV).astype(int); lum = sm.mean(2)
    m = np.full((hh, ww), cv2.GC_PR_BGD, np.uint8)
    skin = (hsv[..., 0] < 30) & (hsv[..., 1] > 40) & (lum > 120)
    white = (hsv[..., 1] < 50) & (lum > 170)
    m[skin | white] = cv2.GC_PR_FGD
    m[:int(hh*0.18)] = np.where(m[:int(hh*0.18)] == cv2.GC_PR_FGD, cv2.GC_PR_BGD, m[:int(hh*0.18)])
    if 'deisseroth' in key:     # dark curly hair: the head-top region is figure
        hm = np.zeros((hh, ww), np.uint8); cv2.ellipse(hm, (int(ww*0.45), int(hh*0.27)), (int(ww*0.26), int(hh*0.19)), 0, 0, 360, 1, -1)
        m[(hm > 0)] = cv2.GC_PR_FGD; m[(hm > 0) & (lum < 90)] = cv2.GC_FGD
    cv2.ellipse(m, (int(ww*0.49), int(hh*0.45)), (int(ww*0.11), int(hh*0.15)), 0, 0, 360, int(cv2.GC_FGD), -1)
    m[int(hh*0.86):, int(ww*0.32):int(ww*0.68)] = cv2.GC_FGD
    m[:int(hh*0.12), :int(ww*0.14)] = cv2.GC_BGD; m[:int(hh*0.12), -int(ww*0.14):] = cv2.GC_BGD
    m[int(hh*0.25):int(hh*0.55), :int(ww*0.04)] = cv2.GC_BGD; m[int(hh*0.25):int(hh*0.55), -int(ww*0.04):] = cv2.GC_BGD
    bg = np.zeros((1, 65), np.float64); fg = np.zeros((1, 65), np.float64)
    cv2.grabCut(sm, m, None, bg, fg, 6, cv2.GC_INIT_WITH_MASK)
    sil = ((m == 1) | (m == 3)).astype(np.uint8)
    sil = cv2.morphologyEx(sil, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(sil)
    if n > 1: sil = (lab == 1+int(np.argmax(st[1:, cv2.CC_STAT_AREA]))).astype(np.uint8)
    ff = sil.copy(); pad = np.zeros((hh+2, ww+2), np.uint8)
    for seed in ((0, 0), (ww-1, 0)):
        if ff[seed[1], seed[0]] == 0: cv2.floodFill(ff, pad, seed, 2)
    sil = (ff != 2).astype(np.uint8)
    dil = cv2.dilate(sil, np.ones((15, 15), np.uint8))
    inp = cv2.inpaint(sm, dil*255, 12, cv2.INPAINT_TELEA)
    inp = cv2.resize(inp, (w, h), interpolation=cv2.INTER_CUBIC).astype(np.float32)/255
    inp = cv2.GaussianBlur(inp, (0, 0), 3)
    msk = cv2.GaussianBlur(cv2.resize(sil.astype(np.float32), (w, h), interpolation=cv2.INTER_LINEAR), (0, 0), 1.5)
    dm = cv2.resize(dil.astype(np.float32), (w, h))[..., None]
    ground = im*(1-dm)+inp*dm
    _cache[k] = (im, ground, msk); return _cache[k]

def port_view(key, Wc, Hc, zoom, cx, cy, par):
    """ground at `zoom`, person at zoom*par (par>1 -> person comes forward)"""
    im, ground, msk = port_split(key)
    B = _cam0(ground, Wc, Hc, zoom=zoom, cx=cx, cy=cy)
    Fg = _cam0(im, Wc, Hc, zoom=zoom*par, cx=cx, cy=cy)
    M = _cam0(np.repeat(msk[..., None], 3, 2), Wc, Hc, zoom=zoom*par, cx=cx, cy=cy)[..., :1]
    return B*(1-M)+Fg*M

# ================================================================================================
# SF04: family-painted Crick; person/ground parallax; foreground bokeh; softer light sweep
# ================================================================================================
_s = R10.src_of('sf_r10.py', "@scene('SF04_crick_quote', 5.0)")
_s = R10.sub(_s, "P0 = img('sf04g_crick')", "P0 = None")
_s = R10.sub(_s, "Pc = cam(P0, pw, ph, zoom=1.02+0.08*u, cx=0.5+0.015*u, cy=0.47)",
             "Pc = port_view('sf04h_crick', pw, ph, 1.02+0.06*u, 0.5+0.012*u, 0.46, 1.0+0.045*ease(u))")
_s = R10.sub(_s, "np.array([1.0, 0.8, 0.45])*0.6", "np.array([1.0, 0.8, 0.45])*0.30")
_s = R10.sub(_s, "NC = (1112*s, 142*s); NR = int(100*s)", "NC = (1085*s, 172*s); NR = int(92*s)")
_s = R10.sub(_s, "bx0, bx1, by = NC[0]-NR, NC[0]+NR, NC[1]+NR+30*s", "bx0, bx1, by = NC[0]-NR-330*s, NC[0]-NR-30*s, NC[1]-34*s")
_s = R10.sub(_s, "    rgb = over(rgb, drift_specks(W, H, t, 45, 9, (240, 220, 180), 0.3, 1.6, (-10, -5)), shadow=0)\n",
             "    rgb = over(rgb, drift_specks(W, H, t, 45, 9, (240, 220, 180), 0.3, 1.6, (-10, -5)), shadow=0)\n"
             "    rgb = over(rgb, fg_bokeh(W, H, t, ((-40, 700, 140), (560, 760, 90))), shadow=0)\n")
_s = R10.sub(_s, "    rgb = over(rgb, L2.get(), shadow=0.4)\n    return grade(rgb, seed=int(t*24))",
             "    rgb = over(rgb, L2.get(), shadow=0.4)\n    rgb = _cam0(np.clip(rgb, 0, 1), W, H, zoom=math.exp(0.020*t), cx=0.5, cy=0.5)\n    return grade(rgb, seed=int(t*24))")
exec(compile(_s, 'sf_r12_sf04', 'exec'), globals())

# ================================================================================================
# SF05: painted portraits with parallax; picture icons; light streams from the ChR2 badge to each icon
# ================================================================================================
_ICON_SRC = {'neuron': ('sf06t_neuron', 1.7, 0.73, 0.53), 'alga': ('sf03e_microbes', 2.3, 0.695, 0.47),
             'current': ('sf09e_chr2', 2.6, 0.49, 0.47)}
def _icon12(L, kind, c, s, a, lit, t, R):
    if a <= 0: return
    x, y = c; key, z, cx, cy = _ICON_SRC[kind]; r = int(R)
    if kind == 'neuron':      # the gold neuron of SF02: dim until it lights
        gim, gd2, gp = _gold_neuron(); src = gim if lit > 0.5 else gd2; ci = circ_img(src, r, zoom=2.4, cx=gp[0], cy=gp[1])
    else: ci = circ_img(img(key), r, zoom=z, cx=cx, cy=cy)
    if lit < 1:
        arr = np.asarray(ci).astype(np.float32); arr[..., :3] *= 0.55+0.45*lit; ci = Image.fromarray(arr.astype(np.uint8), 'RGBA')
    L.dot((x, y), R+4*s, fill=(10, 12, 30), alpha=0.95*a)
    L.paste(ci, (x-r, y-r), alpha=a)
    L.ring((x, y), R, fill=(255, 222, 150) if lit > 0.5 else (150, 160, 200), width=2.0*s, alpha=a)
    if kind == 'current' and lit > 0:
        for j, pxn in enumerate((0.4375, 0.558)):
            X = x+(2*r/1024)*z*(pxn*1536-cx*1536)
            for n in range(2):
                p = (t*0.9+n/2+j*0.5) % 1.0; L.dot((X, y-r*0.55+p*r*1.1), 1.8*s, fill=(255, 209, 102), alpha=lit*min(1, p*5)*min(1, (1-p)*5))

@scene('SF05_nobel_portraits', 5.0)
def sf05(t, W, H):
    s = W/1280; u = lin(t, 5)
    zP = math.exp(0.039*t); zB = math.exp(0.024*t); zF = math.exp(0.065*t)
    PC = (W*0.5, 400*s)
    bg = np.zeros((H, W, 3), np.float32)+np.array([0.07, 0.055, 0.16])
    bg = bg*0.6+fam_bg(W, H)*0.30+radial(W, H, W*(0.3+0.4*u), H*0.12, W*0.42, (80, 90, 160), 0.12)
    bg = _cam0(bg, W, H, zoom=zB, cx=0.5, cy=PC[1]/H)
    people = [('sf05h_deisseroth', 'Karl Deisseroth', 'neuron', '装进神经元'),
              ('sf05h_hegemann', 'Peter Hegemann', 'alga', '衣藻的感光电流'),
              ('sf05h_nagel', 'Georg Nagel', 'current', '证明它是光控通道')]
    cw = int(320*s); gap = int(44*s); x0 = (W-3*cw-2*gap)//2; y0 = int(172*s)
    plate = np.zeros((H, W, 3), np.float32); pm = np.zeros((H, W, 1), np.float32)
    L = Layer(W, H); icons = []
    for i, (key, nm, kind, cap) in enumerate(people):
        a = ramp(t, 0.2+i*0.3, 0.9+i*0.3); dy = int(18*s*(1-ease_out(a)))
        Pc = port_view(key, cw, cw, 1.06+0.04*u, 0.5+(i-1)*0.010*u, 0.43-0.012*u, 1.0+0.05*ease(u))
        tl = 1.6+i*0.75; sw = ramp(t, tl-0.3, tl+1.0)
        if 0 < sw < 1:
            yy, xx = np.mgrid[0:cw, 0:cw]; band = np.exp(-(((xx+yy*0.5)/cw-(-0.2+1.7*sw))/0.09)**2)
            lum = Pc.mean(2, keepdims=True); Pc = np.clip(Pc+band[..., None]*np.clip(lum-0.25, 0, 1)*np.array([1.0, 0.82, 0.45])*0.35, 0, 1)
        x = x0+i*(cw+gap); y = y0+dy
        yy, xx = np.mgrid[0:cw, 0:cw]; e = np.minimum.reduce([xx/cw*2.2, (1-xx/cw)*2.2, yy/cw*3, (1-yy/cw)*1.6]); m = (np.clip(e/0.5, 0, 1)**1.6)[..., None]*a
        plate[y:y+cw, x:x+cw] = Pc*m; pm[y:y+cw, x:x+cw] = m
        ly = y0+cw+16*s
        L.line([(x+18*s, ly), (x+18*s+(cw-36*s)*ease_out(a), ly)], fill=GOLD, width=1.4*s, alpha=a)
        L.text((x+cw/2, ly+40*s), nm, F(SERIF_B, 28*s), fill=CREAM, alpha=a, anchor='ms')
        lit = ramp(t, tl-0.05, tl+0.25); ia = ramp(t, tl-0.9, tl-0.5)
        IR = 31*s; ic = (x+cw/2-F(SANS_B, 20*s).getlength(cap)/2-26*s, ly+78*s)
        _icon12(L, kind, ic, s, ia, lit, t, IR)
        L.text((x+cw/2+22*s, ly+85*s), cap, F(SANS_B, 20*s), fill=(255, 226, 170) if lit > 0.5 else BRIGHT, alpha=ia, anchor='ms')
        icons.append((ic, tl, lit))
    Lr = L.get()
    M = lambda z: np.array([[z, 0, PC[0]*(1-z)], [0, z, PC[1]*(1-z)]], np.float32)
    pl = cv2.warpAffine(plate, M(zP), (W, H), flags=cv2.INTER_CUBIC); pmw = cv2.warpAffine(pm, M(zP), (W, H))[..., None]
    rgb = bg*(1-pmw)+pl
    Lw = cv2.warpAffine(Lr, M(zP), (W, H), flags=cv2.INTER_LINEAR)
    rgb = over(rgb, Lw, shadow=0.45)
    fg = fg_bokeh(W, H, t, ((-20, 680, 120), (1300, 60, 110)))
    rgb = over(rgb, cv2.warpAffine(fg, M(zF), (W, H)), shadow=0)
    rgb = over(rgb, drift_specks(W, H, t, 40, 21, (240, 220, 170), 0.26, 1.5, (8, -4)), shadow=0)
    # fixed plane: header, badge, footnote
    Lh = Layer(W, H)
    Lh.rrect((W/2-330*s, 36*s, W/2+330*s, 140*s), 10*s, fill=(10, 12, 30), alpha=0.55*ramp(t, 0, 0.5))
    Lh.text((W/2, 74*s), '2026 年 10 月 5 日  ·  诺贝尔生理学或医学奖', F(SANS_B, 28*s), fill=GOLD, alpha=ramp(t, 0, 0.5), anchor='ms', tracking=2*s)
    fr = F(SERIF, 22*s); reason = '获奖理由：发现光控离子通道，并由此建立光遗传学'; tw = fr.getlength(reason)
    rx0 = W/2-tw/2+26*s
    Lh.text((rx0, 120*s), reason, fr, fill=CREAM, alpha=ramp(t, 0.9, 1.5), anchor='ls')
    ux0 = rx0+fr.getlength('获奖理由：发现'); ux1 = ux0+fr.getlength('光控离子通道'); kk = ease_out(ramp(t, 1.5, 2.1))
    Lh.line([(ux0, 130*s), (ux0+(ux1-ux0)*kk, 130*s)], fill=CYAN, width=2*s, alpha=ramp(t, 1.5, 1.7))
    plate_text(Lh, (W/2, H-16*s), '据诺贝尔奖官方新闻稿  ·  头像为插画', F(SANS, 20*s), fill=CREAM, alpha=ramp(t, 3.6, 4.2), anchor='ms')
    rgb = over(rgb, Lh.get(), shadow=0.45)
    bx, by = rx0-46*s, 112*s; k = ease(ramp(t, 0.5, 1.3))
    cx_, cy_ = W/2+(bx-W/2)*k, 380*s+(by-380*s)*k; r = int((150-118*k)*s)
    Lb = Layer(W, H); ba = 1.0 if t > 0.05 else 0.0
    Lb.dot((cx_, cy_), r+4*s, fill=(8, 10, 24), alpha=0.95*ba)
    Lb.paste(circ_img(img('sf09e_chr2'), r, zoom=2.2, cx=0.49, cy=0.47), (cx_-r, cy_-r), alpha=ba)
    Lb.ring((cx_, cy_), r, fill=CYAN, width=2*s, alpha=ba)
    rgb = over(rgb, Lb.get(), shadow=0.3)
    opn = ramp(t, 1.6, 2.0)
    if opn > 0:
        Li = Layer(W, H)
        for j, pxn in enumerate((0.4375, 0.558)):
            X = cx_+(2*r/1024)*2.2*(pxn*1536-0.49*1536)
            for n in range(3):
                p = (t*0.9+n/3+j*0.5) % 1.0; Li.dot((X, cy_-r*0.6+p*r*1.2), 2.0*s, fill=(255, 209, 102), alpha=opn*min(1, p*5)*min(1, (1-p)*5))
        rgb = over(rgb, Li.get(), shadow=0, glow_amt=0.7)
        rgb = rgb+radial(W, H, cx_, cy_, r*1.5, CYAN, 0.18*opn*(0.7+0.3*math.sin(t*5)))
    # light streams: from the badge down to each laureate's icon, arriving as the icon lights
    Ls = Layer(W, H); glowpts = []
    for (ic, tl, lit) in icons:
        IX, IY = PC[0]+(ic[0]-PC[0])*zP, PC[1]+(ic[1]-PC[1])*zP
        c1 = ((cx_+IX)/2+(IX-cx_)*0.1, min(cy_, IY)+60*s)
        for n in range(9):
            p = (t-(tl-0.75)-n*0.045)/0.7
            if 0 < p < 1:
                q = ease(p); X = (1-q)**2*cx_+2*q*(1-q)*c1[0]+q*q*IX; Y = (1-q)**2*cy_+2*q*(1-q)*c1[1]+q*q*IY
                Ls.dot((X, Y), (3.4-0.25*n)*s, fill=(170, 230, 255), alpha=0.95*(1-n/10)*min(1, (1-p)*6+0.3))
        if lit > 0: glowpts.append((IX, IY, lit, tl))
    rgb = over(rgb, Ls.get(), shadow=0, glow_amt=1.2)
    for (IX, IY, lit, tl) in glowpts:
        fl = math.exp(-((t-tl-0.1)/0.18)**2)
        rgb = rgb+radial(W, H, IX, IY, 34*s, (255, 220, 150), (0.10+0.06*math.sin(t*4+tl*3))*lit+0.45*fl)
    return grade(rgb, seed=int(t*24))

# ================================================================================================
# SF03: alga as a sprite cut from the still (rigid drift + flagellar beat); eyespot at the equator;
#       archaea side keeps the Wan clip; label fades staggered so no two texts cross-fade
# ================================================================================================
def chl12():
    if 'chl12' in _cache: return _cache['chl12']
    im = img('sf03e_microbes'); h, w = im.shape[:2]; u8 = (im*255).astype(np.uint8)
    hsv = cv2.cvtColor(u8, cv2.COLOR_RGB2HSV).astype(int); Hh, Ss, Vv = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    m = ((Hh > 28) & (Hh < 95) & (Ss > 50) & (Vv > 70)).astype(np.uint8); m[:, :int(0.55*w)] = 0
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(m); sp = (lab == 1+int(np.argmax(st[1:, cv2.CC_STAT_AREA]))).astype(np.uint8)
    ff = sp.copy(); pad = np.zeros((h+2, w+2), np.uint8); cv2.floodFill(ff, pad, (w-1, h-1), 2); sp = (ff != 2).astype(np.uint8)
    body = cv2.morphologyEx(sp, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (31, 31)))
    nb, lb, sb, cb = cv2.connectedComponentsWithStats(body); kb = 1+int(np.argmax(sb[1:, cv2.CC_STAT_AREA])); body = (lb == kb).astype(np.uint8)
    bx, by, bw, bh = sb[kb][:4]; bc = (cb[kb][0], cb[kb][1])
    sp = cv2.dilate(sp, np.ones((3, 3), np.uint8))                     # include the dark outline
    fl = sp*(1-cv2.dilate(body, np.ones((5, 5), np.uint8)))
    # flagellum bases = flagellum pixels touching the body top
    touch = fl*cv2.dilate(body, np.ones((15, 15), np.uint8)); touch[int(by+bh*0.35):] = 0
    ys, xs = np.nonzero(touch); xm = xs.mean()
    bases = [(xs[xs < xm].mean(), ys[xs < xm].mean()), (xs[xs >= xm].mean(), ys[xs >= xm].mean())]
    # eyespot: paint out the one near the flagella, redraw at the equator on the right flank
    es = (((Hh < 24) | (Hh > 165)) & (Ss > 90) & (Vv > 100)).astype(np.uint8); es[:, :int(0.6*w)] = 0; es *= cv2.dilate(body, np.ones((9, 9), np.uint8))
    spr = cv2.inpaint(u8, cv2.dilate(es, np.ones((15, 15), np.uint8))*255, 9, cv2.INPAINT_TELEA)
    ey = int(by+bh*0.56); row = np.nonzero(body[ey])[0]; ex = row.max()-bw*0.17
    # ground: inpaint the whole alga away (half res) so it can move over it
    hs = cv2.resize(u8, (w//2, h//2), interpolation=cv2.INTER_AREA); md = cv2.resize(cv2.dilate(sp, np.ones((9, 9), np.uint8)), (w//2, h//2))
    gi = cv2.resize(cv2.inpaint(hs, md*255, 9, cv2.INPAINT_TELEA), (w, h), interpolation=cv2.INTER_CUBIC)
    gi = cv2.GaussianBlur(gi, (0, 0), 2.0); dd = cv2.GaussianBlur(cv2.dilate(sp, np.ones((13, 13), np.uint8)).astype(np.float32), (0, 0), 3)[..., None]
    ground = (u8.astype(np.float32)/255)*(1-dd)+(gi.astype(np.float32)/255)*dd
    alpha = cv2.GaussianBlur(sp.astype(np.float32), (0, 0), 1.0)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    _cache['chl12'] = dict(spr=spr.astype(np.float32)/255, a=alpha, ground=ground, bases=bases, bc=bc, box=(bx, by, bw, bh),
                           eye=(ex, ey), grid=(xx, yy), w=w, h=h)
    return _cache['chl12']

def chl_frame(t):
    """alga sprite at time t over the ground; returns (base image, eyespot xy in image px)"""
    C = chl12(); xx, yy = C['grid']; w, h = C['w'], C['h']; bx, by, bw, bh = C['box']
    # 1) flagellar beat (breast stroke): rotation about each base, lagging along the flagellum
    sx, sy = xx.copy(), yy.copy(); om = 2*math.pi*1.1; D = 0.55*h
    for j, (Bx, By) in enumerate(C['bases']):
        side = (xx < (C['bases'][0][0]+C['bases'][1][0])/2) if j == 0 else (xx >= (C['bases'][0][0]+C['bases'][1][0])/2)
        dx, dy = xx-Bx, yy-By; d = np.sqrt(dx*dx+dy*dy)+1e-3
        above = np.clip((By+8-yy)/24.0, 0, 1)
        th = 0.20*np.clip(d/D, 0, 1.2)*np.sin(om*t-2.2*d/D)*above*side*(1 if j == 0 else -1)
        c, s_ = np.cos(-th), np.sin(-th)
        sx = np.where(side, Bx+c*dx-s_*dy, sx); sy = np.where(side, By+s_*dx+c*dy, sy)
    sx = sx.astype(np.float32); sy = sy.astype(np.float32)
    spr = cv2.remap(C['spr'], sx, sy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    al = cv2.remap(C['a'], sx, sy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    # 2) rigid swim: slow drift up-left with a bob and a slight rock, about the body centre
    u = lin(t, 5); cxp, cyp = C['bc']
    tx = -0.020*w*ease(u)+3.0*math.sin(t*2.2); ty = -0.012*h*ease(u)+4.0*math.sin(om*t-0.6)
    ang = 2.2*math.sin(t*0.9)
    Mr = cv2.getRotationMatrix2D((float(cxp), float(cyp)), ang, 1.0); Mr[0, 2] += tx; Mr[1, 2] += ty
    spr = cv2.warpAffine(spr, Mr, (w, h), flags=cv2.INTER_LINEAR); al = cv2.warpAffine(al, Mr, (w, h), flags=cv2.INTER_LINEAR)
    ex, ey = C['eye']; E = Mr@np.array([ex, ey, 1.0])
    out = C['ground']*(1-al[..., None])+spr*al[..., None]
    # eyespot: orange-red disc with a dark rim and a highlight
    Le = Layer(w, h, ss=1); er = bw*0.075
    Le.dot((E[0], E[1]), er+2.5, fill=(60, 14, 10)); Le.dot((E[0], E[1]), er, fill=(236, 84, 40)); Le.dot((E[0]-er*0.3, E[1]-er*0.35), er*0.35, fill=(255, 190, 120), alpha=0.9)
    out = over(out, Le.get(), shadow=0.25)
    return out, (E[0], E[1])

@scene('SF03_microbe_clues', 5.0)
def sf03(t, W, H):
    base0 = img('sf03e_microbes'); ih, iw = base0.shape[:2]
    vid = vat('sf03_swim', t, (iw, ih))
    stat, (exi, eyi) = chl_frame(t)
    if 'seam12' not in _cache:
        xx = np.arange(iw, dtype=np.float32)/iw; _cache['seam12'] = np.clip((xx-0.50)/0.06, 0, 1)[None, :, None]
    sm = _cache['seam12']; im = vid*(1-sm)+stat*sm
    u = lin(t, 5); s = W/1280; z = 1.02+0.07*u; cxx = 0.5+0.012*u; cyy = 0.5
    rgb = cam(im, W, H, zoom=z, cx=cxx, cy=cyy)
    P = lambda x, y: to_px(base0, x, y, W, H, z, cxx, cyy)
    ex, ey = P(exi/iw, eyi/ih)
    flash = ramp(t, 2.6, 3.0)*(0.7+0.3*math.sin(t*6))
    rgb = rgb+radial(W, H, ex, ey, W*0.012, (255, 120, 60), 0.45*flash)+radial(W, H, ex, ey, W*0.05, CYAN, 0.12*flash)
    rgb = over(rgb, drift_specks(W, H, t, 60, 7, (190, 230, 255), 0.3, 1.4, (12, -6)), shadow=0)
    L = Layer(W, H)
    CL = (560*s, 160*s); RL = int(112*s); zl = 1.05+0.08*u
    ax, ay = P(0.352, 0.375)
    R5.inset(L, None, t, ramp(t, 0.6, 1.3), R8._ins_l3(), CL, RL, (ax, ay), GOLD, None, u)
    CR = (1110*s, 440*s); RR = int(108*s)
    R5.inset(L, None, t, ramp(t, 2.6, 3.3), img('sf03_ins_r2'), CR, RR, (ex, ey), CYAN, None, u)
    rgb = over(rgb, L.get(), shadow=0.35)
    aL = ramp(t, 0.6, 1.3)
    if aL >= 1:      # pump rhythm: one H+ at a time, carried up through the pump and released outside
        Lp = Layer(W, H); IP = lambda x, y: (CL[0]+(x-0.5)*2*RL*zl, CL[1]+(y-0.5)*2*RL*zl)
        rng = np.random.default_rng(4); T0 = 1.4; per = 0.55
        nmax = int((t-T0)/per)+1 if t > T0 else 0
        for n in range(max(0, nmax-7), nmax):
            age = t-(T0+n*per)
            if age < 0: continue
            if age < 0.35: q = ease(age/0.35); x, y = 0.505, 0.66-0.42*q
            else:
                d = age-0.35; ang = rng.uniform(-2.4, -0.7); x = 0.505+math.cos(ang)*0.10*d; y = 0.24+math.sin(ang)*0.07*d
            X, Y = IP(x, y)
            if math.hypot(X-CL[0], Y-CL[1]) < RL*0.92:
                Lp.dot((X, Y), 7.0*s, fill=(110, 230, 150), alpha=min(1, age*8)*(1-ramp(age, 2.6, 3.2)))
        X, Y = IP(0.505, 0.70); ph = ((t-T0) % per)/per
        Lp.dot((X, Y+6*s*(1-ph)), 7.0*s, fill=(110, 230, 150), alpha=0.85)
        rgb = over(rgb, Lp.get(), shadow=0.2, glow_amt=0.5)
        rgb = rgb+radial(W, H, *IP(0.505, 0.45), 24*s, (180, 140, 255), 0.18*math.exp(-((((t-T0) % per))/0.12)**2))
    L2 = Layer(W, H)
    def card(x, y, title, a, col, right=False):
        if a <= 0: return
        tw = F(SANS_B, LT*s).getlength(title)+36*s; x0 = x-tw if right else x
        L2.rrect((x0, y, x0+tw, y+46*s), 6*s, fill=(12, 18, 38), alpha=0.8*a); L2.line([(x0, y), (x0, y+46*s)], fill=col, width=3*s, alpha=a)
        L2.text((x0+18*s, y+31*s), title, F(SANS_B, LT*s), fill=CREAM, alpha=a, anchor='ls')
    # one text change at a time, each fade 0.25 s
    card(40*s, 636*s, '嗜盐古菌（1970s）：光驱动的泵', ramp(t, 1.0, 1.25), GOLD)
    plate_text(L2, (CL[0], CL[1]+RL+30*s), 'H⁺ 被一个一个泵到膜外', F(SANS_B, 20*s), fill=(150, 240, 175), alpha=ramp(t, 1.6, 1.85)*(1-ramp(t, 2.45, 2.7)))
    card(1240*s, 636*s, '衣藻（1991–96）：眼点受光，微秒级出电流', ramp(t, 3.0, 3.25), CYAN, right=True)
    plate_text(L2, (CR[0], CR[1]-RR-16*s), '眼点膜上的感光蛋白', F(SANS_B, 20*s), fill=CREAM, alpha=ramp(t, 3.45, 3.7))
    return grade(over(rgb, L2.get()), seed=int(t*24))

# ================================================================================================
# SF07: new dorsal mouse brain plate (sf07h_brain), pushed from frame 0; neuron network pulses out from the fibre tip;
#       magnifier fibre-tip -> neurons -> ChR2 (as round 9/10); title below the brain
# ================================================================================================
BT = (0.426, 0.255)
def _brain12():
    if 'br12' in _cache: return _cache['br12']
    im = img('sf07h_brain'); h, w = im.shape[:2]; u8 = (im*255).astype(np.uint8)
    hsv = cv2.cvtColor(u8, cv2.COLOR_RGB2HSV).astype(int)
    cm = ((hsv[..., 0] > 78) & (hsv[..., 0] < 108) & (hsv[..., 1] > 50) & (hsv[..., 2] > 140)).astype(np.float32)
    cm[:int(BT[1]*h-0.02*h)] = 0
    cmb = cv2.GaussianBlur(cv2.dilate(cm, np.ones((5, 5), np.uint8)), (0, 0), 2.5)[..., None]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32); d = np.hypot(xx/w-BT[0], (yy/h-BT[1])*h/w)
    lum = im.mean(2, keepdims=True); dim = im*(1-cmb)+(lum*np.array([0.80, 0.62, 0.95]))*cmb     # unlit network = lilac
    fe = np.ones((h, w), np.float32); fw = int(0.07*w)
    for i in range(fw):
        v = (i/fw)**1.5; fe[i, :] = np.minimum(fe[i, :], v); fe[-1-i, :] = np.minimum(fe[-1-i, :], v); fe[:, i] = np.minimum(fe[:, i], v); fe[:, -1-i] = np.minimum(fe[:, -1-i], v)
    ys, xs = np.nonzero(cm > 0.5); rng = np.random.default_rng(3); idx = rng.choice(len(xs), min(110, len(xs)), replace=False)
    pts = [(xs[i]/w, ys[i]/h, rng.random()) for i in idx]
    _cache['br12'] = (im, dim, cmb, d, fe, pts); return _cache['br12']

@scene('SF07_main_title', 5.0)
def sf07(t, W, H):
    s = W/1280; im, dim, cmb, d, fe, pts = _brain12(); h, w = im.shape[:2]
    WAVES = (0.10, 1.25, 2.40, 3.55, 4.70)
    wv = sum(np.exp(-((t-(w0+d*7.0))/0.20)**2) for w0 in WAVES); lit = np.clip(0.15+wv, 0, 1)[..., None]
    base = dim*(1-cmb*lit)+(im*1.15+np.array([0.10, 0.25, 0.35])*wv[..., None])*cmb*lit
    # placement: brain centre at (520, 292), 0.645 W wide; push about the brain centre
    z = math.exp(0.047*t); Q = (520*s, 292*s); sc = W*0.645/w*z
    ox = Q[0]-0.5*w*sc; oy = Q[1]-0.5*h*sc
    M = np.array([[sc, 0, ox], [0, sc, oy]], np.float32)
    pic = cv2.warpAffine(np.clip(base, 0, 1).astype(np.float32), M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
    mk = cv2.warpAffine(fe, M, (W, H), flags=cv2.INTER_LINEAR)[..., None]
    if ('bg12', W) not in _cache:
        _cache[('bg12', W)] = np.array([0.07, 0.055, 0.16])*0.6+fam_bg(W, H)*0.34+radial(W, H, 520*s, 300*s, 420*s, (70, 80, 170), 0.10)
    bgc = _cam0(_cache[('bg12', W)], W, H, zoom=math.exp(0.025*t))
    rgb = bgc*(1-mk)+pic*mk
    yy = np.mgrid[0:H, 0:W][0]; lm = np.clip((yy/H-0.66)/0.22, 0, 1)[..., None]; rgb = rgb*(1-0.55*lm)+np.array(INK)/255*0.55*lm
    fx, fbot = ox+BT[0]*w*sc, oy+BT[1]*h*sc
    L = Layer(W, H)
    for (px, py, ph) in pts:
        dd = math.hypot(px-BT[0], (py-BT[1])*h/w); a = 0.2
        for w0 in WAVES: a += math.exp(-((t-(w0+dd*7.0+ph*0.12))/0.15)**2)
        L.dot((ox+px*w*sc, oy+py*h*sc), 2.0*s, fill=(180, 235, 255), alpha=min(1, a))
    # fibre continued to the frame top + photons running down it
    L.line([(fx, -10), (fx, oy+0.09*h*sc)], fill=(20, 18, 40), width=7*s); L.line([(fx, -10), (fx, oy+0.09*h*sc)], fill=(120, 124, 150), width=4*s)
    for n in range(5):
        p = (t*0.9+n/5) % 1.0; L.dot((fx, fbot*p), 2.6*s, fill=(210, 240, 255), alpha=min(1, (1-p)*6))
    rgb = over(rgb, L.get(), shadow=0, glow_amt=1.3)
    rgb = rgb+radial(W, H, fx, fbot, 50*s, CYAN, 0.32*(0.85+0.15*math.sin(t*4)))
    rgb = over(rgb, drift_specks(W, H, t, 60, 11, (180, 205, 255), 0.3, 1.6, (10, -5)), shadow=0)
    # magnifier: fibre tip -> neurons -> ChR2 on their membrane
    C = (1088*s, 262*s); R = int(138*s); a = ramp(t, 0.5, 1.3)
    L = Layer(W, H); hx, hy = fx, fbot+8*s
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
    if op > 0:
        Li = Layer(W, H); sc2 = (2*R/1024)*zc
        for j, pxn in enumerate((0.4375, 0.558)):
            X = C[0]+sc2*(pxn*1536-0.49*1536); yt = C[1]+sc2*(0.34-0.46)*1024; yb = C[1]+sc2*(0.64-0.46)*1024
            Li.line([(X, yt), (X, yb)], fill=(160, 225, 255), width=3*s, alpha=0.5*op)
            for n in range(6):
                p = (t*0.75+n/6+j*0.5) % 1.0; Y = yt-20*s+(yb-yt+40*s)*p
                if math.hypot(X-C[0], Y-C[1]) < R-6*s:
                    Li.dot((X+1.5*s*math.sin(n*2+t*5), Y), 4*s, fill=(255, 209, 102), alpha=op*min(1, p*6)*min(1, (1-p)*6))
        rgb = over(rgb, Li.get(), shadow=0, glow_amt=0.7)
        rgb = rgb+radial(W, H, C[0], C[1]-R*0.75, 70*s, CYAN, 0.22*op*(0.8+0.2*math.sin(t*6)))
    L = Layer(W, H)
    a = ramp(t, 1.0, 1.8); tr = (60*(1-ease_out(ramp(t, 1.0, 2.6)))+34)*s
    L.text((W/2, 604*s), '光遗传学', F(SERIF_B, 96*s), fill=CREAM, alpha=a, anchor='ms', tracking=tr)
    L.text((W/2, 648*s), 'O P T O G E N E T I C S', F(SANS_B, 20*s), fill=(185, 225, 255), alpha=ramp(t, 1.6, 2.2), anchor='ms', tracking=4*s)
    L.text((C[0], C[1]+R+36*s), '这一期，就讲这枚开关', F(SANS_B, 24*s), fill=CREAM, alpha=ramp(t, 2.6, 3.2), anchor='ms', tracking=2*s)
    L.text((C[0], C[1]+R+66*s), '神经元膜上的光控通道', F(SANS, 20*s), fill=(226, 232, 248), alpha=ramp(t, 2.9, 3.5), anchor='ms')
    plate_text(L, (150*s, 132*s), '小鼠脑 · 背面观', F(SANS_B, 20*s), fill=(226, 232, 248), alpha=ramp(t, 0.3, 0.8), anchor='ms')
    return grade(over(rgb, L.get(), glow_amt=0.3, shadow=0.55), seed=int(t*24))

# ================================================================================================
# SF10: new mouse plates -> Wan wake (first/last frame) + Wan walk; eyes-shut frames cut and flow-bridged
#   output map: 0-2.6 asleep (wake f0-24, slowed) | 2.6-3.4 fast-forward (f24-60) | 3.4-3.93 rise (f60-76)
#               3.93-4.07 bridge f76->f84 | 4.07-6.23 rise 1:1 (f84-149) | 6.23-6.43 bridge -> walk f0 | 6.43- walk 1:1
# ================================================================================================
SZ10 = (1176, 784)
def _clip12(name):
    k = ('clip12', name)
    if k not in _cache:
        c = cv2.VideoCapture('/workspace/e2work/v8/gen/vid/'+name+'.mp4'); fr = []
        while True:
            ok, f = c.read()
            if not ok: break
            fr.append(cv2.resize(cv2.cvtColor(f, cv2.COLOR_BGR2RGB), SZ10, interpolation=cv2.INTER_CUBIC).astype(np.float32)/255)
        _cache[k] = fr
    return _cache[k]
def _fat(name, f):
    fr = _clip12(name); f = min(max(f, 0), len(fr)-1.0001); i = int(f); a = f-i
    return fr[i] if a < 0.02 else fr[i]*(1-a)+fr[min(i+1, len(fr)-1)]*a
_dis12 = [None]
def _bridge(A, B, al, key):
    if key not in _cache:
        if _dis12[0] is None: _dis12[0] = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)
        g = lambda x: cv2.cvtColor((x*255).astype(np.uint8), cv2.COLOR_RGB2GRAY)
        _cache[key] = (_dis12[0].calc(g(A), g(B), None), _dis12[0].calc(g(B), g(A), None))
    fab, fba = _cache[key]; h, w = A.shape[:2]
    if 'grid12' not in _cache:
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32); _cache['grid12'] = (xx, yy)
    xx, yy = _cache['grid12']
    Aw = cv2.remap(A, xx-al*fab[..., 0], yy-al*fab[..., 1], cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    Bw = cv2.remap(B, xx-(1-al)*fba[..., 0], yy-(1-al)*fba[..., 1], cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    wb = ease((al-0.35)/0.3) if 0.35 < al < 0.65 else float(al >= 0.65)
    return Aw*(1-wb)+Bw*wb
WK, WL = 'sf10_wake11', 'sf10_walk11'
def src10(t):
    if t < 2.6: return _fat(WK, t*24/2.6)
    if t < 3.4: return _fat(WK, 24+(t-2.6)/0.8*36)
    if t < 3.933: return _fat(WK, 60+(t-3.4)/0.533*16)
    if t < 4.233: return _bridge(_clip12(WK)[76], _clip12(WK)[84], (t-3.933)/0.30, 'br76')
    if t < 6.233: return _fat(WK, 84+(t-4.233)*32.5)
    if t < 6.433: return _bridge(_clip12(WK)[149], _clip12(WL)[0], ease((t-6.233)/0.2), 'brWL')
    return _fat(WL, (t-6.433)*30)

def _track12():
    """implant position per output frame (24 fps), template-matched along the composed sequence"""
    if 'trk12' in _cache: return _cache['trk12']
    n = int(round(R10.SF10_D*24))+2; x, y = 605.0, 290.0; r = 26; pos = []; tpl = None
    for k in range(n):
        g = cv2.cvtColor((np.clip(src10(k/24), 0, 1)*255).astype(np.uint8), cv2.COLOR_RGB2GRAY)
        if tpl is None: tpl = g[int(y)-r:int(y)+r, int(x)-r:int(x)+r]
        sw = 70; x0, y0 = max(0, int(x)-sw), max(0, int(y)-sw); win = g[y0:int(y)+sw, x0:int(x)+sw]
        res = cv2.matchTemplate(win, tpl, cv2.TM_CCOEFF_NORMED); _, _, _, ml = cv2.minMaxLoc(res)
        x, y = x0+ml[0]+r, y0+ml[1]+r; pos.append((x/SZ10[0], y/SZ10[1]))
        if k % 3 == 0: tpl = g[int(y)-r:int(y)+r, int(x)-r:int(x)+r]
    pos = np.array(pos); pos = np.stack([cv2.GaussianBlur(pos[:, i].reshape(-1, 1), (1, 0), 1.5).ravel() for i in (0, 1)], 1)
    _cache['trk12'] = (pos, 24.0, SZ10[0], SZ10[1]); return _cache['trk12']

def frame12(ct):
    f = np.clip(src10(ct), 0, 1).astype(np.float32)
    if ct > 3.85:       # the implant only glows during the pulse trains: take Wan's steady glow out
        pos = _track12()[0]; px, py = pos[min(int(ct*24), len(pos)-1)]; X, Y = int(px*SZ10[0]), int(py*SZ10[1]); r = 64
        y0, y1, x0, x1 = max(0, Y-r-20), min(SZ10[1], Y+r), max(0, X-r), min(SZ10[0], X+r)
        p = (f[y0:y1, x0:x1]*255).astype(np.uint8); hsv = cv2.cvtColor(p, cv2.COLOR_RGB2HSV).astype(np.float32)
        m = ((hsv[..., 0] > 85) & (hsv[..., 0] < 130) & (hsv[..., 1] > 70) & (hsv[..., 2] > 110)).astype(np.float32)
        m = cv2.GaussianBlur(m, (0, 0), 2.0)*ramp(ct, 3.85, 4.1)
        hsv[..., 1] *= 1-0.85*m; hsv[..., 2] *= 1-0.30*m
        f[y0:y1, x0:x1] = cv2.cvtColor(np.clip(hsv, 0, 255).astype(np.uint8), cv2.COLOR_HSV2RGB).astype(np.float32)/255
    return f
R10.c10 = lambda t: [(t, 1.0)]
R10.frame10 = frame12
R10._trk10 = _track12
R11.rerun10('sf10', [
    ("circ_img(img('sf10_orexin'), r, zoom=1.15+0.05*lin(t, 3), cx=0.5, cy=0.47)", "circ_img(_orx11(), r, zoom=1.55+0.10*lin(t, 3), cx=0.73, cy=0.53)"),
    ("radial(W, H, C[0], C[1]-6*s, 70*s, CYAN, 0.5*pl*a)", "radial(W, H, C[0]+4*s, C[1]+4*s, 46*s, CYAN, 0.55*pl*a)"),
    ("L = Layer(W, H); C = (1100*s, 250*s); R = int(138*s)", "L = Layer(W, H); C = (205*s, 352*s); R = int(116*s)"),
    ("z = 1.04+0.05*lin(t, SF10_D); cxx = 0.55-0.05*lin(t, SF10_D); cyy = 0.50", "z = 1.02*math.exp(0.031*t); cxx = 0.54-0.03*ease(lin(t, SF10_D)); cyy = 0.50"),
    ("cx_, cy_ = W*0.36, 112*s+120*s", "cx_, cy_ = W*0.74, 150*s"),
    ("L2.text((C[0], C[1]+R+34*s), '下丘脑外侧 · 食欲素神经元'", "plate_text(L2, (C[0], C[1]+R+34*s), '下丘脑外侧 · 食欲素神经元'"),
    ("L2.text((C[0], C[1]+R+62*s), '膜上装了光控通道，随光脉冲放电'", "plate_text(L2, (C[0]+6*s, C[1]+R+66*s), '膜上装了光控通道，随光脉冲放电'"),
])

# ================================================================================================
# SF01 polish: left third less crushed (title still on a calm field), footer brighter / larger (>=7:1)
# SF06 polish: lighter bloom on the neuron, title without the boxed card
# ================================================================================================
import sf_r7 as R7
_s1 = open(TOOLS+'sf_r5.py').read(); _a = _s1.index("@scene('SF01_open_title'"); _b = _s1.index("# ----", _a); _s1 = _s1[_a:_b]
for o, n in (("fm = (np.clip(1-xx/(W*0.45), 0, 1)**1.5*0.45)[..., None]", "fm = (np.clip(1-xx/(W*0.45), 0, 1)**1.5*0.22)[..., None]"),
             ("L.text((98*s, 640*s), 'EigenLens 主观知识  ·  第 2 期', F(SANS, 16*s), fill=(176, 186, 212), alpha=ramp(t, 3.0, 3.8)*0.9",
              "L.text((98*s, 640*s), 'EigenLens 主观知识  ·  第 2 期', F(SANS, 19*s), fill=(226, 230, 244), alpha=ramp(t, 3.0, 3.8)")):
    assert o in _s1, o; _s1 = _s1.replace(o, n)
exec(compile(_s1, 'sf_r12_sf01_r5', 'exec'), R5.__dict__)
R7._sf01 = S['SF01_open_title'][0]
_dk0 = R7._darkL
R7._darkL = lambda a, edge=0.56, amt=0.62: _dk0(a, edge, amt)
R10._sf01_prev = R7.sf01
S['SF01_open_title'] = (R10.sf01, 5.0)
def _lift01(fn):
    def g(t, W, H):
        rgb = fn(t, W, H); s = W/1280
        return np.clip(rgb+radial(W, H, 260*s, 250*s, 330*s, (70, 90, 190), 0.10)+radial(W, H, 180*s, 560*s, 260*s, (120, 70, 170), 0.07), 0, 1)
    return g
S['SF01_open_title'] = (_lift01(R10.sf01), 5.0)
R11.rerun10('sf06', [("rgb = glow(rgb, 0.7, W/70, 0.3*on)", "rgb = glow(rgb, 0.80, W/100, 0.14*on)"),
                     ("np.array([0.25, 0.65, 1.0])*0.32*", "np.array([0.25, 0.65, 1.0])*0.22*"),
                     ("    L2.rrect((40*s, 40*s, 80*s+tw0, 102*s), 8*s, fill=(10, 13, 30), alpha=0.82*ta)\n    L2.line([(40*s, 40*s), (40*s, 102*s)], fill=CYAN, width=3*s, alpha=ta)\n", "")])

# ------------------------------------------------------------------------------------------------
# wrap every scene again (round-9/10 wrapper + round-10 push multiplier)
# ------------------------------------------------------------------------------------------------
for _n in list(S):
    _fn, _d = S[_n]
    if getattr(_fn, '_r11', False): continue
    if not getattr(_fn, '_r10', False): _fn = R10._wrap10(_n, _fn)
    S[_n] = (R11._wrap11(_n, _fn), _d)
S['SF10_mouse_tripo'] = (S['SF10_mouse_tripo'][0], R10.SF10_D)
