"use client";

import { useEffect } from "react";
import { afterLcpIdle } from "@/components/field/afterPaint";

/** Attach the CJK faces only after LCP and an idle slice, so they are not on the critical path. */
export function DeferredFonts() {
  useEffect(() => {
    return afterLcpIdle(() => {
      if (document.querySelector('link[data-deferred-fonts]')) return;
      const link = document.createElement("link");
      link.rel = "stylesheet";
      link.href = "/fonts/faces.css";
      link.dataset.deferredFonts = "true";
      document.head.appendChild(link);
    });
  }, []);

  return null;
}
