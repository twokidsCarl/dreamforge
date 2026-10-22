import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Local SVG covers and the locked mark are served from /public.
  // Do not turn on the default image optimizer: on Cloudflare it needs
  // a separate Images binding. See README.
  poweredByHeader: false,
};

export default nextConfig;

// Lets `next dev` see Cloudflare bindings later (R2, KV, etc.).
// No-op outside development. This MVP does not read any bindings.
import { initOpenNextCloudflareForDev } from "@opennextjs/cloudflare";

initOpenNextCloudflareForDev();
