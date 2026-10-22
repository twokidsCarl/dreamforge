import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { StatusBadge } from "@/components/StatusBadge";
import { RevealZh } from "@/components/text/RevealZh";
import { VideoStage } from "@/components/VideoStage";
import { formatPublishedAt, getEpisode, getEpisodes } from "@/lib/episodes";
import { playbackNote } from "@/lib/video";

type EpisodePageProps = {
  params: Promise<{ slug: string }>;
};

export function generateStaticParams() {
  return getEpisodes().map((episode) => ({ slug: episode.slug }));
}

export const dynamicParams = false;

export async function generateMetadata({ params }: EpisodePageProps): Promise<Metadata> {
  const { slug } = await params;
  const episode = getEpisode(slug);
  if (!episode) return { title: "未找到" };
  return {
    title: `${episode.number} ${episode.titleZh}`,
    description: episode.synopsis,
    openGraph: {
      title: `${episode.number} ${episode.titleZh}`,
      description: episode.synopsis,
    },
  };
}

export default async function EpisodePage({ params }: EpisodePageProps) {
  const { slug } = await params;
  const episode = getEpisode(slug);
  if (!episode) notFound();

  return (
    <article className="mx-auto max-w-5xl px-5 pt-8 pb-20">
      <p>
        <Link href="/#episodes" className="text-sm text-mist hover:text-cyan">
          ← 返回剧集
        </Link>
      </p>
      <header className="mt-6">
        <div className="flex flex-wrap items-center gap-3">
          <p className="font-latin text-sm tracking-[0.32em] text-cyan">{episode.number}</p>
          <StatusBadge status={episode.status} />
          {episode.publishedAt ? (
            <p className="text-sm text-mist">
              <time dateTime={episode.publishedAt}>{formatPublishedAt(episode.publishedAt)}</time>
            </p>
          ) : null}
        </div>
        <RevealZh text={episode.titleZh} className="font-serif mt-4 text-[clamp(2.1rem,6vw,4rem)] leading-[1.12] font-semibold text-cream" />
        <p className="font-latin mt-3 text-sm tracking-[0.16em] text-mist uppercase">{episode.titleEn}</p>
      </header>

      <div className="mt-8">
        <VideoStage episode={episode} />
      </div>

      <div className="mt-8 grid gap-8 border-t border-white/10 pt-8 md:grid-cols-[minmax(0,1fr)_16rem]">
        <div>
          <h2 className="font-latin text-[0.72rem] tracking-[0.32em] text-gold uppercase">简介</h2>
          <p className="mt-4 text-lg leading-9 text-cream/95">{episode.synopsis}</p>
        </div>
        <aside className="text-sm leading-7 text-mist">
          <p className="font-latin text-[0.72rem] tracking-[0.28em] text-cyan uppercase">影像</p>
          <p className="mt-3">{playbackNote(episode.video)}</p>
        </aside>
      </div>
    </article>
  );
}
