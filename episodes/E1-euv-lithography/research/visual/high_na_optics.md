# High-NA EUV (EXE:5000 / EXE:5200) optics and machine layout, with NXE:3400/3600 for comparison

Researched 2026-10-19. Every claim below has a source quote. Confidence tags:
- **[H] high**: stated outright in ASML, ZEISS or Intel material.
- **[M] medium**: read off an official drawing that is labelled "design example" or "schematic", or a secondary report quoting ASML staff.
- **[L] low**: inferred. These are marked as inferences.

Where the PNGs are: `R = /Users/adam429/Desktop/project-2026/dreamforge/episodes/E1-euv-lithography/renders/review/refs/highna`. The source PDFs are in the same subfolders.

Main sources:
- **[A22]** Jan van Schoot (ASML), "High NA EUV: Getting closer to introduction", EUVL Workshop, 7 June 2022. https://euvlitho.com/2022/P3.pdf
- **[A21]** Jan van Schoot (ASML), "High-NA EUV Progress and Outlook", EUVL Workshop, 8 June 2021. https://www.euvlitho.com/2021/P3.pdf
- **[A17]** van Schoot et al. (ASML + ZEISS), "High-NA EUV lithography", EUVL Workshop, 15 June 2017. https://www.euvlitho.com/2017/P22.pdf
- **[Z15]** Tilmann Heil et al. (ZEISS, with van Schoot of ASML), "Anamorphic High NA Optics enabling EUV Lithography with sub 8nm Resolution", EUVL Symposium, 7 Oct 2015. https://euvlsymposium.lbl.gov/pdf/2015/Oral_Wednesday/Session9_EUV%20Lithography%20Extendibility/S9.2_Heil.pdf
- **[Z21]** Wischmeier, Graeupner, Kuerz (ZEISS), Stoeldraijer, van Schoot (ASML), "High NA EUV optics: a big step in lithographic resolution", EUVL Workshop, 10 June 2021. https://euvlitho.com/2021/P52.pdf
- **[Z24]** Kaumanns, Neumann, Conradi, Graeupner (ZEISS), "Status and outlook of EUV optics at ZEISS", EUVL Workshop, 6 June 2024. https://euvlitho.com/2024/P22.pdf
- **[A14]** van Schoot, Valentin, van Ingen-Schenau (ASML), Migura (ZEISS), "EUV lithography scanner for sub 9 nm resolution", EUVL Symposium, 29 Oct 2014. https://euvlsymposium.lbl.gov/pdf/2014/f158fa8ccb1f4e3b8a59b22822e61157.pdf
- **[D20]** Davydova et al. (ASML), SPIE 11517 (2020), on SHARP imaging experiments with central obscuration. https://goldberg.lbl.gov/papers/Davydova_SPIE_11517(2020).pdf
- **[dW22]** de Winter, van Schoot et al. (ASML/ZEISS), "Extreme ultraviolet scanner with high numerical aperture: obscuration and wavefront description", JM3 21(2) 023801 (2022). Only the abstract was available.
- **[C11]** Conradi et al. (ZEISS), "Optics for EUV Production", EUVL Symposium 2011. https://euvlsymposium.lbl.gov/pdf/2011/pres/Olaf%20Conradi.pdf. The user already has this; local copy at `refs/conradi2011.pdf`.
- **[INTEL]** Intel newsroom, "With High NA EUV, Intel Foundry Opens New Frontier in Chipmaking", 18 Apr 2024. https://intel.com/content/www/us/en/newsroom/news/intel-foundry-opens-new-frontier-chipmaking.html. Also the Intel resource page https://intel.com/content/www/us/en/newsroom/resources/intel-high-na-euv.html
- **[ASML5]** ASML, "5 things you should know about High NA EUV lithography" (2024). https://www.asml.com/en/news/stories/2024/5-things-high-na-euv
- **[ZMAG]** ZEISS SMT magazine, "High-NA-EUV lithography". https://www.zeiss.com/semiconductor-manufacturing-technology/smt-magazine/high-na-euv-lithography.html
- **[ZEUV]** ZEISS, "EUV lithography". https://www.zeiss.com/semiconductor-manufacturing-technology/inspiring-technology/euv-lithography.html

---

## 1. Projection optics (POB) of the 0.55 NA system

### 1.1 Mirror count: the published drawings show 6 mirrors, not 8

- **The High-NA design labels its last two mirrors M5 and M6, and the hole is "drilled" in those two.** [Z15] slide 9 has the title "There is a solution: Obscuration – We drill a hole into the mirror." It labels the two final mirrors **M6** (large, upper) and **M5** (small, just above the wafer). Slides 5–8 compare "Medium NA" with "High-NA" using the same M5/M6 names: "…increases the angles on M5…", "Standard EUV coatings are not able to reflect the combination of large angles and large angular spreads on M5 needed for high-NA."
  - **[M]** Calling the last mirror M6 implies a 6-mirror design.
  - PNG: `R/heil2015/heil_p9.png`
- **ZEISS 2024 uses "Last mirror" and "Second to last mirror" for the two obscured mirrors.** [Z24] slide 9 has the labels "Last mirror", "Second to last mirror", "High NA unobscured", "High NA obscured" and "Wafer level". No total mirror count is given. **[H]** for which two mirrors are obscured.
  - PNG: `R/euvlitho2024_P22/zeiss24_p9.png`
- **Every ASML/ZEISS 0.55 NA "design example" drawing shows six mirrors between reticle and wafer.** These are [Z15] slides 19 and 20, [A17] slide 15 and [A21] slide 35. The [Z21] and [Z24] "design scheme" renders also show six. **[M]** All of them are labelled "Design examples" or "design scheme". ASML says the anamorphic lens is new, "Because this new lens is fundamentally different" (ASML, "Making EUV: from lab to fab", 2022).
- **Where the "8 mirrors?" idea comes from.** ZEISS [C11] slide 25 (2011) is a roadmap titled "We see design solutions for high NA systems enabling 11 nm resolution and beyond". It has two rows, "6 mirrors" and "8 mirrors". The "8 mirrors, central obscured" bar sits around NA 0.5–0.7 / 8 nm. That was a 2011 option space, marked "schematic designs – for illustration only".
  - From 2014 on, ASML and ZEISS talks only show the 6-mirror obscured design with M5/M6.
  - **Conclusion:** the public evidence points to 6 mirrors **[M]**. No ASML or ZEISS text found says "the EXE POB has N mirrors" (see section 5).
- **Comparison, 0.33 NA has 6 mirrors.**
  - [ZEUV]: "the optical EUV system consists of the projection optics - with six mirrors." **[H]**
  - [C11] slide 20: "Full field 6 mirror designs can be extended to NA 0.33". **[H]**

### 1.2 Central obscuration (the holed mirrors)

- **Why there is an obscuration.** [Z24] slide 9: "Central obscuration – Reduces angular load and angle variation – High-transmission design solution". **[H]**
- **Which mirrors.** [D20] §1: "a central obscuration is introduced in the projection optics to reduce the range of reflection angles from the second to the last mirror". [Z24] labels the second-to-last and last mirrors. **[H]**
  - Geometry from [Z15] slide 9 (right half) and [Z24] slide 9. **[H]**
  - Both mirrors have a central hole. The beam comes down through the hole in the big upper mirror (M6) to the small lower mirror (M5). M5 reflects it back up to M6. M6 is concave and focuses the light down through the hole in M5 onto the wafer.
  - So M5 sits directly above the wafer, coaxial with it. M6 sits above M5.
- **Size of the obscuration.**
  - [D20] §5: "The high-NA scanner has central obscuration of approximately 20% of the pupil plane." **[H]**
  - [Z15] slide 24: "...which can be tolerated if kept below ~20% radius." Slide 25: "NA=0.55, 12 nm spaces 4x/8x Anamorphic, 20% obscuration".
  - [dW22] abstract: "The introduction of a central obscuration in the optics design reduces the angular load on the multilayer mirrors, enabling a high transmission and throughput. The central obscuration area has been minimized for best imaging, overlay, and transmission." **[H]**
  - [A21] slide 36: "For high-NA machines, projection lens has a central obscuration (CO)". Because of the obscuration, ASML describes wavefronts with Tatian polynomials instead of Zernikes.
- **Transmission benefit.** [Z15] slide 9: "The obscuration massively reduces angles & angular spread on the mirrors… …which significantly increases the transmission of the optical system vs. 3300!" [Z15] slide 20: "Obscuration enables significantly higher optics transmission vs. 3300". **[H]**

### 1.3 Layout drawing: 0.55 NA POB "design example" (side view) for a 3D modeller

PNGs:
- `R/euvlitho2021/vs21_p35_PO_zoom.png` (300 dpi crop, best)
- `R/euvlitho2021/vs21_p35.png` (whole slide)
- `R/heil2015/heil_p19.png` and `R/heil2015/heil_p20.png` (same design in 2015, with feature call-outs)

Quote on the slide [A21 s.35]: "High-NA projection optics design available – Larger elements with tighter specifications… Extreme aspheres enabling further improved wavefront / imaging performance · Obscuration enables higher optics Transmission · Big last mirror driven by High-NA". It is labelled "Design examples". It is the same design as [Z15] slide 19/20, which credits "Source: Zeiss, 'EUV lithography optics for sub-9nm resolution,' Proc. SPIE 9422, (2015)" ([A17] slide 15).

Positions below were measured off the 2D drawing **[M]**:
- Origin = the image point on the wafer.
- h = height above the wafer, as a fraction of the reticle-to-wafer distance (reticle at h = 1.00).
- x = horizontal offset in the same unit, positive to the right.
- Mirror names follow the M5/M6 labels of [Z15].

| Element | Position (x, h) | Apparent width (same unit) | Orientation / role |
|---|---|---|---|
| Reticle | x −0.22…−0.03, h 1.00 | 0.19 | Horizontal at the very top, pattern facing down. The beam leaves near x ≈ −0.08, going down and slightly right. |
| M1 | (−0.02, 0.63) | ~0.09 | Small. Faces up, slightly tilted. Takes the steep beam coming down from the reticle. |
| M2 | (+0.12, 0.86) | ~0.09 | Small. Upper right, tilted ~15–20°, faces down-left. Gets the beam reflected up-right from M1. |
| M3 | (+0.07, 0.40) | ~0.18 | Medium. Faces up, sits just above M6. Gets a wide, nearly vertical column coming down from M2. |
| M4 | (−0.06, 0.585) | ~0.08 | Small. Mid-left, tilted ~20°, faces down-right. Gets the beam reflected up-left from M3. |
| Intermediate focus (narrow waist) | (−0.035, ~0.375) | – | The beam from M4 converges here, just above M6, then passes down through M6's central hole. |
| **M6 (last mirror, largest, holed)** | (0.00, ~0.34) | **~0.39** | Large. Concave, faces down, central hole, coaxial with the wafer. In the drawing it is wider than everything else combined. |
| **M5 (second to last, holed)** | (0.00, ~0.035) | ~0.16 | Faces up, sits just above the wafer, central hole. Reflects the beam up to M6. M6 focuses a full cone back down through M5's hole onto the wafer. |
| Wafer | h 0 | – | – |

- **Beam path:** reticle ↓ M1 ↗ M2 ↓ M3 ↖ M4 ↓ (focus, then through the hole in M6) ↓ M5 ↑ M6 ↓ (through the hole in M5) → wafer. In the upper half the beam zig-zags like a folded "Z" in a narrow column. The lower 40 % of the height is the big solid M6/M5 cone.
- **Size relative to NXE [L].** The same slide draws the NA 0.33 design next to it, apparently at the same scale.
  - NXE reticle-to-wafer height is ~0.77 of the High-NA one.
  - The NXE largest mirror (its M6, unobscured, sitting off-axis above an off-axis M5 beside the wafer focus) is ~0.42 times as wide as the High-NA M6.
  - Whether the two drawings share one scale is not stated.
  - The quantitative statement ZEISS does make, [ZMAG]: a High-NA mirror is "about twice as large and ten times as heavy as current EUV mirrors" and the mirrors "weigh several hundred kilograms". **[H]**
- **NA 0.33 drawing on the same slide, for comparison [M].** PNG: same file, left side.
  - Reticle at top left. The beam goes down to M1 (low, h ≈ 0.47), up to M2 (h ≈ 0.75), down to small M3 (h ≈ 0.38), up-right to small tilted M4 (h ≈ 0.51).
  - From M4 it goes down-left to small M5 just beside the wafer (h ≈ 0.03, off to the right of the image point), up to large M6 (h ≈ 0.30), and M6 focuses down to the wafer.
  - No holes; the beam passes beside M5.
  - Matches [C11] slide 20 ("NXE 3300 – Projection optics design for NA 0.33", 6 mirrors).

### 1.4 "Design scheme" renders (stylized, from ZEISS)

PNGs:
- `R/euvlitho2021_P52/zeiss21_p9.png` [Z21] slide 9, "High-NA EUV – The optical system for the ultimate printing machine with NA = 0.55 · design scheme"
- `R/euvlitho2024_P22/zeiss24_p13_current_zoom.png` [Z24] slide 13, "Current 0.55 NA"

Description of the "current 0.55 NA" render **[M]**. It is stylized and not to scale.
- **Source:** IR laser (red) at far left behind a collector dish. The collector axis is roughly horizontal and points right.
- **Collector cone:** converges rightward to the **intermediate focus (IF)**.
- **Illuminator:**
  - Right after the IF, a small tilted mirror sits low. It folds the beam up-right.
  - Next is a large tilted mirror at the top. In ASML's labelled drawings this is the field facet mirror ([A22] slide 36, [Z21] slide 13).
  - Down to a mirror at the bottom (the pupil facet mirror).
  - Steeply up to the reticle at the top, which faces down.
- **PO zig-zag:** M1 bottom → M2 top → M3 bottom → M4 top (tilted). Then down through the hole of the large M6 (bottom right) → small M5 resting on the wafer → back up to M6 → down to the wafer.
- The renders do not number the mirrors.

### 1.5 NA, magnification, scan direction, field, reticle, chief-ray angle

- **NA 0.55**
  - [ASML5]: "we've increased the NA from 0.33 in our NXE systems to 0.55 in EXE systems." **[H]**
  - [ZMAG]: "With a numerical aperture of 0.55…" **[H]**
- **Anamorphic 4x / 8x, with 8x in the scan direction (Y)**
  - [Z24] slide 9: "Anamorphic lens design: 4× reduction in non-scan direction, 8× reduction in scan direction". **[H]**
  - [A22] slide 27: "Half-Field (26mm x 16.5mm) … X=4x mag, Y=8x mag (Anamorphic Mask) … Half-field mask 104 mm [x] × 132 mm [y]". **[H]**
  - [Z21] slide 11: "βscan = 1/8, βx-scan = 1/4". **[H]**
  - [A14] slide 14: "Anamorphic optics half field: 8x Magnification in scan, 4x Magnification in other direction". **[H]**
  - [ASML5]: "the system's mirrors demagnify it by 4x in one direction and 8x in the other."
  - [A21] slide 34: "4x/8y magnification".
  - **Directions:** X = slit (cross-scan), Y = scan. The reticle moves along Y. [A21] slide 34 draws a double arrow labelled "Scan direction" along the reticle's long side (132 mm), with the wafer moving antiparallel.
- **Field at the wafer: 26 mm × 16.5 mm (half field)**
  - [A22] slide 12: "0.55NA prints a Half Field" (26 mm × 16.5 mm), compared with "0.33NA prints a Full Field" 26 × 33 mm. **[H]**
  - [A22] slide 14: "188 half fields per wafer".
  - Exposure slit at the wafer: [Z21] slide 11 gives a 26 × 1.6 mm² arc. At the reticle it is "104x12.8 mm²", drawn as a curved (arc-shaped) slit. **[H]**
- **Reticle: standard 6-inch, image field 104 × 132 mm, unchanged from NXE**
  - [A21] slide 34, "Unchanged vs 0.33NA": "Reticle blank…", "Image field size at reticle level (104 x 132 mm)", "Pellicle…", "EUV pod". **[H]**
  - [Z15] slide 21: "26mm slit @wafer and 6'' mask".
- **Chief-ray angle at the reticle (CRAO): about 5.3–5.4°** (NXE: 6°)
  - [Z24] slide 9: "4x/4x demagnification … 6° … NOK: overlapping light cones" against "4x/8x demagnification … 5.4° … OK: works". **[H]**
  - [A21] slide 34, "Changed vs 0.33NA": "Exposure Chief Ray Angle (~5.3°)". Same slide, under unchanged: "Mask metrology Chief Ray Angle (6°)". **[H]**
  - A figure of 5.355° shows up in search snippets attributed to de Winter et al. 2020 (SPIE 11517). I could not open the full text, so it is **unverified**.
  - **Use "≈5.4° (ASML: ~5.3°)"; the NXE value is 6°.**
  - NXE 6° is stated in [Z15] slide 11 ("NXE:3300 Projection with MAG 4x, CRAO 6°, NA 0.33") and [C11] slide 20 ("CRAO = 6°").
- **Angles at the mask (multilayer limit)**
  - [A22] slide 12: "11 deg required for 0.33NA", "~18deg" for 0.55NA isomorphic, and "~8deg"/"~9deg" for 0.55NA anamorphic. **[H]**
  - [Z21] slide 11 marks "9°" on the 4x isomorphic mask cone. Search snippets of an SPIE paper say that without anamorphic optics "the maximum angle at reticle level would extend up to 17° in the critical (scanning) direction".
  - PNG: `R/euvlitho2022/vs22_p12.png`
- **Pupil shapes.** [A22] slide 13: "Anamorphic projection lens has same resolution in x & y – Elliptical illumination pupil is transformed in a round exit pupil". The drawing shows the reticle on top, two elliptical "Pupil in / Pupil out" cones, and a round pupil above the wafer, with "Scan" arrows. **[H]**
  - PNG: `R/euvlitho2022/vs22_p13.png`
- **Weight and parts.** [ZMAG]: "the projection optics consists of over 40,000 parts and weighs approximately twelve tons." [Z24] slide 8: "> 40.000 individual parts, ~ 12 t weight, < 1 Å mirror surface figure control, < 0.1 nrad mirror tilt control". **[H]**
  - NXE PO for comparison, [ZEUV]: "This requires around 20,000 individual parts weighing 2 tonnes." The page context implies this is the PO. **[H]/[M]** on which module it refers to.
  - [ZMAG]: High-NA optics are "about seven times larger in volume and weight than EUV optics that are currently in use."

## 2. Illuminator

- **Same principle as NXE: a field facet mirror (FFM) followed by a pupil facet mirror (PFM), with actuated facets.**
  - [A22] slide 36 title: "High NA flexible illuminator design available – Principle NXE:3300/3400 illuminator can be reused". Labels: "Intermediate Focus", "Field Facet Mirror", "Pupil Facet Mirror", "Illuminator elliptical pupil is projected in a circular pupil at the wafer". **[H]**
  - [Z21] slide 13: "High-NA illuminator will utilize 0.33NA technology with actuated facet mirrors … High-NA illuminator provides 20% pupil fill ratio". **[H]**
  - PNG: `R/euvlitho2022/vs22_p36.png`. Geometry [M], schematic:
    - IF at lower left (a small blue spot).
    - A green cone diverges upward and right to the FFM: an elliptical plate seen from below at the top centre, carrying about a dozen blue arc/banana-shaped facets.
    - The facets send narrow beamlets steeply down and right to the PFM at lower right: a grid of round facets on short cylinders (about 6 × 4 shown), some red ("on") and some yellow.
    - Also on the slide: a grey ZEISS CAD render of the illuminator module, an elliptical "pupil @ mask" next to a circular "pupil @ wafer" (dipole example), and a reference to Zimmermann et al., EUVL Symposium 2016.
- **Mirror count after the PFM: not stated in text.**
  - Every High-NA "design scheme" render ([Z21] slide 9, [Z24] slide 13 "Current 0.55 NA") draws three illuminator mirrors **[M]**:
    1. a small fold mirror just after the IF,
    2. a large top mirror (FFM),
    3. a bottom mirror (PFM),
    and the PFM sends light directly up to the reticle.
  - The NXE scheme ([C11] slide 5, [Z15] slide 10) draws four: FFM (top) → PFM (bottom) → a third mirror (top) → a fourth (bottom) → reticle.
  - The renders are stylized, so the actual EXE illuminator mirror count is **not public**.
- **Future concept (ZEISS 2024), useful as a contrast.** [Z24] slide 13 compares "Current 0.55 NA: Pupil Fill Ratio 20%" with "Concept 0.55 NA: Pupil Fill Ratio ~10%, High transmission". **[H]** for the text.
  - The concept render drops the fold mirror after the IF and moves the source to the lower left, firing steeply upward into the FFM, like the NXE layout. **[M]**
  - PNG: `R/euvlitho2024_P22/zeiss24_p13_concept_zoom.png`
- **Grazing-incidence mirror: not confirmed for EXE or NXE.**
  - No ZEISS or ASML slide reviewed labels a grazing-incidence mirror.
  - ZEISS patents describe illuminators whose last transfer mirror works at grazing incidence, but none is tied to a product.
  - The small fold mirror in the EXE renders is unlabelled. Its incidence type is **not public**.
- **Weight and parts.** [ZMAG]: "With High-NA-EUV lithography, it weighs more than six tons and consists of more than 25,000 parts." [Z24] slide 8: "> 25.000 individual parts, ~ 6 t weight". **[H]**
  - NXE illuminator, [ZEUV]: "The illumination system consists of 15,000 individual parts weighing 1.5 tonnes." **[H]**
- **Delivery dates.** [Z24] slide 11: "ILLU #1: 31.03.2023 · POB #1: 11.07.2023 · 1st shipment ex ASML: 21.12.2023 · successful in-resist images 10nm half-pitch (Spring 2024)". **[H]**

## 3. Whole machine (EXE:5000 / EXE:5200)

### 3.1 Module arrangement

- **Four independently testable subsystems: Mask (top), Optics (middle), Wafer (bottom), Source (beside, on the right).** [A22] slide 34 has the title "High NA system consists of 4 independent testable subsystems – Improved testability and cycle time". **[H]**
  - PNGs: `R/euvlitho2022/vs22_p34.png` and `R/euvlitho2022/vs22_p34_zoom.png`
  - CAD exploded view, side elevation **[H]** for the labels, **[M]** for the read-off geometry:
    - **Top tier, "Mask":** a long flat module across the top with the "Mask Handler" on the left half and the "Mask Stage" on the right half.
    - **Middle tier, "Optics":** the "POB" (left) and "illuminator" (right, on the source side) inside a single angular grey housing that is wider at the top. It sits in a box-like "Mid Frame" with round ports.
    - **Lower tier, "Wafer":** a heavy "Base Frame" with many octagonal ports. The "Wafer Stage" is a low white box sticking out at the bottom left under the base frame. The "Wafer Handler" sits on the far left at floor level.
    - **"Source", separate block on the right at the same floor level:**
      - a "Vessel" (rounded chamber with cabling) mounted on a boxy pedestal,
      - the "Collector" inside the vessel, whose port faces left toward the illuminator at roughly mid-frame height,
      - an "Optical Platform": a table on four tall legs extending further right.
    - All four sit on one dark floor plate.
  - **Beam direction source→scanner.** The vessel's output faces left (horizontally) into the illuminator side of the optics tier. The exact elevation angle is **not public**. The ZEISS render ([Z24] slide 13 "Current") also draws the collector axis roughly horizontal, with a fold mirror after the IF. **[M]**
    - This differs from NXE, where the source sits low and fires diagonally upward ([C11] slide 5; [A17] slide 22 cut-away).
- **Block diagram: which modules are new and which are shared with NXE.** [A22] slide 33 has the title "High NA system architecture finalized – Maximized commonality between 0.33NA and 0.55NA platforms". **[H]**
  - PNG: `R/euvlitho2022/vs22_p33.png`
  - Grid, read off the slide:
    - top row: "Mask Handler" (left) | "Mask Stage" (centre)
    - middle row: "Projection Optics" (left) | "Illuminator" (centre) | "Source Vessel" (right)
    - bottom row: "Wafer Handler" (left) | "Wafer Stage" (centre) | "Drive Laser" (right, under the Source Vessel)
  - Colour scale from "Specific" to "Common": the optics are fully specific; the source and drive laser are common with NXE.
  - Real-world placement of the drive laser (sub-fab or not) is not given on this slide.
- **Exterior and what changed.** [A22] slide 32 has the title "High NA system architecture finalized and system assembly started". **[H]**
  - PNG: `R/euvlitho2022/vs22_p32.png`
  - Call-outs on a render of the white EXE:5000 enclosure:
    - "Lens & illuminator: NA 0.55 for high contrast, High transmission"
    - "Mask Stage: 4x increase in acceleration"
    - "Improved Source position: Allows for larger transmission, compatible with 0.33 NA"
    - "Improved metrology 1.5~2x improvement in overlay/focus"
    - "Wafer Stage: 2x increase in acceleration"
    - "New Frames: Improved thermal and dynamic control with larger optics"
  - Enclosure description [M]:
    - a long white panelled box with a vertical-seam pattern and an ASML logo and signal light at upper left,
    - an "EXE:5000" badge and screen at lower left,
    - the right-hand third (the source side) has a recessed lower half,
    - two cleanroom workers at a screen on the right give the scale.
- **Stage accelerations.** [ASML5]: "The wafer stage in an EXE system accelerates at 8g, twice as fast as the NXE's wafer stage" and "the EXE's reticle stage accelerates four times faster than the NXE's – 32g". **[H]**
- **Older 2016/2017 mechanical CAD.** [A17] slide 29, "Mechanical layout – Modularity key for manufacturing, shipment and service". PNG: `R/euvlitho2017_P22/vs17_p29.png`. **[M]**, early design.
  - The colour-coded CAD has a red top module (reticle stage) on a purple gantry frame.
  - An orange frame module is in the front right, a grey/white central body, and a green/orange wafer-handler area on the left with a human figure for scale.

### 3.2 Size, weight, shipping

- **Weight**
  - [INTEL] (18 Apr 2024): "The 165-ton High NA EUV tool was built by ASML…". Same article: "The total weight of each new system is more than 150 metric tons." **[H]**
  - Intel resource page: "It is as big as a double-decker bus and weighs as much as a blue whale."
  - Watch out: [ZMAG] also says "more than 150 tons", but that is ZEISS's mirror **metrology vacuum chamber** ("a five-by-ten-meter vacuum chamber … a total weight of more than 150 tons"), not the scanner.
- **Overall dimensions (L × W × H): not public.** Only comparisons exist.
  - Intel: "as big as a double-decker bus".
  - CNBC (2025, secondary), quoting ASML High NA qualification lead Assia Haddou: "bigger than a double-decker bus". **[M]**
- **Base frame alone: 6 m × 2.5 m × 2.5 m, about 21 t.** [A21] slides 47–49: "Base Frame pre-milling of sections completed, e-beam welding in progress · Four sections ready for welding · Volume: 6m x 2.5m x 2.5m · Weight: ~21,000kg". **[H]**
  - This sets a lower bound on the scanner body's footprint. PNG: `R/euvlitho2021/vs21_p47.png`
- **Heaviest single module: 28 t.** [A21] slide 55: "Heaviest module test, successfully loaded in B747 – 28 Tons @ Airbridge Cargo Schiphol Airport". **[H]**
- **Shipping**
  - [INTEL]: "The TWINSCAN EXE:5000 system was transported to Oregon in more than 250 crates inside 43 freight containers. These were loaded onto multiple cargo planes that landed in Seattle. They were then transferred to 20 trucks for the drive to Oregon." **[H]**
  - CNBC (secondary, quoting ASML): "seven partially loaded Boeing 747s, or at least 25 trucks"; "four modules, manufactured in Connecticut, California, Germany and the Netherlands". **[M]**
  - [ASML5]: "EXE systems are made up of modules that can be independently tested before being integrated into a complete system" and "shipped the first modules of the first High NA EUV lithography system to Intel in December 2023."
- **Power consumption: not public** for EXE. No ASML figure found.
- **Throughput**
  - [A22] slide 16:
    - EXE:5000: "<1.1 nm [MMO], 150wph", with footnote "185wph@20mJ/cm2"
    - EXE:5200B: "<0.8 nm, 220wph"
    - "wafers/hours (wph) are based on 30mJ/cm²"
  - **[H]** These are the 2022 roadmap targets.
  - The ASML EXE:5200B product page gives its numbers "at dose: 50 mJ/cm²", but the values did not render in text.
- **Optics within the machine.** [A22] slide 39 inset: a translucent render of the whole machine with "Projection optics" and "Illuminator" highlighted as dark solids in the middle tier. The illuminator is on the right of the POB, toward the source. **[M]**
  - PNG: `R/euvlitho2022/vs22_p39.png`
  - The same slide has ZEISS photos: the POB frame hanging from a crane, a coated mirror, and the illuminator frame in a stand with two people.

## 4. NXE:3400/3600 (0.33 NA) for comparison

- **Optical train (confirmed).**
  - [C11] slide 5 "The optical train – Introduction" ("λ 13.5 nm, NA 0.25/0.33, Field 26 x 33 mm², Mag 4x") shows:
    - plasma/collector at lower left,
    - the beam rising diagonally up-right to the IF,
    - "field facet mirror" (large, top) → "pupil facet mirror" (bottom) → a third mirror (top) → a fourth mirror (bottom) → reticle (top, facing down) → 6-mirror PO → wafer.
  - [Z15] slide 10 is the same render ("The EUV Optical System", labels "Source", "Intermediate Focus", "Illuminator", "Projection Optics", "Aspheric Mirrors", "Multi-Layer Coating", "Wafer"). **[H]** for the labels.
  - The illuminator count of 4 (FFM, PFM + 2) is **[M]**: taken from a schematic, not stated in text.
  - PNG: `R/heil2015/heil_p10.png`
- **PO: 6 mirrors, CRAO 6°, 4x, full field 26 × 33 mm.**
  - [ZEUV] "projection optics - with six mirrors"
  - [C11] slide 20 "Slit width 26mm, MAG = 4x, CRAO = 6°… Full field 6 mirror designs can be extended to NA 0.33"
  - [Z15] slide 11 "NXE:3300 Projection with MAG 4x, CRAO 6°, NA 0.33 … 104 mm × 132 mm … 26 mm × 33 mm"
  - **[H]** for all three.
  - No obscuration. In the design drawing ([A21] slide 35 left, [C11] slide 20) M5 sits off-axis beside the wafer focus and M6 is the large concave mirror above it.
- **Source position on NXE:3400.** [A17] slide 22 overlays an NXE:3400B cut-away. The source is at bottom right, below the level of the optics, and the illuminator/PO beams are shown in purple in the middle. **[M]**
  - PNG: `R/euvlitho2017_P22/vs17_p22.png`
  - For EXE, ASML lists "Improved Source position: Allows for larger transmission" ([A21] slide 40, [A22] slide 32).
- **NXE optics weights.** Illuminator "15,000 individual parts weighing 1.5 tonnes"; PO "around 20,000 individual parts weighing 2 tonnes" ([ZEUV]). **[H]**
- **NXE:3400 overall dimensions and weight: no primary source found.**
  - Secondary press often says "~180 t, 40 containers, 20 trucks, 3 cargo planes", sometimes attributed to "the manufacturer" (igorslab, Asia Times 2021). None of it was found on asml.com. **Treat as unverified.**

## 5. NOT public (or not found in any primary source)

1. A text statement of the **exact number of mirrors** in the EXE projection optics. Drawings and the M5/M6 labels point to 6; no ASML/ZEISS sentence says "6 mirrors" for EXE.
2. **Real mirror positions, radii, aspheric prescriptions and absolute diameters** for EXE (or NXE). Published drawings are "design examples / schematic – for illustration only". There is no absolute M6 diameter, only "about twice as large and ten times as heavy" with "several hundred kilograms".
3. The **exact EXE illuminator mirror count**, and whether any mirror is **grazing incidence**. This includes the identity of the small fold mirror after the IF in the ZEISS renders.
4. **Overall machine length/width/height** of EXE:5000/5200 and NXE:3400. Only "bigger than a double-decker bus" and the base frame's 6 × 2.5 × 2.5 m.
5. A primary-source **NXE:3400 weight**.
6. **Power consumption** of EXE (and NXE).
7. The **exact elevation angle of the source→IF beam** on EXE and NXE, and the **IF height** above the floor.
8. **Drive-laser location** (sub-fab or not) for EXE. ASML's block diagram only puts the "Drive Laser" under the "Source Vessel".
9. The CRAO to more than one decimal place. 5.355° appears only in unverified search snippets; the published values are "~5.3°" (ASML) and "5.4°" (ZEISS).
10. **Mirror numbering inside the illuminator** and the **number of facets** on the EXE FFM/PFM.
