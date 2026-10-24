# E2 Cut10 · B 段缩放链样段 v3.1（覆盖 v3；Carl t304/t305/t306）

**时间**：2026-10-24 ≈11:45 Asia/Shanghai  
**样段**：`E2_cut10_B_chain_v3_share.mp4` · **≈208 s ≈ 3:28** · 带旁白（VO 183.5 起）  
**URL**：https://files.grolar-wage.ts.net/e2/cut10/E2_cut10_B_chain_v3_share.mp4（**已覆盖**坏 v3）

## Vivian 自检失败（v3 曾误发）
密帧 1 fps 扫到 **≈168–192 s 连续 mad≈0（约 20 s 静帧）**，正是 Carl t306「小鼠视频前面也有静止好长时间」。  
根因：把 `SF13_spike_causality.mp4` 当全程运动素材，但它 **t≥20 s 后是多段静板硬切**（非 hold-last pad，效果等同冻帧）。小鼠 HUD 还残留实心黑条「蓝开 · 黄关」。

**门禁未过却已 scp**——本 v3.1 先自检 PASS 再覆盖同一 URL，避免 Carl 继续看坏片。

## v3.1 改法
1. **神经元**：只用 SF13 **运动头 0–19 s**；余下时长用 **程序连续锋电位动画**（相机漂移 + 脉冲 + 轴突行进），**禁止** tpad/hold-last。  
2. **小鼠**：SF18 **只播一次**（skip 首 1 s 标题卡）；delogo 去掉 EIGENLENS +「蓝开·黄关」实心条；入点即动。  
3. 邻站 xfade 0.30 s；无循环、无静帧小鼠站。

## 自检数字（上传前，≥1 fps）
| 门 | 分 | 结果 |
|----|----|------|
| (a) 无实心字幕/HUD 条 | **100** | bar=0 · center-pill=0 · mouse0_pill=false |
| (b) 无 ≥3 s mad&lt;1 | **100** | longest=1 s · bad_spans=[] · p50 residual≈12.8 |
| (c) 链含衣藻+卵母细胞 | **100** | chlamy + oocyte 在站表 |
| (d) 小鼠不循环 / 前不静 | **100** | st=15.08≤源；head_motion≈5.93；pre_mouse_freeze_seconds=**0** |

`audit_v31/summary.json` · `pass=true` 后才覆盖 scp。

## 相对 SHOT_REDESIGN（诚实）
链站仍在：古菌→膜泵/通道（同膜横移）→衣藻→卵母细胞→ChR2→神经元→活体小鼠。  
剩余差距：邻站短 xfade ≠ 真光学连续变焦；卵母细胞仍为程序微距。

## 花费
≈ $0。未碰 E1 `e1r24`。
