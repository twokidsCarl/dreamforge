# 芯片：ZEISS“1840 亿元件”核实、裸片照片是否 EUV 制造、裸片彩虹色的物理

调研日期：2026-10-19。所有引文均为原文照录；“推断”和“估算”都会单独标出。没有下载任何图片：Commons 信息来自 API（`prop=imageinfo&iiprop=url|extmetadata|size`），没有逐张目视检查。

---

## A. ZEISS “184 billion components”

### A1. 现行措辞（2026-10-19 抓取）

**英文页面** https://www.zeiss.com/semiconductor-manufacturing-technology/inspiring-technology/euv-lithography.html （小节“The light of the future”）：

> "In 1970, there was room for about 1,000 transistors on a microchip. Today there are 184 billion (semiconductor) components on an area only slightly larger than a fingertip."

紧接着的一句：

> "Microchips show structures 5,000 times finer than a human hair and are produced with light of the extremely short wavelength of 13.5 nanometers."

**德文页面** https://www.zeiss.de/semiconductor-manufacturing-technology/inspiring-technology/euv-lithographie.html ：

> "1970 haben auf einem Mikrochip etwa 1.000 Transistoren Platz gefunden. Heute sind es 184 Milliarden (Halbleiter-)Bauelemente auf einer Fläche, nur etwas größer als eine Fingerkuppe."

**繁体中文页面**（hreflang zh / zh-tw）https://www.zeiss.com.tw/semiconductor-manufacturing-technology/inspiring-technology/euv.html ：

> "1970 年時一枚晶片僅能容納約 1,000 個電晶體，如今面積僅略大於指尖的晶片上已能容納 1,840 億個（半導體）元件。"

要点：
- 用词是 **components / Bauelemente / 元件**，不是 transistors。1970 年那句说的是 transistors，但 184 billion 那句没有。
- 原文是“**略大于**指尖”（slightly larger than / etwas größer als / 略大於），不是“指尖大小”。
- **三种语言都没有点名任何具体芯片。**
- 我们的 F19 措辞“比指尖略大的面积上有 1840 亿个元件”与原文相符。

### A2. 改动历史（Wayback Machine）

我拉取了这一页的 CDX 快照列表，并解析了以下快照：

| 快照 | 数字 |
|---|---|
| 20220810115329 | "today there are 57 billion (semiconductor) components on an area only slightly larger than a fingertip"（当时 1970 那句和这句用分号连成一句） |
| 20230402031758、20231210112531、20240419063449、20241012134031、20251012200639、20260214202759、20260319045220、20260608144042 | "Today there are 57 billion (semiconductor) components …" |
| 20260801065137、20260819152358、20260825030650、20260827172118、20260910123606 | "Today there are 184 billion (semiconductor) components …" |

可以核对的链接示例：
- 改动前：https://web.archive.org/web/20260608144042/https://www.zeiss.com/semiconductor-manufacturing-technology/inspiring-technology/euv-lithography.html
- 改动后：https://web.archive.org/web/20260801065137/https://www.zeiss.com/semiconductor-manufacturing-technology/inspiring-technology/euv-lithography.html

结论：数字在 **2026-06-08 到 2026-08-01 之间**由 570 亿改为 1840 亿。ZEISS 别处还在用旧数字，例如 2025-04-01 的新闻稿“30 Years of EUV”（https://www.zeiss.com/semiconductor-manufacturing-technology/news-and-events/smt-press-releases/2025/euv-30-years.html）写的是：

> "The result: Thanks to EUV, more than 57 billion transistors fit on the fingernail-sized silicon area of a microchip."

（这份新闻稿用的是 *transistors* 和 *fingernail*。）

### A3. 指的是哪颗芯片？ZEISS 没说（不公开）

**推断（非 ZEISS 原文，置信度中）**：这两个数字恰好等于 Apple 公布的晶体管数。
- 570 亿 = Apple M1 Max（2021-10，TSMC 5 nm）。Apple 新闻稿原文这次没有抓到，只有二手报道，如 eeNews Europe：https://www.eenewseurope.com/en/apple-m1-max-boasts-57-billion-transistors-on-a-5nm-process/
- 1840 亿 = Apple M3 Ultra（2025-03）。Apple 新闻室：https://www.apple.com/newsroom/2025/03/apple-reveals-m3-ultra-taking-apple-silicon-to-a-new-extreme/ ，大意是 UltraFusion 合计带来 1840 亿个晶体管。M3 Ultra 由**两颗 M3 Max 裸片**经 UltraFusion 连接而成。

如果这个推断成立，“略大于指尖”和实际面积对不上：两颗大裸片拼在一起，面积远大于指尖。所以 ZEISS 这句话应当作 **ZEISS 的表述**引用，不能当作某颗芯片的实测参数。
- 旁白建议保留“1840 亿个元件”并标明出自 ZEISS，**不要**说成“一颗芯片 / 1840 亿个晶体管”。
- 画面上**不要**配某颗具体芯片的照片来暗示就是“这一颗”。

置信度：措辞与 URL 为 A（亲自抓取的原文）；改动时间窗为 A（Wayback）；“指的是 M3 Ultra”为推断，C。

---

## B. 裸片照片是否用到了 EUV

### B0. 节点与 EUV 的一手依据

- **TSMC N7（初代）不用 EUV。** TSMC 2019-10-07 新闻稿 https://pr.tsmc.com/english/news/2010 的标题是 "TSMC's N7+ Technology is First EUV Process Delivering Customer Products to Market in High Volume"，正文称 N7+ 为 "the industry's first commercially available Extreme Ultraviolet (EUV) lithography technology"。TSMC 技术页 https://www.tsmc.com/english/dedicatedFoundry/technology/platform_HPC_tech_advancedTech 写道："The N7+ node was TSMC's first EUV process to enter volume production." WikiChip N7 页（https://en.wikichip.org/wiki/N7 ，二手）："For N7, TSMC continued to use deep ultraviolet (DUV) 193 nm ArF Immersion lithography."
- **TSMC N6 用 EUV。** 同一份新闻稿："With further application of EUV, N6 will offer 18% higher logic density over N7"。技术页："The 6nm (N6) technology utilizes additional EUV layers …"。层数方面，AnandTech（二手）给出 N7+ 最多 4 层、N6 最多 5 层。
- **TSMC N5 家族（N5/N4/N4P/N4X）用 EUV。** 技术页："Extreme ultra-violet (EUV) lithography makes N5 mask layers and process complexity more manageable."，以及 "The 4nm (N4) technology is an enhanced version of 5nm (N5) technology"，以及 "To further enhance the N5 family's performance and power, TSMC introduced N4P and N4X"。层数方面，IEEE Spectrum 转述 TSMC 的说法是 N5 有超过 10 层 EUV（二手）。
- **TSMC N3（N3B/N3E）用 EUV**：所有资料都这么写，但这次**没有拿到 TSMC 原文明确写 N3 + EUV 的句子**（技术页的 N3 段没提 EUV）。置信度高但属于二手。
- **Intel 14 nm 不用 EUV；Intel 4 是 Intel 第一个 EUV 节点。** Intel 新闻室 https://newsroom.intel.com/manufacturing/new-fab-ireland-high-volume-production-intel-4-technology 说 Intel 4 "uses extreme ultraviolet (EUV) technology"。AnandTech https://www.anandtech.com/show/17448 ："it's the first Intel process to incorporate EUV"。RealWorldTech https://www.realworldtech.com/intel-4/5 说 EUV 在 10 nm 时期（约 2017）还没准备好量产，Intel 改用多重曝光。14 nm 早于 10 nm，因此不用 EUV（置信度 A−）。
- **注意：即使是“EUV 节点”，也只有部分层用 EUV，其余仍是 DUV 浸没式。** 旁白若说“每一个元件都由这台 EUV 机器的光画出”，严格说是夸大。比较稳的说法是“这些芯片最关键的几层图形是用 EUV 光刻的”。
  - TSMC 说 N5 的 EUV 用于 cut、contact、via、metal line（IEEE Spectrum 转述）。由此**推断**每个晶体管都至少有一个 EUV 图形化的特征（接触孔/通孔），但没有找到明确的原文。

### B1. 我们现有的三张照片

| # | Commons 文件 | 尺寸 | 许可（页面原文） | 节点 | 用 EUV？ | 说明 |
|---|---|---|---|---|---|---|
| 1 | File:Intel@14nm@Skylake@Skylake-SP(XCC)@Xeon(ES)@QJW5 DSCx8 poly@20x - Flickr - FritzchensFritz.jpg | 16309×12435 | CC0 / "Creative Commons Zero, Public Domain Dedication" | Intel 14 nm | **否（纯 DUV）** | 描述："Xeon ES QJW5 (Skylake-SP \| XCC) (Polysilicon \| 20x \| Brightfield NIC Lambda) (4,644mm x 3,535mm (16,417mm²) …) Just one core and a high resolution stitch of them"。只拍了**一个核心**，不是整颗裸片；颜色来自 Nomarski DIC 加 λ 波片，**不是衍射**（见 C4） |
| 2 | File:AMD@7nm@Zen2 RDNA APU@Oberon@PlayStation5@CXD90060GG 100-000000189 WM33440U00089 S DSCx6 poly@50xDICL - Flickr - FritzchensFritz.jpg | 28561×14778 | CC0 | TSMC N7（初代 Oberon） | **否（DUV）** | 描述："(Polysilicon \| 50x \| Brightfield NIC Lambda) (3,246 x 1,679 [5,45mm²] …) Image showing up the PS5 Zen2 core area with L2 and L3 Cache"。只是**核心区局部**，颜色同样来自 DIC λ 波片。另外几张 PS5 Oberon 照片（DSC09299、DSC09310、ZS-retouched-3、DSCx2@IR）拍摄于 2021-02，也是 CXD90060GG，都是 N7 |
| 3 | File:AMD@4nmCCD(6nmIOD)@Zen5@Granite Ridge@Ryzen 5 9600X@100-000001405 BY 2429SUY 9AEQ579S40073 DSCx12 CCD topmetal@50xBF.jpg | **2448×1624** | CC0 | TSMC 4 nm（N4P） | **是** | 描述："(Top-Metal \| 50x Brightfield)"。50 倍**局部**、分辨率低、明场。画面是顶层厚金属，不是 EUV 图形化的那些层 |

**PS5 Oberon 的节点：**
- 初代 Oberon 是 TSMC N7。2022 年的 CFI-1202 改版换成 N6 的 “Oberon Plus”（Angstronomics：https://www.angstronomics.com/p/ps5-refresh-oberon-plus ；大意：AMD 半定制团队把 PS5 芯片移植到 TSMC N6，代号 Oberon Plus，设计不变；裸片约 300 mm² → 小于 260 mm²）。
- Sony 和 AMD 从未官方公布过节点，这一点**不公开**，只有 Angstronomics 等基于裸片分析的报道（置信度 B）。
- 我们用的照片都标 CXD90060GG，拍摄于 2021，早于 Oberon Plus（2022-09），所以是 **N7 = 不含 EUV**（置信度 A−）。happytrees.org 的 CXD90060GG 条目记录裸片约 298.4 mm²，与初代 Oberon 一致。

**AMD 官方节点**（amd.com 产品规格页，"Processor Technology for CPU Cores"）：
- Ryzen 5 9600X："TSMC 4nm FinFET"；Ryzen 5 7600："TSMC 5nm FinFET"；两者 I/O Die 都是 "TSMC 6nm FinFET"。
- 页面：https://www.amd.com/en/products/processors/desktops/ryzen/9000-series/amd-ryzen-5-9600x.html 、https://www.amd.com/en/products/processors/desktops/ryzen/7000-series/amd-ryzen-5-7600.html
- AMD 产品页没有写 “N4P”。N4P 来自 Hardwareluxx/PCGH 转述 AMD（另有 N4X 的说法），但 N4P 和 N4X 都属 N5 家族、都用 EUV，结论不受影响。

**结论：#1、#2 不是 EUV 芯片，配在“每个元件都由 EUV 的光画出”下面是错的，应换掉。#3 是 EUV 芯片，但应换成同一颗芯片的 5x 整片图（见 B2）。**

### B2. 推荐替换：明确用 EUV 制造的 CC0 整片裸片照片（全部 Fritzchens Fritz，CC0）

所有文件的 API `LicenseShortName` 都是 "CC0"，`UsageTerms` 都是 "Creative Commons Zero, Public Domain Dedication"，作者署名为 FritzchensFritz / Fritzchens Fritz。CC0 不要求署名，但片尾保留“芯片显微照片：Fritzchens Fritz（CC0）”是好做法。

文件名里的约定（根据 Fritzchens 的命名和描述字段归纳）：
- **poly**：剥掉金属层，露出多晶硅/晶体管层，功能块最清楚。
- **topmetal**：顶层金属，主要是厚的电源网格。
- **5xExt**：5 倍物镜，外部光源。
- **5xBF**：明场。
- **BF POL / BFPOL**：明场加偏振。
- **SWIR / IR**：红外透过硅背面拍摄。

这里的“光照”只根据文件名和描述判断，**没有看过画面**，见 E 节。

**首选（整片、功能块清楚、外部光源）**

1. **Intel Lunar Lake（Core Ultra 200V，288V）计算 tile + 平台控制器 tile**
   - 节点：计算 tile TSMC N3B，平台控制器 tile TSMC N6，两者都用 EUV。
   - 来源：AnandTech https://www.anandtech.com/show/21425/intel-lunar-lake-architecture-deep-dive-lion-cove-xe2-and-npu4 （"The entire compute tile … is built on TSMC's N3B node, while the SoC tile is made using the TSMC N6 node."）。
   - Intel 数据手册 829568-004 第 17 页原文是 "built on Intel 4 process and N3B technology"，与上面的说法有出入，但无论哪种说法都是 EUV 节点。
   - 文件：
     - `File:Intel@TSMC N3 N6@LunarLake@LNL(4P+4LPE)@CoreUltra200Series@DSCx01 poly@5xExt.jpg`，11928×12147。https://commons.wikimedia.org/wiki/File:Intel@TSMC_N3_N6@LunarLake@LNL(4P%2B4LPE)@CoreUltra200Series@DSCx01_poly@5xExt.jpg
     - `…@DSCx03 poly@5xExt.jpg`，11928×12147，同组的另一种光照。
     - `…@DSCx04 poly@5xExt.jpg`、`…@DSCx06 poly@5xExt.jpg`，14576×11352，22060 dpi，更高倍。
     - `…@DSCx02 poly@5xBFPOL.jpg`、`…@DSCx05 poly@5xBFPOL.jpg`，明场加偏振，对照用。
   - 描述："Poly | 5x External Light | 11030 dpi … Compute Tile 16.289mm x 8.579mm … Plattform Controller Tile 3.954mm x 11.520mm …"。两颗 tile 都是整片。
   - 另有相机宏观照 `…@DSC04600-DSC04785.jpg`，9500×5057，描述 "(Lunar Lake | Compute Tile)"。

2. **Intel Arrow Lake-S（Core Ultra 9 285K）各 tile**
   - 节点：计算 tile N3B，GPU tile N5P，SoC 与 IO tile N6，都是 EUV 节点。
   - 来源：The Register https://www.theregister.com/2024/10/10/intel_arrow_lake_deep_dive 给出计算 N3B、GPU N5P；SoC/IO 的 N6 只有二手来源（TechPowerUp 论坛转述 HighYield）。
   - 底座 tile 据报道是 Intel 22 nm（DUV），照片若带底座，那部分不是 EUV。
   - 文件：
     - `File:Intel@TSMC N3 N5 N6@ArrowLake-S@ARL(8P+16E)@CoreUltra200S@DSCx01 poly@5xExt.jpg`，19756×16524。https://commons.wikimedia.org/wiki/File:Intel@TSMC_N3_N5_N6@ArrowLake-S@ARL(8P%2B16E)@CoreUltra200S@DSCx01_poly@5xExt.jpg
     - `…@DSCx02 poly@5xExt2.jpg`，19756×16524，第二种外部光照。
     - `…@DSCx04 poly@5xExt.jpg`、`…@DSCx05 poly@5xExt2.jpg`，22357×10198，22060 dpi。
     - `…@DSCx03 poly@5xBF.jpg`、`…@DSCx06 poly@5xBF.jpg`，明场。
   - 描述列出了 SoC 86.6 mm²、IO 24.5 mm²、Graphic 23.0 mm²、Compute 117.2 mm²（含划片道），都是整片。

3. **AMD Zen 5 CCD（Ryzen 5 9600X），TSMC 4 nm**，与现有 #3 是同一颗芯片的整片版
   - `File:AMD@4nmCCD(6nmIOD)@Zen5@Granite Ridge@Ryzen 5 9600X@100-000001405 BY 2429SUY 9AEQ579S40073 DSCx14 CCD poly@5xExt.jpg`，7849×6737。https://commons.wikimedia.org/wiki/File:AMD@4nmCCD(6nmIOD)@Zen5@Granite_Ridge@Ryzen_5_9600X@100-000001405_BY_2429SUY_9AEQ579S40073_DSCx14_CCD_poly@5xExt.jpg
     - 描述："(Poly | 5x External Light | 22060 dpi) CCD: 9.037mm x 7.743mm = 69.973mm² (with scribe lines) …"，整颗 CCD。
   - `…DSCx15 CCD poly@5xBF.jpg`，7858×6737，明场。
   - `…DSCx11 CCD topmetal@5xBF.jpg`，7826×6710，整颗 CCD 的顶层金属，明场。
   - 相机宏观照：`…DSC01985.jpg`（9440×6236）、`…DSC02499-DSC02769.jpg`（9504×6336）、`…DSC02822-DSC03132.jpg`（9402×5289），描述都只写 "AMD Ryzen 5 9600X (Zen 5 | Granite Ridge | CCD)"，光照未知。

4. **AMD Zen 4 CCD（Ryzen 5 7600），TSMC 5 nm**
   - `File:AMD@5nmCCD(6nmIOD)@Zen4@Raphael@Ryzen 5 7600@100-000001015 BQ 2246SUY 9LS4795W20142 DSCx13 CCD poly@5xExt.jpg`，8998×5828。https://commons.wikimedia.org/wiki/File:AMD@5nmCCD(6nmIOD)@Zen4@Raphael@Ryzen_5_7600@100-000001015_BQ_2246SUY_9LS4795W20142_DSCx13_CCD_poly@5xExt.jpg
     - 描述："(Polysilicon | 5x | External Lighsource) (10.369 x 6.702 [69.49mm²] | 22060dpi)"。
   - `…DSCx14 CCD poly@5xBF.jpg`，9010×5818，明场。
   - `…DSCx09 CCD topmetal@5xBF.jpg`，9010×5820，顶层金属，明场。
   - `…DSCx15 CCD poly@80xBF+Pol.jpg`，42990×20313，80 倍核心加 L2 局部，适合推近镜头。
   - 宏观照：`…DSC04178-DSC04306.jpg`（5763×4000）、`…DSC02685-DSC02786.jpg`（5652×3790），描述 "AMD Ryzen 7600 & 7800X3D (Zen 4 | Raphael)"，光照未知。

**查过但不推荐**
- NVIDIA AD102（RTX 4090，TSMC 4N）：Commons 上只有封装可见光照（DSCx1@VIS、DSCx3@VIS）、红外背面照和一张堆栈照，**没有正面整片显微图**。4N 用 EUV 也只有二手来源（4N 属 N5 衍生）。
- NVIDIA H100（Geekerwan）：CC BY 3.0，作者 "极客湾Geekerwan"，3840×2160，内容是**显卡产品照，不是裸片**。
- Apple A14+/M1+、Samsung 7LPP/5LPE、Intel Meteor Lake 计算 tile（Intel 4）：Commons 上**没有找到**自由许可的裸片照片（"Meteor Lake.png" 只是 148×287 的示意图）。

---

## C. 裸片的彩虹色到底是什么

### C1. 机理（有来源）

- **周期结构就是反射光栅。** 晶圆检测专利 US5970168A（KLA-Tencor，1997-08-05 提交，https://patents.google.com/patent/US5970168A/en ）写道："the array serves as a reflective diffraction grating that produces diffraction spots"。它说的阵列是 "an array of memory cells, where the repeating pattern has a period of several microns"，周期典型值 2–20 µm。这是 1990 年代的存储阵列，现代单元要小得多。
- **光栅方程**：d(sin α + sin β) = mλ（Wikipedia "Diffraction grating"；Newport/MKS 光栅手册）。
- **衍射级是否存在**：Newport https://www.newport.com/n/diffraction-orders ："The grating equation reveals that only those spectral orders for which |mλ/d| < 2 can exist"，以及 "Specular reflection, for which m = 0, is always possible"。Wikipedia："When groove spacing is less than half the wavelength of light, the only present order is the m = 0 order."（即“亚波长光栅”）
- **另外两个产生颜色的机理（非衍射）**：一是多层介质薄膜干涉（层间 SiO₂/low-k 厚度不同，颜色随厚度和角度变化）；二是材料本身的反射率。EEVblog 论坛 T3sl4co1l 2020-07-13 的帖子把颜色归为掺杂、薄膜干涉、周期图案衍射三类，并提到存储阵列和总线显衍射、随机逻辑显斑驳。这只是论坛来源，权威性低，仅作佐证。

### C2. 颜色怎样随角度变化（由光栅方程推出）

- 光源和栅距 d 固定时，第 m 级在观察角 β 处出射的波长是 λ = d(sin α + sin β)/m。观察者或光源一动，β 或 α 变了，同一块区域的颜色就沿光谱扫过，相当于“彩虹在芯片上流动”。
- d 越大，存在的级次越多（"For λ/d << 1, a large number of diffracted orders will exist"，Newport），各级颜色交叠，颜色变淡、偏白。d 只比 λ/2 略大时，只在掠射角才出现一级，而且最先出现的是紫/蓝。
- 光栅只在垂直于线条的方向上色散。旋转裸片（方位角）时，线条方向不同的功能块会轮流亮起或变暗。这是标准光学结论（锥面衍射），这次没有单独找文献引用。

### C3. 哪些结构能把可见光衍射出来

可见光 λ ≈ 380–750 nm。要出现任何非零级，需要 d > λ/2，即紫光 d > ~190 nm、红光 d > ~375 nm，而且只在掠入射、掠出射时成立。正入射且在法线附近观察时，大约需要 d > λ。

EUV 印出来的关键层周期：
- TSMC N3E："a 48-nanometer poly pitch, a 26-nanometer fin pitch, along with a minimum metal pitch of 23 nanometers"。N3B 的 CPP 是 45 nm。来源：WikiChip Fuse https://fuse.wikichip.org/news/7375/tsmc-n3-and-challenges-ahead/ 。
- Intel 4："the fins and M0 are 30nm pitch … the contacted gate and M1 are all 50nm pitch"（RealWorldTech https://www.realworldtech.com/intel-4/3 ；VLSI 2022 论文摘要也是 50 nm 栅距、30 nm 鳍距、30 nm 最小金属间距）。
- TSMC N5 的高密度 SRAM 单元面积 0.021 µm²（IEDM 2019，G. Yeap et al.，经 Cadence/Semiconductor Digest/WikiChip 转述）。N3E 的 SRAM 单元与 N5 相同（WikiChip）。
- 结论：**鳍、栅、M0/M1 这些 23–50 nm 的周期远小于 λ/2，对可见光只有零级（镜面反射），不会产生彩虹。** 它们可能通过等效介质效应、形式双折射改变反射率和偏振。这一点是推断：Fritzchens 用偏振（POL）拍摄能提高对比度，与此相符，但没有找到专门文献。

真正衍射出彩虹的，是更粗的周期（估算，没有找到逐项文献值）：
- 一组组重复排列的单元形成的超周期。例如 SRAM 单元通常镜像排列，实际周期是两个单元。0.021 µm² 的单元边长约 0.1–0.2 µm，镜像后周期约 0.2–0.4 µm，已能在斜射下衍射蓝紫光（估算）。
- 标准单元行：N3E HP 单元高 169 nm（WikiChip），镜像成对后约 340 nm（估算）。
- 中上层金属和顶层厚金属（电源网格）。TSMC N5/N3 顶层厚金属的间距**不公开**；Intel 4 有两层厚顶层金属，但具体数值只在图片表格里，这次没有核实。
- 大块阵列、SRAM bank、去耦电容阵列等的宏观重复（微米到几十微米）。

**对片子的含义：**
1. 彩虹色本身**不是** EUV 图形的直接显影。它来自由这些（部分 EUV 印制的）单元拼成的更大周期，以及上层金属。
2. 我们着色器里每块区域的“栅距”如果想要可见色散，应取约 0.3–2 µm 量级（估算）。真实的 23–50 nm 栅距画不出彩虹。
3. 裸芯片通常还盖着顶层厚金属和钝化层，肉眼看到的彩虹主要来自顶层金属和阵列区，随机逻辑区偏灰、斑驳。

### C4. Fritzchens 照片里的颜色不全是衍射

- 文件名带 "NIC Lambda" 或 "DICL" 的（我们现用的 #1、#2），是 Nomarski 微分干涉（DIC）加全波（λ）补偿片拍的。
- Olympus/FSU Microscopy Primer（https://micro.magnet.fsu.edu/primer/java/dic/opticalstaining/index.html 等）说明：全波片在约 550 nm 处加一个波长的延迟，背景呈品红，颜色反映的是表面高度和光程梯度，**是显微镜光学造出的假彩色，不是芯片自己的衍射色**。Olympus 的 "DIC Microscopy of Computer Chip Surfaces" 教程也写到 IC 拍摄时光路里有延迟片，旋转起偏器会改变颜色。
- "BF"（明场）照片基本是金属白、氧化物彩色薄膜干涉色。
- "Ext"（外部光源）的照片最可能带斜射衍射色，但**没有目视确认**。

---

## D. 给剪辑的结论

- 撤下 Intel 14 nm Skylake-SP 和 PS5 Oberon（N7）在“EUV 画出”旁白下的镜头。可以改放到“DUV 时代”段落，标注 14 nm / 7 nm DUV。
- EUV 段首选 Lunar Lake `DSCx01 poly@5xExt`（N3B + N6，两颗 tile 都是 EUV 节点），或 Zen 5 CCD `DSCx14 CCD poly@5xExt`（TSMC 4 nm）。推近用 Zen 4 `DSCx15 CCD poly@80xBF+Pol`（42990 px 宽）。
- ZEISS 数字照原文说“1840 亿个（半导体）元件，面积略大于指尖”，标明出自 ZEISS，不配某颗具体芯片。

---

## E. 不公开 / 不确定清单

1. ZEISS 的“1840 亿”指哪颗芯片：**ZEISS 未说明**。与 Apple M3 Ultra（两颗裸片）的晶体管数相同只是推断；若确是它，“略大于指尖”的面积说法与实物不符。
2. PS5 Oberon 的工艺节点：**Sony/AMD 未官方公布**。N7 和 Oberon Plus = N6 来自 Angstronomics 等裸片分析。我们照片上的 CXD90060GG 拍摄于 2021，是初代芯片。
3. Zen 5 CCD 是 N4P 还是 N4X：AMD 产品页只写 "TSMC 4nm FinFET"。两者都用 EUV，不影响结论。
4. Lunar Lake 平台控制器 tile 的节点：AnandTech 和新闻稿说 N6，Intel 数据手册写 "Intel 4 process and N3B technology"，互相矛盾。两种说法都是 EUV 节点。Arrow Lake SoC/IO 的 N6 只有二手来源，底座 tile（据报道 Intel 22 nm）不是 EUV。
5. TSMC N3 用 EUV 的说法这次没有拿到 TSMC 原文，属二手但普遍确认。NVIDIA 4N 用 EUV 也只有二手来源。
6. 每个节点的 EUV 具体层数及位置：TSMC/Intel **不完整公开**（只有“最多 4/5 层”“超过 10 层”等转述）。“每个晶体管都含 EUV 图形化特征”是推断。
7. TSMC N5/N3 顶层厚金属间距：**不公开**。Intel 4 的厚金属间距在 RealWorldTech/WikiChip 的图片表格里，未核实。
8. C3 中 SRAM 镜像周期、标准单元行对的约 0.2–0.4 µm 是**估算**。
9. 候选图片的实际光照效果（是否有彩虹衍射色）：**未目视检查**（按要求没有下载，浏览器扩展也未连接），只根据文件名里的 Ext/BF/POL/DIC 推断。定稿前需要人工看一眼 Commons 预览图。
