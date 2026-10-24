# EigenLens（主观知识）视频制作规范（所有 agent 必读）

> 适用：本仓库所有期的科普视频（当前 E1《一台光刻机里发生了什么》，约 20 分钟中文科普片；E2《光遗传学》以及之后每一期同样适用）。
> 本文是唯一权威的流程与规范，取代 2026-10-15 的初版方案（见 git 历史）。
> 检查点、认可条、未过线禁推、复盘沉淀（Carl t327 / t334 / t331 / t341，2026-10-24）对每一期持续有效，不是某一集的备注。条文在第 1.1、4.5 节与 [aesthetics/PROCESS_LOOP_v3.md](aesthetics/PROCESS_LOOP_v3.md)。
> 动手之前先读完第 1、2 节：这两节是制片人（用户）的硬性要求，违反任何一条都算返工。

## 品牌（2026-10-21 锁定）

公开品牌由 Carl 于 2026-10-21 锁定。GitHub 仓库和项目文件夹都是 `eigenlens`（原名 dreamforge）。正文里的英文名写 **EigenLens**。

| 项 | 锁定 |
|---|---|
| 中文主名 | 主观知识 |
| 英文主名 | EigenLens（正文用驼峰；仓库 slug 是 `eigenlens`） |
| 片头与片尾 | 每集片头 2–4 秒 sting，片尾 end card。不用 MetaHuman，也不用数字人主持人 |
| 标语含义 | 选主轴，看结构。主观是编辑上的选择；「主」取主轴，对应 eigen |
| 画面 | 暗色 HUD，冷青 / 冷紫，与 E2 A0 一致 |

标志已锁定（现行：程序重绘稿 03s6 琥珀金 → `brand/eigenlens_logo_locked/`；Carl 2026-10-22 确认不是草稿）。文件包括：`sting_open.mp4`（片头 3 秒）、`sting_end.mp4`（片尾 2 秒）、`endcard_16x9.png`、`lockup.svg` 等；路径由 `paths.BRAND` 给出。不要用其中的 `_superseded_rena_approx_2026-10-21/`（Carl 已否掉的近似重绘）。`shared/tools/edit_film.py` 默认开品牌：成片前接 `sting_open.mp4`，后接 `sting_end.mp4`（两段 sting 无声，补静音对齐，正片混音不动），此时不加 `--tail` 黑场；`--no-brand` 只出正片，独立短片再加 `--tail`。

**环境变量仍用旧前缀 `DREAMFORGE_`。** 这些名字由 `shared/tools/paths.py` 和调用它的脚本读取，这次只记录，不改代码。后续可以再迁前缀。仍在使用的名字：

- `DREAMFORGE_EPISODE`：当前期，默认 E1
- `DREAMFORGE_RENDER_DIR`：渲染根目录
- `DREAMFORGE_CYCLES_DEVICE`：Cycles 设备
- `DREAMFORGE_ASR_COMPUTE`：语音识别计算精度

分镜总览的 `kicker`（`episodes/*/storyboard/page.yaml`）、审查评论标记 `dreamforge-review`、素材请求的 User-Agent 仍是旧名，和上面的环境变量一起留到后续迁移。

---

## 1. 制片人的偏好（硬规则）

### 1.1 沟通与交付
- **一律用中文回复**，包括进度汇报。汇报要简短：做完了什么、发现了什么问题、下一步做什么。
- **自主迭代，只在检查点交付**：审美细节由 agent 自己看、自己改、自己剪，不要把小问题抛给用户一项项确认。用户问“进度”时如实说明，没完成就说没完成。
- **交付前必须按真实时长完整看一遍**（见第 5 节）。只抽几帧就交付不行，“预览”也必须按成片标准审。
- **Checkpoint 交付门（Carl HARD t327，2026-10-24；E2 与全频道）**：样段、低清全片、1080p，以及同类推给用户的检查点，顺序是**通看 → 列出具体修改 → 改 → 再通看 → 自己认可才交**。Vivian 用观众的眼睛看完整条（全片，或这条样段的全长），写下具体问题并改掉，再把完整条看一遍。只有这次再看之后 Vivian 自己认可，才可以交付。字幕条、冻帧、音画抽样、抽帧脚本、L0/L2 勾选等技术机器门只能拦截，不能单独授权推送。条文见 [aesthetics/PROCESS_LOOP_v3.md](aesthetics/PROCESS_LOOP_v3.md) §B，检查点见第 4.5 节，自审顺序见第 5 节。
- **未过线不得 Checkpoint（Carl HARD t334，2026-10-24）**：诚实再通看分低于认可线（E2 全片偏好约 95–98；不得低于已写明的再通看门槛）时，不得 scp、push、SendToUser 这条成片或它的可看地址。技术门高分（例如假 96）不是诚实分。中途刀留在内部。失败的自看不要报成「一版」，也不要附可看地址。先改到再通看认可，再交一次。t327 顺序不变：通看 → 列出具体修改 → 改 → 再通看 → 认可 → 才 Checkpoint。问进度可以回答还在改；不要把未过线的片子交出去。
- **技术四门 ≠ 认可条（Carl HARD t341/t342，2026-10-24；全频道）**：字幕条、冻帧、小鼠出场前静止、音画滞后，必要但永远不够。认可条 = Vivian 诚实通看全片 + F6 整片画面观感 + SHOT_REDESIGN 叙事 + 知识密度 + 科学/旁白同步 + 英雄质量。四门全过、L0/L2 勾选、表上分数，都不授权推送。
- **偏好条 vs 临时地板（Carl HARD t341/t342）**：知识片（E1、E2、之后每一期）诚实主观偏好约 **95–98**。这是频道目标。临时再推地板（例如失败的 74 之后 ≥90）只是恢复门，必须写明「恢复，不是目标」。Cut10：技术门 Vivian 96 作废，诚实 74，I01–I05 后 90，残留继续往 95–98。未达条不 scp、不挂公开 URL、不推给 Carl。
- **讨论后自主迭代（Carl HARD t331/t332，2026-10-24）**：改什么一旦说清，同一回合写进频道流程（本文件与 `docs/aesthetics/`）并接着改片，不等 Carl 再问。Checkpoint 是交给他看、给他调。下一档（例如 1080p）等他点头。当前这条已知残留继续改，不空等。
- **小鼠 HARD（Carl t341/t342）**：不得把同一段写实小鼠片段循环播放来垫时长。
- **用户能轻易挑出的错，就是 agent 的失职**。工程、结构、光学细节，用户都会逐项检验。实心字幕条、只靠 Ken Burns 的 PPT 式推镜、空笼、样片墙，在他看见之前先改掉。
- **审美叙事（Carl t295 / t341）**：不满的是画面怎么讲故事（缩放链、一镜一概念、多风格过渡、连续因果运动），不是片长，也不是抽空知识。F6 只评整片画面观感。
- **如实报告**：没验证过的不说“已解决”；子任务犯的错（例如泄露了用户信息）要主动告诉用户。

### 1.2 内容与真实性（详见第 2 节）
- 画面和旁白里的每个工程、结构、光学细节，都必须出自一手资料：ASML、ZEISS、TRUMPF、Intel 等厂商的官方资料，SPIE / EUVL Symposium / EUVL Workshop 的论文和报告，同行评审论文，专利。**不准凭印象或“看起来合理”来画。**
- **不说“据报道”“据估算”**：这是科普片，讲的是道理。只有媒体来源的数字（C 级），先去找一手来源（厂商年报、技术报告常常就有），找到就升级成 A/B 级照原文用；找不到就删掉，不要靠加限定词保留。
- 公开资料里没有的细节（例如精确尺寸），画面标“示意”，在核查表里写明依据。
- 不暗示不实的对应关系。例如 ZEISS 说的“比指尖略大的面积上有 1840 亿个元件”是泛指，不能配一颗具体芯片说“这颗芯片里有 1840 亿个”。

### 1.3 画面红线
- **人物只用逆光剪影**，不做写实人脸。
- **不仿制 ASML 整机外观**，不复制 ASML、航空公司、工厂的标志和涂装。机器内部结构照公开资料画，外壳保持通用造型。
- 审美标准从严：构图、光比、节奏、字幕可读性都按院线科普纪录片的标准看。

### 1.4 声音
- 全片旁白情绪统一，同一个音色（目前是 Qwen TTS 的 Andre），解说语气平稳，不夸张。
- 关键词必须听得清，用语音识别逐句验证（见 4.4、5.3）。

### 1.5 工程纪律
- **每完成一个阶段，在功能分支上 git commit，然后 push，向 `main` 开拉取请求**。GitHub Actions 的 `review` 检查必须通过（`shared/tools/review_pr.py`，说明见 [REVIEW.md](REVIEW.md)）。仓库已打开 squash 自动合并；`main` 受保护，必需检查就是 `review`，自动合并会等它通过。不要直接 push 到 `main`，不要用 `--admin` 绕过保护。提交信息写清楚改了什么，结尾加 `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`。
- **API key 只放在仓库根目录的 `.env`**（权限 600，已加入 gitignore），回复里不要复述 key。目前有 `DASHSCOPE_API_KEY`（Qwen TTS）、`ELEVENLABS_API_KEY`（配乐和音效）。Tripo 或 Meshy 的 key 也只放这里；`.env` 里没有该服务的 key，就不能调用。
- **网络请求里不放用户的邮箱或任何个人信息**。有些网站要求请求头里带联系方式（例如 SEC EDGAR），一律用占位地址。给调研子任务写提示词时要明确写上这一条。
- 付费工具只用已开通的：Qwen TTS（DashScope 国际版）、ElevenLabs Creator 档。免费图片和 HDRI 只用 Poly Haven（CC0），以及逐张核实为 CC0 的 Wikimedia Commons 图片。三维资产的分工见下一条，也见第 6.4 节。
- **三维资产**：核心科学结构必须用参数化 Blender Python 建模。包括蛋白和通道（如 ChR2）、神经元、膜、离子流、视网膜剖面，以及任何结构必须准确、或要做精确动画的对象。周边写实道具可以用 AI 三维生成（Tripo 或 Meshy），例如实验小鼠、光纤植入器件、护目镜、实验台和日常物件。调用前要同时满足：`.env` 里已经配好该服务的 key；在该期 `research/visual/assets.yaml` 记下工具、prompt 和日期；核对产出的许可和商用条款；在 Blender 里对齐全片风格并清掉多余几何。仍然不做写实真人面孔。Tripo 和 Meshy 哪一个为主还没定，对比做完之前不要写死。

---

## 2. 真实性规范

### 2.1 两张表
| 表 | 位置 | 管什么 |
|---|---|---|
| 事实库 | `episodes/<期>/research/facts.yaml` | 旁白和屏幕标注里的数字与论断。每条写明 claim、等级、来源 URL、注意事项 |
| 画面事实核查表 | `episodes/<期>/research/visual/audit_<段>.yaml` | 画面里出现的每个工程、结构、光学细节，每行一项 |

### 2.2 事实等级
- **A**：厂商官方（ASML / ZEISS / TRUMPF / Intel）。
- **B**：论文、专利、客户一手资料。
- **C**：媒体报道。**C 级不进旁白，也不进屏幕标注。**

### 2.3 画面核查表的状态
| 状态 | 含义 |
|---|---|
| `sourced` | 与引用的一手资料一致 |
| `wrong` | 与资料矛盾，必须改 |
| `unsourced` | 自己设定的或尚未查证，不得进入最终渲染 |
| `simplified` | 有意简化，写明与真实情况的差别，以及在哪一段修正 |
| `artistic` | 刻意的表现手法（慢动作、EUV 用紫色表示等），观众可能当真的地方要标“示意” |

**规则：一段的核查表里还有 `wrong` 或 `unsourced`，这段就不能出成片。** A0 以外发现的问题先记进 `research/visual/audit_backlog.yaml`，到对应段落再处理。

### 2.4 调研方法
1. 每个主题单独写一份调研报告，放在 `research/visual/<主题>.md`，每条都要附原文引语、URL、页码或幻灯片号和可信度，最后列出“未公开”的项目。
2. PDF 用 curl 下到 `renders/review/refs/`（不入库），用 `.venv/bin/python -I` 加 PyMuPDF 渲染成图片，**亲眼看图**后再建模，不只读文字。
3. 示意图上的几何关系要量出来写进代码注释，注明出自哪份资料、第几页。可参考 `build_machine.py` 文件头部的写法。
4. 互相矛盾的说法（例如“13 个”和“43 个集装箱”）都记下来，只用最权威的一种，并注明原因。
5. 调研可以拆成几路并行交给子任务（每路一个主题）。子任务的结论，主 agent 要亲自看原图核对后才能用。

### 2.5 已核实的关键结论（E1）
- **整机按 High-NA EXE:5000 画**，因为 A0 讲的就是它。
  - 模块分层：掩模层在顶，光学层居中（投影物镜和照明系统），晶圆层在底；光源是独立单元，放在扫描机旁边。出处：ASML van Schoot 2022 年报告第 34 页。
  - 光路：等离子体 → 收集镜 → 中间焦点 → 折转镜 → 场复眼镜 → 光瞳复眼镜 → 掩模。出处：ZEISS 2024 年报告第 13 页。
  - 投影物镜：按 6 面镜的设计示例画，M6 和 M5 中心开孔（中心遮拦约 20%）。出处：van Schoot 2021 年报告第 35 页，Heil 2015 年报告。
  - 掩模处主光线角 5.4°，变形缩放 4×/8×（8× 在扫描方向）。
  - **旁白里不说 EXE 的镜片总数**：公开文字资料没有给出。
- NXE 的光路（对照用）：出处是 ZEISS Conradi 2011 年报告第 5、20 页，主光线角 6°，投影物镜 6 面镜。
- 首台 High-NA 的时间线：2023 年 12 月首批模块**发货**，2024 年 1 月运抵俄勒冈，4 月完成安装。不能说“12 月交付”。
- 运输画面以英特尔官方视频为准：
  - 747 货机抬起机头，用剪叉式升降平台车装货；
  - “43 个集装箱”是带倒角顶的白色铝框运输箱；
  - “250 个板条箱”是航空货盘上罩着货网的箱子；
  - 卡车是平板挂车。
- 芯片照片只能用确实采用 EUV 工艺的芯片，目前用 AMD Zen 5 CCD（台积电 4 nm）。旁白要说“最精细的那几层”靠 EUV，不能说“每一个元件”都靠 EUV。

---

## 3. 制作流程（按阶段；每阶段在功能分支上提交并开 PR，见 1.5）

| 阶段 | 产出 | 工具 / 命令 | 进入下一阶段的条件 |
|---|---|---|---|
| P1 调研 | `research/facts.yaml`、`research/visual/*.md` | WebSearch、curl 加 PyMuPDF、调研子任务 | 每个论断都有 A/B 级来源 |
| P2 剧本 | `script/script_zh.md`（每句标事实编号〔F..〕）、`pronunciation.yaml` | `python3 shared/tools/lint_script.py` | lint 没有 ERROR；没有“据报道”之类的限定词；没有夸大 |
| P3 分镜 | `storyboard/parts/*.yaml` 合并成 `storyboard.yaml` | `python3 shared/tools/storyboard_check.py` | 每个镜头写明 style 和 style_why；时长不短于配音 |
| P4 配音 | `audio/vo/<音色>/` | 见 4.4 节 | 语音识别逐句核对通过 |
| P5 定时 | `storyboard.timed.yaml`、`subs/zh.srt` | `python3 shared/tools/retime.py` | 全片时长在目标 ±1.5 分钟内 |
| P6 画面核查 | `research/visual/audit_<段>.yaml` | 人工对照调研报告 | 没有 `wrong` 和 `unsourced` 的项 |
| P7 建模与镜头 | `blender/scripts/`、`blender/shots/`、`mograph/` | 见第 6.4、8 节 | 单帧试渲通过 |
| P8 渲染 | `renders/shots/<镜头>/<质量>/` | `shared/tools/render_batch.sh`、`mograph.py` | 帧数齐全，日志里没有报错 |
| P9 声音设计 | `sound/<段>.yaml`（配乐和音效） | `shared/tools/eleven.py` | 关键音效对准词的时间戳 |
| P10 剪辑 | `renders/edit/<段>_vN.mp4` | `python3 shared/tools/edit_film.py` | 第 5 节自审清单全部通过 |

**改剧本的顺序**：`script_zh.md` 和 `storyboard/parts/*.yaml` 里的旁白文字必须完全一致，两处都要改。改完依次跑：配音（tts）→ 对齐（vo_align）→ 定时（retime）→ 语音识别核对（asr_check）。配音任务在后台运行时**不要改剧本**：对齐脚本按文字哈希找配音缓存，文字一变就找不到对应的配音。

---

## 4. 检查点与交付

### 4.1 三个检查点（只在这里向用户交付）
1. **剧本定稿和分镜总览页**
2. **全片动态分镜**
3. **成片 v1**

### 4.2 样片标准段
铺开全片之前，先把一段（E1 用的是 A0，开头约 55 秒）按成片标准做完：1080p，带配乐、音效，画面事实全部核查通过。之后各段都按这个标准做。

### 4.3 交付物格式
- 视频：H.264，1080p，24 fps，-16 LUFS。
- 字幕：中文 SRT；英文字幕后续再做。
- 附一段简短说明：这一版改了什么、自审发现并解决了什么、还剩哪些问题。

### 4.4 配音规范
- 模型 `qwen3-tts-flash`，音色 Andre，**整段合成**（paragraph 模式，一段一个请求，保证语气统一）。
- 每段最多合成 10 版：`.venv/bin/python shared/tools/tts.py --voice Andre --attempts 10 --asr all`。
- 选版规则：
  - 语速、音高接近目标（全片统一 107 Hz）；
  - **同时看每一版中最难听清的那一句**：用语音识别逐句打分，取最低分。
  - **按拼音比，不按汉字比**：识别结果和剧本都转成不带声调的拼音再比较。“掩模/眼膜”“锡滴/溪滴”这类同音字算对；“激光→机关”“氢气→亲戚”这种韵母念错才扣分。
  - **术语检查**：`episodes/<期>/script/asr_terms.txt` 里列出全片术语（也作为识别器的上下文提示）。句子里出现的术语，拼音必须完整出现在识别结果里，否则每漏一个扣 0.05 分。
  - 识别结果缓存在每一版配音文件旁边的 `.asr.txt` 里，重跑只重新打分，不重新识别。
- 然后依次运行：`.venv/bin/python shared/tools/vo_align.py`（按识别结果切句）→ `retime.py` → `.venv/bin/python shared/tools/asr_check.py`。
- 分镜字段：`hold: 秒` 表示最后一个字说完后还留多少秒纯画面（例如片名停顿、爆闪后的停顿）；`lead: 秒` 表示镜头开始后第一个字从第几秒说起（冷开场先留一拍安静）。

### 4.5 Checkpoint 推送（样段 / 低清全片 / 1080p）

推给用户的样段、低清全片、1080p，以及同类成片或样片，都是 Checkpoint。交付前走第 1.1 节的交付门和第 5 节的再通看：**通看 → 改 → 再通看 → 认可才交**。

机器门（字幕条、冻帧、音画抽样、抽帧、响度、语音识别、L0/L2 勾选、自评分数）全过，也不等于可以推。未得到 Vivian 再通看之后的亲自认可，不交。第 4.1 节的三个产品检查点同样适用：到了该交的版本，仍要先走完这个顺序。

**未过线不得 Checkpoint（Carl HARD t334，2026-10-24）**：诚实再通看分低于认可线，这一刀就不是可以交的 Checkpoint。E2 全片偏好约 95–98，且不得低于已写明的再通看门槛。技术门高分不能顶替诚实分。低于认可线不得 scp、push、SendToUser 成片或可看地址；中途刀只留内部。先改到再通看认可，再交一次。

**t341/t342（全频道，与第 1.1 节同一条）**：字幕条 / 冻帧 / 小鼠前静止 / 音画滞后四门必要但不够。知识片偏好条是诚实主观约 95–98；≥90 一类数字只有在当刀写明「恢复地板」时才能再交一次，而且不是频道目标。Cut10 假 96 / 诚实 74 / 恢复 90 / 仍往 95–98 是范例。公开 URL 不许拿来包住未达条的片子。讨论清楚的改动同一回合写入流程并继续改（t331/t332）；1080p 等 Carl 点头；已知残留不空等。不满的是审美叙事方式，不是片长，也不是抽空知识。不得用同一段写实小鼠循环垫时长。实心字幕条、Ken Burns 式 PPT 推镜、空笼、样片墙，自己先抓。

---

## 5. 每轮自审清单（交付前必须全部做完）

**Checkpoint 顺序（不可跳）**：通看完整条 → 列出具体修改 → 改 → 再通看完整条 → Vivian 认可才交。第 2 项是第一次通看。第 1 项和第 3–7 项是机器门和清单门，过了也不代替第二次通看，也不代替认可。第 8 项才是改完之后的再通看和认可。只看过一遍就交付，算没做完自审。再通看的诚实分低于认可线（知识片偏好约 95–98；临时地板不是目标；不得低于已写明的再通看门槛；Carl HARD t334 / t341，2026-10-24）就继续内部改，不得 scp、push、SendToUser，也不得当成一版附上可看地址或公开 URL。字幕条、冻帧、小鼠前静止、音画滞后全过，仍不算认可。

1. **抽帧拼图**：每 0.5 秒抽一帧拼成接触表，逐张看。可疑的地方再抽原尺寸帧细看。
   - 命令示例：`ffmpeg -i X.mp4 -vf "fps=2,scale=480:-1,tile=4x4" sheet_%02d.png`
2. **按真实时长完整看一遍**，重点看节奏、转场、字幕和画面是否同步。
3. **用语音识别核对混音**：转写成片音轨，逐句对照剧本，任何一个词被配乐或音效盖住都要改。例如“等离子体”曾被爆炸音效盖住，后来改成旁白说完再炸开。
   - 工具：`.venv/bin/python shared/tools/review_asr.py <成片>`（faster-whisper large-v3-turbo）。
4. **响度**：`ffmpeg -af ebur128`，整体 -16 LUFS，真峰值不超过 -1.5 dBTP，冲击音要有动态起伏。
5. **字幕和标签可读**：浅色背景上也要看清（字幕带深色描边）；标签最多显示 5 秒；标签的来源行写机构名，不写事实编号。
6. **关键事件对准关键词**：用词级时间戳（`.venv/bin/python shared/tools/review_words.py <音频> <起点秒> <时长秒>`）确认标题、爆炸、转场落在对应的词上。
7. **画面事实核查表**：这一段所有项都是 `sourced`、`simplified` 或 `artistic`。
8. 第一次通看记下的具体问题必须改完，再按真实时长把**完整条**看第二遍。第二遍仍有观众一眼能挑出的问题，就继续改，不得交付。样段、低清全片、1080p 及同类检查点，只有 Vivian 在再通看之后自己认可，且诚实再通看分不低于认可线（Carl HARD t334），才可以交给用户。低于认可线的中途刀留在内部，不报成版本，不给可看地址。抽帧、识别、响度和核查表过了，也不代替这次再看和认可。字幕条、冻帧、小鼠前静止、音画滞后全过也不够（Carl HARD t341/t342）。知识片偏好约 95–98；临时地板不是目标。实心字幕条、Ken Burns 式 PPT 推镜、空笼、样片墙在第一次通看就改掉。同一段写实小鼠不得循环垫时长。

---

## 6. 设计系统

### 6.1 画面语言（每个镜头先问“它在回答什么问题”，再选语言）
| 回答的问题 | 语言 | 实现 |
|---|---|---|
| 它真实存在、长什么样 | 真实渲染 | Cycles，Poly Haven 的 HDRI 和 PBR 材质 |
| 内部怎么排布 | 透明剖视（xray） | `styles.apply_style("xray")` |
| 为什么这样设计 | 蓝图 | `blueprint` |
| 看不见的物理 | 能量图 | `energy` |
| 多大、多少、比什么强 | 平面信息图 | `mograph`（Pillow） |
| 零件怎么组装、怎么运动 | 白模 | `clay` |
| 纳米尺度长什么样 | 显微风格 | `sem` |

- 同一种语言最多连续用 3 个镜头（连续长镜头除外），每段至少用 3 种语言，风格切换要有理由。
- 强调色：EUV 紫、激光橙、计量青、线稿白。EUV 本身看不见，紫色是全片约定的表示方式，片中要说明一次。
- 建模时给物体标 role（structure / shell / emitter / env / rig / rays），由风格系统统一换材质。

### 6.2 字幕与标签
- 字幕：黑体，白字加深色描边，底部居中，字高约画面高度的 4.3%，每条不超过 18 个字。
- 标签：右上角，最多 3 行（主文字、副文字、来源机构），只在 3D 镜头上用，最多显示 5 秒。2D 信息图自己带文字，不另加标签。
- 2D 图要给底部字幕留出安全区。

### 6.3 镜头与节奏
- 冷开场先给一个不解释的“真东西”，并留一拍安静再开口。
- 重要的冲击（爆闪、炸开）放在旁白的空档里，不要压在词上。
- 片名镜头的片名要一直在画面内，后面留足停顿。

### 6.4 建模：什么必须手写，什么可以用生成
- **核心科学结构用参数化 Blender Python**，不用 Tripo 或 Meshy 的网格代替。范围：蛋白和通道（如 ChR2）、神经元、膜、离子流、视网膜剖面，以及任何结构必须准确、或要做精确动画的对象。
- **周边写实道具可以用 Tripo 或 Meshy**：实验小鼠、光纤植入器件、护目镜、实验台、日常物件。哪一个为主还没定，对比做完之前不要写死。
- 调用生成服务前，`.env` 里要有该服务的 key。没有 key 就不生成。
- 每件生成资产写入该期 `research/visual/assets.yaml`：工具、prompt、日期。核对许可和商用条款；进镜头前在 Blender 里对齐风格并清理几何。
- 人物仍只做逆光剪影。不用生成模型做写实人脸，也不做真人肖像。

---

## 7. 声音规范
- **配乐**：ElevenLabs Music（`eleven.music`，用 composition_plan 按段落写结构）。写进 `sound/<段>.yaml`，生成后要确认没有人声。
- **音效**：ElevenLabs Sound Effects（`eleven.sfx`），每条写明在哪个镜头、第几秒、多长、增益多少。结果按请求哈希缓存在 `audio/eleven/`。
- **混音**（`edit_film.py` 已实现）：
  - 配乐用旁白做侧链压缩（阈值 0.03，比例 6）；
  - 音效也用旁白做侧链，但更轻（阈值 0.04，比例 3）；
  - 最后 loudnorm 到 I=-16、TP=-1.5。

---

## 8. 技术规范

### 8.1 渲染
- 建模分工见 6.4 节：核心科学结构只写 Blender Python；Tripo / Meshy 只用于周边道具。
- Blender 5.2：EEVEE 用于风格化镜头，Cycles 用于真实渲染。Metal 显存不够时会自动改用 CPU 重试。
- 质量预设：preview 640×360，sample 960×540，final 1920×1080；24 fps。
- 镜头登记在 `episodes/<期>/blender/shots/registry.yaml`。常用字段：
  - `scene`、`args`、`camera`、`style`、`engine`；
  - `start`：从模拟的第几帧开始，可以是小数，也可以小于 1；
  - `step`：每帧前进几个模拟帧，小于 1 就是慢动作；
  - `black_tail`：结尾留几帧黑场。
- **单帧试渲**：`DREAMFORGE_RENDER_DIR=<临时目录> blender -b --factory-startup -P shared/tools/render_storyboard.py -- --shot X --quality preview --frames 1,60`（也可写 `1,mid,last`；批量用 `FRAMES=1,mid,last shared/tools/render_batch.sh preview <id>...`）。改动后先试渲几帧，确认无误再整段渲染。
- **不开 GPU 的冒烟**：`blender -b --factory-startup -P shared/tools/build_check.py -- [--shots X,Y | --segment B]`。逐镜 build、套风格、切到首 / 中 / 尾帧，检查相机存在、视野里有东西，并核对 registry 覆盖 timed.yaml 的全部镜头 id；不渲染（`--render X` 才渲 1 帧）。registry 里只有 `mograph:` 的条目是 2D 镜头，跳过。
- 渲染时会在开头读取场景脚本；**渲染进行中改脚本，可能导致同一批镜头用的不是同一版代码**。改完要确认哪些镜头需要重渲。
- 共用中心点和位置用常量（例如 `BM.CENTER`、`BM.RETICLE`），不要在各个镜头里硬写坐标。

### 8.2 环境坑
- 系统 python3 有 Pillow，但缺 SSL 证书；`.venv` 有 certifi、faster-whisper、PyMuPDF，但没有 Pillow。需要联网下载的用 `.venv/bin/python`，或依赖 `eleven.py` / `fetch_assets.py` 里已加的 CA 处理。
- 语音识别的计算精度由环境变量 `DREAMFORGE_ASR_COMPUTE` 决定（默认 `int8`；box 上用 `float32`，见第 9 节）。
- `.venv` 没有 pip，装包用 `uv pip install --python .venv/bin/python <包名>`。
- 素材下载：`shared/tools/fetch_assets.py`。会校验 Poly Haven 文件的 md5，Wikimedia 图片的授权必须是 CC0，否则报错。下载目录 `shared/assets/` 不入库。
- 后台长任务用工具自带的后台运行方式，不要用 `&` 自己挂起，否则完成时收不到通知。

---

## 9. 踩过的坑（新 agent 务必看）
| 现象 | 原因 | 做法 |
|---|---|---|
| 光路在中间焦点处拐弯 | 自己排的光路；中间焦点只是会聚点，不是镜子 | 照一手资料的光路图画，每个转折点都必须是镜子 |
| 说 High-NA 有 8 面镜 | 来自注明“仅作示意”的旧路线图和二手文章 | 只用设计示例图上的结构；没有原文的数字不进旁白 |
| 芯片照片用了 14 nm、7 nm 的芯片 | 没核实制造工艺 | 只用确实采用 EUV 的芯片，标注型号和工艺 |
| 芯片表面整片是平滑的彩虹渐变 | 不懂衍射的物理 | 按区块做光栅：每块有自己的周期和朝向，用衍射方程算颜色 |
| “12 月交付” | 把发货当成交付 | 区分发货、运抵、安装完成 |
| 彩色海运集装箱、胶合板箱 | 凭想象画 | 照官方视频画白色运输箱、货网托盘、平板挂车 |
| 锡滴旁边多了个“月牙” | 镜面锡滴映出了背后虚焦的收集镜 | 冷开场用纯黑背景，去掉干扰物 |
| 薄盘表面一团团斑驳 | 镜面材质映出环境 | 提高粗糙度，减弱褶皱 |
| 片名被画面上沿裁掉 | 镜头没考虑片名位置 | 片名全程在画面内，机器变高时同步调整片名 |
| 浅色画面上字幕看不清 | 字幕只有阴影 | 字幕加深色描边 |
| 关键词被音效盖住 | 音效压在词上 | 音效侧链压缩，冲击挪到旁白空档 |
| 配音把“这是一滴锡”念含糊 | 选版只看语速和音高 | 选版时用语音识别打分，取最难听清那句的分数 |
| 核对报告里一大半是“掩模→眼膜”这类误报 | 按汉字比较，同音字被算成错 | 按不带声调的拼音比较，另加术语检查 |
| 混音成片没有生成 | 新音效请求遇到 SSL 证书错误 | 已在 eleven.py 里修复；剪辑后要确认 mp4 确实生成了 |
| 两个同名 `after_style`，后一个覆盖前一个 | 复制粘贴 | 一个模块只写一个 after_style，内部再按镜头分支 |
| 整机耗电写成“据行业估算” | 只找了媒体来源 | ASML 年报里就有一手数字（NXE:3800E 约 1.26 MW）。遇到 C 级数字，先找一手来源，找不到再删 |
| 后台配音任务出错，后面的步骤还在用旧数据跑 | 用管道过滤输出，错误被吞掉 | 长链条命令加 `set -e -o pipefail`，完整日志写进文件 |
| 只重配一段（`--segments B1`）后，其他段的配音全部“找不到” | tts.py 局部运行时用这一段覆盖了 timing.json 和 sentences.json | tts.py 已改为局部运行时保留其他段；跑完后台任务必须看日志结尾，不能只看外层退出码 |
| 改坏了 facts.yaml，校验却显示“通过” | 跑校验时只用 grep 筛 ERROR/WARN，Python 报错被筛掉 | 校验命令不过滤输出，看退出码；改完 YAML 立刻 `yaml.safe_load` 一遍 |
| 语音识别整段输出乱码（「点击点击」、夹英文碎词），所有版本得分 0 | 部分 x86 CPU 上 faster-whisper 的 int8 计算出错（2026-10-21 在 box 的 Xeon 上复现；float32 正常） | 在 Linux box 上设 `DREAMFORGE_ASR_COMPUTE=float32`；识别缓存 `*.asr.txt` 若是乱码要删掉重识别 |

---

## 10. 目录结构
```
eigenlens/
├── README.md
├── docs/WORKFLOW.md              本文件
├── shared/
│   ├── tools/                    tts / vo_align / retime / asr_check / lint_script / storyboard_check /
│   │                             render_storyboard / render_batch.sh / mograph / edit_film / eleven /
│   │                             fetch_assets / paths（当前期由 DREAMFORGE_EPISODE 切换，默认 E1）
│   ├── blender/                  common（场景、HDRI）、materials（含 Poly Haven PBR）、styles（画面语言）
│   └── assets/                   下载的 CC0 素材（不入库）
└── episodes/E<n>-<短名>/
    ├── research/                 facts.yaml；visual/（调研报告、audit_<段>.yaml、audit_backlog.yaml、assets.yaml）
    ├── script/                   script_zh.md、pronunciation.yaml
    ├── storyboard/               parts/*.yaml → storyboard.yaml → storyboard.timed.yaml
    ├── sound/                    <段>.yaml（配乐和音效）
    ├── subs/                     zh.srt
    ├── blender/                  scripts/（建模）、shots/（镜头和 registry.yaml）
    ├── mograph/                  二维镜头
    ├── audio/                    配音和音效缓存（不入库）
    └── renders/                  shots/、edit/、review/（审片和参考资料，不入库）
```

根目录名是 `eigenlens`。树里的 `DREAMFORGE_EPISODE` 是仍在使用的旧环境变量，见文首「品牌」。

## 11. 新开一期
1. 复制 `episodes/E1-*/` 的目录骨架，不复制 audio 和 renders。
2. 设置 `DREAMFORGE_EPISODE=E<n>-<短名>`。
3. 从 P1 调研开始，按第 3 节逐个阶段推进，第 1、2 节的规则同样适用。

E2《光遗传学》在 `episodes/E2-optogenetics/`。检查点①、检查点②（全片动态分镜）都已于 2026-10-21 通过，见该期 README。P7 建模与镜头已完成；下一步是 P8 第一批试渲：按 [RUNPOD.md](RUNPOD.md) 用 API 开 GPU，镜头和命令见该期 `FIRST_BATCH.md`。

## 12. 拉取请求审查

`main` 受保护，必需检查是 `review`。仓库已打开 squash 自动合并，会等 `review` 通过。检查项见 [REVIEW.md](REVIEW.md)。用 `gh pr merge --auto --squash`，不要加 `--admin`，不要直接 push 到 `main`。
