"use client";

import { useSyncExternalStore } from "react";
import { FIELD_THEMES, resolveTheme, type FieldTheme } from "@/lib/themes";

let current: FieldTheme = FIELD_THEMES.default;
let releaseTimer = 0;
const listeners = new Set<() => void>();

function emit() {
  listeners.forEach((listener) => listener());
}

export function getFieldTheme() {
  return current;
}

export function subscribeFieldTheme(listener: () => void) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

export function setTheme(slugOrId: string) {
  window.clearTimeout(releaseTimer);
  const next = resolveTheme(slugOrId);
  if (next.id === current.id) return;
  current = next;
  emit();
}

/** Return to the default field after the pointer or focus has been gone for 800ms. */
export function releaseTheme() {
  window.clearTimeout(releaseTimer);
  releaseTimer = window.setTimeout(() => {
    if (current.id === "default") return;
    current = FIELD_THEMES.default;
    emit();
  }, 800);
}

export function useFieldTheme() {
  return useSyncExternalStore(subscribeFieldTheme, getFieldTheme, () => FIELD_THEMES.default);
}
