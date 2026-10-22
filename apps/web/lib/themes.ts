export const THEME_IDS = ["euv", "opto", "default"] as const;

export type ThemeId = (typeof THEME_IDS)[number];

export type FieldTheme = {
  id: string;
  /** Deep, mid, bright. Mid/bright stay on the brand cyan and violet. */
  palette: [string, string, string];
  /** Visual wavelength, dimensionless, 0.6–3.0. */
  wavelength: number;
  /** Coherent point sources, 2–6. The pointer is an extra source. */
  sources: number;
  /** 0 = continuous wave. Above 0 = pulse rate in cycles per second. */
  pulse: number;
  targetShape: "mirrors" | "dendrite" | "axis";
  hud: { label: string; value: string }[];
  /** Principal-axis angle in radians. Particles project onto this line. */
  axis: number;
};

/**
 * Dark stops are deepened brand hues so the cream title stays readable.
 * Mid and bright stops are the brand cyan / violet from the brief.
 * E1 mirror count is the six projection mirrors in the episode script,
 * not an unverified total.
 */
export const FIELD_THEMES: Record<ThemeId, FieldTheme> = {
  default: {
    id: "default",
    palette: ["#100c1c", "#6d5cff", "#c3b4ff"],
    wavelength: 1.35,
    sources: 4,
    pulse: 0,
    targetShape: "axis",
    hud: [{ label: "AXIS", value: "EIGEN" }],
    axis: 0,
  },
  euv: {
    id: "euv",
    palette: ["#071820", "#3ec8e0", "#8eebff"],
    wavelength: 0.72,
    sources: 6,
    pulse: 0,
    targetShape: "mirrors",
    hud: [
      { label: "λ", value: "13.5 nm" },
      { label: "PATH", value: "VACUUM" },
      { label: "OPTICS", value: "MIRRORS x6" },
    ],
    axis: -0.08,
  },
  opto: {
    id: "opto",
    palette: ["#120e24", "#6d5cff", "#8eebff"],
    wavelength: 2.45,
    sources: 3,
    pulse: 0.85,
    targetShape: "dendrite",
    hud: [
      { label: "λ", value: "470 nm" },
      { label: "GATE", value: "ChR2" },
    ],
    axis: -Math.PI / 2,
  },
};

const BY_SLUG: Record<string, ThemeId> = {
  "euv-lithography": "euv",
  optogenetics: "opto",
};

export function isThemeId(value: string): value is ThemeId {
  return (THEME_IDS as readonly string[]).includes(value);
}

export function resolveTheme(slugOrId: string | undefined): FieldTheme {
  if (!slugOrId) return FIELD_THEMES.default;
  if (isThemeId(slugOrId)) return FIELD_THEMES[slugOrId];
  const mapped = BY_SLUG[slugOrId];
  return mapped ? FIELD_THEMES[mapped] : FIELD_THEMES.default;
}
