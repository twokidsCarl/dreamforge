# E1 不在 git 里的素材（R2 清单）

只放清单和拉取命令，不放文件、不写密钥。背景见 `STATUS.md` 第 5 节。

## 位置

- 存储：Cloudflare R2 私有桶 `eigenlens-file-transfer`（不开公开访问）
- 路径前缀：`episodes/E1-euv-lithography/`，与仓库里的路径一一对应
- 上传：2026-10-23，来源机器 Carl 的 Mac（`/Users/adam429/Desktop/project-2026/dreamforge`），对应 git commit `d7593e8`

## 内容（只传了“必需”的配音素材）

| 路径（相对 `episodes/E1-euv-lithography/`） | 内容 | 用途 |
|---|---|---|
| `audio/vo/Andre/` | 全片 160 句的成品句子 wav、`sentences.json`、`timing.json`、整条配音轨 `vo_track.wav`、各段 wav、`asr_report.json` | 定时、剪辑和混音直接用；有了它就不用重配 |
| `audio/vo_cache/para/<段>_<key>.wav`（15 个，每段被选中的那一版）及其 `.asr.txt` | 段落模式下各段最终选中的原始合成版 | `vo_align.py` 重新切句时要用；文件名的 key 由 `tts.py` 按模型、音色、版本号和文本算出 |
| `audio/eleven/` | ElevenLabs 生成的配乐和音效 | `edit_film.py` 混音 |

合计 230 个文件，约 178 MiB。桶里还有一次中断上传留下的几十个 `audio/vo_cache/` 落选版本，不影响使用。

**没有传的**：
- `renders/`（约 26 GB）：样片和终版帧都没传，接手机器按 `STATUS.md` 第 4 节重渲。
  - A0 的 1080p 成片 `renders/edit/A0_final_v1.mp4` 也只在原机器上。
- `audio/vo_cache/` 里其余落选的合成版本（约 700 MB）：只是缓存。
  - 注意：`tts.py` 重跑时，选版是按缓存里 1–10 版逐一评分，缺了落选版就会重新请求合成；只要不改旁白，就不要重跑 `tts.py`，直接用上面的成品。

## 接手机器拉取

```bash
# 先在本机配好 rclone 的 R2 remote（名字用 r2；密钥找 Carl 要，不进仓库）
rclone copy r2:eigenlens-file-transfer/episodes/E1-euv-lithography/audio episodes/E1-euv-lithography/audio --transfers 16 --progress
rclone check episodes/E1-euv-lithography/audio r2:eigenlens-file-transfer/episodes/E1-euv-lithography/audio --one-way
```

## 提醒

- Linux 上要把 `shared/tools/overlay_labels.py` 的字体从 macOS 的 STHeiti 换成 Noto Sans CJK SC（改 `FONT` / `FONT_INDEX`）。
- 做语音识别时设 `DREAMFORGE_ASR_COMPUTE=float32`（x86 上 int8 会出乱码）。
- 不要重新合成配音：TTS 每次结果不同，会打乱所有镜头的时长。
