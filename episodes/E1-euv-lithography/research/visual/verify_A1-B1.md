# Verification pass A1, A2, A3, B1 (2026-10-22)

Independent re-check of audit_A1/A2/A3/B1.yaml against the code at HEAD a393fa0 and the sample frames in
renders/shots/<shot>/sample. Every re-checked item carries `verified: "2026-10-22: ..."` in its yaml. New
problems were added as rows with status wrong/glitch and a fix. Nothing was edited in code, storyboard, script or
facts. 2D shots with no sample were rendered from the current mograph code into a scratch folder (not renders/).

## Counts (all rows, including new ones)

| segment | rows | sourced | simplified | artistic | wrong | unsourced | glitch |
|---|---|---|---|---|---|---|---|
| A1 | 55 (12 new) | 19 | 11 | 13 | 3 | 0 | 9 |
| A2 | 37 (8 new) | 18 | 4 | 7 | 1 | 0 | 7 |
| A3 | 42 (13 new) | 15 | 4 | 8 | 2 | 1 | 12 |
| B1 | 112 (22 new) | 58 | 14 | 17 | 1 | 0 | 22 |

## Earlier audit items that are still open

- A1_05 f20-80: scan line still descends. Fix: fade the exposed columns in through the full thickness.
- A1_04 f40-90: no beam taper, so the print is still 1:1. Fix: taper BeamBelow.
- A1_09: the EUV layers are one solid block (22 of 60 layers).
- A3_04 f1-195: the beam still reads as crossing open air (the vacuum chamber is not legible). Fix: show the chamber wall or a viewport, or add 真空中·示意.
- A3_02: the S1 "outer space" wording is still missing from F1 (facts side).
- A3_05: the partner overlay has no fact (facts side).
- B1_11: wrong, cannot be verified because there is no render. The tips have no liquid threads.
- B1_14: cannot be verified, no render.

## New problems (the full list and fixes are in the yaml files)

**A1**
- A1_03: the notch is a raised black cube (f60, f176-197).
- A1_03 f176-197: the spin freezes for the last frames.
- A1_03: the resist is drawn as a rigid coin.
- A1_04 f130-191: the camera sits inside the beam box, and the end of the shot is frozen.
- A1_06 f100: gold appears before the resist strip.
- A1_07: 6 of the 9 levels show as blank slabs.
- A1_09: the EUV layers clip to white.
- A1_02: the layers in the section look the same.
- A1_01: the rainbow arc ends in a hard cut and shows moiré.
- A1_10: the 示意 tag is unreadable.
- Storyboard: the A1_08 overlay still says 约 100 层, and the A1_06 visual still gives the old order.

**A2**
- A2_04: the light cone starts outside the lens.
- A2_01: the chapter card is not drawn.
- A2_02: the caption sits on the resist line.
- A2_05: the pen label overflows and DUV is missing.
- A2_06: the label scrolls off the frame.
- A2_07: a "0" counter shows too early.
- A2-wide: footer text is 18-24 px.

**A3**
- A3_04:
  - the lens shows as a black disc
  - both beams clip to white
  - the beam ends in mid-air
  - the camera is behind the mirror
  - there is a dark torus
  - frame 1 has a white dot
  - the storyboard still says rainbow mirror
- A3_03: the beam is drawn in steps, and the molecule flashes do not follow it.
- A3_05:
  - motion-blur ghosts at the cuts (f130, f195)
  - the floor edge and a void are visible
  - the time bar and euro counter are missing
- A3_06: the collector is a flat disc (build_machine `_disc`). The same model is used in A0 and C.
- A3_06: the storyboard describes beats that are not rendered.
- A3_07: the cut from A3_06 jumps.

**B1**
- Shared mograph:
  - text alpha is ignored under Pillow 12.3, so every 2D text fade pops (all segments)
- B1_02:
  - labels merged, IF dropped
  - stray ring f84-120
- B1_03: the pre-pulse fires too early (f99-108).
- B1_04: the jet strobes (f60-65).
- B1_05: smear and flicker (f9-139).
- B1_08:
  - HUD missing
  - dark rod f1-35
- B1_09:
  - the label is clipped f46-52
  - the footnote is 18 px
- B1_10: the label covers the sheet.
- B1_13 f7: a black core dot (the same simulation feeds A0_01, B2_03 and C_02).
- B1_18: the spectrum spike is clipped at the top.
- B1_19 f1-30: black lines that are not yet glowing.
- B1_20:
  - dark bar f26-28
  - textbook page missing
- B1_24: white clipped pulse.
- B1_29: white bar beam (the energy style lacks the violet-ray fix).
- B1_28/29: no NXE/EXE label (示意（High-NA EXE 布局）).
- B1_01/27: key numbers at 20 px.
- Storyboard text:
  - B1_07 says 50 000
  - B1_15 says rainbow
  - B1_27 says 600 W / 原理样机

## Stale renders

- A1_04 (beam material changed 10-22 00:57) and A1_06 (FlashSheet added 22:42; re-render to confirm it is not visible).
- A2_08 and A3_04: content is current, but the old compositor dispersion shows as fringes on A2_08.
- B1 with no sample: B1_01, B1_06, B1_18, B1_27 (2D) and B1_11, B1_14 (3D).
- B1 with the wrong length (rendered before the retime):

  | shot | sample frames | timed frames |
  |---|---|---|
  | B1_04 | 202 | 170 |
  | B1_05 | 185 | 173 |
  | B1_09 | 110 | 99 |
  | B1_16 | 257 | 222 |
  | B1_17 | 132 | 123 |
  | B1_19 | 167 | 163 |
  | B1_20 | 211 | 189 |
  | B1_22 | 104 | 97 |

- Every 3D sample rendered before 10-22 00:57 uses dispersion 0.012 instead of 0.004. This is minor.
