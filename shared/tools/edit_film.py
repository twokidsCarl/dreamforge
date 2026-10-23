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
from richtext import draw_text, text_bbox  # noqa: E402
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
    """Every subtitle sits on a dark bar (SCALE_E1 v2 §4; R1 review: 2D frames had none). The old luma test is kept
    only for EIGENLENS_SUB_BAR=auto."""
    if os.environ.get("EIGENLENS_SUB_BAR", "always") != "auto" or engine not in ENGINES_2D:
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
    l, t, r, b = text_bbox(d, (cx, cy), text, f, anchor="mm")
    if bar:
        px, py = 0.6 * size, 0.28 * size
        d.rounded_rectangle((l - px, min(t, cy - size / 2) - py, r + px, max(b, cy + size / 2) + py),
                            radius=max(1, round(4 * H / 1080)), fill=(*SUB_BAR, int(255 * SUB_BAR_ALPHA * a)))
    else:
        # plain dark 2D card: a soft dark halo (stroked glyphs, blurred) is enough
        sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        draw_text(ImageDraw.Draw(sh), (cx, cy + H * 0.002), text, f, anchor="mm", fill=(0, 0, 0, int(235 * a)),
                  stroke_width=max(2, round(H * 0.004)), stroke_fill=(0, 0, 0, int(235 * a)))
        layer.alpha_composite(sh.filter(ImageFilter.GaussianBlur(H * 0.005)))
    draw_text(d, (cx, cy), text, f, anchor="mm", fill=(*SUB_INK, int(255 * a)))
    return Image.alpha_composite(img.convert("RGBA"), layer)


def _lab(texts, facts, sub_extra=()):
    # sub/superscripts (Sn⁸⁺, H₂) are kept: overlay_labels typesets them via richtext (smaller raised/lowered glyphs)
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
    ovs = [o for o in s.get("overlays") or [] if o.get("kind") not in ("chapter", "page")]
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


def page_of(s):
    return next((o for o in s.get("overlays") or [] if o.get("kind") == "page"), None)


def draw_page(img, pg, t, W, H):
    """A 'textbook page' inserted over a 3D shot (left third): old title, struck through at `strike`, new title written
    at `write`, a source line. Overlay keys: kind: page, at, strike, write, old, new, note."""
    a = max(0.0, min(1.0, (t - pg["at"]) / 0.4))
    if a <= 0:
        return img
    k = H / 1080
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    x0, y0, x1, y1 = 110 * k, 300 * k, 760 * k, 760 * k
    d.rounded_rectangle([x0, y0, x1, y1], radius=10 * k, fill=(236, 232, 222, int(235 * a)))
    for yy in range(int(y0 + 60 * k), int(y1 - 40 * k), int(34 * k)):          # faint ruled lines
        d.line([(x0 + 30 * k, yy), (x1 - 30 * k, yy)], fill=(200, 196, 186, int(150 * a)), width=max(1, int(k)))
    f1, f2, f3 = font(int(40 * k)), font(int(44 * k)), font(int(26 * k))
    d.text((x0 + 40 * k, y0 + 60 * k), pg["old"], font=f1, fill=(70, 70, 76, int(255 * a)))
    st = max(0.0, min(1.0, (t - pg["strike"]) / 0.5))
    if st > 0:
        tw = d.textlength(pg["old"], font=f1)
        yy = y0 + 84 * k
        d.line([(x0 + 36 * k, yy), (x0 + 36 * k + (tw + 8 * k) * st, yy)], fill=(200, 40, 40, int(255 * a)), width=int(4 * k))
    wr = max(0.0, min(1.0, (t - pg["write"]) / 0.6))
    if wr > 0:
        txt = pg["new"][:max(1, int(len(pg["new"]) * wr))]
        d.text((x0 + 40 * k, y0 + 190 * k), txt, font=f2, fill=(92, 50, 200, int(255 * a)))
    d.text((x0 + 40 * k, y1 - 70 * k), pg.get("note", ""), font=f3, fill=(110, 110, 118, int(255 * a)))
    return Image.alpha_composite(img.convert("RGBA"), layer)


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


def picture(shots, W, H, order, tmp, tail=0.0):
    mg = SR.mograph_ids()
    t_film0 = shots[0]["start"]
    n_total = round((shots[-1]["start"] + shots[-1]["duration"] - t_film0) * FPS)
    spans = []
    for s in shots:
        a = round((s["start"] - t_film0) * FPS)
        b = round((s["start"] + s["duration"] - t_film0) * FPS)
        spans.append((s, a, b, best_frames(s["id"], order), (labels_for(s, mg), chapter_of(s, mg), page_of(s))))
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
        labs, chap, pg = lab
        t = (f - a) / FPS
        if pg:
            img = draw_page(img, pg, t, W, H)
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
    keys = (["[vokey]"] if music_parts else []) + (["[vokey2]"] if sfx_parts else [])
    filters[0] = (f"[0:a]aresample=48000,pan=stereo|c0=c0|c1=c0,apad=whole_dur={total:.3f}" +
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


CTA_TEXT = os.path.join(EP, "brand", "endcard_cta_text.png")   # per-episode CTA lines (eigenlens.ai), optional
CTA_HOLD, CTA_SLIDE, CTA_LIFT = 6.0, 0.75, 0.10                # seconds held, slide-up time, lift (share of height)


def cta_tail(out_mp4, brand_dir=BRAND, text_png=CTA_TEXT):
    """After sting_end lands on the locked end card: the card slides up CTA_LIFT and the CTA lines fade in, then hold.
    Silent, 1920x1080 @ FPS. Returns out_mp4, or None when the episode has no CTA text."""
    if not os.path.exists(text_png):
        return None
    import tempfile
    base = Image.open(os.path.join(brand_dir, "endcard_16x9.png")).convert("RGB").resize((1920, 1080))
    txt = Image.open(text_png).convert("RGBA").resize((1920, 1080))
    bg = base.getpixel((3, 3))
    n, ns = round(CTA_HOLD * FPS), round(CTA_SLIDE * FPS)
    with tempfile.TemporaryDirectory() as tmp:
        for i in range(n):
            k = min(1.0, i / ns)
            k = k * k * (3 - 2 * k)                                     # smoothstep
            img = Image.new("RGB", base.size, bg)
            img.paste(base, (0, round(-CTA_LIFT * 1080 * k)))
            ta = max(0.0, min(1.0, (i - ns * 0.6) / ns))
            if ta > 0:
                t = txt.copy()
                t.putalpha(t.getchannel("A").point(lambda v: int(v * ta)))
                img = Image.alpha_composite(img.convert("RGBA"), t).convert("RGB")
            img.save(os.path.join(tmp, f"{i:05d}.png"))
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-framerate", str(FPS), "-i", os.path.join(tmp, "%05d.png"),
                        "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", out_mp4], check=True)
    return out_mp4


def apply_brand_stings(body_mp4, out_mp4, brand_dir=BRAND):
    """open sting + body + end sting (+ the episode's CTA tail, if any) -> out_mp4, at the body's frame size. The
    stings are silent: each gets a silence pad of its own length, so the body's mix (VO / music / loudness) is
    untouched, only delayed. Returns (open, body, end) durations in seconds (end includes the CTA tail)."""
    op, end = (os.path.join(brand_dir, f) for f in ("sting_open.mp4", "sting_end.mp4"))
    for p in (op, end):
        if not os.path.exists(p):
            raise FileNotFoundError(f"[edit_film] 品牌 sting 不存在：{p}")
    tail = cta_tail(os.path.splitext(out_mp4)[0] + "_cta_tail.mp4", brand_dir)
    if tail:                                     # sting_end + CTA tail become one silent end piece
        joined = os.path.splitext(out_mp4)[0] + "_end_cta.mp4"
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", end, "-i", tail, "-filter_complex",
                        f"[0:v]fps={FPS},scale=1920:1080,setsar=1,format=yuv420p[a];"
                        f"[1:v]fps={FPS},scale=1920:1080,setsar=1,format=yuv420p[b];[a][b]concat=n=2:v=1:a=0[v]",
                        "-map", "[v]", "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", joined], check=True)
        end = joined
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
