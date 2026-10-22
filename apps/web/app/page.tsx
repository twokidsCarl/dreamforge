import { EpisodeCard } from "@/components/EpisodeCard";
import { getEpisodes } from "@/lib/episodes";

export default function HomePage() {
  const episodes = getEpisodes();

  return (
    <>
      <section className="axis relative mx-auto flex min-h-[calc(100svh-8rem)] max-w-6xl flex-col items-center justify-center px-5 pt-10 pb-16 text-center">
        <p className="font-latin text-[0.72rem] tracking-[0.46em] text-cyan uppercase">系列</p>
        <img src="/brand/lockup.svg" alt="EigenLens 主观知识" className="brand-lockup relative mt-6" />
        <h1 className="font-serif relative mt-2 text-[clamp(2.5rem,8vw,5.25rem)] leading-[1.08] font-semibold text-cream">
          选主轴，看结构
        </h1>
        <p className="relative mt-5 max-w-xl text-base leading-8 text-mist sm:text-lg">
          主观，是编辑上的选择。主，取主轴。每一期只沿一条轴，把结构看清楚。
        </p>
      </section>

      <section id="episodes" className="mx-auto max-w-6xl scroll-mt-24 px-5 pt-4 pb-20" aria-labelledby="episodes-heading">
        <div className="mb-6 flex items-end justify-between gap-4 border-b border-white/10 pb-4">
          <div>
            <p className="font-latin text-[0.72rem] tracking-[0.36em] text-gold uppercase">Index</p>
            <h2 id="episodes-heading" className="font-serif mt-2 text-3xl font-semibold text-cream">
              剧集
            </h2>
          </div>
          <p className="font-latin text-sm tracking-[0.22em] text-mist">{episodes.length} 期</p>
        </div>
        <ul className="grid gap-6 md:grid-cols-2">
          {episodes.map((episode, index) => (
            <EpisodeCard key={episode.slug} episode={episode} index={index} />
          ))}
        </ul>
      </section>
    </>
  );
}
