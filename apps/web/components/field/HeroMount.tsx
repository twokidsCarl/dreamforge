"use client";

import { useEffect, useState, type ComponentType } from "react";
import { canRunField } from "./capability";
import { setFieldPoster } from "./Poster";
import { useFieldTheme } from "./useFieldTheme";

type Mode = "pending" | "field" | "poster";
type FieldComponent = ComponentType<{ onFallback: () => void }>;

/**
 * Decides whether the hero may load the WebGL chunk.
 * Reduced motion, save-data, and slow networks never import it.
 */
export default function HeroMount() {
  const theme = useFieldTheme();
  const [mode, setMode] = useState<Mode>("pending");
  const [Field, setField] = useState<FieldComponent | null>(null);

  useEffect(() => {
    const media = window.matchMedia("(prefers-reduced-motion: reduce)");
    const connection = (navigator as Navigator & { connection?: EventTarget }).connection;
    const sync = () => {
      if (!canRunField()) {
        setMode("poster");
        setField(null);
        return;
      }
      setMode((current) => (current === "poster" ? "pending" : current));
    };
    sync();
    media.addEventListener("change", sync);
    connection?.addEventListener?.("change", sync);
    return () => {
      media.removeEventListener("change", sync);
      connection?.removeEventListener?.("change", sync);
    };
  }, []);

  useEffect(() => {
    if (mode !== "pending" || !canRunField()) return;
    let cancel = false;
    void import("./HeroField").then((mod) => {
      if (!cancel) {
        setField(() => mod.HeroField);
        setMode("field");
      }
    });
    return () => {
      cancel = true;
    };
  }, [mode]);

  useEffect(() => {
    setFieldPoster(theme.id, mode === "poster");
  }, [mode, theme.id]);

  if (mode !== "field" || !Field) return null;
  return <Field onFallback={() => setMode("poster")} />;
}
