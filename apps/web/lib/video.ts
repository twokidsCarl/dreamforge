import type { EpisodeVideo } from "./types";

export type Playable = {
  kind: "file";
  src: string;
  mock: boolean;
};

/**
 * One direct MP4. Accepts an absolute http(s) URL (the R2 public URL)
 * or a same-site path. Empty or invalid values are not playable.
 */
export function mp4Source(url: string | undefined): string | null {
  if (!url) return null;
  const value = url.trim();
  if (!value) return null;

  if (value.startsWith("/") && !value.startsWith("//")) {
    if (value.includes("..") || value.includes("\\") || /[\s?#]/.test(value)) return null;
    return value;
  }

  try {
    const parsed = new URL(value);
    if (parsed.protocol !== "https:" && parsed.protocol !== "http:") return null;
    if (parsed.username || parsed.password) return null;
    return parsed.toString();
  } catch {
    return null;
  }
}

/** Returns null when this episode has no public file yet. */
export function resolvePlayback(video: EpisodeVideo): Playable | null {
  if (video.type !== "mp4") return null;
  const src = mp4Source(video.url);
  if (!src) return null;
  return { kind: "file", src, mock: video.mock === true };
}

export function playbackNote(video: EpisodeVideo): string {
  const playable = resolvePlayback(video);
  if (!playable) {
    return "还没有公开的播放地址。成片会放在 Cloudflare R2，页面用一档 mp4 播放。";
  }
  if (playable.mock) {
    return "现在播的是站内示例片，不是这一期成片。正式文件会换成 R2 上的一档 mp4。";
  }
  return "页面直接播放一档 mp4。成片存放在 Cloudflare R2。";
}
