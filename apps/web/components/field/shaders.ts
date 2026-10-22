/** Original GLSL. Not derived from Shadertoy or other snippet libraries. */

export const fullscreenVert = /* glsl */ `
attribute vec2 position;
attribute vec2 uv;
void main() {
  gl_Position = vec4(position, 0.0, 1.0);
}
`;

export const fieldFrag = /* glsl */ `
precision highp float;

uniform vec2 uResolution;
uniform float uTime;
uniform vec3 uColorA;
uniform vec3 uColorB;
uniform vec3 uColorC;
uniform float uWavelength;
uniform float uSources;
uniform float uPulse;
uniform vec2 uPointer;

float hash(vec2 p) {
  vec3 p3 = fract(vec3(p.xyx) * 0.1031);
  p3 += dot(p3, p3.yzx + 33.33);
  return fract((p3.x + p3.y) * p3.z);
}

float vnoise(vec2 p) {
  vec2 i = floor(p);
  vec2 f = fract(p);
  vec2 u = f * f * (3.0 - 2.0 * f);
  float a = hash(i);
  float b = hash(i + vec2(1.0, 0.0));
  float c = hash(i + vec2(0.0, 1.0));
  float d = hash(i + vec2(1.0, 1.0));
  return mix(mix(a, b, u.x), mix(c, d, u.x), u.y);
}

float fbm(vec2 p) {
  float v = 0.0;
  float a = 0.5;
  for (int i = 0; i < 4; i++) {
    v += a * vnoise(p);
    p = p * 2.03 + vec2(1.7, 9.2);
    a *= 0.5;
  }
  return v;
}

void main() {
  vec2 p = (gl_FragCoord.xy - 0.5 * uResolution) / min(uResolution.x, uResolution.y);
  float k = 6.2831853 / max(uWavelength, 0.2);
  float omega = 0.9;
  vec2 acc = vec2(0.0);
  float active = 0.0;

  for (int i = 0; i < 6; i++) {
    float fi = float(i);
    float gate = step(fi + 0.5, uSources);
    float ang = fi * 2.399963 + uTime * 0.045;
    float rad = 0.16 + 0.2 * sin(fi * 1.7);
    vec2 s = vec2(
      cos(ang) * rad + sin(uTime * 0.07 + fi) * 0.11,
      sin(ang) * rad * 0.72 + cos(uTime * 0.055 + fi * 1.3) * 0.09
    );
    float phase = k * length(p - s) - omega * uTime;
    acc += gate * vec2(cos(phase), sin(phase));
    active += gate;
  }

  float pointerPhase = k * length(p - uPointer) - omega * uTime;
  acc += vec2(cos(pointerPhase), sin(pointerPhase));
  active += 1.0;

  float intensity = dot(acc, acc) / max(active, 1.0);
  float ph = fract(uTime * max(uPulse, 0.0001));
  float burst = exp(-pow((ph - 0.12) * 7.5, 2.0));
  float env = mix(1.0, 0.22 + 0.78 * burst, step(0.001, uPulse));
  intensity *= env;
  intensity *= 0.55 + 0.9 * fbm(p * 1.55 + vec2(uTime * 0.03, -uTime * 0.02));

  float tone = intensity / (1.0 + intensity);
  tone = pow(clamp(tone, 0.0, 1.0), 0.8);
  vec3 col = mix(uColorA, uColorB, smoothstep(0.08, 0.45, tone));
  col = mix(col, uColorC, smoothstep(0.45, 0.92, tone));
  col *= 0.08 + 0.92 * tone;

  vec2 q = gl_FragCoord.xy / uResolution;
  float vig = smoothstep(1.22, 0.18, length((q * 2.0 - 1.0) * vec2(0.82, 1.0)));
  col *= mix(0.22, 1.0, vig);
  float y = q.y;
  col *= smoothstep(0.0, 0.12, y) * smoothstep(1.0, 0.8, y);

  gl_FragColor = vec4(col, 1.0);
}
`;

export const particleVert = /* glsl */ `
attribute vec3 position;
attribute vec3 aAxis;
attribute vec3 aShape;
attribute vec3 aShapeNext;
attribute float aSeed;

uniform float uMorph;
uniform float uShapeMix;
uniform float uDpr;
uniform float uTime;
uniform vec2 uResolution;

varying float vSeed;

void main() {
  float t1 = smoothstep(0.0, 1.0, clamp(uMorph, 0.0, 1.0));
  float t2 = smoothstep(0.0, 1.0, clamp(uMorph - 1.0, 0.0, 1.0));
  vec3 axis = mix(position, aAxis, t1);
  vec3 target = mix(aShape, aShapeNext, clamp(uShapeMix, 0.0, 1.0));
  vec3 p = mix(axis, target, t2);
  p.x += sin(uTime * 0.35 + aSeed * 12.0) * 0.007;
  p.y += cos(uTime * 0.28 + aSeed * 8.0) * 0.007;

  float ax = uResolution.x / max(uResolution.y, 1.0);
  float ay = 1.0;
  if (ax < 1.0) {
    ay = 1.0 / ax;
    ax = 1.0;
  }
  gl_Position = vec4(p.x / ax, p.y / ay, 0.0, 1.0);
  float depth = clamp(0.75 + p.z * 1.5, 0.35, 1.7);
  gl_PointSize = clamp((1.15 + aSeed * 2.15) * depth * uDpr, 1.0, 7.0);
  vSeed = aSeed;
}
`;

export const particleFrag = /* glsl */ `
precision highp float;

varying float vSeed;
uniform vec3 uColor;

void main() {
  vec2 q = gl_PointCoord * 2.0 - 1.0;
  float r2 = dot(q, q);
  if (r2 > 1.0) discard;
  float glow = exp(-r2 * 4.0);
  gl_FragColor = vec4(uColor * glow * (0.55 + 0.45 * vSeed), 1.0);
}
`;
