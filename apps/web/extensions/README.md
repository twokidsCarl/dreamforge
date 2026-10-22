# 还没做的部分

这一版只是剧集展示：首页和 `/e/[slug]`。成片是 R2 上的一档 mp4，地址来自 `content/episodes`。播放器不接 Cloudflare Stream，也不嵌 Bilibili / YouTube。

下面的目录留着，避免以后的功能塞进页面组件里。现在都是空的，路由、依赖和密钥都还没有。

| 目录 | 以后 |
|---|---|
| `extensions/agent/` | 站内对话。不做主持人，也不接这一版的页面 |
| `extensions/mcp/` | 给外部客户端的 MCP。不在这个 Next 应用里暴露 |
| `extensions/sim/` | 可交互的结构演示，跟成片分开 |
| `extensions/auth/` | 登录与付款。这一版没有账号 |

部署目标是 Cloudflare Workers（`@opennextjs/cloudflare`），不是默认的 Vercel。新功能如果要绑定 KV、R2 或 D1，写进 `wrangler.toml`，不要改 Blender / Python 工具。
