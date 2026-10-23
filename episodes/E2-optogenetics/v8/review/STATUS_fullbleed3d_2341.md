# E2 internal rework — 16:9 Full-Bleed Multi-Cam 3D + Cage Environment · 2026-10-23 ~23:54 Asia/Shanghai

## Done (local CPU Blender + 8-worker full-bleed compositor · E2 pods=[] · $0)
1. **SF10 (~19.0s window: `161.07–180.05s`) — 100% Continuous 4-Camera 3D Animation (ZERO static hold)**:
   - Replaced the previous `5s motion + 2s hold + 12s static KB` (`HOLD_LAST_STEMS`) with a continuous 456-frame (`19.0s @24fps`) 4-camera 3D animation sequence:
     - **Cam A (`0.0–4.8s`, `sf10_gpu` 120f)**: C57 mouse in slow-wave sleep on dark wood-chip bedding → 470 nm blue fiber pulse turns on.
     - **Cam B (`4.8–9.8s`, `m6` 120f)**: Rigged `mouse_qwalk.glb` + Geometry Nodes Melanin hair (`mouse_v3.py`) — breathing spine → head lift → awakening and walking stride forward with bone-parented ceramic ferrule & slack optical fiber.
     - **Cam C (`9.8–14.5s`, `m5` 120f)**: Low-angle hero tracking shot following continuous walking stride across bedding.
     - **Cam D (`14.5–19.0s`, `envA` 3D cage)**: High-angle 3/4 view inside transparent acrylic experimental cage with corner posts & overhead commutator.
   - Removed `"SF10_mouse_tripo"` from `HOLD_LAST_STEMS` in `assemble_v8_roughcut.py` (uses `trim` on the full 19.0s source).
   - Verified frame-to-frame motion across the entire `161.5–179.5s` window in the assembled master (`71` quarter-second steps: `min_diff = 3.32`, `mean_diff = 10.00`, `zero_steps = 0`).

2. **True 3D Experimental Cage Environment (`blender/render_cage_multicam.py` → `renders/cage_3d/`) for SF18 / SF19 & Hero Chapters**:
   - Built full 3D experimental cage scene in Blender 5.2 (`CYCLES` + OpenImageDenoise + AgX) with rigged `mouse_qwalk.glb`, Geometry Nodes fur, bone-parented ceramic cannula + hooked slack fiber, transparent acrylic walls (`IOR=1.49`), aluminum corner posts, top cross-bar with rotary commutator joint, wood-chip bedding, and removable metal shock-grid rods:
     - `envA_0001..0032.png`: Transparent acrylic cage Context A (cool 470 nm ChR2 blue pulse, calm exploration, high-angle 3/4 camera).
     - `envB_0001..0032.png`: Conditioning chamber Context B (metal grid floor rods, warm amber chamber lighting + 470 nm blue fiber recall, opposite 3/4 camera with foreground post bokeh).
     - `nphr_0001..0032.png`: Transparent cage with 590 nm yellow/amber NpHR chloride-pump light inhibition.
   - Rebuilt **SF18 (`96.0s`)** and **SF19 (`88.0s`)** around these multi-cam 3D cage sequences + `m6`/`m5`/`m4` 3D walking shots, replacing the isolated cutout-mouse-on-flat-plate look.

3. **Broke the Homogeneous "Left Small Box + Right Two Chips" Layout Across All 23 Styleframes (`tools/cinematic_fullbleed_v8.py`)**:
   - Re-architected all 23 styleframes (`SF01`–`SF23`, `860.84s` / `99.51%` of runtime) to **16:9 full-bleed widescreen framing**:
     - Primary visual (3D mouse cage / 3D walking mouse / Goodsell molecular cross-section / retinal apparatus) fills the entire 16:9 frame with subtle top/bottom scrims.
     - Added sleek **cross-scale picture-in-picture magnifier insets** (`650,74 → 932,232`) with callout pointers linking microscopic molecular/circuit mechanisms (`chr2`, `orexin`, `brain`, `eye_inset`) directly to macroscopic in-vivo behavior.
     - Replaced bulky right-hand card stacks with lightweight translucent **top-left chapter HUD header** and **lower-left scientific HUD card** (strictly above `0.79H` / `620px` caption bar).

4. **Assembled New Internal Master & Share**:
   - Master: `/workspace/e2work/lowres_cut/E2_roughcut_v8_internal_20261023_2341.mp4` (`864.71s`, `280.4 MB`, `1280×720 @24fps`, **AAC audio verified**).
   - Share (local only): `/workspace/e2work/lowres_cut/E2_roughcut_v8_internal_20261023_2341_share.mp4` (`84.8 MB`).
   - Extracted 32 frames across full timeline (`v8/review/_selfeval_2341/film_t*.png`) and ran `tesseract` (`chi_sim+eng`): **0 hits** for `deferred`, `制作备注`, `多机位鼠板`, `非同一侧视`, `写真板`, `插画头`, `无人脸`.

## Carl Five-Dim Self-Eval (`ACCEPTANCE.md`) — **91.8 / 100 (< 95 gate) · DO NOT PUSH**
| 维 | 粗分 | 依据与差在哪 |
|---|---|---|
| 1 尺度美学 | **94** | 全片 23 个 SF 已全面升级为 **16:9 全画幅电影感构图 + 右上跨尺度放大镜小窗**（微观分子/脑回路 ↔ 宏观 3D 活体笼箱），彻底打破了旧版「左小框+右两张卡」的 PPT 拼盘感。 |
| 2 主体质量 | **90** | SF10/18/19 及多段英雄镜已换上带骨骼行走与 GN 毛发的 `mouse_qwalk.glb` / `mouse_c57.glb` + 透明亚克力笼箱/金属电击栅格/旋转接头 3D 场景（`m6`/`m5`/`m4`/`envA`/`envB`/`nphr`）；但长镜头中固定地面纹理与鼠爪接触仍有轻微滑步感，且视网膜/分子章节（SF03/08/09/11/20/21/22）主画面仍以 2D 高清插画运镜为主。 |
| 3 科学与旁白 | **94** | 旁白、字幕、HUD 角标与跨尺度小窗严格对齐（1979 Crick、ChR2、Orexin 睡眠唤醒、ChR2+NpHR 蓝开黄关、海马环境甲/乙假记忆仅限小鼠、ChrimsonR+护目镜部分视觉、6/10 与 4/8 分母及未获批监管边界），全片 0 `deferred`/制作备注。 |
| 4 运动与声音 | **90** | SF10 19s 窗口已实现 100% 连续四机位 3D 动作（0 静帧 hold）；SF18/19/13/15/16/23 嵌入了多段真 3D 行走与笼内运镜。但在 88s–120s 的超长章节（如 SF16/18/19/22/23）中，几段 3D 序列（每段约 32–120 帧，1.3–5 秒）仍需通过往返/切机位循环支撑长时窗，且分子/视网膜段仍缺真 3D 连续构象动画。 |
| 5 可看完 | **91** | 16:9 全画幅 + 轻量 HUD 使成片观感从「演播室卡片拼盘」跃升至准纪录片形态；但离 Branch Education / HHMI 级 95+ 成片仍差大约 3 分（主要在超长章节里 5 秒级 3D 镜头的重复率，以及分子孔道/视网膜光路尚未做成真 3D 连续动力学动画）。 |

**Mean: 91.8 / 100 (< 95 threshold) → Verdict: NEEDS_REWORK · 不上传 `aws-egress` · 不推 Carl。**

## Remaining Gap to ≥95 (Next Knife)
1. **分子与视网膜章节真 3D 连续动画（SF09 / SF15 / SF16 / SF11 / SF20 / SF21）**：用 Blender 渲染真正的 3D 脂双层 + ChR2 七次跨膜螺旋蓝光开孔阳离子流、BR 质子泵对照、以及护目镜 595nm 光脉冲穿过角膜/晶状体打亮视网膜神经节细胞层的连续 3D 镜头，替换目前这些章节中仍在使用的 2D 静态底图平滑推拉。
2. **扩充活体笼箱 3D 独立镜头池并消除滑步**：为长达 88–100 秒的 SF18/19/23 增加更多不同焦段与动作阶段的真 3D 渲染序列（如俯视全景笼箱、光纤旋转接头特写、环境甲探索 vs 冻结姿态静态微呼吸特写），避免 1.3–5 秒短序列在长章节内多次复现。

## Paths & Cost
- Master: `/workspace/e2work/lowres_cut/E2_roughcut_v8_internal_20261023_2341.mp4` (`864.71s`, AAC)
- Share (local only, NOT uploaded): `/workspace/e2work/lowres_cut/E2_roughcut_v8_internal_20261023_2341_share.mp4`
- Notes: `/workspace/e2work/lowres_cut/E2_roughcut_v8_internal_NOTES.md`
- 3D Cage Script & Frames: `/workspace/e2work/v8/blender/render_cage_multicam.py` → `/workspace/e2work/v8/renders/cage_3d/{envA,envB,nphr}_0001..0032.png`
- Full-Bleed Builder: `/workspace/e2work/v8/tools/cinematic_fullbleed_v8.py`
- Probe dir: `/workspace/e2work/v8/review/_selfeval_2341/`
- RunPod: E2 `pods=[]` (`$0` spent this round; E1 pod `z9355v69oq8cgm` untouched)
