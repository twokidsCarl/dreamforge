# B6 (mask, pellicle) and B7 (projection optics, High-NA): source notes for the visual audit

Checked 2026-10-21 for `audit_B6.yaml` and `audit_B7.yaml`. Every quote below is copied from the source; slide or page
numbers are given. PDFs and page renders are in `renders/review/refs/B6B7/` (not in git) and, for the High-NA decks, in
`renders/review/refs/highna/` (see `high_na_optics.md`). Grades follow WORKFLOW 2.2: A = ASML / ZEISS / Intel,
B = papers, patents, imec.

The machine shown in the film is the High-NA EXE:5000. NXE numbers (6°, 4×, six projection mirrors, 26 × 33 mm field)
must not be shown as EXE numbers, and vice versa.

---

## S1. ASML, "EUV lithography systems" product page (A)
https://www.asml.com/en/products/euv-lithography-systems (read 2026-10-21)
- "In EUV, reticles are multilayer reflectors that use interference to reflect light from the pattern."
- The optics are "shrinking the reticle pattern by a factor of four." (A3_sources.md has the full sentence: "EUV systems
  use several multilayer mirrors instead of lenses to guide the EUV light to the wafer, shrinking the reticle pattern by
  a factor of four.")
- NXE systems "print microchip features with a resolution of 13 nm"; they have "a numerical aperture (NA) of 0.33".
- EXE: "With an (NA) of 0.55" the platform can "print with a resolution of just 8 nm".
- "The first High NA EUV lithography system was delivered in December 2023." This conflicts with F20/WORKFLOW 2.5,
  which say "shipped" (Dec 2023), arrived (Jan 2024), installed (Apr 2024). Keep "发货".
- **The page does not mention an absorber.** F14 ("吸收层'关掉'不需要的区域") cites only this page, so the absorber part
  needs S7.

## S2. ASML, Kate Brunton, "Indistinguishable from magic: the EUV pellicle", 14 Sep 2022 (A)
https://www.asml.com/en/news/stories/2022/the-euv-pellicle-indistinguishable-from-magic
- Exact title: **"Indistinguishable from magic: the EUV pellicle"**. The B6_16 card reverses it as "The EUV pellicle —
  indistinguishable from magic".
- "A super-thin membrane, 13 nanometers thick (for reference, a human hair is approximately 80,000–100,000 nanometers
  thick)"
- "can withstand temperatures of up to 500 degrees Celsius in a high-vacuum environment"
- **"They are positioned inside the lithography machine just below the reticle"**. The reticle faces down in the
  scanner, so the pellicle hangs below it. B6_12's narration says 掩模**上方**.
- "a core polycrystalline silicon (p-Si) layer bringing mechanical strength"; "a silicide composite pellicle"
- "their job is to catch miniscule particles that would otherwise cling to the reticle"
- "this delicate, shimmering film". This is the only appearance cue. It names no colours, interference or rainbow.
- Not given: standoff distance, frame, membrane size, transmission figure.

## S3. ASML, Wilton CT location page (A)
https://www.asml.com/en/company/about-asml/locations/wilton-ct
- "For every one million movements, the reticle handler can't generate more than one particle that lands on the
  reticle."
- "It transfers the reticle within 20-25 micrometers of the same location, every time"
- "Here a symphony of robots operates in parallel to move the reticle into and out of the vacuum chamber."
- The robot's shape is not described or shown, so B6_10's arm is 示意.

## S4. ASML, "Computational lithography" product page (A)
https://www.asml.com/en/products/computational-lithography
- "diffraction of the light as well as physical and chemical effects in the photosensitive layer deform the image"
- "intentionally deforming the patterns to compensate for the physical and chemical effects"
- "These models are used to optimize the mask, or blueprint of the desired end result"
- No mask shapes are described on the page (no hammerheads, serifs or curvilinear shapes). S9 covers those.

## S5. Derk Brouns (ASML), "Development and performance of EUV pellicles", Adv. Opt. Techn. 6(3-4):221–227 (2017) (B, ASML author)
https://www.frontiersin.org/articles/10.1515/aot-2017-0023/pdf. Local copy: `refs/B6B7/brouns2017/` (p2.png, p3.png).
- p.221: "particles will land on the pellicle membrane (which is not in focus) instead of on the reticle (which is in a
  field plane, so any obscuration will print directly onto the wafer"
- Fig. 1 caption (p.222): "with a pellicle (double light pass); particles are kept out of focus reducing printability."
- p.221: "**Although small particles on the film do not print, the film still needs to be free of larger particles that
  can be up to several micrometers in size.**" The narration in B6_15 is absolute; this qualifies it.
- p.221: "At higher EUV source powers, pellicle films reach temperatures in excess of several hundred degrees C."
- p.222: "The ASML pellicle, has a small slit (≈0.2 mm) between the reticle and the pellicle frame; ... the only point of
  contact between the pellicle and the reticle are at the four stud mounts ... the actual pellicle frame is suspended
  above the reticle"
- p.223 Fig. 3, "The NXE pellicle concept": a **rectangular** membrane over the pattern area, with a thin border and a
  low frame on four studs glued to the reticle (cross-section labels: Fixtures, Membrane, Border, Stud, Frame, Glue
  interfaces). Fig. 4 shows the sizing history, from "11 mm × 11 mm" (Oct '12) to "Final size (full field)"
  (Feb–Apr '15), a rectangle.
- p.226: "thermo-mechanical resistance under EUV/H2". This places the pellicle in hydrogen.
- Note: this paper describes ~50 nm-thick films ("Typical thickness of the current pellicles is approximately 50 nm"),
  an older generation. The 13 nm figure is S2's. The frame height (standoff) is not given; it is not public in the
  sources found.

## S6. Mark van de Kerkhof et al. (ASML), "Defectivity Improvements Enabling HVM for EUV Scanners", EUVL Workshop, 12 June 2019 (A)
https://www.euvlitho.com/2019/P23.pdf. Local copy: `refs/B6B7/euvlw2019_P23/P23.pdf`.
- Slide 3: "**A particle on reticle front side is repeated on every wafer for each die (100% yield loss for full field
  dies)**" and "Damage threshold for 7nm node is ~52nm"
- Slide 7: "Reduce plasma lift-off", "Plasma charging". EUV-induced plasma exists near the reticle; this is the only
  support for B6_13's violet rim.
- Slide 29: "ultimate requirement: ~1 particle (>32nm) per month"

## S7. Vicky Philipsen et al. (imec), "EUV masks: prospects and challenges", EUVL Workshop 2021 (B)
https://euvlitho.com/2021/P11.pdf. Local copy: `refs/B6B7/euvlw2021_P11/P11.pdf`.
- Slide 2, cartoon cross-section "EUV mask": "Ru cap", "Mo/Si ML mirror", "Absorber".
- Slide 8, "Mask absorber material space vs. reference TaBN": "Thickness << 60nm ...", "Thickness ~ 60nm ...". The
  reference TaBN absorber is about 60 nm thick.
- Slide 11: "60nm Ta (SRAF – yes)". This is the reference absorber in an SMO comparison.
- Slide 15: "Carbon nanotube (CNT) is building-block for configurable pellicle"

## S8. AGC (Asahi Glass) patent US 8,288,062 B2, "Reflective mask blank for EUV lithography" (B)
https://patents.google.com/patent/US8288062B2/en
- "a SiO2−TiO2 glass of 6 inches (152 mm) square in outer contour" and "of 0.25 inches (6.3 mm) thick was employed"
- "laminating a Mo layer having a film thickness of 2.3±0.1 nm and a Si layer having a film thickness 4.5±0.1 nm" "so
  that the number of repeating units becomes 30 to 60." **Mo is the thinner layer, period ≈ 6.8 nm.** This also answers
  the open question in audit_B2.yaml (B2_05).
- "the thickness of the absorber layer 14 is preferably from 20 to 50 nm" (this patent's low-reflective absorber;
  imec's reference TaBN is ~60 nm, S7)
- Supporting (TSMC patent US 8,691,476 B2): "the ML 120 includes forty pairs of layers of Mo/Si."

## S9. Brion Technologies (now ASML) patent US 7,694,267 B1, "Method for process window optimized optical proximity correction" (B)
https://patents.google.com/patent/US7694267B1/en
- "Line ends have a tendency to "pull back" from their desired end point location as a function of exposure and focus."
- "Extra structures (or assist features) known as "hammerheads" or "serifs" are routinely added to line ends" "to
  effectively anchor them in place and provide reduced pull back over the entire process window."

## S10. ZEISS, Kaumanns et al., "Status and outlook of EUV optics at ZEISS", EUVL Workshop, 6 June 2024 (A) [Z24]
https://euvlitho.com/2024/P22.pdf. Local render: `refs/highna/euvlitho2024_P22/zeiss24_p9.png`.
- Slide 9: "4x/4x demagnification" with "6°" and "**NOK: overlapping light cones**"; "4x/8x demagnification" with
  "5.4°" and "OK: works"; "Anamorphic lens design 4× reduction in non-scan direction 8× reduction in scan direction".
  The drawing shows the 4x/8x cones as **narrower** ellipses than the 4x/4x cones. The separation comes from the
  narrower cones, not from the smaller angle.
- Slide 9 (right half): "Central obscuration", "Reduces angular load and angle variation", "High-transmission design
  solution"; "Last mirror", "Second to last mirror", "High NA unobscured", "High NA obscured", "Wafer level".
- Slide 8: "> 40.000 individual parts ~ 12 t weight < 1 Å mirror surface figure control"

## S11. Jan van Schoot (ASML), "High-NA EUV Progress and Outlook", EUVL Workshop, 8 June 2021 (A) [A21]
https://www.euvlitho.com/2021/P3.pdf. Local renders: `refs/highna/euvlitho2021/vs21_p34.png`, `vs21_p35_PO_zoom.png`.
- Slide 34, "Unchanged vs 0.33NA": "Reticle blank", "**Image field size at reticle level (104 x 132 mm)**", "Pellicle",
  "EUV pod"; "Changed vs 0.33NA": "Exposure Chief Ray Angle (~5.3°)".
- Slide 35: "High-NA projection optics design available – Larger elements with tighter specifications... Extreme
  aspheres ... Obscuration enables higher optics Transmission · Big last mirror driven by High-NA", labelled "Design
  examples". It draws **NA 0.33 (left) and NA 0.55 (right) side by side**: grey mirror blanks (no colour bands), violet
  beams. In the NA 0.55 design, a narrow beam comes down from M4 through the hole of the large top mirror (M6) to a
  small mirror just above the wafer (M5); M5 sends it up to M6, and M6 sends a full cone down through M5 to the wafer.
  In the NA 0.33 design, M5 sits off-axis beside the focus and M6 has no hole. This is the drawing the backlog asks B7
  to show.
- Slide 36: "**Zernike wave front description replaced by Tatians** • Zernike is a well-known basis to expand
  wavefronts • For high-NA machines, projection lens has a central obscuration (CO) • Tatian (or annular-Zernike) is a
  basis that ASML uses to express aberration with CO"

## S12. Jan van Schoot (ASML), "High NA EUV: Getting closer to introduction", EUVL Workshop, 7 June 2022 (A) [A22]
https://euvlitho.com/2022/P3.pdf. Local renders: `refs/highna/euvlitho2022/`.
- Slide 12: "0.55NA prints a Half Field" (26 mm × 16.5 mm), against "0.33NA prints a Full Field" (26 × 33 mm).
- Slide 14: "High NA and fast stages enables 220 Wph **188 half fields per wafer**". F52 is grade B in facts.yaml but
  this is ASML: grade A.
- Slide 27: "Half-Field (26mm x 16.5mm) (Anamorphic Mask) Half-field mask 104 mm X=4x mag Y=8x mag ... 132 mm"; "Tatians
  Zernikes".
- Slide 34: the four-module CAD (Mask / Optics / Wafer / Source); the POB sits in an angular housing that is wider at
  the top.
- Slide 39: ZEISS photos of the **projection-optics frame hanging from a crane**, a wide, low, angular frame covered in
  cabling; of a "Coated mirror", a metallic mirror in a mount; and of the illuminator frame, with two people for scale.

## S13. Tilmann Heil et al. (ZEISS, with ASML), "Anamorphic High NA Optics enabling EUV Lithography with sub 8nm Resolution", EUVL Symposium, 7 Oct 2015 (A) [Z15]
Local renders: `refs/highna/heil2015/heil_p9.png`, `heil_p19.png`, `heil_p20.png`.
- Slide 9: "There is a solution: Obscuration – We drill a hole into the mirror." It labels M6 (top, large) and M5
  (bottom, small, just above the wafer focus). In the obscured design (right), a narrow beam enters through M6's central
  hole, and the full cone from M6 converges through the gap in M5 to the wafer. "The obscuration massively reduces
  angles & angular spread on the mirrors… …which significantly increases the transmission of the optical system vs.
  3300!"
- Slide 24: "...which can be tolerated if kept below ~20% radius." Slide 25: "4x/8x Anamorphic, 20% obscuration".
- Slide 21: "26mm slit @wafer and 6'' mask".

## S14. Olaf Conradi et al. (ZEISS), "Optics for EUV Production", EUVL Symposium 2011 (A) [C11]
Local render: `refs/conradi_p20.png`.
- Slide 20: "NXE 3300 – Projection optics design for NA 0.33"; "Slit width 26mm MAG = 4x CRAO = 6°"; "Full field 6
  mirror designs can be extended to NA 0.33"; "schematic designs – for illustration only". The mirrors are drawn as
  grey blanks.

## S15. Natalia Davydova et al. (ASML), SPIE 11517 (2020), "Experimental verification of high-NA imaging simulations using SHARP" (B, ASML authors)
Local copy: `refs/highna/davydova2020/doc.pdf`.
- p.2: "a central obscuration is introduced in the projection optics to reduce the range of reflection angles from the
  second to the last mirror"
- p.6: "**The high-NA scanner has central obscuration of approximately 20% of the pupil plane.**"

## S16. ZEISS, "EUV lithography" (A) [ZEUV]
https://www.zeiss.com/semiconductor-manufacturing-technology/inspiring-technology/euv-lithography.html
- "the optical EUV system consists of the projection optics - with six mirrors" (NXE; quoted in high_na_optics.md
  §1.1). This is the source of F7. **It is an NXE statement**; no ASML/ZEISS text gives the EXE mirror count
  (high_na_optics.md §5.1).

## S17. ZEISS SMT magazine, "High-NA-EUV lithography" (A) [ZMAG]
https://www.zeiss.com/semiconductor-manufacturing-technology/smt-magazine/high-na-euv-lithography.html
- "the projection optics consists of over 40,000 parts and weighs approximately twelve tons"; a High-NA mirror is
  "about twice as large and ten times as heavy as current EUV mirrors" (quoted in high_na_optics.md §1.3, §1.5). No
  absolute size of the projection optics is given.

## S18. Intel newsroom, 18 Apr 2024, and Intel video WHmRj2mZ-dk (A)
Quoted in full in `shipment_suppliers.md` A1–A3.
- "The TWINSCAN EXE:5000 system was transported to Oregon in more than 250 crates inside 43 freight containers. These
  were loaded onto multiple cargo planes that landed in Seattle. They were then transferred to 20 trucks for the drive
  to Oregon."
- The video shows white ASML shipment boxes with bevelled ("gabled") tops and bright aluminium extrusions, nose-loaded
  into Cargolux 747 freighters from a scissor highloader. Ordinary crates sit on netted air-cargo pallets. Flatbed
  trailers carry the boxes. WORKFLOW §9 already lists "彩色海运集装箱、胶合板箱" as an error.

## S19. ASML, "5 things you should know about High NA EUV lithography" (2024) (A)
https://www.asml.com/en/news/stories/2024/5-things-high-na-euv (quoted in high_na_optics.md §1.5; the site returned 403
on 2026-10-21)
- "we've increased the NA from 0.33 in our NXE systems to 0.55 in EXE systems"; "the system's mirrors demagnify it by
  4x in one direction and 8x in the other."

---

## D. Derived values (physics, no new source)

- **Cone half-angle at the mask** = asin(NA / magnification).
  - NXE: asin(0.33/4) = **4.73°**. B7_07 uses this; B6_04 draws 2.6°.
  - EXE 4×/4×: asin(0.55/4) = 7.90°, larger than 6°, so the cones overlap (S10).
  - EXE scan direction 8×: asin(0.55/8) = **3.94°**, so there is room for 5.4° (S10). The gap between the cones is
    2 × (5.4 − 3.94) ≈ 2.9° at 5.4°; it would be 4.1° at 6°. **Lowering the angle narrows the gap; halving the cone opens
    it.**
- **Cone half-angle at the wafer** = asin(NA): 19.3° (0.33) and **33.4°** (0.55).
  - B7_15 draws ≈ 11° (NA ≈ 0.19).
  - B7_03/04 draw atan(0.55·tan θ) = 10.9° and 19.9°.
- **Thin-film colour of a 13 nm membrane.** The first visible interference maximum needs an optical thickness n·d of
  about λ/4. For p-Si (n ≈ 4 in the visible) and d = 13 nm, the first maximum lies near 4·n·d ≈ 210 nm, in the UV.
  So the film shows a uniform faint tint and reflection, not colour bands, like the "black film" of a soap bubble. The
  Mo/Si period (6.8 nm, S8) and the Ru cap (a few nm) are also far too thin for visible colour.
- **Visible diffraction from mask patterns.** A first diffraction order exists only if the pitch p > λ/(1 + sin θi).
  For 400 nm light, p must exceed ≈ 200 nm. A dense EUV mask pitch of 104–160 nm (26–40 nm on the wafer, ×4) gives
  no visible orders. Colours come only from μm-scale periodic areas, block by block (WORKFLOW §9, the chip-rainbow
  lesson).
- **Glow of a 500 °C membrane.** 500 °C = 773 K is about the Draper point (≈ 798 K, 525 °C), the onset of a barely
  visible dull red glow. B6_13 sets the blackbody node to 1050 K (777 °C), a clear orange-red. Either use ≤ 773 K at
  very low strength or mark the glow 示意.
- **Mask-to-wafer scale.** The mask carries the pattern 4× larger (NXE) or 4×/8× larger (EXE) (S1, S10). A morph from
  mask shapes to wafer lines at a fixed scale bar (B6_07) shows the wrong size.
- **Field sizes on the wafer graphics.** The wafer radius is 430 px for 150 mm, so 2.867 px/mm.
  - Full field 26 × 33 mm = 74.5 × 94.6 px; drawn 60 × 80 px (≈ 81 %).
  - Half field 26 × 16.5 mm = 74.5 × 47.3 px; drawn 62 × 42 px (≈ 83–89 %).

## Not public (draw as 示意, never state as fact)
1. The EXE projection-optics mirror count in text, and real mirror radii, prescriptions and absolute sizes
   (high_na_optics.md §5).
2. The hole diameters of M5/M6. Only the pupil obscuration "approximately 20%" is public (S15).
3. Whether M5 is concave or convex. The drawings do not settle it.
4. The pellicle standoff (frame height) and exact membrane dimensions. ASML gives only the 0.2 mm slit and four studs
   (S5).
5. The reticle-handler robot design (S3 gives performance only).
6. The absolute size of the High-NA projection-optics module (only 12 t, > 40,000 parts; S10, S17).
