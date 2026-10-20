# E2《光遗传学》

状态：**P1/P2 骨架**（2026-10-20 Carl 批准期号 E2、建目录、走远程 PR）。还没到检查点①（剧本定稿 + 分镜总览）。

目录名沿用 E1：`episodes/E<n>-<短名>/`。E1 是 `episodes/E1-euv-lithography/`，这一期是 `episodes/E2-optogenetics/`。

## 定位

| 项 | 锁定值 |
|---|---|
| 片名 | 《光遗传学》 |
| 目标时长 | 12–15 分钟（WORKFLOW 允许 ±1.5 分钟） |
| 镜数 | 约 120–150（E1 约 20 分钟 / 196 镜，本片更短） |
| 样片段 | 计划先做 A0；尚未开拍 |
| 语气 | 高质量长片，把机制和边界讲清楚。不做 2–3 分钟快餐解说，片内不预告下一期 |

## 钩子（已锁定）

Crick 1979「理想信号是光」→ 2026 诺奖。

冷开场只给这句预言和诺奖之间的空档，不解释通道蛋白。衣藻开门是第二幕的视觉高潮，不是片头主钩。计划里说的「47 年」只是这两个年份相减，事实表没有单独成条；F1、F3 一手核对之前，定稿旁白不要把「47」说成已核实数字。

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

`research/facts.yaml` 只种了制作计划里的 15 条。每条有 claim、等级、来源类型、`status: needs_verification`。**没有 URL、DOI、页码或自造数字。** 一手核对前不得改成 `verified`。

等级沿用 A/B/C，但本片的 A 不是 E1 那套厂商名单：A = 诺奖官方新闻稿 / 摘要 / 科学背景，以及监管或公司的正式公告；B = 同行评审论文、专利、学会材料。

大纲里有、事实表还没有的节拍（定稿前要么补一条并核一手，要么不要说成已核实）：

- A2：fMRI 热图只能看见哪里亮了
- A4：早期多组件（计划举例 chARGe）为什么不够
- B2：衣藻里感光器与通道是同一蛋白
- B8：工具箱里具体的开 / 关 / 红移蛋白
- C6：穿透、发热、非生理激活、疗效有限（只有方向，没有数字）

事实表有、大纲不单列的：F10 觉醒（Adamantidis 2007）。要用再写进旁白，并先核实。

## 画面语言（尚未分镜）

对齐 WORKFLOW §6.1 七种核心：真实渲染 / xray / blueprint / energy / infographic / clay / sem。计划里还用了 HUD、type、documentary，标成「WORKFLOW 表外扩展」。同一种语言连续不超过 3 镜；每段至少 3 种；真做分镜时每镜写 `style_why`。

## 本目录

```
episodes/E2-optogenetics/
├── README.md                  本简报
├── research/facts.yaml        P1 事实种子（全部待一手核实）
├── research/visual/TOPICS.md  视觉调研题目，报告还没写
├── script/script_zh.md        P2 分 beat 大纲，不是定稿旁白
├── script/pronunciation.yaml  空词表，读音未猜
├── storyboard/parts/          空（P3）
├── sound/                     空（P9）
├── subs/                      空（P5）
├── blender/scripts/           空（P7）
├── blender/shots/             空（P7）
└── mograph/                   空（P7）
```

`audio/` 和 `renders/` 按仓库惯例不入库，也还没有产出。

校验大纲：

```bash
DREAMFORGE_EPISODE=E2-optogenetics python3 shared/tools/lint_script.py
```

lint 打出来的分钟数是大纲句子的估算，不是成片目标时长。
