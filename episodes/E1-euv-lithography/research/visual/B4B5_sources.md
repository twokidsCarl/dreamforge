# B4 / B5 sources: multilayer mirrors, mirror precision, light loss, illuminator

Checked 2026-10-21. Used by `audit_B4.yaml` and `audit_B5.yaml` (S-numbers). Builds on `high_na_optics.md` (cited as
HNO §n) and `euv_source.md` (ES §n); A3 S5/S6 = the CXRO results in `A3_sources.md`. Local copies (not committed):
`renders/review/refs/B4B5/` (pdf/, txt/ = extracted text, png/ = slides rendered with PyMuPDF and looked at, web/,
sheets/ = 3x3 contact sheets of every B4/B5 preview). Slides were viewed as images, not only as text.
Confidence: A = ASML / ZEISS first-party; B = peer-reviewed / book chapter / lab database; C = media (none used).

## S1 ZEISS SMT, "EUV lithography" (A)
https://www.zeiss.com/semiconductor-manufacturing-technology/inspiring-technology/euv-lithography.html
(saved `refs/A3/web/zeiss_euv.html`, text `refs/B4B5/txt/zeiss_euv.txt`)
- "If you were to enlarge such an EUV mirror to the size of Germany, the largest unevenness – the Zugspitze, so to speak – would be a whole 0.1 millimeters high."
- "Extremely thin layers of silicon and molybdenum – only a few atomic layers thick – are vapor-deposited onto the glass surface. For this, up to 100 layers lie on top of each other here. A single layer would only reflect a good one percent of the light – the loss would be far too great."
- "The layer thicknesses are only a few nanometers thin. The result is a reflectivity that makes up to 70 percent of the light usable. This happens through constructive interference: the EUV light is reflected by individual layers in each case. When these are precisely superimposed, the light is amplified because the individual radiation waves are perfectly superimposed."
- "If one of these EUV mirrors were to redirect a laser beam and aim it at the Moon, it would be able to hit a ping pong ball in the Moon's surface." (heading "Precision to the Moon", "maximum tilt stability")
- "The illumination system consists of 15,000 individual parts weighing 1.5 tonnes." / "the projection optics - with six mirrors ... This requires around 20,000 individual parts weighing 2 tonnes."
- "In it, the EUV light from the source is converted into the appropriate illumination for the structures on the mask."
- This page describes the 0.33 NA generation ("up to 100 layers"). Compare S2 and S10 for the layer count.

## S2 ZEISS SMT, "High-NA-EUV lithography" (inspiring technology) (A)
https://www.zeiss.com/semiconductor-manufacturing-technology/inspiring-technology/high-na-euv-lithography.html
(saved `web/inspiring-technology_high-na-euv-lithography.html`)
- "Manufactured to atomic precision and consisting of more than a hundred layers, the mirrors are at the heart of High-NA-EUV technology. Compared to current EUV lithography mirrors, they are significantly larger – and take around a year to manufacture."
- "If the mirrors of High-NA-EUV lithography were to be enlarged to the size of Germany, the measurement technology would need to be able to measure accurately to 100 micrometers."
- "The mirrors for High-NA-EUV lithography are measured in vacuum chambers with a diameter of five meters" ... "The measuring device – located in the five by ten meter vacuum chamber – weighs about 150 tons."
- "A mirror for High-NA-EUV lithography is about twice as large and ten times as heavy as current EUV mirrors."
- "the illumination system weighs around six tons – four times more than before. More than 40,000 parts of the projection optics for High-NA-EUV lithography weigh around twelve tons"
- "The illumination system of High-NA-EUV lithography consists of more than 25,000 parts and weighs over six tons."
- "The large numerical aperture of the optics for High-NA-EUV lithography requires larger mirror surfaces with even more extreme curvatures and therefore even more precision."

## S3 ZEISS SMT magazine, "High-NA-EUV lithography" (interview, P. Kürz) (A)
https://www.zeiss.com/semiconductor-manufacturing-technology/smt-magazine/high-na-euv-lithography.html (saved `web/smt-magazine_high-na-euv-lithography.html`)
- "The mirrors used for High-NA-EUV technology weigh several hundred kilograms – making them about twice as large and ten times as heavy as current EUV mirrors."
- "The new generation of mirrors is machined for months in SMT production until it has the required precision. If they were enlarged to the dimension of Germany, the deviation would be only a tenth of a millimeter."
- "a five-by-ten-meter vacuum chamber consisting of more than a hundred thousand parts and a total weight of more than 150 tons."
- "the projection optics consists of over 40,000 parts and weighs approximately twelve tons ... [the illumination system] weighs more than six tons and consists of more than 25,000 parts."

## S4 ASML, "Lenses & mirrors" (A)
https://www.asml.com/en/technology/lithography-principles/lenses-and-mirrors (saved `refs/A2/asml_lenses-and-mirrors.html`)
- "Our state-of-the-art EUV lithography machines, whose largest mirrors are 1 meter across and smooth down to tens of picometers, have an NA of 0.55."
- Use: the only first-party absolute size for a High-NA mirror. Cross-check: S6 slide 19 scales a High-NA mirror to Germany (850 km) "by ~1 million", i.e. about 0.85 m (derived).

## S5 ZEISS, Bihr, Gräupner, Jürgens, Neumann, Bilski, "Past, Present and Future – ZEISS EUV Optics", EUVL Workshop, 9 June 2022 (A)
https://euvlitho.com/2022/P53.pdf (`pdf/euvlitho2022_P53.pdf`; the copy in refs/highna/ was truncated, re-downloaded)
- Slide 5 (in the "0.33NA EUV optics" section): "The most precise mirror in the world: If we were to enlarge an EUV mirror to the size of Germany, the largest deviation from the nominal shape would be just 0.1 millimeters." (scale bar: EUV mirror 0.1 mm, space mirror 2 cm, household mirror 5 m, Zugspitze 2,962 m)
- Slide 6 (same section): "Mirror tilts controlled with sub nrad accuracy for sub nm image placement" ... "≈ 390,000 km" ... "Sensors and actuators in ZEISS projection optics work so precisely that you would hit a golf ball on the surface of the moon with the deflected laser beam."
- Slide 10: "High-NA illuminator will utilize 0.33NA technology with actuated facet mirrors" ... "High-NA illuminator provides 20% pupil fill ratio".
- Slide 12: "Obscuration reduces angular load and angle variation"; "SMO avoid obscuration".
- Slide 14 photos: "Illuminator frame", "POB frames after integration test" (a wide, flat, angular frame block with cable looms), "Mirror modules with aluminum dummies".

## S6 ZEISS + ASML, Wischmeier, Graeupner, Kuerz, Stoeldraijer, van Schoot, "High NA EUV optics: a big step in lithographic resolution", EUVL Workshop, 10 June 2021 (A)
https://euvlitho.com/2021/P52.pdf (`refs/highna/euvlitho2021_P52/doc.pdf`)
- Slide 13: "High-NA illuminator will utilize 0.33NA technology with actuated facet mirrors"; drawing: IF, green cone to an elliptical "Field Facet Mirror" carrying arc-shaped (curved strip) facets, beamlets down to a "Pupil Facet Mirror" of round facets on short cylinders, some red (lit); "Standard Illumination Settings" icons (conventional and annular with a central hole, x/y dipoles, quadrupoles/quasars, hexapoles, slim dipoles) and "Tachyon SMO pupils"; "High-NA illuminator provides 20% pupil fill ratio"; "More focus on medium sigma dipoles".
- Slide 15 "Build up of system integration tooling": "mirror glueing", "mirror module assembly", "force frame & module integration", "sensor frame & interferometer assembly".
- Slide 16 "Optics manufacturing process": Grinding, Polishing, Ion beam Figuring, Coating, Surface Figure Metrology, Roughness metrology, Reflectivity metrology.
- Slide 18: "Mirror roughness after polishing rms = 47pm / 61pm / 50pm / 42pm"; "6 Decades" of spatial frequency.
- Slide 19 "Challenges scale with accuracy and size – Atomic level figuring required": "Germany 850km", "Zugspitze 2962m", "High-NA mirror ... RMS ~ 20 pm", "Scale to size of Germany by ~1 million", "heights of ~20µm in Germany or 1/5 of a human hair". The mirror photo is a thick disc that reflects the room like a plain mirror (no colour bands).

## S7 ZEISS, Kaumanns, Neumann, Conradi, Graeupner, "Status and outlook of EUV optics at ZEISS", EUVL Workshop, 6 June 2024 (A)
https://euvlitho.com/2024/P22.pdf (`refs/highna/euvlitho2024_P22/doc.pdf`)
- Slide 8 "Creating the heart of NA 0.55 EUV technology... High-precision optics with two function modules": Illumination system "> 25.000 individual parts, ~ 6 t weight"; Projection optics "> 40.000 individual parts, ~ 12 t weight", "< 1 Å mirror surface figure control", "< 0.1 nrad mirror tilt control". The projection-optics render is a wide, angular frame block (about 1.6x wider than tall) with cable looms. A photo shows the mirror metrology vacuum chamber: a horizontal cylinder with a large round end door, blue columns, people in clean-room suits for scale.
- Slide 13 "Current 0.55 NA" render: IF -> small fold mirror -> field facet mirror (top) -> pupil facet mirror (bottom) -> reticle (HNO §1.4).

## S8 ZEISS + ASML, Liddle, Zimmermann, Neumann, Roesch, Gehrke, Kneer, van Setten, van Schoot, van de Kerkhof, "Latest developments in EUV optics", EUVL Workshop, 15 June 2017 (A)
https://www.euvlitho.com/2017/P23.pdf (`pdf/euvlitho2017_P23.pdf`, slides `png/z17_p4/p5/p6/p10.png`)
- Slide 4 "Starlith 3300 illuminator – Actuated fly's eye unit enables lossless setting changes": IF, cone to the field facet mirror (elliptical carrier, ~12 curved arc-shaped facets), beamlets to the pupil facet mirror (round facets, red = lit); "Standard pupil shapes": "conventional setting" (22 nm hp), "off-axis illumination" (< 22 nm hp): annular, dipoles, quadrupoles.
- Slide 5: "Starlith 3350 • 2 pupil facets per field facet"; "Starlith 3400 • many pupil facets per field facet"; "≈ 40% pupil fill ratio" (3350), "≈ 20%" (3400).
- Slide 6 "New application specific pupil types": "Quasar – Contact Hole array 18 nm half-pitch; H&V Lines&Spaces 18 nm half-pitch"; "Small conventional – Logic (irregular contacts)"; "Rotated Dipoles 22° – 13 nm hp SE"; "Hexapoles – DRAM storage node". Poles are drawn as leaf/lens shapes made of dots.
- Slide 8: "Dipole Y" for horizontal lines (3D mask effect example).
- Slide 10 "Freeform pupil shapes": "all examples without light loss (100% illuminator efficiency) on Starlith 3400 illumination system".
- Slide 13: "Reduced PFR translates in improved contrast and LCDU, (without loss of light down to 20% PFR)".
- These are NXE (0.33 NA) statements.

## S9 ASML, J. van Schoot, "High NA EUV: Getting closer to introduction", EUVL Workshop, 7 June 2022 (A)
https://euvlitho.com/2022/P3.pdf (`refs/highna/euvlitho2022/P3.pdf`, slides `png/vs22_p36.png`, `vs22_p39.png`)
- Slide 36 "High NA flexible illuminator design available – Principle NXE:3300/3400 illuminator can be reused": "pupil @ mask" (ellipse, dipole of dots) -> "pupil @ wafer" (circle); "Illuminator elliptical pupil is projected in a circular pupil at the wafer"; FFM with arc-shaped facets, PFM with round facets.
- Slide 39 "Optics Sub-system: Assembly and qualification in progress – Mirrors at final shape, mirror metrology system reached final accuracy level": photos "Projection optics – Frame integration" (angular frame hanging from a crane), "Coated mirror – Qualified with reflectometer and interferometer" (a large curved mirror in a mount, plain mirror finish), "Illuminator – Frame integration".

## S10 ZEISS, W. Kaiser, "Starlith 3400: Projection Optics", VLSI-TSA, Taiwan, 20 Feb 2019 (A)
https://www.euvlitho.com/2019/P24.pdf (`refs/A3/pdf/zeiss2019_P24.pdf`; slides `kaiser2019_s18/s19/s23.png`)
- Slide 18 "Mirror manufacturing": photo of a finished EUV mirror, plain silvery, reflecting the worker.
- Slide 19 "Figure control on atomic level": "Computer Controlled Polishing | Ion Beam Figuring | Interferometric Surface Metrology", "multiple iterative loops".
- Slide 22: "What does 50pm surface deviation mean? Correspond to heights of 100µm in Germany."
- Slide 23 "Coating technology: The multilayer coating defines EUV.": "EUV Coating: Mo/Si Bragg Reflectors" sketch: incident ray a few degrees (θ) from the normal, several parallel reflected rays leaving from successive interfaces, straight (unbent) ray through the stack, Mo layers thinner than Si layers on a "Substrate"; a cross-section micrograph (dark/light bands); "> 50 Bi Layers"; "Reflectivity >67%, high bandwidth"; "Layer thickness control <0.2%".
- Slide 24: "EUV mirrors can control the position of an image on the moon with less than 20cm accuracy"; "Mirror tilts controlled with sub nrad accuracy to enable sub nm image placement."

## S11 G. Panici, D. N. Ruzic (Univ. of Illinois), "Tin Mitigation in EUV Sources", Chapter 18 in an SPIE Press book (2023 download) (B)
https://cpmi.illinois.edu/files/2023/10/Ch18-1.pdf (`pdf/cpmi_ch18.pdf`) - the source of F7 / F33.
- p.749: "Upwards of 50 alternating layers of molybdenum (Mo) and silicon (Si) are used to build these mirrors atop of a substrate." "While each bilayer reflection is small, the total sum of the stack can reach 70% at 13.5 nm."
- p.750: "even with perfectly deposited bilayers and normal incidence, peak reflectivity is 74%." "Active cooling of the mirrors is a necessity in these vessels." "A layer of ruthenium coats the top of the mirror due to its protection against oxidation."
- p.751: "Modern mirrors reflect only up to 68% of the incident flux." "If 100 W of EUV photons are created by the LPP and make it into the scanner, the wafer will see 1.0 W at best since there are 10 mirrors total." Fig. 18.4 caption: "There are upwards of ten mirrors in the scanner alone ... Each of these mirrors has, at most, 68% reflectivity ... Only 1% of the light that exits the source reaches the wafer."
- Arithmetic check (ours): 0.68^10 = 2.1 %, 0.70^10 = 2.8 %, 0.70^11 = 2.0 %, 0.66^11 = 1.0 %. "1 W at best" is looser than its own numbers.

## S12 CXRO, X-ray interactions with matter, mirror reflectivity (B, LBNL database)
https://henke.lbl.gov/cgi-bin/mirror.pl (form https://henke.lbl.gov/optical_constants/mirror2.html), single bulk surface, sigma 0, unpolarised. Saved `web/mirror_*.dat`.

| material | grazing angle | R at 13.5 nm |
|---|---|---|
| Ag 10.5 g/cm3 | 90 deg (normal) | 0.0051 |
| Ag | 63 deg (27 deg from normal, as in B4_01) | 0.0056 |
| Al 2.7 | 90 deg | 0.00022 |
| SiO2 2.2 (glass) | 90 deg | 0.00015 |
| Ru 12.4 | 5 deg (grazing) | 0.943 |
| Ru | 10 deg | 0.883 |

- A household mirror is silvered on the back, so EUV meets the glass first and is absorbed within ~0.1 um (A3 S5: SiO2 attenuation length 0.0997 um); it never reaches the silver.
- At grazing incidence metals reflect EUV well (Ru 94 % at 5 deg), so the B4_01 storyboard note "镜面与入射光成小角度" must not be read as grazing.

## S13 Liu et al., "Comparative Study on Microstructure of Mo/Si Multilayers Deposited on Large Curved Mirror with and without the Shadow Mask", Micromachines 14 (2023) 526 (B, open access)
https://pmc.ncbi.nlm.nih.gov/articles/PMC10055843/ (`refs/B2/mosi_pmc10055843.xml`)
- Table 3 (fit, no shadow mask, X = 47.5 mm): "Mo 2.140 [nm] ... Mo-on-Si 0.802 ... Si 3.720 ... Si-on-Mo 0.409" (period about 7.07 nm).
- Table 4: Mo crystallite size "2.15" / "2.17" nm; text: "the peak mainly correspond to Mo (110) crystallites".
- Use: Mo is the thinner layer (about 0.3-0.4 of the period); Mo is polycrystalline with ~2 nm grains, so there is no extended single-crystal sheet in the stack. Closes the B2 audit's open question on the Mo/Si split. CXRO design value Gamma = 0.4 (A3 S6) gives Mo 2.8 nm / Si 4.1 nm for d = 6.9 nm.

## S14 ASML, van de Kerkhof et al., "Defectivity Improvements Enabling HVM for EUV Scanners", EUVL Workshop 2019, slide 2 (A)
https://www.euvlitho.com/2019/P23.pdf (see B2_sources.md S4)
- "Driven by prevention of oxidation of Ru-coated mirrors and removal of carbon growth". The top of a scanner mirror is a Ru cap, not bare Si or Mo.

## S15 NASA NSSDC, Moon fact sheet (A for the numbers)
https://nssdc.gsfc.nasa.gov/planetary/factsheet/moonfact.html (saved `web/nasa_moon.html`)
- "Semimajor axis (10^6 km) 0.3844"; "Volumetric mean radius (km) 1737.4 [Moon] 6371.0 [Earth] 0.2727 [ratio]"; atmosphere "Surface pressure (night): 3 x 10^-15 bar" (so the lunar sky is black).
- Golf ball diameter not less than 42.67 mm (R&A / USGA Equipment Rules, Part 4; standard value, page not fetched).

## Conflicts noted (use the most authoritative, say why)
1. Layer count: S1 "up to 100 layers" (0.33 NA web page) vs S10 "> 50 Bi Layers" (Starlith 3400 = more than 100 layers) and S2 "more than a hundred layers" (High-NA). The film shows High-NA: use 上百层 / 100 多层, not 最多约 100 层.
2. Moon analogy: S1 "ping pong ball", S5 slide 6 "golf ball" (0.33 NA section, "sub nrad"), S10 slide 24 "less than 20cm". The <0.1 nrad figure is High-NA (S7 s.8). A mirror tilt δ moves the reflected beam by 2δ: 2 x 0.1 nrad x 384,400 km = 7.7 cm, about 1.8 golf-ball diameters. Keep ZEISS's analogy as an analogy; do not write "≈" between 0.1 nrad and the golf ball.
3. Germany: 0.1 mm maximum deviation (S1, S3 for High-NA, S5 s.5), 100 um for 50 pm (S10 s.22), but ~20 um for the High-NA RMS 20 pm (S6 s.19). 0.1 mm is a peak value, 20 um an RMS value (F9 / F29 note).
4. Manufacture time: S2 "take around a year to manufacture" vs S3 "machined for months". Both compatible with 约一年 if the whole process is meant; F31 uses S2.
5. Illuminator efficiency: "100% illuminator efficiency" / "lossless" is said for Starlith 3300/3400 (NXE) only (S8). For High-NA ZEISS says it reuses that technology (S5 s.10, S6 s.13); no explicit High-NA efficiency statement.

## Not public
1. Facet count and exact facet shape of the EXE field and pupil facet mirrors (only schematic drawings: arc-shaped field facets, round pupil facets).
2. End-to-end EUV transmission of the EXE (IF to wafer) as a number. ZEISS only says the obscuration "significantly increases the transmission ... vs. 3300" (HNO §1.2).
3. Diameter of the NXE ("previous generation") mirrors; only the ratio "about twice as large" is public. Largest EXE mirror about 1 m (S4).
4. How mirrors are loaded into the 150 t metrology chamber.
5. The exact mirror-holding structure (mounts, actuator layout) inside the High-NA projection optics.
