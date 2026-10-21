# E2 声音设计状态（P9）

| 段 | 状态 | 配乐 | 音效 | 预听 |
|---|---|---|---|---|
| A0 | **v3 已生成，待审听**（2026-10-21） | composition_plan，`music/4d4c6b60fb70c3bd.mp3` | 14 条（新增 3 条） | `renders/edit/A0_sample_v3_sound.mp4` |
| A–D | 未开始；动态分镜用 `temp_music.yaml` 的临时配乐 | — | — | — |

路径都相对 `episodes/E2-optogenetics/`；`audio/`、`renders/` 不入库，在 box 的主 checkout（`/workspace/dreamforge/episodes/E2-optogenetics/`）里。

## A0 v3

复现（在仓库根目录）：

```bash
export DREAMFORGE_EPISODE=E2-optogenetics
.venv/bin/python shared/tools/sound_gen.py A0 --dry-run     # 哪些请求已缓存、哪些要花钱
.venv/bin/python shared/tools/sound_gen.py A0               # 生成缺的（已缓存的不再请求）
.venv/bin/python shared/tools/sound_gen.py A0 --check       # 每条音效落在空档还是压词、源峰值、配乐响度
.venv/bin/python shared/tools/edit_film.py --segments A0 --quality sample --size 960x540 --tail 3.5 --out A0_sample_v3_sound
```

这一轮花费：ElevenLabs 4 次请求（配乐 1 条 62.6 s，新音效 3 条）。其余 11 条音效沿用缓存。

改了什么（相对 A0_sample_v2）：

- **配乐**：从 prompt 生成改为 composition_plan，6 段（quote / method / prize / missing / title / decay）的时长对准旁白段落边界；片名「光遗传学」（53.7 s）落在 title 段的和弦解决上，decay 段只剩长音，衰减落进 3.5 s 尾巴。3.4 s 进（「光」字之后）。增益 -15 dB：120 Hz 高通后 -30.1 LUFS，和 v2 持平。
- **新增 3 条冲击音效，全部放在旁白空档里**：A0_03b 放电（21.77 s，空档 21.17–23.32）、A0_04b 名单落定（38.68 s，空档 38.13–40.28）、A0_06a 片名落定的低频（54.95 s，「学」54.84 说完之后）。
- **压在词上的提示音降到 -24 dB**：打字、开 / 关、三个光点。它们和已渲染的画面动作同步，没法挪到空档；yaml 里每条写了 `over_vo` 理由，`--check` 会列出来。
- A0_05b「光熄灭」源文件很轻（峰值 -31 dBFS），-18 dB 下几乎听不见；在空档里，增益提到 -6。
- `edit_film.py`：loudnorm 真峰值目标 -1.5 → -2.0。AAC 编码会多出约 0.2 dB，v3 第一次出片 mp4 真峰值是 -1.3 dBTP（在旁白爆破音上），改后 -1.9。

自审：

| 项 | 结果 |
|---|---|
| 配乐无人声 | demucs 人声轨比其余低 60.9 dB，没有超阈值的 1 秒窗口；Whisper 单听配乐转写为空 |
| 关键词不被盖住 | 混音转写和纯旁白转写（`review_words.py`，同一模型）逐字对照，没有丢字或换字。差异只有识别噪声：英文名 Hegemann、Nagel 两边都识别错；混音里「遗传」「拨动」反而识别对了 |
| 冲击放在空档 | `sound_gen.py A0 --check` 通过：冲击 7 条都在空档里；压词的 7 条都有 `over_vo` 理由，增益都不高于 -24 dB（底噪 -20） |
| 响度 | -16.5 LUFS，真峰值 -1.9 dBTP，LRA 6.0 LU（v2：-16.9 / -1.5 / 6.6） |
| 源文件削波 | 无（最高 -1.3 dBFS，配乐） |

还没做 / 待审：

- **要人耳审听**：配乐和段落是否合拍、A0_05b 提到 -6 后是否合适、片名低频是否太重。
- 画面没变（仍是 sample 960×540）。1080p 成片要等 final 渲染（P8）。
- 旁白本身的两个读音问题（不是 P9）：识别结果里「只让」都成了「只要」、「一句」成了「一具」，纯旁白也一样。是否要重录由 P4 决定。
