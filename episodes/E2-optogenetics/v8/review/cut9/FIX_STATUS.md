# E2 Cut9 samples — 2026-10-24 (UTC+8)

Carl Cut8 feedback (09:23): Goodsell molecular style LOCKED (SF09 ChR2 / SF06, untouched); Blender-fur mouse REJECTED ("还是太假"); SF01 ball-and-stick neurons REJECTED ("这个有问题").
Blender fur iteration stopped (no hair retune). Real-mouse refs: Wikimedia Commons "Black 6 mouse" (eating.jpg / drinking.jpg), see `mouse_routes_vs_real.png`.

| file | route | how |
|---|---|---|
| mouseA_photoreal_still.png / mouseA_photoreal_clip.mp4 (5 s, 1176x784) | A · photoreal AI still → i2v | gpt-image-2 text-to-image (C57 traits + headcap/ferrule/patch-cord spelled out) → wan2.6-i2v-flash, side track + gentle push-in |
| mouseB_illustrated_still.png / mouseB_illustrated_clip.mp4 (5 s) | B · clean illustrated (no beads) | gpt-image-2 edit of the A still → ink-outline cel illustration in the indigo/violet/teal palette → wan2.6-i2v-flash |
| sf01_goodsell_still.png / sf01_goodsell_clip.mp4 (5 s, 1280x720) | SF01 redo · Goodsell tissue | gpt-image-2 with sf09e_chr2 as style ref → edit to centre the 470 nm cone → wan2.6-i2v-flash slow push-in; text-free, no PIP (HUD goes on in post) |

## Self-check (viewer eyes)
- **A**: reads as a real black-6 lab mouse. Glossy near-black coat, pointed snout, no neck, thin pink ears, one small bead eye, fine whiskers, white headcap + ferrule + metal sleeve + thin fibre. Camera tracks forward only, no grain, floor stays solid. Minor issue: over the 5 s the coat drifts a little toward grey-brown. **Recommended.**
- **B**: clean and not scary, and the eye is correct. It sits better next to the indigo palette, but it reads as a children's-book drawing more than Goodsell. The back wall grid grows a little during the push.
- **SF01**: dense Goodsell tissue, one class of pyramidal neuron lit teal inside a top-centre blue cone, others unlit. The axon "pulse" segments read slightly like glowing beads.

Rejected in-round: A v1 (copied the ref photo, cracker and paper towel included), A v3 (headcap with no ferrule/fibre), B v1/v2 (put the mouse on a membrane / protein heap = wrong scale), B v3 (still photographic), SF01 v2 (four identical neurons in a row = templated), SF01 v1 (beam top-left, lit cell outside the beam).

## Spend
gpt-image-2 ≈ $0.33 (11 calls) · Wan 2.6 flash 3×5 s ≈ $1.50 (est) · RunPod none. Round ≈ $1.83.
