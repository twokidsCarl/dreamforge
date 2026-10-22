# E1 不在 git 里的素材（R2 清单）与云端接手步骤

这里只放清单、拉取命令和接手步骤，不放文件，也不写密钥。项目现状和待办见 `STATUS.md`，制作规范见 `docs/WORKFLOW.md`。

## 位置

- 存储：Cloudflare R2 私有桶 `eigenlens-file-transfer`，不开公开访问。
- 路径前缀：`episodes/E1-euv-lithography/`，和仓库里的路径一一对应。
- 上传时间：2026-10-23，从 Carl 的 Mac 上传，对应 git commit `d7593e8`。
- 校验：桶里共 267 个文件，199.6 MiB。逐目录做过 `rclone check --one-way`，结果都是 0 differences。桶里只有下表这些文件。

## 桶里有什么（只传了换机器后无法重新生成、或重新生成会改变成片的文件）

| 路径（相对 `episodes/E1-euv-lithography/`） | 文件数 | 内容 | 为什么必须有 |
|---|---|---|---|
| `audio/vo/Andre/` | 179 | 全片 160 句成品 wav（`sentences/`），以及 `sentences.json`、`timing.json`、整条配音轨 `vo_track.wav`、各段 wav、`asr_report.json` | 定时、剪辑和混音直接用。重新合成每次结果都不同，所有镜头时长会跟着变 |
| `audio/vo_cache/para/<段>_<key>.wav` 及 `.asr.txt` | 30 | 15 段在段落模式下最终选中的原始合成版 | `vo_align.py` 重新切句时要用 |
| `audio/eleven/` | 21 | ElevenLabs 生成的配乐和音效 | `edit_film.py` 混音直接读。重新生成要花额度，声音也会变 |
| `renders/shots/B1_15/sample/` | 36 | B1_15 的样片帧（已按最新代码渲好） | 2D 镜头 C_07 读取它的画面 |
| `renders/sample_b1/cycles/CamNozzle/0060.png` | 1 | 早期锡滴模拟的一帧 | 2D 镜头 `mograph/b1.py` 用它当背景 |

## 没有传、接手机器要自己生成的

| 内容 | 怎么得到 |
|---|---|
| 第三方素材 `shared/assets/`（Poly Haven 贴图和 HDRI、维基共享资源的芯片照片） | `python3 shared/tools/fetch_assets.py`（按 md5 校验） |
| 品牌片头片尾 `brand/eigenlens_logo_locked/sting_*.mp4` | 用该目录下的 `build.py` 生成；只剪审片版时，可以给 `edit_film.py` 加 `--no-brand` 跳过 |
| 全部 3D 样片（原机器上已渲好的 74 个镜头没传，约 5 GB；原机器渲了约 14 小时） | 重渲，见下面第 3 步 |
| 全部 2D 图形样片 | 重渲，CPU 就行，很快 |
| A0 的 1080p 终版镜头和 `renders/edit/A0_final_v1.mp4` | 只在原机器上。终版阶段重渲 |
| `audio/vo_cache/` 里其余落选的合成版本、试听样本 | 都是缓存，不需要 |

**不要重跑 `tts.py`。** 它重跑时会给每段的多个合成版逐一评分，桶里没有落选版，它就会重新请求合成，全片时长随之改变。只要旁白不改，就直接用桶里的成品。

## 云端接手步骤

### 1. 拉代码和素材

```bash
git clone https://github.com/twokidsCarl/eigenlens.git dreamforge && cd dreamforge
# 先配好 rclone 的 R2 remote，名字用 r2。密钥找 Carl 单独要，不进仓库，不打进日志
rclone copy r2:eigenlens-file-transfer/episodes/E1-euv-lithography episodes/E1-euv-lithography --transfers 16 --progress
rclone check r2:eigenlens-file-transfer/episodes/E1-euv-lithography episodes/E1-euv-lithography --one-way
python3 shared/tools/fetch_assets.py
```

`check` 只用来确认桶里的文件都拉下来了，显示 0 differences 就行。

### 2. 环境

- 软件：Blender 5.2、ffmpeg。Python 依赖 Pillow、PyYAML、numpy；Blender 用的 PyYAML 放在 `.blender_pylib/`；语音识别用 `.venv` 里的 faster-whisper（large-v3-turbo）。
- **GPU**：在 Linux 上必须设 `DREAMFORGE_CYCLES_DEVICE=OPTIX`（或 `CUDA`），否则 Cycles 默认走 CPU，见 `shared/blender/common.py`。
- **中文字体**：装 `fonts-noto-cjk`。`overlay_labels.py` 找不到 macOS 的黑体时，会自动改用 `/usr/share/fonts/opentype/noto/` 下的 Noto Sans CJK SC。
- 在 x86 上做语音识别要设 `DREAMFORGE_ASR_COMPUTE=float32`，int8 会识别出乱码。
- `sentences.json` 里的路径是原 Mac 上的绝对路径。`retime.wav_for` 发现文件不存在时，会按文件名到本机的 `audio/vo/Andre/sentences/` 下找，不用手改。

### 3. 渲染样片（sample，960×540）

云端机器上一个渲染都没有，所以 `STATUS.md` 第 4.1 节"只差 45 个"在这里不适用：**119 个 3D 镜头要全部渲**（B1_15 已经从桶里拉下来，可以跳过）。一次只跑一个 Blender 进程。

```bash
export DREAMFORGE_CYCLES_DEVICE=OPTIX
for s in $(.venv/bin/python -c "import yaml;print(' '.join(yaml.safe_load(open('episodes/E1-euv-lithography/blender/shots/registry.yaml')).keys()))"); do
  [ "$s" = B1_15 ] && continue
  blender -b --factory-startup -P shared/tools/render_storyboard.py -- --shot $s --quality sample
done
```

3D 全部渲完后，再渲 78 个 2D 镜头。以下两个有先后依赖：

- `C_07` 读取 B1_13、B1_15、C_04 的渲染，这三个渲完后再渲它。
- `A3_07` 渲之前，要先在 A3_06 新渲的最后一帧上重新量光源坐标 `SRC_XY`（`mograph/a3.py`）。

```bash
python3 shared/tools/mograph.py --shot <2D 镜头 id ...> --quality sample
```

2D 镜头 id 就是 `storyboard/storyboard.timed.yaml` 里有、但 `blender/shots/registry.yaml` 里没有的那些。

### 4. 之后

按 `STATUS.md` 第 4.2–4.5 节继续：剪全片 v2 样片并自审，复核 B4–B9、C、D，最后出 1080p 终版。
