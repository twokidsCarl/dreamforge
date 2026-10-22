"""Round 7 (Carl 18:17 + routing 18:19): fix only what the round-6b independent review named.
Routing: organic motion = Wan (SF10 walk); science mechanics = controllable 2D layers (SF06/08/09/11);
titles/portraits = still plates + 2D camera / light sweeps (SF04/05/07)."""
import sys, os; sys.path.insert(0, '/workspace/e2work/v8/tools')
from sf_r7 import *          # noqa
from sf_r7 import _cache, vat, vframes, have
import sf_r5 as R5, sf_r6 as R6

def chip_seq(L2, t, states, s, x_right=1230, y=44):
    """status chip: states never overlap (each fades fully out before the next fades in)"""
    for name, col, a0, a1 in states:
        aa = (ramp(t, a0+0.12, a0+0.32) if a0 > 0 else 1)*(1-ramp(t, a1-0.12, a1+0.04))
        if aa <= 0.002: continue
        tw_ = F(SANS_B, 20*s).getlength(name)
        L2.rrect((x_right*s-tw_-90*s, y*s, x_right*s, (y+44)*s), 22*s, fill=(12, 18, 38), alpha=0.82*aa)
        L2.dot((x_right*s-tw_-64*s, (y+22)*s), 7*s, fill=col, alpha=aa)
        L2.text((x_right*s-tw_-48*s, (y+30)*s), name, F(SANS_B, 20*s), fill=CREAM, alpha=aa, anchor='ls')

def family_tex(W, H, amt=1.0):
    """faint Goodsell-family backdrop: the ChR2 plate, blurred and darkened"""
    k = ('ftex', W, H)
    if k not in _cache:
        b = cv2.GaussianBlur(img('sf09e_chr2'), (0, 0), 7)
        _cache[k] = cv2.resize(b, (W, H), interpolation=cv2.INTER_AREA)
    return _cache[k]*amt

def tint_family(P, amt=0.55):
    """recolour a warm portrait toward the purple-teal family: luminance -> indigo/lilac/cream ramp + cyan rim"""
    lum = P.mean(2, keepdims=True)
    lo = np.array([0.10, 0.10, 0.26]); mid = np.array([0.52, 0.48, 0.78]); hi = np.array([0.98, 0.95, 0.92])
    g = np.where(lum < 0.5, lo+(mid-lo)*(lum/0.5), mid+(hi-mid)*((lum-0.5)/0.5))
    out = P*(1-amt)+g*amt
    e = cv2.Canny((np.clip(lum[..., 0], 0, 1)*255).astype(np.uint8), 40, 110).astype(np.float32)/255
    e = cv2.GaussianBlur(e, (0, 0), 0.8)[..., None]
    return np.clip(out*(1-0.35*e)+np.array([0.12, 0.10, 0.22])*0.35*e, 0, 1)

# =====================================================================================================
# SF10: illustration-family plates; Wan 3.0 first/last wake-up; Wan 2.6 real walk; light leads; time skip
# =====================================================================================================
SF10_TV = 5.0
def _trk10b():
    if 'trk10b' in _cache: return _cache['trk10b']
    A = img('sf10s_ill'); ih, iw = A.shape[:2]
    fr, fps = vframes('sf10_wake7', (iw, ih))
    g = [cv2.cvtColor((f*255).astype(np.uint8), cv2.COLOR_RGB2GRAY) for f in fr]
    x, y = int(0.615*iw), int(0.335*ih); r = 20; pos = []
    tpl = g[0][y-r:y+r, x-r:x+r]
    for k in range(len(g)):
        x0, y0 = max(0, x-60), max(0, y-60); win = g[k][y0:y+60, x0:x+60]
        res = cv2.matchTemplate(win, tpl, cv2.TM_CCOEFF_NORMED); _, _, _, ml = cv2.minMaxLoc(res)
        x, y = x0+ml[0]+r, y0+ml[1]+r; pos.append((x/iw, y/ih))
        if k % 4 == 0: tpl = g[k][y-r:y+r, x-r:x+r]
    pos = np.array(pos); pos = np.stack([cv2.GaussianBlur(pos[:, i].reshape(-1, 1), (1, 0), 3).ravel() for i in (0, 1)], 1)
    _cache['trk10b'] = (pos, fps); return _cache['trk10b']

def sf10_clip_t(t):
    """map scene time to (clip, clip time). 0-2.0 hold first frame (asleep), 2.0-5.0 wake clip 0.2-5.0 s, 5.0+ walk clip"""
    if t < 2.0: return 'sf10_wake7', 0.0
    if t < SF10_TV: return 'sf10_wake7', 0.2+(t-2.0)*(4.8/3.0)
    return 'sf10_walk7', (t-SF10_TV)*0.96

@scene('SF10_mouse_tripo', 7.5)
def sf10(t, W, H, still=False, still_frame=None):
    if still: t = 6.4
    s = W/1280; A = img('sf10s_ill'); ih, iw = A.shape[:2]
    z = 1.06+0.06*lin(t, 7.5); cxx = 0.55-0.04*lin(t, 7.5); cyy = 0.50
    P = lambda x, y: to_px(A, x, y, W, H, z, cxx, cyy)
    clip, ct = sf10_clip_t(t)
    frame = vat(clip, ct, (iw, ih))
    if t < 2.0:   # gentle breathing while asleep
        br = 1.0+0.006*math.sin(t*2*math.pi/1.6); M = cv2.getRotationMatrix2D((0.72*iw, 0.62*ih), 0, br)
        frame = cv2.warpAffine(frame, M, (iw, ih), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    if SF10_TV <= t < SF10_TV+0.2:   # same pose at the join; tiny cross-dissolve hides codec differences
        b = ramp(t, SF10_TV, SF10_TV+0.2); frame = vat('sf10_wake7', 99, (iw, ih))*(1-b)+frame*b
    rgb = cam(frame, W, H, zoom=z, cx=cxx, cy=cyy)
    on = ramp(t, 1.0, 1.35)
    if clip == 'sf10_wake7':
        pos, fps = _trk10b(); k = min(int(ct*fps), len(pos)-1); fx, fy = pos[k]
        X, Y = P(fx, fy); own = 1-0.4*ramp(ct, 3.6, 4.6)      # the clip's own fibre glow joins near its end
        if on*own > 0:
            Lf = Layer(W, H); topx, _ = P(fx+0.01, 0)
            Lf.line([(topx, -5), (X, Y-8*s)], fill=CYAN, width=2.4*s, alpha=0.95*on*own)
            # photons running down the fibre
            for n in range(6):
                p = (t*1.4+n/6) % 1.0; Lf.dot((topx+(X-topx)*p, (Y-8*s)*p), 2.4*s, fill=(210, 240, 255), alpha=on*own*min(1, (1-p)*6))
            rgb = over(rgb, Lf.get(), shadow=0, glow_amt=1.3)
            rgb = rgb+radial(W, H, X, Y, 16*s, CYAN, 0.9*on*own)+radial(W, H, X, Y, 70*s, CYAN, 0.16*on*own)
        imp = (X, Y)
    else:
        imp = None
    rgb = over(rgb, drift_specks(W, H, t, 26, 17, (190, 215, 255), 0.2, 1.3, (3, -2)), shadow=0)
    # time compression: the light has to stay on a while before the state flips
    sk = ramp(t, 1.55, 1.85)*(1-ramp(t, 2.75, 3.05))
    if sk > 0:
        yy, xx = np.mgrid[0:H, 0:W]
        rgb = rgb*(1-0.18*sk*np.clip(np.abs(xx/W-0.5)*2, 0, 1)[..., None])        # slight edge dim during the skip
    L2 = Layer(W, H)
    if imp is not None:
        label(L2, imp, (60*s, 96*s), '光纤 + 颅骨植入件', '把蓝光送进下丘脑外侧那群细胞', t=ramp(t, 0.5, 1.2)*(1-ramp(t, 4.6, 4.9)), font_size=LT*s, sub_size=LS*s, accent=CYAN)
    if sk > 0:
        cx_, cy_ = W*0.36, 112*s; tw = F(SANS_B, 24*s).getlength('约 20 秒后')
        L2.rrect((cx_-tw/2-62*s, cy_-34*s, cx_+tw/2+26*s, cy_+16*s), 25*s, fill=(12, 18, 38), alpha=0.86*sk)
        # fast-forward glyph, its two triangles pulse in turn
        for j in range(2):
            x0 = cx_-tw/2-50*s+j*16*s; aj = sk*(0.55+0.45*math.sin(t*12-j*1.5))
            L2.d.polygon([((x0)*2, (cy_-22*s)*2), ((x0+15*s)*2, (cy_-9*s)*2), ((x0)*2, (cy_+4*s)*2)], fill=(*CYAN, int(255*aj)))
        L2.text((cx_-tw/2+4*s, cy_-1*s), '约 20 秒后', F(SANS_B, 24*s), fill=CREAM, alpha=sk, anchor='ls')
        L2.text((cx_, cy_+40*s), '光一直开着', F(SANS, 16*s), fill=(176, 186, 212), alpha=sk, anchor='ms')
    a = ramp(t, 0.2, 0.9)
    L2.rrect((56*s, 612*s, 560*s, 684*s), 6*s, fill=(14, 20, 40), alpha=0.78*a); L2.line([(56*s, 612*s), (56*s, 684*s)], fill=GOLD, width=3*s, alpha=a)
    L2.text((76*s, 642*s), '2007 · 小鼠 · 食欲素神经元', F(SANS_B, 21*s), fill=CREAM, alpha=a, anchor='ls')
    L2.text((76*s, 670*s), '光一开：从睡眠转入清醒的概率升高', F(SANS, 16*s), fill=(176, 186, 212), alpha=a, anchor='ls')
    chip_seq(L2, t, [('睡眠中', (150, 160, 190), 0.0, 1.0), ('光开', CYAN, 1.0, 2.9), ('这一次：醒来', GOLD, 2.9, SF10_TV), ('醒来后走动', GOLD, SF10_TV, 99)], s)
    return grade(over(rgb, L2.get()), seed=int(t*24))

# =====================================================================================================
# SF11: illustration-family eye; refracted beams; fovea magnifier: RGCs + ChrimsonR + AAV capsids
# =====================================================================================================
EYE7 = [[(0.135, 0.365), (0.300, 0.372), (0.405, 0.392), (0.684, 0.478)],
        [(0.135, 0.455), (0.300, 0.455), (0.405, 0.448), (0.684, 0.478)]]
RGC7 = [(0.18, 0.23), (0.47, 0.23), (0.82, 0.23)]
@scene('SF11_eye_goggles', 5.0)
def sf11(t, W, H):
    s = W/1280; u = lin(t, 5)
    if 'eye7' not in _cache:
        raw = np.asarray(Image.open(G+'sf11d_eye.png').convert('RGB')); ih, iw = raw.shape[:2]
        r_, g_, b_ = [raw[..., i].astype(np.int16) for i in range(3)]
        m = ((r_ > 225) & (g_ > 170) & (b_ < 190) & (r_-b_ > 70)).astype(np.uint8)*255
        yy, xx = np.mgrid[0:ih, 0:iw]; band = (xx > 0.03*iw) & (xx < 0.70*iw) & (yy > 0.28*ih) & (yy < 0.52*ih)
        # keep only thin ray-like structures inside the beam band (not the bright retina itself)
        m = m*band; m = cv2.dilate(m.astype(np.uint8), np.ones((9, 9), np.uint8))
        _cache['eye7'] = cv2.inpaint(raw, m, 7, cv2.INPAINT_TELEA).astype(np.float32)/255
    im = _cache['eye7']; z = 1.02+0.06*u; cxx = 0.50+0.01*u; cyy = 0.50
    rgb = cam(im, W, H, zoom=z, cx=cxx, cy=cyy)
    P = lambda x, y: to_px(im, x, y, W, H, z, cxx, cyy)
    on = ramp(t, 0.6, 1.1)
    Lb = Layer(W, H); arrive = []
    for bi, beam in enumerate(EYE7):
        pts = [P(*p) for p in beam]
        seg = [math.hypot(pts[i+1][0]-pts[i][0], pts[i+1][1]-pts[i][1]) for i in range(3)]; tot = sum(seg)
        grow = ramp(t, 0.6, 1.6)*tot          # beam draws on from the goggles to the fovea
        d = 0; drawn = [pts[0]]
        for i in range(3):
            if grow >= d+seg[i]: drawn.append(pts[i+1])
            else:
                f = max(0, (grow-d)/seg[i]); drawn.append((pts[i][0]+(pts[i+1][0]-pts[i][0])*f, pts[i][1]+(pts[i+1][1]-pts[i][1])*f)); break
            d += seg[i]
        if len(drawn) > 1: Lb.line(drawn, fill=(255, 190, 90), width=2.2*s, alpha=0.8*on)
        for p in pts[1:3]:
            if grow > math.hypot(p[0]-pts[0][0], p[1]-pts[0][1]): Lb.ring(p, 5*s, fill=(255, 230, 170), width=1.4*s, alpha=0.8*on)
        if t > 1.6:
            for n in range(4):
                dd = ((t*0.7+n/4+bi*0.12) % 1.0)*tot; i = 0
                while i < 2 and dd > seg[i]: dd -= seg[i]; i += 1
                f = dd/seg[i]; Lb.dot((pts[i][0]+(pts[i+1][0]-pts[i][0])*f, pts[i][1]+(pts[i+1][1]-pts[i][1])*f), 3.6*s, fill=(255, 215, 140), alpha=ramp(t, 1.6, 1.9))
    rgb = over(rgb, Lb.get(), shadow=0, glow_amt=1.1)
    FX, FY = P(0.684, 0.478)
    rgb = rgb+radial(W, H, FX, FY, 14*s, (255, 200, 110), 0.8*ramp(t, 1.4, 1.7)*(0.8+0.2*math.sin(t*7)))
    # magnifier at the fovea
    C = (300*s, 515*s); R = int(152*s); a = ramp(t, 1.9, 2.6)
    L = Layer(W, H)
    if a > 0:
        k = ease_out(a); px, py = FX+(C[0]-FX)*k, FY+(C[1]-FY)*k; r = max(2, int(R*k))
        L.ring((FX, FY), 10*s, fill=AMBER, width=1.8*s, alpha=a)
        ang = math.atan2(FY-py, FX-px)
        for sg in (-1, 1): L.line([(FX, FY), (px+r*math.cos(ang+sg*0.6), py+r*math.sin(ang+sg*0.6))], fill=AMBER, width=1.1*s, alpha=0.6*a)
        L.dot((px, py), r+6*s, fill=(8, 10, 24), alpha=0.9*a)
        zi = 1.0+0.06*ramp(t, 2.0, 5.0)
        L.paste(circ_img(img('sf11_inset'), r, zoom=zi, cx=0.5, cy=0.5), (px-r, py-r), alpha=a)
        L.ring((px, py), r, fill=AMBER, width=2.4*s, alpha=a)
    rgb = over(rgb, L.get(), shadow=0.35)
    IP = lambda x, y: (C[0]+(x-0.5)*2*R*1.0, C[1]+(y-0.5)*2*R*1.0)
    if a >= 1:
        # amber light arrives in pulses; each RGC fires in turn (ChrimsonR opens)
        for j, (rx, ry) in enumerate(RGC7):
            ph = ((t-2.6-j*0.12) % 0.8)/0.8 if t > 2.6 else 1
            fl = math.exp(-(ph/0.18)**2)*ramp(t, 2.6, 2.9)
            X, Y = IP(rx, ry); rgb = rgb+radial(W, H, X, Y, 22*s, (255, 190, 90), 0.75*fl)+radial(W, H, X, Y, 6*s, (255, 240, 200), 0.8*fl)
        # the beam enters the magnifier from the top
        rgb = rgb+radial(W, H, C[0]-40*s, C[1]-R*0.75, 60*s, (255, 190, 90), 0.12*(0.8+0.2*math.sin(t*5)))
    L2 = Layer(W, H)
    X, Y = P(0.09, 0.30); label(L2, (X, Y), (60*s, 96*s), '护目镜', '把外界明暗换成琥珀色光脉冲', t=ramp(t, 0.3, 1.1), font_size=LT*s, sub_size=LS*s, accent=AMBER)
    X, Y = P(0.405, 0.392); label(L2, (X, Y), (560*s, 70*s), '角膜、晶状体把光折向中央凹', None, t=ramp(t, 1.1, 1.9), font_size=19*s, accent=(255, 200, 120))
    X, Y = IP(*RGC7[1]); label(L2, (X, Y), (520*s, 448*s), '神经节细胞：膜上装了 ChrimsonR', '病毒载体（AAV，紫色小颗粒）把基因带进去', t=ramp(t, 2.7, 3.5), font_size=LT*s, sub_size=LS*s, accent=AMBER)
    X, Y = IP(0.62, 0.80); label(L2, (X, Y), (520*s, 640*s), '感光细胞：已大量丢失', None, t=ramp(t, 3.5, 4.2), font_size=19*s, accent=(170, 170, 180))
    return grade(over(rgb, L2.get()), seed=int(t*24), lift=(0.03, 0.04, 0.09))

# =====================================================================================================
# SF06: neuron redrawn in the family (dark outlines); title clear of dendrites; '?' fully out before ChR2;
#       light-up stretched to ~0.8 s
# =====================================================================================================
@scene('SF06_switch_diagram', 6.0)
def sf06(t, W, H):
    s = W/1280; u = lin(t, 6); im = img('sf06t_neuron'); ih, iw = im.shape[:2]
    if 'nm6t' not in _cache:
        lum = cv2.GaussianBlur(im.mean(2), (0, 0), 1.2)
        m = np.clip((lum-0.30)/0.18, 0, 1); _cache['nm6t'] = cv2.GaussianBlur(m, (0, 0), 1.5)[..., None]
    nm = _cache['nm6t']
    on = ramp(t, 3.7, 4.5)
    if on > 0:
        yy, xx = np.mgrid[0:ih, 0:iw]; d = np.hypot(xx/iw-0.75, (yy/ih-0.55)*0.6)
        front = np.clip((on*0.95-d)/0.16, 0, 1)[..., None]
        src = im+nm*front*np.array([0.25, 0.65, 1.0])*0.32*(0.92+0.08*math.sin(t*5))
    else: src = im
    z = 1.0+0.08*u; cxx = 0.50+0.03*u; cyy = 0.5
    rgb = cam(src, W, H, zoom=z, cx=cxx, cy=cyy); rgb = glow(rgb, 0.7, W/70, 0.3*on)
    P = lambda x, y: to_px(im, x, y, W, H, z, cxx, cyy)
    yy, xx = np.mgrid[0:H, 0:W]
    calm = np.clip(1-np.hypot((xx/W)/0.55, (yy/H)/0.22), 0, 1)**0.8                 # top-left title field
    calm = np.maximum(calm, np.clip((yy/H-0.86)/0.08, 0, 1))                      # timeline strip
    rgb = rgb*(1-0.62*calm[..., None])+np.array(INK)/255*0.62*calm[..., None]
    rgb = over(rgb, drift_specks(W, H, t, 50, 31, (170, 190, 255), 0.3, 1.5, (10, -4)), shadow=0)
    L = Layer(W, H); ax, ay = P(0.685, 0.50); C = (360*s, 345*s); R = int(165*s)
    a = ramp(t, 1.3, 2.1)
    if a > 0:
        k = ease_out(a); px, py = ax+(C[0]-ax)*k, ay+(C[1]-ay)*k; r = max(2, int(R*k))
        L.ring((ax, ay), 9*s, fill=CYAN, width=1.6*s, alpha=a)
        ang = math.atan2(ay-py, ax-px)
        for sg in (-1, 1): L.line([(ax, ay), (px+r*math.cos(ang+sg*0.5), py+r*math.sin(ang+sg*0.5))], fill=CYAN, width=1.0*s, alpha=0.6*a)
        L.dot((px, py), r+5*s, fill=(8, 10, 24), alpha=0.88*a)
        q_out = 1-ramp(t, 2.25, 2.65); rev = ease(ramp(t, 2.7, 3.3))
        if rev > 0:
            ch = circ_img(img('sf09e_chr2'), r, zoom=2.1+0.15*u, cx=0.495, cy=0.47)
            L.paste(ch, (px-r, py-r), alpha=a*rev)
        if q_out > 0: L.text((px, py+30*s*k), '?', F(SERIF_B, 96*s*k), fill=MUTED, alpha=a*q_out, anchor='ms')
        L.ring((px, py), r, fill=CYAN if rev > 0.5 else (130, 150, 200), width=2.2*s, alpha=a)
    rgb = over(rgb, L.get(), shadow=0.3)
    if t > 3.3:
        b = ramp(t, 3.3, 3.8)
        rgb = rgb+radial(W, H, C[0]-20*s, C[1]-60*s, 110*s, CYAN, 0.18*b*(0.85+0.15*math.sin(t*6)))
    L2 = Layer(W, H)
    ta = ramp(t, 0, 0.7); tw0 = F(SERIF_B, 32*s).getlength('从设想到方法，中间缺什么？')+13*2*s
    L2.rrect((40*s, 40*s, 80*s+tw0, 102*s), 8*s, fill=(10, 13, 30), alpha=0.82*ta)
    L2.line([(40*s, 40*s), (40*s, 102*s)], fill=CYAN, width=3*s, alpha=ta)
    L2.text((60*s, 82*s), '从设想到方法，中间缺什么？', F(SERIF_B, 32*s), fill=CREAM, alpha=ta, anchor='ls', tracking=2*s)
    a3 = ramp(t, 3.0, 3.6)
    L2.text((C[0], C[1]+R+40*s), '一枚能用光拨动的开关', F(SANS_B, 26*s), fill=CYAN, alpha=a3, anchor='ms')
    L2.text((C[0], C[1]+R+68*s), '光控离子通道（如 ChR2），装在神经元膜上', F(SANS, 16*s), fill=(176, 186, 212), alpha=a3, anchor='ms')
    a4 = ramp(t, 3.4, 4.0)
    for (dx, dy, tx, ty, txt, col) in ((-112, -18, 112, 150, '视黄醛：吸收光', (255, 138, 61)), (-62, 40, 612, 150, '孔道：离子通过', CYAN)):
        x0, y0 = C[0]+dx*s, C[1]+dy*s; tx, ty = tx*s, ty*s
        L2.ring((x0, y0), 5*s, fill=col, width=1.5*s, alpha=a4)
        L2.line([(x0, y0), (x0+(tx-x0)*ease_out(a4), y0+(ty-y0)*ease_out(a4))], fill=col, width=1.1*s, alpha=0.9*a4)
        tw = F(SANS_B, 16*s).getlength(txt)
        L2.rrect((tx-tw/2-10*s, ty-24*s, tx+tw/2+10*s, ty+6*s), 6*s, fill=(12, 18, 38), alpha=0.85*a4)
        L2.text((tx, ty-3*s), txt, F(SANS_B, 16*s), fill=CREAM, alpha=a4, anchor='ms')
    y = 676*s; x0, x1 = 60*s, 1220*s; a0 = ramp(t, 0.4, 1.2)
    L2.line([(x0, y), (x0+(x1-x0)*ease_out(ramp(t, 0.4, 4.8)), y)], fill=(120, 132, 170), width=1.2*s, alpha=a0)
    nodes = [(0.0, 0.6, '1999', '一句自认牵强的设想', GOLD), (0.45, 1.8, '？', '缺一枚光控开关', CYAN), (1.0, 4.6, '2026 诺奖', '一套能用的方法：光遗传学', GOLD)]
    for (q, t0, yr, txt, col) in nodes:
        aa = ramp(t, t0, t0+0.5); x = x0+(x1-x0)*q
        if aa <= 0: continue
        L2.dot((x, y), 5*s, fill=col, alpha=aa)
        an = 'l' if q < 0.9 else 'r'; xo = x+(10*s if an == 'l' else -10*s)
        L2.text((xo, y-12*s), yr+'  '+txt, F(SANS_B, 16*s), fill=CREAM, alpha=aa, anchor=an+'s')
    return grade(over(rgb, L2.get()), seed=int(t*24))

# =====================================================================================================
# SF04: portrait re-toned to the family; faint family backdrop; continuous push; the word 光 lights up
# =====================================================================================================
_cache['sf04_crick_portrait'] = tint_family(img('sf04_crick_portrait'), 0.5)
_sf04_r6 = R6.S['SF04_crick_quote'][0]
@scene('SF04_crick_quote', 5.0)
def sf04(t, W, H):
    s = W/1280; u = lin(t, 5)
    rgb = _sf04_r6(t, W, H)
    lum = rgb.mean(2, keepdims=True); dark = np.clip((0.22-lum)/0.12, 0, 1)
    rgb = rgb+family_tex(W, H)*0.22*dark*ramp(t, 0, 1.0)
    # 光 glows once the beam has reached the quote
    f = F(SERIF_B, 46*s); x0 = 690*s+f.getlength('“理想的信号会是'); w = f.getlength('光')
    gl = ramp(t, 1.8, 2.4)*(0.75+0.25*math.sin(t*3.2))
    rgb = rgb+radial(W, H, x0+w/2, 302*s, 34*s, CYAN, 0.55*gl)
    # slow continuous push + drift (separates it from a held still)
    rgb = cam(np.clip(rgb, 0, 1), W, H, zoom=1.0+0.07*ease(u)+0.01*u, cx=0.5+0.015*u, cy=0.5-0.01*u)
    return np.clip(rgb, 0, 1)

# =====================================================================================================
# SF05: portraits re-toned; family backdrop; ChR2 badge lights when the citation names the channel; push
# =====================================================================================================
for _k in 'DHN':
    _n = R5.P5[_k][0]; _cache[_n] = tint_family(img(_n), 0.5)
_sf05_r5 = R5.S['SF05_nobel_portraits'][0]
@scene('SF05_nobel_portraits', 5.0)
def sf05(t, W, H):
    s = W/1280; u = lin(t, 5)
    rgb = _sf05_r5(t, W, H)
    lum = rgb.mean(2, keepdims=True); dark = np.clip((0.22-lum)/0.12, 0, 1)
    rgb = rgb+family_tex(W, H)*0.2*dark
    # ChR2 badge left of the citation line, lights with the words 光控离子通道
    a = ramp(t, 2.5, 3.1); L = Layer(W, H)
    f = F(SERIF, 20*s); tw = f.getlength('获奖理由：发现光控离子通道，并由此建立光遗传学')
    bx, by, r = W/2-tw/2-46*s, 111*s, int(26*s)
    if a > 0:
        L.dot((bx, by), r+4*s, fill=(8, 10, 24), alpha=0.9*a)
        L.paste(circ_img(img('sf09e_chr2'), r, zoom=2.4, cx=0.49, cy=0.47), (bx-r, by-r), alpha=a)
        L.ring((bx, by), r, fill=CYAN, width=1.8*s, alpha=a)
    rgb = over(rgb, L.get(), shadow=0.3)
    if a > 0:
        pulse = ramp(t, 3.0, 3.4)*(0.6+0.4*math.sin((t-3.0)*5))
        rgb = rgb+radial(W, H, bx, by, 34*s, CYAN, 0.45*pulse)
        # underline glow under 光控离子通道
        x0 = W/2-tw/2+f.getlength('获奖理由：发现'); x1 = x0+f.getlength('光控离子通道')
        Lu = Layer(W, H); k = ease_out(ramp(t, 3.0, 3.6)); Lu.line([(x0, 126*s), (x0+(x1-x0)*k, 126*s)], fill=CYAN, width=2*s, alpha=0.9)
        rgb = over(rgb, Lu.get(), shadow=0, glow_amt=0.8)
    zz = 1.0+0.05*ease(u)+0.01*u; rgb = cam(np.clip(rgb, 0, 1), W, H, zoom=zz, cx=0.5, cy=0.5+0.5*(1-1/zz)*0.6)
    return np.clip(rgb, 0, 1)

# =====================================================================================================
# SF07: only a small cluster under the fibre lights (one cell type, not the whole cortex);
#       clean dark family backdrop instead of the blurred side blobs; steady push toward the title
# =====================================================================================================
@scene('SF07_main_title', 5.0)
def sf07(t, W, H):
    s = W/1280; im0 = img('sf07e_title_bg'); ih, iw = im0.shape[:2]; u = lin(t, 5)
    tip = (0.59, 0.245)
    if 'p7f' not in _cache:
        yy, xx = np.mgrid[0:ih, 0:iw]; d = np.hypot(xx/iw-tip[0], (yy/ih-tip[1])*1.5)
        cm = cyan_mask(im0, 110, 2.0)[..., None]; far = np.clip((d-0.10)/0.07, 0, 1)[..., None]
        fib = ((np.abs(xx/iw-tip[0]) < 0.02) & (yy/ih < tip[1]))[..., None]
        far = far*(1-fib)
        lum = im0.mean(2, keepdims=True); lil = lum*np.array([0.95, 0.72, 1.05])
        dim = im0*(1-cm*far)+lil*cm*far
        cm2 = cyan_mask(im0, 175, 1.0)*(d < 0.12); ys, xs = np.nonzero(cm2 > 0.5); rng = np.random.default_rng(2)
        idx = rng.choice(len(xs), min(90, len(xs)), replace=False) if len(xs) else []
        _cache['p7f'] = (dim, [(xs[i]/iw, ys[i]/ih, rng.random()) for i in idx])
    im, pts = _cache['p7f']
    bgc = np.zeros((H, W, 3), np.float32)+np.array(INK)/255
    if ('bg7f', W) not in _cache:
        tx_ = cv2.resize(im0[int(0.58*ih):, :], (W, H), interpolation=cv2.INTER_AREA)
        _cache[('bg7f', W)] = cv2.GaussianBlur(tx_, (0, 0), 3.5*W/1280)
    bgc = bgc*0.6+_cache[('bg7f', W)]*0.42
    yy, xx = np.mgrid[0:H, 0:W]
    z = 1.0+0.06*u+0.10*ease(ramp(t, 1.5, 5.0)); sc_ = H*0.95/ih*z; Wi, Hi = int(iw*sc_), int(ih*sc_)
    ox = W*0.5-0.5*Wi-10*s*u; oy = H*0.10-0.12*Hi+4*s*u
    M = np.array([[sc_, 0, ox], [0, sc_, oy]], np.float32)
    pic = cv2.warpAffine(im, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
    e = np.minimum.reduce([(xx-ox)/(180*s), (ox+Wi-xx)/(180*s)]); mk = np.clip(e, 0, 1)[..., None]
    rgb = bgc*(1-mk)+pic*mk
    lm = np.clip((yy/H-0.62)/0.2, 0, 1)[..., None]; rgb = rgb*(1-0.6*lm)+np.array(INK)/255*0.6*lm
    L = Layer(W, H)
    for (px, py, ph) in pts:
        d = math.hypot(px-tip[0], (py-tip[1])*1.5); a = 0.25*(t > 0.7+d*8)
        for w0 in (0.7, 1.9, 3.1, 4.3): a += math.exp(-((t-(w0+d*8.0+ph*0.15))/0.16)**2)
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

# =====================================================================================================
# SF02: new field (varied neuron shapes; the non-lit cells are neurons too); bullets -> in-picture labels
# =====================================================================================================
@scene('SF02_1979_request', 5.0)
def sf02(t, W, H):
    im = img('sf02c_crowd'); ih, iw = im.shape[:2]; s = W/1280
    if 'g2c' not in _cache:
        hsv = cv2.cvtColor((im*255).astype(np.uint8), cv2.COLOR_RGB2HSV).astype(np.float32)
        m = ((hsv[..., 0] > 6) & (hsv[..., 0] < 32) & (hsv[..., 1] > 90) & (hsv[..., 2] > 110)).astype(np.uint8)
        nlab, lab = cv2.connectedComponents(cv2.dilate(m, np.ones((7, 7), np.uint8)))
        area = np.bincount(lab.ravel())
        cent = {k: (np.nonzero(lab == k)[1].mean()/iw, np.nonzero(lab == k)[0].mean()/ih) for k in range(1, nlab) if area[k] > 150}
        order = {k: i/max(1, len(cent)-1) for i, k in enumerate(sorted(cent, key=lambda k: cent[k][0]))}
        gray = im.mean(2, keepdims=True); d2 = im*0.30+gray*np.array([0.40, 0.42, 0.58])*0.45
        # soma of the biggest gold cell near the centre, and a slate (non-lit) neuron soma for the labels
        big = max(cent, key=lambda k: area[k]*(1.2-abs(cent[k][0]-0.5)-abs(cent[k][1]-0.5)))
        bm = ((hsv[..., 0] > 100) & (hsv[..., 0] < 135) & (hsv[..., 1] > 60) & (hsv[..., 2] > 120)).astype(np.uint8)
        bm[:int(0.2*ih)] = 0; bm[int(0.8*ih):] = 0; bm[:, :int(0.2*iw)] = 0; bm[:, int(0.8*iw):] = 0
        bm = cv2.morphologyEx(bm, cv2.MORPH_OPEN, np.ones((9, 9), np.uint8))
        nb, lb, st, cc = cv2.connectedComponentsWithStats(bm)
        j = 1+int(np.argmax(st[1:, cv2.CC_STAT_AREA])) if nb > 1 else None
        blue = (cc[j][0]/iw, cc[j][1]/ih) if j else (0.35, 0.55)
        _cache['g2c'] = (lab, order, m, d2, cent[big], blue)
    lab, order, m, d2, gpos, bpos = _cache['g2c']
    on = np.zeros(lab.shape, np.float32); pulse = np.zeros(lab.shape, np.float32)
    for k, q in order.items():
        tk = 0.9+1.6*q; on[lab == k] = ramp(t, tk, tk+0.6); pulse[lab == k] = math.exp(-((t-tk-0.3)/0.25)**2)
    gm = cv2.GaussianBlur(m.astype(np.float32)*on, (0, 0), 2)[..., None]; pm = cv2.GaussianBlur(m.astype(np.float32)*pulse, (0, 0), 6)[..., None]
    base = d2*(1-gm)+im*0.95*gm+pm*np.array([1.0, 0.75, 0.35])*0.35
    z = 1.10+0.08*lin(t, 5); cx, cy = 0.50+0.02*lin(t, 5), 0.50
    rgb = cam(base, W, H, zoom=z, cx=cx, cy=cy); rgb = glow(rgb, 0.75, W/90, 0.3)
    rgb = over(rgb, drift_specks(W, H, t, 40, 5, (255, 220, 170), 0.25), shadow=0)
    P = lambda x, y: to_px(im, x, y, W, H, z, cx, cy)
    L = Layer(W, H)
    L.rrect((56*s, 52*s, 470*s, 124*s), 6*s, fill=(14, 20, 40), alpha=0.8*ramp(t, 0.2, 0.9))
    L.line([(56*s, 52*s), (56*s, 124*s)], fill=GOLD, width=3*s, alpha=ramp(t, 0.2, 0.9))
    L.text((76*s, 84*s), 'Francis Crick · 1979', F(SANS_B, 23*s), fill=CREAM, alpha=ramp(t, 0.3, 1.0), anchor='ls')
    L.text((76*s, 110*s), '《科学美国人》 Thinking about the Brain', F(SANS, 16*s), fill=(176, 186, 212), alpha=ramp(t, 0.4, 1.1), anchor='ls')
    X, Y = P(*gpos); label(L, (X, Y), (X+(150 if X < W*0.6 else -150)*s, Y-120*s), '同一类神经元', '一起被点亮', t=ramp(t, 2.7, 3.5), font_size=LT*s, sub_size=LS*s, accent=GOLD)
    X, Y = P(*bpos); label(L, (X, Y), (X+(150 if X < W*0.6 else -150)*s, Y+110*s), '其余神经元', '大体不动', t=ramp(t, 3.3, 4.1), font_size=LT*s, sub_size=LS*s, accent=(150, 156, 200))
    return grade(over(rgb, L.get()), seed=int(t*24))

# =====================================================================================================
# SF03: archaeal inset: baked-in green dots removed; H+ now pumped out one at a time (pump, not channel)
#       cards shortened to one line each; insets staggered
# =====================================================================================================
def _ins_l3():
    if 'sf03_ins_l3' not in _cache:
        raw = (img('sf03_ins_l2')*255).astype(np.uint8); hsv = cv2.cvtColor(raw, cv2.COLOR_RGB2HSV)
        m = ((hsv[..., 0] > 45) & (hsv[..., 0] < 85) & (hsv[..., 1] > 90) & (hsv[..., 2] > 90)).astype(np.uint8)*255
        m = cv2.dilate(m, np.ones((9, 9), np.uint8))
        _cache['sf03_ins_l3'] = cv2.inpaint(raw, m, 9, cv2.INPAINT_TELEA).astype(np.float32)/255
    return _cache['sf03_ins_l3']

@scene('SF03_microbe_clues', 5.0)
def sf03(t, W, H):
    base0 = img('sf03e_microbes')
    im = vat('sf03_swim', t, (base0.shape[1], base0.shape[0])) if have('sf03_swim') else base0
    u = lin(t, 5); s = W/1280; z = 1.02+0.07*u; cxx = 0.5+0.012*u; cyy = 0.5
    rgb = cam(im, W, H, zoom=z, cx=cxx, cy=cyy)
    P = lambda x, y: to_px(im, x, y, W, H, z, cxx, cyy)
    ex, ey = P(0.733, 0.505)
    flash = ramp(t, 2.6, 3.0)*(0.7+0.3*math.sin(t*6))
    rgb = rgb+radial(W, H, ex, ey, W*0.012, (255, 120, 60), 0.45*flash)+radial(W, H, ex, ey, W*0.05, CYAN, 0.12*flash)
    rgb = over(rgb, drift_specks(W, H, t, 60, 7, (190, 230, 255), 0.3, 1.4, (12, -6)), shadow=0)
    L = Layer(W, H)
    L.rrect((28*s, 26*s, 352*s, 68*s), 6*s, fill=(12, 18, 38), alpha=0.75*ramp(t, 0.1, 0.8))
    L.text((44*s, 54*s), '接下来的那些年 · 微生物那边', F(SANS, 18*s), fill=CREAM, alpha=ramp(t, 0.1, 0.8)*0.92, anchor='ls', tracking=3*s)
    CL = (560*s, 160*s); RL = int(112*s); zl = 1.05+0.08*u
    ax, ay = P(0.352, 0.375)
    R5.inset(L, None, t, ramp(t, 0.6, 1.3), _ins_l3(), CL, RL, (ax, ay), GOLD, None, u)
    CR = (1110*s, 440*s); RR = int(108*s)
    R5.inset(L, None, t, ramp(t, 2.6, 3.3), img('sf03_ins_r2'), CR, RR, (ex, ey), CYAN, None, u)
    rgb = over(rgb, L.get(), shadow=0.35)
    # pump rhythm inside the archaeal inset: one H+ at a time, carried up through the pump and released outside
    aL = ramp(t, 0.6, 1.3)
    if aL >= 1:
        Lp = Layer(W, H); IP = lambda x, y: (CL[0]+(x-0.5)*2*RL*zl, CL[1]+(y-0.5)*2*RL*zl)
        rng = np.random.default_rng(4); T0 = 1.4; per = 0.55
        nmax = int((t-T0)/per)+1 if t > T0 else 0
        for n in range(max(0, nmax-7), nmax):
            age = t-(T0+n*per)
            if age < 0: continue
            if age < 0.35:          # through the pump, inside -> outside
                q = ease(age/0.35); x, y = 0.505, 0.66-0.42*q
            else:                   # released, drifts away outside
                d = age-0.35; ang = rng.uniform(-2.4, -0.7) if True else 0
                x = 0.505+math.cos(ang)*0.10*d; y = 0.24+math.sin(ang)*0.07*d
            X, Y = IP(x, y)
            if math.hypot(X-CL[0], Y-CL[1]) < RL*0.92:
                Lp.dot((X, Y), 7.0*s, fill=(110, 230, 150), alpha=min(1, age*8)*(1-ramp(age, 2.6, 3.2)))
        # waiting H+ on the inside: one steps up each cycle
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
    card(40*s, 636*s, '嗜盐古菌（1970s）：光驱动的泵', ramp(t, 1.0, 1.6), GOLD)
    card(1240*s, 636*s, '衣藻（1991–96）：眼点受光，微秒级出电流', ramp(t, 3.0, 3.6), CYAN, right=True)
    a = ramp(t, 1.6, 2.2)
    L2.text((CL[0], CL[1]+RL+26*s), 'H⁺ 被一个一个泵到膜外', F(SANS_B, 17*s), fill=(150, 240, 175), alpha=a, anchor='ms')
    a = ramp(t, 3.1, 3.7); L2.text((CR[0], CR[1]-RR-14*s), '眼点膜上的感光蛋白', F(SANS_B, 17*s), fill=CREAM, alpha=a, anchor='ms')
    return grade(over(rgb, L2.get()), seed=int(t*24))

# ===== SF08 r7: slower pan (1.2 s, eased), ion label on first sight, speed bar from the start of route two =====
from sf_r5 import azo_sprite, MAG, MAG_O
@scene('SF08_early_attempts', 7.0)
def sf08(t, W, H):  # r7
    im = img('sf08e_relay'); s = W/1280
    pan = ease(ramp(t, 3.3, 4.5)); u = lin(t, 7)
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
    openA = ramp(t, 2.6, 3.0)*(1-ramp(t, 3.4, 3.9)); X, Y = P(0.585, 0.49); rgb = rgb+radial(W, H, X, Y, W*0.025, (255, 209, 102), 0.3*openA)
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
    L = Layer(W, H); b1 = 1-ramp(t, 3.25, 3.5); b2 = ramp(t, 4.3, 4.6)
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
    if b1 > 0:
        X, Y = P(0.60, 0.62); label(L, (X, Y), (760*s, 600*s), '离子', '通道一开就流进细胞', t=ramp(t, 2.5, 2.8)*b1, font_size=19*s, sub_size=LS*s, accent=(255, 209, 102))
    # speed comparison on a log time axis
    a = ramp(t, 4.5, 5.0)
    if a > 0:
        bx, by, bw = 60*s, 560*s, 600*s
        L.rrect((bx, by, bx+bw, by+136*s), 8*s, fill=(12, 18, 38), alpha=0.86*a)
        x0, x1 = bx+30*s, bx+bw-30*s; ay_ = by+100*s
        L.line([(x0, ay_), (x1, ay_)], fill=(150, 160, 190), width=1.2*s, alpha=a)
        ticks = ['1 ms', '10 ms', '100 ms', '1 s', '10 s']
        for q, tk in enumerate(ticks):
            x = x0+(x1-x0)*q/4; L.line([(x, ay_-4*s), (x, ay_+4*s)], fill=(150, 160, 190), width=1.2*s, alpha=a)
            L.text((x, ay_+24*s), tk, F(SANS, 16*s), fill=(176, 186, 212), alpha=a, anchor='ms')
        L.rrect((x0-5*s, ay_-14*s, x0+(x1-x0)*0.08, ay_-4*s), 4*s, fill=CYAN, alpha=a)
        L.text((x0-5*s, ay_-24*s), '需要：毫秒级', F(SANS_B, 16*s), fill=CYAN, alpha=a, anchor='ls')
        g = ease_out(ramp(t, 4.6, 5.3)); xa_ = x0+(x1-x0)*0.75
        L.rrect((xa_, ay_-14*s, xa_+(x1-xa_)*g, ay_-4*s), 4*s, fill=(255, 180, 120), alpha=a)
        L.text((xa_-40*s, ay_-24*s), '多步接力：秒级', F(SANS_B, 16*s), fill=(255, 200, 150), alpha=a, anchor='ls')
        c = ramp(t, 5.7, 6.2); xc0, xc1 = x0+(x1-x0)*0.02, x0+(x1-x0)*0.30
        L.rrect((xc0, ay_-38*s-14*s, xc0+(xc1-xc0)*ease_out(c), ay_-38*s-4*s), 4*s, fill=MAG, alpha=a*c)
        L.text((xc0, ay_-60*s), '化学开关：快，但要另外给药', F(SANS_B, 16*s), fill=(240, 160, 220), alpha=a*c, anchor='ls')
    return grade(over(rgb, L.get()), seed=int(t*24))


# ===== SF09 r7: helix bundles open (warp), ions jitter and scatter =====
from sf_r6 import ret_sprite
import mol
@scene('SF09_chr2_channel', 5.0)
def sf09(t, W, H):  # r7
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
    # helix bundles swing apart around each pore as the gate opens (controlled warp, not a glow)
    if opn > 0:
        if 'warp9' not in _cache:
            yy, xx = np.mgrid[0:ih, 0:iw].astype(np.float32); sig = 0.040*iw; D = np.zeros((ih, iw), np.float32)
            vy = np.clip((yy/ih-0.27)/0.05, 0, 1)*np.clip((0.70-yy/ih)/0.05, 0, 1)
            for pc in (0.434, 0.548):
                dxp = xx-pc*iw; D += dxp/sig*np.exp(-(dxp/sig)**2)
            _cache['warp9'] = (xx, yy, D*vy)
        xx, yy, D = _cache['warp9']; A = 0.012*iw*ease(opn)
        base = cv2.remap(base.astype(np.float32), xx-A*D, yy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
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
            jx = 0.006*math.sin(n*2.3+p*9+t*3.1)+0.004*math.sin(n*5.1+t*7.3)
            spread = max(0, p-0.72)/0.28; jx += (offs[j, n]-0.3)*0.20*spread      # ions scatter once they leave the pore
            X, Y = P(px_+jx, 0.20+p*0.62); a = ramp(t, 1.7, 2.0)*min(1, p*8)*min(1, (1-p)*6)
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

