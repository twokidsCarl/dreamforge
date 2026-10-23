"""Build before/after comparison videos for SF04/SF05/SF10."""
import cv2, numpy as np, subprocess, os
ROOT='/workspace/e2work/v8'
REV=f'{ROOT}/review'
BEF=f'{ROOT}/styleframes/before_carl_style'
CUR=f'{ROOT}/styleframes'
os.makedirs(REV, exist_ok=True)

def load(p):
    cap=cv2.VideoCapture(p); fr=[]
    while True:
        ok,f=cap.read()
        if not ok: break
        fr.append(f)
    cap.release(); return fr

def write(path, frames, w, h, fps=24):
    p=subprocess.Popen(['ffmpeg','-loglevel','error','-y','-f','rawvideo','-pix_fmt','bgr24','-s',f'{w}x{h}','-r',str(fps),'-i','-',
                        '-c:v','libx264','-crf','14','-pix_fmt','yuv420p',path], stdin=subprocess.PIPE)
    for f in frames: p.stdin.write(np.ascontiguousarray(f).tobytes())
    p.stdin.close(); p.wait()

for name, label in [('SF04_crick_quote','SF04'), ('SF05_nobel_portraits','SF05')]:
    a=load(f'{BEF}/{name}.mp4'); b=load(f'{CUR}/{name}.mp4')
    n=min(len(a),len(b)); h,w=540,960; cmp=[]
    for i in range(n):
        aa=cv2.resize(a[i],(w,h)); bb=cv2.resize(b[i],(w,h))
        cv2.putText(aa,'BEFORE (beads)',(16,34),cv2.FONT_HERSHEY_SIMPLEX,0.8,(0,0,255),2,cv2.LINE_AA)
        cv2.putText(bb,'AFTER (clean illus)',(16,34),cv2.FONT_HERSHEY_SIMPLEX,0.8,(0,220,0),2,cv2.LINE_AA)
        cmp.append(np.hstack([aa,bb]))
    out=f'{REV}/{label}_macro_clean_before_after.mp4'
    write(out, cmp, w*2, h)
    # still pair
    mid=n//2
    cv2.imwrite(f'{REV}/{label}_macro_clean_before_after.png', np.hstack([cv2.resize(a[mid],(w,h)), cv2.resize(b[mid],(w,h))]))
    print('wrote', out)
