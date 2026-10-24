import sys, glob
from PIL import Image, ImageDraw
fs=sys.argv[2:]; out=sys.argv[1]
cols=3; w=640; h=360
rows=(len(fs)+cols-1)//cols
c=Image.new('RGB',(cols*w,rows*h))
for i,f in enumerate(fs):
    im=Image.open(f).convert('RGB').resize((w,h)); ImageDraw.Draw(im).text((6,6),f.split('/')[-1],fill=(255,255,0))
    c.paste(im,((i%cols)*w,(i//cols)*h))
c.save(out,quality=85)
