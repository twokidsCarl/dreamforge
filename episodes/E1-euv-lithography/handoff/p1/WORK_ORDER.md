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

## 第 2 轮（按 R1 独立审的改法顺序）
1. 补每镜的机理主体（解 H1/H6）：B9_05 1 nm² 计数到 ≈20、B4_10 地球 → 月球 → 高尔夫球、B1_15 镜面对照、B6_12 膜与间隙、C_03 四站可辨、B1_10/A0_01 橙色激光脉冲、B1_22 放大链光束和功率。
2. 全片统一提曝光、改背景：#0E1424 冷蓝渐变、轮廓光 + 菲涅尔边缘；C_03/B5_01 提 1.5–2 档。
3. 修 H5 和事实细节：B8_03 改成反射光路 + 狭缝 + 8:1；A0_03 换白色铝框箱；B9_05 标剂量；橙色只留给激光。
4. 替换 H4 道具：A0_03 改成真扁平信息图；A0_02 货机做金属漆面，打分仍不过就按决定 3 改用 image2 + Wan 背景板。
5. 排版：字幕加深色底条，小字 ≥3.5 % 画面高，B8_17 数字区上移；补片名卡送审（防 H7）。

> **2026-10-23 02:11 暂停第 2 轮**：Carl 要求先做 E1 审美校准（`docs/aesthetics/picks/E1/`）。第 2 轮的改法，要等他点选后、`SCALE_E1` 换了锚再定；上面这份第 2 轮清单只作为候选。没有起 pod。
