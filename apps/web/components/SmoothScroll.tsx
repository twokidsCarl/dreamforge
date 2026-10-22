"use client";

import { useEffect } from "react";
import { clearScrollMotion, setScrollMotion, setScrollReader } from "@/components/field/scrollMotion";
import "lenis/dist/lenis.css";

/**
 * Lenis smooths wheel input (lerp 0.1). Touch and keyboard stay native.
 * GSAP ScrollTrigger turns hero scroll into the field's morph, and a 1.6s
 * tween plays the entrance. Both stay off the critical path.
 */
export function SmoothScroll() {
  useEffect(() => {
    const media = window.matchMedia("(prefers-reduced-motion: reduce)");
    let generation = 0;
    let stop: (() => void) | null = null;

    const sync = () => {
      const token = ++generation;
      stop?.();
      stop = null;
      clearScrollMotion();
      if (media.matches) return;

      void (async () => {
        const [{ default: Lenis }, { gsap }, { ScrollTrigger }] = await Promise.all([
          import("lenis"),
          import("gsap"),
          import("gsap/ScrollTrigger"),
        ]);
        if (token !== generation || media.matches) return;

        gsap.registerPlugin(ScrollTrigger);
        const lenis = new Lenis({
          lerp: 0.1,
          smoothWheel: true,
          syncTouch: false,
          anchors: true,
          autoRaf: false,
        });
        setScrollReader(() => lenis.scroll);
        const onLenisScroll = () => {
          ScrollTrigger.update();
        };
        lenis.on("scroll", onLenisScroll);
        const tick = (time: number) => {
          lenis.raf(time * 1000);
        };
        gsap.ticker.add(tick);
        gsap.ticker.lagSmoothing(0);

        const motion = { intro: 0 };
        let scrollProgress = 0;
        const publish = () => setScrollMotion({ intro: motion.intro, scroll: scrollProgress });
        const introTween = gsap.to(motion, {
          intro: 1,
          duration: 1.6,
          ease: "power2.out",
          onUpdate: publish,
        });
        const hero = document.getElementById("hero");
        const trigger = hero
          ? ScrollTrigger.create({
              trigger: hero,
              start: "top top",
              end: "bottom top",
              scrub: true,
              onUpdate: (self) => {
                scrollProgress = self.progress;
                publish();
              },
            })
          : null;
        publish();

        stop = () => {
          introTween.kill();
          trigger?.kill();
          gsap.ticker.remove(tick);
          lenis.destroy();
          clearScrollMotion();
        };
      })();
    };

    sync();
    media.addEventListener("change", sync);
    return () => {
      generation += 1;
      media.removeEventListener("change", sync);
      stop?.();
      clearScrollMotion();
    };
  }, []);

  return null;
}
