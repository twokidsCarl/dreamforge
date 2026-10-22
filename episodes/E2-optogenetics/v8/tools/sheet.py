import sys
from PIL import Image,ImageDraw,ImageFont
out=sys.argv[1]; fs=sys.argv[2:]; W=480; cols=3
F=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',16)
ims=[]
for f in fs:
    im=Image.open(f).convert('RGB'); im=im.resize((W,int(W*im.height/im.width))); ims.append((f.split('/')[-1],im))
H=max(i.height for _,i in ims)+22; rows=(len(ims)+cols-1)//cols
s=Image.new('RGB',(W*cols,H*rows),'white'); d=ImageDraw.Draw(s)
for k,(n,im) in enumerate(ims):
    x,y=(k%cols)*W,(k//cols)*H; s.paste(im,(x,y+22)); d.text((x+4,y+2),n,fill='black',font=F)
s.save(out,quality=88)
