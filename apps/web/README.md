# EigenLens 公开网站

`apps/web` 是 **EigenLens / 主观知识** 的剧集站。这一版只做多集视频展示：首页和 `/e/[slug]`。没有对话、MCP、交互演示、登录或付款。这四块的空目录在 `extensions/`。

影像不进仓库。每一集的地址写在 `content/episodes/*.json`。没有地址时，单集页是占位，不是坏掉的播放器。播放约定见下面「影像」。

制作工具在仓库根的 `shared/` 和 `episodes/`，这里不调用它们。

标志用 `brand/eigenlens_logo_locked/` 的 `mark.svg` 和 `lockup.svg`。`public/brand/` 里是同一套路径，只去掉了锁版 SVG 自带的深色底板，方便叠在页面上。改标志请重跑锁版目录里的 `build.py`，再同步过来，不要在网页里另画一枚。

## 本地

在 `apps/web` 目录：

```bash
npm install
npm run dev
```

浏览器打开 <http://localhost:3000>。生产构建：

```bash
npm run build
npm start
```

`npm run build` 是 Next.js 自己的构建，用来确认页面和内容文件能编过。

## Cloudflare

部署目标是 Cloudflare Workers，经 [`@opennextjs/cloudflare`](https://opennext.js.org/cloudflare)。配置：

| 文件 | 作用 |
|---|---|
| `open-next.config.ts` | OpenNext 适配器。没有接 Next 的 R2 增量缓存 |
| `wrangler.toml` | Worker 名 `eigenlens`，`nodejs_compat`，静态资源目录 `.open-next/assets` |
| `public/_headers` | `/_next/static/*` 长期缓存 |

Workers 运行时本地预览（会先跑 `next build`，再交给 Wrangler）：

```bash
cp .dev.vars.example .dev.vars
npm run preview
```

部署（需要已登录的 Wrangler，账号不写进仓库）：

```bash
npx wrangler login
npm run deploy
```

自定义域名 `eigenlens.ai` 在 Cloudflare 控制台绑到这个 Worker，不写在 `wrangler.toml` 里。

图片用 `public/` 里的 SVG，没有打开 Next 图片优化。以后若要优化远程封面，再在 `wrangler.toml` 加 Images 绑定。需要 ISR 时再加 R2 绑定 `NEXT_INC_CACHE_R2_BUCKET`，并在 `open-next.config.ts` 里接上。那个桶只给 Next 缓存，不放成片。

页面在每次请求时读统计 token，所以首页和单集页是服务端渲染。成片字节不打进页面，只有一条很小的示例片路由。

## 影像

早期站内播放是 **Cloudflare R2 上的一档 mp4**（1080p 或 720p，只留一档），页面用原生 `<video>` 直链播放。

- 不接 Cloudflare Stream。
- 现在不做自适应 HLS。
- 播放器不用 Bilibili / YouTube 嵌入。那些是以后的分发渠道，不是站内默认路径。
- `video.url` 写成 R2 的公开 https 地址。地址还没有时留空，页面显示占位。`video.r2Key` 只记下对象名，Worker 不绑定这个桶，也不去拉这个 key。
- E1 目前指向 `/media/sample.mp4`，并标了 `mock: true`。那是一条几秒的静音样片，用来确认播放器，不是《一台光刻机里发生了什么》。
- 不要把 `.mp4` 提交进仓库。审查会拒绝媒体文件。

换上正式成片时，把对应 JSON 的 `url` 改成 R2 公开地址，去掉 `mock`。字段见 [content/README.md](content/README.md)。

## 访问统计

只用 [Cloudflare Web Analytics](https://developers.cloudflare.com/web-analytics/get-started/)（无 cookie）。不要加 Google Analytics。

没有 token 时，页面里不会出现统计脚本。本地默认就是这样。

1. 在 Cloudflare 控制台打开 Web Analytics，Add a site，在 Manage site 里复制 snippet 中的 token。
2. 把 token 写进 `NEXT_PUBLIC_CF_WEB_ANALYTICS_TOKEN`。这是公开的 beacon id，会出现在 HTML 里，不要当成密钥，也不要提交进仓库。
   - 本地 `next dev` / `next start`：写在 gitignore 的 `.env.local`
   - Worker：仪表盘 Settings → Variables，或 gitignore 的 `.dev.vars`。`wrangler.toml` 里留了注释掉的 `[vars]` 例子
3. 有 token 时，布局在 `</body>` 前插入官方这一段（`token` 换成变量的值）：

```html
<script type="module" src="https://static.cloudflareinsights.com/beacon.min.js" data-cf-beacon='{"token":"..."}'></script>
```

这个变量在每次请求时读取。Worker 上改完变量即可生效，不用为了换 token 改代码。变量为空、未设置，或格式不像 site token 时，不插入脚本。

## 加一集

复制 `content/episodes/` 里的 JSON，改 slug（文件名必须一致），补封面和 `video`。字段说明见 [content/README.md](content/README.md)。
