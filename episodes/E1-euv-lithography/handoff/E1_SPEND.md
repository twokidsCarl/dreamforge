# E1 花费台账（E1 单独预算：总额 $60，单日上限 $25；Carl 2026-10-23 批）

时间均为北京时间。GPU 按 RunPod 返回的 costPerHr × 开机到 Terminate 的时长计；网络卷 `eigenlens-cache` 与 E2 共用，月费记在 E2 账上。

| 日期 | 项 | 资源 | 时长 | 金额 (USD) | 用途 | Terminate 确认 |
|---|---|---|---|---|---|---|
| 2026-10-23 | P1 第 1 轮风格帧（18 个 3D 镜头 × 3 帧，sample） | RunPod A40 Secure `li78fx244uzcxo`（CA-MTL-1 + 卷 eigenlens-cache），$0.59/h | 01:47:31–01:51:55，4.4 min | 0.04 | 一次 3 个 Blender 进程；54 帧全部拉回 | 是（DELETE 204，GET /pods = []） |
| 2026-10-23 | 审美校准选图包 v1 mock-up（6 张，medium，1536×1024） | image2（gpt-image-2） | 02:13–02:17 | 0.23 | 按返回 usage 估算；明细 `/workspace/e1work/calib/costs_image2.jsonl` | 不适用（无 GPU） |

**累计：$0.27 / $60；今日（10-23）：$0.27 / $25**。GPU $0.04，image2 $0.23，Wan $0。
