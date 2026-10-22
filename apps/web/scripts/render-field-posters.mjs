/**
 * Offline posters for the Eigen Field fallback.
 * Same interference formula as components/field/shaders.ts (a short CPU port).
 * Theme numbers are kept in sync with lib/themes.ts.
 */
import { mkdir, stat } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import sharp from "sharp";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const outDir = path.join(root, "public", "field");
const width = 840;
const height = 480;
const limit = 60 * 1024;

const themes = {
  default: { palette: ["#100c1c", "#6d5cff", "#c3b4ff"], wavelength: 1.35, sources: 4, pulse: 0 },
  euv: { palette: ["#071820", "#3ec8e0", "#8eebff"], wavelength: 0.72, sources: 6, pulse: 0 },
  opto: { palette: ["#120e24", "#6d5cff", "#8eebff"], wavelength: 2.45, sources: 3, pulse: 0.85 },
};

function hex(value) {
  const n = Number.parseInt(value.slice(1), 16);
  return [((n >> 16) & 255) / 255, ((n >> 8) & 255) / 255, (n & 255) / 255];
}

function hash(x, y) {
  const sx = Math.sin(x * 127.1 + y * 311.7) * 43758.5453;
  return sx - Math.floor(sx);
}

function vnoise(x, y) {
  const ix = Math.floor(x);
  const iy = Math.floor(y);
  const fx = x - ix;
  const fy = y - iy;
  const ux = fx * fx * (3 - 2 * fx);
  const uy = fy * fy * (3 - 2 * fy);
  const a = hash(ix, iy);
  const b = hash(ix + 1, iy);
  const c = hash(ix, iy + 1);
  const d = hash(ix + 1, iy + 1);
  return (a + (b - a) * ux) * (1 - uy) + (c + (d - c) * ux) * uy;
}

function fbm(x, y) {
  let v = 0;
  let a = 0.5;
  let px = x;
  let py = y;
  for (let i = 0; i < 4; i += 1) {
    v += a * vnoise(px, py);
    const nx = px * 2.03 + 1.7;
    const ny = py * 2.03 + 9.2;
    px = nx;
    py = ny;
    a *= 0.5;
  }
  return v;
}

function smooth(edge0, edge1, x) {
  const t = Math.min(1, Math.max(0, (x - edge0) / (edge1 - edge0)));
  return t * t * (3 - 2 * t);
}

function render(theme) {
  const [ca, cb, cc] = theme.palette.map(hex);
  const rgba = Buffer.alloc(width * height * 4);
  const time = 1.4;
  const k = 6.2831853 / theme.wavelength;
  const omega = 0.9;
  const pointerX = 0.12;
  const pointerY = 0.04;
  const minSide = Math.min(width, height);
  for (let y = 0; y < height; y += 1) {
    for (let x = 0; x < width; x += 1) {
      const px = (x + 0.5 - width * 0.5) / minSide;
      const py = (height * 0.5 - (y + 0.5)) / minSide;
      let re = 0;
      let im = 0;
      let active = 0;
      for (let i = 0; i < 6; i += 1) {
        if (i + 0.5 > theme.sources) continue;
        const ang = i * 2.399963 + time * 0.045;
        const rad = 0.16 + 0.2 * Math.sin(i * 1.7);
        const sx = Math.cos(ang) * rad + Math.sin(time * 0.07 + i) * 0.11;
        const sy = Math.sin(ang) * rad * 0.72 + Math.cos(time * 0.055 + i * 1.3) * 0.09;
        const phase = k * Math.hypot(px - sx, py - sy) - omega * time;
        re += Math.cos(phase);
        im += Math.sin(phase);
        active += 1;
      }
      const pointerPhase = k * Math.hypot(px - pointerX, py - pointerY) - omega * time;
      re += Math.cos(pointerPhase);
      im += Math.sin(pointerPhase);
      active += 1;
      let intensity = (re * re + im * im) / active;
      if (theme.pulse > 0) {
        const ph = (time * theme.pulse) % 1;
        const burst = Math.exp(-(((ph - 0.12) * 7.5) ** 2));
        intensity *= 0.22 + 0.78 * burst;
      }
      intensity *= 0.55 + 0.9 * fbm(px * 1.55 + time * 0.03, py * 1.55 - time * 0.02);
      let tone = intensity / (1 + intensity);
      tone **= 0.8;
      const m1 = smooth(0.08, 0.45, tone);
      const m2 = smooth(0.45, 0.92, tone);
      let r = ca[0] + (cb[0] - ca[0]) * m1;
      let g = ca[1] + (cb[1] - ca[1]) * m1;
      let b = ca[2] + (cb[2] - ca[2]) * m1;
      r += (cc[0] - r) * m2;
      g += (cc[1] - g) * m2;
      b += (cc[2] - b) * m2;
      const shade = 0.08 + 0.92 * tone;
      r *= shade;
      g *= shade;
      b *= shade;
      const qx = (x / width) * 2 - 1;
      const qy = (y / height) * 2 - 1;
      const vig = smooth(1.22, 0.18, Math.hypot(qx * 0.82, qy));
      const edge = 0.22 + 0.78 * vig;
      const yNorm = 1 - y / height;
      const fade = smooth(0, 0.12, yNorm) * smooth(1, 0.8, yNorm);
      const gain = edge * fade;
      const o = (y * width + x) * 4;
      rgba[o] = Math.max(0, Math.min(255, Math.round(r * gain * 255)));
      rgba[o + 1] = Math.max(0, Math.min(255, Math.round(g * gain * 255)));
      rgba[o + 2] = Math.max(0, Math.min(255, Math.round(b * gain * 255)));
      rgba[o + 3] = 255;
    }
  }
  return rgba;
}

async function writePoster(id, theme) {
  const pixels = render(theme);
  let quality = 64;
  let file = null;
  let bytes = Infinity;
  while (quality >= 30) {
    file = await sharp(pixels, { raw: { width, height, channels: 4 } })
      .webp({ quality, effort: 6, smartSubsample: true })
      .toBuffer();
    bytes = file.length;
    if (bytes <= limit) break;
    quality -= 6;
  }
  if (!file || bytes > limit) {
    throw new Error(`${id} poster is ${bytes} bytes, over ${limit}`);
  }
  const target = path.join(outDir, `${id}.webp`);
  await sharp(file).toFile(target);
  const info = await stat(target);
  console.log(`${id}.webp ${info.size} bytes (q${quality})`);
}

await mkdir(outDir, { recursive: true });
for (const [id, theme] of Object.entries(themes)) {
  await writePoster(id, theme);
}
