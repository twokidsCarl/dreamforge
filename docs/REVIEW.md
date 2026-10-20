# 拉取请求审查

`shared/tools/review_pr.py` 审查本仓库的拉取请求。检查全部通过之后，才执行：

```bash
gh pr merge <编号> --auto --squash --match-head-commit <刚审查的 SHA>
```

不会强制合并，不会加 `--admin`，也不会绕过分支保护。保护规则没满足时，自动合并会一直等着。

## 用法

在仓库根目录：

```bash
python3 shared/tools/review_pr.py                  # 审查当前分支相对 origin/main 的提交
python3 shared/tools/review_pr.py --pr 12          # 审查该 PR，发评论，并在通过时打开自动合并
python3 shared/tools/review_pr.py --pr 12 --no-merge
python3 shared/tools/review_pr.py --self-test      # 只跑内置自检
```

GitHub Actions 工作流 `.github/workflows/review.yml` 在 PR 打开或更新时做同一件事。工作流只在同一仓库的 PR 上跑（不跑 fork）。

未提交的改动会让审查直接失败，避免评论和自动合并对不上磁盘上的文件。

## 检查什么

1. **剧本 lint**：每一期跑 `shared/tools/lint_script.py`（先设 `DREAMFORGE_EPISODE`）。不跑 `storyboard_check.py`，因为它会重写 `storyboard.yaml`。
2. **YAML**：`HEAD` 里每个 `.yaml` / `.yml` 都能解析。
3. **facts.yaml**：条目要有 `claim` 和 `status`。`verified` / `derived` 的等级只能是 A 或 B，并且有来源。`reported` 必须是 C 级。`needs_verification` 必须带 `verification: pending` 和非空的 `source_type`，等级只能是 A、B 或计划表那种 `B/A`。`rejected` 可以不写等级。
4. **旁白红线**（`script/script_zh.md` 全文，以及分镜里的 `vo`）：
   - 禁止「治愈失明」「治好盲人」「Boyden拿了诺奖」「Boyden是诺奖得主」「MCO-010已上市」「光遗传已能操控思想」「洗脑」「改写人类记忆」（忽略空白）。
   - 新改或新加的旁白若引用 C 级事实，算错误。main 上已经存在、这次 diff 没动的 E1 句子只警告。
   - 引用 `needs_verification`：文件里还有「状态：大纲」、且没有「状态：定稿」时只警告。大纲标记去掉之后，这些引用变成错误。
5. **大文件**：本次 diff 里新增或修改的文件，超过 2 MiB 即失败。视频、音频、`.blend`、压缩包等媒体扩展名不论大小都失败。`.png` 纹理只要不超过 2 MiB 可以通过。
6. **秘密**：diff 新增行里的私钥、云厂商密钥、GitHub 令牌、`.env` 和证书文件名。

退出码：自检或上述检查失败为 1。检查通过为 0，即使仓库设置拒绝了自动合并。

## 自动合并需要 Carl 打开的设置

审查脚本改不了仓库设置。`gh pr merge --auto` 要先在 GitHub 上打开 **Settings → General → Pull Requests → Allow auto-merge**。

建议再给 `main` 加分支保护，把本工作流的检查 **review** 设为必需。这样自动合并会等这次审查跑完；没有必需检查时，一次新的推送可能在新审查结束前就被合并。

如果保护规则还要求人工批准，脚本不会自己提交 approving review，自动合并会继续等。
