"""Round 16: temporal stabilisation of the lobe-mouse Wan clips (the lobe texture is re-drawn every frame = 'boiling').
Each frame = 0.2*prev + 0.6*cur + 0.2*next, neighbours warped onto the current frame with DIS optical flow; two passes.
Writes gen/vid/<name>s.mp4."""
import cv2, numpy as np, subprocess, sys
V = '/workspace/e2work/v8/gen/vid/'
dis = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)
def load(n):
    c = cv2.VideoCapture(V+n+'.mp4'); fr = []
    while True:
        ok, f = c.read()
        if not ok: break
        fr.append(f.astype(np.float32))
    return fr
def warp_to(src, dst):
    a = cv2.cvtColor(dst.astype(np.uint8), cv2.COLOR_BGR2GRAY); b = cv2.cvtColor(src.astype(np.uint8), cv2.COLOR_BGR2GRAY)
    fl = dis.calc(a, b, None); h, w = a.shape
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    return cv2.remap(src, xx+fl[..., 0], yy+fl[..., 1], cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
def smooth(fr):
    out = []
    for i in range(len(fr)):
        p = warp_to(fr[max(i-1, 0)], fr[i]); n = warp_to(fr[min(i+1, len(fr)-1)], fr[i])
        out.append(0.2*p+0.6*fr[i]+0.2*n)
    return out
for n in sys.argv[1:]:
    fr = load(n); h, w = fr[0].shape[:2]
    fr = smooth(smooth(fr))
    p = subprocess.Popen(['ffmpeg', '-loglevel', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{w}x{h}', '-r', '30', '-i', '-',
                          '-c:v', 'libx264', '-crf', '10', '-pix_fmt', 'yuv444p', V+n+'s.mp4'], stdin=subprocess.PIPE)
    for f in fr: p.stdin.write(np.clip(f, 0, 255).astype(np.uint8).tobytes())
    p.stdin.close(); p.wait(); print('done', n, len(fr))
