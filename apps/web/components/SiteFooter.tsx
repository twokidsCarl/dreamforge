export function SiteFooter() {
  return (
    <footer className="mt-auto border-t border-white/5">
      <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-5 py-8 text-sm text-mist">
        <p>
          EigenLens ·{" "}
          <a href="https://token99.io/?utm_source=eigenlens&utm_medium=site" className="text-cream underline decoration-white/20 underline-offset-4 hover:text-gold hover:decoration-gold">
            token99.io
          </a>
        </p>
        <p className="font-latin text-[0.72rem] tracking-[0.28em] uppercase">eigenlens.ai</p>
      </div>
    </footer>
  );
}
