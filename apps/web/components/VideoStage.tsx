import type { Episode } from "@/lib/types";
import { resolvePlayback } from "@/lib/video";

export function VideoStage({ episode }: { episode: Episode }) {
  const playback = resolvePlayback(episode.video);

  return (
    <figure>
      <div className="stage">
        {playback ? (
          <video
            controls
            playsInline
            preload="metadata"
            poster={episode.coverImage}
            src={playback.src}
            aria-label={playback.mock ? `${episode.titleZh}（示例片）` : episode.titleZh}
          >
            你的浏览器不能直接播放这段影像。
          </video>
        ) : (
          <div className="absolute inset-0 flex flex-col items-center justify-center px-6 text-center">
            <div className="pointer-events-none absolute inset-5 border border-dashed border-cyan/20" aria-hidden="true" />
            <div className="gate-ring relative" aria-hidden="true">
              <span />
            </div>
            <p className="font-latin mt-6 text-[0.72rem] tracking-[0.38em] text-cyan uppercase">{episode.number}</p>
            <p className="font-serif mt-3 text-2xl font-semibold text-cream sm:text-3xl">成片还在制作</p>
            <p className="mt-3 max-w-md text-sm leading-7 text-mist">
              这一期还在制作。成片公开后，会以一档 mp4 在这里播放。
            </p>
          </div>
        )}
        {playback?.mock ? (
          <p className="pointer-events-none absolute top-3 left-3 border border-gold/55 bg-ink/80 px-2.5 py-1 text-[0.72rem] tracking-[0.22em] text-gold">
            示例
          </p>
        ) : null}
      </div>
      {playback?.mock ? (
        <figcaption className="mt-3 text-sm leading-7 text-mist">
          这是一条示例 mp4，用来看播放器。不是《{episode.titleZh}》的成片。
        </figcaption>
      ) : null}
    </figure>
  );
}
