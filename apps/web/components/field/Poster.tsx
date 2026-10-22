const THEME_IDS = new Set(["default", "euv", "opto"]);

/** Show or hide the static field poster. The image is requested only on the fallback path. */
export function setFieldPoster(themeId: string, live: boolean) {
  const poster = document.querySelector<HTMLElement>("[data-field-poster]");
  if (!poster) return;
  if (!live) {
    poster.classList.remove("is-live");
    poster.style.removeProperty("background-image");
    return;
  }
  const id = THEME_IDS.has(themeId) ? themeId : "default";
  poster.style.backgroundImage = `url("/field/${id}.webp")`;
  poster.classList.add("is-live");
}
