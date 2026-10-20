# A0 冷开场：画面调研

只覆盖 A0 画面里会出现的结构和文字。旁白里的数字和论断在 `research/facts.yaml`，这里只记画面。

## 1. 引文纸页（A0_01a、A0_02b）

- 引文出处：F3。2026 诺奖科学背景（nobelprize.org，advanced-medicineprize2026.pdf）把「理想的信号是光」「相当牵强（rather far-fetched）」归于 Crick 1999（Phil Trans R Soc Lond B）。可信度 A。
- **画面不能冒充原件。** 我们没有 Crick 1999 的版面或手稿图片（Phil Trans 全文 PDF 403，见 `verification.md`）。所以纸页上只有不可读的抽象行，不排英文原句，也不排中文。中文那句只在下一镜（A0_01b）作排版出现，是旁白的译文。
- 上屏年份只用 **1999**（检查点①决定 1）。不出现 1979（F3b 未核实），不出现「47 年」。
- 未公开 / 没核实：Crick 写下这句话时的环境、纸张、字体。全部是氛围示意。

## 2. 「只动一类细胞」（A0_03a、A0_03b）

- 要求本身来自 F3：只打开或关掉某一类神经元，其余大体不动，而且要快。
- 神经元画成通用的胞体 + 树突 + 一根轴突。不对应任何具体脑区或细胞类型，不标数量和比例。
- 「打开」用通道蓝，「关掉」用抑制琥珀（全片色彩约定，见 `storyboard/page.yaml`）。这只是颜色编码，不是真实的光色说明。

## 3. 诺奖三人（A0_04a、A0_04b、A0_05a）

- F1：2026-10-05，诺贝尔生理学或医学奖授予 Karl Deisseroth、Peter Hegemann、Georg Nagel；理由是光控离子通道与光遗传学。来源：nobelprize.org 2026 新闻稿。A 级。
- 名字只写这三个，顺序按新闻稿；不画肖像（WORKFLOW 1.3：人物只做剪影或抽象）。
- 不写奖金，不写「Boyden」（A0 里不涉及，第二幕再分清名单）。

## 4. 紫膜一闪（A0_91）

- 紫膜的二维晶格：细菌视紫红质三聚体排成六方晶格（空间群 P3，晶胞边长约 62 Å），三聚体之间和中间由脂质填充；每个蛋白有 7 段大致垂直于膜面的 α 螺旋。
  - Henderson R, Unwin PNT. Three-dimensional model of purple membrane obtained by electron microscopy. *Nature* 257:28–32 (1975). https://doi.org/10.1038/257028a0 （摘要：7 段 α 螺旋，脂双层填充蛋白之间。）B 级。
  - Krebs MP, Isenbarger TA. Structural determinants of purple membrane assembly. *BBA Bioenergetics* 1460:15–26 (2000). https://www.sciencedirect.com/science/article/pii/S0005272800001262 第 3 节：「arranged in trimeric units that pack in a hexagonal lattice (space group P3 with a unit cell dimension of ∼62 Å)… Lipid molecules are located between trimers and in the space enclosed by each trimer」。B 级。
- 1971 年 Oesterhelt 与 Stoeckenius 的紫膜见 F4。A0 这一镜**不标年份**（分镜要求），1.5 秒一闪，作第二幕的伏笔。
- 画法：灰度「电镜风格」的晶格起伏，带一点紫色调。真实的电镜结果是投影密度图，不是这种带光影的表面，所以记为 `simplified`。

## 5. 1999 → 2026（A0_92）

- HUD 计数从 1999 走到 2026 后停住。两端分别是 F3（Crick 1999，诺奖科学背景引用）和 F1（2026-10-05 授奖）。不出现 1979。
- 不在屏幕上写两者相差多少年。

## 6. 片名（A0_06a、A0_06b）

- 片名《光遗传学》。optogenetics 一词出自 F7（2006，Deisseroth 等）；A0 片名镜头不写年份。

## 未公开 / 不画

- Crick 原稿的样子。
- 三位得主的长相（项目规则也不允许写实人脸）。
- 真实神经元放电时的颜色：神经元不发光，蓝 / 琥珀是约定配色。
