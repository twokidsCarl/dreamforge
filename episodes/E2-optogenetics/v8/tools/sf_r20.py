"""Round 19 (PROMPT 第 19 轮, 2026-10-23): remove the three things fresh reviewers keep catching — SF10 two-plate
transition (now a single plate, no dissolve/flow), lumpy face skin on the portraits (procedural skin smoothing),
SF02 full-screen synchronous flash (now a travelling wave), SF07 static opening.  Each change kept only if both
calibrated reviewers re-score the shot higher.  Narration NOT changed."""
import sys, os, math; sys.path.insert(0, '/workspace/e2work/v8/tools')
import numpy as np, cv2
import sf_r19 as R19
from sf_r19 import S, R18, R17, R16, R15, R14, R12, R11, R10, _wrapped
TRY = set(x for x in os.environ.get('R19_TRY', '').split(',') if x)
ACCEPT = {'SF02'}
# re-scores (A / B): SF02 wave 92.45->92.60 / 91.35->91.50 (kept); SF07 fibre insertion 91.30->91.30 / 90.75->90.75 (no gain, not kept);
#   SF04 face smoothing 90.60->90.25 / 91.00->89.80 (reverted, not rolled out to SF05); SF10 single plate v1 91.20->91.00 / 90.05->89.35 (reverted);
#   SF10 single plate v2 (opaque lids) 91.20->91.20 / 90.05->89.70 (reverted, round-18 SF10 kept);
#   SF01 wider light spread 92.00->92.00 / 91.65->91.65 (no gain); SF11 label moved 91.15->90.65 / 91.25->90.85 (reverted: base re-run brought back an old eye fragment)

# ---- SF10: single-plate 2.5D (tools/sf10_single19.py -> gen/vid/sf10_single19.mp4) ----
def src10_19(t):
    return R12._fat('sf10_single19', t*24)
if 'SF10' in TRY or 'SF10' in ACCEPT:
    R18.src10_17 = src10_19
    def cam19(t):
        z = math.exp(0.044*t); hx = 0.5/z; hh = 0.4219/z
        cx = 0.47-0.02*R12.ease(min(1.0, max(0.0, (t-4.0)/5.0))); cy = 0.46
        return z, min(max(cx, hx+0.004), 1-hx-0.004), min(max(cy, hh+0.004), 1-hh-0.004)
    R10.CAM14 = cam19

# ---- SF04/SF05: face skin de-lumped procedurally (tools/face_smooth19.py), hair/clothes keep their lobes ----
FACE19 = {'sf04h_crick': 'r19_crick_face', 'sf05h_deisseroth': 'r19_face_deisseroth', 'sf05h_hegemann': 'r19_face_hegemann', 'sf05h_nagel': 'r19_face_nagel'}
def _face_map(keys):
    _ps = R12.port_split; mp = {k: FACE19[k] for k in keys}
    R12.port_split = lambda k: _ps(mp.get(k, k))
if 'SF04' in TRY or 'SF04' in ACCEPT:
    _face_map(['sf04h_crick'])
    R18.ANIM['sf04h_crick'] = R19.crick_anim18 if hasattr(R19, 'crick_anim18') else R18.ANIM['sf04h_crick']
if 'SF05' in TRY or 'SF05' in ACCEPT:
    _face_map(['sf05h_deisseroth', 'sf05h_hegemann', 'sf05h_nagel'])

# ---- SF07: the fibre is inserted from above during the first 0.6 s (plate without a painted fibre: gen/sf07k_brain.png);
#      tip glow only once it is in; magnifier swap slowed to 0.6 s ----
def sf07_v19():
    _sb = open('/workspace/e2work/v8/tools/sf_r12.py').read(); _a = _sb.index('def _brain12():'); _b = _sb.index("@scene('SF07_main_title'", _a)
    bsrc = _sb[_a:_b].replace("img('sf07h_brain')", "img('sf07k_brain')").replace("fw = int(0.07*w)", "fw = int(0.17*w)").replace("v = (i/fw)**1.5", "v = (i/fw)**2.2")
    exec(compile(bsrc, 'sf_r20_brain', 'exec'), R12.__dict__); R12._cache.pop('br12', None)
    src = open('/workspace/e2work/v8/tools/sf_r12.py').read(); a = src.index("@scene('SF07_main_title'"); b = src.index("# ====", a); src = src[a:b]
    o = "        L.ring((px, py), r, fill=CYAN, width=2.4*s, alpha=a)\n"
    src = src.replace(o, o+"        plate_text(L, (px, py+r+32*s), '神经元（放大）', F(SANS_B, 20*s), fill=CREAM, alpha=a*ramp(t, 0.9, 1.2)*(1-ramp(t, 1.75, 2.05)), anchor='ms')\n")
    for o, n in (("    L.line([(fx, -10), (fx, oy+0.09*h*sc)], fill=(20, 18, 40), width=7*s); L.line([(fx, -10), (fx, oy+0.09*h*sc)], fill=(120, 124, 150), width=4*s)",
                  "    ins = ease(ramp(t, 0.0, 0.6)); fend = -10+(fbot+10)*ins\n"
                  "    L.line([(fx, -10), (fx, fend)], fill=(20, 18, 40), width=9*s); L.line([(fx, -10), (fx, fend)], fill=(130, 134, 160), width=5*s)\n"
                  "    L.rrect((fx-8*s, fend-46*s, fx+8*s, fend-10*s), 3*s, fill=(160, 166, 190), alpha=1.0); L.dot((fx, fend), 4*s, fill=(200, 240, 255), alpha=ramp(t, 0.45, 0.7))"),
                 ("        p = (t*0.9+n/5) % 1.0; L.dot((fx, fbot*p), 2.6*s, fill=(210, 240, 255), alpha=min(1, (1-p)*6))",
                  "        p = (t*0.9+n/5) % 1.0; L.dot((fx, fbot*p), 2.6*s, fill=(210, 240, 255), alpha=min(1, (1-p)*6)*ramp(t, 0.6, 0.9))"),
                 ("    rgb = rgb+radial(W, H, fx, fbot, 50*s, CYAN, 0.32*(0.85+0.15*math.sin(t*4)))",
                  "    rgb = rgb+radial(W, H, fx, fbot, 50*s, CYAN, 0.32*(0.85+0.15*math.sin(t*4))*ramp(t, 0.5, 0.8))"),
                 ("alpha=a*(1-ease(ramp(t, 1.3, 1.8))))", "alpha=a*(1-ease(ramp(t, 1.3, 1.9))))"),
                 ("alpha=a*ease(ramp(t, 1.3, 1.8)))", "alpha=a*ease(ramp(t, 1.3, 1.9)))")):
        assert o in src, o; src = src.replace(o, n)
    exec(compile(src, 'sf_r20_sf07', 'exec'), R12.__dict__)
    return _wrapped('SF07_main_title', R12.S['SF07_main_title'][0])
if 'SF07' in TRY or 'SF07' in ACCEPT:
    S['SF07_main_title'] = (sf07_v19(), 5.0)

# ---- SF02: the synchronous burst becomes a wave travelling left -> right across the lit network; peak -30 %, ~8-frame rise ----
def _envw(T):
    p = np.mod((T-2.9)*1.25, 1.0)
    rise = np.clip((p-0.06)/0.42, 0, 1); rise = rise*rise*(3-2*rise)
    v = np.where(p < 0.06, 0.0, np.where(p < 0.48, 0.49*rise, 0.49*np.exp(-(p-0.48)/0.22)))
    return np.where(T < 2.9, 0.0, v)
R10._envw = _envw
def sf02_v19():
    R11.rerun10('sf02', [("max(0.0, math.sin((t-2.9)*2*math.pi*1.25))**4", "_env12(t)"),
                         ("alpha=0.7*(1-ph)*ramp(t, 2.9, 3.2)", "alpha=0.7*(1-ph)*min(1, ph*6)*ramp(t, 2.9, 3.2)"),
                         ("base = base+gm*sy*np.array([1.0, 0.74, 0.36])*0.30+gb*sy*np.array([1.0, 0.62, 0.25])*0.30",
                          "xw = np.linspace(0, 1, base.shape[1], dtype=np.float32)[None, :, None]; syw = ramp(t, 2.9, 3.3)*_envw(t-0.6*xw)\n"
                          "    base = base+gm*syw*np.array([1.0, 0.74, 0.36])*0.30+gb*syw*np.array([1.0, 0.62, 0.25])*0.30")])
    return _wrapped('SF02_1979_request', R10.S['SF02_1979_request'][0])
if 'SF02' in TRY or 'SF02' in ACCEPT:
    S['SF02_1979_request'] = (sf02_v19(), 5.0)

# ---- SF01: soft, wider light spread from the fibre tip so every lit (cyan) neuron sits inside the light ----
def _ov_sf01c(fn):
    def g(t, W, H):
        rgb = fn(t, W, H); a = R12.ramp(t, 0.8, 1.8)
        if a <= 0: return rgb
        s = W/1280; x0, y1 = int(0.70*W), int(0.15*H)
        reg = rgb[:y1, x0:]; sc = cv2.GaussianBlur(reg.min(2).astype(np.float32), (0, 0), 3*s)
        yy_, xx_ = np.unravel_index(np.argmax(sc), sc.shape); tx, ty = x0+xx_, yy_
        k = ('cone01', W, H)
        if k not in R12._cache: R12._cache[k] = np.mgrid[0:H, 0:W].astype(np.float32)
        Y, X = R12._cache[k]
        dx, dy = X-tx, Y-ty; ang = np.arctan2(dy, dx); d = np.hypot(dx, dy)/W
        a0, a1 = math.radians(95), math.radians(150)                     # between straight down-left-ish and left-down
        inside = np.clip(np.minimum(ang-a0, a1-ang)/math.radians(14), 0, 1)
        cone = inside*np.exp(-d/0.55)*np.clip(d/0.04, 0, 1)
        return np.clip(rgb+cone[..., None]*np.array([0.25, 0.55, 1.0])*0.16*a, 0, 1)
    g._r11 = True; return g
if 'SF01' in TRY or 'SF01' in ACCEPT:
    f, d = S['SF01_open_title']; S['SF01_open_title'] = (_ov_sf01c(f), d)

# ---- SF11: the ganglion-cell label moved off the fundus (lower left of the lens), re-using the round-13/18 SF11 build ----
def sf11_v19():
    R11.rerun10('sf11', [("(760*s, 440*s), '神经节细胞：膜上装了 ChrimsonR'", "(560*s, 470*s), '神经节细胞：膜上装了 ChrimsonR'")])
    import sf_r13 as R13
    src = open('/workspace/e2work/v8/tools/sf_r13.py').read(); a = src.index("@scene('SF11_eye_goggles'"); b = src.index("# ====", a); src = src[a:b]
    for o, n in (("C = (150*s, 150*s); R = int(112*s); a = ramp(t, 1.3, 1.9)", "C = (150*s, 150*s); R = int(112*s); a = ramp(t, 1.3, 1.9)*(1-ramp(t, 3.9, 4.4))"),
                 ("L2 = Layer(W, H); ta = ramp(t, 1.5, 2.1)", "L2 = Layer(W, H); ta = ramp(t, 1.5, 2.1)*(1-ramp(t, 3.9, 4.4))")):
        src = src.replace(o, n)
    exec(compile(src, 'sf_r20_sf11', 'exec'), R13.__dict__)
    return R18._ov_sf11(_wrapped('SF11_eye_goggles', R13.S['SF11_eye_goggles'][0]))
if 'SF11' in TRY or 'SF11' in ACCEPT:
    S['SF11_eye_goggles'] = (sf11_v19(), 5.0)
