# B3 sources: collector mirror, plasma at focus 1, EUV focused to the intermediate focus

Checked 2026-10-21. Used by `audit_B3.yaml` (S-numbers). Local copies (not committed): `renders/review/refs/B3/`
(slide PNGs copied from `refs/source/`; contact sheets of the B3 previews in `refs/B3/sheets/`).
Confidence: A = ASML / Cymer / ZEISS first-party; B = patent, peer-reviewed or standard reference; C = our own arithmetic from A/B inputs.
Background: `research/visual/euv_source.md` s.4-6 (collector, plasma, vessel) and its "NOT public" list.

## S1 Fomenkov (ASML), 2017 Source Workshop, slide 35 "EUV Collector: Normal Incidence" (A)
https://www.euvlitho.com/2017/S1.pdf (`refs/B3/fomenkov_sw2017_slide35.png`)
- "Ellipsoidal design • Plasma at first focus • Power delivered to exposure tool at second focus (intermediate focus)"
- "Wavelength matching across the entire collection area"; caption "Normal Incidence Graded Multilayer Coated Collector".
- The photo: two gloved people hold the mirror at its rim. It is a shallow bowl that reflects like a mirror, with a warm gold/amber cast and **no rainbow bands**. A small round feature sits at the centre. Our reading of the photo is that it spans about 1/6 of the width (C).

## S2 Fomenkov, Schafgans et al. (Cymer/ASML), poster P-ET-04, 2016 EUVL Symposium, panel 1 (A)
https://euvlsymposium.lbl.gov/pdf/2016/Poster/P-ET-04.pdf (`refs/B3/euvls2016_poster_panel1_layout.png`)
- ">5sr 650mm diameter normal incidence collector"; "Source vessel fully populated: • 62 degree orientation • Horizontal tin droplets".
- The schematic is drawn with z horizontal. Its rim reaches about the plasma plane, just behind the plasma. The laser comes through the collector centre along z. The droplet generator and the "Tin catch" sit on opposite sides of the plasma. "Vanes" line a cone that narrows to the "Intermediate Focus Unit", an hourglass throat at the vessel/"Scanner" boundary. Red rays cross at the IF and diverge into the scanner. All proportions in the drawing are schematic.

## S3 Fomenkov et al. (Cymer/ASML), Adv. Opt. Techn. 6:173-186 (2017) (A)
https://www.degruyterbrill.com/document/doi/10.1515/aot-2017-0029/pdf (`refs/source/fomenkov2017.pdf`)
- p.174: "The laser-plasma interaction takes place at the primary focus of the ellipsoidal collector mirror."
- p.175: "EUV mirrors typically have a reflectivity of less than 70%" and "in the scanner with 10 reflections from intermediate focus (IF) to the wafer and peak mirror reflectivity of 67%, the overall transmission is about 2%."
- p.176: "The focused beam propagates through a central aperture in the collector and strikes the droplet at the primary focus of the ellipsoidal collector mirror".
- p.181: "open access to the EUV emission pattern over the full 4π sr; however, typically only ∼2π sr hemisphere can be used to collect EUV. A sample picture of a collector with 5.5 sr collecting angle is shown in Figure 16. The challenge is to achieve high reflectance over the full surface of the collector, accepting the fact that when the angle of incidence approaches 45°, only the s-polarized light is reflected."
- p.183: "Primary microparticles generated at plasma location are usually blocked by a small obscuration in direct line of sight from the plasma to the intermediate focus"; the collector is "facing up against gravity in the EUV source".

## S4 Purvis (ASML), "An Introduction to EUV Sources for Lithography", STROBE 2020, slide 11 (A)
https://strobe.colorado.edu/wp-content/uploads/STROBE_ASML-EUV-Sources_Purvis_25-Sept-2020-1.pdf (`refs/B3/purvis2020_slide11.png`)
- Title: "EUV light is generated in the source and guided through the scanner onto the wafer".
- The schematic has a "source" box and a "scanner" box, with the IF on the boundary between them. The collector is tilted, the CO2 laser comes in through its centre to "PF", and a pink cone runs from the collector to the "IF".
- After the IF the beam reflects off the first "illuminator" mirror and then **zig-zags between mirrors**. Every change of direction happens at a mirror.
- Inset "EUV far-field intensity distribution": a ring with a dark centre and a thin horizontal dark band across it.

## S5 Fomenkov (ASML), 2017 Source Workshop, slide 28 "NXE:3XY0 EUV Source: Main modules" (A)
https://www.euvlitho.com/2017/S1.pdf (`refs/B3/fomenkov_sw2017_slide28.png`)
- Rendered photo of the vessel. "EUV Collector" is at the bottom and "Intermediate Focus" at the top. "Droplet Catcher" is on the left flank and "Droplet Generator" on the right, on one horizontal line.

## S6 US7288777B2, "Collector for EUV light source" (Cymer, now ASML; priority 2003-04-08) (B)
https://patents.google.com/patent/US7288777B2/en
- "an elliptical mirror that has a first focus at the ignition site 28"; the collector has "an aperture for the laser light to enter to the ignition site 28".
- The claims name an elliptical mirror "comprising an aperture centered on the longitudinal axis of the elliptical collector mirror permitting irradiation of the plasma initiation point with a laser beam".
- The mirror extends "almost to the focus point 28 of the elliptical mirror 150", so that it does not block the target droplets.

## S7 US7439530B2, "LPP EUV light source drive laser system" (Cymer, now ASML), cited by F56 (B)
https://patents.google.com/patent/US7439530B2/en
- "a collector 30, e.g., a reflector, e.g., in the form of a truncated ellipse, with an aperture for the laser light to enter to the ignition site 28".
- "an elliptical mirror that has a first focus at the ignition site 28 and a second focus at the so-called intermediate point 40".
- The patent gives no distances and no collector diameter.

## S8 US10101569B2, "Mirror, in particular collector mirror for microlithography" (Carl Zeiss SMT) (B)
https://patents.google.com/patent/US10101569B2/en
- "a layer stack including a plurality of alternating individual layers of molybdenum and silicon"; "a layer thickness of the individual layers is chosen depending on a local ray incidence angle". This is the graded coating: the layer period changes across the mirror.
- "the collector mirror 10 may have a perforation or a hole there" (vertex region). All coordinates are normalised, so the patent gives no absolute size.

## S9 Wolfram MathWorld, "Ellipse" (B, after Hilbert & Cohn-Vossen 1999, pp. 2-3)
https://mathworld.wolfram.com/Ellipse.html
- An ellipse is "the locus of all points in the plane the sum whose distances ... is a given positive constant".
- "A ray of light passing through a focus will pass through the other focus after a single bounce".

## S10 ASML, "Light and lasers" (A), through F2
https://www.asml.com/en/technology/lithography-principles/light-and-lasers
- "this process is repeated 50,000 times every second".

## S11 High-NA illuminator train (A): `research/visual/high_na_optics.md`
- ZEISS, EUVL Workshop 2024 [Z24], slide 13; ASML, EUVL Workshop 2022 [A22], slide 36 ("Intermediate Focus", "Field Facet Mirror", "Pupil Facet Mirror").
- The train after the IF is a small fold mirror, then the field facet mirror, then the pupil facet mirror, then the mask. Each one folds the beam.

## Geometry recomputed from the code (C)
Script run 2026-10-21 (python, written out in the audit notes).
- **3D collector** (`build_source.py`): IF_X = 14, COLLECTOR_VERTEX_X = -4, RIM_X = -0.35, HOLE_R = 0.7.
  - This gives a = 11, c = 7, b = 8.485 and eccentricity 0.636. Plasma to vertex is 4 units; plasma to IF is 14 (3.5x).
  - The rim radius is 6.31 (diameter 12.6). Seen from the plasma, the rim sits at 93.2° from the axis toward the IF, i.e. 3° behind the plasma plane. The hole edge sits at 170°. Hole to rim diameter ratio is 0.11.
  - Collected solid angle is 5.84 sr. The angle of incidence is 3.9° at the hole edge and 31.5° at the rim.
  - The IF cone half-angle at the rim is 23.7°. The IF is 1.1 collector diameters from the plasma.
  - `light_rays()` uses the focal polar form r = b²/(a - c·cosθ). I traced 2000 random rays: every hit point lies on the surface (error < 1e-6), and the reflected direction points at F2 to within 2.3e-6°.
- **2D blueprint** (`mograph/b3.py`): A = 640, B = 360, c = 529, eccentricity 0.827. F1 to vertex is 111 px; F1 to F2 is 1058 px (9.5x).
  - The mirror arc runs over θ = 0.62π to 1.38π. Seen from F1 its ends are 48.7° from the axis, i.e. far in front of the plasma toward F2. As a surface of revolution that arc would collect 10.4 sr, and its angle of incidence at the ends is 54°.
  - B3_04 rays hit between 58.5° and 180° (9.6 sr, angle of incidence up to 51°). One ray, k = 7, hits the vertex exactly.
  - All 15 rays reflect through F2 (maximum error 1.2e-6°). The normals come from the gradient (cosθ/A, sinθ/B), which is correct.

## Reflectivity
No B3 shot shows a reflectivity number. If one is added, use ZEISS "up to 70 percent" (A3_sources S2) or S3 p.175 "peak mirror reflectivity of 67%" (scanner mirrors). No public number gives the reflectivity of the collector itself when new. FOM17 Fig. 17B plots it against pulse count but quotes no headline figure.

## Not public (draw as 示意)
1. Plasma-to-vertex and plasma-to-IF distances, and the ellipse parameters (S7 and S8 give none; euv_source.md not-public items 1-2).
2. Diameter of the central hole (we read about 1/6 of the width off the S1 photo).
3. IF aperture diameter, and the geometry of the IF unit throat.
4. Geometry of the obscuration, the vanes and the vessel interior.
