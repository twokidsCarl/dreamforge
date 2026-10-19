# EUV LPP source (NXE): visual and engineering reference

Checked 2026-10-19. Every bullet has an exact quote, URL, page or slide, and confidence.
Confidence: **A** = ASML/Cymer/TRUMPF first-party text or drawing; **B** = peer-reviewed or ARCNL with ASML co-authors, or an ASML/Cymer patent; **C** = our own inference or arithmetic from A/B inputs (labelled "derived").
Local copies: `renders/review/refs/source/` (written below as `refs/`).

Sources used (all public):
- [FOM17] Fomenkov et al. (Cymer/ASML), "Light sources for high-volume manufacturing EUV lithography", Adv. Opt. Techn. 6(3-4):173-186 (2017). https://www.degruyterbrill.com/document/doi/10.1515/aot-2017-0029/pdf (also https://escholarship.org/content/qt2nw3x8dm/qt2nw3x8dm.pdf). `refs/fomenkov2017.pdf`
- [SW17] Fomenkov (ASML Fellow), "EUV Source for High Volume Manufacturing: Performance at 250 W...", 2017 Source Workshop, Dublin. https://www.euvlitho.com/2017/S1.pdf. `refs/euvlitho2017_S1.pdf`
- [POS16] Fomenkov, Schafgans, ... (Cymer/ASML), poster "LPP EUV Light Source for HVM: Status and Outlook", 2016 EUVL Symposium, Hiroshima. https://euvlsymposium.lbl.gov/pdf/2016/Poster/P-ET-04.pdf. `refs/euvls2016_P-ET-04.pdf`
- [WS18] A. Yen (ASML), 2018 EUVL Workshop. https://www.euvlitho.com/2018/P3.pdf. `refs/euvlitho2018_P3.pdf`
- [PUR20] M. Purvis (ASML), "An Introduction to EUV Sources for Lithography", STROBE, 25 Sep 2020. https://strobe.colorado.edu/wp-content/uploads/STROBE_ASML-EUV-Sources_Purvis_25-Sept-2020-1.pdf. `refs/purvis_strobe2020.pdf`
- [ASML-LL] https://www.asml.com/en/technology/lithography-principles/light-and-lasers
- [TRUMPF] https://www.trumpf.com/en_US/solutions/applications/euv-lithography/euv-drive-laser/
- [TOR20] Torretti et al. (ARCNL), "Spectral characterization of an industrial EUV light source for nanolithography", J. Phys. D 53, 055204 (2020). https://doi.org/10.1088/1361-6463/ab56d4 (read online; the PDF download was blocked)
- [KUR16] Kurilovich et al. (ARCNL plus ASML co-author), Phys. Rev. Applied 6, 014018 (2016). https://arxiv.org/pdf/1604.00214. `refs/kurilovich2016_arxiv.pdf`
- [SCH21] Schupp et al. (ARCNL), arXiv:2103.14758 (2021). https://arxiv.org/pdf/2103.14758. `refs/schupp2021_arxiv.pdf`
- [PAT245] US7872245B2 (Cymer, now ASML), "Systems and methods for target material delivery in a laser produced plasma EUV light source". https://patents.google.com/patent/US7872245B2/en

---

## 1. Droplets

**Diameter** (published values range 20-30 µm. The 2018-2020 ASML figure is 27 µm)
- "molten tin droplets of around 25 microns in diameter" (ASML-LL, web page). **A**
- "Droplet diameter | 27 µm" (Gen III droplet generator table) (WS18, slide 14; POS16, panel 6). **A**
- "Droplet stream of 27µm droplets" and "Droplet Diameter 27µm" (PUR20, slide 23). **A**
- "liquid tin droplets of, for example, ~30-μm diameter" (FOM17, p.176). **A**
- "Droplet (<30um)" (SW17, slide 29). **A**
- Table 1 "Droplet diameter 20–30 μm" (FOM17, p.179). **A**

**Speed** (published values range 70-100 m/s. Use 70 m/s for narration, matching facts.yaml F3. About 80 m/s appears in the source-operation drawings)
- "are ejected from a generator at 70 meters per second" (ASML-LL). **A**
- "Droplet stream ~80 m/s" (SW17, slide 29); "80 m/s" (PUR20, slide 23). **A**
- "Small tin droplets (~30um) traveling at high velocity (~100m/s)" (PUR20, slide 12). **A**
- Table 1 "Droplet velocity 60–120 m/s" (FOM17, p.179). **A**

**Repetition rate**
- "this process is repeated 50,000 times every second" (ASML-LL). **A**
- "Current LPP sources operate at a repetition rate of 50 kHz" (FOM17, p.176). **A**
- "Repetition Rate 50kHz" at 250 W (SW17, slide 39; WS18, slide 8). **A**
- Research droplet generators: Table 1 "Droplet frequency 40–100 kHz" (FOM17, p.179); "Tin droplets at 80 kHz" (SW17, slide 33). **A**

**Spacing**
- "Approximately 100 small droplets at an average frequency of 5 MHz were used in this example to produce 50 kHz droplets with a 1.5-mm droplet-to-droplet spacing" (FOM17, p.180). **A**
- Derived: 70 m/s ÷ 50 kHz = 1.4 mm; 80 m/s ÷ 50 kHz = 1.6 mm. **C**
- Formation: the droplet generator modulates a continuous jet. The jet breaks into many tiny droplets, which then merge in flight. "Picture of modulated droplets as they break up from a continuous jet (top) and that of the fully coalesced (formed) droplets at some distance away from the nozzle" (FOM17, Fig. 10, p.179). "Multiple small droplets coalesce together to form larger droplets at larger separation distance" (SW17, slide 32). **A**
- Faster droplets are spaced further apart, which protects the next droplet from the plasma: "Higher-velocity droplets arrive at the target location with greater spacing" (FOM17, Fig. 11, p.180, which shows rows at 26/40/58/84/104/121 m/s). **A**
- Stability: Table 1 "Transverse stability (3σ) <2 μm; Longitudinal stability (3σ) <2 μm" (FOM17). "Short term droplet position stability σ~1µm" (SW17, slide 31). **A**

**Direction of the stream**
- The stream is horizontal. "Source vessel fully populated: • 62 degree orientation • Horizontal tin droplets" (POS16, panel 1). **A**
- The stream crosses the collector axis at right angles. The POS16 panel-1 drawing marks "z" along the collector axis toward the IF and "x" from the "Tin Droplet Generator" through the plasma to the "Tin catch". PUR20 slides 26-27 label "X: droplet & target travel", "Z: laser direction", plus a "Y direction". SW17 slide 30 shows the axes x (droplets), z (toward collector/laser), y. **A**
- Cymer patent background: "horizontal droplet streams ... may be a viable droplet orientation for the EUV LPP source", and droplets at 20 m/s shift only about 1.1 mm from a horizontal path at 300 mm from the nozzle (PAT245, quoted through a page summary). **B**
- Generator principle: "Tin is loaded in a vessel & heated above melting point • Pressure applied by an inert gas • Tin flows through a filter prior to the nozzle • Tin jet is modulated by mechanical vibrations" (SW17, slide 31; PUR20, slide 14). **A**

**Droplet catcher**
- It sits on the opposite side of the vessel from the generator, on the same horizontal line through the plasma. SW17 slide 28 is a rendered photo of the "Populated vacuum vessel with tin droplet generator and collector": "Droplet Catcher" is labelled on the left flank, "Droplet Generator" on the right flank, "EUV Collector" at the bottom and "Intermediate Focus" at the top. The POS16 drawing shows "Tin catch" diametrically opposite the "Tin Droplet Generator" across the plasma. The hydrogen-flow schematic (SW17, slide 34) has "DG" and "Sn catcher" on opposite sides of the vessel. **A**

Drawings rendered:
- `refs/fomenkov_sw2017_slide28.png`: front view of the real NXE:3xy0 vessel. Bowl-shaped lower vessel with radial ports, the collector at the bottom, a tall stack of modules rising to the IF at the top. A large cylindrical catcher module sticks out horizontally to the left. A smaller generator module with a mesh-covered end cap sticks out to the right at the same height.
- `refs/fomenkov_sw2017_slide31.png`: generator schematic (gas bottle, Sn reservoir, filter, modulator, nozzle) and a photo of the generator. It is a long stainless cylinder roughly 3-4x longer than its diameter, ending in a thin angled nozzle tube. Inset shadowgraphs show vertical columns of droplets at 140/50/30/16 µm sizes.
- `refs/fomenkov_sw2017_slide33.png`: droplets at 80 kHz imaged 200 mm from the nozzle across a 1.5 mm field. Six rows; with higher pressure the droplets get bigger and further apart.
- `refs/fomenkov2017_fig11_droplet_spacing.png`: spacing against velocity.

## 2. Drive laser: CO2, pre-pulse and main pulse

**CO2 wavelength and power**
- "The BTS delivers the beam to a focusing optical system where the 10.6-μm wavelength light is focused to a minimum spot size" (FOM17, p.176). **A**
- PUR20 slide 23 labels the main pulse "MP 10.59 µm" (the CO2 P(20) line). **A**
- "ASML NXE systems use CO2 laser with multiple stages of amplification to reach the required power level of >20 kW. It may be operated in pulsed mode at ~50 kHz" (FOM17, p.176). "High power CO2 laser: >20kW pulsed • Laser and EUV pulse duration: 10's ns" (PUR20, slide 12). "MP power on droplet 21.5kW" (SW17, slide 39). TRUMPF: "This method enables the 40 kilowatts of laser power to be used efficiently". **A**

**Path into the vessel: through the central hole of the collector, along its axis**
- "The focused beam propagates through a central aperture in the collector and strikes the droplet at the primary focus of the ellipsoidal collector mirror inside the vacuum space of the source vessel chamber" (FOM17, p.176). **A**
- POS16 panel 1 and SW17 slide 34 both draw the "Laser beam" coming in from behind the collector, through its centre, along the collector axis toward the IF. PUR20 slide 16 (vessel cutaway) shows "Laser pulses" as a red cone rising through the centre of the bowl-shaped collector to the plasma. **A**

**Pre-pulse: also CO2 in the NXE source**
- SW17 slide 29 labels both beams "Pre-pulse CO2 beam" and "Main pulse CO2 beam". PUR20 slide 23 does the same. **A**
- "an industrial ASML 'S2' EUV source driven by a 10.6 μm ... using a 10 μm laser prepulse of few tens of mJ" (TOR20, quoted from the online article). **B**
- The two pulses come from one seed module and are amplified in the same CO2 chain: POS16 "PP&MP Seed unit"; FOM17 Fig. 1 "Prepulse requires seed laser trigger control"; PUR20 slide 40 shows seed stages "MP" and "PP" feeding PA0-PA4. **A**
- The exact pre-pulse wavelength is **not public**. The ASML documents say only "CO2" and the ARCNL paper says "10 μm".

**Energies**
- Main pulse "approximately 500 mJ"; prepulse "few tens of mJ" (TOR20, ASML S2 source used for the experiments). **B**
- Derived: 21.5 kW of main pulse on droplet ÷ 50 kHz ≈ 430 mJ per pulse delivered to the droplet. **C**
- Production pulse energies are **not public**.

**Beam directions and focal spots**
- PUR20 slide 23 "Spatial View" (axes: Z = laser direction, horizontal in the drawing; X = droplet travel, downward). The droplets fall along X at "80 m/s". The pre-pulse beam enters from the left along Z, "Beam Diameter 100µm / Droplet Diameter 27µm". Further along X, the main-pulse beam enters from the same side along Z, "Beam Diameter 400µm / Target Diameter 400µm". EUV is drawn coming off the face of the target that looks back toward the incoming laser. **A**
- SW17 slide 29 shows the same layout: both CO2 beams arrive from one side, perpendicular to the droplet stream, and the main-pulse focus is downstream of the pre-pulse focus. **A**
- PUR20 slide 26: a narrow PP beam waist, then a much wider MP beam. The ellipses show the target can tilt depending on where the droplet sits in the PP beam ("Scan of droplet position in PP beam along direction of droplet travel"). **A**

**Delay between pre-pulse and main pulse**
- **Not public for ASML production sources.**
- ASML modelling follows the drift phase for more than 2 µs: "An adaptive mesh tracks the expanding droplet material for more than 2us" (PUR20, slide 29, with frames at t = 300/500/1000/1500 ns). **A**
- ARCNL lab (1 µm PP, not the ASML source): "The target diameter is precisely controlled via the time delay between pre- and main pulse, which ranges 0–3 µs" (SCH21, p.2). **B**
- Derived, low confidence: in the PUR20 slide 23 overlay, the PP arrow sits at DFC X ≈ 0 and the MP arrow at DFC X ≈ 300 µm. At 80 m/s that offset is about 3-4 µs of flight. The arrows are schematic labels, so treat this only as an order of magnitude. **C**

**Pulse duration**
- "Laser and EUV pulse duration: 10's ns" (PUR20, slide 12). In the PUR20 slide 23 "Temporal View" the PP is a short spike and the MP is a taller, longer pulse with a slow rise and a tail. **A**

Drawings rendered: `refs/purvis2020_slide23.png`, `refs/fomenkov_sw2017_slide29.png`, `refs/purvis2020_slide26.png`, `refs/fomenkov2017_fig12_prepulse_concept.png` (concept drawing: two hourglass beam waists with the laser from above, the droplet trajectory running left to right between them, the droplet flattening, and EUV rays from the expanded target at the main-pulse waist).

## 3. Pre-pulse target shape

- Purpose: "Pre-pulse transforms tin droplet into 'pancake/mist' that matches CO2 main pulse beam profile" (SW17, slide 29). "the droplets are hit first by a low-intensity laser pulse that flattens them into a pancake shape" (ASML-LL). "Pre-pulse (pp) concept drawing showing expansion of the Sn droplet to match the main pulse (MP) beam waist diameter and lower the density of the target material" (FOM17, Fig. 12, p.180). TRUMPF: "the droplet to swell into a disk-like shape" and "The following main pulse is absorbed by the resulting liquid film". **A**
- Size: "Target Diameter 400µm" (PUR20, slide 23). "into a thin, disk-like target about 300 μm in diameter" (TOR20). FOM17 Fig. 7 plots CE against "Target diameter (µm)" from 0 to 500 µm. **A/B**
- Orientation: the disk faces the laser, with its plane perpendicular to the beam. FOM17 Fig. 13B, "Side view shadowgrams ... (B) disk target", shows the disk edge-on as a thin vertical dark line, with the laser travelling horizontally in the image. PUR20 slide 23 draws the expanded target as a flattened ellipse perpendicular to Z (the laser). PM351 (SPIE Press sample, ch.2, p.40 in `refs/PM351.pdf`): "For 10-ns pre-pulses on a droplet, the plasma is essentially disc shaped, with the dominant expansion orthogonal to the incident beam direction". **A/B**
- Production targets are not always a flat disk: "Figure 13A shows a shadowgraph of a typical low density target generated with pre-pulse technologies. For comparison, Figure 13B shows a disk target" (FOM17, p.180). FOM17 Fig. 14 ranks targets "No PP / Disk / Disk / Partial-cloud / Cloud" with CE rising to about 6% for "Cloud". SW17 uses "pancake/mist". **A**
- Mechanism and timescale (ARCNL): "the droplet is accelerated ... The subsequent deformation of the droplet occurs on the much longer inertial timescale τi = R0/U ≈ 1 µs ... slowed down by surface tension on the capillary timescale ... ≈ 14 µs" (KUR16, p.3). ASML: "A small plasma forms at the front side of the droplet that initiates the forces and subsequent shock waves that drive the expansion process" (PUR20, slide 29). The droplet is also pushed along the laser direction (KUR16 title, "Plasma propulsion"). Radial expansion "∼90 m/s" (SCH21, p.2). **A/B**
- What shadowgraphs look like:
  - FOM17 Fig. 13A (`refs/fomenkov2017_fig13_shadowgrams.png`): grey backlit field with a rough, mottled, semi-transparent dome or cloud, about 2/3 of the frame wide, darker toward one side. This is the "spherical"/low-density target. Fig. 13B: a single sharp dark vertical bar, the disk seen edge-on, slightly blurred.
  - KUR16 Fig. 2 (`refs/kurilovich2016_fig2_sheet_expansion.png`, 100 µm scale bar, In-Sn, Nd:YAG 1 µm, laser from the left). Side-view sequence at 0 / 0.4 / 2 / 4.5 / 9 µs: a dark sphere becomes a lens shape, then a thin vertical line growing to about 4x the droplet diameter, which breaks into fragments at the tips by 9 µs. The 30° front view at 2 µs is a dark disk with a thin bright rim. At 70 mJ: 0 / 0.2 / 0.4 / 1 / 1.7 µs, with a faster, thicker, curved sheet. "The white glow visible to the left of the expanding droplet is plasma light" (KUR16, Fig. 2 caption). **B**
  - PUR20 slide 23 right panel: a backlit movie frame from the ASML source, "t = -0.200 usec", axes "DFC Z [um]" from -300 to 400 and "DFC X [um]" from -200 to 600. A dark round droplet sits at (0, 0) with faint diffraction rings, and the PP and MP arrows are overlaid.

## 4. Plasma

- Location: "The laser-plasma interaction takes place at the primary focus of the ellipsoidal collector mirror" (FOM17, p.174). "Plasma at first focus" (SW17, slide 35). **A**
- Temperature: "Temperature ~ 30 -100 eV; Ion density ~ 10^17 – 10^18 #/cm3" (SW17, slide 22, after Nishihara 2008). "Conditions for optimal plasma: Temperatures between 50-100eV" (PUR20, slide 20). Measured on the ASML S2 source: "a 30–42 eV temperature range was probed" (TOR20). Ions: "the ions Sn11+ –Sn14+ contribute to radiation in the 2% reflectivity bandwidth" (TOR20). For narration, follow facts.yaml F5. **A/B**
- Size of the emitting region: **not public as a number**. Proxies: the main-pulse beam and target are 400 µm (PUR20, slide 23), the beam spot was 200-400 µm in TOR20, and the etendue spec is "less than 1–3.3 mm2 sr" (FOM17, p.176).
- Appearance:
  - SW17 slide 23 (`refs/fomenkov_sw2017_slide23.png`) shows an ASML "Tin Laser Produced Plasma Image": on black, a small intense blue-white point inside a soft glow that shades to green and then red-orange at the edge. The camera, filter and false colouring are not stated, so treat it as indicative only.
  - PUR20 slide 16 (`refs/purvis2020_slide16_vessel_cutaway.png`) is an artist's rendering, not a photo: a white-hot point with a violet glow just above the collector centre, and a violet cone of EUV rising to the IF.
  - EUV itself (13.5 nm) is invisible. Any visible colour is plasma emission at longer wavelengths, which ASML has not characterised publicly as a "look".
- Debris: "debris in the form of target fragments, clusters of neutrals and ions" (FOM17, p.175). The electric field in the expanding plasma "accelerates ions from its plasma temperature, i.e. several 10 eV, up to several keV" (FOM17, p.180). The SW17 slide 23 cartoon shows tin ions and electrons flying back toward the laser side, and "'ejecta' microparticles tin vapor" leaving the far side. **A**
- Forces on the next droplet: radiation and an ion "wind" push the incoming droplet (SW17, slide 30: "Measured Angular dependence of Forces on the droplets", "0.1 – 3.0mm spatial scale"). **A**
- Hydrogen: "Hydrogen buffer gas (pressure ~100Pa) causes deceleration of ions • Hydrogen flow away from collector reduces atomic tin deposition rate" (SW17, slide 34; PUR20, slide 35). Tin is removed as stannane: "Sn (s) + 4H (g) → SnH4 (g)" (same slides; FOM17, p.183). "fresh gas has to be flown constantly into the vessel at high flow rates" (FOM17, p.183). In SW17 slide 34 the H2 flow lines start on the collector surface and fan out from it toward the plasma and the IF. **A**
- Debris toward the scanner: "Primary microparticles generated at plasma location are usually blocked by a small obscuration in direct line of sight from the plasma to the intermediate focus" (FOM17, p.183). **A**
- Vessel shape (from the drawings):
  - POS16 panel 1 (`refs/euvls2016_poster_panel1_layout.png`) is a side-section schematic drawn with z horizontal, so it is rotated relative to the real 62° install. The collector is a red concave arc at one end of a rectangular vessel. Orange "Vanes" (seven plates above and below) line a cone that narrows from the collector to the "Intermediate Focus Unit", an hourglass-shaped throat in the vessel wall that joins the "Scanner". The vessel sits on spring/damper mounts on a "Source Pedestal".
  - Real vessel (SW17 slide 28; `refs/euvls2016_poster_panel1_vessel.png`): a wide bowl-shaped lower chamber around the collector with many radial ports, a narrower upper section, and the IF unit and metrology boxes on top. "Six DOF frame" (POS16). "Vessel with vacuum pumping to remove hot gas and tin vapor • Internal hardware to collect micro particles" (SW17, slide 34). **A**

## 5. Collector

- Type: "Ellipsoidal design • Plasma at first focus • Power delivered to exposure tool at second focus (intermediate focus)" and "Normal Incidence Graded Multilayer Coated Collector" (SW17, slide 35). PUR20 slide 33 adds "• IR spectral filtering". "multilayer-coated ellipsoidal mirror" (FOM17, p.176). **A**
- Diameter: ">5sr 650mm diameter normal incidence collector" (POS16, panel 1, NXE:3400B 250 W configuration). **A**
- Collection angle: "A sample picture of a collector with 5.5 sr collecting angle is shown in Figure 16"; "typically only ∼2π sr hemisphere can be used to collect EUV" (FOM17, p.181). **A**
- Central hole: the laser passes "through a central aperture in the collector" (FOM17, p.176). The **hole size is not public**. In the SW17 slide 35 photo (`refs/fomenkov_sw2017_slide35_collector_photo.png`), two gloved people hold the mirror at its rim. It is a shallow, mirror-bright bowl with a gold cast, and a small round central feature about 1/6 of the mirror width. That fraction is our reading of a perspective photo, not a spec. **C**
- Mirror below and behind the plasma, facing up: "accumulated Sn falling or dripping onto the collector surface as it is facing up against gravity in the EUV source" (FOM17, p.183). The vessel photos and PUR20 slide 16 show the collector at the bottom of the vessel, with the plasma just above its centre and the IF at the top. **A**
- Plasma-to-collector and plasma-to-IF distances: **not public**. The only figure is a generic one in Cymer patent background text: the collector is "positioned at a relatively short distance, e.g., 10-50 cm, from the plasma" (PAT245). It is not an NXE design value. **B (generic)**
- Lifetime and temperature: "EUV collector Temperature controlled" (SW17, slide 34). "Over 100 Billion pulses collector lifetime has been demonstrated" (FOM17, p.182). **A**
- Photos: `refs/fomenkov2017_fig16_collector_3100.png` ("normal incidence EUV collector used in the ASML NXE 3100 source"). The mirror sits in a cylindrical stainless housing about one mirror-diameter deep, with a rectangular window in the side wall. A technician in a cleanroom suit stands beside it; the housing is about chest height across.

## 6. Source orientation in the machine; drive laser location

- Tilt: "Source vessel fully populated: • 62 degree orientation • Horizontal tin droplets" (POS16, panel 1). ASML does not say what the 62° is measured from. The most likely reading is the angle between the collector axis (plasma to IF) and horizontal, because the droplets are horizontal and run perpendicular to that axis. Treat the reference plane as **not public**. **A for the number; C for the interpretation**
- EUV leaves upward at an angle toward the IF and illuminator:
  - PUR20 slide 11 (`refs/purvis2020_slide11.png`) is an ASML schematic. Inside the "source" box, the collector is tilted with its concave face up and to the right. The "CO2 laser" (green line) enters from the lower left through the collector centre to "PF". The "droplet generator" sits upper left and the droplets cross PF diagonally. A pink EUV cone runs up and right to "IF" at the boundary with the "scanner" box, then to the illuminator mirrors. The angles in this drawing are schematic.
  - The vessel photos (SW17 slide 28; POS16) show the IF at the top of the vessel. The ASML collector patent family allows the axis "at a nonzero angle, e.g., 10-90 degrees, relative to a horizontal plane" (PAT245). **A/B**
- EUV far field at the IF: PUR20 slide 11 inset "EUV far-field intensity distribution" shows an annulus (red-yellow ring, blue outer edge) with a dark centre and a thin horizontal dark band across it. These are the shadows of the central obscuration and the horizontal hardware. Our reading. **A/C**
- Drive laser in the sub-fab: "The laser is typically installed in the sub-fab along with its RF generators and water-to-water heat exchangers" and "Turning mirrors may be used to allow the beam to travel from the sub-fab to the fab through the waffle-slab floor" (FOM17, p.176). FOM17 Fig. 1, POS16 panel 1 and WS18 slide 6 all label "Fab Floor" over "Sub-Fab Floor", with the CO2 chain (seed, pre-amp, four PAs) below and a "Beam Transport System" rising through the floor to the focusing optics behind the vessel. **A**
- Beam path length: TRUMPF says the BTS "transports the laser beam up to 30 meters in the direction of the droplet chamber". PUR20 slide 12 says "Long laser beam path (~300m) with precise laser-to-droplet timing and targeting required". This is probably the total optical path including the amplifier passes; ASML does not explain it. **A**
- Scale drawing `refs/fomenkov2017_fig2_scale_drawing.png` ("Scale drawing of a laser-produced plasma source for ASML NXE:3300B", FOM17, p.174). On the left is the source vessel on its frame (round vessel, modules, a tall vertical beam tube at the far left). A long, straight, slightly inclined beam-transport tube with regularly spaced supports runs right to a cluster of four large box enclosures in a T/L plan (the laser). No floor plane is drawn.
- PUR20 slide 16 (`refs/purvis2020_slide16.png`): system render labelling "Drive Laser" (large grey X-shaped enclosure), "Drive Laser Ancillaries" (green and blue cabinets), "Beam Transport System" (yellow tube), "Final Focus Assembly", "Vessel" and "Scanner". The levels are not separated in this render.
- High-NA (EXE): "Improved Source position: Allows for larger transmission, compatible with 0.33 NA" (PUR20, slide 42). The EXE source geometry is otherwise **not public**.

---

## NOT public (do not show as fact; use generic or stylised geometry)

1. Plasma-to-collector-vertex distance and plasma-to-IF distance for NXE/EXE (only generic patent text: "10-50 cm").
2. Collector central-aperture diameter, exact ellipsoid parameters, collector thickness and back structure.
3. What the "62 degree orientation" is measured from (horizontal is the likely reading but not stated); the EXE source tilt.
4. Exact pre-pulse wavelength (documents say only "CO2" or "10 μm"); production pre-pulse and main-pulse energies; pulse durations beyond "10's ns".
5. Pre-pulse to main-pulse delay in production (ASML models more than 2 µs of drift; ARCNL labs use 0-3 µs).
6. Exact PP/MP focal offset along the droplet path (only a schematic overlay of about 300 µm in PUR20 slide 23).
7. Nozzle-to-plasma distance and catcher-to-plasma distance (imaging was done at 200 mm and 300 mm from the nozzle in demos, which does not give the installed distance).
8. Size of the EUV-emitting plasma as a number; a calibrated visible-light colour of the plasma (ASML's one "plasma image" has no stated filter or camera).
9. Hydrogen flow rates and the internal vane and obscuration geometry (only "vanes", "small obscuration" and "~100 Pa" are public).
10. Current (NXE:3800E / EXE) droplet size, speed and rate if they differ from the 2016-2020 numbers; the newest public ASML first-party numbers are 27 µm, ~80 m/s and 50 kHz.
