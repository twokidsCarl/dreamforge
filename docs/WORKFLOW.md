# Dreamforge 制作方案：《一台光刻机里发生了什么》
> 正片约 5 分钟｜Blender 3D｜中文旁白｜中英双语字幕｜外加一条幕后花絮：AI 如何用 Blender 做出这部片
> 编写日期：2026-10-15。标「✅」的链接或编号已经检索确认；标「⚠️待核」的写进脚本前必须再查原始出处。**不得编造数字。**

---
## 0. 总原则
1. **结构准确交给代码，画面质感交给人和 AI 打磨**：光刻机的关键结构（光源、收集镜、照明系统、掩模台、投影物镜、晶圆台）全部用 Blender Python 参数化建模，可以复现、可以修改；外壳、线缆、管路这类装饰件才用 AI 生成 3D。
2. **每个事实都要有出处**：脚本里每一句涉及事实的话，都在 `research/facts.yaml` 里有对应条目（来源、链接、原文摘录）。
3. **全程留痕**：所有 AI 对话、提示词、渲染日志、录屏都留下来，同时作为第二支片的素材。

---
## 1. 资料来源

### 1.1 专利（用于结构细节，叙述时用“示意”的说法）
| 编号 | 标题 | 权利人 | 状态 |
|---|---|---|---|
| US 9,715,174 | Droplet generator, EUV radiation source, lithographic apparatus… | ASML Netherlands B.V. | ✅ 2017-07-25 授权 |
| US 10,750,604 B2 / WO2017102261A1 | Droplet generator for lithographic apparatus, EUV source… | ASML | ✅ [Google Patents](https://patents.google.com/patent/WO2017102261A1/en) |
| US 12,324,084 | Apparatus for and method of controlling droplet generator performance | ASML | ✅ 2025-06-03 授权 |
| US 9,392,678 | Target material supply apparatus for an EUV light source | ASML（原 Cymer 一系） | ✅（锡液滴、毛细管喷嘴、高压供料） |

还要继续检索的方向（用 CPC 分类号 G03F7/70 和 H05G2/00 检索）：
- 收集镜去污染与碎屑抑制（氢气流）
- 多层 Mo/Si 反射镜（Zeiss）
- 预脉冲加主脉冲的打靶方式
- 磁悬浮双工件台

检索平台：
- [Google Patents](https://patents.google.com)
- [Espacenet](https://worldwide.espacenet.com)
- [CNIPA 专利检索](https://pss-system.cponline.cnipa.gov.cn)，用来查中国相关专利，例如上海微电子和国内高校的申请

### 1.2 论文与综述
- ✅ Versolato, *Physics of laser-driven tin plasma sources of EUV radiation for nanolithography*, Plasma Sources Sci. Technol. 28 (2019), [DOI 10.1088/1361-6595/ab3302](https://ui.adsabs.harvard.edu/abs/2019PSST...28h3001V/abstract)：光源物理方面的核心综述。
- ✅ ARCNL, *Microdroplet-tin plasma sources of EUV radiation driven by solid-state lasers* (Topical Review), J. Opt., [DOI 10.1088/2040-8986/ac5a7e](https://doi.org/10.1088/2040-8986/ac5a7e)，[开放 PDF](https://ir.arcnl.nl/pub/257/00205publishedVersion.pdf)。
- ✅ Bakshi, *Photon Source Technology for Lithography and Metrology: An Overview*, SPIE eBook (2023), [DOI 10.1117/3.2638242.ch1](https://doi.org/10.1117/3.2638242.ch1)。
- ✅ arXiv 2602.03583, *Multi-Diagnostic Characterization of Laser-Produced Tin Plasmas for EUV Lithography*, [链接](https://arxiv.org/html/2602.03583v1)。
- 还要补的方向：
  - 高数值孔径 EUV（High-NA，0.55 NA）的变形投影光学：SPIE Advanced Lithography 会议论文集
  - 多层膜反射镜：Mo/Si 膜系
  - 光刻胶随机效应（stochastics）
  - 工件台控制：机电一体化和磁悬浮相关论文
- 检索入口：
  - [SPIE Digital Library](https://www.spiedigitallibrary.org)
  - [arXiv](https://arxiv.org)
  - [Google Scholar](https://scholar.google.com)
  - [Semantic Scholar](https://www.semanticscholar.org)

### 1.3 官方资料（画面参考和公开数据的首选）
- ASML 官网的 EUV 技术页面、产品页（NXE / EXE 系列）、年报，以及 YouTube 官方动画：[asml.com](https://www.asml.com)。
- ZEISS SMT 的 EUV 光学页面：[zeiss.com/semiconductor-manufacturing-technology](https://www.zeiss.com/semiconductor-manufacturing-technology)。
- TRUMPF 的 EUV 驱动 CO₂ 激光放大器页面：[trumpf.com](https://www.trumpf.com)。
- 常被引用的公开数字，⚠️写进脚本前要逐条到 ASML 原文核对：
  - 13.5 nm 波长
  - 每秒约 5 万个锡滴
  - 每个锡滴被打两次（预脉冲加主脉冲）
  - 等离子体温度
  - 反射镜数量
  - 整机重量和运输方式

### 1.4 参考图
- ASML 新闻图库（press images）、公开技术讲座截图、SPIE 论文里的示意图。只作内部参考，**不直接出现在成片里**，以免版权问题。
- 整理进 `research/refs/`，每张图附 `source.txt`，写明来源链接。

---
## 2. 脚本与分镜工具
| 用途 | 工具 | 说明 |
|---|---|---|
| 资料汇总与事实表 | Claude Code（Opus）加网页检索 | 输出 `research/facts.yaml`，每条事实附来源 |
| 脚本 | Claude（Opus），人工审稿 | 中文口语化，按 5 分钟、约 1200 到 1300 字估算 |
| 分镜表 | Claude 输出 `storyboard.yaml` | 每个镜头写明：时长、画面、镜头运动、旁白段号、所需资产 |
| 动态分镜 | Blender 灰模加 EEVEE 快速出片 | 先锁节奏，再做精模 |

脚本结构（约 300 秒）：
1. **0:00–0:20 开场**：一颗锡滴被激光击中，爆成一团比太阳表面还热的等离子体（温度数字待核）。抛出问题：芯片上的电路是怎么“印”上去的？
2. **0:20–0:50 为什么需要 EUV**：用“越细的笔写越小的字”打比方，引出 13.5 nm 波长。
3. **0:50–1:50 光源**：锡液滴发生器、预脉冲把锡滴压扁、主脉冲把它打成等离子体、收集镜收光。这一段是全片的视觉高潮，用体积光来表现。
4. **1:50–2:50 光路**：EUV 会被空气吸收，所以整条光路都在真空里，而且只能用反射镜；讲多层 Mo/Si 反射镜和镜面精度（比喻要找到出处）。
5. **2:50–3:50 掩模与投影**：反射式掩模，投影物镜把图形缩小 4 倍（High-NA 是变形缩放）。
6. **3:50–4:30 工件台**：晶圆台高速运动，对准精度做到纳米级；用“两架飞机并排飞行、对准一根针”这类比喻（要核实或改写）。
7. **4:30–5:00 收尾**：一块晶圆、数十亿个晶体管，再回到那颗锡滴。

---
## 3. 图像生成（概念图、风格帧、四视图）
| 工具 | 用途 |
|---|---|
| Midjourney | 风格帧和整体氛围 |
| Nano Banana（Gemini 图像） | 局部修改，统一配色 |
| ComfyUI 加 Flux（本地、可控） | 四视图参考图（正、背、左、右）；用 ControlNet 锁定构图 |
| 即梦（中文提示友好） | 备用 |

产出：`art/styleframes/` 放 5 到 8 张关键帧；`art/refs4view/` 放每个 AI 生成资产对应的四视图。

---
## 4. 3D 资产：AI 生成和代码建模怎么分工
| 类型 | 方法 | 理由 |
|---|---|---|
| 光源腔、收集镜、反射镜组、掩模台、晶圆台、晶圆、光路 | **Blender Python 参数化建模**（Claude Code 写脚本，通过 [Blender MCP](https://github.com/ahujasid/mcp-for-blender) 实时调用） | 形状、比例、光路几何必须准确，可以复现、可以修改 |
| 外壳、管线、机柜、真空泵、线缆、洁净室环境 | AI 生成 3D：[Hunyuan3D-2.1](https://github.com/Tencent-Hunyuan/Hunyuan3D-2.1)（开源，带 PBR 材质）、Tripo、Hyper3D Rodin、Meshy | 只起装饰作用，追求速度 |
| 通用资产（HDRI、材质贴图） | Poly Haven（Blender MCP 内置） | 免费，CC0 授权 |

AI 生成资产的流程（借鉴 X 上已经验证有效的做法）：
1. 先出四视图参考图。
2. 交给 Tripo 或 Hunyuan3D 生成模型。
3. 让 Claude 检查拓扑、比例和朝向，并重新拓扑或简化。
4. 换成我们自己的材质。

**原则：不让大模型从零自由造型。**

---
## 5. Blender 精修
- **渲染器**：
  - 灰模和动态分镜用 EEVEE（Next）。
  - 成片用 Cycles（GPU、OptiX 加速，配合 OpenImageDenoise 降噪）。
- **材质（Principled BSDF）**：
  - 抛光金属：金属度 1，粗糙度 0.05 到 0.2。
  - 多层膜反射镜：用薄膜干涉（Thin Film）参数做出彩色光泽。
  - 晶圆表面：各向异性加衍射光泽。
- **体积效果**：
  - EUV 光束：Volume Scatter 配合低密度的“可视化光束”。注意 EUV 本身不可见，要在字幕里说明“示意”。
  - 等离子体：Emission 加 Volume，叠加 Geometry Nodes 生成的粒子。
- **Geometry Nodes**：锡液滴流、掩模上的电路图形、晶圆上的芯片阵列、真空腔里的氢气流线。
- **灯光**：三点布光加工业风 HDRI；暗场里用轮廓光勾出结构；以冷色为主，等离子体用暖色做对比。
- **镜头**：
  - 景深：近景 f/2.8 的效果。
  - 运动模糊：开启，用于锡滴和工件台的高速运动。
  - 镜头语言：缓推，加上“剖切显示内部结构”的转场。
- **合成**：Blender Compositor 处理辉光、光晕、镜头畸变和颗粒；渲染输出 OpenEXR 多通道。
- **渲染农场**：
  - 本机 GPU。
  - 云端 RTX 实例。
  - 农场服务：SheepIt（免费社区农场）、RebusFarm、GarageFarm。
  - 估算方法：先测单帧耗时，再乘以 9000 帧（5 分钟、30fps），最后决定用哪种。
- **后期**：DaVinci Resolve 负责剪辑、调色（ACES 或 AgX 色彩管理）和字幕压制。

---
## 6. 音频与字幕
| 环节 | 工具 |
|---|---|
| 中文旁白 | CosyVoice（阿里开源，可本地部署）、MiniMax 语音、ElevenLabs（多语种）；如果条件允许，用真人录音效果最好 |
| 配乐 | Suno（注意确认商用授权条款） |
| 音效 | Freesound（看清每条的授权）、ElevenLabs 音效生成 |
| 字幕 | 中文字幕以脚本原文为准，用 Whisper 或 faster-whisper 做时间轴对齐；英文由 Claude 翻译后人工校对，输出 SRT 或 ASS，在 Resolve 里双语压制 |

---
## 7. 幕后花絮拍摄计划（第二支片）
- **录屏**：用 OBS 全程录制 Claude Code 终端和 Blender 窗口。
- **延时**：每个镜头自动渲染关键帧截图，脚本用 `bpy.ops.render.opengl` 保存，按时间戳命名，最后拼成延时。
- **日志**：
  - 保存 Claude Code 的会话记录。
  - 用 git commit 历史画出“模型演化”。
  - 记录渲染耗时 CSV。
- **对比素材**：同一个镜头的四个阶段，灰模、材质、光照、成片，做“前后对比”。
- **叙事**：一句话提示，到 AI 写的建模脚本，再到报错修正，最后到成片。要如实展示人工介入的部分，这样更可信。

---
## 8. 分阶段流程（输入 → 输出）
| 阶段 | 输入 | 输出 | 用时（估计） |
|---|---|---|---|
| S1 调研 | 选题 | `research/facts.yaml`、`refs/`、`sources.md` | 3 天 |
| S2 脚本 | facts | `script/script_zh.md` 与审校版 | 2 天 |
| S3 分镜与风格 | script | `storyboard.yaml`、`art/styleframes/` | 2 天 |
| S4 灰模动态分镜 | storyboard | `blender/animatic.blend`、`renders/animatic.mp4`（含临时 TTS） | 3 天 |
| S5 建模 | refs、四视图 | `blender/scripts/*.py`、`assets/` | 5 到 7 天 |
| S6 材质、灯光、动画 | 模型 | `blender/shots/shotXX.blend` | 5 天 |
| S7 渲染 | shots | `renders/shotXX/*.exr` | 2 到 4 天 |
| S8 音频与字幕 | 定稿脚本 | `audio/vo_zh.wav`、`music/`、`subs/zh.srt`、`subs/en.srt` | 2 天 |
| S9 后期调色 | 渲染、音频 | `final/dreamforge_euv_v1.mp4` | 2 天 |
| S10 幕后花絮 | 录屏、日志 | `bts/bts_v1.mp4` | 3 天 |

**总计约 4 到 5 周**（单人加 AI，按全职估算）。

---
## 9. 仓库目录结构（多期视频）
每一期一个文件夹 `episodes/E<序号>-<英文短名>/`，所有期共用的代码放在 `shared/`。

```
dreamforge/
├── README.md
├── docs/WORKFLOW.md                本文件：通用制作流程
├── shared/                         所有期共用
│   ├── tools/                      配音、读音、对齐、分镜、渲染、剪辑、二维动画、校验等工具
│   │   └── paths.py                当前是哪一期、渲染和音频放哪（默认 E1，可用 DREAMFORGE_EPISODE 切换）
│   └── blender/                    场景设置、材质库、画面语言风格系统
└── episodes/
    └── E1-euv-lithography/         第一期《一台光刻机里发生了什么》
        ├── research/  facts.yaml
        ├── script/    script_zh.md  pronunciation.yaml
        ├── storyboard/ parts/  storyboard.yaml  storyboard.timed.yaml  REVIEW.md
        ├── subs/      zh.srt
        ├── blender/   scripts/（本期建模）  shots/（本期镜头与 registry.yaml）
        ├── mograph/   本期二维动画镜头
        ├── docs/      早期调研文档与第三稿剧本（历史）
        ├── experiments/  冒烟测试
        ├── audio/     配音缓存与成品（不入库）
        └── renders/   渲染输出（不入库）
```
新开一期：复制 `episodes/E1-*/` 的目录骨架（不复制 audio、renders），设置 `DREAMFORGE_EPISODE=E2-xxx` 后运行同一套工具。

## 10. 可复用的工作流
`shared/` 下的工具和 Blender 模块对每一期都通用；每期只写自己的事实库、剧本、分镜、建模和镜头。每个新项目照着 S1 到 S10 的检查清单走一遍。


## 时长与结构变更（2026-10-15）
- 成片从约 5 分钟改为约 **10 分钟**。
- 结构：先按子系统分讲（光源/锡滴与双脉冲、收集镜、真空光路、Mo/Si 多层膜、反射掩模与 pellicle、投影物镜含 High-NA、工件台），再组合成从锡滴到晶圆的完整流程。
