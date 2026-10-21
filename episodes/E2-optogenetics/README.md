# E2《光遗传学》

状态：**检查点②已通过**（Carl 2026-10-21 对全片动态分镜说「继续吧」，按通过处理）。检查点①已于同日 01:07 UTC+8 通过（六条决定见下）。
**P7 建模与镜头已完成**（PR #17）：126 镜全部登记，67 个 3D 镜头 build 通过。下一步是 **P8 第一批试渲**：15 个镜头和命令见 [FIRST_BATCH.md](FIRST_BATCH.md)，等 Carl 按 [docs/RUNPOD.md](../../docs/RUNPOD.md) 开 GPU，Luna 协调和看片。

目录名是 `episodes/E<n>-<短名>/`。这一期是 `episodes/E2-optogenetics/`。

## 检查点①的决定（2026-10-21，制片人批准）

| # | 决定 | 落到哪里 |
|---|---|---|
| 1 | ~~钩子年份只用 1999~~ **已作废**：2026-10-21 Carl HARD 改为 1979 起头（F3b）→ 微生物平行线（F3c）→ 1999（F3）→ 2026（F1），见下「钩子」 | A0 旁白、A0_01a/01b/02a/02b/05a/92 已改；仍不说「47 年」，光不挂 1979 |
| 2 | **永不提** PDUFA「2027 上半年」 | 剧本和分镜里没有这个日期；F12 不收 |
| 3 | 保留 GS030 的 6/10 和 4/8，旁白必须写明出自公司公告 | 第三幕那句改成「……而且下面的数字出自公司公告。……公告还写，完成行为测试的八人里有四人……」 |
| 4 | F10 食欲素觉醒实验留在第一幕，作「相关变成因果」的例子 | 不变 |
| 5 | 光学人工耳蜗只留一句「仍是临床前」，不加 NCT05110183 可行性研究 | 第三幕那句改成「光学人工耳蜗，按 2023 年的综述，仍是临床前。」 |
| 6 | 按 126 镜分镜总览进入配音和渲染 | P4 起按 `storyboard/storyboard.yaml` |

## 检查点②（全片动态分镜，2026-10-21 通过）

通过的是 PR #13 / #14 的 animatic v2：A0 用成片样片段，其余镜头是定时分镜板 + 真实配音 + 临时配乐。从这里起按下面的约定做：

| 约定 | 内容 |
|---|---|
| 时长 | 以 `storyboard/storyboard.timed.yaml` 为准（真实配音定时）。场景代码用 `e2_shot.shot_frames(id)` 读时长，不在代码里写死秒数。旁白、retime 都已锁定，P7 不改 |
| 镜头 id | registry key = 分镜 id，126 镜一一对应（`shared/tools/build_check.py` 核对覆盖率） |
| 3D / 2D 分工 | `engine: eevee / cycles` 的镜头走 Blender（`blender/shots/*_scenes.py`）；`pillow / manim` 的镜头是 2D，registry 里写 `mograph: <模块>`，由 `mograph/*.py` 的 `@shot` 渲染。B_04a、B_06a、B_16b 分镜写 manim，但画的是膜、通道、卵母细胞，按硬约束改在 Blender 里用 blueprint 风格做（registry 注释写明） |
| 画面语言 | 每镜的 `style` 和 `style_why` 跟分镜一致，不连续四镜同风格 |
| 中文标注 | Blender 文字读不了 SC 字面。需要中文标注的 3D 镜头在 registry 写 `raw: true`，帧先写到 `<质量>_raw/`，由 mograph 里同 id 的后处理叠字（与 A0_04a 相同）。3D 镜头的 `overlays` 由 `edit_film.py` 统一贴在右上角 |
| 道具 | 小鼠、笼子、光纤、护目镜、实验台是参数化低细节示意（`build_props.py`，标 `TODO(prop)`）。以后可换 Tripo / Meshy，换之前在 `research/visual/assets.yaml` 记录 |
| 画面核查 | `research/visual/audit_C.yaml` 已写（两条 unsourced 待补，见文件头）；A、B、D 的 `audit_<段>.yaml` 还没写（P6）。场景代码文件头写了几何依据和简化点，进最终渲染前要补核查表 |

## 第一批 GPU 渲染之前

1. 第一批镜头已定：15 个，见 [FIRST_BATCH.md](FIRST_BATCH.md)（首 / 中 / 尾帧 preview 试渲，再渲 6 个短镜全长）。
2. Carl 开 RunPod，步骤见 [docs/RUNPOD.md](../../docs/RUNPOD.md)（预算 $15/天、$80/周；agent 不租 GPU）。
3. 渲染：`FRAMES=1,mid,last shared/tools/render_batch.sh preview <id>...`，环境变量见 FIRST_BATCH.md。
4. 不开 GPU 的检查：`DREAMFORGE_EPISODE=E2-optogenetics blender -b --factory-startup -P shared/tools/build_check.py`（逐镜 build + 套风格，不渲染）。

## 定位

| 项 | 锁定值 |
|---|---|
| 片名 | 《光遗传学》 |
| 目标时长 | 12–15 分钟（WORKFLOW 允许 ±1.5 分钟） |
| 镜数 | 约 120–150（E1 约 20 分钟 / 196 镜，本片更短） |
| 样片段 | A0（冷开场，约 45–60 秒） |
| 语气 | 高质量长片，把机制和边界讲清楚。不做 2–3 分钟快餐解说，片内不预告下一期 |

## 钩子（2026-10-21 Carl HARD 锁定，取代检查点①决定 1）

1979 Crick 的要求 → 同期微生物线索 → 1999 Crick 写下「光」→ 2026 诺奖。

1. **1979 起头，不藏**：《科学美国人》Thinking about the Brain，要有办法只动某一类神经元、其余大体不动（F3b）。只配这条要求，**不配光**。
2. **不干跳**：接下来的那些年，微生物那边的线索（F3c：1981 盐视紫红质的分离；1991–1996 衣藻微秒级光电流）。只作 HUD / 剪影和一句旁白，不开第二幕（不出现通道视紫红质、2002/2003）。
3. **讲座里猜过光，不写年份**；不编 1979–1999 之间的 Crick 讲座年份。
4. **1999** 才落定「理想的信号会是光」「相当牵强」（F3，诺奖科学背景括注 Crick 1999）。
5. **2026** 诺奖三人收束（F1）。

不说「47 年」，屏幕上不写年份差。衣藻开门仍是第二幕的视觉高潮。尾声 D 回到「相当牵强」只指 1999 那句，不暗示 1979 已点名光。

改动的镜头还没重新配音、定时和渲染，清单见 `/workspace/e2work/a0_1979_rewrite/REVIEW.md`；`storyboard.timed.yaml` 里这些镜头带 `retime_note`。

## 已锁定的决定

1. **第三幕** = 假记忆（Ramirez et al. 2013）+ 视觉临床路径。
2. **保留 C5b 一句**：光学人工耳蜗仍处临床前（还没有进入人体疗效试验）。不展开。
3. **不做下一期预告**。各期独立成片，片尾不承诺下一期题目。

## 红线

C 级（媒体二手）不进旁白，也不进屏幕标注。下面这些说法直接禁止，不要靠加限定词留下来：

- 治愈失明 / 治好盲人
- Boyden 拿了诺奖 / Boyden 是诺奖得主（可说他是 2005 年论文的第一作者，也可对照 Brain Prize 六人与诺奖三人）
- MCO-010 已上市（只可说申请被受理、尚未获批）
- 光遗传已能操控思想 / 洗脑
- 改写人类记忆

人物只做逆光剪影或抽象，不画写实人脸。动物实验风格化，不血腥。

## 事实表现在是什么

`research/facts.yaml` 已按一手材料改写，说明在 `research/verification.md`。A = 诺奖官方新闻稿 / 科学背景，以及公司正式公告；B = 同行评审论文。

仍不能当已核实用的：

- **F3b** 已核实为否定：1979 没有「理想信号是光」，只有「只动一类神经元」的要求；后者现在进 A0 旁白和屏幕（见「钩子」）。
- **PDUFA「约 2027 上半年」**：不在 Nanoscope 2026-09-09 公告正文里，已从 F12 删掉。
- fMRI、chARGe 这个名字、穿透深度和发热的具体数字：没有新建条目。早期方案「达不到毫秒级」只用 F16（诺奖科学背景）。泵和通道分开：F4 是 1971 的紫膜蛋白，F4b 是 1973 的细菌视紫红质质子泵。

F10（觉醒）已核实，定稿放在第一幕，当作「相关变成因果」的一个例子，不单开一条临床线。

## 分镜总览

`storyboard/parts/e2_overview.yaml` 合并为 `storyboard/storyboard.yaml`，总览页是 `storyboard/overview.html`。126 镜，板面时长约 16.3 分钟（口播约 14.3 分钟，其余是纯画面）。每镜有 `style` 和 `style_why`。同一种画面语言没有连续四镜。每段至少三种。

通道、膜、神经元、离子流、视网膜和耳蜗剖面标成参数化 Blender Python。小鼠、光纤、护目镜只作示意，这一步不调用 Tripo 或 Meshy，也不渲染。

## 本目录

```
episodes/E2-optogenetics/
├── README.md                  本简报
├── FIRST_BATCH.md             P8 第一批试渲：镜头、命令、输出、重试
├── research/facts.yaml        已核实的事实（含 F3b 1979 要求、F3c 微生物平行线）
├── research/verification.md   核实和降级说明
├── research/visual/TOPICS.md  视觉调研题目，报告还没写
├── script/script_zh.md        定稿旁白
├── script/pronunciation.yaml  空词表，读音未猜
├── storyboard/                分镜、定时分镜（storyboard.timed.yaml）、总览页
├── sound/                     临时配乐（P9 前）
├── subs/                      zh.srt
├── blender/scripts/           参数化 builder：膜、通道、神经元、紫膜、脑、视网膜、耳蜗、细胞、道具；e2_shot 共用件
├── blender/shots/             各段场景模块（a0 / a / b / b_cell / c / d）和 registry.yaml（126 镜）
└── mograph/                   2D 镜头（a0.py；b.py / c.py 暂时只有 raw 镜头叠字，共用件 raw_overlay.py；A–D 的 2D 镜头 P7 后续补）
```

`audio/` 和 `renders/` 按仓库惯例不入库，也还没有产出。

校验：

```bash
DREAMFORGE_EPISODE=E2-optogenetics python3 shared/tools/lint_script.py
DREAMFORGE_EPISODE=E2-optogenetics python3 shared/tools/storyboard_check.py
```

lint 打出来的分钟数是大纲句子的估算，不是成片目标时长。

## 旁白选条（P4）

段落模式每段 7 条，选用：A0 第 1 条、A 第 5 条、B 第 4 条、C 第 7 条、D 第 3 条（timing.json 里的 take 从 0 数，所以 B 是 `take: 3`）。

B 第 12 句（2006 年那句，六个作者名）在选用条里读坏了（「Mueske, Mueske」），这一句单独取 B 的第 1 条（`take: 0`），
其余句子不动。`audio/` 不入库，所以在这里记下：重建时在 `audio/vo/Andre/timing.json` 的 B 段加

```json
"line_takes": {"12": 0}
```

再跑 `vo_align.py`（加 `--reuse` 就不重跑语音识别）和 `retime.py`。这一句比原来长 0.59 秒，B 段随之后移。
