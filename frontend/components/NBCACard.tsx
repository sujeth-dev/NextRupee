"use client";

import { useState } from "react";
import type { NBCA } from "@/lib/api";
import { rangeLabel } from "@/lib/format";
import CategoryIcon from "@/components/CategoryIcon";
import ConfidenceBadge from "@/components/ConfidenceBadge";
import EvidenceChip from "@/components/EvidenceChip";

const CATEGORY_LABEL: Record<NBCA["category"], string> = {
  stabilize: "Get steady",
  emergency_fund: "Safety net",
  debt: "Clear debt",
  insurance: "Protect your family",
  invest_allocation: "Grow your money",
};

interface Props {
  card: NBCA;
  rank: number;
}

/** Ranked action card with the fixed reasoning-disclosure cascade:
 *  Decision → Evidence → Reasoning → Alternatives → What would change this.
 *  Rank 1 wears a gradient glow; every card starts folded. */
export default function NBCACard({ card, rank }: Props) {
  const [open, setOpen] = useState(false);
  const isGold = card.category === "invest_allocation" && /gold/i.test(card.action);

  const article = (
    <article className="card overflow-hidden">
      <button
        type="button"
        className="flex w-full items-start gap-4 p-6 text-left"
        aria-expanded={open}
        onClick={() => setOpen(!open)}
      >
        <span className="flex shrink-0 flex-col items-center gap-2">
          <span
            className={`flex h-8 w-8 items-center justify-center rounded-full font-display text-[15px] font-semibold ${
              rank === 1 ? "bg-indigo-600 text-white" : "bg-surface-2 text-ink-2"
            }`}
          >
            {rank}
          </span>
          <CategoryIcon category={card.category} />
        </span>
        <span className="min-w-0 flex-1">
          <span className="flex flex-wrap items-center gap-2">
            <span
              className={`font-mono text-[12px] font-medium uppercase tracking-widest ${
                isGold ? "gold-shimmer" : "text-indigo-600"
              }`}
            >
              {CATEGORY_LABEL[card.category]}
            </span>
            <ConfidenceBadge level={card.confidence} />
            {card.degraded && (
              <span className="rounded-full bg-surface-2 px-3 py-1 font-sans text-[12px] text-ink-3">
                engine text
              </span>
            )}
          </span>
          <span className="mt-2 block font-display text-lg font-semibold leading-snug text-ink">
            {card.action}
          </span>
          <span className="mt-1.5 inline-block border-b-2 border-indigo-100 pb-0.5 font-mono text-[15px] font-medium tabular-nums text-ink-2">
            {rangeLabel(card.amount_range)}
          </span>
        </span>
        <span
          className="mt-1 shrink-0 rounded-full border border-border-strong px-3 py-1 font-sans text-[12px] font-medium text-ink-2"
          aria-hidden="true"
        >
          {open ? "Hide ▴" : "Details ▾"}
        </span>
      </button>

      <div className={`details-fold ${open ? "open" : ""}`}>
        <div>
          <div className="space-y-6 border-t border-border px-6 py-6">
            <section>
              <h3 className="field-label">Why this, step by step</h3>
              <ol className="mt-2 space-y-2">
                {card.rationale_chain.map((step, i) => (
                  <li key={i} className="flex gap-3 text-[14px] leading-relaxed text-ink-2">
                    <span className="font-mono text-[13px] text-ink-3">{i + 1}.</span>
                    {step}
                  </li>
                ))}
              </ol>
            </section>

            <section>
              <h3 className="field-label">The numbers behind it — every one traced</h3>
              <div className="mt-2 space-y-2">
                {card.evidence.map((ev, i) => (
                  <EvidenceChip key={i} evidence={ev} />
                ))}
              </div>
            </section>

            <section>
              <h3 className="field-label">How sure we are, and why</h3>
              <p className="mt-1 text-[14px] leading-relaxed text-ink-2">{card.confidence_basis}</p>
            </section>

            <section>
              <h3 className="field-label">Other ways to do this</h3>
              <ul className="mt-1 list-inside list-disc space-y-1 text-[14px] text-ink-2">
                {card.alternatives.map((a, i) => (
                  <li key={i}>{a}</li>
                ))}
              </ul>
            </section>

            <section>
              <h3 className="field-label">What you give up by choosing this</h3>
              <p className="mt-1 text-[14px] leading-relaxed text-ink-2">{card.opportunity_cost}</p>
            </section>

            <section className="rounded-chip bg-warning-bg px-4 py-3">
              <h3 className="font-sans text-[13px] font-medium text-warning">
                What would change this advice
              </h3>
              <ul className="mt-1 list-inside list-disc space-y-1 text-[13px] text-ink-2">
                {card.invalidation_conditions.map((c, i) => (
                  <li key={i}>{c}</li>
                ))}
              </ul>
            </section>
          </div>
        </div>
      </div>
    </article>
  );

  if (rank !== 1) return article;
  return (
    <div className="pulse-once rounded-[13px] bg-gradient-to-br from-indigo-600 via-indigo-300 to-gold-signal p-px shadow-md">
      {article}
    </div>
  );
}
