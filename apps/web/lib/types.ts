export const VIDEO_TYPES = ["mp4", "none"] as const;
export const EPISODE_STATUSES = ["published", "coming_soon"] as const;

export type VideoType = (typeof VIDEO_TYPES)[number];
export type EpisodeStatus = (typeof EPISODE_STATUSES)[number];

/**
 * In-site playback is one progressive MP4 (1080p or 720p).
 * The file lives on a public Cloudflare R2 URL, or — until that URL exists —
 * `url` is empty and the page shows a placeholder.
 * `r2Key` names the object we expect in the episode bucket. It is not fetched.
 * Do not add Cloudflare Stream or adaptive HLS here.
 * Bilibili / YouTube embeds are distribution, not this player.
 */
export type EpisodeVideo = {
  type: VideoType;
  /** Public R2 https URL, or a same-site path such as `/media/sample.mp4`. */
  url?: string;
  /** Object key inside the episode bucket, for example `euv-lithography/1080.mp4`. */
  r2Key?: string;
  /** True when `url` is a stand-in reel, not the finished episode. */
  mock?: boolean;
};

export type Episode = {
  slug: string;
  /** Display number such as "E1". */
  number: string;
  titleZh: string;
  titleEn: string;
  synopsis: string;
  /** Site path, for example "/covers/e1.svg". */
  coverImage: string;
  video: EpisodeVideo;
  status: EpisodeStatus;
  /** ISO date (YYYY-MM-DD) once the episode is public. Null while unpublished. */
  publishedAt: string | null;
};

export const STATUS_LABEL: Record<EpisodeStatus, string> = {
  published: "已发布",
  coming_soon: "即将上线",
};
