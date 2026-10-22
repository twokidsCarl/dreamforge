"use client";

import { useEffect, useRef } from "react";
import { prefersReducedMotion } from "@/components/field/capability";

const CHARSET = "0123456789ABCDEFλ·/";
const TICK_SECONDS = 0.03;

/**
 * Left-to-right lock via ScrambleText. The accessible name is the final
 * string; the cycling glyphs are hidden from assistive tech.
 */
export function Scramble({ value, play }: { value: string; play: boolean }) {
  const ref = useRef<HTMLSpanElement>(null);

  useEffect(() => {
    const node = ref.current;
    if (!node) return;
    node.textContent = value;
    if (!play || prefersReducedMotion() || value.length > 24) return;

    let cancel = false;
    let tween: { kill: () => void } | null = null;
    void Promise.all([import("gsap"), import("gsap/ScrambleTextPlugin")]).then(([{ gsap }, { ScrambleTextPlugin }]) => {
      if (cancel || !ref.current) return;
      gsap.registerPlugin(ScrambleTextPlugin);
      tween = gsap.to(ref.current, {
        duration: 0.58,
        ease: "none",
        scrambleText: {
          text: value,
          chars: CHARSET,
          speed: 0.05 / TICK_SECONDS,
          revealDelay: 0,
        },
      });
    });

    return () => {
      cancel = true;
      tween?.kill();
      if (ref.current) ref.current.textContent = value;
    };
  }, [play, value]);

  return (
    <span className="scramble" style={{ ["--chars" as string]: value.length }} aria-label={value}>
      <span ref={ref} aria-hidden="true">
        {value}
      </span>
    </span>
  );
}
