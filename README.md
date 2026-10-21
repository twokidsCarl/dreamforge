# EigenLens

用 AI 控制 Blender 做 3D 建模与科普解说视频。一个系列，多期视频。中文名是**主观知识**。

## 品牌

公开品牌于 2026-10-21 由 Carl 锁定。GitHub 仓库和项目文件夹都是 `eigenlens`（原名 dreamforge）。正文里的英文名写 **EigenLens**。

| 项 | 锁定 |
|---|---|
| 中文主名 | 主观知识 |
| 英文主名 | EigenLens（正文用驼峰；仓库 slug 是 `eigenlens`） |
| 片头与片尾 | 每集片头 2–4 秒 sting，片尾 end card。不用 MetaHuman，也不用数字人主持人 |
| 标语含义 | 选主轴，看结构。主观是编辑上的选择；「主」取主轴，对应 eigen |
| 画面 | 暗色 HUD，冷青 / 冷紫，与 E2 A0 一致 |

标志还没有定稿。Rena 的 v1 方向是草稿，等 Carl 选定。仓库里没有 `brand/eigenlens_logo_v1/`。

工具仍读旧环境变量，前缀是 `DREAMFORGE_`（例如 `DREAMFORGE_EPISODE`）。这次只记录品牌，不改这些名字。说明见 [docs/WORKFLOW.md](docs/WORKFLOW.md)。

| 期 | 文件夹 | 状态 |
|---|---|---|
| E1《一台光刻机里发生了什么》（约 20 分钟） | `episodes/E1-euv-lithography/` | 制作中 |
| E2《光遗传学》（目标 12–15 分钟） | `episodes/E2-optogenetics/` | 检查点①②已通过；P7 建模完成（126 镜登记，67 个 3D 镜头 build 通过）；下一步 P8 第一批试渲，等 Carl 开 GPU，见 [FIRST_BATCH.md](episodes/E2-optogenetics/FIRST_BATCH.md) |

- 所有期共用的工具与 Blender 模块：`shared/`
- 制作流程与目录约定：[docs/WORKFLOW.md](docs/WORKFLOW.md)
- 拉取请求审查与自动合并：[docs/REVIEW.md](docs/REVIEW.md)
- GPU 渲染开卡（Carl 自开 RunPod）：[docs/RUNPOD.md](docs/RUNPOD.md)
- 当前期由 `shared/tools/paths.py` 决定，默认 E1；切换：`DREAMFORGE_EPISODE=E2-optogenetics`

常用命令（在仓库根目录运行）：
```
python3 shared/tools/lint_script.py                 # 剧本与事实库校验
python3 shared/tools/review_pr.py                   # 审查当前分支；--pr N 时通过后打开自动合并
python3 shared/tools/storyboard_check.py            # 合并并校验分镜
python3 shared/tools/tts.py --voice Andre           # 整段合成配音
.venv/bin/python shared/tools/vo_align.py           # 语音识别对齐切句
python3 shared/tools/retime.py                      # 按配音重排分镜、生成字幕
shared/tools/render_batch.sh preview B1_02 B1_03    # 渲染镜头
python3 shared/tools/mograph.py --shot B1_27        # 二维动画镜头
python3 shared/tools/story_reel.py                  # 故事板动态预览
```
