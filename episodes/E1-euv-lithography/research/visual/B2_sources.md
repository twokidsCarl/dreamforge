# B2 sources: vacuum, hydrogen and debris

Checked 2026-10-21. Used by `audit_B2.yaml` (S-numbers). Local copies (not committed) are in `renders/review/refs/B2/`, plus the earlier
source-research files in `renders/review/refs/source/`. Confidence: A = ASML / ZEISS / TRUMPF first-party; B = peer-reviewed,
ARCNL, lab database, patent or textbook; C = media (not used).

## S1 Fomenkov (ASML), "EUV Source for High Volume Manufacturing", 2017 Source Workshop, Dublin (A)
https://www.euvlitho.com/2017/S1.pdf (`refs/source/euvlitho2017_S1.pdf`; slides rendered as `refs/source/fomenkov_sw2017_slide*.png`)
- Slide 34 "Collector Protection by Hydrogen Flow": "Hydrogen buffer gas (pressure ~100Pa) causes deceleration of ions • Hydrogen flow away from collector reduces atomic tin deposition rate"; "Reaction of H radicals with Sn to form SnH4, which can be pumped away. Sn (s) + 4H (g) → SnH4 (g)"; "Vessel with vacuum pumping to remove hot gas and tin vapor • Internal hardware to collect micro particles"; "EUV collector Temperature controlled". Drawing: blue H2 flow lines start on the collector surface and fan out toward the plasma and the IF; DG at top, Sn catcher at bottom.
- Slide 23 (cartoon "Laser produced plasma (LPP) as an EUV emitter"): "tin ions" and "electrons" fly back toward the incoming laser; '"ejecta" microparticles tin vapor' leave the far side of the droplet. The laser enters through the collector, so ions head toward the collector and microparticles away from it. Schematic, not a measurement.
- Slide 28: real NXE vessel, bowl-shaped around the collector, IF at the top. Slide 35: photo of a collector, mirror-bright with a gold cast.
- Use: B2_01, B2_03, B2_06, B2_08, B2_09, B2_10 (source pressure ~100 Pa).

## S2 Fomenkov et al. (Cymer/ASML), "Light sources for high-volume manufacturing EUV lithography", Adv. Opt. Techn. 6 (2017) 173-186 (A)
https://www.degruyterbrill.com/document/doi/10.1515/aot-2017-0029/pdf (`refs/source/fomenkov2017.pdf`; pages rendered `refs/B2/fom17_p182.png`, `fom17_p183.png`)
- p.175: "debris in the form of target fragments, clusters of neutrals and ions".
- p.176: "Tin debris, high-energy ions, and neutrals from the plasma can interact with the collector surface and have the potential to degrade its reflectivity over time."
- p.180: "This electric field accelerates ions from its plasma temperature, i.e. several 10 eV, up to several keV depending on plasma density profile."
- p.182: "high-energy ions and neutrals from the plasma could strike the collector surface and cause irreversible damage. To protect the multilayer reflective coating, hydrogen buffer gas may be used within the vacuum chamber to slow down the high-energy ions, along with special collector capping layers." / "A tin cleaning technique using hydrogen radicals was developed to enhance the rate of tin removal from the collector." / buffer gas "has to efficiently cool the region near the plasma, it has to efficiently stop fast Sn ions, and it should be able to efficiently etch Sn" / "maximum EUV absorption by the buffer gas of 20–30% is accepted".
- Fig. 17 (p.182): NXE:3300 collector reflectivity falling with pulse count, "-0.6%/Gp (SPIE 2016)", "-0.4%/Gp (SPIE 2017)"; "Over 100 Billion pulses collector lifetime has been demonstrated".
- Fig. 18 (p.183): "Hydrogen buffer gas pressure vs. ion energy and flux at the location of the collector surface". Faraday-cup signal against Sn ion energy 0-3500 eV. Without H2 the spectrum reaches ~3.5 keV; at P1 < P2 < P3 both flux and maximum energy drop (to <~1.6 keV, <~1 keV), not to zero.
- p.183: "Sn + 4·H → SnH4 (1)"; "H2 → ·H + ·H (2)"; "Dissociation of molecular hydrogen happens by several mechanisms in the source: thermal dissociation in the plasma region, photo-dissociation by plasma radiation, dissociation by photo-electrons." / "Once SnH4 (stannane) is formed, it can be pumped away as it is gas under the source conditions. However, competing mechanisms are photo-dissociation of stannane and catalytic dissociation on Sn-covered surfaces. These mechanisms tend to bring Sn back to collector surfaces" / "K_net = K_SnH4_formation · (1 − K_Sn_redep)" / "fresh gas has to be flown constantly into the vessel at high flow rates" / "Primary microparticles generated at plasma location are usually blocked by a small obscuration in direct line of sight from the plasma to the intermediate focus."
- Use: B2_01, B2_04, B2_05, B2_06, B2_07, B2_08, B2_09. Also the correct primary source for facts.yaml F27 (see "F27" below).

## S3 ASML, "EUV lithography systems" (A)
https://www.asml.com/en/products/euv-lithography-systems (quoted in A3_sources.md S3)
- "EUV light is absorbed by everything, even air. So the whole light path and everything the light interacts with – from source to wafer – must be in high vacuum."
- Use: B2_02 overlay.

## S4 van de Kerkhof et al. (ASML), "Defectivity Improvements Enabling HVM for EUV Scanners", EUVL Workshop 2019, Berkeley, 12 Jun 2019 (A)
https://www.euvlitho.com/2019/P23.pdf (`refs/B2/euvlitho2019_P23.pdf`; slides `refs/B2/vdk2019_slide2.png`, `_slide15.png`, `_slide19.png`). This is the facts.yaml F28 source.
- Slide 2 (NXE:3400B): "System is not at vacuum: ~5 Pa of H2 • Driven by prevention of oxidation of Ru-coated mirrors and removal of carbon growth • Drawbacks are transport of particles by gas and chemical activity of hydrogen plasma".
- Slide 15 "EUV scanner plasma is different from source plasma. In scanner, plasma is created by EUV photons": source - "Intense CO2 laser pulse strikes tin droplets • High plasma density & temperature"; scanner - "EUV photons hit H2 molecules • Primary electrons create secondaries • Low plasma density & temperature". The slide's illustration shows the scanner plasma as a **violet glow** along the light path inside a cut-away scanner, and the source plasma as a violet glow in the vessel. These are ASML artwork, not photographs.
- Slide 14: "Switch to EUV-ON in 2016 showed >100x more particles. EUV-induced plasma results in new release forces and reduced adhesion".
- Use: B2_10, B2_11.

## S5 Fomenkov, Schafgans et al. (Cymer/ASML), poster "LPP EUV Light Source for HVM: Status and Outlook", EUVL Symposium 2016 (A)
https://euvlsymposium.lbl.gov/pdf/2016/Poster/P-ET-04.pdf (`refs/source/euvls2016_P-ET-04.pdf`, `euvls2016_poster_panel1_layout.png`, `euvls2016_poster_panel10_flow.png`)
- Panel 1: "Source vessel fully populated: • 62 degree orientation • Horizontal tin droplets"; schematic with "Vanes" lining the cone from collector to "Intermediate Focus Unit".
- Panel 10: "protection flow versus EUV power into NXE:3400" - critical cone flow (slm) against raw EUV plasma power, "Used flow 27 um droplets: less needed than anticipated!" (y-axis values not labelled, so no flow number is public).
- Use: B2_02, B2_09 (vessel shape, vanes, tilt).

## S6 Poirier, Hemminga, Lassise, Assink, Hoekstra, Sheil, Versolato (ARCNL), "Strongly anisotropic ion emission in the expansion of Nd:YAG-laser-produced plasma", Phys. Plasmas 29, 123102 (2022) (B)
https://doi.org/10.1063/5.0129112 (abstract via https://research.vu.nl/en/publications/strongly-anisotropic-ion-emission-in-the-expansion-of-ndyag-laser/)
- Ion kinetic-energy distributions measured at seven angles relative to the laser beam for ns Nd:YAG on Sn microdroplets show "strong anisotropic emission characteristics", matching 2D radiation-hydrodynamic simulations. Full text not opened (paywalled); used only for "not isotropic".
- Use: B2_03.

## S7 Poirier, Bayerle, Lassise, Torretti, Schupp, Behnke, Mostafa, Ubachs, Versolato, Hoekstra (ARCNL), "Cross-calibration of a combined electrostatic and time-of-flight analyzer for energy- and charge-state-resolved spectrometry of tin laser-produced plasma", Appl. Phys. B 128 (2022) (B, open access)
https://pmc.ncbi.nlm.nih.gov/articles/PMC8818011/ (full text via Europe PMC, `refs/B2/poirier2022.xml`). This is the facts.yaml F26 source.
- "the violently expanding Sn plasma generates ionic "debris" that may affect the lifetime of the light-collecting multilayer optics by, e.g., coating, implantation or sputtering depending on the energy and charge state of the ions coming from the plasma."
- "Typically the Sn ions coming from the plasma are in charge states of 1+ to 8+ and have energies ranging up to several keV."
- "For ions with the same energy-over-charge ratio, the higher charged ions have higher energy".
- "a hydrogen buffer gas was added ... Sn ions in higher charge states are driven into lower charge states by means of electron capture from the H2 gas."
- Lab plasma (Nd:YAG, 1.12 m flight path, 60 deg), not ASML's CO2-driven source.
- Use: B2_04, B2_05, B2_06.

## S8 van de Kerkhof, Yakunin, Astakhov, van Kampen, van der Horst, Banine (ASML/TU/e/ISTEQ), "EUV-induced Hydrogen Plasma: Pulsed Mode Operation and Confinement in Scanner", J. Micro/Nanopattern. Mater. Metrol. 20(3) 033801 (2021) (A/B)
https://arxiv.org/pdf/2105.10029 (`refs/B2/vdk2021_arxiv.pdf`; "µ" is dropped in the arXiv text layer, so "20 s" there reads 20 µs)
- p.1: "in practice a background gas of roughly 5 Pa hydrogen (H2) must be used, to maintain self-cleaning conditions for the sensitive EUV mirrors. Hydrogen was chosen as background gas, because of the low EUV-absorption and high chemical activity of H-radicals and ions. This gas is excited into a low-density H2 plasma by the EUV radiation." / "The EUV beam will vary in intensity and shape throughout the scanner, as will the plasma which is induced by this ionizing radiation."
- p.3: "firing short <100 ns pulses with energy of ~5 mJ at a repetition period of 20 µs ... 50 kHz"; "The typical EUV pulse train duration is in order of ~100 ms, or ~5000 pulses". Phases: "0 – 0.2 µs Photo-ionization and photo-electric electrons • 0.2 – 1 µs Secondary ionization ... fast expansion • 1 – 20 µs Ambipolar diffusion, decay and slow electron cooling • 20 µs Next EUV pulse: repeat". Table 1: beam at reticle 11 x 1 cm², photon energy 92 eV.
- p.6: "Typical decay times of the scanner plasma at pressures of 1-10 Pa will be longer than the pulse interval of 20 µs and plasma will build up over several pulses."
- p.7: "Pulse by pulse, the electron density will build up until equilibrium is reached ... resulting in a quasi-steady-state background with transient peaks"; H2 at 5 Pa: n = 1.21e21 m^-3; photoionisation attenuation length 0.13 km.
- p.8: "the integrated initial ion density over a single pulse will be in order of 10^15 m^-3" (i.e. ionisation of order 1e-6).
- Use: B2_03, B2_10, B2_11, B2_12.

## S9 Two-body elastic collision kinematics (B, textbook physics)
- For a projectile of mass m1 striking a resting target of mass m2 < m1, the largest possible laboratory deflection of the projectile is θmax = arcsin(m2/m1); the target recoils. Standard result, e.g. M. Nastasi, J. W. Mayer, J. K. Hirvonen, *Ion-Solid Interactions: Fundamentals and Applications* (Cambridge University Press, 1996), ch. 2 (kinematics of binary elastic collisions).
- Derived: Sn (118.71 u) on H2 (2.016 u): arcsin(2.016/118.71) = 0.97 deg; on a single H atom 0.49 deg. Maximum energy transfer per head-on collision 4·m1·m2/(m1+m2)² = 6.5 % (H2).
- Derived: a 1 keV Sn ion moves at sqrt(2E/m) ≈ 40 km/s.
- Use: B2_06, B2_07 (why zig-zag tracks are wrong).

## S10 Liu et al., "Comparative Study on Microstructure of Mo/Si Multilayers Deposited on Large Curved Mirror with and without the Shadow Mask", Micromachines 14 (2023) 526 (B, open access)
https://pmc.ncbi.nlm.nih.gov/articles/PMC10055843/ (`refs/B2/mosi_pmc10055843.xml`)
- "multilayers consisting of 50 bilayers of Mo and Si were deposited ... the period range is from 6.97 nm to 7.07 nm"; "At the wavelength of 13.5 nm, many research groups have been able to fabricate Mo/Si multilayers with the reflectivity close to 70% at near normal incidence".
- The Mo/Si thickness split was not found in this pass (take it from the B4 research).
- Use: B2_05, B2_08 (scale of atoms vs layers).

## S11 CXRO gas transmission (B, LBNL database)
See A3_sources.md S4: air at 1 atm, 13.5 nm - transmission 0.499 through 0.1 mm, 9.6e-4 through 1 mm; H2 at 5 Pa, 1 m - 0.994.
- Use: B2_02.

## S12 ASML patent US11013096B2, "System, method and apparatus for target material debris cleaning of EUV vessel and EUV collector" (priority 2016-01-21) (B)
https://patents.google.com/patent/US11013096B2/en
- Abstract: "generating hydrogen radicals in situ in the EUV vessel, proximate to the target material debris deposits and volatilizing the target material debris deposits and purging the volatilized target material debris deposits from the EUV vessel".
- Radicals come from RF/inductive "hydrogen radical source[s]", not from EUV; product "volatile tin compounds such as SnH4", removed "through the purge outlet"; example "about 1.3 Torr", "about 90 slm"; "additional hydrogen radical sources can be included near the vanes". Pump type not given.
- Use: B2_08 (in-situ cleaning), B2_09 (pumps not specified).

## S13 van de Kerkhof, Yakunin, Kvon, Cats, Heijmans, Chaudhuri, Astakhov (ASML/TU/e/ISTEQ), "Plasma-assisted Discharges and Charging in EUV-induced Plasma", J. Micro/Nanopattern. Mater. Metrol. (2021) (A/B)
https://arxiv.org/pdf/2012.03027 (`refs/B2/vdk2020_arxiv.pdf`)
- Abstract: "The energetic EUV photons excite the background gas into a low-density H2 plasma."
- Fig. 4: "(a) during isolated EUV pulse the electrons from the EUV beam penetrate through the slits. (b) plasma accumulation beyond the beam confines over multiple pulses."
- Use: B2_11 (the glow is not confined to a tube of beam diameter).

## Checked and not used
- US7372049B2 (ASML, priority 2005-12-02), "Lithographic apparatus including a cleaning device and method for cleaning an optical element": hydrogen radicals from hot filaments / RF / electrodes delivered through a flow tube. It does **not** mention SnH4 and does not say EUV makes the radicals. It is a weak source for F27 as worded.
- Harilal et al., Appl. Phys. B 86 (2007) (Purdue), tin-ion stopping in gases: the PDF is a scan without a text layer; not needed.

## F27 (facts.yaml) - recommended re-sourcing
F27 ("氢气缓冲层给锡离子减速；EUV 把氢分子打成氢自由基，与锡反应生成气态 SnH₄ 被抽走") is currently sourced to US11013096B2 and US7372049B2, neither of which supports "EUV makes the radicals". Use S2 p.183 (eqs. 1-2; "photo-dissociation by plasma radiation, dissociation by photo-electrons"; "can be pumped away") and S1 slide 34 (grade A). Narration wording stays acceptable as a simplification.

## Not public (show as 示意 or not at all)
1. Hydrogen flow rates in the source (S5 panel 10 has no y-axis values); exact H2 pressure distribution inside the vessel (only "~100 Pa").
2. Pump type, number and placement on the source vessel; exhaust duct positions.
3. Vane and obscuration geometry (only "vanes" and "a small obscuration").
4. Collector capping-layer material and thickness (only "special collector capping layers"); scanner mirrors are "Ru-coated" (S4).
5. Charge-state and energy spectra of ASML's CO2-driven production source (published spectra are ARCNL Nd:YAG lab plasmas or the S2 Fig. 18 Faraday-cup trace without axes in absolute units).
6. A calibrated visible-light image or colour of the EUV-induced hydrogen plasma (ASML shows only violet artwork, S4 slide 15).
