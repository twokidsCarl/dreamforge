from PIL import Image, ImageDraw, ImageFont, ImageFilter
import json, sys, os
B='/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'; R='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
def F(p,s): return ImageFont.truetype(p,s,index=2)
BG=(11,16,34); COL=[(63,169,255),(233,184,92),(240,131,91),(140,220,190)]
def load(spec):
    if isinstance(spec,list):  # horizontal composite
        ims=[load(s) for s in spec]; h=min(i.height for i in ims)
        ims=[i.resize((int(i.width*h/i.height),h),Image.LANCZOS) for i in ims]
        gap=int(h*0.02); W=sum(i.width for i in ims)+gap*(len(ims)-1)
        out=Image.new('RGB',(W,h),BG); x=0
        for i in ims: out.paste(i,(x,0)); x+=i.width+gap
        return out
    path,crop=(spec['p'],spec.get('crop')) if isinstance(spec,dict) else (spec,None)
    im=Image.open(path).convert('RGB')
    if crop:
        w,h=im.size; im=im.crop((int(crop[0]*w),int(crop[1]*h),int(crop[2]*w),int(crop[3]*h)))
    return im
def fit(im,w,h,mode,fy=0.5):
    if mode=='cover':
        s=max(w/im.width,h/im.height); im2=im.resize((max(w,round(im.width*s)),max(h,round(im.height*s))),Image.LANCZOS)
        x=(im2.width-w)//2; y=int((im2.height-h)*fy); return im2.crop((x,y,x+w,y+h))
    bg=im.resize((w,h)).filter(ImageFilter.GaussianBlur(30)); bg=Image.blend(bg,Image.new('RGB',(w,h),BG),0.6)
    s=min(w/im.width,h/im.height); im2=im.resize((round(im.width*s),round(im.height*s)),Image.LANCZOS)
    bg.paste(im2,((w-im2.width)//2,(h-im2.height)//2)); return bg
def tw(d,t,f): b=d.textbbox((0,0),t,font=f); return b[2]-b[0]
def build(sp,out):
    W,H=1600,900; img=Image.new('RGB',(W,H),BG); d=ImageDraw.Draw(img)
    d.text((28,14),sp['title'],font=F(B,38),fill=(245,240,230))
    x0=28+tw(d,sp['title'],F(B,38))+22
    d.text((x0,30),sp['shots'],font=F(R,20),fill=(170,180,205))
    d.text((28,64),sp['q'],font=F(R,19),fill=(233,184,92))
    c=sp['cands']; n=len(c); top=100; m=24; gap=18; caph=46
    if n==4: cols,rows=2,2
    else: cols,rows=n,1
    cw=(W-2*m-gap*(cols-1))//cols; ch=(H-top-m-gap*(rows-1))//rows; ih=ch-caph
    for i,cd in enumerate(c):
        cx=m+(i%cols)*(cw+gap); cy=top+(i//cols)*(ch+gap)
        im=fit(load(cd['src']),cw,ih,cd.get('mode','cover'),cd.get('fy',0.5))
        img.paste(im,(cx,cy)); col=COL[i]
        L='ABCD'[i]; fL=F(B,52)
        d.rounded_rectangle((cx+10,cy+10,cx+76,cy+82),10,fill=(10,14,30))
        d.rounded_rectangle((cx+10,cy+10,cx+76,cy+82),10,outline=col,width=3)
        d.text((cx+43-tw(d,L,fL)//2,cy+8),L,font=fL,fill=col)
        if cd.get('mock'):
            t='MOCK-UP · image2 生成示意'; f=F(B,22); w=tw(d,t,f)
            d.rounded_rectangle((cx+cw-w-30,cy+12,cx+cw-10,cy+48),6,fill=(200,40,60))
            d.text((cx+cw-w-20,cy+12),t,font=f,fill='white')
        if cd.get('ctrl'):
            t='对照项'; f=F(B,20); w=tw(d,t,f)
            d.rounded_rectangle((cx+cw-w-30,cy+12,cx+cw-10,cy+46),6,fill=(90,96,110))
            d.text((cx+cw-w-20,cy+13),t,font=f,fill='white')
        # source tag bottom-right on image
        st=cd['tag']; fs=F(R,15); w=tw(d,st,fs)
        d.rectangle((cx+cw-w-16,cy+ih-26,cx+cw,cy+ih),fill=(0,0,0))
        d.text((cx+cw-w-8,cy+ih-25),st,font=fs,fill=(200,205,215))
        fc=F(B,22) if tw(d,cd['cap'],F(B,22))<=cw-10 else F(B,19)
        d.text((cx+2,cy+ih+8),L+'  '+cd['cap'],font=fc,fill=col)
        assert tw(d,L+'  '+cd['cap'],fc)<=cw, (out,cd['cap'],tw(d,L+'  '+cd['cap'],fc),cw)
    img.save(out,quality=92)
if __name__=='__main__':
    for sp in json.load(open(sys.argv[1])):
        build(sp,sp['out']); print(sp['out'])
