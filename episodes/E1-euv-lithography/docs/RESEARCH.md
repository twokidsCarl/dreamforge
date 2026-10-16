# EUV 光刻机详尽研究资料库（ASML NXE / EXE 级）

> 用途：5 分钟说明性 Blender 动画《一台光刻机里发生了什么》的事实底座  
> 编写：2026-10-15  
> 规则：**每个事实须有出处；数字未经原件核对一律标「待核」；不得编造专利号或数值。**  
> 相关旧稿：`/workspace/dreamforge-plan/WORKFLOW.md`（方案总纲）

---

## 目录

1. [历史脉络](#1-历史脉络)
2. [物理与子系统](#2-物理与子系统)
3. [已核实数字与待核项](#3-已核实数字与待核项)
4. [专利（已逐条打开页面核实）](#4-专利已逐条打开页面核实)
5. [论文（Crossref / DOI 已核实）](#5-论文crossref--doi-已核实)
6. [官方与行业一手来源](#6-官方与行业一手来源)
7. [动画可用：公开可视 vs 保密](#7-动画可用公开可视-vs-保密)
8. [缺口与下一步](#8-缺口与下一步)

---

## 1. 历史脉络

### 1.1 从 DUV 到 EUV

- 芯片特征尺寸逼近193 nm（ArF）浸没式光刻极限后，业界探索更短波长；**13.5 nm** 落在 Extreme Ultraviolet（EUV）波段，成为主流目标波长。出处：ASML 产品页写明「light with a wavelength of just 13.5 nm」——[asml.com EUV lithography systems](https://www.asml.com/en/products/euv-lithography-systems)。
- EUV 几乎被一切材料（含空气）强烈吸收，因此**整条光路必须在高真空中**，且**只能用反射光学**，不能用透射透镜。出处：同上 ASML 页「EUV light is absorbed by everything, even air… high vacuum」。
- 早期探索可追溯至 1980 年代；1994 年起产业联盟推进工业化；ASML 与合作伙伴长期坚持。出处：ASML「The road to EUV」时间线（同上页）。

### 1.2 三家核心角色

| 角色 | 公司 | 公开职责 |
|---|---|---|
| 整机与光源集成 | **ASML**（荷兰） | NXE/EXE 扫描仪、LPP 光源系统集成；2013 年起收购 Cymer 光源能力 |
| 投影 / 照明光学 | **Carl Zeiss SMT**（德国） | Mo/Si 多层膜 EUV 反射镜、投影物镜（含 High-NA 变形光学） |
| 驱动激光 | **TRUMPF**（德国） | 高功率脉冲 CO₂ 激光放大器链，用于锡靶 LPP |

出处：ASML「We acquired Cymer… to accelerate EUV source development」；ZEISS SMT / TRUMPF 产品线公开定位见第 6 节官方页。

### 1.3 NXE（0.33 NA）与 EXE High-NA（0.55 NA）时间线

| 节点 | 公开事实 | 出处 |
|---|---|---|
| 2006 | 首台 EUV demo tool 交付 Albany / imec | ASML road to EUV |
| 2010 | 首台预量产 TWINSCAN **NXE:3100** 出货 | 同上 |
| 2013 | 首台量产机 **NXE:3300** 出货 | 同上 |
| ~2016 起 | 客户加大订购 NXE:3400 等 | 同上 |
| 2020 初 | 庆祝第 100 台 EUV 出货 | 同上 |
| 在役代表性 | **NXE:3400C**（7/5 nm 节点量产）；**NXE:3600D**（5/3 nm）；**NXE:3800E**（面向 2 nm Logic / 先进 DRAM） | [ASML EUV products](https://www.asml.com/en/products/euv-lithography-systems) |
| 2023-12 | 首台 **High-NA** EUV 系统交付 | 同上 |
| 2025–2026 | EXE 平台预期支持高产量制造 | 同上 |
| High-NA 机型 | **EXE:5000**（首代 High-NA）；**EXE:5200B**（面向 sub-2 nm Logic / 先进 DRAM） | 同上 |

**光学关键差异（公开）：**

- NXE：NA **0.33**，分辨率约 **13 nm**（ASML 表述）。
- EXE High-NA：NA **0.55**，分辨率约 **8 nm**；采用新颖光学设计（变形 / anamorphic）。出处：ASML EXE 介绍 + Migura 等 SPIE 2015（见论文列表）。

---

## 2. 物理与子系统

光路主链（公开叙述，可作分镜骨架）：

```
锡液滴发生器 → CO₂ 激光（预脉冲 + 主脉冲）→ 锡等离子体（~13.5 nm）
    → 收集镜（collector）→ 中间焦点 IF
    → 照明光学 → 反射式掩模（reticle，常含 pellicle）
    → 投影光学（NXE 0.33 / EXE 0.55）→ 晶圆台 → 光刻胶
```

### 2.1 波长与真空

- **工作波长 13.5 nm**。出处：ASML 产品页。
- 真空必要性：EUV 被空气吸收。出处：同上。

### 2.2 锡 LPP 光源

**原理（综述级，Versolato 2019）：**  
CO₂ 激光轰击锡微液滴，产生高电离锡等离子体；离子退激 / 复合辐射出带内 EUV。详见 DOI [10.1088/1361-6595/ab3302](https://doi.org/10.1088/1361-6595/ab3302)。

**公开工艺画面（ASML）：**

- 「a CO₂ laser fires **two separate laser pulses** at a fast-moving drop of tin… vaporizes the tin and creates EUV light… **up to 50,000 times per second**.」  
  出处：[ASML How does EUV work?](https://www.asml.com/en/products/euv-lithography-systems)

**液滴发生器（专利族，结构示意可用）：**

- 熔融锡高压经微孔喷出，压电等电致动扰动使射流碎成液滴；可用调幅 / 调频扰动使液滴合并，以得到合适间距与抖动。代表性专利：US7897947B2、US8158960B2、US9715174B2、US10750604B2、US12295088B2、US8513629B2（见第 4 节）。
- 专利背景中反复出现的**研发量级**描述（非 ASML 量产规格承诺）：约 **40–100 kHz** 量级液滴、约 **10–50 μm** 量级液滴、约 **10–12 kW** 级 CO₂ 设想等——脚本中若引用须标明为「专利/文献中的典型量级」，或标待核。出处：如 US7897947B2 背景段。

**预脉冲 / 主脉冲：**

- 预脉冲改变液滴形貌（展平 / 膨胀），主脉冲再加热以提升转换效率——多篇 ARCNL / Cymer 文献与专利家族讨论。论文：Kurilovich PRA 2016/2018、Schupp PRA 2019、Fomenkov AOT 2017。

**等离子体温度：**

- 专利 / 综述常用表述：电子温度达 **数十 eV**（tens of eV）。出处：如 US7897947B2 背景；Versolato 综述。  
- 「比太阳表面更热」等科普比喻：**待核**具体对比数字后再写进旁白。

**转换效率 CE：**

- 定义为带内 EUV 功率与驱动激光功率之比；具体量产 CE 数值因机型与工况变化大，**待核** ASML/TRUMPF 最新公开值后再写入脚本。

### 2.3 收集镜、IF、照明

- **收集镜**：近正入射椭球多层膜镜，第一焦点在等离子体附近，第二焦点为 **中间焦点 IF**，再送入扫描仪光学。出处：多件 Cymer/ASML 光源专利背景（如 US7439530B2、US7872245B2）。
- **碎屑 mitigation**：锡离子 / 微滴会污染收集镜；工业方案含氢自由基清洗生成挥发性 **SnH₄** 等。专利：US11013096B2、US7372049B2。
- **照明系统**：场镜 / 瞳镜等反射元件整形光束后照到掩模。ASML 公开动画有「Optical column」说明。

### 2.4 Mo/Si 多层膜反射镜

- EUV 近正入射必须用**多层膜干涉反射**（典型 **Mo/Si** 交替）。出处：ZEISS / 专利 US7261957B2、US9915876B2；论文 Haase Optics Express 2017。
- **为什么镜片很多**：每面镜有限反射率，总透过率 ≈ Rⁿ，故光学设计在收集光、照明均匀性、像质之间折中，系统使用多面反射镜。  
  - **单面峰值反射率**常见公开量级约 **~70%**（理想实验室 Mo/Si），**待核**进脚本前查 ZEISS/文献精确值与「带内积分」定义。  
  - 「系统里大约十几面镜」类说法：**待核**具体机型光路图，动画中宜说「多面反射镜」并示意损耗，不写死未经核对的个数。

### 2.5 掩模（reticle）与 pellicle

- EUV 掩模为**反射式**多层膜图案。出处：ASML「Reticles… multilayer reflectors」。
- **Pellicle**：置于掩模前的超薄膜，挡住颗粒；因不在焦面，颗粒不会清晰成像到晶圆。EUV pellicle 材料与透射率是活跃研发区。专利：US11567399B2、US11231646B2；论文 Choi 等 Adv. Mater. Interfaces 2023、Membranes 2022。

### 2.6 投影光学：NA 0.33 vs High-NA 0.55

- 分辨率大致随 **λ / NA** 改善。  
- NXE：**NA 0.33**，公开分辨率约 **13 nm**。  
- EXE：**NA 0.55**，公开分辨率约 **8 nm**；采用 **变形（anamorphic）** 光学以在掩模放大倍率与视场之间折中。出处：ASML；Migura SPIE 2015 DOI 相关会议文；Levinson JJAP 2022 / JM3 2025。
- 缩小倍率：传统叙述常为 **4×**；High-NA 在扫描方向与正交方向倍率不同（变形）。出处：ASML「shrinking the reticle pattern by a factor of four」；High-NA 细节见 Levinson / Migura。

### 2.7 晶圆台（wafer stage）

- ASML 公开：「positions the wafer to within **a quarter of a nanometer**… checking and adjusting **20,000 times per second**.」出处：[ASML How EUV works](https://www.asml.com/en/products/euv-lithography-systems)。
- 双工件台（TWINSCAN）架构：曝光与计量可并行。出处：ASML 产品命名与资料。
- 平面电机 / 磁悬浮相关专利：US9172294B2（planar motor）、US6906789B2（磁浮 REMA 刀口级）。动画可表现「无机械导轨接触的悬浮运动」，具体气隙 / 加速度数字 **待核**。

### 2.8 光刻胶与随机效应（stochastics）

- EUV 光子能量高、单位剂量光子数相对少，导致**光子散粒噪声**与化学放大胶中酸扩散等共同造成线边缘粗糙度（LER）、随机缺陷。论文：Jiang 等 JPS 2019；Koyama JJAP 2021；Severi JM3 2022。
- 动画建议：用「每个像素只有很少几个光子」的可视化，避免过度简化成「胶不行」。

---

## 3. 已核实数字与待核项

### 3.1 可写入脚本的已核实公开数字

| 数字 / 事实 | 出处 |
|---|---|
| 波长 **13.5 nm** | ASML 产品页 |
| 锡滴被 **两次** 激光脉冲打击 | ASML「two separate laser pulses」 |
| 最高约 **50,000** 次/秒 | ASML「up to 50,000 times per second」 |
| NXE **NA = 0.33**；分辨率约 **13 nm** | ASML |
| EXE **NA = 0.55**；分辨率约 **8 nm** | ASML |
| 晶圆台定位约 **0.25 nm**（a quarter of a nanometer） | ASML |
| 晶圆台伺服约 **20,000 Hz** | ASML |
| 整机高真空光路 | ASML |
| 掩模图形缩小约 **4×**（标准叙述） | ASML |
| 等离子体电子温度 **数十 eV** 量级 | 专利背景 / Versolato 综述 |

### 3.2 明确标「待核」——未写入定稿旁白前须回原件

| 项目 | 备注 |
|---|---|
| 量产光源 EUV 功率（如 250 W / 500 W 档） | 投资者日 PDF 有讨论，须对 ASML 最新公开页/年报逐条核对 |
| 转换效率 CE 精确值 | 工况依赖大 |
| 等离子体「比太阳表面热多少倍」 | 科普常用，需统一换算依据 |
| 系统反射镜确切片数 | 机型相关；勿写死 |
| Mo/Si 单面反射率精确值 | 定义（峰值 vs 带内）不同 |
| 液滴直径量产规格 | 专利为研发范围，非规格书 |
| 晶圆台峰值加速度、扫描速度 | 未见本轮核实的一手规格句 |
| Overlay 具体规格（如 0.9 nm 等） | 投资者材料提及，待核最新产品说明书 |
| 整机重量、货柜运输件数 | 常见媒体数字，待核 ASML 原文 |
| Pellicle EUV 透射率精确值 | 材料世代不同 |

---

## 4. 专利（已逐条打开页面核实）

> 下列每条均已通过 `patents.google.com/patent/<ID>` 打开确认标题、权利人与摘要主旨。叙述动画结构时用「示意」，勿暗示未公开的内部尺寸。

### 4.1 液滴发生器 / 靶材输送（ASML / Cymer 系）

| 编号 | 权利人 | 一句话权利要求要旨 | URL |
|---|---|---|---|
| **US7897947B2** | ASML (ex-Cymer) | 用调频/调幅等多频扰动产生液滴流，使相邻液滴合并后再受激 | https://patents.google.com/patent/US7897947B2/en |
| **US8158960B2** | ASML | 扰动使液滴初速不同、间距在飞行中减小并可合并；含双液滴等模式 | https://patents.google.com/patent/US8158960B2/en |
| **US8513629B2** | ASML | 液滴发生器：第一波形造滴，第二波形清喷嘴污染物 | https://patents.google.com/patent/US8513629B2/en |
| **US8969840B2** | ASML | 致动器诱导喷嘴清洁的液滴发生器（同族延伸） | https://patents.google.com/patent/US8969840B2/en |
| **US9715174B2** | ASML | 含亥姆霍兹共振器结构的液滴发生器 / EUV 源 / 光刻机 | https://patents.google.com/patent/US9715174B2/en |
| **US10750604B2** | ASML | 带过滤等结构的液滴发生器 | https://patents.google.com/patent/US10750604B2/en |
| **US12295088B2** | ASML | 混合式（hybrid）液滴发生器 | https://patents.google.com/patent/US12295088B2/en |
| **US7872245B2** | ASML | 非竖直靶材输送路径、收集镜倾斜与接料/防护结构 | https://patents.google.com/patent/US7872245B2/en |

### 4.2 驱动激光与光束输送

| 编号 | 权利人 | 要旨 | URL |
|---|---|---|---|
| **US7439530B2** | ASML (ex-Cymer) | LPP 驱动激光：折转 + 收集镜孔径内聚焦镜；预脉冲/主脉冲同放；多放大器高重频 | https://patents.google.com/patent/US7439530B2/en |
| **US8461560B2** | ASML | LPP 驱动激光输送与聚焦相关系统 | https://patents.google.com/patent/US8461560B2/en |
| **WO2014044392A1** | TRUMPF | EUV 产生装置：中间腔与双窗等真空/导光结构 | https://patents.google.com/patent/WO2014044392A1/en |

### 4.3 收集镜清洁 / 碎屑

| 编号 | 权利人 | 要旨 | URL |
|---|---|---|---|
| **US7372049B2** | ASML | 氢自由基清洁光学元件的装置 | https://patents.google.com/patent/US7372049B2/en |
| **US11013096B2** | ASML | 光源内原位氢自由基除锡碎屑等 | https://patents.google.com/patent/US11013096B2/en |

### 4.4 多层膜与投影光学（Zeiss）

| 编号 | 权利人 | 要旨 | URL |
|---|---|---|---|
| **US7261957B2** | Zeiss | EUV 多层膜 + 铱等保护层 | https://patents.google.com/patent/US7261957B2/en |
| **US9915876B2** | Zeiss | EUV 多层膜周期分组设计 | https://patents.google.com/patent/US9915876B2/en |
| **US10048592B2** | Zeiss | High-NA **变形（anamorphic）** 投影物镜 | https://patents.google.com/patent/US10048592B2/en |
| **EP3257054B1** | Zeiss SMT | EUV 多层镜 + 光谱纯度滤波（减 UV 反射） | https://patents.google.com/patent/EP3257054B1/en |

### 4.5 工件台 / 掩模相关

| 编号 | 权利人 | 要旨 | URL |
|---|---|---|---|
| **US9172294B2** | ASML | 平面电机 | https://patents.google.com/patent/US9172294B2/en |
| **US6906789B2** | ASML Holding | 磁悬浮 REMA 刀口级定位 | https://patents.google.com/patent/US6906789B2/en |

### 4.6 Pellicle

| 编号 | 权利人 | 要旨 | URL |
|---|---|---|---|
| **US11567399B2** | ASML | EUV pellicle（金属氧硅化物 / Mo+Ru 等体系相关） | https://patents.google.com/patent/US11567399B2/en |
| **US11231646B2** | ASML | Pellicle 与 pellicle 组件（应力释放结构、框架、执行器等） | https://patents.google.com/patent/US11231646B2/en |

**本轮已核实专利合计：21 件**（覆盖液滴、激光、清洁、多层膜、High-NA 光学、台架、pellicle、TRUMPF 光源腔）。

---

## 5. 论文（Crossref / DOI 已核实）

> 下列 DOI 均经 Crossref API 返回确认。共 **25** 篇。

### 5.1 光源物理（ARCNL / Versolato 线）

| DOI | 题名（截断） | 作者 | 年 | 期刊 |
|---|---|---|---|---|
| [10.1088/1361-6595/ab3302](https://doi.org/10.1088/1361-6595/ab3302) | Physics of laser-driven tin plasma sources of EUV radiation for nanolithography | Versolato | 2019 | PSST |
| [10.1088/2040-8986/ac5a7e](https://doi.org/10.1088/2040-8986/ac5a7e) | Microdroplet-tin plasma sources… solid-state-lasers (Topical Review) | Versolato, Sheil, Witte | 2022 | J. Optics |
| [10.1103/PhysRevApplied.6.014018](https://doi.org/10.1103/PhysRevApplied.6.014018) | Plasma Propulsion of a Metallic Microdroplet… | Kurilovich et al. | 2016 | PR Applied |
| [10.1103/PhysRevApplied.10.054005](https://doi.org/10.1103/PhysRevApplied.10.054005) | Expansion Dynamics after Laser-Induced Cavitation… | Kurilovich et al. | 2018 | PR Applied |
| [10.1103/PhysRevApplied.12.014010](https://doi.org/10.1103/PhysRevApplied.12.014010) | Efficient Generation of Extreme Ultraviolet Light… | Schupp et al. | 2019 | PR Applied |
| [10.1038/s41467-020-15678-y](https://doi.org/10.1038/s41467-020-15678-y) | Prominent radiative contributions from multiply-excited states… | Torretti et al. | 2020 | Nat. Commun. |
| [10.1103/physrevresearch.4.013142](https://doi.org/10.1103/physrevresearch.4.013142) | Early-time hydrodynamic response of a tin droplet… | Hernandez-Rueda et al. | 2022 | PR Research |
| [10.1007/s00339-020-04207-9](https://doi.org/10.1007/s00339-020-04207-9) | Cylindrically and non-cylindrically symmetric expansion… | de Faria Pinto et al. | 2021 | Appl. Phys. A |
| [10.1088/1361-6501/ad1810](https://doi.org/10.1088/1361-6501/ad1810) | Characteristics of tin droplet target system… | Sun et al. | 2023 | Meas. Sci. Technol. |
| [10.1063/5.0189195](https://doi.org/10.1063/5.0189195) | Temporal pre-pulse shaping in dual pulse LPP… | Sizyuk et al. | 2024 | JAP |
| [10.1063/5.0200896](https://doi.org/10.1063/5.0200896) | Acceleration mechanisms of energetic ion debris… | Totorica et al. | 2024 | APL |

### 5.2 工业光源与系统展望

| DOI | 题名 | 作者 | 年 | 期刊 |
|---|---|---|---|---|
| [10.1515/aot-2017-0029](https://doi.org/10.1515/aot-2017-0029) | Light sources for HVM EUV lithography… | Fomenkov, Brandt, Ershov | 2017 | Adv. Opt. Tech. |
| [10.1515/aot-2017-0040](https://doi.org/10.1515/aot-2017-0040) | Next-generation lithography – outlook on EUV… | Schoot, Schift | 2017 | Adv. Opt. Tech. |
| [10.1145/3838602](https://doi.org/10.1145/3838602) | The ASML Monopoly: Platform and Ecosystem Leadership in EUV | Cusumano | 2026 | CACM |

### 5.3 High-NA

| DOI | 题名 | 作者 | 年 | 期刊 |
|---|---|---|---|---|
| [10.1117/12.2196393](https://doi.org/10.1117/12.2196393) | Anamorphic high-NA EUV lithography optics | Migura, Kneer, Neumann | 2015 | SPIE Proc. |
| [10.35848/1347-4065/ac49fa](https://doi.org/10.35848/1347-4065/ac49fa) | High-NA EUV lithography: current status and outlook | Levinson | 2022 | JJAP |
| [10.1117/1.jmm.24.1.010101](https://doi.org/10.1117/1.jmm.24.1.010101) | The Era of High-NA EUV Lithography Has Arrived! | Levinson | 2025 | JM3 |

### 5.4 多层膜 / 光学损伤

| DOI | 题名 | 作者 | 年 | 期刊 |
|---|---|---|---|---|
| [10.1364/oe.25.015441](https://doi.org/10.1364/oe.25.015441) | Interface morphology of Mo/Si multilayer… | Haase et al. | 2017 | Opt. Express |
| [10.1063/5.0035490](https://doi.org/10.1063/5.0035490) | Multi-shot damage on Mo/Si multilayer… | Li et al. | 2021 | AIP Advances |

### 5.5 Pellicle

| DOI | 题名 | 作者 | 年 | 期刊 |
|---|---|---|---|---|
| [10.1002/admi.202202489](https://doi.org/10.1002/admi.202202489) | Graphite Pellicle… Next-Generation EUV | Choi et al. | 2023 | Adv. Mater. Interfaces |
| [10.1088/1361-6528/ad902d](https://doi.org/10.1088/1361-6528/ad902d) | Metal silicide EUV pellicle for 400W… | Choi et al. | 2024 | Nanotechnology |
| [10.3390/membranes13010005](https://doi.org/10.3390/membranes13010005) | Degradation of EUV Transmittance of Pellicle | Wi et al. | 2022 | Membranes |

### 5.6 光刻胶 / 计量 / 随机效应

| DOI | 题名 | 作者 | 年 | 期刊 |
|---|---|---|---|---|
| [10.2494/photopolymer.32.21](https://doi.org/10.2494/photopolymer.32.21) | Sensitizer for EUV CAR: Metal versus Halogen | Jiang et al. | 2019 | J. Photopolym. Sci. Tech. |
| [10.35848/1347-4065/ac26e5](https://doi.org/10.35848/1347-4065/ac26e5) | Acid diffusion and resist molecular size vs LER | Koyama et al. | 2021 | JJAP |
| [10.1117/1.jmm.21.2.021207](https://doi.org/10.1117/1.jmm.21.2.021207) | CAR CDSEM metrology for high NA EUV | Severi et al. | 2022 | JM3 |

### 5.7 建议继续阅读（WORKFLOW 已标 ✅，本轮未再跑 Crossref）

- Bakshi, *Photon Source Technology for Lithography and Metrology*（SPIE eBook 2023）DOI 10.1117/3.2638242.ch1  
- arXiv:2602.03583 *Multi-Diagnostic Characterization of Laser-Produced Tin Plasmas…*

---

## 6. 官方与行业一手来源

### 6.1 ASML

| 页面 | 用途 | URL |
|---|---|---|
| EUV 产品总览 NXE/EXE | 波长、NA、分辨率、50k 滴/s、台精度 | https://www.asml.com/en/products/euv-lithography-systems |
| NXE:3800E 等子页 | 机型定位 | 自总览页链入 |
| EXE:5000 / 5200B | High-NA 机型 | 同上 |
| 投资者日 EUV 材料（示例） | 功率/产率讨论（引用前再核） | media.asml.com 投资者 PDF |
| YouTube 官方拆解动画 | 分镜与外壳造型参考（勿直接搬画面） | ASML 官方频道 |

### 6.2 ZEISS SMT

| 页面 | 用途 | URL |
|---|---|---|
| Semiconductor Manufacturing Technology | EUV 光学能力与宣传图 | https://www.zeiss.com/semiconductor-manufacturing-technology |

### 6.3 TRUMPF

| 页面 | 用途 | URL |
|---|---|---|
| EUV / Laser Amplifier 相关产品页 | CO₂ 驱动激光公开叙述（重频、功率档位引用前再核） | https://www.trumpf.com （站内搜 EUV / CO2 amplifier） |

### 6.4 其他权威入口

- SPIE Advanced Lithography 会议录（High-NA、光源、胶）  
- ARCNL 开放获取 PDF（Versolato 线）  
- Espacenet / Google Patents / USPTO  

---

## 7. 动画可用：公开可视 vs 保密

### 7.1 可以较准确建模（公开原理 + 专利示意级）

| 镜头 | 依据 | 注意 |
|---|---|---|
| 锡滴飞行 + 双脉冲打爆 + 等离子体发光 | ASML 公开叙述 + Versolato | 液滴直径、精确 CE 勿瞎编 |
| 椭球收集镜把光聚到 IF | 专利标准几何 | 膜层微观不必真画 40–60 对 Mo/Si，用材质暗示 |
| 真空腔切开、光路只有反射镜 | ASML | 镜片数量用「多面」示意 |
| 反射式掩模 + pellicle 挡尘 | ASML + pellicle 专利 | pellicle 膜极薄，用尺度夸张 |
| 投影缩小 / High-NA 变形示意 | ASML + Migura | 用 2D 示意图解释 anamorphic，避免假 CAD |
| 磁浮晶圆台高速步进扫描 | ASML 0.25 nm / 20 kHz | 加速度数字待核；可用生活化比喻但需审核 |
| 氢气氛清洗收集镜（示意气泡/辉光） | 清洁专利 | 勿声称看到真实腔体内部视频级还原 |

### 7.2 必须风格化 / 抽象（商业秘密或未公开）

- 喷嘴孔径、毛细管内部、精确液滴发生器几何与控制系统  
- 收集镜确切膜系、镀膜工艺与在线监测布局  
- 照明/投影镜片真实面形、装调公差、热控管路真实走向  
- 光源功率升级路线的内部参数、剂量控制算法  
- 客户工厂内的真实机台外观细节（外壳以官方宣传图为「神似」即可）  
- 光刻胶化学配方  

### 7.3 叙事建议（服务 5 分钟片）

1. **开场 20 s**：一滴锡 → 双脉冲 → 等离子体（视觉高潮）。  
2. **为何 13.5 nm**：波长与分辨率直觉。  
3. **光源段**：发生器 → 收集镜 → IF。  
4. **真空与多层膜**：解释「为什么不能用玻璃透镜」。  
5. **掩模与投影**：含 High-NA 一句彩蛋即可。  
6. **工件台**：纳米对准。  
7. **收束**：光子随机性 / 制造奇迹，留第二支幕后片钩子。

---

## 8. 缺口与下一步

| 缺口 | 建议动作 |
|---|---|
| 反射镜片数、单面反射率进旁白 | 查 ZEISS 技术白皮书 / SPIE 系统级 paper 后改「待核」为核实 |
| 500 W 级光源、overlay、产率 | 核对 ASML 最新投资者材料与产品说明书英文原句 |
| TRUMPF 激光精确 kW / Hz | 打开 TRUMPF 产品页原文摘录进 facts.yaml |
| Bakshi 2023 章节与 arXiv 2602.03583 | 全文阅读后补「关键句摘录」 |
| 中文专利（上微、高校） | CNIPA 检索作对比叙事，非主线 |
| 事实表机器可读化 | 从本文件抽出 `research/facts.yaml`（WORKFLOW 已规划） |

---

## 统计（本轮交付）

| 类别 | 数量 |
|---|---|
| 已核实专利 | **21** |
| 已核实论文（Crossref DOI） | **25** |
| 官方主页面（ASML/ZEISS/TRUMPF 入口） | **3+** 产品族页面，另含 ASML 投资者材料入口 |
| 可写进旁白的硬数字 | 见 §3.1（约 10 项） |
| 明确待核项 | 见 §3.2（10+ 项） |

**文件路径：** `/workspace/dreamforge-plan/RESEARCH.md`
