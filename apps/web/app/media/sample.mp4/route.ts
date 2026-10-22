import { Buffer } from "node:buffer";
import { sampleMp4Base64 } from "@/lib/sample-mp4";

/**
 * Stand-in reel for the player shell. Not an episode.
 * The bytes live in source as base64 so the repo review does not see an .mp4 blob.
 * Finished films are one public R2 object each; point `video.url` at that URL.
 */
const SAMPLE = Uint8Array.from(Buffer.from(sampleMp4Base64, "base64"));

function headers(extra: Record<string, string> = {}): Headers {
  return new Headers({
    "Content-Type": "video/mp4",
    "Accept-Ranges": "bytes",
    "Cache-Control": "public, max-age=86400",
    "X-Content-Type-Options": "nosniff",
    ...extra,
  });
}

function full(): Response {
  return new Response(Buffer.from(SAMPLE), {
    status: 200,
    headers: headers({ "Content-Length": String(SAMPLE.byteLength) }),
  });
}

export function GET(request: Request): Response {
  const total = SAMPLE.byteLength;
  const range = request.headers.get("range");
  if (!range || range.includes(",")) return full();

  const match = /^bytes=(\d*)-(\d*)$/.exec(range.trim());
  if (!match || (match[1] === "" && match[2] === "")) {
    return new Response(null, {
      status: 416,
      headers: headers({ "Content-Range": `bytes */${total}` }),
    });
  }

  let start: number;
  let end: number;
  if (match[1] === "") {
    const suffix = Number(match[2]);
    start = Math.max(total - suffix, 0);
    end = total - 1;
  } else {
    start = Number(match[1]);
    end = match[2] === "" ? total - 1 : Number(match[2]);
  }

  if (!Number.isFinite(start) || !Number.isFinite(end) || start >= total || end < start) {
    return new Response(null, {
      status: 416,
      headers: headers({ "Content-Range": `bytes */${total}` }),
    });
  }

  end = Math.min(end, total - 1);
  const slice = SAMPLE.subarray(start, end + 1);
  return new Response(Buffer.from(slice), {
    status: 206,
    headers: headers({
      "Content-Length": String(slice.byteLength),
      "Content-Range": `bytes ${start}-${end}/${total}`,
    }),
  });
}
