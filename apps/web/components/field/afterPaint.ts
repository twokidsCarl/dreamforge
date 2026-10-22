/**
 * Run work only after the first LCP entry, then during idle.
 * Field, GSAP, and Lenis use this so they do not compete with first paint.
 * If the page never reports LCP (hidden tab), the fallback still runs.
 */
export function afterLcpIdle(run: () => void): () => void {
  let cancel = false;
  let armed = false;
  let idleId = 0;
  let fallback = 0;

  const start = () => {
    if (cancel) return;
    const idle = window.requestIdleCallback;
    if (typeof idle === "function") {
      idleId = idle(() => {
        if (!cancel) run();
      }, { timeout: 1200 });
      return;
    }
    idleId = window.setTimeout(() => {
      if (!cancel) run();
    }, 1);
  };

  const arm = () => {
    if (armed || cancel) return;
    armed = true;
    window.clearTimeout(fallback);
    start();
  };

  let observer: PerformanceObserver | null = null;
  try {
    observer = new PerformanceObserver((list) => {
      if (list.getEntries().length) arm();
    });
    observer.observe({ type: "largest-contentful-paint", buffered: true });
  } catch {
    arm();
  }

  fallback = window.setTimeout(arm, 2000);

  return () => {
    cancel = true;
    observer?.disconnect();
    window.clearTimeout(fallback);
    if (typeof window.cancelIdleCallback === "function") window.cancelIdleCallback(idleId);
    else window.clearTimeout(idleId);
  };
}
