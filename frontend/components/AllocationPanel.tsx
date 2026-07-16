"use client";

import type { Allocation } from "@/lib/api";
import { rupees } from "@/lib/format";
import InstrumentIcon from "@/components/InstrumentIcon";

/** "Where your money goes" — the deterministic %-split of investable surplus across
 *  asset classes, computed by the rules engine. Shown only when the base is secure;
 *  otherwise a calm "secure this first" note stands in. Every % and rupee is traced. */

const BAR_COLOR: Record<string, string> = {
  index: "bg-indigo-600",
  equity: "bg-indigo-600",
  bonds: "bg-ink-2",
  fd: "bg-ink-2",
  smallsavings: "bg-ink-2",
  gold: "bg-gold-signal",
  cash: "bg-success",
  commodities: "bg-ink-3",
  realestate: "bg-ink-3",
};

export default function AllocationPanel({ allocation }: { allocation: Allocation }) {
  if (!allocation.available) {
    return (
      <section className="card p-6">
        <div className="flex items-center gap-2">
          <h2 className="font-display text-lg font-semibold text-ink">Where your money goes</h2>
          <span className="rounded-full bg-warning-bg px-2.5 py-0.5 font-sans text-[12px] font-medium text-warning">
            paused
          </span>
        </div>
        <p className="mt-2 text-[14px] leading-relaxed text-ink-2">
          {allocation.reason ?? "Secure your base before investing."}
        </p>
        <p className="mt-1 text-[13px] text-ink-3">
          The split appears here the moment your cash flow and buffer can support it — decided by a
          fixed rule, not opinion.
        </p>
      </section>
    );
  }

  return (
    <section className="card p-6">
      <div className="flex flex-wrap items-baseline justify-between gap-x-3 gap-y-1">
        <h2 className="font-display text-lg font-semibold text-ink">Where your money goes</h2>
        <p className="font-sans text-[13px] text-ink-3">
          {allocation.risk_label} split ·{" "}
          <span className="font-mono font-medium text-ink-2">
            {rupees(allocation.monthly_investable)}/mo
          </span>
        </p>
      </div>
      <p className="mt-1 text-[13px] text-ink-3">
        Asset classes, not instruments. Every share is computed by the engine and traceable.
      </p>

      {/* proportion bar */}
      <div className="mt-4 flex h-3 overflow-hidden rounded-full">
        {allocation.slices.map((s) => (
          <div
            key={s.kind}
            className={BAR_COLOR[s.kind] ?? "bg-ink-3"}
            style={{ width: `${s.pct}%` }}
            title={`${s.label}: ${s.pct}%`}
          />
        ))}
      </div>

      <ul className="mt-5 space-y-4">
        {allocation.slices.map((s, i) => (
          <li key={s.kind} className={`reveal reveal-${Math.min(i + 1, 4)} flex items-start gap-3`}>
            <InstrumentIcon kind={s.kind} className="h-9 w-9" />
            <div className="min-w-0 flex-1">
              <div className="flex flex-wrap items-baseline justify-between gap-x-3">
                <span className="font-sans text-[15px] font-medium text-ink">{s.label}</span>
                <span className="font-mono text-[14px] tabular-nums text-ink-2">
                  <span className="font-semibold text-ink">{s.pct}%</span> ·{" "}
                  {rupees(s.monthly_amount)}/mo
                </span>
              </div>
              <p className="mt-0.5 text-[13px] leading-relaxed text-ink-3">{s.note}</p>
            </div>
          </li>
        ))}
      </ul>

      {allocation.foundations_pending && allocation.foundations_note && (
        <p className="mt-5 rounded-chip bg-warning-bg px-4 py-3 text-[13px] leading-relaxed text-warning">
          {allocation.foundations_note}
        </p>
      )}
    </section>
  );
}
