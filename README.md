# dreamforge

用 AI 控制 Blender 做 3D 建模与科普解说视频。一个系列，多期视频。

| 期 | 文件夹 | 状态 |
|---|---|---|
| E1《一台光刻机里发生了什么》（约 20 分钟） | `episodes/E1-euv-lithography/` | 制作中 |
| E2《光遗传学》（目标 12–15 分钟） | `episodes/E2-optogenetics/` | 检查点①：剧本和分镜总览等审 |

- 所有期共用的工具与 Blender 模块：`shared/`
- 制作流程与目录约定：[docs/WORKFLOW.md](docs/WORKFLOW.md)
- 拉取请求审查与自动合并：[docs/REVIEW.md](docs/REVIEW.md)
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
