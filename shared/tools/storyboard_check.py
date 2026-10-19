"""Merge storyboard parts and check them against the script, the fact base and the style rules.

  python3 tools/storyboard_check.py            # merge parts/*.yaml -> storyboard.yaml, then check
  python3 tools/storyboard_check.py --no-merge # check storyboard.yaml as is

Errors (exit 1): missing / duplicated / out-of-order narration, shot shorter than its VO,
unknown or rejected facts, on-screen numbers without facts, 
unknown style or engine, duplicate ids.
Warnings: >3 consecutive shots in one style (segment C exempt), <3 styles in a segment,
segment duration more than 15% off target.
"""
import argparse
import collections
import glob
import os
import re
import sys

import yaml

sys.path.insert(0, os.path.dirname(__file__))
from lint_script import CHARS_PER_MIN, parse, spoken_len  # noqa: E402

from paths import AUDIO, EP, REPO, RENDERS, SHARED  # noqa: E402,F401
SB = os.path.join(EP, "storyboard")
STYLES = {"photoreal", "xray", "blueprint", "energy", "infographic", "clay", "sem", "hud", "type",
          "documentary"}
ENGINES = {"cycles", "eevee", "manim", "pillow"}
TARGET_S = {"A0": 50, "A1": 80, "A2": 80, "A3": 50, "B1": 165, "B2": 75, "B3": 45, "B4": 120,
            "B5": 55, "B6": 100, "B7": 110, "B8": 120, "B9": 70, "C": 100, "D": 55}
PAUSE_S = 0.35
DIGIT = re.compile(r"[0-9]")


def merge():
    shots = []
    for p in sorted(glob.glob(os.path.join(SB, "parts", "*.yaml"))):
        shots += yaml.safe_load(open(p, encoding="utf-8"))["shots"]
    order = list(TARGET_S)
    shots.sort(key=lambda s: (order.index(s["segment"]), s["id"]))
    with open(os.path.join(SB, "storyboard.yaml"), "w", encoding="utf-8") as fh:
        fh.write("# Merged by tools/storyboard_check.py from storyboard/parts/*.yaml — edit the parts.\n")
        yaml.safe_dump({"shots": shots}, fh, allow_unicode=True, sort_keys=False, width=120)
    return shots


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-merge", action="store_true")
    a = ap.parse_args()
    shots = (yaml.safe_load(open(os.path.join(SB, "storyboard.yaml"), encoding="utf-8"))["shots"]
             if a.no_merge else merge())
    facts = yaml.safe_load(open(os.path.join(EP, "research/facts.yaml"), encoding="utf-8"))
    script = parse(os.path.join(EP, "script/script_zh.md"))
    errors, warns = [], []

    ids = [s["id"] for s in shots]
    for i, c in collections.Counter(ids).items():
        if c > 1:
            errors.append(f"duplicate id {i}")

    # narration coverage and order
    expected = [L["text"] for seg in script for L in seg["lines"]]
    got = [(s["id"], v) for s in shots for v in s.get("vo") or []]
    got_text = [v for _, v in got]
    for t in expected:
        n = got_text.count(t)
        if n != 1:
            errors.append(f"narration appears {n}x: {t[:30]}")
    stray = [f"{i}: {v[:30]}" for i, v in got if v not in expected]
    errors += [f"vo not in script — {x}" for x in stray]
    seq = [t for t in got_text if t in expected]
    if seq != [t for t in expected if t in seq]:
        errors.append("narration out of script order")

    for s in shots:
        vo_s = sum(spoken_len(v) / CHARS_PER_MIN * 60 + PAUSE_S for v in s.get("vo") or [])
        if s["duration"] + 1e-6 < vo_s:
            errors.append(f"{s['id']} duration {s['duration']}s < VO {vo_s:.1f}s")
        if s.get("style") not in STYLES:
            errors.append(f"{s['id']} unknown style {s.get('style')}")
        if s.get("engine") not in ENGINES:
            errors.append(f"{s['id']} unknown engine {s.get('engine')}")
        cited = set(s.get("facts") or [])
        for ov in s.get("overlays") or []:
            cited |= set(ov.get("facts") or [])
            if DIGIT.search(str(ov.get("text", ""))) and not ov.get("facts"):
                errors.append(f"{s['id']} overlay number without facts: {ov.get('text')}")
        for f in cited:
            if f not in facts:
                errors.append(f"{s['id']} unknown fact {f}")
            elif facts[f]["status"] == "rejected":
                errors.append(f"{s['id']} rejected fact {f}")

    # style rhythm
    run, prev = 0, None
    for s in shots:
        run = run + 1 if (s["style"] == prev and s["segment"] != "C") else 1
        prev = s["style"]
        if run == 4:
            warns.append(f"{s['id']}: 4+ consecutive '{s['style']}' shots")
    by_seg = collections.OrderedDict()
    for s in shots:
        by_seg.setdefault(s["segment"], []).append(s)
    print(f"{'seg':<4}{'shots':>6}{'dur':>8}{'target':>8}  styles")
    for seg, ss in by_seg.items():
        d = sum(x["duration"] for x in ss)
        st = collections.Counter(x["style"] for x in ss)
        print(f"{seg:<4}{len(ss):>6}{d:>7.0f}s{TARGET_S.get(seg, 0):>7}s  {dict(st)}")
        if len(st) < 3:
            warns.append(f"{seg}: only {len(st)} styles")
        if seg in TARGET_S and abs(d - TARGET_S[seg]) > 0.15 * TARGET_S[seg]:
            warns.append(f"{seg}: {d:.0f}s vs target {TARGET_S[seg]}s")
    total = sum(s["duration"] for s in shots)
    allst = collections.Counter(s["style"] for s in shots)
    print(f"total {len(shots)} shots, {total / 60:.1f} min  styles {dict(allst.most_common())}")
    print("engines", dict(collections.Counter(s["engine"] for s in shots)))
    for w in warns:
        print("WARN ", w)
    for e in errors:
        print("ERROR", e)
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
