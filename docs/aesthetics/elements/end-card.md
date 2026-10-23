# 元素：片尾卡

**状态：LOCKED**（Carl 2026-10-22 / 2026-10-23）

## 已锁定
- 片尾放「贴片」：画面上写 **eigenlens.ai**，加一句中文号召，引导观众去本期的互动知识和模拟网站。
- 片中**不出现 token99 的赞助署名**。token99 只出现在网站上。
- 不预告「下一期幕后」之类我们没把握兑现的内容（E1 已删掉这句旁白）。
- 顺序：本期最后一镜 → 品牌片尾 sting → 6 秒号召尾帧。号召尾帧里，锁定的片尾卡上移 10 %，号召文字淡入。实现在 `shared/tools/edit_film.py` 的 `cta_tail`，只在剧集带有 `brand/endcard_cta_text.png` 时生效。

## 各期文案
- E1：「互动版在这里：跟着光，自己走一遍」+ eigenlens.ai。规格见 `episodes/E1-euv-lithography/handoff/END_CARD.md`。
- E2：待定。目前 E2 没有号召文字图，所以不会接号召尾帧。

## E1 选图包（2026-10-23）
- 片尾卡不在 E1 选图包 9 题里，状态和画法不变。双层视觉系统（`../topics/E1-euv-lithography.md` §2）只影响片尾之前的最后一镜，不改 end card。
