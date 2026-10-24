# E2 Cut10 · B 段缩放链样段 v3.2（覆盖 v3.1；Carl t314–t317）

**时间**：2026-10-24 ≈13:30 Asia/Shanghai  
**样段**：`E2_cut10_B_chain_v3_share.mp4` · **≈208 s ≈ 3:28** · 带旁白  
**URL**：https://files.grolar-wage.ts.net/e2/cut10/E2_cut10_B_chain_v3_share.mp4（**已覆盖** v3.1）

## Carl 反馈（t314/t316/t317）
1. **字幕和音频没有对上**
2. **卵母等站一眼糙**（旧 PPT 球 + 波形 HUD；角标复述旁白 → 双行字）
3. 要以最严标准自拦，不要靠 Carl 一眼抓

## v3.2 改法
1. **A/V 同源**：`VO_START=183.76` = BASE 上开场句「这枚开关…」ASR 真实发音起点（SRT cue0=180.75，Δ≈3.01s）。ASS **按 VO 的 chunked ASR 重对时**（禁止只改 VO 或只改 ASS）。  
2. **卵母**：全段 Goodsell 膜板程序连续（离子流 + 光脉冲）；角标只留站名「卵母·2002 / 卵母·ChR1」，**禁止**复述 VO「光一到，门就动」。  
3. **衣藻**：加强鞭毛连续运动；站名角标。  
4. 神经元/小鼠沿用 v3.1 门禁通过站（SF13 运动头 + 程序尾；SF18 一次、无蓝开黄关）。

## 自检数字（上传前）
| 门 | 分 | 结果 |
|----|----|------|
| (a) 无实心字幕/烧字 pill | **100** | bar=0 · top_pill=0 |
| (b) 无 ≥3 s mad&lt;1 | **100** | longest=1 s |
| (c) 链含衣藻+卵母 | **100** | ok |
| (d) 小鼠不循环/前不静 | **100** | loop=false · pre_freeze=0 |
| (av) 字幕↔旁白 | **100** | median \|lag\|≈0 · sample 7–8/8 |
| (oo) 卵母非 PPT | **100** | pptish=0 |
| Vivian 主观 | **96** | ≥95 |

`audit_v32/summary.json` · **pass=true** 后才覆盖 scp。

## 相对 SHOT_REDESIGN（诚实）
链站仍在。邻站短 xfade ≠ 真光学连续变焦。

## 花费
≈ $0。未碰 E1。
