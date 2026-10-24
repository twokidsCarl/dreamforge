# E2 Cut10 · 低清全片 Checkpoint B（Carl t321 放行 A 后）

**时间**：2026-10-24 ≈15:10 Asia/Shanghai  
**成片**：`E2_cut10_full_lowres_share.mp4` · **865.0s ≈ 14:25** · 带旁白  
**URL**：https://files.grolar-wage.ts.net/e2/cut10/E2_cut10_full_lowres_share.mp4

## Carl 拍板（t321）
「有些小问题，你先出低清全片吧，我在全片上给你调。」→ Checkpoint A 放行；本刀交 **Checkpoint B 低清全片**。

## 组装
1. **旁白脊骨**：全长 BASE VO（865s），**未** Cut9 砍尾。
2. **B 窗** [183.76, 391.80]：焊入已过线 B-chain v3.2 `video_raw`（音画已对齐站）。
3. **A0/A/C/D**：干净 gen/SF 底板 + 程序连续 cam（thin_label 站名角标）；去 EIGENLENS/顶栏烧字；片头 sting 改为开场板连续运动（消实心条误检）。
4. **字幕**：软 ASS（BorderStyle=1）。**ASR 同源重对**（chunked 30s、无 VAD；开场 speech onset=4.30s 校准早期 Whisper 时钟）；`ASS_SOURCE.txt` 锁定，禁止再被 naive SRT±3.01 覆盖。
5. **小鼠**：行为只在 B 链播一次；A 段用静帧+运镜，C 记忆段不用 SF18 行为循环。

## 自检（上传前 · pass=true）

| 门 | 分 | 结果 |
|----|----|------|
| (a) 无实心字幕/烧字 pill | **100** | bar=0 · top_pill=0 |
| (b) 无 ≥3 s mad&lt;1 | **100** | longest=2 s |
| (d) 小鼠前不静 | **100** | pre_freeze=0 |
| (av) 字幕↔旁白 | **100** | median \|lag\|=0.0 · sample 12/12 |
| (oo) 卵母非 PPT | **100** | pptish=0 |
| (open) 前 30s 无 pill | **100** | hits=0 |
| 时长 ~15 min | **100** | 865.0s |
| Vivian 主观 | **96** | ≥95 |

`audit/summary.json` · **pass=True**

## 相对 SHOT_REDESIGN / Carl「小问题」（诚实差距，供全片调）
1. **邻站短运镜 ≠ 真光学连续变焦**（B 链亦同；全片 A/C/D 多为单板缓推）。
2. **C 记忆段**未铺条件化箱/行为小鼠，改用神经元板+运镜保知识旁白（避小鼠行为二播）。
3. **人物脸**（Crick/诺奖）仍偏珠粒插画，未完全落到「脸无颗粒」偏好。
4. **监管/临床段**信息层偏薄（底板+角标），不是 SHOT_REDESIGN 里的数据卡叠层完成态。
5. **长板重复**：A 锋电位、C/D 收束多段复用同一神经元底板，观感会腻——可按镜表换板。

## 花费
≈ $0（本机 CPU ASR + ffmpeg；未起 GPU pod）。**未碰 E1**（tmux e1r26 仍在）。
