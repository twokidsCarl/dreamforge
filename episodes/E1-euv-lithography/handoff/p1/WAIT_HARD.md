# WAIT_HARD — 禁止 pgrep 自锁等审 / 等渲（Carl / Luna · NS-17 · R25）

**适用**：主进程与一切 subagent（冒烟代理、审稿 lane、cut/helper）。复制 `r{N}smoke/COMMON_AGENT.md` 时 **Waiting 段必须含本文件要点**；下一轮 job `PROMPT.md` 必须继承 R26 `(d)`。

## 根因（写清，勿再犯）

R25 主进程等三路独立审时写了：

```bash
for P in $(pgrep -f "run_lane.sh p"); do tail --pid=$P -f /dev/null; done
```

`pgrep -f` 匹配到**等待 shell 自己的 cmdline**（cmdline 里含 `run_lane.sh p`），于是 `tail --pid=$自己`。三路 lane 在 13:27–13:28 已全部 `exit 0` / `STATUS` done，主进程却空转 ≥33 分钟，写不出 merge / REVIEW / PUBLISHED。R20 cut 子任务也曾用 `pgrep -f` 等渲染，自匹配空等约 30 分钟。

## HARD 规则

1. **禁止**用 `pgrep -f` + `tail --pid`、`while pgrep …`、或 sleep 轮询来等独立审或等渲染。
2. **等独立审**：只盯文件出现——
   - `review_rN/p1/STATUS.txt`
   - `review_rN/p2/STATUS.txt`
   - `review_rN/p3/STATUS.txt`
   - （或 `lane_p*.out` 已写 done / STATUS）
   三路齐了 → **立刻** `merge.py`，**不等**进程退出，**不** pgrep。
   推荐（Luna 维护）：`/workspace/luna-ops/claude-hooks/scripts/wait-review-lanes.sh <review_rN>`。
3. **等渲染**：前台跑（Bash 带足够 timeout）或 background + **done-file**；禁止 pgrep 等待。

## COMMON_AGENT Waiting 段（复制用）

```text
## Waiting / budget (hard)
- NEVER wait with `pgrep -f` + `tail --pid`, `while pgrep`, or sleep loops for independent review OR for renders
  (R25: main process `pgrep -f "run_lane.sh p"` matched the waiting shell itself → 33+ min idle after lanes exited;
   R20 cut: same self-match ~30 min).
- Waiting for independent review is the MAIN PROCESS job: watch only
  `review_rN/p1/STATUS.txt`, `p2/STATUS.txt`, `p3/STATUS.txt` (or `lane_p*.out` done); when all three exist, run merge.py immediately. Do not wait on PIDs.
- For your own smokes/renders: run in the FOREGROUND of a Bash call, or background with a done-file and do other work. Never pgrep-wait.
```

## 交叉引用

- `ROUND_PIPELINE.md` §B（R14 / R21 / R26 追加）、§E 审分并行、禁止事项表
- `WORK_ORDER.md`「每轮流程」§5
- job PROMPT R25 RETRO `(d)`（R26 起默认必带，后续轮继承）
