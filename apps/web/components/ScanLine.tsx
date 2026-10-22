"use client";

import { usePathname } from "next/navigation";

/**
 * A 1px line whose old and new positions differ, so the view-transition
 * group travels from the top of the viewport to the bottom (and back).
 * The element itself stays invisible; the group paints the stroke.
 */
export function ScanLine() {
  const pathname = usePathname();
  const atEnd = pathname.startsWith("/e/");
  return (
    <div
      className="vt-scan"
      aria-hidden="true"
      style={{ top: atEnd ? "100dvh" : "0px", viewTransitionName: "field-scan" }}
    />
  );
}
