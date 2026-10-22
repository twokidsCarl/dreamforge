import sys; sys.path.insert(0,'/workspace/e2work/v8/tools')
from sf import *
G='/workspace/e2work/v8/gen/'
S={}
def scene(name,dur):
    def d(fn): S[name]=(fn,dur); return fn
    return d
_cache={}
def img(n):
    if n not in _cache: _cache[n]=load(G+n+'.png')
    return _cache[n]

# ---------- SF01 片头标题卡 (new, 0:03-0:08) ----------
@scene('SF01_open_title',5.0)
def sf01(t,W,H):
    k=t/5.0; z=1.0+0.06*ease(k)
    rgb=cam(img('sf01_open_bg'),W,H,zoom=z,cx=0.52+0.02*k,cy=0.5)
    # beam breathes on (light 'switches on' at 0.6s)
    nx,ny=to_px(img('sf01_open_bg'),0.68,0.56,W,H,z,0.52+0.02*k,0.5)
    on=ramp(t,0.4,1.4); rgb=rgb*(0.55+0.45*on)+radial(W,H,nx,ny,W*0.07,CYAN,0.55*on*(0.85+0.15*math.sin(t*5)))
    rgb=glow(rgb,0.72,W/50,0.5*on)
    L=Layer(W,H); s=W/1280
    a=ramp(t,1.2,2.4); tr=int(40*s*(1-ease_out(ramp(t,1.2,3.0)))+18*s)
    L.text((150*s,330*s),'光遗传学',F(SERIF_B,104*s),fill=CREAM,alpha=a,anchor='ls',tracking=tr)
    L.line([(152*s,362*s),(152*s+300*s*ease_out(ramp(t,1.8,2.8)),362*s)],fill=CYAN,width=1.6*s,alpha=a)
    L.text((152*s,398*s),'用一束光，只拨动一类神经元',F(SANS,27*s),fill=CREAM,alpha=ramp(t,2.3,3.2)*0.92,anchor='ls',tracking=3*s)
    L.text((152*s,436*s),'OPTOGENETICS',F(SANS,15*s),fill=MUTED,alpha=ramp(t,2.6,3.4),anchor='ls',tracking=9*s)
    L.text((152*s,600*s),'EigenLens 主观知识  ·  第 2 期',F(SANS,15*s),fill=MUTED,alpha=ramp(t,3.0,3.8)*0.8,anchor='ls',tracking=2*s)
    return grade(over(rgb,L.get(),glow_amt=0.25),seed=int(t*24))

# ---------- SF02 1979 要求 (A0_01a, 0:03-0:12; Carl 0:06) ----------
@scene('SF02_1979_request',5.0)
def sf02(t,W,H):
    im=img('sf02_1979_crowd'); k=t/5
    if 'gold' not in _cache:
        hsv=cv2.cvtColor((im*255).astype(np.uint8),cv2.COLOR_RGB2HSV).astype(np.float32)
        m=((hsv[...,0]>10)&(hsv[...,0]<32)&(hsv[...,1]>90)&(hsv[...,2]>120)).astype(np.float32)
        m[int(im.shape[0]*0.45):, :int(im.shape[1]*0.45)]=0   # exclude desk lamp/page area
        _cache['gold']=cv2.GaussianBlur(m,(0,0),2)[...,None]
        gray=im.mean(2,keepdims=True); _cache['dim']=im*0.35+gray*np.array([0.42,0.42,0.55])*0.45
    z=1.04+0.05*ease(k); cx,cy=0.55,0.47
    gold=_cache['gold']; on=ramp(t,1.2,3.0)
    base=_cache['dim']*(1-gold)+im*gold*(0.3+1.2*on)+_cache['dim']*gold*(1-on)*0.7
    # keep desk/lamp area original (context)
    rgb=cam(base,W,H,zoom=z,cx=cx,cy=cy); rgb=glow(rgb,0.6,W/90,0.6*on)
    L=Layer(W,H); s=W/1280
    L.rrect((60*s,52*s,340*s,118*s),6*s,fill=(14,20,40),alpha=0.72*ramp(t,0.2,0.9))
    L.line([(60*s,52*s),(60*s,118*s)],fill=GOLD,width=3*s,alpha=ramp(t,0.2,0.9))
    L.text((78*s,82*s),'Francis Crick · 1979',F(SANS_B,22*s),fill=CREAM,alpha=ramp(t,0.3,1.0),anchor='ls')
    L.text((78*s,106*s),'《科学美国人》“Thinking about the Brain”',F(SANS,14*s),fill=MUTED,alpha=ramp(t,0.4,1.1),anchor='ls')
    # the requirement, as legend
    a=ramp(t,2.6,3.4)
    L.dot((852*s,600*s),6*s,fill=GOLD,alpha=a); L.text((870*s,607*s),'只动某一类神经元',F(SANS_B,24*s),fill=CREAM,alpha=a,anchor='ls')
    b=ramp(t,3.3,4.0)
    L.dot((852*s,642*s),6*s,fill=(120,124,150),alpha=b); L.text((870*s,649*s),'其余的大体不动',F(SANS,22*s),fill=MUTED,alpha=b,anchor='ls')
    return grade(over(rgb,L.get()),seed=int(t*24))

# ---------- SF03 微生物线索 (A0_01b, Carl 0:13) ----------
@scene('SF03_microbe_clues',5.0)
def sf03(t,W,H):
    im=img('sf03b_microbes_dusk'); k=t/5; z=1.03+0.04*ease(k)
    rgb=cam(im,W,H,zoom=z,cx=0.5-0.015*k,cy=0.5)
    sx,_=to_px(im,0.5,0.5,W,H,z,0.5-0.015*k,0.5)
    rgb=rgb+radial(W,H,sx,H*0.3,W*0.05,CYAN,0.12*(0.8+0.2*math.sin(t*3)))
    L=Layer(W,H); s=W/1280
    L.text((40*s,58*s),'接下来的那些年 · 微生物那边',F(SANS,17*s),fill=MUTED,alpha=ramp(t,0.1,0.8),anchor='ls',tracking=3*s)
    a1=ramp(t,0.6,2.0); a2=ramp(t,2.0,3.4)
    ax,ay=to_px(im,0.24,0.37,W,H,z,0.5-0.015*k,0.5)
    label(L,(ax,ay),(60*s,600*s),'1981 · 古菌 · 盐视紫红质','紫膜上的光驱动离子泵',t=a1,accent=GOLD,font_size=22*s,sub_size=15*s)
    bx,by=to_px(im,0.785,0.385,W,H,z,0.5-0.015*k,0.5)
    label(L,(bx,by),(1220*s,610*s),'1991–1996 · 衣藻 · 微秒级光电流','眼点附近：光一到，膜上立刻有电流',t=a2,accent=CYAN,font_size=22*s,sub_size=15*s)
    return grade(over(rgb,L.get()),seed=int(t*24))

# ---------- SF04 Crick 1999 引文 (A0_02a, Carl 0:27 「相当牵」) ----------
@scene('SF04_crick_quote',5.0)
def sf04(t,W,H):
    s=W/1280; rgb=np.zeros((H,W,3),np.float32)+np.array(INK)/255
    rgb=rgb+radial(W,H,W*0.3,H*0.45,W*0.28,(40,60,120),0.5)
    por=Image.open(G+'sf04_crick_portrait.png'); ph=int(H*0.92); pw=ph
    pa=ramp(t,0,0.8); dx=int(12*s*(1-ease_out(ramp(t,0,1.5))))
    P=cam(load(G+'sf04_crick_portrait.png'),pw,ph,zoom=1.0+0.03*t/5)
    # soft mask fade to background on right/bottom
    yy,xx=np.mgrid[0:ph,0:pw]; m=np.clip(1-np.maximum((xx/pw-0.62)/0.38,0),0,1)*np.clip(1-np.maximum((yy/ph-0.8)/0.2,0),0,1)
    m=(m*pa)[...,None]; x0=int(40*s)-dx; y0=H-ph
    rgb[y0:,x0:x0+pw]=rgb[y0:,x0:x0+pw]*(1-m)+P*m
    L=Layer(W,H)
    L.text((690*s,250*s),'1999',F(SANS,18*s),fill=GOLD,alpha=ramp(t,0.5,1.1),anchor='ls',tracking=6*s)
    L.text((690*s,320*s),'“理想的信号会是光。”',F(SERIF_B,44*s),fill=CREAM,alpha=ramp(t,0.8,1.8),anchor='ls')
    L.text((690*s,392*s),'——他也承认，',F(SERIF,26*s),fill=MUTED,alpha=ramp(t,2.2,2.8),anchor='ls')
    L.text((690*s,446*s),'这个想法相当牵强。',F(SERIF_B,36*s),fill=GOLD,alpha=ramp(t,2.6,3.4),anchor='ls')
    L.line([(690*s,486*s),(690*s+420*s*ease_out(ramp(t,3.2,4.2)),486*s)],fill=(80,90,120),width=1*s)
    L.text((690*s,516*s),'原文 “rather far-fetched” — F. Crick, Phil. Trans. R. Soc. Lond. B, 1999',F(SANS,13*s),fill=MUTED,alpha=ramp(t,3.4,4.2),anchor='ls')
    return grade(over(rgb,L.get(),glow_amt=0.15),seed=int(t*24))

# ---------- SF05 诺奖三人漫画头像 (A0_04a, Carl 0:50) ----------
@scene('SF05_nobel_portraits',5.0)
def sf05(t,W,H):
    s=W/1280; bg=img('sf05_nobel_hegemann')[5:40,5:40].reshape(-1,3).mean(0); rgb=np.zeros((H,W,3),np.float32)+bg
    names=[('sf05_nobel_deisseroth','Karl Deisseroth','美国 · 斯坦福大学'),('sf05_nobel_hegemann','Peter Hegemann','德国 · 柏林洪堡大学'),('sf05_nobel_nagel','Georg Nagel','德国 · 维尔茨堡大学')]
    L=Layer(W,H); cw=340*s; gap=40*s; x0=(W-3*cw-2*gap)/2; y0=150*s
    for i,(n,nm,aff) in enumerate(names):
        a=ramp(t,0.5+i*0.45,1.3+i*0.45); dy=int(26*s*(1-ease_out(a)))
        P=cam(img(n),int(cw),int(cw),zoom=1.0+0.02*t/5)
        x=int(x0+i*(cw+gap)); y=int(y0)+dy
        yy,xx=np.mgrid[0:int(cw),0:int(cw)]; e=np.minimum.reduce([xx/cw,1-xx/cw,yy/cw,(1-yy/cw)*0.6]); m=(np.clip(e/0.12,0,1)**1.5)[...,None]*a
        rgb[y:y+int(cw),x:x+int(cw)]=rgb[y:y+int(cw),x:x+int(cw)]*(1-m)+P*m
        L.line([(x,y0+cw+18*s),(x+cw*ease_out(a),y0+cw+18*s)],fill=GOLD,width=1.2*s,alpha=a)
        L.text((x,y0+cw+50*s),nm,F(SERIF_B,24*s),fill=CREAM,alpha=a,anchor='ls')
    L.text((W/2,70*s),'2026 年 10 月 5 日  ·  诺贝尔生理学或医学奖',F(SANS_B,22*s),fill=GOLD,alpha=ramp(t,0,0.6),anchor='ms',tracking=2*s)
    L.text((W/2,104*s),'“表彰他们发现光控离子通道并建立光遗传学”',F(SERIF,17*s),fill=CREAM,alpha=ramp(t,2.2,3.0)*0.85,anchor='ms')
    return grade(over(rgb,L.get()),seed=int(t*24))

def circ(path,box,size,ring=GOLD):
    im=Image.open(path).convert('RGB'); w,h=im.size; im=im.crop((int(box[0]*w),int(box[1]*h),int(box[2]*w),int(box[3]*h))).resize((size*2,size*2),Image.LANCZOS)
    m=Image.new('L',(size*2,size*2),0); ImageDraw.Draw(m).ellipse([0,0,size*2-1,size*2-1],fill=255); im.putalpha(m); return im

# ---------- SF06 设想→开关→方法 (A0_05a, Carl 0:59 一格格跳) ----------
@scene('SF06_switch_diagram',6.0)
def sf06(t,W,H):
    s=W/1280; rgb=np.zeros((H,W,3),np.float32)+np.array(INK)/255
    rgb=rgb+radial(W,H,W*0.5,H*0.5,W*0.35,(30,50,100),0.45)
    # drifting dot grid (sub-pixel)
    L0=Layer(W,H); off=(t*6*s)%(40*s)
    for gx in range(-1,34):
        for gy in range(-1,19):
            L0.dot((gx*40*s+off,gy*40*s+off*0.5),0.9*s,fill=(70,85,130),alpha=0.5)
    rgb=over(rgb,L0.get(),shadow=0)
    L=Layer(W,H); cy=320*s
    # node 1: the 1999 idea
    a1=ramp(t,0.0,0.8); x1=250*s
    P=circ(G+'sf04_crick_portrait.png',(0.2,0.08,0.68,0.56),int(95*s)); L.paste(P,((x1-95*s),(cy-95*s)),alpha=a1)
    L.ring((x1,cy),96*s,fill=GOLD,width=1.5*s,alpha=a1)
    L.text((x1,cy+160*s),'一句自认牵强的设想',F(SANS_B,26*s),fill=CREAM,alpha=a1,anchor='ms')
    L.text((x1,cy+188*s),'“理想的信号会是光” · 1999',F(SANS,15*s),fill=MUTED,alpha=a1,anchor='ms')
    # connector 1 -> slot, draws on smoothly + travelling photon
    xs=640*s; c1=ease(ramp(t,0.8,1.8)); xa=x1+105*s; xb=xs-120*s
    L.line([(xa,cy),(xa+(xb-xa)*c1,cy)],fill=(120,140,190),width=1.4*s,alpha=0.9)
    # slot
    a2=ramp(t,1.4,2.0); fill_in=ease_out(ramp(t,2.6,3.6))
    L.rrect((xs-115*s,cy-115*s,xs+115*s,cy+115*s),20*s,outline=CYAN if fill_in>0.5 else (120,140,190),width=1.6*s,alpha=a2)
    if fill_in<1: L.text((xs,cy+16*s),'?',F(SERIF_B,64*s),fill=MUTED,alpha=a2*(1-fill_in),anchor='ms')
    if fill_in>0:
        ch=Image.open(G+'sf09b_chr2_dusk.png').convert('RGB'); w,h=ch.size; ch=ch.crop((int(0.37*w),int(0.24*h),int(0.63*w),int(0.62*h))).resize((int(220*s),int(220*s)),Image.LANCZOS)
        m=Image.new('L',ch.size,0); ImageDraw.Draw(m).rounded_rectangle([0,0,ch.size[0]-1,ch.size[1]-1],int(16*s),fill=255); ch.putalpha(m)
        dy=(1-fill_in)*-60*s; L.paste(ch,(xs-110*s,cy-110*s+dy),alpha=fill_in)
    a3=ramp(t,3.2,3.9)
    L.text((xs,cy+160*s),'一枚能用光拨动的开关',F(SANS_B,28*s),fill=CYAN,alpha=a3,anchor='ms')
    L.text((xs,cy+188*s),'光控离子通道',F(SANS,15*s),fill=MUTED,alpha=a3,anchor='ms')
    # connector slot -> method
    c2=ease(ramp(t,3.6,4.5)); xc=xs+120*s; x3=1035*s; xd=x3-150*s
    L.line([(xc,cy),(xc+(xd-xc)*c2,cy)],fill=(120,140,190),width=1.4*s,alpha=0.9)
    for i,(n,b) in enumerate([('sf05_nobel_deisseroth',(0.2,0.08,0.8,0.68)),('sf05_nobel_hegemann',(0.2,0.08,0.8,0.68)),('sf05_nobel_nagel',(0.2,0.08,0.8,0.68))]):
        a=ramp(t,4.2+i*0.2,4.8+i*0.2); px=x3+(i-1)*92*s; py=cy+(-40 if i==1 else 30)*s
        L.paste(circ(G+n+'.png',b,int(56*s)),(px-56*s,py-56*s+(1-ease_out(a))*14*s),alpha=a); L.ring((px,py+(1-ease_out(a))*14*s),57*s,fill=GOLD,width=1.2*s,alpha=a)
    a4=ramp(t,4.6,5.2)
    L.text((x3,cy+160*s),'一套能用的方法',F(SANS_B,26*s),fill=CREAM,alpha=a4,anchor='ms')
    L.text((x3,cy+188*s),'光遗传学 · 2026 诺奖',F(SANS,15*s),fill=MUTED,alpha=a4,anchor='ms')
    lay=L.get(); rgb=over(rgb,lay,glow_amt=0.2)
    # travelling photons along connectors (smooth sub-pixel glow dots)
    for ph in range(3):
        u=((t*0.55+ph/3)%1.0)
        if c1>0.99: rgb=rgb+radial(W,H,xa+(xb-xa)*u,cy,5*s,CYAN,0.9)
        if c2>0.99: rgb=rgb+radial(W,H,xc+(xd-xc)*u,cy,5*s,CYAN,0.9)
    if fill_in>0: rgb=rgb+radial(W,H,xs,cy,150*s,CYAN,0.18*fill_in*(0.85+0.15*math.sin(t*4)))
    return grade(rgb,seed=int(t*24))

# ---------- SF07 片名 (A0_06a, Carl 1:07 只有字) ----------
@scene('SF07_main_title',5.0)
def sf07(t,W,H):
    im=img('sf07_title_bg'); k=t/5; z=1.0+0.07*ease(k); cx,cy=0.5,0.40
    if 'cy7' not in _cache:
        hsv=cv2.cvtColor((im*255).astype(np.uint8),cv2.COLOR_RGB2HSV).astype(np.float32)
        _cache['cy7']=cv2.GaussianBlur(((hsv[...,0]>90)&(hsv[...,0]<115)&(hsv[...,2]>170)).astype(np.float32),(0,0),1.5)
        hh,ww=im.shape[:2]; yy,xx=np.mgrid[0:hh,0:ww]; _cache['d7']=np.hypot(xx/ww-0.44,yy/hh-0.39)
    wave=np.clip(1-np.abs(_cache['d7']-(t-0.6)*0.18)/0.06,0,1)*(t>0.6)
    boost=(_cache['cy7']*(0.6*wave+0.25))[...,None]*np.array([0.25,0.66,1.0])
    rgb=cam(np.clip(im*0.92+boost,0,1),W,H,zoom=z,cx=cx,cy=cy); rgb=glow(rgb,0.75,W/70,0.45)
    L=Layer(W,H); s=W/1280
    a=ramp(t,1.0,2.2); tr=(60*(1-ease_out(ramp(t,1.0,3.2)))+34)*s
    L.text((W/2,585*s),'光遗传学',F(SERIF_B,118*s),fill=CREAM,alpha=a,anchor='ms',tracking=tr)
    L.text((W/2,632*s),'O P T O G E N E T I C S',F(SANS,16*s),fill=CYAN,alpha=ramp(t,2.0,2.8),anchor='ms',tracking=4*s)
    L.text((W/2,666*s),'这一期，就讲这枚开关',F(SANS,17*s),fill=MUTED,alpha=ramp(t,2.6,3.4),anchor='ms',tracking=4*s)
    return grade(over(rgb,L.get(),glow_amt=0.35),seed=int(t*24))

# ---------- SF08 早先的光控尝试 (A_05a, Carl 2:03 白模+shape 不明) ----------
@scene('SF08_early_attempts',6.0)
def sf08(t,W,H):
    im=img('sf08b_relay_dusk'); k=t/6; z=1.02; cxx=0.5; cyy=0.48
    # spotlight travels along the relay (receptor -> channel), then to the right panel
    path=[(0.12,0.33),(0.17,0.60),(0.33,0.65),(0.47,0.60),(0.61,0.45)]
    u=ramp(t,0.6,3.6)*(len(path)-1); i=min(int(u),len(path)-2); f=u-i
    px=path[i][0]+(path[i+1][0]-path[i][0])*f; py=path[i][1]+(path[i+1][1]-path[i][1])*f
    rgb=cam(im,W,H,zoom=z,cx=cxx,cy=cyy)*(0.62+0.38*ramp(t,3.8,4.6))
    sx,sy=to_px(im,px,py,W,H,z,cxx,cyy); rgb=rgb+radial(W,H,sx,sy,W*0.05,CYAN,0.35*(1-ramp(t,3.8,4.6)))
    rx,ry=to_px(im,0.87,0.45,W,H,z,cxx,cyy); rgb=rgb+radial(W,H,rx,ry,W*0.06,(255,90,200),0.25*ramp(t,4.0,4.8))
    L=Layer(W,H); s=W/1280
    steps=[((0.12,0.30),'① 感光蛋白','先接住光'),((0.25,0.66),'② 信号接力','一步步传下去'),((0.47,0.60),'③ 再传一步',None),((0.61,0.40),'④ 通道才打开',None)]
    tpos=[(60,90),(60,600),(420,640),(860,110)]
    for j,((ax,ay),ti,sub) in enumerate(steps):
        a=ramp(t,0.7+j*0.75,1.4+j*0.75); X,Y=to_px(im,ax,ay,W,H,z,cxx,cyy)
        label(L,(X,Y),(tpos[j][0]*s,tpos[j][1]*s),ti,sub,t=a,font_size=20*s,sub_size=14*s,accent=CYAN)
    X,Y=to_px(im,0.87,0.40,W,H,z,cxx,cyy); label(L,(X,Y),(1220*s,620*s),'外加化学光开关','另需把化学分子送进组织',t=ramp(t,4.0,4.9),font_size=20*s,sub_size=14*s,accent=(255,90,200))
    # speed meter: needs ms, these are slower
    a=ramp(t,4.8,5.5); L.rrect((400*s,650*s,880*s,690*s),8*s,fill=(14,20,40),alpha=0.8*a)
    L.text((420*s,676*s),'需要：毫秒级',F(SANS_B,16*s),fill=CYAN,alpha=a,anchor='ls')
    L.line([(540*s,670*s),(540*s+140*s*ease_out(a),670*s)],fill=CYAN,width=3*s,alpha=a)
    L.text((700*s,676*s),'这两条路：慢一拍',F(SANS,16*s),fill=MUTED,alpha=a,anchor='ls')
    return grade(over(rgb,L.get()),seed=int(t*24))

# ---------- SF09 ChR2 Goodsell (A_06a, Carl 2:21) ----------
@scene('SF09_chr2_channel',5.0)
def sf09(t,W,H):
    im=img('sf09b_chr2_dusk'); k=t/5; z=1.05+0.08*ease(k); cxx=0.5; cyy=0.45
    if 'ion9' not in _cache:  # remove baked ions: inpaint the yellow dots so we animate them ourselves
        u8=(im*255).astype(np.uint8); hsv=cv2.cvtColor(u8,cv2.COLOR_RGB2HSV)
        hh,ww=im.shape[:2]; yy,xx=np.mgrid[0:hh,0:ww]
        m=((hsv[...,0]>15)&(hsv[...,0]<35)&(hsv[...,1]>120)&(hsv[...,2]>190)&(np.abs(xx/ww-0.5)<0.035)).astype(np.uint8)
        m=cv2.dilate(m,np.ones((7,7),np.uint8)); _cache['ion9']=cv2.inpaint(u8,m*255,6,cv2.INPAINT_TELEA).astype(np.float32)/255
    on=ramp(t,0.3,1.3); base=_cache['ion9']
    rgb=cam(base,W,H,zoom=z,cx=cxx,cy=cyy)
    # dim the light shaft before switch-on
    bx,_=to_px(im,0.5,0.1,W,H,z,cxx,cyy)
    rgb=rgb*(0.75+0.25*on)
    # ion stream through the pore, smooth
    L=Layer(W,H); s=W/1280
    for n in range(16):
        ph=(t*0.32+n/16)%1.0
        if t<1.3 and ph>0.3+0.4*ramp(t,0.8,1.3): continue
        y=0.06+ph*0.72; x=0.5+0.012*math.sin(n*2.3+ph*9)*(1 if abs(y-0.42)>0.12 else 0.3)
        X,Y=to_px(im,x,y,W,H,z,cxx,cyy); a=on*min(1,ph*8)*min(1,(1-ph)*8)
        L.dot((X,Y),6.5*s*z,fill=(255,209,102),alpha=a)
    rgb=over(rgb,L.get(),shadow=0.3,glow_amt=0.6)
    rgb=rgb+radial(W,H,bx,H*0.42,W*0.05,CYAN,0.18*on)
    L2=Layer(W,H)
    X,Y=to_px(im,0.44,0.36,W,H,z,cxx,cyy); label(L2,(X,Y),(60*s,110*s),'通道视紫红质-2（ChR2）','一个蛋白，自己就是带门的通道',t=ramp(t,1.6,2.5),font_size=22*s,sub_size=15*s,accent=(99,199,168))
    X,Y=to_px(im,0.44,0.47,W,H,z,cxx,cyy); label(L2,(X,Y),(60*s,620*s),'视黄醛','吸收蓝光，拧开这扇门',t=ramp(t,2.4,3.2),font_size=20*s,sub_size=14*s,accent=(255,138,61))
    X,Y=to_px(im,0.505,0.62,W,H,z,cxx,cyy); label(L2,(X,Y),(1220*s,620*s),'阳离子（如钠离子 Na+）','顺梯度涌入细胞',t=ramp(t,3.0,3.8),font_size=20*s,sub_size=14*s,accent=(255,209,102))
    X,Y=to_px(im,0.5,0.06,W,H,z,cxx,cyy); label(L2,(X,max(Y,30*s)),(1000*s,120*s),'蓝光 ~470 nm',None,t=ramp(t,0.8,1.6),font_size=20*s,accent=CYAN)
    return grade(over(rgb,L2.get()),seed=int(t*24))

# ---------- SF11 眼 / 器官标准 (C_08a) ----------
@scene('SF11_eye_goggles',5.0)
def sf11(t,W,H):
    im=img('sf11_eye'); k=t/5; z=1.0+0.05*ease(k); cxx=0.52; cyy=0.47
    rgb=cam(im,W,H,zoom=z,cx=cxx,cy=cyy)
    L=Layer(W,H); s=W/1280
    X,Y=to_px(im,0.12,0.38,W,H,z,cxx,cyy); label(L,(X,Y),(60*s,620*s),'护目镜','把外界明暗变化换成光脉冲',t=ramp(t,0.4,1.3),font_size=20*s,sub_size=14*s,accent=AMBER)
    X,Y=to_px(im,0.785,0.35,W,H,z,cxx,cyy); label(L,(X,Y),(1220*s,80*s),'视网膜神经节细胞','病毒带进 ChrimsonR，新装上光控通道',t=ramp(t,1.4,2.3),font_size=20*s,sub_size=14*s,accent=CYAN)
    X,Y=to_px(im,0.86,0.52,W,H,z,cxx,cyy); label(L,(X,Y),(1220*s,650*s),'感光细胞','已大量丢失',t=ramp(t,2.3,3.1),font_size=20*s,sub_size=14*s,accent=(170,170,180))
    return grade(over(rgb,L.get()),seed=int(t*24),lift=(0.03,0.04,0.09))

# ---------- SF10 Tripo 小鼠 + 光纤 (A_08a, Carl 2:23) : Blender render + 2D light/labels pass ----------
import json as _json
_PJ=None
@scene('SF10_mouse_tripo',4.0)
def sf10(t,W,H,still=False):
    global _PJ
    if _PJ is None: _PJ=_json.load(open('/workspace/e2work/v8/work/mouse_proj.json'))
    f=min(96,max(1,int(round(t*24))+1))
    if still or t is None:
        src='/workspace/e2work/v8/renders/sf10_raw.png'; tip=_PJ['still']; on=1.0
    else:
        src='/workspace/e2work/v8/renders/mouse_anim/f_%04d.png'%f; tip=_PJ[str(f)]; on=ramp(f,30,42)
    rgb=load(src); rgb=cv2.resize(rgb,(W,H),interpolation=cv2.INTER_AREA)
    s=W/1280; X,Y=tip[0]*W,tip[1]*H
    L=Layer(W,H)
    # fiber carries light: cyan core along the cable direction
    for k in range(40):
        u=k/40; L.dot((X-0.33*u*Y*1.0, Y-u*Y),2.2*s,fill=CYAN,alpha=0.55*on)
    rgb=over(rgb,L.get(),shadow=0,glow_amt=1.2*on)
    rgb=rgb+radial(W,H,X,Y+12*s,26*s,CYAN,0.9*on)+radial(W,H,X,Y+18*s,90*s,CYAN,0.22*on)
    L2=Layer(W,H)
    label(L2,(X,Y+10*s),(560*s,95*s),'光纤 + 颅骨植入件','把蓝光送进下丘脑外侧那群细胞',t=ramp(t if not still else 9,0.6,1.5),font_size=21*s,sub_size=15*s,accent=CYAN)
    a=ramp(t if not still else 9,0.2,0.9)
    L2.rrect((60*s,620*s,520*s,676*s),6*s,fill=(14,20,40),alpha=0.7*a); L2.line([(60*s,620*s),(60*s,676*s)],fill=GOLD,width=3*s,alpha=a)
    L2.text((78*s,646*s),'2007 · 小鼠 · 食欲素神经元',F(SANS_B,19*s),fill=CREAM,alpha=a,anchor='ls')
    L2.text((78*s,668*s),'光一开：从睡眠转入清醒的概率升高',F(SANS,14*s),fill=MUTED,alpha=a,anchor='ls')
    return grade(over(rgb,L2.get()),vig=0.25,grain=0.012,seed=f,lift=(0.02,0.03,0.07))

# ======================= ROUND 2 (after independent review round 1) =======================
LT,LS=22,16   # label title / sub sizes at 1280 (review: subs >=15px)
def cyan_mask(im,vmin=170,blur=1.5):
    hsv=cv2.cvtColor((np.clip(im,0,1)*255).astype(np.uint8),cv2.COLOR_RGB2HSV).astype(np.float32)
    return cv2.GaussianBlur(((hsv[...,0]>88)&(hsv[...,0]<118)&(hsv[...,2]>vmin)).astype(np.float32),(0,0),blur)
def drift_specks(W,H,t,n=60,seed=1,color=(200,215,255),amt=0.5,size=1.6,speed=(6,-3)):
    L=Layer(W,H); rng=np.random.default_rng(seed); s=W/1280
    for i in range(n):
        x=(rng.random()*W+speed[0]*s*t*(0.5+rng.random()))%W; y=(rng.random()*H+speed[1]*s*t*(0.5+rng.random()))%H
        a=amt*(0.4+0.6*rng.random())*(0.6+0.4*math.sin(t*1.3+i))
        L.dot((x,y),size*s*(0.6+rng.random()),fill=color,alpha=a)
    return L.get()

@scene('SF01_open_title',5.0)
def sf01(t,W,H):
    im=img('sf01b_open_bg')
    if 'm1' not in _cache: _cache['m1']=cyan_mask(im,150,2.0)[...,None]
    m=_cache['m1']; on=ramp(t,0.5,1.6)
    base=im*(1-m)+im*m*(0.18+0.82*on)
    z=1.0+0.07*ease(t/5); cx,cy=0.5+0.02*t/5,0.5
    rgb=cam(base,W,H,zoom=z,cx=cx,cy=cy); rgb=glow(rgb,0.7,W/55,0.55*on)
    rgb=over(rgb,drift_specks(W,H,t,50,3,(170,200,255),0.35),shadow=0)
    L=Layer(W,H); s=W/1280
    a=ramp(t,1.3,2.5); tr=(46*(1-ease_out(ramp(t,1.3,3.2)))+18)*s
    L.text((96*s,330*s),'光遗传学',F(SERIF_B,108*s),fill=CREAM,alpha=a,anchor='ls',tracking=tr)
    L.line([(98*s,364*s),(98*s+310*s*ease_out(ramp(t,1.9,2.9)),364*s)],fill=CYAN,width=1.8*s,alpha=a)
    L.text((98*s,404*s),'用一束光，只拨动一类神经元',F(SANS,28*s),fill=CREAM,alpha=ramp(t,2.4,3.3)*0.94,anchor='ls',tracking=3*s)
    L.text((98*s,442*s),'OPTOGENETICS',F(SANS,16*s),fill=MUTED,alpha=ramp(t,2.7,3.5),anchor='ls',tracking=9*s)
    L.text((98*s,640*s),'EigenLens 主观知识  ·  第 2 期',F(SANS,16*s),fill=MUTED,alpha=ramp(t,3.0,3.8)*0.85,anchor='ls',tracking=2*s)
    return grade(over(rgb,L.get(),glow_amt=0.25),seed=int(t*24))

@scene('SF02_1979_request',5.0)
def sf02(t,W,H):
    im=img('sf02_1979_crowd')
    if 'g2' not in _cache:
        hsv=cv2.cvtColor((im*255).astype(np.uint8),cv2.COLOR_RGB2HSV).astype(np.float32)
        m=((hsv[...,0]>10)&(hsv[...,0]<32)&(hsv[...,1]>90)&(hsv[...,2]>120)).astype(np.uint8)
        m[int(im.shape[0]*0.42):, :int(im.shape[1]*0.42)]=0; m[:int(im.shape[0]*0.35),:int(im.shape[1]*0.3)]=0
        nlab,lab=cv2.connectedComponents(cv2.dilate(m,np.ones((9,9),np.uint8)))
        area=np.bincount(lab.ravel()); xs_=np.array([np.nonzero(lab==k)[1].mean() if area[k]>0 else 0 for k in range(nlab)])
        big=[k for k in range(1,nlab) if area[k]>120]; big.sort(key=lambda k:xs_[k])
        order={k:i/max(1,len(big)-1) for i,k in enumerate(big)}; _cache['g2']=(lab,order,m)
        gray=im.mean(2,keepdims=True); _cache['d2']=im*0.32+gray*np.array([0.40,0.42,0.56])*0.45
    lab,order,m=_cache['g2']
    on=np.zeros(lab.shape,np.float32)
    for k in range(1,lab.max()+1):
        tk=1.0+1.6*order.get(k,0.5); on[lab==k]=ramp(t,tk,tk+0.6)
    gm=cv2.GaussianBlur(m.astype(np.float32)*on,(0,0),2)[...,None]
    base=_cache['d2']*(1-gm)+np.clip(im*(1.15+0.5*gm),0,1)*gm
    z=1.34+0.10*ease(t/5); cx,cy=0.63+0.02*t/5,0.46
    rgb=cam(base,W,H,zoom=z,cx=cx,cy=cy); rgb=glow(rgb,0.6,W/90,0.7)
    rgb=over(rgb,drift_specks(W,H,t,40,5,(255,220,170),0.25),shadow=0)
    L=Layer(W,H); s=W/1280
    L.rrect((56*s,52*s,470*s,124*s),6*s,fill=(14,20,40),alpha=0.75*ramp(t,0.2,0.9))
    L.line([(56*s,52*s),(56*s,124*s)],fill=GOLD,width=3*s,alpha=ramp(t,0.2,0.9))
    L.text((76*s,84*s),'Francis Crick · 1979',F(SANS_B,23*s),fill=CREAM,alpha=ramp(t,0.3,1.0),anchor='ls')
    L.text((76*s,110*s),'《科学美国人》 Thinking about the Brain',F(SANS,16*s),fill=MUTED,alpha=ramp(t,0.4,1.1),anchor='ls')
    a=ramp(t,2.6,3.4)
    L.rrect((830*s,574*s,1224*s,672*s),8*s,fill=(14,20,40),alpha=0.6*a)
    L.dot((856*s,604*s),6*s,fill=GOLD,alpha=a); L.text((874*s,612*s),'只动某一类神经元',F(SANS_B,25*s),fill=CREAM,alpha=a,anchor='ls')
    b=ramp(t,3.3,4.0)
    L.dot((856*s,646*s),6*s,fill=(130,134,160),alpha=b); L.text((874*s,654*s),'其余的大体不动',F(SANS,22*s),fill=MUTED,alpha=b,anchor='ls')
    return grade(over(rgb,L.get()),seed=int(t*24))

@scene('SF03_microbe_clues',5.0)
def sf03(t,W,H):
    im=img('sf03c_microbes'); k=t/5; z=1.03+0.06*ease(k); cxx=0.5-0.02*k
    rgb=cam(im,W,H,zoom=z,cx=cxx,cy=0.5)
    sx,_=to_px(im,0.503,0.5,W,H,z,cxx,0.5)
    rgb=rgb+radial(W,H,sx,H*0.35,W*0.04,CYAN,0.10*(0.8+0.2*math.sin(t*3)))
    rgb=over(rgb,drift_specks(W,H,t,70,7,(190,230,255),0.35,1.4,(10,-4)),shadow=0)
    ex,ey=to_px(im,0.766,0.528,W,H,z,cxx,0.5); rgb=rgb+radial(W,H,ex,ey,W*0.012,(255,120,60),0.5*ramp(t,2.0,2.6)*(0.8+0.2*math.sin(t*6)))
    L=Layer(W,H); s=W/1280
    L.rrect((28*s,30*s,330*s,72*s),6*s,fill=(12,18,38),alpha=0.7*ramp(t,0.1,0.8))
    L.text((44*s,58*s),'接下来的那些年 · 微生物那边',F(SANS,18*s),fill=CREAM,alpha=ramp(t,0.1,0.8)*0.9,anchor='ls',tracking=3*s)
    ax,ay=to_px(im,0.33,0.56,W,H,z,cxx,0.5)
    label(L,(ax,ay),(60*s,640*s),'1981 · 古菌 · 盐视紫红质','嗜盐古菌膜上的光驱动氯离子泵',t=ramp(t,0.6,2.0),accent=GOLD,font_size=LT*s,sub_size=LS*s)
    label(L,(ex,ey),(1220*s,640*s),'1991–1996 · 衣藻 · 微秒级光电流','眼点受光，膜上立刻出现电流',t=ramp(t,2.0,3.4),accent=CYAN,font_size=LT*s,sub_size=LS*s)
    return grade(over(rgb,L.get()),seed=int(t*24))

@scene('SF04_crick_quote',5.0)
def sf04(t,W,H):
    s=W/1280; P0=load(G+'sf04_crick_portrait.png'); bg=np.concatenate([P0[:30,:30].reshape(-1,3),P0[:30,-30:].reshape(-1,3)]).mean(0)
    rgb=np.zeros((H,W,3),np.float32)+bg; rgb=rgb+radial(W,H,W*0.28,H*0.42,W*0.25,(50,70,130),0.25)
    ph=int(H*0.94); pw=ph; pa=ramp(t,0,0.8); dx=int(14*s*(1-ease_out(ramp(t,0,1.5))))
    P=cam(P0,pw,ph,zoom=1.0+0.035*t/5)
    yy,xx=np.mgrid[0:ph,0:pw]; e=np.minimum.reduce([xx/pw*3,(1-xx/pw)*1.6,yy/ph*4,(1-yy/ph)*2.2]); m=(np.clip(e,0,1)**1.4*pa)[...,None]
    x0=int(30*s)-dx; y0=H-ph
    rgb[y0:,x0:x0+pw]=rgb[y0:,x0:x0+pw]*(1-m)+P*m
    rgb=over(rgb,drift_specks(W,H,t,30,9,(240,220,180),0.25),shadow=0)
    L=Layer(W,H)
    L.text((690*s,246*s),'1999',F(SANS_B,20*s),fill=GOLD,alpha=ramp(t,0.5,1.1),anchor='ls',tracking=6*s)
    L.text((690*s,318*s),'“理想的信号会是光。”',F(SERIF_B,46*s),fill=CREAM,alpha=ramp(t,0.8,1.8),anchor='ls')
    L.text((690*s,392*s),'——他也承认，',F(SERIF,27*s),fill=MUTED,alpha=ramp(t,2.2,2.8),anchor='ls')
    L.text((690*s,448*s),'这个想法相当牵强。',F(SERIF_B,38*s),fill=GOLD,alpha=ramp(t,2.6,3.4),anchor='ls')
    L.line([(690*s,490*s),(690*s+440*s*ease_out(ramp(t,3.2,4.2)),490*s)],fill=(90,100,135),width=1*s)
    L.text((690*s,522*s),'原文 “rather far-fetched”',F(SANS,17*s),fill=CREAM,alpha=ramp(t,3.4,4.2)*0.8,anchor='ls')
    L.text((690*s,548*s),'F. Crick, Phil. Trans. R. Soc. Lond. B, 1999',F(SANS,16*s),fill=MUTED,alpha=ramp(t,3.5,4.3),anchor='ls')
    return grade(over(rgb,L.get(),glow_amt=0.15),seed=int(t*24))

@scene('SF05_nobel_portraits',5.0)
def sf05(t,W,H):
    s=W/1280; bg=img('sf05_nobel_hegemann')[5:40,5:40].reshape(-1,3).mean(0); rgb=np.zeros((H,W,3),np.float32)+bg
    rgb=rgb+radial(W,H,W*0.5,H*0.05,W*0.45,(80,90,150),0.18)
    names=[('sf05_nobel_deisseroth','Karl Deisseroth'),('sf05_nobel_hegemann','Peter Hegemann'),('sf05_nobel_nagel','Georg Nagel')]
    L=Layer(W,H); cw=int(368*s); gap=int(30*s); x0=(W-3*cw-2*gap)//2; y0=int(150*s)
    for i,(n,nm) in enumerate(names):
        a=ramp(t,0.5+i*0.45,1.3+i*0.45); dy=int(26*s*(1-ease_out(a)))
        P=cam(img(n),cw,cw,zoom=1.0+0.03*t/5)
        x=x0+i*(cw+gap); y=y0+dy
        yy,xx=np.mgrid[0:cw,0:cw]; e=np.minimum.reduce([xx/cw,1-xx/cw,yy/cw,(1-yy/cw)*0.6]); m=(np.clip(e/0.12,0,1)**1.5)[...,None]*a
        rgb[y:y+cw,x:x+cw]=rgb[y:y+cw,x:x+cw]*(1-m)+P*m
        L.line([(x+10*s,y0+cw+16*s),(x+10*s+(cw-20*s)*ease_out(a),y0+cw+16*s)],fill=GOLD,width=1.3*s,alpha=a)
        L.text((x+cw/2,y0+cw+56*s),nm,F(SERIF_B,27*s),fill=CREAM,alpha=a,anchor='ms')
    L.text((W/2,72*s),'2026 年 10 月 5 日  ·  诺贝尔生理学或医学奖',F(SANS_B,25*s),fill=GOLD,alpha=ramp(t,0,0.6),anchor='ms',tracking=2*s)
    L.text((W/2,110*s),'获奖理由：发现光控离子通道，并由此建立光遗传学',F(SERIF,19*s),fill=CREAM,alpha=ramp(t,2.2,3.0)*0.9,anchor='ms')
    L.text((W/2,H-26*s),'据诺贝尔奖官方新闻稿 · 头像为插画',F(SANS,15*s),fill=MUTED,alpha=ramp(t,2.6,3.4)*0.8,anchor='ms')
    return grade(over(rgb,L.get()),seed=int(t*24))

@scene('SF06_switch_diagram',6.0)
def sf06(t,W,H):
    s=W/1280
    if 'bg6' not in _cache:
        b=cv2.GaussianBlur(img('sf01b_open_bg'),(0,0),9)*0.35; _cache['bg6']=b
    rgb=cam(_cache['bg6'],W,H,zoom=1.15+0.04*t/6,cx=0.55,cy=0.5)+np.array(INK)/255*0.4
    L0=Layer(W,H); off=(t*6*s)%(40*s)
    for gx in range(-1,34):
        for gy in range(-1,19): L0.dot((gx*40*s+off,gy*40*s+off*0.5),0.9*s,fill=(80,95,140),alpha=0.4)
    rgb=over(rgb,L0.get(),shadow=0)
    L=Layer(W,H); cy=345*s
    L.text((W/2,92*s),'从设想到方法，中间缺什么？',F(SERIF_B,30*s),fill=CREAM,alpha=ramp(t,0,0.7)*0.95,anchor='ms',tracking=2*s)
    a1=ramp(t,0.2,1.0); x1=250*s; R=105*s
    P=circ(G+'sf04_crick_portrait.png',(0.2,0.08,0.68,0.56),int(R)); L.paste(P,((x1-R),(cy-R)),alpha=a1); L.ring((x1,cy),R+1*s,fill=GOLD,width=1.6*s,alpha=a1)
    L.text((x1,cy+R+52*s),'一句自认牵强的设想',F(SANS_B,27*s),fill=CREAM,alpha=a1,anchor='ms')
    L.text((x1,cy+R+82*s),'“理想的信号会是光” · 1999',F(SANS,17*s),fill=MUTED,alpha=a1,anchor='ms')
    xs=640*s; c1=ease(ramp(t,0.9,1.9)); xa=x1+R+12*s; xb=xs-132*s
    L.line([(xa,cy),(xa+(xb-xa)*c1,cy)],fill=(130,150,200),width=1.5*s,alpha=0.9)
    a2=ramp(t,1.5,2.1); fill_in=ease_out(ramp(t,2.6,3.6))
    L.rrect((xs-125*s,cy-125*s,xs+125*s,cy+125*s),22*s,fill=(12,18,38),outline=CYAN if fill_in>0.5 else (130,150,200),width=1.8*s,alpha=a2)
    if fill_in<1: L.text((xs,cy+22*s),'?',F(SERIF_B,72*s),fill=MUTED,alpha=a2*(1-fill_in),anchor='ms')
    if fill_in>0:
        ch=Image.open(G+'sf09c_chr2.png').convert('RGB'); w,h=ch.size; ch=ch.crop((int(0.30*w),int(0.08*h),int(0.70*w),int(0.80*h))).resize((int(236*s),int(236*s)),Image.LANCZOS)
        mk=Image.new('L',ch.size,0); ImageDraw.Draw(mk).rounded_rectangle([0,0,ch.size[0]-1,ch.size[1]-1],int(20*s),fill=255); ch.putalpha(mk)
        L.paste(ch,(xs-118*s,cy-118*s+(1-fill_in)*-50*s),alpha=fill_in)
    a3=ramp(t,3.2,3.9)
    L.text((xs,cy+R+52*s),'一枚能用光拨动的开关',F(SANS_B,30*s),fill=CYAN,alpha=a3,anchor='ms')
    L.text((xs,cy+R+82*s),'光控离子通道（如 ChR2）',F(SANS,17*s),fill=MUTED,alpha=a3,anchor='ms')
    c2=ease(ramp(t,3.6,4.5)); xc=xs+132*s; x3=1035*s; xd=x3-160*s
    L.line([(xc,cy),(xc+(xd-xc)*c2,cy)],fill=(130,150,200),width=1.5*s,alpha=0.9)
    for i,n in enumerate(['sf05_nobel_deisseroth','sf05_nobel_hegemann','sf05_nobel_nagel']):
        a=ramp(t,4.2+i*0.2,4.8+i*0.2); px=x3+(i-1)*98*s; py=cy+(-46 if i==1 else 34)*s; r=60*s; dy=(1-ease_out(a))*14*s
        L.paste(circ(G+n+'.png',(0.2,0.08,0.8,0.68),int(r)),(px-r,py-r+dy),alpha=a); L.ring((px,py+dy),r+1*s,fill=GOLD,width=1.3*s,alpha=a)
    a4=ramp(t,4.6,5.2)
    L.text((x3,cy+R+52*s),'一套能用的方法',F(SANS_B,27*s),fill=CREAM,alpha=a4,anchor='ms')
    L.text((x3,cy+R+82*s),'光遗传学 · 2026 诺奖',F(SANS,17*s),fill=MUTED,alpha=a4,anchor='ms')
    rgb=over(rgb,L.get(),glow_amt=0.2)
    for ph in range(3):
        u=((t*0.55+ph/3)%1.0)
        if c1>0.99: rgb=rgb+radial(W,H,xa+(xb-xa)*u,cy,5*s,CYAN,0.9)
        if c2>0.99: rgb=rgb+radial(W,H,xc+(xd-xc)*u,cy,5*s,CYAN,0.9)
    if fill_in>0: rgb=rgb+radial(W,H,xs,cy,160*s,CYAN,0.16*fill_in*(0.85+0.15*math.sin(t*4)))
    return grade(rgb,seed=int(t*24))

@scene('SF07_main_title',5.0)
def sf07(t,W,H):
    s=W/1280; im=img('sf07c_title_bg'); ih,iw=im.shape[:2]
    if 'p7' not in _cache:
        bg=np.concatenate([im[:40,:40].reshape(-1,3),im[-40:,:40].reshape(-1,3),im[-40:,-40:].reshape(-1,3)]).mean(0)
        cm=cyan_mask(im,175,1.0); ys,xs=np.nonzero(cm>0.5); rng=np.random.default_rng(2); idx=rng.choice(len(xs),min(160,len(xs)),replace=False)
        pts=[(xs[i]/iw,ys[i]/ih) for i in idx]; tip=(0.595,0.245)
        _cache['p7']=(bg,pts,tip)
    bg,pts,tip=_cache['p7']
    z=1.0+0.06*ease(t/5); sc_=H*1.25/ih*z; Wi,Hi=int(iw*sc_),int(ih*sc_)
    ox=W/2-Wi*0.5; oy=-0.045*Hi+10*s*(1-t/5)
    M=np.array([[sc_,0,ox],[0,sc_,oy]],np.float32)
    rgb=np.zeros((H,W,3),np.float32)+bg
    pic=cv2.warpAffine(im,M,(W,H),flags=cv2.INTER_CUBIC,borderMode=cv2.BORDER_CONSTANT,borderValue=tuple(float(v) for v in bg))
    yy,xx=np.mgrid[0:H,0:W]; e=np.minimum((xx-ox)/(140*s),(ox+Wi-xx)/(140*s)); mk=np.clip(e,0,1)[...,None]
    rgb=rgb*(1-mk)+pic*mk
    # sparks along fibers, ordered by distance from fiber tip
    L=Layer(W,H)
    for (px,py) in pts:
        d=math.hypot(px-tip[0],(py-tip[1])*1.5); tk=0.7+d*4.0; a=math.exp(-((t-tk)/0.18)**2)+0.25*(t>tk)
        X=ox+px*Wi; Y=oy+py*Hi; L.dot((X,Y),2.2*s,fill=(170,225,255),alpha=min(1,a))
    rgb=over(rgb,L.get(),shadow=0,glow_amt=1.4)
    rgb=over(rgb,drift_specks(W,H,t,60,11,(180,205,255),0.3),shadow=0)
    L=Layer(W,H)
    a=ramp(t,1.0,2.2); tr=(60*(1-ease_out(ramp(t,1.0,3.2)))+34)*s
    L.text((W/2,590*s),'光遗传学',F(SERIF_B,118*s),fill=CREAM,alpha=a,anchor='ms',tracking=tr)
    L.text((W/2,636*s),'O P T O G E N E T I C S',F(SANS,17*s),fill=CYAN,alpha=ramp(t,2.0,2.8),anchor='ms',tracking=4*s)
    L.text((W/2,672*s),'这一期，就讲这枚开关',F(SANS,18*s),fill=MUTED,alpha=ramp(t,2.6,3.4),anchor='ms',tracking=4*s)
    return grade(over(rgb,L.get(),glow_amt=0.35),seed=int(t*24))

@scene('SF08_early_attempts',6.5)
def sf08(t,W,H):
    im=img('sf08c_relay'); s=W/1280; z=1.03+0.03*t/6.5; cxx=0.5; cyy=0.47
    rgb=cam(im,W,H,zoom=z,cx=cxx,cy=cyy)
    P=lambda x,y: to_px(im,x,y,W,H,z,cxx,cyy)
    path=[(0.115,0.33),(0.245,0.53),(0.41,0.52),(0.575,0.47)]
    u=ramp(t,0.9,3.4)*(len(path)-1); i=min(int(u),len(path)-2); f=u-i
    if 0<u<len(path)-1+1e-6 and t<3.6:
        px=path[i][0]+(path[i+1][0]-path[i][0])*f; py=path[i][1]+(path[i+1][1]-path[i][1])*f
        X,Y=P(px,py); rgb=rgb+radial(W,H,X,Y,W*0.012,(255,226,176),0.9)+radial(W,H,X,Y,W*0.05,(255,226,176),0.15)
    X,Y=P(0.115,0.29); rgb=rgb+radial(W,H,X,Y,W*0.03,CYAN,0.6*math.exp(-((t-0.7)/0.3)**2))
    openA=ramp(t,3.4,3.9); cxA,cyA=P(0.578,0.47); rgb=rgb+radial(W,H,cxA,cyA,W*0.02,(255,209,102),0.35*openA)
    # right: light hits switch later, channel opens even later (slower)
    lt=ramp(t,3.9,4.4); sx,sy=P(0.80,0.31); rgb=rgb+radial(W,H,sx,sy,W*0.03,(255,90,200),0.5*lt)
    openB=ramp(t,5.3,5.8); cxB,cyB=P(0.835,0.49); rgb=rgb+radial(W,H,cxB,cyB,W*0.02,(255,209,102),0.35*openB)
    L=Layer(W,H)
    for (cx_,cy_,op,ph0) in ((0.578,0.47,openA,0.0),(0.835,0.49,openB,0.3)):
        if op<=0: continue
        for n in range(8):
            p=(t*0.5+n/8+ph0)%1.0; X,Y=P(cx_+0.004*math.sin(n*2.1+p*7),0.30+p*0.42); a=op*min(1,p*8)*min(1,(1-p)*8)
            L.dot((X,Y),5.5*s,fill=(255,209,102),alpha=a)
    rgb=over(rgb,L.get(),shadow=0.2,glow_amt=0.6)
    L=Layer(W,H)
    steps=[((0.115,0.30),'① 感光蛋白','先接住光',(60,96)),((0.245,0.56),'② 信号接力','一步步往下传',(60,610)),((0.41,0.58),'③ 再传一步',None,(420,650)),((0.575,0.36),'④ 通道才打开','离子这时才流过',(860,96))]
    for j,((ax,ay),ti,sub,tp) in enumerate(steps):
        a=ramp(t,0.6+j*0.8,1.3+j*0.8); X,Y=P(ax,ay); label(L,(X,Y),(tp[0]*s,tp[1]*s),ti,sub,t=a,font_size=LT*s,sub_size=LS*s,accent=(255,226,176) if j<3 else (255,209,102))
    X,Y=P(0.80,0.30); label(L,(X,Y),(1220*s,96*s),'外加化学光开关','另需把化学分子送进组织',t=ramp(t,3.9,4.8),font_size=LT*s,sub_size=LS*s,accent=(255,90,200))
    a=ramp(t,4.6,5.2); bx=780*s; by=600*s
    L.rrect((bx,by,1230*s,690*s),8*s,fill=(12,18,38),alpha=0.82*a)
    L.text((bx+18*s,by+30*s),'需要：毫秒级',F(SANS_B,17*s),fill=CYAN,alpha=a,anchor='ls')
    L.line([(bx+170*s,by+24*s),(bx+170*s+40*s*ease_out(ramp(t,4.7,4.9)),by+24*s)],fill=CYAN,width=6*s,alpha=a)
    L.text((bx+18*s,by+68*s),'这两条路：更慢',F(SANS,17*s),fill=CREAM,alpha=a,anchor='ls')
    L.line([(bx+170*s,by+62*s),(bx+170*s+250*s*ramp(t,4.8,6.5),by+62*s)],fill=(255,180,120),width=6*s,alpha=a)
    return grade(over(rgb,L.get()),seed=int(t*24))

@scene('SF09_chr2_channel',5.0)
def sf09(t,W,H):
    im=img('sf09c_chr2'); s=W/1280; z=1.12+0.08*ease(t/5); cxx=0.5; cyy=0.47
    on=ramp(t,0.3,1.2)
    if 'b9' not in _cache: _cache['b9']=cyan_mask(im,140,6)[...,None]
    base=im*(1-_cache['b9']*(1-(0.35+0.65*on)))
    rgb=cam(base,W,H,zoom=z,cx=cxx,cy=cyy)
    P=lambda x,y: to_px(im,x,y,W,H,z,cxx,cyy)
    L=Layer(W,H)
    for (px_,ph0) in ((0.432,0.0),(0.577,0.5)):
        for n in range(9):
            p=(t*0.36+n/9+ph0)%1.0
            if t<1.2 and p>0.2+0.8*ramp(t,0.8,1.2): continue
            X,Y=P(px_+0.004*math.sin(n*2.3+p*8),0.22+p*0.56); a=on*min(1,p*8)*min(1,(1-p)*8)
            L.dot((X,Y),6.5*s*z,fill=(255,209,102),alpha=a)
    rgb=over(rgb,L.get(),shadow=0.3,glow_amt=0.6)
    rgb=over(rgb,drift_specks(W,H,t,40,13,(160,190,255),0.25,1.4,(4,2)),shadow=0)
    L2=Layer(W,H)
    X,Y=P(0.60,0.31); label(L2,(X,Y),(1220*s,96*s),'通道视紫红质-2（ChR2）','二聚体：每个亚基各有一条孔道',t=ramp(t,1.4,2.3),font_size=LT*s,sub_size=LS*s,accent=(99,199,168))
    X,Y=P(0.41,0.555); label(L2,(X,Y),(60*s,630*s),'视黄醛','吸收蓝光，让这扇门打开',t=ramp(t,2.2,3.0),font_size=LT*s,sub_size=LS*s,accent=(255,138,61))
    X,Y=P(0.577,0.68); label(L2,(X,Y),(1220*s,630*s),'阳离子（如钠离子 Na+）','顺浓度梯度涌入细胞',t=ramp(t,2.9,3.7),font_size=LT*s,sub_size=LS*s,accent=(255,209,102))
    X,Y=P(0.24,0.12); label(L2,(max(X,40*s),max(Y,40*s)),(60*s,96*s),'蓝光 约 470 nm',None,t=ramp(t,0.6,1.4),font_size=LT*s,accent=CYAN)
    return grade(over(rgb,L2.get()),seed=int(t*24))

@scene('SF11_eye_goggles',5.0)
def sf11(t,W,H):
    im=img('sf11b_eye'); s=W/1280; z=1.0+0.06*ease(t/5); cxx=0.5; cyy=0.47
    rgb=cam(im,W,H,zoom=z,cx=cxx,cy=cyy)
    P=lambda x,y: to_px(im,x,y,W,H,z,cxx,cyy)
    L=Layer(W,H); fx,fy=0.80,0.465
    for k in range(6):
        y0=0.36+k*0.028
        for n in range(3):
            p=(t*0.7+n/3+k*0.13)%1.0; x=0.18+(fx-0.18)*p; y=y0+(fy-y0)*p
            X,Y=P(x,y); L.dot((X,Y),3.2*s,fill=(255,196,110),alpha=min(1,p*6)*min(1,(1-p)*10)*ramp(t,0.2,0.8))
    rgb=over(rgb,L.get(),shadow=0,glow_amt=1.1)
    # ganglion cells near focus answer with warm spikes (bible: firing = #F0835B)
    rng=np.random.default_rng(5)
    for k in range(9):
        gy=0.40+k*0.016; gx=0.785+0.004*rng.standard_normal(); tk=1.2+((k*0.37)%1.0)*2.2
        a=math.exp(-((t-tk)%1.6/0.12)**2) if t>1.2 else 0
        X,Y=P(gx,gy); rgb=rgb+radial(W,H,X,Y,7*s,(240,131,91),0.9*a)
    L=Layer(W,H)
    X,Y=P(0.12,0.30); label(L,(X,Y),(60*s,640*s),'护目镜','把外界明暗换成琥珀色光脉冲',t=ramp(t,0.4,1.3),font_size=LT*s,sub_size=LS*s,accent=AMBER)
    X,Y=P(0.788,0.42); label(L,(X,Y),(1220*s,90*s),'视网膜神经节细胞','病毒带进 ChrimsonR，受光后放电',t=ramp(t,1.4,2.3),font_size=LT*s,sub_size=LS*s,accent=(240,131,91))
    X,Y=P(0.845,0.33); label(L,(X,Y),(1220*s,650*s),'感光细胞','已大量丢失',t=ramp(t,2.3,3.1),font_size=LT*s,sub_size=LS*s,accent=(170,170,180))
    return grade(over(rgb,L.get()),seed=int(t*24),lift=(0.03,0.04,0.09))

# ---- SF10 round 2: rigged Tripo mouse (quadruped walk), light on f40-52, wakes and walks from f58 ----
_PJ2=None
@scene('SF10_mouse_tripo',5.0)
def sf10(t,W,H,still=False,still_frame=100):
    global _PJ2
    if _PJ2 is None: _PJ2=_json.load(open('/workspace/e2work/v8/work/mouse_proj2.json'))
    f=still_frame if still else min(120,max(1,int(round(t*24))+1))
    rgb=load('/workspace/e2work/v8/renders/m4/f_%04d.png'%f); rgb=cv2.resize(rgb,(W,H),interpolation=cv2.INTER_AREA)
    tip=_PJ2[str(f)]; on=ramp(f,40,52); s=W/1280; X,Y=tip[0]*W,tip[1]*H
    rgb=rgb*(0.86+0.14*on)
    rgb=rgb+radial(W,H,X,Y,22*s,CYAN,1.0*on)+radial(W,H,X,Y+10*s,80*s,CYAN,0.25*on)
    rgb=glow(rgb,0.8,W/120,0.4)
    L2=Layer(W,H); tt=f/24
    label(L2,(X,Y),(1220*s if X<W*0.55 else 60*s,96*s),'光纤 + 颅骨植入件','把蓝光送进下丘脑外侧那群细胞',t=ramp(tt,1.7,2.5),font_size=LT*s,sub_size=LS*s,accent=CYAN)
    a=ramp(tt,0.2,0.9)
    L2.rrect((56*s,612*s,560*s,684*s),6*s,fill=(14,20,40),alpha=0.72*a); L2.line([(56*s,612*s),(56*s,684*s)],fill=GOLD,width=3*s,alpha=a)
    L2.text((76*s,642*s),'2007 · 小鼠 · 食欲素神经元',F(SANS_B,21*s),fill=CREAM,alpha=a,anchor='ls')
    L2.text((76*s,670*s),'光一开：从睡眠转入清醒的概率升高',F(SANS,16*s),fill=MUTED,alpha=a,anchor='ls')
    return grade(over(rgb,L2.get()),vig=0.25,grain=0.012,seed=f,lift=(0.02,0.03,0.07))
