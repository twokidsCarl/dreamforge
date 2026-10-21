"""Cut finished-look film from rendered shots: picture, clean subtitles, on-screen labels, VO, music, SFX.

  python3 shared/tools/edit_film.py --segments A0 [--quality sample] [--size 1920x1080] [--out name]
                                    [--no-brand [--tail 2]]

Unlike story_reel (a review board with shot ids and debug overlays), this is the deliverable look:
- picture: each shot's best render (final > sample > preview), shot-relative frame clamped at its end;
  a short dissolve where the storyboard asks for one;
- subtitles: Heiti, #E8ECF4, bottom centre inside the bottom 15 %; on 3D shots and on 2D frames whose
  subtitle zone is not near-black, a translucent bar rgba(7,11,20,0.55) sits under the line (E2 STYLE_REVIEW
  P0-5); plain dark 2D cards keep a soft shadow instead;
- labels: the shot's on-screen overlays (upper right), only on 3D shots (2D graphics carry their own text);
- sound: the VO track (audio/vo/<voice>/vo_track.wav), music + SFX from episodes/<ep>/sound/<seg>.yaml,
  music ducked under the voice (sidechain), integrated loudness normalised to -16 LUFS;
- brand (on by default): brand/eigenlens_logo_locked/sting_open.mp4 before the body, sting_end.mp4 after it,
  both silent (padded with silence so sound stays in sync); the end sting replaces --tail. --no-brand cuts
  the body alone, and only then does --tail apply (stand-alone cuts).
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

from paths import AUDIO, BRAND, EP, RENDERS, timed_shots  # noqa: E402

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


SUB_INK = (232, 236, 244)          # #E8ECF4 (E2 palette INK_1)
SUB_BAR = (7, 11, 20)              # BG-0 #070B14 ...
SUB_BAR_ALPHA = 0.55               # ... at 55 %
SUB_ZONE = 0.85                    # subtitles live in the bottom 15 % of the frame
SUB_DARK_LUMA = 20                 # subtitle zone darker than this (0-255) counts as a plain dark card
ENGINES_2D = ("pillow", "manim")


def needs_bar(img, W, H, engine):
    """3D shots always get the bar; 2D frames only when the subtitle zone is not near-black."""
    if engine not in ENGINES_2D:
        return True
    zone = img.convert("L").crop((int(0.1 * W), int(SUB_ZONE * H), int(0.9 * W), H))
    hist = zone.histogram()
    mean = sum(i * n for i, n in enumerate(hist)) / max(1, sum(hist))
    return mean > SUB_DARK_LUMA


def subtitle(img, text, W, H, a=1.0, bar=True):
    if not text or a <= 0:
        return img
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    size = int(H * 0.043)
    f = font(size)
    cx, cy = W / 2, H * 0.905                       # line centre; bar spans ~0.873H-0.937H, inside the bottom 15 %
    l, t, r, b = d.textbbox((cx, cy), text, font=f, anchor="mm")
    if bar:
        px, py = 0.6 * size, 0.28 * size
        d.rounded_rectangle((l - px, min(t, cy - size / 2) - py, r + px, max(b, cy + size / 2) + py),
                            radius=max(1, round(4 * H / 1080)), fill=(*SUB_BAR, int(255 * SUB_BAR_ALPHA * a)))
    else:
        # plain dark 2D card: a soft dark halo (stroked glyphs, blurred) is enough
        sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(sh).text((cx, cy + H * 0.002), text, font=f, anchor="mm", fill=(0, 0, 0, int(235 * a)),
                                stroke_width=max(2, round(H * 0.004)), stroke_fill=(0, 0, 0, int(235 * a)))
        layer.alpha_composite(sh.filter(ImageFilter.GaussianBlur(H * 0.005)))
    d.text((cx, cy), text, font=f, anchor="mm", fill=(*SUB_INK, int(255 * a)))
    return Image.alpha_composite(img.convert("RGBA"), layer)


def label_for(s, mg):
    if s["id"] in mg or s.get("style") == "type":
        return None
    ovs = [o for o in s.get("overlays") or [] if o.get("kind") != "chapter"]
    if not ovs:
        return None
    tr = str.maketrans("₀₁₂₃₄₅₆₇₈₉⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻", "01234567890123456789+-")
    ovs = [dict(o, text=o["text"].translate(tr)) for o in ovs]
    return {"text": ovs[0]["text"], "sub": " ｜ ".join(o["text"] for o in ovs[1:3]),
            "source": SR.fact_orgs(sorted({f for o in ovs for f in o.get("facts") or []})), "facts": [],
            "pos": "upper_right"}


def picture(shots, W, H, order, tmp, tail=0.0):
    mg = SR.mograph_ids()
    t_film0 = shots[0]["start"]
    n_total = round((shots[-1]["start"] + shots[-1]["duration"] - t_film0) * FPS)
    spans = []
    for s in shots:
        a = round((s["start"] - t_film0) * FPS)
        b = round((s["start"] + s["duration"] - t_film0) * FPS)
        spans.append((s, a, b, best_frames(s["id"], order), label_for(s, mg)))
    cache = {}
    bars = {}                                                        # shot id -> subtitle bar on / off (one decision per shot)

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
        if lab:
            end = min(b, a + 5 * FPS)                                # a label reads in 5 s; then get out of the way
            la = max(0.0, min(1.0, (f - a - 10) / 8, (end - f - 4) / 8))
            if la > 0:
                layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
                draw_label(layer, lab, la, W, H)
                img = Image.alpha_composite(img, layer)
        t = (f - a) / FPS
        cue = next((c for c in s.get("subs") or [] if c["start"] <= t < c["end"]), None)
        if cue:
            ca = min(1.0, (t - cue["start"]) * 8, (cue["end"] - t) * 8)
            if s["id"] not in bars:
                bars[s["id"]] = needs_bar(img, W, H, s.get("engine"))
            img = subtitle(img, cue["text"], W, H, ca, bar=bars[s["id"]])
        img.convert("RGB").save(os.path.join(tmp, f"{f:05d}.png"))
    # optional tail for a stand-alone cut: hold the last frame and fade it to black
    n_tail = round(tail * FPS)
    if n_tail:
        last = Image.open(os.path.join(tmp, f"{n_total - 1:05d}.png")).convert("RGB")
        black = Image.new("RGB", (W, H), (0, 0, 0))
        for i in range(n_tail):
            k = min(1.0, (i + 1) / max(1, n_tail - 6))           # reach black a quarter second before the end
            Image.blend(last, black, k).save(os.path.join(tmp, f"{n_total + i:05d}.png"))
    return n_total / FPS


def sound(shots, seg_files, dur, voice, out_wav, tail=0.0):
    t0 = shots[0]["start"]
    start_of = {s["id"]: s["start"] - t0 for s in shots}
    inputs, filters, mixes = [], [], []
    vo = os.path.join(AUDIO, "vo", voice, "vo_track.wav")
    silent = not os.path.exists(vo)
    if silent:                             # 配音还没出：整段静音，画面预览照常（不混配乐和音效）
        print(f"[edit_film] 警告：{vo} 不存在，输出静音轨", file=sys.stderr)
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "lavfi", "-t", f"{dur:.3f}", "-i",
                        "anullsrc=r=48000:cl=stereo", out_wav], check=True)
        return
    inputs += ["-ss", f"{t0:.3f}", "-t", f"{dur:.3f}", "-i", vo]
    total = dur + tail                                        # the narration stops at dur; music and effects ring on
    filters.append(f"[0:a]aresample=48000,pan=stereo|c0=c0|c1=c0,apad=whole_dur={total:.3f},"
                   "asplit=3[vo][vokey][vokey2]")
    n = 1
    music_parts, sfx_parts = [], []
    for sf in seg_files:
        cfg = yaml.safe_load(open(sf, encoding="utf-8"))
        for m in cfg.get("music") or []:
            inputs += ["-i", os.path.join(AUDIO, "eleven", m["file"])]
            d = int(m.get("at", 0) * 1000)
            fo = m.get("fade_out", 2.0)
            filters.append(f"[{n}:a]aresample=48000,volume={m.get('gain', -6)}dB,adelay={d}|{d},"
                           f"afade=t=out:st={max(0, total - fo):.2f}:d={fo}[m{n}]")
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
    if music_parts:
        filters.append("".join(music_parts) + f"amix=inputs={len(music_parts)}:normalize=0[mus]")
        filters.append("[mus][vokey]sidechaincompress=threshold=0.03:ratio=6:attack=40:release=500[musd]")
        mixes.append("[musd]")
    if sfx_parts:
        filters.append("".join(sfx_parts) + f"amix=inputs={len(sfx_parts)}:normalize=0[fx]")
        # effects step back a little under the words (gentler than the music), so no word is masked
        filters.append("[fx][vokey2]sidechaincompress=threshold=0.04:ratio=3:attack=20:release=350[fxd]")
        mixes.append("[fxd]")
    end_fade = f"afade=t=out:st={dur:.3f}:d={tail:.3f}," if tail else ""
    filters.append("[vo]" + "".join(mixes) + f"amix=inputs={1 + len(mixes)}:normalize=0,"
                   f"atrim=0:{total:.3f},{end_fade}loudnorm=I=-16:TP=-1.5:LRA=11[out]")
    cmd = ["ffmpeg", "-loglevel", "error", "-y", *inputs, "-filter_complex", ";".join(filters), "-map", "[out]",
           "-ar", "48000", out_wav]
    subprocess.run(cmd, check=True)


def probe(path, entries, streams=None):
    sel = ["-select_streams", streams] if streams else []
    out = subprocess.run(["ffprobe", "-v", "error", *sel, "-show_entries", entries, "-of", "csv=p=0", path],
                         check=True, capture_output=True, text=True).stdout
    return [v.strip(",") for v in out.split()]


def apply_brand_stings(body_mp4, out_mp4, brand_dir=BRAND):
    """open sting + body + end sting -> out_mp4, at the body's frame size. The stings are silent: each gets
    a silence pad of its own length, so the body's mix (VO / music / loudness) is untouched, only delayed.
    Returns (open, body, end) durations in seconds."""
    op, end = (os.path.join(brand_dir, f) for f in ("sting_open.mp4", "sting_end.mp4"))
    for p in (op, end):
        if not os.path.exists(p):
            raise FileNotFoundError(f"[edit_film] 品牌 sting 不存在：{p}")
    W, H = probe(body_mp4, "stream=width,height", "v:0")[0].split(",")
    d_op, d_body, d_end = (float(probe(p, "format=duration")[0]) for p in (op, body_mp4, end))
    has_audio = bool(probe(body_mp4, "stream=index", "a"))
    sil = lambda d: ["-f", "lavfi", "-t", f"{d:.3f}", "-i", "anullsrc=r=48000:cl=stereo"]
    inputs = ["-i", op, "-i", body_mp4, "-i", end, *sil(d_op), *sil(d_end)]
    if not has_audio:                       # body 没有音轨：整段补静音
        print(f"[edit_film] 警告：{body_mp4} 没有音轨，用静音代替", file=sys.stderr)
        inputs += sil(d_body)
    va = f"fps={FPS},scale={W}:{H}:flags=lanczos,setsar=1,format=yuv420p"
    aa = "aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo"
    filters = [f"[{i}:v]{va}[v{i}]" for i in range(3)]
    filters += [f"[3:a]{aa}[a0]", f"[{1 if has_audio else 5}:a]{aa},apad,atrim=0:{d_body:.3f}[a1]", f"[4:a]{aa}[a2]",
                "[v0][a0][v1][a1][v2][a2]concat=n=3:v=1:a=1[v][a]"]
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", *inputs, "-filter_complex", ";".join(filters),
                    "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-crf", "16", "-preset", "slow",
                    "-pix_fmt", "yuv420p", "-r", str(FPS), "-c:a", "aac", "-b:a", "256k",
                    "-movflags", "+faststart", out_mp4], check=True)
    return d_op, d_body, d_end


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--segments", required=True)
    ap.add_argument("--quality", default="final,sample,preview")
    ap.add_argument("--size", default="1920x1080")
    ap.add_argument("--voice", default="Andre")
    ap.add_argument("--out")
    ap.add_argument("--tail", type=float, default=0.0,
                    help="seconds after the last shot: picture fades to black, music and effects decay "
                         "(stand-alone cuts; only with --no-brand)")
    ap.add_argument("--brand", action=argparse.BooleanOptionalAction, default=True,
                    help="open sting before, end sting after (default on; --no-brand for the body alone)")
    a = ap.parse_args()
    if a.brand and a.tail:                 # 片尾 sting 取代淡出黑场
        print(f"[edit_film] 警告：品牌开启时忽略 --tail {a.tail}（片尾 sting 取代淡出）；独立短片用 --no-brand --tail",
              file=sys.stderr)
        a.tail = 0.0
    segs = a.segments.split(",")
    W, H = (int(v) for v in a.size.split("x"))
    shots = timed_shots(segs)
    out_dir = os.path.join(RENDERS, "edit")
    tmp = os.path.join(out_dir, "tmp_" + "_".join(segs))
    shutil.rmtree(tmp, ignore_errors=True)
    os.makedirs(tmp)
    dur = picture(shots, W, H, a.quality.split(","), tmp, a.tail)
    wav = os.path.join(tmp, "mix.wav")
    seg_files = [os.path.join(EP, "sound", f"{s.lower()}.yaml") for s in segs]
    sound(shots, [p for p in seg_files if os.path.exists(p)], dur, a.voice, wav, a.tail)
    name = a.out or "_".join(segs)
    mp4 = os.path.join(out_dir, f"{name}.mp4")
    body = os.path.join(tmp, "body.mp4") if a.brand else mp4
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-framerate", str(FPS), "-i", os.path.join(tmp, "%05d.png"),
                    "-i", wav, "-c:v", "libx264", "-crf", "16", "-preset", "slow", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "256k", "-shortest", "-movflags", "+faststart", body], check=True)
    if a.brand:
        d_op, d_body, d_end = apply_brand_stings(body, mp4)
        shutil.rmtree(tmp)
        print(mp4, f"{d_op + d_body + d_end:.1f}s (open {d_op:.1f} + body {d_body:.1f} + end {d_end:.1f})")
        return
    shutil.rmtree(tmp)
    print(mp4, f"{dur + a.tail:.1f}s")


if __name__ == "__main__":
    main()
