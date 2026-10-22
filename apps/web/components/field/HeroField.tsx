"use client";

import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { startField } from "./engine";

export function HeroField({ onFallback }: { onFallback: () => void }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const fallbackRef = useRef(onFallback);
  fallbackRef.current = onFallback;
  const [root, setRoot] = useState<HTMLElement | null>(null);

  useEffect(() => {
    const node = document.querySelector<HTMLElement>("[data-field-root]");
    if (!node) {
      fallbackRef.current();
      return;
    }
    setRoot(node);
  }, []);

  useEffect(() => {
    const canvas = canvasRef.current;
    const section = document.getElementById("hero");
    if (!root || !canvas || !section) return;
    let handle: { stop: () => void } | null = null;
    try {
      handle = startField(canvas, section, () => fallbackRef.current());
    } catch {
      fallbackRef.current();
    }
    return () => handle?.stop();
  }, [root]);

  if (!root) return null;
  return createPortal(<canvas ref={canvasRef} className="hero-canvas" aria-hidden="true" />, root);
}
