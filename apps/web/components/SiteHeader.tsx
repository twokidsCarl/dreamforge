import Link from "next/link";

export function SiteHeader() {
  return (
    <header className="sticky top-0 z-40 border-b border-white/5 bg-[#07060d]/75 backdrop-blur-md" style={{ viewTransitionName: "site-header" }}>
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-5 py-3">
        <Link href="/" className="group flex items-center gap-3 rounded-sm" aria-label="EigenLens 主观知识，回到首页">
          <span className="relative block h-12 w-12 shrink-0 overflow-hidden" aria-hidden="true">
            <img
              src="/brand/mark.svg"
              alt=""
              className="absolute left-0 top-0 h-[148%] w-full max-w-none object-cover object-top"
            />
          </span>
          <span className="flex flex-col">
            <span className="font-latin text-[0.95rem] font-medium tracking-[0.22em] text-cream">EigenLens</span>
            <span className="mt-1 text-[0.78rem] tracking-[0.42em] text-gold-soft">主观知识</span>
          </span>
        </Link>
        <nav aria-label="主导航">
          <Link
            href="/#episodes"
            className="font-latin text-[0.72rem] tracking-[0.32em] text-mist uppercase hover:text-cyan"
          >
            剧集
          </Link>
        </nav>
      </div>
    </header>
  );
}
