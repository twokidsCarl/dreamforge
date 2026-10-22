"""Round 16 (PROMPT 第 16 轮, 2026-10-23): zero-risk fixes first, then a targeted portrait/mouse family redraw,
sample -> calibrated re-score -> roll out only if it gains.  Narration NOT changed."""
import sys, os, math; sys.path.insert(0, '/workspace/e2work/v8/tools')
import numpy as np, cv2
import sf_r16 as R16
from sf_r16 import S, R15, R14, R12, R11, R10, _wrapped
TRY = set(x for x in os.environ.get('R16_TRY', '').split(',') if x)
ACCEPT = {'SF08_early_attempts', 'SF10_mouse_tripo'}
# round-16 re-scores (A / B): SF08 90.90->91.05 / 90.60->91.00; SF10 90.50->90.90 / 89.65->89.80;
# SF10 lobe-mouse (R16_SF10 candidate) re-scored 91.20 / 89.30 (grey patch, texture boiling); repaired version showed new
#   frame-jump spikes (f115, f167) and a negative push reading -> not adopted; SF05 90.65->90.65 / 90.80->90.80 (no gain -> R15 kept)

# ---- SF05: ChR2 badge flies to the header by 0.7 s; Hegemann fades in only after it has passed ----
def sf05_v16():
    src = R15._s5
    for o, n in (("a = ramp(t, 0.2+i*0.3, 0.9+i*0.3)", "a = ramp(t, (0.0, 0.72, 0.30)[i], (0.6, 1.3, 0.9)[i])"),
                 ("k = ease(ramp(t, 0.5, 1.3))", "k = ease(ramp(t, 0.1, 0.7))")):
        assert o in src, o; src = src.replace(o, n)
    exec(compile(src, 'sf_r17_sf05', 'exec'), R12.__dict__)
    return _wrapped('SF05_nobel_portraits', R12.S['SF05_nobel_portraits'][0])

# ---- SF08: route two = preparation time (dashed bar), title asks the ms question; no route-two "response" bar ----
def sf08_v16():
    import inspect
    src = inspect.getsource(R16.sf08_v15)
    for o, n in (("'从开始到神经元有反应，要多久？'", "'能做到毫秒级吗？'"),
                 ("'路线二 · 先给药：分钟级'", "'路线二 · 每次先给药，等几分钟才就位'"),
                 ("            L.rrect((xa0, yy_-5*s, xe, yy_+5*s), 5*s, fill=col, alpha=0.85*ra)\n",
                  "            if j < 2: L.rrect((xa0, yy_-5*s, xe, yy_+5*s), 5*s, fill=col, alpha=0.85*ra)\n"
                  "            else:\n"
                  "                xd = xa0\n"
                  "                while xd < xe:\n"
                  "                    L.line([(xd, yy_), (min(xd+9*s, xe), yy_)], fill=col, width=4*s, alpha=0.85*ra); xd += 15*s\n"),
                 ("        L.text((bx+22*s, by+32*s),", "        L.text((bx+bw-22*s, by+32*s), '虚线 = 用之前的准备时间', F(SANS, 18*s), fill=(214, 200, 236), alpha=a*ramp(t, 5.6, 6.2), anchor='rs')\n        L.text((bx+22*s, by+32*s),"),
                 ("def sf08_v15():", "def _sf08_v16():")):
        assert o in src, o; src = src.replace(o, n)
    ns = dict(R16.__dict__); exec(compile(src, 'sf_r17_sf08', 'exec'), ns)
    return ns['_sf08_v16']()

# ---- SF10: smooth light pulses (raised cosine, soft train edges) instead of a hard 5 Hz square wave; more room ahead
#      of the nose at the end ----
def soft_pulses(t, t0, t1, hz=5.0, on=0.06):
    if t < t0 or t > t1: return 0.0
    edge = min(1.0, (t-t0)/0.25, (t1-t)/0.25)
    ph = ((t-t0)*hz) % 1.0
    return edge*(0.35+0.65*(0.5+0.5*math.cos(2*math.pi*ph))**2)
CAM16_RATE = [0.038]
CAM16_SIG = [14]
def cam16(t):
    pos = R12._track12()[0]
    k = ('cam16', len(pos), CAM16_SIG[0])
    if k not in R12._cache:
        R12._cache[k] = np.stack([cv2.GaussianBlur(pos[:, i].reshape(-1, 1).astype(np.float64), (1, 0), CAM16_SIG[0]).ravel() for i in (0, 1)], 1)
    sm = R12._cache[k]; i = min(max(int(t*24), 0), len(sm)-1); px, py = sm[i]
    z = 1.0*math.exp(CAM16_RATE[0]*t); hx = 0.5/z; hh = 0.4219/z
    off = 0.07-0.06*R12.ease(min(1.0, max(0.0, (t-6.0)/2.5)))     # mouse faces left: window moves left ahead of the nose
    cx = min(max(px+off, hx+0.004), 1-hx-0.004)
    cy = min(0.5, py+0.44*hh); cy = min(max(cy, hh+0.004), 1-hh-0.004)
    return z, cx, cy

def apply():
    if 'SF05' in TRY or 'SF05_nobel_portraits' in ACCEPT: S['SF05_nobel_portraits'] = (sf05_v16(), 5.0)
    if 'SF08' in TRY or 'SF08_early_attempts' in ACCEPT: S['SF08_early_attempts'] = (sf08_v16(), 7.0)
    if 'SF10' in TRY or 'SF10_mouse_tripo' in ACCEPT:
        R10.pulses = soft_pulses; R10.CAM14 = cam16
apply()

# ---- SF04 portrait direction (samples c1 beads / c2 spheres / c3 lobes); chosen by calibrated re-score ----
SF04_PORT = os.environ.get('R16_SF04', '')            # e.g. r13s_crick_beads | r16_crick_spheres | r16_crick_lobes
SF04_WIN = 'r16_crick_lobes_ink'   # re-scores (A / B): v1 beads 89.40/89.80, v2 spheres 88.50/88.75, v3 lobes 89.60/90.15,
                                   # v3b lobes+ink outlines+note 90.00/90.50 -> mean 90.25 >= 89.03+1 -> adopted
def _set_sf04_port(key):
    if not key: return
    _ps = R12.port_split
    def ps(k):
        return _ps(key if k == 'sf04h_crick' else k)
    R12.port_split = ps
_set_sf04_port(SF04_PORT or SF04_WIN)

# ---- SF04 v3b: lobes portrait with dark indigo cluster outlines + a small '头像为插画' note ----
def _sf04_note(fn):
    def g(t, W, H):
        rgb = fn(t, W, H); s = W/1280; a = R12.ramp(t, 3.6, 4.2)
        if a <= 0: return rgb
        L = R12.Layer(W, H)
        R12.plate_text(L, (70*s, H-46*s), '头像为插画', R12.F(R12.SANS, 18*s), fill=(236, 238, 248), alpha=a, anchor='ls')
        return R12.over(rgb, L.get(), shadow=0)
    g._r11 = True; return g
if os.environ.get('R16_SF04NOTE') or SF04_WIN:
    _f, _d = S['SF04_crick_quote']; S['SF04_crick_quote'] = (_sf04_note(_f), _d)

# ---- SF05: the SF04 winner rolled out (lobe-built heads with ink outlines) ----
SF05_PORT = {'sf05h_deisseroth': 'r16_lobes_deisseroth_ink', 'sf05h_hegemann': 'r16_lobes_hegemann_ink', 'sf05h_nagel': 'r16_lobes_nagel_ink'}
SF05_WIN = True    # re-scores (A / B): 90.65->91.10 / 90.80->91.45 -> adopted
if os.environ.get('R16_SF05') or SF05_WIN:
    _ps5 = R12.port_split
    def _ps5w(k):
        return _ps5(SF05_PORT.get(k, k))
    R12.port_split = _ps5w

# ================================================================================================
# SF10 v16 candidate: lobe-built mouse (image2 restyled keyframes sf10_r16_k* -> three Wan 3.0 clips):
#   wake16 (asleep -> eyes open), rise16 (eyes open lying -> half up; its eyes-shut frames 42-48 are skipped),
#   walk16 (half up -> stand -> walk left).  Last 3 frames of first/last-frame clips are not used (target snap).
#   Same retime (motion-weighted, flow in-betweens) and follow camera as round 14/15.
# ================================================================================================
_dis16 = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)
SEQ16 = {'sf10_wake16s': list(range(0, 147)), 'sf10_rise16s': list(range(0, 42))+list(range(49, 147)), 'sf10_walk16s': list(range(0, 90))}
def _arc16(name, a, b):
    k = ('arc16', name, a, b)
    if k not in R12._cache:
        fr = R12._clip12(name); seq = SEQ16[name][a:b+1]
        g = [cv2.cvtColor((cv2.resize(fr[i], (392, 261))*255).astype(np.uint8), cv2.COLOR_RGB2GRAY).astype(np.float32) for i in seq]
        d = np.array([np.abs(g[i+1]-g[i]).mean() for i in range(len(g)-1)])
        w = np.where(d < 0.12, 0.0, d)**0.6
        cum = np.concatenate([[0], np.cumsum(w)]); cum /= max(cum[-1], 1e-6)
        R12._cache[k] = (seq, cum)
    return R12._cache[k]
def _pair16(name, i, j):
    k = ('fl16', name, i, j)
    if k not in R12._cache:
        fr = R12._clip12(name)
        A = cv2.cvtColor((fr[i]*255).astype(np.uint8), cv2.COLOR_RGB2GRAY); B = cv2.cvtColor((fr[j]*255).astype(np.uint8), cv2.COLOR_RGB2GRAY)
        R12._cache[k] = (_dis16.calc(A, B, None), _dis16.calc(B, A, None))
    return R12._cache[k]
def _play16(name, a, b, q):
    seq, cum = _arc16(name, a, b); q = min(max(q, 0.0), 1.0)
    f = float(np.interp(q, cum, np.arange(len(cum)))); n = int(f); al = f-n
    fr = R12._clip12(name)
    if al < 0.02 or n+1 >= len(seq): return fr[seq[min(n, len(seq)-1)]]
    if al > 0.98: return fr[seq[n+1]]
    i, j = seq[n], seq[n+1]; fab, fba = _pair16(name, i, j); h, w = fr[i].shape[:2]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    Aw = cv2.remap(fr[i], xx+al*fba[..., 0], yy+al*fba[..., 1], cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    Bw = cv2.remap(fr[j], xx+(1-al)*fab[..., 0], yy+(1-al)*fab[..., 1], cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    return Aw*(1-al)+Bw*al
def src10_16(t):
    if t < 2.6: return _play16('sf10_wake16s', 0, 30, t/2.6)                       # asleep, slowed
    if t < 3.4: return _play16('sf10_wake16s', 30, 90, (t-2.6)/0.8)                # time skip ("几十秒后")
    if t < 4.3: return _play16('sf10_wake16s', 90, 146, (t-3.4)/0.9)               # eyes open, lifts head
    if t < 6.1: return _play16('sf10_rise16s', 0, len(SEQ16['sf10_rise16s'])-1, (t-4.3)/1.8)
    return _play16('sf10_walk16s', 0, 89, (t-6.1)/(R10.SF10_D-6.1))
if os.environ.get('R16_SF10'):
    CAM16_RATE[0] = float(os.environ.get('R16_SF10_RATE', '0.038'))
    R10.frame10 = lambda ct: np.clip(R12.src10(ct), 0, 1).astype(np.float32)      # lobe clips: no Wan glow -> no HSV patch
    def cam16s(t):                                   # scripted path (the implant tracker drifts on these clips)
        z = math.exp(CAM16_RATE[0]*t); hx = 0.5/z; hh = 0.4219/z
        cx = 0.50-0.10*R12.ease(min(1.0, max(0.0, (t-5.6)/3.8))); cy = 0.47-0.03*R12.ease(min(1.0, max(0.0, (t-3.6)/2.6)))
        return z, min(max(cx, hx+0.004), 1-hx-0.004), min(max(cy, hh+0.004), 1-hh-0.004)
    R10.CAM14 = cam16s
    CAM16_SIG[0] = 26
    def _sf10c(t, W, H):
        if R12.src10 is not src10_16:
            R12.src10 = src10_16; R12._cache.pop('trk12', None)
        return R15._sf10_14(t, W, H)
    _sf10c._r11 = True
    S['SF10_mouse_tripo'] = (_sf10c, R10.SF10_D)
