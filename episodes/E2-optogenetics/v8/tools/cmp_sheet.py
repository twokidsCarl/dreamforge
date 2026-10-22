from PIL import Image,ImageDraw,ImageFont
V='/workspace/e2work/v8/'
F=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',18,index=2); FB=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc',20,index=2)
rows=[('SF01 片头标题卡（新增）','3.5','0:03 v7 无片名','r42_title_veritasium_fiber','SF01_open_title'),
('SF02 1979 要求（Carl 0:06）','6','0:06','r30_mcgovern_neuron_glow','SF02_1979_request'),
('SF03 微生物线索（Carl 0:13）','13','0:13','r03_kurzgesagt_bacteria_depth','SF03_microbe_clues'),
('SF04 Crick 1999 引文（Carl 0:27「相当牵」）','27','0:27','r41_title_3bodyproblem_credits','SF04_crick_quote'),
('SF05 诺奖漫画头像（Carl 0:50）','50','0:50','r36_elmehed_hegemann','SF05_nobel_portraits'),
('SF06 设想→开关→方法（Carl 0:59 跳帧）','59','0:59','r26_3b1b_convolution','SF06_switch_diagram'),
('SF07 片名（Carl 1:07 纯字）','67','1:07','r40_title_ourplanet2','SF07_main_title'),
('SF08 早先的光控尝试（Carl 2:03 白模）','123','2:03','r06_goodsell_synapses','SF08_early_attempts'),
('SF09 ChR2 通道（Carl 2:21 Goodsell）','141','2:21','r10_goodsell_rhodopsin_membrane','SF09_chr2_channel'),
('SF10 Tripo 绑骨小鼠（Carl 2:23 小鼠）','167','2:47 A_08a','r43_mouse_3d_fiber_implant','SF10_mouse_tripo'),
('SF11 眼球 / 器官（C_08a）','600','10:00','r19_nucleus_eye_retina_inside','SF11_eye_goggles')]
W=480; H=270; pad=34
S=Image.new('RGB',(W*3+40,60+len(rows)*(H+pad)),(18,22,36)); d=ImageDraw.Draw(S)
for j,h in enumerate(['v7 原帧','参考帧（100 分锚点）','v8 样张']): d.text((20+j*W+W//2,22),h,font=FB,fill=(240,235,225),anchor='mm')
def fit(p):
    im=Image.open(p).convert('RGB'); r=min(W/im.width,H/im.height); im=im.resize((int(im.width*r),int(im.height*r)),Image.LANCZOS)
    c=Image.new('RGB',(W,H),(10,12,20)); c.paste(im,((W-im.width)//2,(H-im.height)//2)); return c
for i,(name,t,tl,ref,sf) in enumerate(rows):
    y=50+i*(H+pad); d.text((20,y+2),name,font=F,fill=(233,184,92))
    for j,p in enumerate([V+f'v7frames/cmp_{t}.png',V+f'refs/{ref}.jpg',V+f'styleframes/{sf}.png']):
        S.paste(fit(p),(20+j*W,y+28))
    d.text((24,y+28+H-24),'v7 '+tl,font=F,fill=(255,255,255))
S.save(V+'styleframes/SHEET_v7_ref_v8.jpg',quality=88); print(S.size)
