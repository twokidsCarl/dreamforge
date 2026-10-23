#!/usr/bin/env python3
"""handoff/p1/score_timeline.png for E1 P1 (rerun after every scoring round).
Visual style matched to E2 v8 tools/plot_score_timeline.py (Carl 2026-10-23: E1/E2 同格式).
Reads p1/scores_round1.json, scores_round1_recalibrated.json, scores_roundN.json if present.
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

P1 = Path(__file__).resolve().parents[1] / "p1"
WORK = Path("/workspace/e1work/p1")
# (axis label, json filename) — short labels like E2
# Carl 2026-10-23: drop SCALE v1 point — timeline only SCALE_v2 for fair compare
SERIES = [
    ("R1", "scores_round1_recalibrated.json"),  # first v2 round (recal)
]
SERIES += [(f"R{n}", f"scores_round{n}.json") for n in range(2, 10)]


def load_rounds():
    rows = []
    for lab, fn in SERIES:
        p = P1 / fn
        if not p.exists():
            continue
        d = json.loads(p.read_text())
        rows.append((lab, float(d["avg"]), float(d["min"]), str(d.get("min_shot", ""))))
    return rows


def main():
    matplotlib.rcParams["font.sans-serif"] = [
        "Noto Sans CJK SC", "Noto Serif CJK SC", "WenQuanYi Micro Hei", "DejaVu Sans"
    ]
    matplotlib.rcParams["axes.unicode_minus"] = False
    rows = load_rounds()
    if not rows:
        print("no score json found under", P1)
        return
    labels = [r[0] for r in rows]
    avg = [r[1] for r in rows]
    mins = [r[2] for r in rows]
    min_labs = [r[3] for r in rows]
    last = labels[-1].split("\n")[0]
    fig, ax = plt.subplots(figsize=(10, 5.5), dpi=140)
    x = list(range(len(rows)))
    ax.axhline(92, color="#2ca02c", ls="--", lw=1.4, label="门槛均分 ≥ 92")
    ax.axhline(88, color="#ff7f0e", ls=":", lw=1.4, label="单张门槛 ≥ 88")
    ax.plot(x, avg, "o-", color="#1f77b4", lw=2.2, ms=8, label="独立审均分")
    ax.plot(x, mins, "s--", color="#d62728", lw=1.8, ms=7, label="最低单张")
    for i, (a, m, lab) in enumerate(zip(avg, mins, min_labs)):
        ax.annotate(
            f"{a:g}", (i, a), textcoords="offset points", xytext=(0, 10),
            ha="center", fontsize=9, color="#1f77b4", fontweight="bold",
        )
        ax.annotate(
            f"{m:g}\n({lab})", (i, m), textcoords="offset points", xytext=(0, -22),
            ha="center", fontsize=8, color="#d62728",
        )
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel("SCALE_v2 分数")
    lo = min(60, max(40, min(mins) - 8))
    ax.set_ylim(lo, 100)
    ax.set_title(f"E1 P1 风格帧 · SCALE_v2 分数时间轴（含 {last}）", fontsize=13, pad=12)
    ax.legend(loc="lower right", framealpha=0.92)
    ax.grid(True, alpha=0.35)
    ax.set_axisbelow(True)
    fig.tight_layout()
    out = P1 / "score_timeline.png"
    fig.savefig(out, bbox_inches="tight")
    WORK.mkdir(parents=True, exist_ok=True)
    fig.savefig(WORK / "score_timeline.png", bbox_inches="tight")
    print("wrote", out)
    print("wrote", WORK / "score_timeline.png", rows)


if __name__ == "__main__":
    main()
