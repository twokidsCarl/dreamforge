# WAIT_HARD — 禁止 pgrep 自锁等审 / 等渲（Carl / Luna · NS-17 · R25）

**适用**：主进程与一切 subagent（冒烟代理、审稿 lane、cut/helper）。复制 `r{N}smoke/COMMON_AGENT.md` 时 **Waiting 段必须含本文件要点**，**派工约束段必须含下方 t331 段**；下一轮 job `PROMPT.md` 必须继承 R26 `(d)` 与 t331 三句。分数停滞的完整规则在 `ROUND_PIPELINE.md` 文首「常设 HARD」，这里只放要复制进代理提示词的句子。

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

## COMMON_AGENT 派工约束（t331，复制用）

主进程在派代理之前已经做完常设 HARD 第 1、2 条。代理侧只守这四句，避免在错的几何或错的 Facing 上继续调参：

```text
## Dispatch constraints (t331 — main process already applied)
- Optical/layout recipes in this task were sketched and checked on an 8 spp frame before they entered the work order. If your frame shows the read is geometrically impossible, stop that shot and keep prior-round pixels. Do not invent a camera rotate or a hook tweak to force it.
- Shared shaders/modules were looked at by the main process on one importer at 8 spp before dispatch. Do not replace Facing or the shared default params. A new misread (solid column, glass plate, glow dot, wire cage, light appearing from nowhere) means that shot keeps prior-round pixels.
- A shot marked structural (recurring minimum, or a turn path such as A0_10) is a scene-level rebuild into the frame. Hook depth, edge, alpha, and small camera nudges do not satisfy it.
- Report real pixels. Do not edit extra importers to inflate changed_vs_prev.
```

## PROMPT 必抄（t331，主进程写进下一轮 job PROMPT）

与 R26 `(d)` 一起默认必带。讨论之后就迭代，不要等 Carl 再问。

```text
(t331) Discussed process changes are already in ROUND_PIPELINE.md 常设 HARD. Apply them this round. Do not wait to be asked to iterate.
Optical/layout work-order rows need a sketch plus an 8 spp frame proving the fix is on screen before dispatch. Impossible recipes are banned.
Look at one importer at 8 spp before dispatching agents onto a shared shader. If Q4 fails or a new misread appears, keep prior-round pixels and report the real changed_vs_prev.
(Carl t381/t383, ROUND_PIPELINE 常设 HARD 7) Only visibly different structural changes count: prove each with an R(N-1) vs R(N) side-by-side + SELFCHECK sentence; invisible parameter tweaks = not delivered, not counted. The whole light path IF → illuminator → mask → projection → wafer stays complete and visible. Physical objects use regular, correct shapes (tin = regular near-round thin disc). Render quality is already good enough: target Carl's visible issues and gate gaps only; no cosmetic polish; shots Carl is happy with stay frozen.
(Carl t383) Never stop to wait for Carl between rounds: self-check → fix → if adjusted pass=no write r{N+1}job and launch it (tmux e1r{N+1}) before PUBLISHED/STATUS; the PUBLISHED push to Carl is reporting. Stop only on gate pass, budget limit, or a real blocker.
(Carl t384, ROUND_PIPELINE 常设 HARD 8) R34 closeout (and every later round, rolling vs 3 rounds back) runs the 3-round improvement check on drift-adjusted scores: improving = R34 adj avg >= 89.27 (R31 88.27 + 1.0) AND R34 adj min > 84.65 (R31 min) AND mean adj avg of R32-R34 > 88.49 (R26-R31 plateau top). Improving -> write r35job and launch. Not improving -> NO R35: write handoff/p1/BEST_PICK.md (per shot best adjusted score R19-R34 with frames present; tin shots only R32+, full-light-path shots only from rounds that meet Carl t381; gold controls latest; ties <=0.3 -> later round; one model per part across shots) + /workspace/e1work/p1/best_pick/CONTACT_BEST_PICK.jpg, and STATUS/PUBLISHED say 'E1 iteration stopped (no improvement over 3 rounds), BEST_PICK ready for low-res full-film assembly'. Do not start assembly.
```

## 交叉引用

- `ROUND_PIPELINE.md` 文首常设 HARD、§B（R14 / R21 / R26 追加）、§E 审分并行、禁止事项表
- `WORK_ORDER.md`「每轮流程」§0–§1、§5、§6
- job PROMPT R25 RETRO `(d)`（R26 起默认必带，后续轮继承）+ 上面的 t331 三句
