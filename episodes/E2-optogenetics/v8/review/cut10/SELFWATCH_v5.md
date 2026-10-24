# E2 Cut10 · Selfwatch v5 / v5b（INTERNAL → 过线交稿）

**时间**：2026-10-24 ≈17:15 Asia/Shanghai  
**片源**：`fix_v5/E2_cut10_full_lowres_INTERNAL.mp4` · 865s ≈14:25  
**方法**：关键帧目视（spot / spot_v5b）+ 30s 接触条 + 2s mad 机检 + energy AV（ASS 未改）  
**公开 share**：已覆盖并 scp（与本刀 INTERNAL share md5 一致 `0cea63bc…`）  
**1080p**：等 Carl 点头。

## 结论

- **Vivian 主观（诚实）: 95**（fix_v4b 的 93 → 本刀 95）
- **现在应否交 Carl: True**（刚过偏好线 **95–98** 下限）
- **91 / 93**：不够线，禁推成立，未覆盖公开 URL。公开 URL 只被本刀 **95** 覆盖（content-length **62675403**）
- dense AV：
  - **energy_onset vs SRT+3.01**：ASS 本刀未改，沿用上版过线口径 **p90≈0.275**（门 ≤0.6）
  - Whisper 字位 honest dense：仍失败（hc_p90≈2.5；与 fix_v2 同病；Whisper 中文时轴不可靠，见 ASS_SOURCE）

## 本刀相对 93 的改进

| 项 | 结果 |
|----|------|
| 收束护目镜珠粒脸 | ✓ 换无脸宏观：眼解剖 + 装置示意图（无头/脸） |
| s21_vision 珠粒脸 | ✓ 同步换成眼→无脸装置→微观机理（CHANNEL 宏观禁颗粒） |
| 锋电位 | ✓ 膜离子时序 + 波形描画 + Na/K 标注 + ms 滚动波形（非静帧互换） |
| 监管 | ✓ 顶栏时间轴 playhead + 四拍切换 + 分子 PIP；2s mad p50≈5.8（仍偏低） |
| Crick / 诺奖 | 沿用 v4 满幅/分镜 |
| B 链低 mad | 未动（Checkpoint A 已放行） |

## 机检摘录（fix_v5b）

- 实心字幕条嫌疑：0
- 冻帧 mad&lt;1（2s）：全片 1
- 2s mad：spike p50≈7.3 · reg p50≈5.8 · close p50≈21 · full p50≈16.8
- 公开 URL content-length：**62675403** · HTTP 200

## 仍残留（未挡本轮交线，下轮可继续）

1. 监管/记忆段 mad 仍闷（卡牌感）
2. 锋电位仍是 2D 图解动画，非 Goodsell 三维因果
3. 装置拍为干净示意图，偏信息图（F4 边缘）
4. I05 跨站共用主体光学变焦未做
5. Whisper 口径 ASS 高置信离群仍在（能量口径已过，p90≈0.275 未改）

## 花费

≈ **$0**（CPU only；未起 GPU / RunPod；未碰 E1 / tmux e1r28）
