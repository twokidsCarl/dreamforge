# A1–A3 visual fixes, 2026-10-22: what changed and what still needs a decision

This file follows research/visual/verify_A1-B1.md and audit_A1/A2/A3.yaml. Code changes are in:
- blender/shots/a1_scenes.py
- blender/shots/a23_scenes.py
- mograph/a1.py, a2.py, a3.py
- registry.yaml (one change: `A1_07 start: 181 → 191`)

Everything below was checked on single sample frames (960×540), not on full-shot renders. Every A1–A3 shot needs a full re-render before the audit rows can be marked verified.

## 1. Proposed storyboard changes (`storyboard/parts/p1_A0-B1.yaml`; the timed file follows)

| Shot | Field | Now | Proposed |
|---|---|---|---|
| A1_01 | visual | 晶圆边缘的虚焦反光，慢慢对焦 | 晶圆边沿的虚焦衍射色带，两端在画面内渐隐，慢慢对焦 |
| A1_03 | visual | 边缘甩出细丝 | 胶液先在中心堆成小圆丘，随转速升高摊开到边缘、再甩薄成一层带边缘微凸的薄膜，边缘甩出细小液滴；晶圆边上是一个 V 形定位缺口 |
| A1_04 | visual | 图形的影子投在下方的光刻胶层上 | 光穿过掩模后经一枚缩小镜头（示意）会聚，图形缩小 4 倍落在光刻胶上，被照区域泛起荧光。The word 影子 should go: the picture is now a reduction projection. |
| A1_05 | camera.notes | 扫描线自上而下重绘一次 | 被照区域在整个胶厚内同时浮现（薄胶近乎均匀曝光） |
| A1_05 | fx | scanline | delete |
| A1_06 | visual | 沉积，金属填进沟槽，余胶被剥离 (old order, from the audit) | 显影 → 刻蚀 → 去胶 → 沉积（金属盖满并填进沟槽）→ 抛光，只在沟槽里留下导线 |
| A1_07 | visual | — | add: 每层截面上都露出导线或通孔（一层是长条，一层是点），越往上层越厚、线越粗 |
| A1_08 | overlay | 最多约 100 层图形 | 上百层图形 |
| A1_08 | visual | 计数器滚到约 100 | 计数器滚到“上百层” |
| A1_09 | visual | — | 最底部的那几层（约 8 层，中间夹着非 EUV 层）染成 EUV 紫 |
| A1_11 | visual | 真正的电路版图 | 电路版图（示意） |
| A2_04 | visual | — | 左边：波长标尺逐段缩短（路线一）；右边：镜头随光锥半角 θ 张大而变宽（路线二） |
| A2_05 | visual | 笔杆印着“193 nm 深紫外 DUV” | 笔杆印着“193 nm DUV（浸没式）” |
| A2_05 | overlay | 单次曝光极限约 40 nm | no change; it is now drawn in the picture as a corner footer |
| A2_06 | visual | — | add: 图例固定在工序条左上方 |
| A3_04 | visual | 暗色摄影棚……一面泛着彩虹干涉色的多层膜反射镜 | 真空腔内（钢制腔壁、法兰与观察窗）：光学玻璃透镜在换镜滑台上，紫光射入即被吞掉，入射点一圈暖色辉光；滑台移动，一面素净银亮的多层膜反射镜换到光路上，入射角约 12°，光束以 24° 折返，亮度约为入射的七成 |
| A3_04 | fx | thin_film_iridescence, caustics | delete both |
| A3_05 | fx / camera.move | whip pans, film_grain, light_leak | 硬切 (hard cuts). Neither the shot nor edit_film draws whip pans, grain or leaks. |
| A3_05 | overlays | 17 年, 投入 60 多亿欧元, partners | Keep only `ASML · 蔡司 ZEISS · 通快 TRUMPF 等伙伴` with `at: 5.9` (when the narration reaches 联合蔡司、通快). See note A3_05 below. |
| A3_06 | visual | 洁净室里那台机器被扫描光带扫过，外壳变成幽灵玻璃 | 从切入起即为透明剖视；紫线从收集镜出发沿光路依次点亮，光源、照明、掩模台、投影物镜、晶圆台在光到达时泛起紫光；最后镜头拉开，整条光路同在画面内 |
| A3_07 | camera.notes | 左侧沿用 A3_06 最后一帧并压暗 | 开场即 A3_06 最后一帧，约 1 秒内压暗（全画面） |

**A3_05 note.** The time bar (1 → 17 年, bottom) and the euro counter (投入 0 → 60 多亿欧元, upper left) are now rendered inside the shot. If the overlays stay as they are, edit_film also draws `17 年 / 投入 60 多亿欧元` upper right for 5 s, so the numbers appear twice.

## 2. Facts (`facts.yaml`)

- **A3_05 partners.** Add an entry for ASML · 蔡司 · 通快 等伙伴 and point the overlay's `facts` at it. Sources:
  - ZEISS EUV page: "together with strategic partner ASML, TRUMPF, the Fraunhofer Institute IOF and around 1,200 other partners"
  - TRUMPF drive-laser page: "ASML, Zeiss, and TRUMPF joined forces"
- **F1.** Add ASML's wording "EUV light occurs naturally in outer space…", which supports the narration 地球上没有现成的…. This is carried over from the verification pass and is still open.
- No new numbers were introduced.

## 3. New or changed audit rows to record (audit yamls not edited here)

### A1
- **A1_02**
  - Substrate and three films now have four distinct clay tones: cool dark grey, sand, blue-grey, rose.
  - A dark inset seam separates each pair of layers.
  - The layers carry role `emitter` so the clay style keeps their material. → glitch fixed.
- **A1_03**
  - The notch is a V cut into the rim (boolean), not a raised cube. → wrong fixed.
  - The spin and camera keys run past the shot end (length read from storyboard.timed.yaml), so nothing freezes.
  - The resist is a lathe mesh:
    - it starts as a dome puddle (shape key);
    - it spreads to the rim by f106;
    - it thins to 0.22 × by f150, with a wetting meniscus and a faint edge bead.
  - Droplets now fly off only after the film reaches the rim (f104 onward), two every 3 frames.
  - The wafer's edge-split modifier now runs after the boolean, which removes the bent reflections.
  - The yellow strips were moved low and far so the mirror wafer actually reflects them.
- **A1_04**
  - 4× reduction: below the mask the beam converges from 4.0 to 1.0 wide, and the latent pattern is a quarter of the mask pattern.
  - A single lens outline (thin glowing mount ring) stands for the projection optics. New row: **simplified**. Sources: S10 p2 (stepper reduction optics), S4 (ASML 4×). B7 shows the real mirror train.
  - The beams are open tubes with no glowing lids.
  - The camera ends at a high three-quarter view outside the beam, showing the mask pattern, the converging light and the small glowing print. The last key drifts linearly to the end.
  - The resist is a dim amber slab.
- **A1_05**: the columns fade in through the full thickness at once; no scan line (mograph/a1.py).
- **A1_06**
  - The trench metal has `hide_render` until f122 and the blanket overburden until f123.
  - After develop (f56) and strip (f119), the resist is hidden, as is the overburden after CMP (f175), so no slivers are left on the film top.
  - The camera keys end past the shot.
- **A1_07**
  - Moved to sim frames 191–341 (registry start 191). Before, its first layer appeared during the last frames of A1_06.
  - 12 levels. Each shows metal on the front cut face:
    - along-x wire levels have one line on the face, a long gold bar;
    - along-y levels end on the face as dots;
    - via levels have 3 vias on the face.
  - The levels thicken and coarsen upward.
  - The exposure flash is the saturated EUV violet at 1.6, sized exactly to the slab.
  - The camera ends with the whole column in frame.
- **A1_09**
  - 8 EUV levels {0, 1, 3, 4, 5, 7, 8, 10} among 60, with grey levels interleaved.
  - They are solid matte, emission (0.30, 0.06, 1.0) at 1.0, low specular.
  - Max pixel 226, nothing clipped.
  - Bottom levels are thicker so the bands read.
  - The camera starts with the whole stack in frame and ends on a three-quarter view of the bottom.

### A3
- **A3_04**
  - Inside a steel vacuum chamber: stiffener rings, CF ports with bolt circles, two lit viewports, an end-cap beam inlet. → closes the open-air wrong.
  - The lens is clear glass against the lit wall, rendered with more Cycles transmission/glossy bounces (`after_style`).
  - Beams are saturated violet (0.30, 0.04, 1.0): 1.3 incoming, 0.91 reflected (0.7×).
  - Beams are invisible to glossy, transmission and diffuse rays, so no violet glint "inside" the lens or in the waiting mirror.
  - The beam grows from the inlet with an end-anchored rod: no dot at f1.
  - The beam end is keyed per frame: lens surface → mirror face. The mirror sits 0.6 along the beam on a linear stage with the lens, so the axis is never uncovered during the swap (f96–124).
  - The warm ring is hidden from f97.
  - Camera on the reflecting side.
  - The lens ring and the mirror (post plus clamp) are mounted on the carriage.
  - AOI changed from 25° to 12°, which updates the "simplified" row. Reflection reads mildly dimmer than the incoming beam, not strongly.
- **A3_05**
  - `motion_blur_position = START`, and camera, aim and lens keys all use CONSTANT interpolation at the cuts. Sample frames 65, 130 and 195 are clean.
  - DOF off for this shot (the overlay rig rides on the camera).
  - Laser hall: floor 90×40, back, front and end walls, ceiling, panel seams.
  - Time bar: 17 ticks with a violet fill from f8 to f232, and the readout `n 年` rides the head, ending at `17 年`.
  - Euro counter (upper left, opaque plate): counts 0 → 59 亿欧元 over f96–130, then holds `60 多亿欧元`.
  - New row: **artistic**. The count-up values in between are animation, not a spending profile. Years are relative (ASML gives no start year).
- **A3_06**
  - The path bevel is mapped by length and drawn linearly f1–125.
  - Each module (SrcDrum, Illuminator, ReticleStage, POBarrel, WaferStage) gets a soft violet glow as the light reaches it. New row: **artistic**.
  - The camera follows source → illuminator → reticle/PO, then pulls back. The last frame (157) shows the whole path, source to wafer, with the reticle in frame.
  - The collector disc item belongs to build_machine (shared), which was fixed in 0dd7f35.
- **A3_07**: frame 1 is A3_06's last frame and darkens within about 1 s. `mograph/a3.py` `SRC_XY = (1470, 525)` was measured on sample A3_06/0157; re-measure on the final render.

## 4. Not done / open

- **A2_07**: the storyboard's ending (the short-wave "pen" draws a much finer line) is not drawn.
- **A2_01**: the fan keeps the deliberate 1.4× angle simplification.
- **A2_08**: no code change. A sample f22 re-render shows the ribbon without colour fringes.
- **A3_04**: a 真空中 · 示意 tag is no longer needed now that the chamber is visible. Add it to the overlay only if a reviewer still reads the scene as open air.
- **Full re-renders needed**:
  - A1_02, A1_03, A1_04, A1_06, A1_07, A1_09, A3_04, A3_05, A3_06;
  - all A1/A2/A3 mograph shots, because the shared Canvas text changed;
  - then A3_07, after the final A3_06.
