"""Round 23 (P1): same as compose_round22 writing contact_round23.jpg; R23 overlays in mograph/r2_ov_zz23*.py.
Round 22 (P1): same as compose_round21 writing contact_round22.jpg; R22 overlays in mograph/r2_ov_zz22*.py.
Round 21 (P1): same as compose_round19 writing contact_round21.jpg; R20 overlays in mograph/r2_ov_zz20*.py
(r2_ov_zz20.py cutaway, r2_ov_zz20s.py source, r2_ov_zz20m.py misc).

Round 19 (P1): same as compose_round18 writing contact_round19.jpg; R19 overlays in mograph/r2_ov_zz19*.py
(r2_ov_zz19.py cutaway, r2_ov_zz19s.py source, r2_ov_zz19m.py misc).

Round 18 (P1): same as compose_round17 writing contact_round18.jpg; R18 overlays in mograph/r2_ov_zz18*.py
(r2_ov_zz18.py cutaway, r2_ov_zz18s.py source, r2_ov_zz18m.py misc, r2_ov_zz18p.py plates).

Round 17 (P1): same as compose_round16 writing contact_round17.jpg; R17 overlays in mograph/r2_ov_zy17*.py
(r2_ov_zy17.py cutaway, r2_ov_zy17s.py source, r2_ov_zy17m.py misc, r2_ov_zy17p.py plates).

Round 16 (P1): same as compose_round15 writing contact_round16.jpg; R16 overlays in mograph/r2_ov_zx16*.py
(one file per scene module: r2_ov_zx16.py cutaway, r2_ov_zx16s.py source, r2_ov_zx16m.py misc).

Round 15 (P1): same as compose_round14 writing contact_round15.jpg; R15 overlays in mograph/r2_ov_zw15*.py (B8_03 /
C_03 / B5_01 label load cut to one top-right block + <=1 leader, B1_15 one label, A2_03 opaque formula band + NA / k1
time-split, pancake 300 um dimension line).

Round 14 (P1): same as compose_round13 writing contact_round14.jpg; R14 overlays in mograph/r2_ov_zv14*.py (B8_03
magnifier follows the pointer + current reading, B3_02 one label at a time, B7_06 three timed steps).

Round 13 (P1): same as compose_round12 writing contact_round13.jpg; R13 overlays in mograph/r2_ov_zu13.py (B8_03
two-line read-out + bigger wafer-ruler inset, B7_06 separate M5 / M6 ring labels).

Round 12 (P1): same as compose_round11 writing contact_round12.jpg; R12 overlays in mograph/r2_ov_zt12.py (B8_03
picture-in-picture of the reticle stage from the B8_03M pass + relabelled wafer-ruler inset).

Round 11 (P1): same as compose_round10 writing contact_round11.jpg (no new overlays in R11; structural round).

Round 10 (P1): same as compose_round9 writing contact_round10.jpg; R10 overlays in mograph/r2_ov_zs10*.py.

Round 9 (P1): same as compose_round8 writing contact_round9.jpg (no new overlays in R9).

Round 8 (P1): same as compose_round7 writing contact_round8.jpg; R8 overlays in mograph/r2_ov_zr8.py.

Round 7 (P1): same as compose_round6 writing contact_round7.jpg; R7 overlays in mograph/r2_ov_zr7.py.

Round 6 (P1): compose_round5 writing contact_round6.jpg; R6 overlays in mograph/r2_ov_zr6.py.

Round 5 (P1): compose_round4 writing contact_round5.jpg; R5 overlays in mograph/r2_ov_zr5.py.

Round 4 (P1): compose_round3.py writing contact_round4.jpg; new R4 overlays come from mograph/r2_ov_zr4.py,
which loads last and overrides earlier modules.

Round 3 (P1): compose_round2.py with one change: B5_01 is composed without the chapter
card (R2 review: the card sat on the beam path; in the edit it gets its own beat before the shot).

Round 2 (P1): same as compose_styleframes.py plus the overlay layer from mograph/r2_ov_*.py (magnifiers,
leader labels, counters, title) drawn on the render before the storyboard label and the subtitle bar.
Shots listed in a module's NO_STORYBOARD_LABELS skip the storyboard label (their overlay carries the text).

Styleframes as the viewer will see them: rendered frame + on-screen label + subtitle at that moment (edit_film's
look), one 3-frame strip per shot, and a contact sheet.
  python3 compose_styleframes.py JOBS_FILE [JOBS_FILE ...] --out DIR
JOBS lines: "<shot> f1,f2,f3". Reads renders/shots/<shot>/sample/<f>.png. Writes DIR/<shot>_<f>.png,
DIR/strip_<shot>.jpg, DIR/contact.jpg."""
import argparse, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "../../../.."))
sys.path.insert(0, os.path.join(REPO, "shared/tools"))
from PIL import Image, ImageDraw
import edit_film as EF
import story_reel as SR
from overlay_labels import draw_label as _draw_label_r4, font
import overlay_labels as _OL


def draw_label(layer, lab, a, W, H):
    """R5: storyboard labels on a crisp dark translucent panel. The R4 soft scrim read as a grey smudge on bright
    frames (D_07 ceiling, B6_12 / B7_06 studio backdrops)."""
    orig = _OL.scrim

    def panel(layer_, box, a_, s_):
        d_ = ImageDraw.Draw(layer_)
        pad = int(8 * s_)
        d_.rounded_rectangle((box[0] - pad // 2, box[1] - pad, box[2] + pad * 2, box[3] + pad),
                             radius=int(6 * s_), fill=(7, 11, 20, int(190 * a_)))
    _OL.scrim = panel
    try:
        _draw_label_r4(layer, lab, a, W, H)
    finally:
        _OL.scrim = orig
from paths import RENDERS, timed_shots
import glob as _glob
import importlib.util as _ilu

OVERLAYS, NO_LABELS = {}, set()
_mg = os.path.join(REPO, "episodes/E1-euv-lithography/mograph")
sys.path.insert(0, _mg)
for _p in sorted(_glob.glob(os.path.join(_mg, "r2_ov_*.py"))):
    if _p.endswith("r2_ov_common.py"):
        continue
    _spec = _ilu.spec_from_file_location(os.path.basename(_p)[:-3], _p)
    _m = _ilu.module_from_spec(_spec)
    _spec.loader.exec_module(_m)
    OVERLAYS.update(getattr(_m, "OVERLAYS", {}))
    NO_LABELS |= set(getattr(_m, "NO_STORYBOARD_LABELS", ()))

FPS = 24
NO_CHAPTER = {"B5_01"}
ap = argparse.ArgumentParser()
ap.add_argument("jobs", nargs="+")
ap.add_argument("--out", required=True)
ap.add_argument("--size", default="960x540")
ap.add_argument("--src", default="sample", help="render subfolder under renders/shots/<id>/")
a = ap.parse_args()
W, H = map(int, a.size.split("x"))
os.makedirs(a.out, exist_ok=True)
shots = {s["id"]: s for s in timed_shots()}
mg = SR.mograph_ids()
order = []
for jf in a.jobs:
    for l in open(jf):
        if l.strip() and not l.startswith("#"):
            sid, fr = l.split()
            if sid not in shots:            # R12: B8_03M is a render pass for the B8_03 overlay, not a shot
                continue
            order.append((sid, [int(x) for x in fr.split(",")]))
strips = []
for sid, frames in order:
    s = shots[sid]
    labs, chap = EF.labels_for(s, mg), (None if sid in NO_CHAPTER else EF.chapter_of(s, mg))
    if sid in NO_LABELS:
        labs = []
    tiles = []
    for f in frames:
        p = os.path.join(RENDERS, "shots", sid, a.src, f"{f:04d}.png")
        img = Image.open(p).convert("RGB").resize((W, H), Image.LANCZOS)
        t = (f - 1) / FPS
        if sid in OVERLAYS:
            img = OVERLAYS[sid](img, t, s["duration"], W, H)
        img = img.convert("RGBA")
        if chap:
            ca = max(0.0, min(1.0, (t - 0.2) / 0.5, (2.8 - t) / 0.5))
            if ca > 0:
                img = EF.draw_chapter(img, chap[0], chap[1], ca, W, H)
        for t0, t1, lb in labs:
            la = max(0.0, min(1.0, (t - t0) / 0.33, (t1 - t - 0.17) / 0.33))
            if la > 0:
                layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
                draw_label(layer, lb, la, W, H)
                img = Image.alpha_composite(img, layer)
        cue = next((c for c in s.get("subs") or [] if c["start"] <= t < c["end"]), None)
        if cue:
            img = EF.subtitle(img, cue["text"], W, H, 1.0, bar=EF.needs_bar(img, W, H, s.get("engine")))
        img = img.convert("RGB")
        img.save(os.path.join(a.out, f"{sid}_{f:04d}.png"))
        tiles.append(img)
    strip = Image.new("RGB", (W * len(tiles), H))
    for i, im in enumerate(tiles):
        strip.paste(im, (i * W, 0))
    strip.save(os.path.join(a.out, f"strip_{sid}.jpg"), quality=90)
    strips.append((sid, s["style"], strip))
# contact sheet: one row per shot (3 frames at 320x180) with an id tag
tw, th = 320, 180
sheet = Image.new("RGB", (tw * 3 + 150, th * len(strips)), (12, 12, 16))
d = ImageDraw.Draw(sheet)
for r, (sid, style, strip) in enumerate(strips):
    sheet.paste(strip.resize((tw * 3, th), Image.LANCZOS), (150, r * th))
    d.text((10, r * th + 60), sid, font=font(26), fill=(240, 240, 240))
    d.text((10, r * th + 100), style, font=font(18), fill=(160, 170, 190))
sheet.save(os.path.join(a.out, "contact.jpg"), quality=85)
sheet.save(os.path.join(a.out, "contact_round23.jpg"), quality=85)
print(len(strips), "shots ->", a.out)
