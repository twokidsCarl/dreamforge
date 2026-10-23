# E1 花费台账（E1 单独预算：总额 $60，单日上限 $25；Carl 2026-10-23 批）

时间均为北京时间。GPU 按 RunPod 返回的 costPerHr × 开机到 Terminate 的时长计；网络卷 `eigenlens-cache` 与 E2 共用，月费记在 E2 账上。

| 日期 | 项 | 资源 | 时长 | 金额 (USD) | 用途 | Terminate 确认 |
|---|---|---|---|---|---|---|
| 2026-10-23 | P1 第 1 轮风格帧（18 个 3D 镜头 × 3 帧，sample） | RunPod A40 Secure `li78fx244uzcxo`（CA-MTL-1 + 卷 eigenlens-cache），$0.59/h | 01:47:31–01:51:55，4.4 min | 0.04 | 一次 3 个 Blender 进程；54 帧全部拉回 | 是（DELETE 204，GET /pods = []） |
| 2026-10-23 | 审美校准选图包 v1 mock-up（6 张，medium，1536×1024） | image2（gpt-image-2） | 02:13–02:17 | 0.23 | 按返回 usage 估算；明细 `/workspace/e1work/calib/costs_image2.jsonl` | 不适用（无 GPU） |
| 2026-10-23 | P1 第 2 轮纪实底板（3 张：A0_02 夜间货机、A0_03 铝框箱 + 货机 + 卡车、D_07 冷白洁净室；high，1536×1024） | image2（gpt-image-2） | 约 09:20 | 0.11 | 按返回 usage 估算；明细 `/workspace/e1work/p1/plates/costs_image2_r2.jsonl`，提示词 `p1/plates/` | 不适用（无 GPU） |
| 2026-10-23 | P1 第 2 轮风格帧（24 镜 × 3 帧，960×540 Cycles 32 spp） | RunPod A40 Secure `o3yiwzo8jqpi1m`（CA-MTL-1 + 卷 eigenlens-cache），$0.59/h | 09:34:29–09:38:58，4.5 min | 0.04 | 一次 4 个 Blender 进程；72 帧拉回（B7_06 因脚本 KeyError 在 box CPU 上补渲 3 帧，$0） | 是（DELETE 204，GET /pods = []，事后再查仍为 []） |
| 2026-10-23 | P1 第 3 轮风格帧（24 镜 × 3 帧，960×540 Cycles 32 spp） | RunPod A40 Secure `d5c1rs0bhpbp9l`（CA-MTL-1 + 卷 eigenlens-cache），$0.59/h | 10:20:02–10:32:47，12.75 min（其中同步仓库与 renders 约 8 min） | 0.13 | 一次 4 个 Blender 进程；72 帧全部拉回，24 镜 rc=0 | 是（DELETE 204，GET /pods = []，事后 curl 复查仍为 []） |
| 2026-10-23 | P1 第 4 轮风格帧（24 镜 × 3 帧，960×540 Cycles 32 spp） | RunPod A40 Secure ×3：`xzbt778szav910`（11:03:46–11:08:45，4.97 min，$0.05）、`trl4wj7lthoixr`（11:09:06–11:18:50，9.72 min，$0.10）两次同步仓库时 tar-over-ssh 管道中断（rc 255）即 Terminate；`d373yo6an51gwd`（11:19:48–11:29:40，9.86 min，$0.10）改为分块同步 + 重试后成功 | 24.55 min | 0.24 | 一次 4 个 Blender 进程；72 帧（B1_15 36 帧）全部拉回，24 镜 rc=0 | 是（三台均 DELETE 204 + TERMINATED_CONFIRMED，事后 curl GET /pods = []） |

**累计：$0.79 / $60；今日（10-23）：$0.79 / $25**。GPU $0.45，image2 $0.34，Wan $0。本轮（P1 第 4 轮）：GPU $0.24（上限 $2，其中 $0.15 是两次同步失败的空转）、image2 $0（未使用，上限 $3）。
