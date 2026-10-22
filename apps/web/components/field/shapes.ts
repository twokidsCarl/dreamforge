import type { FieldTheme } from "@/lib/themes";

const MAX_PARTICLES = 12000;

export { MAX_PARTICLES };

type Seg = { ax: number; ay: number; bx: number; by: number; len: number };

function mulberry32(seed: number) {
  let a = seed >>> 0;
  return () => {
    a |= 0;
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function gauss(rng: () => number) {
  const u = Math.max(rng(), 1e-8);
  const v = rng();
  return Math.sqrt(-2 * Math.log(u)) * Math.cos(Math.PI * 2 * v);
}

export function writeCloud(target: Float32Array, seed = 0x51a7) {
  const rng = mulberry32(seed);
  const count = target.length / 3;
  for (let i = 0; i < count; i += 1) {
    const o = i * 3;
    target[o] = Math.max(-1.15, Math.min(1.15, gauss(rng) * 0.4));
    target[o + 1] = Math.max(-1.15, Math.min(1.15, gauss(rng) * 0.4));
    target[o + 2] = gauss(rng) * 0.2;
  }
}

export function writeAxis(target: Float32Array, cloud: Float32Array, angle: number) {
  const c = Math.cos(angle);
  const s = Math.sin(angle);
  const count = cloud.length / 3;
  for (let i = 0; i < count; i += 1) {
    const o = i * 3;
    const t = cloud[o] * c + cloud[o + 1] * s;
    target[o] = t * c;
    target[o + 1] = t * s;
    target[o + 2] = cloud[o + 2] * 0.18;
  }
}

function arcSegments(cx: number, cy: number, radius: number, a0: number, a1: number, steps: number): Seg[] {
  const segs: Seg[] = [];
  for (let i = 0; i < steps; i += 1) {
    const t0 = a0 + ((a1 - a0) * i) / steps;
    const t1 = a0 + ((a1 - a0) * (i + 1)) / steps;
    const ax = cx + Math.cos(t0) * radius;
    const ay = cy + Math.sin(t0) * radius;
    const bx = cx + Math.cos(t1) * radius;
    const by = cy + Math.sin(t1) * radius;
    segs.push({ ax, ay, bx, by, len: Math.hypot(bx - ax, by - ay) });
  }
  return segs;
}

function lineSegments(points: Array<[number, number]>): Seg[] {
  const segs: Seg[] = [];
  for (let i = 0; i < points.length - 1; i += 1) {
    const [ax, ay] = points[i];
    const [bx, by] = points[i + 1];
    segs.push({ ax, ay, bx, by, len: Math.hypot(bx - ax, by - ay) });
  }
  return segs;
}

let mirrorSegs: Seg[] | null = null;
function mirrors(): Seg[] {
  if (mirrorSegs) return mirrorSegs;
  mirrorSegs = [
    ...arcSegments(-1.02, 0.02, 0.58, -1.05, 1.05, 36),
    ...arcSegments(0.02, 0.7, 0.46, 3.5, 5.3, 28),
    ...arcSegments(0.12, -0.72, 0.5, -1.05, 1.05, 28),
    ...arcSegments(0.92, 0.04, 0.4, 1.7, 4.5, 28),
    ...lineSegments([
      [-1.2, 0.04],
      [-0.58, 0.16],
      [-0.12, -0.02],
      [0.28, 0.26],
      [0.62, -0.1],
      [1.12, 0.06],
    ]),
  ];
  return mirrorSegs;
}

let dendriteSegs: Seg[] | null = null;
function dendrite(): Seg[] {
  if (dendriteSegs) return dendriteSegs;
  let code = "F";
  for (let iter = 0; iter < 3; iter += 1) {
    let next = "";
    for (const ch of code) next += ch === "F" ? "FF[+F][-F]" : ch;
    code = next;
  }
  let x = 0;
  let y = 0;
  let heading = Math.PI / 2;
  const stack: Array<[number, number, number]> = [];
  const raw: Array<[number, number, number, number]> = [];
  for (const ch of code) {
    if (ch === "F") {
      const nx = x + Math.cos(heading);
      const ny = y + Math.sin(heading);
      raw.push([x, y, nx, ny]);
      x = nx;
      y = ny;
    } else if (ch === "+") heading += 0.5;
    else if (ch === "-") heading -= 0.5;
    else if (ch === "[") stack.push([x, y, heading]);
    else if (ch === "]") {
      const top = stack.pop();
      if (top) {
        x = top[0];
        y = top[1];
        heading = top[2];
      }
    }
  }
  let minX = Infinity;
  let maxX = -Infinity;
  let minY = Infinity;
  let maxY = -Infinity;
  for (const [ax, ay, bx, by] of raw) {
    minX = Math.min(minX, ax, bx);
    maxX = Math.max(maxX, ax, bx);
    minY = Math.min(minY, ay, by);
    maxY = Math.max(maxY, ay, by);
  }
  const width = Math.max(maxX - minX, 1e-3);
  const height = Math.max(maxY - minY, 1e-3);
  const scale = Math.min(1.45 / width, 1.5 / height);
  const cx = (minX + maxX) / 2;
  dendriteSegs = raw.map(([ax, ay, bx, by]) => {
    const x1 = (ax - cx) * scale;
    const x2 = (bx - cx) * scale;
    const y1 = (ay - minY) * scale - 0.78;
    const y2 = (by - minY) * scale - 0.78;
    return { ax: x1, ay: y1, bx: x2, by: y2, len: Math.hypot(x2 - x1, y2 - y1) };
  });
  return dendriteSegs;
}

function sampleSegments(target: Float32Array, segs: Seg[], seed: number, jitter: number) {
  const rng = mulberry32(seed);
  const total = segs.reduce((sum, seg) => sum + seg.len, 0);
  const count = target.length / 3;
  for (let i = 0; i < count; i += 1) {
    let pick = rng() * total;
    let seg = segs[0];
    for (const candidate of segs) {
      pick -= candidate.len;
      if (pick <= 0) {
        seg = candidate;
        break;
      }
    }
    const t = rng();
    const x = seg.ax + (seg.bx - seg.ax) * t;
    const y = seg.ay + (seg.by - seg.ay) * t;
    const dx = seg.bx - seg.ax;
    const dy = seg.by - seg.ay;
    const inv = 1 / Math.max(Math.hypot(dx, dy), 1e-5);
    const j = (rng() - 0.5) * jitter;
    const o = i * 3;
    target[o] = x + -dy * inv * j;
    target[o + 1] = y + dx * inv * j;
    target[o + 2] = (rng() - 0.5) * 0.08;
  }
}

export function writeShape(target: Float32Array, theme: FieldTheme, cloud: Float32Array) {
  if (theme.targetShape === "axis") {
    writeAxis(target, cloud, theme.axis);
    return;
  }
  if (theme.targetShape === "mirrors") {
    sampleSegments(target, mirrors(), 0xa11ce, 0.03);
    return;
  }
  sampleSegments(target, dendrite(), 0xd3e07, 0.026);
}
