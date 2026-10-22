"""Round 18 v2 (sf10_lobe25d2): sleeping mouse composited onto the awake plate background (only the mouse region
transitions), 1.0 s local morph, head looks +/-9 deg, ear twitches, whisker tremble.
Round 17 SF10 candidate: lobe-built mouse animated in 2.5D from two image2 plates (no per-frame regeneration,
so the lobe texture never 'boils').  Output gen/vid/sf10_lobe25d.mp4 at 24 fps, 1176x784, SF10 timing:
  0-3.6 s asleep (r16_sf10_k0) with breathing | 3.6-4.3 s optical-flow morph to the awake plate (head lifts, eyes open)
  | 4.3-9.4 s awake (r16_sf10_k76): breathing, looks left (5.0 s), right (6.4 s), up toward the fibre (7.8 s)."""
import sys, math; sys.path.insert(0, '/workspace/e2work/v8/tools')
import numpy as np, cv2, subprocess
G = '/workspace/e2work/v8/gen/'; SZ = (1176, 784); FPS = 24; N = int(round(9.4*FPS))+2
A = cv2.resize(cv2.imread(G+'r16_sf10_k0.png'), SZ, interpolation=cv2.INTER_AREA).astype(np.float32)
B = cv2.resize(cv2.imread(G+'r16_sf10_k76.png'), SZ, interpolation=cv2.INTER_AREA).astype(np.float32)
h, w = A.shape[:2]; yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
dis = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)
ga, gb = cv2.cvtColor(A.astype(np.uint8), cv2.COLOR_BGR2GRAY), cv2.cvtColor(B.astype(np.uint8), cv2.COLOR_BGR2GRAY)
fab, fba = dis.calc(ga, gb, None), dis.calc(gb, ga, None)
ease = lambda x: 0.5-0.5*math.cos(math.pi*min(1, max(0, x)))
def body_weight(img):
    hsv = cv2.cvtColor(img.astype(np.uint8), cv2.COLOR_BGR2HSV)
    m = ((hsv[..., 2] < 120) & (hsv[..., 1] < 170) & (yy > 0.25*h)).astype(np.float32)
    m = cv2.GaussianBlur(cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((25, 25), np.uint8)), (0, 0), 18)
    return np.clip(m*1.4, 0, 1)
WA, WB = body_weight(A), body_weight(B)
MU = np.clip(cv2.GaussianBlur(np.maximum(WA, WB), (0, 0), 10)*1.6, 0, 1)[..., None]     # union of both mouse regions
A = A*MU+B*(1-MU)                                                                        # sleeping mouse on the awake background
def breathe(img, wgt, t, base=0.66):
    s = 0.011*math.sin(2*math.pi*t/1.7)
    sy = (yy+(yy-base*h)*s*wgt).astype(np.float32)
    return cv2.remap(img, xx, sy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
# head of the awake plate: pivot at the neck (found from the implant: head centre ~ below the implant ferrule)
hsvB = cv2.cvtColor(B.astype(np.uint8), cv2.COLOR_BGR2HSV)
fer = ((hsvB[..., 1] < 70) & (hsvB[..., 2] > 150) & (yy < 0.45*h) & (yy > 0.15*h) & (xx > 0.33*w) & (xx < 0.62*w)).astype(np.uint8)
ys, xs = np.nonzero(fer); FX, FY = (np.median(xs), np.median(ys)) if len(xs) else (0.45*w, 0.3*h)
PIV = (FX+0.02*w, FY+0.22*h)
def head_turn(img, ang, lift):
    d = np.hypot((xx-(PIV[0]-0.05*w))/(0.19*w), (yy-(PIV[1]-0.10*h))/(0.20*h))
    wgt = np.clip(1.3-d, 0, 1); wgt = wgt*wgt*(3-2*wgt)
    a = math.radians(ang)*wgt; ca, sa = np.cos(a), np.sin(a)
    sx = PIV[0]+(xx-PIV[0])*ca+(yy-PIV[1])*sa; sy = PIV[1]-(xx-PIV[0])*sa+(yy-PIV[1])*ca+lift*h*wgt
    return cv2.remap(img, sx.astype(np.float32), sy.astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
hsv2 = hsvB
ear = (((hsv2[..., 0] > 160) | (hsv2[..., 0] < 8)) & (hsv2[..., 1] > 60) & (hsv2[..., 2] > 120) & (yy < 0.48*h)).astype(np.uint8)
ear = cv2.morphologyEx(ear, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
n_, lab_, st_, cen_ = cv2.connectedComponentsWithStats(ear)
EARS = sorted([(st_[i, cv2.CC_STAT_AREA], i) for i in range(1, n_)], reverse=True)[:2]
EAR = []
for _, i in EARS:
    x, y, ww, hh, _a = st_[i]; m = cv2.GaussianBlur(cv2.dilate((lab_ == i).astype(np.uint8), np.ones((9, 9), np.uint8)).astype(np.float32), (0, 0), 4)
    EAR.append(((x+ww/2, y+hh), m))                                     # pivot = bottom centre of the ear
nose = (((hsv2[..., 0] > 160) | (hsv2[..., 0] < 8)) & (hsv2[..., 1] > 60) & (yy > 0.3*h) & (xx < FX)).astype(np.uint8)
ys_, xs_ = np.nonzero(nose); NOSE = (float(np.median(xs_)), float(np.median(ys_))) if len(xs_) else (FX-0.1*w, FY+0.25*h)
def twitch(img, t):
    out = img
    for k, (pv, m) in enumerate(EAR):
        a = 0.0
        for t0 in ((5.3, 7.1, 8.6) if k == 0 else (5.9, 7.9)):
            x = (t-t0)/0.35
            if 0 < x < 1: a += math.sin(math.pi*x)*7.0*(1 if k == 0 else -1)
        if a == 0: continue
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        sx = (pv[0]+(xx-pv[0])*ca+(yy-pv[1])*sa).astype(np.float32); sy = (pv[1]-(xx-pv[0])*sa+(yy-pv[1])*ca).astype(np.float32)
        r = cv2.remap(out, sx, sy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT); mm = cv2.remap(m, sx, sy, cv2.INTER_LINEAR)[..., None]
        out = out*(1-mm)+r*mm
    # whisker tremble around the snout
    d = np.hypot(xx-NOSE[0]+0.03*w, yy-NOSE[1]); wgt = np.clip(1-d/(0.10*w), 0, 1)**2
    dy = (1.3*math.sin(2*math.pi*9*t)*wgt).astype(np.float32)
    return cv2.remap(out, xx, yy+dy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
def frame(t):
    if t < 3.6: return breathe(A, WA, t)
    if t < 4.6:
        al = ease((t-3.6)/1.0)
        Aw = cv2.remap(breathe(A, WA, t), xx+al*fba[..., 0], yy+al*fba[..., 1], cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        Bw = cv2.remap(B, xx+(1-al)*fab[..., 0], yy+(1-al)*fab[..., 1], cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        wb = ease((al-0.25)/0.5)
        return (Aw*(1-wb)+Bw*wb)*MU+B*(1-MU)
    look = (9.0*ease((t-4.9)/0.6)-9.0*ease((t-6.0)/0.7)*2+9.0*ease((t-7.4)/0.6))      # left, right, back to centre
    lift = -0.012*ease((t-7.6)/0.6)*(1-ease((t-8.8)/0.5))                                 # glance up toward the fibre
    return head_turn(twitch(breathe(B, WB, t), t), look, lift)
p = subprocess.Popen(['ffmpeg', '-loglevel', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{w}x{h}', '-r', str(FPS), '-i', '-',
                      '-c:v', 'libx264', '-crf', '10', '-pix_fmt', 'yuv444p', G+'vid/sf10_lobe25d2.mp4'], stdin=subprocess.PIPE)
for i in range(N): p.stdin.write(np.clip(frame(i/FPS), 0, 255).astype(np.uint8).tobytes())
p.stdin.close(); p.wait(); print('ok', N, 'ferrule', FX, FY)
