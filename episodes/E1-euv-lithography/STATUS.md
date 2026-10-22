# E1《一台光刻机里发生了什么》现状与交接（2026-10-22 23:00）

给接手的 agent：先读 `docs/WORKFLOW.md`（制作规范，权威），再读本文件。本文件只记“做到哪了、还差什么、怎么接着做”。

## 1. 一句话现状

剧本、配音、分镜、事实库和全部场景代码都已按四轮画面审核和两轮复核改完并提交。卡在**渲染**：样片（sample，960×540）还有 45 个 3D 镜头没按最新代码重渲，然后要剪全片 v2 样片、按真实时长看片、修问题，最后出 1080p 终版。

## 2. 已完成

| 部分 | 状态 |
|---|---|
| 剧本 `script/script_zh.md` | 定稿；B4/B6/B7/B8/B9/C 的旁白按审核改过并已重配 |
| 配音（Qwen3-TTS，音色 Andre，段落模式） | 全片 160 句已合成、对齐、定时，19.8 分钟；`asr_check` 160 句中 8 句低于 0.9（多为同音字，可接受） |
| 分镜 `storyboard/parts/*.yaml` → `storyboard.timed.yaml` | 已合并、定时；`storyboard_check.py` 无 ERROR |
| 事实库 `research/facts.yaml` | F1–F65，全部有一手出处；本轮新增 F62（激光在辅助层）、F63（最大镜子约 1 m）、F64（半场与狭缝尺寸）、F65（合作伙伴） |
| 画面审核 `research/visual/audit_<段>.yaml` | 全部 15 段都审过；修复记录在 `research/visual/fixes_*.md`，复核记录在 `verify_A1-B1.md`、`verify_B2-D.md` |
| 2D 图形（mograph） | 全部按最新代码重渲到 sample |
| 3D 镜头 | 82 个已按最新代码渲到 sample，45 个还没有（见第 4 节） |
| A0 开场 1080p 终版 | `renders/edit/A0_final_v1.mp4` 已出；之后 A0_05 已按新光路重渲 final，A0_01 的等离子体核时序改了一帧，final 需重渲（Cycles，约 2.5 小时） |

## 3. 本轮的关键修正（避免回退）

- **EUV 镜子不画彩虹**：`materials.multilayer_mirror()` 已是素净金属镜面（13.5 nm 的 Mo/Si 周期在可见光下不出干涉色）。掩模、pellicle 同理。
- **整机光路**（`build_machine.PATH`）：M5 的反射点在镜环上（`M5_HIT`），不在中心孔里；收集镜是带中心孔的凹面壳。
- **NXE/EXE 不混用**：High-NA 扫描方向缩小 8 倍（掩模比晶圆快 8 倍）、每片 188 个半场、>185 片/小时；1 万牛推力和“砸车”是 NXE 一代；旁白不说 EXE 的镜片数。
- **驱动激光在楼下辅助层**（B1_25 两层剖面），光束经转向镜穿过华夫板楼板（F62）。
- **照明系统**：可转动的是场分面镜（弧形长条），圆环/两极出现在光瞳分面镜（圆形小镜）上（B5）。
- **锡滴发生器**按公开比例：4 μm 孔、3 μm 射流、约 100 颗 5.8 μm 小液滴合成 1 颗 27 μm 锡滴（B1_04/05，`b1_jet.py`）。
- **工具修复**：`tts.py --segments X` 局部运行时保留其他段（以前会冲掉全片的配音索引）；单版下载失败跳过、不再中断；`edit_film.py` 新增 3D 镜头的章节卡、标签 `at:` 定时、`kind: page` 插页（B1_20 教科书页）；`mograph.Canvas.text` 用 alpha 蒙版画字（Pillow 12 下淡入淡出不再跳变），并设 26 px 最小字号。
- **风格**：xray / energy 风格里的 `rays` 光束强制饱和紫、限制强度（以前发白）；合成器色散 0.004（以前细光束有红蓝边）。

## 4. 待办（按顺序）

### 4.1 重渲样片（sample）——还没渲的 45 个 3D 镜头
```
C_02 C_03 C_04 C_05 C_06 C_08 C_09 C_10
B1_02 B1_03 B1_04 B1_05 B1_08 B1_10 B1_11 B1_13 B1_14 B1_19 B1_20 B1_24
B2_01 B2_02 B2_04 B2_05 B2_06 B2_07 B2_08 B2_09 B2_11
B3_01 B3_05 B3_06 B3_07  B5_01 B5_09  D_08
A1_02 A1_03 A1_04 A1_06 A1_07 A1_09  A3_04 A3_05 A3_06
```
然后：A3_07（2D）要在 A3_06 新渲的最后一帧上重新量光源坐标 `SRC_XY`（`mograph/a3.py`）再重渲；C_07 读取 B1_13、B1_15、C_04 的现有渲染，这三个渲完后再渲 C_07。

命令（一次只跑一个 Blender 进程，两个同时跑会互抢 GPU、总速度反而更慢；本机 sample Cycles 约 8 s/帧、EEVEE 约 1.5–3 s/帧）：
```
/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P shared/tools/render_storyboard.py -- --shot C_02 --quality sample
python3 shared/tools/mograph.py --shot A3_07 --quality sample
```

### 4.2 剪全片 v2 样片并看片
```
python3 shared/tools/edit_film.py --segments A0,A1,A2,A3,B1,B2,B3,B4,B5,B6,B7,B8,B9,C,D --quality sample,preview --size 1280x720 --out full_v2
```
按 WORKFLOW 第 5 节自审：每 0.5 s 抽帧拼接触表逐张看、`review_asr.py` 听写检查每句旁白、响度 -16 LUFS。

### 4.3 复核
B4–B9、C、D 的修复还没有做“对照新画面逐条复核”（A1–A3、B1、B2、B3、B5、D 做过一轮，B2/B3 的复核问题已修但没再复核）。复核要更新 `audit_<段>.yaml` 每条的 `status` 和 `verified`：段里还有 wrong/unsourced 的，不能进终版。

### 4.4 已知未做 / 有意简化
- A2_07：分镜里“短波笔尖画出一条更细的线”的结尾没画。
- A3_05：分镜写的横甩切换、胶片颗粒、漏光没做，实际是硬切（建议改分镜文字）。
- B2_08：分镜里的 EUV 闪光和 H₂ 劈开没做（改分镜或补做，见 `fixes_B2-B3.md`）。
- B1_10/C_02：预脉冲后薄饼只沿激光方向漂移，没有沿锡滴方向的下游运动（audit 记为 simplified；改 `sample_b1.py` 会影响 A0_01、B1、B2、B3、C_02、D 的共用模拟）。
- 标签字体缺上下标字形（Sn⁸⁺、H₂、SnH₄ 被压平），`edit_film.label_for` 把它们转成普通数字。
- A0_03 的货机是哑光白模，偏玩具感（风格化，可再打磨）。

### 4.5 终版
全部段复核通过后，按 1080p `--quality final` 渲染（Cycles final 256 spp，A0 已出），再 `edit_film.py --quality final --size 1920x1080`。

## 5. 换机器接手要注意

- **渲染和配音文件不在 git 里**（`.gitignore`：`episodes/*/renders/` 26 GB，`episodes/*/audio/` 1 GB）。
  - 没有 `audio/` 就要重新合成全片配音，TTS 每次的版本是随机的，时长会变，所有镜头时长要重排、已渲画面的长度会对不上。**强烈建议从原机器拷贝 `episodes/E1-euv-lithography/audio/`**（至少 `audio/vo/Andre/` 132 MB 和 `audio/vo_cache/para/`），以及需要的 `renders/shots/`。
  - 第三方素材 `shared/assets/` 用 `shared/tools/fetch_assets.py` 重新下载。
- **密钥**：仓库根目录 `.env`（不入库，chmod 600）里放 `DASHSCOPE_API_KEY`、`ELEVENLABS_API_KEY`。不要在日志、回复或网页请求里打印密钥。
- **字体**：`shared/tools/overlay_labels.py` 写死了 macOS 的 `/System/Library/Fonts/STHeiti Medium.ttc`。Linux 上要换成同等的中文黑体（例如 Noto Sans CJK SC）并改 `FONT`/`FONT_INDEX`，否则所有 2D 图形和字幕会报错或变样。
- **软件**：Blender 5.2；Python 依赖 Pillow、PyYAML、numpy；ASR 用 `.venv` 里的 faster-whisper（large-v3-turbo，CPU）；Blender 的 PyYAML 放在 `.blender_pylib/`。
- **规则**：人物只用逆光剪影（`shared/blender/figures.py`）；不仿制 ASML 外观、航司/工厂标志；网页请求里不放任何个人信息（需要联系人时用 research@example.com）；每个阶段提交一次，提交信息末尾加署名行。
- **共享文件**：`shared/tools/tts.py`、`vo_align.py` 本地和远端（E2 的工作）都改过，合并时以两边功能都保留为准。
