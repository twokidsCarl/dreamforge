# E1 选图包 v1 · 来源表

仅供内部选风格，版权归原作者。图片原件在 box 的 `/workspace/e1work/calib/cand/`，mock-up 在 `/workspace/e1work/calib/mock/`；表格生成参数见 `../../tools/spec_E1.py`。YouTube 帧取自 `i.ytimg.com/vi/<id>/maxres{1,2,3}.jpg`（片长约 25 / 50 / 75 % 处的自动关键帧）或 `maxresdefault.jpg`（官方缩略图）。`rXX` 是 E2 参考包里已有的图（`/workspace/e2work/v8/refs/`，来源见其 SOURCES.md）。

| 表 | 项 | 文件 | 创作者 / 作品 | URL |
|---|---|---|---|---|
| 01 片头 | A | r40_title_ourplanet2.jpg | Netflix《Our Planet II》开场 | https://youtu.be/2R5cB-ukuP8?t=72 |
| 01 | B | r42_title_veritasium_fiber.jpg | Veritasium "The Insane Engineering of Fiber Optics"（缩略图） | https://youtu.be/NiCgcUTL9_Q |
| 01 | C | yt_MiUHjLxm3V0_maxresdefault.jpg | Veritasium "The Ridiculous Engineering Of The World's Most Important Machine"（2025-12-31，缩略图） | https://youtu.be/MiUHjLxm3V0 |
| 01 | D | yt_MfFGRl00LKY_maxresdefault.jpg | ASML "Inside the machine: How a High NA system generates EUV light"（缩略图） | https://youtu.be/MfFGRl00LKY |
| 02 整机 | A | imec_highna_scanner.jpg | ASML 产品渲染（courtesy of ASML），见 imec "High-NA EUVL: the next major step" Fig.1 | https://www.imec-int.com/en/articles/high-na-euvl-next-major-step-lithography |
| 02 | B | yt_B2482h_TNwg_maxresdefault.jpg（裁右上） | Branch Education × ASML "The $200M Machine that Prints Microchips"（缩略图） | https://youtu.be/B2482h_TNwg |
| 02 | C | yt_3PCtf1ONYMU_maxres3.jpg | Intel Newsroom "Intel Receives ASML's First High NA EUV system" | https://youtu.be/3PCtf1ONYMU |
| 02 | D | mock/e1_machine.png | **MOCK-UP**（gpt-image-2 生成），提示词 mock/p_machine.txt | — |
| 03 光源 | A | yt_IattxYrc9Go_maxres1.jpg | ASML "Laser and tin in the light source – Inside the TWINSCAN NXE:3400" | https://youtu.be/IattxYrc9Go |
| 03 | B | yt_NHSR6AHNiDs_maxres2.jpg | TRUMPF "EUV lithography – This all happens in one second" | https://youtu.be/NHSR6AHNiDs |
| 03 | C | nat_sn_fig1.png | "Prominent radiative contributions from multiply-excited states in laser-produced tin plasma for nanolithography", Nature Communications (2020), doi:10.1038/s41467-020-15678-y, Fig. 1（开放获取） | https://www.nature.com/articles/s41467-020-15678-y |
| 03 | D | mock/e1_plasma.png | **MOCK-UP**（gpt-image-2，以 E2 `gen/sf09e_chr2.png` 为画风参考），提示词 mock/p_plasma.txt | — |
| 04 反射镜 | A | yt_B2482h_TNwg_maxres1.jpg | Branch Education × ASML（同 02B） | https://youtu.be/B2482h_TNwg |
| 04 | B | yt_V__HbVlnICc_maxres3.jpg（裁中上，去频道角标） | "How Carl Zeiss Crafts Optics for a $150 Million EUV Machine"（画面来自 ZEISS） | https://youtu.be/V__HbVlnICc |
| 04 | C | yt_1FJ37hzhd1c_maxresdefault.jpg（裁左，去字） | "The Most Precise Mirrors Ever Made (Inside ASML's $400M Machine)"（缩略图） | https://youtu.be/1FJ37hzhd1c |
| 04 | D | nist/i-000.png | NIST，EUV 光学章节 Fig.1：典型 Mo/Si 多层膜 TEM 截面 | https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=921048 |
| 05 掩模 | A | imec_cnt_pellicle.jpg | imec "Imec demonstrates CNT pellicle utilization on EUV scanner"（2020） | https://www.imec-int.com/en/press/imec-demonstrates-cnt-pellicle-utilization-euv-scanner |
| 05 | B | yt_B2482h_TNwg_maxresdefault.jpg（裁左上） | Branch Education × ASML（同 02B） | https://youtu.be/B2482h_TNwg |
| 05 | C（对照） | imec_mask_xsection.jpg | imec "High-NA EUVL: the next major step" Fig.5 EUV 掩模剖面示意 | https://www.imec-int.com/en/articles/high-na-euvl-next-major-step-lithography |
| 06 晶圆 | A | cm_wafer_diffract.jpg | Wikimedia Commons "Diffracted Light Spectrum on Patterned Silicon Wafer" | https://commons.wikimedia.org/wiki/File:Diffracted_Light_Spectrum_on_Patterned_Silicon_Wafer.jpg |
| 06 | B | imec_highna_first_exposures.jpg（裁右栏 10 nm MOR） | imec "Entering the High NA EUV Lithography era"（2024）Fig.1 | https://www.imec-int.com/en/articles/entering-high-na-euv-lithography-era |
| 06 | C | yt_dX9CGRZwD-w_maxres1.jpg（裁左） | Branch Education "How are Microchips Made?" | https://youtu.be/dX9CGRZwD-w |
| 06 | D | mock/e1_wafer.png | **MOCK-UP**（gpt-image-2，E2 画风参考），提示词 mock/p_wafer.txt | — |
| 07 信息图 | A | yt__Pqfjer8-O4_maxres3.jpg | Branch Education "How do Transistors Work?" | https://youtu.be/_Pqfjer8-O4 |
| 07 | B | r21_nucleus_stroke_vessel.jpg | Nucleus Medical Media "How Stroke Affects Your Brain" | https://youtu.be/_lAmW2ree3Q?t=143 |
| 07 | C（对照） | r25_3b1b_network.jpg | 3Blue1Brown "But what is a neural network?" | https://youtu.be/aircAruvnKk?t=840 |
| 08 纪实 | A | cm_747_cargolux_tpe.jpg | Wikimedia Commons "Cargolux Boeing 747-8 (LX-VCB) at Taiwan Taoyuan International Airport" | https://commons.wikimedia.org/wiki/File:Cargolux_Boeing_747-8_(LX-VCB)_at_Taiwan_Taoyuan_International_Airport.jpg |
| 08 | B | yt_3PCtf1ONYMU_maxres1.jpg | Intel Newsroom（同 02C） | https://youtu.be/3PCtf1ONYMU |
| 08 | C | imec_cleanroom_300mm.jpg | imec "A look inside imec's 300 mm cleanroom"（见 "Entering the High NA EUV Lithography era" 页） | https://www.imec-int.com/en/articles/entering-high-na-euv-lithography-era |
| 08 | D | mock/e1_docu.png | **MOCK-UP**（gpt-image-2，E2 画风参考），提示词 mock/p_docu.txt | — |
| 09 人物 | A | yt_NHSR6AHNiDs_maxres1.jpg | TRUMPF（同 03B） | https://youtu.be/NHSR6AHNiDs |
| 09 | B | yt_1JkzrR-hznE_maxresdefault.jpg（裁右，去字） | CNBC "How ASML Makes Chips Faster With Its New $400 Million High NA Machine"（缩略图） | https://youtu.be/1JkzrR-hznE |
| 09 | C | imec_cleanroom_020.jpg | imec cleanroom 照片（同 08C 页） | https://www.imec-int.com/en/articles/entering-high-na-euv-lithography-era |
| 09 | D | mock/e1_people.png | **MOCK-UP**（gpt-image-2 生成），提示词 mock/p_people.txt | — |

花费：image2（gpt-image-2，medium，1536×1024）6 张，按返回 usage 估算 $0.23；记账 `/workspace/e1work/calib/costs_image2.jsonl` 和 `episodes/E1-euv-lithography/handoff/E1_SPEND.md`。无 GPU，无 Wan。
