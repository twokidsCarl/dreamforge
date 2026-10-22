"use client";

import Link from "next/link";
import { useState, type PointerEvent } from "react";
import { ViewTransition } from "react";
import { releaseTheme, setTheme } from "@/components/field/useFieldTheme";
import { Scramble } from "@/components/text/Scramble";
import { resolveTheme } from "@/lib/themes";
import type { Episode } from "@/lib/types";
import { StatusBadge } from "./StatusBadge";

function spotlight(event: PointerEvent<HTMLAnchorElement>) {
  const el = event.currentTarget;
  const rect = el.getBoundingClientRect();
  el.style.setProperty("--mx", `${event.clientX - rect.left}px`);
  el.style.setProperty("--my", `${event.clientY - rect.top}px`);
  if (event.pointerType !== "mouse" && event.pointerType !== "pen") return;
  if (!window.matchMedia("(hover: hover) and (pointer: fine)").matches) return;
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  const px = (event.clientX - rect.left) / rect.width - 0.5;
  const py = (event.clientY - rect.top) / rect.height - 0.5;
  el.style.setProperty("--rx", `${(-py * 12).toFixed(2)}deg`);
  el.style.setProperty("--ry", `${(px * 12).toFixed(2)}deg`);
}

function resetTilt(event: PointerEvent<HTMLAnchorElement>) {
  event.currentTarget.style.setProperty("--rx", "0deg");
  event.currentTarget.style.setProperty("--ry", "0deg");
}

export function EpisodeCard({ episode, index }: { episode: Episode; index: number }) {
  const [hot, setHot] = useState(false);
  const theme = resolveTheme(episode.theme ?? episode.slug);
  const name = `ep-${episode.slug}`;

  return (
    <li className={index === 0 ? "rise" : "rise rise-late"}>
      <Link
        href={`/e/${episode.slug}`}
        prefetch
        className="panel block h-full"
        onPointerEnter={() => {
          setHot(true);
          setTheme(episode.slug);
        }}
        onPointerLeave={(event) => {
          resetTilt(event);
          setHot(false);
          releaseTheme();
        }}
        onFocus={() => {
          setHot(true);
          setTheme(episode.slug);
        }}
        onBlur={() => {
          setHot(false);
          releaseTheme();
        }}
        onPointerMove={spotlight}
      >
        <ViewTransition name={name} share="morph" default="none">
          <div className="cover-frame vt-share" style={{ viewTransitionName: name, ["--vt-name" as string]: name }}>
            <img src={episode.coverImage} alt="" />
            <ul className="card-hud">
              {theme.hud.map((item) => (
                <li key={item.label}>
                  <span className="card-hud-k">{item.label}</span>
                  <Scramble value={item.value} play={hot} />
                </li>
              ))}
            </ul>
          </div>
        </ViewTransition>
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
