# E2 internal rework — clear deferred + SF10 hold + SF19 pullback · 2026-10-23 ~20:41 Asia/Shanghai

## Done (no GPU this round · pods=[])
1. **SF18/SF19** re-ran `macro_photo_boost.py` only:
   - Removed all on-screen `deferred` / 笼写实制作备注 (chip + footer).
   - Audience copy: `光纤植入 · 清醒活动 / 头戴光纤 · 自由走动`; footer `B · 活体 · 光纤植入小鼠` / `C · 假记忆 · 环境甲 / 环境乙`.
   - SF19: `fit_plate` + threeq stills, zoom_amp≈0.018 (full-body, not hindquarters ken-burns).
   - SF18 act1/2/3: fit_plate contain instead of aggressive kb_crop.
2. **SF10**: rebuilt from 120 GPU frames → **18.96s@24fps** = motion 5s → hold 2s → soft fade to awake still KB (~12s). Assemble uses **trim** (no xfade-loop ghost). Also patched `assemble_v8_roughcut.py` `HOLD_LAST_STEMS` fallback.
3. Assembled INTERNAL master (AAC).

## Self-proof (OCR tesseract eng+chi_sim)
| Asset | deferred hit |
|---|---|
| `styleframes/SF18_invivo_dual.png` + vid t22/t50 | CLEAN |
| `styleframes/SF19_engram.png` + vid t10/t40 | CLEAN |
| Film t400/420/450/500/520 (SF18/19 windows) | CLEAN |

Probe dir: `/workspace/e2work/v8/review/_nodeferred_probe/` + `_selfeval_2030/`.

## Carl five-dim self-eval — **~81 / 100 · DO NOT PUSH**
| 维 | 粗分 | 差在哪 |
|---|---|---|
| 1 尺度美学 | 76 | 大半时间线仍是插画板；宏观英雄只嵌 SF04/05/10/18/19 |
| 2 主体质量 | 83 | 锁定 glb 毛皮 OK；SF19 已退远见全身；**笼箱写实毛发仍 deferred（未进画面）** |
| 3 科学与旁白 | 90 | 旁白跟得上；**SF18/19 板内 deferred 文案已清**（OCR 自证） |
| 4 运动与声音 | 84 | AAC；SF10 不再 5s×loop 残影（trim 单遍）；长窗后半仍是静帧 KB |
| 5 可看完 | 72 | ~14.4 min 有声连贯，仍是板拼盘，远非 Branch/HHMI 能播 |

**Verdict: NEEDS_REWORK · 不推 Carl / 不上 Funnel/files。**  
相对 1957 自评 ~77：主要兑现「清 deferred + SF10 无残影 loop + SF19 退远」；整体仍 ≪95，因为插画板占比 + 笼箱写实未上。

## Paths
- Master: `/workspace/e2work/lowres_cut/E2_roughcut_v8_internal_20261023_2030.mp4` (864.71s, AAC)
- Share (local only): `..._2030_share.mp4`
- SF10/18/19: `/workspace/e2work/v8/styleframes/SF{10_mouse_tripo,18_invivo_dual,19_engram}.{mp4,png}`
- Boost log: `v8/review/_macro_boost_nodeferred.log`
- pods=[] GraphQL-confirmed 20:41 CST · $0 this round

## Next knife (if continue)
1. More macro photoreal plates into timeline (replace long illustration stretches).
2. Cage-box photoreal fur when align-loop ROI wins (still deferred intentionally).
3. SF10 true multi-beat animation longer than 5s (sleep→wake continuous) instead of still KB tail.
