import Link from "next/link";

export default function NotFound() {
  return (
    <section className="mx-auto flex min-h-[70svh] max-w-xl flex-col items-center justify-center px-5 text-center">
      <p className="font-latin text-[0.72rem] tracking-[0.4em] text-cyan uppercase">404</p>
      <h1 className="font-serif mt-4 text-4xl font-semibold text-cream">未找到这一期</h1>
      <p className="mt-4 leading-8 text-mist">这个地址没有对应的剧集。</p>
      <Link href="/" className="mt-8 border border-gold/50 px-4 py-2 text-sm text-gold hover:bg-gold/10">
        回到首页
      </Link>
    </section>
  );
}
