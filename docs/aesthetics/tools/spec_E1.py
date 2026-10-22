import json
R='/workspace/e2work/v8/refs/'; C='/workspace/e1work/calib/cand/'; M='/workspace/e1work/calib/mock/'; O='/workspace/e1work/calib/'
Y=lambda i,k='maxresdefault': C+f'yt_{i}_{k}.jpg'
S=[
dict(out=O+'01_title.jpg',title='01 片头标题卡',shots='A0_10 片名《一台光刻机里发生了什么》 + 品牌片头后',q='问：片名卡要哪种气质？（可多选，或写「都不要，要更像 X」）',cands=[
 dict(src=R+'r40_title_ourplanet2.jpg',tag='Netflix · Our Planet II',cap='宽字距细体大写，字压在发光主体上，近黑底'),
 dict(src=R+'r42_title_veritasium_fiber.jpg',tag='Veritasium · Fiber Optics',cap='主体自己发光做唯一光源，大号衬线字'),
 dict(src=Y('MiUHjLxm3V0'),tag='Veritasium · World\'s Most Important Machine',cap='同题材：白衬线短句 + 整机全景 + 人做尺度'),
 dict(src=Y('MfFGRl00LKY'),tag='ASML · Making EUV light',cap='同题材：粗无衬线字压在等离子强光上')]),
dict(out=O+'02_machine.jpg',title='02 整机 / 系统外观',shots='A0_10 · B5_01 · C_03 · D_06 · D_07（红线：不仿 ASML 外观和标志）',q='问：整台机器出现时用哪种呈现？',cands=[
 dict(src=C+'imec_highna_scanner.jpg',mode='contain',tag='ASML via imec · High-NA scanner',cap='官方白色产品棚拍：只学布光留白，不仿外观'),
 dict(src={'p':Y('B2482h_TNwg'),'crop':[0.36,0,1,0.6]},tag='Branch Education × ASML',cap='CG 剖视：去掉机壳，紫色光路贯穿各模块'),
 dict(src=Y('3PCtf1ONYMU','maxres3'),tag='Intel Newsroom · first High NA',cap='实拍纪实：洁净室里正在组装的整机'),
 dict(src=M+'e1_machine.png',mock=True,tag='gpt-image-2 mock-up',cap='无品牌暗厅剪影，只靠轮廓光和缝隙紫光')]),
dict(out=O+'03_tin_plasma.jpg',title='03 锡滴 + 激光 → 等离子体光源',shots='A0_01 · B1_03–B1_15 · B2_* · B3_02 · D_08 · D_09',q='问：光源腔里的锡滴、激光和等离子体用哪种画法？',cands=[
 dict(src=Y('IattxYrc9Go','maxres1'),tag='ASML · NXE:3400 laser and tin',cap='官方 CG：金属腔体写实，中心紫色等离子辉光'),
 dict(src=Y('NHSR6AHNiDs','maxres2'),tag='TRUMPF · EUV in one second',cap='极简黑底：高速锡滴拖尾成一道紫色光'),
 dict(src=C+'nat_sn_fig1.png',mode='contain',tag='Nature Commun. (2020) · Fig.1',cap='科研实拍：真实等离子照片 + 13.5 nm 光谱'),
 dict(src=M+'e1_plasma.png',mock=True,tag='gpt-image-2 mock-up',cap='沿用 E2 插画家族：描边、饱和、柔光')]),
dict(out=O+'04_mirrors.jpg',title='04 多层膜反射镜与反射光路',shots='A2_08 · B3_02 · B4_04–B4_10 · B5_01 · B7_06 · C_03',q='问：反射镜和镜间光路用哪种画法？（D 是镜子内部的纳米层）',cands=[
 dict(src=Y('B2482h_TNwg','maxres1'),tag='Branch Education × ASML',cap='CG 机内剖视：紫光在金属镜座间折返'),
 dict(src={'p':Y('V__HbVlnICc','maxres3'),'crop':[0.12,0,0.70,0.6]},tag='ZEISS 实拍（经 YouTube）',cap='实拍：工程师围着巨大镜面，镜里映出厂房'),
 dict(src={'p':Y('1FJ37hzhd1c'),'crop':[0,0,0.55,1]},mode='contain',tag='YouTube · The Most Precise Mirrors',cap='实拍产品照：手套托着的超光滑镜面'),
 dict(src=C+'nist/i-000.png',mode='contain',tag='NIST · Mo/Si 多层膜 TEM 截面',cap='实拍电镜截面：约 40 对钼/硅层，黑白')]),
dict(out=O+'05_mask_pellicle.jpg',title='05 掩模 / 掩模版 / 保护膜（pellicle）',shots='B6_01–B6_12 · C_03',q='问：掩模和 13 nm 保护膜用哪种呈现？',cands=[
 dict(src=C+'imec_cnt_pellicle.jpg',tag='imec · CNT pellicle (2020)',cap='实拍：手套托着的真实保护膜，薄、透'),
 dict(src={'p':Y('B2482h_TNwg'),'crop':[0,0,0.62,0.72]},tag='Branch Education × ASML',cap='CG：光打到掩模上，放大框看图形'),
 dict(src=C+'imec_mask_xsection.jpg',ctrl=True,mode='contain',tag='imec · EUV mask cross-section',cap='扁平剖面示意 + 文字标注（对照）')]),
dict(out=O+'06_wafer_nano.jpg',title='06 晶圆 / 芯片 / 纳米图形',shots='A0_07 · A0_08 · B8_* · B9_* · D_01',q='问：晶圆和纳米尺度的线条、晶体管用哪种画法？',cands=[
 dict(src=C+'cm_wafer_diffract.jpg',tag='Wikimedia Commons · patterned wafer',cap='实拍晶圆：分区衍射彩光，真实质感'),
 dict(src={'p':C+'imec_highna_first_exposures.jpg','crop':[0.64,0,1,1]},mode='contain',tag='imec · first High-NA exposures (2024)',cap='实拍电镜：10 nm 线条，灰阶 SEM'),
 dict(src={'p':Y('dX9CGRZwD-w','maxres1'),'crop':[0,0,0.5,1]},mode='contain',tag='Branch Education · How are Microchips Made',cap='CG 剖视：芯片里一层层金属连线'),
 dict(src=M+'e1_wafer.png',mock=True,tag='gpt-image-2 mock-up',cap='沿用 E2 插画家族 + 圆形放大框')]),
dict(out=O+'07_scale_infographic.jpg',title='07 尺度对比与数据信息图',shots='A0_03 · A0_06 · A2_03 · B1_18 · B4_10 · B8_17 · B9_05',q='问：数字、比例和对比用哪种图解方式？',cands=[
 dict(src=Y('_Pqfjer8-O4','maxres3'),tag='Branch Education · Transistors',cap='3D 实物做尺度：地球、芯片放在一个画面里'),
 dict(src=R+'r21_nucleus_stroke_vessel.jpg',tag='Nucleus · How Stroke Affects…',cap='数字和标注做成半透明底条，叠在 3D 画面上'),
 dict(src=R+'r25_3b1b_network.jpg',ctrl=True,tag='3Blue1Brown · neural network',cap='纯深底极简线条和数字（对照，E2 未选）')]),
dict(out=O+'08_documentary.jpg',title='08 纪实：货机、车队、洁净室',shots='A0_02 · A0_03 · D_06 · D_07（Carl 决定 3：可用 image2 + Wan 背景板）',q='问：纪实段落要哪种观感？',cands=[
 dict(src=C+'cm_747_cargolux_tpe.jpg',tag='Wikimedia Commons · Cargolux 747-8F',cap='实拍照片感：夜间货机开鼻装货，钠灯'),
 dict(src=Y('3PCtf1ONYMU','maxres1'),tag='Intel Newsroom · first High NA',cap='官方纪实航拍：白色货箱卡车进厂'),
 dict(src=C+'imec_cleanroom_300mm.jpg',tag='imec · 300 mm cleanroom',cap='实拍洁净室：冷白光，设备排开'),
 dict(src=M+'e1_docu.png',mock=True,tag='gpt-image-2 mock-up',cap='沿用 E2 插画家族的夜间货机装货')]),
dict(out=O+'09_people.jpg',title='09 人物（红线：只用剪影，无脸）',shots='D_06 · D_07 · B 段工程师',q='问：人出现时取哪种构图和氛围？（实拍项只看构图，成片一律做剪影）',cands=[
 dict(src=Y('NHSR6AHNiDs','maxres1'),tag='TRUMPF · EUV in one second',cap='兔子服两人走过洁净室，中景纪实'),
 dict(src={'p':Y('1JkzrR-hznE'),'crop':[0.5,0.17,1,1]},mode='contain',tag='CNBC · ASML High NA',cap='人站在机器旁做尺度，机器占满背景'),
 dict(src=C+'imec_cleanroom_020.jpg',tag='imec · cleanroom',cap='近景工作特写：手、屏幕、兔子服'),
 dict(src=M+'e1_people.png',mock=True,tag='gpt-image-2 mock-up',cap='逆光剪影群像，顶灯一排排亮起')]),
]
json.dump(S,open(O+'spec.json','w'),ensure_ascii=False,indent=1)
