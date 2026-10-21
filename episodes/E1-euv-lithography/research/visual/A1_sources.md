# A1 visual audit: sources and exact quotes

Backs `research/visual/audit_A1.yaml`. Grades follow WORKFLOW 2.2 (A = vendor official, B = paper / patent / customer primary, C = media).
Downloads (not committed) are in `renders/review/refs/A1/`. Quotes copied from the downloaded files are verbatim. For S1, S2, S4, S5 and S12 the quotes come from a page fetch, are short, and are marked "(page fetch)".

---

## S1. ASML, "How microchips are made" (A)
https://www.asml.com/en/technology/all-about-microchips/how-microchips-are-made (page fetch)
- "Microchips are made by building up layers of interconnected patterns on a silicon wafer."
- "Modern chips can have up to 100 layers, which all need to align on top of each other with nanometer precision."
- EUV is used "for the most critical layers with the smallest features"; DUV prints the less critical layers.

Used for: A1_08 (layer count, with the S3 conflict), A1_09.

## S2. ASML story, "Fellow Simon Mathijssen: aligning lithography to the nanometer" (2021) (A)
https://www.asml.com/en/company/stories/2021/fellow-simon-mathijssen-aligning-lithography-nanometer (page fetch; also F44)
- "As many as 100 of these patterns are needed to make a microchip" ... they "all have to align with each other precisely for the chip to work."
- "the patterns in different layers have to line up with extreme accuracy."
- "A lithography system's ability to line up one pattern with the previous one is measured by its overlay performance."
- The most advanced systems "deliver overlay performance better than 2 nm."
- The wafer is "initially positioned with a precision of around 80 micrometers."
- Alignment marks are "specially designed gratings that are created on the wafer alongside each layer's pattern."
- "For overlay, there could be over 1,000." (marks)

Used for: A1_08, A1_10 (alignment before exposure, overlay < 2 nm).

## S3. ASML Annual Report 2021 (Form 20-F) (A)
https://www.sec.gov/Archives/edgar/data/937966/000093796622000013/asml-20211231.htm ("How microchips are made" / "Taking a closer look inside a fab" sections). Local: `refs/A1/asml_20f_2021.htm`
- "To make an entire microchip, this process is repeated layer after layer, stacking the patterns to create an integrated circuit (IC). The simplest chips have around 40 layers, while the most complex can have over 150 layers."
- "The size of the features to be printed varies depending on the layer, which means that different types of lithography systems are used for different layers – our latest-generation EUV systems for the most critical layers with the smallest features, and ArFi, ArF, KrF and i-line systems for less critical layers with larger features."
- "Microchips are made of layers about 50 to 150 nm thick that are built on the semiconductor substrate one layer at a time. Some microchips can have up to 150 or more layers of varying complexity. Typically, the most complex layers are at the bottom and the least complex at the top."

Used for: A1_02 (layers on a substrate, film thickness), A1_07 (repeat and stack; upper layers coarser), A1_08 (**conflict**: over 150 vs S1/S2/S5's up to 100), A1_09 (finest at the bottom).

**Conflict (WORKFLOW 2.4.4):** ASML's website (S1, S2, S5) says "up to 100" / "as many as 100"; ASML's 2021 annual report says "over 150" / "up to 150 or more". 上百层 fits both; 最多约 100 层 is contradicted by the annual report.

## S4. ASML, EUV lithography systems product page (A)
https://www.asml.com/en/products/euv-lithography-systems (page fetch)
- "EUV systems are used to print the most intricate layers on a chip"
- "Chipmakers use our NXE systems to print the highly complex foundation layers of their 7 nm, 5 nm and 3 nm nodes."
- The optics shrink "the reticle pattern by a factor of four".

Used for: A1_04 (real scanners reduce 4x; corrected in B7), A1_09 ("foundation layers" = bottom).

## S5. ASML story, "The popularity of maturity" (2023) (A)
https://asml.com/en/news/stories/2023/the-popularity-of-maturity (page fetch)
- Today's most advanced chips "can have as many as 100 layers of extremely tiny electronic features."
- "Printing the most sensitive layers of these chips requires ASML's most advanced technology: extreme ultraviolet (EUV) lithography"
- "most chips, and even most of the layers on advanced chips, are printed on dry lithography machines."

Used for: A1_08, A1_09 (EUV layers are a minority and interleave with DUV layers).

## S6. ASML Annual Report 2025 (A)
https://www.sec.gov/Archives/edgar/data/937966/000162828026011377/asml-2025xannualxreportx.htm. Local: `refs/logistics/asml_ar/asml_2025_annual_report_6k.htm`
- EUV systems "are used for the most intricate, critical layers on the most advanced microchips."
- "DUV lithography systems are the workhorses of the industry, producing the majority of layers in microchips."
- Immersion systems "can be used in seamless combination with EUV systems to print different layers on the same chip."
- "Continued investment in e-beam inspection, e-beam metrology and YieldStar optical metrology."

Used for: A1_09 (EUV and DUV layers interleave), A1_10 (overlay is measured optically, so the SEM look is a style choice).

## S7. ASML Investor Day, 8 Nov 2018, EUV presentation (Form 6-K exhibit 99.4) (A, dated)
https://www.sec.gov/Archives/edgar/data/0000937966/000119312518323057/d650002dex994.htm (slide 8). Local: `refs/A1/asml_6k_2018_ex994.htm`
- Table "EUV estimated demand per fab by market. Range of layers and corresponding systems per fab": "Logic ... EUV layers 10 – 20 ... (7nm – 5nm)"; "DRAM ... 1—6 ... (16nm -1Anm)".
- Footnote: "“Typical” process and system conditions in the 2018-2022 timeframe, not specific customer condition".

This is the only primary EUV layer count found. It covers 7-5 nm logic and is a 2018 estimate, so it does not support 二十多层 for current chips (A1_09).

## S8. ASML Investor Day, 14 Nov 2024 (Form 6-K exhibit 99.2) (A)
https://www.sec.gov/Archives/edgar/data/937966/000093796624000026/exhibit992.htm (pages 27-32). Local: `refs/A1/asml_6k_2024_ex992.htm`
- "Logic and DRAM are expected to drive further critical lithography exposures. We expect EUV 0.33 NA layers to continue to increase node on node" (p. 27; the chart axis is "# of EUV 0.33 NA Exposures" with no absolute values).
- "Expected average High NA Layers ... 2029 - 2030 ... LOGIC 4-6 ... DRAM 2-3" (p. 32).

No absolute EUV layer count for current logic. The ASML Investor Day 2021 deck (6-K 0001193125-21-287742, ex. 99.3 slides 18-19, "Projection of lithography layers by technology") has a chart only, with no numbers in the text.

## S9. MicroChemicals GmbH, "Spin-coating of Photoresists" (resist manufacturer application note) (A for basic process)
https://www.microchemicals.com/technical_information/spin_coating_photoresist.pdf. Local: `refs/A1/mc_spin_coating_photoresist.pdf`
- p1: "typically a few ml of resist are placed (dispensed) on a substrate which is typically brought to a rotational speed of several 1000 rpm before (dynamic spin-coating Fig. 53) or shortly thereafter (static spin-coating)."
- p1: "Due to the centrifugal force, the dispensed resist spreads into a uniform resist film of desired film thickness, excess resist is spun off the edge of the substrate."
- p1: "The spin-coating of the resist typically takes only 10 - 20 seconds"
- p2: "to use a resist which achieves the desired film thickness with conventional spin profiles (2000 - 4000 rpm for 20 - 30 seconds)."

Used for: A1_03 (the process is right; the drawn speed of about 75 rpm is wrong; edge threads are not in the source).

## S10. MicroChemicals GmbH, "Exposure of Photoresists" (application note) (A for basic process)
https://www.microchemicals.com/technical_information/exposure_photoresist.pdf. Local: `refs/A1/mc_exposure_photoresist.pdf`
- p1: "The chemical processes occurring here in the resist film result in an increased (positive resists) or reduced (negative resists) solubility in the developer, whereby a structured resist mask can be produced."
- p1: "The spectral sensitivity of the AZ® and TI photoresists we sell is in the near-UV range, and with most resists, also in the visible short-wavelength (blue) spectral range." (This is why the lighting is yellow: no blue or UV.)
- p2 (mask aligner): "The dimensions of the structures on the photo mask correspond to 1 : 1 the dimensions of the exposed areas of the resist film, the image is thus congruent."
- p2 (stepper): "Using a stepper, exposure is also performed as a projection through a photo mask (Fig. 83 centre). By reduction optics, the dimensions of the exposed resist areas are, however, smaller than the structures of the photo mask"
- p6: "In the case of optically thin resist films (with a film thickness less than the penetration depth of the exposure wavelength), an almost homogeneous exposure occurs from the exposure start." and "Optically thick resist films ... absorbs only in the uppermost μm at the beginning of the exposure, which thereby bleach and guide the light increasingly deeper toward the substrate during further exposure."
- p9: "even with a perfect contact (G = 0), the lateral intensity distribution on the resist surface is inhomogeneous, since the finite gap width forms a diffraction pattern immediately behind the slit."

Used for: A1_03 (yellow light), A1_04 (chemistry change; 1:1 vs reduction), A1_05 (latent image; a top-down front only happens in thick bleaching resists), A1_06 (positive-tone develop), A1_12 (diffraction blur).

## S11. P. C. Andricacos (IBM), "Copper On-Chip Interconnections", The Electrochemical Society Interface, Spring 1999, pp. 32-37 (B; Fig. 3 reprinted from IBM J. Res. Dev. 42(5), 1998)
https://www.electrochem.org/dl/interface/spr/spr99/IF3-99-Pages32-37.pdf. Local: `refs/A1/ecs_andricacos_interface1999.pdf`, rendered page `refs/A1/ecs_andricacos_p2.png` (looked at)
- p33 Fig. 3, Damascene column (from the image): "insulator deposition and patterning, seed layer deposition" -> "plating" (the metal covers the whole surface, inside and outside the trench) -> "planarization". Dual-damascene row: "insulator deposition" (with "etchstop (silicon nitride)") -> "via definition" / "line definition" -> "barrier and seed layer deposition" -> "plating and CMP".
- p33: "In Damascene processing, the seed layer is deposited on top of the patterned substrate and therefore, electroplating occurs everywhere, inside and outside features, from the bottom upward and from the sides inward."
- p33: "In a Damascene process, excess material is deposited on top of the useful wiring structure (called “overburden”) and must be removed by a planarization process called chemical mechanical planarization (CMP)."
- p33 (the alternative, through-mask plating): "the seed layer is deposited again over the wafer surface prior to patterning. Electroplating occurs only in those lithographic areas that are not covered by the masking material."

Used for: A1_06 (the etch step is right; deposit-before-strip with a flush fill is wrong; the fix is strip -> blanket deposit -> CMP), A1_07 (each metal level is patterned lines, not a sheet).

## S12. US 2016/0025650 A1, "Overlay metrology method and overlay control method and system" (B, patent)
https://patents.google.com/patent/US20160025650A1/en (page fetch)
- "The inner box 11 is formed on a current layer of the wafer 100"
- "the outer box 12 is formed on a previous layer under the current layer of the wafer 100"
- "An overlay error is determined by measuring a distance between the center of the inner box 11 and the center of the outer box 12"

Used for: A1_10 (box-in-box marks; inner box = new layer, outer box = layer below, as drawn in mograph/a1.py).

## S13. SEMI 3D10, product page (scope) (A, standards body)
https://store-us.semi.org/products/3d01000-semi-3d10-guide-to-describing-materials-properties-for-intermediate-wafers-for-use-in-a-300-mm-3ds-ic-wafer-stack-1 (page fetch)
- "This Guide describes wafers and wafer stacks with nominal diameter of 300 mm and nominal thickness of 775 µm, ..."

Used for: A1_02 (shows how far the drawn proportions are from a real wafer).

## S14. Media only (C), kept for the record and not usable on screen or in VO
- TrendForce, 2024-07-22 (relaying TheElec): Samsung 3 nm has 20 EUV layers; 2 nm "late-20s". https://www.trendforce.com/news/2024/07/22/news-samsungs-2nm-node-will-reportedly-feature-30-more-euv-layers/ (this is F55).
- Secondary reports put TSMC N3B at about 25 EUV layers and N3E at about 19 (WikiChip/AnandTech). No TSMC primary found.

## Internal file checked
- `blender/textures/make_circuit.py` header: "Generate circuit.png: a stylised standard-cell layout mask (white = pattern), tileable rows. Illustrative only, not a real design." This is why A1_11's "→ 真正的电路版图" is wrong and A1_04's mask pattern is simplified.

## Not public / not found
- A primary (ASML, TSMC, Samsung, Intel or imec) count of EUV layers for a current 3 nm or 2 nm logic chip. Searched ASML annual reports 2021, 2024 and 2025, Investor Day decks 2018, 2021 and 2024, the Q2 2021 earnings call transcript, and the asml.com stories.
- A source for resist "threads" flung from the wafer edge during spin coating.
