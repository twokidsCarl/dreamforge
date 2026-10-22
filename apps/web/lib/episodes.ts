import fs from "node:fs";
import path from "node:path";
import { isThemeId } from "./themes";
import { mp4Source } from "./video";
import {
  EPISODE_STATUSES,
  VIDEO_TYPES,
  type Episode,
  type EpisodeStatus,
  type EpisodeVideo,
  type VideoType,
} from "./types";

const EPISODES_DIR = path.join(process.cwd(), "content", "episodes");
const SLUG = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;
const NUMBER = /^E[1-9]\d*$/;
const DATE = /^\d{4}-\d{2}-\d{2}$/;
/** Planned object name only. Not a URL, and not fetched by the player. */
const R2_KEY = /^[A-Za-z0-9][A-Za-z0-9._/-]{0,200}$/;

function fail(file: string, message: string): never {
  throw new Error(`${file}: ${message}`);
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function requiredString(file: string, record: Record<string, unknown>, key: string): string {
  const value = record[key];
  if (typeof value !== "string" || value.trim() === "") {
    fail(file, `${key} must be a non-empty string`);
  }
  return value.trim();
}

function optionalString(file: string, record: Record<string, unknown>, key: string): string | undefined {
  if (!(key in record) || record[key] == null || record[key] === "") return undefined;
  if (typeof record[key] !== "string") fail(file, `${key} must be a string`);
  const value = (record[key] as string).trim();
  return value === "" ? undefined : value;
}

function optionalBoolean(file: string, record: Record<string, unknown>, key: string): boolean | undefined {
  if (!(key in record) || record[key] == null) return undefined;
  if (typeof record[key] !== "boolean") fail(file, `${key} must be a boolean`);
  return record[key] as boolean;
}

function parseVideo(file: string, value: unknown): EpisodeVideo {
  if (!isRecord(value)) fail(file, "video must be an object");
  const type = value.type;
  if (typeof type !== "string" || !VIDEO_TYPES.includes(type as VideoType)) {
    fail(file, `video.type must be one of ${VIDEO_TYPES.join(", ")}`);
  }

  const rawUrl = optionalString(file, value, "url");
  let url: string | undefined;
  if (rawUrl) {
    const source = mp4Source(rawUrl);
    if (!source) fail(file, "video.url must be an http(s) URL or a site path starting with /");
    url = source;
  }

  const r2Key = optionalString(file, value, "r2Key");
  if (r2Key && (!R2_KEY.test(r2Key) || r2Key.includes(".."))) {
    fail(file, "video.r2Key must be an object key, not a URL");
  }

  const mock = optionalBoolean(file, value, "mock");
  if (type === "none" && (url || r2Key || mock)) {
    fail(file, "video.type none cannot include url, r2Key, or mock");
  }
  if (mock && !url) fail(file, "video.mock needs a playable url");

  return {
    type: type as VideoType,
    url,
    r2Key,
    mock,
  };
}

function parseEpisode(file: string, value: unknown): Episode {
  if (!isRecord(value)) fail(file, "episode must be a JSON object");
  for (const key of [
    "slug",
    "number",
    "titleZh",
    "titleEn",
    "synopsis",
    "coverImage",
    "video",
    "status",
    "publishedAt",
  ]) {
    if (!(key in value)) fail(file, `missing ${key}`);
  }

  const slug = requiredString(file, value, "slug");
  const number = requiredString(file, value, "number");
  if (!SLUG.test(slug)) fail(file, "slug must be lowercase words separated by hyphens");
  if (!NUMBER.test(number)) fail(file, 'number must look like "E1"');

  const coverImage = requiredString(file, value, "coverImage");
  if (!coverImage.startsWith("/")) fail(file, "coverImage must be a site path starting with /");

  const status = value.status;
  if (typeof status !== "string" || !EPISODE_STATUSES.includes(status as EpisodeStatus)) {
    fail(file, `status must be one of ${EPISODE_STATUSES.join(", ")}`);
  }

  const publishedAt = value.publishedAt;
  if (publishedAt !== null && (typeof publishedAt !== "string" || !DATE.test(publishedAt))) {
    fail(file, "publishedAt must be null or YYYY-MM-DD");
  }
  if (status === "published" && publishedAt === null) {
    fail(file, "published episodes need a publishedAt date");
  }

  const theme = optionalString(file, value, "theme");
  if (theme && !isThemeId(theme)) {
    fail(file, "theme must be one of euv, opto, default");
  }

  return {
    slug,
    number,
    titleZh: requiredString(file, value, "titleZh"),
    titleEn: requiredString(file, value, "titleEn"),
    synopsis: requiredString(file, value, "synopsis"),
    coverImage,
    video: parseVideo(file, value.video),
    status: status as EpisodeStatus,
    publishedAt,
    theme,
  };
}

function episodeIndex(number: string): number {
  return Number(number.slice(1));
}

let cached: Episode[] | null = null;

export function getEpisodes(): Episode[] {
  if (cached) return cached;
  if (!fs.existsSync(EPISODES_DIR)) {
    throw new Error(`Missing episode directory: ${EPISODES_DIR}`);
  }
  const files = fs
    .readdirSync(EPISODES_DIR)
    .filter((name) => name.endsWith(".json"))
    .sort();
  if (files.length === 0) throw new Error("No episode JSON files in content/episodes");

  const episodes = files.map((name) => {
    const full = path.join(EPISODES_DIR, name);
    let parsed: unknown;
    try {
      parsed = JSON.parse(fs.readFileSync(full, "utf8")) as unknown;
    } catch (error) {
      const message = error instanceof Error ? error.message : "invalid JSON";
      fail(name, message);
    }
    const episode = parseEpisode(name, parsed);
    const expected = `${episode.slug}.json`;
    if (name !== expected) fail(name, `filename must be ${expected}`);
    return episode;
  });

  const slugs = new Set<string>();
  const numbers = new Set<string>();
  for (const episode of episodes) {
    if (slugs.has(episode.slug)) fail(episode.slug, "duplicate slug");
    if (numbers.has(episode.number)) fail(episode.slug, `duplicate number ${episode.number}`);
    slugs.add(episode.slug);
    numbers.add(episode.number);
  }

  cached = episodes.sort((a, b) => episodeIndex(a.number) - episodeIndex(b.number));
  return cached;
}

export function getEpisode(slug: string): Episode | undefined {
  return getEpisodes().find((episode) => episode.slug === slug);
}

export function formatPublishedAt(iso: string): string {
  const [year, month, day] = iso.split("-").map(Number);
  const date = new Date(Date.UTC(year, month - 1, day));
  return new Intl.DateTimeFormat("zh-CN", {
    year: "numeric",
    month: "long",
    day: "numeric",
    timeZone: "UTC",
  }).format(date);
}
