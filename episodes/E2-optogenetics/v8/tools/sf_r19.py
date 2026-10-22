"""Round 18 (PROMPT 第 18 轮, 2026-10-23): continue subject animation; each change kept only if both calibrated
reviewers re-score the shot higher.  Narration NOT changed."""
import sys, os, math; sys.path.insert(0, '/workspace/e2work/v8/tools')
import numpy as np, cv2
import sf_r18 as R18
from sf_r18 import S, R17, R16, R15, R14, R12, R11, R10, _wrapped
TRY = set(x for x in os.environ.get('R18_TRY', '').split(',') if x)
ACCEPT = {'SF10', 'SF07', 'SF01', 'SF08', 'SF11'}   # SF11 91.15->91.15 / 91.15->91.25; SF01 91.75->92.00 / 91.40->91.65; SF08 91.20->91.45 / 91.10->91.20
# re-scores (A / B): SF10 v2 91.05->91.20 / 89.90->90.05 (kept); SF07 symmetric brain 90.80->91.30 / 90.40->90.75 (kept);
#   SF04 V1(small lobes)+BEAT 90.60->90.60 / 91.00->91.00 and V2('smooth face')+BEAT 90.60 / 91.00 (no gain, R17 portrait kept)

# ---- SF10 v2: local wake transition, visible head looks, ear twitches, whisker tremble (tools/sf10_lobe25d2.py) ----
def src10_18(t):
    return R12._fat('sf10_lobe25d2', t*24)
if 'SF10' in TRY or 'SF10' in ACCEPT:
    R18.src10_17 = src10_18            # the round-17 SF10 wrapper looks this name up at call time
    def cam18(t):
        z = math.exp(0.040*t); hx = 0.5/z; hh = 0.4219/z
        cx = 0.47-0.02*R12.ease(min(1.0, max(0.0, (t-4.0)/5.0))); cy = 0.46
        return z, min(max(cx, hx+0.004), 1-hx-0.004), min(max(cy, hh+0.004), 1-hh-0.004)
    R10.CAM14 = cam18

# ---- SF04/SF05 portraits: V1 = lobes ~60 % smaller, V2 = 'smooth face' attempt (image2 kept fine beads on the face);
#      inked with the same Canny outline pass ----
PORT18 = {'V1': {'sf04h_crick': 'r18_crick_small_ink', 'sf05h_deisseroth': 'r18_small_deisseroth_ink', 'sf05h_hegemann': 'r18_small_hegemann_ink', 'sf05h_nagel': 'r18_small_nagel_ink'},
          'V2': {'sf04h_crick': 'r18_crick_smoothface_ink', 'sf05h_deisseroth': 'r18_smoothface_deisseroth_ink', 'sf05h_hegemann': 'r18_smoothface_hegemann_ink', 'sf05h_nagel': 'r18_smoothface_nagel_ink'}}
for _v in ('V1', 'V2'):
    if _v in TRY or _v in ACCEPT:
        _ps18 = R12.port_split; _map = PORT18[_v]
        R12.port_split = (lambda ps, mp: (lambda k: ps(mp.get(k, k))))(_ps18, _map)

# ---- second action beat: Crick's head comes back level toward the viewer after the nod (3.6-4.6 s);
#      the laureates turn toward the frame centre one after another from 3.0 s ----
def crick_anim18(t):
    up = R18._ease((t-0.8)/1.2); nod = math.sin(math.pi*min(1, max(0, (t-2.6)/1.0))); back = R18._ease((t-3.6)/1.0)
    return (-4.0*up*(1-back)+2.2*nod+1.2*back, (0.014*up-0.010*nod)*(1-back)-0.006*back, 0.0)
def laureate_anim18(i):
    f0 = R18.laureate_anim(i)
    def f(t):
        ang, dy, rim = f0(t)
        turn = R18._ease((t-3.0-i*0.3)/0.7)
        return (ang+(-3.5, 0.0, 3.5)[i]*turn, dy-0.004*turn*(i == 1), rim)
    return f
if 'BEAT' in TRY or 'BEAT' in ACCEPT:
    R18.ANIM['sf04h_crick'] = crick_anim18
    for i, k in enumerate(('sf05h_deisseroth', 'sf05h_hegemann', 'sf05h_nagel')):
        R18.ANIM[k] = laureate_anim18(i)

# ---- SF07: symmetric dorsal brain (tools/sf07_sym18.py -> gen/sf07j_brain.png) + wider plate feather (no hard edge) ----
if 'SF07' in TRY or 'SF07' in ACCEPT:
    _sb = open('/workspace/e2work/v8/tools/sf_r12.py').read(); _a = _sb.index('def _brain12():'); _b = _sb.index("@scene('SF07_main_title'", _a)
    _src = _sb[_a:_b].replace("img('sf07h_brain')", "img('sf07j_brain')").replace("fw = int(0.07*w)", "fw = int(0.17*w)").replace("v = (i/fw)**1.5", "v = (i/fw)**2.2")
    exec(compile(_src, 'sf_r19_brain', 'exec'), R12.__dict__)
    R12._cache.pop('br12', None)

# ---- SF08: timeline card -> one thin strip; the three bars on one axis, each labelled directly (no legend) ----
STRIP = '''    a = ramp(t, 4.4, 4.9)
    if a > 0:
        bx, by, bw, bh = 40*s, 592*s, 700*s, 96*s
        L.rrect((bx, by, bx+bw, by+bh), 12*s, fill=(10, 14, 34), alpha=0.55*a)
        L.text((bx+18*s, by-12*s), '能做到毫秒级吗？', F(SANS_B, 22*s), fill=CREAM, alpha=a, anchor='ls')
        x0, x1 = bx+44*s, bx+bw-44*s; ay_ = by+58*s
        Q = lambda lg: x0+(x1-x0)*(lg+3)/5.78
        L.line([(x0, ay_), (x1, ay_)], fill=(150, 160, 190), width=1.4*s, alpha=0.8*a)
        for lg, tk, an in ((-3, '1 ms', 'ms'), (0, '1 秒', 'ms'), (2.78, '10 分钟', 'ms')):
            x = Q(lg); L.line([(x, ay_-4*s), (x, ay_+4*s)], fill=(150, 160, 190), width=1.4*s, alpha=a)
            L.text((x, ay_+30*s), tk, F(SANS_B, 20*s), fill=BRIGHT, alpha=a, anchor=an)
        bars = ((-3.0, -2.6, CYAN, (150, 210, 255), '需要：毫秒级', 4.4, 4.9, False),
                (-0.5, 1.0, (255, 180, 120), (255, 210, 170), '路线一：秒级', 4.9, 5.5, False),
                (1.78, 2.78, MAG, (250, 175, 235), '路线二：先给药', 5.6, 6.2, True))
        for j, (l0, l1, col, tcol, txt, t0, t1, dash) in enumerate(bars):
            g = ease_out(ramp(t, t0, t1)); ra = a*ramp(t, t0-0.1, t0+0.2)
            if ra <= 0: continue
            xa0, xa1 = Q(l0), Q(l1); xe = xa0+max(6*s, (xa1-xa0)*g)
            if not dash: L.rrect((xa0, ay_-5*s, xe, ay_+5*s), 5*s, fill=col, alpha=0.9*ra)
            else:
                xd = xa0
                while xd < xe:
                    L.line([(xd, ay_), (min(xd+9*s, xe), ay_)], fill=col, width=5*s, alpha=0.9*ra); xd += 15*s
            for n in range(3):
                p = ((t*0.9+n/3+j*0.27) % 1.0)
                L.dot((xa0+(xe-xa0)*p, ay_), 4.0*s, fill=(255, 255, 255), alpha=ra*min(1, p*6)*min(1, (1-p)*6)*0.9)
            if j == 0: L.text((xa0-4*s, ay_-16*s), txt, F(SANS_B, 19*s), fill=tcol, alpha=ra, anchor='ls')
            elif j == 1: L.text((xa0-4*s, ay_-16*s), txt, F(SANS_B, 19*s), fill=tcol, alpha=ra, anchor='ls')
            else: L.text((xa1+8*s, ay_-16*s), txt, F(SANS_B, 19*s), fill=tcol, alpha=ra, anchor='rs')
'''
def sf08_v18():
    s8 = R14._s8
    for o, n in (("'路线一：好几步接力', '感光蛋白 → 中间几步 → 通道', t=ramp(t, 4.9, 5.5)", "'路线一：好几步接力', '感光蛋白 → 中间几步 → 通道', t=ramp(t, 3.1, 3.6)"),
                 ("'受紫光弯折 → 通道打开', None, t=ramp(t, 5.4, 6.0)", "'受紫光弯折 → 通道打开', None, t=ramp(t, 5.4, 6.0)*(1-ramp(t, 6.4, 6.8))")):
        assert o in s8, o; s8 = s8.replace(o, n)
    a = s8.index("    a = ramp(t, 4.4, 4.9)\n    if a > 0:\n        bx, by, bw, bh"); b = s8.index("    return grade(over(rgb, L.get()), seed=int(t*24))", a)
    s8 = s8[:a]+STRIP+s8[b:]
    for o, n in (("    z = 1.10*math.exp(0.021*t); cxx = 0.462+(0.520-0.462)*pan; cyy = 0.47\n",
                  "    z = max(1.0, math.exp(0.026*(t-0.8))); cxx = 0.5-0.03*ease(lin(t, 7)); cxx = min(max(cxx, 0.5/z), 1-0.5/z); cyy = 0.47\n"),
                 ("L.rrect((40*s, 30*s, 40*s+tw, 76*s), 23*s", "L.rrect((40*s, 44*s, 40*s+tw, 90*s), 23*s"),
                 ("L.dot((62*s, 53*s), 6*s, fill=col, alpha=a)", "L.dot((62*s, 67*s), 6*s, fill=col, alpha=a)"),
                 ("L.text((78*s, 61*s), txt, F(SANS_B, 22*s), fill=CREAM, alpha=a, anchor='ls')", "L.text((78*s, 75*s), txt, F(SANS_B, 22*s), fill=CREAM, alpha=a, anchor='ls')")):
        assert o in s8, o; s8 = s8.replace(o, n)
    exec(compile(s8, 'sf_r19_sf08', 'exec'), R10.__dict__)
    return _wrapped('SF08_early_attempts', R10.S['SF08_early_attempts'][0])
if 'SF08' in TRY or 'SF08' in ACCEPT:
    S['SF08_early_attempts'] = (sf08_v18(), 7.0)

# ---- SF01: the light source reads as a torch -> label it '光纤' (tracked to its glowing tip each frame) ----
def _ov_sf01(fn):
    def g(t, W, H):
        rgb = fn(t, W, H); a = R12.ramp(t, 1.6, 2.2)
        if a <= 0: return rgb
        s = W/1280; x0, y1 = int(0.70*W), int(0.15*H)
        reg = rgb[:y1, x0:]; sc = cv2.GaussianBlur(reg.min(2).astype(np.float32), (0, 0), 3*s)
        yy_, xx_ = np.unravel_index(np.argmax(sc), sc.shape); tx, ty = x0+xx_, yy_
        L = R12.Layer(W, H)
        lx, ly = tx-120*s, ty+58*s
        L.line([(tx-14*s, ty+10*s), (lx+34*s, ly-8*s)], fill=(200, 230, 255), width=1.4*s, alpha=0.8*a)
        R12.plate_text(L, (lx, ly), '光纤', R12.F(R12.SANS_B, 20*s), fill=(236, 240, 250), alpha=a, anchor='ms')
        return np.clip(R12.over(rgb, L.get(), shadow=0), 0, 1)
    g._r11 = True; return g
if 'SF01' in TRY or 'SF01' in ACCEPT:
    f, d = S['SF01_open_title']; S['SF01_open_title'] = (_ov_sf01(f), d)

# ---- SF11: the goggles circle + caption fade out after 3.9 s (final frame: 2 labels + 1 circle instead of 3 + 2) ----
def sf11_v18():
    src = open('/workspace/e2work/v8/tools/sf_r13.py').read(); a = src.index("@scene('SF11_eye_goggles'"); b = src.index("# ====", a); src = src[a:b]
    for o, n in (("C = (150*s, 150*s); R = int(112*s); a = ramp(t, 1.3, 1.9)", "C = (150*s, 150*s); R = int(112*s); a = ramp(t, 1.3, 1.9)*(1-ramp(t, 3.9, 4.4))"),
                 ("L2 = Layer(W, H); ta = ramp(t, 1.5, 2.1)", "L2 = Layer(W, H); ta = ramp(t, 1.5, 2.1)*(1-ramp(t, 3.9, 4.4))")):
        assert o in src, o; src = src.replace(o, n)
    import sf_r13 as R13
    exec(compile(src, 'sf_r19_sf11', 'exec'), R13.__dict__)
    return R18._ov_sf11(_wrapped('SF11_eye_goggles', R13.S['SF11_eye_goggles'][0]))
if 'SF11' in TRY or 'SF11' in ACCEPT:
    S['SF11_eye_goggles'] = (sf11_v18(), 5.0)
