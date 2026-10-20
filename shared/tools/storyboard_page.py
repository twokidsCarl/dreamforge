"""Render the storyboard as a single self-contained HTML review page.

  python3 tools/storyboard_page.py OUT.html

Reads episodes/<episode>/storyboard/storyboard.yaml, the script titles, and
storyboard/page.yaml. Legend questions, sample frames, and the ref note default
to the lithography wording; an episode overrides them with style_questions
(no trailing question mark), sample_frames, and ref_note. Images are embedded
as JPEG data URIs.
"""
import base64
import html
import io
import os
import sys

import yaml
from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
from lint_script import parse  # noqa: E402
from zh_terms import ENGINES, TRANSITIONS, camera_zh, fx_zh  # noqa: E402

from paths import AUDIO, EP, REPO, RENDERS, SHARED  # noqa: E402,F401
RENDERS = RENDERS

STYLE_ZH = {"photoreal": "真实渲染", "xray": "透明剖视", "blueprint": "蓝图", "energy": "能量图",
            "infographic": "平面信息图", "clay": "白模", "sem": "显微成像", "hud": "HUD 遥测",
            "type": "动态排版", "documentary": "纪实氛围"}
STYLE_Q = {"photoreal": "它真实存在、长什么样", "xray": "机器里面怎么排布", "blueprint": "为什么这样设计",
           "energy": "看不见的物理怎么流动", "infographic": "多大、多少、比什么强", "clay": "怎么组装、怎么运动",
           "sem": "纳米尺度长什么样", "hud": "控制与测量怎么实时发生", "type": "章节与情绪节点",
           "documentary": "它在真实世界的哪里"}

FRAMES = [
    ("style_test/cycles/CamStyle_photoreal/0230.png", "真实渲染", "同一场景 · 第 230 帧"),
    ("style_test/cycles/CamStyle_xray/0230.png", "透明剖视", "同一场景 · 第 230 帧"),
    ("style_test/eevee/CamStyle_blueprint/0230.png", "蓝图", "同一场景 · 第 230 帧"),
    ("style_test/eevee/CamStyle_energy/0230.png", "能量图", "同一场景 · 第 230 帧"),
    ("sample_b1/edit/0075.png", "B1 样片", "喷嘴微距 · 锡滴 25 μm"),
    ("sample_b1/edit/0140.png", "B1 样片", "预脉冲把锡滴压扁"),
    ("sample_b1/edit/0226.png", "B1 样片", "主脉冲闪白"),
    ("sample_b1/edit/0250.png", "B1 样片", "等离子体与发光碎屑"),
]


def page_meta():
    """Page chrome (title, lede, accent colors) lives in the episode, not in this tool.

    The tool used to bake the EUV lithography title and palette into every episode.
    Missing metadata is an error: never fall back to another episode's chrome.
    """
    path = os.path.join(EP, "storyboard", "page.yaml")
    if not os.path.isfile(path):
        raise SystemExit(
            f"缺少 {path}。分镜总览的标题、简介和强调色必须写在当期 storyboard/page.yaml，"
            "不能套用其他期的页面外壳。"
        )
    data = yaml.safe_load(open(path, encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit(f"{path} 必须是映射")
    required = ("document_title", "kicker", "title", "lede", "frames_label", "rules", "accents")
    missing = [key for key in required if not data.get(key)]
    if missing:
        raise SystemExit(f"{path} 缺少 {', '.join(missing)}")
    return data


def style_questions(meta):
    """Legend prompts. Omit style_questions to keep the original wording."""
    override = meta.get("style_questions") or {}
    if not isinstance(override, dict):
        raise SystemExit("storyboard/page.yaml 的 style_questions 必须是映射")
    unknown = [key for key in override if key not in STYLE_Q]
    if unknown:
        raise SystemExit(f"style_questions 有未知画面语言：{', '.join(unknown)}")
    merged = dict(STYLE_Q)
    for key, value in override.items():
        if not isinstance(value, str) or not value.strip():
            raise SystemExit(f"style_questions.{key} 必须是非空字符串")
        if value.endswith("？") or value.endswith("?"):
            raise SystemExit(f"style_questions.{key} 不要自带问号，页面会加上")
        merged[key] = value
    return merged


def sample_frames(meta):
    """Omit sample_frames to keep the built-in style-board list."""
    if "sample_frames" not in meta:
        return list(FRAMES)
    raw = meta.get("sample_frames") or []
    if not isinstance(raw, list):
        raise SystemExit("sample_frames 必须是列表")
    frames = []
    for item in raw:
        if not isinstance(item, dict):
            raise SystemExit("sample_frames 的每一项必须是映射（path、label、caption）")
        path, label, caption = item.get("path"), item.get("label"), item.get("caption")
        if not all(isinstance(x, str) and x.strip() for x in (path, label, caption)):
            raise SystemExit("sample_frames 的 path、label、caption 都必须是非空字符串")
        frames.append((path, label, caption))
    return frames


def rules_html(items):
    if not isinstance(items, list) or not all(isinstance(item, str) and item.strip() for item in items):
        raise SystemExit("storyboard/page.yaml 的 rules 必须是非空字符串列表")
    return "\n".join(f"        <li>{esc(item)}</li>" for item in items)


def esc(x):
    return html.escape(str(x), quote=True)


def tc(t):
    return f"{int(t // 60):02d}:{t % 60:04.1f}"


def jpeg_uri(path, width=720):
    im = Image.open(path).convert("RGB")
    im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=74, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def main():
    out = sys.argv[1]
    meta = page_meta()
    acts = meta.get("acts") or {}
    if not isinstance(acts, dict):
        raise SystemExit("storyboard/page.yaml 的 acts 必须是映射")
    shots = yaml.safe_load(open(os.path.join(EP, "storyboard/storyboard.yaml"),
                                encoding="utf-8"))["shots"]
    titles = {s["id"]: s["title"] for s in parse(os.path.join(EP, "script/script_zh.md"))}
    total = sum(s["duration"] for s in shots)
    counts = {}
    for s in shots:
        counts[s["style"]] = counts.get(s["style"], 0) + 1

    # timeline strip
    t, strip, segs = 0.0, [], []
    for s in shots:
        s["_t0"] = t
        t += s["duration"]
        strip.append(f'<a class="tick st-{s["style"]}" href="#{esc(s["id"])}" '
                     f'style="flex-grow:{s["duration"]:.2f}" title="{esc(s["id"])} · {STYLE_ZH[s["style"]]} · '
                     f'{s["duration"]:.1f}s"></a>')
    order = []
    for s in shots:
        if s["segment"] not in order:
            order.append(s["segment"])
    seg_marks = []
    for seg in order:
        ss = [x for x in shots if x["segment"] == seg]
        d = sum(x["duration"] for x in ss)
        seg_marks.append(f'<a class="segmark" href="#seg-{seg}" style="flex-grow:{d:.1f}">'
                         f'<span>{seg}</span></a>')

    legend = "".join(
        f'<button class="chip st-{k}" type="button" data-style="{k}" aria-pressed="false" id="f-{k}">'
        f'<span class="dot"></span>{STYLE_ZH[k]}<span class="n">{counts.get(k, 0)}</span></button>'
        for k in STYLE_ZH)
    questions = style_questions(meta)
    qrows = "".join(f'<li><span class="sw st-{k}"></span><b>{STYLE_ZH[k]}</b>{questions[k]}？</li>'
                    for k in STYLE_ZH)

    frames = []
    for rel, label, cap in sample_frames(meta):
        p = os.path.join(RENDERS, rel)
        if os.path.exists(p):
            frames.append(f'<figure><img src="{jpeg_uri(p)}" alt="{esc(label)}：{esc(cap)}" loading="lazy">'
                          f'<figcaption><b>{esc(label)}</b>{esc(cap)}</figcaption></figure>')

    body = []
    for seg in order:
        ss = [x for x in shots if x["segment"] == seg]
        d = sum(x["duration"] for x in ss)
        act = f'<p class="act">{esc(acts[seg])}</p>' if seg in acts else ""
        body.append(f'<section class="seg" id="seg-{seg}">{act}<header class="seghead">'
                    f'<h2><span class="segid">{seg}</span>{esc(titles.get(seg, ""))}</h2>'
                    f'<p class="segmeta">{len(ss)} 个镜头 · {d:.0f} 秒 · 起于 {tc(ss[0]["_t0"])}</p></header>')
        for s in ss:
            vo = "".join(f"<p>{esc(v)}</p>" for v in s.get("vo") or []) or '<p class="mute">（纯画面，无旁白）</p>'
            ovs = "".join(
                f'<li>{esc(o.get("text", ""))}'
                + (f'<span class="fid">{esc("、".join(o.get("facts") or []))}</span>' if o.get("facts") else "")
                + "</li>" for o in s.get("overlays") or [])
            cam = s.get("camera") or {}
            cam_txt = " · ".join(str(x) for x in [camera_zh(cam.get("move")),
                                                    f'{cam["lens_mm"]} 毫米焦距' if cam.get("lens_mm") else None,
                                                    f'光圈 f/{cam["fstop"]}' if cam.get("fstop") else None] if x)
            extra = "".join(f"<dt>{k}</dt><dd>{esc(v)}</dd>" for k, v in [
                ("机位", cam_txt + (f'；{cam["notes"]}' if cam.get("notes") else "")),
                ("特效", "、".join(fx_zh(f) for f in s.get("fx") or [])),
                ("声音", "、".join(s.get("sfx") or [])),
                ("渲染", ENGINES.get(s.get("engine", ""), s.get("engine", ""))),
                ("复用", (meta.get("ref_note") or "沿用 B1 样片机位 ") + s["ref"].split(":")[-1]
                 if s.get("ref") else ""),
            ] if v)
            body.append(
                f'<article class="shot" id="{esc(s["id"])}" data-style="{s["style"]}">'
                f'<div class="meta"><span class="sid">{esc(s["id"])}</span>'
                f'<span class="tc">{tc(s["_t0"])}</span><span class="dur">{s["duration"]:.1f}s</span>'
                f'<span class="chip sm st-{s["style"]}"><span class="dot"></span>{STYLE_ZH[s["style"]]}</span>'
                f'<span class="tr">转场：{esc(TRANSITIONS.get(s.get("transition_in", ""), s.get("transition_in", "")))}</span></div>'
                f'<div class="main"><p class="visual">{esc(s.get("visual", ""))}</p>'
                f'<div class="vo">{vo}</div>'
                f'<p class="why">为什么用{STYLE_ZH[s["style"]]}：{esc(s.get("style_why", ""))}</p>'
                + (f'<ul class="ovs">{ovs}</ul>' if ovs else "")
                + f'<details><summary>制作细节</summary><dl>{extra}</dl></details></div></article>')
        body.append("</section>")

    accents = meta["accents"]
    if len(accents) != 3:
        raise SystemExit("storyboard/page.yaml 的 accents 必须是 3 个强调色")
    page = TEMPLATE.format(
        n=len(shots), mins=f"{total / 60:.1f}", strip="".join(strip), segmarks="".join(seg_marks),
        legend=legend, qrows=qrows, frames="".join(frames), body="".join(body),
        nseg=len(order),
        document_title=meta["document_title"],
        kicker=meta["kicker"],
        h1=meta["title"],
        lede=meta["lede"],
        frames_label=meta["frames_label"],
        rules=rules_html(meta["rules"]),
        a=accents[0]["id"], b=accents[1]["id"], c=accents[2]["id"],
        a_light=accents[0]["light"], b_light=accents[1]["light"], c_light=accents[2]["light"],
        a_dark=accents[0]["dark"], b_dark=accents[1]["dark"], c_dark=accents[2]["dark"],
    )
    open(out, "w", encoding="utf-8").write(page)
    print(out, f"{os.path.getsize(out) / 1e6:.2f} MB")


TEMPLATE = """<title>{document_title}</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;500;700&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans+Condensed:wght@500;600&display=swap">
<style>
/* Layout: a film reel read top to bottom — one timeline strip of the whole cut, then shots as numbered frames per segment. */
:root {{
  --ground: #f3f4f7; --panel: #ffffff; --ink: #141826; --ink-2: #4b5268; --rule: #dde0e8;
  --{a}: {a_light}; --{b}: {b_light}; --{c}: {c_light};
  --st-photoreal: #5d6b80; --st-xray: #aab3c2; --st-blueprint: #1f5fbf; --st-energy: #7b52e6;
  --st-infographic: #0f9bb0; --st-clay: #c9bfae; --st-sem: #7a7a7a; --st-hud: #12a37f;
  --st-type: #22273a; --st-documentary: #c98a1e;
  --f-display: "IBM Plex Sans Condensed", "Noto Sans SC", "PingFang SC", sans-serif;
  --f-body: "Noto Sans SC", "PingFang SC", "Hiragino Sans GB", sans-serif;
  --f-mono: "IBM Plex Mono", ui-monospace, "SF Mono", Menlo, monospace;
}}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{
  --ground: #0b0e17; --panel: #131828; --ink: #e8ebf3; --ink-2: #a1a8bd; --rule: #262c40;
  --{a}: {a_dark}; --{b}: {b_dark}; --{c}: {c_dark}; --st-type: #e8ebf3; --st-xray: #c7cedb;
  color-scheme: dark; }} }}
:root[data-theme="dark"] {{
  --ground: #0b0e17; --panel: #131828; --ink: #e8ebf3; --ink-2: #a1a8bd; --rule: #262c40;
  --{a}: {a_dark}; --{b}: {b_dark}; --{c}: {c_dark}; --st-type: #e8ebf3; --st-xray: #c7cedb;
  color-scheme: dark; }}
* {{ box-sizing: border-box; }}
body {{ background: var(--ground); color: var(--ink); font: 15px/1.7 var(--f-body);
  padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px));
  padding-block: 32px 64px; }}
.wrap {{ max-width: 1120px; margin: 0 auto; display: grid; gap: 40px; }}
h1, h2 {{ font-family: var(--f-display); text-wrap: balance; margin: 0; }}
h1 {{ font-size: clamp(30px, 5vw, 46px); line-height: 1.15; letter-spacing: .01em; }}
.lede {{ max-width: 62ch; color: var(--ink-2); margin: 10px 0 0; }}
.stats {{ display: flex; flex-wrap: wrap; gap: 28px; margin-top: 18px; font-family: var(--f-mono); font-size: 13px; color: var(--ink-2); }}
.stats b {{ display: block; font-family: var(--f-display); font-size: 28px; color: var(--ink); font-variant-numeric: tabular-nums; }}
.label {{ font-family: var(--f-mono); font-size: 12px; letter-spacing: .08em; text-transform: uppercase; color: var(--ink-2); margin: 0 0 10px; }}
.reel {{ display: grid; gap: 6px; }}
.strip {{ display: flex; height: 42px; border-radius: 4px; overflow: hidden; background: var(--rule); gap: 1px; }}
.tick {{ display: block; min-width: 1px; background: var(--c); opacity: .92; }}
.tick:hover, .tick:focus-visible {{ opacity: 1; outline: 2px solid var(--ink); outline-offset: -2px; }}
.segmarks {{ display: flex; gap: 1px; font-family: var(--f-mono); font-size: 11px; color: var(--ink-2); }}
.segmark {{ min-width: 0; border-left: 1px solid var(--rule); padding-left: 3px; color: inherit; text-decoration: none; overflow: hidden; white-space: nowrap; }}
.reelfoot {{ display: flex; justify-content: space-between; font-family: var(--f-mono); font-size: 11px; color: var(--ink-2); }}
.legend {{ display: flex; flex-wrap: wrap; gap: 8px; }}
.chip {{ --c: var(--ink-2); display: inline-flex; align-items: center; gap: 7px; border: 1px solid var(--rule); background: var(--panel);
  color: var(--ink); border-radius: 999px; padding: 5px 12px; font: 500 13px var(--f-body); cursor: pointer; }}
.chip .dot {{ width: 9px; height: 9px; border-radius: 50%; background: var(--c); flex: none; }}
.chip .n {{ font-family: var(--f-mono); color: var(--ink-2); font-size: 12px; }}
.chip[aria-pressed="true"] {{ border-color: var(--c); box-shadow: inset 0 0 0 1px var(--c); }}
.chip:focus-visible {{ outline: 2px solid var(--{a}); outline-offset: 2px; }}
.chip.sm {{ cursor: default; padding: 2px 9px; font-size: 12px; }}
.clear {{ font: 500 13px var(--f-body); background: none; border: 0; color: var(--{a}); cursor: pointer; padding: 5px 6px; }}
.st-photoreal {{ --c: var(--st-photoreal); }} .st-xray {{ --c: var(--st-xray); }} .st-blueprint {{ --c: var(--st-blueprint); }}
.st-energy {{ --c: var(--st-energy); }} .st-infographic {{ --c: var(--st-infographic); }} .st-clay {{ --c: var(--st-clay); }}
.st-sem {{ --c: var(--st-sem); }} .st-hud {{ --c: var(--st-hud); }} .st-type {{ --c: var(--st-type); }} .st-documentary {{ --c: var(--st-documentary); }}
.two {{ display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 32px; }}
.qlist {{ list-style: none; margin: 0; padding: 0; display: grid; gap: 6px; font-size: 14px; color: var(--ink-2); }}
.qlist b {{ color: var(--ink); font-weight: 500; display: inline-block; min-width: 6.5em; }}
.sw {{ display: inline-block; width: 10px; height: 10px; border-radius: 2px; background: var(--c); margin-right: 8px; vertical-align: 1px; }}
.rules {{ margin: 0; padding-left: 1.1em; color: var(--ink-2); font-size: 14px; display: grid; gap: 6px; }}
.frames {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; }}
figure {{ margin: 0; }}
figure img {{ display: block; width: 100%; aspect-ratio: 16 / 9; object-fit: cover; border-radius: 3px; background: #000; }}
figcaption {{ font-size: 12px; color: var(--ink-2); margin-top: 5px; }}
figcaption b {{ color: var(--ink); font-weight: 500; margin-right: 6px; }}
.seg {{ display: grid; gap: 10px; scroll-margin-top: 16px; }}
.act {{ font-family: var(--f-mono); font-size: 12px; letter-spacing: .1em; color: var(--{a}); margin: 18px 0 0; }}
.seghead {{ display: flex; flex-wrap: wrap; align-items: baseline; justify-content: space-between; gap: 6px 16px; border-bottom: 1px solid var(--ink); padding-bottom: 8px; }}
.seghead h2 {{ font-size: 24px; font-weight: 600; }}
.segid {{ font-family: var(--f-mono); font-size: 15px; color: var(--ink-2); margin-right: 12px; font-weight: 500; }}
.segmeta {{ margin: 0; font-family: var(--f-mono); font-size: 12px; color: var(--ink-2); }}
.shot {{ display: grid; grid-template-columns: 170px minmax(0, 1fr); gap: 18px; padding: 14px 0; border-bottom: 1px solid var(--rule); scroll-margin-top: 16px; }}
.shot:target {{ background: color-mix(in srgb, var(--{a}) 8%, transparent); }}
.meta {{ display: flex; flex-direction: column; align-items: flex-start; gap: 4px; font-family: var(--f-mono); font-size: 12px; color: var(--ink-2); }}
.sid {{ font-size: 15px; color: var(--ink); font-weight: 500; }}
.tc, .dur {{ font-variant-numeric: tabular-nums; }}
.main {{ display: grid; gap: 8px; min-width: 0; }}
.visual {{ margin: 0; }}
.vo {{ border-left: 2px solid var(--{a}); padding-left: 12px; color: var(--ink); font-size: 14.5px; }}
.vo p {{ margin: 0; }}
.vo .mute {{ color: var(--ink-2); }}
.why {{ margin: 0; font-size: 13px; color: var(--ink-2); }}
.ovs {{ margin: 0; padding: 0; list-style: none; display: flex; flex-wrap: wrap; gap: 6px; }}
.ovs li {{ font-size: 12.5px; border: 1px solid var(--rule); border-radius: 3px; padding: 2px 8px; background: var(--panel); }}
.fid {{ font-family: var(--f-mono); color: var(--{c}); margin-left: 6px; font-size: 11.5px; }}
details {{ font-size: 13px; color: var(--ink-2); }}
summary {{ cursor: pointer; width: max-content; }}
summary:focus-visible {{ outline: 2px solid var(--{a}); outline-offset: 2px; }}
dl {{ display: grid; grid-template-columns: 5em minmax(0, 1fr); gap: 2px 10px; margin: 8px 0 0; }}
dt {{ color: var(--ink); }} dd {{ margin: 0; overflow-wrap: anywhere; }}
.filtering .shot:not(.on) {{ display: none; }}
.filtering .seg:not(.has) {{ display: none; }}
@media (max-width: 760px) {{
  .two {{ grid-template-columns: 1fr; }}
  .frames {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
  .shot {{ grid-template-columns: 1fr; gap: 8px; }}
  .meta {{ flex-direction: row; flex-wrap: wrap; align-items: center; gap: 4px 12px; }}
}}
@media (prefers-reduced-motion: reduce) {{ html {{ scroll-behavior: auto; }} }}
</style>
<div class="wrap">
  <header>
    <p class="label">{kicker}</p>
    <h1>{h1}</h1>
    <p class="lede">{lede}</p>
    <div class="stats"><span><b>{n}</b>个镜头</span><span><b>{mins}</b>分钟（按旁白字数估算）</span><span><b>{nseg}</b>个段落</span><span><b>10</b>种画面语言</span></div>
  </header>

  <section class="reel" aria-label="全片时间轴">
    <p class="label">全片时间轴 · 按画面语言着色，点击跳到镜头</p>
    <div class="strip">{strip}</div>
    <div class="segmarks">{segmarks}</div>
    <div class="reelfoot"><span>00:00</span><span>{mins} 分钟</span></div>
  </section>

  <section class="two">
    <div>
      <p class="label">画面语言 · 每个镜头先问它在回答什么</p>
      <ul class="qlist">{qrows}</ul>
    </div>
    <div>
      <p class="label">混搭规则</p>
      <ol class="rules">
{rules}
      </ol>
    </div>
  </section>

  <section>
    <p class="label">{frames_label}</p>
    <div class="frames">{frames}</div>
  </section>

  <section aria-label="按画面语言筛选">
    <p class="label">按画面语言筛选</p>
    <div class="legend" id="legend">{legend}<button class="clear" type="button" id="clear">显示全部</button></div>
  </section>

  <main id="board">{body}</main>
</div>
<script>
(function () {{
  var board = document.getElementById('board');
  var chips = Array.prototype.slice.call(document.querySelectorAll('#legend .chip'));
  function apply() {{
    var on = chips.filter(function (c) {{ return c.getAttribute('aria-pressed') === 'true'; }})
                  .map(function (c) {{ return c.dataset.style; }});
    board.classList.toggle('filtering', on.length > 0);
    document.querySelectorAll('.seg').forEach(function (seg) {{
      var any = false;
      seg.querySelectorAll('.shot').forEach(function (s) {{
        var hit = on.indexOf(s.dataset.style) >= 0; s.classList.toggle('on', hit); any = any || hit;
      }});
      seg.classList.toggle('has', any);
    }});
  }}
  chips.forEach(function (c) {{
    c.addEventListener('click', function () {{
      c.setAttribute('aria-pressed', c.getAttribute('aria-pressed') === 'true' ? 'false' : 'true'); apply();
    }});
  }});
  document.getElementById('clear').addEventListener('click', function () {{
    chips.forEach(function (c) {{ c.setAttribute('aria-pressed', 'false'); }}); apply();
  }});
}})();
</script>
"""

if __name__ == "__main__":
    main()
