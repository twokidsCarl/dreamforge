type NetworkInformation = {
  saveData?: boolean;
  effectiveType?: string;
};

export function prefersReducedMotion() {
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

export function connectionSavesData() {
  const connection = (navigator as Navigator & { connection?: NetworkInformation }).connection;
  if (!connection) return false;
  if (connection.saveData) return true;
  return connection.effectiveType === "slow-2g" || connection.effectiveType === "2g" || connection.effectiveType === "3g";
}

/** Reduced motion, save-data, and slow networks skip the field chunk entirely. */
export function canRunField() {
  return !prefersReducedMotion() && !connectionSavesData();
}

export function fieldBudget() {
  const coarse = window.matchMedia("(pointer: coarse)").matches;
  const narrow = window.matchMedia("(max-width: 760px)").matches;
  const mobile = coarse || narrow;
  const cores = navigator.hardwareConcurrency || 8;
  const memory = (navigator as Navigator & { deviceMemory?: number }).deviceMemory;
  const lowEnd = cores <= 4 || (memory !== undefined && memory <= 4);
  const count = lowEnd ? 2000 : mobile ? 4000 : 12000;
  const dprCap = mobile ? 1.5 : 2;
  const dpr = Math.min(dprCap, window.devicePixelRatio || 1);
  const finePointer = window.matchMedia("(hover: hover) and (pointer: fine)").matches;
  return { count, dpr, mobile: mobile || !finePointer };
}
