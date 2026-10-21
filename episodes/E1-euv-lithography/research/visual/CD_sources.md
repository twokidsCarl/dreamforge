# C/D sources: the long-take recap (C_01–C_10) and the ending (D_01–D_10)

Checked 2026-10-21. Used by `audit_C.yaml` and `audit_D.yaml` (S-numbers). Builds on `high_na_optics.md` (cited
as HNA §n, with its own tags [A21], [A22], [Z21], [Z24], [Z15], [D20]), `euv_source.md` (ES §n), `B1_sources.md`
(B1-Sn), `chips.md` and `shipment_suppliers.md`. Local copies (not committed): `renders/review/refs/CD/sheets/`
(4x3 contact sheets of every C/D preview). The ASML annual report text was fetched from SEC EDGAR with a placeholder
contact (research@example.com) in the User-Agent; no personal data was sent anywhere.
Confidence: A = ASML / ZEISS / TRUMPF / Intel first-party; B = peer-reviewed paper, patent, SPIE paper, research
institute; C = media (not usable on screen).

## S1 ASML Annual Report 2025 (A)
https://www.sec.gov/Archives/edgar/data/937966/000162828026011377/asml-2025xannualxreportx.htm
(page numbers are the "ASML Annual Report 2025 nn" running heads in the SEC text)
- Power, NXE only: "For the TWINSCAN NXE:3800E, the total power consumption decreased 0.06 MW to 1.26 MW compared to
  2024. Compared to the 2018 baseline figure of 1.44 MW, this is a reduction of 13%." (sustainability, product use)
- Energy per wafer pass: "In all, energy per wafer pass decreased from 5.9 to 5.5 kWh, a reduction of 57% against our
  target reduction of 60% versus our 2018 baseline of 12.8 kWh/wafer." and (CEO letter) "Today, the energy
  consumption per wafer pass has fallen by 57% since the shipment of the first system for high-volume manufacturing in
  2018". 5.5 / 12.8 = 0.43, so the D_04 bar at 43% is right.
- What the NXE figure covers: "For EUV NXE, we include source, scanner, laser, PVAC and abatement, and relevant
  cabinets ... Energy efficiency is reflected in kWh per wafer pass."
- EXE is different and must not be mixed in: "In 2025, we performed our first SEMI S23 measurement for the TWINSCAN
  EXE:5000A, which resulted in energy use per wafer pass of 25.2 kWh/wafer. This relatively high figure is explained by
  the low throughput of 53 wafers per hour at the test".
- Source power, p.30: "1,000-watt EUV light source power shows path to higher productivity. In April 2025, ASML reached
  a historic milestone: demonstrating the first ever 1,000-watt light source for EUV lithography." (B1-S3 cites the
  strategic-report PDF as p.31; same text.) Nothing about a path beyond 1,000 W, and no "600 W" anywhere in the report.
- Suppliers, p.4 and p.41: "5,100 Total number of suppliers"; regional split on p.239 (shipment_suppliers.md B1:
  1,600 Netherlands / 700 rest of EMEA / 1,350 North America / 1,450 Asia).

## S2 ASML Annual Report 2025, story "cutting-edge physics" (A) = B1-S3
- "this process is repeated thousands of times per second – 60,000 times per second in our latest commercial
  sources." The older ASML web figure is 50,000 (S11). Neither is stated for the EXE source specifically.

## S3 ASML SPIE papers on source power (B, ASML authors) = B1-S4
- Hummler et al., Proc. SPIE 12953, 129530V (2024): NXE:3800E throughput "made possible by an increase in EUV source
  power (to >500W)".
- Umstadter et al., Proc. SPIE 12494, 124940Z (2023): "Sources at customers operate at ~250 Watt power"; "600W
  milestone" only on "ASMLs research systems".

## S4 ZEISS, Kaumanns et al., "Status and outlook of EUV optics at ZEISS", EUVL Workshop 2024 (A) [Z24]
https://euvlitho.com/2024/P22.pdf
- slide 9: "Anamorphic lens design: 4× reduction in non-scan direction, 8× reduction in scan direction"; "4x/8x
  demagnification ... 5.4° ... OK: works"; "Central obscuration – Reduces angular load and angle variation".
- slide 13 "Current 0.55 NA": plasma → collector → intermediate focus → small fold mirror → field facet mirror → pupil
  facet mirror → reticle → projection optics → wafer (HNA §1.4; WORKFLOW 2.5). No total mirror count in text.

## S5 ZEISS/ASML, Wischmeier et al., "High NA EUV optics", EUVL Workshop 2021 (A) [Z21]
https://euvlitho.com/2021/P52.pdf
- slide 11: "βscan = 1/8, βx-scan = 1/4"; exposure slit at the wafer a 26 × 1.6 mm² arc; at the reticle "104x12.8
  mm²", drawn curved.
- slide 13: "High-NA illuminator will utilize 0.33NA technology with actuated facet mirrors ... High-NA illuminator
  provides 20% pupil fill ratio". The facet count is not given (HNA not-public item 10).

## S6 ASML, van Schoot, "High-NA EUV Progress and Outlook", EUVL Workshop 2021 (A) [A21]
https://www.euvlitho.com/2021/P3.pdf (PNG `renders/review/refs/highna/euvlitho2021/vs21_p34.png`, viewed)
- slide 34 "The ASML High-NA Reticle Design": "Changed vs 0.33NA • 4x/8y magnification • Exposure Chief Ray Angle
  (~5.3°)"; "Unchanged vs 0.33NA ... Pellicle, pellicle infra- structure, pellicle relevant mask layout ... EUV pod".
  The render labels "Pellicle + mounting" on the pattern side (face down). The reticle carries a double-headed arrow
  "Scan direction" and the wafer a second double-headed arrow. **Both arrows are double-headed, so the slide does not
  say whether reticle and wafer move in the same or opposite directions** (HNA §1.5 reads "antiparallel"; that is not
  on the slide). The reticle is drawn as a dark grey plate, not iridescent.
- slide 35: projection optics "Design examples", six mirrors, obscuration, "Big last mirror driven by High-NA".

## S7 ASML, van Schoot, "High NA EUV: Getting closer to introduction", EUVL Workshop 2022 (A) [A22]
https://euvlitho.com/2022/P3.pdf
- slide 12: "0.55NA prints a Half Field" 26 mm × 16.5 mm (0.33 NA: full field 26 × 33 mm).
- slide 34: module tiers; source a separate unit beside the scanner (A0_05).
- slide 32: "Mask Stage: 4x increase in acceleration", "Wafer Stage: 2x increase in acceleration".

## S8 Obscuration: Davydova et al. (ASML), SPIE 11517 (2020) (B); Heil et al. (ZEISS), EUVL Symposium 2015 (A)
- Davydova §5: "The high-NA scanner has central obscuration of approximately 20% of the pupil plane."
- Heil slide 9: "Obscuration – We drill a hole into the mirror", M6 (large, upper) and M5 (small, above the wafer);
  slide 20: "Obscuration enables significantly higher optics transmission vs. 3300".
- Consequence for the drawn ray: the centre of the pupil is the obscured part, so a ray drawn reflecting at the centre
  of M5 reflects off the hole.

## S9 Nikon, US 5,831,716 "Slit-scanning type light exposure apparatus" (1998) (B) — the source behind F57
https://patents.google.com/patent/US5831716A/en
- "As the reticle R and the wafer W are scanned in the opposite directions at the same constant speeds" with
  "β ... the projection magnification of the projection optical system PL and is 1/4, for example".
- The apparatus uses a KrF excimer laser (248 nm) and a refractive lens: **DUV, not EUV**. F57's other source (Design
  News) is media (C). No primary EUV/EXE source found for the relative scan direction. Patents for reflective/EUV stages
  checked (US 6,353,271 EUV LLC; US 7,193,683 Nikon) do not state it either. A search-engine snippet of ASML's
  "Mechanics and mechatronics" page reads "accelerate at 5 g and 15 g in opposite directions" but the page itself was
  blocked (403 / Vercel checkpoint), the figures are DUV-class (EXE: wafer 8 g, reticle 32 g, HNA §3.1), so it was
  not used. Physics note (ours, not a source): the image orientation, and so the relative direction, depends on the
  number of intermediate images and reflections in the specific design, which ASML/ZEISS do not state in text.

## S10 ZEISS EUV page (A) = F19, chips.md A
- "Today there are 184 billion (semiconductor) components on an area only slightly larger than a fingertip." ZEISS
  does not name a chip (chips.md A3). The Zen 5 CCD on screen (TSMC 4 nm, chips.md B) is not that chip.

## S11 ASML, "Light and lasers" (A) = B1-S1
https://www.asml.com/en/technology/lithography-principles/light-and-lasers
- "molten tin droplets of around 25 microns in diameter"; "this process is repeated 50,000 times every second"; "hit
  first by a low-intensity laser pulse that flattens them ... Then a more powerful laser pulse vaporizes".

## S12 ASML San Diego page (A) = B1-S2 / F22
- each droplet "is individually imaged and targeted by two high-powered CO2 laser pulses".

## S13 University of Illinois textbook chapter 18 (B) = F7, F33
https://cpmi.illinois.edu/files/2023/10/Ch18-1.pdf
- about 10 reflections from source to wafer; of ~100 W entering the scanner about 1 W reaches the wafer. A generic,
  0.33-NA-era estimate; ZEISS says the High-NA obscured design has "significantly higher optics transmission vs. 3300"
  (S8), so it is not an EXE figure.

## S14 EUV bundle is hollow: Purvis (ASML) 2020 slide 11 (A) = ES §6; Fomenkov et al. 2017 p.176 (B)
- PUR20 slide 11 inset "EUV far-field intensity distribution": an annulus with a dark centre.
- FOM17 p.176: the drive laser "propagates through a central aperture in the collector". So the collector centre is
  where no EUV comes from; a single line starting at the collector centre is a simplification.

## S15 Asyst Technologies / Murata, US 7,410,340 "Direct tool loading" (B)
https://patents.google.com/patent/US7410340B2/en
- "The OHT system lowers a FOUP onto the kinematic plate of the load port at approximately 900 mm height"; the load
  port kinematic plate has "an active container hold down mechanism (in compliance with SEMI Standard E15.1)"; the OHT
  is a cable-hoist vehicle ("cable hoist vehicles", "cable hoist extensions").

## S16 Miraial (FOUP manufacturer) product pages (B)
https://www.miraial.co.jp/en/product/kt-3003/ , https://www.miraial.co.jp/en/product/300mm-fosb/
- 300 mm FOUP: "Holds 26 wafers (The 26th wafer is a dummy that is used to protect the 25th wafer)", material PC,
  "Redundant lid gaskets". Outer dimensions are not given for the FOUP; the 300 mm FOSB shipping box is 389.5 mm wide,
  327 mm long, 341.8 mm high (reference size only; SEMI E47.1 sets FOUP envelopes but is paywalled).

## S17 DLR, clean room PR-13 (B, research institute)
https://www.dlr.de/en/images/large-scale-research-facilities/clean-room-pr-13/
- "Yellow lighting prevents accidental exposure of UV-sensitive photoresist layer" (lithography lab).

## S18 Intel on the EXE:5000 (A) = HNA §3.2
- "It is as big as a double-decker bus and weighs as much as a blue whale."; "more than 150 metric tons". Overall
  dimensions are not public.

## Not public (keep generic, label 示意)
1. Relative scan direction of reticle and wafer in NXE/EXE (S9).
2. Number of facets on the EXE field and pupil facet mirrors (S5); when and how often facets are switched in
   production (only "actuated facet mirrors" for setting the pupil).
3. EXE source repetition rate and power (S2 gives "latest commercial sources" without naming the platform).
4. EXE whole-machine power (S1 gives only one EXE:5000A test at 53 wph).
5. FOUP outer dimensions per SEMI E47.1 and the load-port undock stroke (S15/S16 give only the 900 mm plate height and
   26-slot capacity).
6. Country/city positions of the 5,100 suppliers (only four regions, S1 p.239).
