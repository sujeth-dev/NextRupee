const STYLES: Record<string, string> = {
  high: "bg-success-bg text-success",
  medium: "bg-warning-bg text-warning",
  low: "bg-error-bg text-error",
};

/** Confidence signal pattern: level is engine-owned; UI only displays it. */
export default function ConfidenceBadge({ level }: { level: "high" | "medium" | "low" }) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 font-sans text-[12px] font-medium ${STYLES[level]}`}
    >
      <span className="inline-block h-1.5 w-1.5 rounded-full bg-current" aria-hidden="true" />
      {level} confidence
    </span>
  );
}
