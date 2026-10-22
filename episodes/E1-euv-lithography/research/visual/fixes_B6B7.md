# B6 / B7 visual fixes: what changed in code, and what the lead still has to apply

Written 2026-10-22 against `audit_B6.yaml` and `audit_B7.yaml` (sources: `B6B7_sources.md`). The code changes are in
`blender/shots/b6_scenes.py`, `blender/shots/b7_scenes.py`, `mograph/b6.py` and `mograph/b7.py`. `registry.yaml` needed
no change, because every camera and start frame still matches the timed durations. Every shot was checked with single
test frames at sample quality (in `$CLAUDE_JOB_DIR/tmp/r`, not in `renders/`). **No full-shot renders were made. All of
B6 and B7 must be re-rendered.**

Sections 1–4 are the changes for the lead to apply (narration, storyboard text, facts.yaml, files I do not own).
Section 5 is the per-shot record of what the code now does.

---

## 1. Narration changes (script_zh.md and p2_B2-B6.yaml / p3_B7-D.yaml together, then tts → vo_align → retime → asr_check)

| Shot | Old line | New line | Why / priority |
|---|---|---|---|
| B6_12 | 掩模上方还罩着一层保护膜，叫 pellicle，只有 13 纳米厚， | 掩模的图形面前还罩着一层保护膜，叫 pellicle，只有 13 纳米厚， | **Required.** ASML: "just below the reticle", and the reticle faces down. "图形面前" is true in any orientation. The B6_12–14 picture shows the reticle face up, as in Brouns Fig. 3. Re-voice. |
| B7_01 | 从掩模反射出的光，进入投影物镜——由六面反射镜组成。 | 从掩模反射出的光，进入投影物镜——一组弯曲的反射镜。 | **Required.** The six-mirror count is published for the NXE only (ZEISS); no text gives a count for the EXE (WORKFLOW 2.5). The shot shows the EXE optics. Re-voice. |
| B7_02 | 它把图形缩小 4 倍，投向晶圆。 | 现役 NXE 把图形缩小 4 倍，投向晶圆。 | **Strongly recommended.** B7_02 now shows the NXE and EXE designs side by side, so "它" is ambiguous and isotropic 4× is NXE-only (EXE is 4×/8×, B7_10). If it is not re-voiced, the graphic's "NXE" label is the minimum fix. Re-voice. |
| B7_11 | 入射角从 6 度降到 5.4 度，两只光锥恰好错开； | 扫描方向的光锥细了一半，入射角还能从 6 度降到 5.4 度，两只光锥恰好错开； | Recommended. It is halving the cone (8×) that separates the cones; lowering the angle narrows the gap (ZEISS 2024 s.9; B6B7_sources D). The new line is longer, so retime. If it is not re-voiced, the overlay below carries the point. |
| B6_03 | 有图案的地方反射光，吸收层的地方把光“关掉”。 | 吸收层上刻出图形：开口处反射光，留下吸收层的地方把光“关掉”。 | Optional (`simplified`). The overlay fix below is enough. |
| B6_15 | 灰尘落在膜上，离开了焦点，就印不出来。 | 小颗粒落在膜上，离开了焦点，就印不出来。 | Optional (`simplified`; Brouns p.221: larger particles still matter). The graphic already reads "小颗粒离焦". |
| B7_16 | ……却也让描述镜头误差的标准数学工具失效了—— | ……却也让描述镜头误差的标准数学工具不再适用—— | Optional (`simplified`; ASML says "replaced"). |

---

## 2. Storyboard text changes (storyboard parts; shot id: old → new)

### B6
- **B6_01**
  - style_why "掩模的图案在光下泛着虹彩" → "掩模的图形区在光下呈现明暗不一的功能块".
  - visual "表面的电路图案在侧光下折射出彩虹般的衍射色带" → "镜面般的图形区在侧光下显出一块块明暗不同的功能区和芯片之间的切割道（没有彩虹：EUV 掩模的图形周期太细，看不到可见光衍射色）".
  - camera notes "微微转动带出衍射色" → "微微转动带出镜面高光".
  - fx: drop `diffraction_iridescence`.
- **B6_03**: overlay "反射 = 亮 · 吸收 = 关" → "开口 = 反射 · 吸收层 = 关".
- **B6_04**: overlay "入射角 ≈ 6°" → "NXE：入射角 ≈ 6°". This is drawn in the graphic too.
- **B6_09**: overlay "1 颗颗粒 → 每一颗芯片 · 良率损失 100%" → "1 颗颗粒 → 每一颗芯片 · 满场芯片良率损失 100%". This is drawn in the graphic too.
- **B6_10**: add overlay "机械手外形示意". The motion trails and the 1,000,000 counter are still post-overlay work.
- **B6_12**
  - visual "掩模上方一圈边框撑起一张近乎看不见的薄膜，只在掠射角泛出淡淡的虹彩" → "掩模图形区前方，四个小支座托起一圈低矮的框架（与掩模之间留一道细缝），框上绷着一张近乎看不见的矩形薄膜，只在掠射角泛出一层淡淡的反光".
  - fx: drop `thin_film_iridescence`.
  - Keep the overlay "支架与间距示意".
  - The 13 nm vs 13.5 nm side-by-side is still a post overlay.
- **B6_13**: add overlay "暗红辉光为示意（500 °C 时肉眼几乎看不到）".
- **B6_14**
  - visual "干涉色带缓缓流过表面" → "微弱的暗红辉光缓缓起伏，镜面高光沿膜面滑过".
  - fx: drop `thin_film_iridescence`.
  - Optionally change the overlay to "13 nm · 500 °C（发光示意）".
- **B6_15**: overlay "离焦 → 印不出来（示意）" → "小颗粒离焦 → 印不出来（示意）". This is drawn in the graphic.
- **B6_16**: overlay "The EUV pellicle — indistinguishable from magic · ASML, 2022" → "Indistinguishable from magic: the EUV pellicle · ASML, 2022". This is drawn in the graphic.
- **B6_17**: visual "射进下方投影物镜的幽灵玻璃外壳里" → "从光瞳复眼镜射上掩模、再反射进下方投影物镜的 M1、M2（High-NA 光路）".

### B7
- **B7_01**
  - Overlays: delete "投影物镜：6 面反射镜" (no EXE count). Replace "M1–M6 排布示意（非真实设计）" with "按 ASML / ZEISS 公开设计示例绘制（示意）".
  - visual → "掩模反射下来的 EUV 紫光进入投影物镜：上半部 M1–M4 在窄柱里折返，光束穿过大末镜 M6 中心的孔落到贴近晶圆的小镜 M5，再反射回 M6，最后一只宽光锥穿过 M5 的孔汇聚到晶圆。光每到一面镜子，镜缘亮起一圈紫光。浅灰棚拍背景、幽灵玻璃外壳（外壳示意）。"
  - Drop "Mo/Si 膜就亮起一圈虹彩".
  - facts: drop F7 from this shot if the narration is re-voiced.
- **B7_02**: the shot is now the NXE vs EXE blueprint (van Schoot 2021 s.35 traced).
  - visual → "蓝图并排画出两份公开设计示例：左 NXE（NA 0.33），右 High-NA EXE（NA 0.55），掩模在上、晶圆在下，紫色半透明光束逐段画出；NXE 一侧，掩模上的一段图形以 1/4 大小落到晶圆，标“缩小 4×”。"
  - overlay "缩小 4×" → "NXE：缩小 4×".
  - Add overlay "设计示例 · ASML / ZEISS". It is drawn in the graphic.
  - builders → `mograph b7.po_compare`. engine: mograph.
- **B7_05**
  - visual → "夜色停机坪：一台平板挂车载着一只白色铝框、倒角顶的运输箱缓缓驶过，箱体侧面印着“2023.12”；背景里一架货机抬起机头、剪叉式升降平台车停在机头下，湿地面反着灯光。不出现任何标志和涂装。"
  - sfx "叉车液压声 / 集装箱门关闭的金属回响" → "卡车低速驶过的柴油声 / 远处货机 APU 的嗡鸣".
- **B7_06**
  - overlays "High-NA 投影光学（外形示意，人形为比例参考）" + "外形示意" → "High-NA 投影物镜（外形示意 · 尺寸未公开）" and "约 12 吨 · 4 万多个零件（ZEISS）" (F18).
  - visual → "纯白哑光的 High-NA 投影物镜模块（照 ZEISS 公开渲染图的外形：宽而矮的棱角框架、下部斜面、窄底座、顶部线缆）在浅灰棚里缓缓转动". There is no human figure.
  - style_why: drop "加一个人形比例尺".
  - camera notes: drop "爆炸峰值时".
  - fx: drop `explode_stagger`.
- **B7_09**
  - fx: drop `chromatic_dispersion` (13.5 nm light is narrow-band).
  - visual: the mask is now above, face down, with the cones below (consistent with B7_07/08 and the machine). The "示意" overlay stays.
- **B7_11**: overlays "入射角 6° → 5.4°" → "扫描方向光锥减半（≈3.9°）· 入射角 6° → 5.4°", and add "角度放大示意".
- **B7_13**: overlay "掩模图形：扫描方向拉长 2×" stays. The graphic now also says "掩模和图形区：尺寸不变" and "只装得下半个场".
- **B7_14**
  - visual → "真空腔幽暗中，上方一面巨大的凹面镜（M6）镜面朝下、中心开孔；下方贴近晶圆处一面小镜（M5）镜面朝上、也开孔。镜头从侧面绕到下方，沿光轴仰望：两面镜子的孔对成一线。"
  - Drop "Mo/Si 膜层泛着淡淡的虹彩".
  - fx: drop `thin_film_iridescence`.
- **B7_15**: visual → "镜头顺着从 M4 来的细光束下降，穿过 M6 中心的孔；光落到 M5 的镜环、反射回 M6，再从 M6 的整圈镜面汇成一只宽光锥（半角约 33°，中心空心），穿过 M5 的孔收束到晶圆上的一点。最后在下方仰望：两道环形镜对齐。"

---

## 3. facts.yaml changes

- **F14**: add the imec source for the absorber part, which the ASML page never mentions.
  - Source: Philipsen et al. (imec), EUVL Workshop 2021, https://euvlitho.com/2021/P11.pdf
  - Slide 2 labels: "Ru cap", "Mo/Si ML mirror", "Absorber". Slide 8: reference TaBN absorber "Thickness ~ 60nm".
  - Note: the absorber part is grade B (imec); keep A for the multilayer part (ASML: "reticles are multilayer reflectors that use interference to reflect light from the pattern").
- **F52**: grade B → **A**. The source is ASML (van Schoot, EUVL Workshop 2022, slide 14: "188 half fields per wafer").
- **F7**: add a note: "6 面仅为 NXE（0.33 NA）的公开数字（ZEISS）；EXE 无文字来源，旁白不得用于 High-NA（WORKFLOW 2.5）". segments: B7 only if the B7_01 line keeps a count.
- **F40**
  - Add source ASML van Schoot 2021 https://www.euvlitho.com/2021/P3.pdf slide 34: "Exposure Chief Ray Angle (~5.3°)", "Image field size at reticle level (104 x 132 mm)" (unchanged vs 0.33 NA).
  - Add a note: "光锥分开靠的是扫描方向 8× 让光锥减半（asin(0.55/8)=3.94°），降入射角只会让缝变窄".
- **F36**: add notes with the exact title "Indistinguishable from magic: the EUV pellicle" and the position quote "positioned inside the lithography machine just below the reticle".
- **F18**: add ZEISS EUVL Workshop 2024 slide 8 (https://euvlitho.com/2024/P22.pdf): "> 40.000 individual parts ~ 12 t weight". It is used by the new B7_06 overlay.
- **F35**: already carries the qualifier "满场芯片良率损失 100%". Nothing to change.

---

## 4. Changes needed in files I do not own

- `shared/blender/common.py` `setup_compositor()`: the global lens dispersion (0.012) puts red/blue fringes on thin violet beams in energy shots (visible in B6_03 test frames).
  - Suggestion: lower it to ≤ 0.004, or let a scene opt out with a scene flag such as `sc["no_dispersion"]`, as `no_glare` already does. I did not change it.
- `research/visual/audit_B6.yaml` / `audit_B7.yaml`: update statuses after the re-render (section 5 has the resolution of each item).
- No change was needed in `build_machine.py`. B6_17 uses `BM.machine()` and `BM.PATH` as they are. B7_01 uses `BM.PO_MIRRORS`, `PO_FOCUS`, `RETICLE`, `WAFER`, `M5_R`, `M6_R`.

---

## 5. Per-shot record of the code changes

### B6 (b6_scenes.py, mograph/b6.py)

**Shared reticle model (`_mask`, `mask_material`)**
- **Image field:** now a 132 × 104 mm rectangle on the 152 mm plate. The long side runs along X (the scan direction), and the plane of incidence is XZ.
- **No rainbow:** the thin-film rainbow is removed. The field is a mirror-bright Mo/Si surface with a dark absorber mosaic: 3 × 2 dies, scribe streets, and functional blocks of different density, so each block has a different average reflectivity.
- **Bug fixes:**
  - Fixed an old bug where the field plane inherited the plate's scale and sat *inside* the plate, so only strips of it showed.
  - Fixed the `ShaderNodeMix` socket bug, which had made the colour constant.

**B6_01**: the new reticle in its holder. Plain metallic look, no rainbow.

**B6_02**
- **Absorber:** 60 nm tall (1.94 units at the 6.8 nm period scale), lines at the 104 nm pitch (52 nm wide), with a wider stack under them.
- **Camera:** the move now ends on a frame that shows the absorber lines and the Mo/Si stack together. It no longer pixel-matches B4_02's end frame (stack only), as the audit asked.

**B6_03**
- **Light:** saturated EUV-violet beams at 6° (NXE) from the normal. Openings reflect, and beams stop on the absorber tops.
- **Glitch fixed:** the absorber now has a dim dark-grey energy fill, so beams no longer end in mid-air.
- **Camera:** the pull-back continues from the B6_02 end frame.

**B6_04**
- **Cone:** cone half-angle 4.73° (asin(0.33/4)).
- **Heading:** "NXE：入射角 ≈ 6°（主光线相对法线）". The fact id is gone.

**B6_05**
- **Shapes:** rebuilt from US 7,694,267:
  - straight lines at the 104 nm mask pitch with hammerheads at the line ends;
  - isolated lines flanked by thin assist bars;
  - an L-wire with corner serifs and a jog.
  - The sine-wobbled "rivers" and droplets are gone.
- **Scale bar:** one pitch long, "104 nm（掩模上）".

**B6_06**: the fact id is removed from the footer.

**B6_07**: the same picture morphs to the printed result: no hammerheads or assist bars, slightly rounded ends. At the end the labels cross-fade to "晶圆上的线条（已按 4× 放大显示）" with the bar "26 nm（晶圆上）".

**B6_08**: a small (~2 % of frame width) irregular, displaced grain instead of the smooth egg. A visible slanted light shaft, motes, and the defocused reticle field in the lower frame.

**B6_09**
- **Fields:** true 26 × 33 mm size (74.5 × 94.6 px) on the 300 mm wafer. Columns sit on the centre line and rows are centred. Every field touching the wafer is drawn and clipped to the circle. That is exactly 96, matching F45.
- **Text:** "良率损失 100%（满场芯片）". The fact id is gone.

**B6_10**: no change (artistic). Needs the "机械手外形示意" overlay; the trails and counter are post work.

**B6_12** (pellicle after Brouns 2017 Fig. 3/4)
- **Pellicle parts:**
  - a rectangular membrane (137 × 107 mm, 示意) just larger than the field;
  - a thin border;
  - a low frame lifted over a visible slit;
  - four studs glued to the reticle, with fixtures, on the long sides near the corners (示意).
- **Membrane material:** about 3 mm above the plate (standoff 示意). A faint warm-grey, highly transmissive film with a weak Fresnel sheen and no thin film.
- **Glitch fixed:** the beams' keyed visibility is cleared before they are hidden, so no pulses appear in this shot (checked at frame 75).

**B6_13**
- **Light:** EUV at 5.4° (EXE) in the scan plane: a narrow V of saturated violet.
- **Glitch fixed:** beam visibility and emission switch on the same frames with constant interpolation, so there is no black V before a pulse.
- **Glow:** the membrane glow is now the colour of a 773 K body (deep red) at a low strength, so it reads as a faint dull red. Blender's Blackbody node is luminance-normalised, which is why the old glow was salmon-bright. A faint violet H2 rim stays (artistic).
- **Camera:** higher, so the film over the field reads.

**B6_14**
- **Look:** no interference bands, only the faint drifting red glow and the sheen.
- **Camera:** grazing slide with the near border and fixture in focus.

**B6_15**: the text reads "小颗粒离焦 → 印不出来（示意）".

**B6_16**: the subtitle is the exact ASML title, "Indistinguishable from magic: the EUV pellicle · ASML, 2022".

**B6_17**
- **Machine:** the High-NA machine from `BM`.
- **Light path:** the path starts at the pupil facet mirror (`PATH.index(FACET2)`). It shows the incoming ray to the face-down reticle, then the reflection growing into M1 and M2. The beam is thicker.
- **Camera:** framed on `BM.RETICLE` → between M1 and M2 instead of hard-coded old coordinates.
- **Mirrors:** they use the already-plain `multilayer_mirror`.

### B7 (b7_scenes.py, mograph/b7.py)

**B7_01**: the projection optics rebuilt from the design example in BM coordinates.
- **Mirrors:**
  - M1–M4 are curved blanks at `PO_MIRRORS[:4]`, oriented to bisect the legs. Their radii come from the drawing widths.
  - M5 is a holed blank just above the wafer, facing up.
  - M6 is the big holed blank, facing down.
  - Hole radii are chosen to pass the beams (示意).
- **Light:** translucent violet bundles grow leg by leg, as ASML draws them: reticle → M1 → M2 → M3 → M4 → focus → (through M6's hole) M5 annulus → M6 → a hollow cone through M5's hole to the wafer.
- **Rim rings:** each mirror's violet rim ring stays hidden until the beam arrives (glitch fixed: no black rings).
- **Materials:** grey blanks as on the slide, a dark face-down reticle and a ghost housing (示意).
- **Camera:** follows the light down, then rises to a 3/4 view.
- **Not changed:** the final cone in the drawing is about 29°, not 33.4°. B7_15 carries the true NA.

**B7_02**: new `po_compare` blueprint.
- **Drawings:** NXE (traced from s.35 left, cross-checked with Conradi 2011 s.20) beside EXE (s.35 right), at one scale with the wafer levels aligned. Coordinates were measured off `vs21_p35_PO_zoom.png` and are commented in the code. The bands are translucent violet.
- **4× on the NXE side:** a cell drawing at the mask and a quarter-size copy at the wafer, labelled "缩小 4×".
- **Labels:** "设计示例 · ASML / ZEISS（示意）". No mirror count is shown. The old isotropic `reduce4` is removed.

**B7_03 / B7_04**
- **Cones:** drawn at the true half-angles asin(0.33) = 19.3° and asin(0.55) = 33.4°.
- **Footers:** fact ids replaced by "来源：ASML".

**B7_05**: rebuilt on the A0 shipment models (`a0_scenes.shipping_mats`, `_enclosure`, `_flatbed_truck`, `freighter`).
- **Scene:** night wet apron. A white, aluminium-framed, chamfered-roof box on a flatbed with a cab (windscreen, grille) rolls past. Behind it stands a generic freighter with its nose raised, a lit hold and a scissor highloader at the sill. Light masts and haze.
- **Text:** the navy stencil "2023.12" only.
- **Removed:** no ISO container, no forklift, no logos.

**B7_06**: new clay model after ZEISS 2024 s.8 / 2022 s.39.
- **Shape:** a wide, low, angular block (chamfered octagonal plan), a slanted lower section with ribs, a narrower base, panel seams, actuator boxes and cable bundles on top, and a round port.
- **Removed:** the human figure.
- **Motion:** a turntable turn of 50°.

**B7_09 / B7_11 / B7_12**
- **Orientation:** flipped to match B7_07/08 and the machine: the mask is above, face down, and the cones open downward.
- **Cones:**
  - Half-angles come from asin(NA/mag): 7.9° at 4×/4×, and in the scan direction 3.94° at 8× (cone X-scale = tan ratio). Angles are drawn ×3 (示意).
  - Tilt 6° → 5.4°.
  - B7_11's animation and camera end at its last frame (227).
- **Ripple sheet:** it now fades by transparency (frames 118–150) before it is hidden at 152. An unlit sheet never shows as dark squiggles.
- **B7_12 photon:** a small saturated-violet photon slides along the reflected cone's inner edge (the computed edge next to the gap). The camera focuses on that edge, so there is no white blob in the dark gap.

**B7_14 / B7_15**: rebuilt to Heil 2015 s.9 / van Schoot 2021 s.35.
- **M6:** large (r 3.0), high, concave toward the wafer. Its rim height is set so the cone meets the wafer at 33.4°, the NA 0.55 half-angle.
- **M5:** small (0.155/0.386 of M6), about 9× closer to the wafer, facing up.
- **Holes:** they give about 20 % pupil obscuration and let the cone pass M5.
- **Material:** the plain mirror material, with a grey substrate on the back and rim.

**B7_14**: the camera arcs from a side view of both mirrors to beneath, looking up the axis through M5's ring at M6's hole.

**B7_15**
- **Path:** the camera rides down the narrow incoming beam (a see-through glow cone, never an unlit black solid) through M6's hole. The violet rays then draw on in order: focus → M5 annulus → M6 → wafer point, through M5's hole, as a hollow 33° cone.
- **Camera:** it pulls out to show both mirrors, then looks back up through both rings.
- **Glitches fixed:** the old flat wedge glitch is gone (the rig cards stay camera-invisible), and no rays are visible before they light.

**B7_10**: footer "示意 · 来源：ZEISS / ASML".

**B7_13**
- **Beat 1:** the reticle and the 104 × 132 mm field outline stay fixed. The pattern inside stretches 2× in the scan direction; the half that no longer fits turns red and is cut. The labels read "掩模和图形区：尺寸不变 / 图形：扫描方向拉长 2× / 只装得下半个场".
- **Beat 3:** true 26 × 16.5 mm half fields, clipped at the edge, exactly 188. The NXE inset shows true full fields (96).
- **Footer:** "场的尺寸按比例 · 来源：ASML".

**B7_16**: obscuration 20 % (hole radius 0.2, Tatian maps eps 0.2, inner circles at 0.2). The fact id is removed.

---

## 6. Open items (not fixed in code)

- **Re-render:** all B6/B7 shots must be re-rendered at the target quality, and the contact sheets reviewed at full length (WORKFLOW 5).
- **Post overlays still needed:**
  - B6_10: motion trails and the 1,000,000 counter.
  - B6_12: the 13 nm vs 13.5 nm comparison.
  - All label texts in section 2.
- **Orientation, B6_12–14:** the reticle is shown face up with the pellicle above, as in Brouns Fig. 3. This is correct only together with the re-voiced B6_12 line ("图形面前"). If the line is not re-voiced, the shot contradicts ASML's "just below the reticle".
- **Glow, B6_13/14:** the dull-red glow is still deliberately visible, so the "暗红辉光为示意" overlay is needed.
- **Not public:**
  - Pellicle stud positions, frame height, membrane size.
  - M5/M6 hole sizes.
  - Whether M5 is concave.
  - The absolute size of the PO module.
  - Treatment: all are drawn and labelled 示意 (see the overlays).
