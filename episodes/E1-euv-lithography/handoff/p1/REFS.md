# E1 风格帧参考帧（rE 系列 + E2 跨题材锚）

图片不入库（版权归原作者），放在 box 的 `/workspace/e1work/p1/refs/`。YouTube 帧取自 `i.ytimg.com/vi/<id>/maxres{1,2,3}.jpg`（片长约 25 / 50 / 75 % 处的自动关键帧）或官方缩略图。

| 文件 | 来源 | 学什么 |
|---|---|---|
| rE01_branch_euv_mirror_path.jpg | Branch Education × ASML「The $200M Machine that Prints Microchips」 https://youtu.be/B2482h_TNwg | 机内剖视：金属镜座材质、紫色 EUV 光束在镜间折返、景深 |
| rE02_branch_euv_mask_wafer_light.jpg | 同上（缩略图） | 光路 → 掩模 → 晶圆在一张图里讲清；紫光与暗金属的光比 |
| rE03_branch_euv_resist_spin.jpg | 同上 | 旋涂光刻胶的写实微距：暖光、反射、标题字 |
| rE04_branch_euv_machine_exterior.jpg | 同上 | 整机外观（只学光与留白；**不得仿制外观或标志**） |
| rE05_branch_fab_cutaway_split.jpg | Branch Education「How are Microchips Made?」 https://youtu.be/dX9CGRZwD-w | 剖视模型与实景并列，同一套光 |
| rE06_branch_chip_layers.jpg | 同上 | 芯片层级与晶体管阵列：饱和色块 + 清楚层次 |
| rE07_branch_clay_robot_wafer.jpg | 同上 | 白模机械：棚拍光、AO、干净背景——白模的及格线 |
| rE08_branch_wafer_diffraction.jpg | 同上（缩略图） | 晶圆衍射色按区块分布（不是整片彩虹） |
| rE09_asml_euv_plasma.jpg | ASML「Inside the machine: How a High NA system generates EUV light」 https://youtu.be/MfFGRl00LKY（缩略图） | 等离子体发光的官方观感 |
| r14 / r22 / r25 / r27 / r32 / r40 / r42 | E2 参考包（`/workspace/e2work/v8/refs/`，来源见其 SOURCES.md）：WEHI 景深、Nucleus 黑底玻璃、3B1B / Primer 一画一概念、Neuralink 产品白模、Our Planet II / Veritasium 片名 | 跨题材的审美锚 |

## v2 锚（Carl 2026-10-23 点选，SCALE_E1 v2 的 100 分锚）

文件在 `/workspace/e1work/p1/refs/`，从 `/workspace/e1work/calib/cand/` 和 `/workspace/e1work/calib/mock/` 拷入（长边压到 ≤1600 px；带裁切的按选图包 `docs/aesthetics/tools/spec_E1.py` 的裁切框）。来源 URL 见 `docs/aesthetics/picks/E1/SOURCES.md`。

| 文件 | 选中项 | 原件 | 学什么 |
|---|---|---|---|
| k1C_title_white_serif_machine_person.jpg | 1C | cand/yt_MiUHjLxm3V0_maxresdefault.jpg | 白衬线短句 + 整机全景 + 人做尺度 |
| k2A_studio_white_product_lighting.jpg | 2A | cand/imec_highna_scanner.jpg | 白色产品棚拍的布光、留白、地面反射（**不仿外观**） |
| k2B_cg_cutaway_violet_path_modules.jpg | 2B | cand/yt_B2482h_TNwg_maxresdefault.jpg 裁 [0.36,0,1,0.6] | 去机壳剖视：高密度模块、线缆、紫光贯穿（**极细致和还原**） |
| k3A_cg_metal_source_chamber_plasma.jpg | 3A | cand/yt_IattxYrc9Go_maxres1.jpg | 写实金属光源腔 + 中心紫色等离子辉光 |
| k3D_mock_plasma_illustration_micro.png | 3D | mock/e1_plasma.png（MOCK-UP） | 机理放大框的插画语言（只看方向） |
| k4A_cg_mirror_mounts_violet_bounce.jpg | 4A | cand/yt_B2482h_TNwg_maxres1.jpg（= rE01） | 紫光在金属镜座间多次折返 |
| k4D_tem_mosi_multilayer_40pairs.png | 4D | cand/nist/i-000.png | Mo/Si 多层膜 TEM 截面，能数出约 40 对 |
| k5A_real_pellicle_gloved_hands.jpg | 5A | cand/imec_cnt_pellicle.jpg | 手套托着的超薄真实保护膜 |
| k6C_cg_chip_interconnect_layers.jpg | 6C | cand/yt_dX9CGRZwD-w_maxres1.jpg 裁 [0,0,0.5,1] | 芯片里一层层立体金属连线 |
| k6D_mock_wafer_circular_magnifier.png | 6D | mock/e1_wafer.png（MOCK-UP） | 晶圆 + 圆形放大框（只看方向） |
| k7A_3d_objects_same_space_scale.jpg | 7A | cand/yt__Pqfjer8-O4_maxres3.jpg | 3D 实物同屏做尺度 |
| k8A_night_freighter_nose_loading.jpg | 8A | cand/cm_747_cargolux_tpe.jpg | 夜间货机开鼻装货、钠灯（成片无航司标） |
| k8C_cold_white_cleanroom_tools.jpg | 8C | cand/imec_cleanroom_300mm.jpg | 冷白光洁净室、设备排开 |
| k9A_bunnysuit_pair_walking.jpg | 9A | cand/yt_NHSR6AHNiDs_maxres1.jpg | 洁净服两人行走中景（成片只做剪影） |
| k9B_person_beside_machine_scale.jpg | 9B | cand/yt_1JkzrR-hznE_maxresdefault.jpg 裁 [0.5,0.17,1,1] | 人站机器旁做尺度（成片只做剪影） |

## v2 反例（扣分方向）

| 文件 | 落选项 | 为什么是反例 |
|---|---|---|
| x5C_flat_mask_section_diagram.jpg | 5C | 扁平剖面 + 文字标注（H14） |
| x7C_minimal_dark_lines_3b1b.jpg | 7C | 纯深底极简线条和数字（H14） |
| x2D_mock_dark_hall_silhouette.png | 2D | 只有剪影没有结构 |
| x3B_minimal_black_droplet_trail.jpg | 3B | 纯黑底无腔体 |
| R1 的 B5_01 / C_03 / B7_06 / B8_03 帧（`/workspace/e1work/p1/round1/`） | — | 简陋几何剖视、白模（H13 / H4） |
