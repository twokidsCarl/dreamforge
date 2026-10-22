/**
 * Scroll/morph bridge. Lenis and GSAP write it; the field reads it.
 * Neither side imports the other's library, so the field chunk stays free of GSAP.
 */

type Reader = () => number;

let intro = 0;
let scroll = 0;
let driven = false;
let reader: Reader = () => (typeof window === "undefined" ? 0 : window.scrollY);

export function setScrollReader(next: Reader) {
  reader = next;
}

export function getScrollY() {
  return reader();
}

export function setScrollMotion(next: { intro: number; scroll: number }) {
  intro = next.intro;
  scroll = next.scroll;
  driven = true;
}

export function clearScrollMotion() {
  driven = false;
  intro = 0;
  scroll = 0;
  reader = () => window.scrollY;
}

export function isScrollDriven() {
  return driven;
}

/** Intro ease (0–1) plus hero scroll progress (0–1), clamped to the morph range. */
export function readMorph() {
  return Math.min(2, Math.max(0, intro + scroll));
}
