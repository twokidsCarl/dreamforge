"""Round 15 (PROMPT 第 15 轮, 2026-10-23): small steps on the round-14 baseline; each change kept only if both
calibrated reviewers re-score that shot higher.  Narration NOT changed.
"""
import sys, os, math; sys.path.insert(0, '/workspace/e2work/v8/tools')
import numpy as np, cv2
import sf_r15 as R15
from sf_r15 import S, R14, R12, R11, R10
KEEP = {}            # shot -> True once its re-score beat the baseline (filled in below as results come in)

def _wrapped(name, fn):
    return R11._wrap11(name, R10._wrap10(name, fn))

# ================================================================================================
# SF08 v15: whole chain stays in frame (push from the full frame, no right pan); lighter timeline overlay with
# light pulses running along each bar, one axis "start -> neurons respond" with all three rows (route two drawn);
# top-left chip inside the 5 % safe area
# ================================================================================================
def sf08_v15():
    s8 = R14._s8
    a = s8.index("    a = ramp(t, 4.4, 4.9)\n    if a > 0:\n        bx, by, bw, bh"); b = s8.index("    return grade(over(rgb, L.get()), seed=int(t*24))", a)
    new = '''    a = ramp(t, 4.4, 4.9)
    if a > 0:
        bx, by, bw, bh = 40*s, 492*s, 650*s, 192*s
        L.rrect((bx, by, bx+bw, by+bh), 14*s, fill=(10, 14, 34), alpha=0.62*a)
        L.text((bx+22*s, by+32*s), '从开始到神经元有反应，要多久？', F(SANS_B, 22*s), fill=CREAM, alpha=a, anchor='ls')
        x0, x1 = bx+46*s, bx+bw-46*s; ay_ = by+bh-48*s
        Q = lambda lg: x0+(x1-x0)*(lg+3)/5.78                    # log10 seconds: 1 ms .. 10 min
        L.line([(x0, ay_), (x1, ay_)], fill=(150, 160, 190), width=1.4*s, alpha=0.8*a)
        for lg, tk, an in ((-3, '1 ms', 'ls'), (0, '1 秒', 'ms'), (1.78, None, 'ms'), (2.78, '10 分钟', 'rs')):
            x = Q(lg); L.line([(x, ay_-5*s), (x, ay_+5*s)], fill=(150, 160, 190), width=1.4*s, alpha=a)
            if tk: L.text((x if an != 'ls' else x-4*s, ay_+33*s), tk, F(SANS_B, 26*s), fill=BRIGHT, alpha=a, anchor=an)
        rows = ((by+64*s, -3.0, -2.6, CYAN, (150, 210, 255), '需要：毫秒级', 'r', 4.4, 4.9),
                (by+98*s, -0.5, 1.0, (255, 180, 120), (255, 210, 170), '路线一 · 接力：秒级', 'l', 4.9, 5.5),
                (by+132*s, 1.78, 2.78, MAG, (250, 175, 235), '路线二 · 先给药：分钟级', 'l', 5.6, 6.2))
        for j, (yy_, l0, l1, col, tcol, txt, side, t0, t1) in enumerate(rows):
            g = ease_out(ramp(t, t0, t1)); ra = a*ramp(t, t0-0.1, t0+0.2)
            if ra <= 0: continue
            xa0, xa1 = Q(l0), Q(l1); xe = xa0+max(6*s, (xa1-xa0)*g)
            L.rrect((xa0, yy_-5*s, xe, yy_+5*s), 5*s, fill=col, alpha=0.85*ra)
            for n in range(3):                                     # light pulses running along the bar
                p = ((t*0.9+n/3+j*0.27) % 1.0)
                L.dot((xa0+(xe-xa0)*p, yy_), 4.2*s, fill=(255, 255, 255), alpha=ra*min(1, p*6)*min(1, (1-p)*6)*0.9)
            if side == 'r': L.text((xa1+14*s, yy_+7*s), txt, F(SANS_B, 20*s), fill=tcol, alpha=ra, anchor='ls')
            else: L.text((xa0-14*s, yy_+7*s), txt, F(SANS_B, 20*s), fill=tcol, alpha=ra, anchor='rs')
        xm = Q(-2.6)+3*s; L.line([(xm, by+46*s), (xm, ay_)], fill=(140, 200, 255), width=1.2*s, alpha=0.5*a)
'''
    s8 = s8[:a]+new+s8[b:]
    for o, n in (("    z = 1.10*math.exp(0.021*t); cxx = 0.462+(0.520-0.462)*pan; cyy = 0.47\n",
                  "    z = max(1.0, math.exp(0.026*(t-0.8))); cxx = 0.5-0.03*ease(lin(t, 7)); cxx = min(max(cxx, 0.5/z), 1-0.5/z); cyy = 0.47\n"),
                 ("L.rrect((40*s, 30*s, 40*s+tw, 76*s), 23*s", "L.rrect((40*s, 44*s, 40*s+tw, 90*s), 23*s"),
                 ("L.dot((62*s, 53*s), 6*s, fill=col, alpha=a)", "L.dot((62*s, 67*s), 6*s, fill=col, alpha=a)"),
                 ("L.text((78*s, 61*s), txt, F(SANS_B, 22*s), fill=CREAM, alpha=a, anchor='ls')", "L.text((78*s, 75*s), txt, F(SANS_B, 22*s), fill=CREAM, alpha=a, anchor='ls')")):
        assert o in s8, o; s8 = s8.replace(o, n)
    exec(compile(s8, 'sf_r16_sf08', 'exec'), R10.__dict__)
    return _wrapped('SF08_early_attempts', R10.S['SF08_early_attempts'][0])

# ================================================================================================
# SF02 v15: synchronous bursts with a ~5-frame smooth attack and 30 % lower peak (was 2-3 frames -> strobe)
# ================================================================================================
def _env15(t):
    p = ((t-2.9)*1.25) % 1.0
    if p < 0.08: return 0.0
    if p < 0.34: return 0.7*R12.ease((p-0.08)/0.26)
    return 0.7*math.exp(-(p-0.34)/0.24)

# ================================================================================================
# SF04 v15: more motion — drifting molecule ground behind the portrait, stronger portrait parallax, more specks
# ================================================================================================
def sf04_v15():
    _s = R10.src_of('sf_r10.py', "@scene('SF04_crick_quote', 5.0)")
    for o, n in R15.SF04_SUBS + (
        ("rgb = rgb*0.6+fam_bg(W, H)*0.32+radial(W, H, W*(0.32-0.05*u), H*0.45, W*0.26, (60, 70, 150), 0.22)",
         "rgb = rgb*0.6+_cam0(fam_bg(W, H), W, H, zoom=1.06*math.exp(0.03*t), cx=0.5+0.035*math.sin(t*0.55), cy=0.5-0.02*u)*0.34+radial(W, H, W*(0.32-0.05*u), H*0.45, W*0.26, (60, 70, 150), 0.22)"),
        ("1.0+0.045*ease(u)+0.006*math.sin(2*math.pi*t/3.1)", "1.0+0.075*ease(u)+0.008*math.sin(2*math.pi*t/3.1)"),
        ("drift_specks(W, H, t, 45, 9, (240, 220, 180), 0.3, 1.6, (-10, -5))", "drift_specks(W, H, t, 85, 9, (240, 220, 180), 0.34, 1.8, (-16, -8))"),
    ):
        _s = R10.sub(_s, o, n)
    exec(compile(_s, 'sf_r16_sf04', 'exec'), R12.__dict__)
    return _wrapped('SF04_crick_quote', R12.S['SF04_crick_quote'][0])

# ================================================================================================
# SF03 v15: 'H⁺ 被一个一个泵到膜外' stays to the last frame; bottom captions lifted 16 px off the edge
# ================================================================================================
def sf03_v15():
    _s3 = open('/workspace/e2work/v8/tools/sf_r12.py').read(); _a = _s3.index("@scene('SF03_microbe_clues'"); _b = _s3.index("# ====", _a); _s3 = _s3[_a:_b]
    for o, n in (("alpha=ramp(t, 1.6, 1.85)*(1-ramp(t, 2.45, 2.7)))", "alpha=ramp(t, 1.6, 1.85))"),
                 ("card(40*s, 636*s,", "card(40*s, 620*s,"), ("card(1240*s, 636*s,", "card(1240*s, 620*s,")):
        assert o in _s3, o; _s3 = _s3.replace(o, n)
    exec(compile(_s3, 'sf_r16_sf03', 'exec'), R12.__dict__)
    return _wrapped('SF03_microbe_clues', R12.S['SF03_microbe_clues'][0])

# ================================================================================================
# SF07 v15: the magnifier's first stage (neurons, before it pushes onto the channel) gets a label
# ================================================================================================
def sf07_v15():
    src = open('/workspace/e2work/v8/tools/sf_r12.py').read(); a = src.index("@scene('SF07_main_title'"); b = src.index("# ====", a); src = src[a:b]
    o = "        L.ring((px, py), r, fill=CYAN, width=2.4*s, alpha=a)\n"
    assert o in src
    src = src.replace(o, o+"        plate_text(L, (px, py+r+32*s), '神经元（放大）', F(SANS_B, 20*s), fill=CREAM, alpha=a*ramp(t, 0.9, 1.2)*(1-ramp(t, 1.75, 2.05)), anchor='ms')\n")
    exec(compile(src, 'sf_r16_sf07', 'exec'), R12.__dict__)
    return _wrapped('SF07_main_title', R12.S['SF07_main_title'][0])

V15 = {'SF08_early_attempts': sf08_v15, 'SF04_crick_quote': sf04_v15, 'SF03_microbe_clues': sf03_v15, 'SF07_main_title': sf07_v15}
DUR = {'SF07_main_title': 5.0, 'SF08_early_attempts': 7.0, 'SF04_crick_quote': 5.0, 'SF03_microbe_clues': 5.0, 'SF02_1979_request': 5.0}
ACCEPT = {'SF08_early_attempts', 'SF02_1979_request', 'SF03_microbe_clues', 'SF04_crick_quote', 'SF07_main_title', 'SF11_eye_goggles',
          'SF11b', 'SF06_switch_diagram', 'SF05_nobel_portraits'}
# round-15 re-scores (A / B): SF08 90.35->90.90 / 89.45->90.60; SF02 92.30->92.45 / 91.05->91.35;
#                            SF03 92.05->92.30 / 90.75->91.25; SF04 88.45->88.95 / 88.70->89.15;
#                            SF07 90.55->90.80 / 90.15->90.40; SF11 90.75->90.90 / 90.60->90.75;
#                            SF06 92.00->92.15 / 92.15->92.15; SF11b 90.90->91.15 / 90.75->91.00
#                            SF05 90.45->90.65 / 90.60->90.80
# tried, not submitted: SF10 rim light + ink contour on the mouse (mask too blocky on the lighter fur)
TRY = set(x for x in os.environ.get('R15_TRY', '').split(',') if x)
for _n, _f in V15.items():
    if _n in ACCEPT or _n[:4] in TRY:
        S[_n] = (_f(), DUR[_n])
if 'SF02_1979_request' in ACCEPT or 'SF02' in TRY:
    R10._env12 = _env15

# ================================================================================================
# SF11 v15: the two amber beams enter parallel, bend a little at the cornea and clearly at the lens (refraction)
# ================================================================================================
EYE15 = [[(0.135, 0.350), (0.300, 0.353), (0.405, 0.392), (0.684, 0.478)],
         [(0.135, 0.510), (0.300, 0.506), (0.405, 0.470), (0.684, 0.478)]]
if 'SF11_eye_goggles' in ACCEPT or 'SF11' in TRY:
    R10.EYE7[:] = EYE15

# ================================================================================================
# SF06 v15: the "?" magnifier arrives at 0.5-1.2 s (was 1.3-2.1 s; the first 2 s were title-only)
# ================================================================================================
def sf06_v15():
    R11.rerun10('sf06', [("rgb = glow(rgb, 0.7, W/70, 0.3*on)", "rgb = glow(rgb, 0.80, W/100, 0.14*on)"),
                         ("np.array([0.25, 0.65, 1.0])*0.32*", "np.array([0.25, 0.65, 1.0])*0.22*"),
                         ("    L2.rrect((40*s, 40*s, 80*s+tw0, 102*s), 8*s, fill=(10, 13, 30), alpha=0.82*ta)\n    L2.line([(40*s, 40*s), (40*s, 102*s)], fill=CYAN, width=3*s, alpha=ta)\n", ""),
                         ("    a = ramp(t, 1.3, 2.1)", "    a = ramp(t, 0.5, 1.2)")])
    return _wrapped('SF06_switch_diagram', R10.S['SF06_switch_diagram'][0])
if 'SF06_switch_diagram' in ACCEPT or 'SF06' in TRY:
    S['SF06_switch_diagram'] = (sf06_v15(), 6.0)

# SF11 v15b: photoreceptor-loss label held to the last frame (was fading at 4.0 s)
if 'SF11b' in TRY or 'SF11b' in ACCEPT:
    R10.LBL[('SF11_eye_goggles', '感光细胞：已大量丢失')] = 99.0

# ================================================================================================
# SF05 v15: Hegemann's background channel recoloured to the violet of the other membrane proteins (it crowded his
# head); the three portraits start fading in at 0 s (the first 0.4 s were nearly empty)
# ================================================================================================
def sf05_v15():
    _ps = R12.port_split
    def ps15(key):
        return _ps('sf05p_hegemann' if key == 'sf05h_hegemann' else key)
    R12.port_split = ps15
    src = R15._s5
    o = "a = ramp(t, 0.2+i*0.3, 0.9+i*0.3)"; assert o in src
    src = src.replace(o, "a = ramp(t, 0.0+i*0.22, 0.6+i*0.22)")
    exec(compile(src, 'sf_r16_sf05', 'exec'), R12.__dict__)
    return _wrapped('SF05_nobel_portraits', R12.S['SF05_nobel_portraits'][0])
if 'SF05_nobel_portraits' in ACCEPT or 'SF05' in TRY:
    S['SF05_nobel_portraits'] = (sf05_v15(), 5.0)
