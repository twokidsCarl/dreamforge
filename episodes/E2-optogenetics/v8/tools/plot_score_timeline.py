#!/usr/bin/env python3
"""Update review/score_timeline.png for E2 v8 independent-review rounds.
Carl HARD 2026-10-22: regenerate every scoring round.
Edit ROUNDS below when a new independent review lands, then run.
"""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# (label, avg, min_score, min_sf_label)
ROUNDS = [
    ('R4\n(v2 复打)', 79.4, 73.2, 'SF10'),
    ('R5', 85.4, 79.9, 'SF10'),
    ('R6b', 86.8, 83.5, 'SF10'),
    ('R7', 86.4, 81.6, 'SF10'),
    ('R8', 87.77, 83.2, 'SF05'),
    ('R9', 90.2, 87.5, 'SF05'),
    ('R10', 90.5, 88.1, 'SF05'),
    ('R11', 91.1, 88.7, 'SF04'),
    ('R12', 88.9, 85.3, 'SF10'),
    ('R13', 87.9, 80.95, 'SF10'),
    ('R14', 90.97, 88.58, 'SF04'),
]

OUT = Path(__file__).resolve().parents[1] / 'review' / 'score_timeline.png'

def main():
    matplotlib.rcParams['font.sans-serif'] = [
        'Noto Sans CJK SC', 'Noto Serif CJK SC', 'WenQuanYi Micro Hei', 'DejaVu Sans']
    matplotlib.rcParams['axes.unicode_minus'] = False
    labels = [r[0] for r in ROUNDS]
    avg = [r[1] for r in ROUNDS]
    mins = [r[2] for r in ROUNDS]
    min_labs = [r[3] for r in ROUNDS]
    last = labels[-1].split('\n')[0]
    fig, ax = plt.subplots(figsize=(10, 5.5), dpi=140)
    x = list(range(len(ROUNDS)))
    ax.axhline(92, color='#2ca02c', ls='--', lw=1.4, label='门槛均分 ≥ 92')
    ax.axhline(88, color='#ff7f0e', ls=':', lw=1.4, label='单张门槛 ≥ 88')
    ax.plot(x, avg, 'o-', color='#1f77b4', lw=2.2, ms=8, label='独立审均分')
    ax.plot(x, mins, 's--', color='#d62728', lw=1.8, ms=7, label='最低单张')
    for i, (a, m, lab) in enumerate(zip(avg, mins, min_labs)):
        ax.annotate(f'{a:g}', (i, a), textcoords='offset points', xytext=(0, 10),
                    ha='center', fontsize=9, color='#1f77b4', fontweight='bold')
        ax.annotate(f'{m:g}\n({lab})', (i, m), textcoords='offset points', xytext=(0, -22),
                    ha='center', fontsize=8, color='#d62728')
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel('SCALE_v2 分数')
    ax.set_ylim(70, 95)
    ax.set_title(f'E2 v8 样张独立审分数时间轴（含第 {last.lstrip("R")} 轮）', fontsize=13, pad=12)
    ax.legend(loc='lower right', framealpha=0.92)
    ax.grid(True, alpha=0.35)
    ax.set_axisbelow(True)
    fig.tight_layout()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, bbox_inches='tight')
    print('wrote', OUT)

if __name__ == '__main__':
    main()
