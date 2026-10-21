"""Cut finished-look film from rendered shots: picture, clean subtitles, on-screen labels, VO, music, SFX.

  python3 shared/tools/edit_film.py --segments A0 [--quality sample] [--size 1920x1080] [--out name]

Unlike story_reel (a review board with shot ids and debug overlays), this is the deliverable look:
- picture: each shot's best render (final > sample > preview), shot-relative frame clamped at its end;
  a short dissolve where the storyboard asks for one;
- subtitles: Heiti, white with a soft shadow, bottom centre, no box;
- labels: the shot's on-screen overlays (upper right), only on 3D shots (2D graphics carry their own text);
- sound: the VO track (audio/vo/<voice>/vo_track.wav), music + SFX from episodes/<ep>/sound/<seg>.yaml,
  music ducked under the voice (sidechain), integrated loudness normalised to -16 LUFS.
"""
import argparse
import os
import shutil
import subprocess
import sys

import yaml
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(__file__))
from overlay_labels import draw_label, font  # noqa: E402
import story_reel as SR  # noqa: E402

from paths import AUDIO, EP, RENDERS  # noqa: E402

FPS = 24
DISSOLVE = 8


def best_frames(sid, order):
    for q in order:
        d = os.path.join(RENDERS, "shots", sid, q)
        if os.path.isdir(d):
            fr = sorted(f for f in os.listdir(d) if f.endswith(".png"))
            if fr:
                return [os.path.join(d, f) for f in fr]
    return []


def subtitle(img, text, W, H, a=1.0):
    if not text or a <= 0:
        return img
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    f = font(int(H * 0.043))
    tw = d.textlength(text, font=f)
    x, y = (W - tw) / 2, H * 0.865
    # a soft dark halo (stroked glyphs, blurred) keeps white type readable on pale studio shots too
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sh).text((x, y + H * 0.002), text, font=f, fill=(0, 0, 0, int(235 * a)),
                            stroke_width=max(2, round(H * 0.004)), stroke_fill=(0, 0, 0, int(235 * a)))
    layer.alpha_composite(sh.filter(ImageFilter.GaussianBlur(H * 0.005)))
    layer.alpha_composite(sh.filter(ImageFilter.GaussianBlur(H * 0.0015)))
    d.text((x, y), text, font=f, fill=(255, 255, 255, int(255 * a)))
    return Image.alpha_composite(img.convert("RGBA"), layer)


def _lab(texts, facts, sub_extra=()):
    tr = str.maketrans("₀₁₂₃₄₅₆₇₈₉⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻", "01234567890123456789+-")
    texts = [t.translate(tr) for t in texts]
    rest = list(sub_extra) + texts[1:]
    rest = (["示意"] if "示意" in rest else []) + [r for r in rest if r != "示意"]   # 示意 is never dropped
    return {"text": texts[0], "sub": " ｜ ".join(rest[:2]), "source": SR.fact_orgs(sorted(set(facts))), "facts": [],
            "pos": "upper_right"}


def labels_for(s, mg):
    """[(start_s, end_s, label)] for a 3D shot. Overlays without `at:` share one label from 0.4 s (or after the chapter
    card); an overlay with `at: <s>` gets its own label from that second, until the next one or 5 s, so long takes
    can follow the narration."""
    if s["id"] in mg or s.get("style") == "type":
        return []
    dur = s["duration"]
    ovs = [o for o in s.get("overlays") or [] if o.get("kind") != "chapter"]
    timed = sorted((o for o in ovs if o.get("at") is not None), key=lambda o: o["at"])
    plain = [o for o in ovs if o.get("at") is None]
    out = []
    t0 = 3.0 if chapter_of(s, mg) else 10 / FPS
    if plain:
        end = min(dur, t0 + 5.0, timed[0]["at"] if timed and timed[0]["at"] > t0 + 1.5 else dur)
        out.append((t0, end, _lab([o["text"] for o in plain], [f for o in plain for f in o.get("facts") or []])))
    for k, o in enumerate(timed):
        nxt = timed[k + 1]["at"] if k + 1 < len(timed) else dur
        out.append((o["at"], min(dur, nxt, o["at"] + 5.0), _lab([o["text"]], o.get("facts") or [])))
    return out


def chapter_of(s, mg):
    """(title, subtitle) of a chapter overlay on a 3D shot (2D graphics draw their own chapter cards)."""
    if s["id"] in mg:
        return None
    for o in s.get("overlays") or []:
        if o.get("kind") == "chapter":
            t = o["text"].split("·", 1)[-1].strip()
            title, _, sub = t.partition("：")
            return title.strip(), sub.strip()
    return None


def draw_chapter(img, title, sub, a, W, H):
    """Chapter card over a 3D picture, lower left on a soft dark gradient: 章节 / title / subtitle / a growing rule."""
    k = H / 1080
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    grad = Image.linear_gradient("L").rotate(90, expand=True).resize((W, H))      # dark at the left
    shade = Image.new("RGBA", (W, H), (4, 5, 9, 0))
    shade.putalpha(grad.point(lambda v: int(max(0.0, (255 - v) / 255 - 0.35) / 0.65 * 230 * a)))   # left 2/3
    layer.alpha_composite(shade)
    d = ImageDraw.Draw(layer)
    d.text((160 * k, 470 * k), "章节", font=font(int(34 * k)), fill=(150, 158, 182, int(255 * a)))
    ft = font(int(96 * k))
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(glow).text((160 * k, 520 * k), title, font=ft, fill=(164, 128, 255, int(160 * a)))
    layer.alpha_composite(glow.filter(ImageFilter.GaussianBlur(14 * k)))
    d.text((160 * k, 520 * k), title, font=ft, fill=(236, 238, 244, int(255 * a)))
    tw = d.textlength(title, font=ft)
    d.rectangle([160 * k, 640 * k, 160 * k + tw * a, 643 * k], fill=(164, 128, 255, int(255 * a)))
    if sub:
        d.text((164 * k, 662 * k), sub, font=font(int(34 * k)), fill=(190, 170, 255, int(255 * a)))
    return Image.alpha_composite(img.convert("RGBA"), layer)


def picture(shots, W, H, order, tmp):
    mg = SR.mograph_ids()
    t_film0 = shots[0]["start"]
    n_total = round((shots[-1]["start"] + shots[-1]["duration"] - t_film0) * FPS)
    spans = []
    for s in shots:
        a = round((s["start"] - t_film0) * FPS)
        b = round((s["start"] + s["duration"] - t_film0) * FPS)
        spans.append((s, a, b, best_frames(s["id"], order), (labels_for(s, mg), chapter_of(s, mg))))
    cache = {}

    def frame_of(span, f):
        s, a, b, fr, lab = span
        if not fr:
            return Image.new("RGB", (W, H), (0, 0, 0))
        p = fr[min(len(fr) - 1, f - a)]
        if p not in cache:
            if len(cache) > 64:
                cache.clear()
            cache[p] = Image.open(p).convert("RGB").resize((W, H), Image.LANCZOS)
        return cache[p]

    for f in range(n_total):
        k = max(i for i, sp in enumerate(spans) if sp[1] <= f)
        sp = spans[k]
        img = frame_of(sp, f)
        s, a, b, fr, lab = sp
        if k > 0 and s.get("transition_in") in ("dissolve", "fade") and f - a < DISSOLVE:
            prev = frame_of(spans[k - 1], f)
            img = Image.blend(prev, img, (f - a + 1) / (DISSOLVE + 1))
        img = img.convert("RGBA")
        labs, chap = lab
        t = (f - a) / FPS
        if chap:                                                     # chapter card 0.2-2.8 s, 0.5 s fades
            ca = max(0.0, min(1.0, (t - 0.2) / 0.5, (2.8 - t) / 0.5))
            if ca > 0:
                img = draw_chapter(img, chap[0], chap[1], ca, W, H)
        for t0, t1, lb in labs:                                      # a label reads in 5 s; then gets out of the way
            la = max(0.0, min(1.0, (t - t0) / 0.33, (t1 - t - 0.17) / 0.33))
            if la > 0:
                layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
                draw_label(layer, lb, la, W, H)
                img = Image.alpha_composite(img, layer)
        cue = next((c for c in s.get("subs") or [] if c["start"] <= t < c["end"]), None)
        if cue:
            ca = min(1.0, (t - cue["start"]) * 8, (cue["end"] - t) * 8)
            img = subtitle(img, cue["text"], W, H, ca)
        img.convert("RGB").save(os.path.join(tmp, f"{f:05d}.png"))
    return n_total / FPS


def sound(shots, seg_files, dur, voice, out_wav):
    t0 = shots[0]["start"]
    start_of = {s["id"]: s["start"] - t0 for s in shots}
    inputs, filters, mixes = [], [], []
    vo = os.path.join(AUDIO, "vo", voice, "vo_track.wav")
    inputs += ["-ss", f"{t0:.3f}", "-t", f"{dur:.3f}", "-i", vo]
    filters.append(None)                     # the VO split, filled in once we know which keys are needed
    n = 1
    music_parts, sfx_parts = [], []
    for sf in seg_files:
        cfg = yaml.safe_load(open(sf, encoding="utf-8"))
        for m in cfg.get("music") or []:
            inputs += ["-i", os.path.join(AUDIO, "eleven", m["file"])]
            d = int(m.get("at", 0) * 1000)
            fo = m.get("fade_out", 2.0)
            filters.append(f"[{n}:a]aresample=48000,volume={m.get('gain', -6)}dB,adelay={d}|{d},"
                           f"afade=t=out:st={max(0, dur - fo):.2f}:d={fo}[m{n}]")
            music_parts.append(f"[m{n}]")
            n += 1
        import eleven
        for c in cfg.get("cues") or []:
            if c["shot"] not in start_of:
                continue
            p = eleven.sfx(c["text"], c.get("len"))
            inputs += ["-i", p]
            d = int((start_of[c["shot"]] + c["at"]) * 1000)
            filters.append(f"[{n}:a]aresample=48000,volume={c.get('gain', -14)}dB,adelay={d}|{d}[s{n}]")
            sfx_parts.append(f"[s{n}]")
            n += 1
    keys = (["[vokey]"] if music_parts else []) + (["[vokey2]"] if sfx_parts else [])
    filters[0] = ("[0:a]aresample=48000,pan=stereo|c0=c0|c1=c0" +
                  (f",asplit={1 + len(keys)}[vo]{''.join(keys)}" if keys else "[vo]"))   # no unconnected pads
    if music_parts:
        filters.append("".join(music_parts) + f"amix=inputs={len(music_parts)}:normalize=0[mus]")
        filters.append("[mus][vokey]sidechaincompress=threshold=0.03:ratio=6:attack=40:release=500[musd]")
        mixes.append("[musd]")
    if sfx_parts:
        filters.append("".join(sfx_parts) + f"amix=inputs={len(sfx_parts)}:normalize=0[fx]")
        # effects step back a little under the words (gentler than the music), so no word is masked
        filters.append("[fx][vokey2]sidechaincompress=threshold=0.04:ratio=3:attack=20:release=350[fxd]")
        mixes.append("[fxd]")
    filters.append("[vo]" + "".join(mixes) + f"amix=inputs={1 + len(mixes)}:normalize=0,"
                   f"atrim=0:{dur:.3f},loudnorm=I=-16:TP=-2.0:LRA=11[out]")
    cmd = ["ffmpeg", "-loglevel", "error", "-y", *inputs, "-filter_complex", ";".join(filters), "-map", "[out]",
           "-ar", "48000", out_wav]
    subprocess.run(cmd, check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--segments", required=True)
    ap.add_argument("--quality", default="final,sample,preview")
    ap.add_argument("--size", default="1920x1080")
    ap.add_argument("--voice", default="Andre")
    ap.add_argument("--out")
    a = ap.parse_args()
    segs = a.segments.split(",")
    W, H = (int(v) for v in a.size.split("x"))
    shots = [s for s in yaml.safe_load(open(os.path.join(EP, "storyboard/storyboard.timed.yaml"),
                                            encoding="utf-8"))["shots"] if s["segment"] in segs]
    out_dir = os.path.join(RENDERS, "edit")
    tmp = os.path.join(out_dir, "tmp_" + "_".join(segs))
    shutil.rmtree(tmp, ignore_errors=True)
    os.makedirs(tmp)
    dur = picture(shots, W, H, a.quality.split(","), tmp)
    wav = os.path.join(tmp, "mix.wav")
    seg_files = [os.path.join(EP, "sound", f"{s.lower()}.yaml") for s in segs]
    sound(shots, [p for p in seg_files if os.path.exists(p)], dur, a.voice, wav)
    name = a.out or "_".join(segs)
    mp4 = os.path.join(out_dir, f"{name}.mp4")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-framerate", str(FPS), "-i", os.path.join(tmp, "%05d.png"),
                    "-i", wav, "-c:v", "libx264", "-crf", "16", "-preset", "slow", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "256k", "-shortest", "-movflags", "+faststart", mp4], check=True)
    shutil.rmtree(tmp)
    print(mp4, f"{dur:.1f}s")


if __name__ == "__main__":
    main()
