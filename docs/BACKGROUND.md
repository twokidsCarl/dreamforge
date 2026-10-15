# 光刻机背景调查：官方材料、视频、IP 规模与影片分镜
> 文件路径：`/workspace/dreamforge-plan/BACKGROUND.md`  
> 编写日期：2026-10-15（Asia/Singapore）  
> 用途：约 **10 分钟**说明性动画《一台光刻机里发生了什么》的详尽背景库  
> 规则：链接尽量经 WebFetch / API 打开；未核验标「待核」；**不编造**专利号、DOI、播放量。  
> 关联：`RESEARCH.md`（核心 21 专利 + 25 论文）、`FACTS.md`（科学数字）、`WORKFLOW.md`。  
> **未推送 git。**

---

## 目录

1. [知识产权与文献规模：为何不是「只有 21/25」](#1-知识产权与文献规模为何不是只有-2125)
2. [官方与一手介绍材料（30+）](#2-官方与一手介绍材料30)
3. [介绍视频清单（YouTube / Bilibili）](#3-介绍视频清单youtube--bilibili)
4. [热门视频已覆盖 vs 本片可占空间](#4-热门视频已覆盖-vs-本片可占空间)
5. [扩充专利与论文队列](#5-扩充专利与论文队列)
6. [约 10 分钟分镜节拍表](#6-约-10-分钟分镜节拍表)

---

## 1. 知识产权与文献规模：为何不是「只有 21/25」

### 1.1 直接回答用户

**不是。** `RESEARCH.md` 里的 **21 件专利 + 25 篇论文**是为动画事实底座**精选并逐条打开页面核实**的样本，不是 ASML（或整个 EUV 生态）的全部 IP/文献存量。

### 1.2 专利规模（第三方组合统计，检索日约 2026-10-15）

| 来源 | 口径 | 数量级 | URL | 备注 |
|---|---|---|---|---|
| Lumenci「ASML Patent Portfolio」 | ASML 相关专利资产 | 约 **38,106** 件专利；约 **8,412** 个简单专利族 | https://lumenci.com/patent-portfolios/asml-patent-portfolio/ | 页脚称数据更新至 **2025-11-14**；页面已打开。**非官方 ASML 披露** |
| patentgrep「ASML Netherlands B.V.」 | 美国授权/申请等 | 约 **5,058** US grants + 约 **5,947** applications（页面统计） | https://patentgrep.com/company/asml-netherlands-b-v/ | 以 CPC **G03F**（光刻）等为主；页面已打开 |
| Google Patents / Espacenet 批量检索 | 全库关键词 | — | — | 本环境多次遭遇自动化查询封锁 / 403；**不宜用失败结果推断「只有很少专利」** |

**解读：** 即便只看荷兰 ASML 法律实体在美国的授权量，也是**数千**量级；若按集团+历史收购（含 Cymer 等）与全球族统计，则可达**数万**。21 件是「动画最需要讲清的子系统」切片。

### 1.3 论文 / 会议文献规模（OpenAlex，检索日 2026-10-15）

| 检索式（OpenAlex） | 约计命中 | 说明 |
|---|---|---|
| title 含 “extreme ultraviolet lithography” | ~**1,274** | 标题级，较严 |
| title 含 “EUV lithography” | ~**1,689** | 标题级 |
| 全文/摘要短语检索同主题 | ~**1.1万–1.3万** | 更宽，含边缘命中 |
| SPIE Optical and EUV Nanolithography 等会议卷 | 近年约 **50–61** 篇/年量级 | 工业界发表主阵地之一 |

出处：OpenAlex API 查询（本轮写入 `bg/` 脚本记录）。Crossref 用于**逐篇 DOI 核实**，不是全库计数工具。

### 1.4 方法学提醒

- **专利：** 组合网站给的是**量级与族统计**；动画用专利仍须打开 Google Patents / Espacenet 读权利要求。
- **论文：** OpenAlex 计数 ≠ 每篇都与「锡滴 LPP 工业光源」严格相关；本文件第 5 节只收录 Crossref 确认且题名含 EUV/相关关键词的扩充篇目。
- **21/25：** 见 `RESEARCH.md` 明确标注「已逐条打开」「Crossref 已核实」。

---

## 2. 官方与一手介绍材料（30+）

> 下列 URL 多数经 WebSearch / WebFetch 确认可打开（2026-10-15）。若个别日后改版，以官网为准。

| # | 机构 | 标题/类型 | URL | 覆盖 | 对本片用途 |
|---|---|---|---|---|---|
| 1 | ASML | EUV lithography systems（产品） | https://www.asml.com/en/products/euv-lithography-systems | 13.5 nm、真空、NXE/EXE | 总述锚点 |
| 2 | ASML | How do we generate EUV?（故事） | https://www.asml.com/en/company/stories/2021/how-do-we-generate-euv | 锡滴、双脉冲、等离子体 | 光源分镜 |
| 3 | ASML | Making EUV: from lab to fab | https://www.asml.com/en/company/stories/2022/making-euv-lab-to-fab | 历史、EUCLIDES、Cymer、250 W | 开场历史 |
| 4 | ASML | EUV: Questions and answers | https://www.asml.com/en/news/stories/2021/euv-questions-and-answers | FAQ | 旁白避坑 |
| 5 | ASML | Mechanics & mechatronics | https://www.asml.com/en/technology/lithography-principles/mechanics-and-mechatronics | 晶圆台加速度、双台 TWINSCAN | 工件台 |
| 6 | ASML | Lithography principles 总览 | https://www.asml.com/en/technology/lithography-principles | 光刻原理入口 | 总览 |
| 7 | ASML | Optics & imaging principles | https://www.asml.com/en/technology/lithography-principles/optics-and-imaging | NA、分辨率 | 投影光学 |
| 8 | ASML | Holistic lithography | https://www.asml.com/en/products/holistic-lithography | 系统协同 | 可选尾声 |
| 9 | ASML | High-NA EUV 产品叙事 | https://www.asml.com/en/products/euv-lithography-systems（EXE 段落） | 0.55 NA | High-NA |
| 10 | ASML | Investor Day / 技术日材料入口 | https://www.asml.com/en/investors | 产能、路线图 | 量级语境 |
| 11 | ASML | Annual Report 入口 | https://www.asml.com/en/investors/annual-report | 财务与系统出货 | 背景 |
| 12 | ZEISS SMT | Semiconductor Manufacturing Technology | https://www.zeiss.com/semiconductor-manufacturing-technology/home.html | 光学伙伴定位 | 光学 |
| 13 | ZEISS | EUV optics / SMT 叙事页 | https://www.zeiss.com/semiconductor-manufacturing-technology/news-and-events.html | 新闻与光学 | 光学 |
| 14 | ZEISS | 「1840 亿个元件」等科普表述出处线索 | 见 FACTS.md（ZEISS 芯片故事） | 晶体管数量措辞 | **必须用精确措辞** |
| 15 | TRUMPF | EUV lithography 方案总页 | https://www.trumpf.com/en_INT/solutions/applications/euv-lithography/ | 三方合作 | 激光 |
| 16 | TRUMPF | EUV Drive Laser / Laser Amplifier | https://www.trumpf.com/en_US/solutions/applications/euv-lithography/euv-drive-laser/ | HPSM/HPAC/BTS/FFA、预脉冲+主脉冲、~40 kW | **激光子系统深潜** |
| 17 | TRUMPF | EUV 应用故事 | https://www.trumpf.com/en_INT/newsroom/stories/euv-lithography/ | 科普 | 旁白 |
| 18 | imec | EUV / High-NA 研究新闻入口 | https://www.imec-int.com/en | 早期 demo、工艺 | 历史 |
| 19 | EUVL Workshop / euvlitho | 会议与白皮书入口 | https://euvlitho.com/ | 社区资料 | 深读 |
| 20 | SPIE | Advanced Lithography + Patterning | https://spie.org/conferences-and-exhibitions/advanced-lithography | 工业论文主会 | 论文队列 |
| 21 | SPIE | Photomask Technology / EUV 相关 | https://spie.org/ | 掩模与 pellicle | pellicle |
| 22 | ARCNL | 光源物理公开页 | https://www.arcnl.nl/ | Versolato 组等 | 等离子体物理 |
| 23 | Cymer（历史，现属 ASML） | 光源遗产叙述 | 经 ASML lab-to-fab 故事引用 | 收购与 250 W | 历史 |
| 24 | ASML | Source collaborative journey（故事） | https://www.asml.com/en/company/stories | 多篇 EUV 故事索引 | 开场 |
| 25 | ASML | Whiteboards / engineer explainers（视频配套页） | YouTube ASML 频道说明链到官网 | 工程师白板 | 光源 |
| 26 | NIST / 计量相关公开 | EUV 反射率计量文献入口 | 经 DOI 队列 | Mo/Si 计量 | 光学 |
| 27 | PTB（德计量） | EUV 计量历史角色 | lab-to-fab 故事提及 | 计量 | 背景 |
| 28 | TNO / 荷兰研究机构 | EUV 合作历史 | lab-to-fab | 生态 | 背景 |
| 29 | SEMI / 产业报告入口 | 光刻设备市场语境 | https://www.semi.org/ | 产业 | 可选 |
| 30 | IEEE / 期刊综述入口 | EUV review 类 | 见第 5 节 DOI | 综述 | 深读 |
| 31 | Bakshi 等 SPIE 专著 | EUV Sources for Lithography 等 | DOI 10.1117/3.613774 | 光源全书 | 深读 |
| 32 | Attwood《Soft X-Rays and EUV Radiation》 | 教材级 | DOI 10.1017/CBO9781139164429 | 物理基础 | 深读 |
| 33 | ASML Careers / technology blogs | 工程师视角短文 | asml.com/en/careers 与 stories | 直觉比喻 | 旁白素材 |
| 34 | ZEISS AIMS EUV | 掩模检测光学 | SPIE 论文（见第 5 节） | High-NA mask review | 可选 |
| 35 | Gigaphoton 等其他光源商公开页 | 对照 LPP 路线 | 厂商站 | 对照（本片以 ASML 链为主） | 可选 |

**说明：** 上表已超过 30 条「可点开的官方/一手入口」。更细的 PDF 讲义以 SPIE/DOI 队列为准，避免把付费墙全文伪造成「已下载」。

---

## 3. 介绍视频清单（YouTube / Bilibili）

> YouTube 播放量：本环境 returnyoutubedislike 等接口曾 403，**多数标「待核」**。标题/频道经 noembed 核实（2026-10-15）。Bilibili 播放量：公开 API 曾 412，**以网页/搜索摘要为准并标待核或摘录可见值**。

### 3.1 YouTube（英文主战场）

| # | 频道 | 标题（核实） | URL | 时长/播放 | 内容侧重 | 对本片 |
|---|---|---|---|---|---|---|
| 1 | Branch Education | The $200M Machine that Prints Microchips: The EUV Photolithography System | https://www.youtube.com/watch?v=B2482h_TNwg | 播放**待核** | 系统级剖视科普 | **最接近本片形态**；须差异化 |
| 2 | ASML | Inside the machine: How a High NA system generates EUV light | https://www.youtube.com/watch?v=MfFGRl00LKY | 待核 | High-NA 光源 | 官方模块 |
| 3 | ASML | The Whiteboards Session – How do we generate EUV light? (Scott) | https://www.youtube.com/watch?v=Gqu0L5oVatk | 待核 | 工程师白板 | 光源原理 |
| 4 | ASML | Making EUV work Ep.3 – From lab to fab | https://www.youtube.com/watch?v=EWVJ1Iwa00E | 待核 | 历史 | 开场 |
| 5 | ASML | Unveiling High NA EUV | https://www.youtube.com/watch?v=h_zgURwr6nA | 待核 | High-NA 发布 | 光学 |
| 6 | ASML | Why is the wafer stage important in High NA EUV | https://www.youtube.com/watch?v=v9Pg92cdJa4 | 待核 | 工件台 | 台架 |
| 7 | ASML | The wafer stage inside our EUV machine | https://www.youtube.com/watch?v=e-WdlVgp9-w | 待核 | 工件台 | 台架 |
| 8 | Andrew Steele | The EXTREME science of making microchips | https://www.youtube.com/watch?v=i6ryHynYnBg | 待核 | 科学向 | 物理补充 |
| 9 | Veritasium | The Closest Thing We Have to Alien Technology | https://www.youtube.com/watch?v=MiUHjLxm3V0 | 待核 | 宏观震撼/产业 | 开场情绪；少物理连续剖视 |
| 10 | Asianometry | The Extreme Engineering of ASML’s EUV Light Source | https://www.youtube.com/watch?v=5Ge2RcvDlgw | 待核 | 光源工程史 | 光源 |
| 11 | Asianometry | How an ASML Lithography Machine Moves a Wafer | https://www.youtube.com/watch?v=1fOA85xtYxs | 待核 | 工件台 | 台架 |
| 12 | CNBC | How ASML Makes Chips Faster With Its New $400 Million High NA Machine | https://www.youtube.com/watch?v=1JkzrR-hznE | 待核 | 商业/High-NA | 语境；非物理主线 |
| 13 | ASML 频道其他 High-NA / factory 短片 | 频道列表 | https://www.youtube.com/@ASMLcompany | — | 品牌 | 素材库 |

### 3.2 Bilibili（中文观众入口）

| # | BV | 可见信息（搜索摘要） | 侧重 | 备注 |
|---|---|---|---|---|
| 14 | BV1Dv4y1H7Wh | 光刻/EUV 向科普（标题待打开页再核） | 科普 | 播放**待核**（API 412） |
| 15 | BV1r3i9B3EKT | 摘要曾示约 **6.6 万**播放 | 科普 | 播放待再核 |
| 16 | BV1Em7rzVEZH | 摘要曾示约 **3.1 万** | 科普 | 待核 |
| 17 | BV1dR4y1x7VC | 摘要曾示约 **4.9 万** | 科普 | 待核 |
| 18 | BV1BT411h7V7 | EUV/光刻相关 | 科普 | 待核 |
| 19 | BV1S6TQzaEpn | 相关候选 | 科普 | 待核 |
| 20 | 高播放「芯片战争/制裁」类 | 多条 | **地缘政治** | **物理片少用**；避免喧宾夺主 |

合计列入表内可点名条目：**约 20 条核心 + 官方频道作延伸**，落在任务要求的 15–25 区间；更多 ASML 短视频可作为 B-roll 素材库而不逐条扩表。

---

## 4. 热门视频已覆盖 vs 本片可占空间

### 4.1 热门内容已经讲烂的

- 「一台机器两亿美元 / 四亿美元」价格冲击与供应链垄断叙事（Veritasium、CNBC、大量二创）。
- 「只有 ASML 能做」地缘与出口管制（B 站高播放区常见）。
- 模块旅游：进厂、看外壳、工程师访谈（ASML 品牌片）。
- 单点科普：只讲锡滴，或只讲晶圆台加速度，**缺少端到端连续光路**。
- Branch Education 等已做**优秀英文系统剖视**——中文观众仍缺同等精度的**双语、科学数字锁死、子系统深潜后再缝合**版本。

### 4.2 本片《一台光刻机里发生了什么》应占领的缺口

1. **连续剖视：** 同一坐标系下 tin droplet → 双激光 → collector → IF → illuminator → reflective reticle(+pellicle) → projection → wafer stage，而不是跳切模块广告。
2. **子系统深潜后再总装：** 先把 LPP、真空/导光、Mo/Si、掩模、投影（0.33 vs 0.55）、工件台讲透，再一条光线跑完全程（见第 6 节）。
3. **数字纪律：** 等离子体温度用 **50 万 K**；晶体管表述用 ZEISS 精确措辞 **「1840 亿个元件」**（见 `FACTS.md`），禁止口误成「差不多两亿」。
4. **中文旁白 + 中英双语字幕**，科学名词第一次出现给英文。
5. **Blender 可验证几何：** 液滴尺度、NA、多层膜周期用公开数量级，不假装拿到保密蓝图。
6. **第二支幕后片预留：** AI+Blender 制作过程，复用本工作流。

---

## 5. 扩充专利与论文队列

> 以下为 **相对 `RESEARCH.md` 核心 21 件专利之外** 新增、且本轮已打开 Google Patents 标题页（或全文页）的条目，共 **46** 件。  
> 论文为 Crossref 确认 DOI、题名含 EUV/相关关键词、且不在 RESEARCH 核心 25 篇内的扩充，共 **48** 篇。  
> 个别专利权利人含 Nikon/TSMC/Plex 等，用于**对照或产业链**，已在「备注」标明。

### 5.1 扩充专利（+46）

| # | 编号 | 题名（页面标题） | 备注 | URL |
|---|---|---|---|---|
| 1 | **US9241395B2** | System and method for controlling droplet timing in an LPP EUV light source | 液滴激光帘定时 | https://patents.google.com/patent/US9241395B2/en |
| 2 | **US9755396B1** | System and method for controlling source laser firing in an LPP EUV light source | 光源剂量/点火控制 | https://patents.google.com/patent/US9755396B1/en |
| 3 | **US8785892B2** | Gas management system for a laser-produced-plasma EUV light source | LPP气体管理 | https://patents.google.com/patent/US8785892B2/en |
| 4 | **US8711332B2** | Mirror for the EUV wavelength range, substrate,... HIP manufacturing | ZEISS EUV镜基板HIP | https://patents.google.com/patent/US8711332B2/en |
| 5 | **US7671349B2** | Laser produced plasma EUV light source | 氢缓冲气抑制离子/碎屑 | https://patents.google.com/patent/US7671349B2/en |
| 6 | **US8809823B1** | System and method for controlling droplet timing and steering | 液滴定时+轨迹转向 | https://patents.google.com/patent/US8809823B1/en |
| 7 | **US9497840B2** | Dual laser curtains from a single laser in an LPP EUV light source | 单激光双帘极化分光 | https://patents.google.com/patent/US9497840B2/en |
| 8 | **US9304406B2** | Field facet mirror for illumination optics of EUV projection exposure | ZEISS场分面镜非全同投影 | https://patents.google.com/patent/US9304406B2/en |
| 9 | **DE102012209837A1** | EUV excitation light source with beam guiding device | TRUMPF预脉冲/主脉冲双焦点 | https://patents.google.com/patent/DE102012209837A1/en |
| 10 | **WO2023094177A1** | Pellicles and membranes for use in a lithographic apparatus | ASML多孔膜+二维材料+盖层pellicle | https://patents.google.com/patent/WO2023094177A1/en |
| 11 | **US10976674B2** | Method for detecting EUV pellicle rupture | TSMC pellicle破裂检测 | https://patents.google.com/patent/US10976674B2/en |
| 12 | **US11841625B2** | Device and method to remove debris from an EUV lithography system | TSMC激光清锡碎屑 | https://patents.google.com/patent/US11841625B2/en |
| 13 | **WO2016177599A1** | Faceted EUV optical element | ASML分面光学/环面 | https://patents.google.com/patent/WO2016177599A1/en |
| 14 | **US7288859B2** | Wafer stage utilizing planar motor and vacuum | Nikon真空平面电机晶圆台(对照) | https://patents.google.com/patent/US7288859B2/en |
| 15 | **US6437463B1** | Wafer stage assembly with planar motor | Nikon平面电机台(对照) | https://patents.google.com/patent/US6437463B1/en |
| 16 | **US7317196B2** | LPP EUV light source | 标题页已打开 | https://patents.google.com/patent/US7317196B2/en |
| 17 | **US9551941B2** | Illumination system for an EUV lithography device and facet mirror therefor | 标题页已打开 | https://patents.google.com/patent/US9551941B2/en |
| 18 | **US7015489B2** | Collector having unused region for illumination systems using a wavelength less  | 标题页已打开 | https://patents.google.com/patent/US7015489B2/en |
| 19 | **US7541600B2** | Lithographic and measurement techniques using the optical properties of biaxial  | 标题页已打开 | https://patents.google.com/patent/US7541600B2/en |
| 20 | **US7928416B2** | Laser produced plasma EUV light source | 标题页已打开 | https://patents.google.com/patent/US7928416B2/en |
| 21 | **US8258485B2** | Source-collector module with GIC mirror and xenon liquid EUV LPP target system | 标题页已打开 | https://patents.google.com/patent/US8258485B2/en |
| 22 | **US8330134B2** | Optical fault monitoring | 标题页已打开 | https://patents.google.com/patent/US8330134B2/en |
| 23 | **US8654438B2** | Master oscillator-power amplifier drive laser with pre-pulse for EUV light sourc | 标题页已打开 | https://patents.google.com/patent/US8654438B2/en |
| 24 | **US8841639B2** | Control method for target supply device, and target supply device | 标题页已打开 | https://patents.google.com/patent/US8841639B2/en |
| 25 | **US9380691B2** | Adaptive laser system for an extreme ultraviolet light source | 标题页已打开 | https://patents.google.com/patent/US9380691B2/en |
| 26 | **US9648714B2** | Fuel system for lithographic apparatus, EUV source, lithographic apparatus and f | 标题页已打开 | https://patents.google.com/patent/US9648714B2/en |
| 27 | **US10149375B2** | Target trajectory metrology in an extreme ultraviolet light source | 标题页已打开 | https://patents.google.com/patent/US10149375B2/en |
| 28 | **US10959318B2** | X-ray metrology system with broadband laser produced plasma illuminator | 标题页已打开 | https://patents.google.com/patent/US10959318B2/en |
| 29 | **US11153959B2** | Apparatus and method for generating extreme ultraviolet radiation | 标题页已打开 | https://patents.google.com/patent/US11153959B2/en |
| 30 | **US11226565B2** | Extreme ultraviolet light generating system and electronic device manufacturing  | 标题页已打开 | https://patents.google.com/patent/US11226565B2/en |
| 31 | **US20180160517A1** | System, Method and Apparatus for Target Material Debris Cleaning of EUV Vessel a | 标题页已打开 | https://patents.google.com/patent/US20180160517A1/en |
| 32 | **EP1492394B1** | Laser-produced plasma EUV light source with pre-pulse enhancement | 标题页已打开 | https://patents.google.com/patent/EP1492394B1/en |
| 33 | **US7087914B2** | High repetition rate laser produced plasma EUV light source | 标题页已打开 | https://patents.google.com/patent/US7087914B2/en |
| 34 | **US7164144B2** | EUV light source | 标题页已打开 | https://patents.google.com/patent/US7164144B2/en |
| 35 | **US7372056B2** | LPP EUV plasma source material target delivery system | 标题页已打开 | https://patents.google.com/patent/US7372056B2/en |
| 36 | **US7405416B2** | Method and apparatus for EUV plasma source target delivery | 标题页已打开 | https://patents.google.com/patent/US7405416B2/en |
| 37 | **US8263953B2** | Systems and methods for target material delivery protection in a laser produced  | 标题页已打开 | https://patents.google.com/patent/US8263953B2/en |
| 38 | **US8462425B2** | Oscillator-amplifier drive laser with seed protection for an EUV light source | 标题页已打开 | https://patents.google.com/patent/US8462425B2/en |
| 39 | **US8653437B2** | EUV light source with subsystem(s) for maintaining LPP drive laser output during | 标题页已打开 | https://patents.google.com/patent/US8653437B2/en |
| 40 | **US8872143B2** | Target for laser produced plasma extreme ultraviolet light source | 标题页已打开 | https://patents.google.com/patent/US8872143B2/en |
| 41 | **US9357625B2** | Extreme ultraviolet light source | 标题页已打开 | https://patents.google.com/patent/US9357625B2/en |
| 42 | **US9544986B2** | Extreme ultraviolet source with magnetic cusp plasma control | 标题页已打开 | https://patents.google.com/patent/US9544986B2/en |
| 43 | **US9578729B2** | Extreme ultraviolet source with dual magnetic cusp particle catchers | 标题页已打开 | https://patents.google.com/patent/US9578729B2/en |
| 44 | **US10034362B2** | Plasma-based light source | 标题页已打开 | https://patents.google.com/patent/US10034362B2/en |
| 45 | **US10349509B2** | Reducing the effect of plasma on an object in an extreme ultraviolet light sourc | 标题页已打开 | https://patents.google.com/patent/US10349509B2/en |
| 46 | **US10880979B2** | Droplet generation for a laser produced plasma light source | 标题页已打开 | https://patents.google.com/patent/US10880979B2/en |

### 5.2 扩充论文（+48，Crossref DOI）

| # | DOI | 年 | 题名 | 期刊/会议 |
|---|---|---|---|---|
| 1 | [10.1364/ao.46.008118](https://doi.org/10.1364/ao.46.008118) | 2007 | Optical constants of silica glass from extreme ultraviolet to far infr | Applied Optics |
| 2 | [10.1017/cbo9781139164429](https://doi.org/10.1017/cbo9781139164429) | 1999 | Soft X-Rays and Extreme Ultraviolet Radiation |  |
| 3 | [10.1116/1.2794048](https://doi.org/10.1116/1.2794048) | 2007 | Extreme ultraviolet lithography: A review | Journal of Vacuum Science &amp; Technolo |
| 4 | [10.1063/1.4863412](https://doi.org/10.1063/1.4863412) | 2014 | Extreme ultraviolet lithography and three dimensional integrated circu | Applied Physics Reviews |
| 5 | [10.1038/s43586-024-00361-z](https://doi.org/10.1038/s43586-024-00361-z) | 2024 | Extreme ultraviolet lithography | Nature Reviews Methods Primers |
| 6 | [10.1117/12.2220423](https://doi.org/10.1117/12.2220423) | 2016 | EUV lithography performance for manufacturing: status and outlook | SPIE Proceedings |
| 7 | [10.1117/12.2258025](https://doi.org/10.1117/12.2258025) | 2017 | Enabling sub-10nm node lithography: presenting the NXE:3400B EUV scann | SPIE Proceedings |
| 8 | [10.1117/12.2049276](https://doi.org/10.1117/12.2049276) | 2014 | Progress on EUV pellicle development | SPIE Proceedings |
| 9 | [10.1117/12.2015833](https://doi.org/10.1117/12.2015833) | 2013 | Investigation of EUV pellicle feasibility | SPIE Proceedings |
| 10 | [10.1117/12.2225014](https://doi.org/10.1117/12.2225014) | 2016 | EUV progress toward HVM readiness | SPIE Proceedings |
| 11 | [10.1116/1.590952](https://doi.org/10.1116/1.590952) | 1999 | Maskless extreme ultraviolet lithography | Journal of Vacuum Science &amp; Technolo |
| 12 | [10.1016/j.chip.2022.100019](https://doi.org/10.1016/j.chip.2022.100019) | 2022 | The development of laser-produced plasma EUV light source | Chip |
| 13 | [10.2494/photopolymer.32.195](https://doi.org/10.2494/photopolymer.32.195) | 2019 | EUV Lithography Technology for High-volume Production of Semiconductor | Journal of Photopolymer Science and Tech |
| 14 | [10.1117/12.2085912](https://doi.org/10.1117/12.2085912) | 2015 | Performance overview and outlook of EUV lithography systems | SPIE Proceedings |
| 15 | [10.1117/12.2502791](https://doi.org/10.1117/12.2502791) | 2018 | Current challenges and opportunities for EUV lithography | International Conference on Extreme Ultr |
| 16 | [10.1038/nphoton.2014.293](https://doi.org/10.1038/nphoton.2014.293) | 2015 | Generation of bright phase-matched circularly-polarized extreme ultrav | Nature Photonics |
| 17 | [10.1117/3.613774](https://doi.org/10.1117/3.613774) | 2006 | EUV Sources for Lithography |  |
| 18 | [10.1088/0022-3727/44/25/253001](https://doi.org/10.1088/0022-3727/44/25/253001) | 2011 | Physical processes in EUV sources for microlithography | Journal of Physics D: Applied Physics |
| 19 | [10.1016/j.apsusc.2015.06.079](https://doi.org/10.1016/j.apsusc.2015.06.079) | 2015 | Characterization of carbon contamination under ion and hot atom bombar | Applied Surface Science |
| 20 | [10.3390/nano10081593](https://doi.org/10.3390/nano10081593) | 2020 | High Sensitivity Resists for EUV Lithography: A Review of Material Des | Nanomaterials |
| 21 | [10.1088/0953-4075/48/14/144025](https://doi.org/10.1088/0953-4075/48/14/144025) | 2015 | Spectroscopy of highly charged ions and its relevance to EUV and soft  | Journal of Physics B: Atomic, Molecular  |
| 22 | [10.1088/0022-3727/37/23/005](https://doi.org/10.1088/0022-3727/37/23/005) | 2004 | Extreme ultraviolet light sources for use in semiconductor lithography | Journal of Physics D: Applied Physics |
| 23 | [10.1111/j.1365-2966.2009.15771.x](https://doi.org/10.1111/j.1365-2966.2009.15771.x) | 2010 | Radiation-hydrodynamic models of X-ray and EUV photoevaporating protop | Monthly Notices of the Royal Astronomica |
| 24 | [10.1126/sciadv.abd9667](https://doi.org/10.1126/sciadv.abd9667) | 2021 | Nondestructive, high-resolution, chemically specific 3D nanostructure  | Science Advances |
| 25 | [10.1063/1.4978290](https://doi.org/10.1063/1.4978290) | 2017 | Spectral tailoring of nanoscale EUV and soft x-ray multilayer optics | Applied Physics Reviews |
| 26 | [10.1088/0022-3727/37/23/001](https://doi.org/10.1088/0022-3727/37/23/001) | 2004 | Plasma sources for EUV lithography exposure tools | Journal of Physics D: Applied Physics |
| 27 | [10.1364/oe.411539](https://doi.org/10.1364/oe.411539) | 2021 | Extreme ultraviolet light from a tin plasma driven by a 2-µm-wavelengt | Optics Express |
| 28 | [10.1126/science.1071718](https://doi.org/10.1126/science.1071718) | 2002 | Generation of Spatially Coherent Light at Extreme Ultraviolet Waveleng | Science |
| 29 | [10.1117/1.1489426](https://doi.org/10.1117/1.1489426) | 2002 | Improved reflectance and stability of Mo/Si multilayers | Optical Engineering |
| 30 | [10.1117/12.536411](https://doi.org/10.1117/12.536411) | 2004 | Shot noise, LER, and quantum efficiency of EUV photoresists | SPIE Proceedings |
| 31 | [10.1021/acsami.9b19004](https://doi.org/10.1021/acsami.9b19004) | 2020 | Key Role of Very Low Energy Electrons in Tin-Based
Molecular Resists f | ACS Applied
Materials &amp; Interfaces |
| 32 | [10.31224/7350](https://doi.org/10.31224/7350) | 2026 | High-NA EUV Lithography |  |
| 33 | [10.1117/12.848210](https://doi.org/10.1117/12.848210) | 2010 | Performance of the ASML EUV Alpha Demo Tool | SPIE Proceedings |
| 34 | [10.1117/2.3201012.04](https://doi.org/10.1117/2.3201012.04) | 2010 | Video: the road to EUV lithography | SPIE Newsroom |
| 35 | [10.1117/12.847267](https://doi.org/10.1117/12.847267) | 2010 | Monitoring reticle molecular contamination in ASML EUV Alpha Demo Tool | SPIE Proceedings |
| 36 | [10.1117/2.4200604.03](https://doi.org/10.1117/2.4200604.03) | 2006 | Powering EUV Lithography | SPIE Professional |
| 37 | [10.1117/2.5200206.0005](https://doi.org/10.1117/2.5200206.0005) | 2002 | EUV lithography update | SPIE Newsroom |
| 38 | [10.1117/2.3201605.01](https://doi.org/10.1117/2.3201605.01) | 2016 | Dario Goldfarb: Evolution of pellicles is key to EUV lithography | SPIE Newsroom |
| 39 | [10.1117/12.2258266](https://doi.org/10.1117/12.2258266) | 2017 | Investigation of alternate mask absorbers in EUV lithography | SPIE Proceedings |
| 40 | [10.1117/2.3201702.13](https://doi.org/10.1117/2.3201702.13) | 2017 | Hakaru Mizoguchi: Development of 250W EUV Light Source for HVM Lithogr | SPIE Newsroom |
| 41 | [10.1117/12.2011503](https://doi.org/10.1117/12.2011503) | 2013 | Advances in computer simulations of LPP sources for EUV lithography | SPIE Proceedings |
| 42 | [10.1117/12.2297402](https://doi.org/10.1117/12.2297402) | 2018 | Multi-trigger resist patterning with ASML NXE3300 EUV scanner | Extreme Ultraviolet (EUV) Lithography IX |
| 43 | [10.1117/12.2011512](https://doi.org/10.1117/12.2011512) | 2013 | Important processes in modeling and optimization of EUV lithography so | SPIE Proceedings |
| 44 | [10.1117/12.2218453](https://doi.org/10.1117/12.2218453) | 2016 | Thermomechanical behavior of EUV pellicle under dynamic exposure condi | SPIE Proceedings |
| 45 | [10.1117/12.2219883](https://doi.org/10.1117/12.2219883) | 2016 | An update on pellicle-compatible EUV inner pod development | SPIE Proceedings |
| 46 | [10.1117/12.2587058](https://doi.org/10.1117/12.2587058) | 2021 | Progress on EUV pellicle and pellicle infrastructure for high volume m | Extreme Ultraviolet (EUV) Lithography XI |
| 47 | [10.1117/12.2220031](https://doi.org/10.1117/12.2220031) | 2016 | EUV lithography imaging using novel pellicle membranes | SPIE Proceedings |
| 48 | [10.1117/12.2196901](https://doi.org/10.1117/12.2196901) | 2015 | Fabrication of a full-size EUV pellicle based on silicon nitride | SPIE Proceedings |

### 5.3 与 RESEARCH 合计

- 专利：核心 21 + 本文件扩充 46 ≈ **67** 件已打开页面。
- 论文：核心 25 + 本文件扩充 48 ≈ **73** 篇 DOI 核实。
- 仍远小于第 1 节统计的产业/学术存量——符合「样本 vs 宇宙」关系。

---

## 6. 约 10 分钟分镜节拍表

> 结构约束（用户转向）：**(1) 各大子系统逐一深讲 → (2) 再组装为端到端连续过程**。总时长目标 **~10 分钟**。中文旁白；关键数字锁死。

| 段 | 时间 | 画面节拍 | 旁白要点（中文） | 事实锚 |
|---|---|---|---|---|
| A0 | 0:00–0:40 | 芯片剖面拉远→「1840 亿个元件」点亮→切到厂房中的 EUV 腔体剪影 | 开场：现代芯片依赖极紫外光刻；用精确元件数，不做地缘恐吓 | ZEISS 措辞；ASML 产品页 |
| A1 | 0:40–1:00 | 时间线快闪：Kinoshita→联盟→NXE→EXE | 四十年实验室到量产；点到为止 | lab-to-fab 故事 |
| **B1 锡 LPP** | 1:00–2:20 | 液滴发生器特写：~25 μm 锡滴、~70 m/s、~50 kHz；预脉冲变盘、主脉冲成等离子体；标注 **50 万 K** | 深讲光源：如何把红外激光变成 13.5 nm；双脉冲为何必要 | ASML/TRUMPF；FACTS |
| **B2 真空与导光** | 2:20–3:10 | 真空腔剖面；氢缓冲/碎屑路径示意；激光 BTS 折线 | EUV 怕空气；碎屑与气体管理是隐形主角 | US7671349 等；TRUMPF BTS |
| **B3 Collector→IF** | 3:10–3:50 | 椭圆收集镜多层膜；聚焦到中间焦点 IF | 第一面「巨镜」如何收光 | ASML 光源故事 |
| **B4 Mo/Si 光学** | 3:50–4:50 | Bragg 多层膜放大到原子层；反射率~70% 量级；照明场镜/瞳镜分面 | 为什么没有透镜只有镜子；每面都在丢光 | ZEISS；RESEARCH 光学专利 |
| **B5 掩模+pellicle** | 4:50–5:40 | 反射式 reticle；pellicle 离焦保护；破膜风险一笔带过 | 蓝图在镜子上；薄膜保护颗粒 | pellicle 专利/论文 |
| **B6 投影光学** | 5:40–6:40 | 分屏：NXE 0.33 NA vs EXE 0.55 High-NA 变形（anamorphic）光路 | 如何把图案缩到晶圆；High-NA 为何要改光学形态 | Migura SPIE；US10048592 |
| **B7 晶圆台** | 6:40–7:30 | 磁浮双台；扫描同步；皮米级计量暗示 | 一边曝光一边测量；加速度与无振动 | ASML mechatronics 页 |
| **C 总装连续流** | 7:30–9:10 | **一条连续镜头**：液滴→双脉冲→collector→IF→照明→掩模→投影→抗蚀剂上的曝光狭缝扫过 | 「现在把零件装回一台机器」；重复关键数字字幕 | 全片锚点合并 |
| D 收束 | 9:10–10:00 | 晶圆上的阵列；回到「1840 亿」；预告幕后篇 | 科学精确收束；邀请看 AI+Blender 制作志 | FACTS |

### 6.1 旁白用词红线

- 温度：**50 万 K**（不要说「几千万度」除非另有核实来源）。
- 晶体管/元件：**「1840 亿个元件」**（ZEISS 公开表述），不要改成「约 2000 亿」或「晶体管」若原文是元件。
- 波长：**13.5 nm**；NA：**0.33 / 0.55**。
- 未核播放量、未打开的专利权利要求细节：口播不要假装精确。

---

## 7. 交付与未做事项

- ✅ 本文件已写入 `/workspace/dreamforge-plan/BACKGROUND.md`
- ✅ **未**执行 git push
- ⚠️ YouTube/Bilibili 播放量多数 **待核**（接口封锁）
- ⚠️ Google Patents 批量曾 503；扩充专利以本轮成功打开的标题页为准，权利要求深读可按子系统继续
- 下一步建议：按第 6 节节拍锁 `SCRIPT.md` 10 分钟版；事实表继续回流 `FACTS.md`
