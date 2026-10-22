# E2 v8 阶段 A：视觉标准与样张（代码与提示词）

- 标准：[../docs/VISUAL_BIBLE_v8.md](../docs/VISUAL_BIBLE_v8.md)；全片逐镜方案：[../docs/SHOT_REDESIGN_v8.md](../docs/SHOT_REDESIGN_v8.md)
- 大文件不进 git，都在本机 `/workspace/e2work/v8/`：`refs/`（47 张参考帧）、`gen/`（image2 底图）、`tripo/`（glb）、`renders/`、`styleframes/`（样张、动态和对照表 `SHEET_v7_ref_v8.jpg`）、`review/`（独立审稿）
- `tools/gen.py`：gpt-image-2，经 Token99 用 curl 调用，每次调用记账到 `costs_image2.jsonl`。key 从 `~/.config/token99.env` 读，不入库
- `tools/tripo.py`：Tripo 建任务、轮询、下载
- `tools/sf.py`：2D 合成基础库（浮点相机、超采样文字、引线标注、统一 grade）。`tools/sf_scenes.py` 是 SF01–SF11 各镜；`tools/render_sf.py` 出静帧和 24 fps 动态；`tools/cmp_sheet.py` 出对照表
- `blender/mouse_v2.py`：Tripo 绑骨小鼠，含 GN 毛发、骨骼挂载的植入件和光纤、木屑垫料。`mouse_scene.py` 是静态版（第一轮）
- `prompts/`：image2 提示词前缀 CORE、G，以及各张底图的完整提示词
