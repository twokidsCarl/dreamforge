# P1 风格帧工单（第 1 轮起；不设轮数上限，过线即止）

目标：G0 门槛——隔离独立审按 `handoff/SCALE_E1.md`，**均分 ≥92 且单张 ≥88**。过了才开 P2 全片样片。

## 镜头（23 个，覆盖 10 种画面语言 + 风险镜头）

| # | 镜头 | 语言 | 为什么选它 | 渲染 |
|---|---|---|---|---|
| 1 | A0_01 | photoreal | 冷开场锡滴，全片第一印象 | RunPod Cycles |
| 2 | A0_02 | documentary | 夜间货运机场，纪实氛围 | RunPod Cycles |
| 3 | A0_03 | 3D 信息图 | 货机白模（H4 风险）、全片最重场景 | RunPod Cycles |
| 4 | B1_10 | photoreal | 预脉冲拍扁锡滴：机理 + 质感 | RunPod Cycles |
| 5 | B1_15 | photoreal | 等离子体旁的素净镜面（复用 R2 上的现成帧） | 已有 |
| 6 | B3_02 | photoreal | 椭球收集镜（H8：不能有彩虹） | RunPod Cycles |
| 7 | B4_10 | photoreal | 地月高尔夫球比喻 | RunPod Cycles |
| 8 | B5_01 | xray | 透明整机 + 照明模块 | RunPod EEVEE |
| 9 | C_03 | xray | 一镜到底长镜头的中段 | RunPod EEVEE |
| 10 | B6_12 | xray | pellicle 13 nm 薄膜 | RunPod Cycles |
| 11 | B1_22 | blueprint | TRUMPF 激光放大链蓝图 | RunPod EEVEE |
| 12 | A2_08 | energy | 13.5 nm 波带（build_check 曾报视野空） | RunPod EEVEE |
| 13 | B9_05 | energy | 光子雨 | RunPod EEVEE |
| 14 | B2_08 | sem | 氢自由基 → 锡烷（化学式标注） | RunPod EEVEE |
| 15 | B4_07 | sem | 镜面一镜缩放到原子 | RunPod EEVEE |
| 16 | B8_03 | clay | 扫描：掩模台与晶圆台反向 8:1 | RunPod EEVEE |
| 17 | B7_06 | clay | High-NA 投影物镜白模 | RunPod EEVEE |
| 18 | B1_08 | hud | 锡滴锁定框 | RunPod Cycles |
| 19 | D_07 | documentary | 大厅剪影 + 世界地图 | RunPod EEVEE |
| 20 | A0_06 | infographic | 5100 家供应商地图 | box CPU（mograph） |
| 21 | A2_03 | type | CD = k₁·λ/NA 公式卡（下标） | box CPU |
| 22 | B1_18 | infographic | Sn⁸⁺–Sn¹⁴⁺ 谱线（上标） | box CPU |
| 23 | B8_17 | infographic | 188 个半场、185 片/小时 | box CPU |

每镜取镜头时长 25 % / 55 % / 85 % 三帧（帧号见 `round1_jobs*.txt`），960×540 sample；`handoff/tools/compose_styleframes.py` 叠片中标签和字幕后出 strip 和接触表。

## 每轮流程
1. 改代码（场景 / 风格 / mograph），只改上轮独立审点名的问题。
2. `handoff/tools/pod_styleframes.py p1/roundN_jobs.txt --cap-usd 3`：开 1 张 A40 → 渲 → 拉回 → **必定 Terminate** 并确认 `GET /pods` 为空；2D 在 box 上跑 `mograph.py`。
3. `compose_styleframes.py` 出 strip 和接触表（`/workspace/e1work/p1/roundN/`，不入库）。
4. 隔离独立审：审稿目录只放 `SCALE_E1.md`、`BRIEF.md`、`FACTS_CHECKLIST.md`、`refs/`、`frames/`，经 Carl 的 Claude Code（`run-claude-job.sh`，keys 模式）跑；不给改动说明。
5. 记分数到 `p1/scores_roundN.json`，更新 `p1/score_timeline.png`，记账 `E1_SPEND.md`，提交、推送、开 PR；推 Carl（附时间轴图）。

每轮预计 GPU 5–10 分钟（约 $0.05–0.10）。

## 进度

| 轮 | 时间（北京） | 独立审均分 | 最低 | 结论 | 花费 |
|---|---|---|---|---|---|
| R1 | 10-23 01:47–02:06 | 69.84 | 57.65（B9_05） | 未过；8 镜命中封顶（H1×6、H4×2、H5、H6×3） | GPU $0.04 |
| R1-recal | 10-23（SCALE_E1 v2 重打同一批帧） | 64.89 | 53.65（B9_05） | 换成 Carl 点选锚后下调 4.95；H13×5、H14×8、H15×2 | 0 |
| R2 | 10-23 09:34–09:50 | **79.33**（24 镜，含 A0_10） | 67.05（A2_08） | 未过（无一张 ≥88；最高 B9_05 85.4）；H13×5（B3_02 B5_01 C_03 B8_03 B7_06）、H14×2（A2_08 A2_03）、H2×2（A0_02 B8_03）；C_03 掩模入射角画成 35–40° 与「约 6°」标注不符。第 3 轮改法见 `REVIEW_round2_independent.md` 末节 | GPU $0.04 + image2 $0.11 |

## 第 2 轮工单（2026-10-23 改写：按 SCALE_E1 v2 + Carl 点选 `1C 2A+B 3A+D 4A+D 5A 6C+D 7A 8A+C 9A+B`）

依据：`../SCALE_E1.md` v2、`REVIEW_round1_recalibrated.md`（R1-recal 均分 **64.89**，最低 B9_05 53.65）、`docs/aesthetics/topics/E1-euv-lithography.md`（LOCKED）。
原第 2 轮候选清单（R1 独立审的改法）并入下表；**画法一律改走双层统一视觉系统**：Macro = 工业级高精度 CG 剖视 / 实拍质感；Micro = 圆形放大框插画或电镜截面；数字和公式只做叠在画面上的标注层，不再做纯深底整屏（7C 反例）。

### 改法清单（按 R1-recal 最违背 Carl 点选的顺序）

| 优先 | 镜头 | 点选 | 命中 | 第 2 轮改法 | 实现 |
|---|---|---|---|---|---|
| 1 | **C_03、B5_01、B3_02、B8_03、B7_06** | **2B（极细致和还原）**+ 4A + 2A | H13 ×5、H1、H5、H6 | 重建整台机器的去壳剖视：源腔（切开的真空腔、端口法兰、螺栓圈、视窗、泵、液滴发生器、收集镜 + 中心孔 + 冷却环）→ IF 颈部波纹管 → 照明模块（场分面镜阵列、光瞳分面镜阵列、聚光镜、hexapod 镜座）→ 掩模台（直线导轨、电机、卡盘、反射式掩模）→ 投影物镜箱（6 面镜 + 镜座 + 环形框架）→ 晶圆台（花岗岩基座、导轨）；箱体内部满填：加强筋、支撑笼、执行器 / 传感器块 + 状态灯、冷却管 + 管夹、彩色线束、金箔 MLI；#8A5CFF 光束带核心 + 光晕，只在镜面拐弯。B8_03 光路改反射式 + 狭缝 + 掩模台 8× / 晶圆台 1× 反向（修 H5）；B7_06 改 2A 棚拍产品转台 + 人影尺度 | `blender/scripts/kit_r2.py`、`build_cutaway_r2.py`、`shots/r2_cutaway.py`，标注 `mograph/r2_ov_cutaway.py` |
| 2 | **B9_05、B4_10、A0_03、A0_06、A2_03、B1_18、B8_17、B1_22、A2_08** | 7A、6C+D | H14 ×8、H1、H4 | 全部换成「3D 实物 + 标注层」：B4_10 地球 / 月球 / 高尔夫球同屏；A0_06 3D 地球 + 供应商光点与连线；B8_17 真实晶圆 188 场 + 晶圆叠计数；B9_05 真实晶圆光刻胶 + 1 nm² 放大框计数到 ≈20；A2_03 公式叠在机内虚焦背景上；B1_18 谱线 HUD 叠在光源腔观察窗上 + ±1 % 反射窗口；B1_22 3D 放大链硬件 + 逐级变粗的橙色光束；A2_08 发光管波 + 193 nm 灰色对照；A0_03 image2 实拍感底板（货机 + 白色铝框箱 + 卡车）+ 计数链 | `shots/r2_misc.py`、`shots/r2_source.py`、`shots/r2_plates.py`；`mograph/r2_ov_misc.py`、`r2_ov_source.py`、`r2_ov_cutaway.py` |
| 3 | **A0_01、B1_10、B1_15、B1_08、B2_08** | 3A + 3D | 3B 家族、H1、H15 | 写实金属源腔（弧形腔壁、端口、法兰、视窗、喷嘴、收集镜背景），液态锡滴 → 两次橙色脉冲 → 液态薄饼 → 紫白等离子；B1_10 / A0_01 加 3D 风格机理放大框（25 μm → 300 μm；Sn⁸⁺–Sn¹⁴⁺ → 13.5 nm）；B1_15 等离子 vs 镜面二分构图；B1_08 多颗锡滴各自被青色准星锁定；B2_08 收集镜面 + 放大框里 H₂ → 2 H·、Sn + 4 H· → SnH₄↑ → 泵 | `shots/r2_source.py`、`mograph/r2_ov_source.py` |
| 4 | **B4_07、B6_12** | 4D、5A | H6、H15、H1 | B4_07 宏观镜面推近切边 → 放大框里约 40 对 Mo/Si 的灰阶 TEM 截面（可数层、比例尺）；B6_12 棚拍光下近乎透明的 pellicle（微雾、掠射高光、无彩虹）悬在反射式掩模上方，计量青尺寸线标间隙 | `shots/r2_misc.py`、`mograph/r2_ov_misc.py` |
| 5 | **A0_02、D_07** | 8A + 8C + 9A + 9B | H4、2D/9D 家族 | 按 Carl 决定 3 用 image2 生成实拍质感底板：A0_02 夜间开鼻货机 + 钠灯 + 白色铝框箱 + 背影地勤；D_07 冷白光洁净室 + 去壳整机 + 两名洁净服背影（无脸）；Blender 里做纪实推镜 + 手持微晃 + 灯光渐亮。**无航司 / 厂商标志、无写实人脸** | `shots/r2_plates.py`，底板 `renders/plates/`（不入库，提示词入库 `p1/plates/`） |
| 6 | **A0_10 片名卡（新增送审）** | 1C + 2A + 9B | H7 风险 | 白色棚拍里的整机剖视全景 + 两个洁净服剪影做尺度 + 白色衬线片名「一台光刻机里发生了什么」（「光刻机」下 EUV 紫下划线）+ 英文小字 | `shots/r2_cutaway.py` title、`mograph/r2_ov_cutaway.py` |
| 7 | 全片 | H5 / H8 / H10 / 排版 | — | B8_03 反射光路（上）；`shared/tools/richtext.py` 把 `·`（k₁ · λ、H·）改用拉丁字体排，不再是全角大间距；`shared/tools/edit_film.py` 字幕**一律**深色底条（2D 镜头也加）；所有标注字高 ≥ 3.5 % 画面高；标注避开右上角标签区和底部字幕区 | — |

### 渲染与交付
- 24 镜（R1 的 23 镜 + A0_10 片名卡）全部走 Blender Cycles：`p1/round2_jobs.txt`，`tools/pod_styleframes.py p1/round2_jobs.txt --cap-usd 2`（1×A40，GPU ≤ $2，渲完**立刻 Terminate** 并确认 `GET /pods = []`）。image2 底板 ≤ $6（本轮实际见 `E1_SPEND.md`）。
- 合成：`tools/compose_round2.py p1/round2_jobs.txt --out /workspace/e1work/p1/round2`（渲染 → 标注层 → 故事板标签 → 带底条字幕），出 strip、`contact_round2.jpg`；`tools/make_calib_comparison.py` 出 `calib_vs_round2_comparison.jpg`（Carl 选中参考与第 2 轮新帧并排）。
- 隔离独立审按 SCALE_E1 v2 → `REVIEW_round2_independent.md`、`scores_round2.json`；更新 `score_timeline.png`（R1 / R1-recal / R2）。
