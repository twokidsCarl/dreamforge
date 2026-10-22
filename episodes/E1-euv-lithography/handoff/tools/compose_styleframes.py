"""Styleframes as the viewer will see them: rendered frame + on-screen label + subtitle at that moment (edit_film's
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
from overlay_labels import draw_label, font
from paths import RENDERS, timed_shots

FPS = 24
ap = argparse.ArgumentParser()
ap.add_argument("jobs", nargs="+")
ap.add_argument("--out", required=True)
ap.add_argument("--size", default="960x540")
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
            order.append((sid, [int(x) for x in fr.split(",")]))
strips = []
for sid, frames in order:
    s = shots[sid]
    labs, chap = EF.labels_for(s, mg), EF.chapter_of(s, mg)
    tiles = []
    for f in frames:
        p = os.path.join(RENDERS, "shots", sid, "sample", f"{f:04d}.png")
        img = Image.open(p).convert("RGB").resize((W, H), Image.LANCZOS).convert("RGBA")
        t = (f - 1) / FPS
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
print(len(strips), "shots ->", a.out)
