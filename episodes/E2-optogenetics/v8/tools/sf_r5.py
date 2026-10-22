"""Round 5 overrides (P0 only): SF01/03/04/05/07/08/09/10/11 (+SF06 card uses fixed retinal plate)."""
import sys; sys.path.insert(0, '/workspace/e2work/v8/tools')
from sf_scenes import *          # noqa  (S, scene, img, _cache, label, LT, LS, drift_specks, cyan_mask, circ_arr, P5, portrait ...)
import sf_scenes as SS
from sf_scenes import _cache
import mol
from scipy.interpolate import RBFInterpolator

def lin(t, dur): return min(max(t/dur, 0), 1)          # constant-speed drift: never settles into a still

def beam_motes(L, t, src, dst, spread, n=40, seed=3, color=(190, 225, 255), amt=0.7, s=1.0, speed=0.12):
    """dust motes travelling down a light cone from src to dst (pixel coords)"""
    rng = np.random.default_rng(seed)
    for i in range(n):
        u = (rng.random() + t*speed*(0.6+0.8*rng.random())) % 1.0
        off = (rng.random()-0.5)*2*spread*u
        x = src[0]+(dst[0]-src[0])*u; y = src[1]+(dst[1]-src[1])*u
        dx, dy = dst[0]-src[0], dst[1]-src[1]; Ln = math.hypot(dx, dy); nx, ny = -dy/Ln, dx/Ln
        a = amt*min(1, u*6)*min(1, (1-u)*5)*(0.5+0.5*math.sin(t*2.1+i*1.7))
        L.dot((x+nx*off, y+ny*off), (1.0+1.2*rng.random())*s, fill=color, alpha=max(0, a))

# ---------------- SF01: continuous dolly + beam motes + travelling pulses ----------------
@scene('SF01_open_title', 5.0)
def sf01(t, W, H):
    im = img('sf01b_open_bg')
    if 'off1' not in _cache:
        m = cyan_mask(im, 120, 1.0); m = cv2.GaussianBlur(cv2.dilate(m, np.ones((9, 9), np.uint8)), (0, 0), 4)[..., None]
        _cache['m1b'] = m
        fg = cv2.GaussianBlur(np.ascontiguousarray(im[:, ::-1]), (0, 0), 18); _cache['fg1'] = fg
        ih, iw = im.shape[:2]; yy, xx = np.mgrid[0:ih, 0:iw]; _cache['xy1'] = (xx/iw + yy/ih).astype(np.float32)
    on = ramp(t, 0.6, 1.8); fade = ramp(t, 0.0, 0.9); u = lin(t, 5)
    # neurons: travelling brightness waves along the dendrites keep them alive after the reveal
    wave = 0.82 + 0.18*np.sin(_cache['xy1']*22 - t*5.0)[..., None]
    src = im*(1-_cache['m1b']) + im*_cache['m1b']*(wave*on + 0.25*(1-on))
    z = 1.0 + 0.10*u; cx, cy = 0.5 + 0.035*u, 0.5 - 0.01*u
    rgb = cam(src, W, H, zoom=z, cx=cx, cy=cy)*fade; rgb = glow(rgb, 0.7, W/55, 0.15+0.45*on)
    fg = cam(_cache['fg1'], W, H, zoom=1.25+0.16*u, cx=0.62-0.07*u, cy=0.55)
    yy, xx = np.mgrid[0:H, 0:W]; fm = (np.clip(1-xx/(W*0.45), 0, 1)**1.5*0.45)[..., None]
    rgb = rgb*(1-fm) + (fg*0.55)*fm
    s = W/1280
    Lm = Layer(W, H)
    sx, sy = to_px(im, 0.905, 0.035, W, H, z, cx, cy); dx_, dy_ = to_px(im, 0.66, 0.62, W, H, z, cx, cy)
    beam_motes(Lm, t, (sx, sy), (dx_, dy_), 120*s, n=70, seed=4, amt=0.8*on, s=s)
    rgb = over(rgb, Lm.get(), shadow=0, glow_amt=0.9)
    rgb = over(rgb, drift_specks(W, H, t, 50, 3, (170, 200, 255), 0.35, 1.6, (14, -6)), shadow=0)
    L = Layer(W, H)
    a = ramp(t, 1.3, 2.5); tr = (46*(1-ease_out(ramp(t, 1.3, 3.2)))+18)*s
    L.text((96*s, 330*s), '光遗传学', F(SERIF_B, 108*s), fill=CREAM, alpha=a, anchor='ls', tracking=tr)
    L.line([(98*s, 364*s), (98*s+310*s*ease_out(ramp(t, 1.9, 2.9)), 364*s)], fill=CYAN, width=1.8*s, alpha=a)
    L.text((98*s, 404*s), '用一束光，只拨动一类神经元', F(SANS, 28*s), fill=CREAM, alpha=ramp(t, 2.4, 3.3)*0.94, anchor='ls', tracking=3*s)
    L.text((98*s, 442*s), 'OPTOGENETICS', F(SANS, 16*s), fill=MUTED, alpha=ramp(t, 2.7, 3.5), anchor='ls', tracking=9*s)
    L.text((98*s, 640*s), 'EigenLens 主观知识  ·  第 2 期', F(SANS, 16*s), fill=(176, 186, 212), alpha=ramp(t, 3.0, 3.8)*0.9, anchor='ls', tracking=2*s)
    # a slow light glint travels along the cyan rule after the title settles
    g = ((t-3.0)/1.6) % 1.0 if t > 3.0 else -1
    if g >= 0: L.dot((98*s+310*s*g, 364*s), 3*s, fill=(220, 240, 255), alpha=0.9*math.sin(math.pi*g))
    return grade(over(rgb, L.get(), glow_amt=0.25), seed=int(t*24))

# ---------------- SF03: one unified plate + magnifier insets showing the membrane opsins ----------------
def circ_img(arr, R, zoom=1.0, cx=0.5, cy=0.5):
    a = cam(arr, R*2, R*2, zoom=zoom, cx=cx, cy=cy); im = Image.fromarray((np.clip(a, 0, 1)*255).astype(np.uint8)).convert('RGBA')
    m = Image.new('L', (R*2*4, R*2*4), 0); ImageDraw.Draw(m).ellipse([0, 0, R*8-1, R*8-1], fill=255); im.putalpha(m.resize((R*2, R*2), Image.LANCZOS)); return im

def inset(L, rgbL_pts, t, a, arr, centre, R, anchor, col, ring_label, zoom_t):
    """magnifier: leader from the cell membrane to a circular close-up that grows out of it"""
    if a <= 0: return
    cx, cy = centre; ax, ay = anchor; k = ease_out(a)
    # inset grows from the anchor toward its centre
    px, py = ax+(cx-ax)*k, ay+(cy-ay)*k; r = max(2, int(R*k))
    # leader: two tangent-ish lines from anchor ring to the inset rim
    L.ring((ax, ay), 9*L.W/1280, fill=col, width=1.6*L.W/1280, alpha=a)
    ang = math.atan2(ay-py, ax-px); off = 0.55
    for sgn in (-1, 1):
        ex, ey = px+r*math.cos(ang+sgn*off), py+r*math.sin(ang+sgn*off)
        L.line([(ax, ay), (ex, ey)], fill=col, width=1.0*L.W/1280, alpha=0.6*a)
    L.dot((px, py), r+5*L.W/1280, fill=(10, 14, 30), alpha=0.55*a)
    L.paste(circ_img(arr, r, zoom=1.05+0.08*zoom_t, cx=0.5, cy=0.5), (px-r, py-r), alpha=a)
    L.ring((px, py), r, fill=col, width=2.2*L.W/1280, alpha=a)

@scene('SF03_microbe_clues', 5.0)
def sf03(t, W, H):
    im = img('sf03d_microbes'); u = lin(t, 5); s = W/1280
    z = 1.02+0.07*u; cxx = 0.5+0.012*u; cyy = 0.5
    # the alga sways (rotation about its body) — whole-cell motion, not a still
    ih, iw = im.shape[:2]; acx, acy = 0.69*iw, 0.55*ih
    ang = 2.0*math.sin(t*1.9); M = cv2.getRotationMatrix2D((acx, acy), ang, 1.0); M[0, 2] += 7*math.sin(t*1.2); M[1, 2] += 5*math.sin(t*1.6)
    rot = cv2.warpAffine(im, M, (iw, ih), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
    if 'am3d' not in _cache:
        yy, xx = np.mgrid[0:ih, 0:iw]; d = np.hypot((xx-acx)/(0.30*iw), (yy-0.42*ih)/(0.50*ih))
        _cache['am3d'] = (np.clip((1-d)/0.25, 0, 1)*(xx > 0.53*iw))[..., None]
    src = im*(1-_cache['am3d']) + rot*_cache['am3d']
    rgb = cam(src, W, H, zoom=z, cx=cxx, cy=cyy)
    P = lambda x, y: to_px(im, x, y, W, H, z, cxx, cyy)
    ex, ey = P(0.733+0.004*math.sin(t*1.2), 0.505+0.003*math.sin(t*1.6))
    flash = ramp(t, 2.3, 2.8)*(0.7+0.3*math.sin(t*6))
    rgb = rgb + radial(W, H, ex, ey, W*0.012, (255, 120, 60), 0.45*flash) + radial(W, H, ex, ey, W*0.05, CYAN, 0.12*flash)
    rgb = over(rgb, drift_specks(W, H, t, 70, 7, (190, 230, 255), 0.35, 1.4, (12, -6)), shadow=0)
    L = Layer(W, H)
    # header
    L.rrect((28*s, 26*s, 352*s, 68*s), 6*s, fill=(12, 18, 38), alpha=0.75*ramp(t, 0.1, 0.8))
    L.text((44*s, 54*s), '接下来的那些年 · 微生物那边', F(SANS, 18*s), fill=CREAM, alpha=ramp(t, 0.1, 0.8)*0.92, anchor='ls', tracking=3*s)
    # left inset: archaeal membrane, purple light-driven pumps
    ax, ay = P(0.352, 0.375)
    inset(L, None, t, ramp(t, 0.7, 1.5), img('sf03_ins_l2'), (560*s, 150*s), int(108*s), (ax, ay), GOLD, None, lin(t, 5))
    # right inset: algal eyespot membrane, teal channels
    inset(L, None, t, ramp(t, 2.0, 2.8), img('sf03_ins_r2'), (1110*s, 440*s), int(108*s), (ex, ey), CYAN, None, lin(t, 5))
    rgb = over(rgb, L.get(), shadow=0.35)
    # light pulses inside the insets (the opsins are driven by light)
    for (c, a0) in (((560*s, 150*s), 1.5), ((1110*s, 440*s), 2.8)):
        if t > a0: rgb = rgb + radial(W, H, c[0], c[1]-40*s, 40*s, (170, 215, 255), 0.10*(0.6+0.4*math.sin(t*4))*ramp(t, a0, a0+0.4))
    L2 = Layer(W, H)
    def card(x, y, title, sub, a, col, right=False):
        if a <= 0: return
        tw = max(F(SANS_B, LT*s).getlength(title), F(SANS, LS*s).getlength(sub)) + 36*s
        x0 = x - tw if right else x
        L2.rrect((x0, y, x0+tw, y+66*s), 6*s, fill=(12, 18, 38), alpha=0.8*a); L2.line([(x0, y), (x0, y+66*s)], fill=col, width=3*s, alpha=a)
        L2.text((x0+18*s, y+28*s), title, F(SANS_B, LT*s), fill=CREAM, alpha=a, anchor='ls')
        L2.text((x0+18*s, y+54*s), sub, F(SANS, LS*s), fill=(176, 186, 212), alpha=a, anchor='ls')
    card(40*s, 610*s, '嗜盐古菌 · 1970s–80s', '膜上找到光驱动的泵：细菌视紫红质、盐视紫红质', ramp(t, 1.1, 1.8), GOLD)
    card(1240*s, 610*s, '衣藻 · 1991–96', '眼点受光，膜上微秒级就出现电流', ramp(t, 2.5, 3.2), CYAN, right=True)
    # in-inset captions (what the magnified blobs are)
    a = ramp(t, 1.3, 1.9); L2.text((560*s, 150*s+108*s+24*s), '膜蛋白（视紫红质类）', F(SANS_B, 16*s), fill=CREAM, alpha=a, anchor='ms')
    a = ramp(t, 2.6, 3.2); L2.text((1110*s, 440*s-108*s-12*s), '眼点膜上的感光蛋白', F(SANS_B, 16*s), fill=CREAM, alpha=a, anchor='ms')
    return grade(over(rgb, L2.get()), seed=int(t*24))

# ---------------- SF04: layered parallax + light sweep (no dead frames) ----------------
@scene('SF04_crick_quote', 5.0)
def sf04(t, W, H):
    s = W/1280; u = lin(t, 5)
    P0 = img('sf04_crick_portrait'); bg = np.concatenate([P0[:30, :30].reshape(-1, 3), P0[:30, -30:].reshape(-1, 3)]).mean(0)
    rgb = np.zeros((H, W, 3), np.float32)+bg
    rgb = rgb + radial(W, H, W*(0.30-0.05*u), H*0.42, W*0.25, (50, 70, 130), 0.25)       # bg glow drifts opposite (parallax)
    ph = int(H*0.94); pw = ph; pa = ramp(t, 0, 0.8); dx = int(14*s*(1-ease_out(ramp(t, 0, 1.5))))
    Pc = cam(P0, pw, ph, zoom=1.0+0.085*u, cx=0.5+0.02*u, cy=0.48)
    # warm light sweep across the face after the quote lands
    sw = ramp(t, 2.4, 4.6)
    if 0 < sw < 1:
        yy, xx = np.mgrid[0:ph, 0:pw]; band = np.exp(-(((xx+yy*0.6)/pw - (-0.2+1.8*sw))/0.08)**2)
        lum = Pc.mean(2, keepdims=True); Pc = np.clip(Pc + band[..., None]*np.clip(lum-0.25, 0, 1)*np.array([1.0, 0.8, 0.45])*0.55, 0, 1)
    yy, xx = np.mgrid[0:ph, 0:pw]; e = np.minimum.reduce([xx/pw*3, (1-xx/pw)*1.6, yy/ph*4, (1-yy/ph)*2.2]); m = (np.clip(e, 0, 1)**1.4*pa)[..., None]
    x0 = int(30*s)-dx; y0 = H-ph
    rgb[y0:, x0:x0+pw] = rgb[y0:, x0:x0+pw]*(1-m)+Pc*m
    rgb = over(rgb, drift_specks(W, H, t, 45, 9, (240, 220, 180), 0.32, 1.6, (-10, -5)), shadow=0)
    L = Layer(W, H); ty = -8*s*u      # text block drifts up slowly (separate depth plane)
    L.text((690*s, 246*s+ty), '1999', F(SANS_B, 20*s), fill=GOLD, alpha=ramp(t, 0.5, 1.1), anchor='ls', tracking=6*s)
    L.text((690*s, 318*s+ty), '“理想的信号会是光”', F(SERIF_B, 46*s), fill=CREAM, alpha=ramp(t, 0.8, 1.8), anchor='ls')
    L.text((690*s, 390*s+ty), '——他也承认：', F(SERIF, 27*s), fill=(176, 186, 212), alpha=ramp(t, 2.2, 2.8), anchor='ls')
    em = ramp(t, 2.6, 3.4); tr = (2.5*ease_out(ramp(t, 2.6, 4.0)))*s
    L.text((690*s, 448*s+ty), '这个想法相当牵强。', F(SERIF_B, 38*s), fill=GOLD, alpha=em, anchor='ls', tracking=tr)
    L.line([(690*s, 490*s+ty), (690*s+440*s*ease_out(ramp(t, 3.2, 4.2)), 490*s+ty)], fill=(90, 100, 135), width=1*s)
    L.text((690*s, 522*s+ty), '原文 “rather far-fetched”', F(SANS, 18*s), fill=CREAM, alpha=ramp(t, 3.4, 4.2)*0.92, anchor='ls')
    L.text((690*s, 550*s+ty), 'F. Crick, Phil. Trans. R. Soc. Lond. B, 1999', F(SANS, 17*s), fill=(176, 186, 212), alpha=ramp(t, 3.5, 4.3), anchor='ls')
    rgb = over(rgb, L.get(), glow_amt=0.15)
    # glow pulse on the emphasised phrase
    rgb = rgb + radial(W, H, 850*s, 435*s+ty, 170*s, GOLD, 0.06*em*(0.6+0.4*math.sin(t*3)))
    return grade(rgb, seed=int(t*24))

# ---------------- SF05: each portrait keeps drifting + staggered gold sweeps ----------------
@scene('SF05_nobel_portraits', 5.0)
def sf05(t, W, H):
    s = W/1280; u = lin(t, 5)
    bg = np.mean([img(P5[k][0])[5:60, 5:60].reshape(-1, 3).mean(0) for k in 'DHN'], axis=0); rgb = np.zeros((H, W, 3), np.float32)+bg
    rgb = rgb + radial(W, H, W*(0.35+0.3*u), H*0.15, W*0.40, (80, 90, 150), 0.12)
    names = [('D', 'Karl Deisseroth'), ('H', 'Peter Hegemann'), ('N', 'Georg Nagel')]
    L = Layer(W, H); cw = int(372*s); gap = int(28*s); x0 = (W-3*cw-2*gap)//2; y0 = int(176*s)
    for i, (k, nm) in enumerate(names):
        a = ramp(t, 0.5+i*0.45, 1.3+i*0.45); dy = int(26*s*(1-ease_out(a)))
        n, cy = P5[k]; Pc = cam(img(n), cw, cw, zoom=1.0+0.14*u, cx=0.5+(i-1)*0.025*u, cy=cy-0.03*u)
        sw = ramp(t, 2.6+i*0.4, 3.9+i*0.4)
        if 0 < sw < 1:
            yy, xx = np.mgrid[0:cw, 0:cw]; band = np.exp(-(((xx+yy*0.5)/cw-(-0.2+1.7*sw))/0.09)**2)
            lum = Pc.mean(2, keepdims=True); Pc = np.clip(Pc+band[..., None]*np.clip(lum-0.25, 0, 1)*np.array([1.0, 0.8, 0.45])*0.5, 0, 1)
        x = x0+i*(cw+gap); y = y0+dy
        yy, xx = np.mgrid[0:cw, 0:cw]; e = np.minimum.reduce([xx/cw, (1-xx/cw), yy/cw*1.5, (1-yy/cw)*0.55]); m = (np.clip(e/0.24, 0, 1)**1.8)[..., None]*a
        rgb[y:y+cw, x:x+cw] = rgb[y:y+cw, x:x+cw]*(1-m)+Pc*m
        L.line([(x+10*s, y0+cw+18*s), (x+10*s+(cw-20*s)*ease_out(a), y0+cw+18*s)], fill=GOLD, width=1.3*s, alpha=a)
        if 0 < sw < 1: L.dot((x+10*s+(cw-20*s)*sw, y0+cw+18*s), 3*s, fill=(255, 236, 190), alpha=math.sin(math.pi*sw))
        L.text((x+cw/2, y0+cw+60*s), nm, F(SERIF_B, 28*s), fill=CREAM, alpha=a, anchor='ms')
    L.text((W/2, 76*s), '2026 年 10 月 5 日  ·  诺贝尔生理学或医学奖', F(SANS_B, 26*s), fill=GOLD, alpha=ramp(t, 0, 0.6), anchor='ms', tracking=2*s)
    L.text((W/2, 118*s), '获奖理由：发现光控离子通道，并由此建立光遗传学', F(SERIF, 20*s), fill=CREAM, alpha=ramp(t, 2.2, 3.0)*0.92, anchor='ms')
    L.text((W/2, H-22*s), '据诺贝尔奖官方新闻稿  ·  头像为插画', F(SANS, 16*s), fill=(176, 186, 212), alpha=ramp(t, 2.6, 3.4)*0.9, anchor='ms')
    rgb = over(rgb, drift_specks(W, H, t, 40, 21, (240, 220, 170), 0.28, 1.5, (8, -4)), shadow=0)
    return grade(over(rgb, L.get()), seed=int(t*24))

# ---------------- SF06: same card, retinal plate fixed (beta-ionone) ----------------
_sf06_src = SS.S['SF06_switch_diagram'][0]
@scene('SF06_switch_diagram', 6.0)
def sf06(t, W, H):
    G0 = SS.G; orig = Image.open
    def op(p, *a, **k): return orig(p.replace('sf09d_chr2.png', 'sf09e_chr2.png') if isinstance(p, str) else p, *a, **k)
    SS.Image.open = op
    try: return _sf06_src(t, W, H)
    finally: SS.Image.open = orig

# ---------------- SF07: rays no longer tinted brown, whole brain in frame, continuous activity ----------------
@scene('SF07_main_title', 5.0)
def sf07(t, W, H):
    s = W/1280; im = img('sf07c_title_bg'); ih, iw = im.shape[:2]; u = lin(t, 5)
    if 'p7c' not in _cache:
        bg = np.concatenate([im[:40, :40].reshape(-1, 3), im[-40:, :40].reshape(-1, 3), im[-40:, -40:].reshape(-1, 3)]).mean(0)
        tip = (0.595, 0.245); yy, xx = np.mgrid[0:ih, 0:iw]; d = np.hypot(xx/iw-tip[0], (yy/ih-tip[1])*1.5)
        cm = cyan_mask(im, 110, 2.0); far = np.clip((d-0.10)/0.12, 0, 1)
        # god-rays at upper-left: fade them into the navy background instead of tinting them (was the brown smear)
        rays = np.clip((0.52-xx/iw)/0.12, 0, 1)*np.clip((0.33-yy/ih)/0.08, 0, 1)
        lum = im.mean(2, keepdims=True); kc = (cm*far)[..., None]
        tame = im*(1-kc)+(lum*np.array([0.85, 0.72, 0.82]))*kc          # stray cyan on the brain -> its own pink tone
        poly = np.array([[0.0, 0.0], [0.44, 0.0], [0.40, 0.10], [0.31, 0.175], [0.22, 0.22], [0.0, 0.16]])*[iw, ih]
        pm = np.zeros((ih, iw), np.uint8); cv2.fillPoly(pm, [poly.astype(np.int32)], 1)
        fib = (np.abs(xx/iw-0.592) < 0.012)
        pm[fib] = 0
        kr = cv2.GaussianBlur(pm.astype(np.float32), (0, 0), 6)[..., None]
        w_ = (1-cv2.dilate(pm, np.ones((25, 25), np.uint8))).astype(np.float32)[..., None]
        fillc = cv2.GaussianBlur(im*w_, (0, 0), 45)/np.maximum(cv2.GaussianBlur(w_, (0, 0), 45)[..., None], 1e-3)
        tame = tame*(1-kr)+fillc*kr
        cm2 = cyan_mask(im, 175, 1.0)*(d < 0.16); ys, xs = np.nonzero(cm2 > 0.5); rng = np.random.default_rng(2); idx = rng.choice(len(xs), min(110, len(xs)), replace=False)
        _cache['p7c'] = (bg, tame, [(xs[i]/iw, ys[i]/ih, rng.random()) for i in idx], tip)
    bg, tame, pts, tip = _cache['p7c']
    z = 1.0+0.13*u; sc_ = H*0.86/ih*z; Wi, Hi = int(iw*sc_), int(ih*sc_)
    ox = W*0.5-0.55*Wi - 18*s*u; oy = H*0.36-0.36*Hi + 6*s*u
    M = np.array([[sc_, 0, ox], [0, sc_, oy]], np.float32)
    rgb = np.zeros((H, W, 3), np.float32)+bg
    pic = cv2.warpAffine(tame, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_CONSTANT, borderValue=tuple(float(v) for v in bg))
    yy, xx = np.mgrid[0:H, 0:W]; e = np.minimum.reduce([(xx-ox)/(140*s), (ox+Wi-xx)/(140*s), (yy-oy-0.10*Hi)/(0.12*Hi)+0.25]); mk = np.clip(e, 0, 1)[..., None]
    rgb = rgb*(1-mk)+pic*mk
    L = Layer(W, H)
    for (px, py, ph) in pts:
        d = math.hypot(px-tip[0], (py-tip[1])*1.5)
        a = 0.25*(t > 0.7+d*8)
        for w0 in (0.7, 2.2, 3.7):                      # three activity waves spread out from the fibre tip
            tk = w0+d*8.0+ph*0.15; a += math.exp(-((t-tk)/0.16)**2)
        L.dot((ox+px*Wi, oy+py*Hi), 2.2*s, fill=(170, 225, 255), alpha=min(1, a))
    # photons running down the fibre
    fx = ox+0.592*Wi; ftop = 0; fbot = oy+tip[1]*Hi
    for n in range(5):
        p = (t*0.9+n/5) % 1.0
        L.dot((fx+(ox+tip[0]*Wi-fx)*p, ftop+(fbot-ftop)*p), 2.6*s, fill=(210, 240, 255), alpha=ramp(t, 0.4, 0.8)*min(1, (1-p)*6))
    rgb = over(rgb, L.get(), shadow=0, glow_amt=1.4)
    tx, ty = ox+tip[0]*Wi, oy+tip[1]*Hi; rgb = rgb+radial(W, H, tx, ty, 60*s, CYAN, 0.35*ramp(t, 0.5, 1.2)*(0.85+0.15*math.sin(t*4)))
    rgb = over(rgb, drift_specks(W, H, t, 60, 11, (180, 205, 255), 0.3, 1.6, (10, -5)), shadow=0)
    L = Layer(W, H)
    a = ramp(t, 1.0, 2.2); tr = (60*(1-ease_out(ramp(t, 1.0, 3.2)))+34)*s
    L.text((W/2, 598*s), '光遗传学', F(SERIF_B, 108*s), fill=CREAM, alpha=a, anchor='ms', tracking=tr)
    L.text((W/2, 640*s), 'O P T O G E N E T I C S', F(SANS, 17*s), fill=CYAN, alpha=ramp(t, 2.0, 2.8), anchor='ms', tracking=4*s)
    L.text((W/2, 680*s), '这一期，就讲这枚开关', F(SANS, 22*s), fill=(190, 198, 222), alpha=ramp(t, 2.6, 3.4), anchor='ms', tracking=4*s)
    return grade(over(rgb, L.get(), glow_amt=0.35), seed=int(t*24))

# ---------------- SF08: two beats (camera pans), unified ball-and-stick azobenzene ----------------
AZO_T = mol.azobenzene_geom(False); AZO_C = mol.azobenzene_geom(True)
def azo_geom(k):
    """morph trans->cis by interpolating atom positions (k in 0..1)"""
    Ct, b, n, a = AZO_T; Cc = AZO_C[0]
    # align: keep ring a fixed (same in both), move the rest
    return ({key: (Ct[key][0]*(1-k)+Cc[key][0]*k, Ct[key][1]*(1-k)+Cc[key][1]*k) for key in Ct}, b, n, a)
MAG = (236, 92, 196); MAG_O = (70, 20, 60)
_azo_cache = {}
def azo_sprite(k, px, ang):
    key = (round(k, 2), int(px), int(ang))
    if key not in _azo_cache: _azo_cache[key] = mol.draw(azo_geom(k), px, ang, fill=MAG, outline=MAG_O, bond=0.42)[0]
    return _azo_cache[key]

@scene('SF08_early_attempts', 7.0)
def sf08(t, W, H):
    im = img('sf08e_relay'); s = W/1280
    pan = ease(ramp(t, 3.25, 4.15)); u = lin(t, 7)
    z = 1.52+0.04*u; cxx = 0.335+(0.672-0.335)*pan+0.006*u; cyy = 0.43
    rgb = cam(im, W, H, zoom=z, cx=cxx, cy=cyy)
    P = lambda x, y: to_px(im, x, y, W, H, z, cxx, cyy)
    # --- beat 1: relay pulse receptor -> G protein -> effector -> channel
    path = [(0.115, 0.40), (0.23, 0.52), (0.41, 0.50), (0.585, 0.47)]
    uu = ramp(t, 0.7, 2.6)*(len(path)-1); i = min(int(uu), len(path)-2); f = uu-i
    if 0 < uu and t < 2.75:
        px = path[i][0]+(path[i+1][0]-path[i][0])*f; py = path[i][1]+(path[i+1][1]-path[i][1])*f
        X, Y = P(px, py); rgb = rgb+radial(W, H, X, Y, W*0.014, (255, 226, 176), 0.9)+radial(W, H, X, Y, W*0.05, (255, 226, 176), 0.15)
    X, Y = P(0.11, 0.30); rgb = rgb+radial(W, H, X, Y, W*0.03, CYAN, 0.6*math.exp(-((t-0.55)/0.3)**2))
    openA = ramp(t, 2.6, 3.0); X, Y = P(0.585, 0.49); rgb = rgb+radial(W, H, X, Y, W*0.025, (255, 209, 102), 0.3*openA)
    # --- beat 2: free azobenzene switches drift in; violet light bends the tethered one; channel opens late
    L = Layer(W, H)
    free = [(0.775, 0.085, 20), (0.92, 0.075, -25), (0.87, 0.20, 40), (0.965, 0.25, 10), (0.70, 0.18, -15)]
    for j, (fx, fy, ang) in enumerate(free):
        X, Y = P(fx+0.006*math.sin(t*0.7+j), fy+0.02*u+0.004*math.sin(t*0.9+j*2))
        spr = azo_sprite(0, 104*s, ang+8*math.sin(t*0.5+j)); L.paste(spr, (X-spr.size[0]/2, Y-spr.size[1]/2), alpha=0.85)
    hit = ramp(t, 4.7, 5.0); bend = ease(ramp(t, 4.95, 5.35))
    TX, TY = P(0.82, 0.345)
    L.line([P(0.808, 0.395), (TX-18*s, TY+10*s)], fill=MAG_O, width=5*s); L.line([P(0.808, 0.395), (TX-18*s, TY+10*s)], fill=MAG, width=3*s)
    spr = azo_sprite(round(bend*20)/20, 120*s, -12); L.paste(spr, (TX-spr.size[0]/2, TY-spr.size[1]/2))
    rgb = over(rgb, L.get(), shadow=0.35)
    # violet light (photoswitch needs its own wavelength) arrives as a wavy photon
    if t > 4.3:
        Lp = Layer(W, H); sx, sy = TX+150*s, TY-200*s; k = ramp(t, 4.3, 4.75)
        pts = []
        for q in np.linspace(0, k, 60):
            x = sx+(TX-sx)*q; y = sy+(TY-sy)*q; nx, ny = 0.8, 0.6
            pts.append((x+nx*7*s*math.sin(q*40), y+ny*7*s*math.sin(q*40)*-1))
        if len(pts) > 1: Lp.line(pts, fill=(190, 150, 255), width=2.2*s, alpha=1-ramp(t, 5.2, 5.6))
        rgb = over(rgb, Lp.get(), shadow=0, glow_amt=1.2)
        rgb = rgb+radial(W, H, TX, TY, 40*s, (190, 150, 255), 0.5*hit*(1-ramp(t, 5.3, 6.0)))
    openB = ramp(t, 5.55, 5.9); X, Y = P(0.82, 0.50); rgb = rgb+radial(W, H, X, Y, W*0.025, (255, 209, 102), 0.3*openB)
    L = Layer(W, H)
    for (cx_, op, ph0) in ((0.585, openA, 0.0), (0.82, openB, 0.3)):
        if op <= 0: continue
        for n in range(10):
            p = (t*0.45+n/10+ph0) % 1.0; X, Y = P(cx_+0.004*math.sin(n*2.1+p*7), 0.33+p*0.36); a = op*min(1, p*8)*min(1, (1-p)*8)
            L.dot((X, Y), 5.5*s, fill=(255, 209, 102), alpha=a)
    rgb = over(rgb, L.get(), shadow=0.2, glow_amt=0.6)
    # --- annotations: max 3 per beat
    L = Layer(W, H); b1 = 1-ramp(t, 3.1, 3.4); b2 = ramp(t, 3.9, 4.3)
    def chip(txt, col, a):
        if a <= 0: return
        tw = F(SANS_B, 20*s).getlength(txt)+40*s
        L.rrect((40*s, 30*s, 40*s+tw, 72*s), 21*s, fill=(12, 18, 38), alpha=0.85*a); L.dot((60*s, 51*s), 6*s, fill=col, alpha=a)
        L.text((76*s, 58*s), txt, F(SANS_B, 20*s), fill=CREAM, alpha=a, anchor='ls')
    chip('路线一 · 好几步信号接力', (255, 226, 176), ramp(t, 0.1, 0.6)*b1)
    chip('路线二 · 通道上外加化学光开关', MAG, b2)
    if b1 > 0:
        steps = [((0.115, 0.36), '① 感光蛋白先接住光', None, (330, 160)), ((0.235, 0.57), '② 中间好几步接力', '一级传一级', (330, 640)), ((0.585, 0.36), '③ 通道最后才打开', None, (1010, 160))]
        for j, ((ax, ay), ti, sub, tp) in enumerate(steps):
            a = ramp(t, 0.5+j*0.85, 1.2+j*0.85)*b1; X, Y = P(ax, ay)
            label(L, (X, Y), (tp[0]*s, tp[1]*s), ti, sub, t=a, font_size=LT*s, sub_size=LS*s, accent=(255, 226, 176) if j < 2 else (255, 209, 102))
    if b2 > 0:
        label(L, (TX+20*s, TY), (1220*s, 300*s), '合成光开关（偶氮苯）', '要另外把化学分子送进组织', t=ramp(t, 4.0, 4.8), font_size=LT*s, sub_size=LS*s, accent=MAG)
        X, Y = P(0.82, 0.58); label(L, (X, Y), (1220*s, 470*s), '受光弯折 → 通道打开', None, t=ramp(t, 5.4, 6.0), font_size=LT*s, accent=(255, 209, 102))
    # speed comparison on a log time axis
    a = ramp(t, 5.9, 6.4)
    if a > 0:
        bx, by, bw = 60*s, 584*s, 560*s
        L.rrect((bx, by, bx+bw, by+108*s), 8*s, fill=(12, 18, 38), alpha=0.86*a)
        x0, x1 = bx+30*s, bx+bw-30*s; ay_ = by+74*s
        L.line([(x0, ay_), (x1, ay_)], fill=(150, 160, 190), width=1.2*s, alpha=a)
        ticks = ['1 ms', '10 ms', '100 ms', '1 s', '10 s']
        for q, tk in enumerate(ticks):
            x = x0+(x1-x0)*q/4; L.line([(x, ay_-4*s), (x, ay_+4*s)], fill=(150, 160, 190), width=1.2*s, alpha=a)
            L.text((x, ay_+22*s), tk, F(SANS, 14*s), fill=(176, 186, 212), alpha=a, anchor='ms')
        L.rrect((x0-5*s, ay_-14*s, x0+(x1-x0)*0.08, ay_-4*s), 4*s, fill=CYAN, alpha=a)
        L.text((x0-5*s, ay_-24*s), '需要：毫秒级', F(SANS_B, 16*s), fill=CYAN, alpha=a, anchor='ls')
        g = ease_out(ramp(t, 6.1, 6.8)); xa_ = x0+(x1-x0)*0.5
        L.rrect((xa_, ay_-14*s, xa_+(x1-xa_)*g, ay_-4*s), 4*s, fill=(255, 180, 120), alpha=a)
        L.text((xa_, ay_-24*s), '这两条路：更慢', F(SANS_B, 16*s), fill=(255, 200, 150), alpha=a, anchor='ls')
    return grade(over(rgb, L.get()), seed=int(t*24))

# ---------------- SF09: retinal redrawn (beta-ionone ring + polyene + Schiff base), denser ion stream ----------------
@scene('SF09_chr2_channel', 5.0)
def sf09(t, W, H):
    im = img('sf09e_chr2'); s = W/1280; u = lin(t, 5); z = 1.30+0.10*u; cxx = 0.49; cyy = 0.44
    on = ramp(t, 0.3, 1.2)
    if 'b9e' not in _cache: _cache['b9e'] = cyan_mask(im, 140, 6)[..., None]
    base = im*(1-_cache['b9e']*(1-(0.8+0.2*on)))
    rgb = cam(base, W, H, zoom=z, cx=cxx, cy=cyy)
    P = lambda x, y: to_px(im, x, y, W, H, z, cxx, cyy)
    L = Layer(W, H); rng = np.random.default_rng(9); offs = rng.random((2, 15))*0.6
    for j, (px_, ph0) in enumerate(((0.434, 0.0), (0.548, 0.5))):
        for n in range(15):
            p = (t*0.36+n/15+ph0+offs[j, n]*0.05) % 1.0
            if t < 1.2 and p > 0.2+0.8*ramp(t, 0.8, 1.2): continue
            X, Y = P(px_+0.004*math.sin(n*2.3+p*8), 0.20+p*0.62); a = on*min(1, p*8)*min(1, (1-p)*8)
            L.dot((X, Y), 5.0*s*z, fill=(255, 209, 102), alpha=a)
    rgb = over(rgb, L.get(), shadow=0.3, glow_amt=0.6)
    rgb = over(rgb, drift_specks(W, H, t, 40, 13, (160, 190, 255), 0.25, 1.4, (4, 2)), shadow=0)
    # retinal glows briefly when light arrives (absorbs blue)
    for (rx, ry) in ((0.394, 0.452), (0.600, 0.458)):
        X, Y = P(rx, ry); rgb = rgb+radial(W, H, X, Y, 40*s, (255, 160, 80), 0.35*math.exp(-((t-1.0)/0.35)**2))
    L2 = Layer(W, H)
    X, Y = P(0.60, 0.33); label(L2, (X, Y), (1220*s, 96*s), '通道视紫红质-2（ChR2）', '二聚体：每个亚基各有一条孔道', t=ramp(t, 1.4, 2.3), font_size=LT*s, sub_size=LS*s, accent=(99, 199, 168))
    X, Y = P(0.378, 0.432); label(L2, (X, Y), (60*s, 620*s), '视黄醛', '吸收蓝光后弯折，带动这扇门打开', t=ramp(t, 2.2, 3.0), font_size=LT*s, sub_size=LS*s, accent=(255, 138, 61))
    X, Y = P(0.548, 0.70); label(L2, (X, Y), (1220*s, 630*s), '阳离子（如 Na⁺）', '顺浓度梯度涌入细胞', t=ramp(t, 2.9, 3.7), font_size=LT*s, sub_size=LS*s, accent=(255, 209, 102))
    X, Y = P(0.33, 0.12); label(L2, (max(X, 40*s), max(Y, 40*s)), (60*s, 96*s), '蓝光 约 470 nm', None, t=ramp(t, 0.6, 1.4), font_size=LT*s, accent=CYAN)
    X, Y = P(0.78, 0.42); label(L2, (X, Y), (1220*s, 470*s), '其他膜蛋白', '不受光控制', t=ramp(t, 3.4, 4.1), font_size=19*s, sub_size=LS*s, accent=(150, 146, 180))
    return grade(over(rgb, L2.get()), seed=int(t*24))

# ---------------- SF11: beams refract at cornea and lens; label order follows narration ----------------
EYE_BEAMS = [[(0.125, 0.370), (0.302, 0.370), (0.378, 0.398), (0.645, 0.445)],
             [(0.125, 0.495), (0.300, 0.495), (0.380, 0.476), (0.645, 0.445)]]
@scene('SF11_eye_goggles', 5.0)
def sf11(t, W, H):
    s = W/1280; u = lin(t, 5)
    if 'eye_clean' not in _cache:
        raw = np.asarray(Image.open(G+'sf11c_eye.png').convert('RGB')); ih, iw = raw.shape[:2]
        m = np.zeros((ih, iw), np.uint8)
        for (a, b) in (((0.13, 0.335), (0.645, 0.445)), ((0.12, 0.42), (0.645, 0.445))):
            cv2.line(m, (int(a[0]*iw), int(a[1]*ih)), (int(b[0]*iw), int(b[1]*ih)), 255, 9)
        hsv = cv2.cvtColor(raw, cv2.COLOR_RGB2HSV); bright = ((hsv[..., 1] > 60) & (hsv[..., 2] > 200)).astype(np.uint8)*255
        m = cv2.bitwise_and(cv2.dilate(m, np.ones((5, 5), np.uint8)), cv2.dilate(bright, np.ones((7, 7), np.uint8)))
        m = cv2.dilate(m, np.ones((5, 5), np.uint8))
        _cache['eye_clean'] = cv2.inpaint(raw, m, 6, cv2.INPAINT_TELEA).astype(np.float32)/255
    im = _cache['eye_clean']; z = 1.05+0.08*u; cxx = 0.47+0.01*u; cyy = 0.48
    rgb = cam(im, W, H, zoom=z, cx=cxx, cy=cyy)
    P = lambda x, y: to_px(im, x, y, W, H, z, cxx, cyy)
    fx, fy = 0.645, 0.445
    on = ramp(t, 1.3, 1.9)
    Lb = Layer(W, H)
    for beam in EYE_BEAMS:
        pts = [P(*p) for p in beam]
        Lb.line(pts, fill=(255, 190, 90), width=2.0*s, alpha=0.75*on)
        for p in pts[1:3]: Lb.dot(p, 3.0*s, fill=(255, 230, 170), alpha=0.8*on)
        # photons travel along the refracted path
        seg = [math.hypot(pts[i+1][0]-pts[i][0], pts[i+1][1]-pts[i][1]) for i in range(3)]; tot = sum(seg)
        for n in range(5):
            d = ((t*0.8+n/5) % 1.0)*tot; i = 0
            while i < 2 and d > seg[i]: d -= seg[i]; i += 1
            f = d/seg[i]; X = pts[i][0]+(pts[i+1][0]-pts[i][0])*f; Y = pts[i][1]+(pts[i+1][1]-pts[i][1])*f
            Lb.dot((X, Y), 3.6*s, fill=(255, 210, 130), alpha=on)
    rgb = over(rgb, Lb.get(), shadow=0, glow_amt=1.1)
    for k in range(7):
        a_ = k/7*2*math.pi; gx = fx+0.022*math.cos(a_); gy = fy+0.035*math.sin(a_); tk = 0.6+((k*0.37) % 1.0)*1.0
        a = math.exp(-((((t-tk) % 1.4))/0.12)**2)*ramp(t, 0.5, 0.8) if t > 0.5 else 0
        X, Y = P(gx, gy); rgb = rgb+radial(W, H, X, Y, 6*s, (240, 131, 91), 0.9*a)
    L = Layer(W, H)
    X, Y = P(fx, fy); label(L, (X, Y), (1220*s, 250*s), '中央凹附近的神经节细胞', '病毒带进 ChrimsonR，受光后放电', t=ramp(t, 0.3, 1.2), font_size=LT*s, sub_size=LS*s, accent=(240, 131, 91))
    X, Y = P(0.09, 0.30); label(L, (X, Y), (60*s, 640*s), '护目镜', '把外界明暗换成琥珀色光脉冲', t=ramp(t, 1.3, 2.2), font_size=LT*s, sub_size=LS*s, accent=AMBER)
    X, Y = P(0.302, 0.37); label(L, (X, Y), (420*s, 96*s), '角膜、晶状体把光折向中央凹', None, t=ramp(t, 2.2, 3.0), font_size=19*s, accent=(255, 200, 120))
    X, Y = P(0.735, 0.24); label(L, (X, Y), (1220*s, 96*s), '感光细胞层', '已大量丢失，残缺不全', t=ramp(t, 3.0, 3.8), font_size=LT*s, sub_size=LS*s, accent=(170, 170, 180))
    return grade(over(rgb, L.get()), seed=int(t*24), lift=(0.03, 0.04, 0.09))

# ---------------- SF10: sleep (breathing) -> light -> cut on the flash -> head lifts -> walks ----------------
def _sf10_prep():
    if 'm10' in _cache: return
    A = img('sf10_awake'); Cn = cv2.resize(img('sf10_clean'), (A.shape[1], A.shape[0]), interpolation=cv2.INTER_AREA)
    ih, iw = A.shape[:2]
    d = np.abs(cv2.GaussianBlur(A, (0, 0), 2.5)-cv2.GaussianBlur(Cn, (0, 0), 2.5)).mean(2)*255
    b = (d > 13).astype(np.uint8)
    yy, xx = np.mgrid[0:ih, 0:iw]
    b[(xx < 0.44*iw) | (yy > 0.79*ih)] = 0
    b = cv2.morphologyEx(b, cv2.MORPH_CLOSE, np.ones((31, 31), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(b); k = 1+np.argmax(st[1:, 4]); b = (lab == k).astype(np.uint8)
    ff = b.copy(); h2 = np.zeros((ih+2, iw+2), np.uint8); cv2.floodFill(ff, h2, (0, 0), 1); b = b | (1-ff)
    b = cv2.erode(b, np.ones((3, 3), np.uint8))
    alpha = cv2.GaussianBlur(b.astype(np.float32), (0, 0), 1.6)
    _cache['m10'] = (A, Cn, alpha)

FEET = [((0.555, 0.625), 0.0), ((0.640, 0.715), 0.5), ((0.830, 0.712), 0.5)]
ANCH = [(0.49, 0.42), (0.58, 0.37), (0.54, 0.23), (0.67, 0.27), (0.60, 0.27), (0.75, 0.30), (0.85, 0.38), (0.70, 0.56),
        (0.80, 0.58), (0.56, 0.50), (0.90, 0.60), (0.88, 0.48), (0.62, 0.05), (0.45, 0.20), (0.45, 0.75), (0.95, 0.20), (0.97, 0.75), (0.66, 0.42)]
HEAD = {0, 1, 2, 3, 4, 17}
def _warp_mouse(t_wake, t_walk, iw, ih):
    """thin-plate warp: head rises after waking; feet swing/stance in a gait cycle while the body travels"""
    src = []; dsp = []
    lift = (1-ease_out(min(max(t_wake/0.6, 0), 1)))*0.035*ih
    T = 0.52; A = 0.012*iw
    for i, (x, y) in enumerate(ANCH):
        dy = lift if i in HEAD else 0.0
        bob = -0.004*ih*abs(math.sin(math.pi*t_walk/T*2)) if t_walk > 0 and i not in (12, 13, 14, 15, 16) else 0
        src.append((x*iw, y*ih)); dsp.append((0.0, dy+bob))
    for (x, y), ph in FEET:
        if t_walk <= 0: dx = 0; dy = 0
        else:
            phi = (t_walk/T+ph) % 1.0
            if phi < 0.4: q = phi/0.4; dx = A-2*A*ease(q); dy = -0.016*ih*math.sin(math.pi*q)      # swing forward (left) and up
            else: q = (phi-0.4)/0.6; dx = -A+2*A*q; dy = 0.0                                       # stance: foot slides back = planted
        src.append((x*iw, y*ih)); dsp.append((dx, dy))
    return np.array(src), np.array(dsp)

@scene('SF10_mouse_tripo', 6.0)
def sf10(t, W, H, still=False, still_frame=None):
    if still: t = 4.8
    s = W/1280; _sf10_prep(); A, Cn, alpha = _cache['m10']; ih, iw = A.shape[:2]
    TCUT = 2.35
    L2 = Layer(W, H)
    if t < TCUT:
        S0 = img('sf10_sleep')
        if 'br10' not in _cache:
            yy, xx = np.mgrid[0:ih, 0:iw]; _cache['br10'] = np.clip(1-np.hypot((xx-0.72*iw)/(0.2*iw), (yy-0.58*ih)/(0.2*ih)), 0, 1)**1.5
        br = 0.007*math.sin(t*2*math.pi*0.9)
        yy, xx = np.mgrid[0:ih, 0:iw].astype(np.float32); cyb = 0.66*ih
        mapy = (yy-(yy-cyb)*br*_cache['br10']).astype(np.float32); src = cv2.remap(S0, xx, mapy, cv2.INTER_LINEAR)
        z = 1.0+0.035*t/TCUT; cxx = 0.53; cyy = 0.50
        rgb = cam(src, W, H, zoom=z, cx=cxx, cy=cyy); P = lambda x, y: to_px(S0, x, y, W, H, z, cxx, cyy)
        on = ramp(t, 1.3, 1.7)
        Lf = Layer(W, H)
        if on > 0:
            for k in range(36):
                q = k/35; X, Y = P(0.615, 0.355*q); Lf.dot((X, Y), 2.0*s, fill=CYAN, alpha=on*0.9)
        rgb = over(rgb, Lf.get(), shadow=0, glow_amt=1.2)
        X, Y = P(0.61, 0.34); rgb = rgb+radial(W, H, X, Y, 24*s, CYAN, 0.8*on)+radial(W, H, X, Y, 90*s, CYAN, 0.15*on)
        fl = math.exp(-((t-TCUT)/0.12)**2); rgb = rgb+radial(W, H, X, Y, W*0.5, CYAN, 0.9*fl)
        imp = (X, Y)
    else:
        tw = t-TCUT; t_walk = max(0.0, t-(TCUT+0.55))
        v = 0.040*iw                                     # plate px / s
        dxm = -v*t_walk
        src_pts, dsp = _warp_mouse(tw, t_walk, iw, ih)
        x0, x1, y0, y1 = int(0.40*iw), int(1.0*iw), 0, int(0.82*ih)
        gy, gx = np.mgrid[y0:y1:8, x0:x1:8]; grid = np.stack([gx.ravel(), gy.ravel()], 1).astype(np.float64)
        rbf = RBFInterpolator(src_pts+dsp, dsp, kernel='thin_plate_spline', smoothing=1.0)
        D = rbf(grid).reshape(gx.shape+(2,)).astype(np.float32)
        D = cv2.resize(D, (x1-x0, y1-y0), interpolation=cv2.INTER_LINEAR)
        yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
        mx = xx-D[..., 0]-dxm; my = yy-D[..., 1]
        # composite onto the clean cage in the full-plate frame
        fullx = np.mgrid[0:ih, 0:iw][1].astype(np.float32); fully = np.mgrid[0:ih, 0:iw][0].astype(np.float32)
        mapx = fullx-dxm; mapy = fully.copy()
        mapx[y0:y1, x0:x1] = mx; mapy[y0:y1, x0:x1] = my
        mouse = cv2.remap(A, mapx, mapy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
        al = cv2.remap(alpha, mapx, mapy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)[..., None]
        # contact shadow moves with the mouse
        yyp, xxp = np.mgrid[0:ih, 0:iw]
        sh = np.exp(-(((xxp-(0.72*iw+dxm))/(0.20*iw))**2+((yyp-0.725*ih)/(0.022*ih))**2))[..., None]
        bgp = Cn*(1-0.45*sh)
        plate = bgp*(1-al)+mouse*al
        # cut-in framing that follows the walk
        z = 1.32+0.03*tw/3.65; cxx = 0.615+dxm/iw*0.75; cyy = 0.47
        rgb = cam(plate, W, H, zoom=z, cx=cxx, cy=cyy); P = lambda x, y: to_px(A, x, y, W, H, z, cxx, cyy)
        hx = 0.602*iw+dxm; hy = 0.265*ih + (1-ease_out(min(tw/0.6, 1)))*0.035*ih
        X, Y = P(hx/iw, hy/ih)
        fl = math.exp(-((tw)/0.10)**2); rgb = rgb+radial(W, H, X, Y, W*0.5, CYAN, 0.9*fl)
        rgb = rgb+radial(W, H, X, Y, 22*s, CYAN, 0.7)+radial(W, H, X, Y, 80*s, CYAN, 0.12)
        imp = (X, Y)
    # bedding parallax foreground strip
    rgb = over(rgb, drift_specks(W, H, t, 30, 17, (190, 215, 255), 0.25, 1.3, (3, -2)), shadow=0)
    label(L2, imp, (60*s, 96*s), '光纤 + 颅骨植入件', '把蓝光送进下丘脑外侧那群细胞', t=ramp(t, 1.4, 2.1), font_size=LT*s, sub_size=LS*s, accent=CYAN)
    a = ramp(t, 0.2, 0.9)
    L2.rrect((56*s, 612*s, 560*s, 684*s), 6*s, fill=(14, 20, 40), alpha=0.78*a); L2.line([(56*s, 612*s), (56*s, 684*s)], fill=GOLD, width=3*s, alpha=a)
    L2.text((76*s, 642*s), '2007 · 小鼠 · 食欲素神经元', F(SANS_B, 21*s), fill=CREAM, alpha=a, anchor='ls')
    L2.text((76*s, 670*s), '光一开：从睡眠转入清醒的概率升高', F(SANS, 16*s), fill=(176, 186, 212), alpha=a, anchor='ls')
    st = [('睡眠中', (150, 160, 190), 0.0, 1.3), ('光开', CYAN, 1.3, TCUT), ('醒来 · 走动', GOLD, TCUT, 99)]
    for name, col, a0, a1 in st:
        aa = ramp(t, a0, a0+0.25)*(1-ramp(t, a1, a1+0.25)) if a0 > 0 else (1-ramp(t, a1, a1+0.25))
        if aa <= 0: continue
        tw_ = F(SANS_B, 20*s).getlength(name)
        L2.rrect((1200*s-tw_-60*s, 44*s, 1230*s, 88*s), 22*s, fill=(12, 18, 38), alpha=0.8*aa); L2.dot((1200*s-tw_-34*s, 66*s), 7*s, fill=col, alpha=aa)
        L2.text((1200*s-tw_-18*s, 74*s), name, F(SANS_B, 20*s), fill=CREAM, alpha=aa, anchor='ls')
    return grade(over(rgb, L2.get()), seed=int(t*24))
