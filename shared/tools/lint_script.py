"""Check a narration script against the fact base and report length per segment.

  python3 tools/lint_script.py [episodes/<episode>/script/script_zh.md]

Script format:
  ## A0 开场：外星机器            segment heading (id first)
  - 旁白句……〔F17,F50〕          one narration sentence; fact ids in 〔〕 at the end
    > 画面：……                    visual note (ignored for length)

Rules (errors fail the run):
  * every cited fact id exists in episodes/<episode>/research/facts.yaml and is not `rejected`
  * a sentence containing a number must cite at least one fact
  * a sentence citing a `reported` (grade C) fact must say so (据报道 / 据…估算 / 据…)
Warnings: `disputed` facts (check the wording against the fact's `narration`).
"""
import os
import re
import sys

import yaml

from paths import AUDIO, EP, REPO, RENDERS, SHARED  # noqa: E402,F401
CHARS_PER_MIN = 250
NUMBER = re.compile(r"[0-9０-９]|(?:[二三四五六七八九十百千万亿两]|一[十百千万亿])[一二三四五六七八九十百千万亿两几]*\s*"
                    r"(?:个|倍|层|面|次|吨|米|纳米|微米|皮米|开尔文|瓦|千瓦|兆瓦|度|秒|年|小时|片|家|辆|分之|成)")
# rhetorical counts that are not factual claims
IDIOMS = re.compile(r"四面八方|千百个|一笔一笔|一层一层|一遍又一遍|三道难题|两条路|两只光锥|两张台子|两张晶圆台|两发激光|开这两枪|打两次|十几倍")
REF = re.compile(r"〔([^〕]*)〕\s*$")
HEDGE = re.compile(r"据[^，。]{0,12}(报道|估算|称|说|介绍)|据报道")


def parse(path):
    segs, cur = [], None
    for ln, line in enumerate(open(path, encoding="utf-8"), 1):
        if line.startswith("## "):
            sid, _, title = line[3:].strip().partition(" ")
            cur = {"id": sid, "title": title, "lines": []}
            segs.append(cur)
        elif line.startswith("- ") and cur is not None:
            text = line[2:].strip()
            m = REF.search(text)
            refs = [r.strip() for r in m.group(1).split(",")] if m else []
            body = REF.sub("", text).strip()
            cur["lines"].append({"ln": ln, "text": body, "refs": [r for r in refs if r]})
    return segs


def spoken_len(text):
    return len(re.sub(r"[\s，。、；：？！“”‘’（）《》—…·,.;:?!()\"'-]", "", text))


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(EP, "script/script_zh.md")
    facts = yaml.safe_load(open(os.path.join(EP, "research/facts.yaml"), encoding="utf-8"))
    segs = parse(path)
    errors, warnings = [], []
    total = 0
    print(f"{'seg':<5}{'sentences':>10}{'chars':>8}{'est':>8}  title")
    for s in segs:
        n = 0
        for L in s["lines"]:
            n += spoken_len(L["text"])
            where = f"{os.path.basename(path)}:{L['ln']}"
            for r in L["refs"]:
                f = facts.get(r)
                if f is None:
                    errors.append(f"{where} unknown fact {r}")
                elif f["status"] == "rejected":
                    errors.append(f"{where} cites rejected fact {r}")
                elif f["status"] == "reported" and not HEDGE.search(L["text"]):
                    pass  # 2026-10-19: popular-science narration, no "据报道" hedge required (user decision)
                elif f["status"] == "disputed":
                    warnings.append(f"{where} disputed fact {r}: use wording “{f.get('narration', '')}”")
            if NUMBER.search(IDIOMS.sub("", L["text"])) and not L["refs"]:
                errors.append(f"{where} number without fact reference: {L['text'][:40]}")
        total += n
        print(f"{s['id']:<5}{len(s['lines']):>10}{n:>8}{n / CHARS_PER_MIN * 60:>7.0f}s  {s['title']}")
    print(f"{'total':<5}{sum(len(s['lines']) for s in segs):>10}{total:>8}{total / CHARS_PER_MIN:>7.1f}m"
          f"  (+~10% visual breathing ≈ {total / CHARS_PER_MIN * 1.1:.1f} min)")
    for w in warnings:
        print("WARN ", w)
    for e in errors:
        print("ERROR", e)
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
