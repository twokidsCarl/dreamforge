"""ECC affine zoom (%/s) from 1.0 s to the last frame, on 480x270 grey, sigma 3 (same method as the R9 independent review)."""
import sys, cv2, numpy as np, glob, os
def frames(p):
    cap = cv2.VideoCapture(p); fps = cap.get(cv2.CAP_PROP_FPS); out = []
    while True:
        ok, f = cap.read()
        if not ok: break
        g = cv2.GaussianBlur(cv2.cvtColor(cv2.resize(f, (480, 270)), cv2.COLOR_BGR2GRAY).astype(np.float32), (0, 0), 3); out.append(g)
    return out, fps
for p in sorted(glob.glob('/workspace/e2work/v8/styleframes/SF*.mp4')) if len(sys.argv) < 2 else sys.argv[1:]:
    fr, fps = frames(p); a, b = fr[int(fps)], fr[-1]; dt = (len(fr)-1-int(fps))/fps
    M = np.eye(2, 3, dtype=np.float32)
    try:
        _, M = cv2.findTransformECC(a, b, M, cv2.MOTION_AFFINE, (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 200, 1e-6), None, 5)
        z = np.sqrt(abs(np.linalg.det(M[:, :2])))
    except cv2.error: z = float('nan')
    d05 = [np.abs(fr[i+12]-fr[i]).mean() for i in range(0, len(fr)-12, 6)]
    print(f'{os.path.basename(p)[:4]}  zoom {100*(z**(1/dt)-1):+.2f} %/s   d05 mean {np.mean(d05):.1f} min {np.min(d05):.1f}')
