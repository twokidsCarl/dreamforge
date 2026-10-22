import { defineCloudflareConfig } from "@opennextjs/cloudflare";

// No Next.js incremental cache. Episode films are a different R2 use:
// one public MP4 per episode, played by URL. See wrangler.toml.
// If a route later needs ISR, add NEXT_INC_CACHE_R2_BUCKET and
// `incrementalCache: r2IncrementalCache` here. Do not point that bucket
// at the episode films, and do not add Cloudflare Stream.
const config = defineCloudflareConfig({});

export default config;
