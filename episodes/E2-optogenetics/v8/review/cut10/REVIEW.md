# E2 Cut10 · B 段缩放链样段 v2（Carl t301/t302）

**时间**：2026-10-24 ≈10:45 Asia/Shanghai  
**样段**：`E2_cut10_B_chain_v2_share.mp4` · **≈162 s ≈ 2:42** · 带旁白（v7 骨架 B 窗 VO 183.5→348.5）  
**URL**：https://files.grolar-wage.ts.net/e2/cut10/E2_cut10_B_chain_v2_share.mp4  
**上版 v1（作废）**：https://files.grolar-wage.ts.net/e2/cut10/E2_cut10_B_chain_preview_share.mp4

## 承认（t302）
**v1 推送前没有做整段自看 / 密帧审计**——实心底栏字幕条和 Ken-Burns 站板本可在发布前拦住。这是流程失败，不是审美争议。本 v2 **先**做了每 2 s 一帧的密帧自检 + 站内残差运动量化，两项自评 ≥95 才上传。

## Carl t301 两点硬伤 → v2 改法
1. **实心底栏字幕条** → 去掉 `b_chain_cap.mp4` 整幅色块叠底；改 ASS `BorderStyle=1` 描边软字幕（无 opaque box）。密帧扫 81 帧，实心底栏嫌疑 = 0。
2. **站 = Ken-Burns 静板** → 每站加 VO 同步画内变化：
   - microbes：光粒子汇入 + 紫膜区脉冲
   - relay：①→②→③→④ 接力高亮 + 速度条（不到 ms）
   - pump：≈2.2 s 一离子上跳循环（标签「第 n 次」）
   - ChR2：蓝光 → 视黄醛脉冲 → 门开 → Na+ 流
   - neuron：胞体点亮 + 轴突锋电位行进
   - mouse：写实 clip 循环（非静图推镜）+ 插芯蓝光
   站内中心残差（去全局缩放下）全部 PASS（microbes 14.8 … mouse_clip 24.6）。

## 相对 SHOT_REDESIGN 的自检（4 行）
1. **链**：古菌/紫膜 → 接力 → 泵 → ChR2 → 神经元 → 写实光纤小鼠；邻站 0.55 s xfade + 站内缓推。
2. **字幕**：软 ASS，无实心底栏；站标是左下角小半透明 pill，不是全宽色条。
3. **画内**：上列六站均有程序/clip 内变化，不是纯 Ken-Burns。
4. **未完成（诚实）**：邻站仍非「同一主体连续推入下一尺度」真连续变焦；缺衣藻单镜、卵母细胞台；全片 15 min 未做——等本样过目再铺。

## 自评分（发布门槛两项）
| 项 | 分 | 依据 |
|----|----|------|
| (a) 无实心底栏字幕 | **97** | 81/81 帧无 solid bar；底区 RGB std 31–66 |
| (b) 站非 Ken-Burns-only | **96** | 7/7 站 center_residual ≥ 3.6 |

## 花费
≈ $0（复用 Goodsell 板 + Cut9 小鼠 clip；无新 Token99/Wan）。E1 e1r23 未碰。
