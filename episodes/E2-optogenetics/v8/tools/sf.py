"""Styleframe compositor: smooth sub-pixel camera moves, glows, CJK type, labels, grade. 24 fps."""
import numpy as np, cv2, subprocess, os, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter
SERIF_B='/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc'; SERIF='/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc'
SANS='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'; SANS_B='/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'
INK=(11,16,34); CREAM=(244,239,230); GOLD=(233,184,92); CYAN=(63,169,255); AMBER=(255,180,67); MUTED=(150,162,190)
def F(path,size,idx=2): return ImageFont.truetype(path,int(size),index=idx)  # idx 2 = SC in Noto CJK ttc
def ease(t): t=min(max(t,0),1); return t*t*(3-2*t)
def ease_out(t): t=min(max(t,0),1); return 1-(1-t)**3
def ramp(t,a,b): return ease((t-a)/(b-a)) if b>a else float(t>=a)
def load(p): return np.asarray(Image.open(p).convert('RGB')).astype(np.float32)/255
def cam(img,W,H,zoom=1.0,cx=0.5,cy=0.5):
    """crop centered at (cx,cy) of img (normalized) with zoom (1=fit width); sub-pixel via warpAffine"""
    h,w=img.shape[:2]; s=max(W/w,H/h)*zoom
    M=np.array([[s,0,W/2-s*cx*w],[0,s,H/2-s*cy*h]],np.float32)
    return cv2.warpAffine(img,M,(W,H),flags=cv2.INTER_CUBIC,borderMode=cv2.BORDER_REFLECT)
def to_px(img,x,y,W,H,zoom,cx,cy):
    h,w=img.shape[:2]; s=max(W/w,H/h)*zoom; return (W/2+s*(x*w-cx*w), H/2+s*(y*h-cy*h))
def glow(rgb,thresh=0.7,radius=25,amt=0.6):
    b=np.clip(rgb-thresh,0,1)/(1-thresh); g=cv2.GaussianBlur(b,(0,0),radius); return np.clip(rgb+g*amt,0,1)
def radial(W,H,x,y,r,color,amt):
    yy,xx=np.mgrid[0:H,0:W]; d=np.exp(-((xx-x)**2+(yy-y)**2)/(2*r*r)); return d[...,None]*np.array(color)/255*amt
def grade(rgb,vig=0.35,grain=0.018,seed=0,lift=(0.043,0.062,0.133)):
    H,W=rgb.shape[:2]; yy,xx=np.mgrid[0:H,0:W]; d=((xx/W-0.5)**2+(yy/H-0.5)**2)/0.5
    rgb=rgb*(1-vig*d[...,None]); lift=np.array(lift)
    rgb=lift+rgb*(1-lift)   # never pure black: lift shadows to ink
    rng=np.random.default_rng(seed); rgb=rgb+rng.normal(0,grain,(H,W,1))
    return np.clip(rgb,0,1)
class Layer:
    """RGBA text/graphics layer at supersample 2x"""
    def __init__(s,W,H,ss=2): s.W,s.H,s.ss=W,H,ss; s.im=Image.new('RGBA',(W*ss,H*ss),(0,0,0,0)); s.d=ImageDraw.Draw(s.im)
    def text(s,xy,txt,font,fill=CREAM,alpha=1.0,anchor='la',tracking=0):
        x,y=xy[0]*s.ss,xy[1]*s.ss; c=(*fill,int(255*alpha))
        f=ImageFont.truetype(font.path,font.size*s.ss,index=getattr(font,'index',2)) if True else font
        if tracking==0: s.d.text((x,y),txt,font=f,fill=c,anchor=anchor); return
        widths=[f.getlength(ch) for ch in txt]; total=sum(widths)+tracking*s.ss*(len(txt)-1)
        if anchor[0]=='m': x-=total/2
        elif anchor[0]=='r': x-=total
        for ch,wd in zip(txt,widths): s.d.text((x,y),ch,font=f,fill=c,anchor='l'+anchor[1]); x+=wd+tracking*s.ss
    def line(s,pts,fill=CREAM,width=1.2,alpha=1.0):
        s.d.line([(x*s.ss,y*s.ss) for x,y in pts],fill=(*fill,int(255*alpha)),width=max(1,int(width*s.ss)),joint='curve')
    def dot(s,xy,r,fill=CREAM,alpha=1.0):
        x,y=xy; s.d.ellipse([(x-r)*s.ss,(y-r)*s.ss,(x+r)*s.ss,(y+r)*s.ss],fill=(*fill,int(255*alpha)))
    def ring(s,xy,r,fill=CREAM,width=1.2,alpha=1.0):
        x,y=xy; s.d.ellipse([(x-r)*s.ss,(y-r)*s.ss,(x+r)*s.ss,(y+r)*s.ss],outline=(*fill,int(255*alpha)),width=max(1,int(width*s.ss)))
    def rrect(s,box,r,fill=None,outline=None,width=1.2,alpha=1.0):
        b=[v*s.ss for v in box]
        s.d.rounded_rectangle(b,r*s.ss,fill=(*fill,int(255*alpha)) if fill else None,outline=(*outline,int(255*alpha)) if outline else None,width=max(1,int(width*s.ss)))
    def paste(s,img,xy,alpha=1.0,size=None):
        im=img.convert('RGBA'); size=size or im.size   # sizes are in output px; layer is supersampled
        im=im.resize((int(size[0]*s.ss),int(size[1]*s.ss)),Image.LANCZOS)
        if alpha<1: a=np.asarray(im).copy(); a[...,3]=(a[...,3]*alpha).astype(np.uint8); im=Image.fromarray(a)
        s.im.alpha_composite(im,(int(xy[0]*s.ss),int(xy[1]*s.ss)))
    def get(s,shadow=True,glow_amt=0.0):
        im=s.im.resize((s.W,s.H),Image.LANCZOS); a=np.asarray(im).astype(np.float32)/255; return a
def over(rgb,layer_rgba,shadow=0.55,glow_amt=0.0):
    a=layer_rgba[...,3:4]; c=layer_rgba[...,:3]
    if shadow>0:
        sh=cv2.GaussianBlur(a,(0,0),3)[...,None] if a.ndim==3 else cv2.GaussianBlur(a,(0,0),3)
        sh=sh.reshape(a.shape); rgb=rgb*(1-sh*shadow)
    if glow_amt>0:
        g=cv2.GaussianBlur(c*a,(0,0),6); rgb=np.clip(rgb+g*glow_amt,0,1)
    return rgb*(1-a)+c*a
def label(L,anchor_pt,text_pt,title,sub=None,color=CREAM,t=1.0,font_size=22,sub_size=15,accent=CYAN):
    """leader-line label that draws on with t in [0,1]"""
    if t<=0: return
    ax,ay=anchor_pt; tx,ty=text_pt; k=ease_out(min(t*1.6,1))
    L.ring((ax,ay),5*k,fill=accent,width=1.5); L.dot((ax,ay),2.2,fill=accent,alpha=k)
    mx,my=ax+(tx-ax)*k,ay+(ty-ay)*k; L.line([(ax,ay),(mx,my)],fill=color,width=1.1,alpha=0.85)
    ta=ramp(t,0.45,1.0)
    if ta>0:
        right = tx < L.W*0.5   # text grows away from the nearest frame edge
        L.line([(tx,ty),(tx+(1 if right else -1)*8,ty)],fill=color,width=1.1,alpha=ta)
        x0=tx+(14 if right else -14); an='l' if right else 'r'
        tw=max(F(SANS_B,font_size).getlength(title), F(SANS,sub_size).getlength(sub) if sub else 0)
        bx0,bx1=(x0-8,x0+tw+8) if right else (x0-tw-8,x0+8)
        L.rrect((bx0,ty-font_size-8,bx1,ty+(sub_size+14 if sub else 8)),6,fill=(11,16,34),alpha=0.55*ta)
        L.text((x0,ty-2),title,F(SANS_B,font_size),fill=color,alpha=ta,anchor=an+'s')
        if sub: L.text((x0,ty+6),sub,F(SANS,sub_size),fill=MUTED,alpha=ta,anchor=an+'t')
def write_video(frames_fn,n,out,W,H,fps=24):
    p=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(fps),'-i','-','-c:v','libx264','-pix_fmt','yuv420p','-crf','18','-preset','medium',out],stdin=subprocess.PIPE)
    for i in range(n): p.stdin.write((np.clip(frames_fn(i),0,1)*255).astype(np.uint8).tobytes())
    p.stdin.close(); p.wait()
def save(rgb,out): Image.fromarray((np.clip(rgb,0,1)*255).astype(np.uint8)).save(out)
