import sys; sys.path.insert(0,'/workspace/e2work/v8/tools')
import numpy as np, cv2, mol
from PIL import Image
G='/workspace/e2work/v8/gen/'
def loadu8(n): return np.asarray(Image.open(G+n+'.png').convert('RGB'))
def hsvmask(im,hlo,hhi,smin,vmin,box=None):
    hsv=cv2.cvtColor(im,cv2.COLOR_RGB2HSV); m=((hsv[...,0]>=hlo)&(hsv[...,0]<=hhi)&(hsv[...,1]>=smin)&(hsv[...,2]>=vmin)).astype(np.uint8)
    if box is not None:
        h,w=m.shape; k=np.zeros_like(m); x0,y0,x1,y1=box; k[int(y0*h):int(y1*h),int(x0*w):int(x1*w)]=1; m*=k
    return m
def erase(im,m,dil=7,r=7):
    m=cv2.dilate(m,np.ones((dil,dil),np.uint8)); return cv2.inpaint(im,m*255,r,cv2.INPAINT_TELEA)
def put(im,spr,c):
    f=mol.composite(im.astype(np.float32)/255,spr,c); return (np.clip(f,0,1)*255).astype(np.uint8)
RET=mol.retinal_geom()
def retinal(px,ang,flip=False):
    g=RET
    if flip:
        C,b,n,a=g; g=({k:(-x,y) for k,(x,y) in C.items()},b,n,a)
    return mol.draw(g,px,ang)[0]
# --- SF09: orange flat retinals with a ring at each end -> beta-ionone + polyene + Schiff base
im=loadu8('sf09d_chr2'); h,w=im.shape[:2]
for box in ((0.36,0.39,0.43,0.50),(0.57,0.39,0.635,0.50)):
    im=erase(im,hsvmask(im,5,22,120,120,box),9,9)
# left: ring upper-outer (0.376,0.424), chain down-inward to (0.415,0.48)
L=retinal(int(0.075*w),38); im=put(im,L,(0.394*w,0.452*h))
R=retinal(int(0.075*w),-38,flip=True); im=put(im,R,(0.600*w,0.458*h))
Image.fromarray(im).save(G+'sf09e_chr2.png')
# --- SF03 insets: small two-ring retinals -> correct retinal (only compact bright-orange blobs inside proteins)
for n in ('sf03_ins_l','sf03_ins_r'):
    im=loadu8(n); h,w=im.shape[:2]; hsv=cv2.cvtColor(im,cv2.COLOR_RGB2HSV)
    m=((hsv[...,0]>=5)&(hsv[...,0]<=20)&(hsv[...,1]>=190)&(hsv[...,2]>=200)).astype(np.uint8)
    nl,lab,st,cen=cv2.connectedComponentsWithStats(cv2.dilate(m,np.ones((3,3),np.uint8)))
    keep=[k for k in range(1,nl) if 1000<st[k][4]<6000 and st[k][2]<w*0.12]
    mm=np.isin(lab,keep).astype(np.uint8)
    im2=erase(im,mm,9,7)
    for k in keep:
        x,y,ww,hh,a=st[k]; fl=cen[k][0]>w*0.5 and n.endswith('r')
        im2=put(im2,retinal(int(max(ww,hh)*1.25),38 if not fl else -38,flip=fl),(cen[k][0],cen[k][1]))
    Image.fromarray(im2).save(G+n+'2.png')
# --- SF08: remove magenta neon molecules everywhere
im=loadu8('sf08d_relay'); m=hsvmask(im,135,170,90,110,(0.5,0.0,1.0,0.6))
out=erase(im,m,9,9).astype(np.float32)
k=cv2.GaussianBlur(cv2.dilate(m,np.ones((31,31),np.uint8)).astype(np.float32),(0,0),8)[...,None]
out=out*(1-k)+out*np.array([0.45,0.6,0.95])*0.8*k
Image.fromarray(np.clip(out,0,255).astype(np.uint8)).save(G+'sf08e_relay.png')
print('ok')
# --- SF09 r6: plate without retinal (drawn live so it can bend)
im=loadu8('sf09d_chr2')
for box in ((0.36,0.39,0.43,0.50),(0.57,0.39,0.635,0.50)):
    im=erase(im,hsvmask(im,5,22,120,120,box),9,9)
Image.fromarray(im).save(G+'sf09f_noret.png'); print('sf09f ok')
