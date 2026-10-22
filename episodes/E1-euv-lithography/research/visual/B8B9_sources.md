# B8 / B9 sources: stages, scanning, alignment, overlay, throughput, photon budget, stochastics

Checked 2026-10-21. Used by `audit_B8.yaml` and `audit_B9.yaml` (S-numbers). Builds on `high_na_optics.md` (cited as
HNA [tag] slide n), `euv_source.md` and `B1_sources.md`, which are not repeated here. Local copies (not committed):
`renders/review/refs/B8B9/` (web/ = page text read through the r.jina.ai text proxy because asml.com answers 403 to
curl; pdf/ = downloaded PDFs; sheets/ = 3x3 contact sheets of every B8/B9 preview).
Confidence: A = ASML / ZEISS / TRUMPF / Intel first-party; B = SPIE/EUVL paper by vendor authors, patent, customer
first-party, peer-reviewed or textbook chapter; C = media (not usable on screen).

## S1 ASML, Wilton CT location page (A)
https://www.asml.com/en/company/about-asml/locations/wilton-ct (saved `web/company_about-asml_locations_wilton-ct.md`, lines 252-260)
- "In Wilton, we design, test and assemble two crucial modules of our lithography systems: the reticle handler and the reticle stage."
- "Once the reticle is received, the reticle stage securely holds it in place, without distorting or allowing it to move by more than a few picometers. The completely magnetically levitated stage accelerates at more than 15 g, more than three times the g-force experienced by a fighter jet pilot at takeoff, up to a constant velocity of more than three meters per second. It positions the reticle within fractions of nanometers in all six degrees of freedom at full speed."
- "The motors that propel the reticle stage generate more than 10,000 newton (N) of thrust force, which would be like dropping a car onto the reticle stage every time it accelerates."
- Consequences: (a) the 10,000 N, the car and the "few picometers" belong to the same paragraph as the ">15 g" stage, which is the NXE value (F15b). They are not EXE numbers. (b) The stage is "completely magnetically levitated", so it does not run on contact rails. (c) The page does **not** contain "nanometer and nanosecond". F51 cites this page wrongly; the sentence is on S3.

## S2 ASML, "5 things you should know about High NA EUV lithography" (2024) (A)
https://www.asml.com/en/news/stories/2024/5-things-high-na-euv (saved `web/news_stories_2024_5-things-high-na-euv.md`, lines 30-38). This is HNA [ASML5].
- "the system's mirrors demagnify it by 4x in one direction and 8x in the other."
- "Because of their anamorphic optics, EXE systems have exposure fields half the size of their NXE predecessors. It therefore takes twice as many exposures to pattern a single wafer."
- "The wafer stage in an EXE system accelerates at 8g, twice as fast as the NXE's wafer stage. And the EXE's reticle stage accelerates four times faster than the NXE's – 32g, the equivalent of a race car going from 0 to 100 km/h in 0.09 seconds."
- "With its new stages, the TWINSCAN EXE:5000 can print more than 185 wafers per hour ... And we have a roadmap for increasing that to 220 wafers per hour in 2025."
- Also HNA [Z24] slide 9: "4× reduction in non-scan direction, 8× reduction in scan direction"; HNA [A22] slide 27: "X=4x mag, Y=8x mag", half-field mask "104 mm [x] × 132 mm [y]"; HNA [A22] slide 12: half field 26 mm × 16.5 mm; HNA [A22] slide 14: "188 half fields per wafer"; HNA [A21] slide 34: the reticle scans along its 132 mm side and the wafer moves antiparallel.
- Consequence: on the EXE the reticle must move **8x** faster than the wafer in the scan direction. "缩小 4 倍 → 快 4 倍" is the NXE case.

## S3 ASML, "Mechanics and mechatronics" (A)
https://www.asml.com/en/technology/lithography-principles/mechanics-and-mechatronics (saved `web/technology_lithography-principles_mechanics-and-mechatronics.md`, lines 143-165)
- "Sensors that measure positioning 20,000 times per second with an accuracy of 60 picometers (less than the size of a silicon atom)?" (intro)
- "In 2008, ASML's NXT TWINSCAN platform brought another significant improvement ... a novel magnetic levitation system for moving the stages to enable much greater accelerations – up to 5 g ... Meanwhile, the position of the wafer is measured some 20,000 times per second using sensors that are accurate to around 60 picometers – that's less than the size of a silicon atom."
- "the magnetically levitating wafer tables that hold the wafer in place inside the system accelerate at up to 7 g"
- "In an ASML lithography machine, the stage moves two wafer tables simultaneously, each holding a silicon wafer. While one wafer is being exposed, the position of the other wafer is measured by the machine's metrology sensors."
- "As each copy of the pattern is printed on the wafer, the reticle moves smoothly through a narrow slit of light, exposing only a small part of the pattern at a time. Meanwhile, the wafer moves smoothly in the opposite direction to capture the whole pattern. ... The ability to synchronize the motion of wafer and reticle to the nanometer and nanosecond as they accelerate at 5 g and 15 g in opposite directions ..."
- Consequences: the 60 pm figure is given in the NXT (DUV) paragraph, so it is an ASML-generic number and not an EXE spec. The nanometre/nanosecond sentence is the real source of F51. The wafer tables are maglev; there is no row of contact actuators with lamps.

## S4 ASML, EUV lithography systems product page (A)
https://www.asml.com/en/products/euv-lithography-systems (saved `web/products_euv-lithography-systems.md`, line 275)
- "The wafer stage positions the wafer to within a quarter of a nanometer for each exposure, checking and adjusting 20,000 times per second." (generic EUV, F15)

## S5 ASML, "Measuring accuracy" (A)
https://www.asml.com/en/technology/lithography-principles/measuring-accuracy (saved, line 274)
- "A single lithography system can generate up 31 terabytes of data per week from its sensors alone – that's three times more than the Hubble Space Telescope gathers in a year." (not tied to a model)
- line 252: "Hundreds of sensors ... coordinate the necessary tweaks ... at the sub-nanometer scale, using thousands of actuators."

## S6 ASML, "Aligning lithography to the nanometer" (Simon Mathijssen, 2021) (A)
https://www.asml.com/en/company/stories/2021/fellow-simon-mathijssen-aligning-lithography-nanometer (saved)
- "When it enters the system, the wafer is initially positioned with a precision of around 80 micrometers – about the diameter of an average human hair. ... To make the jump to sub-nanometer accuracy, ASML's systems use an optical alignment sensor that calculates the wafer's position based on how light reflects from special features on the wafer called 'alignment marks'."
- "Alignment marks are specially designed gratings that are created on the wafer alongside each layer's pattern."
- "The big difference is the number of marks. For wafer positioning, there are tens of alignment markers. For overlay, there could be over 1,000," (said about **overlay metrology**, which the article links to the YieldStar page)
- "A lithography system's ability to line up one pattern with the previous one is measured by its overlay performance."
- Consequences: the scanner reads **tens of alignment marks** to get from 80 um to sub-nm. "Over 1,000" are overlay-metrology marks, and those are not what corrects the wafer position. F44 and the B8_13 line/overlay conflate the two. The marks are gratings, not crosses.

## S7 ASML, "TWINSCAN: 20 years of lithography innovation" (2021) (A)
https://www.asml.com/en/news/stories/2021/twinscan-20-years-innovation (saved, line 26)
- "TWINSCAN was the first – and is still the only – lithography system platform with two complete wafer table modules (or wafer stages). ... When the wafer on table one is being exposed, another wafer is loaded on table two and then aligned and mapped. The tables then swap position so that the wafer on table two is exposed while the wafer on table one is unloaded."
- line 28: "The first TWINSCAN system with this revolutionary dual-stage technology was shipped in 2001." (F58 says 2000; it is not drawn in B8)

## S8 ASML, TWINSCAN EXE:5000 / EXE:5200B product pages (A)
https://www.asml.com/en/products/euv-lithography-systems/twinscan-exe-5000 , .../twinscan-exe-5200b (saved)
- "The dual-stage extreme ultraviolet (EUV) lithography system ..."
- "The anamorphic mirrors require an exposure field half the size of that in NXE systems ... The EXE:5000 therefore has new, faster wafer and reticle stages"
- The spec block reads "Wafers per hour / At dose: 50 mJ/cm²" (EXE:5000 and EXE:5200B). The digits are JS counters and did not render. The NXE:3800E page reads "At dose: 30 mJ/cm2".

## S9 Maas, Lercel, Smeets, Young (ASML), "EUV Industrialization", EUVL Workshop 2023, P62 (B, ASML authors)
https://euvlitho.com/2023/P62.pdf (saved `pdf/euvlitho2023_P62.pdf`)
- p.16: "NXE:3800E throughput ≥220 wph at 0.9 nm Matched Machine Overlay" ... "Throughput specification (96 full fields, 30mJ/cm2)"; the module list includes "Reticle Clamp – Improved thermal stability", "Reticle Stage – Higher acceleration supporting ≥220 wph", "Wafer Stage – Faster wafer stages with increased step & scan speeds".
- p.17: "Increased Sn droplet velocity and repetition rate show 10% increased CE and >500W EUV power at IF." "Higher acceleration wafer stages running under interferometer and lot operation software control."
- p.19 roadmap: "EXE:5000 1.1 nm | 150 wph"; "EXE:5200B <0.8 nm | 220 wph".
- Consequences: (a) 96 fields and 220 wph are **NXE:3800E** numbers. (b) Source power is stated **at the intermediate focus (IF)**, i.e. the light entering the scanner. (c) The NXE:3800E wafer-stage control text mentions interferometers, so drawing an encoder grating as "the" EUV sensor is not supported.
- Geometry check (computed, not from the slide): 96 x 26 x 33 mm = 82,400 mm², more than the area of a 300 mm wafer (70,700 mm²). So "96 full fields" must include edge fields that overhang the wafer edge. With 26 x 33 mm fields, a grid offset by half a field in y, and every field touching the 294 mm usable disc counted, the count is exactly 96. Only about 64 fields fit wholly inside.

## S10 Intel Foundry blog, December 2025 (B, customer first-party)
URL as published: https://community.intel.com/t5/Blogs/Intel-Foundry/Systems-Foundry-for-the-AI-Era/How-Collaboration-in-High-NA-EUV-and-Transistor-R-D-Are-Shaping/post/1730050
(now 301-redirects to an Intel search page; the text below is the verbatim quotation of the post in https://x.com/theaustinlyons/status/2000623709120536712, which links to it)
- "Today we are excited to share that Intel and ASML have reached the milestone of "acceptance testing" on the TWINSCAN EXE:5200B. This High NA EUV tool maintains the high resolution of the first-generation EXE:5000, while expanding output to 175 wafers per hour and improving overlay (accurate alignment of different lithography layers) to 0.7 nanometers."
- Consequences: F43b (now grade C, Bits&Chips) can be raised to B with this source. The 0.7 nm belongs to the **EXE:5200B**, not to the EXE:5000 that the film depicts. Media reports add "175 wph at 50 mJ/cm²"; Intel's text gives no dose.

## S11 Stoeldraijer et al. (ASML), "NXE platform", EUVL Symposium 2009 (B, ASML authors)
https://euvlsymposium.lbl.gov/pdf/2009/pres/O_ET-01_Stoeldraijer_ASML.pdf (saved `pdf/stoeldraijer2009.pdf`), slide 7
- "Wafer Stage: Dual planar stage + balance mass; E-clamp"
- "Reticle Stage: Building on Alpha and advanced TWINSCAN; E-clamp from Alpha; new REMA (X and Y)" (REMA = reticle masking blades)
- slide 11: "CO2 Laser amplifiers in subfab"
- With HNA [C11] slide 5 ("reticle (top, facing down)") and the HNA §1.4 drawings: the EUV reticle is held by an electrostatic clamp on its backside, pattern facing **down**, and lit from below.

## S12 ZEISS patents on the arc-shaped slit (B)
- US8717541B2 (Carl Zeiss SMT), "Field facet mirror for an illumination optics of a projection exposure apparatus for EUV microlithography": "a part ring or arc shape of the field facets can allow well adapted illumination of a correspondingly part ring-shaped or arcuate object field." https://patents.google.com/patent/US8717541B2/en
- US7126137B2 (Carl Zeiss SMT): "Scanning uniformity is a problem of the aforementioned scanning exposure systems in illuminating a slit, particularly a curved slit." "the curved slit is typically represented by a segment of a ring field, which is also called an arc shaped field." https://patents.google.com/patent/US7126137B2/en
- HNA [Z21] slide 11: the High-NA exposure slit at the wafer is a "26 × 1.6 mm²" arc, at the reticle "104x12.8 mm²", drawn curved.
- Consequence: the slit's shape comes from the illuminator's field facets (imaged onto the reticle). It is not two blades pinching a glow above the wafer. The blades (REMA, S11) frame the field near the reticle.

## S13 US5831716A, "Slit-scanning type light exposure apparatus" (B, patent; F57 source)
https://patents.google.com/patent/US5831716A/en
- "As the reticle R and the wafer W are scanned in the opposite directions at the same constant speeds in complete synchronism with each other ..." Exposure happens at constant speed, so thrust is near zero while the slit exposes.

## S14 Ruzic group, "Tin Mitigation in EUV Sources", SPIE ebook chapter 18, p.751 (B, textbook chapter; F33 source)
https://cpmi.illinois.edu/files/2023/10/Ch18-1.pdf (saved `pdf/illinois_ch18.pdf`)
- "Mo/Si ... reflect only up to 68% of the incident flux."
- "If 100 W of EUV photons are created by the LPP and make it into the scanner, the wafer will see 1.0 W at best since there are 10 mirrors total."
- Fig. 18.4 caption: "There are upwards of ten mirrors in the scanner alone. ... Each of these mirrors has, at most, 68% reflectivity ... Only 1% of the light that exits the source reaches the wafer."
- Consequence: 100 W is a **hypothetical round number** for the power that enters the scanner. It is not a measured value, and there is no loss between "EUV 产生" and "进入扫描仪" in this example. Real NXE:3800E: >500 W at IF (S9).

## S15 imec Magazine, "EUV lithography: sailing along the stochastic cliffs" (July 2019) (B, imec research institute)
https://www.imec-int.com/en/imec-magazine/imec-magazine-july-2019/euv-lithography-sailing-along-the-stochastic-cliffs (saved)
- "Stochastic printing failures are random, non-repeating, isolated defects such as microbridges, locally broken lines and missing or merging contacts. ... the energy from the light source is distributed over less photons. ... Besides this so-called "photon shot-noise effect", stochastic effects originate from the molecular nature of matter, and the probabilistic behavior of their interactions."
- "the use of higher dose resists is increasingly more accepted. And indeed, it does push back one of the cliffs (the microbridges) but, surprisingly, does not appear to have an effect on the second cliff (the broken-line cliff) nor on the floor. So, it is not a miracle switch."
- Also: De Bisschop, "Stochastic effects in EUV lithography: random, local CD variability, and printing failures", JM3 16(4) 041013 (2017), doi:10.1117/1.JMM.16.4.041013.

## S16 ASML on why source power goes up (A/B)
- ASML Annual Report 2025 story (B1 S3, saved `renders/review/refs/B1/web/asml_ar2025_stories.md`): "1,000-watt EUV light source power shows path to higher productivity"; "It is a critical step toward faster, more cost-efficient production of tomorrow's cutting-edge microchips".
- Hummler et al. (ASML), Proc. SPIE 12953, 129530V (2024), abstract: "The NXE:3800E system marks a substantial step forward in scanner productivity, delivering a remarkable increase of (+60 WPH) in throughput, made possible by an increase in EUV source power (to >500W)."
- Umstadter et al. (ASML), Proc. SPIE 12494 (2023), abstract: "Sources at customers operate at ~250 Watt power"; "reaching a new 600W milestone for EUV Sources" on "ASMLs research systems".
- Consequence: ASML gives **productivity** as the reason for more watts. That more power buys more dose (more photons) at the same throughput is physics (wph is specified at a dose, S8/S9). It is not ASML's stated motive.

## S17 Physical constants (A, NIST/CODATA) and derived geometry
- hc = 1239.84198 eV·nm (CODATA 2018). 13.5 nm -> 91.84 eV; 193 nm -> 6.424 eV; ratio 14.30.
- 1 eV = 1.602177e-19 J, so one EUV photon = 1.4714e-17 J. 30 mJ/cm² = 3.0e-16 J/nm² -> 20.4 photons/nm²; 50 mJ/cm² -> 34.0; 20 mJ/cm² -> 13.6. Poisson with mean 20 has SD 4.5.
- Silicon lattice constant a = 543.102 pm (NIST, F60). Nearest-neighbour distance a·√3/4 = 235.2 pm. Viewed along [110]: "dumbbells" of two atoms separated along [001] by a/4 = 135.8 pm. They sit on a centred rectangular cell a/√2 x a = 384.0 x 543.1 pm, so the dumbbells repeat every 384.0 pm along a row and the rows are 271.6 pm apart, shifted by 192.0 pm.

## S18 SVMI 300 mm prime wafer datasheet SV029, citing the SEMI standard (B, vendor spec)
https://svmi.com/wp-content/uploads/2021/01/SV029.pdf (saved `pdf/svmi_SV029.pdf`)
- "Diameter mm 300±0.20 | Thickness µm 775±25 | Notch – SEMI Standard | Notch depth mm 1.0 + 0.25 – 0.00 | Notch angle 90° +5° -1° | Edge exclusion mm 3.0"

## Not public / not found
1. EXE:5000 reticle-stage thrust (the 10,000 N figure is for the >15 g stage), EXE reticle/wafer stage mass and speed.
2. The position-sensor type and accuracy for the EXE wafer stage specifically (60 pm is quoted in the NXT paragraph).
3. EXE total mirror count and its source-to-wafer transmission (only the generic "about 10 mirrors, about 1%" textbook figure, S14).
4. A first-party text saying the stage alternates scan direction field to field (standard meander practice, but no quote was found).
5. The EXE:5000 throughput dose used in the 2024 "more than 185 wph" sentence (HNA [A22] footnote: "185wph@20mJ/cm2").
