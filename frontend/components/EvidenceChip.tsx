import type { Evidence } from "@/lib/api";

const SOURCE_LABEL: Record<Evidence["source"], string> = {
  rules_engine: "computed",
  gold_engine: "live data",
  document: "cited doc",
};

/** Evidence trace pattern: claim + verbatim value + traceable ref. */
export default function EvidenceChip({ evidence }: { evidence: Evidence }) {
  return (
    <div className="flex items-start gap-3 rounded-chip border border-border bg-surface-2 px-3 py-2.5">
      <div className="min-w-0 flex-1">
        <p className="text-[13px] leading-snug text-ink-2">{evidence.claim}</p>
        <p className="mt-1 font-mono text-[12px] text-ink-3">
          {SOURCE_LABEL[evidence.source]} · {evidence.ref}
        </p>
      </div>
      {evidence.value && (
        <span className="shrink-0 font-mono text-[14px] font-medium text-ink">{evidence.value}</span>
      )}
    </div>
  );
}
