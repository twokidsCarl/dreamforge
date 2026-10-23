# E2 internal rework — macro photo OPEN (SF01–03 / 06–09 / 11–12) · 2026-10-23 ~23:02 Asia/Shanghai

## Done (no GPU · pods=[] · $0)
1. **Rebuilt residual opening & apparatus/micro boards (`SF01–03 / 06–09 / 11–12`, ~90.6s film)** via `tools/macro_photo_boost_open.py` (with rerender pass on SF03/08/09/11 to strip all internal production remarks from chips/footers):
   | board | film window | unique dur | before → after |
   |---|---|---|---|
   | SF01_open_title | 3.00–8.00s | 5.0s | type title card → LARGE 3D mouse (`awake_3d_tq`) + title chips |
   | SF02_1979_request | 8.00–12.02s | 4.0s | diagram request card → clean Crick 2.5D portrait + chips |
   | SF03_microbe_clues | 12.02–19.75s | 8.0s | small microbe diagram → LARGE scale-correct clean micro plate (`sf03e_microbes`) |
   | SF12_neuron_select | 30.71–40.42s | 10.0s | A0_03 diagram → 2-beat (`sleep_tq` → `awake_3d`) + selectivity chips |
   | SF06_switch_diagram | 51.49–60.74s | 9.0s | switch diagram → 2-beat (`awake_3d_tq` → `still_awake_tq`) + switch chips |
   | SF07_main_title | 61.14–68.31s | 7.0s | title card → 2-beat (`still_awake_tq` → `sleep_3d`) + main title chips |
   | SF08_early_attempts | 121.38–137.06s | 16.0s | early-attempt diagram → 3-beat multi-pose (`sleep_3d` / `still_sleep_tq` / `awake_3d`) |
   | SF09_chr2_channel | 137.46–145.21s | 8.0s | small channel diagram → LARGE scale-correct clean ChR2 micro plate (`sf09e_chr2`) |
   | SF11_eye_goggles | 593.87–618.16s | 24.0s | eye diagram → 3-beat SF21-class apparatus plates (`eye` / `eye_b` / `eye_c`) |
2. **Completed `assemble_v8_roughcut.py` (PID 356724)**:
   - Master: `/workspace/e2work/lowres_cut/E2_roughcut_v8_internal_20261023_2237.mp4` (`864.71s`, `981.9 MB`, `1280×720 @24fps`, **AAC audio verified**).
   - Share (local only): `/workspace/e2work/lowres_cut/E2_roughcut_v8_internal_20261023_2237_share.mp4` (`36.0 MB`).
3. **No A40 / RunPod**: `pods=[]` GraphQL-confirmed. $0 spent.

## Coverage (picture time · total 865.04s / master 864.71s)
- **v8 styleframes inserted (all 23 SFs: SF01–SF23)**: **860.84s / 865.04s (99.51%)**
  - Macro photoreal / 3D mouse / apparatus / clean portrait forward (`SF01, 02, 04, 05, 06, 07, 08, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23` — 21 SFs): **845.36s (97.72%)**
  - Scale-correct LARGE clean micro (`SF03` microbes 7.73s + `SF09` ChR2 7.75s — 2 SFs): **15.48s (1.79%)**
- **Remaining v7 base (`keep`)**: **4.20s (0.49%)** — ONLY:
  - `0.00–3.00s` (3.00s): brand `open_sting` (EigenLens logo sting)
  - `51.09–51.49s` (0.40s), `60.74–61.14s` (0.40s), `137.06–137.46s` (0.40s): three 0.4s transitions
  - **0.00s of old v7 narrative illustration segments remain.**

## Self-proof (OCR & Frame Inspection)
- Extracted 24 film frames across full timeline (`v8/review/_selfeval_2237/film_t*.png`) + inspected all 9 new styleframe PNGs/MP4s (`SF01–03/06–09/11–12`).
- **Tesseract OCR (`chi_sim+eng`) + visual check**: **0 matches** for `deferred`, `制作备注`, `多机位鼠板`, `非同一侧视循环`, `眼/装置写真板`, `三机位轮换·非插画头`, etc. (Earlier 22:09 build had production notes on SF08/SF11 chips; 22:32–22:37 rerender + 22:37 assemble completely eliminated them).
- Audio: `aac` stream verified on master (`864.708s`).

## Carl five-dim self-eval — **89.0 / 100 (< 95 gate) · DO NOT PUSH**
| 维 | 粗分 | 依据与差在哪 |
|---|---|---|
| 1 尺度美学 | **93** | 全片 23 个 SF（860.84s / 99.5%）已全部换完，旧 v7 叙事插画清零；宏观镜为 3D/写真鼠与眼装置，微观（SF03/SF09）为大画幅干净微观图，尺度对齐。仅差：仍是左画框+右信息卡的板式结构，非全画幅连续电影镜头。 |
| 2 主体质量 | **86** | 开场与尾段换上了多姿态/多角度（`awake_3d_tq` / `sleep_3d` / `still_awake_tq` / `eye_b/c`），消除了单侧视死循环；但全片核心长窗仍在复用有限的几张静态鼠/装置板（约 8–10 张底图），且 **C_03/C_04 笼箱写实毛发（cage-box photoreal fur）仍未通过 align-loop 真正落地**。 |
| 3 科学与旁白 | **93** | 全片旁白/字幕/科学边界（1979 Crick、ChR2、睡眠唤醒、假记忆仅限小鼠、ChrimsonR 护目镜绑定、监管边界）严谨对应；画面已 100% 清空 `deferred` 与制作备注。 |
| 4 运动与声音 | **85** | 原片 VO+音乐+音效 AAC 完整保留；但除 SF10 前半段外，其余近 14 分钟画面本质仍是**静态底图 + 轻微 Ken Burns 平移缩放 + xfade/hold**，缺乏真正的连续 3D 骨骼/物理动画。 |
| 5 可看完 | **88** | 14.4 分钟无硬伤、无备注穿帮、无旧插画断层，演播室卡片完成度高；但整片“左图右卡 + 静态底图 KB 轮播”的拼盘感仍在，距离 Branch Education / HHMI 级 95 分成片仍有代差。 |

**Mean: 89.0 / 100 (< 95 threshold) → Verdict: NEEDS_REWORK · 不上传 files.grolar-wage.ts.net · 不推 Carl。**

## Why < 95 & Next Knife Must Move What
虽然全片画面覆盖率已达 **99.51%**（叙事段 100% 脱离旧 v7 插画），但本质仍是 **“有限静态渲染图/写真底图的 Ken Burns 卡片拼盘”**，靠继续刷 2D 板子已触及天花板（~89 分）。下一刀若要冲 ≥95 门槛，必须动真格的 3D/连续镜头（按 ROI 排序）：
1. **真多拍连续动画（True multi-beat animation）**：把 SF10（18.98s，后半段仍是 `hold_last` 静帧克隆）以及 SF13/15/16/18/19 的核心英雄拍，用 Blender 渲出真正的连续动作拍（如睡眠呼吸→蓝光脉冲打入光纤→抬头苏醒迈步、双侧光纤笼内走动、离子通道构象开闭连续动画），替换静态 PNG 的 Ken Burns 平移。
2. **笼箱写实毛发（Cage-box photoreal fur align-loop）**：跑通 `ALIGN_LOOP_READY.md` 里的 C_03/C_04 笼箱写实毛发小鼠与实验笼具环境（含垫料、透明笼壁、双光纤旋转接头），替换 SF18/SF19 中抠图贴在纯色/木纹底板上的孤立鼠像。
3. **多机位 Blender 真全画幅静帧/运镜（Multi-cam Blender full-bleed shots）**：减少“左小框 + 右两张文字 chip”的 PPT 卡片占比，在关键章节（开场 SF01/07、SF10、SF18/19、SF21）导出 16:9 全画幅多机位 Blender 景深镜头（带实验室台面、光纤激光散射体积光、视网膜微距景深），破除整片同构卡片感。

## Paths & Cost
- Master: `/workspace/e2work/lowres_cut/E2_roughcut_v8_internal_20261023_2237.mp4` (`864.71s`, AAC)
- Share (local only, NOT uploaded): `/workspace/e2work/lowres_cut/E2_roughcut_v8_internal_20261023_2237_share.mp4`
- Notes: `/workspace/e2work/lowres_cut/E2_roughcut_v8_internal_NOTES.md`
- Probe dir: `/workspace/e2work/v8/review/_selfeval_2237/`
- RunPod: `pods=[]` GraphQL-confirmed · **$0 this round**
