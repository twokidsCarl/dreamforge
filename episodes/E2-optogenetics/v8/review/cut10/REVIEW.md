# E2 Cut10 · B 段缩放链样段 v3（Carl t304 / t305 / t306）

**时间**：2026-10-24 ≈11:25 Asia/Shanghai  
**样段**：`E2_cut10_B_chain_v3_share.mp4` · **≈208 s ≈ 3:28** · 带旁白（VO 窗 183.5→393.5）  
**URL**：https://files.grolar-wage.ts.net/e2/cut10/E2_cut10_B_chain_v3_share.mp4  
**作废**：v2 https://files.grolar-wage.ts.net/e2/cut10/E2_cut10_B_chain_v2_share.mp4 · v1 preview 同目录

## 为什么 v2 不行（承认）
v2 自评「有画内变化」但仍是 **Goodsell 静板 + Ken Burns + 粒子/步进 overlay + 站间 dissolve**——不是 `SHOT_REDESIGN` 锁定的连续缩放链。缺 **衣藻**、**卵母细胞**；小鼠 **同一 clip 循环垫时长**，且前面有 **静帧小鼠站**。Carl t304「不行」+ t305/t306 硬约束后整段重做，不在 v2 上贴补丁。

## v3 相对 SHOT_REDESIGN B 表改了什么
| 链站 | v3 做法 |
|------|--------|
| 古菌→紫膜 | `sf03e` 左焦点连续推入紫斑 + 视黄醛结构色脉冲 |
| 泵↔通道 | **同一张** `sf08e` 膜：先推泵（一次一离子）再横移到通道孔（离子成串）——共享主体，非两张无关板溶解 |
| 衣藻 B_05 | `sf03e` 右半：鞭毛 warp + 趋光转向 + 眼点脉冲（v2 缺此站） |
| 卵母细胞 B_06 | 程序微距卵（动/植物极）+ 基因带飞入 + 双电极 + 青蓝给光 + 实时膜电流 + 放大框接 ChR1（v2 缺此站） |
| ChR2 | `sf09e`：接光/孔同分子 → 门开 → 阳离子流 → 脱敏/短脉冲 |
| 神经元 | **运动资产** `SF13_spike_causality.mp4`（去徽章），非静板缓推 |
| 活体小鼠 | **`SF18_invivo_dual` 只播一次**（≤源时长，无 loop）；无静帧小鼠站；入点即动（头 2 s 残差运动 >6） |

其它：ASS `BorderStyle=1` 描边软字幕；去掉 EIGENLENS 角标 spam / 步骤 pill；邻站 xfade 缩到 0.30 s。

## 自检（发布门槛，密帧 ≥1 fps）
| 项 | 分 | 依据 |
|----|----|------|
| (a) 无实心字幕色块 | **100** | 208/208 帧 solid-bar hits = 0 |
| (b) 无 ≥8 s KenBurns-only | **100** | longest low-motion = 7 s；bad_spans = [] |
| 链完整（衣藻+卵母细胞） | **100** | stations 含 chlamy / oocyte |
| 小鼠不循环 | **100** | st_mouse 15.08 s ≤ SF18 源 30 s；不重复同一 clip |
| 小鼠前无长静帧 | **100** | 无 still-mouse 站；入点头 2 s motion=6.54 |

`audit/summary.json` · `pass=true` 后才 scp。

## 诚实剩余差距
1. 邻站仍是短 xfade，不是真正「同一主体连续推到下一尺度」的光学变焦贯穿。  
2. 卵母细胞是程序微距，不是 Blender 电影级次表面散射台；放大框接膜仍偏示意。  
3. 泵/通道的离子与光谱仍有 2D 程序层（规则对，但未到原子球渲染循环）。  
4. 全片 ~15 min 未铺——等本样过目。

## 花费
≈ $0（复用 gen 板 + SF13/SF18；无新 pod / Token99 / Wan）。**未碰** E1 `e1r24`。
