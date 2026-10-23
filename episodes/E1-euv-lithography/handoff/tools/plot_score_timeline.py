#!/usr/bin/env python3
"""handoff/p1/score_timeline.png for E1 P1 (rerun after every scoring round, SCALE_E1 §5.6).
Reads p1/scores_round1.json, p1/scores_round1_recalibrated.json, p1/scores_round2.json (… roundN) if present."""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

P1 = Path(__file__).resolve().parents[1] / "p1"
SERIES = [("R1\n(SCALE v1)", "scores_round1.json"), ("R1-recal\n(SCALE v2)", "scores_round1_recalibrated.json")]
SERIES += [(f"R{n}\n(SCALE v2)", f"scores_round{n}.json") for n in range(2, 10)]


def main():
    matplotlib.rcParams["font.sans-serif"] = ["Noto Sans CJK SC", "Noto Serif CJK SC", "DejaVu Sans"]
    matplotlib.rcParams["axes.unicode_minus"] = False
    rows = []
    for lab, fn in SERIES:
        p = P1 / fn
        if p.exists():
            d = json.loads(p.read_text())
            rows.append((lab, d["avg"], d["min"], d.get("min_shot", "")))
    fig, ax = plt.subplots(figsize=(9, 4.8), dpi=130)
    fig.patch.set_facecolor("#0E1424")
    ax.set_facecolor("#0E1424")
    x = range(len(rows))
    ax.plot(x, [r[1] for r in rows], "-o", color="#8A5CFF", lw=2.5, label="独立审均分")
    ax.plot(x, [r[2] for r in rows], "--s", color="#3FD6E0", lw=1.8, label="最低单镜")
    for i, r in enumerate(rows):
        ax.annotate(f"{r[1]:.2f}", (i, r[1]), textcoords="offset points", xytext=(0, 9), ha="center", color="#E8ECF4")
        ax.annotate(f"{r[2]:.2f}\n{r[3]}", (i, r[2]), textcoords="offset points", xytext=(0, -26), ha="center",
                    color="#9FB3C8", fontsize=8)
    ax.axhline(92, color="#FF8A3D", lw=1, ls=":")
    ax.text(len(rows) - 0.5, 92.6, "门槛：均分 ≥92", color="#FF8A3D", ha="right", fontsize=9)
    ax.axhline(88, color="#FF8A3D", lw=0.8, ls=":", alpha=0.6)
    ax.text(len(rows) - 0.5, 88.6, "单张 ≥88", color="#FF8A3D", ha="right", fontsize=8, alpha=0.8)
    ax.set_xticks(list(x))
    ax.set_xticklabels([r[0] for r in rows], color="#E8ECF4")
    ax.set_ylim(40, 100)
    ax.tick_params(colors="#E8ECF4")
    for s in ax.spines.values():
        s.set_color("#3a4560")
    ax.set_title("E1 P1 风格帧 · 分数时间轴（R1-recal 起按 SCALE_E1 v2 = Carl 点选锚）", color="#E8ECF4", fontsize=11)
    ax.legend(facecolor="#0E1424", edgecolor="#3a4560", labelcolor="#E8ECF4", loc="lower right")
    ax.grid(color="#1e2740", lw=0.6)
    fig.tight_layout()
    out = P1 / "score_timeline.png"
    fig.savefig(out, facecolor=fig.get_facecolor())
    print("wrote", out, rows)


if __name__ == "__main__":
    main()
