"""Round 8 (PROMPT 第 8 轮, 18:57): fix only the round-7 independent-review gaps.
1 SF10: one continuous wan3.0 clip (same fibre model throughout), rise at >=1.2 s, orexin-neuron magnifier, light as pulse trains
2 SF08: speed bar says the chemical switch needs the drug first and takes minutes to be in place (narration unchanged);
        leader lines fade with their text; azobenzene tether reattached; its label moved off the ring
3 label system: secondary text >= 20 px at 1280, brighter; main protein name inside the first second
4 SF04/05/07: a causal second beat each; SF07 pushes into the membrane switch
5 SF11: magnifier tied to the fovea; goggles readable (insert of a head wearing them)"""
import sys, os, math; sys.path.insert(0, '/workspace/e2work/v8/tools')
import sf, sf_scenes
from sf_r8 import *          # noqa
from sf_r8 import _cache, vat, vframes, have, chip_seq, family_tex, sf10_clip_t
import sf_r8 as R8, sf_r7 as R7, sf_r6 as R6, sf_r5 as R5

# ------------------------------------------------------------------------------------------------
# 3. label system: every sans text below 20 px (1280 basis) is set at 20 px; greys brightened.
#    F is patched (not only the draw), so text measured for boxes uses the same size.
# ------------------------------------------------------------------------------------------------
_SC = [1.0]
_F0 = sf.F
def F2(path, size, idx=2):
    s = _SC[0]
    if path in (sf.SANS, sf.SANS_B) and 9*s < size < 20*s-0.01: size = 20*s
    return _F0(path, size, idx)
BRIGHT = (218, 224, 242)
_DIM = {(176, 186, 212), (150, 162, 190), (190, 198, 222), (170, 170, 180), (150, 156, 200), (150, 160, 190)}
_text0 = sf.Layer.text
def text2(self, xy, txt, font, fill=CREAM, alpha=1.0, anchor='la', tracking=0):
    if alpha <= 0.004 or not txt: return          # PIL replaces RGBA pixels: invisible text would punch holes in panels
    if tuple(fill) in _DIM: fill = BRIGHT
    return _text0(self, xy, txt, font, fill=fill, alpha=alpha, anchor=anchor, tracking=tracking)
sf.Layer.text = text2

def label2(L, anchor_pt, text_pt, title, sub=None, color=CREAM, t=1.0, font_size=22, sub_size=15, accent=CYAN):
    """leader-line label; the leader fades with the text (no orphan lines) and the plate is darker"""
    if t <= 0: return
    s = L.W/1280; font_size = max(font_size, 22*s); sub_size = max(sub_size, 20*s)
    ax, ay = anchor_pt; tx, ty = text_pt; k = ease_out(min(t*1.6, 1)); la = min(1, t*2.2)
    L.ring((ax, ay), 5*s*k, fill=accent, width=1.6*s, alpha=la); L.dot((ax, ay), 2.4*s, fill=accent, alpha=k*la)
    mx, my = ax+(tx-ax)*k, ay+(ty-ay)*k; L.line([(ax, ay), (mx, my)], fill=color, width=1.3*s, alpha=0.9*la)
    ta = ramp(t, 0.45, 1.0)
    if ta > 0:
        right = tx < L.W*0.5
        x0 = tx+(14*s if right else -14*s); an = 'l' if right else 'r'
        tw = max(F2(SANS_B, font_size).getlength(title), F2(SANS, sub_size).getlength(sub) if sub else 0)
        bx0, bx1 = (x0-10*s, x0+tw+10*s) if right else (x0-tw-10*s, x0+10*s)
        L.rrect((bx0, ty-font_size-10*s, bx1, ty+(sub_size+16*s if sub else 9*s)), 6*s, fill=(11, 16, 34), alpha=0.72*ta)
        L.text((x0, ty-2*s), title, F2(SANS_B, font_size), fill=color, alpha=ta, anchor=an+'s')
        if sub: L.text((x0, ty+7*s), sub, F2(SANS, sub_size), fill=BRIGHT, alpha=ta, anchor=an+'t')

for _m in list(sys.modules.values()):
    if _m is None or not getattr(_m, '__file__', '') or '/e2work/v8/tools/' not in (_m.__file__ or ''): continue
    if getattr(_m, 'F', None) is _F0: _m.F = F2
    if getattr(_m, 'label', None) is sf.label: _m.label = label2
    if hasattr(_m, 'LT'): _m.LT = 22
    if hasattr(_m, 'LS'): _m.LS = 20
F = F2; label = label2; LT, LS = 22, 20

# ================================================================================================
# 1. SF10: one wan3.0 clip (sleep -> eyes -> rise -> walk) from the sleep plate; fibre identical throughout
#    clip map: 0-2.8 asleep | 2.8-3.3 time skip (dissolve to the same closed-eye pose at 4.95) |
#              3.3-5.0 rise (clip 5.0-6.1 at 0.65x, ~1.7 s) | 5.0-8.9 walk (clip 6.1-10.0, 1:1)
# ================================================================================================
CL10 = 'sf10_r8_one'; SF10_D = 8.9
def c10(t):
    if t < 3.05: return [(t*0.78, 1.0)]                 # asleep (clip 0-2.38, before its eyes open at ~2.8)       # time skip = dip to dark and cut (no ghosting dissolve)
    if t < 3.3: return [(4.95, 1.0)]
    if t < 5.0: return [(4.95+(t-3.3)*0.65, 1.0)]
    return [(6.055+(t-5.0), 1.0)]

def _trk10():
    if 'trk10r8' in _cache: return _cache['trk10r8']
    fr, fps = vframes(CL10, None)
    ih, iw = fr[0].shape[:2]
    g = [cv2.cvtColor((f*255).astype(np.uint8), cv2.COLOR_RGB2GRAY) for f in fr]
    x, y = int(0.613*iw), int(0.338*ih); r = max(10, int(iw*0.022)); pos = []
    tpl = g[0][y-r:y+r, x-r:x+r]
    for k in range(len(g)):
        sw = int(r*2.5); x0, y0 = max(0, x-sw), max(0, y-sw); win = g[k][y0:y+sw, x0:x+sw]
        res = cv2.matchTemplate(win, tpl, cv2.TM_CCOEFF_NORMED); _, _, _, ml = cv2.minMaxLoc(res)
        x, y = x0+ml[0]+r, y0+ml[1]+r; pos.append((x/iw, y/ih))
        if k % 3 == 0: tpl = g[k][y-r:y+r, x-r:x+r]
    pos = np.array(pos); pos = np.stack([cv2.GaussianBlur(pos[:, i].reshape(-1, 1), (1, 0), 2).ravel() for i in (0, 1)], 1)
    _cache['trk10r8'] = (pos, fps, iw, ih); return _cache['trk10r8']

def _vframes_native(name):
    k = ('vn', name)
    if k not in _cache:
        cap = cv2.VideoCapture(R7.GV+name+'.mp4'); fr = []; fps = cap.get(cv2.CAP_PROP_FPS) or 30
        while True:
            ok, f = cap.read()
            if not ok: break
            fr.append(cv2.cvtColor(f, cv2.COLOR_BGR2RGB).astype(np.float32)/255)
        _cache[k] = (fr, fps)
    return _cache[k]
def vframes(name, size):       # noqa: size None = native
    return _vframes_native(name) if size is None else R7.vframes(name, size)

def frame10(ct):
    fr, fps = _vframes_native(CL10); x = min(max(ct*fps, 0), len(fr)-1.001); i = int(x); a = x-i
    return fr[i]*(1-a)+fr[min(i+1, len(fr)-1)]*a

def pulses(t, t0, t1, hz=5.0, on=0.06):
    """visible pulse train (the real trains are 15 ms pulses at 5-30 Hz, ~10 s per train; shown slowed)"""
    if t < t0 or t > t1: return 0.0
    ph = ((t-t0)*hz) % 1.0
    return 1.0 if ph < on*hz else math.exp(-((ph-on*hz)/0.12))*0.6

@scene('SF10_mouse_tripo', SF10_D)
def sf10(t, W, H):
    s = W/1280
    parts = c10(t); frame = sum(frame10(ct)*w for ct, w in parts)
    ih, iw = frame.shape[:2]
    z = 1.04+0.05*lin(t, SF10_D); cxx = 0.55-0.05*lin(t, SF10_D); cyy = 0.50
    rgb = cam(frame, W, H, zoom=z, cx=cxx, cy=cyy)
    P = lambda x, y: to_px(frame, x, y, W, H, z, cxx, cyy)
    pos, fps, _, _ = _trk10()
    fx = sum(pos[min(int(ct*fps), len(pos)-1)][0]*w for ct, w in parts); fy = sum(pos[min(int(ct*fps), len(pos)-1)][1]*w for ct, w in parts)
    X, Y = P(fx, fy)
    # light = trains of pulses (train 1 while asleep, train 2 at the time skip); the fibre itself never changes
    pl = max(pulses(t, 1.0, 2.75), pulses(t, 3.35, 4.6))
    if pl > 0:
        Lf = Layer(W, H); topx, _ = P(fx, 0)
        Lf.line([(topx, -5), (X, Y-6*s)], fill=CYAN, width=2.6*s, alpha=0.85*pl)
        rgb = over(rgb, Lf.get(), shadow=0, glow_amt=1.4)
        rgb = rgb+radial(W, H, X, Y, 12*s, (200, 235, 255), 0.95*pl)+radial(W, H, X, Y, 60*s, CYAN, 0.22*pl)
    rgb = over(rgb, drift_specks(W, H, t, 26, 17, (190, 215, 255), 0.2, 1.3, (3, -2)), shadow=0)
    dip = math.exp(-((t-3.05)/0.13)**2); rgb = rgb*(1-0.85*dip)
    sk = ramp(t, 2.6, 2.85)*(1-ramp(t, 3.45, 3.7))
    if sk > 0:
        yy, xx = np.mgrid[0:H, 0:W]
        rgb = rgb*(1-0.2*sk*np.clip(np.abs(xx/W-0.5)*2, 0, 1)[..., None])
    # magnifier: the lateral hypothalamus under the fibre — the orexin neurons that carry the channel
    L = Layer(W, H); C = (1100*s, 250*s); R = int(138*s)
    a = ramp(t, 0.5, 1.2)*(1-ramp(t, 2.9, 3.3))
    if a > 0:
        k = ease_out(ramp(t, 0.5, 1.2)); hx, hy = X, Y+38*s             # point just under the implant
        px, py = hx+(C[0]-hx)*k, hy+(C[1]-hy)*k; r = max(2, int(R*k))
        L.ring((hx, hy), 9*s, fill=CYAN, width=1.8*s, alpha=a)
        ang = math.atan2(hy-py, hx-px)
        for sg in (-1, 1): L.line([(hx, hy), (px+r*math.cos(ang+sg*0.55), py+r*math.sin(ang+sg*0.55))], fill=CYAN, width=1.4*s, alpha=0.75*a)
        L.dot((px, py), r+6*s, fill=(8, 10, 24), alpha=0.92*a)
        L.paste(circ_img(img('sf10_orexin'), r, zoom=1.15+0.05*lin(t, 3), cx=0.5, cy=0.47), (px-r, py-r), alpha=a)
        L.ring((px, py), r, fill=CYAN, width=2.4*s, alpha=a)
    rgb = over(rgb, L.get(), shadow=0.35)
    if a > 0:
        # each pulse lands on the orexin cluster: it fires in step with the light
        rgb = rgb+radial(W, H, C[0], C[1]-6*s, 70*s, CYAN, 0.5*pl*a)+radial(W, H, C[0], C[1]-R*0.9, 26*s, (210, 240, 255), 0.5*pl*a)
    L2 = Layer(W, H)
    if a > 0:
        L2.text((C[0], C[1]+R+34*s), '下丘脑外侧 · 食欲素神经元', F(SANS_B, 22*s), fill=CREAM, alpha=a*ramp(t, 0.9, 1.4), anchor='ms')
        L2.text((C[0], C[1]+R+62*s), '膜上装了光控通道，随光脉冲放电', F(SANS, 20*s), fill=BRIGHT, alpha=a*ramp(t, 1.2, 1.7), anchor='ms')
    # pulse-train glyph (top left): the light comes as trains of brief pulses, not a steady beam
    ga = ramp(t, 0.9, 1.3)*(1-ramp(t, 4.6, 5.0))
    if ga > 0:
        gx, gy = 60*s, 60*s
        L2.rrect((gx, gy, gx+430*s, gy+92*s), 8*s, fill=(12, 18, 38), alpha=0.86*ga)
        L2.line([(gx, gy), (gx, gy+92*s)], fill=CYAN, width=3*s, alpha=ga)
        L2.text((gx+20*s, gy+32*s), '蓝光：一串串短脉冲', F(SANS_B, 22*s), fill=CREAM, alpha=ga, anchor='ls')
        bx = gx+20*s; by = gy+76*s
        L2.line([(bx, by), (bx+390*s, by)], fill=(120, 140, 190), width=1.2*s, alpha=ga)
        for j in range(16):
            x = bx+6*s+j*24*s; lit = 1.0 if (t*5.0 % 16) > j else 0.35
            L2.rrect((x, by-22*s, x+7*s, by), 1.5*s, fill=CYAN, alpha=ga*lit)
        L2.text((bx+390*s, by-30*s+0*s), '', F(SANS, 20*s), alpha=0)
    if sk > 0:
        cx_, cy_ = W*0.36, 112*s+120*s; txt = '几十秒后'; tw = F(SANS_B, 24*s).getlength(txt)
        L2.rrect((cx_-tw/2-62*s, cy_-34*s, cx_+tw/2+26*s, cy_+16*s), 25*s, fill=(12, 18, 38), alpha=0.88*sk)
        for j in range(2):
            x0 = cx_-tw/2-50*s+j*16*s; aj = sk*(0.55+0.45*math.sin(t*12-j*1.5))
            L2.d.polygon([((x0)*2, (cy_-22*s)*2), ((x0+15*s)*2, (cy_-9*s)*2), ((x0)*2, (cy_+4*s)*2)], fill=(*CYAN, int(255*aj)))
        L2.text((cx_-tw/2+4*s, cy_-1*s), txt, F(SANS_B, 24*s), fill=CREAM, alpha=sk, anchor='ls')
        L2.text((cx_, cy_+42*s), '光脉冲串反复给', F(SANS, 20*s), fill=BRIGHT, alpha=sk, anchor='ms')
    ab = ramp(t, 0.2, 0.9)
    L2.rrect((56*s, 604*s, 640*s, 684*s), 6*s, fill=(14, 20, 40), alpha=0.82*ab); L2.line([(56*s, 604*s), (56*s, 684*s)], fill=GOLD, width=3*s, alpha=ab)
    L2.text((76*s, 638*s), '2007 · 小鼠 · 食欲素神经元', F(SANS_B, 22*s), fill=CREAM, alpha=ab, anchor='ls')
    L2.text((76*s, 670*s), '光脉冲一来：从睡眠转入清醒的概率升高', F(SANS, 20*s), fill=BRIGHT, alpha=ab, anchor='ls')
    chip_seq(L2, t, [('睡眠中', (150, 160, 190), 0.0, 3.4), ('醒来', GOLD, 3.4, 5.0), ('醒来后走动', GOLD, 5.0, 99)], s, y=620)
    return grade(over(rgb, L2.get()), seed=int(t*24))

# ================================================================================================
# 2. SF08: speed bar fixed (chemical switch = drug first, minutes before it is in place); leader lines fade
#    with text; azobenzene tether reattached; label clear of the ring.  Narration is NOT changed.
# ================================================================================================
from sf_r5 import azo_sprite, MAG, MAG_O
@scene('SF08_early_attempts', 7.0)
def sf08(t, W, H):
    im = img('sf08e_relay'); s = W/1280
    pan = ease(ramp(t, 3.3, 4.5)); u = lin(t, 7)
    z = 1.52+0.04*u; cxx = 0.335+(0.672-0.335)*pan+0.006*u; cyy = 0.43
    rgb = cam(im, W, H, zoom=z, cx=cxx, cy=cyy)
    P = lambda x, y: to_px(im, x, y, W, H, z, cxx, cyy)
    path = [(0.115, 0.40), (0.23, 0.52), (0.41, 0.50), (0.585, 0.47)]
    uu = ramp(t, 0.7, 2.6)*(len(path)-1); i = min(int(uu), len(path)-2); f = uu-i
    if 0 < uu and t < 2.75:
        px = path[i][0]+(path[i+1][0]-path[i][0])*f; py = path[i][1]+(path[i+1][1]-path[i][1])*f
        X, Y = P(px, py); rgb = rgb+radial(W, H, X, Y, W*0.014, (255, 226, 176), 0.9)+radial(W, H, X, Y, W*0.05, (255, 226, 176), 0.15)
    X, Y = P(0.11, 0.30); rgb = rgb+radial(W, H, X, Y, W*0.03, CYAN, 0.6*math.exp(-((t-0.55)/0.3)**2))
    openA = ramp(t, 2.6, 3.0)*(1-ramp(t, 3.4, 3.9)); X, Y = P(0.585, 0.49); rgb = rgb+radial(W, H, X, Y, W*0.025, (255, 209, 102), 0.3*openA)
    L = Layer(W, H)
    free = [(0.775, 0.085, 20), (0.92, 0.075, -25), (0.87, 0.20, 40), (0.965, 0.25, 10), (0.70, 0.18, -15)]
    for j, (fx, fy, ang) in enumerate(free):
        X, Y = P(fx+0.006*math.sin(t*0.7+j), fy+0.02*u+0.004*math.sin(t*0.9+j*2))
        spr = azo_sprite(0, 104*s, ang+8*math.sin(t*0.5+j)); L.paste(spr, (X-spr.size[0]/2, Y-spr.size[1]/2), alpha=0.85)
    hit = ramp(t, 4.7, 5.0); bend = ease(ramp(t, 4.95, 5.35))
    TX, TY = P(0.82, 0.345)
    spr = azo_sprite(round(bend*20)/20, 120*s, -12)
    # tether: from the channel's top to the sprite's lower-left ring, ends meet the drawn atoms
    sa = np.asarray(spr)[..., 3]; ys, xs = np.nonzero(sa > 120)
    lx = xs.min(); ly = ys[xs < lx+sa.shape[1]*0.12].mean() if len(xs) else sa.shape[0]/2
    end = (TX-spr.size[0]/2+lx+4*s, TY-spr.size[1]/2+ly)
    L.line([P(0.808, 0.395), end], fill=MAG_O, width=5*s); L.line([P(0.808, 0.395), end], fill=MAG, width=3*s)
    L.dot(end, 4*s, fill=MAG)
    L.paste(spr, (TX-spr.size[0]/2, TY-spr.size[1]/2))
    rgb = over(rgb, L.get(), shadow=0.35)
    if t > 4.3:
        Lp = Layer(W, H); sx, sy = TX+150*s, TY-200*s; k = ramp(t, 4.3, 4.75); pts = []
        for q in np.linspace(0, k, 60):
            x = sx+(TX-sx)*q; y = sy+(TY-sy)*q
            pts.append((x+0.8*7*s*math.sin(q*40), y-0.6*7*s*math.sin(q*40)))
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
    L = Layer(W, H); b1 = 1-ramp(t, 3.15, 3.45); b2 = ramp(t, 4.3, 4.6)
    def chip(txt, col, a):
        if a <= 0: return
        tw = F(SANS_B, 22*s).getlength(txt)+44*s
        L.rrect((40*s, 30*s, 40*s+tw, 76*s), 23*s, fill=(12, 18, 38), alpha=0.86*a); L.dot((62*s, 53*s), 6*s, fill=col, alpha=a)
        L.text((78*s, 61*s), txt, F(SANS_B, 22*s), fill=CREAM, alpha=a, anchor='ls')
    chip('路线一 · 好几步信号接力', (255, 226, 176), ramp(t, 0.1, 0.6)*b1)
    chip('路线二 · 通道上外加化学光开关', MAG, b2)
    if b1 > 0:
        steps = [((0.115, 0.36), '① 感光蛋白先接住光', None, (330, 160)), ((0.235, 0.57), '② 中间好几步接力', '一级传一级', (330, 640)), ((0.585, 0.36), '③ 通道最后才打开', None, (1010, 160))]
        for j, ((ax, ay), ti, sub, tp) in enumerate(steps):
            a = ramp(t, 0.5+j*0.85, 1.2+j*0.85)*b1; X, Y = P(ax, ay)
            label(L, (X, Y), (tp[0]*s, tp[1]*s), ti, sub, t=a, font_size=LT*s, sub_size=LS*s, accent=(255, 226, 176) if j < 2 else (255, 209, 102))
        X, Y = P(0.60, 0.62); label(L, (X, Y), (760*s, 600*s), '离子', '通道一开就流进细胞', t=ramp(t, 2.5, 2.8)*b1, font_size=LT*s, sub_size=LS*s, accent=(255, 209, 102))
    if b2 > 0:
        # anchor on the azobenzene's top edge; text sits above-right, clear of the rings
        label(L, (TX+10*s, TY-spr.size[1]*0.32), (1225*s, 150*s), '合成光开关（偶氮苯）', '要另外把化学分子送进组织', t=ramp(t, 4.0, 4.8), font_size=LT*s, sub_size=LS*s, accent=MAG)
        X, Y = P(0.84, 0.58); label(L, (X, Y), (1225*s, 430*s), '受紫光弯折 → 通道打开', None, t=ramp(t, 5.4, 6.0), font_size=LT*s, accent=(255, 209, 102))
    # how long until each switch can be used: log time axis 1 ms ... 10 min
    a = ramp(t, 4.5, 5.0)
    if a > 0:
        bx, by, bw, bh = 40*s, 516*s, 700*s, 184*s
        L.rrect((bx, by, bx+bw, by+bh), 8*s, fill=(12, 18, 38), alpha=0.9*a)
        x0, x1 = bx+34*s, bx+bw-40*s; ay_ = by+bh-46*s
        L.line([(x0, ay_), (x1, ay_)], fill=(150, 160, 190), width=1.4*s, alpha=a)
        ticks = [(0.0, '1 ms'), (0.4, '1 s'), (0.71, '1 分钟'), (1.0, '10 分钟')]   # log10 seconds: -3, 0, 1.78, 2.78 over 5.78
        for q, tk in ticks:
            x = x0+(x1-x0)*q; L.line([(x, ay_-5*s), (x, ay_+5*s)], fill=(150, 160, 190), width=1.4*s, alpha=a)
            L.text((x, ay_+30*s), tk, F(SANS, 20*s), fill=BRIGHT, alpha=a, anchor='ms')
        L.rrect((x0-5*s, ay_-16*s, x0+(x1-x0)*0.06, ay_-5*s), 4*s, fill=CYAN, alpha=a)
        L.text((x0-5*s, ay_-26*s), '需要：毫秒级', F(SANS_B, 20*s), fill=(130, 200, 255), alpha=a, anchor='ls')
        g = ease_out(ramp(t, 4.6, 5.3)); xa0, xa1 = x0+(x1-x0)*0.36, x0+(x1-x0)*0.52
        L.rrect((xa0, ay_-16*s, xa0+(xa1-xa0)*g, ay_-5*s), 4*s, fill=(255, 180, 120), alpha=a)
        L.text((xa0-6*s, ay_-26*s), '多步接力：秒级', F(SANS_B, 20*s), fill=(255, 200, 150), alpha=a, anchor='ls')
        c = ramp(t, 5.7, 6.2); xc0, xc1 = x0+(x1-x0)*0.66, x0+(x1-x0)*0.98; yb = ay_-74*s
        L.rrect((xc0, yb-11*s, xc0+(xc1-xc0)*ease_out(c), yb), 4*s, fill=MAG, alpha=a*c)
        L.text((xc1, yb-20*s), '化学开关：要先给药，几分钟才就位', F(SANS_B, 20*s), fill=(245, 170, 225), alpha=a*c, anchor='rs')
    return grade(over(rgb, L.get()), seed=int(t*24))

# ================================================================================================
# SF09: main protein named inside the first second (was 2.4 s); everything else as round 7
# ================================================================================================
_sf09_src = open('/workspace/e2work/v8/tools/sf_r8.py').read()
_a = _sf09_src.index("@scene('SF09_chr2_channel'"); _sf09_src = _sf09_src[_a:]
_sf09_src = _sf09_src.replace("t=ramp(t, 1.9, 2.7), font_size=LT*s, sub_size=LS*s, accent=(99, 199, 168)", "t=ramp(t, 0.2, 0.9), font_size=LT*s, sub_size=LS*s, accent=(99, 199, 168)")
_sf09_src = _sf09_src.replace("'蓝光 约 470 nm', None, t=ramp(t, 0.4, 1.1)", "'蓝光 约 470 nm', None, t=ramp(t, 0.6, 1.2)")
from sf_r6 import ret_sprite
import mol
exec(compile(_sf09_src, 'sf_r9_sf09', 'exec'), globals())

# ================================================================================================
# 4a. SF04: second beat with a cause: the light he imagined travels on from the word 光 to a neuron, which fires
# ================================================================================================
_sf04_r6 = R6.S['SF04_crick_quote'][0]
@scene('SF04_crick_quote', 5.0)
def sf04(t, W, H):
    s = W/1280; u = lin(t, 5)
    rgb = _sf04_r6(t, W, H)
    lum = rgb.mean(2, keepdims=True); dark = np.clip((0.22-lum)/0.12, 0, 1)
    rgb = rgb+family_tex(W, H)*0.22*dark*ramp(t, 0, 1.0)
    f = F(SERIF_B, 46*s); x0 = 690*s+f.getlength('“理想的信号会是'); w = f.getlength('光'); gx, gy = x0+w/2, 302*s
    gl = ramp(t, 1.8, 2.4)*(0.75+0.25*math.sin(t*3.2))
    rgb = rgb+radial(W, H, gx, gy, 34*s, CYAN, 0.55*gl)
    # neuron vignette lower right (family neuron plate)
    NC = (1160*s, 150*s); NR = int(80*s); na = ramp(t, 2.3, 2.9)
    L = Layer(W, H)
    if na > 0:
        L.dot(NC, NR+5*s, fill=(8, 10, 24), alpha=0.9*na)
        L.paste(circ_img(img('sf06t_neuron'), NR, zoom=2.2, cx=0.70, cy=0.52), (NC[0]-NR, NC[1]-NR), alpha=na)
        L.ring(NC, NR, fill=(130, 150, 200), width=2*s, alpha=na)
    # light packet travels from 光 to the neuron
    k = ramp(t, 2.9, 3.6)
    if 0 < k < 1:
        pts = [(gx+20*s+(NC[0]-NR*0.5-gx-20*s)*q, gy-30*s+(NC[1]+NR*0.6-gy+30*s)*q) for q in np.linspace(max(0, k-0.25), k, 12)]
        L.line(pts, fill=(170, 220, 255), width=3*s, alpha=0.9)
    rgb = over(rgb, L.get(), shadow=0.3, glow_amt=0.8)
    fire = ramp(t, 3.55, 3.75)
    if fire > 0:
        ring = (1-ramp(t, 3.6, 4.6))
        Lr = Layer(W, H); Lr.ring(NC, NR+(6+40*ramp(t, 3.6, 4.6))*s, fill=CYAN, width=2.5*s, alpha=0.8*ring); Lr.ring(NC, NR, fill=CYAN, width=2.4*s, alpha=fire)
        rgb = over(rgb, Lr.get(), shadow=0, glow_amt=1.0)
        rgb = rgb+radial(W, H, NC[0]-10*s, NC[1], 60*s, CYAN, 0.5*fire*(0.7+0.3*math.sin(t*9)))
    L2 = Layer(W, H); ta = ramp(t, 3.7, 4.2)
    tw_ = F(SANS_B, 20*s).getlength('设想：光一照，神经元就放电')
    L2.rrect((NC[0]-NR-30*s-tw_, NC[1]-22*s, NC[0]-NR-8*s, NC[1]+16*s), 6*s, fill=(11, 16, 34), alpha=0.7*ta)
    L2.text((NC[0]-NR-18*s, NC[1]+5*s), '设想：光一照，神经元就放电', F(SANS_B, 20*s), fill=CREAM, alpha=ta, anchor='rs')
    rgb = over(rgb, L2.get(), shadow=0.4)
    rgb = cam(np.clip(rgb, 0, 1), W, H, zoom=1.0+0.07*ease(u)+0.01*u, cx=0.5+0.015*u, cy=0.5-0.01*u)
    return np.clip(rgb, 0, 1)

# ================================================================================================
# 4b. SF05: no empty open (the channel icon flies in to the citation); second half: the channel opens
#     (ions through it) and a light sweep passes over the three laureates in turn
# ================================================================================================
_sf05_r5 = R5.S['SF05_nobel_portraits'][0]
@scene('SF05_nobel_portraits', 5.0)
def sf05(t, W, H):
    s = W/1280; u = lin(t, 5)
    rgb = _sf05_r5(t, W, H)
    lum = rgb.mean(2, keepdims=True); dark = np.clip((0.22-lum)/0.12, 0, 1)
    rgb = rgb+family_tex(W, H)*0.2*dark
    f = F(SERIF, 20*s); tw = f.getlength('获奖理由：发现光控离子通道，并由此建立光遗传学')
    bx, by = W/2-tw/2-46*s, 111*s
    # 0-0.9: big channel at centre, flying to its badge place
    k = ease(ramp(t, 0.35, 1.1)); grow = ease(ramp(t, 3.0, 3.5))*(1-ease(ramp(t, 4.5, 4.95)))
    cx_, cy_ = W/2+(bx-W/2)*k, 360*s+(by-360*s)*k; r = int((150-122*k)*s+18*s*grow)
    L = Layer(W, H)
    L.dot((cx_, cy_), r+4*s, fill=(8, 10, 24), alpha=0.92)
    L.paste(circ_img(img('sf09e_chr2'), r, zoom=2.2, cx=0.49, cy=0.47), (cx_-r, cy_-r))
    L.ring((cx_, cy_), r, fill=CYAN, width=2*s)
    rgb = over(rgb, L.get(), shadow=0.3)
    if grow > 0.2:    # the channel opens: ions stream through both pores
        Li = Layer(W, H)
        for j, px in enumerate((-0.17, 0.12)):
            for n in range(6):
                p = (t*0.8+n/6+j*0.5) % 1.0; Li.dot((cx_+px*r, cy_-r*0.75+p*r*1.5), 3.2*s, fill=(255, 209, 102), alpha=grow*min(1, p*6)*min(1, (1-p)*6))
        rgb = over(rgb, Li.get(), shadow=0, glow_amt=0.7)
        rgb = rgb+radial(W, H, cx_, cy_-r*0.8, r*0.6, CYAN, 0.25*grow)
    # underline + light sweep over the three laureates (left to right) once the channel is open
    x0 = W/2-tw/2+f.getlength('获奖理由：发现'); x1 = x0+f.getlength('光控离子通道')
    Lu = Layer(W, H); kk = ease_out(ramp(t, 1.2, 1.8)); Lu.line([(x0, 126*s), (x0+(x1-x0)*kk, 126*s)], fill=CYAN, width=2*s, alpha=0.9*ramp(t, 1.2, 1.4))
    rgb = over(rgb, Lu.get(), shadow=0, glow_amt=0.8)
    for j, px in enumerate((0.30, 0.50, 0.70)):
        b = math.exp(-((t-(3.5+j*0.35))/0.3)**2)
        rgb = rgb+radial(W, H, px*W, 330*s, 150*s, (120, 190, 255), 0.18*b)
    zz = 1.0+0.05*ease(u)+0.01*u; rgb = cam(np.clip(rgb, 0, 1), W, H, zoom=zz, cx=0.5, cy=0.5+0.5*(1-1/zz)*0.6)
    return np.clip(rgb, 0, 1)

# ================================================================================================
# 4c. SF07: the fibre's light reaches the lit cluster; a magnifier pushes onto one neuron's membrane and
#     shows the switch (ChR2) opening; the tagline 'this switch' points at it.  Different from SF01's card.
# ================================================================================================
_sf07_src = open('/workspace/e2work/v8/tools/sf_r8.py').read()
_a = _sf07_src.index("@scene('SF07_main_title'"); _b = _sf07_src.index("# ====", _a); _sf07_src = _sf07_src[_a:_b]
_sf07_src = _sf07_src.replace("def sf07(t, W, H):", "def _sf07_base(t, W, H):").replace("@scene('SF07_main_title', 5.0)\n", "")
_sf07_src = _sf07_src.replace("    L = Layer(W, H)\n    a = ramp(t, 1.0, 2.2)", "    _cache['sf07_tip'] = (fx, fbot)\n    L = Layer(W, H)\n    a = ramp(t, 2.4, 3.4)")
_sf07_src = _sf07_src.replace("'光遗传学', F(SERIF_B, 108*s)", "'光遗传学', F(SERIF_B, 96*s)").replace("ramp(t, 1.0, 3.2)", "ramp(t, 2.4, 4.2)")
_sf07_src = _sf07_src.replace("alpha=ramp(t, 2.0, 2.8), anchor='ms', tracking=4*s)", "alpha=ramp(t, 3.0, 3.6), anchor='ms', tracking=4*s)")
_sf07_src = _sf07_src.replace("'这一期，就讲这枚开关', F(SANS, 22*s), fill=(190, 198, 222), alpha=ramp(t, 2.6, 3.4)", "'', F(SANS, 22*s), fill=(190, 198, 222), alpha=0")
exec(compile(_sf07_src, 'sf_r9_sf07', 'exec'), globals())
@scene('SF07_main_title', 5.0)
def sf07(t, W, H):
    s = W/1280; rgb = _sf07_base(t, W, H); fx, fbot = _cache['sf07_tip']
    C = (990*s, 300*s); R = int(150*s); a = ramp(t, 0.9, 1.7)
    L = Layer(W, H); hx, hy = fx, fbot+14*s
    if a > 0:
        k = ease_out(a); px, py = hx+(C[0]-hx)*k, hy+(C[1]-hy)*k; r = max(2, int(R*k))
        L.ring((hx, hy), 10*s, fill=CYAN, width=1.8*s, alpha=a)
        ang = math.atan2(hy-py, hx-px)
        for sg in (-1, 1): L.line([(hx, hy), (px+r*math.cos(ang+sg*0.55), py+r*math.sin(ang+sg*0.55))], fill=CYAN, width=1.3*s, alpha=0.75*a)
        L.dot((px, py), r+6*s, fill=(8, 10, 24), alpha=0.92*a)
        zin = 1.0+1.3*ease(ramp(t, 1.2, 2.6))            # push from the neuron cluster onto its membrane switch
        L.paste(circ_img(img('sf10_orexin'), r, zoom=1.2+0.8*ease(ramp(t, 1.2, 2.0)), cx=0.47, cy=0.42), (px-r, py-r), alpha=a*(1-ease(ramp(t, 1.7, 2.2))))
        L.paste(circ_img(img('sf09e_chr2'), r, zoom=1.6+0.5*ease(ramp(t, 1.7, 4.5)), cx=0.49, cy=0.46), (px-r, py-r), alpha=a*ease(ramp(t, 1.7, 2.2)))
        L.ring((px, py), r, fill=CYAN, width=2.4*s, alpha=a)
    rgb = over(rgb, L.get(), shadow=0.35)
    op = ramp(t, 2.5, 2.9)
    if op > 0:      # the switch opens with each light pulse: ions through both pores
        Li = Layer(W, H)
        for j, px in enumerate((-0.13, 0.10)):
            for n in range(7):
                p = (t*0.7+n/7+j*0.5) % 1.0; Li.dot((C[0]+px*R, C[1]-R*0.7+p*R*1.4), 4*s, fill=(255, 209, 102), alpha=op*min(1, p*6)*min(1, (1-p)*6))
        rgb = over(rgb, Li.get(), shadow=0, glow_amt=0.7)
        rgb = rgb+radial(W, H, C[0], C[1]-R*0.75, 70*s, CYAN, 0.25*op*(0.8+0.2*math.sin(t*6)))
    L2 = Layer(W, H); ta = ramp(t, 3.4, 4.0)
    L2.text((C[0], C[1]+R+36*s), '这一期，就讲这枚开关', F(SANS_B, 24*s), fill=CREAM, alpha=ta, anchor='ms', tracking=2*s)
    L2.text((C[0], C[1]+R+66*s), '神经元膜上的光控通道', F(SANS, 20*s), fill=BRIGHT, alpha=ramp(t, 3.7, 4.3), anchor='ms')
    return over(rgb, L2.get(), shadow=0.45)

# ================================================================================================
# 5. SF11: magnifier sits by the fovea with a filled cone from the fovea; goggles shown as a readable insert
# ================================================================================================
_sf11_src = open('/workspace/e2work/v8/tools/sf_r8.py').read()
_a = _sf11_src.index("EYE7 = "); _b = _sf11_src.index("# ====", _sf11_src.index("def sf11")); _sf11_src = _sf11_src[_a:_b]
_sf11_src = _sf11_src.replace("C = (300*s, 515*s); R = int(152*s)", "C = (1010*s, 545*s); R = int(140*s)")
_sf11_src = _sf11_src.replace("for sg in (-1, 1): L.line([(FX, FY), (px+r*math.cos(ang+sg*0.6), py+r*math.sin(ang+sg*0.6))], fill=AMBER, width=1.1*s, alpha=0.6*a)",
    "e1 = (px+r*math.cos(ang+0.75), py+r*math.sin(ang+0.75)); e2 = (px+r*math.cos(ang-0.75), py+r*math.sin(ang-0.75))\n"
    "        L.d.polygon([(FX*2, FY*2), (e1[0]*2, e1[1]*2), (e2[0]*2, e2[1]*2)], fill=(255, 190, 90, int(46*a)))\n"
    "        for e in (e1, e2): L.line([(FX, FY), e], fill=AMBER, width=1.8*s, alpha=0.9*a)")
_sf11_src = _sf11_src.replace("label(L2, (X, Y), (60*s, 96*s), '护目镜', '把外界明暗换成琥珀色光脉冲', t=ramp(t, 0.3, 1.1), font_size=LT*s, sub_size=LS*s, accent=AMBER)", "pass")
_sf11_src = _sf11_src.replace("(560*s, 70*s), '角膜、晶状体把光折向中央凹'", "(640*s, 60*s), '角膜、晶状体把光折向中央凹'")
_sf11_src = _sf11_src.replace("(520*s, 448*s), '神经节细胞：膜上装了 ChrimsonR'", "(760*s, 440*s), '神经节细胞：膜上装了 ChrimsonR'")
_sf11_src = _sf11_src.replace("(520*s, 640*s), '感光细胞：已大量丢失'", "(760*s, 660*s), '感光细胞：已大量丢失'")
_sf11_src = _sf11_src.replace("def sf11(t, W, H):", "def _sf11_base(t, W, H):").replace("@scene('SF11_eye_goggles', 5.0)\n", "")
exec(compile(_sf11_src, 'sf_r9_sf11', 'exec'), globals())
@scene('SF11_eye_goggles', 5.0)
def sf11(t, W, H):
    s = W/1280; rgb = _sf11_base(t, W, H)
    # goggles insert, top-left: a head wearing the goggles, its amber beam lines up with the beam into the eye
    C = (150*s, 150*s); R = int(112*s); a = ramp(t, 0.1, 0.7)
    L = Layer(W, H)
    L.dot(C, R+6*s, fill=(8, 10, 24), alpha=0.92*a)
    L.paste(circ_img(img('sf11_goggles'), R, zoom=1.7, cx=0.32, cy=0.44), (C[0]-R, C[1]-R), alpha=a)
    L.ring(C, R, fill=AMBER, width=2.4*s, alpha=a)
    rgb = over(rgb, L.get(), shadow=0.35)
    pl = ramp(t, 0.6, 0.9)*(0.6+0.4*math.sin(t*7.5)**2)
    rgb = rgb+radial(W, H, C[0]+8*s, C[1]+2*s, 14*s, (255, 200, 110), 0.7*pl)
    L2 = Layer(W, H); ta = ramp(t, 0.4, 1.0)
    L2.rrect((C[0]+R+14*s, C[1]-46*s, C[0]+R+400*s, C[1]+44*s), 6*s, fill=(11, 16, 34), alpha=0.75*ta)
    L2.text((C[0]+R+28*s, C[1]-12*s), '护目镜（戴在眼前）', F(SANS_B, 22*s), fill=CREAM, alpha=ta, anchor='ls')
    L2.text((C[0]+R+28*s, C[1]+24*s), '摄像头看外界 → 打出琥珀色光脉冲', F(SANS, 20*s), fill=BRIGHT, alpha=ta, anchor='ls')
    return grade(over(rgb, L2.get()), seed=int(t*24)+7, grain=0.004, vig=0.0, lift=(0, 0, 0))

# ------------------------------------------------------------------------------------------------
# every scene renders with the label scale set for its own width
# ------------------------------------------------------------------------------------------------
def _wrap(fn):
    def g(t, W, H, *a, **k):
        _SC[0] = W/1280; return fn(t, W, H, *a, **k)
    return g
for _n in list(S):
    _fn, _d = S[_n]
    if not getattr(_fn, '_r9', False):
        w = _wrap(_fn); w._r9 = True; S[_n] = (w, _d)
