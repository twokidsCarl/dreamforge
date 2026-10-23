# E2 SF10 re-render + nest — 2026-10-23 ~20:10 Asia/Shanghai (INTERNAL)

## Accident fixed
Prior pod `b5i8o4a5jefxxu` Terminated with container-disk only → only `f_0001`+`f_0120` on box. SF18/19 stills already local (4 OK).

## Done
1. **A40** `5xssas6x92zgq8` CA-MTL-1 + vol `3b6w9chaub` $0.59/h · 19:33:06→~19:41 CST ≈**8.5 min · ~$0.08**
2. Re-ran `sf10_gpu_plate.py` dens=120000 samples=48 nframes=120 960×540 from locked `mouse_c57.glb`
3. **HARD pull first**: continuous pull → local **120/120 contiguous** under `/workspace/e2work/v8/renders/sf10_gpu/` then pod gone (`pods=[]` API-confirmed; did not touch later E1 pods)
4. Overwrote `styleframes/SF10_mouse_tripo.{mp4,png}` (5.0s@24fps; assemble loop-extends to 18.98s window)
5. Plates: `gen/sf10_{sleep,awake}.png` ← `renders/sf18_19_stills/mouse_{sleep,awake}_side.png`; `macro_photo_boost.py` SF18=**96.0s** SF19=**88.0s** (not shortened)
6. Internal roughcut: `E2_roughcut_v8_internal_20261023_1957.mp4` (864.71s, AAC) + `_share.mp4`

## Carl five-dim self-eval (ACCEPTANCE) — **~77 / 100 · DO NOT PUSH**
| 维 | 粗分 | 差在哪 |
|---|---|---|
| 1 尺度美学 | 72 | 大半仍是插画板；宏观英雄只嵌了 SF10/18/19 一小段 |
| 2 主体质量 | 78 | 锁定 glb 毛皮明显好于照片 2.5D；但 SF10 成片有残影/叠影；笼箱写实毛发仍 deferred；SF19 ken-burns 裁得过近（后胯/背毛） |
| 3 科学与旁白 | 82 | 旁白/字幕跟得上；**SF18 板内仍印着「笼箱写实毛发仍 deferred」制作备注**（漏进成片） |
| 4 运动与声音 | 80 | 有 AAC；SF10 源仅 5s 循环撑 19s，重复感重 |
| 5 可看完 | 70 | ~14.4 min 有声连贯，但仍是板拼盘感，远非 Branch/HHMI 能播 |

**Verdict: NEEDS_REWORK · 不推 Carl / 不上 Funnel/files。** 下一刀优先：清掉 SF18 板内 deferred 文案；SF10 渲更长源或更好的 loop；SF19 构图退远；笼箱毛发仍 deferred。

## Paths
- Frames: `/workspace/e2work/v8/renders/sf10_gpu/f_0001.png` … `f_0120.png` (120)
- SF10/18/19: `/workspace/e2work/v8/styleframes/SF{10_mouse_tripo,18_invivo_dual,19_engram}.{mp4,png}`
- Master: `/workspace/e2work/lowres_cut/E2_roughcut_v8_internal_20261023_1957.mp4`
- Share (local only): `..._1957_share.mp4`
- Spend: `/workspace/dreamforge-costs/E2-runpod.md` (row `5xssas6x92zgq8`)
- pods=[] confirmed 20:10 CST
See also STATUS_nodeferred_2030.md
