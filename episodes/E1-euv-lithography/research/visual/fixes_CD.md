# C/D fixes for the lead: changes in files the C/D agent does not own

Written 2026-10-22 alongside the code fixes in `blender/shots/c_scenes.py`, `d_scenes.py`, `mograph/cd.py`,
`b1_source.py` (CamD_09 line + the D_08/D_09 branch only) and the C_/D_ lines of `registry.yaml`. Sources are the
S-numbers of `research/visual/CD_sources.md`. Nothing below has been applied; each item says where it goes.

## 1. Narration (script_zh.md AND storyboard/parts/*.yaml, then tts → vo_align → retime → asr_check)

All three lines are in segment C, so one C re-voice covers them (`tts.py --segments C`).

| Shot | Old line | New line | Why |
|---|---|---|---|
| C_04 | 六面镜子把图形缩小，投向晶圆； | 投影物镜把图形缩小，投向晶圆； | No EXE mirror count in text anywhere (ZEISS 2024 gives none; the six are "design examples", S6 s.35); WORKFLOW 2.5 "旁白里不说 EXE 的镜片总数". **Re-voice.** |
| C_04 | 狭缝扫过，掩模和晶圆反向飞驰； | 狭缝扫过，掩模和晶圆同步飞驰； | The only source for "opposite" is a 1998 Nikon KrF (DUV, refractive) patent (S9); ASML's High-NA slide has double-headed arrows only (S6 s.34). "同步" is true for every scanner. **Re-voice.** |
| C_06 | 这一切，每秒最多发生 5 万次。 | 这样的一滴锡、一束光，最新的光源每秒要重复 6 万次。 | F2: "60,000 times per second in our latest commercial sources" (S2); no 最多; the rate is the droplet/pulse rate, not "一层电路" per pulse (audit C_06). **Re-voice.** |

Timing note for C_06: `c_scenes.pulses()` lets the flashes fuse into one band at shot frame 84 (3.5 s), i.e. just
after "万次" in the current take. If the new line ends later, move the fusion: the launch loop (`while t < 84`) and the
strength key at 84 → the frame of "次" + 4. The C_04 beats (light on the wafer by "投向晶圆" ≈ 4.0 s, stage race
4.7–8.2 s, slit scan 8.6–11.7 s) only need a check after the re-voice; the line lengths barely change.

## 2. Storyboard overlays / visual text (storyboard/parts, then merge; I did not touch storyboard/*.yaml)

- **C_01** visual: drop "最后一块咬合时，白模表面开始长出真实金属材质" (not built; the take stays clay) — or keep it as a
  wish, but it is not in the render. Camera notes: "环绕后推近到光源舱体（+x 侧）".
- **C_02** overlays: the single label shows 0.4–5 s only, so "13.5 nm" disappears before "13.5 纳米" (7.45 s). Either drop
  `13.5 nm` here (B1 already showed it) or use the per-overlay timing proposed in §4.
- **C_03** overlays (if §4 lands): `中间焦点 IF · 示意` at: 1.2; `可动分面镜 · 示意` at: 4.1. Visual text: replace
  "成百上千块小镜片同时翻转，把光打散再拼成一条均匀的弧形光带" with "分面镜把光分成许多小束，再叠加成一条均匀的弧形光带，照到掩模上是一条弧形狭缝（示意）"
  (facet count not public, no per-pulse flipping, S5 s.13); replace "光束横截面里出现 SKY130 线条" with "反射回来的光带上电路图形（通用线条，示意）";
  builders: drop `pdk_patterns.sky130_tile`.
- **C_04** overlays: `6 面镜 · 缩小 4×` (F7, F11) → `投影物镜 · 缩小 4×/8×（扫描方向 8×）` with facts **[F12]** (EXE: S4 s.9, S5 s.11;
  F11 is the NXE). `光的账本：到达晶圆约 1%` → `光的账本：到达晶圆只剩约 1%（教材估算 · 示意）` (F33 is a 0.33-NA textbook estimate; S8:
  High-NA transmission is higher). Visual text: "在六面镜之间折返" → "在投影物镜的反射镜之间折返（设计示例 6 面，M6、M5 中心开孔）"; "以发光轮廓反向飞驰" →
  "以计量青轮廓同步扫描（掩模走的距离是晶圆的 8 倍）"; add "贴近晶圆时，光从 M5 的中心孔穿下，汇成 26 × 1.6 mm 的弧形狭缝；晶圆在狭缝下扫过，一个 26 × 16.5 mm
  的曝光场里留下潜像（示意）；随后步进到下一个场". `fx: photon rain` is not built (the latent field fills in behind the slit instead).
- **C_05** camera notes: ends on the whole-machine side view (all of the path, collector to wafer, in frame).
- **C_06** overlay `最多 50,000 次 / 秒` → `每秒 6 万次 · ASML 最新商用光源` (F2). Visual: counter → "60,000 / s".
- **C_07** visual: "锡滴爆成等离子体；收集镜虹彩表面；掩模台急停；晶圆上的潜像亮起" → "主脉冲点燃等离子体（B1_13）；收集镜被等离子体照亮（B1_15）；
  掩模台和晶圆台按 8:1 扫描（C_04）；狭缝后潜像写出（C_04）". The inserts are read from whatever render of those shots exists:
  **re-render B1_13, B1_15 and C_04 before C_07.**
- **C_08** visual: "镜子（虹彩）" → "镜子（蓝色光环：收集镜、折转镜、两块分面镜、M1–M6，共 10 面）"; "光源（激光橙 + EUV 紫）" is what is built (orange drive
  laser through the collector's central hole, violet plasma).
- **C_10** camera notes: "从整机侧视缓推向等离子体，余烬最终落在画面中心（与 D_08 锡滴位置一致）".
- **D_01** visual: "一只晶圆盒从一台机器的装载口缓缓滑出，被头顶轨道上的搬运车吊起带走；身后同样的晶圆盒一个接一个" →
  "晶圆盒停在装载口（托板离地约 900 mm）上，与机台脱开几厘米，头顶轨道上的搬运车放下吊带夹爪，夹住盒顶的把手法兰把它吊起带走；轨道上每个晶圆盒都挂在自己的搬运车下"
  (S15; the FOUP never comes out of the machine).
- **D_02** visual / builders / style: the dive is into the AMD Zen 5 CCD die photo (chips.md), not a grey SEM SKY130 array.
  Keep the `1840 亿个元件` overlay out of the picture (2D shot; WORKFLOW 1.2).
- **D_04** overlays: `每片晶圆能耗：自 2018 年以来 −57%` → `NXE 每片晶圆每次曝光的能耗：12.8 → 5.5 kWh（−57%）` (S1, "energy per wafer pass").
- **D_05** visual / overlays (the record still says 600 W / 原理样机): visual → "三个一手数据点连成折线：约 250 W（2023 年客户现场，ASML SPIE 2023）→
  NXE:3800E 超过 500 W（ASML SPIE 2024）→ 2025 年演示 1000 W（ASML 2025 年报；最后一段虚线：演示，不是量产），止于 1000 W，不再往上画"; overlays →
  `NXE:3800E 超过 500 W`（F4c）/ `2025 年演示 1000 W`（F4c）; camera `tilt-up` → `static`.
- **D_06** visual: "像一块黑色方碑" → "一块黑色体块，比例接近双层巴士（约 10 × 3.2 × 4.5 m，示意；Intel："as big as a double-decker bus"）".
- **D_07** overlays: add a second overlay `各地区数量据 ASML 2025 年报；地区内位置为示意` (facts: [F50]); the texture was regenerated from the
  current `mograph/a0.py` REGIONS (1,600 NL / 700 rest of EMEA / 1,350 North America / 1,450 Asia, S1 p.239), same as A0_06.
- **D_08** camera notes: "start 6（跟拍从静止起步的第一帧会糊）".

## 3. facts.yaml

- **F57** (used by B8 and C): the claim states "反向" and "4 倍" as universal, from a DUV patent. Proposed:
  - claim: `步进扫描：光被整形成一条狭缝，掩模台与晶圆台同步扫描；NXE（4 倍缩小）掩模速度是晶圆的 4 倍，EXE 扫描方向是 8 倍；扫完一个曝光场再步进到下一个`
  - values: `{reticle_to_wafer_speed_nxe: 4, reticle_to_wafer_speed_exe_scan: 8}`
  - add source https://euvlitho.com/2021/P52.pdf (Wischmeier et al., ZEISS/ASML, EUVL Workshop 2021, slide 11: "βscan = 1/8, βx-scan = 1/4")
  - notes: `"反向"只见于 DUV 专利（Nikon US 5,831,716, KrF 248 nm 折射式）；EUV/EXE 的相对扫描方向没有公开原文（ASML van Schoot 2021 第 34 页两个双向箭头）。旁白说"同步"，不说"反向"。Design News 为 C 级，删除。`
- **F12**: add https://euvlitho.com/2024/P22.pdf with quote "Anamorphic lens design: 4× reduction in non-scan direction, 8× reduction in
  scan direction" (Kaumanns et al., ZEISS, EUVL Workshop 2024, slide 9); segments add `C`.
- **F7**: segments add `C, D`; notes add `EXE 不说镜片总数（只有"设计示例"图）；D_03 的"约 10 面"按教材`.
- **F33**: notes add `0.33 NA 时代的教材估算；High-NA 中心遮拦设计透过率更高（Heil et al., ZEISS, EUVL Symposium 2015, slide 20: "significantly higher optics transmission vs. 3300"）。屏幕写"教材估算"。`
- **F4c**: D_05 now shows the 2023 starting point. Add quote "Sources at customers operate at ~250 Watt power" (Umstadter et al., ASML,
  Proc. SPIE 12494, 124940Z, 2023, https://doi.org/10.1117/12.2657772) and value `customers_2023_w: 250`.
- Optional new fact (visual only, no on-screen number yet): `EXE 曝光场 26 × 16.5 mm（半场）；晶圆处狭缝为 26 × 1.6 mm 弧形，掩模处 104 × 12.8 mm`
  — https://euvlitho.com/2022/P3.pdf slide 12 ("0.55NA prints a Half Field") and https://euvlitho.com/2021/P52.pdf slide 11. C_03/C_04 draw
  these sizes.

## 4. Files other agents own

- **edit_film.py: chapter cards.** `label_for` drops `kind: chapter`, so C_01 (章节 · 总装：跟着一滴锡走完全程) and D_01 (章节 · 收束：回到那一滴锡)
  never appear. Proposal: draw them in edit_film as the B1_01 card does, lower left over the 3D picture: "章节" 34 px INK2 at (160, 470),
  the title 96 px INK with weight glow at (160, 520) (`总装` / `收束`), the subtitle 34 px VIOLET at (164, 650) (`跟着一滴锡走完全程` /
  `回到那一滴锡`), a 3 px violet rule growing under the title, shown 0.2–2.8 s with a 0.5 s fade, on a soft dark gradient on the left
  third so it reads over the clay (C_01) and the yellow room (D_01). Then the shot's normal label as now.
- **edit_film.py: per-overlay timing.** One label per shot from 0.4 to 5 s cannot follow the narration in the long take. Proposal: an optional
  `at: <s>` on each overlay; overlays with `at` get their own label from `at` for up to 5 s (one at a time, the next replaces the previous).
  Values: C_02 `锡滴 ≈ 25 μm` at 1.2, `单独成像 · 单独瞄准` at 2.0, `13.5 nm` at 7.4; C_03 `中间焦点 IF · 示意` at 1.2, `可动分面镜 · 示意` at
  4.1; C_04 `投影物镜 · 缩小 4×/8×` at 1.2, `光的账本…` at 8.6.
- **b1_source.py CamC_02** (not mine): the last key aims at (-2.2, 1.5, 0.6), so C_02 ends on plasma fog and a port, not the collector. Proposed
  last key `(300, (-2.4, 0.0, 0.0), (4.2, 2.6, 1.4), 35, 4.0)` so the lit collector (apex x = -4, rim x = -0.35, facing +x) fills the end
  frame and C_03 (which now opens on the machine-scale collector from the IF side) continues it.
- **sample_b1.py** (shared constant, audit_B1 B1_10 / audit_C C_02): the sheet still drifts only along +x; key it +y by 1.6–2.4 units between
  T_PRE and T_MAIN and aim the main pulse there.
- **A0_01 has the same two defects I fixed for D_08/D_09** (b1_source `_cold_open`, shared): (1) the droplet flies through the `SoftBack` softbox
  (12 × 4 m at (-3, -10, 1)) around sim 15–25; close up its dark falling-off edge fills half the tin as a black disc (visible in A0_01 sample
  frame ~10) and the camera crosses the card; (2) the `BokehLED` spheres sit right beside the droplet and read as a second droplet (A0_01
  sample frames 126–133). D_08/D_09 now hide SoftBack, the bokeh LEDs and the unlit beams in `_closing_droplet()`; A0_01 needs the lead's call.
- **build_machine.py gotcha** (for every agent): `_box` calls `bpy.ops.object.transform_apply(scale=True)`, whose `location` and `rotation`
  default to True as well, so every box-built part (ReticleStage, WaferStage, Base, panels…) has its origin at the world origin. Offsets
  relative to `obj.location` land at z = 0; use the BM constants for centres (I hit this in C_04/C_08).
- **storyboard.timed.yaml was briefly unparseable** (2026-10-22 00:56, fixed by ~01:05): line 5180, B6 overlay `Indistinguishable from magic: the EUV
  pellicle · ASML, 2022` had an unquoted `: `; render_storyboard.py and mograph.py fail on that. Worth a yaml.safe_load after every
  storyboard merge (WORKFLOW s.9).

## 5. Registry changes made (C_/D_ lines)

- C_04 `start: 411` → `431` (C_03 covers sim 1–419; the old start overlapped it by 9 frames).
- D_08 `start: 4` → `6`.
- D_09 `start: 42` → `90`, added `step: 0.155` (58 rendered frames cover sim 90–98.8, the pre-pulse closing in; 2 black frames).
