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
| 2026-10-23 | P1 第 5 轮风格帧（24 镜 × 3 帧，960×540 Cycles 32 spp） | RunPod A40 Secure `kt3vcifud3rb2t`（CA-MTL-1 + 卷 eigenlens-cache），$0.59/h | 12:06:19–12:10:42，4.37 min（分块同步一次成功） | 0.04 | 一次 4 个 Blender 进程；72 帧（B1_15 36 帧）全部拉回，24 镜 rc=0；另：NASA Blue Marble / 云图贴图（公有领域）免费下载 | 是（DELETE 204 + TERMINATED_CONFIRMED，事后 curl GET /pods = []） |
| 2026-10-23 | P1 第 6 轮风格帧（24 镜 × 3 帧，960×540 Cycles 32 spp） | RunPod A40 Secure `xj3ikaz1vgx4cn`（CA-MTL-1 + 卷 eigenlens-cache），$0.59/h | 12:45:07–12:48:57，3.82 min（分块同步一次成功） | 0.04 | 一次 4 个 Blender 进程；72 帧（B1_15 36 帧）全部拉回，24 镜 rc=0；本地 CPU 预览 $0 | 是（DELETE 204 + TERMINATED_CONFIRMED，事后 curl GET /pods = []） |
| 2026-10-23 | P1 第 7 轮首次尝试（上一会话中断） | RunPod A40 Secure `wnft7drbkh6yiw`（CA-MTL-1），$0.59/h | 13:39:23 起；会话中断，RunPod 账单计 122 s（2.04 min） | 0.02 | 帧来源无法确认，未采用，全部重渲 | 是（13:58、14:10 curl GET /pods = []） |
| 2026-10-23 | P1 第 7 轮风格帧（24 镜 × 3 帧，960×540 Cycles 32 spp） | RunPod A40 Secure `oi60q939uq79ty`（CA-MTL-1 + 卷 eigenlens-cache），$0.59/h | 13:59:02–14:03:06，4.07 min（分块同步一次成功） | 0.04 | 一次 4 个 Blender 进程；72 帧（B1_15 36 帧）全部拉回，24 镜 rc=0；本地 CPU 冒烟 6 镜 $0 | 是（DELETE 204 + TERMINATED_CONFIRMED，14:10 curl GET /pods = []） |
| 2026-10-23 | P1 第 8 轮风格帧（24 镜 × 3 帧，960×540 Cycles 32 spp） | RunPod A40 Secure `9vb893nzeotrii`（CA-MTL-1 + 卷 eigenlens-cache），$0.59/h | 15:08:04–15:18:07，10.04 min（分块同步一次成功；新零件库让 C_03 等镜渲染变慢） | 0.10 | 一次 4 个 Blender 进程；72 帧（B1_15 36 帧）全部拉回，24 镜 rc=0；本地 CPU 冒烟 20 镜 $0 | 是（DELETE 204 + TERMINATED_CONFIRMED 15:18:07，事后 curl GET /pods = []） |
| 2026-10-23 | P1 第 9 轮风格帧（24 镜 × 3 帧，960×540 Cycles 32 spp） | RunPod A40 Secure `6itxc34wc9pl4h`（CA-MTL-1 + 卷 eigenlens-cache），$0.59/h | 17:14:31–17:18:01，3.49 min（分块同步一次成功；场景构建改为逐顶点建网格，C_03 构建从约 4 min 降到 3 s） | 0.03 | 一次 4 个 Blender 进程；72 帧（B1_15 36 帧）全部拉回，24 镜 rc=0；本地 CPU 冒烟 24 镜 $0 | 是（DELETE 204 + TERMINATED_CONFIRMED 17:18:01，事后 curl GET /pods = []） |

**累计：$1.06 / $60；今日（10-23）：$1.06 / $25**。GPU $0.72，image2 $0.34，Wan $0。本轮（P1 第 9 轮）：GPU $0.03（上限 $2）、image2 $0（未使用）。
