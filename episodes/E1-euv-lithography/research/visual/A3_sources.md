# A3 sources: three hard problems, 17 years / EUR 6 bn

Checked 2026-10-21. Used by `audit_A3.yaml` (S-numbers). Pages saved (not committed) under
`renders/review/refs/A3/web/` and `renders/review/refs/A3/pdf/`. Confidence: A = ASML / ZEISS / TRUMPF / Intel first-party;
B = peer-reviewed, lab database or conference paper; C = media (not used).

## S1 ASML, "Light and lasers" (A)
https://www.asml.com/en/technology/lithography-principles/light-and-lasers (saved `web/asml_light.html`)
- "EUV lithography, a technology entirely unique to ASML, uses light with a wavelength of 13.5 nanometers. This wavelength is more than 14 times shorter than DUV light."
- "EUV light occurs naturally in outer space. But to make EUV lithography possible, we needed to engineer a way to create such light within a system. So, we developed a radically new approach to generating light for lithography."
- Consequence for A3_02: the card ("没有现成的 13.5 nm 强光源") is fine; the narration "自然界里没有现成的" contradicts ASML. Use "地球上没有现成的" or drop "自然界里".

## S2 ZEISS SMT, "EUV lithography" (A)
https://www.zeiss.com/semiconductor-manufacturing-technology/inspiring-technology/euv-lithography.html (saved `web/zeiss_euv.html`)
- "The light visible to humans has wavelengths between 400 and 800 nanometers. The range of ultraviolet light begins below 400 nanometers."
- "Since extreme ultraviolet light is absorbed by all materials – including air, ZEISS SMT created an optical system for the EUV lithography machine. This operates in the vacuum chamber and is made up of curved mirrors."
- "EUV light is absorbed by materials (even air), therefore the EUV system has a large vacuum chamber in which the light is directed by reflecting mirrors."
- "Extremely thin layers of silicon and molybdenum – only a few atomic layers thick – are vapor-deposited onto the glass surface. For this, up to 100 layers lie on top of each other here. A single layer would only reflect a good one percent of the light"
- "The result is a reflectivity that makes up to 70 percent of the light usable."
- "Most recently, in 2019, together with strategic partner ASML, TRUMPF, the Fraunhofer Institute IOF and around 1,200 other partners, a further technological leap was achieved. This perpetuates Moore's Law: EUV lithography."

## S3 ASML, "EUV lithography systems" (A)
https://www.asml.com/en/products/euv-lithography-systems (saved `web/asml_euv.html`)
- "EUV light is absorbed by everything, even air. So the whole light path and everything the light interacts with – from source to wafer – must be in high vacuum."
- "EUV systems use several multilayer mirrors instead of lenses to guide the EUV light to the wafer, shrinking the reticle pattern by a factor of four."
- "EUV technology took more than two decades to develop ... ASML invested more than €6 billion in EUV R&D over 17 years. We acquired Cymer – a company specialized in light source technology – to accelerate EUV source development."
- "The first EUV production system – the TWINSCAN NXE:3300 – was shipped in 2013" ... "At the beginning of 2020, we celebrated the 100th EUV system shipment."
- The page gives no start or end year for the "17 years" and no mirror reflectivity number.

## S4 CXRO gas transmission, air at 13.5 nm (B, LBNL database)
https://henke.lbl.gov/cgi-bin/gastrn.pl (form https://henke.lbl.gov/optical_constants/gastrn2.html), POST: Formula `N1.562O.42C.0003Ar.0094` (CXRO "Air"), 760 Torr, 295 K, wavelength 13.4-13.6 nm. Output saved `web/gas_Air_*.dat`.

| path | transmission at 13.5 nm |
|---|---|
| 0.01 cm (0.1 mm) | 0.49912 |
| 0.1 cm (1 mm) | 9.5944E-04 |

Attenuation length (1/e) = 0.1 mm / ln(1/0.499) = ~0.14 mm (derived). For comparison, H2 at 5 Pa (0.0375 Torr, F28), 100 cm: 0.99386.

## S5 CXRO attenuation length, glass (B)
https://henke.lbl.gov/cgi-bin/atten.pl (form https://henke.lbl.gov/optical_constants/atten2.html), normal incidence. Saved `web/atten_*.dat`.
- SiO2, density 2.2: 13.5 nm -> 9.971761E-02 um (~100 nm).
- (Mo 10.22 g/cm3: 0.167 um; Si 2.33: 0.588 um.)

## S6 CXRO multilayer reflectivity, Mo/Si (B)
https://henke.lbl.gov/cgi-bin/multi.pl (form https://henke.lbl.gov/optical_constants/multi2.html). Si/Mo, Gamma 0.4, 40 bilayers, sigma 0 (ideal interfaces), SiO2 substrate, unpolarised. Saved `web/multi_*.dat`.

| period d | grazing angle (AOI) | R at 13.5 nm |
|---|---|---|
| 6.9 nm | 90 deg (normal) | 0.729 (peak 0.729 at 13.50 nm) |
| 6.9 nm | 65 deg (25 deg AOI) | 0.011 |
| 7.5 nm | 65 deg | 0.253 |
| 7.6 nm | 65 deg | 0.565 (peak ~0.65 at 13.35 nm) |

The ~7 nm period is ~60x below visible wavelengths, so the stack gives no visible thin-film colour.

## S7 TRUMPF, "EUV drive laser" (A)
https://www.trumpf.com/en_US/solutions/applications/euv-lithography/euv-drive-laser/ (curl blocked with 403; read through WebFetch)
- "ASML, Zeiss, and TRUMPF joined forces to develop a technology to produce extreme ultraviolet (EUV) light."
- "The High Power Seed Module (HPSM) consists of two seed lasers"; "An initial amplifier is used to pre-amplify the light to a magnitude of 100 W"; the High Power Amplification Chain "consists of four resonators to increase the power".
- Beam transport system "transports the laser beam up to 30 meters in the direction of the droplet chamber".
- Laser in the sub-fab, enclosed beam transport: see `euv_source.md` (Fomenkov 2017 p.176 and Fig. 2; Purvis 2020 slide 16).

## S8 ZEISS, Winfried Kaiser, "Starlith 3400: Projection Optics", VLSI-TSA Taiwan, 2019-02-20 (A)
https://www.euvlitho.com/2019/P24.pdf (saved `pdf/zeiss2019_P24.pdf`; slides rendered `pdf/kaiser2019_s18.png`, `_s19`, `_s23`)
- Slide 18 "Mirror manufacturing": photo of a finished EUV mirror in a ZEISS clean room. It is a plain silvery mirror (the worker's face reflected), with no rainbow colours.
- Slide 19 "Figure control on atomic level": "Figuring process ... multiple iterative loops ... Computer Controlled Polishing | Ion Beam Figuring | Interferometric Surface Metrology ... Polishing technologies and metrology closing the loop".
- Slide 23 "Coating technology: The multilayer coating defines EUV.": drawing of Mo/Si Bragg layers on a "Substrate"; "> 50 Bi Layers"; "Reflectivity >67%, high bandwidth"; reflectivity curve peaks ~0.75 near 13.5 nm.
- Use: the substrate is polished and ion-beam figured first, then coated. A blank shown being polished must be bare substrate (A3_05 vignette 2). A finished mirror looks like a plain mirror (A3_04, iridescence = artistic).
- The 2022 ZEISS deck (euvlitho.com/2022/P53.pdf, F9) would not download fully (connection reset at ~1.2 MB). It was not needed.

## Reference only: milestones NOT shown in A3 (for a possible dated time bar)
- S9 EUV LLC: Intel press release "Government-Industry Partnership To Develop Advanced Lithography Technology", SAN JOSE, Sept. 11, 1997: "A private industry consortium, led by Intel Corporation, Advanced Micro Devices and Motorola" ... "The group, known as the EUV LLC (Extreme Ultraviolet Limited Liability Company), will invest $250 million" with the Virtual National Laboratory of "Lawrence Livermore National Laboratory ... Sandia National Laboratories and E.O. Lawrence Berkeley National Laboratory". https://www.intel.com/pressroom/archive/releases/1997/CN091197.HTM (A). A search snippet says Congressional Research Service report 98-81 dates the CRADA signing to March 1997. I did not open that report. If a date goes on screen, show "1997" without a month.
- S10 First production system shipped 2013 (NXE:3300), 100th system early 2020: S3. EUV in volume production in 2019: S2 ("in 2019 ... EUV lithography").
- S11 High-NA: first EXE:5000 modules shipped December 2023, arrived Oregon January 2024: F20 / shipment_suppliers.md A1.
- Light-source power history: not shown in A3. Do not add it without its own sourcing pass (see euv_source.md).
- Do not map the "17 years" onto calendar years: ASML does not say which 17.

## Not public
- The exact path length and molecule spacing for an "air absorbs EUV" picture. The physics (S4) is public; any drawing is 示意.
- The visible appearance of absorbed EUV heating glass. Nothing documents a visible glow.
- The machine's overall dimensions (as in A0_05).
