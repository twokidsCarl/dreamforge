import type { Metadata, Viewport } from "next";
import { Outfit } from "next/font/google";
import { Analytics } from "@/components/Analytics";
import { ScanLine } from "@/components/ScanLine";
import { SiteFooter } from "@/components/SiteFooter";
import { SiteHeader } from "@/components/SiteHeader";
import { SmoothScroll } from "@/components/SmoothScroll";
import "./globals.css";

const outfit = Outfit({
  subsets: ["latin"],
  weight: ["300", "400", "500", "600"],
  variable: "--font-outfit",
  display: "swap",
});

export const metadata: Metadata = {
  metadataBase: new URL("https://eigenlens.ai"),
  title: {
    default: "EigenLens · 主观知识",
    template: "%s · EigenLens",
  },
  description: "选主轴，看结构。EigenLens（主观知识）的科普影像。",
  applicationName: "EigenLens",
  openGraph: {
    title: "EigenLens · 主观知识",
    description: "选主轴，看结构。",
    locale: "zh_CN",
    type: "website",
    siteName: "EigenLens",
  },
};

export const viewport: Viewport = {
  themeColor: "#07060d",
  colorScheme: "dark",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="zh-Hans" className={outfit.variable}>
      <body>
        <SmoothScroll />
        <ScanLine />
        <a className="skip-link" href="#content">
          跳到内容
        </a>
        <div className="corner corner-tl" aria-hidden="true" />
        <div className="corner corner-tr" aria-hidden="true" />
        <div className="corner corner-bl" aria-hidden="true" />
        <div className="corner corner-br" aria-hidden="true" />
        <div className="site-shell">
          <SiteHeader />
          <main id="content" className="flex-1">
            {children}
          </main>
          <SiteFooter />
        </div>
        <Analytics />
      </body>
    </html>
  );
}
