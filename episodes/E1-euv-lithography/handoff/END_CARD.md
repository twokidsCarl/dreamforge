# E1 片尾规格（Carl 2026-10-23 拍板）

## 决定
- **删掉**旁白最后一句「下一期，我们会公开这部片子是怎么用 AI 和 Blender 做出来的。」以及它所在的镜头 D_10（「下一期 · 幕后篇」排版卡）。全片以 D_09（回到开场那颗锡滴、被击中前切黑）收尾。
- 片尾 end card 必须出现 **eigenlens.ai**，并有一句指向本集互动网站的中文号召。
- 画面和字幕里**不得**出现 token99 字样或致谢。

## 顺序
D_09 切黑 → `sting_end.mp4`（2 s，落到锁定的 end card）→ **CTA 尾板 6 s**：锁定 end card 原样上移 10 %（0.75 s smoothstep），两行字淡入后停住。配乐尾音可以延续到 CTA 尾板（P3 声音设计时处理）；旁白不在这里出现。

## 文案
| 行 | 内容 | 字体 / 颜色 | 位置（1080p） |
|---|---|---|---|
| 号召 | **互动版在这里：跟着光，自己走一遍** | Noto Sans CJK SC，高 0.034H，暖白 #E8ECF4 | 居中，y = 0.835H |
| 网址 | **eigenlens.ai** | Outfit wght 300，高 0.056H，品牌金 #ECBE5C + 柔光 | 居中，y = 0.91H |

文案理由：呼应全片主线「跟着光走一遍」，指向互动网站，不承诺具体功能；12 个汉字，一眼读完。

## 实现
- `handoff/tools/make_endcard_cta.py` → `episodes/E1-euv-lithography/brand/endcard_cta.png`（审看用的完整静帧）和 `endcard_cta_text.png`（只有两行字，透明底）。标志锁定稿 `brand/eigenlens_logo_locked/` **不改**。
- `shared/tools/edit_film.py`：`apply_brand_stings` 发现本期有 `brand/endcard_cta_text.png` 时，自动在 `sting_end.mp4` 后接 CTA 尾板（`cta_tail()`）。没有这个文件的期（如 E2）行为不变。
- 验收：低清全片最后 8 s 抽帧，确认 eigenlens.ai 清晰、无 token99、无「下一期」。
