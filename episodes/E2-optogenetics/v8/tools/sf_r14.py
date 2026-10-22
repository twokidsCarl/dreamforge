"""Round 13 (PROMPT 第 13 轮, 2026-10-23): stop the losses, take the better of R11/R12 per shot, then small steps.
Narration NOT changed.
Baseline: SF01/SF04/SF05/SF10 back to their round-11 versions (round-12 changes regressed); everything else from R12.
"""
import sys, os, math; sys.path.insert(0, '/workspace/e2work/v8/tools')
import sf, sf_scenes
from sf_scenes import S
import sf_r12 as R12                       # -> round-11 state
import sf_r10 as R10, sf_r11 as R11, sf_r7 as R7
S11 = dict(S)
_dk11 = R7._darkL
_src10_11 = R12.src10
_lbl11 = dict(R10.LBL)
_trk11 = R12._cache.get('trk12')
import sf_r13 as R13                       # -> round-12 state
S12 = dict(S)
_dk12 = R7._darkL
_src10_12 = R12.src10

def _use11(name, before=None):
    fn, d = S11[name]
    def g(t, W, H):
        if before: before()
        return fn(t, W, H)
    g._r11 = True
    S[name] = (g, d)

def _sf01_pre():
    R7._darkL = _dk11
def _sf10_pre():
    if R12.src10 is not _src10_11:
        R12.src10 = _src10_11; R12._cache.pop('trk12', None)
_use11('SF01_open_title', _sf01_pre)
_use11('SF04_crick_quote')
_use11('SF05_nobel_portraits')
_use11('SF10_mouse_tripo', _sf10_pre)

# ================================================================================================
# SF10: round-11 version; blink frames kept with eyes repainted open (no f99 double-tail crossfade); push >= 3 %/s
# (gen/vid/sf10_wake13.mp4 is made by tools/sf10_eyepatch13.py)
_fat, _bridge, _clip12 = R12._fat, R12._bridge, R12._clip12
WK13, WL11 = 'sf10_wake13', 'sf10_walk11'
def src10_13(t):
    if t < 2.6: return _fat(WK13, t*24/2.6)
    if t < 3.4: return _fat(WK13, 24+(t-2.6)/0.8*36)
    if t < 3.933: return _fat(WK13, 60+(t-3.4)/0.533*16)
    if t < 4.233: return _fat(WK13, 76+(t-3.933)/0.30*8)          # was a flow crossfade 76->84 (double tail)
    if t < 6.233: return _fat(WK13, 84+(t-4.233)*32.5)
    if t < 6.433: return _bridge(_clip12(WK13)[149], _clip12(WL11)[0], R12.ease((t-6.233)/0.2), 'brWL13')
    return _fat(WL11, (t-6.433)*30)
SF10_Z = [1.02, 0.046]
R11.rerun10('sf10', [
    ("circ_img(img('sf10_orexin'), r, zoom=1.15+0.05*lin(t, 3), cx=0.5, cy=0.47)", "circ_img(_orx11(), r, zoom=1.55+0.10*lin(t, 3), cx=0.73, cy=0.53)"),
    ("radial(W, H, C[0], C[1]-6*s, 70*s, CYAN, 0.5*pl*a)", "radial(W, H, C[0]+4*s, C[1]+4*s, 46*s, CYAN, 0.55*pl*a)"),
    ("L = Layer(W, H); C = (1100*s, 250*s); R = int(138*s)", "L = Layer(W, H); C = (205*s, 352*s); R = int(116*s)"),
    ("z = 1.04+0.05*lin(t, SF10_D); cxx = 0.55-0.05*lin(t, SF10_D); cyy = 0.50", "z = SF10_Z[0]*math.exp(SF10_Z[1]*t); cxx = 0.54-0.03*ease(lin(t, SF10_D)); cyy = 0.50"),
    ("cx_, cy_ = W*0.36, 112*s+120*s", "cx_, cy_ = W*0.74, 150*s"),
    ("L2.text((C[0], C[1]+R+34*s), '下丘脑外侧 · 食欲素神经元'", "plate_text(L2, (C[0], C[1]+R+34*s), '下丘脑外侧 · 食欲素神经元'"),
    ("L2.text((C[0], C[1]+R+62*s), '膜上装了光控通道，随光脉冲放电'", "plate_text(L2, (C[0]+6*s, C[1]+R+66*s), '膜上装了光控通道，随光脉冲放电'"),
])
R10.SF10_Z = SF10_Z
_sf10_13 = R11._wrap11('SF10_mouse_tripo', R10._wrap10('SF10_mouse_tripo', R10.S['SF10_mouse_tripo'][0]))
def _sf10(t, W, H):
    if R12.src10 is not src10_13:
        R12.src10 = src10_13; R12._cache.pop('trk12', None)
    return _sf10_13(t, W, H)
_sf10._r11 = True
S['SF10_mouse_tripo'] = (_sf10, R10.SF10_D)

# ================================================================================================
# SF04 / SF05: round-11 layouts, portraits swapped for bead-built (Goodsell) heads — the style that won the isolated
# family-fit judgement (review/r13_family: beads B 86 > silhouette 72 > round-11 painted head 50)
# ================================================================================================
PORT13 = {'sf04h_crick': 'r13s_crick_beads', 'sf05h_deisseroth': 'sf05m_deisseroth',
          'sf05h_hegemann': 'sf05m_hegemann', 'sf05h_nagel': 'sf05m_nagel'}
_ps11 = R12.port_split
def _ps13(key):
    k2 = PORT13.get(key, key)
    if k2 == key: return _ps11(key)
    k = ('ps13', k2)
    if k not in R12._cache:
        im, ground, msk = _ps11(k2 if 'deisseroth' not in k2 else k2)
        R12._cache[k] = (im, ground, msk)
    return R12._cache[k]
R12.port_split = _ps13

# ================================================================================================
# SF07: new dorsal brain plate (tools/sf07_brain13.py -> gen/sf07i_brain.png): symmetric hemispheres, bulbs on the
# frontal poles, colliculi + foliated cerebellum; fibre tip at (0.420, 0.300)
# ================================================================================================
_sb = open(TOOLS13 if False else '/workspace/e2work/v8/tools/sf_r12.py').read()
_a = _sb.index('def _brain12():'); _b = _sb.index("@scene('SF07_main_title'", _a)
exec(compile(_sb[_a:_b].replace("img('sf07h_brain')", "img('sf07i_brain')"), 'sf_r14_brain', 'exec'), R12.__dict__)
R12.BT = (0.420, 0.300); R12._cache.pop('br12', None)

# ================================================================================================
# SF05: round-11 source + solid footnote plate (>= 7:1); bottom ~9 px dark strip removed by a 1.3 % uniform scale
# about the top centre (round 12's per-column max smeared the footnote into a "barcode" — not used)
# ================================================================================================
_s5 = open('/workspace/e2work/v8/tools/sf_r12.py').read(); _a = _s5.index("@scene('SF05_nobel_portraits'"); _b = _s5.index("# ====", _a); _s5 = _s5[_a:_b]
_o = "    plate_text(Lh, (W/2, H-16*s), '据诺贝尔奖官方新闻稿  ·  头像为插画', F(SANS, 20*s), fill=CREAM, alpha=ramp(t, 3.6, 4.2), anchor='ms')\n"
assert _o in _s5
_s5 = _s5.replace(_o, "    fa_ = ramp(t, 3.6, 4.2); fn_ = F(SANS_B, 20*s); txt_ = '据诺贝尔奖官方新闻稿  ·  头像为插画'; tw_ = fn_.getlength(txt_)\n"
                      "    if fa_ > 0:\n"
                      "        Lh.rrect((W/2-tw_/2-14*s, H-50*s, W/2+tw_/2+14*s, H-18*s), 8*s, fill=(8, 10, 24), alpha=0.94*fa_)\n"
                      "        Lh.text((W/2, H-27*s), txt_, fn_, fill=(250, 248, 242), alpha=fa_, anchor='ms')\n")
exec(compile(_s5, 'sf_r14_sf05', 'exec'), R12.__dict__)
_sf05_13 = R11._wrap11('SF05_nobel_portraits', R10._wrap10('SF05_nobel_portraits', R12.S['SF05_nobel_portraits'][0]))
import cv2 as _cv2, numpy as _np
def _sf05(t, W, H):
    rgb = _sf05_13(t, W, H)
    n = int(math.ceil(11*H/720)); k = H/(H-n); W2 = int(round(W*k))
    big = _cv2.resize(_np.ascontiguousarray(rgb[:H-n]), (W2, H), interpolation=_cv2.INTER_CUBIC)
    x0 = (W2-W)//2
    return _np.clip(big[:, x0:x0+W], 0, 1)
_sf05._r11 = True
S['SF05_nobel_portraits'] = (_sf05, 5.0)

# ================================================================================================
# SF08: round-12 two-route version, but the timeline compares ONE quantity (light -> response delay): need ms vs
# route one (relay) seconds; route two's cost (drug first, minutes to settle) is a separate note, not a bar on the
# same axis.  Tick text 26 px (>= 2.5 % of frame height); route-one leader ends on the relay proteins.
# ================================================================================================
_s8 = R13._s8
for o, n in (("Q = lambda lg: x0+(x1-x0)*(lg+3)/5.78                    # log10 seconds: 1 ms .. 10 min",
              "Q = lambda lg: x0+(x1-x0)*(lg+3)/4.3                     # log10 seconds: 1 ms .. ~20 s"),
             ("for lg, tk, an in ((-3, '1 ms', 'ls'), (-1, '100 ms', 'ms'), (1, '10 s', 'ms'), (2.78, '10 分钟', 'rs')):",
              "for lg, tk, an in ((-3, '1 ms', 'ls'), (-2, '10 ms', 'ms'), (-1, '100 ms', 'ms'), (0, '1 s', 'ms'), (1, '10 s', 'ms')):"),
             ("L.text((x if an != 'ls' else x-4*s, ay_+32*s), tk, F(SANS_B, 22*s), fill=BRIGHT, alpha=a, anchor=an)",
              "L.text((x if an != 'ls' else x-4*s, ay_+34*s), tk, F(SANS_B, 26*s), fill=BRIGHT, alpha=a, anchor=an)"),
             ("L.text((bx+22*s, by+34*s), '能做到毫秒级吗？', F(SANS_B, 22*s), fill=CREAM, alpha=a, anchor='ls')",
              "L.text((bx+22*s, by+34*s), '光一来，多久起作用？', F(SANS_B, 22*s), fill=CREAM, alpha=a, anchor='ls')\n"
              "        na_ = a*ramp(t, 5.9, 6.5)\n"
              "        if na_ > 0:\n"
              "            L.text((bx+bw-20*s, by+34*s), '路线二：每次先给药，等几分钟才就位', F(SANS_B, 20*s), fill=(250, 175, 235), alpha=na_, anchor='rs')\n"),
             ("                (by+130*s, 1.78, 2.78, MAG, (250, 175, 235), '路线二 · 先给药：分钟级', 'l', 5.9, 6.5))",
              ")"),
             ("rows = ((by+62*s,", "rows = ((by+70*s,"), ("(by+96*s, -0.5, 1.0,", "(by+112*s, -0.5, 1.0,"),
             ("X1, Y1 = P(0.29, 0.43); label(", "X1, Y1 = P(0.262, 0.528); label(")):
    assert o in _s8, o; _s8 = _s8.replace(o, n)
exec(compile(_s8, 'sf_r14_sf08', 'exec'), R10.__dict__)
S['SF08_early_attempts'] = (R11._wrap11('SF08_early_attempts', R10._wrap10('SF08_early_attempts', R10.S['SF08_early_attempts'][0])), S12['SF08_early_attempts'][1])

# ================================================================================================
# SF03: 'H⁺ 被一个一个泵到膜外' stays from 1.3 s to the last frame (was ~1 s); SF11: photoreceptor label held ~2.6 s
# ================================================================================================
_s3 = open('/workspace/e2work/v8/tools/sf_r12.py').read(); _a = _s3.index("@scene('SF03_microbe_clues'"); _b = _s3.index("# ====", _a); _s3 = _s3[_a:_b]
_o = "alpha=ramp(t, 1.6, 1.85)*(1-ramp(t, 2.45, 2.7)))"; assert _o in _s3
_s3 = _s3.replace(_o, "alpha=ramp(t, 1.3, 1.55))")
exec(compile(_s3, 'sf_r14_sf03', 'exec'), R12.__dict__)
S['SF03_microbe_clues'] = (R11._wrap11('SF03_microbe_clues', R10._wrap10('SF03_microbe_clues', R12.S['SF03_microbe_clues'][0])), 5.0)
R10.LBL[('SF11_eye_goggles', '感光细胞：已大量丢失')] = 4.0
