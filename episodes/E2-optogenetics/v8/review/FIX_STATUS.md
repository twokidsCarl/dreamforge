# E2 Cut8 样段修复状态（眼 / 运动 / PIP / 分子插画 / F6）

**时间**：2026-10-24 Asia/Shanghai  
**交付级别**：样段自检，**禁止推全片 / 禁止 re-assemble**，等 Carl 目视。  
**E1**：未触碰（`tmux e1r22` 仍在跑）。

---

## 旧过线作废

- Cut7 五维加权（尺度美学/主体/旁白/运动/完播）→ **废止**。它奖励 PIP、OCR=0、zero_steps、满幅 HUD，放过眼错位、周期晃、PPT 模板。
- 「真实感 / 真3D / 毛发技术分」不得再驱动画法（Carl t271）。
- **新观感门 L2 + F6**：
  1. 主画面像纪录片英雄镜头（干净、可辨、不吓人）？
  2. 运动连续向前、不回摆？
  3. 信息层克制（非每镜四角贴满）？
  4. 通看 30s 会不会像 PPT？
  5. 分子镜是否 Goodsell/SF08e·SF09e 插画（光滑 3D 剖视 → FAIL）？
  6. **F6**：通看后若觉得变长/变闷/像样片墙 → FAIL；默认先砍料，不为「每镜真3D」撑时长。

OCR/帧差只做负向门禁，不加分。

---

## 刀 1 — 眼睛

### 根因
亮度启发式：
```python
ebox = (… & Z∈[0.105,0.185] …)
is_eye = ebox & (v_lum <= percentile(..., 15))
```
在 `mouse_c57.glb` 上颅顶≈Z0.35，该窗落在**胸肩**（旧质心 Z≈0.179）→ 角膜球挂颈/肩。

### 改法
`blender/mouse_eye_anatomy.py` → `place_c57_eyes()`  
- snout / ear / implant 解剖锚点；眶区 snout↔ear≈0.60、高度 `imp_z-0.105`（中颊）  
- 硬拒绝颈肩与近耳额影；UV 暗斑只在眶 band 内取紧簇  
- 角膜 ≈头长 4.5%，外推 0.3R（减小「浮珠重影」）  
同步：`test_fur_v2_closeup.py`、`render_mouse_v2_all.py`、`render_cage_multicam.py`

### 路径
| | path |
|---|---|
| Before（Carl 原投诉） | `review/eye_fix_before/fur_v2_closeup.png` · `sf10_camA_0001.png` · `mouse_awake_threeq.png` |
| After 侧脸 | `renders/fur_v2_closeup.png` · `renders/eye_fix/fur_v2_closeup_after.png` |
| After threeq | `renders/eye_fix/mouse_awake_threeq_after.png` |
| After camA | `renders/eye_fix/sf10_camA_0001.png` |

探针：旧质心 Z≈0.179（胸）→ 新 centers Z≈0.24–0.25（颅侧中颊）。  
**自检**：已离开颈肩；若 Carl 仍觉略前/重影，下一刀只微调 `eye_d` / 簇阈值，不再开亮度 ebox。

---

## 刀 2 — 运动（去周期往返）

### 旧 → 新
| 旧 | 新 |
|---|---|
| `head_yaw = ±0.01x * sin(2πu)` | `0` 或 `k * ease_mono(u)` 单向 |
| `breathe = 0.4–0.6 * sin/cos(2πu…)` | 常量 ≤0.08 |
| `stride_phase = u·4π` + lift 0.022 | ≤π；lift/爪Y 减半 |
| 相机 orbit 回摆 | 单向缓推 |

7 个序列全改（sf10_camA/B/C · cage_envA/B · nphr · comm）。

### 证明
- 曲线：`review/motion_mono_curves.png` + `motion_mono_check.json` → **MOTION_MONO_OK**
- 短片：`review/sf10_camA_mono.mp4`（已去周期往返、改为连续前移：睡姿→蓝光点亮，yaw=0）
- MAD：`review/sf10_camA_frame_mad.png`（相邻帧 MAD 平稳，无高低交替晃）

---

## 刀 3 — 关右上 PIP + 左下密 HUD

```python
ENABLE_CROSS_SCALE_PIP = False   # place_inset / inset_frame 总闸
ENABLE_DENSE_LOWER_HUD = False   # 左下卡默认关
CHAPTER_OPEN_FRAC = 0.12         # 仅章节头 ~12% 允许左下卡
```

### 前后对比（SF01 中段同一帧）
- `review/pip_before_SF01_with_pip.png`
- `review/pip_after_SF01_no_pip.png`
- `review/pip_before_after_SF01.png`
- PIP 区 MAD≈55.8（证明小窗确实被关掉）

---

## 刀 4 — 分子回 Goodsell / SF08e·SF09e（Cut8）

```python
USE_TRUE3D_MOLECULAR = False
mol_src('chr2'|'relay'|'microbes'|…)  # → gen/sf09e_chr2 · sf08e_relay · sf03e_microbes …
```
- SF06 / SF08 / SF09 及所有原 `chr2_3d`/`br_pump_3d`/`microbe_3d`/`hippo_cone_3d`/`retina_3d`/`nphr_3d` **主画面**改为插画静帧+轻运镜  
- 默认**不再加载** 6 套 `mol_retina_3d` 长序列（F6：不撑时长）  
- 真 3D 只留宏观小鼠/笼箱  

样段：`review/mol_style_SF06_switch_diagram.png` · `mol_style_SF08_early_attempts.png` · `mol_style_SF09_chr2_channel.png`  
（若仍是光滑 3D 剖视 → FAIL）

---

## 样段自检（新标准）

| # | 问 | 结论 |
|---|---|---|
| 1 | 英雄主画面干净不吓人？ | 眼已离颈肩；交 Carl 目视 after 侧脸/threeq |
| 2 | 运动连续向前？ | 公式 MONO_OK + `sf10_camA_mono.mp4` |
| 3 | 信息层克制？ | PIP 默认 OFF；左下仅章节头 |
| 4 | 还像 PPT？ | SF01 去小窗后主画面满幅 |
| 5 | 分子插画？ | `USE_TRUE3D_MOLECULAR=False` + mol_style_*.png |
| 6 | F6 变长变闷？ | 未挂 6 套长 3D 分子序列；全片时长重排等 Carl 过样段后再做 |

**未做**：全片 assemble、推 Carl 新成片、RunPod、动 E1。

---

## 代码清单
- `blender/mouse_eye_anatomy.py`（新）
- `blender/test_fur_v2_closeup.py`
- `blender/render_mouse_v2_all.py`
- `blender/render_cage_multicam.py`
- `tools/cinematic_fullbleed_v8.py`

## PR
（同步 eigenlens 后填）
