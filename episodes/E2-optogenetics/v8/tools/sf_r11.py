"""Round 10 (PROMPT 第 10 轮, 22:43): only the round-9 independent-review Top gaps.  Narration NOT changed.
1 SF05: three depth planes pushed in all the way (portraits ~3.4 %/s, ground slower, foreground faster); header,
        badge and footnote on a fixed plane so they never leave the frame; staggered light sweep on the heads.
2 push >= 3 %/s on every plate (SF01/02/03/06/08/09/11 via a camera-zoom multiplier that also moves the label
  anchors; SF07 exponential push from frame 0; SF04 whole-frame push with the vignette moved inside the safe area).
  Key labels stay on screen: SF09 '470 nm' held to the end (retinal label hands over to the ion label instead);
  SF11 '感光细胞' held to 3.4 s, the cornea label waits for it; SF03 H+ caption held to 4.3 s.
3 SF08: 3 ticks only (1 ms / 100 ms / 10 s) at 26 px; route-two chip retires when the speed bar arrives.
4 SF04/SF05 portraits: Goodsell-family treatment (GrabCut silhouette -> dark contour, cyan/violet rim light,
  blurred molecule ground) - tools/famport.py.
5 cleanup: SF11 top-left crescent painted out; SF09 retinal smaller and set inside each helix bundle (seen through
  the helices); SF10 magnifier shows a single neuron (soma, dendrites, axon) that flashes with each pulse."""
import sys, os, math; sys.path.insert(0, '/workspace/e2work/v8/tools')
import sf, sf_scenes
import sf_r10 as R10
from sf_r10 import *          # noqa
from sf_r10 import _cache, _gold_neuron, _icon
import sf_r9 as R9
from famport import fam_portrait
TOOLS = '/workspace/e2work/v8/tools/'

# ------------------------------------------------------------------------------------------------
# camera-zoom multiplier: applied to any full-frame plate camera (cam / to_px at frame size), so label
# anchors computed with to_px follow the plate while label text stays screen-fixed.
# ------------------------------------------------------------------------------------------------
ZX = [None]; FR = [0, 0]
_cam0, _tp0 = sf.cam, sf.to_px
def cam11(img, W, H, zoom=1.0, cx=0.5, cy=0.5):
    if ZX[0] is not None and (W, H) == (FR[0], FR[1]) and img.shape[0]*img.shape[1] >= 300000: zoom = zoom*ZX[0]
    return _cam0(img, W, H, zoom, cx, cy)
def to_px11(img, x, y, W, H, zoom, cx, cy):
    if ZX[0] is not None and (W, H) == (FR[0], FR[1]) and img.shape[0]*img.shape[1] >= 300000: zoom = zoom*ZX[0]
    return _tp0(img, x, y, W, H, zoom, cx, cy)
for _m in list(sys.modules.values()):
    if _m is None or '/e2work/v8/tools/' not in (getattr(_m, '__file__', '') or ''): continue
    if getattr(_m, 'cam', None) is _cam0: _m.cam = cam11
    if getattr(_m, 'to_px', None) is _tp0: _m.to_px = to_px11
cam = cam11; to_px = to_px11
PUSH = {'SF01_open_title': 0.014, 'SF02_1979_request': 0.022, 'SF03_microbe_clues': 0.022, 'SF06_switch_diagram': 0.013,
        'SF08_early_attempts': 0.012, 'SF09_chr2_channel': 0.022, 'SF11_eye_goggles': 0.024}

# ------------------------------------------------------------------------------------------------
# re-run a round-9 build block (sf_r10.py) with extra patches, in sf_r10's namespace
# ------------------------------------------------------------------------------------------------
_R10SRC = open(TOOLS+'sf_r10.py').read()
def rerun10(tag, extra=(), ns=None):
    ex = "exec(compile(_s, 'sf_r10_%s', 'exec'), globals())" % tag
    b = _R10SRC.index(ex); a = _R10SRC.rindex("\n_s = src_of(", 0, b)+1
    code = _R10SRC[a:b]
    for o, n in extra:
        code += "_s = sub(_s, %r, %r)\n" % (o, n)
    code += "exec(compile(_s, 'sf_r11_%s', 'exec'), globals())\n" % tag
    exec(compile(code, 'rerun10_'+tag, 'exec'), ns if ns is not None else R10.__dict__)

# label diet edits (keys are (scene, label title) -> fade-out time)
R10.LBL.pop(('SF09_chr2_channel', '蓝光 约 470 nm'), None)
R10.LBL[('SF09_chr2_channel', '视黄醛')] = 2.45
R10.LBL[('SF11_eye_goggles', '感光细胞：已大量丢失')] = 3.4

# ================================================================================================
# SF03: H+ caption held longer (pushed out never; fades at 3.9 s)
# ================================================================================================
rerun10('sf03', [("alpha=a*(1-ramp(t, 2.9, 3.3)))", "alpha=a*(1-ramp(t, 3.9, 4.3)))")])

# ================================================================================================
# SF04: family portrait treatment; vignette inside the safe area; whole-frame push (+2 %/s on top of the plate)
# ================================================================================================
_s = R10.src_of('sf_r10.py', "@scene('SF04_crick_quote', 5.0)")
_s = R10.sub(_s, "P0 = img('sf04g_crick')", "P0 = fam_portrait('sf04g_crick', img('sf04g_crick'), fam_bg(1280, 720))")
_s = R10.sub(_s, "NC = (1112*s, 142*s); NR = int(100*s)", "NC = (1085*s, 172*s); NR = int(92*s)")
_s = R10.sub(_s, "bx0, bx1, by = NC[0]-NR, NC[0]+NR, NC[1]+NR+30*s", "bx0, bx1, by = NC[0]-NR-330*s, NC[0]-NR-30*s, NC[1]-34*s")
_s = R10.sub(_s, "    rgb = over(rgb, L2.get(), shadow=0.4)\n    return grade(rgb, seed=int(t*24))",
             "    rgb = over(rgb, L2.get(), shadow=0.4)\n    rgb = _cam0(np.clip(rgb, 0, 1), W, H, zoom=math.exp(0.020*t), cx=0.5, cy=0.5)\n    return grade(rgb, seed=int(t*24))")
exec(compile(_s, 'sf_r11_sf04', 'exec'), globals())

# ================================================================================================
# SF05: depth planes, continuous push; fixed header plane; family portraits
# ================================================================================================
@scene('SF05_nobel_portraits', 5.0)
def sf05(t, W, H):
    s = W/1280; u = lin(t, 5)
    zP = math.exp(0.039*t); zB = math.exp(0.024*t); zF = math.exp(0.065*t)
    PC = (W*0.5, 300*s)                                  # push centre (portrait row)
    # ground plane
    bg = np.zeros((H, W, 3), np.float32)+np.array([0.07, 0.055, 0.16])
    bg = bg*0.6+fam_bg(W, H)*0.30+radial(W, H, W*(0.3+0.4*u), H*0.12, W*0.42, (80, 90, 160), 0.12)
    bg = _cam0(bg, W, H, zoom=zB, cx=0.5, cy=PC[1]/H)
    # portrait plane (portraits + names + contribution icons), composed flat then pushed
    people = [('sf05g_deisseroth', 'Karl Deisseroth', 'neuron', '装进神经元'),
              ('sf05g_hegemann', 'Peter Hegemann', 'alga', '衣藻的感光电流'),
              ('sf05g_nagel', 'Georg Nagel', 'current', '证明它是光控通道')]
    cw = int(320*s); gap = int(44*s); x0 = (W-3*cw-2*gap)//2; y0 = int(172*s)
    plate = np.zeros((H, W, 3), np.float32); pm = np.zeros((H, W, 1), np.float32)
    L = Layer(W, H); blobs = fam_bg(1280, 720)
    for i, (key, nm, kind, cap) in enumerate(people):
        a = ramp(t, 0.2+i*0.3, 0.9+i*0.3); dy = int(18*s*(1-ease_out(a)))
        P0 = fam_portrait(key, img(key), blobs)
        Pc = _cam0(P0, cw, cw, zoom=1.10+0.05*u, cx=0.5+(i-1)*0.012*u, cy=0.42-0.015*u)   # inner drift = parallax
        tl = 1.6+i*0.75; sw = ramp(t, tl-0.3, tl+1.0)                                      # staggered light sweep
        if 0 < sw < 1:
            yy, xx = np.mgrid[0:cw, 0:cw]; band = np.exp(-(((xx+yy*0.5)/cw-(-0.2+1.7*sw))/0.09)**2)
            lum = Pc.mean(2, keepdims=True); Pc = np.clip(Pc+band[..., None]*np.clip(lum-0.18, 0, 1)*np.array([1.0, 0.82, 0.45])*0.6, 0, 1)
        x = x0+i*(cw+gap); y = y0+dy
        yy, xx = np.mgrid[0:cw, 0:cw]; e = np.minimum.reduce([xx/cw*2.2, (1-xx/cw)*2.2, yy/cw*3, (1-yy/cw)*1.6]); m = (np.clip(e/0.5, 0, 1)**1.6)[..., None]*a
        plate[y:y+cw, x:x+cw] = Pc*m; pm[y:y+cw, x:x+cw] = m
        ly = y0+cw+16*s
        L.line([(x+18*s, ly), (x+18*s+(cw-36*s)*ease_out(a), ly)], fill=GOLD, width=1.4*s, alpha=a)
        L.text((x+cw/2, ly+40*s), nm, F(SERIF_B, 28*s), fill=CREAM, alpha=a, anchor='ms')
        lit = ramp(t, tl+0.2, tl+0.5); ia = ramp(t, tl-0.15, tl+0.2)
        _icon(L, kind, (x+cw/2-F(SANS_B, 20*s).getlength(cap)/2-20*s, ly+76*s), s, ia, lit, t)
        L.text((x+cw/2+18*s, ly+83*s), cap, F(SANS_B, 20*s), fill=(255, 226, 170) if lit > 0.5 else BRIGHT, alpha=ia, anchor='ms')
    Lr = L.get()
    # push the portrait plane (with its text) about the portrait row
    M = lambda z: np.array([[z, 0, PC[0]*(1-z)], [0, z, PC[1]*(1-z)]], np.float32)
    pl = cv2.warpAffine(plate, M(zP), (W, H), flags=cv2.INTER_CUBIC); pmw = cv2.warpAffine(pm, M(zP), (W, H))[..., None]
    rgb = bg*(1-pmw)+pl
    Lw = cv2.warpAffine(Lr, M(zP), (W, H), flags=cv2.INTER_LINEAR)
    rgb = over(rgb, Lw, shadow=0.45)
    # foreground plane: out-of-focus molecules, faster push
    fg = fg_bokeh(W, H, t, ((-20, 680, 120), (1300, 60, 110)))
    rgb = over(rgb, cv2.warpAffine(fg, M(zF), (W, H)), shadow=0)
    rgb = over(rgb, drift_specks(W, H, t, 40, 21, (240, 220, 170), 0.26, 1.5, (8, -4)), shadow=0)
    # fixed plane: header, badge, footnote (never pushed out)
    Lh = Layer(W, H)
    Lh.rrect((W/2-330*s, 36*s, W/2+330*s, 140*s), 10*s, fill=(10, 12, 30), alpha=0.55*ramp(t, 0, 0.5))
    Lh.text((W/2, 74*s), '2026 年 10 月 5 日  ·  诺贝尔生理学或医学奖', F(SANS_B, 28*s), fill=GOLD, alpha=ramp(t, 0, 0.5), anchor='ms', tracking=2*s)
    fr = F(SERIF, 22*s); reason = '获奖理由：发现光控离子通道，并由此建立光遗传学'; tw = fr.getlength(reason)
    rx0 = W/2-tw/2+26*s
    Lh.text((rx0, 120*s), reason, fr, fill=CREAM, alpha=ramp(t, 0.9, 1.5), anchor='ls')
    ux0 = rx0+fr.getlength('获奖理由：发现'); ux1 = ux0+fr.getlength('光控离子通道'); kk = ease_out(ramp(t, 1.5, 2.1))
    Lh.line([(ux0, 130*s), (ux0+(ux1-ux0)*kk, 130*s)], fill=CYAN, width=2*s, alpha=ramp(t, 1.5, 1.7))
    Lh.text((W/2, H-12*s), '据诺贝尔奖官方新闻稿  ·  头像为插画', F(SANS, 20*s), fill=BRIGHT, alpha=ramp(t, 3.6, 4.2), anchor='ms')
    rgb = over(rgb, Lh.get(), shadow=0.45)
    # ChR2 badge: big at centre for the first beat, then settles left of the reason line
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
    return grade(rgb, seed=int(t*24))

# ================================================================================================
# SF07: exponential push from frame 0 (3.6 %/s on the brain plate)
# ================================================================================================
rerun10('sf07', [("z = 1.0+0.06*u+0.10*ease(ramp(t, 0.0, 5.0))", "z = math.exp(0.047*t)")])

# ================================================================================================
# SF08: 3 ticks at 26 px; route-two chip retires when the speed bar arrives
# ================================================================================================
# the speed-bar block lives in sf_r10's patched text; patch the tick list there and re-exec
_code8 = _R10SRC[_R10SRC.rindex("\n_s = src_of(", 0, _R10SRC.index("exec(compile(_s, 'sf_r10_sf08'"))+1:_R10SRC.index("exec(compile(_s, 'sf_r10_sf08'")]
for o, n in (("        bx, by, bw, bh = 40*s, 548*s, 640*s, 150*s", "        bx, by, bw, bh = 40*s, 540*s, 640*s, 158*s"),
             ("x0, x1 = bx+34*s, bx+bw-40*s; ay_ = by+bh-42*s", "x0, x1 = bx+44*s, bx+bw-56*s; ay_ = by+bh-50*s"),
             ("for q, tk in ((0.0, '1 ms'), (0.25, '10 ms'), (0.5, '100 ms'), (0.75, '1 s'), (1.0, '10 s')):",
              "for q, tk in ((0.0, '1 ms'), (0.5, '100 ms'), (1.0, '10 s')):"),
             ("L.text((x, ay_+28*s), tk, F(SANS, 20*s), fill=BRIGHT, alpha=a, anchor='ms')", "L.text((x, ay_+36*s), tk, F(SANS_B, 26*s), fill=BRIGHT, alpha=a, anchor='ms')")):
    assert o in _code8, o; _code8 = _code8.replace(o, n)
_code8 += "_s = sub(_s, \"chip('路线二 · 通道上外加化学光开关', MAG, b2)\", \"chip('路线二 · 通道上外加化学光开关', MAG, b2*(1-ramp(t, 4.35, 4.75)))\")\n"
_code8 += "exec(compile(_s, 'sf_r11_sf08', 'exec'), globals())\n"
exec(compile(_code8, 'rerun10_sf08b', 'exec'), R10.__dict__)

# ================================================================================================
# SF09: retinal smaller, set inside each helix bundle and seen through the helices; label hand-over
# ================================================================================================
_s9 = open(TOOLS+'sf_r8.py').read(); _s9 = _s9[_s9.index("@scene('SF09_chr2_channel'"):]
for o, n in (("t=ramp(t, 1.9, 2.7), font_size=LT*s, sub_size=LS*s, accent=(99, 199, 168)", "t=ramp(t, 0.2, 0.9), font_size=LT*s, sub_size=LS*s, accent=(99, 199, 168)"),
             ("'蓝光 约 470 nm', None, t=ramp(t, 0.4, 1.1)", "'蓝光 约 470 nm', None, t=ramp(t, 0.6, 1.2)"),
             ("    base8 = base.copy()\n", "    base8 = base.copy(); pre8 = base.copy()\n"),
             ("for (cx0, cy0, ang, flip) in ((0.394, 0.452, 38, False), (0.600, 0.458, -38, True)):",
              "for (cx0, cy0, ang, flip) in ((0.414, 0.455, 38, False), (0.580, 0.460, -38, True)):"),
             ("spr0, P0 = ret_sprite(0, int(0.085*iw), ang, flip); spr, P1 = ret_sprite(round(bend*20)/20, int(0.085*iw), ang, flip)",
              "spr0, P0 = ret_sprite(0, int(0.066*iw), ang, flip); spr, P1 = ret_sprite(round(bend*20)/20, int(0.066*iw), ang, flip)"),
             ("    rgb = cam(base8, W, H, zoom=z, cx=cxx, cy=cyy)\n",
              "    dm = np.clip(np.abs(base8-pre8).sum(2, keepdims=True)*8, 0, 1); dm = cv2.GaussianBlur(dm, (0, 0), 1.2)[..., None] if dm.ndim == 2 else cv2.GaussianBlur(dm[..., 0], (0, 0), 1.2)[..., None]\n"
              "    base8 = base8*(1-0.30*dm)+pre8*0.30*dm\n"
              "    rgb = cam(base8, W, H, zoom=z, cx=cxx, cy=cyy)\n"),
             ("for (rx, ry) in ((0.394, 0.452), (0.600, 0.458)):", "for (rx, ry) in ((0.414, 0.455), (0.580, 0.460)):"),
             ("X, Y = P(0.378, 0.432); label(L2, (X, Y), (60*s, 620*s), '视黄醛'", "X, Y = P(0.400, 0.445); label(L2, (X, Y), (60*s, 620*s), '视黄醛'"),
             ("'阳离子（如 Na⁺）', '门开后顺浓度梯度涌入细胞', t=ramp(t, 2.6, 3.4)", "'阳离子（如 Na⁺）', '门开后顺浓度梯度涌入细胞', t=ramp(t, 2.6, 3.3)")):
    assert o in _s9, o; _s9 = _s9.replace(o, n)
exec(compile(_s9, 'sf_r11_sf09', 'exec'), R9.__dict__)

# ================================================================================================
# SF10: magnifier = one neuron (soma, dendrites, axon) in the channel colour, flashing with each pulse
# ================================================================================================
def _orx11():
    if 'orx11' not in _cache:
        im = img('sf06t_neuron'); hsv = cv2.cvtColor((im*255).astype(np.uint8), cv2.COLOR_RGB2HSV).astype(np.int16)
        hsv[..., 0] = (hsv[..., 0]-14) % 180; hsv[..., 1] = np.clip(hsv[..., 1]*1.05, 0, 255)
        _cache['orx11'] = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2RGB).astype(np.float32)/255
    return _cache['orx11']
R10._orx11 = _orx11
rerun10('sf10', [("circ_img(img('sf10_orexin'), r, zoom=1.15+0.05*lin(t, 3), cx=0.5, cy=0.47)", "circ_img(_orx11(), r, zoom=1.55+0.10*lin(t, 3), cx=0.73, cy=0.53)"),
                 ("radial(W, H, C[0], C[1]-6*s, 70*s, CYAN, 0.5*pl*a)", "radial(W, H, C[0]+4*s, C[1]+4*s, 46*s, CYAN, 0.55*pl*a)")])

# ================================================================================================
# SF11: top-left crescent painted out (mirrored molecule ground); cornea label waits for the photoreceptor label
# ================================================================================================
rerun10('sf11', [
    ("lm = cv2.GaussianBlur(lm, (0, 0), 0.012*iw)[..., None]; _cache['eye7b'] = _e7*(1-lm)+sh*lm",
     "lm = cv2.GaussianBlur(lm, (0, 0), 0.012*iw)[..., None]; _b7 = _e7*(1-lm)+sh*lm\n"
     "        tl = np.zeros((ih, iw), np.float32); tl[:int(0.34*ih), :int(0.22*iw)] = 1; tl = cv2.GaussianBlur(tl, (0, 0), 0.02*iw)[..., None]\n"
     "        _cache['eye7b'] = _b7*(1-tl)+np.roll(_b7, -int(0.55*ih), axis=0)*tl"),
    ("'角膜、晶状体把光折向中央凹', None, t=ramp(t, 2.6, 3.3)", "'角膜、晶状体把光折向中央凹', None, t=ramp(t, 3.5, 4.1)"),
])

# ------------------------------------------------------------------------------------------------
# wrap every scene: round-9 wrapper (label scale + scene clock) + round-10 push multiplier
# ------------------------------------------------------------------------------------------------
def _wrap11(name, fn):
    def g(t, W, H, *a, **k):
        FR[0], FR[1] = W, H; r = PUSH.get(name); ZX[0] = math.exp(r*t) if r else None
        try: return fn(t, W, H, *a, **k)
        finally: ZX[0] = None
    g._r11 = True; return g
for _n in list(S):
    _fn, _d = S[_n]
    if getattr(_fn, '_r11', False): continue
    if not getattr(_fn, '_r10', False): _fn = R10._wrap10(_n, _fn)
    S[_n] = (_wrap11(_n, _fn), _d)
S['SF10_mouse_tripo'] = (S['SF10_mouse_tripo'][0], R10.SF10_D)
