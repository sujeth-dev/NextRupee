"use client";

import { useState } from "react";
import type { NBCA } from "@/lib/api";
import { rangeLabel } from "@/lib/format";
import ConfidenceBadge from "@/components/ConfidenceBadge";
import EvidenceChip from "@/components/EvidenceChip";

const CATEGORY_LABEL: Record<NBCA["category"], string> = {
  stabilize: "Stabilize",
  emergency_fund: "Emergency fund",
  debt: "Debt",
  insurance: "Protection",
  invest_allocation: "Invest",
};

interface Props {
  card: NBCA;
  rank: number;
}

/** Ranked action card with the fixed reasoning-disclosure cascade:
 *  Decision → Evidence → Reasoning → Alternatives → What would change this. */
export default function NBCACard({ card, rank }: Props) {
  const [open, setOpen] = useState(rank === 1);
  const isGold = card.category === "invest_allocation" && /gold/i.test(card.action);

  return (
    <article className={`card overflow-hidden ${rank === 1 ? "ring-1 ring-indigo-600" : ""}`}>
      <button
        type="button"
        className="flex w-full items-start gap-4 p-6 text-left"
        aria-expanded={open}
        onClick={() => setOpen(!open)}
      >
        <span
          className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full font-display text-[15px] font-semibold ${
            rank === 1 ? "bg-indigo-600 text-white" : "bg-surface-2 text-ink-2"
          }`}
        >
          {rank}
        </span>
        <span className="min-w-0 flex-1">
          <span className="flex flex-wrap items-center gap-2">
            <span
              className={`font-mono text-[12px] font-medium uppercase tracking-widest ${
                isGold ? "text-gold-signal" : "text-indigo-600"
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
          <span className="mt-1 block font-mono text-[14px] text-ink-2">
            {rangeLabel(card.amount_range)}
          </span>
        </span>
        <span className="mt-1 shrink-0 font-mono text-[13px] text-ink-3" aria-hidden="true">
          {open ? "−" : "+"}
        </span>
      </button>

      {open && (
        <div className="space-y-6 border-t border-border px-6 py-6">
          <section>
            <h3 className="field-label">Why — the causal chain</h3>
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
            <h3 className="field-label">Evidence — every number, traced</h3>
            <div className="mt-2 space-y-2">
              {card.evidence.map((ev, i) => (
                <EvidenceChip key={i} evidence={ev} />
              ))}
            </div>
          </section>

          <section>
            <h3 className="field-label">Confidence basis</h3>
            <p className="mt-1 text-[14px] leading-relaxed text-ink-2">{card.confidence_basis}</p>
          </section>

          <section>
            <h3 className="field-label">Alternatives (subordinate, still visible)</h3>
            <ul className="mt-1 list-inside list-disc space-y-1 text-[14px] text-ink-2">
              {card.alternatives.map((a, i) => (
                <li key={i}>{a}</li>
              ))}
            </ul>
          </section>

          <section>
            <h3 className="field-label">Opportunity cost</h3>
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
      )}
    </article>
  );
}
