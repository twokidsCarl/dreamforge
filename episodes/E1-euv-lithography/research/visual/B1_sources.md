# B1 sources: the EUV light source (droplets, double pulse, plasma, collector, drive laser, atomic physics)

Checked 2026-10-21. Used by `audit_B1.yaml` (S-numbers). This builds on `research/visual/euv_source.md`, which is
cited as ES §n and is not repeated here. Local copies (not committed): `renders/review/refs/B1/` (web/, pdf/, sheets/
= 3x3 contact sheets of every B1 preview) and `renders/review/refs/source/`.
Confidence: A = ASML / ZEISS / TRUMPF first-party; B = peer-reviewed paper, patent, or SPIE paper by ASML authors;
C = media (not usable on screen).

## S1 ASML, "Light and lasers" (A)
https://www.asml.com/en/technology/lithography-principles/light-and-lasers
- "molten tin droplets of around 25 microns in diameter are ejected from a generator at 70 meters per second"
- "this process is repeated 50,000 times every second"
- "the droplets are hit first by a low-intensity laser pulse that flattens them into a pancake shape"
- "Then a more powerful laser pulse vaporizes the flattened droplet to create a plasma that emits EUV light"

## S2 ASML, San Diego location page (A)
https://asml.com/company/about-asml/locations/san-diego
- droplets "which fly at more than 241 km per hour in a vacuum vessel" (241 km/h = 67 m/s, consistent with S1)
- "whose size is a fraction of the thickness of a human hair"
- each droplet "is individually imaged and targeted by two high-powered CO2 laser pulses" (F22)

## S3 ASML Annual Report 2025 (A)
Strategic report PDF, p.31: https://ourbrand.asml.com/m/8ab959d4926657b/original/asml-2025-annual-report-strategic-report-section.pdf
(saved `pdf/asml_ar2025_strategic.pdf`). Full story: https://investor.asml.com/annual-reports/2025/strategy-and-stories
(403 to curl; read through a text proxy, saved `web/asml_ar2025_stories.md`).
- "In April 2025, ASML reached a historic milestone: demonstrating the first ever 1,000-watt light source for EUV lithography." (PDF p.31)
- "this process is repeated thousands of times per second – 60,000 times per second in our latest commercial sources." (story)
- "transforming the droplets into exploding balls of plasma 40 times hotter than the surface of the sun" (story)
- "found that flattening the tin droplet before triggering the explosion increased the EUV light output" (story)
- Consequences: (a) the 1000 W demo is grade A, but the words 原理样机 / 实验室 come only from media (Bits&Chips
  "proof of concept"); (b) "每秒最多 5 万颗" is contradicted by ASML's own newest figure (60,000/s); (c) "40 times
  hotter than the surface of the sun" (about 23万 K) agrees with ZEISS, not with the 50万 K that F5 takes from
  ASML's "hot machines" page. The producer has already chosen 50万 K; this second ASML figure is new and should be
  recorded in F5.

## S4 ASML SPIE papers on source power (B, ASML authors)
- Hummler, Zhu, ... Purvis, ... Brown, "High-power EUV light sources (>500W) for high throughput in next-generation
  EUV lithography tools", Proc. SPIE 12953, 129530V (2024), doi:10.1117/12.3010463. Abstract (via Semantic Scholar
  API): "The NXE:3800E system marks a substantial step forward in scanner productivity, delivering a remarkable
  increase of (+60 WPH) in throughput, made possible by an increase in EUV source power (to >500W)."
- Umstadter, Graham, Purvis, Schafgans, Stewart, Mayer, Brown, "EUV light source for high-NA and low-NA lithography",
  Proc. SPIE 12494, 124940Z (2023), doi:10.1117/12.2657772: "Sources at customers operate at ~250 Watt power" ...
  "reaching a new 600W milestone for EUV Sources" (on "ASMLs research systems").
- No first-party text found for "600 W in production". That figure (high-NA production sources) appears only in
  media (Bits&Chips, Feb 2026). It stays grade C and must not appear on screen.

## S5 TRUMPF, EUV drive laser product page (A)
https://www.trumpf.com/en_US/products/lasers/euv-drive-laser
- High Power Seed Module "consists of two seed lasers – which generate output pulses of just a few watts"
- "An initial amplifier is used to pre-amplify the light to a magnitude of 100 W."
- "The High Power Amplification Chain (HPAC) consists of four resonators to increase the power."
- "This method enables the 40 kilowatts of laser power to be used efficiently."
- "The TRUMPF Laser Amplifier sequentially amplifies a laser pulse by more than 10,000 times."
- "Short pulses ensure an extremely high peak output power in the MW range."
- beam transport system "transports the laser beam up to 30 meters in the direction of the droplet chamber" (using mirrors and periscopes)
- "three different cooling circuits make sure that the system has the required level of stability."
- "The pre pulse initially hits the tin droplet with a low pulse power" (the page says this turns the droplet into a disk with a larger surface area); "The following main pulse is absorbed by the resulting liquid film"
- The page says nothing about where the laser is installed. For that, see ES §6: FOM17 p.176 puts it in the sub-fab, with the beam going up through the waffle-slab floor.

## S6 TRUMPF press release "ASML honors TRUMPF for new EUV laser" (A)
https://www.trumpf.com/en_INT/newsroom/global-press-releases/press-release-detail-page/release/asml-honors-trumpf-for-new-euv-laser-9838/
- "With more than 450,000 individual parts and a weight of over 20 tons" ... "series production is scheduled to begin in 2026."

## S7 ASML, Simon Mathijssen story (A)
https://www.asml.com/en/company/stories/2021/fellow-simon-mathijssen-aligning-lithography-nanometer
- "the wafer is initially positioned with a precision of around 80 micrometers", which is "about the diameter of an
  average human hair". This supports the B1_06 hair comparison (80 µm).

## S8 ASML patent US9715174B2, droplet generator (B)
https://patents.google.com/patent/US9715174
- Assignee ASML Netherlands BV. The nozzle is "shaped like a nozzle 66 with an inner diameter of 3-5 μm" (an alternative goes up to about 10 µm); droplets "diameter ~30 um"
- The jet is broken up at "a high frequency close to the Rayleigh frequency" ("in the region of MHz"), then "a lower frequency in the kHz range" varies the droplet speed, so that "high speed droplets overtake low speed droplets and coalesce into larger droplets spaced at a large distance"; the spacing is desirably greater than about 1 mm; velocities "between 40 to 100 m/s"

## S9 ASML patent US11240904B2, "controlling coalescence of droplets in a droplet stream" (B)
https://patents.google.com/patent/US11240904B2/en
- The orifice is about 0.5-30 µm, at the end of a capillary tube with an inside diameter of about 0.5-0.8 mm; droplet velocities about 30-150 m/s; a hybrid waveform makes the small droplets fully coalesce, in stages, before they reach the irradiation region.

## S10 Fomenkov et al. (Cymer/ASML), Adv. Opt. Techn. 2017 (A) — `refs/source/fomenkov2017.pdf`
- p.180: "Approximately 100 small droplets at an average frequency of 5 MHz were used in this example to produce 50 kHz droplets with a 1.5-mm droplet-to-droplet spacing"
- Fig. 10 (p.179, rendered `refs/B1/fom17_p7.png`): top, a continuous jet that breaks into a dense row of tiny dots in clusters; bottom, two fully formed droplets far apart. Each droplet is a small dot, roughly 1/40 of the spacing.
- p.176: the beam is "focused to a minimum spot size" and "propagates through a central aperture in the collector" (ES §2).
- Fig. 16 / SW17 slide 35 (collector photos): a deep, mirror-bright bowl that reflects the cleanroom with a warm metallic cast. It shows no rainbow or concentric banding.

## S11 Torretti et al., Nature Communications 11, 2334 (2020) (B)
https://pmc.ncbi.nlm.nih.gov/articles/PMC7214432 (doi:10.1038/s41467-020-15678-y)
- For Sn12+ the full CI calculation "generates over 3 × 10^5 fine-structure levels and more than 10^10 dipole-allowed transitions"
- "not from the singly-excited states decaying to the ground state as is the current paradigm"; "Contrary to the prevailing view, contributions from one-electron-excited states are minor"; "the contributions from multiply-excited states dominate"; "the well-known transitions to the ground levels comprise only 11% of the total opacity"
- Consequence for B1_20: the old picture is "单激发态（向基态跃迁）". It is not "单电子跃迁": every one of these E1 lines is a one-electron jump, including those from multiply-excited states.

## S12 Torretti et al., J. Phys. B 51, 045005 (2018), arXiv:1709.02626 (B)
https://ar5iv.labs.arxiv.org/html/1709.02626
- In-band photons come from 4p-4d and 4d-4f transitions in "Sn8+–Sn14+", "clustered in so-called unresolved transition arrays (UTAs)"; the feature rises "to a peak at exactly 13.5 nm". Table 1 gives line counts from a few up to 28,983 per array, i.e. thousands of lines in total.

## S13 Tin sheet thickness, ARCNL (B)
- Bo Liu, PhD thesis, VU Amsterdam 2022, "Morphology of liquid tin sheets formed by laser impact on droplets"
  (https://research.vu.nl/en/publications/morphology-of-liquid-tin-sheets-formed-by-laser-impact-on-droplet/):
  "The results reveal a thickness of just several tens of nanometers for the sheet."; "we directly visualize the
  presence of the bounding rim and the center mass"; "more than half of the liquid is lost from the sheet to other
  channels a few microseconds after the laser pulse".
- Liu, Kurilovich, Gelderblom, Versolato, Phys. Rev. Applied 13, 024035 (2020), doi:10.1103/PhysRevApplied.13.024035:
  "less than half of the initial amount of tin remains in the sheet"; the lost mass "ends up as fine fragments".
- Derived check (C): a 25 µm droplet (8.2×10^3 µm³) spread over a 300 µm disk has a mean thickness of about 0.12 µm.
  The B1 pancake mesh is 6 µm thick at the centre and 21 µm at the rim, about 50-100x too thick.

## S14 Kurilovich et al., Phys. Rev. Applied 6, 014018 (2016), arXiv:1604.00214 (B) — `refs/source/kurilovich2016_arxiv.pdf`
- p.3: "the droplet is accelerated to a speed U ∼0.5 −350 m/s"; the ablated mass's distribution "peaks in the direction back towards the laser". So the droplet and sheet are pushed along the laser direction (away from the collector, toward the IF) while they keep their original speed along the droplet path.
- Consequence: the backlog item ("the disk drifts along the laser axis; really it keeps flying along the droplet path") is half right. The correct motion is both: the sheet keeps its downstream velocity of about 70-80 m/s (so roughly 160-300 µm before the main pulse, PUR20 slide 23) and also gets a smaller push along +laser.

## S15 NIST Atomic Spectra Database, ground configurations (B, standard reference)
https://physics.nist.gov/PhysRefData/ASD/ionEnergy.html
- Sn I: [Kr]4d10 5s2 5p2 (shells 2-8-18-18-4); Sn IV/V (Sn4+): [Kr]4d10; Sn XV (Sn14+): [Ar]3d10 4s2 4p6. So stripping 5p², 5s², then ten 4d electrons gives Sn14+, matching the b1_atom strip order.

## Not public (keep 示意)
Nozzle exterior shape and its distance to the plasma (the installed value; the derived lower bound is about 0.3 m, because the generator sits on the vessel flank outside a 650 mm collector, SW17 slide 28 / POS16); coalescence length; production PP/MP delay and pulse energies; plasma size and visible colour; collector hole size; EXE source geometry; the real floor plan of the TRUMPF amplifier chain (FOM17 Fig. 2 shows four large enclosures in a T/L plan, not a straight row).
