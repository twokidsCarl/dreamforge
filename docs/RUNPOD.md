# RunPod 开卡清单（Carl 自己开）

agent 不租 GPU、不启动 Pod。这一页给 Carl 开卡时照着做。各期通用；E2 第一批要渲哪些镜头见 [episodes/E2-optogenetics/FIRST_BATCH.md](../episodes/E2-optogenetics/FIRST_BATCH.md)。

## 预算

| 项 | 值 |
|---|---|
| 上限 | **$15/天，$80/周**（与视频预算一致） |
| 参考价 | A40 / RTX A6000 约 $0.4–0.6/小时（2026 年 9–10 月第三方记录，Secure Cloud 9 月涨过价）。**以开卡页实价为准** |
| E2 第一批 | 预计 1–2 小时，约 $1–2 |
| 记账 | 每次开卡记一行：日期、GPU、开机到 Terminate 的时长、金额。可写在 PR 评论里 |

**渲完、结果拉回之后立刻 Terminate。** Stop 只停 GPU，盘还在计费；第一批不要留 Pod，也不需要 Network Volume。可选：账户里只充当天要用的额度，作为硬上限。

## 开卡

| 选项 | 建议 |
|---|---|
| GPU | **RTX A6000 48GB 或 A40 48GB**（优先，1 张）。没货时 RTX 4090 24GB / L40S 48GB 也可以；第一批是 640×360，显存不紧 |
| Cloud | Community 更便宜；没货再用 Secure |
| 模板 | 任一官方 Ubuntu 22.04 / 24.04 + CUDA 12 的模板（例如 RunPod PyTorch）。不需要 PyTorch，只要 NVIDIA 驱动和 SSH |
| 环境变量 | **`NVIDIA_DRIVER_CAPABILITIES=all`**（开卡时在模板里加）。不加的话容器里没有图形库，无显示器的 EEVEE 起不来；Cycles 不受影响 |
| 磁盘 | Container 20 GB；Volume 40 GB（挂在 `/workspace`） |
| 端口 | 开 SSH（TCP 22）。公钥先加到 RunPod 账户设置里 |

## SSH 之后

**1. 系统库和 Blender 5.2.2（约 3 分钟）**

```bash
apt-get update && apt-get install -y libxi6 libxkbcommon0 libsm6 libxrender1 libxxf86vm1 libxfixes3 \
  libgl1 libegl1 xz-utils git tmux rsync python3-pip
cd /workspace
curl -LO https://download.blender.org/release/Blender5.2/blender-5.2.2-linux-x64.tar.xz
tar xf blender-5.2.2-linux-x64.tar.xz
```

**2. 仓库和 Blender 用的 PyYAML**

```bash
git clone https://github.com/twokidsCarl/eigenlens.git && cd eigenlens
python3 -m pip install --target .blender_pylib pyyaml
```

**3. 环境变量和 GPU 检查**

```bash
export DREAMFORGE_EPISODE=E2-optogenetics
export DREAMFORGE_RENDER_DIR=/workspace/renders
export DREAMFORGE_CYCLES_DEVICE=OPTIX
export BLENDER=/workspace/blender-5.2.2-linux-x64/blender
nvidia-smi
$BLENDER -b --factory-startup -P shared/tools/render_storyboard.py -- --shot A0_03b --quality preview --frames 1
$BLENDER -b --factory-startup -P shared/tools/render_storyboard.py -- --shot A0_91 --quality preview --frames 1
```

第一条是 EEVEE，第二条是 Cycles。两张 png 都出现在 `/workspace/renders/shots/` 下，才往下走。

**4. 跑第一批**

```bash
tmux new -s r
```

在 tmux 里按 FIRST_BATCH.md 的「命令」一节跑（环境变量要在 tmux 里重新 export）。

**5. 拉回结果，然后 Terminate**

在 Mac 的仓库根目录（IP 和端口在 RunPod 的 Connect 页面）：

```bash
rsync -avz -e "ssh -p <端口>" root@<IP>:/workspace/renders/ episodes/E2-optogenetics/renders/
```

确认 `shots/`、`log_*.txt`、`times.csv` 都在本机了，再到 RunPod 控制台 **Terminate**。

## EEVEE 起不来

现象：EEVEE 镜头全部失败，日志里有 EGL、display、OpenGL、`GPU backend` 之类的报错；Cycles 正常。

原因：容器没开图形能力。

做法：不在这台 Pod 上修。Terminate，开卡时加 `NVIDIA_DRIVER_CAPABILITIES=all` 重开；还不行就换一个模板或换一家机器。排查不要超过 15 分钟。

## Cycles 慢

Cycles 一帧 preview 超过 30 秒，或日志里看不到 GPU 设备：检查 `DREAMFORGE_CYCLES_DEVICE`。不设时 Linux 默认用 CPU。OPTIX 不行就改 `CUDA`。
