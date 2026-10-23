#!/usr/bin/env python3
"""Shared E1/E2 round-progress board (timeline on top + per-round score header + contact).
Carl 2026-10-23 delivery preference: score_timeline.png only; this board is optional/internal.
Visual: dark #0e1424; cyan=过线 / orange=未过; gate avg≥92 and min≥88.
Usage:
  python3 build_round_progress_board.py --ep E1
  python3 build_round_progress_board.py --ep E2
  python3 build_round_progress_board.py --ep both
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

BG = (14, 20, 36)
HDR = (22, 30, 52)
CYAN = (63, 214, 224)
ORANGE = (255, 138, 61)
MUTED = (159, 179, 200)
GRAY_PANEL = (28, 36, 56)
GATE_AVG, GATE_MIN = 92.0, 88.0
CONTACT_H_CAP = 300
TITLE_H, HEADER_H, GAP = 52, 56, 12
SPLIT_AT = 8000
PREFER_SINGLE_UNDER = 6000

FONT_REG = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
FONT_BOLD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"

E1_P1 = Path("/workspace/eigenlens-e1/episodes/E1-euv-lithography/handoff/p1")
E1_WORK = Path("/workspace/e1work/p1")
E1_PLOT = Path("/workspace/eigenlens-e1/episodes/E1-euv-lithography/handoff/tools/plot_score_timeline.py")
E2_REVIEW = Path("/workspace/e2work/v8/review")
E2_PLOT = Path("/workspace/e2work/v8/tools/plot_score_timeline.py")
E2_REPO_COPIES = [
    Path("/workspace/eigenlens/episodes/E2-optogenetics/v8/review"),
    Path("/workspace/eigenlens-e1/episodes/E2-optogenetics/v8/review"),
]


def fonts():
    try:
        return (
            ImageFont.truetype(FONT_BOLD, 28, index=0),
            ImageFont.truetype(FONT_REG, 18, index=0),
            ImageFont.truetype(FONT_BOLD, 22, index=0),
        )
    except Exception:
        d = ImageFont.load_default()
        return d, d, d


def ensure_timeline(plot_py: Path, out: Path) -> Path:
    if plot_py.exists():
        subprocess.run([sys.executable, str(plot_py)], check=False)
    if not out.exists():
        raise FileNotFoundError(f"timeline missing: {out}")
    return out


def scale_contact(path: Path | None, tw: int, placeholder: str) -> Image.Image:
    if path and path.exists():
        im = Image.open(path).convert("RGB")
        scale = min(tw / im.width, CONTACT_H_CAP / im.height)
        nw, nh = max(1, int(im.width * scale)), max(1, int(im.height * scale))
        im = im.resize((nw, nh), Image.Resampling.LANCZOS)
        canvas = Image.new("RGB", (tw, nh), BG)
        canvas.paste(im, ((tw - nw) // 2, 0))
        return canvas
    h = min(CONTACT_H_CAP, 160)
    canvas = Image.new("RGB", (tw, h), GRAY_PANEL)
    d = ImageDraw.Draw(canvas)
    _, font_s, _ = fonts()
    d.text((tw // 2, h // 2), placeholder, fill=MUTED, font=font_s, anchor="mm")
    return canvas


def compose(ep: str, title: str, timeline: Path, rounds: list[tuple], outs: list[Path]) -> list[Path]:
    """rounds: list of (label, avg, mn, min_shot, contact_path|None)"""
    font_b, font_s, font_t = fonts()
    tl = Image.open(timeline).convert("RGB")
    tw, th = tl.size
    panels = []
    for lab, avg, mn, ms, cpath in rounds:
        panels.append((lab, avg, mn, ms, scale_contact(cpath, tw, "无接触表")))
    body_h = sum(HEADER_H + p[4].height + GAP for p in panels)
    total_h = TITLE_H + th + GAP + body_h
    written: list[Path] = []

    def paint(panel_slice, page_title, dests):
        bh = sum(HEADER_H + p[4].height + GAP for p in panel_slice)
        H = TITLE_H + th + GAP + bh
        out = Image.new("RGB", (tw, H), BG)
        d = ImageDraw.Draw(out)
        d.rectangle([0, 0, tw, TITLE_H], fill=HDR)
        d.text((20, TITLE_H // 2), page_title, fill=CYAN, font=font_t, anchor="lm")
        out.paste(tl, (0, TITLE_H))
        y = TITLE_H + th + GAP
        for lab, avg, mn, ms, canvas in panel_slice:
            ok = avg >= GATE_AVG and mn >= GATE_MIN
            col = CYAN if ok else ORANGE
            d.rectangle([0, y, tw, y + HEADER_H], fill=HDR)
            tag = "过线" if ok else "未过"
            d.text(
                (20, y + HEADER_H // 2),
                f"{lab}   均分 {avg:.2f}   最低 {mn:.2f}（{ms}）   {tag}",
                fill=col, font=font_b, anchor="lm",
            )
            y += HEADER_H
            out.paste(canvas, (0, y))
            y += canvas.height + GAP
        for dest in dests:
            dest.parent.mkdir(parents=True, exist_ok=True)
            out.save(dest, format="PNG")
            print("wrote", dest, out.size)
            written.append(dest)

    if total_h <= SPLIT_AT or total_h <= PREFER_SINGLE_UNDER + 500:
        paint(panels, f"{ep} · 每一轮分+图", outs)
    else:
        # page1: timeline + older; page2: recent 6
        recent = panels[-6:]
        older = panels[:-6] if len(panels) > 6 else panels
        paint(older or panels[:1], f"{ep} · 每一轮分+图 · p1", [p.with_name(p.stem + "_p1.png") for p in outs])
        paint(recent, f"{ep} · 每一轮分+图 · p2（近6轮）", [p.with_name(p.stem + "_p2.png") for p in outs])
    return written


def e1_rounds():
    mapping = [
        ("R1", "scores_round1.json", E1_WORK / "round1" / "contact.jpg"),
        ("R1-recal", "scores_round1_recalibrated.json", E1_WORK / "round1" / "contact.jpg"),
        ("R2", "scores_round2.json", E1_WORK / "round2" / "contact_round2.jpg"),
    ] + [(f"R{k}", f"scores_round{k}.json", E1_WORK / f"round{k}" / f"contact_round{k}.jpg") for k in range(3, 11)]
    rows = []
    for lab, fn, contact in mapping:
        sp = E1_P1 / fn
        if not sp.exists():
            continue
        d = json.loads(sp.read_text())
        cpath = contact
        if not cpath.exists():
            alt = E1_P1 / f"contact_{lab.lower().replace('-', '_')}.jpg"
            cands = list((E1_WORK / ("round1" if lab.startswith("R1") else "round2")).glob("contact*.jpg")) if lab.startswith("R") else []
            cpath = alt if alt.exists() else (cands[0] if cands else None)
        rows.append((lab, float(d["avg"]), float(d["min"]), str(d.get("min_shot", "")), cpath))
    return rows


def e2_rounds():
    # Prefer ROUNDS list from plot_score_timeline.py
    ns: dict = {}
    code = E2_PLOT.read_text()
    exec(compile(code, str(E2_PLOT), "exec"), ns)
    rounds = ns.get("ROUNDS") or []
    rows = []
    for lab, avg, mn, ms in rounds:
        short = lab.split("\n")[0]
        m = re.match(r"R(\d+)", short)
        n = int(m.group(1)) if m else None
        cpath = None
        if n is not None:
            for cand in [
                E2_REVIEW / f"R{n}_contact.jpg",
                E2_REVIEW / f"R{n}_best_contact.jpg",
            ]:
                if cand.exists():
                    cpath = cand
                    break
        rows.append((short, float(avg), float(mn), str(ms), cpath))
    return rows


def build_e1():
    tl = ensure_timeline(E1_PLOT, E1_P1 / "score_timeline.png")
    outs = [
        E1_WORK / "round_progress_scores_and_contacts.png",
        E1_P1 / "round_progress_scores_and_contacts.png",
    ]
    return compose("E1", "E1 · 每一轮分+图", tl, e1_rounds(), outs)


def build_e2():
    tl = ensure_timeline(E2_PLOT, E2_REVIEW / "score_timeline.png")
    outs = [E2_REVIEW / "round_progress_scores_and_contacts.png"]
    for repo in E2_REPO_COPIES:
        if repo.exists():
            outs.append(repo / "round_progress_scores_and_contacts.png")
    return compose("E2", "E2 · 每一轮分+图", tl, e2_rounds(), outs)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ep", choices=["E1", "E2", "both"], default="both")
    args = ap.parse_args()
    if args.ep in ("E1", "both"):
        build_e1()
    if args.ep in ("E2", "both"):
        build_e2()


if __name__ == "__main__":
    main()
