# RunPod 渲染清单

agent 用 RunPod API 起停 Pod，预算内自行开卡、渲染、拉回、Terminate。各期通用；E2 第一批要渲哪些镜头见 [episodes/E2-optogenetics/FIRST_BATCH.md](../episodes/E2-optogenetics/FIRST_BATCH.md)。

## 预算

| 项 | 值 |
|---|---|
| 上限 | **$15/天，$80/周**（与视频预算一致）。卷的月费也算在里面 |
| 参考价 | A40 / RTX A6000 约 $0.4–0.6/小时（2026 年 9–10 月第三方记录，Secure Cloud 9 月涨过价）。**以开卡时实价为准** |
| E2 第一批 | 预计 1–2 小时，约 $1–2 |
| 记账 | 每次开卡记一行：日期、GPU、开机到 Terminate 的时长、金额。可写在 PR 评论里 |

**渲完、结果拉回 box 之后立刻 Terminate。** Stop 只停 GPU，容器盘还在计费；不要留 Pod。

## 持久化策略

| 放哪 | 放什么 |
|---|---|
| **Network Volume `eigenlens-cache`**（id `3b6w9chaub`，50 GB，机房 **CA-MTL-1**），挂在 `/workspace` | Blender 5.2.2（`/workspace/blender-5.2.2-linux-x64`）、仓库 clone（`/workspace/eigenlens`）、仓库里的 `.blender_pylib` |
| **box** 的 `episodes/<期>/renders/` | 渲染结果。**唯一的正本在这里** |

- 渲染结果先写在卷上的 `/workspace/renders`，渲完 rsync 回 box，核对齐全后再 Terminate。卷上的那份不算备份，不能当唯一副本；拉回之后清掉，省卷空间。
- 不用 Hugging Face 存片。
- Pod 本身用完即 Terminate；下次重开挂同一个卷，Blender 和仓库都还在。
- **卷空闲也计费**（按 GB/月，50 GB 约 $3–4/月，以 RunPod 账单为准）。暂时不删；不再需要时由 Carl 决定删卷。

## 开卡

**卷只能挂在同一机房的 Pod 上。** 起机必须指定 CA-MTL-1，否则挂不上。Network Volume 只支持 Secure Cloud。

| 选项 | 值 |
|---|---|
| 机房 | **CA-MTL-1** |
| Network Volume | **`3b6w9chaub`**（`eigenlens-cache`），挂 `/workspace` |
| Cloud | Secure |
| GPU | **RTX A6000 48GB 或 A40 48GB**（优先，1 张）。CA-MTL-1 没货时 RTX 4090 24GB / L40S 48GB 也可以；第一批是 640×360，显存不紧。都没货就等，不换机房 |
| 镜像 | 任一官方 Ubuntu 22.04 / 24.04 + CUDA 12 镜像（例如 RunPod PyTorch）。不需要 PyTorch，只要 NVIDIA 驱动和 SSH |
| 环境变量 | **`NVIDIA_DRIVER_CAPABILITIES=all`**。不加的话容器里没有图形库，无显示器的 EEVEE 起不来；Cycles 不受影响 |
| 容器盘 | 20 GB（另挂卷，不用再开 Pod Volume） |
| 端口 | SSH `22/tcp`。公钥在 RunPod 账户设置里 |

### API

API key 放在 `RUNPOD_API_KEY`，不要写进仓库。用 REST API（`https://rest.runpod.io/v1`）；字段名以 [RunPod API 文档](https://docs.runpod.io/api-reference) 为准：

```bash
# 起机
curl -s -X POST https://rest.runpod.io/v1/pods \
  -H "Authorization: Bearer $RUNPOD_API_KEY" -H "Content-Type: application/json" \
  -d '{
    "name": "eigenlens-render",
    "imageName": "<官方 Ubuntu + CUDA 12 镜像>",
    "cloudType": "SECURE",
    "gpuTypeIds": ["NVIDIA RTX A6000", "NVIDIA A40"],
    "gpuCount": 1,
    "dataCenterIds": ["CA-MTL-1"],
    "networkVolumeId": "3b6w9chaub",
    "volumeMountPath": "/workspace",
    "containerDiskInGb": 20,
    "ports": ["22/tcp"],
    "env": {"NVIDIA_DRIVER_CAPABILITIES": "all"}
  }'

# 查 SSH 的 IP 和端口
curl -s -H "Authorization: Bearer $RUNPOD_API_KEY" https://rest.runpod.io/v1/pods/<podId>

# 用完 Terminate（删 Pod，卷保留）
curl -s -X DELETE -H "Authorization: Bearer $RUNPOD_API_KEY" https://rest.runpod.io/v1/pods/<podId>
```

起机后记下 podId；每次会话结束前确认 Pod 已 Terminate（`GET /v1/pods` 里没有它）。

## SSH 之后

### 首次灌卷（卷上还没有 Blender 时，只做一次）

```bash
apt-get update && apt-get install -y libxi6 libxkbcommon0 libsm6 libxrender1 libxxf86vm1 libxfixes3 \
  libgl1 libegl1 xz-utils git tmux rsync python3-pip
cd /workspace
curl -LO https://download.blender.org/release/Blender5.2/blender-5.2.2-linux-x64.tar.xz
tar xf blender-5.2.2-linux-x64.tar.xz && rm blender-5.2.2-linux-x64.tar.xz
if [ -d /workspace/eigenlens/.git ]; then git -C /workspace/eigenlens pull; \
else git clone https://github.com/twokidsCarl/eigenlens.git /workspace/eigenlens; fi
cd /workspace/eigenlens
python3 -m pip install --target .blender_pylib pyyaml
```

### 之后每次

同一个卷、同一机房起机。卷上已有 Blender 和仓库，跳过下载；系统库装在容器盘上，Terminate 后会丢，每次要重装：

```bash
apt-get update && apt-get install -y libxi6 libxkbcommon0 libsm6 libxrender1 libxxf86vm1 libxfixes3 \
  libgl1 libegl1 git tmux rsync
ls /workspace/blender-5.2.2-linux-x64/blender   # 不在就回到「首次灌卷」
cd /workspace/eigenlens && git pull
```

`.blender_pylib` 在卷上，不用重装；依赖有变化时再 `python3 -m pip install --target .blender_pylib <包>`。

### 环境变量和 GPU 检查

```bash
cd /workspace/eigenlens
export DREAMFORGE_EPISODE=E2-optogenetics
export DREAMFORGE_RENDER_DIR=/workspace/renders
export DREAMFORGE_CYCLES_DEVICE=OPTIX
export BLENDER=/workspace/blender-5.2.2-linux-x64/blender
nvidia-smi
$BLENDER -b --factory-startup -P shared/tools/render_storyboard.py -- --shot A0_03b --quality preview --frames 1
$BLENDER -b --factory-startup -P shared/tools/render_storyboard.py -- --shot A0_91 --quality preview --frames 1
```

第一条是 EEVEE，第二条是 Cycles。两张 png 都出现在 `/workspace/renders/shots/` 下，才往下走。

### 跑渲染

```bash
tmux new -s r
```

在 tmux 里按该期 FIRST_BATCH.md 的「命令」一节跑（环境变量要在 tmux 里重新 export）。

### 拉回 box，然后 Terminate

在 box 的仓库根目录（IP 和端口从 API 或 RunPod 的 Connect 页面拿）：

```bash
rsync -avz -e "ssh -p <端口>" root@<IP>:/workspace/renders/ episodes/E2-optogenetics/renders/
```

确认 `shots/`、`log_*.txt`、`times.csv` 都在 box 上了，再清掉卷上的副本并 Terminate：

```bash
# Pod 上
rm -rf /workspace/renders
```

然后 `DELETE /v1/pods/<podId>`（或控制台 **Terminate**）。

## EEVEE 起不来

现象：EEVEE 镜头全部失败，日志里有 EGL、display、OpenGL、`GPU backend` 之类的报错；Cycles 正常。

原因：容器没开图形能力。

做法：不在这台 Pod 上修。Terminate，确认起机参数里有 `NVIDIA_DRIVER_CAPABILITIES=all` 再重开（还是 CA-MTL-1 + 同一个卷）；还不行就换一个镜像或换 GPU 型号。排查不要超过 15 分钟。

## Cycles 慢

Cycles 一帧 preview 超过 30 秒，或日志里看不到 GPU 设备：检查 `DREAMFORGE_CYCLES_DEVICE`。不设时 Linux 默认用 CPU。OPTIX 不行就改 `CUDA`。
