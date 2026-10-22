"""Round 12 (PROMPT 第 12 轮, 2026-10-23): the round-11 independent-review Top gaps.  Narration NOT changed.
1 SF04: Crick repainted as an ink-outlined, cel-shaded illustration (image2 sf04k_crick); right side cut to three
  lines (quote / admission / source); the "设想" idea lives inside the neuron inset (light enters, cell fires);
  secondary motion: breathing, two light sweeps, drifting molecule ground, foreground bokeh.
2 SF05: the three heads repainted the same way (sf05k_*); bottom dark strip removed; footnote on a solid plate (>=7:1).
3 SF08: wider framing so the relay chain stays in frame to the last frame; '路线一' / '路线二' labels; timeline gets
  the route-two row (先给药，分钟级) -> both routes visibly miss the millisecond mark; dark smudge painted out.
4 SF10: rise rebuilt from a new Wan 3.0 first/last clip (lying eyes-open -> half-up keyframe, no dissolve, one tail)
  and a Wan 2.6 walk that starts from its last frame; fibre cable drawn over the tracked implant (always visible);
  push >= 3 %/s.
5 SF11: one label at a time on the eye (cornea label dropped, photoreceptor label hands over); goggles caption one line.
  SF01: relief shading + ink edges on the neuron plate (bead volume)."""
import sys, os, math; sys.path.insert(0, '/workspace/e2work/v8/tools')
import sf, sf_scenes
import sf_r12 as R12
from sf_r12 import *          # noqa
from sf_r12 import _cam0, _cache, _gold_neuron
import sf_r11 as R11, sf_r10 as R10, sf_r9 as R9, sf_r8 as R8, sf_r7 as R7, sf_r5 as R5
from sf_r5 import circ_img
TOOLS = '/workspace/e2work/v8/tools/'; GEN = '/workspace/e2work/v8/gen/'

# ================================================================================================
# SF04: ink-outlined Crick; three text lines; idea inside the inset; more secondary motion
# ================================================================================================
@scene('SF04_crick_quote', 5.0)
def sf04(t, W, H):
    s = W/1280; u = lin(t, 5)
    bg0 = np.zeros((H, W, 3), np.float32)+np.array([0.075, 0.06, 0.17])
    fb = _cam0(fam_bg(W, H), W, H, zoom=1.08*math.exp(0.035*t), cx=0.5+0.03*math.sin(t*0.5), cy=0.5-0.02*u)
    rgb = bg0*0.55+fb*0.36+radial(W, H, W*(0.32-0.05*u), H*0.45, W*0.26, (60, 70, 150), 0.22)
    # slow light scan across the molecule ground (right half)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    scan = np.exp(-(((xx/W)-0.35-0.65*((t*0.22) % 1.0))/0.07)**2)[..., None]
    rgb = rgb+scan*np.clip(fb-0.08, 0, 1)*np.array([0.5, 0.75, 1.0])*0.55
    ph = int(H*0.96); pw = ph
    br = 0.006*math.sin(2*math.pi*t/3.1)                                   # breathing
    Pc = port_view('sf04k_crick', pw, ph, 1.04+0.05*u, 0.47+0.01*u, 0.44, 1.0+0.05*ease(u)+br)
    py_, px_ = np.mgrid[0:ph, 0:pw].astype(np.float32)
    lum = Pc.mean(2, keepdims=True)
    for (t0, t1, col, amt) in ((0.6, 2.4, (0.55, 0.8, 1.0), 0.30), (2.9, 4.8, (1.0, 0.82, 0.48), 0.28)):
        sw = ramp(t, t0, t1)
        if 0 < sw < 1:
            band = np.exp(-(((px_+py_*0.55)/pw-(-0.25+1.8*sw))/0.09)**2)[..., None]
            Pc = np.clip(Pc+band*np.clip(lum-0.2, 0, 1)*np.array(col)*amt, 0, 1)
    e = np.minimum.reduce([px_/pw*3, (1-px_/pw)*1.7, py_/ph*4, (1-py_/ph)*3]); m = (np.clip(e, 0, 1)**1.4*(0.6+0.4*ramp(t, 0, 0.5)))[..., None]
    x0 = int(26*s-10*s*ease_out(ramp(t, 0, 1.5))); y0 = H-ph
    rgb[y0:, x0:x0+pw] = rgb[y0:, x0:x0+pw]*(1-m)+Pc*m
    rgb = over(rgb, drift_specks(W, H, t, 70, 9, (240, 220, 180), 0.34, 1.9, (-14, -7)), shadow=0)
    rgb = over(rgb, fg_bokeh(W, H, t*1.6, ((-40, 700, 150), (560, 760, 95), (1290, 690, 110))), shadow=0)
    # three lines: quote / admission / source
    L = Layer(W, H); ty = -10*s*u; X0 = 662*s
    L.text((X0, 384*s+ty), '“理想的信号会是光”', F(SERIF_B, 50*s), fill=CREAM, alpha=ramp(t, 0.4, 1.3), anchor='ls')
    fa = F(SERIF, 30*s); fb2 = F(SERIF_B, 36*s); a2 = ramp(t, 2.0, 2.6); em = ramp(t, 2.4, 3.2)
    L.text((X0, 452*s+ty), '他也承认：', fa, fill=BRIGHT, alpha=a2, anchor='ls')
    L.text((X0+fa.getlength('他也承认：'), 452*s+ty), '这个想法相当牵强。', fb2, fill=GOLD, alpha=em, anchor='ls', tracking=(2.0*ease_out(ramp(t, 2.4, 3.8)))*s)
    L.line([(X0, 486*s+ty), (X0+470*s*ease_out(ramp(t, 3.0, 3.8)), 486*s+ty)], fill=(110, 120, 160), width=1*s)
    L.text((X0, 522*s+ty), 'F. Crick, Phil. Trans. B (1999)：“rather far-fetched”', F(SANS, 20*s), fill=(232, 236, 248), alpha=ramp(t, 3.2, 3.9), anchor='ls')
    rgb = over(rgb, L.get(), glow_amt=0.15)
    f = F(SERIF_B, 50*s); gx = X0+f.getlength('“理想的信号会是')+f.getlength('光')/2; gy = 366*s+ty
    gl = ramp(t, 1.2, 1.8)*(0.75+0.25*math.sin(t*3.2)); rgb = rgb+radial(W, H, gx, gy, 36*s, CYAN, 0.5*gl)
    rgb = rgb+radial(W, H, X0+300*s, 440*s+ty, 170*s, GOLD, 0.06*em*(0.6+0.4*math.sin(t*3)))
    # the idea, drawn: light enters the neuron inset, the cell fires, a spike train runs under it
    im, d2, gp = _gold_neuron(); NC = (1040*s, 182*s); NR = int(100*s); na = ramp(t, 0.9, 1.5)
    if na > 0:
        zN = 3.2+0.25*u; cxN, cyN = gp[0], gp[1]
        lit = circ_img(im, NR, zoom=zN, cx=cxN, cy=cyN); dim = circ_img(d2, NR, zoom=zN, cx=cxN, cy=cyN)
        sweep = ramp(t, 1.6, 2.6); fire = ramp(t, 2.55, 2.75)
        a_l = np.asarray(lit).astype(np.float32)/255; a_d = np.asarray(dim).astype(np.float32)/255
        xg = np.linspace(0, 1, NR*2)[None, :, None]
        front = np.clip((sweep*1.3-0.15-xg)/0.15, 0, 1); blue = np.exp(-((xg-(sweep*1.3-0.15))/0.06)**2)
        mix = a_d.copy(); mix[..., :3] = a_d[..., :3]*(1-front*fire)+a_l[..., :3]*front*fire
        mix[..., :3] = np.clip(mix[..., :3]+blue*np.array([0.25, 0.55, 1.0])*0.55*(sweep > 0)*(sweep < 1), 0, 1)
        mix[..., :3] = np.clip(mix[..., :3]*(1+0.35*fire*(0.6+0.4*math.sin(t*14)**2)), 0, 1)
        vim = Image.fromarray((mix*255).astype(np.uint8), 'RGBA')
        Lv = Layer(W, H)
        # incoming light: a soft cone from the upper left into the ring
        if 1.4 < t < 3.6:
            ba = ramp(t, 1.4, 1.8)*(1-ramp(t, 3.0, 3.6))*(0.75+0.25*math.sin(t*5))
            src = (NC[0]-NR*1.9, NC[1]-NR*1.55); e1 = (NC[0]-NR*0.95, NC[1]+NR*0.05); e2 = (NC[0]+NR*0.05, NC[1]-NR*0.95)
            Lv.d.polygon([(src[0]*2, src[1]*2), (e1[0]*2, e1[1]*2), (e2[0]*2, e2[1]*2)], fill=(90, 175, 255, int(85*ba)))
            for n in range(4):
                q = ((t-1.4)*1.1+n/4) % 1.0; Lv.dot((src[0]+(NC[0]-NR*0.5-src[0])*q, src[1]+(NC[1]-NR*0.5-src[1])*q), 3.2*s, fill=(200, 235, 255), alpha=ba*min(1, (1-q)*5))
        Lv.dot(NC, NR+6*s, fill=(8, 10, 24), alpha=0.92*na); Lv.paste(vim, (NC[0]-NR, NC[1]-NR), alpha=na)
        Lv.ring(NC, NR, fill=CYAN if sweep > 0 else (130, 150, 200), width=2.4*s, alpha=na)
        if fire > 0:
            rr = ramp(t, 2.75, 3.6); Lv.ring(NC, NR+(6+40*rr)*s, fill=(255, 200, 120), width=2.4*s, alpha=0.8*(1-rr)*fire)
        # spike trace just under the ring: flat until the cell fires, then spikes
        bx0, bx1, by = NC[0]-NR*0.95, NC[0]+NR*0.95, NC[1]+NR+26*s; pts = []
        for q in np.linspace(0, 1, 140):
            tt = 0.9+q*(t-0.9); v = 1 if (tt > 2.7 and ((tt-2.7)*6) % 1.0 < 0.12) else 0
            pts.append((bx0+(bx1-bx0)*q, by-v*18*s))
        Lv.line([(bx0, by), (bx1, by)], fill=(90, 100, 140), width=1*s, alpha=na)
        Lv.line(pts, fill=(255, 205, 130) if t > 2.7 else (150, 160, 200), width=1.8*s, alpha=na)
        # the "idea" tag sits on the ring itself
        ft = F(SANS_B, 20*s); tag = '设想'; tw = ft.getlength(tag); tx, tyy = NC[0]+NR*0.62, NC[1]-NR*0.86
        Lv.rrect((tx-tw/2-10*s, tyy-17*s, tx+tw/2+10*s, tyy+12*s), 12*s, fill=(14, 18, 40), alpha=0.95*na)
        Lv.text((tx, tyy+5*s), tag, ft, fill=(250, 244, 230), alpha=na, anchor='ms')
        rgb = over(rgb, Lv.get(), shadow=0.35, glow_amt=0.5)
        rgb = rgb+radial(W, H, NC[0], NC[1], 70*s, (255, 180, 90), 0.3*fire*(0.7+0.3*math.sin(t*9)))
    rgb = _cam0(np.clip(rgb, 0, 1), W, H, zoom=math.exp(0.022*t), cx=0.5, cy=0.5)
    return grade(rgb, seed=int(t*24))

# ================================================================================================
# SF05: ink-outlined heads; no bottom strip; footnote on a solid plate
# ================================================================================================
_s5 = open(TOOLS+'sf_r12.py').read(); _a = _s5.index("@scene('SF05_nobel_portraits'"); _b = _s5.index("# ====", _a); _s5 = _s5[_a:_b]
for o, n in (("('sf05h_deisseroth'", "('sf05k_deisseroth'"), ("('sf05h_hegemann'", "('sf05k_hegemann'"), ("('sf05h_nagel'", "('sf05k_nagel'"),
             ("    plate_text(Lh, (W/2, H-16*s), '据诺贝尔奖官方新闻稿  ·  头像为插画', F(SANS, 20*s), fill=CREAM, alpha=ramp(t, 3.6, 4.2), anchor='ms')\n",
              "    fa_ = ramp(t, 3.6, 4.2); fn_ = F(SANS_B, 20*s); txt_ = '据诺贝尔奖官方新闻稿  ·  头像为插画'; tw_ = fn_.getlength(txt_)\n"
              "    if fa_ > 0:\n"
              "        Lh.rrect((W/2-tw_/2-14*s, H-46*s, W/2+tw_/2+14*s, H-12*s), 8*s, fill=(8, 10, 24), alpha=0.94*fa_)\n"
              "        Lh.text((W/2, H-22*s), txt_, fn_, fill=(250, 248, 242), alpha=fa_, anchor='ms')\n")):
    assert o in _s5, o; _s5 = _s5.replace(o, n)
exec(compile(_s5, 'sf_r13_sf05', 'exec'), R12.__dict__)
S['SF05_nobel_portraits'] = R12.S['SF05_nobel_portraits']
_sf05_inner = S['SF05_nobel_portraits'][0]
def _sf05_fix(t, W, H):
    rgb = _sf05_inner(t, W, H)
    # bottom rows: the vignette + grade left an ~8 px dark strip; blend the last rows toward the rows above
    s = W/1280; n = int(11*s)+1; ref = rgb[H-n-int(16*s):H-n].mean(0, keepdims=True)
    rgb[H-n:] = np.maximum(rgb[H-n:], ref*0.97)
    return rgb
S['SF05_nobel_portraits'] = (_sf05_fix, 5.0)

# ================================================================================================
# SF08: whole relay chain kept in frame; route labels; two-route timeline; smudge painted out
# ================================================================================================
def _sf08f():
    p = GEN+'sf08f_relay.png'
    if not os.path.exists(p):
        im = (img('sf08e_relay')*255).astype(np.uint8); h, w = im.shape[:2]
        src = im.copy(); dx = int(0.30*w)
        sh = np.zeros_like(im); sh[:, dx:] = im[:, :-dx]           # content from 0.42-0.64 lands on 0.72-0.94
        m = np.zeros((h, w), np.float32)
        cv2.ellipse(m, (int(0.82*w), int(0.15*h)), (int(0.115*w), int(0.17*h)), 0, 0, 360, 1, -1)
        m[int(0.345*h):] = 0
        m = cv2.GaussianBlur(m, (0, 0), 0.025*w)[..., None]
        out = src*(1-m)+sh*m
        Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).save(p)
    return 'sf08f_relay'
_sf08f()
_c8 = R11._code8; _c8 = _c8[:_c8.rindex("exec(compile(_s, 'sf_r11_sf08'")]
_c8 += "FINAL8 = _s\n"
exec(compile(_c8, 'r13_sf08_src', 'exec'), R10.__dict__)
_s8 = R10.FINAL8
_cut = _s8.index("    # light -> channel open: the only quantity"); _end = _s8.index("    return grade(over(rgb, L.get()), seed=int(t*24))")
_s8 = _s8[:_cut] + '''    X1, Y1 = P(0.29, 0.43); label(L, (X1, Y1), (250*s, 150*s), '路线一：好几步接力', '感光蛋白 → 中间几步 → 通道', t=ramp(t, 4.9, 5.5), font_size=LT*s, sub_size=LS*s, accent=(255, 226, 176))
    a = ramp(t, 4.4, 4.9)
    if a > 0:
        bx, by, bw, bh = 40*s, 508*s, 640*s, 198*s
        L.rrect((bx, by, bx+bw, by+bh), 8*s, fill=(12, 18, 38), alpha=0.9*a)
        L.text((bx+22*s, by+34*s), '能做到毫秒级吗？', F(SANS_B, 22*s), fill=CREAM, alpha=a, anchor='ls')
        x0, x1 = bx+40*s, bx+bw-40*s; ay_ = by+bh-46*s
        Q = lambda lg: x0+(x1-x0)*(lg+3)/5.78                    # log10 seconds: 1 ms .. 10 min
        L.line([(x0, ay_), (x1, ay_)], fill=(150, 160, 190), width=1.4*s, alpha=a)
        for lg, tk, an in ((-3, '1 ms', 'ls'), (-1, '100 ms', 'ms'), (1, '10 s', 'ms'), (2.78, '10 分钟', 'rs')):
            x = Q(lg); L.line([(x, ay_-5*s), (x, ay_+5*s)], fill=(150, 160, 190), width=1.4*s, alpha=a)
            L.text((x if an != 'ls' else x-4*s, ay_+32*s), tk, F(SANS_B, 22*s), fill=BRIGHT, alpha=a, anchor=an)
        rows = ((by+62*s, -3.0, -2.6, CYAN, (150, 210, 255), '需要：毫秒级', 'r', 4.4, 4.9),
                (by+96*s, -0.5, 1.0, (255, 180, 120), (255, 210, 170), '路线一 · 接力：秒级', 'l', 4.9, 5.5),
                (by+130*s, 1.78, 2.78, MAG, (250, 175, 235), '路线二 · 先给药：分钟级', 'l', 5.9, 6.5))
        for (yy_, l0, l1, col, tcol, txt, side, t0, t1) in rows:
            g = ease_out(ramp(t, t0, t1)); ra = a*ramp(t, t0-0.1, t0+0.2)
            if ra <= 0: continue
            xa0, xa1 = Q(l0), Q(l1)
            L.rrect((xa0, yy_-6*s, xa0+max(6*s, (xa1-xa0)*g), yy_+6*s), 5*s, fill=col, alpha=ra)
            if side == 'r': L.text((xa1+14*s, yy_+7*s), txt, F(SANS_B, 20*s), fill=tcol, alpha=ra, anchor='ls')
            else: L.text((xa0-14*s, yy_+7*s), txt, F(SANS_B, 20*s), fill=tcol, alpha=ra, anchor='rs')
        xm = Q(-2.6)+3*s; L.line([(xm, by+48*s), (xm, ay_)], fill=(140, 200, 255), width=1.2*s, alpha=0.6*a)
''' + _s8[_end:]
for o, n in (("im = img('sf08e_relay')", "im = img('sf08f_relay')"),
             ("    z = 1.52+0.04*u; cxx = 0.335+(0.672-0.335)*pan+0.006*u; cyy = 0.43\n",
              "    z = 1.10*math.exp(0.021*t); cxx = 0.462+(0.520-0.462)*pan; cyy = 0.47\n"),
             ("    chip('路线二 · 通道上外加化学光开关', MAG, b2*(1-ramp(t, 4.35, 4.75)))\n", ""),
             ("'合成光开关（偶氮苯）', '要另外把化学分子送进组织'", "'路线二：合成光开关（偶氮苯）', '要另外把化学分子送进组织'")):
    assert o in _s8, o; _s8 = _s8.replace(o, n)
exec(compile(_s8, 'sf_r13_sf08', 'exec'), R10.__dict__)
S['SF08_early_attempts'] = R10.S['SF08_early_attempts']

# ================================================================================================
# SF11: one label at a time on the eye; goggles caption on one line
# ================================================================================================
R10.LBL[('SF11_eye_goggles', '角膜、晶状体把光折向中央凹')] = None
R10.LBL[('SF11_eye_goggles', '感光细胞：已大量丢失')] = 3.0
@scene('SF11_eye_goggles', 5.0)
def sf11(t, W, H):
    s = W/1280; rgb = R10._sf11_base10(t, W, H)
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
        f2 = F(SANS_B, 22*s); txt = '护目镜：把看到的画面变成琥珀色光脉冲'; tw = f2.getlength(txt)
        L2.rrect((C[0]+R+14*s, C[1]-26*s, C[0]+R+42*s+tw, C[1]+22*s), 6*s, fill=(11, 16, 34), alpha=0.8*ta)
        L2.line([(C[0]+R+14*s, C[1]-26*s), (C[0]+R+14*s, C[1]+22*s)], fill=AMBER, width=3*s, alpha=ta)
        L2.text((C[0]+R+28*s, C[1]+7*s), txt, f2, fill=CREAM, alpha=ta, anchor='ls')
    return grade(over(rgb, L2.get()), seed=int(t*24)+7, grain=0.004, vig=0.0, lift=(0, 0, 0))

# ================================================================================================
# SF01: relief shading + ink edges on the neuron plate (gives the flat lace neurons bead-like volume)
# ================================================================================================
def relief(a):
    h, w = a.shape[:2]; lum = a.mean(2)
    sat = a.max(2)-a.min(2)
    hm = cv2.GaussianBlur(np.clip(lum*1.2+sat*0.6, 0, 1.5), (0, 0), 2.2*w/1672)
    gx = cv2.Sobel(hm, cv2.CV_32F, 1, 0, ksize=3); gy = cv2.Sobel(hm, cv2.CV_32F, 0, 1, ksize=3)
    k = 6.0; nx, ny = -gx*k, -gy*k; nz = np.ones_like(nx); nn = np.sqrt(nx*nx+ny*ny+nz*nz)
    lx, ly, lz = -0.5, -0.6, 0.62; dif = (nx*lx+ny*ly+nz*lz)/nn
    sh = np.clip((dif-0.62)*0.9, -0.24, 0.26)
    spec = np.clip(dif-0.9, 0, 1)*2.5
    fine = cv2.GaussianBlur(lum, (0, 0), 0.9); coarse = cv2.GaussianBlur(lum, (0, 0), 3.0)
    ink = np.clip((coarse-fine)*4.0, 0, 0.42)*(1-np.clip((a[..., 2]-0.55)*3, 0, 1)*np.clip((a[..., 1]-0.45)*3, 0, 1))                     # dark rims where a bright shape meets dark ground
    out = a*(1+sh[..., None])+spec[..., None]*np.array([0.55, 0.6, 0.75])*0.25
    out = out*(1-ink[..., None])+np.array([0.05, 0.04, 0.12])*ink[..., None]
    return np.clip(out, 0, 1).astype(np.float32)
_dk12 = R7._darkL
R7._darkL = lambda a, edge=0.56, amt=0.62: _dk12(relief(a), edge, amt)

# ------------------------------------------------------------------------------------------------
# SF10 (needs gen/vid/sf10_riseA12.mp4 + sf10_walk12.mp4)
# ------------------------------------------------------------------------------------------------
import sf_r13_sf10  # noqa: E402,F401

# ------------------------------------------------------------------------------------------------
# wrap every new scene again (round-9/10 wrapper + round-10 push multiplier)
# ------------------------------------------------------------------------------------------------
for _n in list(S):
    _fn, _d = S[_n]
    if getattr(_fn, '_r11', False): continue
    if not getattr(_fn, '_r10', False): _fn = R10._wrap10(_n, _fn)
    S[_n] = (R11._wrap11(_n, _fn), _d)
S['SF10_mouse_tripo'] = (S['SF10_mouse_tripo'][0], R10.SF10_D)
