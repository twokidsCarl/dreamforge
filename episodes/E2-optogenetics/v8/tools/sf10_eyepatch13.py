"""Round 13 SF10: the round-11 wake clip closes its eyes on source frames 77-83 (round 11 cut them and bridged
76->84 with a flow crossfade = the f99 double-tail ghost).  Here those frames are kept (real Wan motion of the tail
and body, no dissolve) and only the eyes are repainted open: eye patches from f76 / f84, placed by ECC-tracking the
head.  Output: gen/vid/sf10_wake13.mp4 (lossless-ish, same 784x522 @30)."""
import cv2, numpy as np, subprocess
V = '/workspace/e2work/v8/gen/vid/'
cap = cv2.VideoCapture(V+'sf10_wake11.mp4'); fr = []
while True:
    ok, f = cap.read()
    if not ok: break
    fr.append(f)
H, W = fr[0].shape[:2]
EYES = {76: [(395, 275), (325, 270)], 84: [(365, 260), (290, 255)]}
def refine(ref, guess):
    # snap eye centre to darkest blob near the guess
    g = cv2.GaussianBlur(cv2.cvtColor(fr[ref], cv2.COLOR_BGR2GRAY), (0, 0), 3)
    x, y = guess; r = 22; win = g[y-r:y+r, x-r:x+r]; yy, xx = np.unravel_index(np.argmin(win), win.shape)
    return (x-r+xx, y-r+yy)
for k in EYES: EYES[k] = [refine(k, e) for e in EYES[k]]
print('eyes', EYES)
def track(ref, i):
    # translation of the head between ref and i (ECC on a head box, eyes masked out)
    x0, y0 = min(e[0] for e in EYES[ref])-90, min(e[1] for e in EYES[ref])-90
    box = (max(0, x0), max(0, y0), 240, 190)
    a = cv2.cvtColor(fr[ref], cv2.COLOR_BGR2GRAY).astype(np.float32); b = cv2.cvtColor(fr[i], cv2.COLOR_BGR2GRAY).astype(np.float32)
    msk = np.zeros_like(a, np.uint8); x, y, w, h = box; msk[y:y+h, x:x+w] = 255
    for (ex, ey) in EYES[ref]: cv2.circle(msk, (ex, ey), 26, 0, -1)
    M = np.eye(2, 3, dtype=np.float32)
    try: _, M = cv2.findTransformECC(cv2.GaussianBlur(a, (0, 0), 2), cv2.GaussianBlur(b, (0, 0), 2), M, cv2.MOTION_TRANSLATION,
                                     (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 200, 1e-5), msk, 5)
    except cv2.error as e: print('ecc fail', i, e)
    return M[0, 2], M[1, 2]
out = [f.copy() for f in fr]
for i in range(77, 84):
    ref = 76 if i <= 79 else 84
    dx, dy = track(ref, i)
    src = fr[ref].astype(np.float32); dst = out[i].astype(np.float32)
    sh = cv2.warpAffine(src, np.float32([[1, 0, dx], [0, 1, dy]]), (W, H), borderMode=cv2.BORDER_REFLECT)
    m = np.zeros((H, W), np.float32)
    for k, (ex, ey) in enumerate(EYES[ref]):
        rx, ry = (24, 20) if k == 0 else (17, 17)
        cv2.ellipse(m, (int(ex+dx), int(ey+dy)), (rx, ry), 0, 0, 360, 1, -1)
    m = cv2.GaussianBlur(m, (0, 0), 4)[..., None]
    # match local brightness so the pasted eye sits in the current frame's lighting
    out[i] = np.clip(dst*(1-m)+sh*m, 0, 255).astype(np.uint8)
    print(i, 'ref', ref, 'shift', round(dx, 1), round(dy, 1))
p = subprocess.Popen(['ffmpeg', '-loglevel', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', '30', '-i', '-',
                      '-c:v', 'libx264', '-crf', '10', '-pix_fmt', 'yuv444p', V+'sf10_wake13.mp4'], stdin=subprocess.PIPE)
for f in out: p.stdin.write(f.tobytes())
p.stdin.close(); p.wait()
