import type { InstrumentKind } from "@/lib/instruments";

/** Inline SVG per asset class, drawn in a soft tinted circle — the shared icon set
 *  for the AskBox explorer and the allocation split. Line style matches CategoryIcon. */

const PATHS: Record<InstrumentKind, JSX.Element> = {
  // banknote
  cash: (
    <>
      <rect x="3" y="6" width="18" height="12" rx="2" />
      <circle cx="12" cy="12" r="2.4" />
    </>
  ),
  // padlock (locked, guaranteed)
  fd: (
    <>
      <rect x="5" y="11" width="14" height="9" rx="2" />
      <path d="M8 11V8a4 4 0 0 1 8 0v3" />
    </>
  ),
  // certificate / note
  bonds: (
    <>
      <rect x="6" y="3" width="12" height="18" rx="2" />
      <path d="M9 8h6M9 12h6M9 16h4" />
    </>
  ),
  // stacked coins (long-term saving)
  smallsavings: (
    <>
      <ellipse cx="12" cy="6" rx="6" ry="2.4" />
      <path d="M6 6v5c0 1.3 2.7 2.4 6 2.4s6-1.1 6-2.4V6" />
      <path d="M6 11v5c0 1.3 2.7 2.4 6 2.4s6-1.1 6-2.4v-5" />
    </>
  ),
  // trending-up arrow
  equity: (
    <>
      <path d="M4 18 10 12l4 3 6-8" />
      <path d="M20 7h-4M20 7v4" />
    </>
  ),
  // basket of holdings (grid)
  index: (
    <>
      <rect x="4" y="4" width="6" height="6" rx="1" />
      <rect x="14" y="4" width="6" height="6" rx="1" />
      <rect x="4" y="14" width="6" height="6" rx="1" />
      <rect x="14" y="14" width="6" height="6" rx="1" />
    </>
  ),
  // coin with a mark
  gold: (
    <>
      <circle cx="12" cy="12" r="8" />
      <path d="M9.5 9.5h4M9.5 12h4M12.5 9.5c1.4 0 1.9 2.5 0 2.5H10l3 3.5" />
    </>
  ),
  // droplet (silver / oil)
  commodities: <path d="M12 3s5.5 5.8 5.5 9.8a5.5 5.5 0 0 1-11 0C6.5 8.8 12 3 12 3Z" />,
  // house
  realestate: (
    <>
      <path d="M4 11 12 4l8 7" />
      <path d="M6 10v9h12v-9" />
      <path d="M10 19v-5h4v5" />
    </>
  ),
};

const TINT: Record<InstrumentKind, string> = {
  cash: "bg-success-bg text-success",
  fd: "bg-indigo-100 text-indigo-600",
  bonds: "bg-surface-2 text-ink-2",
  smallsavings: "bg-success-bg text-success",
  equity: "bg-indigo-100 text-indigo-600",
  index: "bg-indigo-100 text-indigo-600",
  gold: "bg-warning-bg text-gold-signal",
  commodities: "bg-surface-2 text-ink-2",
  realestate: "bg-indigo-100 text-indigo-600",
};

export default function InstrumentIcon({
  kind,
  className = "h-7 w-7",
}: {
  kind: InstrumentKind;
  className?: string;
}) {
  return (
    <span
      className={`flex shrink-0 items-center justify-center rounded-full ${className} ${TINT[kind]}`}
      aria-hidden="true"
    >
      <svg
        viewBox="0 0 24 24"
        className="h-[16px] w-[16px]"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.7"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        {PATHS[kind]}
      </svg>
    </span>
  );
}
