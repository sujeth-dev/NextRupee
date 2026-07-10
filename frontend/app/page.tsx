import Link from "next/link";

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
      <section className="max-w-3xl">
        <p className="mb-4 font-mono text-[13px] font-medium uppercase tracking-widest text-indigo-600">
          Decision support for Indian households
        </p>
        <h1 className="font-display text-4xl font-semibold leading-tight tracking-tight text-ink sm:text-6xl">
          The single best next use of your money — with proof.
        </h1>
        <p className="mt-6 max-w-2xl text-[17px] leading-relaxed text-ink-2">
          Tell NextRupee your money situation. It referees the fight between what your family
          says, what your emotions say, and what the arithmetic says — and always shows its work.
        </p>
        <div className="mt-8 flex flex-wrap items-center gap-4">
          <Link href="/intake" className="btn-primary">
            Start — takes 3 minutes
          </Link>
          <span className="font-sans text-[13px] text-ink-3">
            No account. Nothing sold. Nothing named.
          </span>
        </div>
      </section>

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
