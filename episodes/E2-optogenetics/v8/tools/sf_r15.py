"""Round 14 (PROMPT 第 14 轮, 2026-10-23): stop oscillating.  Frozen baseline = best version per shot:
SF01/SF03/SF04/SF05/SF07/SF10 = round 11 (styleframes/r11_backup); SF08/SF11 = round 13; SF02/SF06/SF09 unchanged.
Only zero-risk fixes on that baseline.  Narration NOT changed.
- SF10: the wake clip jumps from lying (src f82) to half-up (src f83) with no pose in between; round 11 hid it with a
  flow crossfade (f99 double tail), round 13 exposed it (H3).  Now: wake clip f0-76 -> R12's Wan 3.0 rise (its first
  frame IS wake f76: lying -> half-up, continuous) f0-75 -> new Wan 3.0 clip from the rise's f75 (half-up -> standing
  -> walking left; its last 3 frames snap to the target image and are not used).  No crossfades between poses;
  held frames skipped by a motion-weighted retime with optical-flow in-betweens.  Push >= 3 %/s.
- SF05: background layer was zoomed about y=0.555 -> its bottom ~40 px fell outside the image at zoom~1 (dark band
  shrinking with the push).  Centred instead (soft field, shift invisible).  Badge fades in over 7 frames.
  Footnote on a solid plate (>= 7:1).
- SF04: round-11 text kept (the three-line version cropped the citation under the push and lost '1999': reviewed
  87.5 < anchor 88.7, reverted); breathing + an early cyan light sweep added.
- SF08: round-13 version (single-metric timeline, 26 px ticks).
"""
import sys, os, math; sys.path.insert(0, '/workspace/e2work/v8/tools')
import numpy as np, cv2
import sf_r14 as R14                       # imports the R11 and R12 chains, snapshots S11, adds the R13 versions
from sf_r14 import S, S11, R12, R11, R10, R7
TOOLS = '/workspace/e2work/v8/tools/'

# ---- undo round-13 global patches that would leak into the round-11 functions ----
R12.port_split = R14._ps11                                     # R11 painted portraits (no bead swap)
_sb = open(TOOLS+'sf_r12.py').read(); _a = _sb.index('def _brain12():'); _b = _sb.index("@scene('SF07_main_title'", _a)
exec(compile(_sb[_a:_b], 'sf_r15_brain11', 'exec'), R12.__dict__)   # sf07h_brain again
R12.BT = (0.426, 0.255); R12._cache.pop('br12', None)

# ---- frozen baseline ----
for n in ('SF03_microbe_clues', 'SF07_main_title'):
    R14._use11(n)
# SF01 already R11 (sf_r14), SF08/SF11 = round 13 (sf_r14), SF02/SF06/SF09 unchanged

def _wrapped(name, fn):
    return R11._wrap11(name, R10._wrap10(name, fn))

# ================================================================================================
# SF04 (R11) : R11 text; breathing; early cyan light sweep over the portrait
# ================================================================================================
_s = R10.src_of('sf_r10.py', "@scene('SF04_crick_quote', 5.0)")
SF04_SUBS = (
    ("P0 = img('sf04g_crick')", "P0 = None"),
    ("Pc = cam(P0, pw, ph, zoom=1.02+0.08*u, cx=0.5+0.015*u, cy=0.47)",
     "Pc = port_view('sf04h_crick', pw, ph, 1.02+0.06*u, 0.5+0.012*u, 0.46, 1.0+0.045*ease(u)+0.006*math.sin(2*math.pi*t/3.1))\n"
     "    sw0 = ramp(t, 0.5, 2.1)\n"
     "    if 0 < sw0 < 1:\n"
     "        yy0, xx0 = np.mgrid[0:ph, 0:pw]; band0 = np.exp(-(((xx0+yy0*0.6)/pw-(-0.2+1.8*sw0))/0.09)**2)\n"
     "        Pc = np.clip(Pc+band0[..., None]*np.clip(Pc.mean(2, keepdims=True)-0.2, 0, 1)*np.array([0.55, 0.8, 1.0])*0.26, 0, 1)"),
    ("np.array([1.0, 0.8, 0.45])*0.6", "np.array([1.0, 0.8, 0.45])*0.30"),
    ("NC = (1112*s, 142*s); NR = int(100*s)", "NC = (1085*s, 172*s); NR = int(92*s)"),
    ("bx0, bx1, by = NC[0]-NR, NC[0]+NR, NC[1]+NR+30*s", "bx0, bx1, by = NC[0]-NR-330*s, NC[0]-NR-30*s, NC[1]-34*s"),
    ("    rgb = over(rgb, drift_specks(W, H, t, 45, 9, (240, 220, 180), 0.3, 1.6, (-10, -5)), shadow=0)\n",
     "    rgb = over(rgb, drift_specks(W, H, t, 45, 9, (240, 220, 180), 0.3, 1.6, (-10, -5)), shadow=0)\n"
     "    rgb = over(rgb, fg_bokeh(W, H, t, ((-40, 700, 140), (560, 760, 90))), shadow=0)\n"),
    ("    rgb = over(rgb, L2.get(), shadow=0.4)\n    return grade(rgb, seed=int(t*24))",
     "    rgb = over(rgb, L2.get(), shadow=0.4)\n    rgb = _cam0(np.clip(rgb, 0, 1), W, H, zoom=math.exp(0.020*t), cx=0.5, cy=0.5)\n    return grade(rgb, seed=int(t*24))"),
)
for o, n in SF04_SUBS:
    _s = R10.sub(_s, o, n)
exec(compile(_s, 'sf_r15_sf04', 'exec'), R12.__dict__)
S['SF04_crick_quote'] = (_wrapped('SF04_crick_quote', R12.S['SF04_crick_quote'][0]), 5.0)

# ================================================================================================
# SF05 (R11) : centred background layer (no bottom band); badge fades in; footnote on a solid plate
# ================================================================================================
_s5 = open(TOOLS+'sf_r12.py').read(); _a = _s5.index("@scene('SF05_nobel_portraits'"); _b = _s5.index("# ====", _a); _s5 = _s5[_a:_b]
for o, n in (
    ("bg = _cam0(bg, W, H, zoom=zB, cx=0.5, cy=PC[1]/H)", "bg = _cam0(bg, W, H, zoom=zB, cx=0.5, cy=0.5)"),
    ("Lb = Layer(W, H); ba = 1.0 if t > 0.05 else 0.0", "Lb = Layer(W, H); ba = ease(ramp(t, 0.0, 0.3))"),
    ("    plate_text(Lh, (W/2, H-16*s), '据诺贝尔奖官方新闻稿  ·  头像为插画', F(SANS, 20*s), fill=CREAM, alpha=ramp(t, 3.6, 4.2), anchor='ms')\n",
     "    fa_ = ramp(t, 3.6, 4.2); fn_ = F(SANS_B, 20*s); txt_ = '据诺贝尔奖官方新闻稿  ·  头像为插画'; tw_ = fn_.getlength(txt_)\n"
     "    if fa_ > 0:\n"
     "        Lh.rrect((W/2-tw_/2-14*s, H-46*s, W/2+tw_/2+14*s, H-14*s), 8*s, fill=(8, 10, 24), alpha=0.94*fa_)\n"
     "        Lh.text((W/2, H-23*s), txt_, fn_, fill=(250, 248, 242), alpha=fa_, anchor='ms')\n"),
):
    assert o in _s5, o; _s5 = _s5.replace(o, n)
exec(compile(_s5, 'sf_r15_sf05', 'exec'), R12.__dict__)
S['SF05_nobel_portraits'] = (_wrapped('SF05_nobel_portraits', R12.S['SF05_nobel_portraits'][0]), 5.0)

# ================================================================================================
# SF10 (R11 scene) : continuous rise -> stand -> walk, no pose crossfades
# ================================================================================================
_clip12 = R12._clip12
WK, RA, BR = 'sf10_wake11', 'sf10_riseA12', 'sf10_bridge13'
T_RA, T_BR, T_END = 3.933, 5.9, R10.SF10_D
SEG = {RA: (0, 75), BR: (0, 86)}          # bridge f87-89 snap to its last-frame target -> never used
_dis = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)
def _arcmap(name):
    """frame position for a 0..1 progress: Wan 3.0 output holds ~every other frame (15 fps effective), so the clip
    is retimed over cumulative motion (weights d^0.6; held frames add ~0) instead of frame count."""
    k = ('arc14', name)
    if k not in R12._cache:
        fr = _clip12(name); a, b = SEG[name]
        g = [cv2.cvtColor((cv2.resize(fr[i], (392, 261))*255).astype(np.uint8), cv2.COLOR_RGB2GRAY).astype(np.float32) for i in range(a, b+1)]
        d = np.array([np.abs(g[i+1]-g[i]).mean() for i in range(len(g)-1)])
        w = np.where(d < 0.12, 0.0, d)**0.6
        cum = np.concatenate([[0], np.cumsum(w)]); cum /= cum[-1]
        R12._cache[k] = (a, cum)
    return R12._cache[k]
def _flowpair(name, i):
    k = ('fl14', name, i)
    if k not in R12._cache:
        fr = _clip12(name); h, w = fr[i].shape[:2]
        A = cv2.cvtColor((fr[i]*255).astype(np.uint8), cv2.COLOR_RGB2GRAY); B = cv2.cvtColor((fr[i+1]*255).astype(np.uint8), cv2.COLOR_RGB2GRAY)
        R12._cache[k] = (_dis.calc(A, B, None), _dis.calc(B, A, None))
    return R12._cache[k]
def _interp(name, f):
    fr = _clip12(name); i = int(f); al = f-i
    if al < 0.02 or i+1 >= len(fr): return fr[min(i, len(fr)-1)]
    if al > 0.98: return fr[i+1]
    fab, fba = _flowpair(name, i); h, w = fr[i].shape[:2]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    Aw = cv2.remap(fr[i], xx+al*fba[..., 0], yy+al*fba[..., 1], cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    Bw = cv2.remap(fr[i+1], xx+(1-al)*fab[..., 0], yy+(1-al)*fab[..., 1], cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    return Aw*(1-al)+Bw*al
def _play(name, q):
    a, cum = _arcmap(name); q = min(max(q, 0.0), 1.0)
    f = float(np.interp(q, cum, np.arange(len(cum))))
    return _interp(name, a+f)
def src10_14(t):
    if t < 2.6: return R12._fat(WK, t*24/2.6)
    if t < 3.4: return R12._fat(WK, 24+(t-2.6)/0.8*36)
    if t < T_RA: return R12._fat(WK, 60+(t-3.4)/(T_RA-3.4)*16)
    if t < T_BR: return _play(RA, (t-T_RA)/(T_BR-T_RA))                    # RA f0 == wake f76: lying -> half-up
    return _play(BR, (t-T_BR)/(T_END-T_BR))                                # BR f0 == RA f75: half-up -> stand -> walk
R14.SF10_Z[:] = [1.02, 0.046]
def _sf10(t, W, H):
    if R12.src10 is not src10_14:
        R12.src10 = src10_14; R12._cache.pop('trk12', None)
    return R14._sf10_13(t, W, H)
_sf10._r11 = True
S['SF10_mouse_tripo'] = (_sf10, R10.SF10_D)

# ---- SF10 camera: follows the (heavily smoothed) implant track so the head and the cable stay in frame ----
def CAM14(t):
    pos = R12._track12()[0]
    k = ('cam14', len(pos))
    if k not in R12._cache:
        sm = np.stack([cv2.GaussianBlur(pos[:, i].reshape(-1, 1).astype(np.float64), (1, 0), 14).ravel() for i in (0, 1)], 1)
        R12._cache[k] = sm
    sm = R12._cache[k]; i = min(max(int(t*24), 0), len(sm)-1)
    px, py = sm[i]
    z = 1.0*math.exp(0.038*t)
    hx = 0.5/z; hh = 0.4219/z                                  # half-window (source-normalised; 16:9 out of 3:2)
    cx = min(max(px+0.07, hx+0.004), 1-hx-0.004)
    cy = min(0.5, py+0.44*hh); cy = min(max(cy, hh+0.004), 1-hh-0.004)
    return z, cx, cy
R10.CAM14 = CAM14
R11.rerun10('sf10', [
    ("circ_img(img('sf10_orexin'), r, zoom=1.15+0.05*lin(t, 3), cx=0.5, cy=0.47)", "circ_img(_orx11(), r, zoom=1.55+0.10*lin(t, 3), cx=0.73, cy=0.53)"),
    ("radial(W, H, C[0], C[1]-6*s, 70*s, CYAN, 0.5*pl*a)", "radial(W, H, C[0]+4*s, C[1]+4*s, 46*s, CYAN, 0.55*pl*a)"),
    ("L = Layer(W, H); C = (1100*s, 250*s); R = int(138*s)", "L = Layer(W, H); C = (205*s, 352*s); R = int(116*s)"),
    ("z = 1.04+0.05*lin(t, SF10_D); cxx = 0.55-0.05*lin(t, SF10_D); cyy = 0.50", "z, cxx, cyy = CAM14(t)"),
    ("cx_, cy_ = W*0.36, 112*s+120*s", "cx_, cy_ = W*0.74, 150*s"),
    ("L2.text((C[0], C[1]+R+34*s), '下丘脑外侧 · 食欲素神经元'", "plate_text(L2, (C[0], C[1]+R+34*s), '下丘脑外侧 · 食欲素神经元'"),
    ("L2.text((C[0], C[1]+R+62*s), '膜上装了光控通道，随光脉冲放电'", "plate_text(L2, (C[0]+6*s, C[1]+R+66*s), '膜上装了光控通道，随光脉冲放电'"),
])
_sf10_14 = _wrapped('SF10_mouse_tripo', R10.S['SF10_mouse_tripo'][0])
def _sf10b(t, W, H):
    if R12.src10 is not src10_14:
        R12.src10 = src10_14; R12._cache.pop('trk12', None)
    return _sf10_14(t, W, H)
_sf10b._r11 = True
S['SF10_mouse_tripo'] = (_sf10b, R10.SF10_D)
