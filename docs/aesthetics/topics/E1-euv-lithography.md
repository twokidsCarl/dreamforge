# 题材：E1《一台光刻机里发生了什么》（EUV 光刻机）

**状态：LOCKED (2026-10-23)**。Carl 已对选图包 v1（`../picks/E1/`，9 张表）给出正式点选；Vivian 同日拍板跨元素整片风格。本文件是 E1 画面语言的最终依据，`episodes/E1-euv-lithography/handoff/SCALE_E1.md` v2 的锚和反例都从这里来。

## 1. Carl 的点选（2026-10-23，北京时间 08:25 前收到）

一行答案：**`1C 2A+B 3A+D 4A+D 5A 6C+D 7A 8A+C 9A+B`**

原话（逐字保留）：「2 A和B（B做极细致和还原）」。Carl 特别强调 2B 要做得极细致、高还原。其余各题只给了字母，没有附加说明。

| # | 元素 | 选中 | 选中项是什么（锚点文件见 §4） | 落选 |
|---|---|---|---|---|
| 01 | 片头标题卡 | **C** | 同题材纪录片海报式：白色衬线短句 + 整机全景 + 人站在机器旁做尺度 | A 宽字距细体压发光主体；B 主体自发光 + 大衬线；D 粗无衬线压等离子强光 |
| 02 | 整机 / 系统外观 | **A + B** | A：白色产品棚拍的布光与留白（**只学光和留白，不仿 ASML 外观**）；B：去掉机壳的 CG 剖视，紫色光路贯穿各模块（**极细致、高还原**） | C 洁净室组装实拍；D 无品牌暗厅剪影（mock-up） |
| 03 | 锡滴 + 激光 → 等离子体 | **A + D** | A：写实金属腔体 + 中心紫色等离子辉光；D：微观机理段可用 E2 科学插画风格 | B 极简黑底拖尾；C 科研实拍 + 光谱 |
| 04 | 多层膜反射镜与光路 | **A + D** | A：CG 机内剖视，紫光在金属镜座间折返；D：镜面内部纳米层用实拍感电镜截面（能数出约 40 对 Mo/Si） | B 工程师围镜实拍；C 手套托镜产品照 |
| 05 | 掩模 / 保护膜 | **A** | 手套托着的超薄真实保护膜（pellicle），薄、透、真实质感 | B CG 掩模 + 放大框；**C 扁平剖面示意 + 文字标注（对照项，明确不要）** |
| 06 | 晶圆 / 芯片 / 纳米图形 | **C + D** | C：CG 剖视芯片里一层层立体金属连线；D：E2 插画风格 + 圆形放大框看微观结构 | A 晶圆衍射彩光实拍；B 灰阶 SEM 线条 |
| 07 | 尺度对比与数据信息图 | **A** | 3D 实物同屏做尺度（地球、月球、高尔夫球、芯片放在同一 3D 空间） | B 半透明底条数字叠 3D；**C 纯深底极简线条（对照项，明确不要）** |
| 08 | 纪实：货机、车队、洁净室 | **A + C** | A：夜间货机开鼻装货，钠灯，实拍照片质感；C：冷白光洁净室实拍感，设备排开 | B 官方纪实航拍；D 插画家族夜间货机 |
| 09 | 人物（只用剪影） | **A + B** | A：穿洁净服（兔子服）两人在洁净室行走的中景；B：人站在机器旁当尺度参照 | C 近景手和屏幕；D 逆光剪影群像 + 顶灯（mock-up） |

## 2. 跨元素整片风格裁定（Vivian 拍板，2026-10-23）

附加问题（E1 走插画家族、CG 写实，还是按问题换语言）的答案：

> **双层统一视觉系统**：Macro 工业级高精度写实 / 剖视 + Micro 科学插画 / 电镜截面放大框。

| 层 | 管哪些画面 | 画法 | 锚 |
|---|---|---|---|
| **Macro 宏观与机器层** | 整机、剖视光路、光源腔、镜座、pellicle、3D 实物尺度对比、夜间货机与冷白光洁净室、洁净服人物与尺度剪影 | Branch Education / 工业产品级高精度 CG + 实拍级材质与灯光。**2B 机内剖视必须做极细致、高还原的机械和光学结构，告别简陋几何体和玩具白模。**白色棚拍（2A）只借布光、留白和轮廓光 | 1C、2A、2B、3A、4A、5A、6C、7A、8A、8C、9A、9B |
| **Micro 微观与原子 / 纳米机理层** | 等离子体微观跃迁、40 对 Mo/Si 纳米多层膜截面、10 nm 晶圆线条与多层互连放大 | 圆形 / 局部放大框里的科学插画（3D、6D），或高真实感 SEM / TEM 电镜截面（4D）；**嵌入**宏观 CG 画面，不单独铺满整片 | 3D、4D、6D |

两层共用同一套色板和光比：

| 色 | 值 | 只给 |
|---|---|---|
| EUV 紫 | `#8A5CFF` | EUV 光（叙事光），片中说明一次「紫色是约定」 |
| 激光橙 | `#FF8A3D` | CO₂ 激光 |
| 计量青 | `#3FD6E0` | 测量、对准、HUD、尺寸线 |
| 底色 | `#070B14`–`#0E1424` | 暗场镜头；棚拍镜头用中灰 / 冷白棚 |
| 线稿白 | `#E8ECF4` | 标注与线稿 |

光比：主体亮部与背景 ≥ 8:1，轮廓光把主体从底里分出来。

这个裁定**替代** Carl 决定 4（「按问题选画面语言，统一色板和光比」）里的「10 种画面语言轮换」：E1 不再按 documentary / hud / type / infographic / energy / blueprint / sem / xray / clay / photoreal 十种语言换着画，而是归并成上面两层。原 10 种语言里：
- photoreal、xray（改成写实剖视）、clay（升级成 2A 棚拍级产品材质，不再是白模）、documentary → Macro 层；
- sem、energy 里的原子 / 光子机理 → Micro 层，以放大框或电镜截面出现；
- type、infographic、hud、blueprint → 只作为叠在 Macro / Micro 画面上的标注层（细引线、深色底条、计量青尺寸线），不再做纯深底整屏（7C 是反例）。

## 3. 已经定下的（沿用）
- Carl 的四项决定（2026-10-23 01:42，`episodes/E1-euv-lithography/handoff/E1_PLAN.md` 第 0 节）：预算总额 $60、单日 $25；片尾改 eigenlens.ai 加号召；纪实镜头可用 image2 + Wan 背景板；统一色板和光比（第 4 条的画面语言部分由 §2 的双层系统具体化）。
- 红线：不仿 ASML 整机外观和标志；不出现 ASML / TRUMPF / ZEISS / 航司 / 工厂标志；人物只用剪影或背影，无写实人脸；网页请求里不带个人信息。
- 通用规则沿用 `../CHANNEL_PREFERENCES.md` 第 5 节。

## 4. 锚点文件（`/workspace/e1work/p1/refs/`，不入库，登记见 `episodes/E1-euv-lithography/handoff/p1/REFS.md`）

| 选中 | 文件 | 原件 |
|---|---|---|
| 1C | `k1C_title_white_serif_machine_person.jpg` | `calib/cand/yt_MiUHjLxm3V0_maxresdefault.jpg`（Veritasium） |
| 2A | `k2A_studio_white_product_lighting.jpg` | `calib/cand/imec_highna_scanner.jpg`（ASML via imec） |
| 2B | `k2B_cg_cutaway_violet_path_modules.jpg` | `calib/cand/yt_B2482h_TNwg_maxresdefault.jpg` 裁右上（Branch × ASML） |
| 3A | `k3A_cg_metal_source_chamber_plasma.jpg` | `calib/cand/yt_IattxYrc9Go_maxres1.jpg`（ASML） |
| 3D | `k3D_mock_plasma_illustration_micro.png` | `calib/mock/e1_plasma.png`（MOCK-UP，只看方向） |
| 4A | `k4A_cg_mirror_mounts_violet_bounce.jpg` | `calib/cand/yt_B2482h_TNwg_maxres1.jpg`（= rE01） |
| 4D | `k4D_tem_mosi_multilayer_40pairs.png` | `calib/cand/nist/i-000.png`（NIST TEM） |
| 5A | `k5A_real_pellicle_gloved_hands.jpg` | `calib/cand/imec_cnt_pellicle.jpg`（imec） |
| 6C | `k6C_cg_chip_interconnect_layers.jpg` | `calib/cand/yt_dX9CGRZwD-w_maxres1.jpg` 裁左（Branch） |
| 6D | `k6D_mock_wafer_circular_magnifier.png` | `calib/mock/e1_wafer.png`（MOCK-UP，只看方向） |
| 7A | `k7A_3d_objects_same_space_scale.jpg` | `calib/cand/yt__Pqfjer8-O4_maxres3.jpg`（Branch） |
| 8A | `k8A_night_freighter_nose_loading.jpg` | `calib/cand/cm_747_cargolux_tpe.jpg`（Wikimedia；成片不得出现航司标） |
| 8C | `k8C_cold_white_cleanroom_tools.jpg` | `calib/cand/imec_cleanroom_300mm.jpg`（imec） |
| 9A | `k9A_bunnysuit_pair_walking.jpg` | `calib/cand/yt_NHSR6AHNiDs_maxres1.jpg`（TRUMPF；成片只做剪影） |
| 9B | `k9B_person_beside_machine_scale.jpg` | `calib/cand/yt_1JkzrR-hznE_maxresdefault.jpg` 裁右（CNBC；成片只做剪影） |

反例文件：`x5C_flat_mask_section_diagram.jpg`（5C 扁平剖面）、`x7C_minimal_dark_lines_3b1b.jpg`（7C 纯深底极简线条）、`x2D_mock_dark_hall_silhouette.png`（2D 暗厅剪影，落选）、`x3B_minimal_black_droplet_trail.jpg`（3B 极简黑底拖尾，落选）。

## 5. 落到 E1 镜头

| 镜头 | 用哪条 |
|---|---|
| 片名卡（A0_10 / 送审帧 `A0_TITLE`） | 1C：白衬线短句 + 整机全景（2A 棚光，不仿 ASML 外观）+ 尺度人影（9B 剪影） |
| A0_01、B1_10、B1_15、B3_02 | 3A 写实金属腔体 + 紫色等离子辉光 + 橙色激光脉冲；机理放大框用 3D |
| B5_01、C_03、B3_02、B7_06、B8_03 | 2B + 4A：高密度机内剖视，紫色光束在镜座间多次折返；2A 棚拍级轮廓光 |
| B4_07 | 4D：约 40 对 Mo/Si 电镜截面质感，嵌在镜面放大框里 |
| B6_12 | 5A：真实薄膜反射 / 透光质感的 pellicle，膜与掩模间隙可见 |
| B9_05、B2_08、B1_18、A2_08 | Micro 层：放大框里的插画 / 电镜质感，叠在 Macro 画面上 |
| B4_10、A0_03 | 7A：3D 实物同屏做尺度（地球 / 月球 / 高尔夫球；货机与白色铝框运输箱） |
| A0_02、D_07 | 8A 夜间货机开鼻装货 + 钠灯；8C 冷白光洁净室；9A/9B 洁净服剪影与尺度人影 |
| A0_06、A2_03、B8_17 | 标注层叠在 3D 实物画面上（晶圆、地球、机器），不做纯深底整屏 |

## 6. 回答后的执行记录
- 2026-10-23：本文件、9 个元素文件、`CHANNEL_PREFERENCES.md` v1.1、`SCALE_E1.md` v2、`handoff/p1/REFS.md` 已更新（分支 `e1/aesthetic-locked`）。
- 接着：用 SCALE_E1 v2 重打 P1 第 1 轮（`handoff/p1/REVIEW_round1_recalibrated.md`），改写第 2 轮工单并执行；交付时出 `calib_vs_round2_comparison.jpg`（选中参考与第 2 轮新帧并排）推给 Carl。
