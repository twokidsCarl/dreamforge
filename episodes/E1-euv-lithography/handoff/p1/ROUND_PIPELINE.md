# E1 P1 一轮加速流水线（Carl 2026-10-23 批准）

目标：把一轮墙钟从 ~70–90 分钟压到 **~50 分钟**（不保证）。  
GPU 已够快（4–10 分）；加速点在 **改结构压缩、流水线重叠、审分并行、收尾钉死**。  
门槛不变：隔离独立审按 `SCALE_E1.md` v2，**均分 ≥92 且单张 ≥88**。过线才开 P2。

相关：`WORK_ORDER.md`（每轮工单 + 进度）、`BRIEF.md`、`../SCALE_E1.md`。

---

## 阶段一览（墙钟目标）

| 阶段 | 目标时长 | 可否与他阶段重叠 | 备注 |
|---|---|---|---|
| A 改结构 | 20–30 分 | 可与上轮「审分尾声」重叠起草 | 大头；扩共用库，少整库重写 |
| B 冒烟减量 | 3–6 分 | 串在 A 后、开卡前 | **禁止 24 镜全冒烟** |
| C GPU 渲 + 拉回 | 4–10 分 | 可叠着改「不碰帧」的脚本 / 起草 R(n+1) | 渲完必 Terminate |
| D 合成 strip / 接触表 | 2–4 分 | 与 D→E 交接紧挨 | 出 `/workspace/e1work/p1/roundN/` |
| E 审分并行（2–3 路） | 8–12 分 | 帧一拉回立刻起；同时可起草 R(n+1) | 全量盲审，合并一篇 REVIEW |
| F 收尾钉死 | 3–6 分 | 不与下一轮 GPU 重叠到「审未完」 | 时间轴 → merge → 推 Carl → 开下一轮 |

预期合计 ~50 分；若改结构项特别重或审稿漂移复盘，允许回到 60–70 分，但不得退回串行空等。

---

## A. 改结构（压缩）

硬规则：
- **只做**上轮独立审「下一轮最值钱的改法」点名的结构性项；工单表格只列这些。
- **优先扩**共用可命名零件库（`hero_kit_rN.py` / `build_cutaway_r2.py`），一次做厚、多镜复用；**少整库重写**。
- **禁**：单镜微雕、标签 / HUD polish、glow / 噪点修补当本轮主活。
- **禁**：为「好看一点」改未点名的镜头。
- 验收语言：零件要过「评审能用一个词叫出它吗？」；种类数是验收项。

输出：代码改动 + 本轮 `WORK_ORDER`「第 N 轮工单」段落已写好。

---

## B. 冒烟减量（开卡前硬门槛）

**只冒烟以下集合的并集**（去重后通常 3–8 镜，不是 24）：

1. 上轮**最低分镜**
2. **本轮改过的镜**（结构性触及的 shot 脚本 / 共用资产被这些镜引用）
3. 本轮 `WORK_ORDER` 写明的**烟测门槛镜**

每镜：本地低清 1 条 strip 或 1–3 静帧，对照门槛 checklist。  
**不达标 → 不开 GPU。**  
**禁止**：开卡前对全 24 镜跑冒烟「以防万一」。

---

## C. GPU 渲

```text
handoff/tools/pod_styleframes.py p1/roundN_jobs.txt --cap-usd 2
```

- 1×A40；过线前低清样张（960×540 / 既定 spp）。
- 拉回后：**立刻 Terminate**，确认**本会话 E1 pods = `[]`**（不要误杀其他 episode 的卡）。
- 2D / mograph 在 box CPU 跑，不占卡。
- **审分未出完前，不要租下一轮 GPU。**

---

## D. 合成

- `compose_roundN.py` → `/workspace/e1work/p1/roundN/`：strip、`contact_roundN.jpg`、`calib_vs_roundN_comparison.jpg`。
- 接触表等大图可不入库；分数 / REVIEW / 时间轴入库。

---

## E. 审分并行（2–3 路）

### 原则
- **全量 24 镜盲审**（防尺度漂移）。**禁止**只审改过的镜。
- 隔离目录只放：`SCALE_E1.md`、`BRIEF.md`、`FACTS_CHECKLIST.md`、`refs/`、`frames/`。不给改动说明、不给上轮分数。
- 经 Carl 的 Claude Code（`run-claude-job.sh`，keys 模式）跑。

### 怎么开 2–3 路
按镜头分组（示例，可按当轮风险微调，但每路镜数大致均分）：

| 路 | 建议镜头组 |
|---|---|
| R1 | 光源 / 锡滴：`A0_01` `A0_02` `A0_03` `B1_08` `B1_10` `B1_15` `B1_18` `B1_22` `B2_08` |
| R2 | 2B 剖视：`A0_10` `B3_02` `B5_01` `B7_06` `B8_03` `C_03` |
| R3 | 其余：`A0_06` `A2_03` `A2_08` `B4_07` `B4_10` `B6_12` `B8_17` `B9_05` `D_07` |

每路独立工作目录（例：`/workspace/e1work/p1/review_rN/p{1,2,3}/`），各写：
- `scores_partial.json`（只含本路镜头）
- `REVIEW_partial.md`（本路逐镜意见）

**主进程**等 2–3 路都退出后：
1. 合并 `scores_partial.json` → `scores.json` / 入库 `scores_roundN.json`
2. 拼一篇完整 `REVIEW_roundN_independent.md`（含分数表 + 汇总 +「下一轮最值钱的改法」）
3. 写审稿 `STATUS.txt`（`roundN avg=… min=… <shot> pass=yes/no`）

叫醒方式：等子进程退出 / `STATUS` 或 `scores_partial.json` **文件出现**；**禁止** `sleep` 轮询空转。

---

## F. 收尾钉死（同一回合）

顺序锁死，中间不插入空等：

1. REVIEW + scores 已落盘  
2. 更新 `score_timeline.png`（**仅 SCALE_v2**，`plot_score_timeline.py --ep E1`）  
3. 记账 `E1_SPEND.md`；需要的 handoff 文件进 git  
4. feature 分支 → 就绪非 draft PR → **Vivian squash-merge 自合**，只报「已合并 + link」（不要 force-push main）  
5. **立刻推 Carl：只要 `score_timeline.png`**（不要塞接触表 / 长文）  
6. 若 `pass=no`：**同回合**开下一轮 job（写好 `r{N+1}job/PROMPT.md` + `run_e1_r{N+1}.sh` 并 launch）；不要等 Carl 问「下一轮呢」  
7. 若 `pass=yes`：停在 P1 过线，准备 P2；丢掉预先起草的 R(n+1) 结构草稿  

`STATUS.txt` / `PUBLISHED.txt`（job 目录）只在 PR 已合并、时间轴已更新后写。

---

## 流水线重叠（墙钟收益最大）

```text
时间 →
[改结构 A]----[冒烟 B]-[GPU C]--[合成 D]
                         \--[审分并行 E]--------[收尾 F]
                         \--[起草 R(n+1) 草稿（内存/草稿目录）]
                                              \--[未过线 → 落地改 R(n+1) 代码 = 下一轮 A]
```

硬门槛：
- **帧一拉回 → 立刻起独立审**（不要先去做无关整理）。
- 审分进行中可起草 R(n+1) 结构草稿；**仅当本轮未过线才把草稿落成代码**；若本轮过线 → **丢弃草稿**。
- **审分未出完前不要租下一轮 GPU**（避免过线后白烧卡，也避免两轮帧搅在一起）。

---

## 禁止事项（汇总）

| 禁止 | 原因 |
|---|---|
| 24 镜全冒烟再开卡 | 吃掉 10–20 分墙钟，收益低 |
| 只审改过的镜 | 尺度漂移无法校正 |
| 单镜微雕 / 标签 polish 当主活 | Carl HARD：结构性 only |
| 审分未完就租下一轮 GPU | 过线风险 + 账本混乱 |
| sleep 轮询等分 / 空等 Carl | NO-IDLE-WAIT |
| 推 Carl 塞接触表或长 REVIEW | 只要 score_timeline.png |
| 渲完不 Terminate | 烧钱；确认 E1 pods=[] |
| force-push main / 提交 secrets | 硬禁 |
| 两份 WORK_ORDER 打架 | 以 repo `handoff/p1/WORK_ORDER.md` 为准；`e1work/p1/` 不另存副本 |

---

## 成功标准（每一轮）

- 冒烟集合 ⊆ {最低分 ∪ 改过 ∪ 工单门槛}，有记录。
- pods：本会话 E1 渲完后 `[]`。
- 独立审全量 24 镜，2–3 路合并为一篇 REVIEW + 一份 scores。
- `score_timeline.png` 含本轮，SCALE_v2 only。
- PR 已 squash-merge；Carl 已收到时间轴图。
- 未过线则下一轮 job 已在同回合 launch（或至少 PROMPT 就绪且回报写明一键开）。
