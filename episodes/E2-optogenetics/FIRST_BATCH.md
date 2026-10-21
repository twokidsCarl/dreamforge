# E2 P8 第一批试渲（交接包）

目的：一开 GPU 就能渲。这一批只做 **preview 试渲**，看 GPU 上的 EEVEE / Cycles 是否和本机 CPU 预览一致、各段代表镜头的画面是否成立。不是成片渲染。

- 开卡步骤：[docs/RUNPOD.md](../../docs/RUNPOD.md)（agent 用 API 起停；Network Volume `eigenlens-cache`，机房 CA-MTL-1）
- 预算：$15/天、$80/周。这一批预计 GPU 用时 1–2 小时，费用约 $1–2
- 放在本目录而不是 `renders/`，因为 `renders/` 不入库（`.gitignore`）
- 协调：Luna 定批次和看片；agent 开卡、跑命令、拉回 box、Terminate

## 选了哪些镜头

15 个 3D 镜头：A0 4 个（与已有 A0 样片对照），A、B、C 各 3–4 个，D 1 个。七种画面语言（documentary、clay、energy、sem、xray、photoreal、blueprint）全覆盖；EEVEE 9 个、Cycles 6 个。2D 镜头不在 GPU 上渲（Pillow，本机就能跑）。

帧数 = `storyboard.timed.yaml` 时长 × 24，与 `render_storyboard.py` 算法一致。中帧 = `(帧数+1)//2`。

| # | 镜头 | 场景模块（args） | engine | 风格 | 帧数 | 中帧 | 为何选它 |
|---|---|---|---|---|---|---|---|
| 1 | A0_01a | a0_scenes（paper） | cycles | documentary | 94 | 47 | A0 对照：开场纸页。和 A0 样片 v2 同一代码，用来确认 GPU Cycles 与本机结果一致 |
| 2 | A0_03b | a0_scenes（neurons） | eevee | clay | 32 | 16 | A0 对照：最便宜的 EEVEE 镜头，先用它验证无显示器的 EEVEE 能在 Pod 上起来 |
| 3 | A0_04a | a0_scenes（laureates） | eevee | energy | 375 | 188 | A0 对照：`raw: true` 全流程（Blender 写 `preview_raw/` → `mograph.py` 叠字）唯一已写好后处理的镜头 |
| 4 | A0_91 | a0_scenes（membrane） | cycles | sem | 36 | 18 | A0 对照：52 万面的紫膜，看 GPU 显存和 sem 风格 |
| 5 | A_01a | a_scenes（spike） | eevee | xray | 255 | 128 | 第一幕核心：膜剖面 + 离子 + 膜电位曲线。build 最慢（本机约 22 秒），顺便测 build 开销 |
| 6 | A_06a | a_scenes（opsin） | eevee | energy | 134 | 67 | 第一幕核心分子：七次跨膜蛋白被光打开（PR #17 推荐） |
| 7 | A_08a | a_scenes（bench） | cycles | photoreal | 461 | 231 | 示意道具（实验台、光纤）在 photoreal 下能不能看；只渲单帧 |
| 8 | B_05a | b_cell_scenes（chlamy_swim） | cycles | photoreal | 288 | 144 | 第二幕视觉高潮的前一镜：衣藻游向光 |
| 9 | B_06a | b_cell_scenes（oocyte） | eevee | blueprint | 586 | 293 | 唯一 blueprint 风格的代表，也是分镜写 manim、改在 Blender 做的三镜之一；最长镜头，只渲单帧 |
| 10 | B_08a | b_scenes（chr2） | eevee | energy | 453 | 227 | 第二幕核心：蓝光打开 ChR2、峰值落到平台（PR #17 推荐） |
| 11 | B_09b | b_scenes（chr2） | eevee | energy | 32 | 16 | 与 B_08a 同一场景、起始帧 265。验证「第二段时间表」接得上 |
| 12 | C_03a | c_scenes（cage, env B, mouse fiber） | cycles | photoreal | 408 | 204 | 第三幕假记忆：示意小鼠 + 光纤 + 笼。看道具和「不血腥」 |
| 13 | C_07a | c_scenes（retina, rp） | eevee | xray | 403 | 202 | 第三幕临床线核心：参数化视网膜剖面。`raw: true`，叠字还没写，先只看 `preview_raw/` |
| 14 | C_18a | c_scenes（desens） | eevee | energy | 230 | 115 | ChR2 脱敏，和 B_08a 同一分子在另一幕的样子（PR #17 推荐） |
| 15 | D_92 | d_scenes（closing） | cycles | sem | 96 | 48 | 结尾最后一镜：通道关闭（PR #17 推荐） |

全长合计 3883 帧。这一批不全渲，分三步：

| 步 | 内容 | 帧数 | 预计 GPU 时间 |
|---|---|---|---|
| 1 | 15 镜 × 首 / 中 / 尾三帧，preview | 45 | 10–20 分钟（主要是每镜 build） |
| 2 | 6 个短镜全长，preview：A0_03b、A0_91、B_09b、D_92、A_06a、C_18a | 560 | 20–40 分钟 |
| 3 | （看完 1、2 再定）A0_01a 全长 sample，和 A0 样片 v2 并排比 | 94 | 约 10 分钟 |

2026-10-21 在无 GPU 的 Linux 机上跑过 `build_check --shots <上面 15 个>`：全部 OK，registry 126 条无缺漏。用 CPU 渲 A0_03b 尾帧一张（preview）8.8 秒。

没选的已知问题镜头（C_17a、B_14a 偏淡，C_08a 视网膜像圆盘，A_92 不够暗）等第一批看完再调，不进这一批。

## 环境变量

| 变量 | 值 | 说明 |
|---|---|---|
| `DREAMFORGE_EPISODE` | `E2-optogenetics` | 必设。默认是 E1 |
| `DREAMFORGE_RENDER_DIR` | `/workspace/renders` | 渲染根目录。Pod 上放 `/workspace`（Network Volume；拉回 box 后清掉）；不设就写到 `episodes/E2-optogenetics/renders/` |
| `DREAMFORGE_CYCLES_DEVICE` | `OPTIX` | **必设**。Linux 默认是 CPU，不设 Cycles 会在 CPU 上慢渲。OPTIX 不行就用 `CUDA` |
| `BLENDER` | `/workspace/blender-5.2.2-linux-x64/blender` | `render_batch.sh` 用它找 Blender。仓库按 Blender 5.2 写 |
| `FRAMES` | `1,mid,last` | 可选。`render_batch.sh` 只渲这几帧；不设就渲全长 |

`--frames` 现在接受 `mid`、`last`（本次 PR 加的），不用逐镜算中帧。

## 命令

在 Pod 上的仓库根目录。环境变量先设好：

```bash
export DREAMFORGE_EPISODE=E2-optogenetics
export DREAMFORGE_RENDER_DIR=/workspace/renders
export DREAMFORGE_CYCLES_DEVICE=OPTIX
export BLENDER=/workspace/blender-5.2.2-linux-x64/blender
```

**0. 冒烟（不渲染，约 1 分钟）**

```bash
$BLENDER -b --factory-startup -P shared/tools/build_check.py -- \
  --shots A0_01a,A0_03b,A0_04a,A0_91,A_01a,A_06a,A_08a,B_05a,B_06a,B_08a,B_09b,C_03a,C_07a,C_18a,D_92
```

最后一行应是 `FAIL 0`。

**单帧试渲（一个镜头）**

```bash
$BLENDER -b --factory-startup -P shared/tools/render_storyboard.py -- --shot A0_03b --quality preview --frames 1,mid,last
```

先跑 A0_03b（EEVEE）和 A0_91（Cycles）各一次。两张都出来、日志里 Cycles 用的是 GPU，再跑整批。

**第 1 步：15 镜首 / 中 / 尾帧**

```bash
FRAMES=1,mid,last shared/tools/render_batch.sh preview \
  A0_01a A0_03b A0_04a A0_91 A_01a A_06a A_08a B_05a B_06a B_08a B_09b C_03a C_07a C_18a D_92
```

**第 2 步：短镜全长**

```bash
shared/tools/render_batch.sh preview A0_03b A0_91 B_09b D_92 A_06a C_18a
```

**第 3 步（Luna 看完再定）**

```bash
shared/tools/render_batch.sh sample A0_01a
```

长任务放在 `tmux` 里跑，SSH 断了也不会停（`tmux new -s r`，断开后 `tmux attach -t r`）。

## 输出目录

```
$DREAMFORGE_RENDER_DIR/
├── shots/<id>/preview/0001.png      帧号从 1 起，对应镜头内帧号
├── shots/<id>/preview_raw/...       raw: true 的镜头（A0_04a、C_07a）先写这里
├── log_<id>.txt                     每镜 Blender 全部输出
└── times.csv                        每帧耗时：timestamp, shot, engine, preset, frame, seconds
```

拉回 box 后放到 `episodes/E2-optogenetics/renders/`（不入库）。A0_04a 的叠字在 box 上做，不占 GPU 时间：

```bash
DREAMFORGE_EPISODE=E2-optogenetics python3 shared/tools/mograph.py --shot A0_04a --quality preview --frames 1,188,375
```

`times.csv` 一起拉回。第一批的每帧耗时用来估算后面 final 的总 GPU 时间。

## 失败和重试

`render_batch.sh` 遇到失败打印 `FAIL <id>`，继续下一个镜头，最后退出码为 1。

1. 先看 `log_<id>.txt` 末尾。
2. **偶发错误**（CUDA / OptiX 报错、显存不足、进程被杀）：同一条命令只对这个镜头重跑 **一次**。Cycles 在 GPU 报错时会自动改用 CPU 重试那一帧，日志里有 `retrying ... on CPU`；看到这句说明那一帧是 CPU 渲的，记下来。
3. **代码错误**（日志里是场景模块的 Python Traceback）：不重试，**不要在 Pod 上改脚本**（WORKFLOW 8.1：渲染中改脚本会让同一批用的不是同一版代码）。记下镜头 id 和 Traceback，跳过，交给 Luna 走 PR 修。
4. 同一镜头重试后仍失败：标记为阻塞，继续其他镜头。
5. **EEVEE 镜头全部失败**、日志里有 EGL / display / OpenGL 字样：是容器没开图形能力。见 [docs/RUNPOD.md](../../docs/RUNPOD.md) 的「EEVEE 起不来」。不要花超过 15 分钟排查，先 Terminate，换配置重开（仍是 CA-MTL-1 + 同一个卷）。
6. Cycles 镜头日志里没有 GPU 设备、或每帧明显慢（preview 一帧超过 30 秒）：检查 `DREAMFORGE_CYCLES_DEVICE`。

## 看片要看什么

- 15 个镜头的三帧和本机 CPU 预览比：构图、风格、亮度一致吗
- A0 四镜和 A0 样片 v2 一致吗
- B_08a 尾帧接 B_09b 首帧是否连续
- `times.csv`：EEVEE / Cycles 每帧秒数，按此估算全片 final 的 GPU 小时数
- 结论写回 PR 或本文件末尾，再定第二批

## 不在这一批

- final / sample 全片渲染
- 2D 镜头（A–D 的 mograph 模块还没写）
- raw 镜头的叠字（B_02a 等 7 个，除 A0_04a）
- P6 画面核查表 `research/visual/audit_<段>.yaml`
