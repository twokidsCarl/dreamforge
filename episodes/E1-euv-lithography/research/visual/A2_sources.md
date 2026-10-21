# A2 sources: why a shorter wavelength (diffraction, Rayleigh, 193 nm -> 13.5 nm)

Visual audit: `research/visual/audit_A2.yaml`. Downloads (not committed): `renders/review/refs/A2/`
(ASML pages `asml_*.html`, annual reports `ar2022.htm` / `ar2025.htm`, `dl/spie5040_36.pdf`, page render
`smith5040_p2.png`, preview contact sheets `sheet_A2_*.png`). All quotes are verbatim; fetched 2026-10-21.

## S1 ASML, "The Rayleigh criterion for resolution" (grade A)
https://www.asml.com/en/technology/lithography-principles/rayleigh-criterion
- Formula: "CD = k1 • λ / NA"
- "In the Rayleigh criterion equation, CD is the critical dimension, or smallest possible feature size, and λ is the wavelength of light used."
- "NA is the numerical aperture of the optics, defining how much light they can collect."
- "Finally, k1 (or the k1 factor) is a coefficient that depends on many factors related to the chip manufacturing process. The physical limit lithography is k1 = 0.25."
- "Smaller critical dimension can be achieved by using a combination of smaller light wavelength and larger numerical aperture (NA), while pushing k1 as close as possible to the physical limit."
- The page names no NA values, no diffraction, no computed resolutions.

Used for: A2_03 (formula, labels, k1 = 0.25), A2_04 (two routes -> finer lines).

## S2 ASML Annual Report 2022, p.82, "Advanced patterning with EUV ..." (grade A)
https://www.sec.gov/Archives/edgar/data/937966/000093796623000016/a2022annualreportbasedon.htm
> "With a single exposure of DUV light at 193 nm, for example, the smallest feature of the image of a microchip
> pattern reaches its physical limit around 40 nm. However, by using two or more exposures of the same pattern –
> so-called multiple patterning – it is possible to image details at 20 nm with two exposures, or at 10 nm with four
> exposures and additional process steps. Over the past decades, multiple patterning with DUV has become mainstream
> in semiconductor manufacturing, at the cost of having to go through the same process steps multiple times, which
> increases production cycle time and environmental impact. Compared to DUV, EUV at 13.5 nm enables a more efficient
> chip-manufacturing process. Because of the higher resolution of an EUV system, several exposures and process steps
> can be replaced by a single exposure and fewer process steps to pattern a certain layer of a chip. According to a
> study conducted by imec, EUV enables the number of non-lithography processing steps for some critical layers to be
> reduced by up to three to five times – and this significantly reduces production cycle time."

Used for: A2_05 (~40 nm), A2_06 (20 nm / 2 exposures, 10 nm / 4 exposures + extra steps, same steps repeated),
A2_09 (single exposure replaces several; up to 3-5x fewer non-litho steps, some critical layers, imec study).

S2b, ASML Annual Report 2025 (business strategy, p.40-41 region of the SEC text):
https://www.sec.gov/Archives/edgar/data/0000937966/000162828026011378/asml-20251231.htm
> "By developing new lithography technologies with finer resolutions – such as EUV 0.33 NA and the latest EUV 0.55 NA
> (High NA) system – ASML supports chipmakers in simplifying the manufacturing process, moving from multi-patterning to
> single patterning."

## S3 ASML, "Light and lasers" (grade A)
https://www.asml.com/en/technology/lithography-principles/light-and-lasers
- "Going even further into the UV spectrum, the next generation of DUV lithography systems use argon-fluoride (ArF) excimer lasers that produce light with a wavelength of 193 nm. This enabled features sizes of 38 nm to be printed."
- "EUV lithography, a technology entirely unique to ASML, uses light with a wavelength of 13.5 nanometers. This wavelength is more than 14 times shorter than DUV light."
- "The shorter the wavelength of light, the smaller the microchip features that can be printed in a lithography process."

Used for: A2_07 (to-scale comparison, "短 14 倍以上"), A2_05 (38 nm vs the annual report's ~40 nm).

S3b ASML, "Lenses and mirrors" (grade A): https://www.asml.com/en/technology/lithography-principles/lenses-and-mirrors
- "In 2003, ASML took an important step forward in improving the resolution of our DUV systems. We developed immersion lithography ... by projecting the light through a layer of water between the lens and the wafer."
- "Without the water, reaching an NA of more than 1 was impossible. With it, our systems' optics reach an NA of 1.35."
- "ASML's latest EUV platform (EXE) increased the system's NA from 0.33 to 0.55."
- EUV mirrors "have an NA of 0.55. Although that's lower than the NA in DUV machines, the EUV systems print smaller features because they use a much smaller wavelength of light"

## S4 ASML, TWINSCAN NXT:2100i product page (grade A)
https://www.asml.com/en/products/duv-lithography-systems/twinscan-nxt2100i
- Spec table: Resolution "≤ 38 nm"; "1.35 NA".

## S5 OpenStax, University Physics Vol. 3, s.4.1 Single-Slit Diffraction (textbook)
https://openstax.org/books/university-physics-volume-3/pages/4-1-single-slit-diffraction
- Minima: "a sin θ = mλ" (a slit width, θ angle from the original direction, m order).
- "After passing through a narrow aperture (opening), a wave propagating in a specific direction tends to spread out."
- "According to Huygens's principle, every part of the wave front in the slit emits wavelets."
- Consequence used in A2_01/A2_02: first minimum at sin θ = λ/a, so a narrower slit gives a wider central lobe;
  for a ≤ λ there is no minimum and the wave spreads over the whole forward half-space.

## S6 B. W. Smith (RIT), "Forbidden pitch or duty-free: revealing the causes of across-pitch imaging differences", Proc. SPIE 5040 (2003) (grade B)
https://rit.edu/~w-lithography/research/imagetheory/SPIE_5040-36_full.pdf (p.2 text, Fig.2 annotations; page render viewed)
- p.2: "Zone A is the region of first order capture, where additional first order results in imaging energy beyond the zero order."
- Fig.2 marks the first-order capture threshold at pitch = λ/(NA(1+σ)) (pitch axis in units of λ/NA).
- Consequence: an image of a line/space pattern needs at least one first diffraction order inside the lens; with
  σ -> 1 the smallest pitch is λ/(2NA), i.e. half-pitch 0.25 λ/NA - the k1 = 0.25 limit of S1. Below it the lens passes
  only the zero order and the exposure is uniform (A2_02's lines merging into one grey band).

## S7 Evident (Olympus) Microscopy Resource Center, "Numerical aperture" tutorial (manufacturer reference)
https://evidentscientific.com/en/microscope-resource/tutorials/nuaperture (same text: https://micro.magnet.fsu.edu/primer/java/nuaperture/index.html)
- "Numerical Aperture (NA) = n • sin(θ) where n is the refractive index of the media in the object space"; θ is one half of the angular aperture.

Used for: A2_04 (NA drawn as the half-angle of the converging cone).

## Recomputations
| quantity | computation | result | where |
|---|---|---|---|
| wavelength ratio | 193 / 13.5 | 14.30 ("more than 14 times", S3) | A2_07 |
| A2_07 scale | 1400 px x 13.5/193 | 97.9 px per EUV period; 14 periods = 1371 px, 0.30 period (29 px) left undrawn | A2_07 |
| ArFi theoretical limit | 0.25 x 193 / 1.35 | 35.7 nm | A2_05 |
| k1 implied by 38 nm (S3, S4) | 38 x 1.35 / 193 | 0.266 | A2_05 |
| k1 implied by ~40 nm (S2) | 40 x 1.35 / 193 | 0.280 | A2_05 |
| dry ArF floor (NA < 1, S3b) | 0.25 x 193 / 1.0 | 48 nm -> 40 nm needs immersion | A2_05 |
| EUV 0.33 NA limit (not shown) | 0.25 x 13.5 / 0.33 | 10.2 nm | - |
| EUV 0.55 NA limit (not shown) | 0.25 x 13.5 / 0.55 | 6.1 nm | - |
| pitch splitting | 40 / 2, 40 / 4 | 20 nm, 10 nm (matches S2) | A2_06 |
| A2_01 slit | a = 90 px, λ = 60 px: asin(λ/a) | first minimum 41.8 deg; drawn fan 1.4 x = 58.5 deg | A2_01 |
| A2_01 phase | 820 mod 60 | 40 px: arcs start 2/3 λ out of step with the plane crests | A2_01 |
| A2_02 inset | a from 90 to 20 px | 1.5 λ -> 0.33 λ; fan clamped at 85 deg | A2_02 |
| A2_04 cone | sin 14 deg, sin 36 deg | 0.24 -> 0.59 (EUV 0.33 = 19.3 deg, 0.55 = 33.4 deg) | A2_04 |
| A2_05 finer lines | 80 px = 40 nm -> 2 px/nm | cyan lines 12 px = 6 nm wide, 44 px = 22 nm pitch (inconsistent) | A2_05 |
| A2_09 collapse | before 4 x (3 + 2 grey) = 20 blocks, non-litho 4 etch + 8 grey = 12; after 3 blocks, 1 non-litho | 12x non-litho (6.7x total) vs caption 3-5x; with 2 grey kept: 12/3 = 4x | A2_09 |

## Conflicts
- 38 nm (ASML light-and-lasers, NXT:2100i spec) vs "around 40 nm" (ASML AR 2022). Both ASML. The film says 约 40 nm,
  which is the annual report's general statement and covers both; the 38 nm figure is a product spec at k1 0.266.

## Notes outside the fact check
- A2_10 preview is black after 0.2 s: `pen_fails()` calls `fade(t, 0.0, 0.2, dur, 0.05)` (shared/tools/mograph.py
  `fade(t, a, b, dur, f)` = 1 only inside [a, b]); 128 of 132 frames are 750-byte black PNGs.
- A2_08 ribbon: the WOOD/BANDS displacement gives notched, doubled crests in every preview frame.
- Fact IDs printed on screen (F53, F1 · F54, F54, F1) are a film-wide convention (A0 does the same); a bare "F54"
  (A2_06) tells viewers nothing - add the source name.
- Narration "过去二十多年的主力" (A2_05 vo) is a facts.yaml matter, not checked here; ASML dates immersion to 2003 (S3b).

## Not public / not needed
- Nothing in A2 depends on unpublished data; the only unlabelled geometry (cone angle, ruler length, ribbon) is
  conceptual and carries no number.
