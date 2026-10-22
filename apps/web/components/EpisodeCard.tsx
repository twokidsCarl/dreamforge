import Link from "next/link";
import type { Episode } from "@/lib/types";
import { StatusBadge } from "./StatusBadge";

export function EpisodeCard({ episode, index }: { episode: Episode; index: number }) {
  return (
    <li className={index === 0 ? "rise" : "rise rise-late"}>
      <Link href={`/e/${episode.slug}`} className="panel block h-full">
        <div className="cover-frame">
          <img src={episode.coverImage} alt="" />
        </div>
        <div className="flex items-center justify-between gap-3 px-4 pt-4">
          <p className="font-latin text-sm tracking-[0.28em] text-cyan">{episode.number}</p>
          <StatusBadge status={episode.status} />
        </div>
        <div className="px-4 pt-3 pb-5">
          <h3 className="font-serif text-2xl leading-snug font-semibold text-cream">{episode.titleZh}</h3>
          <p className="font-latin mt-1 text-[0.78rem] tracking-[0.14em] text-mist uppercase">{episode.titleEn}</p>
          <p className="mt-3 line-clamp-3 text-sm leading-7 text-mist">{episode.synopsis}</p>
        </div>
      </Link>
    </li>
  );
}
