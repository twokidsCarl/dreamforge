import { brandLockupSvg } from "./brandLockupSvg";

/** Vector mark. Not an image element, so it does not take Largest Contentful Paint. */
export function BrandLockup() {
  return (
    <div
      className="brand-lockup"
      role="img"
      aria-label="EigenLens 主观知识"
      dangerouslySetInnerHTML={{ __html: brandLockupSvg }}
    />
  );
}
