import { connection } from "next/server";

const TOKEN_ENV = "NEXT_PUBLIC_CF_WEB_ANALYTICS_TOKEN";

/**
 * Cloudflare Web Analytics beacon.
 * https://developers.cloudflare.com/web-analytics/get-started/
 *
 * No token → no script, so local dev and preview stay quiet.
 * The value is a public site token (it is visible in the HTML), not a secret.
 * Bracket access is intentional: Next inlines `process.env.NEXT_PUBLIC_*`
 * at build time, which would ignore a Worker variable set later.
 */
export async function Analytics() {
  await connection();
  const token = normalizeToken(process.env[TOKEN_ENV]);
  if (!token) return null;

  return (
    <script
      type="module"
      src="https://static.cloudflareinsights.com/beacon.min.js"
      data-cf-beacon={JSON.stringify({ token })}
    />
  );
}

function normalizeToken(value: string | undefined): string | undefined {
  if (!value) return undefined;
  const token = value.trim();
  if (!/^[A-Za-z0-9_-]{8,128}$/.test(token)) return undefined;
  return token;
}
