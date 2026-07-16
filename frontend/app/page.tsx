import Link from "next/link";
import ExampleCases from "@/components/ExampleCases";

const STEPS = [
  { n: "1", title: "Share your numbers", body: "Income, expenses, savings, debt — 3 minutes, no account." },
  { n: "2", title: "Get one clear move", body: "A ranked next action with the exact amount, decided by rules, not vibes." },
  { n: "3", title: "Ask why, see proof", body: "Every number traces to a calculation or a cited source document." },
];

const PRINCIPLES = [
  {
    title: "Show the work",
    body: "Every figure links to the calculation or document that produced it. Expand any recommendation to trace its evidence.",
  },
  {
    title: "The model never computes",
    body: "All arithmetic is deterministic and code-owned. The language model explains decisions; it is mechanically blocked from inventing numbers.",
  },
  {
    title: "Confidence has boundaries",
    body: "Every recommendation states the concrete conditions that would change it — and confidence drops when live data goes stale.",
  },
];

export default function Landing() {
  return (
    <div className="py-12 sm:py-20">
      <section className="grid items-center gap-10 lg:grid-cols-[1fr,360px]">
        <div className="max-w-3xl">
          <p className="reveal mb-4 font-mono text-[13px] font-medium uppercase tracking-widest text-indigo-600">
            Decision support for Indian households
          </p>
          <h1 className="reveal reveal-1 font-display text-4xl font-semibold leading-tight tracking-tight text-ink sm:text-6xl">
            The single best next use of your money —{" "}
            <span className="bg-gradient-to-r from-indigo-600 to-gold-signal bg-clip-text text-transparent">
              with proof.
            </span>
          </h1>
          <p className="reveal reveal-2 mt-6 max-w-2xl text-[17px] leading-relaxed text-ink-2">
            Tell NextRupee your money situation. It referees the fight between what your family
            says, what your emotions say, and what the arithmetic says — and always shows its work.
          </p>
          <div className="reveal reveal-3 mt-8 flex flex-wrap items-center gap-4">
            <Link href="/intake" className="btn-primary">
              Start — takes 3 minutes
            </Link>
            <span className="font-sans text-[13px] text-ink-3">
              No account. Nothing sold. Nothing named.
            </span>
          </div>
        </div>

        {/* Mock result card, built from the real card styles so it always matches the product. */}
        <div className="reveal reveal-3 float-slow hidden lg:block" aria-hidden="true">
          <div className="rounded-[13px] bg-gradient-to-br from-indigo-600 via-indigo-300 to-gold-signal p-px shadow-lg">
            <div className="card p-5">
              <div className="flex items-center gap-2">
                <span className="flex h-7 w-7 items-center justify-center rounded-full bg-indigo-600 font-display text-[13px] font-semibold text-white">
                  1
                </span>
                <span className="font-mono text-[11px] font-medium uppercase tracking-widest text-indigo-600">
                  Clear debt
                </span>
                <span className="rounded-full bg-success-bg px-2.5 py-0.5 font-sans text-[11px] text-success">
                  high confidence
                </span>
              </div>
              <p className="mt-3 font-display text-[15px] font-semibold leading-snug text-ink">
                Prepay the 42% APR debt — every rupee here earns a guaranteed 42%
              </p>
              <p className="mt-1.5 inline-block border-b-2 border-indigo-100 pb-0.5 font-mono text-[13px] font-medium text-ink-2">
                ₹1,20,000
              </p>
              <div className="mt-3 border-t border-border pt-3">
                <p className="font-mono text-[10px] uppercase tracking-widest text-ink-3">
                  Why this, step by step
                </p>
                <p className="mt-1.5 text-[12px] leading-relaxed text-ink-2">
                  1. Prepayment returns 42% guaranteed, tax-free…
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="mt-16 grid max-w-5xl gap-6 sm:grid-cols-3">
        {STEPS.map((s) => (
          <div key={s.n} className="flex gap-4">
            <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-indigo-100 font-display text-[15px] font-semibold text-indigo-600">
              {s.n}
            </span>
            <div>
              <h2 className="font-display text-[16px] font-semibold text-ink">{s.title}</h2>
              <p className="mt-1 text-[14px] leading-relaxed text-ink-2">{s.body}</p>
            </div>
          </div>
        ))}
      </section>

      <ExampleCases />

      <section className="card mt-16 max-w-3xl p-8">
        <p className="font-mono text-[13px] font-medium uppercase tracking-widest text-gold-signal">
          The October question
        </p>
        <blockquote className="mt-3 font-display text-xl font-medium leading-relaxed text-ink sm:text-2xl">
          &ldquo;It&rsquo;s October. You have ₹60,000 spare. Family says buy gold for Diwali.
          Your credit card is at 42% APR. What should you actually do?&rdquo;
        </blockquote>
        <p className="mt-4 text-[15px] leading-relaxed text-ink-2">
          NextRupee answers this with a ranked list: what to do first, for how much, why the
          arithmetic says so, what would change the answer — and what buying the gold anyway
          would cost you. Then you can ask it <em>why gold is expensive right now</em> and get
          a cited, live-data answer.
        </p>
      </section>

      <section className="mt-16 grid max-w-5xl gap-6 sm:grid-cols-3">
        {PRINCIPLES.map((p) => (
          <div key={p.title} className="card p-6">
            <h2 className="font-display text-lg font-semibold text-ink">{p.title}</h2>
            <p className="mt-2 text-[14px] leading-relaxed text-ink-2">{p.body}</p>
          </div>
        ))}
      </section>
    </div>
  );
}
