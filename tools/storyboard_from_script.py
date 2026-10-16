"""Turn the narration script into a storyboard skeleton.

  python3 tools/storyboard_from_script.py > projects/euv/storyboard/skeleton.yaml

Each `> [语言] 画面` note opens a shot that starts at the narration line it follows and runs
until the next note; several notes on one line split that line's time. Durations are
estimates from character count (tools/lint_script.CHARS_PER_MIN) until real VO timing exists.
"""
import os
import re
import sys

import yaml

sys.path.insert(0, os.path.dirname(__file__))
from lint_script import CHARS_PER_MIN, REF, spoken_len  # noqa: E402

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
NOTE = re.compile(r"^\s+>\s*\[([^\]]+)\]\s*(.*)$")
STYLE_KEYS = {"真实": "photoreal", "透明": "xray", "蓝图": "blueprint", "能量": "energy",
              "信息图": "infographic", "白模": "clay", "显微": "sem", "HUD": "hud",
              "排版": "type", "纪实": "documentary"}
PAUSE_S = 0.35      # breath after each sentence


def styles_of(tag):
    return [STYLE_KEYS[k] for k in re.findall("|".join(STYLE_KEYS), tag)] or ["tbd"]


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(REPO, "projects/euv/script/script_zh.md")
    segs, seg, last_line = [], None, None
    for raw in open(path, encoding="utf-8"):
        if raw.startswith("## "):
            sid, _, title = raw[3:].strip().partition(" ")
            seg = {"id": sid, "title": title, "lines": []}
            segs.append(seg)
        elif raw.startswith("- ") and seg is not None:
            text = raw[2:].strip()
            m = REF.search(text)
            last_line = {"text": REF.sub("", text).strip(),
                         "facts": [r.strip() for r in m.group(1).split(",")] if m else [],
                         "notes": []}
            seg["lines"].append(last_line)
        elif seg is not None and last_line is not None and NOTE.match(raw):
            tag, desc = NOTE.match(raw).groups()
            last_line["notes"].append({"tag": tag, "desc": desc})

    shots = []
    for s in segs:
        n, cur = 0, None
        for L in s["lines"]:
            dur = spoken_len(L["text"]) / CHARS_PER_MIN * 60 + PAUSE_S
            if L["notes"]:
                k = len(L["notes"])
                for note in L["notes"]:
                    n += 1
                    st = styles_of(note["tag"])
                    cur = {"id": f"{s['id']}_{n:02d}", "segment": s["id"], "style": st[0],
                           "style_to": st[1] if len(st) > 1 else None,
                           "visual": note["desc"], "vo": [L["text"]], "facts": list(L["facts"]),
                           "duration": round(dur / k, 2)}
                    shots.append(cur)
                    L = {"text": "", "facts": []}   # later notes on this line carry no VO
            elif cur is None or cur["segment"] != s["id"]:
                n += 1
                cur = {"id": f"{s['id']}_{n:02d}", "segment": s["id"], "style": "tbd",
                       "style_to": None, "visual": "", "vo": [L["text"]], "facts": list(L["facts"]),
                       "duration": round(dur, 2)}
                shots.append(cur)
            else:
                cur["vo"].append(L["text"])
                cur["facts"] += [f for f in L["facts"] if f not in cur["facts"]]
                cur["duration"] = round(cur["duration"] + dur, 2)
    for sh in shots:
        sh["vo"] = [v for v in sh["vo"] if v]
        if not sh["style_to"]:
            del sh["style_to"]
    total = sum(sh["duration"] for sh in shots)
    print(f"# skeleton: {len(shots)} shots, {total / 60:.1f} min of VO-driven time")
    print(yaml.safe_dump({"shots": shots}, allow_unicode=True, sort_keys=False, width=120))


if __name__ == "__main__":
    main()
