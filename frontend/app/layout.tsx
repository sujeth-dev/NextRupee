import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "NextRupee — the single best next use of your money",
  description:
    "Tell it your money situation; it tells you the single best next use of your money and proves why with live data. Educational decision support — not investment advice.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="mx-auto flex min-h-screen max-w-grid flex-col px-6">
          <header className="flex items-center justify-between py-6">
            <a href="/" className="flex items-center gap-2">
              <svg width="24" height="24" viewBox="0 0 24 24" aria-hidden="true">
                <path d="M12 3 L19 20 L12 15.5 L5 20 Z" fill="#0B0D12" />
              </svg>
              <span className="font-display text-lg font-semibold tracking-tight">
                NextRupee
              </span>
            </a>
            <span className="hidden font-mono text-[13px] text-ink-3 sm:block">
              every number shows its work
            </span>
          </header>
          <main className="flex-1">{children}</main>
          <footer className="border-t border-border py-8">
            <p className="max-w-3xl font-sans text-[13px] leading-relaxed text-ink-3">
              NextRupee is educational decision support, not investment advice. It reasons at
              the asset-class level and never recommends specific instruments. Rankings are
              computed deterministically in code; the language model only explains them.
            </p>
          </footer>
        </div>
      </body>
    </html>
  );
}
