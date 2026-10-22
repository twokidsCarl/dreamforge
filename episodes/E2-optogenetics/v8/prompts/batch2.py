import subprocess
from concurrent.futures import ThreadPoolExecutor
G=("Scientific illustration in David S. Goodsell's molecular painting style (flat fills, thin dark outlines, crowded but legible, cross-section, painted texture), "
 "but in a DUSK KEY to match a dark cinematic documentary: the extracellular water is deep indigo-teal (#13203F to #1C3350) with molecules in desaturated dusty blue and violet; "
 "the membrane is warm ochre-cream lipid heads (#E3C27D) with darker amber tails; the cytoplasm below is deep plum (#2A1735) crowded with muted mauve filaments and blobs. "
 "Only story light is luminous cyan-blue (#3FA9FF) with a soft glow. No text, no labels, no watermark. ")
J=[
("sf09b_chr2_dusk","1536x864","high",G+"Center: the light-gated ion channel channelrhodopsin-2 as a dimer of two seven-helix bundles, mint-teal (#63C7A8) with darker teal outline, a small orange retinal chromophore (#FF8A3D) inside each half. A narrow shaft of cyan-blue light descends from top onto it; the pore between is open and glowing faintly cyan, and a stream of small yellow sodium ions (#FFD166) passes through it from top to bottom. Elsewhere in the membrane a few closed teal channels sit dark. Generous breathing room around the hero channel; camera slightly low so the membrane band reads as a slab with depth."),
("sf08b_relay_dusk","1536x864","high",G+"A single continuous membrane slab across the frame, slight perspective. Left two-thirds: a slow multi-step relay reading left to right — (1) a violet light-sensing receptor catches a cyan photon, (2) a three-part G-protein (rose, orange, tan) detaches and drifts along the inner leaflet, (3) an intermediate enzyme (muted blue), (4) finally a teal ion channel opens far to the right; faint dotted motion trails link the steps. Right third, separated by a soft gap: a teal ion channel with a tiny bright magenta synthetic chemical photoswitch tethered to its mouth, and a few magenta molecules drifting down from above as if added from outside. Clean readable staging, not cluttered."),
("sf03b_microbes_dusk","1536x864","high","Art direction: premium cinematic science-documentary illustration, stylized 3D-illustration hybrid, soft volumetric light, deep indigo-navy shadows, matte painterly surfaces, fine grain, clear depth. No text. "
 "Microscopic diptych as one continuous dusk-lit scene, separated by a thin vertical shaft of cyan-blue light. Left: rod-shaped halophilic archaea (Halobacterium) among small cubic salt crystals, cells muted rose with distinct deep-purple membrane patches, dim warm backlight. Right: a single green Chlamydomonas alga (oval body, cup-shaped chloroplast, two front flagella) in dark teal water, its orange-red eyespot catching a ray of cyan light. Restrained saturation, elegant, scientifically plausible, no sunset, no landscape."),
]
def run(j):
    open(f"work/p_{j[0]}.txt","w").write(j[3])
    return subprocess.run(["python3","tools/gen.py",*j[:3],f"work/p_{j[0]}.txt"],capture_output=True,text=True).stdout
for o in ThreadPoolExecutor(3).map(run,J): print(o.strip())
