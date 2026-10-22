import { STATUS_LABEL, type EpisodeStatus } from "@/lib/types";

export function StatusBadge({ status }: { status: EpisodeStatus }) {
  const live = status === "published";
  return (
    <span
      className={
        live
          ? "inline-flex items-center gap-2 border border-cyan/40 px-2 py-1 text-[0.72rem] tracking-[0.18em] text-cyan"
          : "inline-flex items-center gap-2 border border-gold/40 px-2 py-1 text-[0.72rem] tracking-[0.18em] text-gold"
      }
    >
      <span className={live ? "h-1.5 w-1.5 bg-cyan" : "h-1.5 w-1.5 bg-gold"} aria-hidden="true" />
      {STATUS_LABEL[status]}
    </span>
  );
}
