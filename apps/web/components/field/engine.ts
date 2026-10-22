import { Geometry, Mesh, Program, Renderer, Triangle } from "ogl";
import { FIELD_THEMES, type FieldTheme } from "@/lib/themes";
import { fieldBudget } from "./capability";
import { getScrollY, isScrollDriven, readMorph } from "./scrollMotion";
import { fieldFrag, fullscreenVert, particleFrag, particleVert } from "./shaders";
import { MAX_PARTICLES, writeAxis, writeCloud, writeShape } from "./shapes";
import { getFieldTheme, subscribeFieldTheme } from "./useFieldTheme";

type RGB = [number, number, number];

type Sample = {
  palette: [RGB, RGB, RGB];
  wavelength: number;
  sources: number;
  pulse: number;
  axis: number;
  theme: FieldTheme;
};

const PREVIEW = 0.72;

function hexToRgb(hex: string): RGB {
  const value = Number.parseInt(hex.slice(1), 16);
  return [((value >> 16) & 255) / 255, ((value >> 8) & 255) / 255, (value & 255) / 255];
}

function sampleTheme(theme: FieldTheme): Sample {
  return {
    palette: [hexToRgb(theme.palette[0]), hexToRgb(theme.palette[1]), hexToRgb(theme.palette[2])],
    wavelength: theme.wavelength,
    sources: theme.sources,
    pulse: theme.pulse,
    axis: theme.axis,
    theme,
  };
}

function smoothstep(t: number) {
  const x = Math.min(1, Math.max(0, t));
  return x * x * (3 - 2 * x);
}

function mix(a: number, b: number, t: number) {
  return a + (b - a) * t;
}

function mixRgb(out: RGB, a: RGB, b: RGB, t: number) {
  out[0] = mix(a[0], b[0], t);
  out[1] = mix(a[1], b[1], t);
  out[2] = mix(a[2], b[2], t);
}

/**
 * At rest the cloud has converged onto the principal axis (morph 1).
 * Hovering an episode eases the particles part-way toward that episode's
 * shape so the theme reads in the hero; scrolling the hero away finishes at 2.
 */
function composeMorph(base: number, reveal: number) {
  if (base < 1) return base;
  return base + (2 - base) * reveal * PREVIEW;
}

export type FieldHandle = { stop: () => void };

export function startField(canvas: HTMLCanvasElement, section: HTMLElement, onFallback: () => void): FieldHandle {
  const budget = fieldBudget();
  let dpr = budget.dpr;
  let drawCount = budget.count;
  let downgrades = 0;
  let stopped = false;

  const renderer = new Renderer({
    canvas,
    dpr,
    alpha: false,
    depth: false,
    stencil: false,
    antialias: false,
    powerPreference: "default",
    autoClear: false,
    webgl: 2,
  });

  if (!renderer.isWebgl2 || !renderer.gl) {
    const gl = renderer.gl;
    gl?.getExtension("WEBGL_lose_context")?.loseContext();
    onFallback();
    return { stop() {} };
  }

  const gl = renderer.gl;
  gl.clearColor(7 / 255, 6 / 255, 13 / 255, 1);

  const bg = new Mesh(gl, {
    geometry: new Triangle(gl),
    program: new Program(gl, {
      vertex: fullscreenVert,
      fragment: fieldFrag,
      depthTest: false,
      depthWrite: false,
      cullFace: false,
      uniforms: {
        uResolution: { value: [1, 1] },
        uTime: { value: 0 },
        uColorA: { value: [0, 0, 0] },
        uColorB: { value: [0, 0, 0] },
        uColorC: { value: [0, 0, 0] },
        uWavelength: { value: 1.35 },
        uSources: { value: 4 },
        uPulse: { value: 0 },
        uPointer: { value: [0, 0] },
      },
    }),
  });

  const cloud = new Float32Array(MAX_PARTICLES * 3);
  const axis = new Float32Array(MAX_PARTICLES * 3);
  const shape = new Float32Array(MAX_PARTICLES * 3);
  const shapeNext = new Float32Array(MAX_PARTICLES * 3);
  const seeds = new Float32Array(MAX_PARTICLES);
  writeCloud(cloud);
  writeAxis(axis, cloud, FIELD_THEMES.default.axis);
  writeShape(shape, FIELD_THEMES.default, cloud);
  shapeNext.set(shape);
  for (let i = 0; i < MAX_PARTICLES; i += 1) seeds[i] = (i * 0.6180339887) % 1;

  const geometry = new Geometry(gl, {
    position: { size: 3, data: cloud },
    aAxis: { size: 3, data: axis },
    aShape: { size: 3, data: shape },
    aShapeNext: { size: 3, data: shapeNext },
    aSeed: { size: 1, data: seeds },
  });
  geometry.setDrawRange(0, drawCount);

  const points = new Mesh(gl, {
    mode: gl.POINTS,
    geometry,
    program: new Program(gl, {
      vertex: particleVert,
      fragment: particleFrag,
      depthTest: false,
      depthWrite: false,
      cullFace: false,
      transparent: true,
      uniforms: {
        uMorph: { value: 0 },
        uShapeMix: { value: 0 },
        uDpr: { value: dpr },
        uTime: { value: 0 },
        uResolution: { value: [1, 1] },
        uColor: { value: [0.7, 0.8, 1] },
      },
    }),
  });
  points.program.setBlendFunc(gl.ONE, gl.ONE);

  const linked = gl.getProgramParameter(bg.program.program, gl.LINK_STATUS) && gl.getProgramParameter(points.program.program, gl.LINK_STATUS);
  if (!linked) {
    gl.getExtension("WEBGL_lose_context")?.loseContext();
    onFallback();
    return { stop() {} };
  }

  let from = sampleTheme(FIELD_THEMES.default);
  let to = from;
  let blend = 1;
  let blendStart = 0;
  let shapeMix = 0;
  let writtenAngle = from.axis;
  const colorA: RGB = [...from.palette[0]];
  const colorB: RGB = [...from.palette[1]];
  const colorC: RGB = [...from.palette[2]];

  const pointer = { x: 0, y: 0 };
  const pointerTarget = { x: 0, y: 0.05 };
  let visible = true;
  let hidden = document.hidden;
  let raf = 0;
  let last = performance.now();
  let startedAt = performance.now();
  let warm = 0;
  let accum = 0;
  let samples = 0;

  function mark(attr: { needsUpdate?: boolean } | undefined) {
    if (attr) attr.needsUpdate = true;
  }

  function retarget(theme: FieldTheme) {
    if (theme.id === to.theme.id && blend === 1) return;
    const ease = smoothstep(blend);
    const displayed: Sample = {
      palette: [
        [mix(from.palette[0][0], to.palette[0][0], ease), mix(from.palette[0][1], to.palette[0][1], ease), mix(from.palette[0][2], to.palette[0][2], ease)],
        [mix(from.palette[1][0], to.palette[1][0], ease), mix(from.palette[1][1], to.palette[1][1], ease), mix(from.palette[1][2], to.palette[1][2], ease)],
        [mix(from.palette[2][0], to.palette[2][0], ease), mix(from.palette[2][1], to.palette[2][1], ease), mix(from.palette[2][2], to.palette[2][2], ease)],
      ],
      wavelength: mix(from.wavelength, to.wavelength, ease),
      sources: Math.round(mix(from.sources, to.sources, ease)),
      pulse: mix(from.pulse, to.pulse, ease),
      axis: mix(from.axis, to.axis, ease),
      theme: to.theme,
    };
    for (let i = 0; i < shape.length; i += 1) {
      shape[i] = shape[i] * (1 - shapeMix) + shapeNext[i] * shapeMix;
    }
    mark(geometry.attributes.aShape);
    writeShape(shapeNext, theme, cloud);
    mark(geometry.attributes.aShapeNext);
    from = displayed;
    to = sampleTheme(theme);
    blend = 0;
    shapeMix = 0;
    blendStart = performance.now();
  }

  function resize() {
    const width = document.documentElement.clientWidth || window.innerWidth;
    const height = section.clientHeight || window.innerHeight;
    renderer.dpr = dpr;
    renderer.setSize(Math.max(1, width), Math.max(1, height));
    renderer.setViewport(gl.canvas.width, gl.canvas.height);
    const resolution = [gl.canvas.width, gl.canvas.height];
    bg.program.uniforms.uResolution.value = resolution;
    points.program.uniforms.uResolution.value = resolution;
    points.program.uniforms.uDpr.value = dpr;
  }

  function downgrade() {
    if (downgrades >= 2) return;
    downgrades += 1;
    dpr = dpr > 1.5 ? 1.5 : 1;
    drawCount = Math.max(256, Math.floor(drawCount / 2));
    geometry.setDrawRange(0, drawCount);
    resize();
  }

  function applyUniforms(now: number) {
    if (blend < 1) {
      blend = Math.min(1, (now - blendStart) / 600);
    }
    const ease = smoothstep(blend);
    mixRgb(colorA, from.palette[0], to.palette[0], ease);
    mixRgb(colorB, from.palette[1], to.palette[1], ease);
    mixRgb(colorC, from.palette[2], to.palette[2], ease);
    const wavelength = mix(from.wavelength, to.wavelength, ease);
    const sources = Math.round(mix(from.sources, to.sources, ease));
    const pulse = mix(from.pulse, to.pulse, ease);
    const axisAngle = mix(from.axis, to.axis, ease);
    if (blend >= 1 && to.theme.id !== from.theme.id) {
      shape.set(shapeNext);
      mark(geometry.attributes.aShape);
      from = to;
    }
    shapeMix = blend >= 1 ? 0 : ease;
    if (Math.abs(axisAngle - writtenAngle) > 0.0008) {
      writeAxis(axis, cloud, axisAngle);
      mark(geometry.attributes.aAxis);
      writtenAngle = axisAngle;
    }

    const elapsed = (now - startedAt) / 1000;
    const dt = Math.min(48, Math.max(8, now - last));
    if (budget.mobile) {
      pointerTarget.x = Math.sin(elapsed * 0.17) * 0.34;
      pointerTarget.y = Math.cos(elapsed * 0.13) * 0.22;
    }
    const follow = 1 - Math.pow(0.92, dt / 16.666);
    pointer.x += (pointerTarget.x - pointer.x) * follow;
    pointer.y += (pointerTarget.y - pointer.y) * follow;

    const reveal = mix(from.theme.targetShape === "axis" ? 0 : 1, to.theme.targetShape === "axis" ? 0 : 1, ease);
    let base: number;
    if (isScrollDriven()) {
      base = readMorph();
    } else {
      const intro = smoothstep(Math.min(1, (now - startedAt) / 1600));
      const height = section.clientHeight || window.innerHeight;
      const progress = Math.min(1, Math.max(0, getScrollY() / Math.max(height * 0.92, 1)));
      base = Math.min(2, intro + progress);
    }

    bg.program.uniforms.uTime.value = elapsed;
    bg.program.uniforms.uColorA.value = colorA;
    bg.program.uniforms.uColorB.value = colorB;
    bg.program.uniforms.uColorC.value = colorC;
    bg.program.uniforms.uWavelength.value = wavelength;
    bg.program.uniforms.uSources.value = sources;
    bg.program.uniforms.uPulse.value = pulse;
    bg.program.uniforms.uPointer.value = [pointer.x, pointer.y];
    points.program.uniforms.uTime.value = elapsed;
    points.program.uniforms.uMorph.value = composeMorph(base, reveal);
    points.program.uniforms.uShapeMix.value = shapeMix;
    points.program.uniforms.uColor.value = colorC;
  }

  function frame(now: number) {
    if (stopped) return;
    raf = requestAnimationFrame(frame);
    if (!visible || hidden) return;
    applyUniforms(now);
    renderer.setViewport(gl.canvas.width, gl.canvas.height);
    gl.clear(gl.COLOR_BUFFER_BIT);
    bg.draw();
    points.draw();

    const dt = now - last;
    last = now;
    if (dt <= 0 || dt > 80) return;
    if (warm < 45) {
      warm += 1;
      return;
    }
    accum += dt;
    samples += 1;
    if (samples >= 60) {
      const average = accum / samples;
      accum = 0;
      samples = 0;
      if (average > 22) downgrade();
    }
  }

  function syncLoop() {
    const run = visible && !hidden && !stopped;
    if (!run) {
      if (raf) cancelAnimationFrame(raf);
      raf = 0;
      return;
    }
    if (!raf) {
      last = performance.now();
      raf = requestAnimationFrame(frame);
    }
  }

  function onPointerMove(event: PointerEvent) {
    if (budget.mobile) return;
    const rect = canvas.getBoundingClientRect();
    if (rect.width < 1 || rect.height < 1) return;
    const minSide = Math.min(rect.width, rect.height);
    pointerTarget.x = ((event.clientX - rect.left) / rect.width - 0.5) * (rect.width / minSide);
    pointerTarget.y = (0.5 - (event.clientY - rect.top) / rect.height) * (rect.height / minSide);
  }

  function onVisibility() {
    hidden = document.hidden;
    syncLoop();
  }

  function onContextLost(event: Event) {
    event.preventDefault();
    stop();
    onFallback();
  }

  const observer = new IntersectionObserver(
    ([entry]) => {
      visible = Boolean(entry?.isIntersecting);
      syncLoop();
    },
    { threshold: 0 },
  );

  const resizeObserver = new ResizeObserver(() => resize());

  function stop() {
    if (stopped) return;
    stopped = true;
    if (raf) cancelAnimationFrame(raf);
    raf = 0;
    observer.disconnect();
    resizeObserver.disconnect();
    section.removeEventListener("pointermove", onPointerMove);
    document.removeEventListener("visibilitychange", onVisibility);
    canvas.removeEventListener("webglcontextlost", onContextLost);
    unsubscribe();
    bg.program.remove();
    points.program.remove();
  }

  const unsubscribe = subscribeFieldTheme(() => retarget(getFieldTheme()));
  retarget(getFieldTheme());
  resize();
  observer.observe(section);
  resizeObserver.observe(section);
  section.addEventListener("pointermove", onPointerMove, { passive: true });
  document.addEventListener("visibilitychange", onVisibility);
  canvas.addEventListener("webglcontextlost", onContextLost);
  syncLoop();

  return { stop };
}
