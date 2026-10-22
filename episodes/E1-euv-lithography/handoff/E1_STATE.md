# E1《一台光刻机里发生了什么》现状盘点（接手：视频制作-Vivian，2026-10-23 01:40 北京时间）

依据：`origin/main` @ `49b67d4`（#42，ASSETS.md 与桶对齐），`STATUS.md`（2026-10-22 23:00 交接），`docs/WORKFLOW.md`，本期全部目录；R2 桶实查；box 上 `build_check.py` 冒烟。本文件只写看到的事实，判断和缺口见 `E1_GAP_ANALYSIS.md`。

## 1. 一句话

剧本、配音、分镜、事实库、15 段画面核查和全部场景代码都已就绪，**但云端（box）上一帧 3D 样片都还没有**：119 个 3D 镜头、78 个 2D 镜头都要渲；全片 v2 样片还没剪过；B4–B9、C、D 的画面修复还没对照新画面复核；声音设计只做了 A0。

## 2. 各部分现状

| 部分 | 现状 | 证据 |
|---|---|---|
| 剧本 `script/script_zh.md` | 第四稿定稿，15 段 160 句，每句标事实编号；`lint_script.py` 无 ERROR / WARN；B8/B9 的审核改句（8 倍、NXE 推力、几十个对准标记、188 场、1000 W）已在剧本里 | lint 输出：160 句 3753 字，纯旁白 15.0 分钟 |
| 事实库 `research/facts.yaml` | 71 条：A 级 54、B 级 15；F55（C 级，三星 EUV 层数）未进旁白，F15c 已 rejected | `yaml` 实读 |
| 配音（Qwen3-TTS，Andre，段落模式） | 160 句全部在；`vo_track.wav` 1191.3 s（19.9 分钟）；`asr_report.json` 中 5 句 ratio < 0.9，都是同音或近音（锡滴→CD、掩模→眼眸、晶圆→氢圆），没有漏句 | R2 拉下后实测 |
| 分镜 `storyboard/storyboard.timed.yaml` | 196 镜，总长 1190.3 s（设计 1307 s）；每镜都有 style、style_why、sfx 描述 | `yaml` 实读 |
| 画面语言分布 | energy 43、photoreal 40、infographic 30、xray 18、sem 18、clay 11、blueprint 11、type 10、hud 8、documentary 7 | 同上 |
| 3D 镜头 `blender/shots/registry.yaml` | 119 条（Cycles 49 条约 6,700 帧，EEVEE 70 条约 9,900 帧，按 24 fps 和定时时长计） | 同上 |
| 2D 镜头 `mograph/*.py` | 78 个（timed 里有、registry 里没有的镜头） | `build_check` 覆盖报告 |
| 画面核查 `research/visual/audit_*.yaml` | 15 段全审过。A0–A3、B1–B3、B5、D 做过一轮复核；**B4、B6、B7、B8、B9、C 的 `verified` 全为 0**，status 里仍有 `wrong` 共 86 条（B4 16、B6 16、B7 13、B8 23、B9 4、C 14）、`unsourced` 9 条、C 段 8 条无 status。按 `fixes_*.md`，代码大多已改，但没对照新画面确认 | `yaml` 实读 |
| 声音设计 `sound/*.yaml` | **只有 `a0.yaml`**（1 条配乐 + 16 条音效）。R2 上 `audio/eleven/` 共 2 首配乐、19 条音效，基本只够 A0 | 目录与桶实查 |
| 字幕 `subs/zh.srt` | 已按定时生成 | 文件在 |
| 品牌 | `brand/eigenlens_logo_locked/` 有 `endcard_16x9.png`、`build.py`；`sting_open.mp4`/`sting_end.mp4` 不入库，box 上目前没有，要跑 `build.py` 生成。end card 只有标志和「EigenLens / 主观知识」，**没有 eigenlens.ai** | 目录实查 |
| 已有成片 | A0 的 1080p `A0_final_v1.mp4` 和原机器上 74 个 3D 样片只在 Carl 的 Mac 上，没传。box 上只有 B1_15 的 36 帧样片和 `sample_b1/.../0060.png` 一帧 | ASSETS.md、桶实查 |
| 最近一次工作 | 2026-10-22：A1–A3、B2/B3 复核修复（`4a8f5d2`）、Cycles 样片预设 32 spp、合并 E2 共享改动、写 STATUS/ASSETS 并把必需素材传 R2（#41、#42） | `git log origin/main` |

## 3. 画质现状（凭现有两份帧的观感，不是正式打分）

- B1_15（等离子体爆闪旁的镜面）：碎屑粒子和辉光干净，但底色灰紫、偏平，等离子体是一团柔光球，看不出结构；属于「专业但普通」。
- `CamNozzle/0060`（喷嘴与锡滴）：景深、反射质感不错，接近产品渲染。
- 整片样片 box 上没有，**全片画质无法评估**。STATUS 自己点名的短板：A0_03 货机是哑光白模、偏玩具；标签字体缺上下标字形。

## 4. R2 素材核对（2026-10-23 01:15 北京时间）

- remote `r2`（provider Cloudflare，endpoint 为 Carl 指定的账户），配置在仓库外的 `~/.config/rclone/rclone.conf`，不含密钥；密钥只经 `~/bin/rclone-r2` 从环境变量 `R2_ACCESS_KEY_ID` / `R2_SECRET_ACCESS_KEY` 传入，不落盘、不进日志。
- 桶 `eigenlens-file-transfer/episodes/E1-euv-lithography/`：**267 个文件，199.617 MiB**，与 ASSETS.md 一致。
- 已全部拉到本工作树（`audio/`、`renders/` 已被 `.gitignore` 排除），`rclone check --one-way`：**0 differences，267 matching**。
- 分目录：`audio/vo/Andre/` 179、`audio/vo_cache/para/` 30、`audio/eleven/` 21、`renders/shots/B1_15/sample/` 36、`renders/sample_b1/cycles/CamNozzle/0060.png` 1。缺失：无。

## 5. box 环境（不装重东西，只查）

| 项 | 现状 |
|---|---|
| Blender | 5.2.2 LTS（`~/.local/bin/blender`），与 WORKFLOW 要求一致 |
| GPU | **box 没有 GPU**（无 nvidia-smi，Cycles 报 CUEW 初始化失败）。Cycles 只能走 CPU（8 核），EEVEE 需要 GPU；样片和终版都要开 RunPod |
| ffmpeg | 7.1.5 |
| Python | 系统 python3 有 Pillow 12.3、PyYAML、numpy；Blender 用的 PyYAML 已从 `/workspace/dreamforge/.blender_pylib` 复制到工作树 |
| 中文字体 | `fonts-noto-cjk` 已装（`/usr/share/fonts/opentype/noto/NotoSansCJK-*.ttc`），`overlay_labels.py` 会自动回落；Outfit 已装 |
| `shared/assets/` | 用 `/workspace/dreamforge/shared/assets`（Poly Haven，6.1 MB）软链；终版前应跑一次 `fetch_assets.py` 校验 md5 |
| ASR `.venv`（faster-whisper large-v3-turbo） | **box 上没有**，自审第 3 步要先建（模型约 1.6 GB，CPU，免费），并设 `DREAMFORGE_ASR_COMPUTE=float32` |
| 密钥 | `/workspace/dreamforge/.env` 里有 DASHSCOPE、ELEVENLABS；没有 Tripo/Meshy |
| rclone | v1.75.2 装在 `~/bin/` |

### build_check 冒烟（不渲染，CPU）

- 119 条中 **117 条 OK**。
- `A2_08`（能量风格的波带）FAIL：「相机视野里没有可见物体」。可能是检查对单个长网格的误报，也可能相机真的对空，要渲 1 帧确认。
- `A0_04` FAIL：registry 里还有这条，但 timed.yaml 里已没有这个镜头（并进了 A0_03）。是孤儿条目，应删掉。
- `A0_03`（物流全景）OK，但光搭场景就要 167 s、50 万三角面，是全片最重的场景。
- 78 个 2D 镜头被报为「缺 registry」，这是覆盖检查把 2D 也算进去了；本身不是错，但会让 `build_check` 退出码一直是 1，CI 式使用前要改。
- 日志：`/tmp/e1_buildcheck_all.log`、`/tmp/e1_bc_a003.log`（box 本地）。

## 6. 文档里只适用于 Mac 的地方

STATUS 4.1 的渲染命令用 `/Applications/Blender.app/...`；「只差 45 个」只对 Carl 的 Mac 成立，云端是 119 个全渲（ASSETS 第 3 步已说明）。
