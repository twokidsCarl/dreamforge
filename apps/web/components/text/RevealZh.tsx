"use client";

import { useEffect, useRef } from "react";
import { prefersReducedMotion } from "@/components/field/capability";

/**
 * SSR and the first client render keep the full string.
 * After mount, SplitText (which uses Intl.Segmenter for graphemes) wraps
 * each grapheme and GSAP staggers opacity and blur. Total time stays ≤ 700ms.
 */
export function RevealZh({ text, className }: { text: string; className?: string }) {
  const ref = useRef<HTMLHeadingElement>(null);

  useEffect(() => {
    const heading = ref.current;
    if (!heading) return;
    const media = window.matchMedia("(prefers-reduced-motion: reduce)");
    let split: { revert: () => void } | null = null;
    let tween: { kill: () => void } | null = null;
    let cancel = false;

    const play = () => {
      if (cancel || media.matches || !ref.current) return;
      const segmenter = new Intl.Segmenter("zh-Hans", { granularity: "grapheme" });
      const count = [...segmenter.segment(text)].length;
      let duration = 0.42;
      let stagger = 0.018;
      if (count > 1) {
        const total = (count - 1) * stagger + duration;
        if (total > 0.7) {
          const scale = 0.7 / total;
          duration *= scale;
          stagger *= scale;
        }
      }
      void Promise.all([import("gsap"), import("gsap/SplitText")]).then(([{ gsap }, { SplitText }]) => {
        if (cancel || media.matches || !ref.current) return;
        gsap.registerPlugin(SplitText);
        split = SplitText.create(ref.current, {
          type: "chars",
          tag: "span",
          charsClass: "reveal-char",
          aria: "auto",
          reduceWhiteSpace: false,
          onSplit: (instance) => {
            instance.chars.forEach((node) => {
              const el = node as HTMLElement;
              el.style.display = "inline";
              el.style.lineHeight = "inherit";
            });
            tween = gsap.fromTo(
              instance.chars,
              { opacity: 0, filter: "blur(6px)" },
              {
                opacity: 1,
                filter: "blur(0px)",
                duration,
                stagger,
                ease: "power1.out",
                overwrite: true,
              },
            );
          },
        });
      });
    };

    const stop = () => {
      tween?.kill();
      tween = null;
      split?.revert();
      split = null;
    };

    if (!prefersReducedMotion()) play();
    const onChange = () => {
      stop();
      if (!media.matches) play();
    };
    media.addEventListener("change", onChange);
    return () => {
      cancel = true;
      media.removeEventListener("change", onChange);
      stop();
    };
  }, [text]);

  return (
    <h1 ref={ref} className={className}>
      {text}
    </h1>
  );
}
