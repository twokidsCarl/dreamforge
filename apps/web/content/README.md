# 剧集内容

每一期一个 JSON 文件，放在 `content/episodes/<slug>.json`。网站在构建时读取这个目录，按 `number`（E1、E2…）排序。

不要把成片放进仓库。早期约定：

- 成片是 **一档** 渐进式 mp4（1080p 或 720p，只留一档）。
- 文件放在 Cloudflare R2 的公开地址，写进 `video.url`。
- 页面用原生 `<video>` 直链播放。不接 Cloudflare Stream，也不做自适应 HLS。
- Bilibili / YouTube 嵌入不是站内播放器。分发渠道以后另说，不要写进 `video.type`。

制作工程在仓库的 `episodes/`，和这里的 JSON 互不导入。改剧本、分镜、Blender 不会自动改网站。

## 字段

| 字段 | 说明 |
|---|---|
| `slug` | URL，`/e/<slug>`。小写英文和连字符，并且必须和文件名一致 |
| `number` | 显示用期号，`E1`、`E2` |
| `titleZh` / `titleEn` | 中文片名、英文片名 |
| `synopsis` | 短简介。只写已经核对过的事实，不写未核实的数字 |
| `coverImage` | 站内路径，例如 `/covers/e1.svg`。同时作为播放器 poster |
| `video.type` | `mp4` 或 `none` |
| `video.url` | 可省略或留空。有值时是 R2 的 http(s) 公开地址，或站内路径（例如示例片 `/media/sample.mp4`） |
| `video.r2Key` | 可选。桶里的对象名，例如 `optogenetics/1080.mp4`。只是占位，播放器不读它 |
| `video.mock` | 可选布尔。`true` 表示 `url` 是示例片，不是这一期成片 |
| `status` | `published` 或 `coming_soon` |
| `publishedAt` | 公开日期 `YYYY-MM-DD`，未公开写 `null`。`published` 必须有日期 |

`type` 为 `mp4` 但 `url` 为空时，单集页显示占位，不显示坏掉的播放器。`type` 为 `none` 时不能再写 `url`、`r2Key` 或 `mock`。

`/media/sample.mp4` 是一条几秒钟的静音样片，用来看播放器。它不是光刻机成片。

## 例子

正式成片（公开 URL 换成实际上传后的地址）：

```json
{
  "slug": "optogenetics",
  "number": "E2",
  "titleZh": "光遗传学",
  "titleEn": "Optogenetics",
  "synopsis": "……",
  "coverImage": "/covers/e2.svg",
  "video": {
    "type": "mp4",
    "url": "https://media.example.com/optogenetics/1080.mp4",
    "r2Key": "optogenetics/1080.mp4"
  },
  "status": "published",
  "publishedAt": "2026-11-01"
}
```

成片还没上传，只记下对象名：

```json
"video": {
  "type": "mp4",
  "url": "",
  "r2Key": "optogenetics/1080.mp4"
}
```
